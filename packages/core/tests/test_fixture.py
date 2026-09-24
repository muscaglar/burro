"""What must hold of the committed synthetic release, which is what the service runs on.

The other tests build their releases by hand. These read the one that is
committed, because what they protect was found there: a word that begins a
name, a wish that barely moved the ranking, a sentence that was untrue of the
release it described.
"""

import dataclasses
import re

import pytest
from burro_core.catalogue import FEATURES
from burro_core.explain import render
from burro_core.facts import Fact, facts_for
from burro_core.ids import (
    FactKind,
    FeatureId,
    InterpretStatus,
    Mode,
    Notice,
    Provenance,
    Strictness,
    TagId,
    Tenure,
    UnmetCategory,
)
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.ops import NO_OPERATIONS
from burro_core.places import resolve_area, resolve_place
from burro_core.rank import RankedArea, RankResult, rank
from burro_core.reducer import ReducerResult, apply
from burro_core.release import InMemoryRelease, Neighbourhood
from burro_core.spec import Commute, PreferenceSpec, default_spec
from burro_core.verify import verify

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)


def release() -> InMemoryRelease:
    return fixture_release()


def name_of(area_id: str) -> str:
    found = release().neighbourhood(area_id)
    assert found is not None
    return found.name


# One reader for every test: it keeps the names of the release and nothing else.
READER = RuleInterpreter()


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=release()))


def reduced(text: str, spec: PreferenceSpec = RENTER) -> ReducerResult:
    return apply(spec, read(text, spec).operations, release())


def ranked(text: str, spec: PreferenceSpec = RENTER) -> RankResult:
    return rank(reduced(text, spec).spec, release())


def first_names(result: RankResult, count: int) -> list[str]:
    return [name_of(area.area_id) for area in result.ranked[:count]]


def said(area: RankedArea, spec: PreferenceSpec) -> dict[str, float | None]:
    """The utility of each component the person asked for, as against a default."""
    asked = {f"feature:{w.feature_id}" for w in spec.weights if w.provenance != "default"}
    asked |= {f"tag:{t.tag_id}" for t in spec.tags}
    return {c.component: c.utility for c in area.contributions if c.component in asked}


# What a person types, the area this release puts first for it, and why that is sensible.
WISHES = [
    ("leafy and quiet", "Alderwick", "it is the leafiest area of the release and the quietest"),
    (
        "somewhere buzzy with bars and restaurants",
        "Pellam Cross",
        "it is the centre, with more places to eat and drink than anywhere else",
    ),
    (
        "good schools and a park for the kids",
        "Dulcimer Green",
        "its schools have the best results of any area, and a park is close",
    ),
    (
        "by the river",
        "Sable Reach",
        "it is inside the bend of the river, with more of its land by the water than any other",
    ),
]


@pytest.mark.parametrize(("text", "first", "because"), WISHES, ids=[w[0] for w in WISHES])
def test_what_a_person_says_decides_which_area_comes_first(text: str, first: str, because: str):
    spec = reduced(text).spec
    result = rank(spec, release())
    assert first_names(result, 1) == [first], because
    # The area that comes first does well on every single thing that was asked for.
    asked = said(result.ranked[0], spec)
    assert asked
    assert all(utility is not None and utility >= 0.65 for utility in asked.values()), asked
    # And the wish moved the ranking where a person would see it: the first
    # three are not the three the defaults alone show, and an area has come
    # into the first five that was not there.
    by_default = first_names(rank(RENTER, release()), 5)
    assert first_names(result, 3) != by_default[:3]
    assert set(first_names(result, 5)) - set(by_default)


def test_four_different_wishes_put_four_different_areas_first():
    firsts = [first_names(ranked(text), 1)[0] for text, _, _ in WISHES]
    assert len(set(firsts)) == len(WISHES), firsts
    assert firsts == [first for _, first, _ in WISHES]


def waterside(area_id: str) -> float:
    row = release().tag(area_id, TagId.WATERSIDE)
    return 0.0 if row is None or row.score is None else row.score


