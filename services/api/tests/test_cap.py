"""The cap on calls to a model: so many a minute and so many a day, for the whole service.

Without it a key on the open internet is an open bill (ADR 0032). It counts
calls, and nothing of who made them. Over it the rules read, and the person is
answered as they are when a provider says that it is capped: never by a 429,
a login wall or a 5xx.

No test here reaches a provider, and none waits for a minute to pass: the
clock is the test's own, and is moved by hand.
"""

import ast
import inspect
import json
import logging
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier, Thread
from typing import Any

import pytest
from burro_api import cap as the_cap
from burro_api.calls import CallStatus
from burro_api.cap import CAPPED, Cap, Reached
from burro_api.logs import LOGGABLE, JsonFormatter
from burro_api.reader import ModelCapped, ModelError, ModelInterpreter, ModelTimeout
from burro_api.routes.interpret import answer
from burro_core.interpret import InterpretRequest

from .support import (
    MODEL,
    NOW,
    FakeModelClient,
    FixedClock,
    client_for,
    make_deps,
    model_output,
    release,
    renter,
    watching,
)

# Two made-up words in mixed case, found nowhere else.
MARK = "Vexelmoor Quandrith"
# Not plain, so that the rules leave words unread and a model is asked.
TEXT = f"Honestly, 30 minutes to Cindermoor Works. I work nights at {MARK}"
# Plain, so that the rules apply it and no model is asked.
PLAIN = "leafy"
MINUTE = timedelta(minutes=1)
DAY = timedelta(days=1)


class Unhurried(int):
    """A cap that lets go of the processor as a count is held to it.

    Calls that come at one moment then overlap, every time and not by chance: each
    has found the cap not yet reached before any has been counted. Only a counter that
    lets one call in at a time holds against that.
    """

    def __le__(self, count: int) -> bool:
        time.sleep(0.0005)
        return int(self) <= count


def capped(a_minute: int, a_day: int, clock: FixedClock | None = None) -> tuple[Cap, FixedClock]:
    clock = clock or FixedClock()
    return Cap(a_minute, a_day, clock.now), clock


def let_in(cap: Cap, calls: int) -> int:
    """How many of so many calls, one after another, the cap lets in."""
    return [cap.lets_in() for _ in range(calls)].count(True)


def lines_of(records: list[logging.LogRecord], event: str) -> list[dict[str, Any]]:
    written = [json.loads(JsonFormatter().format(record)) for record in records]
    return [line for line in written if line["event"] == event]


# The counts.


def test_no_more_calls_than_the_cap_are_let_in_within_a_minute():
    cap, _ = capped(3, 100)

    assert [cap.lets_in() for _ in range(5)] == [True, True, True, False, False]


def test_a_minute_passes_and_calls_are_let_in_again():
    cap, clock = capped(3, 100)
    assert let_in(cap, 5) == 3

    clock.at += MINUTE

    assert let_in(cap, 5) == 3


def test_a_minute_is_a_minute_of_the_clock_and_not_sixty_seconds_from_the_first_call():
    cap, clock = capped(3, 100, FixedClock(NOW.replace(second=59)))
    assert let_in(cap, 5) == 3

    # One second on, another minute is running.
    clock.at += timedelta(seconds=1)

    assert let_in(cap, 5) == 3


def test_the_cap_of_a_day_holds_across_its_minutes():
    cap, clock = capped(3, 7)
    let: list[int] = []

    for _ in range(4):
        let.append(let_in(cap, 5))
        clock.at += MINUTE

    # Three, three, and the one that is left of the day. Then none, minute after minute.
    assert let == [3, 3, 1, 0]


def test_a_day_passes_and_calls_are_let_in_again():
    cap, clock = capped(3, 4)
    assert let_in(cap, 5) == 3
    clock.at += MINUTE
    assert let_in(cap, 5) == 1

    clock.at += DAY

    assert let_in(cap, 5) == 3


def test_a_day_is_a_day_of_the_clock_in_utc():
    # Half past midnight where the clock stands is half past eleven at night in UTC.
    ahead = timezone(timedelta(hours=1))
    clock = FixedClock(datetime(2026, 9, 24, 0, 30, tzinfo=ahead))
    cap = Cap(100, 3, clock.now)
    assert let_in(cap, 5) == 3

    # Midnight has passed there and not in UTC, so the day that is running has not turned.
    clock.at = datetime(2026, 9, 24, 0, 45, tzinfo=ahead)
    assert let_in(cap, 5) == 0

    clock.at = datetime(2026, 9, 24, 0, 0, tzinfo=UTC)
    assert let_in(cap, 5) == 3


