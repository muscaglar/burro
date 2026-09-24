"""Green cover: the share of an area's land that lies inside a public park or garden.

The sites come from OS Open Greenspace, which `green_sites.py` reads. The land
comes from the boundaries of LSOAs, which `cells/land.py` measures.

**It is public parks and gardens, and not green space.** The figure counts one
kind of site, and the licence registry asks that the product is never
described as all green space. `LABEL` says parks and gardens, and core names
the measure the same, so a build carries it. No word of the measure says green
space, or says of an area that it is greener than another. Do not give it a
name that does.

It is a share of land. The design of the vibes gave the id another reading,
the share of homes within 300 metres of a public park or garden. No module
works that out. Core defines the measure as it is built here.

The design asks that 20 named commons, heaths and forests are looked for in
the file before any figure of parks is shown. That check has not been made:
the list is the founder's to give.

Which sites count, and why. The publisher gives every site one of ten kinds.
The file names the kinds and defines none of them, and no page of the
publisher was opened for this. So the choice rests on the names alone:

| Kind | Counts | Why |
|---|---|---|
| Public Park Or Garden | Yes | It is the one kind the publisher names as public |
| Playing Field, Play Space | No | Named for a use. The file does not say who may go in |
| Tennis Court, Bowling Green, Other Sports Facility | No | The same |
| Allotments Or Community Growing Spaces | No | The same |
| Religious Grounds | No | The same |
| Cemetery, Golf Course | No | The same, and the design says neither ever counts |

The file has no kind for a common, a heath, a wood or a forest. One is
counted where the publisher maps it as a public park or garden, and not
otherwise. So the figure is a floor: it is the land that is surely a public
park or garden, and an area holds other green land that it leaves out. The
licence registry asks that the product is never described as all green space.

How a figure is made:

1. The outline of each LSOA is laid over the outlines of the parks, and the
   land of the LSOA that lies inside any park is measured, in hectares. A park
   may lie inside another, as a garden inside a park does. Land inside two is
   counted once.
2. An area's figure is the park land of its LSOAs over the land of its LSOAs,
   times 100. That is `lsoa_ratio_by_homes`, which the pipeline design names:
   one sum over another, and never a mean of shares.
3. It is given to one decimal place. The two outlines come from two
   publishers, and do not agree to the metre.

Nothing is filled in. An LSOA that lies on a square of the National Grid that
no file was read for has no park land that is known, and the coverage of its
area falls by its homes. An LSOA that the files cover and that no park touches
holds nought, and nought is what the figure says: the publisher mapped no park
there.

The land is what the generalised outline of an LSOA encloses, as it is for
homes per hectare. When areas are drawn by hand an LSOA may be split between
two, and the park land must then be measured on the outlines of output areas,
which are not registered for scoring today.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import land
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.shapes import Shape, hectares_inside
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import green_sites
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.green_sites import Greenspace
from burro_pipeline.derive.methods import (
    LSOA_RATIO_BY_HOMES,
    Worked,
    lsoa_ratio_by_homes,
    row_of,
    to_places,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.GREEN_COVER
SOURCE = green_sites.SOURCE
# The one kind of site that counts.
COUNTS = green_sites.PARK
# How many kinds the publisher has that do not count.
LEFT_OUT = len(green_sites.KINDS) - 1
# A share is shown as a percentage.
TIMES = 100
# Park land is kept to this many decimal places of a hectare, as the land is.
HECTARE_DECIMALS = land.DECIMALS
# A figure is given to this many decimal places.
DECIMALS = 1
# What the sites are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POLYGON
PUBLISHER, PRODUCT = green_sites.PUBLISHER, "OS Open Greenspace"
OF_THE_LAND = "Office for National Statistics"

INSIDE_SITES = Method(
    derivation_id="land_inside_sites@1",
    sentence="The land of each small census area that lies inside a site, measured where the "
    "outline of the area lies over the outlines of the sites, with land inside two sites counted "
    "once, in hectares to 4 decimal places.",
    kind=Kind.MEASURED,
    parameters={"decimal_places": HECTARE_DECIMALS},
    code="burro_pipeline.derive.green_cover",
)
# The arithmetic, how the land was measured and how the park land was: what a methods page
# prints beside the measure. The first is the one a row names.
METHOD = LSOA_RATIO_BY_HOMES
METHODS: tuple[Method, ...] = (METHOD, land.MEASURED, INSIDE_SITES)
# What a person reads beside the figure: it counts public parks and gardens alone. It is
# core's name for the measure too.
LABEL = "Public parks and gardens as a share of the area"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The land inside the sites that {publisher} maps as {counts} in {product} as at {sites}, as "
    "a share of all the land inside the boundaries of the area's small census areas as at "
    "{land}, which the {of_the_land} generalised and cut at the mean high water mark: land "
    "inside two sites is counted once, the figure is given to {places} decimal place with a "
    "half taken upward, and none of the publisher's other {left_out} kinds of site is counted, "
    "nor any common, wood, private garden or street tree that it does not map as such a site, "
    "so it is not all the green space of an area."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts only the land its publisher maps as a public park or garden, so playing fields, "
    "cemeteries, golf courses, private gardens, street trees and any common or wood that is not "
    "mapped as a park are left out, and an area holds more green land than this figure counts.",
    "It cannot see what a park is like: whether it is grass, water or paving, how well it is "
    "kept, or when its gates are open.",
)


@dataclass(frozen=True)
class Cover:
    """Green cover for every area, in percent, with what stands behind each figure."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # The park land of each LSOA that the files cover, in hectares.
    inside: Mapping[str, float]
    # How many sites count as a park, of how many the files hold.
    parks: int
    sites: int


