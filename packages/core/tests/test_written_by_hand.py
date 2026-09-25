"""A release that was written by hand is refused by core.

A file of changes can be written with no panel, and so can a release. So nothing the panel
refuses protects what is served. What protects it is what core refuses, when a release is
checked and when the service loads it. Each test here writes by hand what a change might
have made, and holds that core refuses it, by the file and the rule.

Every name here is made up. The areas, the boroughs and the places are those of the small
release of the tests, which describes no real place.
"""

import hashlib
import json
from collections.abc import Callable
from typing import Any

import pytest
from burro_core import catalogue
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    PLACED_ONLY_WITH,
    RANKED_AS,
    SHOWN_BESIDE_THE_MIX,
    TAGS,
    tag_raw,
)
from burro_core.ids import FeatureId, FeatureKind, TagId
from burro_core.release import (
    EVIDENCE,
    HASHES,
    LOCK,
    MANIFEST,
    ReleaseError,
    holds_the_name_of_a_place,
    open_served,
    parse_release,
    what_a_measure_breaks,
    what_a_vibe_breaks,
)

from .support import AREA_NAMES, BOROUGHS, PLACES, documents
from .test_adjusted import measure, shares, vibe, worked_out_again
from .test_release import as_real, packed

Documents = dict[str, Any]
CATALOGUE = "catalogue.json"
# The hash of a file of changes: any will do where the file is not read.
OF_A_FILE = hashlib.sha256(b"a made-up file of changes\n").hexdigest()
OF_ANOTHER = hashlib.sha256(b"another made-up file of changes\n").hexdigest()


def changed() -> Documents:
    """The small release, which says that it was built with a file of changes."""
    found = documents()
    found[MANIFEST]["changes_sha256"] = OF_A_FILE
    return found


def refused(found: Documents) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        parse_release(found)
    assert "Alderwick" not in str(caught.value), "a refusal names a file and a rule, and no value"
    return caught.value.file, caught.value.rule


# 1, 2 and 3. A recipe gains a part


def with_a_part(tag_id: str, part: str, reading: str = "high") -> Documents:
    """A recipe that holds one part more, with ten hundredths taken from its first."""
    found = changed()
    terms = vibe(found, tag_id)["terms"]
    terms[0]["hundredths"] -= 10
    terms.append({"feature_id": part, "hundredths": 10, "reading": reading})
    return found


def in_the_place_of_the_first(tag_id: str, part: str) -> Documents:
    found = changed()
    vibe(found, tag_id)["terms"][0]["feature_id"] = part
    return found


ON_REQUEST = sorted(f for f, held in FEATURES.items() if held.kind is FeatureKind.ON_REQUEST)[0]
# What core names as no feature at all: a table of the census that is shown on the page of
# an area, and the estimate of household income, which is shown beside a release.
NO_FEATURE = ("ethnic_group", "religion", "country_of_birth", "household_income", "no_such_part")
# What core names as a feature, and no recipe may read.
NOT_FOR_A_RECIPE = (
    *sorted(RANKED_AS),
    *sorted(SHOWN_BESIDE_THE_MIX)[:2],
    ON_REQUEST,
    FeatureId.CRIME_VIOLENCE_ROBBERY,
)


@pytest.mark.parametrize("part", NO_FEATURE)
def test_a_recipe_gains_no_part_that_is_no_feature_of_core(part: str):
    assert part not in FeatureId
    for found in (with_a_part("leafy", part), in_the_place_of_the_first("leafy", part)):
        file, rule = refused(found)
        assert (file, rule) == (CATALOGUE, "catalogue_matches_core")


@pytest.mark.parametrize("part", NOT_FOR_A_RECIPE, ids=lambda part: part.value)
def test_a_recipe_gains_no_part_that_is_shown_and_never_ranked_on_or_asked_for_by_name(
    part: FeatureId,
):
    for found in (with_a_part("leafy", part.value), in_the_place_of_the_first("leafy", part)):
        assert refused(found) == (CATALOGUE, "vibes_match_core")


@pytest.mark.parametrize("part", sorted(FeatureId), ids=lambda part: part.value)
def test_a_recipe_gains_no_part_at_all_whatever_the_part(part: FeatureId):
    held = TAGS[TagId.LEAFY]
    if part in {term.feature_id for term in held.terms}:
        return
    first, *rest = held.terms
    more = held.terms[-1].replace(feature_id=part, hundredths=10)
    gained = held.replace(terms=(first.replace(hundredths=first.hundredths - 10), *rest, more))
    assert what_a_vibe_breaks(gained) == "recipe_holds_cores_parts"


