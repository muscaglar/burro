"""The routes of the contract, driven through the app on the committed synthetic release."""

import copy
import json
import re
from collections.abc import Iterator
from dataclasses import replace
from functools import cache
from typing import Any, cast

import pytest
from burro_api.app import deps_from
from burro_api.deps import Deps
from burro_api.providers.choose import BY_RULES, told_of
from burro_api.providers.terms import (
    RULES_NOTICE,
    SETTINGS,
    TERMS,
    WORDS_ALONE,
    Provider,
    Question,
)
from burro_api.reader import ModelInterpreter
from burro_api.routes.common import default_for, told_tag
from burro_api.settings import Settings
from burro_api.stores import InMemoryShareStore
from burro_api.wire import BODIES, CompareStatus
from burro_core import ENGINE_VERSION, apply, check_spec, portrait, rank, similar, spec_hash
from burro_core.catalogue import (
    FAMILIES,
    FEATURES,
    JUDGEMENT,
    TAGS,
    default_direction,
    tags_of,
)
from burro_core.explain import REASON_MIN_UTILITY, TRADE_OFF_MAX_UTILITY
from burro_core.ids import (
    Combine,
    Direction,
    FeatureId,
    FilterReason,
    GrittyVariant,
    InterpreterName,
    Notice,
    OpsGroup,
    Provenance,
    TagId,
    Tenure,
    Toward,
    UnrankedReason,
)
from burro_core.interpret import (
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    Span,
    notice_text,
)
from burro_core.release import InMemoryRelease
from burro_core.spec import FeatureWeight, PreferenceSpec, TagWeight
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .support import (
    MODEL,
    NOW,
    SCHOOL,
    SCHOOL_COARSE,
    WORKS,
    FakeModelClient,
    budget,
    client_for,
    commute,
    make_deps,
    model_commute,
    model_output,
    reader_asking,
    release,
    renter,
    searching,
    wire,
)

GETS = ("/v1/areas", "/v1/areas/geometry", "/v1/areas/syn-n0001", "/v1/meta")
OF_THE_RELEASE = GETS
LOADED = '"syn-2026-09-23-01"'
# Route 11 says who reads what is typed, which is no part of the release. Its tag names
# the release and what is told, so that an answer which tells of another reader is never kept.
META = "/v1/meta"
META_BY_RULES = f'"syn-2026-09-23-01.{told_tag(BY_RULES)}"'


def tag_of(path: str) -> str:
    """The tag a browser is given for a route, where the rules read what is typed."""
    return META_BY_RULES if path == META else LOADED


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Kept open for the whole test, so that each request does not start a loop of its own.
    with client_for(make_deps()) as kept:
        yield kept


def fields_of(value: Any) -> set[str]:
    """The name of every field of an answer, however deep."""
    if isinstance(value, dict):
        held = cast(dict[str, Any], value)
        return set(held) | {name for inner in held.values() for name in fields_of(inner)}
    if isinstance(value, list):
        return {name for inner in cast(list[Any], value) for name in fields_of(inner)}
    return set()


def data(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    return response.json()["data"]


def asking_for(
    feature_id: FeatureId, weight: float, direction: Direction | None = None
) -> FeatureWeight:
    return FeatureWeight(
        feature_id=feature_id,
        weight=weight,
        direction=direction or default_direction(feature_id),
        provenance=Provenance.STATED,
    )


def posts(share_id: str = "") -> list[tuple[str, dict[str, Any]]]:
    spec = wire(searching())
    return [
        ("/v1/interpret", {"text": "somewhere leafy, 40 minutes to Cindermoor Works"}),
        ("/v1/rank", {"spec": spec}),
        # One area is explained: these are asked for how a call is answered, and not what with.
        ("/v1/explanations", {"spec": spec, "limit": 1}),
        ("/v1/compare", {"area_ids": ["syn-n0001", "syn-n0002"], "spec": spec}),
        ("/v1/places/search", {"q": "Wexmoor"}),
        ("/v1/shares", {"spec": spec}),
    ]


# The whole service.


def test_api_loads_the_committed_synthetic_release():
    deps = deps_from(Settings.from_env({}))

    manifest = deps.release.manifest
    assert manifest.release_id == "syn-2026-09-23-01" and manifest.synthetic is True
    assert len(deps.release.neighbourhoods) == manifest.counts.neighbourhoods == 24
    # The default is the rules: they need nothing.
    assert isinstance(deps.interpreter, RuleInterpreter)


def test_every_route_works_with_no_key_configured():
    client = client_for(deps_from(Settings.from_env({})))

    for path, body in posts():
        assert client.post(path, json=body).status_code == 200, path
    made = client.post("/v1/shares", json={"spec": wire(searching())}).json()["data"]
    for path in (*GETS, f"/v1/shares/{made['share_id']}", "/healthz"):
        assert client.get(path).status_code == 200, path
    interpreted = data(client.post("/v1/interpret", json=posts()[0][1]))
    assert interpreted["interpreter"] == "rule" and interpreted["degraded"] is False


@pytest.mark.parametrize(
    ("synthetic", "preview"), [(True, False), (False, False), (False, True), (True, True)]
)
def test_every_response_says_whether_it_is_synthetic_and_whether_it_is_a_preview(
    synthetic: bool, preview: bool
):
    loaded = release()
    told = replace(loaded, manifest=loaded.manifest.replace(synthetic=synthetic, preview=preview))
    client = client_for(make_deps(release=told))
    flag = "true" if synthetic else "false"
    unfinished = "true" if preview else "false"
    made = client.post("/v1/shares", json={"spec": wire(searching())}).json()["data"]

    answered = [client.post(path, json=body) for path, body in posts()]
    answered += [client.get(path) for path in (*GETS, f"/v1/shares/{made['share_id']}")]
    refused = [
        client.post("/v1/rank", json={"spec": "no"}),
        client.post("/v1/rank", content=b"{", headers={"content-type": "application/json"}),
        client.post("/v1/rank", content=b"{}", headers={"content-type": "text/plain"}),
        client.post("/v1/rank", json={"spec": wire(renter(commutes=(commute("syn-p9"),)))}),
        client.get("/v1/areas/nowhere"),
        client.get("/v1/shares/nothing"),
        client.get("/v1/nothing"),
        client.delete("/v1/meta"),
    ]

    assert [r.status_code for r in answered] == [200] * len(answered)
    assert [r.status_code for r in refused] == [422, 400, 415, 422, 404, 404, 404, 405]
    for response in (*answered, *refused):
        assert response.headers["x-burro-synthetic"] == flag
        assert response.headers["x-burro-preview"] == unfinished
        assert response.json()["meta"] == {
            "release_id": "syn-2026-09-23-01",
            "engine_version": ENGINE_VERSION,
            "synthetic": synthetic,
            "preview": preview,
        }
    # The health check says nothing about the release, but it too carries the flags.
    health = client.get("/healthz")
    assert health.json() == {"ok": True} and health.headers["x-burro-synthetic"] == flag
    assert health.headers["x-burro-preview"] == unfinished


def test_every_fact_served_is_marked_synthetic(client: TestClient):
    profile = data(client.get("/v1/areas/alderwick"))
    explained = data(client.post("/v1/explanations", json={"spec": wire(searching())}))

    facts = profile["facts"] + explained["facts"]
    assert len(facts) > 40
    assert all(fact["synthetic"] is True for fact in facts)
    assert all(fact["sources"] and fact["as_of"] for fact in facts)


def test_no_route_but_a_share_returns_a_spec_it_was_not_sent(client: TestClient):
    sent = wire(searching())
    ranked = data(client.post("/v1/rank", json={"spec": sent}))
    again = data(client.post("/v1/rank", json={"spec": wire(renter())}))

    # Nothing is kept for a search: the second ranking knows nothing of the first.
    assert ranked["spec"] == sent
    assert again["spec"] == wire(renter()) and again["spec_hash"] != ranked["spec_hash"]
    assert client.get(f"/v1/shares/{ranked['spec_hash']}").status_code == 404
    app = client.app
    assert isinstance(app, FastAPI)
    assert [path for path in app.openapi()["paths"] if "{" in path] == [
        "/v1/areas/{id_or_slug}",
        "/v1/areas/{id_or_slug}/census",
        "/v1/areas/{id_or_slug}/income",
        "/v1/shares/{share_id}",
    ]


def test_a_request_for_no_route_is_told_so_whatever_it_sends(client: TestClient):
    huge = b"x" * 100_000
    nowhere = client.post("/v1/nothing", content=huge, headers={"content-type": "text/plain"})
    wrong_way = client.post("/v1/meta", content=huge, headers={"content-type": "text/plain"})
    right_way = client.post("/v1/rank", content=huge, headers={"content-type": "text/plain"})

    # The body is not what is wrong with the first two, so it is not what is refused.
    assert (nowhere.status_code, nowhere.json()["error"]["code"]) == (404, "not_found")
    assert (wrong_way.status_code, wrong_way.json()["error"]["code"]) == (
        405,
        "method_not_allowed",
    )
    assert wrong_way.headers["allow"] == "GET"
    assert right_way.status_code == 415


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/v1/interpret/"),
        ("POST", "/v1/rank/"),
        ("POST", "/v1/explanations/"),
        ("POST", "/v1/compare/"),
        ("POST", "/v1/places/search/"),
        ("POST", "/v1/shares/"),
        ("GET", "/v1/areas/"),
        ("GET", "/v1/areas/geometry/"),
        ("GET", "/v1/areas/syn-n0001/"),
        ("GET", "/v1/meta/"),
        ("GET", "/healthz/"),
        ("GET", "/v1/"),
        ("GET", "//v1/meta"),
    ],
)
def test_a_path_with_a_slash_too_many_is_no_route_and_is_never_redirected(
    client: TestClient, method: str, path: str
):
    body = {"spec": wire(searching())} if method == "POST" else None
    answered = client.request(method, path, follow_redirects=False, json=body)

    # Never a redirect: it has no envelope, and its `Location` repeats the path.
    assert (answered.status_code, answered.json()["error"]["code"]) == (404, "not_found")
    assert "location" not in answered.headers
    assert answered.json()["meta"]["synthetic"] is True


def test_a_share_is_never_sent_on_to_another_path(client: TestClient):
    made = data(client.post("/v1/shares", json={"spec": wire(searching())}))["share_id"]
    answered = client.get(f"/v1/shares/{made}/", follow_redirects=False)

    assert (answered.status_code, answered.json()["error"]["code"]) == (404, "not_found")
    # A redirect would hand the share's id back in a header, to be logged by whatever reads it.
    assert made not in str(answered.headers) and made not in answered.text


def test_only_a_route_that_is_a_function_of_the_release_may_be_cached(client: TestClient):
    made = data(client.post("/v1/shares", json={"spec": wire(searching())}))

    for path in OF_THE_RELEASE:
        headers = client.get(path).headers
        # A browser may keep the answer, and asks each time whether it still stands.
        assert headers["cache-control"] == "no-cache"
        assert headers["etag"] == tag_of(path)
    kept_out = [client.post(path, json=body) for path, body in posts()]
    kept_out += [client.get(f"/v1/shares/{made['share_id']}"), client.get("/v1/areas/nowhere")]
    for response in kept_out:
        assert response.headers["cache-control"] == "no-store"
        assert "etag" not in response.headers


@pytest.mark.parametrize("held", ["{tag}", "W/{tag}", '"syn-2026-01-01-01", {tag}'])
def test_a_browser_that_holds_the_loaded_release_is_told_that_it_still_stands(
    client: TestClient, held: str
):
    for path in OF_THE_RELEASE:
        answered = client.get(path, headers={"if-none-match": held.format(tag=tag_of(path))})

        assert (answered.status_code, answered.content) == (304, b""), path
        assert answered.headers["etag"] == tag_of(path)
        assert answered.headers["cache-control"] == "no-cache"
        # It has no body to say so in, so the header says it alone.
        assert answered.headers["x-burro-synthetic"] == "true"
        assert "Origin" in answered.headers["vary"]


@pytest.mark.parametrize("held", ['"syn-2026-01-01-01"', "syn-2026-09-23-01", "*", '""', ""])
def test_a_browser_that_holds_anything_else_is_answered_in_full(client: TestClient, held: str):
    for path in OF_THE_RELEASE:
        answered = client.get(path, headers={"if-none-match": held})

        assert answered.status_code == 200 and answered.json()["meta"]["synthetic"] is True
        assert answered.headers["etag"] == tag_of(path)


def test_an_answer_that_stands_is_as_readable_from_the_web_app_as_any_other():
    client = client_for(make_deps(allowed_origins=LISTED))
    held = {"if-none-match": META_BY_RULES}

    allowed = client.get("/v1/meta", headers=held | {"origin": LISTED[0]})
    elsewhere = client.get("/v1/meta", headers=held | {"origin": "https://elsewhere.example"})

    assert allowed.status_code == elsewhere.status_code == 304
    assert about_origins(allowed) == {
        "access-control-allow-origin": LISTED[0],
        "access-control-expose-headers": "X-Burro-Synthetic, X-Burro-Preview, X-Request-Id",
    }
    assert about_origins(elsewhere) == {}
    # It has no body to say what kind of data it is of, so its headers say both.
    for answered in (allowed, elsewhere):
        assert answered.headers["x-burro-synthetic"] == "true"
        assert answered.headers["x-burro-preview"] == "false"


def test_only_an_answer_that_would_be_given_is_said_to_stand(client: TestClient):
    asked = {"if-none-match": LOADED}
    made = data(client.post("/v1/shares", json={"spec": wire(searching())}))

    nowhere = client.get("/v1/areas/nowhere", headers=asked)
    shared = client.get(f"/v1/shares/{made['share_id']}", headers=asked)
    ranked = client.post("/v1/rank", json={"spec": wire(searching())}, headers=asked)

    # An area the release lacks is still not found, and what is no function
    # of the release alone is answered in full each time.
    assert (nowhere.status_code, nowhere.json()["error"]["code"]) == (404, "area_not_found")
    assert shared.status_code == ranked.status_code == 200
    assert "etag" not in shared.headers and "etag" not in ranked.headers


# Origins.

WEB_APP = "http://localhost:3000"
LISTED = ("https://burro.example", "https://staging.burro.example:8443")
ELSEWHERE = [
    "https://elsewhere.example",
    "http://localhost:3001",
    "http://localhost:30000",
    "https://localhost:3000",
    "http://LOCALHOST:3000",
    "http://localhost:3000.elsewhere.example",
    "http://localhost:3000/",
    " http://localhost:3000",
    "http://localhost",
    "localhost:3000",
    "null",
    "*",
    "",
]
PREFLIGHT = {
    "access-control-request-method": "POST",
    "access-control-request-headers": "content-type",
}


class Unkept:
    """A call log that cannot keep a record, so that a route lets an error fall."""

    def add(self, record: object) -> None:
        raise RuntimeError

    def records(self, now: object) -> tuple[()]:
        return ()


def called_from(origin: str, deps: Deps | None = None) -> list[Any]:
    """One call to every route, and one of every kind of refusal, as a browser makes them."""
    sent = {"origin": origin}
    deps = deps or make_deps()
    huge = b'{"text": "' + b"x" * 20_000 + b'"}'
    as_json = sent | {"content-type": "application/json"}
    with client_for(deps) as client, client_for(replace(deps, calls=Unkept())) as broken:
        made = client.post("/v1/shares", json={"spec": wire(searching())}).json()["data"]
        return [
            *(client.post(path, json=body, headers=sent) for path, body in posts()),
            *(client.get(path, headers=sent) for path in (*GETS, "/healthz")),
            client.get(f"/v1/shares/{made['share_id']}", headers=sent),
            client.post("/v1/rank", json={"spec": "no"}, headers=sent),
            client.post("/v1/rank", content=b"{", headers=as_json),
            client.post("/v1/rank", content=b"{}", headers=sent | {"content-type": "text/plain"}),
            client.post("/v1/interpret", content=huge, headers=as_json),
            client.get("/v1/areas/nowhere", headers=sent),
            client.get("/v1/nothing", headers=sent),
            client.get("/v1/meta/", headers=sent),
            client.delete("/v1/meta", headers=sent),
            broken.post("/v1/interpret", json={"text": "somewhere leafy"}, headers=sent),
        ]


