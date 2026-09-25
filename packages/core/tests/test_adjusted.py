"""What a release may carry that is not core's own: the shares of a recipe, and a name.

A person adjusts the shares of a recipe and renames a vibe or a measure at the panel, and
a build carries what they decided (ADR 0029). Core is still the only judge of a release:
it holds what a release carries to every rule that core's own recipes are held to, and
lets nothing else of a vibe or a measure differ. Every name here is made up.
"""

from collections.abc import Callable
from typing import Any

import pytest
from burro_core.catalogue import (
    COMMON_CANNOT_SEE,
    FEATURES,
    TAGS,
    band_of,
    percentile_of,
    tag_raw,
)
from burro_core.facts import facts_for
from burro_core.ids import FactKind, FeatureId, Provenance, TagId, Tenure, Toward
from burro_core.rank import rank
from burro_core.release import (
    ReleaseError,
    name_is_plain,
    parse_release,
    what_a_measure_breaks,
    what_a_vibe_breaks,
)
from burro_core.spec import TagWeight, default_spec

from . import support
from .support import area_id

Documents = dict[str, Any]
# The hash of a file of changes: any will do, because core reads no such file.
OF_A_FILE = "5" * 64


def documents() -> Documents:
    """The small release, which says that it was built with a file of changes: a release
    that carries what is not core's is refused unless it says so."""
    found = support.documents()
    found["manifest.json"]["changes_sha256"] = OF_A_FILE
    return found


def vibe(found: Documents, tag_id: str) -> dict[str, Any]:
    return next(v for v in found["catalogue.json"]["vibes"] if v["tag_id"] == tag_id)


def measure(found: Documents, feature_id: str) -> dict[str, Any]:
    return next(m for m in found["catalogue.json"]["metrics"] if m["feature_id"] == feature_id)


def worked_out_again(found: Documents, tag_id: str) -> None:
    """Work the rows of a vibe out again, from the recipe the release now carries."""
    held = TAGS[TagId(tag_id)].model_validate(vibe(found, tag_id))
    areas = found["neighbourhoods.json"]["neighbourhoods"]
    rankable = [area["rankable"] for area in areas]
    percentiles = {
        (row["area_id"], FeatureId(row["feature_id"])): row["percentile"]
        for row in found["features.json"]["rows"]
    }
    raws = [
        tag_raw(
            held.tag_id,
            {t.feature_id: percentiles.get((area["area_id"], t.feature_id)) for t in held.terms},
            held.terms,
        )
        for area in areas
    ]
    scores = percentile_of([raw.raw for raw in raws], rankable)
    bands = band_of([raw.raw for raw in raws], rankable)
    rows = {row["area_id"]: row for row in found["tags.json"]["rows"] if row["tag_id"] == tag_id}
    for area, raw, score, band in zip(areas, raws, scores, bands, strict=True):
        rows[area["area_id"]].update(
            raw=raw.raw,
            score=score,
            coverage=raw.coverage,
            band=band,
            spread_low=band,
            spread_high=band,
        )


def shares(found: Documents, tag_id: str, *hundredths: int) -> None:
    terms = vibe(found, tag_id)["terms"]
    assert len(terms) == len(hundredths)
    for term, share in zip(terms, hundredths, strict=True):
        term["hundredths"] = share
    worked_out_again(found, tag_id)


def refused(found: Documents) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        parse_release(found)
    return caught.value.file, caught.value.rule


# The shares of a recipe


def test_a_band_is_worked_out_with_the_recipe_it_is_handed():
    leafy = TAGS[TagId.LEAFY]
    figures = {
        FeatureId.LAND_GARDENS: 90.0,
        FeatureId.LAND_WOODLAND: 10.0,
        FeatureId.GREEN_COVER: 10.0,
    }
    assert tag_raw(TagId.LEAFY, figures).raw == 0.42
    assert tag_raw(TagId.LEAFY, figures, leafy.terms).raw == 0.42
    more = tuple(
        term.replace(hundredths=share)
        for term, share in zip(leafy.terms, (50, 25, 25), strict=True)
    )
    assert tag_raw(TagId.LEAFY, figures, more).raw == 0.5
    # How much of a recipe is there is counted in the shares it is handed.
    assert tag_raw(TagId.LEAFY, {FeatureId.LAND_GARDENS: 90.0}, more).coverage == 0.5


