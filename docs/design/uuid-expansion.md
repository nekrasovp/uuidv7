# UUID expansion: implementation plan (2026-11-09)

Base: `4d9912368da259590c31092837fc985bda8a3951` (fastuuid7 0.5.0).
Worktree: `uuidv7-next`, branch `feature/uuid4-parsing`.
The September feasibility study remains in [PR #15](https://github.com/nekrasovp/uuidv7/pull/15)
at `225aec2fb436f15b4e83ae84b0b11828ea6b5ffa`; its measurements are historical.

## Scope and sequence

1. Promote CPython 3.15 to the stable test and wheel matrix. Keep the existing GIL
   requirement and Python 3.9 floor; check the actual built artifacts.
2. Add `uuid4`, `uuid4_str`, `uuid4_bytes`, and corresponding `_many` operations.
   Reuse the OS entropy pool and PID reset. Return standard UUIDs for `uuid4`.
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
