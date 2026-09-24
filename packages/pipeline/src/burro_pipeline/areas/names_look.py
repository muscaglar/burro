"""The names a person must look at hardest, each marked with why.

A person reads every name before it ships. A mark says which to read with
most care, and gives the reason in words. A mark is never a verdict: it
changes no name, no tier and no seed.

| Mark | A name is marked when |
|---|---|
| `may_describe_residents` | It holds a word for a group of people |
| `same_name_elsewhere` | Another place of the draft has the same name |
| `two_names_one_place` | A record gives it a second name. A label of several names holds it. |
| | Or it gave way to a seed close by |
| `joined_beyond_1km` | Two records were taken for one place, over 1 km apart |
| `may_be_a_built_thing` | It holds a word for an estate, a business, a building or a road. |
| | Or its box is the smallest the file draws |
| `also_a_borough` | A borough has the same name |
| `also_a_station` | A railway station has the same name |
| `also_a_ward` | A ward has the same name |
| `as_many_points` | It and a seed too close to it have as many points as each other |
| `seed_far_from_place` | Its seed stands on its town centre, over 800 m from its own point |
| | A town centre is taken to stand at a point inside its outline |
| `seed_on_a_label_that_holds_it` | Its seed was moved to a town centre whose label holds |
| | its name among other words, and is not its name |
| `class_was_read` | Its points rest on a town centre whose class was read as district |
| `no_receipt` | It rests on a file that has no receipt |
| `one_publisher` | Fewer than two publishers write it. Whether that is a doubt is said |
| | once the borders are drawn: one official publisher is enough where it writes the |
| | name for a populated place at a point inside the area |

**One distance for one thing.** Three lengths lie between a place and a town
centre, and each is said with what it is from and what it is to. From the
place's point to the centre's outline, which is what gives the centre's points.
From the place's point to where the centre is taken to stand, which is how far
a seed was moved. And from a record to the edge of an area, which the lines of
the desk say. The first two are said in whole metres, so that one length is
never written in two ways.

A mark that a name shares with most names says little. So each row of a draft
says whether its mark is grave: one that few names carry and that a person
should settle before the name ships. A station or a ward of the same name that
stands where the place does is no grave mark: it is what one would expect.

**The two lists of words are no test.** They see whole words only, and know
nothing of any place. A name with none of the words may still describe who
lives somewhere, and a name with one may not. The design keeps a name that
describes residents only where a publisher writes it as the name of the place,
and puts each to the founder. Nothing here coins a name or drops one.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from burro_pipeline.areas import names_centres, names_wards
from burro_pipeline.areas.names_candidates import (
    ENDINGS,
    SAME_PLACE_METRES,
    WORD,
    Candidate,
    Match,
    core,
    fold,
    parts,
)
from burro_pipeline.areas.names_files import File
from burro_pipeline.areas.seeds import Put, Rules, Seed, Why


class Mark(StrEnum):
    """Why a name is to be looked at. They are listed the gravest first."""

    MAY_DESCRIBE_RESIDENTS = "may_describe_residents"
    SAME_NAME_ELSEWHERE = "same_name_elsewhere"
    TWO_NAMES_ONE_PLACE = "two_names_one_place"
    JOINED_BEYOND_1KM = "joined_beyond_1km"
    MAY_BE_A_BUILT_THING = "may_be_a_built_thing"
    ALSO_A_BOROUGH = "also_a_borough"
    ALSO_A_STATION = "also_a_station"
    ALSO_A_WARD = "also_a_ward"
    AS_MANY_POINTS = "as_many_points"
    SEED_FAR_FROM_PLACE = "seed_far_from_place"
    SEED_ON_A_LABEL_THAT_HOLDS_IT = "seed_on_a_label_that_holds_it"
    CLASS_WAS_READ = "class_was_read"
    NO_RECEIPT = "no_receipt"
    ONE_PUBLISHER = "one_publisher"


ORDER = {mark: index for index, mark in enumerate(Mark)}
# The marks that are grave wherever they stand. A station or a ward of the same name is
# grave only where it lies elsewhere, which `Look.grave` says.
GRAVE = frozenset(
    {
        Mark.MAY_DESCRIBE_RESIDENTS,
        Mark.SAME_NAME_ELSEWHERE,
        Mark.TWO_NAMES_ONE_PLACE,
        Mark.JOINED_BEYOND_1KM,
        Mark.MAY_BE_A_BUILT_THING,
        Mark.ALSO_A_BOROUGH,
        Mark.AS_MANY_POINTS,
    }
)

# Words for a group of people: by faith, by country or people, and by means. Words for a
# rank or a calling are left out: a name that holds the word for a king says nothing of
# who lives there.
PEOPLE = frozenset(
    """
    jew jews jewish jewry christian christians muslim muslims hindu hindus sikh sikhs
    buddhist buddhists catholic catholics protestant protestants quaker quakers huguenot
    huguenots
    english irish scots scottish welsh british french german germans dutch flemish italian
    italians spanish portuguese polish greek greeks turkish turks arab arabs african africans
    caribbean jamaican indian indians bengali bangla bangladeshi pakistani chinese korean
    japanese vietnamese somali nigerian ghanaian cypriot russian american
    black white asian gypsy gypsies traveller travellers romany roma
    gay lesbian queer
    poor paupers beggars rich gentlemen workers workmen labourers students
    """.split()  # noqa: SIM905  one word to a line would run to ninety lines
)
ESTATE, BUSINESS, BUILDING, ROAD = (
    "an estate or a development",
    "a business",
    "a building",
    "a road",
)
# Words for a thing that is built or run, and what kind of thing each is.
BUILT: Mapping[str, str] = {
    "estate": ESTATE,
    "quarter": ESTATE,
    "yard": ESTATE,
    "square": ESTATE,
    "terrace": ESTATE,
    "mews": ESTATE,
    "court": ESTATE,
    "place": ESTATE,
    "close": ESTATE,
    "walk": ESTATE,
    "row": ESTATE,
    "village": ESTATE,
    "wharf": ESTATE,
    "quay": ESTATE,
    "dock": ESTATE,
    "docks": ESTATE,
    "basin": ESTATE,
    "works": BUSINESS,
    "market": BUSINESS,
    "exchange": BUSINESS,
    "retail": BUSINESS,
    "shopping": BUSINESS,
    "industrial": BUSINESS,
    "business": BUSINESS,
    "trading": BUSINESS,
    "studios": BUSINESS,
    "arms": BUSINESS,
    "inn": BUSINESS,
    "tavern": BUSINESS,
    "hotel": BUSINESS,
    "house": BUILDING,
    "hall": BUILDING,
    "tower": BUILDING,
    "towers": BUILDING,
    "palace": BUILDING,
    "castle": BUILDING,
    "hospital": BUILDING,
    "college": BUILDING,
    "university": BUILDING,
    "campus": BUILDING,
    "barracks": BUILDING,
    "prison": BUILDING,
    "station": BUILDING,
    "arsenal": BUILDING,
    "stadium": BUILDING,
    "arena": BUILDING,
    "mill": BUILDING,
    "mills": BUILDING,
    "farm": BUILDING,
    "airport": BUILDING,
    "centre": BUILDING,
    "road": ROAD,
    "street": ROAD,
    "lane": ROAD,
    "avenue": ROAD,
    "way": ROAD,
    "broadway": ROAD,
    "parade": ROAD,
}
# The side of the smallest box that OS Open Names draws round a populated place, in metres.
SMALLEST_BOX = 500.0


@dataclass(frozen=True)
class Look:
    """One reason to look hard at one name."""

    # The place, by the record it is known by.
    key: tuple[str, str, str]
    name: str
    mark: Mark
    # Why, in words. Every name in them is a name a file holds.
    why: str
    # The other record the reason rests on, where there is one.
    source_id: str = ""
    record_id: str = ""
    # Whether the other record lies elsewhere: over 1 km from the place.
    elsewhere: bool = False

    @property
    def grave(self) -> bool:
        """Whether this is a mark to settle before the name ships."""
        return self.mark in GRAVE or self.elsewhere


def _km(metres: float) -> str:
    return f"{metres / 1000:.1f} km"


def _m(metres: float) -> str:
    return f"{round(metres):,} m"


def _words(name: str) -> list[str]:
    return WORD.findall(name.casefold().replace("'", ""))


NAME, POINTS, SEED = "name", "points", "seed"


def what_rests_on(seed: Seed) -> dict[str, tuple[str, ...]]:
    """For each source, which of a name, its points and its seed rest on it, in that order.

    The name rests on every source whose record writes it. The points rest on the
    source of each record that gave one. The seed rests on the file of town centres
    where it stands on a town centre, and on the place's own record where it does not.
    """
    place, weight = seed.place, seed.weight
    of_the_name = {place.key.source_id}
    of_the_name |= {other.candidate.source_id for other in place.others if other.writes}
    of_the_points = {
        *([place.key.source_id] if weight.place or weight.roads else []),
        *([names_centres.SOURCE] if weight.centre else []),
        *([names_wards.SOURCE] if weight.ward else []),
    }
    of_the_seed = {names_centres.SOURCE if seed.put is Put.CENTRE else place.key.source_id}
    held = ((NAME, of_the_name), (POINTS, of_the_points), (SEED, of_the_seed))
    return {
        source: tuple(what for what, sources in held if source in sources)
        for source in sorted(of_the_name | of_the_points | of_the_seed)
    }


def rests_on(seed: Seed) -> tuple[str, ...]:
    """The sources a name, its points and its seed rest on."""
    return tuple(what_rests_on(seed))


def _rest_on(what: Sequence[str], source: str) -> str:
    """That a name, its points or its seed rest on a file with no receipt: which of them."""
    named = [f"its {each}" for each in what]
    listed = " and ".join([", ".join(named[:-1]), named[-1]] if len(named) > 1 else named)
    # Points are several whether or not anything else rests there with them.
    rest = "rests" if len(named) == 1 and what[0] != POINTS else "rest"
    return f"I{listed[1:]} {rest} on {source}, a file that has no receipt."


def _of_the_name(seed: Seed, files: Mapping[str, File]) -> list[Look]:
    """The marks that rest on the name and the place's own record."""
    found: list[Look] = []

    def look(mark: Mark, why: str, other: Candidate | None = None) -> None:
        found.append(
            Look(
                seed.key,
                seed.name,
                mark,
                why,
                other.source_id if other else "",
                other.record_id if other else "",
            )
        )

    for word in _words(seed.name):
        if word in PEOPLE:
            look(
                Mark.MAY_DESCRIBE_RESIDENTS,
                f'It holds the word "{word}", which is a word for a group of people. '
                f"{seed.place.key.publisher} writes it as the name of the place.",
            )
        if word in BUILT:
            look(Mark.MAY_BE_A_BUILT_THING, f'It holds the word "{word}", as {BUILT[word]} may.')
    record = seed.place.record
    if record is not None and record.box is not None:
        wide, high = record.box[2] - record.box[0], record.box[3] - record.box[1]
        if max(wide, high) <= SMALLEST_BOX:
            look(
                Mark.MAY_BE_A_BUILT_THING,
                f"Its box is {_m(wide)} by {_m(high)}, the smallest the file draws round a place.",
            )
    if record is not None and record.second_name:
        look(
            Mark.TWO_NAMES_ONE_PLACE,
            f'The same record gives it a second name, "{record.second_name}".',
            seed.place.key,
        )
    for other in seed.place.others:
        label = other.candidate.as_written
        if other.candidate.source_id == names_centres.SOURCE:
            if other.match is Match.SAME and other.beyond:
                look(
                    Mark.JOINED_BEYOND_1KM,
                    f'The town centre "{label}" is taken for the same place. Its outline is '
                    f"{_m(other.metres)} from the place's point, inside the box that is drawn "
                    "round the place.",
                    other.candidate,
                )
            if other.match is Match.PART:
                look(
                    Mark.TWO_NAMES_ONE_PLACE,
                    f'The town centre "{label}" names it beside another name.',
                    other.candidate,
                )
        if other.candidate.source_id == names_wards.SOURCE and other.match is Match.SAME:
            look(
                Mark.ALSO_A_WARD,
                f'The ward "{label}" has the same name, {_m(other.metres)} from the place.'
                if other.metres
                else f'The ward "{label}" has the same name, and holds the place.',
                other.candidate,
            )
    if seed.one_publisher:
        look(
            Mark.ONE_PUBLISHER,
            f"Only {seed.place.key.publisher} writes it. One official publisher is enough "
            "where it writes the name for a populated place at a point inside the area, "
            "which is said once the borders are drawn.",
        )
    for source, what in what_rests_on(seed).items():
        if not files[source].has_receipt:
            look(Mark.NO_RECEIPT, _rest_on(what, source))
    return found


