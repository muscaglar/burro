"""Seeds: which names can be the heart of an area, and the weight of what is known of each.

Section 6 of the areas design gives a table of points, and the rules that turn
points into tiers. They are here once, with every number in `Rules`. Every
number is the design's first guess.

| Evidence | Points | Tonight |
|---|---|---|
| A populated place in OS Open Names | 3 | Read |
| 50 or more road records give it as their settlement | 2 | Read |
| A town centre of district class or above within 800 m | 3 | Read, from a file with no receipt |
| A ward carries it | 1 | Read |
| An area of London in Wikidata, and its article | 2, and 1 | No file: nobody has made the query |
| A name in one MSOA name, or in more | 2, or 3 | The gate refuses the source |

**What the design leaves open, and what is done here.**

- *Within 800 m of what.* Of the centre's outline. The file's own point lies
  outside the outline of some centres. A place that is itself a town centre,
  because the two are one place, has the points however far apart the two
  records lie.
- *Two publishers.* The points of a place come from two publishers when a
  town centre lies near it. Its name rests on two publishers only when both
  write it. The first decides the tier, as the design's table is written. The
  second is kept beside it, and is what a page may say of a name.
- *Its town centre.* The design wrote "its town centre" before anyone knew
  that the file names each centre. It does. So a seed is put on a town centre
  only where the centre is the place's own by its name: the centre that is the
  same place, or one within 800 m whose label writes the place's name or holds
  it. A centre is given to one place, the one its name fits best, and of those
  the nearest. A seed is never moved to a centre of another name: that centre
  is a name of its own, and is weighed as one.
- *Which ward.* Several wards may carry a name: one writes it, and another
  holds it among other words. The point is one whichever gives it. The ward
  that is named as giving it is one that writes the name where one does, and
  of those the nearest, so that it is a ward a person is shown.
- *Too close.* Of two seeds within 600 m along the roads, the one with fewer
  points becomes another name of the other. With as many points each, the one
  that more publishers write stays, then the one more roads name, then the one
  whose record id sorts first. A tie is marked for a person.
- *A wide name.* A populated place of the kind `City` whose box is over 1,750
  hectares is a name for more ground than an area, and is never a seed. 1,750
  hectares is five areas of the size the design expects: London's 157,000
  hectares of land over 450 areas is 350 each, and the design gives a wide
  name to five areas at most. A city in a smaller box is weighed as any other
  place is, and a person says what it is.
- *Landing in range.* The design moves the 6 until 400 to 500 names are
  areas. Where too few places have points from two publishers for that, the
  design left it to the founder whether one publisher is enough. The draft
  then takes the highest number of points that lands in range with one
  publisher allowed, and says so of every area it lets in. The founder has
  since decided that one official publisher is enough for a name it writes for
  a populated place at a point inside the area: `draft_decided.py`. That is
  said of a name once its border is drawn, and changes no number here.
- *What a person decided.* At the review desk a person says of a name put
  forward as an area that it is another name, or no name to keep. The desk
  cannot take the ground from under an area, so the draft is made again. A
  name that was turned down is then no seed, whatever its points. One that
  is not kept is in no list. One that a person made an area stands, and
  never gives way. The rule is chosen before any decision is laid over it:
  the points asked for do not move because a person turned names down.

Nothing here knows a place. A seed is where a file puts it.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum

from burro_pipeline.areas import names_centres, names_places, names_wards
from burro_pipeline.areas.names_candidates import CARRIES, ENDINGS, Match, Place, match
from burro_pipeline.areas.names_centres import Centre
from burro_pipeline.areas.names_shapes import Ground
from burro_pipeline.areas.seeds_roads import Roads
from burro_pipeline.cells.shapes import Point

Key = tuple[str, str, str]


class Tier(StrEnum):
    """What a name is proposed as. The words are the answers of the review desk."""

    AREA = "area"
    SAME_GROUND = "same_ground"
    INSIDE = "inside"
    WIDE = "wide"


class Why(StrEnum):
    """Why a name that is no area is proposed as it is."""

    NONE = ""
    TOO_CLOSE = "too_close"
    FEW_POINTS = "few_points"
    ONE_PUBLISHER = "one_publisher"
    WIDE_KIND = "wide_kind"
    DECIDED = "decided_at_the_desk"


class Put(StrEnum):
    """Where a seed is put."""

    CENTRE = "town_centre"
    PLACE = "place_point"


@dataclass(frozen=True)
class Rules:
    """Every number of the design's rules for seeds. Each is its first guess."""

    place: int = 3
    roads: int = 2
    roads_needed: int = 50
    centre: int = 3
    centre_metres: float = 800.0
    ward: int = 1
    points: int = 6
    publishers: int = 2
    too_close_metres: float = 600.0
    least: int = 400
    most: int = 500
    # How many areas a wide name is given to, at most.
    wide_over: int = 5
    # A city whose box is larger than this, in hectares, is a wide name.
    wide_hectares: float = 1_750.0


