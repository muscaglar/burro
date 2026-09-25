"""A file of changes that was written by hand is refused by the build.

The file is plain, so that it can be read with no panel. So it can be written with none,
and nothing the panel refuses protects a build. What protects it is what the reader of the
file, the build and core refuse. Each test here writes by hand a line the panel would never
write, hands the file to `preview`, and holds that the build stops, names the line and the
rule, and writes nothing.

The town is Quillhaven and Tallowgate, which do not exist. Every reason is made up.
"""

import hashlib
import io
import json
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from burro_core import catalogue
from burro_core.catalogue import TAGS
from burro_core.ids import FeatureId, TagId
from burro_core.release import EVIDENCE, HASHES, LOCK
from burro_pipeline import changes
from burro_pipeline.derive import brand_table
from burro_pipeline.release import cli as release_check
from burro_pipeline.release.read import read_served

from ..evidence.support import GIT, git
from .published import Published, published
from .support import RELEASE, Made, made, made_once

pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to publish a file of changes")

Printed = pytest.CaptureFixture[str]
CANARY = "Zzyzx Parva canary reason"
LEAFY = changes.recipe_of(TAGS[TagId.LEAFY])
PACE = changes.recipe_of(TAGS[TagId.PACE])
FAMILY_AREA = changes.recipe_of(TAGS[TagId.FAMILY_AREA])


def a_line(n: int = 1, **changed: Any) -> dict[str, Any]:
    held: dict[str, Any] = {
        "n": n,
        "on": "2026-09-25",
        "by": "r1",
        "what": "recipe",
        "of": "leafy",
        "was": LEAFY,
        "now": {"land_gardens": 20, "land_woodland": 50, "green_cover": 30},
        "why": CANARY,
        "takes_back": None,
    }
    return {**held, **changed}


def named(of: str, **now: Any) -> dict[str, Any]:
    was = changes.names_of(TAGS[TagId(of)])
    return a_line(what="name", of=of, was=was, now={**was, **now})


def with_a_part(part: str, tag_id: str = "leafy", honest: bool = True) -> dict[str, Any]:
    """A recipe that gains a part. Where it is not honest, it says the part was there."""
    was = changes.recipe_of(TAGS[TagId(tag_id)])
    first = next(iter(was))
    now = {**was, first: was[first] - 10, part: 10}
    return a_line(of=tag_id, was=was if honest else {**was, part: 0}, now=now)


def refused(folder: Path, capsys: Printed, *lines: dict[str, Any], **how: Any) -> str:
    """Hand a build a file that was published, and give what it said as it stopped."""
    found = made_once(folder / "build")
    held = published(folder, *lines, **how)
    assert found.run(*held.arguments()) == 2
    said = capsys.readouterr()
    assert "Zzyzx" not in said.out + said.err, "a refusal never repeats a reason"
    assert not found.out.exists(), "nothing was written"
    return said.err


def rule_of(said: str) -> tuple[int, str]:
    """The line and the rule a build named as it stopped. What it noted before is left out."""
    start = "error: the file of changes cannot be built on: line "
    (error,) = [line for line in said.splitlines() if line.startswith("error: ")]
    assert error.startswith(start), error
    number, _, rest = error.removeprefix(start).partition(" breaks the rule ")
    return int(number), rest.split(".")[0]


# 1, 2 and 3. A recipe gains a part


NO_FEATURE = ("ethnic_group", "religion", "country_of_birth", "household_income", "no_such_part")
A_FEATURE = ("air_no2", "venue_food_drink", "grocer_premium_nearby", "brand_lidl")


@pytest.mark.parametrize("part", [*NO_FEATURE, *A_FEATURE])
@pytest.mark.parametrize("honest", [True, False], ids=["as it is", "as if it had been there"])
def test_a_recipe_gains_no_part(tmp_path: Path, capsys: Printed, part: str, honest: bool):
    said = refused(tmp_path, capsys, with_a_part(part, honest=honest))
    assert rule_of(said) in {(1, "change_is_of_its_kind"), (1, changes.STALE)}


