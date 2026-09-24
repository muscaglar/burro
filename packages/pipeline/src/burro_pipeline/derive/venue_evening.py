"""Pubs and bars: how many are within reach of where homes are.

The register has one kind for a pub, a bar and a nightclub, and the measure
counts that kind and no other. It is counted as places to eat and drink are,
by `derive/venue_food_drink.py`: the businesses of the kind within 800 metres
of the centre of each output area, in a straight line, as the mean over the
area's homes. Nothing is filled in. A business with no point is within reach
of nobody, and an output area with a home outside London within its reach has
no verdict. One with only land outside London within its reach is counted, and
a place on that land is missed.

What the licence registry allows of the register, and what it forbids, is at
the head of `derive/food_register.py`. No rating, no name and no address is
read.

Core has a feature for it, `venue_evening`, which it names pubs, bars and
evening venues and gives for each square kilometre. The figure is a count
within reach of homes, and the register names no venue of the evening but a
pub, a bar and a nightclub: it has no kind for a theatre, a cinema or a hall.
So the row of the catalogue that is made here carries a name and a unit of
its own. Do not give it core's name while core says evening venues.

**The measure is held back from every release and from every vibe.** A check
of the first figures found that pubs alone follow how a council fills in the
register as much as they follow pubs. `HELD_BACK` says what was found and
what would settle it. The figure is worked out at every build, and a build
leaves it out whatever core says of it. Take nothing out of `HELD_BACK` but in
a change a person reads, once the kind has been held to a second source.
"""

from burro_core.ids import FeatureId

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import venue_food_drink
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.venue_food_drink import Venues, at_homes, carried, counted
from burro_pipeline.evidence.method import Method
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.VENUE_EVENING
SOURCE = venue_food_drink.SOURCE
PUBS_AND_BARS = counted(FEATURE, "Pubs, bars and nightclubs", Group.PUB)
KEYED_BY = venue_food_drink.KEYED_BY
METHOD = venue_food_drink.METHOD
METHODS: tuple[Method, ...] = venue_food_drink.METHODS
# What keeps the measure out of a release, and whose it is to settle.
WAITS_ON = (
    "Core names the measure pubs, bars and evening venues, and gives it for each square "
    "kilometre. The register has one kind for a pub, a bar and a nightclub and none for any "
    "other venue of the evening, and the figure is a count within 800 metres of where homes "
    "are, in a straight line. A name and a unit in core that say so bring it in.",
    *venue_food_drink.OF_THE_REGISTER,
)
# What a check of the first figures found, and what would settle it. While it holds
# anything, no release carries the measure.
HELD_BACK = (
    "Each council gives a business its kind, and councils do not give kinds alike: of its "
    "places to eat and drink one council lists 4 in 100 as a pub, a bar or a nightclub and "
    "another 18 in 100. What is left of the figure of a borough, once how built up and how "
    "central it is are taken out, follows that share closely. So the figure cannot tell an "
    "area with few pubs from an area whose council lists its pubs as places to eat.",
    "The kind holds what is no pub that a person can walk into. A check of a sample of the "
    "businesses counted found about one in five to be a club for its members, a hall or a "
    "theatre, or a kitchen that trades inside a pub.",
    "A pub that the register gives no point for is counted nowhere, and nearly every such pub "
    "has an address, so it is a pub that stands somewhere and is missed. Under five councils "
    "more than one pub in seven is missed so.",
    "A second source of pubs to hold the register's kind to would settle it, and none is "
    "registered for that. Until one is, no release and no vibe carries the figure.",
)
# What the product shows beside the figure.
CANNOT_SEE = (
    *venue_food_drink.OF_EVERY_KIND,
    "The register has one kind for a pub, a bar and a nightclub, so it cannot tell one from "
    "another, and it cannot say how late a place is open or how loud it is.",
    venue_food_drink.AT_THE_EDGE,
    venue_food_drink.OF_ONE_KIND,
    venue_food_drink.ONE_KIND_FOLLOWS_DENSITY,
    venue_food_drink.AS_AT_THE_CENSUS,
)


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return venue_food_drink.is_a_file(name)


def build(inputs: Inputs, found: Spine) -> Venues:
    """The pubs and bars within reach of every area's homes, and the evidence."""
    return carried(at_homes(inputs, found, PUBS_AND_BARS))