def about_origins(response: Any) -> dict[str, str]:
    return {k: v for k, v in response.headers.items() if k.startswith("access-control-")}


def test_a_browser_may_call_from_the_web_app_on_this_machine_unless_told_otherwise():
    answered = called_from(WEB_APP)

    assert [r.status_code for r in answered][-9:] == [422, 400, 415, 413, 404, 404, 404, 405, 500]
    for response in answered:
        # An error is as readable from the web app as an answer is.
        assert about_origins(response) == {
            "access-control-allow-origin": WEB_APP,
            "access-control-expose-headers": "X-Burro-Synthetic, X-Burro-Preview, X-Request-Id",
        }


@pytest.mark.parametrize("origin", LISTED)
def test_an_origin_on_the_list_is_allowed(origin: str):
    for response in called_from(origin, make_deps(allowed_origins=LISTED)):
        assert response.headers["access-control-allow-origin"] == origin
        # The answer depends on who asked, and whatever keeps a copy must know it.
        assert "Origin" in response.headers["vary"]


@cache
def answered_when_allowed() -> tuple[int, ...]:
    """How each call is answered from an origin on the list. Worked out once: it never changes."""
    allowed = called_from(LISTED[0], make_deps(allowed_origins=LISTED))
    assert {about_origins(r)["access-control-allow-origin"] for r in allowed} == {LISTED[0]}
    return tuple(response.status_code for response in allowed)


@pytest.mark.parametrize("origin", [*ELSEWHERE, WEB_APP, *(o.upper() for o in LISTED)], ids=repr)
def test_an_origin_off_the_list_is_not(origin: str):
    asked = called_from(origin, make_deps(allowed_origins=LISTED))

    for response, allowed in zip(asked, answered_when_allowed(), strict=True):
        # It is answered as any call is, and the browser is given nothing that
        # lets the page read the answer: no origin, and never every origin.
        assert about_origins(response) == {}
        assert response.status_code == allowed
        assert "Origin" in response.headers["vary"]


def test_a_call_that_names_no_origin_is_answered_as_before(client: TestClient):
    for response in (client.get("/v1/meta"), client.post("/v1/rank", json=posts()[1][1])):
        assert response.status_code == 200 and about_origins(response) == {}
        assert "Origin" in response.headers["vary"]


@pytest.mark.parametrize("path", ["/v1/rank", "/v1/interpret", "/v1/meta", "/v1/areas/syn-n0001"])
def test_a_browser_that_asks_first_is_told_what_it_may_send(path: str):
    client = client_for(make_deps(allowed_origins=LISTED))
    asked = client.options(path, headers=PREFLIGHT | {"origin": LISTED[1]})

    assert (asked.status_code, asked.content) == (204, b"")
    assert about_origins(asked) == {
        "access-control-allow-origin": LISTED[1],
        "access-control-allow-methods": "GET, POST",
        "access-control-allow-headers": "Content-Type",
        "access-control-max-age": "600",
        "access-control-expose-headers": "X-Burro-Synthetic, X-Burro-Preview, X-Request-Id",
    }
    assert asked.headers["x-burro-synthetic"] == "true" and "Origin" in asked.headers["vary"]


@pytest.mark.parametrize("origin", [*ELSEWHERE, WEB_APP], ids=repr)
def test_a_browser_that_asks_first_from_anywhere_else_is_told_nothing(origin: str):
    client = client_for(make_deps(allowed_origins=LISTED))
    asked = client.options("/v1/rank", headers=PREFLIGHT | {"origin": origin})
    plain = client.options("/v1/rank", headers={"origin": LISTED[0]})

    # Not a question about origins at all, then: a method the route does not take.
    for response in (asked, plain):
        assert (response.status_code, response.json()["error"]["code"]) == (
            405,
            "method_not_allowed",
        )
    assert about_origins(asked) == {}


def test_no_answer_allows_every_origin_or_asks_for_a_cookie():
    deps = make_deps(allowed_origins=LISTED)
    asked = client_for(deps).options("/v1/rank", headers=PREFLIGHT | {"origin": LISTED[0]})

    for response in (*called_from(LISTED[0], deps), *called_from("*", deps), asked):
        assert "access-control-allow-credentials" not in response.headers
        assert "*" not in about_origins(response).values()
        assert "set-cookie" not in response.headers


# Route 1.


@pytest.mark.parametrize("text", ["", "   ", "\n\t ", "x" * 601])
def test_a_prompt_with_nothing_in_it_is_refused_before_a_model_is_asked(text: str):
    model = FakeModelClient(model_output())
    asked = ModelInterpreter(model, model=MODEL, max_tokens=512, timeout_s=1.0)
    client = client_for(make_deps(interpreter=asked, model_id=MODEL))

    refused = client.post("/v1/interpret", json={"text": text})

    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "invalid_text")
    # A line of spaces is an empty line. It must not cost a call to a model.
    assert model.calls == []


def test_a_sentence_becomes_edits_and_the_reducer_applies_them(client: TestClient):
    text = "Renting a 2 bed for £2,100 a month, no more than 35 minutes to Cindermoor Works"
    found = data(client.post("/v1/interpret", json={"text": text}))

    start = default_for(release(), Tenure.RENT)
    expected = RuleInterpreter().interpret(InterpretRequest(text, start, release()))
    reduced = apply(start, expected.operations, release())
    assert found["operations"] == expected.operations.model_dump(mode="json")
    assert found["spec"] == wire(reduced.spec)
    assert found["spec_hash"] == spec_hash(reduced.spec)
    assert found["spec"]["budget"]["amount"] == 2100
    assert found["spec"]["commutes"] == [
        {
            "place_id": WORKS,
            "mode": "pt",
            "max_minutes": 35,
            "strictness": "hard",
            "provenance": "stated",
        }
    ]
    assumed = {"code": "mode", "group": "commute_ops", "index": 0, "word": ""}
    assert assumed in found["assumptions"]


def test_each_edit_says_which_words_of_the_text_it_rests_on(client: TestClient):
    text = "Renting a 2 bed for £2,100 a month, no more than 35 minutes to Cindermoor Works, leafy"
    found = data(client.post("/v1/interpret", json={"text": text}))

    start = default_for(release(), Tenure.RENT)
    expected = RuleInterpreter().interpret(InterpretRequest(text, start, release()))
    assert found["rests_on"] == [rests.model_dump(mode="json") for rests in expected.rests_on]
    # An edit of several parts has an entry for each, in the order they stand.
    assert [(r["group"], r["index"], text[r["start"] : r["end"]]) for r in found["rests_on"]] == [
        ("budget_ops", 0, "Renting"),
        ("budget_ops", 0, "2 bed"),
        ("budget_ops", 0, "£2,100"),
        ("commute_ops", 0, "no more than 35 minutes to Cindermoor Works"),
        ("tag_ops", 0, "leafy"),
    ]
    # Every entry points at an edit that was served, and every edit is pointed at.
    served = {(g, i) for g, edits in found["operations"].items() for i in range(len(edits))}
    assert {(r["group"], r["index"]) for r in found["rests_on"]} == served


@pytest.mark.parametrize(
    "text",
    [
        "leafy",
        "   leafy",
        "\n\t leafy \n",
        "\N{NO-BREAK SPACE}\N{IDEOGRAPHIC SPACE}leafy\N{EM SPACE}",
    ],
)
def test_where_the_words_stand_is_counted_in_the_text_as_it_was_sent(client: TestClient, text: str):
    found = data(client.post("/v1/interpret", json={"text": text}))

    # The text is read without the space around it, and a caller does not
    # have to know that: the offsets are into what it sent, in code points.
    [rests] = found["rests_on"]
    assert text[rests["start"] : rests["end"]] == "leafy"
    assert (rests["group"], rests["index"]) == ("tag_ops", 0)
    assert [edit["tag_id"] for edit in found["operations"]["tag_ops"]] == ["leafy"]
    assert found["suggestions"] == found["unread"] == []


@pytest.mark.parametrize(
    "text",
    [
        "Pubs are so noisy",
        "   Pubs are so noisy",
        "\n\t Pubs are so noisy \n",
        # A sentence the reader makes nothing of, with characters that are two
        # units long in UTF-16, and then one it notices things in.
        "  \N{DECIDUOUS TREE}\N{DECIDUOUS TREE} trees!\nPubs are so noisy  ",
        "caf\N{LATIN SMALL LETTER E WITH ACUTE}s? \N{REGIONAL INDICATOR SYMBOL LETTER G}"
        "\N{REGIONAL INDICATOR SYMBOL LETTER B}!\nPubs are so noisy",
    ],
)
def test_where_what_was_noticed_stands_is_counted_in_the_text_as_it_was_sent(
    client: TestClient, text: str
):
    found = data(client.post("/v1/interpret", json={"text": text}))

    def words(spans: list[dict[str, int]]) -> list[str]:
        return [text[span["start"] : span["end"]] for span in spans]

    noticed = {s["target"]: words(s["spans"]) for s in found["suggestions"]}
    assert noticed["feature:venue_evening_per_homes"] == ["Pubs"]
    assert noticed["feature:noise_exposure"] == ["noisy"]
    assert words(found["unread"])[-1] == "are so"
    # Nothing was applied, so no edit rests on anything.
    assert found["rests_on"] == [] and found["applied"] == []


def test_an_interpreter_cannot_point_outside_the_text_or_at_an_edit_it_did_not_make():
    text = "somewhere leafy"

    class Wild:
        name = InterpreterName.MODEL

        def interpret(self, request: InterpretRequest) -> InterpretResult:
            read = RuleInterpreter().interpret(request)
            [rests] = read.rests_on
            wild = [
                rests.replace(start=0, end=len(text) + 1),
                rests.replace(start=-1, end=3),
                rests.replace(start=5, end=5),
                rests.replace(start=9, end=4),
                rests.replace(index=1),
                rests.replace(group=OpsGroup.AREA),
                rests,
            ]
            return read.replace(rests_on=tuple(wild), interpreter=self.name)

    client = client_for(make_deps(interpreter=Wild(), model_id=MODEL))
    found = data(client.post("/v1/interpret", json={"text": f"  {text}"}))

    assert [(r["start"], r["end"]) for r in found["rests_on"]] == [(12, 17)]


def test_an_interpreter_cannot_offer_or_leave_unread_what_is_outside_the_text():
    text = "Pubs are so noisy"
    beyond = [(0, len(text) + 1), (-1, 3), (5, 5), (9, 4)]

    class Wild:
        name = InterpreterName.MODEL

        def interpret(self, request: InterpretRequest) -> InterpretResult:
            read = RuleInterpreter().interpret(request)
            wild = tuple(Span(start=start, end=end) for start, end in beyond)
            pubs, noise = read.suggestions
            offered = (pubs.replace(spans=(*wild, *pubs.spans)), noise.replace(spans=wild))
            return read.replace(
                suggestions=offered, unread=(*wild, *read.unread), interpreter=self.name
            )

    client = client_for(make_deps(interpreter=Wild(), model_id=MODEL))
    found = data(client.post("/v1/interpret", json={"text": f"  {text}"}))

    # A suggestion that points at nothing in the text is not served at all.
    assert [(s["target"], s["spans"]) for s in found["suggestions"]] == [
        ("feature:venue_evening_per_homes", [{"start": 2, "end": 6}])
    ]
    assert found["unread"] == [{"start": 7, "end": 13}]


def test_a_second_sentence_edits_the_spec_that_is_sent_with_it(client: TestClient):
    first = data(client.post("/v1/interpret", json={"text": "work at Cindermoor Works"}))
    second = data(
        client.post("/v1/interpret", json={"text": "much more leafy", "spec": first["spec"]})
    )

    assert [c["place_id"] for c in second["spec"]["commutes"]] == [WORKS]
    # A thing named for the first time is worth a half, however it is asked for.
    assert second["spec"]["tags"] == [
        {"tag_id": "leafy", "weight": 0.5, "toward": "high", "provenance": "stated"}
    ]


def test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served(
    client: TestClient,
):
    found = data(client.post("/v1/interpret", json={"text": "leafy, not too many students"}))

    assert found["status"] == "policy_redirect" and found["notice"] == "neutral_places"
    assert found["notice_text"].startswith("Burro ranks places by what is there")
    assert [edit["tag_id"] for edit in found["operations"]["tag_ops"]] == ["leafy"]
    assert found["operations"]["weight_ops"] == []


def test_a_wish_for_safety_never_weights_crime_without_being_asked(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "somewhere safe"}))

    # "Safe" names no crime, so nothing is applied and nothing is turned away.
    assert (found["status"], found["operations"], found["rejected"]) == ("suggest", NO_EDITS, [])
    assert not [w for w in found["spec"]["weights"] if w["feature_id"].startswith("crime")]
    # Recorded crime is offered by its name, with what Burro cannot say of a place.
    assert [(s["target"], s["choices"][0]["label"]) for s in found["suggestions"]] == [
        ("feature:crime_violence_robbery", "Less recorded violence and robbery"),
        ("feature:crime_burglary_theft", "Less recorded burglary and theft"),
    ]
    for offered in found["suggestions"]:
        assert offered["note"].startswith("Burro cannot say how safe a place is.")
        assert "Recorded crime depends on what is reported" in offered["note"]
    # To press one is to ask for it by name, and then it counts.
    pressed = found["suggestions"][0]["choices"][0]["operations"]
    ranked = data(client.post("/v1/rank", json={"spec": found["spec"], "operations": pressed}))
    assert ranked["rejected"] == []
    assert [w["feature_id"] for w in ranked["spec"]["weights"] if w["provenance"] == "ui_edit"] == [
        "crime_violence_robbery"
    ]


NO_EDITS: dict[str, list[dict[str, Any]]] = {
    f"{group}_ops": [] for group in ("budget", "commute", "weight", "tag", "area", "setting")
}
MONEY_AND_WORK = (
    "I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works."
)
THE_WORKS = {"place_id": WORKS, "name": "Cindermoor Works", "kind": "district"}


