"""The synthetic release: unmistakably made up, the same every time, and a plausible small city."""

import ast
import math
import re
from collections.abc import Callable, Iterator
from functools import cache
from pathlib import Path
from typing import cast

import pytest
from burro_core import default_spec, facts_for, rank, resolve_area, resolve_place, verify
from burro_core.explain import render
from burro_core.ids import (
    FeatureId,
    Mode,
    Provenance,
    PtBasis,
    Segment,
    Strictness,
    Tenure,
    TravelStatus,
)
from burro_core.release import (
    NEARBY_STATION_MINUTES,
    SYNTHETIC_ATTRIBUTION,
    AreaGeometry,
    InMemoryRelease,
    Neighbourhood,
)
from burro_core.spec import Commute
from burro_pipeline.release import build_synthetic, read_release, write_release
from burro_pipeline.release.read import IGNORED
from burro_pipeline.release.synthetic import (
    BUILT_AT,
    RELEASE_ID,
    SEED,
    build,
    chart,
    journeys,
    names,
)
from burro_pipeline.release.write import packed

FIXTURE = Path(__file__).parents[3] / "data" / "fixtures" / "synthetic" / RELEASE_ID
ONE_MEGABYTE = 1_000_000

# Real names, held here so that none can slip into the made-up city. The 32
# boroughs and the City, the tube and rail lines, and well-known places.
REAL_NAMES = """
barking dagenham barnet bexley brent bromley camden croydon ealing enfield greenwich hackney
hammersmith fulham haringey harrow havering hillingdon hounslow islington kensington chelsea
kingston lambeth lewisham merton newham redbridge richmond southwark sutton tower hamlets
waltham wandsworth westminster london
bakerloo central circle district jubilee metropolitan northern piccadilly victoria waterloo
elizabeth docklands overground lioness mildmay windrush weaver suffragette liberty thameslink
tramlink crossrail
soho mayfair covent shoreditch brixton notting canary wimbledon hampstead clapham peckham dalston
stratford paddington marylebone bloomsbury holborn whitechapel bermondsey battersea putney
chiswick tottenham walthamstow highgate finsbury pancras euston blackfriars farringdon
clerkenwell barbican knightsbridge pimlico vauxhall deptford woolwich bethnal hoxton angel bank
bow kew oval temple strand aldgate moorgate wapping limehouse poplar stepney tooting balham
streatham dulwich wembley twickenham heathrow thames charing leicester trafalgar guildhall
""".split()  # noqa: SIM905  one name to a line would run to a hundred and twenty lines
# Real places the made-up city once held and the list above did not catch. Three a
# reviewer knew for what they are: a hamlet in Cornwall, a small street by a bridge in
# London, and a loch in Galloway. Two more were found when every name was looked up in an
# encyclopaedia: a locality in Renfrewshire and an old spelling of a Shropshire hamlet.
# All were replaced on 2026-09-23 and are held here so that none comes back. The names
# were looked up in one encyclopaedia and in no gazetteer: a small street, a farm or a
# hamlet that it does not cover would not have been found.
ONCE_USED = ("dunmere", "copper row", "skerrow", "kilnside", "withyford")
# What real buildings are called, and what a place here once had as a name of its own.
# Inside a longer made-up name each is a word for a kind of building, and is allowed.
ONCE_A_NAME_OF_ITS_OWN = ("moot hall", "the exchange", "the playhouse")
# Real places that the releases the tests build by hand once held.
ONCE_IN_A_TEST = (
    *("tarnside", "orrin", "orrins", "marl", "marlow", "the moor", "far ings"),
    *("kings reach", "king's reach", "king\N{RIGHT SINGLE QUOTATION MARK}s reach"),
    "hundred acres",
)
# The letters a postcode in or around London begins with, and the form one takes.
REAL_POSTCODE = re.compile(
    r"^(e|ec|n|nw|se|sw|w|wc|br|cr|da|en|ha|ig|kt|rm|sm|tw|ub|wd)\d{1,2}[a-z]?$"
)
# No British postcode begins with any of these.
NEVER_A_POSTCODE = ("q", "v", "x")

