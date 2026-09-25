"""What must hold of the committed synthetic release, which is what the service runs on.

The other tests build their releases by hand. These read the one that is
committed, because what they protect was found there: a word that begins a
name, a wish that barely moved the ranking, a sentence that was untrue of the
release it described.
"""

import dataclasses
import re

import pytest
from burro_core.catalogue import FEATURES, band_of
from burro_core.explain import render
from burro_core.facts import Fact, facts_for
from burro_core.ids import (
    FactKind,
    FeatureId,
    InterpretStatus,
    Mode,
    Notice,
    Provenance,
    SentenceRole,
    Strictness,
    TemplateId,
    Tenure,
    UnmetCategory,
    UnrankedReason,
)
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter, Suggestion
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


# One reader for them all: it makes the names of the release ready once.
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
    row = release().feature(area_id, FeatureId.WATER_ACCESS)
    return 0.0 if row is None or row.value is None else row.value


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


def chosen(*pressed: str, spec: PreferenceSpec = RENTER) -> PreferenceSpec:
    """The search after a person has pressed the first choice of each of some suggestions.

    What they typed is not plain, so nothing of it was applied. Each thing
    that was noticed was offered, and they pressed what they had asked for.
    """
    text = (
        "I start at Cindermoor Works in three months. Somewhere leafy and fairly quiet, not "
        "too far from a decent pub. About £1,600 a month on a one bed flat."
    )
    # The first thing offered of each kind: of the budget, its amount.
    offered: dict[str, Suggestion] = {}
    for found in read(text, spec).suggestions:
        offered.setdefault(found.target, found)
    assert set(pressed) <= set(offered)
    for target in pressed:
        spec = apply(spec, offered[target].choices[0].operations, release()).spec
    return spec


def test_an_area_with_no_figure_for_what_was_asked_of_a_place_is_listed_apart_and_never_first():
    # Otterby Fields is the new town: it has a journey time, a rent, and a
    # station, and no figure for how leafy or quiet it is or for its pubs.
    # It came first, 14 points clear, for a newcomer who asked for all three.
    spec = chosen(
        "commute", "tag:leafy", "tag:quiet_residential", "feature:venue_evening_per_homes", "budget"
    )
    result = rank(spec, release())
    assert "Otterby Fields" not in first_names(result, len(result.ranked))
    apart = {name_of(found.area_id): found for found in result.unranked}
    # What is said of the place leads, so an area with no figure for any of it lacks more
    # than half of all that was asked, by weight, and is listed apart for that.
    assert apart["Otterby Fields"].reason is UnrankedReason.INSUFFICIENT_DATA
    assert {"tag:leafy", "tag:quiet_residential", "feature:venue_evening_per_homes"} <= set(
        apart["Otterby Fields"].missing
    )
    # Whoever is ranked has a figure for half or more of the character asked for.
    wished = {c.component for c in result.ranked[0].contributions} - {"commute", "budget"}
    for area in result.ranked:
        weights = {c.component: (c.weight, c.present) for c in area.contributions}
        asked = sum(weights[name][0] for name in wished)
        known = sum(weights[name][0] for name in wished if weights[name][1])
        assert 2 * round(known * 20) >= round(asked * 20), name_of(area.area_id)


def test_a_journey_and_a_rent_alone_do_not_rank_an_area_of_which_little_else_is_known():
    # With a workplace and a budget and nothing said of character, what is
    # left of the usual settings is the character that counts. Otterby Fields
    # has a figure for two of those six, and was second of 22.
    result = rank(chosen("commute", "budget"), release())
    apart = {name_of(found.area_id): found.reason for found in result.unranked}
    assert apart["Otterby Fields"] is UnrankedReason.CHARACTER_UNKNOWN
    assert first_names(result, 1) == ["Cindermoor"]


BEYOND = re.compile(
    r"(?P<word>[a-z ]+?)(?: than)? (?P<pct>\d+)% of the (?P<compared>\d+) areas compared in "
    r"this release(?:, and the same as (?P<level>\d+) others?)?\.(?: Recorded crime .*)?"
)
LEVEL = re.compile(
    r"the same as (?:(?P<level>\d+) of the |all )(?P<others>\d+) other areas compared in this "
    r"release\.(?: Recorded crime .*)?"
)
NONE = re.compile(
    r"(?P<word>[a-z ]+?)(?: than)? none of the (?P<others>\d+) other areas compared in this "
    r"release\.(?: Recorded crime .*)?"
)
# What a band says where it rests on part of its recipe, and nowhere else.
PARTLY = (
    r"(?:Worked out from (?P<known>\d+) of its (?P<parts>\d+) parts, "
    r"(?P<share>\d+) of 100 by weight\. )?"
)
VIBE = re.compile(
    r"band (?P<band>[1-5]) of 5, counted from (?P<low>[A-Za-z ]+) to (?P<high>[A-Za-z ]+), among "
    rf"the (?P<compared>\d+) areas compared in this release\. {PARTLY}"
    r"Parts dated (?P<span>[0-9 to]+)\. The recipe is Burro's own\. The weights are a judgement\."
)
VIBE_RANGE = re.compile(
    r"varies within this area, from band (?P<low_band>[1-5]) to band (?P<high_band>[1-5]) of 5, "
    rf"counted from (?P<low>[A-Za-z ]+) to (?P<high>[A-Za-z ]+)\. {PARTLY}"
    r"Parts dated (?P<span>[0-9 to]+)\. The recipe is Burro's own\. The weights are a judgement\."
)
VIBE_UNKNOWN = re.compile(
    r"Burro cannot place (?P<what>.+)\. Parts with a figure in this release: "
    r"(?P<known>\d+) of (?P<parts>\d+)\."
)


