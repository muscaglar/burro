"""A draft of the made-up city, so that the desk can be tried before a real file exists.

It reads the synthetic release and nothing else, and it writes a draft folder of the
shape docs/design/desk.md, section 8, asks of the areas build, the pipeline and the
research run. Every name is made from a name of the release, every id begins `syn-`,
and every venue says in its name that it is made up. It describes no real place.

The release holds no cells, no sentences and no claims. So cells are cut here as a grid,
and every case a person must be able to decide is planted by hand, in the tables below:
a name with one publisher, a name in two places, a border in doubt, an area in two
boroughs, a sentence for each answer. The release names one borough. The draft cuts the
city into three, so that a border between boroughs can be tried.

The same release gives the same draft, byte for byte. Standard library only.
"""

import hashlib
import json
import math
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, Final, cast

from desk.fill import draft, layers
from desk.fill.gate import MADE_UP
from desk.fill.layers import Point, Unfit, canonical

type Square = tuple[int, int]

# The side of a cell, in degrees: about 330 metres, which gives an area about 46 cells.
STEP: Final = 0.003
# The publishers of the made-up city. They stand in for a gazetteer of names, a list of
# items, a file of town centres and a file of wards.
NAMES, ITEMS, CENTRES, WARDS = (
    f"{MADE_UP}-{word}" for word in ("names", "items", "centres", "wards")
)
RETRIEVED: Final = "2026-09-23"

# The three boroughs of the draft, and the two lines that part them.
CITY, EAST, SOUTH = "Quillhaven", "East Quillhaven", "South Quillhaven"
EAST_OF, SOUTH_OF = 0.0445, -0.006

# Planted: areas whose name only one publisher writes.
ONE_PUBLISHER: Final = ("syn-n0008", "syn-n0016", "syn-n0020")
# Planted: a second spelling, as one publisher writes the name.
ALSO_WRITTEN: Final[Mapping[str, str]] = {
    "syn-n0004": "Dulcimer green",
    "syn-n0010": "Hollinsworth quay",
    "syn-n0012": "Lantern-Yard",
    "syn-n0017": "Otterby fields",
}
# Planted: pairs of areas whose shared border is in doubt, with a margin under 10%.
IN_DOUBT: Final = (
    ("syn-n0007", "syn-n0012"),
    ("syn-n0018", "syn-n0021"),
    ("syn-n0001", "syn-n0005"),
)
# Planted: a second town centre in one area, a name over several areas, and a name that
# stands in two places.
SECOND_CENTRE: Final = ("Tallowgate Parade", "syn-n0021")
WIDE: Final = ("Quillhaven Waterside", ("syn-n0009", "syn-n0010", "syn-n0011", "syn-n0019"))
TWICE: Final = ("Pellam", "syn-n0003")
# Planted: a name that says who lives there, as one publisher writes it. It is put after
# the name of its area, so that it is a name of the made-up city and of nowhere else.
OF_RESIDENTS: Final = ("Pensioners Row", "syn-n0013")
# Planted: rules put to the founder, each with what it says and what could go wrong. They
# are made up as the city is, and none is adopted. The code, the queue, what the rule
# gives an item it fits, what it says, and what could go wrong. One of them leans on the
# two before it: it settles an item only where the rule the item leans on is adopted too.
BUILT: Final = ("Parade", "Quay", "Yard")
LEANS: Final = "a_made_up_flag_that_asks_nothing"
LEANS_ON: Final = ("two_made_up_publishers_write_it", "a_made_up_smaller_place")
# The flags that the rule that leans says ask nothing of a person.
ASKS_NOTHING: Final = frozenset({"one_publisher", "same_name_elsewhere"})
RULES_PUT: Final = (
    (
        "two_made_up_publishers_write_it",
        "names",
        "proposed",
        "Made up for testing. A name put forward as an area is accepted when the made-up "
        "gazetteer and the made-up list of items write it letter for letter, and it has no "
        "flag.",
        "Made up for testing. The two made-up publishers may have copied one another.",
    ),
    (
        "a_made_up_smaller_place",
        "names",
        "proposed",
        "Made up for testing. Another name is accepted as a smaller place inside its area "
        "when the made-up gazetteer writes it at a point inside, and it has no flag.",
        "Made up for testing. The name stays with its area if the border moves later.",
    ),
    (
        "named_for_a_made_up_building",
        "names",
        "drop",
        f"Made up for testing. A name that ends in {', '.join(BUILT[:-1])} or {BUILT[-1]} is "
        "the name of a street or a building, and is not kept.",
        "Made up for testing. Where such a name is an area today, the draft is made again "
        "without it, and the borders of its neighbours move.",
    ),
    (
        LEANS,
        "names",
        "proposed",
        "Made up for testing. A flag that says only that one made-up publisher writes the "
        "name, or that the same name stands in another place, does not hold a name back "
        "from the rule its records fit. This rule settles a name only where that rule is "
        "adopted too.",
        "Made up for testing. The flag may have been the only sign of a fault.",
    ),
    (
        "every_made_up_border",
        "borders",
        "",
        "Made up for testing. A border that no flag is on is left as drafted, and is "
        "offered to nobody.",
        "Made up for testing. A border that is wrong, and that no rule flags, is looked at "
        "by nobody.",
    ),
)
# Planted, in the map of areas to articles: an article that two areas claim, and a thing
# whose name does not match its article letter for letter.
CLAIMED_TWICE: Final = ("syn-n0007", "syn-n0012")
UNSURE_THING: Final = ("syn-n0001", "Alderwick Primary School", "Alderwick School")
# Planted: figures that moved since the release before, by what they were multiplied by.
MOVED: Final = (
    ("syn-n0002", "venue_food_drink", 0.6),
    ("syn-n0013", "culture_venues", 1.5),
    ("syn-n0021", "park_proximity", 0.75),
)
# Planted: figures that the coverage report would say have no record behind them.
NO_RECORD: Final = (("syn-n0005", "green_cover"), ("syn-n0018", "homes_density"))
# The coverage report's line between `present` and `partial`. A test holds it to the report.
FULLY_COVERED: Final = 0.99

