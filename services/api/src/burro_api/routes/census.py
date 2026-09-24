"""Route 13: the census figures of one area. It stands apart from every route that ranks.

It is the only route that reads the census, and the census is all it reads
but the name of the area. It takes an area and nothing else: no body, no
query and no spec, so nothing can be asked of it but one area's own table.
No route lists the figures of several areas, so no client can put one area
before another by a figure.

What is served is worked out by core's `panel`: a share, its count, and the
whole city's share beside it. No figure is worked out here.

The answer may not be kept and may not be indexed. A browser holds it while the
page is open and asks again on the next visit, and a search engine is asked to
leave it out.
"""

from burro_core.census import CensusPanel, panel
from fastapi import APIRouter, Request, Response

from burro_api.deps import Ctx
from burro_api.errors import ApiError
from burro_api.routes.common import ANY_ROUTE, NOT_FOUND, PREFIX, envelope
from burro_api.wire import Envelope, ErrorCode

router = APIRouter(prefix=PREFIX)

NO_STORE = "no-store"
NOT_INDEXED = "noindex, nosnippet"


@router.get(
    "/areas/{id_or_slug}/census",
    response_model=Envelope[CensusPanel],
    responses=ANY_ROUTE | NOT_FOUND,
)
def get_census(
    id_or_slug: str, context: Ctx, request: Request, response: Response
) -> Envelope[CensusPanel]:
    """The census figures of one area, beside the figures of the whole city and nothing else."""
    if request.url.query:
        # The route takes nothing. A query could only be a way to ask for more than one
        # area's own table, so it is refused, whatever it holds, and never read.
        raise ApiError(ErrorCode.INVALID_REQUEST)
    release = context.release
    area_id = context.area_id_for_slug.get(id_or_slug, id_or_slug)
    area = release.neighbourhood(area_id)
    if area is None:
        raise ApiError(ErrorCode.AREA_NOT_FOUND)
    census = context.deps.census
    found = None if census is None else panel(census, area.area_id, area.name)
    if found is None:
        raise ApiError(ErrorCode.CENSUS_NOT_AVAILABLE)
    response.headers["Cache-Control"] = NO_STORE
    response.headers["X-Robots-Tag"] = NOT_INDEXED
    return envelope(context, found)
