"""Build research and unchanged baseline extensions outside shipped packages.

No setuptools, pip installation, runtime dependency, or pyproject edit needed.
Run with each target interpreter, CPython >= 3.13 on POSIX with a C compiler.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CORE = ROOT / "uuidv7/uuidv7_impl"


def build(output: Path) -> None:
    if sys.version_info < (3, 13) or os.name != "posix":
        raise SystemExit("prototype requires POSIX CPython >= 3.13")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    compiler = shlex.split(os.environ.get("CC", "cc"))
    flags = ["-O3", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fPIC", "-pthread"]
    flags += ["-I" + sysconfig.get_path("include"), "-I" + str(CORE / "include")]
    link = ["-bundle", "-undefined", "dynamic_lookup"] if sys.platform == "darwin" else ["-shared"]
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    commands = []
    prototype = compiler + flags + ["-I" + str(CORE / "src"), str(HERE / "prototype.c")]
    commands.append(prototype + link + ["-o", str(output / ("_ft_uuid7" + suffix))])
    # Separate import root permits default-GIL baseline probing on a t build.
    baseline = output / "baseline"
    for package in ("fastuuid7", "uuidv7", "uuidv7/uuidv7_impl"):
        destination = baseline / package
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / package / "__init__.py", destination / "__init__.py")
    # The unchanged baseline has existing unused-parameter warnings.
    baseline_flags = [flag for flag in flags if flag not in ("-Wextra", "-Werror")]
    commands.append(
        compiler
        + baseline_flags
        + [str(CORE / "uuid7_gen.c"), str(CORE / "src/uuid7_gen.c")]
        + link
        + ["-o", str(baseline / "uuidv7/uuidv7_impl" / ("uuid7_gen" + suffix))]
    )
    for command in commands:
        subprocess.run(command, check=True)
    sources = (
        [HERE / name for name in ("prototype.c", "build.py", "check.py", "measure.py", "run.py")]
        + [
            CORE / "src/uuid7_gen.c",
            CORE / "uuid7_gen.c",
            ROOT / "uuidv7/__init__.py",
            ROOT / "fastuuid7/__init__.py",
        ]
        + sorted((CORE / "include").glob("*.h"))
    )
    metadata = {
        "python": sys.version,
        "platform": platform.platform(),
        "gil_disabled_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "compiler": subprocess.check_output(compiler + ["--version"], text=True).splitlines()[0],
        "commands": commands,
        "sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sources
        },
    }
    (output / "build.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args().output)
