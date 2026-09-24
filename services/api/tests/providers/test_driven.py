"""The service as it starts, driven with a stand-in where the provider would be.

Five states: no provider, a provider that reads, one that will not read a
sentence, one that is slow, and one that is broken. For each: what the person
is shown, that what they typed went as they typed it or went nowhere, and
that no line and no record holds a word of it. No call is made to any
provider.
"""

import json
import threading
from collections.abc import Callable, Iterator

import pytest
from burro_api import logs
from burro_api.app import create_app, deps_from
from burro_api.logs import JsonFormatter
from burro_api.providers.base import Request, Response
from burro_api.providers.choose import choose
from burro_api.providers.terms import TERMS, Provider, Question
from burro_api.settings import Settings
from fastapi.testclient import TestClient

from ..support import LOOP, model_output
from .cases import CASES, KEY_TEXT, KEYED, Sender, all_of, listening

GEMINI = CASES[0]
# Two made-up words in mixed case, found nowhere else.
MARK = "Quillfeather Zebrano"
# Not plain, so that the rules leave words unread and a model is asked. It
# holds what a person might well type of themselves.
TEXT = f"Honestly, 30 minutes to Cindermoor Works. I work nights at {MARK} and I am unwell"
OFF: dict[str, str] = {}
ON = {
    "BURRO_MODEL_PROVIDER": "gemini",
    "GEMINI_API_KEY": KEY_TEXT,
    "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
    "BURRO_MODEL_TIMEOUT_S": "0.2",
}
LET_GO = threading.Event()


def reads(request: Request) -> Response:
    return Response(200, json.dumps(GEMINI.whole(json.dumps(model_output()))).encode())


def refuses(request: Request) -> Response:
    return Response(200, json.dumps(GEMINI.refusal()).encode())


def is_slow(request: Request) -> Response:
    LET_GO.wait(5)
    return reads(request)


def is_broken(request: Request) -> Response:
    # The body of an error can repeat the request. It is never read.
    return Response(500, request.body)


def raises(request: Request) -> Response:
    raise ConnectionResetError(request.body.decode())


STATES: dict[str, tuple[dict[str, str], Callable[[Request], Response]]] = {
    "off": (OFF, reads),
    "on": (ON, reads),
    "refusing": (ON, refuses),
    "slow": (ON, is_slow),
    "broken": (ON, is_broken),
    "broken, and says so in words": (ON, raises),
}
# What the person is shown in each: who read, whether the rules answered in a
# model's place, whether the model would not read, and how the call is counted.
SHOWN = {
    "off": ("rule", False, False, "suggest"),
    "on": ("model", False, False, "suggest"),
    "refusing": ("rule", True, True, "refused"),
    "slow": ("rule", True, False, "timeout"),
    "broken": ("rule", True, False, "error"),
    "broken, and says so in words": ("rule", True, False, "error"),
}


class Driven:
    """One state of the service, driven once: what was served, written, kept and sent."""

    def __init__(self, env: dict[str, str], answers: Callable[[Request], Response]) -> None:
        self.send = Sender(answers)
        # Every record that any logger writes, at any level, from the start of the service.
        with listening() as records:
            deps = deps_from(Settings.from_env(env), choose(env, send=self.send))
            client = TestClient(create_app(deps), raise_server_exceptions=True)
            if LOOP:
                client.portal = LOOP[0]
            self.meta = client.get("/v1/meta")
            self.read = client.post("/v1/interpret", json={"text": TEXT})
            self.lines = [json.loads(JsonFormatter().format(record)) for record in records]
            self.written = "\n".join(
                [JsonFormatter().format(record) + all_of(record) for record in records]
            )
        self.calls = deps.calls.records(deps.clock.now())


@pytest.fixture(params=STATES, ids=list(STATES))
def driven(request: pytest.FixtureRequest) -> Iterator[tuple[str, Driven]]:
    LET_GO.clear()
    try:
        yield request.param, Driven(*STATES[request.param])
    finally:
        LET_GO.set()


def test_in_every_state_the_person_is_answered_and_is_told_who_read(driven: tuple[str, Driven]):
    state, found = driven

    # Never a 5xx, whatever the provider does.
    assert (found.meta.status_code, found.read.status_code) == (200, 200)
    data = found.read.json()["data"]
    assert (
        data["interpreter"],
        data["degraded"],
        data["model_refused"],
        found.calls[0].status.value,
    ) == SHOWN[state]
    # What the rules noticed is offered in every state, and nothing is applied by itself.
    [offer] = data["suggestions"]
    assert offer["target"] == "commute"
    journeys = [edit for way in offer["choices"] for edit in way["operations"]["commute_ops"]]
    assert [edit["max_minutes"] for edit in journeys] == [30]
    assert data["applied"] == []


def test_in_every_state_the_notice_says_who_reads_and_nothing_of_the_company_as_fact(
    driven: tuple[str, Driven],
):
    state, found = driven
    reader = found.meta.json()["data"]["reader"]

    if state == "off":
        assert reader["model_reads"] is False and reader["terms_url"] is None
        assert "not sent to a language model" in reader["notice"]
    else:
        assert (reader["model_reads"], reader["company"]) == (True, "Google")
        assert "sent to a language model run by Google, to be read" in reader["notice"]
        assert "Do not type anything private." in reader["notice"]
        assert "Burro itself keeps nothing of what you type." in reader["notice"]
        assert reader["terms_url"] == TERMS[Provider.GEMINI].terms_url
    for terms in TERMS.values():
        assert not [q for q in Question if terms.says(q) in json.dumps(reader)]


def test_what_is_typed_is_sent_as_it_was_typed_or_is_not_sent(driven: tuple[str, Driven]):
    state, found = driven

    if state == "off":
        assert found.send.requests == []
        return
    # Once, to the one host, and with nothing taken out of it or put in its place.
    [request] = found.send.requests
    assert request.host == GEMINI.host
    turn = json.loads(GEMINI.user_in(json.loads(request.body)))
    assert turn == {"request": TEXT}


def test_in_no_state_does_a_line_or_a_record_hold_a_typed_word(driven: tuple[str, Driven]):
    _, found = driven
    kept = "\n".join(record.model_dump_json() for record in found.calls)

    for written in (found.written, kept):
        folded = written.casefold()
        assert MARK.casefold() not in folded and "unwell" not in folded
        assert "cindermoor" not in folded and "honestly" not in folded
        assert KEYED not in folded
    # Nor anything worked out from one: a line of ours is an event and fields from the list.
    for line in found.lines:
        if line["event"] != "library":
            assert set(line) - {"at", "level", "event"} <= logs.LOGGABLE, line["event"]


def test_a_refusal_is_said_in_the_line_of_its_call_and_in_no_line_of_its_own(
    driven: tuple[str, Driven],
):
    state, found = driven
    [read] = [line for line in found.lines if line["event"] == "interpret"]

    assert read["call_status"] == SHOWN[state][3]
    assert read["provider"] == ("" if state == "off" else "gemini")
    # Nothing counts refusals, and nothing reads the record of calls to write a line.
    assert "model_refused" not in {line["event"] for line in found.lines}
    assert not [line for line in found.lines if "refusals" in line]
