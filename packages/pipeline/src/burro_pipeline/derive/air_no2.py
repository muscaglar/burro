"""Nitrogen dioxide: the modelled annual mean at background, for each area.

Defra publishes one file for each pollutant and year. It holds one value for
each square of a grid that covers Great Britain, in squares 1000 metres wide.
The value is what a model gives for the square as a whole, as a mean over the
year. It is not a reading, and it is not the level at any kerb, street or home.

The file does not say which grid its squares are on. They are taken to be on
the National Grid, which the centres of output areas are on: the eastings and
northings of the squares fit Great Britain on it.

How a figure is made:

1. Each output area is given the value of the square that its centre stands
   on. The centre is the point the statistics office gives for it.
2. An area's figure is the mean of those values, weighted by the homes of each
   output area at the census of 2021. That is `grid_at_homes`, which the
   pipeline design names, and it is marked as modelled. It is given to one
   decimal place: the file writes seven figures, which is more than a model
   of the air over a square knows.
3. An output area on a square with no value adds nothing, and the area's
   coverage falls by its homes. Below half the homes covered no figure is
   given. Nothing is filled in from a neighbouring square.

How the file is laid out:

    no2,,,
    2024,,,
    annual mean,,,
    ug m-3,,,
    ,,,
    gridcode,x,y,no22024
    ...

Four rows of notes, one empty row, the header, and then one row for each
square. `x` and `y` are the middle of the square in whole metres. The name of
the last column holds the pollutant and the year, so it changes with the file.
Where the model gives no value the publisher writes `MISSING`.

The parser reads the notes and holds them to what the measure claims: the
pollutant, the statistic, the unit, and the year the file's receipt gives. A
file that says anything else is refused, because the label would then be wrong.

Two records stand behind a figure. The row of evidence names the four files it
was worked out from and the method `grid_at_homes@1`. The row of the catalogue
holds the sentence a methods page prints for the measure: what it is, from
whom, for which year, and what it is not.

The publisher lays the file of every pollutant out the same way. So the parser
and the reading at homes are here once, and take a `Mapped` that says what
differs: the first note, the name of the column of values and the name of the
file. The measure of fine particles, `derive/air_pm25.py`, reads its file with
them.
"""

import csv
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId
from burro_core.release import Metric

from burro_pipeline.cells import centres
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import (
    GRID_AT_HOMES,
    SQUARE,
    Worked,
    cell_of,
    grid_at_homes,
    row_of,
    to_places,
)
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

FEATURE = FeatureId.AIR_NO2
SOURCE = "defra-pcm-background-air"
PUBLISHER = "Defra"
# The publisher names a file for what it maps and the year: `mapno22024.csv`.
FILE_STARTS = "mapno2"
# What the first four rows say, each in its first cell. The second is the year.
POLLUTANT, STATISTIC, UNIT_AS_WRITTEN = "no2", "annual mean", "ug m-3"
# The header is the sixth row. One empty row stands between it and the notes.
NOTES, HEADER_ROW = 4, 6
GRIDCODE, EASTING, NORTHING = "gridcode", "x", "y"
# What the publisher writes where the model gives no value.
NO_VALUE = "MISSING"
# The middle of a square is this far from its sides.
HALF = SQUARE // 2
# What the rows of the file are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.GRID_1KM
# A figure is given to this many decimal places. The file writes seven figures, which is
# more than a model of the air over a square 1000 metres wide knows.
DECIMALS = 1
YEAR = re.compile(r"[0-9]{4}")
WHOLE = re.compile(r"-?[0-9]+")
NUMBER = re.compile(r"[0-9]+(\.[0-9]+)?")

