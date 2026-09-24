"""Homes built since 2000, as a share of the homes whose build period is recorded.

It is read from the table homes built before 1919 is read from, and in the
same way: `homes_pre1919` says what a home is, which rows are read, why the
area's own row is the figure, how a cell is read, and which census the codes
follow. This page says what differs.

What is counted:

- The table of homes by build period gives each home one period, or none. One
  period is 2000 to 2008. From 2009 the table has a column for each year, and
  gains one with each edition. The period and every year are added.
- The last year is the year of the day the table is of. The table of 31 March
  2025 holds a column for 2025, which is the homes of its first three months.
- The share is those homes over the homes of the area that have a period, as
  a percentage.

What a dash does to a figure. A dash is a count of 1 to 4, too small to round
to 10. In a column for one year it is common: a year in which an area gained a
handful of homes is written so.

- `0` for the period and for every year: the figure is 0.0. The publisher
  counted no home since 2000.
- A dash or a nought for each, and at least one dash: no figure is given, and
  the state is `suppressed`. The area has a home built since 2000, so its
  share is not nought, and the file does not say what it is.
- A dash for some and a number for others: the numbers are the top, and the
  figure is marked `suppressed_in_source`. Each dash hides 1 to 4 homes and
  adds nothing, and `Counted.hidden_at_most` says how many that can be. The
  figure is not a floor for it: a year of 5 to 9 homes is written as 10, as a
  year of 1 to 4 is written as a dash, so the counts that are added run over
  as well as under.
- `-` for homes of no known period, or for all homes: as for homes built
  before 1919.

More than the whole. Each count is rounded by itself, so in an area built
almost wholly since 2000 the counts that are added can come to more than the
homes that have a period. A share is never more than the whole. Where the
counts come to more by no more than rounding allows, which is 5 homes for each
number that is added and 5 for each of the two counts of the bottom, the share
is given as 100.0, and `Post2000.at_the_whole` names the area. Where they come
to more than that, the table is not what was described, and the step stops.

Which columns are years. The step reads the names of the columns, and takes as
a year each that is named for one. It stops unless the years run from 2009 to
the year of the day the table is of, with none missing and none after. A
period of more than one year that the step does not know stops it too: a table
that is laid out anew may count the years another way.

What is not read: the homes of each band, the periods that end before 2000,
and the names of areas.
"""

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.homes_pre1919 import (
    A_PERIOD,
    ALL_BANDS,
    BAND,
    CODE,
    GEOGRAPHY,
    HOMES,
    KEYED_BY,
    LSOA,
    LSOA_CODE,
    MEMBER,
    MSOA,
    MSOA_CODE,
    NAMED_FOR,
    NOT_KNOWN,
    ONE_YEAR,
    PERIODS,
    PUBLISHER,
    SOURCE,
    is_the_table,
)
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked, area_row_ratio, row_of, to_places
from burro_pipeline.derive.rounded_counts import (
    MOST_HIDDEN,
    ROUNDED_TO,
    ROUNDING,
    TOO_SMALL,
    Count,
    disagrees,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow, Flag
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.HOMES_POST2000
# The one period of more than a year that is counted. It is the last such period of the table.
FROM_2000 = "bp_2000_2008"
# The first year the table gives a column of its own.
FIRST_YEAR = 2009
# The year the measure is named for: a home of this year or a later one is counted.
BUILT_SINCE = 2000
# The columns that are read whatever the edition. The years are read beside them.
COLUMNS = (GEOGRAPHY, CODE, BAND, FROM_2000, NOT_KNOWN, HOMES)
# A share is given to this many decimal places. Each count is within 5 homes of what was
# counted, of some thousands, so a second place would say nothing.
DECIMALS = 1
# The most a share can be.
WHOLE = 100
# The bottom of the share is one count less another, and each is rounded.
IN_THE_BOTTOM = 2

# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (AREA_ROW_RATIO,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Homes the {publisher} records as built from {since} to {last}, as a percentage of the "
    "homes on its council tax valuation lists as at {as_at} whose build period it records, "
    "which is its count of all homes less its count of homes of no recorded build period and "
    "not the sum of its counts by period: the counts are the publisher's own for the area, "
    "which it rounds to {rounded}, and are not added up from smaller areas; the homes built "
    "since {since} are its count for {since} to {until} and its count for each year from "
    "{first} to {last}, added up; where it gives a dash for a year, which is a count of 1 to "
    "{hidden} and too small to round, the year adds nothing, as a year of {half} to {under} "
    "homes adds {rounded}; where it gives no count but a dash, no figure is given; where the "
    "counts that are added come to more than the homes with a period, which rounding allows in an "
    "area built almost wholly since {since}, the share is given as {whole}; the share is "
    "given to {places} decimal place, with a half taken upward; a home of no recorded build "
    "period is left out and lowers the coverage; so it is the recorded age of homes, and says "
    "nothing of what kind of home was built or of any building that is not a home."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts the build period the Valuation Office Agency records for each home, with the "
    "count of each year rounded to 10 by itself, and leaves out homes with no recorded period.",
    "It cannot see what stood there before, how tall or how large a new building is, or how "
    "old any building is that is not a home.",
)


