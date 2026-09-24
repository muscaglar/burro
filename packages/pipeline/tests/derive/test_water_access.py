"""Water close by, from the publisher's lines to a figure for each area.

Every file here is made up. `water_support.py` says how the water is laid out
and where the town's homes stand. The figures the tests hold, worked out by
hand from that:

    Quillhaven 001   60 m, 300 m, 300.5 m and 608 m from water   230 of 500 homes near
    Quillhaven 002   100 m, 200 m, 300 m and 1,000 m             480 of 660
    Tallowgate 001   50 m, 301 m, 250 m and 4,472 m              400 of 820
"""

import math
import re
from collections.abc import Callable
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, Polarity
from burro_pipeline.cells import centres, spine
from burro_pipeline.derive import measures, water_access
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.water_access import Access
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .water_support import (
    CAN_INDEX,
    CANARY,
    COVERS,
    EDITION,
    FAR_AWAY,
    FIELDS,
    NORTH_OF_THE_TOWN,
    OAS,
    PLACED,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    TALLOWGATE,
    WATER,
    Place,
    Stretch,
    inputs_of,
    line_blob,
    network,
    on,
    stretch,
    the_water,
    water_receipt,
    with_one,
    zipped,
)

needs_an_index = pytest.mark.skipif(not CAN_INDEX, reason="this SQLite cannot make an index")


def built(
    folder: Path, packed: bytes | None = None, placed: dict[str, Place] | None = None
) -> Access:
    inputs = inputs_of(folder, packed, placed)
    return water_access.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Access:
    """The town with its water, as most tests read it. It is built once."""
    return built(tmp_path_factory.mktemp("town"))


def refused(folder: Path, packed: bytes, edition: str = EDITION) -> LockError:
    """The refusal of a file, which names a rule and repeats nothing the file holds."""
    inputs = inputs_of(folder, packed, edition=edition)
    with pytest.raises(LockError) as stopped:
        water_access.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# The parser


def test_the_water_round_the_homes_is_read_each_stretch_with_its_form(town: Access):
    found = town.rivers
    assert (found.rows, len(found.links)) == (5, 4)
    assert found.by_form == {"canal": 1, "inlandRiver": 1, "lake": 1, "tidalRiver": 1}
    assert (found.edition, found.covers) == (EDITION, COVERS)
    assert found.file_id == water_receipt(the_water()).file_id


def test_every_form_the_file_names_counts_as_water(town: Access):
    assert water_access.FORMS == ("canal", "inlandRiver", "lake", "tidalRiver")
    assert sorted(link.form for link in town.rivers.links) == sorted(water_access.FORMS)


def test_water_far_from_every_home_is_not_read(town: Access):
    lines = {link.line for link in town.rivers.links}
    assert not any(northing == 500_000 for line in lines for northing in line[1::2])


@pytest.mark.parametrize("indexed", [True, False])
def test_the_form_of_water_far_from_every_home_changes_nothing(
    town: Access, tmp_path: Path, indexed: bool
):
    """A figure rests on the water that was read, and on no other row of the file."""
    far = Stretch(CANARY, FAR_AWAY.line, fictitious=CANARY, length=CANARY)
    found = built(tmp_path, zipped(network((*WATER, far), indexed=indexed and CAN_INDEX)))
    assert (found.rivers.rows, found.rivers.links) == (6, town.rivers.links)
    assert found.worked == town.worked


def test_the_lines_add_up_to_what_the_file_says_they_are_long(town: Access):
    assert town.rivers.metres_stated == 3_000 * 2 + 2_000 + 200
    assert town.rivers.metres_drawn == town.rivers.metres_stated


@needs_an_index
def test_the_same_water_is_kept_with_the_files_index_and_without_it(town: Access, tmp_path: Path):
    without = built(tmp_path, zipped(network(indexed=False)))
    assert (town.rivers.indexed, without.rivers.indexed) == (True, False)
    assert without.rivers.links == town.rivers.links
    assert (without.worked, without.metres) == (town.worked, town.metres)


@needs_an_index
def test_an_index_that_does_not_hold_every_row_is_refused(tmp_path: Path):
    stopped = refused(tmp_path, zipped(network(index_holds=3)))
    assert "its index does not hold every stretch of water" in str(stopped)


