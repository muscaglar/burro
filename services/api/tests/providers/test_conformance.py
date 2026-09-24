"""The same cases, put to all four adapters. None is held to less than another."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from typing import Any, cast

import pytest
from burro_api.providers.base import (
    MAX_BYTES,
    PATIENCE,
    REST_S,
    STUCK,
    Adapter,
    Request,
    Response,
    over_https,
)
from burro_api.providers.interface import (
    ModelCapped,
    ModelError,
    ModelFailure,
    ModelRefused,
    ModelTimeout,
)

from .cases import (
    ANSWER,
    CASES,
    KEY_TEXT,
    KEYED,
    MAX_TOKENS,
    SYSTEM,
    TIMEOUT_S,
    TYPED,
    USER,
    Case,
    Sender,
    answering,
    ask,
    assert_bare,
    failing,
    key,
)

each = pytest.mark.parametrize("case", CASES, ids=str)

# Every status the four reports list, and those either side of them. What a
# status means is read the same way whoever sends it.
STATUSES: dict[int, type[ModelFailure]] = {
    **dict.fromkeys((408, 504), ModelTimeout),
    **dict.fromkeys((402, 429), ModelCapped),
    **dict.fromkeys(
        (100, 101, 201, 202, 204, 206, 300, 301, 302, 303, 304, 305, 307, 308),
        ModelError,
    ),
    **dict.fromkeys(
        (401, 403, 404, 405, 409, 410, 413, 416, 418, 422, 499, 500, 501, 502, 503, 529, 599),
        ModelError,
    ),
}
# A provider's error can repeat the request it refused.
ECHO = json.dumps({"error": {"message": f"could not read: {USER} with {KEY_TEXT}"}}).encode()

UNFIT_NAMES = (
    "",
    " ",
    "Gemini-3.5-Flash",
    "gemini/../x",
    "gemini?key=abc",
    "gemini#x",
    "gemini:generate",
    "gemini%2fx",
    "gemini flash",
    "gemini-flash\n",
    "gemini-flash\r\nx-injected: 1",
    "-gemini",
    ".gemini",
    "g" * 65,
    "gemini-flash-latest",
    "gpt-latest",
    "modèle",
)


@each
def test_it_sends_by_the_one_function_that_sends_unless_it_is_given_another(case: Case):
    assert vars(case.client(key()))["_send"] is over_https


@each
def test_a_whole_answer_is_read_with_its_counts(case: Case):
    send = answering(case.whole(ANSWER))

    reply = ask(case.made(send), case)

    assert reply.output == ANSWER
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == case.counts


@each
def test_one_post_goes_to_the_address_in_code_with_the_key_in_a_header(case: Case):
    send = answering(case.whole(ANSWER))

    ask(case.made(send), case)

    [request] = send.requests
    assert (request.host, request.path) == (case.host, case.path)
    assert (request.key_header, request.key_scheme) == (case.key_header, case.key_scheme)
    assert request.key.for_header() == KEY_TEXT
    # The key is in the one header, and in nothing else that is sent.
    assert KEYED not in request.path and KEYED not in request.host
    assert KEYED not in request.body.decode() and KEYED not in repr(dict(request.headers))
    assert send.timeouts == [TIMEOUT_S]


@each
def test_what_is_sent_is_the_instructions_the_words_and_the_limit(case: Case):
    send = answering(case.whole(ANSWER))

    ask(case.made(send), case)

    assert case.system_in(send.sent).startswith(SYSTEM)
    assert case.user_in(send.sent) == USER
    assert case.limit_in(send.sent) == MAX_TOKENS
    # What the person typed is sent once, in their own turn, and nowhere else.
    assert send.requests[0].body.decode().count(TYPED) == 1


@each
def test_nothing_is_sent_that_stands_for_a_person_or_keeps_the_text(case: Case):
    send = answering(case.whole(ANSWER))

    ask(case.made(send), case)

    unwanted = {
        "user",
        "user_id",
        "metadata",
        "safety_identifier",
        "prompt_cache_key",
        "previous_response_id",
        "conversation",
        "tools",
        "cachedContent",
        "cached_content",
        "cache_control",
        "background",
        "inference_geo",
        "temperature",
    }
    assert not unwanted & set(send.sent)
    assert send.sent.get("stream", False) is False
    assert send.sent.get("store", False) is False


def _keys(node: object) -> set[str]:
    if isinstance(node, dict):
        held = cast(dict[str, object], node)
        return set(held) | {key for value in held.values() for key in _keys(value)}
    if isinstance(node, list):
        return {key for item in cast(list[object], node) for key in _keys(item)}
    return set()


@each
def test_the_schema_is_sent_with_every_reference_written_out(case: Case):
    send = answering(case.whole(ANSWER))

    ask(case.made(send), case)

    sent: Any = case.schema_in(send.sent)
    if sent is None:
        # The one provider that takes no schema is given it in the instructions.
        sent = json.loads(case.system_in(send.sent).split("JSON Schema:\n")[1].split("\n")[0])
    assert _keys(sent) <= {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "enum",
        "items",
        "status",
        "edits",
        "kind",
        "words",
        "minutes",
    }
    assert sent["properties"]["edits"]["items"]["properties"]["kind"] == {
        "enum": ["add", "remove"],
        "type": "string",
    }


@each
def test_a_refusal_is_said_to_be_one_though_it_arrives_as_a_success(case: Case):
    # The provider would not read what was sent, for safety or for its own
    # terms. It is told apart from a fault, so that a person can be told.
    failure = failing(case.made(answering(case.refusal())), case)

    assert type(failure) is ModelRefused
    # Why it would not is never read. The words of a refusal can repeat what was typed.
    assert_bare(failure)


@each
def test_an_answer_cut_short_is_an_error_though_it_arrives_as_a_success(case: Case):
    failure = failing(case.made(answering(case.cut_short())), case)

    assert type(failure) is ModelError
    assert_bare(failure)


@each
@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        f"Here is the answer for {TYPED}.",
        '{"status": "ok", "edits": [',
        f"```json\n{ANSWER}\n```",
        "[]",
        '"ok"',
        "12",
        "null",
    ],
    ids=range(9),
)
def test_an_answer_that_is_not_a_json_object_is_an_error(case: Case, text: str):
    failure = failing(case.made(answering(case.whole(text))), case)

    assert type(failure) is ModelError
    assert_bare(failure)


@each
@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"<html>not the provider " + TYPED.encode() + b"</html>",
        b"[]",
        b"null",
        b'{"unfinished": ',
        b"\xff\xfe\x00not text",
        b"{}",
        b'{"error": {"message": "' + TYPED.encode() + b'"}}',
        b"[" * 100_000,
    ],
    ids=range(9),
)
def test_a_body_that_is_not_the_providers_answer_is_an_error(case: Case, body: bytes):
    failure = failing(case.made(answering(body)), case)

    assert type(failure) is ModelError
    assert_bare(failure)


@each
@pytest.mark.parametrize(("status", "expected"), STATUSES.items(), ids=str)
def test_every_status_but_200_is_one_of_the_three_failures(
    case: Case, status: int, expected: type[ModelFailure]
):
    send = Sender(Response(status, ECHO))

    failure = failing(case.made(send), case)

    assert type(failure) is expected
    assert_bare(failure)
    # Once, and never again: a retry multiplies how long a person waits.
    assert len(send.requests) == 1


@each
def test_a_status_that_is_a_failure_is_one_even_with_a_whole_answer_in_its_body(case: Case):
    whole = json.dumps(case.whole(ANSWER)).encode()

    assert type(failing(case.made(Sender(Response(500, whole))), case)) is ModelError
    assert type(failing(case.made(Sender(Response(302, whole))), case)) is ModelError
    assert type(failing(case.made(Sender(Response(429, whole))), case)) is ModelCapped


@each
def test_the_body_of_an_error_is_asked_for_only_where_a_provider_needs_it(case: Case):
    send = answering(case.whole(ANSWER))

    ask(case.made(send), case)

    [request] = send.requests
    assert request.wants - {200} == ({400} if str(case) == "anthropic" else set())


@each
def test_a_redirect_is_an_error_and_is_not_followed(case: Case):
    send = Sender(Response(307, b""))

    failure = failing(case.made(send), case)

    assert type(failure) is ModelError
    assert [(sent.host, sent.path) for sent in send.requests] == [(case.host, case.path)]


@each
def test_a_body_that_is_too_large_is_an_error(case: Case):
    padded = case.whole(ANSWER) | {"padding": "x" * MAX_BYTES}

    failure = failing(case.made(answering(padded)), case)

    assert type(failure) is ModelError
    assert_bare(failure)


@each
def test_a_body_of_the_greatest_size_is_read(case: Case):
    whole = json.dumps(case.whole(ANSWER)).encode()

    reply = ask(case.made(answering(whole + b" " * (MAX_BYTES - len(whole)))), case)

    assert reply.output == ANSWER


@each
def test_blank_lines_before_the_answer_are_no_part_of_it(case: Case):
    # A provider under load keeps the connection open with empty lines.
    whole = json.dumps(case.whole(ANSWER)).encode()

    assert ask(case.made(answering(b"\n\n\r\n" + whole)), case).output == ANSWER


@each
def test_a_slow_answer_is_a_timeout(case: Case):
    failure = failing(case.made(Sender(ModelTimeout())), case)

    assert type(failure) is ModelTimeout
    assert_bare(failure)


class _Late(ModelTimeout):
    def __init__(self) -> None:
        super().__init__(f"gave up on {USER} with {KEY_TEXT}")


@each
@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (ModelTimeout(), ModelTimeout),
        (ModelCapped(), ModelCapped),
        (ModelError(), ModelError),
        (_Late(), ModelTimeout),
        (ModelFailure(f"no words for {USER}"), ModelError),
        (TimeoutError(f"timed out sending {USER}"), ModelTimeout),
        (RuntimeError(f"could not send {USER} with {KEY_TEXT}"), ModelError),
        (json.JSONDecodeError("not JSON", USER, 0), ModelError),
        (MemoryError(), ModelError),
        (RecursionError(), ModelError),
    ],
    ids=range(10),
)
def test_whatever_the_sender_raises_leaves_as_one_of_the_three_and_bare(
    case: Case, raised: Exception, expected: type[ModelFailure]
):
    failure = failing(case.made(Sender(raised)), case)

    assert type(failure) is expected
    assert failure is not raised
    assert_bare(failure)


@each
@pytest.mark.parametrize("name", UNFIT_NAMES, ids=range(len(UNFIT_NAMES)))
def test_a_model_name_that_is_not_allowed_is_never_sent(case: Case, name: str):
    send = answering(case.whole(ANSWER))

    failure = failing(case.made(send), case, model=name)

    assert type(failure) is ModelError
    assert send.requests == []
    assert_bare(failure)


@each
@pytest.mark.parametrize(
    "changes",
    [
        {"max_tokens": 0},
        {"max_tokens": -1},
        {"max_tokens": "512"},
        {"timeout_s": 0},
        {"timeout_s": -2.5},
        {"timeout_s": float("nan")},
        {"schema": {"$ref": "#/$defs/Missing"}},
        {"schema": {"$ref": "https://example.test/schema.json"}},
        {"schema": {"$defs": {"A": {"$ref": "#/$defs/A"}}, "$ref": "#/$defs/A"}},
        {"schema": None},
        {"user": b"\xff".decode("latin-1").encode("latin-1")},
    ],
    ids=range(11),
)
def test_what_cannot_be_sent_as_it_is_is_never_sent(case: Case, changes: dict[str, Any]):
    send = answering(case.whole(ANSWER))

    failure = failing(case.made(send), case, **changes)

    assert type(failure) is ModelError
    assert send.requests == []
    assert_bare(failure)


@each
def test_a_count_that_is_missing_is_an_error_and_never_nought(case: Case):
    for name in case.needed:
        answer = case.whole(ANSWER)
        del case.usage_in(answer)[name]

        assert type(failing(case.made(answering(answer)), case)) is ModelError, name


@each
@pytest.mark.parametrize("value", [-1, True, False, "9", 9.0, None, [9], {"tokens": 9}], ids=str)
def test_a_count_that_is_not_a_count_is_an_error(case: Case, value: object):
    for name in case.needed:
        answer = case.whole(ANSWER)
        case.usage_in(answer)[name] = value

        assert type(failing(case.made(answering(answer)), case)) is ModelError, name


@each
def test_an_answer_with_no_usage_at_all_is_an_error(case: Case):
    answer = case.whole(ANSWER)
    case.usage_in(answer).clear()

    assert type(failing(case.made(answering(answer)), case)) is ModelError


@each
def test_the_request_as_it_is_sent_names_the_key_once_and_in_its_header(case: Case):
    seen: list[bytes] = []

    def send(request: Request, timeout_s: float) -> Response:
        from burro_api.providers import base

        seen.append(vars(base)["_written"](request))
        return Response(200, json.dumps(case.whole(ANSWER)).encode())

    ask(case.client(key(), send), case)

    [wire] = seen
    head, _, body = wire.partition(b"\r\n\r\n")
    lines = head.decode("ascii").split("\r\n")
    assert lines[0] == f"POST {case.path} HTTP/1.1"
    assert f"Host: {case.host}" in lines
    assert f"{case.key_header}: {case.key_scheme}{KEY_TEXT}" in lines
    assert wire.count(KEY_TEXT.encode()) == 1
    assert f"Content-Length: {len(body)}" in lines
    assert json.loads(body) == json.loads(body.decode("utf-8"))


@each
def test_each_model_the_adapter_was_fitted_to_is_asked_for_by_its_own_name(case: Case):
    assert {case.model, case.other} == case.client.FITS
    for model in sorted(case.client.FITS):
        send = answering(case.whole(ANSWER))

        assert ask(case.made(send), case, model=model).output == ANSWER

        [request] = send.requests
        assert model in request.path or send.sent["model"] == model


@each
def test_a_model_the_adapter_was_not_fitted_to_is_never_sent_a_word(case: Case):
    # A model of the provider's own family, which its documents say refuses
    # the setting for thinking, or the field for the cache, or is gone.
    for model in (*case.refuses, f"{case.model}-next", case.model.rsplit("-", 1)[0]):
        send = answering(case.whole(ANSWER))

        failure = failing(case.made(send), case, model=model)

        assert type(failure) is ModelError, model
        assert send.requests == [], model
        assert_bare(failure)


class Clock:
    """A clock that goes on only when a test says so."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def refusing(case: Case, status: int) -> tuple[Adapter, Sender, Clock]:
    send, clock = Sender(Response(status, ECHO)), Clock()
    return case.client(key(), send, clock), send, clock


