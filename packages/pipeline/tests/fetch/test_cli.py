"""The commands of fetch, driven as a person or a workflow drives them.

Every file is made up. Only the tests of `fetch` are let through to the
loopback stand-in. Every other command is driven with sockets blocked, which
is the proof that it opens none.
"""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

import public_log
import pytest
from burro_pipeline.evidence import How, read_receipts, seal
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded, Limits, download
from burro_pipeline.fetch.run import Why
from burro_pipeline.fetch.sources import LISTS
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import load

from .support import (
    CANARY_ROW,
    MADE_UP_REGISTRY,
    ONLY_LOOPBACK,
    Answer,
    Served,
    made_up_csv,
    made_up_zip,
    serving,
)

ROWS = [f"E0{n},{CANARY_ROW} {n},{n}0" for n in range(1, 6)]
BODY = ("\n".join(["code,name,homes", *ROWS]) + "\n").encode()
SHA256 = hashlib.sha256(BODY).hexdigest()
PUBLISHER = "https://files.made-up.example"

LIST = """
schema_version = 1
build = "made-up"

[[file]]
item = "homes"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up homes by made-up area"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/files/homes.csv"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025-03-31" }

[[file]]
item = "notes"
source_id = "made-up-homes"
use = "display"
what = "Made-up notes, which a person saves"
format = "zip"
page = "https://made-up.example/notes"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025" }
by_hand = true
"""


class Folders:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.store = root / "store"
        self.receipts = root / "receipts"
        self.registry = root / "registry.toml"
        self.list = root / "made-up.toml"
        self.registry.write_text(MADE_UP_REGISTRY, encoding="utf-8")
        self.list.write_text(LIST, encoding="utf-8")
        self.environment = {
            "BURRO_STORE_FOLDER": str(self.store),
            "BURRO_FETCH_CONTACT": "data@made-up.example",
        }

    def common(self) -> list[str]:
        return ["--list", str(self.list), "--registry", str(self.registry)]


@pytest.fixture
def folders(tmp_path: Path) -> Folders:
    return Folders(tmp_path)


@pytest.fixture
def served() -> Iterator[Served]:
    pages = {"/files/homes.csv": Answer(body=BODY)}
    with serving(lambda request: pages.get(request.path, Answer(404))) as server:
        yield server


def through(served: Served):
    """A downloader that finds the made-up publisher at the stand-in's address."""

    def downloader(
        address: str,
        to: Path,
        limits: Limits,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
    ) -> Downloaded:
        assert address.startswith(PUBLISHER)
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


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


# The first line of a step that writes to the store, or shows that it answers.
A_FOLDER = "step=store kind=folder"


def printed(capsys: pytest.CaptureFixture[str]) -> tuple[list[str], str]:
    """What a step printed, less the line that says which kind of store it was given."""
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    return lines[1:] if lines[:1] == [A_FOLDER] else lines, captured.err


@ONLY_LOOPBACK
def test_fetch_fetches_what_has_an_address_and_says_what_is_missing(
    folders: Folders, served: Served, capsys: pytest.CaptureFixture[str]
):
    code = main(
        ["fetch", *folders.common(), "--receipts", str(folders.receipts)],
        folders.environment,
        through(served),
    )
    lines, errors = printed(capsys)
    assert code == 1
    assert errors == ""
    assert lines == [
        f"step=fetch n=1 source=made-up-homes status=ok file_id=f-{SHA256[:12]} "
        f"sha256={SHA256} bytes={len(BODY)} new=1 seconds={lines[0].rsplit('=', 1)[1]}",
        f"step=fetch n=2 source=made-up-homes status=missing by_hand=1 "
        f"why={int(Why.NOT_SAVED_BY_HAND)} seconds={lines[1].rsplit('=', 1)[1]}",
        "step=fetch status=failed files=2 ok=1 skipped=0 refused=0 failed=0 missing=1 "
        "unreadable=0 differs=0",
    ]
    assert [held.sha256 for held in FolderStore(folders.store).list()] == [SHA256]
    assert [receipt.how for receipt in read_receipts(folders.receipts)] == [How.FETCHED]