def test_a_plain_prompt_about_money_and_work_is_read_in_full(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": MONEY_AND_WORK}))

    assert (found["status"], found["unmet"]) == ("ok", [])
    assert found["suggestions"] == found["unread"] == found["rejected"] == []
    held = found["spec"]["budget"]
    assert (found["spec"]["tenure"], held["amount"], held["segment"]) == ("rent", 1500, "bed_1")
    assert [c["place_id"] for c in found["spec"]["commutes"]] == [WORKS]
    # The place is given by the release's own name, so nothing reads "Place 1".
    assert found["places"] == [THE_WORKS]


def test_a_prompt_that_is_not_plain_applies_nothing_and_offers_what_was_noticed(
    client: TestClient,
):
    text = "Pubs are so noisy"
    start = wire(default_for(release(), Tenure.RENT))
    found = data(client.post("/v1/interpret", json={"text": text}))

    assert (found["status"], found["unmet"], found["notice"]) == ("suggest", ["other"], "none")
    # Not even a guess at which way: the spec is the one a search starts from.
    assert found["operations"] == NO_EDITS and found["spec"] == start
    assert found["applied"] == found["rests_on"] == found["places"] == []
    assert found["unread"] == [{"start": 5, "end": 11}]
    pubs, noise = found["suggestions"]
    assert (pubs["target"], pubs["label"]) == ("feature:venue_evening_per_homes", "Pubs and bars")
    assert pubs["spans"] == [{"start": 0, "end": 4}]
    assert [(c["direction"], c["label"]) for c in pubs["choices"]] == [
        ("more", "More pubs and bars"),
        ("less", "Fewer pubs and bars"),
        ("ignore", "Skip"),
    ]
    # The rules never guess which way a thing was meant.
    assert pubs["does"] == "Pubs and bars: more, or fewer?"
    assert not any(c["guess"] for offer in found["suggestions"] for c in offer["choices"])
    assert (noise["target"], noise["label"]) == ("feature:noise_exposure", "Less transport noise")
    assert [c["direction"] for c in noise["choices"]] == ["less", "ignore"]
    for suggestion in found["suggestions"]:
        *chosen, ignored = suggestion["choices"]
        assert ignored["operations"] == NO_EDITS
        for choice in chosen:
            edits = [edit for group in choice["operations"].values() for edit in group]
            # The person pressed it, so the edit is a control's and no reading.
            assert [edit["provenance"] for edit in edits] == ["ui_edit"]


def test_a_choice_that_is_pressed_is_an_edit_that_route_2_takes_as_it_is(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "Pubs are so noisy"}))
    [fewer] = [c for c in found["suggestions"][0]["choices"] if c["direction"] == "less"]

    ranked = data(
        client.post("/v1/rank", json={"spec": found["spec"], "operations": fewer["operations"]})
    )

    assert ranked["applied"] == [{"group": "weight_ops", "index": 0, "changed": True}]
    [pubs] = [w for w in ranked["spec"]["weights"] if w["feature_id"] == "venue_evening_per_homes"]
    assert (pubs["direction"], pubs["provenance"]) == ("less", "ui_edit")
    assert ranked["ranked"] and ranked["rejected"] == []


# Prompts that are not plain, of which something is noticed. Each was read
# wrongly, or led nowhere, when the first slice was walked.
OFFERED = (
    "Pubs are so noisy",
    "gritty but safe",
    "I am new here. My budget is about \N{POUND SIGN}2,000 a month for a two bed flat.",
    "Happy anywhere as long as it is under \N{POUND SIGN}450k",
    "30 minutes to Pellam Cross by bike is too long",
    "I love Cindermoor",
    "My partner works at Pellam Infirmary",
    "near a leisure centre",
    "a sense of community",
    "I want a big garden",
    "street character",
    "pace",
)


def test_every_choice_that_is_offered_is_an_edit_that_route_2_applies(client: TestClient):
    labels: list[str] = []
    for text in OFFERED:
        found = data(client.post("/v1/interpret", json={"text": text}))
        assert found["operations"] == NO_EDITS and found["suggestions"], text
        for offer in found["suggestions"]:
            *choices, ignored = offer["choices"]
            assert choices and ignored["operations"] == NO_EDITS, text
            for choice in choices:
                pressed = {"spec": found["spec"], "operations": choice["operations"], "limit": 1}
                ranked = data(client.post("/v1/rank", json=pressed))
                # Nothing that is offered is turned away, and each changes the search.
                assert ranked["rejected"] == [], (text, choice["label"])
                assert [edit["changed"] for edit in ranked["applied"]] == [True], choice["label"]
                labels.append(choice["label"])
            labels.append(offer["does"])
    # What an offer says it would do, and what each way of it is called, say
    # all that it holds: what is counted, how far, which tenure.
    assert {
        "Towards Gritty, counting recorded crime",
        "Less recorded violence and robbery",
        "Set a budget of \N{POUND SIGN}2,000 a month.",
        "Look for a 2-bedroom home.",
        "Set a budget of \N{POUND SIGN}450,000 to buy.",
        "Add a journey to Pellam Cross: at most 30 minutes, by public transport.",
        "Look only in Cindermoor",
        "Leave it out of the results",
        "Towards Calm",
    } <= set(labels)


@pytest.mark.parametrize(
    ("text", "note"),
    [
        ("somewhere safe", "Burro cannot say how safe a place is."),
        ("near a leisure centre", "Burro cannot tell a swimming pool or a leisure centre"),
        ("a sense of community", "Burro cannot measure whether neighbours know each other."),
        ("I want a big garden", "Burro cannot see whether one home has a garden."),
        # The name the scale had. It names no end, so it is offered with both.
        ("street character", "Gritty counts recorded criminal damage"),
    ],
)
def test_what_burro_cannot_do_is_said_beside_what_it_offers_in_its_place(
    client: TestClient, text: str, note: str
):
    found = data(client.post("/v1/interpret", json={"text": text}))

    assert (found["status"], found["operations"]) == ("suggest", NO_EDITS)
    assert found["suggestions"] and all(s["note"].startswith(note) for s in found["suggestions"])
    # Most things that are noticed need nothing said of them.
    plain = data(client.post("/v1/interpret", json={"text": "Pubs are so noisy"}))
    assert [s["note"] for s in plain["suggestions"]] == ["", ""]


@pytest.mark.parametrize(
    ("text", "unmet"),
    [("cheap", "affordability_verdict"), ("somewhere with low rent", "affordability_verdict")],
)
def test_a_verdict_burro_does_not_give_is_heard_and_nothing_is_offered_for_it(
    client: TestClient, text: str, unmet: str
):
    found = data(client.post("/v1/interpret", json={"text": text}))

    assert (found["status"], found["unmet"]) == ("ok", [unmet])
    assert found["operations"] == NO_EDITS and found["suggestions"] == found["unread"] == []


def test_an_everyday_hedge_is_read_as_a_word_of_degree(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "somewhere leafy and fairly quiet"}))

    # "Fairly" made the whole prompt a question, where "a bit" was read.
    assert (found["status"], found["unmet"], found["unread"]) == ("ok", [], [])
    assert [(e["tag_id"], e["step"]) for e in found["operations"]["tag_ops"]] == [
        ("leafy", "up_large"),
        ("quiet_residential", "up_small"),
    ]
    assert [tag["provenance"] for tag in found["spec"]["tags"]] == ["stated", "stated"]


@pytest.mark.parametrize(
    ("text", "mode", "strictness"),
    [
        ("I work at Cindermoor Works. A 40 minute commute on foot.", "walk", "soft"),
        ("I work at Cindermoor Works, a 35 minute commute by bike", "cycle", "soft"),
        ("I work at Cindermoor Works, no more than 35 minutes", "pt", "hard"),
    ],
)
def test_minutes_said_apart_from_a_place_keep_how_they_are_travelled_and_their_limit(
    client: TestClient, text: str, mode: str, strictness: str
):
    found = data(client.post("/v1/interpret", json={"text": text}))

    [journey] = found["spec"]["commutes"]
    assert (found["status"], found["unread"], found["places"]) == ("ok", [], [THE_WORKS])
    assert (journey["mode"], journey["strictness"]) == (mode, strictness)


@pytest.mark.parametrize(
    "text",
    [
        "I don't want pubs or restaurants nearby",
        "I don't want nightlife or pubs on my doorstep",
        "no pubs or nightlife nearby",
        "avoid pubs and restaurants nearby",
    ],
)
def test_the_last_thing_of_a_turned_list_is_never_raised(client: TestClient, text: str):
    found = data(client.post("/v1/interpret", json={"text": text}))

    # It was applied as plain, with the last thing of the list raised.
    assert found["status"] in ("ok", "suggest") and found["rejected"] == []
    raised = [w for w in found["spec"]["weights"] if w["provenance"] == "stated"]
    assert {w["direction"] for w in raised} <= {"less"}
    assert {tag["toward"] for tag in found["spec"]["tags"]} <= {"low"}
    assert (found["status"] == "suggest") is (found["operations"] == NO_EDITS)


def test_what_nothing_was_made_of_is_the_whole_text_when_nothing_was_noticed(client: TestClient):
    text = "boozers on every corner would finish me off"
    found = data(client.post("/v1/interpret", json={"text": text}))

    assert (found["status"], found["unmet"]) == ("ok", ["other"])
    assert found["suggestions"] == [] and found["operations"] == NO_EDITS
    assert found["unread"] == [{"start": 0, "end": len(text)}]


@pytest.mark.parametrize(
    ("text", "changed"),
    [
        ("Somewhere leafy with lots of students like me", True),
        # Nothing is applied of a prompt that is not plain, whatever was noticed in it.
        ("My street is leafy, with lots of students like me", False),
        ("lots of students like me", False),
        # A wish for fewer of those Burro counts is a wish about people as any other is.
        ("Somewhere leafy, with fewer young professionals", True),
        ("no families", False),
    ],
)
def test_the_notice_says_the_rest_was_applied_only_where_something_was(
    client: TestClient, text: str, changed: bool
):
    found = data(client.post("/v1/interpret", json={"text": text}))

    assert (found["status"], found["notice"]) == ("policy_redirect", "neutral_places")
    assert any(edit["changed"] for edit in found["applied"]) is changed
    assert found["notice_text"] == notice_text(Notice(found["notice"]), changed)
    assert found["notice_text"].endswith(
        "The rest of your search has been applied."
        if changed
        else "Nothing you typed has changed your search."
    )


def test_a_tenure_that_is_said_is_the_persons_own_whether_or_not_it_moves(client: TestClient):
    start = default_for(release(), Tenure.RENT)
    found = data(client.post("/v1/interpret", json={"text": "Renting a one bed flat"}))

    # A search starts from renting. Said, it is no longer assumed.
    assert wire(start)["tenure_from"] == "default"
    assert (found["spec"]["tenure"], found["spec"]["tenure_from"]) == ("rent", "stated")
    assert found["applied"] == [{"group": "budget_ops", "index": 0, "changed": True}]
    assert found["spec_hash"] == spec_hash(start)


def test_a_status_the_reader_gives_is_one_a_call_can_be_recorded_with():
    deps = make_deps()
    client = client_for(deps)
    for text in ("Pubs are so noisy", "leafy", "I work at Pellam", "leafy, no students"):
        assert client.post("/v1/interpret", json={"text": text}).status_code == 200

    said = [record.status.value for record in deps.calls.records(NOW)]
    assert said == ["suggest", "ok", "clarify", "policy_redirect"]


# The places of a spec, by name.


def test_every_place_of_a_spec_that_is_returned_is_given_by_name(client: TestClient):
    spec = renter(commutes=(commute(SCHOOL, 30), commute(WORKS, 40)))
    sent = {"spec": wire(spec)}
    school = {"place_id": SCHOOL, "name": "Alderwick Primary School", "kind": "school"}
    station = {"place_id": SCHOOL_COARSE, "name": "Eskerfold", "kind": "station"}

    read = data(client.post("/v1/interpret", json=sent | {"text": "leafy"}))
    ranked = data(client.post("/v1/rank", json=sent))
    exact = data(client.post("/v1/shares", json=sent | {"exact_destinations": True}))
    coarse = data(client.post("/v1/shares", json=sent))
    opened = data(client.get(f"/v1/shares/{coarse['share_id']}"))

    # One for each journey of the spec that is returned, in the spec's order.
    for found in (read, ranked, exact):
        assert found["places"] == [THE_WORKS, school]
        assert [p["place_id"] for p in found["places"]] == [
            c["place_id"] for c in found["spec"]["commutes"]
        ]
    # A share names the place that stands in, which is the one it stores.
    assert coarse["places"] == opened["places"] == [station, THE_WORKS]
    assert data(client.post("/v1/rank", json={"spec": wire(renter())}))["places"] == []


def test_a_place_is_named_as_the_release_names_it_and_never_as_it_was_typed(client: TestClient):
    found = data(client.post("/v1/interpret", json={"text": "i work at CINDERMOOR   works"}))
    searched = data(client.post("/v1/places/search", json={"q": "cindermoor works"}))["places"]

    assert found["places"] == [THE_WORKS]
    assert searched[0]["name"] == found["places"][0]["name"]


# Route 2.


def test_ranking_over_the_wire_is_the_ranking_core_gives(client: TestClient):
    spec = searching()
    found = data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 5}))

    expected = rank(spec, release())
    assert found["spec_hash"] == expected.spec_hash == spec_hash(spec)
    assert found["scores"] == [
        {
            "area_id": area.area_id,
            "score": area.score,
            "counted": area.counted,
            "present": area.present,
        }
        for area in expected.ranked
    ]
    assert found["ranked"] == [area.model_dump(mode="json") for area in expected.ranked[:5]]
    assert found["unranked"] == [u.model_dump(mode="json") for u in expected.unranked]
    assert found["empty_spec"] is False
    every = found["scores"] + found["filtered"] + found["unranked"]
    assert len({row["area_id"] for row in every}) == 24


def test_a_ranking_says_how_many_areas_are_ranked_and_how_many_of_them_are_listed(
    client: TestClient,
):
    # Journeys alone ask nothing of the place itself, so every rankable area is ranked.
    spec = renter(commutes=(commute(),), weights=(), tags=())
    expected = len(rank(spec, release()).ranked)
    assert expected == 22
    sent = {"spec": wire(spec)}
    as_usual = data(client.post("/v1/rank", json=sent))
    a_few = data(client.post("/v1/rank", json=sent | {"limit": 5}))
    every = data(client.post("/v1/rank", json=sent | {"limit": 100}))
    made = data(client.post("/v1/shares", json=sent | {"exact_destinations": True}))
    opened = data(client.get(f"/v1/shares/{made['share_id']}"))

    # The list stopped at 20 and nothing said that two areas stood below it.
    for found, listed in ((as_usual, 20), (a_few, 5), (every, 22), (opened, 20)):
        assert (found["areas_ranked"], found["areas_listed"]) == (expected, listed)
        assert len(found["scores"]) == expected and len(found["ranked"]) == listed
    # Where an area is left out or listed apart, it is not among those ranked.
    firm = data(client.post("/v1/rank", json={"spec": wire(searching(budget=budget(900, True)))}))
    assert firm["filtered"] and firm["unranked"]
    assert firm["areas_ranked"] == len(firm["scores"]) == firm["areas_listed"] < 20
    assert firm["areas_ranked"] + len(firm["filtered"]) + len(firm["unranked"]) == 24


def test_the_same_request_ranks_the_same_every_time(client: TestClient):
    body = {"spec": wire(searching())}

    first = client.post("/v1/rank", json=body).json()
    assert all(client.post("/v1/rank", json=body).json() == first for _ in range(5))


def test_slider_and_chat_edits_reach_the_same_spec(client: TestClient):
    said = data(client.post("/v1/interpret", json={"text": "quiet is essential"}))
    slid = data(
        client.post(
            "/v1/rank",
            json={
                "spec": wire(default_for(release(), Tenure.RENT)),
                "operations": {
                    "budget_ops": [],
                    "commute_ops": [],
                    "weight_ops": [],
                    "tag_ops": [
                        {
                            "action": "set",
                            "tag_id": "quiet_residential",
                            "value": 1.0,
                            "step": "none",
                            "toward": "default",
                            "provenance": "ui_edit",
                        }
                    ],
                    "area_ops": [],
                    "setting_ops": [],
                },
            },
        )
    )

    # Provenance says who asked. The spec that is ranked is the same.
    assert slid["spec_hash"] == said["spec_hash"]
    assert slid["applied"] == [{"group": "tag_ops", "index": 0, "changed": True}]


