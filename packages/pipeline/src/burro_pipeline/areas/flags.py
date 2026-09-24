"""What makes a border flagged: each rule, the number it turns on, and the words a desk shows.

Section 9 of the areas design lists what a reviewer is shown first. A person
cannot look at every area, so the draft says which to look at and why. Every
rule is here once, as one function, with the number it turns on in `Rules`.
Every number is a first guess, as the design says of its own thresholds.

| Flag | An area is flagged when |
|---|---|
| `one_publisher` | Fewer than two publishers write its name, and no official publisher |
| | writes it for a populated place at a point inside the area |
| `seeds_close` | Its seed is within 600 m of another seed, in a straight line |
| `follows_nothing` | Under a quarter of its border runs along a line that can be named |
| `size_unlike_neighbours` | It holds over three times its neighbours' median, or under a third |
| `two_pieces` | Its output areas are in more than one piece |
| `two_boroughs` | An output area of it lies outside its main borough |
| `margin_under_10` | A fifth or more of it is nearly as close to the next area |
| `least_compact` | Its shape is among the least compact twentieth |
| `two_centres` | Two town centres of district class or above lie mostly in it |
| `both_banks` | The draft lists it as lying on both banks of the tidal water |
| `seed_outside` | The draft lists its seed as lying in an output area of another area |
| `no_receipt` | Its name or its seed rests on a file that has no receipt |

A line that can be named is a borough line, a ward line or a main road. "Nearly
as close" is a margin under 10%: the second choice is under a tenth further.
`Rules.lines` writes each rule in full, from the numbers in use.

A flag is about the border or about the name. `one_publisher` and `no_receipt`
are about the name: a person settles them where names are read. The founder has
decided that one official publisher is enough for a name it writes for a
populated place at a point inside the area: decision record 0022, and
`draft_decided.py`. So `one_publisher` is raised only where that rule does not
fit the name. Every other flag is about the border.

A flag about the border says how much of the area it puts in doubt, in one of
two ways. It points at output areas, each with how unsure the method is of it
from 0 to 1. Or it is of the area as a whole, where no output area is more in
doubt than another. `flags_order.py` turns both into what is at stake.

| Flag | Points at | How unsure |
|---|---|---|
| `margin_under_10` | Each cell with a margin under 10% | 1 at no margin, falling to 0 at 10% |
| `two_pieces` | The cells cut off from the largest piece | 1 |
| `two_boroughs` | The cells outside the main borough | A half |
| `seeds_close` | The cells on the border with the other area | A half |
| `follows_nothing` | The cells on the stretches that follow nothing | The whole area |
| `size_unlike_neighbours`, `least_compact`, `two_centres` | No cell | The whole area |
| `both_banks`, `seed_outside` | No cell | The whole area |

A flag may say more of what it means, for the desk to mark on its map. The
flag for a seed close to another names the area of that seed. The flag for a
border that follows nothing names each side that follows none: the output area
of this area, and the one beside it. The flag for two town centres names each
centre as its file writes it.

A rule reads the draft and the ground, and nothing else. The ground is places
and land: outlines, sides, boroughs, wards, roads and town centres. Nothing here
reads who lives anywhere. An area's size is its homes where the licence gate
gives the count of homes for this use, and its output areas where it does not.

A flag says why in words a person can read. Every name in the words is a name
a file holds, and every number is one that was worked out here. Where the
draft gives no margin the rule for margins says nothing: no margin is made up.

The arithmetic repeats: every loop is over a sorted list and every sum is
`math.fsum`.
"""

import math
import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property

Point = tuple[float, float]

BORDERS, NAMES = "borders", "names"

ONE_PUBLISHER = "one_publisher"
SEEDS_CLOSE = "seeds_close"
FOLLOWS_NOTHING = "follows_nothing"
SIZE = "size_unlike_neighbours"
TWO_PIECES = "two_pieces"
TWO_BOROUGHS = "two_boroughs"
MARGIN = "margin_under_10"
LEAST_COMPACT = "least_compact"
TWO_CENTRES = "two_centres"
BOTH_BANKS = "both_banks"
SEED_OUTSIDE = "seed_outside"
NO_RECEIPT = "no_receipt"
SAME_NAME = "same_name_elsewhere"

# What an area's size is counted in.
HOMES, CELLS = "homes", "output areas"