# The eight vibes that people rate, docs/design/vibes.md 6.2, each with a rubric in words
# about streets, buildings and places. These are for the made-up city: the founder writes
# the rubrics for London.
RUBRICS: Final = (
    (
        "homes",
        "Are the homes mostly houses, or mostly flats?",
        "nearly all houses",
        "nearly all flats",
    ),
    ("built_age", "How old do the streets look?", "nearly all built since 2000", "nearly all old"),
    (
        "pace",
        "How much is there to eat, drink and go out to near the homes?",
        "very little",
        "a great deal",
    ),
    (
        "leafy",
        "How much of what you see from the street is trees, hedges and gardens?",
        "very little",
        "a great deal",
    ),
    (
        "village_feel",
        "Does it have a small centre of its own, with old streets and shops?",
        "not at all",
        "very much",
    ),
    (
        "quiet_residential",
        "How quiet are the streets of homes, away from main roads?",
        "not quiet",
        "very quiet",
    ),
    (
        "foodie",
        "How many places to eat and drink stand along its streets?",
        "very few",
        "a great many",
    ),
    (
        "works_warehouses",
        "How much of it is works, depots, warehouses and railway arches?",
        "none",
        "a great deal",
    ),
)

# The pages of a made-up encyclopaedia: the area, the page, its revision, and each
# sentence with its heading and the answer it was planted for. A sentence names only the
# made-up city. Every answer of the queue `sentences` is planted at least once.
PAGES: Final = (
    (
        "syn-n0007",
        4107,
        88307,
        (
            ("", "fit", "Foxholt is a district of Quillhaven."),
            ("", "fit", "It lies between Lantern Yard and Dulcimer Green."),
            ("History", "fit", "The name is first recorded in 1274 as Foxholte."),
            ("History", "fit", "Foxholt Market has been held on the high street since 1880."),
            ("History", "fit", "The station at Foxholt opened in 1907."),
            (
                "History",
                "change_or_price",
                "In recent years Foxholt has become up and coming, and rents have risen.",
            ),
            ("Demography", "residents", "Foxholt is popular with young families."),
            ("Demography", "safety", "It is one of the safest parts of Quillhaven."),
            (
                "Landmarks",
                "praise",
                "The market hall of Foxholt is the finest building in the city.",
            ),
            (
                "Landmarks",
                "person",
                "A well-known painter lived beside the market hall until her death.",
            ),
            ("Landmarks", "not_a_place", "A fox is a small wild animal of the dog family."),
        ),
    ),
    (
        "syn-n0001",
        4021,
        88213,
        (
            ("", "fit", "Alderwick is a district of Quillhaven."),
            ("", "fit", "It stands on the rising ground north of Thrushcombe."),
            ("History", "fit", "The station at Alderwick opened in 1907."),
            ("History", "fit", "The name comes from an old word for a farm among alder trees."),
            (
                "History",
                "not_a_place",
                "The market at Foxholt, to the south, is older than the station.",
            ),
            ("History", "praise", "Alderwick is the most sought-after address in Quillhaven."),
            ("Demography", "residents", "Most of the people who live in Alderwick are retired."),
            ("Landmarks", "fit", "Alderwick Primary School stands beside the green."),
        ),
    ),
    (
        "syn-n0011",
        4311,
        88511,
        (
            ("", "fit", "Kindlewharf is a district of Quillhaven, on the south bank of the river."),
            ("History", "fit", "The wharves of Kindlewharf were built in 1842."),
            (
                "History",
                "change_or_price",
                "The old warehouses have been regenerated as flats that few can afford.",
            ),
            ("Culture", "residents", "Kindlewharf has long been home to artists and students."),
            (
                "Culture",
                "fit",
                "Kindlewharf Studios stands in a former rope works beside the water.",
            ),
            ("Culture", "safety", "The streets behind the wharves were once known for theft."),
        ),
    ),
)
# The claims of the made-up city: the page quoted, which is the page of the claim's own
# area, the sentence quoted, its kind, the thing it names, whether the page gives a
# reference for it, and the answer it was planted for. Every answer of the queue `claims`
# is planted at least once.
CLAIMS: Final = (
    (4021, 3, "history", None, True, "accept"),
    (4021, 4, "name_origin", None, False, "accept"),
    (4021, 5, "history", None, True, "not_this_place"),
    (4107, 3, "name_origin", None, True, "accept"),
    (4107, 4, "known_for", "Foxholt Market", True, "accept"),
    (4107, 7, "history", None, False, "describes_people"),
    (4107, 9, "known_for", "market hall", True, "passes_judgement"),
    (4311, 2, "history", None, True, "accept"),
    (4311, 5, "known_for", "Kindlewharf Studios", True, "accept"),
    (4311, 6, "history", None, True, "not_fair"),
)

# The venues of the made-up city, by kind: how many, the words each name is made with,
# and the category as a feed might write it. The first look at Overture Places found
# stage schools under theatre and scout groups under community hall, and one hospital
# on many records: docs/research/data/overture-places.md. Each is planted here.
VENUES: Final = (
    ("theatre", 7, "Made-up Theatre", "theatre"),
    ("theatre", 7, "Made-up Stage School", "performing_arts_school"),
    ("community_hall", 6, "Made-up Community Hall", "community_centre"),
    ("community_hall", 6, "Made-up Scout Group", "scout_group"),
    ("hospital", 3, "Made-up Hospital", "hospital"),
    ("gym", 8, "Made-up Gym", "gym"),
    ("library", 6, "Made-up Library", "library"),
    ("pub", 20, "Made-up Tap", "pub"),
    ("cafe", 120, "Made-up Cafe", "cafe"),
)
# How many records each made-up hospital has, and the one record that stands under two kinds.
RECORDS_OF_A_HOSPITAL: Final = 3
IN_TWO_KINDS: Final = ("pub", "cafe")
FEEDS: Final = ("made-up feed A", "made-up feed B", "made-up feed C")

# The commons the founder might name: the name, and each match in the made-up file of
# green space as its name, its kind and whether it has a way in.
COMMONS: Final = (
    ("Gorsebeck Forest", ()),
    ("Larkspur Heath", (("", "Public Park Or Garden", True),)),
    ("Alderwick Common", (("Alderwick Common", "Public Park Or Garden", False),)),
    (
        "Marrowfen Common",
        (
            ("Marrowfen Common", "Public Park Or Garden", True),
            ("Marrowfen Common Playing Field", "Playing Field", True),
        ),
    ),
    ("Thrushcombe Green", (("Thrushcombe Green", "Public Park Or Garden", True),)),
    ("Wickerford Heath", (("Wickerford Heath", "Public Park Or Garden", True),)),
)
THE_GREEN: Final = "syn-p0043"
# What the synthetic release says of itself, which its claims say too.
LICENCE: Final = "None. Made up for testing"
ATTRIBUTION: Final = "Synthetic data generated by Burro for testing. It describes no real place."