def test_a_part_is_put_in_the_place_of_another_by_no_line(tmp_path: Path, capsys: Printed):
    now = {"air_no2": 40, "land_woodland": 30, "green_cover": 30}
    assert rule_of(refused(tmp_path, capsys, a_line(now=now)))[1] == "change_is_of_its_kind"


def test_a_second_line_cannot_build_on_a_part_the_first_was_refused(
    tmp_path: Path, capsys: Printed
):
    first = with_a_part("air_no2", honest=False)
    second = a_line(2, was=first["now"], now={**first["now"], "air_no2": 20, "land_woodland": 20})
    # The second line is the one that stands, and it holds a part core's recipe does not.
    assert rule_of(refused(tmp_path, capsys, first, second)) == (2, "recipe_holds_cores_parts")


# 4 and 5. A part that counts who lived somewhere


@pytest.mark.parametrize(
    "line",
    [
        # No line says which end a part is read from: a share is a whole number.
        a_line(of="family_area", was=FAMILY_AREA, now={**FAMILY_AREA, "reading": "low"}),
        a_line(
            of="family_area",
            was=FAMILY_AREA,
            now={
                **FAMILY_AREA,
                "households_dependent_children": {"hundredths": 40, "reading": "low"},
            },
        ),
        a_line(of="family_area", was=FAMILY_AREA, now=FAMILY_AREA, reading="low"),
        a_line(of="family_area", was=FAMILY_AREA, now={**FAMILY_AREA, "park_proximity": -15}),
        # Nor may such a part be put in a scale between two ends, or in any other vibe.
        with_a_part("households_dependent_children", "pace"),
        with_a_part("households_dependent_children", "pace", honest=False),
        with_a_part("residents_aged_20_34", "leafy"),
    ],
)
def test_a_part_that_counts_residents_is_turned_round_or_moved_by_no_line(
    tmp_path: Path, capsys: Printed, line: dict[str, Any]
):
    number, rule = rule_of(refused(tmp_path, capsys, line))
    assert number == 1
    assert rule in {
        "change_is_of_its_kind",
        "line_is_a_line",
        "recipe_keeps_its_rules",
        changes.STALE,
    }


@pytest.mark.parametrize(
    "hundredths", [(41, 25, 19, 15), (59, 20, 11, 10), (30, 41, 15, 14), (100, 0, 0, 0)]
)
def test_no_part_is_given_more_than_its_limit_where_residents_are_counted(
    tmp_path: Path, capsys: Printed, hundredths: tuple[int, ...]
):
    now = dict(zip(FAMILY_AREA, hundredths, strict=True))
    said = refused(tmp_path, capsys, a_line(of="family_area", was=FAMILY_AREA, now=now))
    assert rule_of(said) == (1, "recipe_keeps_its_rules")


# 6. A vibe that is held off


def test_a_vibe_the_build_places_no_area_on_is_placed_by_no_change_to_its_shares(
    tmp_path: Path, capsys: Printed
):
    # The made-up build holds half of the recipe of Going out, so no area has a band.
    # By hand, its shares are moved to the two parts the build holds.
    now = dict(zip(PACE, (1, 58, 40, 1), strict=True))
    said = refused(tmp_path, capsys, a_line(of="pace", was=PACE, now=now))
    assert "error: the release breaks a rule of the contract" in said
    assert "[held_off_stays_held_off]" in said


