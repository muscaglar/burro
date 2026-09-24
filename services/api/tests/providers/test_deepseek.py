"""DeepSeek: what is sent to chat completions, and how its answer is read."""

import json
from typing import Any

import pytest
from burro_api.providers.base import inlined
from burro_api.providers.deepseek import DeepSeekClient, nothing_asked
from burro_api.providers.interface import ModelError, ModelReply

from . import documents
from .cases import (
    ANSWER,
    CASES,
    MAX_TOKENS,
    SCHEMA,
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

DEEPSEEK = CASES[2]
# Every value the provider's reference lists, but the one that is an answer.
NOT_FINISHED = (
    "length",
    "content_filter",
    "tool_calls",
    "insufficient_system_resource",
    "aborted",
    "a_reason_not_yet_invented",
    "STOP",
    "",
    None,
)


def read(answer: dict[str, Any]) -> ModelReply:
    return ask(DEEPSEEK.made(answering(answer)), DEEPSEEK)


def test_the_body_is_the_one_the_providers_documents_describe():
    send = answering(DEEPSEEK.whole(ANSWER))

    ask(DEEPSEEK.made(send), DEEPSEEK)

    instructions = send.sent["messages"][0]["content"]
    assert send.sent == {
        "model": "deepseek-flash",
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": USER},
        ],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }


def test_the_schema_is_in_the_instructions_because_the_provider_takes_none():
    send = answering(DEEPSEEK.whole(ANSWER))

    ask(DEEPSEEK.made(send), DEEPSEEK)

    instructions: str = send.sent["messages"][0]["content"]
    assert instructions.startswith(SYSTEM)
    # The provider asks for the word, for the shape and for an example.
    assert "json" in instructions.lower()
    assert json.dumps(inlined(SCHEMA)) in instructions
    assert json.dumps({"status": "ok", "edits": []}) in instructions
    # Nothing the person typed is in the instructions, so they are the same for every call.
    assert TYPED not in instructions


def test_the_instructions_are_the_same_byte_for_byte_whatever_is_typed():
    first, second = answering(DEEPSEEK.whole(ANSWER)), answering(DEEPSEEK.whole(ANSWER))

    ask(DEEPSEEK.made(first), DEEPSEEK, user="one thing")
    ask(DEEPSEEK.made(second), DEEPSEEK, user="another")

    assert first.sent["messages"][0] == second.sent["messages"][0]


def test_thinking_is_turned_off_on_every_call():
    # It is on unless it is turned off, and it sends the person's words back a second time.
    for model in ("deepseek-flash", "deepseek-v4-pro"):
        send = answering(DEEPSEEK.whole(ANSWER))
        ask(DEEPSEEK.made(send), DEEPSEEK, model=model)

        assert send.sent["thinking"] == {"type": "disabled"}


def test_an_answer_that_asks_for_nothing_is_made_from_the_schema():
    schema = inlined(
        {
            "type": "object",
            "properties": {
                "status": {"enum": ["ok", "off_topic"], "type": "string"},
                "edits": {"type": "array", "items": {"type": "string"}},
                "note": {"type": "string"},
                "minutes": {"type": "integer"},
                "weight": {"type": "number"},
                "hard": {"type": "boolean"},
                "inner": {"type": "object", "properties": {"kind": {"enum": ["add"]}}},
            },
        }
    )

    assert nothing_asked(schema) == {
        "status": "ok",
        "edits": [],
        "note": "",
        "minutes": 0,
        "weight": 0,
        "hard": False,
        "inner": {"kind": "add"},
    }


def test_the_answer_in_the_providers_own_example_is_read_as_it_stands():
    example = loaded(documents.DEEPSEEK_WHOLE)

    reply = DeepSeekClient(key()).read(example)

    assert isinstance(reply, ModelReply)
    assert reply.output == "Hello! How can I help you today?"
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (16, 10, 0)


def test_the_json_in_the_providers_own_guide_is_an_answer():
    reply = read(DEEPSEEK.whole(documents.DEEPSEEK_JSON_CONTENT))

    assert json.loads(reply.output)["answer"] == "The Nile River"


def test_tokens_in_are_those_that_missed_the_cache():
    answer = DEEPSEEK.whole(ANSWER)
    answer["usage"] |= {
        "prompt_tokens": 3000,
        "prompt_cache_hit_tokens": 2700,
        "prompt_cache_miss_tokens": 300,
        "completion_tokens": 250,
    }

    reply = read(answer)

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (300, 250, 2700)


def with_usage(**counts: Any) -> dict[str, Any]:
    return DEEPSEEK.whole(ANSWER) | {"usage": counts}


