# Formatting, parsing and FastAPI: sprint results

Core formatting and parsing improved across all three measured configurations. The explicit Pydantic adapters improved relative to their 0.6.0 counterparts, but remain slower than built-in Pydantic for the 1,000-UUID validate/dump path. The HTTP experiment does **not** establish a repeatable application speedup. Keep built-in Pydantic handling as the default.

Measured implementation: `5a8324a47a8410816aa4f12ec712ca7afeac05dc`. Baseline: published **fastuuid7 0.6.0**, source `d733169281a1d8039a891e6334aa6281007fd638`. Reference: **uuid-utils 1.2.0**. The development wheel still reports 0.6.0; wheel/runtime hashes distinguish it from the PyPI baseline. Measurements completed on 2026-11-10 UTC / 2026-11-11 Moscow.

[Protocol and reproduction](../../api/README.md) · [Linux CI run](https://github.com/nekrasovp/uuidv7/actions/runs/42909399947) · [Artifact identities and SHA256](manifest.json)

## Core operations against 0.6.0

Each cell is **baseline → candidate ns/UUID (time reduction)**: median of five fresh-process means, retaining lists of 64 outputs. Lower is better. All raw process values and exploratory paired-bootstrap intervals are in the linked summaries. These are three separate host/interpreter cohorts, not a Python-version comparison.

| Operation | macOS M3 Pro, Python 3.14.6 | Linux Xeon 8573C, Python 3.12.16 | Linux EPYC 9V74, Python 3.14.10 |
|---|---:|---:|---:|
| Format existing stdlib UUID | 110.1 → 48.6 (+55.8%) | 216.3 → 81.0 (+62.6%) | 182.2 → 81.1 (+55.5%) |
| Generate v7 + str | 359.9 → 162.1 (+54.9%) | 1029.3 → 349.5 (+66.0%) | 714.5 → 309.7 (+56.6%) |
| Parse into stdlib UUID | 74.0 → 60.0 (+19.0%) | 169.8 → 132.7 (+21.9%) | 138.4 → 128.0 (+7.5%) |
| Parse batch into stdlib UUIDs | 65.6 → 50.9 (+22.4%) | 155.9 → 113.6 (+27.2%) | 125.5 → 111.0 (+11.6%) |
| Parse batch into packed bytes | 25.5 → 11.7 (+54.1%) | 52.1 → 21.3 (+59.1%) | 39.0 → 18.3 (+53.2%) |
| Generate v4, retain object | 88.3 → 88.2 (+0.1%) | 173.9 → 174.9 (-0.6%) | 160.3 → 159.1 (+0.8%) |
| Generate v7, retain object | 86.9 → 87.0 (-0.1%) | 189.4 → 194.8 (-2.8%) | 178.2 → 176.6 (+0.9%) |

Formatting saves **55.5–62.6%**, generate-v7-and-string **54.9–66.0%**, scalar parsing **7.5–21.9%**, object batch parsing **11.6–27.2%**, and packed batch parsing **53.2–59.1%**. The targeted improvements have intervals excluding zero in every cohort. Generation was not changed: the observed Linux 3.12 v7 retained-object regression is 2.8% (interval −7.0 to −1.7% time reduction), while the other generation controls are roughly flat. Retain this regression in the evidence; do not call generation faster in this sprint.

Candidate wheels are built locally/on the runner, while baseline wheels are the published artifacts. Compiler/build differences, host noise and code layout may contribute to small changes; these measurements compare installed artifacts, not source alone.

## Candidate against uuid-utils

Cells are **candidate / uuid-utils ns/UUID** in the same candidate worker. `compat` returns stdlib UUID values; `native` returns a different Python type. Native rows compare the stated output workload, not complete API or driver equivalence.

| Workload / uuid-utils reference | macOS 3.14 | Linux 3.12 | Linux 3.14 |
|---|---:|---:|---:|
| v4 objects / compat | 88.2 / 234.9 | 174.9 / 763.0 | 159.1 / 471.8 |
| v7 objects / compat | 87.0 / 283.8 | 194.8 / 875.2 | 176.6 / 602.4 |
| v4 objects / native | 88.2 / 51.2 | 174.9 / 100.3 | 159.1 / 84.5 |
| v7 objects / native | 87.0 / 76.1 | 194.8 / 147.9 | 176.6 / 133.5 |
| v4 generation + str / native | 351.7 / 118.3 | 1008.4 / 182.6 | 671.8 / 169.9 |
| v7 generation + str / native | 162.1 / 143.8 | 349.5 / 236.2 | 309.7 / 224.3 |
| Existing object formatting / native str | 48.6 / 66.4 | 81.0 / 88.9 | 81.1 / 89.6 |
| Parse to stdlib / native parse | 60.0 / 65.2 | 132.7 / 151.2 | 128.0 / 132.5 |
| Packed batch parse / native parse + join | 11.7 / 98.2 | 21.3 / 232.6 | 18.3 / 207.4 |

We remain ahead of `uuid-utils.compat` for standard-object generation. The optimized formatter and parser also have lower medians than native uuid-utils in these cohorts, although the scalar-parse lead on Linux 3.14 is only about 3%. **Native uuid-utils still wins standard-object-vs-native generation and generate-then-str**. In particular, `str(uuid4())` remains the stdlib path and was not optimized.

For a string-only caller, avoid allocating an intermediate UUID: candidate `uuid4_str()` measures 62.5 / 96.7 / 98.7 ns and `uuid7_str()` 57.7 / 112.6 / 104.9 ns (same cohort order). If an existing stdlib object must be formatted, use `format_uuid(value)`. `format_uuid(uuid4())` measures 144.7 / 249.7 / 244.2 ns; this is still slower than the native uuid-utils v4 generate+str path, but much faster than stdlib `str(uuid4())`.

## Pydantic stages

Microseconds per model containing **1,000 varied UUIDs**, measured outside HTTP. Cells are **validate JSON / dump parsed model / validate-and-dump**. All sizes (1, 64, 1,000), invalid-input cases, process samples and min/max values remain in each raw report.

| Variant | macOS 3.14 | Linux 3.12 | Linux 3.14 |
|---|---:|---:|---:|
| baseline-default | 71.8 / 68.2 / 139.8 | 150.4 / 98.7 / 251.3 | 139.1 / 94.1 / 233.8 |
| candidate-default | 72.1 / 66.7 / 138.2 | 150.8 / 98.6 / 251.4 | 138.9 / 94.3 / 237.0 |
| baseline-explicit | 93.0 / 142.0 / 229.8 | 293.0 / 258.8 / 562.3 | 174.4 / 215.1 / 424.7 |
| candidate-explicit | 78.6 / 78.4 / 157.3 | 162.1 / 117.6 / 280.1 | 151.2 / 115.4 / 267.2 |
| uuid-utils-compat | 71.5 / 68.0 / 140.0 | 150.9 / 98.8 / 251.5 | 138.9 / 94.2 / 234.5 |
| uuid-utils-native | 129.3 / 82.7 / 217.2 | 327.2 / 100.7 / 431.1 | 264.8 / 103.8 / 367.7 |

The explicit adapters now complete the 1,000-UUID round trip about 31–50% sooner than the same adapters using 0.6.0, but still take about **11–14% longer than built-in Pydantic**. Validation crosses a Python callback and serialization constructs an intermediate list of strings. The native uuid-utils adapter is slower here too. A faster scalar parser is not automatically a faster JSON validator.

Pydantic 2.14.3/core 2.50.4 does not call `_UUID7.__str__` when serializing a value through `TypeAdapter(uuid.UUID)`. A process-local diagnostic wrapping that method recorded one call for manual `str(value)` and zero for `dump_json(value)` on the measured macOS candidate. This explains why faster `str(uuid7())` does not imply a built-in Pydantic serialization gain. The prepared standard-UUID response and default parse cases are unchanged-path controls.

## Full HTTP results

The full matrix contains **1,260 measured cells and 151,200 checked responses** across the three cohorts: six variants × seven scenarios × two offered rates × five repeats per cohort. Each cohort also has 30 isolated Pydantic workers. All responses matched status/value/version/error-location contracts; **zero errors and zero scheduling-overload flags**. Warmup responses are additional and excluded from these totals.

Actual loopback TCP, separate uvicorn and client processes, one worker, asyncio/h11; no database, TLS or proxy. Server CPU excludes client work. Measurements are at fixed offered load, **not maximum throughput**. One-second repeats and small sample counts make p99 and the five-repeat intervals exploratory; all results, including losses, are retained.

Below: **server CPU reduction from replacing built-in Pydantic with the candidate explicit adapter**, at the higher declared rate. Negative means the adapter costs more CPU. Brackets give exploratory 95% paired-repeat bootstrap intervals. The complete two-rate CPU/latency/lag tables are linked below.

| Scenario / offered rps | macOS 3.14 | Linux 3.12 | Linux 3.14 |
|---|---:|---:|---:|
| path / 300 | +0.3% [-14.9, +29.9] | -2.7% [-14.8, +7.7] | +11.7% [-30.3, +26.5] |
| body-1 / 300 | -4.5% [-14.4, +0.0] | -13.7% [-26.3, +8.4] | +2.1% [-16.5, +6.7] |
| body-1000 / 60 | -32.0% [-56.6, +8.8] | -0.1% [-17.1, +25.1] | +9.2% [-17.3, +11.4] |
| response / 60 | -41.8% [-85.8, +2.5] | -3.7% [-33.2, +18.2] | -13.5% [-25.3, +8.5] |
| invalid / 300 | +4.1% [-19.8, +11.5] | -11.6% [-34.5, -9.4] | -3.3% [-36.2, +1.4] |
| generate-v4 / 120 | +13.2% [-40.9, +30.7] | +5.1% [-20.8, +34.3] | +6.2% [-49.0, +8.9] |
| generate-v7 / 120 | -2.4% [-42.1, +35.7] | -17.6% [-21.9, +18.9] | -1.6% [-19.5, +16.0] |

No adapter meets the predeclared requirement of a repeatable ≥10% server CPU reduction across configurations/rates, intervals excluding zero, and no latency regression. Isolated favorable cells are insufficient; most intervals are wide, and unchanged default paths also move. There is no basis here for a general FastAPI speed claim or installing framework hooks by default.

## Next optimization priorities

1. Keep the measured core formatting/parsing changes and existing stdlib-compatible return contracts. Preserve the targeted microbenchmarks in CI.
2. Profile the explicit JSON boundary before adding an integration: avoid per-item Python callbacks and intermediate string lists. Any batch serializer or framework adapter needs a fresh paired comparison against built-in pydantic-core, not just against 0.6.0.
3. For v4 string workloads, document/use `uuid4_str()` or `format_uuid(existing_uuid)`. Changing the public v4 object type solely to accelerate `str()` would require a separate compatibility decision.
4. If HTTP performance becomes a release claim, repeat on a quiet dedicated host with longer runs and a capacity sweep. Keep this short CI matrix for reproducibility and correctness; do not infer production RPS from it.

## Validation and evidence

- Fresh `git clone --no-local` at the measured source: 846 tests each on CPython 3.9 and 3.12; 851 each on 3.14 and 3.15. Ruff, formatting, mypy, actionlint and diff checks passed.
- Installed candidate outside checkout: 425 selected runtime/API contract tests and four FastAPI/Pydantic integration tests passed; both import names checked. Two upstream Starlette/AnyIO deprecation warnings were retained.
- Strict parser: exhaustive byte substitutions for all accepted text shapes, arbitrary 128-bit properties and 200,000 deterministic inputs under ASan/UBSan passed. Formatting covers every single bit, nil/max, unusual ints and custom UUID subclasses.
- Wheel/sdist builds, Twine and package-content checks passed. All hosted tests, integrations, parser sanitizers and platform wheel builds passed on the measured source. See PR checks for validation of the final documentation/evidence commit.

| Cohort | Full tables | Raw microbenchmarks | Raw HTTP and Pydantic | Derived comparisons |
|---|---|---|---|---|
| macos-py314 | [summary](macos-py314/summary.md) | [micro.json](macos-py314/micro.json) | [api.json](macos-py314/api.json) | [summary.json](macos-py314/summary.json) |
| linux-py312 | [summary](linux-py312/summary.md) | [micro.json](linux-py312/micro.json) | [api.json](linux-py312/api.json) | [summary.json](linux-py312/summary.json) |
| linux-py314 | [summary](linux-py314/summary.md) | [micro.json](linux-py314/micro.json) | [api.json](linux-py314/api.json) | [summary.json](linux-py314/summary.json) |

`manifest.json` records byte-identical copies of the completed reports. `analyze.py` reproduces every derived JSON summary. Runtime source and measured harness files are unchanged by this evidence commit; the measured commit remains the identity of these results. Subsequent hosted reruns validate the PR but do not replace this cohort after seeing its outcomes.
