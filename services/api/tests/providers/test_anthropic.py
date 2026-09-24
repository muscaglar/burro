"""Anthropic's Claude: what is sent to the Messages API, and how its answer is read."""

import json
from typing import Any

import pytest
from burro_api.providers.anthropic import OWN_LIMIT, AnthropicClient
from burro_api.providers.base import PATIENCE, Response
from burro_api.providers.interface import (
    ModelCapped,
    ModelError,
    ModelFailure,
    ModelReply,
    ModelTimeout,
)

from . import documents
from .cases import (
    ANSWER,
    CASES,
    KEY_TEXT,
    MAX_TOKENS,
    SYSTEM,
    TYPED,
    USER,
    Sender,
    answering,
    ask,
    assert_bare,
    failing,
    key,
    loaded,
)

ANTHROPIC = CASES[3]
# Every value the provider's reference lists, but the one that is an answer.
NOT_FINISHED = (
    "max_tokens",
    "stop_sequence",
    "tool_use",
    "pause_turn",
    "refusal",
    "model_context_window_exceeded",
    "a_reason_not_yet_invented",
    "END_TURN",
    "",
    None,
)


def with_usage(**counts: Any) -> dict[str, Any]:
    return ANTHROPIC.whole(ANSWER) | {"usage": counts}


def read(answer: dict[str, Any]) -> ModelReply:
    return ask(ANTHROPIC.made(answering(answer)), ANTHROPIC)


def refused(document: str | bytes, status: int) -> ModelFailure:
    body = document if isinstance(document, bytes) else document.encode()
    return failing(ANTHROPIC.made(Sender(Response(status, body))), ANTHROPIC)


def test_the_body_is_the_one_the_providers_documents_describe():
    send = answering(ANTHROPIC.whole(ANSWER))

    ask(ANTHROPIC.made(send), ANTHROPIC)

    schema = send.sent["output_config"]["format"]["schema"]
    assert send.sent == {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": USER}],
        "thinking": {"type": "disabled"},
        "output_config": {"format": {"type": "json_schema", "schema": schema}},
    }
    assert schema["type"] == "object" and "$defs" not in schema


def test_the_version_is_sent_and_the_key_is_in_its_own_header():
    send = answering(ANTHROPIC.whole(ANSWER))

    ask(ANTHROPIC.made(send), ANTHROPIC)

    [request] = send.requests
    assert (request.key_header, request.key_scheme) == ("x-api-key", "")
    assert dict(request.headers) == {"anthropic-version": "2023-06-01"}


def test_nothing_is_marked_for_the_cache():
    send = answering(ANTHROPIC.whole(ANSWER))

    ask(ANTHROPIC.made(send), ANTHROPIC)

    # A mark at the top of the body would mark the person's turn.
    assert "cache_control" not in send.requests[0].body.decode()


def test_thinking_is_turned_off_on_every_call():
    # On the next model up it is on unless it is turned off, and it is paid for as output.
    for model in ("claude-haiku-4-5-20251001", "claude-sonnet-5"):
        send = answering(ANTHROPIC.whole(ANSWER))
        ask(ANTHROPIC.made(send), ANTHROPIC, model=model)

        assert send.sent["thinking"] == {"type": "disabled"}


def test_the_answer_in_the_providers_own_example_is_read_as_it_stands():
    example = loaded(documents.ANTHROPIC_WHOLE)

    reply = AnthropicClient(key()).read(example)

    assert isinstance(reply, ModelReply)
    assert reply.output == "Sure, I'd be happy to provide..."
    # The example holds no count for the cache, which is none.
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (30, 309, 0)


def test_the_json_in_the_providers_own_guide_is_an_answer():
    reply = read(ANTHROPIC.whole(documents.ANTHROPIC_JSON_CONTENT))

    assert json.loads(reply.output)["demo_requested"] is True


def test_tokens_written_to_the_cache_are_among_the_tokens_in():
    # The provider's own example of usage. Its three counts of tokens in
    # add up to all that was sent.
    reply = read(ANTHROPIC.whole(ANSWER) | {"usage": loaded(documents.ANTHROPIC_USAGE_WITH_CACHE)})

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (4146, 503, 2051)


def test_a_count_for_the_cache_that_is_null_is_none():
    reply = read(
        with_usage(
            input_tokens=30,
            output_tokens=309,
            cache_creation_input_tokens=None,
            cache_read_input_tokens=None,
        )
    )

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (30, 309, 0)


@pytest.mark.parametrize("name", ["cache_creation_input_tokens", "cache_read_input_tokens"])
@pytest.mark.parametrize("value", [-1, True, "3", 2.0])
def test_a_count_for_the_cache_must_be_a_count_when_it_is_there(name: str, value: object):
    answer = with_usage(input_tokens=30, output_tokens=309, **{name: value})

    assert type(failing(ANTHROPIC.made(answering(answer)), ANTHROPIC)) is ModelError


def test_the_refusal_in_the_providers_own_example_is_an_error():
    failure = failing(ANTHROPIC.made(answering(loaded(documents.ANTHROPIC_REFUSAL))), ANTHROPIC)

    assert type(failure) is ModelError
    assert_bare(failure)


@pytest.mark.parametrize("reason", NOT_FINISHED, ids=str)
def test_any_stop_reason_but_the_end_of_the_turn_is_an_error(reason: str | None):
    # Read before the text is: an answer that was cut short or refused still holds text.
    failure = failing(
        ANTHROPIC.made(answering(ANTHROPIC.whole(ANSWER) | {"stop_reason": reason})), ANTHROPIC
    )

    assert type(failure) is ModelError
    assert_bare(failure)