def test_a_call_that_is_turned_away_is_not_counted():
    cap, clock = capped(2, 3)
    # Two are let in, and ten are turned away by the cap of the minute.
    assert let_in(cap, 12) == 2

    clock.at += MINUTE

    # Had the ten been counted, the day would be spent. One of it is left.
    assert let_in(cap, 12) == 1


def test_a_clock_that_is_put_back_brings_no_call_back():
    cap, clock = capped(3, 4)
    assert let_in(cap, 5) == 3

    clock.at -= MINUTE
    assert let_in(cap, 5) == 0
    clock.at -= DAY
    assert let_in(cap, 5) == 0

    # Time is counted again from the latest the clock has said.
    clock.at = NOW + MINUTE
    assert let_in(cap, 5) == 1


def test_a_cap_of_nought_lets_no_call_in():
    for a_minute, a_day in ((0, 100), (100, 0), (0, 0)):
        cap, clock = capped(a_minute, a_day)
        assert let_in(cap, 3) == 0
        clock.at += DAY
        assert let_in(cap, 3) == 0


def test_the_cap_holds_where_many_calls_come_at_once():
    cap, _ = capped(Unhurried(10), 1000)
    together = Barrier(64)
    let: list[bool] = []

    def call() -> None:
        together.wait(5)
        let.append(cap.lets_in())

    threads = [Thread(target=call, daemon=True) for _ in range(64)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)

    assert (len(let), let.count(True)) == (64, 10)


# What is written, and what is kept.


def test_one_line_says_that_a_cap_was_reached_the_first_time_in_its_minute_and_in_its_day():
    with watching() as seen:
        cap, clock = capped(2, 5)
        said: list[list[str]] = []
        for _ in range(4):
            before = len(seen.events(CAPPED))
            let_in(cap, 6)
            said.append([line["reason"] for line in seen.events(CAPPED)[before:]])
            clock.at += MINUTE
        clock.at += DAY
        before = len(seen.events(CAPPED))
        let_in(cap, 6)
        said.append([line["reason"] for line in seen.events(CAPPED)[before:]])

    # Once in each of two minutes. Then the day is spent, which is said once, however many
    # minutes of it are left. The next day the cap of a minute is reached again.
    assert said == [
        ["calls_per_minute"],
        ["calls_per_minute"],
        ["calls_per_day"],
        [],
        ["calls_per_minute"],
    ]


def test_the_line_holds_the_name_of_the_event_and_which_cap_and_no_more():
    with watching() as seen:
        cap, _ = capped(1, 5)
        let_in(cap, 3)
        [line] = seen.events(CAPPED)
        [record] = [record for record in seen.records if record.msg == CAPPED]

    assert line == {
        "at": line["at"],
        "event": "model_capped",
        "level": "warning",
        "reason": "calls_per_minute",
    }
    # No count of what was let in or turned away, and nothing a message could be made of.
    assert record.args in ((), None)
    assert {"reason"} <= LOGGABLE
    assert [reached.value for reached in Reached] == ["calls_per_minute", "calls_per_day"]


def test_the_counter_is_handed_nothing_of_a_call_and_holds_nothing_of_one():
    cap, _ = capped(2, 5)
    let_in(cap, 3)

    # Nobody is told apart from anybody: there is nothing to tell them apart by.
    assert list(inspect.signature(cap.lets_in).parameters) == []
    held = {name: value for name, value in vars(cap).items() if name not in ("_now", "_lock")}
    assert held and all(type(value) in (int, bool) for value in held.values()), held


def test_the_counter_reads_no_request_and_makes_no_hash():
    source = Path(inspect.getsourcefile(the_cap) or "").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for name in (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
        )
    }

    # The standard library, and the one way a line is written.
    assert imported - {"burro_api"} <= set(sys.stdlib_module_names)
    assert not imported & {"hashlib", "hmac", "secrets", "uuid", "fastapi", "starlette", "socket"}
    named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert not named & {"headers", "cookies", "client", "scope", "environ", "getenv"}


# The reader, and the route.


