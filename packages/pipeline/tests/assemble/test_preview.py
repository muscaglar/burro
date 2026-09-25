"""The step `preview`, run as a person runs it, on the whole of a made-up build.

The town is Quillhaven and Tallowgate, which do not exist, and every figure is
made up. The files are shaped as the publishers' are, so the step that reads
these reads the real ones.
"""

import hashlib
import io
import json
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import tags_of as vibes_of
from burro_core.facts import facts_for
from burro_core.ids import (
    Direction,
    FeatureId,
    GrittyVariant,
    Mode,
    Part,
    Provenance,
    PtBasis,
    TagId,
    Tenure,
    TravelStatus,
)
from burro_core.rank import rank
from burro_core.spec import FeatureWeight, TagWeight, check_spec, default_spec
from burro_pipeline import cli
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.assemble.cli import of_the_list
from burro_pipeline.assemble.release import sources_of
from burro_pipeline.derive import brands_nearby, water_access
from burro_pipeline.derive.measures import MEASURES
from burro_pipeline.evidence.lock import Lock, LockError
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.served import rows_behind, unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.fetch.store import FOLDER_VARIABLE
from burro_pipeline.registry import load
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..cells.support import CANARY, held
from ..derive import test_air_no2 as grid
from ..derive.stops_support import stops_receipt
from ..derive.tfl_support import stations_receipt
from .support import (
    ONE,
    REGISTRY,
    RELEASE,
    THREE,
    File,
    Made,
    files,
    held_back_for_a_while,
    list_of,
    made,
)

Printed = pytest.CaptureFixture[str]
MEASURED = (
    "air_no2",
    "conservation_cover",
    "green_cover",
    "highstreet_access",
    "homes_density",
    "homes_flats",
    "homes_higher_bands",
    "homes_post2000",
    "homes_pre1919",
    "land_gardens",
    "land_industry",
    "land_storage",
    "land_transport_other",
    "land_woodland",
    "listed_buildings",
    "noise_exposure",
    "park_large_proximity",
    "park_proximity",
    "road_major_exposure",
    "road_traffic_nearby",
    "school_primary_nearby",
    "station_walk",
    "venue_food_drink",
    "venue_food_drink_per_homes",
    "water_access",
)
# What the build carries and shows, and ranks no area on by itself. Main roads are
# switched off by their own row, until the founder says otherwise. The count of places
# to eat and drink is shown, and a wish for them is ranked on the places for each 1,000
# homes.
SHOWN_ONLY = ("road_major_exposure", "venue_food_drink")
# What the build works out and leaves out: what it measures is not what core says it is.
# The two of town centres and what a park offers keep core's names until the founder has
# looked at each.
NOT_AS_CORE_SAYS = ("centre_compact", "centre_small", "park_facilities")
# What the build works out and finds no figure of for any area: no play space of the made-up
# town has a way in marked.
NO_FIGURE = ("play_space_proximity",)
# What the build works out and a check of its figures holds back, whatever core says of it.
# No measure is held back today. A test holds one back for a while, to see that the hold
# alone keeps it out.
HELD_BACK = ()
NO_RECEIPT = "input_has_one_receipt"
# What the build has no file of. The two measures of recorded incidents are counted from the
# police's crime files, the two of cultural venues, the measures of brands and the nearest
# food shop from the file of places, the nearest GP practice from the report of practices,
# and the nearest pharmacy
# from the pharmaceutical list. So are the cafes, the gyms and the pubs and bars, and the
# homes near a cluster of pubs and bars, from the file of places. The made-up build holds
# none of them, so each is left out. So is what homes sell for, and how far it has risen:
# their workbook is in no list of the build. And so are the measures of how near stops
# are: four read the national file of stops, and the made-up build holds the file of London
# alone, and one reads the
# routes of buses, which it does not hold. So are the four shares of who lived in an area:
# the two census tables they are read from are in a list of their own, which the made-up
# build does not take. So is private outdoor space, whose workbook is in a list of its own:
# with its files a build carries it, and `test_preview_of_outdoor_space.py` holds that. And
# so is how much of the nearest high street lies in a conservation area, whose file of high
# streets is in a list of its own: `test_preview_of_high_streets.py` holds that.
INCIDENTS = ("incident_antisocial", "incident_criminal_damage")
CULTURE = ("culture_venues", "culture_venues_per_homes")
SURGERY, PHARMACY, FOOD_SHOP = ("gp_walk",), ("pharmacy_walk",), ("grocery_walk",)
BRANDS = tuple(feature.value for feature in brands_nearby.FEATURES)
VENUES = (
    "evening_cluster_exposure",
    "venue_cafe",
    "venue_cafe_per_homes",
    "venue_evening",
    "venue_evening_per_homes",
    "venue_gym",
    "venue_gym_per_homes",
)
STOPS_NEARBY = (
    "bus_routes_nearby",
    "bus_stops_nearby",
    "overground_proximity",
    "rail_proximity",
    "underground_proximity",
)
HOUSEHOLDS = ("households_dependent_children", "households_one_person")
RESIDENTS = ("residents_aged_20_34", "residents_aged_65_over")
OF_PRICES = ("price_median", "price_rise_10y", "price_rise_5y")
OUTDOOR_SPACE = ("private_outdoor_space",)
HIGH_STREET = ("highstreet_conserved",)
NO_FILE = (
    *BRANDS,
    *CULTURE,
    *VENUES,
    *SURGERY,
    *PHARMACY,
    *FOOD_SHOP,
    *INCIDENTS,
    *OF_PRICES,
    *STOPS_NEARBY,
    *HOUSEHOLDS,
    *RESIDENTS,
    *OUTDOOR_SPACE,
    *HIGH_STREET,
)
POLICE, PRICES = "police-uk-street-level-crime", "ons-median-house-prices-msoa"
OUTDOOR = "ons-access-to-garden-space-2020"
HIGH_STREETS = "gla-high-street-boundaries"
CENSUS = "ons-census-2021-age-and-household-tables"
PLACES, PRACTICES = "overture-places", "nhs-ods-gp-practices"
PHARMACIES = "nhsbsa-consolidated-pharmaceutical-list"
WORKBOOK = "mhclg-iod-2025-underlying-indicators"
REGISTER = "fsa-food-hygiene-ratings"
# The measures of the files that the second of two lists names, each with its source.
SOURCE_OF = {
    "centre_compact": "gla-town-centre-boundaries",
    "centre_small": "gla-town-centre-boundaries",
    "conservation_cover": "mhclg-planning-data-conservation-areas",
    "listed_buildings": "historic-england-listed-buildings",
    "green_cover": "os-open-greenspace",
    "highstreet_access": "gla-town-centre-boundaries",
    "park_facilities": "os-open-greenspace",
    "park_large_proximity": "os-open-greenspace",
    "park_proximity": "os-open-greenspace",
    "play_space_proximity": "os-open-greenspace",
    **dict.fromkeys(OF_PRICES, PRICES),
    "road_major_exposure": "os-open-roads",
    "school_primary_nearby": "dfe-gias",
    "station_walk": "dft-naptan",
    "venue_food_drink": REGISTER,
    "venue_food_drink_per_homes": REGISTER,
    "water_access": "os-open-rivers",
}
# The source of each measure that is worked out and left out.
LEFT_OUT_FROM = {
    "centre_compact": "gla-town-centre-boundaries",
    "centre_small": "gla-town-centre-boundaries",
    "park_facilities": "os-open-greenspace",
    "play_space_proximity": "os-open-greenspace",
}
# All that a build leaves out, in the order of the ids, which is the order a build says them
# in, each with the rule that keeps it out and the source it is said with.
LEFT_OUT = tuple(sorted((*HELD_BACK, *NO_FILE, *NO_FIGURE, *NOT_AS_CORE_SAYS)))
RULE_OF = (
    dict.fromkeys(NO_FILE, NO_RECEIPT)
    | dict.fromkeys(NO_FIGURE, "measure_has_a_figure")
    | dict.fromkeys(HELD_BACK, "measure_is_not_held_back")
    | dict.fromkeys(NOT_AS_CORE_SAYS, "measure_is_as_core_says")
)
SAID_WITH = (
    dict.fromkeys(INCIDENTS, POLICE)
    | dict.fromkeys((*CULTURE, *BRANDS, *VENUES, *FOOD_SHOP), PLACES)
    | dict.fromkeys(SURGERY, PRACTICES)
    | dict.fromkeys(PHARMACY, PHARMACIES)
    | dict.fromkeys(STOPS_NEARBY, "dft-naptan")
    | {"bus_routes_nearby": "tfl-bus-stops-and-routes"}
    | dict.fromkeys((*HOUSEHOLDS, *RESIDENTS), CENSUS)
    | dict.fromkeys(OF_PRICES, PRICES)
    | dict.fromkeys(OUTDOOR_SPACE, OUTDOOR)
    | dict.fromkeys(HIGH_STREET, HIGH_STREETS)
    | dict.fromkeys(HELD_BACK, REGISTER)
    | LEFT_OUT_FROM
)
# The files of the made-up build, and the vibes that rest on parks: green cover is a part
# of Leafy, and the nearest park of Parks close by.
FILES, SQUARES, LEAFY = 25, ("sites-tb", "sites-tc", "sites-tg", "sites-th"), "leafy"
# The file of the food register of each of the town's two authorities.
REGISTERS = ("register-901", "register-902")
# The two files of the planning data platform, by their names in the list.
HERITAGE = ("conservation-areas", "listed-buildings")
PARKS, QUIET = "parks_close_by", "quiet_residential"
# The files of the second list, where a build is given two. The table of land use is in
# the first.
LATER = (*SQUARES, "roads", "schools", "stops", "town-centres", "water", *HERITAGE)
# The vibes a build can place. Homes rests on two of its three parts, 75 in 100: flats and
# homes per hectare. Parks close by rests on two of its three, 70 in 100: the nearest park
# and the nearest large park. Quiet streets rests on three of its four, 70 in 100: main
# roads, traffic and transport noise. Built age rests on all four of its parts: homes built before
# 1919, homes built since 2000, conservation cover and listed buildings. Leafy rests on all
# three of its parts: gardens, woodland, and public parks and gardens. Family amenities
# rests on two of its three, 65 in 100: the primary schools and the nearest park. Going out
# is not placed: it holds the places to eat and drink and the nearest town centre, which are
# 50 in 100, and its pubs and its culture are counted from the file of places, which the
# made-up build does not hold. Works and warehouses is a part of Gritty, and no vibe of a
# build. The two vibes that count who lived in an area have no band: no census table is
# read, and what is left of each is under 60 in 100 of its recipe.
HOMES, BUILT_AGE, VILLAGE = "homes", "built_age", "village_feel"
FAMILY, GOING_OUT = "family_amenities", "pace"
PLACED = {
    BUILT_AGE: 1.0,
    FAMILY: 0.65,
    HOMES: 0.75,
    LEAFY: 1.0,
    PARKS: 0.7,
    QUIET: 0.7,
}


