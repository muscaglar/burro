"""A release that was built under another catalogue, read by its own.

A release says what it measures and how each vibe is made, in its own catalogue, so
that it can be read alone. `open_built` reads it so, to be held against another build.
What is served is read by `open_served`, which holds a release to the catalogue as core
holds it today: nothing here loosens that.

Every release here is the small made-up one. It is made older by hand: another version,
a vibe fewer, a measure fewer, a recipe of other parts and other shares, a label that
was another, and no word of how sure a vibe is, which a release did not say then.
"""

from typing import Any

import pytest
from burro_core.catalogue import CATALOGUE_VERSION, TAGS
from burro_core.ids import FeatureId, Sureness, TagId
from burro_core.release import (
    EVIDENCE,
    HASHES,
    LOCK,
    MANIFEST,
    OF_CORES_CATALOGUE,
    RULES,
    RULES_OF_ITS_OWN,
    ReleaseError,
    open_built,
    open_served,
    versions_are_its_own,
)

from .support import documents
from .test_release import BROKEN, Break, as_real, built_beside, packed, rows, set_in, vibe

Documents = dict[str, Any]
OLDER = CATALOGUE_VERSION - 1
# What the older catalogue did not hold: a vibe, and a measure that stands in no recipe.
NOT_YET_A_VIBE, NOT_YET_A_MEASURE = "well_connected", "water_access"
# A label of the older catalogue, which core has worded otherwise since.
WAS_LABELLED = "Nitrogen dioxide in the air, as it was labelled"


def older(found: Documents | None = None) -> Documents:
    """The small release as a build under an older catalogue would have written it."""
    found = documents() if found is None else found
    found["manifest.json"]["catalogue_version"] = OLDER
    catalogue = found["catalogue.json"]
    catalogue["catalogue_version"] = OLDER
    catalogue["vibes"] = [one for one in catalogue["vibes"] if one["tag_id"] != NOT_YET_A_VIBE]
    catalogue["metrics"] = [
        one for one in catalogue["metrics"] if one["feature_id"] != NOT_YET_A_MEASURE
    ]
    found["tags.json"]["rows"] = [
        row for row in found["tags.json"]["rows"] if row["tag_id"] != NOT_YET_A_VIBE
    ]
    found["features.json"]["rows"] = [
        row for row in found["features.json"]["rows"] if row["feature_id"] != NOT_YET_A_MEASURE
    ]
    for one in catalogue["vibes"]:
        # A release of then said nothing of how sure a vibe is.
        del one["sureness"]
    # The recipe of a vibe held another part, at other shares, and the vibe said otherwise
    # what it means.
    village = vibe(found, "village_feel")
    village["terms"] = [
        {"feature_id": "homes_density", "hundredths": 40, "reading": "low"},
        {"feature_id": "homes_pre1919", "hundredths": 35, "reading": "high"},
        {"feature_id": "green_cover", "hundredths": 25, "reading": "high"},
    ]
    village.update(meaning="What it was said to mean then", strip=True)
    next(one for one in catalogue["metrics"] if one["feature_id"] == "air_no2").update(
        label=WAS_LABELLED
    )
    return found


def read(found: Documents) -> Any:
    folder, files = packed(found)
    return open_built(folder, files, None)


def refused_for(found: Documents, beside: dict[str, bytes] | None = None) -> tuple[str, str]:
    folder, files = packed(found)
    with pytest.raises(ReleaseError) as caught:
        open_built(folder, files, beside)
    return caught.value.file, caught.value.rule


def test_a_release_of_another_catalogue_is_not_served():
    folder, files = packed(older())
    with pytest.raises(ReleaseError) as caught:
        open_served(folder, files, None)
    assert (caught.value.file, caught.value.rule) == (MANIFEST, "versions_match")


