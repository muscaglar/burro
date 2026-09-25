"""How far what homes sold for has risen: over five years, and over ten.

`derive/price.py` reads the statistics office's workbook of median prices
paid, which holds a column for every year that ends with a quarter, from 1995.
This reads the first sheet of the same workbook, the median for a home of any
kind, for three of its years: the last, the one that ended five years before,
and the one that ended ten years before. Each figure is the publisher's own
for the middle layer super output area that an area of the build is.

The figure is the median of the last year for each £100 of the median of the
earlier year. So £112 says that the middle price rose by 12 in 100, and £97
that it fell by 3. It is never below nought, as a rise in per cent would be
where prices fell, and no sum is taken over areas: it is one figure of the
area's own row over another.

**A rise is of prices that were paid, and promises nothing.** It says what
homes sold for then and now. It says nothing of what a home will sell for, and
nothing of who lives in a place or is moving to it. A person may weigh it, and
no word applies it: it is offered for a word for a place on the rise, with
that sentence beside it.

What moves the figure that is no rise in what a home is worth:

- The median is of the homes that were sold in each year, of every kind and
  size. Where new flats were built, or large houses came to be sold, the
  middle price moves though no home is worth more or less.
- The publisher gives a figure from 5 sales up, and no count. A rise in an
  area where few homes sell moves more from year to year than one where many
  do.

Where the publisher gives no figure for either year, none is given here.

The workbook is opened through `derive/price.py`, which holds its cover and
its contents to what is read, and says what the registry allows of it.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import price
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked, row_of, to_places
from burro_pipeline.derive.noise_sheet import Value, read_sheet
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow, Flag, State
from burro_pipeline.inputs import Inputs, Opened

SOURCE = price.SOURCE
USE = price.USE
KEYED_BY = price.KEYED_BY
# The sheet that is read: the median for a home of any kind.
SHEET = price.ALL.sheet
# The measure of each span of years.
OVER: Mapping[int, FeatureId] = {5: FeatureId.PRICE_RISE_5Y, 10: FeatureId.PRICE_RISE_10Y}
IN_WORDS: Mapping[int, str] = {5: "five", 10: "ten"}
# What the later median is given for each of, in pounds of the earlier one.
FOR_EACH = 100
# A figure is given to this many decimal places.
DECIMALS = 1

# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The median price paid for a home sold in the area in the year ending {month} {year}, for "
    "each £{for_each} of the median price paid for a home sold there in the year ending "
    "{month} {before}, which was {years} years before: each median is the {publisher}'s own "
    "for the middle layer super output area the area is, in statistics it adapted from data of "
    "HM Land Registry, and is of homes of every kind and size; the figure is given to {places} "
    "decimal place, with a half taken upward; where the publisher gives no figure for either "
    "year none is given; so it says how far the middle of what was paid has moved, which moves "
    "too where other homes came to be sold, and it promises nothing of what a home will sell "
    "for."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "A rise is of prices that were paid, and promises nothing: it says what homes sold for "
    "then and now, and nothing of what one will sell for.",
    "It is the middle price of the homes that were sold in each year, of every kind and size, "
    "so it moves where other homes came to be sold, as where new flats were built, though no "
    "home is worth more.",
    "A middle price may rest on as few as 5 sales, so the figure moves more in an area where "
    "few homes sell. It says nothing of who lives in a place, or of who is moving to it.",
)


def risen_over(years: int) -> Method:
    """The record of the method for one span of years. The span is part of its id."""
    if years not in OVER:
        raise ValueError("a rise is worked out over five years, or over ten")
    return Method(
        derivation_id=f"area_row_rise_{years}y@1",
        sentence="The publisher's own figure for the area in the last year, for each 100 of "
        f"its own figure for the area in the year that ended {years} years before, each taken "
        "from the area's own row as it is written and never worked out from the rows of smaller "
        "or of larger areas, and not given where the row gives no figure for either year.",
        kind=Kind.MEASURED,
        parameters={"years": years, "for_each": FOR_EACH},
        code="burro_pipeline.derive.price_rise",
    )


METHODS: tuple[Method, ...] = (risen_over(5), risen_over(10))


@dataclass(frozen=True)
class Medians:
    """The median of each MSOA in the last year and in each earlier one, as the sheet has them."""

    # The median of each MSOA that has one, in pounds, by the years before the last: 0, 5, 10.
    paid: Mapping[int, Mapping[str, int]]
    # The MSOAs with a row and no figure for a year: the publisher withheld it.
    withheld: Mapping[int, frozenset[str]]
    # The local authority the sheet puts each MSOA in.
    district: Mapping[str, str]
    year: price.Year
    # The name of the column of each year, as the sheet writes it.
    columns: Mapping[int, str]
    file_id: str


@dataclass(frozen=True)
class Risen:
    """The figure of every area over one span of years, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography
    medians: Medians


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return price.is_the_workbook(name)


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _column(year: price.Year, before: int) -> str:
    """The name of the column of the year that ended so many years before the last."""
    return f"Year ending {year.month[:3]} {year.year - before}"


def _price_of(opened: Opened, cell: Value) -> int | None:
    """The median in a cell, in pounds, or none where the publisher withheld it."""
    if cell == price.WITHHELD:
        return None
    if not (isinstance(cell, float) and cell.is_integer() and cell > 0):
        raise _refused(opened, "a price is not a price")
    return int(cell)


