"""What homes let for: the middle monthly rent of each kind of home, for the place an area lies in.

No publisher gives a rent for an area as small as one of Burro's. The
statistics office gives the rents that were recorded in London over twelve
months, for each borough and for each postcode district: how many there were,
and their lower quartile, their median and their upper quartile, for a room, a
studio, and a home of one, two, three, and four or more bedrooms. The founder
decided on 2026-09-25 that these are shown, and used for a budget, with the
place a figure is of and the publisher's caution said beside it (ADR 0021, as
amended that day).

So an area is given the figure of the place it lies in, and the figure says
which place that is. It is never the area's own.

| An area takes | Where |
|---|---|
| The figure of a postcode district | Half or more of its homes stand in the district, and the |
| | district has a median and both quartiles for the kind of home |
| The figure of its borough | No district holds half of its homes, or the district has no |
| | such figure, and the borough has one |
| No figure | Neither has one. Nothing is filled in, and nothing is taken from a |
| | place the area does not lie in |

**Where the homes of an area stand.** An output area stands in the postcode
district of most of its postcodes in use, as the postcode directory gives them,
and in the first of them by name where two are level. Its homes are the
households of the census. An area takes a district where the homes of its
output areas that stand in it are half or more of all its homes, counted in
whole homes. Where two districts hold half each it takes the first by name. An
output area with no postcode in use stands in no district, and its homes are
homes of the area all the same. An area lies wholly in its borough.

**What the licence registry asks of the workbook, and what is done here.**

| The registry says | So here |
|---|---|
| Carry a figure as the workbook writes it | A figure is read to the pound and handed on as it is |
| A figure is of a place, and never of an area | Every row says the place: `CostOf` |
| Never take a figure from a place the area does not lie in | `figure_of` asks one district and |
| | one borough, and no other |
| Show the twelve months beside every figure | A row holds the first month and the last |
| Say what the workbook says of how to read it | The step stops at a workbook that no longer |
| | says it: `CLAIMED` |
| `..`, `-` and `.` are no figure, and never nought | Each is read as none, and says which |
| Counts are rounded to the nearest 10 | A row of evidence is marked `rounded_in_source` |
| Never blend it with the Price Index of Private Rents | That workbook is not read |

**What is read.** Two tables, by their names in the workbook: `2`, by borough,
and `3`, by postcode district. Of each, the place, the kind of home, the count
of rents, the lower quartile, the median and the upper quartile. The mean is
never read. The cover, the contents and the notes are read first, so that a
workbook that says another thing of itself than this module takes it to say is
stopped before a figure is read.

**How a cell is read.**

| The file writes | It is read as |
|---|---|
| A whole number above nought | A count, or a rent in pounds a month |
| `..` | No figure: the publisher says it is not available |
| `-` | No figure: the publisher withheld it, of fewer than five rents |
| `.` | No figure: the publisher says it does not apply |
| Anything else | The file is not what was described, and the step stops |

**What is carried.** A row that holds a count, a median and both quartiles. A
row that holds a median and no quartile is not carried: a rent of a release is
a range, and nothing is put in the place of a quartile that no source gives.

What it cannot see is in `CANNOT_SEE`. It holds no postcode: a district is what
stands before the space of one, and is how the publisher gives its figures.
"""

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.facts import cost_key, fact_id
from burro_core.ids import CostOfKind, FactKind, Segment, Tenure
from burro_core.release import (
    DISTRICT_PATTERN,
    FEWEST_SALES,
    CostEstimate,
    CostOf,
    confidence_of,
)

from burro_pipeline.cells import postcodes
from burro_pipeline.cells.postcodes import Lookup
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.methods import DECIMALS, Worked, row_of, to_places
from burro_pipeline.derive.noise_sheet import Value, read_sheet
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import FULLY_COVERED, EvidenceRow, Flag, State
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "ons-private-rental-market-london-postcode-district"
PUBLISHER = "Office for National Statistics"
# Whose Rent Officers collected the rents, as the cover of the workbook says.
COLLECTED_BY = "Valuation Office Agency"
# What the gate is asked before the workbook is read: a cost of a release is ranked on.
USE = Use.SCORING
# The publisher's name for the file starts so.
FILE_STARTS = "londonrentalstats"

