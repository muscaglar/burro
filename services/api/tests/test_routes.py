"""The routes of the contract, driven through the app on the committed synthetic release."""

import copy
import re
from dataclasses import replace
from functools import cache
from typing import Any, cast

import pytest
from burro_api.app import deps_from
from burro_api.claude import ClaudeInterpreter
from burro_api.deps import Deps
from burro_api.routes.common import default_for
from burro_api.settings import Settings
from burro_api.stores import InMemoryShareStore
from burro_api.wire import BODIES, CompareStatus
from burro_core import ENGINE_VERSION, apply, check_spec, rank, spec_hash
from burro_core.catalogue import FEATURES, TAGS, default_direction
from burro_core.ids import (
    Direction,
    FeatureId,
    FilterReason,
    InterpreterName,
    OpsGroup,
    Provenance,
    TagId,
    Tenure,
    UnrankedReason,
)
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.release import InMemoryRelease
from burro_core.spec import FeatureWeight, PreferenceSpec, TagWeight
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .support import (
    MODEL,
    NOW,
    WORKS,
    FakeModelClient,
    budget,
    client_for,
    commute,
    make_deps,
    model_commute,
    model_output,
    release,
    renter,
    searching,
    wire,
)

GETS = ("/v1/areas", "/v1/areas/geometry", "/v1/areas/syn-n0001", "/v1/meta")
OF_THE_RELEASE = GETS


@pytest.fixture
def client() -> TestClient:
    return client_for(make_deps())


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
        ("/v1/explanations", {"spec": spec}),
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


@pytest.mark.parametrize("synthetic", [True, False])
def test_every_response_carries_the_synthetic_flag(synthetic: bool):
    loaded = release()
    told = replace(loaded, manifest=loaded.manifest.replace(synthetic=synthetic))
    client = client_for(make_deps(release=told))
    flag = "true" if synthetic else "false"
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
        assert response.json()["meta"] == {
            "release_id": "syn-2026-09-23-01",
            "engine_version": ENGINE_VERSION,
            "synthetic": synthetic,
        }
    # The health check says nothing about the release, but it too carries the flag.
    health = client.get("/healthz")
    assert health.json() == {"ok": True} and health.headers["x-burro-synthetic"] == flag


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
        assert headers["cache-control"] == "public, max-age=3600"
        assert headers["etag"] == '"syn-2026-09-23-01"'
    kept_out = [client.post(path, json=body) for path, body in posts()]
    kept_out += [client.get(f"/v1/shares/{made['share_id']}"), client.get("/v1/areas/nowhere")]
    for response in kept_out:
        assert response.headers["cache-control"] == "no-store"
        assert "etag" not in response.headers


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
    client = client_for(deps)
    made = client.post("/v1/shares", json={"spec": wire(searching())}).json()["data"]
    broken = client_for(replace(deps, calls=Unkept()))
    huge = b'{"text": "' + b"x" * 20_000 + b'"}'
    as_json = sent | {"content-type": "application/json"}
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
            "access-control-expose-headers": "X-Burro-Synthetic, X-Request-Id",
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
        "access-control-expose-headers": "X-Burro-Synthetic, X-Request-Id",
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
    asked = ClaudeInterpreter(model, model=MODEL, max_tokens=512, timeout_s=1.0)
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
    assert {"code": "mode", "group": "commute_ops", "index": 0} in found["assumptions"]


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
        # A sentence the reader does not read, with characters that are two
        # units long in UTF-16, and then one it reads.
        "  \N{DECIDUOUS TREE}\N{DECIDUOUS TREE} trees!\nI want somewhere leafy  ",
        "caf\N{LATIN SMALL LETTER E WITH ACUTE}s? \N{REGIONAL INDICATOR SYMBOL LETTER G}"
        "\N{REGIONAL INDICATOR SYMBOL LETTER B}!\nI want somewhere leafy",
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


def test_an_interpreter_cannot_point_outside_the_text_or_at_an_edit_it_did_not_make():
    text = "somewhere leafy"

    class Wild:
        name = InterpreterName.CLAUDE

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


def test_a_second_sentence_edits_the_spec_that_is_sent_with_it(client: TestClient):
    first = data(client.post("/v1/interpret", json={"text": "work at Cindermoor Works"}))
    second = data(
        client.post("/v1/interpret", json={"text": "much more leafy", "spec": first["spec"]})
    )

    assert [c["place_id"] for c in second["spec"]["commutes"]] == [WORKS]
    # A thing named for the first time is worth a half, however it is asked for.
    assert second["spec"]["tags"] == [{"tag_id": "leafy", "weight": 0.5, "provenance": "stated"}]


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

    assert {r["reason"] for r in found["rejected"]} == {"crime_needs_explicit_request"}
    assert not [w for w in found["spec"]["weights"] if w["feature_id"].startswith("crime")]