def lines_of(capsys: Printed) -> tuple[list[str], str]:
    out = capsys.readouterr()
    return out.out.splitlines(), out.err


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The made-up build, built once for every test that only reads it.

    What the step printed is thrown away. A test that changes what was built
    builds its own.
    """
    found = made(tmp_path_factory.mktemp("built"))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run() == 0
    return found


# The made-up files


def test_the_made_up_files_are_the_same_files_whenever_a_test_makes_them(
    monkeypatch: pytest.MonkeyPatch,
):
    """A zip holds the time its members were written, and a file is known by its hash.

    A test that made the files again to name one failed when the clock had moved on.
    """
    made_at: list[dict[str, str]] = []
    for clock in (1_790_000_000.0, 1_790_000_100.0):
        monkeypatch.setattr(time, "time", lambda clock=clock: clock)
        made_at.append({item: file.sha256 for item, file in files().items()})
    assert made_at[0] == made_at[1]


# What the step does


def test_the_step_builds_a_release_and_prints_one_line_for_each_part_of_the_work(
    tmp_path: Path, capsys: Printed
):
    assert made(tmp_path).run() == 0
    said, _ = lines_of(capsys)
    assert all(is_public(line) for line in said)
    assert [line.split()[0] + " " + line.split()[1] for line in said] == [
        "step=seal status=ok",
        "step=cells status=ok",
        *(["step=derive status=ok"] * len(MEASURED)),
        *(["step=derive status=skipped"] * len(LEFT_OUT)),
        "step=places status=ok",
        "step=assemble status=ok",
        "step=check status=ok",
        "step=report status=ok",
    ]
    assert said[0].startswith(f"step=seal status=ok release={RELEASE} inputs={FILES} missing=0 ")
    assert said[1].endswith("areas=3 output_areas=12 lsoas=6 msoas=3 boroughs=2 files=4")
    assert [line.split()[2] for line in said[2:-4]] == [
        f"feature={feature}" for feature in (*MEASURED, *LEFT_OUT)
    ]
    # The three stations of the made-up file, and where the homes of each area stand.
    assert said[-4] == "step=places status=ok source=dft-naptan rows=3 areas=3 files=2"
    assert f" areas=3 measures={len(MEASURED)} files=11 manifest_sha256=" in said[-3]
    assert " findings=0 " in said[-2]


def test_it_runs_through_the_pipelines_one_command_line(tmp_path: Path, capsys: Printed):
    found = made(tmp_path)
    assert "preview" in cli.STEPS
    assert cli.parse(found.arguments()).command == "preview"


def test_what_it_prints_names_no_area_and_repeats_nothing_from_a_file(
    tmp_path: Path, capsys: Printed
):
    assert made(tmp_path).run() == 0
    said = "".join(capsys.readouterr())
    for word in (CANARY, "Quillhaven", "Tallowgate", "E00999", "E01999", "lon-n", str(tmp_path)):
        assert word not in said


def test_the_release_is_one_that_core_opens(build: Made):
    release = read_release(build.release)
    assert [area.name for area in release.neighbourhoods] == [
        "Quillhaven 001",
        "Quillhaven 002",
        "Tallowgate 001",
    ]
    assert [metric.feature_id for metric in release.metrics] == list(MEASURED)
    assert all(release.geometry(area.area_id) for area in release.neighbourhoods)
    counts = release.manifest.counts
    assert (counts.neighbourhoods, counts.rankable) == (3, 3)
    # The three stations of the file of stops, each a place and the end of journeys to it.
    assert (counts.destinations, counts.places, counts.stations) == (3, 3, 0)


def test_built_twice_from_the_same_files_it_writes_the_same_bytes(
    build: Made, tmp_path: Path, capsys: Printed
):
    assert build.run(out=tmp_path / "again") == 0
    first, second = held(build.out), held(tmp_path / "again")
    assert first == second
    # The 11 files of the release, and the 7 that stand beside it.
    assert len(first) == 18


def test_nothing_is_written_to_the_store_or_to_the_receipts(tmp_path: Path, capsys: Printed):
    found = made(tmp_path)
    before = held(found.store), held(found.receipts)
    assert found.run() == 0
    assert (held(found.store), held(found.receipts)) == before


def test_a_release_that_is_there_is_never_written_over(build: Made, capsys: Printed):
    before = held(build.out)
    assert build.run() == 2
    said, words = lines_of(capsys)
    assert said == ["step=assemble status=unreadable"]
    assert "is there already" in words and "a correction is a new release" in words
    assert held(build.out) == before


def test_nothing_made_from_a_publishers_file_is_written_where_git_would_take_it_in(
    tmp_path: Path, capsys: Printed
):
    """The step's own example once left copies of publishers' files in the working copy."""
    found = made(tmp_path / "build")
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    inside = ["--root", str(repository), "--commit", "0" * 40]
    for more in (["--out", str(repository / "out")], ["--work", str(repository / "copies")]):
        arguments = [*found.arguments(), *inside, *more]
        assert assemble.main(arguments, {FOLDER_VARIABLE: str(found.store)}) == 2
        said, words = lines_of(capsys)
        assert said == ["step=assemble status=unreadable"]
        assert f"{more[0]} is inside the repository" in words
        assert "data/releases/ or scratch/" in words
    assert sorted(path.name for path in repository.iterdir()) == [".git"]


# It says it is real, and unfinished


def test_the_release_says_that_it_is_not_made_up_and_that_it_is_a_preview(build: Made):
    manifest = read_release(build.release).manifest
    assert (manifest.synthetic, manifest.preview, manifest.city, manifest.seed) == (
        False,
        True,
        "lon",
        None,
    )
    assert all(
        not area.area_id.startswith("syn-") for area in read_release(build.release).neighbourhoods
    )


def test_the_lock_says_it_is_a_development_build(build: Made):
    lock = Lock.model_validate_json((build.beside / "lock.json").read_bytes())
    assert lock.development and lock.release_id == RELEASE
    assert read(build.beside / "build.json")["development"] is True


# What is not measured is not there


def test_what_a_first_build_has_not_measured_is_not_in_it_and_nothing_stands_in(build: Made):
    release = read_release(build.release)
    assert (release.costs, release.station_rows) == ((), ())
    for part in (Part.TRAVEL, Part.STATIONS):
        assert not release.origin(part).stated
    # It names the stations as places to reach, and holds no journey time to any.
    assert release.travel_table.destination_ids == ()
    for end in release.destinations:
        journey = release.travel(ONE, end.destination_id, Mode.PT, PtBasis.TYPICAL)
        assert (journey.status, journey.minutes) == (TravelStatus.MISSING, None)
    # Core works each vibe out, from the parts of its recipe that are measured. A release
    # that is not made up carries the twelve and gritty as the one scale, which holds recorded
    # incidents. No file of them is read, so they are parts with no figure.
    assert release.manifest.gritty_variant is GrittyVariant.B
    assert release.vibes == vibes_of(GrittyVariant.B)
    gritty = [tag for tag in release.tags if tag.tag_id is TagId.STREET_CHARACTER]
    assert len(gritty) == 3 and {(tag.score, tag.band) for tag in gritty} == {(None, None)}
    assert len(release.tags) == 3 * 14
    # Nothing stands in for who lives somewhere: a vibe that counts them is not placed on
    # the places alone where they are under 60 in 100 of it.
    for vibe in (TagId.FAMILY_AREA, TagId.YOUNG_PROFESSIONALS):
        unplaced = [tag for tag in release.tags if tag.tag_id is vibe]
        assert {(tag.score, tag.band) for tag in unplaced} == {(None, None)}
        assert all(tag.coverage < 0.6 for tag in unplaced)
    # Six vibes have 60 in 100 of their recipe measured. Each is placed on the parts that
    # are, in each of the three areas, and says so. No other vibe has a band.
    placed = [tag for tag in release.tags if tag.score is not None]
    assert {tag.tag_id: tag.coverage for tag in placed} == PLACED
    assert len(PLACED) == 6 and len(placed) == 3 * len(PLACED)
    assert all(
        tag.band is not None and tag.band == tag.spread_low == tag.spread_high for tag in placed
    )
    others = [tag for tag in release.tags if tag.tag_id not in PLACED]
    assert all((tag.raw, tag.score, tag.band) == (None, None, None) for tag in others)
    assert all(tag.coverage < 0.6 for tag in others)
    # Public parks and gardens are 30 in 100 of Leafy. Gardens and woodland are the rest,
    # and the table of land use gives both.
    assert {tag.coverage for tag in release.tags if tag.tag_id == LEAFY} == {1.0}


def test_an_area_with_too_little_behind_a_figure_has_none_and_is_never_given_nought(build: Made):
    """Three of the four output areas of the third area stand off the made-up grid."""
    release = read_release(build.release)
    found = release.feature(THREE, FeatureId.AIR_NO2)
    assert found is not None
    assert (found.value, found.percentile, found.coverage) == (
        None,
        None,
        pytest.approx(0.2, abs=0.05),
    )
    row = Evidence.model_validate_json((build.beside / "evidence.json").read_bytes()).row(
        f"{THREE}/feature/air_no2"
    )
    assert row is not None and row.state is State.BELOW_THRESHOLD


def test_a_percentile_is_the_one_core_gives(build: Made):
    release = read_release(build.release)
    found = [
        release.feature(area.area_id, FeatureId.HOMES_DENSITY) for area in release.neighbourhoods
    ]
    assert [(f.value, f.percentile) for f in found if f] == [
        (50.0, 50.0),
        (10.0, 16.7),
        (100.0, 83.3),
    ]


def test_main_roads_are_shown_and_no_area_is_ranked_on_them_alone(build: Made):
    """The row of the measure switches it off, so the release ranks no area on it by itself.

    230 of the 500 homes of the first area stand on the square the A road runs by, 480
    of the 660 of the second and 190 of the 820 of the third. Quiet streets rests on
    the figure all the same, and may be asked for.
    """
    release = read_release(build.release)
    roads = FeatureId.ROAD_MAJOR_EXPOSURE
    found = [release.feature(area.area_id, roads) for area in release.neighbourhoods]
    assert [one.value for one in found if one] == [46.0, 72.7, 23.2]
    assert {metric.feature_id: metric.rankable for metric in release.metrics} == {
        FeatureId(feature): feature not in SHOWN_ONLY for feature in MEASURED
    }
    nothing = default_spec(Tenure.RENT).replace(weights=())
    alone = FeatureWeight(
        feature_id=roads, weight=0.5, direction=Direction.LESS, provenance=Provenance.UI_EDIT
    )
    asked = check_spec(nothing.replace(weights=(alone,)), release)
    assert [one.problem for one in asked] == ["not_in_release"]
    quiet = TagWeight(tag_id=TagId.QUIET_RESIDENTIAL, weight=0.5, provenance=Provenance.UI_EDIT)
    assert check_spec(nothing.replace(tags=(quiet,)), release) == ()
    ranked = rank(nothing.replace(tags=(quiet,)), release)
    # The third area has the fewest homes by a main road, and the least noise but one.
    assert ranked.ranked[0].area_id == THREE


def test_the_release_ranks_on_what_it_measures(build: Made):
    release = read_release(build.release)
    spec = default_spec(Tenure.RENT)
    carried = {metric.feature_id for metric in release.metrics}
    spec = spec.replace(weights=tuple(w for w in spec.weights if w.feature_id in carried))
    ranked = rank(spec, release)
    assert [area.area_id for area in ranked.ranked] and not ranked.filtered


# A figure traces to its evidence, to its file, to its receipt


def test_every_fact_of_the_release_has_a_row_a_file_and_a_receipt_in_the_store(build: Made):
    release = read_release(build.release)
    evidence = Evidence.model_validate_json((build.beside / "evidence.json").read_bytes())
    lock = Lock.model_validate_json((build.beside / "lock.json").read_bytes())
    assert unevidenced(release, evidence, lock, load(REGISTRY)) == ()
    for area in release.neighbourhoods:
        for fact in facts_for(release, area.area_id, None):
            # A vibe that cannot be placed, and a likeness, rest on the rows of the figures
            # they were counted from. Every other fact rests on the row of its own id.
            rows = [evidence.row(row_id) for row_id in rows_behind(release, fact.fact_id)]
            assert rows, fact.fact_id
            cited: set[str] = set()
            for row in rows:
                assert row is not None and row.has_a_value and row.derivation_id is not None
                assert evidence.method(row.derivation_id) is not None
                cited |= evidence.sources_of(row)
                for file_id in row.inputs:
                    receipt = evidence.receipt(file_id)
                    assert receipt is not None and lock.holds(file_id)
                    kept = build.store / receipt.vault_key()
                    assert hashlib.sha256(kept.read_bytes()).hexdigest() == receipt.sha256
                    assert (build.receipts / receipt.source_id / f"{file_id}.json").is_file()
            assert {source.source_id for source in fact.sources} <= cited


def test_every_source_a_fact_cites_is_credited_as_the_registry_credits_it(build: Made):
    release = read_release(build.release)
    registry = load(REGISTRY)
    cited = {source_id for metric in release.metrics for source_id in metric.source_ids}
    cited |= set(release.origin(Part.NEIGHBOURHOODS).source_ids)
    assert {source.source_id for source in release.manifest.sources} == cited
    for source in release.manifest.sources:
        entry = registry.get(source.source_id)
        assert (source.name, source.publisher, source.attribution, source.url) == (
            entry.name,
            entry.publisher,
            entry.attribution,
            entry.url,
        )
        assert source.retrieved_on == "2026-09-23"


def test_every_pair_of_an_area_and_a_measure_has_a_row_and_a_state(build: Made):
    coverage = read(build.beside / "coverage.json")
    assert len(coverage["cells"]) == 3 * len(coverage["measures"])
    assert [cell for cell in coverage["cells"] if not cell["record"]] == []
    states = {
        cell["measure"]: cell["state"] for cell in coverage["cells"] if cell["area_id"] == ONE
    }
    assert states["feature/homes_flats"] == "present"
    for feature in LEFT_OUT:
        assert states[f"feature/{feature}"] == "not_carried"
    assert (
        states["travel/pt"]
        == states["cost/rent.bed_1"]
        == states["station/nearest"]
        == "not_carried"
    )
    # Homes built before 1919 and conservation cover are 35 in 100 of Village feel, which is
    # too few to place an area. The source of conservation areas decides no vibe alone.
    assert states[f"tag/{VILLAGE}"] == "below_threshold"
    # The places to eat and drink for each 1,000 homes alone are 40 in 100 of Food and drink.
    assert states["tag/foodie"] == "below_threshold"
    # Without what was recorded, Gritty holds 55 in 100 of its recipe.
    assert states["tag/street_character"] == "below_threshold"
    # Each vibe that is placed on part of its recipe says so, and its row says how much.
    assert {vibe: states[f"tag/{vibe}"] for vibe in PLACED} == {
        vibe: "present" if share == 1.0 else "partial" for vibe, share in PLACED.items()
    }
    report = (build.beside / "coverage.md").read_text(encoding="utf-8")
    assert report.startswith(f"# Coverage of {RELEASE}\n")
    # What no area has is said once, and not once for every area.
    assert report.count("| travel/pt | not_carried | yes |") == 1
    assert f"| {ONE} | travel/pt |" not in report
    assert report.count(f"| tag/{VILLAGE} | below_threshold | yes |") == 1
    # The name and the outline of an area, every measure that is carried, and every placed vibe.
    have = 2 + len(MEASURED) + len(PLACED)
    assert f"Of the 144 things Burro measures, {have} have a figure in at least one area." in report
    # What one area lacks and another has is still listed for the area that lacks it.
    assert f"| {THREE} | feature/air_no2 | below_threshold | yes |" in report


# A measure that is left out


def test_a_measure_that_is_not_what_core_says_it_is_is_left_out_and_said(
    tmp_path: Path, capsys: Printed
):
    """It is worked out, and it is left out, because its name is not the one core gives.

    What a park offers is counted within a straight line where core says a walk, and the
    two measures of town centres are not what core's names say. Each is worked out, and it
    is left out. So are the pubs, which a check of their figures holds back.
    """
    found = made(tmp_path)
    assert found.run() == 0
    said, words = lines_of(capsys)
    skipped = [line for line in said if " status=skipped " in line]
    assert skipped == [
        f"step=derive status=skipped feature={feature} source={SAID_WITH[feature]} "
        f"{RULE_OF[feature]}=1"
        for feature in LEFT_OUT
    ]
    for feature in LEFT_OUT:
        assert f"{feature} is left out of the release" in words
    left_out = read(found.beside / "build.json")["measures_left_out"]
    assert [(one["feature_id"], one["rule"]) for one in left_out] == [
        (feature, RULE_OF[feature]) for feature in LEFT_OUT
    ]


def test_the_build_and_the_coverage_report_say_what_each_measure_left_out_waits_on(build: Made):
    """A reader of the report finds why a measure is not on the map, and whose it is to settle."""
    left_out = read(build.beside / "build.json")["measures_left_out"]
    assert [one["feature_id"] for one in left_out] == list(LEFT_OUT)
    report = (build.beside / "coverage.md").read_text(encoding="utf-8")
    section = report.split("## Worked out and left out")[1].split("## Gaps")[0]
    gaps = report.split("## Gaps")[1].split("## Claims")[0]
    for one in left_out:
        assert one["waits_on"] and all(said.endswith(".") for said in one["waits_on"])
        row = f"| feature/{one['feature_id']} | {RULE_OF[one['feature_id']]} | "
        assert section.count(row) == 1
        assert all(said in section for said in one["waits_on"])
        (line,) = [line for line in gaps.splitlines() if f"| feature/{one['feature_id']} |" in line]
        assert "Worked out, and left out of the release" in line
    # What no step works out is still said so.
    assert "| travel/pt | not_carried | yes | This build does not work the measure out |" in gaps


def test_a_measure_that_is_carried_waits_on_nothing_and_one_that_is_not_says_what():
    for measure in MEASURES:
        # A measure with no file, or with no figure, waits on nothing but that.
        kept_out = measure.feature in (*NOT_AS_CORE_SAYS, *HELD_BACK)
        assert bool(measure.waits_on) is kept_out, measure.feature
        assert bool(measure.held_back) is (measure.feature in HELD_BACK), measure.feature
        for said in (*measure.held_back, *measure.waits_on):
            assert said.endswith(".") and "!" not in said and "\n" not in said and "|" not in said


# A measure that a check of its figures holds back


# What a test says holds a measure back, for as long as the test runs.
FOUND_BY_A_CHECK = ("A check found that the figure follows something else.",)


def test_no_measure_of_a_build_is_held_back_today():
    """The pubs were, while the food register was the one source of them. Private outdoor
    space was, for want of a row of the proxy audit, until the audit was dropped on
    2026-09-25."""
    assert [measure.feature for measure in MEASURES if measure.held_back] == list(HELD_BACK)


def test_a_measure_that_is_held_back_is_left_out_whatever_core_says_of_it(
    tmp_path: Path, capsys: Printed
):
    """Core names the water as the measure does, and held back it stays out all the same.

    Nothing but the hold keeps it out then, and no vibe moves: the water is a part of none.
    What holds it back is said before anything else it waits on.
    """
    found = made(tmp_path)
    water = FeatureId.WATER_ACCESS
    with held_back_for_a_while(water, FOUND_BY_A_CHECK):
        assert found.run() == 0
    said, _ = lines_of(capsys)
    skipped = {line.split()[2]: line.split()[-1] for line in said if " status=skipped " in line}
    assert skipped[f"feature={water}"] == "measure_is_not_held_back=1"
    release = read_release(found.release)
    assert {metric.feature_id for metric in release.metrics} == {
        FeatureId(feature) for feature in MEASURED if feature != water
    }
    assert {tag.tag_id: tag.coverage for tag in release.tags if tag.score is not None} == PLACED
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    row = evidence.row(f"{ONE}/feature/{water}")
    assert row is not None
    assert (row.state, row.inputs, row.value) == (State.NOT_CARRIED, (), None)
    left_out = {
        one["feature_id"]: one for one in read(found.beside / "build.json")["measures_left_out"]
    }
    assert left_out[water]["rule"] == "measure_is_not_held_back"
    assert left_out[water]["waits_on"] == list(FOUND_BY_A_CHECK)
    assert left_out[water]["why"].startswith("It is held back: a check of its figures found ")
    gaps = (found.beside / "coverage.md").read_text(encoding="utf-8")
    gaps = gaps.split("## Gaps")[1].split("## Claims")[0]
    (line,) = [line for line in gaps.splitlines() if f"| feature/{water} |" in line]
    assert "[measure_is_not_held_back]" in line


def test_a_measure_is_left_out_where_its_name_is_not_cores(tmp_path: Path, capsys: Printed):
    """A build holds a measure to core's name for it, and to nothing else.

    The water is carried, because core names it as it is measured. Named a share of the
    area, as core named it once, it is left out.
    """
    found = made(tmp_path)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(water_access, "LABEL", "Share of the area within 300 m of a river or canal")
        assert found.run() == 0
    said, _ = lines_of(capsys)
    skipped = {line.split()[2]: line.split()[-1] for line in said if " status=skipped " in line}
    assert skipped["feature=water_access"] == "measure_is_as_core_says=1"
    release = read_release(found.release)
    assert FeatureId.WATER_ACCESS not in {metric.feature_id for metric in release.metrics}
    # The water is a part of no vibe, so no vibe moves.
    assert {tag.tag_id: tag.coverage for tag in release.tags if tag.score is not None} == PLACED


def test_the_places_to_eat_and_drink_are_carried_both_ways_and_no_vibe_is_scored_from_the_count(
    tmp_path: Path, capsys: Printed
):
    """The hold on the count was lifted when core came to say what was decided.

    A build carries the count and the places for each 1,000 homes, and the check of the
    release finds nothing. The count is shown and no area is ranked on it. No vibe is
    scored from the count alone: no recipe of core's gives it 60 in 100. So the vibes
    that are placed are those the build places without it. The pubs and bars are counted
    from the file of places, which the made-up build does not hold, so they stay out.
    """
    found = made(tmp_path)
    assert found.run() == 0
    said, _ = lines_of(capsys)
    carried = [line.split()[2] for line in said if line.startswith("step=derive status=ok")]
    assert "feature=venue_food_drink" in carried and "feature=venue_evening" not in carried
    assert "feature=venue_food_drink_per_homes" in carried
    assert " findings=0 " in said[-2]
    release = read_release(found.release)
    held = {metric.feature_id: metric for metric in release.metrics}
    assert FeatureId.VENUE_EVENING not in held
    count, rate = (
        held[FeatureId.VENUE_FOOD_DRINK],
        held[FeatureId.VENUE_FOOD_DRINK_PER_HOMES],
    )
    assert (count.unit, count.rankable) == ("count", False)
    assert (rate.unit, rate.rankable) == ("per 1,000 homes", True)
    assert count.vintage == rate.vintage and count.source_ids == rate.source_ids
    nothing = default_spec(Tenure.RENT).replace(weights=())
    for metric, problems in ((count, ["not_in_release"]), (rate, [])):
        alone = FeatureWeight(
            feature_id=metric.feature_id,
            weight=0.5,
            direction=Direction.MORE,
            provenance=Provenance.UI_EDIT,
        )
        asked = check_spec(nothing.replace(weights=(alone,)), release)
        assert [one.problem for one in asked] == problems
    assert {tag.tag_id: tag.coverage for tag in release.tags if tag.score is not None} == PLACED
    assert {tag.coverage for tag in release.tags if str(tag.tag_id) == "foodie"} == {0.4}
    # Every figure of each has its row, which rests on the file of every authority.
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    for feature in (FeatureId.VENUE_FOOD_DRINK, FeatureId.VENUE_FOOD_DRINK_PER_HOMES):
        row, figure = evidence.row(f"{ONE}/feature/{feature}"), release.feature(ONE, feature)
        assert row is not None and row.has_a_value
        assert figure is not None and figure.value == row.value


def test_a_measure_whose_file_has_no_receipt_is_left_out_and_never_filled_in(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path, without_a_receipt=["homes-by-kind", "noise"])
    assert found.run() == 0
    said, words = lines_of(capsys)
    assert f" inputs={FILES - 2} missing=2 " in said[0]
    skipped = [line.split()[2:] for line in said if " status=skipped " in line]
    # Each with its source and the rule that keeps it out, in the order of the ids.
    left_out = {
        **{
            feature: (SOURCE_OF[feature], "measure_is_as_core_says") for feature in NOT_AS_CORE_SAYS
        },
        **{feature: (PLACES, NO_RECEIPT) for feature in (*BRANDS, *CULTURE, *VENUES, *FOOD_SHOP)},
        **{feature: (PRACTICES, NO_RECEIPT) for feature in SURGERY},
        **{feature: (PHARMACIES, NO_RECEIPT) for feature in PHARMACY},
        "homes_flats": ("voa-council-tax-stock-of-properties", NO_RECEIPT),
        **{feature: (POLICE, NO_RECEIPT) for feature in INCIDENTS},
        "noise_exposure": (WORKBOOK, NO_RECEIPT),
        "play_space_proximity": ("os-open-greenspace", "measure_has_a_figure"),
        **{feature: (PRICES, NO_RECEIPT) for feature in OF_PRICES},
        **{feature: (OUTDOOR, NO_RECEIPT) for feature in OUTDOOR_SPACE},
        **{feature: (HIGH_STREETS, NO_RECEIPT) for feature in HIGH_STREET},
        # Four read the national file of stops, which the made-up build does not hold.
        **{feature: ("dft-naptan", NO_RECEIPT) for feature in STOPS_NEARBY},
        "bus_routes_nearby": ("tfl-bus-stops-and-routes", NO_RECEIPT),
        # The four shares of who lived in an area: the made-up build takes no census table.
        **{feature: (CENSUS, NO_RECEIPT) for feature in (*HOUSEHOLDS, *RESIDENTS)},
    }
    assert skipped == [
        [f"feature={feature}", f"source={source}", f"{rule}=1"]
        for feature, (source, rule) in sorted(left_out.items())
    ]
    assert "homes-by-kind of the list has no receipt" in words
    release = read_release(found.release)
    assert FeatureId.HOMES_FLATS not in {metric.feature_id for metric in release.metrics}
    assert release.feature(ONE, FeatureId.HOMES_FLATS) is None
    evidence = Evidence.model_validate_json((found.beside / "evidence.json").read_bytes())
    row = evidence.row(f"{ONE}/feature/homes_flats")
    assert row is not None and (row.state, row.inputs) == (State.NOT_CARRIED, ())
    lock = Lock.model_validate_json((found.beside / "lock.json").read_bytes())
    assert not lock.holds(files()["homes-by-kind"].receipt().file_id)
    record = read(found.beside / "build.json")
    assert [one["item"] for one in record["files_of_the_list_with_no_receipt"]] == [
        "homes-by-kind",
        "noise",
    ]


def test_with_no_measure_at_all_there_is_no_release(tmp_path: Path, capsys: Printed):
    found = made(
        tmp_path,
        without_a_receipt=[
            "homes-by-band",
            "homes-by-kind",
            "homes-by-period",
            "grid",
            "land-use",
            "noise",
            *SQUARES,
            "roads",
            "traffic",
            "schools",
            "stops",
            "town-centres",
            "water",
            *REGISTERS,
            *HERITAGE,
        ],
    )
    assert found.run() == 2
    said, words = lines_of(capsys)
    assert said[-1] == "step=assemble status=unreadable"
    assert "no measure could be worked out" in words
    assert not found.out.exists()


# What stops the build


def test_a_file_the_geography_needs_with_no_receipt_stops_the_build(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path, without_a_receipt=["lookup"])
    assert found.run() == 2
    said, _ = lines_of(capsys)
    assert said[-1] == "step=assemble status=refused input_has_one_receipt=1"
    assert not found.out.exists()


def test_a_file_changed_in_the_store_after_it_was_fetched_stops_the_build(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    kept = found.store / files()["homes-by-kind"].receipt().vault_key()
    kept.write_bytes(kept.read_bytes() + b"made up")
    assert found.run() == 2
    said, _ = lines_of(capsys)
    assert said[-1].startswith("step=assemble status=refused file_is_in_the_vault=1 file_id=f-")
    assert not found.out.exists()


def test_a_file_that_is_not_laid_out_as_its_step_reads_it_stops_the_build(
    tmp_path: Path, capsys: Printed
):
    broken = replace(
        files()["grid"], content=grid.grid_csv(notes=("pm25", "2024", "annual mean", "ug m-3"))
    )
    found = made(tmp_path, changed={"grid": broken})
    assert found.run() == 2
    said, words = lines_of(capsys)
    assert said[-1].startswith("step=assemble status=refused input_is_as_described=1 file_id=f-")
    assert "it is not a map of nitrogen dioxide" in words
    assert not found.out.exists()


def with_no_use_for_a_name(found: Made, tmp_path: Path) -> list[str]:
    """A build whose registry reads a source for scoring, and names no area by it."""
    narrowed = tmp_path / "registry"
    narrowed.mkdir()
    for path in REGISTRY.glob("*.toml"):
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            'uses = ["cells", "gazetteer", "scoring"]', 'uses = ["cells", "scoring"]'
        )
        (narrowed / path.name).write_text(text, encoding="utf-8")
    arguments = found.arguments()
    arguments[arguments.index("--registry") + 1] = str(narrowed)
    return arguments


def test_the_gate_is_asked_again_about_every_file_a_row_rests_on(tmp_path: Path, capsys: Printed):
    """A source that is read for scoring may still not name an area: the use differs."""
    # With no file of stops the build names no place, and asks nothing of the centres
    # but for scoring. What names an area is then found by the check alone.
    found = made(tmp_path, without_a_receipt=["stops"])
    arguments = with_no_use_for_a_name(found, tmp_path)
    assert assemble.main(arguments, {FOLDER_VARIABLE: str(found.store)}) == 1
    said, words = lines_of(capsys)
    # The name and the outline of each of the three areas rest on a file that may name none.
    assert said[-1].startswith("step=check status=failed ")
    assert said[-1].endswith(" input_is_allowed=6")
    assert "6 facts may not be served, so nothing was written" in words
    assert not found.release.exists()


def test_the_gate_is_asked_again_about_every_source_the_release_cites(
    tmp_path: Path, capsys: Printed, monkeypatch: pytest.MonkeyPatch
):
    """The writer asks too, of the sources a release names, were the check to find nothing."""
    found = made(tmp_path, without_a_receipt=["stops"])
    arguments = with_no_use_for_a_name(found, tmp_path)

    def finds_nothing(*_: object, **__: object) -> tuple[()]:
        return ()

    monkeypatch.setattr(assemble, "unevidenced", finds_nothing)
    assert assemble.main(arguments, {FOLDER_VARIABLE: str(found.store)}) == 2
    said, words = lines_of(capsys)
    assert said[-1] == "step=assemble status=unreadable"
    assert "neighbourhoods.json" in words and "gazetteer" in words
    assert not found.release.exists()


def test_where_the_homes_of_an_area_stand_is_read_only_where_the_gate_allows_it(
    tmp_path: Path, capsys: Printed
):
    """The centres of output areas are put to the naming of places, and the gate is asked."""
    found = made(tmp_path)
    arguments = with_no_use_for_a_name(found, tmp_path)
    assert assemble.main(arguments, {FOLDER_VARIABLE: str(found.store)}) == 2
    said, words = lines_of(capsys)
    assert said[-1] == "step=assemble status=refused gate_refuses=1"
    assert "gazetteer" in words and not found.release.exists()


# The places to reach


def test_a_build_that_reads_the_stops_names_each_station_and_says_where_homes_stand(
    build: Made,
):
    release = read_release(build.release)
    assert [(place.name, place.kind.value) for place in release.places] == [
        ("Pellam Cross Station", "station"),
        ("Sable Reach Tram Stop", "station"),
        ("Tallowgate", "station"),
    ]
    for place in release.places:
        # A station stands in for itself, and the journeys to it end at it.
        assert place.coarse_place_id == place.place_id
        assert place.destination_id == place.place_id.replace("-p", "-d", 1)
        assert place.source_id == "dft-naptan"
    assert {d.destination_id: d.centroid for d in release.destinations} == {
        place.destination_id: place.centroid for place in release.places
    }
    # A person types the name alone, or the name and "station".
    assert "Pellam Cross" in release.places[0].aliases
    assert "Tallowgate station" in release.places[2].aliases
    # Where the homes of an area stand is the middle of the centres of its output areas.
    assert all(area.homes_at is not None for area in release.neighbourhoods)
    assert "ons-oa-pwc-2021" in release.origin(Part.NEIGHBOURHOODS).source_ids
    # And no journey time is held: a journey is estimated for a search, and is in no file.
    assert release.manifest.preview and release.travel_table.pt_typical == ((), (), ())


def test_the_name_of_an_area_rests_on_the_centres_where_its_homes_are_placed(build: Made):
    evidence = Evidence.model_validate_json((build.beside / "evidence.json").read_bytes())
    row = evidence.row(f"{ONE}/area/name")
    assert row is not None
    sources = {receipt.source_id for receipt in map(evidence.receipt, row.inputs) if receipt}
    assert "ons-oa-pwc-2021" in sources
    # No journey is carried: what is said of one is estimated for a search.
    for mode in Mode:
        journeys = evidence.row(f"{ONE}/travel/{mode.value}")
        assert journeys is not None and journeys.state is State.NOT_CARRIED


def test_a_build_with_no_file_of_stops_names_no_place_and_goes_on(tmp_path: Path, capsys: Printed):
    found = made(tmp_path, without_a_receipt=["stops"])
    assert found.run() == 0
    said, words = lines_of(capsys)
    assert "step=places status=skipped source=dft-naptan input_has_one_receipt=1" in said
    assert "no place to reach is named in the release" in words
    release = read_release(found.release)
    assert (release.places, release.destinations) == ((), ())
    # And it says of no area where its homes stand: nothing could be estimated from it.
    assert all(area.homes_at is None for area in release.neighbourhoods)
    assert "ons-oa-pwc-2021" not in release.origin(Part.NEIGHBOURHOODS).source_ids
    record = read(found.beside / "build.json")
    assert record["places"]["places"] == 0
    assert record["places"]["left_out"]["rule"] == "input_has_one_receipt"


def test_the_record_of_a_build_counts_the_places_and_names_none(build: Made):
    record = read(build.beside / "build.json")
    assert record["places"] == {
        "source_id": "dft-naptan",
        "places": 3,
        "areas_with_homes_placed": 3,
        "left_out": None,
        "journeys": "No journey time is held. A journey by public transport to a place is "
        "estimated for a search, from distance, and is said to be an estimate.",
    }


def test_a_source_says_whether_its_publisher_asks_for_its_statement_beside_every_figure():
    """The registry says which publisher asks that. A release carries it of each source."""
    registry = load(REGISTRY)
    stations = stations_receipt(b"made up")
    stops = stops_receipt(b"made up too")
    credited = {source.source_id: source for source in sources_of(registry, [stations, stops])}
    assert credited["tfl-step-free-station-topology"].credit_beside_figures is True
    assert credited["tfl-step-free-station-topology"].attribution.startswith("Powered by TfL")
    assert credited["dft-naptan"].credit_beside_figures is False


def test_a_source_carries_what_its_terms_ask_to_be_said_with_its_credit():
    """The London Datastore asks whoever re-uses its data to state that the Greater London
    Authority cannot warrant the quality or accuracy of the data. The registry holds the
    statement with each of the authority's two sources, and a release that rests on either
    carries it with the credit. One that rests on neither says nothing of it."""
    registry = load(REGISTRY)
    stops = stops_receipt(b"made up too")
    centres = stops.model_copy(update={"source_id": "gla-town-centre-boundaries"})
    streets = stops.model_copy(update={"source_id": HIGH_STREETS})
    asked = "The Greater London Authority cannot warrant the quality or accuracy of the data."

    credited = {s.source_id: s for s in sources_of(registry, [stops, centres, streets])}

    for source_id in ("gla-town-centre-boundaries", HIGH_STREETS):
        assert credited[source_id].said_with_attribution == asked
        # The credit is the publisher's own words, and holds none of the statement.
        assert credited[source_id].attribution == registry.get(source_id).attribution
        assert "warrant" not in credited[source_id].attribution
    assert credited["dft-naptan"].said_with_attribution is None
    [neither] = sources_of(registry, [stops])
    assert neither.said_with_attribution is None
    # What a release is written with says it of the two, and holds no word of it for the rest.
    written = {s.source_id: s.model_dump(mode="json") for s in credited.values()}
    assert {k for k, v in written.items() if v["said_with_attribution"]} == {
        "gla-town-centre-boundaries",
        HIGH_STREETS,
    }


# The receipts of the list


def pm25() -> File:
    """The second file of the source of the air, which another list names."""
    content = grid.grid_csv(notes=("pm25", "2024", "annual mean", "ug m-3"))
    return replace(files()["grid"], item="grid-pm25", name="mappm252024g.csv", content=content)


def test_a_receipt_of_another_list_is_left_alone(tmp_path: Path, capsys: Printed):
    found = made(tmp_path, unlisted=[pm25()])
    assert found.run() == 0
    lock = Lock.model_validate_json((found.beside / "lock.json").read_bytes())
    assert len(lock.inputs) == FILES and not lock.holds(pm25().receipt().file_id)


def in_two_lists(
    found: Made, *, second: bool = True, turned: bool = False, out: Path | None = None
) -> list[str]:
    """The arguments of the step, with the files of the build named in two lists.

    The first holds what a first build reads. The second holds the sites, the
    roads, the schools, the stops, the town centres, the water and the two
    files of heritage, as the lists of the real files do. With `second` false
    the step is given the first alone. With `turned` the second is given first.
    """
    every = list(files().values())
    later = [file for file in every if file.item in LATER]
    lists = {"first": [file for file in every if file not in later], "second": later}
    for name, listed in lists.items():
        (found.folder / f"{name}.toml").write_text(list_of(listed), encoding="utf-8")
    arguments = found.arguments(out=out)
    at = arguments.index("--list")
    names = ("first", "second") if second else ("first",)
    given = [
        word
        for name in (names[::-1] if turned else names)
        for word in ("--list", str(found.folder / f"{name}.toml"))
    ]
    return [*arguments[:at], *given, *arguments[at + 2 :]]


def test_a_build_takes_the_files_of_more_than_one_list(tmp_path: Path, capsys: Printed):
    found = made(tmp_path)
    assert assemble.main(in_two_lists(found), {FOLDER_VARIABLE: str(found.store)}) == 0
    said, _ = lines_of(capsys)
    assert f" inputs={FILES} missing=0 " in said[0]
    record = read(found.beside / "build.json")
    assert record["list"] == "first+second"
    assert [one["feature_id"] for one in record["measures_carried"]] == list(MEASURED)
    lock = Lock.model_validate_json((found.beside / "lock.json").read_bytes())
    assert all(lock.holds(file.receipt().file_id) for file in files().values())


def test_the_order_the_lists_are_given_in_changes_nothing_that_is_written(
    tmp_path: Path, capsys: Printed
):
    """The record of the build held the lists as they were typed. It was the one file to differ."""
    found = made(tmp_path)
    store = {FOLDER_VARIABLE: str(found.store)}
    assert assemble.main(in_two_lists(found), store) == 0
    again = in_two_lists(found, turned=True, out=tmp_path / "turned")
    assert assemble.main(again, store) == 0
    assert held(tmp_path / "turned") == held(found.out)
    assert read(found.beside / "build.json")["list"] == "first+second"


def test_the_order_of_the_lists_changes_nothing_where_a_file_of_each_has_no_receipt(
    tmp_path: Path, capsys: Printed
):
    """The record of the build named the files with no receipt in the order of the lists."""
    found = made(tmp_path, without_a_receipt=["noise", "water"])
    store = {FOLDER_VARIABLE: str(found.store)}
    assert assemble.main(in_two_lists(found), store) == 0
    again = in_two_lists(found, turned=True, out=tmp_path / "turned")
    assert assemble.main(again, store) == 0
    assert held(tmp_path / "turned") == held(found.out)
    record = read(found.beside / "build.json")
    assert [one["item"] for one in record["files_of_the_list_with_no_receipt"]] == [
        "noise",
        "water",
    ]


def test_a_file_that_is_in_no_list_of_the_build_is_no_part_of_it(tmp_path: Path, capsys: Printed):
    """Its receipt is in the folder, and the build was not given its list. It is left alone."""
    found = made(tmp_path)
    arguments = in_two_lists(found, second=False)
    assert assemble.main(arguments, {FOLDER_VARIABLE: str(found.store)}) == 0
    said, _ = lines_of(capsys)
    assert f" inputs={FILES - len(LATER)} missing=0 " in said[0]
    skipped = [line.split()[2:] for line in said if " status=skipped " in line]
    # The register is of the first list, so what is counted from it is worked out.
    of_the_register = {feature for feature in SOURCE_OF if SOURCE_OF[feature] == REGISTER}
    for feature in sorted(set(SOURCE_OF) - of_the_register):
        assert [f"feature={feature}", f"source={SOURCE_OF[feature]}", f"{NO_RECEIPT}=1"] in skipped
    lock = Lock.model_validate_json((found.beside / "lock.json").read_bytes())
    assert not any(lock.holds(files()[item].receipt().file_id) for item in LATER)
    release = read_release(found.release)
    assert FeatureId.GREEN_COVER not in {metric.feature_id for metric in release.metrics}
    # Leafy is placed on gardens and woodland alone, 70 in 100 of its recipe.
    placed = {tag.tag_id: tag.coverage for tag in release.tags if tag.score is not None}
    assert placed == {HOMES: 0.75, LEAFY: 0.7}


def test_two_lists_that_name_a_file_alike_are_refused(tmp_path: Path, capsys: Printed):
    found = made(tmp_path)
    arguments = [*found.arguments(), "--list", str(found.folder / "made-up.toml")]
    assert assemble.main(arguments, {FOLDER_VARIABLE: str(found.store)}) == 2
    said, words = lines_of(capsys)
    assert said == ["step=assemble status=unreadable"]
    assert "two lists of the build name a file alike" in words
    assert not found.out.exists()


def test_the_receipts_of_a_list_are_told_apart_by_address_and_then_counted(tmp_path: Path):
    (tmp_path / "made-up.toml").write_text(list_of(list(files().values())), encoding="utf-8")
    listed = load_list(tmp_path / "made-up.toml").files
    receipts = [file.receipt() for file in files().values()]
    other = pm25().receipt()
    found, with_one, without = of_the_list([*receipts, other], listed)
    assert [receipt.file_id for receipt in found] == [receipt.file_id for receipt in receipts]
    assert ([file.item for file in with_one], without) == ([file.item for file in listed], [])
    # A publisher that hands a download on leaves another address in the receipt.
    moved = [receipt.model_copy(update={"url": f"{receipt.url}/moved"}) for receipt in receipts]
    found, _, without = of_the_list(moved, listed)
    assert (len(found), without) == (FILES, [])
    # Then nothing tells two files of one source, edition and period apart.
    with pytest.raises(LockError) as refused:
        of_the_list([*moved, other], listed)
    assert refused.value.rule == "listed_file_has_one_receipt"
