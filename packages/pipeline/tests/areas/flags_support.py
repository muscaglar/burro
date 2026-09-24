"""What the tests of flags share: a made-up town, drawn in squares of 100 metres.

Nothing here is real. The town is drawn as rows of letters, one letter for
each output area, and a letter is an area:

    AAABBB
    AAABBB      row 0 is the northern row, and column 0 the western
    CCCDDD

The areas take the names of the made-up city of the synthetic release, and the
two boroughs are Quillhaven and Tallowgate, which do not exist. Every code is
shaped like the statistics office's and is none it has given out. The town
stands in the North Sea.
"""

from collections.abc import Mapping, Sequence

from burro_pipeline.areas.flags import Area, Cell, Draft, Point, Side

# Where the town stands on the National Grid, and the side of a square in metres.
EAST, NORTH, SIDE = 700_000.0, 400_000.0, 100.0
QUILLHAVEN, TALLOWGATE = "E09000901", "E09000902"
BOROUGHS = {QUILLHAVEN: "Quillhaven", TALLOWGATE: "Tallowgate"}
NAMES = {
    "A": "Alderwick",
    "B": "Brackenhythe",
    "C": "Cindermoor",
    "D": "Dulcimer Green",
    "E": "Eskerfold",
    "F": "Foxholt",
}
SURVEY, AUTHORITY = "The Made-up Survey", "The Made-up Authority"

Square = tuple[int, int]


def area_id(letter: str) -> str:
    return f"syn-n{ord(letter) - ord('A') + 1:04d}"


def oa(row: int, column: int) -> str:
    return f"E00999{row:01d}{column:02d}"


def middle(row: int, column: int) -> Point:
    """The middle of a square, on the National Grid."""
    return EAST + (column + 0.5) * SIDE, NORTH - (row + 0.5) * SIDE


def town(
    rows: Sequence[str],
    *,
    split: int | None = None,
    wards: Sequence[str] | None = None,
    margins: Mapping[Square, float] | None = None,
    seconds: Mapping[Square, str] | None = None,
    homes: Mapping[Square, int] | int | None = None,
    seeds: Mapping[str, Square] | None = None,
    publishers: Mapping[str, tuple[str, ...]] | None = None,
    unreceipted: Mapping[str, tuple[str, ...]] | None = None,
    centres: Mapping[str, tuple[str, ...]] | None = None,
    roads: Sequence[tuple[Square, Square]] = (),
    no_margin: bool = False,
) -> Draft:
    """A draft of the made-up town.

    `split` is the first column of Tallowgate: every column west of it is
    Quillhaven. `wards` is drawn as the areas are, one letter a ward. A cell
    has a margin of 50 unless `margins` says another, and none at all with
    `no_margin`. A seed stands in the middle of the square named for its area.
    `roads` names the pairs of squares whose shared side runs along a main road.
    """
    squares = {
        (row, column): letter
        for row, line in enumerate(rows)
        for column, letter in enumerate(line)
        if letter != "."
    }
    letters = sorted(set(squares.values()))

    def homes_of(square: Square) -> int | None:
        if homes is None or isinstance(homes, int):
            return homes
        return homes.get(square, 100)

    cells = {
        oa(*square): Cell(
            oa=oa(*square),
            area=area_id(letter),
            borough=TALLOWGATE if split is not None and square[1] >= split else QUILLHAVEN,
            ward=f"E05999{ord(wards[square[0]][square[1]]):03d}" if wards else "",
            hectares=SIDE * SIDE / 10_000,
            perimeter=4 * SIDE,
            margin=None if no_margin else (margins or {}).get(square, 50.0),
            second=area_id((seconds or {})[square]) if square in (seconds or {}) else "",
            homes=homes_of(square),
        )
        for square, letter in squares.items()
    }
    along = {frozenset(pair) for pair in roads}
    sides = [
        Side(
            a=min(oa(*square), oa(*other)),
            b=max(oa(*square), oa(*other)),
            metres=SIDE,
            along_a_road=SIDE if frozenset((square, other)) in along else 0.0,
        )
        for square in sorted(squares)
        for other in ((square[0], square[1] + 1), (square[0] + 1, square[1]))
        if other in squares
    ]
    areas = {
        area_id(letter): Area(
            area_id=area_id(letter),
            name=NAMES[letter],
            seed=middle(*seeds[letter]) if seeds and letter in seeds else None,
            publishers=(publishers or {}).get(letter, (SURVEY, AUTHORITY)),
            unreceipted=(unreceipted or {}).get(letter, ()),
            centres=(centres or {}).get(letter, ()),
        )
        for letter in letters
    }
    return Draft(areas=areas, cells=cells, sides=sides, boroughs=BOROUGHS)
