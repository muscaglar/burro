import re

import pytest
from burro_core.catalogue import (
    CENSUS_SAID,
    CHAINS,
    COMMON_CANNOT_SEE,
    COUNTS_RESIDENTS,
    DISTANCE,
    FAMILIES,
    FEATURES,
    GRITTY,
    HOLDS_RESIDENTS,
    KINDS_OF_CHAIN,
    MIXED_WORDS,
    NEAR_A_STATION,
    NEARBY,
    NEAREST_WITHIN_M,
    NEVER_A_TRADE_OFF,
    NUISANCES,
    ON_CONSERVATION_AREAS,
    PLACED_ONLY_WITH,
    RANKED_AS,
    ROUGH_GUIDE,
    ROUGH_GUIDES,
    SHOWN_BESIDE_THE_MIX,
    TAGS,
    TIERS,
    TRAFFIC_WITHIN_M,
    WHY_A_ROUGH_GUIDE,
    WITHIN_M,
    Chain,
    RoughGuide,
    Tag,
    TagTerm,
    band_of,
    checked_floors,
    checked_recipe,
    default_direction,
    direction_allowed,
    of_a_tier,
    percentile_of,
    rough_guides,
    says_rough,
    tag_raw,
    tags_of,
)
from burro_core.ids import (
    Describes,
    Dimension,
    Direction,
    Family,
    FeatureId,
    FeatureKind,
    GrittyVariant,
    Method,
    NativeResolution,
    Polarity,
    Sureness,
    TagId,
    TagShape,
    Tenure,
    TermReading,
    Toward,
)
from burro_core.ops import TagEdit, WeightEdit
from burro_core.spec import FeatureWeight, default_spec
from pydantic import ValidationError

from .support import documents, draws

# Words for who lives somewhere. None may appear in anything a user can rank on, but for
# the four measures of age and of households and the two vibes that hold one, which say
# who is counted because they must (ADR 0006, as amended on 2026-09-24).
RESIDENT_WORDS = (
    r"residents?|people|population|households?|famil(?:y|ies)|students?|tenure|tenants?|"
    r"owners?|ages?|aged|young|old|elderly|child(?:ren)?|kids?|ethnic\w*|rac(?:e|ial)|"
    r"religio\w*|faith|born|birth|languages?|gender|sex\w*|disab\w*|health|incomes?|"
    r"depriv\w*|poor|rich|wealth\w*|class|migrants?|immigra\w*|nationalit\w*"
)
# "per 1,000 residents" is the denominator of a crime rate, which is how a rate
# is written down. It describes the place's recorded crime, not who lives there.
# "Built age" is the id of a vibe, and "Age of buildings" its name: each is the age of
# buildings, and says so.
ALLOWED = ("per 1,000 residents a year", "family amenities", "built age", "age of buildings")
# The name of transport noise says whose share it is, because its file counts who is exposed
# and gives no count of homes. It is a measure of the place: how loud it is where people
# live. It is let through as the whole of a name and as no part of one, so a word more or a
# word less is refused as any other name is. Decided on 2026-09-24 (ADR 0006).
NOISE_LABEL = "Share of residents exposed to 55 dB or more of transport noise"
RESIDENTS = re.compile(rf"\b(?:{RESIDENT_WORDS})\b", re.IGNORECASE)
# What was not decided on. It is every word of `RESIDENT_WORDS` that is no word for age or
# for households, and seven more. No name that counts residents may hold one, so a vibe
# that counts households can never be named for a faith, a nation or a class.
NOT_DECIDED_ON = re.compile(
    r"\b(?:ethnic\w*|rac(?:e|ial)|religio\w*|faith|born|birth|languages?|gender|sex\w*|"
    r"disab\w*|health|incomes?|depriv\w*|poor|rich|wealth\w*|class|migrants?|immigra\w*|"
    r"nationalit\w*|students?|tenure|tenants?|owners?|married|marriage|partnership|"
    r"cohabiting|lone parents?|employed|qualifications?)\b",
    re.IGNORECASE,
)
# The four measures that say who lived in an area, by id and by name, letter for letter.
THE_FOUR = {
    FeatureId.RESIDENTS_AGED_20_34: (
        "Residents aged 20 to 34 as a share of all residents, Census 2021"
    ),
    FeatureId.RESIDENTS_AGED_65_OVER: (
        "Residents aged 65 and over as a share of all residents, Census 2021"
    ),
    FeatureId.HOUSEHOLDS_DEPENDENT_CHILDREN: (
        "Households with dependent children as a share of all households, Census 2021"
    ),
    FeatureId.HOUSEHOLDS_ONE_PERSON: (
        "Households of one person as a share of all households, Census 2021"
    ),
}


def names_residents(text: str) -> bool:
    if text == NOISE_LABEL:
        return False
    # An id is written with underscores, which would hide a word from `\b`.
    lowered = text.lower().replace("_", " ")
    for phrase in ALLOWED:
        lowered = lowered.replace(phrase, "")
    return RESIDENTS.search(lowered) is not None


def test_nothing_describes_residents_but_the_four_measures_and_the_two_vibes_that_hold_one():
    definitions = [m["definition"] for m in documents()["catalogue.json"]["metrics"]]
    places = [f for f in FEATURES.values() if f.feature_id not in COUNTS_RESIDENTS]
    of_places = [t for t in TAGS.values() if t.tag_id not in HOLDS_RESIDENTS]
    texts = [
        # The name of a feature is held alone, so that the one name that is let through
        # is let through as the whole of a name and hides nothing that stands beside it.
        *(f.label for f in places),
        *(f"{f.feature_id} {f.short_label} {f.unit} {f.higher} {f.lower}" for f in places),
        *(
            f"{t.tag_id} {t.label} {t.short_label} {t.meaning} {t.low_end} {t.high_end} "
            f"{t.shelf_word}"
            for t in of_places
        ),
        *(line for t in of_places for line in t.cannot_see),
        *MIXED_WORDS,
        *(label for family, label in FAMILIES.items() if family is not Family.WHO_LIVES_THERE),
        *definitions,
    ]
    assert [t for t in texts if names_residents(t)] == []
    # What is left out of the search is the four, the two vibes and the group they stand in.
    assert set(THE_FOUR) == COUNTS_RESIDENTS
    assert {TagId.FAMILY_AREA, TagId.YOUNG_PROFESSIONALS} == HOLDS_RESIDENTS
    assert {member.value for member in Describes} == {"place", "buildings", "events", "residents"}


def test_the_measures_that_say_who_lived_somewhere_are_these_four_and_each_says_so():
    """Decided on 2026-09-24: age and what households are made of, and nothing else.

    Each name says who is counted and in which census. Each is a share in 100, so that a
    release holds no count of people. A person may ask for more of what one counts and
    never for fewer, and two areas are never said to be alike for who lives in them.
    """
    found = {f: feature for f, feature in FEATURES.items() if f in COUNTS_RESIDENTS}
    assert {f: feature.label for f, feature in found.items()} == THE_FOUR
    assert {f for f, feature in FEATURES.items() if feature.describes == "residents"} == set(found)
    for feature in found.values():
        assert feature.label.endswith(f", {CENSUS_SAID}") and CENSUS_SAID == "Census 2021"
        assert (feature.unit, feature.polarity) == ("%", Polarity.MORE)
        assert (feature.kind, feature.dimension) == (FeatureKind.RESIDENTS, Dimension.RESIDENTS)
        assert feature.family is Family.WHO_LIVES_THERE
        assert feature.in_likeness is False
        assert feature.short_label.startswith("More ")
        assert feature.short_label in {
            "More young adults",
            "More older residents",
            "More households with children",
            "More households of one person",
        }
        assert (feature.higher, feature.lower) == ("more", "fewer")
        assert direction_allowed(feature.feature_id, Direction.MORE)
        assert not direction_allowed(feature.feature_id, Direction.LESS)
    # No other feature is of that kind, and none of the four is weighed until it is asked for.
    assert {f for f, feature in FEATURES.items() if feature.kind == "residents"} == set(found)
    for tenure in Tenure:
        assert not {weight.feature_id for weight in default_spec(tenure).weights} & set(found)


def test_no_name_that_counts_residents_holds_a_word_for_what_was_not_decided_on():
    said = [
        *(
            f"{f.feature_id} {f.label} {f.short_label}"
            for f in FEATURES.values()
            if f.feature_id in COUNTS_RESIDENTS
        ),
        *(
            f"{t.tag_id} {t.label} {t.meaning} {t.shelf_word} {' '.join(t.cannot_see)}"
            for t in TAGS.values()
            if t.tag_id in HOLDS_RESIDENTS
        ),
        FAMILIES[Family.WHO_LIVES_THERE],
    ]
    # What a vibe cannot see may say so: "Who is a student" is what it does not count.
    cannot_see = "Who is a student."
    found = [text for text in said if NOT_DECIDED_ON.search(text.replace("_", " "))]
    assert [NOT_DECIDED_ON.findall(text.replace(cannot_see, "")) for text in found] == [[]]
    assert cannot_see in TAGS[TagId.YOUNG_PROFESSIONALS].cannot_see
    for text in ("Muslim families", "Households by ethnic group", "Wealthy retirees"):
        assert NOT_DECIDED_ON.search(text) or names_residents(text)


@pytest.mark.parametrize(
    "text",
    [
        "student_share",
        "Share of residents aged 20 to 24",
        "Households with children",
        "median_age",
        "Share of the population exposed to transport noise",
        # What was not decided on, said beside what was.
        "Residents aged 20 to 34 by ethnic group",
        "Households of lone parents",
        "Residents born abroad",
        "Students as a share of all residents",
    ],
)
def test_the_denylist_would_catch_a_feature_that_describes_residents(text: str):
    assert names_residents(text)
    # None is a name of the four, so none is let through as one.
    assert text not in THE_FOUR.values()


@pytest.mark.parametrize(
    "text",
    [
        # The name with one thing about it changed: the level, the noise, the verb, the
        # word for who, a word more, a word less.
        "Share of residents exposed to 65 dB or more of transport noise",
        "Share of residents exposed to 55 dB or more of noise",
        "Share of residents exposed to 55 dB or more of aircraft noise",
        "Share of residents exposed to 55 dB or more of transport noise at night",
        "Share of residents who report 55 dB or more of transport noise",
        "Share of older residents exposed to 55 dB or more of transport noise",
        "Share of residents aged 65 exposed to 55 dB or more of transport noise",
        "Share of households exposed to 55 dB or more of transport noise",
        "Share of people exposed to 55 dB or more of transport noise",
        "Share of residents exposed to transport noise",
        "Residents exposed to 55 dB or more of transport noise",
        "Share of residents",
        "residents",
        # The name said twice hides nothing that stands between.
        f"{NOISE_LABEL} and share of residents who rent. {NOISE_LABEL}",
        # Every other name of the catalogue, were it to say residents.
        "Share of residents within 100 m of a main road",
        "Share of residents within a 10-minute walk of a high street or town centre",
        "Places to eat and drink for each 1,000 residents",
        "Residents per hectare",
    ],
)
def test_the_guard_lets_the_one_name_of_transport_noise_through_and_refuses_every_other(
    text: str,
):
    assert not names_residents(NOISE_LABEL)
    assert names_residents(text)
    # It is the name as it is written, and no other spelling of it.
    assert names_residents(NOISE_LABEL.upper()) and names_residents(f" {NOISE_LABEL}")


