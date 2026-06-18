#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string.h>
#include "uuid7_gen.h"

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

static void write_u64_be(unsigned char bytes[8], uint64_t value) {
    bytes[0] = (unsigned char)(value >> 56);
    bytes[1] = (unsigned char)(value >> 48);
    bytes[2] = (unsigned char)(value >> 40);
    bytes[3] = (unsigned char)(value >> 32);
    bytes[4] = (unsigned char)(value >> 24);
    bytes[5] = (unsigned char)(value >> 16);
    bytes[6] = (unsigned char)(value >> 8);
    bytes[7] = (unsigned char)value;
}

#if !defined(Py_LIMITED_API)
#if PY_VERSION_HEX >= 0x030C0000
#define UUIDV7_LONG_DIGITS(op) (((PyLongObject *)(op))->long_value.ob_digit)
#else
#define UUIDV7_LONG_DIGITS(op) (((PyLongObject *)(op))->ob_digit)
#endif
#endif

static PyObject *uuid_words_to_int(uint64_t high, uint64_t low) {
#if !defined(Py_LIMITED_API) && PyLong_SHIFT == 30
    digit digits[5];
    Py_ssize_t ndigits = 5;
    PyLongObject *result;
    digit *result_digits;

    digits[0] = (digit)(low & PyLong_MASK);
    digits[1] = (digit)((low >> 30) & PyLong_MASK);
    digits[2] = (digit)(((low >> 60) | ((high & UINT64_C(0x3ffffff)) << 4)) & PyLong_MASK);
    digits[3] = (digit)((high >> 26) & PyLong_MASK);
    digits[4] = (digit)(high >> 56);

    while (ndigits > 0 && digits[ndigits - 1] == 0) {
        ndigits--;
    }

    if (ndigits == 0) {
        return PyLong_FromLong(0);
    }

    result = _PyLong_New(ndigits);
    if (result == NULL) {
        return NULL;
    }

    result_digits = UUIDV7_LONG_DIGITS(result);
    for (Py_ssize_t index = 0; index < ndigits; index++) {
        result_digits[index] = digits[index];
    }

    return (PyObject *)result;
#elif !defined(Py_LIMITED_API)
    unsigned char uuid[16];

    write_u64_be(uuid, high);
    write_u64_be(uuid + 8, low);
    return _PyLong_FromByteArray(uuid, 16, 0, 0);
#else
    PyObject *high_obj = NULL;
    PyObject *low_obj = NULL;
    PyObject *shift = NULL;
    PyObject *shifted = NULL;
    PyObject *result = NULL;

    high_obj = PyLong_FromUnsignedLongLong(high);
    if (high_obj == NULL) {
        goto done;
    }

    low_obj = PyLong_FromUnsignedLongLong(low);
    if (low_obj == NULL) {
        goto done;
    }

    shift = PyLong_FromLong(64);
    if (shift == NULL) {
        goto done;
    }

    shifted = PyNumber_Lshift(high_obj, shift);
    if (shifted == NULL) {
        goto done;
    }

    result = PyNumber_Or(shifted, low_obj);

done:
    Py_XDECREF(high_obj);
    Py_XDECREF(low_obj);
    Py_XDECREF(shift);
    Py_XDECREF(shifted);
    return result;
#endif
}

static PyObject *uuid_bytes_to_int(const unsigned char uuid[16]) {
    return uuid_words_to_int(read_u64_be(uuid), read_u64_be(uuid + 8));
}

static PyObject *uuid7_type = NULL;
static PyObject *uuid7_safe_uuid = NULL;
static PyObject *uuid_int_attr = NULL;
static PyObject *uuid_is_safe_attr = NULL;

typedef struct {
    PyObject_HEAD
    uint64_t high;
    uint64_t low;
} NativeUUID7Object;

static PyTypeObject NativeUUID7Type;

