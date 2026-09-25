"""What the API tests share: the committed synthetic release, fakes, and a way to see every leak.

Every name here is made up. The release is the synthetic fixture, which
describes no real place.
"""

import json
import logging
import traceback
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from functools import cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, cast

import httpx2
from anyio.from_thread import BlockingPortal
from burro_api.app import create_app
from burro_api.calls import InMemoryCallLog
from burro_api.deps import Deps
from burro_api.loading import load_census, load_income, load_release
from burro_api.logs import JsonFormatter
from burro_api.offers import Offer, Way, of_the_rules
from burro_api.providers.choose import BY_RULES, told_of
from burro_api.providers.interface import ModelError
from burro_api.providers.terms import TERMS, Provider
from burro_api.reader import ModelInterpreter, ModelReply
from burro_api.settings import SYNTHETIC_CENSUS, SYNTHETIC_FIXTURE, SYNTHETIC_INCOME
from burro_api.stores import InMemoryShareStore
from burro_core import RuleInterpreter, TemplateExplainer, default_spec
from burro_core.census import Census
from burro_core.ids import Mode, Provenance, Strictness, Tenure
from burro_core.income import Income
from burro_core.interpret import InterpretRequest, InterpretResult
from burro_core.release import InMemoryRelease
from burro_core.spec import Budget, Commute, PreferenceSpec
from fastapi.testclient import TestClient

# A string found nowhere else. All lower case, so that nothing that folds
# case on the way can hide it.
CANARY = "zqxcanary7431"
NOW = datetime(2026, 9, 23, 12, 0, 0, tzinfo=UTC)
MODEL = "test-model-1"

WORKS = "syn-p0021"  # Cindermoor Works, a district that names itself
SCHOOL = "syn-p0031"  # Alderwick Primary School, which a share coarsens
SCHOOL_COARSE = "syn-p0005"  # Eskerfold station
ACADEMY = "syn-p0032"  # Eskerfold Academy, which coarsens to the same station


@cache
def release() -> InMemoryRelease:
    return load_release(SYNTHETIC_FIXTURE)


@cache
def census() -> Census:
    """The made-up count that is committed, which is what the service serves with nothing set."""
    found = load_census(SYNTHETIC_CENSUS, release())
    assert found is not None
    return found


@cache
def income() -> Income:
    """The made-up estimate of household income that is committed, served with nothing set."""
    found = load_income(SYNTHETIC_INCOME, release())
    assert found is not None
    return found


class FixedClock:
    """A clock that says the same time, and moves on a millisecond each time it is asked."""

    def __init__(self, now: datetime = NOW) -> None:
        self.at = now
        self._elapsed = 0.0

    def now(self) -> datetime:
        return self.at

    def elapsed(self) -> float:
        self._elapsed += 0.001
        return self._elapsed


class CountedIds:
    """Ids that count up, so a test can say which one it expects."""

    def __init__(self) -> None:
        self._made = 0

    def _next(self) -> int:
        self._made += 1
        return self._made

    def request_id(self) -> str:
        return f"00000000-0000-4000-8000-{self._next():012d}"

    def call_id(self) -> str:
        return f"11111111-1111-4111-8111-{self._next():012d}"

    def share_id(self) -> str:
        return f"share{self._next():017d}"


# What people are told in a test where a model reads. No test here calls a provider.
A_MODEL_READS = told_of(TERMS[Provider.GEMINI], with_settings=False)


def make_deps(**changes: Any) -> Deps:
    """What the service depends on, with a fixed clock, counted ids and the rules.

    People are told what fits whoever reads, unless the test says what they are told.
    """
    by_rules = isinstance(changes.get("interpreter", RuleInterpreter()), RuleInterpreter)
    deps = Deps(
        release=release(),
        interpreter=RuleInterpreter(),
        explainer=TemplateExplainer(),
        shares=InMemoryShareStore(),
        calls=InMemoryCallLog(),
        clock=FixedClock(),
        ids=CountedIds(),
        told=BY_RULES,
    )
    # The committed count is of the committed release. A test that serves another
    # release serves no census, unless it brings one made for that release.
    changes.setdefault("census", None if "release" in changes else census())
    changes.setdefault("income", None if "release" in changes else income())
    return replace(deps, **({"told": BY_RULES if by_rules else A_MODEL_READS} | changes))


# The event loop the tests have started, if they have. A test client starts a loop of
# its own for every request it makes, unless it is given one: `conftest.py` starts one
# for the whole run and puts it here.
LOOP: list[BlockingPortal] = []


