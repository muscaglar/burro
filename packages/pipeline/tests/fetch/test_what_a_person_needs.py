"""What a person needs to mend a failed fetch is in the line a hosted run shows.

A hosted run shows lines of names and numbers, and withholds every word. So
two things a person needs were withheld: what arrived in place of the file,
and which host a publisher sent the request on to.

The first is printed as one word from the list of kinds. The second is printed
as the start of a hash of the host's name, and `plan --words` prints the same
hash beside each host it knows, so that a person can match the two and the
name of a host never reaches a log. Every file here is made up.
"""

import hashlib
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import public_log
import pytest
from burro_pipeline.fetch.by_hand import keep_by_hand
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded, Limits, download, user_agent
from burro_pipeline.fetch.kinds import Kind
from burro_pipeline.fetch.run import WORDS, Outcome, Status, Why, fetch, host_mark
from burro_pipeline.fetch.s3 import S3Store
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Registry, load

from .support import (
    CANARY_ROW,
    MADE_UP_REGISTRY,
    ONLY_LOOPBACK,
    Answer,
    Seen,
    Served,
    made_up_zip,
    serving,
)

pytestmark = ONLY_LOOPBACK

NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
AGENT = user_agent("data@made-up.example")
PUBLISHER = "https://files.made-up.example"
ELSEWHERE = "cdn.made-up.example"
CSV = f"code,homes\nmade-up-1,{CANARY_ROW}\n".encode()
PAGE = f"<!DOCTYPE html><html><body>Sign in. {CANARY_ROW}</body></html>".encode()


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


class Publisher:
    def __init__(self) -> None:
        self.pages: dict[str, Answer] = {}

    def __call__(self, request: Seen) -> Answer:
        return self.pages.get(request.path, Answer(404, body=b"not here"))


@pytest.fixture
def publisher() -> Publisher:
    return Publisher()


@pytest.fixture
def served(publisher: Publisher) -> Iterator[Served]:
    with serving(publisher) as server:
        yield server


def through(served: Served):
    """The real download, which finds the made-up publisher at the stand-in's address."""

    def downloader(
        address: str,
        to: Path,
        limits: Limits,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
    ) -> Downloaded:
        got = download(
            address.replace(PUBLISHER, served.address, 1),
            to,
            limits,
            agent=agent,
            may_redirect_to=may_redirect_to,
            loopback_for_tests=True,
        )
        return replace(got, final_url=f"{PUBLISHER}{urlsplit(got.final_url).path}")

    return downloader


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": f"{PUBLISHER}/files/homes",
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def as_a_run_shows_it(outcome: Outcome) -> str:
    """The line of an outcome, if the public log would show it. The source is made up."""
    line = outcome.line()
    assert public_log.is_public(line.replace("source=made-up-homes", "source=synthetic")), line
    return line


# The kind of what arrived


