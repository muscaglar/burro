"""What an offer says of itself, for a client that takes what is offered and asks nothing.

Two promises of the product rested on a person choosing. Recorded crime counts
only when a person asks for it by name, and to type "gritty" is to ask. And
some things are offered and never applied: what counts who lived somewhere,
and the share of homes in the higher council tax bands, which follows what
households are estimated to have (ADR 0006, 0013 and 0028).

So an offer says two things. `by_name`: the person's own words name what it
counts, as "gritty" and "low crime" name recorded crime, and "safe" and "posh"
do not. `only_by_choice`: what is offered waits for a person to choose it, and
is never applied for them. Every sentence here is made up.
"""

import pytest
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    HOLDS_CRIME,
    HOLDS_RESIDENTS,
    OFFERED_AND_NEVER_APPLIED,
    TAGS,
    only_by_choice,
)
from burro_core.ids import Dimension, FeatureId, TagId, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter, Suggestion
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
CRIME = Dimension.CRIME

GRITTY = f"tag:{TagId.STREET_CHARACTER}"
VIOLENCE = f"feature:{FeatureId.CRIME_VIOLENCE_ROBBERY}"
BURGLARY = f"feature:{FeatureId.CRIME_BURGLARY_THEFT}"
DAMAGE = f"feature:{FeatureId.INCIDENT_CRIMINAL_DAMAGE}"
BANDS = f"feature:{FeatureId.HOMES_HIGHER_BANDS}"
SELLS_FOR = f"feature:{FeatureId.PRICE_MEDIAN}"
MIX = f"feature:{FeatureId.BRAND_MIX}"
PACE = f"tag:{TagId.PACE}"
LEAFY = f"tag:{TagId.LEAFY}"
PUBS = f"feature:{FeatureId.VENUE_EVENING_PER_HOMES}"


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def offers(text: str) -> dict[str, Suggestion]:
    found = read(text)
    # Nothing is applied of a sentence that is no plain list: all of it is offered.
    assert found.operations == NO_OPERATIONS
    return {offer.target: offer for offer in found.suggestions}


# Each sentence names recorded crime, in a measure or in the vibe that holds it, in a
# sentence that is no plain list: the person asked for it by name.
NAMES_CRIME = [
    ("Somewhere gritty, I think", (GRITTY,)),
    ("somewhere polished, I think", (GRITTY,)),
    ("low crime and leafy, honestly", (VIOLENCE, BURGLARY)),
    ("honestly, a low crime rate", (VIOLENCE, BURGLARY)),
    ("burglary worries me", (BURGLARY,)),
    ("honestly, I worry about violent crime", (VIOLENCE,)),
    ("vandalism worries me", (DAMAGE,)),
]
# Each is a word that recorded crime is only read into. It names none.
NAME_NO_CRIME = [
    ("I want somewhere safe", (VIOLENCE, BURGLARY)),
    ("honestly, I want to feel safe", (VIOLENCE, BURGLARY)),
    ("somewhere posh", (GRITTY,)),
    ("somewhere affluent, I think", (GRITTY,)),
    ("somewhere edgy, I think", (GRITTY,)),
    ("a bit rough, honestly", (GRITTY,)),
    ("honestly, somewhere up and coming", (GRITTY,)),
    ("near the warehouses, I think", (GRITTY,)),
]


@pytest.mark.parametrize(("text", "targets"), NAMES_CRIME)
def test_words_that_name_recorded_crime_say_so_of_every_offer_of_it(
    text: str, targets: tuple[str, ...]
):
    found = offers(text)

    assert set(targets) <= set(found), sorted(found)
    for target in targets:
        assert found[target].by_name, target
        # The person asked for it by name, so it waits for nobody.
        assert not found[target].only_by_choice, target


@pytest.mark.parametrize(("text", "targets"), NAME_NO_CRIME)
def test_a_word_that_recorded_crime_is_read_into_names_none_and_the_offer_waits_for_a_person(
    text: str, targets: tuple[str, ...]
):
    found = offers(text)

    assert set(targets) <= set(found), sorted(found)
    for target in targets:
        assert not found[target].by_name, target
        assert found[target].only_by_choice, target


def test_every_offer_that_counts_recorded_crime_waits_for_a_person_unless_the_words_name_it():
    sentences = [text for text, _ in (*NAMES_CRIME, *NAME_NO_CRIME)]
    seen = 0
    for text in sentences:
        for offer in read(text).suggestions:
            kind, _, named = offer.target.partition(":")
            of_a_measure = kind == "feature" and FEATURES[FeatureId(named)].dimension is CRIME
            if of_a_measure or (kind == "tag" and TagId(named) in HOLDS_CRIME):
                seen += 1
                assert offer.only_by_choice is not offer.by_name, (text, offer.target)
    assert seen >= len(sentences)


