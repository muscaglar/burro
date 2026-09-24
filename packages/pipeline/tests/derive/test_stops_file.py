"""The file of stops, from the publisher's rows to the ways in and the stations they gather into.

Every file here is made up: `stops_support.py` writes it, with the publisher's
43 columns. Each test says what the reader does with one kind of row, and what
it never reads.
"""

from collections.abc import Iterator, Sequence
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import pytest
from burro_pipeline.derive import stops_file
from burro_pipeline.derive.stops_file import Station, Stop
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Opened
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held
from .stops_support import (
    BAY,
    BUS,
    CANARY,
    COLUMNS,
    PELLAM,
    PIER,
    SABLE,
    SHUT,
    STOPS,
    TALLOW,
    TRAM,
    UNDER,
    WAY_1,
    WAY_2,
    MadeUpStop,
    at,
    inputs_of,
    stops_csv,
)


def opened_of(folder: Path, stops: Sequence[MadeUpStop] = STOPS, use: Use = Use.SCORING) -> Opened:
    return stops_file.open_the_file(inputs_of(folder, stops_csv(stops)), use)


def ways_in(folder: Path, stops: Sequence[MadeUpStop] = STOPS) -> tuple[Stop, ...]:
    return stops_file.read(opened_of(folder, stops), stops_file.STATION_TYPES, names=True)


def refused(folder: Path, stops: Sequence[MadeUpStop]) -> str:
    with pytest.raises(LockError) as error:
        ways_in(folder, stops)
    assert error.value.rule == "input_is_as_described"
    return str(error.value)


# What is read


def test_the_ways_in_to_a_station_are_the_rows_of_two_types(tmp_path: Path):
    found = ways_in(tmp_path)
    assert [(way.code, way.type, way.name, way.point) for way in found] == [
        ("4900PELLAMX1", "RSE", PELLAM, at(50, 150)),
        ("4900PELLAMX2", "RSE", PELLAM, at(50, 50)),
        ("4900ZZCRSBR1", "TMU", SABLE, at(550, 250)),
        ("4900ZZLUTLG1", "TMU", TALLOW, at(350, 100)),
    ]
    assert stops_file.STATION_TYPES == ("RSE", "TMU")


def test_a_pier_and_a_stop_of_a_bus_are_no_way_in_to_a_station(tmp_path: Path):
    codes = {way.code for way in ways_in(tmp_path)}
    assert not codes & {PIER.code, BUS.code, BAY.code}


def test_a_row_that_is_not_active_is_left_out(tmp_path: Path):
    assert SHUT.code not in {way.code for way in ways_in(tmp_path)}
    pending = replace(SHUT, status="pending")
    assert SHUT.code not in {way.code for way in ways_in(tmp_path / "pending", [WAY_1, pending])}


def test_the_stops_of_a_bus_are_read_when_they_are_asked_for(tmp_path: Path):
    found = stops_file.read(opened_of(tmp_path), stops_file.BUS_TYPES)
    assert [(stop.code, stop.type, stop.name) for stop in found] == [
        (BUS.code, "BCT", None),
        (BAY.code, "BCS", None),
    ]


def test_the_rows_are_handed_over_in_the_order_of_their_codes(tmp_path: Path):
    turned = ways_in(tmp_path, list(reversed(STOPS)))
    assert turned == ways_in(tmp_path / "again")


def test_it_is_the_file_of_london_and_of_no_other_authority():
    assert stops_file.is_the_file("490Stops.csv")
    for name in ("Stops.csv", "910Stops.csv", "490Stops.xml", "490stops.csv", "4900Stops.csv"):
        assert not stops_file.is_the_file(name)


def test_the_file_of_another_authority_is_not_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, name="910Stops.csv")
    with pytest.raises(LockError) as error:
        stops_file.open_the_file(inputs, Use.SCORING)
    assert error.value.rule == "input_has_one_receipt"


# What is never read


@pytest.fixture
def asked(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, ...]]:
    """The columns each reading of a table asked for."""
    columns: list[tuple[str, ...]] = []
    rows = Opened.rows

    def spy(self: Opened, text: TextIO, named: Sequence[str]) -> Iterator[dict[str, str]]:
        columns.append(tuple(named))
        return rows(self, text, named)

    monkeypatch.setattr(Opened, "rows", spy)
    return columns


def test_seven_columns_are_read_by_name_and_no_other(tmp_path: Path, asked: list[tuple[str, ...]]):
    ways_in(tmp_path)
    assert asked == [
        ("ATCOCode", "CommonName", "StopType", "Status", "GridType", "Easting", "Northing")
    ]
    assert set(asked[0]) < set(COLUMNS) and len(COLUMNS) == 43


def test_a_step_that_needs_no_name_reads_none(tmp_path: Path, asked: list[tuple[str, ...]]):
    found = stops_file.read(opened_of(tmp_path), stops_file.STATION_TYPES)
    assert asked == [("ATCOCode", "StopType", "Status", "GridType", "Easting", "Northing")]
    assert {way.name for way in found} == {None}