static void format_uuid7(const unsigned char uuid[16], char text[36]) {
    static const char hex[] = "0123456789abcdef";
#define WRITE_HEX_BYTE(target, source)       \
    do {                                     \
        unsigned char byte = uuid[(source)]; \
        text[(target)] = hex[byte >> 4];     \
        text[(target) + 1] = hex[byte & 0x0f]; \
    } while (0)

    WRITE_HEX_BYTE(0, 0);
    WRITE_HEX_BYTE(2, 1);
    WRITE_HEX_BYTE(4, 2);
    WRITE_HEX_BYTE(6, 3);
    text[8] = '-';
    WRITE_HEX_BYTE(9, 4);
    WRITE_HEX_BYTE(11, 5);
    text[13] = '-';
    WRITE_HEX_BYTE(14, 6);
    WRITE_HEX_BYTE(16, 7);
    text[18] = '-';
    WRITE_HEX_BYTE(19, 8);
    WRITE_HEX_BYTE(21, 9);
    text[23] = '-';
    WRITE_HEX_BYTE(24, 10);
    WRITE_HEX_BYTE(26, 11);
    WRITE_HEX_BYTE(28, 12);
    WRITE_HEX_BYTE(30, 13);
    WRITE_HEX_BYTE(32, 14);
    WRITE_HEX_BYTE(34, 15);

#undef WRITE_HEX_BYTE
}

static void format_uuid7_hex(const unsigned char uuid[16], char text[32]) {
    static const char hex[] = "0123456789abcdef";

    for (int index = 0; index < 16; index++) {
        unsigned char byte = uuid[index];
        text[index * 2] = hex[byte >> 4];
        text[index * 2 + 1] = hex[byte & 0x0f];
    }
}

static void uuid_words_to_bytes(uint64_t high, uint64_t low, unsigned char uuid[16]) {
    write_u64_be(uuid, high);
    write_u64_be(uuid + 8, low);
}

static PyObject *uuid_bytes_to_string(const unsigned char uuid[16]) {
#if !defined(Py_LIMITED_API)
    PyObject *result = PyUnicode_New(36, 127);
    char *text;

    if (result == NULL) {
        return NULL;
    }

    text = (char *)PyUnicode_1BYTE_DATA(result);
    format_uuid7(uuid, text);
    return result;
#else
    char text[36];

    format_uuid7(uuid, text);
    return PyUnicode_FromStringAndSize(text, 36);
#endif
}

static PyObject *uuid_words_to_string(uint64_t high, uint64_t low) {
    unsigned char uuid[16];

    uuid_words_to_bytes(high, low, uuid);
    return uuid_bytes_to_string(uuid);
}

static PyObject *uuid_bytes_to_hex(const unsigned char uuid[16]) {
#if !defined(Py_LIMITED_API)
    PyObject *result = PyUnicode_New(32, 127);
    char *text;

    if (result == NULL) {
        return NULL;
    }

    text = (char *)PyUnicode_1BYTE_DATA(result);
    format_uuid7_hex(uuid, text);
    return result;
#else
    char text[32];

    format_uuid7_hex(uuid, text);
    return PyUnicode_FromStringAndSize(text, 32);
#endif
}

static PyObject *uuid_words_to_hex(uint64_t high, uint64_t low) {
    unsigned char uuid[16];

    uuid_words_to_bytes(high, low, uuid);
    return uuid_bytes_to_hex(uuid);
}

static uint64_t uuid_timestamp_ms_from_high(uint64_t high) {
    return high >> 16;
}

static uint64_t uuid_node_from_low(uint64_t low) {
    return low & UINT64_C(0x0000ffffffffffff);
}

static PyObject *native_uuid7_str(PyObject *self) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    return uuid_words_to_string(uuid->high, uuid->low);
}

static PyObject *native_uuid7_repr(PyObject *self) {
    PyObject *text;
    PyObject *result;

    text = native_uuid7_str(self);
    if (text == NULL) {
        return NULL;
    }

    result = PyUnicode_FromFormat("UUID('%U')", text);
    Py_DECREF(text);
    return result;
}

