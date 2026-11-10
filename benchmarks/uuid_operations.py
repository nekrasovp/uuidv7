"""Process-repeated UUID comparisons with explicit lifetime/output contracts.

Run against an installed wheel from outside the checkout; no source-path injection.
Install references exactly as recorded in REFERENCE_PINS (legacy in a second env).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
import timeit
import uuid
from pathlib import Path

REFERENCE_PINS = {"uuid-utils": "1.2.0", "fastuuidv7": "0.1.10", "fastuuid": "0.14.0"}
LEGACY_UUID_UTILS = "0.19.0"
SIZE = 64


def build_cases():
    import fastuuid
    import fastuuidv7
    import uuid_utils
    import uuid_utils.compat as compat

    import fastuuid7 as candidate

    cases = []
    rng = random.Random(9562)
    objects = [uuid.UUID(int=rng.getrandbits(128)) for _ in range(SIZE)]
    texts = [str(value) for value in objects]
    raw = [value.bytes for value in objects]
    native_objects = [uuid_utils.UUID(text) for text in texts]

    def add(key, statement, scope, shape, operation, units=SIZE):
        scope = {
            **scope,
            "size": SIZE,
            "texts": texts,
            "raw": raw,
            "objects": objects,
            "native_objects": native_objects,
        }
        # Evaluate outside timing, retaining the output for contract checks.
        before_ms = time.time_ns() // 1_000_000
        result = eval(statement, scope)
        after_ms = time.time_ns() // 1_000_000
        if shape.startswith("list"):
            assert len(result) == SIZE, key
            element = result[0]
            expected = shape.removeprefix("list[").removesuffix("]")
            if expected == "uuid.UUID":
                assert isinstance(element, uuid.UUID), key
            elif expected == "str":
                assert type(element) is str and str(uuid.UUID(element)) == element, key
            elif expected == "native":
                assert not isinstance(element, (uuid.UUID, str, bytes)), key
            values = [uuid.UUID(str(value)) for value in result]
            if operation.startswith("v"):
                assert all(
                    v.version == int(operation[1]) and v.variant == uuid.RFC_4122 for v in values
                ), key
            else:
                assert values == objects, key
            if operation == "v7":
                assert all(before_ms - 20 <= v.int >> 80 <= after_ms + 20 for v in values), key
            if operation.startswith("v"):
                assert len(set(values)) == SIZE, key
        elif shape == "packed bytes":
            assert result == b"".join(raw), key
        cases.append((key, statement, scope, shape, operation, units))

    for version in (4, 7):
        generators = [
            ("candidate", getattr(candidate, f"uuid{version}", None), "uuid.UUID"),
            ("stdlib", getattr(uuid, f"uuid{version}", None), "uuid.UUID"),
            ("uuid-utils.compat", getattr(compat, f"uuid{version}"), "uuid.UUID"),
            ("uuid-utils.native", getattr(uuid_utils, f"uuid{version}"), "native"),
        ]
        if version == 4:
            generators.append(("fastuuid.native", fastuuid.uuid4, "native"))
        else:
            generators.append(("fastuuidv7.native", fastuuidv7.uuid7, "native"))
            generators.append(("candidate.native", candidate.uuid7_obj, "native"))
        for library, gen, shape in generators:
            if gen is None:
                continue
            for mode in ("discard", "retain", "serialize"):
                statement = (
                    "[str(gen()) for _ in range(size)]"
                    if mode == "serialize"
                    else "[gen() for _ in range(size)]"
                )
                output = "str" if mode == "serialize" else shape
                add(
                    f"v{version}/{library}/{mode}",
                    statement,
                    {"gen": gen},
                    f"list[{output}]",
                    f"v{version}",
                )
                if mode == "discard":
                    # Change only after validating retained values. This loop discards each
                    # result before the next call, exposing any sole-owner object reuse.
                    key, _, scope, _, operation, units = cases.pop()
                    cases.append(
                        (
                            key,
                            "for _ in range(size): gen()",
                            scope,
                            shape + " (discarded)",
                            operation,
                            units,
                        )
                    )
        direct = getattr(candidate, f"uuid{version}_str", None)
        if hasattr(candidate, "format_uuid"):
            add(
                f"v{version}/candidate/format-generated",
                "[fmt(gen()) for _ in range(size)]",
                {"fmt": candidate.format_uuid, "gen": getattr(candidate, f"uuid{version}")},
                "list[str]",
                f"v{version}",
            )
        if direct is not None:
            add(
                f"v{version}/candidate/direct-string",
                "[gen() for _ in range(size)]",
                {"gen": direct},
                "list[str]",
                f"v{version}",
            )
        if version == 7:
            add(
                "v7/fastuuidv7/direct-string",
                "[gen() for _ in range(size)]",
                {"gen": fastuuidv7.uuid7_str},
                "list[str]",
                "v7",
            )
        batch = getattr(candidate, f"uuid{version}_many", None)
        if batch is not None:
            add(
                f"v{version}/candidate/batch",
                "batch(size)",
                {"batch": batch},
                "list[uuid.UUID]",
                f"v{version}",
            )

    parsers = [
        ("stdlib", uuid.UUID, "uuid.UUID"),
        ("uuid-utils.native", uuid_utils.UUID, "native"),
        ("fastuuid.native", fastuuid.UUID, "native"),
    ]
    if hasattr(candidate, "parse"):
        parsers.append(("candidate", candidate.parse, "uuid.UUID"))
    for name, parse, shape in parsers:
        add(
            f"parse/{name}",
            "[parse(text) for text in texts]",
            {"parse": parse},
            f"list[{shape}]",
            "parse",
        )
        if shape == "native":
            add(
                f"parse/{name}-to-stdlib",
                "[UUID(int=parse(text).int) for text in texts]",
                {"parse": parse, "UUID": uuid.UUID},
                "list[uuid.UUID]",
                "parse",
            )
        add(
            f"packed/{name}",
            "b''.join(parse(text).bytes for text in texts)",
            {"parse": parse},
            "packed bytes",
            "parse",
        )
    if hasattr(candidate, "parse"):
        add(
            "parse/candidate-batch",
            "parse(texts)",
            {"parse": candidate.parse_many},
            "list[uuid.UUID]",
            "parse",
        )
        add(
            "packed/candidate-batch",
            "parse(texts)",
            {"parse": candidate.parse_bytes_many},
            "packed bytes",
            "parse",
        )
        add(
            "format/candidate-UUID",
            "[fmt(value) for value in objects]",
            {"fmt": candidate.format_uuid},
            "list[str]",
            "format",
        )
        add(
            "format/candidate-bytes",
            "[fmt(value) for value in raw]",
            {"fmt": candidate.format_uuid},
            "list[str]",
            "format",
        )
    add("format/stdlib-UUID", "[str(value) for value in objects]", {}, "list[str]", "format")
    add(
        "format/uuid-utils.native",
        "[str(value) for value in native_objects]",
        {},
        "list[str]",
        "format",
    )
    add(
        "format/stdlib-bytes",
        "[str(UUID(bytes=value)) for value in raw]",
        {"UUID": uuid.UUID},
        "list[str]",
        "format",
    )
    return cases


def worker(seed):
    cases = build_cases()
    random.Random(seed).shuffle(cases)
    rows = []
    for key, statement, scope, shape, operation, units in cases:
        timer = timeit.Timer(statement, globals=scope)
        loops = 1
        while timer.timeit(loops) < 0.025:
            loops *= 2
        timer.timeit(loops)  # untimed warmup
        values = [timer.timeit(loops) * 1e9 / (loops * units) for _ in range(3)]
        rows.append(
            {
                "key": key,
                "shape": shape,
                "operation": operation,
                "loops": loops,
                "ns_per_uuid": values,
                "mean_ns": statistics.mean(values),
            }
        )
    import fastuuid7
    import uuidv7.uuidv7_impl.uuid7_gen as extension

    packages = {name: metadata.version(name) for name in ["fastuuid7", *REFERENCE_PINS]}
    cpu = platform.processor()
    if sys.platform == "darwin":
        cpu = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
    elif sys.platform.startswith("linux"):
        cpu = next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            cpu,
        )
    return {
        "cpu": cpu,
        "cpu_count": os.cpu_count(),
        "seed": seed,
        "rows": rows,
        "packages": packages,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "candidate_path": fastuuid7.__file__,
        "extension_sha256": hashlib.sha256(Path(extension.__file__).read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=int)
    parser.add_argument("--processes", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-sha", default="unspecified")
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(args.worker)))
        return
    if args.processes < 3 or args.output is None or args.source_sha == "unspecified":
        parser.error("require --processes >= 3, --output, and --source-sha")
    samples = []
    for index in range(args.processes):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(9562 + index)],
            capture_output=True,
            text=True,
            check=True,
        )
        samples.append(json.loads(result.stdout))
        print(f"process {index + 1}/{args.processes} complete", flush=True)
    summaries = {}
    for row in samples[0]["rows"]:
        key = row["key"]
        values = [
            next(item["mean_ns"] for item in sample["rows"] if item["key"] == key)
            for sample in samples
        ]
        summaries[key] = {
            "shape": row["shape"],
            "median_ns": statistics.median(values),
            "process_means_ns": values,
            "min_ns": min(values),
            "max_ns": max(values),
        }
    report = {
        "protocol": "uuid-operations-v1",
        "source_sha": args.source_sha,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "batch_size": SIZE,
        "samples": samples,
        "summary": summaries,
        "limits": [
            "same-host microbenchmarks; no application throughput claim",
            "compare equal output contracts; native objects are not stdlib UUIDs",
            "fastuuidv7 uses a non-cryptographic RNG; guarantees differ",
            "GC disabled by timeit; list allocation/deallocation included",
            "parse inputs are prepared outside timing; canonical varied UUIDs",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