def towards(tag_id: str, toward: str, value: float = 0.5) -> dict[str, Any]:
    edit = {"action": "set", "tag_id": tag_id, "value": value, "step": "none"}
    return NO_EDITS | {"tag_ops": [edit | {"toward": toward, "provenance": "ui_edit"}]}


def names_of(found: dict[str, Any], first: int) -> list[str]:
    named = {area.area_id: area.name for area in release().neighbourhoods}
    return [named[score["area_id"]] for score in found["scores"][:first]]


def test_a_scale_is_ranked_towards_the_end_that_is_asked_for_and_can_be_turned(
    client: TestClient,
):
    said = data(client.post("/v1/interpret", json={"text": "not buzzy"}))
    calm = data(client.post("/v1/rank", json={"spec": said["spec"]}))
    turned = data(
        client.post("/v1/rank", json={"spec": said["spec"], "operations": towards("pace", "high")})
    )

    [asked] = said["spec"]["tags"]
    assert (asked["tag_id"], asked["toward"]) == ("pace", "low")
    assert "Lantern Yard" not in names_of(calm, 10)
    # To turn a scale is one edit, and it changes the spec though no weight moves.
    assert turned["applied"] == [{"group": "tag_ops", "index": 0, "changed": True}]
    assert [(t["tag_id"], t["toward"], t["weight"]) for t in turned["spec"]["tags"]] == [
        ("pace", "high", asked["weight"])
    ]
    assert names_of(turned, 3) == ["Pellam Cross", "Tallowgate", "Lantern Yard"]
    assert turned["spec_hash"] != calm["spec_hash"]


def test_an_end_that_is_left_out_of_a_spec_is_the_high_end_and_is_always_returned(
    client: TestClient,
):
    leafy = {"tag_id": "leafy", "weight": 0.5, "provenance": "stated"}
    sent = wire(renter()) | {"tags": [leafy]}

    found = data(client.post("/v1/rank", json={"spec": sent}))

    assert found["spec"]["tags"] == [leafy | {"toward": "high"}]
    # A spec published before a vibe had ends keeps its hash.
    high = TagWeight(tag_id=TagId.LEAFY, weight=0.5, provenance=Provenance.STATED)
    assert high.toward is Toward.HIGH and found["spec_hash"] == spec_hash(renter(tags=(high,)))


def test_an_edit_to_a_vibe_must_say_which_end_and_a_one_way_vibe_has_one(client: TestClient):
    spec = wire(renter())
    unsaid = towards("pace", "high")
    del unsaid["tag_ops"][0]["toward"]

    refused = client.post("/v1/rank", json={"spec": spec, "operations": unsaid})
    low = data(client.post("/v1/rank", json={"spec": spec, "operations": towards("leafy", "low")}))
    held = wire(renter()) | {
        "tags": [{"tag_id": "leafy", "weight": 0.5, "toward": "low", "provenance": "stated"}]
    }
    against = client.post("/v1/rank", json={"spec": held})

    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "invalid_operations")
    assert refused.json()["error"]["fields"] == [
        {"path": "operations.tag_ops[0].toward", "problem": "missing"}
    ]
    assert low["rejected"] == [{"group": "tag_ops", "index": 0, "reason": "direction_not_allowed"}]
    assert against.json()["error"]["fields"] == [
        {"path": "spec.tags[0].toward", "problem": "direction_not_allowed"}
    ]


@pytest.mark.parametrize("retired", ["buzzy", "evening_venues", "historic_character", "waterside"])
def test_a_vibe_that_was_retired_is_no_longer_a_vibe(client: TestClient, retired: str):
    held = {"tag_id": retired, "weight": 0.5, "provenance": "stated"}
    edits = towards("pace", "high")
    edits["tag_ops"][0]["tag_id"] = retired

    in_a_spec = client.post("/v1/rank", json={"spec": wire(renter()) | {"tags": [held]}})
    in_an_edit = client.post("/v1/rank", json={"spec": wire(renter()), "operations": edits})

    assert (in_a_spec.status_code, in_a_spec.json()["error"]["code"]) == (422, "invalid_spec")
    assert in_a_spec.json()["error"]["fields"] == [
        {"path": "spec.tags[0].tag_id", "problem": "not_allowed"}
    ]
    assert in_an_edit.json()["error"]["code"] == "invalid_operations"
    assert retired not in in_a_spec.text + in_an_edit.text


def test_a_vibe_the_release_does_not_carry_cannot_be_ranked_on():
    # A release that holds no recorded crime carries every vibe but Gritty.
    client = client_for(make_deps(release=built_from_land_use()))
    other = TagId.STREET_CHARACTER
    assert other not in {vibe.tag_id for vibe in built_from_land_use().vibes}
    held = TagWeight(tag_id=other, weight=0.5, provenance=Provenance.STATED)

    in_a_spec = client.post("/v1/rank", json={"spec": wire(renter(tags=(held,)))})
    edits = towards(other.value, "high")
    in_an_edit = data(client.post("/v1/rank", json={"spec": wire(renter()), "operations": edits}))

    assert in_a_spec.json()["error"]["fields"] == [
        {"path": "spec.tags[0].tag_id", "problem": "not_in_release"}
    ]
    assert in_an_edit["rejected"] == [{"group": "tag_ops", "index": 0, "reason": "not_in_release"}]


def test_every_result_shows_where_it_sits_on_the_vibes_that_were_asked_for(client: TestClient):
    pace = TagWeight(tag_id=TagId.PACE, weight=0.5, toward=Toward.LOW, provenance=Provenance.STATED)
    leafy = TagWeight(tag_id=TagId.LEAFY, weight=0.8, provenance=Provenance.STATED)
    spec = renter(tags=(pace, leafy))
    found = data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 100}))

    expected = {area.area_id: area for area in rank(spec, release()).ranked}
    carried = {vibe.tag_id.value for vibe in release().vibes}
    for area in found["ranked"]:
        strip = area["strip"]
        assert strip == [m.model_dump(mode="json") for m in expected[area["area_id"]].strip]
        assert 1 <= len(strip) <= 6 and {mark["tag_id"] for mark in strip} <= carried
        asked = [(mark["tag_id"], mark["toward"]) for mark in strip if mark["asked"]]
        # Heaviest first. A vibe the area cannot be placed on is left out.
        assert asked in ([("leafy", "high"), ("pace", "low")], [])
        for mark in strip:
            assert mark["fact_id"] == f"{area['area_id']}/tag/{mark['tag_id']}"
            assert 1 <= mark["spread_low"] <= mark["band"] <= mark["spread_high"] <= 5
            assert (mark["toward"] is None) is not mark["asked"]
    # The strip is shown and never scored: no result holds a score for a vibe to print.
    assert "percentile" not in str([area["strip"] for area in found["ranked"]])


def test_how_much_of_what_counts_an_area_has_a_figure_for_is_said_of_every_area(
    client: TestClient,
):
    gap = next(row for row in release().features if row.value is None)
    # Beside a thing the area has a figure for, so that it has one for half of
    # the character asked for and is ranked.
    known = next(
        row.feature_id
        for row in release().features
        if row.area_id == gap.area_id and row.value is not None
    )
    spec = searching(weights=(asking_for(gap.feature_id, 0.3), asking_for(known, 0.3)))
    found = data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 1}))

    assert len(found["ranked"]) == 1 and len(found["scores"]) >= 20
    by_area = {score["area_id"]: score for score in found["scores"]}
    for area in rank(spec, release()).ranked:
        said = by_area[area.area_id]
        assert said["counted"] == len(area.contributions) == 4
        assert said["present"] == sum(c.present for c in area.contributions)
    assert by_area[gap.area_id]["present"] == 3


# Each journey is a guide: "in 35 minutes" is no limit, where "within 35 minutes" is one.
TO_WORK_AND_TO_STUDY = (
    "I work at Cindermoor Works and want to get there in 35 minutes. "
    "I study at Wexmoor University and want to get there in 40 minutes."
)
NEWCOMER = (
    "I have a job at Cindermoor Works and I have never lived in the city. "
    "I want somewhere leafy and fairly quiet, not too far from a decent pub. "
    "I can spend about \N{POUND SIGN}1,600 a month on a one bed flat."
)
OTTERBY_FIELDS = "syn-n0017"  # the new town, of which little is known


def chosen(client: TestClient, text: str) -> dict[str, Any]:
    """The spec a person holds once they have pressed the first choice of all that was offered."""
    read = data(client.post("/v1/interpret", json={"text": text}))
    assert read["status"] == "suggest" and read["applied"] == []
    spec = read["spec"]
    for offer in read["suggestions"]:
        pressed = {"spec": spec, "operations": offer["choices"][0]["operations"], "limit": 1}
        taken = data(client.post("/v1/rank", json=pressed))
        assert taken["rejected"] == []
        spec = taken["spec"]
    return spec


def test_an_area_with_no_figure_for_what_was_asked_is_listed_apart_with_what_it_lacks(
    client: TestClient,
):
    spec = chosen(client, NEWCOMER)
    found = data(client.post("/v1/rank", json={"spec": spec, "limit": 100}))

    assert [place["name"] for place in found["places"]] == ["Cindermoor Works"]
    assert [(tag["tag_id"], tag["toward"]) for tag in spec["tags"]] == [
        ("leafy", "high"),
        ("quiet_residential", "high"),
    ]
    # It came first, fit 88, with a journey, a rent and no figure for leafy, quiet or pubs.
    # What is said of the place now leads, so an area with no figure for any of it lacks
    # more than half of all that was asked, by weight, and is listed apart for that.
    [apart] = [area for area in found["unranked"] if area["area_id"] == OTTERBY_FIELDS]
    assert apart["reason"] == "insufficient_data"
    assert {"tag:leafy", "tag:quiet_residential", "feature:venue_evening_per_homes"} <= set(
        apart["missing"]
    )
    assert "commute" not in apart["missing"] and "budget" not in apart["missing"]
    ranked = [score["area_id"] for score in found["scores"]]
    assert OTTERBY_FIELDS not in ranked and len(ranked) == found["areas_ranked"] == 21
    # An area that is not rankable was never scored, so it says nothing of what it lacks.
    others = [area for area in found["unranked"] if area["area_id"] != OTTERBY_FIELDS]
    assert {(area["reason"], tuple(area["missing"])) for area in others} == {("not_rankable", ())}
    # Every area that is ranked has a figure for half of the character that was asked for.
    for area in found["ranked"]:
        character = [c for c in area["contributions"] if c["component"][:3] in ("tag", "fea")]
        present = sum(c["weight"] for c in character if c["present"])
        assert 2 * present >= sum(c["weight"] for c in character)


def test_an_area_that_is_listed_apart_is_compared_with_what_it_lacks(client: TestClient):
    spec = chosen(client, NEWCOMER)
    first = data(client.post("/v1/rank", json={"spec": spec, "limit": 1}))["ranked"][0]
    body = {"area_ids": [OTTERBY_FIELDS, first["area_id"]], "spec": spec}
    found = data(client.post("/v1/compare", json=body))

    apart, ranked = found["areas"]
    assert (apart["status"], apart["counted"], apart["present"]) == ("insufficient_data", 0, 0)
    assert (ranked["status"], ranked["counted"]) == ("ranked", len(first["contributions"]))
    served = {fact["fact_id"]: fact for fact in found["facts"]}
    rows = {row["component"]: row["cells"][0] for row in found["rows"]}
    said = {"tag:quiet_residential": "vibe_unknown", "feature:venue_evening_per_homes": "missing"}
    for lacking, template in said.items():
        cell = rows[lacking]
        # Nothing is filled in, and nothing is credited to an area that was not scored.
        assert (cell["value"], cell["utility"], cell["contribution"]) == (None, None, None)
        # The fact it cites says that there is no figure, and holds none about the place.
        assert served[cell["fact_id"]]["template"] == template
    # What is known of it is still shown: its journey and its rent.
    journey, rent = rows["commute.syn-p0021.pt"], rows["budget"]
    assert served[journey["fact_id"]]["kind"] == "travel" and journey["value"] is not None
    assert served[rent["fact_id"]]["kind"] == "budget_fit" and rent["value"] is not None
    assert (journey["utility"], rent["utility"]) == (None, None)


def test_an_area_far_from_one_workplace_is_not_first_because_another_has_no_time(
    client: TestClient,
):
    read = data(client.post("/v1/interpret", json={"text": TO_WORK_AND_TO_STUDY}))
    found = data(client.post("/v1/rank", json={"spec": read["spec"], "limit": 100}))

    assert [(c["max_minutes"], c["strictness"]) for c in read["spec"]["commutes"]] == [
        (35, "soft"),
        (40, "soft"),
    ]
    assert [place["name"] for place in read["places"]] == ["Cindermoor Works", "Wexmoor University"]
    assert "Gorsebeck" not in names_of(found, 5)
    [gorsebeck] = [a for a in found["ranked"] if a["area_id"] == "syn-n0008"]
    works, campus = gorsebeck["legs"]
    assert (works["minutes"], campus["minutes"], campus["status"]) == (63, None, "missing")
    [journeys] = [c for c in gorsebeck["contributions"] if c["component"] == "commute"]
    # Scored on the journey that has a time, which is far over its limit.
    assert (journeys["present"], journeys["utility"]) == (True, 0.0)
    assert journeys["fact_ids"] == [
        "syn-n0008/travel/syn-p0021.pt",
        "syn-n0008/missing/commute.syn-p0026.pt",
    ]
    explained = data(client.post("/v1/explanations", json={"spec": read["spec"], "limit": 5}))
    assert "syn-n0008" not in [e["area_id"] for e in explained["explanations"]]


def test_bad_edit_is_rejected_and_the_rest_applied(client: TestClient):
    edits = {
        "budget_ops": [],
        "commute_ops": [
            {
                "action": "add",
                "place_id": "",
                "mode": "pt",
                "max_minutes": 30,
                "strictness": "soft",
                "step": "none",
                "provenance": "ui_edit",
            }
        ],
        "weight_ops": [
            {
                "action": "SET",
                "feature_id": "green_cover",
                "value": 0.6,
                "step": "none",
                "direction": "default",
                "provenance": "ui_edit",
            }
        ],
        "tag_ops": [],
        "area_ops": [],
        "setting_ops": [],
    }
    found = data(client.post("/v1/rank", json={"spec": wire(renter()), "operations": edits}))

    assert found["rejected"] == [{"group": "commute_ops", "index": 0, "reason": "unknown_place"}]
    assert found["applied"] == [{"group": "weight_ops", "index": 0, "changed": True}]
    assert {"green_cover": 0.6}.items() <= {
        w["feature_id"]: w["weight"] for w in found["spec"]["weights"]
    }.items()


def test_a_spec_that_cannot_be_ranked_is_refused_with_paths_and_codes(client: TestClient):
    far = wire(renter(commutes=(commute(minutes=120),)))
    against = wire(renter(weights=(asking_for(FeatureId.PARK_PROXIMITY, 0.5, Direction.MORE),)))

    too_long = client.post("/v1/rank", json={"spec": far})
    wrong_way = client.post("/v1/rank", json={"spec": against})

    assert too_long.status_code == wrong_way.status_code == 422
    assert too_long.json()["error"]["fields"] == [
        {"path": "spec.commutes[0].max_minutes", "problem": "out_of_range"}
    ]
    assert wrong_way.json()["error"]["fields"] == [
        {"path": "spec.weights[0].direction", "problem": "direction_not_allowed"}
    ]


def stale_place() -> PreferenceSpec:
    """A spec that names a place the release does not have, as one kept from an older release."""
    return renter(commutes=(commute("syn-p9999"), commute(WORKS)))


