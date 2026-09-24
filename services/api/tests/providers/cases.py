"""What the tests of the adapters share: two markers, a stand-in for the sender, and the four cases.

No test here reaches a provider. An adapter is given a function that answers
in the provider's place, with what the provider's documents show.
"""

import json
import logging
import traceback
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, cast

from burro_api.providers import base
from burro_api.providers.anthropic import AnthropicClient
from burro_api.providers.base import Adapter, Key, Request, Response
from burro_api.providers.deepseek import DeepSeekClient
from burro_api.providers.gemini import GeminiClient
from burro_api.providers.interface import ModelFailure, ModelReply
from burro_api.providers.openai import OpenAIClient
from burro_api.providers.terms import Provider, Terms

from . import documents

# Two strings found nowhere else. One stands in what a person typed, and
# one in the key. All lower case, so that nothing that folds case can hide them.
TYPED = "zqxtyped5290"
KEYED = "zqxkeyed8143"
KEY_TEXT = f"test-{KEYED}-opens-nothing"

SYSTEM = "Turn the request into edits. Answer in JSON."
# The person's turn as the reader makes it: their words, and their search as
# it stands. The search is never empty, and it says what they can pay and
# where they will not live.
SPEC = {
    "areas": [{"area_id": "syn-n0001", "rule": "exclude"}],
    "budget": {"amount": 1700, "segment": "bed_1", "strictness": "soft", "weight": 16},
    "commutes": [{"max_minutes": 30, "mode": "cycle", "position": 1, "strictness": "soft"}],
    "schema_version": 1,
    "tags": [{"tag_id": "leafy", "weight": 10}],
    "tenure": "rent",
    "weights": [{"direction": "less", "feature_id": "noise_exposure", "weight": 4}],
}
USER = json.dumps({"request": f"ten minutes from {TYPED}", "spec": SPEC})
# An answer that fits the small schema below. A model copies the person's words.
ANSWER = json.dumps({"status": "ok", "edits": [{"kind": "add", "words": TYPED, "minutes": 10}]})
MAX_TOKENS = 512
TIMEOUT_S = 2.5

# A small schema of the kind the reader sends: closed objects, every field
# required, and every choice a reference to a definition.
SCHEMA: dict[str, object] = {
    "$defs": {
        "Status": {"enum": ["ok", "off_topic"], "type": "string"},
        "Kind": {"enum": ["add", "remove"], "type": "string"},
        "Edit": {
            "additionalProperties": False,
            "properties": {
                "kind": {"$ref": "#/$defs/Kind"},
                "words": {"type": "string"},
                "minutes": {"type": "integer"},
            },
            "required": ["kind", "words", "minutes"],
            "type": "object",
        },
    },
    "additionalProperties": False,
    "properties": {
        "status": {"$ref": "#/$defs/Status"},
        "edits": {"items": {"$ref": "#/$defs/Edit"}, "type": "array"},
    },
    "required": ["status", "edits"],
    "type": "object",
}


def key() -> Key:
    return Key(KEY_TEXT)


def with_each(terms: Terms, **changes: object) -> Terms:
    """`terms`, with the same change made to every answer of it."""
    return replace(terms, answers=tuple(replace(answer, **changes) for answer in terms.answers))  # type: ignore[arg-type]


Answers = Response | BaseException | Callable[[Request], Response]


class Sender:
    """Stands in for `over_https`. It keeps what it was sent, which the real one never does."""

    def __init__(self, answers: Answers) -> None:
        self.answers = answers
        self.requests: list[Request] = []
        self.timeouts: list[float] = []

    def __call__(self, request: Request, timeout_s: float) -> Response:
        self.requests.append(request)
        self.timeouts.append(timeout_s)
        if isinstance(self.answers, BaseException):
            raise self.answers
        if isinstance(self.answers, Response):
            return self.answers
        return self.answers(request)

    @property
    def sent(self) -> dict[str, Any]:
        """The body of the one request that was sent."""
        [request] = self.requests
        return json.loads(request.body)


def answering(answer: object, status: int = 200) -> Sender:
    body = answer if isinstance(answer, bytes) else json.dumps(answer).encode()
    return Sender(Response(status, body))


def loaded(document: str) -> dict[str, Any]:
    return json.loads(document)


def _gemini_whole(text: str) -> dict[str, Any]:
    whole = loaded(documents.GEMINI_WHOLE)
    whole["candidates"][0]["content"]["parts"][0]["text"] = text
    return whole


def _openai_whole(text: str) -> dict[str, Any]:
    whole = loaded(documents.OPENAI_WHOLE)
    whole["output"][0]["content"][0]["text"] = text
    return whole


