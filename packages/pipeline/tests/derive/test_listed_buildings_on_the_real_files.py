"""Listed buildings, worked out from the files their publishers gave.

Every other test of the measure runs on made-up entries. These read the real
file, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the file, the count of areas with a figure, and three
figures: London's lowest, middle and highest. None is said of a named area or
of a named authority, and no entry of the list is named. Each was worked out
on 2026-09-24, by a program.

© Historic England 2026. Contains Ordnance Survey data © Crown copyright and
database right 2026. The Historic England GIS Data contained in this material
was obtained on 2026-09-24. The most publicly available up to date Historic
England GIS Data can be obtained from HistoricEngland.org.uk. Source: Office
for National Statistics licensed under the Open Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import listed_buildings
from burro_pipeline.derive.listed_buildings import Counted, Listed
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The file of listed buildings, by the id of its receipt, and the edition it was kept under.
ENTRIES, EDITION = "f-3d843cc2d377", "retrieved 2026-09-24"
# The boundaries of LSOAs, the lookup and the table of homes.
BOUNDARIES, LOOKUP, HOMES = "f-9f549e33f46b", "f-49321b95f212", "f-af7b512615ea"


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
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def measured(real: Inputs, found: Spine) -> Land:
    return land.build(real, found)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine, measured: Land) -> Listed:
    return listed_buildings.build(real, found, measured, edition=EDITION)


# The file


def test_every_record_of_the_file_is_counted_once(made: Listed):
    assert made.counted == Counted(
        in_the_file=381_754,
        in_the_box=24_743,
        nowhere=0,
        ended=207,
        not_points=0,
        in_no_area=5_316,
        placed=19_220,
        by_grade={"I": 602, "II": 17_186, "II*": 1_432},
    )


def test_every_live_entry_is_a_point_and_has_a_grade(made: Listed):
    assert made.counted.not_points == 0
    assert "" not in made.counted.by_grade
    assert sum(made.counted.by_grade.values()) == made.counted.placed


def test_nine_entries_in_ten_are_of_the_lowest_grade(made: Listed):
    assert round(100 * made.counted.by_grade["II"] / made.counted.placed) == 89


# Coverage


def test_the_file_holds_an_entry_in_every_one_of_the_33_authorities(made: Listed):
    assert len(made.of_authority) == 33
    counts = sorted(made.of_authority.values())
    assert (counts[0], statistics.median(counts), counts[-1]) == (44, 308, 3_993)
    assert sum(counts) == 19_220


# The figures


def test_every_area_has_a_figure_and_is_wholly_covered(made: Listed):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Listed):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (0.0, 3.9, 414.3)


def test_one_area_in_eight_holds_no_entry_at_all(made: Listed):
    assert sum(one.value == 0 for one in made.worked.values()) == 125


def test_the_other_reading_for_each_thousand_homes_is_what_was_worked_out(
    made: Listed, found: Spine
):
    """It joins no release. It is held here so that the two readings can be compared."""
    other = listed_buildings.for_each_thousand_homes(made.entries, found)
    values = sorted(one.value for one in other.values() if one.value is not None)
    assert len(values) == 1_002
    assert (values[0], statistics.median(values), values[-1]) == (0.0, 1.45, 302.4)


# The evidence


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_design(made: Listed):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {
        tuple(sorted([ENTRIES, BOUNDARIES, LOOKUP, HOMES]))
    }
    assert {row.derivation_id for row in made.rows} == {"lsoa_ratio_by_homes@1"}
    # From the day of the census, which the weights are of, to the day of the file.
    span = Period(start="2021-03-21", end="2026-09-24")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-24"}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    assert Evidence.of("lon-2026-10-09-01", made.files, listed_buildings.METHODS, made.rows)


def test_the_row_of_the_catalogue_is_cores_and_names_every_source(made: Listed):
    assert says_what_core_says(made.metric)
    assert made.metric.vintage == "2026-09-24"
    assert made.metric.source_ids == (
        "historic-england-listed-buildings",
        "ons-census-2021-housing-tables",
        "ons-lsoa-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Listed, before: dict[str, tuple[int, int]]
):
    copies = sorted(path for path in real.work.rglob("*") if path.is_file())
    assert sorted(path.relative_to(real.work).parts[0] for path in copies) == sorted(
        [ENTRIES, BOUNDARIES, LOOKUP, HOMES]
    )
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
