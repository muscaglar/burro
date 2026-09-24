"""Anthropic's Claude, through the Messages API.

The schema is enforced by the provider, by constrained decoding. It writes
down three exceptions: a refusal, an answer cut short, and an enum value
whose case differs. The first two arrive as a 200 and are errors here. The
third is put right where the answer is validated, as it is for every
provider.

Nothing is marked for the cache, thinking is turned off, and nothing is sent
that stands for a person. The key is one that is tied to one workspace, so no
workspace header is sent.

For the first live call to settle: that the schema is accepted at its size.
See "To confirm with the first real call" in `docs/design/models.md`.
"""

from collections.abc import Mapping
from typing import ClassVar

from burro_api.providers.base import (
    OK,
    Adapter,
    Outcome,
    Response,
    count,
    count_if_given,
    listed,
    parsed,
    record,
    refused,
    words,
)
from burro_api.providers.interface import ModelCapped, ModelError, ModelFailure, ModelReply

HOST = "api.anthropic.com"
PATH = "/v1/messages"
VERSION = "2023-06-01"
FINISHED = "end_turn"
BAD_REQUEST = 400
# How the provider begins its message when a limit on spending that the
# customer set has been reached. It answers 400 then, as it does for a bad
# request, and only these words tell the two apart.
OWN_LIMIT = (
    "You have reached your specified API usage limits",
    "You have reached your specified workspace API usage limits",
)
# The provider's table of what each model rejects lists `"disabled"` for
# neither Claude Haiku 4.5 nor Claude Sonnet 5, and says "any value not
# listed as rejected is accepted". It lists it for Claude Opus 5.5, Fable 5,
# Fable 5.1 and the Mythos models, which answer 400. Read on
# 23 September 2026, as the page's own text:
# https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting
FITS = frozenset({"claude-haiku-4-5-20251001", "claude-sonnet-5"})


def _own_limit(body: bytes) -> bool:
    """Whether a 400 is a limit the customer set. The message is compared and let go of."""
    try:
        error = record(parsed(body).get("error"))
        return error.get("type") == "invalid_request_error" and words(
            error.get("message")
        ).startswith(OWN_LIMIT)
    except Exception:
        return False


class AnthropicClient(Adapter):
    """One call to `/v1/messages`, with the key in `x-api-key` and thinking off."""

    HOST = HOST
    FITS = FITS
    KEY_HEADER = "x-api-key"
    HEADERS: ClassVar[Mapping[str, str]] = {"anthropic-version": VERSION}
    # The body of a 400 is read, for the one case above, and of no other error.
    WANTS = frozenset({OK, BAD_REQUEST})

    def path(self, model: str) -> str:
        return PATH

    def body(
        self, system: str, user: str, schema: dict[str, object], model: str, max_tokens: int
    ) -> dict[str, object]:
        return {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            # On by default on the next model up, and paid for as output.
            "thinking": {"type": "disabled"},
            "output_config": {"format": {"type": "json_schema", "schema": schema}},
        }

    def failure(self, response: Response) -> type[ModelFailure] | None:
        if response.status == BAD_REQUEST and _own_limit(response.body):
            return ModelCapped
        return refused(response.status)

    def read(self, answer: dict[str, object]) -> Outcome:
        if answer.get("stop_reason") != FINISHED:
            # A refusal, an answer cut short, or a reason that did not exist
            # when this was written. Read before the text is.
            return ModelError
        blocks = [record(block) for block in listed(answer.get("content"))]
        said = [words(block.get("text")) for block in blocks if block.get("type") == "text"]
        if not said:
            return ModelError
        usage = record(answer.get("usage"))
        return ModelReply(
            output="".join(said),
            # What was written to a cache was sent and was not read from one.
            input_tokens=count(usage.get("input_tokens"))
            + count_if_given(usage.get("cache_creation_input_tokens")),
            output_tokens=count(usage.get("output_tokens")),
            cache_read_tokens=count_if_given(usage.get("cache_read_input_tokens")),
        )