@pytest.mark.parametrize(
    ("arrived", "listed_as", "kind"),
    [
        (PAGE, "csv", Kind.HTML),
        (PAGE, "zip", Kind.HTML),
        (PAGE, "other", Kind.HTML),
        (CSV, "zip", Kind.CSV),
        (CSV, "xlsx", Kind.CSV),
        (b"", "csv", Kind.EMPTY),
        (b"%PDF-1.7 made up", "csv", Kind.PDF),
        (b'{"error": "made up"}', "csv", Kind.JSON),
        (b'<?xml version="1.0"?><Error><Code>made-up</Code></Error>', "zip", Kind.XML),
        (b"\x00\x01\x02 made up", "csv", Kind.UNKNOWN),
        (b"\x1f\x8b\x08 made up", "csv", Kind.GZIP),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_what_arrived_in_place_of_the_file_is_printed_as_one_word(
    publisher: Publisher,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    arrived: bytes,
    listed_as: str,
    kind: Kind,
):
    publisher.pages["/files/homes"] = Answer(body=arrived)
    file = listed(format=listed_as)
    (outcome,) = fetch(
        [file], registry, store, receipts, agent=AGENT, now=lambda: NOW, downloader=through(served)
    )
    assert (outcome.status, outcome.why) == (Status.UNREADABLE, Why.NOT_THE_FORMAT)
    assert f" status=unreadable why=5 kind={kind} seconds=" in as_a_run_shows_it(outcome)
    assert CANARY_ROW not in outcome.line() + outcome.words()


def test_a_zip_that_arrived_as_a_workbook_is_said_to_be_one(
    publisher: Publisher,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
):
    inside = {"xl/workbook.xml": b"<workbook/>", "[Content_Types].xml": b"<Types/>"}
    publisher.pages["/files/homes"] = Answer(
        body=made_up_zip(tmp_path / "made-up.xlsx", inside).read_bytes()
    )
    (outcome,) = fetch(
        [listed(format="zip")],
        registry,
        store,
        receipts,
        agent=AGENT,
        now=lambda: NOW,
        downloader=through(served),
    )
    assert " why=5 kind=workbook " in as_a_run_shows_it(outcome)


def test_a_file_that_is_kept_prints_no_kind(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    publisher.pages["/files/homes"] = Answer(body=CSV)
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent=AGENT, downloader=through(served)
    )
    assert outcome.status is Status.OK and " kind=" not in as_a_run_shows_it(outcome)


def test_a_page_saved_by_hand_in_place_of_the_file_is_said_to_be_a_page(
    registry: Registry, store: FolderStore, receipts: Path, tmp_path: Path
):
    saved = tmp_path / "homes.csv"
    saved.write_bytes(PAGE)
    file = listed(url="", by_hand=True)
    address = "https://made-up.example/notes/download"
    outcome = keep_by_hand(1, file, saved, address, "2026-09-24", registry, store, receipts, NOW)
    assert " status=unreadable by_hand=1 why=5 kind=html " in as_a_run_shows_it(outcome)


def test_the_public_log_knows_every_kind_and_no_other_word():
    of_a_file = {str(kind) for kind in Kind}
    of_a_store = {FolderStore.kind, S3Store.kind}
    assert of_a_file | of_a_store == public_log.KINDS
    assert not of_a_file & of_a_store
    for word in ("html,csv", "Html", "page", CANARY_ROW.split()[0], "homes.csv", "", "1"):
        assert not public_log.is_public(f"step=fetch kind={word}")


def test_the_words_say_where_the_kind_is_printed():
    assert WORDS[Why.NOT_THE_FORMAT].startswith("What arrived is not the format listed")
    assert "kind=" in WORDS[Why.NOT_THE_FORMAT]


# The host a request was sent on to


def test_the_start_of_a_hash_stands_for_a_host():
    assert host_mark(ELSEWHERE) == hashlib.sha256(ELSEWHERE.encode()).hexdigest()[:12]
    assert public_log.is_public(f"host={host_mark(ELSEWHERE)}")
    assert not public_log.is_public(f"host={ELSEWHERE}")


def test_a_host_is_the_same_host_however_it_is_written():
    assert len({host_mark(name) for name in (ELSEWHERE, ELSEWHERE.upper(), f"{ELSEWHERE}.")}) == 1
    assert host_mark(ELSEWHERE) != host_mark(f"www.{ELSEWHERE}")


@pytest.mark.parametrize(
    "location",
    [
        f"https://{ELSEWHERE}/files/homes.csv?sig=zzyzx",
        f"https://{ELSEWHERE.upper()}:443/files/homes.csv",
        f"//{ELSEWHERE}/files/homes.csv",
    ],
)
def test_a_redirect_to_a_host_the_list_does_not_name_prints_the_hash_of_that_host(
    publisher: Publisher,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    location: str,
):
    publisher.pages["/files/homes"] = Answer(302, {"Location": location})
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent=AGENT, downloader=through(served)
    )
    assert (outcome.status, outcome.why) == (Status.FAILED, Why.REDIRECT_ELSEWHERE)
    line = as_a_run_shows_it(outcome)
    assert f" status=failed why=28 host={host_mark(ELSEWHERE)} seconds=" in line
    assert "made-up.example" not in line.lower() and "zzyzx" not in line + outcome.words()
    # A person at a terminal is still told the host by name.
    assert ELSEWHERE in outcome.words()


def test_a_redirect_that_cannot_be_read_prints_no_hash(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    publisher.pages["/files/homes"] = Answer(302, {"Location": "https://made up/x"})
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent=AGENT, downloader=through(served)
    )
    assert outcome.why is Why.REDIRECT_ELSEWHERE
    assert " host=" not in as_a_run_shows_it(outcome)


def test_the_words_say_where_the_hash_is_printed_and_how_to_match_it():
    said = WORDS[Why.REDIRECT_ELSEWHERE]
    assert "Name that host in the list under may_redirect_to" in said
    assert "host=" in said and "plan --words" in said


# Plan prints the same hash beside each host it knows

LIST = f"""
schema_version = 1
build = "made-up"

[[file]]
item = "homes"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes"
format = "csv"
page = "https://made-up.example/homes"
url = "{PUBLISHER}/files/homes"
max_bytes = 1000000
edition = "2025"
data_period = {{ as_at = "2025-03-31" }}
"""


class Folders:
    def __init__(self, root: Path, text: str = LIST) -> None:
        self.store, self.receipts = root / "store", root / "receipts"
        self.registry, self.list = root / "registry.toml", root / "made-up.toml"
        self.registry.write_text(MADE_UP_REGISTRY, encoding="utf-8")
        self.list.write_text(text, encoding="utf-8")
        self.environment = {
            "BURRO_STORE_FOLDER": str(self.store),
            "BURRO_FETCH_CONTACT": "data@made-up.example",
        }

    def words(self, step: str, *more: str) -> list[str]:
        kept = ["--receipts", str(self.receipts)] if step == "fetch" else []
        return [step, "--list", str(self.list), "--registry", str(self.registry), *kept, *more]


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


def test_plan_prints_the_hash_beside_each_host_the_list_and_the_entry_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    named = LIST + f'may_redirect_to = ["{ELSEWHERE}", "More.Made-Up.example"]\n'
    folders = Folders(tmp_path, named)
    assert main(folders.words("plan", "--words"), {}, never) == 0
    spoken = capsys.readouterr().out
    for host in (
        "files.made-up.example",
        "made-up.example",
        ELSEWHERE,
        "more.made-up.example",
    ):
        assert f"{host} host={host_mark(host)}" in spoken, host
    assert spoken.count(f"host={host_mark(ELSEWHERE)}") == 1


def test_plan_prints_no_host_and_no_hash_where_anyone_reads(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    assert main(folders.words("plan"), {}, never) == 0
    quiet = capsys.readouterr().out
    assert "host=" not in quiet and "made-up.example" not in quiet


def test_the_hash_a_run_prints_is_the_one_plan_prints_beside_the_host(
    tmp_path: Path, publisher: Publisher, served: Served, capsys: pytest.CaptureFixture[str]
):
    """A run fails and shows a hash. A person names the host they think it is, and plan agrees."""
    publisher.pages["/files/homes"] = Answer(302, {"Location": f"https://{ELSEWHERE}/homes.csv"})
    folders = Folders(tmp_path)
    assert main(folders.words("fetch"), folders.environment, through(served)) == 1
    (shown,) = [line for line in capsys.readouterr().out.splitlines() if " host=" in line]
    in_the_run = shown.split(" host=")[1].split()[0]

    folders.list.write_text(LIST + f'may_redirect_to = ["{ELSEWHERE}"]\n', encoding="utf-8")
    main(folders.words("plan", "--words"), {}, never)
    beside = [line for line in capsys.readouterr().out.splitlines() if ELSEWHERE in line]
    assert beside and all(f"{ELSEWHERE} host={in_the_run}" in line for line in beside)
