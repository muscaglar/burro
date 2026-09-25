"""What the routes depend on. Tests pass fakes; the service passes the real thing.

`Deps` is everything that can differ between a test and the running service:
the release, the interpreter, what people are told of who reads their words,
the explainer, the two stores, the clock and the source of ids. `Context`
adds what is worked out from the release once, when the app is made, so that
no request works it out again.
"""

import secrets
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Protocol, cast

from burro_core.census import Census
from burro_core.explain import Explainer
from burro_core.ids import InterpreterName
from burro_core.income import Income
from burro_core.interpret import Interpreter
from burro_core.places import Names
from burro_core.rank import ENGINE_VERSION
from burro_core.release import Release
from fastapi import Depends, Request

from burro_api.calls import TIMESTAMP_FORMAT, CallLog
from burro_api.providers.choose import Told
from burro_api.settings import DEFAULT_ORIGINS, DEFAULT_TIMEOUT_S
from burro_api.stores import ShareStore
from burro_api.wire import Meta

# 128 random bits, as URL-safe text.
SHARE_ID_BYTES = 16


class Clock(Protocol):
    def now(self) -> datetime:
        """The time, in UTC."""
        ...

    def elapsed(self) -> float:
        """Seconds on a clock that only runs forward, for measuring how long something took."""
        ...


class Ids(Protocol):
    def request_id(self) -> str: ...
    def call_id(self) -> str: ...
    def share_id(self) -> str: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def elapsed(self) -> float:
        return time.monotonic()


class RandomIds:
    def request_id(self) -> str:
        return str(uuid.uuid4())

    def call_id(self) -> str:
        return str(uuid.uuid4())

    def share_id(self) -> str:
        # Random, and never derived from the spec: holding a spec must not reveal a link.
        return secrets.token_urlsafe(SHARE_ID_BYTES)


@dataclass(frozen=True)
class Deps:
    release: Release
    interpreter: Interpreter
    explainer: Explainer
    shares: ShareStore
    calls: CallLog
    clock: Clock
    ids: Ids
    # What people are told of who reads what they type. It has no default: a
    # default would be "not sent to a language model", said of a service that
    # sends. Whoever makes a `Deps` takes it from the `Choice` the interpreter
    # was made from.
    told: Told
    # Recorded with a call to a model. Empty when the interpreter is the rules.
    model_id: str = ""
    # The census that was made for the release, or `None` where none is served. It stands
    # beside the release and is no part of it: one route reads it, and no other can.
    census: Census | None = None
    # The household income that was made for the release, or `None` where none is served.
    # It stands beside the release as the census does: one route reads it, and no other can.
    income: Income | None = None
    # How long route 1 waits for an interpreter before the rules answer in its place.
    model_timeout_s: float = DEFAULT_TIMEOUT_S
    # The origins a browser may call from, and no other.
    allowed_origins: tuple[str, ...] = DEFAULT_ORIGINS

    def __post_init__(self) -> None:
        by_rules = self.interpreter.name is InterpreterName.RULE
        # Text of our own, and nothing that was set.
        if self.told.model_reads is by_rules:
            raise ValueError("what people are told does not fit who reads")
        if self.census is not None and self.census.release_id != self.release.manifest.release_id:
            raise ValueError("the census was made for another release")
        if self.income is not None and self.income.release_id != self.release.manifest.release_id:
            raise ValueError("the household income was made for another release")


@dataclass(frozen=True)
class Context:
    deps: Deps
    meta: Meta
    names: Names
    area_id_for_slug: Mapping[str, str]

    @property
    def release(self) -> Release:
        return self.deps.release

    def timestamp(self) -> str:
        return self.deps.clock.now().astimezone(UTC).strftime(TIMESTAMP_FORMAT)


def context_for(deps: Deps) -> Context:
    manifest = deps.release.manifest
    return Context(
        deps=deps,
        meta=Meta(
            release_id=manifest.release_id,
            engine_version=ENGINE_VERSION,
            synthetic=manifest.synthetic,
            preview=manifest.preview,
        ),
        names=Names(deps.release),
        area_id_for_slug={area.slug: area.area_id for area in deps.release.neighbourhoods},
    )


def _context(request: Request) -> Context:
    return cast(Context, request.app.state.context)


Ctx = Annotated[Context, Depends(_context)]
