"""A file whose publisher names no edition, and puts another file at the same address.

The list says where such a file states its own edition. Fetch reads it in what
arrives, before anything is kept, and writes the receipt from that. So a second
fetch does one of three things, and these hold it to each.

    the same bytes, the same day   nothing new, and the receipt stands
    new bytes, a new day           a new file and a new receipt, beside the old
    new bytes, the same day        refused: one edition is one file

Every file is made up and shaped like a publisher's. The object store is a
stand-in on the loopback address, and a connection to any other address is blocked.
"""

import hashlib
from collections.abc import Iterator
from pathlib import Path

import public_log
import pytest
from burro_pipeline.evidence import EditionFrom, How, Period, Receipt, Where, read_receipts
from burro_pipeline.fetch import run
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.run import WORDS, Arrival, Outcome, Standing, Status, Why, keep
from burro_pipeline.fetch.s3 import S3Store
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore, Store

from .dated_support import (
    DAY,
    RETRIEVED_AT,
    TIME,
    block,
    geopackage,
    header_block,
    header_of,
    register,
    street_extract,
)
from .support import CANARY_ROW, ONLY_LOOPBACK, Answer, Served, serving
from .test_cli import Folders, never, printed, through
from .test_fetch_run import as_the_log_knows_it
from .test_s3_store import NOW, StandIn, settings

pytestmark = ONLY_LOOPBACK

ADDRESS = "https://files.made-up.example/files/register-501.xml"
LATER = "2026-10-01T09:12:31Z"
IN_THE_HEADER = {
    "where": "xml_header",
    "at": "Header/ExtractDate",
    "words": "extract of",
    "period_too": True,
}
THE_DAY_RETRIEVED = {"where": "retrieved", "at": "", "words": "retrieved", "period_too": True}
LAST_CHANGE = {
    "where": "geopackage",
    "at": "gpkg_contents.last_change",
    "words": "last changed",
    "period_too": False,
}
RUNS_TO = {
    "where": "street_extract",
    "at": "OSMHeader.osmosis_replication_timestamp",
    "period_too": True,
}


@pytest.fixture
def served() -> Iterator[Served]:
    with serving(StandIn()) as server:
        yield server


@pytest.fixture(params=["a folder", "an object store"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Store:
    if request.param == "a folder":
        return FolderStore(tmp_path / "store")
    return S3Store(settings(request.getfixturevalue("served")), now=lambda: NOW)


@pytest.fixture
def folder(tmp_path: Path) -> FolderStore:
    return FolderStore(tmp_path / "store")


@pytest.fixture
def receipts(tmp_path: Path) -> Path:
    return tmp_path / "receipts"


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "register-501",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up register of a made-up authority",
        "format": "xml",
        "page": "https://made-up.example/homes",
        "url": ADDRESS,
        "max_bytes": 1_000_000,
        "edition_from": IN_THE_HEADER,
        **changed,
    }
    return Listed.model_validate(fields)


def arrived(
    tmp_path: Path, content: bytes, when: str = RETRIEVED_AT, address: str = ADDRESS
) -> Arrival:
    path = tmp_path / "arrived"
    path.write_bytes(content)
    return Arrival(path, address.rsplit("/", 1)[-1], address, when, How.FETCHED)


def ended(outcome: Outcome) -> tuple[Status, Why | None, bool]:
    return outcome.status, outcome.why, outcome.new


OF_THE_DAY = register(header_of(DAY))
OF_THE_DAY_AGAIN = register(header_of(DAY), rows=3)
OF_THE_NEXT_DAY = register(header_of("2026-09-17"), rows=3)


# The receipt is written from what the file says.


def test_the_receipt_of_a_file_that_states_its_own_edition_is_written_from_the_file(
    store: Store, receipts: Path, tmp_path: Path
):
    outcome = keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, receipts)
    assert ended(outcome) == (Status.OK, None, True)
    (receipt,) = read_receipts(receipts)
    assert (receipt.edition, receipt.data_period) == (f"extract of {DAY}", Period(as_at=DAY))
    # The receipt says that the edition was read in the file, and where in it.
    assert receipt.edition_from == EditionFrom(
        where=Where.XML_HEADER, at="Header/ExtractDate", period_too=True
    )
    assert receipt.retrieved_at == RETRIEVED_AT
    assert store.receipts() == {receipt.kept_key(): receipt.canonical()}


