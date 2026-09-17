"""Exercise the installed distribution outside its source checkout."""

import importlib.resources
import pickle
import uuid

import fastuuid7
import uuidv7

assert fastuuid7.uuid7 is uuidv7.uuid7
assert fastuuid7.uuid7_at is uuidv7.uuid7_at
assert fastuuid7.uuid7_at_many is uuidv7.uuid7_at_many
for package in (fastuuid7, uuidv7):
    assert importlib.resources.files(package).joinpath("py.typed").is_file()
    value = package.uuid7_at(unix_ms=1_645_557_742_123)
    assert isinstance(value, uuid.UUID) and value.time == 1_645_557_742_123
    assert pickle.loads(pickle.dumps(value)) == value
    timestamps = [0, 42, (1 << 48) - 1, 42]
    historical = package.uuid7_at_many(unix_ms=iter(timestamps))
    assert [v.time for v in historical] == timestamps
    assert all(isinstance(v, uuid.UUID) and v.version == 7 for v in historical)
    assert all(v.variant == uuid.RFC_4122 for v in historical)
    assert pickle.loads(pickle.dumps(historical)) == historical
    assert package.uuid7_at_many(unix_ms=[]) == []
    for invalid, error in [(True, TypeError), (-1, ValueError), (1 << 48, ValueError)]:
        try:
            package.uuid7_at_many(unix_ms=[42, invalid])
        except error:
            pass
        else:
            raise AssertionError("historical batch accepted an invalid timestamp")
    for method in (package.uuid7_many, package.uuid7_obj_many, package.uuid7_str_many):
        values = [uuid.UUID(str(v)) for v in method(100)]
        assert all(v.version == 7 and v.variant == uuid.RFC_4122 for v in values)
        assert all(a < b for a, b in zip(values, values[1:]))
    raw = package.uuid7_bytes_many(100)
    values = [uuid.UUID(bytes=raw[i : i + 16]) for i in range(0, len(raw), 16)]
    assert len(values) == 100 and all(a < b for a, b in zip(values, values[1:]))
print(f"Installed fastuuid7 {fastuuid7.__version__}: both imports, history and batches OK")