static PyObject *native_uuid7_int_method(PyObject *self, PyObject *Py_UNUSED(args)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    return uuid_words_to_int(uuid->high, uuid->low);
}

static PyObject *native_uuid7_int_unary(PyObject *self) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    return uuid_words_to_int(uuid->high, uuid->low);
}

static PyObject *native_uuid7_bytes_method(PyObject *self, PyObject *Py_UNUSED(args)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    PyObject *result = PyBytes_FromStringAndSize(NULL, 16);

    if (result == NULL) {
        return NULL;
    }

#if !defined(Py_LIMITED_API)
    uuid_words_to_bytes(uuid->high, uuid->low, (unsigned char *)PyBytes_AS_STRING(result));
#else
    {
        char *bytes = PyBytes_AsString(result);
        if (bytes == NULL) {
            Py_DECREF(result);
            return NULL;
        }
        uuid_words_to_bytes(uuid->high, uuid->low, (unsigned char *)bytes);
    }
#endif

    return result;
}

static PyObject *native_uuid7_get_int(PyObject *self, void *Py_UNUSED(closure)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    return uuid_words_to_int(uuid->high, uuid->low);
}

static PyObject *native_uuid7_get_bytes(PyObject *self, void *Py_UNUSED(closure)) {
    return native_uuid7_bytes_method(self, NULL);
}

static PyObject *native_uuid7_get_bytes_le(PyObject *self, void *Py_UNUSED(closure)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    unsigned char bytes_le[16];
    unsigned char bytes[16];

    uuid_words_to_bytes(uuid->high, uuid->low, bytes);
    bytes_le[0] = bytes[3];
    bytes_le[1] = bytes[2];
    bytes_le[2] = bytes[1];
    bytes_le[3] = bytes[0];
    bytes_le[4] = bytes[5];
    bytes_le[5] = bytes[4];
    bytes_le[6] = bytes[7];
    bytes_le[7] = bytes[6];
    memcpy(bytes_le + 8, bytes + 8, 8);

    return PyBytes_FromStringAndSize((const char *)bytes_le, 16);
}

static PyObject *native_uuid7_get_hex(PyObject *self, void *Py_UNUSED(closure)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    return uuid_words_to_hex(uuid->high, uuid->low);
}

static PyObject *native_uuid7_get_time(PyObject *self, void *Py_UNUSED(closure)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    return PyLong_FromUnsignedLongLong(uuid_timestamp_ms_from_high(uuid->high));
}

static PyObject *native_uuid7_get_urn(PyObject *self, void *Py_UNUSED(closure)) {
    PyObject *text;
    PyObject *result;

    text = native_uuid7_str(self);
    if (text == NULL) {
        return NULL;
    }

    result = PyUnicode_FromFormat("urn:uuid:%U", text);
    Py_DECREF(text);
    return result;
}

static PyObject *native_uuid7_get_version(PyObject *self, void *Py_UNUSED(closure)) {
    (void)self;
    return PyLong_FromLong(7);
}

static PyObject *native_uuid7_get_variant(PyObject *self, void *Py_UNUSED(closure)) {
    (void)self;
    return PyUnicode_FromString("specified in RFC 4122");
}

static PyObject *native_uuid7_get_fields(PyObject *self, void *Py_UNUSED(closure)) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    PyObject *result;
    PyObject *item;
    uint32_t time_low;
    uint16_t time_mid;
    uint16_t time_hi_version;
    uint8_t clock_seq_hi_variant;
    uint8_t clock_seq_low;

    result = PyTuple_New(6);
    if (result == NULL) {
        return NULL;
    }

    time_low = (uint32_t)(uuid->high >> 32);
    time_mid = (uint16_t)((uuid->high >> 16) & UINT64_C(0xffff));
    time_hi_version = (uint16_t)(uuid->high & UINT64_C(0xffff));
    clock_seq_hi_variant = (uint8_t)(uuid->low >> 56);
    clock_seq_low = (uint8_t)(uuid->low >> 48);