def test_a_vibe_that_is_held_off_is_placed_by_no_change_to_its_shares(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """For a while, Parks close by places an area only where what a park offers has a
    figure, which the made-up build leaves out.

    No vibe is held off today. Village feel was, until the founder chose on 2026-09-25 to
    serve it on another recipe, as a rough guide. What holding a vibe off does is kept for
    any vibe that is held off in future, and is held here on a vibe that is not.
    """
    assert dict(catalogue.PLACED_ONLY_WITH) == {}
    held_off = {TagId.PARKS_CLOSE_BY: frozenset({FeatureId.PARK_FACILITIES})}
    monkeypatch.setattr(catalogue, "PLACED_ONLY_WITH", held_off)
    held = changes.recipe_of(TAGS[TagId.PARKS_CLOSE_BY])
    now = dict(zip(held, (50, 40, 10), strict=True))
    # Files of its own: core is changed here for a while, and nothing that is made once
    # for every test is made while it is.
    found = made(tmp_path / "build")
    line = a_line(of="parks_close_by", was=held, now=now)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run(*published(tmp_path, line).arguments()) == 0
    release = read_served(found.release)
    assert release.placed(TagId.PARKS_CLOSE_BY) is False
    rows = [row for row in release.tags if row.tag_id is TagId.PARKS_CLOSE_BY]
    assert rows and all(row.raw is None and row.band is None for row in rows)
    # Any other vibe is placed as it was.
    assert release.placed(TagId.BUILT_AGE)


# 7. A name or a label


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        (named("leafy", label="Students"), "name_is_plain"),
        (named("leafy", label="Polish families"), "name_is_plain"),
        (named("leafy", label="Top 10 streets"), "name_is_plain"),
        (named("leafy", label="Safe streets"), "name_is_plain"),
        (named("pace", high_end="Rough"), "name_is_plain"),
        (
            a_line(
                what="cannot_see",
                of="leafy",
                was=changes.lines_of(TAGS[TagId.LEAFY]),
                now=[*changes.lines_of(TAGS[TagId.LEAFY]), "Trees under 5 m."],
            ),
            "says_what_it_cannot_see",
        ),
    ],
)
def test_a_name_that_holds_a_word_for_people_or_a_figure_is_refused_by_its_line(
    tmp_path: Path, capsys: Printed, line: dict[str, Any], rule: str
):
    assert rule_of(refused(tmp_path, capsys, line)) == (1, rule)


@pytest.mark.parametrize(
    "now",
    [
        {"label": "State primary schools within 500 m of home", "short_label": "Schools"},
        {"label": "State primary schools nearby", "short_label": "Schools within 800 m"},
        {"label": "Schools for students", "short_label": "Schools"},
    ],
)
def test_a_label_that_holds_a_figure_of_its_own_stops_the_build(
    tmp_path: Path, capsys: Printed, now: dict[str, str]
):
    core = changes.FEATURES[changes.FeatureId.SCHOOL_PRIMARY_NEARBY]
    was = {"label": core.label, "short_label": core.short_label}
    line = a_line(what="label", of="school_primary_nearby", was=was, now=now)
    assert rule_of(refused(tmp_path, capsys, line)) == (1, "name_is_plain")


@pytest.mark.parametrize(
    "line",
    [
        named("leafy", label="Tallowgate feel"),
        named("leafy", label="Like Quillhaven"),
        named("pace", low_end="As Pellam Cross Station"),
    ],
)
def test_a_name_that_holds_the_name_of_a_place_of_the_build_stops_the_build(
    tmp_path: Path, capsys: Printed, line: dict[str, Any]
):
    said = refused(tmp_path, capsys, line)
    assert "error: the release breaks a rule of the contract" in said
    assert "[names_name_no_place]" in said
    assert "Tallowgate" not in said and "Pellam" not in said


# 8. A brand


def row_of(key: str, **changed: Any) -> dict[str, Any]:
    return {**changes.row_of(brand_table.the_table().by_key[key]), **changed}


def a_chain(of: str, was: object, now: object) -> dict[str, Any]:
    return a_line(what="brand", of=of, was=was, now=now)