def _of_the_seed(seed: Seed, by_key: Mapping[tuple[str, str, str], Seed]) -> list[Look]:
    """The marks that rest on where the seed stands, and on what it gave way to."""
    found: list[Look] = []
    if seed.weight.centre_rank_is_read:
        found.append(
            Look(
                seed.key,
                seed.name,
                Mark.CLASS_WAS_READ,
                f"Points were given for the town centre {seed.weight.centre_record}, whose class "
                "is written with another word beside the word for district.",
                names_centres.SOURCE,
                seed.weight.centre_record,
            )
        )
    if seed.put is Put.CENTRE and seed.place.record is not None:
        moved = ((seed.at[0] - seed.place.at[0]) ** 2 + (seed.at[1] - seed.place.at[1]) ** 2) ** 0.5
        own = [
            other
            for other in seed.place.others
            if other.candidate.source_id == names_centres.SOURCE
            and other.candidate.record_id == seed.own_centre
        ]
        if own and all(other.match is Match.HELD for other in own):
            found.append(
                Look(
                    seed.key,
                    seed.name,
                    Mark.SEED_ON_A_LABEL_THAT_HOLDS_IT,
                    f"Its seed was moved {_m(moved)} from the place's point, to where the "
                    f'town centre "{own[0].candidate.as_written}" is taken to stand. That '
                    "label holds the name among other words, and is not the name.",
                    names_centres.SOURCE,
                    seed.own_centre,
                )
            )
        if moved > Rules().centre_metres:
            found.append(
                Look(
                    seed.key,
                    seed.name,
                    Mark.SEED_FAR_FROM_PLACE,
                    f"Its seed stands where its town centre is taken to stand, {_m(moved)} "
                    f"from the point that {seed.place.key.publisher} gives the place.",
                    names_centres.SOURCE,
                    seed.own_centre,
                )
            )
    if seed.why is Why.TOO_CLOSE and seed.of:
        other = by_key[seed.of[0]]
        found.append(
            Look(
                seed.key,
                seed.name,
                Mark.TWO_NAMES_ONE_PLACE,
                f"Its seed is {_m(seed.metres or 0)} along the roads from the seed of "
                f'"{other.name}", which has {other.weight.total} points to its '
                f"{seed.weight.total}. So it is put forward as another name of that area.",
                other.place.key.source_id,
                other.place.key.record_id,
            )
        )
        if seed.tie:
            for one, two in ((seed, other), (other, seed)):
                found.append(
                    Look(
                        one.key,
                        one.name,
                        Mark.AS_MANY_POINTS,
                        f'It and "{two.name}" lie too close to both be areas, and have as many '
                        f"points as each other. "
                        f'"{other.name}" was kept: more publishers write it, or more roads '
                        "name it, or its record id sorts first.",
                        two.place.key.source_id,
                        two.place.key.record_id,
                    )
                )
    return found


