"""Routes 4, 5 and 6: the areas of the release. Each is a function of the release alone.

So each may be kept by a browser, which asks each time whether the release
still stands. A path here holds an area's id or its slug, which come from the
release and never from what a person typed.

Where an area sits on a vibe is read from the release, and what is said of it
is core's: no band, no likeness and no sentence is worked out here.
"""

from burro_core.facts import fact_id, facts_for
from burro_core.ids import FactKind, Tenure, segments_for
from burro_core.likeness import similar
from burro_core.portrait import portrait
from burro_core.release import Neighbourhood, Release
from fastapi import APIRouter, Request, Response

from burro_api.deps import Ctx
from burro_api.errors import ApiError
from burro_api.routes.common import (
    ANY_ROUTE,
    NOT_FOUND,
    NOT_MODIFIED,
    PREFIX,
    envelope,
    of_the_release,
    summary,
)
from burro_api.wire import (
    AreaData,
    AreasData,
    BandMark,
    Envelope,
    ErrorCode,
    GeoFeature,
    GeometryData,
    GeoProperties,
    Similar,
    VibeBands,
)

router = APIRouter(prefix=PREFIX)


def _bands(release: Release) -> tuple[VibeBands, ...]:
    """Where every area sits on every vibe a map may be coloured by, as the release holds it."""
    return tuple(
        VibeBands(
            tag_id=vibe.tag_id,
            marks=tuple(
                BandMark(
                    area_id=area.area_id,
                    # `null` for an area that cannot be placed. Nothing is filled in.
                    band=row.band if row else None,
                    spread_low=row.spread_low if row else None,
                    spread_high=row.spread_high if row else None,
                )
                for area in release.neighbourhoods
                for row in [release.tag(area.area_id, vibe.tag_id)]
            ),
        )
        for vibe in release.vibes
        if vibe.lens
    )


@router.get("/areas", response_model=Envelope[AreasData], responses=ANY_ROUTE | NOT_MODIFIED)
def list_areas(context: Ctx, request: Request, response: Response) -> Envelope[AreasData]:
    """Every area of the release, by id, and where each sits on every vibe."""
    of_the_release(context, request, response)
    release = context.release
    found = tuple(summary(area) for area in release.neighbourhoods)
    return envelope(context, AreasData(areas=found, bands=_bands(release)))


# Declared before the route for one area, or `geometry` would be read as a slug.
@router.get(
    "/areas/geometry", response_model=Envelope[GeometryData], responses=ANY_ROUTE | NOT_MODIFIED
)
def get_geometry(context: Ctx, request: Request, response: Response) -> Envelope[GeometryData]:
    """The boundary of every area, as a GeoJSON feature collection."""
    of_the_release(context, request, response)
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
    tags = (release.tag(area_id, vibe.tag_id) for vibe in release.vibes)
    costs = (
        release.cost(area_id, tenure, segment)
        for tenure in Tenure
        for segment in segments_for(tenure)
    )
    neighbours = (release.neighbourhood(neighbour) for neighbour in area.neighbours)
    drawn = portrait(release, area_id)
    assert drawn is not None  # the release has the area
    return AreaData(
        area=area,
        # A value that is not known is served as `null`. Nothing is filled in.
        features=tuple(row for row in features if row is not None),
        tags=tuple(row for row in tags if row is not None),
        cost=tuple(row for row in costs if row is not None),
        stations=release.stations(area_id),
        neighbours=tuple(summary(found) for found in neighbours if found is not None),
        portrait=drawn,
        # What orders them is never served: a distance is not a fact about a place.
        similar=tuple(
            Similar(area_id=like.area_id, fact_id=fact_id(area_id, FactKind.LIKENESS, like.area_id))
            for like in similar(release, area_id)
        ),
        facts=facts_for(release, area_id, None),
    )


@router.get(
    "/areas/{id_or_slug}",
    response_model=Envelope[AreaData],
    responses=ANY_ROUTE | NOT_FOUND | NOT_MODIFIED,
)
def get_area(
    id_or_slug: str, context: Ctx, request: Request, response: Response
) -> Envelope[AreaData]:
    """One area: what the release holds about it, and the facts a profile page shows."""
    release = context.release
    area_id = context.area_id_for_slug.get(id_or_slug, id_or_slug)
    found = release.neighbourhood(area_id)
    if found is None:
        raise ApiError(ErrorCode.AREA_NOT_FOUND)
    of_the_release(context, request, response)
    return envelope(context, _profile(found, release))
