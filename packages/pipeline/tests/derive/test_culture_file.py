"""The file of places, read for culture: the kind and the point of each venue, and no more.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places. The file is read as a build reads it, from a store,
through the licence gate, by its receipt. No socket is opened.
"""

import struct
from pathlib import Path

import pytest
from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import culture_file
from burro_pipeline.derive.culture_file import Places
from burro_pipeline.derive.culture_kinds import Kind
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from ..fetch.parquet_support import point
from .culture_support import (
    ARTS,
    CAFE,
    CANARY,
    DAY,
    EDITION,
    GALLERY,
    IN_THE_TOWN,
    LIBRARY,
    MUSEUM,
    Q1,
    SOURCE,
    THEATRE,
    Wanted,
    beside,
    counts,
    inputs_of,
    on_the_grid,
    place,
    places_receipt,
)

# The columns of the list, with the name of the dataset in place of everything the file
# says of where a record came from.
DATASET = "sources.list.element.dataset"
DATASET_ALONE = tuple(DATASET if name == "sources" else name for name in Wanted().columns)


def read(folder: Path, *places: object, **how: object) -> Places:
    given = places if places else IN_THE_TOWN
    return culture_file.build(inputs_of(folder, given, **how))  # pyright: ignore[reportArgumentType]


def refused(folder: Path, *places: object, **how: object) -> LockError:
    with pytest.raises(LockError) as stopped:
        read(folder, *places, **how)
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# What is read


def test_every_venue_of_a_kind_is_read_with_its_kind_and_its_point(tmp_path: Path):
    found = read(tmp_path)
    assert counts(found.by_kind) == {
        "cinema": 1,
        "gallery": 2,
        "library": 2,
        "museum": 3,
        "music_venue": 1,
        "theatre": 1,
    }
    museum = longitude_and_latitude(*on_the_grid(beside(Q1, 100)))
    theatre = longitude_and_latitude(*on_the_grid(beside(Q1, -100)))
    read_as = {(venue.kind, venue.longitude, venue.latitude) for venue in found.venues}
    assert {(Kind.MUSEUM, *museum), (Kind.THEATRE, *theatre)} <= read_as
    assert len(found.venues) == 10


def test_what_is_left_out_is_counted_by_the_reason(tmp_path: Path):
    found = read(tmp_path)
    assert found.rows == 28
    assert counts(found.left_out) == {
        "also_teaches": 1,
        "closed": 1,
        "not_a_kind": 1,
        "not_culture": 14,
        "parent_alone": 1,
    }
    assert found.rows == len(found.venues) + sum(found.left_out.values())


def test_what_is_left_out_of_culture_is_counted_by_its_category(tmp_path: Path):
    """So a person can see what each line of the table costs. No name of a place is kept."""
    found = read(tmp_path)
    assert dict(found.left_out_as) == {
        "choir": 1,
        "museum": 1,
        "performing_arts_venue": 1,
        "theatre_venue": 1,
    }
    assert dict(found.counted_as) == {
        "art_gallery": 2,
        "art_museum": 1,
        "library": 2,
        "movie_theater": 1,
        "museum": 2,
        "music_venue": 1,
        "theatre_venue": 1,
    }


def test_the_point_of_every_record_is_kept_whatever_it_is(tmp_path: Path):
    """It is what a count of everything is made from, to hold a count of venues against."""
    found = read(tmp_path)
    assert len(found.every) == 28
    assert {(venue.longitude, venue.latitude) for venue in found.venues} <= set(found.every)


def test_which_of_the_publishers_sources_gave_each_venue_is_kept(tmp_path: Path):
    """The licence registry asks for it, so that the records of one licence can be left out."""
    found = read(
        tmp_path,
        place(Q1, MUSEUM, dataset="meta"),
        place(beside(Q1, 50), MUSEUM, dataset="Foursquare"),
        place(beside(Q1, 90), GALLERY, dataset="Microsoft"),
        place(beside(Q1, 95), CAFE, dataset="AllThePlaces"),
    )
    assert [venue.datasets for venue in found.venues] == [
        ("meta",),
        ("Foursquare",),
        ("Microsoft",),
    ]
    assert dict(found.by_dataset) == {"Foursquare": 1, "Microsoft": 1, "meta": 1}


