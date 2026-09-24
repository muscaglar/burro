"""Buildings of the kinds of one table, counted within reach of where homes are.

Two measures count what is there from the file of places: places of worship,
and community and cultural centres. Each has a table of its own that says
which of the publisher's categories is which kind. This module is what the
two share, so that both are counted one way. It holds no table and no kind.

It asks for everything else:

- The file is read by `culture_file.records`, which reads the columns that
  culture reads and no other. No name is read.
- What is within reach, the mean over homes and the edge of London are
  `culture_reach.py`'s, as for cultural venues.
- The distance at which records are one building is `culture_venues.ONE_VENUE`.

**A figure is a count of buildings.** For each area it is the number of
buildings of a kind within 800 metres of home, in a straight line, as the
mean over the area's homes. Nothing here divides a count by anything, sets
one kind against another, or adds the kinds up by weights. The one sum that
is made is the plain number of buildings of every kind of the table.

**One building with many records counts once, where they stand together.**
Records of one kind that stand within 25 metres of the first of them are one
building. The records are taken from west to east, so the same file gives the
same buildings, and the first is the most westerly. A record of the same
building that stands further than that from the first is a building again: five
records that each stand within 20 metres of the middle of one building are
four buildings. So `close_together` counts the buildings of each kind that
stand within 50 metres of another of the same kind, for a person to look at.
It changes no figure.

**What is handed back holds no count of homes.** The reach of cultural venues
holds how many homes are within the same reach, and says how many kinds are
within it. Neither is handed on. A count of buildings for each so many homes
would stand in for who lives somewhere, and how many kinds are near would say
how mixed a place is. `Within` holds the counts and nothing else.

**The kinds are added up only where a measure asks.** Places of worship are
one thing of several kinds, and their plain number is a figure. A community
centre and a cultural centre are two things, and no figure is both.

**When nought is a count.** As for cultural venues: nought is read as a count
only where the file holds a record of any kind within the same reach. Where
it holds none, the output area has no count and the coverage of its area
falls by its homes.

**Does a count say something.** A first look at the file found that a count
of one kind of place stands in almost the order of a count of everything the
file holds. `held_against_the_centre` asks it of each figure, as
`culture_check.py` asks it of culture: against homes per hectare, against how
far an area's homes are from the middle of London's homes, and against a
count of every record within the same reach.

A refusal names the file by its id and the rule. It repeats nothing the file
holds.
"""

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from burro_core.facts import fact_id
from burro_core.ids import (
    Describes,
    Dimension,
    FactKind,
    FeatureKind,
    NativeResolution,
    Polarity,
)

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file
from burro_pipeline.derive.culture_check import Held as HeldAgainst
from burro_pipeline.derive.culture_check import distance_from_the_middle, held_against
from burro_pipeline.derive.culture_file import Point, Record
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.culture_reach import (
    METRES,
    Ground,
    figures,
    first_of_each,
    kept,
    reach_of,
    within,
    within_at,
)
from burro_pipeline.derive.culture_venues import ONE_VENUE, SEEN
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Opened

# A figure is a count of buildings, and the one way a person may ask for it is more.
UNIT = "count"
METHOD: Method = within_at(METRES)
# Why a record of a kind is not counted, whatever the table. Each is counted.
CLOSED, NO_POINT = "closed", "no_point"
# How near another of its kind a building stands for a person to look at it again, in whole
# metres: twice the distance at which records are one building. It is a choice.
CLOSE = 2 * ONE_VENUE

# What a table says a record is: one of its kinds, or why it is none.
Decide = Callable[[Record], StrEnum]


@dataclass(frozen=True)
class Building:
    """One record of a kind, or one building that several records are."""

    longitude: float
    latitude: float
    kind: str
    datasets: tuple[str, ...]
    # How sure the publisher is that the place exists, from 0 to 1. None where it says nothing.
    confidence: float | None


def in_order(one: Building) -> tuple[float, float, str, tuple[str, ...], bool, float]:
    """Where a record stands among the records of a file: from west to east, then by what it is."""
    sure = one.confidence
    return (
        one.longitude,
        one.latitude,
        one.kind,
        one.datasets,
        sure is not None,
        0.0 if sure is None else sure,
    )


@dataclass(frozen=True)
class Held:
    """What one file of places holds of the kinds of one table. No name of a place is here."""

    # Every record of a kind, in the order of where it stands.
    records: tuple[Building, ...]
    # The point of every record that has one, whatever the record is.
    every: tuple[Point, ...]
    # How many rows were read, and how many of them were left out, by the reason.
    rows: int
    left_out: Mapping[str, int]
    # The records of a kind by their most particular category, and the records that the
    # table names and leaves out by theirs. A category is the publisher's word.
    counted_as: Mapping[str, int]
    left_out_as: Mapping[str, int]
    file: Receipt

    @property
    def by_kind(self) -> dict[str, int]:
        return dict(sorted(Counter(one.kind for one in self.records).items()))

    @property
    def by_dataset(self) -> dict[str, int]:
        found = Counter(name for one in self.records for name in one.datasets)
        return dict(sorted(found.items()))

    @property
    def as_at(self) -> str:
        """The day the file is as at, as its receipt gives it."""
        return self.file.data_period.days()[1]