def test_it_is_read_by_its_own_catalogue_to_be_held_against_another_build():
    release = read(older())
    assert release.manifest.catalogue_version == OLDER != CATALOGUE_VERSION
    carried = {one.tag_id for one in release.vibes}
    assert (
        TagId(NOT_YET_A_VIBE) not in carried
        and len(carried) == len(documents()["catalogue.json"]["vibes"]) - 1
    )
    assert FeatureId(NOT_YET_A_MEASURE) not in {one.feature_id for one in release.metrics}
    assert release.feature("syn-n0001", FeatureId(NOT_YET_A_MEASURE)) is None
    # The recipe, the meaning and the label are the release's own, and not core's.
    (village,) = [one for one in release.vibes if one.tag_id is TagId.VILLAGE_FEEL]
    assert [(term.feature_id.value, term.hundredths) for term in village.terms] == [
        ("homes_density", 40),
        ("homes_pre1919", 35),
        ("green_cover", 25),
    ]
    assert village.terms != TAGS[TagId.VILLAGE_FEEL].terms
    assert (village.meaning, village.strip) == ("What it was said to mean then", True)
    (air,) = [one for one in release.metrics if one.feature_id is FeatureId.AIR_NO2]
    assert air.label == WAS_LABELLED
    # What a release did not say then is read as it was meant then: as sure as the rest.
    assert {one.sureness for one in release.vibes} == {Sureness.AS_THE_REST}
    assert TAGS[TagId.VILLAGE_FEEL].sureness is Sureness.ROUGH_GUIDE


def test_a_release_of_todays_catalogue_is_read_as_it_is_served():
    folder, files = packed(documents())
    assert open_built(folder, files, None) == open_served(folder, files, None)


def test_every_rule_is_held_or_is_said_to_be_of_cores_catalogue():
    """No rule is passed over without a word: a rule that is added is held, until it is
    named as one that holds a release to the catalogue of today."""
    assert set(RULES_OF_ITS_OWN) == (set(RULES) - set(OF_CORES_CATALOGUE)) | {versions_are_its_own}
    assert set(OF_CORES_CATALOGUE) < set(RULES) and versions_are_its_own not in RULES
    assert [rule.__name__ for rule in OF_CORES_CATALOGUE] == [
        "versions_match",
        "catalogue_matches_core",
        "vibes_match_core",
        "names_name_no_place",
        "held_off_stays_held_off",
        "changes_are_named",
        "raw_matches_recipe",
    ]
    # What is held is held in the order it always was.
    kept = [rule for rule in RULES if rule not in OF_CORES_CATALOGUE]
    assert list(RULES_OF_ITS_OWN) == [versions_are_its_own, *kept]


OF_ITSELF = [
    (rule, file, break_it)
    for rule, file, break_it in BROKEN
    if rule not in {one.__name__ for one in OF_CORES_CATALOGUE}
]


@pytest.mark.parametrize(
    ("rule", "file", "break_it"),
    OF_ITSELF,
    ids=[f"{rule}-{file}-{n}" for n, (rule, file, _) in enumerate(OF_ITSELF)],
)
def test_a_release_that_does_not_hold_together_is_refused_whatever_its_catalogue(
    rule: str, file: str, break_it: Break
):
    """Read by its own catalogue, a release is still held to itself: its ids, its rows,
    its ranges, its sources, and every percentile, score and band to its own figures."""
    assert len(OF_ITSELF) > 100
    broken = documents()
    break_it(broken)
    folder, files = packed(broken)
    with pytest.raises(ReleaseError) as caught:
        open_built(folder, files, None)
    assert (caught.value.file, caught.value.rule) == (file, rule)


