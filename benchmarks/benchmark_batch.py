"""Compare scalar loops with the native fastuuid7 batch APIs."""

from __future__ import annotations

import argparse
import platform
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fastuuid7 import (
    uuid7,
    uuid7_bytes,
    uuid7_bytes_many,
    uuid7_many,
    uuid7_obj,
    uuid7_obj_many,
    uuid7_str,
    uuid7_str_many,
)


@dataclass
class BatchCase:
    shape: str
    implementation: str
    function: Callable[[int], object]


@dataclass
class BatchResult:
    shape: str
    implementation: str
    count: int
    median_ns_per_uuid: float


def cases() -> list[BatchCase]:
    return [
        BatchCase("uuid.UUID", "Python loop", lambda count: [uuid7() for _ in range(count)]),
        BatchCase("uuid.UUID", "C batch", uuid7_many),
        BatchCase(
            "native object", "Python loop", lambda count: [uuid7_obj() for _ in range(count)]
        ),
        BatchCase("native object", "C batch", uuid7_obj_many),
        BatchCase("string", "Python loop", lambda count: [uuid7_str() for _ in range(count)]),
        BatchCase("string", "C batch", uuid7_str_many),
        BatchCase(
            "contiguous bytes",
            "Python loop",
            lambda count: b"".join(uuid7_bytes() for _ in range(count)),
        ),
        BatchCase("contiguous bytes", "C batch", uuid7_bytes_many),
    ]


def run_case(case: BatchCase, count: int, rounds: int) -> BatchResult:
    for _ in range(3):
        case.function(count)

    measurements = []
    for _ in range(rounds):
        start = time.perf_counter_ns()
        case.function(count)
        elapsed = time.perf_counter_ns() - start
        measurements.append(elapsed / count)

    return BatchResult(
        shape=case.shape,
        implementation=case.implementation,
        count=count,
        median_ns_per_uuid=statistics.median(measurements),
    )


def report(results: list[BatchResult], rounds: int) -> str:
    scalar_by_shape = {
        result.shape: result.median_ns_per_uuid
        for result in results
        if result.implementation == "Python loop"
    }
    lines = [
        "# UUIDv7 Batch Benchmark",
        "",
        "## Environment",
        "",
        f"- OS: {platform.platform()}",
        f"- Machine: {platform.machine()}",
        f"- CPU: {platform.processor() or 'unknown'}",
        f"- Python: {platform.python_version()}",
        f"- Rounds: {rounds}",
        "",
        "## Results",
        "",
        "| Shape | Implementation | Batch size | median ns/UUID | Speedup vs loop |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for result in results:
        baseline = scalar_by_shape[result.shape]
        speedup = baseline / result.median_ns_per_uuid
        lines.append(
            f"| {result.shape} | {result.implementation} | {result.count:,} | "
            f"{result.median_ns_per_uuid:,.1f} | {speedup:.2f}x |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=10_000, help="UUIDs per batch")
    parser.add_argument("--rounds", type=int, default=5, help="measurement rounds")
    parser.add_argument("--output", type=Path, help="write Markdown results to this path")
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be at least 1")
    if args.rounds < 1:
        raise SystemExit("--rounds must be at least 1")

    results = [run_case(case, args.count, args.rounds) for case in cases()]
    markdown = report(results, args.rounds)
    print(markdown)
    if args.output:
        args.output.write_text(markdown + "\n", encoding="utf-8")
        print(f"\nWrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
