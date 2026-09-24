"""Homes per hectare: the homes on the council tax lists, over all the land inside the line.

What is counted:

- A home is a property on the council tax valuation lists, as the Valuation
  Office Agency counts them at 31 March of a year. The table of homes by band
  is read for its total and for no band. A band is a value of 1991, and says
  nothing of how built up a place is.
- The land is what the generalised outlines of the area's LSOAs enclose, in
  hectares, from `cells/land.py`. The outline is cut at the mean high water
  mark, so the tidal Thames is no part of it.

What the land takes in, and why:

- Everything inside the line is land: homes, roads, railways, parks, playing
  fields, reservoirs, docks and the river above the tide.
- Nothing is taken out, because nothing that may be read says what a piece of
  land is used for. No source of land use is registered for scoring.
- So the figure says how built up an area is as a whole. It is not how closely
  homes stand on the land that homes are on. An area with a large park or a
  reservoir reads as less dense than its streets are.

Which rows are read. The table has a row for every kind of area, from an LSOA
to England and Wales. Two kinds are read:

| Row | What it is for |
|---|---|
| Of an MSOA | The figure. While an area is an MSOA, it is the area's own row |
| Of an LSOA | To hold the MSOA's row to. It is part of no figure |

Why the area's own row, and not the sum of its LSOAs. The publisher rounds
every count to 10. The row of an MSOA is rounded once. A sum of the rows of
its LSOAs takes in one rounding for each, so it can differ from the row, and
it is not the number a reader finds in the publisher's table. The method is
`area_row_ratio`. When areas are drawn by hand no row is published for one,
and the figure must be summed from smaller areas by `lsoa_ratio_by_homes`.

How a cell of the table is read:

| The file writes | It is read as |
|---|---|
| A whole number of tens | A count. The publisher rounds every count to 10 |
| `0` | A count of nought |
| `-` | 1 to 4: a count too small to round to 10. An area with `-` has no figure |
| Anything else | The file is not what was described, and the step stops |

Neither the table nor the notes beside it says what `-` means. The reading is
held to the file's own rows, by `rounded_counts.disagrees`: the count of every
area of the build is held against the counts of its LSOAs, and the step stops
if any does not fit.

The publisher gives the total in three tables. This one is read because it is
the smallest, and has one row for an area and not nine. The three gave the
same total for every LSOA when they were compared, once, on the tables of 31
March 2025.

Which census the codes follow. Neither the table nor its notes names a census.
So the table is held to the spine, which is made from the lookup of 2021: the
step stops if an LSOA or an MSOA of the spine has no row. A table on the codes
of 2011 would lack every area that was drawn again for 2021. The land is
measured on the boundaries of 2021, and `cells/land.py` stops in the same way.

What is not read: the homes of each band, and the names of areas.
"""

import csv
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked, area_row_ratio, row_of, to_places
from burro_pipeline.derive.rounded_counts import ROUNDED_TO, TOO_SMALL, Count, disagrees
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow, Flag
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.HOMES_DENSITY
SOURCE = "voa-council-tax-stock-of-properties"
# The table of homes by band. The publisher's name for its file starts so.
TABLE = "CTSOP1.1"
# The one table inside the zip. The notes beside it are a workbook, and are not read.
MEMBER = ".csv"
# The table is named for the day its counts are of.
NAMED_FOR = re.compile(r"CTSOP1_1_(?P<year>[0-9]{4})_(?P<month>[0-9]{2})_(?P<day>[0-9]{2})\.csv")
# The columns that are read. The table holds a column for each band, which are not.
GEOGRAPHY, CODE, HOMES = "geography", "ecode", "all_properties"
COLUMNS = (GEOGRAPHY, CODE, HOMES)
# The table holds rows for larger areas too. The rows read are that of an MSOA, which is
# the area's own while an area is an MSOA, and those of its LSOAs, which it is held to.
LSOA, MSOA = "LSOA", "MSOA"
LSOA_CODE = re.compile(r"[EW]01[0-9]{6}")
MSOA_CODE = re.compile(r"[EW]02[0-9]{6}")
# A figure is given to this many decimal places. The count is within 5 homes of what was
# counted, of some thousands, so a second place would say nothing.
DECIMALS = 1
# What the rows a figure is read from are keyed by. It is held to the spine, and never assumed.
KEYED_BY = Geography.MSOA21
PUBLISHER, OF_THE_LAND = "Valuation Office Agency", "Office for National Statistics"

