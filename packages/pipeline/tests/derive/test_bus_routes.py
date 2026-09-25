"""How many routes of a bus stop near home, on a made-up file of the stops of routes.

Every route and every stop here is made up. The tests of cells draw the town,
and the centre of each output area is put in the very middle of its square, so
each figure can be worked out by hand.

    columns  0    1    2    3    4    5
    row 1  | a1 | a2 | b1 | b2 | c1 | c2 |
    row 0  | a3 | a4 | b3 | b4 | c3 | c4 |

    Quillhaven 001   homes 110, 120, 130, 140   in a1, a2, a3 and a4
    Quillhaven 002   homes 150, 160, 170, 180   in b1, b2, b3 and b4
    Tallowgate 001   homes 190, 200, 210, 220   in c1, c2, c3 and c4

    Stop 1   at the middle of a3          routes 7, 12 and N7
    Stop 2   400 metres north of stop 1   route 12 again, and route 40
    Stop 3   400 metres east of the middle of c4   route 40, and what is no route of its own
"""

import csv
import hashlib
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, RANKED_AS, TAGS
from burro_core.ids import FeatureId, NativeResolution, Polarity, TagId
from burro_pipeline.cells import spine
from burro_pipeline.derive import bus_routes, measures
from burro_pipeline.derive.bus_routes import Nearby, is_a_route
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.station_shapes import which_within
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .stops_support import AREAS, CANARY, OAS, QUILLHAVEN_1, TALLOWGATE, at, inputs_of

NAME = "Data_3rdParties_bus-sequences-20251003.csv"
DAY = "2025-10-03"
COLUMNS = (
    "Route",
    "Run",
    "Sequence",
    "Stop_Code_LBSL",
    "Bus_Stop_Code",
    "Naptan_Atco",
    "Stop_Name",
    "Location_Easting",
    "Location_Northing",
    "Heading",
    "Virtual_Bus_Stop",
)


@dataclass(frozen=True)
class Call:
    """One row of the file: a route calls at a stop."""

    route: str
    stop: str
    point: tuple[object, object]
    virtual: str = "0"
    run: int = 1


ONE, TWO, THREE = at(50, 50), at(50, 450), at(950, 50)
CALLS = (
    Call("7", "S1", ONE),
    # The same route the other way, and again at the same stop: it is one route.
    Call("7", "S1", ONE, run=2),
    Call("12", "S1", ONE),
    Call("N7", "S1", ONE),
    Call("12", "S2", TWO),
    Call("40", "S2", TWO),
    Call("40", "S3", THREE),
    # A bus that stands in for a line that is shut, and route 7 sent another way.
    Call("UL3", "S3", THREE),
    Call("TR2", "S3", THREE),
    Call("DL11", "S3", THREE),
    Call("Y7", "S3", THREE),
    # A pier and a tram stop: the file marks each as no stop.
    Call("RB1", "P1", at(550, 150), virtual="1"),
    Call("T1", "T1", at(550, 150), virtual="1"),
)


def sequences(calls: Sequence[Call] = CALLS) -> bytes:
    """The made-up file, as the publisher lays it out, with a mark at its start."""
    text = io.StringIO(newline="")
    table = csv.writer(text, lineterminator="\r\n")
    table.writerow(COLUMNS)
    for at_, call in enumerate(calls, start=1):
        east, north = call.point
        row = [call.route, call.run, at_, call.stop, "NONE", "", CANARY, east, north, "90"]
        table.writerow([*row, call.virtual])
    return b"\xef\xbb\xbf" + text.getvalue().encode("utf-8")


def receipt_of(content: bytes, name: str = NAME) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=bus_routes.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at="2026-09-24T00:00:00Z",
        how=How.FETCHED,
        edition="20251003",
        data_period=Period(as_at=DAY),
    )


def given(folder: Path, calls: Sequence[Call] = CALLS) -> Inputs:
    content = sequences(calls)
    return inputs_of(folder, more=[(receipt_of(content), content)])


def built(inputs: Inputs) -> Nearby:
    return bus_routes.build(inputs, spine.build(inputs))


@pytest.fixture(scope="module")
def town(tmp_path_factory: pytest.TempPathFactory) -> Nearby:
    return built(given(tmp_path_factory.mktemp("town")))