def stale_area() -> dict[str, Any]:
    rule = {"area_id": "syn-n9999", "rule": "exclude", "provenance": "stated"}
    return wire(renter()) | {"areas": [rule]}


def editing(**groups: list[dict[str, Any]]) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "budget_ops": [],
        "commute_ops": [],
        "weight_ops": [],
        "tag_ops": [],
        "area_ops": [],
        "setting_ops": [],
    }
    return empty | groups


def removing(place_id: str) -> dict[str, Any]:
    return {
        "action": "remove",
        "place_id": place_id,
        "mode": "unchanged",
        "max_minutes": 0,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "ui_edit",
    }


def test_a_spec_that_has_gone_stale_can_be_put_right_by_an_edit(client: TestClient):
    gone = editing(commute_ops=[removing("syn-p9999")])
    cleared = editing(
        area_ops=[{"action": "clear", "area_id": "syn-n9999", "provenance": "ui_edit"}]
    )

    place = data(client.post("/v1/rank", json={"spec": wire(stale_place()), "operations": gone}))
    area = data(client.post("/v1/rank", json={"spec": stale_area(), "operations": cleared}))

    # The edits are applied first and the result is what is checked, so the
    # reducer's rule that what a release has dropped can always be removed is
    # one a client can reach.
    assert [c["place_id"] for c in place["spec"]["commutes"]] == [WORKS]
    assert place["applied"] == [{"group": "commute_ops", "index": 0, "changed": True}]
    assert area["spec"]["areas"] == [] and area["rejected"] == []
    assert place["ranked"] and area["ranked"]


def test_a_stale_spec_is_still_refused_unless_the_edit_puts_it_right(client: TestClient):
    other = editing(commute_ops=[removing(WORKS)])
    sent = [
        {"spec": wire(stale_place())},
        {"spec": wire(stale_place()), "operations": editing()},
        {"spec": wire(stale_place()), "operations": other},
    ]
    refused = [client.post("/v1/rank", json=body) for body in sent]

    assert [r.status_code for r in refused] == [422, 422, 422]
    assert {r.json()["error"]["code"] for r in refused} == {"unknown_place"}
    # The path is into the spec after the edits, in id order: the place that
    # is left when the other commute has been taken out is the first.
    assert [r.json()["error"]["fields"][0]["path"] for r in refused] == [
        "spec.commutes[1].place_id",
        "spec.commutes[1].place_id",
        "spec.commutes[0].place_id",
    ]
    unknown = client.post("/v1/rank", json={"spec": stale_area()})
    assert (unknown.status_code, unknown.json()["error"]["code"]) == (422, "unknown_area")


def test_words_put_no_stale_spec_right_whoever_reads_them():
    gone = model_commute(action="remove", position=2, words="I no longer work there")
    answer = model_output(commute_ops=[gone])
    model = FakeModelClient(answer)
    asked = ModelInterpreter(model, model=MODEL, max_tokens=512, timeout_s=1.0)
    deps = make_deps(interpreter=asked, model_id=MODEL)
    body = {"text": "I no longer work there", "spec": wire(stale_place())}

    found = client_for(deps).post("/v1/interpret", json=body)
    ruled = client_for(make_deps()).post("/v1/interpret", json=body)

    # The rules never remove a commute from words, and nothing a model reads
    # is applied. So it stays refused, and the control that takes it out puts it right.
    for refused in (found, ruled):
        assert (refused.status_code, refused.json()["error"]["code"]) == (422, "unknown_place")
    # The call was made, so it is on record, whether or not the spec could then be ranked.
    assert len(model.calls) == 1
    assert [record.status for record in deps.calls.records(NOW)] == ["ok"]


# Numbers.


def every_number() -> dict[str, dict[str, Any]]:
    """A body for each route that takes one, holding every field that is a number."""
    leafy = TagWeight(tag_id=TagId.LEAFY, weight=0.5, provenance=Provenance.STATED)
    spec = wire(searching(tags=(leafy,)))
    edits = editing(
        budget_ops=[
            {
                "action": "set",
                "tenure": "unchanged",
                "amount": 1500,
                "segment": "unchanged",
                "strictness": "unchanged",
                "step": "none",
                "provenance": "ui_edit",
            }
        ],
        commute_ops=[removing(WORKS) | {"action": "update", "max_minutes": 30}],
        weight_ops=[
            {
                "action": "set",
                "feature_id": "green_cover",
                "value": 0.5,
                "step": "none",
                "direction": "default",
                "provenance": "ui_edit",
            }
        ],
        tag_ops=[
            {
                "action": "set",
                "tag_id": "leafy",
                "value": 0.5,
                "step": "none",
                "toward": "default",
                "provenance": "ui_edit",
            }
        ],
        setting_ops=[
            {
                "action": "set",
                "setting": "commute_weight",
                "choice": "none",
                "value": 0.5,
                "step": "none",
                "provenance": "ui_edit",
            }
        ],
    )
    return {
        "/v1/interpret": {"text": "somewhere leafy", "spec": spec},
        "/v1/rank": {"spec": spec, "operations": edits, "limit": 5},
        "/v1/explanations": {"spec": spec, "limit": 2},
        "/v1/compare": {"area_ids": ["syn-n0001", "syn-n0002"], "spec": spec},
        "/v1/places/search": {"q": "Wexmoor", "limit": 3},
        "/v1/shares": {"spec": spec},
    }


def numbers_in(document: object, path: str = "") -> list[str]:
    """The path of every number in a document, as an error names it."""
    if isinstance(document, dict):
        fields = cast(dict[str, object], document)
        return [
            where
            for name, value in fields.items()
            for where in numbers_in(value, f"{path}.{name}" if path else name)
        ]
    if isinstance(document, list):
        items = cast(list[object], document)
        return [
            where
            for index, value in enumerate(items)
            for where in numbers_in(value, f"{path}[{index}]")
        ]
    return [path] if isinstance(document, int | float) and not isinstance(document, bool) else []


def with_value(document: dict[str, Any], path: str, value: object) -> dict[str, Any]:
    """A copy of `document` with `value` at `path`."""
    changed = copy.deepcopy(document)
    at: Any = changed
    *parents, last = [int(p) if p.isdecimal() else p for p in re.findall(r"[^.\[\]]+", path)]
    for part in parents:
        at = at[part]
    at[last] = value
    return changed


def test_the_bodies_these_tests_lean_on_hold_every_number_a_body_can():
    bodies = every_number()
    found = {path for body in bodies.values() for path in numbers_in(body)}

    assert all(
        client_for(make_deps()).post(p, json=b).status_code == 200 for p, b in bodies.items()
    )
    assert found >= {
        "limit",
        "spec.schema_version",
        "spec.commute_weight",
        "spec.budget.amount",
        "spec.budget.weight",
        "spec.commutes[0].max_minutes",
        "spec.weights[0].weight",
        "spec.tags[0].weight",
        "operations.budget_ops[0].amount",
        "operations.commute_ops[0].max_minutes",
        "operations.weight_ops[0].value",
        "operations.tag_ops[0].value",
        "operations.setting_ops[0].value",
    }


@pytest.mark.parametrize("sent", [True, False, "1", "0.5", "", "one"], ids=repr)
def test_a_number_must_be_sent_as_a_number(client: TestClient, sent: Any):
    for route, body in every_number().items():
        for path in numbers_in(body):
            refused = client.post(route, json=with_value(body, path, sent))

            # `true` is not 1 and "0.5" is not 0.5, whatever a parser would make of them.
            assert refused.status_code == 422, (route, path)
            fields = {(f["path"], f["problem"]) for f in refused.json()["error"]["fields"]}
            assert fields & {(path, "wrong_type"), (path, "not_allowed")}, (route, path, fields)


def test_a_whole_number_is_a_number_wherever_one_is_asked_for(client: TestClient):
    spec: dict[str, Any] = wire(searching()) | {"commute_weight": 1}
    spec["budget"] = spec["budget"] | {"weight": 1}

    found = data(client.post("/v1/rank", json={"spec": spec, "limit": 1}))

    assert found["spec"]["commute_weight"] == 1.0 and len(found["ranked"]) == 1


def choices_in(schema: object) -> list[list[dict[str, object]]]:
    """Every `anyOf` in a schema, however deep."""
    if isinstance(schema, dict):
        document = cast(dict[str, object], schema)
        found = [cast(list[dict[str, object]], document["anyOf"])] if "anyOf" in document else []
        return found + [choice for value in document.values() for choice in choices_in(value)]
    if isinstance(schema, list):
        return [choice for value in cast(list[object], schema) for choice in choices_in(value)]
    return []


def test_no_body_has_a_field_that_may_be_a_number_or_something_else():
    # The check that a number was sent as one reads a body beside its own
    # schema. It knows a field that may be left empty, and no other choice.
    for body in BODIES:
        for choice in choices_in(body.model_json_schema()):
            kinds = [option.get("type") for option in choice]
            assert len(choice) == 2 and kinds.count("null") == 1, (body.__name__, choice)


def test_missing_data_is_served_as_null_and_never_as_zero(client: TestClient):
    loaded = release()
    gaps = [row for row in loaded.features if row.value is None]
    assert gaps, "the synthetic release has gaps on purpose"
    gap = gaps[0]

    profile = data(client.get(f"/v1/areas/{gap.area_id}"))
    [served] = [row for row in profile["features"] if row["feature_id"] == gap.feature_id]
    assert served["value"] is None and served["percentile"] is None
    assert not [f for f in profile["facts"] if f["key"] == gap.feature_id]

    others = (w for w in renter().weights if w.feature_id != gap.feature_id)
    spec = renter(weights=(asking_for(gap.feature_id, 0.3), *others))
    found = data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 100}))
    [area] = [a for a in found["ranked"] if a["area_id"] == gap.area_id]
    [dropped] = [c for c in area["contributions"] if not c["present"]]
    # Dropped for that area, the weights rebalanced, and the coverage reported.
    assert dropped["component"] == f"feature:{gap.feature_id}"
    assert dropped["utility"] is None and area["weight_coverage"] < 1
    assert abs(sum(c["share"] for c in area["contributions"]) - 1) < 0.001


# Route 3.


def test_every_sentence_of_an_explanation_cites_a_fact_that_is_served(client: TestClient):
    found = data(client.post("/v1/explanations", json={"spec": wire(searching()), "limit": 2}))

    served = {fact["fact_id"]: fact for fact in found["facts"]}
    top = rank(searching(), release()).ranked[:2]
    assert [e["area_id"] for e in found["explanations"]] == [area.area_id for area in top]
    for explanation in found["explanations"]:
        sentences = [explanation["orientation"], *explanation["reasons"], *explanation["missing"]]
        sentences += [explanation["trade_off"]] if explanation["trade_off"] else []
        assert 2 <= len(explanation["reasons"]) <= 3
        for sentence in sentences:
            assert sentence["origin"] == "template" and sentence["replaced"] is False
            assert sentence["fact_ids"] and set(sentence["fact_ids"]) <= set(served)
            assert all(fact.startswith(explanation["area_id"]) for fact in sentence["fact_ids"])
    assert all(fact["sources"] and fact["as_of"] for fact in served.values())


def test_an_explanation_says_which_spec_it_is_for(client: TestClient):
    spec = searching()
    found = data(client.post("/v1/explanations", json={"spec": wire(spec), "limit": 1}))
    ranked = data(client.post("/v1/rank", json={"spec": wire(spec)}))

    assert found["spec_hash"] == ranked["spec_hash"] == spec_hash(spec)
    assert re.fullmatch(r"[0-9a-f]{64}", found["spec_hash"])


def test_every_mark_on_a_result_that_is_explained_has_its_fact_served(client: TestClient):
    leafy = TagWeight(tag_id=TagId.LEAFY, weight=0.8, provenance=Provenance.STATED)
    spec = searching(tags=(leafy,))
    found = data(client.post("/v1/explanations", json={"spec": wire(spec), "limit": 5}))
    ranked = data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 5}))

    served = {fact["fact_id"]: fact for fact in found["facts"]}
    marks = [mark for area in ranked["ranked"] for mark in area["strip"]]
    # Each fact is served once, however many sentences and marks name it.
    assert len(marks) > 5 and len(served) == len(found["facts"])
    for mark in marks:
        fact = served[mark["fact_id"]]
        assert (fact["kind"], fact["key"]) == ("tag", mark["tag_id"])
        assert fact["template"] in ("vibe", "vibe_range")
        assert fact["slots"]["band"] == str(mark["band"])
        # A vibe is said as a band, and never as a share of areas.
        assert "pct" not in fact["slots"] and not [n for n in fact["numbers"] if "%" in n]


def test_a_reason_is_said_from_its_better_side_and_a_trade_off_from_its_worse(
    client: TestClient,
):
    read = data(client.post("/v1/interpret", json={"text": "near a station"}))
    found = data(client.post("/v1/explanations", json={"spec": read["spec"], "limit": 5}))
    ranked = data(client.post("/v1/rank", json={"spec": read["spec"], "limit": 5}))

    facts = {fact["fact_id"]: fact for fact in found["facts"]}
    worth = {
        (area["area_id"], c["fact_ids"][0]): c["utility"]
        for area in ranked["ranked"]
        for c in area["contributions"]
        if c["present"]
    }
    told = 0
    for explanation in found["explanations"]:
        area_id = explanation["area_id"]
        for reason in explanation["reasons"]:
            fact = facts[reason["fact_ids"][0]]
            assert worth[area_id, fact["fact_id"]] >= REASON_MIN_UTILITY
            if fact["kind"] == "feature":
                assert fact["slots"]["standing"] in reason["text"]
                told += 1
        if explanation["trade_off"] is not None:
            fact = facts[explanation["trade_off"]["fact_ids"][0]]
            assert worth[area_id, fact["fact_id"]] < TRADE_OFF_MAX_UTILITY
            if fact["kind"] == "feature":
                assert fact["slots"]["standing_worse"] in explanation["trade_off"]["text"]
                assert fact["slots"]["comparative"] not in explanation["trade_off"]["text"]
    assert told >= 5
    # A walk of a few minutes to a station is nothing an area gives up.
    walks = [f for f in facts.values() if f["key"] == "station_walk"]
    given_up = [e["trade_off"]["fact_ids"][0] for e in found["explanations"] if e["trade_off"]]
    assert walks and not [fact for fact in walks if fact["fact_id"] in given_up]


def test_a_band_that_rests_on_part_of_its_recipe_says_how_much_wherever_it_is_said(
    client: TestClient,
):
    on_foot = TagWeight(tag_id=TagId.EVERYDAY_ON_FOOT, weight=1.0, provenance=Provenance.STATED)
    found = data(client.post("/v1/explanations", json={"spec": wire(renter(tags=(on_foot,)))}))

    facts = {fact["fact_id"]: fact for fact in found["facts"]}
    clause = "Worked out from 3 of its 5 parts, 70 of 100 by weight."
    said = 0
    for explanation in found["explanations"]:
        for sentence in explanation["reasons"]:
            fact = facts[sentence["fact_ids"][0]]
            if fact["key"] != "everyday_on_foot":
                continue
            # The release lacks two parts of the recipe. The band was said as any other.
            slots = fact["slots"]
            assert (slots["known"], slots["parts"], slots["share"]) == ("3", "5", "70")
            assert slots["partly"] == clause and clause in sentence["text"]
            # It is the template's own sentence, and the verifier passed it.
            assert sentence["replaced"] is False and {"70", "100"} <= set(fact["numbers"])
            said += 1
    assert said == len(found["explanations"]) == 3
    # A band that rests on the whole of its recipe says nothing more than it did.
    whole = data(client.get("/v1/areas/alderwick"))["facts"]
    [leafy] = [fact for fact in whole if (fact["kind"], fact["key"]) == ("tag", "leafy")]
    assert (leafy["slots"]["share"], leafy["slots"]["partly"]) == ("100", "")
    # How much of a recipe is no percentage of anything about the place.
    vibes = [fact for fact in whole if fact["kind"] == "tag"]
    assert not [number for fact in vibes for number in fact["numbers"] if "%" in number]


