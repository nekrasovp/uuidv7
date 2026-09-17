"""Native PostgreSQL UUID primary keys with text and binary result decoding."""

import uuid

import psycopg
import pytest
from psycopg.types.json import Jsonb

from fastuuid7 import uuid7, uuid7_at


@pytest.mark.parametrize("binary", [False, True])
def test_uuid_primary_key_round_trip_order_and_constraints(postgres_dsn, binary):
    values = [uuid7(), uuid7_at(unix_ms=0), uuid7_at(unix_ms=(1 << 48) - 1)]
    expected = {value: {"index": index} for index, value in enumerate(values)}
    # Each parametrized case owns a different table within the module's schema.
    table = psycopg.sql.Identifier(f"fastuuid7_test_psycopg_{int(binary)}")
    with psycopg.connect(postgres_dsn) as connection:
        connection.execute(
            psycopg.sql.SQL("CREATE TABLE {} (id uuid PRIMARY KEY, payload jsonb NOT NULL)").format(
                table
            )
        )
        with connection.cursor(binary=binary) as cursor:
            for value, payload in expected.items():
                cursor.execute(
                    psycopg.sql.SQL("INSERT INTO {} VALUES (%s, %s) RETURNING id").format(table),
                    (value, Jsonb(payload)),
                )
                assert cursor.fetchone()[0] == uuid.UUID(bytes=value.bytes)
    # Reopen after commit so this verifies persisted values rather than input objects.
    with psycopg.connect(postgres_dsn) as connection, connection.cursor(binary=binary) as cursor:
        cursor.execute(psycopg.sql.SQL("SELECT id, payload FROM {} ORDER BY id").format(table))
        rows = cursor.fetchall()
        assert [row[0] for row in rows] == sorted(expected)
        assert dict(rows) == expected
        assert all(isinstance(row[0], uuid.UUID) and row[0].version == 7 for row in rows)
        cursor.execute(
            psycopg.sql.SQL("SELECT payload FROM {} WHERE id = %s").format(table), (values[0],)
        )
        assert cursor.fetchone()[0] == expected[values[0]]
        with pytest.raises(psycopg.errors.UniqueViolation), connection.transaction():
            cursor.execute(
                psycopg.sql.SQL("INSERT INTO {} VALUES (%s, %s)").format(table),
                (values[0], Jsonb({"duplicate": True})),
            )
        with pytest.raises(psycopg.errors.InvalidTextRepresentation), connection.transaction():
            cursor.execute("SELECT %s::uuid", ("not-a-uuid",))