def read(
    opened: Opened,
    decide: Decide,
    kinds: Sequence[StrEnum],
    passed_by: Sequence[StrEnum],
) -> Held:
    """What a file of places holds of the kinds of one table.

    `decide` is the table's rule. `kinds` are what it counts. `passed_by` are
    its reasons for a record that is nothing of the table's, which is most of
    any file: such a record is counted by the reason and not by its category.
    Stops at a category that the table should hold and does not.
    """
    records: list[Building] = []
    every: list[Point] = []
    left_out: Counter[str] = Counter()
    counted_as: Counter[str] = Counter()
    left_out_as: Counter[str] = Counter()
    rows = 0
    by_reason_alone = {reason.value for reason in passed_by}
    for record in culture_file.records(opened):
        rows += 1
        if record.at is not None:
            every.append(record.at)
        try:
            found = decide(record)
        except NotOnTheTable:
            raise LockError(
                "input_is_as_described",
                opened.file_id,
                "it holds a category that the table of kinds should hold and does not",
            ) from None
        why = None if found in kinds else found.value
        if why is None and record.closed:
            why = CLOSED
        if why is None and record.at is None:
            why = NO_POINT
        if why is not None:
            left_out[why] += 1
            if why not in by_reason_alone:
                left_out_as[str(record.primary)] += 1
            continue
        assert record.at is not None
        records.append(
            Building(record.at[0], record.at[1], found.value, record.datasets, record.confidence)
        )
        counted_as[str(record.primary)] += 1
    return Held(
        records=tuple(sorted(records, key=in_order)),
        every=tuple(sorted(every)),
        rows=rows,
        left_out=dict(sorted(left_out.items())),
        counted_as=dict(sorted(counted_as.items())),
        left_out_as=dict(sorted(left_out_as.items())),
        file=opened.receipt,
    )


def as_buildings(
    records: Sequence[Building], kinds: Sequence[str], metres: int = ONE_VENUE
) -> tuple[tuple[Building, ...], dict[str, int]]:
    """The buildings that some records are, and how many records were a building again, by kind.

    Records of one kind within so many metres of the first of them are one
    building, which stands where the first stands and keeps every source that
    gave a record of it. The records are taken in the order of where they
    stand, so the order of a file changes nothing.
    """
    buildings: list[Building] = []
    again: Counter[str] = Counter()
    for kind in kinds:
        of_kind = sorted((one for one in records if one.kind == kind), key=in_order)
        firsts = first_of_each([(one.longitude, one.latitude) for one in of_kind], metres)
        sources: dict[int, set[str]] = {}
        for place, first in enumerate(firsts):
            sources.setdefault(first, set()).update(of_kind[place].datasets)
            again[kind] += first != place
        buildings += [
            Building(
                of_kind[first].longitude,
                of_kind[first].latitude,
                kind,
                tuple(sorted(sources[first])),
                of_kind[first].confidence,
            )
            for first in sorted(sources)
        ]
    return (
        tuple(sorted(buildings, key=in_order)),
        {kind: again[kind] for kind in kinds if again[kind]},
    )


def close_together(
    buildings: Sequence[Building], kinds: Sequence[str], metres: int = CLOSE
) -> dict[str, int]:
    """How many buildings of each kind stand within so many metres of another of the same kind.

    It is where one building may have been counted more than once: records of
    it that stand further apart than the rule of one building allows. It is
    also where two buildings of one kind stand side by side. Which it is, a
    person says. It changes no figure, and a kind with none is left out.
    """
    found: dict[str, int] = {}
    for kind in kinds:
        of_kind = [one for one in buildings if one.kind == kind]
        held = kept((one.longitude, one.latitude, 0, 1) for one in of_kind)
        found[kind] = sum(
            within(held, (one.longitude, one.latitude), metres, 1)[0] > 1 for one in of_kind
        )
    return {kind: count for kind, count in found.items() if count}


@dataclass(frozen=True)
class Within:
    """What stands within reach of where the homes of each output area are taken to stand.

    It holds counts of buildings and nothing else. How many homes are within
    the same reach is not here, so no count can be set over it, and nothing
    here says how many of the kinds hold anything.
    """

    metres: int
    # For each output area with a verdict: what is within reach, in each slot. The last slot
    # holds every record of the file, whatever it is.
    within: Mapping[str, tuple[int, ...]]
    # The output areas with a centre, and with no verdict: a centre outside London lies
    # within their reach.
    near_the_edge: tuple[str, ...]

    def of(self, slots: Iterable[int]) -> dict[str, float]:
        """What some slots add up to within reach of each output area that has a verdict."""
        wanted = tuple(slots)
        return {oa: float(sum(held[n] for n in wanted)) for oa, held in self.within.items()}


