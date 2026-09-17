#ifndef UUID7_INT_H
#define UUID7_INT_H

#include <Python.h>
#include <stdint.h>
#include <string.h>

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

/* The bytes API entered the full C API in 3.13 and the Limited API in
 * 3.14. Older ABI floors use public arithmetic instead. */
static PyObject *uuid_words_to_int_portable(uint64_t high, uint64_t low) {
#if PY_VERSION_HEX >= 0x030D0000 && (!defined(Py_LIMITED_API) || Py_LIMITED_API >= 0x030E0000)
#if PY_BIG_ENDIAN
    uint64_t words[2] = {high, low};
#else
    uint64_t words[2] = {low, high};
#endif
    return PyLong_FromUnsignedNativeBytes(
        words, sizeof(words), Py_ASNATIVEBYTES_NATIVE_ENDIAN);
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

static PyObject *uuid_words_to_int(uint64_t high, uint64_t low) {
#if PY_VERSION_HEX >= 0x030E0000 && !defined(Py_LIMITED_API)
    const PyLongLayout *layout = PyLong_GetNativeLayout();
    const uint16_t one = 1;
    const int native_endianness = *(const unsigned char *)&one ? -1 : 1;
    uint32_t digits[5];
    void *buffer;
    PyLongWriter *writer;

    /* Use the documented writer layout, never PyLongObject internals.
     * A different layout remains correct through the public bytes API. */
    if (layout->bits_per_digit != 30 || layout->digit_size != sizeof(uint32_t) ||
        layout->digits_order != -1 || layout->digit_endianness != native_endianness) {
        return uuid_words_to_int_portable(high, low);
    }

    writer = PyLongWriter_Create(0, 5, &buffer);
    if (writer == NULL) {
        return NULL;
    }

    /* Every shift operates on uint64_t and is strictly less than 64.
     * Initialize all digits, including leading zeroes: Finish normalizes. */
    digits[0] = (uint32_t)(low & UINT64_C(0x3fffffff));
    digits[1] = (uint32_t)((low >> 30) & UINT64_C(0x3fffffff));
    digits[2] = (uint32_t)(((low >> 60) | (high << 4)) & UINT64_C(0x3fffffff));
    digits[3] = (uint32_t)((high >> 26) & UINT64_C(0x3fffffff));
    digits[4] = (uint32_t)(high >> 56);
    memcpy(buffer, digits, sizeof(digits));
    return PyLongWriter_Finish(writer);
#elif !defined(Py_LIMITED_API) && PyLong_SHIFT == 30
    /* CPython 3.9-3.13: keep the measured fast path until the public writer
     * is available. No private integer API is compiled on 3.14+. */
#if PY_VERSION_HEX >= 0x030C0000
#define UUIDV7_LONG_DIGITS(op) (((PyLongObject *)(op))->long_value.ob_digit)
#else
#define UUIDV7_LONG_DIGITS(op) (((PyLongObject *)(op))->ob_digit)
#endif
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
#undef UUIDV7_LONG_DIGITS
#else
    return uuid_words_to_int_portable(high, low);
#endif
}

static PyObject *uuid_bytes_to_int(const unsigned char uuid[16]) {
    return uuid_words_to_int(read_u64_be(uuid), read_u64_be(uuid + 8));
}

#endif /* UUID7_INT_H */