@dataclass(frozen=True)
class Rules:
    """The number each rule turns on. Each is a first guess, to be tuned on a real draft."""

    # A name that the rule on one official publisher does not fit needs this many
    # publishers (areas design, section 6).
    publishers: int = 2
    # Two seeds nearer than this, in metres in a straight line. The design joins two
    # seeds within 600 m by road, so a pair this near was kept apart by the roads alone.
    seeds_metres: float = 600.0
    # The least share of a border that runs along a line a person could name. On the first
    # draft of London the share was 38 in 100 at the median, and under 25 for one area in 7.
    follows_share: float = 0.25
    # A side runs along a main road where it is within this many metres of one. An
    # outline is drawn to about 20 m, and a road is a line down its middle.
    road_metres: float = 20.0
    # How many times the middle of its neighbours an area may hold, or one over it.
    size_times: float = 3.0
    # A cell nearer than this to its second choice, in hundredths (design, section 9).
    margin_percent: float = 10.0
    # The share of an area in such cells at which the area is flagged. On the first draft
    # of London the share was 12 in 100 at the median, and 20 or more for one area in 7.
    margin_share: float = 0.2
    # The share of all areas that are the least compact (design, section 9).
    least_compact_share: float = 0.05
    # How many town centres lying mostly in one area are too many.
    centres: int = 2
    # How many cells outside its main borough put an area in two boroughs.
    cells_outside: int = 1
    # How unsure the method is of a cell outside its area's main borough, and of a cell on
    # the border between two seeds that are close, from 0 to 1. The method chose each by
    # distance, and the design doubts both choices.
    doubt_across_a_borough: float = 0.5
    doubt_between_seeds: float = 0.5

    def lines(self) -> dict[str, str]:
        """Each rule in one line a person can read, with the number it turns on."""
        return {
            ONE_PUBLISHER: f"Fewer than {self.publishers} publishers write its name, and no "
            "official publisher writes it for a populated place at a point inside the area.",
            SEEDS_CLOSE: f"Its seed is within {_whole(self.seeds_metres)} m of the seed of "
            "another area, in a straight line.",
            FOLLOWS_NOTHING: f"Under {_percent(self.follows_share)}% of its border with other "
            "areas runs along a borough line, a ward line or a main road. A main road is a "
            f"motorway, an A road or a B road, within {_plain(self.road_metres)} m.",
            SIZE: f"It holds over {_plain(self.size_times)} times what the areas beside it hold "
            f"at the median, or under 1 part in {_plain(self.size_times)} of it.",
            TWO_PIECES: "Its output areas are in more than one piece.",
            TWO_BOROUGHS: f"{self.cells_outside} or more of its output areas lie outside its "
            "main borough.",
            MARGIN: f"{_percent(self.margin_share)}% or more of it is in output areas nearly as "
            f"close to the next area: a margin under {_plain(self.margin_percent)}%.",
            LEAST_COMPACT: f"Its shape is among the least compact "
            f"{_percent(self.least_compact_share)}% of all areas.",
            TWO_CENTRES: f"{self.centres} or more town centres of district class or above lie "
            "mostly in it.",
            BOTH_BANKS: "The draft lists it as lying on both banks of the tidal water.",
            SEED_OUTSIDE: "The draft lists its seed as lying in an output area of another area.",
            NO_RECEIPT: "Its name or its seed rests on a file that has no receipt.",
            SAME_NAME: "Another area has the same name.",
        }


# What the desk says for a flag, as its file of questions holds words by code. A test
# holds the two together: a flag the desk has no words for would stop its fill.
WORDS: Mapping[str, Mapping[str, str]] = {
    BORDERS: {
        MARGIN: "a border cell is nearly as close to the next area",
        LEAST_COMPACT: "its shape is among the least compact",
        TWO_BOROUGHS: "it lies in two boroughs",
        TWO_CENTRES: "it holds two town centres",
        ONE_PUBLISHER: "one publisher writes its name, and one is not enough for it",
        SEEDS_CLOSE: "its seed is close to the seed of another area",
        FOLLOWS_NOTHING: "its border follows no line that can be named",
        SIZE: "it is far larger or far smaller than the areas beside it",
        TWO_PIECES: "it is in two pieces",
        BOTH_BANKS: "it lies on both banks of the tidal water",
        SEED_OUTSIDE: "its seed lies outside it",
        NO_RECEIPT: "it rests on a file that has no receipt",
    },
    NAMES: {
        ONE_PUBLISHER: "one publisher writes this name, and one is not enough for it",
        SAME_NAME: "the same name stands in another place",
        NO_RECEIPT: "it rests on a file that has no receipt",
    },
}
# The flags that are about the name, and not about where the border runs.
ABOUT_THE_NAME = frozenset({ONE_PUBLISHER, NO_RECEIPT, SAME_NAME})
# The flags that say an area breaks a rule the design holds a release to: an area is in
# one piece, and on one bank (areas design, section 10).
BREAKS_A_RULE = frozenset({TWO_PIECES, BOTH_BANKS})