def test_the_file_says_which_release_it_is_and_when(tmp_path: Path):
    found = read(tmp_path)
    assert (found.file.source_id, found.file.edition) == (SOURCE, EDITION)
    assert found.as_at == DAY
    assert found.file.taken is not None and found.file.taken.rows == 28


def test_no_name_address_or_id_of_a_place_is_read(tmp_path: Path):
    found = read(tmp_path, packed="none")
    assert CANARY not in repr(found)
    assert set(culture_file.READ) == {
        "geometry",
        "taxonomy",
        "operating_status",
        "sources",
        "confidence",
    }


def test_of_what_the_file_says_of_its_sources_the_dataset_alone_is_asked_for(tmp_path: Path):
    """The part holds the name of the dataset and nothing beside it, and is read all the same.

    A read of a byte that was not taken is refused, so a step that asked for the id a
    source gave a record, or for anything else beside the dataset, would stop here.
    """
    inputs = inputs_of(tmp_path, IN_THE_TOWN, wanted=Wanted(columns=DATASET_ALONE), packed="none")
    found = culture_file.build(inputs)
    (opened,) = inputs.opened
    taken = opened.receipt.taken
    assert taken is not None and DATASET in taken.columns and "sources" not in taken.columns
    rows = opened.path.read_bytes()[: -taken.runs[-1][1]]
    assert CANARY.encode() not in rows
    whole = read(tmp_path / "whole")
    assert found.venues == whole.venues and found.by_dataset == whole.by_dataset
    assert (found.rows, found.left_out) == (whole.rows, whole.left_out)


def test_a_file_that_names_the_dataset_of_a_source_twice_stops_the_build(tmp_path: Path):
    """Which of two columns is the dataset is not guessed."""
    assert culture_file.dataset_in(["id", "sources.list.element.dataset"]) == DATASET
    for layout in (
        ["sources.list.element.dataset", "sources.list.element.between.dataset"],
        ["sources.list.element.record_id", "taxonomy.dataset", "dataset"],
        [],
    ):
        with pytest.raises(ValueError, match="dataset"):
            culture_file.dataset_in(layout)


def test_the_same_file_in_any_order_of_rows_reads_the_same(tmp_path: Path):
    one = read(tmp_path / "a", *IN_THE_TOWN)
    other = read(tmp_path / "b", *reversed(IN_THE_TOWN), rows_in_a_group=3)
    assert one.venues == other.venues and one.every == other.every
    assert (one.left_out, one.counted_as) == (other.left_out, other.counted_as)


def test_a_file_that_was_kept_whole_is_read_the_same(tmp_path: Path):
    part, whole = read(tmp_path / "a"), read(tmp_path / "b", whole=True)
    assert part.venues == whole.venues and part.left_out == whole.left_out
    assert whole.file.taken is None


def test_only_the_row_groups_that_were_taken_are_read(tmp_path: Path):
    """The part holds the row groups that may hold a place in the box, and the step reads those."""
    far = place((400_000.0, 0.0), MUSEUM)
    town = (*IN_THE_TOWN[12:16], far, far, far, far)
    near = Wanted(box=(2.0, 53.0, 4.5, 54.0))
    found = read(tmp_path, *town, wanted=near, rows_in_a_group=4)
    assert found.file.taken is not None
    assert (found.file.taken.row_groups, found.file.taken.of_row_groups) == ((0,), 2)
    assert found.rows == 4 and len(found.venues) == 4


# What is left out, one rule at a time


def test_a_place_that_the_file_says_has_closed_for_good_is_left_out(tmp_path: Path):
    found = read(
        tmp_path,
        place(Q1, MUSEUM, status="permanently_closed"),
        place(beside(Q1, 50), MUSEUM, status="temporarily_closed"),
        place(beside(Q1, 90), MUSEUM, status="open"),
        place(beside(Q1, 95), MUSEUM, status=None),
    )
    assert counts(found.left_out) == {"closed": 1}
    assert len(found.venues) == 3


def test_a_place_with_no_category_is_left_out_and_is_never_given_one(tmp_path: Path):
    found = read(tmp_path, place(Q1, (), primary=None), place(beside(Q1, 50), MUSEUM))
    assert counts(found.left_out) == {"no_category": 1}
    assert [venue.kind for venue in found.venues] == [Kind.MUSEUM]


