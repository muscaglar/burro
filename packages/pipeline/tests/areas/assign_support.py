"""What the tests of the draft share: a made-up town, as plain values.

Nothing here is real. The town is a grid of square output areas in the North
Sea, each 100 metres a side, with a road node at the centre of each and a link
between every two that lie side by side. A tidal river may run between two of
its rows, with a bridge over it. Every code is shaped like the statistics
office's and is none it has given out, and every seed's id begins `syn-`.

    row 3  | 19 | 20 | 21 | 22 | 23 | 24 |        north bank
    row 2  | 13 | 14 | 15 | 16 | 17 | 18 |
           ~~~~~~~~~~~ the river ~~~~~~~~~~~      a bridge at each column in `bridges`
    row 1  |  7 |  8 |  9 | 10 | 11 | 12 |        south bank
    row 0  |  1 |  2 |  3 |  4 |  5 |  6 |
"""

import random
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, replace

from burro_pipeline.areas.assign import NORTH, NOT_DRAWN, SOUTH, Cell, Seed
from burro_pipeline.areas.grow import Link, Roads, roads_of

EAST, NORTH_OF, SIDE = 700_000.0, 400_000.0, 100.0
QUILLHAVEN, TALLOWGATE = "E09000901", "E09000902"

Square = tuple[int, int]


def code(square: Square, columns: int) -> str:
    column, row = square
    return f"E00999{row * columns + column + 1:03d}"


def node(square: Square) -> str:
    return f"syn-node-{square[1]:02d}-{square[0]:02d}"


def centre(square: Square) -> tuple[float, float]:
    return EAST + (square[0] + 0.5) * SIDE, NORTH_OF + (square[1] + 0.5) * SIDE


@dataclass(frozen=True)
class Town:
    """A made-up town: its output areas, its roads and the sides its output areas share."""

    columns: int
    rows: int
    cells: tuple[Cell, ...]
    links: tuple[Link, ...]
    beside: Mapping[str, Mapping[str, float]]

    @property
    def roads(self) -> Roads:
        return roads_of(self.links)

    def oa(self, column: int, row: int) -> str:
        return code((column, row), self.columns)

    def seed(self, number: int, column: int, row: int, weight: float = 6.0) -> Seed:
        """A seed at the centre of one output area."""
        square = (column, row)
        return Seed(
            seed_id=f"syn-n{number:04d}",
            point=centre(square),
            weight=weight,
            oa=code(square, self.columns),
            node=node(square),
        )

    def without_links(self, gone: Collection[tuple[Square, Square]]) -> "Town":
        """The town with some links taken up, each named by the two squares it joined."""
        ends = {frozenset((node(a), node(b))) for a, b in gone}
        kept = tuple(link for link in self.links if frozenset((link.start, link.end)) not in ends)
        return replace(self, links=kept)

    def without_sides(self, gone: Collection[tuple[Square, Square]]) -> "Town":
        """The town with some shared sides taken away, as where water lies between."""
        pairs = {frozenset((code(a, self.columns), code(b, self.columns))) for a, b in gone}
        beside = {
            oa: {
                other: metres
                for other, metres in others.items()
                if frozenset((oa, other)) not in pairs
            }
            for oa, others in self.beside.items()
        }
        return replace(self, beside=beside)

    def on_the_roads(self) -> "Town":
        """The town with each output area at its node only where a link still reaches it."""
        held = self.roads.number_of
        cells = tuple(cell if cell.node in held else replace(cell, node="") for cell in self.cells)
        return replace(self, cells=cells)

    def with_cells(self, changed: Mapping[str, Cell]) -> "Town":
        return replace(self, cells=tuple(changed.get(cell.oa, cell) for cell in self.cells))

    def shuffled(self, seed: int) -> "Town":
        """The same town, handed over in another order."""
        drawn = random.Random(seed)  # noqa: S311
        cells, links = list(self.cells), list(self.links)
        drawn.shuffle(cells)
        drawn.shuffle(links)
        turned = [Link(link.end, link.start, link.metres) for link in links]
        names = list(self.beside)
        drawn.shuffle(names)
        beside = {
            oa: dict(drawn.sample(sorted(self.beside[oa].items()), len(self.beside[oa])))
            for oa in names
        }
        return replace(self, cells=tuple(cells), links=tuple(turned), beside=beside)


def town(
    columns: int = 6,
    rows: int = 4,
    *,
    river_above_row: int | None = None,
    bridges: Sequence[int] = (),
    borough_from_column: int | None = None,
) -> Town:
    """A grid of output areas. A river above a row parts the banks, but for its bridges.

    Every output area of a column at or beyond `borough_from_column` is in the
    second borough. With a river, a link crosses it only at a bridge, and no
    side is shared across it.
    """
    squares = [(column, row) for row in range(rows) for column in range(columns)]
    cells: list[Cell] = []
    for square in squares:
        bank = NOT_DRAWN
        if river_above_row is not None:
            bank = NORTH if square[1] > river_above_row else SOUTH
        second = borough_from_column is not None and square[0] >= borough_from_column
        cells.append(
            Cell(
                oa=code(square, columns),
                borough=TALLOWGATE if second else QUILLHAVEN,
                centre=centre(square),
                bank=bank,
                node=node(square),
                to_node=0,
                hectares=1.0,
            )
        )
    links: list[Link] = []
    beside: dict[str, dict[str, float]] = {code(square, columns): {} for square in squares}
    for column, row in squares:
        for other in ((column + 1, row), (column, row + 1)):
            if other[0] >= columns or other[1] >= rows:
                continue
            over_water = river_above_row is not None and row == river_above_row and other[1] > row
            if not over_water or column in bridges:
                links.append(Link(node((column, row)), node(other), SIDE))
            if not over_water:
                beside[code((column, row), columns)][code(other, columns)] = SIDE
                beside[code(other, columns)][code((column, row), columns)] = SIDE
    return Town(columns, rows, tuple(cells), tuple(links), beside)
