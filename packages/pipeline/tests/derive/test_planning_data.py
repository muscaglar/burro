"""A file of the planning data platform, read a record at a time and held to its shape.

Every file here is made up: `heritage_support.py` writes the records, laid out
as the platform's own, on the made-up town of the tests of cells. No real file
is opened.
"""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.derive import planning_data
from burro_pipeline.derive.heritage_shapes import in_degrees
from burro_pipeline.derive.planning_data import Read, Record
from burro_pipeline.evidence.lock import LockError

from ..cells.support import EAST, NORTH
from .heritage_support import (
    AREAS,
    CANARY,
    CONSERVATION,
    ENTRIES,
    FAR_OFF,
    LISTED,
    OF_QUILLHAVEN,
    OLD_QUARTER,
    THE_COPY,
    THE_MINISTRY,
    MadeUp,
    areas_file,
    collection,
    entries_file,
    feature,
    opened_of,
    outline,
    point,
)

# The box round the made-up town, and a kilometre beyond it.
TOWN = in_degrees((EAST, NORTH - 200, EAST + 800, NORTH + 200), 1_000)
GRADE = "listed-building-grade"


def areas(folder: Path, content: bytes | None = None) -> Read:
    opened = opened_of(folder, CONSERVATION, areas_file() if content is None else content)
    return planning_data.read(opened, CONSERVATION[2], TOWN)


def entries(folder: Path, content: bytes | None = None) -> Read:
    opened = opened_of(folder, LISTED, entries_file() if content is None else content)
    return planning_data.read(opened, LISTED[2], TOWN, asked=(GRADE,))


def refused(folder: Path, content: bytes) -> str:
    """The refusal of a file, which names a rule and repeats nothing the file holds."""
    with pytest.raises(LockError) as stopped:
        areas(folder, content)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return str(stopped.value)


def written(features: list[Any], **members: Any) -> bytes:
    """A collection that holds whatever it is given, as the platform lays one out."""
    whole = {"type": "FeatureCollection", "name": CONSERVATION[2]} | members
    before = "".join(f"{json.dumps(name)}: {json.dumps(value)},\n" for name, value in whole.items())
    rows = ",\n".join(json.dumps(one) for one in features)
    return f'{{\n{before}"features": [\n{rows}\n]\n}}\n'.encode()


# What is read


def test_the_records_in_the_box_are_read_and_the_rest_are_counted(tmp_path: Path):
    found = areas(tmp_path)
    assert found.in_the_file == len(AREAS) == 8
    assert [record.entity for record in found.records] == [
        f"4400000{number}" for number in range(1, 8)
    ]
    assert FAR_OFF.entity not in {record.entity for record in found.records}
    assert found.nowhere == 0


def test_a_record_holds_its_provider_its_quality_and_its_days(tmp_path: Path):
    by_entity = {record.entity: record for record in areas(tmp_path).records}
    old, copy = by_entity[OLD_QUARTER.entity], by_entity[THE_COPY.entity]
    assert (old.provider, old.quality, old.entered, old.ended) == (
        OF_QUILLHAVEN,
        "authoritative",
        "2024-05-01",
        "",
    )
    assert (copy.provider, copy.quality, copy.entered) == (THE_MINISTRY, "some", "2025-06-01")
    assert by_entity["44000005"].ended == "2020-01-01"


def test_a_record_holds_where_it_is_as_the_file_writes_it(tmp_path: Path):
    by_entity = {record.entity: record for record in areas(tmp_path).records}
    assert by_entity[OLD_QUARTER.entity].kind == "Polygon"
    assert by_entity[OLD_QUARTER.entity].coordinates == outline(-20, 100, 220, 120)["coordinates"]
    assert by_entity["44000006"].kind == "Point"
    assert by_entity["44000006"].coordinates == point(350, 50)["coordinates"]


def test_no_name_and_no_note_is_ever_read(tmp_path: Path):
    """Every made-up record holds a string found nowhere else, as its name and in its notes."""
    assert CANARY.encode() in areas_file()
    assert CANARY.encode() in entries_file()
    for found in (areas(tmp_path / "a"), entries(tmp_path / "b")):
        assert found.records
        assert CANARY not in repr(found)
        assert "made-up.example" not in repr(found)


