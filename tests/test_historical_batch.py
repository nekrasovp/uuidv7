"""Historical batch contract and a durable, transactional migration example."""

import gc
import importlib.util
import os
import pickle
import select
import sqlite3
import subprocess
import sys
import uuid
import weakref
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import fastuuid7
import uuidv7
from uuidv7.uuidv7_impl.uuid7_gen import (
    _configure_uuid7,
    _generate_uuid7_bytes_for_tests,
    _reset_state_for_tests,
    _set_state_for_tests,
)

MAX_MS = (1 << 48) - 1
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "historical_migration" / "migrate.py"
spec = importlib.util.spec_from_file_location("historical_migration", EXAMPLE)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


@pytest.fixture(autouse=True)
def isolated_state():
    _reset_state_for_tests()
    yield
    _configure_uuid7(uuidv7._UUID7, uuid.SafeUUID.unknown)
    _reset_state_for_tests()


def counter_of(value):
    return (((value.int >> 64) & 0xFFF) << 30) | ((value.int >> 32) & ((1 << 30) - 1))


@pytest.mark.parametrize("factory", [list, tuple, iter, lambda values: (v for v in values)])
def test_order_boundaries_aliases_and_scalar_contract_parity(factory):
    assert fastuuid7.uuid7_at_many is uuidv7.uuid7_at_many
    timestamps = [MAX_MS, 0, 1, 42, 42, 1_645_557_742_123, 1 << 47]
    values = fastuuid7.uuid7_at_many(unix_ms=factory(timestamps))
    assert isinstance(values, list) and len(values) == len(timestamps)
    for ms, value in zip(timestamps, values):
        scalar = fastuuid7.uuid7_at(unix_ms=ms)
        assert type(value) is type(scalar)
        assert value.time == value.int >> 80 == scalar.time == ms
        assert value.version == scalar.version == 7
        assert value.variant == scalar.variant == uuid.RFC_4122
        assert value.is_safe == scalar.is_safe == uuid.SafeUUID.unknown
        assert uuid.UUID(str(value)) == uuid.UUID(bytes=value.bytes) == value
        assert pickle.loads(pickle.dumps(value)) == value
        with pytest.raises(TypeError):
            value.int = 0


@pytest.mark.parametrize("empty", [[], (), iter(()), range(0), "", b""])
def test_empty_iterables(empty):
    assert fastuuid7.uuid7_at_many(unix_ms=empty) == []


@pytest.mark.parametrize("value", [None, True, False, 3, 1.5])
def test_input_must_be_iterable(value):
    with pytest.raises(TypeError):
        fastuuid7.uuid7_at_many(unix_ms=value)


def test_keyword_only_and_required_argument():
    for args, kwargs in [(([1],), {}), ((), {}), ((), {"timestamps": [1]})]:
        with pytest.raises(TypeError):
            fastuuid7.uuid7_at_many(*args, **kwargs)


class IndexOnly:
    def __index__(self):
        return 42


@pytest.mark.parametrize("value", [True, False, 1.5, "123", None, IndexOnly(), object()])
def test_non_integer_elements_match_scalar_rejection(value):
    with pytest.raises(TypeError, match="integer"):
        fastuuid7.uuid7_at(unix_ms=value)
    with pytest.raises(TypeError, match=r"unix_ms\[2\].*integer"):
        fastuuid7.uuid7_at_many(unix_ms=iter([0, 42, value]))


@pytest.mark.parametrize("value", [-1, -(1 << 100), 1 << 48, 1 << 64, 1 << 100])
def test_invalid_range_matches_scalar_rejection(value):
    with pytest.raises(ValueError, match="unix_ms"):
        fastuuid7.uuid7_at(unix_ms=value)
    with pytest.raises(ValueError, match=r"unix_ms\[2\]"):
        fastuuid7.uuid7_at_many(unix_ms=[0, MAX_MS, value])


def test_int_subclasses_bytes_and_mapping_keys_follow_item_contract():
    class Milliseconds(int):
        pass

    for values in [[Milliseconds(42)], bytes([0, 42, 255]), {42: "ignored", 0: "ignored"}]:
        assert [v.time for v in fastuuid7.uuid7_at_many(unix_ms=values)] == list(values)


def test_iterable_consumed_once_fully_before_element_validation():
    events = []

    class Once:
        def __iter__(self):
            assert not events
            events.append("iter")
            for ms in [42, False, 0]:
                events.append(ms)
                yield ms

    with pytest.raises(TypeError, match=r"unix_ms\[1\]"):
        fastuuid7.uuid7_at_many(unix_ms=Once())
    assert events == ["iter", 42, False, 0]
    iterator = iter([42, 0])
    assert [v.time for v in fastuuid7.uuid7_at_many(unix_ms=iterator)] == [42, 0]
    assert fastuuid7.uuid7_at_many(unix_ms=iterator) == []


