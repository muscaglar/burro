"""What is read of a repository: the commit that is checked out, and whether the files are it.

The code reads git's own files and runs no program. The tests make each
repository with git itself, in a folder of their own, and hold what the code
reads to what git says. Every file is made up, and nothing is fetched or pushed.
"""

import subprocess
from pathlib import Path

import pytest
from burro_pipeline.evidence.repository import (
    LARGEST_OBJECT,
    CheckedOut,
    NotRead,
    checked_out,
    held,
    holds,
    top_of,
    tracks,
)

from .conftest import FILES, write
from .support import CANARY, GIT, git

pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to make a repository to read")


@pytest.fixture
def root(repository: Path) -> Path:
    return repository


def as_git_has_it(root: Path) -> tuple[str, bool]:
    """The commit git says is checked out, and whether git says a tracked file has changes."""
    said = git(root, "status", "--porcelain=v2", "--branch", "--untracked-files=no").splitlines()
    commit = next(line.split()[2] for line in said if line.startswith("# branch.oid "))
    return commit, any(not line.startswith("#") for line in said)


def clean(root: Path) -> CheckedOut:
    """What is read of a working copy that git itself calls clean, but for untracked files."""
    commit, changes = as_git_has_it(root)
    assert not changes
    found = checked_out(root)
    assert found == CheckedOut(commit, changed=0, staged=False)
    assert found.clean and found.in_words() == ""
    return found


def dirty(root: Path, changed: int, staged: bool) -> CheckedOut:
    """What is read of a working copy that git itself says has changes."""
    commit, changes = as_git_has_it(root)
    assert changes
    found = checked_out(root)
    assert found == CheckedOut(commit, changed, staged)
    assert not found.clean
    assert CANARY not in found.in_words() and "\n" not in found.in_words()
    return found


# The commit.


def test_the_commit_is_the_one_that_is_checked_out(root: Path):
    first = clean(root).commit
    write(root, {"a/first.py": "FIRST = 11\n"})
    git(root, "commit", "--quiet", "--all", "--message", "Change one file")
    second = clean(root).commit
    assert first != second and len(second) == 40


def test_a_folder_that_is_in_no_working_copy_is_not_read(tmp_path: Path, root: Path):
    assert top_of(root) == root.resolve()
    assert top_of(tmp_path) is None and top_of(tmp_path / "nowhere" / "deeper") is None
    with pytest.raises(NotRead) as caught:
        checked_out(tmp_path)
    assert str(caught.value) == "the folder is in no working copy"
    assert str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize("inside", ["a/deeper", "a/not/there/yet"])
def test_a_folder_inside_a_working_copy_is_read_as_the_working_copy(root: Path, inside: str):
    """Git itself looks in the folder it is run in and in every folder above it."""
    assert top_of(root / inside) == root.resolve()
    assert checked_out(root / inside) == clean(root)
    # A change anywhere in the working copy is seen from a folder that does not hold it.
    write(root, {"README.md": "changed\n"})
    assert checked_out(root / inside) == dirty(root, changed=1, staged=False)
    git(root, "add", "README.md")
    assert checked_out(root / inside) == dirty(root, changed=0, staged=True)
    # An object is read from there too.
    commit = git(root, "rev-parse", "HEAD")
    assert held(root / inside, commit) == held(root, commit)


def test_a_folder_reached_by_a_link_is_read_as_the_working_copy_it_is_in(
    root: Path, tmp_path: Path
):
    (tmp_path / "way-in").symlink_to(root / "a" / "deeper", target_is_directory=True)
    assert top_of(tmp_path / "way-in") == root.resolve()
    assert checked_out(tmp_path / "way-in") == clean(root)


def test_the_nearest_working_copy_above_a_folder_is_the_one_that_is_read(
    root: Path, tmp_path: Path
):
    """A second working copy kept inside the first, which the first does not track."""
    other = root / "scratch" / "other"
    git(root, "worktree", "add", "--quiet", "-b", "other", str(other))
    write(other, {"a/first.py": "FIRST = 3\n"})
    git(other, "commit", "--quiet", "--all", "--message", "Change it in the other copy")
    assert top_of(other / "a" / "deeper") == other.resolve()
    assert checked_out(other / "a" / "deeper").commit == git(other, "rev-parse", "HEAD")
    assert checked_out(root / "a").commit == git(root, "rev-parse", "HEAD")
    assert checked_out(other / "a").commit != checked_out(root / "a").commit


