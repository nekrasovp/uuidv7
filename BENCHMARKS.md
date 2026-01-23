# UUID v7 Performance Benchmarks

This document compares the performance of different UUID v7 implementations, including our C-based implementation, Python's built-in UUID v7 (Python 3.13+), and other popular implementations.

## Table of Contents

- [Methodology](#methodology)
- [Implementations Compared](#implementations-compared)
- [Benchmark Results](#benchmark-results)
- [Analysis](#analysis)
- [Running Benchmarks](#running-benchmarks)

## Methodology

### Test Environment

- **CPU**: Tested on various systems (see individual results)
- **Python Version**: Python 3.8+ (with Python 3.13+ for built-in UUID v7)
- **Iterations**: 100,000 UUID generations per implementation
- **Warmup**: 1,000 iterations before actual timing
- **Measurement**: Uses `time.perf_counter()` for high-precision timing

### Benchmark Process

1. **Warmup Phase**: Each implementation runs 1,000 iterations to warm up caches
2. **Measurement Phase**: 100,000 UUID generations are timed
3. **Metrics Calculated**:
   - Total time (seconds)
   - Time per UUID (microseconds)
   - UUIDs per second (throughput)

### Validation

All implementations are validated to ensure:
- Correct UUID format (36 characters, 4 hyphens)
- Valid UUID v7 structure (version field = 7, variant field = 8/9/a/b)

## Implementations Compared

### 1. Our C Implementation (`uuidv7`)

- **Language**: C with Python bindings
- **Repository**: This repository
- **Description**: High-performance C implementation using `clock_gettime()` for timestamp generation
- **Features**: Thread-safe, RFC 9562 compliant

### 2. Python Built-in (`uuid.uuid7`)

- **Language**: Python (C implementation)
- **Availability**: Python 3.13+
- **Description**: Python's standard library UUID v7 implementation
- **Features**: Part of Python standard library, RFC 9562 compliant

### 3. Pure Python Implementation

- **Language**: Pure Python
- **Description**: Reference implementation for comparison
- **Features**: Simple implementation using `time.time()` and `random`

### 4. uuid7 Library (PyPI)

- **Language**: Python
- **Package**: `uuid7` on PyPI
- **Repository**: [https://github.com/ytorg/uuid7](https://github.com/ytorg/uuid7)
- **Description**: Pure Python UUID v7 implementation
- **Installation**: `pip install uuid7`

### 5. Other Implementations

Additional implementations may be tested if available:
- **python-uuid7**: [https://github.com/0x4b/python-uuid7](https://github.com/0x4b/python-uuid7)
- **fastuuid**: [https://github.com/fastuuid/fastuuid](https://github.com/fastuuid/fastuuid) (if UUID v7 support exists)

## Benchmark Results

### Latest Results

For actual benchmark results from a real system, see **[BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md)**.

### Example Results (Linux, x86_64)

| Implementation | UUIDs/sec | Time/UUID (μs) | Speedup vs Slowest |
|----------------|-----------|----------------|---------------------|
| **Our C Implementation** | ~2,500,000 | 0.40 | **1.00x** (baseline) |
| Python Built-in (3.13+) | ~1,800,000 | 0.56 | 1.39x slower |
| Pure Python | ~150,000 | 6.67 | 16.67x slower |
| uuid7 Library (PyPI) | ~200,000 | 5.00 | 12.50x slower |

*Note: Actual results vary by system. Run benchmarks locally for your environment. See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) for real-world results.*

### Performance Characteristics

#### Our C Implementation

**Strengths:**
- ✅ Fastest implementation (C compiled code)
- ✅ Minimal overhead (direct system calls)
- ✅ Efficient memory usage
- ✅ Thread-safe

**Trade-offs:**
- Requires compilation (C extension)
- Platform-specific (needs `librt` on Linux)

#### Python Built-in (`uuid.uuid7`)

**Strengths:**
- ✅ Part of standard library (no dependencies)
- ✅ Well-tested and maintained
- ✅ Good performance (C implementation)
- ✅ Cross-platform

**Trade-offs:**
- Requires Python 3.13+ (not available in older versions)
- Slightly slower than our optimized C implementation

#### Pure Python Implementations

**Strengths:**
- ✅ No compilation required
- ✅ Easy to understand and modify
- ✅ Works on all Python versions

**Trade-offs:**
- ❌ Significantly slower (10-20x)
- ❌ Python interpreter overhead
- ❌ GIL limitations for concurrent generation

## Analysis

### Why Our Implementation is Faster

1. **Direct System Calls**: Uses `clock_gettime()` directly without Python overhead
2. **Compiled Code**: C code compiled to native machine code
3. **Minimal Allocations**: Pre-allocated buffers, minimal memory allocations
4. **Optimized String Formatting**: Uses `snprintf()` efficiently

### Performance Scaling

For high-throughput scenarios (1M+ UUIDs/second):
- **Our C Implementation**: Recommended for maximum performance
- **Python Built-in**: Good alternative if Python 3.13+ is available
- **Pure Python**: Suitable for low-volume use cases (< 10K UUIDs/second)

### Memory Usage

- **Our C Implementation**: ~37 bytes per UUID (string allocation)
- **Python Built-in**: Similar, with Python object overhead
- **Pure Python**: Higher overhead due to Python objects

## Running Benchmarks

### Prerequisites

```bash
# Install the package in development mode
uv pip install -e .

# Install optional dependencies for comparison
pip install uuid7  # Optional: for uuid7 library comparison
```

### Run Benchmarks

```bash
# Run the benchmark script
python benchmarks/benchmark.py

# Or using uv
uv run python benchmarks/benchmark.py
```

### Expected Output

```
Running benchmarks with 100,000 iterations per implementation...
================================================================================
Benchmarking: Our C Implementation...
  ✓ Completed: 2,500,000 UUIDs/sec
Benchmarking: Python Built-in (uuid.uuid7)...
  ✓ Completed: 1,800,000 UUIDs/sec
Benchmarking: Pure Python Implementation...
  ✓ Completed: 150,000 UUIDs/sec
================================================================================
RESULTS SUMMARY
================================================================================
Implementation                        UUIDs/sec   Time/UUID (μs)
--------------------------------------------------------------------------------
Our C Implementation                 2,500,000             0.40
Python Built-in (uuid.uuid7)        1,800,000             0.56
Pure Python Implementation            150,000             6.67
```

### Customizing Benchmarks

Edit `benchmarks/benchmark.py` to:
- Change iteration count
- Add more implementations
- Modify warmup iterations
- Add additional metrics

## Contributing Benchmarks

If you have benchmark results from different systems or implementations, please:

1. Run the benchmark script on your system
2. Document your system specifications (CPU, OS, Python version)
3. Submit results via issue or pull request

### System Information Template

```markdown
## System: [Your System Name]

- **OS**: [e.g., Linux Ubuntu 22.04]
- **CPU**: [e.g., Intel i7-12700K]
- **Python Version**: [e.g., 3.13.0]
- **Architecture**: [e.g., x86_64]

### Results

| Implementation | UUIDs/sec | Time/UUID (μs) |
|----------------|-----------|----------------|
| Our C Implementation | X | Y |
| Python Built-in | X | Y |
| ... | ... | ... |
```

## References

- [RFC 9562 - UUID Version 7](https://www.rfc-editor.org/rfc/rfc9562.html)
- [Python uuid module documentation](https://docs.python.org/3/library/uuid.html)
- [uuid7 PyPI package](https://pypi.org/project/uuid7/)
- [python-uuid7 GitHub](https://github.com/0x4b/python-uuid7)

## License

Benchmark results and methodology are provided under the same license as this project (MIT).

