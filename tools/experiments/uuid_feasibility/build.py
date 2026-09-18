"""Build only the standalone experiment, never the production extension."""

import os
from pathlib import Path

from setuptools import Extension, setup

os.chdir(Path(__file__).resolve().parent)
setup(
    name="uuid-lab-prototype",
    version="0.0.0",
    ext_modules=[
        Extension("_uuid_lab", ["prototype.c"], extra_compile_args=["-O3", "-Wall", "-Wextra"])
    ],
    script_args=["build_ext", "--inplace"],
)
