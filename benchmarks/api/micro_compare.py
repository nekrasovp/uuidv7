"""Interleave fresh-process baseline/candidate UUID operation measurements."""

import argparse
import json
import random
import statistics
import subprocess
from pathlib import Path

from common import BASE_SHA, HERE, ROOT, check_packages, digest, save
from run import check_wheel, clean_env


def run(args):
    if args.processes < 3:
        raise ValueError("require at least three processes per implementation")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    harness = HERE.parent / "uuid_operations.py"
    output = {
        "protocol": "uuid-operations-paired-v1",
        "harness_commit": head,
        "source_dirty": subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True
        ).strip(),
        "candidate_source": head,
        "baseline_source": BASE_SHA,
        "candidate_wheel_sha256": digest(args.candidate_wheel),
        "installed_candidate": check_wheel(args.candidate_python, args.candidate_wheel),
        "harness_sha256": digest(harness),
        "lock_sha256": digest(HERE / "uv.lock"),
        "samples": {"baseline": [], "candidate": []},
        "summary": {},
        "complete": False,
    }
    rng = random.Random(9562)
    for repeat in range(args.processes):
        providers = ["baseline", "candidate"]
        rng.shuffle(providers)
        for provider in providers:
            python = getattr(args, provider + "_python")
            result = subprocess.run(
                [python, str(harness), "--worker", str(9562 + repeat)],
                cwd=args.work_dir,
                env=clean_env(provider),
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            expected_version = (
                output["installed_candidate"]["version"] if provider == "candidate" else "0.6.0"
            )
            assert data["packages"]["fastuuid7"] == expected_version
            assert data["packages"]["uuid-utils"] == "1.2.0"
            data["repeat"] = repeat
            output["samples"][provider].append(data)
            save(args.output, output)
            print(f"Micro {provider} repeat {repeat + 1} complete", flush=True)
    first = output["samples"]["baseline"][0]
    for provider, samples in output["samples"].items():
        assert all(s["python"] == first["python"] and s["cpu"] == first["cpu"] for s in samples)
        for sample in samples:
            check_packages(
                sample["packages"],
                first["packages"],
                output["installed_candidate"]["version"] if provider == "candidate" else "0.6.0",
            )
        summary = {}
        for row in first["rows"]:
            key = row["key"]
            values = [next(v["mean_ns"] for v in s["rows"] if v["key"] == key) for s in samples]
            summary[key] = {
                "shape": row["shape"],
                "median_ns": statistics.median(values),
                "process_means_ns": values,
                "min_ns": min(values),
                "max_ns": max(values),
            }
        output["summary"][provider] = summary
    output["complete"] = True
    save(args.output, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-python", required=True)
    parser.add_argument("--baseline-python", required=True)
    parser.add_argument("--candidate-wheel", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--processes", type=int, default=5)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    for field in ("candidate_python", "baseline_python", "candidate_wheel", "work_dir"):
        setattr(args, field, str(Path(getattr(args, field)).absolute()))
    if Path(args.work_dir).resolve().is_relative_to(ROOT):
        parser.error("work directory must be outside the source checkout")
    run(args)
