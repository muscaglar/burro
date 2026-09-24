"""The schema as it is sent: every reference written out, and nothing lost on the way.

The guard that follows every adapter relies on the names of the fields, on
which are required, on their types and on the choices each may take. A
translation that kept all four has lost nothing the guard relies on. Limits
on length and on range are no part of the schema that is sent: they are
checked where the answer is validated, as they always were.

The tests of the reader's own schema need the reader, and the reader needs
the engine. They are skipped, and say so, while the engine cannot be loaded.
"""

import copy
import json
from collections.abc import Callable, Iterator
from typing import Any, cast

import pytest
from burro_api.providers.base import Unfit, inlined
from burro_api.providers.deepseek import nothing_asked

from .cases import SCHEMA

# What is left once every reference is written out. Each is on the list of
# what is supported in the documents of all four providers.
KEYWORDS = {"type", "properties", "required", "additionalProperties", "enum", "items"}


def fits(value: object, schema: dict[str, Any], defined: dict[str, Any] | None = None) -> bool:
    """Whether `value` fits `schema`, for the keywords the reader's schema is made of."""
    known: dict[str, Any] = schema.get("$defs", defined or {})
    if "$ref" in schema:
        return fits(value, known[schema["$ref"].removeprefix("#/$defs/")], known)
    if "enum" in schema and value not in schema["enum"]:
        return False
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            return False
        held = cast(dict[str, object], value)
        properties: dict[str, Any] = schema.get("properties", {})
        if set(schema.get("required", ())) - set(held):
            return False
        if schema.get("additionalProperties") is False and set(held) - set(properties):
            return False
        return all(fits(held[name], properties[name], known) for name in held if name in properties)
    if kind == "array":
        return isinstance(value, list) and all(
            fits(item, schema.get("items", {}), known) for item in cast(list[object], value)
        )
    if isinstance(value, bool):
        return kind in (None, "boolean")
    checks: dict[object, tuple[type, ...]] = {
        "string": (str,),
        "integer": (int,),
        "number": (int, float),
        "boolean": (bool,),
        None: (object,),
    }
    return isinstance(value, checks[kind])


def full(schema: dict[str, Any]) -> object:
    """An answer that fits `schema` and uses all of it: one item in every list."""
    if "enum" in schema:
        return schema["enum"][-1]
    if schema.get("type") == "object":
        return {name: full(held) for name, held in schema.get("properties", {}).items()}
    if schema.get("type") == "array":
        return [full(schema["items"])]
    return nothing_asked(schema)


def spoiled(answer: object) -> Iterator[tuple[str, object]]:
    """`answer`, again and again, each time with one thing wrong with it."""

    def places(node: object, path: tuple[object, ...] = ()) -> Iterator[tuple[object, ...]]:
        yield path
        if isinstance(node, dict):
            for name, held in cast(dict[str, object], node).items():
                yield from places(held, (*path, name))
        if isinstance(node, list):
            for index, held in enumerate(cast(list[object], node)):
                yield from places(held, (*path, index))

    def changed(path: tuple[object, ...], change: Callable[[object], object] | None) -> object:
        whole = copy.deepcopy(answer)
        if not path:
            return whole if change is None else change(whole)
        holder: Any = whole
        for step in path[:-1]:
            holder = holder[step]
        if change is None:
            del holder[path[-1]]
        else:
            holder[path[-1]] = change(holder[path[-1]])
        return whole

    def another_choice(_: object) -> object:
        return "not-a-choice-0"

    def another_type(old: object) -> object:
        return [old, {"a": None}]

    def nothing(_: object) -> object:
        return None

    def one_field_more(old: object) -> object:
        return (cast(dict[str, object], old) if isinstance(old, dict) else {}) | {"another": 1}

    for path in places(answer):
        where = "/".join(map(str, path))
        if path and isinstance(path[-1], str):
            yield f"{where} is missing", changed(path, None)
        yield f"{where} is a choice nobody offered", changed(path, another_choice)
        yield f"{where} is of another type", changed(path, another_type)
        yield f"{where} is null", changed(path, nothing)
        yield f"{where} holds a field nobody named", changed(path, one_field_more)