A_PERSON = {
    "name": "Ada Quillfeather",
    "kind": "coffee",
    "tier": "premium",
    "wikidata": [],
    "spellings": ["Ada Quillfeather"],
}


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        # A chain of the table is moved by its tier alone.
        (a_chain("lidl", row_of("lidl"), row_of("lidl", name="Ada Quillfeather")), "moved"),
        (a_chain("lidl", row_of("lidl"), row_of("lidl", kind="coffee")), "moved"),
        (a_chain("lidl", row_of("lidl"), row_of("lidl", spellings=["Lidl", "Ada"])), "moved"),
        (a_chain("lidl", row_of("lidl"), row_of("lidl", wikidata=[])), "moved"),
        # A chain that is added is named as the file of places writes it.
        (a_chain("ada", None, {**A_PERSON, "spellings": ["Gildcrest"]}), "named"),
        (a_chain("ada", None, {**A_PERSON, "spellings": []}), "named"),
        (
            a_chain("ada", None, {**A_PERSON, "name": "Students", "spellings": ["Students"]}),
            "plain",
        ),
    ],
)
def test_a_row_of_the_table_is_moved_by_its_tier_and_added_under_the_name_it_is_written_by(
    tmp_path: Path, capsys: Printed, line: dict[str, Any], rule: str
):
    rules = {
        "moved": "chain_moves_by_its_tier_alone",
        "named": "chain_is_named_as_it_is_written",
        "plain": "name_is_plain",
    }
    assert rule_of(refused(tmp_path, capsys, line)) == (1, rules[rule])


def test_a_chain_that_no_file_of_places_shows_to_be_one_is_not_added(
    tmp_path: Path, capsys: Printed
):
    # The made-up build holds no file of places with their brands. So nothing shows that
    # the name is of a chain, and not of a person or of one shop.
    said = refused(tmp_path, capsys, a_chain("ada", None, A_PERSON))
    assert rule_of(said) == (1, "chain_is_seen_to_be_one")
    assert "Quillfeather" not in said


# 9. Who made a change


@pytest.mark.parametrize(
    "by", ["founder", "Ada Quillfeather", "ada@example.org", "R1", "r0", "r100", "", " r1", "r1 "]
)
def test_a_line_names_its_reviewer_by_the_label_of_the_desk(
    tmp_path: Path, capsys: Printed, by: str
):
    said = refused(tmp_path, capsys, a_line(by=by))
    assert rule_of(said) == (1, "reviewer_is_a_label")
    assert "example.org" not in said and "Quillfeather" not in said


# 10. Whose the file is, and whether it is the copy that was published


@pytest.mark.parametrize("reviewer", ["r2", "r17"])
def test_a_file_of_another_reviewer_than_the_founder_is_never_built(
    tmp_path: Path, capsys: Printed, reviewer: str
):
    said = refused(tmp_path, capsys, a_line(by=reviewer), name=f"{reviewer}.jsonl")
    assert rule_of(said) == (1, "changes_are_the_founders")
    # Nor under the name of the founder's file.
    shutil.rmtree(tmp_path / "repository")
    said = refused(tmp_path, capsys, a_line(by=reviewer), name="r1.jsonl")
    assert rule_of(said) == (1, "changes_are_the_founders")


def test_the_founders_file_under_another_name_is_not_built(tmp_path: Path, capsys: Printed):
    said = refused(tmp_path, capsys, a_line(), name="r2.jsonl")
    assert "is named r1.jsonl" in said


NOT_PUBLISHED = (
    "error: the file of changes is not the copy that was published: a build takes the file "
    "as the repository holds it"
)


def stopped(found: Made, capsys: Printed, *arguments: str) -> str:
    assert found.run(*arguments) == 2
    said = capsys.readouterr()
    assert "Zzyzx" not in said.out + said.err
    assert not found.out.exists(), "nothing was written"
    return said.err


def test_a_file_that_is_in_no_repository_is_not_built(tmp_path: Path, capsys: Printed):
    found = made_once(tmp_path / "build")
    path = tmp_path / "by-hand" / "r1.jsonl"
    path.parent.mkdir()
    path.write_text(json.dumps(a_line()) + "\n", encoding="utf-8")
    assert stopped(found, capsys, "--changes", str(path)).startswith(NOT_PUBLISHED)


def test_a_file_outside_the_repository_of_the_build_is_not_built(tmp_path: Path, capsys: Printed):
    held = published(tmp_path, a_line())
    outside = tmp_path / "by-hand" / "r1.jsonl"
    outside.parent.mkdir()
    shutil.copy(held.path, outside)
    found = made_once(tmp_path / "build")
    said = stopped(
        found, capsys, "--changes", str(outside), "--root", str(held.root), "--commit", held.commit
    )
    assert said.startswith(NOT_PUBLISHED)


