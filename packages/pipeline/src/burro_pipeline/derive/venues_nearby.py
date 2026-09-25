"""Cafes, gyms and pubs nearby: how many of each are within reach of where homes are.

The places come from the one file of Overture Maps Places that culture nearby
is counted from, read the same way: `culture_file.records` hands over the
kind and the point of each record, and nothing else of it. Which category is
which kind is in `venue_kinds.py`. Where homes are, how far a place may be,
and what is done at the edge of London are in `culture_reach.py`, which every
measure of venues asks. What the licence registry asks of the file is at the
head of `culture_file.py`. No name and no address is read.

**A figure is about what is within reach of an area's homes, and not about
what lies inside its outline.** A parade of shops on a border serves both
sides.

Two figures are worked out of each kind, for every area, and core holds all
six:

| Kind | The count, which is shown | The figure for each 1,000 homes, which is ranked on |
|---|---|---|
| Cafes and coffee shops | `venue_cafe` | `venue_cafe_per_homes` |
| Gyms and fitness studios | `venue_gym` | `venue_gym_per_homes` |
| Pubs and bars | `venue_evening` | `venue_evening_per_homes` |

The count is the places of a kind within 800 metres of home, in a straight
line, as the mean over the area's homes. The second figure is the places for
each 1,000 homes within the same reach: one sum over another, each taken over
the area's homes.

**The count is shown and never ranked on.** It is the rule of the places to
eat and drink and of the cultural venues, applied alike. On the part of
release 2026-09-23.0 each count is mostly a map of how much is about: the
count of cafes stands in the order of a count of every record at 0.93. The
figure for each 1,000 homes follows it less, and is what a wish is ranked on.
`test_venues_on_the_real_files.py` holds the numbers.

**One place with many records counts once.** Records of one kind that stand
within 25 metres of the first of them are one place, as for cultural venues.

**When nought is a count.** As for cultural venues: nought is read as a count
only where the file holds a record of any kind within the same reach.

**Pubs and bars are counted from this file, and not from the food hygiene
register.** The register was the first source of them, and was held back: a
check found that its pubs follow how a council fills in the register as much
as they follow pubs. The two were held against each other on 2026-09-24,
borough by borough, and `PUBS_ARE_FROM_THE_FILE` says what was found and why
this file is taken for the sounder. It is not the better of the two in every
borough, and `THIN_AT_THE_EDGE` says so beside every figure of pubs.

The figures are read once for a build, and kept for the next measure of the
same build that asks: each is known by the files it was worked out from.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Protocol

from burro_core.catalogue import RANKED_AS
from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file, places_counted, venue_kinds
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.culture_file import Point, Record
from burro_pipeline.derive.culture_reach import (
    DECIMALS,
    METRES,
    PER,
    Reach,
    figures,
    for_each_at,
    ground_of,
    rates,
    reach_at,
    within_at,
)
from burro_pipeline.derive.culture_venues import (
    A_STRAIGHT_LINE,
    AS_AT_THE_CENSUS,
    AT_THE_EDGE,
    GATHERED,
    HOW_SURE,
    NOUGHT,
    OF_THE_RELEASE,
    ON_THE_FILE,
    ONE_VENUE,
    SEEN,
)
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.derive.places_counted import Building, Held, as_buildings
from burro_pipeline.derive.venue_kinds import KINDS, WORDS, Kind, LeftOut
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened

SOURCE = culture_file.SOURCE
PUBLISHER = culture_file.PUBLISHER
KEYED_BY = culture_file.KEYED_BY
CENSUS = 2021
# The slot every record of the file adds to, after one for each kind.
EVERY = len(KINDS)
# The count of each kind, as core names it. The figure for each 1,000 homes is the measure
# core says the count is ranked as.
COUNT_OF: Mapping[Kind, FeatureId] = MappingProxyType(
    {
        Kind.CAFE: FeatureId.VENUE_CAFE,
        Kind.GYM: FeatureId.VENUE_GYM,
        Kind.PUB: FeatureId.VENUE_EVENING,
    }
)
# What is counted of each kind, as a name begins and as a sentence says it.
NAMED: Mapping[Kind, str] = MappingProxyType(
    {
        Kind.CAFE: "Cafes and coffee shops",
        Kind.GYM: "Gyms and fitness studios",
        Kind.PUB: "Pubs and bars",
    }
)
IN_WORDS: Mapping[Kind, str] = MappingProxyType(
    {
        Kind.CAFE: "a cafe, a coffee shop or a tea room",
        Kind.GYM: "a gym, a fitness studio or a sport or fitness facility",
        Kind.PUB: "a pub or a bar",
    }
)
METHOD, METHOD_OF_THE_RATE = within_at(METRES), for_each_at(METRES)

_COUNTED = (
    "records that release {release} of Overture Maps Places, of the {publisher}, as at {as_at}, "
    "gives a category of {kinds}, leaving out a record that its file says has closed for good, "
    "and counting records within {one_venue} metres of the first of them as one place"
)
_WHERE = (
    "within {metres} metres in a straight line of the point the statistics office gives as the "
    "centre of each census output area"
)
_NOUGHT = (
    "with nought read as a count only where the file holds a record of any kind within the "
    "same distance"
)
_HOW = (
    "given to {decimals} decimal place with a half taken upward: it is measured across whatever "
    "lies between and not along any street, a place the file does not hold is not counted, and "
    "a place that has closed and is still listed as open, or as nothing, is."
)
DEFINITION = (
    f"The number of places, from the {_COUNTED}, {_WHERE}, as the mean over the area's homes at "
    f"the census of {{census}}, {_NOUGHT}, and {_HOW}"
)
DEFINITION_OF_THE_RATE = (
    f"The number of places, from the {_COUNTED}, {_WHERE}, for each {{per}} homes at the census "
    f"of {{census}} within the same distance of the same point, each added up over the area's "
    f"homes before one is divided by the other, {_NOUGHT}, and {_HOW}"
)

# What the product shows beside a figure. Each line has a name, so that a figure takes a
# line by what it says and never by where it stands.
BY_CATEGORY = (
    "A place is what the category of its record says it is, and nothing is decided from a "
    "name, so a restaurant with a bar that is filed as a bar is counted as one, and a cafe "
    "that is filed as a bakery is not counted."
)
ONE_PLACE = (
    f"Records of one kind that stand within {ONE_VENUE} metres of the first of them count as "
    "one place, so a place whose records stand further apart counts more than once, and two "
    "of one kind side by side count as one."
)
WHAT_IT_IS_LIKE = (
    "It cannot say what a place is like, what it costs, when it is open, how large it is or "
    "how well it is thought of, and it cannot tell a chain from a place that is one of a kind."
)
FOLLOWS_THE_CENTRE = (
    "The count follows how built up an area is, how near the middle of London it stands and "
    "how many places of every kind are about, so on its own it says little more than that an "
    "area is dense and central."
)
NO_TRAINER = (
    "A trainer, a class in one sport, a pool and a court are not counted, so an area whose "
    "one place to train is a swimming pool or a boxing club reads as one with none."
)
NO_NIGHTCLUB = (
    "A nightclub, a lounge and a bar for smoking are not counted, and it cannot say how late "
    "a pub or a bar is open or how loud it is."
)
THIN_AT_THE_EDGE = (
    "Toward the edge of London the file holds fewer of the pubs that the food hygiene register "
    "lists, and in some boroughs about half of them have no pub or bar of the file within 200 "
    "metres, so an area far from the middle reads lower than it would if every pub were listed."
)
OF_THE_RATE = (
    "It divides the places the file lists now by the homes of the last census, so where many "
    "homes have been built since it reads too high.",
    "It reads highest where few homes are, so an area of offices or of shops leads it.",
)
_OF_EVERY_KIND = (
    OF_THE_RELEASE,
    ON_THE_FILE,
    GATHERED,
    BY_CATEGORY,
    ONE_PLACE,
    HOW_SURE,
    A_STRAIGHT_LINE,
    WHAT_IT_IS_LIKE,
    NOUGHT,
    AT_THE_EDGE,
    AS_AT_THE_CENSUS,
)
_OF_A_KIND: Mapping[Kind, tuple[str, ...]] = MappingProxyType(
    {Kind.CAFE: (), Kind.GYM: (NO_TRAINER,), Kind.PUB: (NO_NIGHTCLUB, THIN_AT_THE_EDGE)}
)

# Why pubs and bars are counted from the file of places, and no longer from the register.
# It is what the two sources gave when they were held against each other on 2026-09-24,
# and it names no place.
PUBS_ARE_FROM_THE_FILE = (
    "The food hygiene register gives a point to 3,562 pubs, bars and nightclubs in London, "
    "and the file of places holds 6,559 pubs and bars there. Across the areas the two counts "
    "stand in one order at 0.90, and 8 in 10 of the register's pubs have a pub or a bar of "
    "the file within 100 metres.",
    "Each council gives a business its kind, and the file bears out that councils do not give "
    "kinds alike: under the council that lists 4 in 100 of its places to eat and drink as a "
    "pub, the register gives a point to 147 and the file holds 834. One in three of the "
    "file's pubs and bars stands within 50 metres of a place the register lists as a place to "
    "eat, and of no pub of the register.",
    "So the register is not confirmed as a count of pubs from one council to the next, and "
    "the file stands in its place. The file is one table of kinds for all of London, it "
    "tells a pub from a bar and from a nightclub, and the cafes, the gyms and the cultural "
    "venues are counted from it the same way.",
    "The file is not the better of the two everywhere. In three boroughs at the edge of "
    "London under six in ten of the register's pubs have a pub or a bar of the file within "
    "200 metres, and in nine under three in four. No name was read of either, so nothing "
    "says which of the two is right of any one pub.",
)


@dataclass(frozen=True)
class Of:
    """One measure: the kind it counts, and which of its two figures it is."""

    feature: FeatureId
    kind: Kind
    # Whether it is the figure for each 1,000 homes, which is ranked on.
    rate: bool

    @property
    def label(self) -> str:
        if self.rate:
            return (
                f"{NAMED[self.kind]} for each {PER:,} homes within {METRES} m, in a straight line"
            )
        return f"{NAMED[self.kind]} within {METRES} m of home, in a straight line"

    @property
    def method(self) -> Method:
        return METHOD_OF_THE_RATE if self.rate else METHOD

    @property
    def cannot_see(self) -> tuple[str, ...]:
        """What the product shows beside the figure."""
        own = (*OF_THE_RATE,) if self.rate else (FOLLOWS_THE_CENTRE,)
        return (*_OF_EVERY_KIND, *_OF_A_KIND[self.kind], *own)


MEASURES: Mapping[FeatureId, Of] = MappingProxyType(
    {
        one.feature: one
        for kind in KINDS
        for one in (
            Of(COUNT_OF[kind], kind, rate=False),
            Of(RANKED_AS[COUNT_OF[kind]], kind, rate=True),
        )
    }
)


@dataclass(frozen=True)
class Found:
    """What one build found of the three kinds: the places, and what is within reach."""

    held: Held
    # The places that the records are, of every kind, in the order of where they stand.
    places: tuple[Building, ...]
    # How many records were taken to be a place that was counted already, by kind.
    records_of_one_place: Mapping[Kind, int]
    # What is within reach of each output area: a slot for each kind, and one for every
    # record of the file.
    reach: Reach
    # The output areas that have a count: the file holds something within reach of each.
    seen: frozenset[str]

    def counted(self, kind: Kind) -> dict[str, float]:
        """The places of a kind within reach of each output area that has a count."""
        slot = KINDS.index(kind)
        return {oa: count for oa, count in self.reach.of((slot,)).items() if oa in self.seen}

    def of_kind(self, kind: Kind) -> tuple[Building, ...]:
        return tuple(place for place in self.places if place.kind == kind.value)


@dataclass(frozen=True)
class Nearby:
    """One figure of one kind for every area of the spine, with what stands behind it."""

    of: Of
    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    found: Found
    geography: Geography


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file these measures read."""
    return culture_file.is_the_file(name)


