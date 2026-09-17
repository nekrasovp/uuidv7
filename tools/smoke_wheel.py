"""Exercise the installed distribution outside its source checkout."""

import importlib.resources
import pickle
import uuid

import fastuuid7
import uuidv7

assert fastuuid7.uuid7 is uuidv7.uuid7
assert fastuuid7.uuid7_at is uuidv7.uuid7_at
for package in (fastuuid7, uuidv7):
    assert importlib.resources.files(package).joinpath("py.typed").is_file()
    value = package.uuid7_at(unix_ms=1_645_557_742_123)
    assert isinstance(value, uuid.UUID) and value.time == 1_645_557_742_123
    assert pickle.loads(pickle.dumps(value)) == value
    for method in (package.uuid7_many, package.uuid7_obj_many, package.uuid7_str_many):
        values = [uuid.UUID(str(v)) for v in method(100)]
        assert all(v.version == 7 and v.variant == uuid.RFC_4122 for v in values)
        assert all(a < b for a, b in zip(values, values[1:]))
    raw = package.uuid7_bytes_many(100)
    values = [uuid.UUID(bytes=raw[i : i + 16]) for i in range(0, len(raw), 16)]
    assert len(values) == 100 and all(a < b for a, b in zip(values, values[1:]))
print(f"Installed fastuuid7 {fastuuid7.__version__}: both imports, history and batches OK")
