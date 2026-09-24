"""What goes wrong with one file is said of that file, and the run goes on to the next.

A letter outside ASCII in one address stopped a whole run: the request could
not be written, and the fault was nobody's to catch. So an address that holds
one is refused before anything is asked, and any fault of fetch's own in one
file gives that file a failed status with a number of its own.

The publisher is a stand-in on the loopback address, and every file is made up.
"""

import hashlib
from collections.abc import Iterator
from pathlib import Path

import public_log
import pytest
from burro_pipeline.evidence import read_receipts
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import (
    Downloaded,
    DownloadRefused,
    Limits,
    Reason,
    download,
    may_be_asked,
    next_address,
    user_agent,
)
from burro_pipeline.fetch.run import WORDS, Status, Why, fetch
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore, Held
from burro_pipeline.registry import Registry, load

from .support import CANARY_ROW, MADE_UP_REGISTRY, ONLY_LOOPBACK, Answer, Served, serving

BODY = b"code,homes\nmade-up-1,10\n"
SHA256 = hashlib.sha256(BODY).hexdigest()
AGENT = user_agent("data@made-up.example")
LIMITS = Limits(max_bytes=1_000_000, connect_seconds=2, read_seconds=2, total_seconds=5)
FILES = "https://files.made-up.example/files"
# Addresses as a person might copy them from the bar of a browser.
NOT_ASCII = [
    f"{FILES}/café homes.csv".replace(" ", "%20"),
    f"{FILES}/homes.csv?name=café",
    f"{FILES}/住宅.csv",
    f"{FILES}/homes\u2013final.csv",
    f"{FILES}/homes.csv#café",
]


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
def served() -> Iterator[Served]:
    pages = {
        "/files/homes.csv": Answer(body=BODY),
        "/latest": Answer(302, {"Location": "/files/café.csv"}),
    }
    with serving(lambda request: pages.get(request.path, Answer(404))) as server:
        yield server


