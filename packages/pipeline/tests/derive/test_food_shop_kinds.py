"""The table of kinds of food shop: which category counts, and which is left out by name.

The table reads no file, and nor do these. `test_grocery_walk_on_the_real_files.py`
holds it to the part of the real file.
"""

import re

import pytest
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.food_shop_kinds import (
    FOOD_AND_DRINK_SHOPS,
    IS,
    IS_NOT,
    KINDS,
    PARENTS,
    READ_UNDER,
    SAID,
    Kind,
    LeftOut,
    kind_of,
)

SHOPS = ("shopping", FOOD_AND_DRINK_SHOPS)
GROCER = (*SHOPS, "grocery_store")


def test_two_kinds_of_food_shop_are_counted():
    assert [kind.value for kind in KINDS] == ["grocer", "convenience_store"]
    assert {IS[category] for category in IS} == set(KINDS)
    assert SAID == "a grocer, a supermarket or a convenience store"


def test_a_grocer_of_any_cuisine_is_a_grocer_and_so_is_a_supermarket():
    grocers = sorted(category for category, kind in IS.items() if kind is Kind.GROCER)
    assert grocers == [
        "asian_grocery_store",
        "ethical_grocery_store",
        "grocery_store",
        "indian_grocery_store",
        "international_grocery_store",
        "korean_grocery_store",
        "mexican_grocery_store",
        "organic_grocery_store",
        "russian_grocery_store",
        "supermarket",
        "superstore",
    ]
    assert [c for c, kind in IS.items() if kind is Kind.CONVENIENCE_STORE] == ["convenience_store"]


@pytest.mark.parametrize(
    ("hierarchy", "found"),
    [
        (GROCER, Kind.GROCER),
        ((*GROCER, "organic_grocery_store"), Kind.GROCER),
        ((*GROCER, "korean_grocery_store"), Kind.GROCER),
        (("shopping", "superstore"), Kind.GROCER),
        (("shopping", "supermarket"), Kind.GROCER),
        (("shopping", "convenience_store"), Kind.CONVENIENCE_STORE),
        # A shop that sells food or drink, and not which.
        (SHOPS, LeftOut.PARENT_ALONE),
        # One kind of food, drink, or no food at all.
        ((*SHOPS, "butcher_shop"), LeftOut.NOT_A_KIND),
        ((*SHOPS, "fishmonger"), LeftOut.NOT_A_KIND),
        ((*SHOPS, "specialty_foods_store", "produce_store"), LeftOut.NOT_A_KIND),
        ((*SHOPS, "specialty_foods_store", "frozen_foods_store"), LeftOut.NOT_A_KIND),
        ((*SHOPS, "liquor_store"), LeftOut.NOT_A_KIND),
        ((*SHOPS, "tobacco_shop"), LeftOut.NOT_A_KIND),
        ((*SHOPS, "health_food_store"), LeftOut.NOT_A_KIND),
        # What the publisher files in another branch is no record of this one.
        (("food_and_drink", "casual_eatery", "bakery"), LeftOut.NOT_A_FOOD_SHOP),
        (("food_and_drink", "casual_eatery", "delicatessen"), LeftOut.NOT_A_FOOD_SHOP),
        (("shopping", "market", "farmers_market"), LeftOut.NOT_A_FOOD_SHOP),
        (("shopping", "discount_store"), LeftOut.NOT_A_FOOD_SHOP),
        (("shopping", "warehouse_club_store"), LeftOut.NOT_A_FOOD_SHOP),
        (("shopping", "department_store"), LeftOut.NOT_A_FOOD_SHOP),
        (("shopping",), LeftOut.NOT_A_FOOD_SHOP),
        (
            ("services_and_business", "b2b_service", "wholesaler", "wholesale_grocer"),
            LeftOut.NOT_A_FOOD_SHOP,
        ),
        (("arts_and_entertainment", "museum"), LeftOut.NOT_A_FOOD_SHOP),
    ],
)
def test_the_most_particular_category_of_a_record_decides(
    hierarchy: tuple[str, ...], found: Kind | LeftOut
):
    assert kind_of(hierarchy[-1], hierarchy) is found


@pytest.mark.parametrize("primary", [None, ""])
def test_a_record_with_no_category_is_counted_as_one(primary: str | None):
    assert kind_of(primary, ()) is LeftOut.NO_CATEGORY


@pytest.mark.parametrize(
    "hierarchy",
    [
        (*SHOPS, "halal_butcher_shop"),
        (*GROCER, "welsh_grocery_store"),
        (*SHOPS, "specialty_foods_store", "egg_store"),
        ("shopping", "convenience_store", "petrol_station_shop"),
        ("shopping", "superstore", "hypermarket"),
        # A category that is filed under the branch in a release to come, wherever it stood.
        (*SHOPS, "bakery"),
    ],
)
def test_a_new_category_of_the_branch_stops_the_build(hierarchy: tuple[str, ...]):
    """It is never counted and never dropped by a guess: a person says what it is."""
    with pytest.raises(NotOnTheTable):
        kind_of(hierarchy[-1], hierarchy)


def test_every_category_that_is_left_out_by_its_name_says_why_in_plain_words():
    assert not set(IS_NOT) & (set(IS) | PARENTS)
    assert not set(IS) & PARENTS
    for category, why in IS_NOT.items():
        assert re.fullmatch(r"[a-z][a-z0-9_]*", category), category
        assert why and why[0].islower() and not why.endswith(".") and "!" not in why
    assert "one kind of food" in IS_NOT["butcher_shop"]
    assert "drink" in IS_NOT["liquor_store"]


def test_the_branch_that_is_read_holds_every_kind():
    assert {FOOD_AND_DRINK_SHOPS} == PARENTS
    assert {FOOD_AND_DRINK_SHOPS, "convenience_store", "superstore", "supermarket"} == READ_UNDER
    # Each kind stands under the branch, or is itself a category that is read under.
    assert {"convenience_store", "superstore", "supermarket"} <= set(IS)


RESIDENT_WORDS = re.compile(
    r"\b(residents?|people|population|households?|famil(y|ies)|ages?|incomes?)\b", re.I
)


def test_no_word_of_the_table_describes_who_lives_somewhere_or_names_a_business():
    said = [SAID, *IS_NOT.values(), *IS, *IS_NOT, *(kind.value for kind in KINDS)]
    assert [one for one in said if RESIDENT_WORDS.search(one.replace("_", " "))] == []
