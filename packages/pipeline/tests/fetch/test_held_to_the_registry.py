"""A file of a list is held to the registry entry of its source, and not to its id alone.

The registry answers for an id and a use. A list states both, beside a page
and an address. If nothing held the page and the address to the entry, any
file could be fetched under any approved id: a census table about residents
under the entry for housing, with a receipt that says `scoring`.

So a file's page is one the entry holds, its address is one the entry names
for its files, and nothing that says what the file is may name a census table
about residents, before the file is asked for or after it has arrived. The
tests of the address itself are in `test_an_address_is_of_one_entry.py`. Every
file here is made up. The publisher is a stand-in on the loopback address.
"""

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from burro_pipeline.evidence import read_receipts
from burro_pipeline.fetch.by_hand import keep_by_hand
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded, Limits, download, user_agent
from burro_pipeline.fetch.gate import Reason, Refused, ask, hold_what_arrived
from burro_pipeline.fetch.run import WORDS, Outcome, Status, Why, fetch
from burro_pipeline.fetch.sources import Listed, load_list
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Registry, load

from .support import (
    MADE_UP_REGISTRY,
    ONLY_LOOPBACK,
    Answer,
    Seen,
    Served,
    made_up_zip,
    serving,
)

pytestmark = ONLY_LOOPBACK

REPOSITORY = Path(__file__).parents[4]
BODY = b"code,homes\nmade-up-1,10\nmade-up-2,20\n"
NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
AGENT = user_agent("data@made-up.example")
PUBLISHER = "https://files.made-up.example"
# The entry for housing in the repository's own registry, and the page it holds.
HOUSING = "ons-census-2021-housing-tables"
HOUSING_PAGE = "https://www.nomisweb.co.uk/datasets/c2021ts044"


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


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes by made-up area",
        "format": "csv",
        "page": "https://made-up.example/homes",
        "url": f"{PUBLISHER}/files/homes.csv",
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


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
        assert address.startswith(PUBLISHER)
        got = download(
            address.replace(PUBLISHER, served.address, 1),
            to,
            limits,
            agent=agent,
            may_redirect_to=may_redirect_to,
            loopback_for_tests=True,
        )
        parts = urlsplit(got.final_url)
        query = f"?{parts.query}" if parts.query else ""
        return replace(got, final_url=f"{PUBLISHER}{parts.path}{query}")

    return downloader


def refused(file: Listed, registry: Registry) -> Refused:
    with pytest.raises(Refused) as caught:
        ask(file, registry)
    return caught.value


# What the gate is asked


def test_a_file_that_is_as_its_entry_has_it_passes_and_the_entry_is_given(registry: Registry):
    assert ask(listed(), registry).id == "made-up-homes"
    assert ask(listed(page="https://made-up.example/notes", url=""), registry).id == "made-up-homes"


def test_the_gate_is_still_the_first_thing_asked(registry: Registry):
    file = listed(source_id="made-up-ratings", page="https://elsewhere.example/ratings")
    found = refused(file, registry)
    assert found.reason is Reason.GATE
    assert "is banned" in found.detail


@pytest.mark.parametrize(
    "page",
    [
        "https://made-up.example/rail",
        "https://made-up.example/homes/",
        "https://made-up.example/homes?table=all",
        "https://elsewhere.example/homes",
        "https://www.nomisweb.co.uk/datasets/c2021ts021",
    ],
)
def test_a_page_that_the_entry_does_not_hold_is_refused(registry: Registry, page: str):
    found = refused(listed(page=page), registry)
    assert found.reason is Reason.NOT_THE_PAGE
    assert "example" not in str(found) and "nomisweb" not in str(found)


@pytest.mark.parametrize(
    "address",
    [
        "https://elsewhere.example/files/homes.csv",
        "https://files.made-up.example.elsewhere.example/files/homes.csv",
        "https://more.files.made-up.example/files/homes.csv",
        "https://example/files/homes.csv",
        # The host of the licence is no host of the entry's files.
        "https://licence.made-up.example/files/homes.csv",
    ],
)
def test_an_address_on_a_host_the_entry_does_not_name_is_refused(registry: Registry, address: str):
    found = refused(listed(url=address), registry)
    assert found.reason is Reason.NOT_THE_HOST
    assert "example" not in str(found)


