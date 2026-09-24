"""OpenAI: what is sent to the Responses API, and how its answer is read."""

import re
from typing import Any

import pytest
from burro_api.providers.interface import ModelCapped, ModelError, ModelFailure, ModelReply
from burro_api.providers.openai import SCHEMA_NAME, OpenAIClient

from . import documents
from .cases import (
    ANSWER,
    CASES,
    MAX_TOKENS,
    SYSTEM,
    TYPED,
    USER,
    answering,
    ask,
    assert_bare,
    failing,
    key,
    loaded,
)

OPENAI = CASES[1]


def with_usage(**counts: Any) -> dict[str, Any]:
    return OPENAI.whole(ANSWER) | {"usage": counts}


def read(answer: dict[str, Any]) -> ModelReply:
    return ask(OPENAI.made(answering(answer)), OPENAI)


def test_the_body_is_the_one_the_providers_documents_describe():
    send = answering(OPENAI.whole(ANSWER))

    ask(OPENAI.made(send), OPENAI)

    schema = send.sent["text"]["format"]["schema"]
    assert send.sent == {
        "model": "gpt-6-luna",
        "store": False,
        "reasoning": {"effort": "none"},
        "max_output_tokens": MAX_TOKENS,
        "prompt_cache_options": {"mode": "explicit"},
        "input": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "burro_edits",
                "strict": True,
                "schema": schema,
            }
        },
    }
    assert schema["type"] == "object" and "$defs" not in schema


def test_nothing_is_stored_whatever_is_asked_for():
    # Left out, `store` is true, and the provider keeps the call for 30 days.
    for model in ("gpt-6-luna", "gpt-6-sol"):
        send = answering(OPENAI.whole(ANSWER))
        ask(OPENAI.made(send), OPENAI, model=model, max_tokens=16)

        assert send.sent["store"] is False
        assert send.sent["reasoning"] == {"effort": "none"}


def test_nothing_a_person_typed_is_marked_for_the_cache():
    send = answering(OPENAI.whole(ANSWER))

    ask(OPENAI.made(send), OPENAI)

    # The explicit mode with nothing marked is no cache at all. Left to
    # itself the provider marks the end of the person's words.
    assert send.sent["prompt_cache_options"] == {"mode": "explicit"}
    assert "prompt_cache_breakpoint" not in send.requests[0].body.decode()


def test_the_name_of_the_schema_is_one_the_provider_takes():
    assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", SCHEMA_NAME)


def test_the_key_goes_in_as_a_bearer_and_no_other_header_names_anyone():
    send = answering(OPENAI.whole(ANSWER))

    ask(OPENAI.made(send), OPENAI)

    [request] = send.requests
    assert (request.key_header, request.key_scheme) == ("Authorization", "Bearer ")
    assert dict(request.headers) == {}


def test_the_answer_in_the_providers_own_example_is_read_as_it_stands():
    example = loaded(documents.OPENAI_WHOLE)

    reply = OpenAIClient(key()).read(example)

    assert isinstance(reply, ModelReply)
    assert reply.output == example["output"][0]["content"][0]["text"]
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (36, 87, 0)


def test_the_refusal_in_the_providers_own_example_is_an_error():
    # Its status is `completed`. Only the kind of its content says it is a refusal.
    example = loaded(documents.OPENAI_REFUSAL)
    assert example["status"] == "completed"

    failure = failing(OPENAI.made(answering(example)), OPENAI)

    assert type(failure) is ModelError
    assert_bare(failure)


def test_the_words_of_a_refusal_are_never_the_answer():
    answer = OPENAI.whole(ANSWER)
    answer["output"][0]["content"].append({"type": "refusal", "refusal": f"Not {TYPED}."})

    failure = failing(OPENAI.made(answering(answer)), OPENAI)

    assert type(failure) is ModelError
    assert_bare(failure)


def test_reasoning_is_among_the_tokens_out_as_the_providers_example_counts_it():
    reply = read(OPENAI.whole(ANSWER) | loaded(documents.OPENAI_USAGE_WITH_REASONING))

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (75, 1186, 0)


def test_tokens_read_from_the_cache_are_taken_out_of_the_tokens_in():
    details = {"cached_tokens": 2700, "cache_write_tokens": 100}

    reply = read(with_usage(input_tokens=3000, input_tokens_details=details, output_tokens=300))

    # What was written to the cache was sent, and was not read from it.
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (300, 300, 2700)


