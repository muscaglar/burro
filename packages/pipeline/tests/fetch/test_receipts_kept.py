"""A receipt is kept in the store beside its file, so that it outlives the machine that fetched.

A hosted run fetches on a machine that is thrown away. The file is safe in the
store. Its receipt was written to that machine's disk, and a figure can be
cited to nothing else. So fetch keeps a copy of the receipt in the store, and
the step `receipts` brings every copy back to the repository.

Every file here is made up. The object store is a stand-in on the loopback
address, and a connection to any other address is blocked.
"""

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import public_log
import pytest
from burro_pipeline.evidence import How, Period, Receipt, file_id_of, read_receipts
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded
from burro_pipeline.fetch.run import WORDS, Arrival, Outcome, Status, Why, fetch, keep
from burro_pipeline.fetch.s3 import S3Store
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore, Store, StoreError
from burro_pipeline.registry import Registry, Use, load

from .support import CANARY_ROW, ONLY_LOOPBACK, Served, made_up_zip, serving
from .test_s3_store import NOW, StandIn, settings

pytestmark = ONLY_LOOPBACK

CONTENT = f"code,homes\nmade-up-1,10\n{CANARY_ROW},20\n".encode()
SHA256 = hashlib.sha256(CONTENT).hexdigest()
KEY = f"receipts/made-up-homes/f-{SHA256[:12]}.json"
Printed = pytest.CaptureFixture[str]


def receipt_of(content: bytes = CONTENT, retrieved_at: str = "2026-09-24T09:12:31Z") -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id="made-up-homes",
        use=Use.SCORING,
        publisher_file="homes.csv",
        url="https://files.made-up.example/files/homes.csv",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=retrieved_at,
        how=How.FETCHED,
        edition="2025",
        data_period=Period(as_at="2025-03-31"),
    )


@pytest.fixture
def stand_in() -> StandIn:
    return StandIn()


@pytest.fixture
def served(stand_in: StandIn) -> Iterator[Served]:
    with serving(stand_in) as server:
        yield server


@pytest.fixture(params=["a folder", "an object store"])
def store(request: pytest.FixtureRequest, tmp_path: Path, served: Served) -> Store:
    if request.param == "a folder":
        return FolderStore(tmp_path / "store")
    return S3Store(settings(served), now=lambda: NOW)


def test_a_receipt_is_kept_under_a_key_of_its_own_and_comes_back_byte_for_byte(store: Store):
    receipt = receipt_of()
    assert receipt.kept_key() == KEY
    assert store.keep_receipt(KEY, receipt.canonical())
    assert store.receipts() == {KEY: receipt.canonical()}
    assert Receipt.model_validate_json(store.receipts()[KEY]) == receipt


def test_the_first_receipt_kept_stands(store: Store):
    first, later = receipt_of(), receipt_of(retrieved_at="2026-12-18T00:00:00Z")
    assert store.keep_receipt(KEY, first.canonical())
    assert not store.keep_receipt(KEY, later.canonical())
    assert store.receipts() == {KEY: first.canonical()}


def test_a_receipt_is_no_file_of_a_publisher_and_is_in_no_listing(store: Store, tmp_path: Path):
    saved = tmp_path / "saved.csv"
    saved.write_bytes(CONTENT)
    held, _ = store.put("made-up-homes", "homes.csv", saved)
    store.keep_receipt(KEY, receipt_of().canonical())
    assert store.list() == [held]
    assert list(store.receipts()) == [KEY]


@pytest.mark.parametrize(
    "key",
    [
        "",
        "receipts/made-up-homes/receipt.json",
        f"receipts/../f-{SHA256[:12]}.json",
        f"receipts/Made-Up/f-{SHA256[:12]}.json",
        f"raw/made-up-homes/{SHA256}/homes.csv",
        f"receipts/made-up-homes/f-{SHA256[:12]}.json/more",
    ],
)
def test_a_key_that_is_not_the_key_of_a_receipt_is_refused(store: Store, key: str):
    with pytest.raises(StoreError, match="not the key of a receipt"):
        store.keep_receipt(key, receipt_of().canonical())
    assert store.receipts() == {}


def test_what_is_too_large_to_be_a_receipt_is_refused(store: Store):
    with pytest.raises(StoreError, match="too large"):
        store.keep_receipt(KEY, b" " * 2_000_000)
    assert store.receipts() == {}


