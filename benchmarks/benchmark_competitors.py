"""Benchmark uuidv7 against optional competitor packages by API shape."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import platform
import statistics
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastuuid7 import uuid7, uuid7_bytes, uuid7_obj, uuid7_str
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7 as ext_generate_uuid7_str,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_bytes as ext_generate_uuid7_bytes,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_int as ext_generate_uuid7_int,
)

DEFAULT_ITERATIONS = 1_000_000
WARMUP_ITERATIONS = 2_000
OPTIONAL_DISTRIBUTIONS = [
    "uuid-utils",
    "fastuuidv7",
    "uuid7",
    "uuid7-rs",
    "c_uuid_v7",
    "uuid-v7",
    "uuid6",
]


@dataclass
class BenchmarkCase:
    name: str
    package: str
    version: str
    shape: str
    func: Callable[[], object]
    source: str


@dataclass
class BenchmarkResult:
    name: str
    package: str
    version: str
    shape: str
    source: str
    iterations: int
    total_seconds: float
    ops_per_second: float
    ns_per_op: float
    best_ns_per_op: float
    median_ns_per_op: float
    rounds: int
    return_type: str


@dataclass
class SkippedCase:
    name: str
    package: str
    reason: str
    source: str


def package_version(distribution_name: str) -> str:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def install_optional_packages() -> dict[str, str]:
    failures: dict[str, str] = {}
    for distribution in OPTIONAL_DISTRIBUTIONS:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", distribution],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            message = result.stderr.strip().splitlines()[-1:] or ["unknown pip failure"]
            failures[distribution] = message[0]
    return failures


def parsed_uuid(value: object) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, bytes):
        return uuid.UUID(bytes=value)
    if isinstance(value, int):
        return uuid.UUID(int=value)
    return uuid.UUID(str(value))


def validate_uuid7(value: object) -> None:
    parsed = parsed_uuid(value)
    if parsed.version != 7:
        raise AssertionError(f"{value!r} is not UUIDv7")
    if parsed.variant != uuid.RFC_4122:
        raise AssertionError(f"{value!r} is not RFC-compatible")


def optional_case(
    *,
    distribution: str,
    module_name: str,
    function_name: str,
    name: str,
    shape: str,
    source: str,
) -> tuple[BenchmarkCase | None, SkippedCase | None]:
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        return None, SkippedCase(name, distribution, f"import failed: {exc}", source)

    try:
        func = getattr(module, function_name)
    except AttributeError:
        return None, SkippedCase(
            name,
            distribution,
            f"{module_name}.{function_name} not found",
            source,
        )

    return (
        BenchmarkCase(
            name=name,
            package=distribution,
            version=package_version(distribution),
            shape=shape,
            func=func,
            source=source,
        ),
        None,
    )


def optional_factory_case(
    *,
    distribution: str,
    module_name: str,
    name: str,
    shape: str,
    source: str,
    make_func: Callable[[object], Callable[[], object]],
) -> tuple[BenchmarkCase | None, SkippedCase | None]:
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        return None, SkippedCase(name, distribution, f"import failed: {exc}", source)

    try:
        func = make_func(module)
    except Exception as exc:  # noqa: BLE001 - optional API discovery should not fail the run.
        return None, SkippedCase(name, distribution, f"factory failed: {exc}", source)

    return (
        BenchmarkCase(
            name=name,
            package=distribution,
            version=package_version(distribution),
            shape=shape,
            func=func,
            source=source,
        ),
        None,
    )


def benchmark_case(case: BenchmarkCase, iterations: int, rounds: int) -> BenchmarkResult:
    for _ in range(WARMUP_ITERATIONS):
        case.func()

    sample = case.func()
    validate_uuid7(sample)

    measurements: list[float] = []
    for _ in range(rounds):
        start = time.perf_counter_ns()
        for _ in range(iterations):
            case.func()
        end = time.perf_counter_ns()
        measurements.append((end - start) / iterations)

    validate_uuid7(case.func())

    best_ns_per_op = min(measurements)
    median_ns_per_op = statistics.median(measurements)
    total_seconds = best_ns_per_op * iterations / 1_000_000_000
    return BenchmarkResult(
        name=case.name,
        package=case.package,
        version=case.version,
        shape=case.shape,
        source=case.source,
        iterations=iterations,
        total_seconds=total_seconds,
        ops_per_second=iterations / total_seconds,
        ns_per_op=best_ns_per_op,
        best_ns_per_op=best_ns_per_op,
        median_ns_per_op=median_ns_per_op,
        rounds=rounds,
        return_type=type(sample).__name__,
    )


def build_cases() -> tuple[list[BenchmarkCase], list[SkippedCase]]:
    cases = [
        BenchmarkCase(
            name="fastuuid7.uuid7_bytes()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="bytes",
            func=uuid7_bytes,
            source="local candidate",
        ),
        BenchmarkCase(
            name="fastuuid7.uuid7_obj()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="custom native object",
            func=uuid7_obj,
            source="local candidate",
        ),
        BenchmarkCase(
            name="fastuuid7.uuid7_str()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="string/default",
            func=uuid7_str,
            source="local candidate",
        ),
        BenchmarkCase(
            name="fastuuid7.uuid7()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="uuid.UUID compat",
            func=uuid7,
            source="local candidate",
        ),
        BenchmarkCase(
            name="str(fastuuid7.uuid7())",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="convenience string",
            func=lambda: str(uuid7()),
            source="local candidate",
        ),
        BenchmarkCase(
            name="str(fastuuid7.uuid7_obj())",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="materialized string",
            func=lambda: str(uuid7_obj()),
            source="local candidate",
        ),
        BenchmarkCase(
            name="uuidv7 C generate_uuid7_bytes()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="C extension output",
            func=ext_generate_uuid7_bytes,
            source="local candidate",
        ),
        BenchmarkCase(
            name="uuidv7 C generate_uuid7()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="C extension output",
            func=ext_generate_uuid7_str,
            source="local candidate",
        ),
        BenchmarkCase(
            name="uuidv7 C generate_uuid7_int()",
            package="fastuuid7",
            version=package_version("fastuuid7"),
            shape="C extension output",
            func=ext_generate_uuid7_int,
            source="local candidate",
        ),
    ]
    skipped: list[SkippedCase] = []

    optional_specs = [
        {
            "distribution": "c_uuid_v7",
            "module_name": "c_uuid_v7",
            "function_name": "uuid7",
            "name": "c_uuid_v7.uuid7()",
            "shape": "custom default object",
            "source": "https://github.com/lava-sh/c_uuid_v7",
        },
        {
            "distribution": "c_uuid_v7",
            "module_name": "c_uuid_v7.compat",
            "function_name": "uuid7",
            "name": "c_uuid_v7.compat.uuid7()",
            "shape": "uuid.UUID compat",
            "source": "https://github.com/lava-sh/c_uuid_v7",
        },
        {
            "distribution": "uuid7-rs",
            "module_name": "uuid7_rs",
            "function_name": "uuid7",
            "name": "uuid7_rs.uuid7()",
            "shape": "custom default object",
            "source": "https://github.com/lava-sh/uuid7-rs",
        },
        {
            "distribution": "uuid7-rs",
            "module_name": "uuid7_rs.compat",
            "function_name": "uuid7",
            "name": "uuid7_rs.compat.uuid7()",
            "shape": "uuid.UUID compat",
            "source": "https://github.com/lava-sh/uuid7-rs",
        },
        {
            "distribution": "fastuuidv7",
            "module_name": "fastuuidv7",
            "function_name": "uuid7",
            "name": "fastuuidv7.uuid7()",
            "shape": "string/default",
            "source": "https://pypi.org/project/fastuuidv7/",
        },
        {
            "distribution": "uuid-utils",
            "module_name": "uuid_utils",
            "function_name": "uuid7",
            "name": "uuid_utils.uuid7()",
            "shape": "uuid/custom object",
            "source": "https://pypi.org/project/uuid-utils/",
        },
        {
            "distribution": "uuid7",
            "module_name": "uuid_extensions",
            "function_name": "uuid7",
            "name": "uuid_extensions.uuid7()",
            "shape": "uuid.UUID compat",
            "source": "https://pypi.org/project/uuid7/",
        },
        {
            "distribution": "uuid-v7",
            "module_name": "uuid_v7",
            "function_name": "uuid7",
            "name": "uuid_v7.uuid7()",
            "shape": "uuid.UUID compat",
            "source": "https://pypi.org/project/uuid-v7/",
        },
        {
            "distribution": "uuid6",
            "module_name": "uuid6",
            "function_name": "uuid7",
            "name": "uuid6.uuid7()",
            "shape": "uuid.UUID compat",
            "source": "https://pypi.org/project/uuid6/",
        },
    ]

    if hasattr(uuid, "uuid7"):
        cases.append(
            BenchmarkCase(
                name="stdlib uuid.uuid7()",
                package="python",
                version=platform.python_version(),
                shape="uuid.UUID compat",
                func=uuid.uuid7,
                source="https://docs.python.org/3/library/uuid.html#uuid.uuid7",
            )
        )
    else:
        skipped.append(
            SkippedCase(
                name="stdlib uuid.uuid7()",
                package="python",
                reason="not available on this Python runtime",
                source="https://docs.python.org/3/library/uuid.html#uuid.uuid7",
            )
        )

    for spec in optional_specs:
        case, skip = optional_case(**spec)
        if case is not None:
            cases.append(case)
        if skip is not None:
            skipped.append(skip)

    factory_specs = [
        {
            "distribution": "c_uuid_v7",
            "module_name": "c_uuid_v7",
            "name": "str(c_uuid_v7.uuid7())",
            "shape": "materialized string",
            "source": "https://github.com/lava-sh/c_uuid_v7",
            "make_func": lambda module: lambda: str(module.uuid7()),
        },
        {
            "distribution": "uuid7-rs",
            "module_name": "uuid7_rs",
            "name": "str(uuid7_rs.uuid7())",
            "shape": "materialized string",
            "source": "https://github.com/lava-sh/uuid7-rs",
            "make_func": lambda module: lambda: str(module.uuid7()),
        },
        {
            "distribution": "uuid-utils",
            "module_name": "uuid_utils",
            "name": "str(uuid_utils.uuid7())",
            "shape": "materialized string",
            "source": "https://pypi.org/project/uuid-utils/",
            "make_func": lambda module: lambda: str(module.uuid7()),
        },
    ]

    for spec in factory_specs:
        case, skip = optional_factory_case(**spec)
        if case is not None:
            cases.append(case)
        if skip is not None:
            skipped.append(skip)

    return cases, skipped


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


def results_markdown(results: list[BenchmarkResult]) -> str:
    lines = [
        "## Results",
        "",
        "| Shape | Case | Package | Version | Return type | ops/sec | best ns/op | median ns/op | Iterations | Rounds |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for result in sorted(results, key=lambda item: item.ops_per_second, reverse=True):
        lines.append(
            f"| {result.shape} | `{result.name}` | `{result.package}` | {result.version} | "
            f"`{result.return_type}` | {result.ops_per_second:,.0f} | "
            f"{result.best_ns_per_op:,.1f} | {result.median_ns_per_op:,.1f} | "
            f"{result.iterations:,} | {result.rounds:,} |"
        )
    return "\n".join(lines)


def grouped_markdown(results: list[BenchmarkResult]) -> str:
    lines = ["## By API Shape", ""]
    for shape in sorted({result.shape for result in results}):
        group = sorted(
            [result for result in results if result.shape == shape],
            key=lambda item: item.ns_per_op,
        )
        lines.extend(
            [
                f"### {shape}",
                "",
                "| Case | ops/sec | best ns/op | median ns/op | Return type |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for result in group:
            lines.append(
                f"| `{result.name}` | {result.ops_per_second:,.0f} | "
                f"{result.best_ns_per_op:,.1f} | {result.median_ns_per_op:,.1f} | "
                f"`{result.return_type}` |"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def skipped_markdown(skipped: list[SkippedCase]) -> str:
    if not skipped:
        return "## Skipped\n\nNone"

    lines = [
        "## Skipped",
        "",
        "| Case | Package | Reason | Source |",
        "| --- | --- | --- | --- |",
    ]
    for item in skipped:
        lines.append(f"| `{item.name}` | `{item.package}` | {item.reason} | {item.source} |")
    return "\n".join(lines)


def sources_markdown(results: list[BenchmarkResult], skipped: list[SkippedCase]) -> str:
    rows = sorted({(item.package, item.source) for item in results + skipped})
    lines = [
        "## Sources",
        "",
        "| Package | Source |",
        "| --- | --- |",
    ]
    for package, source in rows:
        lines.append(f"| `{package}` | {source} |")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"iterations per case, default {DEFAULT_ITERATIONS}",
    )
    parser.add_argument("--output", type=Path, help="write Markdown results to this path")
    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="measurement rounds per case; best and median are reported",
    )
    parser.add_argument(
        "--install-optional",
        action="store_true",
        help="pip install optional competitor distributions before benchmarking",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.rounds < 1:
        raise SystemExit("--rounds must be at least 1")

    install_failures = install_optional_packages() if args.install_optional else {}
    cases, skipped = build_cases()
    for item in skipped:
        if item.package in install_failures:
            item.reason = f"install failed: {install_failures[item.package]}"
    results: list[BenchmarkResult] = []
    for case in cases:
        try:
            results.append(benchmark_case(case, args.iterations, args.rounds))
        except Exception as exc:  # noqa: BLE001 - benchmark should report optional failures.
            skipped.append(
                SkippedCase(
                    name=case.name,
                    package=case.package,
                    reason=f"benchmark failed: {exc}",
                    source=case.source,
                )
            )

    report = "\n\n".join(
        [
            "# UUIDv7 Competitor Benchmark",
            environment_markdown(),
            (
                "## Interpretation\n\n"
                "Cases can use different entropy, monotonicity, and fork-safety guarantees. "
                "The local fastuuid7 candidate uses the operating-system CSPRNG, a monotonic "
                "counter, and automatic fork reseeding. Consult each linked upstream source "
                "before treating timing results as guarantee-equivalent."
            ),
            results_markdown(results),
            grouped_markdown(results),
            skipped_markdown(skipped),
            sources_markdown(results, skipped),
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