def test_a_release_may_carry_shares_that_are_not_cores_and_every_band_is_worked_out_with_them():
    found = documents()
    before = {(r["area_id"], r["tag_id"]): r["score"] for r in found["tags.json"]["rows"]}
    shares(found, "leafy", 50, 25, 25)
    release = parse_release(found)
    held = next(one for one in release.vibes if one.tag_id is TagId.LEAFY)
    assert [term.hundredths for term in held.terms] == [50, 25, 25]
    after = {(row.area_id, row.tag_id): row.score for row in release.tags}
    moved = {key for key in before if before[key] != after[key]}
    assert moved and {tag_id for _, tag_id in moved} == {"leafy"}
    # Ranking is still a function of a search and a release: it reads the score it is given.
    wish = TagWeight(
        tag_id=TagId.LEAFY, weight=1.0, toward=Toward.HIGH, provenance=Provenance.STATED
    )
    spec = default_spec(Tenure.BUY).replace(weights=(), tags=(wish,))
    scores = [
        row.score
        for area in rank(spec, release).ranked
        if (row := release.tag(area.area_id, TagId.LEAFY)) is not None
    ]
    assert len(scores) > 3 and scores == sorted(scores, key=lambda score: -(score or 0))


def test_a_band_worked_out_with_another_recipe_than_the_release_carries_is_refused():
    found = documents()
    terms = vibe(found, "leafy")["terms"]
    terms[0]["hundredths"], terms[1]["hundredths"] = 50, 20
    assert refused(found) == ("tags.json", "raw_matches_recipe")


def test_the_fact_of_a_vibe_says_the_shares_the_release_carries():
    found = documents()
    shares(found, "leafy", 50, 25, 25)
    release = parse_release(found)
    facts = {fact.fact_id: fact for fact in facts_for(release, area_id(1), None)}
    leafy = facts[f"{area_id(1)}/{FactKind.TAG}/leafy"]
    assert leafy.slots["share"] == "100"


def a_part_added(found: Documents) -> None:
    terms = vibe(found, "leafy")["terms"]
    terms[0]["hundredths"] -= 10
    terms.append({"feature_id": "park_proximity", "hundredths": 10, "reading": "low"})


def a_part_taken_out(found: Documents) -> None:
    terms = vibe(found, "leafy")["terms"]
    gone = terms.pop()
    terms[0]["hundredths"] += gone["hundredths"]


def a_part_turned_round(found: Documents) -> None:
    vibe(found, "leafy")["terms"][0]["reading"] = "low"


def a_part_in_the_place_of_another(found: Documents) -> None:
    vibe(found, "leafy")["terms"][0]["feature_id"] = "park_proximity"


def who_lived_there_read_from_the_low_end(found: Documents) -> None:
    # To read it low is to rank towards fewer of a group of people.
    vibe(found, "family_area")["terms"][0]["reading"] = "low"


def in_another_order(found: Documents) -> None:
    vibe(found, "leafy")["terms"].reverse()


def with_shares(tag_id: str, *hundredths: int) -> Callable[[Documents], None]:
    """Shares that break a rule of a recipe. The recipe is refused before a band is read."""

    def change(found: Documents) -> None:
        for term, share in zip(vibe(found, tag_id)["terms"], hundredths, strict=True):
            term["hundredths"] = share

    return change


def changed(tag_id: str, **more: Any) -> Callable[[Documents], None]:
    def change(found: Documents) -> None:
        vibe(found, tag_id).update(more)

    return change


@pytest.mark.parametrize(
    "broken",
    [
        a_part_added,
        a_part_taken_out,
        a_part_turned_round,
        a_part_in_the_place_of_another,
        who_lived_there_read_from_the_low_end,
        in_another_order,
        # It does not sum to 100.
        with_shares("leafy", 50, 30, 30),
        # One part could place an area alone.
        with_shares("leafy", 60, 20, 20),
        # Beside a part that counts who lived there, no part is over 40.
        with_shares("family_area", 45, 25, 15, 15),
        with_shares("family_area", 30, 45, 15, 10),
        changed("leafy", meaning="The best streets"),
        changed("leafy", family="daily_life"),
        changed("leafy", shape="scale", low_end="Bare", high_end="Leafy"),
        changed("leafy", strip=False),
        changed("leafy", shelf_word="green"),
        changed("family_area", strip=True),
    ],
)
def test_nothing_of_a_recipe_may_differ_from_cores_but_its_shares(
    broken: Callable[[Documents], None],
):
    found = documents()
    broken(found)
    assert refused(found) == ("catalogue.json", "vibes_match_core")


