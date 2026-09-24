"""Each link of the walk, broken in turn.

`test_walk.py` walks the whole of M0 on made-up files. Here one link is broken
at a time, and the build must stop there: with an exit code that is not 0, a
line anyone may read that names the step and the rule, and words beside it
that say what is wrong and what a person can do about it. It must never stop
with a traceback, and never repeat a row, an address or what it was handed.

Nothing here is real, and no publisher is reached.
"""

import json
import shutil
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.evidence import Evidence, LockError, read_receipts
from burro_pipeline.fetch import cli as fetch_cli
from burro_pipeline.fetch.download import Downloaded, Limits
from burro_pipeline.fetch.run import WORDS, Why
from burro_pipeline.fetch.store import FolderStore, StoreError

from ..fetch.support import ONLY_LOOPBACK, Answer, Served, made_up_zip, serving
from .support import (
    CANARY,
    FLATS,
    HOMES,
    MEASURES,
    PUBLISHER,
    RELEASE_ID,
    Said,
    Walk,
    as_the_publisher,
    city,
    evidence_of,
    files_of,
    publishing,
    the_list,
)

pytestmark = ONLY_LOOPBACK

FILES = files_of(city())
GATED = ("gated", "Its made-up terms changed on 1 October.", '"validation_only"')
FACT = f"lon-n0001/feature/{FLATS}"


@pytest.fixture
def served() -> Iterator[Served]:
    with publishing(FILES) as server:
        yield server


@pytest.fixture
def walk(tmp_path: Path, served: Served) -> Walk:
    return Walk(tmp_path, served)


def stopped(said: Said, code: int, *lines: str) -> str:
    """The words a step stopped with. It must stop as a step does, and give nothing away."""
    assert said.code == code, said.everything
    assert said.lines[-len(lines) :] == list(lines) if lines else True, said.lines
    for hidden in (CANARY, "Traceback", "made-up.example", "127.0.0.1", MEASURES):
        assert hidden not in said.everything
    return said.words


def line_of(said: Said, item: int) -> str:
    """What fetch said of one file of the list, with the sentence under it."""
    at = next(n for n, line in enumerate(said.lines) if line.startswith(f"step=fetch n={item} "))
    return "\n".join(said.lines[at : at + 2])


def nothing_is_kept(walk: Walk) -> bool:
    return not walk.receipts.exists() and FolderStore(walk.store).list() == []


def said_with_what_to_do(said: str, why: Why) -> bool:
    """Whether the words under a line are fetch's own for its reason: what is wrong, and what to do.

    The words are fetch's to choose. They are more than one sentence, and they
    are the ones the step `why` prints for the number on the line.
    """
    return WORDS[why].count(". ") >= 1 and WORDS[why] in said


# The gate, before a file is asked for


def test_a_source_the_registry_refuses_is_not_fetched_and_the_registry_says_why(
    walk: Walk, served: Served
):
    walk.register(*GATED)
    said = walk.fetch("--words")
    stopped(
        said,
        1,
        "step=fetch status=failed files=6 ok=0 skipped=0 refused=6 failed=0 missing=0 "
        "unreadable=0 differs=0",
    )
    assert "status=refused why=1 " in line_of(said, 6)
    assert "The licence registry refuses this source for this use" in line_of(said, 6)
    assert "is gated, not approved: Its made-up terms changed on 1 October." in line_of(said, 6)
    assert served.seen == []
    assert nothing_is_kept(walk)


def test_one_file_the_registry_refuses_stops_every_file_of_the_list(walk: Walk, served: Served):
    walk.register(uses='"gazetteer", "scoring", "display", "destination_search"')
    said = walk.fetch("--words")
    stopped(said, 1)
    assert " ok=0 skipped=5 refused=1 " in said.lines[-1]
    assert "is not registered for routing. It is registered for: gazetteer, " in line_of(said, 5)
    assert "Another file of the list was refused by the registry" in line_of(said, 1)
    assert served.seen == []
    assert nothing_is_kept(walk)


def test_plan_finds_the_refusal_before_anything_is_fetched(walk: Walk, served: Served):
    walk.register(uses='"gazetteer", "scoring", "display", "destination_search"')
    said = walk.step("plan", "--list", walk.list, "--registry", walk.registry)
    assert (said.code, said.lines[-1]) == (1, "step=plan status=missing files=6 ready=5")
    assert "step=plan n=5 source=made-up-survey status=refused why=1 seconds=0.0" in said.lines
    assert served.seen == []


# The entry of the registry, which each file is held to before it is asked for

EVERY_FILE_BUT_ONE = (
    "step=fetch status=failed files=6 ok=0 skipped=5 refused=1 failed=0 missing=0 "
    "unreadable=0 differs=0"
)


