# uuidv7

[![CI](https://github.com/yourusername/uuidv7/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/uuidv7/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/fastuuid7.svg)](https://badge.fury.io/py/fastuuid7)

A high-performance UUID v7 generation library implemented in C with Python bindings.

## Features

- Fast UUID v7 generation using C implementation
- RFC 9562 compliant UUID v7 format
- Python 3.8+ support
- Thread-safe implementation
- **High Performance**: See [BENCHMARKS.md](BENCHMARKS.md) for performance comparisons

## Installation

### Using uv (recommended)

```bash
uv pip install fastuuid7
```

### Using pip

```bash
pip install fastuuid7
```

### From source

```bash
git clone https://github.com/yourusername/uuidv7.git
cd uuidv7
uv pip install -e .
```

## Usage

```python
from uuidv7.uuidv7 import generate_uuid7

# Generate a UUID v7
uuid = generate_uuid7()
print(uuid)  # e.g., "018f1234-5678-7abc-def0-123456789abc"
```

## Development

### Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Running Tests

```bash
# Using pytest
uv run pytest

# Using uv
uv run pytest tests/
```

### Linting and Formatting

```bash
# Run ruff linter
uv run ruff check .

# Run ruff formatter
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Building

```bash
# Build wheel
uv build

# Build source distribution
uv build --sdist
```

### Running Benchmarks

```bash
# Run performance benchmarks comparing different implementations
python benchmarks/benchmark.py

# Or using uv
uv run python benchmarks/benchmark.py
```

See [BENCHMARKS.md](BENCHMARKS.md) for detailed performance comparisons with other UUID v7 implementations.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs tests on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13
  - Runs linting with ruff
  - Builds the package to verify it compiles correctly
  - Triggers on push and pull requests

- **Publish Pipeline** (`.github/workflows/publish.yml`):
  - Automatically publishes to PyPI when a new release is created
  - Uses trusted publishing (no API tokens required)
  - Can be manually triggered via workflow_dispatch

### Publishing a New Release

1. Update the version in `pyproject.toml` and `uuidv7/uuidv7/__init__.py`
2. Create a new [GitHub Release](https://github.com/yourusername/uuidv7/releases/new)
3. The workflow will automatically build and publish to PyPI

### Setting Up PyPI Trusted Publishing

To enable automatic publishing:

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Navigate to "API tokens" → "Add API token"
3. Select "Trusted publishing" → "Add"
4. Add your GitHub repository: `yourusername/uuidv7`
5. The workflow will automatically use trusted publishing (no token needed)

## License

MIT License - see LICENSE file for details.

## Author

Pavel Nekrasov
