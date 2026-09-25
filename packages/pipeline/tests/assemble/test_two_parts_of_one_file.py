"""Two parts of one file, which a list takes and a build tells apart by their columns.

The list of places takes London's part of one file twice: as culture reads it,
and again with the brand of each place. The two are one file at one address,
of one edition and one period. What tells them apart is the columns each took,
which the list states and the receipt records.

Every file here is made up. Nothing is fetched and no socket is opened.
"""

from pathlib import Path

import pytest
from burro_pipeline.assemble.cli import of_the_list
from burro_pipeline.evidence.lock import Lock, LockError, seal
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from ..derive.culture_support import (
    CAFE,
    COLUMNS,
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
from ..evidence.support import NO_REPOSITORY, listed

BUILT_AT = "2026-09-24T00:00:00Z"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
TOWN = (place(Q1, MUSEUM), place(Q2, CAFE))
WITH_THE_BRAND = Wanted(columns=(*COLUMNS, "brand"))


def takes_the_brand(receipt: Receipt) -> bool:
    """Whether a receipt is of the part that was taken with the brand."""
    return receipt.taken is not None and "brand" in receipt.taken.columns


def parts(folder: Path) -> tuple[Receipt, Receipt]:
    """The receipt of the part that culture reads, and of the part that holds the brand."""
    written = whole_file(folder, TOWN)
    plain, brand = (part_of(written, wanted) for wanted in (Wanted(), WITH_THE_BRAND))
    return places_receipt(*plain), places_receipt(*brand)


def named(plain: Receipt, brand: Receipt) -> tuple[Listed, Listed]:
    return listed(plain, "places"), listed(brand, "places-with-the-brand")


def sealed(receipts: tuple[Receipt, ...], files: tuple[Listed, ...]) -> Lock:
    vault = {found.vault_key(): found.bytes for found in receipts}
    return seal(
        "lon-2026-09-24-01",
        BUILT_AT,
        COMMIT,
        receipts,
        vault,
        registry(),
        NO_REPOSITORY,
        listed=files,
    )


def test_the_two_parts_are_said_alike_but_for_the_columns_each_took(tmp_path: Path):
    plain, brand = parts(tmp_path)
    assert plain.file_id != brand.file_id
    assert (plain.source_id, plain.use, plain.edition, plain.data_period, plain.url) == (
        brand.source_id,
        brand.use,
        brand.edition,
        brand.data_period,
        brand.url,
    )
    assert plain.publisher_file == brand.publisher_file
    assert plain.taken is not None and brand.taken is not None
    assert set(brand.taken.columns) - set(plain.taken.columns) == {"brand"}


@pytest.mark.parametrize("order", [(0, 1), (1, 0)])
def test_each_item_of_the_list_is_paired_with_the_part_it_took(
    tmp_path: Path, order: tuple[int, int]
):
    """Whatever order the folder of receipts gives them in."""
    both = parts(tmp_path)
    files = named(*both)
    found, with_one, without = of_the_list([both[n] for n in order], files)
    assert [one.file_id for one in found] == [both[0].file_id, both[1].file_id]
    assert [file.item for file in with_one] == ["places", "places-with-the-brand"]
    assert without == []


def test_an_item_whose_part_has_no_receipt_is_not_given_the_other_part(tmp_path: Path):
    plain, brand = parts(tmp_path)
    files = named(plain, brand)
    found, with_one, without = of_the_list([brand], files)
    assert [one.file_id for one in found] == [brand.file_id]
    assert [file.item for file in with_one] == ["places-with-the-brand"]
    assert [file.item for file in without] == ["places"]


def test_a_build_seals_both_parts_of_one_file(tmp_path: Path):
    both = parts(tmp_path)
    lock = sealed(both, named(*both))
    assert {held.name for held in lock.inputs} == {one.file_id for one in both}


def test_a_part_the_list_does_not_name_is_refused(tmp_path: Path):
    plain, brand = parts(tmp_path)
    with pytest.raises(LockError) as stopped:
        sealed((plain, brand), (listed(plain, "places"),))
    assert stopped.value.rule == "receipt_is_listed"


def test_a_part_the_list_names_and_no_receipt_is_of_is_refused(tmp_path: Path):
    plain, brand = parts(tmp_path)
    with pytest.raises(LockError) as stopped:
        sealed((plain,), named(plain, brand))
    assert stopped.value.rule == "listed_file_has_a_receipt"


def test_a_step_is_handed_the_part_it_asks_for_by_what_the_part_holds(tmp_path: Path):
    plain, brand = parts(tmp_path)
    written = whole_file(tmp_path / "again", TOWN)
    content, taken = part_of(written, WITH_THE_BRAND)
    inputs = inputs_of(tmp_path / "store", TOWN, more=[(places_receipt(content, taken), content)])
    with pytest.raises(LockError) as stopped:
        inputs.open(SOURCE, Use.SCORING)
    assert stopped.value.rule == "input_has_one_receipt"
    asked = inputs.open(SOURCE, Use.SCORING, holding=takes_the_brand)
    assert asked.file_id == brand.file_id
    other = inputs.open(SOURCE, Use.SCORING, holding=lambda receipt: not takes_the_brand(receipt))
    assert other.file_id == plain.file_id