# The arithmetic: what a methods page prints beside the measure, and what a row of evidence names.
METHOD = GRID_AT_HOMES
METHODS: tuple[Method, ...] = (METHOD,)
# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "{publisher}'s modelled annual mean of {what} at background for {year}, in micrograms "
    "a cubic metre, on a grid of squares {square} metres wide: the value of a square "
    "is read at the point the statistics office gives as the centre of each census output area, "
    "averaged over the area by homes at the census of 2021 and given to {decimals} decimal "
    "place, with a half taken upward, so it is a model's level for whole squares and not a "
    "reading taken at any kerb, street or home."
)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is a model's estimate for a square one kilometre wide, not a reading from a monitor.",
    "It cannot tell a home on a main road from a home on a quiet street in the same square.",
    "Homes are weighed as they stood at the last census, so where many homes have been built "
    "since, or stand empty, the figure leans to where homes were and not to where they are.",
)

Square = tuple[int, int]


@dataclass(frozen=True)
class Mapped:
    """What one file of the source maps, as the file itself writes it."""

    # The first note of the file, in its first cell.
    note: str
    # The name of the column of values, which holds the year.
    column: str
    # How the publisher's name for the file starts.
    file_starts: str
    # What a refusal calls it.
    words: str

    def column_of(self, year: int) -> str:
        return self.column.format(year=year)

    def names(self, name: str) -> bool:
        """Whether a publisher's name for a file is the name of a grid of this."""
        return name.startswith(self.file_starts)


NO2 = Mapped(POLLUTANT, f"{POLLUTANT}{{year}}", FILE_STARTS, "nitrogen dioxide")


