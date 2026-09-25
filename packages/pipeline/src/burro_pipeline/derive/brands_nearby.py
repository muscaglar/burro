"""Brands nearby: the chains of grocers, gyms and coffee within reach, and independent places.

The founder decided on 2026-09-24 that the chains in a place say something of
it, and gave a table of tiers (ADR 0026). The places come from the part of one
file of Overture Maps Places that was taken with the brand of each place:
`culture_file.branded` reads it. Which chain is of which tier is
`brand_tiers.toml`, and `brand_table.py` says which place is of which chain.
Where homes are and how far a place may be are `culture_reach.py`'s, as for
every measure of places.

**A figure is about what is within reach of an area's homes, and not about
what lies inside its outline.** A shop on a border serves both sides.

What is worked out for every area:

| Figure | Its id |
|---|---|
| The places of a tier within reach | `<kind>_<tier>_nearby` |
| The nearest place of a tier | `<kind>_<tier>_distance` |
| The mix | `brand_mix` |
| The nearest place of a chain | `brand_<key>` |
| Independent places | `independents_nearby` |

- **The places of a tier** are counted for grocers, for gyms and for coffee,
  and for each of three tiers: the places of chains of that tier within 800
  metres of home, as the mean over the area's homes.
- **The nearest place of a tier** is how far the nearest of them is, where one
  is within 2,000 metres.
- **The mix** is, of the places of a tier within 800 metres, the share that
  are premium, with a mid-range one counted as half.
- **The nearest place of a chain** is how far the nearest place of one chain
  is, where one is within 2,000 metres.
- **Independent places** are, of the places to eat and drink within 800
  metres, the share that belong to no chain.

**What is shown and what is ranked on.** The places of a tier and the nearest
of a tier are shown, and no area is ranked on one: each row of the catalogue
says so. The mix is what is ranked on. The nearest of a chain is ranked on
where a person asks for the chain by name. Independent places are a part of
two vibes.

**Which place counts.** A place counts for a tier where its brand is a row of
the table and the file gives it a category of the row's kind: a bank or a
petrol station of a chain of grocers is no grocer. A place its file says has
closed for good is left out, and so is one with no point. Places of one chain
within 25 metres of the first of them are one place.

**Which place is independent.** A place to eat or drink is of a chain where
the file gives it a brand, on the table or off it, and independent where it
gives it none. **The file gives a brand only to places that some of its
sources gave.** In the part of release 2026-09-23.0 no place that Foursquare
or Microsoft alone gave bears one. Whether such a place is of a chain is not
known, and nothing is filled in: it is counted on neither side. The sources
that name a chain are read from the file, and are those that gave a place
that bears a brand.

**Two distances.** A place is within reach at 800 metres, as for every
measure of places. The nearest is looked for as far as 2,000 metres, which is
as far as the part of the file is known to hold every place round every home:
the list takes a box 2,000 metres wider than London's homes. An output area
with no place of the kind within 2,000 metres has no distance. It is not far:
it is not known, and its area's coverage falls by its homes.

**When nought is a count.** As for cultural venues: an output area with none
within reach has a count of nought where the file holds a record of any kind
within the same reach, and has no count where it holds none.

**What it is, and what it is not.** A tier is the founder's judgement of a
chain: what it charges and how it presents itself. A figure here counts shops.
It says nothing of who shops in one, of who lives near one, or of what anyone
earns. The mix is a stand-in for how well off a place is, and its row of the
proxy audit was written before it was served: `docs/research/data/brands.md`.
The audit was dropped on 2026-09-25 (ADR 0006, as amended), and the row holds
nothing back.
"""

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from burro_core.catalogue import (
    CHAINS,
    DISTANCE,
    NEARBY,
    NEAREST_WITHIN_M,
    SHOWN_BESIDE_THE_MIX,
    WITHIN_M,
    of_a_tier,
)
from burro_core.facts import fact_id
from burro_core.ids import FactKind, FeatureId, NativeResolution
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file, park_proximity
from burro_pipeline.derive.brand_table import (
    Chain,
    Kind,
    Table,
    Tier,
    chain_of,
    eats_or_drinks,
    is_of_kind,
    the_table,
)
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.culture_file import Branded, Point
from burro_pipeline.derive.culture_reach import (
    DECIMALS,
    Weighed,
    at_the_edge,
    figures,
    first_of_each,
    given,
    ground_of,
    nearest_at,
    nearest_of,
    reach_at,
    share_at,
    within_at,
)
from burro_pipeline.derive.culture_venues import ONE_VENUE, SEEN
from burro_pipeline.derive.methods import Worked, lsoa_ratio_by_homes, row_of
from burro_pipeline.evidence.method import Kind as MadeBy
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs, Opened