@dataclass(frozen=True)
class Area:
    area_id: str
    name: str
    seed: Point
    ring: tuple[Point, ...]
    aliases: tuple[str, ...]
    neighbours: tuple[str, ...]


@dataclass(frozen=True)
class City:
    """What the draft is made from: the release, and the cells cut from it."""

    release_id: str
    areas: Mapping[str, Area]
    cells: Mapping[Square, str]
    places: Sequence[Mapping[str, Any]]
    features: Sequence[Mapping[str, Any]]
    metrics: Mapping[str, Mapping[str, Any]]

    def borough_of(self, square: Square) -> str:
        x, y = _middle(square)
        return EAST if x >= EAST_OF else SOUTH if y < SOUTH_OF else CITY

    def squares_of(self, area_id: str) -> list[Square]:
        return sorted(square for square, held in self.cells.items() if held == area_id)

    def home_of(self, area_id: str) -> str:
        """The borough that holds most of an area's cells."""
        count = Counter(self.borough_of(square) for square in self.squares_of(area_id))
        return max(sorted(count), key=lambda borough: count[borough])

    def area_at(self, point: Point) -> str | None:
        return self.cells.get((math.floor(point[0] / STEP), math.floor(point[1] / STEP)))


def _draw(*parts: object) -> int:
    """A number that is the same every time, for what the seed of the release does not set."""
    digest = hashlib.sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4])


def _corner(i: int, j: int) -> Point:
    return (round(i * STEP, layers.DECIMALS), round(j * STEP, layers.DECIMALS))


def _middle(square: Square) -> Point:
    return ((square[0] + 0.5) * STEP, (square[1] + 0.5) * STEP)


def _inside(point: Point, ring: Sequence[Point]) -> bool:
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in pairwise(ring):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def _code(at: int) -> str:
    return f"syn-oa{at:04d}"


# The release


def release_in(source: Path) -> Path:
    """The folder of the release: the one given, or the newest that it holds."""
    if (source / "manifest.json").is_file():
        return source
    held = sorted(each for each in source.glob("*/manifest.json"))
    if not held:
        raise Unfit("No synthetic release is in the folder given")
    return held[-1].parent


def _read(folder: Path, name: str) -> Any:
    try:
        return json.loads((folder / name).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Unfit(f"{name} of the synthetic release cannot be read") from error


def city_of(folder: Path) -> City:
    """The made-up city, with its cells cut. Refuses a release that is not made up."""
    manifest = _read(folder, "manifest.json")
    if manifest.get("synthetic") is not True or not str(manifest.get("release_id")).startswith(
        "syn-"
    ):
        raise Unfit("The release given is not made up, and the made-up draft is made from no other")
    rings = {
        feature["id"]: tuple((x, y) for x, y in feature["geometry"]["coordinates"][0])
        for feature in _read(folder, "geometry.json")["features"]
    }
    areas = {
        held["area_id"]: Area(
            held["area_id"],
            held["name"],
            (held["centroid"][0], held["centroid"][1]),
            rings[held["area_id"]],
            tuple(held["aliases"]),
            tuple(held["neighbours"]),
        )
        for held in _read(folder, "neighbourhoods.json")["neighbourhoods"]
    }
    xs = [x for ring in rings.values() for x, _ in ring]
    ys = [y for ring in rings.values() for _, y in ring]
    cells: dict[Square, str] = {}
    for j in range(math.floor(min(ys) / STEP), math.ceil(max(ys) / STEP)):
        for i in range(math.floor(min(xs) / STEP), math.ceil(max(xs) / STEP)):
            for area_id in sorted(areas):
                if _inside(_middle((i, j)), areas[area_id].ring):
                    cells[i, j] = area_id
                    break
    _repair(cells)
    return City(
        release_id=manifest["release_id"],
        areas=areas,
        cells=cells,
        places=_read(folder, "places.json")["places"],
        features=_read(folder, "features.json")["rows"],
        metrics={held["feature_id"]: held for held in _read(folder, "catalogue.json")["metrics"]},
    )


def _around(square: Square) -> tuple[Square, Square, Square, Square]:
    i, j = square
    return ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1))


def _pieces(squares: Iterable[Square]) -> list[list[Square]]:
    """The parts of a set of squares that hold together, side to side. The largest is first."""
    left = set(squares)
    pieces: list[list[Square]] = []
    while left:
        reached, piece = [min(left)], set[Square]()
        while reached:
            square = reached.pop()
            if square in left:
                left.remove(square)
                piece.add(square)
                reached += _around(square)
        pieces.append(sorted(piece))
    return sorted(pieces, key=lambda piece: (-len(piece), piece))


def _repair(cells: dict[Square, str]) -> None:
    """An area must be one piece: docs/design/london-data-areas.md, section 4, step 7.
    A stray part joins the area it shares most sides with."""
    for area_id in sorted(set(cells.values())):
        own = [square for square, held in cells.items() if held == area_id]
        for stray in _pieces(own)[1:]:
            beside = Counter(
                cells[other]
                for square in stray
                for other in _around(square)
                if cells.get(other, area_id) != area_id
            )
            if beside:
                most = max(sorted(beside), key=lambda other: beside[other])
                cells.update(dict.fromkeys(stray, most))


def made_on(source: Path) -> str:
    """The day the release was built, which is the day its draft is said to be made on."""
    return str(_read(release_in(source), "manifest.json")["built_at"])[:10]


# Shapes


def _sides(squares: Iterable[Square]) -> dict[Square, list[Square]]:
    """Every side of a set of squares that has no square of the set beyond it, with the
    set on its left. The keys and values are corners."""
    held = set(squares)
    sides: dict[Square, list[Square]] = {}
    for i, j in sorted(held):
        around = (
            ((i, j - 1), (i, j), (i + 1, j)),
            ((i + 1, j), (i + 1, j), (i + 1, j + 1)),
            ((i, j + 1), (i + 1, j + 1), (i, j + 1)),
            ((i - 1, j), (i, j + 1), (i, j)),
        )
        for beyond, start, end in around:
            if beyond not in held:
                sides.setdefault(start, []).append(end)
    return sides