def test_nothing_of_a_column_that_is_not_named_is_handed_over(tmp_path: Path):
    assert CANARY.encode() in stops_csv()
    found = ways_in(tmp_path)
    assert CANARY not in repr(found) and CANARY not in repr(stops_file.stations_of(found))


def test_a_file_that_lacks_a_column_that_is_read_stops_the_build(tmp_path: Path):
    for number, column in enumerate(stops_file.NAMED):
        without = [name for name in COLUMNS if name != column]
        opened = stops_file.open_the_file(
            inputs_of(tmp_path / str(number), stops_csv(columns=without)), Use.SCORING
        )
        with pytest.raises(LockError) as error:
            stops_file.read(opened, stops_file.STATION_TYPES, names=True)
        assert error.value.rule == "input_is_as_described"


def test_the_gate_is_asked_for_the_use_the_step_puts_the_file_to(tmp_path: Path):
    for number, use in enumerate((Use.SCORING, Use.DESTINATION_SEARCH, Use.ROUTING, Use.DISPLAY)):
        assert opened_of(tmp_path / str(number), use=use).receipt.source_id == "dft-naptan"
    for number, use in enumerate((Use.GAZETTEER, Use.CELLS)):
        with pytest.raises(LockError) as error:
            opened_of(tmp_path / f"refused-{number}", use=use)
        assert error.value.rule == "gate_refuses"


