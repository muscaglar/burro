"""The step `preview`, where the store is reached over a network, as a bucket is.

A hosted run builds from a bucket. A file is read with no socket open, so
every file of the build is copied out of the store before any is read. The
store here stands in for a bucket: behind it is a folder, and it answers only
while a socket may be made. Nothing reaches a network, and every file is made up.
"""

import http.client
import socket
import ssl
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NoReturn, cast

import pytest
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.evidence.lock import read_lock
from burro_pipeline.fetch.run import Why
from burro_pipeline.fetch.store import Store
from public_log import is_public

from ..cells.support import held
from ..test_inputs import Reached, in_place_of_the_environment
from .support import RELEASE, Made, files, made

Printed = pytest.CaptureFixture[str]
# What names an object store. None of it is asked anything: the store is put in its place.
A_BUCKET = {
    "BURRO_STORE_ENDPOINT": "https://made-up.example",
    "BURRO_STORE_BUCKET": "made-up-bucket",
    "BURRO_STORE_KEY_ID": "made-up-key-id",
    "BURRO_STORE_SECRET": "made-up-secret",
}


def from_a_bucket(
    build: Made, patch: pytest.MonkeyPatch, *more: str, out: Path | None = None
) -> tuple[int, Reached]:
    """Run the step on a made-up build whose store is reached as a bucket is."""
    store = Reached(build.store)
    patch.setattr(assemble, "store_from_environment", in_place_of_the_environment(store))
    return assemble.main(build.arguments(*more, out=out), A_BUCKET), store


def lines_of(capsys: Printed) -> tuple[list[str], str]:
    printed = capsys.readouterr()
    return printed.out.splitlines(), printed.err


