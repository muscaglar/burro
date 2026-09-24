"""Routes 4, 5 and 6: the areas of the release. Each is a function of the release alone.

So each may be cached, by the release id. A path here holds an area's id or
its slug, which come from the release and never from what a person typed.
"""

from burro_core.facts import facts_for
from burro_core.ids import TagId, Tenure, segments_for
from burro_core.release import Neighbourhood, Release
from fastapi import APIRouter, Response

from burro_api.deps import Ctx
from burro_api.errors import ApiError
from burro_api.routes.common import ANY_ROUTE, NOT_FOUND, PREFIX, envelope, of_the_release, summary
from burro_api.wire import (
    AreaData,
    AreasData,
    Envelope,
    ErrorCode,
    GeoFeature,
    GeometryData,
    GeoProperties,
)

router = APIRouter(prefix=PREFIX)


@router.get("/areas", response_model=Envelope[AreasData], responses=ANY_ROUTE)
def list_areas(context: Ctx, response: Response) -> Envelope[AreasData]:
    """Every area of the release, by id."""
    of_the_release(context, response)
    found = tuple(summary(area) for area in context.release.neighbourhoods)
    return envelope(context, AreasData(areas=found))


# Declared before the route for one area, or `geometry` would be read as a slug.
@router.get("/areas/geometry", response_model=Envelope[GeometryData], responses=ANY_ROUTE)
def get_geometry(context: Ctx, response: Response) -> Envelope[GeometryData]:
    """The boundary of every area, as a GeoJSON feature collection."""
    of_the_release(context, response)
    release = context.release
    features = tuple(
        GeoFeature(
            type="Feature",
            id=area.area_id,
            properties=GeoProperties(area_id=area.area_id),
            geometry=shape,
        )
        for area in release.neighbourhoods
        if (shape := release.geometry(area.area_id)) is not None
    )
    return envelope(context, GeometryData(type="FeatureCollection", features=features))


def _profile(area: Neighbourhood, release: Release) -> AreaData:
    area_id = area.area_id
    features = (release.feature(area_id, metric.feature_id) for metric in release.metrics)
    tags = (release.tag(area_id, tag_id) for tag_id in TagId)
    costs = (
        release.cost(area_id, tenure, segment)
        for tenure in Tenure
        for segment in segments_for(tenure)
    )
    neighbours = (release.neighbourhood(neighbour) for neighbour in area.neighbours)
    return AreaData(
        area=area,
        # A value that is not known is served as `null`. Nothing is filled in.
        features=tuple(row for row in features if row is not None),
        tags=tuple(row for row in tags if row is not None),
        cost=tuple(row for row in costs if row is not None),
        stations=release.stations(area_id),
        neighbours=tuple(summary(found) for found in neighbours if found is not None),
        facts=facts_for(release, area_id, None),
    )


@router.get(
    "/areas/{id_or_slug}",
    response_model=Envelope[AreaData],
    responses=ANY_ROUTE | NOT_FOUND,
)
def get_area(id_or_slug: str, context: Ctx, response: Response) -> Envelope[AreaData]:
    """One area: what the release holds about it, and the facts a profile page shows."""
    release = context.release
    area_id = context.area_id_for_slug.get(id_or_slug, id_or_slug)
    found = release.neighbourhood(area_id)
    if found is None:
        raise ApiError(ErrorCode.AREA_NOT_FOUND)
    of_the_release(context, response)
    return envelope(context, _profile(found, release))
