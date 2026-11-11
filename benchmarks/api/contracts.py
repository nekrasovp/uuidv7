"""Benchmark-only adapters. Library imports never install framework hooks."""

import uuid
from typing import Annotated

import uuid_utils
import uuid_utils.compat
from pydantic import create_model
from pydantic_core import SchemaValidator, core_schema

import fastuuid7

STANDARD = SchemaValidator(core_schema.uuid_schema())
STANDARD_LIST = SchemaValidator(core_schema.list_schema(core_schema.uuid_schema()))


def configuration(variant):
    if variant not in (
        "baseline-default",
        "candidate-default",
        "baseline-explicit",
        "candidate-explicit",
        "uuid-utils-compat",
        "uuid-utils-native",
    ):
        raise ValueError("unknown benchmark variant")
    explicit = variant.endswith("-explicit")
    native = variant == "uuid-utils-native"
    provider = (
        uuid_utils if native else uuid_utils.compat if variant == "uuid-utils-compat" else fastuuid7
    )
    scalar_type = uuid.UUID
    list_type = list[uuid.UUID]
    if explicit or native:
        parse = uuid_utils.UUID if native else fastuuid7.parse
        result_type = uuid_utils.UUID if native else uuid.UUID

        def parse_or_fallback(value):
            if isinstance(value, result_type):
                return value
            if isinstance(value, str):
                try:
                    return parse(value)
                except (ValueError, UnicodeError):
                    pass
            standard = STANDARD.validate_python(value)
            return uuid_utils.UUID(str(standard)) if native else standard

        class Scalar:
            @classmethod
            def __get_pydantic_core_schema__(cls, _source, _handler):
                normal = core_schema.uuid_schema()
                custom = core_schema.no_info_plain_validator_function(
                    parse_or_fallback, json_schema_input_schema=normal
                )
                strict = (
                    core_schema.is_instance_schema(result_type)
                    if native
                    else core_schema.uuid_schema(strict=True)
                )
                serialize = (
                    core_schema.to_string_ser_schema(when_used="json")
                    if native
                    else core_schema.plain_serializer_function_ser_schema(
                        fastuuid7.format_uuid,
                        return_schema=core_schema.str_schema(),
                        when_used="json",
                    )
                )
                return core_schema.json_or_python_schema(
                    json_schema=custom,
                    python_schema=core_schema.lax_or_strict_schema(custom, strict),
                    serialization=serialize,
                )

        scalar_type = Annotated[result_type, Scalar]
        list_type = list[scalar_type]
        if explicit:

            def bulk_or_fallback(value):
                if isinstance(value, list):
                    try:
                        return fastuuid7.parse_many(value)
                    except (ValueError, TypeError, UnicodeError):
                        pass
                return STANDARD_LIST.validate_python(value)

            def format_list(values):
                return [fastuuid7.format_uuid(value) for value in values]

            class Bulk:
                @classmethod
                def __get_pydantic_core_schema__(cls, _source, _handler):
                    normal = core_schema.list_schema(core_schema.uuid_schema())
                    custom = core_schema.no_info_plain_validator_function(
                        bulk_or_fallback, json_schema_input_schema=normal
                    )
                    strict = core_schema.list_schema(
                        core_schema.uuid_schema(strict=True), strict=True
                    )
                    return core_schema.json_or_python_schema(
                        json_schema=custom,
                        python_schema=core_schema.lax_or_strict_schema(custom, strict),
                        serialization=core_schema.plain_serializer_function_ser_schema(
                            format_list,
                            return_schema=core_schema.list_schema(core_schema.str_schema()),
                            when_used="json",
                        ),
                    )

            list_type = Annotated[list[uuid.UUID], Bulk]
    model = create_model("UUIDPayload", ids=(list_type, ...), label=(str, "sample"))
    single = create_model("UUIDItem", id=(scalar_type, ...))
    return model, single, scalar_type, provider
