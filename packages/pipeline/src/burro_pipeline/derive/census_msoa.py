"""A share of residents, or of households, from a census table by MSOA.

This is the first code in Burro that works out a figure about who lives
somewhere. Until 24 September 2026 no such figure could feed a score. On that
day the founder decided that two things about residents may: how old they
were, and what their households were made of, as Census 2021 counted them.
Nothing else about residents may. See ADR 0006 as amended that day.

So this module reads two census tables and no other, and refuses to be
pointed at a third:

| Table | Counts | Read for |
|---|---|---|
| TS007A, age by five-year age bands | Usual residents | Those aged 20 to 34, and 65 and over |
| TS003, household composition | Households | Those with dependent children, and of one person |

Each of the four measures has a module of its own, which says what is counted
and what is said of it. This module holds what they share: the reading of a
table, the arithmetic, and the row of the catalogue.

Core holds a feature for each, and decides its name: it says who is counted
and in which census. A person may ask for more of what one counts and never
for fewer, it stands in no scale, and no likeness is counted on it. Those are
core's to hold, and the row a measure writes copies them.

The module was written from the publisher's pages, before either table was
fetched. Both were then fetched, and the step reads each as it stands. So each
claim says what it rests on:

| What | Where it is from |
|---|---|
| The categories of each table, their names and their order | Its page, and its header |
| That TS007A counts usual residents and TS003 households | The same pages |
| That the census was taken on 21 March 2021 | The same pages |
| That a zip holds a table for each geography | The page of bulk downloads, and each zip |
| What the table by MSOA is called inside the zip | The zip: the table's code, and `-msoa.csv` |
| The columns `date` and `geography code` | The header of each file |
| How a column of a category is named | The header of each file. The two differ |
| That a count is a whole number, and that none is withheld | Every cell that is read |
| Which census the codes follow | No page. Held to the spine, which is of 2021 |

A table that is fetched again and is not as this one was stops the step, with
a few fixed words that say which of these it does not keep. It guesses none.

How a column is found. The table of age names a column by the name of the
table's variable, a colon, and the name of the category, as the zip of TS044
does. The table of households adds `; measures: Value`, writes "One person"
with no hyphen where its page writes "One-person", writes its total as "Total",
and puts every name between quotes. So a column is taken for a category where
its name is the category's, with or without the variable before it and those
words after it, whatever the case of its letters, and with a hyphen read as a
space. A category that no column is taken for, or that two are, stops the
step. No column is found by its place.

How a figure is made:

1. The counts of an MSOA are read from the publisher's own row for it, in the
   table by MSOA. While an area is an MSOA that row is the area's own.
2. The figure is the counts that are wanted, added up, over the total of the
   same row, as a percentage: `area_row_ratio`.
3. It is given to one decimal place, with a half taken upward.

Why the area's own row. The statistics office makes small changes to counts
before it publishes them, so that nobody can be picked out. The row of an MSOA
is changed once. A sum of the rows of its output areas takes in one change for
each. When areas are drawn by hand no row is published for one, and the figure
must be summed from the table by output area, which the same zip holds.

How a table is held to itself. The categories that make up the total are added
up for every MSOA, and must come to the total, give or take 2 in 100 of it.
Small changes could move a sum a little, and a column taken for the wrong
category moves it far. In both tables as fetched every row comes to its total
to the unit, so none of the 2 in 100 is used. It is a choice and no finding.

Nothing is filled in. An MSOA of the build with no row stops the step. A cell
that is not a whole number stops it: no page says how a count is withheld, and
none is in either table as fetched. An area whose total is nought has no figure.

What is never read: the name of an area, every table of another geography, and
every column that neither a measure nor the total needs. In TS003 that is the
households of each kind of couple, the households with no children or with
children who are grown, and the households of one person by age.

What is read and not added up by a measure. Ten bands of age, and two kinds of
household, are read only to hold each row to its total: single family
households, and other household types.

What no measure is made from. TS003 tells the households with dependent
children apart by how a couple is joined and by whether a parent is alone.
Those four categories are read only to be added up, and `Of` refuses a measure
that counts some of them and not all. It refuses one that counts a category
read only to hold the table to its total, and one that reads a table of its
own making in the place of the two that are held here.

What is kept of a row. A measure hands back what its table was read to hold,
so what is kept is held to the same rule as what is made. The four categories
with dependent children are kept as their one sum, under `TOGETHER`, and the
two kinds of household that are read only for the total are not kept. So
nothing this step hands on holds a count of lone parents, of one kind of
couple, or of households of students. `read` refuses a table of the caller's
own making, as `Of` does. Every band of age is kept: age is what was decided on.
"""

