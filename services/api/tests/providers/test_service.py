"""The service with an adapter under its reader: what a person is answered when a provider fails.

No test here reaches a provider. Each adapter is given a function that
answers in the provider's place.
"""

import json
from typing import Any

import pytest
from burro_api.calls import CallRecord
from burro_api.logs import LOGGABLE, JsonFormatter
from burro_api.providers.base import PATIENCE, REST_S, Response
from burro_api.providers.choose import told_of
from burro_api.providers.terms import TERMS, Provider
from burro_api.reader import ModelInterpreter

from ..support import NOW, client_for, make_deps
from .cases import (
    CASES,
    KEYED,
    MAX_TOKENS,
    TIMEOUT_S,
    TYPED,
    Case,
    Sender,
    answering,
    key,
    listening,
)

each = pytest.mark.parametrize("case", CASES, ids=str)

# Not plain, so that the rules leave words unread and a model is asked.
TEXT = "Honestly, 30 minutes to Cindermoor Works"


def told(case: Case) -> Any:
    return told_of(TERMS[case.provider], with_settings=False)


def served(case: Case, send: Sender) -> dict[str, Any]:
    """What route 1 answers, and keeps about the call, when the adapter is answered by `send`."""
    reader = ModelInterpreter(case.made(send), case.model, MAX_TOKENS, TIMEOUT_S)
    deps = make_deps(interpreter=reader, told=told(case), model_id=case.model)
    with listening() as records:
        answered = client_for(deps).post("/v1/interpret", json={"text": TEXT})
        lines = [json.loads(JsonFormatter().format(record)) for record in records]
    assert answered.status_code == 200
    [call] = deps.calls.records(deps.clock.now())
    [line] = [line for line in lines if line["event"] == "interpret"]
    return {"data": answered.json()["data"], "call": call, "line": line}


@each
@pytest.mark.parametrize(("status", "counted"), [(504, "timeout"), (429, "capped"), (500, "error")])
def test_what_an_adapter_fails_with_is_what_the_route_counts(case: Case, status: int, counted: str):
    found = served(case, Sender(Response(status)))

    # The rules answer in the model's place, and the call is on record as what it was.
    assert found["data"]["degraded"] is True and found["data"]["interpreter"] == "rule"
    assert found["call"].status.value == counted
    # What the rules offer is served, though the model gave nothing.
    [offer] = found["data"]["suggestions"]
    journeys = [edit for way in offer["choices"] for edit in way["operations"]["commute_ops"]]
    assert [edit["max_minutes"] for edit in journeys] == [30]


@each
def test_what_a_provider_would_not_read_the_rules_read_and_the_person_is_told(case: Case):
    # The provider's own refusal, as its documents show one. It arrives as a success.
    found = served(case, answering(case.refusal()))

    assert found["data"]["model_refused"] is True
    assert found["data"]["degraded"] is True and found["data"]["interpreter"] == "rule"
    assert (found["call"].status.value, found["line"]["call_status"]) == ("refused", "refused")
    # What the rules offer is served, as it is where no model reads.
    [offer] = found["data"]["suggestions"]
    journeys = [edit for way in offer["choices"] for edit in way["operations"]["commute_ops"]]
    assert [edit["max_minutes"] for edit in journeys] == [30]


@each
def test_a_refusal_is_said_in_the_line_of_its_call_and_in_no_line_of_its_own(case: Case):
    send = answering(case.refusal())
    reader = ModelInterpreter(case.made(send), case.model, MAX_TOKENS, TIMEOUT_S)
    deps = make_deps(interpreter=reader, told=told(case), model_id=case.model)

    with listening() as records:
        sent = {"text": f"{TEXT}. I work at {TYPED}"}
        assert client_for(deps).post("/v1/interpret", json=sent).status_code == 200
        written = [json.loads(JsonFormatter().format(record)) for record in records]

    assert TYPED not in json.dumps(written) and KEYED not in json.dumps(written)
    # The line every call writes says that it was refused, and by which provider.
    # No line is written for a refusal alone, and nothing counts them: whoever
    # runs the service counts the lines.
    ours = [line for line in written if line["event"] != "library"]
    assert sorted(line["event"] for line in ours) == ["interpret", "request"]
    [line] = [line for line in ours if line["event"] == "interpret"]
    assert line["level"] == "info"
    assert (line["call_status"], line["provider"]) == ("refused", case.provider.value)
    assert "refusals" not in LOGGABLE