def test_a_file_the_repository_does_not_track_is_not_built(tmp_path: Path, capsys: Printed):
    held = published(tmp_path, a_line())
    beside = held.path.with_name("r1.jsonl").parent.parent / "by-hand" / "r1.jsonl"
    beside.parent.mkdir()
    shutil.copy(held.path, beside)
    found = made_once(tmp_path / "build")
    arguments = ("--changes", str(beside), "--root", str(held.root), "--commit", held.commit)
    assert stopped(found, capsys, *arguments).startswith(NOT_PUBLISHED)


def test_a_file_that_git_is_told_to_ignore_is_not_built(tmp_path: Path, capsys: Printed):
    held = published(tmp_path, a_line())
    (held.root / ".gitignore").write_text("data/\n", encoding="utf-8")
    git(held.root, "add", ".gitignore")
    git(held.root, "commit", "--quiet", "--message", "Ignore the data")
    ignored = held.root / "data" / "raw" / "desk" / "decisions" / "changes" / "r1.jsonl"
    ignored.parent.mkdir(parents=True)
    shutil.copy(held.path, ignored)
    commit = git(held.root, "rev-parse", "HEAD")
    found = made_once(tmp_path / "build")
    arguments = ("--changes", str(ignored), "--root", str(held.root), "--commit", commit)
    assert stopped(found, capsys, *arguments).startswith(NOT_PUBLISHED)


def a_byte_added(held: bytes) -> bytes:
    return held + b" "


def a_share_moved(held: bytes) -> bytes:
    moved = held.replace(b'"land_gardens": 20', b'"land_gardens": 21', 1)
    return moved.replace(b'"land_woodland": 50', b'"land_woodland": 49', 1)


def a_line_added(held: bytes) -> bytes:
    return held + held.replace(b'"n": 1', b'"n": 2', 1)


@pytest.mark.parametrize("change", [a_byte_added, a_share_moved, a_line_added])
def test_a_file_changed_by_a_byte_after_it_was_published_is_not_built(
    tmp_path: Path, capsys: Printed, change: Any
):
    held = published(tmp_path, a_line())
    before = held.path.read_bytes()
    held.path.write_bytes(change(before))
    assert held.path.read_bytes() != before
    found = made_once(tmp_path / "build")
    said = stopped(found, capsys, *held.arguments())
    # A byte that makes a line no line is refused as that. Any other is refused because the
    # file is no longer what the repository holds.
    if change is a_byte_added:
        assert rule_of(said)[1] == "line_is_a_line"
    else:
        assert said.startswith(NOT_PUBLISHED)


def test_a_file_that_is_staged_and_not_committed_is_not_built(tmp_path: Path, capsys: Printed):
    held = published(tmp_path, a_line())
    later = a_line(2, was=a_line()["now"], now=LEAFY)
    held.path.write_text(
        "".join(json.dumps(line) + "\n" for line in (a_line(), later)), encoding="utf-8"
    )
    git(held.root, "add", "--all")
    found = made_once(tmp_path / "build")
    said = stopped(found, capsys, *held.arguments())
    assert "what is staged is not what is committed" in said


def test_a_link_to_a_file_is_not_the_file(tmp_path: Path, capsys: Printed):
    held = published(tmp_path, a_line())
    link = held.path.with_name("linked.jsonl")
    link.symlink_to(held.path)
    git(held.root, "add", "--all")
    git(held.root, "commit", "--quiet", "--message", "Link to the file")
    commit = git(held.root, "rev-parse", "HEAD")
    found = made_once(tmp_path / "build")
    arguments = ("--changes", str(link), "--root", str(held.root), "--commit", commit)
    assert "error: the file of changes" in stopped(found, capsys, *arguments)


def test_the_copy_that_was_published_is_built_and_the_lock_names_it(tmp_path: Path):
    held = published(tmp_path, a_line())
    found = made_once(tmp_path / "build")
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run(*held.arguments()) == 0
    release = read_served(found.release)
    sha256 = hashlib.sha256(held.path.read_bytes()).hexdigest()
    assert release.manifest.changes_sha256 == sha256
    lock = json.loads((found.beside / LOCK).read_bytes())
    assert [one["sha256"] for one in lock["inputs"] if one["name"] == "changes/r1.jsonl"] == [
        sha256
    ]
    assert lock["commit"] == held.commit