def keywords(schema: object, names: bool = False) -> set[str]:
    """Every keyword in `schema`. The name of a field is no keyword."""
    if isinstance(schema, list):
        return {found for item in cast(list[object], schema) for found in keywords(item)}
    if not isinstance(schema, dict):
        return set()
    held = cast(dict[str, object], schema)
    below = {
        found
        for key, value in held.items()
        for found in keywords(value, names=key in ("properties", "$defs") and not names)
    }
    return below if names else set(held) | below


def assert_nothing_is_lost(schema: dict[str, Any]) -> None:
    sent = inlined(schema)

    assert keywords(sent) <= KEYWORDS
    assert "$ref" not in json.dumps(sent) and "$defs" not in json.dumps(sent)
    for answer in (nothing_asked(sent), full(sent)):
        assert fits(answer, schema) and fits(answer, sent)
        tried = 0
        for what, wrong in spoiled(answer):
            tried += 1
            assert fits(wrong, schema) == fits(wrong, sent), what
        assert tried >= 10
    # And what is wrong is refused, by both: the way of looking has teeth.
    refused = [what for what, wrong in spoiled(full(sent)) if not fits(wrong, sent)]
    assert len(refused) > len(list(spoiled(full(sent)))) // 2


def test_every_reference_is_written_out_and_the_definitions_are_gone():
    assert inlined(SCHEMA) == {
        "additionalProperties": False,
        "properties": {
            "status": {"enum": ["ok", "off_topic"], "type": "string"},
            "edits": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "kind": {"enum": ["add", "remove"], "type": "string"},
                        "words": {"type": "string"},
                        "minutes": {"type": "integer"},
                    },
                    "required": ["kind", "words", "minutes"],
                    "type": "object",
                },
                "type": "array",
            },
        },
        "required": ["status", "edits"],
        "type": "object",
    }


def test_the_order_of_the_fields_is_kept():
    # Two providers say they write the answer in the order of the schema.
    assert list(cast(dict[str, Any], inlined(SCHEMA)["properties"])) == ["status", "edits"]


def test_the_schema_that_was_given_is_not_changed():
    before = copy.deepcopy(SCHEMA)

    inlined(SCHEMA)

    assert before == SCHEMA


def test_nothing_the_guard_relies_on_is_lost_from_a_small_schema():
    assert_nothing_is_lost(SCHEMA)


def test_what_stands_beside_a_reference_is_kept():
    schema = {
        "$defs": {"Kind": {"enum": ["add", "remove"], "type": "string"}},
        "type": "object",
        "properties": {"kind": {"$ref": "#/$defs/Kind", "enum": ["add"]}},
    }

    # One provider refuses a reference with a keyword beside it. Written out, there is none.
    assert inlined(schema)["properties"] == {"kind": {"enum": ["add"], "type": "string"}}


def test_a_reference_into_definitions_under_their_older_name_is_written_out():
    schema = {"definitions": {"Flag": {"type": "boolean"}}, "$ref": "#/definitions/Flag"}

    assert inlined(schema) == {"type": "boolean"}


def test_a_reference_through_a_reference_is_written_out():
    schema = {
        "$defs": {
            "A": {"$ref": "#/$defs/B"},
            "B": {"items": {"$ref": "#/$defs/C"}},
            "C": {"enum": [1]},
        },
        "$ref": "#/$defs/A",
    }

    assert inlined(schema) == {"items": {"enum": [1]}}


@pytest.mark.parametrize(
    "schema",
    [
        {"$ref": "#/$defs/Missing"},
        {"$defs": {"A": {"type": "string"}}, "$ref": "#/$defs/B"},
        {"$defs": {"A": {"$ref": "#/$defs/A"}}, "$ref": "#/$defs/A"},
        {
            "$defs": {"A": {"items": {"$ref": "#/$defs/B"}}, "B": {"$ref": "#/$defs/A"}},
            "$ref": "#/$defs/A",
        },
        {"$defs": {"A": {"properties": {"again": {"$ref": "#/$defs/A"}}}}, "$ref": "#/$defs/A"},
        {"$ref": "https://schemas.example/edit.json"},
        {"$ref": "edit.json#/$defs/A"},
        {"$ref": "#"},
        {"$ref": "#/properties/kind", "properties": {"kind": {"type": "string"}}},
        {"$ref": 12},
        {"$defs": ["A"], "$ref": "#/$defs/A"},
        {"$defs": {"A": "string"}, "$ref": "#/$defs/A"},
    ],
    ids=range(12),
)
def test_a_reference_that_leads_out_of_the_schema_or_back_to_itself_is_refused(
    schema: dict[str, object],
):
    with pytest.raises(Unfit) as refused:
        inlined(schema)

    assert refused.value.args == ()


