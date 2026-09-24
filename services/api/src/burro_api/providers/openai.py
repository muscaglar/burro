"""OpenAI, through the Responses API.

The schema is enforced by the provider, with `strict`: the answer will
"always ... adhere to your supplied JSON Schema". Two cases are written down
as exceptions, a refusal and an answer cut short, and both arrive as a 200.
The values can still be wrong, so the answer is validated afterwards like any
other.

`store` is sent as false on every call. Left out it is true, and the
provider then keeps each call for at least 30 days. The cache is asked for
in its explicit mode and nothing is marked, so nothing a person typed is
written to it. Nothing is sent that stands for a person or a search.

For the first live call to settle: that the schema is accepted as it
stands, and what the body of an error looks like. See "To confirm with the
first real call" in `docs/design/models.md`.
"""

from burro_api.providers.base import (
    Adapter,
    Outcome,
    count,
    count_if_given,
    listed,
    record,
    words,
)
from burro_api.providers.interface import ModelCapped, ModelError, ModelReply

HOST = "api.openai.com"
PATH = "/v1/responses"
# The name the provider asks a schema to have. It says nothing of a person.
SCHEMA_NAME = "burro_edits"
FINISHED = "completed"
FAILED = "failed"
# The one code inside a 200 that is a limit and not a fault.
RATE_LIMITED = "rate_limit_exceeded"
# The provider's guide to reasoning says "GPT-6 Astra does not support `none`
# reasoning effort" and answers 400 to it, and that GPT-6 Sol and Luna do
# support it. Its guide to the cache gives `prompt_cache_options` for
# "GPT-5.6 and later", so an older model may refuse the call. Read on
# 23 September 2026, the second time through a tool that returns an extraction:
# https://developers.openai.com/api/docs/guides/reasoning
# https://developers.openai.com/api/docs/guides/prompt-caching
FITS = frozenset({"gpt-6-luna", "gpt-6-sol"})


class OpenAIClient(Adapter):
    """One call to `/v1/responses`, with the key in `Authorization` and nothing stored."""

    HOST = HOST
    FITS = FITS
    KEY_HEADER = "Authorization"
    KEY_SCHEME = "Bearer "

    def path(self, model: str) -> str:
        return PATH

    def body(
        self, system: str, user: str, schema: dict[str, object], model: str, max_tokens: int
    ) -> dict[str, object]:
        return {
            "model": model,
            "store": False,
            # The default on the small model is to reason, which is paid for
            # as output and can use up the whole of the limit.
            "reasoning": {"effort": "none"},
            "max_output_tokens": max_tokens,
            # Left to itself the cache is marked at the end of the person's words.
            "prompt_cache_options": {"mode": "explicit"},
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": SCHEMA_NAME,
                    "strict": True,
                    "schema": schema,
                }
            },
        }

    def read(self, answer: dict[str, object]) -> Outcome:
        status = answer.get("status")
        if status == FAILED:
            limited = record(answer.get("error")).get("code") == RATE_LIMITED
            return ModelCapped if limited else ModelError
        if status != FINISHED or answer.get("error") is not None:
            # Cut short, cut by a filter, or not finished.
            return ModelError
        # The message is found by what it is. Something else may stand before it.
        found = [record(item) for item in listed(answer.get("output"))]
        [message] = [item for item in found if item.get("type") == "message"]
        if message.get("status") not in (None, FINISHED):
            return ModelError
        parts = [record(part) for part in listed(message.get("content"))]
        if not parts or any(part.get("type") != "output_text" for part in parts):
            # A refusal is finished too. Its words are never read.
            return ModelError
        usage = record(answer.get("usage"))
        details = usage.get("input_tokens_details")
        cached = 0 if details is None else count_if_given(record(details).get("cached_tokens"))
        return ModelReply(
            output="".join(words(part.get("text")) for part in parts),
            # The provider counts the cached tokens among the tokens in.
            input_tokens=count(count(usage.get("input_tokens")) - cached),
            # Reasoning is among the tokens out, and is billed as they are.
            output_tokens=count(usage.get("output_tokens")),
            cache_read_tokens=cached,
        )
