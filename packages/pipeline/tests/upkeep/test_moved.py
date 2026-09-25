"""What moved between two builds: the step `moved`, on two made-up releases.

The town is Quillhaven and Tallowgate, two boroughs that do not exist. It is built
twice, as `preview` builds it, from made-up files. The second build is given another
file of the air, in which two of the three areas read higher, and no receipt of the
file of noise, so that the measure of noise and the band that rests on it are gone.
Nothing here reaches a network or a store of real files.
"""

import dataclasses
import json
import shutil
from pathlib import Path
from typing import Any

import public_log
import pytest
from burro_core.catalogue import CATALOGUE_VERSION as VERSION
from burro_core.ids import FeatureId
from burro_pipeline import cli
from burro_pipeline.derive import air_no2
from burro_pipeline.evidence import read_receipts
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.registry.model import Use
from burro_pipeline.upkeep import moved, written
from burro_pipeline.upkeep.cli import main
from burro_pipeline.upkeep.searches import read_searches

from ..assemble.support import RELEASE, File, Made, made
from ..derive import test_air_no2 as grid

REPOSITORY = Path(__file__).resolve().parents[4]
SEARCHES = REPOSITORY / "tools" / "desk" / "panel" / "searches.json"
BEFORE, AFTER = RELEASE, "lon-2026-09-23-02"
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# The made-up grid of the air, with the first square higher and the last no longer missing.
HIGHER = (
    ("900001", *grid.A, "12.5"),
    ("900002", *grid.B, "20.0"),
    ("900003", *grid.C, "40.0"),
    ("900004", *grid.D, "30.0"),
    ("900005", *grid.FAR_WEST, "1.5"),
)
# What no line may hold: the name of an area or of a borough of the town, and an id of one.
NAMED = ("Quillhaven", "Tallowgate", "lon-ne", ONE, TWO, THREE)
Printed = pytest.CaptureFixture[str]


@dataclasses.dataclass(frozen=True)
class Two:
    """Two made-up builds on disk, and the receipts and the list of both."""

    before: Made
    after: Made
    receipts: Path
    lists: Path

    @property
    def folders(self) -> tuple[str, str]:
        return str(self.before.out / BEFORE), str(self.after.out / AFTER)

    def compared(self) -> dict[str, Any]:
        return moved.compare(
            moved.open_build(self.before.out / BEFORE),
            moved.open_build(self.after.out / AFTER),
            receipts=read_receipts(self.receipts),
            lists=[load_list(path) for path in sorted(self.lists.glob("*.toml"))],
            searches=read_searches(SEARCHES, REPOSITORY),
        )

    def run(self, *more: str) -> int:
        return main(
            [
                "moved",
                *self.folders,
                *("--receipts", str(self.receipts)),
                *("--lists", str(self.lists)),
                *("--root", str(REPOSITORY)),
                *more,
            ]
        )


@pytest.fixture(scope="module")
def two(tmp_path_factory: pytest.TempPathFactory) -> Two:
    root = tmp_path_factory.mktemp("moved")
    before = made(root / "before")
    assert before.run() == 0
    newer = File(
        "grid", air_no2.SOURCE, Use.SCORING, grid.GRID_NAME, "2024", "2024", grid.grid_csv(HIGHER)
    )
    after = made(root / "after", changed={"grid": newer}, without_a_receipt=("noise",))
    assert after.run("--release-id", AFTER) == 0
    # The receipts of both builds in one folder, as the repository holds the receipts of
    # every edition, and the list as it stands.
    receipts = root / "receipts"
    for build in (before, after):
        for path in sorted(build.receipts.rglob("*.json")):
            kept = receipts / path.relative_to(build.receipts)
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_bytes(path.read_bytes())
    lists = root / "lists"
    lists.mkdir()
    (lists / "made-up.toml").write_bytes((after.folder / "made-up.toml").read_bytes())
    return Two(before, after, receipts, lists)


@pytest.fixture(scope="module")
def found(two: Two) -> dict[str, Any]:
    return json.loads(json.dumps(two.compared()))


# What came and went


def test_a_build_held_against_itself_has_moved_nothing(two: Two):
    same = moved.open_build(two.before.out / BEFORE)
    found = moved.compare(same, same, searches=read_searches(SEARCHES, REPOSITORY))
    assert found["catalogue"] == {"before": VERSION, "after": VERSION, "measures": [], "vibes": []}
    counts = moved.counted(found)
    assert {key: count for key, count in counts.items() if count} == {
        "areas": 3,
        "measures": len(same.release.metrics),
        "vibes": 14,
        "searches": 3,
    }
    assert moved.lines(found)[:-1] == [
        f"step=moved search={number} kept=3 came=0 went=0 reordered=0" for number in (1, 2, 3)
    ]


