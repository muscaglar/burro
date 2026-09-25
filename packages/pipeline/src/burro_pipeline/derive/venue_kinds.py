"""Cafes, gyms and pubs: which of the publisher's categories is which, and which is none.

Overture Maps gives every place a category from a tree of its own, which
`culture_kinds.py` describes. This module is the table that says which
category is a cafe, which a gym and which a pub or a bar. It reads no file and
holds no name of any place.

Three kinds are counted. **The most particular category of a record decides,
and nothing else does.** No rule is made from a name: a name is not read.

| Kind | What counts |
|---|---|
| A cafe | A cafe, a coffee shop and a tea room |
| A gym | A gym, a fitness studio of any kind, and a sport or fitness facility |
| A pub or a bar | A pub, a gastropub, a beer garden, and a bar of any kind but two |

What does not count, though it stands beside one that does:

- No cafe: an internet cafe, a bakery, a sandwich shop, a bubble tea shop, a
  juice bar and a place that roasts coffee.
- No gym: a trainer, who has no premises, a gymnastics centre, a dance studio,
  a martial arts club, a pool, a court, a pitch and a climbing wall.
- No pub and no bar: a bar for smoking, a lounge, a brewery, a distillery, a
  winery and a nightclub.

1. A category is a kind where the table below says so. The table is the whole
   of what counts.
2. The publisher has a category for a sport or fitness facility, which stands
   above the gym and the studio. A record that says no more than that is
   counted as a gym: it is a leisure centre or a sports centre, and the file
   cannot say which.
3. A record whose most particular category stands above the cafes or above
   the bars, and says no kind, is left out.
4. Every other category under a branch that is read is left out by its name,
   with the reason.
5. A category under a branch that is read, and on no table, stops the build,
   so that a person says what a new category is. It is never counted and
   never dropped by a guess.

**The branches that are read** are the four that stand straight above a kind:
places that serve alcohol, casual places to eat, places that serve drinks with
no alcohol, and sport or fitness facilities. A restaurant is of none of them,
and is passed by: the places to eat and drink are counted from the food
hygiene register. A shop that sells equipment for sport stands under
shopping, and is passed by too.

**A nightclub is not counted.** The publisher files it under the arts and
entertainment, where `culture_kinds.py` leaves it out by its name.

**Where the table comes from.** It was written from the part of release
2026-09-23.0 round London, and from no page of the publisher's: each category
is one that stands in the path of a record of the part. A category that the
publisher's tree holds and the part does not is on no table, and stops a
build on the day a file holds it. `test_venues_on_the_real_files.py` holds the
table to the part. No person has looked at a sample of the records, so
nothing says how many records of a kind are what their category says.

**What the choices are, and whose.** Which category is which kind is a choice,
and each is written beside its category. They are the founder's to change:

- A tea room is a cafe. A Hong Kong style cafe is one too, as the publisher
  files it.
- A boxing gym is a gym, and a class for boxing is not: it is a class in one
  sport, as a martial arts club is.
- A bar in a hotel is a bar. A shisha bar and a cigar bar are places to
  smoke, and are not counted.
- A lounge is not counted: the word says a room, and not what is served in it.
"""

from enum import StrEnum

from burro_pipeline.derive.culture_kinds import NotOnTheTable


class Kind(StrEnum):
    """The three kinds that are counted, in the order a build lists them."""

    CAFE = "cafe"
    GYM = "gym"
    PUB = "pub"


class LeftOut(StrEnum):
    """Why a record is not counted. Each is counted."""

    # Its most particular category is under no branch that is read. It is most of any file.
    NOT_OF_THE_TABLE = "not_of_the_table"
    # The file gives it no category at all.
    NO_CATEGORY = "no_category"
    # Its most particular category stands above a kind, and says no kind.
    PARENT_ALONE = "parent_alone"
    # Its category is under a branch that is read, and is none of the three.
    NOT_A_KIND = "not_a_kind"


KINDS = tuple(Kind)
# What a kind is called in a sentence, one and many.
WORDS: dict[Kind, tuple[str, str]] = {
    Kind.CAFE: ("cafe", "cafes"),
    Kind.GYM: ("gym", "gyms"),
    Kind.PUB: ("pub or bar", "pubs and bars"),
}