# The box the contract puts every synthetic coordinate in: open sea.
LONGITUDES, LATITUDES = (-0.20, 0.20), (-0.15, 0.15)


@cache
def fixture() -> InMemoryRelease:
    return read_release(FIXTURE)


def area(name: str) -> Neighbourhood:
    return next(n for n in fixture().neighbourhoods if n.name == name)


def value(name: str, feature_id: FeatureId) -> float | None:
    row = fixture().feature(area(name).area_id, feature_id)
    assert row is not None
    return row.value


def ring(drawn: AreaGeometry) -> list[tuple[float, float]]:
    """The outline of an area. Every synthetic area is one polygon with no hole."""
    assert drawn.geometry.type.value == "Polygon"
    return list(cast(tuple[tuple[tuple[float, float], ...], ...], drawn.geometry.coordinates)[0])


def destination(place: str) -> str:
    return next(p.destination_id for p in fixture().places if p.name == place)


def names_in(release: InMemoryRelease) -> Iterator[str]:
    """Every name the release could ever show."""
    for n in release.neighbourhoods:
        yield from (n.name, n.borough, n.slug.replace("-", " "), *n.aliases)
    for place in release.places:
        yield from (place.name, *place.aliases)
    for row in release.station_rows:
        yield from (row.name, *row.lines)


def test_synthetic_release_rebuilds_byte_for_byte(tmp_path: Path):
    write_release(build_synthetic(SEED, RELEASE_ID, BUILT_AT), tmp_path)
    rebuilt = {file.name: file.read_bytes() for file in (tmp_path / RELEASE_ID).iterdir()}
    # What is committed is the release. What a file browser left beside it is not.
    kept = [file for file in FIXTURE.iterdir() if file.name != IGNORED]
    committed = {file.name: file.read_bytes() for file in kept}
    assert sorted(committed) == sorted(rebuilt)
    stale = sorted(name for name in rebuilt if rebuilt[name] != committed[name])
    assert not stale, "the committed fixture is not what the generator makes: run `make fixture`"


def test_the_seed_decides_every_figure_and_no_name():
    once, again, other = build_synthetic(7), build_synthetic(7), build_synthetic(8)
    assert packed(once) == packed(again)
    assert packed(once)["features.json"] != packed(other)["features.json"]
    assert packed(once)["geometry.json"] != packed(other)["geometry.json"]
    assert set(names_in(once)) == set(names_in(other))
    assert [n.area_id for n in once.neighbourhoods] == [n.area_id for n in other.neighbourhoods]
    assert once.manifest.seed == 7


def test_the_committed_fixture_is_under_a_megabyte():
    assert sum(file.stat().st_size for file in FIXTURE.iterdir()) < ONE_MEGABYTE


def test_the_city_is_the_size_the_tests_and_demos_count_on():
    release = fixture()
    assert len(release.neighbourhoods) == 24
    # An id is never reused or renamed, so the areas are numbered in an order that is fixed.
    assert [n.name for n in release.neighbourhoods] == sorted(
        n.name for n in release.neighbourhoods
    )
    assert {n.borough for n in release.neighbourhoods} == {"Quillhaven"}
    assert len(release.destinations) == 40
    assert [n.name for n in release.neighbourhoods if not n.rankable] == [
        "Grapnel Dock",
        "Sedgewater Marsh",
    ]
    assert len({(row.station_id, row.name) for row in release.station_rows}) == 16
    assert len({line for row in release.station_rows for line in row.lines}) == 4


def test_synthetic_names_are_not_real_places():
    for name in names_in(fixture()):
        folded = name.casefold()
        for real in (*REAL_NAMES, *ONCE_USED, *ONCE_IN_A_TEST):
            # A short real name is looked for as a word: "bow" is in "elbow".
            held = real in folded if len(real) > 4 else real in re.findall(r"[a-z]+", folded)
            assert not held, f"{name!r} holds the real name {real!r}"
        assert folded not in ONCE_A_NAME_OF_ITS_OWN, name


