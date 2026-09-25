"""What moved between two builds whose catalogues differ in version.

It is when a person most needs the step: after a measure or a vibe was added, or a recipe
changed. The town is Quillhaven and Tallowgate, two boroughs that do not exist. It is built
twice from the same made-up files, as `preview` builds it. The first build is then written
again as a build under the catalogue before would have written it: a measure and a vibe
fewer, a recipe of other parts, a share that stood otherwise, a label that was another,
and no word of how sure a vibe is, which a release did not say then. So nothing of the
release moved between the two but what the catalogue moved.
Nothing here reaches a network or a store of real files.
"""

import dataclasses
import hashlib
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import public_log
import pytest
from burro_core.catalogue import CATALOGUE_VERSION, FEATURES, TAGS
from burro_core.ids import FeatureId, Sureness, TagId
from burro_core.release import ReleaseError
from burro_pipeline.release.read import MEANING, read_built, read_served
from burro_pipeline.upkeep import moved, written
from burro_pipeline.upkeep.cli import main
from burro_pipeline.upkeep.searches import NOT_IN_IT, read_searches

from ..assemble.support import RELEASE, Made, made

REPOSITORY = Path(__file__).resolve().parents[4]
SEARCHES = REPOSITORY / "tools" / "desk" / "panel" / "searches.json"
BEFORE, AFTER = RELEASE, "lon-2026-09-23-02"
OLDER = CATALOGUE_VERSION - 1
# What the catalogue before did not hold: a measure that stands in no recipe, and a vibe
# that two of the three searches ask for.
CAME, CAME_AS_A_VIBE = FeatureId.WATER_ACCESS, TagId.QUIET_RESIDENTIAL
# The measure that was labelled otherwise, and what its label was.
RELABELLED, WAS_LABELLED = FeatureId.AIR_NO2, "Nitrogen dioxide, as it was labelled then"
# The recipe Leafy had: the parts it has, two of them at other shares.
LEAFY_WAS = {"land_gardens": 50, "land_woodland": 20, "green_cover": 30}
# The recipe Village feel had: three parts that are gone, and two that stand at other shares.
VILLAGE_WAS = (
    ("independents_nearby", 25, "high"),
    ("centre_small", 20, "high"),
    ("centre_compact", 20, "high"),
    ("homes_pre1919", 20, "high"),
    ("conservation_cover", 15, "high"),
)
# What no line may hold: the name of an area or of a borough of the town, and an id of one.
NAMED = ("Quillhaven", "Tallowgate", "lon-ne")
Printed = pytest.CaptureFixture[str]
Documents = dict[str, Any]
Change = Callable[[Documents], object]