@pytest.mark.parametrize("details", [None, {}, {"cache_write_tokens": 3}], ids=range(3))
def test_a_count_from_the_cache_that_is_left_out_is_none(details: object):
    usage = {"input_tokens": 81, "output_tokens": 11} | (
        {} if details is None else {"input_tokens_details": details}
    )

    reply = read(OPENAI.whole(ANSWER) | {"usage": usage})

    assert (reply.input_tokens, reply.cache_read_tokens) == (81, 0)


@pytest.mark.parametrize("cached", [-1, True, "3", 2.0, 82], ids=str)
def test_a_count_from_the_cache_must_be_a_count_when_it_is_there(cached: object):
    details = {"cached_tokens": cached}
    answer = with_usage(input_tokens=81, input_tokens_details=details, output_tokens=11)

    assert type(failing(OPENAI.made(answering(answer)), OPENAI)) is ModelError


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"status": "failed", "error": {"code": "rate_limit_exceeded"}}, ModelCapped),
        ({"status": "failed", "error": {"code": "server_error", "message": TYPED}}, ModelError),
        ({"status": "failed", "error": {"code": "invalid_prompt"}}, ModelError),
        ({"status": "failed", "error": None}, ModelError),
        ({"status": "failed"}, ModelError),
        (
            {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}},
            ModelError,
        ),
        ({"status": "incomplete", "incomplete_details": {"reason": "content_filter"}}, ModelError),
        ({"status": "incomplete", "incomplete_details": {"reason": "max_messages"}}, ModelError),
        ({"status": "incomplete", "incomplete_details": {"reason": "steered"}}, ModelError),
        ({"status": "in_progress"}, ModelError),
        ({"status": "queued"}, ModelError),
        ({"status": "cancelled"}, ModelError),
        ({"status": "a_status_not_yet_invented"}, ModelError),
        ({"status": None}, ModelError),
        ({"status": "completed", "error": {"code": "server_error"}}, ModelError),
    ],
    ids=range(15),
)
def test_any_status_but_completed_is_a_failure(
    changes: dict[str, object], expected: type[ModelFailure]
):
    failure = failing(OPENAI.made(answering(OPENAI.whole(ANSWER) | changes)), OPENAI)

    assert type(failure) is expected
    assert_bare(failure)


def test_the_message_is_found_by_what_it_is_and_not_by_where_it_stands():
    answer = OPENAI.whole(ANSWER)
    answer["output"].insert(0, {"type": "reasoning", "id": "rs_1", "summary": []})

    assert read(answer).output == ANSWER


def test_the_text_at_the_top_of_an_answer_is_not_looked_for():
    # `output_text` is made by the provider's own library. It is not in what is sent back.
    answer: dict[str, Any] = OPENAI.whole(ANSWER) | {"output": [], "output_text": ANSWER}

    assert type(failing(OPENAI.made(answering(answer)), OPENAI)) is ModelError


@pytest.mark.parametrize(
    "output",
    [
        [],
        None,
        [{"type": "reasoning", "summary": []}],
        [{"type": "message", "content": []}],
        [{"type": "message", "content": [{"type": "output_text", "text": None}]}],
        [{"type": "message", "content": [{"type": "output_audio", "text": ANSWER}]}],
        [{"type": "message", "content": [{"type": "output_text", "text": ANSWER}]}] * 2,
        [
            {
                "type": "message",
                "status": "incomplete",
                "content": [{"type": "output_text", "text": ANSWER}],
            }
        ],
        ["message"],
    ],
    ids=range(9),
)
def test_output_that_holds_no_one_whole_message_is_an_error(output: object):
    answer = OPENAI.whole(ANSWER) | {"output": output}

    assert type(failing(OPENAI.made(answering(answer)), OPENAI)) is ModelError


def test_a_message_that_does_not_say_whether_it_finished_is_read():
    # The provider's own example of a refusal gives its message no status.
    answer = OPENAI.whole(ANSWER)
    del answer["output"][0]["status"]

    assert read(answer).output == ANSWER


def test_an_error_is_decided_on_its_status_and_its_body_is_not_read():
    send = answering(loaded(documents.OPENAI_ERROR), status=429)

    assert type(failing(OPENAI.made(send), OPENAI)) is ModelCapped
    assert send.requests[0].wants == {200}
