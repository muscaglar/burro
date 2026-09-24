"""Routes 9 and 10: sharing a search.

A share is the only place a spec is stored, and a person makes one on purpose.
Its id is random, so holding a spec does not reveal a link. What is stored
names a station or a district in place of a workplace or a school, unless the
sender asked for the exact places.
"""

from burro_core.rank import rank
from burro_core.release import Release
from burro_core.spec import Commute, PreferenceSpec, check_spec, spec_hash
from fastapi import APIRouter

from burro_api.deps import Ctx
from burro_api.errors import ApiError
from burro_api.routes.common import (
    ANY_ROUTE,
    DEFAULT_LIMIT,
    GONE,
    NOT_FOUND,
    PREFIX,
    WITH_BODY,
    check,
    envelope,
    places_of,
    ranking,
)
from burro_api.stores import StoredShare
from burro_api.wire import Envelope, ErrorCode, ShareBody, ShareCreated, ShareData

router = APIRouter(prefix=PREFIX)


def coarsen(spec: PreferenceSpec, release: Release) -> PreferenceSpec:
    """The spec with each destination replaced by the coarse place that stands in for it.

    If two commutes come to the same coarse place, the one with the lower
    `place_id` before coarsening is kept and the other is dropped.
    """
    kept: dict[str, Commute] = {}
    # A spec keeps its commutes in `place_id` order, so the lower id is met first.
    for commute in spec.commutes:
        place = release.place(commute.place_id)
        coarse = place.coarse_place_id if place else commute.place_id
        kept.setdefault(coarse, commute.replace(place_id=coarse))
    return spec.replace(commutes=tuple(kept.values()))


@router.post("/shares", response_model=Envelope[ShareCreated], responses=WITH_BODY)
def create_share(body: ShareBody, context: Ctx) -> Envelope[ShareCreated]:
    """Store a search and give back the id of a link to it."""
    deps, release = context.deps, context.release
    check(body.spec, release)
    stored = body.spec if body.exact_destinations else coarsen(body.spec, release)
    made = StoredShare(
        share_id=deps.ids.share_id(),
        spec=stored,
        # The stored spec ranks a little differently from the search it came from.
        coarsened=stored != body.spec,
        original_release_id=context.meta.release_id,
        created_at=context.timestamp(),
    )
    deps.shares.put(made)
    return envelope(
        context,
        ShareCreated(
            share_id=made.share_id,
            spec=made.spec,
            coarsened=made.coarsened,
            # Of the spec as stored, so a place that was replaced is never named.
            places=places_of(made.spec, release),
        ),
    )


@router.get(
    "/shares/{share_id}",
    response_model=Envelope[ShareData],
    responses=ANY_ROUTE | NOT_FOUND | GONE,
)
def get_share(share_id: str, context: Ctx) -> Envelope[ShareData]:
    """A shared search, ranked now on the release that is loaded."""
    release = context.release
    found = context.deps.shares.get(share_id)
    if found is None:
        raise ApiError(ErrorCode.SHARE_NOT_FOUND)
    # A share outlives releases. If a place, an area or a feature it names has
    # gone, it can no longer be shown.
    if check_spec(found.spec, release):
        raise ApiError(ErrorCode.RELEASE_CHANGED)
    result = rank(found.spec, release)
    return envelope(
        context,
        ShareData(
            spec=found.spec,
            spec_hash=spec_hash(found.spec),
            coarsened=found.coarsened,
            stale=found.original_release_id != context.meta.release_id,
            original_release_id=found.original_release_id,
            places=places_of(found.spec, release),
            **ranking(result, DEFAULT_LIMIT),
        ),
    )
