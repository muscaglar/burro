"""Which of the publisher's categories is a cafe, a gym or a pub, and which is none.

Nothing is read here: the table is held to itself, and to the rules it is
written by. Every record is made up.
"""

import inspect
import re

import pytest
from burro_pipeline.derive import culture_kinds, venue_kinds
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.venue_kinds import (
    FACILITY,
    IS,
    IS_NOT,
    KINDS,
    OF_FOOD_AND_DRINK,
    OF_SPORT,
    PARENTS,
    READ_UNDER,
    WORDS,
    Kind,
    LeftOut,
    kind_of,
)

FOOD = "food_and_drink"
DRINK = (FOOD, "alcoholic_beverage_venue")
BAR = (*DRINK, "bar")
EATERY = (FOOD, "casual_eatery")
NO_ALCOHOL = (FOOD, "non_alcoholic_beverage_venue")
SPORT = ("sports_and_recreation", FACILITY)
STUDIO = (*SPORT, "fitness_studio")
# A category as the publisher writes one: small letters, digits and `_`.
WRITTEN = re.compile(r"[a-z][a-z0-9_]*")
# Words for who goes somewhere or who lives somewhere. No kind is named for one: a bar
# that the publisher names for who goes there is a bar, and is counted as any other is.
OF_PEOPLE = ("worship", "church", "mosque", "temple", "synagogue", "gurdwara", "religio")


def test_three_kinds_are_counted_and_each_has_a_category_of_its_own():
    assert [kind.value for kind in KINDS] == ["cafe", "gym", "pub"]
    assert set(IS.values()) == set(KINDS) == set(WORDS)
    assert IS["cafe"] is Kind.CAFE and IS["gym"] is Kind.GYM and IS["pub"] is Kind.PUB


def test_a_category_is_on_the_table_once():
    assert not set(IS) & set(IS_NOT)
    assert not set(IS) & PARENTS and not set(IS_NOT) & PARENTS
    assert not set(OF_FOOD_AND_DRINK) & set(OF_SPORT)
    assert IS_NOT == {**OF_FOOD_AND_DRINK, **OF_SPORT}


def test_every_category_is_written_as_the_publisher_writes_one():
    for category in (*IS, *IS_NOT, *PARENTS, *READ_UNDER):
        assert WRITTEN.fullmatch(category), category


def test_every_category_that_is_left_out_says_why_in_plain_words():
    for why in IS_NOT.values():
        assert why and why[0].islower() and not why.endswith(".") and "!" not in why


def test_no_category_of_the_table_is_a_place_of_worship():
    for category in (*IS, *IS_NOT, *PARENTS, *READ_UNDER):
        assert not any(word in category for word in OF_PEOPLE), category


def test_the_table_shares_no_category_with_the_table_of_culture():
    """So no record is a cultural venue and a cafe, a gym or a pub."""
    assert not set(IS) & set(culture_kinds.IS)
    assert not READ_UNDER & culture_kinds.READ_UNDER


@pytest.mark.parametrize(
    ("primary", "hierarchy", "kind"),
    [
        ("cafe", (*EATERY, "cafe"), Kind.CAFE),
        ("coffee_shop", (*NO_ALCOHOL, "coffee_shop"), Kind.CAFE),
        ("tea_room", (*NO_ALCOHOL, "tea_room"), Kind.CAFE),
        ("hong_kong_style_cafe", (*EATERY, "cafe", "hong_kong_style_cafe"), Kind.CAFE),
        ("gym", (*SPORT, "gym"), Kind.GYM),
        ("yoga_studio", (*STUDIO, "yoga_studio"), Kind.GYM),
        ("pilates_studio", (*STUDIO, "pilates_studio"), Kind.GYM),
        ("boot_camp", (*STUDIO, "boot_camp"), Kind.GYM),
        ("cycling_class", (*SPORT, "cycling_class"), Kind.GYM),
        ("boxing_gym", (*SPORT, "boxing_gym"), Kind.GYM),
        ("pub", (*BAR, "pub"), Kind.PUB),
        ("irish_pub", (*BAR, "pub", "irish_pub"), Kind.PUB),
        ("bar", BAR, Kind.PUB),
        ("cocktail_bar", (*BAR, "cocktail_bar"), Kind.PUB),
        ("wine_bar", (*BAR, "wine_bar"), Kind.PUB),
        ("hotel_bar", (*BAR, "hotel_bar"), Kind.PUB),
        ("beer_garden", (*DRINK, "beer_garden"), Kind.PUB),
        ("gastropub", (*EATERY, "gastropub"), Kind.PUB),
    ],
)
def test_the_most_particular_category_of_a_record_decides_its_kind(
    primary: str, hierarchy: tuple[str, ...], kind: Kind
):
    assert kind_of(primary, hierarchy) is kind


