"""Setup configuration for uuidv7 package."""

import os

from setuptools import Extension, setup

extra_compile_args = ["/O2"] if os.name == "nt" else ["-O3"]

uuidv7_extension = Extension(
    "uuidv7.uuidv7_impl.uuid7_gen",
    sources=[
        os.path.join("uuidv7", "uuidv7_impl", "uuid7_gen.c"),
        os.path.join("uuidv7", "uuidv7_impl", "src", "uuid7_gen.c"),
    ],
    include_dirs=[os.path.join("uuidv7", "uuidv7_impl", "include")],
    extra_compile_args=extra_compile_args,
    libraries=["bcrypt"] if os.name == "nt" else [],
)

setup(
    ext_modules=[uuidv7_extension],
)
