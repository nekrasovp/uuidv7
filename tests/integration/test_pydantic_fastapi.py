"""UUID defaults and JSON validation through real Pydantic and ASGI requests."""

import json
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from fastuuid7 import uuid7, uuid7_at


class Event(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid7)
    payload: dict[str, object]


def test_pydantic_default_factory_validation_and_serialization():
    first, second = Event(payload={}), Event(payload={})
    assert first.id != second.id
    assert isinstance(first.id, uuid.UUID) and first.id.version == 7
    for value in (first.id, uuid7_at(unix_ms=0), uuid7_at(unix_ms=(1 << 48) - 1)):
        for input_value in (value, str(value), value.bytes):
            event = Event(id=input_value, payload={"test": True})
            assert event.id == uuid.UUID(int=value.int)
            assert event.model_dump(mode="python")["id"] == value
            assert event.model_dump(mode="json")["id"] == str(value)
            assert json.loads(event.model_dump_json())["id"] == str(value)
            assert Event.model_validate_json(event.model_dump_json()) == event
        assert TypeAdapter(uuid.UUID).validate_python(value, strict=True) == value
    for invalid in ("not-a-uuid", b"short", 123, None):
        with pytest.raises(ValidationError):
            Event(id=invalid, payload={})
    assert Event.model_json_schema()["properties"]["id"]["format"] == "uuid"


def test_fastapi_request_response_and_path_uuid_round_trip():
    app = FastAPI()

    @app.post("/fastuuid7-test/events", response_model=Event)
    def create_event(event: Event):
        return event

    @app.get("/fastuuid7-test/events/{event_id}", response_model=Event)
    def get_event(event_id: uuid.UUID):
        return Event(id=event_id, payload={"found": True})

    with TestClient(app) as client:
        first = client.post("/fastuuid7-test/events", json={"payload": {"index": 1}})
        second = client.post("/fastuuid7-test/events", json={"payload": {"index": 2}})
        assert first.status_code == second.status_code == 200
        first_id, second_id = first.json()["id"], second.json()["id"]
        assert first_id != second_id
        assert uuid.UUID(first_id).version == uuid.UUID(second_id).version == 7
        explicit = uuid7_at(unix_ms=42)
        response = client.post(
            "/fastuuid7-test/events", json={"id": str(explicit), "payload": {"explicit": True}}
        )
        assert response.status_code == 200
        assert response.json() == {"id": str(explicit), "payload": {"explicit": True}}
        fetched = client.get(f"/fastuuid7-test/events/{first_id}")
        assert fetched.status_code == 200 and fetched.json()["id"] == first_id
        assert client.get("/fastuuid7-test/events/not-a-uuid").status_code == 422
        assert (
            client.post(
                "/fastuuid7-test/events", json={"id": "not-a-uuid", "payload": {}}
            ).status_code
            == 422
        )