@pytest.mark.parametrize(
    ("changed", "why"),
    [
        ({"page": "https://made-up.example/another-survey"}, Why.NOT_THE_PAGE),
        ({"url": f"https://elsewhere.made-up.example/files/{MEASURES}"}, Why.NOT_THE_HOST),
        ({"url": f"{PUBLISHER}/another-survey/{MEASURES}"}, Why.NOT_THE_ADDRESS),
        ({"url": f"{PUBLISHER}/files/census2021-ts021-oa.csv"}, Why.RESIDENT_TABLE),
        ({"what": "Made up: TS030, religion, by output area"}, Why.RESIDENT_TABLE),
    ],
    ids=[
        "a page that is not the entry's",
        "a host that is not the entry's",
        "an address that is not the entry's",
        "an address that names a table about residents",
        "a description that names a table about residents",
    ],
)
def test_a_file_that_is_not_as_its_entry_has_it_stops_the_fetch_before_anything_is_asked(
    walk: Walk, served: Served, changed: dict[str, str], why: Why
):
    walk.list.write_text(the_list(walk.files, changed), encoding="utf-8")
    said = walk.fetch("--words")
    stopped(said, 1, EVERY_FILE_BUT_ONE)
    assert f"step=fetch n=6 source=made-up-survey status=refused why={int(why)} " in (
        line_of(said, 6)
    )
    assert said_with_what_to_do(line_of(said, 6), why)
    assert "Nothing was asked for" in line_of(said, 6)
    # No file of the list is fetched, the five that are as the entry has them included.
    assert " status=skipped why=2 " in line_of(said, 1)
    assert served.seen == []
    assert nothing_is_kept(walk)
    # And plan finds it, with no network and no store.
    planned = walk.step("plan", "--list", walk.list, "--registry", walk.registry)
    assert (planned.code, planned.lines[-1]) == (1, "step=plan status=missing files=6 ready=5")
    found = f"step=plan n=6 source=made-up-survey status=refused why={int(why)} seconds=0.0"
    assert found in planned.lines


def answering(pages: dict[str, Answer]) -> Callable[[Any], Answer]:
    """The made-up publisher, with some of its pages answered otherwise."""
    every = {f"/files/{name}": Answer(body=content) for name, content in FILES.items()} | pages
    return lambda request: every.get(request.path, Answer(404))


RESIDENTS = "census2021-ts021-oa.csv"


def sent_on(_: Path) -> dict[str, Answer]:
    return {
        f"/files/{MEASURES}": Answer(302, {"Location": f"/files/{RESIDENTS}"}),
        f"/files/{RESIDENTS}": Answer(body=FILES[MEASURES]),
    }


def named_by_the_publisher(_: Path) -> dict[str, Answer]:
    named = {"Content-Disposition": f'attachment; filename="{RESIDENTS}"'}
    return {f"/files/{MEASURES}": Answer(headers=named, body=FILES[MEASURES])}


def inside_a_zip(folder: Path) -> dict[str, Answer]:
    inside = {"made-up-homes.csv": FILES[HOMES], RESIDENTS: FILES[MEASURES]}
    held = made_up_zip(folder / "made-up.zip", inside).read_bytes()
    return {f"/files/{MEASURES}": Answer(body=held)}


def inside_a_zip_inside_a_zip(folder: Path) -> dict[str, Answer]:
    inner = made_up_zip(folder / "inner.zip", {RESIDENTS: FILES[MEASURES]}).read_bytes()
    held = made_up_zip(folder / "made-up.zip", {"made-up-tables.dat": inner}).read_bytes()
    return {f"/files/{MEASURES}": Answer(body=held)}


def a_zip_that_cannot_be_looked_into(folder: Path) -> dict[str, Answer]:
    inside = {"made-up-homes.csv": FILES[HOMES], "made-up-tables.zip": FILES[MEASURES]}
    held = made_up_zip(folder / "made-up.zip", inside).read_bytes()
    return {f"/files/{MEASURES}": Answer(body=held)}


@pytest.mark.parametrize(
    ("pages", "why"),
    [
        (sent_on, Why.RESIDENT_TABLE),
        (named_by_the_publisher, Why.RESIDENT_TABLE),
        (inside_a_zip, Why.RESIDENT_TABLE),
        (inside_a_zip_inside_a_zip, Why.RESIDENT_TABLE),
        (a_zip_that_cannot_be_looked_into, Why.CANNOT_SEE_INSIDE),
    ],
    ids=[
        "a table about residents, where it was sent on to",
        "a table about residents, by the publisher's name for it",
        "a table about residents inside a zip",
        "a table about residents inside a zip inside a zip",
        "a zip that cannot be looked into",
    ],
)
def test_a_file_that_arrives_as_what_its_entry_may_not_hold_is_not_kept(
    tmp_path: Path, pages: Callable[[Path], dict[str, Answer]], why: Why
):
    """The list says nothing of it. What arrived does, and is held to the entry too."""
    with serving(answering(pages(tmp_path))) as served:
        walk = Walk(tmp_path / "walk", served)
        walk.list.write_text(the_list(walk.files, {"format": "other"}), encoding="utf-8")
        said = walk.fetch("--words")
    assert said.code == 1 and " ok=5 " in said.lines[-1] and " refused=1 " in said.lines[-1]
    assert f"status=refused why={int(why)} " in line_of(said, 6)
    assert said_with_what_to_do(line_of(said, 6), why)
    for hidden in (CANARY, "Traceback", "ts021", "127.0.0.1"):
        assert hidden not in said.everything
    # The five files before it are kept. This one is in no store and has no receipt.
    assert len(FolderStore(walk.store).list()) == 5
    assert len(read_receipts(walk.receipts)) == 5
    # So the build cannot be sealed from the list that names it.
    walk.held()
    words = stopped(walk.seal(), 2, "step=seal status=refused listed_file_has_a_receipt=1")
    assert "measures is a file of the list, and no receipt of it is in the folder" in words


