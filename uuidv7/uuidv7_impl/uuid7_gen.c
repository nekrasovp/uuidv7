#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "uuid7_gen.h"

#if defined(Py_LIMITED_API)
static uint64_t read_u64_be(const unsigned char bytes[8]) {
    return ((uint64_t)bytes[0] << 56) |
           ((uint64_t)bytes[1] << 48) |
           ((uint64_t)bytes[2] << 40) |
           ((uint64_t)bytes[3] << 32) |
           ((uint64_t)bytes[4] << 24) |
           ((uint64_t)bytes[5] << 16) |
           ((uint64_t)bytes[6] << 8) |
           (uint64_t)bytes[7];
}
#endif

static PyObject *uuid_bytes_to_int(const unsigned char uuid[16]) {
#if !defined(Py_LIMITED_API)
    return _PyLong_FromByteArray(uuid, 16, 0, 0);
#else
    PyObject *high = NULL;
    PyObject *low = NULL;
    PyObject *shift = NULL;
    PyObject *shifted = NULL;
    PyObject *result = NULL;

    high = PyLong_FromUnsignedLongLong(read_u64_be(uuid));
    if (high == NULL) {
        goto done;
    }

    low = PyLong_FromUnsignedLongLong(read_u64_be(uuid + 8));
    if (low == NULL) {
        goto done;
    }

    shift = PyLong_FromLong(64);
    if (shift == NULL) {
        goto done;
    }

    shifted = PyNumber_Lshift(high, shift);
    if (shifted == NULL) {
        goto done;
    }

    result = PyNumber_Or(shifted, low);

done:
    Py_XDECREF(high);
    Py_XDECREF(low);
    Py_XDECREF(shift);
    Py_XDECREF(shifted);
    return result;
#endif
}

static void format_uuid7(const unsigned char uuid[16], char text[37]) {
    static const char hex[] = "0123456789abcdef";
    int source = 0;
    int target = 0;

    while (source < 16) {
        if (target == 8 || target == 13 || target == 18 || target == 23) {
            text[target++] = '-';
        }
        text[target++] = hex[uuid[source] >> 4];
        text[target++] = hex[uuid[source] & 0x0f];
        source++;
    }
    text[36] = '\0';
}

static PyObject *py_generate_uuid7(PyObject *self, PyObject *args) {
    unsigned char uuid[16];
    char text[37];

    (void)self;
    (void)args;

    generate_uuid7_bytes(uuid);
    format_uuid7(uuid, text);

    return PyUnicode_FromStringAndSize(text, 36);
}

static PyObject *py_generate_uuid7_bytes(PyObject *self, PyObject *args) {
    unsigned char uuid[16];

    (void)self;
    (void)args;

    generate_uuid7_bytes(uuid);

    return PyBytes_FromStringAndSize((const char *)uuid, 16);
}

static PyObject *py_generate_uuid7_int(PyObject *self, PyObject *args) {
    unsigned char uuid[16];

    (void)self;
    (void)args;

    generate_uuid7_bytes(uuid);

    return uuid_bytes_to_int(uuid);
}

static PyObject *py_generate_uuid7_bytes_for_tests(PyObject *self, PyObject *args) {
    unsigned char uuid[16];
    unsigned long long timestamp_ms;

    (void)self;

    if (!PyArg_ParseTuple(args, "K", &timestamp_ms)) {
        return NULL;
    }

    generate_uuid7_bytes_for_timestamp(uuid, (uint64_t)timestamp_ms);

    return PyBytes_FromStringAndSize((const char *)uuid, 16);
}

static PyObject *py_reset_state_for_tests(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;

    reset_uuid7_state();
    Py_RETURN_NONE;
}

static PyMethodDef uuid7_gen_methods[] = {
    {"generate_uuid7", py_generate_uuid7, METH_NOARGS, "Generate a UUID v7 string"},
    {"generate_uuid7_bytes", py_generate_uuid7_bytes, METH_NOARGS, "Generate UUID v7 bytes"},
    {"generate_uuid7_int", py_generate_uuid7_int, METH_NOARGS, "Generate a UUID v7 integer"},
    {
        "_generate_uuid7_bytes_for_tests",
        py_generate_uuid7_bytes_for_tests,
        METH_VARARGS,
        "Generate UUID v7 bytes for a specific timestamp"
    },
    {
        "_reset_state_for_tests",
        py_reset_state_for_tests,
        METH_NOARGS,
        "Reset UUID v7 generator state"
    },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef uuid7_gen_module = {
    PyModuleDef_HEAD_INIT,
    "uuid7_gen",
    NULL,
    -1,
    uuid7_gen_methods
};

PyMODINIT_FUNC PyInit_uuid7_gen(void) {
    return PyModule_Create(&uuid7_gen_module);
}