@dataclass(frozen=True)
class Weight:
    """The points of one place, and the record behind each."""

    place: int = 0
    roads: int = 0
    centre: int = 0
    ward: int = 0
    # The town centre that gives the points, and how far off its outline is.
    centre_record: str = ""
    centre_metres: float | None = None
    # Whether that centre's class was read as district rank, and is not written as it.
    centre_rank_is_read: bool = False
    ward_record: str = ""
    publishers: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        return self.place + self.roads + self.centre + self.ward


@dataclass(frozen=True)
class Seed:
    """One place, its weight, where its seed is put, and what it is proposed as."""

    place: Place
    weight: Weight
    at: Point
    put: Put
    # The town centre the seed is put on, by its id.
    own_centre: str = ""
    tier: Tier = Tier.INSIDE
    why: Why = Why.NONE
    # The places this name is proposed as a name of, by their keys. One, or for a wide
    # name up to five.
    of: tuple[Key, ...] = ()
    # How far the seed is from the first of them: along the roads, or in a straight line.
    metres: float | None = None
    along_roads: bool = True
    # Whether this place and the one it gave way to had as many points as each other.
    tie: bool = False

    @property
    def key(self) -> Key:
        return self.place.key.key

    @property
    def name(self) -> str:
        return self.place.name

    @property
    def one_publisher(self) -> bool:
        """Whether fewer than two publishers write the name."""
        return len(self.place.publishers) < TWO


@dataclass(frozen=True)
class Tried:
    """One number of points that was tried, and how many areas it gives."""

    points: int
    publishers: int
    areas: int


@dataclass(frozen=True)
class Draft:
    """The seeds of a draft, the rule that was used, and every rule that was tried."""

    seeds: tuple[Seed, ...]
    rules: Rules
    # The points and the publishers the draft asks of an area.
    points: int
    publishers: int
    tried: tuple[Tried, ...] = field(default=())
    # Whether the count of areas landed in the design's range, before any decision.
    in_range: bool = False
    # What the method put each name forward as, of the names a person decided.
    before: Mapping[Key, Tier] = field(default_factory=dict[Key, Tier])

    @property
    def areas(self) -> tuple[Seed, ...]:
        return tuple(seed for seed in self.seeds if seed.tier is Tier.AREA)


def _centres_near(place: Place, ground: Ground, metres: float) -> tuple[tuple[float, str], ...]:
    """The town centres within a length of a place, the nearest first."""
    if place.key.shape is None:
        return ground.within(place.at, metres)
    return ground.near(place.key.shape, metres)


def joined_centre(place: Place) -> str:
    """The town centre that is the same place as a populated place, by its id. Empty if none."""
    found = [
        other.candidate.record_id
        for other in place.others
        if other.candidate.source_id == names_centres.SOURCE and other.match is Match.SAME
    ]
    return found[0] if found else ""


