"""Cultural venues for each 1,000 homes: what a wish for culture is ranked on.

It is the second figure of `derive/culture_venues.py`, which works both out:
the venues within 800 metres of the centre of each output area, in a straight
line, for each 1,000 homes within the same reach. It is one sum over another,
each taken over the area's homes, and never a mean of rates. Nothing is filled
in. An area with no home has no figure.

The rule is the one of the places to eat and drink, applied alike: the count
and this figure are both shown, and a wish for culture is ranked on this one.
The count follows how built up an area is and how near the middle of London it
stands, and this figure follows both less closely. Core has a feature for it,
`culture_venues_per_homes`, under the name and the unit the figure supports,
so a build carries it.

What it cannot see is said beside it: it divides the venues the file lists
now by the homes of the last census, and it reads highest where few homes are,
so an area of offices or of shops leads it.

What the licence registry allows of the file of places is at the head of
`derive/culture_file.py`. No name and no address is read.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_venues
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = culture_venues.FEATURE_OF_THE_RATE
# The id the rows are written under.
KEY = culture_venues.KEY_OF_THE_RATE
SOURCE = culture_venues.SOURCE
KEYED_BY = culture_venues.KEYED_BY
# The arithmetic: what a methods page prints beside the measure. The first is the one a
# row names.
METHOD = culture_venues.METHOD_OF_THE_RATE
METHODS: tuple[Method, ...] = (METHOD,)
# What the product shows beside the figure.
CANNOT_SEE = culture_venues.CANNOT_SEE_OF_THE_RATE


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


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return culture_venues.is_the_file(name)


def build(inputs: Inputs, found: Spine) -> Rate:
    """The cultural venues for each 1,000 homes within reach, and the evidence."""
    made = culture_venues.build(inputs, found)
    return Rate(
        worked=made.rate,
        rows=made.rows_of_the_rate,
        metric=made.metric_of_the_rate,
        files=made.files,
        geography=made.geography,
    )
