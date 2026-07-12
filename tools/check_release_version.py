"""Verify that all public package versions match a release tag or version."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_version(path: Path, pattern: str) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise SystemExit(f"could not find version in {path.relative_to(ROOT)}")
    return match.group(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", help="release version or tag, for example 0.2.1 or v0.2.1")
    args = parser.parse_args()
    expected = args.expected[1:] if args.expected.startswith("v") else args.expected

    versions = {
        "pyproject.toml": _read_version(ROOT / "pyproject.toml", r'^version\s*=\s*"([^"]+)"\s*$'),
        "uuidv7/__init__.py": _read_version(
            ROOT / "uuidv7" / "__init__.py", r'^__version__\s*=\s*"([^"]+)"\s*$'
        ),
        "uuidv7/uuidv7/__init__.py": _read_version(
            ROOT / "uuidv7" / "uuidv7" / "__init__.py",
            r'^__version__\s*=\s*"([^"]+)"\s*$',
        ),
    }
    mismatches = {path: value for path, value in versions.items() if value != expected}
    if mismatches:
        details = ", ".join(f"{path}={value}" for path, value in mismatches.items())
        raise SystemExit(f"expected version {expected}; mismatches: {details}")

    print(f"all package versions match {expected}")


if __name__ == "__main__":
    main()