def test_what_will_not_mend_itself_is_a_request_a_key_or_a_model_that_is_refused():
    assert sorted(STUCK) == [400, 401, 403, 404]
    assert (PATIENCE, REST_S) == (3, 300.0)
    # Each is an error, and is never counted as a cap or a timeout.
    assert all(STATUSES.get(status, ModelError) is ModelError for status in STUCK)


@each
@pytest.mark.parametrize("status", sorted(STUCK))
def test_a_provider_that_refuses_every_call_is_not_sent_every_sentence(case: Case, status: int):
    client, send, clock = refusing(case, status)

    for _ in range(PATIENCE):
        assert not client.resting
        assert type(failing(client, case)) is ModelError
    assert len(send.requests) == PATIENCE and client.resting

    # The sentences that follow reach nobody, and the rules answer.
    for _ in range(20):
        clock.now += 1.0
        failure = failing(client, case)
        assert type(failure) is ModelError
        assert_bare(failure)
    assert len(send.requests) == PATIENCE

    # Then one is let through, to see whether the provider has mended.
    clock.now += REST_S
    assert not client.resting
    assert type(failing(client, case)) is ModelError
    assert len(send.requests) == PATIENCE + 1
    # It has not, so it is left alone again at once.
    assert client.resting
    failing(client, case)
    assert len(send.requests) == PATIENCE + 1