# Route 2.


def test_ranking_over_the_wire_is_the_ranking_core_gives(client: TestClient):
    spec = searching()
    found = data(client.post("/v1/rank", json={"spec": wire(spec), "limit": 5}))

    expected = rank(spec, release())
    assert found["spec_hash"] == expected.spec_hash == spec_hash(spec)
    assert found["scores"] == [
        {"area_id": area.area_id, "score": area.score} for area in expected.ranked
    ]
    assert found["ranked"] == [area.model_dump(mode="json") for area in expected.ranked[:5]]
    assert found["unranked"] == [u.model_dump(mode="json") for u in expected.unranked]
    assert found["empty_spec"] is False
    every = found["scores"] + found["filtered"] + found["unranked"]
    assert len({row["area_id"] for row in every}) == 24


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


def test_words_can_put_a_stale_spec_right_when_a_model_reads_them():
    gone = model_commute(action="remove", position=2, words="I no longer work there")
    answer = model_output(commute_ops=[gone])
    asked = ClaudeInterpreter(FakeModelClient(answer), model=MODEL, max_tokens=512, timeout_s=1.0)
    deps = make_deps(interpreter=asked, model_id=MODEL)
    body = {"text": "I no longer work there", "spec": wire(stale_place())}

    found = data(client_for(deps).post("/v1/interpret", json=body))
    ruled = client_for(make_deps()).post("/v1/interpret", json=body)

    # The places are in id order, so the one the release has dropped is the second.
    assert [c["place_id"] for c in found["spec"]["commutes"]] == [WORKS]
    # The rules never remove a commute from words, so with them it stays refused.
    assert (ruled.status_code, ruled.json()["error"]["code"]) == (422, "unknown_place")
    # The call was made, so it is on record, whether or not the spec could then be ranked.
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
        ("commute", 0.9),
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
        for cell in row["cells"]:
            scored = {c.component: c for c in by_area[cell["area_id"]].contributions}
            assert cell["utility"] == scored[row["component"]].utility
            assert cell["contribution"] == scored[row["component"]].contribution
            if cell["value"] is not None or cell["percentile"] is not None:
                fact = served[cell["fact_id"]]
                assert fact["area_id"] == cell["area_id"] and fact["sources"] and fact["as_of"]
    [journey] = [row for row in found["rows"] if row["component"] == "commute"]
    for cell in journey["cells"]:
        [leg] = by_area[cell["area_id"]].legs
        assert cell["value"] == leg.minutes and cell["percentile"] is None


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
    assert set(areas[0]) == {"area_id", "slug", "name", "borough", "centroid", "rankable"}
    assert shapes["type"] == "FeatureCollection"
    assert [shape["id"] for shape in shapes["features"]] == [area["area_id"] for area in areas]
    for shape in shapes["features"]:
        assert shape["properties"] == {"area_id": shape["id"]}
        assert shape["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_an_area_is_found_by_its_id_or_its_slug(client: TestClient):
    by_id = client.get("/v1/areas/syn-n0004").json()
    by_slug = client.get("/v1/areas/dulcimer-green").json()

    assert by_id == by_slug
    profile = by_id["data"]
    assert profile["area"]["name"] == "Dulcimer Green"
    assert len(profile["features"]) == 23 and len(profile["tags"]) == 12
    assert {n["area_id"] for n in profile["neighbours"]} == set(profile["area"]["neighbours"])
    assert profile["stations"] and profile["cost"]
    # Built with no spec: nothing about a journey or a budget.
    assert {fact["kind"] for fact in profile["facts"]} == {
        "area",
        "feature",
        "tag",
        "cost",
        "station",
    }
    assert client.get("/v1/areas/Dulcimer%20Green").status_code == 404


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
    assert [f["feature_id"] for f in found["features"]] == sorted(FeatureId)
    assert {t["tag_id"]: len(t["terms"]) for t in found["tags"]}["village_feel"] == 5
    assert found["limits"]["cutoff_minutes"] == {"pt": 90, "cycle": 60, "walk": 60}
    assert found["limits"]["rent"] == {"minimum": 300, "maximum": 20000, "unit": 25}
    assert found["limits"]["max_text"] == 600
    [credit] = found["attributions"]
    assert credit["attribution"].endswith("It describes no real place.")
    # A default is a spec like any other: it can be sent straight back to be ranked.
    for tenure in ("rent", "buy"):
        assert found["defaults"][tenure]["tenure"] == tenure
        assert client.post("/v1/rank", json={"spec": found["defaults"][tenure]}).status_code == 200


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