SOURCE = culture_file.SOURCE
PUBLISHER = culture_file.PUBLISHER
KEYED_BY = culture_file.KEYED_BY
CENSUS = 2021
CODE = "burro_pipeline.derive.brands_nearby"
# How far a place may be to be within reach, and how far the nearest is looked for. Both are
# core's, because the name of each measure says its distance.
WITHIN, NEAREST_WITHIN = WITHIN_M, NEAREST_WITHIN_M
# What a mid-range place counts for in the mix, where a premium one counts for one.
MID_COUNTS = 0.5
# The name the publisher gives itself among the sources of a record. It stands beside
# every source, so it says nothing of which source gave a place.
OWN = "Overture"
KINDS, TIERS = tuple(Kind), tuple(Tier)
INDEPENDENT = FeatureId.INDEPENDENTS_NEARBY
MIX = FeatureId.BRAND_MIX
# The slots what is within reach is counted in: one for each kind and tier, then the
# independent places to eat and drink, those of a chain, and every record of the file.
OF_NO_CHAIN = len(KINDS) * len(TIERS)
OF_A_CHAIN, EVERY = OF_NO_CHAIN + 1, OF_NO_CHAIN + 2
SLOTS = EVERY + 1


def slot_of(kind: Kind, tier: Tier) -> int:
    """The slot the places of one kind and one tier are counted in."""
    return KINDS.index(kind) * len(TIERS) + TIERS.index(tier)


def feature_of(chain: Chain) -> FeatureId | None:
    """The measure core names for a chain, or none where core names none for it."""
    found = f"brand_{chain.key}"
    return FeatureId(found) if found in FeatureId else None


MIX_METHOD = Method(
    derivation_id=f"mix_of_tiers_within_{WITHIN}m@1",
    sentence=f"Of the places of a tier within {WITHIN} metres, in a straight line, of the point "
    "where the homes of each census output area are taken to stand, the premium ones and "
    f"{MID_COUNTS} of each mid-range one, over all of them, each added up over the area's homes "
    f"at the census before one is divided by the other, times 100, {at_the_edge(WITHIN)}",
    kind=MadeBy.MEASURED,
    parameters={"metres": WITHIN, "mid_counts": MID_COUNTS, "enough_in_100": 50, "times": 100},
    code=CODE,
)
COUNT_METHOD, SHARE_METHOD = within_at(WITHIN), share_at(WITHIN)
DISTANCE_METHOD = nearest_at(NEAREST_WITHIN)
METHODS: tuple[Method, ...] = (COUNT_METHOD, DISTANCE_METHOD, MIX_METHOD, SHARE_METHOD)