@needs_an_index
def test_a_line_the_index_gives_is_held_to_the_box_by_the_line_itself(tmp_path: Path):
    """An index holds a box a little wider than its line, so it may give a line too many."""
    # It ends three hundredths of a metre short of the box the water is read in.
    short = stretch("canal", (680_000, 400_000), (690_099.97, 400_000))
    found = built(tmp_path, with_one(short))
    assert "canal" not in {link.form for link in found.rivers.links if link.line[0] < 695_000}
    assert len(found.rivers.links) == 4


@pytest.mark.parametrize("missing", ["form", "fictitious", "length"])
def test_a_file_without_a_column_is_refused_and_the_column_is_named(tmp_path: Path, missing: str):
    fields = [(CANARY if name == missing else name, kind) for name, kind in FIELDS]
    stopped = refused(tmp_path, zipped(network(fields=fields)))
    assert f"the column {missing} is missing" in str(stopped)


@pytest.mark.parametrize(
    ("made", "words"),
    [
        (lambda: network(layer="made_up_layer"), "no layer of water on the National Grid"),
        (lambda: network(grid=4326), "no layer of water on the National Grid"),
        (lambda: network(geometry="shape"), "not lines in two dimensions"),
        (lambda: network(lines="MULTILINESTRING"), "not lines in two dimensions"),
        (lambda: network(z=1), "not lines in two dimensions"),
        (lambda: network(changed="2026-05-01T00:00:00.000Z"), "not the month of its receipt"),
        (lambda: network(changed=CANARY), "not the month of its receipt"),
        (lambda: network(covers=(None, None, None, None)), "does not say what it covers"),
        (
            lambda: network(covers=(710_000.0, 390_000.0, 690_000.0, 510_000.0)),
            "does not say what it covers",
        ),
        (lambda: network(()), "it holds no water"),
        (lambda: network((FAR_AWAY,)), "its water does not reach the homes of the build"),
    ],
    ids=[
        "another layer",
        "another grid",
        "another column of lines",
        "lines of several parts",
        "three dimensions",
        "another month",
        "no day",
        "no box",
        "a box turned round",
        "no row",
        "no row near",
    ],
)
def test_a_file_that_is_not_laid_out_as_the_publisher_lays_it_out_is_refused(
    tmp_path: Path, made: Callable[[], bytes], words: str
):
    assert words in str(refused(tmp_path, zipped(made())))


HERE = NORTH_OF_THE_TOWN


@pytest.mark.parametrize(
    ("water", "words"),
    [
        (Stretch("drain", HERE), "of a form that is not known"),
        (Stretch(CANARY, HERE), "of a form that is not known"),
        (Stretch(None, HERE), "of a form that is not known"),
        (Stretch("lake", HERE, fictitious="1"), "marked as fictitious"),
        (Stretch("lake", HERE, fictitious=1), "marked as fictitious"),
        (Stretch("lake", HERE, fictitious=CANARY), "neither there nor not there"),
        (Stretch("lake", HERE, fictitious=None), "neither there nor not there"),
        (Stretch("lake", HERE, length=-1), "a length is no length"),
        (Stretch("lake", HERE, length=CANARY), "a length is no length"),
        (Stretch("lake", HERE, length=30_000), "not as long as it says"),
        (Stretch("lake", HERE, without_a_line=True), "has no line"),
        (Stretch("lake", FAR_AWAY.line, without_a_line=True), "has no line"),
        (Stretch("lake", HERE, blob=CANARY.encode()), "not a line in two dimensions"),
        (Stretch("lake", HERE, blob=line_blob(HERE, kind=5)), "not a line in two dimensions"),
        (Stretch("lake", HERE, blob=line_blob(HERE, grid=4326)), "not a line in two dimensions"),
    ],
    ids=[
        "a form not known",
        "a form from the file",
        "no form",
        "fictitious in text",
        "fictitious in a number",
        "marked in words",
        "not marked",
        "a length below nought",
        "a length in words",
        "a length ten times too long",
        "no line",
        "no line and far away",
        "bytes that are no line",
        "a line of several parts",
        "a line on another grid",
    ],
)
def test_a_row_that_is_not_as_the_file_is_known_to_write_one_stops_the_build(
    tmp_path: Path, water: Stretch, words: str
):
    """The row is within reach of the homes, and further than 300 metres from every one."""
    assert words in str(refused(tmp_path, with_one(water)))