def test_every_request_for_a_receipt_is_signed_and_never_written_over(
    served: Served, stand_in: StandIn
):
    store = S3Store(settings(served), now=lambda: NOW)
    store.keep_receipt(KEY, receipt_of().canonical())
    store.keep_receipt(KEY, receipt_of().canonical())
    assert stand_in.held == {KEY: receipt_of().canonical()}
    assert [request.method for request in served.seen] == ["PUT", "PUT"]
    assert all(request.headers["if-none-match"] == "*" for request in served.seen)
    assert all("Signature=" in request.headers["authorization"] for request in served.seen)


def test_an_object_store_that_fails_names_no_address_bucket_or_key(
    served: Served, stand_in: StandIn
):
    store = S3Store(settings(served), now=lambda: NOW)
    stand_in.fail_with = stand_in.error(500, "InternalError")
    for call in (lambda: store.keep_receipt(KEY, receipt_of().canonical()), store.receipts):
        with pytest.raises(StoreError) as refused:
            call()
        said = str(refused.value)
        assert "500" in said
        assert not [hidden for hidden in ("zzyzx", "127.0.0.1", str(served.port)) if hidden in said]


# Fetch, and the step that brings receipts back


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": "https://files.made-up.example/files/homes.csv",
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def arrived(tmp_path: Path, when: str = "2026-09-24T09:12:31Z") -> Arrival:
    path = tmp_path / "arrived"
    path.write_bytes(CONTENT)
    address = "https://files.made-up.example/files/homes.csv"
    return Arrival(path, "homes.csv", address, when, How.FETCHED)


def test_a_fetch_keeps_the_receipt_it_wrote_in_the_store(store: Store, tmp_path: Path):
    outcome = keep(1, listed(), arrived(tmp_path), store, tmp_path / "receipts")
    assert outcome.status is Status.OK
    (written,) = read_receipts(tmp_path / "receipts")
    assert store.receipts() == {written.kept_key(): written.canonical()}


def test_a_file_fetched_again_keeps_the_receipt_that_already_stands(store: Store, tmp_path: Path):
    keep(1, listed(), arrived(tmp_path), store, tmp_path / "receipts")
    again = keep(1, listed(), arrived(tmp_path, "2026-12-18T00:00:00Z"), store, tmp_path / "again")
    assert again.status is Status.OK
    (first,) = read_receipts(tmp_path / "receipts")
    assert first.retrieved_at == "2026-09-24T09:12:31Z"
    assert store.receipts() == {first.kept_key(): first.canonical()}


def test_a_receipt_in_the_repository_is_the_one_kept_when_the_store_has_none(
    store: Store, tmp_path: Path
):
    """The receipt that was committed stands, whenever the file is fetched again."""
    committed = receipt_of(retrieved_at="2026-09-01T00:00:00Z")
    path = tmp_path / "receipts" / "made-up-homes" / f"{committed.file_id}.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(committed.canonical())
    assert keep(1, listed(), arrived(tmp_path), store, tmp_path / "receipts").status is Status.OK
    assert store.receipts() == {committed.kept_key(): committed.canonical()}


def test_a_file_with_no_receipt_keeps_none_in_the_store(store: Store, tmp_path: Path):
    outcome = keep(1, listed(unsure=["edition"]), arrived(tmp_path), store, tmp_path / "receipts")
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SURE)
    assert len(store.list()) == 1 and store.receipts() == {}


def test_a_store_that_will_not_take_the_receipt_fails_the_file(tmp_path: Path):
    class Full(FolderStore):
        def keep_receipt(self, key: str, content: bytes) -> bool:
            raise StoreError("the store answered 507 to a receipt sent to it")

    outcome = keep(1, listed(), arrived(tmp_path), Full(tmp_path / "store"), tmp_path / "receipts")
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.STORE)
    assert not outcome.done


class Folders:
    def __init__(self, root: Path) -> None:
        self.store, self.receipts = root / "store", root / "data" / "receipts"
        self.environment = {"BURRO_STORE_FOLDER": str(self.store)}
        keep(1, listed(), arrived(root), FolderStore(self.store), root / "on-the-runner")


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