def test_a_folder_named_for_git_that_holds_no_repository_is_refused_and_not_passed_by(
    root: Path,
):
    """What stands nearest is what is read. Nothing above it is tried in its place."""
    (root / "a" / ".git").mkdir()
    assert top_of(root / "a" / "deeper") == (root / "a").resolve()
    refusal(root / "a" / "deeper")
    clean(root)


def test_a_commit_is_read_by_itself_with_no_branch(root: Path):
    git(root, "checkout", "--quiet", "--detach")
    clean(root)


def test_a_commit_is_read_after_git_has_packed_the_repository(root: Path):
    for number in range(3):
        write(root, {"a/first.py": f"FIRST = {number}\n"})
        git(root, "commit", "--quiet", "--all", "--message", f"Change {number}")
    git(root, "gc", "--quiet", "--aggressive", "--prune=now")
    assert not list((root / ".git" / "refs" / "heads").iterdir())
    assert list((root / ".git" / "objects" / "pack").glob("*.pack"))
    clean(root)


def test_a_second_working_copy_of_a_repository_is_read_as_its_own(root: Path, tmp_path: Path):
    other = tmp_path / "other"
    git(root, "worktree", "add", "--quiet", "-b", "other", str(other))
    assert (other / ".git").is_file()
    write(other, {"a/first.py": "FIRST = 3\n"})
    git(other, "commit", "--quiet", "--all", "--message", "Change it in the other copy")
    assert clean(other).commit != clean(root).commit
    write(other, {"a0": "changed\n"})
    dirty(other, changed=1, staged=False)
    clean(root)


def test_a_copy_of_the_last_commit_alone_is_read(root: Path, tmp_path: Path):
    """As a hosted run has it: one commit, in a pack, on a branch made at checkout."""
    write(root, {"a/first.py": "FIRST = 4\n"})
    git(root, "commit", "--quiet", "--all", "--message", "One more")
    copy = tmp_path / "copy"
    git(tmp_path, "clone", "--quiet", "--depth", "1", f"file://{root}", str(copy))
    assert clean(copy).commit == clean(root).commit


# The files.


def test_a_tracked_file_that_was_changed_is_found(root: Path):
    write(root, {"a/deeper/second.py": "SECOND = 3\n", f"data/{CANARY}.csv": "name\n"})
    found = dirty(root, changed=2, staged=False)
    assert found.in_words() == "2 tracked files are not as git last took them"


def test_a_tracked_file_that_is_gone_is_found(root: Path):
    (root / "a.b").unlink()
    assert dirty(root, changed=1, staged=False).in_words() == (
        "1 tracked file is not as git last took it"
    )


def test_a_change_that_is_staged_is_found_though_the_files_are_as_the_index_has_them(root: Path):
    write(root, {"a/first.py": "FIRST = 5\n"})
    git(root, "add", "a/first.py")
    found = dirty(root, changed=0, staged=True)
    assert found.in_words() == "what is staged is not what is committed"


def test_a_file_that_is_staged_and_new_is_found(root: Path):
    write(root, {"a/third.py": "THIRD = 3\n"})
    git(root, "add", "a/third.py")
    dirty(root, changed=0, staged=True)


def test_a_file_taken_out_of_the_index_is_found(root: Path):
    git(root, "rm", "--quiet", "--cached", "a0")
    dirty(root, changed=0, staged=True)


def test_a_branch_moved_back_under_the_files_is_found(root: Path):
    """The index and the files agree, and both are a commit ahead of the one checked out."""
    write(root, {"a/first.py": "FIRST = 6\n"})
    git(root, "commit", "--quiet", "--all", "--message", "One more")
    git(root, "reset", "--quiet", "--soft", "HEAD~1")
    dirty(root, changed=0, staged=True)


def test_a_file_changed_and_staged_and_changed_again_is_found_both_ways(root: Path):
    write(root, {"a/first.py": "FIRST = 7\n"})
    git(root, "add", "a/first.py")
    write(root, {"a/first.py": "FIRST = 8\n"})
    found = dirty(root, changed=1, staged=True)
    assert found.in_words() == (
        "1 tracked file is not as git last took it; what is staged is not what is committed"
    )


def test_a_file_that_may_now_be_run_is_found(root: Path):
    (root / "a0").chmod(0o755)
    dirty(root, changed=1, staged=False)
    (root / "a0").chmod(0o644)
    (root / "run.sh").chmod(0o644)
    dirty(root, changed=1, staged=False)


