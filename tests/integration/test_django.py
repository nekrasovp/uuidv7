"""Run UUIDField defaults, database adaptation and Django serialization."""

import json
import uuid

import django
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from psycopg.conninfo import conninfo_to_dict

from fastuuid7 import uuid7, uuid7_at


@pytest.fixture(scope="module")
def event_model(postgres_dsn):
    from django.db import connection, models

    params = conninfo_to_dict(postgres_dsn)
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": params["dbname"],
                "USER": params.get("user", ""),
                "PASSWORD": params.get("password", ""),
                "HOST": params.get("host", ""),
                "PORT": params.get("port", ""),
                "OPTIONS": {"options": params["options"], "connect_timeout": 5},
            }
        },
        SECRET_KEY="fastuuid7-test-only",
        USE_TZ=True,
    )
    django.setup()

    class Event(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
        payload = models.JSONField()

        class Meta:
            app_label = "fastuuid7_test"
            db_table = "fastuuid7_test_django_event"

    with connection.schema_editor() as editor:
        editor.create_model(Event)
    try:
        yield Event
    finally:
        connection.close()


def test_uuid_primary_key_default_validation_and_read_after_write(event_model):
    from django.core import serializers
    from django.db import IntegrityError, connection, transaction

    events = [event_model(payload={"index": index}) for index in range(2)]
    historical = uuid7_at(unix_ms=1_645_557_742_123)
    events.append(event_model(id=historical, payload={"historical": True}))
    expected = {event.id: event.payload for event in events}
    assert len(expected) == 3
    for event in events:
        assert isinstance(event.id, uuid.UUID) and event.id.version == 7
        event.full_clean()
        event.save(force_insert=True)
    connection.close()
    loaded = list(event_model.objects.order_by("id"))
    assert [event.id for event in loaded] == sorted(expected)
    assert {event.id: event.payload for event in loaded} == expected
    for value in expected:
        assert event_model.objects.get(pk=str(value)).payload == expected[value]
    encoded = json.loads(serializers.serialize("json", loaded))
    assert [row["pk"] for row in encoded] == [str(value) for value in sorted(expected)]
    field = event_model._meta.get_field("id")
    with pytest.raises(ValidationError):
        field.clean("not-a-uuid", None)
    with pytest.raises(IntegrityError), transaction.atomic():
        event_model(id=historical, payload={"duplicate": True}).save(force_insert=True)
