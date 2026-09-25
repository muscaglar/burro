"""The OpenAPI document: one file that the web and iOS clients are generated from.

It is generated and committed. If a route or a record changes and the file is
not written again, the clients would be built against a contract the service
no longer keeps, so a test fails until `make openapi` is run.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from burro_api.cli import openapi_document
from burro_api.routes import areas, census, income, interpret, meta, places, rank, shares
from fastapi import FastAPI
from fastapi.routing import APIRoute

from .support import client_for, make_deps

COMMITTED = Path(__file__).resolve().parents[3] / "contracts" / "openapi.json"

ROUTES = {
    ("POST", "/v1/interpret"),
    ("POST", "/v1/rank"),
    ("POST", "/v1/explanations"),
    ("GET", "/v1/areas"),
    ("GET", "/v1/areas/geometry"),
    ("GET", "/v1/areas/{id_or_slug}"),
    ("GET", "/v1/areas/{id_or_slug}/census"),
    ("GET", "/v1/areas/{id_or_slug}/income"),
    ("POST", "/v1/compare"),
    ("POST", "/v1/places/search"),
    ("POST", "/v1/shares"),
    ("GET", "/v1/shares/{share_id}"),
    ("GET", "/v1/meta"),
    ("GET", "/healthz"),
}


@pytest.fixture(scope="module")
def app() -> FastAPI:
    app = client_for(make_deps()).app
    assert isinstance(app, FastAPI)
    return app


@pytest.fixture(scope="module")
def document(app: FastAPI) -> dict[str, Any]:
    return app.openapi()


def operations(document: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any]]]:
    for path, item in document["paths"].items():
        for method, operation in item.items():
            yield method.upper(), path, operation


def everything_in(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        found = cast(dict[str, Any], value)
        yield found
        for inner in found.values():
            yield from everything_in(inner)
    elif isinstance(value, list):
        for inner in cast(list[Any], value):
            yield from everything_in(inner)


def test_committed_openapi_document_is_up_to_date(app: FastAPI):
    written = COMMITTED.read_text(encoding="utf-8")

    assert written == openapi_document(app), "run `make openapi` and commit the result"


def test_the_routes_are_the_routes_of_the_contract(document: dict[str, Any]):
    found = {(method, path) for method, path, _ in operations(document)}

    assert found == ROUTES
    # Each is named for what a generated client will call it.
    names = [operation["operationId"] for *_, operation in operations(document)]
    assert len(set(names)) == len(ROUTES)
    assert all(name.isidentifier() and name == name.lower() for name in names)


def test_an_operation_is_named_for_its_route(document: dict[str, Any]):
    # The routes as they were declared, whatever the framework nests them in.
    groups = (interpret, rank, areas, census, income, places, shares, meta)
    declared = [route for group in groups for route in group.router.routes]
    routes = [route for route in (*declared, *meta.health.routes) if isinstance(route, APIRoute)]
    named = {route.path: route.name for route in routes}
    assert len(named) == len(ROUTES)

    assert {path: operation["operationId"] for _, path, operation in operations(document)} == named
    # A route is named for its function, but for the one whose function
    # stands beside core's `rank` and so cannot have its name.
    functions = {route.name: route.endpoint.__name__ for route in routes}
    assert {n: f for n, f in functions.items() if n != f} == {"rank": "rank_areas"}


def test_no_route_takes_typed_text_in_a_path_or_query(document: dict[str, Any]):
    parameters = {
        (path, parameter["in"], parameter["name"])
        for _, path, operation in operations(document)
        for parameter in operation.get("parameters", [])
    }

    # An id from the release and an opaque id. Nothing a person types, and no
    # query string at all: a URL reaches logs that Burro does not control.
    assert parameters == {
        ("/v1/areas/{id_or_slug}", "path", "id_or_slug"),
        ("/v1/areas/{id_or_slug}/census", "path", "id_or_slug"),
        ("/v1/areas/{id_or_slug}/income", "path", "id_or_slug"),
        ("/v1/shares/{share_id}", "path", "share_id"),
    }
    # What a person types is sent in a body, so every route that reads it is a POST.
    for method, path, operation in operations(document):
        assert ("requestBody" in operation) == (method == "POST"), path


def test_every_error_is_documented_as_the_one_envelope(document: dict[str, Any]):
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}
    unchanged: set[str] = set()
    for _, path, operation in operations(document):
        for status, response in operation["responses"].items():
            if status == "304":
                # Not an error, and it has no body to hold an envelope.
                assert "content" not in response, path
                unchanged.add(path)
            elif status != "200":
                assert response["content"]["application/json"]["schema"] == envelope, path
    # Only what is a function of the release alone can be said to stand.
    assert unchanged == {"/v1/areas", "/v1/areas/geometry", "/v1/areas/{id_or_slug}", "/v1/meta"}
    # The framework's own error shape repeats the input. It is never served,
    # so it must not be in the document either.
    assert not [name for name in document["components"]["schemas"] if "Validation" in name]
    fields = document["components"]["schemas"]["FieldProblem"]["properties"]
    assert set(fields) == {"path", "problem"}


def test_every_response_is_documented_with_the_two_flags_of_the_release(
    document: dict[str, Any],
):
    for _, path, operation in operations(document):
        if path == "/healthz":
            continue
        reference = operation["responses"]["200"]["content"]["application/json"]["schema"]
        name = reference["$ref"].rsplit("/", 1)[-1]
        schema = document["components"]["schemas"][name]
        assert set(schema["required"]) == {"meta", "data"}, path
    meta = document["components"]["schemas"]["Meta"]
    assert set(meta["required"]) == {"release_id", "engine_version", "synthetic", "preview"}


def test_a_record_has_one_name_and_one_shape_in_the_document(document: dict[str, Any]):
    # A generated client names a type for its schema. A schema named for the
    # module it is in, or once for what is sent and once for what is served,
    # is a name nobody chose.
    names = list(document["components"]["schemas"])

    assert not [name for name in names if "__" in name or "-" in name or "." in name]
    assert {"Choice", "SuggestionChoice", "Operations", "SettingEdit"} <= set(names)
    assert document["components"]["schemas"]["Choice"]["type"] == "string"


def test_what_is_offered_holds_all_that_core_offers_and_the_four_parts_of_an_offer():
    from burro_api import wire
    from burro_core import interpret

    for ours, theirs in (
        (wire.Suggestion, interpret.Suggestion),
        (wire.SuggestionChoice, interpret.Choice),
    ):
        assert set(theirs.model_fields) <= set(ours.model_fields)
        for name, field in theirs.model_fields.items():
            if name != "choices":
                assert ours.model_fields[name].annotation == field.annotation, name
    # What it would do, where the person's words stand, what follows, and the choices.
    assert {"does", "spans", "shown", "follows", "said", "choices"} <= set(
        wire.Suggestion.model_fields
    )
    assert {"id", "guess"} <= set(wire.SuggestionChoice.model_fields)
    # What marks a reading for measuring is never served.
    assert not {"meant", "ruled"} & set(wire.SuggestionChoice.model_fields)
    assert not {"alone", "whole_sentence", "unsaid"} & set(wire.Suggestion.model_fields)


def test_the_document_is_of_the_second_version_of_the_contract(document: dict[str, Any]):
    assert document["info"]["version"] == "2"
    schemas = document["components"]["schemas"]
    # An edit to a vibe must say which end, and what is served says all of this.
    assert "toward" in schemas["TagEdit"]["required"]
    required = {
        "InterpretData": {"suggestions", "unread", "places"},
        "RankData": {"places"},
        "ShareCreated": {"places"},
        "ShareData": {"places"},
        "ExplanationsData": {"spec_hash"},
        "Score": {"counted", "present"},
        "ComparedArea": {"counted", "present"},
        "RankedArea": {"strip"},
        "AreasData": {"bands"},
        "AreaData": {"portrait", "similar"},
        "CompareData": {"character"},
        "MetaData": {"families", "gritty_variant"},
        "ServedLimits": {"reason_min_utility", "trade_off_max_utility"},
        "Metric": {"short_label", "kind", "describes", "family", "method", "in_likeness"},
        "Tag": {"short_label", "shape", "low_end", "high_end", "meaning", "cannot_see", "lens"},
    }
    for name, fields in required.items():
        assert fields <= set(schemas[name]["required"]), name


def test_no_list_on_the_wire_mixes_types(document: dict[str, Any]):
    for schema in everything_in(document["components"]["schemas"]):
        # A pair is a list of fixed length. Its members must all be one type,
        # as the two numbers of a coordinate are.
        members = schema.get("prefixItems", [])
        assert len({member.get("type") for member in members}) <= 1
        items = schema.get("items")
        if isinstance(items, dict):
            assert "anyOf" not in items and "oneOf" not in items


def test_the_only_vocabulary_is_the_allowlist(document: dict[str, Any]):
    from burro_core.ids import FeatureId, TagId

    schemas = document["components"]["schemas"]
    assert schemas["FeatureId"]["enum"] == [feature.value for feature in FeatureId]
    assert schemas["TagId"]["enum"] == [tag.value for tag in TagId]
    # An edit names a feature by its id, and an id is one of the enum or nothing.
    weight = schemas["WeightEdit"]["properties"]["feature_id"]
    assert weight == {"$ref": "#/components/schemas/FeatureId"}


def test_the_name_of_who_read_a_sentence_names_no_provider(document: dict[str, Any]):
    # The answer of route 1 says whether the rules or a model read the words. Which
    # provider's model is said by route 11, with what people are told of it.
    from burro_api.calls import Caller
    from burro_api.providers.terms import TERMS, Provider
    from burro_core.ids import InterpreterName

    assert [name.value for name in InterpreterName] == ["rule", "model"]
    assert [caller.value for caller in Caller] == ["rule", "model", "template"]
    assert document["components"]["schemas"]["InterpreterName"]["enum"] == ["rule", "model"]
    named = {provider.value for provider in Provider}
    named |= {terms.company.lower() for terms in TERMS.values()} | {"claude", "gpt", "google"}
    assert not named & {name.value for name in (*InterpreterName, *Caller)}
