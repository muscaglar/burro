"""The stations as places a person can name, from the publisher's ways in to a row for each.

Every file here is made up: `stops_support.py` writes it. The names are ones
the synthetic release already holds, with the closing words the publisher's
file writes after a name.

The last tests hand the rows to core's own search, as a release would, to see
that the words a person types find the station. Core is not changed: the
places are given a journey's end that is made up, because no build makes one.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from burro_core.ids import PlaceKind
from burro_core.places import Names
from burro_core.release import Place, Release
from burro_pipeline.derive import station_places, stops_file
from burro_pipeline.derive.station_places import StationPlace
from burro_pipeline.derive.stops_file import Station, Stop
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import How
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Status, Use

from ..cells.support import registry
from .stops_support import (
    CANARY,
    PELLAM,
    SABLE,
    SAVED,
    STOPS,
    TALLOW,
    MadeUpStop,
    at,
    inputs_of,
    stops_csv,
)


def places(folder: Path, stops: Sequence[MadeUpStop] = STOPS) -> tuple[StationPlace, ...]:
    return station_places.build(inputs_of(folder, stops_csv(stops))).places


def station(name: str, kind: str = "RSE", code: str = "4900MADEUP1") -> Station:
    return Station(kind, name, (Stop(code, kind, at(0, 0), name),))


# The rows


def test_every_station_is_a_row_with_its_name_its_point_and_its_kind(tmp_path: Path):
    found = places(tmp_path)
    assert [(one.name, one.served, one.network, one.point) for one in found] == [
        (PELLAM, "rail", None, at(50, 100)),
        (SABLE, "tram_metro_underground", "tram", at(550, 250)),
        (TALLOW, "tram_metro_underground", "underground", at(350, 100)),
    ]
    assert {one.kind for one in found} == {PlaceKind.STATION}
    assert {one.source_id for one in found} == {"dft-naptan"}


def test_the_name_is_the_files_own_and_is_never_changed(tmp_path: Path):
    written = [one.name for one in STOPS if one.type in ("RSE", "TMU")]
    assert {one.name for one in places(tmp_path)} == set(written)


def test_a_row_names_the_code_of_each_way_in_and_its_id_is_made_from_the_first(tmp_path: Path):
    first, second, third = places(tmp_path)
    assert first.codes == ("4900PELLAMX1", "4900PELLAMX2")
    assert (first.place_id, second.place_id) == ("lon-p4900pellamx1", "lon-p4900zzcrsbr1")
    assert third.place_id == "lon-p4900zzlutlg1"


def test_the_point_is_the_middle_of_the_ways_in_and_is_given_both_ways(tmp_path: Path):
    first, *_ = places(tmp_path)
    assert first.point == at(50, 100)
    # The made-up town stands in the North Sea, east of the meridian.
    longitude, latitude = first.centroid
    assert 2 < longitude < 3 and 53 < latitude < 54
    assert (round(longitude, 6), round(latitude, 6)) == first.centroid


def test_a_row_that_is_not_active_or_is_no_station_makes_no_place(tmp_path: Path):
    found = places(tmp_path)
    assert len(found) == 3
    assert "Sable Reach Pier" not in {one.name for one in found}
    assert "4900PELLAMX3" not in {code for one in found for code in one.codes}


def test_nothing_of_a_column_that_is_not_named_is_in_a_row(tmp_path: Path):
    assert CANARY not in repr(places(tmp_path))


def test_the_rows_say_when_the_file_was_saved_and_that_a_person_saved_it(tmp_path: Path):
    made = station_places.build(inputs_of(tmp_path))
    assert (made.saved, made.file.how, made.file.source_id) == (SAVED, How.BY_HAND, "dft-naptan")


# The gate


def test_the_gate_is_asked_for_destination_search():
    assert station_places.USE is Use.DESTINATION_SEARCH
    source = registry().require("dft-naptan", station_places.USE)
    assert source.status is Status.APPROVED


def test_a_registry_that_does_not_allow_the_search_stops_it_before_the_file_is_read(
    tmp_path: Path,
):
    sources = [
        source.model_copy(update={"uses": (Use.SCORING, Use.DISPLAY)})
        if source.id == station_places.SOURCE
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, given=Registry(tuple(sources)))
    with pytest.raises(LockError) as error:
        station_places.build(inputs)
    assert error.value.rule == "gate_refuses"
    assert inputs.opened == ()


# What a person may type


@pytest.mark.parametrize(
    ("name", "aliases"),
    [
        ("Tallowgate", ("Tallowgate station",)),
        ("Pellam Cross Station", ("Pellam Cross",)),
        ("Foxholt Rail Station", ("Foxholt", "Foxholt station")),
        ("Wexmoor Underground Station", ("Wexmoor", "Wexmoor station")),
        ("Wexmoor Overground Station", ("Wexmoor", "Wexmoor station")),
        ("Osierholm DLR Station", ("Osierholm", "Osierholm station")),
        ("Osierholm Station DLR", ("Osierholm", "Osierholm station")),
        ("Osierholm DLR", ("Osierholm", "Osierholm station")),
        ("Sable Reach Tram Stop", ("Sable Reach", "Sable Reach station")),
        # The closing words are taken off once: the station in the name is part of it.
        (
            "Kindlewharf Power Station Underground Station",
            ("Kindlewharf Power Station", "Kindlewharf Power Station station"),
        ),
        # A name that is only closing words is kept whole.
        ("Station", ("Station station",)),
        # A sign a person writes as a word.
        (
            "Eskerfold & Foxholt Station",
            ("Eskerfold & Foxholt", "Eskerfold and Foxholt", "Eskerfold and Foxholt station"),
        ),
        # Words in brackets are part of the name, and nothing is taken off after them.
        ("Cindermoor (Birch line)", ("Cindermoor (Birch line) station",)),
    ],
)
def test_an_alias_is_the_name_without_its_closing_words_and_with_station(
    name: str, aliases: tuple[str, ...]
):
    assert station_places.aliases_of(name) == aliases


def test_an_alias_is_never_spelt_as_the_name_or_as_another_alias_of_it(tmp_path: Path):
    for one in places(tmp_path):
        spelt = [station_places.normalise(each) for each in (one.name, *one.aliases)]
        assert len(set(spelt)) == len(spelt) and all(spelt)


def test_two_stations_that_answer_to_one_name_are_each_marked():
    rows = [
        station("Foxholt Rail Station", "RSE", "4900FOXHOLT1"),
        station("Foxholt Station", "TMU", "4900ZZLUFOX1"),
        station("Wexmoor", "TMU", "4900ZZLUWEX1"),
    ]
    found = station_places.places_of(rows)
    assert [(one.name, one.shares_a_name) for one in found] == [
        ("Foxholt Rail Station", True),
        ("Foxholt Station", True),
        ("Wexmoor", False),
    ]


def test_two_stations_may_not_have_one_id():
    rows = [station("Foxholt", "RSE", "4900FOX.1"), station("Wexmoor", "TMU", "4900FOX1")]
    with pytest.raises(ValueError, match="an id names one station"):
        station_places.places_of(rows)
    with pytest.raises(ValueError, match="a code makes an id"):
        station_places.place_id_of(station("Foxholt", "RSE", "--"))


def test_the_network_is_a_hint_and_is_none_where_the_codes_do_not_say():
    rows = [
        station("Foxholt", "TMU", "4900ZZDLFOX1"),
        station("Wexmoor", "TMU", "490000001"),
        station("Eskerfold", "TMU", "4900ZZXXESK1"),
        station("Osierholm", "TMU", "4900ZZALOSI1"),
    ]
    found = {one.name: one.network for one in station_places.places_of(rows)}
    assert found == {"Foxholt": "dlr", "Wexmoor": None, "Eskerfold": None, "Osierholm": "cable_car"}
    assert set(station_places.SERVED) == set(stops_file.STATION_TYPES)


# What core's own search makes of the rows


@dataclass(frozen=True)
class Held:
    """As much of a release as core's search reads: its places, and its areas."""

    places: tuple[Place, ...]
    neighbourhoods: tuple[object, ...] = ()


