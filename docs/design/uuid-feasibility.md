# UUID parsing and broader-library feasibility

Status: **research complete; no production API accepted or released**.
Date: 2026-09-18. Production baseline: fastuuid7 0.5.0,
`4d9912368da259590c31092837fc985bda8a3951`.

## Decision

Do not start a full uuid-utils replacement from these results. A scoped scalar
text-to-stdlib-UUID API and an explicitly packed batch API are reasonable next
implementation candidates. Generic Pydantic replacement validators, a universal
native UUID type and a database acceleration claim are not justified by this
prototype. There is no general “C beats Rust” conclusion.

| Hypothesis | Evidence | Decision |
|---|---|---|
| Scalar text -> ordinary `uuid.UUID` | On Python 3.14, C takes about 24% less time than **direct pydantic-core**, on both ARM64 and Linux x86-64; much larger reduction versus stdlib | Candidate for an explicit `parse()` function in the existing project, subject to production hardening and the full supported Python matrix |
| Batch -> list of ordinary UUIDs | About 6% less time than TypeAdapter on ARM64, but 19%/52% **more** time on the two Linux configurations | No performance case for automatically replacing Pydantic's UUID list validator |
| Batch -> packed bytes | 70% less time than fastuuid + bytes conversion on ARM64, 46% on Linux/Python 3.14, only 6% on Linux/Python 3.12 | Candidate for a narrowly documented binary-processing API; platform-dependent benefit, not a universal claim |
| Parallel packed parsing | Four workers take 60–65% less elapsed time than the one-worker GIL-held case, with equal fixed total work, on all three configurations | Keep this direction for large stateless batches; it is not full free-threaded extension support or automatic async execution |
| Pydantic/FastAPI integration | Per-item C callbacks often regress; bulk/native variants do not establish a repeatable >=10% application win across the configurations | Do not ship these replacement adapters for speed |
| Compact native UUID objects | Roughly 4.0 MB of tracked retained allocation per 100k values versus 11.6 MB for standard objects; formatting can improve, but compatibility is incomplete and conversion can erase speed gains | Optional representation research only; not a drop-in UUID type |
| UUIDv4 | Direct OS-entropy C construction is 59–80% faster than stdlib here, but comparison with uuid-utils.compat changes sign by configuration | Possible convenience extension later; no competitive priority or equivalent-RNG superiority established |
| PostgreSQL consumer | No consistent end-to-end win over Pydantic, including the direct binary UUID adapter | No database speed claim; do not infer one from packed-parser microbenchmarks |
| UUIDv8 / monotonic modes / global monkey-patching | No new workload evidence; existing v7 already advances logical time on counter carry | Defer; unrelated to the parser evidence |

The next useful implementation, if chosen, is small: harden a scalar parser and
packed batch parsing inside fastuuid7, with explicit input/output contracts.
Retain standard framework validators. A new package would add compatibility and
maintenance obligations without a demonstrated broad application advantage.

## What was measured

The [pre-measurement protocol](../../tools/experiments/uuid_feasibility/PROTOCOL.md)
set equivalent outputs, fixed repeats and thresholds: >=20% reduction for a batch
operation, >=10% for a named application consumer, without material tail-latency
or memory regression. Inconclusive/noisy results remain inconclusive.

Main experiment commit: `7bdf7040c1d4d194a5f5c67383627bbbd1c12c84`.
All three main datasets report a clean source checkout and the same source/lock
identity. The installed fastuuid7 comparison is the PyPI 0.5.0 wheel.

| Configuration | Interpreter | CPU | Role |
|---|---|---|---|
| macOS ARM64 | CPython 3.14.6 | Apple M3 Pro, 12 CPUs | Independent clean-clone confirmation |
| Linux x86-64 | CPython 3.12.14 | Intel Xeon 6973P-C, 4 visible CPUs | Main comparison |
| Linux x86-64 | CPython 3.14.7 | AMD EPYC 7763, 4 visible CPUs | Main comparison |

**The Linux jobs used different CPUs. Their differences cannot be attributed to
the Python version alone.** Comparisons are within each configuration.

Pins: fastuuid 0.14.0, uuid-utils 1.0.0, Pydantic 2.13.5 / pydantic-core 2.46.5,
FastAPI 0.141.1, Starlette 1.6.0, uvicorn 0.53.0, psycopg 3.3.6, pyperf 2.10.0.
The full lock, compiler metadata and native-extension hashes are retained.

