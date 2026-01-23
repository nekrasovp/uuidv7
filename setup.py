"""Setup configuration for uuidv7 package."""

import os

from setuptools import Extension, setup
from wheel.bdist_wheel import bdist_wheel


class BinaryDistribution(bdist_wheel):
    """Custom bdist_wheel to fix platform tag."""

    def finalize_options(self):
        bdist_wheel.finalize_options(self)
        # Mark as not pure to allow platform-specific wheels
        self.root_is_pure = False

    def get_tag(self):
        """Override tag to use manylinux instead of linux_x86_64."""
        python, abi, plat = bdist_wheel.get_tag(self)
        # Replace linux_x86_64 with manylinux2014_x86_64 for PyPI compatibility
        if plat.startswith("linux_"):
            plat = plat.replace("linux_", "manylinux2014_")
        return python, abi, plat


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
    cmdclass={"bdist_wheel": BinaryDistribution},
)
