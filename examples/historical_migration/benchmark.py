"""Measure scalar-loop and historical-batch allocations on the same timestamps."""

import argparse
import gc
import json
import platform
import statistics
import time
from importlib.metadata import version

from fastuuid7 import uuid7_at, uuid7_at_many


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--rounds", type=int, default=9)
    args = parser.parse_args()
    if args.count < 1 or args.rounds < 1:
        parser.error("--count and --rounds must be positive")
    timestamps = tuple(1_645_557_742_123 + index // 10 for index in range(args.count))
    methods = {
        "scalar_loop": lambda: [uuid7_at(unix_ms=ms) for ms in timestamps],
        "historical_batch": lambda: uuid7_at_many(unix_ms=timestamps),
    }
    for method in methods.values():
        method()
    samples = {name: [] for name in methods}
    for round_index in range(args.rounds):
        names = list(methods)
        if round_index % 2:
            names.reverse()
        for name in names:
            gc.collect()
            start = time.perf_counter_ns()
            values = methods[name]()
            elapsed = time.perf_counter_ns() - start
            assert [value.time for value in values] == list(timestamps)
            samples[name].append(elapsed / args.count)
            del values
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "package_version": version("fastuuid7"),
                "count": args.count,
                "rounds": args.rounds,
                "input": "prebuilt tuple, 10 rows per millisecond, not timed",
                "output": "list[uuid.UUID], allocation included, deallocation not timed",
                "gc": "enabled; collect before each sample",
                "samples_ns_per_uuid": samples,
                "median_ns_per_uuid": {name: statistics.median(v) for name, v in samples.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
