# UUID feasibility study

Protocol fixed before prototype measurements, 2026-09-18.
Base: fastuuid7 0.5.0, `4d9912368da259590c31092837fc985bda8a3951`.
Owner branch: `research/uuid-feasibility`, isolated worktree.

## Scope and terminal result

Authorized: benchmark harness, isolated research C extension, correctness/fuzz
checks, disposable PostgreSQL, local and GitHub Actions runs, task commits and
research branch/PR. Finish with reproducible raw results and a decision per
hypothesis. Owned paths: this directory, one dedicated workflow, study report.
Production package, root dependencies, versions, main, releases and outreach are
outside this study. Prototypes are not public API or production support claims.

## Hypotheses

1. C parsing can reduce cost of producing a real stdlib UUID, compared with the
   best tested equivalent implementation (including pydantic-core).
2. Batching or packed binary output reduces a complete consumer's work.
3. A compact native UUID representation pays for conversion/integration costs.
4. OS-random UUIDv4 and formatting justify expanding the existing generator.
5. Stateless bulk parsing benefits from releasing the GIL with 1/2/4 workers.

Baseline: pinned stdlib/Python, uuid-utils (native and compat), fastuuid,
pydantic-core (reused TypeAdapter), released fastuuid7 0.5.0.
An API absent from a library is not a failure or an artificial slow fallback.

## Equivalence and input contracts

Shared valid corpus: canonical mixed-case UUID text, 32 hex digits, braces and
lowercase urn:uuid: prefix; v4/v7 and arbitrary 128-bit values. Binary input is
exactly 16 bytes, separate from textual bytes. No version bits are rewritten.
Canonical parsing rejects misplaced hyphens, embedded NUL, non-ASCII, bad lengths
and non-hex. Stdlib's additional permissive spellings are recorded as an explicit
compatibility difference, not silently accepted as full drop-in equivalence.
Invalid and boundary cases are checked before timing, including batch index.
Every ranked case has the same successful input domain and output representation.
Native objects, stdlib objects, bytes, packed bytes and strings have separate rows.
Required conversions are inside the timed consumer. Pydantic adapters accept
existing UUID instances unchanged and fall back to the built-in UUID schema for
invalid/other inputs, preserving framework errors and strictness in tested cases.

## Measurement plan

First baseline without prototype: scalar parse/format/generation; batch sizes
1/100/1000; model Python/JSON validation and serialization. Then prototype
comparison. Fixed deterministic diverse corpus, generated outside timers.
Use pyperf calibrated loops, fresh workers, warmups, raw JSON and metadata.
Final runs: 5 processes, 3 values, 1 warmup, minimum value duration 50 ms.
Do not stop/rerun until a desired speedup appears. Instability is reported.
Profiling/instrumentation and memory measurements are separate from timings.

Application: real uvicorn server plus separate HTTP load process, reusable
connections; path UUID, request lists and response lists, valid and invalid.
Fixed offered rates at two levels, five randomized repeats per variant, warmup;
record throughput, CPU/request, p50/p95/p99, errors, response integrity and
scheduling lag (to expose client/server overload). TestClient is correctness only.
Bulk consumer: text UUIDs -> stdlib UUID -> psycopg binary COPY -> persisted rows,
with complete post-commit verification. Native/packed conversion included.

Initial platforms: Linux x86-64 Python 3.12/3.14; macOS ARM64 Python 3.14 confirms
candidate results. Compiler/build flags, source commit, lock and extension hashes,
package versions and CPU/platform are recorded. Benchmarks on one host run
sequentially. Windows/other Python compatibility is not inferred from this matrix.

## Decision rules fixed before results

- Correctness and equivalent representation are prerequisites.
- >=20% less time for an equivalent bulk operation is a candidate batch API win.
- >=10% less CPU/request or end-to-end time in a named consumer is an integration
  candidate, provided p95/p99 and memory have no reproducible >10% regression.
- Compact objects must preserve a benefit after mandatory consumer conversions;
  otherwise restrict to measured native-only scenarios. Their compatibility cost
  remains a separate reason not to ship a prototype.
- Point estimates crossing thresholds without repeatable separation from noise
  are inconclusive. Inspect independent-run distributions/intervals, not best runs.
- Any improvement only against stdlib is described as such; do not imply victory
  over the best compatible baseline. No weighted overall winner across unlike APIs.
- Full uuid-utils alternative needs useful results in multiple operation families
  and integrations, plus a feasible compatibility plan. A single bulk win justifies
  a scoped extension, not a new general-purpose library.
- One exploratory pass and one fixed final comparison after correctness repairs;
  future optimization ideas are a follow-up, not an unbounded tuning loop.

## Existing evidence

The 0.5.0 release assets are the exact-release generation/PostgreSQL baseline:
https://github.com/nekrasovp/uuidv7/releases/tag/v0.5.0 . Older committed 0.2/0.4
reports retain their original identities. The existing free-threading study in
docs/design/free-threading.md concerns the stateful generator, not this parser.

Primary methodology: https://pyperf.readthedocs.io/en/latest/run_benchmark.html
and https://docs.pydantic.dev/latest/concepts/performance/ .
