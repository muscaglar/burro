"""Raw prompt text and destination strings are never written anywhere (ADR 0005).

Each test plants a canary, a string found nowhere else, in what a person would
type: the prompt, the place search, a destination's name. It then collects
every log record in full, every line as the service writes it, everything on
standard output and standard error, every call record and every response, and
asserts the canary is in none of them.

A test that only looked for the canary would pass if logging were broken. So
each also asserts what should be there: the event, the route template, the
exception's type.
"""

import errno
import json
import logging
import re
import threading
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from dataclasses import fields
from pathlib import Path
from typing import Any, get_args, get_origin

import pytest
from burro_api import logs
from burro_api.calls import CallRecord, CallStatus
from burro_api.deps import Deps
from burro_api.logs import configure_logging
from burro_api.reader import (
    ModelCapped,
    ModelError,
    ModelFailure,
    ModelInterpreter,
    ModelRefused,
    ModelTimeout,
)
from burro_api.wire import MAX_BODY_BYTES, ExplanationsBody
from burro_core import default_spec
from burro_core.explain import ExplainInput, TemplateExplainer
from burro_core.ids import AssumptionCode, InterpreterName, RejectReason, Tenure, UnmetCategory
from burro_core.interpret import InterpretRequest, InterpretResult
from burro_core.spec import PreferenceSpec, spec_hash
from burro_core.verify import Sentence
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from .support import (
    ACADEMY,
    CANARY,
    GROUPS,
    MODEL,
    NOW,
    SCHOOL,
    SCHOOL_COARSE,
    WORKS,
    FakeModelClient,
    Seen,
    assert_no_canary,
    budget,
    commute,
    make_deps,
    model_area,
    model_commute,
    model_output,
    model_tag,
    model_weight,
    release,
    renter,
    searching,
    watching,
    wire,
)

LIBRARY_LINE = {"at", "level", "event", "logger", "where", "exception", "errno"}
# A prompt that is plain, so that there are edits whose words could leak. The
# canary stands where a plain prompt may hold words nobody knows: after a cue.
PLAIN = f"I work at {CANARY}. Somewhere quiet, near a park."
# And one that is not, which holds the canary among words the reader does not
# know. Nothing of it is applied. What is noticed in it is offered, and what is
# made nothing of is pointed at, so that there are offsets that could leak.
PROMPT = (
    f"I work at {CANARY}. I want a quiet flat near a park. Or {CANARY} park for {CANARY} pounds."
)
JSON = {"content-type": "application/json"}
POSTS = (
    "/v1/interpret",
    "/v1/rank",
    "/v1/explanations",
    "/v1/compare",
    "/v1/places/search",
    "/v1/shares",
)

KINDS = ("budget", "commute", "weight", "tag", "area", "setting")
# Everything the line for a reading may hold (contract, section 10.1).
INTERPRET_LINE = {
    "request_id",
    "endpoint",
    "interpreter",
    # One of the four providers by name, or empty where the rules read.
    "provider",
    "model",
    "interpret_status",
    "call_status",
    "degraded",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "latency_ms",
    "edits",
    "rejections",
    "unmet",
    "assumptions",
}

Watch = Callable[..., Seen]
Clean = Callable[[Seen], str]


@pytest.fixture
def watch() -> Iterator[Watch]:
    """Start the app with logging set up as the service sets it up, and keep all that is logged."""
    with ExitStack() as stack:

        def start(deps: Deps | None = None) -> Seen:
            configure_logging()
            return stack.enter_context(watching(deps))

        yield start


@pytest.fixture
def clean(capsys: pytest.CaptureFixture[str]) -> Clean:
    """Assert the canary is nowhere, and give back what the service wrote to standard output."""

    def check(seen: Seen) -> str:
        out, err = capsys.readouterr()
        assert_no_canary(seen, out, err)
        return out

    return check


def by_a_model(answer: Any) -> ModelInterpreter:
    return ModelInterpreter(FakeModelClient(answer), model=MODEL, max_tokens=512, timeout_s=1)


def with_model(answer: Any) -> Deps:
    return make_deps(interpreter=by_a_model(answer), model_id=MODEL)


# The prompt.


def test_a_prompt_is_read_and_appears_nowhere_afterwards(watch: Watch, clean: Clean):
    seen = watch()
    read = seen.post("/v1/interpret", {"text": PLAIN})
    offered = seen.post("/v1/interpret", {"text": PROMPT})

    assert read.status_code == offered.status_code == 200
    # A workplace the release does not hold is asked about in both, plain or not.
    assert [r.json()["data"]["status"] for r in (read, offered)] == ["clarify", "clarify"]
    out = clean(seen)
    applied, nothing = seen.events("interpret")
    assert applied["interpreter"] == "rule" and applied["edits"]["tag_ops"] == 1
    # What was offered is not counted, named or pointed at: nothing was applied. The one
    # edit is the question, which carries no place and is turned away by the reducer.
    assert nothing["edits"] == dict.fromkeys(nothing["edits"], 0) | {"commute_ops": 1}
    assert nothing["rejections"] == {"unknown_place": 1}
    assert offered.json()["data"]["applied"] == []
    assert set(applied) == set(nothing) <= {*INTERPRET_LINE, "at", "level", "event"}
    # The service really did write its log, as JSON, to standard output.
    assert any(json.loads(row)["event"] == "interpret" for row in out.splitlines())


def test_interpret_result_holds_no_user_text(watch: Watch, clean: Clean):
    seen = watch()
    response = seen.post("/v1/interpret", {"text": PLAIN})

    data = response.json()["data"]
    # The name that matched nothing is asked about, and is not repeated.
    assert data["status"] == "clarify"
    assert data["clarify"][0]["options"] == []
    # Nor are the words an edit rests on: what is said of them is where they stand.
    assert {key for rests in data["rests_on"] for key in rests} == {
        "group",
        "index",
        "start",
        "end",
    }
    assert CANARY not in response.text.casefold()
    clean(seen)


def test_a_destination_the_model_names_is_asked_about_and_dropped(watch: Watch, clean: Clean):
    answer = model_output(
        commute_ops=[model_commute(destination_text=CANARY, words=f"I work at {CANARY}")]
    )
    seen = watch(with_model(answer))
    response = seen.post("/v1/interpret", {"text": PROMPT})

    data = response.json()["data"]
    assert data["interpreter"] == "model" and data["status"] == "suggest"
    assert data["operations"]["commute_ops"] == []
    # The release holds no such place, so the person is asked which. What is
    # served of the name is where it stands, and no word of it.
    [asks] = [offer for offer in data["suggestions"] if offer["asks_place"]]
    named = asks["named_at"]
    assert PROMPT[named["start"] : named["end"]] == CANARY and asks["options"] == []
    clean(seen)
    [line] = seen.events("interpret")
    assert line["model"] == MODEL and line["input_tokens"] == 812


def test_a_name_the_model_brought_itself_is_left_out_and_appears_nowhere(
    watch: Watch, clean: Clean
):
    # Names that are not in the person's words: the model's own, and the
    # person's words put in another order.
    answer = model_output(
        commute_ops=[
            model_commute(destination_text=f"the {CANARY} office", words=f"I work at {CANARY}"),
            model_commute(destination_text=f"{CANARY}ville", words=f"{CANARY}ville"),
        ],
        area_ops=[model_area("only", f"park {CANARY}", words=f"Or {CANARY} park")],
    )
    seen = watch(with_model(answer))
    response = seen.post("/v1/interpret", {"text": PROMPT})

    data = response.json()["data"]
    assert (data["status"], data["unmet"]) == ("suggest", ["other"])
    assert data["operations"]["commute_ops"] == [] and data["operations"]["area_ops"] == []
    clean(seen)
    [line] = seen.events("interpret")
    # How many edits were made is logged, and never what was left out or why.
    assert line["edits"] == {
        "budget_ops": 0,
        "commute_ops": 0,
        "weight_ops": 0,
        "tag_ops": 0,
        "area_ops": 0,
        "setting_ops": 0,
    }
    assert line["unmet"] == ["other"]


