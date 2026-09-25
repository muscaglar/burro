"""Traffic near where homes stand: the motor vehicles that pass the busiest count point nearby.

The Department for Transport publishes its street-level road traffic estimates
once a year, as one table for Great Britain inside a zip. The table holds a
row for each count point and year: where the count point stands, the class of
its road, how the figure was made, and the annual average daily flow, which is
the vehicles that pass on an average day of that year. It is a figure about a
road. It says nothing of who lives anywhere.

**It is core's measure of traffic**, `road_traffic_nearby`, and a build
carries it. Core names it "Traffic past the busiest count point within 500 m of
home, in a straight line", and the row of the catalogue that is made here is
core's. A person may rank on it, and Quiet streets holds it.

What is read of a row, and what is not:

| Column | Read | Why |
|---|---|---|
| `count_point_id` | Yes | The rows of one id are the years of one count point |
| `year` | Yes | A count point is read at the latest year it has |
| `easting`, `northing` | Yes | Where the count point stands, on the National Grid |
| `road_category` | Yes | The class of the road the figure is of |
| `estimation_method` | Yes | Whether the figure was counted or estimated |
| `all_motor_vehicles` | Yes | The flow: every vehicle but a pedal cycle |
| `road_name`, the junctions | No | A figure needs no name of a road |
| The region and the authority | No | A count point counts by where it stands |
| Every other column | No | |

The licence registry puts conditions on the file, and each is a rule here:

- **It is read as exposure to busy roads, and never as a model of traffic.**
  A figure is the flow at one count point that stands near a home. Nothing is
  worked out for a road between two count points.
- **Minor roads are sampled, and nothing is filled in.** Every link of a major
  road has a count point, and a minor road has one only where it is in the
  publisher's sample. A home with no count point within reach has no figure.
  It is never given the flow of a road further off or of a class of road, and
  never nought.
- **A figure is given with the year it is of.** A count point is read at the
  latest year it has, which for a minor road that has left the sample may be
  years ago. The row of the catalogue states the years of the figures that
  were read, and not the span of the file.
- **A figure says whether it was counted or estimated.** The sentence of the
  measure says how many of the figures behind a release were each.
- **The flows of two count points are never added together.** A home with
  several within reach is given the highest of them.

How a figure is made:

1. **The latest figure of each count point.** The row of the latest year the
   file holds for it: its flow of all motor vehicles on an average day, and
   where it stood.
2. **The count points near a home.** A home is placed at the point the
   statistics office gives as the centre of population of its output area. A
   count point is near where it stands within 500 metres of that point, in a
   straight line on the National Grid.
3. **The traffic near a home.** The highest flow among those count points, and
   of two as high the count point whose id sorts first.
4. **The figure.** The mean of those flows over the area's homes, to the whole
   vehicle. Below half the area's homes with a figure, none is given.

A flow of nought is a figure: the publisher gives it for a link that no motor
vehicle passed, as a bridge that is closed to them.

**Why 500 metres, and what it costs.** A count point stands at one place on a
link of road, and a link runs from one junction to the next, so the count
point of the road a home stands beside may be some way along it. On the files
of the first build the middle link of a major road is 800 metres long. Within
500 metres, five in six of the homes that stand within 100 metres of a main
road have a count point of a major road, seven in eight of all the homes have
a count point of any road, and 943 of the 1,002 areas have a figure. At 300
metres 578 areas have one. At 800 metres nearly every home has a main road
within reach, so the figure says less of the streets a home stands in. The
distance is a choice and not a finding. It is one line of core's catalogue,
and it stands in the name of the measure.

**Nothing here is of one city.** The file is of Great Britain. A count point
counts where it stands near a home of the build, on whichever side of the
build's edge, and no column that names a region or an authority is read.

What the file is held to, because a figure rests on it:

- It is a zip that holds the one table, with every column that is read.
- Every year is a year of the period its receipt states, and a row is of the
  last year of that period. The file holds no day of its own, so this is what
  ties it to its receipt: a file of another year is another file.
- A count point has one row for a year.
- Every place is a place, every flow a whole number that is not below nought,
  and every figure is marked `Counted` or `Estimated`, on a road of a category
  the publisher's metadata document names.
"""

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.catalogue import TRAFFIC_WITHIN_M
from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import one_indicator
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, lsoa_value_by_homes, row_of, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.ROAD_TRAFFIC_NEARBY
# The id the rows are written under.
KEY = FEATURE.value
# A person may rank an area on the figure by itself: it was asked for so.
RANKABLE = True
SOURCE = "dft-road-traffic-counts"
PUBLISHER = "the Department for Transport"
PRODUCT = "street-level road traffic estimates"
# The publisher's name for the one file, and for the one table inside it.
FILE = "dft_traffic_counts_aadf.zip"
TABLE = "dft_traffic_counts_aadf.csv"
# The columns that are read, as the file names them.
POINT, YEAR, CATEGORY = "count_point_id", "year", "road_category"
EASTING, NORTHING = "easting", "northing"
HOW, FLOW = "estimation_method", "all_motor_vehicles"
READ = (POINT, YEAR, CATEGORY, EASTING, NORTHING, HOW, FLOW)
# How a figure was made, as the file marks it.
COUNTED, ESTIMATED = "Counted", "Estimated"
# The categories of road the publisher's metadata document names: motorways and class A
# roads, trunk or principal, and the minor roads, class B or class C and unclassified.
CATEGORIES = frozenset({"PM", "TM", "PA", "TA", "MB", "MCU"})
# A count point is near a home where it stands no further than this from the centre of the
# home's output area, in metres and in a straight line. Core's name of the measure says it.
METRES = TRAFFIC_WITHIN_M
CENSUS = 2021
# A figure is given to the whole vehicle.
DECIMALS = 0
# What the rows of the file are keyed by, as the parser finds them.
KEYED_BY = Geography.POINT
CODE = "burro_pipeline.derive.road_traffic_nearby"
_WHOLE = re.compile(r"\d{1,9}")
_YEAR = re.compile(r"\d{4}")

