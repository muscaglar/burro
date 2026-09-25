"""The traffic near where homes stand, for each area.

Every file here is made up: `traffic_support.py` writes the count points, and
the tests of cells draw the town they stand on, which `culture_support.py`
spreads out. The centres stand 1,000 metres apart, so every distance can be
worked out by hand.

    Quillhaven 001   Q1  a count point 100 metres off reads 12,000, and one 300 off 15,000
                     Q2  one count point, 400 metres off: 7,000
                     Q3  one count point, last given a figure in 2010: 4,000
                     Q4  no count point, so no figure
    Quillhaven 002   R1  one count point: 30,000. R2, R3 and R4 have none
    Tallowgate 001   none
"""

from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NUISANCES, TRAFFIC_WITHIN_M
from burro_core.ids import FeatureId, Method, NativeResolution, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import measures, road_traffic_nearby
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.road_traffic_nearby import Count, Near, Traffic
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, EAST, NORTH, held, registry
from .culture_support import OAS, ONE, Q1, Q2, Q3, Q4, R1, THREE, TWO, beside, centres_at
from .traffic_support import (
    BY_Q1,
    COLUMNS,
    COUNTS,
    ELSEWHERE,
    ESTIMATED,
    NORTH_OF_Q1,
    SOURCE,
    SOUTH_OF_Q3,
    WEST_OF_Q2,
    MadeUpCount,
    counts_zip,
    inputs_of,
)

OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1 = OAS[4]
NOT_KNOWN = Worked(None, 0, 4, 0.0, State.SOURCE_GAP)


def built(inputs: Inputs) -> Traffic:
    return road_traffic_nearby.build(inputs, spine.build(inputs))


def of(folder: Path, rows: list[MadeUpCount]) -> Traffic:
    """The measure on the town, with the count points given and one far off of the last year."""
    return built(inputs_of(folder, counts_zip([*rows, ELSEWHERE])))


def refused(folder: Path, rows: list[MadeUpCount]) -> LockError:
    with pytest.raises(LockError) as stopped:
        of(folder, rows)
    return stopped.value


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Traffic:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


# The traffic near a home


def test_a_home_is_given_the_busiest_count_point_within_500_metres(town: Traffic):
    assert town.near == {
        OA_Q1: Near(15_000, 2024, "2", True, "PA", 2),
        OA_Q2: Near(7_000, 2025, "3", True, "PA", 1),
        OA_Q3: Near(4_000, 2010, "4", True, "MCU", 1),
        OA_R1: Near(30_000, 2025, "5", False, "TM", 1),
    }
    assert road_traffic_nearby.METRES == TRAFFIC_WITHIN_M == 500


def test_a_home_with_no_count_point_near_it_has_no_figure_and_never_nought(town: Traffic):
    """Nobody counted the traffic near Q4. It is not known to be quiet."""
    assert OA_Q4 not in town.near
    assert town.worked[THREE] == NOT_KNOWN
    assert all(one.value != 0 for one in town.worked.values())


def test_no_figure_is_not_a_figure_of_nought(tmp_path: Path):
    """A bridge that is closed reads nought, which is a figure. A street nobody counted
    reads nothing."""
    closed = [MadeUpCount(11 + n, 2025, beside(at, 50), 0) for n, at in enumerate((Q1, Q2, Q3, Q4))]
    found = of(tmp_path, closed)
    assert found.worked[ONE] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    assert found.worked[TWO] == found.worked[THREE] == NOT_KNOWN


def test_a_count_point_is_read_at_the_latest_year_it_has_and_at_no_other(tmp_path: Path):
    """The count point by Q1 read 20,000 in 2019 and 12,000 in 2023. It reads 12,000."""
    earlier = [replace(BY_Q1[0], flow=20_000), BY_Q1[1]]
    assert of(tmp_path, earlier).near[OA_Q1] == Near(12_000, 2023, "1", False, "PA", 1)


def test_a_figure_of_years_ago_is_given_with_the_year_it_is_of(town: Traffic):
    """The count point by Q3 left the sample after 2010. Its figure is of 2010 and says so."""
    assert (town.near[OA_Q3].flow, town.near[OA_Q3].year) == (4_000, 2010)
    assert town.read_of == Period(start="2010", end="2025")
    assert town.metric.vintage == "2010 to 2025"


def test_a_count_point_counts_at_500_metres_and_not_a_metre_further(tmp_path: Path):
    at_the_reach = MadeUpCount(7, 2025, beside(Q4, 300, 400), 9_000)
    assert of(tmp_path / "at", [at_the_reach]).near[OA_Q4].flow == 9_000
    past_it = replace(at_the_reach, at=beside(Q4, 300, 401))
    assert OA_Q4 not in of(tmp_path / "past", [past_it]).near


