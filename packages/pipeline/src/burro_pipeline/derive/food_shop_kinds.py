"""The kinds of food shop: which of the publisher's categories is which, and which is none.

Overture Maps gives every place a category from a tree of its own. A place
has its most particular category as `taxonomy.primary`, and the path to it
from the top of the tree as `taxonomy.hierarchy`. This module is the table
that says what each category of a shop that sells food is to Burro. It reads
no file and holds no name of any place.

**A food shop is a shop where the food of an ordinary day is sold under one
roof.** Two kinds are counted: a grocer or supermarket, and a convenience
store. **The most particular category of a record decides, and nothing else
does.** No rule is made from a name: a name is not read, so nothing tells a
corner shop from a supermarket.

1. A category is a kind where the table below says so. The table is the whole
   of what counts. A grocer of one cuisine is a grocer, as the publisher files
   it.
2. A record whose most particular category is `food_and_beverage_store`, and
   no more, says a shop that sells food or drink and not which. It is left
   out.
3. Every other category of that branch is left out by its name, with the
   reason. A butcher, a fishmonger, a greengrocer and a cheese shop each sell
   one kind of food. An off-licence sells drink. A tobacconist and a shop of
   vitamins sell no food.
4. A category of the branch that is not on the table stops the build, so that
   a person says what a new category is. It is never counted and never
   dropped by a guess.

What is left out is counted, by the reason and by the category, so that a
person can see what each rule costs.

**What stands in other branches of the tree.** A baker and a delicatessen are
filed as places to eat, and the measures of places to eat count those. A
market is filed apart, and many come and go by the day. A discount store, a
department store and a warehouse club are filed as shops of many kinds of
goods, and nothing says whether food is among them. None is a record of this
branch, and none is counted.

**Where the table comes from.** The part of release 2026-09-23.0 round
London, and nothing else: the publisher's own table of categories was read as
far as its branch for health care, and the branch of shops stands after it.
So the table holds every category that the part holds under
`food_and_beverage_store`, and the two that stand beside it, and no category
that the part does not hold but one. `supermarket` is on the table and in no
record of the part: the part files a supermarket as a grocery store. No
person has looked at a sample of the records.

**The table has been held to a file.** In the part, 36 categories are the
most particular of a record of the branch or of the two beside it. 11 are a
kind, 24 are left out by name, and one is the parent.
`test_grocery_walk_on_the_real_files.py` holds the table to the part.

**What the choices are, and whose.** Each is a first choice, and the
founder's to change:

- A convenience store counts as a supermarket does. Nothing says how large a
  shop is. It is the choice that matters: with no convenience store counted,
  the order of London's areas is 0.85 the same, by the rank correlation of
  the two figures.
- A superstore is a grocer: a large shop that sells food among much else.
  The part holds 16.
- A butcher, a fishmonger and a greengrocer are not counted. With them the
  order of London's areas is 0.99 the same, and with a baker too, 0.96.
- A shop of frozen food, of health food and of imported food is not counted.
  With them the order is 0.99 the same.

Each of those was worked out once, on the part of release 2026-09-23.0, and
no test holds it.
"""

from enum import StrEnum

from burro_pipeline.derive.culture_kinds import NotOnTheTable


class Kind(StrEnum):
    """The kinds of shop that are counted, in the order a sentence lists them."""

    GROCER = "grocer"
    CONVENIENCE_STORE = "convenience_store"


class LeftOut(StrEnum):
    """Why a record is not counted. Each is counted."""

    # Its most particular category is no category of a food shop. It is most of any file.
    NOT_A_FOOD_SHOP = "not_a_food_shop"
    # The file gives it no category at all.
    NO_CATEGORY = "no_category"
    # Its most particular category is the parent of the kinds, and says no kind.
    PARENT_ALONE = "parent_alone"
    # Its category is of a shop that sells food or drink, and is none of the kinds.
    NOT_A_KIND = "not_a_kind"


