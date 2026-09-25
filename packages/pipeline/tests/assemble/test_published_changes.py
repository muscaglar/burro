"""A build that is given the founder's published file of changes, where the repository holds one.

A hosted run builds from a checkout of the repository. It is given one place to look:
where the desk publishes the founder's file. Where the repository tracks a file there,
the build takes it as `--changes` takes one. Where it tracks none, the build is what it
is with no file, byte for byte. It never reads a file the repository does not track.

The town is Quillhaven and Tallowgate, which do not exist. Every reason is made up.
"""

import hashlib
import io
import json
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
from burro_core.release import LOCK
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.release.read import read_served

from ..cells.support import held
from ..evidence.support import GIT, git
from .published import PUBLISHED_AT, Published, published
from .support import Made, made_once
from .test_changes_written_by_hand import NOT_PUBLISHED, a_line, a_share_moved

pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to publish a file of changes")

Printed = pytest.CaptureFixture[str]
OPTION = "--published-changes"


def quietly(run: Callable[[], int]) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return run()


def where_published(kept: Published, name: str = "r1.jsonl") -> tuple[str, ...]:
    """What a hosted build is handed: the place, the repository it is in, and its commit."""
    place = str(kept.root / PUBLISHED_AT / name)
    return (OPTION, place, "--root", str(kept.root), "--commit", kept.commit)


def with_no_file(folder: Path) -> Published:
    """A repository that tracks no file of changes, as the repository does today."""
    kept = published(folder, a_line(), name="notes.txt")
    assert not (kept.root / PUBLISHED_AT / "r1.jsonl").exists()
    return kept


UNREADABLE = "step=assemble status=unreadable"


def stopped(found: Made, capsys: Printed, *arguments: str) -> tuple[str, str]:
    """The line and the words of a build that stopped, and wrote nothing."""
    assert found.run(*arguments) == 2
    said = capsys.readouterr()
    assert "Zzyzx" not in said.out + said.err, "a refusal never repeats a reason"
    assert "Traceback" not in said.err and not found.out.exists(), "nothing was written"
    (line,) = said.out.splitlines()
    return line, said.err


def test_where_the_repository_tracks_no_file_the_build_is_what_it_is_with_none(
    tmp_path: Path, capsys: Printed
):
    kept = with_no_file(tmp_path)
    build = made_once(tmp_path / "build")
    plain = ("--root", str(kept.root), "--commit", kept.commit)
    assert build.run(*plain, out=tmp_path / "as-it-was") == 0
    before = capsys.readouterr().out
    assert build.run(*where_published(kept), out=tmp_path / "given-the-place") == 0
    after = capsys.readouterr().out
    assert held(tmp_path / "given-the-place") == held(tmp_path / "as-it-was")
    assert after == before and "step=changes" not in after


def test_where_the_repository_tracks_the_file_it_is_built_as_a_build_by_hand_builds_it(
    tmp_path: Path, capsys: Printed
):
    kept = published(tmp_path, a_line())
    build = made_once(tmp_path / "build")
    assert build.run(*kept.arguments(), out=tmp_path / "by-hand") == 0
    by_hand = capsys.readouterr().out
    assert build.run(*where_published(kept), out=tmp_path / "hosted") == 0
    hosted = capsys.readouterr().out
    assert held(tmp_path / "hosted") == held(tmp_path / "by-hand")
    assert hosted == by_hand and "step=changes status=ok" in hosted
    sha256 = hashlib.sha256(kept.path.read_bytes()).hexdigest()
    release = read_served(tmp_path / "hosted" / build.release.name)
    assert release.manifest.changes_sha256 == sha256
    lock = json.loads((tmp_path / "hosted" / build.beside.name / LOCK).read_bytes())
    assert [one["sha256"] for one in lock["inputs"] if one["name"] == "changes/r1.jsonl"] == [
        sha256
    ]


def test_a_build_with_the_file_is_not_the_build_with_none(tmp_path: Path):
    kept = published(tmp_path, a_line())
    none = with_no_file(tmp_path / "none")
    build = made_once(tmp_path / "build")
    assert quietly(lambda: build.run(*where_published(kept), out=tmp_path / "with")) == 0
    assert quietly(lambda: build.run(*where_published(none), out=tmp_path / "without")) == 0
    assert held(tmp_path / "with") != held(tmp_path / "without")