import csv
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked, area_row_ratio, row_of, to_places
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import SCORED_TABLES, Use
from burro_pipeline.registry.rules import census_tables_written_in

SOURCE = "ons-census-2021-age-and-household-tables"
PUBLISHER = "Office for National Statistics"
CENSUS = "Census 2021"
# The day the census was taken, as the table's own page gives it, and as it is said in words.
CENSUS_DAY = "2021-03-21"
CENSUS_DAY_IN_WORDS = "21 March 2021"
# What the column `date` holds in every row of a table of this census.
YEAR = "2021"
DATE, CODE = "date", "geography code"
# The shape of the code of an MSOA, of England or of Wales. London's are all of England.
AN_MSOA = re.compile(r"[EW]02[0-9]{6}")
# What the table of households writes after the name of a category.
AFTER = "; measures: value"
# A share is given as a percentage, to this many decimal places. Each count was changed a
# little before it was published, so a second place would say nothing.
TIMES = 100
DECIMALS = 1
# The categories that make up a total come to it, give or take this share of it. In both
# tables as fetched every row comes to its total to the unit. A choice, and no finding.
GIVE_OR_TAKE = 0.02
# What the rows a figure is read from are keyed by, once the table is held to the spine.
KEYED_BY = Geography.MSOA21
# The smallest area the figure is worked out on. The publisher gives the table down to
# output areas, and the figure is read from its own row for the MSOA.
RESOLUTION = NativeResolution.MSOA
# What the sum of the categories that are read only to be added up is kept under.
TOGETHER = "added_up_together"

# The arithmetic: what a methods page prints beside each measure.
METHODS: tuple[Method, ...] = (AREA_ROW_RATIO,)


@dataclass(frozen=True)
class Category:
    """One category of a table, as the table's own page names it."""

    # What the code calls it.
    key: str
    # Its name on the page, and any other way the page or a sister table writes it.
    spelt: tuple[str, ...]

    @property
    def name(self) -> str:
        return self.spelt[0]


