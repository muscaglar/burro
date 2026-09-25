"""What homes sold for, worked out from the sales: the median of each kind of home in each area.

HM Land Registry publishes every sale of a home in England and Wales that was
lodged with it, a file for each year: the price, the day, the postcode, and
the kind of home. This module counts the sales of each kind of home in each
area of London, over every year the build was given, and takes the median of
what was paid. So a flat is priced apart from a house, a figure says how many
sales it rests on, and a budget for a flat is held against flats.

A release carries it as a cost: a price to buy, for each kind of home the
contract names. It is one number and no range, and the row says how many
sales stand behind it and from which month to which.

**What the licence registry asks of the file, and what is done here.**

| The registry says | So here |
|---|---|
| An address is not under the open licence | No line of one is read: `NEVER_READ` |
| Keep the postcode only to put a sale in an area | It is looked up once, and let go: `placed` |
| No row of a sale or of a postcode leaves the pipeline | A median and a count leave it |
| A row of a sale is of one home, and is personal data | No figure rests on under `FEWEST` sales |
| Do not suggest HM Land Registry endorses Burro | No word here does |

**What is read of a sale.** Six columns, by their place, because the file has
no row of names: the price, the day, the postcode, the kind of home, whether
the home was newly built, and whether the sale is a standard one.

| Column | It is read as |
|---|---|
| The price | Whole pounds, above nought |
| The day | The day the sale was completed. It must be a day of the year the file is of |
| The postcode | Where the sale is. It is looked up, and is kept nowhere |
| The kind of home | `D` detached, `S` semi-detached, `T` terraced, `F` a flat, `O` other |
| Newly built | `Y` or `N`. It is counted, and changes no figure |
| The category | `A` a standard sale, `B` an additional one |

**What is never read.** The number of a sale, the name and number of a
building, the flat within it, the street, the locality, the town, the
district and the county, whether the home is freehold or leasehold, and the
status of the record. A row that is handed on holds the six columns and no
other, and a test plants a canary in each of the rest.

**Which sales count.** A standard sale of a detached, a semi-detached or a
terraced house, or of a flat or a maisonette. The publisher calls a sale
standard where a home was sold at its full market value to a private person.
An additional sale is a repossession, a buy-to-let, or a transfer to a
company, and is not counted: the statistics office counts the standard sales
alone in its own medians, which this was held against. A sale of any other
kind of property is not counted: it is no kind of home a budget names.

**Where a sale is put.** In the area of the census output area that the
postcode directory gives for its postcode. A postcode that has ended is put
where it last stood. A sale whose postcode is no row of London in the
directory is put nowhere: most are outside London, and the lookup holds
London alone. A sale with no postcode is put nowhere either.

**The figure.** The median of what was paid, over every sale that counts. With
an even number of sales it is the mean of the two in the middle, given to the
pound with a half taken upward. Where fewer than `FEWEST` sales were made, no
figure is given, and the row of evidence says how many there were. Nothing is
filled in: not from a neighbour, not from a borough, and not from another
kind of home.

What it cannot see is in `CANNOT_SEE`. It gives no price by bedrooms: the file
holds none.
"""

import csv
import re
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from burro_core.facts import cost_key, fact_id
from burro_core.ids import FactKind, Segment, Tenure
from burro_core.release import FEWEST_SALES, CostEstimate, confidence_of

from burro_pipeline.cells import postcodes, spine
from burro_pipeline.cells.postcodes import Lookup
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.methods import Worked, row_of, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow, State
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "hmlr-price-paid"
PUBLISHER = "HM Land Registry"
# What the gate is asked before a file is read: a cost of a release is ranked on.
USE = Use.SCORING
# The publisher's name for the file of a year.
A_FILE = re.compile(r"pp-(?P<year>[0-9]{4})\.csv")
# How many columns a line holds, and the place of each that is read, counted from 1. The
# file has no row of names.
WIDTH = 16
PRICE, DAY, POSTCODE, HOME, NEW, CATEGORY = 2, 3, 4, 5, 6, 15
READ: Mapping[str, int] = {
    "price": PRICE,
    "day": DAY,
    "postcode": POSTCODE,
    "home": HOME,
    "new": NEW,
    "category": CATEGORY,
}
# The columns that are never read, by their place: the number of a sale, whether the home is
# freehold or leasehold, every line of the address, and the status of the record.
NEVER_READ: Mapping[str, tuple[int, ...]] = {
    "sale": (1,),
    "tenure": (7,),
    "address": (8, 9, 10, 11, 12, 13, 14),
    "record": (16,),
}
# The kinds of property the file names. Four are kinds of home a budget names.
KINDS: Mapping[str, Segment | None] = {
    "D": Segment.DETACHED,
    "S": Segment.SEMI_DETACHED,
    "T": Segment.TERRACED,
    "F": Segment.FLAT,
    "O": None,
}
NEWLY_BUILT, NOT_NEW = "Y", "N"
STANDARD, ADDITIONAL = "A", "B"
A_PRICE = re.compile(r"[1-9][0-9]{0,11}")
A_DAY = re.compile(r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2}) 00:00")
# The fewest sales a figure may rest on. It is core's, so that a release holds no figure
# that rests on fewer.
FEWEST = FEWEST_SALES
# What the rows of a file are keyed by.
KEYED_BY = Geography.POSTCODE