def test_the_places_most_like_what_was_asked_for_are_all_near_the_top():
    # One thing said is worth 0.50 and what was left unsaid 0.35 in all. When
    # the defaults gave way to a third it was 0.55, and "by the river" kept
    # the area the defaults put first. Now the area most by the water is
    # first, and the three most by the water are in the first four.
    by_the_water = sorted(
        (area for area in release().neighbourhoods if area.rankable),
        key=lambda area: -waterside(area.area_id),
    )
    first_four = first_names(ranked("by the river"), 4)
    assert {area.name for area in by_the_water[:3]} <= set(first_four)
    assert first_four[0] == by_the_water[0].name
    # A buyer's defaults weigh more, 0.45 in all. The area they like best is
    # itself fifth of 22 for water and stays first, with Sable Reach second.
    buying = first_names(ranked("by the river", default_spec(Tenure.BUY)), 2)
    assert buying == ["Brackenhythe", by_the_water[0].name]


def said_against_unsaid(text: str, spec: PreferenceSpec) -> tuple[float, float]:
    after = reduced(text, spec).spec
    unsaid = sum(w.weight for w in after.weights if w.provenance == "default")
    stated = sum(w.weight for w in after.weights if w.provenance != "default")
    stated += sum(t.weight for t in after.tags)
    return round(stated, 2), round(unsaid, 2)


def test_one_thing_said_counts_for_more_than_everything_left_unsaid():
    assert {text: said_against_unsaid(text, RENTER) for text, _, _ in WISHES} == {
        "leafy and quiet": (1.0, 0.35),
        "somewhere buzzy with bars and restaurants": (1.5, 0.35),
        # The park had a default of its own, which is now the person's.
        "good schools and a park for the kids": (1.5, 0.3),
        "by the river": (0.5, 0.35),
    }
    # A buyer's defaults are heavier, and one thing said still outweighs them.
    assert said_against_unsaid("by the river", default_spec(Tenure.BUY)) == (0.5, 0.45)
    assert said_against_unsaid("leafy", default_spec(Tenure.BUY)) == (0.5, 0.45)


ORDINARY_WORDS = [
    "not far from a station",
    "somewhere not far from Pellam Cross",
    "avoid ma",
    "not too noisy",
    "only a short walk from the shops",
    "not far out",
]


@pytest.mark.parametrize("text", ORDINARY_WORDS)
def test_an_ordinary_word_excludes_no_area_of_the_release(text: str):
    # "Far" begins Farrowmere and "ma" Marrowfen. Neither was named.
    result = read(text)
    assert result.operations.area_ops == ()
    assert rank(reduced(text).spec, release()).filtered == ()


def test_no_single_letter_is_a_place_to_work_at():
    for letter in "abcdefghijklmnopqrstuvwxyz":
        result = read(f"I work at {letter}")
        # At most it is asked about: the edit carries no id, and the reducer turns it away.
        assert {edit.place_id for edit in result.operations.commute_ops} <= {""}, letter
        assert reduced(f"I work at {letter}").spec == RENTER
    asked = read("I work at b")
    assert asked.status is InterpretStatus.CLARIFY
    assert "Brackenhythe" in {option.name for option in asked.clarify[0].options}


def test_no_single_letter_resolves_to_an_area_or_a_place_of_the_release():
    # Nine letters each began the name of one area, and so resolved to it.
    for letter in "abcdefghijklmnopqrstuvwxyz":
        assert resolve_area(letter, release()).resolved is None, letter
        assert resolve_place(letter, release()).resolved is None, letter
    # The whole of a name still does, and so do whole words from the start of one.
    for area in release().neighbourhoods:
        assert resolve_area(area.name, release()).resolved == area.area_id
    assert (
        resolve_area("Hollinsworth", release()).resolved
        == resolve_area("Hollinsworth Quay", release()).resolved
    )


def test_not_far_from_a_named_place_adds_the_journey_and_excludes_nothing():
    spec = reduced("somewhere not far from Pellam Cross").spec
    (commute,) = spec.commutes
    place = release().place(commute.place_id)
    assert place is not None and place.name == "Pellam Cross"
    assert spec.areas == ()


@pytest.mark.parametrize(
    "text",
    [
        "far from a university",
        "nowhere near a university",
        "as far from the university as possible",
        "far from the campus",
        "gay village",
        "student village",
    ],
)
def test_a_request_about_who_lives_somewhere_changes_no_ranking(text: str):
    result = read(text)
    assert (result.status, result.notice) == (
        InterpretStatus.POLICY_REDIRECT,
        Notice.NEUTRAL_PLACES,
    )
    assert result.operations == NO_OPERATIONS
    # The area around the campus is ranked where the defaults alone put it.
    assert rank(reduced(text).spec, release()) == rank(RENTER, release())