def client_for(deps: Deps) -> TestClient:
    # A route that lets an exception fall must answer 500. It must never raise
    # into the server, which would print it.
    client = TestClient(create_app(deps), raise_server_exceptions=True)
    if LOOP:
        client.portal = LOOP[0]
    return client


def renter(**changes: Any) -> PreferenceSpec:
    return default_spec(Tenure.RENT).replace(**changes)


def commute(place_id: str = WORKS, minutes: int = 40, hard: bool = False) -> Commute:
    return Commute(
        place_id=place_id,
        mode=Mode.PT,
        max_minutes=minutes,
        strictness=Strictness.HARD if hard else Strictness.SOFT,
        provenance=Provenance.STATED,
    )


def budget(amount: int | None = 1800, hard: bool = False) -> Budget:
    base = default_spec(Tenure.RENT).budget
    return base.replace(
        amount=amount,
        strictness=Strictness.HARD if hard else Strictness.SOFT,
        provenance=Provenance.STATED,
    )


def searching(**changes: Any) -> PreferenceSpec:
    """A renter with a budget and a journey to work: enough for every component to be asked for."""
    return renter(**({"budget": budget(), "commutes": (commute(),)} | changes))


def wire(spec: PreferenceSpec) -> dict[str, Any]:
    return spec.model_dump(mode="json")


class FakeModelClient:
    """Stands in for the provider. It answers with what it was given, or raises it."""

    def __init__(self, answer: Mapping[str, Any] | str | Exception) -> None:
        self.answer = answer
        self.calls: list[dict[str, Any]] = []

    def complete(self, **sent: Any) -> ModelReply:
        self.calls.append(sent)
        if isinstance(self.answer, Exception):
            raise self.answer
        output = self.answer if isinstance(self.answer, str) else json.dumps(self.answer)
        return ModelReply(output=output, input_tokens=812, output_tokens=96, cache_read_tokens=640)


GROUPS = ("budget_ops", "commute_ops", "weight_ops", "tag_ops", "area_ops", "setting_ops")


def model_output(**changes: Any) -> dict[str, Any]:
    """An answer that fits the schema and asks for nothing."""
    empty: dict[str, Any] = {
        "status": "ok",
        "budget_ops": [],
        "commute_ops": [],
        "weight_ops": [],
        "tag_ops": [],
        "area_ops": [],
        "setting_ops": [],
        "policy_flags": [],
        "unmet": [],
    }
    return empty | changes


def model_commute(**changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "add",
        "destination_text": "",
        "position": 0,
        "mode": "unchanged",
        "max_minutes": 0,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
        "words": "",
    }
    return edit | changes


def model_weight(feature_id: str, **changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "nudge",
        "feature_id": feature_id,
        "value": 0.0,
        "step": "up_large",
        "direction": "default",
        "provenance": "stated",
        "words": "",
    }
    return edit | changes


def model_tag(tag_id: str, **changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "nudge",
        "tag_id": tag_id,
        "value": 0.0,
        "step": "up_large",
        "toward": "default",
        "provenance": "stated",
        "words": "",
    }
    return edit | changes


def model_area(
    action: str, name: str, provenance: str = "stated", words: str = ""
) -> dict[str, Any]:
    return {"action": action, "area_text": name, "provenance": provenance, "words": words}


def model_budget(**changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "set",
        "tenure": "unchanged",
        "amount": 0,
        "segment": "unchanged",
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
        "words": "",
    }
    return edit | changes


def model_setting(setting: str, **changes: Any) -> dict[str, Any]:
    edit: dict[str, Any] = {
        "action": "set",
        "setting": setting,
        "choice": "none",
        "value": 0.0,
        "step": "none",
        "provenance": "stated",
        "words": "",
    }
    return edit | changes


def resting_on(answer: Any, words: str) -> Any:
    """`answer`, with every edit that names no words resting on `words`.

    A model must say which of the person's words each edit rests on. Most
    tests here are of one sentence, and their stand-in rests every edit on
    the whole of it. A test of the words themselves gives them edit by edit.
    """
    if not isinstance(answer, dict):
        return answer
    found = dict(cast(dict[str, Any], answer))
    for group in GROUPS:
        edits = found.get(group)
        if isinstance(edits, list):
            found[group] = [
                edit | {"words": words}
                if isinstance(edit, dict) and cast(dict[str, Any], edit).get("words", "") == ""
                else edit
                for edit in cast(list[Any], edits)
            ]
    return found


class _Switch:
    """The one client the tests' reader asks. It hands each call to the stand-in of the moment.

    A reader makes the names and the words of a release ready once, and that
    takes longer than reading a sentence. So the tests share one reader, as
    the service has one, and what changes from one test to the next is the
    model that answers it.
    """

    def __init__(self) -> None:
        self.to: FakeModelClient | None = None

    def complete(self, **sent: Any) -> ModelReply:
        assert self.to is not None
        return self.to.complete(**sent)


