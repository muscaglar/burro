"""Candidate names: every name of a place that a publisher's file holds, and which are one place.

A candidate is one record of one file: the name as the publisher writes it,
who publishes it, the kind of place in the publisher's own word, where it is,
and the file it came from. A name is never changed, corrected, shortened or
translated. Nothing here comes from anywhere but a file: no name and no place
is supplied by whoever wrote this, or by a model.

**What is the same place.** Two records are one place when their names are
the same and they lie within 1 km of each other. The design gives the 1 km,
as the check on any group of records taken to be one place. On the files of
the first draft it kept apart six town centres and the populated place of
the same name and borough, each 1.0 to 1.5 km off. So a second test was
added, and is marked wherever it is what joined two records: the town centre
lies wholly in the box that Ordnance Survey draws round the place. Names are
the same when they fold to the same words: case, apostrophes and other marks
are left out of the comparison, and `&` is read as `and`. A publisher's word
for the kind of thing it lists is left out too: every ward's name ends in the
word for a ward. The fold is for comparing. What is kept and shown is always
the name as written.

**What a label holds.** A publisher may write several names in one label, or a
name with other words beside it. So a record is matched to a name in one of
four ways, and the way is kept:

| Match | The record's label | Counts as the publisher writing the name |
|---|---|---|
| `same` | Is the name | Yes |
| `part` | Is several names, and one of them is the name | Yes |
| `held` | Holds the name as whole words, with other words beside it | No. It adds points |
| `holds` | Is held by the name as whole words | No. It is a lead for a person |

A label is several names when a stroke, a comma, a bracket or `and` parts it.

A place is known by one record, its key: the populated place of OS Open
Names, or, for a name that only the file of town centres holds, the town
centre. A ward is never a key: its name is read for what it adds to a place.
"""

import dataclasses
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from burro_pipeline.areas import names_centres, names_places, names_shapes, names_wards
from burro_pipeline.areas.names_centres import Centre
from burro_pipeline.areas.names_files import File
from burro_pipeline.areas.names_ground import London
from burro_pipeline.areas.names_places import Names, Record
from burro_pipeline.areas.names_shapes import Ground
from burro_pipeline.areas.names_wards import Outlined
from burro_pipeline.cells.shapes import Point, Shape

# Two records of one name are one place when they lie this near each other. Section 7 of
# the areas design.
SAME_PLACE_METRES = 1_000.0
# What a publisher writes after a name for the kind of thing it lists. Each is in the file
# that uses it: the ending of every ward, of nearly every borough, and the layer and a class
# of the file of town centres.
ENDINGS: Mapping[str, tuple[str, ...]] = {
    names_wards.SOURCE: (names_wards.WARD_ENDS, names_wards.BOROUGH_ENDS),
    names_centres.SOURCE: (" Town Centre", " District Centre"),
}
WORD = re.compile(r"[^\W_]+")
PARTED = re.compile(r"[/,()]|\s-\s")
JOINED = re.compile(r"\s(?:and|&)\s", re.IGNORECASE)

POINT, OUTLINE = "point", "outline"
WARD, BOROUGH = "ward", "borough"


class Match(StrEnum):
    SAME = "same"
    PART = "part"
    HELD = "held"
    HOLDS = "holds"


# The matches that count as a publisher writing a name.
WRITES = frozenset({Match.SAME, Match.PART})
# The matches by which a label carries a name, as the design says of a ward.
CARRIES = frozenset({Match.SAME, Match.PART, Match.HELD})


def fold(text: str) -> str:
    """A name as it is compared, and never as it is shown."""
    plain = text.casefold().replace("&", " and ").replace("\N{RIGHT SINGLE QUOTATION MARK}", "'")
    return " ".join(WORD.findall(plain.replace("'", "")))


def core(label: str, endings: Sequence[str] = ()) -> str:
    """A label without the publisher's word for the kind of thing it lists."""
    for ending in endings:
        if label.casefold().endswith(ending.casefold()) and len(label) > len(ending):
            return label[: -len(ending)]
    return label