def test_a_stretch_the_file_marks_as_there_in_a_number_is_read_as_one_in_text(tmp_path: Path):
    marked = [Stretch(one.form, one.line, fictitious=0) for one in WATER]
    assert built(tmp_path, zipped(network(marked))).worked == built(tmp_path / "as-text").worked


@pytest.mark.parametrize(
    ("packed", "words"),
    [
        (lambda: CANARY.encode(), "it is not a zip"),
        (lambda: zipped(members=()), "it does not hold the one file that is read"),
        (lambda: zipped(members=("Data/a.gpkg", "Data/b.gpkg")), "it does not hold the one file"),
        (lambda: zipped(CANARY.encode()), "its water could not be read"),
    ],
    ids=["no zip", "no geopackage", "two geopackages", "no database"],
)
def test_a_zip_that_does_not_hold_one_geopackage_is_refused(
    tmp_path: Path, packed: Callable[[], bytes], words: str
):
    assert words in str(refused(tmp_path, packed()))


def test_a_name_is_never_read(town: Access, tmp_path: Path):
    """Every name in the made-up file is the canary. Nothing that is made holds it."""
    assert CANARY not in repr(town)
    unnamed = [(name, kind) for name, kind in FIELDS if not name.startswith("watercourse_name")]
    assert built(tmp_path, zipped(network(fields=unnamed))).worked == town.worked


# The gate, the receipt and the store