def brought_back(folders: Folders, capsys: Printed) -> tuple[int, list[str], str]:
    """What the step said after its first line, which says which kind of store it was given."""
    code = main(["receipts", "--receipts", str(folders.receipts)], folders.environment, never)
    out = capsys.readouterr()
    first, *lines = out.out.splitlines()
    assert first == "step=store kind=folder" and public_log.is_public(first)
    return code, lines, out.err


def test_receipts_lost_with_the_machine_are_brought_back_from_the_store(
    tmp_path: Path, capsys: Printed
):
    folders = Folders(tmp_path)
    code, lines, words = brought_back(folders, capsys)
    assert (code, words) == (0, "")
    assert lines == ["step=store status=ok receipts=1 new=1 same=0 differs=0 unreadable=0"]
    assert public_log.is_public(lines[0])
    assert read_receipts(folders.receipts) == read_receipts(tmp_path / "on-the-runner")
    (path,) = folders.receipts.rglob("*.json")
    assert path.relative_to(tmp_path).as_posix() == receipt_of().path().as_posix()


def test_bringing_receipts_back_twice_changes_nothing(tmp_path: Path, capsys: Printed):
    folders = Folders(tmp_path)
    brought_back(folders, capsys)
    (path,) = folders.receipts.rglob("*.json")
    written_at = path.stat().st_mtime_ns
    code, lines, _ = brought_back(folders, capsys)
    assert code == 0
    assert lines == ["step=store status=ok receipts=1 new=0 same=1 differs=0 unreadable=0"]
    assert path.stat().st_mtime_ns == written_at


def test_a_receipt_in_the_repository_is_never_written_over_by_the_store(
    tmp_path: Path, capsys: Printed
):
    folders = Folders(tmp_path)
    other = Receipt.model_validate(receipt_of().model_dump(mode="json") | {"edition": "2026"})
    path = tmp_path / other.path()
    path.parent.mkdir(parents=True)
    path.write_bytes(other.canonical())
    code, lines, words = brought_back(folders, capsys)
    assert code == 1
    assert lines == ["step=store status=differs receipts=1 new=0 same=0 differs=1 unreadable=0"]
    assert "says something else" in words and "homes.csv" not in words
    assert path.read_bytes() == other.canonical()


@pytest.mark.parametrize(
    "planted",
    [
        CANARY_ROW.encode(),
        b'{"file_id": "f-000000000000"}',
        receipt_of(b"another made-up file\n").canonical(),
    ],
    ids=["not JSON", "not a receipt", "the receipt of another file"],
)
def test_what_is_kept_as_a_receipt_and_is_not_one_is_counted_and_left_behind(
    tmp_path: Path, capsys: Printed, planted: bytes
):
    folders = Folders(tmp_path)
    (folders.store / KEY).write_bytes(planted)
    code, lines, words = brought_back(folders, capsys)
    assert code == 1
    assert lines == ["step=store status=unreadable receipts=1 new=0 same=0 differs=0 unreadable=1"]
    assert CANARY_ROW not in words and "is not the receipt" in words
    assert not folders.receipts.exists()


def test_with_no_store_named_the_step_says_which_variable_to_set(capsys: Printed):
    assert main(["receipts"], {}, never) == 2
    out = capsys.readouterr()
    assert out.out == "" and "BURRO_STORE_FOLDER" in out.err


def test_a_file_saved_by_hand_has_its_receipt_kept_too(tmp_path: Path):
    from burro_pipeline.fetch.by_hand import keep_by_hand
    from burro_pipeline.registry import load

    from .support import MADE_UP_REGISTRY

    (tmp_path / "registry.toml").write_text(MADE_UP_REGISTRY, encoding="utf-8")
    saved = made_up_zip(tmp_path / "Made-up notes.zip", {"notes.csv": CONTENT})
    store = FolderStore(tmp_path / "store")
    outcome = keep_by_hand(
        1,
        listed(format="zip", by_hand=True),
        saved,
        "https://made-up.example/notes/download",
        "2026-09-24",
        load(tmp_path / "registry.toml"),
        store,
        tmp_path / "receipts",
        datetime(2026, 9, 24, 17, 30, tzinfo=UTC),
    )
    assert outcome.status is Status.OK
    (written,) = read_receipts(tmp_path / "receipts")
    assert written.how is How.BY_HAND
    assert store.receipts() == {written.kept_key(): written.canonical()}


# One receipt, read back by its key


