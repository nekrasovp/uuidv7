# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

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
