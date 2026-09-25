"""The made-up city: every name the synthetic release uses, and the plan it is built to.

Nothing here is a real place. The names are invented, the borough is invented,
and the character of each area is set by hand, so that a person reading this
table can say which areas a prompt ought to find. A test holds a list of real
names and fails if one appears in anything below: London's best known, and
the names that were once used here, were found to be real and have been
replaced.

A new name is made of a word that is no part of any place name, and it sorts
where the name before it did, because ids are given in name order and an id
never moves. This module reads no list of real places. Every name below
was looked up in one encyclopaedia on 2026-09-23, by title and by phrase, and
in no gazetteer: a small street, a farm or a hamlet would not have been found.
Say how a name was checked when adding one. An alias is a name too, and one
that real buildings bear has the borough before it.
"""

from dataclasses import dataclass

from burro_core.ids import PlaceKind

BOROUGH = "Quillhaven"


@dataclass(frozen=True)
class AreaPlan:
    """One area: where it sits on the grid, and what kind of place it is.

    Rows run south to north and columns west to east. Each trait runs from 0
    to 1. How central an area is, how much of it is near the river and how
    far it is from a station are not set here: they are measured from the map.

    No two traits go together across the city, so that no two vibes find the
    same areas: there are flats that are quiet, a leafy area on a main road,
    an old one with no green, and a lively one where little is independent.
    """

    name: str
    row: int
    col: int
    green: float  # gardens, trees and open ground
    lively: float  # places to eat, drink and go out
    indie: float  # how much of that is not part of a chain
    old: float  # homes built before 1919, streets that are protected
    family: float  # primary schools and play space
    street: float  # a high street within a short walk
    industry: float  # works, depots and the roads that serve them
    rankable: bool = True
    aliases: tuple[str, ...] = ()
    # What the seven traits cannot say. Only the parts that came with the vibes read
    # these two, so that adding them moved no older figure.
    offices: float = 0.0  # how much of it is offices, which empty at night and sell no food
    works: float | None = None  # yards and workshops still in use. As `industry` where not set
    # Where an area is not what its place on the map and its green would make it. Where
    # one is not set, homes are flats towards the centre, a park is where the green is,
    # and the main roads follow the centre, the high street and the works.
    flats: float | None = None  # flats, and homes close together
    parks: float | None = None  # public parks within a walk
    roads: float | None = None  # homes that stand on a main road
    # How well served an area is by lines and by buses, where the lines on the map do not
    # say. Only the three parts of Well connected read it, so that adding it moved no
    # older figure.
    links: float | None = None