def without_scoring() -> Registry:
    """The repository's registry, with the rivers no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.DISPLAY,)})
        if source.id == water_access.SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_water_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=without_scoring())
    found = spine.build(inputs)
    before = inputs.opened
    with pytest.raises(LockError) as stopped:
        water_access.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    # Nothing more was handed over: not the water, and not the centres it would be read at.
    assert inputs.opened == before
    assert not (tmp_path / "work" / water_receipt(the_water()).file_id).exists()


def test_the_water_is_registered_for_scoring_and_so_is_every_file_behind_a_figure(town: Access):
    assert len(town.metric.source_ids) == 4
    for source_id in town.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_two_releases_of_the_water_are_told_apart_by_the_month_that_is_asked_for(tmp_path: Path):
    earlier = zipped(network(changed="2025-10-09T10:00:00.000Z"))
    more = [(water_receipt(earlier, edition="2025-10"), earlier)]
    inputs = inputs_of(tmp_path, more=more)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        water_access.build(inputs, found)
    assert stopped.value.rule == "input_has_one_receipt"
    assert water_access.build(inputs, found, edition="2025-10").metric.vintage == "2025-10"
    assert water_access.build(inputs, found, edition="2026-04").metric.vintage == "2026-04"


def test_the_copy_that_is_unpacked_is_removed_and_the_store_is_as_it_was(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    water_access.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before
    assert [path.name for path in (tmp_path / "work").rglob("*.gpkg")] == []


def test_the_copy_that_is_unpacked_is_removed_when_the_file_is_refused(tmp_path: Path):
    refused(tmp_path, with_one(Stretch("drain", HERE)))
    assert [path.name for path in (tmp_path / "work").rglob("*.gpkg")] == []


# The distance


LINE = (0.0, 0.0, 1_000.0, 0.0)


@pytest.mark.parametrize(
    ("point", "metres"),
    [
        # Beside the middle of the line, on the line, beside each end, and beyond each end.
        ((500.0, 30.0), 30.0),
        ((500.0, 0.0), 0.0),
        ((0.0, -40.0), 40.0),
        ((1_000.0, 40.0), 40.0),
        ((-30.0, 40.0), 50.0),
        ((1_030.0, -40.0), 50.0),
        # Many squares of the grid away, in each direction.
        ((500.0, 4_321.0), 4_321.0),
        ((-7_000.0, 0.0), 7_000.0),
    ],
)
def test_the_distance_is_to_the_nearest_point_of_a_line(point: Place, metres: float):
    assert water_access.nearest({"home": point}, [LINE]) == {"home": metres}


def test_the_nearest_point_of_a_long_line_may_lie_far_from_the_points_it_is_drawn_with():
    """The line runs 7 kilometres from corner to corner, and the home stands by its middle."""
    found = water_access.nearest({"home": (2_600.0, 2_400.0)}, [(0.0, 0.0, 5_000.0, 5_000.0)])
    assert found["home"] == pytest.approx(200 / math.sqrt(2), abs=1e-9)


def test_the_distance_is_to_the_nearest_of_several_lines_in_whatever_order_they_come():
    lines = [LINE, (0.0, 100.0, 1_000.0, 100.0, 1_000.0, 900.0), (0.0, -5_000.0, 9.0, -5_000.0)]
    homes = {"a": (500.0, 60.0), "b": (900.0, 500.0), "c": (5.0, -4_000.0)}
    found = water_access.nearest(homes, lines)
    assert found == {"a": 40.0, "b": 100.0, "c": 1_000.0}
    assert water_access.nearest(homes, list(reversed(lines))) == found


def test_a_home_with_no_line_within_reach_has_no_distance_and_is_not_given_the_reach():
    homes = {"near": (500.0, 9_999.0), "at": (500.0, 10_000.0), "far": (500.0, 10_000.5)}
    assert water_access.nearest(homes, [LINE]) == {"near": 9_999.0, "at": 10_000.0}
    assert water_access.nearest(homes, [LINE], reach=100) == {}
    assert water_access.nearest(homes, []) == {}


def test_more_than_a_few_homes_with_no_water_within_reach_stop_the_build(tmp_path: Path):
    """One centre of the twelve stands 19 kilometres from the nearest line."""
    inputs = inputs_of(tmp_path, placed=on(*PLACED[:11], (703_000.0, 420_000.0)))
    with pytest.raises(LockError) as stopped:
        water_access.build(inputs, spine.build(inputs))
    assert "its water does not reach the homes of the build" in str(stopped.value)


def test_a_home_with_no_water_within_reach_is_far_from_water_and_has_no_distance(town: Access):
    """A town of 200 homes in a row, a metre apart, and one home 19 kilometres to the north."""
    homes = {f"made-up-{at}": (700_000.0 + at, 400_100.0) for at in range(200)}
    near, metres, unreached = water_access.verdicts(
        town.rivers, homes | {"far": (703_000.0, 420_000.0)}
    )
    assert unreached == 1
    assert near["far"] is False and "far" not in metres
    assert all(near[home] and metres[home] == 100.0 for home in homes)


def test_each_output_area_is_as_far_from_water_as_was_worked_out_by_hand(town: Access):
    by_hand = (
        60,
        300,
        300.5,
        math.hypot(600, 100),
        100,
        200,
        300,
        1_000,
        50,
        301,
        250,
        math.hypot(2_000, 4_000),
    )
    assert [town.metres[oa] for oa in OAS] == pytest.approx(by_hand, abs=1e-9)


def test_an_output_area_is_near_water_at_300_metres_and_not_a_half_metre_further(town: Access):
    assert [town.near[oa] for oa in OAS] == [
        *(True, True, False, False),
        *(True, True, True, False),
        *(True, False, True, False),
    ]


# The figure


def test_an_area_is_given_the_share_of_its_homes_that_are_near_water(town: Access):
    assert (110 + 120) / 500 == 0.46
    assert town.worked[QUILLHAVEN_1] == Worked(46.0, 4, 4, 1.0, State.PRESENT)


def test_a_figure_is_given_to_one_decimal_place(town: Access):
    assert round(100 * (150 + 160 + 170) / 660, 4) == 72.7273
    assert round(100 * (190 + 210) / 820, 4) == 48.7805
    assert town.worked[QUILLHAVEN_2] == Worked(72.7, 4, 4, 1.0, State.PRESENT)
    assert town.worked[TALLOWGATE] == Worked(48.8, 4, 4, 1.0, State.PRESENT)


def test_an_area_with_no_home_near_water_is_at_nought_and_nought_is_a_figure(tmp_path: Path):
    placed = on(*PLACED[:8], *[(705_000.0, 405_000.0)] * 4)
    found = built(tmp_path, placed=placed)
    assert found.worked[TALLOWGATE] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    assert found.rows[2].value == 0.0 and found.rows[2].has_a_value


def test_an_output_area_with_no_centre_is_never_taken_to_be_far_from_water(tmp_path: Path):
    placed = {oa: place for oa, place in on(*PLACED).items() if oa != OAS[0]}
    found = built(tmp_path, placed=placed)
    # The first output area holds 110 of the area's 500 homes. Of the other 390, 120 are near.
    assert round(100 * 120 / 390, 4) == 30.7692
    assert found.worked[QUILLHAVEN_1] == Worked(30.8, 3, 4, 0.78, State.PARTIAL)
    assert OAS[0] not in found.near and OAS[0] not in found.metres


def test_an_output_area_outside_what_the_file_covers_has_no_verdict(tmp_path: Path):
    """The last centre stands east of the box the file says its lines cover."""
    placed = on(*PLACED[:11], (COVERS[2] + 1, 400_500.0))
    found = built(tmp_path, placed=placed)
    assert OAS[11] not in found.near
    assert found.worked[TALLOWGATE] == Worked(66.7, 3, 4, round(600 / 820, 6), State.PARTIAL)


def test_below_half_the_homes_no_figure_is_given(tmp_path: Path):
    placed = {oa: place for oa, place in on(*PLACED).items() if oa not in OAS[9:]}
    found = built(tmp_path, placed=placed).worked[TALLOWGATE]
    assert found == Worked(None, 1, 4, round(190 / 820, 6), State.BELOW_THRESHOLD)


def test_an_area_with_no_centre_at_all_is_a_gap_and_has_no_figure(tmp_path: Path):
    placed = {oa: place for oa, place in on(*PLACED).items() if oa not in OAS[8:]}
    found = built(tmp_path, placed=placed)
    assert found.worked[TALLOWGATE] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found.worked[QUILLHAVEN_1] == Worked(46.0, 4, 4, 1.0, State.PRESENT)


def test_the_order_of_the_rows_changes_nothing(town: Access, tmp_path: Path):
    turned = built(tmp_path, zipped(network(tuple(reversed(WATER)))))
    assert (turned.worked, turned.metres) == (town.worked, town.metres)
    assert turned.rivers.links == town.rivers.links


def test_a_lake_counts_as_a_river_does(tmp_path: Path):
    """With the lake taken out of the file, the home beside it is no longer near water."""
    without = built(tmp_path, zipped(network([one for one in WATER if one.form != "lake"])))
    assert without.near[OAS[4]] is False
    assert without.worked[QUILLHAVEN_2] == Worked(50.0, 4, 4, 1.0, State.PRESENT)


def test_a_stretch_drawn_as_one_long_straight_line_counts_as_any_other(tmp_path: Path):
    """The file does not say what such a stretch is, so it is not left out."""
    straight = stretch("inlandRiver", (695_000, 405_100), (709_000, 405_100))
    found = built(tmp_path, with_one(straight))
    assert found.metres[OAS[11]] == 100.0 and found.near[OAS[11]]


# The evidence


def test_every_area_has_a_row_of_evidence_that_holds_its_figure(town: Access):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/water_access" for area in (QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE)
    ]
    assert [row.value for row in town.rows] == [46.0, 72.7, 48.8]
    assert [(row.units_used, row.units_expected) for row in town.rows] == [(4, 4)] * 3
    assert {row.state for row in town.rows} == {State.PRESENT}


def test_a_row_names_the_water_the_centres_the_lookup_and_the_homes(town: Access):
    by_source = {receipt.source_id: receipt.file_id for receipt in town.files}
    assert sorted(by_source) == sorted(
        [water_access.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES]
    )
    for row in town.rows:
        assert row.inputs == tuple(sorted(by_source.values()))
        assert row.derivation_id == "homes_within_300m@1"
        assert row.retrieved_on == "2026-09-23"
        # From the day of the census, which the weights are of, to the end of the water's month.
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", "2026-04-30")


def test_the_figures_are_marked_as_measured_by_the_method_the_design_names():
    assert water_access.METHODS == (water_access.METHOD,)
    assert water_access.METHOD.name == "homes_within_300m"
    assert water_access.METHOD.kind is Kind.MEASURED
    assert water_access.METHOD.parameters["metres"] == water_access.METRES == 300


def test_the_measure_says_that_the_file_is_keyed_by_lines(town: Access):
    assert town.geography is Geography.LINE


def test_the_evidence_of_the_measure_has_no_loose_end(town: Access):
    """Every row names a method and files that the evidence of a release would hold."""
    evidence = Evidence.of("lon-2026-10-09-01", town.files, water_access.METHODS, town.rows)
    assert len(evidence.rows) == 3


def test_the_measure_gives_what_the_list_of_measures_asks_of_one(town: Access):
    measured: measures.Measured = town
    assert measured.metric.feature_id is FeatureId.WATER_ACCESS


# The name, the unit and the sentences


def test_the_row_of_the_catalogue_counts_homes_and_core_says_the_same(town: Access):
    """Core's label is held here, so that this fails on the day core names the area again."""
    core = FEATURES[FeatureId.WATER_ACCESS]
    assert (
        town.metric.label
        == core.label
        == (
            "Share of homes within 300 m, in a straight line, of the centre line of a river, "
            "canal or lake"
        )
    )
    assert measures.says_what_core_says(town.metric)
    of_the_area = town.metric.model_copy(
        update={"label": "Share of the area within 300 m of a river or canal"}
    )
    assert not measures.says_what_core_says(of_the_area)
    listed = {measure.feature: measure for measure in measures.MEASURES}
    assert listed[FeatureId.WATER_ACCESS].waits_on == ()


