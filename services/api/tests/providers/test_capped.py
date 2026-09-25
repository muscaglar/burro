"""The service as it starts, with its cap on calls to a model.

Two settings, each with a default that always applies: how many calls a
minute, and how many a day. Nought means the model is never called, and
people are then told that the rules read. A key alone still turns nothing on,
and what turns nothing on counts nothing (ADR 0032).

No test here reaches a provider. The adapter is given a function that answers
in the provider's place.
"""

import json
from typing import Any

import pytest
import uvicorn
from burro_api.app import create_app, deps_from
from burro_api.cap import CAPPED
from burro_api.cli import main
from burro_api.logs import JsonFormatter
from burro_api.providers.base import Response
from burro_api.providers.choose import BY_RULES, NOT_USED, Refusal, choose
from burro_api.reader import ModelInterpreter
from burro_api.settings import (
    DEFAULT_CALLS_PER_DAY,
    DEFAULT_CALLS_PER_MINUTE,
    MOST_CALLS_PER_DAY,
    MOST_CALLS_PER_MINUTE,
    Settings,
)
from burro_core import RuleInterpreter
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ..support import LOOP, model_output
from .cases import CASES, KEY_TEXT, KEYED, Sender, all_of, listening

GEMINI = CASES[0]
A_MINUTE = "BURRO_MODEL_CALLS_PER_MINUTE"
A_DAY = "BURRO_MODEL_CALLS_PER_DAY"
# Two made-up words in mixed case, found nowhere else.
MARK = "Vexelmoor Quandrith"
# Not plain, so that the rules leave words unread and a model is asked.
TEXT = f"Honestly, 30 minutes to Cindermoor Works. I work nights at {MARK}"
ON = {
    "BURRO_MODEL_PROVIDER": "gemini",
    "GEMINI_API_KEY": KEY_TEXT,
    "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
}


def reads() -> Sender:
    """A provider that reads every sentence it is sent, and keeps count of them."""
    return Sender(Response(200, json.dumps(GEMINI.whole(json.dumps(model_output()))).encode()))


class Started:
    """The service as it starts with `env`, with every line it writes from then on."""

    def __init__(self, env: dict[str, str], send: Sender | None = None) -> None:
        self.send = send or reads()
        self.records: list[Any] = []
        with listening() as records:
            self.deps = deps_from(Settings.from_env(env), choose(env, send=self.send))
            self.client = TestClient(create_app(self.deps), raise_server_exceptions=True)
            if LOOP:
                self.client.portal = LOOP[0]
            self.began = list(records)

    def ask(self, times: int = 1, text: str = TEXT) -> list[dict[str, Any]]:
        """What route 1 answers to the same sentence, so many times over."""
        found: list[dict[str, Any]] = []
        with listening() as records:
            for _ in range(times):
                answered = self.client.post("/v1/interpret", json={"text": text})
                assert answered.status_code == 200
                found.append(answered.json()["data"])
            self.records += records
        return found

    def told(self) -> dict[str, Any]:
        """What the service tells the website of who reads what is typed."""
        answered = self.client.get("/v1/meta")
        assert answered.status_code == 200
        return answered.json()["data"]["reader"]

    def lines(self, event: str) -> list[dict[str, Any]]:
        written = [
            json.loads(JsonFormatter().format(record)) for record in (*self.began, *self.records)
        ]
        return [line for line in written if line["event"] == event]


# The two settings.


def test_with_nothing_set_the_cap_is_thirty_calls_a_minute_and_two_thousand_a_day():
    settings = Settings.from_env({})

    assert (settings.model_calls_per_minute, settings.model_calls_per_day) == (30, 2000)
    assert (DEFAULT_CALLS_PER_MINUTE, DEFAULT_CALLS_PER_DAY) == (30, 2000)
    # Set and left empty, each is its default and never no cap at all.
    empty = Settings.from_env({A_MINUTE: "", A_DAY: ""})
    assert (empty.model_calls_per_minute, empty.model_calls_per_day) == (30, 2000)