def figures(fact: Fact) -> tuple[list[float], float, tuple[str, str]]:
    """The figure of every rankable area, this area's own, and the words for above and below."""
    known = release()
    feature_id = FeatureId(fact.key)

    def figure(area_id: str) -> float | None:
        feature = known.feature(area_id, feature_id)
        return None if feature is None else feature.value

    population = [
        found
        for area in known.neighbourhoods
        if area.rankable and (found := figure(area.area_id)) is not None
    ]
    mine = figure(fact.area_id)
    assert mine is not None
    return population, mine, (FEATURES[feature_id].higher, FEATURES[feature_id].lower)


def vibe_is_true(text: str, fact: Fact, area: Neighbourhood) -> bool:
    """Whether what a sentence says of a vibe is literally true of the committed release."""
    known = release()
    vibe = next(found for found in known.vibes if found.tag_id == fact.key)
    rows = [known.tag(found.area_id, vibe.tag_id) for found in known.neighbourhoods]
    raws = [None if row is None else row.raw for row in rows]
    rankable = [found.rankable for found in known.neighbourhoods]
    band = band_of(raws, rankable)[known.neighbourhoods.index(area)]
    mine = known.tag(area.area_id, vibe.tag_id)
    assert mine is not None
    compared = sum(
        1 for raw, ranked in zip(raws, rankable, strict=True) if ranked and raw is not None
    )
    ends = (vibe.low_end or "least", vibe.high_end or "most")
    carried = {metric.feature_id for metric in known.metrics}
    have = sum(
        1
        for term in vibe.terms
        if term.feature_id in carried
        and (row := known.feature(area.area_id, term.feature_id)) is not None
        and row.value is not None
    )

    def rests_on(said: re.Match[str]) -> bool:
        """What it says of how much of its recipe it rests on, against the release's own row."""
        if mine.coverage == 1:
            return said["share"] is None
        return (said["known"], said["parts"], said["share"]) == (
            str(have),
            str(len(vibe.terms)),
            str(round(100 * mine.coverage)),
        )

    if (said := VIBE_UNKNOWN.fullmatch(text)) is not None:
        named = said["what"] == f"{area.name} on {vibe.label}"
        return (
            named
            and mine.raw is None
            and (int(said["known"]), int(said["parts"]))
            == (
                have,
                len(vibe.terms),
            )
        )
    claim = text.split(": ", 1)[1]
    if (said := VIBE_RANGE.fullmatch(claim)) is not None:
        spread = (int(said["low_band"]), int(said["high_band"]))
        placed = spread == (mine.spread_low, mine.spread_high)
        return placed and (said["low"], said["high"]) == ends and rests_on(said)
    said = VIBE.fullmatch(claim)
    return (
        said is not None
        and int(said["band"]) == band == mine.band
        and int(said["compared"]) == compared
        and (said["low"], said["high"]) == ends
        and rests_on(said)
    )


def true_of_the_release(text: str, fact: Fact, area: Neighbourhood) -> bool:
    """Whether the comparison a sentence makes is literally true of the committed release.

    It is worked out here from the rows of the release, and not from the fact,
    so that a fact that carried a wrong number would be caught.
    """
    if fact.kind is FactKind.TAG:
        return vibe_is_true(text, fact, area)
    population, mine, (above, below) = figures(fact)
    lower = sum(1 for figure in population if figure < mine)
    higher = sum(1 for figure in population if figure > mine)
    level = sum(1 for figure in population if figure == mine) - area.rankable
    claim = text.split(": ", 1)[1].split(", ", 1)[1]
    others = lower + higher + level
    if (said := LEVEL.fullmatch(claim)) is not None:
        # It is said from one side, where no area is beyond this one.
        none_beyond = min(lower, higher) == 0
        return none_beyond and (int(said["level"] or others), int(said["others"])) == (
            level,
            others,
        )
    if (said := NONE.fullmatch(claim)) is not None:
        beyond = lower if said["word"] == above else higher
        return said["word"] in (above, below) and (beyond, level) == (0, 0)
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
    sides: set[str] = set()
    for area, fact in checked:
        # A figure is said from the side of its role, and both sides are true.
        for role in (SentenceRole.REASON, SentenceRole.TRADE_OFF):
            text = render(fact, role).text
            assert true_of_the_release(text, fact, area), text
            sides.add(text)
    # Every feature and every vibe of every area, the two that are not ranked included.
    assert len(checked) > 1_100 and len(sides) > 1_500
    assert {area.rankable for area, _ in checked} == {True, False}
    carried = {metric.feature_id for metric in release().metrics}
    assert {fact.key for _, fact in checked} == {*carried, *(v.tag_id for v in release().vibes)}
    assert len(carried) == 109 and len(release().vibes) == 14
    # Every way a vibe can be said is said of some area of the release.
    assert {fact.template for _, fact in checked if fact.kind is FactKind.TAG} == {
        TemplateId.VIBE,
        TemplateId.VIBE_RANGE,
        TemplateId.VIBE_UNKNOWN,
    }


