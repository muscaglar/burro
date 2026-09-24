"""Listed buildings: the entries of the national list in an area, for each square kilometre.

The entries come from the National Heritage List for England, as the planning
data platform holds it, which `planning_data.py` reads. The land comes from
the boundaries of LSOAs, which `cells/land.py` measures. It is a figure about
buildings. It says nothing of who lives anywhere.

The licence registry asks for aggregates only. So nothing here keeps a record:
what leaves this module is a count for an LSOA, a count for an authority, and
a figure for an area. The name of an entry is never read. It is often an
address, and may be the name of a business.

What an entry is. The list protects a building or a structure, and an entry
is one decision to protect. It may be a palace, a terrace of thirty houses
under one entry, a bollard, a milestone, a tomb or a telephone box. Each is
one entry, and each counts as one. So the figure is how thickly the list is
marked on the map, and not how many buildings are old.

How a figure is made:

1. **Which entries.** An entry that had ended by the day of the file is left
   out. In the file fetched on 2026-09-24 every live entry is a point and has
   a grade, and every ended one is an outline. A live entry that is not a
   point would be counted here as not placed, and never guessed a place.
2. **Where.** Each point is put on the National Grid and given to the LSOA
   whose outline it stands in. The outlines are cut at the mean high water
   mark, so an entry that the list maps over the tidal river, as a bridge or
   a pier may be, stands in none and is counted in no area.
3. **Which authorities.** The publisher says the data may be incomplete. An
   authority in which the file holds no entry at all has no figure, and never
   nought: nothing shows that the list was read there.
4. **The figure.** The entries of an area's LSOAs over the land of its LSOAs
   in square kilometres. That is `lsoa_ratio_by_homes`: one sum over another.
   It is given to one decimal place.

An area of a covered authority that holds no entry holds nought, and nought
is what the figure says.

**Grade.** The file gives the grade of every live entry: I, II* or II. Core's
measure is of listed buildings, and says nothing of grade, so every entry
counts the same. The counts by grade are kept, so that a person can see what
weighing them would change. Nine entries in ten are of grade II.

**For each 1,000 homes.** The design of the data once read the measure as
entries for each 1,000 homes. Core names it for each square kilometre, and
that is what a build carries. `for_each_thousand_homes` works the other out,
for a person to compare. It joins no release.

A point is placed to within 2 metres: `heritage_shapes.py` says why. So an
entry that stands within 2 metres of a line between two areas may be counted
on the wrong side of it.
"""

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import land
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.shapes import Shape
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import planning_data
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.heritage_shapes import (
    POINT,
    Ground,
    box_round,
    in_degrees,
    point_from,
)
from burro_pipeline.derive.methods import (
    LSOA_RATIO_BY_HOMES,
    Worked,
    lsoa_ratio_by_homes,
    row_of,
    to_places,
)
from burro_pipeline.derive.planning_data import Read
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.LISTED_BUILDINGS
SOURCE = "historic-england-listed-buildings"
# The publisher's name for its file, and the name the file gives its dataset.
FILE, DATASET = "listed-building.geojson", "listed-building"
# The property that holds the grade, and the grades the list gives.
GRADE = "listed-building-grade"
GRADES = ("I", "II*", "II")
# Entries are looked for this far beyond the box round London, in metres.
MARGIN = 1_000
HECTARES_IN_A_SQUARE_KILOMETRE = 100
# The land of an LSOA is kept to this many decimal places of a square kilometre: a square metre.
KILOMETRE_DECIMALS = 6
# A figure is given to this many decimal places.
DECIMALS = 1
# What the records are keyed by, as the parser finds them.
KEYED_BY = Geography.POINT
PUBLISHER = "Historic England"
PLATFORM = "planning data platform"
OF_THE_LAND = "Office for National Statistics"
CODE = "burro_pipeline.derive.listed_buildings"

