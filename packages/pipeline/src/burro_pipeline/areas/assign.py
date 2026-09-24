"""Give every output area to one area, grown from the seeds.

This is steps 6 and 7 of section 4 of the areas design: the draft and its
repair. It takes the ground as plain values and reads no file. What it gives is
a draft for a person to correct, and it keeps beside every output area how
sure it was.

| Step | What happens |
|---|---|
| Too close | Of two seeds within `too_close` metres by road, the lighter joins the heavier |
| Grow | Each output area is weighed against the `nearest` seeds along the roads |
| Weigh | A distance is cut where a record holds the seed's name, and raised across a borough |
| Bank | An output area never goes to a seed on the other bank of the tidal water |
| | A seed with no bank is put on the bank most of what it would be given is on |
| Join | An output area no seed reaches joins the area it shares most border with |
| One piece | A part cut off from its area joins the area it shares most border with |
| Smallest | An area of under `smallest` output areas joins the area it shares most border with |

Each number is in `Rules`, on a line of its own, with why it was chosen.

An area may lie in two boroughs: the design's section 8 allows it, and asks
that the share of each is kept. An area may not be in two pieces, and may not
lie on both banks. Where the ground makes either so, the area is listed, and
nothing is forced.

The same ground and the same seeds give the same draft, whatever order they
are handed over in: every loop is over a sorted list, and every distance is a
whole number of millimetres until it is weighed.
"""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from burro_pipeline.areas.grow import (
    MILLIMETRES_IN_A_METRE,
    Millimetres,
    Near,
    Roads,
    nearest_seeds,
    within,
)

Point = tuple[float, float]

# The kinds of thing a publisher's record says of an output area. They are the names
# the review desk shows beside a border.
WARD, ROADS, MSOA, CENTRE = "ward", "roads", "msoa", "centre"
# The banks of the tidal water. An output area the files draw no river beside has none.
NORTH, SOUTH, NOT_DRAWN = "north", "south", ""
# How an output area came to its area.
NEAREST, JOINED, STRAY, SMALL = "nearest", "joined", "stray", "small"
# Why a seed stands for no area of its own.
TOO_CLOSE, UNDER_SMALLEST, NO_OUTPUT_AREA = "too_close", "under_smallest", "no_output_area"
# What is wrong with an area that the method could not put right.
IN_PIECES, BOTH_BANKS, SEED_OUTSIDE = "in_pieces", "both_banks", "seed_outside"


def _cuts() -> dict[str, float]:
    # Section 4, step 6 of the design: 15% where the MSOA's name holds the seed's name,
    # 15% where the roads do, 5% where the ward does.
    return {MSOA: 0.15, ROADS: 0.15, WARD: 0.05}


@dataclass(frozen=True)
class Rules:
    """Every number the method turns on. Each is a first guess, as the design's own are."""

    # How many seeds an output area is weighed against. The design keeps the three
    # nearest by road as evidence, and the draft chooses among them.
    nearest: int = 3
    # Two seeds this near by road, in metres, are one place (design, section 6).
    too_close: float = 600.0
    # The fewest output areas an area may hold. The design says 1,500 homes. The licence
    # gate does not give homes for this use, so no home is counted and output areas are
    # counted in their place. The number is a guess of its own, and rests on no table. It
    # is the founder's to set, with whether homes may be read for this use.
    smallest: int = 12
    # The seeds of areas that stay however small they are: the design's short kept list.
    kept: frozenset[str] = frozenset()
    # How much of a distance is taken off where a record holds the seed's name, by kind.
    cut: Mapping[str, float] = field(default_factory=_cuts)
    # How much is put on a distance to a seed in another borough (design, step 6).
    across_a_borough: float = 0.10


@dataclass(frozen=True)
class Said:
    """What one kind of record says of an output area, and the seeds whose name it holds."""

    kind: str
    # The name, as the record holds it.
    as_written: str
    favours: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Cell:
    """One output area, as the ground holds it."""

    oa: str
    # The code of its borough, from the lookup.
    borough: str
    # Where its homes are taken to stand, on the National Grid.
    centre: Point
    bank: str = NOT_DRAWN
    # The node of the roads nearest its centre, and how far that is. No node where the
    # roads hold none a seed reaches.
    node: str = ""
    to_node: Millimetres = 0
    hectares: float = 0.0
    said: tuple[Said, ...] = ()


