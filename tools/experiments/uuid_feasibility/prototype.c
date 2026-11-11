/* Research only. GIL required for Python object access and module globals.
 * Detached parsing owns all input/output buffers; no Python API in that region.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
#ifdef __linux__
#include <sys/random.h>
#endif
#include "parse_core.h"

typedef struct { PyObject_HEAD unsigned char raw[16]; } LabUUID;
static PyTypeObject LabType;
static PyTypeObject *UUIDType;
static PyObject *SafeUnknown, *IntName, *SafeName, *URandom;

static PyObject *raw_int(const unsigned char *raw) {
    /* Same CPython-specific limitation as the existing generator; not abi3. */
    return _PyLong_FromByteArray(raw, 16, 0, 0);
}
static PyObject *make_uuid(const unsigned char *raw, int shape) {
    if (shape == 1) {
        LabUUID *obj = PyObject_New(LabUUID, &LabType);
        if (obj) memcpy(obj->raw, raw, 16);
        return (PyObject *)obj;
    }
    if (shape == 2) return PyBytes_FromStringAndSize((const char *)raw, 16);
    PyObject *n = raw_int(raw);
    if (!n) return NULL;
    PyObject *obj = UUIDType->tp_alloc(UUIDType, 0);
    if (obj && (PyObject_GenericSetAttr(obj, IntName, n) < 0 ||
                PyObject_GenericSetAttr(obj, SafeName, SafeUnknown) < 0)) Py_CLEAR(obj);
    Py_DECREF(n);
    return obj;
}
static int parse_python(PyObject *input, unsigned char out[16]) {
    if (!PyUnicode_Check(input)) {
        PyErr_SetString(PyExc_TypeError, "expected UUID text"); return -1;
    }
    Py_ssize_t n;
    const char *s = PyUnicode_AsUTF8AndSize(input, &n);
    if (!s) return -1;
    if (uuid_parse_core(s, (size_t)n, out)) {
        PyErr_SetString(PyExc_ValueError, "invalid UUID text"); return -1;
    }
    return 0;
}
static PyObject *parse_shape(PyObject *arg, int shape) {
    unsigned char raw[16];
    if (parse_python(arg, raw)) return NULL;
    return make_uuid(raw, shape);
}
#define SCALAR(name, shape) static PyObject *name(PyObject *self, PyObject *arg) { (void)self; return parse_shape(arg, shape); }
SCALAR(parse, 0)
SCALAR(parse_native, 1)
SCALAR(parse_bytes, 2)
static PyObject *from_bytes(PyObject *self, PyObject *arg) {
    (void)self;
    if (!PyBytes_Check(arg)) { PyErr_SetString(PyExc_TypeError, "expected bytes"); return NULL; }
    if (PyBytes_GET_SIZE(arg) != 16) { PyErr_SetString(PyExc_ValueError, "expected 16 bytes"); return NULL; }
    return make_uuid((const unsigned char *)PyBytes_AS_STRING(arg), 0);
}
static PyObject *batch(PyObject *input, int shape, int detach) {
    /* Tuple snapshot isolates list mutation and preserves item ownership. */
    PyObject *seq = PySequence_Tuple(input);
    if (!seq) return NULL;
    Py_ssize_t n = PyTuple_GET_SIZE(seq), bad = -1;
    if (n > PY_SSIZE_T_MAX / 64) { Py_DECREF(seq); return PyErr_NoMemory(); }
    unsigned char *raw = PyMem_Malloc((size_t)(n ? n : 1) * 16);
    char *texts = NULL;
    unsigned char *lengths = NULL;
    PyObject *result = NULL;
    if (!raw) { Py_DECREF(seq); return PyErr_NoMemory(); }
    if (detach) {
        texts = PyMem_Malloc((size_t)(n ? n : 1) * 45);
        lengths = PyMem_Malloc((size_t)(n ? n : 1));
        if (!texts || !lengths) { PyErr_NoMemory(); goto done; }
        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *item = PyTuple_GET_ITEM(seq, i);
            if (!PyUnicode_Check(item)) { bad = i; break; }
            Py_ssize_t len;
            const char *text = PyUnicode_AsUTF8AndSize(item, &len);
            if (!text) goto done;
            if (len > 45) { bad = i; break; }
            lengths[i] = (unsigned char)len;
            memcpy(texts + i * 45, text, (size_t)len);
        }
        if (bad < 0) {
            Py_BEGIN_ALLOW_THREADS
            for (Py_ssize_t i = 0; i < n; i++) {
                if (uuid_parse_core(texts + i * 45, lengths[i], raw + i * 16)) { bad = i; break; }
            }
            Py_END_ALLOW_THREADS
        }
    } else {
        for (Py_ssize_t i = 0; i < n; i++) {
            if (parse_python(PyTuple_GET_ITEM(seq, i), raw + i * 16)) { bad = i; PyErr_Clear(); break; }
        }
    }
    if (bad >= 0) { PyErr_Format(PyExc_ValueError, "invalid UUID at index %zd", bad); goto done; }
    if (shape == 2) result = PyBytes_FromStringAndSize((const char *)raw, n * 16);
    else {
        result = PyList_New(n);
        if (!result) goto done;
        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *obj = make_uuid(raw + i * 16, shape);
            if (!obj) { Py_CLEAR(result); goto done; }
            PyList_SET_ITEM(result, i, obj);
        }
    }
