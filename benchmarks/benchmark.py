"""Benchmark UUID v7 implementations."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from uuidv7 import uuid7 as fastuuid7_uuid7
from uuidv7 import uuid7_bytes as fastuuid7_uuid7_bytes
from uuidv7 import uuid7_str as fastuuid7_uuid7_str

DEFAULT_ITERATIONS = 1_000_000
WARMUP_ITERATIONS = 1_000


@dataclass
class BenchmarkResult:
    name: str
    version: str
    iterations: int
    total_seconds: float
    uuids_per_second: float
    ns_per_op: float


@dataclass
class BenchmarkCase:
    name: str
    version: str
    func: Callable[[], object]


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def validate_uuid7(value: object) -> None:
    if isinstance(value, uuid.UUID):
        parsed = value
    elif isinstance(value, bytes):
        parsed = uuid.UUID(bytes=value)
    else:
        parsed = uuid.UUID(str(value))
    if parsed.version != 7:
        raise AssertionError(f"{value!r} is not UUIDv7")
    if parsed.variant != uuid.RFC_4122:
        raise AssertionError(f"{value!r} is not RFC-compatible")


def benchmark_case(case: BenchmarkCase, iterations: int) -> BenchmarkResult:
    for _ in range(WARMUP_ITERATIONS):
        validate_uuid7(case.func())

    start = time.perf_counter_ns()
    for _ in range(iterations):
        case.func()
    end = time.perf_counter_ns()

    validate_uuid7(case.func())

    total_ns = end - start
    total_seconds = total_ns / 1_000_000_000
    return BenchmarkResult(
        name=case.name,
        version=case.version,
        iterations=iterations,
        total_seconds=total_seconds,
        uuids_per_second=iterations / total_seconds,
        ns_per_op=total_ns / iterations,
    )


def optional_case(
    package_name: str,
    import_name: str,
    function_name: str,
    display_name: str,
) -> Optional[BenchmarkCase]:
    try:
        module = __import__(import_name, fromlist=[function_name])
        func = getattr(module, function_name)
    except (AttributeError, ImportError):
        return None

    return BenchmarkCase(
        name=display_name,
        version=package_version(package_name),
        func=func,
    )


def current_process_cases() -> list[BenchmarkCase]:
    cases = [
        BenchmarkCase(
            name="fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID",
            version=package_version("fastuuid7"),
            func=fastuuid7_uuid7,
        ),
        BenchmarkCase(
            name="fastuuid7 0.2.0 candidate: uuid7_str() -> str",
            version=package_version("fastuuid7"),
            func=fastuuid7_uuid7_str,
        ),
        BenchmarkCase(
            name="fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes",
            version=package_version("fastuuid7"),
            func=fastuuid7_uuid7_bytes,
        ),
        BenchmarkCase(
            name="fastuuid7 0.2.0 candidate: str(uuid7())",
            version=package_version("fastuuid7"),
            func=lambda: str(fastuuid7_uuid7()),
        ),
    ]

    if hasattr(uuid, "uuid7"):
        cases.append(
            BenchmarkCase(
                name="Python stdlib uuid.uuid7()",
                version=platform.python_version(),
                func=uuid.uuid7,
            )
        )

    for case in (
        optional_case("uuid-utils", "uuid_utils", "uuid7", "uuid-utils uuid7()"),
        optional_case("fastuuidv7", "fastuuidv7", "uuid7", "fastuuidv7 uuid7()"),
        optional_case("uuid7", "uuid_extensions", "uuid7", "uuid7 package uuid_extensions.uuid7()"),
    ):
        if case is not None:
            cases.append(case)

    return cases


def benchmark_published_fastuuid7(iterations: int) -> Optional[BenchmarkResult]:
    python = sys.executable
    with tempfile.TemporaryDirectory(prefix="fastuuid7-0.1.0-bench-") as tmp:
        venv_dir = Path(tmp) / "venv"
        subprocess.run([python, "-m", "venv", str(venv_dir)], check=True, stdout=subprocess.PIPE)
        venv_python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--quiet",
                "fastuuid7==0.1.0",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp,
        )
        if install.returncode != 0:
            print("Skipping published fastuuid7==0.1.0 benchmark; install failed:", file=sys.stderr)
            print(install.stderr.strip(), file=sys.stderr)
            return None

        script = textwrap.dedent(
            f"""
            import json
            import time
            import uuid
            import importlib.metadata
            from uuidv7 import uuid7

            iterations = {iterations}
            for _ in range(1000):
                value = uuid7()
                parsed = uuid.UUID(str(value))
                assert parsed.version == 7

            start = time.perf_counter_ns()
            for _ in range(iterations):
                uuid7()
            end = time.perf_counter_ns()

            total_ns = end - start
            print(json.dumps({{
                "name": "published fastuuid7 0.1.0: uuid7() -> str",
                "version": importlib.metadata.version("fastuuid7"),
                "iterations": iterations,
                "total_seconds": total_ns / 1_000_000_000,
                "uuids_per_second": iterations / (total_ns / 1_000_000_000),
                "ns_per_op": total_ns / iterations,
            }}))
            """
        )
        run = subprocess.run(
            [str(venv_python), "-c", script],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp,
        )
        if run.returncode != 0:
            print(
                "Skipping published fastuuid7==0.1.0 benchmark; benchmark failed:", file=sys.stderr
            )
            print(run.stderr.strip(), file=sys.stderr)
            return None

    data = json.loads(run.stdout)
    return BenchmarkResult(**data)


def environment_markdown() -> str:
    cpu = platform.processor() or "unknown"
    return "\n".join(
        [
            "## Environment",
            "",
            f"- OS: {platform.platform()}",
            f"- Machine: {platform.machine()}",
            f"- CPU: {cpu}",
            f"- Python: {platform.python_version()}",
        ]
    )


def results_markdown(results: list[BenchmarkResult]) -> str:
    lines = [
        "## Results",
        "",
        "| Implementation | Version | UUIDs/sec | ns/op | Iterations |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for result in sorted(results, key=lambda item: item.uuids_per_second, reverse=True):
        lines.append(
            f"| {result.name} | {result.version} | {result.uuids_per_second:,.0f} | {result.ns_per_op:,.1f} | {result.iterations:,} |"
        )
    return "\n".join(lines)


def skipped_markdown(results: list[BenchmarkResult]) -> str:
    measured = {result.name for result in results}
    optional = [
        "Python stdlib uuid.uuid7()",
        "uuid-utils uuid7()",
        "fastuuidv7 uuid7()",
        "uuid7 package uuid_extensions.uuid7()",
        "published fastuuid7 0.1.0: uuid7() -> str",
    ]
    skipped = [name for name in optional if name not in measured]
    if not skipped:
        return ""
    lines = ["## Skipped", ""]
    lines.extend(f"- {name}" for name in skipped)
    return "\n".join(lines)


def write_markdown(output: Path, results: list[BenchmarkResult]) -> None:
    parts = [
        "# UUIDv7 Benchmark Results",
        "",
        environment_markdown(),
        "",
        results_markdown(results),
    ]
    skipped = skipped_markdown(results)
    if skipped:
        parts.extend(["", skipped])
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"iterations per implementation, default {DEFAULT_ITERATIONS}",
    )
    parser.add_argument(
        "--skip-published",
        action="store_true",
        help="skip temporary-venv benchmark for published fastuuid7==0.1.0",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write Markdown results to this path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [benchmark_case(case, args.iterations) for case in current_process_cases()]

    if not args.skip_published and shutil.which(sys.executable):
        published = benchmark_published_fastuuid7(args.iterations)
        if published is not None:
            results.append(published)

    print(environment_markdown())
    print()
    print(results_markdown(results))
    skipped = skipped_markdown(results)
    if skipped:
        print()
        print(skipped)

    if args.output:
        write_markdown(args.output, results)
        print()
        print(f"Wrote {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