def test_a_link_that_leads_elsewhere_is_found(root: Path):
    (root / "latest").unlink()
    (root / "latest").symlink_to("a/deeper/second.py")
    dirty(root, changed=1, staged=False)
    (root / "latest").unlink()
    (root / "latest").write_text("a/first.py", encoding="utf-8")
    dirty(root, changed=1, staged=False)


def test_a_merge_that_is_not_settled_is_found(root: Path):
    git(root, "checkout", "--quiet", "-b", "other")
    write(root, {"a/first.py": "FIRST = 9\n"})
    git(root, "commit", "--quiet", "--all", "--message", "Nine")
    git(root, "checkout", "--quiet", "main")
    write(root, {"a/first.py": "FIRST = 10\n"})
    git(root, "commit", "--quiet", "--all", "--message", "Ten")
    with pytest.raises(subprocess.CalledProcessError):
        git(root, "merge", "--quiet", "other")
    found = checked_out(root)
    assert found.staged and found.changed and not found.clean


def test_a_file_git_does_not_track_is_not_looked_at(root: Path):
    write(root, {"scratch/listing.json": "{}", "a/not_added.py": "NOT = 0\n"})
    assert git(root, "status", "--porcelain") != ""
    clean(root)


@pytest.mark.parametrize("version", ["2", "3", "4"])
def test_the_index_is_read_in_each_form_git_writes_it_in(root: Path, version: str):
    git(root, "update-index", "--index-version", version)
    if version == "3":
        # Only an entry with more to say of it makes git write the third form.
        write(root, {"a/later.py": "LATER = 0\n"})
        git(root, "add", "--intent-to-add", "a/later.py")
        assert (root / ".git" / "index").read_bytes()[4:8] == b"\0\0\0\3"
        assert checked_out(root).staged
        git(root, "rm", "--quiet", "--cached", "a/later.py")
    else:
        assert (root / ".git" / "index").read_bytes()[4:8] == bytes([0, 0, 0, int(version)])
    clean(root)
    write(root, {"a/deeper/second.py": "SECOND = 4\n"})
    dirty(root, changed=1, staged=False)


def test_the_tree_of_the_index_is_the_tree_git_would_write(root: Path):
    """Folders and files in git's own order, which is not the order of their names."""
    names = ("x/b/c", "x/b/c-d", "x/b/c.d/e", "x/b-c", "x/b.c", "x/b0", "x/b_", "x-/y", "x./y")
    write(root, dict.fromkeys(names, "made up\n"))
    git(root, "add", "--all")
    assert checked_out(root).staged
    git(root, "commit", "--quiet", "--message", "Names that sort apart")
    # A folder sorts as if its name ended in a slash: after `b-c` and `b.c`, before `b0`.
    listed = git(root, "ls-tree", "--name-only", "HEAD:x").splitlines()
    assert listed == ["b-c", "b.c", "b", "b0", "b_"] and listed != sorted(listed)
    clean(root)


# Objects, loose and in a pack.


def every_object(root: Path) -> dict[str, tuple[str, bytes]]:
    """Every object of a repository as git gives it, asked for in one go."""
    done = subprocess.run(  # noqa: S603  git, with words that are written here
        [GIT or "git", "-C", str(root), "cat-file", "--batch-all-objects", "--batch"],
        capture_output=True,
        check=True,
        close_fds=False,
    )
    found: dict[str, tuple[str, bytes]] = {}
    left = done.stdout
    while left:
        head, _, left = left.partition(b"\n")
        oid, kind, size = head.decode("ascii").split()
        found[oid] = (kind, left[: int(size)])
        left = left[int(size) + 1 :]
    return found


def kept_as_changes(root: Path) -> list[str]:
    """The objects a pack keeps as changes to another, by what `verify-pack` says of each."""
    found: list[str] = []
    for index in (root / ".git" / "objects" / "pack").glob("*.idx"):
        for line in git(root, "verify-pack", "--verbose", str(index)).splitlines():
            parts = line.split()
            if len(parts) == 7 and len(parts[0]) == 40:
                found.append(parts[1])
    return found


