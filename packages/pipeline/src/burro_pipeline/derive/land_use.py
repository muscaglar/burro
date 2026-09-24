"""Land use: five shares of an area's land, from the land use statistics for England.

The Department for Levelling Up, Housing and Communities publishes how much
land of each LSOA is in each of 28 categories, in its Live Table P405. The
figures are its publisher's estimates, from data Ordnance Survey makes of its
own products. Five measures are read from the one table, each from one
category:

| Measure | Category | What the technical notes say it holds |
|---|---|---|
| `land_industry` | Industry (I) | Works, refineries, shipyards, mills, other industrial sites |
| `land_storage` | Storage and warehousing (S) | Depots, scrap and timber yards, warehousing |
| `land_transport_other` | Transport (other) (T) | Railways, airports and dockland |
| `land_gardens` | Residential gardens (RG) | Residential gardens, whatever their surface |
| `land_woodland` | Forestry and woodland (F) | Areas the map marks as woodland |

A measure is made from a category and never from a group. The group the
publisher calls industry and commerce holds offices and shops beside industry
and storage, and the group it calls transport and utilities holds roads.

**What the workbook holds was read with the step `describe`, which gives the
words of a sheet and never a row that holds a number.** No figure of it was
read to write this. So each claim below says where it rests:

| What | Where it is from |
|---|---|
| The 28 categories, their codes, their groups and what each holds | The technical notes |
| That the figures are estimates | The technical notes |
| The two sheets, and that one is in per cent and one in hectares | The workbook: row 3 of each |
| The three rows that name the columns, and how each column is spelt | The workbook: rows 4 to 6 |
| That a group of one category has one column, called a total | The workbook: rows 5 and 6 |
| That the rows are of the LSOAs of 2021 | The workbook: the first note under the table |
| That the grand total is all the categories added up | The workbook: the second note |
| The year, 2022 | The workbook: the title of each sheet, in row 1 |
| What a dash stands for | Nowhere. It is held to the arithmetic of its own row |

The workbook holds no cover and no sheet of notes. It states no month, no
licence and no rights.

Five of the 13 groups hold one category: defence buildings, outdoor
recreation, residential gardens, undeveloped land and vacant land. The
workbook gives each of them one column, which its row of names calls a total
and the row above names for the group. So the column of residential gardens
is the total of a group of one, and is still one category: `OVER` names the
five, and no group of more than one category is ever read.

How a figure is made:

1. The land of an LSOA in a category is read as the publisher wrote it, in
   hectares, and kept to four decimal places, which is a square metre. The
   table writes a figure to 13 places and more, and some are far less than a
   square metre, so one share in some thousands moves by a tenth. All the land
   of an LSOA is its 28 categories added up. The publisher's own grand total
   is read to hold that sum to, and is part of no figure.
2. An area's figure is the land of the category in its LSOAs, over all the
   land of its LSOAs, as a percentage: `lsoa_ratio_by_homes`, one sum over
   another and never a mean of shares. An LSOA that lies in two areas is
   shared out by where its homes are.
3. It is given to one decimal place, with a half taken upward.

It is a share of the area's land. The design of the vibes asked for a mean of
the shares of an area's LSOAs, weighted by their homes. That is another
figure: it counts a works among homes for more than a works where nobody
lives. Core names each measure as land and says it is measured, so the share
of land is what is built, as green cover is. Which of the two a recipe should
rest on is for whoever owns the recipe.

Nothing is filled in. An LSOA with an empty cell in any of the 28 categories
has no total, so it adds nothing to any measure, and the area's coverage falls
by its homes. An empty cell is never nought. A cell that holds any other text
than a dash stops the step.

A dash stands in some cells where a figure would. Neither the workbook nor any
page says what it stands for. It is read as none of that land, and only where
the row proves it: the workbook says its grand total is all the categories
added up, so where the figures of a row add up to its grand total with every
dash taken as nought, no dash of that row can hide any land. A row that does
not add up stops the step. What rounding allows is worked out from the places
the sheet gives its figures to: `held_to_its_total` has the rule.

The rows of larger areas are not read. The workbook holds a row for England
and for each region above the rows of the LSOAs, and no row for an MSOA: it
gives the MSOA of each LSOA in a column of its row.

Is it a measure of a place? It is. It says what the land is used for, as a map
classes it, and nothing of who lives on it or near it. Three of the 28 categories
do say who lives on the land, and none of them is ever a measure:
`SAYS_WHO_LIVES_THERE` names them, and `measures_of` refuses one.
"""