@each
def test_a_call_to_a_model_is_on_record_with_its_provider_and_its_model(case: Case):
    found = served(case, Sender(Response(500)))

    assert (found["call"].provider, found["call"].model) == (case.provider.value, case.model)
    assert (found["line"]["provider"], found["line"]["model"]) == (case.provider.value, case.model)
    assert found["line"]["interpreter"] == found["call"].interpreter.value != "rule"


def test_a_call_the_rules_read_names_no_provider():
    deps = make_deps()
    with listening() as records:
        assert client_for(deps).post("/v1/interpret", json={"text": TEXT}).status_code == 200
        lines = [json.loads(JsonFormatter().format(record)) for record in records]

    [call] = deps.calls.records(NOW)
    [line] = [line for line in lines if line["event"] == "interpret"]
    assert (call.provider, call.model, call.interpreter.value) == ("", "", "rule")
    assert (line["provider"], line["model"]) == ("", "")


def test_the_provider_of_a_call_is_one_of_the_four_or_none():
    kept = served(CASES[0], Sender(Response(500)))["call"].model_dump()

    for provider in ("", *(provider.value for provider in Provider)):
        assert CallRecord.model_validate(kept | {"provider": provider}).provider == provider
    for unfit in ("google", "Gemini", "gemini ", f"key-{KEYED}", "gemini,openai", "*"):
        with pytest.raises(ValueError):
            CallRecord.model_validate(kept | {"provider": unfit})


class Hands:
    """A clock a test moves by hand."""

    def __init__(self) -> None:
        self.at = 1_000.0

    def __call__(self) -> float:
        return self.at


@each
def test_one_line_says_that_a_provider_is_left_alone_each_time_it_begins_to_be(case: Case):
    # After three answers in a row that will not mend themselves the adapter
    # asks nothing for a while. Whoever runs the service is told once, by
    # the provider's name and nothing of any call.
    clock = Hands()
    send = Sender(Response(401))
    reader = ModelInterpreter(case.client(key(), send, clock), case.model, MAX_TOKENS, TIMEOUT_S)
    client = client_for(make_deps(interpreter=reader, told=told(case), model_id=case.model))

    def ask() -> list[dict[str, Any]]:
        with listening() as records:
            answered = client.post("/v1/interpret", json={"text": f"{TEXT}. I work at {TYPED}"})
            written = [json.loads(JsonFormatter().format(record)) for record in records]
        assert answered.status_code == 200 and answered.json()["data"]["degraded"] is True
        assert TYPED not in json.dumps(written) and KEYED not in json.dumps(written)
        return [line for line in written if line["event"] == "model_resting"]

    said = [ask() for _ in range(PATIENCE + 2)]

    # Nothing until the third refusal, one line then, and none while it rests.
    assert [len(lines) for lines in said] == [0] * (PATIENCE - 1) + [1, 0, 0]
    [line] = said[PATIENCE - 1]
    assert line == {
        "at": line["at"],
        "event": "model_resting",
        "level": "warning",
        "provider": case.provider.value,
    }
    # While it rests nothing is sent, and the rules read.
    assert len(send.requests) == PATIENCE
    # One call is let through once the rest is over. It is refused, and the line is written again.
    clock.at += REST_S + 1
    assert [len(lines) for lines in (ask(), ask())] == [1, 0]
    assert len(send.requests) == PATIENCE + 1


@pytest.mark.parametrize("status", [429, 500, 504])
def test_a_provider_that_may_mend_itself_is_never_said_to_be_left_alone(status: int):
    # A cap may lift within seconds, and a fault of the provider's own may pass.
    case = CASES[0]
    send = Sender(Response(status))
    reader = ModelInterpreter(case.made(send), case.model, MAX_TOKENS, TIMEOUT_S)
    client = client_for(make_deps(interpreter=reader, told=told(case), model_id=case.model))

    with listening() as records:
        for _ in range(PATIENCE + 2):
            assert client.post("/v1/interpret", json={"text": TEXT}).status_code == 200

    assert "model_resting" not in [record.msg for record in records]
    assert len(send.requests) == PATIENCE + 2
