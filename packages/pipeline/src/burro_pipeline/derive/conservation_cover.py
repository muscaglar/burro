"""Conservation cover: the share of an area's land that lies inside a conservation area.

The conservation areas come from the planning data platform, which
`planning_data.py` reads. The land comes from the boundaries of LSOAs, which
`cells/land.py` measures. It is a figure about land and buildings. It says
nothing of who lives anywhere.

The licence registry puts five conditions on the source. Each is kept here:

| The registry asks | What is done |
|---|---|
| De-duplicate at ingest | Two records that cover much the same land are one area, counted once |
| Keep the provider of each record | Each outline carries its provider and its quality |
| Treat missing coverage as unknown, not zero | An authority with no area of its own has no figure |
| Check coverage for all 33 London authorities | `Cover.authorities` counts each, at every build |
| Never let this source decide a tag alone | Core places no vibe on under 60 in 100 of its recipe |

How a figure is made:

1. **Which records.** A record that had ended by the day of the file is left
   out. So is a record whose place is a point: it encloses no land. An outline
   whose rings cross is mended, and counted as mended.
2. **One record for each area.** The publisher says the file holds
   duplicates. Two records are taken to be one conservation area where the
   land they share is half or more of the land the two cover together. One is
   kept: the one its provider gives as authoritative, then the one entered
   last, then the one whose number is lowest. A small area that lies inside a
   large one is not a duplicate of it, and both are kept.
3. **Which authorities.** Each area that is kept is given to the authority
   that holds most of the land it has in London. An authority is covered
   where it holds half or more of one such area, of all that the outline
   encloses. One that is not covered sent nothing that the file holds. What
   it has is not known, so every area in it has no figure, and never nought.
   A conservation area of a place outside London may cross London's edge by
   a few metres. It is given to the authority it crosses into, and its land
   there is conservation land, but it does not make that authority covered:
   it says nothing of what the authority sent. An area that lies over a line
   is still counted on both sides of it, where both sides are covered.
4. **The land.** The outline of each LSOA of a covered authority is laid over
   the conservation areas, and the land of the LSOA that lies inside any is
   measured, in hectares. Land inside two is counted once.
5. **The figure.** The conservation land of an area's LSOAs over the land of
   its LSOAs, times 100. That is `lsoa_ratio_by_homes`: one sum over another,
   and never a mean of shares. It is given to one decimal place.

An area in a covered authority that no conservation area touches holds
nought, and nought is what the figure says: its authority sent its areas, and
none is there.

What the code cannot tell is an authority that sent some of its areas and not
all. The file does not say how many an authority has. So the count of each
authority is kept, by provider and by quality, for a person to hold against
the authority's own list. `docs/research/data/heritage.md` has the counts.

The land is what the generalised outline of an LSOA encloses, cut at the mean
high water mark. A conservation area that takes in the tidal river is counted
for its land alone.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import land
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.shapes import Shape, hectares, hectares_inside, joined
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import planning_data
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.heritage_shapes import (
    MULTIPOLYGON,
    POINT,
    POLYGON,
    box_round,
    hectares_in_each,
    in_degrees,
    outline_from,
    share_of_both,
    sharing_land,
)
from burro_pipeline.derive.methods import (
    LSOA_RATIO_BY_HOMES,
    Worked,
    lsoa_ratio_by_homes,
    row_of,
    to_places,
)
from burro_pipeline.derive.planning_data import AUTHORITATIVE, Read, Record
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.CONSERVATION_COVER
SOURCE = "mhclg-planning-data-conservation-areas"
# The publisher's name for its file, and the name the file gives its dataset.
FILE, DATASET = "conservation-area.geojson", "conservation-area"
# Records are looked for this far beyond the box round London, in metres.
MARGIN = 1_000
# Two records are one area where they share this much of the land the two cover together.
SAME_IN_100 = 50
# An area stands for an authority where the authority holds this much of all it encloses.
HELD_IN_100 = 50
# A share is shown as a percentage.
TIMES = 100
# Conservation land is kept to this many decimal places of a hectare, as the land is.
HECTARE_DECIMALS = land.DECIMALS
# A figure is given to this many decimal places.
DECIMALS = 1
# What the records are keyed by, as the parser finds them.
KEYED_BY = Geography.POLYGON
PUBLISHER = "Ministry of Housing, Communities and Local Government"
PLATFORM = "planning data platform"
OF_THE_LAND = "Office for National Statistics"
CODE = "burro_pipeline.derive.conservation_cover"

ONE_OF_EACH = Method(
    derivation_id="conservation_area_once@1",
    sentence="Two records of conservation areas are taken to be one area recorded twice where "
    "the land they share is 50 in 100 or more of the land the two cover together, and one is "
    "kept: the one its provider gives as authoritative, then the one entered last.",
    kind=Kind.MEASURED,
    parameters={"same_in_100": SAME_IN_100},
    code=CODE,
)
COVERED = Method(
    derivation_id="authority_with_a_record@1",
    sentence="An authority is taken to be covered where the file holds 1 conservation area or "
    "more of which it holds 50 in 100 or more, and an area in an authority that is not covered "
    "has no figure.",
    kind=Kind.MEASURED,
    parameters={"at_least": 1, "held_in_100": HELD_IN_100},
    code=CODE,
)
INSIDE_AREAS = Method(
    derivation_id="land_inside_conservation_areas@1",
    sentence="The land of each small census area that lies inside a conservation area, measured "
    "where the outline of the census area lies over the outlines of the conservation areas, with "
    "land inside two counted once, in hectares to 4 decimal places.",
    kind=Kind.MEASURED,
    parameters={"decimal_places": HECTARE_DECIMALS},
    code=CODE,
)
# The arithmetic, how the land was measured, and how the conservation land was: what a
# methods page prints beside the measure. The first is the one a row names.
METHOD = LSOA_RATIO_BY_HOMES
METHODS: tuple[Method, ...] = (METHOD, land.MEASURED, INSIDE_AREAS, ONE_OF_EACH, COVERED)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The land inside the conservation areas that the {platform} of the {publisher} held as at "
    "{areas}, as a share of all the land inside the boundaries of the area's small census areas "
    "as at {land}, which the {of_the_land} generalised and cut at the mean high water mark: a "
    "conservation area recorded twice is counted once, land inside two is counted once, the "
    "figure is given to {places} decimal place with a half taken upward, and an area has no "
    "figure where its planning authority sent no conservation area."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts the land inside a line a planning authority drew, so it cannot see what the "
    "buildings inside the line are like, how old they are or what state they are in, and a "
    "street of old houses outside any line counts for nothing.",
    "The publisher says the data may be incomplete, so where an authority sent only some of its "
    "conservation areas the figure is too low, and where it sent none there is no figure.",
)


@dataclass(frozen=True)
class Outlined:
    """One conservation area as a record gives it: its outline, and who provided it."""

    entity: str
    provider: str
    quality: str
    entered: str
    # On the National Grid.
    shape: Shape


@dataclass(frozen=True)
class Counted:
    """What became of the records of the file, counted. Each record is counted once."""

    # Every record of the file, and those of them in the box round London.
    in_the_file: int
    in_the_box: int
    # Records that say nothing of where they are, anywhere in the file.
    nowhere: int
    # Of those in the box: ended by the day of the file, a point and no outline, and an
    # outline that encloses no land.
    ended: int
    points: int
    no_land: int
    # Outlines that were mended, of those that enclose land.
    mended: int
    # Outlines that share no land with London.
    outside: int
    # Outlines left out as the second record of an area.
    twice: int
    # The conservation areas that are left: each once, each with land in London.
    kept: int


@dataclass(frozen=True)
class Authority:
    """What the file holds for one planning authority."""

    code: str
    # The conservation areas given to it, each once, by provider and quality: those of which
    # it holds more of the land in London than any other authority does.
    areas: Mapping[tuple[str, str], int]
    # The records left out as the second record of one of its areas.
    twice: int
    # Of its areas, those of which it holds half or more of all the outline encloses. An area
    # that lies mostly over London's edge, or mostly over water, is not among them.
    mostly: Mapping[tuple[str, str], int]

    @property
    def covered(self) -> bool:
        return sum(self.mostly.values()) >= int(COVERED.parameters["at_least"])


@dataclass(frozen=True)
class Cover:
    """Conservation cover for every area, in percent, with what stands behind each figure."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # The conservation land of each LSOA of a covered authority, in hectares.
    inside: Mapping[str, float]
    # What the file holds for each authority, by the code of the authority.
    authorities: Mapping[str, Authority]
    counted: Counted


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return name == FILE