def test_a_part_of_a_recipe_holds_a_hundredth_at_the_least():
    found = documents()
    terms = vibe(found, "leafy")["terms"]
    terms[0]["hundredths"], terms[2]["hundredths"] = 70, 0
    assert refused(found)[0] == "catalogue.json"


# The name of a vibe, and of each of its ends


def test_a_release_may_name_a_vibe_and_its_ends_otherwise_than_core():
    found = documents()
    vibe(found, "pace").update(
        label="Nights out", short_label="Nights out", low_end="Still", high_end="Busy"
    )
    vibe(found, "leafy").update(label="Green and leafy", short_label="Green and leafy")
    release = parse_release(found)
    names = {one.tag_id: (one.label, one.low_end, one.high_end) for one in release.vibes}
    assert names[TagId.PACE] == ("Nights out", "Still", "Busy")
    assert names[TagId.LEAFY] == ("Green and leafy", None, None)
    # What is said of an area says the name the release gives, and no other.
    facts = {fact.fact_id: fact for fact in facts_for(release, area_id(1), None)}
    pace = facts[f"{area_id(1)}/{FactKind.TAG}/pace"]
    assert pace.label == "Nights out"
    assert "Going out" not in (pace.label, *pace.slots.values())
    said = {pace.slots.get("low_end"), pace.slots.get("high_end")}
    assert said <= {"Still", "Busy", "least", "most", None}


NAMES: list[tuple[str, bool]] = [
    ("Green and leafy", True),
    ("Nights out", True),
    ("Café streets", True),
    ("", False),
    (" Leafy", False),
    ("Leafy ", False),
    ("x" * 41, False),
    ("Two\nlines", False),
    ("Leafy​", False),
    # A name holds no figure.
    ("Top 10 streets", False),
    ("Band 5", False),
    # No sentence may call a place safe or unsafe, and no name may.
    ("Safe streets", False),
    ("Unsafe", False),
    ("Rough", False),
    ("Dodgy end", False),
    ("S\N{CYRILLIC SMALL LETTER A}fe streets", False),
    # Praise and blame with nothing behind it.
    ("Best streets", False),
    ("Vibrant", False),
    ("Friendly", False),
    ("Up and coming", False),
    ("Highly rated", False),
    # A name says nothing of who lives somewhere.
    ("Students", False),
    ("Student area", False),
    ("Muslim area", False),
    ("Working class", False),
    ("Posh people", False),
    ("Polish families", False),
    ("Immigrants", False),
]


@pytest.mark.parametrize(("words", "plain"), NAMES)
def test_a_name_a_person_gives_is_held_to_the_words_no_sentence_may_say(words: str, plain: bool):
    assert name_is_plain(words) is plain


def test_a_label_may_hold_a_figure_and_be_long_and_a_name_may_not():
    within = "Places to eat within 1,000 m of home, in a straight line"
    assert name_is_plain(within, limit=200, figures=True)
    assert not name_is_plain(within)
    assert not name_is_plain("x" * 201, limit=200, figures=True)


@pytest.mark.parametrize(
    "changed",
    [
        {"label": "Safe streets", "short_label": "Safe streets"},
        {"label": "Vibrant", "short_label": "Vibrant"},
        {"label": "Students", "short_label": "Students"},
        {"label": "Top 10", "short_label": "Top 10"},
        {"label": "Nights out", "short_label": "Going out"},
        {"label": "Nights out"},
        {"low_end": "Dead", "high_end": "Vibrant"},
        {"low_end": "Buzzy"},
        {"low_end": None},
        {"low_end": ""},
    ],
)
def test_a_name_that_is_not_plain_is_refused(changed: dict[str, Any]):
    found = documents()
    vibe(found, "pace").update(changed)
    assert refused(found) == ("catalogue.json", "vibes_match_core")


