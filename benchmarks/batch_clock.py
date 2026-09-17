"""Measure batch clock caching with the real CSPRNG/counter core, plus a pause probe.

This experiment does not change the production clock policy. Compile the exact
checkout's core into a standalone harness so Python call overhead cannot hide
the clock cost. Includes OS randomness, PID checks, and identical byte output.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
#include <stdio.h>
#include <stdlib.h>
#include "uuid7_core.c"

static double monotonic_ns(void) {
#ifdef _WIN32
    LARGE_INTEGER counter, frequency;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&counter);
    return (double)counter.QuadPart * 1e9 / (double)frequency.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
#endif
}
static uint64_t timestamp(const unsigned char *u) {
    uint64_t ms = 0;
    for (int i = 0; i < 6; ++i) ms = (ms << 8) | u[i];
    return ms;
}
int main(int argc, char **argv) {
    int n = argc > 1 ? atoi(argv[1]) : 1000000;
    int rounds = argc > 2 ? atoi(argv[2]) : 5;
    if (n < 1 || rounds < 1) return 2;
    int strides[] = {1, 32, 256, n};
    volatile unsigned char sink = 0;
    unsigned char u[16];
    for (int round = 0; round < rounds; ++round) {
        /* Rotate order to reduce systematic warmup/frequency bias. */
        for (int j = 0; j < 4; ++j) {
            int stride = strides[(j + round) % 4];
            reset_uuid7_state();
            for (int warm = 0; warm < 2000; ++warm) {
                if (generate_uuid7_bytes(u) < 0) return 3;
            }
            uint64_t cached_ms = 0;
            double start = monotonic_ns();
            for (int i = 0; i < n; ++i) {
                if (i % stride == 0) cached_ms = current_time_ms();
                if (generate_uuid7_bytes_for_timestamp(u, cached_ms) < 0) return 3;
                sink ^= u[15];
            }
            double ns = (monotonic_ns() - start) / n;
            printf("timing,%d,%.3f\n", stride, ns);
        }
    }
    reset_uuid7_state();
    uint64_t cached_ms = current_time_ms();
#ifdef _WIN32
    Sleep(25);
#else
    struct timespec pause = {0, 25000000};
    while (nanosleep(&pause, &pause) != 0) {}
#endif
    if (generate_uuid7_bytes_for_timestamp(u, cached_ms) < 0) return 3;
    uint64_t old_ms = timestamp(u);
    uint64_t observed_ms = current_time_ms();
    printf("pause_cached_lag_ms,%llu\n", (unsigned long long)(observed_ms - old_ms));
    if (generate_uuid7_bytes(u) < 0) return 3;
    uint64_t fresh_ms = timestamp(u);
    printf("pause_fresh_lag_ms,%llu\n", (unsigned long long)(current_time_ms() - fresh_ms));
    if (fresh_ms < observed_ms || old_ms != cached_ms) return 4;
    if (sink == 255) fprintf(stderr, "sink=255\n");
    return 0;
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--iterations", type=int, default=1_000_000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.iterations < 257 or args.rounds < 1:
        parser.error("iterations must be >= 257 and rounds >= 1")
    with tempfile.TemporaryDirectory(prefix="uuidv7-clock-") as directory:
        work = Path(directory)
        source = ROOT / "uuidv7/uuidv7_impl"
        shutil.copy(source / "src/uuid7_gen.c", work / "uuid7_core.c")
        shutil.copy(source / "include/uuid7_gen.h", work / "uuid7_gen.h")
        (work / "harness.c").write_text(HARNESS)
        executable = work / ("harness.exe" if os.name == "nt" else "harness")
        if os.name == "nt":
            command = ["cl", "/nologo", "/O2", "harness.c", "bcrypt.lib", f"/Fe:{executable}"]
        else:
            command = [
                os.environ.get("CC", "cc"),
                "-O3",
                "-std=c11",
                "-D_POSIX_C_SOURCE=200809L",
                "harness.c",
                "-o",
                str(executable),
            ]
        subprocess.run(command, cwd=work, check=True, capture_output=True)
        output = subprocess.check_output(
            [str(executable), str(args.iterations), str(args.rounds)], text=True
        )
    timings, observations = {}, {}
    for line in output.splitlines():
        parts = line.split(",")
        if parts[0] == "timing":
            timings.setdefault(int(parts[1]), []).append(float(parts[2]))
        else:
            observations[parts[0]] = int(parts[1])
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode != 0
    lines = [
        "# Batch clock experiment",
        "",
        f"Commit: `{sha}`",
        f"Tracked source changes: {dirty}",
        f"Platform: {platform.platform()}",
        f"Compiler command: {' '.join(command[:-2])}",
        f"Iterations: {args.iterations}; rounds: {args.rounds}",
        "",
        "The same core, OS CSPRNG, PID check and bytes output are used for every stride. "
        "This measures the C core, not end-to-end Python API throughput.",
        "",
        "| Clock sample every N UUIDs | Median ns/UUID | Best ns/UUID |",
        "| ---: | ---: | ---: |",
    ]
    for stride, values in sorted(timings.items()):
        lines.append(f"| {stride} | {statistics.median(values):.3f} | {min(values):.3f} |")
    lines += ["", "## Simulated scheduling pause (25 ms)", ""]
    lines.extend(f"- {k}: {v}" for k, v in observations.items())
    lines += [
        "",
        "## Decision",
        "",
        "Keep per-UUID wall-clock reads in the production batch API. Caching can reduce "
        "core cost, but a scheduling pause makes later UUIDs retain a stale timestamp. "
        "A count-based refresh cannot bound that lag in wall time. A future snapshot "
        "batch API would need a separate explicit timestamp contract. OS CSPRNG and "
        "process-wide ordering remain unchanged.",
    ]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.output:
        args.output.write_text(report)
        args.output.with_suffix(".json").write_text(
            json.dumps({"commit": sha, "timings_ns": timings, "pause": observations}, indent=2)
            + "\n"
        )


if __name__ == "__main__":
    main()