def test_iteration_error_propagates_even_after_invalid_element():
    class SourceError(Exception):
        pass

    def broken():
        yield 42
        yield False
        raise SourceError("late source failure")

    with pytest.raises(SourceError, match="late source failure"):
        fastuuid7.uuid7_at_many(unix_ms=broken())


def test_full_validation_precedes_any_uuid_construction():
    constructed = []

    class Probe:
        @property
        def int(self):
            return 0

        @int.setter
        def int(self, value):
            constructed.append(value)

    _configure_uuid7(Probe, uuid.SafeUUID.unknown)
    with pytest.raises(ValueError):
        fastuuid7.uuid7_at_many(unix_ms=[42] * 1000 + [MAX_MS + 1])
    assert not constructed
    assert fastuuid7.uuid7_at_many(unix_ms=[]) == []
    assert not constructed


def test_late_construction_failure_frees_partial_results_and_propagates():
    references = []

    class Probe:
        @property
        def int(self):
            return 0

        @int.setter
        def int(self, value):
            del value
            references.append(weakref.ref(self))
            if len(references) == 3:
                raise MemoryError("simulated object construction failure")

    _configure_uuid7(Probe, uuid.SafeUUID.unknown)
    with pytest.raises(MemoryError, match="simulated"):
        fastuuid7.uuid7_at_many(unix_ms=[42] * 10)
    gc.collect()
    assert len(references) == 3
    assert all(reference() is None for reference in references)


def test_live_state_is_unchanged_by_valid_invalid_and_empty_batches():
    _set_state_for_tests(MAX_MS, 123)
    before = uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(MAX_MS))
    fastuuid7.uuid7_at_many(unix_ms=[0, 42, MAX_MS] * 1000)
    fastuuid7.uuid7_at_many(unix_ms=[])
    with pytest.raises(ValueError):
        fastuuid7.uuid7_at_many(unix_ms=[0, MAX_MS + 1])
    after = uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(0))
    assert after.int >> 80 == MAX_MS
    assert counter_of(after) == counter_of(before) + 1
    _set_state_for_tests(MAX_MS, (1 << 42) - 1)
    assert fastuuid7.uuid7_at_many(unix_ms=[0, MAX_MS])[1].time == MAX_MS
    with pytest.raises(OverflowError):
        fastuuid7.uuid7()


def test_repeated_calls_and_entropy_pool_refills_have_fresh_random_fields():
    first = fastuuid7.uuid7_at_many(unix_ms=[42] * 3000)
    second = fastuuid7.uuid7_at_many(unix_ms=[42] * 3000)
    values = first + second
    assert len(set(values)) == len(values)
    # Every one of the 74 random bit positions varies in this sample.
    varying = 0
    for value in values[1:]:
        varying |= value.int ^ values[0].int
    assert varying == (0xFFF << 64) | ((1 << 62) - 1)
    # A smoke check for an accidental live-counter implementation, not a randomness proof.
    assert any(a > b for a, b in zip(first, first[1:]))


def test_threaded_calls():
    with ThreadPoolExecutor(max_workers=4) as pool:
        batches = list(pool.map(lambda ms: fastuuid7.uuid7_at_many(unix_ms=[ms] * 300), range(8)))
    values = [value for batch in batches for value in batch]
    assert len(set(values)) == len(values)
    assert all(value.time == ms for ms, batch in enumerate(batches) for value in batch)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires POSIX fork")
def test_batch_discards_inherited_entropy_and_live_state_after_fork():
    fastuuid7.uuid7_at_many(unix_ms=[42])
    _set_state_for_tests(MAX_MS, (1 << 42) - 1)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            values = fastuuid7.uuid7_at_many(unix_ms=[42] * 8)
            live = fastuuid7.uuid7()
            assert live.time < MAX_MS
            os.write(write_fd, b"".join(v.bytes for v in values))
        except BaseException:
            os._exit(1)
        os._exit(0)
    os.close(write_fd)
    ready = []
    try:
        parent = fastuuid7.uuid7_at_many(unix_ms=[42] * 8)
        ready, _, _ = select.select([read_fd], [], [], 10)
        assert ready, "child did not return its batch"
        child = os.read(read_fd, 128)
    finally:
        os.close(read_fd)
        if not ready:
            os.kill(pid, 9)
        _, status = os.waitpid(pid, 0)
    assert status == 0 and len(child) == 128
    assert not {v.bytes for v in parent} & {child[i : i + 16] for i in range(0, 128, 16)}
    with pytest.raises(OverflowError):
        fastuuid7.uuid7()


def mapping(connection):
    return connection.execute("SELECT * FROM id_map ORDER BY entity, old_id").fetchall()