def is_the_grid(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a grid of nitrogen dioxide."""
    return NO2.names(name)


@dataclass(frozen=True)
class Grid:
    """The publisher's grid: the value of each square, by the corner `cell_of` gives."""

    year: int
    values: Mapping[Square, float]
    # How many rows stand under the header, and how many of them hold no value.
    rows: int
    without_a_value: int
    file_id: str


@dataclass(frozen=True)
class AtHomes:
    """One grid of the source, read where the homes of every area are."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    grid: Grid
    # How many squares with a value the output areas of the spine stand on.
    squares_read: int


@dataclass(frozen=True)
class Air:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    grid: Grid
    geography: Geography
    # How many squares with a value the output areas of the spine stand on.
    squares_read: int


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _cells(line: str) -> list[str]:
    """One line of the file, as its cells."""
    for row in csv.reader([line]):
        return row
    return []


def _year_of(opened: Opened, top: Sequence[Sequence[str]], what: Mapped) -> int:
    """The year the file states, once its notes are seen to say what the measure claims."""
    first = [row[0].strip() if row else "" for row in top]
    if first[0] != what.note:
        raise _refused(opened, f"it is not a map of {what.words}")
    if not YEAR.fullmatch(first[1]):
        raise _refused(opened, "the year it states is no year")
    if first[2] != STATISTIC:
        raise _refused(opened, "it is not an annual mean")
    if first[3] != UNIT_AS_WRITTEN:
        raise _refused(opened, "it is not in micrograms a cubic metre")
    if any(cell.strip() for cell in top[NOTES]):
        raise _refused(opened, "the header is not on the sixth row")
    year = int(first[1])
    if opened.receipt.data_period.days() != (f"{year}-01-01", f"{year}-12-31"):
        raise _refused(opened, "the year it states is not the year of its receipt")
    return year


def _columns(
    opened: Opened, header: Sequence[str], year: int, what: Mapped
) -> tuple[str, str, str]:
    """The three columns that are read. It stops at the first column the file does not hold."""
    value = what.column_of(year)
    for name in (GRIDCODE, EASTING, NORTHING, value):
        if name not in header:
            raise _refused(opened, f"the column {name} is missing")
    return EASTING, NORTHING, value


def read(opened: Opened, what: Mapped = NO2) -> Grid:
    """The value of every square of the publisher's grid that has one.

    A square the publisher gives no value for is counted and left out. It is
    never given the value of a neighbour, and never nought.
    """
    with opened.text() as text:
        top = [_cells(text.readline()) for _ in range(HEADER_ROW)]
    year = _year_of(opened, top, what)
    easting, northing, value = _columns(opened, top[HEADER_ROW - 1], year, what)
    values: dict[Square, float] = {}
    seen: set[Square] = set()
    with opened.text() as text:
        for _ in range(HEADER_ROW - 1):
            text.readline()
        for row in opened.rows(text, (easting, northing, value)):
            if not (WHOLE.fullmatch(row[easting]) and WHOLE.fullmatch(row[northing])):
                raise _refused(opened, "a square is not named by its middle")
            east, north = int(row[easting]), int(row[northing])
            if east % SQUARE != HALF or north % SQUARE != HALF:
                raise _refused(opened, "a square is not named by its middle")
            square = cell_of(east, north)
            if square in seen:
                raise _refused(opened, "a square is there twice")
            seen.add(square)
            if row[value] == NO_VALUE:
                continue
            held = float(row[value]) if NUMBER.fullmatch(row[value]) else math.nan
            if not math.isfinite(held):
                raise _refused(opened, "a value is no value")
            values[square] = held
    if not seen:
        raise _refused(opened, "it holds no square")
    return Grid(year, values, len(seen), len(seen) - len(values), opened.file_id)


def figures(grid: Grid, points: Mapping[str, Point], found: Spine) -> dict[str, Worked]:
    """The figure of every area of the spine, or why an area has none.

    `points` holds the centre of each output area, on the grid the squares are
    on. An output area with no centre, or on a square with no value, adds
    nothing, and the area's coverage falls by its homes.
    """
    worked = grid_at_homes(grid.values, points, found.weights)
    return {
        area: one if one.value is None else replace(one, value=to_places(one.value, DECIMALS))
        for area, one in worked.items()
    }


def definition_of(what: Mapped, year: int) -> str:
    """The sentence a methods page prints: what it is, from whom, for which year, and what not."""
    return DEFINITION.format(
        publisher=PUBLISHER, what=what.words, year=year, square=SQUARE, decimals=DECIMALS
    )


def metric_of(files: Sequence[Receipt], year: int) -> Metric:
    """The row of the catalogue: the name, the unit, the year and every source.

    Core decides the name, the unit and which way is better. The year is the
    one the file states, which is the year of its receipt.
    """
    return catalogue_row(
        FEATURE,
        method=METHOD,
        source_ids={receipt.source_id for receipt in files},
        vintage=str(year),
        definition=definition_of(NO2, year),
    )


def at_homes(
    inputs: Inputs, found: Spine, what: Mapped, key: str, *, edition: str | None = None
) -> AtHomes:
    """One grid of the source read where homes are, with a row of evidence for every area.

    The gate is asked about the grid and about the centres before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the grid and the centres, so they must be files this build
    opened. `key` is what the measure is called in the id of a fact.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=edition, named=what.names)
    placed = inputs.open(centres.CENTRES, Use.SCORING, edition=centres.CENTRES_EDITION)
    grid = read(opened, what)
    points = centres.centres_of(placed, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    behind = sorted({opened.file_id, placed.file_id, *found.inputs})
    if not all(file_id in handed for file_id in behind):
        raise ValueError("the spine is made from files of this build")
    files = tuple(handed[file_id] for file_id in behind)
    worked = figures(grid, points, found)
    rows = tuple(
        row_of(fact_id(area, FactKind.FEATURE, key), worked[area], METHOD, files)
        for area in sorted(worked)
    )
    on = {cell_of(*points[oa]) for oa in found.area_of if oa in points}
    return AtHomes(worked, rows, files, grid, len(on & set(grid.values)))


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Air:
    """The figure of every area and its evidence, from the files of the build.

    `edition` is the year, as the receipt gives it. It tells apart the files of
    two years, once the store holds both.
    """
    read_at = at_homes(inputs, found, NO2, FEATURE, edition=edition)
    return Air(
        worked=read_at.worked,
        rows=read_at.rows,
        metric=metric_of(read_at.files, read_at.grid.year),
        files=read_at.files,
        grid=read_at.grid,
        geography=KEYED_BY,
        squares_read=read_at.squares_read,
    )