COVER, CONTENTS, NOTES = "Cover sheet", "Contents", "Notes"
# The two tables that are read, by the names of their sheets.
OF_BOROUGHS, OF_DISTRICTS = "2", "3"
# The title of the workbook, which is the first row of its cover and ends with the months.
COVER_TITLE = "Private Rental Market in London: {months}"
# The contents and the notes name their columns in their third row, and so does a table.
HEADER_AT = 3
SHEET_NUMBER, SHEET_TITLE = "Worksheet Number", "Worksheet Title"
NOTE_NUMBER, NOTE_TEXT = "Note number", "Note text"
BOROUGH, DISTRICT, KIND = "Borough", "Postcode District", "Bedroom Category"
COUNT, LOWER, MEDIAN, UPPER = "Count of rents", "Lower quartile", "Median", "Upper quartile"
# The columns of a table that are read, beside the one that names the place. The mean is
# never read.
READ = (KIND, COUNT, LOWER, MEDIAN, UPPER)
# What the contents say each table holds, between the months and "for London".
HOLDS: Mapping[str, str] = {
    OF_BOROUGHS: "borough and bedroom category",
    OF_DISTRICTS: "postcode district and bedroom category",
}
A_TABLE = r"Summary of monthly rents recorded between (?P<months>.+) by {holds} for London"

# The kinds of home the workbook names, each as the contract names it for a rent.
KINDS: Mapping[str, Segment] = {
    "Room": Segment.ROOM,
    "Studio": Segment.STUDIO,
    "One Bedroom": Segment.BED_1,
    "Two Bedrooms": Segment.BED_2,
    "Three Bedrooms": Segment.BED_3,
    "Four or More Bedrooms": Segment.BED_4PLUS,
}
# The kinds of home a release carries a rent for, in the order the workbook gives them.
HOMES: tuple[Segment, ...] = tuple(KINDS.values())
# What stands in a cell where the publisher gives no figure.
NOT_AVAILABLE, WITHHELD, NOT_APPLICABLE = "..", "-", "."
NO_FIGURE = frozenset({NOT_AVAILABLE, WITHHELD, NOT_APPLICABLE})
# The fewest rents a figure may rest on. It is core's, so that a release holds no figure
# that rests on fewer. The publisher rounds a count to the nearest 10, so it writes no
# count under it.
FEWEST = FEWEST_SALES
ROUNDED_TO = 10
# The least share of the homes of an area that stand in a district, in hundredths, for the
# area to take the figure of the district.
HALF = 50
A_DISTRICT = re.compile(DISTRICT_PATTERN)

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
A_MONTH = re.compile(r"(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])")

# What a page of Burro says of these rents rests on what the workbook says of itself. The
# step holds the workbook to each, and stops where it no longer says it: a new edition is
# read only once the words of the product are still true of it.
CLAIMED_OF_THE_NOTES: Mapping[str, re.Pattern[str]] = {
    "that its figures are in pounds, to the pound": re.compile(
        r"expressed in £ values and rounded to the nearest £1\b"
    ),
    "that its counts are rounded": re.compile(r"\bCounts are rounded to the nearest 10\b"),
    "who collected the rents": re.compile(
        r"\bcollected by Rent Officers\b.*\bfrom letting agents and landlords who are "
        r"willing to provide data\b",
        re.DOTALL,
    ),
    "that its sample was not drawn at random": re.compile(r"\bThe sample is purposive\b"),
    "that areas should not be compared": re.compile(
        r"\bshould not be compared across time periods or between areas\b"
    ),
    "that it is not the index of rents": re.compile(
        r"\bnot comparable with\b.*\bPrice Index of Private Rents\b", re.DOTALL
    ),
    "who is left out of the sample": re.compile(
        r"\bHousing Benefit claimants are not included in the sample\b"
    ),
    "what is withheld": re.compile(
        r"\bfewer than five observations have been suppressed and denoted by '-'"
    ),
    "what is not available": re.compile(r"denoted by '\.\.' are not available\b"),
}
CLAIMED_OF_THE_COVER: Mapping[str, re.Pattern[str]] = {
    "how its figures are to be read": re.compile(
        r"\bno attempt has been made to account for the change in quality or composition of "
        r"rented property\b"
    ),
    "where the rents come from": re.compile(r"\bVOA's administrative database\b"),
}