@pytest.mark.parametrize(
    ("failure", "status"),
    [
        (ModelTimeout(), CallStatus.TIMEOUT),
        (ModelCapped(), CallStatus.CAPPED),
        (ModelRefused(), CallStatus.REFUSED),
        (ModelError(), CallStatus.ERROR),
        # A failure that is not one of ours, with the prompt in its message.
        (RuntimeError(f"could not read: {PROMPT}"), CallStatus.ERROR),
    ],
)
def test_interpret_timeout_does_not_log_the_prompt(
    watch: Watch, clean: Clean, failure: Exception, status: CallStatus
):
    seen = watch(with_model(failure))
    response = seen.post("/v1/interpret", {"text": PROMPT})

    # The rules answered in the model's place. A model's failure is never a 5xx.
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["degraded"] is True and data["interpreter"] == "rule"
    clean(seen)
    [record] = seen.deps.calls.records(NOW)
    assert record.status is status and record.degraded and record.model == MODEL
    failures = seen.events("failure")
    if isinstance(failure, ModelFailure) and status is not CallStatus.ERROR:
        assert failures == []
    else:
        assert failures[0]["exception"] == type(failure).__name__


def test_an_answer_that_does_not_fit_the_schema_is_not_logged(watch: Watch, clean: Clean):
    seen = watch(with_model(json.dumps({"status": CANARY, CANARY: [PROMPT]})))
    response = seen.post("/v1/interpret", {"text": PROMPT})

    assert response.json()["data"]["degraded"] is True
    clean(seen)
    assert seen.events("failure")[0]["exception"] == "ModelError"


def test_an_interpreter_that_is_too_slow_is_not_waited_for(watch: Watch, clean: Clean):
    release_it = threading.Event()

    class Slow:
        name = InterpreterName.MODEL

        def interpret(self, request: InterpretRequest) -> InterpretResult:
            release_it.wait(5)
            raise RuntimeError(request.text)

    seen = watch(make_deps(interpreter=Slow(), model_id=MODEL, model_timeout_s=0.05))
    try:
        response = seen.post("/v1/interpret", {"text": PROMPT})
    finally:
        release_it.set()

    assert response.json()["data"]["degraded"] is True
    clean(seen)
    [record] = seen.deps.calls.records(NOW)
    assert record.status is CallStatus.TIMEOUT


# Validation.


def bad_bodies() -> list[Any]:
    spec = wire(searching())
    return [
        {CANARY: CANARY},
        [CANARY],
        CANARY,
        {"text": {"nested": CANARY}, "spec": CANARY, "operations": CANARY},
        {"text": PROMPT, "q": [CANARY], "limit": CANARY, "area_ids": [CANARY, CANARY]},
        {"text": PROMPT + "x" * 600, "q": CANARY * 20},
        {"text": PROMPT, "q": CANARY, "spec": spec | {CANARY: 1}},
        {"text": PROMPT, "q": CANARY, "spec": spec | {"tenure": CANARY}},
        {"text": PROMPT, "q": CANARY, "spec": spec | {"commutes": [{"place_id": CANARY}]}},
        {"text": PROMPT, "spec": spec, "exact_destinations": CANARY, "area_ids": CANARY},
        {"spec": spec, "operations": {"weight_ops": [{"feature_id": CANARY, CANARY: CANARY}]}},
        {"spec": spec | {"budget": {"amount": CANARY, "segment": CANARY}}, "area_ids": [1, 2]},
        # Words where a number belongs, which are refused before they are read as one.
        {
            "text": PROMPT,
            "q": CANARY,
            "limit": CANARY,
            "area_ids": ["syn-n0001", "syn-n0002"],
            "spec": spec | {"schema_version": CANARY, "commute_weight": f"0.5 {CANARY}"},
            "operations": {"weight_ops": [{"value": CANARY}], "budget_ops": [{"amount": CANARY}]},
        },
    ]


@pytest.mark.parametrize("path", POSTS)
def test_interpret_validation_failure_does_not_log_the_body(watch: Watch, clean: Clean, path: str):
    seen = watch()
    for body in bad_bodies():
        response = seen.post(path, body)
        assert response.status_code == 422, body
        assert response.json()["error"]["code"].startswith("invalid_")

    clean(seen)
    lines = seen.events("request")
    assert len(lines) == len(bad_bodies())
    assert {line["route"] for line in lines} == {path}
    assert {line["error_code"] for line in lines} <= {
        "invalid_request",
        "invalid_text",
        "invalid_spec",
        "invalid_operations",
        "invalid_compare",
        "invalid_query",
    }


def test_validation_error_response_does_not_echo_what_was_sent(watch: Watch, clean: Clean):
    seen = watch()
    spec = wire(searching()) | {"tenure": CANARY, CANARY: 1}
    spec["commutes"] = [{"place_id": CANARY, "mode": "pt", CANARY: {"deep": CANARY}}]
    response = seen.post("/v1/rank", {"spec": spec, "limit": 500})

    error = response.json()["error"]
    assert error["code"] == "invalid_spec"
    assert error["message"] == "The preference spec is not valid."
    found = {(field["path"], field["problem"]) for field in error["fields"]}
    # Paths and codes. The name of the field that should not be there is not given.
    assert ("spec.tenure", "not_allowed") in found
    assert ("spec.commutes[0].place_id", "bad_format") in found
    assert ("spec.commutes[0].max_minutes", "missing") in found
    assert ("spec.commutes[0]", "unknown_field") in found
    assert ("spec", "unknown_field") in found
    assert ("limit", "out_of_range") in found
    for field in error["fields"]:
        assert set(field) == {"path", "problem"}
    clean(seen)


@pytest.mark.parametrize("path", POSTS)
def test_a_malformed_body_is_refused_without_being_repeated(watch: Watch, clean: Clean, path: str):
    seen = watch()
    text = PROMPT.encode()
    sent = [
        (b'{"text": "' + text, JSON, 400, "malformed_json"),
        (b'{"text": "' + text + b'\xff\xfe"}', JSON, 400, "malformed_json"),
        (text, JSON, 400, "malformed_json"),
        # Nested too deep to be read at all.
        (b"[" * 9000 + text, JSON, 400, "malformed_json"),
        (b"", JSON, 422, "invalid_request"),
        (text, {"content-type": "text/plain"}, 415, "unsupported_media_type"),
        (text, {"content-type": f"application/{CANARY}"}, 415, "unsupported_media_type"),
        (b'{"text": "' + text * 400 + b'"}', JSON, 413, "body_too_large"),
    ]
    for content, headers, status, code in sent:
        response = seen.send("POST", path, content=content, headers=headers)
        error = response.json()["error"]
        assert (response.status_code, error["code"]) == (status, code)
        # An empty path is the body itself: there was none.
        nothing = [{"path": "", "problem": "missing"}]
        assert error["fields"] == (nothing if status == 422 else [])

    clean(seen)
    assert [line["status"] for line in seen.events("request")] == [s for _, _, s, _ in sent]
    assert {line["route"] for line in seen.events("request")} == {path}