# What counts


def test_a_route_counts_once_however_many_of_its_stops_are_near_and_whichever_way_it_runs(
    town: Nearby,
):
    # From the middle of a3: stop 1 is on the spot and stop 2 is at exactly 400 metres.
    # Routes 7, 12 and N7 call at the first, and 12 and 40 at the second: four routes.
    assert town.of_oa[OAS[2]] == 4
    # From the middle of a4, 100 metres east: stop 2 is 412 metres off, and three are left.
    assert town.of_oa[OAS[3]] == 3
    assert (town.stops, town.routes) == (3, 4)


def test_a_night_route_is_a_route_of_its_own():
    every = frozenset({"7", "N7", "12"})
    assert is_a_route("N7", every) and is_a_route("7", every)
    assert is_a_route("148X", every) and is_a_route("SL8", every) and is_a_route("W15", every)


@pytest.mark.parametrize("name", ["UL3", "UL12", "TR2", "DL11"])
def test_a_bus_that_stands_in_for_a_line_that_is_shut_is_no_route(name: str):
    assert not is_a_route(name, frozenset({name, "7"}))


def test_a_route_sent_another_way_is_no_route_of_its_own_where_the_file_holds_the_route():
    assert not is_a_route("Y7", frozenset({"Y7", "7"}))
    assert not is_a_route("Y18N", frozenset({"Y18N", "18N"}))
    # Where the file holds no route of that name, it is a route like any other.
    assert is_a_route("Y7", frozenset({"Y7", "12"}))


def test_what_is_no_route_of_its_own_adds_nothing_near_a_home(town: Nearby):
    """At stop 3 call route 40, three that stand in for a line, and route 7 sent another way."""
    # The homes of c4 are at exactly 400 metres from stop 3, and 500 from stop 1.
    assert town.of_oa[OAS[11]] == 1
    # The homes of c2 are 100 metres from a pier and a tram stop, which are marked as no
    # stop, and 412 from stop 3.
    assert town.of_oa[OAS[9]] == 0


def test_a_stop_that_is_marked_as_virtual_is_no_stop(tmp_path: Path):
    only = built(given(tmp_path, [Call("7", "S1", ONE), Call("9", "V1", THREE, virtual="1")]))
    assert (only.stops, only.routes) == (1, 1)
    # The homes of c4 are 400 metres from what is no stop, and 500 from the one that is.
    assert only.of_oa[OAS[11]] == 0


# The figure


def test_the_figure_is_the_mean_over_an_areas_homes_to_one_decimal_place(town: Nearby):
    assert [town.of_oa[oa] for oa in OAS[:4]] == [4, 4, 4, 3]
    # 110, 120 and 130 homes with four routes, and 140 with three: 1,860 over 500.
    assert town.worked[QUILLHAVEN_1].value == 3.7
    # The homes of c3 are at exactly 400 metres from stop 1, and those of c4 from stop 3.
    assert [town.of_oa[oa] for oa in OAS[8:]] == [0, 0, 3, 1]
    # 210 homes with three routes and 220 with one: 850 over 820.
    assert town.worked[TALLOWGATE].value == 1.0


def test_nought_is_a_figure(tmp_path: Path):
    far = built(given(tmp_path, [Call("7", "S2", TWO)]))
    assert [far.of_oa[oa] for oa in OAS[8:]] == [0, 0, 0, 0]
    assert far.worked[TALLOWGATE].value == 0.0
    assert far.worked[TALLOWGATE].state is State.PRESENT


def test_which_stand_within_a_distance_are_found_point_by_point():
    here, there = [(0.0, 0.0), (1_000.0, 0.0)], [(0.0, 400.0), (0.0, 400.1), (0.0, 0.0)]
    assert which_within(here, there, 400) == [[0, 2], []]
    assert which_within(here, [], 400) == [[], []] and which_within([], there, 400) == []


# The file


def test_the_file_is_known_by_the_publishers_name_for_it_whatever_day_it_is_of():
    assert bus_routes.is_the_file(NAME)
    assert bus_routes.is_the_file("Data_3rdParties_bus-sequences-20260102.csv")
    assert not bus_routes.is_the_file("Data_3rdParties_bus-stops-20251003.csv")
    assert not bus_routes.is_the_file("stop-sequences-example.csv")


