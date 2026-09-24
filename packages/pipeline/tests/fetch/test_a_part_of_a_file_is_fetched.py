"""A run of fetch that takes part of a file: the gate, the pieces, the store, the receipt.

The publisher is a stand-in on the loopback address that gives a file a piece
at a time, as an object store does. The registry is made up, and so is the
file: places in open sea, written by a Parquet library as the publisher of
places lays out its own. A connection to any other address is blocked.
"""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportMissingTypeStubs=false

import hashlib
import io
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import public_log
import pyarrow.parquet as pq
import pytest
from burro_pipeline.evidence import How, Period, Receipt, Taken, read_receipts, seal
from burro_pipeline.fetch.download import Downloaded, Limits, user_agent
from burro_pipeline.fetch.run import WORDS, Outcome, Status, Why, fetch, summary
from burro_pipeline.fetch.sources import Format, Listed, Take
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.fetch.take import TakenFile, plan_in, take_part
from burro_pipeline.registry import Registry, Use, load

from . import pieces_support
from .parquet_support import BOX_IN, CANARY, TAKEN, a_town, made_up_places
from .support import ONLY_LOOPBACK, Answer, Served, made_up_registry_at, serving

pytestmark = ONLY_LOOPBACK

NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
AGENT = user_agent("data@made-up.example")
PUBLISHER = "https://files.made-up.example"
PATH = "/files/release/1/places.parquet"
# A box round the second and third row groups of the made-up file.
WANTED = Take(box=(2.3, 53.0, 2.7, 54.0), box_in=BOX_IN, columns=TAKEN)


@pytest.fixture
def whole(tmp_path: Path) -> bytes:
    return made_up_places(tmp_path / "whole.parquet", a_town(), packed="none").read_bytes()


@pytest.fixture
def publisher(whole: bytes) -> pieces_support.InPieces:
    return pieces_support.InPieces(whole)


@pytest.fixture
def served(publisher: pieces_support.InPieces) -> Iterator[Served]:
    with serving(publisher) as server:
        yield server


@pytest.fixture
def registry(tmp_path: Path, served: Served) -> Registry:
    path = tmp_path / "registry.toml"
    path.write_text(made_up_registry_at(served.port), encoding="utf-8")
    return load(path)


@pytest.fixture
def store(tmp_path: Path) -> FolderStore:
    return FolderStore(tmp_path / "store")


@pytest.fixture
def receipts(tmp_path: Path) -> Path:
    return tmp_path / "receipts"


def over_loopback(
    address: str,
    to: Path,
    limits: Limits,
    wanted: Take,
    *,
    agent: str,
    may_redirect_to: tuple[str, ...] = (),
) -> tuple[Downloaded, Taken]:
    """The real taking of a part, which finds the stand-in behind the publisher's address."""
    asked = urlsplit(address)
    assert address.startswith(f"{PUBLISHER}:{asked.port}/")
    got, taken = take_part(
        address.replace(f"{PUBLISHER}:{asked.port}", f"http://127.0.0.1:{asked.port}", 1),
        to,
        limits,
        wanted,
        agent=agent,
        may_redirect_to=may_redirect_to,
        loopback_for_tests=True,
    )
    path = urlsplit(got.final_url).path
    return replace(got, final_url=f"{PUBLISHER}:{asked.port}{path}"), taken


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("a file that is taken in part is never asked for whole")


def listed(served: Served, **changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "made-up-places",
        "source_id": "made-up-homes",
        "use": Use.SCORING,
        "what": "Made-up places, the part round a made-up town",
        "format": Format.PARQUET,
        "page": "https://made-up.example/homes",
        "url": f"{PUBLISHER}:{served.port}{PATH}",
        "max_bytes": 1_000_000,
        "edition": "1",
        "data_period": Period(as_at="2025-03-31"),
        "take": WANTED,
        **changed,
    }
    return Listed.model_validate(fields)