# The arithmetic: what a methods page prints beside the figure. The two are one rule in two
# parts, and a row of evidence names the part its figure came by.
OF_THE_DISTRICT = Method(
    derivation_id="rent_of_the_district@1",
    sentence="The publisher's own figures for the postcode district in which 50 in 100 or "
    "more of the homes of the area stand, taken from its own row as they are written, where "
    "the row rests on 10 rents or more, and said to be of the district and never of the area "
    "alone: an output area stands in the district of most of its postcodes in use, and its "
    "homes are the households of the census.",
    kind=Kind.MEASURED,
    parameters={"fewest_rents": FEWEST, "least_share_of_homes_percent": HALF},
    code="burro_pipeline.derive.rent",
)
OF_THE_BOROUGH = Method(
    derivation_id="rent_of_the_borough@1",
    sentence="The publisher's own figures for the borough the area is in, taken from its own "
    "row as they are written, where the row rests on 10 rents or more, and said to be of the "
    "whole borough and never of the area alone: they are taken where no postcode district "
    "holds 50 in 100 of the homes of the area, or the district has no median with both "
    "quartiles.",
    kind=Kind.MEASURED,
    parameters={"fewest_rents": FEWEST, "least_share_of_homes_percent": HALF},
    code="burro_pipeline.derive.rent",
)
METHODS: tuple[Method, ...] = (OF_THE_DISTRICT, OF_THE_BOROUGH)
BY_KIND: Mapping[CostOfKind, Method] = {
    CostOfKind.POSTCODE_DISTRICT: OF_THE_DISTRICT,
    CostOfKind.BOROUGH: OF_THE_BOROUGH,
}
# What the figure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The median, the lower quartile and the upper quartile of the monthly rents that were "
    "recorded for {a_home} from {months}, in pounds, as the {publisher} gives them for a "
    "postcode district or a borough of London, from rents that Rent Officers of the "
    "{collected_by} collected from letting agents and landlords: an area takes the figures of "
    "the postcode district in which half or more of the homes of the area stand, and those of "
    "its borough where no district holds half or the district has no such figures; where "
    "neither has them no figure is given; so it is of the district or of the whole borough "
    "and never of the area alone, and is not an asking rent, what a new tenant pays, or a "
    "figure of the Price Index of Private Rents."
)
# What the product shows beside the figure. It quotes no figure.
CANNOT_SEE = (
    "This is the middle of the rents that were recorded in a postcode district or a borough, "
    "and is not of this area alone. Every area that takes the figure of one place shows the "
    "same.",
    "The rents are a sample that was not drawn at random: Rent Officers collect them from the "
    "letting agents and landlords who are willing to give them. Their publisher advises "
    "against comparing one area with another on them, or one period with another.",
    "It cannot tell a rent that was agreed this month from one agreed long ago, a large home "
    "from a small one of as many bedrooms, or a flat from a house. It is not an asking rent. "
    "Housing Benefit claimants are not in the sample.",
)
A_HOME: Mapping[Segment, str] = {
    Segment.ROOM: "a room in a shared home",
    Segment.STUDIO: "a studio",
    Segment.BED_1: "a home of one bedroom",
    Segment.BED_2: "a home of two bedrooms",
    Segment.BED_3: "a home of three bedrooms",
    Segment.BED_4PLUS: "a home of four or more bedrooms",
}


