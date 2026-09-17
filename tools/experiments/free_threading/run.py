"""Build, check, and optionally measure under the interpreter invoking this file.

Every dangerous check is subprocess-bounded. Results record observed GIL state.
Run separately with a regular Python and a free-threaded Python (no -X gil=0).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(args):
    if sys.flags.optimize:
        raise SystemExit("Contract assertions require Python without -O or -OO")
    if "PYTHON_GIL" in os.environ or "gil" in sys._xoptions:
        raise SystemExit("Use default interpreter mode; do not force the production GIL off")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    build_dir = output / "build"

    def child(script, parameters, log, timeout=120):
        command = [sys.executable, str(HERE / script)] + parameters
        with (output / log).open("w") as stream:
            subprocess.run(
                command, check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout
            )

    child("build.py", ["--output", str(build_dir)], "build.log")
    free = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    expected = "off" if free else "on"
    child("check.py", ["--build", str(build_dir), "--expected-gil", expected], "checks.log")
    check_log = (output / "checks.log").read_text()
    status = "passed_with_skips" if "skipped=" in check_log else "passed"
    summary = {
        "python": sys.version,
        "build_gil_disabled": free,
        "expected_gil": expected,
        "contracts": status,
        "checks_log": "checks.log",
        "benchmarks": "not_run",
    }
    # Baseline is isolated in its own process: on t builds import should enable GIL.
    probe = (
        "import sys,json; before=sys._is_gil_enabled(); "
        f"sys.path.insert(0, {str(build_dir / 'baseline')!r}); "
        "import fastuuid7; after=sys._is_gil_enabled(); "
        "assert after; "
        "raw=fastuuid7.uuid7_bytes_many(1000); "
        "v=[raw[i:i+16] for i in range(0,len(raw),16)]; "
        "assert len(set(v))==1000 and all(a<b for a,b in zip(v,v[1:])); "
        "print(json.dumps({'before':before,'after':after,'ordered_unique':1000}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    summary["baseline_import_probe"] = json.loads(result.stdout)
    (output / "baseline-import.log").write_text(result.stderr)
    if not args.no_benchmark:
        for backend in ("baseline", "prototype"):
            child(
                "measure.py",
                [
                    "--build",
                    str(build_dir),
                    "--backend",
                    backend,
                    "--expected-gil",
                    "on" if backend == "baseline" else expected,
                    "--output",
                    str(output / f"{backend}.json"),
                    "--rounds",
                    str(args.rounds),
                    "--uuids",
                    str(args.uuids),
                ],
                f"{backend}.log",
                timeout=300,
            )
        summary["benchmarks"] = "completed"
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--no-benchmark", action="store_true")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--uuids", type=int, default=262144)
    run(parser.parse_args())