def test_transport_noise_is_the_one_name_of_a_measure_of_the_place_that_says_residents():
    who = re.compile(r"\bresidents?\b", re.IGNORECASE)
    said = [
        feature.feature_id
        for feature in FEATURES.values()
        if who.search(f"{feature.label} {feature.short_label}")
        and feature.feature_id not in COUNTS_RESIDENTS
    ]
    assert said == [FeatureId.NOISE_EXPOSURE]
    assert not any(
        who.search(f"{tag.label} {tag.short_label} {tag.meaning}")
        for tag in TAGS.values()
        if tag.tag_id not in HOLDS_RESIDENTS
    )
    # Its short label, and the words that compare two areas, say nothing of who.
    noise = FEATURES[FeatureId.NOISE_EXPOSURE]
    assert not names_residents(f"{noise.short_label} {noise.higher} {noise.lower} {noise.unit}")


def test_public_parks_and_gardens_are_never_named_green_space_or_said_to_be_greener():
    """The figure counts the sites its publisher maps as a public park or garden, and no other.

    Its licence registry asks that they are never described as all green space. So no
    word of the measure says green: not its name, not the wish, and not the word that
    says an area has more of it than another.
    """
    parks = FEATURES[FeatureId.GREEN_COVER]
    assert parks.label == "Public parks and gardens as a share of the area"
    assert parks.short_label == "More public parks and gardens"
    assert (parks.higher, parks.lower) == ("more", "less")
    said = f"{parks.label} {parks.short_label} {parks.higher} {parks.lower}".lower()
    assert "green" not in said
    assert (parks.unit, parks.polarity, parks.kind) == ("%", Polarity.MORE, FeatureKind.AMENITY)


@pytest.mark.parametrize(
    ("feature_id", "least"),
    [(FeatureId.PARK_PROXIMITY, 2), (FeatureId.PARK_LARGE_PROXIMITY, 20)],
)
def test_the_distance_to_a_park_is_named_a_straight_line_and_never_a_walk(
    feature_id: FeatureId, least: int
):
    """No network of streets is built, so the distance is across whatever lies between.

    The name says so, and says what it is measured to: a way in that the publisher
    marks. It becomes a walk on the day a walk is worked out, and not before.
    """
    park = FEATURES[feature_id]
    assert park.label == (
        f"Straight-line distance to the nearest marked way into a park of {least} ha or more"
    )
    assert "walk" not in park.label.lower()
    assert park.native_resolution.value == "point"
    assert (park.unit, park.polarity, park.kind) == ("m", Polarity.LESS, FeatureKind.AMENITY)
    assert (park.higher, park.lower) == ("further", "closer")


def test_transport_noise_is_named_a_share_of_residents_and_never_a_share_of_homes():
    """Its file counts who is exposed, and gives no count of homes. So the name says residents.

    It is a measure of the place: how loud it is where people live. It says nothing of
    who they are. The guard on names lets this one name through, whole, and no other.
    """
    noise = FEATURES[FeatureId.NOISE_EXPOSURE]
    assert noise.label == NOISE_LABEL
    assert "homes" not in noise.label.lower()
    assert not names_residents(noise.label)
    assert not names_residents(f"{noise.short_label} {noise.higher} {noise.lower}")
    assert (noise.describes, noise.kind) == (Describes.PLACE, FeatureKind.NUISANCE)
    assert (noise.unit, noise.polarity) == ("%", Polarity.LESS)


def test_places_to_eat_and_drink_are_shown_as_a_count_and_ranked_on_for_each_1000_homes():
    """Decided on 2026-09-24: both figures are shown, and a wish is ranked on the second.

    The count is a true count, and on its own it says little more than that an area is
    dense and central. So it is shown and never ranked on, and whatever asks for it is
    ranked on the places for each 1,000 homes.
    """
    count = FEATURES[FeatureId.VENUE_FOOD_DRINK]
    rate = FEATURES[FeatureId.VENUE_FOOD_DRINK_PER_HOMES]
    assert (count.label, count.unit) == (
        "Places to eat and drink within 800 m of home, in a straight line",
        "count",
    )
    assert (rate.label, rate.unit) == (
        "Places to eat and drink for each 1,000 homes within 800 m, in a straight line",
        "per 1,000 homes",
    )
    # Neither is a walk, and neither is for each square kilometre.
    for feature in (count, rate):
        assert "walk" not in feature.label and "km" not in feature.unit
        assert (feature.dimension, feature.kind) == (Dimension.VENUES_CULTURE, FeatureKind.TASTE)
        assert (feature.polarity, feature.describes) == (Polarity.EITHER, Describes.PLACE)
        assert (feature.higher, feature.lower) == ("more", "fewer")
    # The plain name is the name of what a wish is ranked on.
    assert rate.short_label == "Places to eat and drink"
    assert count.short_label == "Places to eat and drink within reach"
    assert RANKED_AS[FeatureId.VENUE_FOOD_DRINK] is FeatureId.VENUE_FOOD_DRINK_PER_HOMES
    # It is new, and the catalogue holds it out of likeness.
    assert not rate.in_likeness


def test_cultural_venues_are_shown_as_a_count_and_ranked_on_for_each_1000_homes():
    """The rule of the places to eat and drink, applied alike to culture.

    The count within reach is shown. A wish for culture, and the vibe that holds it, are
    ranked on the venues for each 1,000 homes.
    """
    count = FEATURES[FeatureId.CULTURE_VENUES]
    rate = FEATURES[FeatureId.CULTURE_VENUES_PER_HOMES]
    named = "Museums, galleries, theatres, cinemas, music venues and libraries"
    assert (count.label, count.unit) == (
        f"{named} within 800 m of home, in a straight line",
        "count",
    )
    assert (rate.label, rate.unit) == (
        f"{named} for each 1,000 homes within 800 m, in a straight line",
        "per 1,000 homes",
    )
    for feature in (count, rate):
        assert "walk" not in feature.label and "km" not in feature.unit
        assert (feature.dimension, feature.kind) == (Dimension.VENUES_CULTURE, FeatureKind.AMENITY)
        assert (feature.polarity, feature.describes) == (Polarity.MORE, Describes.PLACE)
    # The plain name is the name of what a wish is ranked on.
    assert rate.short_label == "More culture nearby"
    assert count.short_label == "Cultural venues within reach"
    assert RANKED_AS[FeatureId.CULTURE_VENUES] is FeatureId.CULTURE_VENUES_PER_HOMES
    assert not rate.in_likeness


def test_no_recipe_holds_a_measure_that_is_shown_and_never_ranked_on():
    """A vibe is ranked on what a wish is ranked on, so Food and drink holds the rate."""
    assert set(RANKED_AS) == {
        FeatureId.VENUE_FOOD_DRINK,
        FeatureId.CULTURE_VENUES,
        FeatureId.VENUE_CAFE,
        FeatureId.VENUE_GYM,
        FeatureId.VENUE_EVENING,
        FeatureId.BUS_STOPS_NEARBY,
    }
    in_a_recipe = {term.feature_id for tag in TAGS.values() for term in tag.terms}
    assert not in_a_recipe & set(RANKED_AS)
    food = {term.feature_id: term.hundredths for term in TAGS[TagId.FOODIE].terms}
    assert food == {
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES: 40,
        FeatureId.INDEPENDENTS_NEARBY: 40,
        FeatureId.CUISINE_VARIETY: 20,
    }


STRAIGHT_LINES = {
    FeatureId.PLAY_SPACE_PROXIMITY: (
        "Straight-line distance to the nearest marked way into a play space",
        "m",
    ),
    FeatureId.SCHOOL_PRIMARY_NEARBY: (
        "State primary schools within 800 m in a straight line",
        "count",
    ),
    FeatureId.STATION_WALK: ("Straight-line distance to the nearest way in to a station", "m"),
    FeatureId.GROCERY_WALK: ("Straight-line distance to the nearest food shop", "m"),
    FeatureId.HIGHSTREET_ACCESS: (
        "Straight-line distance to the nearest town centre boundary",
        "m",
    ),
    FeatureId.GP_WALK: (
        "Straight-line distance to the nearest GP practice, placed by its postcode",
        "m",
    ),
    FeatureId.PHARMACY_WALK: (
        "Straight-line distance to the nearest pharmacy, placed by its postcode",
        "m",
    ),
}


@pytest.mark.parametrize("feature_id", STRAIGHT_LINES, ids=[str(f) for f in STRAIGHT_LINES])
def test_a_measure_that_is_a_straight_line_says_so_and_is_never_named_a_walk(
    feature_id: FeatureId,
):
    """No network of streets is built. A distance becomes a walk on the day one is worked out."""
    feature = FEATURES[feature_id]
    assert (feature.label, feature.unit) == STRAIGHT_LINES[feature_id]
    said = f"{feature.label} {feature.short_label}".lower()
    assert "straight" in feature.label.lower() and "walk" not in said
    assert feature.native_resolution.value == "point"
    if feature.unit == "m":
        assert (feature.polarity, feature.higher, feature.lower) == (
            Polarity.LESS,
            "further",
            "closer",
        )


def test_a_town_centre_is_never_named_a_high_street():
    """The outlines that are measured to are of town centres. The id is kept."""
    centre = FEATURES[FeatureId.HIGHSTREET_ACCESS]
    assert "high street" not in f"{centre.label} {centre.short_label}".lower()
    assert centre.short_label == "Nearer a town centre"
    # Each recipe that weighs it reads it from its near end.
    readings = [
        term.reading
        for tag in TAGS.values()
        for term in tag.terms
        if term.feature_id is FeatureId.HIGHSTREET_ACCESS
    ]
    assert readings == [TermReading.LOW, TermReading.LOW]


def test_what_was_recorded_is_counted_for_each_1000_homes_a_year():
    """It is counted from the points of the police's file, over homes and not residents."""
    damage = FEATURES[FeatureId.INCIDENT_CRIMINAL_DAMAGE]
    antisocial = FEATURES[FeatureId.INCIDENT_ANTISOCIAL]
    assert damage.label == "Recorded criminal damage and arson"
    assert antisocial.label == "Recorded anti-social behaviour"
    assert damage.unit == antisocial.unit == "per 1,000 homes a year"


def test_two_measures_take_the_name_that_says_what_the_figure_is():
    transport = FEATURES[FeatureId.LAND_TRANSPORT_OTHER]
    assert transport.label == (
        "Land used for transport other than roads, such as railways, airports and docks"
    )
    assert "depot" not in f"{transport.label} {transport.short_label}".lower()
    water = FEATURES[FeatureId.WATER_ACCESS]
    assert water.label == (
        "Share of homes within 300 m, in a straight line, of the centre line of a river, "
        "canal or lake"
    )


def test_three_measures_keep_cores_names_until_the_founder_has_decided():
    """Parks close by stays short of its recipe. The size and the shape of a town centre
    are parts of no recipe since 2026-09-25, and keep their ids and their names."""
    assert FEATURES[FeatureId.PARK_FACILITIES].label == (
        "Kinds of thing to do in parks within a 15-minute walk"
    )
    assert FEATURES[FeatureId.CENTRE_SMALL].label == (
        "Share of homes whose nearest town centre is a small one"
    )
    assert FEATURES[FeatureId.CENTRE_COMPACT].label == (
        "Share of the nearest town centre within 200 m of its middle"
    )


