"""Addresses with private outdoor space, as a share of the addresses of an area.

The Office for National Statistics published "Access to garden space, Great
Britain, April 2020" in May 2020. It is an analysis Ordnance Survey made of
its own maps, and it gives, for each MSOA, how many addresses there are and how
many of them have private outdoor space. The share is one count over the
other, from the area's own row.

It was written from the publisher's pages, before the workbook was fetched.
The workbook was then read as it is stored, on 2026-09-24, by a program and by
no person: its sheet of notes, and the two rows of names of each sheet. What
this module claims, and where each claim is from:

| What | Where it is from |
|---|---|
| That the analysis is by MSOA | The dataset page, and the sheet `MSOA gardens` |
| That it is of April 2020 | The dataset page alone: it is the name of the edition |
| What it was counted from | The notes: "epoch 74 of OS AddressBase Plus" |
| That Ordnance Survey made it | The notes: "Source: Ordnance Survey" |
| That it counts residential addresses | The notes: "residential address records" |
| What the sheet is called, and which rows name its columns | The file. `SHEET`, `HEADER_AT` |
| What the columns are called | The file. `CODE`, `TOTAL`, `ADDRESSES`, `WITH_SPACE` |
| That one row counts houses, flats and both | The file: three headings over its columns |
| What counts as private outdoor space | Neither the file nor any page that was read |
| That a garden flats share is counted | The file names a column for how many flats share one |
| Which census the codes follow | The file names none. They are not those of 2021 |
| Which areas kept their outline | The statistics office's lookup, by its mark of no change |
| How a count that is withheld is written | No cell of the two counts is empty or is text |

The sheet names its columns in two rows. The first holds the names of the
columns that say which area a row is of, and three headings: houses, flats and
both. The second holds, under each heading, the names of its counts, and the
names are the same under each. So a count is asked for under its heading, and
the heading stands over the columns the sheet merges from it. The publisher
spells one name with one `d`, and it is asked for as it is spelt. The notes
state no month: April 2020 is the publisher's name for the edition, on its
page, and the notes state the year 2020 in their line of rights.

How a figure is made:

1. The area is held to the statistics office's lookup between the areas of
   2011 and of 2021. It has a figure only where the lookup marks it as
   unchanged: `derive/areas_of_2011.py` reads the lookup and says which.
2. The row of the area is found by the code of the MSOA the area was in 2011,
   which for an area that did not change is the code it has.
3. The figure is the count of addresses with private outdoor space over the
   count of addresses, as a percentage: `area_row_ratio`, the publisher's own
   row for the area, and never a sum of smaller areas.
4. It is given to one decimal place, with a half taken upward.

Which areas have a figure. The workbook names no census, and its codes are not
those of 2021: it lacks some areas of the build, and holds areas the build does
not. The test on the real file holds the count of each. It was made in May
2020, and the statistics office says the areas of 2021 are "made up of
unchanged 2011 MSOAs and new 2021 MSOAs". An area that the lookup marks as
unchanged, and whose code the workbook holds, has the figure of that row. An
area that was split from a larger one, or made by joining two, has no figure:
no row of the workbook is of its outline, and nothing is shared out to it. An
area the lookup marks as unchanged and the workbook holds no row for has none
either. The lookup is `HELD_TO`. It is read to say which areas kept their
outline, and never to share a figure out. A row of evidence names it beside
the workbook, so the licence registry holds it for `scoring` as well as for
`cells`.

On the real files, of London's 1,002 areas of 2021 the lookup marks 963 as
unchanged, and the workbook holds a row for each. 38 are parts of the 18
areas of 2011 that were split, and one was made by joining two. Those 39 have
no figure, and they are the 39 the workbook holds no row for.

Nothing is filled in. An empty cell is no count, and is never nought. A cell
that holds text where a count belongs stops the step, because neither the file
nor a page says how the publisher marks a count it withholds. A row with more
addresses with outdoor space than addresses stops it too.

It is not gardens as a share of land. `land_use` reads, from another
publisher's table, how much of an area's land is residential garden. That is a
share of the ground, and a few large gardens count for as much as many small
ones. This is a share of addresses: it says how many homes have any outdoor
space of their own, and nothing of how much. The vibe Homes asks for the
second.

Core names the measure as it is built, since catalogue version 13: addresses
with private outdoor space, by MSOA. The licence registry asks that a figure of
the workbook says addresses and never homes or households, because no page
says what Ordnance Survey counted as an address.

**The measure is held back from every release and from every vibe.** It counts
addresses and the ground beside them, and reads nothing of who lives at one.
The publisher's own article still reports, from a survey of people, that access
to a garden differs by ethnic group, by age and by occupation. So decision
record 0006 asks for its row of the proxy audit before it is in a release, and
the design of the vibes lets it into Houses or flats only once that row has
passed. No audit has been run, and none can be yet. `HELD_BACK` says so, and
whose it is to settle. The figure is worked out at every build whose lists
name its files, so that whoever settles it has the figures, and a build leaves
it out whatever core says of it. Take nothing out of `HELD_BACK` but in a
change a person reads, once the row has passed.
"""

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import areas_of_2011
from burro_pipeline.derive.areas_of_2011 import CARRIED, Changes, Mark
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import AREA_ROW_RATIO, Worked, area_row_ratio, row_of, to_places
from burro_pipeline.derive.noise_sheet import Under, Value, read_sheet
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.PRIVATE_OUTDOOR_SPACE
SOURCE = "ons-access-to-garden-space-2020"
EDITION = "April 2020"
PUBLISHER = "Office for National Statistics"
MADE_BY = "Ordnance Survey"
# The publisher's name for the file, as its address gives it.
FILE_NAME = "osprivateoutdoorspacereferencetables.xlsx"

