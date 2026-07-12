# fastuuid7

[![CI](https://github.com/nekrasovp/uuidv7/actions/workflows/ci.yml/badge.svg)](https://github.com/nekrasovp/uuidv7/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/fastuuid7.svg)](https://badge.fury.io/py/fastuuid7)
[![Python versions](https://img.shields.io/pypi/pyversions/fastuuid7.svg)](https://pypi.org/project/fastuuid7/)
[![License](https://img.shields.io/pypi/l/fastuuid7.svg)](LICENSE)

High-performance, fork-safe UUIDv7 generation for Python 3.9-3.14, implemented
in C and compatible with Python's `uuid.UUID` API.

## Features

- RFC 9562 UUIDv7 layout with monotonic ordering within a millisecond
- Random fields sourced from the operating-system CSPRNG
- Automatic entropy and counter reset after a process fork
- `uuid.uuid7()`-compatible API returning `uuid.UUID`
- Native object, canonical string, and raw bytes fast paths
- Python 3.9-3.14 on Linux, macOS, and Windows
- Typed `fastuuid7` and backward-compatible `uuidv7` imports

Python 3.14 includes `uuid.uuid7()` in the standard library. Use the standard
library when it meets your needs. `fastuuid7` is intended for older Python
versions and workloads that benefit from its explicit output shapes and lower
per-call overhead.

## Installation

### Using uv

```bash
uv add fastuuid7
```

### Using pip

```bash
pip install fastuuid7
```

### From source

```bash
git clone https://github.com/nekrasovp/uuidv7.git
cd uuidv7
uv pip install -e .
```

## Usage

### Basic Usage

```python
from fastuuid7 import uuid7

# Generate a UUID v7 (matches Python's uuid.uuid7() API)
u = uuid7()
print(u)        # e.g., 018f1234-5678-7abc-def0-123456789abc
print(repr(u))  # e.g., UUID('018f1234-5678-7abc-def0-123456789abc')
print(u.time)   # Unix timestamp in milliseconds
```

`uuid7()` returns a `uuid.UUID` object, matching Python's built-in
`uuid.uuid7()` function available in Python 3.14+. Use `str(uuid7())` when a
string is needed. See
[Python documentation](https://docs.python.org/3/library/uuid.html#uuid.uuid7)
for details.

### Fast Paths

For performance-critical code that does not need a `uuid.UUID` object:

```python
from fastuuid7 import (
    uuid7_bytes,
    uuid7_bytes_many,
    uuid7_many,
    uuid7_obj,
    uuid7_str,
)

uuid_native = uuid7_obj()
uuid_text = uuid7_str()
uuid_raw = uuid7_bytes()
uuid_batch = uuid7_many(1_000)
packed_batch = uuid7_bytes_many(1_000)  # 16,000 contiguous bytes
```

`uuid7()` remains the compatibility API. `uuid7_obj()` returns a compact native
UUIDv7 object for maximum throughput while still supporting `str()`, `int()`,
`bytes()`, ordering, hashing, `.time`, `.hex`, `.fields`, `.version`, and
`.variant`. `uuid7_str()` and `uuid7_bytes()` are explicit raw-output fast
paths. The `*_many()` functions generate a batch in one C call;
`uuid7_bytes_many()` uses one contiguous `bytes` allocation.

The original `from uuidv7 import ...` path remains supported for existing
applications.

See the [API reference](docs/api.md) for complete scalar and batch contracts.

### Security properties

Random fields are read from a buffered operating-system CSPRNG. The generator
detects PID changes and discards inherited entropy and counters after `fork()`.
UUIDv7 embeds its creation timestamp and is therefore an identifier, not a
secret or authentication token. See the [security policy](SECURITY.md).

### Examples

For more detailed usage examples, see the [`examples/`](examples/) directory:

- **[Basic Usage](examples/basic_usage.py)** - Simple UUID generation, validation, and performance demo
- **[Batch Generation](examples/batch_generation.py)** - High-throughput UUID generation and uniqueness verification
- **[Database Usage](examples/database_usage.py)** - Real SQLAlchemy 2 primary-key integration
- **[Integration Recipes](docs/integrations.md)** - Django, Pydantic/FastAPI, and PostgreSQL

**Quick Start:**
```bash
# Install the package first (required)
uv pip install -e .

# Run examples using python -m (recommended)
python -m examples.basic_usage
python -m examples.batch_generation
uv run --with sqlalchemy python -m examples.database_usage

# Or using uv run
uv run python -m examples.basic_usage
```

See the [examples README](examples/README.md) for more details.

## Development

### Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the project and development dependencies
uv sync --extra dev
```

### Running Tests

```bash
# Using pytest
uv run --extra dev pytest

# Using uv
uv run --extra dev pytest tests/
```

### Linting and Formatting

```bash
# Run ruff linter
uv run --extra dev ruff check .

# Run ruff formatter
uv run --extra dev ruff format .

# Fix auto-fixable issues
uv run --extra dev ruff check --fix .

# Check the typed public API
uv run --extra dev mypy
```

### Building

```bash
# Build wheel
uv build

# Build source distribution
uv build --sdist
```

### Running Benchmarks

```bash
# Run performance benchmarks comparing different implementations
python benchmarks/benchmark.py

# Or using uv
uv run python benchmarks/benchmark.py
```

## Performance Benchmarks

Run benchmarks before making speed claims:

```bash
python benchmarks/benchmark.py --output benchmark-results.md
python benchmarks/benchmark_competitors.py --install-optional --rounds 5 --output competitor-results.md
python benchmarks/benchmark_batch.py --output batch-results.md
python benchmarks/clock_sources.py --output clock-source-results.md
```

The benchmark report includes OS, CPU, Python version, package versions,
iterations, UUIDs/second, and ns/op for:

- `fastuuid7.uuid7()` returning `uuid.UUID`
- `fastuuid7.uuid7_obj()` returning a compact native UUIDv7 object
- `fastuuid7.uuid7_str()`
- `fastuuid7.uuid7_bytes()`
- `str(fastuuid7.uuid7())`
- Python stdlib `uuid.uuid7()` when available
- published `fastuuid7==0.1.0` in an isolated temporary environment
- optional competitors when installed: `uuid-utils`, `fastuuidv7`, `uuid7`,
  `uuid7-rs`, `c_uuid_v7`, `uuid-v7`, and `uuid6`

Published benchmark results must describe both the output shape and generation
guarantees. In particular, CSPRNG-backed and non-cryptographic generators are
not presented as equivalent cases. Release benchmarks are generated in CI from
the exact release candidate rather than copied from a developer workstation.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs tests on Python 3.9 through 3.14
  - Runs linting with ruff
  - Builds the package to verify it compiles correctly
  - Triggers on push and pull requests

- **Wheel Pipeline** (`.github/workflows/wheels.yml`):
  - Builds glibc and musl Linux wheels for x86-64 and ARM64
  - Builds macOS x86-64/ARM64 and Windows x86/x86-64/ARM64 wheels
  - Verifies both import paths and the installed batch API

- **Publish Pipeline** (`.github/workflows/publish.yml`):
  - Automatically publishes to PyPI when a new release is created
  - Builds platform wheels with cibuildwheel plus an sdist before publishing
  - Uses trusted publishing (no API tokens required)
  - Can be manually triggered via workflow_dispatch, but GitHub Releases are the recommended release path

### Publishing a New Release

Follow the complete [release checklist](docs/releasing.md), including the
security-advisory order for 0.3.0.

1. Run tests, builds, and benchmarks.
2. Review benchmark results and decide whether optimization is needed.
3. Verify all source versions with `python tools/check_release_version.py v0.3.0`.
4. Create a new [GitHub Release](https://github.com/nekrasovp/uuidv7/releases/new).
5. The workflow will validate, build, inspect, and publish the distributions.

## License

MIT License - see LICENSE file for details.

## Author

Pavel Nekrasov
