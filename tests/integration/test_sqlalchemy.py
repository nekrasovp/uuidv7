"""Exercise the documented SQLAlchemy callable default on both UUID backends."""

import uuid

import psycopg
import pytest
from sqlalchemy import String, Uuid, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from fastuuid7 import uuid7, uuid7_at


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "fastuuid7_test_sa_event"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid7)
    payload: Mapped[str] = mapped_column(String(200))


@pytest.fixture(params=["sqlite", "postgresql"])
def engine(request):
    if request.param == "sqlite":
        engine = create_engine("sqlite://")
    else:
        dsn = request.getfixturevalue("postgres_dsn")
        engine = create_engine("postgresql+psycopg://", creator=lambda: psycopg.connect(dsn))
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_default_primary_keys_survive_commit_and_new_session(engine):
    historical = uuid7_at(unix_ms=1_645_557_742_123)
    with Session(engine) as session:
        events = [
            Event(payload="first"),
            Event(payload="second"),
            Event(id=historical, payload="old"),
        ]
        session.add_all(events)
        session.flush()
        expected = {event.id: event.payload for event in events}
        assert len(expected) == 3
        assert all(isinstance(value, uuid.UUID) and value.version == 7 for value in expected)
        session.commit()
    # A new session prevents the identity map from disguising failed adaptation.
    with Session(engine) as session:
        loaded = session.scalars(select(Event).order_by(Event.id)).all()
        assert [event.id for event in loaded] == sorted(expected)
        assert {event.id: event.payload for event in loaded} == expected
        for value in expected:
            assert session.get(Event, uuid.UUID(str(value))).payload == expected[value]
    with Session(engine) as session, pytest.raises(IntegrityError):
        session.add(Event(id=historical, payload="duplicate"))
        session.commit()
