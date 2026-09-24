"""Primary schools close by: how many stand within a straight line of where homes are.

The schools come from the register of the Department for Education, which
`schools_file.py` reads. Where homes are comes from the centres of output
areas, which `cells/centres.py` reads.

**It is a straight line, and not a walk.** No network of streets is built. So
a school counts where it stands within 800 metres of a home across whatever
lies between, and the row of the catalogue says so in its name, as core names
the measure. Do not name it a walk while it is a straight line.

**A school close by is not a place at it.** Nothing here says where a school
takes its pupils from, whether it has a place, or how good it is.

Which schools count. The register has no column that says who pays for a
school. It names the status, the type and the phase of each, and a school
counts where all three of these hold. The reading of the types rests on their
names alone: no page of the publisher was opened for it, because its policy
forbids reading its pages with a program.

| Column | Counts |
|---|---|
| `EstablishmentStatus (name)` | `Open`, and `Open, but proposed to close` |
| `TypeOfEstablishment (name)` | The seven types of `COUNTS` |
| `PhaseOfEducation (name)` | `Primary`, `Middle deemed primary`, `All-through` |

Every other value the file holds in one of the three does not count:
`STATUSES`, `KINDS` and `PHASES` name each.

The seven types are the schools an authority maintains, academies and free
schools. A special school, a unit for pupils who are out of school, a nursery
school and a school that charges fees are each a type of their own, and none
counts. An all-through school counts: it teaches the primary years. A value
that this module does not know stops the build, so that a school under a new
name is never counted as none.

What is never read. The register holds the names of head teachers, counts of
pupils and the religious character of a school. `schools_file.py` hands over
none of them, and this module asks for seven columns: the number of the
school, its status, its type, its phase, its region and the two parts of its
point. No name of a school is read, and no postcode.

How a figure is made:

1. A school is placed at the point the register gives it on the National
   Grid. A school with no point is not placed and is counted nowhere.
2. A home is placed at the point the statistics office gives as the centre of
   population of its output area.
3. For each output area, the schools that count within 800 metres of that
   point, in a straight line. The distance is the one core takes for a walk
   of ten minutes, and the one at which the nearest park is never a trade-off.
4. An area's figure is those counts added up over the area's homes and
   divided by the homes: the mean, over the homes of the area, of the schools
   within reach of each. It is `lsoa_ratio_by_homes`, with each output area
   as a unit of its own. It is given to one decimal place.
5. An output area with no centre adds nothing, and the coverage of its area
   falls by its homes. Below half the homes covered no figure is given.

Nought is a figure. The register is of England, so a home with no school
within reach has none, and is not a gap in the file. It is held to that: the
step stops where more than 1 in 100 centres have no school within 10,000
metres, and where more than 1 in 100 of the schools that count have no point.

**The edge of London.** The register is of England, so a school just past the
edge of London is in it, and counts for a home in London that it is near.

The distance to the nearest school is worked out beside the count, by the
arithmetic of the nearest park: `figures` in `park_proximity.py`. It is there
so that the two can be compared. Core holds no measure for it, so it has no
row of the catalogue and no row of evidence, and no release carries it.
"""

