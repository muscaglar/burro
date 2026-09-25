"""A file a person saved from a browser. Every file is made up, and no socket is opened."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from burro_pipeline.evidence import How, Period, read_receipts
from burro_pipeline.fetch.by_hand import keep_by_hand, saved_at
from burro_pipeline.fetch.run import Outcome, Status, Why, fetch
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Registry, Use, load

from .support import MADE_UP_REGISTRY, made_up_workbook

NOW = datetime(2026, 9, 24, 17, 30, 0, tzinfo=UTC)
# A page the made-up registry entry holds. A file is saved from an address on its host.
PAGE = "https://made-up.example/notes"


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    path = tmp_path / "registry.toml"
    path.write_text(MADE_UP_REGISTRY, encoding="utf-8")
    return load(path)


@pytest.fixture
def store(tmp_path: Path) -> FolderStore:
    return FolderStore(tmp_path / "store")


@pytest.fixture
def receipts(tmp_path: Path) -> Path:
    return tmp_path / "receipts"


@pytest.fixture
def saved(tmp_path: Path) -> Path:
    folder = tmp_path / "Downloads"
    folder.mkdir()
    rows: list[list[str | int | float | None]] = [
        ["Area code", "Made-up indicator"],
        *[[f"E0{n}", n / 10] for n in range(1, 5)],
    ]
    return made_up_workbook(folder / "File 8 - made up.xlsx", {"Made up": rows})


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "made-up-file-8",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up indicators",
        "format": "xlsx",
        "page": PAGE,
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025"},
        "by_hand": True,
        **changed,
    }
    return Listed.model_validate(fields)


def keep(
    saved: Path,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    file: Listed | None = None,
    address: str = f"{PAGE}/download",
    day: str = "2026-09-24",
) -> Outcome:
    return keep_by_hand(1, file or listed(), saved, address, day, registry, store, receipts, NOW)


def test_a_file_saved_by_hand_is_stored_with_a_receipt_that_says_so(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    outcome = keep(saved, registry, store, receipts)
    sha256 = hashlib.sha256(saved.read_bytes()).hexdigest()
    assert (outcome.status, outcome.why, outcome.by_hand) == (Status.OK, None, True)
    (receipt,) = read_receipts(receipts)
    assert receipt.how is How.BY_HAND
    assert receipt.url == f"{PAGE}/download"
    assert receipt.retrieved_at == "2026-09-24T00:00:00Z"
    assert receipt.retrieved_on == "2026-09-24"
    assert receipt.publisher_file == "File 8 - made up.xlsx"
    assert (receipt.sha256, receipt.bytes) == (sha256, saved.stat().st_size)
    assert (receipt.edition, receipt.data_period) == ("2025", Period(as_at="2025"))
    assert [held.key for held in store.list()] == [receipt.vault_key()]
    assert saved.exists()
    assert " by_hand=1 " in outcome.line()


def test_the_gate_is_asked_before_the_file_is_opened(
    registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path
):
    file = listed(source_id="made-up-rail", use=Use.ROUTING)
    outcome = keep(tmp_path / "is-not-there.xlsx", registry, store, receipts, file)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.GATE)
    assert "is gated, not approved" in outcome.detail
    assert store.list() == [] and not receipts.exists()


def test_a_time_may_be_given_in_place_of_a_day(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    keep(saved, registry, store, receipts, day="2026-09-24T16:45:10Z")
    assert read_receipts(receipts)[0].retrieved_at == "2026-09-24T16:45:10Z"


@pytest.mark.parametrize(
    "day",
    [
        "",
        "yesterday",
        "24/09/2026",
        "2026-13-01",
        "2026-02-30",
        "2026-09-26",
        "2026-09-24T25:00:00Z",
    ],
)
def test_a_day_that_is_no_day_or_has_not_come_is_refused(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path, day: str
):
    outcome = keep(saved, registry, store, receipts, day=day)
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.DAY_GIVEN)
    assert store.list() == [] and not receipts.exists()


def test_a_day_is_written_as_midnight_and_a_clock_in_another_zone_is_allowed_for():
    assert saved_at("2026-09-24", NOW) == "2026-09-24T00:00:00Z"
    assert saved_at("2026-09-25", NOW) == "2026-09-25T00:00:00Z"
    assert saved_at("2026-09-26", NOW) is None
    assert saved_at("2021-03-21", NOW) == "2021-03-21T00:00:00Z"


@pytest.mark.parametrize(
    "address",
    [
        "",
        "made-up.example/file",
        "http://made-up.example/file",
        "file:///made-up/folder/file.xlsx",
        "https://user:word@made-up.example/file",  # public-only: allow
        "https://",
    ],
)
def test_an_address_that_cannot_be_cited_is_refused(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path, address: str
):
    outcome = keep(saved, registry, store, receipts, address=address)
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.ADDRESS_GIVEN)
    assert store.list() == [] and not receipts.exists()


def test_a_key_in_the_address_a_browser_was_given_is_not_written_down(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    address = f"{PAGE}/download?file=8&token=zzyzx-canary&X-Amz-Signature=zzyzx&k=zzyzx#top"
    file = listed(url=f"{PAGE}/download?file=8", url_parameters=["file"])
    assert keep(saved, registry, store, receipts, file, address=address).status is Status.OK
    assert read_receipts(receipts)[0].url == f"{PAGE}/download?file=8"


# Two addresses as publishers write them. A receipt writes each another way: the `/` in the
# value of a parameter is encoded, and a parameter with no value is given an empty one.
AS_THE_LIST_WRITES_IT = {
    "https://made-up.example/file?uri=/notes/2025/file-8.xlsx": ["uri"],
    "https://made-up.example/downloads?area=GB&format=Workbook&redirect": [
        "area",
        "format",
        "redirect",
    ],
}


@pytest.fixture
def names_each_whole(tmp_path: Path) -> Registry:
    """The made-up registry, with an entry that names each of the two addresses whole."""
    whole = "".join(f'    "{address}",\n' for address in AS_THE_LIST_WRITES_IT)
    prefix = '    "https://made-up.example/notes/",\n'
    assert MADE_UP_REGISTRY.count(prefix) == 1
    path = tmp_path / "whole.toml"
    path.write_text(MADE_UP_REGISTRY.replace(prefix, whole), encoding="utf-8")
    return load(path)


@pytest.mark.parametrize("address", AS_THE_LIST_WRITES_IT)
def test_a_file_is_taken_from_the_address_of_its_item_as_the_list_writes_it(
    saved: Path, names_each_whole: Registry, store: FolderStore, receipts: Path, address: str
):
    """A file that was fetched is handed over again from where it is kept, to another store.

    The entry names the address as the list writes it. So the address a person gives is held
    as the list writes it where it is the list's own, however a receipt writes it."""
    file = listed(url=address, url_parameters=AS_THE_LIST_WRITES_IT[address], by_hand=False)
    outcome = keep(saved, names_each_whole, store, receipts, file, address=address)
    assert (outcome.status, outcome.why) == (Status.OK, None)
    # With a key a browser was given, too: it is no part of the address.
    again = keep(saved, names_each_whole, store, receipts, file, address=f"{address}&token=zzyzx")
    assert (again.status, again.new) == (Status.OK, False)
    (receipt,) = read_receipts(receipts)
    assert "zzyzx" not in receipt.url and receipt.how is How.BY_HAND