# The categories that are a kind, as the publisher writes them.
IS: dict[str, Kind] = {
    # food_and_drink > casual_eatery > cafe, and one under it.
    "cafe": Kind.CAFE,
    "hong_kong_style_cafe": Kind.CAFE,
    # food_and_drink > non_alcoholic_beverage_venue.
    "coffee_shop": Kind.CAFE,
    "tea_room": Kind.CAFE,
    # sports_and_recreation > sport_or_fitness_facility, which says no more.
    "sport_or_fitness_facility": Kind.GYM,
    "gym": Kind.GYM,
    "boxing_gym": Kind.GYM,
    # sport_or_fitness_facility > fitness_studio, and everything under it.
    "fitness_studio": Kind.GYM,
    "barre_class": Kind.GYM,
    "boot_camp": Kind.GYM,
    "pilates_studio": Kind.GYM,
    "qi_gong_studio": Kind.GYM,
    "tai_chi_studio": Kind.GYM,
    "yoga_studio": Kind.GYM,
    # Two classes that the publisher files beside the studio.
    "cardio_class": Kind.GYM,
    "cycling_class": Kind.GYM,
    # food_and_drink > alcoholic_beverage_venue > bar, and what stands under it.
    "bar": Kind.PUB,
    "beer_bar": Kind.PUB,
    "champagne_bar": Kind.PUB,
    "cocktail_bar": Kind.PUB,
    "dive_bar": Kind.PUB,
    "gay_bar": Kind.PUB,
    "hotel_bar": Kind.PUB,
    "piano_bar": Kind.PUB,
    "sake_bar": Kind.PUB,
    "speakeasy": Kind.PUB,
    "sports_bar": Kind.PUB,
    "tiki_bar": Kind.PUB,
    "whiskey_bar": Kind.PUB,
    "wine_bar": Kind.PUB,
    "pub": Kind.PUB,
    "irish_pub": Kind.PUB,
    # food_and_drink > alcoholic_beverage_venue > beer_garden.
    "beer_garden": Kind.PUB,
    # food_and_drink > casual_eatery > gastropub.
    "gastropub": Kind.PUB,
}

_TO_SMOKE = "a place to smoke, which may serve no drink"
_A_MAKER = "a place where drink is made, which may serve none"
_A_SHOP = "a shop that sells food to take away, and no place to sit with a drink"
_TO_EAT = "a place to eat, which the places to eat and drink count"
_A_DRINK = "a shop that sells one kind of drink, and no cafe"
# The categories of food and of drink that stand under a branch that is read and are none
# of the three, each with why.
OF_FOOD_AND_DRINK: dict[str, str] = {
    # Under alcoholic_beverage_venue.
    "cigar_bar": _TO_SMOKE,
    "hookah_bar": _TO_SMOKE,
    "lounge": "a room, which does not say what is served in it",
    "airport_lounge": "a room at an airport, for those who fly",
    "brewery": _A_MAKER,
    "distillery": _A_MAKER,
    "winery": _A_MAKER,
    "wine_tasting_room": _A_MAKER,
    # Under cafe and under coffee_shop.
    "internet_cafe": "a place to use a computer",
    "coffee_roastery": "a place that roasts coffee, which may sell none by the cup",
    # Under non_alcoholic_beverage_venue, beside the coffee shop.
    "bubble_tea_shop": _A_DRINK,
    "milk_bar": _A_DRINK,
    "smoothie_juice_bar": _A_DRINK,
    # Under casual_eatery, beside the cafe.
    "bagel_shop": _A_SHOP,
    "bakery": _A_SHOP,
    "flatbread_shop": _A_SHOP,
    "macaron_shop": _A_SHOP,
    "candy_store": _A_SHOP,
    "chocolatier": _A_SHOP,
    "indian_sweets_shop": _A_SHOP,
    "japanese_confectionery_shop": _A_SHOP,
    "delicatessen": _A_SHOP,
    "dessert_shop": _A_SHOP,
    "cupcake_shop": _A_SHOP,
    "donut_shop": _A_SHOP,
    "frozen_yogurt_shop": _A_SHOP,
    "gelato_shop": _A_SHOP,
    "ice_cream_shop": _A_SHOP,
    "pie_shop": _A_SHOP,
    "shaved_ice_shop": _A_SHOP,
    "popcorn_shop": _A_SHOP,
    "sandwich_shop": _A_SHOP,
    "food_truck_stand": "a van or a stall, which has no place of its own",
    "bistro": _TO_EAT,
    "diner": _TO_EAT,
    "fast_food_restaurant": _TO_EAT,
    "fondue_restaurant": _TO_EAT,
    "food_court": _TO_EAT,
    "tapas_bar": _TO_EAT,
}