def test_an_answer_is_read_from_the_counts_the_reference_lists_and_no_others():
    # The provider's list of the fields of `usage` names these and no count
    # of the cache by another name. Its example holds two more. An answer
    # that holds only what the list names is whole all the same.
    listed_only = with_usage(
        completion_tokens=250,
        prompt_tokens=3000,
        total_tokens=3250,
        prompt_tokens_details={"cached_tokens": 2700},
        completion_tokens_details={"reasoning_tokens": 0},
    )

    reply = read(listed_only)

    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (300, 250, 2700)


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        # As the example has them.
        ({"prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 16}, (16, 0)),
        ({"prompt_cache_hit_tokens": 6, "prompt_cache_miss_tokens": 10}, (10, 6)),
        # By one name, by the other, by both, and by neither.
        ({"prompt_cache_hit_tokens": 6}, (10, 6)),
        ({"prompt_tokens_details": {"cached_tokens": 6}}, (10, 6)),
        (
            {"prompt_cache_hit_tokens": 6, "prompt_tokens_details": {"cached_tokens": 6}},
            (10, 6),
        ),
        ({"prompt_tokens_details": {}}, (16, 0)),
        ({"prompt_tokens_details": None}, (16, 0)),
        ({}, (16, 0)),
        # What missed the cache is never read: it is what is left.
        ({"prompt_cache_hit_tokens": 6, "prompt_cache_miss_tokens": 9999}, (10, 6)),
    ],
    ids=range(9),
)
def test_the_count_from_the_cache_is_read_by_either_of_its_names(
    counts: dict[str, Any], expected: tuple[int, int]
):
    reply = read(with_usage(prompt_tokens=16, completion_tokens=10, **counts))

    assert (reply.input_tokens, reply.cache_read_tokens) == expected
    assert reply.output_tokens == 10


@pytest.mark.parametrize(
    "counts",
    [
        {"completion_tokens": 10},
        {"prompt_tokens": 16},
        {"prompt_tokens": None, "completion_tokens": 10},
        {"prompt_tokens": 16, "completion_tokens": None},
        # The two the example holds are no stand-in for the one the list names.
        {"completion_tokens": 10, "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 16},
        {"completion_tokens": 10, "total_tokens": 26},
    ],
    ids=range(6),
)
def test_a_count_of_tokens_in_or_out_that_is_missing_is_an_error(counts: dict[str, Any]):
    assert type(failing(DEEPSEEK.made(answering(with_usage(**counts))), DEEPSEEK)) is ModelError


@pytest.mark.parametrize("cached", [-1, True, "3", 2.0, 17, [3]], ids=str)
@pytest.mark.parametrize("named", ["prompt_cache_hit_tokens", "cached_tokens"])
def test_a_count_from_the_cache_must_be_a_count_when_it_is_there(named: str, cached: object):
    given = (
        {named: cached} if named != "cached_tokens" else {"prompt_tokens_details": {named: cached}}
    )
    answer = with_usage(prompt_tokens=16, completion_tokens=10, **given)

    assert type(failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)) is ModelError


def test_details_that_are_no_record_are_an_error():
    answer = with_usage(prompt_tokens=16, completion_tokens=10, prompt_tokens_details=[6])

    assert type(failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)) is ModelError


@pytest.mark.parametrize("reason", NOT_FINISHED, ids=str)
def test_any_finish_reason_but_stop_is_an_error(reason: str | None):
    answer = DEEPSEEK.whole(ANSWER)
    answer["choices"][0]["finish_reason"] = reason

    failure = failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)

    assert type(failure) is ModelError
    assert_bare(failure)


@pytest.mark.parametrize(
    "content", ["", " \n\t", None, 12, [ANSWER], {"text": ANSWER}], ids=range(6)
)
def test_empty_content_which_the_provider_says_may_happen_is_an_error(content: object):
    answer = DEEPSEEK.whole(ANSWER)
    answer["choices"][0]["message"]["content"] = content

    assert type(failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)) is ModelError


def test_the_chain_of_thought_is_never_read():
    thought = f"The person works at {TYPED}, so"
    answer = DEEPSEEK.whole(ANSWER)
    answer["choices"][0]["message"]["reasoning_content"] = thought

    assert read(answer).output == ANSWER

    answer["choices"][0]["message"]["content"] = ""
    answer["choices"][0]["message"]["reasoning_content"] = ANSWER
    failure = failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)
    assert type(failure) is ModelError
    assert_bare(failure)


@pytest.mark.parametrize("count", [0, 2])
def test_no_choice_or_more_than_one_is_an_error(count: int):
    answer = DEEPSEEK.whole(ANSWER)
    answer["choices"] = answer["choices"] * count

    assert type(failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)) is ModelError


def test_a_call_to_a_tool_nobody_offered_is_an_error():
    answer = DEEPSEEK.whole("")
    answer["choices"][0] |= {"finish_reason": "tool_calls"}
    answer["choices"][0]["message"]["tool_calls"] = [
        {"type": "function", "function": {"name": "edits", "arguments": ANSWER}}
    ]

    assert type(failing(DEEPSEEK.made(answering(answer)), DEEPSEEK)) is ModelError


def test_an_error_is_decided_on_its_status_because_no_body_is_documented():
    # The provider shows no body for an error. This one is the test's own.
    send = answering({"error": {"message": f"bad request: {USER}"}}, status=422)

    failure = failing(DEEPSEEK.made(send), DEEPSEEK)

    assert type(failure) is ModelError
    assert send.requests[0].wants == {200}
    assert_bare(failure)
