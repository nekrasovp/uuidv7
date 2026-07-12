# Contributing

Bug reports, performance measurements, integration examples, and focused pull
requests are welcome.

## Development setup

```bash
git clone https://github.com/nekrasovp/uuidv7.git
cd uuidv7
uv sync --extra dev
```

## Validation

Run the same core checks used by CI:

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run --extra dev mypy
uv build
uv run --extra release twine check dist/*
```

Building the complete wheel matrix requires Python 3.11+ because current
`cibuildwheel` releases no longer run on older Python versions:

```bash
uv sync --python 3.14 --extra dev --extra release
```

Changes to UUID generation must include tests for format, monotonicity,
collision behavior, clock rollback, and relevant process/thread behavior.
Performance changes should include reproducible before/after benchmark output
with OS, CPU, Python version, package versions, and iteration count.