def test_village_feel_is_the_recipe_the_founder_chose_to_serve():
    """The second try's recipe, as it was counted. Decided on 2026-09-25 (ADR 0013)."""
    village = TAGS[TagId.VILLAGE_FEEL]
    assert [(term.hundredths, term.feature_id, term.reading) for term in village.terms] == [
        (45, FeatureId.HIGHSTREET_CONSERVED, TermReading.HIGH),
        (30, FeatureId.HOMES_DENSITY, TermReading.LOW),
        (15, FeatureId.HOMES_PRE1919, TermReading.HIGH),
        (10, FeatureId.CONSERVATION_COVER, TermReading.HIGH),
    ]
    assert (village.label, village.shape, village.family) == (
        "Village feel",
        TagShape.ONE_WAY,
        Family.STREETS_HOMES,
    )
    # It holds no part for a small or a compact centre, or for independent places: each
    # was tried, and did not help.
    tried = {FeatureId.CENTRE_SMALL, FeatureId.CENTRE_COMPACT, FeatureId.INDEPENDENTS_NEARBY}
    assert not tried & {term.feature_id for term in village.terms}
    assert not any(
        term.feature_id in (FeatureId.CENTRE_SMALL, FeatureId.CENTRE_COMPACT)
        for tag in TAGS.values()
        for term in tag.terms
    )
    # Its meaning says what it is made of, and what it cannot see what it gets wrong.
    assert village.meaning == (
        "A high street in a conservation area, homes that stand apart, period homes and "
        "protected streets"
    )
    assert village.cannot_see == (
        COMMON_CANNOT_SEE,
        "How much traffic runs along a high street.",
        "Whether the high street nearest a home is the centre of a village.",
        "Whether a park makes the homes beside it read as standing apart.",
        "Whether neighbours know each other.",
    )


def test_the_traffic_near_homes_is_a_nuisance_that_a_person_may_rank_on():
    traffic = FEATURES[FeatureId.ROAD_TRAFFIC_NEARBY]
    assert traffic.label == (
        "Traffic past the busiest count point within 500 m of home, in a straight line"
    )
    assert traffic.short_label == "Less traffic nearby"
    assert (traffic.unit, traffic.polarity, traffic.kind) == (
        "motor vehicles a day",
        Polarity.LESS,
        FeatureKind.NUISANCE,
    )
    # It is a figure of air and noise that is measured from where homes stand, so it is
    # shown with the streets and homes, as main roads are.
    assert (traffic.dimension, traffic.family) == (Dimension.AIR_NOISE, Family.STREETS_HOMES)
    # Its publisher gives an estimate, at a point on a road.
    assert (traffic.native_resolution, traffic.method) == (
        NativeResolution.POINT,
        Method.MODELLED,
    )
    assert traffic.describes is Describes.PLACE
    # The name says how near a count point stands, which is one line of the catalogue.
    assert f"within {TRAFFIC_WITHIN_M} m" in traffic.label and TRAFFIC_WITHIN_M == 500
    # No likeness counts a nuisance, and a person is ranked on the figure itself.
    assert traffic.in_likeness is False
    assert FeatureId.ROAD_TRAFFIC_NEARBY not in RANKED_AS
    assert FeatureId.ROAD_TRAFFIC_NEARBY in NUISANCES


def test_the_high_street_in_a_conservation_area_is_a_measure_of_the_place():
    street = FEATURES[FeatureId.HIGHSTREET_CONSERVED]
    assert street.label == "Share of the nearest high street that lies in a conservation area"
    assert street.short_label == "A high street in a conservation area"
    assert (street.unit, street.polarity, street.kind) == ("%", Polarity.MORE, FeatureKind.TASTE)
    assert (street.dimension, street.family) == (Dimension.HOMES, Family.STREETS_HOMES)
    assert (street.native_resolution, street.method) == (
        NativeResolution.POLYGON,
        Method.MEASURED,
    )
    assert street.describes is Describes.BUILDINGS
    # It is the heaviest part of a rough guide, so no likeness between areas counts it.
    assert street.in_likeness is False
    assert FeatureId.HIGHSTREET_CONSERVED not in RANKED_AS
    # It stands in one recipe and no other.
    holding = [
        tag.tag_id
        for tag in TAGS.values()
        if any(term.feature_id is FeatureId.HIGHSTREET_CONSERVED for term in tag.terms)
    ]
    assert holding == [TagId.VILLAGE_FEEL]


def test_village_feel_places_no_area_without_its_high_street():
    """Its other three parts are 55 in 100 of it, which is under what a band needs."""
    rest = {
        FeatureId.HOMES_DENSITY: 20.0,
        FeatureId.HOMES_PRE1919: 80.0,
        FeatureId.CONSERVATION_COVER: 80.0,
    }
    without = tag_raw(TagId.VILLAGE_FEEL, rest)
    assert (without.raw, without.coverage) == (None, 0.55)
    # With its high street and one part more it has a band, as any vibe has at 60 in 100.
    street = {FeatureId.HIGHSTREET_CONSERVED: 80.0}
    assert tag_raw(TagId.VILLAGE_FEEL, street).raw is None
    assert tag_raw(TagId.VILLAGE_FEEL, street | {FeatureId.CONSERVATION_COVER: 80.0}).raw is None
    placed = tag_raw(TagId.VILLAGE_FEEL, street | {FeatureId.HOMES_PRE1919: 80.0})
    assert (placed.raw, placed.coverage) == (0.8, 0.6)
    # Homes per hectare are read from the low end: homes that stand apart count for more.
    whole = tag_raw(TagId.VILLAGE_FEEL, street | rest)
    assert whole.coverage == 1.0
    assert whole.raw == round((45 * 0.8 + 30 * 0.8 + 15 * 0.8 + 10 * 0.8) / 100, 6)
    crowded = tag_raw(TagId.VILLAGE_FEEL, street | rest | {FeatureId.HOMES_DENSITY: 90.0})
    assert crowded.raw is not None and whole.raw is not None and crowded.raw < whole.raw


def test_no_vibe_is_held_off_today_and_the_rule_stands_for_one_that_is(
    monkeypatch: pytest.MonkeyPatch,
):
    """Village feel was held off until the founder chose to serve it, on 2026-09-25.

    Nothing is named in `PLACED_ONLY_WITH` today. What it does is kept, for a vibe that
    is held off in future: a vibe that is named there places an area only where one of
    the parts named for it has a figure, whatever else of its recipe has.
    """
    from burro_core import catalogue

    assert dict(PLACED_ONLY_WITH) == {}
    parts = {FeatureId.LAND_GARDENS: 80.0, FeatureId.GREEN_COVER: 80.0}
    assert tag_raw(TagId.LEAFY, parts).raw == 0.8
    held_off = {TagId.LEAFY: frozenset({FeatureId.LAND_WOODLAND})}
    monkeypatch.setattr(catalogue, "PLACED_ONLY_WITH", held_off)
    without = tag_raw(TagId.LEAFY, parts)
    # How much of the recipe is known is still said: it is what the sentence of the vibe says.
    assert (without.raw, without.coverage) == (None, 0.7)
    with_it = tag_raw(TagId.LEAFY, parts | {FeatureId.LAND_WOODLAND: 80.0})
    assert (with_it.raw, with_it.coverage) == (0.8, 1.0)
    # And it is held to 60 in 100 as any vibe is.
    assert tag_raw(TagId.LEAFY, {FeatureId.LAND_WOODLAND: 80.0}).raw is None
    # Any other vibe is placed as it was.
    food = {FeatureId.VENUE_FOOD_DRINK_PER_HOMES: 80.0, FeatureId.INDEPENDENTS_NEARBY: 80.0}
    assert tag_raw(TagId.FOODIE, food).raw == 0.8


# A vibe that says it is less sure than the rest


def test_a_vibe_says_whether_it_is_a_rough_guide_in_one_field_of_two_values():
    assert [member.value for member in Sureness] == ["as_the_rest", "rough_guide"]
    # A vibe that says nothing is as sure as the rest, which is what a client assumes.
    assert Tag.model_fields["sureness"].default is Sureness.AS_THE_REST
    said = {tag.tag_id: tag.sureness for tag in TAGS.values()}
    assert {tag_id for tag_id, sure in said.items() if sure is Sureness.ROUGH_GUIDE} == {
        TagId.VILLAGE_FEEL
    }
    assert set(ROUGH_GUIDES) == {TagId.VILLAGE_FEEL}
    assert all(
        sure is Sureness.AS_THE_REST for tag_id, sure in said.items() if tag_id not in ROUGH_GUIDES
    )