def test_a_name_that_was_replaced_is_in_no_name_the_generator_holds():
    # The plan itself, and not only what reaches the release from it.
    planned = [plan.name for plan in names.AREAS] + [names.BOROUGH, names.CENTRE]
    planned += [alias for plan in names.AREAS for alias in plan.aliases]
    planned += [line.name for line in names.LINES] + [s for line in names.LINES for s in line.stops]
    planned += [*names.SECOND_STATIONS, *names.STEP_FREE_STATIONS]
    planned += [plan.name for plan in names.PLACES] + [plan.area for plan in names.PLACES]
    planned += [alias for plan in names.PLACES for alias in plan.aliases]
    planned += [*build.NOT_MEASURED, build.NO_COST, build.MODELLED_COST]
    planned += [name for pair in build.NOT_ROUTED for name in pair]
    assert len(planned) > 120
    for name in planned:
        assert not any(real in name.casefold() for real in ONCE_USED), name
        assert name.casefold() not in ONCE_A_NAME_OF_ITS_OWN, name


PACKAGES = Path(__file__).parents[3]
# Every file of code the backend holds. The web app keeps its own.
SOURCES = sorted(
    path
    for folder in ("packages", "services", "tools")
    for path in (PACKAGES / folder).rglob("*.py")
    if ".venv" not in path.parts and path != Path(__file__)
)


def _any_of(names: tuple[str, ...]) -> str:
    return "|".join(re.escape(name) for name in names)


# Any of the names, found in one reading of a text. Most texts hold none, and are
# then read once and not once for each name.
ANY_ONCE_USED = re.compile(
    rf"(?<![a-z])(?:{_any_of((*ONCE_USED, *ONCE_IN_A_TEST))})(?![a-z])"
    rf"|[\"'](?:{'|'.join(ONCE_A_NAME_OF_ITS_OWN)})[\"']"
)


def once_used_in(text: str) -> list[str]:
    """Each name that was replaced and stands in a text: as a word, or as a name of its own."""
    folded = text.casefold()
    if not ANY_ONCE_USED.search(folded):
        return []
    found = [
        name
        for name in (*ONCE_USED, *ONCE_IN_A_TEST)
        # As a whole word, in whatever case: the name of a constant is a name too.
        if re.search(rf"(?<![a-z]){re.escape(name)}(?![a-z])", folded)
    ]
    found += [name for name in ONCE_A_NAME_OF_ITS_OWN if re.search(rf"[\"']{name}[\"']", folded)]
    return found


def test_a_name_that_was_replaced_is_in_no_file_of_code_or_of_tests():
    # The list above sees the names of the release. It did not see a constant that was
    # still named for a hamlet, or a station in a release a test had built by hand.
    assert len(SOURCES) > 60
    assert {path.parts[len(PACKAGES.parts)] for path in SOURCES} == {
        "packages",
        "services",
        "tools",
    }
    held = {
        str(path.relative_to(PACKAGES)): found
        for path in SOURCES
        if (found := once_used_in(path.read_text(encoding="utf-8")))
    }
    assert not held
    # The check finds what it is for: a constant, a name in a test, and an alias that
    # stands alone. It passes the same words inside a longer name, and words that only
    # begin like one.
    hamlet, ward, hall = ONCE_USED[0], ONCE_IN_A_TEST[3], ONCE_A_NAME_OF_ITS_OWN[0]
    assert once_used_in(f"ALDERWICK, {hamlet.upper()} = 1, 2") == [hamlet]
    assert once_used_in(f"named(13, '{ward.title()}', PlaceKind.LANDMARK)") == [ward]
    assert once_used_in(f'aliases=("{hall.title()}",)') == [hall]
    assert once_used_in(f'PlacePlan("Tallowgate {hall.title()}", _LANDMARK)') == []
    assert once_used_in("Marrowfen, Farrowmere and the moorings of Sable Reach") == []
    # And each name stands in this file once, where it is listed.
    here = Path(__file__).read_text(encoding="utf-8").casefold()
    for name in (*ONCE_USED, *ONCE_A_NAME_OF_ITS_OWN, *ONCE_IN_A_TEST[:7]):
        assert here.count(f'"{name}"') == 1, name