def _outlines(records: Sequence[Record], day: str) -> tuple[list[Outlined], dict[str, int]]:
    """The outline of every record that is live and encloses land, and what was left out."""
    found: list[Outlined] = []
    left = {"ended": 0, "points": 0, "no_land": 0, "mended": 0}
    for record in records:
        if not record.live_on(day):
            left["ended"] += 1
            continue
        if record.kind == POINT:
            left["points"] += 1
            continue
        if record.kind not in (POLYGON, MULTIPOLYGON):
            raise ValueError("a conservation area is an outline or a point")
        drawn = outline_from(record.kind, record.coordinates)
        if drawn is None:
            left["no_land"] += 1
            continue
        left["mended"] += int(drawn[1])
        found.append(
            Outlined(record.entity, record.provider, record.quality, record.entered, drawn[0])
        )
    return found, left


def _preferred(outlined: Outlined) -> tuple[int, int, int]:
    """The order in which records are kept: authoritative, then entered last, then by number."""
    entered = date.fromisoformat(outlined.entered).toordinal()
    return (int(outlined.quality != AUTHORITATIVE), -entered, int(outlined.entity))


def one_of_each(found: Sequence[Outlined]) -> tuple[list[Outlined], dict[str, str]]:
    """The conservation areas, each once, and for each record left out the one kept for it.

    The records are taken in the order they are preferred. One is left out
    where it shares enough land with a record that is already kept. So what is
    kept does not turn on the order of the file.
    """
    order = sorted(found, key=_preferred)
    earlier: dict[int, list[int]] = {}
    for first, second in sharing_land([outlined.shape for outlined in order]):
        earlier.setdefault(second, []).append(first)
    kept: dict[int, Outlined] = {}
    left_out: dict[str, str] = {}
    for at, outlined in enumerate(order):
        same = [
            first
            for first in earlier.get(at, ())
            if first in kept
            and TIMES * share_of_both(order[first].shape, outlined.shape) >= SAME_IN_100
        ]
        if same:
            left_out[outlined.entity] = order[same[0]].entity
        else:
            kept[at] = outlined
    return sorted(kept.values(), key=lambda outlined: int(outlined.entity)), left_out


