"""The model-backed reader, made for the evaluation set and for nothing else.

    read -rs GEMINI_API_KEY && export GEMINI_API_KEY
    BURRO_MODEL_PROVIDER=gemini uv run python evals/reader/score.py \\
        --reader burro_api.providers.measure:reader

Every sentence of the evaluation set is made up, so a provider can be
measured before anybody's words are sent to it. That is why this asks for the
provider and its key and for no more: not that its terms were accepted for
what real people type, and not that what people are told was read at the
source. Each case is a call that is paid for.

The service never uses this. There, `choose` is the only way a provider is
turned on.
"""

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from burro_api.providers.base import Key, Send, over_https
from burro_api.providers.choose import ADAPTERS, MODEL_VARIABLE, PROVIDER_VARIABLE
from burro_api.providers.terms import TERMS, Provider

if TYPE_CHECKING:
    from burro_core.interpret import Interpreter

    from burro_api.claude import ModelClient

TIMEOUT_VARIABLE = "BURRO_MODEL_TIMEOUT_S"
MAX_TOKENS_VARIABLE = "BURRO_MODEL_MAX_TOKENS"
# As the service has them.
TIMEOUT_S = 6.0
MAX_TOKENS = 2048

_NAMES = ", ".join(provider.value for provider in Provider)


def _number[N: (int, float)](env: Mapping[str, str], variable: str, otherwise: N) -> N:
    try:
        found = type(otherwise)(env.get(variable, "").strip() or otherwise)
    except ValueError:
        found = None
    # Said once the error is out of reach. It holds what was set, and a value
    # in the wrong variable could be a key.
    if found is None:
        raise SystemExit(f"{variable} is not a number")
    if not found > 0:
        raise SystemExit(f"{variable} is not more than nought")
    return found


def reader(env: Mapping[str, str] | None = None, send: Send = over_https) -> "Interpreter":
    """The reader that asks the provider named in the environment. It says why if it cannot."""
    env = os.environ if env is None else env
    named = env.get(PROVIDER_VARIABLE, "").strip().lower()
    if named not in TERMS:
        raise SystemExit(f"{PROVIDER_VARIABLE} must name one of: {_NAMES}")
    provider = Provider(named)
    terms = TERMS[provider]
    try:
        key = Key(env.get(terms.key_variable, "").strip())
    except ValueError:
        key = None
    if key is None:
        raise SystemExit(f"{terms.key_variable} holds no key. See docs/design/models.md")
    model = env.get(MODEL_VARIABLE, "").strip() or terms.model
    if not ADAPTERS[provider].takes(model):
        # A model is measured as the service would ask it, or not at all.
        raise SystemExit(
            f"{MODEL_VARIABLE} is not a model this provider's adapter was fitted to. "
            "See docs/design/models.md"
        )
    timeout_s = _number(env, TIMEOUT_VARIABLE, TIMEOUT_S)
    max_tokens = _number(env, MAX_TOKENS_VARIABLE, MAX_TOKENS)

    # Imported here, so that choosing a provider needs nothing of the engine.
    from burro_api.claude import ClaudeInterpreter

    # The reader's client and the adapters' are the same in shape, and are
    # made one when the adapters are wired in.
    client = cast("ModelClient", ADAPTERS[provider](key, send))
    return ClaudeInterpreter(client, model, max_tokens, timeout_s)