FOR_THE_AUDIT = """
[[source]]
id = "made-up-faiths"
name = "Made-up tables for the audit"
publisher = "Made-up Office"
url = "https://made-up.example/faiths"
dimension = "{heading}"
licence = "OGL-3.0"
commercial_use = "yes"
share_alike = false
attribution = "Contains made-up data."
attribution_verified = true
status = "{status}"
status_reason = "{reason}"
uses = [{uses}]
{tables}verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://made-up.example/faiths-licence"]
file_urls = ["https://files.made-up.example/faiths/"]
"""
A_FILE_OF_IT = """
[[file]]
item = "faiths"
source_id = "made-up-faiths"
use = "{use}"
what = "A made-up table that is kept apart"
format = "csv"
page = "https://made-up.example/faiths"
url = "https://files.made-up.example/faiths/made-up-faiths.csv"
max_bytes = 1000000
edition = "made up"
data_period = {{ as_at = "2021-03-21" }}
"""
KEPT_APART = {
    "for the audit": ("audit", "held", '"audit_only"', "audit_only", ""),
    "under the audit, to look at": (
        "audit",
        "gated",
        '"audit_only", "validation_only"',
        "validation_only",
        "",
    ),
    "the census table about residents": (
        "residents",
        "approved",
        '"census_table"',
        "census_table",
        'tables = ["TS021"]\n',
    ),
}


@pytest.mark.parametrize(
    ("heading", "status", "uses", "use", "tables"), KEPT_APART.values(), ids=list(KEPT_APART)
)
def test_a_file_that_is_kept_apart_stops_the_fetch_because_no_store_is_built_for_it(
    walk: Walk, served: Served, heading: str, status: str, uses: str, use: str, tables: str
):
    reason = "" if status == "approved" else "Made up. It is read for the audit and no more."
    entry = FOR_THE_AUDIT.format(
        heading=heading, status=status, reason=reason, uses=uses, tables=tables
    )
    walk.registry.write_text(walk.registry.read_text(encoding="utf-8") + entry, encoding="utf-8")
    listed = the_list(walk.files) + A_FILE_OF_IT.format(use=use)
    walk.list.write_text(listed, encoding="utf-8")
    # The licence registry itself allows the file, for the use the list gives.
    from burro_pipeline.registry import Use, load

    assert load(walk.registry).require("made-up-faiths", Use(use)).id == "made-up-faiths"
    said = walk.fetch("--words")
    stopped(
        said,
        1,
        "step=fetch status=failed files=7 ok=0 skipped=6 refused=1 failed=0 missing=0 "
        "unreadable=0 differs=0",
    )
    assert "step=fetch n=7 source=made-up-faiths status=refused why=15 " in line_of(said, 7)
    assert int(Why.NOT_THE_STORE) == 15
    assert said_with_what_to_do(line_of(said, 7), Why.NOT_THE_STORE)
    assert "No such store is built" in line_of(said, 7)
    assert served.seen == []
    assert nothing_is_kept(walk)


# The fetch


@pytest.mark.parametrize(
    ("unset", "names"),
    [
        ("BURRO_FETCH_CONTACT", "BURRO_FETCH_CONTACT must be an email address or an https page"),
        ("BURRO_STORE_FOLDER", "no store is named. Set BURRO_STORE_FOLDER for a folder, or all of"),
    ],
)
def test_a_fetch_with_nothing_set_up_says_which_variable_to_set(
    walk: Walk, served: Served, unset: str, names: str
):
    walk.environment.pop(unset)
    said = walk.fetch()
    assert names in stopped(said, 2)
    assert said.lines == [] and served.seen == []


@pytest.mark.parametrize(
    ("answer", "line", "to_do"),
    [
        (
            Answer(body=b"<!DOCTYPE html><html><body>Sign in to download</body></html>"),
            "status=unreadable why=5 ",
            "Open the address in a browser",
        ),
        (Answer(404), "status=failed why=27 http=404 ", "For 404 look at the address in the list"),
        (Answer(403), "status=failed why=27 http=403 ", "save the file by hand"),
        (
            Answer(302, {"Location": "https://cdn.made-up.example/x?sig=1"}),
            "status=failed why=28 ",
            "Name that host in the list under may_redirect_to",
        ),
        (Answer(body=FILES[MEASURES], cut_short_at=100), "status=failed why=31 ", "Try again"),
    ],
    ids=["a sign-in page", "not found", "refused", "sent elsewhere", "cut short"],
)
def test_a_publisher_that_does_not_give_the_file_is_said_with_what_to_do(
    tmp_path: Path, answer: Answer, line: str, to_do: str
):
    pages = {f"/files/{name}": Answer(body=content) for name, content in FILES.items()}
    pages[f"/files/{MEASURES}"] = answer
    with serving(lambda request: pages.get(request.path, Answer(404))) as served:
        walk = Walk(tmp_path, served)
        said = walk.fetch("--words")
    assert said.code == 1 and " ok=5 " in said.lines[-1]
    assert line in line_of(said, 6) and to_do in line_of(said, 6)
    # The name of another host is said to the person, and the file's own address never is.
    assert "files.made-up.example" not in said.everything and CANARY not in said.everything
    assert [held.name for held in FolderStore(walk.store).list()].count(MEASURES) == 0
    assert MEASURES not in [receipt.publisher_file for receipt in read_receipts(walk.receipts)]


