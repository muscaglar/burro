"""Recorded criminal damage and arson: records a year for each 1,000 homes, for each area.

The figure comes from the police's own file of street-level crime, as the form
at data.police.uk makes it for the Metropolitan Police Service and the City of
London Police. Each month of each force is one file of the zip, and each row
of it is one record, with a kind and a point. The crime files alone are read,
through `derive/street_crime_files.py`, and of each row four columns: the
month, the kind, and the longitude and latitude of the point. Nothing of an
outcome, of a stop and search or of a person is read.

This module holds the counting. `derive/incident_antisocial.py` counts a
second kind with it, and `Recorded` says what differs between the two.

What is counted:

- A record of the kind `Criminal damage and arson`, as the file names it.
- In the latest 36 months the zip holds, and of them the months that are
  whole: `whole_months` has the rule.
- At the point the file gives. **The point is not where it happened.** The
  licence registry says the publisher moves each record to a nearby anonymous
  spot. So a record near the edge of an area may be counted in the area next
  to it, and the figure of a small area is less sure than its count suggests.
- In the area whose land the point lies on. A point is turned to the National
  Grid and laid on the outlines of London's small census areas, the same
  outlines the land of an area is measured on. The column of the file that
  names an LSOA is not read: the file does not say which census it follows.

What is not counted, and is said:

- A record with no point. It is in no area.
- A record whose point lies in no small census area of London.
- A month that is not whole.

**A month that is not whole.** Nothing in a file says whether a force gave
every record of a month. So the months are held to each other: a month is
whole where London's records of the kind in it are at least half of those of
the middle month. A month that is not is left out for every area, and the
figure is a count a year over the months that are left. Nothing stands in for
the month. The half is a choice and no finding.

**What it is divided by.** The homes of the area at the census of 2021, which
is what every figure of a build is shared out by. It is a count of buildings
lived in and says nothing of who lives in one. So a place with few homes and
many visitors reads high. `for_each_hectare` gives the same count over the
area's land, which no build carries: over land the figure follows how close
together homes stand, and says little that homes per hectare does not.

**The name and the unit.** The file counts arson with criminal damage, and the
figure is for each 1,000 homes. The row of the catalogue says both, as core
names the measure, so a build whose lists hold the police's file carries it.
A row of the proxy audit was written before it was served, in
`docs/research/data/incidents.md`, section 11. The audit was dropped on
2026-09-25 (ADR 0006, as amended), and the row holds nothing back.

What is read from the file and never assumed:

| What | Where it is read |
|---|---|
| The months | The names of the crime files, and the month of every row |
| The kind | The column `Crime type` of every row |
| The point | The columns `Longitude` and `Latitude` of every row |
"""

import math
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import land
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.shapes import Shape, holding, on_the_grid
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import street_crime_files
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import DECIMALS as SHARE_DECIMALS
from burro_pipeline.derive.methods import ENOUGH, Worked, row_of, to_places
from burro_pipeline.derive.one_indicator import cited, takes_in
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow, State, state_of
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.INCIDENT_CRIMINAL_DAMAGE
SOURCE = street_crime_files.SOURCE
EDITION = street_crime_files.EDITION

# The columns of a crime file that are read, and no other.
MONTH, KIND, LONGITUDE, LATITUDE = "Month", "Crime type", "Longitude", "Latitude"
COLUMNS = (MONTH, KIND, LONGITUDE, LATITUDE)
# What the rows of a crime file are keyed by.
KEYED_BY = Geography.POINT

# How many months are counted: the latest the zip holds.
MONTHS = 36
MONTHS_IN_A_YEAR = 12
# A month is whole where it holds at least this share of the records of the middle month.
WHOLE = 0.5
# A figure is counted for each of this many homes, and given to this many decimal places.
PER = 1000
DECIMALS = 1
UNIT = "per 1,000 homes a year"
# The same count over land is for each hectare, to this many decimal places.
DECIMALS_OVER_LAND = 2

