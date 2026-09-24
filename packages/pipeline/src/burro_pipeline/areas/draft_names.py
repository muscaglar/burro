"""A name for each drafted area: which name is offered first, and which are the others.

The names are drafted before any border is drawn, and the borders are grown
from their seeds. Only then can it be said which names lie in which area. This
is that step. It takes plain values and reads no file. It holds no name of its
own and coins none: every name it offers is one a publisher's record writes.

| Rule | Detail |
|---|---|
| Where a record lies | A point lies in the area of its output area. An outline lies in every |
| | area that holds a twentieth of it or more |
| A point on a line | A point on the line between two output areas lies in both. Where they |
| | are of two areas it lies in both areas: the file does not settle which. A name is |
| | placed in its own area if that is one of them, else in the one whose id sorts first |
| A name falls in an area | One record that writes the name lies in the area |
| Where a name is placed | In the area of the record it is known by. An outline is placed |
| | where most of it lies |
| Offered first | The name the area was grown from, where it falls in the area |
| | If it does not, the name placed in the area with most points |
| The others | Every other name placed in the area, the most points first |
| No name | An area no name falls in has no name. It is offered as unnamed |
| A wide name | Given to the areas the draft of names chose for it, five at most |
| A second name of a record | Another name of the same ground, wherever the record's name is |

What the design's section 6 asks of a name is one record that puts it on the
map inside the area. So `locates` is worked out again here, against the area as
drawn: `point_inside`, `polygon_overlap`, or `label_only` for a record that
writes the name and lies outside.

A mark is never a verdict. It says what a person should look at, and why.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

POINT, OUTLINE = "point", "outline"
POINT_INSIDE, POLYGON_OVERLAP, LABEL_ONLY = "point_inside", "polygon_overlap", "label_only"
PRIMARY, ALIAS, WIDE_ROLE = "primary", "alias", "wide"
# What a name is put forward as: the answers of the review desk.
AREA, SAME_GROUND, INSIDE, WIDE = "area", "same_ground", "inside", "wide"
# Why a name is offered where it is.
SEED, PLACED, SECOND_NAME = "seed", "placed", "second_name"
# A name that was put forward as an area, and is offered as another name: its own area
# became part of another, or its own area stands and does not hold it.
SEED_OF_NO_AREA, SEED_OUTSIDE = "seed_of_no_area", "seed_outside_its_area"
# What a person should look at.
UNNAMED = "unnamed"
NOT_ITS_SEED = "not_its_seed"
BY_AN_OUTLINE_ALONE = "by_an_outline_alone"
HEAVIER_NAME_INSIDE = "heavier_name_inside"
SEED_LIES_ELSEWHERE = "seed_lies_elsewhere"
ON_THE_LINE = "on_the_line"
WAS_PUT_UNDER_ANOTHER = "was_put_under_another"
MARKS = (
    UNNAMED,
    NOT_ITS_SEED,
    BY_AN_OUTLINE_ALONE,
    HEAVIER_NAME_INSIDE,
    SEED_LIES_ELSEWHERE,
    ON_THE_LINE,
    WAS_PUT_UNDER_ANOTHER,
)


@dataclass(frozen=True)
class Rules:
    """Every number the naming turns on. Each is a first guess."""

    # An outline lies in an area when this share of it or more is on the area's ground.
    # A town centre runs along a street, and a border may run down the same street: a
    # sliver of an outline on the far side of a border is not the centre lying there.
    overlap: float = 0.05
    # Two areas are tied by a name when an outline that writes the name of one has this
    # share of it or more in the other. A ward lies over two areas or three, so a
    # twentieth would tie nearly every area to the next.
    ties: float = 1 / 3
    # How many areas a wide name is given to, at most (design, section 2).
    wide_over: int = 5


@dataclass(frozen=True)
class Record:
    """One record of a publisher's file beside one name, and the ground it lies on."""

    source_id: str
    record_id: str
    publisher: str
    field: str
    # The record's label in full, exactly as the file holds it.
    as_written: str
    # Whether the record gives a point or an outline.
    gives: str
    # How the label writes the name: `same`, `part`, `held` or `holds`.
    match: str
    # Whether that counts as the publisher writing the name.
    writes: bool
    # The share of the record that lies on each output area. A point lies whole on one,
    # or in equal parts on each of those whose edge it stands on.
    lies_on: Mapping[str, float]