@each
def test_a_provider_that_has_mended_is_asked_as_before(case: Case):
    client, send, clock = refusing(case, 401)
    for _ in range(PATIENCE):
        failing(client, case)
    clock.now += REST_S
    send.answers = Response(200, json.dumps(case.whole(ANSWER)).encode())

    assert ask(client, case).output == ANSWER
    assert not client.resting

    # And is given its whole patience again.
    send.answers = Response(401, ECHO)
    for _ in range(PATIENCE - 1):
        failing(client, case)
    assert not client.resting
    assert len(send.requests) == 2 * PATIENCE


@each
def test_refusals_count_only_when_they_come_in_a_row(case: Case):
    client, send, _ = refusing(case, 400)
    whole = Response(200, json.dumps(case.whole(ANSWER)).encode())

    for answer in (send.answers, send.answers, whole) * 4:
        send.answers = answer
        with suppress(ModelError):
            ask(client, case)

    assert not client.resting
    assert len(send.requests) == 12


@each
@pytest.mark.parametrize("status", [301, 402, 408, 409, 429, 500, 502, 503, 504, 529], ids=str)
def test_a_failure_that_may_mend_itself_is_never_a_reason_to_rest(case: Case, status: int):
    client, send, _ = refusing(case, status)

    for _ in range(4 * PATIENCE):
        failing(client, case)

    assert not client.resting
    assert len(send.requests) == 4 * PATIENCE