_SWITCH = _Switch()
# One that sends the words alone, as the service does unless it is set
# otherwise, and one that sends the settings with them.
_READERS = {
    with_settings: ModelInterpreter(
        _SWITCH, model=MODEL, max_tokens=512, timeout_s=2.5, with_settings=with_settings
    )
    for with_settings in (False, True)
}


def reader_asking(client: FakeModelClient, with_settings: bool = False) -> ModelInterpreter:
    """The model-backed reader of these tests, with `client` as the model it asks."""
    _SWITCH.to = client
    return _READERS[with_settings]


# Words the rules leave unread, so that a model is asked about them.
NOT_PLAIN = "somewhere, honestly"


def asked(
    answer: Any,
    text: str = NOT_PLAIN,
    spec: PreferenceSpec | None = None,
    with_settings: bool = False,
) -> tuple[InterpretResult, FakeModelClient]:
    """What the model-backed interpreter makes of `text` when the model answers `answer`."""
    client = FakeModelClient(resting_on(answer, text))
    request = InterpretRequest(text=text, spec=spec or renter(), release=release())
    return reader_asking(client, with_settings).interpret(request), client


def through_the_route(answer: Any, text: str, spec: PreferenceSpec | None = None) -> dict[str, Any]:
    """The same, as route 1 serves it."""
    interpreter = reader_asking(FakeModelClient(resting_on(answer, text)))
    client = client_for(make_deps(interpreter=interpreter, model_id=MODEL))
    body = {"text": text} | ({"spec": wire(spec)} if spec else {})
    response = client.post("/v1/interpret", json=body)
    assert response.status_code == 200
    return response.json()["data"]


def _loggers() -> list[logging.Logger]:
    held = logging.getLogger().manager.loggerDict.values()
    return [each for each in held if isinstance(each, logging.Logger)]


@contextmanager
def logging_put_back() -> Generator[None]:
    """Leave logging as it was found: the root's handlers, and the level of every logger.

    The service sets the level of its own logger when it starts, and a test may set a
    library's. Left so, the next test hears less than it says it hears, and which test is
    next depends on the order the tests run in and on the process each is given.
    """
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    levels = {each.name: each.level for each in _loggers()}
    try:
        yield
    finally:
        root.handlers[:] = handlers
        root.setLevel(level)
        for each in _loggers():
            # One made since then goes back to what a new one has: no level of its own.
            each.setLevel(levels.get(each.name, logging.NOTSET))


# --- What is offered ---------------------------------------------------------------------------


def offers(result: InterpretResult) -> dict[str, Offer]:
    """Each offer of an answer by what it is of. Two of one kind are told apart by their order."""
    found: dict[str, Offer] = {}
    for offer in (of_the_rules(suggestion) for suggestion in result.suggestions):
        name = offer.target
        while name in found:
            name += "+"
        found[name] = offer
    return found


def ways(offer: Offer) -> dict[str, Way]:
    """The ways of an offer by their ids, doing nothing among them."""
    return {way.id: way for way in offer.choices}


def guessed(result: InterpretResult) -> dict[str, str]:
    """For each offer that holds a guess, which way of it Burro guesses."""
    return {
        name: way.id for name, offer in offers(result).items() for way in offer.choices if way.guess
    }


def quoted(result: InterpretResult, text: str) -> dict[str, list[str]]:
    """The words each offer rests on, as the caller finds them in the text it sent."""
    return {
        name: [text[span.start : span.end] for span in offer.spans]
        for name, offer in offers(result).items()
    }


# --- The answers of a model that are on disk ---------------------------------------------------

ANSWERS = Path(__file__).resolve().parents[3] / "evals" / "reader" / "answers"
ANSWERED_BY = "gemini-3.5-flash-lite"