@ONLY_LOOPBACK
def test_fetch_can_be_asked_for_one_item_which_keeps_its_number_in_the_list(
    folders: Folders, served: Served, capsys: pytest.CaptureFixture[str]
):
    arguments = ["fetch", *folders.common(), "--receipts", str(folders.receipts)]
    assert main([*arguments, "--only", "homes"], folders.environment, through(served)) == 0
    assert printed(capsys)[0][0].startswith("step=fetch n=1 source=made-up-homes status=ok ")
    assert main([*arguments, "--only", "notes"], folders.environment, never) == 1
    assert printed(capsys)[0][0].startswith("step=fetch n=2 source=made-up-homes status=missing ")


@ONLY_LOOPBACK
def test_nothing_fetch_prints_holds_a_row_an_address_a_name_or_a_folder(
    folders: Folders, served: Served, capsys: pytest.CaptureFixture[str]
):
    main(
        ["fetch", *folders.common(), "--receipts", str(folders.receipts), "--words"],
        folders.environment,
        through(served),
    )
    lines, errors = printed(capsys)
    everything = "\n".join(lines) + errors
    for secret in (
        CANARY_ROW,
        "made-up.example",
        "127.0.0.1",
        str(served.port),
        "homes.csv",
        str(folders.store),
        folders.environment["BURRO_FETCH_CONTACT"],
    ):
        assert secret not in everything


