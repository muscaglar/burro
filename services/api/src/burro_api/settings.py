"""Settings, read once from the environment when the service starts.

The model id lives here, because a model can be retired during the life of a
release. The key does not: only whether one is present is recorded, and the
provider's SDK reads it for itself.
"""

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, Field

from burro_api.calls import MODEL_PATTERN
from burro_api.wire import Wire

# The committed synthetic release, so that a fresh checkout runs with nothing set.
SYNTHETIC_FIXTURE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "synthetic" / "syn-2026-09-23-01"
)
# The smallest current model. Reading a sentence into typed edits needs no more.
DEFAULT_MODEL_ID = "claude-haiku-4-5"
DEFAULT_TIMEOUT_S = 6.0
DEFAULT_MAX_TOKENS = 2048
KEY_VARIABLE = "ANTHROPIC_API_KEY"
# The web app as it runs on a developer's machine. Whoever deploys the service
# names the address the web app is served from.
DEFAULT_ORIGINS = ("http://localhost:3000",)
# A scheme, a host and perhaps a port, as a browser sends it: in lower case,
# with no path and no slash at the end, and never a pattern. An origin is
# compared as it is written, so one that no browser would send is refused
# here, when the service starts, and not left on the list to match nothing.
ORIGIN_PATTERN = r"^(https?)://([a-z0-9.-]+)(?::([1-9][0-9]{0,4}))?$"
# A label of a host: letters, digits and hyphens, with a letter or a digit at each end.
LABEL_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
LONGEST_HOST = 253
HIGHEST_PORT = 65_535
# The port a browser leaves out, because the scheme says it.
UNSAID_PORT = {"http": "80", "https": "443"}

_ORIGIN = re.compile(ORIGIN_PATTERN)
_LABEL = re.compile(LABEL_PATTERN)


def _as_a_browser_sends_it(origin: str) -> str:
    """`origin`, if a browser could send it. The error never repeats what was set."""
    found = _ORIGIN.fullmatch(origin)
    if found is None:
        raise ValueError("not a scheme, a host and perhaps a port")
    scheme, host, port = found.groups()
    if len(host) > LONGEST_HOST or not all(_LABEL.fullmatch(label) for label in host.split(".")):
        raise ValueError("not the name of a host")
    if port is not None and (int(port) > HIGHEST_PORT or port == UNSAID_PORT[scheme]):
        # A browser leaves out the port its scheme implies, so an entry that
        # names it would allow nothing, and nobody would be told.
        raise ValueError("not a port a browser names")
    return origin


Origin = Annotated[str, AfterValidator(_as_a_browser_sends_it)]


def _origins(listed: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in listed.split(","))


class Settings(Wire):
    release_dir: Path
    model_id: str = Field(pattern=MODEL_PATTERN, min_length=1)
    model_timeout_s: float = Field(gt=0, le=60)
    model_max_tokens: int = Field(ge=256, le=16_000)
    # Whether a key is in the environment. The key itself is never held here.
    model_key_present: bool
    host: str
    port: int = Field(ge=1, le=65_535)
    # The origins a browser may call from. A call from any other is answered,
    # and the browser is given nothing that lets a page read the answer.
    allowed_origins: tuple[Origin, ...] = Field(min_length=1)

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        return cls.model_validate(
            {
                "release_dir": env.get("BURRO_RELEASE_DIR") or SYNTHETIC_FIXTURE,
                "model_id": env.get("BURRO_MODEL_ID") or DEFAULT_MODEL_ID,
                "model_timeout_s": env.get("BURRO_MODEL_TIMEOUT_S") or DEFAULT_TIMEOUT_S,
                "model_max_tokens": env.get("BURRO_MODEL_MAX_TOKENS") or DEFAULT_MAX_TOKENS,
                "model_key_present": bool(env.get(KEY_VARIABLE, "").strip()),
                # The local machine only, unless whoever deploys it says otherwise.
                "host": env.get("BURRO_HOST") or "127.0.0.1",
                "port": env.get("BURRO_PORT") or 8000,
                "allowed_origins": _origins(listed)
                if (listed := env.get("BURRO_ALLOWED_ORIGINS", "").strip())
                else DEFAULT_ORIGINS,
            }
        )
