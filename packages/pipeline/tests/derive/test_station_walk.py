"""The nearest station, from the publisher's ways in to a distance for each area.

Every file here is made up: `stops_support.py` writes the stops, and the tests
of cells draw the town they stand on. The centre of each output area is put in
the very middle of its square, so each distance can be worked out by hand.

    columns  0    1    2    3    4    5        7
    row 2                            T
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |    z1 is land outside London
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |

    Pellam Cross Station   ways in at the middle of a1 and of a3
    Tallowgate             a way in on the line between b2 and b4
    Sable Reach Tram Stop  T: a way in 100 metres north of the middle of c2

    Quillhaven 001   homes 110, 120, 130, 140   at 0, 100, 0 and 100 metres from a way in
    Quillhaven 002   homes 150, 160, 170, 180   at 112, 50, 112 and 50
    Tallowgate 001   homes 190, 200, 210, 220   at 112, 100, 112 and 200

The land outside London is 150 metres from the middle of c2 and 158 from the
middle of c4. So the homes of c4, 200 metres from the tram stop, may have a
nearer station outside London, and their distance is not known.
"""

import math
from collections.abc import Iterator, Sequence
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import pytest
from burro_core.catalogue import FEATURES, NEVER_A_TRADE_OFF
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_core.release import DECIDED_BY_CORE
from burro_pipeline.cells import centres, land, spine
from burro_pipeline.derive import measures, park_proximity, station_walk, stops_file
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.station_shapes import to_the_nearest_land, to_the_nearest_point
from burro_pipeline.derive.station_walk import Distances, Nearest
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.method import Kind
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs, Opened

from ..cells.support import LONDON, held, lookup_csv, lsoa_outlines
from .green_support import centres_in_the_middle
from .stops_support import (
    AREAS,
    BAY,
    BUS,
    CANARY,
    OAS,
    PELLAM,
    PIER,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    SAVED,
    SHUT,
    STOPS,
    TALLOWGATE,
    TRAM,
    UNDER,
    WAY_1,
    WAY_2,
    MadeUpStop,
    at,
    inputs_of,
    stops_csv,
)

# The distance across a square and half of one, and across two and half of one.
SLANT, LONG = math.hypot(100, 50), math.hypot(200, 50)
NO_LAND_OUTSIDE = {"lookup": lookup_csv(LONDON), "lsoa_outlines": lsoa_outlines(LONDON)}


def built(inputs: Inputs) -> Nearest:
    return station_walk.build(inputs, spine.build(inputs))


def of(folder: Path, stops: Sequence[MadeUpStop]) -> Nearest:
    return built(inputs_of(folder, stops_csv(stops)))


def values_of(made: Distances) -> list[float | None]:
    return [made.worked[area].value for area in AREAS]


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Nearest:
    return built(inputs_of(tmp_path_factory.mktemp("town")))


@pytest.fixture(scope="module")
def no_tram(tmp_path_factory: pytest.TempPathFactory) -> Nearest:
    """The town before its tram stop was built. The homes of c2 and c4 are then far."""
    return of(tmp_path_factory.mktemp("no-tram"), [one for one in STOPS if one is not TRAM])


# What counts as a station


def test_a_way_in_to_a_railway_and_to_a_tram_metro_or_underground_station_counts(town: Nearest):
    assert station_walk.COUNTS == ("RSE", "TMU")
    assert town.stops == 4


def test_a_way_in_that_is_not_active_is_not_counted(town: Nearest):
    """It stands at the middle of a2, whose homes are 100 metres from the nearest that is."""
    assert SHUT.point == at(150, 150)
    assert town.found_of_oa[OAS[1]] == 100.0


def test_a_pier_and_a_stop_of_a_bus_are_no_station(town: Nearest):
    """A pier stands at the middle of b3, a stop at the middle of a4 and a bay at that of c4."""
    assert (PIER.point, BUS.point, BAY.point) == (at(250, 50), at(150, 50), at(550, 50))
    assert [town.found_of_oa[oa] for oa in (OAS[6], OAS[3], OAS[11])] == [SLANT, 100.0, 200.0]


# The figure


def test_each_output_area_is_as_far_as_its_centre_is_from_the_nearest_way_in(town: Nearest):
    far = [0.0, 100.0, 0.0, 100.0, SLANT, 50.0, SLANT, 50.0, SLANT, 100.0, SLANT, 200.0]
    assert [town.found_of_oa[oa] for oa in OAS] == far


