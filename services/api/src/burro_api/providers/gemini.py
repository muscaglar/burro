"""Google's Gemini API, through `generateContent`.

The schema is enforced by the provider: it says the answer is "a
syntactically valid JSON string matching the provided schema". It does not
promise the values, and it ignores a keyword it does not know, so the answer
is validated afterwards like any other.

Of Google's two APIs this is the one that stores nothing of its own. The
other, Interactions, keeps every call for 55 days unless each request says
otherwise. Nothing is sent that stores text: no tool, no cache, no file.

For the first live call to settle: which of two fields carries the schema.
This sends `responseMimeType` with `responseJsonSchema`, as Google's
published definition of the API names them. Google's guide shows
`responseFormat.text.schema`. Also that the schema is accepted at its size,
and what an error body looks like. See "To confirm with the first real call"
in `docs/design/models.md`.
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
from burro_api.providers.interface import ModelError, ModelRefused, ModelReply

HOST = "generativelanguage.googleapis.com"
# The model's name is part of the address, which is why it is held to a pattern.
PATH = "/v1beta/models/{model}:generateContent"
FINISHED = "STOP"
# The reasons to stop that say the answer was blocked, for safety or for the
# provider's own terms, as Google's published definition of the API lists them.
BLOCKED = frozenset({"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"})
# The least the small models can be asked to think. They cannot be told not
# to, and thinking is paid for as output and counted against the limit.
THINKING = "minimal"
# Google's table of thinking levels gives `minimal` as "Supported (Default)"
# for "Gemini 3.5 & 3.1 Flash-Lite", and as "Not supported (error)" for
# Gemini 3.8 and 3.7 Flash. Each model's own page says structured outputs are
# supported. Read on 23 September 2026, through a tool that returns an extraction:
# https://ai.google.dev/gemini-api/docs/generate-content/thinking
FITS = frozenset({"gemini-3.5-flash-lite", "gemini-3.1-flash-lite"})


class GeminiClient(Adapter):
    """One call to `generateContent`, with the key in `x-goog-api-key` and never in the address."""

    HOST = HOST
    FITS = FITS
    KEY_HEADER = "x-goog-api-key"

    def path(self, model: str) -> str:
        return PATH.format(model=model)

    def body(
        self, system: str, user: str, schema: dict[str, object], model: str, max_tokens: int
    ) -> dict[str, object]:
        return {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
                "maxOutputTokens": max_tokens,
                "thinkingConfig": {"thinkingLevel": THINKING},
            },
        }

    def read(self, answer: dict[str, object]) -> Outcome:
        feedback = answer.get("promptFeedback")
        if feedback is not None and record(feedback).get("blockReason") is not None:
            # The prompt was blocked. It is a 200 all the same.
            return ModelRefused
        [only] = listed(answer.get("candidates"))
        candidate = record(only)
        if candidate.get("finishReason") in BLOCKED:
            return ModelRefused
        if candidate.get("finishReason") != FINISHED:
            # Cut short, or a reason that did not exist when this was written.
            return ModelError
        parts = [record(part) for part in listed(record(candidate.get("content")).get("parts"))]
        # A thought can repeat what the person typed, and is no part of the answer.
        said = [words(part.get("text")) for part in parts if part.get("thought") is not True]
        if not said:
            return ModelError
        usage = record(answer.get("usageMetadata"))
        # Google counts the cached tokens among the tokens in, and leaves the
        # thinking out of the tokens out though it bills it as output.
        cached = count_if_given(usage.get("cachedContentTokenCount"))
        return ModelReply(
            output="".join(said),
            input_tokens=count(count(usage.get("promptTokenCount")) - cached),
            output_tokens=count(usage.get("candidatesTokenCount"))
            + count_if_given(usage.get("thoughtsTokenCount")),
            cache_read_tokens=cached,
        )