@dataclass(frozen=True)
class Cell:
    """One output area, as the draft places it and as the ground holds it."""

    oa: str
    area: str
    # The code of its borough, from the lookup.
    borough: str
    # The code of the ward that holds most of it. Empty where no ward was read.
    ward: str = ""
    hectares: float = 0.0
    # The length of its outline, in metres.
    perimeter: float = 0.0
    # How much nearer its area is than its second choice, in hundredths. None where the
    # draft does not say.
    margin: float | None = None
    # The area it would be in if not this one. Empty where the draft does not say.
    second: str = ""
    # Its homes, where the gate gives them for this use. None where it does not.
    homes: int | None = None


@dataclass(frozen=True)
class Side:
    """What two output areas share of their outlines."""

    a: str
    b: str
    metres: float
    # How much of it runs along a main road.
    along_a_road: float = 0.0


@dataclass(frozen=True)
class Area:
    """One drafted area, with what stands behind its name."""

    area_id: str
    name: str
    # Where its seed is, on the National Grid. None where the draft does not say.
    seed: Point | None = None
    # Who writes its name, from the rows of evidence that code has checked.
    publishers: tuple[str, ...] = ()
    # Whether an official publisher writes its name for a populated place at a point
    # inside it. One publisher is then enough: `draft_decided.py`.
    by_the_rule: bool = False
    # The sources its name or its seed rests on that have no receipt.
    unreceipted: tuple[str, ...] = ()
    # The town centres of district class or above that lie mostly in it, as written.
    centres: tuple[str, ...] = ()
    # What the draft lists as wrong with it, that its method could not put right.
    listed: tuple[str, ...] = ()


@dataclass(frozen=True)
class Flag:
    """One reason to look at one area."""

    queue: str
    # The item of the desk's queue: the area's id for a border, `n:` and the id for a name.
    item: str
    area: str
    code: str
    # Why, in words the desk can show.
    why: str
    # The cells the flag points at, for the desk to show.
    cells: tuple[str, ...] = ()
    # How unsure the method is of each of those cells, from 0 to 1, in their order.
    doubt: tuple[float, ...] = ()
    # Whether the flag puts the area as a whole in doubt, and no one cell more than another.
    whole: bool = False
    # What the flag means, for the desk to mark on its map. The sides of the border that
    # the flag is about, each as the cell of this area and the cell beside it. The areas
    # whose seed it is about. The town centres it is about, as their file writes them.
    sides: tuple[tuple[str, str], ...] = ()
    seeds: tuple[str, ...] = ()
    centres: tuple[str, ...] = ()