import math
import re
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from types import MappingProxyType
from typing import Protocol

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells.land import Land, kept
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.land_use_sheet import Table, Value, read_table
from burro_pipeline.derive.methods import (
    LSOA_RATIO_BY_HOMES,
    Worked,
    lsoa_ratio_by_homes,
    lsoa_value_by_homes,
    row_of,
    to_places,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "mhclg-land-use-statistics-2022"
EDITION = "2022"
PUBLISHER = "Department for Levelling Up, Housing and Communities"
# The publisher's name for the file starts so. The national tables of the same edition are
# named the same up to the year, and hold no LSOA.
FILE_STARTS = "Live_Tables_-_Land_Use_Stock_2022_-_LSOA"
# The shape of the code of an LSOA of England. London's are all of England.
AN_LSOA = re.compile(r"E01[0-9]{6}")
# What the rows are keyed by, once the table is held to the spine. No page says it.
KEYED_BY = Geography.LSOA21
# A share is given as a percentage, to this many decimal places. The figures are estimates,
# so a second place would say nothing.
TIMES = 100
DECIMALS = 1
# The totals of the table are the hectares of its LSOAs where the middle one is between half
# and twice the land the build measures. The outline the build measures is generalised, so
# the two differ a little. A table in another unit differs far more: by 2.5 times in acres,
# and by a hundred times and more in any other. The two numbers are a choice and no finding.
LEAST, MOST = 0.5, 2.0
# A row whose categories add up to this, give or take so much, is a row of shares.
ALL_OF_IT, GIVE_OR_TAKE = 100.0, 0.5
# What the workbook writes in some cells where a figure would stand. It says nowhere what
# it stands for, so it is read as none of that land only where the row adds up without it.
DASH = "-"
# The name the step asks for the publisher's own total of a row by. It is no category.
ALL = "all"
# How the sheet of hectares says its unit, alone in a cell above the names of its columns.
UNIT = ("Hectares",)
# What the row of names calls the one column of a group.
TOTAL = "Total"
# A figure is taken to be given to this many decimal places at most, and a sum of figures
# to be out by this little whatever they are given to: a hundredth of a square metre.
MOST_PLACES, LEAST_GIVE = 9, 1e-6


@dataclass(frozen=True)
class Category:
    """One of the 28 categories of land, as the technical notes give it."""

    code: str
    # Its name in the table of groups and categories, which the release repeats.
    name: str
    group: str
    # Every way the publisher's two documents write it: its name, the heading of its
    # definition where that differs, each of them with its code after it, and its code alone.
    # Then the way the workbook writes it in its row of names, where that is another.
    spelt: tuple[str, ...]
    # The way the workbook names it over a column its row of names calls a total. Only a
    # group of one category is named so.
    over: tuple[str, ...] = ()


def _category(code: str, name: str, group: str, *also: str, over: str = "") -> Category:
    named = (name, *also)
    spelt = (*named, *(f"{one} ({code})" for one in named), code)
    return Category(code, name, group, spelt, (over,) if over else ())


_COMMUNITY, _COMMERCE = "Community services", "Industry and commerce"
_MINERALS, _OTHER = "Minerals and landfill", "Other developed use"
_TRANSPORT, _FORESTRY = "Transport and utilities", "Forestry, open land and water"

# In the order of the technical notes: developed land, land that is not developed, vacant land.
CATEGORIES: tuple[Category, ...] = (
    _category("C", "Community buildings", _COMMUNITY),
    _category("L", "Leisure (indoor)", _COMMUNITY, "Leisure and recreational buildings"),
    _category("D", "Defence buildings", "Defence buildings", over="Defence"),
    _category("I", "Industry", _COMMERCE),
    _category("J", "Offices", _COMMERCE),
    _category("K", "Retail", _COMMERCE, "Retailing"),
    _category("S", "Storage and warehousing", _COMMERCE),
    _category("M", "Minerals and mining", _MINERALS, "Minerals"),
    _category("Y", "Landfill and waste disposal", _MINERALS, "Landfill waste disposal"),
    _category("~B", "Unidentified building", _OTHER),
    _category(
        "~M",
        "Unidentified general manmade surface",
        _OTHER,
        "Unidentified general manmade surface (not roadside)",
    ),
    _category("~S", "Unidentified structure", _OTHER),
    _category(
        "~U",
        "Unknown surface type with no classification",
        _OTHER,
        "Unknown surface type",
        # As the workbook writes it.
        "Unknown",
    ),
    _category(
        "Q",
        "Communal accommodation",
        "Residential",
        "Institutional and communal accommodation",
        # As the workbook writes it, with the hyphen.
        "Institutional and communal accommo-dations",
    ),
    _category("R", "Residential", "Residential"),
    _category("H", "Highways and roads", _TRANSPORT, "Highways and road transport"),
    _category("T", "Transport (other)", _TRANSPORT),
    _category("U", "Utilities", _TRANSPORT),
    _category("A", "Agricultural land", "Agriculture"),
    _category("B", "Agricultural buildings", "Agriculture"),
    _category("F", "Forestry and woodland", _FORESTRY, "Forestry/Woodland"),
    _category("G", "Rough grassland", _FORESTRY, "Rough grassland and bracken"),
    _category("N", "Natural land", _FORESTRY, "Natural and semi-natural land"),
    _category("W", "Water", _FORESTRY),
    _category("O", "Outdoor recreation", "Outdoor recreation", over="Outdoor recreation"),
    _category("RG", "Residential gardens", "Residential gardens", over="Residential gardens"),
    _category(
        "X",
        "Undeveloped land",
        "Undeveloped land",
        "Urban land not previously developed",
        over="Undeveloped land",
    ),
    _category("V", "Vacant land", "Vacant land", "Vacant land previously developed", over="Vacant"),
)
# The columns that are read, each by the code of its category, with the ways it is spelt.
# The last is the publisher's own total of a row, which every row is held to.
COLUMNS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {category.code: category.spelt for category in CATEGORIES} | {ALL: ("Grand total",)}
)
# The columns the workbook names over a total: the five groups of one category, and the
# grand total. A group of more than one category is never named here.
OVER: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {category.code: category.over for category in CATEGORIES if category.over}
    | {ALL: ("Grand Total",)}
)

