"""What of the panel's work may be in the repository, and what may not.

The repository is public. What a person decides at the panel on real data is kept under
`data/raw/`, which git ignores, and reaches the repository only as the copy that
`desk publish` makes, which a person reads before they commit. A release that was built
from real files is never in it.
"""

import subprocess
from pathlib import Path

import pytest
from burro_pipeline import changes
from desk import cli, server

ROOT = cli.ROOT


def tracked() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if listed.returncode != 0:
        pytest.skip("this copy is no repository")
    return [name for name in listed.stdout.decode().split("\0") if name]


def ignored(name: str) -> bool:
    asked = subprocess.run(
        ["git", "check-ignore", "-q", name], cwd=ROOT, capture_output=True, check=False
    )
    return asked.returncode == 0


def test_what_is_decided_at_the_desk_is_kept_where_git_does_not_look():
    for data in (cli.MADE_UP, cli.REAL):
        kept = data / "decisions" / server.CHANGES / "r1.jsonl"
        assert ignored(str(kept.relative_to(ROOT))), kept
    assert ignored("data/releases/lon-2026-09-25-41/catalogue.json")


def test_a_file_of_changes_is_in_the_repository_only_as_the_copy_that_was_published():
    found = [name for name in tracked() if f"/{server.CHANGES}/" in f"/{name}"]
    files = [name for name in found if name.endswith(".jsonl")]
    assert [name for name in files if not name.startswith("gazetteer/")] == []


def test_every_file_of_changes_in_the_repository_is_one_a_build_can_read():
    """So it names a reviewer by a label and never by a name, says the day and never the
    hour, and holds no figure of a place: the reader refuses each."""
    for name in tracked():
        if name.startswith("gazetteer/") and f"/{server.CHANGES}/" in name:
            lines = changes.read((ROOT / name).read_bytes())
            assert {line.by for line in lines} == {Path(name).stem}, name


def test_no_release_of_real_files_is_in_the_repository():
    held = [
        name for name in tracked() if "/releases/" in f"/{name}" or name.startswith("data/raw/")
    ]
    assert held == []
    # Every release that is in the repository is of the made-up city, and says so by its id.
    fixtures = [name for name in tracked() if name.startswith("data/") and "manifest.json" in name]
    assert fixtures and all(name.startswith("data/fixtures/") for name in fixtures)
    assert all(Path(name).parent.name.startswith("syn-") for name in fixtures)
