"""The postcode lookup: from a postcode as typed to a point and to its census areas.

Every file here is made up: `postcodes_support.py` draws the directory, on the
town of the tests of cells. No postcode here is one that has been given out.
"""

import dataclasses
import inspect
import zipfile
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.cells import postcodes, spine
from burro_pipeline.cells.postcodes import Lookup, Placed
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry.model import Use

from .postcodes_support import (
    A_BOX,
    CANARY,
    DIRECTORY,
    ENDED,
    IN_ANOTHER_FILE,
    IN_ITS_OWN_FILE,
    LONG_ENDED,
    MILL_ROW,
    NO_POINT,
    NORTH_GATE,
    OF_LONDON,
    OF_NORTHERN_IRELAND,
    OUTSIDE,
    QUAY,
    STEM,
    MadeUpPostcode,
    directory_zip,
    inputs_of,
    members_of,
    opened_of,
    point_of,
    unit_at,
)
from .support import zip_of


@pytest.fixture(scope="module")
def lookup(tmp_path_factory: pytest.TempPathFactory) -> Lookup:
    return postcodes.read(opened_of(tmp_path_factory.mktemp("directory")))


def placed(lookup: Lookup, typed: str) -> Placed:
    found = lookup.place(typed)
    assert found is not None
    return found


def refusal(folder: Path, directory: bytes, *, name: str = "ONSPD_AUG_2026.zip") -> str:
    with pytest.raises(LockError) as refused:
        postcodes.read(opened_of(folder, directory, name=name))
    assert refused.value.rule == "input_is_as_described"
    return str(refused.value)


# What is asked of the gate.