_A_PERSON = "a person who teaches, who may have no premises"
_ONE_SPORT = "a place for one sport, and no gym"
_A_GROUND = "a court, a pitch or a course, and no gym"
_FOR_A_DAY_OUT = "a place for a day out, and no gym"
_ON_WATER = "a place for a sport on water, and no gym"
# The categories of sport that stand under the sport or fitness facility and are no gym,
# each with why.
OF_SPORT: dict[str, str] = {
    "fitness_trainer": _A_PERSON,
    "golf_instructor": _A_PERSON,
    "swimming_instructor": _A_PERSON,
    "scuba_diving_instruction": _A_PERSON,
    "diving_instruction": _A_PERSON,
    "horseback_riding_service": _A_PERSON,
    "ski_and_snowboard_school": _A_PERSON,
    "gymnastics_center": "a hall for gymnastics, which is most often a club for children",
    "dance_studio": "a school of dance",
    "boxing_class": "a class in one sport, as a martial arts club is",
    "self_defense_class": "a class in one sport, as a martial arts club is",
    "swimming_pool": "a pool, which may have no gym",
    "adventure_sport": _ONE_SPORT,
    "climbing_service": _ONE_SPORT,
    "rock_climbing_spot": _ONE_SPORT,
    "rock_climbing_gym": "a climbing wall",
    "adventure_sports_center": _FOR_A_DAY_OUT,
    "atv_recreation_park": _FOR_A_DAY_OUT,
    "bowling_alley": _FOR_A_DAY_OUT,
    "indoor_playcenter": "a place for children to play",
    "laser_tag": _FOR_A_DAY_OUT,
    "miniature_golf_course": _FOR_A_DAY_OUT,
    "paintball": _FOR_A_DAY_OUT,
    "pool_billiards": _FOR_A_DAY_OUT,
    "pool_hall": _FOR_A_DAY_OUT,
    "diving_center": _ON_WATER,
    "scuba_diving_center": _ON_WATER,
    "paddleboarding_center": _ON_WATER,
    "kiteboarding": _ON_WATER,
    "water_sport": _ON_WATER,
    "fishing": _ON_WATER,
    "fishing_charter": _ON_WATER,
    "rafting_kayaking_area": _ON_WATER,
    "sailing_area": _ON_WATER,
    "surfing": _ON_WATER,
    "golf_course": _A_GROUND,
    "driving_range": _A_GROUND,
    "hang_gliding_center": _ONE_SPORT,
    "sky_diving": _ONE_SPORT,
    "horse_riding": _ONE_SPORT,
    "equestrian_facility": _ONE_SPORT,
    "race_track": _A_GROUND,
    "go_kart_track": _A_GROUND,
    "horse_racing_track": _A_GROUND,
    "shooting_range": _ONE_SPORT,
    "archery_range": _ONE_SPORT,
    "skate_park": _A_GROUND,
    "skating_rink": _A_GROUND,
    "ice_skating_rink": _A_GROUND,
    "roller_skating_rink": _A_GROUND,
    "sport_court": _A_GROUND,
    "badminton_court": _A_GROUND,
    "basketball_court": _A_GROUND,
    "racquetball_court": _A_GROUND,
    "squash_court": _A_GROUND,
    "tennis_court": _A_GROUND,
    "volleyball_court": _A_GROUND,
    "sport_field": _A_GROUND,
    "airsoft_field": _A_GROUND,
    "baseball_field": _A_GROUND,
    "disc_golf_course": _A_GROUND,
    "hockey_field": _A_GROUND,
    "rugby_pitch": _A_GROUND,
    "soccer_field": _A_GROUND,
}
# Every category that is left out by its name, with why.
IS_NOT: dict[str, str] = {**OF_FOOD_AND_DRINK, **OF_SPORT}

# The branch of sport, which is a kind where a record says no more.
FACILITY = "sport_or_fitness_facility"
# The categories that stand above the cafes and the bars and say no kind. A record whose
# most particular category is one of these is left out.
PARENTS = frozenset({"alcoholic_beverage_venue", "casual_eatery", "non_alcoholic_beverage_venue"})
# The categories whose branch of the tree is read. A record with one of these in its path
# is a record of the table: its most particular category is on it, or the build stops.
READ_UNDER = PARENTS | {FACILITY}


def kind_of(primary: str | None, hierarchy: tuple[str, ...]) -> Kind | LeftOut:
    """What a record is, by its most particular category: a kind, or why it is none.

    `hierarchy` is the path from the top of the publisher's tree to the most
    particular category. Raises `NotOnTheTable` for a category under a branch
    that is read that the table does not hold.
    """
    if primary is None or primary == "":
        return LeftOut.NO_CATEGORY
    kind = IS.get(primary)
    if kind is not None:
        return kind
    if primary in PARENTS:
        return LeftOut.PARENT_ALONE
    if primary in IS_NOT:
        return LeftOut.NOT_A_KIND
    if READ_UNDER & set(hierarchy):
        raise NotOnTheTable
    return LeftOut.NOT_OF_THE_TABLE
