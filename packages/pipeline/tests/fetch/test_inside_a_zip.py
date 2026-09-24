"""What a zip holds is read all the way down, before the zip is kept.

A publisher's zip may hold a zip. A table inside the inner one is as much in
the file as a table inside the outer one, so its name is held to the entry of
the source too. A zip that cannot be looked into is not kept: nothing shows
what it holds. Every file here is made up, and no socket is opened.
"""

import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from burro_pipeline.fetch.by_hand import keep_by_hand
from burro_pipeline.fetch.download import Downloaded
from burro_pipeline.fetch.kinds import CannotSeeInside, names_inside
from burro_pipeline.fetch.run import WORDS, Status, Why, fetch
from burro_pipeline.fetch.sources import Listed
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.registry import Registry, load

from .support import MADE_UP_REGISTRY

NOW = datetime(2026, 9, 24, 9, 12, 31, tzinfo=UTC)
BODY = b"code,homes\nmade-up-1,10\nmade-up-2,20\n"
ADDRESS = "https://files.made-up.example/files/homes.zip"


def zipped(members: dict[str, bytes]) -> bytes:
    held = io.BytesIO()
    with zipfile.ZipFile(held, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), content)
    return held.getvalue()


def nested(levels: int, innermost: dict[str, bytes]) -> bytes:
    """A zip that holds a zip, and so on, `levels` deep in all."""
    content = zipped(innermost)
    for level in range(levels - 1):
        content = zipped({f"made-up-{level}.zip": content})
    return content


def saved(tmp_path: Path, content: bytes, name: str = "made-up.zip") -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


# The names inside


def test_a_file_that_is_no_zip_holds_no_names(tmp_path: Path):
    assert names_inside(saved(tmp_path, BODY, "homes.csv")) == ()
    assert names_inside(saved(tmp_path, b"", "empty.csv")) == ()


def test_a_zip_gives_the_names_inside_it(tmp_path: Path):
    path = saved(tmp_path, zipped({"made-up-a.csv": BODY, "folder/made-up-b.csv": BODY}))
    assert set(names_inside(path)) == {"made-up-a.csv", "folder/made-up-b.csv"}


def test_a_zip_inside_a_zip_gives_its_names_too(tmp_path: Path):
    inner = zipped({"made-up-inner.csv": BODY})
    path = saved(tmp_path, zipped({"made-up-a.csv": BODY, "tables.zip": inner}))
    assert set(names_inside(path)) == {"made-up-a.csv", "tables.zip", "made-up-inner.csv"}


def test_a_zip_inside_a_zip_is_found_by_how_it_starts_and_not_by_its_name(tmp_path: Path):
    inner = zipped({"made-up-inner.csv": BODY})
    path = saved(tmp_path, zipped({"tables.dat": inner}))
    assert "made-up-inner.csv" in names_inside(path)


def test_a_zip_is_looked_into_three_zips_down(tmp_path: Path):
    path = saved(tmp_path, nested(4, {"made-up-innermost.csv": BODY}))
    assert "made-up-innermost.csv" in names_inside(path)


@pytest.mark.parametrize("levels", [5, 6])
def test_a_zip_nested_deeper_than_is_looked_into_cannot_be_seen_into(tmp_path: Path, levels: int):
    path = saved(tmp_path, nested(levels, {"made-up-innermost.csv": BODY}))
    with pytest.raises(CannotSeeInside):
        names_inside(path)


def test_zips_that_unpack_to_more_than_the_limit_cannot_be_seen_into(tmp_path: Path):
    inner = zipped({"made-up-inner.csv": b"0" * 100_000})
    path = saved(tmp_path, zipped({"tables.zip": inner}))
    assert "made-up-inner.csv" in names_inside(path)
    with pytest.raises(CannotSeeInside):
        names_inside(path, most=len(inner) - 1)


def test_a_member_named_as_a_zip_that_is_none_cannot_be_seen_into(tmp_path: Path):
    path = saved(tmp_path, zipped({"tables.zip": BODY}))
    with pytest.raises(CannotSeeInside):
        names_inside(path)