def test_no_name_is_read(town: Nearby, tmp_path: Path):
    content = sequences()
    assert CANARY.encode() in content
    inputs = inputs_of(tmp_path, more=[(receipt_of(content), content)])
    opened = inputs.open(bus_routes.SOURCE, Use.SCORING, named=bus_routes.is_the_file)
    assert CANARY not in repr(bus_routes.read(opened)) + repr(town.rows)


@pytest.mark.parametrize(
    ("calls", "why"),
    [
        ([Call("7", "S1", ("east", 50))], "a point is no point"),
        ([Call("7", "S1", (0, 50))], "a point is no point"),
        ([Call("7", "S1", ONE), Call("12", "S1", TWO)], "a stop stands in two places"),
        ([Call("7", "S1", ONE, virtual="yes")], "a stop is not said to be one or not"),
        ([Call("", "S1", ONE)], "a row names no route or no stop"),
        ([Call("9", "V1", ONE, virtual="1")], "it holds no stop that counts"),
    ],
)
def test_a_file_that_is_not_as_the_reader_was_written_to_read_stops_the_build(
    tmp_path: Path, calls: list[Call], why: str
):
    with pytest.raises(LockError, match=why) as refused:
        built(given(tmp_path, calls))
    assert refused.value.rule == "input_is_as_described"


def test_a_build_with_no_file_of_routes_cannot_work_the_measure_out(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(inputs_of(tmp_path))
    assert refused.value.rule == "input_has_one_receipt"


# The row of the catalogue, and the evidence


def test_the_row_of_the_catalogue_is_cores_and_is_dated_by_the_day_the_file_is_of(town: Nearby):
    metric = town.metric
    assert says_what_core_says(metric)
    assert metric.label == FEATURES[FeatureId.BUS_ROUTES_NEARBY].label == bus_routes.LABEL
    assert (metric.unit, metric.polarity) == ("count", Polarity.MORE)
    assert (metric.native_resolution, metric.vintage) == (NativeResolution.POINT, DAY)
    assert f"as at {DAY}" in metric.definition and "{" not in metric.definition
    assert metric.rankable is True
    assert bus_routes.SOURCE in metric.source_ids


def test_a_wish_for_buses_is_ranked_on_the_routes_and_the_stops_are_shown():
    assert RANKED_AS[FeatureId.BUS_STOPS_NEARBY] is FeatureId.BUS_ROUTES_NEARBY
    recipe = {term.feature_id: term.hundredths for term in TAGS[TagId.WELL_CONNECTED].terms}
    assert recipe[FeatureId.BUS_ROUTES_NEARBY] == 20
    assert FeatureId.BUS_STOPS_NEARBY not in recipe


def test_what_it_cannot_see_says_how_old_the_file_is_and_what_is_to_be_settled():
    said = " ".join(bus_routes.CANNOT_SEE)
    assert "3 October 2025" in said and "two weeks" in said
    assert "to be settled with Transport for London before launch" in said
    assert "how often a route runs" in said
    assert "Only the routes of London Buses are counted" in said


def test_a_row_of_evidence_names_the_file_of_routes_and_holds_the_figure(town: Nearby):
    of_the_source = [r for r in town.files if r.source_id == bus_routes.SOURCE]
    assert [receipt.publisher_file for receipt in of_the_source] == [NAME]
    assert [row.value for row in town.rows] == [town.worked[area].value for area in AREAS]
    assert {row.derivation_id for row in town.rows} == {bus_routes.METHOD.derivation_id}


def test_it_is_on_the_list_of_a_build_and_is_held_to_the_file_of_routes():
    listed = {measure.feature: measure for measure in measures.MEASURES}
    one = listed[FeatureId.BUS_ROUTES_NEARBY]
    assert (one.source, one.cannot_see) == (bus_routes.SOURCE, bus_routes.CANNOT_SEE)
    assert not one.waits_on and not one.held_back
    behind = measures.behind()[FeatureId.BUS_ROUTES_NEARBY]
    assert behind.reads(NAME) and not behind.reads("Data_3rdParties_bus-stops-20251003.csv")
