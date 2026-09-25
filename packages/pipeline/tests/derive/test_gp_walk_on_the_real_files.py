"""The nearest GP practice, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up report. These read the real
report, the real postcode directory and the real centres of output areas, and
are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the report, what became of the practices that count,
the count of areas with a figure, and three figures: London's lowest, middle
and highest. None is said of a named area or of a borough, and no postcode
and no name is held. Each was worked out on 2026-09-24, from the report as it
was fetched that day.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, postcodes, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import gp_walk, nearest_by_postcode
from burro_pipeline.derive.gp_walk import Report, Walk
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.nearest_by_postcode import Placing
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The report, by the id of its receipt.
REPORT = "f-13acc2be00fb"


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
def report(real: Inputs) -> Report:
    return gp_walk.read(real.open(gp_walk.SOURCE, gp_walk.USE, named=gp_walk.is_the_report))


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Walk:
    return gp_walk.build(real, found)


# The report


def test_the_report_is_the_one_that_was_fetched_and_its_receipt_says_so(real: Inputs):
    receipt = real.open(gp_walk.SOURCE, gp_walk.USE, named=gp_walk.is_the_report).receipt
    assert (receipt.file_id, receipt.publisher_file) == (REPORT, "epraccur.csv")
    assert (receipt.how, receipt.edition) == (How.FETCHED, "retrieved 2026-09-24")
    assert receipt.data_period == Period(as_at="2026-09-24")


def test_the_step_reads_the_report_to_its_end(report: Report):
    """It stopped at the first line that says inactive, and at the first cell of two settings."""
    assert report.rows == 15_651
    assert report.by_status == {"active": 12_591, "dormant": 252, "inactive": 2_808}


def test_a_practice_that_is_not_active_is_left_out_and_counted(report: Report):
    """8,187 lines hold the setting of a GP practice alone, and 6 hold it beside another."""
    assert (report.of_a_gp_practice, report.of_several_settings) == (8_193, 6)
    assert report.left_out == {"dormant": 62, "inactive": 1_568}
    assert len(report.postcodes) == 6_563
    assert report.of_a_gp_practice == len(report.postcodes) + sum(report.left_out.values())


def test_what_is_printed_of_the_report_is_counts(report: Report):
    assert repr(report) == "Report(rows=15651, counted=6563)"


# The figure


def test_1145_practices_are_placed_in_london_and_the_rest_are_placed_nowhere(made: Walk):
    """The directory holds London's rows alone, so a practice elsewhere is placed nowhere."""
    assert made.placing == Placing(
        listed=6_563,
        placed=1_145,
        at_an_ended_postcode=1,
        not_a_postcode=0,
        not_of_london=5_418,
        too_coarse=0,
    )


def test_994_of_the_1002_areas_have_a_figure(made: Walk, found: Spine):
    assert len(made.worked) == len(found.areas) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {
        State.PRESENT: 947,
        State.PARTIAL: 47,
        State.BELOW_THRESHOLD: 8,
    }


def test_the_lowest_the_middle_and_the_highest_of_london(made: Walk):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (200.0, 400.0, 1_700.0)
    assert all(value % nearest_by_postcode.NEAREST == 0 for value in values)
    assert len(set(values)) == 15


def test_the_distance_of_26011_output_areas_is_known(made: Walk, found: Spine):
    assert len(found.cells) == 26_369
    assert (len(made.distances.of_oa), len(made.distances.near_the_edge)) == (26_011, 358)
    known = sorted(made.distances.of_oa.values())
    assert (round(known[0]), round(statistics.median(known)), round(known[-1])) == (0, 415, 3_187)


# The edge of London


def test_the_edge_leaves_8_areas_of_5_boroughs_with_no_figure(made: Walk, found: Spine):
    """A practice outside London is placed nowhere, so a home near the edge has no distance."""
    assert sum(found.homes[oa] for oa in made.distances.near_the_edge) == 46_456
    borough = {area.area_id: area.borough for area in found.areas}
    without = [area for area, one in made.worked.items() if one.value is None]
    assert (len(without), len({borough[area] for area in without})) == (8, 5)
    touched = {found.area_of[oa] for oa in made.distances.near_the_edge}
    assert set(without) <= touched


# The evidence, and the row of the catalogue


def test_a_row_names_the_files_behind_it_and_holds_the_figure(made: Walk):
    by_source = {receipt.source_id: receipt.file_id for receipt in made.files}
    assert set(by_source) == {
        gp_walk.SOURCE,
        postcodes.SOURCE,
        centres.CENTRES,
        spine.LOOKUP,
        spine.HOMES,
    }
    assert by_source[gp_walk.SOURCE] == REPORT
    ids = tuple(sorted(by_source.values()))
    assert all(row.inputs == ids for row in made.rows)
    assert [row.value for row in made.rows] == [
        made.worked[row.fact_id.split("/")[0]].value for row in made.rows
    ]
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=gp_walk.METHODS,
        receipts=made.files,
        rows=made.rows,
    )
    assert len(evidence.rows) == 1_002


def test_the_row_of_the_catalogue_is_cores_and_says_when_the_report_was_made(made: Walk):
    assert says_what_core_says(made.metric)
    assert (made.metric.unit, made.metric.vintage) == ("m", "2026-09-24")
    assert "lists as active, as at 2026-09-24" in made.metric.definition


def test_nothing_was_written_to_the_store(made: Walk, before: dict[str, tuple[int, int]]):
    assert made.worked and listing() == before