def test_a_body_that_understates_its_length_is_still_refused(watch: Watch, clean: Clean):
    seen = watch()

    def chunks() -> Iterator[bytes]:
        # No length is sent with a body that arrives in pieces.
        yield b'{"text": "'
        for _ in range(MAX_BODY_BYTES // len(CANARY) + 1):
            yield CANARY.encode()
        yield b'"}'

    response = seen.send("POST", "/v1/interpret", content=chunks(), headers=JSON)

    assert response.status_code == 413
    clean(seen)


# What only a release can decide.


def test_a_place_or_an_area_the_release_does_not_have_is_not_named(watch: Watch, clean: Clean):
    seen = watch()
    unknown_place = wire(renter(commutes=(commute(f"syn-p{CANARY}"),)))
    unknown_area = wire(renter()) | {
        "areas": [{"area_id": f"syn-n{CANARY}", "rule": "exclude", "provenance": "stated"}]
    }
    known = ["syn-n0001", "syn-n0002"]
    for path in ("/v1/interpret", "/v1/rank", "/v1/explanations", "/v1/shares", "/v1/compare"):
        extra = {"text": PROMPT, "area_ids": known}
        body = {key: extra[key] for key in extra if key in _fields_of(path)}
        place = seen.post(path, body | {"spec": unknown_place})
        area = seen.post(path, body | {"spec": unknown_area})
        assert (place.status_code, place.json()["error"]["code"]) == (422, "unknown_place")
        assert place.json()["error"]["fields"] == [
            {"path": "spec.commutes[0].place_id", "problem": "unknown_place"}
        ]
        assert (area.status_code, area.json()["error"]["code"]) == (422, "unknown_area")

    compared = seen.post(
        "/v1/compare", {"area_ids": ["syn-n0001", f"syn-n{CANARY}"], "spec": wire(renter())}
    )
    assert (compared.status_code, compared.json()["error"]["code"]) == (404, "area_not_found")
    clean(seen)


def _fields_of(path: str) -> set[str]:
    return {"/v1/interpret": {"text"}, "/v1/compare": {"area_ids"}}.get(path, set())


def test_request_log_names_the_route_template_not_the_path(watch: Watch, clean: Clean):
    seen = watch()
    made = seen.post("/v1/shares", {"spec": wire(searching())}).json()["data"]["share_id"]
    asked = [
        ("GET", f"/v1/shares/{made}", 200, "/v1/shares/{share_id}"),
        ("GET", f"/v1/shares/{CANARY}", 404, "/v1/shares/{share_id}"),
        ("GET", "/v1/areas/alderwick", 200, "/v1/areas/{id_or_slug}"),
        ("GET", f"/v1/areas/{CANARY}", 404, "/v1/areas/{id_or_slug}"),
        ("GET", f"/v1/areas?near={CANARY}", 200, "/v1/areas"),
        # The census of an area takes nothing: a query is refused, and is in no line.
        ("GET", "/v1/areas/alderwick/census", 200, "/v1/areas/{id_or_slug}/census"),
        ("GET", f"/v1/areas/{CANARY}/census", 404, "/v1/areas/{id_or_slug}/census"),
        ("GET", f"/v1/areas/alderwick/census?{CANARY}=1", 422, "/v1/areas/{id_or_slug}/census"),
        ("POST", f"/v1/areas/{CANARY}/census", 405, "/v1/areas/{id_or_slug}/census"),
        # So does the household income of an area.
        ("GET", "/v1/areas/alderwick/income", 200, "/v1/areas/{id_or_slug}/income"),
        ("GET", f"/v1/areas/{CANARY}/income", 404, "/v1/areas/{id_or_slug}/income"),
        ("GET", f"/v1/areas/alderwick/income?{CANARY}=1", 422, "/v1/areas/{id_or_slug}/income"),
        ("POST", f"/v1/areas/{CANARY}/income", 405, "/v1/areas/{id_or_slug}/income"),
        ("GET", f"/v1/{CANARY}", 404, "unmatched"),
        ("GET", f"/{CANARY}/v1/meta", 404, "unmatched"),
        ("DELETE", f"/v1/areas/{CANARY}", 405, "/v1/areas/{id_or_slug}"),
        # A slash too many is no route. It is not sent on, with the path in a header.
        ("GET", f"/v1/shares/{made}/", 404, "unmatched"),
        ("GET", f"/v1/areas/{CANARY}/", 404, "unmatched"),
        ("POST", f"/v1/{CANARY}/", 404, "unmatched"),
        # A browser on a page that is not the web app, asking what it may send.
        ("OPTIONS", f"/v1/areas/{CANARY}", 405, "/v1/areas/{id_or_slug}"),
        (CANARY.upper(), "/v1/meta", 405, "/v1/meta"),
    ]
    headers = {
        "user-agent": CANARY,
        "x-request-id": CANARY,
        "cookie": f"id={CANARY}",
        "origin": f"https://{CANARY}.example",
        "referer": f"https://{CANARY}.example/{CANARY}",
        "access-control-request-method": CANARY,
        "access-control-request-headers": f"x-{CANARY}",
    }
    for method, path, status, _ in asked:
        answered = seen.send(method, path, headers=headers)
        assert answered.status_code == status
        assert "location" not in answered.headers

    out = clean(seen)
    lines = seen.events("request")[1:]
    assert [line["route"] for line in lines] == [template for *_, template in asked]
    assert lines[-1]["method"] == "OTHER"
    # Neither the share id nor the slug that was asked for.
    assert made not in out and "alderwick" not in out
    assert made not in json.dumps(seen.lines())


def test_what_a_browser_says_it_holds_is_compared_and_never_logged_or_sent_back(
    watch: Watch, clean: Clean
):
    seen = watch()
    gets = ("/v1/meta", "/v1/areas", "/v1/areas/geometry", "/v1/areas/alderwick")
    for path in gets:
        # The tag of the route, which for route 11 names what people are told as well.
        loaded = seen.send("GET", path).headers["etag"]
        assert loaded.startswith('"syn-2026-09-23-01') and CANARY not in loaded
        held = [CANARY, f'"{CANARY}"', f'W/"{CANARY}", {loaded}', f"{loaded}, {CANARY}", loaded]
        answered = [seen.send("GET", path, headers={"if-none-match": tag}) for tag in held]

        assert [r.status_code for r in answered] == [200, 200, 304, 304, 304]
        # What is sent back is the service's own tag, whatever was sent.
        assert {r.headers["etag"] for r in answered} == {loaded}
        assert {r.content for r in answered[2:]} == {b""}

    out = clean(seen)
    lines = seen.events("request")
    assert [line["status"] for line in lines] == [200, 200, 200, 304, 304, 304] * len(gets)
    # The line for an answer that stands is the line for any other, but for its status.
    assert {json.dumps(sorted(line)) for line in lines} == {json.dumps(sorted(lines[0]))}
    assert "etag" not in out.casefold() and "none_match" not in out.casefold()
    assert "alderwick" not in out


def test_the_name_of_a_place_is_in_an_answer_and_in_no_line(watch: Watch, clean: Clean):
    seen = watch()
    text = "I work at Cindermoor Works. I study at Wexmoor University."
    read = seen.post("/v1/interpret", {"text": text}).json()["data"]
    sent = {"spec": read["spec"]}
    ranked = seen.post("/v1/rank", sent).json()["data"]
    made = seen.post("/v1/shares", sent | {"exact_destinations": True}).json()["data"]
    opened = seen.send("GET", f"/v1/shares/{made['share_id']}").json()["data"]
    compared = seen.post("/v1/compare", sent | {"area_ids": ["syn-n0001", "syn-n0002"]})

    named = [{"name": "Cindermoor Works"}, {"name": "Wexmoor University"}]
    for found in (read, ranked, made, opened):
        assert [{"name": place["name"]} for place in found["places"]] == named
    # A comparison names the place of each journey, one to a row.
    rows = compared.json()["data"]["rows"]
    assert [{"name": row["place"]["name"]} for row in rows if row["place"]] == named
    out = clean(seen)
    # A name says where someone works as its id does, and is handled as one.
    written = out + json.dumps(seen.lines()) + str(seen.deps.calls.records(NOW))
    for said in ("Cindermoor", "Wexmoor", "University", "syn-p", "syn-n", made["share_id"]):
        assert said not in written, said
    assert not [name for name in (*logs.LOGGABLE, *CallRecord.model_fields) if "place" in name]


def test_what_a_browser_says_of_itself_is_neither_logged_nor_sent_back(watch: Watch, clean: Clean):
    web_app = "https://burro.example"
    seen = watch(make_deps(allowed_origins=(web_app,)))
    asking = {
        "origin": web_app,
        "access-control-request-method": "POST",
        "access-control-request-headers": f"content-type, x-{CANARY}",
        "referer": f"{web_app}/search/{CANARY}",
    }
    asked = seen.send("OPTIONS", "/v1/interpret", headers=asking)
    told = seen.post("/v1/interpret", {"text": PROMPT})
    called = seen.send("POST", "/v1/interpret", json={"text": PROMPT}, headers=asking)
    elsewhere = seen.send(
        "POST", "/v1/interpret", json={"text": PROMPT}, headers={"origin": f"https://{CANARY}"}
    )

    assert [r.status_code for r in (asked, told, called, elsewhere)] == [204, 200, 200, 200]
    # What is sent back is the entry of the list, and what may be sent is fixed text.
    assert asked.headers["access-control-allow-headers"] == "Content-Type"
    assert called.headers["access-control-allow-origin"] == web_app
    assert "access-control-allow-origin" not in elsewhere.headers
    out = clean(seen)
    # The origin is a header like any other: it is in no line, allowed or not.
    assert "burro.example" not in out and "origin" not in out.casefold()
    assert [(line["method"], line["route"], line["status"]) for line in seen.events("request")] == [
        ("OPTIONS", "/v1/interpret", 204),
        ("POST", "/v1/interpret", 200),
        ("POST", "/v1/interpret", 200),
        ("POST", "/v1/interpret", 200),
    ]


def test_a_stale_spec_is_put_right_without_the_place_being_named(watch: Watch, clean: Clean):
    stale = "syn-p9999"
    spec = wire(renter(commutes=(commute(stale), commute(WORKS))))
    removal = {
        "action": "remove",
        "place_id": stale,
        "mode": "unchanged",
        "max_minutes": 0,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "ui_edit",
    }
    edits: dict[str, list[Any]] = {
        f"{group}_ops": [] for group in ("budget", "weight", "tag", "area", "setting")
    }
    remove = edits | {"commute_ops": [removal]}
    keep = edits | {"commute_ops": [removal | {"action": "update", "max_minutes": 30}]}
    said = f"I no longer work at {CANARY}"
    gone = model_commute(action="remove", position=2, words=said)
    seen = watch(with_model(model_output(commute_ops=[gone])))

    ranked = seen.post("/v1/rank", {"spec": spec, "operations": remove})
    read = seen.post("/v1/interpret", {"text": f"{said}.", "spec": spec})
    kept = seen.post("/v1/rank", {"spec": spec, "operations": keep})

    assert [c["place_id"] for c in ranked.json()["data"]["spec"]["commutes"]] == [WORKS]
    # Nothing a model reads is applied, so words alone put no search right:
    # the control that takes the journey out does.
    for refused in (read, kept):
        assert (refused.status_code, refused.json()["error"]["code"]) == (422, "unknown_place")
        assert refused.json()["error"]["fields"] == [
            {"path": "spec.commutes[1].place_id", "problem": "unknown_place"}
        ]
        assert stale not in refused.text
    out = clean(seen)
    # A place is where someone works, whether or not the release still has it.
    written = out + json.dumps(seen.lines()) + str(seen.deps.calls.records(NOW))
    assert stale not in written and WORKS not in written


def test_what_is_withheld_from_a_model_is_withheld_in_silence(watch: Watch, clean: Clean):
    # A model that does everything it is told not to, in the person's own words.
    people = f"Lots of young families like the {CANARY}s"
    answer = model_output(
        commute_ops=[
            model_commute(destination_text=f"the {CANARY} office", words=f"I work at {CANARY}")
        ],
        weight_ops=[
            {
                "action": "set",
                "feature_id": "crime_violence_robbery",
                "value": 1.0,
                "step": "none",
                "direction": "default",
                "provenance": "stated",
                "words": "Somewhere safe",
            }
        ],
        tag_ops=[
            {
                "action": "set",
                "tag_id": "family_amenities",
                "value": 1.0,
                "step": "none",
                "toward": "default",
                "provenance": "stated",
                "words": people,
            }
        ],
        area_ops=[model_area("only", f"{CANARY}ton", words=f"like the {CANARY}ton")],
        policy_flags=["seek_group"],
    )
    seen = watch(with_model(answer))
    text = f"I work at {CANARY}. Somewhere safe. {people}."
    response = seen.post("/v1/interpret", {"text": text})

    data = response.json()["data"]
    assert (data["status"], data["notice"]) == ("policy_redirect", "neutral_places")
    # The place and the area were never named, and the tag is what was asked
    # about people. "Safe" names no crime, so the rules make no edit of it,
    # and what a model made of it is withheld with the rest.
    edits = data["operations"]
    assert edits["commute_ops"] == edits["area_ops"] == edits["tag_ops"] == []
    assert (edits["weight_ops"], data["rejected"]) == ([], [])
    assert data["spec"]["tags"] == [] and data["spec"]["weights"] == wire(renter())["weights"]
    clean(seen)
    [line] = seen.events("interpret")
    assert (line["interpret_status"], line["unmet"]) == ("policy_redirect", ["other"])
    assert line["rejections"] == {}


def test_what_is_withheld_for_doubt_is_withheld_in_silence(watch: Watch, clean: Clean):
    # A model that raises what the person turned round, in the person's own words.
    near = f"Nowhere near {CANARY} park or Cindermoor Works"
    answer = model_output(
        budget_ops=[
            {
                "action": "set",
                "tenure": "buy",
                "amount": 0,
                "segment": "flat",
                "strictness": "unchanged",
                "step": "none",
                "provenance": "stated",
                "words": "I'm not buying",
            }
        ],
        commute_ops=[
            model_commute(destination_text="Cindermoor Works", words=near),
            model_commute(destination_text=f"{CANARY} park", words=near),
        ],
        weight_ops=[
            {
                "action": "set",
                "feature_id": "park_proximity",
                "value": 1.0,
                "step": "none",
                "direction": "default",
                "provenance": "stated",
                "words": f"{CANARY} park",
            }
        ],
        area_ops=[model_area("only", "Wexmoor", words=f"I used to live in Wexmoor, {CANARY}")],
    )
    seen = watch(with_model(answer))
    text = f"I'm not buying. {near}. I used to live in "
    response = seen.post("/v1/interpret", {"text": f"{text}Wexmoor, {CANARY}"})

    data = response.json()["data"]
    assert (data["status"], data["unmet"]) == ("suggest", ["other"])
    assert data["operations"] == {f"{g}_ops": [] for g in KINDS} and data["applied"] == []
    out = clean(seen)
    [line] = seen.events("interpret")
    # How many edits were kept is logged. What was withheld, and why, is not.
    assert set(line["edits"].values()) == {0} and line["unmet"] == ["other"]
    assert set(line) <= {*INTERPRET_LINE, "at", "level", "event"}
    assert "wexmoor" not in out.casefold() and WORKS not in out


def test_an_answer_with_words_where_its_numbers_belong_is_not_logged(watch: Watch, clean: Clean):
    edit = model_commute(
        action="remove", position=f"1 {CANARY}", max_minutes=True, words=f"I work at {CANARY}"
    )
    seen = watch(with_model(model_output(commute_ops=[edit])))
    response = seen.post("/v1/interpret", {"text": PROMPT, "spec": wire(searching())})

    data = response.json()["data"]
    assert (data["degraded"], data["interpreter"]) == (True, "rule")
    assert [c["place_id"] for c in data["spec"]["commutes"]] == [WORKS]
    clean(seen)
    [failure] = seen.events("failure")
    # The type of what went wrong, which is code. Never its message, which quotes the answer.
    assert (failure["exception"], failure["causes"]) == ("ModelError", ["ValidationError"])
    [record] = seen.deps.calls.records(NOW)
    assert record.status is CallStatus.ERROR and record.degraded


def test_place_search_text_never_reaches_a_log(watch: Watch, clean: Clean):
    seen = watch()
    for q in (CANARY, f"{CANARY} road", f"Wexmoor {CANARY}", "Wexmoor"):
        assert seen.post("/v1/places/search", {"q": q}).status_code == 200

    out = clean(seen)
    # Nor does what was searched for, canary or not.
    assert "wexmoor" not in out.casefold()
    assert len(seen.events("request")) == 4


def test_unhandled_error_logs_the_type_and_not_the_message(watch: Watch, clean: Clean):
    class Broken:
        def add(self, record: CallRecord) -> None:
            raise ValueError(f"cannot keep a record of: {PROMPT}")

        def records(self, now: object) -> tuple[CallRecord, ...]:
            return ()

    seen = watch(make_deps(calls=Broken()))
    response = seen.post("/v1/interpret", {"text": PROMPT})

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "internal_error",
        "message": "Something went wrong on the server.",
        "fields": [],
    }
    clean(seen)
    [failure] = seen.events("failure")
    assert failure["exception"] == "ValueError"
    assert failure["route"] == "/v1/interpret"
    # Whoever watches the log for errors must see it.
    assert failure["level"] == "error"
    assert any(frame.endswith(":add") for frame in failure["frames"])
    [line] = seen.events("request")
    assert (line["status"], line["error_code"]) == (500, "internal_error")