def test_the_flows_of_two_count_points_are_never_added_together(town: Traffic):
    assert town.near[OA_Q1].points == 2
    assert town.near[OA_Q1].flow == 15_000 != 12_000 + 15_000


def test_a_count_point_near_two_homes_counts_for_each(tmp_path: Path):
    """Q1 and Q2 stand 1,000 metres apart. A count point midway is 500 metres from each."""
    between = MadeUpCount(7, 2025, beside(Q1, 500), 7_500)
    found = of(tmp_path, [between])
    assert found.near == {
        OA_Q1: Near(7_500, 2025, "7", True, "PA", 1),
        OA_Q2: Near(7_500, 2025, "7", True, "PA", 1),
    }
    assert set(found.behind) == {"7"}


def test_of_two_count_points_with_one_flow_the_one_whose_id_sorts_first_is_named(
    tmp_path: Path,
):
    same = [
        MadeUpCount(9, 2025, beside(Q1, 60), 8_000),
        MadeUpCount(10, 2024, beside(Q1, 80), 8_000, ESTIMATED),
    ]
    assert of(tmp_path / "one", same).near[OA_Q1] == Near(8_000, 2024, "10", False, "PA", 2)
    assert of(tmp_path / "two", same[::-1]).near[OA_Q1].point == "10"


def test_a_figure_says_whether_it_was_counted_or_estimated(town: Traffic):
    """Four count points stand behind the figures: by Q1, Q2 and Q3 counted, by R1 estimated."""
    assert set(town.behind) == {"2", "3", "4", "5"}
    assert (town.counted, town.estimated) == (3, 1)
    said = town.metric.definition
    assert "of the 4 count points behind the figures of this release 3 were counted" in said
    assert "and 1 were estimated by the publisher" in said


def test_a_count_point_beyond_the_edge_of_the_build_counts_where_it_is_near_a_home(
    tmp_path: Path,
):
    """The file is of Great Britain. A count point counts by where it stands, and the town
    ends at Q1: 400 metres to the west of it no home of the build stands."""
    beyond = MadeUpCount(7, 2025, beside(Q1, -400), 22_000)
    assert of(tmp_path, [beyond]).near == {OA_Q1: Near(22_000, 2025, "7", True, "PA", 1)}


def test_nothing_that_names_a_region_or_an_authority_is_read():
    named = {"region_id", "region_name", "region_ons_code"}
    named |= {"local_authority_id", "local_authority_name", "local_authority_code"}
    assert not named & set(road_traffic_nearby.READ)
    assert named <= set(COLUMNS)


# The figure of an area


def test_an_area_is_given_the_mean_over_its_homes(town: Traffic):
    """The homes of Q4 have no figure. They are 140 of the 500 of Quillhaven 001."""
    assert pytest.approx(8_361.11, abs=0.01) == (110 * 15_000 + 120 * 7_000 + 130 * 4_000) / 360
    assert town.worked == {
        ONE: Worked(8_361.0, 3, 4, 0.72, State.PARTIAL),
        TWO: Worked(None, 1, 4, 0.227273, State.BELOW_THRESHOLD),
        THREE: NOT_KNOWN,
    }


def test_below_half_the_homes_with_a_figure_no_figure_is_given(tmp_path: Path):
    """The homes of Q3 and Q4 are 270 of the 500 of Quillhaven 001, and those of Q1 and
    Q2 are 230, which is under half."""
    found = of(tmp_path / "most", [SOUTH_OF_Q3, MadeUpCount(7, 2025, beside(Q4, 10), 6_000)])
    assert pytest.approx(5_037.04, abs=0.01) == (130 * 4_000 + 140 * 6_000) / 270
    assert found.worked[ONE] == Worked(5_037.0, 2, 4, 0.54, State.PARTIAL)
    found = of(tmp_path / "few", [NORTH_OF_Q1, WEST_OF_Q2])
    assert found.worked[ONE] == Worked(None, 2, 4, 0.46, State.BELOW_THRESHOLD)


def test_a_figure_is_given_to_the_whole_vehicle_with_a_half_taken_upward(tmp_path: Path):
    found = spine.build(inputs_of(tmp_path))
    every = dict.fromkeys(OAS[:4], 0.0) | {OA_Q3: 25.0}
    assert 130 * 25 / 500 == 6.5
    assert road_traffic_nearby.figures(every, found)[ONE].value == 7.0
    assert road_traffic_nearby.DECIMALS == 0


