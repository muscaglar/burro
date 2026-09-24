"""A receipt records the address the list gave, as well as the address the file came from.

A publisher may send a request on. The receipt held the address the file came
from in the end, and nothing of the address that was asked. So a person who
read a receipt could not tell which address of the list, and so which address
of the registry entry, the file was fetched under. A receipt now holds both.

A receipt that has no such address leaves the field out, and is written as it
was before the field: one of a file saved by hand whose list gives no address,
and one of a made-up file. Every file here is made up, and no socket is opened.
"""

import json
from pathlib import Path

import pytest
from burro_pipeline.evidence import (
    Geography,
    How,
    Period,
    Receipt,
    file_id_of,
    made_up_receipt,
    read_receipts,
)
from burro_pipeline.fetch.run import Arrival, Status, keep
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Use
from pydantic import ValidationError

CONTENT = b"code,homes\nmade-up-1,10\n"
LISTED = "https://files.made-up.example/files/latest?year=2025"
FINAL = "https://cdn.made-up.example/2025/homes-v2.csv"
WITH_A_LOGIN = "https://made-up:made-up@files.made-up.example/latest"  # public-only: allow


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": LISTED,
        "url_parameters": ["year"],
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def kept(tmp_path: Path, file: Listed, arrived_from: str, how: How = How.FETCHED) -> Receipt:
    """The receipt of a file of the list that arrived from an address."""
    path = tmp_path / "arrived"
    path.write_bytes(CONTENT)
    arrival = Arrival(path, "homes.csv", arrived_from, "2026-09-24T09:12:31Z", how)
    outcome = keep(1, file, arrival, FolderStore(tmp_path / "store"), tmp_path / "receipts")
    assert outcome.status is Status.OK
    (receipt,) = read_receipts(tmp_path / "receipts")
    return receipt


def as_written(tmp_path: Path, receipt: Receipt) -> dict[str, object]:
    path = tmp_path / "receipts" / receipt.source_id / f"{receipt.file_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def receipt_of(**changed: object) -> Receipt:
    sha256 = "ab" * 32
    fields: dict[str, object] = {
        "file_id": file_id_of(sha256),
        "source_id": "made-up-homes",
        "use": Use.SCORING,
        "publisher_file": "homes.csv",
        "url": FINAL,
        "sha256": sha256,
        "bytes": 24,
        "retrieved_at": "2026-09-24T09:12:31Z",
        "how": How.FETCHED,
        "edition": "2025",
        "data_period": Period(as_at="2025-03-31"),
        **changed,
    }
    return Receipt.model_validate(fields)


# What fetch writes


def test_a_receipt_holds_the_address_the_list_gave_and_the_address_the_file_came_from(
    tmp_path: Path,
):
    receipt = kept(tmp_path, listed(may_redirect_to=["cdn.made-up.example"]), f"{FINAL}?sig=zzyzx")
    assert (receipt.listed_url, receipt.url) == (LISTED, FINAL)
    written = as_written(tmp_path, receipt)
    assert (written["listed_url"], written["url"]) == (LISTED, FINAL)
    assert "zzyzx" not in json.dumps(written)


def test_a_file_that_was_not_sent_on_holds_the_same_address_twice(tmp_path: Path):
    receipt = kept(tmp_path, listed(), LISTED)
    assert receipt.listed_url == receipt.url == LISTED


def test_a_file_saved_by_hand_holds_the_address_the_list_gives_if_it_gives_one(tmp_path: Path):
    saved_from = "https://files.made-up.example/files/latest?year=2025&token=zzyzx"
    receipt = kept(tmp_path, listed(by_hand=True), saved_from, How.BY_HAND)
    assert (receipt.listed_url, receipt.url) == (LISTED, LISTED)


def test_a_file_saved_by_hand_whose_list_gives_no_address_leaves_the_field_out(tmp_path: Path):
    file = listed(url="", url_parameters=[], by_hand=True)
    receipt = kept(tmp_path, file, "https://made-up.example/notes/download", How.BY_HAND)
    assert receipt.listed_url is None
    assert "listed_url" not in as_written(tmp_path, receipt)


def test_the_first_receipt_stands_when_the_list_gives_the_file_another_address(tmp_path: Path):
    first = kept(tmp_path, listed(), LISTED)
    moved = listed(url="https://files.made-up.example/files/2025/homes.csv", url_parameters=[])
    path = tmp_path / "arrived"
    arrival = Arrival(path, "homes.csv", moved.url, "2026-12-18T00:00:00Z", How.FETCHED)
    outcome = keep(1, moved, arrival, FolderStore(tmp_path / "store"), tmp_path / "receipts")
    assert outcome.status is Status.OK
    assert read_receipts(tmp_path / "receipts") == (first,)


# The record


def test_a_receipt_written_before_the_field_is_read_and_written_as_it_was():
    before = receipt_of()
    written = before.canonical()
    assert b"listed_url" not in written
    assert Receipt.model_validate_json(written) == before
    assert Receipt.model_validate_json(written).canonical() == written
    assert "listed_url" not in before.model_dump(mode="json")


def test_a_receipt_with_the_field_is_read_back_as_it_was_written():
    receipt = receipt_of(listed_url=LISTED)
    assert json.loads(receipt.canonical())["listed_url"] == LISTED
    assert Receipt.model_validate_json(receipt.canonical()) == receipt
    assert receipt != receipt_of()


@pytest.mark.parametrize(
    "address",
    [
        "",
        "http://files.made-up.example/files/latest",
        "files.made-up.example/files/latest",
        "https://files.made-up.example/files/latest?token=zzyzx",
        "https://files.made-up.example/files/latest?api_key=zzyzx",
        "https://files.made-up.example/files/latest#part",
        WITH_A_LOGIN,
    ],
)
def test_the_address_the_list_gave_is_held_as_clean_as_the_other(address: str):
    with pytest.raises(ValidationError) as refused:
        receipt_of(listed_url=address)
    assert "zzyzx" not in str(refused.value)


def test_a_made_up_file_has_no_address_of_either_kind():
    made_up = made_up_receipt(
        "made-up-parks.gpkg",
        Use.SCORING,
        Geography.POLYGON,
        Period(as_at="2025-04"),
        "2026-09-23T09:12:31Z",
    )
    assert made_up.listed_url is None and b"listed_url" not in made_up.canonical()
    with pytest.raises(ValidationError):
        Receipt.model_validate(made_up.model_dump(mode="json") | {"listed_url": LISTED})