def test_a_library_that_logs_what_it_was_given_is_cut_down_to_where_it_came_from(
    watch: Watch, capsys: pytest.CaptureFixture[str]
):
    watch()
    library = logging.getLogger("some.library")
    library.setLevel(logging.DEBUG)
    library.debug("request body: %s", PROMPT)
    library.warning("could not send %s", PROMPT)
    try:
        raise RuntimeError(PROMPT)
    except RuntimeError:
        library.exception("failed on " + PROMPT)

    out, err = capsys.readouterr()
    assert CANARY not in (out + err).casefold()
    lines = [json.loads(row) for row in out.splitlines()]
    # Nothing below a warning, and of the rest only where it came from.
    assert [line["level"] for line in lines] == ["warning", "error"]
    assert {line["event"] for line in lines} == {"library"}
    assert lines[1]["exception"] == "RuntimeError"
    assert all(set(line) <= LIBRARY_LINE for line in lines)


def test_a_server_that_cannot_start_says_what_kind_of_error_it_was(
    watch: Watch, capsys: pytest.CaptureFixture[str]
):
    watch()
    # As the server logs a port it may not listen on: the error itself, as the message.
    logging.getLogger("a.server").error(PermissionError(errno.EPERM, f"not permitted: {CANARY}"))

    out, _ = capsys.readouterr()
    [line] = [json.loads(row) for row in out.splitlines()]
    assert (line["exception"], line["errno"]) == ("PermissionError", errno.EPERM)
    assert CANARY not in out and set(line) <= LIBRARY_LINE


