"""Benchmark script to compare UUID v7 implementations."""

import random
import struct
import sys
import time
from typing import Callable

# Our implementation
from uuidv7 import uuid7 as our_uuid7

# Try to import Python's built-in UUID v7 (Python 3.13+)
try:
    import uuid

    if hasattr(uuid, "uuid7"):

        def python_builtin_uuid7() -> str:
            """Python's built-in UUID v7 (Python 3.13+)."""
            return str(uuid.uuid7())

        HAS_BUILTIN = True
    else:
        HAS_BUILTIN = False
        python_builtin_uuid7 = None
except (AttributeError, ImportError):
    HAS_BUILTIN = False
    python_builtin_uuid7 = None


# Pure Python implementation for comparison
def pure_python_uuid7() -> str:
    """Pure Python UUID v7 implementation."""
    # Get current time in milliseconds
    now_ms = int(time.time() * 1000)

    # Generate random bytes (need 10 bytes for 5 uint16 values)
    rand_bytes = bytes([random.randint(0, 255) for _ in range(10)])

    # Pack timestamp (48 bits) and random (80 bits)
    # Format: timestamp_ms (48 bits) | version (4 bits) | rand_a (12 bits)
    #         variant (2 bits) | rand_b (14 bits) | rand_c (16 bits) | rand_d (16 bits)
    timestamp_high = (now_ms >> 28) & 0xFFFFFFFF
    timestamp_low = (now_ms >> 12) & 0xFFFF

    rand_a = struct.unpack(">H", rand_bytes[0:2])[0] & 0x0FFF | 0x7000
    rand_b = struct.unpack(">H", rand_bytes[2:4])[0] & 0x3FFF | 0x8000
    rand_c = struct.unpack(">H", rand_bytes[4:6])[0]
    rand_d = struct.unpack(">H", rand_bytes[6:8])[0]
    rand_e = struct.unpack(">H", rand_bytes[8:10])[0]

    return f"{timestamp_high:08x}-{timestamp_low:04x}-{rand_a:04x}-{rand_b:04x}-{rand_c:04x}{rand_d:04x}{rand_e:04x}"


# Try to import uuid7 library if available (from uuid_extensions package)
try:
    from uuid_extensions import uuid7 as uuid7_func

    def uuid7_library() -> str:
        """uuid7 library from PyPI (uuid_extensions package)."""
        return str(uuid7_func())

    HAS_UUID7_LIB = True
except ImportError:
    HAS_UUID7_LIB = False
    uuid7_library = None


def benchmark(func: Callable[[], str], name: str, iterations: int = 100000) -> dict:
    """Benchmark a UUID generation function."""
    # Warmup
    for _ in range(1000):
        func()

    # Actual benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        uuid_val = func()
        # Verify it's a valid UUID format
        assert len(uuid_val) == 36
        assert uuid_val.count("-") == 4
    end = time.perf_counter()

    total_time = end - start
    time_per_uuid = total_time / iterations
    uuids_per_second = iterations / total_time

    return {
        "name": name,
        "total_time": total_time,
        "time_per_uuid_us": time_per_uuid * 1_000_000,  # microseconds
        "uuids_per_second": uuids_per_second,
        "iterations": iterations,
    }


def run_benchmarks():
    """Run all benchmarks and print results."""
    iterations = 100000
    print(f"Running benchmarks with {iterations:,} iterations per implementation...")
    print("=" * 80)

    results = []

    # Our C implementation
    print("Benchmarking: Our C Implementation (fastuuid7)...")
    results.append(benchmark(our_uuid7, "Our C Implementation (fastuuid7)", iterations))
    print(f"  ✓ Completed: {results[-1]['uuids_per_second']:,.0f} UUIDs/sec")

    # Python built-in (if available)
    if HAS_BUILTIN:
        print("Benchmarking: Python Built-in (uuid.uuid7)...")
        results.append(benchmark(python_builtin_uuid7, "Python Built-in (uuid.uuid7)", iterations))
        print(f"  ✓ Completed: {results[-1]['uuids_per_second']:,.0f} UUIDs/sec")
    else:
        print("  ⚠ Python built-in UUID v7 not available (requires Python 3.13+)")

    # Pure Python implementation
    print("Benchmarking: Pure Python Implementation...")
    results.append(benchmark(pure_python_uuid7, "Pure Python Implementation", iterations))
    print(f"  ✓ Completed: {results[-1]['uuids_per_second']:,.0f} UUIDs/sec")

    # uuid7 library (if available)
    if HAS_UUID7_LIB:
        print("Benchmarking: uuid7 Library (PyPI)...")
        results.append(benchmark(uuid7_library, "uuid7 Library (PyPI)", iterations))
        print(f"  ✓ Completed: {results[-1]['uuids_per_second']:,.0f} UUIDs/sec")
    else:
        print("  ⚠ uuid7 library not installed (pip install uuid7)")

    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'Implementation':<35} {'UUIDs/sec':>15} {'Time/UUID (μs)':>18}")
    print("-" * 80)

    # Sort by performance
    results.sort(key=lambda x: x["uuids_per_second"], reverse=True)

    for result in results:
        print(
            f"{result['name']:<35} {result['uuids_per_second']:>15,.0f} {result['time_per_uuid_us']:>18.2f}"
        )

    # Calculate speedup
    if len(results) > 1:
        fastest = results[0]
        print("\n" + "=" * 80)
        print("SPEEDUP COMPARISON")
        print("=" * 80)
        for result in results[1:]:
            speedup = fastest["uuids_per_second"] / result["uuids_per_second"]
            print(f"{fastest['name']} is {speedup:.2f}x faster than {result['name']}")

    return results


if __name__ == "__main__":
    try:
        results = run_benchmarks()
        sys.exit(0)
    except Exception as e:
        print(f"Error running benchmarks: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
