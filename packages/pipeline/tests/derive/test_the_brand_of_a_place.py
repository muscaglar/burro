"""The chain a place belongs to, read from the part of the file that was taken with it.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places, and every chain is made up too. The file is read as a
build reads it, from a store, through the licence gate, by its receipt. No
socket is opened.
"""

from pathlib import Path

import pytest
from burro_pipeline.derive import culture_file
from burro_pipeline.derive.culture_file import Brand, Branded
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from .culture_support import (
    CAFE,
    CANARY,
    COLUMNS,
    IN_THE_TOWN,
    MUSEUM,
    Q1,
    Q2,
    SOURCE,
    Wanted,
    inputs_of,
    part_of,
    place,
    places_receipt,
    whole_file,
)

# The columns the second item of the list takes: those of the first, and the brand.
WITH_THE_BRAND = Wanted(columns=(*COLUMNS, "brand"))
# Two chains that do not exist, each with the id a made-up encyclopaedia gives it.
GILDCREST, PLAINFARE = ("Gildcrest", "Q00000001"), ("Plainfare", "Q00000002")


def read(folder: Path, *places: object, **how: object) -> list[Branded]:
    inputs = inputs_of(folder, places, wanted=WITH_THE_BRAND, **how)  # pyright: ignore[reportArgumentType]
    return list(culture_file.branded(culture_file.opened_with_the_brand(inputs)))


def test_a_place_of_a_chain_is_read_with_the_name_and_the_id_of_its_chain(tmp_path: Path):
    (found,) = read(tmp_path, place(Q1, CAFE, brand=GILDCREST))
    assert found.brand == Brand(name="Gildcrest", wikidata="Q00000001")
    assert found.record.hierarchy == CAFE and found.record.at is not None


def test_a_place_of_no_chain_has_no_brand(tmp_path: Path):
    (found,) = read(tmp_path, place(Q1, CAFE, brand=None))
    assert found.brand is None


@pytest.mark.parametrize(
    ("written", "read_as"),
    [
        (("Gildcrest", None), Brand("Gildcrest", None)),
        ((None, "Q00000001"), Brand(None, "Q00000001")),
        (("  Gildcrest ", ""), Brand("Gildcrest", None)),
        ((None, None), None),
        (("", "  "), None),
    ],
)
def test_a_brand_with_a_part_missing_is_read_as_far_as_it_goes(
    tmp_path: Path, written: tuple[str | None, str | None], read_as: Brand | None
):
    (found,) = read(tmp_path, place(Q1, CAFE, brand=written))
    assert found.brand == read_as


def test_each_row_keeps_its_own_brand_across_row_groups(tmp_path: Path):
    town = [
        place((float(east), 0.0), CAFE, brand=(f"Chain {east}", None) if east % 3 else None)
        for east in range(0, 1_100, 100)
    ]
    found = read(tmp_path, *town, rows_in_a_group=4)
    assert len(found) == len(town)
    by_east = sorted(found, key=lambda one: one.record.at or (0.0, 0.0))
    assert [one.brand.name if one.brand else None for one in by_east] == [
        f"Chain {east}" if east % 3 else None for east in range(0, 1_100, 100)
    ]


def test_what_is_read_of_a_row_beside_its_brand_is_what_every_measure_reads(tmp_path: Path):
    town = [place(Q1, MUSEUM, brand=None), place(Q2, CAFE, brand=GILDCREST, status=None)]
    inputs = inputs_of(tmp_path, town, wanted=WITH_THE_BRAND)
    opened = culture_file.opened_with_the_brand(inputs)
    assert [one.record for one in culture_file.branded(opened)] == list(
        culture_file.records(opened)
    )