def test_a_field_that_is_not_on_the_list_cannot_be_logged():
    with pytest.raises(ValueError, match="not loggable: text") as refused:
        logs.event("interpret", text=PROMPT, status=200)
    assert CANARY not in str(refused.value)


# What is kept.


def _holds_no_free_text(annotation: Any, info: FieldInfo) -> bool:
    if annotation in (int, bool):
        return True
    if isinstance(annotation, type) and issubclass(annotation, str) and annotation is not str:
        return True  # an enum
    if annotation is str:
        return any(getattr(constraint, "pattern", None) for constraint in info.metadata)
    return False


# The hash of a spec.

README = (
    "Renting a 1 bed for about \N{POUND SIGN}1,700 a month, leafy, 35 minutes to Cindermoor Works"
)


def near_the_default(found: PreferenceSpec) -> Iterator[PreferenceSpec]:
    """Specs a person with the log could try: the default, with a journey, a budget and a tag.

    The reviewer tried a million of these in twenty seconds and found the
    workplace. This holds a few, the one that was searched for among them.
    """
    yield found
    yield renter()
    for place in release().places:
        for minutes in (30, 35, 40, 45):
            journey = found.commutes[0].replace(place_id=place.place_id, max_minutes=minutes)
            yield found.replace(commutes=(journey,))
            yield renter(commutes=(journey,))


def _ours(seen: Seen) -> list[dict[str, Any]]:
    """The lines the service wrote itself, without what is made anew for each: an id, the time."""
    made_anew = ("request_id", "at")
    return [
        {name: value for name, value in line.items() if name not in made_anew}
        for line in seen.lines()
        if line["event"] != "library"
    ]


def _kept(seen: Seen) -> list[dict[str, Any]]:
    records = [record.model_dump(mode="json") for record in seen.deps.calls.records(NOW)]
    return [{n: v for n, v in record.items() if n != "call_id"} for record in records]


def test_nothing_worked_out_from_a_spec_is_logged_or_kept(watch: Watch, clean: Clean):
    seen = watch()
    found = seen.post("/v1/interpret", {"text": README}).json()["data"]
    body = {"spec": found["spec"]}
    for path in ("/v1/explanations", "/v1/rank", "/v1/shares"):
        assert seen.post(path, body).status_code == 200
    # The plain hash is served with the sentences too, to the caller that holds the spec.
    explained = seen.responses[1].json()["data"]
    assert explained["spec_hash"] == found["spec_hash"]
    compared = seen.post("/v1/compare", body | {"area_ids": ["syn-n0001", "syn-n0002"]})
    assert compared.status_code == 200

    spec = PreferenceSpec.model_validate(found["spec"])
    assert [c.place_id for c in spec.commutes] == [WORKS] and spec.budget.amount == 1700
    tried = {spec_hash(candidate) for candidate in near_the_default(spec)}
    assert len(tried) > 300 and found["spec_hash"] in tried
    lines, records = _ours(seen), _kept(seen)
    written = json.dumps(seen.lines()) + str(seen.deps.calls.records(NOW))

    # Not the plain hash, which trying specs arrives at, and no hash of any
    # other kind: nothing in a line or a record is as long as one.
    assert [line["event"] for line in lines].count("request") == 5 and len(records) == 2
    assert not [plain for plain in tried if plain in written]
    assert not re.search(r"[0-9A-Fa-f]{20}|[0-9A-Za-z+/_-]{40}", json.dumps([lines, records]))
    assert not [name for row in (*lines, *records) for name in row if "spec" in name]
    assert not [name for name in (*logs.LOGGABLE, *CallRecord.model_fields) if "spec" in name]
    assert not [name for name in (*logs.LOGGABLE, *CallRecord.model_fields) if "hash" in name]
    # The plain hash is still in the response, to the client that holds the spec.
    assert found["spec_hash"] == spec_hash(spec)
    clean(seen)


def test_a_guess_at_a_spec_cannot_be_confirmed_from_the_log(watch: Watch, clean: Clean):
    # What a checker did with the keyed hash: read one line of somebody's
    # search, then post guesses until a new line held the same value.
    seen = watch()
    found = seen.post("/v1/interpret", {"text": README}).json()["data"]
    spec = PreferenceSpec.model_validate(found["spec"])
    guesses = [wire(guess) for guess in near_the_default(spec)][:24]
    assert found["spec"] in guesses and len({json.dumps(guess) for guess in guesses}) == 24

    routes = ("/v1/explanations", "/v1/rank", "/v1/shares")
    for guess in guesses:
        for path in routes:
            assert seen.post(path, {"spec": guess}).status_code == 200

    # The search that was made and every guess at it leave the same lines
    # and the same record, so nothing written tells one from another.
    lines, records = _ours(seen)[2:], _kept(seen)[1:]
    assert len(lines) == 24 * 4 and len(records) == 24
    assert {json.dumps(lines[n : n + 4]) for n in range(0, len(lines), 4)} == {
        json.dumps(lines[:4])
    }
    assert [line["event"] for line in lines[:4]] == ["explain", "request", "request", "request"]
    assert {json.dumps(record) for record in records} == {json.dumps(records[0])}
    clean(seen)


# What a line says of a reading depends on the words and the spec together.
DEPENDS_ON_THE_SPEC = ("edits", "rejections", "unmet", "assumptions")
READ_BY_THE_SPEC = [
    "I work at Cindermoor Works",
    "\N{POUND SIGN}1,500 a month",
    "a bit cheaper",
    "I want a detached house",
    "much more leafy",
    "no pubs",
]


