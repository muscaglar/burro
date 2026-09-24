"""Homes built before 1919, as a share of the homes whose build period is recorded.

What is counted:

- A home is a property on the council tax valuation lists, as the Valuation
  Office Agency counts them at 31 March of a year. An empty home is a home. A
  building that is not a home is not on the lists.
- The table of homes by build period gives each home one period, or none. Two
  periods end before 1919: before 1900, and 1900 to 1918. The two are added.
- The share is those homes over the homes of the area that have a period, as
  a percentage.

Which rows are read. The table has a row for every kind of area, from an LSOA
to England and Wales, and for every council tax band. A band is a value of
1991 and says nothing of when a home was built, so the row for all bands is
read. Two kinds of area are read:

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
| `-` | 1 to 4: a count too small to round to 10 |
| Anything else | The file is not what was described, and the step stops |

Neither the table nor the notes beside it says what `-` means. The reading is
held to the file's own rows, by `rounded_counts.disagrees`: every count of
every area of the build is held against the same count of its LSOAs, and the
step stops if any does not fit.

What a dash does to a figure:

- `0` for both periods: the figure is 0.0. The publisher counted no old home.
- `-` for one period or both, and no number: no figure is given, and the
  state is `suppressed`. The area has 1 to 8 old homes, so its share is not
  nought, and the file does not say what it is.
- `-` for one period and a number for the other: the number is the top, and
  the figure is marked `suppressed_in_source`. The dash hides at most 4 homes.
- `-` for homes of no known period: it is read as nothing. It moves the bottom
  by at most 4 homes, which is less than rounding does, and the figure is not
  marked for it.
- `-` for all homes: no figure is given, and the state is `suppressed`.

Homes of no known period. The table counts them apart. Nothing says when they
were built, so they are not counted as old and not counted as new: they are
left out of the top and of the bottom. What they lower is the coverage, which
is the share of the area's homes that have a period. So an area where many
homes have no period has a figure that is marked as partial, and below half
it has none.

Which census the codes follow. Neither the table nor its notes names a census.
So the table is held to the spine, which is made from the lookup of 2021: the
step stops if an LSOA or an MSOA of the spine has no row. A table on the codes
of 2011 would lack every area that was drawn again for 2021.

What is not read: the homes of each band, the 27 periods from 1919 on, and the
names of areas.
"""

import csv
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked, area_row_ratio, row_of, to_places
from burro_pipeline.derive.rounded_counts import ROUNDED_TO, TOO_SMALL, Count, disagrees
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow, Flag
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.HOMES_PRE1919
SOURCE = "voa-council-tax-stock-of-properties"
PUBLISHER = "Valuation Office Agency"
# The table of homes by build period. The publisher's name for its file starts so.
TABLE = "CTSOP4.1"
# The one table inside the zip. The notes beside it are a workbook, and are not read.
MEMBER = ".csv"
# The name of the table holds the day its counts are of: CTSOP4_1_2025_03_31.csv.
NAMED_FOR = re.compile(r"CTSOP4_1_(?P<year>[0-9]{4})_(?P<month>[0-9]{2})_(?P<day>[0-9]{2})\.csv")

# The columns that are read.
GEOGRAPHY, CODE, BAND = "geography", "ecode", "band"
BEFORE_1900, FROM_1900 = "bp_pre_1900", "bp_1900_1918"
NOT_KNOWN, HOMES = "bp_unkw", "all_properties"
BEFORE_1919 = (BEFORE_1900, FROM_1900)
COLUMNS = (GEOGRAPHY, CODE, BAND, *BEFORE_1919, NOT_KNOWN, HOMES)
# Every build period of more than one year that the table is known to hold, in its order.
# A period that is not here may end before 1919, so a table that holds one is refused.
PERIODS = (
    BEFORE_1900,
    FROM_1900,
    "bp_1919_1929",
    "bp_1930_1939",
    "bp_1945_1954",
    "bp_1955_1964",
    "bp_1965_1972",
    "bp_1973_1982",
    "bp_1983_1992",
    "bp_1993_1999",
    "bp_2000_2008",
)
A_PERIOD = "bp_"
# From 2009 the table has a column for each year, and gains one with each edition.
ONE_YEAR = re.compile(r"bp_20[0-9]{2}")
# The rows that are read, for all council tax bands together: that of an MSOA, which is the
# area's own while an area is an MSOA, and those of its LSOAs, which it is held to.
LSOA, MSOA, ALL_BANDS = "LSOA", "MSOA", "All"
LSOA_CODE = re.compile(r"[EW]01[0-9]{6}")
MSOA_CODE = re.compile(r"[EW]02[0-9]{6}")
# The year the measure is named for: a home of an earlier build period is counted.
BUILT_BEFORE = 1919
# A share is given to this many decimal places. Each count is within 5 homes of what was
# counted, of some thousands, so a second place would say nothing.
DECIMALS = 1
# What the rows of the table are keyed by, once the table has been held to the spine.
KEYED_BY = Geography.MSOA21

# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (AREA_ROW_RATIO,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Homes the {publisher} records as built before {before}, as a percentage of the homes on "
    "its council tax valuation lists as at {as_at} whose build period it records, which is "
    "its count of all homes less its count of homes of no recorded build period and not the "
    "sum of its counts by period: the counts are the publisher's own for the area, which it "
    "rounds to {rounded}, and are not added up from smaller areas; the share is given to "
    "{places} decimal place, with a half taken "
    "upward; where the publisher gives no count of old homes but a dash, which is a count too "
    "small to round, no figure is given; a home of no recorded build period is left out and "
    "lowers the coverage; so it is the recorded age of homes, and says nothing of their style "
    "or condition or of any building that is not a home."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts the build period the Valuation Office Agency records for each home, rounded to "
    "10 homes, and leaves out homes with no recorded period.",
    "It cannot see whether an old home has kept its character, what state it is in, or how old "
    "any building is that is not a home.",
)


@dataclass(frozen=True)
class Counted:
    """What the table holds for one LSOA or one MSOA, for all council tax bands together.

    A count is as the file gives it. It is `None` where the file writes `-`: a
    count too small to round, which the file does not give.
    """

    before_1900: Count
    from_1900: Count
    not_known: Count
    homes: Count

    @property
    def before_1919(self) -> int:
        """The homes of the two periods before 1919. A count too small to round adds nothing."""
        return (self.before_1900 or 0) + (self.from_1900 or 0)

    @property
    def dated(self) -> int | None:
        """The homes that have a build period: all homes, less those of none."""
        return None if self.homes is None else self.homes - (self.not_known or 0)

    @property
    def old_withheld(self) -> bool:
        """Whether a count of old homes was too small to round, so that the file gives none."""
        return self.before_1900 is None or self.from_1900 is None


@dataclass(frozen=True)
class Stock:
    """The homes of every MSOA and of every LSOA in the table, by when they were built."""

    # The rows the MSOAs are held to. They are part of no figure.
    of_lsoa: Mapping[str, Counted]
    # The publisher's own counts for each MSOA, which is the area while an area is an MSOA.
    of_msoa: Mapping[str, Counted]
    # The day the counts are of, as the name of the table gives it.
    as_at: str
    # How many rows stand under the header: those of larger areas and of single bands too.
    rows: int
    file_id: str


@dataclass(frozen=True)
class Pre1919:
    """The share of homes built before 1919 for every area, with what stands behind each."""

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
    """Stop if the table lacks a column that is read, or holds a period that is not known."""
    with opened.text(MEMBER) as text:
        try:
            header = next(csv.reader(text), list[str]())
        except csv.Error:
            raise _refused(opened, "a row is broken") from None
    for name in COLUMNS:
        if name not in header:
            # The name is the one this step asks for. Nothing of the file is repeated.
            raise _refused(opened, f"the column {name} is missing")
    periods = tuple(
        name
        for name in header
        if name.startswith(A_PERIOD) and name != NOT_KNOWN and not ONE_YEAR.fullmatch(name)
    )
    if periods != PERIODS:
        raise _refused(opened, "a build period is not one the step knows")


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


def _count(opened: Opened, cell: str) -> int | None:
    if cell == TOO_SMALL:
        return None
    if not (cell.isascii() and cell.isdigit()):
        raise _refused(opened, "a count is not a count")
    if int(cell) % ROUNDED_TO:
        raise _refused(opened, "a count is not rounded to 10")
    return int(cell)


def read(opened: Opened) -> Stock:
    """The homes of every MSOA and every LSOA in the table, by when they were built.

    It stops at a column that is missing, a build period it does not know, and
    a cell it cannot read.
    """
    _hold_the_header(opened)
    as_at = _as_at(opened)
    of_lsoa: dict[str, Counted] = {}
    of_msoa: dict[str, Counted] = {}
    rows = 0
    with opened.text(MEMBER) as text:
        for row in opened.rows(text, COLUMNS):
            rows += 1
            if row[BAND] != ALL_BANDS or row[GEOGRAPHY] not in (LSOA, MSOA):
                continue
            code = row[CODE]
            of_kind, shape = (
                (of_lsoa, LSOA_CODE) if row[GEOGRAPHY] == LSOA else (of_msoa, MSOA_CODE)
            )
            if not shape.fullmatch(code):
                raise _refused(opened, "a code is not a code")
            if code in of_kind:
                raise _refused(opened, "an area is there twice")
            of_kind[code] = Counted(
                before_1900=_count(opened, row[BEFORE_1900]),
                from_1900=_count(opened, row[FROM_1900]),
                not_known=_count(opened, row[NOT_KNOWN]),
                homes=_count(opened, row[HOMES]),
            )
    if not of_lsoa:
        raise _refused(opened, "it holds no row of an LSOA")
    if not of_msoa:
        raise _refused(opened, "it holds no row of an MSOA")
    return Stock(of_lsoa=of_lsoa, of_msoa=of_msoa, as_at=as_at, rows=rows, file_id=opened.file_id)