def read(opened: Opened) -> Medians:
    """What the sheet of all homes holds for the last year, and five and ten years before.

    The cover and the contents are read first, as `derive/price.py` reads
    them. It stops at a column that is missing, a code that is no code, an
    MSOA that is there twice, and a cell that is neither a price nor `[x]`.

    A build asks for it once for each span of years. A copy was held to the
    hash in its receipt when it was handed over, so the copy of one receipt in
    one place is read once.
    """
    return _read(opened)


@lru_cache(maxsize=2)
def _read(opened: Opened) -> Medians:
    year = price.year_of(opened)
    price.hold_the_cover(opened)
    price.hold_the_contents(opened, year)
    columns = {before: _column(year, before) for before in (0, *OVER)}
    named = (price.DISTRICT_CODE, price.MSOA_CODE, *columns.values())
    rows = read_sheet(opened, SHEET, named, header_at=price.HEADER_AT)
    found: dict[int, dict[str, int]] = {before: {} for before in columns}
    withheld: dict[int, set[str]] = {before: set() for before in columns}
    district: dict[str, str] = {}
    for row in rows:
        code, within = row[price.MSOA_CODE], row[price.DISTRICT_CODE]
        if not (isinstance(code, str) and price.AN_MSOA.fullmatch(code)):
            raise _refused(opened, "a code is not a code")
        if not (isinstance(within, str) and price.A_DISTRICT.fullmatch(within)):
            raise _refused(opened, "a code is not a code")
        if code in district:
            raise _refused(opened, "an MSOA is there twice")
        district[code] = within
        for before, column in columns.items():
            paid = _price_of(opened, row[column])
            if paid is None:
                withheld[before].add(code)
            else:
                found[before][code] = paid
    if not rows:
        raise _refused(opened, "it holds no row of an MSOA")
    return Medians(
        paid=found,
        withheld={before: frozenset(codes) for before, codes in withheld.items()},
        district=district,
        year=year,
        columns=columns,
        file_id=opened.file_id,
    )


def keyed_by(medians: Medians, found: Spine) -> Geography:
    """What the rows are keyed by. It stops if that is not the MSOAs of the census of 2021."""
    if any(area.code not in medians.district for area in found.areas):
        raise LockError(
            "input_is_as_described", medians.file_id, "an MSOA of the census of 2021 has no row"
        )
    if any(medians.district[area.code] != area.borough_code for area in found.areas):
        raise LockError(
            "input_is_as_described",
            medians.file_id,
            "an MSOA is in another borough than the lookup gives",
        )
    return KEYED_BY


def figures(medians: Medians, found: Spine, years: int) -> dict[str, Worked]:
    """The figure of every area over a span of years, or why an area has no figure.

    It is the median of the last year for each £100 of the median of the
    earlier year. Nothing stands in for a figure the publisher withheld of
    either year.
    """
    now, then = medians.paid[0], medians.paid[years]
    hidden = medians.withheld[0] | medians.withheld[years]
    worked: dict[str, Worked] = {}
    for area in found.areas:
        if area.code in now and area.code in then:
            value = to_places(FOR_EACH * now[area.code] / then[area.code], DECIMALS)
            worked[area.area_id] = Worked(value, 1, 1, 1.0, State.PRESENT)
        elif area.code in hidden:
            marked = (Flag.SUPPRESSED_IN_SOURCE,)
            worked[area.area_id] = Worked(None, 0, 1, 0.0, State.SUPPRESSED, marked)
        else:
            worked[area.area_id] = Worked(None, 0, 1, 0.0, State.SOURCE_GAP)
    return worked


def metric_of(files: Sequence[Receipt], medians: Medians, years: int) -> Metric:
    """The row of the catalogue: the name, the period and every source.

    Core decides the name, the unit and which way is more. The period runs
    from the first month of the earlier year to the last month of the last.
    """
    year = medians.year
    start = f"{int(str(year.period.start)[:4]) - years}{str(year.period.start)[4:]}"
    return catalogue_row(
        OVER[years],
        method=risen_over(years),
        source_ids={receipt.source_id for receipt in files},
        vintage=f"{start} to {year.period.end}",
        definition=DEFINITION.format(
            month=year.month,
            year=year.year,
            before=year.year - years,
            years=IN_WORDS[years],
            for_each=FOR_EACH,
            publisher=price.PUBLISHER,
            places=DECIMALS,
        ),
    )


def build(inputs: Inputs, found: Spine, years: int) -> Risen:
    """How far what homes sold for has risen over a span of years, for every area.

    The gate is asked about the workbook before it is read. `found` is the
    spine of the same build. A row of evidence names the workbook and the
    lookup, which says which MSOA an area is.
    """
    opened = inputs.open(SOURCE, USE, named=is_a_file)
    medians = read(opened)
    geography = keyed_by(medians, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in found.inputs):
        raise ValueError("the spine is made from files of this build")
    lookup = [file_id for file_id in found.inputs if handed[file_id].source_id == spine.LOOKUP]
    files = tuple(handed[file_id] for file_id in sorted({opened.file_id, *lookup}))
    worked = figures(medians, found, years)
    method = risen_over(years)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, OVER[years]), worked[area], method, files)
        for area in sorted(worked)
    )
    return Risen(
        worked=worked,
        rows=rows,
        metric=metric_of(files, medians, years),
        files=files,
        geography=geography,
        medians=medians,
    )