# 4 and 5. A part that counts who lived somewhere


@pytest.mark.parametrize("part", sorted(COUNTS_RESIDENTS), ids=lambda part: part.value)
def test_a_part_that_counts_residents_is_put_in_no_scale_and_in_no_other_vibe(part: FeatureId):
    # Going out is a scale between two ends. Leafy is of one way, and holds no such part.
    for tag_id in ("pace", "leafy"):
        assert refused(with_a_part(tag_id, part.value)) == (CATALOGUE, "vibes_match_core")
        assert refused(in_the_place_of_the_first(tag_id, part.value))[1] == "vibes_match_core"


@pytest.mark.parametrize("tag_id", ["family_area", "young_professionals"])
def test_a_part_that_counts_residents_is_read_from_its_low_end_by_no_release(tag_id: str):
    found = changed()
    counted = vibe(found, tag_id)["terms"][0]
    assert FeatureId(counted["feature_id"]) in COUNTS_RESIDENTS
    counted["reading"] = "low"
    assert refused(found) == (CATALOGUE, "vibes_match_core")


@pytest.mark.parametrize(
    ("tag_id", "hundredths"),
    [
        # The part that counts residents holds more than 40.
        ("family_area", (41, 25, 19, 15)),
        ("family_area", (59, 20, 11, 10)),
        ("young_professionals", (45, 25, 15, 15)),
        # A part beside it holds more than 40.
        ("family_area", (30, 41, 15, 14)),
    ],
)
def test_no_part_holds_more_than_its_limit_where_residents_are_counted(
    tag_id: str, hundredths: tuple[int, ...]
):
    found = changed()
    shares(found, tag_id, *hundredths)
    assert refused(found) == (CATALOGUE, "vibes_match_core")
    assert what_a_vibe_breaks(TAGS[TagId(tag_id)]) is None


# 6. A vibe that is held off


def without_figures(found: Documents, *parts: str) -> None:
    """Take every figure of some measures out of a release: no area has one."""
    for row in found["features.json"]["rows"]:
        if row["feature_id"] in parts:
            row.update(value=None, percentile=None, coverage=0.0)
    for tag_id in [one["tag_id"] for one in found["catalogue.json"]["vibes"]]:
        worked_out_again(found, tag_id)


def placed(found: Documents, tag_id: str) -> int:
    rows = [row for row in found["tags.json"]["rows"] if row["tag_id"] == tag_id]
    return sum(row["raw"] is not None for row in rows)


@pytest.fixture
def leafy_is_held_off(monkeypatch: pytest.MonkeyPatch) -> frozenset[FeatureId]:
    """For a while, Leafy places an area only where woodland has a figure.

    No vibe is held off today. Village feel was, until the founder chose on 2026-09-25 to
    serve it on another recipe, as a rough guide. What holding a vibe off does is kept, for
    any vibe that is held off in future, and these tests hold it on a vibe that is not.
    """
    assert dict(PLACED_ONLY_WITH) == {}
    needed = frozenset({FeatureId.LAND_WOODLAND})
    monkeypatch.setattr(catalogue, "PLACED_ONLY_WITH", {TagId.LEAFY: needed})
    return needed


def test_a_vibe_that_is_held_off_places_no_area_without_its_part_whatever_its_shares(
    leafy_is_held_off: frozenset[FeatureId],
):
    held = TAGS[TagId.LEAFY]
    others = {
        term.feature_id: 80.0 for term in held.terms if term.feature_id not in leafy_is_held_off
    }
    for hundredths in ((40, 30, 30), (58, 1, 41), (41, 1, 58)):
        recipe = tuple(
            term.replace(hundredths=share)
            for term, share in zip(held.terms, hundredths, strict=True)
        )
        assert what_a_vibe_breaks(held.replace(terms=recipe)) is None
        found = tag_raw(TagId.LEAFY, others, recipe)
        assert found.raw is None, "no area is placed, though most of the recipe is there"
        assert found.coverage >= 0.6
    assert tag_raw(TagId.LEAFY, {**others, FeatureId.LAND_WOODLAND: 50.0}).raw is not None


