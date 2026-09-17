"""Exercise the production C helper with arbitrary unsigned 128-bit inputs.

The temporary extension uses the same isolated build backend as the package.
A C compiler and uv are required; build failures are failures, never skips.
No test-only methods are added to the installed fastuuid7 extension.
"""

import importlib.util
import os
import random
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import fastuuid7

C_SOURCE = r"""
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>

#if PY_VERSION_HEX >= 0x030E0000 && !defined(Py_LIMITED_API)
static int wrong_layout = 0;
static int fail_allocation = 0;
static const PyLongLayout *test_layout(void) {
    static PyLongLayout layout;
    layout = *PyLong_GetNativeLayout();
    if (wrong_layout == 1) layout.bits_per_digit = 15;
    if (wrong_layout == 2) layout.digit_size = 2;
    if (wrong_layout == 3) layout.digits_order *= -1;
    if (wrong_layout == 4) layout.digit_endianness *= -1;
    return &layout;
}
static PyLongWriter *test_create(int negative, Py_ssize_t size, void **digits) {
    if (fail_allocation) {
        PyErr_NoMemory();
        return NULL;
    }
    return PyLongWriter_Create(negative, size, digits);
}
#define PyLong_GetNativeLayout test_layout
#define PyLongWriter_Create test_create
#endif

#include "uuid7_int.h"

static PyObject *words(PyObject *self, PyObject *args) {
    unsigned long long high, low;
    if (!PyArg_ParseTuple(args, "KK", &high, &low)) return NULL;
    return uuid_words_to_int((uint64_t)high, (uint64_t)low);
}
static PyObject *portable(PyObject *self, PyObject *args) {
    unsigned long long high, low;
    if (!PyArg_ParseTuple(args, "KK", &high, &low)) return NULL;
    return uuid_words_to_int_portable((uint64_t)high, (uint64_t)low);
}
static PyObject *from_bytes(PyObject *self, PyObject *args) {
    const char *bytes;
    Py_ssize_t size;
    unsigned char buffer[17];
    if (!PyArg_ParseTuple(args, "y#", &bytes, &size)) return NULL;
    if (size != 16) {
        PyErr_SetString(PyExc_ValueError, "expected 16 bytes");
        return NULL;
    }
    /* A deliberately offset buffer also exercises alignment independence. */
    memcpy(buffer + 1, bytes, 16);
    return uuid_bytes_to_int(buffer + 1);
}
static PyObject *roundtrip_bytes(PyObject *self, PyObject *args) {
    unsigned long long high, low;
    unsigned char bytes[16];
    if (!PyArg_ParseTuple(args, "KK", &high, &low)) return NULL;
    write_u64_be(bytes, (uint64_t)high);
    write_u64_be(bytes + 8, (uint64_t)low);
    return PyBytes_FromStringAndSize((const char *)bytes, 16);
}
#if PY_VERSION_HEX >= 0x030E0000 && !defined(Py_LIMITED_API)
static PyObject *fallback(PyObject *self, PyObject *args) {
    unsigned long long high, low;
    int mismatch;
    if (!PyArg_ParseTuple(args, "KKi", &high, &low, &mismatch)) return NULL;
    wrong_layout = mismatch;
    PyObject *result = uuid_words_to_int((uint64_t)high, (uint64_t)low);
    wrong_layout = 0;
    return result;
}
static PyObject *allocation_error(PyObject *self, PyObject *args) {
    fail_allocation = 1;
    PyObject *result = uuid_words_to_int(UINT64_MAX, UINT64_MAX);
    fail_allocation = 0;
    return result;
}
#endif
static PyMethodDef methods[] = {
    {"words", words, METH_VARARGS, NULL},
    {"portable", portable, METH_VARARGS, NULL},
    {"from_bytes", from_bytes, METH_VARARGS, NULL},
    {"roundtrip_bytes", roundtrip_bytes, METH_VARARGS, NULL},
#if PY_VERSION_HEX >= 0x030E0000 && !defined(Py_LIMITED_API)
    {"fallback", fallback, METH_VARARGS, NULL},
    {"allocation_error", allocation_error, METH_NOARGS, NULL},
#endif
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "MODULE_NAME", NULL, -1, methods
};
PyMODINIT_FUNC PyInit_MODULE_NAME(void) { return PyModule_Create(&module); }
"""


