"""The preview of the second build, built from the files their publishers gave.

Every other test of the step runs on a made-up town. These build the release
from the real files, and are skipped where the store of fetched files is not. The store is named
by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts and a few figures, so that a publisher's file that changes
is noticed. A figure here is London's lowest, middle or highest. None is said
of a named area or of a named borough. Each was worked out on 2026-09-24, and
no person has checked one.

The build takes two lists: the files of the first build, and the places of the
second, which hold the sites of green space, the roads, the water, the town
centres, the conservation areas, the listed buildings and the food register.
What is worked out and left out of the release has no figure held here: the
tests of each measure hold its own. Credits for the figures held here, in
the words of the licence registry: © Crown 2026 copyright Defra via
uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL). Contains
public sector information licensed under the Open Government Licence v3.0.
Source: Office for National Statistics licensed under the Open Government
Licence v.3.0. Contains OS data © Crown copyright and database right [year].
Contains OS data © Crown copyright and database right 2026. © Historic England
2026. Contains Ordnance Survey data © Crown copyright and database right 2026.
The Historic England GIS Data contained in this material was obtained on
2026-09-24. The most publicly available up to date Historic England GIS Data
can be obtained from HistoricEngland.org.uk.

Nothing is written to the store. What is built is written to a folder of the
test's own, which is thrown away.
"""

import json
import os
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import tags_of as vibes_of
from burro_core.facts import facts_for
from burro_core.ids import FeatureId, GrittyVariant, Part, TagId
from burro_core.release import InMemoryRelease
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.evidence.lock import Lock
from burro_pipeline.evidence.served import rows_behind, unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FOLDER_VARIABLE
from burro_pipeline.release.read import read_release
from public_log import is_public

from ..cells.support import REPOSITORY, held, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)