def test_no_name_of_a_place_no_address_and_no_id_of_a_place_is_read(tmp_path: Path):
    """The canary stands in every field that is never read, and in what else the brand holds."""
    town = [place(Q1, CAFE, brand=GILDCREST), place(Q2, CAFE, brand=None)]
    found = read(tmp_path, *town, packed="none")
    assert CANARY not in repr(found)
    assert set(Branded.__dataclass_fields__) == {"record", "brand"}
    assert set(Brand.__dataclass_fields__) == {"name", "wikidata"}
    assert culture_file.BRAND_READ == ("brand.wikidata", "brand.names.primary")


def test_the_part_holds_no_column_that_names_a_place(tmp_path: Path):
    inputs = inputs_of(tmp_path, [place(Q1, CAFE, brand=GILDCREST)], wanted=WITH_THE_BRAND)
    opened = culture_file.opened_with_the_brand(inputs)
    assert opened.receipt.taken is not None
    taken = {name.split(".")[0] for name in opened.receipt.taken.columns}
    assert "brand" in taken
    assert not taken & {"id", "names", "addresses", "phones", "websites", "socials", "emails"}


def test_a_file_that_was_kept_whole_is_read_the_same(tmp_path: Path):
    town = [place(Q1, CAFE, brand=GILDCREST), place(Q2, CAFE, brand=None)]
    assert read(tmp_path / "a", *town) == read(tmp_path / "b", *town, whole=True)


def test_the_part_that_culture_reads_gives_no_brand_and_stops_the_build(tmp_path: Path):
    """A part that was taken with no brand holds none, and nothing is read in its place."""
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    with pytest.raises(LockError) as stopped:
        list(culture_file.branded(culture_file.opened_of(inputs)))
    assert stopped.value.rule == "input_is_as_described"
    with pytest.raises(LockError) as none:
        culture_file.opened_with_the_brand(inputs)
    assert none.value.rule == "input_has_one_receipt"


def test_of_two_parts_of_one_file_each_reader_is_handed_its_own(tmp_path: Path):
    """The list takes the part twice. Culture reads the one with no brand, as it always did."""
    town = [place(Q1, MUSEUM, brand=GILDCREST), place(Q2, CAFE, brand=PLAINFARE)]
    written = whole_file(tmp_path / "again", town)
    content, taken = part_of(written, WITH_THE_BRAND)
    inputs = inputs_of(tmp_path, town, more=[(places_receipt(content, taken), content)])
    plain, with_brand = (
        culture_file.opened_of(inputs),
        culture_file.opened_with_the_brand(inputs),
    )
    assert plain.file_id != with_brand.file_id
    assert not culture_file.takes_the_brand(plain.receipt)
    assert culture_file.takes_the_brand(with_brand.receipt)
    assert len(culture_file.build(inputs).venues) == 1
    assert [one.brand for one in culture_file.branded(with_brand)] == [
        Brand(*GILDCREST),
        Brand(*PLAINFARE),
    ]


def test_a_brand_that_is_not_laid_out_as_the_publisher_lays_it_out_stops_the_build(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, [place(Q1, CAFE)], whole=True, without=("brand",))
    with pytest.raises(LockError) as stopped:
        list(culture_file.branded(culture_file.opened_with_the_brand(inputs)))
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value) and str(tmp_path) not in str(stopped.value)


def test_the_gate_is_asked_for_scoring_before_the_part_is_opened(tmp_path: Path):
    real = registry()
    asked: list[tuple[str, Use]] = []

    class Watched:
        def require(self, source_id: str, use: Use) -> object:
            asked.append((source_id, use))
            return real.require(source_id, use)

        def __getattr__(self, name: str) -> object:
            return getattr(real, name)

    inputs = inputs_of(
        tmp_path,
        [place(Q1, CAFE, brand=GILDCREST)],
        wanted=WITH_THE_BRAND,
        given=Watched(),  # pyright: ignore[reportArgumentType]
    )
    list(culture_file.branded(culture_file.opened_with_the_brand(inputs)))
    assert asked[0] == (SOURCE, Use.SCORING)