def test_a_rough_guide_has_one_short_label_and_one_sentence_that_says_why():
    assert ROUGH_GUIDE == "Rough guide"
    assert set(WHY_A_ROUGH_GUIDE) == ROUGH_GUIDES
    why = WHY_A_ROUGH_GUIDE[TagId.VILLAGE_FEEL]
    assert why == (
        "Of the areas it puts highest, about half read as villages to people, and it "
        "takes some busy main roads and some grand inner streets for villages."
    )
    assert says_rough(TagId.VILLAGE_FEEL) == f"Rough guide. {why}"
    for sentence in WHY_A_ROUGH_GUIDE.values():
        # One sentence, which gives no figure that a build could make false.
        assert sentence.endswith(".") and sentence.count(".") == 1
        assert not any(character.isdigit() for character in sentence)
        assert not re.search(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b", sentence)
        assert "about half" in sentence


def test_what_a_rough_guide_says_is_served_for_each_vibe_that_is_one():
    assert rough_guides(TAGS.values()) == (
        RoughGuide(
            tag_id=TagId.VILLAGE_FEEL,
            label="Rough guide",
            why=WHY_A_ROUGH_GUIDE[TagId.VILLAGE_FEEL],
        ),
    )
    others = [tag for tag in TAGS.values() if tag.tag_id is not TagId.VILLAGE_FEEL]
    assert rough_guides(others) == ()


def test_a_rough_guide_is_on_a_result_only_where_it_was_asked_for():
    """It is put on no result by itself, and leads no portrait: `strip`."""
    village = TAGS[TagId.VILLAGE_FEEL]
    assert village.strip is False and village.lens and village.table
    with pytest.raises(ValueError, match="where it is a rough guide"):
        checked_recipe(village.replace(strip=True))
    # Every vibe that is as sure as the rest, and counts nobody, may be put on a result.
    assert {tag.tag_id for tag in TAGS.values() if not tag.strip} == (
        ROUGH_GUIDES | HOLDS_RESIDENTS
    )


def test_a_rough_guide_says_why_and_a_vibe_that_is_as_sure_as_the_rest_does_not():
    leafy = TAGS[TagId.LEAFY]
    with pytest.raises(ValueError, match="says why it is a rough guide"):
        checked_recipe(leafy.replace(sureness=Sureness.ROUGH_GUIDE, strip=False))
    village = TAGS[TagId.VILLAGE_FEEL]
    with pytest.raises(ValueError, match="says why it is a rough guide"):
        checked_recipe(village.replace(sureness=Sureness.AS_THE_REST))


# The chains of grocers, gyms and coffee, as the founder decided on 2026-09-24 (ADR 0026).
FOUNDERS_CHAINS = (
    *("Waitrose", "M&S", "Whole Foods", "Sainsbury's", "Tesco", "Co-op"),
    *("Asda", "Aldi", "Lidl", "Iceland"),
    *("Equinox", "Third Space", "Barry's", "Virgin Active", "Nuffield", "Gymbox"),
    *("PureGym", "The Gym Group"),
    *("Gail's", "Ole & Steen", "Pret", "Nero", "Starbucks", "Greggs"),
)
ADDED_CHAINS = ("Morrisons", "David Lloyd", "Anytime Fitness", "Costa", "Blank Street")


def test_the_places_of_each_tier_are_counted_and_the_nearest_is_measured():
    """Nine tiers: grocers, gyms and coffee, each premium, mid-range and value."""
    assert len(SHOWN_BESIDE_THE_MIX) == 18
    assert (WITHIN_M, NEAREST_WITHIN_M) == (800, 2_000)
    for kind, (one, many) in KINDS_OF_CHAIN.items():
        for tier, said in TIERS.items():
            count = FEATURES[of_a_tier(kind, tier, NEARBY)]
            far = FEATURES[of_a_tier(kind, tier, DISTANCE)]
            assert count.label == (
                f"{said.capitalize()} {many} within 800 m of home, in a straight line, by "
                "Burro's table of tiers"
            )
            assert far.label == (
                f"Straight-line distance to the nearest {said} {one} within 2,000 m of home, "
                "by Burro's table of tiers"
            )
            assert (count.short_label, far.short_label) == (
                f"{said.capitalize()} {many} within reach",
                f"Nearer a {said} {one}",
            )
            assert (count.unit, count.polarity, count.kind) == (
                "count",
                Polarity.MORE,
                FeatureKind.AMENITY,
            )
            assert (far.unit, far.polarity, far.kind) == ("m", Polarity.LESS, FeatureKind.AMENITY)
            assert (far.higher, far.lower) == ("further", "closer")
            for feature in (count, far):
                assert feature.feature_id in SHOWN_BESIDE_THE_MIX
                assert feature.dimension is Dimension.BRANDS
                assert (feature.describes, feature.family) == (Describes.PLACE, Family.DAILY_LIFE)
                assert feature.native_resolution is NativeResolution.POINT
                assert "walk" not in f"{feature.label} {feature.short_label}".lower()
    assert set(TIERS) == {"premium", "mid", "value"}
    assert set(KINDS_OF_CHAIN) == {"grocer", "gym", "coffee"}


def test_the_mix_of_brands_is_a_measure_of_the_place_that_stands_in_no_vibe():
    """It is what a word for a smart area is first read as, and it is of which shops stand.

    It is offered and never applied from a word, it stands in no vibe, no likeness is
    counted on it, and nothing weighs it by default.
    """
    mix = FEATURES[FeatureId.BRAND_MIX]
    assert mix.label == (
        "Share of the chain grocers, gyms and coffee places within 800 m of home that are "
        "premium, with a mid-range one counted as half, by Burro's table of tiers"
    )
    assert (mix.short_label, mix.unit) == ("Mix of brands", "%")
    assert (mix.polarity, mix.kind) == (Polarity.EITHER, FeatureKind.TASTE)
    assert (mix.higher, mix.lower) == ("more premium", "less premium")
    assert (mix.describes, mix.dimension) == (Describes.PLACE, Dimension.BRANDS)
    assert not mix.in_likeness and FeatureId.BRAND_MIX not in SHOWN_BESIDE_THE_MIX
    assert FeatureId.BRAND_MIX not in {t.feature_id for tag in TAGS.values() for t in tag.terms}
    for tenure in Tenure:
        assert FeatureId.BRAND_MIX not in {w.feature_id for w in default_spec(tenure).weights}
    assert not names_residents(f"{mix.label} {mix.short_label} {mix.higher} {mix.lower}")


def test_no_likeness_is_counted_on_a_tier_a_chain_or_the_mix():
    brands = {f for f, feature in FEATURES.items() if feature.dimension is Dimension.BRANDS}
    assert brands == {*SHOWN_BESIDE_THE_MIX, FeatureId.BRAND_MIX, *CHAINS}
    assert not any(FEATURES[feature_id].in_likeness for feature_id in brands)
    assert not brands & {t.feature_id for tag in TAGS.values() for t in tag.terms}


def test_a_chain_is_named_so_that_a_person_can_ask_to_be_near_one():
    assert tuple(chain.name for chain in CHAINS.values()) == (
        *FOUNDERS_CHAINS[:6],
        "Morrisons",
        *FOUNDERS_CHAINS[6:16],
        "David Lloyd",
        "Anytime Fitness",
        *FOUNDERS_CHAINS[16:23],
        "Costa",
        "Blank Street",
        "Greggs",
    )
    assert {chain.name for chain in CHAINS.values()} == {*FOUNDERS_CHAINS, *ADDED_CHAINS}
    for feature_id, chain in CHAINS.items():
        feature = FEATURES[feature_id]
        assert feature_id.value.startswith("brand_") and chain.feature_id is feature_id
        assert feature.label == (
            f"Straight-line distance to the nearest {chain.nearest} within 2,000 m of home"
        )
        assert feature.short_label == f"Nearer {chain.one}"
        assert chain.name in chain.one and chain.name in chain.nearest
        assert (feature.unit, feature.polarity) == ("m", Polarity.LESS)
        # It is weighed only where a person asks for the chain by name.
        assert feature.kind is FeatureKind.ON_REQUEST
        # A person may ask to be near a chain, and never to be far from one.
        assert direction_allowed(feature_id, Direction.LESS)
        assert not direction_allowed(feature_id, Direction.MORE)
    assert FEATURES[FeatureId.BRAND_ALDI].short_label == "Nearer an Aldi"
    assert FEATURES[FeatureId.BRAND_THE_GYM_GROUP].short_label == "Nearer The Gym Group"


def test_core_names_a_tier_and_a_chain_and_never_says_which_chain_is_of_which_tier():
    """The table of tiers is the founder's judgement, and is data of the pipeline's."""
    assert set(Chain.model_fields) == {"feature_id", "name", "one", "nearest"}
    tiers = {said for said in TIERS.values()} | set(TIERS)
    for chain in CHAINS.values():
        said = f"{chain.feature_id} {chain.name} {chain.one} {chain.nearest}".lower()
        assert not any(tier in said.replace("-", " ").split() for tier in tiers)
        feature = FEATURES[chain.feature_id]
        assert "tier" not in feature.label and "premium" not in feature.label


def test_independent_places_are_a_share_of_the_places_within_reach_in_a_straight_line():
    """It is a part of Food and drink, and is named for what is measured. It was a part of
    Village feel until 2026-09-25."""
    independent = FEATURES[FeatureId.INDEPENDENTS_NEARBY]
    assert independent.label == (
        "Share of the places to eat and drink within 800 m of home, in a straight line, that "
        "belong to no chain"
    )
    assert (independent.short_label, independent.unit) == ("More independent places nearby", "%")
    assert (independent.polarity, independent.kind) == (Polarity.MORE, FeatureKind.TASTE)
    assert independent.native_resolution is NativeResolution.POINT
    assert "walk" not in independent.label.lower()
    held = {
        tag.tag_id: term.hundredths
        for tag in TAGS.values()
        for term in tag.terms
        if term.feature_id is FeatureId.INDEPENDENTS_NEARBY
    }
    assert held == {TagId.FOODIE: 40}


def test_what_is_shown_and_not_ranked_on_is_ranked_as_a_measure_of_the_same_kind():
    for shown, ranked in RANKED_AS.items():
        assert shown is not ranked and ranked not in RANKED_AS
        one, other = FEATURES[shown], FEATURES[ranked]
        assert (one.dimension, one.polarity, one.kind) == (
            other.dimension,
            other.polarity,
            other.kind,
        )
        assert (one.higher, one.lower) == (other.higher, other.lower)


def test_the_catalogue_holds_every_feature_and_tag_once():
    assert set(FEATURES) == set(FeatureId)
    assert set(TAGS) == set(TagId)
    assert len(FEATURES) == 114
    # Thirteen vibes, and gritty in both its variants.
    assert len(TAGS) == 15


RETIRED = (
    "buzzy",
    "evening_venues",
    "historic_character",
    "creative",
    "strong_high_street",
    "near_universities",
    "waterside",
)


@pytest.mark.parametrize("retired", RETIRED)
def test_a_retired_tag_id_names_nothing_and_is_never_used_again(retired: str):
    with pytest.raises(ValueError, match="is not a valid TagId"):
        TagId(retired)


@pytest.mark.parametrize("unknown", ["student_share", "median_age", "ethnicity", "", "tenure"])
def test_the_allowlist_refuses_an_unknown_feature_id(unknown: str):
    with pytest.raises(ValueError, match="is not a valid FeatureId"):
        FeatureId(unknown)
    with pytest.raises(ValidationError):
        FeatureWeight.model_validate(
            {"feature_id": unknown, "weight": 0.5, "direction": "more", "provenance": "stated"}
        )
    edit = {"action": "set", "value": 0.5, "step": "none", "provenance": "stated"}
    with pytest.raises(ValidationError):
        WeightEdit.model_validate(edit | {"feature_id": unknown, "direction": "default"})
    with pytest.raises(ValidationError):
        TagEdit.model_validate(edit | {"tag_id": unknown, "toward": "default"})


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_every_recipe_sums_to_a_hundred_with_two_parts_or_more_and_none_of_sixty(tag: Tag):
    assert sum(term.hundredths for term in tag.terms) == 100
    assert len(tag.terms) >= 2
    assert all(term.hundredths < 60 for term in tag.terms)
    assert len({t.feature_id for t in tag.terms}) == len(tag.terms)
    assert all(term.feature_id in FEATURES for term in tag.terms)


def term(hundredths: int, feature_id: FeatureId) -> TagTerm:
    return TagTerm(feature_id=feature_id, hundredths=hundredths, reading=TermReading.HIGH)


BROKEN_RECIPES = {
    "it sums to 99": (term(50, FeatureId.GREEN_COVER), term(49, FeatureId.LAND_GARDENS)),
    "it sums to 101": (term(50, FeatureId.GREEN_COVER), term(51, FeatureId.LAND_GARDENS)),
    "it has one part": (term(100, FeatureId.GREEN_COVER),),
    "a part is 60": (term(60, FeatureId.GREEN_COVER), term(40, FeatureId.LAND_GARDENS)),
    "a part is there twice": (
        term(40, FeatureId.GREEN_COVER),
        term(30, FeatureId.GREEN_COVER),
        term(30, FeatureId.LAND_GARDENS),
    ),
    "a part is weighed on request only": (
        term(50, FeatureId.GREEN_COVER),
        term(50, FeatureId.UNIVERSITY_PROXIMITY),
    ),
    "a part is shown and never ranked on": (
        term(50, FeatureId.GREEN_COVER),
        term(50, FeatureId.CULTURE_VENUES),
    ),
}


def family_area(**changed: object) -> Tag:
    return TAGS[TagId.FAMILY_AREA].replace(**changed)


def with_children(hundredths: int, reading: TermReading, rest: int) -> tuple[TagTerm, ...]:
    children = TagTerm(
        feature_id=FeatureId.HOUSEHOLDS_DEPENDENT_CHILDREN, hundredths=hundredths, reading=reading
    )
    return (children, term(rest, FeatureId.SCHOOL_PRIMARY_NEARBY), term(20, FeatureId.GREEN_COVER))


# A recipe that would rank towards fewer of a group of people, or be one census figure
# under a vibe's name, or not say which census it counts. Each is refused by its own rule.
BROKEN_WHERE_RESIDENTS_COUNT = {
    "reads a part that counts residents from its high end": family_area(
        terms=with_children(40, TermReading.LOW, 40)
    ),
    "holds no part that counts residents, being a scale": family_area(
        shape=TagShape.SCALE, low_end="Few", high_end="Many"
    ),
    "holds no part of more than 40 hundredths where it counts residents": family_area(
        terms=with_children(45, TermReading.HIGH, 35)
    ),
    "holds no part of more than 40 hundredths": family_area(
        terms=with_children(35, TermReading.HIGH, 45)
    ),
    "names the census in its meaning where it counts residents": family_area(
        meaning="Households with dependent children, with schools and a park nearby"
    ),
    "is on a result only where it was asked for, where it counts residents": family_area(
        strip=True
    ),
}


@pytest.mark.parametrize("rule", BROKEN_WHERE_RESIDENTS_COUNT)
def test_a_recipe_that_counts_residents_is_read_high_runs_one_way_and_is_no_one_figure(rule: str):
    with pytest.raises(ValueError, match=f"a recipe {rule}"):
        checked_recipe(BROKEN_WHERE_RESIDENTS_COUNT[rule])
    # The same recipe with no part that counts residents breaks none of these.
    places = TAGS[TagId.FAMILY_AMENITIES]
    assert checked_recipe(places) is places and TagId.FAMILY_AMENITIES not in HOLDS_RESIDENTS


@pytest.mark.parametrize("tag_id", sorted(HOLDS_RESIDENTS))
def test_a_vibe_that_counts_residents_holds_them_at_no_more_than_40_in_100(tag_id: TagId):
    tag = TAGS[tag_id]
    counted = [t for t in tag.terms if t.feature_id in COUNTS_RESIDENTS]
    assert [t.reading for t in counted] == [TermReading.HIGH]
    assert max(t.hundredths for t in tag.terms) == 40 == counted[0].hundredths
    # What is there is six in ten of it: Burro measures places first.
    assert sum(t.hundredths for t in tag.terms if t not in counted) == 60
    assert (tag.shape, tag.family) == (TagShape.ONE_WAY, Family.WHO_LIVES_THERE)
    assert CENSUS_SAID in tag.meaning and tag.shelf_word is None
    assert any("21 March 2021" in line for line in tag.cannot_see)
    # A map may be coloured by it and a comparison may hold it. No result shows it
    # unless it was asked for.
    assert (tag.lens, tag.table, tag.strip) == (True, True, False)


def test_family_area_and_family_amenities_each_say_how_they_differ():
    """Family area counts the households that hold children. Family amenities counts places.

    They are two vibes and not one: on London's areas they find different places, and a
    person can still ask for what is there without counting who lives there.
    """
    area, amenities = TAGS[TagId.FAMILY_AREA], TAGS[TagId.FAMILY_AMENITIES]
    assert {t.feature_id: (t.hundredths, t.reading) for t in area.terms} == {
        FeatureId.HOUSEHOLDS_DEPENDENT_CHILDREN: (40, TermReading.HIGH),
        FeatureId.SCHOOL_PRIMARY_NEARBY: (25, TermReading.HIGH),
        FeatureId.PLAY_SPACE_PROXIMITY: (20, TermReading.LOW),
        FeatureId.PARK_PROXIMITY: (15, TermReading.LOW),
    }
    assert {t.feature_id: (t.hundredths, t.reading) for t in amenities.terms} == {
        FeatureId.SCHOOL_PRIMARY_NEARBY: (40, TermReading.HIGH),
        FeatureId.PLAY_SPACE_PROXIMITY: (35, TermReading.LOW),
        FeatureId.PARK_PROXIMITY: (25, TermReading.LOW),
    }
    assert area.meaning.endswith("It counts who lived there beside what is there")
    assert amenities.meaning.endswith("It counts places alone")
    assert "Who lives there." in amenities.cannot_see


def test_young_professionals_counts_age_and_what_is_near_and_says_it_counts_no_work():
    young = TAGS[TagId.YOUNG_PROFESSIONALS]
    assert {t.feature_id: (t.hundredths, t.reading) for t in young.terms} == {
        FeatureId.RESIDENTS_AGED_20_34: (40, TermReading.HIGH),
        FeatureId.STATION_WALK: (25, TermReading.LOW),
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES: (20, TermReading.HIGH),
        FeatureId.CULTURE_VENUES_PER_HOMES: (15, TermReading.HIGH),
    }
    # The recipe that was proposed and not built held flats and homes per hectare, and
    # found the areas that Houses or flats finds.
    parts = {t.feature_id for t in young.terms}
    assert not parts & {t.feature_id for t in TAGS[TagId.HOMES].terms}
    assert "What anyone does for work: it counts residents by their age alone." in (
        young.cannot_see
    )


@pytest.mark.parametrize("terms", BROKEN_RECIPES.values(), ids=list(BROKEN_RECIPES))
def test_a_recipe_that_breaks_a_rule_is_refused_when_the_catalogue_is_made(
    terms: tuple[TagTerm, ...],
):
    # `TAGS` is built through this check, so a broken recipe stops the import.
    with pytest.raises(ValueError, match="recipe"):
        checked_recipe(TAGS[TagId.LEAFY].replace(terms=terms))


def test_the_check_on_a_recipe_passes_every_vibe_of_the_catalogue():
    for tag in TAGS.values():
        assert checked_recipe(tag) is tag


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_a_scale_has_two_named_ends_and_a_one_way_vibe_has_none(tag: Tag):
    if tag.shape is TagShape.SCALE:
        assert tag.low_end and tag.high_end and tag.low_end != tag.high_end
    else:
        assert tag.low_end is None and tag.high_end is None


def test_a_scale_with_an_end_missing_is_refused_and_so_is_a_one_way_vibe_with_one():
    with pytest.raises(ValueError, match="ends"):
        checked_recipe(TAGS[TagId.PACE].replace(low_end=None))
    with pytest.raises(ValueError, match="ends"):
        checked_recipe(TAGS[TagId.PACE].replace(low_end="Buzzy"))
    with pytest.raises(ValueError, match="ends"):
        checked_recipe(TAGS[TagId.LEAFY].replace(high_end="Leafy"))


def test_three_vibes_are_named_for_what_a_person_would_call_them_and_no_id_moved():
    # Decided on 2026-09-24. "Pace", "Homes" and "Built age" were the names of a recipe,
    # and nobody asks for a place by one. The ids and the ends are as they were.
    named = {tag_id: (TAGS[tag_id].label, TAGS[tag_id].short_label) for tag_id in TAGS}
    assert named[TagId.PACE] == ("Going out", "Going out")
    assert named[TagId.HOMES] == ("Houses or flats", "Houses or flats")
    assert named[TagId.BUILT_AGE] == ("Age of buildings", "Age of buildings")
    assert (TagId.PACE, TagId.HOMES, TagId.BUILT_AGE) == ("pace", "homes", "built_age")
    assert (TAGS[TagId.PACE].low_end, TAGS[TagId.PACE].high_end) == ("Calm", "Buzzy")
    # A name that says age says the age of buildings, and nothing of who lives in them.
    assert names_residents("Age of residents") and names_residents("Average age")
    assert not names_residents(TAGS[TagId.BUILT_AGE].label)


def test_what_homes_sell_for_is_a_measure_of_the_place_that_stands_in_no_vibe():
    """Decided on 2026-09-24: a person may ask for homes that sell for more than the middle.

    It is the second reading of a word for a smart area. It is a figure of what was
    paid for homes, and says nothing of who lives somewhere or of what they earn.
    """
    price = FEATURES[FeatureId.PRICE_MEDIAN]
    assert (price.label, price.short_label) == (
        "Median price paid for a home",
        "What homes sell for",
    )
    assert (price.unit, price.polarity) == ("£", Polarity.EITHER)
    assert (price.higher, price.lower) == ("dearer", "cheaper")
    assert price.native_resolution is NativeResolution.MSOA
    assert (price.kind, price.describes) == (FeatureKind.TASTE, Describes.BUILDINGS)
    assert price.dimension is Dimension.HOMES
    # No vibe rests on it, no likeness is counted on it, and nothing weighs it by default.
    in_a_recipe = {term.feature_id for tag in TAGS.values() for term in tag.terms}
    assert FeatureId.PRICE_MEDIAN not in in_a_recipe
    assert price.in_likeness is False
    for tenure in Tenure:
        assert FeatureId.PRICE_MEDIAN not in {w.feature_id for w in default_spec(tenure).weights}


def test_going_out_is_pubs_places_to_eat_and_drink_high_streets_and_culture():
    """Pubs and bars are 35 in 100 of Going out, as they were before they were held back.

    They were out while the food register was the one source of them, and the recipe was
    45, 30 and 25. They are counted from the file of places, and the shares are as they
    stood before.
    """
    going_out = TAGS[TagId.PACE]
    assert (going_out.label, going_out.low_end, going_out.high_end) == (
        "Going out",
        "Calm",
        "Buzzy",
    )
    assert {term.feature_id: (term.hundredths, term.reading) for term in going_out.terms} == {
        FeatureId.VENUE_EVENING_PER_HOMES: (35, TermReading.HIGH),
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES: (30, TermReading.HIGH),
        # A distance to a town centre, which is read from its near end.
        FeatureId.HIGHSTREET_ACCESS: (20, TermReading.LOW),
        FeatureId.CULTURE_VENUES_PER_HOMES: (15, TermReading.HIGH),
    }
    # A vibe is ranked on what a wish is ranked on: the figure for each 1,000 homes, and
    # never the count. And it no longer says that pubs are not counted.
    in_a_recipe = {term.feature_id for tag in TAGS.values() for term in tag.terms}
    assert FeatureId.VENUE_EVENING not in in_a_recipe
    assert FeatureId.VENUE_FOOD_DRINK not in in_a_recipe
    assert not any("not counted" in line for line in going_out.cannot_see)
    # No one part gives a band, and pubs with either kind of place to eat do.
    alone = tag_raw(TagId.PACE, {FeatureId.VENUE_EVENING_PER_HOMES: 80.0})
    assert (alone.coverage, alone.raw) == (0.35, None)
    two = tag_raw(
        TagId.PACE,
        {FeatureId.VENUE_EVENING_PER_HOMES: 80.0, FeatureId.VENUE_FOOD_DRINK_PER_HOMES: 40.0},
    )
    assert two.coverage == 0.65 and two.raw is not None
    # Without the pubs it still has one: the other three are 65 in 100.
    without = tag_raw(
        TagId.PACE,
        {
            FeatureId.VENUE_FOOD_DRINK_PER_HOMES: 80.0,
            FeatureId.HIGHSTREET_ACCESS: 40.0,
            FeatureId.CULTURE_VENUES_PER_HOMES: 40.0,
        },
    )
    assert without.coverage == 0.65 and without.raw is not None


def test_cafes_gyms_and_pubs_are_each_shown_as_a_count_and_ranked_on_for_each_1000_homes():
    """The rule of the places to eat and drink, applied alike to the three."""
    named = {
        FeatureId.VENUE_CAFE: ("Cafes and coffee shops", "Cafes within reach", "More cafes nearby"),
        FeatureId.VENUE_GYM: ("Gyms and fitness studios", "Gyms within reach", "More gyms nearby"),
        FeatureId.VENUE_EVENING: ("Pubs and bars", "Pubs and bars within reach", "Pubs and bars"),
    }
    for shown, (what, short, wish) in named.items():
        count, rate = FEATURES[shown], FEATURES[RANKED_AS[shown]]
        assert rate.feature_id == f"{shown}_per_homes"
        assert (count.label, count.unit) == (
            f"{what} within 800 m of home, in a straight line",
            "count",
        )
        assert (rate.label, rate.unit) == (
            f"{what} for each 1,000 homes within 800 m, in a straight line",
            "per 1,000 homes",
        )
        assert (count.short_label, rate.short_label) == (short, wish)
        for feature in (count, rate):
            assert "walk" not in feature.label and "km" not in feature.unit
            assert (feature.dimension, feature.describes) == (
                Dimension.VENUES_CULTURE,
                Describes.PLACE,
            )
        # New, and the catalogue holds it out of likeness.
        assert not rate.in_likeness
    # A person may want fewer pubs, and never fewer cafes or gyms.
    for shown in (FeatureId.VENUE_CAFE, FeatureId.VENUE_GYM):
        for feature in (FEATURES[shown], FEATURES[RANKED_AS[shown]]):
            assert (feature.polarity, feature.kind) == (Polarity.MORE, FeatureKind.AMENITY)
            assert not feature.in_likeness
    for feature_id in (FeatureId.VENUE_EVENING, FeatureId.VENUE_EVENING_PER_HOMES):
        pubs = FEATURES[feature_id]
        assert (pubs.polarity, pubs.kind) == (Polarity.EITHER, FeatureKind.TASTE)


def test_the_homes_near_a_cluster_of_pubs_are_named_for_what_is_counted():
    """The file of places cannot say how late a place is open, so no name says late."""
    near = FEATURES[FeatureId.EVENING_CLUSTER_EXPOSURE]
    assert near.label == (
        "Share of homes with three or more pubs or bars within 150 m, in a straight line"
    )
    assert near.short_label == "Away from clusters of pubs and bars"
    assert (near.unit, near.polarity, near.kind) == ("%", Polarity.LESS, FeatureKind.NUISANCE)
    quiet = TAGS[TagId.QUIET_RESIDENTIAL]
    assert (FeatureId.EVENING_CLUSTER_EXPOSURE, 30, TermReading.LOW) in [
        (term.feature_id, term.hundredths, term.reading) for term in quiet.terms
    ]
    assert "late" not in quiet.meaning and "pubs and bars" in quiet.meaning
    assert "How late a pub or a bar is open." in quiet.cannot_see


def test_traffic_is_a_part_of_quiet_streets_and_of_no_other_vibe():
    """Decided for the founder on 2026-09-25, as a first opinion for a person to adjust.

    Main roads held 40 in 100 of Quiet streets. Traffic took half of that and nothing of
    any other part: both are of the roads near a home, the one says how many homes stand
    beside a main road and the other how busy the busiest road nearby is. So roads are
    40 in 100 of the vibe, as they were.
    """
    quiet = TAGS[TagId.QUIET_RESIDENTIAL]
    assert [(term.feature_id, term.hundredths, term.reading) for term in quiet.terms] == [
        (FeatureId.ROAD_MAJOR_EXPOSURE, 20, TermReading.LOW),
        (FeatureId.ROAD_TRAFFIC_NEARBY, 20, TermReading.LOW),
        (FeatureId.EVENING_CLUSTER_EXPOSURE, 30, TermReading.LOW),
        (FeatureId.NOISE_EXPOSURE, 30, TermReading.LOW),
    ]
    assert "traffic" in quiet.meaning
    holding = [
        tag.tag_id
        for tag in TAGS.values()
        if any(term.feature_id is FeatureId.ROAD_TRAFFIC_NEARBY for term in tag.terms)
    ]
    assert holding == [TagId.QUIET_RESIDENTIAL]
    # Gritty counts main roads and transport noise, and its recipe is as it was decided.
    # Village feel is as the founder chose to serve it.
    gritty = TAGS[TagId.STREET_CHARACTER]
    assert {term.feature_id: term.hundredths for term in gritty.terms}[
        FeatureId.ROAD_MAJOR_EXPOSURE
    ] == 15
    assert [term.hundredths for term in TAGS[TagId.VILLAGE_FEEL].terms] == [45, 30, 15, 10]


def test_an_area_with_no_figure_of_traffic_is_not_placed_as_though_it_had_no_traffic():
    """A street nobody counted has no figure, which is not a figure of nought.

    Quiet streets is then worked out from its other parts, which are 80 in 100 of it.
    Had the area been taken to have no traffic, it would have stood higher than its
    other parts put it.
    """
    middling = {
        FeatureId.ROAD_MAJOR_EXPOSURE: 50.0,
        FeatureId.EVENING_CLUSTER_EXPOSURE: 50.0,
        FeatureId.NOISE_EXPOSURE: 50.0,
    }
    not_known = tag_raw(TagId.QUIET_RESIDENTIAL, middling)
    assert (not_known.raw, not_known.coverage) == (0.5, 0.8)
    assert tag_raw(TagId.QUIET_RESIDENTIAL, middling | {FeatureId.ROAD_TRAFFIC_NEARBY: None}) == (
        not_known
    )
    as_though_none = tag_raw(
        TagId.QUIET_RESIDENTIAL, middling | {FeatureId.ROAD_TRAFFIC_NEARBY: 0.0}
    )
    assert (as_though_none.raw, as_though_none.coverage) == (0.6, 1.0)
    # And an area that is known to have the most traffic of all stands lower.
    busiest = tag_raw(TagId.QUIET_RESIDENTIAL, middling | {FeatureId.ROAD_TRAFFIC_NEARBY: 100.0})
    assert (busiest.raw, busiest.coverage) == (0.4, 1.0)
    assert "is not taken to have none" in " ".join(TAGS[TagId.QUIET_RESIDENTIAL].cannot_see)


def test_gritty_is_one_vibe_on_a_scale_that_counts_recorded_crime():
    # Decided on 2026-09-24. Works and warehouses and what is recorded are six in ten of
    # it: homes per hectare and nitrogen dioxide were taken out, because each says central
    # and built up, and between them they put a smart district at the gritty end.
    gritty = TAGS[TagId.STREET_CHARACTER]
    assert (gritty.label, gritty.short_label) == ("Gritty", "Gritty")
    assert (gritty.shape, gritty.low_end, gritty.high_end) == ("scale", "Polished", "Gritty")
    assert {term.feature_id: term.hundredths for term in gritty.terms} == {
        FeatureId.INCIDENT_CRIMINAL_DAMAGE: 30,
        FeatureId.LAND_INDUSTRY: 15,
        FeatureId.LAND_STORAGE: 15,
        FeatureId.INCIDENT_ANTISOCIAL: 15,
        FeatureId.ROAD_MAJOR_EXPOSURE: 15,
        FeatureId.NOISE_EXPOSURE: 10,
    }
    assert all(term.reading is TermReading.HIGH for term in gritty.terms)
    recorded = sum(
        term.hundredths
        for term in gritty.terms
        if FEATURES[term.feature_id].dimension is Dimension.CRIME
    )
    assert recorded == 45
    # So it has no band where recorded crime is not held: what is left is 55 of 100.
    assert 100 - recorded < 60
    parts = {term.feature_id for term in gritty.terms}
    assert not parts & {FeatureId.HOMES_DENSITY, FeatureId.AIR_NO2}
    # Every part is of the place, or of what was recorded there.
    assert {FEATURES[part].describes for part in parts} == {Describes.PLACE, Describes.EVENTS}
    assert "recorded criminal damage and anti-social behaviour" in gritty.meaning


def test_works_and_warehouses_is_a_part_of_gritty_and_is_not_served_beside_it():
    """As a vibe of its own it is right at the top and wrong as five bands.

    Most areas hold no such land and tie in the lowest band. So a release that carries
    Gritty holds the land as parts of Gritty, and carries no second vibe for it.
    """
    works = TAGS[TagId.WORKS_WAREHOUSES]
    assert (works.label, works.shape) == ("Works and warehouses", TagShape.ONE_WAY)
    assert {term.feature_id: term.hundredths for term in works.terms} == {
        FeatureId.LAND_INDUSTRY: 40,
        FeatureId.LAND_STORAGE: 35,
        FeatureId.LAND_TRANSPORT_OTHER: 25,
    }
    assert not crime(works)
    carried = [tag.tag_id for tag in tags_of(GrittyVariant.B)]
    assert TagId.WORKS_WAREHOUSES not in carried
    # Gritty is the last of the vibes of the place. The two that count who lives there
    # come after it.
    assert carried[-3:] == [
        TagId.STREET_CHARACTER,
        TagId.FAMILY_AREA,
        TagId.YOUNG_PROFESSIONALS,
    ]
    gritty = {term.feature_id: term.hundredths for term in TAGS[TagId.STREET_CHARACTER].terms}
    assert (gritty[FeatureId.LAND_INDUSTRY], gritty[FeatureId.LAND_STORAGE]) == (15, 15)


def test_the_scales_are_these_and_their_ends_are_named_low_to_high():
    scales = {t.tag_id: (t.low_end, t.high_end) for t in TAGS.values() if t.shape == "scale"}
    assert scales == {
        TagId.PACE: ("Calm", "Buzzy"),
        TagId.BUILT_AGE: ("Newer", "Historic"),
        TagId.HOMES: ("Houses", "Flats"),
        TagId.STREET_CHARACTER: ("Polished", "Gritty"),
    }


def crime(tag: Tag) -> bool:
    return any(FEATURES[t.feature_id].dimension is Dimension.CRIME for t in tag.terms)


def nuisance(tag: Tag) -> bool:
    return any(t.feature_id in NUISANCES for t in tag.terms)


def test_one_vibe_alone_holds_recorded_crime_and_one_scale_alone_holds_a_nuisance():
    # Gritty is the one vibe that counts recorded crime, in a release of London as in a
    # made-up one (ADR 0013, as amended). Every other recipe holds no crime figure.
    assert [t.tag_id for t in TAGS.values() if crime(t)] == [TagId.STREET_CHARACTER]
    scales = [t for t in TAGS.values() if t.shape is TagShape.SCALE]
    assert [t.tag_id for t in scales if nuisance(t)] == [TagId.STREET_CHARACTER]


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_a_one_way_vibe_reads_a_nuisance_from_its_low_end_only(tag: Tag):
    if tag.shape is TagShape.ONE_WAY:
        assert all(t.reading is TermReading.LOW for t in tag.terms if t.feature_id in NUISANCES)


def test_no_recipe_holds_a_part_that_is_weighed_on_request_only():
    on_request = {f for f, feature in FEATURES.items() if feature.kind is FeatureKind.ON_REQUEST}
    # A campus, the results of schools, and the nearest place of each chain a person may name.
    assert on_request == {
        FeatureId.UNIVERSITY_PROXIMITY,
        FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
        FeatureId.SCHOOL_SECONDARY_ATTAINMENT,
        *CHAINS,
    }
    assert not any(t.feature_id in on_request for tag in TAGS.values() for t in tag.terms)


def test_a_release_carries_the_thirteen_vibes_and_the_one_that_gritty_is_read_as():
    # What the word "gritty" is read as, by what a release carries.
    assert GRITTY == {
        GrittyVariant.A: TagId.WORKS_WAREHOUSES,
        GrittyVariant.B: TagId.STREET_CHARACTER,
    }
    # The committed release and a build of London carry fourteen: every vibe but Works and
    # warehouses, which is a part of Gritty. Gritty comes last of the vibes of the place, and
    # the two that count who lives there come after it.
    carried = tags_of(GrittyVariant.B)
    assert {tag.tag_id for tag in carried} == set(TagId) - {TagId.WORKS_WAREHOUSES}
    assert [tag.shelf_order for tag in carried] == [*range(1, 11), 12, 13, 14, 15]
    assert [tag.tag_id for tag in carried[-3:]] == [
        TagId.STREET_CHARACTER,
        TagId.FAMILY_AREA,
        TagId.YOUNG_PROFESSIONALS,
    ]
    # A release that holds no recorded crime carries fourteen: every vibe but Gritty.
    without = tags_of(GrittyVariant.A)
    assert {tag.tag_id for tag in without} == set(TagId) - {TagId.STREET_CHARACTER}
    assert [tag.shelf_order for tag in without] == [*range(1, 13), 14, 15]
    assert not any(crime(tag) for tag in without)


def test_the_shelf_is_seven_words_in_this_order_and_each_says_which_end_it_asks_for():
    shelf = sorted((t for t in TAGS.values() if t.shelf_word), key=lambda t: t.shelf_order or 0)
    assert [(t.shelf_order, t.tag_id, t.shelf_word, t.shelf_toward) for t in shelf] == [
        (1, TagId.LEAFY, "leafy", Toward.HIGH),
        (2, TagId.VILLAGE_FEEL, "villagey", Toward.HIGH),
        (3, TagId.PACE, "lively", Toward.HIGH),
        (4, TagId.QUIET_RESIDENTIAL, "quiet street", Toward.HIGH),
        (5, TagId.BUILT_AGE, "period", Toward.HIGH),
        (6, TagId.EVERYDAY_ON_FOOT, "walkable", Toward.HIGH),
        (7, TagId.PARKS_CLOSE_BY, "near a big park", Toward.HIGH),
    ]
    more = [t for t in TAGS.values() if not t.shelf_word]
    assert all(t.shelf_toward is None and (t.shelf_order or 0) >= 8 for t in more)


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_every_vibe_says_what_it_cannot_see_and_the_same_line_comes_first(tag: Tag):
    assert (
        tag.cannot_see[0]
        == COMMON_CANNOT_SEE
        == ("One street or one home. An area is many streets.")
    )
    assert len(tag.cannot_see) >= 4
    assert all(line.endswith(".") and line[0].isupper() for line in tag.cannot_see)
    assert tag.meaning and tag.short_label and tag.family in FAMILIES


def test_what_a_vibe_cannot_tell_apart_is_said_in_a_whole_sentence():
    # Seen on a page, under what a vibe cannot see: "Road noise from aircraft noise." and
    # "Weekday from weekend.". Each read as if a word were missing.
    lines = {line for tag in TAGS.values() for line in tag.cannot_see}
    assert not lines & {"Road noise from aircraft noise.", "Weekday from weekend."}
    quiet, pace = TAGS[TagId.QUIET_RESIDENTIAL].cannot_see, TAGS[TagId.PACE].cannot_see
    assert "Which noise is from roads and which from aircraft." in quiet
    assert "How a weekday differs from a weekend." in pace


def test_leafy_says_that_a_wood_that_is_a_public_park_is_counted_twice():
    """No file of woodland outlines is held, so the figure cannot be put right. It is said."""
    assert TAGS[TagId.LEAFY].cannot_see[-1] == (
        "A wood that is a public park is counted twice, by woodland and by public parks."
    )


def test_the_families_are_five_in_the_order_of_the_settings():
    # What counts who lives somewhere stands in a group of its own, last, apart from what
    # counts places. Its name says the census.
    assert list(FAMILIES.items()) == [
        (Family.STREETS_HOMES, "Streets and homes"),
        (Family.PACE_FOOD, "Pace and food"),
        (Family.GREEN, "Green"),
        (Family.DAILY_LIFE, "Daily life"),
        (Family.WHO_LIVES_THERE, "Who lives there, at the 2021 census"),
    ]
    inside = {f for f, feature in FEATURES.items() if feature.family == "who_lives_there"}
    assert inside == COUNTS_RESIDENTS
    assert {t for t, tag in TAGS.items() if tag.family == "who_lives_there"} == HOLDS_RESIDENTS


def test_the_nuisances_are_read_from_what_kind_of_thing_a_feature_is():
    assert {
        FeatureId.CRIME_VIOLENCE_ROBBERY,
        FeatureId.CRIME_BURGLARY_THEFT,
        FeatureId.AIR_NO2,
        FeatureId.NOISE_EXPOSURE,
        FeatureId.ROAD_MAJOR_EXPOSURE,
        FeatureId.EVENING_CLUSTER_EXPOSURE,
        FeatureId.INCIDENT_CRIMINAL_DAMAGE,
        FeatureId.INCIDENT_ANTISOCIAL,
        FeatureId.ROAD_TRAFFIC_NEARBY,
    } == NUISANCES
    # Less of a nuisance is the only wish there is, so its one direction is less.
    assert all(FEATURES[f].polarity is Polarity.LESS for f in NUISANCES)


def test_what_a_feature_describes_is_a_place_its_buildings_or_what_was_recorded_there():
    events = {f for f, feature in FEATURES.items() if feature.describes is Describes.EVENTS}
    assert events == {f for f, feature in FEATURES.items() if feature.dimension == "crime"}
    assert {f for f, feature in FEATURES.items() if feature.describes == "buildings"} == {
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_PRE1919,
        FeatureId.HOMES_POST2000,
        FeatureId.HOMES_DENSITY,
        FeatureId.CONSERVATION_COVER,
        FeatureId.LISTED_BUILDINGS,
        FeatureId.PRIVATE_OUTDOOR_SPACE,
        # What homes sold for is a figure of the homes of a place, and so is how far it
        # has risen, and the council tax bands the homes are in.
        FeatureId.PRICE_MEDIAN,
        FeatureId.PRICE_RISE_5Y,
        FeatureId.PRICE_RISE_10Y,
        FeatureId.HOMES_HIGHER_BANDS,
        # How much of a high street lies in a conservation area, as conservation cover is.
        FeatureId.HIGHSTREET_CONSERVED,
    }
    # Who lived there is said of the four measures of the census, and of nothing else.
    assert {f for f, feature in FEATURES.items() if feature.describes == "residents"} == {
        f for f, feature in FEATURES.items() if feature.dimension == "residents"
    }


def test_a_figure_that_its_publisher_models_is_said_to_be_modelled():
    # Nitrogen dioxide is a model's figure: its publisher gives no reading, and the name
    # of the feature says so. The traffic past a count point is its publisher's estimate
    # of the average day of a year, and no reading either. The rest are said to be
    # measured until a real build finds one that is not.
    modelled = {f for f, feature in FEATURES.items() if feature.method is Method.MODELLED}
    assert modelled == {FeatureId.AIR_NO2, FeatureId.ROAD_TRAFFIC_NEARBY}
    assert "Modelled" in FEATURES[FeatureId.AIR_NO2].label
    averaged = {f for f, feature in FEATURES.items() if feature.method is Method.AVERAGED}
    others = [feature for f, feature in FEATURES.items() if f not in modelled | averaged]
    assert all(feature.method is Method.MEASURED for feature in others)


def test_a_figure_that_is_the_mean_of_smaller_areas_is_said_to_be_averaged():
    # The publisher of transport noise gives a share for each small area, with no top and
    # no bottom, so no sum can be taken: an area's figure is the mean of its small areas.
    averaged = {f for f, feature in FEATURES.items() if feature.method is Method.AVERAGED}
    assert averaged == {FeatureId.NOISE_EXPOSURE}


def test_the_measures_likeness_may_use_are_these_and_none_is_a_nuisance_or_an_event():
    likeness = {f for f, feature in FEATURES.items() if feature.in_likeness}
    assert len(likeness) == 25
    never = (
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_DENSITY,
        FeatureId.PRIVATE_OUTDOOR_SPACE,
        FeatureId.SCHOOL_PRIMARY_NEARBY,
        FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
        FeatureId.SCHOOL_SECONDARY_ATTAINMENT,
        # The heaviest part of a rough guide: no likeness between areas counts it.
        FeatureId.HIGHSTREET_CONSERVED,
    )
    assert not likeness & set(never)
    for feature_id in likeness:
        feature = FEATURES[feature_id]
        assert feature.kind in (FeatureKind.TASTE, FeatureKind.AMENITY)
        assert feature.describes is not Describes.EVENTS
        assert feature.family is not None


def test_crime_and_what_is_in_the_air_belong_to_no_family_of_the_settings():
    for feature in FEATURES.values():
        if feature.dimension is Dimension.CRIME:
            assert feature.family is None
        if feature.feature_id in (FeatureId.AIR_NO2, FeatureId.NOISE_EXPOSURE):
            assert feature.family is None


@pytest.mark.parametrize("feature_id", FeatureId)
def test_a_short_label_is_short_and_holds_no_figure(feature_id: FeatureId):
    short = FEATURES[feature_id].short_label
    assert 0 < len(short) <= 40
    assert not any(character.isdigit() for character in short)
    assert short[0].isupper() and not short.endswith(".")


def test_a_short_label_says_the_wish_where_there_is_one_direction_and_the_measure_where_two():
    assert FEATURES[FeatureId.NOISE_EXPOSURE].short_label == "Less transport noise"
    assert FEATURES[FeatureId.PARK_PROXIMITY].short_label == "Nearer a park"
    assert FEATURES[FeatureId.VENUE_EVENING_PER_HOMES].short_label == "Pubs and bars"
    shorts = [feature.short_label for feature in FEATURES.values()]
    shorts += [tag.short_label for tag in TAGS.values()]
    assert len(set(shorts)) == len(shorts)
    assert all(0 < len(tag.short_label) <= 40 for tag in TAGS.values())


def test_the_words_with_two_meanings_are_few_and_written_in_one_place():
    assert MIXED_WORDS == ("gritty", "edgy", "raw")


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_conservation_areas_never_decide_a_tag_alone(tag: Tag):
    # A condition of the source. With the coverage rule, a tag that has only the parts
    # that rest on conservation areas present is below 60 hundredths and so is unknown.
    # Two measures rest on them: the cover of an area, and of its nearest high street.
    assert set(ON_CONSERVATION_AREAS) == {
        FeatureId.CONSERVATION_COVER,
        FeatureId.HIGHSTREET_CONSERVED,
    }
    carried = sum(t.hundredths for t in tag.terms if t.feature_id in ON_CONSERVATION_AREAS)
    assert carried < 60
    if carried:
        alone = dict.fromkeys(ON_CONSERVATION_AREAS, 90.0)
        assert tag_raw(tag.tag_id, alone).raw is None


def test_a_recipe_whose_parts_on_conservation_areas_come_to_sixty_is_refused():
    """A person may move the shares of a recipe at the panel. Moved so, one source would
    place an area alone, which its licence registry entry forbids."""
    village = TAGS[TagId.VILLAGE_FEEL]
    moved = tuple(
        term.replace(hundredths=share)
        for term, share in zip(village.terms, (50, 25, 15, 10), strict=True)
    )
    with pytest.raises(ValueError, match="rest on conservation areas"):
        checked_recipe(village.replace(terms=moved))
    kept = tuple(
        term.replace(hundredths=share)
        for term, share in zip(village.terms, (49, 26, 15, 10), strict=True)
    )
    assert checked_recipe(village.replace(terms=kept)).terms == kept


def test_crime_has_a_fixed_direction_and_university_cannot_be_asked_to_be_far():
    for feature_id in (FeatureId.CRIME_BURGLARY_THEFT, FeatureId.CRIME_VIOLENCE_ROBBERY):
        assert FEATURES[feature_id].polarity is Polarity.LESS
    # "Far from a university" would be a way to ask for fewer students.
    assert not direction_allowed(FeatureId.UNIVERSITY_PROXIMITY, Direction.MORE)
    assert direction_allowed(FeatureId.UNIVERSITY_PROXIMITY, Direction.LESS)


def test_only_features_of_buildings_venues_and_land_let_the_user_choose_the_direction():
    either = {f.feature_id for f in FEATURES.values() if f.polarity is Polarity.EITHER}
    assert either == {
        FeatureId.VENUE_FOOD_DRINK,
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES,
        FeatureId.VENUE_EVENING,
        FeatureId.VENUE_EVENING_PER_HOMES,
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_PRE1919,
        FeatureId.HOMES_POST2000,
        FeatureId.HOMES_DENSITY,
        FeatureId.LAND_INDUSTRY,
        FeatureId.LAND_STORAGE,
        FeatureId.LAND_TRANSPORT_OTHER,
        FeatureId.PRICE_MEDIAN,
        # Which chains stand in a place: a person may ask for more premium or for less.
        FeatureId.BRAND_MIX,
        FeatureId.PRICE_RISE_5Y,
        FeatureId.PRICE_RISE_10Y,
        FeatureId.HOMES_HIGHER_BANDS,
    }
    assert all(default_direction(f) is Direction.MORE for f in either)
    # Wanting less of one is a taste in places, so each is a taste.
    assert all(FEATURES[f].kind is FeatureKind.TASTE for f in either)


def test_a_band_is_one_of_five_counted_from_the_areas_strictly_below():
    # With 22 compared: 0 to 4 below is band 1, 5 to 8 band 2, 9 to 13 band 3,
    # 14 to 17 band 4, 18 to 21 band 5.
    values = [float(n) for n in range(22)]
    bands = band_of(values, [True] * 22)
    assert bands == (*[1] * 5, *[2] * 4, *[3] * 5, *[4] * 4, *[5] * 4)


def test_a_band_is_unknown_exactly_where_the_value_is():
    assert band_of([5.0, None, 7.0], [True, True, True]) == (1, None, 3)
    assert band_of([None, None], [True, True]) == (None, None)
    assert band_of([], []) == ()


def test_areas_that_are_level_share_a_band_and_none_counts_as_below_another():
    assert band_of([1.0, 1.0, 1.0, 1.0], [True] * 4) == (1, 1, 1, 1)
    # Two of five are strictly below the pair in the middle: 1 + (5 * 2) // 5.
    assert band_of([0.0, 0.0, 3.0, 3.0, 9.0], [True] * 5) == (1, 1, 3, 3, 5)


def test_an_area_that_is_not_rankable_is_banded_against_those_that_are():
    # The population is 10, 20, 30, 40 and 50. The unrankable 35 has three below it.
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 35.0]
    assert band_of(values, [True] * 5 + [False]) == (1, 2, 3, 4, 5, 4)
    assert band_of([4.0, None], [False, True]) == (None, None)