def test_a_release_that_places_a_vibe_that_is_held_off_without_its_part_is_refused(
    leafy_is_held_off: frozenset[FeatureId],
):
    found = changed()
    without_figures(found, *leafy_is_held_off)
    assert placed(found, "leafy") == 0
    assert parse_release(found).placed(TagId.LEAFY) is False
    # The shares are moved to the parts that are there, and the rows are written by hand.
    shares(found, "leafy", 58, 1, 41)
    assert placed(found, "leafy") == 0, "core places no area, whatever the shares"
    for row in found["tags.json"]["rows"]:
        if row["tag_id"] == "leafy":
            row.update(raw=0.5, score=50.0, band=3, spread_low=3, spread_high=3)
    assert refused(found)[0] == "tags.json"


def test_a_vibe_that_core_places_no_area_on_is_placed_by_no_change_to_its_shares():
    found = changed()
    # Two parts of Going out have no figure, so 35 in 100 of its recipe is there.
    without_figures(found, "venue_evening_per_homes", "venue_food_drink_per_homes")
    assert placed(found, "pace") == 0
    assert parse_release(found).placed(TagId.PACE) is False
    # By hand, the shares are moved to the two parts that are there.
    shares(found, "pace", 1, 1, 58, 40)
    assert placed(found, "pace") > 0, "the rows are what the shares give"
    assert refused(found) == (CATALOGUE, "held_off_stays_held_off")


def test_a_vibe_that_core_places_may_have_its_shares_moved():
    found = changed()
    without_figures(found, "venue_evening_per_homes")
    before = placed(found, "pace")
    assert before > 0
    shares(found, "pace", 20, 35, 25, 20)
    # An area may gain a band or lose one: more of the recipe it has a figure for, or less.
    assert placed(found, "pace") >= before
    assert parse_release(found).placed(TagId.PACE)


# 7. A name or a label


NAMES_OF_PLACES = (*AREA_NAMES, *BOROUGHS, *(name for name, _, _ in PLACES))


@pytest.mark.parametrize(
    ("words", "holds"),
    [
        ("Alderwick feel", True),
        ("Like Dulcimer Green", True),
        ("like dulcimer   green", True),
        ("The best of Quillhaven", True),
        ("Near Pellam Cross", True),
        ("Foxholt Works and the like", True),
        # A part of a word is no name, and a name is no part of a word.
        ("Alderwickian", False),
        ("Dulcimer", False),
        ("Green and leafy", False),
        ("Street character", False),
        ("Nights out", False),
    ],
)
def test_a_name_of_a_place_is_found_in_words_as_a_whole_name(words: str, holds: bool):
    assert holds_the_name_of_a_place(words, NAMES_OF_PLACES) is holds


def test_a_word_that_core_itself_says_is_no_name_of_a_place():
    # An area may bear the name of a thing: a park, a station, a village. Core says each
    # word in a label of its own, so each is a word and not a name.
    for word in ("Park", "Station", "Village"):
        assert holds_the_name_of_a_place(f"Near the {word.lower()}", [word]) is False
    assert holds_the_name_of_a_place("Near the park", ["Thrushcombe Park"]) is False
    assert holds_the_name_of_a_place("Near Thrushcombe Park", ["Thrushcombe Park"]) is True


def test_an_area_that_is_named_with_a_part_of_the_compass_is_found_by_its_name_alone():
    names = ["Alderwick, north", "Alderwick, south-east"]
    assert holds_the_name_of_a_place("Alderwick feel", names) is True
    assert holds_the_name_of_a_place("North facing", names) is False


NAMED_BY_HAND: list[tuple[str, Callable[[Documents], dict[str, Any]], dict[str, Any]]] = [
    ("the name of a vibe", lambda f: vibe(f, "leafy"), {"label": "Alderwick feel"}),
    ("an end of a scale", lambda f: vibe(f, "pace"), {"high_end": "Like Cindermoor"}),
    ("the label of a measure", lambda f: measure(f, "homes_density"), {"label": "As Eskerfold"}),
    ("its short label", lambda f: measure(f, "homes_density"), {"short_label": "Ostrel Vale"}),
]


@pytest.mark.parametrize(("what", "of", "given"), NAMED_BY_HAND, ids=[n[0] for n in NAMED_BY_HAND])
def test_a_name_a_person_gave_holds_no_name_of_a_place_of_the_release(
    what: str, of: Callable[[Documents], dict[str, Any]], given: dict[str, Any]
):
    found = changed()
    held = of(found)
    held.update(given)
    if "tag_id" in held and "label" in given:
        # A vibe has one name, which is its label and its short label alike.
        held["short_label"] = given["label"]
    assert refused(found) == (CATALOGUE, "names_name_no_place"), what


