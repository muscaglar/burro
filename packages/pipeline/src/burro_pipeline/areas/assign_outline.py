"""The outline of each drafted area, as a map draws it.

An area's outline is the generalised outlines of its output areas joined, with
every line between them taken out, as `cells/outline.py` makes the outline of
an area of the first build. No point of the publisher's line is moved or
dropped. Each point is turned from the National Grid to longitude and latitude
by the one fixed operation of `cells/shapes.py`, and written to six decimal
places.

The tidal water is in no output area, so it is in no outline. An output area
that is in two pieces, such as one with an island, makes an outline in two
pieces, though the area's output areas all share sides. That is counted apart
from an area whose output areas do not join up.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_pipeline.areas.assign import Drawn
from burro_pipeline.cells.shapes import (
    Point,
    Shape,
    as_geojson,
    fit_together,
    joined,
    longitude_and_latitude,
    pieces,
    point_inside,
    vertices,
)


@dataclass(frozen=True)
class Outline:
    """One area as a map draws it."""

    area: str
    # A GeoJSON geometry: a polygon or a multipolygon, in longitude and latitude.
    geometry: Mapping[str, object]
    # A point inside the largest piece of the outline, as longitude and latitude.
    inside: Point
    # How many points the outline is drawn with, and how many pieces it is in.
    points: int
    pieces: int


@dataclass(frozen=True)
class Outlines:
    """The outline of every area, and whether they fit together with no gap and no overlap."""

    of: Mapping[str, Outline]
    fit_together: bool


def outlines_of(drawn: Mapping[str, Drawn], shapes: Mapping[str, Shape]) -> Outlines:
    """The outline of every area, from the outlines of its output areas.

    It stops if an output area has no outline: an outline with a hole where
    an output area should be is not the area's outline.
    """
    whole: dict[str, Shape] = {}
    for area in sorted(drawn):
        if any(oa not in shapes for oa in drawn[area].cells):
            raise ValueError("an output area has no outline")
        whole[area] = joined([shapes[oa] for oa in drawn[area].cells])
    return Outlines(
        of={
            area: Outline(
                area=area,
                geometry=as_geojson(shape),
                inside=longitude_and_latitude(*point_inside(shape)),
                points=vertices(shape),
                pieces=pieces(shape),
            )
            for area, shape in whole.items()
        },
        fit_together=fit_together(list(whole.values())),
    )


def feature_collection(outlines: Outlines) -> dict[str, object]:
    """The outlines as one GeoJSON document: a feature for each area, in the order of their ids."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": area,
                "properties": {"area_id": area},
                "geometry": outlines.of[area].geometry,
            }
            for area in sorted(outlines.of)
        ],
    }