PLACED = Method(
    derivation_id="entries_in_outline@1",
    sentence="The entries of the list whose point stands inside the outline of each small "
    "census area, each entry counted as 1 whatever its grade and whatever it protects, and "
    "an entry that stands in no outline counted in none.",
    kind=Kind.MEASURED,
    parameters={"each_counts": 1},
    code=CODE,
)
COVERED = Method(
    derivation_id="authority_with_an_entry@1",
    sentence="An authority is taken to be covered where the file holds 1 entry or more that "
    "stands in it, and an area in an authority that is not covered has no figure.",
    kind=Kind.MEASURED,
    parameters={"at_least": 1},
    code=CODE,
)
# The arithmetic, how the land was measured, and how the entries were placed: what a methods
# page prints beside the measure. The first is the one a row names.
METHOD = LSOA_RATIO_BY_HOMES
METHODS: tuple[Method, ...] = (METHOD, land.MEASURED, PLACED, COVERED)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The entries of the National Heritage List for England that {publisher} listed as "
    "buildings and the {platform} held as at {entries}, counted where the point of each stands "
    "inside the boundaries of the area's small census areas as at {land}, which the "
    "{of_the_land} generalised and cut at the mean high water mark, over the land inside those "
    "boundaries in square kilometres: every entry counts as one whatever its grade, an entry "
    "may be one building, a whole terrace or a structure such as a milestone, the figure is "
    "given to {places} decimal place with a half taken upward, and an area has no figure where "
    "the file holds no entry in its planning authority."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts entries on the national list, and an entry may be one house, a whole terrace, "
    "a church, a bollard or a milestone, so it cannot see how many buildings are protected or "
    "how much of a street they make up.",
    "Every entry counts the same whatever its grade, so it cannot see how much a building "
    "matters, and it cannot see a building that is old and not listed, or the state a building "
    "is in.",
)


@dataclass(frozen=True)
class Counted:
    """What became of the entries of the file, counted. Each entry is counted once."""

    # Every record of the file, and those of them in the box round London.
    in_the_file: int
    in_the_box: int
    # Records that say nothing of where they are, anywhere in the file.
    nowhere: int
    # Of those in the box: ended by the day of the file, live and not a point, and live
    # points that stand in no LSOA of London.
    ended: int
    not_points: int
    in_no_area: int
    # The entries that are counted: live, a point, and in an LSOA of London.
    placed: int
    # The entries that are counted, by grade. An entry with no grade is under "".
    by_grade: Mapping[str, int]