def test_a_file_over_the_size_the_list_states_is_not_kept(walk: Walk):
    walk.list.write_text(the_list(walk.files, {"max_bytes": 10}), encoding="utf-8")
    said = walk.fetch("--words")
    assert said.code == 1
    assert "status=failed why=30 " in line_of(said, 6)
    assert "If it is the right file, raise max_bytes in the list" in line_of(said, 6)
    assert len(FolderStore(walk.store).list()) == 5


def test_a_fault_in_one_file_fails_that_file_and_the_run_goes_on_to_the_next(
    walk: Walk, served: Served
):
    gives = as_the_publisher(served)

    def faulty(
        address: str,
        to: Path,
        limits: Limits,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
    ) -> Downloaded:
        """A fault of fetch's own, for one file of the list and no other."""
        if address.endswith(f"/{HOMES}"):
            raise RuntimeError(f"{CANARY} at {address}")
        return gives(address, to, limits, agent=agent, may_redirect_to=may_redirect_to)

    words = ["fetch", *(str(word) for word in walk.kept()), "--words"]
    said = walk.run(lambda: fetch_cli.main(words, walk.environment, faulty))
    stopped(
        said,
        1,
        "step=fetch status=failed files=6 ok=5 skipped=0 refused=0 failed=1 missing=0 "
        "unreadable=0 differs=0",
    )
    at = next(n for n, line in enumerate(said.lines) if " status=failed " in line)
    assert " source=made-up-survey status=failed why=17 " in said.lines[at]
    assert int(Why.FAULT) == 17
    # Only the kind of the fault is said, and what to do to see the rest.
    assert "(RuntimeError)" in said.lines[at + 1]
    assert "BURRO_FETCH_DEBUG=1" in said.lines[at + 1]
    assert said.words == ""
    # The file after it in the list was fetched all the same.
    assert [line for line in said.lines[at + 2 :] if " status=ok " in line]
    assert len(FolderStore(walk.store).list()) == 5
    assert HOMES not in [receipt.publisher_file for receipt in read_receipts(walk.receipts)]
    # And the build is not sealed without it.
    walk.held()
    stopped(walk.seal(), 2, "step=seal status=refused listed_file_has_a_receipt=1")
    assert not walk.locks.exists()


# The receipt


def test_a_file_whose_edition_nobody_is_sure_of_is_stored_and_has_no_receipt(walk: Walk):
    walk.list.write_text(the_list(walk.files, {"unsure": ["edition"]}), encoding="utf-8")
    said = walk.fetch("--words")
    assert said.code == 1 and " ok=5 " in said.lines[-1] and " missing=1 " in said.lines[-1]
    assert "status=missing file_id=f-" in line_of(said, 6) and " why=6 " in line_of(said, 6)
    assert "State both in the list and fetch again" in line_of(said, 6)
    assert len(FolderStore(walk.store).list()) == 6
    assert len(read_receipts(walk.receipts)) == 5


def test_a_second_run_writes_the_receipt_once_a_person_has_stated_both(walk: Walk, served: Served):
    """The first run stores a file that nobody has read, and gives it no receipt."""
    unread = {"unsure": ["edition", "data_period"]}
    walk.list.write_text(the_list(walk.files, unread), encoding="utf-8")
    first = walk.fetch()
    assert first.code == 1 and " ok=5 " in first.lines[-1] and " missing=1 " in first.lines[-1]
    held = {kept.name: kept.sha256 for kept in FolderStore(walk.store).list()}
    assert MEASURES in held and len(read_receipts(walk.receipts)) == 5
    assert FolderStore(walk.store).receipts().keys() == {
        receipt.kept_key() for receipt in read_receipts(walk.receipts)
    }
    # Nothing can be sealed on it, and so nothing can be cited to it.
    walk.held()
    stopped(walk.seal(), 2, "step=seal status=refused listed_file_has_a_receipt=1")
    # A person reads the file, and states its edition and its period in the list.
    read = {"edition": "made up, as the file says", "data_period": {"as_at": "2025-03"}}
    walk.list.write_text(the_list(walk.files, read), encoding="utf-8")
    second = walk.fetch()
    assert second.code == 0 and second.lines[-1].startswith("step=fetch status=ok files=6 ok=6 ")
    assert " new=0 " in line_of(second, 6).splitlines()[0]
    receipt = walk.receipt(MEASURES)
    assert (receipt.sha256, receipt.edition) == (held[MEASURES], "made up, as the file says")
    assert receipt.data_period.as_at == "2025-03"
    assert FolderStore(walk.store).receipts()[receipt.kept_key()] == receipt.canonical()
    assert (walk.held().code, walk.seal().code) == (0, 0)
    assert walk.lock().holds(receipt.file_id)