# The arithmetic: what a methods page prints beside the figure.
MEDIAN_OF_SALES = Method(
    derivation_id="median_of_sales_by_postcode@1",
    sentence="The median of what was paid in the standard sales of homes of one kind, each "
    "sale put in the area of the census output area that the postcode directory gives for its "
    "postcode, taken as the mean of the two middle prices where the sales are even in number "
    "and given to the pound with a half taken upward, and not given where fewer than 10 such "
    "sales were made in the area.",
    kind=Kind.MEASURED,
    parameters={"fewest_sales": FEWEST},
    code="burro_pipeline.derive.price_paid",
)
METHODS: tuple[Method, ...] = (MEDIAN_OF_SALES,)
# What the figure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The median price paid for {a_home} in the standard sales that {publisher} records in the "
    "area from {since} to {until}, in pounds: a sale is put in the area of the census output "
    "area that the postcode directory gives for its postcode; an additional sale, which is a "
    "repossession, a buy-to-let or a transfer to a company, is not counted; where fewer than "
    "{fewest} sales were made no figure is given; so it is the middle of what was paid for the "
    "homes that were sold, of every size, and is not the value of a home that was not sold, "
    "an asking price, a rent or the price of a home of any one size."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is the middle price of the homes of one kind, of all sizes, that were sold. It "
    "cannot see the homes that were not sold.",
    "It cannot tell a large home from a small one, so an area where large homes were sold "
    "reads dearer than one where small homes were. It is not an asking price or a rent.",
    "A sale is put where its postcode is, so a home at the edge of an area may be counted "
    "next door. A sale that was lodged late is not in it yet.",
)
A_HOME: Mapping[Segment, str] = {
    Segment.DETACHED: "a detached house",
    Segment.SEMI_DETACHED: "a semi-detached house",
    Segment.TERRACED: "a terraced house",
    Segment.FLAT: "a flat or a maisonette",
}
# The kinds of home a release carries a price for, in the order a release keeps them.
HOMES: tuple[Segment, ...] = (
    Segment.FLAT,
    Segment.TERRACED,
    Segment.SEMI_DETACHED,
    Segment.DETACHED,
)


@dataclass(frozen=True)
class Sale:
    """What is kept of one sale while it is placed. It holds no line of an address."""

    price: int
    home: Segment
    newly_built: bool
    # As the file writes it. It is looked up once, and is kept nowhere after that.
    postcode: str

    def __repr__(self) -> str:
        """Nothing of the sale, so that a line that prints one prints no postcode."""
        return "Sale()"


@dataclass(frozen=True)
class Counts:
    """What was read, as counts. Nothing here is held to a number: a test on the real files is."""

    # Every line of every file, and the lines of each file by the year it is of.
    rows: int
    by_year: Mapping[int, int]
    # The sales that are no standard sale, and the standard sales of no kind of home.
    additional: int
    of_no_kind_of_home: int
    # The standard sales of a kind of home: those that were put in an area, and those whose
    # postcode is no row of London or is none.
    placed: int
    not_placed: int
    # Of the sales that were placed: by the kind of home, those of a home newly built, and
    # those at a postcode that has ended.
    by_home: Mapping[Segment, int]
    newly_built: Mapping[Segment, int]
    at_an_ended_postcode: int


@dataclass(frozen=True)
class Priced:
    """The median of one kind of home for every area, with what stands behind each."""

    home: Segment
    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # How many sales stand behind the figure of each area that has one.
    sales: Mapping[str, int]
    definition: str