@dataclass(frozen=True)
class Seed:
    """One point an area is grown from."""

    seed_id: str
    point: Point
    # How much stands behind its name. Of two seeds too close, the heavier stands.
    weight: float
    # The output area its point lies in.
    oa: str
    # The node of the roads nearest it, and how far that is.
    node: str
    to_node: Millimetres = 0


@dataclass(frozen=True)
class Choice:
    """One seed an output area was weighed against."""

    seed: str
    # Along the roads from the centre of the output area to the seed.
    far: Millimetres
    # The same, after the cuts and the raise.
    weighed: float
    # Whether the seed is in another borough than the output area.
    across: bool
    # The kinds of record that hold the seed's name.
    favoured_by: tuple[str, ...]


@dataclass(frozen=True)
class Given:
    """One output area, the area it was given to, and how sure the method was."""

    oa: str
    area: str
    how: str
    # By how much the second choice is further than the first, in hundredths, rounded
    # down. Nothing where there was no second choice. 0 where the output area is not in
    # the area the distances chose.
    margin: int | None
    # The area it would be in if not this one. Empty where there is none.
    second: str
    # The seeds it was weighed against, the nearest after weighing first.
    choices: tuple[Choice, ...]


@dataclass(frozen=True)
class Absorbed:
    """One seed that stands for no area of its own, and the area it became part of."""

    seed: str
    into: str
    why: str
    # Along the roads to the seed it was too close to. Nothing for any other reason.
    far: Millimetres | None = None
    # The area that holds the output area its point lies in, at the end.
    lies_in: str = ""
    # How many output areas it held when it was taken in, for one that was too small.
    held: int = 0


@dataclass(frozen=True)
class Drawn:
    """One area of the draft, measured."""

    area: str
    cells: tuple[str, ...]
    hectares: float
    # Its output areas in each borough, by the borough's code.
    boroughs: Mapping[str, int]
    # The borough that holds most of its output areas. Of two that hold as many, the
    # one whose code sorts first.
    primary_borough: str
    # The pieces it is in, the one that holds its seed first. A piece is output areas
    # joined by shared sides.
    pieces: tuple[tuple[str, ...], ...]
    # The banks its output areas are on.
    banks: tuple[str, ...]
    # Whether the output area its seed lies in is one of its own.
    seed_inside: bool
    # The areas it shares a side with, and how many metres with each.
    beside: Mapping[str, float]


@dataclass(frozen=True)
class Listed:
    """One area the method could not put right, and what is wrong with it."""

    area: str
    what: str
    cells: tuple[str, ...] = ()


@dataclass(frozen=True)
class Draft:
    """Every output area in one area, and what the method did to get there."""

    given: Mapping[str, Given]
    drawn: Mapping[str, Drawn]
    absorbed: tuple[Absorbed, ...]
    listed: tuple[Listed, ...]
    rules: Rules

    def counts(self) -> dict[str, int]:
        """What the draft holds, counted and held to no number."""
        how = [given.how for given in self.given.values()]
        return {
            "output_areas": len(self.given),
            "areas": len(self.drawn),
            "seeds_too_close": sum(each.why == TOO_CLOSE for each in self.absorbed),
            "seeds_under_smallest": sum(each.why == UNDER_SMALLEST for each in self.absorbed),
            "seeds_with_no_output_area": sum(each.why == NO_OUTPUT_AREA for each in self.absorbed),
            "given_to_the_nearest": how.count(NEAREST),
            "no_seed_reached": how.count(JOINED),
            "cut_off_and_joined": how.count(STRAY),
            "of_an_area_too_small": how.count(SMALL),
            "areas_in_pieces": sum(each.what == IN_PIECES for each in self.listed),
            "areas_on_both_banks": sum(each.what == BOTH_BANKS for each in self.listed),
            "areas_with_seed_outside": sum(each.what == SEED_OUTSIDE for each in self.listed),
            "areas_in_two_boroughs": sum(len(each.boroughs) > 1 for each in self.drawn.values()),
        }


