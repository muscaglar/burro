"""What the routes share: the envelope, the checks on a spec, and how a ranking is served."""

import json
import zlib
from collections.abc import Mapping
from dataclasses import asdict
from typing import Annotated, Any, TypedDict

from burro_core.ids import Tenure
from burro_core.rank import Filtered, RankedArea, RankResult, Unranked
from burro_core.release import Neighbourhood, Release
from burro_core.spec import PreferenceSpec, check_spec, default_spec
from fastapi import Depends, Request, Response

from burro_api.boundary import REQUEST_ID
from burro_api.deps import Context
from burro_api.errors import spec_refused
from burro_api.providers.choose import Told
from burro_api.wire import AreaSummary, Envelope, ErrorEnvelope, NamedPlace, Score

# Every route but the health check. Each group of routes carries it, so that a
# route's own `path` is the whole template, whatever it is later included in.
PREFIX = "/v1"
DEFAULT_LIMIT = 20

# Every error is one envelope. Naming it for each status keeps the framework's
# own error shape, which repeats the input, out of the OpenAPI document.
Responses = dict[int | str, dict[str, Any]]
_ERROR: dict[str, Any] = {"model": ErrorEnvelope}
ANY_ROUTE: Responses = {500: _ERROR}
WITH_BODY: Responses = {400: _ERROR, 413: _ERROR, 415: _ERROR, 422: _ERROR, 500: _ERROR}
# A route with a parameter in its path is given a 422 by the framework, asked for or not.
NOT_FOUND: Responses = {404: _ERROR, 422: _ERROR}
GONE: Responses = {410: _ERROR}
# It has no body, and so no envelope. The synthetic flag is in its header.
NOT_MODIFIED: Responses = {304: {"description": "The release the caller holds is still loaded"}}
# A browser may keep the answer, and must ask each time whether it still stands.
ASK_EACH_TIME = "no-cache"


def envelope[T](context: Context, data: T) -> Envelope[T]:
    return Envelope[T](meta=context.meta, data=data)


def _request_id(request: Request) -> str:
    found = request.scope.get(REQUEST_ID)
    return found if isinstance(found, str) else ""


RequestId = Annotated[str, Depends(_request_id)]


class NotModified(Exception):
    """The caller holds the answer that would be given. Answered 304, with no body."""

    def __init__(self, headers: Mapping[str, str]) -> None:
        super().__init__()
        # The headers of the answer that stands: ours, and never what was sent.
        self.headers = dict(headers)


def told_tag(told: Told) -> str:
    """Eight characters that change when what people are told changes.

    A checksum of text of Burro's own. It is of nothing a person sent, and it
    says nothing of the release.
    """
    said = json.dumps(asdict(told), sort_keys=True, ensure_ascii=False).encode()
    return f"{zlib.crc32(said):08x}"


def release_headers(context: Context, told: Told | None = None) -> dict[str, str]:
    """The headers of an answer that may be kept: the tag names the release that made it.

    Where the answer also says who reads what is typed, the tag names that
    too. An answer that tells of one reader is then never said to stand once
    the service is set to another.
    """
    tag = context.meta.release_id if told is None else f"{context.meta.release_id}.{told_tag(told)}"
    return {"Cache-Control": ASK_EACH_TIME, "ETag": f'"{tag}"'}


def of_the_release(
    context: Context, request: Request, response: Response, told: Told | None = None
) -> None:
    """Mark a response that is a function of the release alone, so it may be kept.

    The address of such a route does not name the release. So a browser asks
    each time, and is told that what it holds still stands while the release
    does. What it sent is compared and never sent back. `told` is given by
    the one route that says who reads what is typed.
    """
    headers = release_headers(context, told)
    held = request.headers.get("if-none-match", "").split(",")
    if headers["ETag"] in {tag.strip().removeprefix("W/") for tag in held}:
        raise NotModified(headers)
    response.headers.update(headers)


def check(spec: PreferenceSpec, release: Release) -> None:
    """Refuse a spec that names what this release does not have, with paths and codes."""
    problems = check_spec(spec, release)
    if problems:
        raise spec_refused(problems)


def default_for(release: Release, tenure: Tenure) -> PreferenceSpec:
    """The default spec, without any weight this release cannot rank on.

    A release carries the features it has a cleared source for, which may be
    fewer than the catalogue holds. A default that weighted one of the others
    would be refused by the first ranking.
    """
    spec = default_spec(tenure)
    ranked = {metric.feature_id for metric in release.metrics if metric.rankable}
    return spec.replace(weights=tuple(w for w in spec.weights if w.feature_id in ranked))


class RankingFields(TypedDict):
    """The fields of `wire.Ranking`, for the two routes that serve a ranking."""

    scores: tuple[Score, ...]
    ranked: tuple[RankedArea, ...]
    areas_ranked: int
    areas_listed: int
    filtered: tuple[Filtered, ...]
    unranked: tuple[Unranked, ...]
    empty_spec: bool


def places_of(spec: PreferenceSpec, release: Release) -> tuple[NamedPlace, ...]:
    """Each place a spec names, by the release's name for it, in the spec's order.

    It is for a spec that has passed `check`, so the release has every place.
    """
    found = (release.place(commute.place_id) for commute in spec.commutes)
    return tuple(
        NamedPlace(place_id=place.place_id, name=place.name, kind=place.kind)
        for place in found
        if place is not None
    )


def ranking(result: RankResult, limit: int) -> RankingFields:
    """A ranking as it is served: a score for every area, and the first `limit` in full.

    It says how many areas are ranked and how many of them are listed, so
    that a list which stops short of the last area never reads as the whole.
    """
    listed = result.ranked[:limit]
    return RankingFields(
        scores=tuple(
            Score(
                area_id=area.area_id,
                score=area.score,
                # Counted by core, from the contributions of the area.
                counted=area.counted,
                present=area.present,
            )
            for area in result.ranked
        ),
        ranked=listed,
        areas_ranked=len(result.ranked),
        areas_listed=len(listed),
        filtered=result.filtered,
        unranked=result.unranked,
        empty_spec=result.empty_spec,
    )


def summary(area: Neighbourhood) -> AreaSummary:
    return AreaSummary(
        area_id=area.area_id,
        slug=area.slug,
        name=area.name,
        borough=area.borough,
        centroid=area.centroid,
        rankable=area.rankable,
        named=area.named,
    )