def test_migration_resume_after_process_exit_and_repeat(tmp_path):
    database = tmp_path / "resume.sqlite"
    subprocess.run(
        [sys.executable, str(EXAMPLE), str(database), "--max-batches", "1"],
        check=True,
        capture_output=True,
        timeout=20,
    )
    connection = migration.connect(database)
    before = mapping(connection)
    assert len(before) == 5
    assert migration.verify(connection) == {"mapped": 5, "remaining": 3}
    connection.close()
    for _ in range(2):
        subprocess.run(
            [sys.executable, str(EXAMPLE), str(database)],
            check=True,
            capture_output=True,
            timeout=20,
        )
    connection = migration.connect(database)
    try:
        assert set(before) <= set(mapping(connection))
        assert migration.verify(connection, require_complete=True) == {"mapped": 8, "remaining": 0}
        after = mapping(connection)
        assert migration.migrate_batch(connection) == 0
        assert mapping(connection) == after
    finally:
        connection.close()


def test_migration_mid_transaction_failure_rolls_back_only_current_chunk(tmp_path):
    database = tmp_path / "rollback.sqlite"
    connection = migration.connect(database)
    migration.initialize(connection)
    migration.migrate_batch(connection, batch_size=1)
    before = mapping(connection)
    connection.execute(
        """CREATE TRIGGER interrupt_update BEFORE UPDATE ON orders WHEN OLD.id = 13
        BEGIN SELECT RAISE(ABORT, 'simulated interruption'); END"""
    )
    with pytest.raises(sqlite3.IntegrityError, match="simulated interruption"):
        migration.migrate_batch(connection, batch_size=2)
    assert mapping(connection) == before
    assert connection.execute("SELECT uuid FROM customers WHERE id = 2").fetchone() == (None,)
    assert not connection.in_transaction
    connection.close()
    connection = migration.connect(database)
    try:
        connection.execute("DROP TRIGGER interrupt_update")
        while migration.migrate_batch(connection):
            pass
        assert set(before) <= set(mapping(connection))
        migration.verify(connection, require_complete=True)
    finally:
        connection.close()


def test_migration_invalid_late_timestamp_and_integrity_detection(tmp_path):
    connection = migration.connect(tmp_path / "invalid.sqlite")
    try:
        migration.initialize(connection)
        connection.execute("UPDATE orders SET created_ms = -1 WHERE id = 11")
        with pytest.raises(ValueError, match="unix_ms"):
            migration.migrate_batch(connection)
        assert not mapping(connection)
        assert migration.verify(connection) == {"mapped": 0, "remaining": 8}
        connection.execute("UPDATE orders SET created_ms = 42 WHERE id = 11")
        with pytest.raises(ValueError, match="incomplete"):
            migration.verify(connection, require_complete=True)
        while migration.migrate_batch(connection):
            pass
        # This wrong relation still satisfies both SQL foreign keys.
        connection.execute(
            "UPDATE orders SET customer_uuid = (SELECT uuid FROM customers WHERE id = 2) WHERE id = 10"
        )
        with pytest.raises(ValueError, match="relationships"):
            migration.verify(connection)
    finally:
        connection.close()


def test_process_crash_during_chunk_preserves_prior_commits(tmp_path):
    database = tmp_path / "crash.sqlite"
    connection = migration.connect(database)
    migration.initialize(connection)
    migration.migrate_batch(connection, batch_size=1)
    before = mapping(connection)
    connection.close()
    child_code = '''
import importlib.util
import os
import sys
spec = importlib.util.spec_from_file_location("migration", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c = m.connect(sys.argv[2])
c.create_function("crash", 0, lambda: os._exit(77))
c.execute("""CREATE TEMP TRIGGER crash_update BEFORE UPDATE ON orders WHEN OLD.id = 13
BEGIN SELECT crash(); END""")
m.migrate_batch(c, batch_size=2)
'''
    child = subprocess.run(
        [sys.executable, "-c", child_code, str(EXAMPLE), str(database)],
        capture_output=True,
        timeout=20,
    )
    assert child.returncode == 77, child.stderr.decode()
    connection = migration.connect(database)
    try:
        assert mapping(connection) == before
        assert migration.verify(connection) == {"mapped": 3, "remaining": 5}
        while migration.migrate_batch(connection):
            pass
        assert set(before) <= set(mapping(connection))
        migration.verify(connection, require_complete=True)
    finally:
        connection.close()


def test_migration_reuses_previously_persisted_assignment(tmp_path):
    connection = migration.connect(tmp_path / "assigned.sqlite")
    try:
        migration.initialize(connection)
        assigned = str(fastuuid7.uuid7_at(unix_ms=1_645_557_742_123))
        connection.execute("INSERT INTO id_map VALUES ('customer', 1, ?)", (assigned,))
        migration.migrate_batch(connection, batch_size=1)
        assert connection.execute("SELECT uuid FROM customers WHERE id = 1").fetchone() == (
            assigned,
        )
        assert ("customer", 1, assigned) in mapping(connection)
        migration.verify(connection)
    finally:
        connection.close()