def listed(item: str, url: str, **changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": item,
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": url,
        "url_parameters": ["name"],
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def gives_the_file(
    address: str,
    to: Path,
    limits: Limits,
    *,
    agent: str,
    may_redirect_to: tuple[str, ...] = (),
) -> Downloaded:
    """A publisher that gives the made-up file for any address a download would ask."""
    may_be_asked(address)
    to.write_bytes(BODY)
    return Downloaded(SHA256, len(BODY), address, "homes.csv", "text/csv")


# The download


@pytest.mark.disable_socket
@pytest.mark.parametrize("address", NOT_ASCII)
def test_an_address_with_a_letter_outside_ascii_is_refused_before_anything_is_asked(
    tmp_path: Path, address: str
):
    with pytest.raises(DownloadRefused) as refused:
        download(address, tmp_path / "file", LIMITS, agent=AGENT)
    assert refused.value.reason is Reason.NOT_ASCII
    assert "made-up" not in str(refused.value)
    with pytest.raises(DownloadRefused) as unasked:
        may_be_asked(address)
    assert unasked.value.reason is Reason.NOT_ASCII


@ONLY_LOOPBACK
def test_a_publisher_is_never_sent_a_request_that_cannot_be_written(served: Served, tmp_path: Path):
    """As it was, the request was made ready, could not be written, and the fault went up."""
    address = f"{served.address}/files/café.csv"
    with pytest.raises(DownloadRefused) as refused:
        download(address, tmp_path / "file", LIMITS, agent=AGENT, loopback_for_tests=True)
    assert refused.value.reason is Reason.NOT_ASCII
    assert served.seen == []
    assert list(tmp_path.iterdir()) == []


@ONLY_LOOPBACK
def test_a_publisher_that_sends_a_request_on_to_such_an_address_is_refused(
    served: Served, tmp_path: Path
):
    with pytest.raises(DownloadRefused) as refused:
        download(
            f"{served.address}/latest",
            tmp_path / "file",
            LIMITS,
            agent=AGENT,
            loopback_for_tests=True,
        )
    assert refused.value.reason is Reason.NOT_ASCII
    assert [request.path for request in served.seen] == ["/latest"]


def test_where_a_redirect_leads_is_refused_for_a_letter_outside_ascii():
    with pytest.raises(DownloadRefused) as refused:
        next_address(f"{FILES}/latest", "/files/café.csv")
    assert refused.value.reason is Reason.NOT_ASCII


def test_an_address_written_as_a_browser_sends_it_may_be_asked():
    may_be_asked(f"{FILES}/caf%C3%A9%20homes.csv?name=caf%C3%A9")


# A run of fetch


@pytest.mark.parametrize("address", NOT_ASCII[:4])
def test_a_letter_outside_ascii_fails_its_file_and_the_run_goes_on(
    registry: Registry, store: FolderStore, receipts: Path, address: str
):
    files = [listed("first", address), listed("second", f"{FILES}/homes.csv")]
    first, second = fetch(files, registry, store, receipts, agent=AGENT, downloader=gives_the_file)
    assert (first.status, first.why) == (Status.FAILED, Why.NOT_ASCII)
    assert f" status=failed why={int(Why.NOT_ASCII)} " in first.line()
    assert first.line().isascii() and first.words().isascii()
    assert second.status is Status.OK
    assert len(store.list()) == len(read_receipts(receipts)) == 1


def faulty(
    address: str,
    to: Path,
    limits: Limits,
    *,
    agent: str,
    may_redirect_to: tuple[str, ...] = (),
) -> Downloaded:
    """A fault of fetch's own, for one address of the list and no other."""
    if address.endswith("/faulty.csv"):
        raise RuntimeError(f"{CANARY_ROW} at https://zzyzx.made-up.example")
    return gives_the_file(address, to, limits, agent=agent)


def test_a_fault_in_one_file_fails_that_file_and_the_run_goes_on(
    registry: Registry, store: FolderStore, receipts: Path
):
    files = [
        listed("first", f"{FILES}/homes.csv"),
        listed("second", f"{FILES}/faulty.csv"),
        listed("third", f"{FILES}/homes.csv?name=third"),
    ]
    first, second, third = fetch(files, registry, store, receipts, agent=AGENT, downloader=faulty)
    assert (first.status, third.status) == (Status.OK, Status.OK)
    assert (second.status, second.why, second.held) == (Status.FAILED, Why.FAULT, None)
    assert f" status=failed why={int(Why.FAULT)} " in second.line()
    # The kind of the fault is said to a person. Nothing the fault said is said to anyone.
    assert "(RuntimeError)" in second.words()
    for said in (second.line(), second.words()):
        assert CANARY_ROW not in said and "zzyzx" not in said


def test_a_fault_in_the_store_fails_that_file_and_the_run_goes_on(
    registry: Registry, receipts: Path, tmp_path: Path
):
    class Faulty(FolderStore):
        def put(self, source_id: str, name: str, content: Path) -> tuple[Held, bool]:
            if not self.list():
                super().put(source_id, name, content)
                raise KeyError(CANARY_ROW)
            return super().put(source_id, name, content)

    files = [listed("first", f"{FILES}/homes.csv"), listed("second", f"{FILES}/homes.csv")]
    first, second = fetch(
        files, registry, Faulty(tmp_path / "store"), receipts, agent=AGENT, downloader=faulty
    )
    assert (first.status, first.why) == (Status.FAILED, Why.FAULT)
    assert "(KeyError)" in first.words() and CANARY_ROW not in first.words()
    assert second.status is Status.OK


def test_a_developer_who_asks_is_given_the_fault_itself(
    registry: Registry, store: FolderStore, receipts: Path
):
    files = [listed("second", f"{FILES}/faulty.csv")]
    with pytest.raises(RuntimeError):
        fetch(files, registry, store, receipts, agent=AGENT, downloader=faulty, debug=True)


def test_each_has_a_number_of_its_own_and_words_that_say_what_to_do():
    assert len({int(why) for why in Why}) == len(Why)
    assert "percent-encoded" in WORDS[Why.NOT_ASCII]
    assert "went on to the next" in WORDS[Why.FAULT]
    assert "BURRO_FETCH_DEBUG=1" in WORDS[Why.FAULT]


# The command line

LIST = """
schema_version = 1
build = "made-up"

[[file]]
item = "first"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/files/café.csv"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025-03-31" }

[[file]]
item = "second"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/files/faulty.csv"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025-03-31" }

[[file]]
item = "third"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/files/homes.csv"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025-03-31" }
"""


class Folders:
    def __init__(self, root: Path) -> None:
        self.store, self.receipts = root / "store", root / "receipts"
        self.registry, self.list = root / "registry.toml", root / "made-up.toml"
        self.registry.write_text(MADE_UP_REGISTRY, encoding="utf-8")
        self.list.write_text(LIST, encoding="utf-8")
        self.environment = {
            "BURRO_STORE_FOLDER": str(self.store),
            "BURRO_FETCH_CONTACT": "data@made-up.example",
        }

    def words(self, step: str) -> list[str]:
        more = ["--receipts", str(self.receipts)] if step == "fetch" else []
        return [step, "--list", str(self.list), "--registry", str(self.registry), *more]


def of_files(lines: list[str], step: str) -> list[str]:
    """The lines a step printed of the files of a list, less how long each took."""
    return [line.rsplit(" seconds=", 1)[0] for line in lines if line.startswith(f"step={step} n=")]


def test_a_run_ends_with_a_line_for_every_file_whatever_went_wrong_with_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    assert main(folders.words("fetch"), folders.environment, faulty) == 1
    out = capsys.readouterr()
    lines = out.out.splitlines()
    assert out.err == ""
    assert of_files(lines, "fetch") == [
        "step=fetch n=1 source=made-up-homes status=failed why=33",
        "step=fetch n=2 source=made-up-homes status=failed why=17",
        f"step=fetch n=3 source=made-up-homes status=ok file_id=f-{SHA256[:12]} "
        f"sha256={SHA256} bytes={len(BODY)} new=1",
    ]
    assert lines[-1] == (
        "step=fetch status=failed files=3 ok=1 skipped=0 refused=0 failed=2 missing=0 "
        "unreadable=0 differs=0"
    )
    for line in lines:
        assert public_log.is_public(line.replace("source=made-up-homes", "source=synthetic"))
    assert CANARY_ROW not in out.out and "zzyzx" not in out.out and out.out.isascii()


def test_plan_finds_an_address_that_cannot_be_asked_before_a_run_does(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    assert main([*folders.words("plan"), "--words"], {}, faulty) == 1
    lines = capsys.readouterr().out.splitlines()
    assert of_files(lines, "plan") == [
        "step=plan n=1 source=made-up-homes status=failed why=33",
        "step=plan n=2 source=made-up-homes status=ok",
        "step=plan n=3 source=made-up-homes status=ok",
    ]
    assert lines[-1] == "step=plan status=missing files=3 ready=2"
    assert any("percent-encoded" in line for line in lines)


def test_a_developer_who_asks_is_given_the_fault_at_the_command_line(tmp_path: Path):
    folders = Folders(tmp_path)
    with pytest.raises(RuntimeError):
        main(folders.words("fetch"), folders.environment | {"BURRO_FETCH_DEBUG": "1"}, faulty)


def test_a_fault_that_is_of_no_one_file_still_stops_the_step_and_says_its_kind_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    def broken(*_: object) -> str:
        raise RuntimeError(f"{CANARY_ROW} at https://zzyzx.made-up.example")

    monkeypatch.setattr("burro_pipeline.fetch.cli.summary", broken)
    folders = Folders(tmp_path)
    assert main(folders.words("fetch"), folders.environment, faulty) == 3
    out = capsys.readouterr()
    assert out.err == "error: fetch stopped on a fault of its own (RuntimeError)\n"
    assert CANARY_ROW not in out.out and "zzyzx" not in out.out
