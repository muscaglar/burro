"""Pubs, bars and nightclubs of the food hygiene register: how many are within reach of homes.

The register has one kind for a pub, a bar and a nightclub, and the measure
counts that kind and no other. It is counted as places to eat and drink are,
by `derive/venue_food_drink.py`: the businesses of the kind within 800 metres
of the centre of each output area, in a straight line, as the mean over the
area's homes. Nothing is filled in. A business with no point is within reach
of nobody, and an output area with a home outside London within its reach has
no verdict.

What the licence registry allows of the register, and what it forbids, is at
the head of `derive/food_register.py`. No rating, no name and no address is
read.

**No release carries the figure, and core holds no measure of it.** It was
core's measure of pubs and bars, and was held back: a check of the first
figures found that pubs alone follow how a council fills in the register as
much as they follow pubs. It was held to a second source on 2026-09-24, the
file of places, and the second source did not confirm it. So pubs and bars
are counted from the file of places, by `derive/venues_nearby.py`, under
core's id `venue_evening`. `NOT_CARRIED` says what the check found and what
the second source showed.

The figures are still worked out, under an id of their own, so that the two
sources can be held against each other again when either changes.
`test_venues_on_the_real_files.py` holds what they gave.
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
KEY = "venue_pub"
SOURCE = venue_food_drink.SOURCE
WHAT = counted(KEY, "Pubs, bars and nightclubs", Group.PUB)
KEYED_BY = venue_food_drink.KEYED_BY
METHOD = venue_food_drink.METHOD
METHODS: tuple[Method, ...] = venue_food_drink.METHODS
# Why the figure is worked out and no release carries it: what a check of the first
# figures found, and what the second source showed.
NOT_CARRIED = (
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
    "The kind was held to a second source, the file of places, which did not confirm it: "
    "under the council that lists the fewest of its places as pubs, the file holds over five "
    "times the pubs and bars that the register gives a point for. So pubs and bars are "
    "counted from the file of places, and no release carries this figure.",
)
# What the product would show beside the figure.
CANNOT_SEE = (
    *venue_food_drink.OF_EVERY_KIND,
    "The register has one kind for a pub, a bar and a nightclub, so it cannot tell one from "
    "another, and it cannot say how late a place is open or how loud it is.",
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
    """The pubs, bars and nightclubs of the register within reach of every area's homes."""
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
