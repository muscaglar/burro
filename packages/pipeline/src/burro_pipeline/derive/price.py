"""What a home sells for: the median price paid, for each area and each kind of home.

The figure comes from the statistics office's workbook of median prices paid by
middle layer super output area (MSOA). An area of this build is an MSOA, so the
publisher's own figure for the MSOA is the area's figure. Nothing is added up,
averaged or modelled.

A release carries it as a cost: a price to buy, for each kind of home the
contract names. The founder decided on 2026-09-24 that what a home sells for
may be shown (ADR 0021), and the registry allows the workbook for `scoring`
and for `display`.

| What a release carries | How |
|---|---|
| A flat, and a terraced, a semi-detached and a detached house | A row of `cost.json`: `costs` |
| What a row holds | The median, and no range: the workbook gives no quartile |
| What the median rests on | `unstated`: the workbook gives no count of sales |
| A home of any kind | Nothing. The contract holds a price by kind of home |
| A figure the publisher withheld | No row. The evidence says why: `evidence` |

It is a cost and no measure: core's catalogue has no feature for a price, and
no vibe rests on one. So this module is no part of `derive/measures.py`. A
price says what homes sold for. It is no verdict on a place, or on who lives
there.

What the workbook says of itself, on its cover:

- Every figure is in pounds sterling.
- `[x]` stands where no figure is given: there were no sales, or fewer than 5,
  of that kind of home in the year. The publisher calls such a figure
  suppressed.
- The statistics were adapted from data of HM Land Registry.

It does not say how many sales stand behind a figure, which sales are counted,
or whether a year is of the days homes were sold or of the days the sales were
registered. So nothing here says so either.

Which sheets are read. The contents of the workbook say what each holds.

| Sheet | The median price paid for |
|---|---|
| `1a` | A home of any kind |
| `1b` | A detached house |
| `1c` | A semi-detached house |
| `1d` | A terraced house |
| `1e` | A flat or a maisonette |

Sheets `2a` to `3e` hold the same for newly built homes and for existing ones.
They are never opened.

Which column is read. A sheet has a column for every year that ends with a
quarter, from 1995. One is read: the year the receipt of the file gives. The
contents must say that the sheets end with that year, so that a receipt that
states another year than the file's last is noticed.

How a cell is read:

| The file writes | It is read as |
|---|---|
| A whole number above nought | The median, in pounds |
| `[x]` | No figure. The publisher withheld it: none to 4 homes were sold |
| Anything else | The file is not what was described, and the step stops |

What stands behind an area with no figure:

| The file holds | The state of the figure |
|---|---|
| `[x]` | `suppressed`, marked `suppressed_in_source` |
| No row for the MSOA on the sheet of a kind | `source_gap` |
| No row for the MSOA on the sheet of all kinds | The step stops: see below |

Which census the codes follow. The workbook names none. So it is held to the
spine, which is made from the lookup of 2021: the step stops if an MSOA of the
spine has no row on the sheet of all kinds, or if a row puts an MSOA in another
borough than the lookup does.

A median of few sales. The publisher gives a figure from 5 sales up, and no
count. So a figure of 5 sales cannot be told from one of 500. A row says that
what it rests on is not stated, and nothing is made up to stand for a count.

A home of one size. The workbook gives no price by bedrooms. A median for
flats is of flats of every size that were sold, and is what a budget for a
one-bedroom flat is held against. It is never scaled to a size of home, and
the sentence beside the figure says what it is of.

Rents. None is given here: `derive/rent.py` reads them, from another
workbook. The statistics office publishes rents for boroughs and for postcode
districts, and an area is given the figure of the place it lies in, which says
the place it is of (ADR 0021, as amended on 2026-09-25). `NO_RENT` is what a
renter is told of a build that did not read that workbook.

What is not read: the names of local authorities and of MSOAs, every year but
the one the receipt gives, and the sheets of newly built and of existing homes.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.facts import cost_key, fact_id
from burro_core.ids import Confidence, FactKind, Segment, Tenure
from burro_core.release import CostEstimate

from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.derive.noise_sheet import Value, read_sheet
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow, Flag, State
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "ons-median-house-prices-msoa"
PUBLISHER = "Office for National Statistics"
# What the gate is asked before the workbook is read: a cost of a release is ranked on.
USE = Use.SCORING
# The publisher's name for the file starts so.
FILE_STARTS = "medianpricepaidformsoa"

# The cover: one column of notes under the title of the workbook.
COVER, COVER_TITLE = "Cover", "Median price paid by Middle layer Super Output Area (MSOA)"
# The contents: what each sheet holds. The row that names its columns is the third.
CONTENTS, CONTENTS_HEADER_AT = "Contents", 3
SHEET_NAME, DESCRIPTION = "Sheet name", "Table description"
# A sheet of figures. Its title and its source stand above the row that names its columns.
HEADER_AT = 3
DISTRICT_CODE, MSOA_CODE = "Local authority code", "MSOA code"
# What stands in a cell where the publisher gives no figure.
WITHHELD = "[x]"
# The fewest sales the publisher gives a figure for, as the cover says.
FEWEST_SALES = 5
# What the rows of a sheet are keyed by, once the sheet has been held to the spine.
KEYED_BY = Geography.MSOA21

UNIT = "£"
# Which way is more. The file says what was paid, and nothing of what is better.
HIGHER, LOWER = "dearer", "cheaper"

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
AN_MSOA = re.compile(r"[EW]02[0-9]{6}")
A_DISTRICT = re.compile(r"[EW]0[6-9][0-9]{6}")
IN_POUNDS = re.compile(r"\bpounds sterling\b")
WHAT_WITHHELD_MEANS = re.compile(r"\[x\].*\bfewer than five house sales\b", re.DOTALL)
A_YEAR_ENDING = r"year ending [A-Z][a-z]+ [0-9]{4}"

# The arithmetic: what a methods page prints beside the measure. The pipeline design names
# no method for a figure the publisher gives for the area itself and that is no ratio. This
# is the one it needs, and it is held here until the design names it.
AREA_ROW_VALUE = Method(
    derivation_id="area_row_value@1",
    sentence="The publisher's own figure for the area, taken from its own row as it is "
    "written and never worked out from the rows of smaller or of larger areas, and not given "
    "where the row gives none.",
    kind=Kind.MEASURED,
    code="burro_pipeline.derive.price",
)
METHODS: tuple[Method, ...] = (AREA_ROW_VALUE,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The median price paid for {a_home} sold in the area in the year ending {month} {year}, in "
    "pounds, as the {publisher} gives it for the middle layer super output area the area is, "
    "in statistics it adapted from data of HM Land Registry: the figure is the publisher's own "
    "for the area, given as it is written and never worked out from smaller or larger areas; "
    "where there were no sales, or fewer than {fewest}, the publisher gives no figure and none "
    "is given here; so it is the middle of what was paid for the homes that were sold, which "
    "may be as few as {fewest}, and is not the value of a home that was not sold, an asking "
    "price, a rent or the price of a home of any one size."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is the middle price of the homes of one kind, of all sizes, that were sold in the "
    "year, and it may rest on as few as 5 sales. It cannot see the homes that were not sold, "
    "or how many sales stand behind it.",
    "It cannot tell a large home from a small one, so an area where large homes were sold "
    "reads dearer than one where small homes were. It is not an asking price or a rent.",
)
# What a renter is told, where a rent would stand, of a build that read no rents.
NO_RENT = (
    "Burro holds no rent for an area. Rents are published for each borough and for each "
    "postcode district, and not for an area as small as this."
)


@dataclass(frozen=True)
class Home:
    """One kind of home the workbook gives a median for."""

    # This module's own name for the figure. Core's catalogue has none.
    key: str
    sheet: str
    # What the contents say the sheet holds, between "Median price paid" and "by MSOA".
    said: str
    # The kind of home, as a sentence names one of it.
    a_home: str
    # The segment of the contract's cost file the figure is the middle of, where it has one.
    segment: Segment | None

    @property
    def label(self) -> str:
        return f"Median price paid for {self.a_home}"

    @property
    def cost_key(self) -> str | None:
        """The key of the contract's cost fact the figure would be the middle of."""
        return None if self.segment is None else cost_key(Tenure.BUY, self.segment)


