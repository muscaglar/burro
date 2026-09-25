"""A file of changes is held to the copy that was published, whatever store a build reads.

A build on a person's own machine reads a folder, and a hosted build reads a bucket. The
file of changes is read before either is looked for, so a file that was written by hand is
refused the same way from each, and where no store is named at all. The store here stands
in for a bucket: behind it is a folder, and nothing reaches a network.

The town is Quillhaven and Tallowgate, which do not exist. Every reason is made up.
"""

import hashlib
import io
import json
from collections.abc import Callable, Mapping
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.fetch.store import FOLDER_VARIABLE, Store
from burro_pipeline.release.read import read_served

from ..cells.support import held
from ..evidence.support import GIT
from .published import Published, published
from .support import Made, made
from .test_changes_written_by_hand import NOT_PUBLISHED, a_line, a_share_moved
from .test_preview_from_an_object_store import A_BUCKET, from_a_bucket

pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to publish a file of changes")

Printed = pytest.CaptureFixture[str]


def a_folder(build: Made) -> dict[str, str]:
    return {FOLDER_VARIABLE: str(build.store)}


def a_bucket(_: Made) -> dict[str, str]:
    return dict(A_BUCKET)


def no_store(_: Made) -> dict[str, str]:
    return {}


def in_no_repository(folder: Path) -> tuple[str, ...]:
    path = folder / "by-hand" / "r1.jsonl"
    path.parent.mkdir()
    path.write_text(json.dumps(a_line()) + "\n", encoding="utf-8")
    return ("--changes", str(path))


def changed_since_it_was_published(folder: Path) -> tuple[str, ...]:
    kept: Published = published(folder, a_line())
    kept.path.write_bytes(a_share_moved(kept.path.read_bytes()))
    return kept.arguments()


@pytest.mark.parametrize("named", [a_folder, a_bucket, no_store])
@pytest.mark.parametrize("by_hand", [in_no_repository, changed_since_it_was_published])
def test_a_file_that_is_not_the_published_copy_is_refused_before_any_store_is_looked_for(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Printed,
    named: Callable[[Made], dict[str, str]],
    by_hand: Callable[[Path], tuple[str, ...]],
):
    build = made(tmp_path / "build")
    looked_for: list[Mapping[str, str]] = []

    def never(environment: Mapping[str, str]) -> Store:
        looked_for.append(environment)
        raise AssertionError("the store was looked for before the file of changes was held")

    monkeypatch.setattr(assemble, "store_from_environment", never)
    assert assemble.main(build.arguments(*by_hand(tmp_path)), named(build)) == 2
    said = capsys.readouterr()
    assert said.err.startswith(NOT_PUBLISHED)
    assert said.out.splitlines() == ["step=assemble status=unreadable"]
    assert looked_for == [] and not build.out.exists()
    assert "Zzyzx" not in said.out + said.err, "a refusal never repeats a reason"
    assert "made-up-secret" not in said.out + said.err


def test_the_published_copy_is_built_from_a_bucket_as_it_is_from_a_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    kept = published(tmp_path, a_line())
    build = made(tmp_path / "build")
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert build.run(*kept.arguments(), out=tmp_path / "from-a-folder") == 0
        status, store = from_a_bucket(
            build, monkeypatch, *kept.arguments(), out=tmp_path / "from-a-bucket"
        )
    assert status == 0 and store.asked, "every file was copied out of the bucket"
    assert held(tmp_path / "from-a-bucket") == held(tmp_path / "from-a-folder")
    release = read_served(tmp_path / "from-a-bucket" / build.release.name)
    sha256 = hashlib.sha256(kept.path.read_bytes()).hexdigest()
    assert release.manifest.changes_sha256 == sha256
    # The file of changes is no file of the store, so it is never asked of the bucket.
    assert sha256 not in store.asked