def as_a_new_runner_finds_it(walk: Walk) -> None:
    """A hosted run starts on a new disk: the store is as it was, and the folder is empty."""
    shutil.rmtree(walk.receipts)


PUT_RIGHT = {"edition": "made up, second edition"}


def test_a_receipt_in_the_store_that_differs_from_the_list_ends_the_run_red(walk: Walk):
    """The list was put right after the first run. The first receipt stands, in the store."""
    assert walk.fetch().code == 0
    first = walk.receipt(MEASURES)
    kept = FolderStore(walk.store).receipts()
    as_a_new_runner_finds_it(walk)
    walk.list.write_text(the_list(walk.files, PUT_RIGHT), encoding="utf-8")
    said = walk.fetch("--words")
    stopped(
        said,
        1,
        "step=fetch status=failed files=6 ok=5 skipped=0 refused=0 failed=0 missing=0 "
        "unreadable=0 differs=1",
    )
    assert f" status=differs file_id={first.file_id} " in line_of(said, 6)
    assert " new=0 why=16 " in line_of(said, 6)
    assert int(Why.KEPT_RECEIPT_DIFFERS) == 16
    assert said_with_what_to_do(line_of(said, 6), Why.KEPT_RECEIPT_DIFFERS)
    # Nothing was written over, and the run did not say ok of a receipt it dropped.
    assert FolderStore(walk.store).receipts() == kept
    assert MEASURES not in [receipt.publisher_file for receipt in read_receipts(walk.receipts)]
    # Brought back, the first receipt is not the receipt of the file the list names now.
    walk.with_the_store("receipts", "--receipts", walk.receipts)
    assert walk.receipt(MEASURES) == first
    walk.held()
    words = stopped(walk.seal(), 2, "step=seal status=refused listed_file_has_a_receipt=1")
    assert "measures is a file of the list, and no receipt of it is in the folder" in words
    assert not walk.locks.exists()


def test_a_receipt_that_is_wrong_is_put_right_by_a_person_and_by_no_run(walk: Walk):
    """As the guide has it: set aside in the repository and at the store, then fetched again."""
    assert walk.fetch().code == 0
    wrong = walk.receipt(MEASURES)
    walk.list.write_text(the_list(walk.files, PUT_RIGHT), encoding="utf-8")
    # No run puts it right, on the disk that fetched or on a new one.
    assert " status=differs " in line_of(walk.fetch(), 6)
    assert walk.receipt(MEASURES) == wrong
    # A person takes the receipt out of the folder, and its copy out of the store.
    (walk.root / wrong.path()).unlink()
    (walk.store / wrong.kept_key()).unlink()
    said = walk.fetch()
    assert said.code == 0, said.everything
    right = walk.receipt(MEASURES)
    assert (right.file_id, right.sha256) == (wrong.file_id, wrong.sha256)
    assert (wrong.edition, right.edition) == ("made up", "made up, second edition")
    assert FolderStore(walk.store).receipts()[right.kept_key()] == right.canonical()
    # The file itself was never touched: it is the one that was stored first.
    assert " new=0 " in line_of(said, 6)
    assert (walk.held().code, walk.seal().code) == (0, 0)
    assert walk.lock().holds(right.file_id)


def test_a_receipt_put_right_in_the_folder_alone_is_found_when_receipts_are_brought_back(
    walk: Walk,
):
    """The copy in the store was forgotten. Neither is written over, and the step says so."""
    assert walk.fetch().code == 0
    wrong = walk.receipt(MEASURES)
    right = wrong.model_copy(update=PUT_RIGHT)
    (walk.root / wrong.path()).write_bytes(right.canonical())
    said = walk.with_the_store("receipts", "--receipts", walk.receipts)
    assert said.code == 1
    assert said.lines[-1] == (
        "step=store status=differs receipts=6 new=0 same=5 differs=1 unreadable=0"
    )
    assert "Both were left as they are" in said.words and CANARY not in said.everything
    assert walk.receipt(MEASURES) == right
    assert FolderStore(walk.store).receipts()[wrong.kept_key()] == wrong.canonical()


