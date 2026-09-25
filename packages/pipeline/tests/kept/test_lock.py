"""The lock of a release, as a step reads the one that is committed. Every release is made up.

`tools/release_lock.py` writes a lock and is the judge of what an image may
carry. The pipeline reads one to say which files it takes. The two are held
to each other here.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import release_lock
from burro_pipeline.kept.lock import (
    APPROVED,
    BESIDE,
    SERVED_WITH,
    LockRefused,
    approved,
    read_lock,
)

from ..assemble.support import RELEASE
from .support import OTHER, approve, built


def committed(tmp_path: Path) -> Path:
    return approve(tmp_path / "approved", built(tmp_path / "made")) / f"{RELEASE}.json"


def test_what_the_tool_writes_the_pipeline_reads_to_the_same_hash(tmp_path: Path):
    path = committed(tmp_path)
    of_the_tool = release_lock.read(path)
    lock = read_lock(path)
    assert lock.digest() == release_lock.digest(of_the_tool)
    assert lock.model_dump(mode="json") == of_the_tool
    assert [file.name for file in lock.files] == [file["name"] for file in of_the_tool["files"]]
    # The 11 files of the release, and the 7 that stand beside it.
    assert len(lock.files) == 18 and lock.release_id == RELEASE


def test_both_keep_a_lock_in_the_same_folder_under_the_id_of_its_release(tmp_path: Path):
    assert APPROVED == release_lock.APPROVED
    assert read_lock(committed(tmp_path)).path() == APPROVED / f"{RELEASE}.json"
    # And both ask that a lock names what a release is served with.
    assert set(SERVED_WITH) == set(release_lock.SERVED_WITH)
    assert tuple(release_lock.BESIDE) == BESIDE


def test_a_lock_says_what_the_build_left_out_by_the_id_of_the_measure_and_its_rule(
    tmp_path: Path,
):
    lock = read_lock(committed(tmp_path))
    gone = {one.feature.value: one.rule for one in lock.left_out}
    assert gone["centre_compact"] == "measure_is_as_core_says"
    assert gone["price_median"] == "input_has_one_receipt"
    assert lock.holds.areas == 3 and lock.holds.measures == 24 and lock.preview


def broken(tmp_path: Path, change: dict[str, Any]) -> Path:
    path = committed(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8")) | change
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "change",
    [
        {"release_id": "syn-2026-09-23-01"},
        {"release_id": OTHER},
        {"commit": "main"},
        {"built_at": "2026-09-23"},
        {"built_at": "2026-02-31T00:00:00Z"},
        {"development": "yes"},
        {"preview": 1},
        {"schema_version": 2},
        {"schema_version": "1"},
        {"holds": {"areas": 3}},
        {"left_out": [{"feature": "brackenhythe", "rule": "input_has_one_receipt"}]},
        {"left_out": [{"feature": "water_access", "rule": "a_rule_of_my_own"}]},
        {"files": []},
        {"note": "made-up row"},
    ],
)
def test_a_lock_with_a_value_of_another_shape_is_refused_by_both(
    tmp_path: Path, change: dict[str, Any]
):
    path = broken(tmp_path, change)
    with pytest.raises(LockRefused) as refused:
        read_lock(path)
    assert "brackenhythe" not in str(refused.value) and "made-up row" not in str(refused.value)
    with pytest.raises(release_lock.Unreadable):
        release_lock.read(path)


@pytest.mark.parametrize(
    "file",
    [
        {"name": f"{OTHER}/travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}/../travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}/sub/travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}/Brackenhythe.json", "sha256": "0" * 64, "bytes": 1},
        {"name": "travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"/{RELEASE}/travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}/travel.json", "sha256": "0" * 63, "bytes": 1},
        {"name": f"{RELEASE}/travel.json", "sha256": "0" * 64, "bytes": -1},
        {"name": f"{RELEASE}/travel.json", "sha256": "0" * 64, "bytes": 1.5},
        {"name": f"{RELEASE}/travel.json", "sha256": "0" * 64, "bytes": True},
        {"name": f"{RELEASE}/travel.json", "sha256": "0" * 64, "bytes": 1, "figure": 73.25},
    ],
)
def test_a_lock_that_names_what_is_no_file_of_its_release_is_refused_by_both(
    tmp_path: Path, file: dict[str, Any]
):
    path = committed(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["files"] = [one for one in document["files"] if "travel.json" not in one["name"]]
    document["files"].append(file)
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(LockRefused):
        read_lock(path)
    with pytest.raises(release_lock.Unreadable):
        release_lock.read(path)


def test_a_lock_is_named_for_the_release_it_names(tmp_path: Path):
    path = committed(tmp_path)
    other = path.with_name(f"{OTHER}.json")
    path.rename(other)
    with pytest.raises(LockRefused) as refused:
        read_lock(other)
    assert "named for another release" in str(refused.value)


@pytest.mark.parametrize("content", [b"", b"not json", b"[]", b"\xff", b"{}"])
def test_a_file_that_is_no_lock_is_refused_and_not_repeated(tmp_path: Path, content: bytes):
    path = tmp_path / f"{RELEASE}.json"
    path.write_bytes(content)
    with pytest.raises(LockRefused) as refused:
        read_lock(path)
    assert "not json" not in str(refused.value)
    with pytest.raises(LockRefused):
        read_lock(tmp_path / "no-such-file.json")


def test_the_releases_that_are_approved_are_the_locks_in_the_folder(tmp_path: Path):
    assert approved(tmp_path / "no-such-folder") == []
    folder = tmp_path / "approved"
    folder.mkdir()
    (folder / "README.md").write_text("What the folder is for.\n", encoding="utf-8")
    assert approved(folder) == []
    for name in (f"{OTHER}.json", f"{RELEASE}.json", "notes.json", "syn-2026-09-23-01.json"):
        (folder / name).write_text("{}", encoding="utf-8")
    assert approved(folder) == [RELEASE, OTHER]
