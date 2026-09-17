# Resumable historical migration

This self-contained SQLite demonstration uses only the standard library and
`fastuuid7`. It retains legacy integer keys, adds UUID columns, and stores a
permanent `(entity, old_id) -> new_id` mapping for customers and orders.

```bash
uv sync --extra dev --locked
# Use a new path for a fresh demo. Reusing it intentionally resumes the same job.
uv run --extra dev --locked python examples/historical_migration/migrate.py /tmp/history.sqlite --max-batches 1
# {"batches_committed": 1, "mapped": 5, "remaining": 3}
uv run --extra dev --locked python examples/historical_migration/migrate.py /tmp/history.sqlite
# {"batches_committed": 1, "mapped": 8, "remaining": 0}
uv run --extra dev --locked python examples/historical_migration/migrate.py /tmp/history.sqlite
# {"batches_committed": 0, "mapped": 8, "remaining": 0}
```

Each `BEGIN IMMEDIATE` transaction handles a bounded number of customers plus
all their orders. It loads existing assignments, generates only missing UUIDs
with `uuid7_at_many`, persists mappings, and updates customer UUIDs, order UUIDs
and order-to-customer UUID foreign keys. A commit makes the whole chunk durable.
An error or process exit before commit rolls back that chunk. UUIDs generated in
an uncommitted transaction are discarded and must not be exposed externally;
already **committed** IDs never change on resume. Random UUID generation itself
cannot recover earlier assignments without the mapping table.

The example uses integer `created_ms` values, including zero, repeated
milliseconds and the 48-bit maximum. It never derives ordering within one
millisecond from the UUID random fields. `verify` checks SQLite integrity and
foreign keys, agrees old and new relationships, matches every mapping to its
row, and verifies each migrated UUID's timestamp and layout. Completion can also
be required explicitly through `verify(connection, require_complete=True)`.
Tests cover process restart, repeat runs, invalid timestamps, and an injected SQL
failure after some row updates but before commit.

This is a teaching example with source writes paused and one migration writer.
It scans the whole database for verification after each chunk, and a customer
with many orders can still use substantial memory. Production migrations should
bound their workload and use appropriately scoped checks, indexes and a final
integrity pass. Keep the mapping table and backups through cutover. Changing
primary keys, deleting legacy columns and coordinating active writers are
separate operations. See the [PostgreSQL transfer notes](../../docs/integrations.md#resumable-migration-of-related-historical-records).

## Reproduce measurements

```bash
uv run --extra dev --locked python examples/historical_migration/benchmark.py --count 10000 --rounds 9
```

The script records interpreter, OS/architecture, package version, count, rounds,
per-round nanoseconds per UUID and medians. Record the exact Git SHA and CPU model
alongside its JSON output (`git rev-parse HEAD`; on macOS,
`sysctl -n machdep.cpu.brand_string`). Both paths receive the same prebuilt tuple
and produce `list[uuid.UUID]`; timestamp preparation and result disposal are
outside timing, allocations and validation are inside. Each path is warmed once,
measurement order alternates, and garbage collection remains enabled with a
collection before each sample. This compares a scalar loop with the new batch
API in that environment; it is not a database or end-to-end migration benchmark,
and does not establish a general speedup.
