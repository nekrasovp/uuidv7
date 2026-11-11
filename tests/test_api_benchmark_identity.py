"""Release version bumps must not weaken the benchmark dependency pins."""

import runpy
from pathlib import Path

import pytest

check_packages = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "benchmarks" / "api" / "common.py")
)["check_packages"]


def test_new_candidate_version_keeps_published_baseline():
    baseline = {"fastuuid7": "0.6.0", "pydantic": "2.14.3", "uuid-utils": "1.2.0"}
    candidate = {**baseline, "fastuuid7": "0.6.1"}
    check_packages(baseline, baseline, "0.6.0")
    check_packages(candidate, baseline, "0.6.1")
    with pytest.raises(AssertionError):
        check_packages(candidate, candidate, "0.6.1")


@pytest.mark.parametrize(
    "change",
    [
        {"fastuuid7": "0.6.0"},
        {"pydantic": "2.15.0"},
        {"uuid-utils": "1.3.0"},
        {"unexpected-package": "1.0"},
    ],
)
def test_candidate_rejects_wrong_version_or_dependency_drift(change):
    baseline = {"fastuuid7": "0.6.0", "pydantic": "2.14.3", "uuid-utils": "1.2.0"}
    candidate = {**baseline, "fastuuid7": "0.6.1", **change}
    with pytest.raises(AssertionError):
        check_packages(candidate, baseline, "0.6.1")