METHOD = Method(
    derivation_id=f"busiest_count_point_within_{METRES}m_at_homes@1",
    sentence="The highest of the publisher's estimates of the motor vehicles that pass a count "
    "point on an average day, each count point read at the latest year it has a figure for, among "
    f"the count points that stand within {METRES} metres, in a straight line, of the point where "
    "the homes of each census output area are taken to stand, as the mean over the area's homes "
    "at the census, and not given where under 50 in 100 of the area's homes are in an output "
    "area with such a count point.",
    kind=Kind.MODELLED,
    parameters={"metres": METRES, "enough_in_100": 50},
    code=CODE,
)
METHODS: tuple[Method, ...] = (METHOD,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The motor vehicles that pass, on an average day of a year, the busiest count point within "
    "{metres} metres, in a straight line, of the point the statistics office gives as the centre "
    "of each census output area, as {publisher} estimates them in its {product}, each count "
    "point read at the latest year it has a figure for, which is of {years}, as the mean over the "
    "area's homes at the census of {census}, given to the whole vehicle with a half taken upward: "
    "a motor vehicle is every vehicle but a pedal cycle, the flows of two count points are never "
    "added together, a home with no count point within {metres} metres has no figure and is "
    "given none, which is not a figure of nought, an area where under half of the homes have a "
    "figure has none, and of the {points} count points behind the figures of this release "
    "{counted} were counted in the year they are of and {estimated} were estimated by the "
    "publisher, which says that its estimates for a road link are less robust than its figures "
    "for a region, because they are not always based on up-to-date counts made at the place."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "The publisher counts every link of a main road and only a sample of minor roads, so a "
    "quiet street with no count point near it has no figure, which is not the same as a figure "
    "of nought, and a quiet street is less likely to have a figure than a busy one.",
    "A count point stands at one place on a link of road, which runs from one junction to the "
    "next, so a home beside a main road has no figure of that road where its count point stands "
    "further along it than 500 metres.",
    "It takes the busiest count point within 500 metres of the centre of a small census area, "
    "so a main road a few streets away reads as the traffic of a home that stands on a quiet "
    "street, and so does a road that passes over it or under it.",
    "A figure is the publisher's estimate for the latest year the count point has one for, "
    "which may be years ago, and many figures are estimated from an earlier count: the "
    "publisher says its estimates for a road link are less robust than its figures for a "
    "region, because they are not always based on up-to-date counts made at the place.",
    "It counts motor vehicles on an average day, so it cannot see how fast they go, how heavy "
    "they are, how wide the road is, or how a weekday differs from a weekend or a day from a "
    "night.",
)


