"""Microbenchmark the pieces that make up uuidv7.uuid7()."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uuidv7 as uuidv7_module
from uuidv7 import uuid7, uuid7_bytes, uuid7_obj, uuid7_str
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7 as ext_generate_uuid7_str,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_bytes as ext_generate_uuid7_bytes,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_int as ext_generate_uuid7_int,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7 as ext_uuid7,
)

DEFAULT_ITERATIONS = 1_000_000
WARMUP_ITERATIONS = 10_000


@dataclass
class MicroCase:
    name: str
    group: str
    includes: str
    func: Callable[[], object]


@dataclass
class MicroResult:
    name: str
    group: str
    includes: str
    iterations: int
    total_seconds: float
    ops_per_second: float
    ns_per_op: float


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def validate_uuid7(value: object) -> None:
    if isinstance(value, uuid.UUID):
        parsed = value
    elif isinstance(value, int):
        parsed = uuid.UUID(int=value)
    elif isinstance(value, bytes):
        parsed = uuid.UUID(bytes=value)
    else:
        parsed = uuid.UUID(str(value))

    if parsed.version != 7:
        raise AssertionError(f"{value!r} is not UUIDv7")
    if parsed.variant != uuid.RFC_4122:
        raise AssertionError(f"{value!r} is not RFC-compatible")


def benchmark_case(case: MicroCase, iterations: int) -> MicroResult:
    for _ in range(WARMUP_ITERATIONS):
        case.func()

    validate_uuid7(case.func())

    start = time.perf_counter_ns()
    for _ in range(iterations):
        case.func()
    end = time.perf_counter_ns()

    validate_uuid7(case.func())

    total_ns = end - start
    total_seconds = total_ns / 1_000_000_000
    return MicroResult(
        name=case.name,
        group=case.group,
        includes=case.includes,
        iterations=iterations,
        total_seconds=total_seconds,
        ops_per_second=iterations / total_seconds,
        ns_per_op=total_ns / iterations,
    )


def build_cases() -> list[MicroCase]:
    fixed_int = ext_generate_uuid7_int()
    fixed_bytes = ext_generate_uuid7_bytes()
    fixed_uuid = uuidv7_module._uuid7_from_int(fixed_int)

    return [
        MicroCase(
            name="uuidv7.uuid7()",
            group="public uuid object",
            includes="C generation, PyLong conversion, _UUID7 allocation, direct slot writes",
            func=uuid7,
        ),
        MicroCase(
            name="uuidv7.uuid7_obj()",
            group="public native object",
            includes="C generation plus compact native object allocation",
            func=uuid7_obj,
        ),
        MicroCase(
            name="uuidv7 C uuid7()",
            group="C extension output",
            includes="C generation, PyLong conversion, _UUID7 allocation, direct slot writes",
            func=ext_uuid7,
        ),
        MicroCase(
            name="generate_uuid7_int() + _uuid7_from_int(value)",
            group="uuid object split",
            includes="same pieces as uuid7(), called explicitly from Python",
            func=lambda: uuidv7_module._uuid7_from_int(ext_generate_uuid7_int()),
        ),
        MicroCase(
            name="generate_uuid7_int()",
            group="C extension output",
            includes="C generation plus 128-bit PyLong conversion",
            func=ext_generate_uuid7_int,
        ),
        MicroCase(
            name="_uuid7_from_int(fixed_int)",
            group="Python object construction",
            includes="_UUID7 allocation and direct int/is_safe attribute writes",
            func=lambda: uuidv7_module._uuid7_from_int(fixed_int),
        ),
        MicroCase(
            name="uuid.UUID(int=fixed_int)",
            group="Python object construction",
            includes="stdlib UUID constructor from an existing int",
            func=lambda: uuid.UUID(int=fixed_int),
        ),
        MicroCase(
            name="uuid.UUID(bytes=fixed_bytes)",
            group="Python object construction",
            includes="stdlib UUID constructor from existing 16 bytes",
            func=lambda: uuid.UUID(bytes=fixed_bytes),
        ),
        MicroCase(
            name="uuidv7.uuid7_bytes()",
            group="public raw output",
            includes="C generation plus PyBytes allocation",
            func=uuid7_bytes,
        ),
        MicroCase(
            name="generate_uuid7_bytes()",
            group="C extension output",
            includes="C generation plus PyBytes allocation without public wrapper",
            func=ext_generate_uuid7_bytes,
        ),
        MicroCase(
            name="uuidv7.uuid7_str()",
            group="public string output",
            includes="C generation, manual hex encoding, PyUnicode allocation",
            func=uuid7_str,
        ),
        MicroCase(
            name="generate_uuid7()",
            group="C extension output",
            includes="C generation, manual hex encoding, PyUnicode allocation without public wrapper",
            func=ext_generate_uuid7_str,
        ),
        MicroCase(
            name="str(uuidv7.uuid7())",
            group="convenience string output",
            includes="uuid7() plus UUID.__str__ formatting",
            func=lambda: str(uuid7()),
        ),
        MicroCase(
            name="str(uuidv7.uuid7_obj())",
            group="native string output",
            includes="uuid7_obj() plus native formatter",
            func=lambda: str(uuid7_obj()),
        ),
        MicroCase(
            name="str(fixed_uuid)",
            group="Python string formatting",
            includes="UUID.__str__ formatting from an existing UUID object",
            func=lambda: str(fixed_uuid),
        ),
    ]


def environment_markdown() -> str:
    return "\n".join(
        [
            "## Environment",
            "",
            f"- OS: {platform.platform()}",
            f"- Machine: {platform.machine()}",
            f"- CPU: {platform.processor() or 'unknown'}",
            f"- Python: {platform.python_version()}",
            f"- fastuuid7: {package_version('fastuuid7')}",
        ]
    )


def results_markdown(results: list[MicroResult]) -> str:
    lines = [
        "## Results",
        "",
        "| Group | Case | ops/sec | ns/op | Iterations | Includes |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for result in sorted(results, key=lambda item: item.ns_per_op):
        lines.append(
            f"| {result.group} | `{result.name}` | {result.ops_per_second:,.0f} | "
            f"{result.ns_per_op:,.1f} | {result.iterations:,} | {result.includes} |"
        )
    return "\n".join(lines)


def derived_markdown(results: list[MicroResult]) -> str:
    by_name = {result.name: result for result in results}

    def diff(left: str, right: str) -> str:
        value = by_name[left].ns_per_op - by_name[right].ns_per_op
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:,.1f} ns/op"

    lines = [
        "## Derived Reads",
        "",
        "| Estimate | Delta |",
        "| --- | ---: |",
    ]

    pairs = [
        (
            "`uuid7()` over direct `generate_uuid7_int()`",
            "uuidv7.uuid7()",
            "generate_uuid7_int()",
        ),
        (
            "`uuid7()` over `_uuid7_from_int(fixed_int)`",
            "uuidv7.uuid7()",
            "_uuid7_from_int(fixed_int)",
        ),
        (
            "`uuid7_str()` over `uuid7_bytes()`",
            "uuidv7.uuid7_str()",
            "uuidv7.uuid7_bytes()",
        ),
        (
            "`str(uuid7())` over `uuid7()`",
            "str(uuidv7.uuid7())",
            "uuidv7.uuid7()",
        ),
        (
            "public `uuid7()` wrapper over explicit split call",
            "uuidv7.uuid7()",
            "generate_uuid7_int() + _uuid7_from_int(value)",
        ),
        (
            "public `uuid7()` alias over direct C object call",
            "uuidv7.uuid7()",
            "uuidv7 C uuid7()",
        ),
        (
            "public `uuid7_bytes()` wrapper over direct extension call",
            "uuidv7.uuid7_bytes()",
            "generate_uuid7_bytes()",
        ),
        (
            "public `uuid7_str()` wrapper over direct extension call",
            "uuidv7.uuid7_str()",
            "generate_uuid7()",
        ),
    ]

    for label, left, right in pairs:
        lines.append(f"| {label} | {diff(left, right)} |")

    lines.extend(
        [
            "",
            "These deltas are directional microbenchmark reads, not strict additive profiling. "
            "They are useful for choosing the next optimization target.",
        ]
    )
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [benchmark_case(case, args.iterations) for case in build_cases()]
    report = "\n\n".join(
        [
            "# UUIDv7 Internals Microbenchmark",
            environment_markdown(),
            results_markdown(results),
            derived_markdown(results),
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