def test_a_sport_or_fitness_facility_that_says_no_more_is_counted_as_a_gym():
    """It is a leisure centre or a sports centre, and the file cannot say which."""
    assert FACILITY in READ_UNDER and FACILITY not in PARENTS
    assert kind_of(FACILITY, SPORT) is Kind.GYM


@pytest.mark.parametrize("parent", sorted(PARENTS))
def test_a_record_whose_only_category_stands_above_the_cafes_or_the_bars_is_left_out(
    parent: str,
):
    assert kind_of(parent, (FOOD, parent)) is LeftOut.PARENT_ALONE


@pytest.mark.parametrize(
    ("primary", "hierarchy"),
    [
        # A person who trains others, and has no premises.
        ("fitness_trainer", (*SPORT, "fitness_trainer")),
        # A club for children, most often.
        ("gymnastics_center", (*SPORT, "gymnastics_center")),
        ("dance_studio", (*SPORT, "dance_studio")),
        ("boxing_class", (*SPORT, "boxing_class")),
        ("swimming_pool", (*SPORT, "swimming_pool")),
        ("tennis_court", (*SPORT, "sport_court", "tennis_court")),
        ("rock_climbing_gym", (*SPORT, "rock_climbing_gym")),
        ("internet_cafe", (*EATERY, "cafe", "internet_cafe")),
        ("coffee_roastery", (*NO_ALCOHOL, "coffee_shop", "coffee_roastery")),
        ("bakery", (*EATERY, "bakery")),
        ("sandwich_shop", (*EATERY, "sandwich_shop")),
        ("bubble_tea_shop", (*NO_ALCOHOL, "bubble_tea_shop")),
        ("hookah_bar", (*BAR, "hookah_bar")),
        ("cigar_bar", (*BAR, "cigar_bar")),
        ("lounge", (*DRINK, "lounge")),
        ("brewery", (*DRINK, "brewery")),
        ("tapas_bar", (*EATERY, "tapas_bar")),
    ],
)
def test_a_category_is_not_a_kind_because_it_stands_beside_one(
    primary: str, hierarchy: tuple[str, ...]
):
    assert primary in IS_NOT
    assert kind_of(primary, hierarchy) is LeftOut.NOT_A_KIND


@pytest.mark.parametrize(
    ("primary", "hierarchy"),
    [
        # A shop that sells equipment for sport stands under shopping.
        ("fitness_exercise_store", ("shopping", "specialty_store", "sporting_goods_store")),
        ("restaurant", (FOOD, "restaurant")),
        ("italian_restaurant", (FOOD, "restaurant", "italian_restaurant")),
        # A nightclub stands under the arts and entertainment.
        ("dance_club", ("arts_and_entertainment", "nightlife_venue", "dance_club")),
        ("martial_arts_club", ("sports_and_recreation", "sport_or_recreation_club")),
        ("park", ("sports_and_recreation", "park")),
        ("sports_and_recreation", ("sports_and_recreation",)),
        (FOOD, (FOOD,)),
        ("health_and_wellness_club", ("lifestyle_services", "wellness_service")),
    ],
)
def test_a_category_of_no_branch_that_is_read_is_passed_by_and_stops_nothing(
    primary: str, hierarchy: tuple[str, ...]
):
    assert kind_of(primary, (*hierarchy, primary)) is LeftOut.NOT_OF_THE_TABLE


def test_a_record_with_no_category_is_left_out_and_is_no_kind():
    assert kind_of(None, ()) is LeftOut.NO_CATEGORY
    assert kind_of("", ()) is LeftOut.NO_CATEGORY


@pytest.mark.parametrize("parent", sorted(READ_UNDER))
def test_a_category_under_a_branch_that_is_read_that_the_table_does_not_hold_stops_the_build(
    parent: str,
):
    """It is never counted by a guess and never dropped by one: a person says what it is."""
    with pytest.raises(NotOnTheTable) as stopped:
        kind_of("zzyzx_parva_venue", ("top", parent, "zzyzx_parva_venue"))
    assert "zzyzx" not in str(stopped.value)


def test_a_new_kind_of_bar_or_of_studio_stops_the_build():
    for path in (BAR, (*BAR, "pub"), STUDIO, (*EATERY, "cafe"), (*NO_ALCOHOL, "coffee_shop")):
        with pytest.raises(NotOnTheTable):
            kind_of("zzyzx_parva_room", (*path, "zzyzx_parva_room"))


def test_every_kind_stands_under_a_branch_that_is_read():
    """So a category that arrives under the same parent as a kind is never passed by."""
    assert sorted(READ_UNDER) == sorted({*PARENTS, FACILITY})
    assert sorted(READ_UNDER) == [
        "alcoholic_beverage_venue",
        "casual_eatery",
        "non_alcoholic_beverage_venue",
        "sport_or_fitness_facility",
    ]


def test_nothing_of_a_name_is_handed_to_the_rule():
    assert list(inspect.signature(kind_of).parameters) == ["primary", "hierarchy"]
    assert "name" not in {name.lower() for name in vars(venue_kinds) if name.isupper()}
