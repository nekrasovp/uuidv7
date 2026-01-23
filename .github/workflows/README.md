# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD automation.

## Workflows

### `ci.yml` - Continuous Integration

Runs on every push and pull request to main/master/develop branches.

**What it does:**
- Tests the package on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13
- Runs linting with ruff
- Builds the package to ensure it compiles correctly
- Uploads build artifacts

### `publish.yml` - PyPI Publishing

Runs when a new GitHub release is published.

**What it does:**
- Builds source distribution and wheel
- Publishes to PyPI using trusted publishing
- No API tokens required (uses OIDC)

**How to trigger:**
1. Update version in `pyproject.toml` and `uuidv7/uuidv7/__init__.py`
2. Create a new GitHub Release with a tag (e.g., `v0.1.0`)
3. The workflow automatically publishes to PyPI

### `benchmark.yml` - Performance Benchmarks

Runs benchmarks on main branch pushes and can be manually triggered.

**What it does:**
- Runs the benchmark suite
- Can comment results on pull requests

## Setup

### PyPI Trusted Publishing

To enable automatic PyPI publishing:

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Navigate to "API tokens" → "Add API token"
3. Select "Trusted publishing" → "Add"
4. Add your GitHub repository: `yourusername/uuidv7`
5. The workflow will automatically authenticate using OIDC

No secrets or tokens need to be configured in GitHub!

## Local Testing

You can test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test CI workflow
act push

# Test publish workflow (dry run)
act workflow_dispatch
```