def test_one_receipt_is_read_back_by_its_key(store: Store):
    assert store.receipt(KEY) is None
    store.keep_receipt(KEY, receipt_of().canonical())
    assert store.receipt(KEY) == receipt_of().canonical()
    other = receipt_of(b"another made-up file\n")
    assert store.receipt(other.kept_key()) is None


@pytest.mark.parametrize(
    "key",
    ["", "receipts/../secrets.json", f"raw/made-up-homes/{SHA256}/homes.csv", "receipts/"],
)
def test_nothing_but_a_receipt_is_read_back(store: Store, key: str):
    with pytest.raises(StoreError, match="not the key of a receipt"):
        store.receipt(key)


def test_what_is_too_large_to_be_a_receipt_is_not_read_back(tmp_path: Path, stand_in: StandIn):
    folder = FolderStore(tmp_path / "store")
    (folder.folder / KEY).parent.mkdir(parents=True)
    (folder.folder / KEY).write_bytes(b" " * 2_000_000)
    with pytest.raises(StoreError, match="too large"):
        folder.receipt(KEY)


def test_an_object_store_is_asked_for_one_receipt_with_one_signed_request(
    served: Served, stand_in: StandIn
):
    store = S3Store(settings(served), now=lambda: NOW)
    stand_in.held[KEY] = receipt_of().canonical()
    stand_in.held[f"{KEY}.bak"] = b" " * 2_000_000
    assert store.receipt(KEY) == receipt_of().canonical()
    (request,) = served.seen
    assert (request.method, request.path) == ("GET", f"/zzyzx-canary-bucket/{KEY}")
    assert "Signature=" in request.headers["authorization"]
    stand_in.held[KEY] = b" " * 2_000_000
    with pytest.raises(StoreError, match="too large"):
        store.receipt(KEY)


def test_an_object_store_that_fails_to_give_a_receipt_names_nothing(
    served: Served, stand_in: StandIn
):
    store = S3Store(settings(served), now=lambda: NOW)
    stand_in.fail_with = stand_in.error(500, "InternalError")
    with pytest.raises(StoreError) as refused:
        store.receipt(KEY)
    said = str(refused.value)
    assert "500 InternalError" in said
    assert not [hidden for hidden in ("zzyzx", "127.0.0.1", str(served.port)) if hidden in said]


# A hosted run: the file and its receipt are in the store, and the disk is new


@pytest.mark.parametrize(
    "corrected",
    [
        {"edition": "2026"},
        {"data_period": {"as_at": "2026-03-31"}},
        {"data_period": {"start": "2025-01", "end": "2025-03"}},
        {"use": "display"},
    ],
    ids=["the edition", "the day", "the span", "the use"],
)
def test_a_corrected_edition_is_never_dropped_with_a_run_that_says_ok(
    store: Store, tmp_path: Path, corrected: dict[str, object]
):
    """The list was wrong, the file was fetched, and the list was then put right."""
    first = keep(1, listed(), arrived(tmp_path), store, tmp_path / "first-runner")
    assert first.status is Status.OK
    standing = store.receipts()
    again = keep(1, listed(**corrected), arrived(tmp_path), store, tmp_path / "second-runner")
    assert (again.status, again.why) == (Status.DIFFERS, Why.KEPT_RECEIPT_DIFFERS)
    assert not again.done
    assert " status=differs " in again.line()
    assert f" why={int(Why.KEPT_RECEIPT_DIFFERS)} " in again.line()
    # The receipt in the store stands, and none that says otherwise was written beside it.
    assert store.receipts() == standing
    assert not (tmp_path / "second-runner").exists()


def test_a_file_fetched_again_on_a_new_disk_is_given_the_receipt_that_stands(
    store: Store, tmp_path: Path
):
    keep(1, listed(), arrived(tmp_path), store, tmp_path / "first-runner")
    later = arrived(tmp_path, "2026-12-18T00:00:00Z")
    again = keep(1, listed(), later, store, tmp_path / "second-runner")
    assert (again.status, again.new) == (Status.OK, False)
    assert read_receipts(tmp_path / "second-runner") == read_receipts(tmp_path / "first-runner")
    assert read_receipts(tmp_path / "second-runner")[0].retrieved_at == "2026-09-24T09:12:31Z"


