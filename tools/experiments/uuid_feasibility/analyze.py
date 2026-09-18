"""Summarize fixed runs; bootstrap independent process means, never inner loops."""

import argparse
import hashlib
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path


def interval(base, candidate, paired=False):
    """Exploratory 95% percentile interval; small-n and multiplicity remain limits."""
    rng = random.Random(9562)
    gains = []
    for _ in range(4000):
        if paired:
            indices = [rng.randrange(len(base)) for _ in base]
            a, b = [base[i] for i in indices], [candidate[i] for i in indices]
        else:
            a = rng.choices(base, k=len(base))
            b = rng.choices(candidate, k=len(candidate))
        gains.append(100 * (1 - statistics.mean(b) / statistics.mean(a)))
    gains.sort()
    return {
        "reduction_percent": 100 * (1 - statistics.mean(candidate) / statistics.mean(base)),
        "bootstrap_95_percent": [gains[100], gains[3899]],
        "independent_samples": [len(base), len(candidate)],
    }


def micro(path):
    data = json.loads(path.read_text())
    rows = {}
    for b in data["benchmarks"]:
        name = b.get("metadata", {}).get("name", data["metadata"].get("name"))
        process_means = [statistics.mean(r["values"]) for r in b["runs"] if r.get("values")]
        rows[name] = {"seconds": statistics.mean(process_means), "process_means": process_means}
    pairs = []
    names = [
        ("parse/canonical/pydantic", "parse/canonical/c_stdlib"),
        ("scalar/core_schema", "scalar/c_stdlib"),
        ("scalar/type_adapter", "scalar/core_schema"),
        ("batch/1000/core_schema", "batch/1000/c_stdlib"),
        ("batch/1/core_schema", "batch/1/c_stdlib"),
        ("parse/canonical/stdlib", "parse/canonical/c_stdlib"),
        ("parse/canonical/uuid_utils_native", "parse/canonical/c_native"),
        ("parse/canonical/fastuuid_native", "parse/canonical/c_native"),
        ("batch/1000/pydantic", "batch/1000/c_stdlib"),
        ("batch/1000/uuid_utils_native", "batch/1000/c_native"),
        ("batch/1000/fastuuid_packed", "batch/1000/c_packed"),
        ("batch/1000/uuid_utils_packed", "batch/1000/c_packed"),
        ("roundtrip/1000/pydantic", "roundtrip/1000/c_stdlib"),
        ("uuid4/stdlib", "uuid4/c_direct_stdlib"),
        ("uuid4/uuid_utils_compat", "uuid4/c_direct_stdlib"),
    ]
    names += [
        (f"{operation}/{n}/pydantic", f"{operation}/{n}/{variant}")
        for operation in ("model_python", "model_json", "model_dump")
        for n in (1, 1000)
        for variant in ("c_scalar", "c_bulk", "c_native")
    ]
    for baseline, candidate in names:
        if baseline in rows and candidate in rows:
            pairs.append(
                {
                    "baseline": baseline,
                    "candidate": candidate,
                    **interval(rows[baseline]["process_means"], rows[candidate]["process_means"]),
                }
            )
    identity = json.loads(data["metadata"]["study_identity"])
    return {"identity": identity, "benchmarks": rows, "comparisons": pairs}


def http(path):
    data = json.loads(path.read_text())
    by_case = defaultdict(dict)
    overloaded_cases = set()
    for row in data["samples"]:
        by_case[row["scenario"], row["rate"], row["variant"]][row["repeat"]] = row
        if row["scheduling_lag_p99_ms"] > 100:
            overloaded_cases.add((row["scenario"], row["rate"]))
    rows = []
    for (scenario, rate, variant), samples in sorted(by_case.items()):
        repeats = sorted(samples)
        baseline = by_case[scenario, rate, "standard"]
        keys = ("server_cpu_per_request_us", "server_rss", "scheduling_lag_p99_ms")
        row = {
            "scenario": scenario,
            "rate": rate,
            "variant": variant,
            **{k: statistics.median(samples[i][k] for i in repeats) for k in keys},
            **{
                f"p{p}_ms": statistics.median(samples[i]["latency_ms"][f"p{p}"] for i in repeats)
                for p in (50, 95, 99)
            },
            "errors": sum(samples[i]["errors"] for i in repeats),
            "repeats": len(repeats),
            "latency_capacity_eligible": (scenario, rate) not in overloaded_cases,
        }
        if len(baseline) == len(samples):
            row["cpu_reduction"] = interval(
                [baseline[i][keys[0]] for i in repeats],
                [samples[i][keys[0]] for i in repeats],
                paired=True,
            )
            for p in (95, 99):
                row[f"p{p}_reduction"] = interval(
                    [baseline[i]["latency_ms"][f"p{p}"] for i in repeats],
                    [samples[i]["latency_ms"][f"p{p}"] for i in repeats],
                    paired=True,
                )
        rows.append(row)
    return {
        "identity": data["identity"],
        "eligibility_note": (
            "Post-measurement diagnostic: exclude the whole scenario/rate from latency or "
            "capacity acceptance when any variant/repeat has p99 client scheduling lag >100 ms. "
            "All observations and exploratory comparisons remain retained."
        ),
        "rows": rows,
    }


def extras(path):
    data = json.loads(path.read_text())
    groups = defaultdict(list)
    for row in data["samples"]:
        if row.get("warmup"):
            continue
        key = row.get("variant", row.get("fn"))
        key += "/" + str(row.get("workers", row.get("measure", "all")))
        groups[key].append(row)
    result = {}
    for name, rows in groups.items():
        numeric = [
            k for k, v in rows[0].items() if isinstance(v, (float, int)) and not isinstance(v, bool)
        ]
        result[name] = {k: statistics.median(r[k] for r in rows) for k in numeric}
        result[name]["repeats"] = len(rows)
    comparisons = []
    if data["kind"] in ("copy", "packed_copy"):
        baseline = groups["pydantic/all" if data["kind"] == "copy" else "pydantic_uuids/all"]
        for name, rows in groups.items():
            comparisons.append(
                {
                    "variant": name,
                    **interval([r["elapsed"] for r in baseline], [r["elapsed"] for r in rows]),
                }
            )
    return {"identity": data["identity"], "rows": result, "comparisons": comparisons}


def main(args):
    report = {
        "method": "95% percentile bootstrap over independent process means/repeats; exploratory, no multiplicity correction",
        "platforms": {},
    }
    manifests = []
    for directory in sorted(Path(args.results).iterdir()):
        if not directory.is_dir():
            continue
        result = {}
        for kind in ("micro", "http", "memory", "copy", "threads", "packed-copy", "core-baseline"):
            path = directory / (kind + ".json")
            if path.exists():
                result[kind] = {"micro": micro, "core-baseline": micro, "http": http}.get(
                    kind, extras
                )(path)
                manifests.append(
                    {
                        "file": str(path.relative_to(args.results)),
                        "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
        if result:
            report["platforms"][directory.name] = result
    report["raw_manifest"] = manifests
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("results")
    parser.add_argument("output")
    main(parser.parse_args())