import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Homes, Spine
from burro_pipeline.derive import park_proximity, schools_file
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, cell_of, lsoa_ratio_by_homes, row_of, to_places
from burro_pipeline.derive.schools_file import (
    EASTING,
    KIND,
    NORTHING,
    PHASE,
    REGION,
    STATUS,
    URN,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.SCHOOL_PRIMARY_NEARBY
SOURCE = schools_file.SOURCE
PUBLISHER, PRODUCT = "Department for Education", "Get Information About Schools"
# The publisher's name for the download, as a browser saves it.
FILE = "extract.zip"
# The columns that are read. No other is asked for.
COLUMNS = (URN, STATUS, KIND, PHASE, REGION, EASTING, NORTHING)

# Every value the file of 2026-09-24 holds in each of the three columns, and whether a
# school of it counts. A value that is not here stops the build.
STATUSES: Mapping[str, bool] = {
    "Open": True,
    "Open, but proposed to close": True,
    "Closed": False,
    "Proposed to open": False,
}
# The types that count: schools an authority maintains, academies and free schools.
COUNTS = (
    "Academy converter",
    "Academy sponsor led",
    "Community school",
    "Foundation school",
    "Free schools",
    "Voluntary aided school",
    "Voluntary controlled school",
)
DOES_NOT_COUNT = (
    "Academy 16 to 19 sponsor led",
    "Academy 16-19 converter",
    "Academy alternative provision converter",
    "Academy alternative provision sponsor led",
    "Academy secure 16 to 19",
    "Academy special converter",
    "Academy special sponsor led",
    "British schools overseas",
    "City technology college",
    "Community special school",
    "Foundation special school",
    "Free schools 16 to 19",
    "Free schools alternative provision",
    "Free schools special",
    "Further education",
    "Higher education institutions",
    "Institution funded by other government department",
    "Local authority nursery school",
    "Miscellaneous",
    "Non-maintained special school",
    "Offshore schools",
    "Online provider",
    "Other independent school",
    "Other independent special school",
    "Pupil referral unit",
    "Secure units",
    "Service children's education",
    "Sixth form centres",
    "Special post 16 institution",
    "Studio schools",
    "University technical college",
    "Welsh establishment",
)
KINDS: Mapping[str, bool] = {**dict.fromkeys(COUNTS, True), **dict.fromkeys(DOES_NOT_COUNT, False)}
PHASES: Mapping[str, bool] = {
    "Primary": True,
    "Middle deemed primary": True,
    "All-through": True,
    "Middle deemed secondary": False,
    "Secondary": False,
    "Nursery": False,
    "16 plus": False,
    "Not applicable": False,
}
# The region of the register that is London, by its name in the file.
LONDON = "London"
# How the register writes a point it does not give: nothing, or nought.
NO_POINT = ("", "0")
WHOLE = re.compile(r"[0-9]{1,7}")

# A school is within reach of a home within this many metres, in a straight line.
REACH = 800
# A school is looked for this far from a home, in metres, and no further.
FAR = 10_000
# The register holds schools round the homes of a build where all but a few centres have
# one within `FAR`, and all but a few of the schools that count have a point.
UNREACHED_IN_100 = 1
UNPLACED_IN_100 = 1
# The schools are kept by squares this wide while those within reach are looked for, in metres.
KEPT_BY = 1_000
# What the rows of the file are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POINT
# A figure is given to this many decimal places.
DECIMALS = 1
CENSUS = 2021

METHOD = Method(
    derivation_id="points_within_800m_by_homes@1",
    sentence="The number of the points that count within 800 metres, in a straight line, of the "
    "point where the homes of each census output area are taken to stand, added up over the "
    "area's homes at the census and divided by those homes, and not given where under 50 in 100 "
    "of the area's homes are in an output area that has such a point.",
    kind=Kind.MEASURED,
    parameters={"metres": REACH, "enough_in_100": 50},
    code="burro_pipeline.derive.school_primary_nearby",
)
METHODS: tuple[Method, ...] = (METHOD,)
# The arithmetic of the distance to the nearest school. It is the nearest park's.
NEAREST = park_proximity.STRAIGHT_LINE
# What a person reads beside the figure: it is a straight line, and no walk.
LABEL = "State primary schools within 800 m in a straight line"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The number of state primary schools within {metres} metres, in a straight line, of where "
    "homes stand, from the register {product} of the {publisher} as at {day}: a school counts "
    "where the register gives it as open, as one of the {types} types of school that an "
    "authority maintains or that is an academy or a free school, and as of the phase primary, "
    "middle deemed primary or all-through, each school is placed at the point the register "
    "gives it, each home is placed at the point the statistics office gives as the centre of "
    "its census output area, homes are counted as they stood at the census of {census}, a "
    "school past the edge of London counts where it is within the distance, and the figure is "
    "the mean over the area's homes, given to {decimals} decimal place with a half taken "
    "upward, so it is measured across whatever lies between and not along any street, and it "
    "says nothing of how good a school is, of whether it has a place, or of where it takes its "
    "pupils from."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This counts schools within a straight line of where the homes of each small census area "
    "are taken to stand, and not within a walk, so a railway, a river or a main road in between "
    "puts a school further off than the figure says.",
    "It cannot see how good a school is, whether it has a place or where it takes its pupils "
    "from, so a school close by is not a place at it, and an infant school and a junior school "
    "on one site are counted as two.",
)