# The arithmetic: what a methods page prints beside each measure.
METHODS: tuple[Method, ...] = (LSOA_RATIO_BY_HOMES,)
# What each measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Land that Ordnance Survey's land use data classes as {category}, which the technical notes "
    "of the land use statistics for England give as {holds}, as the {publisher} publishes it in "
    "hectares for each small census area as at {as_at}, each figure kept to the square metre, "
    "over all the land of the same small census areas, which is the {classes} classes of the "
    "same table added up, each sum taken over the small census areas the area takes in, times "
    "{times} and given to {decimals} decimal place with a half taken upward, so it is a share "
    "of the area's land, which its publisher calls an estimate, and it says nothing of who "
    "lives there, of how near a home stands to the land, or of what the land has become since "
    "it was mapped."
)
_OF_ALL = "It is a share of all the land of the area, so it cannot tell"


@dataclass(frozen=True)
class Of:
    """One measure: the category it is read from, and what is said of it."""

    feature: FeatureId
    # The code of the one category it is made from.
    category: str
    # What a person reads beside the figure. It is core's, so a build carries the measure.
    label: str
    # What the category holds, in the words of its definition in the technical notes.
    holds: str
    # What the product shows beside the figure.
    cannot_see: tuple[str, str]
    # What keeps the measure out of a release, and whose it is to settle. None waits.
    waits_on: tuple[str, ...] = ()