def test_a_file_that_starts_as_a_zip_and_cannot_be_opened_cannot_be_seen_into(tmp_path: Path):
    whole = zipped({"made-up-a.csv": BODY})
    with pytest.raises(CannotSeeInside):
        names_inside(saved(tmp_path, whole[: len(whole) // 2]))


def test_a_zip_with_something_written_before_it_is_still_a_zip(tmp_path: Path):
    path = saved(tmp_path, b"made up, and no part of the zip\n" + zipped({"made-up-a.csv": BODY}))
    assert names_inside(path) == ("made-up-a.csv",)


def test_a_member_that_cannot_be_unpacked_cannot_be_seen_into(tmp_path: Path):
    whole = bytearray(zipped({"made-up-a.csv": BODY * 50}))
    # The member's own bytes are spoiled, and the list of members at the end is left whole.
    start = whole.index(b"made-up-a.csv") + len(b"made-up-a.csv")
    whole[start : start + 8] = b"\xff" * 8
    with pytest.raises(CannotSeeInside):
        names_inside(saved(tmp_path, bytes(whole)))


# A run of fetch, and a file saved by hand


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    path = tmp_path / "registry.toml"
    path.write_text(MADE_UP_REGISTRY, encoding="utf-8")
    return load(path)


@pytest.fixture
def store(tmp_path: Path) -> FolderStore:
    return FolderStore(tmp_path / "store")


@pytest.fixture
def receipts(tmp_path: Path) -> Path:
    return tmp_path / "receipts"


def listed(**changed: object) -> Listed:
    fields: dict[str, object] = {
        "item": "homes",
        "source_id": "made-up-homes",
        "use": "scoring",
        "what": "Made-up homes by made-up area",
        "format": "zip",
        "page": "https://made-up.example/homes",
        "url": ADDRESS,
        "max_bytes": 1_000_000,
        "edition": "2025",
        "data_period": {"as_at": "2025-03-31"},
        **changed,
    }
    return Listed.model_validate(fields)


def arriving(content: bytes):
    """A stand-in for the download: the file arrives as it is given, and nothing is asked."""

    def downloader(
        address: str, to: Path, limits: object, *, agent: str, may_redirect_to: tuple[str, ...] = ()
    ) -> Downloaded:
        to.write_bytes(content)
        return Downloaded("0" * 64, len(content), address, "homes.zip", "application/zip")

    return downloader


INSIDE = [
    ({"tables.zip": zipped({"census2021-ts021-oa.csv": BODY})}, Why.RESIDENT_TABLE),
    ({"tables.dat": zipped({"census2021-ts021-oa.csv": BODY})}, Why.RESIDENT_TABLE),
    ({"a.zip": zipped({"b.zip": zipped({"TS_021_oa.csv": BODY})})}, Why.RESIDENT_TABLE),
    ({"tables.zip": nested(6, {"made-up.csv": BODY})}, Why.CANNOT_SEE_INSIDE),
    ({"tables.zip": BODY}, Why.CANNOT_SEE_INSIDE),
]


@pytest.mark.parametrize(("members", "why"), INSIDE)
def test_a_zip_is_not_kept_for_what_a_zip_inside_it_holds(
    registry: Registry, store: FolderStore, receipts: Path, members: dict[str, bytes], why: Why
):
    content = zipped({"census2021-ts044-oa.csv": BODY, **members})
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent="made up", downloader=arriving(content)
    )
    assert (outcome.status, outcome.why) == (Status.REFUSED, why)
    assert f" status=refused why={int(why)} " in outcome.line()
    assert store.list() == [] and not receipts.exists()


@pytest.mark.parametrize(("members", "why"), INSIDE)
def test_a_zip_saved_by_hand_is_not_kept_for_what_a_zip_inside_it_holds(
    registry: Registry,
    store: FolderStore,
    receipts: Path,
    tmp_path: Path,
    members: dict[str, bytes],
    why: Why,
):
    path = saved(tmp_path, zipped({"census2021-ts044-oa.csv": BODY, **members}))
    file = listed(url="", by_hand=True)
    outcome = keep_by_hand(1, file, path, ADDRESS, "2026-09-24", registry, store, receipts, NOW)
    assert (outcome.status, outcome.why) == (Status.REFUSED, why)
    assert store.list() == [] and not receipts.exists()


def test_a_zip_of_zips_of_housing_tables_is_kept(
    registry: Registry, store: FolderStore, receipts: Path
):
    content = zipped({"oa.zip": zipped({"census2021-ts044-oa.csv": BODY})})
    (outcome,) = fetch(
        [listed()], registry, store, receipts, agent="made up", downloader=arriving(content)
    )
    assert outcome.status is Status.OK


def test_the_refusal_says_what_a_person_can_do():
    said = WORDS[Why.CANNOT_SEE_INSIDE]
    assert "Nothing was kept" in said