def test_a_receipt_of_an_edition_that_a_page_stated_does_not_say_it_was_read_in_the_file(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    stated = listed(edition_from=None, edition="2025", data_period={"as_at": "2025-03-31"})
    assert keep(1, stated, arrived(tmp_path, OF_THE_DAY), folder, receipts).status is Status.OK
    (receipt,) = read_receipts(receipts)
    assert receipt.edition_from is None
    assert (
        b"edition_from" not in (receipts / "made-up-homes" / f"{receipt.file_id}.json").read_bytes()
    )


def test_the_edition_is_read_before_anything_is_kept(
    folder: FolderStore, receipts: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    kept_when_read: list[int] = []
    read = run.found_in

    def watched(*given: object) -> object:
        kept_when_read.append(len(folder.list()))
        return read(*given)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(run, "found_in", watched)
    assert keep(1, listed(), arrived(tmp_path, OF_THE_DAY), folder, receipts).status is Status.OK
    assert kept_when_read == [0]
    assert len(folder.list()) == 1


@pytest.mark.parametrize(
    "header",
    [header_of(), header_of("16/09/2026"), header_of(CANARY_ROW), header_of(DAY, "2026-09-15")],
    ids=["no day", "a day that is not one", "words", "two days"],
)
def test_a_file_that_states_no_edition_is_kept_with_no_receipt_and_a_reason_of_its_own(
    store: Store, receipts: Path, tmp_path: Path, header: str
):
    outcome = keep(1, listed(), arrived(tmp_path, register(header)), store, receipts)
    assert ended(outcome) == (Status.MISSING, Why.NOT_DATED, True)
    assert outcome.held is not None and store.list() == [outcome.held]
    assert not receipts.exists() and store.receipts() == {}
    assert not outcome.done
    # What the file held in the place of a day is said nowhere.
    assert CANARY_ROW not in outcome.line() + outcome.words()
    assert int(Why.NOT_DATED) == 34 and " why=34 " in outcome.line()


# What a second fetch does.


def test_the_same_bytes_and_the_same_day_are_nothing_new_and_the_receipt_stands(
    store: Store, receipts: Path, tmp_path: Path
):
    keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, receipts)
    (first,) = read_receipts(receipts)
    again = keep(1, listed(), arrived(tmp_path, OF_THE_DAY, LATER), store, receipts)
    assert ended(again) == (Status.OK, None, False)
    assert read_receipts(receipts) == (first,)
    assert first.retrieved_at == RETRIEVED_AT
    assert len(store.list()) == 1 and store.receipts() == {first.kept_key(): first.canonical()}


def test_new_bytes_and_a_new_day_are_a_new_file_with_a_receipt_beside_the_old(
    store: Store, receipts: Path, tmp_path: Path
):
    keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, receipts)
    (first,) = read_receipts(receipts)
    second = keep(1, listed(), arrived(tmp_path, OF_THE_NEXT_DAY, LATER), store, receipts)
    assert ended(second) == (Status.OK, None, True)
    # The old file and its receipt stand as they were: a build's lock names which it used.
    both = {receipt.edition: receipt for receipt in read_receipts(receipts)}
    assert set(both) == {f"extract of {DAY}", "extract of 2026-09-17"}
    assert both[f"extract of {DAY}"] == first
    assert both["extract of 2026-09-17"].retrieved_at == LATER
    assert len(store.list()) == 2 and len(store.receipts()) == 2


def test_new_bytes_that_state_the_same_day_are_refused_and_nothing_is_kept(
    store: Store, receipts: Path, tmp_path: Path
):
    keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, receipts)
    (first,) = read_receipts(receipts)
    held = store.list()
    again = keep(1, listed(), arrived(tmp_path, OF_THE_DAY_AGAIN, LATER), store, receipts)
    assert ended(again) == (Status.REFUSED, Why.SAME_EDITION_OTHER_BYTES, False)
    assert again.held is None and not again.done
    assert store.list() == held
    assert read_receipts(receipts) == (first,)
    assert store.receipts() == {first.kept_key(): first.canonical()}
    assert int(Why.SAME_EDITION_OTHER_BYTES) == 35 and " why=35 " in again.line()


def test_a_receipt_that_stands_in_the_store_alone_is_held_to_as_well(
    store: Store, receipts: Path, tmp_path: Path
):
    """A hosted run starts with the receipts that were committed, and no others."""
    keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, receipts)
    elsewhere = tmp_path / "another-folder-of-receipts"
    again = keep(1, listed(), arrived(tmp_path, OF_THE_DAY_AGAIN, LATER), store, elsewhere)
    assert ended(again) == (Status.REFUSED, Why.SAME_EDITION_OTHER_BYTES, False)
    assert not elsewhere.exists() and len(store.list()) == 1