def names_of(rows: Sequence[StationPlace]) -> Names:
    """The rows as core would hold them. The journey's end is made up: no build makes one."""
    held = tuple(
        Place(
            place_id=row.place_id,
            name=row.name,
            aliases=row.aliases,
            kind=row.kind,
            destination_id="lon-d0",
            coarse_place_id=row.place_id,
            centroid=row.centroid,
            source_id=row.source_id,
        )
        for row in rows
    )
    return Names(cast(Release, Held(held)))


def test_a_row_is_a_place_as_core_holds_one_but_for_where_its_journeys_end(tmp_path: Path):
    assert len(names_of(places(tmp_path)).search_places("a", 10)) == 0
    assert len(names_of(places(tmp_path)).search_places("pellam", 10)) == 1


@pytest.mark.parametrize(
    ("typed", "found"),
    [
        ("Pellam Cross", "lon-p4900pellamx1"),
        ("pellam cross station", "lon-p4900pellamx1"),
        ("Tallowgate", "lon-p4900zzlutlg1"),
        ("tallowgate station", "lon-p4900zzlutlg1"),
        ("Sable Reach", "lon-p4900zzcrsbr1"),
        ("sable reach tram stop", "lon-p4900zzcrsbr1"),
    ],
)
def test_the_words_a_person_types_are_the_whole_of_a_name_or_of_an_alias(
    tmp_path: Path, typed: str, found: str
):
    names = names_of(places(tmp_path))
    assert names.exact_place(typed).resolved == found
    assert names.resolve_place(typed).resolved == found


def test_without_its_aliases_a_station_is_not_found_by_the_words_a_person_types(tmp_path: Path):
    """So the aliases are what the search needs, and core needs no change to read them."""
    bare = [
        StationPlace(**{**vars(one), "aliases": ()})  # pyright: ignore[reportArgumentType]
        for one in places(tmp_path)
    ]
    names = names_of(bare)
    assert names.exact_place("Pellam Cross").resolved is None
    assert names.resolve_place("tallowgate station").resolved is None


def test_a_name_that_two_stations_answer_to_is_offered_and_never_taken():
    rows = station_places.places_of(
        [
            station("Foxholt Rail Station", "RSE", "4900FOXHOLT1"),
            station("Foxholt Station", "TMU", "4900ZZLUFOX1"),
        ]
    )
    answer = names_of(rows).resolve_place("Foxholt")
    assert answer.resolved is None
    assert [option.name for option in answer.options] == ["Foxholt Rail Station", "Foxholt Station"]