def test_a_host_is_the_same_host_however_it_is_written(registry: Registry):
    for address in (
        "https://FILES.made-up.example/files/homes.csv",
        "https://files.made-up.example:443/files/homes.csv",
        "https://files.made-up.example./files/homes.csv",
    ):
        assert ask(listed(url=address), registry).id == "made-up-homes"


@pytest.mark.parametrize(
    "changed",
    [
        {"item": "census-ts021"},
        {"what": "Census 2021 table TS021, ethnic group, by output area"},
        {"what": "Census 2021 table ts007a"},
        {"edition": "Census 2021 TS030"},
        {"url": f"{PUBLISHER}/output/census/2021/census2021-ts021.zip"},
        {"url": f"{PUBLISHER}/datasets/c2021ts004"},
        {"url": f"{PUBLISHER}/bulk?table=TS003", "url_parameters": ["table"]},
        # Written so that a reader of the list would not see it, and the publisher would.
        {"url": f"{PUBLISHER}/output/census2021-t%73021.zip"},
        {"url": f"{PUBLISHER}/output/census2021-%74%73%30%32%31.zip"},
        {"url": f"{PUBLISHER}/output/census2021-%2574s021.zip"},
        # A table nobody has thought about is taken to be about residents.
        {"what": "Census 2021 table TS077, sexual orientation"},
        # A sign inside the code.
        {"what": "Census 2021 table TS 021 ethnic group"},
        {"what": "Census 2021 table TS-021 ethnic group"},
        {"what": "Census 2021 table TS_021 ethnic group"},
        {"what": "Census 2021 table TS.021 ethnic group"},
        {"what": "Census 2021 table TS/021 ethnic group"},
        {"what": "Census 2021 table TS:021 ethnic group"},
        {"what": "Census 2021 table T S021 ethnic group"},
        {"what": "Census 2021 table TS0 21 ethnic group"},
        {"item": "census-ts-021"},
        {"item": "t-s021"},
        {"url": f"{PUBLISHER}/files/census2021-ts-021.csv"},
        {"url": f"{PUBLISHER}/files/census2021-ts_021.csv"},
        {"url": f"{PUBLISHER}/files/census2021-ts.021.csv"},
        {"url": f"{PUBLISHER}/files/census2021-ts%20021.csv"},
        {"url": f"{PUBLISHER}/files/census2021-ts+021.csv"},
        {"url": f"{PUBLISHER}/files/ts/021.csv"},
        # A code joined to a word, and a code with letters after it.
        {"what": "file censusTS021"},
        {"what": "file tableTS021"},
        {"what": "file xTS021"},
        {"what": "file TS021EW"},
        {"what": "file TS021oa"},
        {"what": "file ts021ab"},
        {"url": f"{PUBLISHER}/files/censusts021.zip"},
        {"url": f"{PUBLISHER}/files/bulkTS021.csv"},
        {"url": f"{PUBLISHER}/files/ats021.csv"},
        {"url": f"{PUBLISHER}/files/ts021oa.csv"},
    ],
    ids=lambda changed: next(iter(changed.values()))[-28:],
)
def test_a_file_that_names_a_census_table_about_residents_is_refused(
    registry: Registry, changed: dict[str, str]
):
    found = refused(listed(**changed), registry)
    assert found.reason is Reason.RESIDENT_TABLE
    assert "example" not in str(found) and "21" not in str(found)


@pytest.mark.parametrize(
    "changed",
    [
        {"item": "census-ts044"},
        {"what": "Census 2021 table TS044, accommodation type: households by output area"},
        {"edition": "Census 2021 TS050"},
        {"url": f"{PUBLISHER}/output/census/2021/census2021-ts054.zip"},
        # No table's code: a fourth digit after it. A code has three, and a year has four.
        {"what": "Made-up hits0215, results 2021 and rents-2025"},
    ],
    ids=lambda changed: next(iter(changed.values()))[-28:],
)
def test_a_housing_table_is_no_table_about_residents(registry: Registry, changed: dict[str, str]):
    assert ask(listed(**changed), registry).id == "made-up-homes"