Python 3.14 configurations completed 155 microbenchmarks each; Python 3.12
completed 154 because stdlib UUIDv7 is unavailable there. Each benchmark used
five independent worker processes, three values each and warmup/calibration.
Each configuration also completed 160 HTTP samples covering
four variants, four scenarios, two offered rates and five randomized repeats.
Every HTTP response was checked: **254,400 measured requests, zero correctness
errors** across the three configurations, excluding warmup requests.

The two main PostgreSQL jobs each verified all 4.8 million persisted rows. The
direct-binary supplement and its later reproduction each verified another 3.6
million rows: **16.8 million rows verified in total**. Reproduction cohorts are
reported separately, not pooled or selected for the best result.

## Scalar parsing: correct the tempting headline

Main microbenchmarks call the public `TypeAdapter` interface. That includes a
Python wrapper, so it cannot establish an equivalent speedup over the native
Rust parser. The supplementary experiment compares direct `SchemaValidator`
calls, with the same standard `uuid.UUID` result.

| Python 3.14 scalar canonical parse | stdlib | TypeAdapter | Direct core schema | C prototype |
|---|---:|---:|---:|---:|
| ARM64 | 451 ns | 262 ns | 108 ns | 82 ns |
| Linux x86-64 | 1,157 ns | 569 ns | 282 ns | 214 ns |

The C reduction relative to direct core is 24.0% [22.4%, 25.4%] on ARM64 and
24.3% [22.4%, 26.3%] on the Linux supplement. Brackets are exploratory 95%
bootstrap intervals over independent process means. They do not correct for
multiple comparisons or prove portability. Direct-core supplementation covers
Python 3.14 only; no corresponding direct-core claim is made for Python 3.12.

The parser accepts canonical, hex, brace and URN text and preserves all 128 bits.
It intentionally rejects some extra spellings accepted by stdlib. It is not a
replacement for the full `uuid.UUID` constructor's fields/int/bytes_le/version
contract, and version validation is separate from lexical parsing.

## Batching and framework results

| 1,000 inputs, time per batch | ARM64 | Linux 3.12 | Linux 3.14 |
|---|---:|---:|---:|
| Packed C reduction vs fastuuid -> bytes -> joined buffer | 70.4% | 5.6% | 46.0% |
| C standard-object batch reduction vs Pydantic TypeAdapter | 5.8% | -52.4% | -18.8% |

Negative reductions mean a regression. The packed comparison includes required
conversion in the baseline and returns the same contiguous bytes. Standard and
native-object rows are not ranked as interchangeable APIs.

For example, ARM64 JSON model validation with 1,000 UUIDs takes about 81.6 us
with built-in Pydantic, 105.6 us with the C bulk adapter, and 150.6 us with the
per-item adapter. The native model improves dumping (54.6 us versus 79.8 us)
but has a different object type and does not provide the full strict-mode and
driver compatibility contract. Faster standalone parsing does not automatically
accelerate Pydantic's fused list/JSON validation path.

At 120 batch HTTP requests/s, CPU/request changes for the bulk adapter are +2.3%
reduction on ARM64 (interval crosses zero), **14.3% more CPU** on Linux 3.12, and
**5.5% more CPU** on Linux 3.14. Some native response-only cells improve, including
a 12% point estimate at 40 responses/s on Linux 3.12, but the same result is not
established across configurations and the native type's contract is narrower.

The 900 requests/s path scenario exposed scheduling overload: using a
post-measurement diagnostic cutoff of 100 ms, 27 individual samples exceeded
that p99 client scheduling lag, including every such sample
on the Linux 3.14 host. **Do not use those high-load path comparisons for latency
or capacity acceptance.** No samples were deleted; raw lag, elapsed time and
latency remain in the evidence. Lower-rate and batch/response scenarios remain
separate. Reported client latency also includes response validation; CPU/request
is measured in the separate server process. These are local synthetic workloads,
not production service-capacity benchmarks.

## Threads and memory

The threading study parses a fixed 2,097,152 UUIDs, returning identical packed
buffers, including owned input preparation and result construction. Executor
setup is outside timing. Median elapsed times:

