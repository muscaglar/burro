"""Google's Gemini: what is sent to `generateContent`, and how its answer is read."""

from typing import Any

import pytest
from burro_api.providers.gemini import GeminiClient
from burro_api.providers.interface import ModelCapped, ModelError, ModelRefused, ModelReply

from . import documents
from .cases import (
    ANSWER,
    CASES,
    KEYED,
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

GEMINI = CASES[0]
# Every value Google's published definition of the API lists, but the one that is an answer.
NOT_FINISHED = (
    "FINISH_REASON_UNSPECIFIED",
    "MAX_TOKENS",
    "SAFETY",
    "RECITATION",
    "LANGUAGE",
    "OTHER",
    "BLOCKLIST",
    "PROHIBITED_CONTENT",
    "SPII",
    "MALFORMED_FUNCTION_CALL",
    "UNEXPECTED_TOOL_CALL",
    "TOO_MANY_TOOL_CALLS",
    "IMAGE_SAFETY",
    "IMAGE_PROHIBITED_CONTENT",
    "IMAGE_OTHER",
    "NO_IMAGE",
    "IMAGE_RECITATION",
    "A_REASON_NOT_YET_INVENTED",
    "stop",
    "",
    None,
)
BLOCKED = ("SAFETY", "OTHER", "BLOCKLIST", "PROHIBITED_CONTENT", "IMAGE_SAFETY", "NOT_YET_INVENTED")
# The reasons to stop that say the provider would not read or answer, for
# safety or for its own terms. Any other is a fault, or an answer cut short.
WOULD_NOT = ("SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII")


def with_usage(**counts: Any) -> dict[str, Any]:
    return GEMINI.whole(ANSWER) | {"usageMetadata": counts}


def read(answer: dict[str, Any]) -> ModelReply:
    return ask(GEMINI.made(answering(answer)), GEMINI)


def test_the_body_is_the_one_the_providers_documents_describe():
    send = answering(GEMINI.whole(ANSWER))

    ask(GEMINI.made(send), GEMINI)

    schema = send.sent["generationConfig"]["responseJsonSchema"]
    assert send.sent == {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": USER}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": schema,
            "maxOutputTokens": MAX_TOKENS,
            "thinkingConfig": {"thinkingLevel": "minimal"},
        },
    }
    assert schema["type"] == "object" and "$defs" not in schema


def test_the_models_name_is_in_the_address_and_the_key_is_not():
    send = answering(GEMINI.whole(ANSWER))

    ask(GEMINI.made(send), GEMINI, model="gemini-3.1-flash-lite")

    [request] = send.requests
    assert request.path == "/v1beta/models/gemini-3.1-flash-lite:generateContent"
    # Google's older samples put the key in the address, after `?key=`.
    assert "?" not in request.path and "key" not in request.path and KEYED not in request.path
    assert request.key_header == "x-goog-api-key"


def test_the_answer_in_googles_own_example_is_read_as_it_stands():
    example = loaded(documents.GEMINI_WHOLE)

    reply = GeminiClient(key()).read(example)

    assert isinstance(reply, ModelReply)
    assert reply.output == example["candidates"][0]["content"]["parts"][0]["text"]
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (9, 87, 0)


def test_thinking_is_counted_as_output_because_it_is_billed_as_output():
    # The counts of Google's own example of an answer from a model that thinks.
    reply = read(with_usage(promptTokenCount=7, candidatesTokenCount=20, thoughtsTokenCount=22))

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (7, 42, 0)


def test_tokens_read_from_the_cache_are_taken_out_of_the_tokens_in():
    reply = read(
        with_usage(promptTokenCount=3000, cachedContentTokenCount=2700, candidatesTokenCount=300)
    )

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (300, 300, 2700)


def test_more_tokens_from_the_cache_than_were_sent_is_no_count():
    answer = with_usage(promptTokenCount=10, cachedContentTokenCount=11, candidatesTokenCount=5)

    assert type(failing(GEMINI.made(answering(answer)), GEMINI)) is ModelError