ALL = Home("price_median", "1a", "", "a home", None)
HOMES: tuple[Home, ...] = (
    ALL,
    Home(
        "price_median_detached", "1b", " for detached houses", "a detached house", Segment.DETACHED
    ),
    Home(
        "price_median_semi_detached",
        "1c",
        " for semi-detached houses",
        "a semi-detached house",
        Segment.SEMI_DETACHED,
    ),
    Home(
        "price_median_terraced", "1d", " for terraced houses", "a terraced house", Segment.TERRACED
    ),
    Home(
        "price_median_flat", "1e", " for flats/maisonettes", "a flat or a maisonette", Segment.FLAT
    ),
)


@dataclass(frozen=True)
class Year:
    """The year of sales that is read: the one the receipt of the file gives."""

    period: Period
    # The name of the column of the year, as a sheet writes it.
    column: str
    # The year, as the contents of the workbook write it.
    said: str
    month: str
    year: int

    @property
    def vintage(self) -> str:
        return f"{self.period.start} to {self.period.end}"


@dataclass(frozen=True)
class Sheet:
    """What one sheet holds for the year that is read, for every MSOA it has a row for."""

    home: Home
    # The median of each MSOA that has one, in pounds.
    price: Mapping[str, int]
    # The MSOAs with a row and no figure: the publisher withheld it.
    withheld: frozenset[str]
    # The local authority the sheet puts each MSOA in.
    district: Mapping[str, str]
    # The rows under the header, for England and Wales.
    rows: int