@pytest.mark.parametrize(
    "planted",
    [CANARY_ROW.encode(), b"{}", receipt_of(b"another made-up file\n").canonical()],
    ids=["not JSON", "not a receipt", "the receipt of another file"],
)
def test_what_is_kept_as_the_receipt_of_a_file_and_is_not_is_never_passed_over(
    tmp_path: Path, planted: bytes
):
    store = FolderStore(tmp_path / "store")
    (store.folder / KEY).parent.mkdir(parents=True)
    (store.folder / KEY).write_bytes(planted)
    outcome = keep(1, listed(), arrived(tmp_path), store, tmp_path / "receipts")
    assert (outcome.status, outcome.why) == (Status.DIFFERS, Why.KEPT_RECEIPT_DIFFERS)
    assert CANARY_ROW not in outcome.line() + outcome.words()
    assert (store.folder / KEY).read_bytes() == planted
    assert not (tmp_path / "receipts").exists()


def test_a_receipt_kept_by_another_run_a_moment_ago_is_read_back_and_compared(tmp_path: Path):
    other = Receipt.model_validate(receipt_of().model_dump(mode="json") | {"edition": "2026"})

    class Raced(FolderStore):
        """Another run keeps its receipt after this one looked, and before it kept its own."""

        def keep_receipt(self, key: str, content: bytes) -> bool:
            super().keep_receipt(key, other.canonical())
            return super().keep_receipt(key, content)

    store = Raced(tmp_path / "store")
    outcome = keep(1, listed(), arrived(tmp_path), store, tmp_path / "receipts")
    assert (outcome.status, outcome.why) == (Status.DIFFERS, Why.KEPT_RECEIPT_DIFFERS)
    assert store.receipts() == {KEY: other.canonical()}


def test_a_store_that_cannot_be_asked_for_the_receipt_fails_the_file(tmp_path: Path):
    class Unreadable(FolderStore):
        def receipt(self, key: str) -> bytes | None:
            raise StoreError("the store answered 503 when asked for a receipt")

    store = Unreadable(tmp_path / "store")
    outcome = keep(1, listed(), arrived(tmp_path), store, tmp_path / "receipts")
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.STORE)
    assert not (tmp_path / "receipts").exists() and store.receipts() == {}


CORRECTED = """
schema_version = 1
build = "made-up"

[[file]]
item = "homes"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/files/homes.csv"
max_bytes = 1000000
edition = "2026"
data_period = { as_at = "2025-03-31" }
"""


def test_a_run_that_finds_another_receipt_in_the_store_ends_red(tmp_path: Path, capsys: Printed):
    """As the command line runs it: a new disk, and the list put right since the first run."""
    from .support import MADE_UP_REGISTRY

    folders = Folders(tmp_path)
    (tmp_path / "registry.toml").write_text(MADE_UP_REGISTRY, encoding="utf-8")
    (tmp_path / "list.toml").write_text(CORRECTED, encoding="utf-8")

    def downloader(
        address: str,
        to: Path,
        limits: object,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
    ) -> Downloaded:
        to.write_bytes(CONTENT)
        return Downloaded(SHA256, len(CONTENT), address, "homes.csv", "text/csv")

    arguments = ["fetch", "--list", str(tmp_path / "list.toml")]
    arguments += ["--registry", str(tmp_path / "registry.toml")]
    arguments += ["--receipts", str(tmp_path / "second-runner")]
    environment = folders.environment | {"BURRO_FETCH_CONTACT": "data@made-up.example"}
    assert main(arguments, environment, downloader) == 1
    printed = capsys.readouterr().out.splitlines()
    assert printed[-1] == (
        "step=fetch status=failed files=1 ok=0 skipped=0 refused=0 failed=0 missing=0 "
        "unreadable=0 differs=1"
    )
    assert f" status=differs file_id=f-{SHA256[:12]} " in printed[-2]
    assert " new=0 why=16 " in printed[-2]
    real = printed[-2].replace("source=made-up-homes", "source=synthetic")
    assert public_log.is_public(real)
    assert not (tmp_path / "second-runner").exists()


# An item that is saved by hand, looked for by fetch among the receipts


