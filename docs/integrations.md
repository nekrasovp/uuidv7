# Integration recipes

The distribution is installed as `fastuuid7`. Both `fastuuid7` and the original
`uuidv7` import path expose the same API.

## Python 3.14 migration

Use the standard library when its performance and output shapes are sufficient.
The fallback below lets a project use the same call site on Python 3.9-3.14:

```python
try:
    from uuid import uuid7
except ImportError:
    from fastuuid7 import uuid7
```

Install `fastuuid7` only for environments older than Python 3.14, or import it
unconditionally when its string, bytes, native-object, or batch fast paths are
required.

## SQLAlchemy 2

### Backfilling historical records

Use an explicit timestamp when migrating existing rows. Require a timezone-aware
`datetime` and use integer arithmetic to avoid floating-point timestamp rounding:

```python
from datetime import datetime, timezone

from fastuuid7 import uuid7_at

created_at = datetime(2022, 2, 22, 19, 22, 22, 123000, tzinfo=timezone.utc)
delta = created_at - datetime(1970, 1, 1, tzinfo=timezone.utc)
unix_ms = (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
new_id = uuid7_at(unix_ms=unix_ms)
```

Persist the generated value as part of the migration. Running the same call
again generates a different identifier. Rows within one millisecond have no
guaranteed relative order; retain a separate sequence column if that matters.

### New records

```python
import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fastuuid7 import uuid7


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid7
    )
    payload: Mapped[str] = mapped_column(String(200))
```

`default=uuid7` passes the callable to SQLAlchemy so a new identifier is
created for each row.

## Django

```python
from django.db import models

from fastuuid7 import uuid7


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    payload = models.JSONField()
```

## Pydantic and FastAPI

```python
import uuid

from pydantic import BaseModel, Field

from fastuuid7 import uuid7


class Event(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid7)
    payload: dict[str, object]
```

## PostgreSQL

Use the native `uuid` column type and pass the returned `uuid.UUID` directly
through a compatible driver:

```sql
CREATE TABLE event (
    id uuid PRIMARY KEY,
    payload jsonb NOT NULL
);
```

Application-side generation lets an ID exist before an insert and works across
PostgreSQL versions. PostgreSQL 18 can instead generate UUIDv7 values on the
server with `uuidv7()` when application-side IDs are unnecessary.

## Resumable migration of related historical records

The runnable [SQLite example](../examples/historical_migration/README.md) uses
`uuid7_at_many(unix_ms=...)` to backfill customers and their orders. It persists
`(entity, old_id) -> new_id` in a mapping table. Each transaction inserts mappings,
updates customer and order UUID columns, and updates order-to-customer UUID
references together. Committed mappings survive process exit; resume selects
unmigrated customers and reuses any persisted assignments. UUID generation alone
is not idempotent.

From a source checkout:

```bash
uv sync --extra dev --locked
uv run --extra dev --locked python examples/historical_migration/migrate.py /tmp/history.sqlite --max-batches 1
uv run --extra dev --locked python examples/historical_migration/migrate.py /tmp/history.sqlite
```

The first invocation stops after a committed chunk; the second completes the
migration. Further runs leave assigned UUIDs unchanged. The example checks SQL
foreign keys, old/new relationship agreement, mapping correspondence, UUID
version/variant, and exact historical timestamps. Tests also interrupt a chunk
between related updates to prove rollback and resume. Source writes are paused
for this demonstration; the legacy keys remain available throughout.

For PostgreSQL, preserve the same transaction boundaries and persistent unique
mapping keys, use native `uuid` columns, and pass `uuid.UUID` values through the
driver. Select and lock the parent rows for each chunk in a transaction; concurrent
workers need an explicit ownership/locking policy, with each parent's dependent
rows handled by the same transaction. Unique constraints on both old mapping
keys and new UUIDs must remain in place. On conflict, load the winning committed
mapping rather than generating a replacement. Coordinate or pause source writers
so that newly inserted children cannot miss the backfill. Validate the complete
mapping and foreign keys before a separately planned switch of primary keys.
The SQLite example demonstrates this data flow; it does not execute or benchmark
a PostgreSQL migration.

PostgreSQL reference: [row-level locking](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)
and the [native UUID type](https://www.postgresql.org/docs/current/datatype-uuid.html).