def test_an_answer_with_no_stop_reason_is_an_error():
    answer = ANTHROPIC.whole(ANSWER)
    del answer["stop_reason"]

    assert type(failing(ANTHROPIC.made(answering(answer)), ANTHROPIC)) is ModelError


def test_the_text_is_found_by_what_it_is_and_not_by_where_it_stands():
    answer = ANTHROPIC.whole(ANSWER)
    answer["content"].insert(0, {"type": "thinking", "thinking": f"They work at {TYPED}."})

    assert read(answer).output == ANSWER


@pytest.mark.parametrize(
    "content",
    [
        [],
        None,
        [{"type": "thinking", "thinking": ANSWER}],
        [{"type": "tool_use", "name": "edits", "input": {}}],
        [{"type": "text", "text": None}],
        [{"type": "text"}],
        [ANSWER],
        ANSWER,
    ],
    ids=range(8),
)
def test_content_that_holds_no_text_is_an_error(content: object):
    answer = ANTHROPIC.whole(ANSWER) | {"content": content}

    assert type(failing(ANTHROPIC.made(answering(answer)), ANTHROPIC)) is ModelError


def test_the_body_of_a_400_is_asked_for_and_of_no_other_error():
    send = answering(ANTHROPIC.whole(ANSWER))

    ask(ANTHROPIC.made(send), ANTHROPIC)

    assert send.requests[0].wants == {200, 400}


@pytest.mark.parametrize("begins", OWN_LIMIT)
def test_a_limit_on_spending_that_the_customer_set_is_a_cap_though_it_answers_400(begins: str):
    message = f"{begins}. You will regain access on 2026-10-01 at 00:00 UTC."
    body = {"type": "error", "error": {"type": "invalid_request_error", "message": message}}

    failure = refused(json.dumps(body), 400)

    assert type(failure) is ModelCapped
    assert_bare(failure)


def test_the_limit_as_the_test_wrote_it_out_in_full_is_a_cap():
    assert type(refused(documents.ANTHROPIC_OWN_LIMIT, 400)) is ModelCapped


def test_a_limit_the_customer_set_is_a_cap_and_no_reason_to_rest():
    # It answers 400, as a request that is refused does. A cap is never
    # counted towards a rest, whatever its status: it may lift at any time.
    send = Sender(Response(400, documents.ANTHROPIC_OWN_LIMIT.encode()))
    client = ANTHROPIC.made(send)

    for _ in range(4 * PATIENCE):
        assert type(failing(client, ANTHROPIC)) is ModelCapped

    assert not client.resting
    assert len(send.requests) == 4 * PATIENCE
    # A 400 that is no limit is counted, from nought.
    send.answers = Response(400, documents.ANTHROPIC_RETENTION_NEEDED.encode())
    for _ in range(PATIENCE):
        assert type(failing(client, ANTHROPIC)) is ModelError
    assert client.resting


@pytest.mark.parametrize(
    "body",
    [
        documents.ANTHROPIC_RETENTION_NEEDED,
        json.dumps({"type": "error", "error": {"type": "invalid_request_error", "message": ""}}),
        json.dumps({"type": "error", "error": {"type": "invalid_request_error"}}),
        json.dumps({"type": "error", "error": {"type": "api_error", "message": OWN_LIMIT[0]}}),
        json.dumps({"type": "error", "error": {"message": OWN_LIMIT[0]}}),
        json.dumps({"type": "error", "error": OWN_LIMIT[0]}),
        json.dumps({"error": {"type": "invalid_request_error", "message": f"no: {OWN_LIMIT[0]}"}}),
        json.dumps({"error": {"type": "invalid_request_error", "message": [OWN_LIMIT[0]]}}),
        json.dumps({"message": OWN_LIMIT[0]}),
        json.dumps([OWN_LIMIT[0]]),
        json.dumps(
            {
                "error": {
                    "type": "invalid_request_error",
                    "message": f"messages.0.content: could not read {USER} sent with {KEY_TEXT}",
                }
            }
        ),
        OWN_LIMIT[0],
        "<html>Bad Request</html>",
        "",
        b"\xff\xfe",
        b"[" * 100_000,
    ],
    ids=range(16),
)
def test_any_other_400_is_an_error_and_nothing_of_its_body_is_kept(body: str | bytes):
    failure = refused(body, 400)

    assert type(failure) is ModelError
    assert_bare(failure)


def test_the_words_of_a_limit_are_looked_for_in_a_400_and_in_no_other_status():
    for status in (401, 403, 404, 500, 529):
        assert type(refused(documents.ANTHROPIC_OWN_LIMIT, status)) is ModelError


@pytest.mark.parametrize(
    ("document", "status", "expected"),
    [
        (documents.ANTHROPIC_NOT_FOUND, 404, ModelError),
        (documents.ANTHROPIC_MONTHLY_CAP, 429, ModelCapped),
        (documents.ANTHROPIC_RETENTION_NEEDED, 400, ModelError),
        (documents.ANTHROPIC_OVERLOADED, 529, ModelError),
        (documents.ANTHROPIC_OVERLOADED, 402, ModelCapped),
        (documents.ANTHROPIC_OVERLOADED, 504, ModelTimeout),
        ("<html>Request Entity Too Large</html>", 413, ModelError),
    ],
    ids=range(7),
)
def test_the_errors_in_the_providers_own_documents_are_each_one_of_the_three(
    document: str, status: int, expected: type[ModelFailure]
):
    failure = refused(document, status)

    assert type(failure) is expected
    assert_bare(failure)