# In name order, which is the order of their ids. After the name and the cell come the
# seven traits: green, lively, indie, old, family, street, industry.
AREAS = (
    # A leafy hillside of large old houses in their own grounds, a long walk from any
    # station. Few schools, and the green is private: no park is near.
    AreaPlan("Alderwick", 3, 1, 0.95, 0.08, 0.30, 0.70, 0.30, 0.30, 0.00, parks=0.30, roads=0.20),
    # Meadows along the north bank, west of the centre, and the river road through them.
    AreaPlan("Brackenhythe", 1, 0, 0.80, 0.25, 0.60, 0.55, 0.35, 0.50, 0.00, roads=0.60),
    # Works and depots at the eastern end of the Amber line, and the cafes that feed them.
    AreaPlan("Cindermoor", 1, 5, 0.20, 0.20, 0.70, 0.25, 0.30, 0.40, 0.85),
    # Schools and playgrounds, built new along the main road, half way out on the Cobalt line.
    AreaPlan(
        "Dulcimer Green",
        2,
        4,
        0.65,
        0.22,
        0.40,
        0.10,
        0.92,
        0.55,
        0.05,
        aliases=("Dulcimer",),
        roads=0.75,
        links=0.95,
    ),
    # A northern suburb at the end of the Birch line.
    AreaPlan("Eskerfold", 3, 2, 0.60, 0.18, 0.35, 0.25, 0.80, 0.50, 0.00),
    # Cheap and far out, but on the Cobalt line: estates of flats beside the trunk road. The
    # line ends at the bus station, where the routes of the eastern suburbs meet.
    AreaPlan(
        "Farrowmere",
        2,
        5,
        0.40,
        0.15,
        0.25,
        0.10,
        0.70,
        0.45,
        0.25,
        flats=0.95,
        roads=0.65,
        links=1.00,
    ),
    # The busiest high street outside the centre, most of it chains. A large park lies
    # behind it, and the homes stand in quiet streets off it.
    AreaPlan("Foxholt", 2, 3, 0.30, 0.50, 0.25, 0.40, 0.50, 0.95, 0.10, parks=0.90, roads=0.15),
    # The north-western edge: fields, few shops, no station, and the yards of a depot.
    AreaPlan("Gorsebeck", 3, 0, 0.70, 0.05, 0.30, 0.20, 0.40, 0.15, 0.10, works=0.60),
    # Working docks east of the river. Too few homes to rank.
    AreaPlan("Grapnel Dock", 0, 4, 0.05, 0.10, 0.20, 0.30, 0.05, 0.10, 1.00, rankable=False),
    # Old quays turned studios and theatres, one stop west of the centre. Those who come
    # for a show eat at a chain.
    AreaPlan(
        "Hollinsworth Quay",
        1,
        1,
        0.30,
        0.70,
        0.45,
        0.60,
        0.30,
        0.60,
        0.15,
        aliases=("Hollinsworth",),
    ),
    # The south bank opposite the centre: kitchens, bars and an art school, in low terraces.
    # Two lines cross here, and the buses of the south bank turn round.
    AreaPlan("Kindlewharf", 0, 2, 0.25, 0.70, 0.85, 0.45, 0.35, 0.60, 0.20, flats=0.35, links=0.97),
    # Where the city goes out at night, one stop north of the centre: bars and clubs, most
    # of them chains, in old yards that are still workshops by day.
    AreaPlan("Lantern Yard", 2, 2, 0.15, 0.95, 0.20, 0.75, 0.15, 0.85, 0.05, works=0.30),
    # A leafy western suburb with no station of its own, and a parade of shops and cafes.
    AreaPlan("Larkspur Hill", 2, 0, 0.88, 0.30, 0.50, 0.50, 0.75, 0.40, 0.00),
    # Cheap and far out, nowhere near a line, and beside the orbital road.
    AreaPlan("Marrowfen", 3, 4, 0.45, 0.08, 0.20, 0.05, 0.45, 0.25, 0.30, roads=0.80),
    # Family streets along the south bank, built between the wars.
    AreaPlan("Osierholm", 0, 1, 0.60, 0.25, 0.45, 0.15, 0.85, 0.55, 0.05, roads=0.30),
    # An ordinary northern suburb of plain streets. It has no cost estimate, on purpose.
    AreaPlan("Ostrel Vale", 3, 3, 0.20, 0.15, 0.35, 0.20, 0.60, 0.45, 0.05),
    # A new town in the south-east that most surveys have not reached yet.
    AreaPlan(
        "Otterby Fields", 0, 5, 0.35, 0.10, 0.15, 0.00, 0.55, 0.30, 0.15, aliases=("Otterby",)
    ),
    # The centre. Much of it is offices, so it is busiest by day, and what is open is a chain.
    AreaPlan(
        "Pellam Cross",
        1,
        2,
        0.08,
        0.90,
        0.10,
        0.55,
        0.10,
        1.00,
        0.10,
        aliases=("Pellam",),
        offices=1.0,
    ),
    # New flats on the inside of the river's bend, water on two sides: a riverside park,
    # no road through, and little open in the evening.
    AreaPlan("Sable Reach", 0, 3, 0.25, 0.10, 0.40, 0.05, 0.30, 0.45, 0.10, parks=0.70, roads=0.10),
    # Marsh and reservoir in the far north-east. Too few homes to rank.
    AreaPlan("Sedgewater Marsh", 3, 5, 0.90, 0.00, 0.20, 0.10, 0.05, 0.00, 0.05, rankable=False),
    # The old town, beside the centre: terraces on lanes too narrow for a main road.
    AreaPlan("Tallowgate", 1, 3, 0.25, 0.55, 0.80, 1.00, 0.30, 0.85, 0.00, flats=0.30, roads=0.10),
    # A village swallowed by the city, with its green, its own shops and its cottages.
    AreaPlan("Thrushcombe", 2, 1, 0.70, 0.35, 0.95, 0.85, 0.65, 0.80, 0.00, flats=0.20),
    # Around the university: student bars, most of them chains, and a campus closed to cars.
    AreaPlan("Wexmoor", 1, 4, 0.40, 0.90, 0.15, 0.30, 0.25, 0.70, 0.10, roads=0.10),
    # A quiet old riverside village in the south-west corner: stone quays more than gardens.
    AreaPlan("Wickerford", 0, 0, 0.50, 0.15, 0.90, 0.80, 0.30, 0.40, 0.00),
)

