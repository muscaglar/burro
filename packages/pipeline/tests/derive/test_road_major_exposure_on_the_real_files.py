"""Main roads, worked out from the files their publishers gave.

Every other test of the measure runs on made-up roads. These read the real
ones, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts and a few figures, so that a publisher's file that changes
is noticed. A figure here is London's lowest, middle or highest, or that of all
of London. None is said of a named area. Each was worked out on 2026-09-24.

Contains OS data © Crown copyright and database right [year]. Source: Office
for National Statistics licensed under the Open Government Licence v.3.0. The
words are each publisher's own, as the licence registry holds them.

Nothing is written to the store. A file is copied out of it to be read.
"""

import math
import os
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.spine import Homes, Spine
from burro_pipeline.derive import road_major_exposure as roads
from burro_pipeline.derive.methods import homes_within
from burro_pipeline.derive.road_major_exposure import Exposure
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
# The roads, the centres, the lookup and the table of homes, by the ids of their receipts.
ROADS, CENTRES, LOOKUP, HOMES = (
    "f-908c0eda3a1b",
    "f-00e1d0532798",
    "f-49321b95f212",
    "f-af7b512615ea",
)


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
def made(real: Inputs, found: Spine) -> Exposure:
    return roads.build(real, found)


def values_of(made: Exposure) -> list[float]:
    return sorted(one.value for one in made.worked.values() if one.value is not None)


# The roads


def test_the_file_holds_as_many_roads_as_were_counted(made: Exposure):
    assert made.roads.file_id == ROADS
    assert (made.roads.edition, made.roads.indexed) == ("2026-04", True)
    # Every road of Great Britain, and those that come within 250 metres of London's homes.
    assert (made.roads.rows, len(made.roads.links)) == (3_961_077, 254_655)


def test_the_roads_round_london_are_classed_as_they_were_counted(made: Exposure):
    assert made.roads.by_class == {
        "Motorway": 454,
        "A Road": 29_533,
        "B Road": 8_731,
        "Classified Unnumbered": 11_877,
        "Unclassified": 139_038,
        "Not Classified": 21_778,
        "Unknown": 43_244,
    }
    assert sum(made.roads.by_class.values()) == len(made.roads.links)
    # 47 stretches of a main road are in a tunnel, and are left out.
    assert made.roads.in_tunnel == 47
    assert sum(link.main for link in made.roads.links) == 454 + 29_533 - 47


def test_the_lines_are_as_long_as_the_file_says_they_are(made: Exposure):
    """The publisher states a length for each road. The lines as read add up to it."""
    assert made.roads.metres_stated == 23_378_205
    assert round(made.roads.metres_drawn) == 23_379_608
    assert abs(made.roads.metres_drawn / made.roads.metres_stated - 1) < 0.0001


def test_the_file_says_it_covers_great_britain(made: Exposure):
    west, south, east, north = made.roads.covers
    assert (round(west), round(south), round(east), round(north)) == (
        9_123,
        8_046,
        655_563,
        1_216_649,
    )


# The verdicts


def test_every_output_area_of_london_has_a_verdict(made: Exposure):
    assert len(made.near) == 26_369
    assert sum(made.near.values()) == 6_666


def test_the_roads_reach_the_homes_of_london(made: Exposure):
    """One centre of 26,369 is further than 250 metres from any road of any class."""
    assert made.unreached == 1


def test_a_sample_of_verdicts_is_the_same_worked_out_another_way(
    real: Inputs, made: Exposure, found: Spine
):
    """Every main road is tried against each centre of the sample, with no grid to look in."""
    points = centres.build(real, found)
    main = [link.line for link in made.roads.links if link.main]

    def metres_to(point: tuple[float, float], line: tuple[float, ...]) -> float:
        nearest = math.inf
        for at in range(0, len(line) - 2, 2):
            ax, ay, bx, by = line[at : at + 4]
            whole = math.hypot(bx - ax, by - ay)
            along = 0.0
            if whole > 0:
                along = ((point[0] - ax) * (bx - ax) + (point[1] - ay) * (by - ay)) / whole**2
            along = min(1.0, max(0.0, along))
            nearest = min(
                nearest,
                math.hypot(point[0] - ax - along * (bx - ax), point[1] - ay - along * (by - ay)),
            )
        return nearest

    sample = sorted(points)[::2_000]
    assert len(sample) == 14
    again = {oa: min(metres_to(points[oa], line) for line in main) <= 100 for oa in sample}
    assert again == {oa: made.near[oa] for oa in sample}
    assert 0 < sum(again.values()) < len(sample)


# The figures


def test_every_area_has_a_figure_and_is_wholly_covered(made: Exposure):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}
    assert sum(one.units_used for one in made.worked.values()) == 26_369


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Exposure):
    values = values_of(made)
    # The two figures in the middle are 23.4 and 23.5.
    assert (values[0], statistics.median(values), values[-1]) == (0.0, 23.45, 91.2)


def test_no_figure_is_outside_what_a_share_can_be(made: Exposure):
    values = values_of(made)
    assert all(0 <= value <= 100 for value in values)
    # 109 areas have no output area centred near a main road, and none has every one.
    assert (values.count(0.0), values.count(100.0)) == (109, 0)


def test_the_figure_of_all_of_london_is_what_was_worked_out(made: Exposure, found: Spine):
    """The same method with London as one area: the homes near a main road, over all homes."""
    london = Homes(area_of=dict.fromkeys(found.area_of, "london"), homes=found.homes)
    whole = homes_within(made.near, london, times=100)["london"]
    assert whole.value is not None and round(whole.value, 2) == 26.15
    assert (whole.units_used, whole.weight_covered) == (26_369, 1.0)
    # 895,299 of 3,423,767 homes, as they stood at the census of 2021.
    near = sum(found.homes[oa] for oa, beside in made.near.items() if beside)
    assert (near, sum(found.homes.values())) == (895_299, 3_423_767)


# The evidence


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_distance(made: Exposure):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {tuple(sorted([ROADS, CENTRES, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"homes_within_100m@1"}
    # From the day of the census, which the weights are of, to the end of the roads' month.
    span = Period(start="2021-03-21", end="2026-04-30")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-23"}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    assert Evidence.of("lon-2026-10-02-01", made.files, roads.METHODS, made.rows)


def test_the_row_of_the_catalogue_names_the_edition_and_every_source(made: Exposure):
    assert made.metric.vintage == "2026-04"
    assert made.metric.source_ids == (
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "os-open-roads",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Exposure, before: dict[str, tuple[int, int]]
):
    copies = sorted(path for path in real.work.rglob("*") if path.is_file())
    assert sorted(path.parent.name for path in copies) == sorted([ROADS, CENTRES, LOOKUP, HOMES])
    # The GeoPackage was unpacked to be read, and the copy is gone.
    assert [path.name for path in copies if path.suffix == ".gpkg"] == []
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
