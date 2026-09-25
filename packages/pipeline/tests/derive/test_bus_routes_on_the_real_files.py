"""How many routes of a bus stop near home, worked out from the file as it was fetched.

Every other test of the measure runs on a made-up file. These read the real
one, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the file, the count of areas with a figure, and three
figures of the measure: London's lowest, middle and highest. None is said of a
named area or of a borough. Each was worked out on 2026-09-24, from the file of
3 October 2025.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.derive import bus_routes
from burro_pipeline.derive.bus_routes import Nearby, Routes
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .real_files import SKIPPED, real_inputs

pytestmark = SKIPPED
# The file of the stops of every route, by the id of its receipt.
ROUTES = "f-88fb691472e4"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def read(real: Inputs) -> Routes:
    opened = real.open(bus_routes.SOURCE, Use.SCORING, named=bus_routes.is_the_file)
    return bus_routes.read(opened)


@pytest.fixture(scope="module")
def made(real: Inputs) -> Nearby:
    return bus_routes.build(real, spine.build(real))


def test_the_file_is_of_3_october_2025_and_its_receipt_says_so(real: Inputs):
    receipt = real.open(bus_routes.SOURCE, Use.SCORING, named=bus_routes.is_the_file).receipt
    assert receipt.file_id == ROUTES
    assert receipt.publisher_file == "Data_3rdParties_bus-sequences-20251003.csv"
    assert (receipt.how, receipt.edition) == (How.FETCHED, "20251003")
    assert receipt.data_period == Period(as_at="2025-10-03")


def test_it_holds_684_routes_of_their_own_at_18867_stops(read: Routes):
    """Of the 798 names of a route the file holds. A pier and a tram stop are no stop, and a
    bus that stands in for a line, or a route sent another way, is no route of its own."""
    assert len(read.stops) == len(read.routes) == 18_867
    assert len(read.every_route) == 684
    assert not any(bus_routes.STANDS_IN.fullmatch(route) for route in read.every_route)
    # A night route is a route of its own.
    assert sum(1 for route in read.every_route if route.startswith("N")) == 62
    # The most routes of their own that call at one stop.
    assert max(len(routes) for routes in read.routes.values()) == 21


def test_every_one_of_the_1002_areas_has_a_figure(made: Nearby):
    assert (made.stops, made.routes) == (18_867, 684)
    assert len(made.worked) == 1_002
    assert Counter(worked.state for worked in made.worked.values()) == {State.PRESENT: 1_002}
    assert len(made.of_oa) == 26_369


def test_the_lowest_the_middle_and_the_highest_of_london(made: Nearby):
    values = sorted(w.value for w in made.worked.values() if w.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (0.9, 5.5, 30.1)
    of_oa = sorted(made.of_oa.values())
    assert (of_oa[0], statistics.median(of_oa), of_oa[-1]) == (0, 5, 50)
    # One output area in thirty has no route of London Buses within 400 metres.
    assert sum(1 for routes in of_oa if routes == 0) == 895


def test_the_row_of_the_catalogue_is_cores_and_is_dated_by_the_day_the_file_is_of(made: Nearby):
    assert says_what_core_says(made.metric)
    assert made.metric.vintage == "2025-10-03"
    assert "as at 2025-10-03" in made.metric.definition
    assert [r.file_id for r in made.files if r.source_id == bus_routes.SOURCE] == [ROUTES]