@dataclass(frozen=True)
class Sold:
    """The median of every kind of home for every area, from the files of the build."""

    of: Mapping[Segment, Priced]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    # The first month and the last of the sales, as `2023-01`.
    since: str
    until: str
    counts: Counts
    # What the rows a figure is read from are keyed by.
    geography: Geography


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this step reads."""
    return A_FILE.fullmatch(name) is not None


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _year_of(opened: Opened) -> int:
    """The year a file is of, from its name. Its receipt must give the whole of that year."""
    named = A_FILE.fullmatch(opened.receipt.publisher_file)
    if named is None:
        raise _refused(opened, "it is not named as a file of a year is")
    year = int(named["year"])
    if opened.receipt.data_period.days() != (f"{year}-01-01", f"{year}-12-31"):
        raise _refused(opened, "it is not of the year its receipt gives")
    return year


def _day(opened: Opened, cell: str, year: int) -> date:
    """The day of a sale. It stops at a cell that is no day, or is a day of another year."""
    found = A_DAY.fullmatch(cell)
    if found is None:
        raise _refused(opened, "a day is not a day")
    try:
        day = date(int(found["year"]), int(found["month"]), int(found["day"]))
    except ValueError:
        raise _refused(opened, "a day is not a day") from None
    if day.year != year:
        raise _refused(opened, "a sale is of another year than its file")
    return day


def _cells(opened: Opened) -> Iterator[dict[str, str]]:
    """The rows of a file, each with the six columns that are read and no other."""
    with opened.text() as text:
        try:
            for line in csv.reader(text):
                if len(line) != WIDTH:
                    raise _refused(opened, "a line has not the columns of the file")
                yield {name: line[place - 1] for name, place in READ.items()}
        except csv.Error:
            raise _refused(opened, "a row is broken") from None


def sales_of(opened: Opened, counted: Counter[str]) -> Iterator[Sale]:
    """The standard sales of a kind of home in one file, each held to what a sale can be.

    It stops at a line that is not as wide as the file, at a price that is no
    price, a day that is no day of the file's year, and a kind, a mark or a
    category the file is not known to hold. `counted` is told of every line.
    """
    year = _year_of(opened)
    for row in _cells(opened):
        counted["rows"] += 1
        counted[f"year {year}"] += 1
        if not A_PRICE.fullmatch(row["price"]):
            raise _refused(opened, "a price is not a price")
        _day(opened, row["day"], year)
        if row["home"] not in KINDS:
            raise _refused(opened, "a kind of home is none the file is known to hold")
        if row["new"] not in (NEWLY_BUILT, NOT_NEW):
            raise _refused(opened, "a mark of a new home is none the file is known to hold")
        if row["category"] not in (STANDARD, ADDITIONAL):
            raise _refused(opened, "a category is none the file is known to hold")
        if row["category"] != STANDARD:
            counted["additional"] += 1
            continue
        home = KINDS[row["home"]]
        if home is None:
            counted["of no kind of home"] += 1
            continue
        yield Sale(int(row["price"]), home, row["new"] == NEWLY_BUILT, row["postcode"])


def placed(
    sales: Iterator[Sale], lookup: Lookup, found: Spine, counted: Counter[str]
) -> Iterator[tuple[str, Segment, int]]:
    """Each sale as the area it is in, its kind of home and its price, and nothing more.

    The postcode is looked up here and is let go: what is handed on holds
    none. A sale whose postcode is no row of London, or is none, or stands in
    no area of the build, is counted and handed on nowhere.
    """
    area_of = found.area_of
    for sale in sales:
        where = lookup.place(sale.postcode) if sale.postcode else None
        area = None if where is None else area_of.get(where.oa)
        if where is None or area is None:
            counted["not placed"] += 1
            continue
        counted["placed"] += 1
        counted[f"home {sale.home}"] += 1
        counted[f"new {sale.home}"] += sale.newly_built
        counted["ended"] += not where.in_use
        yield area, sale.home, sale.price


def median_of(prices: Sequence[int]) -> int:
    """The median of some prices, in whole pounds: a half is taken upward."""
    if not prices:
        raise ValueError("a median is of at least one price")
    ordered = sorted(prices)
    middle, odd = divmod(len(ordered), 2)
    if odd:
        return ordered[middle]
    return int(to_places((ordered[middle - 1] + ordered[middle]) / 2, 0))


def figure_of(prices: Sequence[int]) -> Worked:
    """The figure of one kind of home in one area, or why it has none.

    What stands behind it is counted in sales: how many were made, and of how
    many a figure needs where there are too few.
    """
    sold = len(prices)
    if sold == 0:
        return Worked(None, 0, 0, 0.0, State.SOURCE_GAP)
    if sold < FEWEST:
        return Worked(None, sold, FEWEST, sold / FEWEST, State.BELOW_THRESHOLD)
    return Worked(float(median_of(prices)), sold, sold, 1.0, State.PRESENT)


def _months(files: Sequence[Opened]) -> tuple[str, str]:
    """The first month and the last of the sales. The years of the files stand side by side."""
    years = sorted(_year_of(opened) for opened in files)
    if years != list(range(years[0], years[-1] + 1)):
        raise LockError(
            "input_is_as_described", SOURCE, "the files are not of years that follow one another"
        )
    return f"{years[0]}-01", f"{years[-1]}-12"


def _counts(counted: Counter[str]) -> Counts:
    years = {int(name.split()[1]): held for name, held in counted.items() if name[:5] == "year "}
    return Counts(
        rows=counted["rows"],
        by_year=dict(sorted(years.items())),
        additional=counted["additional"],
        of_no_kind_of_home=counted["of no kind of home"],
        placed=counted["placed"],
        not_placed=counted["not placed"],
        by_home={home: counted[f"home {home}"] for home in HOMES},
        newly_built={home: counted[f"new {home}"] for home in HOMES},
        at_an_ended_postcode=counted["ended"],
    )


def build(inputs: Inputs, found: Spine) -> Sold:
    """The median of every kind of home for every area, from the files of the build.

    The gate is asked about the files before one is read, for the use the
    registry gives them, and about the postcode directory. `found` is the
    spine of the same build. A row of evidence names every file of sales, the
    directory, which says where a postcode is, and the lookup, which says
    which area an output area is part of.
    """
    files = inputs.open_each(SOURCE, USE, named=is_a_file)
    since, until = _months(files)
    lookup = postcodes.build(inputs)
    counted: Counter[str] = Counter()
    paid: dict[tuple[str, Segment], list[int]] = {}
    for opened in files:
        for area, home, price in placed(sales_of(opened, counted), lookup, found, counted):
            paid.setdefault((area, home), []).append(price)

    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in found.inputs):
        raise ValueError("the spine is made from files of this build")
    of_the_spine = [
        file_id for file_id in found.inputs if handed[file_id].source_id == spine.LOOKUP
    ]
    named = {opened.file_id for opened in files} | {lookup.receipt.file_id, *of_the_spine}
    receipts = tuple(handed[file_id] for file_id in sorted(named))

    priced: dict[Segment, Priced] = {}
    for home in HOMES:
        worked = {
            area.area_id: figure_of(paid.get((area.area_id, home), ())) for area in found.areas
        }
        key = cost_key(Tenure.BUY, home)
        rows = tuple(
            row_of(fact_id(area, FactKind.COST, key), worked[area], MEDIAN_OF_SALES, receipts)
            for area in sorted(worked)
        )
        priced[home] = Priced(
            home=home,
            worked=worked,
            rows=rows,
            sales={area: one.units_used for area, one in worked.items() if one.value is not None},
            definition=DEFINITION.format(
                a_home=A_HOME[home],
                publisher=PUBLISHER,
                since=since,
                until=until,
                fewest=FEWEST,
            ),
        )
    return Sold(
        of=priced,
        files=receipts,
        since=since,
        until=until,
        counts=_counts(counted),
        geography=KEYED_BY,
    )


def costs(sold: Sold) -> tuple[CostEstimate, ...]:
    """The rows of `cost.json`: the median of each kind of home, in each area that has one.

    A row holds the median and no range, how many sales it rests on, and the
    first month and the last of those sales. An area with too few sales of a
    kind of home has no row, and its row of evidence says how many there
    were. The rows are in the order a release keeps them.
    """
    source_ids = tuple(sorted({receipt.source_id for receipt in sold.files}))
    rows = [
        CostEstimate(
            area_id=area_id,
            tenure=Tenure.BUY,
            segment=priced.home,
            lower_quartile=None,
            median=int(worked.value),
            upper_quartile=None,
            confidence=confidence_of(priced.sales[area_id]),
            as_of=sold.until,
            since=sold.since,
            sales=priced.sales[area_id],
            source_ids=source_ids,
        )
        for priced in sold.of.values()
        for area_id, worked in priced.worked.items()
        if worked.value is not None
    ]
    return tuple(sorted(rows, key=lambda row: (row.area_id, row.tenure, row.segment)))


def evidence(sold: Sold) -> tuple[EvidenceRow, ...]:
    """The rows of evidence of the costs: one for each area and kind of home, with or without
    a figure."""
    return tuple(row for priced in sold.of.values() for row in priced.rows)