| Configuration | GIL held, 1 worker | GIL released, 1 worker | GIL released, 4 workers |
|---|---:|---:|---:|
| ARM64 | 57.0 ms | 68.9 ms | 22.9 ms |
| Linux 3.12 | 268.5 ms | 271.2 ms | 94.7 ms |
| Linux 3.14 | 292.4 ms | 300.4 ms | 110.0 ms |

Detachment costs time at one worker and helps the large parallel workload. It
does not make the calling event-loop thread asynchronous. The extension still
requires the GIL outside its owned native-buffer region and is not declared safe
for free-threaded CPython or subinterpreters.

For 100,000 retained values, Python-tracked allocations are approximately 11.6 MB
for standard UUID lists, 4.0 MB for native objects, and 1.6 MB for packed bytes.
This is representation evidence, not equivalent Python API behavior. RSS and
tracemalloc are measured in separate fresh processes; RSS is a lifetime high-water
mark and its delta can be masked by an earlier import peak. Native allocations
outside Python's allocator may not appear in tracemalloc.

## PostgreSQL and UUIDv4 limits

All COPY comparisons store identical native PostgreSQL UUID values plus sequence
and payload, using a sequence primary key. They measure parser/adapter consumers,
not UUID index locality. Input generation and connection/DDL are outside timing;
parsing, required conversion, COPY and commit are inside it. Every row is reread.

On Linux 3.14, median times for 100k rows are 180.0 ms for Pydantic, 197.9 ms for
the C UUID batch, and 187.9 ms for packed C values converted to ordinary UUIDs.
The direct binary adapter supplement avoids that conversion but establishes no
reliable end-to-end win: the packed variant's mean reduction interval crosses zero
in both retained cohorts. Linux 3.12 COPY is especially noisy (one C-bulk sample
is 1.117 s versus another at 0.174 s). Apparent wins there are not grounds for a
portable database claim; client CPU also does not support a general improvement.

UUIDv4 direct entropy uses Linux getrandom and macOS arc4random_buf. The observed
58.6–79.6% reduction against stdlib is not proof of an equivalent improvement
against every generator. uuid-utils uses different entropy plumbing; its compat
API is faster than this prototype on both measured Python 3.14 configurations
and slower on the measured 3.12 configuration. Entropy/fork equivalence was not
established by performance or small uniqueness samples.

## Verification and reproducibility

- Existing production/property suite: **520 passed** in a `git clone --no-local`.
- Experiment contract suite: **20 passed** on ARM64 and each Linux Python job;
  includes 2,000 Hypothesis examples, invalid input, batch ordering, value/hash
  equivalence, threaded outputs, Pydantic error/strictness and ASGI round trips.
- C parser/formatter: **200,000 seeded libFuzzer executions under ASan/UBSan in
  each Linux job**, no reported violation. This does not sanitize all CPython or
  replace future production-extension review.
- Ruff and diff checks pass. Two upstream Starlette/AnyIO deprecation warnings
  are retained; they are not experiment failures.
- The first clean build exposed setuptools flat-layout autodiscovery; explicit
  empty Python package/module lists fixed it before final measurements. Smoke
  runs and the failed initial workflow are not performance evidence.
- Local libFuzzer runtime and Docker registry DNS were unavailable; the successful
  Linux workflows supplied sanitizer and PostgreSQL 18.3 evidence.

Run instructions and exact scope are in the
[laboratory README](../../tools/experiments/uuid_feasibility/README.md).
Raw results, [hash manifest](../../tools/experiments/uuid_feasibility/results/manifest.json)
and [computed summary](../../tools/experiments/uuid_feasibility/results/summary.json)
are retained in the repository. `analyze.py` regenerates the summary from raw JSON;
it bootstraps process means/repeats, not thousands of correlated inner iterations.
Intervals are exploratory, five-repetition evidence; no significance or production
ranking is inferred from small noisy differences.

Successful workflows:

- [Main Linux matrix, 7bdf704](https://github.com/nekrasovp/uuidv7/actions/runs/35366226764)
- [Direct binary COPY, d27f5b2](https://github.com/nekrasovp/uuidv7/actions/runs/35367130385)
- [Direct core baseline plus retained COPY reproduction, fb8fb57](https://github.com/nekrasovp/uuidv7/actions/runs/35367489768)

The supplements add consumers and analysis only: the parser, microbenchmark,
framework/HTTP harness, original COPY harness and dependency lock are unchanged
from the main measured commit. No main merge, package release, runtime activation
or claim of a production-ready general UUID replacement is part of this study.