def test_what_a_line_says_of_a_reading_is_counts_and_codes_and_nothing_of_the_spec(
    watch: Watch, clean: Clean
):
    # The checker's: the same words leave a different line when only the spec
    # differs. "I work at Cindermoor Works" assumes a mode where the spec does
    # not hold the place, and nothing where it does.
    seen = watch()
    specs = [
        renter(),
        searching(),
        searching(commutes=(commute(SCHOOL, 30), commute(WORKS, 40))),
        default_spec(Tenure.BUY),
        renter(budget=budget(None)),
    ]
    differed: set[str] = set()
    for text in READ_BY_THE_SPEC:
        before = len(_ours(seen))
        for spec in specs:
            assert seen.post("/v1/interpret", {"text": text, "spec": wire(spec)}).status_code == 200
        lines = [line for line in _ours(seen)[before:] if line["event"] == "interpret"]
        assert len(lines) == len(specs)
        for line in lines:
            differed |= {name for name in line if line[name] != lines[0][name]}
            # A count for each group, a count for each reason, and codes.
            assert set(line["edits"]) == set(GROUPS)
            assert set(line["rejections"]) <= {reason.value for reason in RejectReason}
            assert set(line["unmet"]) <= {category.value for category in UnmetCategory}
            assert set(line["assumptions"]) <= {code.value for code in AssumptionCode}
            counts = [*line["edits"].values(), *line["rejections"].values()]
            assert all(isinstance(count, int) and 0 <= count <= 24 for count in counts)

    # They do differ, and only in these four. None holds an id, a name or a
    # number of the spec, and none can be matched to a spec without the words,
    # which are in no line. Whether that is too much is an open point of the
    # contract (section 13): they are four entries of `LOGGABLE`.
    assert differed and differed <= set(DEPENDS_ON_THE_SPEC) | {"latency_ms"}
    records = _kept(seen)
    assert {json.dumps(record) for record in records} == {json.dumps(records[0])}
    written = json.dumps(seen.lines()) + str(seen.deps.calls.records(NOW))
    assert not re.search(r"syn-[pn][0-9]|[0-9A-Fa-f]{20}", written)
    for place in (WORKS, SCHOOL, "1500", "1800", "1,500"):
        assert place not in written
    clean(seen)


@pytest.mark.parametrize("name", ["spec_hash", "spec_mac", "spec", "spec_id", "search_id"])
def test_no_hash_of_a_spec_can_be_logged(name: str):
    assert name not in logs.LOGGABLE
    with pytest.raises(ValueError, match=f"not loggable: {name}"):
        logs.event("interpret", **{name: spec_hash(renter())})


def test_the_service_holds_no_key_and_nothing_a_spec_could_be_kept_under():
    import burro_api

    modules = {path.stem for path in Path(burro_api.__file__).parent.rglob("*.py")}
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in Path(burro_api.__file__).parent.rglob("*.py")
    )

    assert "keyed" not in modules and "spec_key" not in {f.name for f in fields(Deps)}
    assert "hmac" not in source and "spec_mac" not in source


def test_call_record_has_no_field_that_can_hold_free_text():
    for name, info in CallRecord.model_fields.items():
        assert _holds_no_free_text(info.annotation, info), name
    # Least of all a hash of the prompt: a short prompt can be guessed from its hash.
    assert not [name for name in CallRecord.model_fields if "prompt" in name or "text" in name]
    with pytest.raises(ValueError):
        CallRecord.model_validate(_call() | {"model": f"model {CANARY}"})
    with pytest.raises(ValueError):
        CallRecord.model_validate(_call() | {"spec_mac": ""})
    with pytest.raises(ValueError):
        CallRecord.model_validate(_call() | {"note": CANARY})


def _call() -> dict[str, Any]:
    return {
        "call_id": "11111111-1111-4111-8111-000000000001",
        "at": "2026-09-23T12:00:00Z",
        "endpoint": "interpret",
        "interpreter": "rule",
        "provider": "",
        "model": "",
        "status": "ok",
        "degraded": False,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "latency_ms": 3,
        "release_id": "syn-2026-09-23-01",
        "engine_version": "1.0.0",
    }


def test_a_call_is_recorded_for_each_interpretation_and_each_explanation(
    watch: Watch, clean: Clean
):
    seen = watch()
    seen.post("/v1/interpret", {"text": PLAIN})
    seen.post("/v1/explanations", {"spec": wire(searching())})
    seen.post("/v1/rank", {"spec": wire(searching())})

    first, second = seen.deps.calls.records(NOW)
    assert (first.endpoint, first.interpreter, first.status) == ("interpret", "rule", "clarify")
    assert (second.endpoint, second.interpreter, second.status) == ("explain", "template", "ok")
    assert first.at == second.at == "2026-09-23T12:00:00Z"
    assert (first.provider, second.provider) == ("", "")
    assert set(type(first).model_fields) == {
        "call_id",
        "at",
        "endpoint",
        "interpreter",
        "provider",
        "model",
        "status",
        "degraded",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "latency_ms",
        "release_id",
        "engine_version",
    }
    clean(seen)


def _text_fields(model: type[BaseModel], seen: set[type] | None = None) -> set[str]:
    """Every field, however deep, that is a plain string with no pattern to hold it."""
    seen = seen if seen is not None else set()
    if model in seen:
        return set()
    seen.add(model)
    found: set[str] = set()
    for name, info in model.model_fields.items():
        for part in _parts(info.annotation):
            if isinstance(part, type) and issubclass(part, BaseModel):
                found |= {f"{name}.{inner}" for inner in _text_fields(part, seen)}
            elif part is str and not _holds_no_free_text(str, info):
                found.add(name)
    return found


def _parts(annotation: Any) -> Iterator[Any]:
    if get_origin(annotation) is None:
        yield annotation
    for argument in get_args(annotation):
        yield from _parts(argument)


def test_explainer_input_holds_no_user_text(watch: Watch, clean: Clean):
    given: list[ExplainInput] = []

    class Recording(TemplateExplainer):
        def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
            given.append(area)
            return super().draft(area)

    # The route takes a spec and a number. There is nowhere to put a sentence.
    assert _text_fields(ExplanationsBody) == set()
    seen = watch(make_deps(explainer=Recording()))
    response = seen.post("/v1/explanations", {"spec": wire(searching()), "text": PROMPT})
    assert response.status_code == 422

    assert seen.post("/v1/explanations", {"spec": wire(searching())}).status_code == 200
    assert len(given) == 3
    assert set(ExplainInput.model_fields) == {"area_id", "facts", "contributions", "asks"}
    clean(seen)


# Shares.


def test_share_coarsens_destinations_unless_asked_not_to(watch: Watch, clean: Clean):
    seen = watch()
    spec = renter(commutes=(commute(SCHOOL, 30), commute(ACADEMY, 50), commute(WORKS, 40)))

    coarse = seen.post("/v1/shares", {"spec": wire(spec)}).json()["data"]
    exact = seen.post("/v1/shares", {"spec": wire(spec), "exact_destinations": True}).json()["data"]

    # The school and the academy both come to one station. The lower id is kept.
    assert coarse["coarsened"] is True
    assert [(c["place_id"], c["max_minutes"]) for c in coarse["spec"]["commutes"]] == [
        (SCHOOL_COARSE, 30),
        (WORKS, 40),
    ]
    stored = seen.deps.shares.get(coarse["share_id"])
    assert stored is not None
    assert {c.place_id for c in stored.spec.commutes} == {SCHOOL_COARSE, WORKS}
    assert SCHOOL not in stored.model_dump_json() and ACADEMY not in stored.model_dump_json()
    assert (
        seen.send("GET", f"/v1/shares/{coarse['share_id']}").json()["data"]["spec"]
        == (coarse["spec"])
    )

    assert exact["coarsened"] is False
    assert [c["place_id"] for c in exact["spec"]["commutes"]] == [WORKS, SCHOOL, ACADEMY]
    # A share holds the spec and when it was made, and nothing about who made it.
    assert set(type(stored).model_fields) == {
        "share_id",
        "spec",
        "coarsened",
        "original_release_id",
        "created_at",
    }
    clean(seen)


def test_share_id_is_not_derived_from_the_spec():
    from burro_api.deps import RandomIds

    with watching(make_deps(ids=RandomIds())) as seen:
        body = {"spec": wire(searching())}
        made = [seen.post("/v1/shares", body).json()["data"]["share_id"] for _ in range(20)]

    assert len(set(made)) == 20
    # 128 random bits, as 22 characters that are safe in a URL.
    assert all(len(share_id) == 22 for share_id in made)
    assert all(share_id.replace("-", "").replace("_", "").isalnum() for share_id in made)


# The words an edit rests on.