def keyed_by(stock: Stock, found: Spine) -> Geography:
    """What the rows a figure is read from are keyed by. It stops if that is not the MSOAs of 2021.

    The table names no census. The spine is made from the lookup of 2021, so a
    table that has a row for every LSOA and every MSOA of the spine is on the
    codes of 2021. One on the codes of 2011 lacks every area that was drawn
    again.
    """
    if any(lsoa not in stock.of_lsoa for lsoa in found.lsoas):
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

    Each count of an area's own row is held against the same count of its
    LSOAs, by the four rules of `rounded_counts`. They are what shows that a
    dash is a count of 1 to 4 and that a count is rounded once. It gives how
    many areas were held.
    """
    lsoas_of: dict[str, list[str]] = {}
    for cell in found.cells:
        lsoas_of.setdefault(cell.msoa, [])
    for lsoa, msoa in sorted({(cell.lsoa, cell.msoa) for cell in found.cells}):
        lsoas_of[msoa].append(lsoa)
    for msoa in sorted(lsoas_of):
        own = stock.of_msoa[msoa]
        parts = [stock.of_lsoa[lsoa] for lsoa in lsoas_of[msoa]]
        for count in (_before_1900, _from_1900, _not_known, _homes):
            words = disagrees(count(own), [count(part) for part in parts])
            if words is not None:
                raise LockError("input_is_as_described", stock.file_id, words)
    return len(lsoas_of)


def _before_1900(counted: Counted) -> Count:
    return counted.before_1900


def _from_1900(counted: Counted) -> Count:
    return counted.from_1900


def _not_known(counted: Counted) -> Count:
    return counted.not_known


def _homes(counted: Counted) -> Count:
    return counted.homes


def figures(stock: Stock, found: Spine) -> dict[str, Worked]:
    """The share of homes built before 1919 for every area, or why an area has no figure.

    Each count is the area's own, from the publisher's row for the MSOA the
    area is. An area with no count of all its homes has no figure. Nor has one
    whose old homes are all behind a dash: they are not nought, and the file
    does not say how many they are. A home of no known period adds nothing to
    the top or to the bottom, and the coverage falls by it.
    """
    rows = {
        area.area_id: stock.of_msoa[area.code] for area in found.areas if area.code in stock.of_msoa
    }
    counted = {area: one for area, one in rows.items() if one.homes}
    share = area_row_ratio(
        {
            area: float(one.before_1919)
            for area, one in counted.items()
            if one.before_1919 or not one.old_withheld
        },
        {area: float(one.dated or 0) for area, one in counted.items()},
        found.weights,
        times=100,
        covered={area: (one.dated or 0) / (one.homes or 1) for area, one in counted.items()},
        withheld=[area for area, one in rows.items() if one.old_withheld or one.homes is None],
        flags=[Flag.ROUNDED_IN_SOURCE],
    )
    if any(one.value is not None and one.value > 100 for one in share.values()):
        # Each count is rounded by itself, so the old homes of an area can come to more
        # than all its homes. No figure is cut to fit: a person must look.
        raise LockError("input_is_as_described", stock.file_id, "a share is more than the whole")
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in share.items()
    }


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the name, the unit and which way is more. The period is the
    day the table is of.
    """
    return catalogue_row(
        FEATURE,
        method=AREA_ROW_RATIO,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=DEFINITION.format(
            publisher=PUBLISHER,
            before=BUILT_BEFORE,
            as_at=as_at,
            rounded=ROUNDED_TO,
            places=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine) -> Pre1919:
    """The share of homes built before 1919 for every area, from the files of the build.

    The gate is asked about the table before it is read. `found` is the spine
    of the same build. A row of evidence names the table and the lookup, which
    says which MSOA an area is. It does not name the census table of homes:
    nothing is shared out by homes while the figure is the area's own row.
    """
    opened = inputs.open(SOURCE, Use.SCORING, named=is_the_table)
    stock = read(opened)
    geography = keyed_by(stock, found)
    held = hold_the_rows(stock, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in found.inputs):
        raise ValueError("the spine is made from files of this build")
    lookup = [file_id for file_id in found.inputs if handed[file_id].source_id == spine.LOOKUP]
    files = tuple(handed[file_id] for file_id in sorted({opened.file_id, *lookup}))
    worked = figures(stock, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], AREA_ROW_RATIO, files)
        for area in sorted(worked)
    )
    return Pre1919(
        worked=worked,
        rows=rows,
        metric=metric_of(files, stock.as_at),
        files=files,
        stock=stock,
        geography=geography,
        rows_held=held,
    )