# What the product shows beside a figure. Each line has a name, so that a figure takes a
# line by what it says and never by where it stands.
A_JUDGEMENT = (
    "Which chain is premium, which is mid-range and which is value is Burro's own table, and "
    "a judgement: it says what a chain charges and how it presents itself."
)
PLACES_NOT_PEOPLE = (
    "It counts shops. It says nothing of who shops in one, of who lives near one, or of what "
    "anyone earns."
)
OF_THE_RELEASE = (
    "The day it is as at is the day its publisher released the file, and not the day of each "
    "record: many records of the file were last changed years before it."
)
WHAT_BEARS_A_BRAND = (
    "The file is gathered from what businesses and others have put on the web, and it names "
    "the chain of a place only where its publisher has matched the two, so a place of a chain "
    "that it has not matched is not counted."
)
BY_THE_TABLE = (
    "A place is of a chain where the file writes the chain one of the ways Burro's table "
    "lists, so a place the file writes another way is not counted."
)
BY_CATEGORY = (
    "A place of a chain counts only where the file also says what kind of place it is, so a "
    "bank, a pharmacy or a petrol station of a chain of grocers is no grocer, and the larger "
    "shops of one chain count where the file calls them department stores."
)
ONE_PLACE = (
    f"Places of one chain that stand within {ONE_VENUE} metres of the first of them count as "
    "one place."
)
CLOSED = (
    "A place that has closed is counted unless the file says it has closed for good, which it "
    "says of almost none."
)
A_STRAIGHT_LINE = (
    "It is a straight line from where the homes of each small census area are taken to stand, "
    "and not a walk, so a railway, a river or a main road in between puts a place further off "
    "than it is counted."
)
NOUGHT = (
    "Nought is given only where the file holds something of any kind within reach, and even "
    "there it means that the file lists no such place, which is not the same as there being none."
)
AT_THE_EDGE = (
    "Near the edge of London the homes of a small census area are left out of the figure where "
    "homes outside London are within reach of them, so the figure of an area at the edge rests "
    "on the homes further in."
)
NO_FURTHER = (
    f"The nearest is looked for as far as {NEAREST_WITHIN:,} metres. Where none stands within "
    "that, there is no figure: it is not known how far the nearest is."
)
OVER_HALF = (
    "The figure is of the homes that have such a place within that distance, and is given "
    "where they are half of the area's homes or more, so it reads nearer than the distance "
    "from every home would."
)
FEW_PLACES = (
    "Where few places of a tier are within reach the mix rests on few places, and one shop "
    "more or fewer moves it far."
)
ALL_KINDS_TOGETHER = (
    "Grocers, gyms and coffee are counted together, so the mix follows coffee and grocers, "
    "of which there are many, more than gyms, of which there are few."
)
NOT_EVERY_SOURCE = (
    "A place is counted only where a source that names chains gave it. A place that another "
    "source alone gave is counted on neither side, because the file cannot say whether it is "
    "of a chain."
)
BRAND_IS_NOT_A_CHAIN = (
    "The file gives some places the brand of a business with one shop, and gives no brand to "
    "some places of a chain, so a place is counted as of a chain, or as of none, as the file "
    "has it."
)
_OF_EVERY = (OF_THE_RELEASE, WHAT_BEARS_A_BRAND, A_STRAIGHT_LINE)
_OF_A_TIER = (A_JUDGEMENT, PLACES_NOT_PEOPLE, BY_THE_TABLE, BY_CATEGORY, ONE_PLACE, CLOSED)
CANNOT_SEE_OF_A_COUNT = (*_OF_A_TIER, *_OF_EVERY, NOUGHT, AT_THE_EDGE)
CANNOT_SEE_OF_A_DISTANCE = (*_OF_A_TIER, *_OF_EVERY, NO_FURTHER, OVER_HALF)
CANNOT_SEE_OF_THE_MIX = (*_OF_A_TIER, FEW_PLACES, ALL_KINDS_TOGETHER, *_OF_EVERY, AT_THE_EDGE)
CANNOT_SEE_OF_A_CHAIN = (
    PLACES_NOT_PEOPLE,
    BY_THE_TABLE,
    BY_CATEGORY,
    ONE_PLACE,
    CLOSED,
    *_OF_EVERY,
    NO_FURTHER,
    OVER_HALF,
)
CANNOT_SEE_OF_INDEPENDENT = (
    NOT_EVERY_SOURCE,
    BRAND_IS_NOT_A_CHAIN,
    CLOSED,
    *_OF_EVERY,
    AT_THE_EDGE,
)


class LeftOut(StrEnum):
    """Why a place of a chain of the table is not counted. Each is counted."""

    # The file gives it no category of the chain's kind: a bank of a chain of grocers.
    NOT_OF_ITS_KIND = "not_of_its_kind"
    CLOSED = "closed"
    NO_POINT = "no_point"
    # It stands within a few metres of a place of the same chain that was counted.
    COUNTED_ALREADY = "counted_already"


