"""Resumable SQLite backfill: durable UUID mappings and related rows per transaction."""

from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from pathlib import Path

from fastuuid7 import uuid7_at_many

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    created_ms INTEGER NOT NULL,
    uuid TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    created_ms INTEGER NOT NULL,
    uuid TEXT UNIQUE,
    customer_uuid TEXT REFERENCES customers(uuid)
);
CREATE TABLE IF NOT EXISTS id_map (
    entity TEXT NOT NULL CHECK (entity IN ('customer', 'order')),
    old_id INTEGER NOT NULL,
    new_id TEXT NOT NULL UNIQUE,
    PRIMARY KEY (entity, old_id)
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    """Create the demo schema, preserving existing data on every subsequent run."""
    connection.executescript(SCHEMA)
    connection.execute("BEGIN IMMEDIATE")
    try:
        if not connection.execute("SELECT 1 FROM customers LIMIT 1").fetchone():
            # Deliberately unsorted timestamps, including a same-millisecond pair.
            connection.executemany(
                "INSERT INTO customers(id, created_ms) VALUES (?, ?)",
                [(1, 1_645_557_742_123), (2, 0), (3, 1_645_557_742_123), (4, (1 << 48) - 1)],
            )
            connection.executemany(
                "INSERT INTO orders(id, customer_id, created_ms) VALUES (?, ?, ?)",
                [(10, 1, 1_645_557_742_124), (11, 1, 1_645_557_742_124), (12, 2, 1), (13, 3, 42)],
            )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def migrate_batch(connection: sqlite3.Connection, *, batch_size: int = 2) -> int:
    """Commit at most batch_size customers, their orders, and all UUID mappings.

    Resume by selecting unmigrated customers; always reuse persisted mappings.
    The demo assumes source writes are paused during the backfill.
    """
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if connection.in_transaction:
        raise ValueError("migrate_batch requires a connection without an active transaction")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise ValueError("foreign_keys must be enabled")
    connection.execute("BEGIN IMMEDIATE")
    try:
        customers = connection.execute(
            "SELECT id, created_ms FROM customers WHERE uuid IS NULL ORDER BY id LIMIT ?",
            (batch_size,),
        ).fetchall()
        if not customers:
            connection.commit()
            return 0
        # One query per parent avoids SQLite's bound-parameter limit for large chunks.
        orders = [
            row
            for customer_id, _ in customers
            for row in connection.execute(
                "SELECT id, created_ms, customer_id FROM orders WHERE customer_id = ? ORDER BY id",
                (customer_id,),
            )
        ]
        records = [("customer", old_id, ms) for old_id, ms in customers]
        records.extend(("order", old_id, ms) for old_id, ms, _ in orders)
        mappings = {}
        missing = []
        for entity, old_id, ms in records:
            row = connection.execute(
                "SELECT new_id FROM id_map WHERE entity = ? AND old_id = ?", (entity, old_id)
            ).fetchone()
            if row is None:
                missing.append((entity, old_id, ms))
            else:
                value = uuid.UUID(row[0])
                if value.version != 7 or value.int >> 80 != ms:
                    raise ValueError("persisted mapping has an incompatible timestamp or version")
                mappings[entity, old_id] = row[0]
        generated = uuid7_at_many(unix_ms=(ms for _, _, ms in missing))
        for (entity, old_id, _), value in zip(missing, generated):
            text = str(value)
            connection.execute("INSERT INTO id_map VALUES (?, ?, ?)", (entity, old_id, text))
            mappings[entity, old_id] = text
        for old_id, _ in customers:
            connection.execute(
                "UPDATE customers SET uuid = ? WHERE id = ?", (mappings["customer", old_id], old_id)
            )
        for old_id, _, customer_id in orders:
            connection.execute(
                "UPDATE orders SET uuid = ?, customer_uuid = ? WHERE id = ?",
                (mappings["order", old_id], mappings["customer", customer_id], old_id),
            )
        verify(connection)
        connection.commit()
        return len(customers)
    except BaseException:
        connection.rollback()
        raise


def verify(connection: sqlite3.Connection, *, require_complete: bool = False) -> dict[str, int]:
    """Check FKs, old/new relationship agreement, mapping correspondence and UUID time."""
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite integrity check failed")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("foreign key check failed")
    if connection.execute(
        """SELECT 1 FROM orders o JOIN customers c ON c.id = o.customer_id
        WHERE o.customer_uuid IS NOT c.uuid OR (o.uuid IS NULL) != (c.uuid IS NULL)
        LIMIT 1"""
    ).fetchone():
        raise ValueError("old and new relationships disagree")
    expected = {}
    remaining = 0
    for entity, table in [("customer", "customers"), ("order", "orders")]:
        for old_id, ms, text in connection.execute(f"SELECT id, created_ms, uuid FROM {table}"):
            if text is None:
                remaining += 1
                continue
            value = uuid.UUID(text)
            if value.version != 7 or value.variant != uuid.RFC_4122 or value.int >> 80 != ms:
                raise ValueError("UUID layout or historical timestamp mismatch")
            expected[entity, old_id] = text
    actual = {
        (entity, old_id): text
        for entity, old_id, text in connection.execute("SELECT * FROM id_map")
    }
    if actual != expected:
        raise ValueError("persisted mapping does not match migrated rows")
    if require_complete and remaining:
        raise ValueError("migration is incomplete")
    return {"mapped": len(actual), "remaining": remaining}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-batches", type=int, help="Stop after this many committed batches")
    args = parser.parse_args()
    if args.max_batches is not None and args.max_batches < 1:
        parser.error("--max-batches must be positive")
    connection = connect(args.database)
    try:
        initialize(connection)
        batches = 0
        while args.max_batches is None or batches < args.max_batches:
            if not migrate_batch(connection, batch_size=args.batch_size):
                break
            batches += 1
        status = verify(connection)
        status["batches_committed"] = batches
        print(json.dumps(status, sort_keys=True))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
