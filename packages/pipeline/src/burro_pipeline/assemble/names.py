"""The name each area of a build bears, from the draft of London's named areas.

An area of a build is a census area, which its publisher labels with a borough
and a number. Nobody knows a place by that. The draft of the areas gives every
output area of London to one named neighbourhood, by the names publishers
write and the roads between them. This lays that draft over the areas of a
build. It reads no publisher's file and names nothing itself: every name is
one the draft holds, as its publisher writes it.

**The rule.** An area bears the name of the drafted neighbourhood that holds
more of its output areas than any other does. The draft gives an output area
to the neighbourhood whose seed is nearest to it along the roads, so this is
the name nearest to where most of the area's homes are. It is counted in
output areas and not in homes, because the licence registry gives no count of
homes for naming a place, and an output area is drawn to hold much the same
number of homes as the next. Of two neighbourhoods that hold as many, the one
whose id sorts first gives the name. A neighbourhood gives a name only where a
record of a publisher writes that name letter for letter, or a person chose it
at the review desk from what a record writes. An area none of whose output
areas lies in a neighbourhood that gives a name keeps its publisher's label,
and nothing is made up for it.

**Two areas of one name.** A neighbourhood is larger than a census area, so
two areas or more may bear one name. Each says its borough, as every area
does. Where two of one borough bear one name, each adds the side of them it
lies on, as "Foxholt, north": the nearest of north, east, south and west to the
line from the middle of those areas to its own middle. Where two of them would
still say the same, each of the two says the nearest of eight points, as
"north-east". Two that lie the same way from the middle say the same, and the
publisher's label beside each name tells them apart. An area that says a side
holds the name alone among its other names, so that a search for the name
finds every area that bears it.

**A draft, and what a person decided.** Every name is a draft until a person
has decided it at the review desk. The desk writes who chose a name in the
rows of evidence behind it: a name with such a row is said to be checked, and
is served as the person spelt it. Any other is said to be a draft, whether it
stands by the founder's rule that one official publisher is enough, or still
waits at the desk. What a mark of the draft says of a name is for the person
at the desk, and turns no name down here.

**What is read.** Three files of one folder: the folder a draft was written
to, or the gazetteer the review desk compiled from it. Each is named in the
lock of the build by its hash, and is read only as the lock names it.

| File | Read for | Columns read |
|---|---|---|
| `areas.csv` | The name of each neighbourhood | `area_id`, `name` |
| `oa_to_area.csv` | The neighbourhood of each output area | `oa21cd`, `area_id` |
| `name_evidence.csv` | Who writes each name, in which file, and who chose it | `area_id`, |
| | | `role`, `source_id`, `as_written`, `snapshot_sha256`, `chosen_by` |

A name rests on the publisher's file that writes it. The draft says which file
that was, by its hash, and the build takes the name only where that file is a
file of its own lock. The build does not open the publisher's file again: the
draft read it, and what the draft read is held to the lock by its hash.

What is made here names places, so it is written only where a build writes,
and nothing here prints a name.
"""

import csv
import hashlib
import io
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_core.ids import NameState

from burro_pipeline.cells.spine import Area
from burro_pipeline.evidence.lock import InputKind, Lock, LockedInput, LockError
from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Use

AREAS, GIVEN, EVIDENCE = "areas.csv", "oa_to_area.csv", "name_evidence.csv"
# The columns that are read of each file. A file may hold others, which are not.
COLUMNS: Mapping[str, tuple[str, ...]] = {
    AREAS: ("area_id", "name"),
    GIVEN: ("oa21cd", "area_id"),
    EVIDENCE: ("area_id", "role", "source_id", "as_written", "snapshot_sha256", "chosen_by"),
}
# How the lock names each file of the folder: it is no publisher's file.
LOCKED_AS = "gazetteer/{}"
# The role of a row of evidence that is of the name of a neighbourhood itself.
PRIMARY = "primary"
# What stands between a name and the side an area lies on.
BETWEEN = ", "
# The points of the compass, anticlockwise from east, as a side is said.
FOUR = ("east", "north", "west", "south")
EIGHT = (
    "east",
    "north-east",
    "north",
    "north-west",
    "west",
    "south-west",
    "south",
    "south-east",
)