@pytest.mark.parametrize(
    "given",
    [
        "https://made-up.example/file?uri=/notes/2025/file-9.xlsx",
        "https://made-up.example/file",
        "https://made-up.example/downloads?area=GB&format=Workbook",
        "https://made-up.example/downloads?area=NI&format=Workbook&redirect",
    ],
)
def test_an_address_that_is_not_the_lists_own_is_held_to_the_entry_as_it_was_given(
    saved: Path, names_each_whole: Registry, store: FolderStore, receipts: Path, given: str
):
    (address,) = [one for one in AS_THE_LIST_WRITES_IT if one.startswith(given.split("?")[0])]
    file = listed(url=address, url_parameters=AS_THE_LIST_WRITES_IT[address], by_hand=False)
    outcome = keep(saved, names_each_whole, store, receipts, file, address=given)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert store.list() == [] and not receipts.exists()


@pytest.mark.parametrize("what", ["missing", "folder"])
def test_a_path_that_is_not_a_file_is_refused(
    registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path, what: str
):
    path = tmp_path / "not-a-file"
    if what == "folder":
        path.mkdir()
    outcome = keep(path, registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.NOT_A_FILE)


def test_a_link_is_followed_to_the_file_it_names(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path
):
    link = tmp_path / "link.xlsx"
    link.symlink_to(saved)
    assert keep(link, registry, store, receipts).status is Status.OK
    assert read_receipts(receipts)[0].publisher_file == "link.xlsx"


def test_a_file_over_the_size_stated_is_refused(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    outcome = keep(saved, registry, store, receipts, listed(max_bytes=10))
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.TOO_LARGE)
    assert store.list() == []


def test_a_saved_page_is_not_taken_for_the_file(
    registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path
):
    page = tmp_path / "File 8.xlsx"
    page.write_bytes(b"<!DOCTYPE html><html><body>Sign in to download</body></html>")
    outcome = keep(page, registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.UNREADABLE, Why.NOT_THE_FORMAT)
    assert store.list() == [] and not receipts.exists()


def test_a_file_whose_period_is_not_stated_is_stored_without_a_receipt(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    outcome = keep(saved, registry, store, receipts, listed(data_period=None))
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SURE)
    assert len(store.list()) == 1 and not receipts.exists()


def test_once_saved_by_hand_a_file_is_found_by_a_run_of_fetch(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    def never(*_: object, **__: object):
        raise AssertionError("a file saved by hand is never asked of a publisher")

    def run() -> Outcome:
        (outcome,) = fetch([listed()], registry, store, receipts, agent="made up", downloader=never)
        return outcome

    assert (run().status, run().why) == (Status.MISSING, Why.NOT_SAVED_BY_HAND)
    kept = keep(saved, registry, store, receipts)
    found = run()
    assert (found.status, found.held, found.by_hand) == (Status.OK, kept.held, True)


def test_a_file_of_another_edition_is_not_the_one_a_run_looks_for(
    saved: Path, registry: Registry, store: FolderStore, receipts: Path
):
    keep(saved, registry, store, receipts)
    (outcome,) = fetch([listed(edition="2026")], registry, store, receipts, agent="made up")
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SAVED_BY_HAND)
