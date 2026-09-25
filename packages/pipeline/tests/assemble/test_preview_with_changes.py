"""The step `preview`, given a file of changes, on the whole of a made-up build.

The town is Quillhaven and Tallowgate, which do not exist. The changes are made up too:
what a person might decide at the panel of the review desk, of a recipe and of a name.
Every reason here is made up, and none names a real place.
"""

import hashlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import TAGS, band_of, percentile_of, tag_raw
from burro_core.ids import TagId
from burro_pipeline import changes
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.derive import brand_table
from burro_pipeline.evidence.lock import InputKind, Lock
from burro_pipeline.release.read import read_served
from public_log import is_public

from ..evidence.support import GIT
from .published import published
from .support import RELEASE, Made, made

pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to publish a file of changes")

Printed = pytest.CaptureFixture[str]
# A reason no other test writes. If a line that is printed repeats it, it shows.
CANARY = "Zzyzx Parva canary reason"
# The made-up town holds every part of Leafy, and no two parts put its areas in one order.
VIBE = TagId.LEAFY
WAS = changes.recipe_of(TAGS[VIBE])
NOW = {"land_gardens": 20, "land_woodland": 50, "green_cover": 30}


def a_line(n: int, **changed: Any) -> dict[str, Any]:
    held: dict[str, Any] = {
        "n": n,
        "on": "2026-09-25",
        "by": "r1",
        "what": "recipe",
        "of": VIBE.value,
        "was": WAS,
        "now": NOW,
        "why": CANARY,
        "takes_back": None,
    }
    return {**held, **changed}


def taken_back(n: int, line: int) -> dict[str, Any]:
    return a_line(n, what="take_back", was=None, now=None, takes_back=line)


def file_of(folder: Path, *lines: dict[str, Any], name: str = "r1.jsonl") -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return path


def built(folder: Path, *lines: dict[str, Any]) -> Made:
    """The made-up build, from a file of changes that was published, or from none."""
    found = made(folder)
    more = published(folder / "published", *lines).arguments() if lines else ()
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run(*more) == 0
    return found


