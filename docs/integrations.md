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