def test_an_area_is_given_the_median_over_its_homes_to_the_nearest_ten_metres(town: Nearest):
    assert town.worked == {
        # 240 homes at 0 and 260 at 100: half of the 500 are no further than 100.
        QUILLHAVEN_1: Worked(100.0, 4, 4, 1.0, State.PRESENT),
        # 340 homes at 50 and 320 at 112: half of the 660 are no further than 50.
        QUILLHAVEN_2: Worked(50.0, 4, 4, 1.0, State.PRESENT),
        # Of the homes whose distance is known, 200 are at 100 and 400 at 112.
        TALLOWGATE: Worked(110.0, 3, 4, round(600 / 820, 6), State.PARTIAL),
    }


def test_the_nearest_is_found_however_the_points_lie():
    """Held to measuring to every point, for points laid out by arithmetic."""
    points = [(float(7 * n * n % 9_000), float(13 * n * n * n % 7_000)) for n in range(60)]
    homes = [(0.0, 0.0), (4_500.5, 3_500.5), (-25_000.0, 40_000.0), (8_999.0, 6_999.0)]
    every = [min(math.dist(home, point) for point in points) for home in homes]
    assert to_the_nearest_point(homes, points) == pytest.approx(every, abs=1e-9)
    assert to_the_nearest_point(homes, []) == [math.inf] * 4
    assert to_the_nearest_point([], points) == []
    assert to_the_nearest_land(homes, []) == [math.inf] * 4


def test_it_is_worked_out_the_same_twice_and_in_whatever_order_the_rows_come(
    tmp_path: Path, town: Nearest
):
    again = built(inputs_of(tmp_path / "again"))
    assert (again.worked, again.rows, again.metric) == (town.worked, town.rows, town.metric)
    turned = of(tmp_path / "turned", list(reversed(STOPS)))
    assert (turned.worked, turned.of_oa, turned.edge) == (town.worked, town.of_oa, town.edge)


# The edge of London


def test_a_home_nearer_to_land_outside_london_than_to_a_way_in_has_no_distance(town: Nearest):
    assert OAS[11] not in town.of_oa and town.found_of_oa[OAS[11]] == 200.0
    assert set(town.of_oa) == set(OAS[:11])
    assert all(town.of_oa[oa] == town.found_of_oa[oa] for oa in town.of_oa)


def test_the_areas_the_edge_touches_are_listed_and_so_are_those_it_leaves_with_no_figure(
    town: Nearest, no_tram: Nearest
):
    assert town.edge == station_walk.Edge((OAS[11],), (TALLOWGATE,), ())
    assert no_tram.edge == station_walk.Edge((OAS[9], OAS[11]), (TALLOWGATE,), (TALLOWGATE,))


def test_below_half_the_homes_known_no_figure_is_given(no_tram: Nearest):
    """The homes of c2 and c4 are 206 metres from the underground, and the edge is nearer."""
    assert [no_tram.found_of_oa[oa] for oa in (OAS[9], OAS[11])] == [LONG, LONG]
    assert no_tram.worked[TALLOWGATE] == Worked(
        None, 2, 4, round(400 / 820, 6), State.BELOW_THRESHOLD
    )
    assert values_of(no_tram) == [100.0, 50.0, None]
    assert [row.value for row in no_tram.rows] == [100.0, 50.0, None]


def test_with_no_distance_known_an_area_is_a_gap_and_nothing_is_filled_in(tmp_path: Path):
    found = of(tmp_path, [WAY_1, WAY_2])
    assert found.worked[TALLOWGATE] == Worked(None, 0, 4, 0.0, State.SOURCE_GAP)
    assert found.edge.without_a_figure == (TALLOWGATE,)
    assert all(row.inputs for row in found.rows)


def test_a_way_in_as_far_as_the_land_outside_is_known_and_one_a_metre_further_is_not(
    tmp_path: Path,
):
    """The land outside London is 150 metres from the middle of c2."""
    north = replace(TRAM, point=at(550, 300))
    further = replace(TRAM, point=at(550, 301))
    assert of(tmp_path / "as-far", [WAY_1, north]).of_oa[OAS[9]] == 150.0
    assert OAS[9] not in of(tmp_path / "further", [WAY_1, further]).of_oa


def test_ground_that_is_no_land_of_anyone_is_no_edge(town: Nearest):
    """Between the town and the land outside is a strip 100 metres wide that no outline holds.

    The tidal river is such ground in London. The homes of c2 are 50 metres
    from the strip and 100 from the tram stop, and their distance is known.
    """
    assert town.of_oa[OAS[9]] == 100.0


