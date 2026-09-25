"""The steps `keep` and `take`, run as a person runs them, on the made-up build.

The store of releases is a folder of the test's own, which stands in for a
bucket. Nothing here reaches a network.
"""

import hashlib
import io
import json
from pathlib import Path

import pytest
import release_lock
from burro_pipeline.kept import cli
from burro_pipeline.kept.lock import read_lock
from burro_pipeline.kept.store import FOLDER_VARIABLE, PREFIX
from burro_pipeline.release.read import read_served
from public_log import is_public

from ..assemble.support import RELEASE
from ..cells.support import CANARY, REPOSITORY, held
from .support import MADE_UP, OTHER, approve, built, keep, run, take

FIXTURE = REPOSITORY / "data" / "fixtures" / "synthetic"


def kept_and_approved(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A build that was kept and approved: where it was built, the store, and the locks."""
    out = built(tmp_path / "made")
    assert keep(out, tmp_path / "store")[0] == 0
    return out, tmp_path / "store", approve(tmp_path / "approved", out)


# Keep


def test_a_release_that_was_built_is_kept_file_by_file_under_the_name_its_lock_gives(
    tmp_path: Path,
):
    out = built(tmp_path / "made")
    status, lines, words = keep(out, tmp_path / "store")
    size = sum(len(content) for content in held(out).values())
    assert (status, words) == (0, "")
    assert lines == [
        "step=keep kind=folder",
        f"step=keep status=ok release={RELEASE} files=18 bytes={size} new=18 same=0",
    ]
    assert held(tmp_path / "store" / PREFIX) == held(out)
    lock = release_lock.lock_of(out, RELEASE)
    assert sorted(held(tmp_path / "store" / PREFIX)) == [file["name"] for file in lock["files"]]


def test_a_release_that_is_kept_already_is_left_as_it_is(tmp_path: Path):
    out = built(tmp_path / "made")
    keep(out, tmp_path / "store")
    before = held(tmp_path / "store")
    status, lines, _ = keep(out, tmp_path / "store")
    assert status == 0
    assert lines[-1].endswith(" new=0 same=18")
    assert held(tmp_path / "store") == before


def test_a_run_that_stopped_half_way_is_finished_by_the_next(tmp_path: Path):
    out = built(tmp_path / "made")
    keep(out, tmp_path / "store")
    (tmp_path / "store" / PREFIX / RELEASE / "manifest.json").unlink()
    status, lines, _ = keep(out, tmp_path / "store")
    assert status == 0
    assert lines[-1].endswith(" new=1 same=17")
    assert held(tmp_path / "store" / PREFIX) == held(out)


def test_a_release_is_never_written_over_and_nothing_is_kept_of_one_that_differs(
    tmp_path: Path,
):
    """Two builds under one id that differ: the second is refused, whole."""
    out = built(tmp_path / "made")
    keep(out, tmp_path / "store")
    kept = tmp_path / "store" / PREFIX / f"{RELEASE}-build" / "coverage.md"
    kept.write_bytes(kept.read_bytes() + b"\n")
    (tmp_path / "store" / PREFIX / RELEASE / "manifest.json").unlink()
    before = held(tmp_path / "store")
    status, lines, words = keep(out, tmp_path / "store")
    assert status == 1
    assert lines == [
        "step=keep kind=folder",
        f"step=keep status=refused release={RELEASE} differs=1",
    ]
    assert "never written over" in words and "new id" in words
    # Not even the file that was missing was added.
    assert held(tmp_path / "store") == before


def test_a_folder_that_would_not_be_served_is_not_kept(tmp_path: Path):
    out = built(tmp_path / "made")
    evidence = out / f"{RELEASE}-build" / "evidence.json"
    evidence.write_bytes(evidence.read_bytes() + b" ")
    status, lines, words = keep(out, tmp_path / "store")
    assert (status, lines) == (2, [])
    assert "would not be served" in words and "[build_is_as_it_was_written]" in words
    assert not (tmp_path / "store").exists()


def test_a_folder_that_holds_no_build_is_not_kept(tmp_path: Path):
    out = built(tmp_path / "made")
    for case, (release, folder) in enumerate(
        [(OTHER, out), (RELEASE, tmp_path / "nowhere"), ("Brackenhythe", out), (MADE_UP, FIXTURE)]
    ):
        status, lines, words = keep(folder, tmp_path / f"store-{case}", release)
        assert (status, lines) == (2, [])
        assert words.startswith("error: ") and "Brackenhythe" not in words
        assert not (tmp_path / f"store-{case}").exists()


def test_what_a_build_does_not_write_is_not_kept(tmp_path: Path):
    out = built(tmp_path / "made")
    (out / f"{RELEASE}-build" / "more").mkdir()
    status, lines, words = keep(out, tmp_path / "store")
    assert (status, lines) == (2, [])
    assert "a build writes files alone" in words


def test_keep_needs_a_store_of_releases_and_is_not_given_the_store_of_files(tmp_path: Path):
    out = built(tmp_path / "made")
    status, lines, words = run(
        ["keep", str(out), "--release", RELEASE], {"BURRO_STORE_FOLDER": str(tmp_path / "files")}
    )
    assert (status, lines) == (2, [])
    assert "no store of releases is named" in words
    assert not (tmp_path / "files").exists()


# Take


def test_the_release_a_committed_lock_names_is_taken_and_every_file_is_as_the_lock_says(
    tmp_path: Path,
):
    out, store, locks = kept_and_approved(tmp_path)
    status, lines, words = take(tmp_path / "taken", store, locks, "--release", RELEASE)
    lock = read_lock(locks / f"{RELEASE}.json")
    size = sum(file.bytes for file in lock.files)
    assert (status, words) == (0, "")
    assert lines == [
        "step=take kind=folder",
        f"step=take status=ok release={RELEASE} files=18 bytes={size} sha256={lock.digest()}",
    ]
    assert held(tmp_path / "taken") == held(out)
    # It is a release the service would open, with what it is served with beside it.
    assert read_served(tmp_path / "taken" / RELEASE).manifest.release_id == RELEASE
    # And it is what an image may carry.
    assert release_lock.carried(tmp_path / "taken", RELEASE, locks, io.StringIO()) == 0


def test_a_release_no_lock_names_is_not_taken(tmp_path: Path):
    out = built(tmp_path / "made")
    keep(out, tmp_path / "store")
    (tmp_path / "approved").mkdir()
    status, lines, words = take(
        tmp_path / "taken", tmp_path / "store", tmp_path / "approved", "--release", RELEASE
    )
    assert status == 1
    assert lines == [f"step=take status=missing release={RELEASE}"]
    assert "no lock names" in words and "only the founder commits one" in words
    assert not (tmp_path / "taken").exists()


def test_a_release_is_not_taken_by_the_lock_of_another(tmp_path: Path):
    _, store, locks = kept_and_approved(tmp_path)
    status, lines, _ = take(tmp_path / "taken", store, locks, "--release", OTHER)
    assert (status, lines) == (1, [f"step=take status=missing release={OTHER}"])
    # Nor by a lock that was given the name of another release.
    (locks / f"{RELEASE}.json").rename(locks / f"{OTHER}.json")
    status, lines, words = take(tmp_path / "taken", store, locks, "--release", OTHER)
    assert (status, lines) == (1, [f"step=take status=unreadable release={OTHER}"])
    assert "named for another release" in words
    assert not (tmp_path / "taken").exists()


@pytest.mark.parametrize(
    "name",
    [f"{RELEASE}/features.json", f"{RELEASE}-build/evidence.json", f"{RELEASE}-build/build.json"],
)
def test_a_release_of_which_one_byte_was_changed_is_refused_and_nothing_is_left(
    tmp_path: Path, name: str
):
    _, store, locks = kept_and_approved(tmp_path)
    kept = store / PREFIX / name
    content = kept.read_bytes()
    changed = content.replace(b"1", b"2", 1)
    assert len(changed) == len(content) and changed != content
    kept.write_bytes(changed)
    status, lines, words = take(tmp_path / "taken", store, locks, "--release", RELEASE)
    assert status == 1
    assert lines == [
        "step=take kind=folder",
        f"step=take status=differs release={RELEASE} differing=1",
    ]
    assert "is not the file the lock names" in words
    assert not (tmp_path / "taken").exists()


def test_a_release_that_lacks_a_file_of_its_lock_is_refused_and_nothing_is_left(tmp_path: Path):
    _, store, locks = kept_and_approved(tmp_path)
    (store / PREFIX / f"{RELEASE}-build" / "lock.json").unlink()
    status, lines, words = take(tmp_path / "taken", store, locks, "--release", RELEASE)
    assert (status, lines) == (2, ["step=take kind=folder"])
    assert "holds no file of that name" in words
    assert not (tmp_path / "taken").exists()


def test_a_file_the_lock_does_not_name_is_not_taken(tmp_path: Path):
    out, store, locks = kept_and_approved(tmp_path)
    (store / PREFIX / RELEASE / "travel.bin").write_bytes(CANARY.encode())
    (store / PREFIX / f"{OTHER}").mkdir()
    (store / PREFIX / f"{OTHER}" / "manifest.json").write_bytes(b"{}\n")
    assert take(tmp_path / "taken", store, locks, "--release", RELEASE)[0] == 0
    assert held(tmp_path / "taken") == held(out)


def test_a_lock_whose_hash_was_changed_takes_nothing(tmp_path: Path):
    """Whoever can write to the bucket cannot make a lock: it is committed."""
    _, store, locks = kept_and_approved(tmp_path)
    path = locks / f"{RELEASE}.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["files"][0]["sha256"] = hashlib.sha256(b"another file").hexdigest()
    path.write_text(json.dumps(document), encoding="utf-8")
    status, lines, _ = take(tmp_path / "taken", store, locks, "--release", RELEASE)
    assert status == 1 and lines[-1] == f"step=take status=differs release={RELEASE} differing=1"
    assert not (tmp_path / "taken").exists()


def test_with_no_lock_and_no_release_named_the_made_up_city_is_taken(tmp_path: Path):
    (tmp_path / "approved").mkdir()
    status, lines, words = take(tmp_path / "taken", tmp_path / "no-store", tmp_path / "approved")
    size = sum(len(content) for content in held(FIXTURE).values())
    assert (status, words) == (0, "")
    assert lines == [f"step=take status=ok release={MADE_UP} files=11 bytes={size}"]
    assert held(tmp_path / "taken") == held(FIXTURE)
    nowhere = tmp_path / "approved"
    assert release_lock.carried(tmp_path / "taken", MADE_UP, nowhere, io.StringIO()) == 0
    # It reached no store: none is there.
    assert not (tmp_path / "no-store").exists()


def test_the_made_up_city_is_taken_by_its_own_id_though_a_release_is_approved(tmp_path: Path):
    _, store, locks = kept_and_approved(tmp_path)
    status, lines, _ = take(tmp_path / "taken", store, locks, "--release", MADE_UP)
    assert status == 0 and lines[-1].startswith(f"step=take status=ok release={MADE_UP} ")
    assert held(tmp_path / "taken") == held(FIXTURE)


def test_with_a_release_approved_and_none_named_nothing_is_taken(tmp_path: Path):
    _, store, locks = kept_and_approved(tmp_path)
    status, lines, words = take(tmp_path / "taken", store, locks)
    assert (status, lines) == (2, ["step=take status=refused"])
    assert "Name the release to take with --release" in words
    assert not (tmp_path / "taken").exists()


def test_a_made_up_city_that_is_not_committed_under_that_id_is_not_taken(tmp_path: Path):
    (tmp_path / "approved").mkdir()
    status, lines, _ = take(
        tmp_path / "taken",
        tmp_path / "store",
        tmp_path / "approved",
        *("--release", "syn-2026-09-23-99"),
    )
    assert (status, lines) == (1, ["step=take status=missing release=syn-2026-09-23-99"])


def test_the_folder_a_release_is_taken_to_holds_nothing_else(tmp_path: Path):
    _, store, locks = kept_and_approved(tmp_path)
    (tmp_path / "taken" / "lon-2026-09-22-01").mkdir(parents=True)
    status, lines, words = take(tmp_path / "taken", store, locks, "--release", RELEASE)
    assert (status, lines) == (2, [])
    assert "holds something already" in words
    # An empty folder is as good as a new one.
    (tmp_path / "taken" / "lon-2026-09-22-01").rmdir()
    assert take(tmp_path / "taken", store, locks, "--release", RELEASE)[0] == 0


def test_a_release_is_never_taken_to_where_git_would_take_it_in(tmp_path: Path):
    _, store, locks = kept_and_approved(tmp_path)
    top = tmp_path / "repository"
    (top / ".git").mkdir(parents=True)
    arguments = ["take", "--release", RELEASE, "--approved", str(locks), "--root", str(top)]
    environment = {FOLDER_VARIABLE: str(store)}
    for folder in ("served", "data/approved/served", "deploy/api/release"):
        status, lines, words = run([*arguments, "--out", str(top / folder)], environment)
        assert (status, lines) == (2, [])
        assert "is never committed" in words
    for folder in ("data/releases/served", "scratch/served"):
        assert run([*arguments, "--out", str(top / folder)], environment)[0] == 0


@pytest.mark.parametrize("release", ["Brackenhythe", "lon-2026-09-23", "../lon-2026-09-23-01"])
def test_what_is_not_the_id_of_a_release_is_refused_and_not_repeated(tmp_path: Path, release: str):
    _, store, locks = kept_and_approved(tmp_path)
    status, lines, words = take(tmp_path / "taken", store, locks, "--release", release)
    assert (status, lines) == (2, [])
    assert release not in words


# What is printed


def test_every_line_the_two_steps_print_is_one_the_public_log_would_show(tmp_path: Path):
    out, store, locks = kept_and_approved(tmp_path)
    printed = [
        *keep(out, store)[1],
        *keep(out, tmp_path / "again")[1],
        *take(tmp_path / "a", store, locks, "--release", RELEASE)[1],
        *take(tmp_path / "b", store, locks, "--release", OTHER)[1],
        *take(tmp_path / "c", store, locks)[1],
        *take(tmp_path / "d", store, locks, "--release", MADE_UP)[1],
    ]
    (store / PREFIX / RELEASE / "features.json").write_bytes(b"{}\n")
    printed += [
        *take(tmp_path / "e", store, locks, "--release", RELEASE)[1],
        *keep(out, store)[1],
    ]
    assert len(printed) >= 12
    assert [line for line in printed if not is_public(line)] == []


def test_nothing_the_two_steps_say_names_a_place_or_gives_a_figure(tmp_path: Path):
    out, store, locks = kept_and_approved(tmp_path)
    names = {
        row["name"]
        for row in json.loads((out / RELEASE / "neighbourhoods.json").read_bytes())[
            "neighbourhoods"
        ]
    }
    assert len(names) == 3
    said = [keep(out, store), take(tmp_path / "taken", store, locks, "--release", RELEASE)]
    for _, lines, words in said:
        for name in names:
            assert name not in "\n".join(lines) and name not in words


def test_the_steps_are_steps_of_the_one_command_line():
    from burro_pipeline import cli as whole

    assert [step.name for step in cli.STEPS] == ["keep", "take"]
    assert {"keep", "take"} <= set(whole.STEPS)