def _turn(came: Square, at: Square, to: Square) -> int:
    """How far a step turns from the step before: 0 is left, 1 straight on, 2 right."""
    ahead = (at[0] - came[0], at[1] - came[1])
    step = (to[0] - at[0], to[1] - at[1])
    cross = ahead[0] * step[1] - ahead[1] * step[0]
    return 0 if cross > 0 else 2 if cross < 0 else 1


def _rings(squares: Iterable[Square]) -> list[list[Square]]:
    """The outlines of a set of squares, each a closed ring of corners with no corner that
    lies on a straight line between its neighbours."""
    sides = _sides(squares)
    rings: list[list[Square]] = []
    while sides:
        first = min(sides)
        ring, came, at = [first], first, sides[first].pop()
        while at != first:
            ring.append(at)
            ways = sides[at]
            to = min(ways, key=lambda way: _turn(came, at, way))
            ways.remove(to)
            came, at = at, to
        ring.append(first)
        for corner in [corner for corner, ways in sides.items() if not ways]:
            del sides[corner]
        bends = [
            corner
            for before, corner, after in zip([ring[-2], *ring], ring, ring[1:], strict=False)
            if _turn(before, corner, after) != 1
        ]
        rings.append([*bends, bends[0]])
    return rings


def _area(ring: Sequence[Square]) -> float:
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in pairwise(ring)) / 2


def outline(squares: Iterable[Square]) -> dict[str, Any]:
    """The shape of a set of squares: a polygon, or several where the set is in pieces."""
    rings = _rings(squares)
    outer = [ring for ring in rings if _area(ring) > 0]
    holes = [ring for ring in rings if _area(ring) < 0]
    polygons = [
        [ring, *(hole for hole in holes if _inside(_nudged(hole), [_as_point(c) for c in ring]))]
        for ring in outer
    ]
    shapes = [[[list(_corner(i, j)) for i, j in ring] for ring in polygon] for polygon in polygons]
    if len(shapes) == 1:
        return {"type": "Polygon", "coordinates": shapes[0]}
    return {"type": "MultiPolygon", "coordinates": shapes}


def _as_point(corner: Square) -> Point:
    return (float(corner[0]), float(corner[1]))


def _nudged(hole: Sequence[Square]) -> Point:
    """A point just off the first corner of a hole, so that it lies on no line of the grid."""
    return (hole[0][0] + 0.25, hole[0][1] + 0.25)


def compactness(squares: Sequence[Square]) -> float:
    """How near a shape is to a circle: 4 pi times its area, over its edge squared."""
    edge = sum(len(ways) for ways in _sides(squares).values())
    return 4 * math.pi * len(squares) / edge**2


def _feature(code: str, geometry: Mapping[str, Any], /, **properties: str | int) -> dict[str, Any]:
    return {"type": "Feature", "id": code, "properties": properties, "geometry": dict(geometry)}


def _square(square: Square) -> dict[str, Any]:
    i, j = square
    ring = [
        _corner(i, j),
        _corner(i + 1, j),
        _corner(i + 1, j + 1),
        _corner(i, j + 1),
        _corner(i, j),
    ]
    return {"type": "Polygon", "coordinates": [[list(point) for point in ring]]}


def _point(point: Point) -> dict[str, Any]:
    return {"type": "Point", "coordinates": [round(value, layers.DECIMALS) for value in point]}


def _ring_round(point: Point, radius: float) -> dict[str, Any]:
    """Eight points round a middle: the outline of a made-up town centre."""
    ring = [
        [
            round(point[0] + radius * math.cos(turn * math.pi / 4), layers.DECIMALS),
            round(point[1] + radius * math.sin(turn * math.pi / 4), layers.DECIMALS),
        ]
        for turn in range(8)
    ]
    return {"type": "Polygon", "coordinates": [[*ring, ring[0]]]}


# The tables of names


@dataclass(frozen=True)
class Record:
    """One publisher's record of one name: a row of `name_evidence.csv`, and a point drawn."""

    area_id: str
    name: str
    source_id: str
    # The tier the name is proposed for: empty for the name of the area itself.
    kind: str = ""
    as_written: str = ""
    at: Point | None = None

    @property
    def role(self) -> str:
        return {"": draft.PRIMARY, "wide": draft.WIDE}.get(self.kind, draft.ALIAS)

    @property
    def field(self) -> str:
        """The column of the publisher's file that the name was read from."""
        if self.source_id == ITEMS:
            return "label" if self.kind in ("", "wide") else "also_known_as"
        return {NAMES: "name1", CENTRES: "sitename", WARDS: "name"}[self.source_id]

    @property
    def locates(self) -> str:
        placed = self.at is not None and self.source_id in (NAMES, ITEMS) and self.kind != "wide"
        return "point_inside" if placed else "polygon_overlap"


def _centres(city: City) -> list[tuple[str, str, Point]]:
    """The town centres: each district of the release, and the one planted. A name, the
    area it lies in and its middle."""
    found = [
        (str(place["name"]), area_id, (place["centroid"][0], place["centroid"][1]))
        for place in city.places
        if place["kind"] == "district"
        and (area_id := city.area_at((place["centroid"][0], place["centroid"][1]))) is not None
    ]
    name, area_id = SECOND_CENTRE
    x, y = city.areas[area_id].seed
    return [*found, (name, area_id, (x + STEP, y - STEP))]


