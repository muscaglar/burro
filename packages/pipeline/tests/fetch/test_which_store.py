"""One store is named, and a run says which kind it is.

A folder named as the store won over an object store that was named too, and
nothing was said. In a hosted run that is a fetch into a folder on a machine
that is thrown away, with a green tick. So a step refuses to start when both
are named, and the steps that write to the store, or show that it answers, say
which kind they were given.

Every file is made up. The object store is a stand-in on the loopback address.
"""

from collections.abc import Iterator
from pathlib import Path

import public_log
import pytest
from burro_pipeline.fetch.cli import main
from burro_pipeline.fetch.download import Downloaded
from burro_pipeline.fetch.s3 import S3Store
from burro_pipeline.fetch.store import (
    FOLDER_VARIABLE,
    S3_VARIABLES,
    FolderStore,
    StoreError,
    store_from_environment,
)

from .support import (
    CANARY_BUCKET,
    CANARY_KEY,
    CANARY_SECRET,
    MADE_UP_REGISTRY,
    ONLY_LOOPBACK,
    Answer,
    Served,
    made_up_zip,
    serving,
)

OBJECT_STORE = {
    "BURRO_STORE_ENDPOINT": "https://zzyzx-account.made-up.example",
    "BURRO_STORE_BUCKET": CANARY_BUCKET,
    "BURRO_STORE_KEY_ID": CANARY_KEY,
    "BURRO_STORE_SECRET": CANARY_SECRET,
}
LIST = """
schema_version = 1
build = "made-up"

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


def never(*_: object, **__: object) -> Downloaded:
    raise AssertionError("nothing may be asked of a publisher here")


def nothing_is_given_away(said: str, folder: Path) -> bool:
    hidden = [*OBJECT_STORE.values(), "zzyzx", "made-up.example", str(folder)]
    return not [value for value in hidden if value in said]


# Which store the environment names


def test_a_folder_alone_names_a_folder(tmp_path: Path):
    store = store_from_environment({FOLDER_VARIABLE: str(tmp_path)})
    assert isinstance(store, FolderStore) and store.kind == "folder"


def test_the_four_of_an_object_store_alone_name_an_object_store():
    store = store_from_environment(OBJECT_STORE)
    assert isinstance(store, S3Store) and store.kind == "object_store"


def test_a_folder_and_an_object_store_named_together_are_refused(tmp_path: Path):
    with pytest.raises(StoreError) as refused:
        store_from_environment({FOLDER_VARIABLE: str(tmp_path), **OBJECT_STORE})
    said = str(refused.value)
    assert "both a folder and an object store are named" in said
    assert FOLDER_VARIABLE in said and all(name in said for name in S3_VARIABLES)
    assert nothing_is_given_away(said, tmp_path)


@pytest.mark.parametrize("name", [*S3_VARIABLES, "BURRO_STORE_REGION"])
def test_a_folder_and_any_part_of_an_object_store_are_refused(tmp_path: Path, name: str):
    """One variable left behind is enough: nobody can say which store was meant."""
    with pytest.raises(StoreError, match="both a folder and an object store are named") as refused:
        store_from_environment({FOLDER_VARIABLE: str(tmp_path), name: "zzyzx-left-behind"})
    assert nothing_is_given_away(str(refused.value), tmp_path)


def test_a_variable_that_is_set_to_nothing_names_nothing(tmp_path: Path):
    """A secret that was never stored reaches a step as an empty value."""
    empty = dict.fromkeys(S3_VARIABLES, "")
    assert isinstance(
        store_from_environment({FOLDER_VARIABLE: str(tmp_path), **empty}), FolderStore
    )
    assert isinstance(store_from_environment({FOLDER_VARIABLE: "", **OBJECT_STORE}), S3Store)


# What a step says


class Folders:
    def __init__(self, root: Path) -> None:
        self.store, self.receipts = root / "store", root / "receipts"
        self.registry, self.list = root / "registry.toml", root / "made-up.toml"
        self.registry.write_text(MADE_UP_REGISTRY, encoding="utf-8")
        self.list.write_text(LIST, encoding="utf-8")
        self.saved = made_up_zip(root / "Made-up notes.zip", {"notes.csv": b"code\nmade-up\n"})
        self.contact = {"BURRO_FETCH_CONTACT": "data@made-up.example"}
        self.folder = {FOLDER_VARIABLE: str(self.store), **self.contact}

    def words(self, step: str) -> list[str]:
        listed = ["--list", str(self.list), "--registry", str(self.registry)]
        kept = ["--receipts", str(self.receipts)]
        by_hand = ["--item", "notes", "--file", str(self.saved), "--saved-on", "2026-09-24"]
        by_hand += ["--url", "https://made-up.example/notes/download"]
        return {
            "fetch": ["fetch", *listed, *kept],
            "by-hand": ["by-hand", *listed, *kept, *by_hand],
            "held": ["held"],
            "receipts": ["receipts", *kept],
            "describe": ["describe", "f-0123456789ab"],
        }[step]


@pytest.fixture
def folders(tmp_path: Path) -> Folders:
    return Folders(tmp_path)


@pytest.fixture
def served() -> Iterator[Served]:
    with serving(lambda _: Answer(200)) as server:
        yield server


@pytest.mark.parametrize("step", ["fetch", "by-hand", "held", "receipts", "describe"])
def test_no_step_starts_when_both_are_named(
    folders: Folders, capsys: pytest.CaptureFixture[str], step: str
):
    assert main(folders.words(step), folders.folder | OBJECT_STORE, never) == 2
    out = capsys.readouterr()
    assert out.out == ""
    assert "both a folder and an object store are named" in out.err
    assert out.err.count("\n") == 1 and nothing_is_given_away(out.err, folders.store)
    assert not folders.store.exists() and not folders.receipts.exists()


@pytest.mark.parametrize("step", ["fetch", "by-hand", "held"])
def test_a_step_that_writes_to_the_store_or_shows_that_it_answers_says_which_kind_it_is(
    folders: Folders, capsys: pytest.CaptureFixture[str], step: str
):
    main(folders.words(step), folders.folder, never)
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "step=store kind=folder"
    assert public_log.is_public(lines[0])
    assert len([line for line in lines if " kind=" in line]) == 1


@ONLY_LOOPBACK
@pytest.mark.parametrize("step", ["fetch", "by-hand", "held"])
def test_an_object_store_is_said_to_be_one_before_anything_is_asked_of_it(
    folders: Folders, served: Served, capsys: pytest.CaptureFixture[str], step: str
):
    """The stand-in speaks no TLS, so the step fails when it asks. It has said the kind by then."""
    named = OBJECT_STORE | {"BURRO_STORE_ENDPOINT": f"https://127.0.0.1:{served.port}"}
    main(folders.words(step), named | folders.contact, never)
    out = capsys.readouterr()
    assert out.out.splitlines()[0] == "step=store kind=object_store"
    assert public_log.is_public(out.out.splitlines()[0])
    assert nothing_is_given_away(out.out + out.err, folders.store)
    assert str(served.port) not in out.out + out.err


def test_a_step_that_cannot_start_says_nothing_of_a_store(
    folders: Folders, capsys: pytest.CaptureFixture[str]
):
    assert main(folders.words("held"), {}, never) == 2
    assert capsys.readouterr().out == ""
    assert main(["fetch", "--list", "m99"], folders.folder, never) == 2
    assert capsys.readouterr().out == ""


def test_the_public_log_knows_each_kind_of_store_and_no_other_word():
    assert {FolderStore.kind, S3Store.kind} == {"folder", "object_store"}
    assert {FolderStore.kind, S3Store.kind} <= public_log.KINDS
    for word in ("bucket", "made-up", "zzyzx-account", "1", ""):
        assert not public_log.is_public(f"step=store kind={word}")
