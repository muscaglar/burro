"""Settings, read once from the environment when the service starts.

Nothing of a provider of a model is held here: not which provider, not its
key, not whether its terms were accepted, and not its model. Those are read
by `providers.choose`, which decides who reads what is typed. What is here
of a model is how long it is waited for and how much it may answer.
"""

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, Field

from burro_api.wire import Wire

# The committed synthetic release, so that a fresh checkout runs with nothing set.
SYNTHETIC_FIXTURE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "synthetic" / "syn-2026-09-23-01"
)
# The made-up count that was made for it. It is kept outside the folder of releases.
RESIDENTS_FOLDER = "-residents"
SYNTHETIC_CENSUS = (
    SYNTHETIC_FIXTURE.parents[1] / "residents" / f"{SYNTHETIC_FIXTURE.name}{RESIDENTS_FOLDER}"
)
# The one word that switches the census off.
OFF = "off"
DEFAULT_TIMEOUT_S = 6.0
DEFAULT_MAX_TOKENS = 2048
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


def _census_dir(env: Mapping[str, str]) -> Path | None:
    """Where the census of the release is looked for, or `None` where it is switched off.

    With nothing set it is the made-up count that is committed. With a release
    named it is the folder beside the release, named for it with `-residents`
    after. `BURRO_CENSUS_DIR` names another folder, and `BURRO_CENSUS=off`
    serves none, whatever is there.
    """
    if env.get("BURRO_CENSUS", "").strip().lower() == OFF:
        return None
    if named := env.get("BURRO_CENSUS_DIR"):
        return Path(named)
    if release := env.get("BURRO_RELEASE_DIR"):
        folder = Path(release).resolve()
        return folder.with_name(f"{folder.name}{RESIDENTS_FOLDER}")
    return SYNTHETIC_CENSUS


class Settings(Wire):
    release_dir: Path
    # The folder of the census that was made for the release, or `None` where none is
    # served. A folder that is not there is no census. One that is there is held to
    # every rule, and the service does not start on one that breaks any.
    census_dir: Path | None
    # Whether the folder was named by whoever runs the service. One that was named and
    # is not there is a fault, and not the want of a census.
    census_named: bool
    model_timeout_s: float = Field(gt=0, le=60)
    model_max_tokens: int = Field(ge=256, le=16_000)
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
                "census_dir": _census_dir(env),
                "census_named": bool(env.get("BURRO_CENSUS_DIR")),
                "model_timeout_s": env.get("BURRO_MODEL_TIMEOUT_S") or DEFAULT_TIMEOUT_S,
                "model_max_tokens": env.get("BURRO_MODEL_MAX_TOKENS") or DEFAULT_MAX_TOKENS,
                # The local machine only, unless whoever deploys it says otherwise.
                "host": env.get("BURRO_HOST") or "127.0.0.1",
                "port": env.get("BURRO_PORT") or 8000,
                "allowed_origins": _origins(listed)
                if (listed := env.get("BURRO_ALLOWED_ORIGINS", "").strip())
                else DEFAULT_ORIGINS,
            }
        )
