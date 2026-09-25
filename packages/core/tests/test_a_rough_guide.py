"""A vibe that is a rough guide: how the rules read a word for it, and what its offer says.

The founder decided on 2026-09-25 that Village feel is served though it did
not reach the bar they had set, and that it says it is less sure than the
other vibes (ADR 0013, as amended). So it is never taken without a press of
its own: the rules apply it from no word, and offer it with its label and its
sentence. Every area here is made up.
"""

import pytest
from burro_core.catalogue import ROUGH_GUIDE, ROUGH_GUIDES, TAGS, WHY_A_ROUGH_GUIDE, says_rough
from burro_core.ids import (
    InterpretStatus,
    Provenance,
    Sureness,
    TagId,
    Tenure,
    Toward,
    WeightAction,
)
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.lexicon import LEXICON, NO_IDENTITY, NO_NEIGHBOURS, is_a_rough_guide, prepare
from burro_core.likeness import parts_of, similar
from burro_core.ops import NO_OPERATIONS
from burro_core.portrait import portrait
from burro_core.rank import rank
from burro_core.reducer import apply
from burro_core.release import Release, parse_release
from burro_core.spec import PreferenceSpec, TagWeight, default_spec

from .support import documents, small_release, unplaced
from .test_adjusted import refused, vibe

RENTER = default_spec(Tenure.RENT)
VILLAGE = f"tag:{TagId.VILLAGE_FEEL}"
SAID = says_rough(TagId.VILLAGE_FEEL)
# Every way the reader knows of naming the vibe itself, and plain sentences that hold one.
BY_ITS_NAME = (
    "villagey",
    "village feel",
    "a village feel",
    "Somewhere with a village feel",
    "I like villages",
    "An area with a village vibe",
)
WITH_MORE = (
    "leafy and villagey",
    "villagey, quiet streets and near a park",
    "We're hoping for a village feel with good schools",
)


def read(
    text: str, release: Release | None = None, spec: PreferenceSpec = RENTER
) -> InterpretResult:
    request = InterpretRequest(text=text, spec=spec, release=release or small_release())
    return RuleInterpreter().interpret(request)


def asking_for(tag_id: TagId) -> PreferenceSpec:
    asked = TagWeight(tag_id=tag_id, weight=0.5, toward=Toward.HIGH, provenance=Provenance.STATED)
    return RENTER.replace(tags=(asked,))


def offer_of(result: InterpretResult, target: str = VILLAGE):
    (found,) = [found for found in result.suggestions if found.target == target]
    return found


def test_village_feel_is_the_one_rough_guide_and_says_so_in_these_words():
    assert set(ROUGH_GUIDES) == {TagId.VILLAGE_FEEL}
    assert SAID == (
        "Rough guide. Of the areas it puts highest, about half read as villages to people, "
        "and it takes some busy main roads and some grand inner streets for villages."
    )
    assert f"{ROUGH_GUIDE}. {WHY_A_ROUGH_GUIDE[TagId.VILLAGE_FEEL]}" == SAID


