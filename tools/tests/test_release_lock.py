"""The lock of a release, and what an image may carry. Every release here is made up.

Its one name is Brackenhythe, which the made-up city holds and no map does. Its areas
stand under the ids of a release of London, because a lock is of a release that is not
made up.
"""

import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest
from public_log import FOLDERS, is_public
from release_lock import (
    APPROVED,
    BESIDE,
    Unreadable,
    carried,
    checked,
    compare,
    digest,
    hash_build,
    lock_of,
    read,
    show,
    written,
)

ROOT = Path(__file__).resolve().parents[2]
RELEASE = "lon-2026-09-23-01"
OTHER = "lon-2026-09-23-02"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
# A name and a figure that stand in the files of the made-up release, and in no lock.
NAME, FIGURE = "Brackenhythe", "73.25"


def packed(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


def release_files() -> dict[str, bytes]:
    """The files of a made-up release, but for its manifest. They hold a name and a figure."""
    return {
        "catalogue.json": packed(
            {
                "catalogue_version": 13,
                "metrics": [{"feature_id": "homes_flats"}, {"feature_id": "air_no2"}],
                "vibes": [{"tag_id": "homes"}],
            }
        ),
        "features.json": packed({"rows": [{"area_id": "lon-ne02999001", "value": FIGURE}]}),
        "neighbourhoods.json": packed({"rows": [{"area_id": "lon-ne02999001", "name": NAME}]}),
    }


def build_files(release: str = RELEASE, commit: str = COMMIT) -> dict[str, bytes]:
    """What a build writes beside its release. The record of the build says why in words."""
    return {
        "build.json": packed(
            {
                "release_id": release,
                "built_at": "2026-09-23T00:00:00Z",
                "commit": commit,
                "development": True,
                "measures_left_out": [
                    {
                        "feature_id": "water_access",
                        "rule": "measure_is_as_core_says",
                        "why": f"It is not named as core names it, in {NAME}.",
                    },
                    {"feature_id": "noise_exposure", "rule": "input_has_one_receipt"},
                ],
            }
        ),
        "evidence.json": packed({"rows": [{"area_id": "lon-ne02999001", "value": FIGURE}]}),
        "hashes.json": packed({"release_id": release}),
        "lock.json": packed({"release_id": release, "commit": commit}),
        "names.csv": f"area_id,name\nlon-ne02999001,{NAME}\n".encode(),
    }


def income_files() -> dict[str, bytes]:
    return {"income.json": packed({"rows": [{"value": FIGURE}]}), "manifest.json": packed({})}


def manifest_of(release: str, files: dict[str, bytes], synthetic: bool = False) -> bytes:
    listed = [
        {"name": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        for name, content in sorted(files.items())
    ]
    return packed(
        {
            "release_id": release,
            "built_at": "2026-09-23T00:00:00Z",
            "synthetic": synthetic,
            "preview": True,
            "counts": {
                "neighbourhoods": 2,
                "rankable": 2,
                "destinations": 0,
                "places": 0,
                "stations": 0,
            },
            "files": listed,
        }
    )


def built(
    out: Path,
    release: str = RELEASE,
    *,
    changed: dict[str, bytes] | None = None,
    income: bool = True,
) -> Path:
    """A made-up build in a folder: the release, and what stands beside it.

    `changed` takes the place of a file, by its name in the lock.
    """
    files = release_files()
    folders: dict[str, dict[str, bytes]] = {
        release: files | {"manifest.json": manifest_of(release, files)},
        f"{release}-build": build_files(release),
    }
    if income:
        folders[f"{release}-income"] = income_files()
    for name, content in (changed or {}).items():
        folder, _, file = name.partition("/")
        folders[folder][file] = content
    for folder, held in folders.items():
        (out / folder).mkdir(parents=True)
        for name, content in held.items():
            (out / folder / name).write_bytes(content)
    return out


def hashed(out: Path, copy: str = "a", release: str = RELEASE) -> tuple[int, str, str]:
    printed, outputs = io.StringIO(), io.StringIO()
    status = hash_build(out, release, copy, printed, outputs)
    return status, printed.getvalue(), outputs.getvalue()


def output_of(out: Path, copy: str = "a") -> str:
    status, _, outputs = hashed(out, copy)
    assert status == 0
    return outputs.removeprefix(f"{copy}=").strip()


def compared(out: Path, other: str, release: str = RELEASE) -> tuple[int, str]:
    printed = io.StringIO()
    return compare(out, release, other, printed), printed.getvalue()


def shown(out: Path, release: str = RELEASE) -> tuple[int, str, str]:
    printed, summary = io.StringIO(), io.StringIO()
    status = show(out, release, printed, summary)
    return status, printed.getvalue(), summary.getvalue()


def approved(folder: Path, out: Path, release: str = RELEASE) -> Path:
    """The folder of locks that are committed, with the lock of one build in it."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{release}.json").write_text(written(lock_of(out, release)), encoding="utf-8")
    return folder


def held(folder: Path, release: str, locks: Path) -> tuple[int, str]:
    printed = io.StringIO()
    return carried(folder, release, locks, printed), printed.getvalue()


# What a lock holds


def test_a_lock_names_the_release_the_commit_and_every_file_by_its_hash(tmp_path: Path):
    lock = lock_of(built(tmp_path), RELEASE)
    assert (lock["release_id"], lock["commit"], lock["built_at"]) == (
        RELEASE,
        COMMIT,
        "2026-09-23T00:00:00Z",
    )
    on_disk = {
        f"{folder.name}/{path.name}": path.read_bytes()
        for folder in sorted(tmp_path.iterdir())
        for path in sorted(folder.iterdir())
    }
    assert len(on_disk) == 11
    assert lock["files"] == [
        {"name": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
        for name, content in sorted(on_disk.items())
    ]


def test_a_lock_says_how_much_the_release_holds_and_what_was_left_out_and_why(tmp_path: Path):
    lock = lock_of(built(tmp_path), RELEASE)
    assert lock["holds"] == {
        "areas": 2,
        "rankable": 2,
        "measures": 2,
        "vibes": 1,
        "destinations": 0,
        "places": 0,
        "stations": 0,
    }
    assert lock["left_out"] == [
        {"feature": "noise_exposure", "rule": "input_has_one_receipt"},
        {"feature": "water_access", "rule": "measure_is_as_core_says"},
    ]
    assert (lock["preview"], lock["development"]) == (True, True)


def test_a_lock_holds_no_name_of_a_place_and_no_figure(tmp_path: Path):
    lock = written(lock_of(built(tmp_path), RELEASE))
    assert NAME not in lock and NAME.lower() not in lock and FIGURE not in lock
    # Nor the words of a build, which may name what a file holds.
    assert "It is not named" not in lock


def test_the_same_files_give_the_same_lock_and_one_byte_gives_another(tmp_path: Path):
    a, b = lock_of(built(tmp_path / "a"), RELEASE), lock_of(built(tmp_path / "b"), RELEASE)
    assert written(a) == written(b) and digest(a) == digest(b)
    changed = {f"{RELEASE}-build/evidence.json": build_files()["evidence.json"] + b" "}
    c = lock_of(built(tmp_path / "c", changed=changed), RELEASE)
    assert digest(c) != digest(a)
    assert [one["name"] for one, other in zip(a["files"], c["files"], strict=True) if one != other]


def test_a_lock_is_written_the_same_way_however_it_was_made(tmp_path: Path):
    lock = lock_of(built(tmp_path), RELEASE)
    text = written(lock)
    assert text.endswith("}\n") and text.count("\n") > 20
    # What is pasted may gain or lose a line at its end. What it says is what is held.
    again = checked(json.loads(f"\n{text}\n\n"))
    assert again == lock and digest(again) == digest(lock)


def test_a_build_with_no_income_beside_it_has_a_lock_too(tmp_path: Path):
    lock = lock_of(built(tmp_path, income=False), RELEASE)
    assert not any("-income/" in file["name"] for file in lock["files"])
    assert len(lock["files"]) == 9


@pytest.mark.parametrize(
    "gone",
    [f"{RELEASE}/manifest.json", f"{RELEASE}-build/build.json", f"{RELEASE}/catalogue.json"],
)
def test_a_build_that_lacks_what_a_lock_is_read_from_has_none(tmp_path: Path, gone: str):
    built(tmp_path)
    (tmp_path / gone).unlink()
    with pytest.raises(Unreadable):
        lock_of(tmp_path, RELEASE)


def test_a_build_with_no_folder_beside_the_release_has_no_lock(tmp_path: Path):
    built(tmp_path)
    for path in (tmp_path / f"{RELEASE}-build").iterdir():
        path.unlink()
    (tmp_path / f"{RELEASE}-build").rmdir()
    with pytest.raises(Unreadable):
        lock_of(tmp_path, RELEASE)


@pytest.mark.parametrize("name", ["Brackenhythe.csv", ".hidden.json", "rows.txt", "a b.json"])
def test_a_file_whose_name_no_build_writes_is_refused_and_not_named(tmp_path: Path, name: str):
    built(tmp_path)
    (tmp_path / RELEASE / name).write_bytes(b"made-up row\n")
    with pytest.raises(Unreadable) as refused:
        lock_of(tmp_path, RELEASE)
    assert NAME not in str(refused.value) and name not in str(refused.value)


def test_a_folder_inside_a_folder_of_a_build_is_refused(tmp_path: Path):
    built(tmp_path)
    (tmp_path / RELEASE / "more").mkdir()
    with pytest.raises(Unreadable):
        lock_of(tmp_path, RELEASE)


def test_what_a_file_browser_leaves_behind_is_no_file_of_a_release(tmp_path: Path):
    before = lock_of(built(tmp_path), RELEASE)
    (tmp_path / RELEASE / ".DS_Store").write_bytes(b"left by a file browser")
    assert lock_of(tmp_path, RELEASE) == before


def test_a_release_that_says_it_is_made_up_has_no_lock(tmp_path: Path):
    built(tmp_path)
    files = release_files()
    (tmp_path / RELEASE / "manifest.json").write_bytes(manifest_of(RELEASE, files, True))
    with pytest.raises(Unreadable):
        lock_of(tmp_path, RELEASE)


def test_a_build_of_another_release_than_the_folder_is_named_for_has_no_lock(tmp_path: Path):
    built(tmp_path)
    (tmp_path / RELEASE).rename(tmp_path / OTHER)
    (tmp_path / f"{RELEASE}-build").rename(tmp_path / f"{OTHER}-build")
    (tmp_path / f"{RELEASE}-income").rename(tmp_path / f"{OTHER}-income")
    with pytest.raises(Unreadable):
        lock_of(tmp_path, OTHER)


# What a lock may hold: every value is held to a shape


def a_lock(tmp_path: Path) -> dict[str, Any]:
    return json.loads(written(lock_of(built(tmp_path), RELEASE)))


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("release_id", "syn-2026-09-23-01"),
        ("release_id", "Brackenhythe"),
        ("release_id", 3),
        ("commit", "main"),
        ("commit", "0123456"),
        ("built_at", "yesterday"),
        ("built_at", "2026-09-23"),
        ("built_at", "2026-02-31T00:00:00Z"),
        ("development", "yes"),
        ("preview", 1),
        ("schema_version", 2),
        ("holds", {"areas": 2}),
        ("holds", []),
        ("left_out", [{"feature": "Brackenhythe", "rule": "input_has_one_receipt"}]),
        ("left_out", [{"feature": "water_access", "rule": "a rule of my own"}]),
        ("left_out", [{"feature": "water_access"}]),
        ("left_out", "none"),
        ("files", []),
        ("files", "none"),
    ],
)
def test_a_lock_with_a_value_of_another_shape_is_refused(tmp_path: Path, key: str, value: object):
    document = a_lock(tmp_path)
    document[key] = value
    with pytest.raises(Unreadable) as refused:
        checked(document)
    assert NAME not in str(refused.value)


# A file a build may write, which sorts after every file of the made-up build.
LAST = f"{RELEASE}/travel.json"


def test_a_lock_may_name_any_file_a_build_is_known_to_write(tmp_path: Path):
    document = a_lock(tmp_path)
    document["files"].append({"name": LAST, "sha256": "0" * 64, "bytes": 1})
    assert checked(document)["files"][-1]["name"] == LAST


@pytest.mark.parametrize(
    "file",
    [
        {"name": f"{RELEASE}/Brackenhythe.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}/zzz.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{OTHER}/travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}-residents/travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": f"{RELEASE}/../travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": "travel.json", "sha256": "0" * 64, "bytes": 1},
        {"name": 3, "sha256": "0" * 64, "bytes": 1},
        {"name": LAST, "sha256": "0" * 63, "bytes": 1},
        {"name": LAST, "sha256": "0" * 64, "bytes": -1},
        {"name": LAST, "sha256": "0" * 64, "bytes": True},
        {"name": LAST, "sha256": "0" * 64, "bytes": 1.0},
        {"name": LAST, "sha256": "0" * 64, "bytes": 1, "figure": 73.25},
        {"name": LAST, "sha256": "0" * 64},
    ],
)
def test_a_lock_names_a_file_of_its_own_release_and_nothing_more(
    tmp_path: Path, file: dict[str, object]
):
    document = a_lock(tmp_path)
    document["files"].append(file)
    with pytest.raises(Unreadable):
        checked(document)


def test_a_lock_names_each_file_once_and_in_the_order_of_their_names(tmp_path: Path):
    document = a_lock(tmp_path)
    twice = dict(document, files=[*document["files"], document["files"][-1]])
    turned = dict(document, files=list(reversed(document["files"])))
    for broken in (twice, turned):
        with pytest.raises(Unreadable):
            checked(broken)


def test_a_lock_holds_no_field_it_is_not_known_to_hold(tmp_path: Path):
    document = a_lock(tmp_path) | {"note": NAME}
    with pytest.raises(Unreadable):
        checked(document)
    less = a_lock(tmp_path / "again")
    del less["commit"]
    with pytest.raises(Unreadable):
        checked(less)


@pytest.mark.parametrize("missing", [f"{RELEASE}/manifest.json", f"{RELEASE}-build/hashes.json"])
def test_a_lock_names_what_a_release_is_served_with(tmp_path: Path, missing: str):
    """The service opens a release by its manifest, and holds it to the hashes of its build."""
    document = a_lock(tmp_path)
    document["files"] = [file for file in document["files"] if file["name"] != missing]
    with pytest.raises(Unreadable):
        checked(document)


# One build, and two side by side


def test_one_build_is_hashed_and_its_lock_is_the_output_of_the_job(tmp_path: Path):
    status, printed, outputs = hashed(built(tmp_path), "a")
    lock = lock_of(tmp_path, RELEASE)
    size = sum(file["bytes"] for file in lock["files"])
    assert status == 0
    assert printed == (
        f"step=lock status=ok copy=a release={RELEASE} files=11 bytes={size} "
        f"areas=2 measures=2 vibes=1 sha256={digest(lock)}\n"
    )
    assert outputs.startswith("a={") and outputs.count("\n") == 1
    assert checked(json.loads(outputs.removeprefix("a="))) == lock


def test_a_build_that_cannot_be_hashed_gives_no_output(tmp_path: Path):
    built(tmp_path)
    (tmp_path / RELEASE / "manifest.json").write_bytes(b"not json")
    assert hashed(tmp_path) == (1, "step=lock status=unreadable copy=a\n", "")


@pytest.mark.parametrize(
    ("copy", "release"), [("c", RELEASE), ("made-up row", RELEASE), ("a", "Brackenhythe")]
)
def test_a_copy_is_a_or_b_and_a_release_is_named_by_its_id(tmp_path: Path, copy: str, release: str):
    status, printed, outputs = hashed(built(tmp_path), copy, release)
    assert (status, printed, outputs) == (1, "step=lock status=refused\n", "")


def test_two_builds_of_the_same_bytes_are_the_same(tmp_path: Path):
    a = output_of(built(tmp_path / "a"), "a")
    status, printed = compared(built(tmp_path / "b"), a)
    lock = lock_of(tmp_path / "b", RELEASE)
    assert status == 0
    assert printed == f"step=compare status=ok files=11 differing=0 sha256={digest(lock)}\n"


def test_two_builds_that_differ_by_a_byte_fail_and_say_which_file(tmp_path: Path):
    a = output_of(built(tmp_path / "a"), "a")
    changed = {f"{RELEASE}-build/evidence.json": build_files()["evidence.json"] + b" "}
    status, printed = compared(built(tmp_path / "b", changed=changed), a)
    assert status == 1
    assert printed == (
        "step=compare status=differs folder=build file=evidence.json\n"
        "step=compare status=differs files=11 differing=1\n"
    )


def test_a_file_that_only_one_build_wrote_is_a_difference(tmp_path: Path):
    a = output_of(built(tmp_path / "a"), "a")
    status, printed = compared(built(tmp_path / "b", income=False), a)
    assert status == 1
    assert "step=compare status=differs folder=income file=income.json\n" in printed
    assert printed.endswith("step=compare status=differs files=11 differing=2\n")


def test_two_builds_from_two_commits_differ_though_every_file_is_the_same(tmp_path: Path):
    a = json.loads(output_of(built(tmp_path / "a"), "a"))
    a["commit"] = "f" * 40
    status, printed = compared(built(tmp_path / "b"), json.dumps(a))
    assert status == 1
    assert printed == "step=compare status=differs files=11 differing=0 wrong=1\n"


@pytest.mark.parametrize(
    "other", ["", "not json", "[]", "{}", '{"release_id": "Brackenhythe", "files": []}']
)
def test_a_build_that_gave_no_lock_cannot_be_compared(tmp_path: Path, other: str):
    status, printed = compared(built(tmp_path), other)
    assert (status, printed) == (1, "step=compare status=missing\n")


# What the run shows of a release: its lock, to be committed


def test_the_summary_of_a_run_holds_the_lock_as_it_is_to_be_committed(tmp_path: Path):
    status, printed, summary = shown(built(tmp_path))
    lock = lock_of(tmp_path, RELEASE)
    assert status == 0
    assert printed == f"step=lock status=ok release={RELEASE} files=11 sha256={digest(lock)}\n"
    block = summary.split("```json\n", 1)[1].split("```", 1)[0]
    assert block == written(lock)
    assert f"`{APPROVED.as_posix()}/{RELEASE}.json`" in summary
    # What is approved is said before it is: what it holds, and that it is not finished.
    assert "2 areas" in summary and "a preview" in summary and "a development build" in summary
    assert "water_access" in summary and "measure_is_as_core_says" in summary


def test_the_summary_holds_no_name_of_a_place_and_no_figure(tmp_path: Path):
    _, printed, summary = shown(built(tmp_path))
    _, hashes, outputs = hashed(tmp_path, "b")
    for said in (printed, summary, hashes, outputs):
        assert NAME not in said and NAME.lower() not in said and FIGURE not in said


def test_a_build_that_cannot_be_read_is_not_shown(tmp_path: Path):
    built(tmp_path)
    (tmp_path / f"{RELEASE}-build" / "build.json").write_bytes(f'{{"commit": "{NAME}"}}'.encode())
    assert shown(tmp_path) == (1, "step=lock status=unreadable\n", "")


# What an image may carry


def test_a_release_whose_lock_is_committed_and_whose_bytes_are_the_same_is_carried(
    tmp_path: Path,
):
    locks = approved(tmp_path / "approved", built(tmp_path / "built"))
    status, printed = held(built(tmp_path / "taken"), RELEASE, locks)
    lock = lock_of(tmp_path / "built", RELEASE)
    size = sum(file["bytes"] for file in lock["files"])
    assert status == 0
    assert printed == (
        f"step=take status=ok release={RELEASE} files=11 bytes={size} sha256={digest(lock)}\n"
    )


def test_a_release_no_lock_names_is_not_carried(tmp_path: Path):
    (tmp_path / "approved").mkdir()
    status, printed = held(built(tmp_path / "taken"), RELEASE, tmp_path / "approved")
    assert (status, printed) == (1, f"step=take status=missing release={RELEASE}\n")
    # Nor where another release is approved, and this one is not.
    locks = approved(tmp_path / "approved", built(tmp_path / "other", OTHER), OTHER)
    assert held(tmp_path / "taken", RELEASE, locks)[0] == 1


def test_a_release_of_which_one_byte_was_changed_is_not_carried(tmp_path: Path):
    locks = approved(tmp_path / "approved", built(tmp_path / "built"))
    content = release_files()["features.json"]
    changed = {f"{RELEASE}/features.json": content.replace(b"73.25", b"73.26")}
    assert len(changed[f"{RELEASE}/features.json"]) == len(content)
    status, printed = held(built(tmp_path / "taken", changed=changed), RELEASE, locks)
    assert status == 1
    assert printed == (
        f"step=take status=differs release={RELEASE} folder=release file=features.json\n"
        f"step=take status=differs release={RELEASE} files=11 differing=1\n"
    )


def test_a_release_that_lacks_a_file_of_its_lock_or_holds_one_more_is_not_carried(
    tmp_path: Path,
):
    locks = approved(tmp_path / "approved", built(tmp_path / "built"))
    built(tmp_path / "less")
    (tmp_path / "less" / f"{RELEASE}-build" / "names.csv").unlink()
    assert held(tmp_path / "less", RELEASE, locks) == (
        1,
        f"step=take status=differs release={RELEASE} folder=build file=names.csv\n"
        f"step=take status=differs release={RELEASE} files=11 differing=1\n",
    )
    built(tmp_path / "more")
    (tmp_path / "more" / RELEASE / "cost.json").write_bytes(b"{}\n")
    assert held(tmp_path / "more", RELEASE, locks) == (
        1,
        f"step=take status=differs release={RELEASE} folder=release file=cost.json\n"
        f"step=take status=differs release={RELEASE} files=11 differing=1\n",
    )


def test_a_second_release_beside_the_one_that_is_carried_is_refused(tmp_path: Path):
    """An image holds what is served and nothing else: no preview that lay in the folder."""
    locks = approved(tmp_path / "approved", built(tmp_path / "built"))
    built(tmp_path / "taken")
    built(tmp_path / "taken", OTHER)
    status, printed = held(tmp_path / "taken", RELEASE, locks)
    assert (status, printed) == (1, f"step=take status=refused release={RELEASE} unlisted=3\n")


def test_a_lock_that_is_named_for_another_release_than_it_names_is_refused(tmp_path: Path):
    locks = approved(tmp_path / "approved", built(tmp_path / "built"))
    (locks / f"{RELEASE}.json").rename(locks / f"{OTHER}.json")
    status, printed = held(built(tmp_path / "taken", OTHER), OTHER, locks)
    assert (status, printed) == (1, f"step=take status=unreadable release={OTHER}\n")


def test_a_lock_that_cannot_be_read_stands_for_nothing(tmp_path: Path):
    locks = tmp_path / "approved"
    locks.mkdir()
    (locks / f"{RELEASE}.json").write_text('{"release_id": "lon-2026-09-23-01"}')
    status, printed = held(built(tmp_path / "taken"), RELEASE, locks)
    assert (status, printed) == (1, f"step=take status=unreadable release={RELEASE}\n")


def test_the_made_up_city_is_carried_with_no_lock_as_it_is_committed(tmp_path: Path):
    fixture = ROOT / "data" / "fixtures" / "synthetic"
    status, printed = held(fixture, "syn-2026-09-23-01", tmp_path / "no-such-folder")
    assert status == 0
    assert printed.startswith("step=take status=ok release=syn-2026-09-23-01 files=11 bytes=")


def test_a_made_up_city_that_is_not_what_its_manifest_says_is_not_carried(tmp_path: Path):
    files = release_files()
    made_up = "syn-2026-09-23-01"
    (tmp_path / made_up).mkdir()
    for name, content in files.items():
        (tmp_path / made_up / name).write_bytes(content)
    (tmp_path / made_up / "manifest.json").write_bytes(manifest_of(made_up, files, True))
    assert held(tmp_path, made_up, tmp_path / "none")[0] == 0
    (tmp_path / made_up / "features.json").write_bytes(files["features.json"] + b" ")
    assert held(tmp_path, made_up, tmp_path / "none") == (
        1,
        f"step=take status=differs release={made_up} folder=release file=features.json\n"
        f"step=take status=differs release={made_up} files=4 differing=1\n",
    )


def test_a_release_under_a_made_up_id_that_says_it_is_real_is_not_carried(tmp_path: Path):
    files = release_files()
    made_up = "syn-2026-09-23-01"
    (tmp_path / made_up).mkdir()
    for name, content in files.items():
        (tmp_path / made_up / name).write_bytes(content)
    (tmp_path / made_up / "manifest.json").write_bytes(manifest_of(made_up, files, False))
    assert held(tmp_path, made_up, tmp_path / "none") == (
        1,
        f"step=take status=refused release={made_up}\n",
    )


@pytest.mark.parametrize("release", ["Brackenhythe", "lon-2026-09-23", "../lon-2026-09-23-01", ""])
def test_what_is_not_the_id_of_a_release_is_refused_and_not_repeated(tmp_path: Path, release: str):
    status, printed = held(built(tmp_path), release, tmp_path / "approved")
    assert (status, printed) == (1, "step=take status=refused\n")


# A lock that is committed


def test_a_lock_is_read_back_as_it_was_written(tmp_path: Path):
    lock = lock_of(built(tmp_path), RELEASE)
    path = tmp_path / f"{RELEASE}.json"
    path.write_text(written(lock), encoding="utf-8")
    assert read(path) == lock


@pytest.mark.parametrize("content", [b"", b"not json", b"[]", b"\xff", b'{"release_id": 3}'])
def test_a_file_that_is_no_lock_is_not_read_as_one(tmp_path: Path, content: bytes):
    path = tmp_path / f"{RELEASE}.json"
    path.write_bytes(content)
    with pytest.raises(Unreadable):
        read(path)


def test_every_lock_this_repository_holds_is_one_and_is_named_for_its_release():
    """To approve a release is to commit its lock. One that cannot be read approves nothing."""
    folder = ROOT / APPROVED
    found = sorted(path for path in folder.iterdir() if path.name != "README.md")
    for path in found:
        assert path.suffix == ".json", path.name
        assert read(path)["release_id"] == path.stem, path.name


# What is printed


def test_every_line_printed_is_one_the_public_log_would_show(tmp_path: Path):
    a = output_of(built(tmp_path / "a"), "a")
    changed = {f"{RELEASE}/features.json": b"{}\n"}
    built(tmp_path / "b", changed=changed)
    locks = approved(tmp_path / "approved", tmp_path / "a")
    printed = (
        hashed(tmp_path / "a")[1]
        + hashed(tmp_path / "a", "made-up row")[1]
        + hashed(tmp_path / "nowhere")[1]
        + compared(tmp_path / "a", a)[1]
        + compared(tmp_path / "b", a)[1]
        + compared(tmp_path / "a", "")[1]
        + shown(tmp_path / "a")[1]
        + held(tmp_path / "a", RELEASE, locks)[1]
        + held(tmp_path / "b", RELEASE, locks)[1]
        + held(tmp_path / "a", OTHER, locks)[1]
        + held(tmp_path / "a", "Brackenhythe", locks)[1]
    )
    assert len(printed.splitlines()) >= 12
    assert all(is_public(line) for line in printed.splitlines())
    # A folder is said by one of three words, which are the three the public log shows.
    assert set(BESIDE.values()) == FOLDERS