# 11. What a release that was built with a file of changes is served with


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Made, Published]:
    folder = tmp_path_factory.mktemp("built")
    held = published(folder, a_line())
    found = made_once(folder / "build")
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert found.run(*held.arguments()) == 0
    return found, held


def copied(built: tuple[Made, Published], folder: Path) -> tuple[Path, Path]:
    """A copy of the release and of what stands beside it, for one test to write in."""
    found, _ = built
    release = Path(shutil.copytree(found.release, folder / RELEASE))
    beside = Path(shutil.copytree(found.beside, folder / f"{RELEASE}-build"))
    return release, beside


def checked(release: Path, capsys: Printed) -> tuple[int, str]:
    code = release_check.main(["check", str(release)])
    said = capsys.readouterr()
    return code, said.out + said.err


def rehashed(beside: Path, release: Path) -> None:
    """Write the hashes of the build again, as a hand would to hide what it changed."""
    hashes = json.loads((beside / HASHES).read_bytes())
    hashes["lock_sha256"] = hashlib.sha256((beside / LOCK).read_bytes()).hexdigest()
    hashes["evidence_sha256"] = hashlib.sha256((beside / EVIDENCE).read_bytes()).hexdigest()
    hashes["manifest_sha256"] = hashlib.sha256((release / "manifest.json").read_bytes()).hexdigest()
    (beside / HASHES).write_text(json.dumps(hashes), encoding="utf-8")


def test_the_release_is_served_as_it_was_built(
    built: tuple[Made, Published], tmp_path: Path, capsys: Printed
):
    release, _ = copied(built, tmp_path)
    code, said = checked(release, capsys)
    assert code == 0, said


def test_it_is_not_served_with_no_lock(
    built: tuple[Made, Published], tmp_path: Path, capsys: Printed
):
    release, beside = copied(built, tmp_path)
    (beside / LOCK).unlink()
    code, said = checked(release, capsys)
    assert code == 2 and "[real_release_has_its_build]" in said
    shutil.rmtree(beside)
    code, said = checked(release, capsys)
    assert code == 2 and "[real_release_has_its_build]" in said


def with_the_lock(beside: Path, change: Any) -> None:
    lock = json.loads((beside / LOCK).read_bytes())
    change(lock)
    (beside / LOCK).write_text(json.dumps(lock), encoding="utf-8")


def another_file(lock: dict[str, Any]) -> None:
    for one in lock["inputs"]:
        if one["name"].startswith("changes/"):
            one["sha256"] = hashlib.sha256(b"another file of changes\n").hexdigest()


def no_file(lock: dict[str, Any]) -> None:
    lock["inputs"] = [one for one in lock["inputs"] if not one["name"].startswith("changes/")]


@pytest.mark.parametrize("change", [another_file, no_file])
def test_it_is_not_served_with_a_lock_that_names_another_file_of_changes_or_none(
    built: tuple[Made, Published], tmp_path: Path, capsys: Printed, change: Any
):
    release, beside = copied(built, tmp_path)
    with_the_lock(beside, change)
    code, said = checked(release, capsys)
    assert code == 2 and "[build_is_as_it_was_written]" in said
    # The hashes of the build are written again by hand, to hide it.
    rehashed(beside, release)
    code, said = checked(release, capsys)
    assert code == 2 and "[changes_are_locked]" in said


def test_it_is_not_served_as_a_release_that_was_built_with_no_file(
    built: tuple[Made, Published], tmp_path: Path, capsys: Printed
):
    release, beside = copied(built, tmp_path)
    manifest = json.loads((release / "manifest.json").read_bytes())
    del manifest["changes_sha256"]
    (release / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with_the_lock(beside, no_file)
    rehashed(beside, release)
    code, said = checked(release, capsys)
    assert code == 2 and "[changes_are_named]" in said
