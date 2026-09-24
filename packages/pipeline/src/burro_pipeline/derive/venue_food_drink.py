"""Places to eat and drink: how many are within reach of where homes are.

The places come from the food hygiene register, which `food_register.py`
reads: the kind of each business and its point, and nothing else of it. Where
homes are comes from the centres of output areas, which `cells/centres.py`
reads. What the licence registry allows of the register, and what it forbids,
is at the head of `food_register.py`.

**A figure is about what is within reach of an area's homes, and not about
what lies inside its outline.** A high street on a border serves both sides.

What counts. The register's own kind decides, and no rule is made from a name:

| Measure | The register's kinds | Its id |
|---|---|---|
| Places to eat and drink | The three below, together | `venue_food_drink`, core's |
| The same, for each 1,000 homes | The three together | `venue_food_drink_per_homes`, core's |
| Pubs and bars | Pub/bar/nightclub | `venue_evening`, core's |
| Places to eat | Restaurant/Cafe/Canteen | `venue_eat`. Core has none |
| Takeaways | Takeaway/sandwich shop | `venue_takeaway`. Core has none |

A hotel is a place to stay, and the register does not say whether it has a
place to eat. A van has no place of its own. A caterer, a school and a
hospital feed the people they serve. None of them counts. The three other
measures are in modules of their own, and are worked out here.

How a figure is made:

1. For each output area, the places that count within 800 metres of its
   centre, in a straight line.
2. An area's figure is the mean of those counts over its homes: what is
   within reach of its typical home. A home is a household at the census of
   2021. It is given to one decimal place.
3. A second figure asks a sharper question: the places within reach for each
   1,000 homes within the same reach. It is one sum over another, each taken
   over the area's homes, and never a mean of rates.

**It is a straight line, and not a walk.** The design asks for a walk of ten
minutes, and no network of streets is built yet. So the name of the measure
says a straight line, and core names it the same.

Why 800 metres. A person who walks 80 metres in a minute walks 800 in ten,
which is the walk the design asks for. As a straight line it reaches further
than that walk does, by as much as the streets wind. So it counts what a walk
of ten minutes reaches and some of what it does not. On the first files the
areas stood in nearly the same order at 600 and at 1,000 metres, so the
choice moves few areas. The distance is a choice and not a finding.

How a distance is measured. The register gives a longitude and a latitude,
and a centre is on the National Grid. `culture_reach.py` measures every
distance of every measure of venues, and says where the edge of London is:
this module holds no second copy of any part of it, so that a count of places
to eat and a count of any other venue are made the same way.

**The last digit of a figure is not known.** On the first files 38 in 100 of
the places that count stood on a point that another shares, so a point is
more often that of a postcode than of a door, though the file does not say.
A second count that measured each distance another way, by under ten
centimetres, moved 59 of 1,002 figures by 0.1 or 0.2. A figure is given to
one decimal place because it is a mean over homes, and `SHARED_POINT` says
beside it what a point is. Whether it is shown as a whole number is the
founder's to say.

Nothing is filled in:

- A business with no point is counted by the parser and is within reach of
  nobody. It is never put at the centre of its authority.
- An output area has a count only where no centre of an output area outside
  London lies within 800 metres of its own. Where one does, homes outside
  London are within reach, and so may a place to eat be, in the file of an
  authority that was not read. Such an output area adds nothing, and the
  coverage of its area falls by its homes. Below half the homes covered no
  figure is given.
- **The rule asks where homes are, and not where land is.** Where no home
  outside London is within reach, land outside London still may be. Such an
  output area is counted, and a place that stands on that land is missed. A
  second count of the first files, against the outlines of output areas,
  found 404 output areas so, with 1.5 in 100 of London's homes. So no
  sentence here says that the register covers the whole reach of an output
  area that is counted. A rule that asks about land needs outlines that the
  licence registry gives for scoring, which is the founder's to approve.

**A kind is what a council says it is.** Each council gives a business its
kind, and they do not give kinds alike. On the first files one authority
listed 4 in 100 of its places to eat and drink as a pub, a bar or a
nightclub, and another 18 in 100. So the three kinds together compare better
from one council to the next than any one of them does.

**Nought is a count only because the register is whole.** A build holds the
register to London before any count is read as a count: every borough of
the build is the borough that most of one file's businesses lie in, and each
file is of one borough. A borough with no file stops the build. Each file is
held to its own header by the parser, so a file is never half a file.

What nought cannot mean. A count is of businesses with a point. So nought is
no place with a point within reach, and a place with none may stand there.
`food_register.py` counts them, by authority and by kind.

**Both figures are carried, and a wish is ranked on the second.** A check of
the first figures found that the count is a true count that says little of
its own: it stands in nearly the order of every business in the register
within the same reach, and how built up and how central an area is give about
seven tenths of its order. It was held back until the founder had decided,
and the founder decided on 2026-09-24: both figures are shown, and a wish for
places to eat and drink is ranked on the places for each 1,000 homes. So the
count is carried and shown, and no area is ranked on it: `RANKABLE`, which is
core's to say. Core holds a release to that. The second figure is a measure of its own, in
`venue_food_drink_per_homes.py`. `FOLLOWS_DENSITY` still says beside the
count what the check found. The pubs are still held back.

Two records stand behind a figure. The row of evidence names every file of
the register that the build read, the centres, the lookup and the homes, and
the method. The row of the catalogue holds the name, the unit, the days of
the extracts and the sentence a methods page prints.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache

from burro_core.catalogue import RANKED_AS
from burro_core.facts import fact_id
from burro_core.ids import Dimension, FactKind, FeatureId, NativeResolution, Polarity
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_reach, food_register
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.culture_reach import (
    DECIMALS,
    METRES,
    PER,
    Point,
    for_each_at,
    ground_of,
    kept,
    nearest,
    reach_at,
    within_at,
)
from burro_pipeline.derive.food_register import Group, Place, Register
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.VENUE_FOOD_DRINK
SOURCE = food_register.SOURCE
PUBLISHER = food_register.PUBLISHER
# A business votes for the borough of the nearest centre, where one is this near, in metres.
NEAR = 250
# What the places are keyed by, as the parser finds them. No receipt says it yet.
KEYED_BY = Geography.POINT
CENSUS = 2021
# What a count is a count of, and what the second figure is for each of. Core says the same
# of the places to eat and drink. Of the pubs it still gives the unit as `per km²`.
UNIT, UNIT_OF_THE_RATE = "count", "per 1,000 homes"
# Whether an area is ranked on the count of places to eat and drink by itself. It is shown,
# and a wish for them is ranked on the places for each 1,000 homes: decided on 2026-09-24.
# Core says which measures are so, and refuses a release that ranks on one.
RANKABLE = FEATURE not in RANKED_AS
# The groups a measure may count, in the order their counts are kept in.
COUNTED = (Group.EAT, Group.PUB, Group.TAKEAWAY)

# The records of the two methods are those of every measure of venues. What is true of the
# register alone at the edge of London is said beside a figure, in `AT_THE_EDGE`.
METHOD, METHOD_OF_THE_RATE = within_at(METRES), for_each_at(METRES)
METHODS: tuple[Method, ...] = (METHOD, METHOD_OF_THE_RATE)


@dataclass(frozen=True)
class Counted:
    """What one measure counts, and what it is called."""

    # What the rows of evidence call the measure. It is core's id where core has one.
    key: str
    groups: tuple[Group, ...]
    # What is counted, as a name begins and as a sentence says it.
    named: str
    # The kinds, as the register writes them.
    kinds: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.named} within {METRES} m of home, in a straight line"

    @property
    def label_of_the_rate(self) -> str:
        return f"{self.named} for each {PER:,} homes within {METRES} m, in a straight line"

    @property
    def key_of_the_rate(self) -> str:
        return f"{self.key}_per_homes"


def counted(key: str, named: str, *groups: Group) -> Counted:
    kinds = tuple(
        name for _, (name, group) in sorted(food_register.KINDS.items()) if group in groups
    )
    return Counted(key, groups, named, tuple(sorted(kinds)))


FOOD_AND_DRINK = counted(FEATURE, "Places to eat and drink", *COUNTED)

# What the measure is, from whom, for what period, and what it is not.
DEFINITION = (
    "The number of businesses that the food hygiene register of the {publisher} lists as "
    "{kinds}, as at {as_at}, and gives a point for within {metres} metres in a straight line of "
    "the point the statistics office gives as the centre of each census output area, as the "
    "mean over the area's homes at the census of {census} and given to {decimals} decimal place "
    "with a half taken upward: it is measured across whatever lies between and not along any "
    "street, so it reaches further than a walk of that length, a business the register gives no "
    "point for is not counted, and a business that has closed and is still listed is."
)
DEFINITION_OF_THE_RATE = (
    "The number of businesses that the food hygiene register of the {publisher} lists as "
    "{kinds}, as at {as_at}, and gives a point for within {metres} metres in a straight line of "
    "the point the statistics office gives as the centre of each census output area, for each "
    "{per} homes at the census of {census} within the same distance of the same point, each "
    "added up over the area's homes before one is divided by the other, and given to {decimals} "
    "decimal place with a half taken upward: it is measured across whatever lies between and "
    "not along any street, a business the register gives no point for is not counted, and a "
    "business that has closed and is still listed is."
)
# What a check of the first figures found that keeps a measure out of every release. It
# held three lines of the count until 2026-09-24, when the founder decided that the count
# and the places for each 1,000 homes are both shown and that a wish is ranked on the
# second. Core's catalogue now says so, and no recipe of core's makes a vibe of the count
# alone. So nothing holds the measure back. What the check found is said beside the
# figure, in `FOLLOWS_DENSITY`.
HELD_BACK: tuple[str, ...] = ()
# What every measure of the register waits on, whatever it counts.
OF_THE_REGISTER = (
    "Some businesses of the kinds that count have no point in the register and are counted "
    "nowhere, and how many differs much from one authority to the next. The postcode directory "
    "would place those that have an address, and it has no receipt. Whether a count is shown "
    "before then is the founder's to say.",
    "An output area is left out where homes outside London are within its reach, and is counted "
    "where only land outside London is, so a place on that land is missed. The files of the "
    "districts that border London would close it, and so would a rule that asks about land, "
    "which needs outlines that the licence registry gives for scoring. Each is the founder's to "
    "approve.",
    "Nothing that is read says how long ago a place was last inspected, so nothing says how "
    "many of the places counted may have closed. The register gives the day of each inspection, "
    "and the licence registry does not say that it may be read. One condition added to the "
    "entry would let businesses be counted by how long ago each was inspected, with the day "
    "never shown of one business. It is the founder's to add.",
)
# The measure is carried, and a measure that is carried waits on nothing. What is not
# settled of the register is said beside each figure, in `CANNOT_SEE`.
WAITS_ON: tuple[str, ...] = ()
# What the product shows beside the figure. Each line has a name, so that the measure of
# one kind takes a line by what it says and never by where it stands.
ON_THE_REGISTER = (
    "It counts what is on the register, so a place that has closed and is still listed is "
    "counted, and a place that trades and is not registered is not."
)
A_STRAIGHT_LINE = (
    "It is a straight line from where the homes of each small census area are taken to stand, "
    "and not a walk, so a railway, a river or a main road in between puts a place further off "
    "than it is counted."
)
HOW_LONG_AGO = (
    "Nothing that is read says how long ago a council last saw a place, so the figure cannot "
    "say how many of the places it counts are still there."
)
NO_POINT = (
    "A business that the register gives no point for is counted nowhere, and how many those are "
    "differs much from one council to the next, so an area under a council that gives few "
    "points reads lower than the same area would under a council that gives many."
)
SHARED_POINT = (
    "Many places stand on a point that another shares, so a point is not always where the door "
    "is, and a place near the end of the reach is counted or missed by where its point was put."
)
ONE_KIND_FOR_THREE = (
    "The register has one kind for a restaurant, a cafe and a canteen, so a canteen that serves "
    "one workplace counts as a place to eat, and it cannot say what a place sells, what it "
    "charges or when it is open."
)
AT_THE_EDGE = (
    "Near the edge of London a place outside it may be within reach, in a file that was not "
    "read: where homes outside London are within reach the homes beside them are left out of "
    "the figure, and where only land outside London is within reach they are counted and a "
    "place on that land is missed, so the figure reads low."
)
KINDS_TOGETHER = (
    "Each council gives a business its kind, and councils do not give kinds alike, so the three "
    "kinds together compare better from one council to the next than any one of them does."
)
# What is said of one kind alone, in the place of the sentence above.
OF_ONE_KIND = (
    "Each council gives a business its kind, and councils do not give kinds alike, so a pub "
    "that serves food may be listed as a pub under one council and as a place to eat under "
    "another, and a figure of one kind compares less well than a figure of all that count."
)
FOLLOWS_DENSITY = (
    "The count follows how built up an area is and how near the middle of London it stands, and "
    "most of what is left follows how many businesses of every kind are about, so on its own it "
    "says little more than that an area is dense and central."
)
# The same of one kind alone, which follows both less closely.
ONE_KIND_FOLLOWS_DENSITY = (
    "The count follows how built up an area is and how near the middle of London it stands, "
    "which between them give half or more of its order."
)
AS_AT_THE_CENSUS = (
    "Homes are weighed as they stood at the last census, so where many homes have been built "
    "since, or stand empty, the figure leans to where homes were and not to where they are."
)
# What is said of every measure of the register, before what is said of its own kinds.
OF_EVERY_KIND = (ON_THE_REGISTER, HOW_LONG_AGO, A_STRAIGHT_LINE, NO_POINT, SHARED_POINT)
CANNOT_SEE = (
    *OF_EVERY_KIND,
    ONE_KIND_FOR_THREE,
    AT_THE_EDGE,
    KINDS_TOGETHER,
    FOLLOWS_DENSITY,
    AS_AT_THE_CENSUS,
)
# Why places to eat and takeaways are each worked out and neither is put forward to be shown
# on its own. It is said of both, in `venue_eat.py` and in `venue_takeaway.py`.
NOT_ALONE = (
    "A check of a sample of the places counted found that the register's kinds do not part a "
    "place to eat from a takeaway well: some that are listed as a place to eat read as a "
    "takeaway, and a few are the canteen of one workplace. So the two are not shown apart on a "
    "screen, and the three kinds together are what is put forward."
)
# What is said of the second figure alone, for each 1,000 homes within the same reach.
OF_THE_RATE = (
    "It divides the places the register lists now by the homes of the last census, so where "
    "many homes have been built since it reads too high.",
    "It reads highest where few homes are, so an area of offices or of shops leads it.",
)
# What the product shows beside the second figure. It follows how built up an area is about
# half as closely as the count does, so that line is the count's alone.
CANNOT_SEE_OF_THE_RATE = (
    *(line for line in CANNOT_SEE if line != FOLLOWS_DENSITY),
    *OF_THE_RATE,
)


@dataclass(frozen=True)
class Reach:
    """What is within reach of where the homes of each output area are taken to stand."""

    # What was found, as every measure of venues finds it: a slot for each group.
    found: culture_reach.Reach
    # The groups, in the order of the slots.
    groups: tuple[Group, ...]
    # The borough that most of the businesses of each file lie in, by the authority of the file.
    borough_of: Mapping[str, str]

    @property
    def metres(self) -> int:
        return self.found.metres

    @property
    def places(self) -> Mapping[str, tuple[int, ...]]:
        """For each output area with a verdict: the places of each group within reach."""
        return self.found.within

    @property
    def homes(self) -> Mapping[str, int]:
        """For each output area with a verdict: the homes within the same reach."""
        return self.found.homes

    @property
    def near_the_edge(self) -> tuple[str, ...]:
        """The output areas with no verdict: a centre outside London lies within their reach."""
        return self.found.near_the_edge

    def of(self, groups: Iterable[Group]) -> dict[str, float]:
        """The places of some groups within reach of each output area that has a verdict."""
        return self.found.of(self.groups.index(group) for group in groups)


@dataclass(frozen=True)
class AtHomes:
    """One measure read where homes are: its two figures, with what stands behind each."""

    counted: Counted
    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The second figure: the places for each 1,000 homes within the same reach.
    rate: Mapping[str, Worked]
    rows_of_the_rate: tuple[EvidenceRow, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    register: Register
    reach: Reach
    geography: Geography


@dataclass(frozen=True)
class Venues(AtHomes):
    """The same, for a measure core's catalogue has a feature for."""

    metric: Metric


