# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

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