COUNTED = Method(
    derivation_id="points_in_area_by_homes@1",
    sentence="The records whose point lies on the land of the area's small census areas, "
    "counted over the whole months of the latest 36 and given as a count a year, over the "
    "area's homes at the census, and not given where under 50 in 100 of the months are whole "
    "or where the area holds no home.",
    kind=Kind.MEASURED,
    parameters={"months": MONTHS, "whole_in_100": 50, "enough_in_100": 50},
    code="burro_pipeline.derive.incident_criminal_damage",
)
# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (COUNTED,)

# What stands in every sentence of a measure of this file, after what is counted.
MADE_SO = (
    "as the police's street-level crime file gives each record a kind and a point, counted "
    "over the {counted} whole months from {first} to {last} at the point the file gives, which "
    "its publisher moved to a nearby anonymous spot, in the area whose land the point lies on, "
    "given as a count a year for each {per} homes of the area at the census of 2021, to "
    "{decimals} decimal place with a half taken upward, so it counts what was recorded and "
    "not all that happened."
)
# What the product shows beside every figure of this file, after what is its own.
NOT_SEEN = (
    "Each record is at a point its publisher moved to a nearby anonymous spot, so a record "
    "near the edge of an area may be counted in the area next to it.",
    "It is counted for each 1,000 homes, so a place with few homes and many visitors reads high.",
    "It cannot see whether a force gave every record of a month: a month that holds under half "
    "the records of the middle month is left out, and nothing stands in for it.",
)


@dataclass(frozen=True)
class Recorded:
    """What one kind of record is, as the file names it and as the product says it."""

    feature: FeatureId
    # The kind, as the column `Crime type` writes it.
    kind: str
    # What a person reads beside the figure.
    label: str
    # What the measure counts: the start of its sentence, which `MADE_SO` ends.
    counts: str
    # What the product shows beside the figure that is this measure's alone.
    cannot_see: tuple[str, ...]


CRIMINAL_DAMAGE = Recorded(
    feature=FEATURE,
    kind="Criminal damage and arson",
    label="Recorded criminal damage and arson",
    counts="Records of criminal damage and arson, ",
    cannot_see=(
        "It counts what the police recorded as criminal damage or arson, which is not all that "
        "happened, and it cannot tell graffiti from a broken window or a fire.",
    ),
)

# What the product shows beside the figure.
CANNOT_SEE = (*CRIMINAL_DAMAGE.cannot_see, *NOT_SEEN)

# A point as the file writes it: its longitude and its latitude, as text.
Written = tuple[str, str]


@dataclass(frozen=True)
class Counted:
    """What the crime files hold of one kind: the records of each month, at each point."""

    # For each month that is counted, the records at each point.
    at: Mapping[str, Mapping[Written, int]]
    # For each month that is counted, the records with no point.
    without: Mapping[str, int]
    # How many crime files were read.
    files: int
    file_id: str

    @property
    def months(self) -> tuple[str, ...]:
        return tuple(sorted(self.at))

    def of_month(self, month: str) -> int:
        """Every record of the kind in one month, with a point or with none."""
        return sum(self.at[month].values()) + self.without[month]


@dataclass(frozen=True)
class Placed:
    """The records of one kind, by the area each lies in."""

    # For each month that is whole, the records in each area.
    of_area: Mapping[str, Mapping[str, int]]
    # The months that are whole, and those that are not.
    whole: tuple[str, ...]
    left_out: tuple[str, ...]
    # The records of the whole months whose point lies in no small census area of London,
    # and those that have no point.
    outside: int
    without: int

    def count(self, area: str) -> int:
        """The records of one area over the whole months."""
        return sum(self.of_area[month].get(area, 0) for month in self.whole)

    @property
    def period(self) -> Period:
        """From the first whole month to the last."""
        first, last = self.whole[0], self.whole[-1]
        return Period(as_at=first) if first == last else Period(start=first, end=last)


@dataclass(frozen=True)
class Incidents:
    """The figure of every area, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    counted: Counted
    placed: Placed
    geography: Geography


def is_the_zip(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a zip the form made."""
    return name.endswith(".zip")