CENTRE = "Pellam Cross"

# What is said of the name of an area. A real area is drawn as its publisher draws it, and
# its publisher labels it with its borough and a number: here the borough and the place of
# the area in the order of the ids. The label stands beside the name. A name is a draft
# until a person has checked it, and most of the city's are drafts, as most of a real
# city's are. These three are said to have been checked.
CHECKED = frozenset({"Pellam Cross", "Tallowgate", "Thrushcombe"})
# These two bear no name but their label, so nothing is said of who wrote one: the docks,
# and the new town that no list of names has reached yet.
NOT_NAMED = frozenset({"Grapnel Dock", "Otterby Fields"})


def label_of(number: int) -> str:
    """The label of an area as a publisher would give it: the borough and a number."""
    return f"{BOROUGH} {number:03d}"


@dataclass(frozen=True)
class Lived:
    """Who a made-up census counted in an area, each from 0 to 1. A claim about nothing."""

    young: float  # residents aged 20 to 34
    children: float  # households with dependent children


# Who lived where. Only the four made-up census figures read it, so that adding them moved
# no older figure. Neither trait follows the flats, the schools or the centre, so that no
# two vibes find the same areas: the households that hold children are most where homes
# are cheap and far out, and fewest where the schools and the play space are most. Those
# in their twenties and early thirties are most in flats on a line, and few in the middle
# of town, which is offices and nights out.
WHO_LIVED_THERE = {
    "Alderwick": Lived(0.05, 0.30),
    "Brackenhythe": Lived(0.45, 0.70),
    "Cindermoor": Lived(0.70, 0.90),
    "Dulcimer Green": Lived(0.60, 0.05),
    "Eskerfold": Lived(0.30, 0.95),
    "Farrowmere": Lived(0.90, 0.85),
    "Foxholt": Lived(0.70, 0.75),
    "Gorsebeck": Lived(0.15, 0.85),
    "Grapnel Dock": Lived(0.40, 0.30),
    "Hollinsworth Quay": Lived(1.00, 0.40),
    "Kindlewharf": Lived(0.50, 0.60),
    "Lantern Yard": Lived(0.20, 0.45),
    "Larkspur Hill": Lived(0.10, 0.15),
    "Marrowfen": Lived(0.35, 1.00),
    "Osierholm": Lived(0.30, 0.10),
    "Ostrel Vale": Lived(0.40, 0.80),
    "Otterby Fields": Lived(0.40, 0.80),
    "Pellam Cross": Lived(0.10, 0.30),
    "Sable Reach": Lived(1.00, 0.65),
    "Sedgewater Marsh": Lived(0.10, 0.30),
    "Tallowgate": Lived(0.15, 0.50),
    "Thrushcombe": Lived(0.20, 0.10),
    "Wexmoor": Lived(0.60, 0.50),
    "Wickerford": Lived(0.10, 0.45),
}

# The grid, in kilometres. Cells are smaller near the centre, as a city's are.
COLUMN_WIDTHS_KM = (3.0, 2.2, 1.6, 1.8, 2.4, 3.2)
ROW_HEIGHTS_KM = (2.0, 1.6, 2.2, 3.0)

# The river runs west to east under the second row, then turns south to the
# sea. These four cells are its south bank; every other cell is north or east.
SOUTH_BANK = frozenset({(0, 0), (0, 1), (0, 2), (0, 3)})


@dataclass(frozen=True)
class LinePlan:
    name: str
    # Minutes between services at the morning peak.
    headway: int
    # The stations it calls at, in order.
    stops: tuple[str, ...]


LINES = (
    LinePlan(
        "Amber line",
        4,
        (
            "Brackenhythe",
            "Hollinsworth Quay",
            "Pellam Cross",
            "Tallowgate",
            "Wexmoor",
            "Cindermoor",
        ),
    ),
    LinePlan("Birch line", 6, ("Eskerfold", "Lantern Yard", "Pellam Cross", "Kindlewharf")),
    LinePlan(
        "Cobalt line",
        8,
        ("Pellam Cross", "Coracle Row", "Foxholt", "Dulcimer Green", "Farrowmere"),
    ),
    LinePlan(
        "Dunlin line",
        10,
        ("Wickerford", "Osierholm", "Kindlewharf", "Sable Reach", "Tallowgate", "Coracle Row"),
    ),
)

