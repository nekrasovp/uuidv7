# Release checklist

## Prepare

1. Update `pyproject.toml`, `uuidv7/__init__.py`, and
   `uuidv7/uuidv7/__init__.py` to the same version.
2. Replace `Unreleased` in `CHANGELOG.md` with the release date.
3. Run:

   ```bash
   uv sync --python 3.14 --extra dev --extra release --extra properties --locked
   uv run --extra dev --extra release --extra properties --locked pytest
   uv run --extra dev --extra release --locked ruff check .
   uv run --extra dev --extra release --locked ruff format --check .
   uv run --extra dev --extra release --locked mypy
   uv build
   uv run --extra dev --extra release --locked twine check dist/*
   python tools/check_release_version.py v0.5.0
   ```

4. Run the scalar, competitor, batch, clock-source, and batch-clock experiment benchmarks from the
   exact release commit. Review output shapes and security guarantees before
   making comparative claims.
   Run the PostgreSQL 18 workload matrix with `--include-historical-batch` and
   retain its JSON/Markdown reports. Keep the isolated workload lock's published
   fastuuid7 0.4.0 baseline; it must not resolve to the candidate checkout.
   Require the integration/property and Python prerelease workflows as well.
5. Verify the exact commit in a clean `git clone --no-local`, with locked dependencies,
   tests, lint, typing, source/wheel builds and installed-wheel smoke tests.
   Check that the sdist includes workload locks, historical examples, integer
   conversion headers and free-threading experiment sources, with no nested
   virtual environments. Installed wheels must remain limited to runtime packages.
6. Push the release commit and wait for CI, benchmarks, and every wheel job to pass.
   Review both timing results and skipped/rejected cases. Attach CI benchmark
   reports to the GitHub release; do not copy timing claims from older releases.

## Publish

1. Create the matching `vX.Y.Z` GitHub release. The publish workflow validates
   the tag, builds fresh artifacts, runs `twine check`, and uses PyPI trusted
   publishing.
2. Verify the PyPI page shows the expected version, Python range, SPDX license,
   project links, and wheels.
3. Install one published wheel into a clean environment and smoke-test both
   import paths plus scalar, historical, and batch generation. Compare all published artifact
   filenames and SHA-256 hashes with the publish workflow artifacts.
   The installed-wheel suite includes `tests/test_historical_batch.py`; its
   migration example comes from the corresponding source checkout. Prerelease
   and research artifacts are not stable release wheels.

## Security release 0.3.0

After 0.3.0 artifacts are available, publish a GitHub Security Advisory for the
non-cryptographic PRNG and inherited post-fork state in versions through 0.2.x.
The advisory should tell Python 3.8 users to upgrade Python because a resolver
can otherwise keep selecting the unsupported 0.2.x release.

## Announce

Use CI-generated benchmark links in announcements. Lead with fork safety,
stdlib compatibility, explicit output shapes, and the native batch API. Track
the four-week median of daily PyPI downloads rather than release-day traffic,
along with stars, external dependents, and documentation referrals.