@pytest.mark.parametrize("text", ["muslim schools", "jewish schools nearby"])
def test_a_school_for_a_community_is_an_amenity_and_weights_no_school_results(text: str):
    result = read(text)
    assert (result.status, result.unmet) == (
        InterpretStatus.OK,
        (UnmetCategory.COMMUNITY_AMENITIES,),
    )
    assert reduced(text).spec == RENTER


def test_exactly_half_the_default_weight_present_is_ranked_whichever_half_it_is():
    # An area with no figure for air, noise or the walk to a station has 0.9
    # of the 1.8 a renter's default asks for. So has one with no figure for
    # the high street, the park or the lines. Both are ranked.
    known = release()
    # An area that has a figure for every feature the default weighs.
    target = next(area.area_id for area in rank(RENTER, known).ranked if area.weight_coverage == 1)
    for missing in (
        {"air_no2", "noise_exposure", "station_walk"},
        {"highstreet_access", "park_proximity", "station_lines"},
    ):
        gaps = tuple(
            row.replace(value=None, percentile=None, coverage=0.0)
            if row.area_id == target and row.feature_id in missing
            else row
            for row in known.features
        )
        result = rank(RENTER, dataclasses.replace(known, features=gaps))
        area = next(a for a in result.ranked if a.area_id == target)
        assert area.weight_coverage == 0.5


BEYOND = re.compile(
    r"(?P<word>[a-z ]+?)(?: than)? (?P<pct>\d+)% of the (?P<compared>\d+) areas compared in "
    r"this release(?:, and the same as (?P<level>\d+) others?)?\.(?: Recorded crime .*)?"
)
LEVEL = re.compile(
    r"the same as (?:(?P<level>\d+) of the |all )(?P<others>\d+) other areas compared in this "
    r"release\.(?: Recorded crime .*)?"
)


def figures(fact: Fact) -> tuple[list[float], float, tuple[str, str]]:
    """The figure of every rankable area, this area's own, and the words for above and below."""
    known = release()

    def figure(area_id: str) -> float | None:
        if fact.kind is FactKind.TAG:
            tag = known.tag(area_id, TagId(fact.key))
            return None if tag is None or tag.score is None else tag.raw
        feature = known.feature(area_id, FeatureId(fact.key))
        return None if feature is None else feature.value

    words = ("ranks above", "ranks below")
    if fact.kind is FactKind.FEATURE:
        words = (FEATURES[FeatureId(fact.key)].higher, FEATURES[FeatureId(fact.key)].lower)
    population = [
        found
        for area in known.neighbourhoods
        if area.rankable and (found := figure(area.area_id)) is not None
    ]
    mine = figure(fact.area_id)
    assert mine is not None
    return population, mine, words


def true_of_the_release(text: str, fact: Fact, area: Neighbourhood) -> bool:
    """Whether the comparison a sentence makes is literally true of the committed release.

    It is worked out here from the rows of the release, and not from the fact,
    so that a fact that carried a wrong number would be caught.
    """
    population, mine, (above, below) = figures(fact)
    lower = sum(1 for figure in population if figure < mine)
    higher = sum(1 for figure in population if figure > mine)
    level = sum(1 for figure in population if figure == mine) - area.rankable
    claim = text.split(": ", 1)[1]
    claim = claim if fact.kind is FactKind.TAG else claim.split(", ", 1)[1]
    if (said := LEVEL.fullmatch(claim.removeprefix("ranks "))) is not None:
        few = 100 * max(lower, higher) < len(population)
        others = lower + higher + level
        return few and (int(said["level"] or others), int(said["others"])) == (level, others)
    said = BEYOND.fullmatch(claim)
    if said is None or said["word"] not in (above, below):
        return False
    beyond = lower if said["word"] == above else higher
    share = 100 * beyond / len(population)
    return (
        int(said["compared"]) == len(population)
        # The share is rounded down, so the sentence never says more than is so.
        and int(said["pct"]) <= share < int(said["pct"]) + 1
        # And every area that is level is counted: none is passed off as beaten.
        and int(said["level"] or 0) == level
    )


def comparisons() -> list[tuple[Neighbourhood, Fact]]:
    return [
        (area, fact)
        for area in release().neighbourhoods
        for fact in facts_for(release(), area.area_id, None)
        if fact.kind in (FactKind.FEATURE, FactKind.TAG)
    ]