# What the step asks the workbook for, each as the file holds it. The names of the columns
# stand in two rows: `HEADER_AT` is the first, and the counts are named in the row below it.
SHEET = "MSOA gardens"
HEADER_AT = 1
CODE = "MSOA code"
# The heading over the counts of houses and flats together. The sheet holds the same names
# under a heading for houses and under one for flats, and neither is read.
TOTAL = "Property type: Total"
ADDRESSES = "Address count"
# As the publisher spells it.
WITH_SPACE = "Adress with private outdoor space count"
COLUMNS = (CODE, ADDRESSES, WITH_SPACE)

# The shape of the code of an area of the workbook: an MSOA of England or of Wales, or an
# intermediate zone of Scotland. The workbook is of Great Britain.
AN_AREA = re.compile(r"[EWS]02[0-9]{6}")
# What the rows are keyed by. The workbook names no census, and its codes are not those of
# 2021. A row is found by the code an area had in 2011, which the lookup gives.
KEYED_BY = Geography.MSOA11
# The statistics office's lookup from the areas of 2011 to those of 2021, by its id in the
# licence registry. Every area that has a figure is held to it.
HELD_TO = areas_of_2011.SOURCE
# A share is given as a percentage, to this many decimal places.
WHOLE = 100
DECIMALS = 1

# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = (AREA_ROW_RATIO,)
# The name says what is counted, as core names the measure: addresses, and never homes.
LABEL = "Addresses with private outdoor space"
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "Addresses that have private outdoor space, as a percentage of the addresses of the "
    "area, from the {publisher}'s analysis of {made_by} data as at {as_at}: both counts are "
    "the publisher's own for the area, found by the code of the area, and are not added up "
    "from smaller areas; the counts are of the area as it was drawn for the census of 2011, "
    "so an area has a figure only where the {publisher}'s lookup between the areas of 2011 "
    "and of 2021 marks it as unchanged, and an area that was split, merged or drawn again "
    "has no figure, and nothing is shared out to it; an empty cell is no count and is never "
    "nought; the share is given to {places} decimal place, with a half taken upward; so it "
    "counts addresses and not homes, says whether an address has any outdoor space and not "
    "how much, and says nothing of who lives at one."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "It counts addresses as Ordnance Survey mapped them in April 2020, so it cannot see a home "
    "or a garden made since, or an area whose outline was drawn again for the census of 2021.",
    "It cannot see how large an outdoor space is, what kind it is, or whether several flats "
    "share it.",
)
# What the row of the catalogue waits on. Core names the measure as it is built, so nothing.
WAITS_ON: tuple[str, ...] = ()
# What keeps the measure out of every release, whatever core says of it, and whose it is to
# settle. It is no finding of a check of the figures: it is the row of the proxy audit, which
# is asked for before a measure that may follow who lives somewhere is in a release. While it
# holds anything, no release carries the measure.
HELD_BACK = (
    "The row of the proxy audit for private outdoor space is not written, and no audit has "
    "been run: the tables an audit is run on are gated or held in the licence registry, and "
    "no store of the audit's own is built. Decision "
    "record 0006 asks for the row before the measure is in a release, and the design of the "
    "vibes lets it into Houses or flats only if it is under 0.3 on every table of the audit. "
    "The publisher's own article reports, from a survey of people, that access to a garden "
    "differs by ethnic group, by age and by occupation.",
    "The rule of the audit, and the tables it is run on, are the founder's to settle. Until "
    "the row has passed, no release and no vibe carries the figure.",
)


@dataclass(frozen=True)
class Counted:
    """What the workbook holds for one area. A count is `None` where the cell is empty."""

    addresses: int | None
    with_space: int | None

    @property
    def whole(self) -> bool:
        """Whether the row gives both counts, and at least one address to take a share of."""
        return bool(self.addresses) and self.with_space is not None


@dataclass(frozen=True)
class Table:
    """The rows of the workbook that are of an area, by the code of the area."""

    of_area: Mapping[str, Counted]
    # How many rows stand under the row that names the columns, of an area or not.
    rows: int
    file_id: str


@dataclass(frozen=True)
class OutdoorSpace:
    """The share of addresses with private outdoor space for every area, and what is behind it."""

    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    table: Table
    # What the rows a figure is read from are keyed by.
    geography: Geography
    # The areas of the build that the workbook holds no row for.
    without_a_row: frozenset[str]
    # What the lookup says of every area of the build.
    changes: Changes
    # The areas of the build that the lookup does not mark as unchanged, each with its mark.
    # None has a figure.
    drawn_again: Mapping[str, Mark]