@dataclass(frozen=True)
class Proposed:
    """What the row of the catalogue would say, once core holds the measure.

    It is the row of no release. Core decides the name, the unit and which way
    is more, and has decided none of them for this.
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


def is_a_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a file this measure reads."""
    return food_register.is_a_file(name)


def boroughs_of(
    places: Sequence[Place], at: Mapping[str, Point], borough_of_oa: Mapping[str, str]
) -> dict[str, str]:
    """The borough that most of the businesses of each file lie in, by the file's authority.

    A business lies in the borough of the nearest centre of an output area,
    where one is within 250 metres. One that is further from every centre says
    nothing. A file is of a borough where over half of what its businesses
    say is that borough. A file that is of none is left out.
    """
    boroughs = sorted(set(borough_of_oa.values()))
    centres_kept = kept(
        (at[oa][0], at[oa][1], boroughs.index(borough_of_oa[oa]), 1) for oa in sorted(at)
    )
    said: dict[str, list[int]] = {}
    for place in places:
        voted = nearest(centres_kept, (place.longitude, place.latitude), NEAR)
        if voted is not None:
            said.setdefault(place.authority, [0] * len(boroughs))[voted] += 1
    found: dict[str, str] = {}
    for authority in sorted(said):
        most = max(said[authority])
        if 2 * most > sum(said[authority]):
            found[authority] = boroughs[said[authority].index(most)]
    return found