def reading(
    model: Any, a_minute: int, a_day: int, clock: FixedClock | None = None
) -> tuple[ModelInterpreter, FixedClock]:
    cap, clock = capped(a_minute, a_day, clock)
    return ModelInterpreter(model, MODEL, 512, 2.5, cap=cap), clock


def post(client: Any, text: str = TEXT, **more: Any) -> Any:
    return client.post("/v1/interpret", json={"text": text} | more)


def test_a_call_over_the_cap_is_read_by_the_rules_and_never_reaches_the_model():
    model = FakeModelClient(model_output())
    reader, clock = reading(model, 2, 100)
    deps = make_deps(interpreter=reader, model_id=MODEL, clock=clock)
    client = client_for(deps)

    answered = [post(client) for _ in range(5)]

    # Never a 429, a login wall or a 5xx: the rules answer, and the form still works.
    assert [response.status_code for response in answered] == [200] * 5
    read = [response.json()["data"] for response in answered]
    assert [data["interpreter"] for data in read] == ["model", "model", "rule", "rule", "rule"]
    assert [data["degraded"] for data in read] == [False, False, True, True, True]
    assert len(model.calls) == 2
    statuses = [record.status for record in deps.calls.records(NOW)]
    assert statuses == [CallStatus.SUGGEST] * 2 + [CallStatus.CAPPED] * 3
    assert client.post("/v1/rank", json={"spec": answered[-1].json()["data"]["spec"]}).is_success


def test_over_the_cap_the_rules_answer_as_with_no_model_but_for_what_says_a_model_was_capped():
    reader, clock = reading(FakeModelClient(model_output()), 1, 100)
    client = client_for(make_deps(interpreter=reader, model_id=MODEL, clock=clock))
    post(client)

    over = post(client)
    ruled = post(client_for(make_deps()))

    assert over.status_code == ruled.status_code == 200
    # Byte for byte, but for the one field that says the rules answered in a model's place.
    assert over.content != ruled.content
    assert over.content.replace(b'"degraded":true', b'"degraded":false', 1) == ruled.content
    assert ruled.content.count(b'"degraded":') == 1
    assert MARK.encode() not in over.content


def _of_the_call(found: Any) -> dict[str, Any]:
    """What is served, kept and written of one call, without what is made anew for each."""
    [record] = found.deps.calls.records(NOW)
    [line] = found.events("interpret")
    [response] = found.responses
    anew = ("call_id", "request_id", "at", "latency_ms")
    return {
        "status": response.status_code,
        "body": response.content,
        "headers": {k: v for k, v in response.headers.items() if k != "x-request-id"},
        "record": {k: v for k, v in record.model_dump(mode="json").items() if k not in anew},
        "line": {k: v for k, v in line.items() if k not in anew},
    }


def test_a_cap_of_the_services_own_looks_to_a_client_as_a_cap_of_the_providers_does():
    ours, clock = reading(FakeModelClient(model_output()), 1, 100)
    theirs = ModelInterpreter(FakeModelClient(ModelCapped()), MODEL, 512, 2.5)
    # The one call of the minute is made, so that the next finds the cap reached.
    ours.interpret(InterpretRequest(text=TEXT, spec=renter(), release=release()))

    with watching(make_deps(interpreter=ours, model_id=MODEL, clock=clock)) as by_ours:
        by_ours.post("/v1/interpret", {"text": TEXT})
        of_ours = _of_the_call(by_ours)
    with watching(make_deps(interpreter=theirs, model_id=MODEL)) as by_theirs:
        by_theirs.post("/v1/interpret", {"text": TEXT})
        of_theirs = _of_the_call(by_theirs)

    assert of_ours == of_theirs
    assert (of_ours["status"], of_ours["record"]["status"]) == (200, "capped")
    assert of_ours["line"]["call_status"] == "capped"


def test_a_minute_passes_and_a_model_reads_again():
    model = FakeModelClient(model_output())
    reader, clock = reading(model, 1, 3)
    client = client_for(make_deps(interpreter=reader, model_id=MODEL, clock=clock))
    read_by: list[list[str]] = []

    for _ in range(4):
        read_by.append([post(client).json()["data"]["interpreter"] for _ in range(2)])
        clock.at += MINUTE
    clock.at += DAY
    read_by.append([post(client).json()["data"]["interpreter"] for _ in range(2)])

    # One a minute, until the three of the day are spent. The next day, one a minute again.
    assert read_by == [["model", "rule"]] * 3 + [["rule", "rule"]] + [["model", "rule"]]
    assert len(model.calls) == 4


