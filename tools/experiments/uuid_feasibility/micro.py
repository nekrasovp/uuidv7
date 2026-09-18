"""pyperf comparison; use --prototype only after building the research module."""
import functools
import json
import sys
import uuid

import fastuuid
import fastuuid7
import pyperf
import uuid_utils
from pydantic import BaseModel, TypeAdapter

from common import RAW, TEXTS, UUIDS, identity

PROTOTYPE = "--prototype" in sys.argv
if PROTOTYPE:
    sys.argv.remove("--prototype")
    import _uuid_lab as lab

    from integration import BulkModel, NativeModel, ScalarModel


class StandardModel(BaseModel):
    ids: list[uuid.UUID]
    label: str = "sample"


ONE = TypeAdapter(uuid.UUID)
MANY = TypeAdapter(list[uuid.UUID])


def repeated(fn, values):
    for value in values:
        fn(value)


def each(fn, values):
    return [fn(x) for x in values]


def main():
    runner = pyperf.Runner(add_cmdline_args=lambda cmd, args: cmd.extend(["--prototype"] if PROTOTYPE else []))
    runner.metadata["study_identity"] = json.dumps(identity(), sort_keys=True)
    runner.metadata["prototype"] = int(PROTOTYPE)
    if PROTOTYPE:
        from common import digest
        runner.metadata["extension_sha256"] = digest(lab.__file__)
    scalar = {
        "stdlib": uuid.UUID,
        "pydantic": ONE.validate_python,
        "uuid_utils_to_stdlib": lambda s: uuid.UUID(int=uuid_utils.UUID(s).int),
        "fastuuid_to_stdlib": lambda s: uuid.UUID(int=fastuuid.UUID(s).int),
        "uuid_utils_native": uuid_utils.UUID,
        "fastuuid_native": fastuuid.UUID,
    }
    if PROTOTYPE:
        scalar.update(c_stdlib=lab.parse, c_native=lab.parse_native, c_bytes=lab.parse_bytes)
    for form, values in {
        "canonical": TEXTS[:32], "hex": [u.hex for u in UUIDS[:32]],
        "urn": [u.urn for u in UUIDS[:32]],
    }.items():
        for name, fn in scalar.items():
            actual = [fn(s) for s in values]
            assert [x if isinstance(x, bytes) else x.bytes for x in actual] == RAW[:32]
            if name in ("stdlib", "pydantic", "uuid_utils_to_stdlib", "fastuuid_to_stdlib", "c_stdlib"):
                assert all(type(x) is uuid.UUID for x in actual)
            runner.bench_func(f"parse/{form}/{name}", repeated, fn, values, inner_loops=len(values))
    for size in (1, 100, 1000):
        values = TEXTS[:size]
        batch = {"stdlib": functools.partial(each, uuid.UUID), "pydantic": MANY.validate_python,
                 "uuid_utils_to_stdlib": functools.partial(each, scalar["uuid_utils_to_stdlib"]),
                 "fastuuid_to_stdlib": functools.partial(each, scalar["fastuuid_to_stdlib"])}
        if PROTOTYPE:
            batch.update(c_stdlib=lab.parse_many, c_native=lab.parse_many_native,
                         c_packed=lab.parse_many_bytes, c_packed_detach=lab.parse_many_bytes_detach)
        for name, fn in batch.items():
            result = fn(values)
            assert (result if isinstance(result, bytes) else b"".join(x.bytes for x in result)) == b"".join(RAW[:size])
            runner.bench_func(f"batch/{size}/{name}", fn, values)
        # Complete parse->canonical text consumer: native conversion remains timed.
        for name, fn in batch.items():
            if "packed" not in name:
                runner.bench_func(f"roundtrip/{size}/{name}", lambda f=fn, v=values: [str(x) for x in f(v)])
        models = {"pydantic": StandardModel}
        if PROTOTYPE:
            models.update(c_scalar=ScalarModel, c_bulk=BulkModel, c_native=NativeModel)
        payload = {"ids": values, "label": "sample"}
        encoded = json.dumps(payload).encode()
        for name, model in models.items():
            obj = model.model_validate(payload)
            assert json.loads(obj.model_dump_json()) == payload
            runner.bench_func(f"model_python/{size}/{name}", model.model_validate, payload)
            runner.bench_func(f"model_json/{size}/{name}", model.model_validate_json, encoded)
            runner.bench_func(f"model_dump/{size}/{name}", obj.model_dump_json)
    objects = {"stdlib": UUIDS[:32], "uuid_utils": [uuid_utils.UUID(s) for s in TEXTS[:32]],
               "fastuuid": [fastuuid.UUID(s) for s in TEXTS[:32]]}
    if PROTOTYPE:
        objects["c_native"] = lab.parse_many_native(TEXTS[:32])
    for name, values in objects.items():
        for shape, fn in {"str": str, "hex": lambda u: u.hex, "bytes": lambda u: u.bytes}.items():
            runner.bench_func(f"format/{shape}/{name}", repeated, fn, values, inner_loops=32)
    for name, fn in {"stdlib": uuid.uuid4, "uuid_utils_compat": uuid_utils.compat.uuid4,
                     "uuid_utils_native": uuid_utils.uuid4, "fastuuid_native": fastuuid.uuid4,
                     **({"c_stdlib": lab.uuid4} if PROTOTYPE else {})}.items():
        assert fn().version == 4
        runner.bench_func(f"uuid4/{name}", fn)
    runner.bench_func("uuid7/released_050", fastuuid7.uuid7)
    runner.bench_func("uuid7/uuid_utils_compat", uuid_utils.compat.uuid7)
    if hasattr(uuid, "uuid7"):
        runner.bench_func("uuid7/stdlib", uuid.uuid7)


if __name__ == "__main__":
    main()
