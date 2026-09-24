"""Places to eat and drink for each 1,000 homes: what a wish for them is ranked on.

It is the second figure of `derive/venue_food_drink.py`, which works both
out: the places that count within 800 metres of the centre of each output
area, in a straight line, for each 1,000 homes within the same reach. It is
one sum over another, each taken over the area's homes, and never a mean of
rates. Nothing is filled in. An area with no home has no figure.

The founder decided on 2026-09-24 that the count and this figure are both
shown, and that a wish for places to eat and drink is ranked on this one. The
count follows how built up an area is and how near the middle of London it
stands. This figure follows both about half as closely, and nearly half of
its order is its own. Core has a feature for it, `venue_food_drink_per_homes`,
under the name and the unit the figure supports, so a build carries it.

What it cannot see is said beside it: it divides the places of one year by
the homes of another, and it reads highest where few homes are, so an area of
offices or of shops leads it.

What the licence registry allows of the register, and what it forbids, is at
the head of `derive/food_register.py`. No rating, no name and no address is
read.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.ids import FeatureId
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import venue_food_drink
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_food_drink import FOOD_AND_DRINK, at_homes, metric_of_the_rate
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.VENUE_FOOD_DRINK_PER_HOMES
# The id the rows are written under.
KEY = FOOD_AND_DRINK.key_of_the_rate
SOURCE = venue_food_drink.SOURCE
KEYED_BY = venue_food_drink.KEYED_BY
# The arithmetic: what a methods page prints beside the measure. The first is the one a
# row names.
METHOD = venue_food_drink.METHOD_OF_THE_RATE
METHODS: tuple[Method, ...] = (METHOD,)
# What the product shows beside the figure.
CANNOT_SEE = venue_food_drink.CANNOT_SEE_OF_THE_RATE


@dataclass(frozen=True)
class Rate:
    """The figure of every area, with what stands behind each."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return venue_food_drink.is_a_file(name)


def build(inputs: Inputs, found: Spine) -> Rate:
    """The places to eat and drink for each 1,000 homes within reach, and the evidence."""
    made = at_homes(inputs, found, FOOD_AND_DRINK)
    return Rate(
        worked=made.rate,
        rows=made.rows_of_the_rate,
        metric=metric_of_the_rate(made.files, made.register.as_at, made.counted),
        files=made.files,
        geography=made.geography,
    )