@dataclass(frozen=True)
class Placed:
    """One place of a chain of the table: where it is, and which chain. It names no place."""

    longitude: float
    latitude: float
    chain: str
    kind: Kind
    tier: Tier
    datasets: tuple[str, ...]


@dataclass(frozen=True)
class Held:
    """What one part of the file of places holds of brands. No name of a place is here."""

    # Every place of a chain of the table that counts, in the order of where it stands.
    places: tuple[Placed, ...]
    # Every place to eat or drink that a source that names chains gave: where it is, and
    # whether the file gives it a brand.
    eating: tuple[tuple[float, float, bool], ...]
    # The point of every record that has one, whatever the record is.
    every: tuple[Point, ...]
    rows: int
    # How many rows bear a brand, and how many of those a brand of the table.
    branded: int
    of_the_table: int
    # For each chain of the table, by its key: the rows the file gives its brand, by the
    # spelling; the places counted; and what was left out, by the reason.
    written: Mapping[str, Mapping[str, int]]
    counted: Mapping[str, int]
    left_out: Mapping[str, Mapping[LeftOut, int]]
    # The sources that name a chain for some place of the file, and how many places to eat
    # or drink no such source gave.
    name_chains: tuple[str, ...]
    eating_of_no_such_source: int
    file: Receipt

    @property
    def as_at(self) -> str:
        """The day the file is as at, as its receipt gives it."""
        return self.file.data_period.days()[1]


def _in_order(placed: Placed) -> tuple[float, float, str, tuple[str, ...]]:
    return (placed.longitude, placed.latitude, placed.chain, placed.datasets)


def as_places(
    found: Sequence[Placed], metres: int = ONE_VENUE
) -> tuple[tuple[Placed, ...], dict[str, int]]:
    """The places that some records are, and how many records were a place again, by chain.

    Records of one chain within so many metres of the first of them are one
    place, which stands where the first stands. The records are taken in the
    order of where they stand, so the order of a file changes nothing.
    """
    places: list[Placed] = []
    again: Counter[str] = Counter()
    for chain in sorted({one.chain for one in found}):
        of_chain = sorted((one for one in found if one.chain == chain), key=_in_order)
        firsts = first_of_each([(one.longitude, one.latitude) for one in of_chain], metres)
        for place, first in enumerate(firsts):
            if first == place:
                places.append(of_chain[place])
            else:
                again[chain] += 1
    return tuple(sorted(places, key=_in_order)), dict(again)


def held_in(rows: Sequence[Branded], table: Table, file: Receipt) -> Held:
    """What some rows of a file of places hold of brands, by the table of tiers."""
    name_chains = tuple(
        sorted(
            {
                name
                for row in rows
                if row.brand is not None
                for name in row.record.datasets
                if name != OWN
            }
        )
    )
    named = frozenset(name_chains)
    found: list[Placed] = []
    eating: list[tuple[float, float, bool]] = []
    written: dict[str, Counter[str]] = {chain.key: Counter() for chain in table.chains}
    left_out: dict[str, Counter[LeftOut]] = {chain.key: Counter() for chain in table.chains}
    of_no_such_source = 0
    for row in rows:
        record, chain = row.record, chain_of(row.brand, table)
        if chain is not None and row.brand is not None:
            written[chain.key][row.brand.name or ""] += 1
            why = (
                LeftOut.NOT_OF_ITS_KIND
                if not is_of_kind(record, chain.kind)
                else LeftOut.CLOSED
                if record.closed
                else LeftOut.NO_POINT
                if record.at is None
                else None
            )
            if why is not None:
                left_out[chain.key][why] += 1
            elif record.at is not None:
                found.append(Placed(*record.at, chain.key, chain.kind, chain.tier, record.datasets))
        if eats_or_drinks(record) and record.at is not None and not record.closed:
            if named.intersection(record.datasets):
                eating.append((record.at[0], record.at[1], row.brand is not None))
            else:
                of_no_such_source += 1
    places, again = as_places(found)
    for key, count in again.items():
        left_out[key][LeftOut.COUNTED_ALREADY] += count
    counted = Counter(one.chain for one in places)
    return Held(
        places=places,
        eating=tuple(sorted(eating)),
        every=tuple(sorted(row.record.at for row in rows if row.record.at is not None)),
        rows=len(rows),
        branded=sum(row.brand is not None for row in rows),
        of_the_table=sum(sum(one.values()) for one in written.values()),
        written={key: dict(sorted(one.items())) for key, one in written.items()},
        counted={chain.key: counted[chain.key] for chain in table.chains},
        left_out={key: dict(sorted(one.items())) for key, one in left_out.items()},
        name_chains=name_chains,
        eating_of_no_such_source=of_no_such_source,
        file=file,
    )