RELEASE = "lon-2026-09-23-01"
LISTS = ("m1", "m2-places")
# No commit of any repository: the tests may be run in a working copy with changes.
COMMIT = "0" * 40
# What each measure came to on 2026-09-24: the lowest, the middle and the highest area.
# They are in the order a build works them out in, which is the order of their ids.
FIGURES = {
    FeatureId.AIR_NO2: (8.8, 17.4, 32.7),
    FeatureId.CONSERVATION_COVER: (0.0, 7.8, 100.0),
    FeatureId.GREEN_COVER: (0.0, 3.3, 78.1),
    FeatureId.HIGHSTREET_ACCESS: (0.0, 530.0, 2_770.0),
    FeatureId.HOMES_DENSITY: (1.3, 32.2, 154.8),
    FeatureId.HOMES_FLATS: (1.7, 53.5, 99.0),
    FeatureId.HOMES_POST2000: (0.4, 10.6, 100.0),
    FeatureId.HOMES_PRE1919: (0.0, 23.4, 97.2),
    FeatureId.LISTED_BUILDINGS: (0.0, 3.9, 414.3),
    FeatureId.NOISE_EXPOSURE: (15.1, 50.5, 100.0),
    FeatureId.PARK_LARGE_PROXIMITY: (120.0, 1_030.0, 4_290.0),
    FeatureId.PARK_PROXIMITY: (110.0, 450.0, 2_020.0),
    FeatureId.PLAY_SPACE_PROXIMITY: (60.0, 300.0, 1_110.0),
    FeatureId.ROAD_MAJOR_EXPOSURE: (0.0, 23.4, 91.2),
    FeatureId.WATER_ACCESS: (0.0, 2.8, 100.0),
}
# What each measure of the food register came to: the lowest, the middle, and the figure
# that nine areas in ten do not pass. The highest is not held: one area of London is a
# borough on its own, and it leads both, so its figure would be the figure of a named place.
TO_THE_NINTH = {
    FeatureId.VENUE_FOOD_DRINK: (3.1, 51.5, 163.2),
    FeatureId.VENUE_FOOD_DRINK_PER_HOMES: (1.2, 8.2, 15.9),
}
# Every measure a build carries, in the order of their ids.
CARRIED = tuple(sorted((*FIGURES, *TO_THE_NINTH)))
# How many areas have a figure. 23 areas have old homes that are all behind a dash, and 3
# have new homes that are: they are not nought, and the publisher does not say how many
# they are.
WITH_A_FIGURE = {
    FeatureId.AIR_NO2: 1_002,
    FeatureId.CONSERVATION_COVER: 1_002,
    FeatureId.GREEN_COVER: 1_002,
    # 26 areas at the edge of London stand nearer to homes outside it than to any centre.
    FeatureId.HIGHSTREET_ACCESS: 976,
    FeatureId.HOMES_DENSITY: 1_002,
    FeatureId.HOMES_FLATS: 1_002,
    FeatureId.HOMES_POST2000: 999,
    FeatureId.HOMES_PRE1919: 979,
    FeatureId.LISTED_BUILDINGS: 1_002,
    FeatureId.NOISE_EXPOSURE: 1_002,
    FeatureId.PARK_LARGE_PROXIMITY: 1_002,
    FeatureId.PARK_PROXIMITY: 1_002,
    FeatureId.PLAY_SPACE_PROXIMITY: 1_002,
    FeatureId.ROAD_MAJOR_EXPOSURE: 1_002,
    # Ten areas at the edge of London have homes outside it within reach, and no figure.
    FeatureId.VENUE_FOOD_DRINK: 992,
    FeatureId.VENUE_FOOD_DRINK_PER_HOMES: 992,
    FeatureId.WATER_ACCESS: 1_002,
}
# What is left out, and the rule that keeps each out, in the order of the ids. A measure
# whose file is on no list of this build is read from no file here: the table of land use
# and the file of places are each in a list of their own, and the police's crime files, the
# register of schools and the file of stops are on the list m2-living, as is the workbook of
# what homes sell for. The tests of each such measure work it out from the real file. The
# pubs are worked out, and a check of their figures holds them back. The others are worked
# out, and keep a name of core's that their figure does not bear out: the size and the shape
# of a town centre, whose figures are held in
# `tests/derive/test_centres_on_the_real_files.py`, and what a park offers.
NO_FILE, NOT_AS_CORE_SAYS = "input_has_one_receipt", "measure_is_as_core_says"
HELD_BACK = "measure_is_not_held_back"
LEFT_OUT = {
    "centre_compact": NOT_AS_CORE_SAYS,
    "centre_small": NOT_AS_CORE_SAYS,
    "culture_venues": NO_FILE,
    "culture_venues_per_homes": NO_FILE,
    "incident_antisocial": NO_FILE,
    "incident_criminal_damage": NO_FILE,
    "land_gardens": NO_FILE,
    "land_industry": NO_FILE,
    "land_storage": NO_FILE,
    "land_transport_other": NO_FILE,
    "land_woodland": NO_FILE,
    "park_facilities": NOT_AS_CORE_SAYS,
    "price_median": NO_FILE,
    "school_primary_nearby": NO_FILE,
    "station_walk": NO_FILE,
    "venue_evening": HELD_BACK,
}
# The vibes that have 60 in 100 of their recipe measured, the share each rests on where an
# area has every part, and the areas each places. Built age rests on homes built before 1919,
# homes built since 2000, conservation cover and listed buildings. Going out rests on the
# places to eat and drink for each 1,000 homes and the nearest town centre, and Family
# amenities on the nearest play space and the nearest park: this build reads no school.
PLACED = {
    TagId.BUILT_AGE: 1.0,
    TagId.FAMILY_AMENITIES: 0.6,
    TagId.HOMES: 0.75,
    TagId.PACE: 0.75,
    TagId.PARKS_CLOSE_BY: 0.7,
    TagId.QUIET_RESIDENTIAL: 0.7,
}
AREAS_PLACED = {
    TagId.BUILT_AGE: 1_001,
    TagId.FAMILY_AMENITIES: 1_002,
    TagId.HOMES: 1_002,
    TagId.PACE: 971,
    TagId.PARKS_CLOSE_BY: 1_002,
    TagId.QUIET_RESIDENTIAL: 1_002,
}
# How much of a vibe each area rests on, where areas differ. Of Built age, an area with no
# figure for homes built since 2000 has 80 in 100, and one with none for homes built before
# 1919 has 65: each is placed. The one area with neither has 45 in 100, and is not. Of Going
# out, an area at the edge of London may lack the places to eat, the town centre or both.
RESTS_ON = {
    TagId.BUILT_AGE: {1.0: 977, 0.8: 2, 0.65: 22, 0.45: 1},
    TagId.PACE: {0.75: 971, 0.45: 21, 0.3: 5, 0.0: 5},
}
ENOUGH = 0.6