Beside = Mapping[str, Mapping[str, float]]


def _held(cells: Sequence[Cell], seeds: Sequence[Seed], beside: Beside, roads: Roads) -> None:
    """Stop where the ground does not fit together."""
    codes = {cell.oa for cell in cells}
    if len(codes) != len(cells) or len({seed.seed_id for seed in seeds}) != len(seeds):
        raise ValueError("an output area or a seed is there twice")
    if not seeds or not cells:
        raise ValueError("there is no seed, or no output area")
    if any(seed.oa not in codes or seed.node not in roads.number_of for seed in seeds):
        raise ValueError("a seed lies in no output area, or starts from no node")
    if any(not math.isfinite(seed.weight) for seed in seeds):
        raise ValueError("a weight is a number")
    if any(cell.node and cell.node not in roads.number_of for cell in cells):
        raise ValueError("an output area is put at a node the roads do not hold")
    if any(cell.bank not in (NORTH, SOUTH, NOT_DRAWN) for cell in cells):
        raise ValueError("a bank is north, south or not drawn")
    for oa, others in beside.items():
        if oa not in codes or any(other not in codes or other == oa for other in others):
            raise ValueError("a side is of an output area the ground does not hold")
        if any(beside.get(other, {}).get(oa) != metres for other, metres in others.items()):
            raise ValueError("a side is shared by both output areas, at one length")


def heaviest_first(seeds: Iterable[Seed]) -> list[Seed]:
    return sorted(seeds, key=lambda seed: (-seed.weight, seed.seed_id))


def too_close(seeds: Sequence[Seed], roads: Roads, rules: Rules) -> dict[str, Absorbed]:
    """The seeds that are one place with a heavier seed, each with the seed that stands.

    The heaviest seed stands. Each seed after it stands unless a seed that
    stands is within the distance along the roads, and then it becomes part
    of the nearest such. Of two as heavy as each other, the one whose id
    sorts first stands.
    """
    limit = round(rules.too_close * MILLIMETRES_IN_A_METRE)
    standing: dict[str, list[Seed]] = {}
    found: dict[str, Absorbed] = {}
    for seed in heaviest_first(seeds):
        reached = within(roads, seed.node, limit - seed.to_node) if standing else {}
        near = sorted(
            (seed.to_node + far + other.to_node, other.seed_id)
            for node, far in reached.items()
            for other in standing.get(node, ())
        )
        if near and near[0][0] <= limit:
            found[seed.seed_id] = Absorbed(seed.seed_id, near[0][1], TOO_CLOSE, near[0][0])
        else:
            standing.setdefault(seed.node, []).append(seed)
    return found


def _weighed(cell: Cell, near: Near, seed_cell: Cell, rules: Rules) -> Choice:
    far = near.far + cell.to_node
    favoured = tuple(
        kind
        for kind in sorted(rules.cut)
        if any(said.kind == kind and near.seed in said.favours for said in cell.said)
    )
    weighed = float(far)
    for kind in favoured:
        weighed *= 1.0 - rules.cut[kind]
    across = cell.borough != seed_cell.borough
    if across:
        weighed *= 1.0 + rules.across_a_borough
    return Choice(near.seed, far, weighed, across, favoured)


def _other_bank(one: str, other: str) -> bool:
    return bool(one and other and one != other)


def _pieces(cells: Iterable[str], beside: Beside) -> list[tuple[str, ...]]:
    """Some output areas as the pieces they are in: each a run of shared sides, in order."""
    wanted = set(cells)
    seen: set[str] = set()
    found: list[tuple[str, ...]] = []
    for first in sorted(wanted):
        if first in seen:
            continue
        seen.add(first)
        piece, waiting = [first], [first]
        while waiting:
            for other in beside.get(waiting.pop(), {}):
                if other in wanted and other not in seen:
                    seen.add(other)
                    piece.append(other)
                    waiting.append(other)
        found.append(tuple(sorted(piece)))
    return found


