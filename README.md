# fastuuid7

[![CI](https://github.com/nekrasovp/uuidv7/actions/workflows/ci.yml/badge.svg)](https://github.com/nekrasovp/uuidv7/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/fastuuid7.svg)](https://badge.fury.io/py/fastuuid7)

A high-performance UUID v7 generation library implemented in C with Python bindings.
The PyPI package is `fastuuid7`; the import package is `uuidv7`.

## Features

- Fast UUID v7 generation using C implementation
- RFC 9562 compliant UUID v7 format
- Python 3.8+ support
- Thread-safe implementation
- `uuid.uuid7()`-compatible API returning `uuid.UUID`
- **High Performance**: See [Performance Benchmarks](#performance-benchmarks) section below
- **Usage Examples**: See [Examples](#examples) section and [`examples/`](examples/) directory

## Installation

### Using uv (recommended)

```bash
uv pip install fastuuid7
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
from uuidv7 import uuid7

# Generate a UUID v7 (matches Python's uuid.uuid7() API)
u = uuid7()
print(u)        # e.g., 018f1234-5678-7abc-def0-123456789abc
print(repr(u))  # e.g., UUID('018f1234-5678-7abc-def0-123456789abc')
print(u.time)   # Unix timestamp in milliseconds
```

**Note**: Since 0.2.0, `uuid7()` returns a `uuid.UUID` object, matching
Python's built-in `uuid.uuid7()` function available in Python 3.14+. Use
`str(uuid7())` when a string is needed. See
[Python documentation](https://docs.python.org/3/library/uuid.html#uuid.uuid7)
for details.

### Fast Paths

For performance-critical code that does not need a `uuid.UUID` object:

```python
from uuidv7 import uuid7_bytes, uuid7_obj, uuid7_str

uuid_native = uuid7_obj()
uuid_text = uuid7_str()
uuid_raw = uuid7_bytes()
```

`uuid7()` remains the compatibility API. `uuid7_obj()` returns a compact native
UUIDv7 object for maximum throughput while still supporting `str()`, `int()`,
`bytes()`, ordering, hashing, `.time`, `.hex`, `.fields`, `.version`, and
`.variant`. `uuid7_str()` and `uuid7_bytes()` are explicit raw-output fast paths.

### Examples

For more detailed usage examples, see the [`examples/`](examples/) directory:

- **[Basic Usage](examples/basic_usage.py)** - Simple UUID generation, validation, and performance demo
- **[Batch Generation](examples/batch_generation.py)** - High-throughput UUID generation and uniqueness verification
- **[Database Usage](examples/database_usage.py)** - Using UUID v7 as primary keys with time-ordered records

**Quick Start:**
```bash
# Install the package first (required)
uv pip install -e .

# Run examples using python -m (recommended)
python -m examples.basic_usage
python -m examples.batch_generation
python -m examples.database_usage

# Or using uv run
uv run python -m examples.basic_usage
```

See the [examples README](examples/README.md) for more details.

## Development

### Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Running Tests

```bash
# Using pytest
uv run pytest

# Using uv
uv run pytest tests/
```

### Linting and Formatting

```bash
# Run ruff linter
uv run ruff check .

# Run ruff formatter
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
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
python benchmarks/clock_sources.py --output clock-source-results.md
```

The benchmark report includes OS, CPU, Python version, package versions,
iterations, UUIDs/second, and ns/op for:

- `uuidv7.uuid7()` returning `uuid.UUID`
- `uuidv7.uuid7_obj()` returning a compact native UUIDv7 object
- `uuidv7.uuid7_str()`
- `uuidv7.uuid7_bytes()`
- `str(uuidv7.uuid7())`
- Python stdlib `uuid.uuid7()` when available
- published `fastuuid7==0.1.0` in an isolated temporary environment
- optional competitors when installed: `uuid-utils`, `fastuuidv7`, `uuid7`,
  `uuid7-rs`, `c_uuid_v7`, `uuid-v7`, and `uuid6`

### Latest Release Benchmark Snapshot

Final release-check benchmark for `0.2.0` on GitHub Actions Ubuntu, x86_64,
CPython 3.14.5:

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| `uuidv7.uuid7_bytes()` | 0.2.0 | 8,651,617 | 115.6 | 1,000,000 |
| `uuidv7.uuid7_str()` | 0.2.0 | 6,701,999 | 149.2 | 1,000,000 |
| `fastuuid7==0.1.0 uuid7()` | 0.1.0 | 2,673,281 | 374.1 | 1,000,000 |
| `uuidv7.uuid7()` | 0.2.0 | 1,922,267 | 520.2 | 1,000,000 |
| `str(uuidv7.uuid7())` | 0.2.0 | 774,285 | 1,291.5 | 1,000,000 |
| `uuid.uuid7()` | 3.14.5 | 396,208 | 2,523.9 | 1,000,000 |

Latest local competitor comparison after the native-object optimization on
Linux x86_64, CPython 3.12.3, using 1,000,000 iterations and 5 rounds per case:

| Shape | Implementation | Version | ops/sec | best ns/op | median ns/op |
| --- | --- | ---: | ---: | ---: | ---: |
| custom object | `c_uuid_v7.uuid7()` | 0.0.11 | 29,313,107 | 34.1 | 34.9 |
| custom object | `uuid7_rs.uuid7()` | 0.0.9 | 28,611,589 | 35.0 | 35.1 |
| custom object | `uuidv7.uuid7_obj()` | 0.2.0 | 28,056,053 | 35.6 | 36.2 |
| bytes | `uuidv7.uuid7_bytes()` | 0.2.0 | 25,474,951 | 39.3 | 39.5 |
| string | `fastuuidv7.uuid7()` | 0.1.5 | 24,702,409 | 40.5 | 40.5 |
| string | `uuidv7.uuid7_str()` | 0.2.0 | 20,895,972 | 47.9 | 48.8 |
| UUID-compatible | `uuidv7.uuid7()` | 0.2.0 | 13,328,017 | 75.0 | 75.6 |
| UUID-compatible | `uuid_utils.uuid7()` | 0.16.1 | 12,215,938 | 81.9 | 82.8 |
| UUID-compatible | `uuid7_rs.compat.uuid7()` | 0.0.9 | 3,258,733 | 306.9 | 310.2 |
| UUID-compatible | `c_uuid_v7.compat.uuid7()` | 0.0.11 | 2,852,392 | 350.6 | 354.5 |

Clock-source benchmark from the final release-check CI run:

| OS | Clock source | ns/call | Iterations |
| --- | --- | ---: | ---: |
| Linux x86_64 | `clock_gettime(CLOCK_REALTIME_COARSE)` | 6.783 | 10,000,000 |
| Linux x86_64 | `clock_gettime(CLOCK_REALTIME)` | 28.664 | 10,000,000 |
| Windows x86_64 | `GetSystemTimeAsFileTime` | 2.218 | 10,000,000 |
| Windows x86_64 | `GetSystemTimePreciseAsFileTime` | 31.240 | 10,000,000 |

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs tests on Python 3.8 through 3.14
  - Runs linting with ruff
  - Builds the package to verify it compiles correctly
  - Triggers on push and pull requests

- **Wheel Pipeline** (`.github/workflows/wheels.yml`):
  - Builds wheels with cibuildwheel for Linux, macOS, and Windows
  - Verifies installed wheels can import `uuidv7` and generate UUIDv7 values

- **Publish Pipeline** (`.github/workflows/publish.yml`):
  - Automatically publishes to PyPI when a new release is created
  - Builds platform wheels with cibuildwheel plus an sdist before publishing
  - Uses trusted publishing (no API tokens required)
  - Can be manually triggered via workflow_dispatch, but GitHub Releases are the recommended release path

### Publishing a New Release

1. Run tests, builds, and benchmarks.
2. Review benchmark results and decide whether optimization is needed.
3. Create a new [GitHub Release](https://github.com/nekrasovp/uuidv7/releases/new).
4. The workflow will automatically build and publish to PyPI.

## License

MIT License - see LICENSE file for details.

## Author

Pavel Nekrasov