def test_a_line_of_what_a_vibe_cannot_see_holds_no_name_of_a_place():
    found = changed()
    vibe(found, "leafy")["cannot_see"].append("Whether Gorsebeck has trees.")
    assert refused(found) == (CATALOGUE, "names_name_no_place")


def test_the_names_core_gives_are_held_to_no_list_of_places():
    # The small release has an area named for a word core's own label says.
    found = changed()
    found["neighbourhoods.json"]["neighbourhoods"][0]["name"] = "Leafy"
    assert parse_release(found).neighbourhoods[0].name == "Leafy"


@pytest.mark.parametrize(
    ("feature_id", "given"),
    [
        # The label of core says the distance it counts within. No other may be said.
        ("school_primary_nearby", {"label": "State primary schools within 500 m of home"}),
        ("school_primary_nearby", {"label": "State primary schools within 1,800 m of home"}),
        ("school_primary_nearby", {"label": "The 3 nearest state primary schools"}),
        ("school_primary_nearby", {"short_label": "Schools within 800 m"}),
        ("homes_density", {"label": "Homes per hectare, of 40 or more"}),
        ("homes_density", {"label": "Homes per hectare\N{SUPERSCRIPT TWO}"}),
        ("homes_density", {"label": "Homes per hectare, \N{ARABIC-INDIC DIGIT THREE}"}),
    ],
)
def test_a_label_a_person_gave_holds_no_figure_that_the_label_of_core_does_not(
    feature_id: str, given: dict[str, str]
):
    carried = {metric.feature_id: metric for metric in parse_release(documents()).metrics}
    made = carried[FeatureId(feature_id)].replace(**given)
    assert what_a_measure_breaks(made) == "name_is_plain"
    found = changed()
    measure(found, feature_id).update(given)
    assert refused(found) == (CATALOGUE, "catalogue_matches_core")


def test_a_label_may_say_again_the_figure_the_label_of_core_says():
    found = changed()
    core = FEATURES[FeatureId.SCHOOL_PRIMARY_NEARBY]
    assert "800" in core.label
    measure(found, "school_primary_nearby").update(
        label="State primary schools no further than 800 m from home, in a straight line"
    )
    held = parse_release(found).metrics
    assert "no further than 800 m" in next(
        one.label for one in held if one.feature_id is FeatureId.SCHOOL_PRIMARY_NEARBY
    )


@pytest.mark.parametrize(
    "line", ["Trees under 5 m.", "Whether 3 in 4 streets have trees.", "Gardens of 2021."]
)
def test_a_line_of_what_a_vibe_cannot_see_holds_no_figure_a_person_gave(line: str):
    found = changed()
    # The line core says of Leafy holds a figure, and stands.
    assert any(each.isdigit() for one in TAGS[TagId.LEAFY].cannot_see for each in one)
    assert parse_release(found).placed(TagId.LEAFY)
    vibe(found, "leafy")["cannot_see"].append(line)
    assert refused(found) == (CATALOGUE, "vibes_match_core")


# 11. What a release that carries a change is served with


def lock_of(*inputs: dict[str, Any]) -> bytes:
    return (json.dumps({"inputs": list(inputs)}) + "\n").encode()


def a_file_of_changes(sha256: str = OF_A_FILE, name: str = "changes/r1.jsonl") -> dict[str, Any]:
    return {"name": name, "kind": "gazetteer", "sha256": sha256, "bytes": 560}


A_PUBLISHERS_FILE = {"name": "f-0123456789ab", "kind": "publisher_file", "sha256": OF_ANOTHER}


def beside(files: dict[str, bytes], lock: bytes) -> dict[str, bytes]:
    """What stands beside a release: its evidence, its lock, and the hashes of the build."""
    evidence = b'{"rows":[]}\n'
    hashes = {
        "release_id": json.loads(files[MANIFEST])["release_id"],
        "manifest_sha256": hashlib.sha256(files[MANIFEST]).hexdigest(),
        "evidence_sha256": hashlib.sha256(evidence).hexdigest(),
        "lock_sha256": hashlib.sha256(lock).hexdigest(),
    }
    return {EVIDENCE: evidence, LOCK: lock, HASHES: json.dumps(hashes).encode()}


def not_served(found: Documents, lock: bytes | None) -> tuple[str, str]:
    folder, files = packed(found)
    with pytest.raises(ReleaseError) as caught:
        open_served(folder, files, None if lock is None else beside(files, lock))
    return caught.value.file, caught.value.rule


def with_other_shares(found: Documents) -> Documents:
    shares(found, "leafy", 50, 25, 25)
    return found