@pytest.fixture(scope="session")
def conversion_modules(tmp_path_factory):
    build = tmp_path_factory.mktemp("int-conversion")
    root = Path(__file__).resolve().parents[1]
    shutil.copyfile(root / "uuidv7/uuidv7_impl/include/uuid7_int.h", build / "uuid7_int.h")
    # Use the project's existing backend requirements, without adding runtime deps.
    pyproject = (root / "pyproject.toml").read_text()
    build_system = pyproject.split("[build-system]", 1)[1].split("\n[", 1)[0]
    (build / "pyproject.toml").write_text("[build-system]" + build_system)
    names = ["_int_conversion_native", "_int_conversion_limited"]
    for name in names:
        prefix = "#define Py_LIMITED_API 0x03090000\n" if name.endswith("limited") else ""
        (build / f"{name}.c").write_text(prefix + C_SOURCE.replace("MODULE_NAME", name))
    (build / "setup.py").write_text(
        "import os\nfrom setuptools import Extension, setup\n"
        f"names = {names!r}\n"
        "setup(name='fastuuid7-int-test', version='0', packages=[], "
        "ext_modules=[Extension(n, [n + '.c'], include_dirs=['.'], "
        "extra_compile_args=['/O2'] if os.name == 'nt' else ['-O3']) for n in names])\n"
    )
    # Avoid inheriting a caller's project selection into the independent harness.
    env = os.environ.copy()
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    subprocess.run(
        ["uv", "build", "--wheel", "--python", sys.executable, "--out-dir", str(build / "dist")],
        cwd=build,
        env=env,
        check=True,
        timeout=180,
    )
    [wheel] = (build / "dist").glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(build / "installed")
    modules = []
    for name in names:
        [binary] = (build / "installed").glob(name + ".*")
        spec = importlib.util.spec_from_file_location(name, binary)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    return modules


MASK64 = (1 << 64) - 1
MAX128 = (1 << 128) - 1
BOUNDARIES = sorted(
    {0, MAX128, 0x0123456789ABCDEFFEDCBA9876543210, 0xFF000000000000000000000000000001}
    | {value for bit in range(128) for value in ((1 << bit) - 1, 1 << bit, (1 << bit) + 1)}
)


@pytest.mark.parametrize("value", BOUNDARIES, ids=lambda value: f"{value:032x}")
def test_exact_unsigned_128_bit_boundaries(conversion_modules, value):
    high, low = value >> 64, value & MASK64
    data = value.to_bytes(16, "big")
    for module in conversion_modules:
        assert module.roundtrip_bytes(high, low) == data
        results = (module.words(high, low), module.from_bytes(data), module.portable(high, low))
        for result in results:
            assert type(result) is int
            assert result == value == int.from_bytes(data, "big")
            assert result >= 0
            assert result.bit_length() == value.bit_length()
            assert result.to_bytes(16, "big") == data
            assert result + 1 == value + 1
            assert hash(result) == hash(value)


def test_random_words_and_big_endian_bytes(conversion_modules):
    rng = random.Random(315)
    for _ in range(4096):
        value = rng.getrandbits(128)
        for module in conversion_modules:
            assert module.words(value >> 64, value & MASK64) == value
            assert module.from_bytes(value.to_bytes(16, "big")) == value


if sys.version_info >= (3, 14):

    @pytest.mark.parametrize("mismatch", [1, 2, 3, 4])
    def test_unrecognized_writer_layout_uses_public_fallback(conversion_modules, mismatch):
        native = conversion_modules[0]
        for value in BOUNDARIES:
            assert native.fallback(value >> 64, value & MASK64, mismatch) == value

    def test_writer_allocation_error_propagates_and_next_call_succeeds(conversion_modules):
        native = conversion_modules[0]
        with pytest.raises(MemoryError):
            native.allocation_error()
        assert native.words(MASK64, MASK64) == MAX128


@pytest.mark.parametrize("timestamp", [0, 1, (1 << 47) - 1, 1 << 47, (1 << 48) - 1])
def test_historical_uuid_integer_consistency(timestamp):
    value = fastuuid7.uuid7_at(unix_ms=timestamp)
    assert value.int == int.from_bytes(value.bytes, "big")
    assert value.int >> 80 == timestamp


def test_live_native_integer_protocols():
    for value in fastuuid7.uuid7_obj_many(256):
        expected = int.from_bytes(value.bytes, "big")
        assert value.int == int(value) == value.__index__() == expected