def held_most(shape: Shape, authorities: Mapping[str, Shape]) -> tuple[str, float] | None:
    """The authority that holds most of the land of an outline, and how much of it, in 100.

    It is none where no authority holds any. Where two hold the same, it is
    the one whose code sorts first. The share is of all the outline encloses,
    so it is small where the outline lies mostly outside every authority.
    """
    held = hectares_in_each(shape, authorities)
    if not held:
        return None
    code = min(held, key=lambda code: (-held[code], code))
    return code, TIMES * held[code] / hectares(shape)


def outlines_of_authorities(outlines: Mapping[str, Shape], found: Spine) -> dict[str, Shape]:
    """The land of each authority: the outlines of its LSOAs, joined."""
    of_lsoa = {cell.lsoa: cell.borough for cell in found.cells}
    parts: dict[str, list[Shape]] = {}
    for lsoa in sorted(outlines):
        parts.setdefault(of_lsoa[lsoa], []).append(outlines[lsoa])
    return {code: joined(shapes) for code, shapes in sorted(parts.items())}


@dataclass(frozen=True)
class Held:
    """The conservation areas of London, each once, and what the file holds for each authority."""

    kept: tuple[Outlined, ...]
    authorities: Mapping[str, Authority]
    counted: Counted


def held_for_london(read: Read, day: str, authorities: Mapping[str, Shape]) -> Held:
    """The conservation areas of London from the records of the file.

    `authorities` is the land of each authority, by its code. `day` is the day
    the file is of.
    """
    drawn, left = _outlines(read.records, day)
    placed = {outlined.entity: held_most(outlined.shape, authorities) for outlined in drawn}
    in_london = [outlined for outlined in drawn if placed[outlined.entity] is not None]
    given = {outlined.entity: held for outlined in in_london if (held := placed[outlined.entity])}
    kept, left_out = one_of_each(in_london)
    areas: dict[str, dict[tuple[str, str], int]] = {code: {} for code in authorities}
    mostly: dict[str, dict[tuple[str, str], int]] = {code: {} for code in authorities}
    twice = dict.fromkeys(authorities, 0)
    for outlined in kept:
        key = (outlined.provider, outlined.quality)
        code, in_100 = given[outlined.entity]
        areas[code][key] = areas[code].get(key, 0) + 1
        if in_100 >= HELD_IN_100:
            mostly[code][key] = mostly[code].get(key, 0) + 1
    for entity in left_out:
        twice[given[entity][0]] += 1
    counted = Counted(
        in_the_file=read.in_the_file,
        in_the_box=len(read.records),
        nowhere=read.nowhere,
        ended=left["ended"],
        points=left["points"],
        no_land=left["no_land"],
        mended=left["mended"],
        outside=len(drawn) - len(in_london),
        twice=len(left_out),
        kept=len(kept),
    )
    return Held(
        kept=tuple(kept),
        authorities={
            code: Authority(
                code,
                dict(sorted(areas[code].items())),
                twice[code],
                dict(sorted(mostly[code].items())),
            )
            for code in sorted(authorities)
        },
        counted=counted,
    )