def test_a_measure_that_a_build_no_longer_carries_is_said_to_have_gone(found: dict[str, Any]):
    assert found["measures"]["went"] == [
        {
            "id": "noise_exposure",
            "label": "Share of residents exposed to 55 dB or more of transport noise",
            "unit": "%",
            "with_a_figure": 3,
        }
    ]
    assert found["measures"]["came"] == []
    assert found["before"]["measures"] == found["after"]["measures"] + 1


def test_a_measure_that_a_build_gains_is_said_to_have_come(two: Two):
    turned = moved.compare(
        moved.open_build(two.after.out / AFTER), moved.open_build(two.before.out / BEFORE)
    )
    assert [one["id"] for one in turned["measures"]["came"]] == ["noise_exposure"]
    assert moved.counted(turned)["measures_came"] == 1
    assert "step=moved feature=noise_exposure came=1" in moved.lines(turned)


# How far the figures of a measure moved


def test_a_measure_says_how_many_areas_changed_and_by_how_much(found: dict[str, Any]):
    (air,) = found["measures"]["moved"]
    assert {key: air[key] for key in air if key != "moved_most"} == {
        "id": "air_no2",
        "label": "Modelled annual mean nitrogen dioxide",
        "unit": "µg/m³",
        "dated": {"was": "2024", "now": "2024"},
        "areas": 3,
        "changed": 2,
        "up": 2,
        "down": 0,
        "gained": 0,
        "lost": 0,
        # The lower of the two in the middle, so that it is a step an area took.
        "middle": 1.2,
        "most": 7.3,
    }
    assert air["moved_most"] == [
        {"id": TWO, "name": "Quillhaven 002", "borough": "Quillhaven", "was": 10.0, "now": 17.3,
         "by": 7.3},
        {"id": ONE, "name": "Quillhaven 001", "borough": "Quillhaven", "was": 15.4, "now": 16.6,
         "by": 1.2},
    ]  # fmt: skip


def test_a_step_is_the_difference_a_person_finds_by_hand(two: Two):
    """No figure is what a float makes of a subtraction: 17.3 less 10.0 is 7.3."""
    before = moved.open_build(two.before.out / BEFORE).release
    after = moved.open_build(two.after.out / AFTER).release
    was = before.feature(TWO, FeatureId.AIR_NO2)
    now = after.feature(TWO, FeatureId.AIR_NO2)
    assert was is not None and now is not None
    assert (was.value, now.value) == (10.0, 17.3)
    assert 17.3 - 10.0 != 7.3


def test_an_area_that_gains_a_figure_or_loses_one_is_counted_apart(two: Two):
    before = moved.open_build(two.before.out / BEFORE)
    without = dataclasses.replace(
        before.release,
        features=tuple(
            row.replace(value=None, percentile=None)
            if (row.area_id, row.feature_id) == (ONE, FeatureId.AIR_NO2)
            else row
            for row in before.release.features
        ),
    )
    lost = moved.compare(before, moved.Build(without, before.lock))
    (air,) = lost["measures"]["moved"]
    assert (air["changed"], air["gained"], air["lost"]) == (0, 0, 1)
    assert (air["middle"], air["most"], air["moved_most"]) == (None, None, [])
    gained = moved.compare(moved.Build(without, before.lock), before)
    (air,) = gained["measures"]["moved"]
    assert (air["changed"], air["gained"], air["lost"]) == (0, 1, 0)


# The bands of a vibe


def test_a_vibe_says_how_many_areas_changed_band_gained_one_or_lost_one(found: dict[str, Any]):
    (quiet,) = found["vibes"]["moved"]
    assert quiet == {
        "id": "quiet_residential",
        "label": "Quiet streets",
        "areas": 3,
        "changed": 0,
        "up": 0,
        "down": 0,
        "gained": 0,
        "lost": 3,
        "by_bands": [],
        "recipe_changed": False,
        "moved_most": [],
    }
    assert found["vibes"]["came"] == [] and found["vibes"]["went"] == []