@pytest.mark.parametrize("name", ["cachedContentTokenCount", "thoughtsTokenCount"])
@pytest.mark.parametrize("value", [-1, True, "3", 2.0])
def test_a_count_that_may_be_left_out_must_be_a_count_when_it_is_there(name: str, value: object):
    answer = with_usage(promptTokenCount=10, candidatesTokenCount=5, **{name: value})

    assert type(failing(GEMINI.made(answering(answer)), GEMINI)) is ModelError


@pytest.mark.parametrize("reason", NOT_FINISHED, ids=str)
def test_any_finish_reason_but_stop_is_a_failure_and_a_block_is_a_refusal(reason: str | None):
    answer = GEMINI.whole(ANSWER)
    answer["candidates"][0]["finishReason"] = reason

    failure = failing(GEMINI.made(answering(answer)), GEMINI)

    assert type(failure) is (ModelRefused if reason in WOULD_NOT else ModelError)
    assert_bare(failure)


def test_an_answer_with_no_finish_reason_is_an_error():
    answer = GEMINI.whole(ANSWER)
    del answer["candidates"][0]["finishReason"]

    assert type(failing(GEMINI.made(answering(answer)), GEMINI)) is ModelError


@pytest.mark.parametrize("reason", BLOCKED)
def test_a_prompt_that_was_blocked_is_a_refusal_whatever_else_is_there(reason: str):
    answer = GEMINI.whole(ANSWER) | {"promptFeedback": {"blockReason": reason}}

    failure = failing(GEMINI.made(answering(answer)), GEMINI)

    assert type(failure) is ModelRefused
    assert_bare(failure)


def test_feedback_that_blocks_nothing_is_no_error():
    answer: dict[str, Any] = GEMINI.whole(ANSWER) | {"promptFeedback": {"safetyRatings": []}}

    assert read(answer).output == ANSWER


def test_a_thought_is_no_part_of_the_answer():
    answer = GEMINI.whole(ANSWER)
    answer["candidates"][0]["content"]["parts"].insert(
        0, {"text": f"The person works at {TYPED}.", "thought": True}
    )

    assert read(answer).output == ANSWER


def test_an_answer_in_more_than_one_part_is_read_as_one():
    answer = GEMINI.whole(ANSWER)
    answer["candidates"][0]["content"]["parts"] = [{"text": ANSWER[:9]}, {"text": ANSWER[9:]}]

    assert read(answer).output == ANSWER


@pytest.mark.parametrize(
    "parts",
    [
        [],
        [{"text": "only a thought", "thought": True}],
        [{"functionCall": {"name": "rank", "args": {}}}],
        [{"text": ANSWER}, {"inlineData": {"mimeType": "image/png", "data": ""}}],
        [{"text": 12}],
        [ANSWER],
        None,
    ],
    ids=range(7),
)
def test_parts_that_are_not_the_text_of_an_answer_are_an_error(parts: object):
    answer = GEMINI.whole(ANSWER)
    answer["candidates"][0]["content"]["parts"] = parts

    assert type(failing(GEMINI.made(answering(answer)), GEMINI)) is ModelError


@pytest.mark.parametrize("count", [0, 2])
def test_no_candidate_or_more_than_one_is_an_error(count: int):
    answer = GEMINI.whole(ANSWER)
    answer["candidates"] = answer["candidates"] * count

    assert type(failing(GEMINI.made(answering(answer)), GEMINI)) is ModelError


def test_an_error_is_decided_on_its_status_and_its_body_is_not_read():
    # The one sample of an error there is, and it is from Google's general
    # guide and not from this API. Its status says all that is needed.
    send = answering(loaded(documents.GEMINI_ERROR), status=429)

    assert type(failing(GEMINI.made(send), GEMINI)) is ModelCapped
    assert send.requests[0].wants == {200}
