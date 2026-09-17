/* Research only. Never compiled by setup.py or imported by fastuuid7.
 * POSIX / CPython >= 3.13. Python objects belong to module state; the exact
 * checked-out generator core belongs to one process-wide native mutex.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#ifdef CLOCK_MONOTONIC_RAW
#define AUDIT_CLOCK CLOCK_MONOTONIC_RAW
#define AUDIT_CLOCK_NAME "CLOCK_MONOTONIC_RAW"
#else
#define AUDIT_CLOCK CLOCK_MONOTONIC
#define AUDIT_CLOCK_NAME "CLOCK_MONOTONIC"
#endif

static int fail_read = 0;
static int interrupt_read = 0;
static int short_read = 0;

static ssize_t experiment_read(int fd, void *buffer, size_t count) {
    if (fail_read) { errno = EIO; return -1; }
    if (interrupt_read) { interrupt_read = 0; errno = EINTR; return -1; }
    if (short_read && count > 17) count = 17;
    return read(fd, buffer, count);
}

/* Include, do not edit/copy, the production algorithm. The build records its
 * digest. Only entropy read fault injection is substituted in this harness.
 */
#define read experiment_read
#include "uuid7_gen.c"
#undef read

static pthread_mutex_t generator_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_once_t fork_once = PTHREAD_ONCE_INIT;
static int fork_registration_error = 0;
static uint64_t serial = 0;

static void lock_generator(void) {
    if (pthread_mutex_lock(&generator_lock) != 0) abort();
}

static void unlock_generator(void) {
    if (pthread_mutex_unlock(&generator_lock) != 0) abort();
}

static void child_after_fork(void) {
    /* prepare acquired the mutex in the thread that forked. No Python API,
     * entropy I/O, memory allocation, or Python object access in handlers.
     */
    reset_process_state((uint64_t)getpid());
    serial = 0;
    fail_read = interrupt_read = short_read = 0;
    unlock_generator();
}

static void register_fork_handlers(void) {
    fork_registration_error = pthread_atfork(
        lock_generator, unlock_generator, child_after_fork
    );
}

static uint64_t monotonic_ns(void) {
    struct timespec value;
    if (clock_gettime(AUDIT_CLOCK, &value) != 0) abort();
    return (uint64_t)value.tv_sec * UINT64_C(1000000000) + value.tv_nsec;
}

typedef struct {
    PyObject *uuid_type;  /* Strong reference, immutable after module exec. */
} ModuleState;

static PyObject *generate(PyObject *self, PyObject *args) {
    Py_ssize_t count = 1;
    long long timestamp = -1;
    int audit = 0, fail_pack = 0, historical = 0, return_gate_fd = -1;
    int status = 0;
    uint64_t first = 0, wait_ns = 0, hold_ns = 0, before = 0, acquired = 0;
    (void)self;
    if (!PyArg_ParseTuple(args, "|nLpppi", &count, &timestamp, &audit,
                          &fail_pack, &historical, &return_gate_fd)) return NULL;
    if (count < 0 || timestamp < -1 || timestamp > (long long)UUID7_MAX_TIMESTAMP ||
        (historical && (timestamp < 0 || audit))) {
        PyErr_SetString(PyExc_ValueError, "invalid count, timestamp, or historical audit");
        return NULL;
    }
    if (count > PY_SSIZE_T_MAX / 16) return PyErr_NoMemory();
    PyObject *result = PyBytes_FromStringAndSize(NULL, count * 16);
    if (result == NULL) return NULL;
    /* Exclusive, unpublished bytes; obtain pointer while attached, then write
     * only raw memory. All refcounting/allocations stay outside native lock.
     */
    unsigned char *buffer = (unsigned char *)PyBytes_AS_STRING(result);
    Py_BEGIN_ALLOW_THREADS
    if (audit) before = monotonic_ns();
    lock_generator();
    if (audit) { acquired = monotonic_ns(); wait_ns = acquired - before; }
    first = serial;
    for (Py_ssize_t index = 0; index < count; index++) {
        if (historical) {
            status = generate_uuid7_at_bytes(buffer + index * 16, (uint64_t)timestamp);
        } else if (timestamp >= 0) {
            status = generate_uuid7_bytes_for_timestamp(buffer + index * 16,
                                                       (uint64_t)timestamp);
        } else {
            status = generate_uuid7_bytes(buffer + index * 16);
        }
        if (status != 0) break;
        if (!historical) serial++;
    }
    if (audit) hold_ns = monotonic_ns() - acquired;
    unlock_generator();
    if (return_gate_fd >= 0) {
        char token;
        ssize_t received;
        do { received = read(return_gate_fd, &token, 1); }
        while (received < 0 && errno == EINTR);
        if (received != 1) status = -1;
    }
    Py_END_ALLOW_THREADS
    if (status != 0 || fail_pack) {
        Py_DECREF(result);
        if (status == UUID7_TIMESTAMP_EXHAUSTED) {
            PyErr_SetString(PyExc_OverflowError, "timestamp exhausted");
        } else if (status != 0) {
            PyErr_SetString(PyExc_OSError, "entropy unavailable");
        } else {
            PyErr_NoMemory();  /* Explicit simulation of result allocation failure. */
        }
        return NULL;
    }
    if (audit) return Py_BuildValue("KNKK", (unsigned long long)first, result,
                                    (unsigned long long)wait_ns,
                                    (unsigned long long)hold_ns);
    return result;
}

