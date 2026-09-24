"""The client that calls the provider, with the provider's SDK and no provider.

Nothing here reaches a network: the SDK is given a transport that answers in
its place. So these tests show that the request is one the SDK accepts and
sends as intended, and that every failure is mapped. They cannot show that the
provider accepts it. That needs a key, and a run that is not part of CI.
"""

import io
import json
import logging
from collections.abc import Callable
from typing import Any

import anthropic
import httpx2
import pytest
from burro_api.claude import (
    SCHEMA,
    SYSTEM,
    ClaudeInterpreter,
    ModelCapped,
    ModelError,
    ModelFailure,
    ModelTimeout,
)
from burro_api.claude_sdk import AnthropicModelClient
from burro_api.logs import configure_logging
from burro_core.ids import InterpretStatus
from burro_core.interpret import InterpretRequest

from .support import (
    CANARY,
    MODEL,
    WORKS,
    assert_nothing_follows,
    model_commute,
    model_output,
    release,
    renter,
)

Handler = Callable[[httpx2.Request], httpx2.Response]


def message(text: str, stop_reason: str = "end_turn", **usage: int) -> dict[str, Any]:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": MODEL,
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 900, "output_tokens": 120} | usage,
    }


def answering(handler: Handler) -> AnthropicModelClient:
    """The real SDK, with a transport that answers in the provider's place."""
    sdk = anthropic.Anthropic(
        api_key="a-test-key-that-opens-nothing",
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicModelClient(sdk)


def complete(client: AnthropicModelClient, user: str = "{}"):
    return client.complete(
        system=SYSTEM, user=user, schema=SCHEMA, model=MODEL, max_tokens=512, timeout_s=2.5
    )


def replying(**content: Any) -> Handler:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, **content)

    return handler


def failing(status: int, kind: str) -> Handler:
    def handler(request: httpx2.Request) -> httpx2.Response:
        # A provider's error can repeat the request it refused.
        error = {"type": kind, "message": f"could not process: {request.content.decode()}"}
        return httpx2.Response(status, json={"type": "error", "error": error})

    return handler


def test_the_request_is_structured_output_with_the_instructions_marked_for_caching():
    sent: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(request)
        return httpx2.Response(200, json=message("{}", cache_read_input_tokens=700))

    reply = complete(answering(handler), user='{"request": "somewhere quiet"}')

    [request] = sent
    body = json.loads(request.content)
    assert (request.method, request.url.path) == ("POST", "/v1/messages")
    assert body == {
        "model": MODEL,
        "max_tokens": 512,
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": '{"request": "somewhere quiet"}'}],
        "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
    }
    # The time allowed is the time in settings, and not the SDK's ten minutes.
    assert set(request.extensions["timeout"].values()) == {2.5}
    assert reply.output == "{}"
    assert (reply.input_tokens, reply.output_tokens, reply.cache_read_tokens) == (900, 120, 700)


def test_a_reply_with_no_cache_figures_counts_none():
    reply = complete(answering(replying(json=message("{}"))))

    assert reply.cache_read_tokens == 0


def timing_out(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ReadTimeout("timed out", request=request)


def unreachable(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ConnectError("no route", request=request)


@pytest.mark.parametrize(
    ("handler", "failure"),
    [
        (timing_out, ModelTimeout),
        (unreachable, ModelError),
        (failing(429, "rate_limit_error"), ModelCapped),
        (failing(402, "billing_error"), ModelCapped),
        (failing(400, "invalid_request_error"), ModelError),
        (failing(401, "authentication_error"), ModelError),
        (failing(404, "not_found_error"), ModelError),
        (failing(500, "api_error"), ModelError),
        (failing(529, "overloaded_error"), ModelError),
        (replying(json=message("{}", "refusal")), ModelError),
        (replying(json=message("{", "max_tokens")), ModelError),
        (replying(json=message("") | {"content": []}), ModelError),
        (replying(text="<html>not the provider</html>"), ModelError),
    ],
    ids=range(13),
)
def test_every_failure_leaves_with_nothing_of_the_request_in_it(
    handler: Handler, failure: type[ModelFailure]
):
    with pytest.raises(ModelFailure) as failed:
        complete(answering(handler), user=json.dumps({"request": f"work at {CANARY}"}))

    assert type(failed.value) is failure
    # No message, and nothing to be printed after it.
    assert str(failed.value) == "" and failed.value.args == ()
    assert_nothing_follows(failed.value)


def test_a_call_is_made_once_and_never_again():
    calls: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        return failing(500, "api_error")(request)

    with pytest.raises(ModelError):
        complete(answering(handler))

    # The SDK would try three times. A retry would multiply how long a person
    # waits, and the rules can answer now.
    assert len(calls) == 1


def test_an_sdk_told_to_log_everything_still_logs_none_of_the_request():
    library = logging.getLogger("anthropic")
    written = io.StringIO()
    configure_logging(written)
    # What setting the SDK's own debug variable does: it then logs each request, body and all.
    library.setLevel(logging.DEBUG)
    raw = _Everything()
    library.addHandler(raw)
    try:
        complete(answering(replying(json=message("{}"))), user=f"work at {CANARY}")
        with pytest.raises(ModelError):
            complete(answering(failing(500, "api_error")), user=f"work at {CANARY}")
    finally:
        library.removeHandler(raw)

    # The SDK did log the request. The service wrote none of it.
    assert any(CANARY in line for line in raw.lines)
    assert CANARY not in written.getvalue()
    assert written.getvalue() == ""


class _Everything(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())


def test_a_sentence_goes_all_the_way_through_the_sdk_and_back():
    text = "30 minutes to Cindermoor Works"
    answer = model_output(
        commute_ops=[model_commute(destination_text="Cindermoor Works", max_minutes=30, words=text)]
    )

    def handler(request: httpx2.Request) -> httpx2.Response:
        user = json.loads(json.loads(request.content)["messages"][0]["content"])
        assert user["request"] == text
        return httpx2.Response(200, json=message(json.dumps(answer)))

    interpreter = ClaudeInterpreter(answering(handler), MODEL, max_tokens=512, timeout_s=2.5)
    request = InterpretRequest(text, renter(), release())
    result = interpreter.interpret(request)

    assert result.status is InterpretStatus.OK
    [edit] = result.operations.commute_ops
    assert (edit.place_id, edit.max_minutes) == (WORKS, 30)
    assert [(r.start, r.end) for r in result.rests_on] == [(0, len(text))]
    assert (result.usage.input_tokens, result.usage.output_tokens) == (900, 120)
