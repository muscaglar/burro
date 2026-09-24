"""Route 8: finding a destination by name, in Burro's own index.

It is a `POST`, so that what a person types into the search box travels in a
body and never in a URL. The text is used to look up ids and then dropped.
"""

from burro_core.places import Match
from burro_core.release import Release
from fastapi import APIRouter

from burro_api.deps import Ctx
from burro_api.routes.common import PREFIX, WITH_BODY, envelope
from burro_api.wire import Envelope, FoundPlace, PlacesData, PlaceSearchBody

router = APIRouter(prefix=PREFIX)


def _found(match: Match, release: Release) -> FoundPlace | None:
    place = release.place(match.id)
    coarse = release.place(place.coarse_place_id) if place else None
    if place is None or coarse is None:
        return None
    return FoundPlace(
        place_id=place.place_id, name=place.name, kind=place.kind, coarse_name=coarse.name
    )


@router.post("/places/search", response_model=Envelope[PlacesData], responses=WITH_BODY)
def search_places(body: PlaceSearchBody, context: Ctx) -> Envelope[PlacesData]:
    """The places that match, best first."""
    matches = context.names.search_places(body.q, body.limit)
    found = (_found(match, context.release) for match in matches)
    return envelope(context, PlacesData(places=tuple(place for place in found if place)))
