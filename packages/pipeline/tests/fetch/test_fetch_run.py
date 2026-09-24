"""A run of fetch: the gate, then the download, then the store, then the receipt.

The publisher is a stand-in on the loopback address, the registry is made up,
and so is every file. A connection to any other address is blocked. The
stand-in speaks plain http on a host no registry entry names, so the list
gives the address a publisher would have, and each test hands fetch a
downloader that finds the stand-in behind it.
"""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

import public_log
import pytest
from burro_pipeline.evidence import How, Period, Receipt, read_receipts, seal
from burro_pipeline.fetch.download import Downloaded, Limits, download, user_agent
from burro_pipeline.fetch.run import WORDS, Outcome, Status, Why, fetch, summary
from burro_pipeline.fetch.sources import Format, Listed
from burro_pipeline.fetch.store import FolderStore, Held, StoreError
from burro_pipeline.registry import Registry, RegistryError, Source, Use, load

from .support import (
    CANARY_ROW,
    ONLY_LOOPBACK,
    Answer,
    Seen,
    Served,
    made_up_registry_at,
    serving,
)

pytestmark = ONLY_LOOPBACK

BODY = f"code,homes\nE1,10\nE2,20\nE3,{CANARY_ROW}\n".encode()
SHA256 = hashlib.sha256(BODY).hexdigest()
NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
AGENT = user_agent("data@made-up.example")
PUBLISHER = "https://files.made-up.example"
# Where a made-up publisher sends a request on to: a host that only a list names.
ELSEWHERE = "https://cdn.made-up.example"
REGISTRY = Path(__file__).parents[4] / "registry" / "sources"


class Publisher:
    def __init__(self) -> None:
        self.pages: dict[str, Answer] = {
            "/files/homes.csv": Answer(body=BODY),
            "/rail/timetable.csv": Answer(body=BODY),
        }

    def __call__(self, request: Seen) -> Answer:
        return self.pages.get(request.path, Answer(404, body=b"not here"))


@pytest.fixture
def publisher() -> Publisher:
    return Publisher()


@pytest.fixture
def served(publisher: Publisher) -> Iterator[Served]:
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
    *,
    agent: str,
    may_redirect_to: tuple[str, ...] = (),
) -> Downloaded:
    """The real download, which finds the stand-in behind the address a publisher would have.

    The list gives the publisher's host and the stand-in's port. What comes
    back is given the publisher's address again, as a receipt would hold it.
    What comes back from another stand-in is given the address of another host:
    it stands for a host that the publisher sends a request on to.
    """
    asked = urlsplit(address)
    assert address.startswith(f"{PUBLISHER}:{asked.port}/")
    got = download(
        address.replace(f"{PUBLISHER}:{asked.port}", f"http://127.0.0.1:{asked.port}", 1),
        to,
        limits,
        agent=agent,
        may_redirect_to=may_redirect_to,
        loopback_for_tests=True,
    )
    parts = urlsplit(got.final_url)
    query = f"?{parts.query}" if parts.query else ""
    host = f"{PUBLISHER}:{asked.port}" if parts.port == asked.port else ELSEWHERE
    return replace(got, final_url=f"{host}{parts.path}{query}")


def listed(served: Served, path: str = "/files/homes.csv", **changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "made-up-homes",
        "source_id": "made-up-homes",
        "use": Use.SCORING,
        "what": "Made-up homes by made-up area",
        "format": Format.CSV,
        "page": "https://made-up.example/homes",
        "url": f"{PUBLISHER}:{served.port}{path}" if path else "",
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": Period(as_at="2025-03-31"),
        **changed,
    }
    return Listed.model_validate(fields)


def run(
    files: list[Listed], registry: Registry, store: FolderStore, receipts: Path
) -> list[Outcome]:
    return fetch(
        files, registry, store, receipts, agent=AGENT, now=lambda: NOW, downloader=over_loopback
    )


def nothing_was_kept(store: FolderStore, receipts: Path) -> bool:
    return store.list() == [] and not receipts.exists()


