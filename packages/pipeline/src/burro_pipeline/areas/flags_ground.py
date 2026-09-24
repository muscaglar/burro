"""The ground a flag is worked out on: what the outlines, the wards and the roads say.

The rules of `flags.py` read plain values. This module makes them from shapes:

| Value | From |
|---|---|
| The ground and the outline's length of an output area | Its generalised outline |
| The sides two output areas share, and how long | The straight sides both outlines hold |
| The ward of an output area | The ward that holds most of its ground |
| How much of a side runs along a main road | The road links within a few metres of it |
| The town centres of an area | The area whose output areas hold most of each centre |

Two output areas share a side when both outlines hold the same two points next
to each other. The statistics office cuts its outlines from one map, so a
border is one line held by the output area on each side. No distance is
measured, and nothing is taken as near enough.

A main road is a link the roads file classes as a motorway, an A road or a B
road. It is a line a person can name. The file holds roads for vehicles and no
railway, and no file the licence gate gives for this use draws a railway or a
river above the tide, so a border along either is not seen to follow anything.

It is handed shapes and gives back numbers. It reads no file and no name of a
place, and nothing about who lives anywhere.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from burro_pipeline.areas import assign_shapes, context_shapes
from burro_pipeline.areas.context_shapes import Straight
from burro_pipeline.areas.flags import Area, Cell, Draft, Point, Rules, Side
from burro_pipeline.cells import shapes
from burro_pipeline.cells.shapes import Shape

# The classes of road that are main roads, as the roads file writes them.
MAIN_ROADS = frozenset({"Motorway", "A Road", "B Road"})
# How long a step along a side is, in metres, when it is held against the roads.
STEP = 25.0


@dataclass(frozen=True)
class Ground:
    """What the ground holds of every output area, worked out once for every draft."""

    hectares: Mapping[str, float]
    # The length of each outline, in metres.
    perimeter: Mapping[str, float]
    # The code of the borough of each output area, and the name of each borough.
    borough_of: Mapping[str, str]
    borough_names: Mapping[str, str]
    # The straight sides each pair of output areas shares. The first of a pair sorts first.
    shared: Mapping[tuple[str, str], tuple[Straight, ...]]
    # The code of the ward that holds most of each output area. Empty where no ward was read.
    ward_of: Mapping[str, str] = field(default_factory=dict[str, str])


@dataclass(frozen=True)
class Given:
    """One output area as a draft places it: a row of the file of output areas."""

    area: str
    margin: float | None = None
    second: str = ""


@dataclass(frozen=True)
class Named:
    """One area as a draft names it: a row of the file of areas, and what stands behind it."""

    name: str
    seed: Point | None = None
    publishers: tuple[str, ...] = ()
    # Whether an official publisher writes the name for a populated place at a point
    # inside the area: a checked row of evidence says so.
    by_the_rule: bool = False
    unreceipted: tuple[str, ...] = ()
    # What the draft lists as wrong with it, that its method could not put right.
    listed: tuple[str, ...] = ()
    # The name the seed's own record writes, which may not be the area's. Empty where
    # the draft does not say.
    seed_name: str = ""


@dataclass(frozen=True)
class Centre:
    """One town centre of district class or above: its name as written, and its outline."""

    record_id: str
    name: str
    shape: Shape


def shared_sides(outlines: Mapping[str, Shape]) -> dict[tuple[str, str], tuple[Straight, ...]]:
    """For each pair of outlines that share a side, the straight sides they share."""
    waiting: dict[Straight, str] = {}
    found: dict[tuple[str, str], list[Straight]] = {}
    for code in sorted(outlines):
        for side in shapes.sides(outlines[code]):
            other = waiting.pop(side, None)
            if other is None:
                waiting[side] = code
            elif other != code:
                found.setdefault((other, code), []).append(side)
    return {pair: tuple(sorted(sides)) for pair, sides in sorted(found.items())}


def ground_of(
    outlines: Mapping[str, Shape],
    borough_of: Mapping[str, str],
    borough_names: Mapping[str, str],
    wards: Mapping[str, Shape] | None = None,
) -> Ground:
    """The ground, from the outlines of the output areas and of the wards.

    It stops where an output area has no outline or no borough: a flag cannot
    be worked out round a hole in the ground.
    """
    if set(outlines) != set(borough_of):
        raise ValueError("every output area has an outline and a borough")
    return Ground(
        hectares={code: shapes.hectares(outlines[code]) for code in sorted(outlines)},
        perimeter={code: assign_shapes.metres_round(outlines[code]) for code in sorted(outlines)},
        borough_of=dict(sorted(borough_of.items())),
        borough_names=dict(sorted(borough_names.items())),
        shared=shared_sides(outlines),
        ward_of=_held_most_by(outlines, wards) if wards else {},
    )


def _held_most_by(outlines: Mapping[str, Shape], wards: Mapping[str, Shape]) -> dict[str, str]:
    """The ward that holds most of each output area, as the draft of areas finds it."""
    held = assign_shapes.held_most_by(outlines, wards)
    return {code: ward for code, (ward, _) in sorted(held.items())}


def _length(sides: Sequence[Straight]) -> float:
    return math.fsum(math.dist(a, b) for a, b in sides)


def sides_of(
    ground: Ground, area_of: Mapping[str, str], main_roads: Sequence[Shape], rules: Rules
) -> list[Side]:
    """Every side two output areas of the draft share, with how much of it is along a main road.

    A side is held against the roads only where it is a border: where the two
    output areas are in different areas. A side inside an area follows nothing
    that matters to a border, and is given none.
    """
    pairs = [pair for pair in ground.shared if pair[0] in area_of and pair[1] in area_of]
    borders = [pair for pair in pairs if area_of[pair[0]] != area_of[pair[1]]]
    asked = [side for pair in borders for side in ground.shared[pair]]
    beside = iter(context_shapes.metres_beside(asked, main_roads, rules.road_metres, STEP))
    along = {pair: math.fsum(next(beside) for _ in ground.shared[pair]) for pair in borders}
    return [
        Side(a, b, _length(ground.shared[a, b]), along.get((a, b), 0.0)) for a, b in sorted(pairs)
    ]


def centres_of(
    centres: Sequence[Centre], outlines: Mapping[str, Shape], area_of: Mapping[str, str]
) -> dict[str, tuple[str, ...]]:
    """For each area, the names of the town centres that lie mostly in it, as written.

    A centre lies mostly in the area whose output areas hold more of its ground
    than any other area's do. A centre that lies over no output area is in none.
    """
    held = {centre.record_id: centre for centre in centres}
    ground: dict[str, dict[str, float]] = {}
    shapes_of = {record_id: centre.shape for record_id, centre in held.items()}
    placed = {oa: outlines[oa] for oa in area_of if oa in outlines}
    for record_id, oa, share in context_shapes.overlaps(shapes_of, placed):
        areas = ground.setdefault(record_id, {})
        areas[area_of[oa]] = areas.get(area_of[oa], 0.0) + share
    found: dict[str, list[str]] = {}
    for record_id, areas in sorted(ground.items()):
        most = sorted(areas, key=lambda area: (-areas[area], area))[0]
        found.setdefault(most, []).append(held[record_id].name)
    return {area: tuple(names) for area, names in sorted(found.items())}


def draft_of(
    ground: Ground,
    given: Mapping[str, Given],
    named: Mapping[str, Named],
    *,
    outlines: Mapping[str, Shape] | None = None,
    main_roads: Sequence[Shape] = (),
    centres: Sequence[Centre] = (),
    homes: Mapping[str, int] | None = None,
    rules: Rules | None = None,
) -> Draft:
    """The draft and the ground as the rules read them.

    It stops where the draft leaves an output area of the ground in no area, or
    names one the ground does not hold: an output area is in one area, and no
    flag is worked out on a draft that breaks that.
    """
    if set(given) != set(ground.borough_of):
        raise ValueError("every output area of the ground is in one area of the draft")
    if any(row.area not in named for row in given.values()):
        raise ValueError("an output area is in an area the draft does not name")
    rules = rules or Rules()
    area_of = {oa: row.area for oa, row in given.items()}
    inside = centres_of(centres, outlines, area_of) if outlines and centres else {}
    return Draft(
        areas={
            area_id: Area(
                area_id=area_id,
                name=row.name,
                seed=row.seed,
                publishers=row.publishers,
                by_the_rule=row.by_the_rule,
                unreceipted=row.unreceipted,
                centres=inside.get(area_id, ()),
                listed=row.listed,
            )
            for area_id, row in sorted(named.items())
        },
        cells={
            oa: Cell(
                oa=oa,
                area=row.area,
                borough=ground.borough_of[oa],
                ward=ground.ward_of.get(oa, ""),
                hectares=ground.hectares[oa],
                perimeter=ground.perimeter[oa],
                margin=row.margin,
                second=row.second,
                homes=None if homes is None else homes.get(oa),
            )
            for oa, row in sorted(given.items())
        },
        sides=sides_of(ground, area_of, main_roads, rules),
        boroughs=ground.borough_names,
    )