def test_the_names_core_gives_are_never_refused_whatever_words_they_hold():
    # Gritty and Polished are the names of the ends of one scale, and Young professionals
    # names who is counted. Each is core's own, and is a name and no verdict.
    for tag in TAGS.values():
        assert what_a_vibe_breaks(tag) is None, tag.tag_id
    gritty = TAGS[TagId.STREET_CHARACTER]
    assert what_a_vibe_breaks(gritty.replace(low_end="Smart")) is None
    assert what_a_vibe_breaks(gritty.replace(label="Gritty streets", short_label="Gritty streets"))


# What a vibe cannot see


def test_a_release_may_say_otherwise_what_a_vibe_cannot_see_after_the_first_line():
    found = documents()
    lines = [COMMON_CANNOT_SEE, "Street trees.", "Whether a garden is paved over."]
    vibe(found, "leafy").update(cannot_see=lines)
    release = parse_release(found)
    held = next(one for one in release.vibes if one.tag_id is TagId.LEAFY)
    assert list(held.cannot_see) == lines


@pytest.mark.parametrize(
    ("tag_id", "lines"),
    [
        ("leafy", ["Street trees."]),
        ("leafy", ["Street trees.", COMMON_CANNOT_SEE]),
        ("leafy", []),
        ("leafy", [COMMON_CANNOT_SEE, ""]),
        ("leafy", [COMMON_CANNOT_SEE, "Whether it is safe."]),
        ("leafy", [COMMON_CANNOT_SEE, "Whether the students are friendly."]),
        ("leafy", [COMMON_CANNOT_SEE, "x" * 201]),
        ("leafy", [COMMON_CANNOT_SEE, *["Street trees."] * 12]),
        # What is counted was counted on one day, and the vibe goes on saying so.
        ("family_area", [COMMON_CANNOT_SEE, "Catchments."]),
        # What is recorded depends on what is reported, and the vibe goes on saying so.
        ("street_character", [COMMON_CANNOT_SEE, "Empty shops."]),
    ],
)
def test_what_a_vibe_cannot_see_keeps_what_core_holds_it_to(tag_id: str, lines: list[str]):
    found = documents()
    vibe(found, tag_id).update(cannot_see=lines)
    assert refused(found) == ("catalogue.json", "vibes_match_core")


# The label of a measure


def test_a_release_may_label_a_measure_otherwise_than_core():
    found = documents()
    measure(found, "homes_density").update(
        label="Homes to the hectare", short_label="Homes close by"
    )
    release = parse_release(found)
    held = next(one for one in release.metrics if one.feature_id is FeatureId.HOMES_DENSITY)
    assert (held.label, held.short_label) == ("Homes to the hectare", "Homes close by")
    facts = {fact.fact_id: fact for fact in facts_for(release, area_id(1), None)}
    density = facts[f"{area_id(1)}/{FactKind.FEATURE}/homes_density"]
    assert density.label == "Homes to the hectare"
    assert density.slots["label"] == "Homes to the hectare"


@pytest.mark.parametrize(
    ("feature_id", "changed"),
    [
        ("homes_density", {"label": "Best streets"}),
        ("homes_density", {"label": "Safe homes"}),
        ("homes_density", {"label": "Homes of students"}),
        ("homes_density", {"label": ""}),
        ("homes_density", {"label": "x" * 201}),
        ("homes_density", {"short_label": "Homes within 10 m"}),
        ("homes_density", {"short_label": "x" * 41}),
        ("homes_density", {"unit": "per acre"}),
        ("homes_density", {"polarity": "more"}),
        ("homes_density", {"in_likeness": True}),
        # Who was counted is named by core, and ends with the census it was counted at.
        ("residents_aged_20_34", {"label": "Young people nearby"}),
        ("residents_aged_20_34", {"short_label": "More young people"}),
        ("households_dependent_children", {"label": "Families, Census 2021"}),
    ],
)
def test_a_label_that_is_not_plain_and_a_measure_that_is_not_cores_are_refused(
    feature_id: str, changed: dict[str, Any]
):
    found = documents()
    measure(found, feature_id).update(changed)
    assert refused(found) == ("catalogue.json", "catalogue_matches_core")


def test_every_measure_as_core_names_it_is_a_measure_a_release_may_carry():
    found = documents()
    release = parse_release(found)
    assert all(what_a_measure_breaks(metric) is None for metric in release.metrics)
    assert {metric.label for metric in release.metrics} <= {f.label for f in FEATURES.values()}
