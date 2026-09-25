"""How near stops are: three parts of Well connected and the stops of buses, on made-up files.

Every file here is made up: `stops_support.py` writes the stops, under the name
the publisher gives its national file, `tfl_support.py` writes the stations
with the modes that call at each, and the tests of cells draw the town they
stand on. The centre of each output area is put in the very middle of its
square, so each figure can be worked out by hand.

    columns  0    1    2    3    4    5        7
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |   | z1 |    z1 is land outside London
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |

    Quillhaven 001   homes 110, 120, 130, 140   in a1, a2, a3 and a4
    Quillhaven 002   homes 150, 160, 170, 180   in b1, b2, b3 and b4
    Tallowgate 001   homes 190, 200, 210, 220   in c1, c2, c3 and c4

    The railway stations of the national file, and what the other file says calls at each:

    Pellam Cross   a way in at the middle of a1, the station at that of a3   the Overground
    Tallowgate     the station at the middle of b1            the Elizabeth line and National Rail
    Sable Reach    the station at the middle of c4            not in the other file
"""

import math
from collections.abc import Sequence
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NEVER_A_TRADE_OFF, RANKED_AS, TAGS
from burro_core.ids import FeatureId, NativeResolution, Polarity, TagId
from burro_pipeline.cells import spine
from burro_pipeline.derive import connected, measures, park_proximity, stops_file, tfl_stations
from burro_pipeline.derive.connected import BUS, OVERGROUND, RAIL, UNDERGROUND, Connected
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.station_shapes import how_many_within, nearest_within
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from . import tfl_support
from .stops_support import (
    AREAS,
    CANARY,
    OAS,
    QUILLHAVEN_1,
    QUILLHAVEN_2,
    SAVED,
    TALLOWGATE,
    MadeUpStop,
    at,
    inputs_of,
    stops_csv,
)
from .tfl_support import MadeUpStation

NATIONAL = "Stops.csv"
SLANT = math.hypot(100, 50)
# A way in to an underground station on the line between b2 and b4, and the station itself
# at the middle of b2: the homes of b2 stand on the station, 50 metres from its way in.
WAY_IN = MadeUpStop("4900ZZLUTLG1", "Tallowgate", "TMU", at(350, 100))
STATION = MadeUpStop("9400ZZLUTLG", "Tallowgate", "MET", at(350, 150))
# Three railway stations. The first has a way in at the middle of a1.
PELLAM_WAY_IN = MadeUpStop("4900PELLAMX1", "Pellam Cross Station", "RSE", at(50, 150))
PELLAM = MadeUpStop("9100PELLAMX", "Pellam Cross Station", "RLY", at(50, 50))
TALLOW = MadeUpStop("9100TALLOWG", "Tallowgate Station", "RLY", at(250, 150))
SABLE = MadeUpStop("9100SABLERH", "Sable Reach Station", "RLY", at(550, 50))
# A tram stop, 100 metres north of the middle of c2.
TRAM = MadeUpStop("4900ZZCRSBR1", "Sable Reach Tram Stop", "TMU", at(550, 250))
# What holds letters of its own, and counts as no kind: an end of a cable car at the
# middle of a2, and a miniature railway at the middle of a4.
CABLE_CAR = MadeUpStop("4900ZZALLTY1", "Lantern Yard", "TMU", at(150, 150))
MINIATURE = MadeUpStop("9400ZZRLCRW", "Coracle Row", "MET", at(150, 50))
# A station of another authority, past the edge of the town, 100 metres east of the middle
# of c2.
OUTSIDE = MadeUpStop("1500ZZLUOTB1", "Otterby Fields", "TMU", at(650, 150))
# Stops of a bus: two on one spot at the middle of a4, one exactly 400 metres north of it,
# and one a metre further. A bay and a stop that is not active are no stop.
BUS_1 = MadeUpStop("490000001A", "Coracle Row", "BCT", at(150, 50))
BUS_2 = MadeUpStop("490000001B", "Coracle Row", "BCT", at(150, 50))
AT_THE_REACH = MadeUpStop("490000002A", "Foxholt Market", "BCT", at(150, 450))
PAST_THE_REACH = MadeUpStop("490000002B", "Foxholt Market", "BCT", at(150, 451))
BAY = MadeUpStop("490000003A", "Lantern Yard", "BCS", at(150, 50))
SHUT = MadeUpStop("490000004A", "Lantern Yard", "BCT", at(150, 50), status="inactive")
# A row far from the town that names no grid, as thousands of the national file do.
FAR = MadeUpStop("6400FAR001", "Scrimshaw Airfield", "BCT", (900_000.0, 900_000.0), grid="")
STOPS = (
    WAY_IN,
    STATION,
    PELLAM_WAY_IN,
    PELLAM,
    TALLOW,
    SABLE,
    TRAM,
    CABLE_CAR,
    MINIATURE,
    BUS_1,
    BUS_2,
    AT_THE_REACH,
    PAST_THE_REACH,
    BAY,
    SHUT,
    FAR,
)
# What the other file says of the stations it serves. It gives Pellam Cross two points,
# each 10 metres from a row of the national file, and Tallowgate one, 20 metres off. A point
# of Pellam Cross is 190 metres from Tallowgate, and is not the nearest to it. The third is
# an underground station, which no railway row is joined to. The fourth is a station of
# the Overground 250 metres north of Sable Reach: too far to be the same station.
SERVED = (
    MadeUpStation("910GPELLAMX", ("weaver",), (at(60, 150), at(50, 60))),
    MadeUpStation("910GTALLOWG", ("elizabeth", "national-rail"), (at(250, 170),)),
    MadeUpStation("940GZZLUTLG", ("central",), (at(350, 150),)),
    MadeUpStation("910GOSIERHM", ("weaver",), (at(550, 300),)),
)