def test_the_store_is_never_written_to(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    stops_file.read(stops_file.open_the_file(inputs, Use.SCORING), stops_file.STATION_TYPES)
    assert held(tmp_path / "store") == before


# What the file is held to


@pytest.mark.parametrize(
    ("old", "new", "why"),
    [
        (WAY_1, replace(WAY_1, type="XYZ"), "a type is not known"),
        (PIER, replace(PIER, type=""), "a type is not known"),
        (PIER, replace(PIER, type="rse"), "a type is not known"),
        (BUS, replace(BUS, status="Active"), "a status is not known"),
        (WAY_1, replace(WAY_1, status=""), "a status is not known"),
        (WAY_2, replace(WAY_2, code=WAY_1.code), "a code stands twice or not at all"),
        (BUS, replace(BUS, code=WAY_1.code), "a code stands twice or not at all"),
        (SHUT, replace(SHUT, code=WAY_1.code), "a code stands twice or not at all"),
        (WAY_1, replace(WAY_1, code=""), "a code stands twice or not at all"),
        (WAY_1, replace(WAY_1, name="  "), "a stop has no name"),
        (WAY_1, replace(WAY_1, grid="ITM"), "a point is no point"),
        (WAY_1, replace(WAY_1, grid=""), "a point is no point"),
        (WAY_1, replace(WAY_1, point=("", "")), "a point is no point"),
        (WAY_1, replace(WAY_1, point=("nan", "400150")), "a point is no point"),
        (WAY_1, replace(WAY_1, point=("inf", "400150")), "a point is no point"),
        (WAY_1, replace(WAY_1, point=(-1.0, 400150.0)), "a point is no point"),
        (WAY_1, replace(WAY_1, point=(700050.0, -1.0)), "a point is no point"),
        (WAY_1, replace(WAY_1, point=("0.1E", "400150")), "a point is no point"),
    ],
)
def test_a_row_that_is_not_as_the_guide_describes_stops_the_build(
    tmp_path: Path, old: MadeUpStop, new: MadeUpStop, why: str
):
    said = refused(tmp_path, [new if one is old else one for one in STOPS])
    assert why in said and CANARY not in said and PELLAM not in said


def test_the_point_of_a_row_that_is_not_read_is_never_looked_at(tmp_path: Path):
    """A pier on another grid, and a way in that is shut and has no point, stop nothing."""
    rows = [WAY_1, replace(PIER, grid="ITM"), replace(SHUT, point=("", ""))]
    assert [way.code for way in ways_in(tmp_path, rows)] == [WAY_1.code]


def test_a_file_with_no_stop_that_is_read_stops_the_build(tmp_path: Path):
    assert "it holds no stop that is read" in refused(tmp_path, [PIER, BUS, SHUT])


def test_a_type_that_is_asked_for_is_one_the_guide_names(tmp_path: Path):
    with pytest.raises(ValueError, match="a type that is asked for"):
        stops_file.read(opened_of(tmp_path), ("RSE", "XYZ"))


def test_every_type_that_is_read_is_one_the_guide_names_and_is_called_something():
    read = (*stops_file.STATION_TYPES, *stops_file.BUS_TYPES)
    assert set(read) <= stops_file.TYPES and set(stops_file.CALLED) == set(read)
    assert len(stops_file.TYPES) == 23


# How rows are gathered into one station


def way(code: str, name: str, east: float, north: float, kind: str = "RSE") -> Stop:
    return Stop(code, kind, at(east, north), name)


def test_the_ways_in_of_one_kind_that_share_a_name_are_one_station(tmp_path: Path):
    found = stops_file.stations_of(ways_in(tmp_path))
    assert [(one.type, one.name, len(one.ways_in)) for one in found] == [
        ("RSE", PELLAM, 2),
        ("TMU", SABLE, 1),
        ("TMU", TALLOW, 1),
    ]


def test_a_railway_station_and_an_underground_station_of_one_name_are_two():
    rows = [way("4900FOXHOLT1", "Foxholt", 0, 0), way("4900ZZLUFOX1", "Foxholt", 10, 0, "TMU")]
    found = stops_file.stations_of(rows)
    assert [(one.type, one.name) for one in found] == [("RSE", "Foxholt"), ("TMU", "Foxholt")]


def test_two_ways_in_of_one_name_that_stand_far_apart_are_two_stations():
    """Each way in stands within 1,000 metres of another of its station, and no further."""
    rows = [
        way("4900WEXMOOR1", "Wexmoor", 0, 0),
        way("4900WEXMOOR2", "Wexmoor", 1_000, 0),
        way("4900WEXMOOR3", "Wexmoor", 2_000, 0),
        way("2400WEXMOOR1", "Wexmoor", 3_001, 0),
    ]
    found = stops_file.stations_of(rows)
    assert [[each.code for each in one.ways_in] for one in found] == [
        ["2400WEXMOOR1"],
        ["4900WEXMOOR1", "4900WEXMOOR2", "4900WEXMOOR3"],
    ]
    assert stops_file.APART == 1_000


def test_a_way_in_between_two_groups_joins_them():
    rows = [
        way("4900EAST1", "Eskerfold", 1_600, 0),
        way("4900WEST1", "Eskerfold", 0, 0),
        way("4900MIDDLE1", "Eskerfold", 800, 0),
    ]
    (found,) = stops_file.stations_of(rows)
    assert [each.code for each in found.ways_in] == ["4900EAST1", "4900MIDDLE1", "4900WEST1"]


def test_the_stations_are_the_same_in_whatever_order_the_rows_come(tmp_path: Path):
    found = ways_in(tmp_path)
    assert stops_file.stations_of(reversed(found)) == stops_file.stations_of(found)


def test_a_station_has_the_middle_of_its_ways_in_for_its_point(tmp_path: Path):
    first, *_ = stops_file.stations_of(ways_in(tmp_path))
    assert (first.middle, first.wide) == (at(50, 100), 100.0)
    odd = Station("RSE", "Wexmoor", (way("1", "Wexmoor", 0, 0), way("2", "Wexmoor", 1, 1)))
    # To the metre, with a half taken upward.
    assert odd.middle == at(1, 1)


def test_the_letters_of_a_code_are_a_hint_and_are_read_only_where_a_code_holds_them():
    assert stops_file.letters_of("4900ZZLUTLG1") == "LU"
    assert stops_file.letters_of("4900ZZCRSBR1") == "CR"
    for code in ("4900PELLAMX1", "490000001A", "4900ZZ", "ZZLUTLG1", "4900zzluTLG1", ""):
        assert stops_file.letters_of(code) is None
    assert set(stops_file.SEEN_TO_BE) == {"LU", "DL", "CR", "AL"}


def test_a_station_whose_codes_hold_two_kinds_of_letters_is_given_none():
    agree = Station("TMU", TALLOW, (way("4900ZZLUTLG1", TALLOW, 0, 0, "TMU"),))
    some = Station(
        "TMU",
        TALLOW,
        (way("4900TLG2", TALLOW, 0, 0, "TMU"), way("4900ZZLUTLG1", TALLOW, 0, 0, "TMU")),
    )
    mixed = Station(
        "TMU",
        TALLOW,
        (way("4900ZZDLTLG1", TALLOW, 0, 0, "TMU"), way("4900ZZLUTLG1", TALLOW, 0, 0, "TMU")),
    )
    assert (agree.letters, some.letters, mixed.letters) == ("LU", "LU", None)


def test_a_station_is_gathered_from_ways_in_that_have_a_name(tmp_path: Path):
    unnamed = stops_file.read(opened_of(tmp_path), stops_file.STATION_TYPES)
    with pytest.raises(ValueError, match="ways in that have a name"):
        stops_file.stations_of(unnamed)
    with pytest.raises(ValueError, match="ways in that have a name"):
        stops_file.stations_of([Stop(BUS.code, "BCT", at(0, 0), "Coracle Row")])


def test_the_registry_allows_the_file_for_each_use_a_station_is_put_to(tmp_path: Path):
    """Scoring for the distance, search for a place, routing and display for a journey."""
    given: Registry = inputs_of(tmp_path).registry
    source = given.require("dft-naptan", Use.SCORING)
    assert {Use.SCORING, Use.DESTINATION_SEARCH, Use.ROUTING, Use.DISPLAY} <= set(source.uses)
    assert UNDER.code.startswith("4900") and TRAM.code.startswith("4900")
    assert WAY_2.name == PELLAM