def test_a_property_that_is_asked_for_is_read_and_is_empty_where_a_record_has_none(
    tmp_path: Path,
):
    found = entries(tmp_path)
    assert [record.asked[GRADE] for record in found.records] == [
        "I",
        "II*",
        "II",
        "II",
        "",
        "II",
        "II",
    ]
    assert all(record.asked == {} for record in areas(tmp_path / "areas").records)


def test_the_records_are_given_in_the_order_of_their_numbers(tmp_path: Path):
    turned = areas(tmp_path, areas_file(AREAS[::-1]))
    assert turned.records == areas(tmp_path / "again").records
    numbers = [int(record.entity) for record in turned.records]
    assert numbers == sorted(numbers)


def test_a_number_is_read_as_a_number_and_not_as_text(tmp_path: Path):
    """9 sorts before 10. Read as text it would not."""
    records = [replace(OLD_QUARTER, entity=entity) for entity in ("10", "9", "100")]
    found = areas(tmp_path, areas_file(records))
    assert [record.entity for record in found.records] == ["9", "10", "100"]


def test_a_record_that_says_nothing_of_where_it_is_is_counted_and_is_in_no_box(tmp_path: Path):
    nowhere: list[float] = []
    records = [
        OLD_QUARTER,
        MadeUp("44000020", None),
        MadeUp("44000021", {"type": "Polygon", "coordinates": nowhere}),
    ]
    found = areas(tmp_path, areas_file(records))
    assert (found.in_the_file, found.nowhere, len(found.records)) == (3, 2, 1)


@pytest.mark.parametrize(
    ("day", "live"), [("2019-12-31", True), ("2020-01-01", False), ("2026-09-24", False)]
)
def test_a_record_is_live_until_the_day_it_ends(day: str, live: bool):
    ended = Record("1", "2", "some", "2020-01-01", "2010-01-01", {}, "Point", [0.0, 51.0])
    assert ended.live_on(day) is live
    assert replace(ended, ended="").live_on(day)


# However the file breaks its lines


@pytest.mark.parametrize("layout", ["one", "spread"])
def test_the_file_is_read_the_same_however_it_breaks_its_lines(tmp_path: Path, layout: str):
    as_the_platform = areas(tmp_path / "lines")
    assert areas(tmp_path / layout, areas_file(layout=layout)) == as_the_platform


@pytest.mark.parametrize("at_once", [1, 7, 64, 1_000])
def test_the_file_is_read_the_same_however_small_the_pieces_it_is_read_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, at_once: int
):
    whole = areas(tmp_path / "whole")
    monkeypatch.setattr(planning_data, "AT_ONCE", at_once)
    assert areas(tmp_path / "pieces") == whole
    assert areas(tmp_path / "one", areas_file(layout="one")) == whole


def test_a_member_of_the_collection_that_stands_before_its_features_is_stepped_over(
    tmp_path: Path,
):
    crs = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}
    content = written([feature(CONSERVATION[2], OLD_QUARTER)], crs=crs)
    assert [record.entity for record in areas(tmp_path, content).records] == ["44000001"]


def test_a_file_with_no_record_is_read_and_holds_none(tmp_path: Path):
    found = areas(tmp_path, areas_file([]))
    assert (found.in_the_file, found.records) == (0, ())


# What is outside the box is let go


def test_nothing_is_read_of_a_record_outside_the_box_but_where_it_is(tmp_path: Path):
    """A record far from London may be of any shape. It is counted, and let go."""
    broken = replace(FAR_OFF, instead={"quality": 5, "entity": None}, without=("entry-date",))
    found = areas(tmp_path, areas_file([OLD_QUARTER, broken]))
    assert (found.in_the_file, len(found.records)) == (2, 1)


# What is refused


def test_a_file_that_is_not_json_is_refused(tmp_path: Path):
    assert "not a collection of features" in refused(tmp_path, b"entity,name\n1,Zzyzx Parva\n")


def test_a_file_that_holds_no_list_of_features_is_refused(tmp_path: Path):
    content = json.dumps({"type": "FeatureCollection", "name": CONSERVATION[2]}).encode()
    assert "not a collection of features" in refused(tmp_path, content)


def test_a_file_that_is_not_a_collection_is_refused(tmp_path: Path):
    content = written([], type="Feature")
    assert "not a collection of features" in refused(tmp_path, content)