def test_a_place_that_was_given_a_new_name_kept_its_id():
    # An id is never reused or renamed. Each new name sorts where the old one did,
    # so no area, station or place after it moved up or down.
    release = fixture()
    assert (area("Dulcimer Green").area_id, area("Dulcimer Green").slug) == (
        "syn-n0004",
        "dulcimer-green",
    )
    assert area("Dulcimer Green").aliases == ("Dulcimer",)
    assert (area("Kindlewharf").area_id, area("Kindlewharf").slug) == ("syn-n0011", "kindlewharf")
    assert (area("Wickerford").area_id, area("Wickerford").slug) == ("syn-n0024", "wickerford")
    stations = {row.station_id: row.name for row in release.station_rows}
    assert [stations[f"syn-s{number:04d}"] for number in (3, 4, 9, 16)] == [
        "Coracle Row",
        "Dulcimer Green",
        "Kindlewharf",
        "Wickerford",
    ]
    places = {place.place_id: place.name for place in release.places}
    assert [places[f"syn-p{number:04d}"] for number in (3, 4, 9, 16, 20, 27, 29, 30, 44)] == [
        "Coracle Row",
        "Dulcimer Green",
        "Kindlewharf",
        "Wickerford",
        "Kindlewharf Studios",
        "Kindlewharf School of Art",
        "Dulcimer Green Hospital",
        "Wickerford Cottage Hospital",
        "Scrimshaw Airfield",
    ]
    # An alias that was a name real buildings bear has the borough before it now.
    aliases = {place.place_id: place.aliases for place in release.places}
    assert [aliases[f"syn-p{number:04d}"] for number in (17, 37, 42)] == [
        ("Quillhaven Exchange",),
        ("Quillhaven Playhouse",),
        ("Quillhaven Moot Hall",),
    ]
    # Every id names what it named before, under whatever name: 24 areas, 16 stations, 44 places.
    assert [n.area_id for n in release.neighbourhoods] == [
        f"syn-n{number:04d}" for number in range(1, 25)
    ]
    assert sorted(stations) == [f"syn-s{number:04d}" for number in range(1, 17)]
    assert sorted(places) == [f"syn-p{number:04d}" for number in range(1, 45)]


def test_nothing_in_the_release_could_be_a_real_postcode():
    districts = [p.name for p in fixture().places if p.kind.value == "postcode_district"]
    assert districts
    assert all(name.casefold().startswith(NEVER_A_POSTCODE) for name in districts)
    for name in names_in(fixture()):
        for word in name.casefold().split():
            assert not REAL_POSTCODE.match(word), f"{name!r} could be a real postcode"


def test_every_coordinate_lies_in_open_sea():
    release = fixture()
    points = [n.centroid for n in release.neighbourhoods]
    points += [d.centroid for d in release.destinations]
    points += [p.centroid for p in release.places]
    for drawn in release.geometries:
        points += ring(drawn)
    assert len(points) > 300
    for lon, lat in points:
        assert LONGITUDES[0] <= lon <= LONGITUDES[1]
        assert LATITUDES[0] <= lat <= LATITUDES[1]