def test_the_name_of_a_scale_names_no_end_of_it_so_it_names_nothing_the_offer_counts():
    # "Street character" is what the scale was called. It names neither Gritty nor Polished.
    found = offers("street character, I think")

    assert not found[GRITTY].by_name
    assert found[GRITTY].only_by_choice
    assert not offers("going out, honestly")[PACE].by_name


def test_a_word_for_a_smart_area_is_offered_the_higher_bands_and_never_has_them_applied():
    found = offers("somewhere posh")

    assert found[BANDS].only_by_choice
    assert not found[BANDS].by_name
    # The other readings of the word are of the place, and no record holds them back.
    assert not found[MIX].only_by_choice
    assert not found[SELLS_FOR].only_by_choice
    assert not found[MIX].by_name and not found[SELLS_FOR].by_name


def test_the_higher_bands_wait_for_nobody_where_the_words_are_the_name_of_the_measure():
    label = FEATURES[FeatureId.HOMES_HIGHER_BANDS].short_label.lower()
    found = offers(f"honestly, {label}")

    assert found[BANDS].by_name
    assert not found[BANDS].only_by_choice


WHO_IS_COUNTED = [
    "young professionals",
    "families, honestly",
    "somewhere with lots of families, I think",
    "retirees, honestly",
    "honestly, people my age",
    f"honestly, {FEATURES[FeatureId.RESIDENTS_AGED_20_34].short_label.lower()}",
    f"honestly, {TAGS[TagId.FAMILY_AREA].label.lower()}",
]


@pytest.mark.parametrize("text", WHO_IS_COUNTED)
def test_what_counts_who_lived_somewhere_waits_for_a_person_whatever_the_words(text: str):
    found = read(text).suggestions
    counted = [
        offer
        for offer in found
        if offer.target.removeprefix("feature:") in {f.value for f in COUNTS_RESIDENTS}
        or offer.target.removeprefix("tag:") in {t.value for t in HOLDS_RESIDENTS}
    ]

    assert counted, [offer.target for offer in found]
    assert all(offer.only_by_choice for offer in counted)


NAMED = [
    ("Honestly, somewhere leafy", LEAFY, True),
    ("Honestly, more pubs", PUBS, True),
    ("Honestly, somewhere buzzy", PACE, True),
    # A word that a thing is read into names it no more than "safe" names crime.
    ("Honestly, somewhere lively", PACE, False),
    ("Honestly, somewhere green", LEAFY, False),
]


@pytest.mark.parametrize(("text", "target", "named"), NAMED)
def test_any_thing_says_whether_the_words_name_it_and_waits_for_nobody(
    text: str, target: str, named: bool
):
    found = offers(text)

    assert found[target].by_name is named
    assert not found[target].only_by_choice


def test_what_is_read_from_a_name_or_a_number_that_was_typed_is_named_by_it():
    found = offers("honestly, renting, about £1,500 a month, 30 minutes to Pellam Cross")

    assert {"tenure", "budget", "commute"} <= set(found)
    for target in ("tenure", "budget", "commute"):
        assert found[target].by_name, target
        assert not found[target].only_by_choice, target


def test_a_thing_named_once_and_read_into_another_word_is_named():
    # "Posh" reads the scale into a word, and "gritty" names it.
    found = offers("posh but gritty, I think")

    assert found[GRITTY].by_name
    assert not found[GRITTY].only_by_choice


def test_the_measures_that_are_offered_and_never_applied_are_marked_where_they_are_defined():
    assert frozenset({FeatureId.HOMES_HIGHER_BANDS}) == OFFERED_AND_NEVER_APPLIED
    in_a_vibe = {term.feature_id for tag in TAGS.values() for term in tag.terms}
    # Each stands in no vibe, so no vibe counts one unasked.
    assert not OFFERED_AND_NEVER_APPLIED & in_a_vibe
    assert not OFFERED_AND_NEVER_APPLIED & COUNTS_RESIDENTS


@pytest.mark.parametrize("named", [True, False])
def test_what_waits_for_a_person_is_said_of_every_measure_and_every_vibe(named: bool):
    for feature_id, feature in FEATURES.items():
        residents = feature_id in COUNTS_RESIDENTS
        by_name_alone = feature.dimension is CRIME or feature_id in OFFERED_AND_NEVER_APPLIED
        expected = residents or (by_name_alone and not named)
        assert only_by_choice(feature_id, named) is expected, feature_id
    for tag_id in TAGS:
        expected = tag_id in HOLDS_RESIDENTS or (tag_id in HOLDS_CRIME and not named)
        assert only_by_choice(tag_id, named) is expected, tag_id