@dataclass(frozen=True)
class Given:
    """What one row of a table gives: how many rents, and their range in pounds a month."""

    rents: int
    lower: int
    median: int
    upper: int


@dataclass(frozen=True)
class Table:
    """One table of the workbook, by place and kind of home."""

    # The rows that hold a count, a median and both quartiles.
    given: Mapping[tuple[str, Segment], Given]
    # The rows of which the publisher withheld a figure.
    withheld: frozenset[tuple[str, Segment]]
    # Every place the table names, in the order of their names.
    places: tuple[str, ...]


@dataclass(frozen=True)
class Workbook:
    """The two tables that are read, and the months the rents were recorded in."""

    boroughs: Table
    districts: Table
    # The first month and the last, as `2025-04`, and as the workbook writes the span.
    since: str
    until: str
    months: str
    file_id: str


@dataclass(frozen=True)
class Stood:
    """Where the homes of one area stand, by postcode district."""

    # The district that holds half or more of the homes of the area, or none.
    district: str | None
    # The homes that stand in the district that holds the most of them, and the homes of
    # the area.
    homes: int
    of: int
    # How many districts the homes of the area stand in.
    districts: int


@dataclass(frozen=True)
class Let:
    """The rent of one kind of home for every area, with what stands behind each."""

    home: Segment
    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    # The place the figure of each area is of, and the figure, where it has one.
    taken: Mapping[str, tuple[CostOf, Given]]
    rows: tuple[EvidenceRow, ...]
    definition: str


@dataclass(frozen=True)
class Counts:
    """What was read, as counts. Nothing here is held to a number: a test on the real file is."""

    # The places each table names.
    boroughs: int
    districts: int
    # The areas that lie in a district by half or more of their homes, and those that do not.
    areas_of_a_district: int
    areas_of_no_district: int
    # For each kind of home, the areas whose figure is of each kind of place, and with none.
    by_home: Mapping[Segment, Mapping[str, int]]


@dataclass(frozen=True)
class Rents:
    """The rent of every kind of home for every area, from the files of the build."""

    of: Mapping[Segment, Let]
    # Where the homes of each area stand.
    stood: Mapping[str, Stood]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    since: str
    until: str
    counts: Counts