@dataclass(frozen=True)
class Counted:
    """What the table holds for one LSOA or one MSOA, for all council tax bands together.

    A count is as the file gives it. It is `None` where the file writes `-`: a
    count too small to round, which the file does not give.
    """

    # The count for 2000 to 2008 and for each year after, in the order of the table.
    since_2000: tuple[Count, ...]
    not_known: Count
    homes: Count

    @property
    def new(self) -> int:
        """The homes of every period since 2000. A count too small to round adds nothing."""
        return sum(count or 0 for count in self.since_2000)

    @property
    def dashes(self) -> int:
        """How many of the counts since 2000 are too small to round, so that none is given."""
        return sum(count is None for count in self.since_2000)

    @property
    def hidden_at_most(self) -> int:
        """The most homes the dashes can hide. Each hides 1 to 4."""
        return MOST_HIDDEN * self.dashes

    @property
    def dated(self) -> int | None:
        """The homes that have a build period: all homes, less those of none."""
        return None if self.homes is None else self.homes - (self.not_known or 0)

    @property
    def new_withheld(self) -> bool:
        """Whether a count of new homes was too small to round, so that the file gives none."""
        return self.dashes > 0

    @property
    def over(self) -> int:
        """By how many homes the counts that are added come to more than the homes with a period."""
        return max(0, self.new - (self.dated or 0)) if self.homes else 0

    @property
    def rounding_allows(self) -> int:
        """How far over rounding alone can carry the counts: 5 for each number that is read.

        A nought is a count of none and a dash adds nothing, so neither can
        carry the counts over.
        """
        numbers = sum(bool(count) for count in self.since_2000)
        return ROUNDING * (numbers + IN_THE_BOTTOM)


@dataclass(frozen=True)
class Stock:
    """The homes of every MSOA and of every LSOA in the table, by when they were built."""

    # The rows the MSOAs are held to. They are part of no figure.
    of_lsoa: Mapping[str, Counted]
    # The publisher's own counts for each MSOA, which is the area while an area is an MSOA.
    of_msoa: Mapping[str, Counted]
    # The columns that were added up, in the order of the table: the period, and each year.
    added: tuple[str, ...]
    # The last year the table has a column for, which is the year of the day it is of.
    last_year: int
    # The day the counts are of, as the name of the table gives it.
    as_at: str
    # How many rows stand under the header: those of larger areas and of single bands too.
    rows: int
    file_id: str