def test_a_vibe_that_is_a_reason_is_said_in_short_and_its_fact_holds_the_rest(
    client: TestClient,
):
    leafy = TagWeight(tag_id=TagId.LEAFY, weight=1.0, provenance=Provenance.STATED)
    found = data(client.post("/v1/explanations", json={"spec": wire(renter(tags=(leafy,)))}))

    facts = {fact["fact_id"]: fact for fact in found["facts"]}
    said = 0
    for explanation in found["explanations"]:
        for sentence in explanation["reasons"]:
            fact = facts[sentence["fact_ids"][0]]
            if fact["kind"] != "tag":
                continue
            # A result says in a few lines why this place: the band, and no more.
            assert sentence["text"].endswith("compared in this release.")
            assert "Parts dated" not in sentence["text"]
            assert "judgement" not in sentence["text"]
            # What was left out is served with the sentence, to be shown with its source.
            assert fact["slots"]["judgement"] == JUDGEMENT
            assert fact["as_of"] == fact["slots"]["span"] and fact["sources"]
            said += 1
    assert said == len(found["explanations"]) == 3


def test_a_station_560_metres_off_is_not_what_an_area_gives_up(client: TestClient):
    spec = data(client.post("/v1/interpret", json={"text": TO_WORK_AND_TO_STUDY}))["spec"]
    found = data(client.post("/v1/explanations", json={"spec": spec, "limit": 1}))
    ranked = data(client.post("/v1/rank", json={"spec": spec, "limit": 1}))

    [first], [explained] = ranked["ranked"], found["explanations"]
    assert first["area_id"] == explained["area_id"] == WEXMOOR
    [walk] = [c for c in first["contributions"] if c["component"] == "feature:station_walk"]
    # It is worth less than a trade-off must be, because fourteen areas are closer still.
    assert walk["utility"] < TRADE_OFF_MAX_UTILITY
    cited = [s["fact_ids"][0] for s in (explained["trade_off"], *explained["reasons"]) if s]
    assert f"{WEXMOOR}/feature/station_walk" not in cited
    assert explained["trade_off"]["fact_ids"] != walk["fact_ids"]


def test_a_distance_of_a_thousand_metres_is_written_as_people_write_it(client: TestClient):
    found = data(client.get("/v1/areas/alderwick"))

    far = {f["key"]: f for f in found["facts"] if f["slots"].get("value", "").endswith("0 m")}
    assert (far["university_proximity"]["slots"]["value"]) == "8,230 m"
    # The number it may be checked against holds no separator, as every number of a fact.
    assert "8230" in far["university_proximity"]["numbers"]
    assert not [f for f in far.values() if re.search(r"\d{4}", f["slots"]["value"])]


def test_invented_venue_or_changed_number_is_replaced_by_a_template():
    from burro_core.explain import ExplainInput, TemplateExplainer
    from burro_core.ids import SentenceOrigin
    from burro_core.verify import Sentence

    # `explain` takes the template explainer and no other (contract, section 11),
    # so what plants a sentence is a subclass of it.
    class Inventing(TemplateExplainer):
        def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
            return tuple(
                Sentence(
                    text="It is a short walk from the Gilded Heron, 3 minutes away.",
                    fact_ids=(ask.fact_id,),
                    origin=SentenceOrigin.MODEL,
                )
                for ask in area.asks
            )

    client = client_for(make_deps(explainer=Inventing()))
    found = data(client.post("/v1/explanations", json={"spec": wire(searching()), "limit": 1}))

    [explanation] = found["explanations"]
    shown = [explanation["orientation"], *explanation["reasons"]]
    assert all(s["replaced"] and s["origin"] == "template" for s in shown)
    assert "Gilded Heron" not in str(found)


# Route 7.


def comparing(spec: PreferenceSpec, *area_ids: str) -> dict[str, Any]:
    return {"area_ids": list(area_ids), "spec": wire(spec)}


def test_a_comparison_orders_its_rows_by_the_persons_own_weights(client: TestClient):
    spec = renter(
        budget=budget().replace(weight=0.5),
        commutes=(commute(),),
        commute_weight=0.9,
        weights=(asking_for(FeatureId.GREEN_COVER, 0.5),),
        tags=(TagWeight(tag_id=TagId.LEAFY, weight=1.0, provenance=Provenance.STATED),),
    )
    found = data(client.post("/v1/compare", json=comparing(spec, "syn-n0003", "syn-n0001")))

    assert [(row["component"], row["weight"]) for row in found["rows"]] == [
        ("tag:leafy", 1.0),
        ("commute.syn-p0021.pt", 0.9),
        ("budget", 0.5),
        ("feature:green_cover", 0.5),
    ]
    assert [row["label"] for row in found["rows"]] == [
        TAGS[TagId.LEAFY].label,
        "Journey",
        "Budget",
        FEATURES[FeatureId.GREEN_COVER].label,
    ]
    # The areas stay in the order they were asked for.
    assert [area["area_id"] for area in found["areas"]] == ["syn-n0003", "syn-n0001"]
    for row in found["rows"]:
        assert [cell["area_id"] for cell in row["cells"]] == ["syn-n0003", "syn-n0001"]


def test_every_number_in_a_comparison_names_the_fact_behind_it(client: TestClient):
    leafy = TagWeight(tag_id=TagId.LEAFY, weight=0.4, provenance=Provenance.STATED)
    spec = searching(tags=(leafy,))
    ranked = rank(spec, release())
    areas = [area.area_id for area in ranked.ranked[:3]]
    found = data(client.post("/v1/compare", json=comparing(spec, *areas)))

    served = {fact["fact_id"]: fact for fact in found["facts"]}
    by_area = {area.area_id: area for area in ranked.ranked}
    for row in found["rows"]:
        # The journeys count as one thing. With one journey, its row is all of it.
        component = "commute" if row["place"] else row["component"]
        for cell in row["cells"]:
            scored = {c.component: c for c in by_area[cell["area_id"]].contributions}
            assert cell["utility"] == scored[component].utility
            assert cell["contribution"] == scored[component].contribution
            if cell["value"] is not None or cell["percentile"] is not None:
                fact = served[cell["fact_id"]]
                assert fact["area_id"] == cell["area_id"] and fact["sources"] and fact["as_of"]
    [journey] = journeys_of(found)
    assert journey["component"] == "commute.syn-p0021.pt"
    for cell in journey["cells"]:
        [leg] = by_area[cell["area_id"]].legs
        assert cell["value"] == leg.minutes and cell["percentile"] is None
    # A vibe is shown as a band. The score it is ranked on is no figure of its
    # fact, so no cell holds it to be printed.
    [vibe] = [row for row in found["rows"] if row["component"] == "tag:leafy"]
    [bands] = [row for row in found["character"] if row["tag_id"] == "leafy"]
    for cell, mark in zip(vibe["cells"], bands["marks"], strict=True):
        assert (cell["value"], cell["percentile"]) == (None, None)
        assert cell["fact_id"] == mark["fact_id"] and mark["band"] in range(1, 6)
        assert not [n for n in served[cell["fact_id"]]["numbers"] if "%" in n or "." in n]


def test_an_area_that_is_not_ranked_is_compared_with_its_reason(client: TestClient):
    spec = searching(commutes=(commute(minutes=20, hard=True),))
    ranked = rank(spec, release())
    capped = next(f.area_id for f in ranked.filtered if f.reason is FilterReason.COMMUTE_CAP)
    small = next(u.area_id for u in ranked.unranked if u.reason is UnrankedReason.NOT_RANKABLE)
    kept = ranked.ranked[0].area_id
    found = data(client.post("/v1/compare", json=comparing(spec, kept, capped, small)))

    assert [area["status"] for area in found["areas"]] == ["ranked", "commute_cap", "not_rankable"]
    for row in found["rows"]:
        scored, *others = row["cells"]
        assert scored["utility"] is not None
        assert all(c["utility"] is None and c["contribution"] is None for c in others)
    # Every reason an area can be left out for has a status of its own.
    assert {s.value for s in CompareStatus} == {
        "ranked",
        *(reason.value for reason in FilterReason),
        *(reason.value for reason in UnrankedReason),
    }


def test_a_comparison_shows_a_gap_as_a_gap(client: TestClient):
    gap = next(row for row in release().features if row.value is None)
    whole = next(
        row
        for row in release().features
        if row.feature_id is gap.feature_id and row.value is not None
    )
    spec = renter(weights=(asking_for(gap.feature_id, 0.5),))
    found = data(client.post("/v1/compare", json=comparing(spec, gap.area_id, whole.area_id)))

    [row] = [r for r in found["rows"] if r["component"] == f"feature:{gap.feature_id}"]
    missing, present = row["cells"]
    # Not known is `null`. Zero would be a figure, and a wrong one.
    assert (missing["value"], missing["percentile"], missing["utility"]) == (None, None, None)
    assert missing["fact_id"] == f"{gap.area_id}/missing/feature:{gap.feature_id}"
    assert (present["value"], present["percentile"]) == (whole.value, whole.percentile)
    served = {fact["fact_id"]: fact for fact in found["facts"]}
    assert served[missing["fact_id"]]["numbers"] == []


CAMPUS = "syn-p0026"  # Wexmoor University
WEXMOOR, CINDERMOOR, GORSEBECK = "syn-n0023", "syn-n0003", "syn-n0008"


def two_journeys(**changes: Any) -> PreferenceSpec:
    """A renter who must reach the works within 35 minutes and the campus within 40."""
    return renter(commutes=(commute(WORKS, 35), commute(CAMPUS, 40)), **changes)


def journeys_of(found: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in found["rows"] if row["place"] is not None]


def test_a_comparison_has_one_row_for_each_journey_with_the_same_destination_across_it(
    client: TestClient,
):
    spec = two_journeys()
    areas = (WEXMOOR, CINDERMOOR, GORSEBECK)
    found = data(client.post("/v1/compare", json=comparing(spec, *areas)))

    served = {fact["fact_id"]: fact for fact in found["facts"]}
    journeys = journeys_of(found)
    # One for each journey of the spec, in the spec's order, named as core keys a journey.
    assert [(row["component"], row["place"]) for row in journeys] == [
        (
            "commute.syn-p0021.pt",
            {"place_id": WORKS, "name": "Cindermoor Works", "kind": "district"},
        ),
        (
            "commute.syn-p0026.pt",
            {"place_id": CAMPUS, "name": "Wexmoor University", "kind": "university"},
        ),
    ]
    for row in journeys:
        assert (row["label"], row["weight"]) == ("Journey", spec.commute_weight)
        assert [cell["area_id"] for cell in row["cells"]] == list(areas)
        for cell in row["cells"]:
            fact = served[cell["fact_id"]]
            # It was one row, in which one area was timed to the works and the
            # next to the campus.
            assert (fact["area_id"], fact["slots"]["place"]) == (
                cell["area_id"],
                row["place"]["name"],
            )
    # No row holds the journeys to two places, and no other row names a place.
    assert "commute" not in [row["component"] for row in found["rows"]]
    assert len(journeys) == 2 and len(found["rows"]) > 2


def test_a_journey_with_no_time_is_shown_as_having_none(client: TestClient):
    found = data(client.post("/v1/compare", json=comparing(two_journeys(), WEXMOOR, GORSEBECK)))

    served = {fact["fact_id"]: fact for fact in found["facts"]}
    to_the_works, to_the_campus = journeys_of(found)
    far, unknown = to_the_works["cells"][1], to_the_campus["cells"][1]
    assert (far["value"], far["utility"], far["fact_id"]) == (
        63,
        0.0,
        f"{GORSEBECK}/travel/syn-p0021.pt",
    )
    assert served[far["fact_id"]]["template"] == "travel_pt_over"
    # Not known is `null`, and it is said: the journey has a cell, and a fact of its own.
    assert (unknown["value"], unknown["utility"], unknown["contribution"]) == (None, None, None)
    assert unknown["fact_id"] == f"{GORSEBECK}/missing/commute.syn-p0026.pt"
    said = served[unknown["fact_id"]]
    assert (said["template"], said["numbers"]) == ("missing_journey", [])
    assert said["slots"] == {"name": "Gorsebeck", "place": "Wexmoor University"}


def test_what_the_journeys_add_stands_once_beside_the_journey_that_counts(client: TestClient):
    spec = two_journeys()
    ranked = {area.area_id: area for area in rank(spec, release()).ranked}
    found = data(client.post("/v1/compare", json=comparing(spec, WEXMOOR, CINDERMOOR, GORSEBECK)))

    for at, area_id in enumerate((WEXMOOR, CINDERMOOR, GORSEBECK)):
        area = ranked[area_id]
        [scored] = [c for c in area.contributions if c.component == "commute"]
        cells = [row["cells"][at] for row in journeys_of(found)]
        for cell, leg in zip(cells, area.legs, strict=True):
            # Each journey is worth what core says it is, and shows the time that was scored.
            assert (cell["value"], cell["utility"]) == (leg.minutes, leg.utility)
        # What the journeys add is said once, beside the one that drove the score.
        adds = {cell["fact_id"]: cell["contribution"] for cell in cells}
        assert adds.pop(scored.fact_ids[0]) == scored.contribution
        assert set(adds.values()) == {None}
    # The slowest counts, so two areas are held to two different journeys.
    drove = {
        next(c for c in ranked[area_id].contributions if c.component == "commute").fact_ids[0]
        for area_id in (WEXMOOR, CINDERMOOR)
    }
    assert drove == {f"{WEXMOOR}/travel/syn-p0021.pt", f"{CINDERMOOR}/travel/syn-p0026.pt"}


def test_where_every_journey_counts_no_one_journey_is_said_to_add_the_whole(client: TestClient):
    spec = two_journeys(commute_combine=Combine.MEAN)
    ranked = {area.area_id: area for area in rank(spec, release()).ranked}
    found = data(client.post("/v1/compare", json=comparing(spec, WEXMOOR, CINDERMOOR)))

    for row in journeys_of(found):
        for cell in row["cells"]:
            # What one journey of several adds is not something the ranking
            # says, and nothing is worked out here in its place.
            assert cell["contribution"] is None and cell["utility"] is not None
    # One journey alone is all the journeys there are, whichever way they are put together.
    one = renter(commutes=(commute(WORKS, 35),), commute_combine=Combine.MEAN)
    alone = data(client.post("/v1/compare", json=comparing(one, WEXMOOR, CINDERMOOR)))
    [row] = journeys_of(alone)
    scored = {area.area_id: area for area in rank(one, release()).ranked}
    for cell in row["cells"]:
        [journeys] = [c for c in scored[cell["area_id"]].contributions if c.component == "commute"]
        assert cell["contribution"] == journeys.contribution
    assert ranked[WEXMOOR].legs[0].utility != ranked[WEXMOOR].contributions[0].utility