def build(folder: Path, out: str) -> tuple[int, list[str]]:
    """Run the step as a person runs it, and give back what it printed for anyone to read."""
    (folder / "no-repository").mkdir(exist_ok=True)
    (folder / "printed").mkdir(exist_ok=True)
    arguments = [
        "preview",
        *("--release-id", RELEASE),
        *("--built-at", "2026-09-23T00:00:00Z"),
        *("--out", str(folder / out)),
        *(word for name in LISTS for word in ("--list", name)),
        *("--receipts", str(RECEIPTS)),
        *("--root", str(folder / "no-repository")),
        *("--commit", COMMIT),
        *("--work", str(folder / "copies")),
    ]
    printed = folder / "printed" / out
    with printed.open("w", encoding="utf-8") as said, pytest.MonkeyPatch.context() as patch:
        patch.setattr("sys.stdout", said)
        status = assemble.main(arguments, {FOLDER_VARIABLE: STORE})
    return status, printed.read_text(encoding="utf-8").splitlines()


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, list[str]]:
    folder = tmp_path_factory.mktemp("preview")
    status, said = build(folder, "out")
    assert status == 0, said
    return folder, said


@pytest.fixture(scope="module")
def release(built: tuple[Path, list[str]]) -> InMemoryRelease:
    return read_release(built[0] / "out" / RELEASE)


def beside(built: tuple[Path, list[str]], name: str) -> Any:
    return json.loads((built[0] / "out" / f"{RELEASE}-build" / name).read_bytes())


def test_the_step_counts_london_as_the_files_hold_it(built: tuple[Path, list[str]]):
    said = built[1]
    assert all(is_public(line) for line in said)
    assert said[1] == (
        f"step=cells status=ok release={RELEASE} areas=1002 output_areas=26369 lsoas=4994 "
        "msoas=1002 boroughs=33 files=4"
    )
    carried = [line.split()[2:] for line in said if line.startswith("step=derive status=ok")]
    assert [words[0] for words in carried] == [f"feature={feature}" for feature in CARRIED]
    assert [words[-3:-1] for words in carried] == [
        ["areas=1002", f"values={count}"] for count in WITH_A_FIGURE.values()
    ]
    assert " findings=0 " in said[-2]


def test_the_release_is_real_and_is_a_preview(release: InMemoryRelease):
    manifest = release.manifest
    assert (manifest.synthetic, manifest.preview, manifest.city) == (False, True, "lon")
    counts = manifest.counts
    assert (counts.neighbourhoods, counts.rankable) == (1_002, 1_002)
    assert (counts.destinations, counts.places, counts.stations) == (0, 0, 0)
    assert len({area.borough for area in release.neighbourhoods}) == 33
    assert not release.origin(Part.TRAVEL).stated and not release.origin(Part.STATIONS).stated


