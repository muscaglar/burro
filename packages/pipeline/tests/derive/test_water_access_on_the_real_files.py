"""Water close by, worked out from the files their publishers gave.

Every other test of the measure runs on made-up water. These read the real
file, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the file, the count of areas with a figure, and three
figures: London's lowest, middle and highest. None is said of a named area or
of a borough. Each was worked out on 2026-09-24.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import water_access
from burro_pipeline.derive.water_access import Access
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
# The water, the centres, the lookup and the table of homes, by the ids of their receipts.
WATER, CENTRES, LOOKUP, HOMES = (
    "f-b31e85f9fd41",
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
def made(real: Inputs, found: Spine) -> Access:
    return water_access.build(real, found)


# The file


def test_the_file_holds_as_many_rows_as_were_counted_and_is_read_by_its_own_index(made: Access):
    assert made.rivers.file_id == WATER
    assert (made.rivers.rows, made.rivers.edition) == (193_040, "2026-04")
    assert made.rivers.indexed


def test_the_water_within_reach_of_london_is_what_was_counted(made: Access):
    assert len(made.rivers.links) == 2_747
    assert made.rivers.by_form == {
        "canal": 68,
        "inlandRiver": 2_065,
        "lake": 438,
        "tidalRiver": 176,
    }


def test_the_lines_add_up_to_what_the_file_says_they_are_long(made: Access):
    """The one total the publisher gives in the file: the length of each stretch."""
    stated, drawn = made.rivers.metres_stated, made.rivers.metres_drawn
    assert round(stated) == 2_505_993
    # The file gives a length to a whole metre, so each stretch may differ by a half.
    assert abs(drawn - stated) <= 0.5 * len(made.rivers.links)


def test_the_file_covers_every_home_of_london_and_a_line_is_within_reach_of_each(
    made: Access, found: Spine
):
    assert len(made.near) == len(made.metres) == len(found.area_of) == 26_369
    assert made.unreached == 0
    assert sum(made.near.values()) == 4_586


# The figures


def test_every_area_has_a_figure_and_is_wholly_covered(made: Access):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Access):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (0.0, 2.8, 100.0)


def test_nearly_half_the_areas_are_at_nought(made: Access):
    """The publisher draws no line within 300 metres of any centre of theirs. It is counted."""
    assert sum(one.value == 0 for one in made.worked.values()) == 494


# The evidence


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_design(made: Access):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {tuple(sorted([WATER, CENTRES, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"homes_within_300m@1"}
    # From the day of the census, which the weights are of, to the end of the water's month.
    span = Period(start="2021-03-21", end="2026-04-30")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-23"}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    assert Evidence.of("lon-2026-10-09-01", made.files, water_access.METHODS, made.rows)


def test_the_row_of_the_catalogue_names_the_month_and_every_source(made: Access):
    assert made.metric.vintage == "2026-04"
    assert made.metric.source_ids == (
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "os-open-rivers",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Access, before: dict[str, tuple[int, int]]
):
    copies = sorted(path for path in real.work.rglob("*") if path.is_file())
    assert sorted(path.relative_to(real.work).parts[0] for path in copies) == sorted(
        [WATER, CENTRES, LOOKUP, HOMES]
    )
    # The GeoPackage was unpacked to be read, and the copy is gone.
    assert not [path for path in copies if path.suffix == ".gpkg"]
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