@pytest.mark.parametrize(
    ("change", "said_of_it"),
    [
        ({"note": CANARY}, "holds a field that a record does not have"),
        ({"sha256": "0" * 64}, "file_id is not the first twelve digits of sha256"),
        ({"url": "http://made-up.example/files/x.csv"}, "url is an https address"),
        ({"retrieved_at": "yesterday"}, "retrieved_at"),
    ],
    ids=["a field added", "the hash", "the address", "the time"],
)
def test_a_receipt_edited_by_hand_stops_the_lock(
    walk: Walk, change: dict[str, str], said_of_it: str
):
    walk.fetch()
    walk.held()
    path = walk.root / walk.receipt(MEASURES).path()
    path.write_text(json.dumps(json.loads(path.read_text()) | change), encoding="utf-8")
    words = stopped(walk.seal(), 2, "step=seal status=refused receipt_is_valid=1")
    assert f"{path.name} is not a valid receipt" in words and said_of_it in words
    assert "A receipt is written by fetch and is never edited" in words
    assert words.count("\n") == 1 and words.endswith("[receipt_is_valid]\n")
    assert not walk.locks.exists()


def test_receipts_lost_with_the_machine_that_fetched_are_brought_back_and_sealed(walk: Walk):
    """What a hosted run leaves: the files and their receipts in the store, and no disk."""
    walk.fetch()
    before = read_receipts(walk.receipts)
    shutil.rmtree(walk.root / "data")
    words = stopped(walk.seal(), 2, "step=seal status=unreadable")
    assert "there is no listing" in words
    said = walk.with_the_store("receipts", "--receipts", walk.receipts)
    assert said.lines == [
        "step=store kind=folder",
        "step=store status=ok receipts=6 new=6 same=0 differs=0 unreadable=0",
    ]
    assert read_receipts(walk.receipts) == before
    walk.listing.unlink(missing_ok=True)
    assert (walk.held().code, walk.seal().code) == (0, 0)
    assert len(walk.lock().inputs) == 6


# The store, between the fetch and the lock


def test_a_file_gone_from_the_store_stops_the_lock_and_is_named_by_its_id(walk: Walk):
    walk.fetch()
    receipt = walk.receipt(MEASURES)
    (walk.store / receipt.vault_key()).unlink()
    walk.held()
    said = walk.seal()
    line = f"step=seal status=refused file_is_in_the_vault=1 file_id={receipt.file_id}"
    words = stopped(said, 2, line)
    assert f"{receipt.file_id} is not in the vault, or is not the size its receipt gives" in words
    assert "Make the listing again with" in words and "fetch the file again" in words
    assert not walk.locks.exists()


def test_a_lock_is_not_sealed_without_a_listing_of_the_store(walk: Walk):
    walk.fetch()
    words = stopped(walk.seal(), 2, "step=seal status=unreadable")
    assert "there is no listing at listing.json" in words
    assert "python -m burro_pipeline held --out" in words
    assert not walk.locks.exists()


# The gate, again, when the lock is sealed


def test_a_source_that_lost_its_approval_after_the_fetch_stops_the_lock(walk: Walk):
    walk.fetch()
    walk.held()
    walk.register(*GATED)
    said = walk.seal()
    words = stopped(said, 2)
    assert said.lines[0].startswith("step=seal status=refused gate_refuses=1 file_id=f-")
    assert "is gated, not approved: Its made-up terms changed on 1 October." in words
    assert "The registry entry says what would change this" in words
    assert not walk.locks.exists()


def test_every_refusal_of_the_lock_says_what_a_person_can_do_about_it():
    from burro_pipeline.evidence import cli, lock

    assert set(cli.TO_DO) == set(lock.MEANING)
    for rule, to_do in cli.TO_DO.items():
        said = cli.in_full(LockError(rule, "f-0123456789ab", "made up."))
        assert said == f"f-0123456789ab {lock.MEANING[rule]}: made up. {to_do} [{rule}]"
        assert to_do[0].isupper() and not to_do.endswith(".")


# The lock, when a step takes a file


def test_a_file_changed_in_the_store_after_the_lock_is_never_handed_to_a_step(walk: Walk):
    walk.to_the_lock()
    kept = walk.store / walk.receipt(MEASURES).vault_key()
    kept.write_bytes(kept.read_bytes() + b"U9,made up,1\n")
    with pytest.raises(StoreError) as refused:
        walk.derive()
    assert "does not match its hash, so it was not used" in str(refused.value)
    assert "look at it by hand" in str(refused.value)
    assert not (walk.root / "taken" / MEASURES).exists()


def test_a_file_the_lock_does_not_name_is_refused_by_name_and_rule(walk: Walk):
    walk.to_the_lock()
    other = walk.root / "another.csv"
    other.write_bytes(b"unit_code,unit_name,flats\nU9,made up,1\n")
    with pytest.raises(LockError) as refused:
        walk.lock().admit_file(other)
    assert str(refused.value) == (
        "another.csv is not an input of this build: its hash is not in the lock [input_is_locked]"
    )


def test_a_file_fetched_after_the_lock_was_sealed_is_not_an_input_of_the_build(walk: Walk):
    # A build of one file, and then a longer list with a second file on it.
    others = [name for name in walk.files if name != HOMES]
    walk.list.write_text(the_list(walk.files, without=others), encoding="utf-8")
    walk.fetch()
    walk.held()
    assert walk.seal().code == 0
    walk.list.write_text(the_list(walk.files), encoding="utf-8")
    walk.fetch("--only", "measures")
    with pytest.raises(LockError, match="input_is_locked"):
        walk.taken(MEASURES)