def weigh(place: Place, centres: Mapping[str, Centre], ground: Ground, rules: Rules) -> Weight:
    """The points of a place, as the design's table gives them."""
    publishers: set[str] = set()
    is_place = place.record is not None
    roads = is_place and place.roads >= rules.roads_needed
    carrying = [
        other
        for other in place.others
        if other.candidate.source_id == names_wards.SOURCE and other.match in CARRIES
    ]
    # A ward that writes the name stands before one that only holds it, however near the
    # second lies: a person is shown the first as a record of the name, and not the second.
    ward = min(
        carrying,
        key=lambda each: (RANK[each.match], each.metres, each.candidate.key),
        default=None,
    )
    if is_place:
        publishers.add(place.key.publisher)
    if ward is not None:
        publishers.add(ward.candidate.publisher)
    near = [
        (metres, code)
        for metres, code in _centres_near(place, ground, rules.centre_metres)
        if centres[code].counts
    ]
    own = joined_centre(place)
    if not near and own and centres[own].counts:
        near = [(place.key.metres_from_shape(centres[own].shape), own)]
    if near:
        publishers.add(centres[near[0][1]].publisher)
    return Weight(
        place=rules.place if is_place else 0,
        roads=rules.roads if roads else 0,
        centre=rules.centre if near else 0,
        ward=rules.ward if ward is not None else 0,
        centre_record=near[0][1] if near else "",
        centre_metres=near[0][0] if near else None,
        centre_rank_is_read=bool(near) and centres[near[0][1]].rank_is_read,
        ward_record=ward.candidate.record_id if ward is not None else "",
        publishers=tuple(sorted(publisher for publisher in publishers if publisher)),
    )


# What the file of town centres writes after a name for the kind of thing it lists.
CENTRE_ENDS = ENDINGS[names_centres.SOURCE]
# A name rests on two publishers, or is marked.
TWO = 2


RANK = {Match.SAME: 0, Match.PART: 1, Match.HELD: 2}


def is_wide(place: Place, rules: Rules) -> bool:
    """Whether a place is a name for more ground than an area: a city in a large box."""
    record = place.record
    if record is None or record.kind != names_places.CITY:
        return False
    return record.hectares is not None and record.hectares > rules.wide_hectares


def own_centres(places: Sequence[Place], rules: Rules) -> dict[Key, str]:
    """The town centre each place's seed is put on. A centre is given to one place.

    A centre goes to the populated place whose name it fits best, and of
    those to the nearest. A centre that is the same place is that place's
    however far off it lies. One whose label writes or holds the name must lie
    within 800 m. A name that only a town centre holds stands on that centre
    too, and is not asked about here: where both are put forward as areas they
    lie too close, and the one with fewer points gives way.
    """
    pairs: list[tuple[int, float, Key, str]] = []
    for place in places:
        if place.record is None or is_wide(place, rules):
            continue
        for other in place.written_by(names_centres.SOURCE):
            if other.match not in RANK:
                continue
            if other.match is Match.SAME or other.metres <= rules.centre_metres:
                pairs.append(
                    (RANK[other.match], other.metres, place.key.key, other.candidate.record_id)
                )
    given: dict[Key, str] = {}
    taken: set[str] = set()
    for _, _, key, code in sorted(pairs):
        if key not in given and code not in taken:
            given[key] = code
            taken.add(code)
    return given


# What a person decided of each name, by its key: what it is, or None where it is no name
# to keep.
Decided = Mapping[Key, Tier | None]


def _order(seed: Seed) -> tuple[int, int, int, Key]:
    """The order in which seeds are kept: the most points first."""
    return (-seed.weight.total, -len(seed.place.publishers), -seed.place.roads, seed.key)


def _as_strong(a: Seed, b: Seed) -> bool:
    return a.weight.total == b.weight.total


def _same_ground(seed: Seed, kept: Seed) -> bool:
    """Whether a name that gave way is another name of the same ground, and not a place in it.

    It is, when it is known by a town centre and that centre is the one the
    other's seed stands on, or its label holds the other's name.
    """
    if seed.place.centre is None:
        return False
    how = match(kept.name, seed.name, CENTRE_ENDS)
    return kept.own_centre == seed.place.key.record_id or how in CARRIES


