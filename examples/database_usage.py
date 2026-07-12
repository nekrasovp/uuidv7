"""SQLAlchemy 2 example using UUIDv7 primary keys.

Run with:
    uv run --with sqlalchemy python -m examples.database_usage
"""

from __future__ import annotations

import uuid

from sqlalchemy import String, Uuid, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fastuuid7 import uuid7


class Base(DeclarativeBase):
    """Base for the example's ORM models."""


class Event(Base):
    """Event stored with an application-generated UUIDv7 primary key."""

    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid7)
    payload: Mapped[str] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"Event(id={self.id}, payload={self.payload!r})"


def main() -> None:
    """Insert and retrieve UUIDv7-keyed rows from an in-memory database."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(Event(payload=f"event-{index}") for index in range(3))
        session.commit()

        events = session.scalars(select(Event).order_by(Event.id)).all()

    for event in events:
        print(event)

    assert all(isinstance(event.id, uuid.UUID) for event in events)
    assert [event.id for event in events] == sorted(event.id for event in events)


if __name__ == "__main__":
    main()
