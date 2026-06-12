"""Benchmark wall-clock sources used by UUIDv7 generation."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ITERATIONS = 10_000_000


POSIX_SOURCE = r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static inline uint64_t monotonic_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static inline uint64_t realtime_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)(ts.tv_nsec / 1000000);
}

#ifdef CLOCK_REALTIME_COARSE
static inline uint64_t realtime_coarse_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME_COARSE, &ts);
    return (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)(ts.tv_nsec / 1000000);
}
#endif

static void bench_realtime(int iterations, volatile uint64_t *sink) {
    uint64_t start = monotonic_ns();
    for (int i = 0; i < iterations; ++i) {
        *sink ^= realtime_ms();
    }
    uint64_t end = monotonic_ns();
    printf("clock_gettime(CLOCK_REALTIME),%.3f\n", (double)(end - start) / iterations);
}

#ifdef CLOCK_REALTIME_COARSE
static void bench_realtime_coarse(int iterations, volatile uint64_t *sink) {
    uint64_t start = monotonic_ns();
    for (int i = 0; i < iterations; ++i) {
        *sink ^= realtime_coarse_ms();
    }
    uint64_t end = monotonic_ns();
    printf("clock_gettime(CLOCK_REALTIME_COARSE),%.3f\n", (double)(end - start) / iterations);
}
#endif

int main(int argc, char **argv) {
    int iterations = argc > 1 ? atoi(argv[1]) : 10000000;
    volatile uint64_t sink = 0;
    bench_realtime(iterations, &sink);
#ifdef CLOCK_REALTIME_COARSE
    bench_realtime_coarse(iterations, &sink);
#endif
    if (sink == 42) {
        printf("sink,%llu\n", (unsigned long long)sink);
    }
    return 0;
}
"""


WINDOWS_SOURCE = r"""
#define WIN32_LEAN_AND_MEAN
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

typedef VOID (WINAPI *GetSystemTimePreciseAsFileTimeFn)(LPFILETIME);

static inline uint64_t qpc_ns(LARGE_INTEGER frequency) {
    LARGE_INTEGER counter;
    QueryPerformanceCounter(&counter);
    return (uint64_t)((counter.QuadPart * 1000000000ULL) / frequency.QuadPart);
}

static inline uint64_t filetime_ms(FILETIME ft) {
    ULARGE_INTEGER uli;
    uli.LowPart = ft.dwLowDateTime;
    uli.HighPart = ft.dwHighDateTime;
    return (uli.QuadPart - 116444736000000000ULL) / 10000ULL;
}

static void bench_precise(
    int iterations,
    LARGE_INTEGER frequency,
    GetSystemTimePreciseAsFileTimeFn precise,
    volatile uint64_t *sink
) {
    FILETIME ft;
    uint64_t start = qpc_ns(frequency);
    for (int i = 0; i < iterations; ++i) {
        precise(&ft);
        *sink ^= filetime_ms(ft);
    }
    uint64_t end = qpc_ns(frequency);
    printf("GetSystemTimePreciseAsFileTime,%.3f\n", (double)(end - start) / iterations);
}

static void bench_filetime(int iterations, LARGE_INTEGER frequency, volatile uint64_t *sink) {
    FILETIME ft;
    uint64_t start = qpc_ns(frequency);
    for (int i = 0; i < iterations; ++i) {
        GetSystemTimeAsFileTime(&ft);
        *sink ^= filetime_ms(ft);
    }
    uint64_t end = qpc_ns(frequency);
    printf("GetSystemTimeAsFileTime,%.3f\n", (double)(end - start) / iterations);
}

int main(int argc, char **argv) {
    int iterations = argc > 1 ? atoi(argv[1]) : 10000000;
    volatile uint64_t sink = 0;
    LARGE_INTEGER frequency;
    HMODULE kernel32;
    GetSystemTimePreciseAsFileTimeFn precise = NULL;

    QueryPerformanceFrequency(&frequency);
    kernel32 = GetModuleHandleA("kernel32.dll");
    if (kernel32 != NULL) {
        precise = (GetSystemTimePreciseAsFileTimeFn)GetProcAddress(
            kernel32, "GetSystemTimePreciseAsFileTime"
        );
    }

    if (precise != NULL) {
        bench_precise(iterations, frequency, precise, &sink);
    }
    bench_filetime(iterations, frequency, &sink);
    if (sink == 42) {
        printf("sink,%llu\n", (unsigned long long)sink);
    }
    return 0;
}
"""


@dataclass
class ClockResult:
    source: str
    ns_per_call: float


def compiler_command(source: Path, output: Path) -> list[str]:
    if os.name == "nt":
        cl = shutil.which("cl")
        if cl is None:
            raise RuntimeError("MSVC cl.exe is required on Windows")
        return [cl, "/O2", "/nologo", str(source), f"/Fe:{output}"]

    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if cc is None:
        raise RuntimeError("A C compiler is required")
    return [cc, "-O3", str(source), "-o", str(output)]


def run_benchmark(iterations: int) -> list[ClockResult]:
    with tempfile.TemporaryDirectory(prefix="uuidv7-clock-bench-") as tmp:
        tmpdir = Path(tmp)
        source = tmpdir / ("clock_sources.c")
        output = tmpdir / ("clock_sources.exe" if os.name == "nt" else "clock_sources")
        source.write_text(WINDOWS_SOURCE if os.name == "nt" else POSIX_SOURCE, encoding="utf-8")
        subprocess.run(compiler_command(source, output), check=True, cwd=tmpdir)
        run = subprocess.run(
            [str(output), str(iterations)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            cwd=tmpdir,
        )

    results = []
    for line in run.stdout.splitlines():
        name, value = line.split(",", 1)
        if name != "sink":
            results.append(ClockResult(source=name, ns_per_call=float(value)))
    return results


def environment_markdown() -> str:
    return "\n".join(
        [
            "## Environment",
            "",
            f"- OS: {platform.platform()}",
            f"- Machine: {platform.machine()}",
            f"- CPU: {platform.processor() or 'unknown'}",
            f"- Python: {platform.python_version()}",
        ]
    )


def results_markdown(results: list[ClockResult], iterations: int) -> str:
    lines = [
        "## Results",
        "",
        "| Clock source | ns/call | Iterations |",
        "| --- | ---: | ---: |",
    ]
    for result in sorted(results, key=lambda item: item.ns_per_call):
        lines.append(f"| {result.source} | {result.ns_per_call:,.3f} | {iterations:,} |")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"iterations per source, default {DEFAULT_ITERATIONS}",
    )
    parser.add_argument("--output", type=Path, help="write Markdown results to this path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_benchmark(args.iterations)
    report = "\n\n".join(
        [
            "# UUIDv7 Clock Source Benchmark",
            environment_markdown(),
            results_markdown(results, args.iterations),
        ]
    )
    print(report)
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
        print()
        print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