def held_to_london(register: Register, borough_of: Mapping[str, str], found: Spine) -> None:
    """Stop unless the register holds one file for each borough of the build, and no other.

    It is how a count of nought is known to be a count: every borough has its
    file, and the parser has held each file to its own header.
    """
    boroughs = {cell.borough for cell in found.cells}
    files = [one.authority for one in register.extracts]
    of_files = [borough_of.get(authority) for authority in files]
    if None in of_files or len(set(of_files)) != len(of_files) or set(of_files) != boroughs:
        raise LockError(
            "input_is_as_described", SOURCE, "it does not hold one file for each borough of London"
        )


def within_reach(
    places: Sequence[Place],
    at: Mapping[str, Point],
    found: Spine,
    beyond: Sequence[Point],
    metres: int = METRES,
    groups: Sequence[Group] = COUNTED,
) -> Reach:
    """What is within reach of each output area that has a centre, by the register's groups.

    `at` holds the centre of each output area as a longitude and a latitude,
    and `beyond` the centres of output areas outside London. An output area
    with a centre outside London within its reach has no verdict.

    Every measure of a build asks the same of the same places and the same
    centres, so what is found is kept and handed to the next that asks.
    """
    centred = tuple((oa, at[oa], found.homes[oa]) for oa in sorted(at))
    borough_of_oa = tuple((cell.oa, cell.borough) for cell in found.cells if cell.oa in at)
    return _found(tuple(places), centred, borough_of_oa, tuple(beyond), metres, tuple(groups))


