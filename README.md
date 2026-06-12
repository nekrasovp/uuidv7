# uuidv7

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
uuid = uuid7()
print(uuid)       # e.g., UUID('018f1234-5678-7abc-def0-123456789abc')
print(str(uuid))  # e.g., "018f1234-5678-7abc-def0-123456789abc"
print(uuid.time)  # Unix timestamp in milliseconds
```

**Note**: Since 0.2.0, `uuid7()` returns a `uuid.UUID` object, matching
Python's built-in `uuid.uuid7()` function available in Python 3.14+. Use
`str(uuid7())` when a string is needed. See
[Python documentation](https://docs.python.org/3/library/uuid.html#uuid.uuid7)
for details.

### Fast Paths

For performance-critical code that does not need a `uuid.UUID` object:

```python
from uuidv7 import uuid7_bytes, uuid7_str

uuid_text = uuid7_str()
uuid_raw = uuid7_bytes()
```

`uuid7()` remains the compatibility API. `uuid7_str()` and `uuid7_bytes()` are
explicit fast paths.

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

Run benchmarks before release and before making speed claims:

```bash
python benchmarks/benchmark.py --output benchmarks/results-0.2.0-local.md
python benchmarks/clock_sources.py --output benchmarks/clock-results-0.2.0-local.md
```

The benchmark reports environment details, UUIDs/second, and ns/op for:

- `uuidv7.uuid7()` returning `uuid.UUID`
- `uuidv7.uuid7_str()`
- `uuidv7.uuid7_bytes()`
- `str(uuidv7.uuid7())`
- Python stdlib `uuid.uuid7()` when available
- published `fastuuid7==0.1.0` in an isolated temporary environment
- optional competitors when installed: `uuid-utils`, `fastuuidv7`, and `uuid7`

The 0.2.0 release should not be tagged or published until benchmark results are
reviewed.

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
  - Can be manually triggered via workflow_dispatch

### Publishing a New Release

1. Run tests, builds, and benchmarks.
2. Review benchmark results and decide whether optimization is needed.
3. Create a new [GitHub Release](https://github.com/nekrasovp/uuidv7/releases/new).
4. The workflow will automatically build and publish to PyPI.

## License

MIT License - see LICENSE file for details.

## Author

Pavel Nekrasov
