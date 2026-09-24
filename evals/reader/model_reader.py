"""The model-backed reader, made as the service makes it, for `score.py --reader claude`.

This is the only file under `evals/` that imports the API package and, through
it, the provider's SDK. It reads the same settings the service reads, so an
evaluation measures the model and the limits that a person would meet:

    ANTHROPIC_API_KEY        the key. The SDK reads it for itself; nothing here does
    BURRO_MODEL_ID           the model. The service's default if left out
    BURRO_MODEL_TIMEOUT_S    how long to wait for an answer
    BURRO_MODEL_MAX_TOKENS   the most an answer may hold

Every case is a call that is paid for. `evals/README.md` says what a run costs.

A reader that fails, by a timeout, a limit or an answer that does not fit, is
counted as failed and is not answered for by the rules, so that a run measures
the model and nothing else.
"""

import os

from burro_core.interpret import Interpreter


def build() -> Interpreter:
    # Imported here, so that loading this file costs nothing until a reader is asked for.
    from burro_api.claude import ClaudeInterpreter
    from burro_api.claude_sdk import AnthropicModelClient
    from burro_api.settings import Settings

    settings = Settings.from_env(os.environ)
    if not settings.model_key_present:
        raise SystemExit("no key is set, so there is no model to measure. See evals/README.md")
    return ClaudeInterpreter(
        AnthropicModelClient(),
        settings.model_id,
        settings.model_max_tokens,
        settings.model_timeout_s,
    )