def decide(record: Record) -> Kind | LeftOut:
    """What a record is, by the table of kinds."""
    return venue_kinds.kind_of(record.primary, record.hierarchy)


@lru_cache(maxsize=2)
def _read(opened: Opened) -> Held:
    return places_counted.read(
        opened, decide, KINDS, (LeftOut.NOT_OF_THE_TABLE, LeftOut.NO_CATEGORY)
    )


def read(inputs: Inputs, *, edition: str | None = None) -> Held:
    """What the file of places holds of the three kinds. The gate is asked before it is opened."""
    return _read(culture_file.opened_of(inputs, edition=edition))


@lru_cache(maxsize=2)
def _reached(
    places: tuple[Building, ...],
    every: tuple[Point, ...],
    centred: tuple[tuple[str, Point, int], ...],
    beyond: tuple[Point, ...],
) -> Reach:
    kinds = [kind.value for kind in KINDS]
    points = [
        *((one.longitude, one.latitude, kinds.index(one.kind), 1) for one in places),
        *((longitude, latitude, EVERY, 1) for longitude, latitude in every),
    ]
    return reach_at(points, EVERY + 1, centred, beyond, METRES)


def found_of(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Found:
    """The places of the three kinds and what is within reach of each home, from the files.

    The gate is asked about the places and about the centres before either is
    read. Every measure of a build asks the same of the same files, so what
    is found is kept and handed to the next that asks.
    """
    held = read(inputs, edition=edition)
    ground = ground_of(inputs, found)
    places, again = as_buildings(held.records, [kind.value for kind in KINDS])
    centred = tuple((oa, ground.at[oa], found.homes[oa]) for oa in sorted(ground.at))
    reach = _reached(places, held.every, centred, ground.beyond)
    seen = frozenset(oa for oa, within in reach.within.items() if within[EVERY] >= SEEN)
    return Found(
        held=held,
        places=places,
        records_of_one_place={Kind(kind): count for kind, count in again.items()},
        reach=reach,
        seen=seen,
    )


def definition_of(of: Of, held: Held) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    sentence = DEFINITION_OF_THE_RATE if of.rate else DEFINITION
    return sentence.format(
        release=held.file.edition,
        publisher=PUBLISHER,
        as_at=held.as_at,
        kinds=IN_WORDS[of.kind],
        one_venue=ONE_VENUE,
        metres=METRES,
        per=f"{PER:,}",
        census=CENSUS,
        decimals=DECIMALS,
    )


def metric_of(of: Of, files: Sequence[Receipt], held: Held) -> Metric:
    """The row of the catalogue a release carries. The count is shown, and the rate ranked on."""
    return catalogue_row(
        of.feature,
        method=of.method,
        label=of.label,
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=held.as_at,
        rankable=of.feature not in RANKED_AS,
        definition=definition_of(of, held),
    )


def build(
    feature: FeatureId, inputs: Inputs, found: Spine, *, edition: str | None = None
) -> Nearby:
    """One figure of one kind for every area, and its evidence, from the files of the build.

    `found` is the spine of the same build: a row of evidence names its files
    beside the places and the centres, so they must be files this build
    opened. `edition` is the release of the places, as its receipt gives it.
    """
    of = MEASURES[feature]
    made = found_of(inputs, found, edition=edition)
    ground = ground_of(inputs, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    behind = sorted({made.held.file.file_id, ground.placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    counted = made.counted(of.kind)
    worked = rates(counted, made.reach, found) if of.rate else figures(counted, found)
    return Nearby(
        of=of,
        worked=worked,
        rows=tuple(
            row_of(fact_id(area, FactKind.FEATURE, feature), worked[area], of.method, files)
            for area in sorted(worked)
        ),
        metric=metric_of(of, files, made.held),
        files=files,
        found=made,
        geography=KEYED_BY,
    )


class Ground(Protocol):
    """What a measure takes of the geography of a build."""

    @property
    def spine(self) -> Spine: ...


def builder(feature: FeatureId) -> Callable[[Inputs, Ground], Nearby]:
    """One measure, called as the list of the measures of a build calls each."""
    if feature not in MEASURES:
        raise ValueError(f"{feature} is no measure of cafes, gyms or pubs")
    return lambda inputs, ground: build(feature, inputs, ground.spine)


__all__ = ["WORDS", "Found", "Nearby", "Of", "build", "builder", "found_of", "read"]