@dataclass(frozen=True)
class Name:
    """One place of the draft of names, and every record beside its name."""

    place_id: str
    name: str
    # What the draft of names put it forward as, before a border was drawn.
    proposed: str
    points: int
    # The record it is known by first, then every other.
    records: tuple[Record, ...]
    # The places it was put under, by their ids.
    of: tuple[str, ...] = ()
    # A second name its own record gives it. Empty where it gives none.
    second_name: str = ""
    # The column the second name was read from.
    second_field: str = ""

    @property
    def key(self) -> Record:
        return self.records[0]

    @property
    def publishers(self) -> tuple[str, ...]:
        """Who writes the name, wherever their record lies."""
        return tuple(sorted({record.publisher for record in self.records if record.writes}))


@dataclass(frozen=True)
class Located:
    """One record beside one name offered for one area, and whether it lies in the area."""

    record: Record
    locates: str
    # The share of the record that lies in the area.
    share: float
    # The area that holds most of the record. Empty where it lies in none.
    lies_in: str


@dataclass(frozen=True)
class Offered:
    """One name offered for one area."""

    area_id: str
    name: Name
    # The name as it is offered: the place's own, or the second name of its record.
    as_offered: str
    # `primary` for the name offered first, `alias` or `wide` for any other.
    role: str
    # Empty for the name offered first. For any other: `same_ground`, `inside` or `wide`.
    kind: str
    why: str
    records: tuple[Located, ...]

    @property
    def located(self) -> bool:
        """Whether a record that writes the name lies in the area."""
        return any(each.record.writes and each.locates != LABEL_ONLY for each in self.records)


@dataclass(frozen=True)
class Mark:
    """One thing to look at, of one area or of one name offered for it."""

    area_id: str
    place_id: str
    mark: str
    why: str


@dataclass(frozen=True)
class Naming:
    """Every area with the names offered for it, and what to look at."""

    # The name offered first for each area. None for an area that has no name.
    first: Mapping[str, Offered | None]
    others: Mapping[str, tuple[Offered, ...]]
    marks: tuple[Mark, ...]
    # The area each place is placed in, by the record it is known by.
    placed: Mapping[str, str] = field(default_factory=dict[str, str])

    @property
    def unnamed(self) -> tuple[str, ...]:
        return tuple(area for area, first in sorted(self.first.items()) if first is None)

    def offered(self, area_id: str) -> tuple[Offered, ...]:
        """Every name offered for an area, the first one first."""
        first = self.first[area_id]
        return (*(() if first is None else (first,)), *self.others.get(area_id, ()))


def fold(text: str) -> str:
    """A name as it is put in order, and never as it is shown."""
    return " ".join(text.casefold().split())


def shares_of(record: Record, area_of: Mapping[str, str]) -> dict[str, float]:
    """The share of a record that lies in each area, by the output areas it lies on."""
    found: dict[str, float] = {}
    for oa in sorted(record.lies_on):
        if oa in area_of:
            found[area_of[oa]] = found.get(area_of[oa], 0.0) + record.lies_on[oa]
    return found


def most_of(shares: Mapping[str, float]) -> str:
    """The area that holds most of a record. Of two that hold as much, the id that sorts first."""
    return min(shares, key=lambda area: (-shares[area], area)) if shares else ""


def located(record: Record, area_id: str, area_of: Mapping[str, str], rules: Rules) -> Located:
    """Whether one record lies in one area, in the design's own words."""
    shares = shares_of(record, area_of)
    share = min(1.0, round(shares.get(area_id, 0.0), 6))
    if record.gives == POINT:
        locates = POINT_INSIDE if share > 0 else LABEL_ONLY
    else:
        locates = POLYGON_OVERLAP if share >= rules.overlap and share > 0 else LABEL_ONLY
    return Located(record, locates, share, most_of(shares))


