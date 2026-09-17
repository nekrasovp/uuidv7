# Reproducing the 0.4.0 comparison

Run from a clean release checkout after `uv sync --extra dev --locked`:

```sh
uv run --extra dev --locked python benchmarks/benchmark.py --rounds 5 --output /tmp/scalar.md
uv run --extra dev --locked python benchmarks/benchmark_competitors.py --install-optional --rounds 5 --output /tmp/competitors.md
uv run --extra dev --locked python benchmarks/benchmark_batch.py --output /tmp/batch.md
uv run --extra dev --locked python benchmarks/clock_sources.py --output /tmp/clocks.md
uv run --extra dev --locked python benchmarks/batch_clock.py --output /tmp/batch-clock.md
```

The scalar and competitor runners create temporary virtual environments for
published packages. Pins and primary sources are in `competitors.json` (verified
against PyPI on 2026-09-17). Each case executes in a separate worker process;
imports and validation are outside the measured loop. No upstream allocator can
contaminate another implementation's measurements. Unavailable wheels, missing
APIs, version mismatches and failed conformance samples have explicit reasons.
A candidate failure makes the command fail. The legacy `uuid7==0.1.0` and `uuid-v7==1.0.0` cases are
retained as negative controls for outdated timestamp layouts.

Compare the same output representation, including conversion costs, with the
same entropy and ordering requirements. `fastuuidv7.uuid7()` now returns a custom
object; its string and bytes helpers have separate rows. `uuid_utils.compat`
returns a stdlib UUID. Custom objects are not implicitly interchangeable with
stdlib UUIDs. RNG/fork labels marked unverified must not be promoted to guarantees
merely because a small uniqueness test passed.

Initial timestamps are checked before warmup. UUID generators that advance a
logical timestamp on every call can legitimately run ahead of wall time under
load; the final clock delta records this tradeoff separately. A short sample
checks uniqueness and stated ordering, not statistical collision bounds.

The C batch-clock experiment compares refresh intervals with the real core's
CSPRNG, counter, and PID checks. Its scheduling-pause probe explains why reduced
clock cost alone is insufficient to change the production timestamp contract.
Batch APIs continue to read the wall clock for every UUID. Absolute C timings
must not be compared with end-to-end Python timings.

Existing `*-0.2.0-*` reports are historical measurements of a different entropy
implementation. They are retained for provenance and are not current speed claims.
Release measurements are CI artifacts attached to the matching GitHub release.