@dataclass(frozen=True)
class Listed:
    """Listed buildings for every area, for each square kilometre, and what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # The entries of each LSOA of a covered authority. Nought is a count.
    entries: Mapping[str, int]
    # The entries of each authority, by its code. An authority with none is not covered.
    of_authority: Mapping[str, int]
    counted: Counted


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return name == FILE


@dataclass(frozen=True)
class Placed:
    """The entries of London: how many stand in each LSOA, and what was counted on the way."""

    in_lsoa: Mapping[str, int]
    counted: Counted


def place(read: Read, day: str, outlines: Mapping[str, Shape]) -> Placed:
    """The live entries of the file, each given to the LSOA its point stands in.

    `day` is the day the file is of. It raises `ValueError` where a point is
    not a longitude and a latitude, or a grade is not one the list gives.
    """
    live = [record for record in read.records if record.live_on(day)]
    points = [record for record in live if record.kind == POINT]
    if any(record.asked.get(GRADE, "") not in ("", *GRADES) for record in points):
        raise ValueError("a grade is one the list gives")
    stands_in = Ground(outlines).holding([point_from(record.coordinates) for record in points])
    in_lsoa: Counter[str] = Counter()
    by_grade: Counter[str] = Counter()
    for record, lsoa in zip(points, stands_in, strict=True):
        if lsoa is not None:
            in_lsoa[lsoa] += 1
            by_grade[record.asked.get(GRADE, "")] += 1
    counted = Counted(
        in_the_file=read.in_the_file,
        in_the_box=len(read.records),
        nowhere=read.nowhere,
        ended=len(read.records) - len(live),
        not_points=len(live) - len(points),
        in_no_area=len(points) - sum(in_lsoa.values()),
        placed=sum(in_lsoa.values()),
        by_grade=dict(sorted(by_grade.items())),
    )
    return Placed(in_lsoa=dict(sorted(in_lsoa.items())), counted=counted)


def of_authorities(in_lsoa: Mapping[str, int], found: Spine) -> dict[str, int]:
    """The entries of each authority of the spine, by its code. One with none holds nought."""
    of_lsoa = {cell.lsoa: cell.borough for cell in found.cells}
    counts = dict.fromkeys(sorted(set(of_lsoa.values())), 0)
    for lsoa, count in in_lsoa.items():
        counts[of_lsoa[lsoa]] += count
    return counts


def covered_entries(in_lsoa: Mapping[str, int], found: Spine) -> dict[str, int]:
    """The entries of each LSOA of a covered authority. An LSOA with none holds nought.

    An LSOA of an authority in which the file holds no entry is left out: what
    it holds is not known.
    """
    at_least = int(COVERED.parameters["at_least"])
    of_authority = of_authorities(in_lsoa, found)
    of_lsoa = {cell.lsoa: cell.borough for cell in found.cells}
    return {
        lsoa: in_lsoa.get(lsoa, 0)
        for lsoa in found.lsoas
        if of_authority[of_lsoa[lsoa]] >= at_least
    }


def square_kilometres(measured: Land) -> dict[str, float]:
    """The land of each LSOA in square kilometres, to a square metre."""
    return {
        lsoa: to_places(hectares / HECTARES_IN_A_SQUARE_KILOMETRE, KILOMETRE_DECIMALS)
        for lsoa, hectares in measured.of_lsoa.items()
    }


def figures(entries: Mapping[str, int], measured: Land, found: Spine) -> dict[str, Worked]:
    """Listed buildings for each square kilometre, for every area, or why an area has none."""
    counts = {lsoa: float(count) for lsoa, count in entries.items()}
    worked = lsoa_ratio_by_homes(counts, square_kilometres(measured), found.lsoa_of, found.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def for_each_thousand_homes(entries: Mapping[str, int], found: Spine) -> dict[str, Worked]:
    """Listed buildings for each 1,000 homes, for every area: the reading core does not take.

    A home is a household at the census of 2021, as the spine counts them. It
    is for a person to compare with the figure a build carries, and joins no
    release. An area with no homes has no figure.
    """
    homes: dict[str, float] = dict.fromkeys(found.lsoas, 0.0)
    for cell in found.cells:
        homes[cell.lsoa] += cell.homes
    counts = {lsoa: float(count) for lsoa, count in entries.items()}
    worked = lsoa_ratio_by_homes(counts, homes, found.lsoa_of, found.weights, times=1_000.0)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def _when(period: Period) -> str:
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the name, the unit and which way is more, and the figure is
    what core's name and unit say: listed buildings for each square
    kilometre. The period is the day the receipt of the file gives.
    """
    period = {receipt.source_id: _when(receipt.data_period) for receipt in files}
    return catalogue_row(
        FEATURE,
        method=METHOD,
        source_ids=period,
        vintage=as_at,
        definition=DEFINITION.format(
            publisher=PUBLISHER,
            platform=PLATFORM,
            entries=as_at,
            land=period[land.BOUNDARIES],
            of_the_land=OF_THE_LAND,
            places=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine, measured: Land, *, edition: str | None = None) -> Listed:
    """Listed buildings for every area and its evidence, from the files of the build.

    The gate is asked about the list and about the boundaries before either
    is read. `found` and `measured` are the spine and the land of the same
    build. `edition` says which file is meant where the folder of receipts
    holds more than one. A row of evidence names the file of listed buildings,
    the boundaries, the lookup, and the table of homes that coverage is
    counted by.
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
    within = in_degrees(box_round(outlines), MARGIN)
    read = planning_data.read(opened, DATASET, within, asked=(GRADE,))
    try:
        placed = place(read, day, outlines)
    except ValueError:
        raise LockError(
            "input_is_as_described", opened.file_id, "an entry could not be read"
        ) from None
    entries = covered_entries(placed.in_lsoa, found)
    worked = figures(entries, measured, found)
    behind = sorted({opened.file_id, boundaries.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Listed(
        worked=worked,
        rows=rows,
        metric=metric_of(files, _when(opened.receipt.data_period)),
        files=files,
        geography=KEYED_BY,
        entries=entries,
        of_authority=of_authorities(placed.in_lsoa, found),
        counted=placed.counted,
    )


def entries_in(entries: Mapping[str, int]) -> int:
    """The entries of every LSOA that has any, added up."""
    return int(math.fsum(entries.values()))
