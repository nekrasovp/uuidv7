"""Check benchmark equivalence before measuring installed comparison wheels."""

import json
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import create_app  # noqa: E402
from common import TEXTS, VARIANTS  # noqa: E402
from contracts import configuration  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import TypeAdapter, ValidationError  # noqa: E402
from run import RATES, request_data, validate_response  # noqa: E402


@pytest.mark.parametrize("variant", VARIANTS)
def test_models_preserve_values_schema_and_json(variant):
    model, single, scalar_type, _ = configuration(variant)
    payload = {"ids": TEXTS, "label": "sample"}
    value = model.model_validate_json(json.dumps(payload))
    assert len(value.ids) == 1000
    assert [v.int for v in value.ids] == [uuid.UUID(s).int for s in TEXTS]
    assert json.loads(value.model_dump_json()) == payload
    assert single.model_json_schema()["properties"]["id"]["format"] == "uuid"
    if variant != "uuid-utils-native":
        assert all(type(v) is uuid.UUID for v in value.ids)
        assert (
            TypeAdapter(scalar_type).validate_python(uuid.UUID(TEXTS[0]), strict=True)
            == value.ids[0]
        )
        with pytest.raises(ValidationError):
            TypeAdapter(scalar_type).validate_python(TEXTS[0], strict=True)
        with pytest.raises(ValidationError):
            model.model_validate(payload, strict=True)
        assert model.model_validate_json(json.dumps(payload), strict=True) == value
    else:
        assert all(not isinstance(v, uuid.UUID) for v in value.ids)
        assert TypeAdapter(scalar_type).validate_python(value.ids[0], strict=True) is value.ids[0]
    for invalid in ("bad", "", None, 123, "\ud800"):
        with pytest.raises(ValidationError) as error:
            model(ids=[TEXTS[0], invalid])
        assert error.value.errors()[0]["loc"] == ("ids", 1)


@pytest.mark.parametrize("variant", VARIANTS)
def test_all_http_scenarios_and_error_paths(variant):
    with TestClient(create_app(variant)) as client:
        for scenario in RATES:
            for index in (0, 9):
                method, url, content, headers = request_data(scenario, index)
                response = client.request(method, url, content=content, headers=headers)
                validate_response(scenario, index, response)
        assert client.get("/item/not-a-uuid").status_code == 422
        invalid_json = client.post(
            "/batch", content=b'{"ids":', headers={"content-type": "application/json"}
        )
        assert invalid_json.status_code == 422
        bad = client.post("/batch", json={"ids": [TEXTS[0], None]})
        assert bad.status_code == 422 and bad.json()["detail"][0]["loc"] == ["body", "ids", 1]
        assert client.get("/generate/5").status_code == 404


def test_response_validation_rejects_mismatches():
    import httpx

    for scenario, body in (
        ("path", {"id": TEXTS[1]}),
        ("body-1", {"ids": [], "label": "sample"}),
        ("invalid", {"detail": [{"loc": ["body", "ids", 0]}]}),
        ("generate-v7", {"ids": [TEXTS[0]] * 64, "label": "sample"}),
    ):
        with pytest.raises(AssertionError):
            validate_response(
                scenario, 0, httpx.Response(422 if scenario == "invalid" else 200, json=body)
            )
