"""Compare pinned UUIDv7 implementations in separate worker processes."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((Path(__file__).with_name("competitors.json")).read_text())


@dataclass(frozen=True)
class Case:
    key: str
    package: str
    module: str
    function: str
    shape: str
    entropy: str
    ordering: str
    fork: str
    source: str
    transform: str = ""
    published: bool = False


def build_cases():
    cases = []
    shapes = [
        ("uuid7", "uuid.UUID"),
        ("uuid7_obj", "native"),
        ("uuid7_str", "str"),
        ("uuid7_bytes", "bytes"),
    ]
    for published in [False, True]:
        for function, shape in shapes:
            label = f"published {PINS['fastuuid7']['version']}" if published else "candidate"
            cases.append(
                Case(
                    f"{label}: {function}",
                    "fastuuid7",
                    "fastuuid7",
                    function,
                    shape,
                    "OS CSPRNG",
                    "process",
                    "PID reset",
                    "https://github.com/nekrasovp/uuidv7",
                    published=published,
                )
            )
        cases.append(
            Case(
                f"{label}: str(uuid7())",
                "fastuuid7",
                "fastuuid7",
                "uuid7",
                "str",
                "OS CSPRNG",
                "process",
                "PID reset",
                "https://github.com/nekrasovp/uuidv7",
                "str",
                published,
            )
        )
    cases.append(
        Case(
            "stdlib uuid7",
            "python",
            "uuid",
            "uuid7",
            "uuid.UUID",
            "OS CSPRNG",
            "process",
            "not verified",
            "https://docs.python.org/3/library/uuid.html#uuid.uuid7",
        )
    )
    specs = [
        ("uuid-utils", "uuid_utils", "uuid7", "native", "", "upstream RNG", "millisecond"),
        (
            "uuid-utils",
            "uuid_utils.compat",
            "uuid7",
            "uuid.UUID",
            "",
            "upstream RNG",
            "millisecond",
        ),
        ("uuid-utils", "uuid_utils", "uuid7", "str", "str", "upstream RNG", "millisecond"),
        ("fastuuidv7", "fastuuidv7", "uuid7", "native", "", "non-cryptographic", "none"),
        ("fastuuidv7", "fastuuidv7", "uuid7_str", "str", "", "non-cryptographic", "none"),
        ("fastuuidv7", "fastuuidv7", "uuid7_hex", "hex", "", "non-cryptographic", "none"),
        ("fastuuidv7", "fastuuidv7", "uuid7_bytes", "bytes", "", "non-cryptographic", "none"),
        (
            "fastuuidv7",
            "fastuuidv7",
            "uuid7_with_count",
            "native",
            "",
            "non-cryptographic",
            "thread",
        ),
        (
            "fastuuidv7",
            "fastuuidv7",
            "SequentialGenerator",
            "native",
            "sequential",
            "non-cryptographic",
            "instance",
        ),
        ("uuid7-rs", "uuid7_rs", "uuid7", "native", "", "not verified", "not verified"),
        ("uuid7-rs", "uuid7_rs.compat", "uuid7", "uuid.UUID", "", "not verified", "not verified"),
        ("uuid7-rs", "uuid7_rs", "uuid7", "str", "str", "not verified", "not verified"),
        ("c_uuid_v7", "c_uuid_v7", "uuid7", "native", "", "non-cryptographic", "not verified"),
        (
            "c_uuid_v7",
            "c_uuid_v7.compat",
            "uuid7",
            "uuid.UUID",
            "",
            "non-cryptographic",
            "not verified",
        ),
        ("c_uuid_v7", "c_uuid_v7", "uuid7", "str", "str", "non-cryptographic", "not verified"),
        ("uuid7", "uuid_extensions", "uuid7", "uuid.UUID", "", "legacy draft", "not verified"),
        ("uuid-v7", "uuid_v7.base", "uuid7", "uuid.UUID", "", "not verified", "not verified"),
        ("uuid6", "uuid6", "uuid7", "uuid.UUID", "", "OS CSPRNG", "process"),
    ]
    for package, module, function, shape, transform, entropy, ordering in specs:
        label = f"{module}.{function}()"
        if transform == "str":
            label = f"str({label})"
        cases.append(
            Case(
                label,
                package,
                module,
                function,
                shape,
                entropy,
                ordering,
                "not verified",
                PINS[package]["source"],
                transform,
            )
        )
    return cases


def parsed_uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, bytes):
        return uuid.UUID(bytes=value)
    if isinstance(value, int):
        return uuid.UUID(int=value)
    return uuid.UUID(str(value))


def validate_uuid7(value, shape, *, before_ms=None, after_ms=None):
    expected = {"uuid.UUID": uuid.UUID, "str": str, "hex": str, "bytes": bytes}
    if shape in expected and not isinstance(value, expected[shape]):
        raise ValueError(f"expected {shape}, got {type(value).__module__}.{type(value).__name__}")
    if shape == "native" and isinstance(value, (uuid.UUID, str, bytes, int)):
        raise ValueError("expected a custom native object")
    parsed = parsed_uuid(value)
    if parsed.version != 7 or parsed.variant != uuid.RFC_4122:
        raise ValueError("invalid UUIDv7 version/variant bits")
    if shape == "str" and value != str(parsed):
        raise ValueError("noncanonical UUID string")
    if shape == "hex" and value != parsed.hex:
        raise ValueError("noncanonical UUID hex")
    tolerance_ms = max(10, math.ceil(time.get_clock_info("time").resolution * 1000))
    if (
        before_ms is not None
        and not before_ms - tolerance_ms <= parsed.int >> 80 <= after_ms + tolerance_ms
    ):
        raise ValueError(
            "timestamp does not encode current Unix milliseconds (legacy layout or clock drift)"
        )
    return parsed


def measure(case, iterations, rounds):
    # Never import another competitor in this worker. In particular, a process-
    # wide allocator installed by one extension cannot influence another case.
    if case.published:
        sys.path[:] = [p for p in sys.path if Path(p or os.getcwd()).resolve() != ROOT]
    else:
        sys.path.insert(0, str(ROOT))
    version = (
        platform.python_version()
        if case.package == "python"
        else importlib.metadata.version(case.package)
    )
    if (
        case.package != "python"
        and (case.package != "fastuuid7" or case.published)
        and version != PINS[case.package]["version"]
    ):
        raise ValueError(f"expected pinned {PINS[case.package]['version']}, got {version}")
    module = importlib.import_module(case.module)
    if (
        case.package == "fastuuid7"
        and not case.published
        and Path(module.__file__).resolve().parent.parent != ROOT
    ):
        raise ValueError("candidate import is not from this checkout")
    function = getattr(module, case.function)
    if case.transform == "sequential":
        generator = function()
        function = generator.next_uuid
    elif case.transform == "str":
        original = function

        def function():
            return str(original())

    # Validate time on the first call, before a logical clock can legitimately
    # advance during a high-throughput test (e.g. uuid6's timestamp counter).
    before = time.time_ns() // 1_000_000
    sample = function()
    after = time.time_ns() // 1_000_000
    previous = validate_uuid7(sample, case.shape, before_ms=before, after_ms=after)
    seen = {previous.int}
    for _ in range(64):
        current = validate_uuid7(function(), case.shape)
        if current.int in seen:
            raise ValueError("duplicate UUID in validation sample")
        seen.add(current.int)
        if (
            case.ordering in {"process", "thread", "instance", "millisecond"}
            and current <= previous
        ):
            raise ValueError("sample violated advertised monotonicity")
        previous = current
    for _ in range(2000):
        function()
    timings = []
    for _ in range(rounds):
        start = time.perf_counter_ns()
        for _ in range(iterations):
            function()
        timings.append((time.perf_counter_ns() - start) / iterations)
    final = validate_uuid7(function(), case.shape)
    return {
        **asdict(case),
        "version": version,
        "return_type": f"{type(sample).__module__}.{type(sample).__name__}",
        "best_ns": min(timings),
        "median_ns": statistics.median(timings),
        "iterations": iterations,
        "rounds": rounds,
        "final_clock_delta_ms": (final.int >> 80) - time.time_ns() // 1_000_000,
    }


def install_packages(directory, packages):
    subprocess.run([sys.executable, "-m", "venv", str(directory)], check=True, capture_output=True)
    python = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    failures = {}
    for package in sorted(packages):
        result = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--only-binary=:all:",
                f"{package}=={PINS[package]['version']}",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode:
            failures[package] = (result.stderr.strip().splitlines() or ["installation failed"])[-1]
    return python, failures


def report(results, skipped, sha, dirty=False):
    lines = [
        "# UUIDv7 comparison",
        "",
        f"Commit: `{sha}`",
        f"Tracked source changes: {dirty}",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.platform()} / {platform.machine()}",
        "",
        "Each case runs in a fresh process. Versions are pinned in competitors.json. "
        "Validation checks shape, canonical encoding, initial timestamp (10 ms or the system clock resolution, whichever is larger), "
        "uniqueness and advertised ordering on a small sample. It is not a proof of "
        "fork safety or RNG strength; guarantee labels describe upstream contracts. "
        "Unknown guarantees remain explicitly unverified. The final clock delta shows "
        "logical-clock drift during the workload, not a conformance verdict.",
        "",
        "Compare only matching output shapes AND generation guarantees. "
        f"The candidate and published {PINS['fastuuid7']['version']} both use OS CSPRNG entropy and PID reset.",
        "",
    ]
    for shape in sorted({r["shape"] for r in results}):
        lines += [
            f"## {shape}",
            "",
            "| Case | Version | Entropy | Order scope | Fork | ns/UUID median | best | final clock delta ms | Return type |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
        for r in sorted((r for r in results if r["shape"] == shape), key=lambda r: r["median_ns"]):
            lines.append(
                f"| {r['key']} | {r['version']} | {r['entropy']} | {r['ordering']} | {r['fork']} | {r['median_ns']:.1f} | {r['best_ns']:.1f} | {r['final_clock_delta_ms']} | {r['return_type']} |"
            )
    lines += ["", "## Skipped or rejected", ""]
    lines.extend(f"- {s['key']}: {s['reason']}" for s in skipped)
    lines += ["", "## Sources and pins", ""]
    lines.extend(f"- {p}=={v['version']}: {v['source']}" for p, v in PINS.items())
    if results:
        lines += [
            "",
            f"Iterations per round: {results[0]['iterations']}; rounds: {results[0]['rounds']}.",
        ]
    return "\n".join(lines) + "\n"


def main(argv=None, *, scalar_only=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--iterations", type=int, default=1_000_000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--install-optional", action="store_true")
    parser.add_argument("--skip-published", action="store_true")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.iterations < 1 or args.rounds < 1:
        parser.error("iterations and rounds must be positive")
    cases = build_cases()
    if args.worker:
        case = next(c for c in cases if c.key == args.worker)
        try:
            result = {"result": measure(case, args.iterations, args.rounds)}
        except Exception as exc:
            result = {"skip": {"key": case.key, "reason": f"{type(exc).__name__}: {exc}"}}
        print(json.dumps(result))
        return 0
    if scalar_only:
        cases = [c for c in cases if c.package in {"fastuuid7", "python"}]
    if args.skip_published:
        cases = [c for c in cases if not c.published]
    results, skipped = [], []
    with tempfile.TemporaryDirectory(prefix="uuidv7-compare-") as directory:
        python = Path(sys.executable)
        failures = {}
        if args.install_optional or (scalar_only and not args.skip_published):
            packages = {
                c.package
                for c in cases
                if c.package != "python" and (c.package != "fastuuid7" or c.published)
            }
            python, failures = install_packages(Path(directory) / "venv", packages)
        for case in cases:
            if case.package in failures and (case.package != "fastuuid7" or case.published):
                skipped.append({"key": case.key, "reason": failures[case.package]})
                continue
            worker_python = (
                sys.executable
                if case.package == "fastuuid7" and not case.published
                else str(python)
            )
            print(f"Measuring {case.key}", file=sys.stderr, flush=True)
            run = subprocess.run(
                [
                    worker_python,
                    str(Path(__file__).resolve()),
                    "--worker",
                    case.key,
                    "-n",
                    str(args.iterations),
                    "--rounds",
                    str(args.rounds),
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if run.returncode:
                skipped.append(
                    {
                        "key": case.key,
                        "reason": f"worker exited {run.returncode}: {run.stderr[-400:]}",
                    }
                )
                continue
            data = json.loads(run.stdout)
            if "result" in data:
                results.append(data["result"])
            else:
                skipped.append(data["skip"])
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode != 0
    output = report(results, skipped, sha, dirty)
    print(output)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        args.output.with_suffix(".json").write_text(
            json.dumps(
                {"commit": sha, "source_dirty": dirty, "results": results, "skipped": skipped},
                indent=2,
            )
            + "\n"
        )
    # A broken candidate is a release failure, never an optional skip.
    return int(any(s["key"].startswith("candidate:") for s in skipped))


if __name__ == "__main__":
    raise SystemExit(main())