def _refused(file_id: str, words: str) -> LockError:
    return LockError("input_is_as_described", file_id, words)


def _follow(months: Sequence[str]) -> bool:
    """Whether months follow each other with none between them missing."""
    numbered = [int(month[:4]) * MONTHS_IN_A_YEAR + int(month[5:]) for month in months]
    return all(later - earlier == 1 for earlier, later in pairwise(numbered))


def read(opened: Opened, what: Recorded = CRIMINAL_DAMAGE) -> Counted:
    """The records of one kind in the latest 36 months of the zip, at each point.

    It stops where the zip holds fewer months than are counted, where a month
    between two others is missing, where a force has no file of a month that
    is counted, and where a row is of another month than its file.
    """
    files = street_crime_files.crime_files(opened)
    months = sorted({file.month for file in files})[-MONTHS:]
    if len(months) < MONTHS:
        raise _refused(opened.file_id, "it holds fewer months than are counted")
    if not _follow(months):
        raise _refused(opened.file_id, "a month between two others is missing")
    read_from = [file for file in files if file.month in months]
    if len(read_from) != MONTHS * len(street_crime_files.FORCES):
        raise _refused(opened.file_id, "a force has no file of a month that is counted")
    at: dict[str, Counter[Written]] = {month: Counter() for month in months}
    without: Counter[str] = Counter({month: 0 for month in months})
    for file in read_from:
        for row in street_crime_files.rows(opened, file.name, COLUMNS):
            if row[MONTH] != file.month:
                raise _refused(opened.file_id, "a row is of another month than its file")
            if row[KIND] != what.kind:
                continue
            if row[LONGITUDE] and row[LATITUDE]:
                at[file.month][(row[LONGITUDE], row[LATITUDE])] += 1
            else:
                without[file.month] += 1
    return Counted(at=at, without=without, files=len(read_from), file_id=opened.file_id)


def whole_months(counted: Counted) -> tuple[str, ...]:
    """The months that hold at least half the records of the middle month."""
    least = WHOLE * statistics.median(counted.of_month(month) for month in counted.months)
    return tuple(
        month
        for month in counted.months
        if counted.of_month(month) >= least and counted.of_month(month) > 0
    )


def _number(file_id: str, written: Written) -> tuple[float, float]:
    try:
        longitude, latitude = float(written[0]), float(written[1])
    except ValueError:
        raise _refused(file_id, "a point is not a point") from None
    if not (math.isfinite(longitude) and math.isfinite(latitude)):
        raise _refused(file_id, "a point is not a point")
    if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
        raise _refused(file_id, "a point is not a point")
    return longitude, latitude


def place(counted: Counted, outlines: Mapping[str, Shape], found: Spine) -> Placed:
    """The records of the whole months, by the area whose land each point lies on.

    `outlines` are those of London's small census areas, on the National
    Grid. It stops if no record lies in London at all: the file is then of
    somewhere else.
    """
    whole = whole_months(counted)
    if not whole:
        raise _refused(counted.file_id, "it holds no record of the kind")
    written = sorted({point for month in whole for point in counted.at[month]})
    lies_in = dict(
        zip(
            written,
            holding(outlines, on_the_grid([_number(counted.file_id, one) for one in written])),
            strict=True,
        )
    )
    of_area: dict[str, Counter[str]] = {month: Counter() for month in whole}
    outside = 0
    for month in whole:
        for point in sorted(counted.at[month]):
            lsoa = lies_in[point]
            if lsoa is None:
                outside += counted.at[month][point]
            else:
                of_area[month][found.area_of_lsoa[lsoa]] += counted.at[month][point]
    if not any(of_area[month] for month in whole):
        raise _refused(counted.file_id, "it holds no record of London")
    return Placed(
        of_area=of_area,
        whole=whole,
        left_out=tuple(month for month in counted.months if month not in whole),
        outside=outside,
        without=sum(counted.without[month] for month in whole),
    )