def parts(label: str) -> tuple[str, ...]:
    """The names a label of several names is made of, each folded. Nothing for a plain label."""
    first = [part for part in PARTED.split(label) if fold(part)]
    found = list(first) if len(first) > 1 else []
    for part in first:
        second = [each for each in JOINED.split(part) if fold(each)]
        if len(second) > 1:
            found += second
    return tuple(dict.fromkeys(fold(part) for part in found))


def _within(words: str, held_in: str) -> bool:
    """Whether some words stand in others, whole and in order."""
    return f" {words} " in f" {held_in} " and words != held_in


def match(name: str, label: str, endings: Sequence[str] = ()) -> Match | None:
    """How a record's label writes a name, or nothing if it does not."""
    wanted, given = fold(name), fold(core(label, endings))
    if not wanted or not given:
        return None
    if wanted == given:
        return Match.SAME
    if wanted in parts(core(label, endings)):
        return Match.PART
    if _within(wanted, given):
        return Match.HELD
    if _within(given, wanted):
        return Match.HOLDS
    return None


@dataclass(frozen=True)
class Candidate:
    """One record of one publisher's file that names a place in London."""

    file: File
    record_id: str
    # The name, exactly as the record holds it, and the column it was read from.
    as_written: str
    field: str
    # The kind of place, in the publisher's own word.
    kind: str
    # Whether the record gives a point or an outline.
    gives: str
    # Where it is, on the National Grid: the point, or a point inside the outline.
    at: Point
    # The output area that holds that point, and the borough of that output area.
    cell: str
    borough: str
    # The outline, where the record gives one. It is never written down.
    shape: Shape | None = dataclasses.field(default=None, compare=False, repr=False)

    @property
    def source_id(self) -> str:
        return self.file.source_id

    @property
    def publisher(self) -> str:
        return self.file.publisher

    @property
    def key(self) -> tuple[str, str, str]:
        return self.source_id, self.record_id, self.field

    def metres_from_shape(self, shape: Shape) -> float:
        """How far this record is from an outline."""
        if self.shape is not None:
            return names_shapes.metres_apart(self.shape, shape)
        return names_shapes.metres_from(shape, self.at)

    def metres_from(self, other: "Candidate") -> float:
        """How far this record is from another: between outlines, or points, or one of each."""
        if self.shape is not None and other.shape is not None:
            return names_shapes.metres_apart(self.shape, other.shape)
        if self.shape is not None:
            return names_shapes.metres_from(self.shape, other.at)
        if other.shape is not None:
            return names_shapes.metres_from(other.shape, self.at)
        return ((self.at[0] - other.at[0]) ** 2 + (self.at[1] - other.at[1]) ** 2) ** 0.5


@dataclass(frozen=True)
class Written:
    """One record that writes the name of a place, or holds it, and how far off it lies."""

    candidate: Candidate
    match: Match
    metres: float

    @property
    def writes(self) -> bool:
        return self.match in WRITES

    @property
    def beyond(self) -> bool:
        """Whether the record lies further off than the design takes one place to reach."""
        return self.metres > SAME_PLACE_METRES


@dataclass(frozen=True)
class Place:
    """One place: the record it is known by, and every other record of its name."""

    key: Candidate
    # Every other record whose label writes or holds the name, the nearest first.
    others: tuple[Written, ...] = ()
    # The record of OS Open Names, where the place is known by one.
    record: Record | None = None
    # The town centre, where the place is known by one.
    centre: Centre | None = None
    # How many road records give the place as their settlement.
    roads: int = 0

    @property
    def name(self) -> str:
        """The name, spelt as the design asks: as the key's publisher writes it."""
        return self.key.as_written

    @property
    def at(self) -> Point:
        return self.key.at

    @property
    def publishers(self) -> tuple[str, ...]:
        """Who writes the name: the key's publisher, and any other whose record writes it."""
        found = {self.key.publisher} | {
            other.candidate.publisher for other in self.others if other.writes
        }
        return tuple(sorted(found))

    def written_by(self, source_id: str) -> tuple[Written, ...]:
        return tuple(other for other in self.others if other.candidate.source_id == source_id)