@cache
def answers_on_disk() -> dict[tuple[str, int], dict[str, Any]]:
    """Every answer a model gave to a made-up sentence, by the sentence's id and the look.

    Each is what the provider answered, word for word. None is made again: a
    stand-in hands it to the reader, and no call is made.
    """
    lines = (ANSWERS / f"{ANSWERED_BY}.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [cast(dict[str, Any], json.loads(line)) for line in lines if line.strip()]
    return {(str(row["id"]), int(row["look"])): row for row in rows}


# Words the rules make nothing of. Put before a sentence that the rules read the whole of,
# they leave it for a model to read, as it was when the answer on disk was given.
UNREAD_FIRST = "Honestly. "


def on_disk(
    case: str, look: int = 1, before: str = ""
) -> tuple[str, PreferenceSpec, FakeModelClient]:
    """The sentence of an answer on disk, the search it was typed into, and the answer.

    `before` is put before the sentence. The answer quotes the sentence, so
    its words still stand in what was typed.
    """
    row = answers_on_disk()[(case, look)]
    answer: str | Exception = str(row["output"]) if "output" in row else ModelError()
    text = before + str(row["text"])
    return text, default_spec(Tenure(row["tenure"])), FakeModelClient(answer)


def read_again(case: str, look: int = 1, before: str = "") -> tuple[InterpretResult, str]:
    """What the reader makes of an answer on disk, and the sentence it answered."""
    text, spec, client = on_disk(case, look, before)
    request = InterpretRequest(text=text, spec=spec, release=release())
    return reader_asking(client).interpret(request), text


def served_again(case: str, look: int = 1, before: str = "") -> tuple[dict[str, Any], str]:
    """The same, as route 1 serves it."""
    text, spec, client = on_disk(case, look, before)
    deps = make_deps(interpreter=reader_asking(client), model_id=MODEL)
    response = client_for(deps).post("/v1/interpret", json={"text": text, "spec": wire(spec)})
    assert response.status_code == 200
    return response.json()["data"], text


# The test client is the caller, not the service. What it logs about the
# request it made is not something the service wrote.
_THE_CALLER = ("httpx", "httpcore")


class _Collect(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        if not record.name.startswith(_THE_CALLER):
            self.records.append(record)


def _all_of(record: logging.LogRecord) -> str:
    """Everything a record carries, as any formatter could come to print it."""
    parts = [repr(record.__dict__)]
    if record.exc_info and record.exc_info[1] is not None:
        parts += traceback.format_exception(record.exc_info[1])
    return "\n".join(parts)


@dataclass
class Seen:
    """Everything a test could leak through: logs, call records and responses."""

    deps: Deps
    client: TestClient
    records: list[logging.LogRecord]
    responses: list[httpx2.Response] = field(default_factory=list[httpx2.Response])

    def send(self, method: str, path: str, **sent: Any) -> httpx2.Response:
        response = self.client.request(method, path, **sent)
        self.responses.append(response)
        return response

    def post(self, path: str, body: Any) -> httpx2.Response:
        return self.send("POST", path, json=body)

    def lines(self) -> list[dict[str, Any]]:
        """The log as it is written: one JSON object for each line."""
        formatter = JsonFormatter()
        return [json.loads(formatter.format(record)) for record in self.records]

    def events(self, name: str) -> list[dict[str, Any]]:
        return [line for line in self.lines() if line["event"] == name]

    def everything(self) -> str:
        """Every log record in full, every log line, every call record and every response."""
        calls = self.deps.calls.records(NOW)
        parts = [
            *(_all_of(record) for record in self.records),
            *(json.dumps(line) for line in self.lines()),
            *(record.model_dump_json() for record in calls),
            *(f"{r.status_code} {dict(r.headers)!r} {r.text}" for r in self.responses),
        ]
        return "\n".join(parts)


@contextmanager
def watching(deps: Deps | None = None) -> Generator[Seen]:
    """Run requests with every logger open at its lowest level, and keep all that is logged."""
    deps = deps or make_deps()
    collect = _Collect()
    root = logging.getLogger()
    before = root.level
    root.addHandler(collect)
    # Lower than the service runs at, so that what a library would say at
    # debug level is seen here too.
    root.setLevel(logging.DEBUG)
    try:
        with client_for(deps) as client:
            yield Seen(deps=deps, client=client, records=collect.records)
    finally:
        root.removeHandler(collect)
        root.setLevel(before)


def assert_nothing_follows(error: BaseException) -> None:
    """A failure that is printed must not be followed by the one that led to it.

    What led to it holds the request, or the answer, and both can quote the person.
    """
    assert error.__cause__ is None
    assert error.__context__ is None or error.__suppress_context__
    assert CANARY not in "".join(traceback.format_exception(error)).casefold()


def assert_no_canary(seen: Seen, *more: str) -> None:
    haystack = "\n".join((seen.everything(), *more)).casefold()
    assert CANARY not in haystack


@cache
def sentences() -> Any:
    """The sentences core's reader is held to: the adversary's, and the plain wishes.

    They are core's, and are read from where core keeps them, so that the
    reader and the guard on a model are measured on the same words.
    """
    held = Path(__file__).resolve().parents[3] / "packages" / "core" / "tests" / "sentences.py"
    found = spec_from_file_location("burro_core_sentences", held)
    assert found is not None and found.loader is not None
    module = module_from_spec(found)
    found.loader.exec_module(module)
    return module