class _Drafting:
    """The draft while it is being made: which area each output area is in, and how."""

    def __init__(
        self, cells: Sequence[Cell], seeds: Sequence[Seed], beside: Beside, rules: Rules
    ) -> None:
        self.cells = {cell.oa: cell for cell in sorted(cells, key=lambda cell: cell.oa)}
        self.seeds = {seed.seed_id: seed for seed in sorted(seeds, key=lambda s: s.seed_id)}
        self.beside = beside
        self.rules = rules
        self.area_of: dict[str, str] = {}
        self.how: dict[str, str] = {}
        self.of_area: dict[str, set[str]] = {}
        self.choices: dict[str, tuple[Choice, ...]] = {}
        self.absorbed: dict[str, Absorbed] = {}
        # The pieces of each area, kept until an output area joins or leaves it.
        self.pieces: dict[str, tuple[tuple[str, ...], ...]] = {}
        # The bank each seed is on: that of the output area it lies in.
        self.bank = {seed_id: self.cells[seed.oa].bank for seed_id, seed in self.seeds.items()}

    def bank_of(self, area: str) -> str:
        return self.bank[area]

    def put(self, oa: str, area: str, how: str) -> None:
        before = self.area_of.get(oa)
        if before is not None:
            self.of_area[before].discard(oa)
            self.pieces.pop(before, None)
        self.area_of[oa] = area
        self.how[oa] = how
        self.of_area.setdefault(area, set()).add(oa)
        self.pieces.pop(area, None)

    def body_first(self, area: str) -> tuple[tuple[str, ...], ...]:
        """The pieces of an area: the one that holds its seed first, or else the largest."""
        if area not in self.pieces:
            home = self.seeds[area].oa
            self.pieces[area] = tuple(
                sorted(
                    _pieces(self.of_area.get(area, ()), self.beside),
                    key=lambda piece: (home not in piece, -len(piece), piece),
                )
            )
        return self.pieces[area]

    def best_beside(self, piece: Sequence[str], but: str | None) -> str | None:
        """The area some output areas share most border with, on a bank they may be on."""
        banks = {self.cells[oa].bank for oa in piece} - {NOT_DRAWN}
        shared: dict[str, list[float]] = {}
        for oa in piece:
            for other, metres in self.beside.get(oa, {}).items():
                area = self.area_of.get(other)
                if area is None or area == but:
                    continue
                if any(_other_bank(bank, self.bank_of(area)) for bank in banks):
                    continue
                shared.setdefault(area, []).append(metres)
        ranked = sorted((-math.fsum(sorted(metres)), area) for area, metres in shared.items())
        return ranked[0][1] if ranked else None

    def grow(self, roads: Roads) -> None:
        """Each output area to the seed that is nearest after weighing, on its own bank."""
        standing = {
            seed_id: (seed.node, seed.to_node)
            for seed_id, seed in self.seeds.items()
            if seed_id not in self.absorbed
        }
        reach = nearest_seeds(roads, standing, self.rules.nearest)
        for oa, cell in self.cells.items():
            weighed = [
                _weighed(cell, near, self.cells[self.seeds[near.seed].oa], self.rules)
                for near in (reach.get(cell.node, ()) if cell.node else ())
                if not _other_bank(cell.bank, self.bank_of(near.seed))
            ]
            self.choices[oa] = tuple(sorted(weighed, key=lambda each: (each.weighed, each.seed)))
        self.take_a_bank()
        for oa, cell in self.cells.items():
            fit = [
                choice
                for choice in self.choices[oa]
                if not _other_bank(cell.bank, self.bank_of(choice.seed))
            ]
            self.choices[oa] = tuple(fit)
            if fit:
                self.put(oa, fit[0].seed, NEAREST)

    def take_a_bank(self) -> None:
        """Put each seed that has no bank on the bank most of what it would be given is on.

        A seed west of where the water ends lies in an output area with no
        bank. It may still be the nearest seed to output areas on both banks,
        round the end of the water. It is put on the bank that more of them
        are on, and of two banks with as many, on the north. A seed that
        would be given no output area with a bank stays with none.
        """
        first: dict[str, dict[str, int]] = {}
        for oa, choices in self.choices.items():
            bank = self.cells[oa].bank
            if choices and bank != NOT_DRAWN and self.bank[choices[0].seed] == NOT_DRAWN:
                counted = first.setdefault(choices[0].seed, {})
                counted[bank] = counted.get(bank, 0) + 1
        for seed_id, counted in sorted(first.items()):
            self.bank[seed_id] = min(counted, key=lambda bank: (-counted[bank], bank))

    def join_the_unreached(self) -> None:
        """Every output area no seed reached, to the area it shares most border with.

        Output areas no seed reached that lie side by side are joined as one,
        so that a run of them is not shared out between two areas by chance.
        One with no area beside it goes to the seed nearest in a straight
        line on a bank it may be on.
        """
        while True:
            left = [oa for oa in self.cells if oa not in self.area_of]
            if not left:
                return
            moved = False
            for piece in _pieces(left, self.beside):
                area = self.best_beside(piece, None)
                if area is not None:
                    for oa in piece:
                        self.put(oa, area, JOINED)
                    moved = True
            if not moved:
                for oa in left:
                    self.put(oa, self.nearest_in_a_straight_line(oa), JOINED)

    def nearest_in_a_straight_line(self, oa: str) -> str:
        cell = self.cells[oa]
        ranked = sorted(
            (
                _other_bank(cell.bank, self.bank_of(seed_id)),
                math.dist(cell.centre, seed.point),
                seed_id,
            )
            for seed_id, seed in self.seeds.items()
            if seed_id not in self.absorbed
        )
        return ranked[0][2]

    def first_stray(self) -> tuple[tuple[str, ...], str] | None:
        """The first part that is cut off from its area and has another area beside it."""
        for area in sorted(self.of_area):
            for piece in self.body_first(area)[1:]:
                to = self.best_beside(piece, area)
                if to is not None:
                    return piece, to
        return None

    def first_too_small(self) -> tuple[str, str] | None:
        """The smallest area under the least size, and the area it becomes part of."""
        small = sorted(
            (len(cells), area)
            for area, cells in self.of_area.items()
            if 0 < len(cells) < self.rules.smallest and area not in self.rules.kept
        )
        for _, area in small:
            to = self.best_beside(sorted(self.of_area[area]), area)
            if to is not None:
                return area, to
        return None

    def repair(self) -> None:
        """Join what is cut off, then take in the smallest area, until nothing moves."""
        while True:
            stray = self.first_stray()
            if stray is not None:
                for oa in stray[0]:
                    self.put(oa, stray[1], STRAY)
                continue
            small = self.first_too_small()
            if small is None:
                return
            area, to = small
            held = sorted(self.of_area[area])
            for oa in held:
                self.put(oa, to, SMALL)
            self.absorbed[area] = Absorbed(area, to, UNDER_SMALLEST, held=len(held))

    def drop_the_empty(self) -> None:
        """A seed that was given no output area becomes part of the area its point lies in."""
        for seed_id, seed in self.seeds.items():
            if seed_id not in self.absorbed and not self.of_area.get(seed_id):
                self.absorbed[seed_id] = Absorbed(seed_id, self.area_of[seed.oa], NO_OUTPUT_AREA)

    def absorbed_at_the_end(self) -> tuple[Absorbed, ...]:
        """Every seed that stands for no area, with the area it became part of at the end."""
        return tuple(
            Absorbed(
                seed=seed_id,
                into=self.stands_as(seed_id),
                why=self.absorbed[seed_id].why,
                far=self.absorbed[seed_id].far,
                lies_in=self.area_of[self.seeds[seed_id].oa],
                held=self.absorbed[seed_id].held,
            )
            for seed_id in sorted(self.absorbed)
        )

    def stands_as(self, seed_id: str) -> str:
        """The area a seed stands for at the end: its own, or the one it became part of."""
        seen: set[str] = set()
        while seed_id in self.absorbed and seed_id not in seen:
            seen.add(seed_id)
            seed_id = self.absorbed[seed_id].into
        return seed_id

    def given(self, oa: str) -> Given:
        """One output area, with its margin worked out against the areas that stand."""
        area = self.area_of[oa]
        best: dict[str, float] = {}
        for choice in self.choices[oa]:
            best.setdefault(self.stands_as(choice.seed), choice.weighed)
        ranked = sorted((weighed, other) for other, weighed in best.items())
        if not ranked:
            # No seed reached it, so no distance stands behind where it was put.
            return Given(oa, area, self.how[oa], 0, "", ())
        if ranked[0][1] != area:
            # It is not where the distances put it: the repair moved it.
            return Given(oa, area, self.how[oa], 0, ranked[0][1], self.choices[oa])
        if len(ranked) == 1:
            return Given(oa, area, self.how[oa], None, "", self.choices[oa])
        (first, _), (next_best, second) = ranked[0], ranked[1]
        margin = math.floor(100 * (next_best - first) / first) if first > 0 else MOST_MARGIN
        return Given(oa, area, self.how[oa], min(margin, MOST_MARGIN), second, self.choices[oa])

    def drawn(self, area: str) -> Drawn:
        cells = tuple(sorted(self.of_area[area]))
        boroughs: dict[str, int] = {}
        for oa in cells:
            boroughs[self.cells[oa].borough] = boroughs.get(self.cells[oa].borough, 0) + 1
        shared: dict[str, list[float]] = {}
        for oa in cells:
            for other, metres in self.beside.get(oa, {}).items():
                if self.area_of[other] != area:
                    shared.setdefault(self.area_of[other], []).append(metres)
        return Drawn(
            area=area,
            cells=cells,
            hectares=math.fsum(self.cells[oa].hectares for oa in cells),
            boroughs=dict(sorted(boroughs.items())),
            primary_borough=min(boroughs, key=lambda code: (-boroughs[code], code)),
            pieces=tuple(self.body_first(area)),
            banks=tuple(sorted({self.cells[oa].bank for oa in cells})),
            seed_inside=self.seeds[area].oa in self.of_area[area],
            beside={other: math.fsum(sorted(shared[other])) for other in sorted(shared)},
        )