def test_a_receipt_that_stands_in_the_folder_alone_is_held_to_as_well(
    receipts: Path, tmp_path: Path
):
    """A receipt that was committed stands, whatever store a run is given."""
    keep(1, listed(), arrived(tmp_path, OF_THE_DAY), FolderStore(tmp_path / "first"), receipts)
    other = FolderStore(tmp_path / "second")
    again = keep(1, listed(), arrived(tmp_path, OF_THE_DAY_AGAIN, LATER), other, receipts)
    assert ended(again) == (Status.REFUSED, Why.SAME_EDITION_OTHER_BYTES, False)
    assert other.list() == [] and other.receipts() == {}


def test_two_files_of_one_source_may_state_the_same_day(
    store: Store, receipts: Path, tmp_path: Path
):
    """A register is a file for each authority, and many are made on one day."""
    other = "https://files.made-up.example/files/register-502.xml"
    first = keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, receipts)
    second = keep(
        2,
        listed(item="register-502", url=other),
        arrived(tmp_path, OF_THE_DAY_AGAIN, address=other),
        store,
        receipts,
    )
    assert ended(first) == ended(second) == (Status.OK, None, True)
    assert [receipt.edition for receipt in read_receipts(receipts)] == [f"extract of {DAY}"] * 2


def test_a_receipt_of_an_edition_that_a_page_stated_is_not_written_over(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    """The list once stated the edition of these bytes. What it says now is another record."""
    stated = listed(edition_from=None, edition=f"extract of {DAY}", data_period={"as_at": DAY})
    keep(1, stated, arrived(tmp_path, OF_THE_DAY), folder, receipts)
    (first,) = read_receipts(receipts)
    again = keep(1, listed(), arrived(tmp_path, OF_THE_DAY, LATER), folder, receipts)
    assert (again.status, again.why) == (Status.DIFFERS, Why.RECEIPT_DIFFERS)
    assert read_receipts(receipts) == (first,)


def test_what_is_kept_as_a_receipt_and_is_none_is_not_taken_for_one(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    (receipts / "made-up-homes").mkdir(parents=True)
    (receipts / "made-up-homes" / "f-000000000000.json").write_text(CANARY_ROW, encoding="utf-8")
    outcome = keep(1, listed(), arrived(tmp_path, OF_THE_DAY), folder, receipts)
    assert ended(outcome) == (Status.OK, None, True)


def test_a_file_that_a_person_hands_over_is_dated_by_what_it_states_too(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    """A publisher may refuse a program. The file a person saves states the same day."""
    saved = arrived(tmp_path, OF_THE_DAY)
    by_hand = Arrival(saved.path, saved.name, saved.address, saved.retrieved_at, How.BY_HAND)
    outcome = keep(1, listed(), by_hand, folder, receipts)
    assert ended(outcome) == (Status.OK, None, True) and outcome.by_hand
    (receipt,) = read_receipts(receipts)
    assert (receipt.how, receipt.edition) == (How.BY_HAND, f"extract of {DAY}")
    assert receipt.edition_from is not None and receipt.edition_from.where is Where.XML_HEADER


# A file that holds no date.


def report(rows: int = 2) -> bytes:
    return (f"RXX,{CANARY_ROW},Y60\n" * rows).encode()


def undated(**changed: object) -> Listed:
    return listed(item="report-ets", format="csv", edition_from=THE_DAY_RETRIEVED, **changed)


def test_a_file_that_holds_no_date_is_dated_by_the_day_it_was_retrieved(
    store: Store, receipts: Path, tmp_path: Path
):
    outcome = keep(1, undated(), arrived(tmp_path, report()), store, receipts)
    assert ended(outcome) == (Status.OK, None, True)
    (receipt,) = read_receipts(receipts)
    assert receipt.edition == "retrieved 2026-09-24"
    assert receipt.data_period == Period(as_at="2026-09-24")
    assert receipt.edition_from == EditionFrom(where=Where.RETRIEVED, at="", period_too=True)


def test_the_same_file_retrieved_on_a_later_day_keeps_the_day_it_was_first_retrieved(
    store: Store, receipts: Path, tmp_path: Path
):
    keep(1, undated(), arrived(tmp_path, report()), store, receipts)
    (first,) = read_receipts(receipts)
    again = keep(1, undated(), arrived(tmp_path, report(), LATER), store, tmp_path / "again")
    assert ended(again) == (Status.OK, None, False)
    assert read_receipts(tmp_path / "again") == (first,)
    assert store.receipts() == {first.kept_key(): first.canonical()}


def test_another_file_retrieved_on_a_later_day_has_a_receipt_of_that_day(
    store: Store, receipts: Path, tmp_path: Path
):
    keep(1, undated(), arrived(tmp_path, report()), store, receipts)
    later = keep(1, undated(), arrived(tmp_path, report(3), LATER), store, receipts)
    assert ended(later) == (Status.OK, None, True)
    assert sorted(receipt.edition for receipt in read_receipts(receipts)) == [
        "retrieved 2026-09-24",
        "retrieved 2026-10-01",
    ]


def test_another_file_retrieved_on_the_same_day_is_refused(
    store: Store, receipts: Path, tmp_path: Path
):
    keep(1, undated(), arrived(tmp_path, report()), store, receipts)
    same_day = "2026-09-24T21:00:00Z"
    again = keep(1, undated(), arrived(tmp_path, report(3), same_day), store, receipts)
    assert ended(again) == (Status.REFUSED, Why.SAME_EDITION_OTHER_BYTES, False)
    assert len(store.list()) == len(read_receipts(receipts)) == 1


# A day that is about the file, and a time that is about the data.


def test_a_geopackage_has_its_edition_from_the_file_and_its_period_from_the_list(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    content = geopackage(tmp_path / "made-up.gpkg", ["2025-12-22T16:37:50.337Z"]).read_bytes()
    unsure = listed(format="gpkg", edition_from=LAST_CHANGE)
    outcome = keep(1, unsure, arrived(tmp_path, content), folder, receipts)
    assert ended(outcome) == (Status.MISSING, Why.NOT_SURE, True)
    assert not receipts.exists()
    sure = listed(format="gpkg", edition_from=LAST_CHANGE, data_period={"as_at": "2021-03"})
    outcome = keep(1, sure, arrived(tmp_path, content), folder, receipts)
    assert ended(outcome) == (Status.OK, None, False)
    (receipt,) = read_receipts(receipts)
    assert (receipt.edition, receipt.data_period) == (
        "last changed 2025-12-22",
        Period(as_at="2021-03"),
    )
    assert receipt.edition_from is not None and not receipt.edition_from.period_too


def test_a_street_extract_has_its_edition_and_its_period_from_its_header_block(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    content = street_extract(block(b"OSMHeader", header_block(TIME)))
    file = listed(format="other", edition_from=RUNS_TO)
    assert keep(1, file, arrived(tmp_path, content), folder, receipts).status is Status.OK
    (receipt,) = read_receipts(receipts)
    assert (receipt.edition, receipt.data_period) == (TIME, Period(as_at="2026-09-22"))


# What a run says, and how often it asks the store.


def test_every_line_of_a_file_that_states_its_own_edition_is_one_a_public_log_lets_through(
    folder: FolderStore, receipts: Path, tmp_path: Path
):
    outcomes = [
        keep(1, listed(), arrived(tmp_path, OF_THE_DAY), folder, receipts),
        keep(1, listed(), arrived(tmp_path, OF_THE_DAY_AGAIN), folder, receipts),
        keep(1, listed(), arrived(tmp_path, register(header_of())), folder, receipts),
    ]
    assert [outcome.why for outcome in outcomes] == [
        None,
        Why.SAME_EDITION_OTHER_BYTES,
        Why.NOT_DATED,
    ]
    for outcome in outcomes:
        assert public_log.is_public(as_the_log_knows_it(outcome.line())), outcome.line()
        assert DAY not in outcome.line() and "register" not in outcome.line()


def test_the_words_of_each_new_reason_say_what_a_person_can_do():
    assert "edition_from" in WORDS[Why.NOT_DATED] and "No receipt" in WORDS[Why.NOT_DATED]
    assert "Nothing was kept" in WORDS[Why.SAME_EDITION_OTHER_BYTES]


def test_the_receipts_of_a_source_are_asked_of_the_store_once_in_a_run(
    receipts: Path, tmp_path: Path
):
    """A register is 33 files of one source. The store is asked for its receipts once."""
    asked: list[str] = []

    class Counted(FolderStore):
        def receipts(self, source_id: str = "") -> dict[str, bytes]:
            asked.append(source_id)
            return super().receipts(source_id)

    store = Counted(tmp_path / "store")
    standing = Standing(store, receipts)
    for number in (501, 502, 503):
        address = f"https://files.made-up.example/files/register-{number}.xml"
        file = listed(item=f"register-{number}", url=address)
        content = register(header_of(DAY), rows=number - 500)
        outcome = keep(
            1, file, arrived(tmp_path, content, address=address), store, receipts, standing
        )
        assert outcome.status is Status.OK
    assert asked == ["made-up-homes"]
    # What the run itself wrote is held to as well.
    again = register(header_of(DAY), rows=9)
    outcome = keep(1, listed(), arrived(tmp_path, again), store, receipts, standing)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.SAME_EDITION_OTHER_BYTES)


def test_a_store_holds_the_receipts_of_one_source_apart(store: Store, tmp_path: Path):
    first = keep(1, listed(), arrived(tmp_path, OF_THE_DAY), store, tmp_path / "receipts")
    other = listed(source_id="made-up-rail", use="validation_only")
    keep(1, other, arrived(tmp_path, OF_THE_NEXT_DAY), store, tmp_path / "receipts")
    assert first.held is not None
    assert len(store.receipts()) == 2
    (key,) = store.receipts("made-up-homes")
    assert key == f"receipts/made-up-homes/{first.held.file_id}.json"
    assert store.receipts("made-up-unknown") == {}
    assert Receipt.model_validate_json(store.receipts("made-up-homes")[key]).edition == (
        f"extract of {DAY}"
    )


# Driven as a person or a workflow drives it.

WHERE = (
    '{ where = "xml_header", at = "Header/ExtractDate", words = "extract of", period_too = true }'
)
A_LIST = f"""
schema_version = 1
build = "made-up"

[[file]]
item = "register-501"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up register of a made-up authority"
format = "xml"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/files/register-501.xml"
max_bytes = 1000000
edition_from = {WHERE}
"""


def test_plan_reads_such_a_file_ready_and_says_to_a_person_where_its_edition_is_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    folders.list.write_text(A_LIST, encoding="utf-8")
    assert main(["plan", *folders.common()], {}, never) == 0
    quiet, _ = printed(capsys)
    assert quiet == [
        "step=plan n=1 source=made-up-homes status=ok seconds=0.0",
        "step=plan status=ok files=1 ready=1",
    ]
    assert main(["plan", *folders.common(), "--words"], {}, never) == 0
    spoken, _ = printed(capsys)
    assert any("Fetch reads its edition in the file" in line for line in spoken)
    assert any("xml_header, at Header/ExtractDate" in line for line in spoken)


def kept_line(content: bytes, new: int) -> str:
    """The line of a file that was kept with its receipt, less how long it took."""
    sha256 = hashlib.sha256(content).hexdigest()
    return (
        f"step=fetch n=1 source=made-up-homes status=ok file_id=f-{sha256[:12]} "
        f"sha256={sha256} bytes={len(content)} new={new}"
    )


def test_a_run_writes_the_receipt_of_each_file_that_arrives_and_refuses_what_should_not_be(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    folders.list.write_text(A_LIST, encoding="utf-8")
    pages: dict[str, Answer] = {}
    arguments = ["fetch", *folders.common(), "--receipts", str(folders.receipts)]
    said: list[tuple[int, str]] = []
    with serving(lambda request: pages.get(request.path, Answer(404))) as publisher:
        # The file as it is, twice. Then the next day's, and then another of that same day.
        for content in (OF_THE_DAY, OF_THE_DAY, OF_THE_NEXT_DAY, register(header_of("2026-09-17"))):
            pages["/files/register-501.xml"] = Answer(body=content)
            code = main(arguments, folders.environment, through(publisher))
            lines, errors = printed(capsys)
            assert errors == "" and len(lines) == 2
            said.append((code, lines[0].rsplit(" seconds=", 1)[0]))
    assert said == [
        (0, kept_line(OF_THE_DAY, new=1)),
        (0, kept_line(OF_THE_DAY, new=0)),
        (0, kept_line(OF_THE_NEXT_DAY, new=1)),
        (1, "step=fetch n=1 source=made-up-homes status=refused why=35"),
    ]
    editions = sorted(receipt.edition for receipt in read_receipts(folders.receipts))
    assert editions == ["extract of 2026-09-16", "extract of 2026-09-17"]
    assert len(FolderStore(folders.store).list()) == 2
