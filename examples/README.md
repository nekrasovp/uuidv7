# Usage Examples

This directory contains practical examples demonstrating how to use the `fastuuid7` library.

## Examples

### 1. `basic_usage.py`

Basic usage examples including:
- Single UUID generation
- Multiple UUID generation
- `uuid.UUID` object attributes such as `version`, `variant`, and `time`
- UUID format validation
- Performance demonstration

**Run:**
```bash
python examples/basic_usage.py
```

### 2. `batch_generation.py`

Examples for high-throughput scenarios:
- Batch UUID generation
- Uniqueness verification
- Timestamp ordering demonstration

**Run:**
```bash
python examples/batch_generation.py
```

### 3. `database_usage.py`

Real SQLAlchemy 2 integration:
- Using UUID v7 as an ORM primary-key default
- Persisting `uuid.UUID` values through SQLAlchemy's `Uuid` type
- Querying records in UUID/time order

**Run:**
```bash
uv run --with sqlalchemy python -m examples.database_usage
```

## Running Examples

All examples can be run from the project root:

```bash
# Make sure the package is installed in editable mode
uv pip install -e .

# Run examples using uv (recommended - ensures correct environment)
uv run python examples/basic_usage.py
uv run python examples/batch_generation.py
uv run --with sqlalchemy python -m examples.database_usage
```

Or directly with Python (after installing the package):

```bash
# Install the package first
uv pip install -e .

# Then run examples
python examples/basic_usage.py
python examples/batch_generation.py
python examples/database_usage.py
```

**Note**: Examples must be run after installing the package with `uv pip install -e .` to ensure the `uuidv7` package is available in the Python path.

## Requirements

- Python 3.9+
- `fastuuid7` package installed (see main README for installation)