def given(
    folder: Path,
    stops: Sequence[MadeUpStop] = STOPS,
    served: Sequence[MadeUpStation] | None = SERVED,
) -> Inputs:
    more = [] if served is None else [tfl_support.given(served)]
    return inputs_of(folder, stops_csv(stops), name=NATIONAL, more=more)


def built(inputs: Inputs, feature: FeatureId) -> Connected:
    return connected.build(feature, inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> dict[FeatureId, Connected]:
    inputs = given(tmp_path_factory.mktemp("town"))
    found = spine.build(inputs)
    return {feature: connected.build(feature, inputs, found) for feature in connected.MEASURES}


def far(made: Connected) -> list[float]:
    return [made.of_oa[oa] for oa in OAS]


def read_as(stops: Sequence[MadeUpStop], folder: Path) -> tuple[stops_file.Stop, ...]:
    opened = stops_file.open_the_national_file(given(folder, stops), Use.SCORING)
    return stops_file.read(opened, connected.TYPES)


# What counts: the Underground and the DLR


def test_the_underground_is_measured_to_a_way_in_or_to_the_station_whichever_is_nearer(
    town: dict[FeatureId, Connected],
):
    """The homes of b2 stand on the station, and those of b4 are nearer its way in."""
    assert town[UNDERGROUND].points == 2
    assert far(town[UNDERGROUND])[4:8] == [100.0, 0.0, SLANT, 50.0]


def test_a_station_with_no_way_in_of_its_own_is_found_by_its_own_point(tmp_path: Path):
    """One station in eight of the real file has none: its way in is a railway station's."""
    alone = built(given(tmp_path, [STATION, PELLAM_WAY_IN, BUS_1]), UNDERGROUND)
    assert alone.points == 1 and alone.of_oa[OAS[5]] == 0.0


def test_what_holds_letters_of_its_own_counts_as_no_kind(tmp_path: Path):
    """An end of a cable car stands at the middle of a2, and a miniature railway at that of a4."""
    for stop in read_as([CABLE_CAR, MINIATURE], tmp_path):
        assert not connected.is_underground_or_dlr(stop)
        assert not connected.is_a_railway_station(stop)
        assert not connected.is_a_tram_stop(stop) and not connected.is_a_bus_stop(stop)


def test_the_two_stations_that_opened_with_letters_of_their_own_are_the_undergrounds(
    tmp_path: Path,
):
    new = [
        MadeUpStop("9400ZZBPSUST", "Kindlewharf", "MET", at(50, 50)),
        MadeUpStop("4900ZZNEUGST", "Sable Reach", "TMU", at(550, 50)),
    ]
    assert connected.UNDERGROUND_OR_DLR == ("LU", "DL", "BP", "NE")
    assert all(connected.is_underground_or_dlr(stop) for stop in read_as(new, tmp_path))


def test_a_stop_past_the_edge_of_london_counts_where_it_is_nearest(tmp_path: Path):
    """The file is the whole country's, so no home is left out for standing near the edge."""
    made = built(given(tmp_path, [*STOPS, OUTSIDE]), UNDERGROUND)
    # The homes of c2 are 100 metres from the station outside, and 200 from the one inside.
    # Those of c4 are 141 from it, and 206 from the way in inside.
    assert [made.of_oa[oa] for oa in OAS[8:]] == [100.0, 100.0, SLANT, math.hypot(100, 100)]
    assert all(one.state is State.PRESENT for one in made.worked.values())


# What counts: which trains call at a railway station


def test_a_railway_station_is_joined_to_the_other_files_by_where_it_stands(tmp_path: Path):
    inputs = given(tmp_path)
    found = spine.build(inputs)
    points = connected.centres.build(inputs, found)
    stops = connected.stops_round(inputs, [points[oa] for oa in sorted(points)])
    served = tfl_stations.open_the_file(inputs, Use.SCORING)
    joined = connected.join(stops, connected.stations_of(served), served)
    assert connected.JOINED_WITHIN == 200
    assert {stop.code: station and station.station_id for stop, station in joined.rows} == {
        "4900PELLAMX1": "910GPELLAMX",
        "9100PELLAMX": "910GPELLAMX",
        "9100TALLOWG": "910GTALLOWG",
        # The station of the Overground that stands 250 metres off is another station.
        "9100SABLERH": None,
    }
    assert joined.stations == 2


def test_the_overground_or_the_elizabeth_line_is_where_the_other_file_says_either_calls(
    town: dict[FeatureId, Connected],
):
    """Pellam Cross, at its way in and at the station, and Tallowgate. Not Sable Reach."""
    assert town[OVERGROUND].points == 3
    assert far(town[OVERGROUND]) == [
        *(0.0, 100.0, 0.0, 100.0),
        *(0.0, 100.0, 100.0, math.hypot(100, 100)),
        *(200.0, 300.0, math.hypot(200, 100), math.hypot(300, 100)),
    ]


def test_national_rail_is_where_the_other_file_says_it_calls_or_does_not_hold_the_station(
    town: dict[FeatureId, Connected],
):
    """Tallowgate, where both call, Sable Reach, which the other file does not hold, and
    the tram stop. Pellam Cross is the Overground's alone, and is not counted."""
    assert town[RAIL].points == 3
    assert far(town[RAIL]) == [
        # The homes of a1 stand at a way in to Pellam Cross, and 200 metres from Tallowgate.
        *(200.0, 100.0, math.hypot(200, 100), math.hypot(100, 100)),
        *(0.0, 100.0, 100.0, math.hypot(100, 100)),
        *(math.hypot(100, 100), 100.0, 100.0, 0.0),
    ]
    assert "National Rail station or tram stop" in connected.MEASURES[RAIL].label


def test_a_tram_stop_counts_with_national_rail_and_is_told_by_the_national_file_alone(
    tmp_path: Path,
):
    made = built(given(tmp_path, [WAY_IN, PELLAM, TRAM, BUS_1]), RAIL)
    # Pellam Cross is the Overground's alone, so the tram stop is all that counts.
    assert made.points == 1
    assert made.of_oa[OAS[9]] == 100.0


def test_a_station_the_other_file_does_not_hold_is_a_national_rail_station(tmp_path: Path):
    made = built(given(tmp_path, [WAY_IN, SABLE, BUS_1], served=SERVED[:1]), RAIL)
    assert made.points == 1 and made.of_oa[OAS[11]] == 0.0
    with pytest.raises(LockError, match="it holds no stop that counts"):
        built(given(tmp_path / "again", [WAY_IN, SABLE, BUS_1], served=SERVED[:1]), OVERGROUND)


def test_the_nearest_within_a_distance_is_found_point_by_point_and_none_where_none_is_near():
    here = [(0.0, 0.0), (1_000.0, 0.0), (0.0, 150.0)]
    there = [(0.0, 200.0), (0.0, 100.0), (0.0, 100.0), (900.0, 0.0)]
    assert nearest_within(here, there, 200) == [1, 3, 0]
    assert nearest_within(here, there, 99) == [None, None, 0]
    assert nearest_within(here, [], 200) == [None, None, None]


def test_the_two_measures_of_railway_stations_are_left_out_where_no_file_of_stations_is_held(
    tmp_path: Path,
):
    inputs = given(tmp_path, served=None)
    for feature in (OVERGROUND, RAIL):
        with pytest.raises(LockError) as refused:
            built(inputs, feature)
        assert refused.value.rule == "input_has_one_receipt"
    # The other two read the national file alone.
    assert built(inputs, UNDERGROUND).points == 2 and built(inputs, BUS).points == 3


# The figures


def test_a_distance_is_the_median_over_an_areas_homes_to_the_nearest_ten_metres(
    town: dict[FeatureId, Connected],
):
    assert far(town[UNDERGROUND]) == [
        *(math.hypot(300, 0), math.hypot(200, 0), math.hypot(300, 50), math.hypot(200, 50)),
        *(100.0, 0.0, SLANT, 50.0),
        *(100.0, 200.0, SLANT, math.hypot(200, 50)),
    ]
    assert town[UNDERGROUND].worked == {
        # 260 homes at 200 and 206, and 240 at 300 and 304: half of the 500 are within 206.
        QUILLHAVEN_1: Worked(210.0, 4, 4, 1.0, State.PRESENT),
        # 160 homes at 0, 180 at 50, 150 at 100 and 170 at 112: half of the 660 are within 50.
        QUILLHAVEN_2: Worked(50.0, 4, 4, 1.0, State.PRESENT),
        # 190 homes at 100, 210 at 112, 200 at 200 and 220 at 206: half of the 820 are within 200.
        TALLOWGATE: Worked(200.0, 4, 4, 1.0, State.PRESENT),
    }


def test_the_stops_of_buses_are_counted_within_400_metres_and_one_at_400_is_within(
    town: dict[FeatureId, Connected],
):
    # Two stand on one spot, and are two stops on one spot. A bay and a stop that is not
    # active are none.
    assert town[BUS].points == 3
    assert connected.REACH == 400 and AT_THE_REACH.point == at(150, 450)
    # From the middle of a4: the two on its own spot, and the one at exactly 400 metres.
    assert town[BUS].of_oa[OAS[3]] == 3.0
    # From the middle of a3, 100 metres west: the stop to the north is 412 metres off.
    assert town[BUS].of_oa[OAS[2]] == 2.0
    # From the middle of c4, 400 metres east of the two: both are within, at the very reach.
    assert town[BUS].of_oa[OAS[11]] == 2.0
    assert town[BUS].of_oa[OAS[9]] == 0.0


def test_a_count_is_the_mean_over_an_areas_homes_to_one_decimal_place(
    town: dict[FeatureId, Connected],
):
    found = town[BUS].of_oa
    quillhaven = [
        found[oa] * homes for oa, homes in zip(OAS[:4], (110, 120, 130, 140), strict=True)
    ]
    assert town[BUS].worked[QUILLHAVEN_1].value == round(sum(quillhaven) / 500, 1)
    # Nought is a figure: the file is the whole country's, so no stop within reach is none.
    assert town[BUS].worked[TALLOWGATE].state is State.PRESENT
    assert min(found.values()) == 0.0


def test_how_many_stand_within_a_distance_is_counted_point_by_point():
    here, there = [(0.0, 0.0), (1_000.0, 0.0)], [(0.0, 400.0), (0.0, 400.1), (0.0, 0.0)]
    assert how_many_within(here, there, 400) == [2, 0]
    assert how_many_within(here, [], 400) == [0, 0] and how_many_within([], there, 400) == []


# The files


def test_a_row_far_away_that_names_no_grid_does_not_stop_the_build(
    town: dict[FeatureId, Connected],
):
    assert FAR.grid == "" and FAR in STOPS
    assert all(len(made.worked) == 3 for made in town.values())


def test_a_row_round_the_homes_of_the_build_that_names_no_grid_stops_it(tmp_path: Path):
    near = MadeUpStop("490000009A", "Coracle Row", "BCT", at(250, 50), grid="")
    with pytest.raises(LockError, match="a point is no point") as refused:
        built(given(tmp_path, [*STOPS, near]), BUS)
    assert refused.value.rule == "input_is_as_described"


def test_the_build_stops_where_the_file_holds_no_stop_of_the_kind(tmp_path: Path):
    with pytest.raises(LockError, match="it holds no stop that counts"):
        built(given(tmp_path, [PELLAM_WAY_IN, BUS_1]), UNDERGROUND)


def test_the_file_is_read_within_a_box_round_the_homes_and_no_home_may_be_further_than_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    box = connected.box_round([(0.0, 0.0), (100.0, 50.0)], 25.0)
    assert box == (-25.0, -25.0, 125.0, 75.0)
    # Read only 150 metres wide of the homes, the homes of a1 are further than that from the
    # one station that is left: a nearer one could stand outside what was read.
    monkeypatch.setattr(connected, "MARGIN", 150)
    with pytest.raises(LockError, match="its stops do not reach the homes of the build"):
        built(given(tmp_path, [WAY_IN, BUS_1]), UNDERGROUND)


def test_the_national_file_is_told_from_the_file_of_london_by_its_name(tmp_path: Path):
    assert connected.is_the_file(NATIONAL) and not connected.is_the_file("490Stops.csv")
    assert stops_file.is_the_file("490Stops.csv") and not stops_file.is_the_file(NATIONAL)
    with pytest.raises(LockError) as refused:
        built(inputs_of(tmp_path, stops_csv(STOPS)), BUS)
    assert refused.value.rule == "input_has_one_receipt"


def test_no_name_is_read_of_a_stop_or_of_a_station(tmp_path: Path):
    read = read_as([stop for stop in STOPS if stop is not FAR], tmp_path)
    assert len(read) == 13 and all(stop.name is None for stop in read)
    served = tfl_stations.open_the_file(given(tmp_path / "stations"), Use.SCORING)
    assert CANARY not in repr(read) + repr(tfl_stations.read(served))


# The rows of the catalogue, and the evidence


@pytest.mark.parametrize("feature", connected.MEASURES)
def test_each_row_of_the_catalogue_is_cores_and_says_a_straight_line(
    feature: FeatureId, town: dict[FeatureId, Connected]
):
    metric = town[feature].metric
    assert says_what_core_says(metric)
    assert metric.rankable is (feature is not BUS)
    assert metric.label == FEATURES[feature].label and "traight" in metric.label
    assert "walk" not in metric.label.lower()
    assert (metric.native_resolution, metric.vintage) == (NativeResolution.POINT, SAVED)
    assert f"retrieved on {SAVED}" in metric.definition and "{" not in metric.definition
    assert metric.source_ids == tuple(sorted({r.source_id for r in town[feature].files}))


def test_a_distance_is_in_metres_and_less_is_better_and_a_count_is_a_count():
    for feature in (UNDERGROUND, OVERGROUND, RAIL):
        assert (FEATURES[feature].unit, FEATURES[feature].polarity) == ("m", Polarity.LESS)
        assert NEVER_A_TRADE_OFF[feature] == 800
        assert connected.MEASURES[feature].method is park_proximity.STRAIGHT_LINE
    assert (FEATURES[BUS].unit, FEATURES[BUS].polarity) == ("count", Polarity.MORE)
    assert connected.WITHIN.parameters["metres"] == 400


def test_the_three_distances_are_parts_of_well_connected_and_the_stops_of_buses_are_shown():
    recipe = {term.feature_id: term.hundredths for term in TAGS[TagId.WELL_CONNECTED].terms}
    routes = FeatureId.BUS_ROUTES_NEARBY
    assert recipe == {UNDERGROUND: 45, OVERGROUND: 20, RAIL: 15, routes: 20}
    # The stops of buses are shown, and a wish for buses is ranked on the routes.
    assert RANKED_AS[BUS] is routes and BUS not in recipe
    assert set(connected.MEASURES) == {UNDERGROUND, OVERGROUND, RAIL, BUS}
    for of in connected.MEASURES.values():
        said = " ".join(of.cannot_see)
        assert "how often" in said or "how many routes" in said


@pytest.mark.parametrize("feature", connected.MEASURES)
def test_a_row_of_evidence_names_the_files_it_was_worked_out_from(
    feature: FeatureId, town: dict[FeatureId, Connected]
):
    made = town[feature]
    of_the_stops = [r for r in made.files if r.source_id == connected.SOURCE]
    assert [receipt.publisher_file for receipt in of_the_stops] == [NATIONAL]
    # The two measures of railway stations rest on the file of stations too, and cite it.
    of_the_stations = [r.publisher_file for r in made.files if r.source_id == connected.STATIONS]
    joined = feature in (OVERGROUND, RAIL)
    assert of_the_stations == ([tfl_stations.FILE] if joined else [])
    assert (connected.STATIONS in made.metric.source_ids) == joined
    assert [row.value for row in made.rows] == [made.worked[area].value for area in AREAS]
    assert {row.derivation_id for row in made.rows} == {
        connected.MEASURES[feature].method.derivation_id
    }
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=connected.METHODS[feature],
        receipts=made.files,
        rows=made.rows,
    )
    assert len(evidence.rows) == 3


def test_the_four_are_on_the_list_of_a_build_and_are_held_to_the_national_file():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    behind = measures.behind()
    for feature, of in connected.MEASURES.items():
        assert listed[feature].source == connected.SOURCE
        assert listed[feature].cannot_see == of.cannot_see
        assert not listed[feature].waits_on and not listed[feature].held_back
        assert behind[feature].reads(NATIONAL) and not behind[feature].reads("490Stops.csv")