def test_a_band_refuses_flags_that_do_not_match_the_values():
    with pytest.raises(ValueError, match="one rankable flag"):
        band_of([1.0, 2.0], [True])


def test_a_band_does_not_depend_on_the_order_of_the_areas_and_follows_the_values():
    draw = draws(13)
    values = [draw.choice([None, *range(9)]) for _ in range(30)]
    floats = [None if v is None else float(v) for v in values]
    flags = [draw.random() < 0.8 for _ in floats]
    expected = dict(zip(range(30), band_of(floats, flags), strict=True))
    for _ in range(10):
        order = draw.sample(range(30), 30)
        shuffled = band_of([floats[i] for i in order], [flags[i] for i in order])
        assert dict(zip(order, shuffled, strict=True)) == expected
    found = [(v, b) for v, b in zip(floats, expected.values(), strict=True) if v is not None]
    if any(flags):
        assert all(b is not None and 1 <= b <= 5 for _, b in found)
        assert [b for _, b in sorted(found)] == sorted(b for _, b in found if b is not None)


def test_percentile_is_the_mid_rank_of_the_contract_example():
    values = [310.0, 120.0, 640.0, 310.0, 900.0]
    assert percentile_of(values, [True] * 5) == (40.0, 10.0, 70.0, 40.0, 90.0)