def test_an_area_that_is_not_ranked_still_shows_each_of_its_journeys(client: TestClient):
    spec = two_journeys().replace(commutes=(commute(WORKS, 20, hard=True), commute(CAMPUS, 40)))
    ranked = rank(spec, release())
    capped = next(f.area_id for f in ranked.filtered if f.reason is FilterReason.COMMUTE_CAP)
    small = next(u.area_id for u in ranked.unranked if u.reason is UnrankedReason.NOT_RANKABLE)
    found = data(client.post("/v1/compare", json=comparing(spec, capped, small)))

    served = {fact["fact_id"]: fact for fact in found["facts"]}
    assert [area["status"] for area in found["areas"]] == ["commute_cap", "not_rankable"]
    to_the_works, _ = journeys_of(found)
    over = to_the_works["cells"][0]
    # The journey that left the area out is shown, with the limit it is over.
    assert over["fact_id"] == f"{capped}/travel/syn-p0021.pt" and over["value"] > 20
    assert served[over["fact_id"]]["template"] == "travel_pt_over"
    assert served[over["fact_id"]]["slots"]["limit"] == "20"
    for row in journeys_of(found):
        for cell in row["cells"]:
            fact = served[cell["fact_id"]]
            assert fact["slots"]["place"] == row["place"]["name"]
            assert (cell["value"] is None) is (fact["template"] == "missing_journey")
            # It was not scored, so its journeys are worth nothing that can be said.
            assert (cell["utility"], cell["contribution"]) == (None, None)


def test_a_comparison_begins_with_where_each_area_sits_on_every_vibe(client: TestClient):
    areas = ("syn-n0007", "syn-n0017", "syn-n0009")  # mixed, all but unknown, not rankable
    found = data(client.post("/v1/compare", json=comparing(searching(), *areas)))

    shown = [vibe.tag_id.value for vibe in release().vibes if vibe.table]
    assert [row["tag_id"] for row in found["character"]] == shown and len(shown) == 14
    served = {fact["fact_id"]: fact for fact in found["facts"]}
    for row in found["character"]:
        assert [mark["area_id"] for mark in row["marks"]] == list(areas)
        for mark in row["marks"]:
            held = release().tag(mark["area_id"], TagId(row["tag_id"]))
            assert held is not None
            assert (mark["band"], mark["spread_low"], mark["spread_high"]) == (
                held.band,
                held.spread_low,
                held.spread_high,
            )
            # Placed or not, the mark names the fact that says so, and it is served.
            fact = served[mark["fact_id"]]
            assert (fact["area_id"], fact["kind"], fact["key"]) == (
                mark["area_id"],
                "tag",
                row["tag_id"],
            )
            assert (fact["template"] == "vibe_unknown") is (mark["band"] is None)
    [pace] = [row for row in found["character"] if row["tag_id"] == "pace"]
    # The third has too few homes for a figure of two of the three parts of Going out.
    assert [(m["band"], m["spread_low"], m["spread_high"]) for m in pace["marks"]] == [
        (4, 3, 5),
        (None, None, None),
        (None, None, None),
    ]


def test_a_comparison_says_how_much_each_fit_is_based_on(client: TestClient):
    spec = searching(commutes=(commute(minutes=20, hard=True),))
    ranked = rank(spec, release())
    capped = next(f.area_id for f in ranked.filtered if f.reason is FilterReason.COMMUTE_CAP)
    kept = ranked.ranked[0]
    found = data(client.post("/v1/compare", json=comparing(spec, kept.area_id, capped)))

    first, second = found["areas"]
    assert (first["counted"], first["present"]) == (kept.counted, kept.present)
    assert kept.counted == len(found["rows"]) > 0
    # An area that is not ranked was not scored, so nothing of it was counted.
    assert (second["status"], second["counted"], second["present"]) == ("commute_cap", 0, 0)


def test_every_cell_of_a_row_is_said_from_one_side(client: TestClient):
    # Of the places to eat and drink no two areas stand level at either end, so each cell
    # has an area strictly beyond it to be said against.
    asked = FeatureId.VENUE_FOOD_DRINK_PER_HOMES
    spec = renter(weights=(asking_for(asked, 0.5, Direction.LESS),))
    areas = [area.area_id for area in rank(spec, release()).ranked]
    found = data(client.post("/v1/compare", json=comparing(spec, areas[0], areas[-1])))
    other = data(
        client.post(
            "/v1/compare",
            json=comparing(
                renter(weights=(asking_for(asked, 0.5, Direction.MORE),)),
                areas[0],
                areas[-1],
            ),
        )
    )

    def comparatives(answer: dict[str, Any]) -> set[str]:
        facts = {fact["fact_id"]: fact for fact in answer["facts"]}
        [row] = answer["rows"]
        return {facts[cell["fact_id"]]["slots"]["comparative"] for cell in row["cells"]}

    feature = FEATURES[asked]
    # The side is the spec's, the same for every cell: fewer places for one who asked for fewer.
    assert comparatives(found) == {f"{feature.lower} than"}
    assert comparatives(other) == {f"{feature.higher} than"}


@pytest.mark.parametrize(
    "area_ids",
    [["syn-n0001"], ["syn-n0001"] * 2, [f"syn-n000{n}" for n in range(1, 6)], "syn-n0001", []],
)
def test_a_comparison_takes_two_to_four_different_areas(client: TestClient, area_ids: Any):
    refused = client.post("/v1/compare", json={"area_ids": area_ids, "spec": wire(renter())})

    assert refused.status_code == 422
    assert refused.json()["error"]["code"] == "invalid_compare"
    assert {field["path"] for field in refused.json()["error"]["fields"]} == {"area_ids"}


# Routes 4, 5 and 6.


def test_areas_are_listed_by_id_with_their_boundaries(client: TestClient):
    areas = data(client.get("/v1/areas"))["areas"]
    shapes = data(client.get("/v1/areas/geometry"))

    assert [area["area_id"] for area in areas] == sorted(area["area_id"] for area in areas)
    assert len(areas) == 24 and sum(area["rankable"] for area in areas) == 22
    assert set(areas[0]) == {
        "area_id",
        "slug",
        "name",
        "borough",
        "centroid",
        "rankable",
        "named",
    }
    assert shapes["type"] == "FeatureCollection"
    assert [shape["id"] for shape in shapes["features"]] == [area["area_id"] for area in areas]
    for shape in shapes["features"]:
        assert shape["properties"] == {"area_id": shape["id"]}
        assert shape["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_an_area_says_its_label_who_wrote_its_name_and_whether_a_person_has_checked_it(
    client: TestClient,
):
    areas = {area["name"]: area for area in data(client.get("/v1/areas"))["areas"]}

    assert areas["Alderwick"]["named"] == {
        "label": "Quillhaven 001",
        "source_ids": ["synthetic"],
        "state": "draft",
    }
    assert areas["Tallowgate"]["named"]["state"] == "checked"
    # An area that bears no name but its label says nothing of one, and nothing is made up.
    assert areas["Grapnel Dock"]["named"] is None
    states = [area["named"]["state"] for area in areas.values() if area["named"]]
    assert (states.count("draft"), states.count("checked")) == (19, 3)

    # The page of an area holds the same, and the fact of its name holds what is shown of it.
    found = data(client.get("/v1/areas/alderwick"))
    assert found["area"]["named"] == areas["Alderwick"]["named"]
    fact = next(fact for fact in found["facts"] if fact["kind"] == "area")
    assert fact["slots"] == {
        "name": "Alderwick",
        "borough": "Quillhaven",
        "label": "Quillhaven 001",
        "written_by": "Burro",
        "state": "draft",
    }
    unnamed = data(client.get("/v1/areas/grapnel-dock"))
    assert unnamed["area"]["named"] is None
    assert next(f for f in unnamed["facts"] if f["kind"] == "area")["slots"] == {
        "name": "Grapnel Dock",
        "borough": "Quillhaven",
    }
    # Every list of areas says it: the neighbours of an area do.
    assert all("named" in neighbour for neighbour in found["neighbours"])


def test_the_map_can_be_coloured_by_any_vibe_from_one_answer(client: TestClient):
    found = data(client.get("/v1/areas"))

    lenses = [vibe for vibe in release().vibes if vibe.lens]
    assert [row["tag_id"] for row in found["bands"]] == [vibe.tag_id.value for vibe in lenses]
    assert len(lenses) == 14
    for row in found["bands"]:
        # One mark for each area, so that an area with no band is drawn as that.
        assert [mark["area_id"] for mark in row["marks"]] == [a["area_id"] for a in found["areas"]]
        for mark in row["marks"]:
            held = release().tag(mark["area_id"], TagId(row["tag_id"]))
            assert held is not None and set(mark) == {
                "area_id",
                "band",
                "spread_low",
                "spread_high",
            }
            assert (mark["band"], mark["spread_low"], mark["spread_high"]) == (
                held.band,
                held.spread_low,
                held.spread_high,
            )
    # It is a band, one of five. The score an area is ranked on is not served here.
    assert "score" not in str(found["bands"]) and "raw" not in str(found["bands"])
    unplaced = [m for row in found["bands"] for m in row["marks"] if m["band"] is None]
    assert len(unplaced) == 32 and {m["spread_low"] for m in unplaced} == {None}


def test_a_vibe_the_release_keeps_off_the_map_is_not_among_the_bands():
    loaded = release()
    hidden = tuple(v.replace(lens=v.tag_id is not TagId.STREET_CHARACTER) for v in loaded.vibes)
    client = client_for(make_deps(release=replace(loaded, vibes=hidden)))

    found = data(client.get("/v1/areas"))

    assert len(found["bands"]) == 13
    assert "street_character" not in [row["tag_id"] for row in found["bands"]]


def test_an_area_is_found_by_its_id_or_its_slug(client: TestClient):
    by_id = client.get("/v1/areas/syn-n0004").json()
    by_slug = client.get("/v1/areas/dulcimer-green").json()

    assert by_id == by_slug
    profile = by_id["data"]
    assert profile["area"]["name"] == "Dulcimer Green"
    # Every feature the release carries, and every vibe: the thirteen, and Gritty.
    assert len(profile["features"]) == 109 and len(profile["tags"]) == 14
    assert {n["area_id"] for n in profile["neighbours"]} == set(profile["area"]["neighbours"])
    assert profile["stations"] and profile["cost"]
    assert [row["tag_id"] for row in profile["tags"]] == [v.tag_id.value for v in release().vibes]
    # Built with no spec: nothing about a journey or a budget.
    assert {fact["kind"] for fact in profile["facts"]} == {
        "area",
        "feature",
        "tag",
        "cost",
        "station",
        "likeness",
    }
    assert client.get("/v1/areas/Dulcimer%20Green").status_code == 404


def marks_of(found: dict[str, Any]) -> dict[str, list[str]]:
    return {name: [mark["tag_id"] for mark in marks] for name, marks in found["portrait"].items()}


def test_the_portrait_of_an_area_is_the_same_for_everyone_and_holds_no_sentence(
    client: TestClient,
):
    found = data(client.get("/v1/areas/foxholt"))

    expected = portrait(release(), "syn-n0007")
    assert expected is not None and found["portrait"] == expected.model_dump(mode="json")
    assert marks_of(found) == {
        "scales": ["homes", "pace", "built_age", "street_character"],
        "more": ["everyday_on_foot", "parks_close_by", "family_amenities"],
        "less": ["well_connected"],
        # A vibe that counts who lived there is on the portrait with its band, and is
        # never among what an area has most of, though this area is in its highest band
        # on both. Nor is a vibe that is a rough guide among what an area has most or
        # least of: Village feel is on the portrait with its band, and leads nothing.
        "others": [
            "leafy",
            "village_feel",
            "quiet_residential",
            "foodie",
            "family_area",
            "young_professionals",
        ],
        "unplaced": [],
    }
    for tag_id in ("family_area", "young_professionals"):
        held = release().tag("syn-n0007", TagId(tag_id))
        assert held is not None and held.band == 5
    facts = {fact["fact_id"]: fact for fact in found["facts"]}
    every = [mark for marks in found["portrait"].values() for mark in marks]
    assert len(every) == 14
    for mark in every:
        # Each mark names the fact that holds its sentence, and each part its figure.
        assert facts[mark["fact_id"]]["kind"] == "tag"
        assert facts[mark["figure_fact_id"]]["kind"] == "feature"
        for part in mark["parts"]:
            assert set(part) == {"feature_id", "hundredths", "reading", "fact_id"}
            assert part["fact_id"] is None or facts[part["fact_id"]]["key"] == part["feature_id"]
        assert sum(part["hundredths"] for part in mark["parts"]) == 100
    # A mixed area is a range, and is said to vary.
    pace = facts["syn-n0007/tag/pace"]
    assert pace["template"] == "vibe_range"
    assert (pace["slots"]["spread_low"], pace["slots"]["spread_high"]) == ("3", "5")
    assert (pace["slots"]["low_end"], pace["slots"]["high_end"]) == ("Calm", "Buzzy")
    assert pace["as_of"] == "2025" != release().manifest.built_at


def test_an_area_that_cannot_be_placed_is_said_to_be_that_and_is_like_nothing(
    client: TestClient,
):
    found = data(client.get("/v1/areas/otterby-fields"))

    placed = marks_of(found)
    assert placed["scales"] == ["homes"] and len(placed["unplaced"]) == 13
    assert placed["more"] == placed["less"] == placed["others"] == []
    facts = {fact["fact_id"]: fact for fact in found["facts"]}
    for mark in found["portrait"]["unplaced"]:
        fact = facts[mark["fact_id"]]
        # It holds no figure about the place: only how much of the recipe is known.
        assert fact["template"] == "vibe_unknown" and "band" not in fact["slots"]
        known = [part for part in mark["parts"] if part["fact_id"] is not None]
        assert fact["slots"]["known"] == str(len(known))
        # Too little of the recipe to place it by, and nothing stands in for the rest.
        assert sum(part["hundredths"] for part in known) < 60
    assert found["similar"] == []
    assert "likeness" not in {fact["kind"] for fact in found["facts"]}
    # A part that this release does not carry has no figure, and none is made up.
    [homes] = found["portrait"]["scales"]
    outdoor = [p for p in homes["parts"] if p["feature_id"] == "private_outdoor_space"]
    assert [part["fact_id"] for part in outdoor] == [None]


def test_the_areas_most_like_an_area_are_named_with_a_sentence_each(client: TestClient):
    found = data(client.get("/v1/areas/thrushcombe"))

    expected = similar(release(), "syn-n0022")
    assert [like["area_id"] for like in found["similar"]] == [like.area_id for like in expected]
    assert len(found["similar"]) == 5 and "syn-n0024" in {s["area_id"] for s in found["similar"]}
    facts = {fact["fact_id"]: fact for fact in found["facts"]}
    labels = set(FAMILIES.values())
    for like in found["similar"]:
        # What orders them is never served: a distance is not a fact about a place.
        assert set(like) == {"area_id", "fact_id"}
        fact = facts[like["fact_id"]]
        assert (fact["kind"], fact["key"]) == ("likeness", like["area_id"])
        assert fact["slots"]["family"] in labels and int(fact["slots"]["measures"]) == 23
        assert fact["sources"] and fact["as_of"]
        # Nor is it in the sentence of the likeness, by any name or as a figure of its own.
        assert not [name for name in fact["slots"] if "distance" in name]
    # No field of the answer is a distance between two areas, whatever else its name holds.
    # A measure may be a distance on the ground, and its label then says so: that is a fact
    # about a place, and it is a value and never the name of a field.
    assert not [name for name in fields_of(found) if "distance" in name]
    # What is served of a likeness never says the word, in a name or in a value.
    likenesses = [facts[like["fact_id"]] for like in found["similar"]]
    assert "distance" not in str(found["similar"]) and "distance" not in str(likenesses)
    # Most alike first, by the count each sentence gives: it read 10, 10, 5, 7, 8.
    same = [int(facts[like["fact_id"]]["slots"]["same"]) for like in found["similar"]]
    assert same == sorted(same, reverse=True) and same[0] > same[-1]


