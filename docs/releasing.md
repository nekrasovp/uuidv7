# Release checklist

## Prepare

1. Update `pyproject.toml`, `uuidv7/__init__.py`, and
   `uuidv7/uuidv7/__init__.py` to the same version.
2. Replace `Unreleased` in `CHANGELOG.md` with the release date.
3. Run:

   ```bash
   uv sync --python 3.14 --extra dev --extra release
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy
   uv build
   uv run twine check dist/*
   python tools/check_release_version.py v0.3.0
   ```

4. Run the scalar, competitor, batch, and clock-source benchmarks from the
   exact release commit. Review output shapes and security guarantees before
   making comparative claims.
5. Push the release commit and wait for CI and every wheel job to pass.

## Publish

1. Create the matching `vX.Y.Z` GitHub release. The publish workflow validates
   the tag, builds fresh artifacts, runs `twine check`, and uses PyPI trusted
   publishing.
2. Verify the PyPI page shows the expected version, Python range, SPDX license,
   project links, and wheels.
3. Install one published wheel into a clean environment and smoke-test both
   import paths plus scalar and batch generation.

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