def is_the_workbook(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the workbook this measure reads."""
    return name == FILE_NAME


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _count(opened: Opened, cell: Value) -> int | None:
    """A count as the workbook holds it: a whole number, or nothing where the cell is empty."""
    if cell is None:
        return None
    if isinstance(cell, str) or cell < 0 or cell != int(cell):
        raise _refused(opened, "a count is not a count")
    return int(cell)


def read(opened: Opened) -> Table:
    """The counts of every area in the workbook, held to what a count can be.

    Each count is the one under the heading for houses and flats together. It
    stops at a sheet, a heading or a column that is missing, a row that holds
    a count and no code of an area, an area that is there twice, a cell that
    is no count, and a row with more addresses with outdoor space than
    addresses.
    """
    of_area: dict[str, Counted] = {}
    under = Under(TOTAL, (ADDRESSES, WITH_SPACE))
    found = read_sheet(opened, SHEET, (CODE,), header_at=HEADER_AT, under=under)
    for row in found:
        code = row[CODE]
        if not isinstance(code, str) or not AN_AREA.fullmatch(code):
            if row[ADDRESSES] is None and row[WITH_SPACE] is None:
                # A note under the table, or a line between its parts.
                continue
            raise _refused(opened, "a row holds a count and no code of an area")
        if code in of_area:
            raise _refused(opened, "an area is there twice")
        counted = Counted(_count(opened, row[ADDRESSES]), _count(opened, row[WITH_SPACE]))
        if counted.whole and (counted.with_space or 0) > (counted.addresses or 0):
            raise _refused(opened, "a share is more than the whole")
        of_area[code] = counted
    if not of_area:
        raise _refused(opened, "it holds no row of an area")
    return Table(of_area=of_area, rows=len(found), file_id=opened.file_id)


def without_a_row(table: Table, found: Spine) -> frozenset[str]:
    """The areas of the build whose code the workbook does not hold.

    It stops if the workbook holds the code of no area of the build at all: it
    is then keyed by something else, and no figure can be read from it.
    """
    missing = frozenset(area.area_id for area in found.areas if area.code not in table.of_area)
    if len(missing) == len(found.areas):
        raise LockError("input_is_as_described", table.file_id, "no area of the build has a row")
    return missing


def drawn_again(changes: Changes, found: Spine) -> dict[str, Mark]:
    """The areas of the build that the lookup does not mark as unchanged, each with its mark."""
    return {
        area.area_id: changes.marks[area.code]
        for area in found.areas
        if changes.marks[area.code] is not Mark.UNCHANGED
    }


def figures(
    table: Table, found: Spine, changes: Changes, carried: Collection[Mark] = CARRIED
) -> dict[str, Worked]:
    """The share of addresses with private outdoor space for every area, or why there is none.

    Each count is the area's own, from the row of the MSOA the area was in
    2011. An area has a figure only where the lookup gives it one area of
    2011, under a mark that `carried` names. One it gives none has no figure,
    and nor has one with no row, or whose row lacks a count or holds no address.
    """
    rows = {
        area.area_id: table.of_area.get(changes.taken_from(area.code, carried) or "")
        for area in found.areas
    }
    counted = {area: row for area, row in rows.items() if row is not None and row.whole}
    share = area_row_ratio(
        {area: float(one.with_space or 0) for area, one in counted.items()},
        {area: float(one.addresses or 0) for area, one in counted.items()},
        found.weights,
        times=WHOLE,
    )
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in share.items()
    }


def _when(period: Period) -> str:
    return period.as_at or f"{period.start} to {period.end}"


def metric_of(files: Sequence[Receipt], as_at: str) -> Metric:
    """The row of the catalogue: the name, the unit, the period and every source.

    The name is `LABEL`, which is core's: the workbook counts addresses. Core
    decides the unit and which way is more.
    """
    return catalogue_row(
        FEATURE,
        method=AREA_ROW_RATIO,
        label=LABEL,
        source_ids={receipt.source_id for receipt in files},
        vintage=as_at,
        definition=DEFINITION.format(
            publisher=PUBLISHER, made_by=MADE_BY, as_at=as_at, places=DECIMALS
        ),
    )


def build(inputs: Inputs, found: Spine) -> OutdoorSpace:
    """The share of addresses with private outdoor space for every area, from the build's files.

    The gate is asked about the workbook and about the lookup between the
    censuses before either is read. `found` is the spine of the same build. A
    row of evidence names the workbook, the lookup that says which MSOA an
    area is, and the lookup that says which areas kept their outline.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=EDITION, named=is_the_workbook)
    table = read(opened)
    missing = without_a_row(table, found)
    changes = areas_of_2011.build(inputs, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not all(file_id in handed for file_id in found.inputs):
        raise ValueError("the spine is made from files of this build")
    lookup = [file_id for file_id in found.inputs if handed[file_id].source_id == spine.LOOKUP]
    behind = {opened.file_id, changes.file_id, *lookup}
    files = tuple(handed[file_id] for file_id in sorted(behind))
    worked = figures(table, found, changes)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, FEATURE), worked[area], AREA_ROW_RATIO, files)
        for area in sorted(worked)
    )
    return OutdoorSpace(
        worked=worked,
        rows=rows,
        metric=metric_of(files, _when(opened.receipt.data_period)),
        files=files,
        table=table,
        geography=KEYED_BY,
        without_a_row=missing,
        changes=changes,
        drawn_again=drawn_again(changes, found),
    )