@dataclass(frozen=True)
class Draft:
    """The draft and the ground, as plain values. The rules read this and nothing else."""

    areas: Mapping[str, Area]
    cells: Mapping[str, Cell]
    sides: Sequence[Side]
    # The name of each borough, by its code, as the lookup writes it.
    boroughs: Mapping[str, str] = field(default_factory=dict[str, str])

    def __post_init__(self) -> None:
        if any(cell.area not in self.areas for cell in self.cells.values()):
            raise ValueError("an output area is in an area the draft does not hold")
        if any(side.a not in self.cells or side.b not in self.cells for side in self.sides):
            raise ValueError("a side is of an output area the draft does not hold")

    @cached_property
    def weighed_by(self) -> str:
        """Homes where every cell has a count of them, and output areas where any has none."""
        return HOMES if all(cell.homes is not None for cell in self.cells.values()) else CELLS

    def weight(self, oa: str) -> float:
        homes = self.cells[oa].homes
        return float(homes) if self.weighed_by == HOMES and homes is not None else 1.0

    def weight_of(self, oas: Iterable[str]) -> float:
        return math.fsum(self.weight(oa) for oa in sorted(oas))

    @cached_property
    def cells_of(self) -> Mapping[str, tuple[str, ...]]:
        """The cells of each area, in the order of their codes. An area may have none."""
        found: dict[str, list[str]] = {area_id: [] for area_id in sorted(self.areas)}
        for oa in sorted(self.cells):
            found[self.cells[oa].area].append(oa)
        return {area_id: tuple(oas) for area_id, oas in found.items()}

    @cached_property
    def held(self) -> Mapping[str, float]:
        """What each area holds: its homes, or its output areas."""
        return {area_id: self.weight_of(oas) for area_id, oas in self.cells_of.items()}

    @cached_property
    def borders(self) -> Mapping[str, tuple[Side, ...]]:
        """For each area, the sides its cells share with the cells of another area."""
        found: dict[str, list[Side]] = {area_id: [] for area_id in sorted(self.areas)}
        for side in sorted(self.sides, key=lambda side: (side.a, side.b)):
            here, there = self.cells[side.a].area, self.cells[side.b].area
            if here != there:
                found[here].append(side)
                found[there].append(side)
        return {area_id: tuple(sides) for area_id, sides in found.items()}

    @cached_property
    def neighbours(self) -> Mapping[str, tuple[str, ...]]:
        """The areas each area shares a side with, in the order of their ids."""
        found: dict[str, set[str]] = {area_id: set() for area_id in self.areas}
        for area_id, sides in self.borders.items():
            for side in sides:
                found[area_id] |= {self.cells[side.a].area, self.cells[side.b].area}
        return {area_id: tuple(sorted(found[area_id] - {area_id})) for area_id in sorted(found)}

    @cached_property
    def pieces(self) -> Mapping[str, tuple[tuple[str, ...], ...]]:
        """The pieces each area is in, the largest first. A piece is cells joined by sides."""
        leader = {oa: oa for oa in self.cells}

        def find(oa: str) -> str:
            while leader[oa] != oa:
                leader[oa] = leader[leader[oa]]
                oa = leader[oa]
            return oa

        for side in self.sides:
            if self.cells[side.a].area == self.cells[side.b].area:
                first, second = sorted((find(side.a), find(side.b)))
                leader[second] = first
        grouped: dict[str, dict[str, list[str]]] = {area_id: {} for area_id in self.areas}
        for oa in sorted(self.cells):
            grouped[self.cells[oa].area].setdefault(find(oa), []).append(oa)
        return {
            area_id: tuple(
                sorted(
                    (tuple(piece) for piece in pieces.values()),
                    key=lambda piece: (-self.weight_of(piece), -len(piece), piece),
                )
            )
            for area_id, pieces in sorted(grouped.items())
        }

    @cached_property
    def compactness(self) -> Mapping[str, float]:
        """How compact each area is: 1 for a circle, and towards 0 as its outline lengthens.

        It is 4 pi times the ground over the square of the outline's length. The
        outline is what is left of the cells' outlines once every side between two
        cells of the area is taken out. An area with no ground has no figure.
        """
        inside: dict[str, list[float]] = {area_id: [] for area_id in self.areas}
        for side in self.sides:
            if self.cells[side.a].area == self.cells[side.b].area:
                inside[self.cells[side.a].area].append(side.metres)
        found: dict[str, float] = {}
        for area_id, oas in self.cells_of.items():
            ground = math.fsum(self.cells[oa].hectares for oa in oas) * 10_000
            around = math.fsum(self.cells[oa].perimeter for oa in oas)
            around -= 2 * math.fsum(sorted(inside[area_id]))
            if ground > 0 and around > 0:
                found[area_id] = min(1.0, 4 * math.pi * ground / around**2)
        return found


def _whole(value: float) -> str:
    return format(round(value), ",d")


def _plain(value: float) -> str:
    return format(value, ".12g")


def _percent(share: float) -> str:
    return _plain(round(share * 100, 1))


def _counted(draft: Draft, held: float) -> str:
    unit = draft.weighed_by.removesuffix("s") if round(held) == 1 else draft.weighed_by
    return f"{_whole(held)} {unit}"


def _of_its_cells(few: int, all_of_them: int) -> str:
    """`2 of its 7 output areas are`, with the verb that fits the first number."""
    return f"{few} of its {all_of_them} output areas {'is' if few == 1 else 'are'}"


def _listed(names: Sequence[str]) -> str:
    return ", ".join(names[:-1]) + (" and " if len(names) > 1 else "") + names[-1]


