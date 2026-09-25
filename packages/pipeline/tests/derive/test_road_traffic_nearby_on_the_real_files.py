"""The traffic near where homes stand, on the real files.

These read the files of the store through their receipts, and are skipped
where the store of fetched files is not, and where the file of count points
has no receipt in `data/receipts/`. The store is named by BURRO_STORE_FOLDER.

What they hold of the file is what its publisher's page says of it: how many
rows it holds, of how many count points, and of which years. What they hold of
the figures is how many output areas and how many areas have one, and the
lowest, the middle and the highest of the build. None is said of a named road,
of a named area or of a borough. Each was worked out on 2026-09-25, by a
program, from the flows as the publisher's file held them when it was retrieved
that day. No person has checked one.

Contains public sector information licensed under the Open Government Licence
v3.0. The Department for Transport says its estimates of traffic for a road
link are less robust than its figures for a region, because they are not
always based on up-to-date counts made at the place. Source: Office for
National Statistics licensed under the Open Government Licence v.3.0. Contains
OS data © Crown copyright and database right 2026.

Nothing is written to the store. A file is copied out of it to be read.
"""

import math
import os
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.centres import Point
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import road_major_exposure, road_traffic_nearby
from burro_pipeline.derive.road_traffic_nearby import Count, Traffic
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import HAS_A_VALUE, State
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and (RECEIPTS / road_traffic_nearby.SOURCE).is_dir()),
    reason="the count points cannot be read here: the store is not named, or the file has "
    "no receipt",
)
# What the publisher's page says the file holds, and what it was counted to hold.
ROWS_ON_THE_PAGE, COUNT_POINTS = 600_551, 46_754
YEARS = (2000, 2025)
# Of the count points of the whole file: how many were last given a figure in the last year,
# and how many of all the latest figures were counted.
OF_THE_LAST_YEAR, COUNTED = 22_334, 25_810
AREAS, OUTPUT_AREAS = 1_002, 26_369
# How many output areas have a count point within 500 metres of their centre, and the homes
# they hold in 100 of the homes of the build.
WITH_A_COUNT_POINT, HOMES_IN_100 = 22_848, 86.9
# The count points that are the busiest near some home: how many, how many of them were
# counted and how many estimated, and how many are of the last year.
BEHIND = {"count points": 2_555, "counted": 1_414, "estimated": 1_141, "of the last year": 1_466}
# On which category of road they stand.
ON = {"PA": 1_380, "MCU": 946, "MB": 208, "TM": 19, "TA": 2}
# The lowest, the middle and the highest flow near the homes of an output area.
NEAR_HOMES = (49, 16_116, 156_491)
# The figure: how many areas have one, and the lowest, the middle and the highest.
FIGURES = (943, 478.0, 16_915.0, 101_407.0)
STATES = {
    State.PRESENT: 398,
    State.PARTIAL: 545,
    State.BELOW_THRESHOLD: 58,
    State.SOURCE_GAP: 1,
}
# What the choice of 500 metres rests on. The middle link of a major road near the homes of
# the build, in kilometres. And of the homes that stand within 100 metres of a main road,
# how many in 100 have a count point of a major road within 300, 500 and 800 metres.
MIDDLE_LINK_KM = 0.8
BESIDE_A_MAIN_ROAD = {300: 62.3, 500: 83.8, 800: 95.7}
# How many areas have a figure at 300 metres, and at 800.
AT_OTHER_DISTANCES = {300: 578, 800: 1_000}


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def counts(real: Inputs) -> dict[str, Count]:
    return road_traffic_nearby.read(real.open(road_traffic_nearby.SOURCE, Use.SCORING))


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Traffic:
    return road_traffic_nearby.build(real, found)


def test_the_file_holds_the_count_points_its_page_says_and_a_figure_of_every_year(
    real: Inputs, counts: dict[str, Count]
):
    opened = real.open(road_traffic_nearby.SOURCE, Use.SCORING)
    assert opened.receipt.data_period == Period(start=str(YEARS[0]), end=str(YEARS[1]))
    with opened.text(road_traffic_nearby.TABLE) as text:
        years = Counter(row["year"] for row in opened.rows(text, ("year",)))
    assert sum(years.values()) == ROWS_ON_THE_PAGE
    assert sorted(years) == [str(year) for year in range(YEARS[0], YEARS[1] + 1)]
    assert len(counts) == COUNT_POINTS


def test_a_count_point_is_read_at_its_latest_year_which_for_half_is_not_the_last(
    counts: dict[str, Count],
):
    latest = Counter(one.year for one in counts.values())
    assert latest[YEARS[1]] == OF_THE_LAST_YEAR
    assert min(latest) == YEARS[0]
    assert sum(one.counted for one in counts.values()) == COUNTED