def is_the_register(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the download of the register."""
    return name == FILE


def _refused(file_id: str, words: str) -> LockError:
    return LockError("input_is_as_described", file_id, words)


@dataclass(frozen=True)
class Tally:
    """What the register holds of some of its rows, and what each step of the choice dropped."""

    rows: int
    # How many rows each value dropped, in the order the columns are asked: a row that is
    # not open is dropped by its status, and is not counted under its type or its phase.
    dropped_by_status: Mapping[str, int]
    dropped_by_kind: Mapping[str, int]
    dropped_by_phase: Mapping[str, int]
    # The schools that count, by their type.
    counted_by_kind: Mapping[str, int]
    # Of the open schools of every kind, and of the schools that count, how many have no point.
    open_without_a_point: int
    without_a_point: int

    @property
    def open_rows(self) -> int:
        return self.rows - sum(self.dropped_by_status.values())

    @property
    def counted(self) -> int:
        return sum(self.counted_by_kind.values())


@dataclass(frozen=True)
class Schools:
    """The schools of the register that count, and where each stands."""

    # The day the register was made, as the name of the file gives it.
    day: str
    # The point of every school that counts and has one, in order. Two schools on one point
    # are two points.
    points: tuple[Point, ...]
    # Those of them that the register gives to a region other than London.
    past_the_edge: tuple[Point, ...]
    # How many points hold more than one school, and how many schools stand on such a point.
    shared_points: int
    on_a_shared_point: int
    # The whole register, and its rows of the region London.
    england: Tally
    london: Tally
    file_id: str


@dataclass(frozen=True)
class Nearby:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    schools: Schools
    # The schools within reach of each output area that has a centre.
    within: Mapping[str, int]
    # How far each output area is from the nearest school, in metres, and the median of it
    # over each area's homes. It is of no release.
    metres: Mapping[str, float]
    nearest: Mapping[str, Worked]
    # How many schools are within reach of a centre of the build, and how many of those the
    # register gives to a region other than London.
    reached: int
    reached_past_the_edge: int


class _Tallied:
    """The counts of one `Tally`, while the register is read."""

    def __init__(self) -> None:
        self.rows = 0
        self.by_status: Counter[str] = Counter()
        self.by_kind: Counter[str] = Counter()
        self.by_phase: Counter[str] = Counter()
        self.counted: Counter[str] = Counter()
        self.open_without_a_point = 0
        self.without_a_point = 0

    def tally(self) -> Tally:
        return Tally(
            rows=self.rows,
            dropped_by_status=dict(sorted(self.by_status.items())),
            dropped_by_kind=dict(sorted(self.by_kind.items())),
            dropped_by_phase=dict(sorted(self.by_phase.items())),
            counted_by_kind=dict(sorted(self.counted.items())),
            open_without_a_point=self.open_without_a_point,
            without_a_point=self.without_a_point,
        )


def _point_of(row: Mapping[str, str], file_id: str) -> Point | None:
    """The point the register gives a school, or none where it gives none."""
    east, north = row[EASTING].strip(), row[NORTHING].strip()
    if east in NO_POINT and north in NO_POINT:
        return None
    if not (WHOLE.fullmatch(east) and WHOLE.fullmatch(north)) or "0" in (east, north):
        raise _refused(file_id, "a point is no point")
    return float(east), float(north)


def _verdict(known: Mapping[str, bool], value: str, file_id: str, words: str) -> bool:
    if value not in known:
        raise _refused(file_id, words)
    return known[value]


def schools_of(rows: Iterable[Mapping[str, str]], day: str, file_id: str) -> Schools:
    """The schools that count, from the rows of the register, with what each step dropped.

    A row is asked its status, then its type, then its phase, and is dropped
    by the first that does not count. Every value of each column is held to
    the ones this module knows, whether or not the row was dropped before.
    """
    england, london = _Tallied(), _Tallied()
    points: list[Point] = []
    past_the_edge: list[Point] = []
    seen: set[str] = set()
    for row in rows:
        if not row[URN] or row[URN] in seen:
            raise _refused(file_id, "a school is there twice, or has no number")
        seen.add(row[URN])
        is_open = _verdict(STATUSES, row[STATUS], file_id, "a status is not known")
        of_kind = _verdict(KINDS, row[KIND], file_id, "a type of school is not known")
        of_phase = _verdict(PHASES, row[PHASE], file_id, "a phase is not known")
        point = _point_of(row, file_id)
        for tallied in (england, *((london,) if row[REGION] == LONDON else ())):
            tallied.rows += 1
            if not is_open:
                tallied.by_status[row[STATUS]] += 1
                continue
            tallied.open_without_a_point += point is None
            if not of_kind:
                tallied.by_kind[row[KIND]] += 1
            elif not of_phase:
                tallied.by_phase[row[PHASE]] += 1
            else:
                tallied.counted[row[KIND]] += 1
                tallied.without_a_point += point is None
        if is_open and of_kind and of_phase and point is not None:
            points.append(point)
            if row[REGION] != LONDON:
                past_the_edge.append(point)
    if not points:
        raise _refused(file_id, "it holds no school that counts")
    if england.without_a_point * 100 > UNPLACED_IN_100 * sum(england.counted.values()):
        raise _refused(file_id, "too many of its schools have no point")
    on_each = Counter(points)
    return Schools(
        day=day,
        points=tuple(sorted(points)),
        past_the_edge=tuple(sorted(past_the_edge)),
        shared_points=sum(1 for held in on_each.values() if held > 1),
        on_a_shared_point=sum(held for held in on_each.values() if held > 1),
        england=england.tally(),
        london=london.tally(),
        file_id=file_id,
    )


def read(opened: Opened) -> Schools:
    """The schools of the register that count. The seven columns are read, and no other."""
    day = schools_file.MEMBER.fullmatch(schools_file.member_of(opened))
    if day is None:
        raise _refused(opened.file_id, "the file it holds is not the establishment download")
    written = day["day"]
    return schools_of(
        schools_file.rows(opened, COLUMNS),
        f"{written[:4]}-{written[4:6]}-{written[6:]}",
        opened.file_id,
    )


class _Kept:
    """Points, kept by the square each stands on, so that those near a point are found near it."""

    def __init__(self, points: Sequence[Point]) -> None:
        self._on: dict[tuple[int, int], list[Point]] = {}
        for point in points:
            self._on.setdefault(cell_of(*point, KEPT_BY), []).append(point)

    def within(self, point: Point, metres: int) -> list[Point]:
        """The points no further than so many metres from a point, in a straight line.

        The verdict is taken on the square of the distance, which no root has rounded.
        """
        low = cell_of(point[0] - metres, point[1] - metres, KEPT_BY)
        high = cell_of(point[0] + metres, point[1] + metres, KEPT_BY)
        return [
            other
            for across in range(low[0], high[0] + KEPT_BY, KEPT_BY)
            for up in range(low[1], high[1] + KEPT_BY, KEPT_BY)
            for other in self._on.get((across, up), ())
            if (other[0] - point[0]) ** 2 + (other[1] - point[1]) ** 2 <= metres * metres
        ]

    def nearest(self, point: Point, reach: int) -> float | None:
        """How far a point is from the nearest of the points, or none if none is within reach."""
        found = self.within(point, KEPT_BY)
        ring = KEPT_BY
        while not found and ring < reach:
            ring = min(2 * ring, reach)
            found = self.within(point, ring)
        if not found:
            return None
        return min(math.hypot(other[0] - point[0], other[1] - point[1]) for other in found)


def within_reach(
    schools: Schools, points: Mapping[str, Point]
) -> tuple[dict[str, int], dict[str, float], frozenset[Point]]:
    """For each output area that has a centre: the schools within reach, and how far the nearest.

    It gives the points that are within reach of any centre too. It stops
    where the register holds no school round the homes of the build: nought
    would then be a gap read as a figure.
    """
    kept = _Kept(schools.points)
    within: dict[str, int] = {}
    metres: dict[str, float] = {}
    reached: set[Point] = set()
    for oa in sorted(points):
        near = kept.within(points[oa], REACH)
        within[oa] = len(near)
        reached.update(near)
        nearest = kept.nearest(points[oa], FAR)
        if nearest is not None:
            metres[oa] = nearest
    if (len(within) - len(metres)) * 100 > UNREACHED_IN_100 * len(within):
        raise _refused(schools.file_id, "its schools do not reach the homes of the build")
    return within, metres, frozenset(reached)


def figures(within: Mapping[str, int], homes: Homes) -> dict[str, Worked]:
    """The figure of every area, to one decimal place, or why it has none.

    `within` holds the schools within reach of each output area that has a
    centre. One that has none adds nothing, and the coverage of its area
    falls by its homes. An area with no homes has no figure: a mean over homes
    is a mean only where there are homes.
    """
    oas = sorted(within)
    worked = lsoa_ratio_by_homes(
        {oa: float(homes.homes[oa] * within[oa]) for oa in oas},
        {oa: float(homes.homes[oa]) for oa in oas},
        {oa: oa for oa in homes.area_of},
        homes,
    )
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def definition_of(day: str) -> str:
    """The sentence a methods page prints for the measure."""
    return DEFINITION.format(
        metres=REACH,
        product=PRODUCT,
        publisher=PUBLISHER,
        day=day,
        types=len(COUNTS),
        census=CENSUS,
        decimals=DECIMALS,
    )


def metric_of(files: Sequence[Receipt], day: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is `LABEL`: the one
    the figure supports, which is core's too. It is measured from points, and
    on no network.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=LABEL,
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=day,
        definition=definition_of(day),
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Nearby:
    """The figure of every area and its evidence, from the files of the build.

    The gate is asked about the register and about the centres before either
    is read. `found` is the spine of the same build: a row of evidence names
    its files beside the register and the centres, so they must be files this
    build opened. `edition` is the day of the register, as its receipt gives
    it. It tells apart the files of two days, once the store holds both.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=is_the_register)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    points = centres.centres_of(placed, found)
    if not points:
        raise _refused(placed.file_id, "it holds no centre of the build")
    schools = read(opened)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, placed.file_id, *found.inputs})
    if not all(file_id in handed for file_id in behind):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in behind)
    within, metres, reached = within_reach(schools, points)
    worked = figures(within, found.weights)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    return Nearby(
        worked=worked,
        rows=rows,
        metric=metric_of(files, schools.day),
        files=files,
        geography=KEYED_BY,
        schools=schools,
        within=within,
        metres=metres,
        nearest=park_proximity.figures(metres, found),
        reached=sum(1 for point in schools.points if point in reached),
        reached_past_the_edge=sum(1 for point in schools.past_the_edge if point in reached),
    )