def renamed(found: Documents) -> Documents:
    vibe(found, "leafy").update(label="Green and leafy", short_label="Green and leafy")
    return found


def relabelled(found: Documents) -> Documents:
    measure(found, "homes_density").update(short_label="How built up")
    return found


def says_otherwise_what_it_cannot_see(found: Documents) -> Documents:
    vibe(found, "leafy")["cannot_see"].append("Whether a garden is kept.")
    return found


BY_A_CHANGE = [with_other_shares, renamed, relabelled, says_otherwise_what_it_cannot_see]


@pytest.mark.parametrize("made", BY_A_CHANGE, ids=lambda made: made.__name__)
def test_a_release_that_carries_what_is_not_cores_says_which_file_of_changes_made_it_so(
    made: Callable[[Documents], Documents],
):
    assert refused(made(documents())) == (MANIFEST, "changes_are_named")
    assert parse_release(made(changed())).manifest.changes_sha256 == OF_A_FILE


@pytest.mark.parametrize("made", BY_A_CHANGE, ids=lambda made: made.__name__)
@pytest.mark.parametrize("real", [False, True], ids=["made up", "real"])
def test_a_release_that_carries_a_change_is_served_only_beside_its_lock(
    made: Callable[[Documents], Documents], real: bool
):
    found = made(changed())
    if real:
        found = as_real(found)
    needs = (HASHES, "real_release_has_its_build") if real else (LOCK, "changes_are_locked")
    assert not_served(found, None) == needs
    folder, files = packed(found)
    served = open_served(folder, files, beside(files, lock_of(a_file_of_changes())))
    assert served.manifest.changes_sha256 == OF_A_FILE


@pytest.mark.parametrize(
    "lock",
    [
        # It names no file of changes.
        lock_of(),
        lock_of(A_PUBLISHERS_FILE),
        # It names another file of changes than the release was built with.
        lock_of(a_file_of_changes(OF_ANOTHER)),
        # It names two.
        lock_of(a_file_of_changes(), a_file_of_changes(OF_ANOTHER, "changes/r2.jsonl")),
        lock_of(a_file_of_changes(), a_file_of_changes()),
        # It is no lock.
        b"{not json, Alderwick",
        b'["changes/r1.jsonl"]',
        b'{"inputs": {"changes/r1.jsonl": 1}}',
        b'{"inputs": [["changes/r1.jsonl"]]}',
        (json.dumps({"inputs": [{"name": "changes/r1.jsonl", "sha256": 7}]})).encode(),
    ],
)
def test_a_lock_that_names_another_file_of_changes_or_none_is_refused(lock: bytes):
    file, rule = not_served(with_other_shares(changed()), lock)
    assert (file, rule) == (LOCK, "changes_are_locked")


def test_a_release_built_with_a_file_that_changed_nothing_of_the_catalogue_names_it_too():
    # A flag, a chain that was moved, and a change that was taken back change no recipe.
    found = changed()
    assert not_served(found, lock_of()) == (LOCK, "changes_are_locked")
    folder, files = packed(found)
    assert open_served(folder, files, beside(files, lock_of(a_file_of_changes())))


def test_a_lock_names_no_file_of_changes_that_the_release_does_not():
    folder, files = packed(as_real(documents()))
    with pytest.raises(ReleaseError) as caught:
        open_served(folder, files, beside(files, lock_of(a_file_of_changes())))
    assert (caught.value.file, caught.value.rule) == (LOCK, "changes_are_locked")


def test_a_release_with_no_change_is_served_as_it_was():
    folder, files = packed(documents())
    served = open_served(folder, files, None)
    assert served.manifest.changes_sha256 is None
    real, of_london = packed(as_real(documents()))
    assert open_served(real, of_london, beside(of_london, lock_of(A_PUBLISHERS_FILE)))
    # A manifest says nothing of a file of changes where the release was built with none,
    # so that such a release is byte for byte what it was.
    assert "changes_sha256" not in served.manifest.as_written()
    named = served.manifest.replace(changes_sha256=OF_A_FILE)
    assert named.as_written() == served.manifest.as_written() | {"changes_sha256": OF_A_FILE}


@pytest.mark.parametrize("held", ["", "abc", "0" * 63, "G" * 64, 7, ["0" * 64]])
def test_the_hash_of_a_file_of_changes_is_a_hash(held: object):
    found = documents()
    found[MANIFEST]["changes_sha256"] = held
    assert refused(found)[0] == MANIFEST
