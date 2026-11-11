"""Public UUIDv4, strict text parsing and formatting contracts."""

import os
import pickle
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

import fastuuid7 as f
import uuidv7
from uuidv7.uuidv7_impl.uuid7_gen import (
    _generate_uuid7_bytes_for_tests,
    _reset_state_for_tests,
    _set_state_for_tests,
)

TEXT = "00112233-4455-4677-8899-aabbccddeeff"
RAW = uuid.UUID(TEXT).bytes
PUBLIC = [
    "uuid4",
    "uuid4_str",
    "uuid4_bytes",
    "uuid4_many",
    "uuid4_str_many",
    "uuid4_bytes_many",
    "parse",
    "parse_many",
    "parse_bytes_many",
    "format_uuid",
]


def test_public_aliases():
    for name in PUBLIC:
        assert getattr(f, name) is getattr(uuidv7, name)
        assert name in f.__all__ and name in uuidv7.__all__


@pytest.mark.parametrize("count", [0, 1, 257, 2049])
def test_v4_shapes_and_pool_refills(count):
    objects = f.uuid4_many(count)
    strings = f.uuid4_str_many(count)
    raw = f.uuid4_bytes_many(count)
    assert len(objects) == len(strings) == count
    assert len(raw) == count * 16
    values = objects + [uuid.UUID(s) for s in strings]
    values += [uuid.UUID(bytes=raw[i : i + 16]) for i in range(0, len(raw), 16)]
    assert all(
        type(v) is uuid.UUID and v.version == 4 and v.variant == uuid.RFC_4122 for v in values
    )
    assert all(v.is_safe is uuid.SafeUUID.unknown for v in objects)
    assert len(set(values)) == len(values)  # catches duplicated buffers; not an RNG proof
    assert len({id(v) for v in objects}) == len(objects)
    assert pickle.loads(pickle.dumps(objects)) == objects


def test_v4_scalar_and_retained_values():
    value = f.uuid4()
    before = value.bytes
    assert type(value) is uuid.UUID and value.version == 4
    assert uuid.UUID(f.uuid4_str()).version == 4
    assert uuid.UUID(bytes=f.uuid4_bytes()).version == 4
    assert isinstance(f.uuid4_str(), str) and type(f.uuid4_bytes()) is bytes
    f.uuid4_many(1000)
    assert value.bytes == before
    with pytest.raises(TypeError):
        value.int = 0


@pytest.mark.parametrize("method", [f.uuid4_many, f.uuid4_str_many, f.uuid4_bytes_many])
def test_v4_count_validation(method):
    with pytest.raises(ValueError):
        method(-1)
    for invalid in (1.5, "2", None):
        with pytest.raises(TypeError):
            method(invalid)
    with pytest.raises(OverflowError):
        method(sys.maxsize + 1)

    # Like the existing v7 batch APIs, accept __index__ and bool.
    class Count:
        def __index__(self):
            return 2

    assert len(method(Count())) == (32 if method is f.uuid4_bytes_many else 2)


def test_packed_count_overflow():
    with pytest.raises(MemoryError):
        f.uuid4_bytes_many(sys.maxsize // 16 + 1)


def test_v4_does_not_advance_live_v7_state():
    try:
        _set_state_for_tests(100_000, 42)
        f.uuid4_many(600)
        value = uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(99_002))
        counter = ((value.int >> 64) & 0xFFF) << 30 | ((value.int >> 32) & ((1 << 30) - 1))
        assert value.int >> 80 == 100_000 and counter == 43
        following = uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(100_001))
        assert value < following
    finally:
        _reset_state_for_tests()


def test_threads_retain_independent_v4_results():
    with ThreadPoolExecutor(4) as pool:
        batches = list(pool.map(f.uuid4_many, [1000] * 4))
    values = [v for batch in batches for v in batch]
    assert len(set(values)) == 4000
    assert all(v.version == 4 for v in values)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires POSIX fork")