def test_the_release_says_that_it_is_synthetic_wherever_it_can():
    release = fixture()
    manifest = release.manifest
    assert manifest.synthetic is True
    assert manifest.release_id.startswith("syn-")
    assert [(s.source_id, s.attribution) for s in manifest.sources] == [
        ("synthetic", SYNTHETIC_ATTRIBUTION)
    ]
    assert "describes no real place" in SYNTHETIC_ATTRIBUTION
    ids = [n.area_id for n in release.neighbourhoods] + [p.place_id for p in release.places]
    ids += [d.destination_id for d in release.destinations]
    ids += [row.station_id for row in release.station_rows]
    assert all(found.startswith("syn-") for found in ids)
    # The flag travels with everything that is worked out from the release.
    assert rank(default_spec(Tenure.RENT), release).synthetic is True
    facts = facts_for(release, area("Alderwick").area_id, None)
    assert facts
    assert all(fact.synthetic for fact in facts)
    assert {source.source_id for fact in facts for source in fact.sources} == {"synthetic"}


def test_every_place_and_area_is_found_by_its_own_name():
    release = fixture()
    for place in release.places:
        assert resolve_place(place.name, release).resolved == place.place_id
    for found in release.neighbourhoods:
        assert resolve_area(found.name, release).resolved == found.area_id


def test_every_fact_about_every_area_can_be_said_and_passes_the_verifier():
    release = fixture()
    place_id = {place.name: place.place_id for place in release.places}
    # A budget, and journeys of each kind: by train, on foot, to a postcode, beyond the cutoff.
    journeys_to = (
        ("Pellam Cross", Mode.PT),
        ("QH2", Mode.WALK),
        ("Scrimshaw Airfield", Mode.PT),
    )
    base = default_spec(Tenure.RENT)
    spec = base.replace(
        budget=base.budget.replace(amount=1500),
        commutes=tuple(
            Commute(
                place_id=place_id[name],
                mode=mode,
                max_minutes=45,
                strictness=Strictness.SOFT,
                provenance=Provenance.STATED,
            )
            for name, mode in journeys_to
        ),
    )
    said = set[str]()
    for found in release.neighbourhoods:
        facts = {fact.fact_id: fact for fact in facts_for(release, found.area_id, spec)}
        for fact in facts.values():
            assert fact.sources and fact.as_of and fact.synthetic
            assert verify(render(fact), facts).ok, fact.fact_id
            said.add(fact.template.value)
    assert {"travel_pt", "travel_other", "travel_beyond", "missing", "station_nearby"} <= said


SYNTHETIC_PACKAGE = Path(build.__file__).parent
# Arithmetic, a seeded random source and records. Nothing that can open a file or a socket.
MAY_IMPORT = {"math", "random", "collections.abc", "dataclasses", "itertools"}