static PyObject *reset(PyObject *self, PyObject *args) {
    (void)self; (void)args;
    Py_BEGIN_ALLOW_THREADS
    lock_generator();
    reset_uuid7_state();
    serial = 0;
    fail_read = interrupt_read = short_read = 0;
    unlock_generator();
    Py_END_ALLOW_THREADS
    Py_RETURN_NONE;
}

static PyObject *set_state(PyObject *self, PyObject *args) {
    unsigned long long timestamp, value;
    int status;
    (void)self;
    if (!PyArg_ParseTuple(args, "KK", &timestamp, &value)) return NULL;
    Py_BEGIN_ALLOW_THREADS
    lock_generator();
    status = set_uuid7_state_for_tests(timestamp, value);
    unlock_generator();
    Py_END_ALLOW_THREADS
    if (status < 0) {
        PyErr_SetString(PyExc_ValueError, "invalid generator state");
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *entropy_fault(PyObject *self, PyObject *arg) {
    long mode = PyLong_AsLong(arg);
    (void)self;
    if (mode == -1 && PyErr_Occurred()) return NULL;
    if (mode < 0 || mode > 3) {
        PyErr_SetString(PyExc_ValueError, "fault mode must be 0..3");
        return NULL;
    }
    Py_BEGIN_ALLOW_THREADS
    lock_generator();
    fail_read = mode == 1 || mode == 2;
    interrupt_read = short_read = mode == 3;
    /* Mode 2 leaves one real cached word for a mid-batch/refill failure. */
    entropy_offset = sizeof(entropy_pool);
    if (mode == 2) entropy_offset -= sizeof(uint64_t);
    unlock_generator();
    Py_END_ALLOW_THREADS
    Py_RETURN_NONE;
}

static PyObject *snapshot(PyObject *self, PyObject *args) {
    uint64_t ms, value, pid, ticket;
    size_t offset;
    int init;
    (void)self; (void)args;
    Py_BEGIN_ALLOW_THREADS
    lock_generator();
    ms = last_ms; value = counter; pid = process_id; ticket = serial;
    offset = entropy_offset; init = initialized;
    unlock_generator();
    Py_END_ALLOW_THREADS
    return Py_BuildValue("KKKKni", (unsigned long long)ms, (unsigned long long)value,
                         (unsigned long long)pid, (unsigned long long)ticket,
                         (Py_ssize_t)offset, init);
}

static PyObject *hold_lock(PyObject *self, PyObject *arg) {
    long fd = PyLong_AsLong(arg);
    (void)self;
    if (fd == -1 && PyErr_Occurred()) return NULL;
    Py_BEGIN_ALLOW_THREADS
    lock_generator();
    char token = 'L';
    if (write((int)fd, &token, 1) != 1) abort();
    struct timespec delay = {0, 100000000};
    while (nanosleep(&delay, &delay) != 0 && errno == EINTR) {}
    unlock_generator();
    Py_END_ALLOW_THREADS
    Py_RETURN_NONE;
}

static PyObject *timer_info(PyObject *self, PyObject *args) {
    struct timespec resolution;
    (void)self; (void)args;
    if (clock_getres(AUDIT_CLOCK, &resolution) != 0) return PyErr_SetFromErrno(PyExc_OSError);
    return Py_BuildValue("sK", AUDIT_CLOCK_NAME,
                         (unsigned long long)resolution.tv_sec * UINT64_C(1000000000)
                         + resolution.tv_nsec);
}

static PyObject *cached_type(PyObject *self, PyObject *args) {
    (void)args;
    ModuleState *state = PyModule_GetState(self);
    if (state->uuid_type == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "module not initialized");
        return NULL;
    }
    return Py_NewRef(state->uuid_type);
}

static PyObject *as_uuid(PyObject *self, PyObject *arg) {
    ModuleState *state = PyModule_GetState(self);
    if (state->uuid_type == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "module not initialized");
        return NULL;
    }
    PyObject *positional = PyTuple_New(0);
    if (positional == NULL) return NULL;
    PyObject *kwargs = Py_BuildValue("{s:O}", "bytes", arg);
    PyObject *result = kwargs ? PyObject_Call(state->uuid_type, positional, kwargs) : NULL;
    Py_XDECREF(kwargs);
    Py_DECREF(positional);
    return result;
}