@pytest.mark.parametrize("by_offset", ["true", "false"], ids=["by offset", "by name"])
def test_every_object_is_read_as_git_reads_it_whole_or_as_changes(root: Path, by_offset: str):
    story = "\n".join(f"Line {number} of a long message, made up." for number in range(40))
    for number in range(6):
        write(root, {"a/first.py": "".join(f"LINE_{n} = {n}\n" for n in range(60 + number))})
        git(root, "commit", "--quiet", "--all", "--message", f"Change {number}\n\n{story}")
    git(root, "config", "repack.useDeltaBaseOffset", by_offset)
    git(root, "repack", "-a", "-d", "-f", "--quiet", "--window=50", "--depth=50")
    assert not [path for path in (root / ".git" / "objects").glob("??") if any(path.iterdir())]
    changes = kept_as_changes(root)
    assert "commit" in changes and "blob" in changes
    objects = every_object(root)
    assert len(objects) > 20
    for oid, as_git_gives_it in objects.items():
        assert held(root, oid) == as_git_gives_it
    clean(root)


def test_an_object_that_is_not_there_is_not_read(root: Path):
    with pytest.raises(NotRead, match="is not in the repository"):
        held(root, "0" * 40)
    git(root, "gc", "--quiet", "--prune=now")
    with pytest.raises(NotRead, match="is not in the repository"):
        held(root, "f" * 40)


def test_an_object_far_larger_than_a_commit_is_not_read(root: Path):
    (root / "large.bin").write_bytes(b"\0" * (LARGEST_OBJECT + 1))
    git(root, "add", "large.bin")
    oid = git(root, "rev-parse", ":large.bin")
    with pytest.raises(NotRead, match="too large"):
        held(root, oid)
    git(root, "commit", "--quiet", "--message", "A large file")
    # The file is still hashed, a piece at a time or whole, and found to be as it was taken.
    clean(root)


# What is refused, and never guessed.


def refusal(root: Path) -> str:
    with pytest.raises(NotRead) as caught:
        checked_out(root)
    said = str(caught.value)
    assert CANARY not in said and str(root) not in said and "\n" not in said
    return said


def test_a_repository_with_no_commit_is_refused(tmp_path: Path):
    git(tmp_path, "init", "--quiet", "--initial-branch", "main")
    assert refusal(tmp_path) == "the branch that is checked out has no commit"


def test_a_repository_whose_hashes_are_not_sha1_is_refused(tmp_path: Path):
    git(tmp_path, "init", "--quiet", "--initial-branch", "main", "--object-format=sha256")
    write(tmp_path, FILES)
    git(tmp_path, "add", "--all")
    git(tmp_path, "commit", "--quiet", "--message", "Made up")
    assert refusal(tmp_path) == "its hashes are not SHA-1"


def test_a_repository_that_keeps_its_branches_as_a_table_is_refused(tmp_path: Path):
    try:
        git(tmp_path, "init", "--quiet", "--initial-branch", "main", "--ref-format=reftable")
    except subprocess.CalledProcessError:
        pytest.skip("this git keeps no branches as a table")
    write(tmp_path, FILES)
    git(tmp_path, "add", "--all")
    git(tmp_path, "commit", "--quiet", "--message", "Made up")
    assert refusal(tmp_path) == "its branches are kept as a table"


def test_a_repository_inside_the_repository_is_refused(root: Path, tmp_path: Path):
    inner = tmp_path / "inner"
    inner.mkdir()
    git(inner, "init", "--quiet", "--initial-branch", "main")
    write(inner, {"README.md": "made up\n"})
    git(inner, "add", "--all")
    git(inner, "commit", "--quiet", "--message", "Made up")
    git(root, "-c", "protocol.file.allow=always", "submodule", "--quiet", "add", str(inner), "in")
    git(root, "commit", "--quiet", "--all", "--message", "A repository inside")
    assert refusal(root) == "the repository holds another repository"


def test_an_index_that_is_split_in_two_is_refused(root: Path):
    git(root, "update-index", "--split-index")
    assert refusal(root) == "the index is split in two"


@pytest.mark.parametrize(
    ("name", "held_there"),
    [
        ("HEAD", f"ref: refs/heads/../../{CANARY}\n"),
        ("HEAD", f"{CANARY}\n"),
        ("HEAD", "ref: /etc/passwd\n"),
        ("index", f"{CANARY}"),
        ("index", "DIRC" + "\0" * 3 + "\2" + "\0" * 3 + "\7"),
    ],
    ids=["a way out", "no commit", "a path", "no index", "an index cut short"],
)
def test_a_repository_that_is_not_as_git_writes_it_is_refused(
    root: Path, name: str, held_there: str
):
    (root / ".git" / name).write_text(held_there, encoding="utf-8")
    refusal(root)