@dataclass(frozen=True)
class Candidates:
    """Every candidate of London, the places they make, and what was left out."""

    places: tuple[Place, ...]
    # Every record that names a place: populated places, town centres, wards and boroughs.
    records: tuple[Candidate, ...]
    # Railway stations. They are no candidates, and are kept for a person to compare with.
    stations: tuple[Candidate, ...]
    # Records whose point or outline is in no output area of London, by source.
    outside: Mapping[str, int]


def _placed(london: London, at: Point, shape: Shape | None = None) -> tuple[str, str] | None:
    """The output area and the borough of a point, or of the nearest part of an outline."""
    cell = london.cell_of(at)
    if cell is None and shape is not None:
        touching = london.ground.near(shape, 0.0)
        cell = touching[0][1] if touching else None
    return None if cell is None else (cell, london.borough_of[cell])


def of_records(
    london: London, file: File, records: Iterable[Record]
) -> tuple[list[tuple[Candidate, Record]], int]:
    """The records of OS Open Names that are in London, as candidates, and how many are not."""
    found: list[tuple[Candidate, Record]] = []
    outside = 0
    for record in records:
        placed = _placed(london, record.at)
        if placed is None:
            outside += 1
            continue
        found.append(
            (
                Candidate(
                    file,
                    record.record_id,
                    record.name,
                    names_places.NAME,
                    record.kind,
                    POINT,
                    record.at,
                    *placed,
                ),
                record,
            )
        )
    return found, outside


def of_centres(
    london: London, file: File, centres: Iterable[Centre]
) -> tuple[list[tuple[Candidate, Centre]], int]:
    found: list[tuple[Candidate, Centre]] = []
    outside = 0
    for centre in centres:
        placed = _placed(london, centre.at, centre.shape)
        if placed is None:
            outside += 1
            continue
        found.append(
            (
                Candidate(
                    file,
                    centre.record_id,
                    centre.name,
                    names_centres.NAME,
                    centre.rank,
                    OUTLINE,
                    centre.at,
                    *placed,
                    shape=centre.shape,
                ),
                centre,
            )
        )
    return found, outside


def of_outlined(london: London, file: File, outlined: Iterable[Outlined]) -> list[Candidate]:
    """The wards or the boroughs of Boundary-Line, as candidates. Each is London's by its code."""
    found: list[Candidate] = []
    for each in outlined:
        placed = _placed(london, each.inside, each.shape)
        if placed is not None:
            found.append(
                Candidate(
                    file,
                    each.record_id,
                    each.name,
                    names_wards.NAME,
                    each.kind,
                    OUTLINE,
                    each.inside,
                    *placed,
                    shape=each.shape,
                )
            )
    return found


def _nearby(
    key: Candidate, near: Sequence[tuple[float, Candidate]], allowed: frozenset[Match]
) -> list[Written]:
    """The records near a place whose label writes or holds its name, the nearest first."""
    found: list[Written] = []
    for metres, other in near:
        how = match(key.as_written, other.as_written, ENDINGS.get(other.source_id, ()))
        if how is not None and how in allowed:
            found.append(Written(other, how, metres))
    return sorted(found, key=lambda each: (each.metres, each.candidate.key))