def test_how_many_homes_have_a_count_point_near_them(made: Traffic, found: Spine):
    assert (len(made.worked), len(found.area_of)) == (AREAS, OUTPUT_AREAS)
    assert len(made.near) == WITH_A_COUNT_POINT
    near = sum(found.homes[oa] for oa in made.near)
    assert round(100 * near / sum(found.homes.values()), 1) == HOMES_IN_100
    flows = sorted(one.flow for one in made.near.values())
    assert (flows[0], statistics.median(flows), flows[-1]) == NEAR_HOMES


def test_how_many_count_points_stand_behind_the_figures_and_how_each_was_made(made: Traffic):
    assert {
        "count points": len(made.behind),
        "counted": made.counted,
        "estimated": made.estimated,
        "of the last year": sum(one.year == YEARS[1] for one in made.behind.values()),
    } == BEHIND
    assert dict(Counter(one.category for one in made.behind.values())) == ON
    assert made.read_of == Period(start=str(YEARS[0]), end=str(YEARS[1]))
    assert made.metric.vintage == "2000 to 2025"
    assert "of the 2,555 count points behind the figures" in made.metric.definition
    assert "1,414 were counted" in made.metric.definition


def test_how_many_areas_have_a_figure_and_what_it_is_across_the_build(made: Traffic):
    assert dict(Counter(one.state for one in made.worked.values())) == STATES
    have = sorted(
        one.value
        for one in made.worked.values()
        if one.state in HAS_A_VALUE and one.value is not None
    )
    assert (len(have), have[0], statistics.median(have), have[-1]) == FIGURES


def test_every_area_has_a_row_of_evidence_that_names_the_files_behind_it(made: Traffic):
    assert len(made.rows) == AREAS
    behind = tuple(sorted(receipt.file_id for receipt in made.files))
    assert len(behind) == 4
    for row in made.rows:
        assert row.inputs == behind
        assert row.value == made.worked[row.fact_id.split("/")[0]].value


def _with_one_within(points: dict[str, Point], counts: list[Point], metres: int) -> frozenset[str]:
    """The points that have a count point within so many metres, in a straight line."""
    held: dict[tuple[int, int], list[Point]] = {}
    for at in counts:
        held.setdefault((math.floor(at[0] / metres), math.floor(at[1] / metres)), []).append(at)
    return frozenset(
        name
        for name, (east, north) in points.items()
        if any(
            (at[0] - east) ** 2 + (at[1] - north) ** 2 <= metres * metres
            for across in (-1, 0, 1)
            for up in (-1, 0, 1)
            for at in held.get(
                (math.floor(east / metres) + across, math.floor(north / metres) + up), ()
            )
        )
    )


def test_what_the_choice_of_500_metres_rests_on(real: Inputs, found: Spine, made: Traffic):
    """The first lines of the module say why 500 metres. Each figure they give is held here."""
    points = centres.build(real, found)
    east, north = [at[0] for at in points.values()], [at[1] for at in points.values()]
    opened = real.open(road_traffic_nearby.SOURCE, Use.SCORING)
    read = ("count_point_id", "year", "road_type", "easting", "northing", "link_length_km")
    latest: dict[str, dict[str, str]] = {}
    with opened.text(road_traffic_nearby.TABLE) as text:
        for row in opened.rows(text, read):
            held = latest.get(row["count_point_id"])
            if held is None or int(row["year"]) > int(held["year"]):
                latest[row["count_point_id"]] = row
    major = [
        (float(row["easting"]), float(row["northing"]), float(row["link_length_km"]))
        for row in latest.values()
        if row["road_type"] == "Major"
        and min(east) - 2_000 <= float(row["easting"]) <= max(east) + 2_000
        and min(north) - 2_000 <= float(row["northing"]) <= max(north) + 2_000
    ]
    assert statistics.median(length for _, _, length in major) == MIDDLE_LINK_KM
    beside = {oa for oa, near in road_major_exposure.build(real, found).near.items() if near}
    homes = sum(found.homes[oa] for oa in beside)
    standing = {oa: points[oa] for oa in beside}
    for metres, in_100 in BESIDE_A_MAIN_ROAD.items():
        within = _with_one_within(standing, [(e, n) for e, n, _ in major], metres)
        assert round(100 * sum(found.homes[oa] for oa in within) / homes, 1) == in_100
    counts = road_traffic_nearby.read(opened)
    for metres, areas in AT_OTHER_DISTANCES.items():
        near = road_traffic_nearby.near(points, counts, metres)
        worked = road_traffic_nearby.figures(
            {oa: float(one.flow) for oa, one in near.items()}, found
        )
        assert sum(one.value is not None for one in worked.values()) == areas
    assert sum(one.value is not None for one in made.worked.values()) == FIGURES[0]


def test_nothing_was_written_to_the_store(made: Traffic, before: dict[str, tuple[int, int]]):
    assert made.worked
    assert listing() == before