NAMED = Method(
    derivation_id="name_from_the_draft@1",
    sentence="The name of the drafted neighbourhood that holds more of the area's census output "
    "areas than any other, as its publisher writes it, with the side the area lies on where "
    "another area of its borough bears the name, and the publisher's own label where no "
    "named neighbourhood holds any of them.",
    kind=Kind.MODELLED,
    code="burro_pipeline.assemble.names",
)

# Why a draft is refused. Each is said in fixed words, which repeat nothing a file holds.
UNREADABLE = "a file of the draft of names is not there, or cannot be read as a table"
LACKS_A_COLUMN = "a file of the draft of names lacks a column the build reads"
GIVEN_TWICE = "the draft of names gives an output area to two neighbourhoods, or names one twice"
NOT_IN_THE_BUILD = (
    "a name of the draft rests on a file that is no file of this build. Give the list that "
    "names the file with --list, or make the draft again from the files of this build"
)
NOT_ALLOWED = "a name of the draft rests on a source the licence registry does not allow for names"

Point = tuple[float, float]


class NamesError(Exception):
    """The draft of names may not be built on. Says why, and never what a file holds."""


@dataclass(frozen=True)
class Written:
    """One neighbourhood of the draft that gives a name."""

    place_id: str
    # The name, as its publisher writes it.
    name: str
    # The hash of the file of each source whose record writes the name letter for letter.
    files: Mapping[str, str]
    # Whether a person chose the name at the review desk.
    checked: bool

    @property
    def state(self) -> NameState:
        return NameState.CHECKED if self.checked else NameState.DRAFT


@dataclass(frozen=True)
class Draft:
    """What a build reads of a draft of names."""

    # Every neighbourhood that gives a name, by its id.
    written: Mapping[str, Written]
    # The neighbourhood each output area was given to.
    given: Mapping[str, str]


@dataclass(frozen=True)
class Bears:
    """The name one area of a build bears, and how much of the area stands behind it."""

    written: Written
    # The side of the areas of its borough that bear the name. Empty where it is the only one.
    side: str
    # How many output areas of the area lie in the neighbourhood, and how many it has.
    held: int
    of: int

    @property
    def name(self) -> str:
        """The name as it is shown."""
        return f"{self.written.name}{BETWEEN}{self.side}" if self.side else self.written.name

    @property
    def aliases(self) -> tuple[str, ...]:
        """The name alone, where the area says a side too: a search for it finds the area."""
        return (self.written.name,) if self.side else ()

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.written.files))


@dataclass(frozen=True)
class Naming:
    """The names of a build: what each area bears, and the files the names rest on."""

    # An area that keeps its publisher's label is not here.
    bears: Mapping[str, Bears]
    # The receipt of every publisher's file that a name of the build rests on.
    files: tuple[Receipt, ...]
    areas: int

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(sorted({receipt.source_id for receipt in self.files}))

    def counts(self) -> dict[str, int]:
        """What the names of a build come to. It holds counts, and no name."""
        shown = [found.name for found in self.bears.values()]
        bare = [found.written.name for found in self.bears.values()]
        return {
            "areas": self.areas,
            "areas_that_bear_a_name": len(self.bears),
            "areas_that_keep_their_label": self.areas - len(self.bears),
            "names": len(set(bare)),
            "names_borne_by_two_areas_or_more": sum(
                bare.count(name) > 1 for name in sorted(set(bare))
            ),
            "areas_that_say_a_side": sum(bool(found.side) for found in self.bears.values()),
            "areas_shown_under_a_name_another_area_is_shown_under": sum(
                shown.count(name) > 1 for name in shown
            ),
            "names_a_person_has_checked": sum(
                found.written.checked for found in self.bears.values()
            ),
        }