static int module_exec(PyObject *module) {
    ModuleState *state = PyModule_GetState(module);
    int once_status;
    /* This process singleton owns native data only, never a PyObject*. */
    Py_BEGIN_ALLOW_THREADS
    once_status = pthread_once(&fork_once, register_fork_handlers);
    Py_END_ALLOW_THREADS
    if (once_status != 0 || fork_registration_error) {
        PyErr_SetString(PyExc_RuntimeError, "atfork registration failed");
        return -1;
    }
    PyObject *uuid_module = PyImport_ImportModule("uuid");
    if (uuid_module == NULL) return -1;
    state->uuid_type = PyObject_GetAttrString(uuid_module, "UUID");
    Py_DECREF(uuid_module);
    return state->uuid_type == NULL ? -1 : 0;
}

static int module_traverse(PyObject *module, visitproc visit, void *arg) {
    ModuleState *state = PyModule_GetState(module);
    Py_VISIT(state->uuid_type);
    return 0;
}

static int module_clear(PyObject *module) {
    ModuleState *state = PyModule_GetState(module);
    Py_CLEAR(state->uuid_type);
    return 0;
}

static void module_free(void *module) { module_clear((PyObject *)module); }

static PyMethodDef methods[] = {
    {"generate", generate, METH_VARARGS, "Packed UUIDs; optional audit/failed-pack/history flags."},
    {"reset", reset, METH_NOARGS, "Test-only process reset; requires quiescence."},
    {"set_state", set_state, METH_VARARGS, "Test-only state injection; requires quiescence."},
    {"entropy_fault", entropy_fault, METH_O, "Test-only entropy fault injection."},
    {"snapshot", snapshot, METH_NOARGS, "Read native state under its mutex."},
    {"hold_lock", hold_lock, METH_O, "Signal a pipe while holding the lock for a fork probe."},
    {"timer_info", timer_info, METH_NOARGS, "Native audit clock and nominal resolution."},
    {"cached_type", cached_type, METH_NOARGS, "Return this module's owned UUID type."},
    {"as_uuid", as_uuid, METH_O, "Construct via this module's owned UUID type."},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef_Slot slots[] = {
    {Py_mod_exec, module_exec},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {0, NULL}
};

static struct PyModuleDef definition = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_ft_uuid7",
    .m_doc = "Isolated POSIX research prototype, not a supported fastuuid7 API.",
    .m_size = sizeof(ModuleState),
    .m_methods = methods,
    .m_slots = slots,
    .m_traverse = module_traverse,
    .m_clear = module_clear,
    .m_free = module_free
};

PyMODINIT_FUNC PyInit__ft_uuid7(void) { return PyModuleDef_Init(&definition); }