def conservation_land(found: Held, outlines: Mapping[str, Shape], spine: Spine) -> dict[str, float]:
    """The conservation land of each LSOA of a covered authority, in hectares.

    An LSOA of an authority that sent nothing is left out: what it holds is
    not known. One of a covered authority that no conservation area touches
    holds nought.
    """
    of_lsoa = {cell.lsoa: cell.borough for cell in spine.cells}
    covered = {
        lsoa: outline
        for lsoa, outline in outlines.items()
        if found.authorities[of_lsoa[lsoa]].covered
    }
    inside = hectares_inside(covered, [outlined.shape for outlined in found.kept])
    return {lsoa: land.kept(held) for lsoa, held in inside.items()}


def figures(inside: Mapping[str, float], measured: Land, found: Spine) -> dict[str, Worked]:
    """Conservation cover for every area of the spine, in percent, or why an area has none.

    An LSOA that lies wholly inside a conservation area is measured twice, as
    its own outline and as the land the two share, and the two may differ in
    the last place that is kept. So conservation land that is over the land of
    its LSOA by no more than that is taken to be all of it. More than that is
    a fault, and stops the step.
    """
    last_place = 10.0**-HECTARE_DECIMALS
    if any(inside[lsoa] > land.kept(measured.of_lsoa[lsoa] + last_place) for lsoa in inside):
        raise ValueError("the conservation land of an LSOA is no more than its land")
    within = {lsoa: min(held, measured.of_lsoa[lsoa]) for lsoa, held in inside.items()}
    worked = lsoa_ratio_by_homes(
        within, measured.of_lsoa, found.lsoa_of, found.weights, times=float(TIMES)
    )
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def _when(period: Period) -> str:
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the name, the unit and which way is more, and the figure is
    what core's name says: a share of the area's land. The period is the day
    the receipt of the file gives.
    """
    period = {receipt.source_id: _when(receipt.data_period) for receipt in files}
    return catalogue_row(
        FEATURE,
        method=METHOD,
        source_ids=period,
        vintage=as_at,
        definition=DEFINITION.format(
            platform=PLATFORM,
            publisher=PUBLISHER,
            areas=as_at,
            land=period[land.BOUNDARIES],
            of_the_land=OF_THE_LAND,
            places=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine, measured: Land, *, edition: str | None = None) -> Cover:
    """Conservation cover for every area and its evidence, from the files of the build.

    The gate is asked about the conservation areas and about the boundaries
    before either is read. `found` and `measured` are the spine and the land
    of the same build. `edition` says which file is meant where the folder of
    receipts holds more than one. A row of evidence names the file of
    conservation areas, the boundaries, the lookup, and the table of homes
    that coverage is counted by.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_file)
    boundaries = inputs.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if boundaries.file_id != measured.file_id or not set(found.inputs) <= set(handed):
        raise ValueError("the spine and the land are made from files of this build")
    outlines = land.read(boundaries, found)
    if any(lsoa not in outlines for lsoa in found.lsoas):
        raise LockError("input_is_as_described", boundaries.file_id, "an LSOA has no outline")
    day = opened.receipt.data_period.days()[1]
    read = planning_data.read(opened, DATASET, in_degrees(box_round(outlines), MARGIN))
    try:
        held = held_for_london(read, day, outlines_of_authorities(outlines, found))
    except ValueError:
        raise LockError(
            "input_is_as_described", opened.file_id, "an outline could not be read"
        ) from None
    inside = conservation_land(held, outlines, found)
    worked = figures(inside, measured, found)
    behind = sorted({opened.file_id, boundaries.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Cover(
        worked=worked,
        rows=rows,
        metric=metric_of(files, _when(opened.receipt.data_period)),
        files=files,
        geography=KEYED_BY,
        inside=inside,
        authorities=held.authorities,
        counted=held.counted,
    )


def hectares_in(inside: Mapping[str, float]) -> float:
    """The conservation land of every LSOA that has any, added up, in hectares."""
    return land.kept(math.fsum(inside.values()))