def _offer(
    name: Name,
    area_id: str,
    area_of: Mapping[str, str],
    rules: Rules,
    *,
    role: str,
    kind: str,
    why: str,
) -> Offered:
    records = tuple(located(record, area_id, area_of, rules) for record in name.records)
    return Offered(area_id, name, name.name, role, kind, why, records)


def _second(of: Offered) -> Offered:
    """The second name of a record, offered beside its first: another name of the same ground."""
    key = of.records[0]
    record = Record(
        source_id=key.record.source_id,
        record_id=key.record.record_id,
        publisher=key.record.publisher,
        field=of.name.second_field,
        as_written=of.name.second_name,
        gives=key.record.gives,
        match="same",
        writes=True,
        lies_on=key.record.lies_on,
    )
    return Offered(
        area_id=of.area_id,
        name=of.name,
        as_offered=of.name.second_name,
        role=ALIAS if of.role == PRIMARY else of.role,
        kind=SAME_GROUND if of.role == PRIMARY else of.kind,
        why=SECOND_NAME,
        records=(Located(record, key.locates, key.share, key.lies_in),),
    )


def _on_a_line(name: Name, area_of: Mapping[str, str]) -> tuple[str, ...]:
    """The areas a name's own point lies on the edge of, where they are more than one."""
    if name.key.gives != POINT:
        return ()
    areas = sorted(shares_of(name.key, area_of))
    return tuple(areas) if len(areas) > 1 else ()


def _listed(areas: Sequence[str]) -> str:
    return ", ".join(areas[:-1]) + (" and " if len(areas) > 1 else "") + areas[-1]


def heaviest_first(name: Name) -> tuple[int, int, str, str]:
    """The order names are offered in: most points, then most publishers, then by name."""
    return (-name.points, -len(name.publishers), fold(name.name), name.place_id)


def _falls_in(name: Name, area_id: str, area_of: Mapping[str, str], rules: Rules) -> bool:
    return any(
        record.writes and located(record, area_id, area_of, rules).locates != LABEL_ONLY
        for record in name.records
    )