def test_a_vibe_says_by_how_many_bands_each_area_moved(two: Two):
    before = moved.open_build(two.before.out / BEFORE)
    placed = [row for row in before.release.tags if row.band is not None]
    assert placed, "the made-up build places an area on some vibe"
    tag_id, up_by = placed[0].tag_id, 5 - (placed[0].band or 0) or -1
    moved_on = dataclasses.replace(
        before.release,
        tags=tuple(
            row.replace(
                band=(row.band or 0) + up_by,
                spread_low=(row.band or 0) + up_by,
                spread_high=(row.band or 0) + up_by,
            )
            if (row.area_id, row.tag_id) == (placed[0].area_id, tag_id)
            else row
            for row in before.release.tags
        ),
    )
    found = moved.compare(before, moved.Build(moved_on, before.lock))
    (vibe,) = found["vibes"]["moved"]
    assert (vibe["id"], vibe["changed"]) == (tag_id.value, 1)
    assert vibe["by_bands"] == [{"by": up_by, "areas": 1}]
    assert (vibe["up"], vibe["down"]) == ((1, 0) if up_by > 0 else (0, 1))
    assert [(one["id"], one["was"], one["now"]) for one in vibe["moved_most"]] == [
        (placed[0].area_id, placed[0].band, (placed[0].band or 0) + up_by)
    ]
    assert [one["id"] for one in found["areas"]["moved_most"]] == [placed[0].area_id]


def test_a_vibe_whose_recipe_a_release_changed_says_so(two: Two):
    before = moved.open_build(two.before.out / BEFORE)
    first = before.release.vibes[0]
    renamed = dataclasses.replace(
        before.release, vibes=(first.replace(label="Another name"), *before.release.vibes[1:])
    )
    found = moved.compare(before, moved.Build(renamed, before.lock))
    (vibe,) = found["vibes"]["moved"]
    assert (vibe["id"], vibe["recipe_changed"], vibe["changed"]) == (first.tag_id.value, True, 0)


# The areas


def test_an_area_that_came_went_or_bears_another_name_is_said(two: Two):
    before = moved.open_build(two.before.out / BEFORE)
    release = before.release
    fewer = dataclasses.replace(
        release,
        neighbourhoods=tuple(
            area.replace(name="Dulcimer Green") if area.area_id == ONE else area
            for area in release.neighbourhoods
            if area.area_id != THREE
        ),
        features=tuple(row for row in release.features if row.area_id != THREE),
        tags=tuple(row for row in release.tags if row.area_id != THREE),
        geometries=tuple(row for row in release.geometries if row.area_id != THREE),
    )
    found = moved.compare(before, moved.Build(fewer, before.lock))
    areas = found["areas"]
    assert (areas["same"], areas["came"]) == (2, [])
    assert areas["went"] == [{"id": THREE, "name": "Tallowgate 001", "borough": "Tallowgate"}]
    assert areas["renamed"] == [
        {
            "id": ONE,
            "name": "Dulcimer Green",
            "borough": "Quillhaven",
            "was": "Quillhaven 001",
            "was_in": "Quillhaven",
        }
    ]
    assert areas["redrawn"] == []
    counts = moved.counted(found)
    assert (counts["areas"], counts["areas_went"], counts["areas_renamed"]) == (2, 1, 1)
    # An area that one build lacks is compared on no measure and no vibe.
    assert found["measures"]["moved"] == [] and found["vibes"]["moved"] == []
    turned = moved.compare(moved.Build(fewer, before.lock), before)
    assert [one["id"] for one in turned["areas"]["came"]] == [THREE]


def test_an_area_that_is_drawn_otherwise_is_said_to_be_redrawn(two: Two):
    before = moved.open_build(two.before.out / BEFORE)
    first, *rest = before.release.geometries
    other = dataclasses.replace(
        before.release, geometries=(first.replace(geometry=rest[0].geometry), *rest)
    )
    found = moved.compare(before, moved.Build(other, before.lock))
    assert [one["id"] for one in found["areas"]["redrawn"]] == [first.area_id]
    assert moved.counted(found)["areas_redrawn"] == 1


# The files behind a build


def test_a_file_that_is_another_file_than_before_is_named_with_both_editions(
    found: dict[str, Any],
):
    files = found["files"]
    assert (files["compared"], len(files["came"])) == (True, 0)
    (changed,) = files["changed"]
    for which in ("was", "now"):
        assert {key: changed[which][key] for key in ("source", "list", "item")} == {
            "source": "defra-pcm-background-air",
            "list": "made-up",
            "item": "grid",
        }
        assert (changed[which]["edition"], changed[which]["period"]) == ("2024", "2024")
    assert changed["was"]["file_id"] != changed["now"]["file_id"]
    (went,) = files["went"]
    assert (went["source"], went["item"]) == ("mhclg-iod-2025-underlying-indicators", "noise")
    # Every other input is the same file in both.
    assert files["same"] > 10