def test_a_place_with_no_point_is_counted_and_is_put_nowhere(tmp_path: Path):
    nowhere = struct.pack("<BIdd", 1, 1, float("nan"), float("nan"))
    off_the_earth = point(200.0, 95.0)
    found = read(
        tmp_path,
        place(Q1, MUSEUM, geometry=nowhere),
        place(Q1, MUSEUM, geometry=off_the_earth),
        place(beside(Q1, 50), MUSEUM),
    )
    assert counts(found.left_out) == {"no_point": 2}
    assert len(found.venues) == 1 and len(found.every) == 1


def test_a_point_written_the_other_way_round_is_read(tmp_path: Path):
    longitude, latitude = longitude_and_latitude(*on_the_grid(Q1))
    other = struct.pack(">BIdd", 0, 1, longitude, latitude)
    found = read(tmp_path, place(Q1, MUSEUM, geometry=other))
    assert [(venue.longitude, venue.latitude) for venue in found.venues] == [(longitude, latitude)]


# A file that is not laid out as expected


def test_a_category_of_culture_that_the_table_does_not_hold_stops_the_build(tmp_path: Path):
    unknown = (ARTS, "museum", "zzyzx_parva_museum")
    error = refused(tmp_path, place(Q1, unknown), place(beside(Q1, 50), MUSEUM))
    assert error.rule == "input_is_as_described"
    assert "zzyzx" not in str(error) and "table of kinds" in str(error)


def test_a_status_the_publisher_is_not_known_to_write_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, place(Q1, MUSEUM, status="zzyzx_parva"))
    assert error.rule == "input_is_as_described" and "zzyzx" not in str(error)


@pytest.mark.parametrize("column", ["geometry", "taxonomy", "operating_status", "sources"])
def test_a_part_that_lacks_a_column_that_is_read_stops_the_build(tmp_path: Path, column: str):
    taken = tuple(name for name in Wanted().columns if name != column)
    error = refused(tmp_path, *IN_THE_TOWN, wanted=Wanted(columns=taken))
    assert error.rule == "input_is_as_described"


def test_a_whole_file_that_lacks_a_column_that_is_read_stops_the_build(tmp_path: Path):
    error = refused(tmp_path, *IN_THE_TOWN, whole=True, without=("taxonomy",))
    assert error.rule == "input_is_as_described"


def test_a_place_that_is_no_point_stops_the_build(tmp_path: Path):
    line = struct.pack("<BII", 1, 2, 2) + struct.pack("<dddd", 2.0, 53.0, 2.1, 53.1)
    for geometry in (line, b"", b"\x01\x01\x00\x00\x00", b"not a point"):
        error = refused(tmp_path / geometry.hex()[:6], place(Q1, MUSEUM, geometry=geometry))
        assert error.rule == "input_is_as_described"


def test_a_file_whose_most_particular_category_is_not_the_end_of_its_path_stops_the_build(
    tmp_path: Path,
):
    error = refused(tmp_path, place(Q1, MUSEUM, primary="art_gallery"))
    assert error.rule == "input_is_as_described"


def test_a_file_that_is_no_parquet_file_stops_the_build(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    content = b"PAR1 and then nothing that a footer is " * 10
    receipt = places_receipt(content, None)
    again = inputs_of(tmp_path / "again", None, more=[(receipt, content)])
    with pytest.raises(LockError) as stopped:
        culture_file.build(again)
    assert stopped.value.rule == "input_is_as_described"
    with pytest.raises(LockError) as missing:
        culture_file.build(inputs)
    assert missing.value.rule == "input_has_one_receipt"


# The gate


def test_the_gate_is_asked_before_the_file_is_opened(tmp_path: Path):
    real = registry()
    asked: list[tuple[str, Use]] = []

    class Watched:
        def require(self, source_id: str, use: Use) -> object:
            asked.append((source_id, use))
            return real.require(source_id, use)

        def __getattr__(self, name: str) -> object:
            return getattr(real, name)

    inputs = inputs_of(tmp_path, given=Watched())  # pyright: ignore[reportArgumentType]
    culture_file.build(inputs)
    assert asked[0] == (SOURCE, Use.SCORING)
    assert [opened.receipt.source_id for opened in inputs.opened] == [SOURCE]


def test_a_library_and_a_theatre_beside_each_other_are_two_venues_here(tmp_path: Path):
    """The file is read record by record. Which records are one venue is the measure's to say."""
    found = read(tmp_path, place(Q1, LIBRARY), place(Q1, THEATRE), place(Q1, THEATRE))
    assert len(found.venues) == 3