#define SET_FIELD(index, value)                 \
    do {                                        \
        item = (value);                         \
        if (item == NULL) {                     \
            Py_DECREF(result);                  \
            return NULL;                        \
        }                                       \
        PyTuple_SET_ITEM(result, (index), item); \
    } while (0)

    SET_FIELD(0, PyLong_FromUnsignedLong(time_low));
    SET_FIELD(1, PyLong_FromUnsignedLong(time_mid));
    SET_FIELD(2, PyLong_FromUnsignedLong(time_hi_version));
    SET_FIELD(3, PyLong_FromUnsignedLong(clock_seq_hi_variant));
    SET_FIELD(4, PyLong_FromUnsignedLong(clock_seq_low));
    SET_FIELD(5, PyLong_FromUnsignedLongLong(uuid_node_from_low(uuid->low)));

#undef SET_FIELD

    return result;
}

static Py_hash_t native_uuid7_hash(PyObject *self) {
    NativeUUID7Object *uuid = (NativeUUID7Object *)self;
    Py_uhash_t hash;

    hash = (Py_uhash_t)uuid->high;
    hash ^= (Py_uhash_t)(uuid->high >> 32);
    hash ^= (Py_uhash_t)uuid->low * (Py_uhash_t)1000003UL;
    hash ^= (Py_uhash_t)(uuid->low >> 32);

    if (hash == (Py_uhash_t)-1) {
        hash = (Py_uhash_t)-2;
    }
    return (Py_hash_t)hash;
}

static PyObject *native_uuid7_richcompare(PyObject *left, PyObject *right, int op) {
    int result;
    NativeUUID7Object *left_uuid;
    NativeUUID7Object *right_uuid;

    if (!PyObject_TypeCheck(left, &NativeUUID7Type) ||
        !PyObject_TypeCheck(right, &NativeUUID7Type)) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    left_uuid = (NativeUUID7Object *)left;
    right_uuid = (NativeUUID7Object *)right;

    switch (op) {
        case Py_EQ:
            result = left_uuid->high == right_uuid->high && left_uuid->low == right_uuid->low;
            break;
        case Py_NE:
            result = left_uuid->high != right_uuid->high || left_uuid->low != right_uuid->low;
            break;
        case Py_LT:
            result = left_uuid->high < right_uuid->high ||
                     (left_uuid->high == right_uuid->high && left_uuid->low < right_uuid->low);
            break;
        case Py_LE:
            result = left_uuid->high < right_uuid->high ||
                     (left_uuid->high == right_uuid->high && left_uuid->low <= right_uuid->low);
            break;
        case Py_GT:
            result = left_uuid->high > right_uuid->high ||
                     (left_uuid->high == right_uuid->high && left_uuid->low > right_uuid->low);
            break;
        case Py_GE:
            result = left_uuid->high > right_uuid->high ||
                     (left_uuid->high == right_uuid->high && left_uuid->low >= right_uuid->low);
            break;
        default:
            Py_RETURN_NOTIMPLEMENTED;
    }

    return PyBool_FromLong(result);
}

static int native_uuid7_setattro(PyObject *self, PyObject *name, PyObject *value) {
    (void)self;
    (void)name;
    (void)value;
    PyErr_SetString(PyExc_TypeError, "UUID objects are immutable");
    return -1;
}

static PyMethodDef native_uuid7_methods[] = {
    {"__int__", native_uuid7_int_method, METH_NOARGS, "Return the UUID as an integer"},
    {"__bytes__", native_uuid7_bytes_method, METH_NOARGS, "Return the UUID as bytes"},
    {NULL, NULL, 0, NULL}
};