def test_what_is_left_out_is_left_out_by_the_name_of_a_rule_and_the_build_says_why(
    built: tuple[Path, list[str]],
):
    """The size and the shape of a town centre count only the homes with a centre within
    800 metres. The pubs are held back by what a check of their figures found.
    """
    record = beside(built, "build.json")
    assert record["list"] == "+".join(LISTS)
    left_out = record["measures_left_out"]
    assert {one["feature_id"]: one["rule"] for one in left_out} == LEFT_OUT
    assert [one["feature_id"] for one in left_out] == list(LEFT_OUT)
    report = (built[0] / "out" / f"{RELEASE}-build" / "coverage.md").read_text(encoding="utf-8")
    section = report.split("## Worked out and left out")[1].split("## Gaps")[0]
    for one in left_out:
        assert f"| feature/{one['feature_id']} | {one['rule']} | " in section
        assert all(said in section for said in one["waits_on"])


def test_the_vibes_that_have_a_score_are_these_and_no_other_has(release: InMemoryRelease):
    """Flats and homes per hectare are 75 in 100 of Homes, so core places every area on it.

    The nearest park and the nearest large park are 70 in 100 of Parks close
    by, and main roads and transport noise are 70 in 100 of Quiet streets.
    Each rests on two of its three parts, and its sentence says so.

    Homes built before 1919, homes built since 2000, conservation cover and
    listed buildings are the whole of Built age, so core places every area
    that has 60 in 100 of them. The one area with no figure for the age of
    its homes has 45 in 100, and is not placed. Conservation cover is 15 in
    100 of Village feel, which places no area: with old homes it has 35 in 100.

    The places to eat and drink for each 1,000 homes and the nearest town
    centre are 75 in 100 of Going out, and the nearest play space and the
    nearest park are 60 in 100 of Family amenities. Each places the areas
    that have both.

    No other vibe has 60 in 100 of its recipe measured, so no other has a
    band. Food and drink holds the places for each 1,000 homes at 40. Main
    roads and transport noise are 25 in 100 of Gritty, and no land use and no
    recorded incident is read. Public parks and gardens are 30 in 100 of
    Leafy.
    """
    assert release.manifest.gritty_variant is GrittyVariant.B
    assert release.vibes == vibes_of(GrittyVariant.B)
    assert len(release.vibes) == 11
    assert len(release.tags) == 11 * 1_002
    placed = Counter(tag.tag_id for tag in release.tags if tag.score is not None)
    assert placed == AREAS_PLACED
    for vibe, share in PLACED.items():
        of_the_vibe = [tag for tag in release.tags if tag.tag_id is vibe]
        shares = Counter(tag.coverage for tag in of_the_vibe)
        scored = {tag.coverage for tag in of_the_vibe if tag.score is not None}
        if vibe in RESTS_ON:
            assert shares == RESTS_ON[vibe] and max(shares) == share
            assert scored == {held for held in RESTS_ON[vibe] if held >= ENOUGH}
        else:
            assert set(shares) == scored == {share}
    others = [tag for tag in release.tags if tag.tag_id not in PLACED]
    assert all((tag.raw, tag.score, tag.band) == (None, None, None) for tag in others)
    most = {tag.tag_id: max(t.coverage for t in others if t.tag_id is tag.tag_id) for tag in others}
    assert max(most.values()) == most[TagId.FOODIE] == 0.4
    assert (most[TagId.STREET_CHARACTER], most[TagId.LEAFY]) == (0.25, 0.3)
    assert TagId.WORKS_WAREHOUSES not in {tag.tag_id for tag in release.tags}
    village = {tag.coverage for tag in release.tags if tag.tag_id is TagId.VILLAGE_FEEL}
    assert village == {0.35, 0.15}


def test_what_is_left_out_has_a_row_that_says_so_and_rests_on_no_file(
    built: tuple[Path, list[str]],
):
    evidence = beside(built, "evidence.json")
    for feature in LEFT_OUT:
        rows = [row for row in evidence["rows"] if row["fact_id"].endswith(f"/feature/{feature}")]
        assert len(rows) == 1_002
        assert {(row["state"], len(row["inputs"]), row["value"]) for row in rows} == {
            ("not_carried", 0, None)
        }