@pytest.fixture(scope="module")
def reader() -> Any:
    """The reader's own module, or a skip that says why there is none."""
    try:
        import burro_api.reader as found
    except ImportError:
        pytest.skip("the reader cannot be loaded: the engine under it is being rebuilt")
    return found


def test_nothing_the_guard_relies_on_is_lost_from_the_readers_schema(reader: Any):
    assert_nothing_is_lost(dict(reader.SCHEMA))


def test_the_readers_schema_is_sent_in_six_keywords_that_all_four_providers_list(reader: Any):
    assert keywords(reader.SCHEMA) == KEYWORDS | {"$defs", "$ref"}
    assert keywords(inlined(reader.SCHEMA)) == KEYWORDS


def _objects(schema: object) -> Iterator[dict[str, Any]]:
    if isinstance(schema, dict):
        held = cast(dict[str, Any], schema)
        if held.get("type") == "object":
            yield held
        for value in held.values():
            yield from _objects(value)
    if isinstance(schema, list):
        for item in cast(list[object], schema):
            yield from _objects(item)


def _depth(schema: object) -> int:
    if isinstance(schema, list):
        return max((_depth(item) for item in cast(list[object], schema)), default=0)
    if not isinstance(schema, dict):
        return 0
    held = cast(dict[str, Any], schema)
    below = max((_depth(value) for value in held.values()), default=0)
    return below + (held.get("type") in ("object", "array"))


def test_the_readers_schema_is_within_every_limit_a_provider_has_published(reader: Any):
    sent = inlined(reader.SCHEMA)
    objects = list(_objects(sent))
    choices = [
        value
        for node in _nodes(sent)
        if isinstance(node.get("enum"), list)
        for value in node["enum"]
    ]
    names = [name for held in objects for name in held["properties"]]

    # Two providers ask that every object be closed and every field required.
    assert sent["type"] == "object" and objects
    assert all(held["additionalProperties"] is False for held in objects)
    assert all(sorted(held["required"]) == sorted(held["properties"]) for held in objects)
    # One counts optional fields, to 24, and fields of more than one type, to 16.
    assert not any(isinstance(node.get("type"), list) for node in _nodes(sent))
    assert not {"anyOf", "oneOf", "allOf"} & keywords(sent)
    # One publishes numbers: 5,000 fields, 1,000 choices, 10 levels, 120,000 characters of names.
    assert len(names) <= 5000 and len(choices) <= 1000 and _depth(sent) <= 10
    assert sum(len(str(text)) for text in (*names, *choices)) <= 120_000
    assert all(isinstance(choice, str) for choice in choices)
    # None publishes a size. It is kept small all the same.
    assert len(json.dumps(sent)) < 16_000


def _nodes(schema: object) -> Iterator[dict[str, Any]]:
    if isinstance(schema, dict):
        yield cast(dict[str, Any], schema)
        for value in cast(dict[str, object], schema).values():
            yield from _nodes(value)
    if isinstance(schema, list):
        for item in cast(list[object], schema):
            yield from _nodes(item)


def test_the_example_one_provider_is_shown_is_an_answer_the_guard_accepts(reader: Any):
    example = nothing_asked(inlined(reader.SCHEMA))

    parsed = reader.ModelOutput.model_validate_json(json.dumps(example))

    assert parsed.status is reader.ModelStatus.OK
    assert example == {"status": "ok"} | {
        name: [] for name in reader.SCHEMA["properties"] if name != "status"
    }


def test_writing_the_references_out_makes_the_readers_schema_no_longer(reader: Any):
    assert len(json.dumps(inlined(reader.SCHEMA))) <= len(json.dumps(dict(reader.SCHEMA)))
