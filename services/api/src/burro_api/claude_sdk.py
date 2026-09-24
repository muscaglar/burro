"""The one `ModelClient` that calls the provider. The only module that imports its SDK.

It is imported only when a key is present, so a service with no key never
loads the SDK. The key is never read here: the SDK takes it from the
environment for itself.

Every failure leaves as a `ModelFailure` with no message and no cause. The
SDK's own exception holds the request, and the request holds what the person
typed, so it is dropped where it is caught and never chained.
"""

from collections.abc import Mapping

import anthropic
from anthropic.types import Message

from burro_api.claude import ModelCapped, ModelError, ModelReply, ModelTimeout

# A spend limit answers 402, which the SDK has no class of its own for.
_PAYMENT_REQUIRED = 402
_FINISHED = "end_turn"


def _reply(message: object) -> ModelReply:
    # An answer that is not JSON comes back from the SDK as the text it was,
    # whatever the SDK's types say. And anything but a finished turn is not an
    # answer: a refusal need not fit the schema, and one cut short is not whole.
    if not isinstance(message, Message) or message.stop_reason != _FINISHED:
        raise ModelError
    text = next((block.text for block in message.content if block.type == "text"), None)
    if text is None:
        raise ModelError
    usage = message.usage
    return ModelReply(
        output=text,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=usage.cache_read_input_tokens or 0,
    )


class AnthropicModelClient:
    """Calls the Messages API with structured output, once, with no retry.

    A retry would multiply the time a person waits, and the route has the
    rule-based interpreter to answer with in the meantime.
    """

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        # With no arguments, so that the SDK finds the key for itself.
        self._client = client or anthropic.Anthropic()

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: Mapping[str, object],
        model: str,
        max_tokens: int,
        timeout_s: float,
    ) -> ModelReply:
        try:
            once = self._client.with_options(max_retries=0, timeout=timeout_s)
            message = once.messages.create(
                model=model,
                max_tokens=max_tokens,
                # The instructions are the same for every request, so they are
                # marked to be cached. The person's words come after them.
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": dict(schema)}},
            )
        except anthropic.APITimeoutError:
            raise ModelTimeout from None
        except anthropic.RateLimitError:
            raise ModelCapped from None
        except anthropic.APIStatusError as error:
            capped = error.status_code == _PAYMENT_REQUIRED
            raise (ModelCapped if capped else ModelError) from None
        except anthropic.AnthropicError:
            raise ModelError from None
        return _reply(message)