def test_a_build_from_a_bucket_copies_every_file_out_before_it_reads_any(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    build = made(tmp_path)
    status, store = from_a_bucket(build, monkeypatch)
    said, _ = lines_of(capsys)
    assert status == 0
    lock = read_lock(build.beside / "lock.json")
    # Every file of the lock was asked for once, and none while a file was read: the
    # store answers only while a socket may be made, and the build went on to its end.
    assert sorted(store.asked) == sorted(locked.sha256 for locked in lock.inputs)
    size = sum(locked.bytes for locked in lock.inputs)
    assert said[0].startswith(f"step=seal status=ok release={RELEASE} inputs={len(lock.inputs)} ")
    assert said[1] == (
        f"step=store status=ok kind=object_store files={len(lock.inputs)} bytes={size}"
    )
    assert all(is_public(line) for line in said)


def test_a_build_from_a_bucket_is_the_bytes_of_a_build_from_a_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    build = made(tmp_path)
    assert build.run(out=tmp_path / "from-a-folder") == 0
    assert from_a_bucket(build, monkeypatch, out=tmp_path / "from-a-bucket")[0] == 0
    assert held(tmp_path / "from-a-bucket") == held(tmp_path / "from-a-folder")


def test_a_build_from_a_folder_says_nothing_of_its_store_as_before(tmp_path: Path, capsys: Printed):
    assert made(tmp_path).run() == 0
    said, _ = lines_of(capsys)
    assert not [line for line in said if line.startswith("step=store")]


def test_a_file_the_bucket_does_not_hold_stops_the_build_before_anything_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    build = made(tmp_path)
    gone = files()["grid"].receipt()
    status, store = from_a_bucket(build, monkeypatch)
    assert status == 0
    (build.store / gone.vault_key()).rename(tmp_path / "set-aside")
    capsys.readouterr()
    status, store = from_a_bucket(build, monkeypatch, out=tmp_path / "again")
    said, words = lines_of(capsys)
    assert status == 2
    # The listing of the store lacks the file, so the lock is not sealed.
    assert said == [f"step=assemble status=refused file_is_in_the_vault=1 file_id={gone.file_id}"]
    assert store.asked == [] and not (tmp_path / "again").exists()
    assert "made-up" not in words.replace("made-up.toml", "")


def test_a_file_that_is_not_the_file_of_its_receipt_stops_the_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    """The listing gives a size. What the bytes are is known once they are copied out."""
    build = made(tmp_path)
    changed = files()["grid"]
    kept = build.store / changed.receipt().vault_key()
    kept.write_bytes(changed.content.replace(b"1", b"2", 1))
    assert kept.stat().st_size == len(changed.content)
    status, _ = from_a_bucket(build, monkeypatch)
    said, _ = lines_of(capsys)
    assert status == 2
    assert said[-1] == (
        f"step=assemble status=refused file_is_in_the_vault=1 file_id={changed.receipt().file_id}"
    )
    assert not build.out.exists()


def test_the_environment_may_name_an_object_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    """A build once took a folder and no other store. A hosted run is given a bucket."""
    build = made(tmp_path)
    seen: list[dict[str, str]] = []

    def named(environment: Mapping[str, str]) -> Store:
        seen.append(dict(environment))
        return cast(Store, Reached(build.store))

    monkeypatch.setattr(assemble, "store_from_environment", named)
    assert assemble.main(build.arguments(), A_BUCKET) == 0
    assert seen == [A_BUCKET]


def test_with_no_store_named_the_step_says_how_either_is_named(tmp_path: Path, capsys: Printed):
    assert assemble.main(made(tmp_path).arguments(), {}) == 2
    said, words = lines_of(capsys)
    assert said == ["step=assemble status=unreadable"]
    assert "BURRO_STORE_FOLDER" in words and "BURRO_STORE_ENDPOINT" in words


def test_a_folder_and_a_bucket_named_together_are_refused(tmp_path: Path, capsys: Printed):
    build = made(tmp_path)
    both = A_BUCKET | {"BURRO_STORE_FOLDER": str(build.store)}
    assert assemble.main(build.arguments(), both) == 2
    said, words = lines_of(capsys)
    assert said == ["step=assemble status=unreadable"]
    assert "both a folder and an object store are named" in words
    assert "made-up-secret" not in words and not build.out.exists()


# A store that is named, and cannot be reached

# A made-up store at an address no host can have: a name that ends `.invalid` is given to
# no host. The store is the one the step makes of the environment, and nothing stands in
# its place. What stands in is the connection, so that nothing is asked of any network.
NO_HOST = {
    "BURRO_STORE_ENDPOINT": "https://rehearsal-0000.invalid",
    "BURRO_STORE_BUCKET": "rehearsal-bucket-0000",
    "BURRO_STORE_KEY_ID": "rehearsal-key-id-0000",
    "BURRO_STORE_SECRET": "rehearsal-secret-0000",
}


def no_such_host(_: http.client.HTTPConnection) -> NoReturn:
    raise socket.gaierror(socket.EAI_NONAME, "nodename nor servname provided, or not known")


def no_answer(_: http.client.HTTPConnection) -> NoReturn:
    raise TimeoutError("timed out")


def not_secure(_: http.client.HTTPConnection) -> NoReturn:
    raise ssl.SSLError("certificate verify failed")


@pytest.mark.parametrize("fails", [no_such_host, no_answer, not_secure])
def test_a_store_that_cannot_be_reached_stops_the_build_in_one_line_that_names_no_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Printed,
    fails: Callable[[http.client.HTTPConnection], NoReturn],
):
    build = made(tmp_path)
    monkeypatch.setattr(http.client.HTTPSConnection, "connect", fails)
    assert assemble.main(build.arguments(), NO_HOST) == 2
    said, words = lines_of(capsys)
    # The step, that it failed, and why by the number fetch gives a store that fails.
    assert said == [f"step=assemble status=failed why={Why.STORE.value}"]
    assert is_public(said[0])
    assert words.startswith("error: the store ") and words.count("\n") == 1
    assert "Traceback" not in words and ' File "' not in words
    printed = (said[0] + words).lower()
    for value in (*NO_HOST.values(), "rehearsal", ".invalid", "https://"):
        assert value not in printed
    assert not build.out.exists()