def a_file_nobody_published(kept: Published) -> None:
    """A file written where the desk publishes, that the repository was never given."""
    place = kept.root / PUBLISHED_AT / "r1.jsonl"
    place.write_text(json.dumps(a_line()) + "\n", encoding="utf-8")


def a_link_to_a_file(kept: Published) -> None:
    elsewhere = kept.root.parent / "elsewhere.jsonl"
    elsewhere.write_text(json.dumps(a_line()) + "\n", encoding="utf-8")
    (kept.root / PUBLISHED_AT / "r1.jsonl").symlink_to(elsewhere)


def a_folder_in_its_place(kept: Published) -> None:
    (kept.root / PUBLISHED_AT / "r1.jsonl").mkdir()


NOT_TRACKED = [a_file_nobody_published, a_link_to_a_file, a_folder_in_its_place]


@pytest.mark.parametrize("there", NOT_TRACKED)
def test_what_stands_there_and_is_not_tracked_is_never_read_and_stops_the_build(
    tmp_path: Path, capsys: Printed, there: Callable[[Published], None]
):
    kept = with_no_file(tmp_path)
    there(kept)
    line, words = stopped(made_once(tmp_path / "build"), capsys, *where_published(kept))
    assert line == UNREADABLE and words.startswith(NOT_PUBLISHED)


def changed_since(kept: Published) -> None:
    kept.path.write_bytes(a_share_moved(kept.path.read_bytes()))


def taken_away(kept: Published) -> None:
    kept.path.unlink()


def staged_and_not_committed(kept: Published) -> None:
    changed_since(kept)
    git(kept.root, "add", "--all")


@pytest.mark.parametrize(
    ("since", "line", "words"),
    [
        (changed_since, UNREADABLE, NOT_PUBLISHED),
        (taken_away, UNREADABLE, "error: the file of changes cannot be read from the disk"),
        # The file is as the index has it, and the index is not what was committed: the
        # lock of the build refuses the tree, as it does of a build by hand.
        (staged_and_not_committed, "step=assemble status=refused tree_has_no_changes=1", ""),
    ],
)
def test_a_file_that_is_tracked_and_is_not_as_it_was_committed_stops_the_build(
    tmp_path: Path, capsys: Printed, since: Callable[[Published], None], line: str, words: str
):
    kept = published(tmp_path, a_line())
    since(kept)
    said = stopped(made_once(tmp_path / "build"), capsys, *where_published(kept))
    assert said[0] == line and said[1].startswith(words)


def test_the_place_is_the_founders_and_no_other_reviewers(tmp_path: Path, capsys: Printed):
    """A run never chooses between two files: it is given one place, and it is the founder's."""
    kept = published(tmp_path, a_line(by="r2"), name="r2.jsonl")
    build = made_once(tmp_path / "build")
    line, words = stopped(build, capsys, *where_published(kept, "r2.jsonl"))
    assert line == UNREADABLE and "is named r1.jsonl" in words
    # With the founder's place named, another reviewer's file beside it is never read.
    assert quietly(lambda: build.run(*where_published(kept), out=tmp_path / "out")) == 0
    lock = json.loads((tmp_path / "out" / build.beside.name / LOCK).read_bytes())
    assert not [one for one in lock["inputs"] if one["name"].startswith("changes/")]


def test_a_build_is_given_a_file_or_the_place_of_one_and_never_both(
    tmp_path: Path, capsys: Printed
):
    kept = published(tmp_path, a_line())
    build = made_once(tmp_path / "build")
    with pytest.raises(SystemExit) as stop:
        assemble.main(build.arguments(*kept.arguments(), OPTION, str(kept.path)), {})
    assert stop.value.code == 2
    assert "Zzyzx" not in capsys.readouterr().err and not build.out.exists()


def test_where_there_is_no_repository_and_no_file_the_build_is_what_it_is_with_none(
    tmp_path: Path,
):
    build = made_once(tmp_path / "build")
    place = str(tmp_path / "nowhere" / "r1.jsonl")
    assert quietly(lambda: build.run(out=tmp_path / "as-it-was")) == 0
    assert quietly(lambda: build.run(OPTION, place, out=tmp_path / "given-the-place")) == 0
    assert held(tmp_path / "given-the-place") == held(tmp_path / "as-it-was")