def name_areas(
    names: Sequence[Name],
    area_of: Mapping[str, str],
    stands_as: Mapping[str, str],
    rules: Rules | None = None,
) -> Naming:
    """The names offered for every area, and what a person should look at.

    `area_of` gives every output area its area. An area is known by the id of the
    place it was grown from. `stands_as` gives, for every place that was a seed,
    the area it stands as at the end: its own, or the area it became part of.
    """
    rules = rules or Rules()
    areas = sorted(set(area_of.values()))
    by_id = {name.place_id: name for name in names}
    if len(by_id) != len(names):
        raise ValueError("a place is there twice")
    marks: list[Mark] = []
    first: dict[str, Offered | None] = dict.fromkeys(areas)
    placed: dict[str, list[Name]] = {area: [] for area in areas}
    where: dict[str, str] = {}
    wide: list[Name] = []

    # The name an area was grown from is offered first, where it falls in the area.
    for area in areas:
        seed = by_id.get(area)
        if seed is not None and _falls_in(seed, area, area_of, rules):
            first[area] = _offer(seed, area, area_of, rules, role=PRIMARY, kind="", why=SEED)
            where[seed.place_id] = area
    # Every other name is placed by the record it is known by.
    for name in sorted(names, key=lambda each: each.place_id):
        if name.place_id in where:
            continue
        if name.proposed == WIDE:
            wide.append(name)
            continue
        area = most_of(shares_of(name.key, area_of))
        if area:
            placed[area].append(name)
            where[name.place_id] = area
    # An area whose own name lies outside it takes the heaviest name placed in it.
    for area in areas:
        if first[area] is not None:
            continue
        seed = by_id.get(area)
        grown_from = f"the name it was grown from, {seed.name}," if seed else "its seed"
        if not placed[area]:
            marks.append(
                Mark(
                    area,
                    "",
                    UNNAMED,
                    f"No record of any name lies in it: {grown_from} lies outside.",
                )
            )
            continue
        chosen = min(placed[area], key=heaviest_first)
        placed[area].remove(chosen)
        first[area] = _offer(chosen, area, area_of, rules, role=PRIMARY, kind="", why=PLACED)
        marks.append(
            Mark(
                area,
                chosen.place_id,
                NOT_ITS_SEED,
                f"It is offered {chosen.name}, which lies in it: {grown_from} lies outside.",
            )
        )

    others: dict[str, list[Offered]] = {area: [] for area in areas}
    for area in areas:
        for name in sorted(placed[area], key=heaviest_first):
            under = {stands_as.get(each, each) for each in name.of}
            same = name.proposed == SAME_GROUND and area in under
            was_a_seed = name.proposed == AREA
            stands = name.place_id in first
            why = (SEED_OUTSIDE if stands else SEED_OF_NO_AREA) if was_a_seed else PLACED
            others[area].append(
                _offer(
                    name,
                    area,
                    area_of,
                    rules,
                    role=ALIAS,
                    kind=SAME_GROUND if same else INSIDE,
                    why=why,
                )
            )
            if was_a_seed and stands:
                marks.append(
                    Mark(
                        area,
                        name.place_id,
                        SEED_LIES_ELSEWHERE,
                        f"{name.name} is the name another area was grown from, and its record "
                        "lies here.",
                    )
                )
            elif not was_a_seed and under and area not in under and not _on_a_line(name, area_of):
                marks.append(
                    Mark(
                        area,
                        name.place_id,
                        WAS_PUT_UNDER_ANOTHER,
                        f"{name.name} was put under another area before the borders were "
                        "drawn, and its record lies here.",
                    )
                )
    for name in wide:
        given: list[str] = []
        for each in name.of:
            area = stands_as.get(each, each)
            if area in first and area not in given:
                given.append(area)
        for area in given[: rules.wide_over]:
            others[area].append(
                _offer(name, area, area_of, rules, role=WIDE_ROLE, kind=WIDE, why=PLACED)
            )
        if given:
            where[name.place_id] = given[0]

    for area in areas:
        for each in (first[area], *others[area]):
            beside = _on_a_line(each.name, area_of) if each is not None else ()
            if each is not None and each.kind != WIDE and beside:
                marks.append(
                    Mark(
                        area,
                        each.name.place_id,
                        ON_THE_LINE,
                        f"The point of {each.name.name} lies on the line between this area "
                        f"and {_listed([other for other in beside if other != area])}. The "
                        "file does not settle which it lies in.",
                    )
                )
    for area in areas:
        offered = first[area]
        seconds = [each for each in (offered, *others[area]) if each and each.name.second_name]
        others[area] += [_second(each) for each in seconds]
        if offered is None:
            continue
        if not any(each.locates == POINT_INSIDE for each in offered.records if each.record.writes):
            marks.append(
                Mark(
                    area,
                    offered.name.place_id,
                    BY_AN_OUTLINE_ALONE,
                    f"No point of {offered.name.name} lies in it. An outline of that name "
                    "lies over it.",
                )
            )
        heavier = [
            each.name
            for each in others[area]
            if each.why != SECOND_NAME
            and each.kind != WIDE
            and each.name.points > offered.name.points
        ]
        if heavier:
            most = min(heavier, key=heaviest_first)
            marks.append(
                Mark(
                    area,
                    most.place_id,
                    HEAVIER_NAME_INSIDE,
                    f"{most.name} lies in it with {most.points} points. "
                    f"{offered.name.name} has {offered.name.points}.",
                )
            )
    return Naming(
        first=first,
        others={area: tuple(found) for area, found in others.items()},
        marks=tuple(sorted(marks, key=lambda mark: (mark.area_id, MARKS.index(mark.mark)))),
        placed=dict(sorted(where.items())),
    )
