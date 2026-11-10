"""Derive tables and exploratory paired-repeat intervals from preserved JSON."""

import argparse
import json
import random
import statistics
from pathlib import Path

from common import save


def reduction(baseline, candidate):
    assert len(baseline) == len(candidate) and len(baseline) >= 3
    median = statistics.median
    rng = random.Random(9562)
    samples = []
    for _ in range(5000):
        indices = rng.choices(range(len(baseline)), k=len(baseline))
        samples.append(
            100
            * (1 - median([candidate[i] for i in indices]) / median([baseline[i] for i in indices]))
        )
    samples.sort()
    return {
        "reduction_pct": 100 * (1 - median(candidate) / median(baseline)),
        "ci95_pct": [samples[125], samples[4874]],
        "baseline_median": median(baseline),
        "candidate_median": median(candidate),
    }


def analyze(api, micro):
    assert api["complete"] and micro["complete"]
    assert api["candidate_source"] == micro["candidate_source"]
    assert api["candidate_wheel_sha256"] == micro["candidate_wheel_sha256"]
    assert not api["source_dirty"] and not micro["source_dirty"], (
        "do not publish dirty-source measurements"
    )
    result = {
        "source": api["candidate_source"],
        "micro": {},
        "pydantic": {},
        "http": [],
        "http_comparisons": [],
    }
    for key, row in micro["summary"]["candidate"].items():
        if "candidate" not in key:
            continue
        base = micro["summary"]["baseline"][key]
        result["micro"][key] = {
            "shape": row["shape"],
            **reduction(base["process_means_ns"], row["process_means_ns"]),
        }
    for sample in api["pydantic"]:
        for row in sample["rows"]:
            result["pydantic"].setdefault(sample["variant"] + "/" + row["case"], []).append(
                row["mean_ns"]
            )
    result["pydantic"] = {
        k: {"median_ns": statistics.median(v), "min_ns": min(v), "max_ns": max(v)}
        for k, v in result["pydantic"].items()
    }
    for scenario, rates in api["rates"].items():
        for rate in rates:
            groups = {}
            for sample in api["http"]:
                if sample["scenario"] == scenario and sample["rate"] == rate:
                    groups.setdefault(sample["variant"], []).append(sample)
            for variant, samples in groups.items():
                samples.sort(key=lambda v: v["repeat"])
                assert len(samples) == api["rounds"]
                result["http"].append(
                    {
                        "scenario": scenario,
                        "rate": rate,
                        "variant": variant,
                        "cpu_us": statistics.median(s["server_cpu_us"] for s in samples),
                        "p99_ms": statistics.median(s["latency_ms"]["p99"] for s in samples),
                        "lag_p99_ms": statistics.median(
                            s["scheduling_lag_p99_ms"] for s in samples
                        ),
                        "overloaded_repeats": sum(s["scheduling_overload"] for s in samples),
                    }
                )
            for base, candidate in (
                ("baseline-default", "candidate-default"),
                ("baseline-explicit", "candidate-explicit"),
                ("candidate-default", "candidate-explicit"),
                ("uuid-utils-compat", "candidate-default"),
            ):
                if base not in groups or candidate not in groups:
                    continue
                base_rows, new_rows = groups[base], groups[candidate]
                cpu = reduction(
                    [r["server_cpu_us"] for r in base_rows], [r["server_cpu_us"] for r in new_rows]
                )
                result["http_comparisons"].append(
                    {
                        "scenario": scenario,
                        "rate": rate,
                        "baseline": base,
                        "candidate": candidate,
                        **cpu,
                        "overloaded_repeats": sum(
                            r["scheduling_overload"] for r in [*base_rows, *new_rows]
                        ),
                        "p99_reduction": reduction(
                            [r["latency_ms"]["p99"] for r in base_rows],
                            [r["latency_ms"]["p99"] for r in new_rows],
                        ),
                    }
                )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", type=Path, required=True)
    parser.add_argument("--micro", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(json.loads(args.api.read_text()), json.loads(args.micro.read_text()))
    save(args.output, result)
    lines = [
        "# UUID performance comparison",
        "",
        f"Source: `{result['source']}`.",
        "",
        "Positive reduction means less time/CPU. Intervals bootstrap the paired process/repeat means",
        "(5,000 resamples, exploratory 95%, no multiple-comparison correction). Inspect all cells",
        "and scheduling overload flags; no saturation throughput or production claim.",
        "",
        "| Microbenchmark | 0.6.0 ns | Candidate ns | Reduction % | 95% interval % |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, row in result["micro"].items():
        lo, hi = row["ci95_pct"]
        lines.append(
            f"| {key} | {row['baseline_median']:.1f} | {row['candidate_median']:.1f} | {row['reduction_pct']:.1f} | {lo:.1f}, {hi:.1f} |"
        )
    lines += [
        "",
        "| HTTP scenario | Offered rps | Variant | CPU us/request | p99 ms | Lag p99 ms | Overloaded repeats |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in result["http"]:
        lines.append(
            f"| {row['scenario']} | {row['rate']} | {row['variant']} | {row['cpu_us']:.1f} | {row['p99_ms']:.2f} | {row['lag_p99_ms']:.2f} | {row['overloaded_repeats']} |"
        )
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n")
