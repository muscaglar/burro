"""What the routes share: the envelope, the checks on a spec, and how a ranking is served."""

from typing import Annotated, Any, TypedDict

from burro_core.ids import Tenure
from burro_core.rank import Filtered, RankedArea, RankResult, Unranked
from burro_core.release import Neighbourhood, Release
from burro_core.spec import PreferenceSpec, check_spec, default_spec
from fastapi import Depends, Request, Response

from burro_api.boundary import REQUEST_ID
from burro_api.deps import Context
from burro_api.errors import spec_refused
from burro_api.wire import AreaSummary, Envelope, ErrorEnvelope, Score

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


def envelope[T](context: Context, data: T) -> Envelope[T]:
    return Envelope[T](meta=context.meta, data=data)


def _request_id(request: Request) -> str:
    found = request.scope.get(REQUEST_ID)
    return found if isinstance(found, str) else ""


RequestId = Annotated[str, Depends(_request_id)]


def of_the_release(context: Context, response: Response) -> None:
    """Mark a response that is a function of the release alone, so it may be cached."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["ETag"] = f'"{context.meta.release_id}"'


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
    filtered: tuple[Filtered, ...]
    unranked: tuple[Unranked, ...]
    empty_spec: bool


def ranking(result: RankResult, limit: int) -> RankingFields:
    """A ranking as it is served: a score for every area, and the first `limit` in full."""
    return RankingFields(
        scores=tuple(Score(area_id=area.area_id, score=area.score) for area in result.ranked),
        ranked=result.ranked[:limit],
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
    )