def test_a_file_of_the_list_that_was_not_fetched_stops_the_lock(walk: Walk):
    walk.fetch("--only", "homes")
    walk.held()
    said = walk.seal()
    words = stopped(said, 2, "step=seal status=refused listed_file_has_a_receipt=1")
    assert " is a file of the list, and no receipt of it is in the folder" in words
    assert "Fetch the file, or bring its receipt back" in words
    assert not walk.locks.exists()


def test_a_receipt_of_a_file_the_list_does_not_name_stops_the_lock(walk: Walk):
    walk.fetch()
    walk.held()
    walk.list.write_text(the_list(walk.files, without=[HOMES]), encoding="utf-8")
    said = walk.seal()
    line = f"step=seal status=refused receipt_is_listed=1 file_id={walk.receipt(HOMES).file_id}"
    words = stopped(said, 2, line)
    assert "move its receipt out of the folder" in words
    assert not walk.locks.exists()


# The evidence


def without_the_row(walk: Walk) -> Evidence:
    whole = evidence_of(read_receipts(walk.receipts), walk.derive())
    rows = [row for row in whole.rows if row.fact_id != FACT]
    return Evidence.of(whole.release_id, whole.receipts, whole.methods, rows)


def test_a_figure_with_no_row_of_evidence_fails_the_check_and_is_written_down(walk: Walk):
    walk.to_the_lock()
    walk.evidence.write_bytes(without_the_row(walk).canonical())
    said = walk.check()
    assert said.code == 1 and said.words == ""
    assert f"step=check status=failed release={RELEASE_ID} facts=1669 rows=1776 " in said.lines[0]
    assert said.lines[0].endswith(" fact_has_a_row=1")
    assert FACT not in said.everything
    assert walk.findings.read_text(encoding="utf-8") == (
        f"{FACT} is served, and no row of evidence stands behind it [fact_has_a_row]\n"
    )


def test_a_check_that_fails_with_nowhere_to_write_says_how_to_see_what_it_found(walk: Walk):
    walk.to_the_lock()
    walk.evidence.write_bytes(without_the_row(walk).canonical())
    said = walk.step(
        *("check", walk.folder_of_the_release(), "--evidence", walk.evidence),
        *("--lock", walk.locks / f"{RELEASE_ID}.json", "--registry", walk.registry),
        *("--hashes", walk.write_hashes()),
    )
    words = stopped(said, 1)
    assert "1 fact may not be served" in words and "--list FILE" in words
    assert FACT not in said.everything


def test_a_row_that_rests_on_a_file_the_lock_does_not_name_fails_the_check(walk: Walk):
    walk.to_the_end()
    # The build is sealed again from a list that leaves the homes out.
    (walk.root / walk.receipt(HOMES).path()).unlink()
    walk.list.write_text(the_list(walk.files, without=[HOMES]), encoding="utf-8")
    assert walk.seal().code == 0
    said = walk.check()
    assert said.code == 1
    assert " input_is_locked=" in said.lines[0]
    found = walk.findings.read_text(encoding="utf-8").splitlines()
    assert f"{FACT} rests on a file that is not in the lock [input_is_locked]" in found


# The gate, again, when a figure is served

NOT_FOR_SCORING = """
[[source]]
id = "made-up-prices"
name = "Made-up prices"
publisher = "Made-up Office"
url = "https://made-up.example/prices"
dimension = "{heading}"
licence = "{licence}"
commercial_use = "yes"
share_alike = {share_alike}
attribution = "Contains made-up data."
attribution_verified = true
status = "{status}"
status_reason = "{reason}"
uses = [{uses}]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://made-up.example/prices-licence"]
file_urls = ["https://files.made-up.example/prices/"]
"""
# What the registry may say of a source whose file the gate lets fetch keep in the
# product's store, and the use the list asks for. None is allowed for scoring.
READ_FOR_LESS = {
    "gated, and read to validate against": (
        ("housing", "OGL-3.0", "false", "gated", "Made up. Its terms are not read."),
        '"validation_only"',
        "validation_only",
    ),
    "held, and read for a prototype": (
        ("housing", "OGL-3.0", "false", "held", "Made up. It is not used in this version."),
        '"prototyping_only"',
        "prototyping_only",
    ),
    "share-alike, and approved for routing and the basemap alone": (
        ("transport", "ODbL-1.0", "true", "approved", ""),
        '"routing", "basemap"',
        "routing",
    ),
}