_MEASURES = (
    Of(
        FeatureId.LAND_INDUSTRY,
        "I",
        "Land used for industry",
        "works, refineries, shipbuilding yards, mills and other industrial sites, but for those "
        "of a public utility",
        (
            "This is land mapped as works, mills and other industrial sites, so it cannot see "
            "what is made there, whether a site is still at work, or how it looks or sounds "
            "from the street.",
            f"{_OF_ALL} a works beside homes from one far from any home, and it leaves out gas, "
            "water and power works, which are mapped as utilities.",
        ),
    ),
    Of(
        FeatureId.LAND_STORAGE,
        "S",
        "Land used for storage and warehousing",
        "depots, scrap and timber yards, warehousing and the like",
        (
            "This is land mapped as depots, yards and warehouses, so it cannot see what is "
            "kept there, how much comes and goes, or whether a building has been put to "
            "another use since it was mapped.",
            f"{_OF_ALL} a warehouse beside homes from one far from any home, and it leaves out "
            "a warehouse inside a dock or a railway yard, which is mapped with them.",
        ),
    ),
    Of(
        FeatureId.LAND_TRANSPORT_OTHER,
        "T",
        "Land used for transport other than roads, such as railways, airports and docks",
        "transport routes and places that are no highway, such as railways, airports and "
        "dockland, with every installation inside their perimeter",
        (
            "This is land mapped as railways, airports, docks and the like, with all that "
            "stands inside their bounds, so it cannot see how many trains or planes pass, or "
            "how loud they are.",
            f"{_OF_ALL} a railway at the end of a garden from one far from any home, and it "
            "counts no road, bus station, public car park, canal or river.",
        ),
    ),
    Of(
        FeatureId.LAND_GARDENS,
        "RG",
        "Land that is residential garden",
        "residential gardens of any type, whatever their surface",
        (
            "This is land mapped as the garden of a home, whatever its surface, so it cannot "
            "tell a lawn from a paved yard, and it cannot see whether any one home has a garden.",
            f"{_OF_ALL} many small gardens from a few large ones, or say how many homes share one.",
        ),
    ),
    Of(
        FeatureId.LAND_WOODLAND,
        "F",
        "Land that is woodland",
        "areas marked as woodland on the Ordnance Survey map, with woodland on farms and "
        "woodland used for recreation",
        (
            "This is land the map marks as woodland, so it counts no tree that stands outside "
            "such land, as in a street or a garden, and it cannot see what has been planted or "
            "felled since.",
            f"{_OF_ALL} a wood that is open to walk in from one that is fenced, or say how "
            "near a home stands to it.",
        ),
    ),
)
# The categories that say something of who lives on the land, as the technical notes give
# them: communal accommodation is hostels, old people's homes, children's homes, monasteries
# and convents, community buildings hold religious buildings and prisons, and defence
# buildings hold barracks. Each is read, because all the land of an LSOA is its 28 categories
# added up. None is ever a measure: a place is ranked, and never who lives in it.
SAYS_WHO_LIVES_THERE = frozenset({"Q", "C", "D"})


def measures_of(*given: Of) -> Mapping[FeatureId, Of]:
    """The measures, each held to one category that says nothing of who lives on the land."""
    codes = {category.code for category in CATEGORIES}
    for of in given:
        if of.category not in codes:
            raise ValueError(f"the category of {of.feature} is no category of the table")
        if of.category in SAYS_WHO_LIVES_THERE:
            raise ValueError(f"the category of {of.feature} says who lives on the land")
    return MappingProxyType({of.feature: of for of in given})


MEASURES: Mapping[FeatureId, Of] = measures_of(*_MEASURES)


@dataclass(frozen=True)
class Sheet:
    """What the table holds of land: the hectares of every LSOA in every category."""

    # The hectares of each LSOA that has all 28, by the code of the category.
    hectares: Mapping[str, Mapping[str, float]]
    # All the land of each such LSOA: its 28 categories added up.
    total: Mapping[str, float]
    # The LSOAs with a row and an empty cell. Nothing stands in for one.
    without: tuple[str, ...]
    # The rows that hold the code of an LSOA, for all of England.
    rows: int
    # The rows under the names of the columns that hold none: of a larger area, of notes.
    others: int
    # The row that names the columns, as the sheet numbers its rows.
    header_at: int
    file_id: str
    # The middle of the totals over the land the build measures, once held to it.
    to_the_land: float | None = None
    # The cells that hold a dash and were read as none of that land, in the LSOAs above.
    dashes: int = 0
    # The decimal places the sheet gives its figures to, as the most any figure holds.
    places: int = 0


@dataclass(frozen=True)
class LandUse:
    """One measure: the figure of every area, in percent, with what stands behind each."""

    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    sheet: Sheet
    geography: Geography