@dataclass(frozen=True)
class Nearby:
    """The buildings of each kind within reach of where homes are, for every area."""

    kinds: tuple[str, ...]
    reach: Within
    # The count of each kind for each area, by the kind and then by the id of the area. An
    # area with no figure is here too, with its state.
    of_kind: Mapping[str, Mapping[str, Worked]]
    # The output areas that have a count: the file holds something within reach of each.
    seen: tuple[str, ...]
    # The output areas with no count because the file holds nothing at all within reach.
    nothing_seen: tuple[str, ...]
    # The buildings of every kind of the table, for each area. It is the plain number of
    # buildings, each counted once, and nothing else is added up. None where the kinds of a
    # table are two things, which are never added up.
    of_all: Mapping[str, Worked] | None
    # For each output area that has a count: the buildings of every kind within reach. None
    # where the kinds are never added up.
    counted: Mapping[str, float] | None


def nearby(
    buildings: Sequence[Building],
    every: Sequence[Point],
    kinds: Sequence[str],
    ground: Ground,
    found: Spine,
    *,
    added_up: bool,
) -> Nearby:
    """Count the buildings of each kind within reach of where the homes of each area stand.

    With `added_up`, the plain number of buildings of every kind is given too.
    """
    slots = len(kinds)
    points = [
        *((one.longitude, one.latitude, kinds.index(one.kind), 1) for one in buildings),
        *((longitude, latitude, slots, 1) for longitude, latitude in every),
    ]
    reached = reach_of(points, slots + 1, ground, found)
    reach = Within(reached.metres, reached.within, reached.near_the_edge)
    seen = {oa for oa, held in reach.within.items() if held[slots] >= SEEN}
    of_kind = {
        kind: figures({oa: count for oa, count in reach.of((slot,)).items() if oa in seen}, found)
        for slot, kind in enumerate(kinds)
    }
    counted = (
        {oa: count for oa, count in reach.of(range(slots)).items() if oa in seen}
        if added_up
        else None
    )
    return Nearby(
        kinds=tuple(kinds),
        reach=reach,
        of_kind=of_kind,
        seen=tuple(sorted(seen)),
        nothing_seen=tuple(sorted(set(reach.within) - seen)),
        of_all=None if counted is None else figures(counted, found),
        counted=counted,
    )


def held_against_the_centre(
    figures_of: Mapping[str, Mapping[str, Worked]],
    counted: Nearby,
    found: Spine,
    density: Mapping[str, float | None],
    ground: Ground,
) -> tuple[HeldAgainst, ...]:
    """Each figure held against how built up and how central each area is, by rank correlation.

    `figures_of` holds the figures of every area under the id of each, and
    `density` the homes per hectare of each area, from the measure of homes of
    the same build. What comes back holds numbers, and no name of an area.
    """
    slot = len(counted.kinds)
    seen = {oa: float(counted.reach.within[oa][slot]) for oa in counted.seen}
    every: dict[str, float | None] = {area: one.value for area, one in figures(seen, found).items()}
    far: dict[str, float | None] = dict(distance_from_the_middle(found, ground.at))
    return tuple(
        held_against(key, {area: one.value for area, one in worked.items()}, density, far, every)
        for key, worked in figures_of.items()
    )


def rows_of(
    key: str, worked: Mapping[str, Worked], files: Sequence[Receipt]
) -> tuple[EvidenceRow, ...]:
    """The row of evidence behind the figure of every area, under one key."""
    return tuple(
        row_of(fact_id(area, FactKind.FEATURE, key), worked[area], METHOD, files)
        for area in sorted(worked)
    )


@dataclass(frozen=True)
class Proposed:
    """What a row of the catalogue would say, once core holds the figure. It is the row of no
    release: core decides the name, the unit and what a person may ask of a figure.
    """

    key: str
    label: str
    # The wish as a person is offered it. It asks for the building nearby, and never for fewer.
    short_label: str
    dimension: Dimension
    unit: str
    polarity: Polarity
    kind: FeatureKind
    describes: Describes
    native_resolution: NativeResolution
    source_ids: tuple[str, ...]
    vintage: str
    # Whether an area may be put in order by it alone. No figure is, until it has been held
    # against the real file.
    rankable: bool
    # Whether any vibe may hold it as a part, and whether likeness may be counted on it.
    in_a_vibe: bool
    in_likeness: bool
    definition: str


def proposed(
    key: str,
    label: str,
    short_label: str,
    definition: str,
    files: Sequence[Receipt],
    vintage: str,
    *,
    kind: FeatureKind,
    in_a_vibe: bool,
) -> Proposed:
    """One row the catalogue would hold. More is the one direction, and nothing is ranked on yet."""
    return Proposed(
        key=key,
        label=label,
        short_label=short_label,
        dimension=Dimension.SERVICES,
        unit=UNIT,
        polarity=Polarity.MORE,
        kind=kind,
        describes=Describes.BUILDINGS,
        native_resolution=NativeResolution.POINT,
        source_ids=tuple(sorted({receipt.source_id for receipt in files})),
        vintage=vintage,
        rankable=False,
        in_a_vibe=in_a_vibe,
        in_likeness=False,
        definition=definition,
    )