@dataclass(frozen=True)
class Table:
    """One census table: what it counts, and the categories that are read."""

    # The code of the table, as the statistics office writes it.
    code: str
    # The name of its variable, which stands before a colon in the name of a column.
    variable: str
    # Who is counted, in the words of its page: usual residents, or households.
    counted: str
    total: Category
    # The categories that are read, the total apart.
    categories: tuple[Category, ...]
    # The categories that make up the total, by key. The table is held to their sum.
    make_up_the_total: tuple[str, ...]
    # The categories that are read only to be added up, by key. A measure counts every one
    # of them or none: what tells one from another was not decided on.
    only_added_up: tuple[str, ...] = ()
    # The categories that are read only to hold the table to its total. No measure counts one.
    only_for_the_total: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.code not in SCORED_TABLES:
            raise ValueError(f"{self.code} is no table that may feed a score")
        keys = [category.key for category in self.categories]
        if len(set(keys)) != len(keys) or {self.total.key, TOGETHER} & set(keys):
            raise ValueError("a category is named once")
        if not set(self.make_up_the_total) <= set(keys):
            raise ValueError("the total is made up of categories that are read")
        if not {*self.only_added_up, *self.only_for_the_total} <= set(keys):
            raise ValueError("what is read only to be added up is a category that is read")
        if not set(self.only_for_the_total) <= set(self.make_up_the_total):
            raise ValueError("what is read only for the total is a part of the total")

    @property
    def member(self) -> str:
        """How the name of the table by MSOA ends, inside the zip."""
        return f"-{self.code.lower()}-msoa.csv"

    @property
    def file(self) -> str:
        """The publisher's name for the zip."""
        return f"census2021-{self.code.lower()}.zip"

    def is_the_table(self, name: str) -> bool:
        """Whether a publisher's name for a file is the name of the zip of this table."""
        return name.lower() == self.file

    def category(self, key: str) -> Category:
        return next(category for category in (self.total, *self.categories) if category.key == key)

    def kept(self, counted: Mapping[str, int]) -> dict[str, int]:
        """What is kept of a row that was read, once it is held to its total.

        The categories that are read only to be added up are kept as their one
        sum, and those read only for the total are not kept. So what a measure
        hands back holds no count that no measure may be made from.
        """
        apart = {*self.only_added_up, *self.only_for_the_total}
        found = {key: count for key, count in counted.items() if key not in apart}
        if self.only_added_up:
            found[TOGETHER] = sum(counted[key] for key in self.only_added_up)
        return found


def _category(key: str, *spelt: str) -> Category:
    return Category(key, spelt)


_BANDS = (
    ("aged_0_4", "Aged 4 years and under"),
    *(
        (f"aged_{first}_{first + 4}", f"Aged {first} to {first + 4} years")
        for first in range(5, 85, 5)
    ),
    ("aged_85_over", "Aged 85 years and over"),
)
# Age by five-year age bands: a total and 18 bands, as its page on Nomis gives them.
AGE = Table(
    code="TS007A",
    variable="Age",
    counted="usual residents",
    total=_category("total", "Total", "Total: All usual residents"),
    categories=tuple(_category(key, name) for key, name in _BANDS),
    make_up_the_total=tuple(key for key, _ in _BANDS),
)
_FAMILY = "Single family household"
# Household composition. Its page gives a total and 21 categories. Seven are read: the
# three kinds of household that make up the total, and the four that hold dependent
# children. The page writes the first of those four with no "With". It is read either way.
HOUSEHOLDS = Table(
    code="TS003",
    variable="Household composition",
    counted="households",
    total=_category("total", "Total: All households", "Total"),
    categories=(
        _category("one_person", "One-person household"),
        _category("one_family", _FAMILY),
        _category("other_kinds", "Other household types"),
        _category(
            "couple_married_children",
            f"{_FAMILY}: Married or civil partnership couple: Dependent children",
            f"{_FAMILY}: Married or civil partnership couple: With dependent children",
        ),
        _category(
            "couple_cohabiting_children",
            f"{_FAMILY}: Cohabiting couple family: With dependent children",
            f"{_FAMILY}: Cohabiting couple family: Dependent children",
        ),
        _category(
            "lone_parent_children",
            f"{_FAMILY}: Lone parent family: With dependent children",
            f"{_FAMILY}: Lone parent family: Dependent children",
        ),
        _category(
            "other_kinds_children",
            "Other household types: With dependent children",
            "Other household types: Dependent children",
        ),
    ),
    make_up_the_total=("one_person", "one_family", "other_kinds"),
    # The table tells these four apart by how a couple is joined and by whether a parent is
    # alone. Marriage and civil partnership is a protected characteristic, and nothing was
    # decided on it or on lone parents. So the four are one count, and never four.
    only_added_up=(
        "couple_married_children",
        "couple_cohabiting_children",
        "lone_parent_children",
        "other_kinds_children",
    ),
    # Households of one family are most households, and other household types take in the
    # households of students. Neither was decided on as a measure.
    only_for_the_total=("one_family", "other_kinds"),
)
TABLES: Mapping[str, Table] = {table.code: table for table in (AGE, HOUSEHOLDS)}