def test_the_order_of_the_rows_changes_nothing(tmp_path: Path, town: Traffic):
    turned = built(inputs_of(tmp_path, counts_zip(COUNTS[::-1])))
    assert turned.worked == town.worked and turned.near == town.near
    assert turned.behind == town.behind and turned.metric == town.metric


def test_an_output_area_with_no_centre_adds_nothing(tmp_path: Path):
    """The file of centres gives no point for Q1, so nothing is known of its homes."""
    found = built(inputs_of(tmp_path, centres=centres_at(without=(OA_Q1,))))
    assert OA_Q1 not in found.near
    assert found.worked[ONE] == Worked(5_440.0, 2, 4, 0.5, State.PARTIAL)


# What the file is held to


@pytest.mark.parametrize(
    "lacks", ["count_point_id", "year", "easting", "estimation_method", "all_motor_vehicles"]
)
def test_a_file_that_lacks_a_column_that_is_read_stops_the_step(tmp_path: Path, lacks: str):
    columns = [name for name in COLUMNS if name != lacks]
    with pytest.raises(LockError) as stopped:
        built(inputs_of(tmp_path, counts_zip(columns=columns)))
    assert stopped.value.rule == "input_is_as_described"


@pytest.mark.parametrize(
    "row",
    [
        replace(NORTH_OF_Q1, year=2026),
        replace(NORTH_OF_Q1, year=1999),
        replace(NORTH_OF_Q1, flow="many"),
        replace(NORTH_OF_Q1, flow=-1),
        replace(NORTH_OF_Q1, flow="1500.5"),
        replace(NORTH_OF_Q1, how="Guessed"),
        replace(NORTH_OF_Q1, category="ZZ"),
        replace(NORTH_OF_Q1, at=(float("nan"), 0.0)),
        replace(BY_Q1[1], flow=1),
    ],
    ids=[
        "a year after the period",
        "a year before the period",
        "a flow that is no number",
        "a flow below nought",
        "a flow that is no whole number",
        "a way of estimating that is not known",
        "a category of road that is not known",
        "a place that is no place",
        "a count point with two figures of one year",
    ],
)
def test_a_row_that_is_not_as_the_publisher_describes_stops_the_step(
    tmp_path: Path, row: MadeUpCount
):
    assert refused(tmp_path, [*BY_Q1, row]).rule == "input_is_as_described"


def test_a_file_with_no_row_of_the_last_year_its_receipt_states_stops_the_step(tmp_path: Path):
    """The receipt says the file runs to 2025. A file that ends in 2024 is another file."""
    with pytest.raises(LockError) as stopped:
        built(inputs_of(tmp_path, counts_zip([*BY_Q1, NORTH_OF_Q1])))
    assert stopped.value.rule == "input_is_as_described"
    to_2024 = inputs_of(
        tmp_path / "to-2024",
        counts_zip([*BY_Q1, NORTH_OF_Q1]),
        period=Period(start="2000", end="2024"),
    )
    assert built(to_2024).near[OA_Q1].flow == 15_000


def test_a_refusal_repeats_nothing_from_the_file(tmp_path: Path):
    said = str(refused(tmp_path, [replace(NORTH_OF_Q1, flow=CANARY)]))
    assert CANARY not in said and "15000" not in said


# The gate, the receipts and the evidence


def test_the_gate_is_asked_before_a_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=Registry(sources=()))
    with pytest.raises(LockError) as stopped:
        road_traffic_nearby.build(inputs, spine.build(inputs_of(tmp_path / "spine")))
    assert stopped.value.rule == "gate_refuses"