@dataclass(frozen=True)
class Workbook:
    """The sheets that are read, by the key of their kind of home."""

    sheets: Mapping[str, Sheet]
    year: Year
    file_id: str


@dataclass(frozen=True)
class Named:
    """The name, the unit and the period of one figure: what a row of a catalogue would hold."""

    key: str
    label: str
    unit: str
    # Which way is more, as the words that fill "than 80% of areas".
    higher: str
    lower: str
    source_ids: tuple[str, ...]
    # The period the data describes.
    vintage: str
    definition: str
    # The key of the contract's cost fact the figure would be the middle of, where it has one.
    cost_key: str | None


@dataclass(frozen=True)
class Priced:
    """The median of one kind of home for every area, with what stands behind each."""

    home: Home
    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    named: Named


@dataclass(frozen=True)
class Prices:
    """Every figure of the workbook that is read, for every area."""

    of: Mapping[str, Priced]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    workbook: Workbook
    # What the rows a figure is read from are keyed by, as the workbook was found to be.
    geography: Geography


def is_the_workbook(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the workbook this measure reads."""
    return name.startswith(FILE_STARTS)


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def year_of(opened: Opened) -> Year:
    """The year of sales the receipt gives: twelve months, named for the last.

    The publisher names a column for the month a year ends with, as
    `Year ending Mar 2026`. The receipt gives the first month and the last.
    """
    period = opened.receipt.data_period
    first = A_MONTH.fullmatch(period.start or "")
    last = A_MONTH.fullmatch(period.end or "")
    if first is None or last is None:
        raise _refused(opened, "its receipt does not give a year of sales")
    months = 12 * (int(last["year"]) - int(first["year"]))
    if months + int(last["month"]) - int(first["month"]) != len(MONTHS) - 1:
        raise _refused(opened, "its receipt does not give a year of sales")
    month, year = MONTHS[int(last["month"]) - 1], int(last["year"])
    return Year(
        period=period,
        column=f"Year ending {month[:3]} {year}",
        said=f"year ending {month} {year}",
        month=month,
        year=year,
    )


def hold_the_cover(opened: Opened) -> None:
    """Stop unless the cover says the figures are in pounds, and what `[x]` stands for."""
    notes = read_sheet(opened, COVER, (COVER_TITLE,))
    said = [note for row in notes if isinstance(note := row[COVER_TITLE], str)]
    if not any(IN_POUNDS.search(note) for note in said):
        raise _refused(opened, "its cover does not say the figures are in pounds")
    if not any(WHAT_WITHHELD_MEANS.search(note) for note in said):
        raise _refused(opened, "its cover does not say what stands where no figure is given")


def hold_the_contents(opened: Opened, year: Year) -> None:
    """Stop unless the contents say each sheet holds what is read from it, up to the year."""
    listed = read_sheet(opened, CONTENTS, (SHEET_NAME, DESCRIPTION), header_at=CONTENTS_HEADER_AT)
    described: dict[str, Value] = {}
    for row in listed:
        name = row[SHEET_NAME]
        if not isinstance(name, str) or name in described:
            raise _refused(opened, "its contents do not list each sheet once")
        described[name] = row[DESCRIPTION]
    for home in HOMES:
        words = described.get(home.sheet)
        holds = rf"Table {home.sheet} - Median price paid{re.escape(home.said)} by MSOA, "
        span = rf"England and Wales, {A_YEAR_ENDING} to (?P<last>{A_YEAR_ENDING})"
        found = re.fullmatch(holds + span, words) if isinstance(words, str) else None
        if found is None:
            raise _refused(opened, f"its contents do not say what the sheet {home.sheet} holds")
        if found["last"] != year.said:
            raise _refused(opened, "its contents give another last year than its receipt")


def _price_of(opened: Opened, cell: Value) -> int | None:
    """The median in a cell, in pounds, or none where the publisher withheld it."""
    if cell == WITHHELD:
        return None
    if not (isinstance(cell, float) and cell.is_integer() and cell > 0):
        raise _refused(opened, "a price is not a price")
    return int(cell)


def read_one(opened: Opened, home: Home, year: Year) -> Sheet:
    """What one sheet holds for the year, held to what a code and a price can be.

    It stops at a sheet or a column that is missing, a code that is no code, an
    MSOA that is there twice, and a cell that is neither a price nor `[x]`.
    """
    rows = read_sheet(
        opened, home.sheet, (DISTRICT_CODE, MSOA_CODE, year.column), header_at=HEADER_AT
    )
    price: dict[str, int] = {}
    withheld: set[str] = set()
    district: dict[str, str] = {}
    for row in rows:
        code, within = row[MSOA_CODE], row[DISTRICT_CODE]
        if not (isinstance(code, str) and AN_MSOA.fullmatch(code)):
            raise _refused(opened, "a code is not a code")
        if not (isinstance(within, str) and A_DISTRICT.fullmatch(within)):
            raise _refused(opened, "a code is not a code")
        if code in district:
            raise _refused(opened, "an MSOA is there twice")
        district[code] = within
        found = _price_of(opened, row[year.column])
        if found is None:
            withheld.add(code)
        else:
            price[code] = found
    if not rows:
        raise _refused(opened, "it holds no row of an MSOA")
    return Sheet(
        home=home, price=price, withheld=frozenset(withheld), district=district, rows=len(rows)
    )


def read(opened: Opened) -> Workbook:
    """The five sheets that are read, for the year the receipt gives.

    The cover and the contents are read first, so that a workbook that says
    another thing of itself than this module takes it to say is stopped before
    a figure is read.
    """
    year = year_of(opened)
    hold_the_cover(opened)
    hold_the_contents(opened, year)
    sheets = {home.key: read_one(opened, home, year) for home in HOMES}
    return Workbook(sheets=sheets, year=year, file_id=opened.file_id)


def keyed_by(workbook: Workbook, found: Spine) -> Geography:
    """What the rows are keyed by. It stops if that is not the MSOAs of the census of 2021.

    The workbook names no census. The spine is made from the lookup of 2021.
    So the sheet of all kinds must hold a row for every MSOA of the spine, and
    every sheet must put an MSOA of the spine in the borough the lookup does.
    A workbook on the codes of 2011 would lack every MSOA drawn again for 2021.
    """
    whole = workbook.sheets[ALL.key]
    if any(area.code not in whole.district for area in found.areas):
        raise LockError(
            "input_is_as_described", workbook.file_id, "an MSOA of the census of 2021 has no row"
        )
    borough = {area.code: area.borough_code for area in found.areas}
    for home in HOMES:
        sheet = workbook.sheets[home.key]
        if any(sheet.district.get(code, within) != within for code, within in borough.items()):
            raise LockError(
                "input_is_as_described",
                workbook.file_id,
                "an MSOA is in another borough than the lookup gives",
            )
    return KEYED_BY


def figures(sheet: Sheet, found: Spine) -> dict[str, Worked]:
    """The median of every area, in pounds, or why an area has no figure.

    The figure is the publisher's own for the MSOA the area is. Nothing stands
    in for a figure the publisher withheld, or for a row the sheet lacks.
    """
    worked: dict[str, Worked] = {}
    for area in found.areas:
        if area.code in sheet.price:
            worked[area.area_id] = Worked(float(sheet.price[area.code]), 1, 1, 1.0, State.PRESENT)
        elif area.code in sheet.withheld:
            marked = (Flag.SUPPRESSED_IN_SOURCE,)
            worked[area.area_id] = Worked(None, 0, 1, 0.0, State.SUPPRESSED, marked)
        else:
            worked[area.area_id] = Worked(None, 0, 1, 0.0, State.SOURCE_GAP)
    return worked


def named(home: Home, files: Sequence[Receipt], year: Year) -> Named:
    """The name, the unit, the period and every source of the figure of one kind of home."""
    return Named(
        key=home.key,
        label=home.label,
        unit=UNIT,
        higher=HIGHER,
        lower=LOWER,
        source_ids=tuple(sorted({receipt.source_id for receipt in files})),
        vintage=year.vintage,
        definition=DEFINITION.format(
            a_home=home.a_home,
            month=year.month,
            year=year.year,
            publisher=PUBLISHER,
            fewest=FEWEST_SALES,
        ),
        cost_key=home.cost_key,
    )


def _row_id(area_id: str, home: Home) -> str:
    """The id of the row of evidence of one kind of home in one area.

    It is the id of the cost the figure is the middle of, so that the fact a
    release serves and its evidence cannot part. A home of any kind is no cost
    of the contract, and its row keeps this module's own name.
    """
    if home.cost_key is None:
        return fact_id(area_id, FactKind.FEATURE, home.key)
    return fact_id(area_id, FactKind.COST, home.cost_key)


def build(inputs: Inputs, found: Spine) -> Prices:
    """The median of every kind of home for every area, from the files of the build.

    The gate is asked about the workbook before it is read, for the use the
    registry gives it. `found` is the spine of the same build. A row of
    evidence names the workbook and the lookup, which says which MSOA an area
    is. It does not name the census table of homes: nothing is shared out by
    homes while the figure is the area's own.
    """
    opened = inputs.open(SOURCE, USE, named=is_the_workbook)
    workbook = read(opened)
    geography = keyed_by(workbook, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in found.inputs):
        raise ValueError("the spine is made from files of this build")
    lookup = [file_id for file_id in found.inputs if handed[file_id].source_id == spine.LOOKUP]
    files = tuple(handed[file_id] for file_id in sorted({opened.file_id, *lookup}))
    priced: dict[str, Priced] = {}
    for home in HOMES:
        worked = figures(workbook.sheets[home.key], found)
        rows = tuple(
            row_of(_row_id(area, home), worked[area], AREA_ROW_VALUE, files)
            for area in sorted(worked)
        )
        priced[home.key] = Priced(
            home=home, worked=worked, rows=rows, named=named(home, files, workbook.year)
        )
    return Prices(of=priced, files=files, workbook=workbook, geography=geography)


def costed(prices: Prices) -> tuple[Priced, ...]:
    """The kinds of home a release carries a price for: those the contract names."""
    return tuple(priced for priced in prices.of.values() if priced.home.segment is not None)


def costs(prices: Prices) -> tuple[CostEstimate, ...]:
    """The rows of `cost.json`: the median of each kind of home, in each area that has one.

    A row holds the median as the publisher wrote it, and no range: the
    workbook gives no quartile. What it rests on is `unstated`: the workbook
    gives no count of sales. An area with no figure for a kind of home has no
    row, and its row of evidence says why. The rows are in the order a release
    keeps them.
    """
    as_of = prices.workbook.year.period.end
    if as_of is None:
        raise ValueError("the year of sales has a last month")
    rows = [
        CostEstimate(
            area_id=area_id,
            tenure=Tenure.BUY,
            segment=segment,
            lower_quartile=None,
            median=int(worked.value),
            upper_quartile=None,
            confidence=Confidence.UNSTATED,
            as_of=as_of,
            source_ids=priced.named.source_ids,
        )
        for priced in costed(prices)
        if (segment := priced.home.segment) is not None
        for area_id, worked in priced.worked.items()
        if worked.value is not None
    ]
    return tuple(sorted(rows, key=lambda row: (row.area_id, row.tenure, row.segment)))


def evidence(prices: Prices) -> tuple[EvidenceRow, ...]:
    """The rows of evidence of the costs: one for each area and kind of home, with or without
    a figure."""
    return tuple(row for priced in costed(prices) for row in priced.rows)
