"""All that the reader knows of a provider: one method, one reply and four failures.

They are defined here and nowhere else, so that an adapter needs nothing of
the reader or of the engine under it. The reader imports them, and so does
the route, which is how an adapter's timeout is counted as a timeout.

A failure carries no message. What went wrong underneath can hold the
request, and the request holds what the person typed.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


class ModelFailure(Exception):
    """The model could not be used. It carries no message: there is nothing safe to say."""


class ModelTimeout(ModelFailure):
    """The model did not answer in time."""


class ModelCapped(ModelFailure):
    """A rate limit or a spend limit was reached."""


class ModelRefused(ModelFailure):
    """The provider would not read what was sent, for safety or for its own terms.

    Why it would not is never read: the words of a refusal can repeat what was typed.
    """


class ModelError(ModelFailure):
    """Anything else, an answer that does not fit the schema included."""


@dataclass(frozen=True)
class ModelReply:
    # The model's answer as JSON text. It can repeat a name the person typed,
    # so it is kept out of every repr.
    output: str = field(repr=False)
    # Tokens that were sent and were not read from a cache. Tokens that were
    # written to one are among them.
    input_tokens: int
    # Tokens the provider bills as output. Thinking is among them.
    output_tokens: int
    cache_read_tokens: int


class ModelClient(Protocol):
    """One call to a model. Tests pass a fake."""

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: Mapping[str, object],
        model: str,
        max_tokens: int,
        timeout_s: float,
    ) -> ModelReply: ...