@pytest.mark.parametrize("native_fork", [False, True])
def test_v4_fork_discards_parent_pool(native_fork):
    f.uuid4()
    read_fd, write_fd = os.pipe()
    if native_fork:
        # Exercise libc fork without CPython's Python-level at-fork callbacks.
        import ctypes

        libc = ctypes.PyDLL(None)
        libc.fork.restype = ctypes.c_int
        pid = libc.fork()
        if pid < 0:
            pytest.fail("native fork failed")
    else:
        pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            os.write(write_fd, f.uuid4_bytes_many(32))
        finally:
            os._exit(0)
    os.close(write_fd)
    try:
        parent = f.uuid4_bytes_many(32)
        child = os.read(read_fd, 512)
    finally:
        os.close(read_fd)
        _, status = os.waitpid(pid, 0)
    assert status == 0 and len(child) == 512
    parent_set = {parent[i : i + 16] for i in range(0, 512, 16)}
    assert parent_set.isdisjoint(child[i : i + 16] for i in range(0, 512, 16))


@pytest.mark.parametrize(
    "text",
    [
        TEXT,
        TEXT.upper(),
        TEXT.replace("-", ""),
        "{" + TEXT + "}",
        "urn:uuid:" + TEXT,
        "UrN:UuId:" + TEXT.upper(),
    ],
)
def test_parse_supported_forms(text):
    value = f.parse(text)
    assert type(value) is uuid.UUID and value.bytes == RAW
    assert value == uuid.UUID(TEXT) and hash(value) == hash(uuid.UUID(TEXT))
    assert value.is_safe is uuid.SafeUUID.unknown
    assert pickle.loads(pickle.dumps(value)) == value
    assert f.format_uuid(value) == f.format_uuid(RAW) == TEXT
    assert f.parse_many(iter([text, text])) == [value, value]
    assert f.parse_bytes_many([text, text]) == RAW * 2


@pytest.mark.parametrize("value", [0, (1 << 128) - 1, *[1 << bit for bit in range(128)]])
def test_parse_all_bits_and_variants(value):
    expected = uuid.UUID(int=value)
    actual = f.parse(str(expected))
    assert actual == expected
    assert actual.version == expected.version and actual.variant == expected.variant
    assert actual.fields == expected.fields and actual.time == expected.time


@pytest.mark.parametrize(
    "text",
    [
        "",
        "0" * 31,
        "0" * 33,
        " " + TEXT,
        TEXT + "\n",
        TEXT + "\x00",
        TEXT[:8] + "_" + TEXT[9:],
        "g" + TEXT[1:],
        "{" + TEXT,
        "{{" + TEXT + "}}",
        "{" + TEXT.replace("-", "") + "}",
        "urn:uuid:" + TEXT.replace("-", ""),
        "urn:uuid:{" + TEXT + "}",
        "Ｕ" + TEXT[1:],
        "\ud800" + TEXT[1:],
        "\x00" + TEXT[1:],
        "+" + TEXT.replace("-", "")[1:],
        "-" + TEXT.replace("-", "")[1:],
        pytest.param(" " * 100_000, id="oversized-whitespace"),
    ],
)
def test_parse_rejects_malformed_text(text):
    with pytest.raises(ValueError):
        f.parse(text)
    for method in (f.parse_many, f.parse_bytes_many):
        with pytest.raises(ValueError, match="index 1"):
            method([TEXT, text, TEXT])


@pytest.mark.parametrize(
    "arg", [None, 1, True, RAW, bytearray(RAW), memoryview(RAW), uuid.UUID(TEXT)]
)
def test_parse_rejects_non_text(arg):
    with pytest.raises(TypeError):
        f.parse(arg)
    for method in (f.parse_many, f.parse_bytes_many):
        with pytest.raises(TypeError, match="index 1"):
            method([TEXT, arg])


def test_batch_snapshot_and_iterator_failure():
    assert f.parse_many([]) == [] and f.parse_bytes_many([]) == b""
    for method in (f.parse_many, f.parse_bytes_many):

        def broken():
            yield TEXT
            raise RuntimeError("iterator failed")

        with pytest.raises(RuntimeError, match="iterator failed"):
            method(broken())
        with pytest.raises(TypeError):
            method(None)

    class Text(str):
        def __str__(self):
            raise AssertionError("must not stringify input")

    assert f.parse(Text(TEXT)) == uuid.UUID(TEXT)