def test_a_file_is_fetched_stored_and_given_its_receipt(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served)], registry, store, receipts)
    held = Held("made-up-homes", SHA256, "homes.csv", len(BODY))
    assert (outcome.status, outcome.why, outcome.held, outcome.new) == (Status.OK, None, held, True)
    assert store.list() == [held]
    (receipt,) = read_receipts(receipts)
    assert receipt == Receipt(
        file_id=f"f-{SHA256[:12]}",
        source_id="made-up-homes",
        use=Use.SCORING,
        publisher_file="homes.csv",
        url=f"https://files.made-up.example:{served.port}/files/homes.csv",
        listed_url=f"https://files.made-up.example:{served.port}/files/homes.csv",
        sha256=SHA256,
        bytes=len(BODY),
        retrieved_at="2026-09-24T09:12:31Z",
        how=How.FETCHED,
        edition="2025",
        data_period=Period(as_at="2025-03-31"),
    )


def test_the_receipt_is_kept_where_the_evidence_looks_for_it(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    run([listed(served)], registry, store, receipts)
    (receipt,) = read_receipts(receipts)
    written = receipts / "made-up-homes" / f"{receipt.file_id}.json"
    assert written.read_bytes() == receipt.canonical()
    assert (
        written.relative_to(receipts).as_posix()
        == receipt.path().relative_to("data/receipts").as_posix()
    )
    assert [held.key for held in store.list()] == [receipt.vault_key()]
    assert [path.name for path in written.parent.iterdir()] == [written.name]


def test_what_was_fetched_can_be_sealed_into_a_lock(
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
    assert [locked.sha256 for locked in lock.inputs] == [SHA256]


class Watched:
    """A registry that writes down how much the publisher had been asked at each question."""

    def __init__(self, registry: Registry, served: Served) -> None:
        self.registry, self.served = registry, served
        self.asked: list[tuple[str, Use, int]] = []

    def require(self, source_id: str, use: Use) -> Source:
        self.asked.append((source_id, use, len(self.served.seen)))
        return self.registry.require(source_id, use)


def test_the_gate_is_asked_before_anything_is_asked_of_the_publisher(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    watched = Watched(registry, served)
    files = [listed(served), listed(served, item="made-up-again", use=Use.DISPLAY)]
    fetch(
        files,
        watched,  # pyright: ignore[reportArgumentType]
        store,
        receipts,
        agent=AGENT,
        now=lambda: NOW,
        downloader=over_loopback,
    )
    assert watched.asked == [
        # Every file of the list, before any request.
        ("made-up-homes", Use.SCORING, 0),
        ("made-up-homes", Use.DISPLAY, 0),
        # Then each again, as the first thing done for it.
        ("made-up-homes", Use.SCORING, 0),
        ("made-up-homes", Use.DISPLAY, 1),
    ]
    assert len(served.seen) == 2


@pytest.mark.parametrize(
    ("source_id", "use", "said"),
    [
        ("made-up-rail", Use.ROUTING, "is gated, not approved"),
        ("made-up-ratings", Use.SCORING, "is banned"),
        ("made-up-homes", Use.GAZETTEER, "not registered for gazetteer"),
        ("made-up-unknown", Use.SCORING, "not in the licence registry"),
    ],
)
def test_a_fetch_is_refused_when_the_gate_refuses(
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    source_id: str,
    use: Use,
    said: str,
):
    (outcome,) = run([listed(served, source_id=source_id, use=use)], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.GATE)
    assert said in outcome.detail
    assert served.seen == []
    assert nothing_was_kept(store, receipts)


def test_one_refusal_stops_every_download(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    files = [listed(served), listed(served, item="rail", source_id="made-up-rail", use=Use.ROUTING)]
    first, second = run(files, registry, store, receipts)
    assert (first.status, first.why) == (Status.SKIPPED, Why.ANOTHER_WAS_REFUSED)
    assert (second.status, second.why) == (Status.REFUSED, Why.GATE)
    assert served.seen == []
    assert nothing_was_kept(store, receipts)


def test_a_source_that_loses_its_approval_during_a_run_is_not_fetched(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    class Withdrawn(Watched):
        def require(self, source_id: str, use: Use) -> Source:
            if len(self.asked) >= 1:
                raise RegistryError("'made-up-homes' is gated, not approved: made up")
            return super().require(source_id, use)

    (outcome,) = fetch(
        [listed(served)],
        Withdrawn(registry, served),  # pyright: ignore[reportArgumentType]
        store,
        receipts,
        agent=AGENT,
        now=lambda: NOW,
        downloader=over_loopback,
    )
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.GATE)
    assert served.seen == []


def test_a_gated_source_may_be_fetched_for_an_internal_use_it_lists(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    rail = "https://made-up.example/rail"
    file = listed(
        served, "/rail/timetable.csv", source_id="made-up-rail", use=Use.VALIDATION_ONLY, page=rail
    )
    (outcome,) = run([file], registry, store, receipts)
    assert outcome.status is Status.OK
    assert read_receipts(receipts)[0].use is Use.VALIDATION_ONLY


def test_a_file_over_its_stated_size_is_refused_and_nothing_is_kept(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served, max_bytes=len(BODY) - 1)], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.TOO_LARGE)
    assert nothing_was_kept(store, receipts)


def test_a_redirect_to_another_host_fails_the_file_and_names_the_host_to_a_person_alone(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    publisher.pages["/files/latest"] = Answer(
        302, {"Location": "https://cdn.made-up.example/x?sig=1"}
    )
    (outcome,) = run([listed(served, "/files/latest")], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.REDIRECT_ELSEWHERE)
    assert "cdn.made-up.example" in outcome.words()
    assert "made-up.example" not in outcome.line()
    assert nothing_was_kept(store, receipts)


def test_a_host_the_list_names_may_be_redirected_to(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    with serving(lambda _: Answer(body=BODY)) as other:
        publisher.pages["/files/latest"] = Answer(302, {"Location": f"{other.address}/homes.csv"})
        file = listed(served, "/files/latest", may_redirect_to=("127.0.0.1",))
        (outcome,) = run([file], registry, store, receipts)
    assert outcome.status is Status.OK
    assert read_receipts(receipts)[0].url == "https://cdn.made-up.example/homes.csv"


KEPT_ELSEWHERE = """
[[source]]
id = "made-up-elsewhere"
name = "Made-up tables for the audit, kept on another host"
publisher = "Made-up Office"
url = "https://made-up.example/elsewhere"
dimension = "audit"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
status = "held"
status_reason = "Made up. It is read for the audit and for nothing else."
uses = ["audit_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23
evidence_urls = ["https://made-up.example/elsewhere-licence"]
file_urls = ["https://cdn.made-up.example/audit/"]
"""


@pytest.mark.parametrize(
    "sent_on_to",
    [
        "/audit/c.csv",
        "/audit//c.csv",
        "/made-up/../audit/c.csv",
        "/made-up/%2e%2e/audit/c.csv",
        "/%2561udit/c.csv",
    ],
)
def test_a_request_sent_on_to_the_file_of_another_entry_is_not_kept_however_it_is_written(
    publisher: Publisher,
    served: Served,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
    sent_on_to: str,
):
    """Through the real download: the publisher sends the request to a host the list names."""
    path = tmp_path / "registry-elsewhere.toml"
    path.write_text(made_up_registry_at(served.port) + KEPT_ELSEWHERE, encoding="utf-8")
    with serving(lambda _: Answer(body=BODY)) as other:
        publisher.pages["/files/latest"] = Answer(302, {"Location": f"{other.address}{sent_on_to}"})
        file = listed(served, "/files/latest", may_redirect_to=("127.0.0.1",))
        (outcome,) = run([file], load(path), store, receipts)
        # The request was sent on, and the other host answered it.
        assert [seen.path for seen in other.seen] == [sent_on_to]
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_ADDRESS)
    assert nothing_was_kept(store, receipts)


def test_a_status_that_is_not_200_is_given_as_a_number(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served, "/files/gone")], registry, store, receipts)
    assert (outcome.status, outcome.why, outcome.http) == (Status.FAILED, Why.STATUS, "404")
    assert " why=27 http=404 " in outcome.line()


@pytest.mark.parametrize(
    ("page", "format"),
    [
        (b"<!DOCTYPE html><html><body>Sign in to download</body></html>", Format.CSV),
        (b"<html><body>The file has moved</body></html>", Format.ZIP),
        (b"<html><body>The file has moved</body></html>", Format.OTHER),
        (b"code,homes\nE1,10\n", Format.ZIP),
        (b"code,homes\nE1,10\n", Format.XLSX),
        (b"code,homes\nE1,10\n", Format.GPKG),
        (b"", Format.CSV),
        (b"", Format.OTHER),
    ],
)
def test_what_is_not_the_file_listed_is_never_stored(
    publisher: Publisher,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    page: bytes,
    format: Format,
):
    publisher.pages["/files/homes.csv"] = Answer(body=page)
    (outcome,) = run([listed(served, format=format)], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.UNREADABLE, Why.NOT_THE_FORMAT)
    assert nothing_was_kept(store, receipts)


def test_a_file_with_no_address_is_missing_and_nothing_is_asked(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served, "")], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NO_ADDRESS)
    assert served.seen == []