def _openai_cut_short() -> dict[str, Any]:
    # Made, from the reference: the whole answer with the named fields changed.
    cut = _openai_whole('{"status": "ok", "edits": [')
    cut["output"][0]["status"] = "incomplete"
    return cut | {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}


def _deepseek_whole(text: str) -> dict[str, Any]:
    whole = loaded(documents.DEEPSEEK_WHOLE)
    whole["choices"][0]["message"]["content"] = text
    return whole


def _deepseek_with(reason: str, text: str) -> dict[str, Any]:
    # Made, from the reference, which names the values and shows no sample.
    changed = _deepseek_whole(text)
    changed["choices"][0]["finish_reason"] = reason
    return changed


def _anthropic_whole(text: str) -> dict[str, Any]:
    whole = loaded(documents.ANTHROPIC_WHOLE)
    whole["content"][0]["text"] = text
    return whole


def _anthropic_cut_short() -> dict[str, Any]:
    # Made, from the reference.
    return _anthropic_whole('{"status": "ok", "edits": [') | {"stop_reason": "max_tokens"}


@dataclass(frozen=True)
class Case:
    """One provider, as the tests that are the same for all four need to know it."""

    provider: Provider
    client: type[Adapter]
    model: str
    host: str
    path: str
    # The header that carries the key, and what stands before the key in it.
    key_header: str
    key_scheme: str
    # A whole answer that holds `text`, made of the provider's own example.
    whole: Callable[[str], dict[str, Any]] = field(repr=False)
    # What the example counts: tokens in, tokens out, tokens read from a cache.
    counts: tuple[int, int, int]
    # A safety block and an answer cut short. Both arrive with status 200.
    refusal: Callable[[], dict[str, Any]] = field(repr=False)
    cut_short: Callable[[], dict[str, Any]] = field(repr=False)
    # Where each thing stands in the body that is sent.
    system_in: Callable[[dict[str, Any]], str] = field(repr=False)
    user_in: Callable[[dict[str, Any]], str] = field(repr=False)
    limit_in: Callable[[dict[str, Any]], int] = field(repr=False)
    # The schema as it was sent, or `None` where the provider takes none.
    schema_in: Callable[[dict[str, Any]], object] = field(repr=False)
    # Where the usage stands in an answer, to take a count out of it.
    usage_in: Callable[[dict[str, Any]], dict[str, Any]] = field(repr=False)
    # The counts an answer cannot be read without.
    needed: tuple[str, ...]
    # Another model whose request was read in the provider's documents.
    other: str
    # Models of the same family that the provider's documents say refuse the
    # request as it is sent, or that are gone. The first is the one its
    # documents are plainest about.
    refuses: tuple[str, ...]

    def __str__(self) -> str:
        return self.provider.value

    def made(self, send: Sender) -> Adapter:
        return self.client(key(), send)


