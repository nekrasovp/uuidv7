# UUID expansion: implementation plan (2026-11-09)

Base: `4d9912368da259590c31092837fc985bda8a3951` (fastuuid7 0.5.0).
Worktree: `uuidv7-next`, branch `feature/uuid4-parsing`.
The September feasibility study remains in [PR #15](https://github.com/nekrasovp/uuidv7/pull/15)
at `225aec2fb436f15b4e83ae84b0b11828ea6b5ffa`; its measurements are historical.

## Scope and sequence

1. Promote CPython 3.15 to the stable test and wheel matrix. Keep the existing GIL
   requirement and Python 3.9 floor; check the actual built artifacts.
2. Add `uuid4`, `uuid4_str`, `uuid4_bytes`, and corresponding `_many` operations.
   Reuse the OS entropy pool and fork reset (native POSIX hook, PID fallback). Return standard UUIDs for `uuid4`.
   UUIDv4 consumes 122 random bits and has no ordering promise. It must not
   advance the UUIDv7 clock/counter. Never reuse returned objects.
3. Add `parse`, `parse_many`, `parse_bytes_many`, and `format_uuid`.
   Parsing accepts ASCII hex (32 digits), canonical hyphenated text, canonical
   text in braces, or a case-insensitive `urn:uuid:` prefix plus canonical text.
   Hex digits are case-insensitive. Other text is rejected, not normalized.
   Preserve all 128 bits and accept all versions/variants, including nil/max.
   Return actual `uuid.UUID` objects; packed output is 16 network-order bytes
   per input. Formatting accepts UUID objects, UUID7Obj, or exactly 16 bytes.
   Native UUID7Obj keeps its v7-only meaning.
4. Benchmark current reference versions with declared output contracts, retained
   results, discarded results, serialization, and process-level repetitions.
   Include uuid-utils 1.2.0 and its legacy 0.19.0 line in separate environments.
5. Validate SDK consumption (LangChain/LangSmith), type identity, pickle,
   Pydantic/JSON, parser failures, entropy failure, fork, and clock rollback.
   Run the final checks in a fresh clone and submit a reviewable PR.

## Decisions and boundaries

The parser uses the production integer helper, not the prototype's private
CPython conversion. No new runtime dependency, package rename, native general
UUID class, implicit framework validator replacement, ABI3 promise, or
free-threaded claim is part of this change. No marketing/outreach is included.
Local changes, commits, branch push and a PR are within this implementation;
publishing a package is a distinct release step after verification.

The September result that request parsing alone did not produce a consistent
FastAPI speedup remains valid for that experiment. Standalone parsing, bulk
conversion, and UUIDv4 are useful independently and need their own measurements.
No universal performance claim follows from a single machine or representation.

## Acceptance evidence

Record exact source/interpreter/dependency identities with new measurements.
Require standard UUID equality/hash/serialization behavior, negative parser
cases, batch cleanup, CSPRNG failure without partial results, fork isolation,
and no v7 ordering regression. Run lint, typing, unit/property/integration tests,
parser sanitizers and installed-wheel checks. CI must cover Linux/macOS/Windows.
Keep old benchmark files and the research PR unchanged.


## Implemented and checked

All five stages are implemented in PR #16. Source `4e47ca2` passed a fresh
`git clone --no-local` run on CPython 3.9–3.15: 709 tests on 3.9–3.13 and
714 on 3.14–3.15, including properties and entropy/fork failure injection.
The original first implementation passed 705/710 before additional fork tests.
Pydantic/FastAPI's four cases and the locked SDK consumer check also passed.
Local ASan/UBSan exercised 200,000 parser inputs; hosted libFuzzer repeats this.
Ruff, mypy, actionlint and diff checks passed.

[New benchmark evidence](../../benchmarks/results/uuid-operations-2026-11-09/README.md)
retains current, legacy, published-baseline and pre-optimization results.
It supports standard-object v4 and parser utility without claiming FastAPI gains.

CI required two portability fixes: pin Ubuntu 24.04 for setup-python's 3.9
availability, and give the oversized parser input a short pytest ID so Windows
can set PYTEST_CURRENT_TEST. The research-only free-threading wrapper includes
the production core and already owns eager fork reset; it now marks that hook
as installed to avoid a second lazy reset callback. Its 18 local contracts pass
on both GIL and free-threaded 3.14. This does not enable no-GIL production support.

Final hosted check state and exact review head are linked from
[PR #16](https://github.com/nekrasovp/uuidv7/pull/16). The source version remains
unreleased; no PyPI publishing or upstream outreach occurred in this work.


Final CI encountered upstream HTTP 504 responses for setup-python's 3.10
release asset and cibuildwheel's get-virtualenv bootstrap archive. CI now uses
uv-managed interpreters for the main test matrix and cibuildwheel's documented
`build[uv]` frontend (with its uv extra) for wheel environments. This changes the
bootstrap path, retains normal verified downloads, and preserves all supported
Python versions and installed-wheel tests.
