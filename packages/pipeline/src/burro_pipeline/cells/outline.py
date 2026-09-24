"""Each area's outline: its output areas joined, as a map can draw it.

The outlines are the statistics office's generalised boundaries of output
areas, which it has already simplified and cut at the mean high water mark. An
area's outline is the outlines of its output areas joined, with every line
between them taken out. Nothing else is simplified: no point of the
publisher's line is moved or dropped. Each point is then turned from the
National Grid to longitude and latitude and written to six decimal places.

So the tidal Thames is in no area, and two areas that face each other across
it share no side and are not neighbours.

The boundaries are registered for cells, for the gazetteer and for display,
and not for scoring. So no figure is worked out from an outline made here. The
land an area covers comes from the LSOA boundaries: see `land.py`.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_pipeline.cells.shapes import (
    DECIMALS,
    Point,
    Shape,
    as_geojson,
    fit_together,
    joined,
    longitude_and_latitude,
    pieces,
    point_inside,
    read_outlines,
    sharing_a_side,
    vertices,
)
from burro_pipeline.cells.spine import OA, Spine
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

BOUNDARIES = "ons-output-areas-2021"
# The generalised boundaries, which are the ones to draw. The registry asks that the
# version is pinned.
BOUNDARIES_EDITION = "BGC V2"

JOINED = Method(
    derivation_id="outline_of_output_areas@1",
    sentence="The outlines of the area's census output areas joined into one, from boundaries "
    "their publisher generalised and cut at the mean high water mark, with each point given to "
    "6 decimal places of longitude and latitude.",
    kind=Kind.MEASURED,
    parameters={"decimal_places": DECIMALS},
    code="burro_pipeline.cells.outline",
)


@dataclass(frozen=True)
class Outline:
    """One area as a map draws it."""

    area_id: str
    # A GeoJSON geometry: a polygon or a multipolygon, in longitude and latitude.
    geometry: Mapping[str, object]
    # A point inside the largest piece of the outline, as longitude and latitude.
    centre: Point
    # The areas that share a side with this one, in the order of their ids.
    neighbours: tuple[str, ...]
    # How many output areas were joined, and how many the area has.
    units_used: int
    units_expected: int
    # How many points the outline is drawn with, and how many pieces it is in.
    points: int
    pieces: int


def outlines_of(spine: Spine, shapes: Mapping[str, Shape], file_id: str) -> dict[str, Outline]:
    """The outline of every area, from the outlines of output areas.

    It stops if an output area has no outline, or if the areas' outlines do
    not fit together: an outline with a hole in it where an output area
    should be is not the area's outline.
    """
    of_area: dict[str, list[Shape]] = {area.area_id: [] for area in spine.areas}
    expected: dict[str, int] = dict.fromkeys(of_area, 0)
    for cell in spine.cells:
        area_id = spine.area_of[cell.oa]
        expected[area_id] += 1
        if cell.oa not in shapes:
            raise LockError("input_is_as_described", file_id, "an output area has no outline")
        of_area[area_id].append(shapes[cell.oa])
    whole = {area_id: joined(parts) for area_id, parts in sorted(of_area.items())}
    if not fit_together(list(whole.values())):
        raise LockError("input_is_as_described", file_id, "the outlines do not fit together")
    beside = sharing_a_side(whole)
    return {
        area_id: Outline(
            area_id=area_id,
            geometry=as_geojson(shape),
            centre=longitude_and_latitude(*point_inside(shape)),
            neighbours=beside[area_id],
            units_used=len(of_area[area_id]),
            units_expected=expected[area_id],
            points=vertices(shape),
            pieces=pieces(shape),
        )
        for area_id, shape in whole.items()
    }


def read(opened: Opened, spine: Spine) -> dict[str, Shape]:
    """The outline of each of London's output areas, on the National Grid."""
    return read_outlines(opened, OA, frozenset(cell.oa for cell in spine.cells))


def build(inputs: Inputs, spine: Spine) -> dict[str, Outline]:
    """The outline of every area, from the files of the build."""
    opened = inputs.open(BOUNDARIES, Use.CELLS, edition=BOUNDARIES_EDITION)
    return outlines_of(spine, read(opened, spine), opened.file_id)


def feature_collection(outlines: Mapping[str, Outline]) -> dict[str, object]:
    """The outlines as `geometry.json` holds them: one feature for each area, in id order."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": area_id,
                "properties": {"area_id": area_id},
                "geometry": outlines[area_id].geometry,
            }
            for area_id in sorted(outlines)
        ],
    }