def test_where_no_land_outside_london_is_near_every_distance_is_known(tmp_path: Path):
    found = built(inputs_of(tmp_path, ground=NO_LAND_OUTSIDE))
    assert found.of_oa == found.found_of_oa and len(found.of_oa) == 12
    assert found.edge == station_walk.Edge((), (), ())
    # The homes of c4 are then counted: 200 at 100, 400 at 112 and 220 at 200.
    assert found.worked[TALLOWGATE] == Worked(110.0, 4, 4, 1.0, State.PRESENT)


def test_the_land_outside_london_is_every_small_area_the_lookup_gives_to_no_borough(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path)
    lookup = inputs.open(spine.LOOKUP, spine.Use.SCORING, edition=spine.LOOKUP_EDITION)
    assert station_walk.outside_london(lookup) == {"E01999901"}


def test_an_output_area_with_no_centre_has_no_distance_and_none_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, ground={"centres": centres_in_the_middle(left_out=[OAS[0]])})
    found = built(inputs)
    assert OAS[0] not in found.found_of_oa and OAS[0] not in found.of_oa
    # The first output area holds 110 of the area's 500 homes.
    assert found.worked[QUILLHAVEN_1] == Worked(100.0, 3, 4, round(390 / 500, 6), State.PARTIAL)
    # It is at no edge: what is listed there is what the edge leaves out.
    assert found.edge.output_areas == (OAS[11],)


def test_a_file_with_no_way_in_to_a_station_stops_the_build(tmp_path: Path):
    with pytest.raises(LockError) as error:
        of(tmp_path, [PIER, BUS, BAY, SHUT])
    assert error.value.rule == "input_is_as_described"


def test_a_build_with_no_file_of_stops_leaves_the_measure_out(tmp_path: Path):
    inputs = inputs_of(tmp_path, name="910Stops.csv")
    with pytest.raises(LockError) as error:
        built(inputs)
    assert error.value.rule == "input_has_one_receipt"


# What is never read


def test_the_measure_reads_six_columns_of_the_stops_and_never_a_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    asked: list[tuple[str, ...]] = []
    rows = Opened.rows

    def spy(self: Opened, text: TextIO, named: Sequence[str]) -> Iterator[dict[str, str]]:
        if self.receipt.source_id == stops_file.SOURCE:
            asked.append(tuple(named))
        return rows(self, text, named)

    monkeypatch.setattr(Opened, "rows", spy)
    found = built(inputs_of(tmp_path))
    assert asked == [("ATCOCode", "StopType", "Status", "GridType", "Easting", "Northing")]
    said = f"{found.worked} {found.rows} {found.metric} {found.edge}"
    assert CANARY not in said and PELLAM not in said


