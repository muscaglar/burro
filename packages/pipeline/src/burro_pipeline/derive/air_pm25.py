"""Fine particles: the modelled annual mean of PM2.5 at background, for each area.

Defra publishes one file for each pollutant and year, and lays each out the
same way. This is the file of fine particles, which the file calls `pm2.5`. It
is read by the parser of nitrogen dioxide, in `derive/air_no2.py`, and a figure
is made the same way: the value of the square that each output area's centre
stands on, averaged by homes at the census of 2021, by `grid_at_homes`, and
given to one decimal place. Nothing is filled in. A square the publisher gives
no value for adds nothing, and the area's coverage falls by the homes on it.

What differs between the two files:

| | Nitrogen dioxide | Fine particles |
|---|---|---|
| The first note | `no2` | `pm2.5` |
| The column of values | `no22024` | `pm252024g` |
| The name of the file | `mapno22024.csv` | `mappm252024g.csv` |

The name of the column leaves out the point that the note has, and ends in
`g`. The file does not say what the `g` stands for, so no sentence of the
measure says it. The list the file was fetched by records what the
publisher's page says of it.

Core holds no measure of fine particles. `FeatureId` is the list of what may
be ranked or shown, and it is core's to change. So this module makes no row of
the catalogue and is not among the measures of a build: no release carries the
figure. It gives the figures, their rows of evidence, and `Proposed`: what the
row of the catalogue would say. `KEY` is the id the rows are written under,
and is the id the catalogue would need.

On the real file the areas differ little, and stand in nearly the order that
nitrogen dioxide puts them in. So the figure tells the middle of the city from
its edge, and tells two neighbouring areas apart poorly. `Proposed` says the
measure is shown and not ranked on. That is the founder's to decide.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.ids import Dimension, FeatureId, NativeResolution, Polarity

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import air_no2
from burro_pipeline.derive.air_no2 import Grid, Mapped
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

# What the rows of evidence call the measure. Core has no feature of this id, or of any
# other, for fine particles.
KEY = "air_pm25"
SOURCE = air_no2.SOURCE
# The file as it writes itself: `pm2.5` in its first note, `pm252024g` over its values.
PM25 = Mapped(
    note="pm2.5", column="pm25{year}g", file_starts="mappm25", words="fine particles (PM2.5)"
)
# What the rows of the file are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = air_no2.KEYED_BY
# A figure is given to this many decimal places, as nitrogen dioxide is.
DECIMALS = air_no2.DECIMALS

# The arithmetic: what a methods page prints beside the measure, and what a row of evidence names.
METHOD = air_no2.METHOD
METHODS: tuple[Method, ...] = (METHOD,)
# What the row of the catalogue would say. Core decides each of these, and has not.
LABEL = "Modelled annual mean fine particles (PM2.5)"
UNIT = "µg/m³"
# Whether an area is ranked on the figure. The areas differ little, and they stand in nearly
# the order that nitrogen dioxide puts them in, so a rank on both counts one thing twice.
RANKABLE = False
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is a model's estimate for a square one kilometre wide, not a reading from a monitor, "
    "so it cannot tell a home on a main road from a home on a quiet street in the same square.",
    "The level differs little from one area to the next, so a small difference between two "
    "areas says little.",
)


@dataclass(frozen=True)
class Proposed:
    """What the row of the catalogue would say, once core holds the measure.

    It is the row of no release. Core decides the name, the unit and which way
    is better, and has decided none of them for fine particles.
    """

    key: str
    label: str
    dimension: Dimension
    unit: str
    polarity: Polarity
    native_resolution: NativeResolution
    source_ids: tuple[str, ...]
    vintage: str
    rankable: bool
    definition: str


@dataclass(frozen=True)
class Air:
    """The measure for every area of the spine, with what stands behind it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    proposed: Proposed
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    grid: Grid
    geography: Geography
    # How many squares with a value the output areas of the spine stand on.
    squares_read: int


def is_the_grid(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a grid of fine particles."""
    return PM25.names(name)


def core_holds_it() -> bool:
    """Whether core has a feature under the id the rows are written under."""
    return KEY in {feature.value for feature in FeatureId}


def proposed_of(files: Sequence[Receipt], year: int) -> Proposed:
    """What the row of the catalogue would say: the name, the unit, the year and every source.

    Less is better, as for nitrogen dioxide, and the figure is held on the
    same grid. The year is the one the file states, which is the year of its
    receipt.
    """
    return Proposed(
        key=KEY,
        label=LABEL,
        dimension=Dimension.AIR_NOISE,
        unit=UNIT,
        polarity=Polarity.LESS,
        native_resolution=NativeResolution.GRID_1KM,
        source_ids=tuple(sorted({receipt.source_id for receipt in files})),
        vintage=str(year),
        rankable=RANKABLE,
        definition=air_no2.definition_of(PM25, year),
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Air:
    """The figure of every area and its evidence, from the files of the build.

    `edition` is the year, as the receipt gives it. It tells apart the files of
    two years, once the store holds both.
    """
    read_at = air_no2.at_homes(inputs, found, PM25, KEY, edition=edition)
    return Air(
        worked=read_at.worked,
        rows=read_at.rows,
        proposed=proposed_of(read_at.files, read_at.grid.year),
        files=read_at.files,
        grid=read_at.grid,
        geography=KEYED_BY,
        squares_read=read_at.squares_read,
    )