def _rows(content: bytes, name: str) -> list[dict[str, str]]:
    """The rows of one file, each with the columns the build reads and no other."""
    try:
        table = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
        columns = set(table.fieldnames or ())
        held = [dict(row) for row in table]
    except (UnicodeDecodeError, csv.Error):
        raise NamesError(UNREADABLE) from None
    if not set(COLUMNS[name]) <= columns:
        raise NamesError(LACKS_A_COLUMN)
    if any(None in row or None in row.values() for row in held):
        raise NamesError(UNREADABLE)
    return [{column: row[column] for column in COLUMNS[name]} for row in held]


def files_of(folder: Path) -> dict[str, bytes]:
    """The three files of a draft that a build reads, by name."""
    try:
        return {name: (folder / name).read_bytes() for name in sorted(COLUMNS)}
    except OSError:
        raise NamesError(UNREADABLE) from None


def to_lock(files: Mapping[str, bytes]) -> tuple[LockedInput, ...]:
    """The files of a draft as the lock of a build names them: each by its hash."""
    found: list[LockedInput] = []
    for name in sorted(files):
        if not files[name]:
            raise NamesError(UNREADABLE)
        found.append(
            LockedInput(
                name=LOCKED_AS.format(name),
                kind=InputKind.GAZETTEER,
                sha256=hashlib.sha256(files[name]).hexdigest(),
                bytes=len(files[name]),
            )
        )
    return tuple(found)


def draft_of(files: Mapping[str, bytes]) -> Draft:
    """The draft, from its three files. It stops where they do not fit each other."""
    neighbourhoods = _rows(files[AREAS], AREAS)
    names = {row["area_id"]: row["name"] for row in neighbourhoods}
    if len(names) != len(neighbourhoods):
        raise NamesError(GIVEN_TWICE)
    given: dict[str, str] = {}
    for row in _rows(files[GIVEN], GIVEN):
        if given.setdefault(row["oa21cd"], row["area_id"]) != row["area_id"]:
            raise NamesError(GIVEN_TWICE)
    written: dict[str, dict[str, str]] = {}
    chosen: set[str] = set()
    for row in _rows(files[EVIDENCE], EVIDENCE):
        place = row["area_id"]
        if row["role"] != PRIMARY or not names.get(place):
            continue
        # A publisher writes a name where the label of its record is the name, letter for
        # letter. A label that holds the name among other words writes another name, unless
        # a person chose the name from it at the desk: the desk offers a spelling only from
        # a label that a publisher wrote.
        if row["as_written"] != names[place] and not row["chosen_by"]:
            continue
        written.setdefault(place, {}).setdefault(row["source_id"], row["snapshot_sha256"])
        if row["chosen_by"]:
            chosen.add(place)
    return Draft(
        written={
            place: Written(place, names[place], dict(sorted(wrote.items())), place in chosen)
            for place, wrote in sorted(written.items())
        },
        given=given,
    )


def chosen_for(draft: Draft, cells: Sequence[str]) -> tuple[Written, int] | None:
    """The neighbourhood that gives an area its name, and how many of its cells it holds.

    It is the neighbourhood that holds most of the area's output areas, of
    those that give a name. Of two that hold as many, the id that sorts first.
    """
    held: dict[str, int] = {}
    for oa in cells:
        place = draft.given.get(oa)
        if place is not None and place in draft.written:
            held[place] = held.get(place, 0) + 1
    if not held:
        return None
    most = min(held, key=lambda place: (-held[place], place))
    return draft.written[most], held[most]


