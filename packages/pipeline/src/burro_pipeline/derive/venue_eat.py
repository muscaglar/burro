"""Places to eat: how many are within reach of where homes are.

The register has one kind for a restaurant, a cafe and a canteen, and the
measure counts that kind and no other. It is counted as places to eat and drink are, by
`derive/venue_food_drink.py`: the businesses of the kind within 800 metres of
the centre of each output area, in a straight line, as the mean over the
area's homes. Nothing is filled in. A business with no point is within reach
of nobody, and an output area with a home outside London within its reach has
no verdict. One with only land outside London within its reach is counted, and
a place on that land is missed.

What the licence registry allows of the register, and what it forbids, is at
the head of `derive/food_register.py`. No rating, no name and no address is
read.

Core holds no measure of it. `FeatureId` is the list of what may be ranked or
shown, and it is core's to change. So this module makes no row of the
catalogue and is not among the measures of a build: no release carries the
figure. It gives the figures, their rows of evidence, and `Proposed`: what
the row of the catalogue would say. `KEY` is the id the rows are written
under, and is the id the catalogue would need.

**It is not put forward to be shown on its own.** A check of the first
figures found that the register's kinds do not part a place to eat from a
takeaway well. `NOT_ALONE` says what was found. The figures are kept so that
the three kinds together can be held to their parts, and core is not asked
for a feature of places to eat alone.
"""

from dataclasses import dataclass

from burro_core.ids import FeatureId

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import venue_food_drink
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.venue_food_drink import AtHomes, Proposed, at_homes, counted, proposed_of
from burro_pipeline.evidence.method import Method
from burro_pipeline.inputs import Inputs

# What the rows of evidence call the measure. Core has no feature of this id.
KEY = "venue_eat"
SOURCE = venue_food_drink.SOURCE
WHAT = counted(KEY, "Restaurants, cafes and canteens", Group.EAT)
KEYED_BY = venue_food_drink.KEYED_BY
# Why the figure is worked out and is not put forward to be shown on its own.
NOT_ALONE = venue_food_drink.NOT_ALONE
METHOD = venue_food_drink.METHOD
METHODS: tuple[Method, ...] = venue_food_drink.METHODS
# What the product shows beside the figure.
CANNOT_SEE = (
    *venue_food_drink.OF_EVERY_KIND,
    venue_food_drink.ONE_KIND_FOR_THREE,
    venue_food_drink.AT_THE_EDGE,
    venue_food_drink.OF_ONE_KIND,
    venue_food_drink.ONE_KIND_FOLLOWS_DENSITY,
    venue_food_drink.AS_AT_THE_CENSUS,
)


@dataclass(frozen=True)
class Places(AtHomes):
    """The measure for every area of the spine, with what the row of the catalogue would say."""

    proposed: Proposed
    # The same of the second figure, for each 1,000 homes within the same reach.
    proposed_rate: Proposed


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return venue_food_drink.is_a_file(name)


def core_holds_it() -> bool:
    """Whether core has a feature under the id the rows are written under."""
    return KEY in {feature.value for feature in FeatureId}


def build(inputs: Inputs, found: Spine) -> Places:
    """The figure of every area and its evidence, from the files of the build."""
    made = at_homes(inputs, found, WHAT)
    as_at = made.register.as_at
    return Places(
        counted=made.counted,
        worked=made.worked,
        rows=made.rows,
        rate=made.rate,
        rows_of_the_rate=made.rows_of_the_rate,
        files=made.files,
        register=made.register,
        reach=made.reach,
        geography=made.geography,
        proposed=proposed_of(made.files, as_at, WHAT),
        proposed_rate=proposed_of(made.files, as_at, WHAT, rate=True),
    )
