"""What homes sell for: the median price paid for a home of any kind, as a measure.

`derive/price.py` reads the statistics office's workbook of median prices paid,
and a release carries the median of each kind of home as a cost, which a
budget is held against. This is the median for a home of any kind, from the
first sheet of the same workbook. It is the publisher's own figure for the
middle layer super output area that an area of the build is. Nothing is added
up, averaged or modelled, and where the publisher gives no figure none is
given here.

The founder decided on 2026-09-24 that a word for a smart area has two
readings, both of the place: the polished end of Gritty, and homes that sell
for more than the middle of the city. This is what the second is ranked on.
Core has a feature for it, `price_median`, under the name and the unit the
figure supports, so a build carries it.

It is a figure of what was paid for homes. It says nothing of who lives in a
place, or of what they earn, and nothing here reads a file that does. No vibe
rests on it and no likeness is counted on it: core says so, and refuses a
recipe that holds it.

The workbook is read by `derive/price.py` and by nothing else. What the
registry allows of it, and what the workbook says of itself, is at the head
of that module.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.ids import FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import price
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.PRICE_MEDIAN
SOURCE = price.SOURCE
KEYED_BY = price.KEYED_BY
# The arithmetic: what a methods page prints beside the measure. The first is the one a
# row names.
METHOD = price.AREA_ROW_VALUE
METHODS: tuple[Method, ...] = (METHOD,)
# What the product shows beside the figure.
CANNOT_SEE = (
    "This is the middle price of the homes that were sold in the year, of every kind and "
    "size, and it may rest on as few as 5 sales. It cannot see the homes that were not sold, "
    "or how many sales stand behind it.",
    "It cannot tell a large home from a small one, or a house from a flat, so an area where "
    "large houses were sold reads dearer than one where small flats were. It is not an asking "
    "price or a rent.",
    "It says what homes sold for. It says nothing of who lives in a place, or of what they earn.",
)


@dataclass(frozen=True)
class Sold:
    """The figure of every area, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return price.is_the_workbook(name)


def metric_of(named: price.Named) -> Metric:
    """The row of the catalogue: the name, the period and every source, as the workbook gives
    them. Core decides the unit and which way is more."""
    return catalogue_row(
        FEATURE,
        method=METHOD,
        label=named.label,
        native_resolution=NativeResolution.MSOA,
        source_ids=named.source_ids,
        vintage=named.vintage,
        definition=named.definition,
    )


def build(inputs: Inputs, found: Spine) -> Sold:
    """The median price paid for a home of any kind in every area, and the evidence."""
    prices = price.build(inputs, found)
    priced = prices.of[price.ALL.key]
    return Sold(
        worked=priced.worked,
        rows=priced.rows,
        metric=metric_of(priced.named),
        files=prices.files,
        geography=prices.geography,
    )
