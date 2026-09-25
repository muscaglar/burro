"""Where releases are kept: a folder, and a bucket against a stand-in on the loopback address.

Every file is made up. The stand-in is the one the tests of the object store
use: it keeps files in memory, and works out every signature again from what
arrived on the wire.
"""

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from burro_pipeline.fetch.s3 import S3Store, Settings
from burro_pipeline.fetch.store import NotTheFile, StoreError
from burro_pipeline.kept.store import (
    FOLDER_VARIABLE,
    PREFIX,
    S3_VARIABLES,
    BucketKept,
    Differs,
    FolderKept,
    Kept,
    kept_from_environment,
    key_of,
)

from ..assemble.support import RELEASE
from ..fetch.support import (
    CANARY_BUCKET,
    CANARY_KEY,
    CANARY_ROW,
    CANARY_SECRET,
    ONLY_LOOPBACK,
    Served,
    serving,
)
from ..fetch.test_s3_store import StandIn

CONTENT = f'{{"rows":["{CANARY_ROW}"]}}\n'.encode()
SHA256, SIZE = hashlib.sha256(CONTENT).hexdigest(), len(CONTENT)
NAME = f"{RELEASE}-build/evidence.json"
NOW = datetime(2026, 9, 25, 9, 0, 0, tzinfo=UTC)
A_BUCKET: dict[str, str] = dict(
    zip(
        S3_VARIABLES,
        ("https://made-up.example", CANARY_BUCKET, CANARY_KEY, CANARY_SECRET),
        strict=True,
    )
)


@pytest.fixture
def saved(tmp_path: Path) -> Path:
    path = tmp_path / "built" / "evidence.json"
    path.parent.mkdir()
    path.write_bytes(CONTENT)
    return path


@pytest.fixture
def other(tmp_path: Path) -> Path:
    """A file of the same size, of which one byte is another."""
    path = tmp_path / "other" / "evidence.json"
    path.parent.mkdir()
    path.write_bytes(CONTENT.replace(b"Z", b"Y", 1))
    assert path.stat().st_size == SIZE
    return path


@pytest.fixture
def stand_in() -> StandIn:
    return StandIn()


@pytest.fixture
def served(stand_in: StandIn) -> Iterator[Served]:
    with serving(stand_in) as server:
        yield server


def bucket(served: Served) -> BucketKept:
    """The store of releases as a bucket, which asks the stand-in on the loopback address."""
    kept = BucketKept(A_BUCKET)
    settings = Settings(
        endpoint=served.address,
        bucket=CANARY_BUCKET,
        key_id=CANARY_KEY,
        secret=CANARY_SECRET,
        plain_http_to_loopback=True,
    )
    kept._store = S3Store(settings, now=lambda: NOW, named=S3_VARIABLES)  # pyright: ignore[reportPrivateUsage]
    return kept


@pytest.fixture(params=["folder", "bucket"])
def kept(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Kept]:
    if request.param == "folder":
        yield FolderKept(tmp_path / "kept")
    else:
        with serving(StandIn()) as server:
            yield bucket(server)


pytestmark = ONLY_LOOPBACK


# What both kinds of store do


def test_a_file_that_is_kept_comes_back_byte_for_byte(kept: Kept, saved: Path, tmp_path: Path):
    assert not kept.holds(NAME, saved)
    assert kept.put(NAME, saved) is True
    assert kept.holds(NAME, saved)
    kept.get(NAME, SHA256, SIZE, tmp_path / "taken" / NAME)
    assert (tmp_path / "taken" / NAME).read_bytes() == CONTENT


def test_a_file_kept_twice_is_kept_once_and_never_written_over(kept: Kept, saved: Path):
    assert kept.put(NAME, saved) is True
    assert kept.put(NAME, saved) is False


def test_another_file_under_the_same_name_is_refused_and_the_first_stands(
    kept: Kept, saved: Path, other: Path, tmp_path: Path
):
    kept.put(NAME, saved)
    with pytest.raises(Differs):
        kept.holds(NAME, other)
    with pytest.raises(Differs):
        kept.put(NAME, other)
    kept.get(NAME, SHA256, SIZE, tmp_path / "taken.json")
    assert (tmp_path / "taken.json").read_bytes() == CONTENT


def test_a_file_that_is_not_the_one_asked_for_is_not_copied_out(
    kept: Kept, saved: Path, tmp_path: Path
):
    kept.put(NAME, saved)
    to = tmp_path / "taken.json"
    with pytest.raises(NotTheFile):
        kept.get(NAME, "0" * 64, SIZE, to)
    with pytest.raises(NotTheFile):
        kept.get(NAME, SHA256, SIZE + 1, to)
    assert not to.exists()
    assert not list(tmp_path.glob("**/.part-*"))