@dataclass(frozen=True)
class Post2000:
    """The share of homes built since 2000 for every area, with what stands behind each."""

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
    # The areas whose counts came to more than the whole, within rounding, and read 100.0.
    at_the_whole: frozenset[str]


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _as_at(opened: Opened) -> date:
    """The day the counts are of, from the name of the table. It must be the receipt's day."""
    named = NAMED_FOR.fullmatch(opened.member(MEMBER).rsplit("/", 1)[-1])
    if named is None:
        raise _refused(opened, "the table is not named for a day")
    try:
        day = date(int(named["year"]), int(named["month"]), int(named["day"]))
    except ValueError:
        raise _refused(opened, "the table is not named for a day") from None
    if opened.receipt.data_period.as_at != day.isoformat():
        raise _refused(opened, "the table is not of the day its receipt gives")
    return day


def _years_of(opened: Opened, as_at: date) -> tuple[str, ...]:
    """The columns of the table that are each one year, in order. It holds the header to them.

    It stops if the table lacks a column that is read, holds a period of more
    than one year that is not known, or does not hold every year from 2009 to
    the year of its day and no other.
    """
    with opened.text(MEMBER) as text:
        try:
            header = next(csv.reader(text), list[str]())
        except csv.Error:
            raise _refused(opened, "a row is broken") from None
    for name in COLUMNS:
        if name not in header:
            # The name is the one this step asks for. Nothing of the file is repeated.
            raise _refused(opened, f"the column {name} is missing")
    named = [name for name in header if name.startswith(A_PERIOD) and name != NOT_KNOWN]
    if tuple(name for name in named if not ONE_YEAR.fullmatch(name)) != PERIODS:
        raise _refused(opened, "a build period is not one the step knows")
    years = tuple(name for name in named if ONE_YEAR.fullmatch(name))
    if years != tuple(f"{A_PERIOD}{year}" for year in range(FIRST_YEAR, as_at.year + 1)):
        raise _refused(opened, "the years since 2009 are not each there once, to the table's own")
    return years


def _count(opened: Opened, cell: str) -> Count:
    if cell == TOO_SMALL:
        return None
    if not (cell.isascii() and cell.isdigit()):
        raise _refused(opened, "a count is not a count")
    if int(cell) % ROUNDED_TO:
        raise _refused(opened, "a count is not rounded to 10")
    return int(cell)


