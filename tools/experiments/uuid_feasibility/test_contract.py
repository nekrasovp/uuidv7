import concurrent.futures
import json
import uuid

import _uuid_lab as lab
import pytest
from common import INVALID, RAW, TEXTS, UUIDS
from hypothesis import given, settings
from hypothesis import strategies as st
from integration import BulkModel, FastUUID, NativeModel, ScalarModel, StandardModel
from pydantic import TypeAdapter, ValidationError


@given(st.integers(min_value=0, max_value=(1 << 128) - 1))
@settings(max_examples=1000, deadline=None)
def test_round_trip_all_bits(value):
    u = uuid.UUID(int=value)
    for text in (str(u), str(u).upper(), u.hex, u.urn, "{" + str(u) + "}"):
        assert type(lab.parse(text)) is uuid.UUID
        assert lab.parse(text) == u
        n = lab.parse_native(text)
        assert n == u and u == n and hash(n) == hash(u)
        assert n.int == value and n.version == u.version
        assert str(n) == str(u) and n.hex == u.hex and n.bytes == u.bytes
        assert lab.parse_bytes(text) == u.bytes
    assert lab.from_bytes(u.bytes) == u


@given(st.binary(max_size=100))
@settings(max_examples=1000, deadline=None)
def test_arbitrary_text(data):
    text = data.decode("latin1")
    try:
        result = lab.parse(text)
    except ValueError:
        return
    assert result == uuid.UUID(text)


@pytest.mark.parametrize("value", INVALID + ["\ud800"])
def test_bad_input(value):
    with pytest.raises((ValueError, UnicodeError)):
        lab.parse(value)
    for fn in (
        lab.parse_many,
        lab.parse_many_native,
        lab.parse_many_bytes,
        lab.parse_many_bytes_detach,
    ):
        with pytest.raises((ValueError, UnicodeError)):
            fn([TEXTS[0], value, TEXTS[1]])


def test_batch_order_ownership_errors():
    for values in ([], TEXTS[:1], TEXTS, (x for x in TEXTS)):
        expected = list(values)
        assert lab.parse_many(expected) == [uuid.UUID(x) for x in expected]
        assert lab.parse_many_bytes(expected) == b"".join(uuid.UUID(x).bytes for x in expected)
        assert lab.parse_many_bytes_detach(expected) == lab.parse_many_bytes(expected)
    for fn in (lab.parse_many, lab.parse_many_bytes_detach):
        with pytest.raises(ValueError, match="index 1"):
            fn([TEXTS[0], "bad"])
        with pytest.raises(TypeError):
            fn(1)
    with pytest.raises(AttributeError):
        lab.parse_native(TEXTS[0]).int = 0
    with pytest.raises(ValueError):
        lab.from_bytes(b"short")
    with pytest.raises(TypeError):
        lab.parse(12)


def test_threads_detached_no_shared_state():
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        results = list(pool.map(lab.parse_many_bytes_detach, [TEXTS] * 32))
    assert all(x == b"".join(RAW) for x in results)


@pytest.mark.parametrize("model", [ScalarModel, BulkModel])
def test_pydantic_equivalent_valid_invalid_strict(model):
    for data in (TEXTS[:4], UUIDS[:4], RAW[:4]):
        payload = {"ids": data}
        assert (
            model.model_validate(payload).model_dump()
            == StandardModel.model_validate(payload).model_dump()
        )
    for value in INVALID + [12, None, b"short", True]:
        errors = []
        for cls in (StandardModel, model):
            with pytest.raises(ValidationError) as e:
                cls(ids=[TEXTS[0], value])
            errors.append(e.value.errors(include_url=False))
        assert errors[0] == errors[1]
    for strict in (True, False):
        payload = {"ids": TEXTS[:4], "label": "sample"}
        obj = model.model_validate_json(json.dumps(payload), strict=strict)
        assert json.loads(obj.model_dump_json()) == payload
        if strict:
            with pytest.raises(ValidationError):
                model.model_validate(payload, strict=True)
            assert model.model_validate({"ids": UUIDS[:4]}, strict=True).ids == UUIDS[:4]
    assert model.model_json_schema()["properties"]["ids"]["items"]["format"] == "uuid"


def test_native_model_scope_and_uuid4():
    data = {"ids": TEXTS[:4], "label": "sample"}
    assert json.loads(NativeModel.model_validate(data).model_dump_json()) == data
    values = [fn() for fn in (lab.uuid4, lab.uuid4_direct) for _ in range(1000)]
    assert len(set(values)) == len(values)
    assert all(
        type(x) is uuid.UUID and x.version == 4 and x.variant == uuid.RFC_4122 for x in values
    )
    # This sample is conformance, not proof of entropy quality or collision odds.


def test_scalar_adapter_strict():
    adapter = TypeAdapter(FastUUID)
    assert adapter.validate_python(UUIDS[0], strict=True) is UUIDS[0]
    with pytest.raises(ValidationError):
        adapter.validate_python(TEXTS[0], strict=True)


def test_real_asgi_contract():
    import app
    from fastapi.testclient import TestClient

    with TestClient(app.app) as client:
        assert client.get("/item/" + TEXTS[0]).json() == {"id": TEXTS[0]}
        assert client.get("/item/not-a-uuid").status_code == 422
        assert client.post("/batch", json={"ids": TEXTS[:4]}).json() == {
            "ids": TEXTS[:4],
            "label": "sample",
        }


def test_consumer_representation():
    from consumers import CONSUMERS

    for fn in CONSUMERS.values():
        result = fn(TEXTS)
        assert all(type(u) is uuid.UUID for u in result)
        assert result == UUIDS