def test_with_no_receipt_a_file_is_known_by_its_id_alone(two: Two):
    found = moved.compare(
        moved.open_build(two.before.out / BEFORE), moved.open_build(two.after.out / AFTER)
    )
    files = found["files"]
    assert files["changed"] == []
    # The file of the air went and another came, and the file of noise went.
    assert sorted(one["source"] for one in files["went"]) == [
        "defra-pcm-background-air",
        "mhclg-iod-2025-underlying-indicators",
    ]
    assert [one["source"] for one in files["came"]] == ["defra-pcm-background-air"]
    assert {one["edition"] for one in (*files["came"], *files["went"])} == {None}


def test_a_made_up_release_has_no_lock_so_no_file_is_compared():
    fixture = REPOSITORY / "data" / "fixtures" / "synthetic" / "syn-2026-09-23-01"
    made_up = moved.open_build(fixture)
    assert made_up.lock is None
    found = moved.compare(made_up, made_up)
    assert found["files"] == {"compared": False, "same": 0, "changed": [], "came": [], "went": []}
    assert "A made-up release has no lock" in written.page(found)


# The searches


def test_the_first_areas_of_each_search_are_given_before_and_after(found: dict[str, Any]):
    searches = found["searches"]
    assert [one["id"] for one in searches] == [
        "the_founders_sentence",
        "a_family_buying_a_house",
        "nights_out_well_connected",
    ]
    first = searches[0]
    assert [area["id"] for area in first["before"]["first"]] == [TWO, ONE, THREE]
    assert [area["id"] for area in first["after"]["first"]] == [ONE, TWO, THREE]
    assert (first["same"], first["kept"], first["came"], first["went"]) == (False, 3, 0, 0)
    assert first["reordered"] == 2
    # What a release cannot hold of a search is said, of each build.
    gone = "Quiet streets is not in this release, so the search is ranked without it."
    assert gone in first["after"]["notes"] and gone not in first["before"]["notes"]


def test_what_is_written_holds_no_sentence_that_a_person_typed(two: Two, found: dict[str, Any]):
    sentences = [search.says for search in read_searches(SEARCHES, REPOSITORY)]
    assert all(len(sentence) > 20 for sentence in sentences)
    whole = json.dumps(found, ensure_ascii=False) + written.page(found)
    for sentence in sentences:
        assert sentence not in whole
    assert all("says" not in one for one in found["searches"])


# What the step prints, and what it writes


def test_the_step_prints_counts_and_never_an_area(two: Two, capsys: Printed, tmp_path: Path):
    assert two.run("--out", str(tmp_path / "out")) == 0
    out = capsys.readouterr()
    lines = out.out.splitlines()
    assert lines == [
        "step=moved feature=noise_exposure went=1",
        "step=moved feature=air_no2 areas=3 changed=2 gained=0 lost=0",
        "step=moved vibe=quiet_residential areas=3 changed=0 up=0 down=0 gained=0 lost=3",
        "step=moved source=defra-pcm-background-air changed=1 came=0 went=0",
        "step=moved source=mhclg-iod-2025-underlying-indicators changed=0 came=0 went=1",
        "step=moved search=1 kept=3 came=0 went=0 reordered=2",
        "step=moved search=2 kept=3 came=0 went=0 reordered=2",
        "step=moved search=3 kept=3 came=0 went=0 reordered=2",
        f"step=moved status=ok before={BEFORE} after={AFTER} catalogue_before={VERSION} "
        f"catalogue_after={VERSION} areas=3 areas_came=0 "
        "areas_went=0 areas_renamed=0 areas_redrawn=0 measures=23 measures_came=0 "
        "measures_went=1 measures_moved=1 vibes=14 vibes_came=0 vibes_went=0 vibes_moved=1 "
        "costs_moved=0 files_changed=1 files_came=0 files_went=1 searches=3 searches_moved=3 "
        "parts_came=0 parts_went=0 shares_changed=0 names_changed=0 rough_came=0 rough_went=0",
    ]
    assert all(public_log.is_public(line) for line in lines)
    assert out.err == ""
    for name in NAMED:
        assert name not in out.out
    # No figure of a place: no number with a fraction is printed.
    assert "." not in out.out