# The arithmetic, and how the land was measured: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (AREA_ROW_RATIO, land.MEASURED)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Properties on the council tax valuation lists as at {homes}, as the {publisher} counts "
    "them for the area itself and rounds to {rounded}, not added up from smaller areas, over "
    "the hectares inside the boundaries of the area's small census areas as at {land}, which "
    "the {of_the_land} generalised and cut at the mean high water mark: the figure is given to "
    "{places} decimal place, with a half taken upward, and every kind of land inside the line "
    "is counted, so it is not the density of the land that homes stand on."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "The land is everything inside the boundary, with its roads, railways, parks and water "
    "that is not tidal, so a place beside a large park reads as less dense than its streets are.",
    "It cannot see how tall a building is, how large a home is, or whether a home is lived in.",
)


@dataclass(frozen=True)
class Stock:
    """The homes of every MSOA and of every LSOA in the table, as the publisher counts them."""

    # The count of each LSOA that has one, by its code. They are part of no figure.
    homes: Mapping[str, int]
    # The LSOAs the file writes a dash for.
    withheld: frozenset[str]
    # The publisher's own count for each MSOA, which is the area while an area is an MSOA.
    # It is `None` where the file writes a dash.
    of_msoa: Mapping[str, Count]
    # The day the counts are of, as the name of the table gives it.
    as_at: str
    # How many rows stand under the header, those for larger areas too.
    rows: int
    file_id: str


@dataclass(frozen=True)
class Density:
    """Homes per hectare for every area, with what stands behind each figure."""

    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    stock: Stock
    # What the rows a figure is read from are keyed by, as the table was found to be.
    geography: Geography
    # How many areas had their own row held to the rows of their LSOAs.
    rows_held: int


