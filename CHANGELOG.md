# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## 0.5.0 - 2026-09-18

### Added

- `uuid7_at_many(*, unix_ms=...)` generates historical UUIDs from a finite
  iterable, preserving each exact timestamp and validating the entire input
  before generation. Both import paths expose the typed API.
- A transactional SQLite migration example persists old-to-new ID mappings,
  resumes after interruption and verifies related-record integrity.
- Executed SQLAlchemy, Django, Pydantic/FastAPI and psycopg integration tests
  with PostgreSQL, plus property tests for UUID compatibility.
- Reproducible PostgreSQL 18 bulk INSERT, binary COPY and historical-import
  workloads with pinned dependencies, persisted-row verification and raw reports.
- An isolated free-threading prototype and architecture decision, plus adoption
  guidance, public dependency evidence and a technical article draft.

### Changed

- Python 3.14+ integer conversion uses the public `PyLongWriter` API with a
  checked layout and public fallback. Older supported Python keeps its fast
  path; `_PyLong_FromByteArray` is no longer used.
- A separate Linux/macOS/Windows matrix checks Python 3.15.0rc2. Stable support
  remains Python 3.9–3.14; this release does not claim ABI3 or GIL-free support.
- Release wheels run the historical batch and migration suite as well as the
  existing boundary tests. The published benchmark baseline is fastuuid7 0.4.0.

## 0.4.0 - 2026-09-17

### Added

- `uuid7_at(*, unix_ms=...)` for historical records, preserving the exact 48-bit
  Unix millisecond timestamp with 74 OS-CSPRNG random bits. It is independent of
  the live generator's monotonic counter and available from both import paths.
- Deterministic counter-carry, timestamp-exhaustion, repeated clock-rollback,
  historical-data isolation, fork-entropy, and subprocess regression tests.
- A reproducible C-core batch-clock experiment, including a scheduling-pause
  probe. Production batch APIs retain per-UUID wall-clock reads.

### Changed

- Benchmarks pin competitors, isolate each case in its own process, validate
  actual output types and timestamp layout, and identify entropy, ordering and
  fork guarantees. The published comparison baseline is now fastuuid7 0.3.0.
- Added modern fastuuidv7 string/bytes/hex/sequential cases and uuid-utils'
  stdlib compatibility path; corrected the uuid-v7 import path.
- Development dependencies are locked; mypy stays on its Python-3.9-compatible
  release line. Wheel builds run the boundary suite and installed-package smoke
  tests on all supported build platforms.

### Fixed

- Timestamp checks respect Python's reported clock resolution, including the
  coarse Windows clock used by Python versions before 3.13.
- Exhaustion of the final representable UUIDv7 timestamp now raises
  `OverflowError` instead of wrapping to zero. Failed generation does not commit
  partial timestamp/counter changes; failed batches return no partial result.
- Legacy-draft UUIDs with incorrect epoch encoding and changed return types
  cannot silently enter the benchmark's valid comparison results.

## 0.3.0 - 2026-07-12

### Added

- System CSPRNG-backed UUID randomness with automatic process-fork reseeding.
- A regression test for duplicate generator state after `fork()`.
- Canonical `fastuuid7` import alias while retaining the existing `uuidv7` API.
- Type stubs and `py.typed` markers for both public import paths.
- Native batch APIs for UUID objects, native objects, strings, and contiguous bytes.
- Release-version and distribution-metadata validation.

### Changed

- Runtime wheels contain only the public packages, compiled extension, typing
  metadata, package metadata, and license.
- Development commands install the `dev` extra explicitly.
- Packaging metadata uses a PEP 639 SPDX expression and includes the MIT license.
- The minimum supported Python version is now 3.9; Python 3.8 is end-of-life.

### Fixed

- Forked processes could inherit identical PRNG and counter state.
- The distributed MIT license file was empty.

## 0.2.0 - 2026-06-19

- Added the `uuid.UUID`-compatible API and explicit native-object, string, and
  bytes fast paths.
- Added Python 3.14 and multi-platform wheel support.

## 0.1.0 - 2026-06-10

- Initial PyPI release.