# A sentence the reader reads, and one it asks about: a prompt that is plain.
RESTING_PLAINLY = f"I want somewhere leafy. I work at {CANARY}."
# The same after a sentence only a model reads, which makes the prompt not plain.
RESTING = f"My {CANARY} lives for a proper brunch spot. {RESTING_PLAINLY}"
QUOTING = model_output(
    commute_ops=[model_commute(destination_text=CANARY, words=f"I work at {CANARY}")],
    weight_ops=[
        model_weight("venue_food_drink_per_homes", words=f"My {CANARY} lives for a proper brunch")
    ],
    tag_ops=[
        model_tag("leafy", words="I want somewhere leafy"),
        # Words the person never typed, and words of theirs from two sentences.
        model_tag("foodie", words=f"the {CANARY} of brunch"),
        model_tag("pace", words=f"somewhere leafy. I work at {CANARY}"),
    ],
)
# Nothing that is written may name a field for them, whatever it holds.
NEVER_WRITTEN = (
    "rests_on",
    "words",
    "start",
    "end",
    "offset",
    "span",
    "spans",
    "suggestions",
    "unread",
    "choices",
    "label",
    "places",
)


def wire_of_an_offer() -> tuple[str, ...]:
    """Every field of an offer as it is served. None of them can hold the person's words."""
    from burro_api.wire import Suggestion

    return tuple(Suggestion.model_fields)


def words_of(response: Any, text: str) -> dict[str, str]:
    """The words each edit rests on, as the caller finds them in the text it sent."""
    return {
        f"{r['group']} {r['index']}": text[r["start"] : r["end"]]
        for r in response.json()["data"]["rests_on"]
    }


READ_BY_THE_RULES = {"commute_ops 0": f"work at {CANARY}", "tag_ops 0": "leafy"}
# What a model read is offered, and each offer says where its words stand.
OFFERED_BY_A_MODEL = {
    "feature:venue_food_drink_per_homes": [f"My {CANARY} lives for a proper brunch"],
    # A scale the model named for words either side of a full stop stands beside it.
    "tag:leafy": ["I want somewhere leafy", f"somewhere leafy. I work at {CANARY}", "leafy"],
    "commute": [f"I work at {CANARY}", CANARY],
}


def stretches_of(response: Any, text: str) -> tuple[dict[str, list[str]], list[str]]:
    """The words of each suggestion and each unread stretch, as the caller finds them."""
    data = response.json()["data"]
    noticed = {
        found["target"]: [text[span["start"] : span["end"]] for span in found["spans"]]
        for found in data["suggestions"]
    }
    return noticed, [text[span["start"] : span["end"]] for span in data["unread"]]


def assert_where_the_words_stand_is_written_nowhere(seen: Seen) -> None:
    lines = seen.lines()
    records = [record.model_dump(mode="json") for record in seen.deps.calls.records(NOW)]
    for written in (*lines, *records):
        assert not [name for name in written if name in NEVER_WRITTEN], written
    assert not [
        name for name in (*logs.LOGGABLE, *CallRecord.model_fields) if name in NEVER_WRITTEN
    ]
    for line in seen.events("interpret"):
        assert set(line) <= {*INTERPRET_LINE, "at", "level", "event"}
        # What a line holds of the edits is how many there were in each group.
        assert set(line["edits"]) == set(GROUPS)
        assert all(isinstance(count, int) for count in line["edits"].values())


@pytest.mark.parametrize(
    ("reader", "text"), [("rule", RESTING_PLAINLY), ("model", RESTING)], ids=["rule", "model"]
)
def test_the_words_an_edit_rests_on_are_returned_as_offsets_and_written_nowhere(
    watch: Watch, clean: Clean, reader: str, text: str
):
    seen = watch(with_model(QUOTING) if reader == "model" else None)
    response = seen.post("/v1/interpret", {"text": text})

    data = response.json()["data"]
    assert (data["interpreter"], data["degraded"]) == (reader, False)
    # The caller holds the text, and is told where in it each edit's words stand.
    if reader == "rule":
        assert words_of(response, text) == READ_BY_THE_RULES
        # Every edit says which words it rests on, the one that is asked about among them.
        assert len(READ_BY_THE_RULES) == len(data["applied"]) + len(data["rejected"])
        assert [r["reason"] for r in data["rejected"]] == ["unknown_place"]
    else:
        # Nothing of a model's is applied. What it read is offered, by where the words stand.
        assert data["rests_on"] == data["applied"] == data["rejected"] == []
        assert stretches_of(response, text)[0] == OFFERED_BY_A_MODEL
    # The words themselves are in no response, no line and no record.
    clean(seen)
    assert_where_the_words_stand_is_written_nowhere(seen)
    [line] = seen.events("interpret")
    assert line["unmet"] == (["other"] if reader == "model" else [])


# What was noticed, and what nothing was made of.

# A place, an area and an amount beside the canary, in words that are not plain.
NOTICED = (
    f"My {CANARY} works at Pellam Infirmary, not {CANARY} Wexmoor. "
    f"Pubs are so {CANARY}. Maybe \N{POUND SIGN}1,450 a month, {CANARY}?"
)
# What may be said of a place is its name in the release, and only in an answer.
NAMED = ("Pellam", "Infirmary", "Wexmoor", "syn-p0028", "syn-n0023", "1450", "1,450")


@pytest.mark.parametrize("reader", ["rule", "model"])
def test_what_was_noticed_and_what_was_left_unread_are_offsets_and_written_nowhere(
    watch: Watch, clean: Clean, reader: str
):
    seen = watch(with_model(model_output()) if reader == "model" else None)
    response = seen.post("/v1/interpret", {"text": f"  {NOTICED}"})

    data = response.json()["data"]
    assert (data["interpreter"], data["status"]) == (reader, "suggest")
    # Words were left unread, and that is said whoever read.
    unmet = ["other"]
    assert data["unmet"] == unmet
    assert data["operations"] == {f"{g}_ops": [] for g in KINDS} and data["rests_on"] == []
    # The caller holds the text, and is told where in it each thing was noticed.
    noticed, unread = stretches_of(response, f"  {NOTICED}")
    assert noticed == {
        "commute": ["Pellam Infirmary"],
        "area": ["Wexmoor"],
        "feature:venue_evening_per_homes": ["Pubs"],
        "budget": ["\N{POUND SIGN}1,450 a month"],
    }
    # The canary is what nothing was made of, and the answer points at it.
    assert len([stretch for stretch in unread if CANARY in stretch]) == 4
    # It holds where the words stand, and no word of them.
    for found in data["suggestions"]:
        assert set(found) == set(wire_of_an_offer())
        assert {key for span in found["spans"] for key in span} == {"start", "end"}
        assert set(found["shown"]) == {"start", "end"} and found["named_at"] is None
        assert {key for choice in found["choices"] for key in choice} == {
            "id",
            "direction",
            "label",
            "guess",
            "operations",
        }
    assert {key for span in data["unread"] for key in span} == {"start", "end"}
    assert [found["label"] for found in data["suggestions"]] == [
        "Pellam Infirmary",
        "Wexmoor",
        "Pubs and bars",
        "A budget of \N{POUND SIGN}1,450 a month",
    ]
    out = clean(seen)
    assert_where_the_words_stand_is_written_nowhere(seen)
    # Nor is what was noticed: a place says where someone works, in words or as an id.
    written = out + json.dumps(seen.lines()) + str(seen.deps.calls.records(NOW))
    assert not [name for name in NAMED if name in written]
    [line] = seen.events("interpret")
    assert (line["interpret_status"], line["unmet"]) == ("suggest", unmet)
    assert set(line["edits"].values()) == {0} and line["assumptions"] == []
    [record] = seen.deps.calls.records(NOW)
    assert record.status is CallStatus.SUGGEST


def test_what_a_line_says_of_a_prompt_does_not_tell_what_was_noticed_in_it(
    watch: Watch, clean: Clean
):
    seen = watch()
    texts = [
        "Pubs are so noisy",
        f"My {CANARY} works at Pellam Infirmary",
        f"cross Cindermoor off my {CANARY}",
        f"Pubs? parks? a station? {CANARY}? Wexmoor? \N{POUND SIGN}900?",
    ]
    for text in texts:
        assert seen.post("/v1/interpret", {"text": text}).json()["data"]["suggestions"]

    # However much was noticed, and whatever it was, the line is the same.
    lines = [line for line in _ours(seen) if line["event"] == "interpret"]
    assert len(lines) == len(texts)
    assert {json.dumps(line | {"latency_ms": 0}) for line in lines} == {
        json.dumps(lines[0] | {"latency_ms": 0})
    }
    records = _kept(seen)
    assert {json.dumps(record) for record in records} == {json.dumps(records[0])}
    clean(seen)