def read(opened: Opened) -> Stock:
    """The homes of every MSOA and every LSOA in the table, by when they were built.

    It stops at a column that is missing, a build period it does not know, a
    year that is missing, and a cell it cannot read.
    """
    as_at = _as_at(opened)
    added = (FROM_2000, *_years_of(opened, as_at))
    of_lsoa: dict[str, Counted] = {}
    of_msoa: dict[str, Counted] = {}
    rows = 0
    with opened.text(MEMBER) as text:
        for row in opened.rows(text, (*COLUMNS, *added[1:])):
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
                since_2000=tuple(_count(opened, row[name]) for name in added),
                not_known=_count(opened, row[NOT_KNOWN]),
                homes=_count(opened, row[HOMES]),
            )
    if not of_lsoa:
        raise _refused(opened, "it holds no row of an LSOA")
    if not of_msoa:
        raise _refused(opened, "it holds no row of an MSOA")
    return Stock(
        of_lsoa=of_lsoa,
        of_msoa=of_msoa,
        added=added,
        last_year=as_at.year,
        as_at=as_at.isoformat(),
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
    if any(lsoa not in stock.of_lsoa for lsoa in found.lsoas):
        raise LockError(
            "input_is_as_described", stock.file_id, "an LSOA of the census of 2021 has no row"
        )
    if any(area.code not in stock.of_msoa for area in found.areas):
        raise LockError(
            "input_is_as_described", stock.file_id, "an MSOA of the census of 2021 has no row"
        )
    return KEYED_BY


def counts_of(counted: Counted) -> tuple[Count, ...]:
    """Every count of a row that is read, in one order: each period, no period, all homes."""
    return (*counted.since_2000, counted.not_known, counted.homes)


def hold_the_rows(stock: Stock, found: Spine) -> int:
    """Stop unless the row of every area is what the rows of its LSOAs allow.

    Each count of an area's own row is held against the same count of its
    LSOAs, by the four rules of `rounded_counts`: the count of each period
    that is added, of homes of no period and of all homes. They are what shows
    that a dash is a count of 1 to 4 and that a count is rounded once. It
    gives how many areas were held.
    """
    lsoas_of: dict[str, list[str]] = {}
    for cell in found.cells:
        lsoas_of.setdefault(cell.msoa, [])
    for lsoa, msoa in sorted({(cell.lsoa, cell.msoa) for cell in found.cells}):
        lsoas_of[msoa].append(lsoa)
    for msoa in sorted(lsoas_of):
        own = counts_of(stock.of_msoa[msoa])
        parts = [counts_of(stock.of_lsoa[lsoa]) for lsoa in lsoas_of[msoa]]
        for at, count in enumerate(own):
            words = disagrees(count, [part[at] for part in parts])
            if words is not None:
                raise LockError("input_is_as_described", stock.file_id, words)
    return len(lsoas_of)


def over_the_whole(stock: Stock, found: Spine) -> frozenset[str]:
    """The areas whose counts since 2000 come to more than their homes that have a period.

    Rounding allows it, by 5 homes for each count that is read. It stops where
    an area is over by more than that: no figure is cut to fit a table that is
    not what was described.
    """
    over = {
        area.area_id: stock.of_msoa[area.code]
        for area in found.areas
        if area.code in stock.of_msoa and stock.of_msoa[area.code].over
    }
    if any(one.over > one.rounding_allows for one in over.values()):
        raise LockError("input_is_as_described", stock.file_id, "a share is more than the whole")
    return frozenset(over)


def figures(stock: Stock, found: Spine) -> dict[str, Worked]:
    """The share of homes built since 2000 for every area, or why an area has no figure.

    Each count is the area's own, from the publisher's row for the MSOA the
    area is. An area with no count of all its homes has no figure. Nor has one
    whose new homes are all behind a dash: they are not nought, and the file
    does not say how many they are. A home of no known period adds nothing to
    the top or to the bottom, and the coverage falls by it. An area whose
    counts come to more than the whole, within rounding, reads 100.0.
    """
    rows = {
        area.area_id: stock.of_msoa[area.code] for area in found.areas if area.code in stock.of_msoa
    }
    counted = {area: one for area, one in rows.items() if one.homes}
    whole = over_the_whole(stock, found)
    share = area_row_ratio(
        {
            area: float(one.dated or 0) if area in whole else float(one.new)
            for area, one in counted.items()
            if one.new or not one.new_withheld
        },
        {area: float(one.dated or 0) for area, one in counted.items()},
        found.weights,
        times=WHOLE,
        covered={area: (one.dated or 0) / (one.homes or 1) for area, one in counted.items()},
        withheld=[area for area, one in rows.items() if one.new_withheld or one.homes is None],
        flags=[Flag.ROUNDED_IN_SOURCE],
    )
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in share.items()
    }


def metric_of(files: Sequence[Receipt], stock: Stock) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the name, the unit and which way is more. The period is the
    day the table is of.
    """
    return catalogue_row(
        FEATURE,
        method=AREA_ROW_RATIO,
        source_ids={receipt.source_id for receipt in files},
        vintage=stock.as_at,
        definition=DEFINITION.format(
            publisher=PUBLISHER,
            since=BUILT_SINCE,
            until=FIRST_YEAR - 1,
            first=FIRST_YEAR,
            last=stock.last_year,
            as_at=stock.as_at,
            rounded=ROUNDED_TO,
            hidden=MOST_HIDDEN,
            half=ROUNDING,
            under=ROUNDED_TO - 1,
            whole=WHOLE,
            places=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine) -> Post2000:
    """The share of homes built since 2000 for every area, from the files of the build.

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
    return Post2000(
        worked=worked,
        rows=rows,
        metric=metric_of(files, stock),
        files=files,
        stock=stock,
        geography=geography,
        rows_held=held,
        at_the_whole=over_the_whole(stock, found),
    )