static PyNumberMethods native_uuid7_as_number = {
    .nb_int = native_uuid7_int_unary,
    .nb_index = native_uuid7_int_unary,
};

static PyGetSetDef native_uuid7_getset[] = {
    {"int", native_uuid7_get_int, NULL, "UUID as a 128-bit integer", NULL},
    {"bytes", native_uuid7_get_bytes, NULL, "UUID as 16 big-endian bytes", NULL},
    {"bytes_le", native_uuid7_get_bytes_le, NULL, "UUID as 16 little-endian field bytes", NULL},
    {"hex", native_uuid7_get_hex, NULL, "UUID as 32 lowercase hexadecimal digits", NULL},
    {"time", native_uuid7_get_time, NULL, "UUIDv7 Unix timestamp in milliseconds", NULL},
    {"timestamp", native_uuid7_get_time, NULL, "UUIDv7 Unix timestamp in milliseconds", NULL},
    {"urn", native_uuid7_get_urn, NULL, "UUID URN", NULL},
    {"version", native_uuid7_get_version, NULL, "UUID version", NULL},
    {"variant", native_uuid7_get_variant, NULL, "UUID variant", NULL},
    {"fields", native_uuid7_get_fields, NULL, "UUID fields tuple", NULL},
    {NULL, NULL, NULL, NULL, NULL}
};

static PyTypeObject NativeUUID7Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "uuidv7.uuidv7_impl.uuid7_gen.UUID7Obj",
    .tp_basicsize = sizeof(NativeUUID7Object),
    .tp_itemsize = 0,
    .tp_repr = native_uuid7_repr,
    .tp_as_number = &native_uuid7_as_number,
    .tp_hash = native_uuid7_hash,
    .tp_str = native_uuid7_str,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "Compact native UUIDv7 object",
    .tp_richcompare = native_uuid7_richcompare,
    .tp_methods = native_uuid7_methods,
    .tp_getset = native_uuid7_getset,
    .tp_setattro = native_uuid7_setattro,
};

static PyObject *py_uuid7_obj(PyObject *self, PyObject *args) {
    NativeUUID7Object *result;

    (void)self;
    (void)args;

    result = PyObject_New(NativeUUID7Object, &NativeUUID7Type);
    if (result == NULL) {
        return NULL;
    }

    generate_uuid7_words(&result->high, &result->low);
    return (PyObject *)result;
}

static PyObject *py_configure_uuid7(PyObject *self, PyObject *const *args, Py_ssize_t nargs) {
    PyObject *new_type;
    PyObject *new_safe_uuid;

    (void)self;

    if (nargs != 2) {
        PyErr_SetString(PyExc_TypeError, "_configure_uuid7() expects uuid type and safe value");
        return NULL;
    }

    new_type = args[0];
    new_safe_uuid = args[1];

    if (!PyType_Check(new_type)) {
        PyErr_SetString(PyExc_TypeError, "uuid type must be a type");
        return NULL;
    }

    Py_INCREF(new_type);
    Py_INCREF(new_safe_uuid);
    Py_XSETREF(uuid7_type, new_type);
    Py_XSETREF(uuid7_safe_uuid, new_safe_uuid);

    Py_RETURN_NONE;
}

static PyObject *py_uuid7(PyObject *self, PyObject *args) {
    unsigned char uuid[16];
    PyObject *value;

    (void)self;
    (void)args;

    if (uuid7_type == NULL || uuid7_safe_uuid == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "uuid7 object fast path is not configured");
        return NULL;
    }

    generate_uuid7_bytes(uuid);
    value = uuid_bytes_to_int(uuid);
    if (value == NULL) {
        return NULL;
    }

