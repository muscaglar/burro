"""Nothing a person typed, and nothing of the key, leaves by any way but the one request.

One marker is planted in what is typed and another in the key. Every failure
is made to happen, for every provider. Then both are looked for in every log
record, in everything printed, in every failure with what led to it and what
it happened during, in every frame of ours it passed through, and in the
`repr` and `str` of every object that was in reach.
"""

import json
import logging
import traceback
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from burro_api.providers import choose as choosing
from burro_api.providers.base import MAX_BYTES, Deadline, Request, Response, over_https
from burro_api.providers.choose import choose
from burro_api.providers.interface import (
    ModelCapped,
    ModelError,
    ModelFailure,
    ModelReply,
    ModelTimeout,
)
from burro_api.providers.terms import TERMS, Read

from .cases import (
    ANSWER,
    CASES,
    CHECKED,
    KEY_TEXT,
    KEYED,
    TYPED,
    USER,
    Case,
    Sender,
    all_of,
    answering,
    ask,
    everything_of,
    failing,
    key,
    listening,
)
from .test_conformance import STATUSES, UNFIT_NAMES

each = pytest.mark.parametrize("case", CASES, ids=str)

# What a provider, a library or the system could say when something goes
# wrong. Each repeats what was sent, as the real ones can.
LEAKY = f"could not process {USER} sent with {KEY_TEXT}"
# The same, as often as makes an answer too long to be read, and no longer than that.
TOO_LONG = LEAKY * (1 + MAX_BYTES // len(LEAKY))


def _shown(*things: object) -> str:
    return "\n".join(f"{thing!r}\n{thing!s}\n{thing}" for thing in things)


def failures(case: Case) -> Iterator[tuple[Sender, dict[str, Any]]]:
    """Every way a call can fail: what the sender does, and what is asked of the adapter."""
    echo = json.dumps({"error": {"message": LEAKY, "type": "invalid_request_error"}}).encode()
    for status in STATUSES:
        yield Sender(Response(status, echo)), {}
    yield Sender(Response(400, echo)), {}
    for raised in (
        ModelTimeout(LEAKY),
        ModelCapped(LEAKY),
        ModelError(LEAKY),
        ModelFailure(LEAKY),
        TimeoutError(LEAKY),
        ConnectionResetError(LEAKY),
        RuntimeError(LEAKY),
        ValueError(f"Invalid header value {KEY_TEXT!r}"),
        json.JSONDecodeError(LEAKY, USER, 0),
        UnicodeDecodeError("utf-8", USER.encode(), 0, 1, LEAKY),
        KeyError(USER),
    ):
        yield Sender(raised), {}
    for body in (
        b"",
        LEAKY.encode(),
        echo,
        b"<html>" + LEAKY.encode() + b"</html>",
        json.dumps([LEAKY]).encode(),
        json.dumps({"leak": LEAKY}).encode(),
        json.dumps(case.whole(ANSWER) | {"padding": TOO_LONG}).encode(),
    ):
        yield Sender(Response(200, body)), {}
    for answer in (case.refusal(), case.cut_short(), case.whole(LEAKY), case.whole("")):
        yield answering(answer), {}
    broken = case.whole(ANSWER)
    case.usage_in(broken).clear()
    case.usage_in(broken)["leak"] = LEAKY
    yield answering(broken), {}
    for name in (*UNFIT_NAMES, LEAKY, KEY_TEXT, TYPED + "\n"):
        yield answering(case.whole(ANSWER)), {"model": name}
    for changes in (
        {"schema": {"$ref": LEAKY}},
        {"schema": {"$defs": {"A": {"$ref": "#/$defs/A"}}, "$ref": "#/$defs/A", "title": LEAKY}},
        {"max_tokens": 0},
        {"max_tokens": LEAKY},
        {"timeout_s": 0.0},
        {"timeout_s": LEAKY},
        {"system": LEAKY.encode()},
    ):
        yield answering(case.whole(ANSWER)), changes


@each
def test_no_failure_gives_away_what_was_typed_or_the_key(
    case: Case, capsys: pytest.CaptureFixture[str]
):
    seen: list[str] = []
    made = 0
    with listening() as records:
        for send, changes in failures(case):
            client = case.made(send)
            failure = failing(client, case, **changes)
            made += 1
            assert type(failure) in (ModelTimeout, ModelCapped, ModelError)
            assert str(failure) == "" and failure.args == () and vars(failure) == {}
            assert failure.__cause__ is None and failure.__context__ is None
            seen.append(everything_of(failure))
            seen.append(_shown(failure, client, type(client), *send.requests))
            seen.append(repr(vars(client)))
        written = [all_of(record) for record in records]

    printed = capsys.readouterr()
    found = "\n".join([*seen, *written, printed.out, printed.err]).casefold()
    assert made > 80
    assert TYPED not in found
    assert KEYED not in found
    # An adapter writes no line at all, whatever happens.
    assert records == []


@each
def test_an_answer_gives_away_nothing_either(case: Case, capsys: pytest.CaptureFixture[str]):
    send = answering(case.whole(ANSWER))
    with listening() as records:
        client = case.made(send)
        reply = ask(client, case)

    printed = capsys.readouterr()
    # The answer itself holds the person's words: a model copies them. It
    # is handed to the reader, and shown by nothing.
    assert TYPED in reply.output
    found = "\n".join(
        [
            _shown(reply, client, *send.requests, Response(200, send.requests[0].body)),
            repr(vars(client)),
            *(all_of(record) for record in records),
            printed.out,
            printed.err,
        ]
    ).casefold()
    assert TYPED not in found and KEYED not in found
    assert records == []


def test_the_function_that_sends_gives_away_nothing_when_it_fails(
    capsys: pytest.CaptureFixture[str],
):
    sent = Request(
        host="api.provider.example",
        path="/v1/answers",
        key_header="x-api-key",
        key=key(),
        body=USER.encode(),
    )
    unfit: tuple[dict[str, Any], ...] = (
        {"path": f"/v1/{TYPED}?key={KEY_TEXT}"},
        {"host": f"{TYPED}.example/"},
        {"headers": {"x-leak": f"{LEAKY}\r\n"}},
        {"key_scheme": f"{TYPED}\r\n"},
        {"key_header": f"{TYPED}\r\n"},
    )
    raised = (
        TimeoutError(LEAKY),
        OSError(61, LEAKY),
        ValueError(f"Invalid header value {KEY_TEXT!r}"),
        RuntimeError(LEAKY),
    )
    seen: list[str] = []
    with listening() as records:
        for error in raised:

            def connect(host: str, deadline: Deadline, error: Exception = error) -> Any:
                raise error

            with pytest.raises(ModelFailure) as failed:
                over_https(sent, 1.0, connect=connect)
            seen.append(everything_of(failed.value))
        for changes in unfit:
            with pytest.raises(ModelFailure) as failed:
                over_https(replace(sent, **changes), 1.0)
            seen.append(everything_of(failed.value))
        written = [all_of(record) for record in records]

    printed = capsys.readouterr()
    found = "\n".join([*seen, *written, printed.out, printed.err, _shown(sent)]).casefold()
    assert TYPED not in found and KEYED not in found
    assert records == []


@pytest.mark.parametrize(
    "env",
    [
        # A key pasted into the wrong variable.
        {"BURRO_MODEL_PROVIDER": KEY_TEXT},
        {"BURRO_MODEL_PROVIDER": "gemini", "BURRO_MODEL_TERMS_ACCEPTED": KEY_TEXT},
        {"BURRO_MODEL_TERMS_ACCEPTED": KEY_TEXT},
        {"BURRO_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": KEY_TEXT},
        {"BURRO_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": f"{KEY_TEXT}\r\nx-injected: 1"},
        {"BURRO_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": f"Bearer {KEY_TEXT}"},
        {
            "BURRO_MODEL_PROVIDER": "anthropic",
            "BURRO_MODEL_TERMS_ACCEPTED": "anthropic",
            "ANTHROPIC_API_KEY": KEY_TEXT,
            "BURRO_MODEL_ID": KEY_TEXT,
        },
        {
            "BURRO_MODEL_PROVIDER": "anthropic",
            "BURRO_MODEL_TERMS_ACCEPTED": "anthropic",
            "ANTHROPIC_API_KEY": KEY_TEXT,
        },
        {"GEMINI_API_KEY": KEY_TEXT},
        {name: KEY_TEXT for name in ("GEMINI_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY")},
    ],
    ids=range(10),
)
@pytest.mark.parametrize("table", [TERMS, CHECKED], ids=["as it stands", "checked"])
def test_choosing_gives_away_nothing_that_was_set(
    env: dict[str, str], table: Any, capsys: pytest.CaptureFixture[str]
):
    # With a table that a person has checked, one of these turns a model on,
    # and the adapter that is made holds the key.
    with listening() as records:
        choice = choose(env, table=table)
        written = [all_of(record) for record in records]
        lines = [json.dumps(vars(record), default=repr) for record in records]

    printed = capsys.readouterr()
    found = "\n".join(
        [
            _shown(choice, choice.told, choice.client, choice.refusal),
            repr(vars(choice.client)) if choice.client is not None else "",
            *written,
            *lines,
            printed.out,
            printed.err,
        ]
    ).casefold()
    assert KEYED not in found
    assert len(records) <= 1


def test_the_tables_and_the_modules_hold_nothing_of_a_call_after_it():
    import burro_api.providers.anthropic as anthropic
    import burro_api.providers.base as base
    import burro_api.providers.deepseek as deepseek
    import burro_api.providers.gemini as gemini
    import burro_api.providers.openai as openai

    for case in CASES:
        ask(case.made(answering(case.whole(ANSWER))), case)
        failing(case.made(Sender(RuntimeError(LEAKY))), case)
    choose({"BURRO_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": KEY_TEXT})
    turned_on = {
        "BURRO_MODEL_PROVIDER": "openai",
        "BURRO_MODEL_TERMS_ACCEPTED": "openai",
        "OPENAI_API_KEY": KEY_TEXT,
    }
    assert choose(turned_on, table=CHECKED).client is not None

    held = "\n".join(
        repr(vars(module)) for module in (base, gemini, openai, deepseek, anthropic, choosing)
    ).casefold()
    assert TYPED not in held and KEYED not in held
    assert all(answer.read in Read for terms in TERMS.values() for answer in terms.answers)


def test_this_test_would_see_a_leak_if_there_were_one():
    """The ways of looking are checked against failures that do give something away."""

    def chained() -> None:
        try:
            raise RuntimeError(LEAKY)
        except RuntimeError:
            # What an adapter must never do: raise while the cause is in reach.
            raise ModelError from None

    def holding() -> None:
        words = USER
        if words:
            raise ModelError

    with pytest.raises(ModelError) as kept_as_context:
        chained()
    assert kept_as_context.value.__context__ is not None
    assert TYPED in everything_of(kept_as_context.value)
    assert KEYED in everything_of(kept_as_context.value)
    # The usual way of printing a failure hides what `from None` suppressed.
    assert TYPED not in "".join(traceback.format_exception(kept_as_context.value))

    with pytest.raises(ModelError) as held_in_a_frame:
        holding()
    step = held_in_a_frame.value.__traceback__
    assert step is not None and step.tb_next is not None
    assert TYPED in repr(step.tb_next.tb_frame.f_locals)

    assert TYPED in _shown(ModelError(USER))
    assert KEYED in _shown(f"Key({KEY_TEXT})")
    assert TYPED not in _shown(ModelReply(USER, 1, 1, 0))

    with listening() as records:
        logging.getLogger("burro_api.providers").debug("sent %s", USER)
    assert TYPED in all_of(records[0])
