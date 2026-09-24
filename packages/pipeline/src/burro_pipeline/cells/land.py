"""The land each LSOA covers, and each area, in hectares.

One measure divides by it: homes per hectare. So it is worked out from a
source the registry holds for scoring, which the LSOA boundaries are and the
output area boundaries are not (ADR 0016).

The land of an LSOA is what its generalised outline encloses. The outline is
in the National Grid, whose unit is the metre, so what it encloses is in
square metres and nothing is projected. An area's land is the sum of the land
of its LSOAs. That is sound while an area is an MSOA, because an LSOA is part
of one MSOA. When areas are drawn by hand an LSOA may be split, and this
module will need the output area boundaries registered for scoring.

What is counted as land:

- Everything inside the outline: homes, roads, parks, reservoirs, docks.
- Nothing seaward of the mean high water mark, so not the tidal Thames.
- The generalised line, and not the full one. How far the two differ for an
  MSOA was measured once, and is in `docs/research/data/m1-files.md`.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from burro_pipeline.cells.shapes import Shape, hectares, read_outlines
from burro_pipeline.cells.spine import LSOA, Spine
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use
from burro_pipeline.rounding import to_places

BOUNDARIES = "ons-lsoa-2021"
# The registry entry covers this version and no other.
BOUNDARIES_EDITION = "BGC V5"
# Hectares are kept to four decimal places, which is a square metre.
DECIMALS = 4

MEASURED = Method(
    derivation_id="land_inside_outline@1",
    sentence="The land inside the outlines of the area's small census areas, from boundaries "
    "their publisher generalised and cut at the mean high water mark, in hectares to 4 decimal "
    "places.",
    kind=Kind.MEASURED,
    parameters={"decimal_places": DECIMALS},
    code="burro_pipeline.cells.land",
)


def kept(land: float) -> float:
    """Land as it is kept: in hectares to four decimal places, with a half taken upward."""
    return to_places(land, DECIMALS)


@dataclass(frozen=True)
class Land:
    """The land of each LSOA and of each area, in hectares."""

    of_lsoa: Mapping[str, float]
    of_area: Mapping[str, float]
    # The file the outlines were read from, by id.
    file_id: str


def land_of(spine: Spine, shapes: Mapping[str, Shape], file_id: str) -> Land:
    """The land of every LSOA of the spine, and of every area. It stops if an LSOA has none."""
    missing = [lsoa for lsoa in spine.lsoas if lsoa not in shapes]
    if missing:
        raise LockError("input_is_as_described", file_id, "an LSOA has no outline")
    of_lsoa = {lsoa: kept(hectares(shapes[lsoa])) for lsoa in spine.lsoas}
    if not all(land > 0 for land in of_lsoa.values()):
        raise LockError("input_is_as_described", file_id, "an LSOA covers no land")
    parts: dict[str, list[float]] = {area.area_id: [] for area in spine.areas}
    for lsoa in spine.lsoas:
        parts[spine.area_of_lsoa[lsoa]].append(of_lsoa[lsoa])
    of_area = {area_id: kept(math.fsum(land)) for area_id, land in parts.items()}
    return Land(of_lsoa=of_lsoa, of_area=of_area, file_id=file_id)


def read(opened: Opened, spine: Spine) -> dict[str, Shape]:
    """The outline of each of London's LSOAs, on the National Grid."""
    return read_outlines(opened, LSOA, frozenset(spine.lsoas))


def build(inputs: Inputs, spine: Spine) -> Land:
    """The land of every LSOA and every area, from the files of the build."""
    opened = inputs.open(BOUNDARIES, Use.SCORING, edition=BOUNDARIES_EDITION)
    return land_of(spine, read(opened, spine), opened.file_id)