def test_percentile_is_unknown_exactly_where_the_value_is():
    assert percentile_of([5.0, None, 7.0], [True, True, True]) == (25.0, None, 75.0)


def test_an_area_that_is_not_rankable_is_placed_without_joining_the_population():
    # The population is 10 and 30. The unrankable 20 sits between them, and
    # leaves their percentiles as they would be without it.
    assert percentile_of([10.0, 20.0, 30.0], [True, False, True]) == (25.0, 50.0, 75.0)


def test_percentile_is_unknown_when_no_rankable_area_has_a_value():
    assert percentile_of([4.0, None], [False, True]) == (None, None)
    assert percentile_of([], []) == ()


def test_percentile_refuses_flags_that_do_not_match_the_values():
    with pytest.raises(ValueError, match="one rankable flag"):
        percentile_of([1.0, 2.0], [True])


def test_percentile_does_not_depend_on_the_order_of_the_areas():
    draw = draws(7)
    values = [draw.choice([None, *range(12)]) for _ in range(40)]
    floats = [None if v is None else float(v) for v in values]
    flags = [draw.random() < 0.8 for _ in floats]
    expected = dict(zip(range(40), percentile_of(floats, flags), strict=True))
    for _ in range(20):
        order = draw.sample(range(40), 40)
        shuffled = percentile_of([floats[i] for i in order], [flags[i] for i in order])
        assert dict(zip(order, shuffled, strict=True)) == expected