def _wards(city: City) -> dict[str, list[Square]]:
    """The wards: blocks of five cells by five, each named for the area most of it lies in."""
    blocks: dict[Square, list[Square]] = {}
    for square in sorted(city.cells):
        blocks.setdefault((square[0] // 5, square[1] // 5), []).append(square)
    wards: dict[str, list[Square]] = {}
    for block in sorted(blocks):
        count = Counter(city.cells[square] for square in blocks[block])
        most = city.areas[max(sorted(count), key=lambda area_id: count[area_id])].name
        held = sum(1 for name in wards if name == most or name.startswith(f"{most} ward "))
        wards[most if not held else f"{most} ward {held + 1}"] = blocks[block]
    return wards


def records_of(city: City) -> list[Record]:
    """Every record of every name, in the order its id is given in."""
    found: list[Record] = []
    wards = _wards(city)
    centred = {name: at for name, _, at in _centres(city)}
    for area_id, area in sorted(city.areas.items()):
        found.append(Record(area_id, area.name, NAMES, at=area.seed))
        if area_id not in ONE_PUBLISHER:
            written = ALSO_WRITTEN.get(area_id, area.name)
            found.append(Record(area_id, area.name, ITEMS, as_written=written, at=area.seed))
            if area.name in wards:
                found.append(Record(area_id, area.name, WARDS))
            if area.name in centred:
                found.append(Record(area_id, area.name, CENTRES, at=centred[area.name]))
        found += [
            Record(area_id, alias, ITEMS, "same_ground", at=area.seed) for alias in area.aliases
        ]
    for name, area_id, at in _centres(city):
        if name != city.areas[area_id].name:
            found.append(Record(area_id, name, CENTRES, "inside", at=at))
            if _draw("names", name) % 2:
                found.append(Record(area_id, name, NAMES, "inside", at=at))
    wide, over = WIDE
    found += [Record(area_id, wide, ITEMS, "wide", at=city.areas[area_id].seed) for area_id in over]
    twice, area_id = TWICE
    x, y = city.areas[area_id].seed
    found.append(Record(area_id, twice, NAMES, "inside", at=(x, y + STEP)))
    of_residents, area_id = OF_RESIDENTS
    x, y = city.areas[area_id].seed
    name = f"{city.areas[area_id].name} {of_residents}"
    found.append(Record(area_id, name, NAMES, "inside", at=(x - STEP, y)))
    return found


def _record_id(at: int) -> str:
    return f"syn-r{at:04d}"


def _names(city: City, records: Sequence[Record]) -> dict[str, Sequence[Mapping[str, object]]]:
    ids = {at: _record_id(at + 1) for at in range(len(records))}
    seeds = {
        record.area_id: ids[at]
        for at, record in enumerate(records)
        if record.role == draft.PRIMARY and record.source_id == NAMES
    }
    areas = [
        {
            "area_id": area_id,
            "slug": draft.slug(area.name),
            "name": area.name,
            "primary_borough": city.home_of(area_id),
            "seed_record": seeds[area_id],
            "review_state": "drafted",
            "superseded_by": "",
        }
        for area_id, area in sorted(city.areas.items())
    ]
    evidence = [
        {
            "area_id": record.area_id,
            "name": record.name,
            "role": record.role,
            "source_id": record.source_id,
            "record_id": ids[at],
            "as_written": record.as_written or record.name,
            "field": record.field,
            "locates": record.locates,
            "data_date": RETRIEVED,
            "retrieved_on": RETRIEVED,
            "snapshot_sha256": hashlib.sha256(record.source_id.encode("utf-8")).hexdigest(),
            "checked": "true",
            "chosen_by": "",
            "chosen_on": "",
        }
        for at, record in enumerate(records)
    ]
    seen: set[tuple[str, str]] = set()
    aliases: list[dict[str, object]] = []
    for at, record in enumerate(records):
        if record.role != draft.PRIMARY and (record.name, record.area_id) not in seen:
            seen.add((record.name, record.area_id))
            aliases.append(
                {
                    "alias": record.name,
                    "area_id": record.area_id,
                    "kind": record.kind,
                    "source_id": record.source_id,
                    "record_id": ids[at],
                }
            )
    return {"areas.csv": areas, "name_evidence.csv": evidence, "aliases.csv": aliases}


# The cells, and what flags an area


def _codes(city: City) -> dict[Square, str]:
    return {
        square: _code(at)
        for at, square in enumerate(sorted(city.cells, key=lambda s: (s[1], s[0])), 1)
    }


def _beside(city: City, square: Square) -> list[str]:
    """The other areas a cell has a side with, in order."""
    here = city.cells[square]
    return sorted({city.cells[each] for each in _around(square) if each in city.cells} - {here})


def _cells(city: City) -> list[dict[str, object]]:
    codes, wards = _codes(city), _wards(city)
    ward_of = {square: name for name, squares in wards.items() for square in squares}
    rows: list[dict[str, object]] = []
    for square in sorted(city.cells, key=lambda s: codes[s]):
        here, beside = city.cells[square], _beside(city, square)
        if any((here, other) in IN_DOUBT or (other, here) in IN_DOUBT for other in beside):
            doubted = [o for o in beside if (here, o) in IN_DOUBT or (o, here) in IN_DOUBT]
            margin, second = 2 + _draw("margin", codes[square]) % 8, doubted[0]
        elif beside:
            margin, second = 12 + _draw("margin", codes[square]) % 30, beside[0]
        else:
            others = (area for area in city.areas.values() if area.area_id != here)
            nearest = min(
                others, key=lambda area: (math.dist(area.seed, _middle(square)), area.area_id)
            )
            margin, second = 45 + _draw("margin", codes[square]) % 50, nearest.area_id
        rows.append(
            {
                "oa21cd": codes[square],
                "area_id": here,
                "basis": "auto",
                "evidence": f"margin={margin};second={second};ward={ward_of[square]}",
                "decided_by": "",
                "decided_on": "",
                "reason": "",
            }
        )
    return rows


def _flags(
    city: City,
    names: Mapping[str, Sequence[Mapping[str, object]]],
    cells: Sequence[Mapping[str, object]],
    claims: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    """What the areas build and the research run would flag, worked out from the draft."""
    found: list[tuple[str, str, str]] = []
    doubted = {
        str(row["area_id"])
        for row in cells
        if float(draft.evidence_of({"evidence": str(row["evidence"])})["margin"]) < draft.UNDER
    }
    found += [("borders", area_id, "margin_under_10") for area_id in sorted(doubted)]
    by_shape = sorted(
        city.areas, key=lambda area_id: (compactness(city.squares_of(area_id)), area_id)
    )
    found += [
        ("borders", area_id, "least_compact")
        for area_id in by_shape[: max(1, round(len(by_shape) / 20))]
    ]
    for area_id in sorted(city.areas):
        if len({city.borough_of(square) for square in city.squares_of(area_id)}) > 1:
            found.append(("borders", area_id, "two_boroughs"))
    centres = Counter(area_id for _, area_id, _ in _centres(city))
    found += [
        ("borders", area_id, "two_centres") for area_id in sorted(centres) if centres[area_id] > 1
    ]
    found += [("names", f"n:{area_id}", "one_publisher") for area_id in ONE_PUBLISHER]
    claimed, by = CLAIMED_TWICE
    found += [("articles", f"{area}:{_item_of(claimed)}", "two_areas") for area in (claimed, by)]
    found.append(
        ("articles", f"{UNSURE_THING[0]}:{_item_of(UNSURE_THING[0], 't1')}", "unsure_match")
    )
    twice, area_id = TWICE
    elsewhere = sorted(str(row["area_id"]) for row in names["aliases.csv"] if row["alias"] == twice)
    found.append(("names", f"a:{area_id}:{draft.slug(twice)}", "one_publisher"))
    found += [
        ("names", f"a:{each}:{draft.slug(twice)}", "same_name_elsewhere") for each in elsewhere
    ]
    for claim in claims:
        others = (area.name for area in city.areas.values() if area.area_id != claim["area_id"])
        if any(name in str(claim["quote"]) for name in others):
            found.append(("claims", str(claim["claim_id"]), "names_another_area"))
    return [{"queue": queue, "item": item, "flag": flag} for queue, item, flag in found]


def _marks(
    city: City, cells: Sequence[Mapping[str, object]], flags: Sequence[Mapping[str, object]]
) -> list[dict[str, object]]:
    """What the desk marks on the map of a border: each cell with a margin under 10%, each
    cell outside the borough of an area flagged for lying in two, and each town centre
    of an area flagged for holding two."""
    raised = {(str(row["item"]), str(row["flag"])) for row in flags if row["queue"] == "borders"}
    found: list[tuple[str, str, str, str]] = []
    for row in cells:
        said = draft.evidence_of({"evidence": str(row["evidence"])})
        if float(said["margin"]) < draft.UNDER:
            found.append((str(row["area_id"]), "margin_under_10", draft.CELL, str(row["oa21cd"])))
    codes = _codes(city)
    for square, area_id in sorted(city.cells.items(), key=lambda held: codes[held[0]]):
        outside = city.borough_of(square) != city.home_of(area_id)
        if outside and (area_id, "two_boroughs") in raised:
            found.append((area_id, "two_boroughs", draft.CELL, codes[square]))
    for name, area_id, _ in _centres(city):
        if (area_id, "two_centres") in raised:
            found.append((area_id, "two_centres", draft.CENTRE, name))
    return [
        {"queue": "borders", "item": item, "flag": flag, "kind": kind, "what": what}
        for item, flag, kind, what in found
    ]


def _rules(
    names: Mapping[str, Sequence[Mapping[str, object]]], flags: Sequence[Mapping[str, object]]
) -> dict[str, list[dict[str, object]]]:
    """The rules put to the founder, and the items each would settle. A rule settles only
    what no rule before it settles, and nothing that carries a flag. The rule that leans
    settles what another rule would but for a flag that asks nothing, and each of its
    items names that rule."""
    flagged = {(str(row["queue"]), str(row["item"])) for row in flags}
    raised: dict[tuple[str, str], set[str]] = {}
    for row in flags:
        raised.setdefault((str(row["queue"]), str(row["item"])), set()).add(str(row["flag"]))
    areas = {str(row["area_id"]): str(row["name"]) for row in names["areas.csv"]}
    others = [
        (f"a:{row['area_id']}:{draft.slug(str(row['alias']))}", row)
        for row in names["aliases.csv"]
        if row["kind"] != draft.WIDE
    ]
    built = [f"n:{area_id}" for area_id, name in areas.items() if name.endswith(BUILT)]
    built += [item for item, row in others if str(row["alias"]).endswith(BUILT)]
    both = [
        f"n:{area_id}"
        for area_id in areas
        if area_id not in ONE_PUBLISHER and area_id not in ALSO_WRITTEN
    ]
    smaller = [
        item for item, row in others if row["kind"] == "inside" and row["source_id"] == NAMES
    ]
    settles: dict[str, list[tuple[str, str]]] = {
        "two_made_up_publishers_write_it": [("names", item) for item in both],
        "a_made_up_smaller_place": [("names", item) for item in smaller],
        "named_for_a_made_up_building": [("names", item) for item in built],
        "every_made_up_border": [("borders", area_id) for area_id in areas],
    }
    # What a rule would settle but for a flag that asks nothing, by the rule it leans on.
    leaning = {
        each: code
        for code in LEANS_ON
        for each in settles[code]
        if each in flagged and raised[each] <= ASKS_NOTHING
    }
    settles[LEANS] = list(leaning)
    taken: set[tuple[str, str]] = set(flagged) - set(leaning)
    # What a building is named for is taken first: no other rule accepts such a name.
    first = ("named_for_a_made_up_building", LEANS, *settles)
    kept: dict[str, list[tuple[str, str]]] = {}
    for code in dict.fromkeys(first):
        kept[code] = [each for each in dict.fromkeys(settles[code]) if each not in taken]
        taken.update(kept[code])
    return {
        draft.RULES_PUT: [
            {
                "rule": code,
                "queue": queue,
                "gives": gives,
                "says": says,
                "goes_wrong": wrong,
                draft.LEANS_ON: " ".join(LEANS_ON) if code == LEANS else "",
            }
            for code, queue, gives, says, wrong in RULES_PUT
        ],
        draft.RULED: [
            {
                "rule": code,
                "queue": queue,
                "item": item,
                draft.LEANS_ON: leaning[queue, item] if code == LEANS else "",
            }
            for code, *_ in RULES_PUT
            for queue, item in sorted(kept[code])
        ],
    }


# The layers


def _collection(
    layer: str, group: str, sources: Iterable[str], features: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "desk": {
            "layer": layer,
            "group": group,
            "source_ids": sorted(set(sources)),
            "synthetic": True,
        },
        "features": list(features),
    }


def _colours(city: City) -> dict[str, int]:
    """A colour for each area that no area beside it has."""
    beside: dict[str, set[str]] = {area_id: set() for area_id in city.areas}
    for square, here in city.cells.items():
        beside[here].update(_beside(city, square))
    colours: dict[str, int] = {}
    for area_id in sorted(city.areas):
        taken = {colours[other] for other in beside[area_id] if other in colours}
        colours[area_id] = next(colour for colour in range(layers.COLOURS) if colour not in taken)
    return colours


def _within(box: Sequence[float], feature: Mapping[str, Any]) -> bool:
    west, south, east, north = box
    return any(
        west <= x <= east and south <= y <= north
        for ring in layers.rings_of(feature["geometry"])
        for x, y in ring
    )


def _drawn(city: City, records: Sequence[Record]) -> dict[tuple[str, str], dict[str, Any]]:
    """Every layer of every group: each borough with a margin of two cells, and `all`."""
    codes, colours = _codes(city), _colours(city)
    cells = {
        square: _feature(
            codes[square],
            _square(square),
            area=area_id,
            colour=colours[area_id],
            borough=city.borough_of(square),
        )
        for square, area_id in city.cells.items()
    }
    areas = [
        _feature(area_id, outline(city.squares_of(area_id)), name=city.areas[area_id].name)
        for area_id in sorted(city.areas)
    ]
    wards = [
        _feature(f"syn-w{at:02d}", outline(squares), name=name)
        for at, (name, squares) in enumerate(_wards(city).items(), 1)
    ]
    centres = [
        _feature(
            f"syn-t{at:02d}",
            _ring_round(middle, STEP),
            **{"name": name, "class": "major" if at == 1 else "district"},
        )
        for at, (name, _, middle) in enumerate(_centres(city), 1)
    ]
    pairs = sorted(
        {
            tuple(sorted((area_id, other)))
            for area_id, area in city.areas.items()
            for other in area.neighbours
        }
    )
    roads = [
        _feature(
            f"syn-rd{at:03d}",
            {
                "type": "LineString",
                "coordinates": [
                    list(_point(city.areas[one].seed)["coordinates"]),
                    list(_point(city.areas[other].seed)["coordinates"]),
                ],
            },
            **{
                "class": ("A road", "B road", "Minor road")[_draw("road", one, other) % 3],
                "name": f"{city.areas[one].name} to {city.areas[other].name} Road",
            },
        )
        for at, (one, other) in enumerate(pairs, 1)
    ]
    placed = [
        _feature(f"syn-nm{at:03d}", _point(area.seed), name=area.name, kind="Suburban Area")
        for at, area in enumerate((city.areas[area_id] for area_id in sorted(city.areas)), 1)
    ]
    seeds = [
        _feature(
            f"syn-sd{area_id[-4:]}",
            _point(city.areas[area_id].seed),
            area=area_id,
            name=city.areas[area_id].name,
        )
        for area_id in sorted(city.areas)
    ]
    points = [
        _feature(
            _record_id(at),
            _point(
                (
                    record.at[0] + (_draw("x", at) % 7 - 3) * STEP / 10,
                    record.at[1] + (_draw("y", at) % 7 - 3) * STEP / 10,
                )
            ),
            source_id=record.source_id,
            as_written=record.as_written or record.name,
        )
        for at, record in enumerate(records, 1)
        if record.at is not None
    ]
    every = {
        "areas": (areas, [MADE_UP]),
        "wards": (wards, [WARDS]),
        "centres": (centres, [CENTRES]),
        "roads": (roads, [MADE_UP]),
        "names": (placed, [NAMES]),
        "seeds": (seeds, [MADE_UP]),
        "records": (points, sorted({record.source_id for record in records})),
    }
    drawn: dict[tuple[str, str], dict[str, Any]] = {}
    boroughs: list[dict[str, Any]] = []
    for borough in (CITY, EAST, SOUTH):
        group = draft.slug(borough)
        own = {square for square in city.cells if city.borough_of(square) == borough}
        near = {
            (i + di, j + dj) for i, j in own for di in (-2, -1, 0, 1, 2) for dj in (-2, -1, 0, 1, 2)
        }
        held = [cells[square] for square in sorted(near & set(cells), key=lambda s: codes[s])]
        box = layers.bounds(held)
        assert box is not None
        drawn[group, "cells"] = _collection("cells", group, [MADE_UP], held)
        for layer, (features, sources) in every.items():
            drawn[group, layer] = _collection(
                layer, group, sources, [each for each in features if _within(box, each)]
            )
        boroughs.append(_feature(f"syn-b-{group}", outline(own), name=borough))
    drawn[layers.ALL, "boroughs"] = _collection("boroughs", layers.ALL, [MADE_UP], boroughs)
    return drawn


# Figures, venues, sentences, claims and commons


def _figures(city: City) -> dict[str, list[dict[str, object]]]:
    moved = {(area_id, feature_id): factor for area_id, feature_id, factor in MOVED}
    now: list[dict[str, object]] = []
    before: list[dict[str, object]] = []
    for row in city.features:
        area_id, feature_id, value = str(row["area_id"]), str(row["feature_id"]), row["value"]
        metric = city.metrics[feature_id]
        said = [draft.SAYS_THIN] if value is not None and row["coverage"] < FULLY_COVERED else []
        if (area_id, feature_id) in NO_RECORD:
            said.append("no_record")
        now.append(
            {
                "area_id": area_id,
                "feature_id": feature_id,
                "value": "" if value is None else draft.plain(value),
                "unit": metric["unit"],
                "source_id": MADE_UP,
                "vintage": metric["vintage"],
                "flag": " ".join(said),
                "label": metric["label"],
            }
        )
        if value is not None:
            was = round(value * moved.get((area_id, feature_id), 1.0), 1)
            before.append({"area_id": area_id, "feature_id": feature_id, "value": draft.plain(was)})
    return {"figures.csv": now, "figures_before.csv": before}


def _venues(city: City) -> list[dict[str, object]]:
    names = [city.areas[area_id].name for area_id in sorted(city.areas)]
    rows: list[dict[str, object]] = []
    for kind, count, words, category in VENUES:
        for at in range(count):
            place = names[at % len(names)]
            number = "" if at < len(names) else f" {at // len(names) + 1}"
            copies = RECORDS_OF_A_HOSPITAL if kind == "hospital" else 1
            for _ in range(copies):
                rows.append(
                    {
                        "record_id": f"syn-v{len(rows) + 1:04d}",
                        "source_id": MADE_UP,
                        "kind": kind,
                        "name": f"{place} {words}{number}",
                        "category": category,
                        "upstream": FEEDS[_draw("feed", kind, len(rows)) % len(FEEDS)],
                    }
                )
    first, second = IN_TWO_KINDS
    shared = next(row for row in rows if row["kind"] == first)
    rows.append({**shared, "kind": second})
    return rows


def _page_text(sentences: Sequence[tuple[str, str, str]]) -> str:
    return " ".join(text for _, _, text in sentences) + "\n"


def _sentences(city: City) -> list[dict[str, object]]:
    return [
        {
            "page_id": page_id,
            "revision_id": revision_id,
            "title": city.areas[area_id].name,
            "section": section,
            "sentence": at,
            "text": text,
        }
        for area_id, page_id, revision_id, sentences in PAGES
        for at, (section, _, text) in enumerate(sentences, 1)
    ]


def claim_id_of(source_id: str, page_id: int, quote: str) -> str:
    """The id of a made-up claim, made as the pipeline makes the id of any claim."""
    named = hashlib.sha256((canonical([source_id, page_id, quote]) + "\n").encode("utf-8"))
    return f"syn-c{named.hexdigest()[:12]}"


def _claims(city: City) -> list[dict[str, Any]]:
    pages = {
        page_id: (area_id, revision_id, sentences)
        for area_id, page_id, revision_id, sentences in PAGES
    }
    rows: list[dict[str, Any]] = []
    for page_id, number, kind, thing, has_reference, _ in CLAIMS:
        area_id, revision_id, sentences = pages[page_id]
        text, (section, _, quote) = _page_text(sentences), sentences[number - 1]
        raw = hashlib.sha256(f"made-up page {page_id}".encode()).hexdigest()
        rows.append(
            {
                "claim_id": claim_id_of(MADE_UP, page_id, quote),
                "area_id": area_id,
                "kind": kind,
                "quote": quote,
                "thing": thing,
                "source_id": MADE_UP,
                "page": f"f-{raw[:12]}",
                "title": city.areas[area_id].name,
                "url": "",
                "page_id": page_id,
                "revision_id": revision_id,
                "source_dated": "2026-08-30T17:40:02Z",
                "retrieved_at": "2026-09-23T09:12:31Z",
                "raw_sha256": raw,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "start": text.index(quote),
                "end": text.index(quote) + len(quote),
                "section": section,
                "derived": {
                    "method": "model_select",
                    "reader_version": "1",
                    "checks_version": "1",
                    "prompt_version": "made-up",
                    "provider": "made-up-provider",
                    "model": "made-up-model",
                    "second_provider": None,
                    "second_model": None,
                },
                "has_reference": has_reference,
                "review": {
                    "status": draft.PENDING,
                    "reviewed_on": None,
                    "reviewer": None,
                    "reason": None,
                },
                "first_release": city.release_id,
                "licence": LICENCE,
                "attribution": ATTRIBUTION,
                "shortened": True,
            }
        )
    return sorted(rows, key=lambda row: str(row["claim_id"]))


def _commons() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name, matches in COMMONS:
        if not matches:
            rows.append({"name": name, "record_id": "", "match": "", "kind": "", "way_in": ""})
        for match, kind, way_in in matches:
            record = THE_GREEN if match == "Thrushcombe Green" else f"syn-g{len(rows) + 1:04d}"
            rows.append(
                {
                    "name": name,
                    "record_id": record,
                    "match": match,
                    "kind": kind,
                    "way_in": "yes" if way_in else "no",
                }
            )
    return rows


def _page_of(area_id: str) -> int:
    """The page of an area in the made-up encyclopaedia: the one it has, or a number that
    is made of the area's id."""
    held = {area: page_id for area, page_id, _, _ in PAGES}
    return held.get(area_id, 6000 + int(area_id[-4:]))


def _item_of(area_id: str, more: str = "") -> str:
    """The id of a made-up item. It begins `syn-`, as every made-up id does."""
    return f"syn-q{area_id[-4:]}{more}"


def _area_sources(city: City) -> list[dict[str, object]]:
    """The map of areas to articles: each area's own article, the article of each of its
    other names that has one, and the two cases planted."""
    rows: list[dict[str, object]] = []

    def row(area_id: str, qid: str, page_id: int, title: str, role: str) -> None:
        rows.append(
            {
                "area_id": area_id,
                "source_id": ITEMS,
                "qid": qid,
                "page_id": page_id,
                "title": title,
                "role": role,
            }
        )

    for area_id, area in sorted(city.areas.items()):
        row(area_id, _item_of(area_id), _page_of(area_id), area.name, "own")
        for at, alias in enumerate(area.aliases[:1], 1):
            row(area_id, _item_of(area_id, f"a{at}"), _page_of(area_id) + 5000, alias, "alias")
    claimed, by = CLAIMED_TWICE
    row(by, _item_of(claimed), _page_of(claimed), city.areas[claimed].name, "alias")
    area_id, _, title = UNSURE_THING
    row(area_id, _item_of(area_id, "t1"), _page_of(area_id) + 9000, title, "thing")
    return rows


def planted(queue: str) -> Iterator[tuple[str, str]]:
    """Each item of a queue that was planted for an answer, with the answer."""
    if queue == "sentences":
        for _, page_id, _, sentences in PAGES:
            for at, (_, answer, _) in enumerate(sentences, 1):
                yield f"syn-page-{page_id}:{at}", answer
    if queue == "claims":
        pages = {page_id: sentences for _, page_id, _, sentences in PAGES}
        for page_id, number, _, _, _, answer in CLAIMS:
            yield claim_id_of(MADE_UP, page_id, pages[page_id][number - 1][2]), answer


def make(source: Path, folder: Path) -> None:
    """Write the draft of the made-up city to a folder, in place of what is there."""
    city = city_of(release_in(source))
    records = records_of(city)
    names, cells, claims = _names(city, records), _cells(city), _claims(city)
    flags = _flags(city, names, cells, claims)
    tables: dict[str, Sequence[Mapping[str, object]]] = {
        **names,
        "oa_to_area.csv": cells,
        "flags.csv": flags,
        draft.MARKED: _marks(city, cells, flags),
        **_rules(names, flags),
        **_figures(city),
        "kinds.csv": _venues(city),
        "commons.csv": _commons(),
        "area_sources.csv": _area_sources(city),
        "rubrics.csv": [
            {"vibe": vibe, "rubric": f"{asks} 1 is {least}. 5 is {most}."}
            for vibe, asks, least, most in RUBRICS
        ],
    }
    for stale in sorted(folder.glob("layers/*/*.geojson")):
        stale.unlink()
    for name, rows in tables.items():
        draft.write_table(folder, name, rows)
    draft.write_lines(folder, "sentences.jsonl", _sentences(city))
    draft.write_lines(folder, "claims.jsonl", cast(list[Mapping[str, object]], claims))
    for (group, layer), collection in sorted(_drawn(city, records).items()):
        (folder / "layers" / group).mkdir(parents=True, exist_ok=True)
        text = canonical(collection) + "\n"
        (folder / "layers" / group / f"{layer}.geojson").write_text(text, encoding="utf-8")