@pytest.mark.parametrize(
    "module", sorted(SYNTHETIC_PACKAGE.glob("*.py")), ids=lambda path: path.stem
)
def test_the_generator_reads_no_file_and_no_dataset(module: Path):
    """Why it needs no licence gate: there is nothing it could have read."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    ours = ("burro_core", "burro_pipeline.release.synthetic")
    assert {name for name in imported if not name.startswith(ours)} <= MAY_IMPORT
    named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert not named & {"open", "print", "input", "eval", "exec", "__import__"}


def km_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    return chart.KM_PER_DEGREE * math.hypot(a[0] - b[0], a[1] - b[1])


def journeys_by(mode: Mode) -> Iterator[tuple[float, int]]:
    """Every journey that has a time, as the distance in a straight line and the minutes."""
    release = fixture()
    for origin in release.neighbourhoods:
        for end in release.destinations:
            travel = release.travel(origin.area_id, end.destination_id, mode, PtBasis.TYPICAL)
            if travel.minutes is not None:
                yield km_between(origin.centroid, end.centroid), travel.minutes


@pytest.mark.parametrize(
    ("mode", "per_km", "fixed"),
    [
        (Mode.WALK, journeys.WALK_MIN_PER_KM, 0.0),
        (Mode.CYCLE, journeys.CYCLE_MIN_PER_KM, journeys.CYCLE_FIXED_MIN),
    ],
)
def test_a_journey_takes_as_long_as_the_map_says(mode: Mode, per_km: float, fixed: float):
    found = list(journeys_by(mode))
    assert len(found) > 100
    for km, minutes in found:
        # The streets add a detour to the straight line, and the river may add a bridge.
        shortest = fixed + per_km * journeys.DETOUR * km
        longest = shortest + per_km * journeys.BRIDGE_KM
        # And no journey is held as shorter than the shortest the release allows.
        assert max(shortest - 1, journeys.SHORTEST_MIN) <= minutes
        assert minutes <= max(longest + 1, journeys.SHORTEST_MIN)


@cache
def redrawn(seed: int) -> InMemoryRelease:
    """The city drawn from another seed, or the committed one for the seed it is built with."""
    return fixture() if seed == SEED else build_synthetic(seed)


def times_in(release: InMemoryRelease) -> Iterator[tuple[str, int]]:
    """Every time the release holds in minutes, with what it is the time of."""
    for origin in release.neighbourhoods:
        for end in release.destinations:
            for mode, basis in (
                (Mode.PT, PtBasis.TYPICAL),
                (Mode.PT, PtBasis.JUST_MISSED),
                (Mode.CYCLE, PtBasis.TYPICAL),
                (Mode.WALK, PtBasis.TYPICAL),
            ):
                found = release.travel(origin.area_id, end.destination_id, mode, basis).minutes
                if found is not None:
                    yield f"{origin.name} to {end.destination_id}, {mode.value}", found
    for row in release.station_rows:
        yield f"{row.area_id} to the station {row.name}", row.walk_minutes
    for row in release.features:
        if row.feature_id is FeatureId.STATION_WALK and row.value is not None:
            yield f"{row.area_id}, the walk to its station", round(row.value)


@pytest.mark.parametrize("seed", [SEED, 1, 2, 3])
def test_no_journey_is_shorter_than_two_minutes(seed: int):
    # "About 0 minutes" is no journey, and "about 1 minutes" is no sentence. Next door is
    # still down the stairs and across the road.
    times = list(times_in(redrawn(seed)))
    assert len(times) > 3_000
    too_short = sorted(what for what, minutes in times if minutes < journeys.SHORTEST_MIN)
    assert not too_short
    assert journeys.SHORTEST_MIN == 2


def test_the_shortest_journeys_of_the_release_are_held_at_two_minutes():
    # The works stand at the middle of Cindermoor: no distance at all, which was 0 minutes.
    # Two stations stand a minute from the middle of their areas.
    release = fixture()
    works = destination("Cindermoor Works")
    for mode in (Mode.WALK, Mode.PT, Mode.CYCLE):
        there = release.travel(area("Cindermoor").area_id, works, mode, PtBasis.TYPICAL)
        assert (there.status, there.minutes) == (TravelStatus.OK, 2), mode
    for name in ("Brackenhythe", "Wickerford"):
        (nearest, *_) = release.stations(area(name).area_id)
        assert (nearest.name, nearest.walk_minutes) == (name, 2)
        assert value(name, FeatureId.STATION_WALK) == 2
        on_foot = release.travel(area(name).area_id, destination(name), Mode.WALK, PtBasis.TYPICAL)
        assert on_foot.minutes == nearest.walk_minutes


@pytest.mark.parametrize(
    ("minutes", "held_as"),
    [(0.0, 2), (0.4, 2), (1.49, 2), (2.0, 2), (2.4, 2), (2.6, 3), (44.5, 44), (45.5, 46)],
)
def test_a_time_is_a_whole_number_of_minutes_and_never_under_two(minutes: float, held_as: int):
    assert journeys.whole_minutes(minutes) == held_as


def test_public_transport_is_never_slower_than_walking_nor_faster_than_a_train():
    release = fixture()
    seen = 0
    for origin in release.neighbourhoods:
        for end in release.destinations:
            ids = (origin.area_id, end.destination_id)
            typical = release.travel(*ids, Mode.PT, PtBasis.TYPICAL).minutes
            missed = release.travel(*ids, Mode.PT, PtBasis.JUST_MISSED).minutes
            on_foot = release.travel(*ids, Mode.WALK, PtBasis.TYPICAL).minutes
            if typical is None:
                continue
            seen += 1
            assert (
                typical >= journeys.RAIL_MIN_PER_KM * km_between(origin.centroid, end.centroid) - 1
            )
            assert on_foot is None or typical <= on_foot
            assert missed is None or typical <= missed <= typical + journeys.BUS_HEADWAY_MIN
    assert seen > 900


def test_an_area_on_a_line_reaches_the_centre_sooner_than_one_as_far_out_that_is_not():
    centre = destination("Pellam Cross")

    def minutes(name: str) -> int:
        found = fixture().travel(area(name).area_id, centre, Mode.PT, PtBasis.TYPICAL).minutes
        assert found is not None
        return found

    def km(name: str) -> float:
        return km_between(area(name).centroid, area("Pellam Cross").centroid)

    # Both are at the edge of the city. Farrowmere is the end of the Cobalt line.
    assert km("Farrowmere") > km("Marrowfen")
    assert minutes("Farrowmere") + 5 < minutes("Marrowfen")
    assert minutes("Pellam Cross") < minutes("Cindermoor") < minutes("Marrowfen")


def test_station_features_say_what_the_station_rows_say():
    release = fixture()
    for found in release.neighbourhoods:
        rows = release.stations(found.area_id)
        assert [row.nearest for row in rows] == [True] + [False] * (len(rows) - 1)
        assert value(found.name, FeatureId.STATION_WALK) == rows[0].walk_minutes
        nearby = [row for row in rows if row.walk_minutes <= NEARBY_STATION_MINUTES]
        lines = {line for row in nearby for line in row.lines}
        assert value(found.name, FeatureId.STATION_LINES) == len(lines)
    # The centre has two stations within a short walk, and between them every line.
    assert [row.name for row in release.stations(area("Pellam Cross").area_id)] == [
        "Pellam Cross",
        "Coracle Row",
    ]
    assert value("Pellam Cross", FeatureId.STATION_LINES) == 4
    assert value("Gorsebeck", FeatureId.STATION_LINES) == 0


def test_the_distance_to_a_university_is_the_distance_to_one_of_the_two_in_the_release():
    campuses = [p.centroid for p in fixture().places if p.kind.value == "university"]
    assert len(campuses) == 2
    for found in fixture().neighbourhoods:
        metres = value(found.name, FeatureId.UNIVERSITY_PROXIMITY)
        assert metres is not None
        nearest = min(km_between(found.centroid, campus) for campus in campuses)
        by_street = 1000 * journeys.DETOUR * nearest
        assert by_street - 50 <= metres <= by_street + 1000 * journeys.BRIDGE_KM + 50


def test_only_the_areas_on_the_river_are_near_water_and_the_bend_is_nearest():
    on_the_river = {
        "Brackenhythe",
        "Hollinsworth Quay",
        "Pellam Cross",
        "Tallowgate",
        "Wickerford",
        "Osierholm",
        "Kindlewharf",
        "Sable Reach",
        "Grapnel Dock",
    }
    near = {n.name: value(n.name, FeatureId.WATER_ACCESS) or 0.0 for n in fixture().neighbourhoods}
    assert {name for name, share in near.items() if share > 5} == on_the_river
    # Sable Reach is inside the bend, with water on two sides.
    assert max(near, key=lambda name: near[name]) == "Sable Reach"


def test_areas_that_are_neighbours_share_a_side_and_the_river_is_not_one():
    release = fixture()
    corners = {drawn.area_id: set(ring(drawn)) for drawn in release.geometries}
    for found in release.neighbourhoods:
        assert found.neighbours
        for other in found.neighbours:
            assert len(corners[found.area_id] & corners[other]) >= 3
    # Kindlewharf faces the centre across the water. They share no side.
    assert area("Kindlewharf").area_id not in area("Pellam Cross").neighbours
    assert not corners[area("Kindlewharf").area_id] & corners[area("Pellam Cross").area_id]


def test_nearer_the_centre_is_denser_noisier_dearer_and_a_shorter_journey():
    release = fixture()
    centre = area("Pellam Cross")
    ranked = [n for n in release.neighbourhoods if n.rankable]
    ranked.sort(key=lambda n: km_between(n.centroid, centre.centroid))
    inner, outer = ranked[:8], ranked[-8:]

    def mean(found: list[Neighbourhood], figure: Callable[[Neighbourhood], float | None]) -> float:
        known = [x for x in (figure(n) for n in found) if x is not None]
        return sum(known) / len(known)

    def feature(feature_id: FeatureId) -> Callable[[Neighbourhood], float | None]:
        return lambda n: value(n.name, feature_id)

    def rent(n: Neighbourhood) -> float | None:
        estimate = release.cost(n.area_id, Tenure.RENT, Segment.BED_1)
        return None if estimate is None else estimate.median

    def journey(n: Neighbourhood) -> float | None:
        to = destination("Pellam Cross")
        return release.travel(n.area_id, to, Mode.PT, PtBasis.TYPICAL).minutes

    for feature_id in (FeatureId.HOMES_DENSITY, FeatureId.NOISE_EXPOSURE, FeatureId.AIR_NO2):
        assert mean(inner, feature(feature_id)) > 1.5 * mean(outer, feature(feature_id))
    assert mean(inner, rent) > mean(outer, rent) + 300
    assert mean(inner, journey) + 15 < mean(outer, journey)


def test_gaps_are_left_on_purpose_and_nothing_fills_them():
    release = fixture()
    # About one figure in twenty is missing, and a missing figure has no percentile.
    missing = [row for row in release.features if row.value is None]
    assert 0.03 < len(missing) / len(release.features) < 0.08
    assert all(row.percentile is None and row.coverage < 0.5 for row in missing)
    assert any(0.5 <= row.coverage < 1 for row in release.features if row.value is not None)
    for name, features in build.NOT_MEASURED.items():
        assert all(value(name, feature_id) is None for feature_id in features)

    # A tag is unknown where too little of its formula is known.
    unknown = {(row.area_id, row.tag_id.value) for row in release.tags if row.score is None}
    assert (area("Gorsebeck").area_id, "historic_character") in unknown
    assert (area("Gorsebeck").area_id, "leafy") not in unknown

    # One area that can be ranked has no cost estimate at all.
    costed = {row.area_id for row in release.costs}
    without = [n.name for n in release.neighbourhoods if n.rankable and n.area_id not in costed]
    assert without == [build.NO_COST]
    # And where a kind of home is too rare to estimate there is no row, not a guess.
    assert release.cost(area("Pellam Cross").area_id, Tenure.BUY, Segment.DETACHED) is None


def test_a_journey_that_was_not_computed_is_not_one_that_is_too_long():
    release = fixture()
    for name, place in build.NOT_ROUTED:
        for mode in Mode:
            travel = release.travel(area(name).area_id, destination(place), mode, PtBasis.TYPICAL)
            assert (travel.status, travel.minutes) == (TravelStatus.MISSING, None)
    # The airfield is out of town. From most of the city it is beyond the cutoff, which is known.
    airfield = destination("Scrimshaw Airfield")
    reach = {
        n.name: release.travel(n.area_id, airfield, Mode.PT, PtBasis.TYPICAL)
        for n in release.neighbourhoods
    }
    assert reach["Wickerford"].status is TravelStatus.BEYOND_CUTOFF
    assert reach["Marrowfen"].status is TravelStatus.OK
    statuses = [travel.status for travel in reach.values()]
    assert statuses.count(TravelStatus.BEYOND_CUTOFF) >= 10
    assert TravelStatus.MISSING not in statuses