def test_percentiles_stay_within_bounds_and_follow_the_values():
    draw = draws(11)
    for _ in range(50):
        values = [float(draw.randrange(30)) for _ in range(draw.randrange(1, 25))]
        found = [p for p in percentile_of(values, [True] * len(values)) if p is not None]
        assert len(found) == len(values)
        assert all(0 <= p <= 100 for p in found)
        in_value_order = [p for _, p in sorted(zip(values, found, strict=True))]
        assert in_value_order == sorted(found)


def test_tag_is_the_weighted_mean_of_the_terms_that_are_present():
    # Parks close by: 0.40 park_proximity low, 0.30 park_large_proximity low,
    # 0.30 park_facilities high.
    full = tag_raw(
        TagId.PARKS_CLOSE_BY,
        {
            FeatureId.PARK_PROXIMITY: 10.0,
            FeatureId.PARK_LARGE_PROXIMITY: 40.0,
            FeatureId.PARK_FACILITIES: 80.0,
        },
    )
    assert full.coverage == 1.0
    assert full.raw == pytest.approx(0.40 * 0.9 + 0.30 * 0.6 + 0.30 * 0.8)


def test_a_missing_term_is_dropped_and_the_rest_reweighted():
    found = tag_raw(TagId.LEAFY, {FeatureId.LAND_GARDENS: 80.0, FeatureId.GREEN_COVER: None})
    assert found.coverage == 0.4
    assert found.raw is None  # 40 hundredths is below 60

    kept = tag_raw(TagId.LEAFY, {FeatureId.LAND_GARDENS: 80.0, FeatureId.LAND_WOODLAND: 10.0})
    assert kept.coverage == 0.7
    assert kept.raw == pytest.approx((0.40 * 0.8 + 0.30 * 0.1) / 0.70)


