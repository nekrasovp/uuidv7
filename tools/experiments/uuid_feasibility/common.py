"""Deterministic inputs, identities and shared adapters for research only."""

import hashlib
import importlib.metadata
import json
import platform
import random
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RNG = random.Random(9562)
UUIDS = [uuid.UUID(int=RNG.getrandbits(128), version=4) for _ in range(2048)]
UUIDS[::2] = [uuid.UUID(int=(u.int & ~(15 << 76)) | (7 << 76)) for u in UUIDS[::2]]
TEXTS = [str(u) for u in UUIDS]
RAW = [u.bytes for u in UUIDS]
INVALID = [
    "",
    "x" * 36,
    TEXTS[0][:-1],
    TEXTS[0] + "0",
    "０" * 32,
    TEXTS[0][:15] + "\0" + TEXTS[0][16:],
    " " + TEXTS[0],
    TEXTS[0].replace("-", "_"),
    "urn:UUID:" + TEXTS[0],
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity():
    packages = [
        "fastuuid7",
        "fastuuid",
        "uuid-utils",
        "pydantic",
        "pydantic-core",
        "fastapi",
        "starlette",
        "uvicorn",
        "pyperf",
        "psycopg",
    ]
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "dirty": subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "compiler": platform.python_compiler(),
        "lock_sha256": digest(HERE / "uv.lock"),
        "sources": {p.name: digest(p) for p in HERE.iterdir() if p.suffix in (".py", ".c", ".h")},
        "packages": {p: importlib.metadata.version(p) for p in packages},
        "corpus_sha256": hashlib.sha256("".join(TEXTS).encode()).hexdigest(),
        "native_extensions": {
            name: {"file": Path(m.__file__).name, "sha256": digest(m.__file__)}
            for name, m in tuple(sys.modules.items())
            if name.startswith(("_uuid_lab", "fastuuid", "uuid_utils", "pydantic_core"))
            and getattr(m, "__file__", "")
            and Path(m.__file__).suffix in (".so", ".pyd")
        },
    }


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