@each
@pytest.mark.parametrize(
    "raised", [ModelTimeout(), TimeoutError(), ConnectionResetError(), RuntimeError()], ids=range(4)
)
def test_a_call_that_got_no_answer_is_never_a_reason_to_rest(case: Case, raised: Exception):
    send = Sender(raised)
    client = case.client(key(), send, Clock())

    for _ in range(4 * PATIENCE):
        failing(client, case)

    assert not client.resting
    assert len(send.requests) == 4 * PATIENCE


@each
def test_an_answer_that_is_refused_by_the_model_is_no_refusal_by_the_provider(case: Case):
    # A safety block and an answer cut short arrive as a 200. The provider
    # took the request, and the next sentence may fare better.
    send = answering(case.refusal())
    client = case.client(key(), send, Clock())

    for _ in range(4 * PATIENCE):
        failing(client, case)

    assert not client.resting
    assert len(send.requests) == 4 * PATIENCE


@each
def test_what_is_never_sent_is_no_refusal_by_the_provider(case: Case):
    client, send, _ = refusing(case, 400)

    for _ in range(4 * PATIENCE):
        failing(client, case, model=case.refuses[0])
        failing(client, case, max_tokens=0)

    assert not client.resting and send.requests == []


@each
def test_all_that_is_kept_between_calls_is_a_count_and_a_time(case: Case):
    client, _, _ = refusing(case, 403)
    before = set(vars(client))

    for _ in range(PATIENCE + 2):
        failing(client, case)

    kept = vars(client)
    assert set(kept) == before == {"_key", "_send", "_clock", "_lock", "_stuck", "_until"}
    assert (type(kept["_stuck"]), type(kept["_until"])) == (int, float)
    # No status, no model, no word of anybody's.
    told = repr({name: held for name, held in kept.items() if name != "_send"}).casefold()
    assert TYPED not in told and KEYED not in told


@each
def test_each_adapter_rests_for_itself_and_tells_nobody(case: Case):
    client, _, _ = refusing(case, 404)
    other = case.made(answering(case.whole(ANSWER)))

    for _ in range(PATIENCE):
        failing(client, case)

    assert client.resting and not other.resting
    assert ask(other, case).output == ANSWER
    assert not case.made(answering(case.whole(ANSWER))).resting


@each
def test_many_calls_at_once_are_counted_without_a_fault(case: Case):
    client, send, _ = refusing(case, 400)

    def one(_: int) -> type[ModelFailure]:
        return type(failing(client, case))

    with ThreadPoolExecutor(max_workers=8) as pool:
        failures = list(pool.map(one, range(200)))

    assert set(failures) == {ModelError}
    assert client.resting
    # Those that set off together were sent. None that set off after the rest began was.
    assert PATIENCE <= len(send.requests) < PATIENCE + 8
