# uuidv7

[![CI](https://github.com/yourusername/uuidv7/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/uuidv7/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/fastuuid7.svg)](https://badge.fury.io/py/fastuuid7)

A high-performance UUID v7 generation library implemented in C with Python bindings.

## Features

- Fast UUID v7 generation using C implementation
- RFC 9562 compliant UUID v7 format
- Python 3.8+ support
- Thread-safe implementation
- **High Performance**: See [Performance Benchmarks](#performance-benchmarks) section below

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
git clone https://github.com/yourusername/uuidv7.git
cd uuidv7
uv pip install -e .
```

## Usage

```python
from uuidv7.uuidv7 import generate_uuid7

# Generate a UUID v7
uuid = generate_uuid7()
print(uuid)  # e.g., "018f1234-5678-7abc-def0-123456789abc"
```

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
- **Python Version**: 3.13.11
- **Iterations**: 100,000 UUID generations per implementation

### Performance Summary

| Implementation | UUIDs/sec | Time/UUID (μs) | Relative Speed |
|----------------|-----------|----------------|----------------|
| **Our C Implementation** | **2,556,103** | **0.39** | **1.00x** (baseline) |
| Pure Python Implementation | 229,796 | 4.35 | **11.12x slower** |

### Detailed Results

#### Our C Implementation

- **Throughput**: 2,556,103 UUIDs/second
- **Latency**: 0.39 microseconds per UUID
- **Language**: C with Python bindings

**Performance Characteristics:**
- ✅ Compiled C code for maximum performance
- ✅ Direct system calls (`clock_gettime`) for timestamp generation
- ✅ Minimal Python overhead
- ✅ Thread-safe implementation

#### Pure Python Implementation

- **Throughput**: 229,796 UUIDs/second
- **Latency**: 4.35 microseconds per UUID
- **Language**: Pure Python

**Performance Characteristics:**
- Reference implementation for comparison
- Uses Python's `time.time()` and `random` module
- Higher overhead due to Python interpreter
- Suitable for low-volume use cases

### Speedup Analysis

Our C implementation is **11.12x faster** than the pure Python reference implementation.

This performance advantage comes from:
1. **Compiled code**: C code compiled to native machine code vs interpreted Python
2. **Direct system calls**: Using `clock_gettime()` directly without Python overhead
3. **Efficient memory management**: Pre-allocated buffers, minimal allocations
4. **Optimized string formatting**: Using `snprintf()` efficiently

### Comparison with Other Implementations

#### Python Built-in (`uuid.uuid7`)

- **Status**: ⚠️ Not available
- **Reason**: Requires Python 3.13+ with UUID v7 support
- **Note**: While Python 3.13.11 is installed, the `uuid.uuid7()` function may not be available in all builds

#### uuid7 Library (PyPI)

- **Status**: ⚠️ Not tested
- **Reason**: Library not installed (`pip install uuid7` required)
- **Note**: Would be interesting to compare if installed

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

Additional implementations that may be tested:
- **Python Built-in** (`uuid.uuid7`): Python 3.13+ standard library
- **uuid7 Library**: [PyPI package](https://pypi.org/project/uuid7/)
- **python-uuid7**: [GitHub](https://github.com/0x4b/python-uuid7)

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

1. Update the version in `pyproject.toml` and `uuidv7/uuidv7/__init__.py`
2. Create a new [GitHub Release](https://github.com/yourusername/uuidv7/releases/new)
3. The workflow will automatically build and publish to PyPI

## License

MIT License - see LICENSE file for details.

## Author

Pavel Nekrasov