@pytest.mark.parametrize("feature", list(TO_THE_NINTH))
def test_a_measure_of_the_food_register_comes_to_what_it_came_to(
    release: InMemoryRelease, feature: FeatureId
):
    rows = [release.feature(area.area_id, feature) for area in release.neighbourhoods]
    values = sorted(row.value for row in rows if row is not None and row.value is not None)
    assert len(values) == WITH_A_FIGURE[feature]
    found = (values[0], round(statistics.median(values), 2), values[(9 * len(values)) // 10])
    assert found == TO_THE_NINTH[feature]


def test_the_count_is_shown_and_a_wish_is_ranked_on_the_places_for_each_1000_homes(
    release: InMemoryRelease,
):
    held = {metric.feature_id: metric for metric in release.metrics}
    count, rate = held[FeatureId.VENUE_FOOD_DRINK], held[FeatureId.VENUE_FOOD_DRINK_PER_HOMES]
    assert (count.unit, count.rankable) == ("count", False)
    assert (rate.unit, rate.rankable) == ("per 1,000 homes", True)
    assert count.vintage == rate.vintage == "2026-09-09 to 2026-09-16"
    assert FeatureId.VENUE_EVENING not in held


@pytest.mark.parametrize("feature", list(FIGURES))
def test_a_measure_comes_to_what_it_came_to(release: InMemoryRelease, feature: FeatureId):
    rows = [release.feature(area.area_id, feature) for area in release.neighbourhoods]
    values = sorted(row.value for row in rows if row is not None and row.value is not None)
    assert len(values) == WITH_A_FIGURE[feature]
    found = (values[0], round(statistics.median(values), 1), values[-1])
    assert found == FIGURES[feature]


def test_every_fact_traces_to_a_row_a_file_and_a_receipt(
    built: tuple[Path, list[str]], release: InMemoryRelease
):
    folder = built[0] / "out" / f"{RELEASE}-build"
    evidence = Evidence.model_validate_json((folder / "evidence.json").read_bytes())
    lock = Lock.model_validate_json((folder / "lock.json").read_bytes())
    assert unevidenced(release, evidence, lock, registry()) == ()
    facts = [f for area in release.neighbourhoods for f in facts_for(release, area.area_id, None)]
    # A label for every area, and a fact for every figure. A fact for every vibe, placed or
    # not. And five areas alike for every area: likeness may count on homes built before
    # 1919, conservation cover, listed buildings, public parks and gardens, the distances to
    # a park, to a play space and to a town centre, and the count of places to eat.
    assert Counter(fact.kind for fact in facts) == {
        "area": 1_002,
        "feature": sum(WITH_A_FIGURE.values()),
        "tag": 11 * 1_002,
        "likeness": 5 * 1_002,
    }
    for fact in facts:
        rows = [evidence.row(row_id) for row_id in rows_behind(release, fact.fact_id)]
        assert rows, fact.fact_id
        cited: set[str] = set()
        for row in rows:
            assert row is not None and row.has_a_value
            assert all(lock.holds(file_id) for file_id in row.inputs)
            cited |= evidence.sources_of(row)
        assert {source.source_id for source in fact.sources} <= cited
    for receipt in evidence.receipts:
        assert (Path(STORE) / receipt.vault_key()).stat().st_size == receipt.bytes
        assert (RECEIPTS / receipt.source_id / f"{receipt.file_id}.json").is_file()


def test_built_twice_from_the_same_files_it_writes_the_same_bytes(built: tuple[Path, list[str]]):
    folder, said = built
    status, again = build(folder, "again")
    assert status == 0
    assert again == said
    assert held(folder / "again") == held(folder / "out")