@pytest.mark.parametrize(("entry", "uses", "use"), READ_FOR_LESS.values(), ids=list(READ_FOR_LESS))
def test_a_figure_that_rests_on_a_file_the_registry_does_not_allow_for_it_fails_the_check(
    tmp_path: Path, entry: tuple[str, str, str, str, str], uses: str, use: str
):
    """The file is fetched, kept and sealed, as the gate allows. No figure may rest on it."""
    heading, licence, share_alike, status, reason = entry
    pages = {f"/prices/{MEASURES}": Answer(body=FILES[MEASURES])}
    with serving(answering(pages)) as served:
        walk = Walk(tmp_path / "walk", served)
        registered = NOT_FOR_SCORING.format(
            heading=heading,
            licence=licence,
            share_alike=share_alike,
            status=status,
            reason=reason,
            uses=uses,
        )
        walk.registry.write_text(
            walk.registry.read_text(encoding="utf-8") + registered, encoding="utf-8"
        )
        under_it = {
            "source_id": "made-up-prices",
            "use": use,
            "page": "https://made-up.example/prices",
            "url": f"{PUBLISHER}/prices/{MEASURES}",
        }
        walk.list.write_text(the_list(walk.files, under_it), encoding="utf-8")
        walk.to_the_lock()
        assert walk.receipt(MEASURES).source_id == "made-up-prices"
        assert str(walk.receipt(MEASURES).use) == use
        walk.write_evidence(walk.derive())
        said = walk.check()
    # The release cites the approved source alone, and the file of it stands behind the row.
    assert said.code == 1, said.everything
    assert f"step=check status=failed release={RELEASE_ID} facts=1669 " in said.lines[0]
    # The rows of 43 measures and 11 vibes, in each of 24 areas.
    assert " findings=1296 " in said.lines[0]
    assert said.lines[0].endswith(" input_is_allowed=1296")
    found = walk.findings.read_text(encoding="utf-8").splitlines()
    assert len(found) == 1296
    assert (
        f"{FACT} rests on a file that the licence registry does not allow for what this "
        "figure is used for, or that was fetched for an internal use, or is a file of the "
        "release that cites a source the registry does not allow for it [input_is_allowed]"
    ) in found
    for hidden in (CANARY, "Traceback", "made-up.example", "127.0.0.1", "made-up-prices"):
        assert hidden not in said.everything


def test_a_file_read_to_validate_against_may_be_sealed_with_no_row_resting_on_it(tmp_path: Path):
    pages = {"/prices/made-up-prices.csv": Answer(body=b"code,price\nmade-up-1,10\n")}
    with serving(answering(pages)) as served:
        walk = Walk(tmp_path / "walk", served)
        entry = NOT_FOR_SCORING.format(
            heading="housing",
            licence="OGL-3.0",
            share_alike="false",
            status="gated",
            reason="Made up. Its terms are not read.",
            uses='"validation_only"',
        )
        walk.registry.write_text(
            walk.registry.read_text(encoding="utf-8") + entry, encoding="utf-8"
        )
        beside = """
[[file]]
item = "prices"
source_id = "made-up-prices"
use = "validation_only"
what = "A made-up file to validate against"
format = "csv"
page = "https://made-up.example/prices"
url = "https://files.made-up.example/prices/made-up-prices.csv"
max_bytes = 1000000
edition = "made up"
data_period = { as_at = "2026-09" }
"""
        walk.list.write_text(the_list(walk.files) + beside, encoding="utf-8")
        walk.to_the_lock()
        assert len(walk.lock().inputs) == 7
        # The evidence holds the receipts of the files a row rests on, and those alone.
        behind = [r for r in read_receipts(walk.receipts) if r.source_id != "made-up-prices"]
        walk.evidence.write_bytes(evidence_of(behind, walk.derive()).canonical())
        said = walk.check()
    assert said.code == 0, said.everything
    assert " status=ok " in said.lines[0] and " findings=0 " in said.lines[0]


def names_a_file_nobody_fetched(document: dict[str, Any]) -> None:
    document["rows"][0]["inputs"] = ["f-000000000000"]


def loses_a_receipt(document: dict[str, Any]) -> None:
    document["receipts"].pop()


def loses_a_method(document: dict[str, Any]) -> None:
    document["methods"].pop()


def gains_a_field(document: dict[str, Any]) -> None:
    document["note"] = CANARY


@pytest.mark.parametrize(
    ("damage", "said_of_it"),
    [
        (names_a_file_nobody_fetched, "no receipt"),
        (loses_a_receipt, "no receipt"),
        (loses_a_method, "a method the evidence does not hold"),
        (gains_a_field, "a field that a record does not have"),
    ],
)
def test_evidence_with_a_loose_end_is_refused_whole(
    walk: Walk, damage: Callable[[dict[str, Any]], object], said_of_it: str
):
    walk.to_the_lock()
    document = json.loads(evidence_of(read_receipts(walk.receipts), walk.derive()).canonical())
    damage(document)
    walk.evidence.write_text(json.dumps(document), encoding="utf-8")
    words = stopped(walk.check(), 2, "step=check status=unreadable")
    assert "evidence.json is not valid evidence" in words and said_of_it in words
    assert words.count("\n") == 1


# The coverage


def test_a_figure_with_no_record_is_counted_in_the_report_and_not_filled_in(walk: Walk):
    walk.to_the_lock()
    walk.evidence.write_bytes(without_the_row(walk).canonical())
    said = walk.coverage()
    assert said.code == 0 and " no_record=1 " in said.lines[0]
    report = walk.report.read_text(encoding="utf-8")
    assert "| Pairs with no record behind them | 1 |" in report
    assert "| feature/homes_flats | 21 | 1 | 2 | 0 | 0 | 0 | 0 | 1 |" in report
