"""Fault injection builds the production C sources in an isolated test extension."""

import importlib.util
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

import pytest

SOURCE = r"""
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <errno.h>
#include <string.h>
static int reads_left = -1;
static int mode = 0;
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
static NTSTATUS fake_rng(BCRYPT_ALG_HANDLE algorithm, PUCHAR bytes, ULONG size, ULONG flags) {
    if (reads_left == 0) return (NTSTATUS)0xC0000001L;
    if (reads_left > 0) reads_left--;
    memset(bytes, 0xab, size);
    return 0;
}
#define BCryptGenRandom fake_rng
#else
#include <unistd.h>
#include <pthread.h>
static int fail_fork_registration = 0;
static int test_atfork(void (*prepare)(void), void (*parent)(void), void (*child)(void)) {
    if (fail_fork_registration) return ENOMEM;
    return pthread_atfork(prepare, parent, child);
}
#define pthread_atfork test_atfork
static ssize_t fake_read(int fd, void *bytes, size_t size) {
    if (reads_left == 0) {
        errno = EIO;
        return mode == 1 ? 0 : -1;
    }
    if (reads_left > 0) reads_left--;
    if (mode == 2) { mode = 0; errno = EINTR; return -1; }
    if (mode == 3 && size > 64) size = 64;
    memset(bytes, 0xab, size);
    return (ssize_t)size;
}
#define read fake_read
#endif
#include "src/uuid7_gen.c"
#define PyInit_uuid7_gen test_module_init
#include "uuid7_gen.c"
#undef PyInit_uuid7_gen
static PyObject *fault(PyObject *self, PyObject *args) {
    if (!PyArg_ParseTuple(args, "ii", &reads_left, &mode)) return NULL;
    reset_uuid7_state();
    Py_RETURN_NONE;
}
#ifndef _WIN32
static PyObject *fork_case(PyObject *self, PyObject *arg) {
    long which = PyLong_AsLong(arg);
    if (which == -1 && PyErr_Occurred()) return NULL;
    memset(entropy_pool, 0xab, sizeof(entropy_pool));
    entropy_offset = 0;
    reads_left = 0;
    mode = 0;
    if (which == 0) {
        after_fork_child();
    } else {
        fork_hook_status = which == 1 ? -1 : 0;
        fail_fork_registration = 1;
        process_id = current_process_id() + 1;
    }
    Py_RETURN_NONE;
}
#endif
static PyMethodDef fault_methods[] = {
#ifndef _WIN32
    {"fork_case", fork_case, METH_O, NULL},
#endif
    {"fault", fault, METH_VARARGS, NULL}, {NULL, NULL, 0, NULL}
};
PyMODINIT_FUNC PyInit__uuid_faults(void) {
    PyObject *module = test_module_init();
    if (module != NULL && PyModule_AddFunctions(module, fault_methods) < 0) {
        Py_DECREF(module);
        return NULL;
    }
    return module;
}
"""


@pytest.fixture(scope="session")
def entropy_module(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    build = tmp_path_factory.mktemp("uuid-entropy")
    shutil.copytree(
        root / "uuidv7/uuidv7_impl",
        build / "native",
        ignore=shutil.ignore_patterns("*.so", "*.pyd", "__pycache__"),
    )
    (build / "faults.c").write_text(SOURCE)
    build_system = (
        (root / "pyproject.toml").read_text().split("[build-system]", 1)[1].split("\n[", 1)[0]
    )
    (build / "pyproject.toml").write_text("[build-system]" + build_system)
    (build / "setup.py").write_text(
        "import os\nfrom setuptools import Extension, setup\n"
        "setup(name='uuid-entropy-test', version='0', packages=[], ext_modules=[Extension("
        "'_uuid_faults', ['faults.c'], include_dirs=['native', 'native/include'], "
        "libraries=['bcrypt'] if os.name == 'nt' else ['pthread'])])\n"
    )
    env = os.environ.copy()
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    subprocess.run(
        ["uv", "build", "--wheel", "--python", sys.executable],
        cwd=build,
        env=env,
        check=True,
        timeout=180,
    )
    [wheel] = (build / "dist").glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(build / "installed")
    [extension] = list((build / "installed").glob("*.so")) + list(
        (build / "installed").glob("*.pyd")
    )
    spec = importlib.util.spec_from_file_location("_uuid_faults", extension)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._configure_uuid7(uuid.UUID, uuid.SafeUUID.unknown, uuid.UUID)
    return module


@pytest.mark.parametrize(
    "method",
    ["uuid4", "uuid4_str", "uuid4_bytes", "uuid4_many", "uuid4_str_many", "uuid4_bytes_many"],
)
def test_entropy_failure_returns_no_result_and_can_recover(entropy_module, method):
    module = entropy_module
    call = getattr(module, method)
    args = (300,) if method.endswith("many") else ()
    # Scalar: fail immediately. Batch: exhaust a successful first pool first.
    module.fault(1 if args else 0, 0)
    with pytest.raises(RuntimeError, match="CSPRNG.*v4"):
        call(*args)
    module.fault(-1, 0)
    result = call(*args)
    assert result
    assert module.uuid4().bytes == bytes.fromhex("abababababab4bababababababababab")


@pytest.mark.skipif(os.name == "nt", reason="POSIX read semantics")
@pytest.mark.parametrize("mode", [0, 1, 2, 3])
def test_posix_short_reads_eintr_eof_and_error(entropy_module, mode):
    module = entropy_module
    module.fault(1 if mode in (0, 1) else -1, mode)
    if mode in (0, 1):
        # After one pool, both read errors and EOF must fail, not reuse bytes.
        with pytest.raises(RuntimeError):
            module.uuid4_bytes_many(257)
    else:
        assert len(module.uuid4_bytes_many(300)) == 4800


def test_entropy_sets_only_version_and_variant_bits(entropy_module):
    entropy_module.fault(-1, 0)
    assert entropy_module.uuid4().bytes == bytes.fromhex("abababababab4bababababababababab")


@pytest.mark.skipif(os.name == "nt", reason="POSIX fork hooks")
@pytest.mark.parametrize("case", [0, 1, 2])
def test_child_hook_pid_fallback_and_registration_failure(entropy_module, case):
    entropy_module.fork_case(case)
    with pytest.raises(RuntimeError, match="CSPRNG"):
        entropy_module.uuid4()
    entropy_module.fault(-1, 0)