def test_the_unit_and_which_way_is_more_are_cores(town: Access):
    metric, core = town.metric, FEATURES[FeatureId.WATER_ACCESS]
    assert (metric.dimension, metric.unit, metric.polarity) == (
        core.dimension,
        core.unit,
        core.polarity,
    )
    assert (metric.unit, metric.polarity) == ("%", Polarity.MORE)
    assert metric.vintage == "2026-04"
    assert metric.source_ids == tuple(sorted(metric.source_ids))


def test_the_definition_is_one_sentence_that_says_what_the_figure_is_and_is_not(town: Access):
    definition = town.metric.definition
    assert definition.endswith(".") and not re.search(r"[.!?]\s|\n", definition)
    for words in (
        "Ordnance Survey's OS Open Rivers of 2026-04",
        "within 300 metres",
        "a river, a tidal river, a canal or a lake",
        "census of 2021",
        "in a straight line",
        "to 1 decimal place",
        "a line with no width",
        "does not say where water runs under the ground",
        "not a measure of a view",
    ):
        assert words in definition
    # Every parameter of the method stands in it, as it stands in the method's own sentence.
    assert str(water_access.METHOD.parameters["metres"]) in definition


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|health|ages?|incomes?)\b", re.I
)


def test_no_sentence_of_the_measure_describes_who_lives_somewhere(town: Access):
    sentences = (town.metric.label, town.metric.definition, *water_access.CANNOT_SEE)
    assert [sentence for sentence in sentences if RESIDENT_WORDS.search(sentence)] == []


def test_what_it_cannot_see_is_said_in_two_sentences_with_no_figure_in_them():
    assert len(water_access.CANNOT_SEE) == 2
    for sentence in water_access.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[.!?]\s|\d", sentence)


def test_it_says_that_a_line_has_no_width_and_that_it_cannot_see_under_the_ground():
    assert "which has no width" in water_access.CANNOT_SEE[0]
    assert "in a tunnel or a pipe" in water_access.CANNOT_SEE[1]


def test_it_claims_no_view_and_no_frontage():
    """The licence registry asks that the product is never used to claim either."""
    said = " ".join((water_access.LABEL, *water_access.CANNOT_SEE)).lower()
    assert "view" not in said and "frontage" not in said and "waterfront" not in said
    conditions = " ".join(registry().get(water_access.SOURCE).conditions)
    assert "waterfront view or frontage" in conditions