CASES = (
    Case(
        provider=Provider.GEMINI,
        client=GeminiClient,
        model="gemini-3.5-flash-lite",
        host="generativelanguage.googleapis.com",
        path="/v1beta/models/gemini-3.5-flash-lite:generateContent",
        key_header="x-goog-api-key",
        key_scheme="",
        whole=_gemini_whole,
        counts=(9, 87, 0),
        refusal=lambda: loaded(documents.GEMINI_PROMPT_BLOCKED),
        cut_short=lambda: loaded(documents.GEMINI_CUT_SHORT),
        system_in=lambda sent: sent["system_instruction"]["parts"][0]["text"],
        user_in=lambda sent: sent["contents"][0]["parts"][0]["text"],
        limit_in=lambda sent: sent["generationConfig"]["maxOutputTokens"],
        schema_in=lambda sent: sent["generationConfig"]["responseJsonSchema"],
        usage_in=lambda answer: answer["usageMetadata"],
        needed=("promptTokenCount", "candidatesTokenCount"),
        other="gemini-3.1-flash-lite",
        # `minimal` is "Not supported (error)" on both.
        refuses=("gemini-3.8-flash", "gemini-3.7-flash"),
    ),
    Case(
        provider=Provider.OPENAI,
        client=OpenAIClient,
        model="gpt-6-luna",
        host="api.openai.com",
        path="/v1/responses",
        key_header="Authorization",
        key_scheme="Bearer ",
        whole=_openai_whole,
        counts=(36, 87, 0),
        refusal=lambda: loaded(documents.OPENAI_REFUSAL),
        cut_short=_openai_cut_short,
        system_in=lambda sent: sent["input"][0]["content"],
        user_in=lambda sent: sent["input"][1]["content"],
        limit_in=lambda sent: sent["max_output_tokens"],
        schema_in=lambda sent: sent["text"]["format"]["schema"],
        usage_in=lambda answer: answer["usage"],
        needed=("input_tokens", "output_tokens"),
        other="gpt-6-sol",
        # The first answers 400 to `none`. The cache field is for GPT-5.6 and later.
        refuses=("gpt-6-astra", "gpt-5.4-nano-2026-03-17", "gpt-5.5"),
    ),
    Case(
        provider=Provider.DEEPSEEK,
        client=DeepSeekClient,
        model="deepseek-flash",
        host="api.deepseek.com",
        path="/chat/completions",
        key_header="Authorization",
        key_scheme="Bearer ",
        whole=_deepseek_whole,
        counts=(16, 10, 0),
        refusal=lambda: _deepseek_with("content_filter", ""),
        cut_short=lambda: _deepseek_with("length", '{"status": "ok", "edits": ['),
        system_in=lambda sent: sent["messages"][0]["content"],
        user_in=lambda sent: sent["messages"][1]["content"],
        limit_in=lambda sent: sent["max_tokens"],
        schema_in=lambda sent: None,
        usage_in=lambda answer: answer["usage"],
        needed=("prompt_tokens", "completion_tokens"),
        other="deepseek-v4-pro",
        # Retired on 24 July 2026, and a name that is routed "temporarily".
        refuses=("deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash"),
    ),
    Case(
        provider=Provider.ANTHROPIC,
        client=AnthropicClient,
        model="claude-haiku-4-5-20251001",
        host="api.anthropic.com",
        path="/v1/messages",
        key_header="x-api-key",
        key_scheme="",
        whole=_anthropic_whole,
        counts=(30, 309, 0),
        refusal=lambda: loaded(documents.ANTHROPIC_REFUSAL),
        cut_short=_anthropic_cut_short,
        system_in=lambda sent: sent["system"],
        user_in=lambda sent: sent["messages"][0]["content"],
        limit_in=lambda sent: sent["max_tokens"],
        schema_in=lambda sent: sent["output_config"]["format"]["schema"],
        usage_in=lambda answer: answer["usage"],
        needed=("input_tokens", "output_tokens"),
        other="claude-sonnet-5",
        # Each answers 400 to `disabled`: thinking is always on.
        refuses=("claude-opus-5-5", "claude-fable-5-1", "claude-fable-5"),
    ),
)


def ask(client: Adapter, case: Case, **changes: Any) -> ModelReply:
    """One call, as the reader makes it."""
    sent: dict[str, Any] = {
        "system": SYSTEM,
        "user": USER,
        "schema": SCHEMA,
        "model": case.model,
        "max_tokens": MAX_TOKENS,
        "timeout_s": TIMEOUT_S,
    } | changes
    return client.complete(**sent)


def failing(client: Adapter, case: Case, **changes: Any) -> ModelFailure:
    """The failure a call ends in. The test fails if it ends in anything else."""
    try:
        ask(client, case, **changes)
    except ModelFailure as failure:
        return failure
    raise AssertionError("the call did not fail")


_OURS = str(Path(base.__file__).parent)


def everything_of(error: BaseException) -> str:
    """All that a failure could give away, however it came to be printed.

    Its words, what it holds, what led to it, what it happened during, every
    frame it passed through, and every local of every frame that is ours.
    """
    seen: list[str] = []
    follow: BaseException | None = error
    while follow is not None and len(seen) < 50:
        seen += [str(follow), repr(follow), repr(follow.args), repr(vars(follow))]
        seen += traceback.format_exception(follow)
        step = follow.__traceback__
        while step is not None:
            if step.tb_frame.f_code.co_filename.startswith(_OURS):
                seen.append(repr(dict(step.tb_frame.f_locals)))
            step = step.tb_next
        follow = follow.__cause__ or follow.__context__
    return "\n".join(seen)


def assert_bare(failure: BaseException) -> None:
    """A failure says nothing, holds nothing and is followed by nothing."""
    assert str(failure) == "" and failure.args == () and vars(failure) == {}
    assert failure.__cause__ is None and failure.__context__ is None
    told = everything_of(failure).casefold()
    assert TYPED not in told and KEYED not in told


class _Collect(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def listening() -> Generator[list[logging.LogRecord]]:
    """Every record that any logger writes, at any level, while the block runs."""
    collect = _Collect()
    root = logging.getLogger()
    before = root.level
    root.addHandler(collect)
    root.setLevel(logging.DEBUG)
    try:
        yield collect.records
    finally:
        root.removeHandler(collect)
        root.setLevel(before)


def all_of(record: logging.LogRecord) -> str:
    """Everything a record carries, as any formatter could come to print it."""
    parts = [repr(record.__dict__), record.getMessage()]
    if record.exc_info and record.exc_info[1] is not None:
        parts.append(everything_of(record.exc_info[1]))
    return "\n".join(parts)


def fields_of(record: logging.LogRecord) -> dict[str, object]:
    return cast(dict[str, object], getattr(record, "burro_fields", {}))