@pytest.mark.parametrize(
    "changed",
    [
        {"edition": ""},
        {"data_period": None},
        {"unsure": ("edition",)},
        {"unsure": ("data_period",)},
    ],
)
def test_a_file_whose_edition_or_period_is_not_sure_is_stored_without_a_receipt(
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    changed: dict[str, object],
):
    (outcome,) = run([listed(served, "/files/homes.csv", **changed)], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SURE)
    assert outcome.held is not None and store.list() == [outcome.held]
    assert not receipts.exists()
    assert not outcome.done


def test_an_address_that_is_not_yet_sure_is_still_fetched(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served, unsure=("url", "max_bytes"))], registry, store, receipts)
    assert outcome.status is Status.OK


def test_a_file_fetched_twice_is_stored_once_and_keeps_its_first_receipt(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    run([listed(served)], registry, store, receipts)
    (before,) = read_receipts(receipts)
    (outcome,) = fetch(
        [listed(served)],
        registry,
        store,
        receipts,
        agent=AGENT,
        now=lambda: datetime(2026, 12, 18, tzinfo=UTC),
        downloader=over_loopback,
    )
    assert (outcome.status, outcome.new) == (Status.OK, False)
    assert read_receipts(receipts) == (before,)
    assert len(store.list()) == 1


def test_a_reissued_file_is_a_second_file_with_a_receipt_of_its_own(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    run([listed(served)], registry, store, receipts)
    publisher.pages["/files/homes.csv"] = Answer(body=BODY + b"E4,40\n")
    (outcome,) = run([listed(served)], registry, store, receipts)
    assert (outcome.status, outcome.new) == (Status.OK, True)
    assert len(store.list()) == len(read_receipts(receipts)) == 2


def test_a_receipt_that_says_something_else_is_never_written_over(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    run([listed(served)], registry, store, receipts)
    (before,) = read_receipts(receipts)
    (outcome,) = run([listed(served, edition="2026")], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.DIFFERS, Why.RECEIPT_DIFFERS)
    assert read_receipts(receipts) == (before,)


def test_a_key_in_an_address_is_never_in_the_receipt(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    signed = "/files/homes.csv?year=2025&token=zzyzx-canary&api_key=zzyzx-canary&sig=zzyzx"
    publisher.pages["/files/latest?year=2025"] = Answer(302, {"Location": signed})
    publisher.pages[signed] = Answer(body=BODY)
    file = listed(served, "/files/latest?year=2025", url_parameters=("year",))
    (outcome,) = run([file], registry, store, receipts)
    assert outcome.status is Status.OK
    (receipt,) = read_receipts(receipts)
    assert receipt.url == f"{PUBLISHER}:{served.port}/files/homes.csv?year=2025"
    assert "zzyzx" not in (receipts / receipt.path().relative_to("data/receipts")).read_text()


def test_a_store_that_fails_is_a_failure_and_no_receipt_is_written(
    served: Served, registry: Registry, receipts: Path, tmp_path: Path
):
    class Broken(FolderStore):
        def put(self, source_id: str, name: str, content: Path) -> tuple[Held, bool]:
            raise StoreError("the store answered 500 InternalError to a file sent to it")

    (outcome,) = run([listed(served)], registry, Broken(tmp_path / "store"), receipts)
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.STORE)
    assert not receipts.exists()


def test_a_file_that_is_saved_by_hand_is_not_asked_of_the_publisher(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    (outcome,) = run([listed(served, by_hand=True)], registry, store, receipts)
    assert (outcome.status, outcome.why) == (Status.MISSING, Why.NOT_SAVED_BY_HAND)
    assert served.seen == []


def test_nothing_is_left_in_the_temporary_folder(
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr("tempfile.tempdir", str(scratch))
    run([listed(served), listed(served, "/files/gone", item="gone")], registry, store, receipts)
    assert list(scratch.iterdir()) == []


def lines_of(outcomes: list[Outcome]) -> list[str]:
    return [*(outcome.line() for outcome in outcomes), summary(outcomes)]


@cache
def ids_of_the_repository() -> frozenset[str]:
    """Every id in the repository's own registry, read once."""
    return frozenset(source.id for source in load(REGISTRY))


def as_the_log_knows_it(line: str) -> str:
    """A line under an id of the repository's own registry, which is what the log knows."""
    assert "defra-pcm-background-air" in ids_of_the_repository()
    return line.replace("source=made-up-homes", "source=defra-pcm-background-air")


def test_every_line_a_run_prints_is_one_the_public_log_lets_through(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    files = [
        listed(served),
        listed(served, "/files/gone", item="gone"),
        listed(served, "", item="nowhere"),
        listed(served, item="unsure", unsure=("edition",)),
        listed(served, item="large", max_bytes=1),
        listed(served, item="by-hand", by_hand=True),
    ]
    outcomes = run(files, registry, store, receipts)
    assert {outcome.status for outcome in outcomes} == {Status.OK, Status.FAILED, Status.MISSING}
    for line in lines_of(outcomes):
        assert public_log.is_public(as_the_log_knows_it(line)), line
    for changed in (
        {"use": Use.ROUTING},
        {"page": "https://made-up.example/rail"},
        {"url": "https://elsewhere.example/files/homes.csv"},
        {"what": "Census 2021 table TS021"},
    ):
        refused = run([listed(served), listed(served, **changed)], registry, store, receipts)
        assert [outcome.status for outcome in refused] == [Status.SKIPPED, Status.REFUSED]
        for line in lines_of(refused):
            assert public_log.is_public(as_the_log_knows_it(line)), line


def test_no_line_a_run_prints_holds_a_row_an_address_or_a_name_of_a_file(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    publisher.pages["/files/latest"] = Answer(302, {"Location": "https://cdn.made-up.example/x"})
    files = [
        listed(served),
        listed(served, "/files/gone", item="gone"),
        listed(served, "/files/latest"),
    ]
    printed = "\n".join(lines_of(run(files, registry, store, receipts)))
    for secret in (CANARY_ROW, "made-up.example", "127.0.0.1", str(served.port), "homes.csv"):
        assert secret not in printed
    assert SHA256 in printed


def test_every_reason_has_its_words_and_its_own_number():
    assert set(WORDS) == set(Why)
    assert len({int(why) for why in Why}) == len(Why)
    assert all(not words.endswith(".") for words in WORDS.values())


def test_the_summary_counts_each_status(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    outcomes = run([listed(served), listed(served, "", item="nowhere")], registry, store, receipts)
    assert summary(outcomes) == (
        "step=fetch status=failed files=2 ok=1 skipped=0 refused=0 failed=0 missing=1 "
        "unreadable=0 differs=0"
    )
    assert summary(outcomes[:1]).startswith("step=fetch status=ok files=1 ok=1 ")


def test_a_receipt_is_written_as_the_evidence_writes_a_record(
    served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    run([listed(served)], registry, store, receipts)
    (path,) = receipts.rglob("*.json")
    document = json.loads(path.read_bytes())
    assert list(document) == sorted(document)
    assert path.read_bytes().endswith(b"}\n")