def test_no_sentence_about_a_vibe_prints_a_score_a_share_or_a_rank():
    for _, fact in comparisons():
        if fact.kind is FactKind.TAG:
            text = render(fact).text
            assert "%" not in text and "ranks" not in text and "score" not in text, text
            assert "percentile" not in fact.slots


# The name of the share of homes near water, as every sentence of it begins.
WATER = FEATURES[FeatureId.WATER_ACCESS].label


def scored_on(fact: Fact) -> float:
    """The mid-rank percentile the area is scored on for this feature."""
    feature = release().feature(fact.area_id, FeatureId(fact.key))
    assert feature is not None and feature.percentile is not None
    return feature.percentile


def test_a_share_worked_out_from_the_mid_rank_percentile_is_not_true_where_areas_tie():
    # What the sentences said before: the percentile an area is scored on,
    # which counts half of the areas level with it as beaten.
    of = "areas compared in this release."
    untrue: list[str] = []
    for area, fact in comparisons():
        if fact.kind is FactKind.TAG or "compared" not in fact.slots:
            continue  # a vibe is said in bands, and prints no share at all
        percentile = scored_on(fact)
        _, _, (above, below) = figures(fact)
        compared = fact.slots["compared"]
        higher = percentile >= 50
        pct = round(percentile) if higher else 100 - round(percentile)
        word = above if higher else below
        old = f"{fact.label}: 0, {word} than {pct}% of the {compared} {of}"
        if not true_of_the_release(old, fact, area):
            untrue.append(old)
    assert len(untrue) > 600
    # An area with no water at all was said to have less than 70% of areas.
    assert f"{WATER}: 0, less than 70% of the 22 {of}" in untrue


REASON, TRADE_OFF = SentenceRole.REASON, SentenceRole.TRADE_OFF
TIED = [
    # An area with no water at all. Thirteen of the 22 have none. Said as what
    # the area does badly, it is from the side of the areas that have more.
    (
        "Thrushcombe",
        "feature/water_access",
        TRADE_OFF,
        f"{WATER}: 0%, less than 40% of the 22 areas compared in this release, and the same "
        "as 12 others.",
    ),
    # From the better side no area has less, so it says only which are level.
    (
        "Thrushcombe",
        "feature/water_access",
        REASON,
        f"{WATER}: 0%, the same as 12 of the 21 other areas compared in this release.",
    ),
    # An area on one line, as twelve are. Seven have none.
    (
        "Wickerford",
        "feature/station_lines",
        REASON,
        "Lines within a 10-minute walk: 1, more than 31% of the 22 areas compared in this "
        "release, and the same as 11 others.",
    ),
    (
        "Thrushcombe",
        "feature/school_primary_nearby",
        REASON,
        "State primary schools within 800 m in a straight line: 4, more than 54% of the 22 "
        "areas compared in this release, and the same as 6 others.",
    ),
    # A vibe is said in bands, whichever role it has.
    (
        "Foxholt",
        "tag/pace",
        TRADE_OFF,
        "Going out: varies within this area, from band 3 to band 5 of 5, counted from Calm to "
        "Buzzy. Parts dated 2025. The recipe is Burro's own. The weights are a judgement.",
    ),
    (
        "Otterby Fields",
        "tag/leafy",
        REASON,
        "Burro cannot place Otterby Fields on Leafy. Parts with a figure in this release: 1 of 3.",
    ),
]


@pytest.mark.parametrize(
    ("name", "key", "role", "text"), TIED, ids=[f"{t[0]} {t[1]} {t[2].value}" for t in TIED]
)
def test_where_areas_tie_the_sentence_says_how_many_and_beats_none_of_them(
    name: str, key: str, role: SentenceRole, text: str
):
    area = next(found for found in release().neighbourhoods if found.name == name)
    facts = {fact.fact_id: fact for fact in facts_for(release(), area.area_id, None)}
    assert render(facts[f"{area.area_id}/{key}"], role).text == text


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