done:
    PyMem_Free(raw); PyMem_Free(texts); PyMem_Free(lengths); Py_DECREF(seq);
    return result;
}
#define BATCH(name, shape, detach) static PyObject *name(PyObject *self, PyObject *arg) { (void)self; return batch(arg, shape, detach); }
BATCH(parse_many, 0, 0)
BATCH(parse_many_native, 1, 0)
BATCH(parse_many_bytes, 2, 0)
BATCH(parse_many_bytes_detach, 2, 1)
static PyObject *native_str(PyObject *obj) {
    char text[36]; uuid_format_core(((LabUUID *)obj)->raw, text, 1);
    return PyUnicode_FromStringAndSize(text, 36);
}
static PyObject *native_hex(PyObject *obj, void *closure) {
    (void)closure; char text[32]; uuid_format_core(((LabUUID *)obj)->raw, text, 0);
    return PyUnicode_FromStringAndSize(text, 32);
}
static PyObject *native_bytes(PyObject *obj, void *closure) {
    (void)closure; return make_uuid(((LabUUID *)obj)->raw, 2);
}
static PyObject *native_int(PyObject *obj, void *closure) {
    (void)closure; return raw_int(((LabUUID *)obj)->raw);
}
static PyObject *native_version(PyObject *obj, void *closure) {
    (void)closure; unsigned char *raw = ((LabUUID *)obj)->raw;
    if ((raw[8] & 0xc0) != 0x80) Py_RETURN_NONE;
    return PyLong_FromLong(raw[6] >> 4);
}
static Py_hash_t native_hash(PyObject *obj) {
    PyObject *n = raw_int(((LabUUID *)obj)->raw);
    if (!n) return -1;
    Py_hash_t h = PyObject_Hash(n); Py_DECREF(n); return h;
}
static PyObject *native_compare(PyObject *left, PyObject *right, int op) {
    PyObject *a = raw_int(((LabUUID *)left)->raw), *b;
    if (!a) return NULL;
    if (PyObject_TypeCheck(right, &LabType)) b = raw_int(((LabUUID *)right)->raw);
    else if (PyObject_TypeCheck(right, UUIDType)) b = PyObject_GetAttr(right, IntName);
    else { Py_DECREF(a); Py_RETURN_NOTIMPLEMENTED; }
    if (!b) { Py_DECREF(a); return NULL; }
    PyObject *result = PyObject_RichCompare(a, b, op); Py_DECREF(a); Py_DECREF(b); return result;
}
static PyGetSetDef getters[] = {
    {"bytes", native_bytes, NULL, NULL, NULL}, {"hex", native_hex, NULL, NULL, NULL},
    {"int", native_int, NULL, NULL, NULL}, {"version", native_version, NULL, NULL, NULL}, {NULL, NULL, NULL, NULL, NULL}
};
static PyTypeObject LabType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_uuid_lab.NativeUUID", .tp_basicsize = sizeof(LabUUID),
    .tp_flags = Py_TPFLAGS_DEFAULT, .tp_str = native_str, .tp_repr = native_str,
    .tp_getset = getters, .tp_hash = native_hash, .tp_richcompare = native_compare
};
static PyObject *uuid4(PyObject *self, PyObject *unused) {
    (void)self; (void)unused;
    /* Deliberately same per-call OS entropy boundary as stdlib, not buffered RNG. */
    PyObject *data = PyObject_CallFunction(URandom, "i", 16);
    if (!data) return NULL;
    if (!PyBytes_Check(data) || PyBytes_GET_SIZE(data) != 16) { Py_DECREF(data); PyErr_SetString(PyExc_RuntimeError, "invalid entropy"); return NULL; }
    unsigned char raw[16]; memcpy(raw, PyBytes_AS_STRING(data), 16); Py_DECREF(data);
    raw[6] = (raw[6] & 15) | 64; raw[8] = (raw[8] & 63) | 128;
    return make_uuid(raw, 0);
}
static PyObject *uuid4_direct(PyObject *self, PyObject *unused) {
    (void)self; (void)unused;
    unsigned char raw[16];
#ifdef __linux__
    size_t offset = 0;
    while (offset < sizeof(raw)) {
        ssize_t n = getrandom(raw + offset, sizeof(raw) - offset, 0);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0) return PyErr_SetFromErrno(PyExc_OSError);
        if (n == 0) { PyErr_SetString(PyExc_OSError, "empty getrandom result"); return NULL; }
        offset += (size_t)n;
    }