@lru_cache(maxsize=4)
def _found(
    places: tuple[Place, ...],
    centred: tuple[tuple[str, Point, int], ...],
    borough_of_oa: tuple[tuple[str, str], ...],
    beyond: tuple[Point, ...],
    metres: int,
    groups: tuple[Group, ...],
) -> Reach:
    slot = {group: n for n, group in enumerate(groups)}
    points = (
        (place.longitude, place.latitude, slot[place.group], 1)
        for place in places
        if place.group in slot
    )
    at = {oa: point for oa, point, _ in centred}
    return Reach(
        found=reach_at(points, len(slot), centred, beyond, metres),
        groups=groups,
        borough_of=boroughs_of(places, at, dict(borough_of_oa)),
    )


def figures(reach: Reach, what: Counted, found: Spine) -> dict[str, Worked]:
    """The count of every area of the spine, or why an area has none.

    It is the mean over the area's homes of what is within reach of each. An
    output area with no verdict adds nothing, and the area's coverage falls
    by its homes.
    """
    return culture_reach.figures(reach.of(what.groups), found)


def rates(reach: Reach, what: Counted, found: Spine) -> dict[str, Worked]:
    """The places for each 1,000 homes within the same reach, for every area of the spine.

    The places within reach of each home are added up over the area's homes,
    and so are the homes within reach of each home. One sum is divided by the
    other. An area with no home has no figure.
    """
    return culture_reach.rates(reach.of(what.groups), reach.found, found, PER)