def _border(
    area: Area,
    code: str,
    why: str,
    cells: Mapping[str, float] | None = None,
    *,
    whole: bool = False,
    sides: Iterable[tuple[str, str]] = (),
    seeds: Iterable[str] = (),
    centres: Iterable[str] = (),
) -> Flag:
    pointed = dict(sorted((cells or {}).items()))
    return Flag(
        queue=BORDERS,
        item=area.area_id,
        area=area.area_id,
        code=code,
        why=why,
        cells=tuple(pointed),
        doubt=tuple(pointed.values()),
        whole=whole,
        sides=tuple(sorted(set(sides))),
        seeds=tuple(sorted(set(seeds))),
        centres=tuple(centres),
    )


# The rules. Each takes the draft and the numbers, and gives the flags it raises.


def one_publisher(draft: Draft, rules: Rules) -> list[Flag]:
    """An area whose name too few publishers write, where the rule on one official
    publisher does not fit the name."""
    found: list[Flag] = []
    for area in _in_order(draft):
        if area.by_the_rule or len(set(area.publishers)) >= rules.publishers:
            continue
        if area.publishers:
            why = (
                f"One publisher writes its name: {sorted(set(area.publishers))[0]}. It "
                "does not write it for a populated place at a point inside the area."
            )
        else:
            why = "No publisher's record of its name has been checked."
        found.append(_border(area, ONE_PUBLISHER, why))
        found.append(Flag(NAMES, f"n:{area.area_id}", area.area_id, ONE_PUBLISHER, why))
    return found


def seeds_close(draft: Draft, rules: Rules) -> list[Flag]:
    seeded = [area for area in _in_order(draft) if area.seed is not None]
    found: list[Flag] = []
    for area in seeded:
        near = sorted(
            (math.dist(_seed(area), _seed(other)), other.area_id)
            for other in seeded
            if other.area_id != area.area_id
        )
        if not near or near[0][0] >= rules.seeds_metres:
            continue
        metres, nearest = near[0]
        between = {
            oa: rules.doubt_between_seeds
            for side in draft.borders[area.area_id]
            for oa in (side.a, side.b)
            if draft.cells[oa].area == area.area_id
            and nearest in (draft.cells[side.a].area, draft.cells[side.b].area)
        }
        why = (
            f"Its seed is {_whole(metres)} m from the seed of {draft.areas[nearest].name}, "
            f"in a straight line. Under {_whole(rules.seeds_metres)} m is flagged."
        )
        found.append(_border(area, SEEDS_CLOSE, why, between, seeds=(nearest,)))
    return found


def _seed(area: Area) -> Point:
    if area.seed is None:
        raise ValueError("an area with no seed has no place")
    return area.seed


def _follows(draft: Draft, side: Side) -> float:
    """How much of a side runs along a line a person could name."""
    a, b = draft.cells[side.a], draft.cells[side.b]
    if a.borough != b.borough or (a.ward and b.ward and a.ward != b.ward):
        return side.metres
    return min(side.metres, side.along_a_road)


def follows_nothing(draft: Draft, rules: Rules) -> list[Flag]:
    found: list[Flag] = []
    for area in _in_order(draft):
        sides = draft.borders[area.area_id]
        length = math.fsum(side.metres for side in sides)
        if length <= 0:
            continue
        share = math.fsum(_follows(draft, side) for side in sides) / length
        if share >= rules.follows_share:
            continue
        stretches = [side for side in sides if _follows(draft, side) < side.metres / 2]
        loose = {
            oa: 0.0
            for side in stretches
            for oa in (side.a, side.b)
            if draft.cells[oa].area == area.area_id
        }
        # Each side that follows nothing, as the cell of this area and the one beside it.
        own_first = [
            (side.a, side.b) if draft.cells[side.a].area == area.area_id else (side.b, side.a)
            for side in stretches
        ]
        why = (
            f"{_percent(share)}% of its border with other areas runs along a borough line, "
            f"a ward line or a main road. Under {_percent(rules.follows_share)}% is flagged."
        )
        found.append(_border(area, FOLLOWS_NOTHING, why, loose, whole=True, sides=own_first))
    return found