# The most a margin is written as: a second choice ten times as far, or further.
MOST_MARGIN = 999


def _listed(drawn: Mapping[str, Drawn]) -> tuple[Listed, ...]:
    found: list[Listed] = []
    for area, each in sorted(drawn.items()):
        if len(each.pieces) > 1:
            cut_off = tuple(oa for piece in each.pieces[1:] for oa in piece)
            found.append(Listed(area, IN_PIECES, cut_off))
        if NORTH in each.banks and SOUTH in each.banks:
            found.append(Listed(area, BOTH_BANKS))
        if not each.seed_inside:
            found.append(Listed(area, SEED_OUTSIDE))
    return tuple(found)


def draft(
    cells: Sequence[Cell],
    seeds: Sequence[Seed],
    roads: Roads,
    beside: Beside,
    rules: Rules | None = None,
) -> Draft:
    """The draft: every output area in exactly one area, from the ground and the seeds.

    `beside` gives, for each output area, the output areas it shares a side
    with and how many metres they share. It stops where the ground does not
    fit together. It never leaves an output area out, and never gives one twice.
    """
    rules = rules or Rules()
    _held(cells, seeds, beside, roads)
    drafting = _Drafting(cells, seeds, beside, rules)
    drafting.absorbed.update(too_close(seeds, roads, rules))
    drafting.grow(roads)
    if not drafting.area_of:
        raise ValueError("no seed reached any output area")
    drafting.join_the_unreached()
    drafting.repair()
    drafting.drop_the_empty()
    given = {oa: drafting.given(oa) for oa in drafting.cells}
    standing = [area for area in sorted(drafting.of_area) if drafting.of_area[area]]
    drawn = {area: drafting.drawn(area) for area in standing}
    if set(given) != set(drafting.cells) or any(each.area not in drawn for each in given.values()):
        raise ValueError("an output area is in no area, or in one that does not stand")
    return Draft(
        given=given,
        drawn=drawn,
        absorbed=drafting.absorbed_at_the_end(),
        listed=_listed(drawn),
        rules=rules,
    )