@lru_cache(maxsize=2)
def _read(opened: Opened, table: Table) -> Held:
    return held_in(list(culture_file.branded(opened)), table, opened.receipt)


def read(opened: Opened, table: Table | None = None) -> Held:
    """What the part that holds the brand holds of brands. Stops at a file that is not one.

    Every measure of a build reads the same part by the same table, so what is
    read is kept and handed to the next that asks.
    """
    return _read(opened, the_table() if table is None else table)


@dataclass(frozen=True)
class One:
    """One measure of brands for every area, as the list of the measures of a build takes it."""

    # The figure of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    metric: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    geography: Geography


@dataclass(frozen=True)
class Brands:
    """Every measure of brands for every area, with what stands behind it."""

    # The figures of each measure, by the id of the measure and then of the area.
    worked: Mapping[FeatureId, Mapping[str, Worked]]
    files: tuple[Receipt, ...]
    held: Held
    table: Table
    # What is within reach of each output area that has a count, by slot, and how far the
    # nearest of each tier and of each chain is from each output area that has a distance.
    within: Mapping[str, tuple[int, ...]]
    nearest_of_a_tier: Mapping[str, tuple[float | None, ...]]
    nearest_of_a_chain: Mapping[str, tuple[float | None, ...]]
    # The output areas with no count because the file holds nothing at all within reach.
    nothing_seen: tuple[str, ...]
    geography: Geography

    def one(self, feature: FeatureId) -> One:
        """One measure, with its rows of evidence and its row of the catalogue."""
        worked = self.worked[feature]
        return One(
            worked=worked,
            rows=tuple(
                row_of(
                    fact_id(area, FactKind.FEATURE, feature),
                    worked[area],
                    method_of(feature),
                    self.files,
                )
                for area in sorted(worked)
            ),
            metric=metric_of(feature, self.files, self.held, self.table),
            files=self.files,
            geography=self.geography,
        )


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file these measures read."""
    return culture_file.is_the_file(name)


def of_the_tiers() -> tuple[FeatureId, ...]:
    """The measures of the tiers: how many, and how far the nearest, of each kind and tier."""
    return tuple(
        of_a_tier(kind, tier, what)
        for what in (NEARBY, DISTANCE)
        for kind in KINDS
        for tier in TIERS
    )


# Every measure this module works out, in the order of their ids.
FEATURES: tuple[FeatureId, ...] = tuple(sorted((*of_the_tiers(), MIX, *CHAINS, INDEPENDENT)))


def method_of(feature: FeatureId) -> Method:
    """The arithmetic a measure is worked out by, which its rows of evidence name."""
    if feature is MIX:
        return MIX_METHOD
    if feature is INDEPENDENT:
        return SHARE_METHOD
    if feature in CHAINS or feature.value.endswith(f"_{DISTANCE}"):
        return DISTANCE_METHOD
    return COUNT_METHOD


def cannot_see(feature: FeatureId) -> tuple[str, ...]:
    """What a measure cannot see, as the product says it beside the figure."""
    if feature is MIX:
        return CANNOT_SEE_OF_THE_MIX
    if feature is INDEPENDENT:
        return CANNOT_SEE_OF_INDEPENDENT
    if feature in CHAINS:
        return CANNOT_SEE_OF_A_CHAIN
    if feature.value.endswith(f"_{DISTANCE}"):
        return CANNOT_SEE_OF_A_DISTANCE
    return CANNOT_SEE_OF_A_COUNT


def _named(chains: Sequence[Chain], last: str = "and") -> str:
    """Some chains by name, as a sentence lists them."""
    names = [chain.name for chain in chains]
    if not names:
        return "no chain"
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} {last} {names[-1]}"


# What a place of each kind is, in the words of a sentence, and what the chains of a kind
# are called.
_KIND_IN_WORDS: Mapping[Kind, str] = {
    Kind.GROCER: "a grocery, a convenience store, a frozen food shop, a discount store or a "
    "department store",
    Kind.GYM: "a sport or fitness facility or a health and wellness club",
    Kind.COFFEE: "a place to eat or drink",
}
_CHAINS_OF: Mapping[Kind, str] = {
    Kind.GROCER: "chains of grocers",
    Kind.GYM: "chains of gyms",
    Kind.COFFEE: "chains of coffee",
}
_TIER_IN_WORDS: Mapping[Tier, str] = {
    Tier.PREMIUM: "premium",
    Tier.MID: "mid-range",
    Tier.VALUE: "value",
}
_RELEASE = "release {release} of Overture Maps Places, of the {publisher}, as at {as_at}"
_WHERE = (
    "in a straight line of the point the statistics office gives as the centre of each census "
    "output area"
)
_FROM_HOME = "from the point the statistics office gives as the centre of each census output area"
_NOUGHT = (
    "with nought read as a count only where the file holds a record of any kind within the "
    "same distance"
)
_UPWARD = "with a half taken upward"
_THE_TABLE = "by Burro's own table of tiers, which is a judgement and no finding"
_OF_THE_SHARE = (
    "each added up over the area's homes at the census of {census} before one is divided by "
    "the other"
)
_LEFT_OUT = "a place the file says has closed for good is left out"


def _kind_and_tier(feature: FeatureId) -> tuple[Kind, Tier]:
    kind, tier, _ = feature.value.split("_")
    return Kind(kind), Tier(tier)


def _a_place_is(release: str, kind: str) -> str:
    """How a place comes to be counted as a place of a chain, as a sentence ends with it."""
    return (
        f"a place is of a chain where {release} gives it the brand of the chain and a category "
        f"of {kind}, {_LEFT_OUT}, and places of one chain within {ONE_VENUE} metres of the "
        "first of them are one place"
    )


def _a_distance(to: str, ends: str) -> str:
    """The sentence of a distance to the nearest place of some chains."""
    return (
        f"The distance in a straight line, in metres, {_FROM_HOME} to the nearest place of "
        f"{to}, where one stands within {NEAREST_WITHIN:,} metres, as the median over the "
        f"area's homes at the census of {CENSUS} that have one, and given to the nearest "
        f"{park_proximity.NEAREST} metres {_UPWARD}: {ends}."
    )


def definition_of(feature: FeatureId, held: Held, table: Table) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    release = _RELEASE.format(release=held.file.edition, publisher=PUBLISHER, as_at=held.as_at)
    added_up = _OF_THE_SHARE.format(census=CENSUS)
    rounded = f"given to {DECIMALS} decimal place {_UPWARD}"
    if feature is INDEPENDENT:
        return (
            f"Of the places to eat and drink within {WITHIN} metres {_WHERE}, the share to "
            f"which the file gives no brand, {added_up}, {_NOUGHT}, and {rounded}: a place to "
            f"eat or drink is one that {release} files under food and drink and that a source "
            f"that names the chain of some place gave, and {_LEFT_OUT}."
        )
    if feature is MIX:
        tiers = ", ".join(
            f"{_TIER_IN_WORDS[tier]} are {_named([c for c in table.chains if c.tier is tier])}"
            for tier in TIERS
        )
        return (
            f"Of the places of a chain that is on Burro's own table of tiers within {WITHIN} "
            f"metres {_WHERE}, the share that are premium, with a mid-range place counted as "
            f"{MID_COUNTS} of one, {added_up}, {_NOUGHT}, and {rounded}: the table is a "
            f"judgement and no finding, by it {tiers}, and "
            f"{_a_place_is(release, 'the kind of the chain')}."
        )
    if feature in CHAINS:
        chain = table.by_key.get(feature.value.removeprefix("brand_"))
        kind = _KIND_IN_WORDS[chain.kind] if chain is not None else "the kind of the chain"
        return _a_distance(CHAINS[feature].name, _a_place_is(release, kind))
    kind, tier = _kind_and_tier(feature)
    chains = (
        f"{_named(table.of(kind, tier), 'or')}, which are the {_CHAINS_OF[kind]} that are "
        f"{_TIER_IN_WORDS[tier]} {_THE_TABLE}"
    )
    if feature.value.endswith(f"_{DISTANCE}"):
        return _a_distance(chains, _a_place_is(release, _KIND_IN_WORDS[kind]))
    return (
        f"The number of places of {chains}, within {WITHIN} metres {_WHERE}, as the mean over "
        f"the area's homes at the census of {CENSUS}, {_NOUGHT}, and {rounded}: "
        f"{_a_place_is(release, _KIND_IN_WORDS[kind])}."
    )


def metric_of(feature: FeatureId, files: Sequence[Receipt], held: Held, table: Table) -> Metric:
    """The row of the catalogue of one measure: the name, the unit, the day and every source.

    Core decides the name, the unit and which way is more. A measure of a
    tier is shown and no area is ranked on it: the mix is what is ranked on.
    """
    return catalogue_row(
        feature,
        method=method_of(feature),
        native_resolution=NativeResolution.POINT,
        source_ids={receipt.source_id for receipt in files},
        vintage=held.as_at,
        rankable=feature not in SHOWN_BESIDE_THE_MIX,
        definition=definition_of(feature, held, table),
    )


def points_of(held: Held) -> list[Weighed]:
    """Every place that is counted within reach, each with the slot it adds to."""
    return [
        *((one.longitude, one.latitude, slot_of(one.kind, one.tier), 1) for one in held.places),
        *(
            (longitude, latitude, OF_A_CHAIN if of_a_chain else OF_NO_CHAIN, 1)
            for longitude, latitude, of_a_chain in held.eating
        ),
        *((longitude, latitude, EVERY, 1) for longitude, latitude in held.every),
    ]


def _share(
    top: Mapping[str, float], bottom: Mapping[str, float], found: Spine
) -> dict[str, Worked]:
    """One sum over another as a share of 100, each added up over the homes of every area."""
    weighed_top = {oa: found.homes[oa] * count for oa, count in top.items()}
    weighed_bottom = {oa: found.homes[oa] * count for oa, count in bottom.items()}
    unit_of = {oa: oa for oa in found.area_of}
    return given(
        lsoa_ratio_by_homes(weighed_top, weighed_bottom, unit_of, found.weights, times=100.0)
    )


def _distances(
    nearest: Mapping[str, tuple[float | None, ...]], slot: int, found: Spine
) -> dict[str, Worked]:
    """The distance to the nearest of one slot for every area, as the median over its homes."""
    of_oa = {oa: far[slot] for oa, far in nearest.items()}
    return park_proximity.figures({oa: far for oa, far in of_oa.items() if far is not None}, found)


def worked_out(
    held: Held,
    table: Table,
    centred: Sequence[tuple[str, Point, int]],
    beyond: Sequence[Point],
    found: Spine,
) -> tuple[
    dict[FeatureId, dict[str, Worked]],
    dict[str, tuple[int, ...]],
    dict[str, tuple[float | None, ...]],
    dict[str, tuple[float | None, ...]],
    tuple[str, ...],
]:
    """Every figure of every area, from the places of the file and the centres of the build."""
    reach = reach_at(points_of(held), SLOTS, centred, beyond, WITHIN)
    seen = {oa: counts for oa, counts in reach.within.items() if counts[EVERY] >= SEEN}
    taken = held.file.taken
    box = None if taken is None else taken.box
    chains = [chain for chain in table.chains if feature_of(chain) is not None]
    place_of = {chain.key: place for place, chain in enumerate(chains)}
    of_a_tier_at = nearest_of(
        ((o.longitude, o.latitude, slot_of(o.kind, o.tier), 1) for o in held.places),
        OF_NO_CHAIN,
        centred,
        NEAREST_WITHIN,
        box,
    )
    of_a_chain_at = nearest_of(
        (
            (o.longitude, o.latitude, place_of[o.chain], 1)
            for o in held.places
            if o.chain in place_of
        ),
        len(chains),
        centred,
        NEAREST_WITHIN,
        box,
    )
    worked: dict[FeatureId, dict[str, Worked]] = {}
    for kind in KINDS:
        for tier in TIERS:
            slot = slot_of(kind, tier)
            worked[of_a_tier(kind, tier, NEARBY)] = figures(
                {oa: float(counts[slot]) for oa, counts in seen.items()}, found
            )
            worked[of_a_tier(kind, tier, DISTANCE)] = _distances(of_a_tier_at, slot, found)
    for chain in chains:
        feature = feature_of(chain)
        assert feature is not None
        worked[feature] = _distances(of_a_chain_at, place_of[chain.key], found)
    # A chain core names and the table does not hold has a figure nowhere.
    for feature in CHAINS:
        worked.setdefault(feature, _distances({}, 0, found))

    def of_tier(counts: Sequence[int], tier: Tier) -> float:
        return float(sum(counts[slot_of(kind, tier)] for kind in KINDS))

    worked[MIX] = _share(
        {
            oa: of_tier(counts, Tier.PREMIUM) + MID_COUNTS * of_tier(counts, Tier.MID)
            for oa, counts in seen.items()
        },
        {oa: float(sum(counts[:OF_NO_CHAIN])) for oa, counts in seen.items()},
        found,
    )
    worked[INDEPENDENT] = _share(
        {oa: float(counts[OF_NO_CHAIN]) for oa, counts in seen.items()},
        {oa: float(counts[OF_NO_CHAIN] + counts[OF_A_CHAIN]) for oa, counts in seen.items()},
        found,
    )
    nothing_seen = tuple(sorted(set(reach.within) - set(seen)))
    return worked, dict(seen), of_a_tier_at, of_a_chain_at, nothing_seen


# What was worked out last, by what it was worked out from: the part of the file, the
# table, the centres and the spine. Every measure of a build asks the same of the same.
_KEPT: dict[tuple[object, ...], Brands] = {}


def _built(
    held: Held,
    table: Table,
    centred: tuple[tuple[str, Point, int], ...],
    beyond: tuple[Point, ...],
    found: Spine,
    files: tuple[Receipt, ...],
) -> Brands:
    known_by = (held.file.sha256, table, centred, beyond, found.inputs, files)
    if known_by not in _KEPT:
        worked, within, of_a_tier_at, of_a_chain_at, nothing_seen = worked_out(
            held, table, centred, beyond, found
        )
        _KEPT.clear()
        _KEPT[known_by] = Brands(
            worked=worked,
            files=files,
            held=held,
            table=table,
            within=within,
            nearest_of_a_tier=of_a_tier_at,
            nearest_of_a_chain=of_a_chain_at,
            nothing_seen=nothing_seen,
            geography=KEYED_BY,
        )
    return _KEPT[known_by]


def build(
    inputs: Inputs, found: Spine, *, edition: str | None = None, table: Table | None = None
) -> Brands:
    """Every measure of brands for every area, from the files of the build.

    The gate is asked about the places and about the centres before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the places and the centres, so they must be files this build
    opened. `edition` is the release of the places, as its receipt gives it.
    Every measure of a build asks the same of the same files, so what is
    worked out is kept and handed to the next that asks.
    """
    opened = culture_file.opened_with_the_brand(inputs, edition=edition)
    held = read(opened, table)
    ground = ground_of(inputs, found, WITHIN)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    behind = sorted({held.file.file_id, ground.placed.file_id, *found.inputs})
    centred = tuple((oa, ground.at[oa], found.homes[oa]) for oa in sorted(ground.at))
    return _built(
        held,
        the_table() if table is None else table,
        centred,
        tuple(ground.beyond),
        found,
        tuple(handed[file_id] for file_id in behind),
    )


def builder(feature: FeatureId) -> Callable[[Inputs, Spine], One]:
    """One measure, called as the list of the measures of a build calls each."""
    if feature not in FEATURES:
        raise ValueError(f"{feature} is no measure of brands")
    return lambda inputs, found: build(inputs, found).one(feature)


__all__ = ["Brands", "Held", "One", "build", "builder", "read"]