def is_the_table(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the table this measure reads."""
    return name.startswith(TABLE)


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _hold_the_header(opened: Opened) -> None:
    """Stop if the table lacks a column that is read, and say which."""
    nothing: list[str] = []
    with opened.text(MEMBER) as text:
        try:
            header = next(csv.reader(text), nothing)
        except csv.Error:
            raise _refused(opened, "a row is broken") from None
    for name in COLUMNS:
        if name not in header:
            # The name is the one this step asks for. Nothing of the file is repeated.
            raise _refused(opened, f"the column {name} is missing")


def _as_at(opened: Opened) -> str:
    """The day the counts are of, from the name of the table. It must be the receipt's day."""
    named = NAMED_FOR.fullmatch(opened.member(MEMBER).rsplit("/", 1)[-1])
    if named is None:
        raise _refused(opened, "the table is not named for a day")
    try:
        day = date(int(named["year"]), int(named["month"]), int(named["day"])).isoformat()
    except ValueError:
        raise _refused(opened, "the table is not named for a day") from None
    if opened.receipt.data_period.as_at != day:
        raise _refused(opened, "the table is not of the day its receipt gives")
    return day


def _count(opened: Opened, cell: str) -> Count:
    if cell == TOO_SMALL:
        return None
    if not (cell.isascii() and cell.isdigit()):
        raise _refused(opened, "a count is not a count")
    if int(cell) % ROUNDED_TO:
        raise _refused(opened, "a count is not rounded to 10")
    return int(cell)


def read(opened: Opened) -> Stock:
    """The count of homes of every MSOA and every LSOA in the table.

    It stops at a column that is missing and at a cell it cannot read.
    """
    _hold_the_header(opened)
    as_at = _as_at(opened)
    of_lsoa: dict[str, Count] = {}
    of_msoa: dict[str, Count] = {}
    rows = 0
    with opened.text(MEMBER) as text:
        for row in opened.rows(text, COLUMNS):
            rows += 1
            if row[GEOGRAPHY] not in (LSOA, MSOA):
                continue
            code = row[CODE]
            of_kind, shape, kind = (
                (of_lsoa, LSOA_CODE, "an LSOA")
                if row[GEOGRAPHY] == LSOA
                else (of_msoa, MSOA_CODE, "an MSOA")
            )
            if not shape.fullmatch(code):
                raise _refused(opened, "a code is not a code")
            if code in of_kind:
                raise _refused(opened, f"{kind} is there twice")
            of_kind[code] = _count(opened, row[HOMES])
    if not of_lsoa:
        raise _refused(opened, "it holds no row of an LSOA")
    if not of_msoa:
        raise _refused(opened, "it holds no row of an MSOA")
    return Stock(
        homes={code: count for code, count in of_lsoa.items() if count is not None},
        withheld=frozenset(code for code, count in of_lsoa.items() if count is None),
        of_msoa=of_msoa,
        as_at=as_at,
        rows=rows,
        file_id=opened.file_id,
    )


def keyed_by(stock: Stock, found: Spine) -> Geography:
    """What the rows a figure is read from are keyed by. It stops if that is not the MSOAs of 2021.

    The table names no census. The spine is made from the lookup of 2021, so a
    table that has a row for every LSOA and every MSOA of the spine is on the
    codes of 2021. One on the codes of 2011 lacks every area that was drawn
    again.
    """
    if any(lsoa not in stock.homes and lsoa not in stock.withheld for lsoa in found.lsoas):
        raise LockError(
            "input_is_as_described", stock.file_id, "an LSOA of the census of 2021 has no row"
        )
    if any(area.code not in stock.of_msoa for area in found.areas):
        raise LockError(
            "input_is_as_described", stock.file_id, "an MSOA of the census of 2021 has no row"
        )
    return KEYED_BY


def hold_the_rows(stock: Stock, found: Spine) -> int:
    """Stop unless the row of every area is what the rows of its LSOAs allow.

    The count of an area's own row is held against the counts of its LSOAs, by
    the four rules of `rounded_counts`. They are what shows that a dash is a
    count of 1 to 4 and that a count is rounded once. It gives how many areas
    were held.
    """
    lsoas_of: dict[str, list[str]] = {}
    for cell in found.cells:
        lsoas_of.setdefault(cell.msoa, [])
    for lsoa, msoa in sorted({(cell.lsoa, cell.msoa) for cell in found.cells}):
        lsoas_of[msoa].append(lsoa)
    for msoa in sorted(lsoas_of):
        words = disagrees(stock.of_msoa[msoa], [stock.homes.get(lsoa) for lsoa in lsoas_of[msoa]])
        if words is not None:
            raise LockError("input_is_as_described", stock.file_id, words)
    return len(lsoas_of)


def figures(stock: Stock, measured: Land, found: Spine) -> dict[str, Worked]:
    """Homes per hectare for every area of the spine, or why an area has no figure.

    The count is the area's own, from the publisher's row for the MSOA the
    area is. The land is the area's, as `cells/land.py` measured it. An area
    whose row holds a dash has no figure: it has homes, and the file does not
    say how many.
    """
    rows = {
        area.area_id: stock.of_msoa[area.code] for area in found.areas if area.code in stock.of_msoa
    }
    worked = area_row_ratio(
        {area: float(count) for area, count in rows.items() if count is not None},
        measured.of_area,
        found.weights,
        withheld=[area for area, count in rows.items() if count is None],
        flags=[Flag.ROUNDED_IN_SOURCE],
    )
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def _when(period: Period) -> str:
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the name, the unit and which way is more. The period is the
    day the table of homes is of. The land is of the day its receipt gives.
    """
    period = {receipt.source_id: _when(receipt.data_period) for receipt in files}
    return catalogue_row(
        FEATURE,
        method=AREA_ROW_RATIO,
        source_ids=period,
        vintage=as_at,
        definition=DEFINITION.format(
            homes=as_at,
            publisher=PUBLISHER,
            rounded=ROUNDED_TO,
            land=period[land.BOUNDARIES],
            of_the_land=OF_THE_LAND,
            places=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine, measured: Land) -> Density:
    """Homes per hectare for every area, from the files of the build.

    The gate is asked about the table before it is read. `found` and
    `measured` are the spine and the land of the same build. A row of evidence
    names the table, the boundaries the land was measured on, and the lookup,
    which says which MSOA an area is and which LSOAs it takes in. It does not
    name the census table of homes: nothing is shared out by homes while the
    count is the area's own row.
    """
    opened = inputs.open(SOURCE, Use.SCORING, named=is_the_table)
    stock = read(opened)
    geography = keyed_by(stock, found)
    held = hold_the_rows(stock, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in (measured.file_id, *found.inputs)):
        raise ValueError("the spine and the land are made from files of this build")
    lookup = [file_id for file_id in found.inputs if handed[file_id].source_id == spine.LOOKUP]
    behind = sorted({opened.file_id, measured.file_id, *lookup})
    files = tuple(handed[file_id] for file_id in behind)
    worked = figures(stock, measured, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], AREA_ROW_RATIO, files)
        for area in sorted(worked)
    )
    return Density(
        worked=worked,
        rows=rows,
        metric=metric_of(files, stock.as_at),
        files=files,
        stock=stock,
        geography=geography,
        rows_held=held,
    )