def test_it_is_the_registrys_own_rule_that_says_what_a_table_about_residents_is():
    """Fetch holds no list of tables and no pattern of its own."""
    import ast

    import burro_pipeline.fetch as package

    for path in sorted(Path(package.__file__).parent.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        written = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        docstrings = {
            ast.get_docstring(node, clean=False)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        }
        for text in written:
            if text in docstrings:
                continue
            assert "ts[0-9]" not in text.lower() and "TS0" not in text, path.name


# The list of the first build, and what the reviewer fetched


def test_every_file_of_the_first_build_is_as_its_registry_entry_has_it():
    registry = load(REPOSITORY / "registry" / "sources")
    for file in load_list("m1").files:
        assert ask(file, registry).id == file.source_id, file.item


def test_a_census_table_about_residents_is_not_fetched_under_the_entry_for_housing(
    store: FolderStore, receipts: Path
):
    """What the reviewer did. The address is made up, on the host the entry names."""
    registry = load(REPOSITORY / "registry" / "sources")
    file = listed(
        item="ethnic-group",
        source_id=HOUSING,
        what="Households by output area",
        page=HOUSING_PAGE,
        url="https://www.nomisweb.co.uk/output/census/2021/census2021-ts021.zip",
        format="zip",
    )
    (outcome,) = fetch([file], registry, store, receipts, agent=AGENT, downloader=never)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.RESIDENT_TABLE)
    assert store.list() == [] and not receipts.exists()


# A run of fetch


def run(
    files: list[Listed], registry: Registry, store: FolderStore, receipts: Path, served: Served
) -> list[Outcome]:
    return fetch(
        files, registry, store, receipts, agent=AGENT, now=lambda: NOW, downloader=through(served)
    )


class Publisher:
    def __init__(self) -> None:
        self.pages: dict[str, Answer] = {"/files/homes.csv": Answer(body=BODY)}

    def __call__(self, request: Seen) -> Answer:
        return self.pages.get(request.path, Answer(404, body=b"not here"))


@pytest.fixture
def publisher() -> Publisher:
    return Publisher()


@pytest.fixture
def served(publisher: Publisher) -> Iterator[Served]:
    with serving(publisher) as server:
        yield server


@pytest.mark.parametrize(
    ("changed", "why"),
    [
        ({"page": "https://made-up.example/rail"}, Why.NOT_THE_PAGE),
        ({"url": "https://elsewhere.example/files/homes.csv"}, Why.NOT_THE_HOST),
        ({"what": "Census 2021 table TS021"}, Why.RESIDENT_TABLE),
    ],
)
def test_one_file_that_is_not_as_its_entry_has_it_stops_every_download(
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    changed: dict[str, str],
    why: Why,
):
    files = [listed(), listed(item="another", **changed)]
    first, second = run(files, registry, store, receipts, served)
    assert (first.status, first.why) == (Status.SKIPPED, Why.ANOTHER_WAS_REFUSED)
    assert (second.status, second.why) == (Status.REFUSED, why)
    assert f" status=refused why={int(why)} " in second.line()
    assert served.seen == []
    assert store.list() == [] and not receipts.exists()


def test_a_redirect_to_a_census_table_about_residents_is_not_kept(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    publisher.pages["/files/latest"] = Answer(302, {"Location": "/files/census2021-ts021-oa.csv"})
    publisher.pages["/files/census2021-ts021-oa.csv"] = Answer(body=BODY)
    files = [listed(url=f"{PUBLISHER}/files/latest"), listed(item="another")]
    first, second = run(files, registry, store, receipts, served)
    assert (first.status, first.why) == (Status.REFUSED, Why.RESIDENT_TABLE)
    assert first.held is None
    # It is found in the middle of a run, so the run goes on to the next file.
    assert second.status is Status.OK
    assert [held.name for held in store.list()] == ["homes.csv"]
    assert len(read_receipts(receipts)) == 1


def test_a_file_the_publisher_names_as_a_census_table_about_residents_is_not_kept(
    publisher: Publisher, served: Served, registry: Registry, store: FolderStore, receipts: Path
):
    named = {"Content-Disposition": 'attachment; filename="census2021-ts021.csv"'}
    publisher.pages["/files/homes.csv"] = Answer(headers=named, body=BODY)
    (outcome,) = run([listed()], registry, store, receipts, served)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.RESIDENT_TABLE)
    assert store.list() == [] and not receipts.exists()