def test_fetch_with_words_adds_a_sentence_that_the_public_log_would_withhold(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    arguments = ["fetch", *folders.common(), "--receipts", str(folders.receipts)]
    main([*arguments, "--only", "notes", "--words"], folders.environment, never)
    lines, _ = printed(capsys)
    assert lines[1].startswith("  The file is saved by hand, and no receipt of it was found.")
    assert lines[1].endswith(" hand it over with the step by-hand.")
    assert [public_log.is_public(line) for line in lines] == [False, False, True]
    # The source is made up, so the log does not know its id. A real id is let through.
    real = lines[0].replace("made-up-homes", "defra-pcm-background-air")
    assert public_log.is_public(real)


def test_fetch_needs_an_address_a_publisher_can_write_to(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    environment = {"BURRO_STORE_FOLDER": str(folders.store)}
    assert main(["fetch", *folders.common()], environment, never) == 2
    assert "BURRO_FETCH_CONTACT" in printed(capsys)[1]


def test_fetch_needs_a_store_and_names_the_variables_and_nothing_they_hold(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    environment = {
        "BURRO_FETCH_CONTACT": "data@made-up.example",
        "BURRO_STORE_ENDPOINT": "https://zzyzx-account.made-up.example",
        "BURRO_STORE_SECRET": "zzyzx-canary-secret",
    }
    assert main(["fetch", *folders.common()], environment, never) == 2
    lines, errors = printed(capsys)
    assert lines == []
    assert "BURRO_STORE_BUCKET" in errors
    assert "zzyzx" not in errors


@pytest.mark.parametrize(
    ("arguments", "said"),
    [
        (["--list", "m99"], "no list of that name"),
        (["--list", "{list}", "--registry", "{root}/absent.toml"], "no registry"),
        (["--list", "{list}", "--registry", "{registry}", "--only", "absent"], "no item named"),
    ],
)
def test_fetch_stops_before_it_starts_when_it_cannot_read_what_it_was_given(
    folders: Folders, capsys: pytest.CaptureFixture[str], arguments: list[str], said: str
):
    filled = [
        argument.format(list=folders.list, registry=folders.registry, root=folders.root)
        for argument in arguments
    ]
    assert main(["fetch", *filled], folders.environment, never) == 2
    lines, errors = printed(capsys)
    assert lines == []
    assert said in errors and errors.count("\n") == 1


def test_a_fault_of_its_own_is_named_by_its_kind_and_nothing_it_said(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    """A fault in one file fails that file. `test_one_file_at_a_time.py` has the rest."""

    def faulty(*_: object, **__: object) -> Downloaded:
        raise RuntimeError(f"{CANARY_ROW} at https://zzyzx.made-up.example")

    arguments = ["fetch", *folders.common(), "--only", "homes", "--words"]
    assert main(arguments, folders.environment, faulty) == 1
    lines, errors = printed(capsys)
    assert errors == ""
    assert lines[0].startswith(f"step=fetch n=1 source=made-up-homes status=failed why={Why.FAULT}")
    assert lines[1].startswith("  Fetch stopped on a fault of its own")
    assert lines[1].endswith(" (RuntimeError).")
    assert CANARY_ROW not in "".join(lines) and "zzyzx" not in "".join(lines)
    with pytest.raises(RuntimeError):
        main(arguments, folders.environment | {"BURRO_FETCH_DEBUG": "1"}, faulty)


def test_plan_says_what_the_gate_says_and_what_is_missing(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    folders.list.write_text(
        LIST.replace('use = "display"', 'use = "gazetteer"').replace(
            'url = "https://files.made-up.example/files/homes.csv"\n', ""
        )
    )
    assert main(["plan", *folders.common()], {}, never) == 1
    lines, errors = printed(capsys)
    assert errors == ""
    assert lines == [
        "step=plan n=1 source=made-up-homes status=missing why=3 seconds=0.0",
        "step=plan n=2 source=made-up-homes status=refused by_hand=1 why=1 seconds=0.0",
        "step=plan status=missing files=2 ready=0",
    ]


def test_plan_passes_a_list_that_is_ready(folders: Folders, capsys: pytest.CaptureFixture[str]):
    assert main(["plan", *folders.common()], {}, never) == 0
    assert printed(capsys)[0][-1] == "step=plan status=ok files=2 ready=2"


def test_the_plan_of_the_first_build_names_each_page_to_a_person_and_to_no_log(
    capsys: pytest.CaptureFixture[str],
):
    registry = str(Path(__file__).parents[4] / "registry" / "sources")
    assert main(["plan", "--list", "m1", "--registry", registry], {}, never) == 0
    quiet, _ = printed(capsys)
    assert all(public_log.is_public(line) for line in quiet)
    # Every file has an address, an edition and a period, so each is ready for a receipt.
    assert quiet[-1] == "step=plan status=ok files=11 ready=11"
    assert "https://" not in "\n".join(quiet)
    main(["plan", "--list", "m1", "--registry", registry, "--words"], {}, never)
    spoken, _ = printed(capsys)
    assert any("https://uk-air.defra.gov.uk/data/pcm-data" in line for line in spoken)
    assert not any("The list holds no address for the file" in line for line in spoken)
    assert not any("does not state its edition and its period" in line for line in spoken)


def test_plan_says_of_no_file_that_it_is_stored(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    """Plan fetches nothing. The words of a run say what a run did, and plan has done none of it."""
    folders.list.write_text(LIST.replace('data_period = { as_at = "2025-03-31" }\n', ""))
    assert main(["plan", *folders.common(), "--words"], {}, never) == 1
    spoken, _ = printed(capsys)
    assert any("does not state its edition and its period" in line for line in spoken)
    assert [line for line in spoken if "is stored" in line or "was written" in line] == []
    assert any("A fetch would store the file and write no receipt" in line for line in spoken)


@pytest.fixture
def saved(tmp_path: Path) -> Path:
    folder = tmp_path / "Downloads"
    folder.mkdir()
    return made_up_zip(folder / "Made-up notes.zip", {"notes.csv": BODY})


def by_hand(folders: Folders, saved: Path, *more: str) -> int:
    arguments = ["by-hand", *folders.common(), "--receipts", str(folders.receipts)]
    arguments += ["--item", "notes", "--file", str(saved)]
    arguments += ["--url", "https://made-up.example/notes/download", "--saved-on", "2026-09-24"]
    return main([*arguments, *more], folders.environment, never)


def test_by_hand_stores_the_file_with_a_receipt_marked_by_hand(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str]
):
    assert by_hand(folders, saved) == 0
    lines, errors = printed(capsys)
    sha256 = hashlib.sha256(saved.read_bytes()).hexdigest()
    assert errors == ""
    assert lines == [
        f"step=fetch n=2 source=made-up-homes status=ok file_id=f-{sha256[:12]} "
        f"sha256={sha256} bytes={saved.stat().st_size} new=1 by_hand=1 seconds=0.0"
    ]
    (receipt,) = read_receipts(folders.receipts)
    assert (receipt.how, receipt.publisher_file) == (How.BY_HAND, "Made-up notes.zip")
    assert receipt.url == "https://made-up.example/notes/download"


def test_by_hand_says_in_words_why_it_refused(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str]
):
    saved.write_bytes(b"<html><body>Sign in</body></html>")
    assert by_hand(folders, saved, "--words") == 1
    lines, _ = printed(capsys)
    assert " status=unreadable " in lines[0]
    assert lines[1].startswith("  What arrived is not the format listed.")


def test_once_a_file_is_saved_by_hand_the_list_is_whole(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    arguments = ["fetch", *folders.common(), "--receipts", str(folders.receipts), "--only", "notes"]
    assert main(arguments, folders.environment, never) == 0


def test_held_writes_the_listing_that_seal_reads(
    folders: Folders, saved: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    capsys.readouterr()
    out = tmp_path / "listing.json"
    assert main(["held", "--out", str(out)], folders.environment, never) == 0
    lines, _ = printed(capsys)
    assert lines == [f"step=store status=ok files=1 bytes={saved.stat().st_size}"]
    assert public_log.is_public(lines[0])
    listing = json.loads(out.read_text())
    (receipt,) = read_receipts(folders.receipts)
    assert listing == {receipt.vault_key(): receipt.bytes}
    lock = seal(
        "lon-2026-09-24-01",
        "2026-09-24T10:00:00Z",
        "0" * 40,
        read_receipts(folders.receipts),
        listing,
        load(folders.registry),
        tmp_path,
    )
    assert [locked.name for locked in lock.inputs] == [receipt.file_id]


# The store, held to the receipts: whether it holds every file that has one

REPOSITORY = Path(__file__).resolve().parents[4]
# What a line says of the made-up list, as a line says it of a list of this repository.
AS_IN_A_RUN = {
    "source=made-up-homes": "source=defra-pcm-background-air",
    "list=made-up": "list=m1",
    "item=notes": "item=oa-lookup",
}


def held_to(folders: Folders, listed: str = LIST) -> int:
    """Hold the store to the receipts, and to a folder of lists that holds the made-up one."""
    lists = folders.root / "lists"
    lists.mkdir(exist_ok=True)
    (lists / "made-up.toml").write_text(listed, encoding="utf-8")
    arguments = ["held", "--receipts", str(folders.receipts), "--lists", str(lists)]
    return main(arguments, folders.environment, never)


def as_in_a_run(line: str) -> str:
    for made_up, real in AS_IN_A_RUN.items():
        line = line.replace(made_up, real)
    return line


def test_a_store_that_holds_every_file_with_a_receipt_says_so_in_one_line(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    capsys.readouterr()
    assert held_to(folders) == 0
    lines, errors = printed(capsys)
    assert errors == ""
    assert lines == [
        f"step=store status=ok files=1 bytes={saved.stat().st_size}",
        # The list names two files, and one has its receipt. The other is not asked about.
        "step=store list=made-up status=ok files=2 receipts=1 missing=0 differs=0",
        "step=store status=ok lists=1 receipts=1 missing=0 differs=0 unlisted=0",
    ]
    assert all(public_log.is_public(as_in_a_run(line)) for line in lines)


def test_a_file_that_is_gone_from_the_store_is_named_and_the_step_ends_red(
    folders: Folders, saved: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    (receipt,) = read_receipts(folders.receipts)
    (folders.store / receipt.vault_key()).rename(tmp_path / "moved out of the store")
    capsys.readouterr()
    assert held_to(folders) == 1
    lines, errors = printed(capsys)
    assert lines == [
        "step=store status=ok files=0 bytes=0",
        "step=store list=made-up status=missing files=2 receipts=1 missing=1 differs=0",
        "step=store list=made-up source=made-up-homes item=notes status=missing "
        f"file_id={receipt.file_id}",
        "step=store status=missing lists=1 receipts=1 missing=1 differs=0 unlisted=0",
    ]
    assert all(public_log.is_public(as_in_a_run(line)) for line in lines)
    assert "does not hold every file that has a receipt" in errors and errors.count("\n") == 1


@pytest.mark.parametrize("how", ["of another size", "under another name"])
def test_a_file_that_is_not_as_its_receipt_has_it_differs(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str], how: str
):
    by_hand(folders, saved)
    (receipt,) = read_receipts(folders.receipts)
    kept = folders.store / receipt.vault_key()
    if how == "of another size":
        kept.write_bytes(kept.read_bytes()[:-1])
    else:
        kept.rename(kept.with_name("another name.zip"))
    capsys.readouterr()
    assert held_to(folders) == 1
    lines, _ = printed(capsys)
    assert lines[1:] == [
        "step=store list=made-up status=differs files=2 receipts=1 missing=0 differs=1",
        "step=store list=made-up source=made-up-homes item=notes status=differs "
        f"file_id={receipt.file_id}",
        "step=store status=differs lists=1 receipts=1 missing=0 differs=1 unlisted=0",
    ]


def test_a_receipt_that_is_of_no_file_of_a_list_is_held_to_the_store_all_the_same(
    folders: Folders, saved: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    (receipt,) = read_receipts(folders.receipts)
    # The list no longer names the file that was saved. Its receipt stands in the folder.
    without = LIST.split('[[file]]\nitem = "notes"')[0]
    capsys.readouterr()
    assert held_to(folders, without) == 0
    assert printed(capsys)[0][1:] == [
        "step=store list=made-up status=ok files=1 receipts=0 missing=0 differs=0",
        "step=store status=ok lists=1 receipts=1 missing=0 differs=0 unlisted=1",
    ]
    (folders.store / receipt.vault_key()).rename(tmp_path / "moved out of the store")
    assert held_to(folders, without) == 1
    lines, _ = printed(capsys)
    assert lines[1:] == [
        "step=store list=made-up status=ok files=1 receipts=0 missing=0 differs=0",
        f"step=store source=made-up-homes status=missing file_id={receipt.file_id}",
        "step=store status=missing lists=1 receipts=1 missing=1 differs=0 unlisted=1",
    ]
    assert all(public_log.is_public(as_in_a_run(line)) for line in lines)


@ONLY_LOOPBACK
def test_two_files_that_a_list_says_alike_are_told_apart_by_their_address(
    folders: Folders, served: Served, saved: Path, capsys: pytest.CaptureFixture[str]
):
    # The same source, use, edition and period, once fetched and once saved by a person.
    alike = LIST.replace('use = "display"', 'use = "scoring"').replace(
        'data_period = { as_at = "2025" }', 'data_period = { as_at = "2025-03-31" }'
    )
    folders.list.write_text(alike, encoding="utf-8")
    fetch = ["fetch", *folders.common(), "--receipts", str(folders.receipts)]
    assert main(fetch, folders.environment, through(served)) == 1
    assert by_hand(folders, saved) == 0
    got = {receipt.how: receipt for receipt in read_receipts(folders.receipts)}
    fetched, by_a_person = got[How.FETCHED], got[How.BY_HAND]
    for receipt in (fetched, by_a_person):
        (folders.store / receipt.vault_key()).unlink()
    capsys.readouterr()
    assert held_to(folders, alike) == 1
    lines, _ = printed(capsys)
    named = {line.split("item=")[1].split()[0]: line for line in lines if " item=" in line}
    assert set(named) == {"homes", "notes"}
    assert f"file_id={fetched.file_id}" in named["homes"]
    assert f"file_id={by_a_person.file_id}" in named["notes"]


def test_nothing_the_step_prints_of_a_file_holds_its_name_an_address_or_a_folder(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    (receipt,) = read_receipts(folders.receipts)
    (folders.store / receipt.vault_key()).unlink()
    capsys.readouterr()
    assert held_to(folders) == 1
    captured = capsys.readouterr()
    for secret in (str(folders.store), str(folders.root), "made-up.example", "Made-up notes"):
        assert secret not in captured.out + captured.err


@pytest.mark.parametrize(
    ("arguments", "said"),
    [
        (["held", "--lists", "{root}"], "so --receipts is given too"),
        (["held", "--receipts", "{root}/absent"], "holds no receipt"),
        (["held", "--receipts", "{root}/receipts", "--lists", "{root}/absent"], "holds no list"),
    ],
)
def test_held_stops_before_it_asks_the_store_when_it_was_given_nothing_to_hold_it_to(
    folders: Folders,
    saved: Path,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    said: str,
):
    by_hand(folders, saved)
    capsys.readouterr()
    filled = [argument.format(root=folders.root) for argument in arguments]
    assert main(filled, folders.environment, never) == 2
    out, errors = capsys.readouterr()
    # A folder that is wrong never reads as a store that holds everything.
    assert out == ""
    assert said in errors and errors.count("\n") == 1


def test_every_list_of_this_repository_is_held_and_every_line_is_one_a_run_may_show(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    receipts = REPOSITORY / "data" / "receipts"
    lists = sorted(path.stem for path in LISTS.glob("*.toml"))
    # Against a store that holds nothing, every file that has a receipt is missing.
    assert main(["held", "--receipts", str(receipts)], folders.environment, never) == 1
    lines, _ = printed(capsys)
    assert [line.split()[1] for line in lines if " source=" not in line][1:-1] == [
        f"list={name}" for name in lists
    ]
    held = len(list(receipts.glob("*/f-*.json")))
    assert held and lines[-1].startswith(
        f"step=store status=missing lists={len(lists)} receipts={held} missing={held} differs=0 "
    )
    assert all(public_log.is_public(line) for line in lines)
    assert len([line for line in lines if " source=" in line]) >= held


def test_the_step_names_a_file_by_the_item_that_a_build_pairs_its_receipt_with(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    """A build pairs a receipt with a file of its list, and the step must name the same file.

    Two files of one list may be said alike, with nothing in a receipt to tell them
    apart. A build gives them out in order, and so does the step.
    """
    from burro_pipeline.assemble.cli import of_the_list
    from burro_pipeline.evidence import LockError
    from burro_pipeline.fetch.sources import load_list

    folder = REPOSITORY / "data" / "receipts"
    main(["held", "--receipts", str(folder)], folders.environment, never)
    lines, _ = printed(capsys)
    named = [
        dict(part.split("=", 1) for part in line.split()) for line in lines if " item=" in line
    ]
    receipts = read_receipts(folder)
    for path in sorted(LISTS.glob("*.toml")):
        listed = load_list(path.stem)
        try:
            paired, files, _ = of_the_list(receipts, listed.files)
        except LockError:
            # More receipts than files that are said alike: a build picks none, and nor is
            # the step held to a choice.
            continue
        by_a_build = {
            (file.item, receipt.file_id) for file, receipt in zip(files, paired, strict=True)
        }
        by_the_step = {(one["item"], one["file_id"]) for one in named if one["list"] == path.stem}
        # A build takes one edition of a file that states its own. The step names each.
        assert by_the_step >= by_a_build, path.stem
        assert {item for item, _ in by_the_step} == {item for item, _ in by_a_build}


def test_describe_reads_a_stored_file_by_its_file_id(
    folders: Folders, saved: Path, capsys: pytest.CaptureFixture[str]
):
    by_hand(folders, saved)
    capsys.readouterr()
    sha256 = hashlib.sha256(saved.read_bytes()).hexdigest()
    assert main(["describe", f"f-{sha256[:12]}", "--inside"], folders.environment, never) == 0
    out, errors = capsys.readouterr()
    assert errors == ""
    assert CANARY_ROW not in out
    shape = json.loads(out)
    assert list(shape)[:4] == ["file_id", "source", "sha256", "kind"]
    assert (shape["file_id"], shape["source"], shape["kind"]) == (
        f"f-{sha256[:12]}",
        "made-up-homes",
        "zip",
    )
    assert shape["members"][0]["inside"]["columns"] == ["code", "name", "homes"]
    assert shape["members"][0]["inside"]["rows"] == 5


def test_describe_reads_a_file_on_disk(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    path = made_up_csv(tmp_path / "homes.csv", "code,name,homes", ROWS)
    assert main(["describe", "--path", str(path)], {}, never) == 0
    out, _ = capsys.readouterr()
    assert CANARY_ROW not in out
    assert json.loads(out)["columns"] == ["code", "name", "homes"]


@pytest.mark.parametrize(
    ("arguments", "said"),
    [
        (["describe"], "a file id or a hash, or --path"),
        (["describe", "f-000000000000"], "holds no file"),
        (["describe", "homes.csv"], "a file id or a hash"),
        (["describe", "--path", "{root}/absent.csv"], "could not be read from disk"),
    ],
)
def test_describe_says_in_one_line_what_it_could_not_do(
    folders: Folders, capsys: pytest.CaptureFixture[str], arguments: list[str], said: str
):
    filled = [argument.format(root=folders.root) for argument in arguments]
    assert main(filled, folders.environment, never) == 2
    out, errors = capsys.readouterr()
    assert out == ""
    assert said in errors and errors.count("\n") == 1


def test_why_gives_the_meaning_of_every_number(capsys: pytest.CaptureFixture[str]):
    assert main(["why"], {}, never) == 0
    lines, _ = printed(capsys)
    assert [line.split()[0] for line in lines] == [f"why={int(why)}" for why in Why]
    assert all(line.endswith(".") for line in lines)