@dataclass(frozen=True)
class Count:
    """The latest figure of one count point."""

    point: str
    year: int
    # Where it stood in that year, on the National Grid.
    at: Point
    # The motor vehicles that passed it on an average day of that year.
    flow: int
    # Whether the figure was counted, and not estimated.
    counted: bool
    category: str


@dataclass(frozen=True)
class Near:
    """The traffic near the homes of one output area: the busiest count point within reach."""

    flow: int
    # The year the flow is of, and the count point it is the flow of.
    year: int
    point: str
    counted: bool
    category: str
    # How many count points stand within reach.
    points: int


@dataclass(frozen=True)
class Traffic:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    # The busiest count point near the homes of each output area that has one within reach.
    near: Mapping[str, Near]
    # How many count points the file holds, in all of Great Britain.
    count_points: int
    # The count points that are the busiest near some home of the build, by their id.
    behind: Mapping[str, Count]
    # The years of the figures behind the build: from the earliest to the latest. Nothing
    # where no home has a figure.
    read_of: Period | None

    @property
    def counted(self) -> int:
        """How many of the count points behind the figures were counted."""
        return sum(one.counted for one in self.behind.values())

    @property
    def estimated(self) -> int:
        """How many of the count points behind the figures were estimated."""
        return sum(not one.counted for one in self.behind.values())


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file that is read."""
    return name == FILE


def _stopped(opened: Opened, why: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, why)


def _years_of(opened: Opened) -> tuple[int, int]:
    """The first and the last year of the period the receipt of the file states."""
    first, last = opened.receipt.data_period.days()
    return int(first[:4]), int(last[:4])


def _one(opened: Opened, row: Mapping[str, str], years: tuple[int, int]) -> Count:
    """One row of the table, held to what the publisher says a row is."""
    if not _YEAR.fullmatch(row[YEAR]) or not years[0] <= int(row[YEAR]) <= years[1]:
        raise _stopped(opened, "a year is no year of the period of the file")
    if not row[POINT].strip() or row[POINT] != row[POINT].strip():
        raise _stopped(opened, "a count point has no id")
    try:
        at = float(row[EASTING]), float(row[NORTHING])
    except ValueError:
        at = math.nan, math.nan
    if not all(math.isfinite(part) for part in at):
        raise _stopped(opened, "a place is no place")
    if not _WHOLE.fullmatch(row[FLOW]):
        raise _stopped(opened, "a flow is no whole number")
    if row[HOW] not in (COUNTED, ESTIMATED):
        raise _stopped(opened, "a figure is made in a way that is not known")
    if row[CATEGORY] not in CATEGORIES:
        raise _stopped(opened, "a category of road is not known")
    return Count(row[POINT], int(row[YEAR]), at, int(row[FLOW]), row[HOW] == COUNTED, row[CATEGORY])


def read(opened: Opened) -> dict[str, Count]:
    """The latest figure of every count point, by its id. It stops where the file is not as
    described above."""
    years = _years_of(opened)
    latest: dict[str, Count] = {}
    seen: set[tuple[str, int]] = set()
    newest = 0
    with opened.text(TABLE) as text:
        for row in opened.rows(text, READ):
            one = _one(opened, row, years)
            if (one.point, one.year) in seen:
                raise _stopped(opened, "a count point has two figures of one year")
            seen.add((one.point, one.year))
            newest = max(newest, one.year)
            held = latest.get(one.point)
            if held is None or one.year > held.year:
                latest[one.point] = one
    if not latest:
        raise _stopped(opened, "it holds no count point")
    if newest != years[1]:
        raise _stopped(opened, "it holds no figure of the last year of its period")
    return {point: latest[point] for point in sorted(latest)}


def near(
    points: Mapping[str, Point], counts: Mapping[str, Count], metres: int = METRES
) -> dict[str, Near]:
    """The busiest count point within so many metres of each point that has one within reach.

    A point with none is not here. A count point at the distance exactly is
    within it. Only sums and products are taken, so that the same places give
    the same answer on every machine, in whatever order they are handed over.
    """
    held: dict[tuple[int, int], list[Count]] = {}
    for point in sorted(counts):
        one = counts[point]
        on = math.floor(one.at[0] / metres), math.floor(one.at[1] / metres)
        held.setdefault(on, []).append(one)
    square = float(metres) * float(metres)
    found: dict[str, Near] = {}
    for name in sorted(points):
        east, north = points[name]
        column, row = math.floor(east / metres), math.floor(north / metres)
        within = [
            one
            for across in (column - 1, column, column + 1)
            for up in (row - 1, row, row + 1)
            for one in held.get((across, up), ())
            if (one.at[0] - east) ** 2 + (one.at[1] - north) ** 2 <= square
        ]
        if not within:
            continue
        most = min(within, key=lambda one: (-one.flow, one.point))
        found[name] = Near(
            most.flow, most.year, most.point, most.counted, most.category, len(within)
        )
    return found


def figures(of_oa: Mapping[str, float], spine: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, to the whole vehicle, or why it has none.

    It is the mean over the area's homes, which `lsoa_value_by_homes` works
    out with each output area as a unit of its own.
    """
    worked = lsoa_value_by_homes(of_oa, {oa: oa for oa in spine.area_of}, spine.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def years_of(behind: Mapping[str, Count]) -> Period | None:
    """The years of the figures behind a build, from the earliest to the latest."""
    if not behind:
        return None
    first = min(one.year for one in behind.values())
    last = max(one.year for one in behind.values())
    return Period(as_at=str(first)) if first == last else Period(start=str(first), end=str(last))


def _in_words(period: Period | None) -> str:
    if period is None:
        return "no year"
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(files: Sequence[Receipt], behind: Mapping[str, Count]) -> Metric:
    """The row of the catalogue: the name, the unit, the years and every source.

    Core decides the name, the unit and which way is better. The period is
    the years of the figures that were read, and not the span of the file.
    """
    years = _in_words(years_of(behind))
    counted = sum(one.counted for one in behind.values())
    return catalogue_row(
        FEATURE,
        method=METHOD,
        source_ids={receipt.source_id for receipt in files},
        vintage=years,
        rankable=RANKABLE,
        definition=DEFINITION.format(
            metres=METRES,
            publisher=PUBLISHER,
            product=PRODUCT,
            years=years,
            census=CENSUS,
            points=f"{len(behind):,}",
            counted=f"{counted:,}",
            estimated=f"{len(behind) - counted:,}",
        ),
    )


def build(inputs: Inputs, spine: Spine) -> Traffic:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about the count points and about the centres before
    either is read. `spine` is the spine of the same build: a row of evidence
    names its files beside the count points and the centres, so they must be
    files this build opened. A row states the years of the figures that were
    read.
    """
    opened = inputs.open(SOURCE, Use.SCORING, named=is_the_file)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    points = centres.centres_of(placed, spine)
    if not points:
        raise LockError("input_is_as_described", placed.file_id, "it holds no centre of the build")
    counts = read(opened)
    found = near(points, counts)
    behind = {one.point: counts[one.point] for one in found.values()}
    behind = {point: behind[point] for point in sorted(behind)}
    worked = figures({oa: float(one.flow) for oa, one in found.items()}, spine)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    named = sorted({opened.file_id, placed.file_id, *spine.inputs})
    if not all(file_id in handed for file_id in named):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in named)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, KEY), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    read_of = years_of(behind)
    if read_of is not None:
        if not one_indicator.takes_in(opened.receipt.data_period, read_of):
            raise _stopped(opened, "a year is no year of the period of the file")
        rows = one_indicator.cited(rows, opened.receipt, files, read_of)
    return Traffic(
        worked=worked,
        rows=rows,
        metric=metric_of(files, behind),
        files=files,
        geography=KEYED_BY,
        near=found,
        count_points=len(counts),
        behind=behind,
        read_of=read_of,
    )