def _towards(point: Point, middle: Point, points: Sequence[str]) -> str:
    """The point of the compass nearest to the line from the middle to a point."""
    east, north = point[0] - middle[0], point[1] - middle[1]
    turn = math.degrees(math.atan2(north, east)) % 360.0
    step = 360.0 / len(points)
    return points[int(((turn + step / 2) % 360.0) // step)]


def sides_of(centres: Mapping[str, Point]) -> dict[str, str]:
    """The side each of several areas lies on, of the middle of them all.

    `centres` gives the middle of each area, east and north in one measure.
    Each says the nearest of four points. Where two would say the same, each
    of the two says the nearest of eight. One area alone says no side.
    """
    if len(centres) <= 1:
        return dict.fromkeys(centres, "")
    ordered = sorted(centres)
    middle = (
        math.fsum(centres[area][0] for area in ordered) / len(ordered),
        math.fsum(centres[area][1] for area in ordered) / len(ordered),
    )
    said = {area: _towards(centres[area], middle, FOUR) for area in ordered}
    alike = [area for area in ordered if list(said.values()).count(said[area]) > 1]
    return said | {area: _towards(centres[area], middle, EIGHT) for area in alike}


def on_the_ground(centre: Point, scale: float) -> Point:
    """A point of longitude and latitude as east and north in one measure.

    A degree of longitude is shorter than one of latitude by the cosine of the
    latitude. `scale` is that cosine, taken once for all the points compared.
    """
    return centre[0] * scale, centre[1]


def name_areas(
    draft: Draft,
    areas: Sequence[Area],
    cells: Mapping[str, Sequence[str]],
    centres: Mapping[str, Point],
) -> dict[str, Bears]:
    """The name each area of a build bears. An area that keeps its label is left out.

    `cells` gives the output areas of each area, and `centres` a point inside
    each, as longitude and latitude.
    """
    found = {
        area.area_id: chosen
        for area in areas
        if (chosen := chosen_for(draft, cells[area.area_id])) is not None
    }
    together: dict[tuple[str, str], list[str]] = {}
    for area in areas:
        if area.area_id in found:
            key = (found[area.area_id][0].name, area.borough_code)
            together.setdefault(key, []).append(area.area_id)
    side: dict[str, str] = {}
    for members in together.values():
        north = math.fsum(centres[area][1] for area in members) / len(members)
        scale = math.cos(math.radians(north))
        side |= sides_of({area: on_the_ground(centres[area], scale) for area in members})
    return {
        area_id: Bears(written, side[area_id], held, len(cells[area_id]))
        for area_id, (written, held) in found.items()
    }


def _receipts_of(
    bears: Mapping[str, Bears], receipts: Sequence[Receipt], lock: Lock | None, registry: Registry
) -> tuple[Receipt, ...]:
    """The receipt of every file a name of the build rests on, each held to the build."""
    by_hash = {receipt.sha256: receipt for receipt in receipts}
    wanted = sorted(
        {
            (source_id, sha256)
            for found in bears.values()
            for source_id, sha256 in found.written.files.items()
        }
    )
    files: dict[str, Receipt] = {}
    for source_id, sha256 in wanted:
        receipt = by_hash.get(sha256)
        if receipt is None or receipt.source_id != source_id:
            raise NamesError(NOT_IN_THE_BUILD)
        if lock is not None and not lock.holds(receipt.file_id):
            raise NamesError(NOT_IN_THE_BUILD)
        try:
            registry.require(source_id, Use.GAZETTEER)
        except RegistryError:
            raise NamesError(NOT_ALLOWED) from None
        files[receipt.file_id] = receipt
    return tuple(files[file_id] for file_id in sorted(files))


def build(
    files: Mapping[str, bytes],
    areas: Sequence[Area],
    cells: Mapping[str, Sequence[str]],
    centres: Mapping[str, Point],
    receipts: Sequence[Receipt],
    lock: Lock | None,
    registry: Registry,
) -> Naming:
    """The names of a build, from the files of a draft. Each file is held to the lock first."""
    if lock is not None:
        for name in sorted(files):
            try:
                lock.admit(files[name], LOCKED_AS.format(name))
            except LockError:
                raise NamesError(NOT_IN_THE_BUILD) from None
    bears = name_areas(draft_of(files), areas, cells, centres)
    return Naming(bears, _receipts_of(bears, receipts, lock, registry), len(areas))