#elif defined(__APPLE__)
    arc4random_buf(raw, sizeof(raw));
#else
    PyErr_SetString(PyExc_NotImplementedError, "direct entropy prototype covers Linux/macOS only"); return NULL;
#endif
    raw[6] = (raw[6] & 15) | 64; raw[8] = (raw[8] & 63) | 128;
    return make_uuid(raw, 0);
}
static PyMethodDef methods[] = {
    {"parse", parse, METH_O, NULL}, {"parse_native", parse_native, METH_O, NULL},
    {"parse_bytes", parse_bytes, METH_O, NULL}, {"from_bytes", from_bytes, METH_O, NULL},
    {"parse_many", parse_many, METH_O, NULL}, {"parse_many_native", parse_many_native, METH_O, NULL},
    {"parse_many_bytes", parse_many_bytes, METH_O, NULL},
    {"parse_many_bytes_detach", parse_many_bytes_detach, METH_O, NULL},
    {"uuid4", uuid4, METH_NOARGS, NULL}, {"uuid4_direct", uuid4_direct, METH_NOARGS, NULL}, {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "_uuid_lab", "Isolated research prototype", -1, methods, NULL, NULL, NULL, NULL};
PyMODINIT_FUNC PyInit__uuid_lab(void) {
    if (PyType_Ready(&LabType) < 0) return NULL;
    PyObject *uuid = PyImport_ImportModule("uuid"), *os = NULL, *safe = NULL;
    if (!uuid) return NULL;
    UUIDType = (PyTypeObject *)PyObject_GetAttrString(uuid, "UUID");
    safe = PyObject_GetAttrString(uuid, "SafeUUID"); Py_DECREF(uuid);
    if (!UUIDType || !safe) return NULL;
    SafeUnknown = PyObject_GetAttrString(safe, "unknown"); Py_DECREF(safe);
    IntName = PyUnicode_InternFromString("int"); SafeName = PyUnicode_InternFromString("is_safe");
    os = PyImport_ImportModule("os"); if (!os) return NULL;
    URandom = PyObject_GetAttrString(os, "urandom"); Py_DECREF(os);
    if (!SafeUnknown || !IntName || !SafeName || !URandom) return NULL;
    PyObject *m = PyModule_Create(&module);
    if (m && PyModule_AddObjectRef(m, "NativeUUID", (PyObject *)&LabType) < 0) Py_CLEAR(m);
    return m;
}