def _also(
    seeds: Sequence[Seed],
    others: Sequence[Candidate],
    mark: Mark,
    kind: str,
    endings: Sequence[str],
) -> list[Look]:
    """A mark for every name that is also the name of a record of another kind."""
    named: dict[str, list[Candidate]] = {}
    for other in others:
        named.setdefault(fold(core(other.as_written, endings)), []).append(other)
    found: list[Look] = []
    for seed in seeds:
        same = named.get(fold(seed.name), [])
        if not same:
            continue
        nearest = min(same, key=lambda other: (seed.place.key.metres_from(other), other.key))
        metres = seed.place.key.metres_from(nearest)
        if metres == 0:
            where = "It holds the place, or stands where the place does"
        elif metres <= SAME_PLACE_METRES:
            where = f"It is {_m(metres)} from the place"
        else:
            where = f"It is {_km(metres)} away, so it may be named for another place"
        found.append(
            Look(
                seed.key,
                seed.name,
                mark,
                f'The {kind} "{nearest.as_written}" has the same name. {where}.',
                nearest.source_id,
                nearest.record_id,
                elsewhere=metres > SAME_PLACE_METRES,
            )
        )
    return found


def _elsewhere(seeds: Sequence[Seed], borough_names: Mapping[str, str]) -> list[Look]:
    """A mark for every name that more than one place of the draft has."""
    named: dict[str, list[Seed]] = {}
    for seed in seeds:
        label = core(seed.name, ENDINGS.get(seed.place.key.source_id, ()))
        named.setdefault(fold(label), []).append(seed)
    found: list[Look] = []
    for same in named.values():
        for seed in same if len(same) > 1 else ():
            for other in same:
                if other.key == seed.key:
                    continue
                metres = seed.place.key.metres_from(other.place.key)
                borough = borough_names.get(other.place.key.borough, other.place.key.borough)
                beside = (
                    "the same borough"
                    if other.place.key.borough == seed.place.key.borough
                    else borough
                )
                found.append(
                    Look(
                        seed.key,
                        seed.name,
                        Mark.SAME_NAME_ELSEWHERE,
                        f'{other.place.key.publisher} writes "{other.name}" for a place '
                        f"{_km(metres)} away, in {beside}.",
                        other.place.key.source_id,
                        other.place.key.record_id,
                    )
                )
    return found


