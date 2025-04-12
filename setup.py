import os
from setuptools import setup, Extension


uuidv7_extension = Extension(
    'uuidv7_extension.uuid7_gen',
    sources=[
        os.path.join('uuidv7_project', 'src', 'uuid7_gen.c')
    ],
    include_dirs=[
        os.path.join('uuidv7_project', 'include')
    ],
)


setup(
    name='uuidv7-extension',
    version='0.1.0',
    description='UUID v7 generation package using a C library',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Pavel Nekrasov',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/uuidv7_extension',
    ext_modules=[uuidv7_extension],
    packages=['uuidv7_extension'],
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: C',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)