def _in_words(kinds: Sequence[str]) -> str:
    return kinds[0] if len(kinds) == 1 else f"{', '.join(kinds[:-1])} or {kinds[-1]}"


def definition_of(what: Counted, as_at: str, *, rate: bool = False) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    sentence = DEFINITION_OF_THE_RATE if rate else DEFINITION
    return sentence.format(
        publisher=PUBLISHER,
        kinds=_in_words(what.kinds),
        as_at=as_at,
        metres=METRES,
        per=f"{PER:,}",
        census=CENSUS,
        decimals=DECIMALS,
    )


def _sources(files: Sequence[Receipt]) -> tuple[str, ...]:
    return tuple(sorted({receipt.source_id for receipt in files}))


def metric_of(files: Sequence[Receipt], as_at: str, what: Counted = FOOD_AND_DRINK) -> Metric:
    """The row of the catalogue: the name, the unit, the days of the extracts and every source.

    Core decides which way is more. The name and the unit are the ones the
    figure supports: a count within a distance, in a straight line. Core says
    the same of the places to eat and drink, so their row is core's. It is
    shown, and no area is ranked on it.
    """
    row = catalogue_row(
        FeatureId(what.key),
        method=METHOD,
        label=what.label,
        native_resolution=NativeResolution.POINT,
        source_ids=_sources(files),
        vintage=as_at,
        rankable=FeatureId(what.key) not in RANKED_AS,
        definition=definition_of(what, as_at),
    )
    # The unit is the one the figure supports, whatever core says of the measure.
    return row.replace(unit=UNIT)


