"""A release that was written by hand is refused when the service loads it.

The service reads the bytes of a release and leaves every check to core. These tests write
by hand, into a copy of the made-up release, what a file of changes might have made, and
hold that the service does not load it. Every name is made up.
"""

import hashlib
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from burro_api.app import deps_from
from burro_api.loading import IGNORED, load_release
from burro_api.settings import SYNTHETIC_FIXTURE, Settings
from burro_core.release import LOCK, ReleaseError

OF_A_FILE = hashlib.sha256(b"a made-up file of changes\n").hexdigest()
Change = Callable[[dict[str, Any]], None]


def written(tmp_path: Path, change: Change, names: str | None = None) -> Path:
    """A copy of the made-up release with its catalogue changed by hand, and its manifest
    mended to match, as a hand would mend it. `names` is the hash of a file of changes
    the manifest is made to say."""
    folder = tmp_path / SYNTHETIC_FIXTURE.name
    shutil.copytree(SYNTHETIC_FIXTURE, folder, ignore=shutil.ignore_patterns(IGNORED))
    catalogue = json.loads((folder / "catalogue.json").read_bytes())
    change(catalogue)
    held = json.dumps(catalogue).encode()
    (folder / "catalogue.json").write_bytes(held)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    for entry in manifest["files"]:
        if entry["name"] == "catalogue.json":
            entry.update(sha256=hashlib.sha256(held).hexdigest(), bytes=len(held))
    if names is not None:
        manifest["changes_sha256"] = names
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


def vibe(catalogue: dict[str, Any], tag_id: str) -> dict[str, Any]:
    return next(one for one in catalogue["vibes"] if one["tag_id"] == tag_id)


def renamed(catalogue: dict[str, Any]) -> None:
    vibe(catalogue, "leafy").update(label="Green and leafy", short_label="Green and leafy")


def named_for_an_area(catalogue: dict[str, Any]) -> None:
    vibe(catalogue, "leafy").update(label="Cindermoor feel", short_label="Cindermoor feel")


def a_part_of_the_census(catalogue: dict[str, Any]) -> None:
    terms = vibe(catalogue, "leafy")["terms"]
    terms[0]["hundredths"] -= 10
    terms.append({"feature_id": "religion", "hundredths": 10, "reading": "high"})


def who_lived_there_read_low(catalogue: dict[str, Any]) -> None:
    vibe(catalogue, "family_area")["terms"][0]["reading"] = "low"


def refused(folder: Path) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        load_release(folder)
    assert "Cindermoor" not in str(caught.value)
    return caught.value.file, caught.value.rule


@pytest.mark.parametrize(
    ("change", "names", "file", "rule"),
    [
        (renamed, None, "manifest.json", "changes_are_named"),
        (renamed, OF_A_FILE, LOCK, "changes_are_locked"),
        (named_for_an_area, OF_A_FILE, "catalogue.json", "names_name_no_place"),
        (a_part_of_the_census, OF_A_FILE, "catalogue.json", "catalogue_matches_core"),
        (who_lived_there_read_low, OF_A_FILE, "catalogue.json", "vibes_match_core"),
    ],
)
def test_the_service_loads_no_release_that_was_changed_by_hand(
    tmp_path: Path, change: Change, names: str | None, file: str, rule: str
):
    assert refused(written(tmp_path, change, names)) == (file, rule)


def test_the_service_does_not_start_on_one(tmp_path: Path):
    folder = written(tmp_path, renamed, OF_A_FILE)
    with pytest.raises(ReleaseError) as caught:
        deps_from(Settings.from_env({"BURRO_RELEASE_DIR": str(folder)}))
    assert (caught.value.file, caught.value.rule) == (LOCK, "changes_are_locked")


def test_a_release_that_names_its_file_is_loaded_beside_a_lock_that_names_it_too(
    tmp_path: Path,
):
    folder = written(tmp_path, renamed, OF_A_FILE)
    beside = folder.with_name(f"{folder.name}-build")
    beside.mkdir()
    lock = {"inputs": [{"name": "changes/r1.jsonl", "sha256": OF_A_FILE, "bytes": 560}]}
    (beside / LOCK).write_text(json.dumps(lock), encoding="utf-8")
    loaded = load_release(folder)
    assert loaded.manifest.changes_sha256 == OF_A_FILE
    assert next(one.label for one in loaded.vibes if one.tag_id == "leafy") == "Green and leafy"
    # The lock is made to name another file.
    lock["inputs"][0]["sha256"] = hashlib.sha256(b"another\n").hexdigest()
    (beside / LOCK).write_text(json.dumps(lock), encoding="utf-8")
    assert refused(folder) == (LOCK, "changes_are_locked")