def run(
    files: list[Listed], registry: Registry, store: FolderStore, receipts: Path
) -> list[Outcome]:
    return fetch(
        files,
        registry,
        store,
        receipts,
        agent=AGENT,
        now=lambda: NOW,
        downloader=never,
        taker=over_loopback,
    )


def is_public(line: str) -> bool:
    """Whether the public log would show a line. The source is made up, so another stands in."""
    return public_log.is_public(line.replace("source=made-up-homes", "source=synthetic"))


def kept(store: FolderStore) -> bytes:
    (held,) = store.list()
    return (store.folder / held.key).read_bytes()


def nothing_was_kept(store: FolderStore, receipts: Path) -> bool:
    return store.list() == [] and not receipts.exists()


def test_a_part_is_fetched_stored_and_given_a_receipt_that_says_which_part(
    served: Served, registry: Registry, store: FolderStore, receipts: Path, whole: bytes
):
    (outcome,) = run([listed(served)], registry, store, receipts)
    assert (outcome.status, outcome.why, outcome.new) == (Status.OK, None, True)
    part = kept(store)
    (receipt,) = read_receipts(receipts)
    assert receipt.taken is not None
    runs = receipt.taken.runs
    assert part == b"".join(whole[first : first + count] for first, count in runs)
    assert receipt == Receipt(
        file_id=f"f-{hashlib.sha256(part).hexdigest()[:12]}",
        source_id="made-up-homes",
        use=Use.SCORING,
        publisher_file="places.parquet",
        url=f"{PUBLISHER}:{served.port}{PATH}",
        listed_url=f"{PUBLISHER}:{served.port}{PATH}",
        sha256=hashlib.sha256(part).hexdigest(),
        bytes=len(part),
        retrieved_at="2026-09-24T09:12:31Z",
        how=How.FETCHED,
        edition="1",
        data_period=Period(as_at="2025-03-31"),
        taken=Taken(
            of_bytes=len(whole),
            box=(2.3, 53.0, 2.7, 54.0),
            box_in="bbox",
            columns=tuple(sorted(TAKEN)),
            of_row_groups=6,
            row_groups=(1, 2),
            of_rows=24,
            rows=8,
            runs=runs,
        ),
    )
    assert len(part) < len(whole)


def test_no_byte_is_asked_of_the_publisher_but_those_of_the_part(
    served: Served, registry: Registry, store: FolderStore, receipts: Path, whole: bytes
):
    run([listed(served)], registry, store, receipts)
    (receipt,) = read_receipts(receipts)
    assert receipt.taken is not None
    asked = [request.headers["range"] for request in served.seen]
    assert asked[0] == "bytes=-8"
    named = [tuple(int(n) for n in one.removeprefix("bytes=").split("-")) for one in asked[1:]]
    arrived = sum(last - first + 1 for first, last in named) + 8
    assert arrived == receipt.bytes
    assert all(request.method == "GET" for request in served.seen)


def test_what_no_step_may_read_never_reaches_the_store(
    served: Served, registry: Registry, store: FolderStore, receipts: Path, whole: bytes
):
    """The names and the addresses of the made-up places hold the canary. No row of the
    part holds it. The footer holds the least and the most of every column, and says so."""
    run([listed(served)], registry, store, receipts)
    (receipt,) = read_receipts(receipts)
    assert receipt.taken is not None
    rows = kept(store)[: -receipt.taken.runs[-1][1]]
    assert CANARY.encode() in whole and CANARY.encode() not in rows


def test_the_part_in_the_store_is_read_as_the_whole_file_is(
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    whole: bytes,
    tmp_path: Path,
):
    run([listed(served)], registry, store, receipts)
    (receipt,) = read_receipts(receipts)
    (held,) = store.list()
    assert receipt.taken is not None
    given = pq.ParquetFile(io.BytesIO(whole))
    with TakenFile(store.folder / held.key, receipt.taken.runs, receipt.taken.of_bytes) as view:
        footer = pq.read_metadata(io.BytesIO(view.footer_alone()))
        read = pq.ParquetFile(view, metadata=footer, pre_buffer=False)
        for n in receipt.taken.row_groups:
            for column in TAKEN:
                assert read.read_row_group(n, columns=[column]).equals(
                    given.read_row_group(n, columns=[column])
                )


