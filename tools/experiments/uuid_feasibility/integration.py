"""Explicit Pydantic integration; ordinary UUID values remain the default."""

import uuid
from typing import Annotated

import _uuid_lab as lab
from pydantic import BaseModel
from pydantic_core import SchemaValidator, core_schema

STANDARD = SchemaValidator(core_schema.uuid_schema())
STANDARD_LIST = SchemaValidator(core_schema.list_schema(core_schema.uuid_schema()))


def parse_or_fallback(value):
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return lab.parse(value)
        except (ValueError, UnicodeError):
            pass
    return STANDARD.validate_python(value)


def bulk_or_fallback(value):
    if isinstance(value, list):
        try:
            return lab.parse_many(value)
        except (ValueError, TypeError, UnicodeError):
            pass
    return STANDARD_LIST.validate_python(value)


class ScalarAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        normal = core_schema.uuid_schema()
        custom = core_schema.no_info_plain_validator_function(
            parse_or_fallback, json_schema_input_schema=normal, serialization=normal
        )
        return core_schema.json_or_python_schema(
            json_schema=custom,
            python_schema=core_schema.lax_or_strict_schema(
                custom, core_schema.uuid_schema(strict=True)
            ),
        )


class BulkAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        normal = core_schema.list_schema(core_schema.uuid_schema())
        custom = core_schema.no_info_plain_validator_function(
            bulk_or_fallback, json_schema_input_schema=normal, serialization=normal
        )
        # In Python strict mode each UUID must already be an instance.
        strict = core_schema.list_schema(core_schema.uuid_schema(strict=True), strict=True)
        return core_schema.json_or_python_schema(
            json_schema=custom, python_schema=core_schema.lax_or_strict_schema(custom, strict)
        )


class NativeAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        def convert(value):
            if isinstance(value, lab.NativeUUID):
                return value
            if isinstance(value, str):
                try:
                    return lab.parse_native(value)
                except (ValueError, UnicodeError):
                    pass
            return lab.parse_native(str(STANDARD.validate_python(value)))

        normal = core_schema.uuid_schema()
        schema = core_schema.no_info_plain_validator_function(
            convert,
            json_schema_input_schema=normal,
            serialization=core_schema.to_string_ser_schema(when_used="json"),
        )
        return core_schema.json_or_python_schema(json_schema=schema, python_schema=schema)


FastUUID = Annotated[uuid.UUID, ScalarAnnotation]
FastUUIDList = Annotated[list[uuid.UUID], BulkAnnotation]
NativeUUID = Annotated[lab.NativeUUID, NativeAnnotation]


class StandardModel(BaseModel):
    ids: list[uuid.UUID]
    label: str = "sample"


class ScalarModel(BaseModel):
    ids: list[FastUUID]
    label: str = "sample"


class BulkModel(BaseModel):
    ids: FastUUIDList
    label: str = "sample"


class NativeModel(BaseModel):
    ids: list[NativeUUID]
    label: str = "sample"
