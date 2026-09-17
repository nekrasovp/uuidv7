"""Pure fail-closed boundaries; full persistence checks run against PostgreSQL 18."""

import uuid

import pytest

from benchmarks.workloads.run import (
    HISTORY_START_MS,
    cases_for,
    check_config,
    historical_ms,
    random_at,
    validate_uuid,
)


def test_matrix_keeps_strategies_separate_and_compares_matching_shapes():
    live = cases_for("copy")
    assert live == cases_for("sqlalchemy")
    assert {c.name for c in live if c.group == "client_uuid7"} == {
        "checkout_scalar",
        "checkout_batch",
        "published_scalar",
        "published_batch",
        "stdlib_uuid7",
        "uuid_utils",
        "uuid6",
    }
    assert next(c for c in live if c.name == "stdlib_uuid4").group == "uuid4_control"
    assert next(c for c in live if c.name == "postgres_uuid7").group == "server_strategy"
    assert all(c.historical for c in cases_for("historical"))
    assert "stdlib_uuid7" not in {c.name for c in cases_for("historical")}
    with pytest.raises(ValueError, match="scenario"):
        cases_for("unknown")


@pytest.mark.parametrize("ms", [0, HISTORY_START_MS, (1 << 48) - 1])
def test_reference_has_exact_timestamp_rfc_layout_and_unique_sample(ms):
    ids = [random_at(ms) for _ in range(128)]
    assert len(set(ids)) == len(ids)
    assert all(validate_uuid(value, exact_ms=ms) == ms for value in ids)


def test_rejects_wrong_layout_legacy_time_and_driver_shape():
    value = random_at(HISTORY_START_MS)
    with pytest.raises(ValueError, match="instance"):
        validate_uuid(str(value))
    with pytest.raises(ValueError, match="version/variant"):
        validate_uuid(uuid.uuid4())
    with pytest.raises(ValueError, match="version/variant"):
        validate_uuid(uuid.UUID(int=value.int & ~(3 << 62)))
    with pytest.raises(ValueError, match="historical timestamp"):
        validate_uuid(value, exact_ms=HISTORY_START_MS + 1)
    with pytest.raises(ValueError, match="clock window"):
        validate_uuid(value, lower_ms=HISTORY_START_MS + 1, upper_ms=HISTORY_START_MS + 1000)


@pytest.mark.parametrize(
    "name", ["postgres", "production", "fastuuid7_workloads_x; DROP DATABASE x", ""]
)
def test_refuses_nondisposable_database_before_connection(name):
    with pytest.raises(ValueError, match="disposable prefix"):
        check_config(100, 10, 3, name)


@pytest.mark.parametrize("numbers", [(0, 10, 3), (100, -1, 3), (100, 10, 0)])
def test_refuses_invalid_workload_sizes(numbers):
    with pytest.raises(ValueError, match="positive"):
        check_config(*numbers, "fastuuid7_workloads_test")


def test_history_contains_repeated_and_out_of_order_exact_milliseconds():
    times = [historical_ms(i) for i in range(100_000)]
    assert times[:8] == [HISTORY_START_MS] * 8
    assert all(HISTORY_START_MS <= t < HISTORY_START_MS + 7 * 86_400_000 for t in times)
    assert any(b < a for a, b in zip(times, times[1:]))


def test_historical_batch_is_an_explicit_addition_not_a_scalar_substitute():
    standard = cases_for("historical")
    extended = cases_for("historical", include_historical_batch=True)
    assert extended[1:] == standard
    assert extended[0].name == "checkout_at_batch"
    assert extended[0].historical and extended[0].batch