def test_the_gate_is_asked_for_the_use_a_measure_puts_the_directory_to(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = postcodes.build(inputs)
    assert postcodes.USE is Use.SCORING
    assert [one.receipt.source_id for one in inputs.opened] == [postcodes.SOURCE]
    assert found.receipt.source_id == postcodes.SOURCE


def test_a_use_the_registry_does_not_list_is_refused_before_anything_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    with pytest.raises(LockError) as refused:
        postcodes.build(inputs, use=Use.GAZETTEER)
    assert refused.value.rule == "gate_refuses"
    assert inputs.opened == ()


# A postcode as it is typed.


@pytest.mark.parametrize(
    "typed",
    ["QH1 1CK", "QH11CK", "qh1 1ck", "qh11ck", "  Qh1  1cK ", "QH1\t1CK", "q h 1 1 c k"],
)
def test_a_postcode_is_found_with_or_without_its_space_and_in_any_case(lookup: Lookup, typed: str):
    assert placed(lookup, typed) == placed(lookup, NORTH_GATE.postcode)


@pytest.mark.parametrize(
    "typed",
    [
        "",
        " ",
        "QH1",
        "1CK",
        "QH1 1C",
        "QH1 1CKK",
        "QH1-1CK",
        "QH1 ICK",
        "\N{LATIN CAPITAL LETTER O WITH OGONEK}H1 1CK",
        "QH\N{FULLWIDTH DIGIT ONE} 1CK",
    ],
)
def test_text_that_has_not_the_shape_of_a_postcode_is_not_found(lookup: Lookup, typed: str):
    assert postcodes.key_of(typed) is None
    assert lookup.place(typed) is None


def test_nothing_is_corrected_so_a_letter_typed_for_a_digit_is_not_found(lookup: Lookup):
    assert lookup.place("QHI 1CK") is None
    assert lookup.place("QH1 1CC") is None


@pytest.mark.parametrize(
    "typed",
    [
        # Each holds a letter that is no letter of a postcode, and that the language makes
        # one when it changes the case of a text: a Kelvin sign, a dotless i, a long s, a
        # sharp s and a ligature of two letters.
        "QH1 1C\N{KELVIN SIGN}",
        "qh1 1c\N{KELVIN SIGN}",
        "QH1 1\N{LATIN SMALL LETTER DOTLESS I}K",
        "\N{LATIN SMALL LETTER LONG S}H1 1CK",
        "\N{LATIN SMALL LETTER SHARP S}1 1CK",
        "QH1 1\N{LATIN SMALL LIGATURE FI}",
    ],
)
def test_a_letter_that_is_no_letter_of_a_postcode_is_never_made_one(typed: str):
    assert postcodes.key_of(typed) is None


# What a postcode is placed at.


def test_a_postcode_gives_its_point_and_the_areas_the_point_is_in(lookup: Lookup):
    unit = unit_at((50, 150))
    assert placed(lookup, NORTH_GATE.postcode) == Placed(
        point=point_of(NORTH_GATE),
        oa=unit.oa,
        lsoa=unit.lsoa,
        msoa=unit.msoa,
        borough=unit.borough,
        quality=1,
        ended=None,
    )


def test_every_row_of_london_is_placed_in_the_output_area_its_point_is_in(lookup: Lookup):
    for row in OF_LONDON:
        assert row.at is not None
        found = placed(lookup, row.postcode)
        assert (found.point, found.oa) == (point_of(row), unit_at(row.at).oa)


def test_what_is_given_back_holds_no_postcode(lookup: Lookup):
    names = {one.name for one in dataclasses.fields(Placed)}
    assert names == {"point", "oa", "lsoa", "msoa", "borough", "quality", "ended"}
    for row in OF_LONDON:
        said = repr(placed(lookup, row.postcode))
        assert row.postcode not in said
        assert row.postcode.replace(" ", "") not in said


# A postcode that has ended.


def test_a_postcode_that_has_ended_is_placed_where_it_last_stood_and_says_when(lookup: Lookup):
    found = placed(lookup, ENDED.postcode)
    assert found.point == point_of(ENDED)
    assert (found.ended, found.in_use) == ("2019-03", False)
    assert placed(lookup, NORTH_GATE.postcode).in_use


def test_a_postcode_that_has_ended_is_never_counted_as_in_use(lookup: Lookup):
    assert lookup.counts.london == len(OF_LONDON) == len(lookup)
    assert lookup.counts.ended == 2
    assert lookup.counts.in_use == 4
    assert sum(lookup.in_use_by_output_area().values()) == 4
    assert unit_at((150, 50)).oa not in lookup.in_use_by_output_area()


def test_a_point_is_good_for_a_distance_only_where_it_is_of_the_postcodes_own_addresses(
    lookup: Lookup,
):
    assert placed(lookup, NORTH_GATE.postcode).good_for_a_distance
    assert placed(lookup, ENDED.postcode).good_for_a_distance
    # The middle of a sector, and a point kept from before November 2000.
    assert not placed(lookup, A_BOX.postcode).good_for_a_distance
    assert not placed(lookup, LONG_ENDED.postcode).good_for_a_distance
    assert lookup.counts.quality_in_use == {1: 3, 6: 1}
    assert lookup.counts.quality_ended == {1: 1, 8: 1}


def test_every_mark_of_quality_the_guide_names_has_its_words():
    assert sorted(postcodes.QUALITY) == [1, 2, 3, 4, 5, 6, 8, 9]
    assert set(postcodes.QUALITY) > postcodes.GOOD_FOR_A_DISTANCE


# London alone, and never Northern Ireland.


def test_a_row_of_another_authority_is_not_kept(lookup: Lookup):
    assert lookup.place(OUTSIDE.postcode) is None
    assert "QZ" not in lookup.counts.areas


def test_a_postcode_with_no_point_has_no_authority_and_is_not_found(lookup: Lookup):
    assert lookup.place(NO_POINT.postcode) is None


def test_no_row_of_northern_ireland_is_kept(lookup: Lookup):
    # Each is written as a row of London, so a reader that kept one would place it.
    for row in OF_NORTHERN_IRELAND:
        assert lookup.place(row.postcode) is None
    assert postcodes.NORTHERN_IRELAND not in lookup.counts.areas
    assert lookup.counts.dropped_for_northern_ireland == 1
    assert lookup.counts.london == len(OF_LONDON)


def test_the_file_of_northern_ireland_is_never_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    opened = opened_of(tmp_path)
    seen: list[str] = []
    really_open = zipfile.ZipFile.open

    def watched(self: zipfile.ZipFile, name: Any, *args: Any, **kwargs: Any) -> Any:
        seen.append(name.filename if isinstance(name, zipfile.ZipInfo) else str(name))
        return really_open(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", watched)
    found = postcodes.read(opened)
    files = postcodes.area_files(opened)
    assert postcodes.NORTHERN_IRELAND in files
    assert sorted(seen) == sorted(
        name for area, name in files.items() if area != postcodes.NORTHERN_IRELAND
    )
    assert (found.counts.files, found.counts.opened) == (4, 3)
    # The whole directory is in the zip too, and is never opened.
    assert f"Data/{STEM}.csv" not in seen


def test_the_file_of_northern_ireland_cannot_be_asked_for(tmp_path: Path):
    opened = opened_of(tmp_path)
    name = postcodes.area_files(opened)[postcodes.NORTHERN_IRELAND]
    for asked in (name, f"Data/{STEM}.csv", "User Guide/Made up guide.odt", "../elsewhere.csv"):
        with pytest.raises(LockError) as refused:
            postcodes.columns_of(opened, asked)
        assert refused.value.rule == "input_is_as_described"
        assert asked not in str(refused.value)


def test_a_row_of_northern_ireland_is_dropped_whatever_its_line_begins_with(tmp_path: Path):
    # The first column of the line says another area, and the postcode that is read says
    # Northern Ireland.
    changed = {IN_ANOTHER_FILE.postcode: {"pcd7": "QT9 1CK", "pcd8": "QT9  1CK"}}
    found = postcodes.read(opened_of(tmp_path, directory_zip(changed=changed)))
    assert found.place(IN_ANOTHER_FILE.postcode) is None
    assert found.counts.dropped_for_northern_ireland == 1
    assert found.counts.london == len(OF_LONDON)


def test_a_line_of_northern_ireland_is_dropped_before_it_is_split_into_columns(tmp_path: Path):
    # The line is no row at all: were it split into columns the step would stop at it.
    members = members_of()
    name = f"Data/multi_csv/{STEM}_QT.csv"
    of_area = members[name]
    assert isinstance(of_area, str)
    members[name] = of_area + '"BT3 1CK","a line that is no row\r\n'
    found = postcodes.read(opened_of(tmp_path, zip_of(members)))
    assert found.counts.dropped_for_northern_ireland == 2
    assert found.counts.london == len(OF_LONDON)


# Columns that are never read.


def test_the_columns_about_who_lives_in_an_area_are_never_read():
    assert set(postcodes.NEVER_READ) == {
        "oac01ind",
        "oac11ind",
        "oac21ind",
        "imd20ind",
        "imd25ind",
    }
    assert not set(postcodes.NEVER_READ) & set(postcodes.READ)
    assert set(postcodes.READ) | set(postcodes.NEVER_READ) <= set(postcodes.HELD)
    assert len(postcodes.READ) == 9


def test_nothing_of_a_column_that_is_not_read_is_kept(lookup: Lookup):
    for row in OF_LONDON:
        assert CANARY not in repr(dataclasses.astuple(placed(lookup, row.postcode)))
    assert CANARY not in repr(vars(lookup))


def test_a_directory_with_none_of_the_columns_about_residents_reads_the_same(
    tmp_path: Path, lookup: Lookup
):
    columns = [name for name in postcodes.HELD if name not in postcodes.NEVER_READ]
    found = postcodes.read(opened_of(tmp_path, directory_zip(columns=columns)))
    assert found.counts == lookup.counts
    for row in OF_LONDON:
        assert found.place(row.postcode) == lookup.place(row.postcode)


def test_the_lookup_gives_out_no_postcode(lookup: Lookup):
    said = repr(lookup) + str(lookup) + repr(lookup.counts)
    for row in DIRECTORY:
        assert row.postcode not in said
        assert row.postcode.replace(" ", "") not in said
    # Nothing that is public gives back a postcode: a point, a code of an area, a district
    # or a count.
    public = [
        name
        for name, _ in inspect.getmembers(Lookup, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    assert sorted(public) == [
        "in_use_by_borough",
        "in_use_by_district",
        "in_use_by_output_area",
        "not_of",
        "place",
        "points_in_use",
    ]
    with pytest.raises(TypeError):
        iter(lookup)  # type: ignore[call-overload]


# The district of a postcode.


def test_the_postcodes_in_use_of_an_output_area_are_counted_by_their_district(lookup: Lookup):
    found = lookup.in_use_by_district()
    # The first half of a postcode, as it is written before the space.
    assert found[unit_at((50, 150)).oa] == {"QH1": 1}
    assert found[unit_at((250, 150)).oa] == {"QH2": 1}
    assert found[unit_at((350, 50)).oa] == {"QH9": 1}
    assert found[unit_at((550, 50)).oa] == {"QT1": 1}
    assert sum(sum(held.values()) for held in found.values()) == lookup.counts.in_use


def test_a_postcode_that_has_ended_is_counted_in_no_district(lookup: Lookup):
    found = lookup.in_use_by_district()
    # Two postcodes of one district have ended, each in an output area of its own.
    assert unit_at((150, 50)).oa not in found
    assert unit_at((130, 150)).oa not in found


def test_an_output_area_may_hold_postcodes_of_more_than_one_district(tmp_path: Path):
    beside = (MadeUpPostcode("QH2 2CK", (60, 160)), MadeUpPostcode("QH2 3CK", (70, 170)))
    found = postcodes.read(opened_of(tmp_path, directory_zip((*DIRECTORY, *beside))))
    assert found.in_use_by_district()[unit_at((50, 150)).oa] == {"QH1": 1, "QH2": 2}


def test_a_district_is_the_whole_of_what_stands_before_the_space(tmp_path: Path):
    # A district of two letters and two digits, and one that ends in a letter.
    long, lettered = MadeUpPostcode("QH10 1CK", (60, 160)), MadeUpPostcode("QH1A 1CK", (70, 170))
    found = postcodes.read(opened_of(tmp_path, directory_zip((*DIRECTORY, long, lettered))))
    assert found.in_use_by_district()[unit_at((50, 150)).oa] == {"QH1": 1, "QH10": 1, "QH1A": 1}


def test_what_is_counted_by_district_holds_no_postcode(lookup: Lookup):
    said = repr(lookup.in_use_by_district())
    for row in DIRECTORY:
        assert row.postcode not in said
        assert row.postcode.replace(" ", "") not in said
        assert row.postcode.split(" ")[1] not in said


def test_the_module_writes_nothing():
    source = inspect.getsource(postcodes)
    for way in ("write_text", "write_bytes", ".write(", "open(", "extract"):
        assert way not in source.replace("archive.open(", "").replace("inputs.open(", "")


# The credits.


def test_the_three_credits_carry_the_year_of_the_data(lookup: Lookup):
    assert postcodes.credits_of(lookup.receipt) == (
        "Contains OS data © Crown copyright and database right 2026",
        "Contains Royal Mail data © Royal Mail copyright and database right 2026",
        "Source: Office for National Statistics licensed under the Open Government Licence v.3.0",
    )


# The areas of a build.


def test_every_postcode_in_use_is_in_an_area_of_the_build(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = postcodes.build(inputs)
    ground = spine.build(inputs)
    assert found.not_of(ground) == {
        "in_no_area": 0,
        "in_use_in_no_area": 0,
        "in_another_borough": 0,
        "in_use_in_another_borough": 0,
        "output_areas_in_another_lsoa_or_msoa": 0,
        "output_areas_with_none_in_use": 8,
    }
    assert found.in_use_by_borough() == {"E09000901": 3, "E09000902": 1}


def test_an_output_area_the_directory_puts_in_another_lsoa_than_the_build_is_counted(
    tmp_path: Path,
):
    changed = {MILL_ROW.postcode: {postcodes.LSOA: "E01999777"}}
    inputs = inputs_of(tmp_path, directory_zip(changed=changed))
    found = postcodes.build(inputs).not_of(spine.build(inputs))
    assert found["output_areas_in_another_lsoa_or_msoa"] == 1


def test_a_postcode_whose_output_area_is_in_no_area_of_the_build_is_counted(tmp_path: Path):
    changed = {
        QUAY.postcode: {postcodes.OA: "E00999777"},
        ENDED.postcode: {postcodes.OA: "E00999778"},
    }
    inputs = inputs_of(tmp_path, directory_zip(changed=changed))
    found = postcodes.build(inputs).not_of(spine.build(inputs))
    assert (found["in_no_area"], found["in_use_in_no_area"]) == (2, 1)


def test_a_point_may_stand_in_another_borough_than_the_build_puts_its_output_area_in(
    tmp_path: Path,
):
    # An output area of 2021 may lie across the border of two boroughs of today. The
    # directory gives each postcode the borough its own point stands in.
    beside = MadeUpPostcode("QH1 2CK", (60, 160))
    changed = {beside.postcode: {postcodes.AUTHORITY: "E09000902"}}
    inputs = inputs_of(tmp_path, directory_zip((*DIRECTORY, beside), changed=changed))
    found = postcodes.build(inputs)
    here, there = placed(found, NORTH_GATE.postcode), placed(found, beside.postcode)
    assert (here.oa, here.lsoa, here.msoa) == (there.oa, there.lsoa, there.msoa)
    assert (here.borough, there.borough) == ("E09000901", "E09000902")
    counted = found.not_of(spine.build(inputs))
    assert (counted["in_another_borough"], counted["in_use_in_another_borough"]) == (1, 1)
    assert counted["in_no_area"] == 0


# A file that is not as the step expects.


def test_a_zip_that_is_not_named_as_the_directory_is_stops_the_step(tmp_path: Path):
    assert "it is not named as the directory is" in refusal(
        tmp_path, directory_zip(), name="postcodes.zip"
    )


def test_a_file_that_is_no_zip_stops_the_step(tmp_path: Path):
    assert "it is not a zip" in refusal(tmp_path, b"pcds,doterm\r\n")


def test_a_file_in_the_folder_that_is_not_named_for_an_area_stops_the_step(tmp_path: Path):
    members = members_of() | {"Data/multi_csv/notes.csv": "pcds\r\n"}
    assert "a file is not named for a postcode area" in refusal(tmp_path, zip_of(members))


def test_a_zip_with_the_file_of_no_area_stops_the_step(tmp_path: Path):
    members = {name: held for name, held in members_of().items() if "multi_csv" not in name} | {
        f"Data/multi_csv/{STEM}_BT.csv": "pcds\r\n"
    }
    assert "it holds no file of a postcode area" in refusal(tmp_path, zip_of(members))


@pytest.mark.parametrize("column", postcodes.READ)
def test_a_file_that_lacks_a_column_that_is_read_stops_the_step(tmp_path: Path, column: str):
    columns = [name for name in postcodes.HELD if name != column]
    assert "a column is missing" in refusal(tmp_path, directory_zip(columns=columns))


def test_the_names_of_an_earlier_edition_are_not_the_names_that_are_read(tmp_path: Path):
    # The publisher changed the names of the columns on 2026-09-07. A file under the old
    # names stops the step, and nothing is read by the place of a column.
    old = [name.upper().replace("26CD", "") for name in postcodes.HELD]
    assert "a column is missing" in refusal(tmp_path, directory_zip(columns=old))


@pytest.mark.parametrize(
    ("column", "value", "words"),
    [
        (postcodes.POSTCODE, "QH11CK", "a postcode is not written as the directory writes one"),
        (postcodes.POSTCODE, "QH1  1CK", "a postcode is not written as the directory writes one"),
        (postcodes.POSTCODE, "qh1 1ck", "a postcode is not written as the directory writes one"),
        (postcodes.ENDED, "2019", "the month a postcode ended is no month"),
        (postcodes.ENDED, "201913", "the month a postcode ended is no month"),
        (postcodes.QUALITY_MARK, "7", "the quality of a point is not one the guide names"),
        (postcodes.QUALITY_MARK, "", "the quality of a point is not one the guide names"),
        (postcodes.EASTING, "", "a row of London has no point"),
        (postcodes.NORTHING, "400150.5", "a row of London has no point"),
        (postcodes.OA, "", "a code is not a code"),
        (postcodes.LSOA, "E02999001", "a code is not a code"),
        (postcodes.MSOA, "W02999001", "a code is not a code"),
        (postcodes.AUTHORITY, "E09", "a code is not a code"),
    ],
)
def test_a_row_of_london_that_is_not_written_as_the_guide_says_stops_the_step(
    tmp_path: Path, column: str, value: str, words: str
):
    said = refusal(tmp_path, directory_zip(changed={NORTH_GATE.postcode: {column: value}}))
    assert words in said
    assert NORTH_GATE.postcode not in said
    assert not value or value not in said


def test_a_postcode_that_is_there_twice_stops_the_step(tmp_path: Path):
    twice = (*DIRECTORY, MadeUpPostcode(NORTH_GATE.postcode, (250, 50)))
    assert "a postcode is there twice" in refusal(tmp_path, directory_zip(twice))


def test_an_output_area_in_two_lsoas_stops_the_step(tmp_path: Path):
    both = (*DIRECTORY, MadeUpPostcode("QH1 2CK", (60, 160)))
    changed = {"QH1 2CK": {postcodes.LSOA: "E01999777"}}
    assert "a unit is part of two others" in refusal(tmp_path, directory_zip(both, changed=changed))


def test_a_row_that_is_short_stops_the_step(tmp_path: Path):
    members = members_of()
    name = f"Data/multi_csv/{STEM}_QH.csv"
    of_area = members[name]
    assert isinstance(of_area, str)
    members[name] = of_area + "QH4 1CK,QH4  1CK,QH4 1CK\r\n"
    assert "a row is short" in refusal(tmp_path, zip_of(members))


def test_the_same_file_read_twice_gives_the_same_lookup(tmp_path: Path, lookup: Lookup):
    again = postcodes.read(opened_of(tmp_path))
    assert again.counts == lookup.counts
    assert again.points_in_use() == lookup.points_in_use()
    assert IN_ITS_OWN_FILE.postcode not in repr(again.counts)