class _Near:
    """The records of one source that give an outline, asked which lie near a record."""

    def __init__(self, records: Sequence[Candidate]) -> None:
        self._by_id = {record.record_id: record for record in records}
        self._ground = Ground(
            {record.record_id: record.shape for record in records if record.shape is not None}
        )

    def of(self, key: Candidate) -> list[tuple[float, Candidate]]:
        if key.shape is None:
            near = self._ground.within(key.at, SAME_PLACE_METRES)
        else:
            near = self._ground.near(key.shape, SAME_PLACE_METRES)
        return [(metres, self._by_id[code]) for metres, code in near]

    def in_the_box_of(self, key: Candidate, record: Record) -> list[tuple[float, Candidate]]:
        """The records that lie wholly in the box a place is given, and beyond 1 km of it."""
        if record.box is None:
            return []
        found = [
            (key.metres_from(self._by_id[code]), self._by_id[code])
            for code in self._ground.inside(record.box)
        ]
        return [(metres, other) for metres, other in found if metres > SAME_PLACE_METRES]


def join(
    london: London,
    names: Names,
    centres: Sequence[Centre],
    wards: Sequence[Outlined],
    boroughs: Sequence[Outlined],
    files: Mapping[str, File],
) -> Candidates:
    """Every candidate of London, and the places they make.

    A populated place of OS Open Names is a place. A town centre whose name
    is the same as a populated place within 1 km is that place, under a second
    publisher. Any other town centre is a place of its own, which one
    publisher writes. A ward or a town centre that writes or holds a place's
    name, within 1 km of it, is put beside the place. So is a town centre of the
    same name that lies wholly in the place's box, however far off.
    """
    open_names, line = files[names_places.SOURCE], files[names_wards.SOURCE]
    placed, outside_places = of_records(london, open_names, names.places)
    stations, outside_stations = of_records(london, open_names, names.stations)
    centred, outside_centres = of_centres(london, files[names_centres.SOURCE], centres)
    warded = of_outlined(london, line, wards)
    of_boroughs = of_outlined(london, line, boroughs)

    near_centres = _Near([candidate for candidate, _ in centred])
    near_wards = _Near(warded)
    same = frozenset({Match.SAME})

    def centres_of(
        candidate: Candidate, record: Record, allowed: frozenset[Match]
    ) -> list[Written]:
        near = _nearby(candidate, near_centres.of(candidate), allowed)
        return near + _nearby(candidate, near_centres.in_the_box_of(candidate, record), same)

    # A town centre is joined to the nearest populated place of the same name.
    taken: dict[str, tuple[float, Candidate]] = {}
    for candidate, record in placed:
        for each in centres_of(candidate, record, same):
            held = taken.get(each.candidate.record_id)
            if held is None or (each.metres, candidate.key) < (held[0], held[1].key):
                taken[each.candidate.record_id] = (each.metres, candidate)

    places: list[Place] = []
    for candidate, record in placed:
        beside = [
            each
            for each in centres_of(candidate, record, CARRIES)
            if each.match is not Match.SAME
            or taken[each.candidate.record_id][1].key == candidate.key
        ]
        beside += _nearby(candidate, near_wards.of(candidate), CARRIES)
        places.append(
            Place(
                key=candidate,
                others=tuple(sorted(beside, key=lambda each: (each.metres, each.candidate.key))),
                record=record,
                roads=names.roads.get(record.uri, 0),
            )
        )
    for candidate, centre in centred:
        if candidate.record_id in taken:
            continue
        beside = _nearby(candidate, near_wards.of(candidate), CARRIES)
        places.append(Place(key=candidate, others=tuple(beside), centre=centre))

    records = [candidate for candidate, _ in placed]
    records += [candidate for candidate, _ in centred]
    records += warded + of_boroughs
    return Candidates(
        places=tuple(sorted(places, key=lambda place: place.key.key)),
        records=tuple(sorted(records, key=lambda record: record.key)),
        stations=tuple(sorted((candidate for candidate, _ in stations), key=lambda c: c.key)),
        outside={
            f"{names_places.SOURCE}:{names_places.PLACE}": outside_places,
            f"{names_places.SOURCE}:{names_places.STATION}": outside_stations,
            names_centres.SOURCE: outside_centres,
        },
    )
