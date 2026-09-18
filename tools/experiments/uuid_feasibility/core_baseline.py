"""Supplement: separate public TypeAdapter overhead from pydantic-core itself."""

import json
import uuid

import _uuid_lab as lab
import pyperf
from common import TEXTS, UUIDS, identity
from pydantic import TypeAdapter
from pydantic_core import SchemaValidator, core_schema


def repeated(fn, values):
    for value in values:
        fn(value)


def main():
    runner = pyperf.Runner()
    runner.metadata["study_identity"] = json.dumps(identity(), sort_keys=True)
    one = TypeAdapter(uuid.UUID)
    core = SchemaValidator(core_schema.uuid_schema())
    many = TypeAdapter(list[uuid.UUID])
    core_many = SchemaValidator(core_schema.list_schema(core_schema.uuid_schema()))
    for name, fn in {
        "stdlib": uuid.UUID,
        "type_adapter": one.validate_python,
        "core_schema": core.validate_python,
        "c_stdlib": lab.parse,
    }.items():
        assert all(type(fn(t)) is uuid.UUID and fn(t) == u for t, u in zip(TEXTS[:32], UUIDS[:32]))
        runner.bench_func("scalar/" + name, repeated, fn, TEXTS[:32], inner_loops=32)
    for n in (1, 1000):
        for name, fn in {
            "type_adapter": many.validate_python,
            "core_schema": core_many.validate_python,
            "c_stdlib": lab.parse_many,
        }.items():
            assert fn(TEXTS[:n]) == UUIDS[:n]
            runner.bench_func(f"batch/{n}/{name}", fn, TEXTS[:n])


if __name__ == "__main__":
    main()