def test_format_types_lengths_and_subclass_failure():
    native = f.uuid7_obj()
    assert f.format_uuid(native) == str(native)
    for arg in (TEXT, None, 1, bytearray(RAW), memoryview(RAW)):
        with pytest.raises(TypeError):
            f.format_uuid(arg)
    for raw in (b"", RAW[:-1], RAW + b"\0"):
        with pytest.raises(ValueError):
            f.format_uuid(raw)

    class BrokenUUID(uuid.UUID):
        @property
        def bytes(self):
            return "not bytes"

    with pytest.raises(TypeError):
        f.format_uuid(BrokenUUID(TEXT))


@pytest.mark.parametrize("number", [0, (1 << 128) - 1, *[1 << bit for bit in range(128)]])
def test_format_and_uuid7_str_preserve_all_128_bits(number):
    reference = uuid.UUID(int=number)
    value = uuidv7._UUID7(int=number)
    assert str(value) == str(reference)
    assert repr(value) == repr(reference)
    assert format(value) == format(reference)
    with pytest.raises(TypeError):
        format(value, ">40")
    assert value.urn == reference.urn
    assert f.format_uuid(reference) == f.format_uuid(value) == str(reference)


def test_format_custom_uuid_subclasses_keep_bytes_contract():
    class Custom(uuid.UUID):
        @property
        def bytes(self):
            return b"\xff" * 16

    class CustomV7(uuidv7._UUID7):
        @property
        def bytes(self):
            return b"\xff" * 16

    for cls in (Custom, CustomV7):
        value = cls(TEXT)
        assert f.format_uuid(value) == str(uuid.UUID(int=(1 << 128) - 1))
        assert str(value) == uuid.UUID.__str__(value)

    class Failing(uuid.UUID):
        @property
        def bytes(self):
            raise RuntimeError("custom bytes")

    with pytest.raises(RuntimeError, match="custom bytes"):
        f.format_uuid(Failing(TEXT))


@pytest.mark.parametrize("number", [-1, 1 << 128, 1 << 256, True])
def test_unusual_uuid_state_preserves_stdlib_fallback(number):
    reference = uuid.UUID(TEXT)
    value = uuidv7._UUID7(TEXT)
    object.__setattr__(reference, "int", number)
    object.__setattr__(value, "int", number)
    try:
        expected_text = str(reference)
    except (OverflowError, ValueError) as error:
        with pytest.raises(type(error)):
            str(value)
    else:
        assert str(value) == expected_text
    try:
        expected = str(uuid.UUID(bytes=reference.bytes))
    except (OverflowError, ValueError) as error:
        for obj in (reference, value):
            with pytest.raises(type(error)):
                f.format_uuid(obj)
    else:
        assert f.format_uuid(reference) == f.format_uuid(value) == expected


def test_format_int_subclass_preserves_python_methods():
    class Number(int):
        def to_bytes(self, *_args, **_kwargs):
            return b"\xff" * 16

    value = uuidv7._UUID7(TEXT)
    reference = uuid.UUID(TEXT)
    for obj in (value, reference):
        object.__setattr__(obj, "int", Number(obj.int))
        assert f.format_uuid(obj) == str(uuid.UUID(int=(1 << 128) - 1))
    assert str(value) == str(reference)


def test_parser_every_single_byte_substitution_against_strict_grammar():
    canonical = r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}"
    grammar = re.compile(
        rf"(?:[0-9a-fA-F]{{32}}|{canonical}|\{{{canonical}\}}|(?i:urn:uuid:){canonical})"
    )
    for original in (TEXT, TEXT.replace("-", ""), "{" + TEXT + "}", "urn:uuid:" + TEXT):
        for position in range(len(original)):
            for byte in range(256):
                text = original[:position] + chr(byte) + original[position + 1 :]
                if grammar.fullmatch(text):
                    normalized = text.lower().removeprefix("urn:uuid:").strip("{}")
                    assert f.parse(text) == uuid.UUID(normalized)
                else:
                    with pytest.raises(ValueError):
                        f.parse(text)