def metric_of_the_rate(
    files: Sequence[Receipt], as_at: str, what: Counted = FOOD_AND_DRINK
) -> Metric:
    """The row of the catalogue of the second figure: the places for each 1,000 homes.

    It is what a wish for places to eat and drink is ranked on. The name and
    the unit are the ones the figure supports, and core says the same.
    """
    row = catalogue_row(
        FeatureId(what.key_of_the_rate),
        method=METHOD_OF_THE_RATE,
        label=what.label_of_the_rate,
        native_resolution=NativeResolution.POINT,
        source_ids=_sources(files),
        vintage=as_at,
        definition=definition_of(what, as_at, rate=True),
    )
    return row.replace(unit=UNIT_OF_THE_RATE)


def proposed_of(
    files: Sequence[Receipt], as_at: str, what: Counted, *, rate: bool = False
) -> Proposed:
    """What the row of the catalogue would say of a figure core has no feature for.

    A person chooses which way is more, as for the measures core has. A
    figure that is for each 1,000 homes is put forward as shown and not
    ranked on: it reads highest where few homes are.
    """
    return Proposed(
        key=what.key_of_the_rate if rate else what.key,
        label=what.label_of_the_rate if rate else what.label,
        dimension=Dimension.VENUES_CULTURE,
        unit=UNIT_OF_THE_RATE if rate else UNIT,
        polarity=Polarity.EITHER,
        native_resolution=NativeResolution.POINT,
        source_ids=_sources(files),
        vintage=as_at,
        rankable=not rate,
        definition=definition_of(what, as_at, rate=rate),
    )


def at_homes(inputs: Inputs, found: Spine, what: Counted) -> AtHomes:
    """One measure read where homes are, with a row of evidence for every area.

    The gate is asked about the register and about the centres before either
    is read. `found` is the spine of the same build: a row of evidence names
    its files beside the register and the centres, so they must be files this
    build opened.
    """
    register = food_register.build(inputs)
    ground = ground_of(inputs, found, METRES)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    reach = within_reach(register.places, ground.at, found, ground.beyond)
    held_to_london(register, reach.borough_of, found)
    placed = ground.placed
    behind = sorted({*(one.file_id for one in register.files), placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    worked, rate = figures(reach, what, found), rates(reach, what, found)
    return AtHomes(
        counted=what,
        worked=worked,
        rows=tuple(
            row_of(fact_id(area, FactKind.FEATURE, what.key), worked[area], METHOD, files)
            for area in sorted(worked)
        ),
        rate=rate,
        rows_of_the_rate=tuple(
            row_of(
                fact_id(area, FactKind.FEATURE, what.key_of_the_rate),
                rate[area],
                METHOD_OF_THE_RATE,
                files,
            )
            for area in sorted(rate)
        ),
        files=files,
        register=register,
        reach=reach,
        geography=KEYED_BY,
    )


def carried(made: AtHomes) -> Venues:
    """A measure core has a feature for, with its row of the catalogue."""
    return Venues(
        counted=made.counted,
        worked=made.worked,
        rows=made.rows,
        rate=made.rate,
        rows_of_the_rate=made.rows_of_the_rate,
        files=made.files,
        register=made.register,
        reach=made.reach,
        geography=made.geography,
        metric=metric_of(made.files, made.register.as_at, made.counted),
    )


def build(inputs: Inputs, found: Spine) -> Venues:
    """The places to eat and drink within reach of every area's homes, and the evidence."""
    return carried(at_homes(inputs, found, FOOD_AND_DRINK))
