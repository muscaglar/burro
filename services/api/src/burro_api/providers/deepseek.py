"""DeepSeek, through chat completions on its stable address.

**The provider does not enforce the schema.** On this address it promises
valid JSON and nothing about its shape: there is no `json_schema` type. So
the schema is written into the instructions, with one empty answer as an
example, as the provider's guide asks. What holds the answer to the schema is
the validation that follows every adapter (`claude._parsed`), and nothing
else. The provider also says an answer may come back empty, which is an error
here.

A schema is enforced only through a tool call on the provider's Beta
address. That is not built: it is Beta, and the path of its answer was not
read.

Thinking is on unless it is turned off, and it returns the person's words a
second time in `reasoning_content`. So it is turned off on every call, and
that field is never read.

Not shown in the provider's documents: the body of an error. See "To confirm
with the first real call" in `docs/design/models.md`.
"""

import json

from burro_api.providers.base import (
    Adapter,
    Outcome,
    Unfit,
    count,
    count_if_given,
    listed,
    record,
    words,
)
from burro_api.providers.interface import ModelError, ModelReply

HOST = "api.deepseek.com"
PATH = "/chat/completions"
FINISHED = "stop"
# The provider's reference gives two values for `model`, and `thinking` as
# "enabled" or "disabled" with no model left out. Two of its pages disagree
# about which model answers to the second name: see `docs/design/models.md`.
# Read on 23 September 2026, through a tool that returns an extraction:
# https://api-docs.deepseek.com/api/create-chat-completion
FITS = frozenset({"deepseek-flash", "deepseek-v4-pro"})

# The provider asks that the prompt hold the word "json" and an example.
SHAPE = """\

The shape of your answer
Answer with one JSON object and nothing else: no words before it, none after it, no code fence. \
It must fit this JSON Schema:
{schema}

An example of the format, which is the answer to a request that asks for nothing:
{example}
"""


def nothing_asked(schema: dict[str, object]) -> object:
    """An answer that fits `schema` and asks for nothing: empty lists and first choices."""
    if "enum" in schema:
        return listed(schema["enum"])[0]
    kind = schema.get("type")
    if kind == "object":
        properties = record(schema.get("properties", {}))
        return {name: nothing_asked(record(held)) for name, held in properties.items()}
    plain: dict[object, object] = {
        "array": [],
        "string": "",
        "integer": 0,
        "number": 0,
        "boolean": False,
        "null": None,
    }
    if kind not in plain:
        raise Unfit
    return plain[kind]


class DeepSeekClient(Adapter):
    """One call to `/chat/completions`, with the key in `Authorization` and thinking off."""

    HOST = HOST
    FITS = FITS
    KEY_HEADER = "Authorization"
    KEY_SCHEME = "Bearer "

    def path(self, model: str) -> str:
        return PATH

    def body(
        self, system: str, user: str, schema: dict[str, object], model: str, max_tokens: int
    ) -> dict[str, object]:
        shape = SHAPE.format(
            schema=json.dumps(schema, ensure_ascii=False),
            example=json.dumps(nothing_asked(schema), ensure_ascii=False),
        )
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system + shape},
                {"role": "user", "content": user},
            ],
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "stream": False,
        }

    def read(self, answer: dict[str, object]) -> Outcome:
        [only] = listed(answer.get("choices"))
        choice = record(only)
        if choice.get("finish_reason") != FINISHED:
            # Cut short, cut by a filter, interrupted, or a call to a tool nobody offered.
            return ModelError
        usage = record(answer.get("usage"))
        cached = _cached(usage)
        return ModelReply(
            # Empty content, which the provider says may happen, is no JSON
            # and is refused as any answer that is no JSON is.
            output=words(record(choice.get("message")).get("content")),
            # The provider counts the cached tokens among the tokens in.
            input_tokens=count(count(usage.get("prompt_tokens")) - cached),
            output_tokens=count(usage.get("completion_tokens")),
            cache_read_tokens=cached,
        )


def _cached(usage: dict[str, object]) -> int:
    """The tokens read from the cache, by whichever of two names the provider gives them.

    The provider's list of the fields of `usage` names `prompt_tokens` and
    `prompt_tokens_details`. Its example also holds `prompt_cache_hit_tokens`,
    which the list does not name. So neither is relied on to be there, and a
    count that is left out is none, as it is for the other providers.
    """
    hit = usage.get("prompt_cache_hit_tokens")
    if hit is not None:
        return count(hit)
    details = usage.get("prompt_tokens_details")
    return 0 if details is None else count_if_given(record(details).get("cached_tokens"))
