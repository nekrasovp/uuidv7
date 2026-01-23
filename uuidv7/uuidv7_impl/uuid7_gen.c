#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "uuid7_gen.h"

// Import the C implementation function
extern void generate_uuid7(char *uuid);

static PyObject *py_generate_uuid7(PyObject *self, PyObject *args) {
    char uuid[37];
    
    generate_uuid7(uuid);
    
    return PyUnicode_FromString(uuid);
}

static PyMethodDef uuid7_gen_methods[] = {
    {"generate_uuid7", py_generate_uuid7, METH_NOARGS, "Generate a UUID v7"},
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