def test_a_file_that_is_not_kept_is_refused(kept: Kept, tmp_path: Path):
    with pytest.raises(StoreError) as refused:
        kept.get(NAME, SHA256, SIZE, tmp_path / "taken.json")
    assert "holds no file of that name" in str(refused.value)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "evidence.json",
        f"{RELEASE}/../evidence.json",
        f"../{RELEASE}/evidence.json",
        f"/{RELEASE}/evidence.json",
        f"{RELEASE}/sub/evidence.json",
        f"{RELEASE}/{CANARY_ROW}.json",
        "syn-2026-09-23-01/evidence.json",
        f"raw/{RELEASE}/evidence.json",
    ],
)
def test_a_name_that_is_none_a_lock_gives_is_refused_and_not_repeated(
    kept: Kept, saved: Path, tmp_path: Path, name: str
):
    for ask in (
        lambda: kept.put(name, saved),
        lambda: kept.holds(name, saved),
        lambda: kept.get(name, SHA256, SIZE, tmp_path / "taken.json"),
    ):
        with pytest.raises(StoreError) as refused:
            ask()
        assert "Zzyzx" not in str(refused.value) and RELEASE not in str(refused.value)


def test_a_release_is_kept_apart_from_every_publishers_file():
    """The store of files keeps under `raw/` and `receipts/`. A release is under neither."""
    assert key_of(NAME) == f"{PREFIX}{NAME}" == f"releases/{RELEASE}-build/evidence.json"


# The bucket


def test_a_file_is_kept_in_the_bucket_under_releases(
    served: Served, stand_in: StandIn, saved: Path
):
    assert bucket(served).put(NAME, saved) is True
    assert stand_in.held == {f"releases/{NAME}": CONTENT}
    assert all("authorization" in request.headers for request in served.seen)


def test_a_file_changed_in_the_bucket_is_refused(
    served: Served, stand_in: StandIn, saved: Path, tmp_path: Path
):
    store = bucket(served)
    store.put(NAME, saved)
    stand_in.held[f"releases/{NAME}"] = CONTENT.replace(b"Z", b"Y", 1)
    with pytest.raises(NotTheFile):
        store.get(NAME, SHA256, SIZE, tmp_path / "taken.json")
    assert not (tmp_path / "taken.json").exists()
    with pytest.raises(Differs):
        store.put(NAME, saved)


def test_an_error_of_the_bucket_names_no_address_bucket_or_key(
    served: Served, stand_in: StandIn, saved: Path, tmp_path: Path
):
    stand_in.fail_with = stand_in.error(403, "AccessDenied")
    store = bucket(served)
    for ask in (
        lambda: store.put(NAME, saved),
        lambda: store.holds(NAME, saved),
        lambda: store.get(NAME, SHA256, SIZE, tmp_path / "taken.json"),
    ):
        with pytest.raises(StoreError) as refused:
            ask()
        said = str(refused.value)
        assert "403 AccessDenied" in said
        for secret in (CANARY_BUCKET, CANARY_KEY, CANARY_SECRET, served.address, "127.0.0.1"):
            assert secret not in said
    assert "BucketKept(not shown)" in repr(store) and CANARY_SECRET not in repr(store)


# Which store the environment names


def test_the_environment_names_one_store_of_releases(tmp_path: Path):
    assert isinstance(kept_from_environment({FOLDER_VARIABLE: str(tmp_path)}), FolderKept)
    assert isinstance(kept_from_environment(A_BUCKET), BucketKept)
    assert kept_from_environment({FOLDER_VARIABLE: str(tmp_path)}).kind == "folder"
    assert kept_from_environment(A_BUCKET).kind == "object_store"


def test_a_folder_and_a_bucket_named_together_are_refused(tmp_path: Path):
    for name in S3_VARIABLES:
        with pytest.raises(StoreError) as refused:
            kept_from_environment({FOLDER_VARIABLE: str(tmp_path), name: A_BUCKET[name]})
        assert "both a folder and a bucket" in str(refused.value)
        assert A_BUCKET[name] not in str(refused.value) and str(tmp_path) not in str(refused.value)


def test_the_store_of_publishers_files_is_no_store_of_releases(tmp_path: Path):
    """A step that is given the key of one store is not thereby given the other."""
    of_files = {
        "BURRO_STORE_FOLDER": str(tmp_path),
        "BURRO_STORE_ENDPOINT": "https://made-up.example",
        "BURRO_STORE_BUCKET": CANARY_BUCKET,
        "BURRO_STORE_KEY_ID": CANARY_KEY,
        "BURRO_STORE_SECRET": CANARY_SECRET,
    }
    with pytest.raises(StoreError) as refused:
        kept_from_environment(of_files)
    assert "no store of releases is named" in str(refused.value)
    from burro_pipeline.fetch.store import store_from_environment

    with pytest.raises(StoreError):
        store_from_environment({FOLDER_VARIABLE: str(tmp_path)} | A_BUCKET)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("BURRO_RELEASES_ENDPOINT", "http://made-up.example"),
        ("BURRO_RELEASES_ENDPOINT", "https://made-up.example/a/path"),
        ("BURRO_RELEASES_BUCKET", "Made Up/Bucket"),
    ],
)
def test_a_bucket_that_is_named_badly_is_refused_by_its_own_name(name: str, value: str):
    with pytest.raises(StoreError) as refused:
        kept_from_environment(A_BUCKET | {name: value})
    assert name in str(refused.value) and "BURRO_STORE" not in str(refused.value)
    assert value not in str(refused.value)