def is_a_tile(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return green_sites.is_a_tile(name)


def parks_of(green: Greenspace) -> list[Shape]:
    """The outline of every site that counts, in the order of their ids."""
    return [site.shape for _, site in sorted(green.sites.items()) if site.kind == COUNTS]


def park_land(green: Greenspace, outlines: Mapping[str, Shape]) -> dict[str, float]:
    """The park land of each LSOA that the files cover, in hectares.

    An LSOA that lies on a square no file was read for is left out: what parks
    it holds is not known. One that the files cover and no park touches holds
    nought.
    """
    covered = {lsoa: outline for lsoa, outline in outlines.items() if green.files_under(outline)}
    inside = hectares_inside(covered, parks_of(green))
    return {lsoa: land.kept(found) for lsoa, found in inside.items()}


def figures(inside: Mapping[str, float], measured: Land, found: Spine) -> dict[str, Worked]:
    """Green cover for every area of the spine, in percent, or why an area has no figure."""
    if any(inside[lsoa] > measured.of_lsoa[lsoa] for lsoa in inside):
        raise ValueError("the park land of an LSOA is no more than its land")
    worked = lsoa_ratio_by_homes(
        inside, measured.of_lsoa, found.lsoa_of, found.weights, times=float(TIMES)
    )
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def _when(period: Period) -> str:
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports, which core gives it too. The period is the one the
    receipts of the sites give.
    The land is of the day its receipt gives.
    """
    period = {receipt.source_id: _when(receipt.data_period) for receipt in files}
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        source_ids=period,
        vintage=as_at,
        definition=DEFINITION.format(
            publisher=PUBLISHER,
            counts=COUNTS,
            product=PRODUCT,
            sites=as_at,
            land=period[land.BOUNDARIES],
            of_the_land=OF_THE_LAND,
            places=DECIMALS,
            left_out=LEFT_OUT,
        ),
    )


def _files_of(
    green: Greenspace, outlines: Mapping[str, Shape], found: Spine
) -> dict[str, tuple[str, ...]]:
    """For each area, the files of sites its figure rests on: those of the squares it lies on.

    An area no file covers rests on every file that was read: each was looked
    in, and none was of its square.
    """
    every = tuple(receipt.file_id for receipt in green.files)
    under: dict[str, set[str]] = {area.area_id: set() for area in found.areas}
    for lsoa in found.lsoas:
        under[found.area_of_lsoa[lsoa]] |= set(green.files_under(outlines[lsoa]) or ())
    return {area: tuple(sorted(files)) or every for area, files in under.items()}


def build(inputs: Inputs, found: Spine, measured: Land, *, edition: str | None = None) -> Cover:
    """Green cover for every area and its evidence, from the files of the build.

    The gate is asked about the sites and about the boundaries before either
    is read. `found` and `measured` are the spine and the land of the same
    build. A row of evidence names the files of sites its area lies on, the
    boundaries, the lookup, and the table of homes that coverage is counted by.
    """
    green = green_sites.build(inputs, edition=edition)
    boundaries = inputs.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if boundaries.file_id != measured.file_id or not set(found.inputs) <= set(handed):
        raise ValueError("the spine and the land are made from files of this build")
    outlines = land.read(boundaries, found)
    if any(lsoa not in outlines for lsoa in found.lsoas):
        raise LockError("input_is_as_described", boundaries.file_id, "an LSOA has no outline")
    inside = park_land(green, outlines)
    worked = figures(inside, measured, found)
    ground = sorted({boundaries.file_id, *found.inputs})
    of_sites = _files_of(green, outlines, found)
    rows = tuple(
        row_of(
            fact_id(area, FactKind.FEATURE, FEATURE),
            worked[area],
            METHOD,
            [handed[file_id] for file_id in sorted({*of_sites[area], *ground})],
        )
        for area in sorted(worked)
    )
    behind = sorted({receipt.file_id for receipt in green.files} | set(ground))
    files = tuple(handed[file_id] for file_id in behind)
    return Cover(
        worked=worked,
        rows=rows,
        metric=metric_of(files, green.as_at),
        files=files,
        geography=KEYED_BY,
        inside=inside,
        parks=len(parks_of(green)),
        sites=len(green.sites),
    )


def hectares_in(inside: Mapping[str, float]) -> float:
    """The park land of every LSOA that has any, added up, in hectares."""
    return land.kept(math.fsum(inside.values()))