@pytest.mark.parametrize(
    ("failure", "status"),
    [
        (ModelTimeout(), CallStatus.TIMEOUT),
        (ModelCapped(), CallStatus.CAPPED),
        (ModelRefused(), CallStatus.REFUSED),
        (ModelError(), CallStatus.ERROR),
        (RuntimeError(f"could not read: {RESTING}"), CallStatus.ERROR),
        # An answer that quotes the person and does not fit the schema.
        (json.dumps(QUOTING | {"status": CANARY}), CallStatus.ERROR),
        (
            json.dumps(QUOTING | {"tag_ops": [model_tag("leafy", words=[RESTING])]}),
            CallStatus.ERROR,
        ),
        (
            json.dumps(QUOTING | {"tag_ops": [model_tag("leafy", words=RESTING * 9)]}),
            CallStatus.ERROR,
        ),
        (json.dumps(QUOTING | {"rests_on": [{"words": RESTING}]}), CallStatus.ERROR),
        (json.dumps(QUOTING)[:-40], CallStatus.ERROR),
    ],
    ids=range(10),
)
def test_where_the_words_stand_is_written_nowhere_when_a_model_fails(
    watch: Watch, clean: Clean, failure: Exception | str, status: CallStatus
):
    seen = watch(with_model(failure))
    plainly = seen.post("/v1/interpret", {"text": RESTING_PLAINLY})
    response = seen.post("/v1/interpret", {"text": RESTING})
    ruled = watch().post("/v1/interpret", {"text": RESTING})

    # A plain prompt is the rules' to read, and no model was asked about it.
    assert plainly.json()["data"]["degraded"] is False
    assert words_of(plainly, RESTING_PLAINLY) == READ_BY_THE_RULES
    # Of a prompt that is not plain they say what they noticed, and what they did not read.
    data = response.json()["data"]
    assert response.status_code == 200 and data["degraded"] is True
    # Nothing is applied. The one edit is the question of which place was meant.
    assert words_of(response, RESTING) == {"commute_ops 0": f"work at {CANARY}"}
    assert data["applied"] == [] and data["status"] == "clarify"
    assert data["suggestions"] == ruled.json()["data"]["suggestions"] != []
    assert data["unread"] == ruled.json()["data"]["unread"] != []
    noticed, unread = stretches_of(response, RESTING)
    assert noticed == {"tag:leafy": ["leafy"]}
    assert len([stretch for stretch in unread if CANARY in stretch]) == 1
    clean(seen)
    assert_where_the_words_stand_is_written_nowhere(seen)
    first, second = seen.deps.calls.records(NOW)
    assert (first.interpreter, first.degraded) == ("rule", False)
    # The rules answered in the model's place, and the call is on record as what it was.
    assert second.status is status and second.degraded


def test_where_the_words_stand_is_written_nowhere_when_the_route_itself_fails(
    watch: Watch, clean: Clean
):
    class Broken:
        def add(self, record: CallRecord) -> None:
            raise ValueError(f"cannot keep a record of: {RESTING}")

        def records(self, now: object) -> tuple[CallRecord, ...]:
            return ()

    stale = wire(renter(commutes=(commute("syn-p9999"),)))
    seen = watch(with_model(QUOTING))
    broken = watch(make_deps(interpreter=by_a_model(QUOTING), model_id=MODEL, calls=Broken()))
    refused = seen.post("/v1/interpret", {"text": RESTING, "spec": stale})
    failed = broken.post("/v1/interpret", {"text": RESTING})

    # The words were read, and then the spec was refused or the service failed.
    # An error holds a code and paths, and nothing of what was read.
    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "unknown_place")
    assert (failed.status_code, failed.json()["error"]["code"]) == (500, "internal_error")
    for response in (refused, failed):
        assert set(response.json()) == {"meta", "error"}
        assert set(response.json()["error"]) == {"code", "message", "fields"}
        assert not [name for name in NEVER_WRITTEN if name in response.text]
    for watched in (seen, broken):
        clean(watched)
        assert_where_the_words_stand_is_written_nowhere(watched)


def test_no_other_route_takes_or_returns_where_the_words_stand(watch: Watch, clean: Clean):
    seen = watch()
    read = seen.post("/v1/interpret", {"text": RESTING_PLAINLY}).json()["data"]
    offered = seen.post("/v1/interpret", {"text": RESTING}).json()["data"]
    assert read["rests_on"] and offered["suggestions"] and offered["unread"]
    spec = read["spec"] | {"commutes": []}
    served_by_route_1_alone = ("rests_on", "suggestions", "unread")
    bodies = {
        "/v1/rank": {"spec": spec},
        "/v1/explanations": {"spec": spec},
        "/v1/compare": {"spec": spec, "area_ids": ["syn-n0001", "syn-n0002"]},
        "/v1/places/search": {"q": "Wexmoor"},
        "/v1/shares": {"spec": spec},
    }
    for path, body in bodies.items():
        answered = seen.post(path, body)
        assert answered.status_code == 200, path
        assert not [name for name in served_by_route_1_alone if name in answered.text], path
        # Sent back to a route that does not take it, it is refused, and not repeated.
        for extra in (
            {"rests_on": read["rests_on"]},
            {"suggestions": offered["suggestions"]},
            {"unread": offered["unread"]},
            {"words": RESTING},
        ):
            refused = seen.post(path, body | extra)
            assert (refused.status_code, refused.json()["error"]["fields"]) == (
                422,
                [{"path": "", "problem": "unknown_field"}],
            )
    inside = seen.post("/v1/rank", {"spec": spec | {"rests_on": read["rests_on"]}})
    within = seen.post("/v1/rank", {"spec": spec | {"unread": offered["unread"]}})
    assert inside.status_code == within.status_code == 422
    # Nor does route 1 take them back with the next sentence.
    again = seen.post("/v1/interpret", {"text": "leafy", "unread": offered["unread"]})
    assert again.status_code == 422

    # A share is the one thing that is stored, and it stores the spec and no more.
    made = seen.post("/v1/shares", {"spec": spec}).json()["data"]
    stored = seen.deps.shares.get(made["share_id"])
    opened = seen.send("GET", f"/v1/shares/{made['share_id']}").text
    gets = ("/v1/meta", "/v1/areas", "/v1/areas/alderwick", "/v1/areas/geometry", "/healthz")
    assert stored is not None
    for name in served_by_route_1_alone:
        assert name not in stored.model_dump_json() and name not in opened
        assert not [path for path in gets if name in seen.send("GET", path).text]
    clean(seen)
    assert_where_the_words_stand_is_written_nowhere(seen)


@pytest.mark.parametrize("name", NEVER_WRITTEN)
def test_where_the_words_stand_cannot_be_logged_or_kept_about_a_call(name: str):
    assert name not in logs.LOGGABLE and name not in CallRecord.model_fields
    with pytest.raises(ValueError, match=f"not loggable: {name}") as refused:
        logs.event("interpret", **{name: "3 to 9"})
    assert "3" not in str(refused.value)
    with pytest.raises(ValueError):
        CallRecord.model_validate(_call() | {name: 3})


def test_what_a_model_is_sent_and_what_it_answers_are_in_no_repr():
    # A failure is logged by its type and its frames, and a debugger prints a
    # repr. Neither may hold the words a model copied from the person.
    from burro_api.reader import ModelOutput

    parsed = ModelOutput.model_validate(QUOTING)
    shown = repr(parsed) + str(parsed) + repr(parsed.tag_ops) + repr(parsed.commute_ops[0])
    request = InterpretRequest(text=RESTING, spec=renter(), release=release())

    assert CANARY not in shown and CANARY not in repr(request) + str(request)
    assert CANARY in parsed.model_dump_json()  # it does hold them: that is what is hidden
