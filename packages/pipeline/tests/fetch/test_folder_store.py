"""The store as a folder on disk. Every file here is made up. No socket is opened."""

import hashlib
from pathlib import Path

import pytest
from burro_pipeline.fetch.store import (
    FolderStore,
    Held,
    StoreError,
    find,
    hash_file,
    publisher_name,
    store_from_environment,
)

CONTENT = b"code,homes\nmade-up-1,10\nmade-up-2,20\n"
SHA256 = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture
def saved(tmp_path: Path) -> Path:
    path = tmp_path / "as saved.csv"
    path.write_bytes(CONTENT)
    return path


@pytest.fixture
def store(tmp_path: Path) -> FolderStore:
    return FolderStore(tmp_path / "store")


def test_putting_a_file_gives_its_hash_and_its_size(store: FolderStore, saved: Path):
    held, new = store.put("made-up-source", "homes.csv", saved)
    assert new
    assert held == Held("made-up-source", SHA256, "homes.csv", len(CONTENT))
    assert held.file_id == f"f-{SHA256[:12]}"


def test_a_file_is_kept_under_its_source_and_its_hash(store: FolderStore, saved: Path):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    assert held.key == f"raw/made-up-source/{SHA256}/homes.csv"
    assert (store.folder / held.key).read_bytes() == CONTENT


def test_a_file_comes_back_by_its_hash_byte_for_byte(
    store: FolderStore, saved: Path, tmp_path: Path
):
    store.put("made-up-source", "homes.csv", saved)
    held = store.get(SHA256, tmp_path / "copy.csv")
    assert (tmp_path / "copy.csv").read_bytes() == CONTENT
    assert held.name == "homes.csv"


def test_a_file_put_twice_is_kept_once_and_never_written_over(store: FolderStore, saved: Path):
    first, _ = store.put("made-up-source", "homes.csv", saved)
    kept = store.folder / first.key
    written_at = kept.stat().st_mtime_ns
    second, new = store.put("made-up-source", "homes.csv", saved)
    assert not new
    assert second == first
    assert kept.stat().st_mtime_ns == written_at
    assert store.list() == [first]


def test_a_publisher_that_reissues_a_file_makes_a_second_file(
    store: FolderStore, saved: Path, tmp_path: Path
):
    first, _ = store.put("made-up-source", "homes.csv", saved)
    reissued = tmp_path / "reissued.csv"
    reissued.write_bytes(CONTENT + b"made-up-3,30\n")
    second, new = store.put("made-up-source", "homes.csv", reissued)
    assert new
    assert second.sha256 != first.sha256
    assert store.list() == sorted([first, second], key=lambda held: held.key)


def test_the_list_holds_every_file_in_a_fixed_order(
    store: FolderStore, saved: Path, tmp_path: Path
):
    other = tmp_path / "other.csv"
    other.write_bytes(b"made up\n")
    store.put("made-up-zebra", "z.csv", saved)
    store.put("made-up-aardvark", "a.csv", other)
    assert [held.source_id for held in store.list()] == ["made-up-aardvark", "made-up-zebra"]


def test_an_empty_store_lists_nothing(store: FolderStore):
    assert store.list() == []


def test_a_file_changed_after_it_was_stored_is_refused(
    store: FolderStore, saved: Path, tmp_path: Path
):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    (store.folder / held.key).write_bytes(b"changed on disk")
    with pytest.raises(StoreError, match="does not match its hash"):
        store.get(SHA256, tmp_path / "copy.csv")
    assert not (tmp_path / "copy.csv").exists()


def test_a_hash_the_store_does_not_hold_is_refused(store: FolderStore, tmp_path: Path):
    with pytest.raises(StoreError, match="holds no file"):
        store.get("0" * 64, tmp_path / "copy.csv")


@pytest.mark.parametrize("source_id", ["", "../escape", "Upper-Case", "a/b", "a b", ".hidden"])
def test_a_source_id_that_is_not_a_registry_id_is_refused(
    store: FolderStore, saved: Path, source_id: str
):
    with pytest.raises(StoreError, match="not a registry id"):
        store.put(source_id, "homes.csv", saved)
    assert not store.folder.exists() or not any(store.folder.rglob("*.csv"))


@pytest.mark.parametrize(
    ("given", "kept"),
    [
        ("homes.csv", "homes.csv"),
        ("Table 1 (final).xlsx", "Table 1 (final).xlsx"),
        ("café homes.csv", "café homes.csv"),
        ("../../etc/passwd", "passwd"),
        ("C:\\saved\\homes.csv", "homes.csv"),
        (".hidden", "hidden"),
        (" . .. homes.csv ", "homes.csv"),
        ("..", "file"),
        ("", "file"),
        ("a\nb\x1b[31m.csv", "ab[31m.csv"),
        ("a\u2028b.csv", "ab.csv"),
        ("x" * 300 + ".csv", "x" * 196 + ".csv"),
    ],
)
def test_a_file_name_cannot_leave_its_folder_or_break_a_line(given: str, kept: str):
    assert publisher_name(given) == kept


def test_a_file_is_held_under_the_name_its_receipt_will_give(store: FolderStore, saved: Path):
    held, _ = store.put("made-up-source", "saved/Table 1 (final).csv", saved)
    assert held.name == "Table 1 (final).csv"
    assert store.list() == [held]
    assert store.get(SHA256, saved.with_name("copy.csv")) == held


def test_a_stray_file_in_the_folder_is_not_taken_for_a_held_file(store: FolderStore, saved: Path):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    (store.folder / held.key).with_name(".DS_Store").write_bytes(b"left by a file browser")
    (store.folder / "raw" / "notes.txt").write_bytes(b"left by a person")
    assert store.list() == [held]


def test_a_file_is_found_by_its_hash_or_by_its_file_id(store: FolderStore, saved: Path):
    held, _ = store.put("made-up-source", "homes.csv", saved)
    assert find(store, SHA256) == held
    assert find(store, held.file_id) == held


def test_a_reference_that_is_neither_a_hash_nor_a_file_id_is_refused(store: FolderStore):
    with pytest.raises(StoreError, match="a file id or a hash"):
        find(store, "homes.csv")


def test_a_reference_to_nothing_held_is_refused(store: FolderStore):
    with pytest.raises(StoreError, match="holds no file"):
        find(store, "f-000000000000")


def test_hashing_reads_a_file_in_pieces(tmp_path: Path):
    large = tmp_path / "large.bin"
    large.write_bytes(b"made up " * 300_000)
    assert hash_file(large) == (hashlib.sha256(b"made up " * 300_000).hexdigest(), 2_400_000)


def test_the_store_is_chosen_by_the_environment(tmp_path: Path):
    store = store_from_environment({"BURRO_STORE_FOLDER": str(tmp_path / "store")})
    assert isinstance(store, FolderStore)


def test_with_no_store_named_the_refusal_names_the_variables_and_nothing_else():
    with pytest.raises(StoreError) as refused:
        store_from_environment({"HOME": "/made-up/home", "BURRO_STORE_SECRET": "made-up-canary"})
    message = str(refused.value)
    assert "BURRO_STORE_FOLDER" in message
    assert "BURRO_STORE_ENDPOINT" in message
    assert "made-up" not in message