def test_fetched_again_the_same_part_is_the_same_file_and_its_receipt_stands(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (first,) = run([listed(served)], registry, store, receipts)
    before = read_receipts(receipts)
    (again,) = run([listed(served)], registry, store, receipts)
    assert (again.status, again.new, again.held) == (Status.OK, False, first.held)
    assert read_receipts(receipts) == before
    assert len(store.list()) == 1


def test_a_part_in_the_store_is_held_to_its_receipt_with_no_connection(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    """The footer is in the part, so the plan is worked out again from the part alone."""
    run([listed(served)], registry, store, receipts)
    (receipt,) = read_receipts(receipts)
    (held,) = store.list()
    assert receipt.taken is not None
    plan = plan_in(store.folder / held.key, receipt.taken.runs, receipt.taken.of_bytes, WANTED)
    assert (plan.row_groups, plan.runs) == (receipt.taken.row_groups, receipt.taken.runs)
    assert (plan.of_rows, plan.rows) == (receipt.taken.of_rows, receipt.taken.rows)


def test_another_box_is_another_part_with_a_receipt_of_its_own(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    run([listed(served)], registry, store, receipts)
    wider = replace_take(listed(served), box=(2.0, 53.0, 2.7, 54.0))
    (outcome,) = run([wider], registry, store, receipts)
    assert (outcome.status, outcome.new) == (Status.OK, True)
    taken = sorted(receipt.taken.row_groups for receipt in read_receipts(receipts) if receipt.taken)
    assert taken == [(0, 1, 2), (1, 2)]


def replace_take(file: Listed, **changed: object) -> Listed:
    assert file.take is not None
    return file.model_copy(update={"take": file.take.model_copy(update=changed)})


def test_what_was_taken_can_be_sealed_into_a_lock(
    served: Served, registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path
):
    run([listed(served)], registry, store, receipts)
    listing = {held.key: held.bytes for held in store.list()}
    lock = seal(
        "lon-2026-09-24-01",
        "2026-09-24T10:00:00Z",
        "0" * 40,
        read_receipts(receipts),
        listing,
        registry,
        tmp_path,
    )
    (receipt,) = read_receipts(receipts)
    assert [(one.name, one.sha256) for one in lock.inputs] == [(receipt.file_id, receipt.sha256)]


# What is refused, and that nothing is kept


def failed(
    served: Served, registry: Registry, store: FolderStore, receipts: Path, **changed: object
) -> Outcome:
    (outcome,) = run([listed(served, **changed)], registry, store, receipts)
    assert outcome.status is Status.FAILED and outcome.held is None
    assert nothing_was_kept(store, receipts)
    assert is_public(outcome.line())
    assert CANARY not in outcome.line() + outcome.words()
    assert "127.0.0.1" not in outcome.line() + outcome.words()
    return outcome


def test_a_publisher_that_gives_no_pieces_is_refused_and_the_whole_file_is_not_read(
    publisher: pieces_support.InPieces,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
):
    publisher.gives_pieces = False
    outcome = failed(served, registry, store, receipts)
    assert outcome.why is Why.NOT_IN_PIECES and " why=36 " in outcome.line()
    assert len(served.seen) == 1


def test_a_file_that_changes_while_it_is_taken_is_refused(
    publisher: pieces_support.InPieces,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
):
    other = made_up_places(tmp_path / "other.parquet", a_town(groups=7)).read_bytes()
    publisher.then[3] = (other, '"made-up-2"')
    outcome = failed(served, registry, store, receipts)
    assert outcome.why is Why.CHANGED and " why=37 " in outcome.line()


def test_a_page_in_place_of_the_file_is_refused(
    publisher: pieces_support.InPieces,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
):
    publisher.body = f"<!doctype html><html><body>Sign in. {CANARY}</body></html>".encode() * 9
    outcome = failed(served, registry, store, receipts)
    assert outcome.why is Why.NOT_LAID_OUT and " why=38 " in outcome.line()
    assert "does not end as a Parquet file ends" in outcome.words()


def test_a_file_that_lacks_a_column_the_list_names_is_refused(
    publisher: pieces_support.InPieces,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
):
    publisher.body = made_up_places(
        tmp_path / "less.parquet", a_town(), without=("taxonomy",)
    ).read_bytes()
    outcome = failed(served, registry, store, receipts)
    assert outcome.why is Why.NOT_LAID_OUT
    assert "lacks 1 of the columns" in outcome.words() and "taxonomy" not in outcome.words()


def test_a_part_over_the_size_the_list_states_is_refused(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    outcome = failed(served, registry, store, receipts, max_bytes=30_000)
    assert outcome.why is Why.TOO_LARGE
    assert served.seen[0].headers["range"] == "bytes=-8"
    assert len(served.seen) == 2


def test_a_footer_over_the_size_the_list_states_is_too_large_and_is_never_asked_for(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    outcome = failed(served, registry, store, receipts, max_bytes=1_000)
    assert outcome.why is Why.TOO_LARGE
    assert len(served.seen) == 1


def test_a_publisher_that_is_not_there_is_said_with_its_status(
    publisher: pieces_support.InPieces,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
):
    publisher.instead[0] = Answer(404, body=b"not here")
    outcome = failed(served, registry, store, receipts)
    assert (outcome.why, outcome.http) == (Why.STATUS, "404")


def test_the_gate_is_asked_before_any_piece_is(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    banned = listed(served, source_id="made-up-ratings", page="https://made-up.example/ratings")
    (outcome,) = run([banned], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.GATE)
    elsewhere = listed(served, url=f"{PUBLISHER}:{served.port}/rail/places.parquet")
    (outcome,) = run([elsewhere], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert served.seen == [] and nothing_was_kept(store, receipts)


def test_a_part_whose_edition_nobody_is_sure_of_is_stored_with_no_receipt(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served, unsure=("edition",))], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SURE)
    assert len(store.list()) == 1 and read_receipts(receipts) == ()


# What a run says


def test_every_line_of_a_run_is_one_a_public_log_shows(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    outcomes = run([listed(served)], registry, store, receipts)
    for line in (*(outcome.line() for outcome in outcomes), summary(outcomes)):
        assert is_public(line)
        assert CANARY not in line and "places" not in line and "bbox" not in line


def test_every_new_reason_has_its_words_and_says_what_a_person_can_do():
    for why in (Why.NOT_IN_PIECES, Why.CHANGED, Why.NOT_LAID_OUT):
        said = WORDS[why]
        assert "Nothing was kept" in said and "!" not in said


# A whole file of the same kind


def test_a_parquet_file_with_nothing_said_of_a_part_is_fetched_whole(
    served: Served, registry: Registry, store: FolderStore, receipts: Path, whole: bytes
):
    from burro_pipeline.fetch.download import download

    def whole_over_loopback(
        address: str, to: Path, limits: Limits, *, agent: str, may_redirect_to: tuple[str, ...] = ()
    ) -> Downloaded:
        port = urlsplit(address).port
        got = download(
            address.replace(f"{PUBLISHER}:{port}", f"http://127.0.0.1:{port}", 1),
            to,
            limits,
            agent=agent,
            loopback_for_tests=True,
        )
        return replace(got, final_url=address)

    (outcome,) = fetch(
        [listed(served, take=None)],
        registry,
        store,
        receipts,
        agent=AGENT,
        now=lambda: NOW,
        downloader=whole_over_loopback,
    )
    assert outcome.status is Status.OK
    (receipt,) = read_receipts(receipts)
    assert receipt.taken is None and kept(store) == whole
    assert "range" not in served.seen[0].headers