def test_what_it_writes_names_each_area_and_is_what_it_found(
    two: Two, found: dict[str, Any], capsys: Printed, tmp_path: Path
):
    out = tmp_path / "out"
    assert two.run("--out", str(out)) == 0
    assert sorted(path.name for path in out.iterdir()) == ["moved.json", "moved.md"]
    assert json.loads((out / "moved.json").read_text(encoding="utf-8")) == found
    page = (out / "moved.md").read_text(encoding="utf-8")
    assert page.startswith(f"# What moved between {BEFORE} and {AFTER}\n")
    assert "| Quillhaven 002, Quillhaven (lon-ne02999002) | 10 | 17.3 |" in page
    assert (
        "| Modelled annual mean nitrogen dioxide | µg/m³ | 2 of 3 | 2 | 0 | 0 | 0 | 1.2 | 7.3 |"
        in (page)
    )
    assert "| Quiet streets | 0 of 3 | 0 | 0 | 0 | 3 |  |  |" in page
    assert "### Files that changed: 1" in page and "### Files that went: 1" in page
    assert "| 1 | Quillhaven 002, Quillhaven (lon-ne02999002) | " in page
    capsys.readouterr()


def test_with_no_folder_named_nothing_is_written(two: Two, capsys: Printed, tmp_path: Path):
    before = sorted(path for path in tmp_path.rglob("*"))
    assert two.run() == 0
    assert sorted(path for path in tmp_path.rglob("*")) == before
    assert capsys.readouterr().out.splitlines()[-1].startswith("step=moved status=ok ")


def test_what_it_writes_is_never_written_where_git_would_take_it_in(
    two: Two, capsys: Printed, tmp_path: Path
):
    top = tmp_path / "repository"
    (top / ".git").mkdir(parents=True)
    arguments = ["moved", *two.folders, "--root", str(top), "--searches", str(SEARCHES)]
    assert main([*arguments, "--out", str(top / "docs" / "moved")]) == 2
    out = capsys.readouterr()
    assert out.out == "" and "is inside the repository" in out.err
    assert not (top / "docs").exists()


@pytest.mark.parametrize("which", [0, 1])
def test_a_release_that_cannot_be_read_is_not_compared(
    two: Two, capsys: Printed, tmp_path: Path, which: int
):
    folders = list(two.folders)
    folders[which] = str(tmp_path / "lon-2026-09-23-09")
    assert main(["moved", *folders, "--root", str(REPOSITORY)]) == 2
    out = capsys.readouterr()
    assert out.out == "" and "a release cannot be read" in out.err
    assert out.err.count("\n") == 1


def test_a_release_with_no_lock_beside_it_is_not_compared(
    two: Two, capsys: Printed, tmp_path: Path
):
    """A release is read with the folder of its build, and held to the hashes there, so a
    lock that cannot be read is one that was changed since."""
    copied = tmp_path / "copy"
    shutil.copytree(two.before.out, copied)
    (copied / f"{BEFORE}-build" / "lock.json").write_text("{}", encoding="utf-8")
    assert main(["moved", str(copied / BEFORE), two.folders[1], "--root", str(REPOSITORY)]) == 2
    said = capsys.readouterr().err
    assert "a release cannot be read" in said and "[build_is_as_it_was_written]" in said


def test_two_releases_of_two_cities_are_not_compared(two: Two, capsys: Printed):
    made_up = REPOSITORY / "data" / "fixtures" / "synthetic" / "syn-2026-09-23-01"
    assert main(["moved", str(made_up), two.folders[1], "--root", str(REPOSITORY)]) == 2
    out = capsys.readouterr()
    assert out.out == "" and "are not of one city" in out.err
    with pytest.raises(moved.OtherCity):
        moved.compare(moved.open_build(made_up), moved.open_build(Path(two.folders[1])))


def test_the_searches_are_read_from_the_file_that_is_named(
    two: Two, capsys: Printed, tmp_path: Path
):
    assert two.run("--searches", str(tmp_path / "absent.json")) == 2
    out = capsys.readouterr()
    assert out.out == "" and "The searches cannot be read" in out.err


def test_moved_follows_the_steps_that_keep_and_take_a_release():
    steps = list(cli.STEPS)
    assert steps.index("take") < steps.index("moved") < steps.index("why")
    assert cli.parse(["moved", "a", "b", "--out", "scratch/moved"]).command == "moved"