def test_a_zip_that_holds_a_census_table_about_residents_is_not_kept(
    publisher: Publisher,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
):
    inside = {"census2021-ts044-oa.csv": BODY, "census2021-ts021-oa.csv": BODY}
    publisher.pages["/files/homes.zip"] = Answer(
        body=made_up_zip(tmp_path / "made-up.zip", inside).read_bytes()
    )
    file = listed(url=f"{PUBLISHER}/files/homes.zip", format="zip")
    (outcome,) = run([file], registry, store, receipts, served)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.RESIDENT_TABLE)
    assert store.list() == [] and not receipts.exists()


def test_a_zip_of_housing_tables_is_kept(
    publisher: Publisher,
    served: Served,
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
):
    inside = {"census2021-ts044-oa.csv": BODY, "census2021-ts044-lsoa.csv": BODY}
    publisher.pages["/files/census2021-ts044.zip"] = Answer(
        body=made_up_zip(tmp_path / "made-up.zip", inside).read_bytes()
    )
    file = listed(url=f"{PUBLISHER}/files/census2021-ts044.zip", format="zip")
    (outcome,) = run([file], registry, store, receipts, served)
    assert outcome.status is Status.OK


def test_what_arrived_is_held_to_the_entry_by_the_same_rule(registry: Registry):
    source = registry.get("made-up-homes")
    hold_what_arrived(source, f"{PUBLISHER}/files/homes.csv", "homes.csv", "census2021-ts044.csv")
    for named in (
        "census2021-ts021.csv",
        "TS030 religion.xlsx",
        "caf%C3%A9-t%53007a.csv",
        "Census TS-021.csv",
        "TS_021_oa.csv",
    ):
        with pytest.raises(Refused) as caught:
            hold_what_arrived(source, f"{PUBLISHER}/files/homes.csv", named)
        assert caught.value.reason is Reason.RESIDENT_TABLE


def test_every_reason_the_gate_gives_has_its_number_and_its_words():
    for reason in Reason:
        assert WORDS[Why[reason.name]]


# A file saved by hand


def by_hand(
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    saved: Path,
    address: str = "https://made-up.example/notes/download",
    **changed: object,
) -> Outcome:
    file = listed(item="notes", page="https://made-up.example/notes", url="", by_hand=True)
    file = file.model_copy(update=changed)
    return keep_by_hand(1, file, saved, address, "2026-09-24", registry, store, receipts, NOW)


@pytest.fixture
def saved(tmp_path: Path) -> Path:
    folder = tmp_path / "Downloads"
    folder.mkdir()
    path = folder / "made-up notes.csv"
    path.write_bytes(BODY)
    return path


def test_a_file_saved_by_hand_is_held_to_its_entry_too(
    registry: Registry, store: FolderStore, receipts: Path, saved: Path
):
    assert by_hand(registry, store, receipts, saved).status is Status.OK


@pytest.mark.parametrize(
    ("address", "why"),
    [
        ("https://elsewhere.example/notes/download", Why.NOT_THE_HOST),
        ("https://made-up.example/census2021-ts021.csv", Why.RESIDENT_TABLE),
        ("https://made-up.example/download?table=t%73021", Why.RESIDENT_TABLE),
    ],
)
def test_an_address_a_file_was_saved_from_is_held_to_the_entry(
    registry: Registry, store: FolderStore, receipts: Path, saved: Path, address: str, why: Why
):
    outcome = by_hand(registry, store, receipts, saved, address)
    assert (outcome.status, outcome.why) == (Status.REFUSED, why)
    assert store.list() == [] and not receipts.exists()