def size_unlike_neighbours(draft: Draft, rules: Rules) -> list[Flag]:
    found: list[Flag] = []
    for area in _in_order(draft):
        beside = [draft.held[other] for other in draft.neighbours[area.area_id]]
        held = draft.held[area.area_id]
        if not beside or held <= 0:
            continue
        middle = statistics.median(sorted(beside))
        if middle <= 0 or 1 / rules.size_times <= held / middle <= rules.size_times:
            continue
        way = "larger" if held > middle else "smaller"
        why = (
            f"It holds {_counted(draft, held)}. The {len(beside)} areas beside it hold "
            f"{_whole(middle)} at the median. It is far {way}."
        )
        found.append(_border(area, SIZE, why, whole=True))
    return found


def two_pieces(draft: Draft, rules: Rules) -> list[Flag]:
    del rules
    found: list[Flag] = []
    for area in _in_order(draft):
        pieces = draft.pieces[area.area_id]
        if len(pieces) < 2:
            continue
        cut_off = [oa for piece in pieces[1:] for oa in piece]
        few = _of_its_cells(len(cut_off), len(draft.cells_of[area.area_id]))
        why = f"It is in {len(pieces)} pieces. {few} cut off from the largest."
        found.append(_border(area, TWO_PIECES, why, dict.fromkeys(cut_off, 1.0)))
    return found


def main_borough(draft: Draft, area_id: str) -> str:
    """The borough that holds most of an area, by what the area is weighed by."""
    held: dict[str, list[str]] = {}
    for oa in draft.cells_of[area_id]:
        held.setdefault(draft.cells[oa].borough, []).append(oa)
    ranked = sorted(held, key=lambda borough: (-draft.weight_of(held[borough]), borough))
    return ranked[0] if ranked else ""


def two_boroughs(draft: Draft, rules: Rules) -> list[Flag]:
    found: list[Flag] = []
    for area in _in_order(draft):
        main = main_borough(draft, area.area_id)
        oas = draft.cells_of[area.area_id]
        outside = [oa for oa in oas if draft.cells[oa].borough != main]
        if len(outside) < rules.cells_outside or not outside:
            continue
        boroughs = sorted({draft.cells[oa].borough for oa in oas} - {main})
        names = [draft.boroughs.get(code, code) for code in (main, *boroughs)]
        share = draft.weight_of(outside) / draft.held[area.area_id]
        why = (
            f"It lies in {_listed(names)}. {_of_its_cells(len(outside), len(oas))} outside "
            f"{names[0]}: {_percent(share)}% of its {draft.weighed_by}."
        )
        across = dict.fromkeys(outside, rules.doubt_across_a_borough)
        found.append(_border(area, TWO_BOROUGHS, why, across))
    return found


def close_cells(draft: Draft, rules: Rules, area_id: str) -> dict[str, float]:
    """The cells of an area nearly as close to the next, each with how unsure the method was.

    The doubt is 1 where the margin is nothing, and falls in a straight line to
    nothing where the margin is the number the rule turns on.
    """
    return {
        oa: 1 - margin / rules.margin_percent
        for oa in draft.cells_of[area_id]
        if (margin := draft.cells[oa].margin) is not None and 0 <= margin < rules.margin_percent
    }


def margin_under(draft: Draft, rules: Rules) -> list[Flag]:
    found: list[Flag] = []
    for area in _in_order(draft):
        oas = draft.cells_of[area.area_id]
        close = close_cells(draft, rules, area.area_id)
        if not close or draft.weight_of(close) < rules.margin_share * draft.held[area.area_id]:
            continue
        share = draft.weight_of(close) / draft.held[area.area_id]
        why = (
            f"{_of_its_cells(len(close), len(oas))} nearly as close to the next area, with a "
            f"margin under {_plain(rules.margin_percent)}%: {_percent(share)}% of its "
            f"{draft.weighed_by}."
        )
        found.append(_border(area, MARGIN, why, close))
    return found


def least_compact(draft: Draft, rules: Rules) -> list[Flag]:
    ranked = sorted(draft.compactness, key=lambda area_id: (draft.compactness[area_id], area_id))
    taken = math.ceil(len(ranked) * rules.least_compact_share) if ranked else 0
    found: list[Flag] = []
    for place, area_id in enumerate(ranked[:taken], start=1):
        why = (
            f"Its shape is the {_ordinal(place)} least compact of {len(ranked)} areas. "
            f"The least compact {_percent(rules.least_compact_share)}% are flagged."
        )
        found.append(_border(draft.areas[area_id], LEAST_COMPACT, why, whole=True))
    return sorted(found, key=lambda flag: flag.item)