# A station is named for the area it stands in, and stands a short walk from the
# middle of it. The centre has a second one, so it gets a name of its own and a
# place: this many kilometres east and north of the middle of its area.
SECOND_STATIONS = {"Coracle Row": ("Pellam Cross", (0.45, 0.35))}

STEP_FREE_STATIONS = frozenset(
    {
        "Pellam Cross",
        "Coracle Row",
        "Tallowgate",
        "Kindlewharf",
        "Sable Reach",
        "Wexmoor",
        "Farrowmere",
        "Eskerfold",
    }
)


@dataclass(frozen=True)
class PlacePlan:
    """Something a person can name as the end of a journey. Stations are added from `LINES`."""

    name: str
    kind: PlaceKind
    # The area it stands in, or "" for the one place outside the city.
    area: str
    aliases: tuple[str, ...] = ()
    # The place whose destination it shares, when two names mean one spot.
    shares: str = ""


_DISTRICT = PlaceKind.DISTRICT
_POSTCODE = PlaceKind.POSTCODE_DISTRICT
_LANDMARK = PlaceKind.LANDMARK
_SCHOOL = PlaceKind.SCHOOL

PLACES = (
    PlacePlan(
        "Pellam Exchange", _DISTRICT, "Pellam Cross", ("Quillhaven Exchange",), "Pellam Cross"
    ),
    PlacePlan("Tallowgate Guild Quarter", _DISTRICT, "Tallowgate", ("Guild Quarter",)),
    PlacePlan("Foxholt Market", _DISTRICT, "Foxholt"),
    PlacePlan("Kindlewharf Studios", _DISTRICT, "Kindlewharf"),
    PlacePlan("Cindermoor Works", _DISTRICT, "Cindermoor"),
    PlacePlan("Grapnel Dock", _DISTRICT, "Grapnel Dock", ("Grapnel Docks",)),
    # No British postcode begins with Q, so none of these can be a real one.
    PlacePlan("QH1", _POSTCODE, "Pellam Cross", shares="Pellam Exchange"),
    PlacePlan("QH2", _POSTCODE, "Tallowgate", shares="Tallowgate Guild Quarter"),
    PlacePlan("QH7", _POSTCODE, "Foxholt", shares="Foxholt Market"),
    PlacePlan("Wexmoor University", PlaceKind.UNIVERSITY, "Wexmoor"),
    PlacePlan(
        "Kindlewharf School of Art",
        PlaceKind.UNIVERSITY,
        "Kindlewharf",
        ("Kindlewharf Art School",),
    ),
    PlacePlan("Pellam Infirmary", PlaceKind.HOSPITAL, "Pellam Cross"),
    PlacePlan("Dulcimer Green Hospital", PlaceKind.HOSPITAL, "Dulcimer Green"),
    PlacePlan("Wickerford Cottage Hospital", PlaceKind.HOSPITAL, "Wickerford"),
    PlacePlan("Alderwick Primary School", _SCHOOL, "Alderwick"),
    PlacePlan("Eskerfold Academy", _SCHOOL, "Eskerfold"),
    PlacePlan("Larkspur Hill School", _SCHOOL, "Larkspur Hill"),
    PlacePlan("Osierholm School", _SCHOOL, "Osierholm"),
    PlacePlan("Thrushcombe Primary School", _SCHOOL, "Thrushcombe"),
    PlacePlan("Gorsebeck Depot", _LANDMARK, "Gorsebeck"),
    PlacePlan(
        "Hollinsworth Quay Playhouse", _LANDMARK, "Hollinsworth Quay", ("Quillhaven Playhouse",)
    ),
    PlacePlan("Lantern Yard Market", _LANDMARK, "Lantern Yard"),
    PlacePlan("Marrowfen Retail Park", _LANDMARK, "Marrowfen"),
    PlacePlan("Otterby Fields Stadium", _LANDMARK, "Otterby Fields"),
    PlacePlan("Sable Reach Pier", _LANDMARK, "Sable Reach"),
    PlacePlan("Tallowgate Moot Hall", _LANDMARK, "Tallowgate", ("Quillhaven Moot Hall",)),
    PlacePlan("Thrushcombe Green", _LANDMARK, "Thrushcombe"),
    # Out of town to the north-east. Most of the city cannot reach it within the cutoff.
    PlacePlan("Scrimshaw Airfield", _LANDMARK, ""),
)

# Where the airfield is, in kilometres east and north of the centre.
OUT_OF_TOWN_KM = (17.8, 12.2)