def _of_several(seeds: Sequence[Seed]) -> list[Look]:
    """A mark for a town centre whose own label is several names."""
    return [
        Look(
            seed.key,
            seed.name,
            Mark.TWO_NAMES_ONE_PLACE,
            "Its label is several names in one: "
            + ", ".join(f'"{part}"' for part in parts(seed.name))
            + ", each in lower case here and as written in the label.",
        )
        for seed in seeds
        if seed.place.centre is not None and parts(seed.name)
    ]


def marks(
    seeds: Sequence[Seed],
    stations: Sequence[Candidate],
    wards: Sequence[Candidate],
    boroughs: Sequence[Candidate],
    borough_names: Mapping[str, str],
    files: Mapping[str, File],
) -> tuple[Look, ...]:
    """Every reason to look hard at a name, the gravest first, and then by name.

    `wards` and `boroughs` are those of Boundary-Line. `borough_names` is the
    name of each borough as the statistics office's lookup writes it, by its
    code. `files` is every file that was read, by its source.
    """
    by_key = {seed.key: seed for seed in seeds}
    found: list[Look] = []
    for seed in seeds:
        found += _of_the_name(seed, files) + _of_the_seed(seed, by_key)
    found += _elsewhere(seeds, borough_names) + _of_several(seeds)
    found += _also(seeds, stations, Mark.ALSO_A_STATION, "railway station", ())
    of_line = ENDINGS[names_wards.SOURCE]
    found += _also(seeds, boroughs, Mark.ALSO_A_BOROUGH, "borough", of_line)
    lookup = {fold(name): name for name in borough_names.values()}
    already = {look.key for look in found if look.mark is Mark.ALSO_A_BOROUGH}
    for seed in seeds:
        if seed.key not in already and fold(seed.name) in lookup:
            found.append(
                Look(
                    seed.key,
                    seed.name,
                    Mark.ALSO_A_BOROUGH,
                    f'The borough "{lookup[fold(seed.name)]}" has the same name.',
                )
            )
    # A ward of the same name near the place is marked with the place. One further off is
    # looked for here, among every ward.
    near = {look.key for look in found if look.mark is Mark.ALSO_A_WARD}
    far = [seed for seed in seeds if seed.key not in near]
    found += _also(far, wards, Mark.ALSO_A_WARD, "ward", of_line)
    unique = {(look.key, look.mark, look.why): look for look in found}
    return tuple(
        sorted(unique.values(), key=lambda look: (ORDER[look.mark], fold(look.name), look.key))
    )