def test_every_comparison_said_of_the_release_is_literally_true():
    checked = comparisons()
    for area, fact in checked:
        text = render(fact).text
        assert true_of_the_release(text, fact, area), text
    # Every feature and every tag of every area, the two that are not ranked included.
    assert len(checked) > 750
    assert {area.rankable for area, _ in checked} == {True, False}
    assert {fact.key for _, fact in checked} == {*FeatureId, *TagId}


def scored_on(fact: Fact) -> float:
    """The mid-rank percentile the area is scored on for this feature or tag."""
    if fact.kind is FactKind.TAG:
        tag = release().tag(fact.area_id, TagId(fact.key))
        assert tag is not None and tag.score is not None
        return tag.score
    feature = release().feature(fact.area_id, FeatureId(fact.key))
    assert feature is not None and feature.percentile is not None
    return feature.percentile


def test_a_share_worked_out_from_the_mid_rank_percentile_is_not_true_where_areas_tie():
    # What the sentences said before: the percentile an area is scored on,
    # which counts half of the areas level with it as beaten.
    of = "areas compared in this release."
    untrue: list[str] = []
    for area, fact in comparisons():
        percentile = scored_on(fact)
        _, _, (above, below) = figures(fact)
        compared = fact.slots["compared"]
        if fact.kind is FactKind.TAG:
            old = f"{fact.label}: ranks above {round(percentile)}% of the {compared} {of}"
        else:
            higher = percentile >= 50
            pct = round(percentile) if higher else 100 - round(percentile)
            word = above if higher else below
            old = f"{fact.label}: 0, {word} than {pct}% of the {compared} {of}"
        if not true_of_the_release(old, fact, area):
            untrue.append(old)
    assert len(untrue) > 600
    # An area with no water at all was said to rank above 30% of areas for it.
    assert f"Waterside: ranks above 30% of the 22 {of}" in untrue
    assert (
        "Share of the area within 300 m of a river or canal: 0, less than 70% of the 22 "
        f"{of}" in untrue
    )


TIED = [
    # An area with no water at all. Thirteen of the 22 have none.
    (
        "Thrushcombe",
        "feature/water_access",
        "Share of the area within 300 m of a river or canal: 0%, less than 40% of the 22 "
        "areas compared in this release, and the same as 12 others.",
    ),
    (
        "Thrushcombe",
        "tag/waterside",
        "Waterside: ranks below 40% of the 22 areas compared in this release, and the same "
        "as 12 others.",
    ),
    # An area on one line, as twelve are. Seven have none.
    (
        "Wickerford",
        "feature/station_lines",
        "Lines within a 10-minute walk: 1, more than 31% of the 22 areas compared in this "
        "release, and the same as 11 others.",
    ),
    (
        "Thrushcombe",
        "feature/school_primary_nearby",
        "State primary schools within a short walk: 4, more than 50% of the 22 areas "
        "compared in this release, and the same as 7 others.",
    ),
]


@pytest.mark.parametrize(("name", "key", "text"), TIED, ids=[f"{t[0]} {t[1]}" for t in TIED])
def test_where_areas_tie_the_sentence_says_how_many_and_beats_none_of_them(
    name: str, key: str, text: str
):
    area = next(found for found in release().neighbourhoods if found.name == name)
    facts = {fact.fact_id: fact for fact in facts_for(release(), area.area_id, None)}
    assert render(facts[f"{area.area_id}/{key}"]).text == text


def test_every_sentence_that_can_be_said_of_the_release_passes_the_verifier():
    # Every fact of every area, with a journey to every place the release
    # holds, three at a time. One place is called a Quarter, which is a word
    # for a quantity everywhere but in a name.
    known = release()
    places = [place.place_id for place in known.places]
    assert any("Quarter" in place.name for place in known.places)
    checked = 0
    for first in range(0, len(places), 3):
        spec = RENTER.replace(
            budget=RENTER.budget.replace(amount=1500),
            commutes=tuple(
                Commute(
                    place_id=place_id,
                    mode=Mode.PT,
                    max_minutes=45,
                    strictness=Strictness.SOFT,
                    provenance=Provenance.STATED,
                )
                for place_id in places[first : first + 3]
            ),
        )
        # A rankable area and one that is not. The journeys are what differ between specs.
        for area in (known.neighbourhoods[0], known.neighbourhoods[8]):
            for fact in facts_for(known, area.area_id, spec):
                sentence = render(fact)
                verdict = verify(sentence, {fact.fact_id: fact})
                assert verdict.ok, (sentence.text, verdict.reason)
                checked += 1
    assert not known.neighbourhoods[8].rankable
    assert checked > 1_000