def homes_of(found: Spine) -> dict[str, float]:
    """The homes of each area at the census of 2021."""
    homes = found.weights
    return {area: homes.weight(homes.of_area[area], by_count=False) for area in homes.areas}


def _figures(
    placed: Placed, over: Mapping[str, float], per: int, decimals: int
) -> dict[str, Worked]:
    covered = to_places(len(placed.whole) / MONTHS, SHARE_DECIMALS)
    years = len(placed.whole) / MONTHS_IN_A_YEAR
    found: dict[str, Worked] = {}
    for area in sorted(over):
        if over[area] <= 0:
            found[area] = Worked(None, 0, MONTHS, 0.0, State.SOURCE_GAP)
        elif covered < ENOUGH:
            found[area] = Worked(None, len(placed.whole), MONTHS, covered, State.BELOW_THRESHOLD)
        else:
            value = to_places(per * placed.count(area) / years / over[area], decimals)
            found[area] = Worked(value, len(placed.whole), MONTHS, covered, state_of(True, covered))
    return found


def figures(placed: Placed, found: Spine) -> dict[str, Worked]:
    """Records a year for each 1,000 homes, for every area, or why an area has no figure.

    The units of a figure are months: how many of the 36 are whole. What is
    covered is the share of the months that are whole. An area with no record
    has a figure of nought: the file covers it and holds none.
    """
    return _figures(placed, homes_of(found), PER, DECIMALS)


def for_each_hectare(placed: Placed, measured: Land) -> dict[str, Worked]:
    """The same count a year, for each hectare of the area's land. No build carries it."""
    return _figures(placed, measured.of_area, 1, DECIMALS_OVER_LAND)


def definition_of(what: Recorded, placed: Placed) -> str:
    """The sentence of the measure: what it counts, from whom, for which months, and how."""
    return what.counts + MADE_SO.format(
        counted=len(placed.whole),
        first=placed.whole[0],
        last=placed.whole[-1],
        per=f"{PER:,}",
        decimals=DECIMALS,
    )


def metric_of(what: Recorded, files: Sequence[Receipt], placed: Placed) -> Metric:
    """The row of the catalogue: the name, the unit, the months and every source.

    The unit is the figure's own, for each 1,000 homes, and core says the
    same. Were core to count the measure for each resident the row would still
    say homes, and a build would leave the measure out.
    """
    row = catalogue_row(
        what.feature,
        method=COUNTED,
        label=what.label,
        source_ids={receipt.source_id for receipt in files},
        vintage=f"{placed.whole[0]} to {placed.whole[-1]}",
        definition=definition_of(what, placed),
    )
    return row if row.unit == UNIT else row.model_copy(update={"unit": UNIT})


def records(inputs: Inputs, found: Spine, what: Recorded) -> Incidents:
    """One kind of record as a figure of every area, with its evidence.

    The gate is asked about the zip and about the outlines before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the zip and the outlines, so they must be files this build
    opened.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=EDITION, named=is_the_zip)
    drawn = inputs.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    counted = read(opened, what)
    placed = place(counted, land.read(drawn, found), found)
    if not takes_in(opened.receipt.data_period, placed.period):
        raise _refused(opened.file_id, "its receipt gives another period than its rows")
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, drawn.file_id, *found.inputs})
    for file_id in behind:
        if file_id not in handed:
            raise LockError("input_has_one_receipt", file_id)
    files = tuple(handed[file_id] for file_id in behind)
    worked = figures(placed, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, what.feature), worked[area], COUNTED, files)
        for area in sorted(worked)
    )
    return Incidents(
        worked=worked,
        # A row states the months that were counted, and not every month of the zip.
        rows=cited(rows, opened.receipt, files, placed.period),
        metric=metric_of(what, files, placed),
        files=files,
        counted=counted,
        placed=placed,
        geography=KEYED_BY,
    )


def build(inputs: Inputs, found: Spine) -> Incidents:
    """The figure of every area and its evidence, from the files of the build."""
    return records(inputs, found, CRIMINAL_DAMAGE)
