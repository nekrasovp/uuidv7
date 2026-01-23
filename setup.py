"""Setup configuration for uuidv7 package."""

import os

from setuptools import Extension, setup

uuidv7_extension = Extension(
    "uuidv7.uuidv7_impl.uuid7_gen",
    sources=[
        os.path.join("uuidv7", "uuidv7_impl", "uuid7_gen.c"),
        os.path.join("uuidv7", "uuidv7_impl", "src", "uuid7_gen.c"),
    ],
    include_dirs=[os.path.join("uuidv7", "uuidv7_impl", "include")],
    libraries=["rt"],  # For clock_gettime on Linux
)


setup(
    ext_modules=[uuidv7_extension],
)