KINDS = tuple(Kind)
# What the kinds are called in a sentence, together.
SAID = "a grocer, a supermarket or a convenience store"

# The branch of the publisher's tree that holds the shops that sell food or drink.
FOOD_AND_DRINK_SHOPS = "food_and_beverage_store"
# The categories that are a kind, as the publisher writes them.
IS: dict[str, Kind] = {
    # shopping > food_and_beverage_store > grocery_store, and everything under it.
    "grocery_store": Kind.GROCER,
    "asian_grocery_store": Kind.GROCER,
    "ethical_grocery_store": Kind.GROCER,
    "indian_grocery_store": Kind.GROCER,
    "international_grocery_store": Kind.GROCER,
    "korean_grocery_store": Kind.GROCER,
    "mexican_grocery_store": Kind.GROCER,
    "organic_grocery_store": Kind.GROCER,
    "russian_grocery_store": Kind.GROCER,
    # In no record of the part. It is named so that a release that writes it is counted.
    "supermarket": Kind.GROCER,
    # shopping > superstore, and shopping > convenience_store.
    "superstore": Kind.GROCER,
    "convenience_store": Kind.CONVENIENCE_STORE,
}

_ONE_KIND = "a shop that sells one kind of food, and not the food of an ordinary day"
_DRINK = "a shop that sells drink, and no food"
_NO_FOOD = "a shop that sells no food"
_SPECIAL = "a shop of special foods, and the file does not say which"
# The categories of a shop that sells food or drink that are none of the kinds, each with
# why. Every one is in a path of the part of release 2026-09-23.0 round London.
IS_NOT: dict[str, str] = {
    "butcher_shop": _ONE_KIND,
    "cheese_shop": _ONE_KIND,
    "custom_cakes_shop": _ONE_KIND,
    "dairy_store": _ONE_KIND,
    "fishmonger": _ONE_KIND,
    "frozen_foods_store": _ONE_KIND,
    "herb_and_spice_store": _ONE_KIND,
    "honey_farm_shop": _ONE_KIND,
    "olive_oil_store": _ONE_KIND,
    "pasta_store": _ONE_KIND,
    "patisserie_cake_shop": _ONE_KIND,
    "produce_store": _ONE_KIND,
    "seafood_market": _ONE_KIND,
    "beer_wine_spirits_store": _DRINK,
    "brewing_supply_store": _DRINK,
    "coffee_and_tea_supplies": _DRINK,
    "liquor_store": _DRINK,
    "water_store": _DRINK,
    "tobacco_shop": _NO_FOOD,
    "vitamin_and_supplement_store": _NO_FOOD,
    "health_food_store": _SPECIAL,
    "imported_food_store": _SPECIAL,
    "specialty_foods_store": _SPECIAL,
    "pick_your_own_farm": "a farm, and no shop",
}
# The category that stands above the kinds and says no kind.
PARENTS = frozenset({FOOD_AND_DRINK_SHOPS})
# The categories whose branch of the tree is read. A record with one of these in its path
# is a record of a food shop: its most particular category is on this table, or the build
# stops.
READ_UNDER = frozenset({FOOD_AND_DRINK_SHOPS, "convenience_store", "superstore", "supermarket"})


def kind_of(primary: str | None, hierarchy: tuple[str, ...]) -> Kind | LeftOut:
    """What a record is, by its most particular category: a kind, or why it is none.

    `hierarchy` is the path from the top of the publisher's tree to the most
    particular category. Raises `NotOnTheTable` for a category of the branch
    that the table does not hold.
    """
    if primary is None or primary == "":
        return LeftOut.NO_CATEGORY
    if primary in PARENTS:
        return LeftOut.PARENT_ALONE
    if primary in IS_NOT:
        return LeftOut.NOT_A_KIND
    kind = IS.get(primary)
    if kind is None:
        if READ_UNDER & set(hierarchy):
            raise NotOnTheTable
        return LeftOut.NOT_A_FOOD_SHOP
    return kind