def test_tag_coverage_of_exactly_sixty_hundredths_is_enough():
    # 0.25 + 0.20 + 0.15. As floats these need not sum to 0.6; as hundredths they do.
    found = tag_raw(
        TagId.EVERYDAY_ON_FOOT,
        {
            FeatureId.GROCERY_WALK: 50.0,
            FeatureId.STATION_WALK: 50.0,
            FeatureId.GP_WALK: 50.0,
        },
    )
    assert found.coverage == 0.6
    assert found.raw == 0.5


def test_everyday_on_foot_says_what_its_distances_cannot_see():
    """Each part is a straight line to a place of which the file says little.

    On London its order is mostly that of homes to the hectare. A person is told
    so beside the band, first of what is the vibe's own.
    """
    said = TAGS[TagId.EVERYDAY_ON_FOOT].cannot_see
    assert said == (
        COMMON_CANNOT_SEE,
        "It is mostly a map of how built up a place is.",
        "How long the walk is: each distance is a straight line.",
        "Which side of a railway a home is on.",
        "How large a food shop is, and what it sells.",
        "Whether a surgery takes new patients.",
        "Opening hours.",
        "Step-free access at every station.",
    )
    assert "straight line" in said[2] and "walk" not in TAGS[TagId.EVERYDAY_ON_FOOT].meaning


def test_a_recipe_runs_short_where_a_release_holds_no_figure_for_a_part():
    # Everyday on foot holds a GP and a pharmacy, which the made-up release does
    # not carry. It runs at 70 hundredths, which is enough to place an area. Each
    # part is a distance, and is read from its near end.
    found = tag_raw(
        TagId.EVERYDAY_ON_FOOT,
        {
            FeatureId.GROCERY_WALK: 20.0,
            FeatureId.HIGHSTREET_ACCESS: 20.0,
            FeatureId.STATION_WALK: 20.0,
        },
    )
    assert found.coverage == 0.7
    assert found.raw == pytest.approx(0.8)


def test_every_walk_time_and_distance_has_a_figure_at_which_it_is_never_a_trade_off():
    # A walk, a time or a distance is bad in itself only when it is long. The
    # figure is in the catalogue, beside the measure, and in no rule of code.
    measured = {f for f, feature in FEATURES.items() if feature.unit in ("min", "m")}
    assert set(NEVER_A_TRADE_OFF) == measured
    # Twelve, the nearest place of each of nine tiers, and the nearest of each of 29 chains.
    assert len(measured) == 12 + 9 + len(CHAINS) == 50
    for feature_id, figure in NEVER_A_TRADE_OFF.items():
        # Each is a measure of which less is better, so a short one is a good one.
        assert FEATURES[feature_id].polarity is Polarity.LESS, feature_id
        assert figure > 0
    # What a person walks in ten minutes and in twenty. No walk is left: each is a distance.
    assert {FEATURES[f].unit for f in measured} == {"m"}
    assert {NEVER_A_TRADE_OFF[f] for f in measured} == {800, 1600}
    assert NEVER_A_TRADE_OFF[FeatureId.STATION_WALK] == 800
    assert NEVER_A_TRADE_OFF[FeatureId.GROCERY_WALK] == 800
    with pytest.raises(ValueError, match="never a trade-off"):
        checked_floors({FeatureId.STATION_WALK: 800})
    with pytest.raises(ValueError, match="never a trade-off"):
        checked_floors({**NEVER_A_TRADE_OFF, FeatureId.GREEN_COVER: 5})


def test_near_a_station_is_said_as_the_figure_core_holds_and_the_figure_is_no_walk():
    """Decided on 2026-09-25: near a station is about a 10 to 15 minute walk.

    A straight line of 800 m is a walk of about that, so the figure at or under which
    the distance to a station is never a trade-off is what near means. The words say
    that figure, whatever it is. The measure is named a straight line, in metres, and
    no word of its own says a walk or a minute.
    """
    floor = NEVER_A_TRADE_OFF[FeatureId.STATION_WALK]
    assert floor == 800
    assert NEAR_A_STATION == "Within 800 m in a straight line is about a 10 to 15 minute walk."
    assert NEAR_A_STATION.startswith(f"Within {floor} m in a straight line ")
    station = FEATURES[FeatureId.STATION_WALK]
    assert station.label == "Straight-line distance to the nearest way in to a station"
    assert (station.unit, station.polarity) == ("m", Polarity.LESS)
    for words in (station.label, station.short_label, station.higher, station.lower):
        assert "walk" not in words.lower() and "minute" not in words.lower()