def is_the_table(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the table by LSOA."""
    return name.startswith(FILE_STARTS)


def _refused(file_id: str, words: str) -> LockError:
    return LockError("input_is_as_described", file_id, words)


def _hectares(opened: Opened, held: Value) -> float | None:
    """The land a cell holds. A dash is nought here, and the row is then held to its total."""
    if held is None:
        return None
    if held == DASH:
        return 0.0
    if not isinstance(held, float):
        raise _refused(opened.file_id, "an area of land is not a number")
    if held < 0:
        raise _refused(opened.file_id, "an area of land is below nothing")
    return kept(held)


def places_of(figure: float) -> int:
    """The decimal places a figure is written to, as the shortest way to write it has them."""
    exponent = Decimal(repr(figure)).normalize().as_tuple().exponent
    return min(MOST_PLACES, max(0, -exponent)) if isinstance(exponent, int) else 0


def held_to_its_total(opened: Opened, found: Mapping[str, float], places: int) -> float:
    """All the land of a row: its categories added up, once held to the publisher's own total.

    The workbook says its grand total is all the categories added up. So a row
    whose figures add up to its grand total, with every dash taken as nought,
    hides no land behind a dash. A figure given to so many places is out by
    half a unit of the last place at most, so a row of figures may be out by
    that for each figure and for the total.
    """
    total = kept(math.fsum(found[code] for code in sorted(found) if code != ALL))
    give = max(LEAST_GIVE, len(found) * 0.5 * 10.0**-places)
    if abs(total - found[ALL]) > give:
        raise _refused(opened.file_id, "a row does not add up to its total")
    return total


def sheet_of(opened: Opened, table: Table) -> Sheet:
    """The hectares of every LSOA, from the rows of the table, each held to what land can be.

    It stops at a cell that holds text other than a dash, at land below
    nothing, at an LSOA that is there twice, at a row that does not add up to
    its own total, and at an LSOA whose land adds up to none.
    """
    hectares: dict[str, dict[str, float]] = {}
    without: set[str] = set()
    dashes = 0
    for row in table.rows:
        if row.code in hectares or row.code in without:
            raise _refused(opened.file_id, "an LSOA is there twice")
        found = {code: _hectares(opened, held) for code, held in row.held.items()}
        whole = {code: land for code, land in found.items() if land is not None}
        if len(whole) < len(found):
            without.add(row.code)
        else:
            hectares[row.code] = whole
            dashes += sum(1 for code, held in row.held.items() if held == DASH and code != ALL)
    places = max(
        (places_of(land) for found in hectares.values() for land in found.values()), default=0
    )
    total = {lsoa: held_to_its_total(opened, hectares[lsoa], places) for lsoa in sorted(hectares)}
    if any(land <= 0 for land in total.values()):
        raise _refused(opened.file_id, "an LSOA covers no land")
    return Sheet(
        hectares={
            lsoa: {code: land for code, land in found.items() if code != ALL}
            for lsoa, found in hectares.items()
        },
        total=total,
        without=tuple(sorted(without)),
        rows=len(table.rows),
        others=table.others,
        header_at=table.header_at,
        file_id=opened.file_id,
        dashes=dashes,
        places=places,
    )


# The table as it was last read, by the hash of its file. Five measures read one table, and
# a file is kept under its hash and never written over.
_READ: dict[str, Sheet] = {}


def read(opened: Opened) -> Sheet:
    """The hectares of every LSOA in the file. The file is read once, whoever asks."""
    found = _READ.get(opened.receipt.sha256)
    if found is None:
        found = sheet_of(
            opened, read_table(opened, COLUMNS, AN_LSOA, over=OVER, total=TOTAL, unit=UNIT)
        )
        _READ.clear()
        _READ[opened.receipt.sha256] = found
    return found


def keyed_by(sheet: Sheet, found: Spine) -> Geography:
    """What the rows are keyed by. It stops if that is not the LSOAs of the census of 2021.

    No page names the census. The spine is made from the lookup of 2021, so a
    table with a row for every LSOA of the spine is on the codes of 2021. One
    on the codes of 2011 lacks every LSOA that was drawn again.
    """
    there = [lsoa in sheet.hectares or lsoa in sheet.without for lsoa in found.lsoas]
    if not any(there):
        raise _refused(sheet.file_id, "it holds no row of London")
    if not all(there):
        raise _refused(sheet.file_id, "an LSOA of the census of 2021 has no row")
    return KEYED_BY


def held_to_the_land(sheet: Sheet, measured: Land, found: Spine) -> Sheet:
    """The sheet, once its totals are seen to be the hectares of its LSOAs.

    No page states the unit. So the total of each LSOA of the spine is set
    against the land the build measures inside its outline. It stops where
    every row adds up to a hundred, which is a table of shares, and where the
    middle LSOA's total is under half its land or over twice.
    """
    totals = [sheet.total[lsoa] for lsoa in found.lsoas if lsoa in sheet.total]
    if not totals:
        return sheet
    if len(totals) > 1 and all(abs(total - ALL_OF_IT) <= GIVE_OR_TAKE for total in totals):
        raise _refused(sheet.file_id, "its figures are shares and not areas of land")
    middle = statistics.median(
        sheet.total[lsoa] / measured.of_lsoa[lsoa]
        for lsoa in found.lsoas
        if lsoa in sheet.total and lsoa in measured.of_lsoa
    )
    if not LEAST <= middle <= MOST:
        raise _refused(sheet.file_id, "its totals are not the hectares of its LSOAs")
    return replace(sheet, to_the_land=to_places(middle, 3))


def figures(feature: FeatureId, sheet: Sheet, found: Spine) -> dict[str, Worked]:
    """The share of every area's land that is in the category, or why an area has no figure."""
    category = MEASURES[feature].category
    top = {lsoa: held[category] for lsoa, held in sheet.hectares.items()}
    worked = lsoa_ratio_by_homes(top, sheet.total, found.lsoa_of, found.weights, times=TIMES)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def figures_by_homes(feature: FeatureId, sheet: Sheet, found: Spine) -> dict[str, Worked]:
    """The other figure: the mean of the shares of an area's LSOAs, weighted by their homes.

    The design of the vibes asked for it. It counts a works among homes for
    more than a works where nobody lives. No build carries it: core names each
    measure as a share of land and says it is measured, and this is a mean of
    shares, so it would be marked as averaged. It is here so that the two can
    be set side by side on the table before a recipe rests on either.
    """
    category = MEASURES[feature].category
    shares = {
        lsoa: TIMES * held[category] / sheet.total[lsoa] for lsoa, held in sheet.hectares.items()
    }
    worked = lsoa_value_by_homes(shares, found.lsoa_of, found.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def _when(period: Period) -> str:
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(feature: FeatureId, files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    Core decides the unit and which way is more. The name is the measure's
    own, and core's too. The period is the receipt's.
    """
    of = MEASURES[feature]
    category = next(one for one in CATEGORIES if one.code == of.category)
    return catalogue_row(
        feature,
        method=LSOA_RATIO_BY_HOMES,
        label=of.label,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=DEFINITION.format(
            category=category.name.lower(),
            holds=of.holds,
            publisher=PUBLISHER,
            as_at=as_at,
            classes=len(CATEGORIES),
            times=TIMES,
            decimals=DECIMALS,
        ),
    )


def build(feature: FeatureId, inputs: Inputs, found: Spine, measured: Land) -> LandUse:
    """One measure: the figure of every area and its evidence, from the files of the build.

    The gate is asked about the table before it is read. `found` and
    `measured` are the spine and the land of the same build. A row of evidence
    names the table and the files of the spine. It does not name the outlines
    the land was measured on: the land is what the totals are held to, and is
    part of no figure.
    """
    if feature not in MEASURES:
        raise ValueError(f"{feature} is no measure of land use")
    opened = inputs.open(SOURCE, Use.SCORING, edition=EDITION, named=is_the_table)
    sheet = read(opened)
    geography = keyed_by(sheet, found)
    sheet = held_to_the_land(sheet, measured, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, *found.inputs})
    for file_id in behind:
        if file_id not in handed:
            raise LockError("input_has_one_receipt", file_id)
    files = tuple(handed[file_id] for file_id in behind)
    worked = figures(feature, sheet, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, feature), worked[area], LSOA_RATIO_BY_HOMES, files)
        for area in sorted(worked)
    )
    return LandUse(
        worked=worked,
        rows=rows,
        metric=metric_of(feature, files, _when(opened.receipt.data_period)),
        files=files,
        sheet=sheet,
        geography=geography,
    )


class Ground(Protocol):
    """The geography of a build, as the list of the measures hands it over."""

    @property
    def spine(self) -> Spine: ...
    @property
    def land(self) -> Land: ...


def builder(feature: FeatureId) -> Callable[[Inputs, Ground], LandUse]:
    """One measure, called as the list of the measures of a build calls each."""
    if feature not in MEASURES:
        raise ValueError(f"{feature} is no measure of land use")
    return lambda inputs, ground: build(feature, inputs, ground.spine, ground.land)
