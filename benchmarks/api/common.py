"""Inputs and provenance shared by the installed-wheel application benchmarks."""

import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_SHA = "d733169281a1d8039a891e6334aa6281007fd638"
VARIANTS = (
    "baseline-default",
    "candidate-default",
    "baseline-explicit",
    "candidate-explicit",
    "uuid-utils-compat",
    "uuid-utils-native",
)
rng = random.Random(9562)
VALUES = [uuid.UUID(int=rng.getrandbits(128), version=4) for _ in range(1000)]
VALUES[::2] = [uuid.UUID(int=(v.int & ~(15 << 76)) | (7 << 76)) for v in VALUES[::2]]
TEXTS = [str(v) for v in VALUES]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_packages(packages, baseline, expected_version):
    """Only the candidate library version may differ from the locked baseline."""
    assert baseline["fastuuid7"] == "0.6.0"
    assert packages["fastuuid7"] == expected_version
    assert {k: v for k, v in packages.items() if k != "fastuuid7"} == {
        k: v for k, v in baseline.items() if k != "fastuuid7"
    }


def identity():
    import uuid_utils

    import fastuuid7
    import uuidv7.uuidv7_impl.uuid7_gen  # noqa: F401

    # Source checkouts must not shadow either installed comparison wheel.
    for module in (fastuuid7, uuid_utils):
        assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
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
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "cpu": cpu,
        "cpu_count": os.cpu_count(),
        "packages": {
            d.metadata["Name"].lower().replace("_", "-"): d.version
            for d in importlib.metadata.distributions()
        },
        "lock_sha256": digest(HERE / "uv.lock"),
        "harness_sha256": {p.name: digest(p) for p in HERE.glob("*.py")},
        "corpus_sha256": hashlib.sha256("".join(TEXTS).encode()).hexdigest(),
        "fastuuid7_python_sha256": digest(
            Path(fastuuid7.__file__).parents[1] / "uuidv7" / "__init__.py"
        ),
        "extensions": {
            name: {"name": Path(m.__file__).name, "sha256": digest(m.__file__)}
            for name, m in tuple(sys.modules.items())
            if name.startswith(("uuidv7.", "uuid_utils.", "pydantic_core."))
            and getattr(m, "__file__", None)
            and Path(m.__file__).suffix in (".so", ".pyd")
        },
    }


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