def test_a_file_of_count_points_with_no_receipt_is_not_read(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        built(inputs_of(tmp_path, with_a_receipt=False))
    assert stopped.value.rule == "input_has_one_receipt"


def test_a_row_of_evidence_names_every_file_the_figure_rests_on(town: Traffic):
    assert sorted(receipt.source_id for receipt in town.files) == sorted(
        [SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    for receipt in town.files:
        registry().require(receipt.source_id, Use.SCORING)
    behind = tuple(sorted(receipt.file_id for receipt in town.files))
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/road_traffic_nearby" for area in (ONE, TWO, THREE)
    ]
    for row in town.rows:
        assert row.inputs == behind
        assert row.derivation_id == road_traffic_nearby.METHOD.derivation_id
        assert row.value == town.worked[row.fact_id.split("/")[0]].value


def test_a_row_of_evidence_states_the_years_of_the_figures_that_were_read(town: Traffic):
    """The file covers 2000 to 2025. The figures that were read are of 2010 to 2025."""
    assert town.read_of == Period(start="2010", end="2025")
    for row in town.rows:
        assert row.data_period is not None
        assert row.data_period.days() == ("2010-01-01", "2025-12-31")


def test_the_method_says_what_is_done(town: Traffic):
    method = road_traffic_nearby.METHOD
    assert method.kind is Kind.MODELLED
    assert method.derivation_id == "busiest_count_point_within_500m_at_homes@1"
    assert method.parameters == {"metres": 500, "enough_in_100": 50}
    assert (method,) == road_traffic_nearby.METHODS
    assert "highest" in method.sentence and "latest year" in method.sentence
    assert "500 metres" in method.sentence and "straight line" in method.sentence
    assert town.geography is Geography.POINT


def test_nothing_is_written_to_the_store_and_twice_is_the_same(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    first, second = built(inputs), built(inputs)
    assert held(tmp_path / "store") == before
    assert first.worked == second.worked and first.rows == second.rows


def test_no_name_of_a_road_is_read(town: Traffic):
    assert CANARY not in repr(town)
    assert not {"road_name", "start_junction_road_name", "end_junction_road_name"} & set(
        road_traffic_nearby.READ
    )


def test_it_reads_the_file_of_the_flow_and_no_other_of_its_source():
    assert road_traffic_nearby.is_the_file("dft_traffic_counts_aadf.zip")
    assert not road_traffic_nearby.is_the_file("dft_traffic_counts_aadf_by_direction.zip")
    assert not road_traffic_nearby.is_the_file("count_points.zip")
    assert road_traffic_nearby.SOURCE == SOURCE


def test_a_count_point_is_kept_with_where_it_stood_in_its_latest_year(tmp_path: Path):
    """A count point that was moved is read where its latest row puts it."""
    moved = [MadeUpCount(7, 2019, beside(Q1, 100), 6_000), MadeUpCount(7, 2025, R1, 6_500)]
    inputs = inputs_of(tmp_path, counts_zip(moved))
    opened = inputs.open(SOURCE, Use.SCORING)
    assert road_traffic_nearby.read(opened) == {
        "7": Count("7", 2025, (EAST + R1[0], NORTH + R1[1]), 6_500, True, "PA")
    }
    assert set(built(inputs).near) == {OA_R1}


# What core holds


def test_the_row_of_the_catalogue_is_cores_and_a_build_carries_the_measure(town: Traffic):
    metric = town.metric
    assert says_what_core_says(metric)
    core = FEATURES[FeatureId.ROAD_TRAFFIC_NEARBY]
    assert (metric.label, metric.unit) == (core.label, "motor vehicles a day")
    assert (metric.polarity, metric.native_resolution) == (Polarity.LESS, NativeResolution.POINT)
    # Its publisher gives an estimate, so the figure is carried as modelled, as core says.
    assert metric.method is Method.MODELLED is core.method
    assert FeatureId.ROAD_TRAFFIC_NEARBY in NUISANCES
    assert metric.source_ids == tuple(sorted(receipt.source_id for receipt in town.files))
    # A person may rank an area on the figure by itself.
    assert metric.rankable is True and road_traffic_nearby.RANKABLE
    on_the_list = [one for one in measures.MEASURES if one.source == SOURCE]
    assert [one.feature for one in on_the_list] == [FeatureId.ROAD_TRAFFIC_NEARBY]
    assert on_the_list[0].cannot_see == road_traffic_nearby.CANNOT_SEE
    assert not on_the_list[0].held_back and not on_the_list[0].waits_on


def test_the_sentence_of_the_measure_says_what_it_is_and_what_it_is_not(town: Traffic):
    said = town.metric.definition
    for words in (
        "500 metres",
        "straight line",
        "latest year",
        "2010 to 2025",
        "census of 2021",
        "never added together",
        "which is not a figure of nought",
        "less robust",
    ):
        assert words in said, words
    assert "{" not in said


def test_what_it_cannot_see_says_that_a_street_nobody_counted_has_no_figure():
    said = road_traffic_nearby.CANNOT_SEE
    assert len(said) == 5
    assert "sample of minor roads" in said[0] and "no figure" in said[0]
    assert "not the same as a figure of nought" in said[0]
    assert "further along it" in said[1]
    assert "a few streets away" in said[2]
    assert "less robust" in said[3] and "years" in said[3]


def test_no_word_of_the_measure_names_a_city():
    """The file is of Great Britain, and a build gives the measure its homes."""
    said = " ".join(
        (
            road_traffic_nearby.DEFINITION,
            road_traffic_nearby.METHOD.sentence,
            *road_traffic_nearby.CANNOT_SEE,
        )
    )
    assert "London" not in said and "borough" not in said.lower()
    assert "London" not in Path(road_traffic_nearby.__file__).read_text(encoding="utf-8")