def test_a_commit_that_is_not_in_the_repository_is_refused(root: Path):
    (root / ".git" / "refs" / "heads" / "main").write_text("0" * 40 + "\n", encoding="utf-8")
    assert refusal(root) == "the commit that is checked out is not in the repository"


# Whether a file is one the repository holds.


def test_a_file_the_repository_tracks_and_that_is_as_it_tracks_it_is_held(root: Path):
    assert holds(root, root / "a" / "first.py") is True
    assert holds(root / "a", root / "a" / "first.py") is True
    # It is named as it is, and as it is reached from a folder beside it.
    assert holds(root, root / "a" / ".." / "a" / "first.py") is True


def test_a_file_that_was_changed_since_git_took_it_is_not_held(root: Path):
    (root / "a" / "first.py").write_text(f"# {CANARY}\n", encoding="utf-8")
    assert holds(root, root / "a" / "first.py") is False


def test_a_file_git_does_not_track_is_not_held(root: Path):
    (root / "a" / "by-hand.py").write_text("# made up\n", encoding="utf-8")
    assert holds(root, root / "a" / "by-hand.py") is False
    assert holds(root, root / "a" / "nowhere.py") is False
    assert holds(root, root / "a") is False


def test_a_link_is_not_held_though_the_file_it_leads_to_is(root: Path):
    assert (root / "latest").is_symlink()
    assert holds(root, root / "latest") is False
    (root / "b").symlink_to(root / "a")
    assert holds(root, root / "b" / "first.py") is True, (
        "the file is, by whatever way it is reached"
    )


def test_a_file_outside_the_working_copy_is_not_held(root: Path, tmp_path: Path):
    outside = tmp_path / "outside.py"
    outside.write_bytes((root / "a" / "first.py").read_bytes())
    assert holds(root, outside) is False
    (root / "inside.py").symlink_to(outside)
    assert holds(root, root / "inside.py") is False


def test_no_file_is_held_where_there_is_no_working_copy(tmp_path: Path):
    (tmp_path / "first.py").write_text("# made up\n", encoding="utf-8")
    assert holds(tmp_path, tmp_path / "first.py") is False


def test_a_file_that_is_staged_and_not_committed_is_held_and_the_lock_refuses_the_tree(
    root: Path,
):
    # `holds` says that the file is as the index has it. That the index is what was
    # committed is `checked_out`'s to say, and a build asks both.
    (root / "a" / "first.py").write_text("# staged\n", encoding="utf-8")
    git(root, "add", "--all")
    assert holds(root, root / "a" / "first.py") is True
    assert checked_out(root).clean is False


def test_what_was_read_of_a_file_is_what_is_held_to_the_repository(root: Path):
    path = root / "a" / "first.py"
    read = path.read_bytes()
    assert holds(root, path, read) is True
    assert holds(root, path, read + b" ") is False
    assert holds(root, path, b"") is False


# Whether the repository tracks a file, whatever is there now.


def test_a_file_the_repository_tracks_is_tracked_whether_or_not_it_is_there_or_as_it_was(
    root: Path,
):
    path = root / "a" / "first.py"
    assert tracks(root, path) is True and tracks(root / "a", path) is True
    assert tracks(root, root / "a" / ".." / "a" / "first.py") is True
    path.write_text(f"# {CANARY}\n", encoding="utf-8")
    assert tracks(root, path) is True and holds(root, path) is False
    path.unlink()
    assert tracks(root, path) is True and holds(root, path) is False


def test_a_file_the_repository_does_not_track_is_not_tracked(root: Path):
    (root / "a" / "by-hand.py").write_text("# made up\n", encoding="utf-8")
    assert tracks(root, root / "a" / "by-hand.py") is False
    assert tracks(root, root / "a" / "nowhere.py") is False
    assert tracks(root, root / "nowhere" / "deeper" / "first.py") is False
    assert tracks(root, root / "a") is False


def test_a_file_outside_the_working_copy_or_in_none_is_not_tracked(root: Path, tmp_path: Path):
    outside = tmp_path / "outside" / "first.py"
    outside.parent.mkdir()
    outside.write_bytes((root / "a" / "first.py").read_bytes())
    assert tracks(root, outside) is False
    assert tracks(outside.parent, outside) is False