def _ordinal(place: int) -> str:
    ending = "th" if place % 100 in (11, 12, 13) else {1: "st", 2: "nd", 3: "rd"}.get(place % 10)
    return f"{place}{ending or 'th'}"


def two_centres(draft: Draft, rules: Rules) -> list[Flag]:
    found: list[Flag] = []
    for area in _in_order(draft):
        if len(area.centres) < rules.centres:
            continue
        why = f"{len(area.centres)} town centres lie mostly in it: {_listed(area.centres)}."
        found.append(_border(area, TWO_CENTRES, why, whole=True, centres=area.centres))
    return found


def listed(draft: Draft, rules: Rules) -> list[Flag]:
    """What the draft itself lists as wrong with an area, that its method could not put right."""
    del rules
    why = {
        BOTH_BANKS: "It lies on both banks of the tidal water. The method could not put it right.",
        SEED_OUTSIDE: "Its seed lies in an output area of another area.",
    }
    return [
        _border(area, code, why[code], whole=True)
        for area in _in_order(draft)
        for code in (BOTH_BANKS, SEED_OUTSIDE)
        if code in area.listed
    ]


def no_receipt(draft: Draft, rules: Rules) -> list[Flag]:
    del rules
    found: list[Flag] = []
    for area in _in_order(draft):
        if not area.unreceipted:
            continue
        sources = _listed(sorted(set(area.unreceipted)))
        why = f"Its name or its seed rests on a file that has no receipt: {sources}."
        found.append(_border(area, NO_RECEIPT, why))
        found.append(Flag(NAMES, f"n:{area.area_id}", area.area_id, NO_RECEIPT, why))
    return found


def same_name(draft: Draft, rules: Rules) -> list[Flag]:
    del rules
    named: dict[str, list[str]] = {}
    for area in _in_order(draft):
        named.setdefault(area.name.casefold(), []).append(area.area_id)
    found: list[Flag] = []
    for area in _in_order(draft):
        others = [each for each in named[area.name.casefold()] if each != area.area_id]
        if not others:
            continue
        codes = {main_borough(draft, each) for each in others} - {""}
        where = sorted(draft.boroughs.get(code, code) for code in codes)
        has = "area has" if len(others) == 1 else "areas have"
        why = f"{len(others)} other {has} the same name"
        why += f", in {_listed(where)}." if where else "."
        found.append(Flag(NAMES, f"n:{area.area_id}", area.area_id, SAME_NAME, why))
    return found


def _in_order(draft: Draft) -> list[Area]:
    return [draft.areas[area_id] for area_id in sorted(draft.areas)]


# Every rule, in the order its flags are written.
RULES = (
    one_publisher,
    seeds_close,
    follows_nothing,
    size_unlike_neighbours,
    two_pieces,
    two_boroughs,
    margin_under,
    least_compact,
    two_centres,
    listed,
    no_receipt,
    same_name,
)


def not_worked_out(draft: Draft) -> dict[str, str]:
    """The rules that could say nothing of this draft, each with why. Nothing is made up."""
    missing: dict[str, str] = {}
    if all(cell.margin is None for cell in draft.cells.values()):
        missing[MARGIN] = "The draft gives no margin for any output area."
    if all(area.seed is None for area in draft.areas.values()):
        missing[SEEDS_CLOSE] = "The draft gives no place for any seed."
    if not draft.sides:
        missing[FOLLOWS_NOTHING] = "No side between two output areas was read."
        missing[TWO_PIECES] = "No side between two output areas was read."
        missing[SIZE] = "No side between two output areas was read."
    if all(cell.perimeter <= 0 for cell in draft.cells.values()):
        missing[LEAST_COMPACT] = "No outline of an output area was read."
    if not any(cell.ward for cell in draft.cells.values()):
        missing["wards"] = "No ward was read, so a border is held to boroughs and roads alone."
    return missing


def flags_of(
    draft: Draft, rules: Rules | None = None, queues: Sequence[str] = (BORDERS, NAMES)
) -> list[Flag]:
    """Every flag of a draft for the queues that are asked for, by queue, item and rule."""
    rules = rules or Rules()
    order = {rule_code: at for at, rule_code in enumerate(rules.lines())}
    found = [flag for rule in RULES for flag in rule(draft, rules) if flag.queue in queues]
    return sorted(found, key=lambda flag: (flag.queue, flag.item, order[flag.code]))