@pytest.mark.parametrize(
    ("break_it", "where"),
    [
        (set_in("manifest.json", None, schema_version=1), (MANIFEST, "schema_version")),
        (set_in("manifest.json", None, schema_version=3), (MANIFEST, "schema_version")),
        (set_in("catalogue.json", None, catalogue_version=OLDER - 1), ("catalogue.json", "")),
        (set_in("manifest.json", None, catalogue_version=OLDER + 5), ("catalogue.json", "")),
    ],
)
def test_a_release_says_one_version_of_its_catalogue_in_a_schema_that_is_read(
    break_it: Break, where: tuple[str, str]
):
    found = older()
    break_it(found)
    folder, files = packed(found)
    with pytest.raises(ReleaseError) as caught:
        open_built(folder, files, None)
    assert (caught.value.file, caught.value.rule) == (where[0], "versions_are_its_own")
    assert caught.value.row == (where[1] or "catalogue_version")


# A measure and a vibe that the code holds no id for, and a field it does not know.
NOT_KNOWN_TO_THE_CODE: list[Break] = [
    lambda found: rows(found, "catalogue.json")[0].update(feature_id="a_measure_to_come"),
    lambda found: vibe(found, "leafy").update(tag_id="a_vibe_to_come"),
    lambda found: vibe(found, "leafy").update(said_since="what a later catalogue says"),
    lambda found: rows(found, "catalogue.json")[0].update(reach_m=800),
]


@pytest.mark.parametrize("break_it", NOT_KNOWN_TO_THE_CODE)
def test_a_release_the_code_cannot_read_at_all_is_refused_and_says_where(break_it: Break):
    """A release of a catalogue that is newer than the code holds what the code has no
    record for. It is not read in part: what is compared is the whole of each build."""
    found = older()
    break_it(found)
    file, rule = refused_for(found)
    assert file == "catalogue.json" and rule in ("catalogue_matches_core", "shape_is_valid")


def test_a_refusal_names_the_file_the_row_and_the_rule_and_never_a_value():
    found = older()
    rows(found, "neighbourhoods.json")[0].update(name="Canary Wharfside", slug="alderwick-2")
    rows(found, "features.json")[0].update(percentile=100.5)
    folder, files = packed(found)
    with pytest.raises(ReleaseError) as caught:
        open_built(folder, files, None)
    assert "Canary" not in str(caught.value) and "100.5" not in str(caught.value)


# It is held to what it was built with, as what is served is


def of_london() -> Documents:
    return older(as_real(documents()))


def test_a_release_that_is_not_made_up_is_read_with_its_build_beside_it():
    folder, files = packed(of_london())
    release = open_built(folder, files, built_beside(files))
    assert (release.manifest.synthetic, release.manifest.catalogue_version) == (False, OLDER)


@pytest.mark.parametrize("missing", [HASHES, EVIDENCE, LOCK])
def test_with_a_file_of_its_build_missing_it_is_not_read(missing: str):
    folder, files = packed(of_london())
    beside = {name: held for name, held in built_beside(files).items() if name != missing}
    assert refused_for(of_london(), beside) == (missing, "real_release_has_its_build")
    assert refused_for(of_london(), None) == (HASHES, "real_release_has_its_build")
    assert folder.startswith("lon-")


@pytest.mark.parametrize("changed", [MANIFEST, EVIDENCE, LOCK])
def test_changed_since_it_was_built_it_is_not_read(changed: str):
    folder, files = packed(of_london())
    beside = built_beside(files)
    if changed == MANIFEST:
        files[MANIFEST] += b" "
    else:
        beside[changed] += b" "
    with pytest.raises(ReleaseError) as caught:
        open_built(folder, files, beside)
    assert (caught.value.file, caught.value.rule) == (changed, "build_is_as_it_was_written")


def test_a_file_of_it_that_was_changed_is_refused_by_its_manifest():
    folder, files = packed(of_london())
    beside = built_beside(files)
    files["tags.json"] = files["tags.json"].replace(b'"band":1', b'"band":2', 1)
    with pytest.raises(ReleaseError) as caught:
        open_built(folder, files, beside)
    assert (caught.value.file, caught.value.rule) == ("tags.json", "files_match_manifest")