def test_a_file_saved_under_the_name_of_a_census_table_about_residents_is_refused(
    registry: Registry, store: FolderStore, receipts: Path, saved: Path
):
    named = saved.rename(saved.with_name("census2021-ts021-oa.csv"))
    outcome = by_hand(registry, store, receipts, named)
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.RESIDENT_TABLE)
    assert store.list() == [] and not receipts.exists()


def test_a_page_that_is_not_the_entrys_stops_a_file_saved_by_hand(
    registry: Registry, store: FolderStore, receipts: Path, saved: Path
):
    outcome = by_hand(registry, store, receipts, saved, page="https://made-up.example/rail")
    assert (outcome.status, outcome.why) == (Status.REFUSED, Why.NOT_THE_PAGE)
    assert store.list() == [] and not receipts.exists()


# The command line: the list is held when it is loaded, for plan and for fetch

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
item = "ethnic-group"
source_id = "made-up-homes"
use = "scoring"
what = "Made-up households by made-up area"
format = "zip"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/output/census2021-ts021.zip"
max_bytes = 1000000
edition = "2025"
data_period = { as_at = "2025-03-31" }
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

    def common(self) -> list[str]:
        return ["--list", str(self.list), "--registry", str(self.registry)]


def printed(capsys: pytest.CaptureFixture[str]) -> tuple[list[str], str]:
    captured = capsys.readouterr()
    return captured.out.splitlines(), captured.err


def of_files(lines: list[str], step: str) -> list[str]:
    """The lines a step printed of the files of a list, less how long each took."""
    return [line.rsplit(" seconds=", 1)[0] for line in lines if line.startswith(f"step={step} n=")]


def test_plan_says_which_file_is_not_as_its_entry_has_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    assert main(["plan", *folders.common(), "--words"], {}, never) == 1
    lines, errors = printed(capsys)
    assert errors == ""
    assert of_files(lines, "plan") == [
        "step=plan n=1 source=made-up-homes status=ok",
        "step=plan n=2 source=made-up-homes status=refused why=14",
    ]
    assert lines[-1] == "step=plan status=missing files=2 ready=1"
    assert any("names a census table about residents" in line for line in lines)


def test_fetch_asks_nothing_of_a_publisher_when_a_file_is_not_as_its_entry_has_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    arguments = ["fetch", *folders.common(), "--receipts", str(folders.receipts)]
    assert main(arguments, folders.environment, never) == 1
    lines, _ = printed(capsys)
    assert of_files(lines, "fetch") == [
        "step=fetch n=1 source=made-up-homes status=skipped why=2",
        "step=fetch n=2 source=made-up-homes status=refused why=14",
    ]
    assert not folders.store.exists() and not folders.receipts.exists()


def test_the_whole_list_is_held_when_one_item_of_it_is_asked_for(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """A list with a file that is not as its entry has it is no list to fetch from."""
    folders = Folders(tmp_path)
    arguments = ["fetch", *folders.common(), "--receipts", str(folders.receipts)]
    assert main([*arguments, "--only", "homes"], folders.environment, never) == 1
    lines, _ = printed(capsys)
    assert of_files(lines, "fetch") == [
        "step=fetch n=1 source=made-up-homes status=skipped why=2",
        "step=fetch n=2 source=made-up-homes status=refused why=14",
    ]
    assert lines[-1].startswith("step=fetch status=failed files=2 ok=0 skipped=1 refused=1 ")
    assert not folders.store.exists() and not folders.receipts.exists()


def test_by_hand_is_refused_for_a_file_that_is_not_as_its_entry_has_it(
    tmp_path: Path, saved: Path, capsys: pytest.CaptureFixture[str]
):
    folders = Folders(tmp_path)
    arguments = ["by-hand", *folders.common(), "--receipts", str(folders.receipts)]
    arguments += ["--item", "ethnic-group", "--file", str(saved), "--saved-on", "2026-09-24"]
    arguments += ["--url", "https://files.made-up.example/output/made-up.zip"]
    assert main(arguments, folders.environment, never) == 1
    lines, _ = printed(capsys)
    assert of_files(lines, "fetch") == [
        "step=fetch n=2 source=made-up-homes status=refused by_hand=1 why=14"
    ]
    assert not folders.store.exists() and not folders.receipts.exists()