@pytest.mark.parametrize(
    ("set_to", "read"),
    [("0", 0), ("1", 1), ("7", 7), ("007", 7), (" 12 ", 12), (str(MOST_CALLS_PER_MINUTE), 600)],
)
def test_each_cap_is_read_from_the_environment_as_a_whole_number(set_to: str, read: int):
    settings = Settings.from_env({A_MINUTE: set_to, A_DAY: set_to})

    assert (settings.model_calls_per_minute, settings.model_calls_per_day) == (read, read)


def test_each_cap_has_a_ceiling_of_its_own():
    assert (MOST_CALLS_PER_MINUTE, MOST_CALLS_PER_DAY) == (600, 100_000)
    most = Settings.from_env({A_MINUTE: "600", A_DAY: "100000"})
    assert (most.model_calls_per_minute, most.model_calls_per_day) == (600, 100_000)
    for over in ({A_MINUTE: "601"}, {A_DAY: "100001"}):
        with pytest.raises(ValidationError):
            Settings.from_env(over)


# A value that is not a whole number from nought to the ceiling. Each holds a marker, or
# is a number that the line must not repeat.
UNFIT = [
    "-1",
    "1.5",
    "30.0",
    "1e3",
    "1_000",
    "+5",
    "0x10",
    " ",
    "thirty",
    "30 a minute",
    "\N{ARABIC-INDIC DIGIT THREE}",
    "99999999999999999999",
    "2000000",
    f"as many as {KEYED}",
    # A key that was set where a number belongs.
    KEY_TEXT,
]


@pytest.mark.parametrize("variable", [A_MINUTE, A_DAY])
@pytest.mark.parametrize("set_to", UNFIT)
def test_a_cap_that_is_not_in_its_form_is_refused_and_is_not_repeated(variable: str, set_to: str):
    with pytest.raises(ValidationError) as refused:
        Settings.from_env({variable: set_to})

    # What the error says, however it comes to be printed. The command line prints none of it.
    said = str(refused.value) + repr(refused.value)
    assert KEYED not in said.casefold()
    assert set_to.strip() == "" or set_to.strip() not in said


@pytest.mark.parametrize("variable", [A_MINUTE, A_DAY])
@pytest.mark.parametrize("set_to", ["-1", "2000000", f"as many as {KEYED}", KEY_TEXT])
def test_a_cap_that_is_not_in_its_form_stops_the_service_as_it_starts_with_one_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    variable: str,
    set_to: str,
):
    def never_runs(app: object, **how: object) -> None:
        raise AssertionError("the service started")

    monkeypatch.setattr(uvicorn, "run", never_runs)
    monkeypatch.setenv(variable, set_to)
    for name, value in ON.items():
        monkeypatch.setenv(name, value)

    assert main(["serve"]) == 2

    out, err = capsys.readouterr()
    assert out == ""
    assert err == "error: a setting in the environment is not in the form it needs\n"


# What the service does with them.


def test_the_service_hands_its_reader_the_caps_of_its_settings():
    started = Started(ON | {A_MINUTE: "2", A_DAY: "50"})

    answered = started.ask(5)

    assert isinstance(started.deps.interpreter, ModelInterpreter)
    assert [data["interpreter"] for data in answered] == ["model", "model", "rule", "rule", "rule"]
    assert [data["degraded"] for data in answered] == [False, False, True, True, True]
    # No more than the cap reached the provider.
    assert len(started.send.requests) == 2
    assert [line["reason"] for line in started.lines(CAPPED)] == ["calls_per_minute"]


def test_with_nothing_set_for_the_caps_the_defaults_hold():
    started = Started(ON)

    answered = started.ask(DEFAULT_CALLS_PER_MINUTE + 2)

    assert len(started.send.requests) == DEFAULT_CALLS_PER_MINUTE == 30
    assert [data["degraded"] for data in answered] == [False] * 30 + [True] * 2