@pytest.fixture(scope="module")
def plain(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The made-up build with no file of changes."""
    return built(tmp_path_factory.mktemp("plain"))


@pytest.fixture(scope="module")
def changed(tmp_path_factory: pytest.TempPathFactory) -> Made:
    """The made-up build with one change of a recipe and one of a name that stand."""
    names = changes.names_of(TAGS[VIBE])
    return built(
        tmp_path_factory.mktemp("changed"),
        a_line(1),
        a_line(2, what="name", was=names, now={**names, "label": "Green and leafy"}),
        a_line(3, what="flag", of="figure/lon-n001/land_gardens", was=None, now=None),
    )


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def files_of(folder: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(folder.iterdir())}


def vibe_of(build: Made) -> dict[str, Any]:
    held = read(build.release / "catalogue.json")["vibes"]
    return next(one for one in held if one["tag_id"] == VIBE)


def test_the_made_up_town_is_placed_on_the_vibe_that_is_changed(plain: Made):
    rows = [row for row in read(plain.release / "tags.json")["rows"] if row["tag_id"] == VIBE]
    assert rows and all(row["band"] is not None for row in rows)
    assert vibe_of(plain)["terms"] == TAGS[VIBE].model_dump(mode="json")["terms"]


def test_the_release_carries_the_shares_and_the_name_a_person_kept(changed: Made):
    held = vibe_of(changed)
    assert {term["feature_id"]: term["hundredths"] for term in held["terms"]} == NOW
    assert (held["label"], held["short_label"]) == ("Green and leafy", "Green and leafy")
    assert (held["low_end"], held["high_end"]) == (None, None)
    # Nothing else of the vibe moved, and no other vibe moved at all.
    core = TAGS[VIBE].model_dump(mode="json")
    moved = {name for name in core if core[name] != held[name]}
    assert moved == {"terms", "label", "short_label"}
    others = [one for one in read(changed.release / "catalogue.json")["vibes"] if one != held]
    assert others == [TAGS[TagId(one["tag_id"])].model_dump(mode="json") for one in others]


def test_every_band_is_worked_out_with_the_shares_the_release_carries(changed: Made, plain: Made):
    release = read_served(changed.release)
    vibe = next(one for one in release.vibes if one.tag_id is VIBE)
    areas = [area.area_id for area in release.neighbourhoods]
    rankable = [area.rankable for area in release.neighbourhoods]
    raws = [
        tag_raw(
            VIBE,
            {
                term.feature_id: row.percentile
                for term in vibe.terms
                if (row := release.feature(area, term.feature_id)) is not None
            },
            vibe.terms,
        )
        for area in areas
    ]
    scores = percentile_of([raw.raw for raw in raws], rankable)
    bands = band_of([raw.raw for raw in raws], rankable)
    for area, raw, score, band in zip(areas, raws, scores, bands, strict=True):
        held = release.tag(area, VIBE)
        assert held is not None
        assert (held.raw, held.score, held.band, held.coverage) == (
            raw.raw,
            score,
            band,
            raw.coverage,
        )
    before = {row.area_id: row.raw for row in read_served(plain.release).tags if row.tag_id is VIBE}
    after = {row.area_id: row.raw for row in release.tags if row.tag_id is VIBE}
    assert before != after, "the shares moved where an area stands"
    assert {row.coverage for row in release.tags if row.tag_id is VIBE} == {1.0}


def test_only_what_was_changed_differs_from_a_build_with_no_file(changed: Made, plain: Made):
    with_it, without = files_of(changed.release), files_of(plain.release)
    differ = {name for name in without if with_it[name] != without[name]}
    assert differ == {"manifest.json", "catalogue.json", "tags.json"}
    rows = {
        name: read(folder.release / "tags.json")["rows"]
        for name, folder in (("a", changed), ("b", plain))
    }
    moved = {row["tag_id"] for row, was in zip(rows["a"], rows["b"], strict=True) if row != was}
    assert moved == {VIBE.value}


def test_a_build_with_no_file_of_changes_says_nothing_of_changes(plain: Made):
    assert "changes" not in read(plain.beside / "build.json")
    lock = Lock.model_validate_json((plain.beside / "lock.json").read_bytes())
    assert not [held for held in lock.inputs if held.name.startswith("changes/")]


def test_a_file_whose_every_change_was_taken_back_builds_the_release_as_it_was(
    tmp_path: Path, plain: Made
):
    found = built(tmp_path, a_line(1), taken_back(2, 1))
    with_it, without = files_of(found.release), files_of(plain.release)
    assert {name for name in without if with_it[name] != without[name]} == {"manifest.json"}
    # The manifest says which file the release was built with, and nothing else of it moved.
    said, was = json.loads(with_it["manifest.json"]), json.loads(without["manifest.json"])
    assert "changes_sha256" not in was
    assert said == was | {"changes_sha256": said["changes_sha256"]}
    assert said["changes_sha256"] == read(found.beside / "build.json")["changes"]["sha256"]
    record = read(found.beside / "build.json")["changes"]
    assert (record["lines"], record["stand"], record["applied"]) == (2, 0, [])


def the_file_of(build: Made) -> Path:
    """The file of changes a build was handed, where it was published."""
    (found,) = (build.folder / "published").rglob("r1.jsonl")
    return found


def test_the_lock_names_the_file_of_changes_by_its_hash(changed: Made):
    content = the_file_of(changed).read_bytes()
    assert (
        read(changed.release / "manifest.json")["changes_sha256"]
        == hashlib.sha256(content).hexdigest()
    )
    lock = Lock.model_validate_json((changed.beside / "lock.json").read_bytes())
    (held,) = [one for one in lock.inputs if one.name.startswith("changes/")]
    assert (held.name, held.kind) == ("changes/r1.jsonl", InputKind.GAZETTEER)
    assert (held.sha256, held.bytes) == (hashlib.sha256(content).hexdigest(), len(content))
    # The hashes of the build hold the lock, so they tie the release to its changes.
    hashes = read(changed.beside / "hashes.json")
    assert hashes["lock_sha256"] == lock.digest()


def test_the_record_of_the_build_lists_each_line_that_was_applied_and_no_reason(changed: Made):
    said = read(changed.beside / "build.json")["changes"]
    assert said["file"] == "r1.jsonl"
    assert (said["lines"], said["stand"], said["flagged"]) == (3, 3, 1)
    assert said["applied"] == [
        {"n": 1, "what": "recipe", "of": "leafy", "by": "r1", "on": "2026-09-25"},
        {"n": 2, "what": "name", "of": "leafy", "by": "r1", "on": "2026-09-25"},
    ]
    for path in sorted(changed.beside.iterdir()):
        assert CANARY.encode() not in path.read_bytes(), path.name
    for path in sorted(changed.release.iterdir()):
        assert CANARY.encode() not in path.read_bytes(), path.name


def test_the_release_is_one_that_is_served_and_every_fact_of_it_has_its_evidence(
    tmp_path: Path, capsys: Printed
):
    found = made(tmp_path)
    assert found.run(*published(tmp_path / "published", a_line(1)).arguments()) == 0
    said = capsys.readouterr()
    lines = said.out.splitlines()
    assert all(is_public(line) for line in lines)
    assert any(line.startswith("step=changes status=ok") and "applied=1" in line for line in lines)
    assert any(line.startswith("step=check status=ok") and "findings=0" in line for line in lines)
    assert "Zzyzx" not in said.out + said.err
    assert read_served(found.release).manifest.release_id == RELEASE


BROKEN: list[tuple[str, list[dict[str, Any]]]] = [
    # It does not sum to 100.
    ("recipe_keeps_its_rules", [a_line(1, now={**NOW, "land_gardens": 50})]),
    # One part could place an area alone.
    (
        "recipe_keeps_its_rules",
        [a_line(1, now={"land_gardens": 60, "land_woodland": 20, "green_cover": 20})],
    ),
    # A part that the recipe does not hold.
    ("change_is_of_its_kind", [a_line(1, now={**NOW, "land_gardens": 10, "air_no2": 10})]),
    (changes.STALE, [a_line(1, was={**WAS, "air_no2": 10}, now={**NOW, "air_no2": 10})]),
    # It was made of a recipe that is not core's, and that no line of the file made.
    (changes.STALE, [a_line(1, was={**WAS, "land_gardens": 45, "land_woodland": 25})]),
    # A vibe that a release of London does not carry.
    (
        changes.NOT_CARRIED,
        [
            a_line(
                1,
                of="works_warehouses",
                was=changes.recipe_of(TAGS[TagId.WORKS_WAREHOUSES]),
                now={"land_industry": 50, "land_storage": 30, "land_transport_other": 20},
            )
        ],
    ),
    (
        "name_is_plain",
        [
            a_line(
                1,
                what="name",
                was=changes.names_of(TAGS[VIBE]),
                now={**changes.names_of(TAGS[VIBE]), "label": "Safe streets"},
            )
        ],
    ),
    ("line_gives_its_reason", [a_line(1, why="")]),
    ("line_is_a_line", [{"n": 1}]),
    # A kind of change that no build applies yet.
    (
        "change_is_one_a_build_applies",
        [a_line(1, what="number", of="fewest_sales", was=10, now=20)],
    ),
]


@pytest.mark.parametrize(("rule", "lines"), BROKEN)
def test_a_change_that_cannot_be_built_stops_the_build_and_names_its_line(
    tmp_path: Path, capsys: Printed, rule: str, lines: list[dict[str, Any]]
):
    found = made(tmp_path)
    assert found.run("--changes", str(file_of(tmp_path / "kept", *lines))) == 2
    said = capsys.readouterr()
    assert said.out.splitlines() == ["step=assemble status=unreadable"]
    assert said.err == (
        f"error: the file of changes cannot be built on: line 1 breaks the rule {rule}. "
        "Look at the line at the panel, or take it back there\n"
    )
    assert not found.out.exists(), "nothing was written"


def test_a_change_that_cannot_be_built_stops_the_build_before_a_file_is_opened(
    tmp_path: Path, capsys: Printed
):
    # No store is named at all, and the refusal is of the file of changes.
    found = made(tmp_path)
    broken = file_of(tmp_path / "kept", a_line(1, why=""))
    assert assemble.main(found.arguments("--changes", str(broken)), {}) == 2
    assert "the file of changes cannot be built on: line 1" in capsys.readouterr().err


@pytest.mark.parametrize("named", ["nowhere.jsonl", "empty.jsonl"])
def test_a_file_of_changes_that_is_not_there_or_holds_no_line_is_refused(
    tmp_path: Path, capsys: Printed, named: str
):
    found = made(tmp_path)
    (tmp_path / "empty.jsonl").write_bytes(b"")
    assert found.run("--changes", str(tmp_path / named)) == 2
    assert "the file of changes" in capsys.readouterr().err
    assert not found.out.exists()


def test_built_twice_with_the_same_file_of_changes_it_writes_the_same_bytes(
    tmp_path: Path, changed: Made
):
    again = built(
        tmp_path, *[json.loads(row) for row in the_file_of(changed).read_text().splitlines()]
    )
    assert files_of(again.release) == files_of(changed.release)
    assert files_of(again.beside) == files_of(changed.beside)


# The table of tiers


def a_chain_moved(n: int, key: str, tier: str) -> dict[str, Any]:
    was = changes.row_of(brand_table.the_table().by_key[key])
    return a_line(n, what="brand", of=key, was=was, now={**was, "tier": tier})


def test_a_chain_that_was_moved_is_laid_over_the_table_of_tiers_for_that_build_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    used: list[str] = []
    measured = assemble._measured  # pyright: ignore[reportPrivateUsage]

    def watched(*given: Any) -> Any:
        used.append(brand_table.the_table().by_key["lidl"].tier.value)
        return measured(*given)

    monkeypatch.setattr(assemble, "_measured", watched)
    found = built(tmp_path, a_chain_moved(1, "lidl", "premium"))
    assert used == ["premium"], "the measures were worked out by the table as it was changed"
    assert brand_table.the_table().by_key["lidl"].tier.value == "value", "and it was put back"
    said = read(found.beside / "build.json")["changes"]
    assert said["applied"] == [
        {"n": 1, "what": "brand", "of": "lidl", "by": "r1", "on": "2026-09-25"}
    ]


def test_with_no_file_of_changes_the_table_of_tiers_is_the_repositorys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    used: list[object] = []
    measured = assemble._measured  # pyright: ignore[reportPrivateUsage]

    def watched(*given: Any) -> Any:
        used.append(brand_table.the_table())
        return measured(*given)

    monkeypatch.setattr(assemble, "_measured", watched)
    built(tmp_path)
    assert used == [brand_table.read()]


def test_a_row_that_is_no_row_of_the_table_stops_the_build(tmp_path: Path, capsys: Printed):
    found = made(tmp_path)
    line = a_chain_moved(1, "lidl", "luxury")
    assert found.run("--changes", str(file_of(tmp_path / "kept", line))) == 2
    assert "line 1 breaks the rule row_is_a_row_of_the_table" in capsys.readouterr().err
    assert not found.out.exists()