def test_a_file_of_another_dataset_is_refused(tmp_path: Path):
    content = collection(LISTED[2], ENTRIES)
    assert "not the dataset that is read" in refused(tmp_path, content)


def test_a_record_of_another_dataset_is_refused(tmp_path: Path):
    content = areas_file([replace(OLD_QUARTER, instead={"dataset": "listed-building"})])
    assert "a record is of another dataset" in refused(tmp_path, content)


@pytest.mark.parametrize(
    "name", ["dataset", "entity", "organisation-entity", "quality", "end-date", "entry-date"]
)
def test_a_record_that_lacks_a_property_that_is_read_is_refused(tmp_path: Path, name: str):
    content = areas_file([replace(OLD_QUARTER, without=(name,))])
    assert "a record lacks a property that is read" in refused(tmp_path, content)


@pytest.mark.parametrize("value", [44000001, 4.5, True, ["44000001"], {"is": "44000001"}])
def test_a_property_that_is_not_text_is_refused(tmp_path: Path, value: object):
    content = areas_file([replace(OLD_QUARTER, instead={"entity": value})])
    assert "a property is not text" in refused(tmp_path, content)


@pytest.mark.parametrize(
    ("instead", "words"),
    [
        ({"entity": "forty"}, "a number of the platform is not a number"),
        ({"entity": ""}, "a number of the platform is not a number"),
        (
            {"organisation-entity": "local-authority:QUI"},
            "a number of the platform is not a number",
        ),
        ({"quality": "trustworthy"}, "a quality is not one the file is known to hold"),
        ({"quality": ""}, "a quality is not one the file is known to hold"),
        ({"entry-date": "1 May 2024"}, "a day is not a day"),
        ({"entry-date": ""}, "a day is not a day"),
        ({"end-date": "2020"}, "a day is not a day"),
    ],
)
def test_a_property_that_is_not_what_it_should_be_is_refused(
    tmp_path: Path, instead: dict[str, str], words: str
):
    content = areas_file([replace(OLD_QUARTER, instead=instead)])
    assert words in refused(tmp_path, content)


def test_two_records_that_share_a_number_are_refused(tmp_path: Path):
    content = areas_file([OLD_QUARTER, replace(THE_COPY, entity=OLD_QUARTER.entity)])
    assert "two records share a number" in refused(tmp_path, content)


@pytest.mark.parametrize(
    "geometry",
    [
        "here",
        {"type": "Polygon"},
        {"coordinates": [0.0, 51.0]},
        {"type": 5, "coordinates": [0.0, 51.0]},
        {"type": "Point", "coordinates": "0.0 51.0"},
        {"type": "Point", "coordinates": ["east", "north"]},
        {"type": "Polygon", "coordinates": [[[0.0]]]},
    ],
)
def test_a_geometry_that_is_not_a_geometry_is_refused(tmp_path: Path, geometry: Any):
    one = feature(CONSERVATION[2], OLD_QUARTER) | {"geometry": geometry}
    assert "a geometry is not a geometry" in refused(tmp_path, written([one]))


@pytest.mark.parametrize("features", [[1, 2, 3], ["a record"], [[]], [{"type": "Record"}]])
def test_features_that_are_not_records_are_refused(tmp_path: Path, features: list[Any]):
    assert "its features are not a list of records" in refused(tmp_path, written(features))


def test_a_feature_in_the_box_with_no_properties_is_refused(tmp_path: Path):
    one = {"type": "Feature", "geometry": OLD_QUARTER.where}
    assert "its features are not a list of records" in refused(tmp_path, written([one]))


@pytest.mark.parametrize("cut", [40, 400, 2_000])
def test_a_file_that_is_cut_short_is_refused(tmp_path: Path, cut: int):
    content = areas_file()
    assert len(content) > 2_000
    words = refused(tmp_path, content[: len(content) - cut])
    assert "a record is cut short" in words or "not a collection of features" in words


def test_a_file_that_goes_on_after_its_collection_is_refused(tmp_path: Path):
    assert "it holds more than one collection" in refused(tmp_path, areas_file() + areas_file())


def test_a_member_after_the_features_is_refused(tmp_path: Path):
    content = areas_file().rstrip().removesuffix(b"}") + b', "more": 1}\n'
    assert "not a collection of features" in refused(tmp_path, content)