@dataclass(frozen=True)
class Counts:
    """What is kept of a table for every MSOA in it: the total, and what a measure may count.

    A category that is read only to be added up is here in the sum of them all,
    under `TOGETHER`, and nowhere by itself. A category that is read only to
    hold the table to its total is not here.
    """

    table: Table
    # What is kept of each MSOA, by the key of the category.
    of_msoa: Mapping[str, Mapping[str, int]]
    # How many rows stand under the header.
    rows: int
    file_id: str
    # How far the categories of any row stand from its total, at the most. The categories
    # themselves are not all kept, so this is what a test holds a table to.
    furthest_from_its_total: int = 0


@dataclass(frozen=True)
class Of:
    """One measure: what is counted, of whom, and what is said of it."""

    # What the rows of evidence call the measure: the id of the feature of core's that it is.
    key: str
    table: Table
    # The categories that are added up, by key. The figure is their sum over the total.
    counted: tuple[str, ...]
    # What a person reads beside the figure. It says who is counted and in which census.
    label: str
    # A few words for a form. A person may ask for more of it, and never for fewer.
    short_label: str
    # What is counted, as the sentence of the measure says it.
    said: str
    # What the figure cannot see, as the product would say it beside the figure.
    cannot_see: tuple[str, ...]

    def __post_init__(self) -> None:
        if TABLES.get(self.table.code) is not self.table:
            raise ValueError(f"{self.key} reads a table as this step holds it, and no other")
        if not self.counted or not set(self.counted) <= {c.key for c in self.table.categories}:
            raise ValueError(f"{self.key} counts categories of its table that are read")
        apart = set(self.counted) & set(self.table.only_added_up)
        if apart and apart != set(self.table.only_added_up):
            raise ValueError(
                f"{self.key} counts some of the categories that are read only to be added up. "
                "A measure counts every one of them, or none"
            )
        if set(self.counted) & set(self.table.only_for_the_total):
            raise ValueError(
                f"{self.key} counts a category that is read only to hold the table to its total"
            )
        named = f"{self.key} {self.label}".lower()
        if self.table.counted.split()[-1] not in named or CENSUS.lower() not in named:
            raise ValueError(f"{self.key} says in its name who is counted and in which census")
        if census_tables_written_in(self.key):
            raise ValueError(f"{self.key} holds the code of a table")

    @property
    def kept(self) -> tuple[str, ...]:
        """What the measure adds up, as a row is kept: its own categories, or the one sum."""
        alone = tuple(key for key in self.counted if key not in self.table.only_added_up)
        return alone if len(alone) == len(self.counted) else (*alone, TOGETHER)