def test_with_a_model_on_people_are_told_of_the_provider_and_with_a_cap_at_nought_of_the_rules():
    on = Started(ON).told()
    assert (on["model_reads"], on["provider"], on["company"]) == (True, "gemini", "Google")
    assert "sent to a language model run by Google" in on["notice"]

    for nought in ({A_MINUTE: "0"}, {A_DAY: "0"}, {A_MINUTE: "0", A_DAY: "0"}):
        started = Started(ON | nought)
        off = started.told()

        # Nothing is ever sent, so people are not told that anything is.
        assert (off["model_reads"], off["provider"], off["company"]) == (False, None, None)
        assert off["notice"] == BY_RULES.notice and off["terms_url"] is None
        assert started.deps.told is BY_RULES and started.deps.model_id == ""
        assert isinstance(started.deps.interpreter, RuleInterpreter)


@pytest.mark.parametrize("nought", [{A_MINUTE: "0"}, {A_DAY: "0"}], ids=["a minute", "a day"])
def test_with_a_cap_at_nought_the_model_is_never_called_and_one_line_says_why(
    nought: dict[str, str],
):
    started = Started(ON | nought)

    answered = started.ask(3)

    assert started.send.requests == []
    # The rules read, as they do where no model is set. Nothing answered in a model's place.
    assert [(data["interpreter"], data["degraded"]) for data in answered] == [("rule", False)] * 3
    assert answered == Started({}).ask(3)
    # One line as the service starts, which names the provider that is not used and why.
    [line] = started.lines(NOT_USED)
    assert line == {
        "at": line["at"],
        "event": "model_not_used",
        "level": "warning",
        "provider": "gemini",
        "reason": "capped_at_nought",
    }
    assert Refusal.CAPPED_AT_NOUGHT.value == "capped_at_nought"
    # And no line for a cap that was reached: no call was there to turn away.
    assert started.lines(CAPPED) == []


def test_a_cap_at_nought_says_nothing_where_no_model_was_turned_on():
    for env in ({A_MINUTE: "0"}, {A_MINUTE: "0", A_DAY: "0"}):
        started = Started(env)

        assert started.ask(2) == Started({}).ask(2)
        assert started.lines(NOT_USED) == [] and started.lines(CAPPED) == []


@pytest.mark.parametrize(
    "env",
    [
        {"GEMINI_API_KEY": KEY_TEXT},
        {"BURRO_MODEL_PROVIDER": "gemini", "GEMINI_API_KEY": KEY_TEXT},
        {
            "BURRO_MODEL_PROVIDER": "gemini",
            "GEMINI_API_KEY": KEY_TEXT,
            "BURRO_MODEL_TERMS_ACCEPTED": "openai",
        },
    ],
    ids=["a key alone", "a key and its provider", "another's terms"],
)
def test_a_key_without_its_terms_accepted_calls_nothing_and_counts_nothing(env: dict[str, str]):
    # A cap that the second sentence would reach, were any sentence counted.
    started = Started(env | {A_MINUTE: "1", A_DAY: "1"})

    answered = started.ask(4)

    assert started.send.requests == []
    assert isinstance(started.deps.interpreter, RuleInterpreter)
    # No call was turned away, because none was counted: the rules read every one alike.
    assert [(data["interpreter"], data["degraded"]) for data in answered] == [("rule", False)] * 4
    assert started.lines(CAPPED) == []
    kept = started.deps.calls.records(started.deps.clock.now())
    assert len(kept) == 4
    assert not [record for record in kept if record.status.value == "capped" or record.provider]
    assert started.told()["model_reads"] is False


def test_nothing_that_was_set_is_in_a_line_of_the_cap():
    started = Started(ON | {A_MINUTE: "1"})
    started.ask(3)
    off = Started(ON | {A_DAY: "0"})
    off.ask(1)

    for service in (started, off):
        written = "\n".join(all_of(record) for record in (*service.began, *service.records))
        assert KEYED not in written.casefold()
        for word in MARK.casefold().split():
            assert word not in written.casefold()