@pytest.mark.parametrize(
    "failure",
    [ModelError(), ModelTimeout(), RuntimeError(MARK)],
    ids=["an error", "a timeout", "an error of no kind of ours"],
)
def test_a_call_that_fails_is_counted(failure: Exception):
    model = FakeModelClient(failure)
    reader, clock = reading(model, 2, 100)
    deps = make_deps(interpreter=reader, model_id=MODEL, clock=clock)
    client = client_for(deps)

    answered = [post(client) for _ in range(4)]

    # It was counted as it was about to be made, so a provider that fails every call is
    # asked no more often than one that answers.
    assert len(model.calls) == 2
    assert [response.status_code for response in answered] == [200] * 4
    assert [record.status for record in deps.calls.records(NOW)][2:] == [CallStatus.CAPPED] * 2


def test_a_call_that_reaches_no_model_is_not_counted():
    model = FakeModelClient(model_output())
    reader, clock = reading(model, 1, 100)
    client = client_for(make_deps(interpreter=reader, model_id=MODEL, clock=clock))

    # What the rules apply by themselves, and what is asked of the rules alone.
    for _ in range(3):
        assert post(client, PLAIN).json()["data"]["degraded"] is False
        assert post(client, ask_model=False).json()["data"]["degraded"] is False
    assert model.calls == []

    # The one call of the minute is still there to be made.
    assert post(client).json()["data"]["interpreter"] == "model"
    assert len(model.calls) == 1


def test_the_cap_holds_where_many_sentences_come_at_once():
    model = FakeModelClient(model_output())
    reader, clock = reading(model, Unhurried(6), 100)
    deps = make_deps(interpreter=reader, model_id=MODEL, clock=clock)
    asked = InterpretRequest(text=TEXT, spec=renter(), release=release())
    # The first sentence makes the reader ready, as it does in the service. Five are left.
    assert answer(deps, asked)[1] is CallStatus.SUGGEST
    together = Barrier(24)
    found: list[CallStatus] = []

    def call() -> None:
        together.wait(10)
        found.append(answer(deps, asked)[1])

    threads = [Thread(target=call, daemon=True) for _ in range(24)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(20)

    # No more than the cap reach the model, and every one of the rest is answered.
    assert len(model.calls) == 6
    assert sorted(found) == sorted([CallStatus.SUGGEST] * 5 + [CallStatus.CAPPED] * 19)


def test_nothing_of_a_sentence_is_written_when_it_is_turned_away(
    capsys: pytest.CaptureFixture[str],
):
    reader, clock = reading(FakeModelClient(model_output()), 1, 100)
    with watching(make_deps(interpreter=reader, model_id=MODEL, clock=clock)) as seen:
        for _ in range(3):
            seen.post("/v1/interpret", {"text": TEXT})
        [line] = seen.events(CAPPED)
        everything = seen.everything()
        kept = [record.model_dump_json() for record in seen.deps.calls.records(NOW)]
        logged = [repr(record.__dict__) for record in seen.records]

    out, err = capsys.readouterr()
    # The words nobody else could have typed are nowhere, the answers included.
    for word in MARK.casefold().split():
        assert word not in "\n".join((everything, out, err)).casefold()
    # A place is named in an answer, and in nothing that is written or kept.
    written = "\n".join((*logged, *kept, json.dumps(seen.lines()), out, err)).casefold()
    assert "cindermoor" not in written and "syn-p" not in written
    # One line for the minute, though two sentences were turned away in it.
    assert set(line) == {"at", "event", "level", "reason"}


def test_a_reader_that_is_handed_no_cap_is_the_evaluation_sets_and_a_tests():
    # The service hands its reader a cap, always: `test_capped.py`. A reader with none is
    # made by the evaluation set, which measures a provider on made-up sentences, and by
    # a test.
    model = FakeModelClient(model_output())
    reader = ModelInterpreter(model, MODEL, 512, 2.5)
    asked = InterpretRequest(text=TEXT, spec=renter(), release=release())

    for _ in range(40):
        reader.interpret(asked)

    assert len(model.calls) == 40