def handed_over(tmp_path: Path, **changed: object) -> tuple[Registry, FolderStore, Path]:
    """A made-up file that a person saved and handed over, under the list as it then stood."""
    from burro_pipeline.fetch.by_hand import keep_by_hand

    from .support import MADE_UP_REGISTRY

    (tmp_path / "registry.toml").write_text(MADE_UP_REGISTRY, encoding="utf-8")
    registry = load(tmp_path / "registry.toml")
    store, receipts = FolderStore(tmp_path / "store"), tmp_path / "receipts"
    name = str(changed.pop("saved_as", "made-up notes.csv"))
    saved = tmp_path / name
    saved.write_bytes(CONTENT + name.encode())
    outcome = keep_by_hand(
        1,
        by_hand(**changed),
        saved,
        "https://made-up.example/notes/download",
        "2026-09-24",
        registry,
        store,
        receipts,
        datetime(2026, 9, 24, 17, 30, tzinfo=UTC),
    )
    assert outcome.status is Status.OK
    return registry, store, receipts


def by_hand(**changed: object) -> Listed:
    return listed(page="https://made-up.example/notes", url="", by_hand=True, **changed)


def looked_for(file: Listed, registry: Registry, store: FolderStore, receipts: Path) -> Outcome:
    (outcome,) = fetch([file], registry, store, receipts, agent="made up", downloader=never)
    return outcome


def test_an_item_saved_by_hand_is_found_by_the_receipt_that_says_what_the_list_says(
    tmp_path: Path,
):
    registry, store, receipts = handed_over(tmp_path)
    outcome = looked_for(by_hand(), registry, store, receipts)
    assert (outcome.status, outcome.why, outcome.by_hand) == (Status.OK, None, True)
    (written,) = read_receipts(receipts)
    assert outcome.held is not None and outcome.held.sha256 == written.sha256


@pytest.mark.parametrize(
    "changed",
    [
        {"data_period": {"as_at": "2024-03-31"}},
        {"data_period": {"start": "2025-03-31", "end": "2025-04-01"}},
        {"use": "display"},
        {"use": "display", "data_period": {"as_at": "2024-03-31"}},
    ],
    ids=["the period", "a span", "the use", "both"],
)
def test_an_item_saved_by_hand_differs_when_its_receipt_says_something_else_than_the_list(
    tmp_path: Path, changed: dict[str, object]
):
    """As it was, fetch said ok of any receipt saved by hand with the edition the list gives."""
    registry, store, receipts = handed_over(tmp_path)
    (before,) = read_receipts(receipts)
    outcome = looked_for(by_hand(**changed), registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.DIFFERS, Why.RECEIPT_DIFFERS)
    assert outcome.held is None and not outcome.done
    assert " status=differs by_hand=1 why=7 " in outcome.line()
    assert read_receipts(receipts) == (before,)


def test_an_item_saved_by_hand_in_another_edition_has_not_been_saved(tmp_path: Path):
    registry, store, receipts = handed_over(tmp_path)
    outcome = looked_for(by_hand(edition="2026"), registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SAVED_BY_HAND)


def test_each_item_saved_by_hand_under_one_source_finds_its_own_receipt(tmp_path: Path):
    """Two files of one edition, saved by hand under one source, for two periods."""
    registry, store, receipts = handed_over(tmp_path)
    handed_over(tmp_path, data_period={"as_at": "2024-03-31"}, saved_as="made-up notes 2024.csv")
    first, second = read_receipts(receipts)
    assert first.sha256 != second.sha256
    for period in ({"as_at": "2025-03-31"}, {"as_at": "2024-03-31"}):
        outcome = looked_for(by_hand(data_period=period), registry, store, receipts)
        assert outcome.status is Status.OK
        assert outcome.held is not None
        kept = next(r for r in (first, second) if r.sha256 == outcome.held.sha256)
        assert kept.data_period == Period.model_validate(period)


def test_a_receipt_of_a_fetched_file_is_no_receipt_of_an_item_saved_by_hand(
    store: FolderStore, tmp_path: Path
):
    from .support import MADE_UP_REGISTRY

    (tmp_path / "registry.toml").write_text(MADE_UP_REGISTRY, encoding="utf-8")
    receipts = tmp_path / "receipts"
    assert keep(1, listed(), arrived(tmp_path), store, receipts).status is Status.OK
    outcome = looked_for(by_hand(), load(tmp_path / "registry.toml"), store, receipts)
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SAVED_BY_HAND)


def test_the_words_of_a_receipt_that_differs_name_the_use_too():
    assert "the edition, the period or the use" in WORDS[Why.RECEIPT_DIFFERS]
