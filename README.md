# uuidv7

[![CI](https://github.com/nekrasovp/uuidv7/actions/workflows/ci.yml/badge.svg)](https://github.com/nekrasovp/uuidv7/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/fastuuid7.svg)](https://badge.fury.io/py/fastuuid7)

A high-performance UUID v7 generation library implemented in C with Python bindings.

## Features

- Fast UUID v7 generation using C implementation
- RFC 9562 compliant UUID v7 format
- Python 3.8+ support
- Thread-safe implementation
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
print(uuid)  # e.g., "018f1234-5678-7abc-def0-123456789abc"
```

**Note**: The API matches Python's built-in `uuid.uuid7()` function (available in Python 3.14+). See [Python documentation](https://docs.python.org/3/library/uuid.html#uuid.uuid7) for details.

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

### Latest Results

**Test Environment:**
- **OS**: Linux 6.8.0-90-generic
- **CPU**: 13th Gen Intel(R) Core(TM) i7-1360P
- **Architecture**: x86_64
- **Python Version**: 3.14.2
- **Iterations**: 100,000 UUID generations per implementation

### Performance Summary

| Implementation | UUIDs/sec | Time/UUID (μs) | Relative Speed |
|----------------|-----------|----------------|----------------|
| **Our C Implementation (fastuuid7)** | **501,071** | **2.00** | **1.00x** (baseline) |
| Pure Python Implementation | 48,827 | 20.48 | **10.26x slower** |
| Python Built-in (`uuid.uuid7`) | 47,122 | 21.22 | **10.63x slower** |
| uuid7 Library (PyPI) | 30,263 | 33.04 | **16.56x slower** |

### Detailed Results

#### Our C Implementation (fastuuid7)

- **Throughput**: 501,071 UUIDs/second
- **Latency**: 2.00 microseconds per UUID
- **Language**: C with Python bindings
- **Package**: `fastuuid7` on PyPI

**Performance Characteristics:**
- ✅ Compiled C code for maximum performance
- ✅ Direct system calls (`clock_gettime`) for timestamp generation
- ✅ Minimal Python overhead
- ✅ Thread-safe implementation

#### Pure Python Implementation

- **Throughput**: 48,827 UUIDs/second
- **Latency**: 20.48 microseconds per UUID
- **Language**: Pure Python

**Performance Characteristics:**
- Reference implementation for comparison
- Uses Python's `time.time()` and `random` module
- Higher overhead due to Python interpreter
- Suitable for low-volume use cases

#### Python Built-in (`uuid.uuid7`)

- **Throughput**: 47,122 UUIDs/second
- **Latency**: 21.22 microseconds per UUID
- **Language**: C (Python standard library)
- **Package**: Part of Python 3.14+ standard library
- **Status**: ✅ Tested and benchmarked

**Performance Characteristics:**
- C-based implementation in Python standard library
- Similar performance to pure Python implementations
- Available in Python 3.14+
- Well-integrated with Python ecosystem

#### uuid7 Library (PyPI)

- **Throughput**: 30,263 UUIDs/second
- **Latency**: 33.04 microseconds per UUID
- **Language**: Pure Python
- **Package**: [uuid7 on PyPI](https://pypi.org/project/uuid7/) (installed as `uuid_extensions`)
- **Status**: ✅ Tested and benchmarked

**Performance Characteristics:**
- Pure Python implementation
- Lower performance compared to other implementations
- Well-maintained package on PyPI

### Speedup Analysis

Our C implementation is:
- **10.26x faster** than the pure Python reference implementation
- **10.63x faster** than Python's built-in `uuid.uuid7()` (Python 3.14+)
- **16.56x faster** than the uuid7 library from PyPI

This performance advantage comes from:
1. **Compiled code**: C code compiled to native machine code vs interpreted Python
2. **Direct system calls**: Using `clock_gettime()` directly without Python overhead
3. **Efficient memory management**: Pre-allocated buffers, minimal allocations
4. **Optimized string formatting**: Using `snprintf()` efficiently

### Comparison with Other Implementations

All major implementations have been benchmarked and results are shown in the Performance Summary table above.

### Performance Recommendations

**When to Use Our C Implementation:**
- ✅ High-throughput applications (>100K UUIDs/second)
- ✅ Performance-critical code paths
- ✅ Systems requiring maximum UUID generation speed
- ✅ Applications generating millions of UUIDs

**When to Use Pure Python:**
- ✅ Low-volume use cases (<10K UUIDs/second)
- ✅ Prototyping and development
- ✅ Applications where ease of deployment is more important than performance
- ✅ Environments where C extensions cannot be installed

### Running Benchmarks

To run benchmarks on your system:

```bash
# Install the package in development mode
uv pip install -e .

# Run benchmarks
python benchmarks/benchmark.py

# Or using uv
uv run python benchmarks/benchmark.py
```

### Benchmark Methodology

The benchmark follows these steps:

1. **Warmup Phase**: Each implementation runs 1,000 iterations to warm up CPU caches
2. **Measurement Phase**: 100,000 UUID generations are timed using `time.perf_counter()`
3. **Validation**: Each generated UUID is validated for:
   - Correct length (36 characters)
   - Correct format (4 hyphens)
   - Valid UUID v7 structure (version field = 7, variant field = 8/9/a/b)

**Metrics Calculated:**
- **UUIDs/second**: Throughput metric showing how many UUIDs can be generated per second
- **Time/UUID (μs)**: Latency metric showing microseconds per UUID generation
- **Speedup**: Relative performance compared to the fastest implementation

### Other Implementations

Additional UUID v7 implementations that exist but were not benchmarked in this test:

- **uuid7 Library**: 
  - [PyPI package](https://pypi.org/project/uuid7/)
  - Pure Python implementation
  - See [Comparison with Other Implementations](#comparison-with-other-implementations) section above for status

**Note**: To add these implementations to benchmarks, install them and run `python benchmarks/benchmark.py`. The benchmark script will automatically detect and test available implementations.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs tests on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13
  - Runs linting with ruff
  - Builds the package to verify it compiles correctly
  - Triggers on push and pull requests

- **Publish Pipeline** (`.github/workflows/publish.yml`):
  - Automatically publishes to PyPI when a new release is created
  - Uses trusted publishing (no API tokens required)
  - Can be manually triggered via workflow_dispatch

### Publishing a New Release

1. Update the version in `pyproject.toml` and `uuidv7/__init__.py`
2. Create a new [GitHub Release](https://github.com/nekrasovp/uuidv7/releases/new)
3. The workflow will automatically build and publish to PyPI

## License

MIT License - see LICENSE file for details.

## Author

Pavel Nekrasov