def _written(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


def written_again(out: Path, release: str, change: Change) -> None:
    """Write a build again with its files changed, as the build itself would have
    written them: the manifest names each file by its new hash, and the hashes of the
    build name the manifest by its own."""
    folder, beside = out / release, out / f"{release}-build"
    found: Documents = {
        path.name: json.loads(path.read_bytes()) for path in sorted(folder.glob("*.json"))
    }
    change(found)
    manifest = found.pop("manifest.json")
    for name, document in found.items():
        (folder / name).write_bytes(_written(document))
    for entry in manifest["files"]:
        content = (folder / entry["name"]).read_bytes()
        entry.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
    (folder / "manifest.json").write_bytes(_written(manifest))
    hashes = json.loads((beside / "hashes.json").read_bytes())
    hashes["manifest_sha256"] = hashlib.sha256(_written(manifest)).hexdigest()
    (beside / "hashes.json").write_bytes(_written(hashes))


def vibe_of(found: Documents, tag_id: str) -> dict[str, Any]:
    return next(one for one in found["catalogue.json"]["vibes"] if one["tag_id"] == tag_id)


def of_the_catalogue_before(found: Documents) -> None:
    """The files of a build, as a build under the catalogue before would have written them."""
    found["manifest.json"]["catalogue_version"] = OLDER
    catalogue = found["catalogue.json"]
    catalogue["catalogue_version"] = OLDER
    catalogue["metrics"] = [one for one in catalogue["metrics"] if one["feature_id"] != CAME]
    catalogue["vibes"] = [one for one in catalogue["vibes"] if one["tag_id"] != CAME_AS_A_VIBE]
    rows = found["features.json"]["rows"]
    found["features.json"]["rows"] = [row for row in rows if row["feature_id"] != CAME]
    rows = found["tags.json"]["rows"]
    found["tags.json"]["rows"] = [row for row in rows if row["tag_id"] != CAME_AS_A_VIBE]
    for one in catalogue["vibes"]:
        del one["sureness"]
    for term in vibe_of(found, "leafy")["terms"]:
        term["hundredths"] = LEAFY_WAS[term["feature_id"]]
    vibe_of(found, "village_feel").update(
        terms=[
            {"feature_id": part, "hundredths": share, "reading": reading}
            for part, share, reading in VILLAGE_WAS
        ],
        strip=True,
    )
    labelled = [one for one in catalogue["metrics"] if one["feature_id"] == RELABELLED]
    labelled[0]["label"] = WAS_LABELLED


@dataclasses.dataclass(frozen=True)
class Two:
    """Two made-up builds on disk, of two versions of the catalogue."""

    older: Made
    newer: Made

    @property
    def folders(self) -> tuple[str, str]:
        return str(self.older.out / BEFORE), str(self.newer.out / AFTER)

    def compared(self, turned: bool = False) -> dict[str, Any]:
        builds = [moved.open_build(Path(folder)) for folder in self.folders]
        found = moved.compare(
            *(reversed(builds) if turned else builds),
            searches=read_searches(SEARCHES, REPOSITORY),
        )
        return json.loads(json.dumps(found))

    def run(self, *more: str) -> int:
        return main(["moved", *self.folders, "--root", str(REPOSITORY), *more])


@pytest.fixture(scope="module")
def two(tmp_path_factory: pytest.TempPathFactory) -> Two:
    root = tmp_path_factory.mktemp("catalogues")
    older, newer = made(root / "older"), made(root / "newer")
    assert older.run() == 0 and newer.run("--release-id", AFTER) == 0
    written_again(older.out, BEFORE, of_the_catalogue_before)
    return Two(older, newer)


@pytest.fixture(scope="module")
def found(two: Two) -> dict[str, Any]:
    return two.compared()


def copied(two: Two, to: Path, change: Change) -> Path:
    """A copy of the build of the catalogue before, with one thing more changed in its
    files, and the folder of its release."""
    shutil.copytree(two.older.out, to)
    written_again(to, BEFORE, change)
    return to / BEFORE


# Each build is read by its own catalogue


def test_a_build_of_the_catalogue_before_is_not_served_and_is_read_by_its_own(two: Two):
    folder = Path(two.folders[0])
    with pytest.raises(ReleaseError) as refused:
        read_served(folder)
    assert refused.value.rule == "versions_match"
    release = read_built(folder)
    assert release.manifest.catalogue_version == OLDER
    assert CAME_AS_A_VIBE not in {vibe.tag_id for vibe in release.vibes}
    assert CAME not in {metric.feature_id for metric in release.metrics}
    (village,) = [vibe for vibe in release.vibes if vibe.tag_id is TagId.VILLAGE_FEEL]
    assert tuple(
        (term.feature_id.value, term.hundredths, term.reading.value) for term in village.terms
    ) == (VILLAGE_WAS)
    assert village.sureness is Sureness.AS_THE_REST


def test_two_builds_whose_catalogues_differ_are_compared(two: Two, capsys: Printed):
    assert two.run() == 0
    out = capsys.readouterr()
    assert out.err == ""
    assert out.out.splitlines()[-1].startswith(
        f"step=moved status=ok before={BEFORE} after={AFTER} "
        f"catalogue_before={OLDER} catalogue_after={CATALOGUE_VERSION} areas=3 "
    )


def test_it_says_the_version_of_the_catalogue_on_each_side(found: dict[str, Any]):
    assert (found["catalogue"]["before"], found["catalogue"]["after"]) == (
        OLDER,
        CATALOGUE_VERSION,
    )
    assert found["before"]["catalogue_version"] == OLDER
    assert found["after"]["catalogue_version"] == CATALOGUE_VERSION
    assert (found["before"]["release_id"], found["after"]["release_id"]) == (BEFORE, AFTER)


# What came and went of the catalogue itself


def test_a_measure_and_a_vibe_that_the_catalogue_gained_are_said_to_have_come(
    found: dict[str, Any],
):
    assert found["measures"]["came"] == [
        {
            "id": CAME.value,
            "label": FEATURES[CAME].label,
            "unit": "%",
            "with_a_figure": 3,
        }
    ]
    assert found["measures"]["went"] == []
    assert found["vibes"]["came"] == [{"id": CAME_AS_A_VIBE.value, "label": "Quiet streets"}]
    assert found["vibes"]["went"] == []
    assert found["before"]["measures"] + 1 == found["after"]["measures"] == 25
    assert found["before"]["vibes"] + 1 == found["after"]["vibes"] == 14


def test_a_measure_and_a_vibe_that_the_catalogue_lost_are_said_to_have_gone(two: Two):
    turned = two.compared(turned=True)
    assert [one["id"] for one in turned["measures"]["went"]] == [CAME.value]
    assert [one["id"] for one in turned["vibes"]["went"]] == [CAME_AS_A_VIBE.value]
    assert (turned["catalogue"]["before"], turned["catalogue"]["after"]) == (
        CATALOGUE_VERSION,
        OLDER,
    )


def of(found: dict[str, Any], what: str, of_id: str) -> dict[str, Any]:
    (one,) = [one for one in found["catalogue"][what] if one["id"] == of_id]
    return one


def test_a_share_of_a_recipe_that_changed_is_said_with_what_it_was(found: dict[str, Any]):
    leafy = of(found, "vibes", "leafy")
    assert leafy["label"] == "Leafy"
    assert leafy["shares"] == [
        {
            "id": "land_gardens",
            "label": FEATURES[FeatureId.LAND_GARDENS].label,
            "was": 50,
            "now": 40,
        },
        {
            "id": "land_woodland",
            "label": FEATURES[FeatureId.LAND_WOODLAND].label,
            "was": 20,
            "now": 30,
        },
    ]
    # A part that stands as it stood is not said, and no part of it came or went.
    assert (leafy["parts_came"], leafy["parts_went"], leafy["names"]) == ([], [], [])
    assert leafy["rough"] == {"was": False, "now": False}


def test_a_part_of_a_recipe_that_came_or_went_is_said_with_its_share_and_its_end(
    found: dict[str, Any],
):
    village = of(found, "vibes", "village_feel")
    assert [(one["id"], one["share"], one["reading"]) for one in village["parts_came"]] == [
        ("highstreet_conserved", 45, "high"),
        ("homes_density", 30, "low"),
    ]
    assert [(one["id"], one["share"], one["reading"]) for one in village["parts_went"]] == [
        ("independents_nearby", 25, "high"),
        ("centre_small", 20, "high"),
        ("centre_compact", 20, "high"),
    ]
    assert [(one["id"], one["was"], one["now"]) for one in village["shares"]] == [
        ("homes_pre1919", 20, 15),
        ("conservation_cover", 15, 10),
    ]
    # Each part is said by the name core gives the measure, whether a build carries it or not.
    came = village["parts_came"][0]
    assert came["label"] == FEATURES[FeatureId.HIGHSTREET_CONSERVED].label


def test_a_part_that_is_read_from_its_other_end_went_and_came(two: Two, tmp_path: Path):
    def turned_round(files: Documents) -> None:
        for term in vibe_of(files, "homes")["terms"]:
            if term["feature_id"] == "homes_density":
                term["reading"] = "low" if term["reading"] == "high" else "high"

    before = moved.open_build(copied(two, tmp_path / "turned", turned_round))
    after = moved.open_build(Path(two.folders[1]))
    homes = of(json.loads(json.dumps(moved.compare(before, after))), "vibes", "homes")
    assert [(one["id"], one["share"]) for one in homes["parts_went"]] == [("homes_density", 35)]
    assert [(one["id"], one["share"]) for one in homes["parts_came"]] == [("homes_density", 35)]
    assert homes["parts_went"][0]["reading"] != homes["parts_came"][0]["reading"]
    assert homes["shares"] == []


def test_a_vibe_that_became_a_rough_guide_says_so_and_so_does_one_that_ceased_to_be(
    two: Two, found: dict[str, Any]
):
    assert of(found, "vibes", "village_feel")["rough"] == {"was": False, "now": True}
    assert TAGS[TagId.VILLAGE_FEEL].sureness is Sureness.ROUGH_GUIDE
    turned = two.compared(turned=True)
    assert of(turned, "vibes", "village_feel")["rough"] == {"was": True, "now": False}
    assert moved.counted(found)["rough_came"] == moved.counted(turned)["rough_went"] == 1
    assert moved.counted(found)["rough_went"] == moved.counted(turned)["rough_came"] == 0


def test_a_label_of_a_measure_that_changed_is_said_with_what_it_was(found: dict[str, Any]):
    assert found["catalogue"]["measures"] == [
        {
            "id": RELABELLED.value,
            "label": FEATURES[RELABELLED].label,
            "names": [{"what": "label", "was": WAS_LABELLED, "now": FEATURES[RELABELLED].label}],
        }
    ]


def test_a_name_of_a_vibe_or_of_an_end_of_one_that_changed_is_said(two: Two, tmp_path: Path):
    def named_otherwise(files: Documents) -> None:
        vibe_of(files, "homes").update(label="Homes", short_label="Homes", low_end="Mostly houses")

    before = moved.open_build(copied(two, tmp_path / "named", named_otherwise))
    after = moved.open_build(Path(two.folders[1]))
    homes = of(json.loads(json.dumps(moved.compare(before, after))), "vibes", "homes")
    now = TAGS[TagId.HOMES]
    assert homes["names"] == [
        {"what": "label", "was": "Homes", "now": now.label},
        {"what": "low_end", "was": "Mostly houses", "now": now.low_end},
    ]
    assert (homes["parts_came"], homes["parts_went"], homes["shares"]) == ([], [], [])


def test_a_vibe_of_which_nothing_of_the_catalogue_changed_is_not_said(found: dict[str, Any]):
    assert [one["id"] for one in found["catalogue"]["vibes"]] == ["leafy", "village_feel"]
    assert [one["id"] for one in found["catalogue"]["measures"]] == [RELABELLED.value]


def test_the_catalogue_is_counted(found: dict[str, Any]):
    counts = moved.counted(found)
    assert {name: count for name, count in counts.items() if count} == {
        "areas": 3,
        "measures": 25,
        "measures_came": 1,
        "vibes": 14,
        "vibes_came": 1,
        "vibes_moved": 2,
        "searches": 3,
        "searches_moved": 1,
        "parts_came": 2,
        "parts_went": 3,
        "shares_changed": 4,
        "names_changed": 1,
        "rough_came": 1,
    }


# What both builds hold is compared as it always was


def test_what_both_builds_hold_is_compared_as_between_two_builds_of_one_catalogue(
    found: dict[str, Any],
):
    # The two were built from the same files, so no figure, price or file moved.
    assert found["measures"]["moved"] == [] and found["costs"] == []
    assert found["measures"]["same"] == 24 and found["vibes"]["same"] == 13
    assert found["areas"]["same"] == 3 and found["areas"]["moved_most"] == []
    files = found["files"]
    assert (files["compared"], files["changed"], files["came"], files["went"]) == (
        True,
        [],
        [],
        [],
    )
    assert files["same"] > 10
    # A vibe whose recipe changed is said among the vibes too, though no band of it moved:
    # the bands of the older build stand as they were written.
    assert [
        (one["id"], one["recipe_changed"], one["changed"], one["gained"], one["lost"])
        for one in found["vibes"]["moved"]
    ] == [("leafy", True, 0, 0, 0), ("village_feel", True, 0, 0, 0)]


def test_a_band_that_moved_between_two_catalogues_is_counted(two: Two, tmp_path: Path):
    def a_band_higher(files: Documents) -> None:
        rows = [row for row in files["tags.json"]["rows"] if row["tag_id"] == "leafy"]
        raws = sorted(row["raw"] for row in rows)
        assert len(set(raws)) == 3, "the three areas of the town stand apart on Leafy"
        lowest, highest = (
            next(row for row in rows if row["raw"] == raw) for raw in (raws[0], raws[-1])
        )
        # The two at the ends change places: every figure that is ranked on goes with them.
        for name in ("raw", "score", "band", "spread_low", "spread_high"):
            lowest[name], highest[name] = highest[name], lowest[name]

    before = moved.open_build(copied(two, tmp_path / "banded", a_band_higher))
    found = moved.compare(before, moved.open_build(Path(two.folders[1])))
    (leafy,) = [one for one in found["vibes"]["moved"] if one["id"] == "leafy"]
    assert (leafy["changed"], leafy["up"], leafy["down"]) == (2, 1, 1)


# The searches


def test_a_search_is_ranked_on_each_build_by_what_that_build_holds(found: dict[str, Any]):
    """Two of the searches ask for a vibe the older build does not hold. That is said of
    that side, and the search is ranked without it there."""
    gone = NOT_IN_IT.format(label="Quiet streets")
    by_id = {one["id"]: one for one in found["searches"]}
    for search in ("the_founders_sentence", "a_family_buying_a_house"):
        assert gone in by_id[search]["before"]["notes"], search
        assert gone not in by_id[search]["after"]["notes"], search
        assert by_id[search]["before"]["ranked"] == by_id[search]["after"]["ranked"] == 3
    # With the vibe, the first of them puts another area first. The second puts the areas
    # in the order it put them in without it: what is said is that it was ranked without.
    first, second = by_id["the_founders_sentence"], by_id["a_family_buying_a_house"]
    assert (first["same"], first["kept"], first["reordered"]) == (False, 3, 2)
    assert (second["same"], second["kept"], second["reordered"]) == (True, 3, 0)
    # The third asks for it of neither, and is ranked the same on both.
    third = by_id["nights_out_well_connected"]
    assert third["same"] is True and third["before"]["notes"] == third["after"]["notes"]


def test_what_is_written_says_which_build_a_search_was_ranked_without_a_vibe_on(
    found: dict[str, Any],
):
    page = written.page(found)
    gone = NOT_IN_IT.format(label="Quiet streets")
    assert page.count(f"- Before: {gone}") == 2
    assert f"- After: {gone}" not in page and f"- {gone}" not in page
    # What is said of both builds alike is said once, of neither.
    pace = NOT_IN_IT.format(label="Going out")
    assert f"- {pace}" in page and f"Before: {pace}" not in page


# What the step prints, and what it writes


def test_the_step_prints_counts_and_ids_of_the_catalogue_and_never_an_area(
    two: Two, capsys: Printed, tmp_path: Path
):
    assert two.run("--out", str(tmp_path / "out")) == 0
    out = capsys.readouterr()
    lines = out.out.splitlines()
    assert lines == [
        f"step=moved feature={CAME.value} came=1",
        f"step=moved feature={RELABELLED.value} names_changed=1",
        f"step=moved vibe={CAME_AS_A_VIBE.value} came=1",
        "step=moved vibe=leafy areas=3 changed=0 up=0 down=0 gained=0 lost=0",
        "step=moved vibe=village_feel areas=3 changed=0 up=0 down=0 gained=0 lost=0",
        "step=moved vibe=leafy parts_came=0 parts_went=0 shares_changed=2 names_changed=0 "
        "rough_came=0 rough_went=0",
        "step=moved vibe=village_feel parts_came=2 parts_went=3 shares_changed=2 "
        "names_changed=0 rough_came=1 rough_went=0",
        "step=moved search=1 kept=3 came=0 went=0 reordered=2",
        "step=moved search=2 kept=3 came=0 went=0 reordered=0",
        "step=moved search=3 kept=3 came=0 went=0 reordered=0",
        f"step=moved status=ok before={BEFORE} after={AFTER} catalogue_before={OLDER} "
        f"catalogue_after={CATALOGUE_VERSION} areas=3 areas_came=0 areas_went=0 "
        "areas_renamed=0 areas_redrawn=0 measures=25 measures_came=1 measures_went=0 "
        "measures_moved=0 vibes=14 vibes_came=1 vibes_went=0 vibes_moved=2 costs_moved=0 "
        "files_changed=0 files_came=0 files_went=0 searches=3 searches_moved=1 parts_came=2 "
        "parts_went=3 shares_changed=4 names_changed=1 rough_came=1 rough_went=0",
    ]
    assert all(public_log.is_public(line) for line in lines)
    assert out.err == ""
    for name in (*NAMED, WAS_LABELLED, "labelled"):
        assert name not in out.out
    assert "." not in out.out


def test_what_it_writes_says_what_came_and_went_of_the_catalogue(
    two: Two, found: dict[str, Any], capsys: Printed, tmp_path: Path
):
    out = tmp_path / "out"
    assert two.run("--out", str(out)) == 0
    capsys.readouterr()
    assert json.loads((out / "moved.json").read_text(encoding="utf-8")) == found
    page = (out / "moved.md").read_text(encoding="utf-8")
    assert page == written.page(found)
    for said in (
        f"## The catalogue: version {OLDER} before, and version {CATALOGUE_VERSION} after",
        "Measures: 1 came, and 0 went. Vibes: 1 came, and 0 went. Each is named below.",
        "### Names and labels that changed: 1",
        f"| {FEATURES[RELABELLED].label} | {RELABELLED.value} | Its label | {WAS_LABELLED} | "
        f"{FEATURES[RELABELLED].label} |",
        "### Leafy: its recipe",
        f"| {FEATURES[FeatureId.LAND_GARDENS].label} | land_gardens | 50 | 40 | "
        "Its share changed |",
        "### Village feel: its recipe",
        "Village feel became a rough guide.",
        f"| {FEATURES[FeatureId.HIGHSTREET_CONSERVED].label} | highstreet_conserved |  | 45 | "
        "Came, read from its high end |",
        f"| {FEATURES[FeatureId.HOMES_DENSITY].label} | homes_density |  | 30 | "
        "Came, read from its low end |",
        f"| {FEATURES[FeatureId.CENTRE_SMALL].label} | centre_small | 20 |  | "
        "Went, read from its high end |",
        f"| {FEATURES[FeatureId.HOMES_PRE1919].label} | homes_pre1919 | 20 | 15 | "
        "Its share changed |",
    ):
        assert said in page, said
    # The table of the two builds says the catalogue of each.
    assert re.search(rf"^\| {BEFORE} \|.*\| {OLDER} \|$", page, re.MULTILINE)
    assert re.search(rf"^\| {AFTER} \|.*\| {CATALOGUE_VERSION} \|$", page, re.MULTILINE)


def test_two_builds_of_one_catalogue_say_that_nothing_of_it_changed(two: Two):
    same = moved.open_build(Path(two.folders[1]))
    found = moved.compare(same, same)
    assert found["catalogue"] == {
        "before": CATALOGUE_VERSION,
        "after": CATALOGUE_VERSION,
        "measures": [],
        "vibes": [],
    }
    page = written.page(json.loads(json.dumps(found)))
    assert f"## The catalogue: version {CATALOGUE_VERSION} in both" in page
    assert "Nothing of the catalogue changed between the two." in page
    assert not [line for line in moved.lines(found) if "parts_came" in line.split(" status=")[0]]


# What is refused, and why


def refused(folder: Path, other: str, capsys: Printed) -> str:
    assert main(["moved", str(folder), other, "--root", str(REPOSITORY)]) == 2
    out = capsys.readouterr()
    assert out.out == "" and out.err.count("\n") == 1
    return out.err


def test_a_build_the_code_cannot_read_at_all_is_refused_and_the_words_say_why(
    two: Two, capsys: Printed, tmp_path: Path
):
    """A build of a catalogue that is newer than the code holds what the code has no
    record for. It is not read in part."""

    def of_a_catalogue_to_come(files: Documents) -> None:
        files["manifest.json"]["catalogue_version"] = CATALOGUE_VERSION + 1
        files["catalogue.json"]["catalogue_version"] = CATALOGUE_VERSION + 1
        vibe_of(files, "leafy")["said_since"] = "what a later catalogue says of a vibe"

    said = refused(copied(two, tmp_path / "newer", of_a_catalogue_to_come), two.folders[1], capsys)
    assert "a release cannot be read" in said and "[shape_is_valid]" in said
    assert "catalogue.json" in said and MEANING["shape_is_valid"] in said
    assert "said_since" not in said and "later catalogue" not in said


def no_band(files: Documents) -> None:
    placed = next(row for row in files["tags.json"]["rows"] if row["band"] is not None)
    placed.update(band=None, spread_low=None, spread_high=None)


# What a build may not be, whatever its catalogue, with the rule that says so.
NOT_WHOLE: list[tuple[str, Change]] = [
    ("versions_are_its_own", lambda files: files["manifest.json"].update(schema_version=3)),
    (
        "versions_are_its_own",
        lambda files: files["catalogue.json"].update(catalogue_version=OLDER - 1),
    ),
    ("rows_are_complete", lambda files: files["features.json"]["rows"].pop()),
    ("bands_match_raw", no_band),
]


@pytest.mark.parametrize(("rule", "change"), NOT_WHOLE)
def test_a_build_that_does_not_hold_together_is_not_compared_whatever_its_catalogue(
    two: Two, capsys: Printed, tmp_path: Path, rule: str, change: Change
):
    said = refused(copied(two, tmp_path / "broken", change), two.folders[1], capsys)
    assert "a release cannot be read" in said and f"[{rule}]" in said
    assert MEANING[rule] in said


def test_a_build_that_was_changed_since_it_was_built_is_not_compared(
    two: Two, capsys: Printed, tmp_path: Path
):
    shutil.copytree(two.older.out, tmp_path / "changed")
    path = tmp_path / "changed" / BEFORE / "tags.json"
    path.write_bytes(path.read_bytes() + b" ")
    said = refused(tmp_path / "changed" / BEFORE, two.folders[1], capsys)
    assert "a release cannot be read" in said and "[files_match_manifest]" in said


def test_nothing_that_serves_a_release_or_checks_one_reads_it_by_its_own_catalogue():
    """What is read by its own catalogue may hold what core no longer does. So it is read
    so where two builds are held against each other, and nowhere else."""
    reads = re.compile(r"\b(?:open_built|read_built|RULES_OF_ITS_OWN)\b")
    may = {
        "packages/core/src/burro_core/release.py",
        "packages/pipeline/src/burro_pipeline/release/read.py",
        "packages/pipeline/src/burro_pipeline/upkeep/moved.py",
    }
    found = {
        path.relative_to(REPOSITORY).as_posix()
        for folder in ("packages", "services", "tools", "evals")
        for path in (REPOSITORY / folder).rglob("*.py")
        if "tests" not in path.parts and reads.search(path.read_text(encoding="utf-8"))
    }
    assert found == may
    # The service and the check of a release read it as it is served.
    api = (REPOSITORY / "services/api/src/burro_api/loading.py").read_text(encoding="utf-8")
    assert "open_served" in api
