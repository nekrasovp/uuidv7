"""Measure packed-byte APIs; performance samples are not safety evidence.

The baseline must run with the GIL on. Importing it on a t build is allowed to
enable the GIL; --expected-gil must match the observed post-import mode.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import functools
import importlib
import json
import os
import platform
import statistics
import subprocess
import sys
import sysconfig
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


def timed_round(call, threads, calls_per_thread):
    ready = threading.Barrier(threads + 1)

    def worker():
        ready.wait(timeout=30)
        for _ in range(calls_per_thread):
            result = call()
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        jobs = [pool.submit(worker) for _ in range(threads)]
        start = time.perf_counter_ns()
        ready.wait(timeout=30)
        for job in jobs:
            job.result(timeout=120)
        duration = time.perf_counter_ns() - start
    return duration


def percentile(data, fraction):
    return sorted(data)[int((len(data) - 1) * fraction)]


def contention(module, threads, batch):
    ready = threading.Barrier(threads)

    def worker():
        samples = []
        ready.wait(timeout=30)
        for _ in range(1000):
            _, _, wait, hold = module.generate(batch, -1, True)
            samples.append((wait, hold))
        return samples

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        jobs = [pool.submit(worker) for _ in range(threads)]
        samples = [sample for job in jobs for sample in job.result(timeout=120)]
    wait, hold = zip(*samples)
    return {
        "samples": len(samples),
        "wait_ns_p50": statistics.median(wait),
        "wait_ns_p95": percentile(wait, 0.95),
        "hold_ns_p50": statistics.median(hold),
        "hold_ns_p95": percentile(hold, 0.95),
        "wait_fraction_of_native_time": sum(wait) / (sum(wait) + sum(hold)),
    }


def measure(args):
    before = sys._is_gil_enabled()
    if args.backend == "baseline":
        sys.path.insert(0, str(args.build.resolve() / "baseline"))
        module = importlib.import_module("fastuuid7")
    else:
        sys.path.insert(0, str(args.build.resolve()))
        module = importlib.import_module("_ft_uuid7")
    after = sys._is_gil_enabled()
    if after != (args.expected_gil == "on"):
        raise SystemExit("GIL state mismatch; refusing mislabeled benchmark")
    if args.backend == "baseline" and not after:
        raise SystemExit("refusing to benchmark unsafe baseline with GIL disabled")
    rows = []
    for batch in (1, 64):
        if args.backend == "baseline":
            call = (
                module.uuid7_bytes
                if batch == 1
                else functools.partial(module.uuid7_bytes_many, batch)
            )
        else:
            call = functools.partial(module.generate, batch)
        for _ in range(1000):
            call()
        for threads in (1, 2, 4, 8):
            calls_per_thread = max(1, args.uuids // (threads * batch))
            actual_uuids = calls_per_thread * threads * batch
            samples = [
                timed_round(call, threads, calls_per_thread) / actual_uuids
                for _ in range(args.rounds)
            ]
            row = {
                "batch": batch,
                "threads": threads,
                "uuids_per_round": actual_uuids,
                "rounds": args.rounds,
                "ns_per_uuid_samples": samples,
                "ns_per_uuid_median": statistics.median(samples),
                "uuids_per_second": 1e9 / statistics.median(samples),
            }
            if args.backend == "prototype":
                row["instrumented_contention_separate_run"] = contention(module, threads, batch)
            rows.append(row)
    cpu = platform.processor()
    if sys.platform == "darwin":
        cpu = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
    build = json.loads((args.build / "build.json").read_text())
    result = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "cpu": cpu,
        "logical_cpus": os.cpu_count(),
        "compiler": build["compiler"],
        "source_sha256": build["sha256"],
        "build_gil_disabled": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "gil_before_import": before,
        "gil_after_import": after,
        "backend": args.backend,
        "api_shape": "packed bytes; scalar or batch=64",
        "method": "O3; no instrumentation in throughput; warmup=1000 calls; fixed UUID count",
        "rows": rows,
    }
    if args.backend == "prototype":
        result["audit_clock"] = module.timer_info()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--backend", choices=("baseline", "prototype"), required=True)
    parser.add_argument("--expected-gil", choices=("on", "off"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--uuids", type=int, default=262144)
    args = parser.parse_args()
    if args.rounds < 1 or args.uuids < 512:
        parser.error("rounds >= 1 and uuids >= 512 required")
    measure(args)
