"""Homes in the higher council tax bands, as a share of homes.

It is read from the table homes per hectare is read from, and in the same
way: `homes_density` says what a home is, which rows are read, why the area's
own row is the figure, how a cell is read, and which census the codes follow.
This page says what differs.

What is counted:

- The table of homes by band gives each home one of eight bands, A to H. A
  ninth, I, is of Wales alone. The higher four of the eight are E, F, G and H,
  and the homes of those four are added.
- The share is those homes over all the homes of the area, as a percentage.

**A band is a value of 1991.** The Valuation Office Agency puts a home in a
band by what it would have sold for on 1 April 1991. So the share says which
homes stand in a place: larger ones, and ones that were dear then. It is no
estimate of what a home would sell for today, and the licence registry asks
that it is never used as one. No word of the measure says a price.

**It counts homes, and not people.** It is a reading of a word for a smart
area, as what homes sell for is, and is offered beside it. It says nothing of
who lives in a home or of what they earn, and nothing here reads a file that
does.

What a dash does to a figure. A dash is a count of 1 to 4, too small to round
to 10. The highest band has one in a third of London's areas.

- `0` for each of the four bands: the figure is 0.0.
- A dash or a nought for each, and at least one dash: no figure is given, and
  the state is `suppressed`. The area has a home in a higher band, so its
  share is not nought, and the file does not say what it is.
- A dash for some and a number for others: the numbers are the top, and the
  figure is marked `suppressed_in_source`. Each dash hides 1 to 4 homes and
  adds nothing. The figure is not a floor for it: a band of 5 to 9 homes is
  written as 10, so the counts that are added run over as well as under.
- `-` for all homes: no figure is given.

More than the whole. Each count is rounded by itself, so in an area whose
homes are almost all in the higher bands the four counts can come to more
than its homes. Where they come to more by no more than rounding allows,
which is 5 homes for each number that is added and 5 for the count of all
homes, the share is given as 100.0. Where they come to more than that, the
table is not what was described, and the step stops.

What is not read: the homes of the lower four bands, band I, and the names of
areas.
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
from burro_pipeline.derive.homes_density import (
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

FEATURE = FeatureId.HOMES_HIGHER_BANDS
# The higher four of the eight bands, by the names of their columns, and what a sentence
# calls them.
HIGHER = ("band_e", "band_f", "band_g", "band_h")
FROM, TO = "E", "H"
# The year a band is a value of.
VALUED_IN = 1991
# The columns that are read. The table holds the lower four bands and band I too.
COLUMNS = (GEOGRAPHY, CODE, *HIGHER, HOMES)
# A share is given to this many decimal places. Each count is within 5 homes of what was
# counted, of some thousands, so a second place would say nothing.
DECIMALS = 1
# The most a share can be.
WHOLE = 100
# The bottom of the share is one count, which is rounded.
IN_THE_BOTTOM = 1

# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (AREA_ROW_RATIO,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Homes in council tax bands {first} to {last}, as a percentage of all the properties on "
    "the council tax valuation lists of the {publisher} as at {as_at}: the counts are the "
    "publisher's own for the area, which it rounds to {rounded}, and are not added up from "
    "smaller areas; the homes of the four bands are added up; where it gives a dash for a "
    "band, which is a count of 1 to {hidden} and too small to round, the band adds nothing; "
    "where it gives no count but a dash, no figure is given; where the counts that are added "
    "come to more than all the homes, which rounding allows, the share is given as {whole}; "
    "the share is given to {places} decimal place, with a half taken upward; a band is what a "
    "home would have sold for in {valued}, so the share says which homes stand in a place, "
    "and is no estimate of what a home sells for today and no figure of who lives in one."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "A band is what a home would have sold for in 1991, so it says which homes stand in a "
    "place and nothing of what one sells for today.",
    "It counts homes. It says nothing of who lives in them, or of what they earn.",
    "It cannot tell a home that is lived in from one that stands empty, or a home built "
    "since from the band it would have been given then.",
)


@dataclass(frozen=True)
class Counted:
    """What the table holds for one LSOA or one MSOA.

    A count is as the file gives it. It is `None` where the file writes `-`: a
    count too small to round, which the file does not give.
    """

    # The count of each of the higher bands, in the order of the table.
    higher: tuple[Count, ...]
    homes: Count

    @property
    def in_the_bands(self) -> int:
        """The homes of the higher bands. A count too small to round adds nothing."""
        return sum(count or 0 for count in self.higher)

    @property
    def withheld(self) -> bool:
        """Whether a count of a higher band was too small to round, so that the file gives none."""
        return any(count is None for count in self.higher)

    @property
    def over(self) -> int:
        """By how many homes the counts that are added come to more than all the homes."""
        return max(0, self.in_the_bands - self.homes) if self.homes else 0

    @property
    def rounding_allows(self) -> int:
        """How far over rounding alone can carry the counts: 5 for each number that is read."""
        numbers = sum(bool(count) for count in self.higher)
        return ROUNDING * (numbers + IN_THE_BOTTOM)


@dataclass(frozen=True)
class Stock:
    """The homes of every MSOA and of every LSOA in the table, and how many are in a higher band."""

    # The rows the MSOAs are held to. They are part of no figure.
    of_lsoa: Mapping[str, Counted]
    # The publisher's own counts for each MSOA, which is the area while an area is an MSOA.
    of_msoa: Mapping[str, Counted]
    # The day the counts are of, as the name of the table gives it.
    as_at: str
    # How many rows stand under the header, those for larger areas too.
    rows: int
    file_id: str


@dataclass(frozen=True)
class Banded:
    """The share of homes in the higher bands for every area, with what stands behind each."""

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
    """The homes of every MSOA and every LSOA in the table, and those of the higher bands.

    It stops at a column that is missing and at a cell it cannot read.
    """
    _hold_the_header(opened)
    as_at = _as_at(opened)
    of_lsoa: dict[str, Counted] = {}
    of_msoa: dict[str, Counted] = {}
    rows = 0
    with opened.text(MEMBER) as text:
        for row in opened.rows(text, COLUMNS):
            rows += 1
            if row[GEOGRAPHY] not in (LSOA, MSOA):
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
                higher=tuple(_count(opened, row[band]) for band in HIGHER),
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
    codes of 2021.
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
    """Every count of a row that is read, in one order: each higher band, and all homes."""
    return (*counted.higher, counted.homes)


def hold_the_rows(stock: Stock, found: Spine) -> int:
    """Stop unless the row of every area is what the rows of its LSOAs allow.

    Each count of an area's own row is held against the same count of its
    LSOAs, by the four rules of `rounded_counts`. It gives how many areas
    were held.
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
    """The areas whose counts of the higher bands come to more than all their homes.

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
    """The share of homes in the higher bands for every area, or why an area has no figure.

    Each count is the area's own, from the publisher's row for the MSOA the
    area is. An area with no count of all its homes has no figure. Nor has one
    whose homes of the higher bands are all behind a dash: they are not
    nought, and the file does not say how many they are.
    """
    rows = {
        area.area_id: stock.of_msoa[area.code] for area in found.areas if area.code in stock.of_msoa
    }
    counted = {area: one for area, one in rows.items() if one.homes}
    whole = over_the_whole(stock, found)
    share = area_row_ratio(
        {
            area: float(one.homes or 0) if area in whole else float(one.in_the_bands)
            for area, one in counted.items()
            if one.in_the_bands or not one.withheld
        },
        {area: float(one.homes or 0) for area, one in counted.items()},
        found.weights,
        times=WHOLE,
        withheld=[area for area, one in rows.items() if one.withheld or one.homes is None],
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
            first=FROM,
            last=TO,
            publisher=PUBLISHER,
            as_at=stock.as_at,
            rounded=ROUNDED_TO,
            hidden=MOST_HIDDEN,
            whole=WHOLE,
            places=DECIMALS,
            valued=VALUED_IN,
        ),
    )


def build(inputs: Inputs, found: Spine) -> Banded:
    """The share of homes in the higher bands for every area, from the files of the build.

    The gate is asked about the table before it is read. `found` is the spine
    of the same build. A row of evidence names the table and the lookup, which
    says which MSOA an area is.
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
    return Banded(
        worked=worked,
        rows=rows,
        metric=metric_of(files, stock),
        files=files,
        stock=stock,
        geography=geography,
        rows_held=held,
        at_the_whole=over_the_whole(stock, found),
    )