# Route 8.


def test_places_are_found_by_name_with_the_place_that_stands_in_for_them(client: TestClient):
    found = data(client.post("/v1/places/search", json={"q": "alderwick prim"}))["places"]
    several = data(client.post("/v1/places/search", json={"q": "Kindlewharf", "limit": 2}))

    assert found == [
        {
            "place_id": "syn-p0031",
            "name": "Alderwick Primary School",
            "kind": "school",
            "coarse_name": "Eskerfold",
        }
    ]
    # A station comes before a district of the same name, as the contract orders them.
    assert [place["kind"] for place in several["places"]] == ["station", "district"]


def test_a_search_by_name_finds_the_areas_that_bear_it_apart_from_the_places(client: TestClient):
    found = data(client.post("/v1/places/search", json={"q": "Kindlewharf"}))
    begun = data(client.post("/v1/places/search", json={"q": "os"}))
    other_name = data(client.post("/v1/places/search", json={"q": "dulcimer"}))
    nothing = data(client.post("/v1/places/search", json={"q": "zz"}))

    # An area is somewhere to live and a place is somewhere to reach: each is listed apart.
    assert [area["name"] for area in found["areas"]] == ["Kindlewharf"]
    assert {place["name"] for place in found["places"]} >= {"Kindlewharf"}
    assert set(found["areas"][0]) == set(data(client.get("/v1/areas"))["areas"][0])
    assert found["areas"][0]["named"]["label"] == "Quillhaven 011"
    # The start of a word is enough, and every area that matches is given, best first.
    assert [area["name"] for area in begun["areas"]] == ["Osierholm", "Ostrel Vale"]
    assert [area["name"] for area in other_name["areas"]] == ["Dulcimer Green"]
    assert nothing == {"places": [], "areas": []}
    cut = data(client.post("/v1/places/search", json={"q": "os", "limit": 1}))
    assert [area["name"] for area in cut["areas"]] == ["Osierholm"]


def test_every_area_that_bears_one_name_is_found_by_it():
    # Two areas of one borough bear one name, and each says which side of it it is.
    loaded = release()
    first, second, *rest = loaded.neighbourhoods
    bearing = replace(
        loaded,
        neighbourhoods=(
            first.replace(name="Foxholt, north", aliases=("Foxholt",)),
            second.replace(name="Foxholt, south", aliases=("Foxholt",)),
            *rest,
        ),
    )
    with client_for(make_deps(release=bearing)) as client:
        found = data(client.post("/v1/places/search", json={"q": "foxholt"}))["areas"]

    assert [area["name"] for area in found] == ["Foxholt", "Foxholt, north", "Foxholt, south"]
    assert [area["area_id"] for area in found[1:]] == [first.area_id, second.area_id]


@pytest.mark.parametrize(
    "body", [{"q": "a"}, {"q": " a "}, {"q": "    "}, {"q": "x" * 81}, {"q": 7}, {}]
)
def test_a_search_needs_two_to_eighty_characters(client: TestClient, body: dict[str, Any]):
    refused = client.post("/v1/places/search", json=body)

    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "invalid_query")


# Routes 9 and 10.


def shared_between(first: InMemoryRelease, second: InMemoryRelease) -> tuple[Deps, Deps]:
    """Two services that share one store, as one service does before and after a release."""
    store = InMemoryShareStore()
    return make_deps(release=first, shares=store), make_deps(release=second, shares=store)


def test_a_shared_search_is_ranked_again_when_it_is_opened(client: TestClient):
    spec = searching()
    made = data(client.post("/v1/shares", json={"spec": wire(spec), "exact_destinations": True}))
    opened = data(client.get(f"/v1/shares/{made['share_id']}"))
    ranked = data(client.post("/v1/rank", json={"spec": wire(spec)}))

    assert opened["spec"] == wire(spec) and opened["spec_hash"] == spec_hash(spec)
    assert opened["stale"] is False and opened["original_release_id"] == "syn-2026-09-23-01"
    for field in ("scores", "ranked", "filtered", "unranked", "empty_spec"):
        assert opened[field] == ranked[field]
    assert (opened["areas_ranked"], opened["areas_listed"]) == (len(ranked["scores"]), 20)


def test_a_share_outlives_the_release_it_was_made_on():
    before = release()
    newer = before.manifest.replace(release_id="syn-2026-10-01-01")
    then, now = shared_between(before, replace(before, manifest=newer))

    made = data(client_for(then).post("/v1/shares", json={"spec": wire(searching())}))
    opened = client_for(now).get(f"/v1/shares/{made['share_id']}")

    found = data(opened)
    assert found["stale"] is True and found["original_release_id"] == "syn-2026-09-23-01"
    assert opened.json()["meta"]["release_id"] == "syn-2026-10-01-01"


def test_a_share_whose_place_has_gone_is_gone():
    before = release()
    without = tuple(place for place in before.places if place.place_id != WORKS)
    then, now = shared_between(before, replace(before, places=without))
    assert check_spec(searching(), now.release)

    made = data(client_for(then).post("/v1/shares", json={"spec": wire(searching())}))
    opened = client_for(now).get(f"/v1/shares/{made['share_id']}")

    assert (opened.status_code, opened.json()["error"]["code"]) == (410, "release_changed")
    assert opened.json()["error"]["fields"] == []


# Route 11.


def test_meta_gives_a_form_everything_it_needs(client: TestClient):
    found = data(client.get("/v1/meta"))

    assert found["release_id"] == "syn-2026-09-23-01" and found["synthetic"] is True
    assert found["built_at"] == "2026-09-23T00:00:00Z"
    # The features the release carries. Four of the catalogue's are in no release yet.
    carried = sorted(metric.feature_id for metric in release().metrics)
    assert [f["feature_id"] for f in found["features"]] == carried
    assert len(carried) == 109 and set(carried) < set(FeatureId)
    assert {t["tag_id"]: len(t["terms"]) for t in found["tags"]}["village_feel"] == 4
    assert found["catalogue_version"] == 14 and found["preview"] is False
    assert found["limits"]["cutoff_minutes"] == {"pt": 90, "cycle": 60, "walk": 60}
    assert found["limits"]["rent"] == {"minimum": 300, "maximum": 20000, "unit": 25}
    assert found["limits"]["max_text"] == 600
    [credit] = found["attributions"]
    assert credit["attribution"].endswith("It describes no real place.")
    # A default is a spec like any other: it can be sent straight back to be ranked.
    for tenure in ("rent", "buy"):
        assert found["defaults"][tenure]["tenure"] == tenure
        assert client.post("/v1/rank", json={"spec": found["defaults"][tenure]}).status_code == 200


def test_meta_says_that_no_language_model_reads_what_is_typed_where_none_does(
    client: TestClient,
):
    found = data(client.get(META))["reader"]

    assert found == {
        "model_reads": False,
        "provider": None,
        "company": None,
        "notice": RULES_NOTICE,
        "terms_url": None,
        "settings_sent": False,
    }
    assert "not sent to a language model" in found["notice"]
    assert not [terms.company for terms in TERMS.values() if terms.company in str(found)]


@pytest.mark.parametrize("provider", Provider, ids=lambda provider: provider.value)
@pytest.mark.parametrize("with_settings", [False, True], ids=["alone", "with settings"])
def test_meta_says_what_is_true_of_the_provider_that_reads(provider: Provider, with_settings: bool):
    terms = TERMS[provider]
    told = told_of(terms, with_settings)
    reads = reader_asking(FakeModelClient(model_output()), with_settings)

    found = data(client_for(make_deps(interpreter=reads, told=told)).get(META))["reader"]

    assert (found["model_reads"], found["provider"]) == (True, provider.value)
    assert (found["company"], found["settings_sent"]) == (terms.company, with_settings)
    # The notice, and the link to the company's own terms. No more is served.
    assert found["notice"] == terms.notice(with_settings)
    assert (SETTINGS in found["notice"], WORDS_ALONE in found["notice"]) == (
        with_settings,
        not with_settings,
    )
    assert found["terms_url"] == terms.terms_url
    assert sorted(found) == [
        "company",
        "model_reads",
        "notice",
        "provider",
        "settings_sent",
        "terms_url",
    ]
    told_by_the_company = f"What you type is sent to a language model run by {terms.company}, "
    assert found["notice"].startswith(told_by_the_company)
    assert "Do not type anything private." in found["notice"]
    assert "Burro itself keeps nothing of what you type." in found["notice"]
    # Nothing of the table of terms is served: nobody has checked it. Not how
    # long words are kept, whether they are used to train, or where they go.
    served = json.dumps(found)
    for question in Question:
        given = terms.answer(question)
        assert terms.says(question) not in served
        assert not given.answer or given.answer not in served
        assert not [quoted for quoted in given.rests_on if quoted in served]
    # Nothing of how the service is set is served: no key, no variable, no model's name.
    assert "API_KEY" not in str(found) and terms.model not in str(found)


def test_an_answer_that_tells_of_another_reader_is_never_said_to_stand():
    gemini, openai = (told_of(TERMS[p], with_settings=False) for p in list(Provider)[:2])
    reads = reader_asking(FakeModelClient(model_output()))
    tellings = {
        "rules": make_deps(),
        "gemini": make_deps(interpreter=reads, told=gemini),
        "openai": make_deps(interpreter=reads, told=openai),
        "gemini, with settings": make_deps(
            interpreter=reader_asking(FakeModelClient(model_output()), True),
            told=told_of(TERMS[Provider.GEMINI], with_settings=True),
        ),
    }
    tags = {name: client_for(deps).get(META).headers["etag"] for name, deps in tellings.items()}

    # One release, and a tag for each thing people can be told.
    assert len(set(tags.values())) == len(tellings)
    assert all(re.fullmatch(r'"syn-2026-09-23-01\.[0-9a-f]{8}"', tag) for tag in tags.values())
    for name, deps in tellings.items():
        client = client_for(deps)
        for held_by, tag in tags.items():
            answered = client.get(META, headers={"if-none-match": tag})
            # A browser that holds what another reader was told of is answered in full.
            assert answered.status_code == (304 if held_by == name else 200), (name, held_by)
            assert answered.headers["etag"] == tags[name]
        # The release alone is no longer enough to say that route 11 stands.
        assert client.get(META, headers={"if-none-match": LOADED}).status_code == 200
        # The routes that are of the release alone are tagged as they were.
        assert client.get("/v1/areas").headers["etag"] == LOADED


def test_meta_gives_the_vibes_the_release_carries_with_all_a_shelf_needs(client: TestClient):
    found = data(client.get("/v1/meta"))

    carried = release().vibes
    assert found["gritty_variant"] == "b"
    assert found["tags"] == [vibe.model_dump(mode="json") for vibe in carried]
    assert [t["tag_id"] for t in found["tags"]] == [
        t.tag_id.value for t in tags_of(GrittyVariant.B)
    ]
    shelf = [tag for tag in found["tags"] if tag["shelf_word"] is not None]
    assert [tag["shelf_word"] for tag in shelf] == [
        "leafy",
        "villagey",
        "lively",
        "quiet street",
        "period",
        "walkable",
        "near a big park",
    ]
    # Works and warehouses is the eleventh of the catalogue, and no release that carries
    # Gritty carries it. The two vibes that count who lived there come last.
    assert [tag["shelf_order"] for tag in found["tags"]] == [*range(1, 11), 12, 13, 14, 15]
    for tag in found["tags"]:
        assert tag["cannot_see"][0] == "One street or one home. An area is many streets."
        assert len(tag["cannot_see"]) > 1 and tag["meaning"]
        scale = tag["shape"] == "scale"
        assert (tag["low_end"] is not None) is (tag["high_end"] is not None) is scale
        assert (tag["shelf_toward"] is None) is (tag["shelf_word"] is None)
    ends = {t["tag_id"]: (t["low_end"], t["high_end"]) for t in found["tags"] if t["low_end"]}
    assert ends == {
        "pace": ("Calm", "Buzzy"),
        "built_age": ("Newer", "Historic"),
        "homes": ("Houses", "Flats"),
        "street_character": ("Polished", "Gritty"),
    }
    assert found["families"] == [
        {"family": "streets_homes", "label": "Streets and homes"},
        {"family": "pace_food", "label": "Pace and food"},
        {"family": "green", "label": "Green"},
        {"family": "daily_life", "label": "Daily life"},
        {"family": "who_lives_there", "label": "Who lives there, at the 2021 census"},
    ]
    assert found["limits"]["reason_min_utility"] == REASON_MIN_UTILITY == 0.5
    assert found["limits"]["trade_off_max_utility"] == TRADE_OFF_MAX_UTILITY == 0.35


def test_every_thing_a_form_shows_has_a_plain_name_of_a_few_words(client: TestClient):
    found = data(client.get("/v1/meta"))

    named = [*found["features"], *found["tags"]]
    assert len(named) == 123
    places = {area.name for area in release().neighbourhoods}
    for thing in named:
        short = thing["short_label"]
        assert 0 < len(short) <= 40 and not re.search(r"\d", short), short
        assert not [name for name in places if name in short]
    shorts = {f["feature_id"]: f["short_label"] for f in found["features"]}
    assert shorts["venue_evening_per_homes"] == "Pubs and bars"
    assert shorts["noise_exposure"] == "Less transport noise"


def built_from_land_use() -> InMemoryRelease:
    """The committed release as one that holds no recorded crime, and so carries no Gritty."""
    loaded = release()
    return replace(
        loaded,
        manifest=loaded.manifest.replace(gritty_variant=GrittyVariant.A),
        vibes=tags_of(GrittyVariant.A),
        tags=tuple(row for row in loaded.tags if row.tag_id is not TagId.STREET_CHARACTER),
    )


def test_which_way_gritty_is_built_is_the_releases_to_say():
    client = client_for(make_deps(release=built_from_land_use()))

    found = data(client.get("/v1/meta"))
    profile = data(client.get("/v1/areas/cindermoor"))
    listed = data(client.get("/v1/areas"))
    said = data(client.post("/v1/interpret", json={"text": "somewhere a bit gritty"}))

    assert found["gritty_variant"] == "a"
    carried = [tag["tag_id"] for tag in found["tags"]]
    assert len(carried) == 14 and "works_warehouses" in carried
    assert "street_character" not in carried
    for served in (profile["tags"], listed["bands"], profile["portrait"]["more"]):
        assert "street_character" not in str(served)
    assert "works_warehouses" in [row["tag_id"] for row in listed["bands"]]
    # The word is read as its place part alone, and the chip quotes the word.
    assert [edit["tag_id"] for edit in said["operations"]["tag_ops"]] == ["works_warehouses"]
    assert {"code": "word", "group": "tag_ops", "index": 0, "word": "gritty"} in said["assumptions"]
    assert "street_cleanliness" in said["unmet"]


def test_a_default_weights_only_what_the_release_can_rank():
    loaded = release()
    fewer = tuple(
        metric.replace(rankable=metric.feature_id is not FeatureId.STATION_WALK)
        for metric in loaded.metrics
        if metric.feature_id is not FeatureId.AIR_NO2
    )
    smaller = replace(loaded, metrics=fewer)
    found = data(client_for(make_deps(release=smaller)).get("/v1/meta"))

    for tenure in (Tenure.RENT, Tenure.BUY):
        served = PreferenceSpec.model_validate(found["defaults"][tenure.value])
        weighted_ids = {w.feature_id for w in served.weights}
        assert check_spec(served, smaller) == ()
        assert not weighted_ids & {FeatureId.STATION_WALK, FeatureId.AIR_NO2}
        assert FeatureId.PARK_PROXIMITY in weighted_ids
