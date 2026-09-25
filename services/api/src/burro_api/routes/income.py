"""Route 14: the household income of one area. It stands apart from every route that ranks.

It is the only route that reads the estimate, and the estimate is all it reads
but the id of the area. It takes an area and nothing else: no body, no query
and no spec, so nothing can be asked of it but one area's own figure. No route
lists the figures of several areas, so no client can put one area before
another by it.

What is served is put into words by core's `shown`: the publisher's estimate,
the two limits round it, the year, and the publisher's own words for what it
is. No figure is worked out here, and none stands beside it.

The answer may not be kept and may not be indexed, as the census may not.
"""

from burro_core.income import IncomeShown, shown
from fastapi import APIRouter, Request, Response

from burro_api.deps import Ctx
from burro_api.errors import ApiError
from burro_api.routes.common import ANY_ROUTE, NOT_FOUND, PREFIX, envelope
from burro_api.wire import Envelope, ErrorCode

router = APIRouter(prefix=PREFIX)

NO_STORE = "no-store"
NOT_INDEXED = "noindex, nosnippet"


@router.get(
    "/areas/{id_or_slug}/income",
    response_model=Envelope[IncomeShown],
    responses=ANY_ROUTE | NOT_FOUND,
)
def get_income(
    id_or_slug: str, context: Ctx, request: Request, response: Response
) -> Envelope[IncomeShown]:
    """The household income of one area, as its publisher estimates it, and nothing else."""
    if request.url.query:
        # The route takes nothing. A query could only be a way to ask for more than one
        # area's own figure, so it is refused, whatever it holds, and never read.
        raise ApiError(ErrorCode.INVALID_REQUEST)
    release = context.release
    area_id = context.area_id_for_slug.get(id_or_slug, id_or_slug)
    area = release.neighbourhood(area_id)
    if area is None:
        raise ApiError(ErrorCode.AREA_NOT_FOUND)
    income = context.deps.income
    found = None if income is None else shown(income, area.area_id)
    if found is None:
        raise ApiError(ErrorCode.INCOME_NOT_AVAILABLE)
    response.headers["Cache-Control"] = NO_STORE
    response.headers["X-Robots-Tag"] = NOT_INDEXED
    return envelope(context, found)