#if !defined(Py_LIMITED_API)
    {
        PyObject *uuid_obj = PyType_GenericAlloc((PyTypeObject *)uuid7_type, 0);
        if (uuid_obj == NULL) {
            Py_DECREF(value);
            return NULL;
        }

        if (PyObject_GenericSetAttr(uuid_obj, uuid_int_attr, value) < 0) {
            Py_DECREF(value);
            Py_DECREF(uuid_obj);
            return NULL;
        }
        Py_DECREF(value);

        if (PyObject_GenericSetAttr(uuid_obj, uuid_is_safe_attr, uuid7_safe_uuid) < 0) {
            Py_DECREF(uuid_obj);
            return NULL;
        }

        return uuid_obj;
    }
#else
    {
        PyObject *empty_args = NULL;
        PyObject *kwargs = NULL;
        PyObject *result = NULL;

        empty_args = PyTuple_New(0);
        if (empty_args == NULL) {
            goto done;
        }

        kwargs = PyDict_New();
        if (kwargs == NULL) {
            goto done;
        }

        if (PyDict_SetItemString(kwargs, "int", value) < 0 ||
            PyDict_SetItemString(kwargs, "is_safe", uuid7_safe_uuid) < 0) {
            goto done;
        }

        result = PyObject_Call(uuid7_type, empty_args, kwargs);

done:
        Py_XDECREF(empty_args);
        Py_XDECREF(kwargs);
        Py_DECREF(value);
        return result;
    }
#endif
}

static PyObject *py_generate_uuid7(PyObject *self, PyObject *args) {
    unsigned char uuid[16];

    (void)self;
    (void)args;

    generate_uuid7_bytes(uuid);

#if !defined(Py_LIMITED_API)
    {
        PyObject *result = PyUnicode_New(36, 127);
        char *text;

        if (result == NULL) {
            return NULL;
        }

        text = (char *)PyUnicode_1BYTE_DATA(result);
        format_uuid7(uuid, text);
        return result;
    }
#else
    {
        char text[36];

        format_uuid7(uuid, text);
        return PyUnicode_FromStringAndSize(text, 36);
    }
#endif
}

static PyObject *py_generate_uuid7_bytes(PyObject *self, PyObject *args) {
    PyObject *result;
    char *uuid;

    (void)self;
    (void)args;

    result = PyBytes_FromStringAndSize(NULL, 16);
    if (result == NULL) {
        return NULL;
    }

#if !defined(Py_LIMITED_API)
    uuid = PyBytes_AS_STRING(result);
#else
    uuid = PyBytes_AsString(result);
    if (uuid == NULL) {
        Py_DECREF(result);
        return NULL;
    }
#endif

    generate_uuid7_bytes((unsigned char *)uuid);
    return result;
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
    {"uuid7", py_uuid7, METH_NOARGS, "Generate a UUID v7 uuid.UUID object"},
    {"uuid7_obj", py_uuid7_obj, METH_NOARGS, "Generate a compact native UUID v7 object"},
    {
        "_configure_uuid7",
        (PyCFunction)py_configure_uuid7,
        METH_FASTCALL,
        "Configure the UUID v7 object fast path"
    },
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
    PyObject *module;

    module = PyModule_Create(&uuid7_gen_module);
    if (module == NULL) {
        return NULL;
    }

    if (PyType_Ready(&NativeUUID7Type) < 0) {
        Py_DECREF(module);
        return NULL;
    }

    Py_INCREF(&NativeUUID7Type);
    if (PyModule_AddObject(module, "UUID7Obj", (PyObject *)&NativeUUID7Type) < 0) {
        Py_DECREF(&NativeUUID7Type);
        Py_DECREF(module);
        return NULL;
    }

    uuid_int_attr = PyUnicode_InternFromString("int");
    uuid_is_safe_attr = PyUnicode_InternFromString("is_safe");
    if (uuid_int_attr == NULL || uuid_is_safe_attr == NULL) {
        Py_CLEAR(uuid_int_attr);
        Py_CLEAR(uuid_is_safe_attr);
        Py_DECREF(module);
        return NULL;
    }

    return module;
}