def is_the_workbook(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the workbook this measure reads."""
    return name.startswith(FILE_STARTS)


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def months_of(opened: Opened) -> tuple[str, str, str]:
    """The twelve months the receipt gives: the first, the last, and the span in words.

    The workbook writes the span as `April 2025 to March 2026`.
    """
    period = opened.receipt.data_period
    first = A_MONTH.fullmatch(period.start or "")
    last = A_MONTH.fullmatch(period.end or "")
    if first is None or last is None or period.start is None or period.end is None:
        raise _refused(opened, "its receipt does not give twelve months")
    months = 12 * (int(last["year"]) - int(first["year"]))
    if months + int(last["month"]) - int(first["month"]) != len(MONTHS) - 1:
        raise _refused(opened, "its receipt does not give twelve months")
    said = (
        f"{MONTHS[int(first['month']) - 1]} {first['year']} to "
        f"{MONTHS[int(last['month']) - 1]} {last['year']}"
    )
    return period.start, period.end, said


def _words(rows: Sequence[Mapping[str, Value]], column: str) -> str:
    return "\n".join(said for row in rows if isinstance(said := row[column], str))


def hold_the_contents(opened: Opened, months: str) -> None:
    """Stop unless the contents say each table holds what is read from it, of the months."""
    listed = read_sheet(opened, CONTENTS, (SHEET_NUMBER, SHEET_TITLE), header_at=HEADER_AT)
    described: dict[str, Value] = {}
    for row in listed:
        name = row[SHEET_NUMBER]
        if not isinstance(name, str) or name in described:
            raise _refused(opened, "its contents do not list each table once")
        described[name] = row[SHEET_TITLE]
    for sheet, holds in HOLDS.items():
        words = described.get(f"Worksheet {sheet}")
        shape = A_TABLE.format(holds=re.escape(holds))
        found = re.fullmatch(shape, words) if isinstance(words, str) else None
        if found is None:
            raise _refused(opened, f"its contents do not say what the table {sheet} holds")
        if found["months"] != months:
            raise _refused(opened, "its contents give another period than its receipt")


def hold_the_cover(opened: Opened, months: str) -> None:
    """Stop unless the cover says how the figures are to be read, and where they come from."""
    title = COVER_TITLE.format(months=months)
    said = _words(read_sheet(opened, COVER, (title,)), title)
    for what, shape in CLAIMED_OF_THE_COVER.items():
        if shape.search(said) is None:
            raise _refused(opened, f"its cover does not say {what}")


def hold_the_notes(opened: Opened) -> None:
    """Stop unless the notes say what a page of Burro says of the rents."""
    listed = read_sheet(opened, NOTES, (NOTE_NUMBER, NOTE_TEXT), header_at=HEADER_AT)
    said = _words(listed, NOTE_TEXT)
    for what, shape in CLAIMED_OF_THE_NOTES.items():
        if shape.search(said) is None:
            raise _refused(opened, f"its notes do not say {what}")


def _figure(opened: Opened, cell: Value) -> int | None:
    """The whole number in a cell, or none where the publisher gives no figure."""
    if isinstance(cell, str) and cell in NO_FIGURE:
        return None
    if not (isinstance(cell, float) and cell.is_integer() and cell > 0):
        raise _refused(opened, "a figure is not a figure")
    return int(cell)


def _given(opened: Opened, row: Mapping[str, Value]) -> Given | None:
    """What a row gives, where it holds a count, a median and both quartiles."""
    count, lower, median, upper = (_figure(opened, row[name]) for name in READ[1:])
    if count is not None and (count < FEWEST or count % ROUNDED_TO):
        raise _refused(opened, "a count is not a count")
    if count is None or lower is None or median is None or upper is None:
        return None
    if not lower <= median <= upper:
        raise _refused(opened, "a range is out of order")
    return Given(rents=count, lower=lower, median=median, upper=upper)


def read_table(opened: Opened, sheet: str, named: str) -> Table:
    """One table, held to what a place, a kind of home and a figure can be.

    It stops at a sheet or a column that is missing, a kind of home the
    workbook is not known to hold, a place that does not hold every kind of
    home once, a district that is not written as one, a cell that is neither a
    figure nor a mark, and a range that is out of order.
    """
    rows = read_sheet(opened, sheet, (named, *READ), header_at=HEADER_AT)
    given: dict[tuple[str, Segment], Given] = {}
    withheld: set[tuple[str, Segment]] = set()
    seen: Counter[str] = Counter()
    kinds: set[tuple[str, Segment]] = set()
    for row in rows:
        place, kind = row[named], row[KIND]
        if not isinstance(place, str) or not place:
            raise _refused(opened, "a place has no name")
        if named == DISTRICT and A_DISTRICT.fullmatch(place) is None:
            raise _refused(opened, "a district is not written as one")
        if not isinstance(kind, str) or kind not in KINDS:
            raise _refused(opened, "a kind of home is none the workbook is known to hold")
        key = (place, KINDS[kind])
        seen[place] += 1
        kinds.add(key)
        found = _given(opened, row)
        if found is not None:
            given[key] = found
        elif any(row[name] == WITHHELD for name in READ[1:]):
            withheld.add(key)
    if not rows:
        raise _refused(opened, "a table holds no row")
    if len(kinds) != len(rows) or any(count != len(KINDS) for count in seen.values()):
        raise _refused(opened, "a place does not hold every kind of home once")
    return Table(given=given, withheld=frozenset(withheld), places=tuple(sorted(seen)))


def read(opened: Opened) -> Workbook:
    """The two tables that are read, of the months the receipt gives.

    The contents, the cover and the notes are read first, so that a workbook
    that says another thing of itself than this module takes it to say is
    stopped before a figure is read.
    """
    since, until, months = months_of(opened)
    hold_the_contents(opened, months)
    hold_the_cover(opened, months)
    hold_the_notes(opened)
    return Workbook(
        boroughs=read_table(opened, OF_BOROUGHS, BOROUGH),
        districts=read_table(opened, OF_DISTRICTS, DISTRICT),
        since=since,
        until=until,
        months=months,
        file_id=opened.file_id,
    )


def _first_of_the_most(held: Mapping[str, int]) -> str:
    """The name that holds the most, and the first by name of those that are level."""
    return min(held, key=lambda name: (-held[name], name))


def stand(lookup: Lookup, found: Spine) -> dict[str, Stood]:
    """Where the homes of each area stand, by postcode district.

    An output area stands in the district of most of its postcodes in use.
    An area lies in a district where the homes of its output areas that stand
    in it are half or more of all its homes. It is counted in whole homes, so
    that no float decides which side of the line an area falls.
    """
    in_use = lookup.in_use_by_district()
    homes = found.homes
    stood: dict[str, Stood] = {}
    for area, oas in sorted(found.weights.of_area.items()):
        held: Counter[str] = Counter()
        for oa in oas:
            counted = in_use.get(oa)
            if counted:
                held[_first_of_the_most(counted)] += homes[oa]
        whole = sum(homes[oa] for oa in oas)
        most = _first_of_the_most(held) if held else None
        in_it = held[most] if most is not None else 0
        lies_in = most if in_it > 0 and 100 * in_it >= HALF * whole else None
        stood[area] = Stood(district=lies_in, homes=in_it, of=whole, districts=len(held))
    return stood


def held_to_the_build(workbook: Workbook, found: Spine) -> None:
    """Stop unless the workbook names every borough of the build, by the name the build gives.

    The workbook writes a borough by its name and gives no code. So a borough
    the workbook names otherwise than the lookup does would be given no
    figure, and its areas would be said to have none.
    """
    named = set(workbook.boroughs.places)
    if any(area.borough not in named for area in found.areas):
        raise LockError(
            "input_is_as_described", workbook.file_id, "a borough of the build has no row"
        )


def figure_of(
    workbook: Workbook, home: Segment, borough: str, stood: Stood
) -> tuple[Worked, tuple[CostOf, Given] | None]:
    """The figure of one kind of home for one area, and the place it is of, or why none.

    The district the area lies in is asked first, and then its borough. No
    other place is asked. What stands behind a figure is counted in rents,
    and what is covered is the share of the homes of the area that stand in
    the place the figure is of.
    """
    marked = (Flag.ROUNDED_IN_SOURCE,)
    district = stood.district
    if district is not None and (district, home) in workbook.districts.given:
        given = workbook.districts.given[district, home]
        covered = to_places(stood.homes / stood.of, DECIMALS)
        state = State.PRESENT if covered >= FULLY_COVERED else State.PARTIAL
        worked = Worked(float(given.median), given.rents, given.rents, covered, state, marked)
        return worked, (CostOf(kind=CostOfKind.POSTCODE_DISTRICT, name=district), given)
    if (borough, home) in workbook.boroughs.given:
        given = workbook.boroughs.given[borough, home]
        worked = Worked(float(given.median), given.rents, given.rents, 1.0, State.PRESENT, marked)
        return worked, (CostOf(kind=CostOfKind.BOROUGH, name=borough), given)
    if (borough, home) in workbook.boroughs.withheld:
        withheld = (Flag.SUPPRESSED_IN_SOURCE,)
        return Worked(None, 0, 1, 0.0, State.SUPPRESSED, withheld), None
    return Worked(None, 0, 1, 0.0, State.SOURCE_GAP), None


def _counts(workbook: Workbook, stood: Mapping[str, Stood], let: Mapping[Segment, Let]) -> Counts:
    by_home: dict[Segment, dict[str, int]] = {}
    for home, one in let.items():
        kinds = Counter(of.kind.value for of, _ in one.taken.values())
        by_home[home] = {kind.value: kinds[kind.value] for kind in CostOfKind} | {
            "none": len(one.worked) - len(one.taken)
        }
    lie_in = sum(1 for where in stood.values() if where.district is not None)
    return Counts(
        boroughs=len(workbook.boroughs.places),
        districts=len(workbook.districts.places),
        areas_of_a_district=lie_in,
        areas_of_no_district=len(stood) - lie_in,
        by_home=by_home,
    )


def build(inputs: Inputs, found: Spine) -> Rents:
    """The rent of every kind of home for every area, from the files of the build.

    The gate is asked about the workbook before it is read, for the use the
    registry gives it, and about the postcode directory. `found` is the spine
    of the same build. A row of evidence names the workbook, the directory,
    which says which district a postcode is of, and the files of the spine,
    which say which area an output area is part of and how many homes it
    holds.
    """
    opened = inputs.open(SOURCE, USE, named=is_the_workbook)
    workbook = read(opened)
    held_to_the_build(workbook, found)
    lookup = postcodes.build(inputs)
    stood = stand(lookup, found)

    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in found.inputs):
        raise ValueError("the spine is made from files of this build")
    named = {opened.file_id, lookup.receipt.file_id, *found.inputs}
    receipts = tuple(handed[file_id] for file_id in sorted(named))

    let: dict[Segment, Let] = {}
    for home in HOMES:
        worked: dict[str, Worked] = {}
        taken: dict[str, tuple[CostOf, Given]] = {}
        rows: list[EvidenceRow] = []
        for area in sorted(found.areas):
            figure, of = figure_of(workbook, home, area.borough, stood[area.area_id])
            worked[area.area_id] = figure
            method = OF_THE_BOROUGH if of is None else BY_KIND[of[0].kind]
            if of is not None:
                taken[area.area_id] = of
            key = fact_id(area.area_id, FactKind.COST, cost_key(Tenure.RENT, home))
            rows.append(row_of(key, figure, method, receipts))
        let[home] = Let(
            home=home,
            worked=worked,
            taken=taken,
            rows=tuple(rows),
            definition=DEFINITION.format(
                a_home=A_HOME[home],
                months=workbook.months,
                publisher=PUBLISHER,
                collected_by=COLLECTED_BY,
            ),
        )
    return Rents(
        of=let,
        stood=stood,
        files=receipts,
        since=workbook.since,
        until=workbook.until,
        counts=_counts(workbook, stood, let),
    )


def costs(rents: Rents) -> tuple[CostEstimate, ...]:
    """The rows of `cost.json`: the rent of each kind of home, in each area that has one.

    A row holds the range as the publisher wrote it, the place it is of, how
    many rents were recorded there, and the first month and the last of them.
    An area with no figure for a kind of home has no row, and its row of
    evidence says why. The rows are in the order a release keeps them.
    """
    source_ids = tuple(sorted({receipt.source_id for receipt in rents.files}))
    rows = [
        CostEstimate(
            area_id=area_id,
            tenure=Tenure.RENT,
            segment=let.home,
            lower_quartile=given.lower,
            median=given.median,
            upper_quartile=given.upper,
            confidence=confidence_of(given.rents),
            as_of=rents.until,
            since=rents.since,
            rents=given.rents,
            of=of,
            source_ids=source_ids,
        )
        for let in rents.of.values()
        for area_id, (of, given) in let.taken.items()
    ]
    return tuple(sorted(rows, key=lambda row: (row.area_id, row.tenure, row.segment)))


def evidence(rents: Rents) -> tuple[EvidenceRow, ...]:
    """The rows of evidence of the rents: one for each area and kind of home, with or without
    a figure."""
    return tuple(row for let in rents.of.values() for row in let.rows)