@pytest.mark.parametrize("text", [*BY_ITS_NAME, *WITH_MORE])
def test_the_rules_never_apply_a_rough_guide_from_a_plain_prompt(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.status is InterpretStatus.SUGGEST
    # It is offered, and one press of its own adds it.
    found = offer_of(result)
    assert [choice.label for choice in found.choices] == ["Add Village feel", "Leave it out"]
    pressed = apply(RENTER, found.choices[0].operations, small_release())
    assert pressed.rejected == ()
    assert [tag.tag_id for tag in pressed.spec.active_tags] == [TagId.VILLAGE_FEEL]


@pytest.mark.parametrize("text", BY_ITS_NAME)
def test_its_offer_holds_its_label_and_its_sentence(text: str):
    assert offer_of(read(text)).note == SAID


def test_what_else_a_plain_prompt_asks_for_is_offered_beside_it_and_not_applied():
    """The rules apply a prompt whole or not at all. A prompt that holds a word for a rough
    guide is left to the person, so the rest of it is offered too."""
    result = read("leafy and villagey")
    assert [found.target for found in result.suggestions] == ["tag:leafy", VILLAGE]
    assert offer_of(result, "tag:leafy").note == ""
    # Without the word the prompt is applied as it always was.
    plain = read("leafy")
    assert plain.status is InterpretStatus.OK
    assert [edit.tag_id for edit in plain.operations.tag_ops] == [TagId.LEAFY]


def test_every_phrase_that_reaches_a_rough_guide_is_offered_and_never_applied():
    reaching = {phrase for phrase, target in LEXICON.items() if is_a_rough_guide(target)}
    assert {prepare(text) for text in ("villagey", "village", "villages", "village feel")} <= (
        reaching
    )
    assert {prepare(text) for text in ("community", "identity", "character")} <= reaching
    for phrase in sorted(reaching):
        result = read(phrase)
        assert not [
            edit
            for edit in result.operations.tag_ops
            if edit.tag_id in ROUGH_GUIDES and edit.action is not WeightAction.REMOVE
        ], phrase
        held = apply(RENTER, result.operations, small_release()).spec
        assert not ROUGH_GUIDES & {tag.tag_id for tag in held.active_tags}, phrase


def test_a_word_for_community_is_offered_village_feel_and_says_what_it_counts():
    assert NO_NEIGHBOURS == (
        "Burro cannot measure whether neighbours know each other. The nearest it can count is "
        "a village feel: a high street in a conservation area, homes that stand apart and "
        "period homes."
    )
    for text in ("a sense of community", "somewhere neighbourly"):
        found = offer_of(read(text))
        assert found.note == f"{NO_NEIGHBOURS} {SAID}"


def test_the_note_under_a_word_for_character_names_village_feel_with_its_label():
    assert NO_IDENTITY == (
        "Burro cannot measure the character of a place. The nearest it can count are a village "
        "feel (rough guide), the age of the buildings and a town centre nearby. Choose any that "
        "fit what you mean."
    )
    result = read("somewhere with a real identity")
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == [
        VILLAGE,
        "tag:built_age",
        "feature:highstreet_access",
    ]
    # Each way says what the word is offered as. The offer of Village feel says too that
    # it is a rough guide, and why.
    assert offer_of(result).note == f"{NO_IDENTITY} {SAID}"
    for target in ("tag:built_age", "feature:highstreet_access"):
        assert offer_of(result, target).note == NO_IDENTITY


def test_on_a_release_that_places_no_area_on_it_the_note_names_no_village_feel():
    release = unplaced(small_release(), TagId.VILLAGE_FEEL)
    result = read("somewhere with a real identity", release)
    assert [found.target for found in result.suggestions] == [
        "tag:built_age",
        "feature:highstreet_access",
    ]
    for found in result.suggestions:
        assert "village" not in found.note and ROUGH_GUIDE.lower() not in found.note.lower()
    assert [thing.target for thing in result.not_in_release] == [VILLAGE]


def test_named_twice_it_is_offered_once_with_all_that_is_said_of_it():
    result = read("villagey, with a real identity")
    assert offer_of(result).note == f"{NO_IDENTITY} {SAID}"


def test_a_vibe_that_is_as_sure_as_the_rest_is_applied_as_it_was_and_says_nothing_of_it():
    for tag_id in (TagId.LEAFY, TagId.EVERYDAY_ON_FOOT):
        result = read(TAGS[tag_id].label)
        assert [edit.tag_id for edit in result.operations.tag_ops] == [tag_id]
    for text in ("somewhere historic", "a swimming pool nearby", "safe"):
        for found in read(text).suggestions:
            assert ROUGH_GUIDE not in found.note


def test_to_turn_a_rough_guide_away_is_no_wish_for_it_and_is_read_as_of_any_vibe():
    """It takes the vibe off a search that holds it, and adds it to none."""
    held = asking_for(TagId.VILLAGE_FEEL)
    for text in ("I don't want a village", "not villagey"):
        result = read(text, spec=held)
        assert [(edit.tag_id, edit.action) for edit in result.operations.tag_ops] == [
            (TagId.VILLAGE_FEEL, WeightAction.REMOVE)
        ], text
        assert apply(held, result.operations, small_release()).spec.active_tags == ()
        assert apply(RENTER, read(text).operations, small_release()).spec.active_tags == ()


# What is served of it, and what it is used for


def test_a_release_carries_the_field_and_may_not_say_otherwise_than_core():
    found = documents()
    said = {one["tag_id"]: one["sureness"] for one in found["catalogue.json"]["vibes"]}
    assert said.pop("village_feel") == "rough_guide"
    assert set(said.values()) == {"as_the_rest"}
    # A release that calls it as sure as the rest is refused, as is one that calls
    # another vibe a rough guide: the field is core's, and no hand may change it.
    vibe(found, "village_feel")["sureness"] = "as_the_rest"
    assert refused(found) == ("catalogue.json", "vibes_match_core")
    other = documents()
    vibe(other, "leafy")["sureness"] = "rough_guide"
    assert refused(other) == ("catalogue.json", "vibes_match_core")


def test_a_vibe_that_does_not_say_is_as_sure_as_the_rest():
    """What a client assumes where the field is absent. Core reads such a vibe so too."""
    found = documents()
    del vibe(found, "leafy")["sureness"]
    (leafy,) = [one for one in parse_release(found).vibes if one.tag_id is TagId.LEAFY]
    assert leafy.sureness is Sureness.AS_THE_REST


def test_a_rough_guide_is_on_a_result_only_where_the_person_asked_for_it():
    release = small_release()
    for area in rank(RENTER, release).ranked:
        assert TagId.VILLAGE_FEEL not in {mark.tag_id for mark in area.strip}
    asked = rank(asking_for(TagId.VILLAGE_FEEL), release)
    placed = [
        area
        for area in asked.ranked
        if (row := release.tag(area.area_id, TagId.VILLAGE_FEEL)) is not None and row.band
    ]
    assert placed
    for area in placed:
        (mark,) = [mark for mark in area.strip if mark.tag_id is TagId.VILLAGE_FEEL]
        assert mark.asked
    # Asked for another vibe, no result shows it.
    for area in rank(asking_for(TagId.LEAFY), release).ranked:
        assert TagId.VILLAGE_FEEL not in {mark.tag_id for mark in area.strip}


def test_no_portrait_says_an_area_has_most_or_least_of_a_rough_guide():
    release = small_release()
    seen = 0
    for area in release.neighbourhoods:
        drawn = portrait(release, area.area_id)
        assert drawn is not None
        assert TagId.VILLAGE_FEEL not in {mark.tag_id for mark in (*drawn.more, *drawn.less)}
        seen += TagId.VILLAGE_FEEL in {mark.tag_id for mark in (*drawn.others, *drawn.unplaced)}
    # Where it sits is still shown, among the vibes an area has neither most nor least of.
    assert seen == len(release.neighbourhoods)


def test_no_likeness_between_areas_counts_a_rough_guide_or_the_part_made_for_it():
    release = small_release()
    assert "highstreet_conserved" not in {part.feature_id for part in parts_of(release)}
    without = unplaced(release, TagId.VILLAGE_FEEL)
    for area in release.neighbourhoods:
        assert similar(release, area.area_id) == similar(without, area.area_id)
