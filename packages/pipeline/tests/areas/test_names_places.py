"""The readers of names: OS Open Names, the town centres, and the wards and boroughs.

Every file here is made up, in the publisher's own layout.
"""

from pathlib import Path

import pytest
from burro_pipeline.areas import names_centres, names_files, names_places, names_wards
from burro_pipeline.areas.names_places import Names
from burro_pipeline.evidence.lock import LockError

from ..cells.support import CANARY
from .names_support import (
    ALDERWICK,
    BOROUGHS,
    CENTRES,
    ESKERFOLD,
    FOXHOLT,
    HEADER,
    LINE,
    NAMES,
    OSIERHOLM,
    PLACES,
    STATIONS,
    TOWN_CENTRES,
    WARDS,
    Named,
    box_of,
    contents,
    given,
    held,
    middle,
    names_zip,
)

EVERYWHERE = (0.0, 0.0, 1_000_000.0, 1_000_000.0)
BY_NUMBER = {place.number: place for place in PLACES}


def read_names(folder: Path, content: bytes, ground: tuple[float, ...] = EVERYWHERE) -> Names:
    made = given(folder, contents() | {"names": content})
    west, south, east, north = ground
    return names_places.read(
        names_files.with_receipt(made.inputs, NAMES), (west, south, east, north)
    )


def test_every_populated_place_and_station_is_read_and_nothing_else(tmp_path: Path):
    found = read_names(tmp_path, names_zip())
    assert [(place.record_id, place.name, place.kind) for place in found.places] == sorted(
        (place.record_id, place.name, place.kind) for place in PLACES
    )
    assert {station.name for station in found.stations} == {each.name for each in STATIONS}
    assert found.tables == 2
    # Eleven places, three stations, seventy-three roads and one postcode.
    assert found.rows == 88


def test_a_table_with_no_header_is_read_by_the_names_the_zip_gives(tmp_path: Path):
    """The columns are found by name, so a file that gives them in another order reads the same."""
    turned = (*HEADER[10:], *HEADER[:10])
    as_given = read_names(tmp_path / "as-given", names_zip())
    assert read_names(tmp_path / "turned", names_zip(header=turned)) == as_given
    assert len(as_given.places) == len(PLACES)


def test_a_name_is_kept_exactly_as_the_file_writes_it(tmp_path: Path):
    odd = " St  Marrowfen\N{RIGHT SINGLE QUOTATION MARK}s-under-LARKSPUR "
    places = (Named(1, odd, "Hamlet", middle((0, 0)), box_of((0, 0)), second="  "),)
    found = read_names(tmp_path, names_zip(places, ()))
    assert [(place.name, place.second_name) for place in found.places] == [(odd, "  ")]


def test_a_postcode_is_never_read():
    """The registry asks that postcodes are dropped: they carry rights of their own."""
    found = held().names
    assert CANARY not in {record.name for record in (*found.places, *found.stations)}
    assert not any(" " in record.record_id for record in (*found.places, *found.stations))


def test_a_road_is_joined_to_its_settlement_by_its_address_and_never_by_its_name():
    roads = held().names.roads
    assert roads == {
        BY_NUMBER[ALDERWICK].uri: 60,
        BY_NUMBER[ESKERFOLD].uri: 3,
        BY_NUMBER[FOXHOLT].uri: 10,
    }


def test_only_what_lies_in_the_box_that_is_asked_about_is_kept(tmp_path: Path):
    found = read_names(tmp_path, names_zip(), box_of((0, 0), 2, 2))
    assert {place.name for place in found.places} == {"Alderwick"}
    assert {station.name for station in found.stations} == {"Alderwick"}
    # A road is counted wherever it lies: only the settlement it names is read.
    assert sum(found.roads.values()) == 73


def test_a_row_that_is_not_as_long_as_the_header_stops_the_step(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        read_names(tmp_path, names_zip(short_row=True))
    assert refused.value.rule == "input_is_as_described"
    assert CANARY not in str(refused.value)


def test_a_file_that_lacks_a_column_that_is_read_stops_the_step(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        read_names(tmp_path, names_zip(header=[name for name in HEADER if name != "NAME2"]))
    assert refused.value.rule == "input_is_as_described"


def test_a_box_is_what_the_file_gives_and_a_station_has_none():
    found = held().names
    alderwick = next(place for place in found.places if place.name == "Alderwick")
    assert alderwick.box == box_of((0, 0), 3, 3) and alderwick.hectares == 225.0
    assert all(station.box is None and station.hectares is None for station in found.stations)


# The town centres


def test_every_town_centre_is_read_with_its_name_and_its_class_as_written():
    found = held().centres
    assert [(centre.record_id, centre.name, centre.rank) for centre in found] == [
        (centre.record_id, centre.name, centre.rank) for centre in TOWN_CENTRES
    ]
    assert {centre.publisher for centre in found} == {"Greater London Authority"}


def test_a_centre_stands_on_its_own_point_only_where_its_outline_holds_the_point():
    by_id = {centre.record_id: centre for centre in held().centres}
    stray = by_id[OSIERHOLM]
    assert stray.point == middle((5, 2)) and not stray.point_is_inside
    assert stray.at == middle((7, 2))
    assert all(centre.at == centre.point for centre in by_id.values() if centre is not stray)


def test_a_class_with_another_word_beside_the_rank_is_read_as_district_and_says_so():
    ranks = {centre.rank: centre for centre in held().centres}
    assert ranks["District"].counts and not ranks["District"].rank_is_read
    assert ranks["Major"].counts
    assert ranks["District Centre"].counts and ranks["District Centre"].rank_is_read
    assert not ranks["Local Centre"].counts


def test_a_town_centre_with_no_name_stops_the_step(tmp_path: Path):
    from .names_support import Centred, centres_gpkg

    nameless = (Centred("TCB90000009", "", "District", box_of((0, 0))),)
    made = given(tmp_path, contents() | {"centres": centres_gpkg(nameless)})
    with pytest.raises(LockError) as refused:
        names_centres.read(names_files.without_receipt(made.inputs, CENTRES))
    assert refused.value.rule == "input_is_as_described"


# The wards and the boroughs


def test_the_wards_and_boroughs_of_london_are_told_by_the_files_own_code():
    wards, boroughs = held().wards, held().boroughs
    assert [(ward.record_id, ward.name) for ward in wards] == [
        (ward.code, ward.name) for ward in WARDS if ward.kind == "LBW"
    ]
    assert [(each.record_id, each.name) for each in boroughs] == [
        (each.code, each.name) for each in BOROUGHS if each.kind == "LBO"
    ]
    assert {ward.kind for ward in wards} == {"London Borough Ward"}
    assert CANARY not in " ".join(each.name for each in (*wards, *boroughs))


def test_a_layer_is_read_by_its_name_from_a_file_that_holds_several(tmp_path: Path):
    made = given(tmp_path)
    file = names_files.with_receipt(made.inputs, LINE)
    assert len(names_wards.read_wards(file)) == 4
    assert len(names_wards.read_boroughs(file)) == 2