@dataclass(frozen=True)
class Share:
    """One measure for every area of the spine, in percent, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    counts: Counts
    geography: Geography


DEFINITION = (
    "{said}, as a percentage of all the {counted} of the area, as {census} counted them on "
    "{day}: both counts are the {publisher}'s own for the census area, from its table "
    "{code}, and are not added up from smaller areas; the share is given to {decimals} "
    "decimal place, with a half taken upward; the statistics office made small changes to "
    "counts before it published them, so that nobody can be picked out; so it says who was "
    "counted as living in the area on one day during a lockdown, and says nothing of who "
    "lives there now."
)
# How what a figure cannot see ends, whatever it counts: it is a count of one day.
SINCE = (
    f"on {CENSUS_DAY_IN_WORDS}, during a lockdown, so it cannot see who has moved in or out "
    "since, or who lives in a home built since."
)


def plain(name: str, variable: str) -> str:
    """The name of a column as it is compared: the category alone, in small letters.

    The variable before it and `; measures: Value` after it are left out, a
    hyphen is read as a space, and any run of spaces as one.
    """
    text = re.sub(r"\s+", " ", name.casefold().replace("-", " ")).strip()
    text = text.removesuffix(AFTER).strip()
    before = f"{variable.casefold().replace('-', ' ')}:"
    return text.removeprefix(before).strip()


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def columns_of(opened: Opened, table: Table, header: Sequence[str]) -> dict[str, str]:
    """The column of each category that is read, by the key of the category.

    It stops at a category that no column is taken for and at one that two
    are, and says which by the key, which is this module's word and not the
    file's.
    """
    found: dict[str, str] = {}
    for category in (table.total, *table.categories):
        spelt = {plain(spelling, table.variable) for spelling in category.spelt}
        named = [name for name in header if plain(name, table.variable) in spelt]
        if not named:
            raise _refused(opened, f"the column of {category.key} is missing")
        if len(named) > 1:
            raise _refused(opened, f"two columns are taken for {category.key}")
        found[category.key] = named[0]
    if len(set(found.values())) != len(found):
        raise _refused(opened, "one column is taken for two categories")
    return found


def _header(opened: Opened, table: Table) -> list[str]:
    with opened.text(table.member) as text:
        try:
            header = next(csv.reader(text), list[str]())
        except csv.Error:
            raise _refused(opened, "a row is broken") from None
    for name in (DATE, CODE):
        if name not in header:
            # The name is the one this step asks for. Nothing of the file is repeated.
            raise _refused(opened, f"the column {name} is missing")
    return header


def _count(opened: Opened, cell: str) -> int:
    if not (cell.isascii() and cell.isdigit()):
        raise _refused(opened, "a count is not a count")
    return int(cell)


def _hold_to_the_total(opened: Opened, table: Table, counted: Mapping[str, int]) -> int:
    """Stop unless the categories that make up the total come to it, give or take a little.

    It gives how far they stand from it, in whole residents or households.
    """
    total = counted[table.total.key]
    added = sum(counted[key] for key in table.make_up_the_total)
    if abs(added - total) > math.ceil(GIVE_OR_TAKE * total):
        raise _refused(opened, "the categories of a row do not come to its total")
    if any(count > total for count in counted.values()):
        raise _refused(opened, "a category holds more than the total")
    return abs(added - total)


def hold_to_census_day(opened: Opened) -> None:
    """Stop unless the receipt of a file says it is of the day of the census."""
    if opened.receipt.data_period.as_at != CENSUS_DAY:
        raise _refused(opened, "its receipt is not of the day of the census")


def read(opened: Opened, table: Table) -> Counts:
    """The counts of every MSOA in the table, for the categories that are read.

    It stops where the receipt is not of Census Day, at a column that is
    missing, at a row of another year, at a code that is not an MSOA's or is
    there twice, at a cell that is not a whole number, and at a row whose
    categories do not come to its total. It refuses a table that is not one of
    the two this step holds: a table of the caller's own could name a column
    that no measure may be made from. What it keeps of a row is `Table.kept`.
    """
    if TABLES.get(table.code) is not table:
        raise ValueError("a table is read as this step holds it, and no other")
    hold_to_census_day(opened)
    columns = columns_of(opened, table, _header(opened, table))
    of_msoa: dict[str, dict[str, int]] = {}
    rows = furthest = 0
    with opened.text(table.member) as text:
        for row in opened.rows(text, (DATE, CODE, *columns.values())):
            rows += 1
            if row[DATE] != YEAR:
                raise _refused(opened, "a row is not of the year of the census")
            code = row[CODE]
            if not AN_MSOA.fullmatch(code):
                raise _refused(opened, "a code is not the code of an MSOA")
            if code in of_msoa:
                raise _refused(opened, "an MSOA is there twice")
            counted = {key: _count(opened, row[name]) for key, name in columns.items()}
            furthest = max(furthest, _hold_to_the_total(opened, table, counted))
            of_msoa[code] = table.kept(counted)
    if not of_msoa:
        raise _refused(opened, "it holds no row of an MSOA")
    return Counts(
        table=table,
        of_msoa=of_msoa,
        rows=rows,
        file_id=opened.file_id,
        furthest_from_its_total=furthest,
    )


def keyed_by(counts: Counts, found: Spine) -> Geography:
    """What the rows are keyed by. It stops if that is not the MSOAs of the census of 2021.

    The spine is made from the lookup of 2021, so a table with a row for every
    MSOA of the spine is on the codes of 2021.
    """
    if any(area.code not in counts.of_msoa for area in found.areas):
        raise LockError(
            "input_is_as_described", counts.file_id, "an MSOA of the census of 2021 has no row"
        )
    return KEYED_BY


def figures(of: Of, counts: Counts, found: Spine) -> dict[str, Worked]:
    """The share of every area, in percent, or why an area has no figure."""
    rows = {area.area_id: counts.of_msoa[area.code] for area in found.areas}
    top = {area: float(sum(row[key] for key in of.kept)) for area, row in rows.items()}
    bottom = {area: float(row[of.table.total.key]) for area, row in rows.items()}
    if any(top[area] > bottom[area] for area in rows):
        raise LockError("input_is_as_described", counts.file_id, "a share is more than the whole")
    worked = area_row_ratio(top, bottom, found.weights, times=TIMES)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def metric_of(of: Of, files: Sequence[Receipt]) -> Metric:
    """The row of the catalogue: the name, the day of the census, the sources and the sentence.

    Core decides the name, the unit and which way is more: a person may ask for
    more of what is counted, and never for fewer. The name is given here as
    the measure has it, so that a build leaves the measure out where the two
    are not the same, letter for letter.
    """
    return catalogue_row(
        FeatureId(of.key),
        method=AREA_ROW_RATIO,
        source_ids={receipt.source_id for receipt in files},
        vintage=CENSUS_DAY,
        label=of.label,
        native_resolution=RESOLUTION,
        definition=DEFINITION.format(
            said=of.said,
            counted=of.table.counted,
            census=CENSUS,
            day=CENSUS_DAY_IN_WORDS,
            publisher=PUBLISHER,
            code=of.table.code,
            decimals=DECIMALS,
        ),
    )


# Each table as it was last read, by its code and the hash of its file. Two measures read
# each table, and a file is kept under its hash and never written over.
_READ: dict[str, tuple[str, Counts]] = {}


def _read_once(opened: Opened, table: Table) -> Counts:
    """The counts of a table. A file is read once, whichever of its measures asks.

    Its receipt is asked about every time: the same bytes may stand under
    another receipt, and what was read before says nothing of this one.
    """
    hold_to_census_day(opened)
    sha256, found = _READ.get(table.code, ("", None))
    if found is None or sha256 != opened.receipt.sha256:
        found = read(opened, table)
        _READ[table.code] = (opened.receipt.sha256, found)
    return found


def build(of: Of, inputs: Inputs, found: Spine) -> Share:
    """One measure: the figure of every area and its evidence, from the files of the build.

    The gate is asked about the table before it is read, for scoring. `found`
    is the spine of the same build. A row of evidence names the table and the
    files of the spine, which say which MSOA an area is.
    """
    opened = inputs.open(SOURCE, Use.SCORING, named=of.table.is_the_table)
    counts = _read_once(opened, of.table)
    geography = keyed_by(counts, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, *found.inputs})
    for file_id in behind:
        if file_id not in handed:
            raise LockError("input_has_one_receipt", file_id)
    files = tuple(handed[file_id] for file_id in behind)
    worked = figures(of, counts, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, of.key), worked[area], AREA_ROW_RATIO, files)
        for area in sorted(worked)
    )
    return Share(
        worked=worked,
        rows=rows,
        metric=metric_of(of, files),
        files=files,
        counts=counts,
        geography=geography,
    )