def test_the_store_is_never_written_to(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    built(inputs)
    assert held(tmp_path / "store") == before


# The stops of buses, which no build carries


def test_the_same_is_worked_out_for_the_nearest_stop_of_a_bus(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = station_walk.distances(inputs, spine.build(inputs), stops_file.BUS_TYPES)
    assert found.stops == 2
    # The stop is at the middle of a4 and the bay at the middle of c4.
    assert [found.found_of_oa[oa] for oa in (OAS[3], OAS[2], OAS[11], OAS[9])] == [
        0.0,
        100.0,
        0.0,
        100.0,
    ]
    assert not hasattr(found, "metric")


# The evidence


def test_every_area_has_a_row_that_holds_its_figure(town: Nearest):
    assert [row.fact_id for row in town.rows] == [f"{area}/feature/station_walk" for area in AREAS]
    assert [row.value for row in town.rows] == [100.0, 50.0, 110.0]
    assert [row.state for row in town.rows] == [State.PRESENT, State.PRESENT, State.PARTIAL]
    for row in town.rows:
        assert row.derivation_id == "straight_line_to_nearest@1"
        assert row.retrieved_on == "2026-09-24"
        assert row.data_period is not None
        assert row.data_period.days() == ("2021-03-21", SAVED)


def test_a_row_names_the_stops_the_centres_the_lookup_the_homes_and_the_outlines(town: Nearest):
    sources = [receipt.source_id for receipt in town.files]
    assert sorted(sources) == sorted(
        [stops_file.SOURCE, centres.CENTRES, spine.LOOKUP, spine.HOMES, land.BOUNDARIES]
    )
    ids = tuple(sorted(receipt.file_id for receipt in town.files))
    assert all(row.inputs == ids for row in town.rows)


def test_a_measure_that_was_built_before_names_none_of_its_files(tmp_path: Path):
    """A build hands every measure the same inputs. A row names what its own measure read."""
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    inputs.open("ons-output-areas-2021", spine.Use.CELLS, edition="BGC V2")
    made = station_walk.build(inputs, found)
    assert "ons-output-areas-2021" not in {receipt.source_id for receipt in made.files}


def test_the_rows_are_evidence_a_release_can_hold(town: Nearest):
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=station_walk.METHODS,
        receipts=town.files,
        rows=town.rows,
    )
    assert len(evidence.rows) == 3


def test_the_method_is_the_one_the_distance_to_a_park_is_worked_out_by():
    assert station_walk.METHOD is park_proximity.STRAIGHT_LINE
    assert station_walk.METHOD.kind is Kind.MEASURED
    assert "straight line" in station_walk.METHOD.sentence


# The row of the catalogue, and what core needs


def test_the_row_says_a_straight_line_in_metres_and_names_every_source(town: Nearest):
    metric = town.metric
    assert metric.feature_id is FeatureId.STATION_WALK
    assert metric.label == "Straight-line distance to the nearest way in to a station"
    assert (metric.unit, metric.polarity) == ("m", Polarity.LESS)
    assert metric.native_resolution is NativeResolution.POINT
    assert metric.vintage == SAVED and town.saved == SAVED
    assert metric.source_ids == tuple(sorted(receipt.source_id for receipt in town.files))
    assert town.geography is Geography.POINT


def test_the_sentence_of_the_measure_says_what_it_is_and_what_it_is_not(town: Nearest):
    said = town.metric.definition
    for words in (
        "in a straight line, in metres",
        "the nearest way in to a railway station or to a tram, metro or underground station",
        "the Department for Transport lists for Greater London in NaPTAN",
        f"saved on {SAVED}",
        "the median over the area's homes at the census of 2021",
        "to the nearest 10 metres with a half taken upward",
        "not along any street or path, so the walk is longer",
        "the file holds no station outside London",
    ):
        assert words in said
    assert said == station_walk.definition_of(SAVED)


def test_nothing_said_of_the_figure_calls_it_a_walk_or_gives_it_in_minutes():
    said = (station_walk.LABEL, station_walk.DEFINITION, *station_walk.CANNOT_SEE)
    for words in said:
        assert "minute" not in words
        assert "walk" not in words or "not a walk" in words or "the walk is longer" in words
    assert "walk" not in station_walk.LABEL.lower()


def test_the_row_is_cores_so_a_build_carries_the_measure(town: Nearest):
    assert says_what_core_says(town.metric)
    core = FEATURES[FeatureId.STATION_WALK]
    differs = {
        name for name in DECIDED_BY_CORE if getattr(town.metric, name) != getattr(core, name)
    }
    assert differs == set()
    in_minutes = town.metric.model_copy(update={"unit": "min"})
    assert not says_what_core_says(in_minutes)


def test_core_names_a_straight_line_in_metres_as_the_figure_is():
    """Core changed three things together: the name, the unit, and the floor.

    The figure at which the measure is never a trade-off was 10 minutes, and is a
    distance in metres.
    """
    core = FEATURES[FeatureId.STATION_WALK]
    assert (core.label, core.unit) == (station_walk.LABEL, station_walk.UNIT)
    assert core.native_resolution is NativeResolution.POINT
    assert NEVER_A_TRADE_OFF[FeatureId.STATION_WALK] == 800
    listed = {measure.feature: measure for measure in measures.MEASURES}
    assert listed[FeatureId.STATION_WALK].waits_on == ()


def test_what_the_measure_cannot_see_is_said_in_whole_sentences():
    for said in station_walk.CANNOT_SEE:
        assert said.endswith(".") and "!" not in said and "\n" not in said and "|" not in said
    assert any("not a walk" in said for said in station_walk.CANNOT_SEE)
    assert any("cable car" in said for said in station_walk.CANNOT_SEE)
    assert any("London's edge" in said for said in station_walk.CANNOT_SEE)


def test_it_reads_the_file_of_londons_stops_and_is_called_as_the_list_calls_a_measure():
    assert station_walk.is_the_file("490Stops.csv") and not station_walk.is_the_file("Stops.csv")
    assert (station_walk.FEATURE, station_walk.SOURCE) == (FeatureId.STATION_WALK, "dft-naptan")
    assert UNDER.type in station_walk.COUNTS