def _straight(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def thin(seeds: Sequence[Seed], roads: Roads, rules: Rules) -> list[Seed]:
    """Of the seeds put forward as areas, those that stay, and those that give way.

    The seeds are taken in order, the most points first. A seed within 600 m
    along the roads of one that stayed gives way to the nearest such. A seed
    that a person made an area stays, however near another it stands, and none
    gives way to it: what a person said of one name says nothing of the next.
    """
    kept: dict[Key, Seed] = {}
    found: list[Seed] = [seed for seed in seeds if seed.why is Why.DECIDED]
    for seed in sorted((seed for seed in seeds if seed.why is not Why.DECIDED), key=_order):
        near = {
            str(index): other.at
            for index, other in enumerate(kept.values())
            if _straight(seed.at, other.at) <= rules.too_close_metres
        }
        reached = roads.within(seed.at, near, rules.too_close_metres) if near else {}
        if not reached:
            kept[seed.key] = seed
            found.append(seed)
            continue
        others = list(kept.values())
        metres, index = min((metres, int(index)) for index, metres in reached.items())
        other = others[index]
        found.append(
            replace(
                seed,
                tier=Tier.SAME_GROUND if _same_ground(seed, other) else Tier.INSIDE,
                why=Why.TOO_CLOSE,
                of=(other.key,),
                metres=metres,
                tie=_as_strong(seed, other),
            )
        )
    return found


def _sift(
    seeds: Sequence[Seed],
    roads: Roads,
    rules: Rules,
    points: int,
    publishers: int,
    decided: Decided | None = None,
) -> tuple[list[Seed], list[Seed]]:
    """The seeds put forward as areas, thinned, and the rest, for one rule."""
    put_forward: list[Seed] = []
    rest: list[Seed] = []
    for seed in seeds:
        said = (decided or {}).get(seed.key)
        if said is Tier.AREA:
            put_forward.append(replace(seed, tier=Tier.AREA, why=Why.DECIDED))
        elif said is not None:
            rest.append(replace(seed, tier=said, why=Why.DECIDED))
        elif is_wide(seed.place, rules):
            rest.append(replace(seed, tier=Tier.WIDE, why=Why.WIDE_KIND))
        elif seed.weight.total < points:
            rest.append(replace(seed, tier=Tier.INSIDE, why=Why.FEW_POINTS))
        elif len(seed.weight.publishers) < publishers:
            rest.append(replace(seed, tier=Tier.INSIDE, why=Why.ONE_PUBLISHER))
        else:
            put_forward.append(replace(seed, tier=Tier.AREA, why=Why.NONE))
    return thin(put_forward, roads, rules), rest


def _count(seeds: Sequence[Seed], roads: Roads, rules: Rules, points: int, publishers: int) -> int:
    """How many areas one rule gives."""
    return sum(seed.tier is Tier.AREA for seed in _sift(seeds, roads, rules, points, publishers)[0])


def _propose(
    seeds: Sequence[Seed],
    roads: Roads,
    rules: Rules,
    points: int,
    publishers: int,
    decided: Decided | None = None,
) -> list[Seed]:
    """Every seed with its tier, for one number of points and of publishers."""
    thinned, rest = _sift(seeds, roads, rules, points, publishers, decided)
    areas = {seed.key: seed.at for seed in thinned if seed.tier is Tier.AREA}
    named = {"|".join(key): at for key, at in areas.items()}
    back = {"|".join(key): key for key in areas}
    waiting = {"|".join(seed.key): seed.at for seed in rest}
    along = roads.nearest_of(named, waiting) if named else {}
    found = list(thinned)
    for seed in rest:
        if seed.tier is Tier.WIDE:
            nearest = sorted((_straight(seed.at, at), key) for key, at in areas.items())
            over = nearest[: rules.wide_over]
            found.append(
                replace(
                    seed,
                    of=tuple(key for _, key in over),
                    metres=over[0][0] if over else None,
                    along_roads=False,
                )
            )
            continue
        reached = along.get("|".join(seed.key))
        if reached is not None:
            found.append(replace(seed, of=(back[reached[0]],), metres=reached[1]))
            continue
        nearest = sorted((_straight(seed.at, at), key) for key, at in areas.items())
        found.append(
            replace(
                seed,
                of=tuple(key for _, key in nearest[:1]),
                metres=nearest[0][0] if nearest else None,
                along_roads=False,
            )
        )
    return sorted(found, key=lambda seed: seed.key)


def _weighed(places: Sequence[Place], centres: Sequence[Centre], rules: Rules) -> list[Seed]:
    """Every place with its points and where its seed is put, before any is put forward."""
    by_id = {centre.record_id: centre for centre in centres}
    ground = Ground({centre.record_id: centre.shape for centre in centres})
    own = own_centres(places, rules)
    seeds: list[Seed] = []
    for place in sorted(places, key=lambda each: each.key.key):
        centre = place.centre or (by_id[own[place.key.key]] if place.key.key in own else None)
        seeds.append(
            Seed(
                place=place,
                weight=weigh(place, by_id, ground, rules),
                at=centre.at if centre is not None else place.at,
                put=Put.CENTRE if centre is not None else Put.PLACE,
                own_centre=centre.record_id if centre is not None else "",
            )
        )
    return seeds


def draft(
    places: Sequence[Place],
    centres: Sequence[Centre],
    roads: Roads,
    rules: Rules | None = None,
    *,
    points: int | None = None,
    publishers: int | None = None,
    decided: Decided | None = None,
) -> Draft:
    """The seeds of a draft. With `points` and `publishers` given, no other rule is tried.

    `decided` is what a person said of a name at the review desk. It is laid
    over the rule once the rule is chosen, and never moves the rule.
    """
    rules = rules or Rules()
    decided = dict(decided or {})
    unknown = set(decided) - {place.key.key for place in places}
    if unknown:
        raise ValueError("a decision is about a place the draft does not hold")
    seeds = _weighed(places, centres, rules)
    if points is not None and publishers is not None:
        count = _count(seeds, roads, rules, points, publishers)
        tried = [Tried(points, publishers, count)]
        chosen = tried[0]
    else:
        highest = max((seed.weight.total for seed in seeds), default=rules.points)
        tried = [
            Tried(number, needs, _count(seeds, roads, rules, number, needs))
            for needs in (rules.publishers, 1)
            for number in range(highest, 0, -1)
        ]
        chosen = _choose(tried, rules)
    before: dict[Key, Tier] = {}
    if decided:
        by_method = _propose(seeds, roads, rules, chosen.points, chosen.publishers)
        before = {seed.key: seed.tier for seed in by_method if seed.key in decided}
    # A name that is not kept stands on no town centre, so the centre is free for another.
    not_kept = {key for key, said in decided.items() if said is None}
    if not_kept:
        seeds = _weighed([each for each in places if each.key.key not in not_kept], centres, rules)
    return Draft(
        tuple(_propose(seeds, roads, rules, chosen.points, chosen.publishers, decided)),
        rules,
        chosen.points,
        chosen.publishers,
        tuple(tried),
        rules.least <= chosen.areas <= rules.most,
        before,
    )


def _choose(tried: Sequence[Tried], rules: Rules) -> Tried:
    """The rule a draft is made by, of those that were tried.

    The design's own rule, if it lands in range. Else the number of points
    nearest the design's that does, with two publishers before one. Else the
    rule that comes nearest the range.
    """

    def lands(each: Tried) -> bool:
        return rules.least <= each.areas <= rules.most

    def far(each: Tried) -> tuple[int, int, int]:
        return (-each.publishers, abs(each.points - rules.points), -each.points)

    landed = [each for each in tried if lands(each)]
    if landed:
        return min(landed, key=far)

    def short(each: Tried) -> tuple[int, int, int, int]:
        by = rules.least - each.areas if each.areas < rules.least else each.areas - rules.most
        return (by, *far(each))

    return min(tried, key=short)
