"""The vocabulary: every id and every enum the rest of Burro may use.

`FeatureId` and `TagId` are the allowlist of ADR 0006. An edit, a spec, a model
or a fact can name nothing that is not a member. Four features describe who
lives somewhere, and no other does: the residents aged 20 to 34 and aged 65 and
over, and the households with dependent children and of one person, each as
Census 2021 counted them (ADR 0006, as amended on 2026-09-24). Nothing else
about who lives somewhere can be asked for: there is no id for it.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import Field

# The prefix is the city and `syn` is synthetic. The letter says what the id names.
AREA_ID_PATTERN = r"^(syn|lon)-n[0-9a-z]+$"
DESTINATION_ID_PATTERN = r"^(syn|lon)-d[0-9a-z]+$"
PLACE_ID_PATTERN = r"^(syn|lon)-p[0-9a-z]+$"
STATION_ID_PATTERN = r"^(syn|lon)-s[0-9a-z]+$"
RELEASE_ID_PATTERN = r"^(syn|lon)-\d{4}-\d{2}-\d{2}-\d{2}$"
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
SOURCE_ID_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
DATE_OR_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])(-\d{2})?$"
TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"

AreaId = Annotated[str, Field(pattern=AREA_ID_PATTERN)]
DestinationId = Annotated[str, Field(pattern=DESTINATION_ID_PATTERN)]
PlaceId = Annotated[str, Field(pattern=PLACE_ID_PATTERN)]
StationId = Annotated[str, Field(pattern=STATION_ID_PATTERN)]
ReleaseId = Annotated[str, Field(pattern=RELEASE_ID_PATTERN)]
SourceId = Annotated[str, Field(pattern=SOURCE_ID_PATTERN)]

SYNTHETIC_PREFIX = "syn-"
SYNTHETIC_SOURCE_ID = "synthetic"


class FeatureId(StrEnum):
    CRIME_VIOLENCE_ROBBERY = "crime_violence_robbery"
    CRIME_BURGLARY_THEFT = "crime_burglary_theft"
    SCHOOL_PRIMARY_NEARBY = "school_primary_nearby"
    SCHOOL_PRIMARY_ATTAINMENT = "school_primary_attainment"
    SCHOOL_SECONDARY_ATTAINMENT = "school_secondary_attainment"
    UNIVERSITY_PROXIMITY = "university_proximity"
    GREEN_COVER = "green_cover"
    PARK_PROXIMITY = "park_proximity"
    PLAY_SPACE_PROXIMITY = "play_space_proximity"
    WATER_ACCESS = "water_access"
    AIR_NO2 = "air_no2"
    NOISE_EXPOSURE = "noise_exposure"
    VENUE_FOOD_DRINK = "venue_food_drink"
    VENUE_EVENING = "venue_evening"
    VENUE_INDEPENDENT = "venue_independent"
    CULTURE_VENUES = "culture_venues"
    HIGHSTREET_ACCESS = "highstreet_access"
    HOMES_FLATS = "homes_flats"
    HOMES_PRE1919 = "homes_pre1919"
    HOMES_DENSITY = "homes_density"
    CONSERVATION_COVER = "conservation_cover"
    STATION_WALK = "station_walk"
    STATION_LINES = "station_lines"
    # The parts the vibes of catalogue version 2 are made of.
    INDEPENDENTS_NEARBY = "independents_nearby"
    CENTRE_SMALL = "centre_small"
    CENTRE_COMPACT = "centre_compact"
    LISTED_BUILDINGS = "listed_buildings"
    HOMES_POST2000 = "homes_post2000"
    ROAD_MAJOR_EXPOSURE = "road_major_exposure"
    EVENING_CLUSTER_EXPOSURE = "evening_cluster_exposure"
    LAND_INDUSTRY = "land_industry"
    LAND_STORAGE = "land_storage"
    LAND_TRANSPORT_OTHER = "land_transport_other"
    LAND_GARDENS = "land_gardens"
    LAND_WOODLAND = "land_woodland"
    PARK_LARGE_PROXIMITY = "park_large_proximity"
    PARK_FACILITIES = "park_facilities"
    GROCERY_WALK = "grocery_walk"
    INCIDENT_CRIMINAL_DAMAGE = "incident_criminal_damage"
    INCIDENT_ANTISOCIAL = "incident_antisocial"
    PRIVATE_OUTDOOR_SPACE = "private_outdoor_space"
    CUISINE_VARIETY = "cuisine_variety"
    GP_WALK = "gp_walk"
    PHARMACY_WALK = "pharmacy_walk"
    # What a wish for places to eat and drink is ranked on. The count is shown.
    VENUE_FOOD_DRINK_PER_HOMES = "venue_food_drink_per_homes"
    # What homes sold for: the second reading of a word for a smart area. It is a figure
    # of the homes of a place, and never of who lives there or of what they earn.
    PRICE_MEDIAN = "price_median"
    # What a wish for culture is ranked on. The count is shown.
    CULTURE_VENUES_PER_HOMES = "culture_venues_per_homes"
    # Cafes, gyms and pubs. Of each the count within reach is shown, and a wish is ranked on
    # the figure for each 1,000 homes. The count of pubs and bars is `venue_evening`.
    VENUE_CAFE = "venue_cafe"
    VENUE_CAFE_PER_HOMES = "venue_cafe_per_homes"
    VENUE_GYM = "venue_gym"
    VENUE_GYM_PER_HOMES = "venue_gym_per_homes"
    VENUE_EVENING_PER_HOMES = "venue_evening_per_homes"
    # The chains of grocers, gyms and coffee within reach, by the tier the table of tiers
    # gives each chain. The table is a judgement, and is data of the pipeline's: core names
    # a tier and never says which chain is of it. Each is a count of places of a chain, and
    # says nothing of who shops anywhere.
    GROCER_PREMIUM_NEARBY = "grocer_premium_nearby"
    GROCER_MID_NEARBY = "grocer_mid_nearby"
    GROCER_VALUE_NEARBY = "grocer_value_nearby"
    GYM_PREMIUM_NEARBY = "gym_premium_nearby"
    GYM_MID_NEARBY = "gym_mid_nearby"
    GYM_VALUE_NEARBY = "gym_value_nearby"
    COFFEE_PREMIUM_NEARBY = "coffee_premium_nearby"
    COFFEE_MID_NEARBY = "coffee_mid_nearby"
    COFFEE_VALUE_NEARBY = "coffee_value_nearby"
    # The distance to the nearest place of each tier.
    GROCER_PREMIUM_DISTANCE = "grocer_premium_distance"
    GROCER_MID_DISTANCE = "grocer_mid_distance"
    GROCER_VALUE_DISTANCE = "grocer_value_distance"
    GYM_PREMIUM_DISTANCE = "gym_premium_distance"
    GYM_MID_DISTANCE = "gym_mid_distance"
    GYM_VALUE_DISTANCE = "gym_value_distance"
    COFFEE_PREMIUM_DISTANCE = "coffee_premium_distance"
    COFFEE_MID_DISTANCE = "coffee_mid_distance"
    COFFEE_VALUE_DISTANCE = "coffee_value_distance"
    # How far the chains within reach lean to premium or to value. It is what a word for a
    # smart area is first read as, and the one measure of the tiers that is ranked on.
    BRAND_MIX = "brand_mix"
    # The distance to the nearest place of one chain, for a person who names the chain.
    BRAND_WAITROSE = "brand_waitrose"
    BRAND_MANDS = "brand_mands"
    BRAND_WHOLE_FOODS = "brand_whole_foods"
    BRAND_SAINSBURYS = "brand_sainsburys"
    BRAND_TESCO = "brand_tesco"
    BRAND_COOP = "brand_coop"
    BRAND_MORRISONS = "brand_morrisons"
    BRAND_ASDA = "brand_asda"
    BRAND_ALDI = "brand_aldi"
    BRAND_LIDL = "brand_lidl"
    BRAND_ICELAND = "brand_iceland"
    BRAND_EQUINOX = "brand_equinox"
    BRAND_THIRD_SPACE = "brand_third_space"
    BRAND_BARRYS = "brand_barrys"
    BRAND_VIRGIN_ACTIVE = "brand_virgin_active"
    BRAND_NUFFIELD = "brand_nuffield"
    BRAND_GYMBOX = "brand_gymbox"
    BRAND_DAVID_LLOYD = "brand_david_lloyd"
    BRAND_ANYTIME_FITNESS = "brand_anytime_fitness"
    BRAND_PUREGYM = "brand_puregym"
    BRAND_THE_GYM_GROUP = "brand_the_gym_group"
    BRAND_GAILS = "brand_gails"
    BRAND_OLE_AND_STEEN = "brand_ole_and_steen"
    BRAND_PRET = "brand_pret"
    BRAND_NERO = "brand_nero"
    BRAND_STARBUCKS = "brand_starbucks"
    BRAND_COSTA = "brand_costa"
    BRAND_BLANK_STREET = "brand_blank_street"
    BRAND_GREGGS = "brand_greggs"
    # The four parts of Well connected, and the stops of buses, which are shown and are
    # ranked on as the routes that call at them. Each counts how near stops are, and
    # nothing of how often anything runs from them.
    UNDERGROUND_PROXIMITY = "underground_proximity"
    OVERGROUND_PROXIMITY = "overground_proximity"
    RAIL_PROXIMITY = "rail_proximity"
    BUS_STOPS_NEARBY = "bus_stops_nearby"
    BUS_ROUTES_NEARBY = "bus_routes_nearby"
    # Who lived in an area at Census 2021: the age of residents, and what households were
    # made of. These four, and no other figure of who lives somewhere (ADR 0006).
    RESIDENTS_AGED_20_34 = "residents_aged_20_34"
    RESIDENTS_AGED_65_OVER = "residents_aged_65_over"
    HOUSEHOLDS_DEPENDENT_CHILDREN = "households_dependent_children"
    HOUSEHOLDS_ONE_PERSON = "households_one_person"
    # The homes of a place by their council tax band: the share in the higher four of the
    # eight. It is a reading of a word for a smart area that counts homes, and never who
    # lives in them or what they earn.
    HOMES_HIGHER_BANDS = "homes_higher_bands"
    # How far what homes sold for has risen, over five years and over ten. A rise is of
    # prices that were paid, and promises nothing.
    PRICE_RISE_5Y = "price_rise_5y"
    PRICE_RISE_10Y = "price_rise_10y"
    # How much of the high street nearest a home lies in a conservation area. It is the
    # heaviest part of Village feel, and counts towards no likeness.
    HIGHSTREET_CONSERVED = "highstreet_conserved"
    # How much traffic passes the busiest count point near a home. It is a nuisance, as
    # main roads are, and a part of Quiet streets.
    ROAD_TRAFFIC_NEARBY = "road_traffic_nearby"


class TagId(StrEnum):
    """On screen a tag is a vibe. Seven ids of catalogue version 1 are retired and never reused:
    buzzy, evening_venues, historic_character, creative, strong_high_street,
    near_universities and waterside."""

    LEAFY = "leafy"
    VILLAGE_FEEL = "village_feel"
    PACE = "pace"
    QUIET_RESIDENTIAL = "quiet_residential"
    BUILT_AGE = "built_age"
    EVERYDAY_ON_FOOT = "everyday_on_foot"
    PARKS_CLOSE_BY = "parks_close_by"
    HOMES = "homes"
    FOODIE = "foodie"
    FAMILY_AMENITIES = "family_amenities"
    # Works and warehouses, and Gritty: the scale that counts recorded crime, under the
    # id it had when it was called Street character. An id is never renamed.
    WORKS_WAREHOUSES = "works_warehouses"
    STREET_CHARACTER = "street_character"
    WELL_CONNECTED = "well_connected"
    # The two vibes that count who lived in an area, beside what is near for them.
    FAMILY_AREA = "family_area"
    YOUNG_PROFESSIONALS = "young_professionals"


class Dimension(StrEnum):
    CRIME = "crime"
    SCHOOLS = "schools"
    GREEN_WATER = "green_water"
    AIR_NOISE = "air_noise"
    VENUES_CULTURE = "venues_culture"
    HOMES = "homes"
    STATION_ACCESS = "station_access"
    SERVICES = "services"
    # The chains of grocers, gyms and coffee. It is of the place: which shops stand there.
    BRANDS = "brands"
    RESIDENTS = "residents"


class FeatureKind(StrEnum):
    """What a person may want of a feature, which decides where it may stand."""

    TASTE = "taste"  # more or less of it
    AMENITY = "amenity"  # more of it, or nearer
    NUISANCE = "nuisance"  # less of it only
    ON_REQUEST = "on_request"  # one direction, by a fairness rule. In no vibe
    # More of it only, and never fewer: it counts who lives somewhere. It may stand in a
    # vibe that runs one way, read from its high end, and in no scale.
    RESIDENTS = "residents"


class Describes(StrEnum):
    """What a feature is a fact about."""

    PLACE = "place"
    BUILDINGS = "buildings"
    EVENTS = "events"
    # Who lived there at the census: their age and their households, and nothing else.
    RESIDENTS = "residents"


class Family(StrEnum):
    """The groups of the settings, in the order they are shown."""

    STREETS_HOMES = "streets_homes"
    PACE_FOOD = "pace_food"
    GREEN = "green"
    DAILY_LIFE = "daily_life"
    # Everything that counts who lives somewhere stands here, apart from what counts places.
    WHO_LIVES_THERE = "who_lives_there"


class Method(StrEnum):
    MEASURED = "measured"
    MODELLED = "modelled"
    AVERAGED = "averaged"


class TagShape(StrEnum):
    SCALE = "scale"  # two named ends, and a person may ask for either
    ONE_WAY = "one_way"  # one direction, and a person may ask for more of it


class Sureness(StrEnum):
    """Whether a vibe is as sure as the rest, or a rough guide. It says so of itself.

    It has these two values and no other. It is no number, and no word of praise or
    blame: it says how far a vibe is to be trusted, and nothing of any place. No client
    works it out. A vibe that does not say is as sure as the rest.
    """

    AS_THE_REST = "as_the_rest"
    # It is served all the same, and says wherever it is shown that it is less sure.
    ROUGH_GUIDE = "rough_guide"


class Toward(StrEnum):
    """Which end of a vibe is asked for. A one-way vibe has the high end alone."""

    HIGH = "high"
    LOW = "low"


class GrittyVariant(StrEnum):
    """Whether a release carries Gritty, the one vibe that counts recorded crime."""

    A = "a"  # It does not, and holds no recorded crime. "Gritty" is read as land use
    B = "b"  # It does: a scale from Polished to Gritty, which Works and warehouses is part of


class Polarity(StrEnum):
    LESS = "less"  # lower is better
    MORE = "more"  # higher is better
    EITHER = "either"  # the user chooses


class NativeResolution(StrEnum):
    OA = "oa"
    LSOA = "lsoa"
    MSOA = "msoa"
    GRID_1KM = "grid_1km"
    POINT = "point"
    POLYGON = "polygon"
    NETWORK = "network"


class TermReading(StrEnum):
    HIGH = "high"
    LOW = "low"


class City(StrEnum):
    SYN = "syn"
    LON = "lon"


class Tenure(StrEnum):
    RENT = "rent"
    BUY = "buy"


class Segment(StrEnum):
    ROOM = "room"
    STUDIO = "studio"
    BED_1 = "bed_1"
    BED_2 = "bed_2"
    BED_3 = "bed_3"
    BED_4PLUS = "bed_4plus"
    FLAT = "flat"
    TERRACED = "terraced"
    SEMI_DETACHED = "semi_detached"
    DETACHED = "detached"


class Confidence(StrEnum):
    """What a cost rests on. The first three are of a range Burro worked out."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    # A publisher's own figure, given with no count of what stands behind it. It is said
    # of a row that holds a median and no range, and of no other. A median that says how
    # many sales it rests on is `high` or `medium`, by how many they are, and so is a rent
    # that says how many rents were recorded.
    UNSTATED = "unstated"


class CostOfKind(StrEnum):
    """The kind of place a cost is of, where it is of a wider place than the area.

    No publisher gives a rent for an area. One gives the rents that were
    recorded in a postcode district and in a borough, and an area is given the
    figure of the place it lies in.
    """

    POSTCODE_DISTRICT = "postcode_district"
    BOROUGH = "borough"


class Mode(StrEnum):
    PT = "pt"
    CYCLE = "cycle"
    WALK = "walk"


class PtBasis(StrEnum):
    TYPICAL = "typical"
    JUST_MISSED = "just_missed"


class Combine(StrEnum):
    SLOWEST = "slowest"
    MEAN = "mean"


class Strictness(StrEnum):
    SOFT = "soft"
    HARD = "hard"


class Direction(StrEnum):
    MORE = "more"
    LESS = "less"


class Provenance(StrEnum):
    STATED = "stated"  # the user said it
    INFERRED = "inferred"  # the interpreter read it into looser words
    DEFAULT = "default"  # nobody chose it
    UI_EDIT = "ui_edit"  # changed with a control


class AreaRuleKind(StrEnum):
    EXCLUDE = "exclude"
    ONLY = "only"


class TravelStatus(StrEnum):
    OK = "ok"
    BEYOND_CUTOFF = "beyond_cutoff"  # no journey within the cutoff. This is data
    MISSING = "missing"  # not computed. This is missing data
    # No time is held, and one was estimated from distance. It is said as a band, and
    # never in minutes. No release holds it: it is what a journey of a search may be.
    ESTIMATED = "estimated"


class JourneyBand(StrEnum):
    """Where an estimated journey stands against the limit a person gave. Never minutes."""

    LIKELY_WITHIN = "likely_within"
    BORDERLINE = "borderline"
    LIKELY_BEYOND = "likely_beyond"


class PlaceKind(StrEnum):
    """In the order that breaks a tie between two matches of the same score."""

    STATION = "station"
    DISTRICT = "district"
    POSTCODE_DISTRICT = "postcode_district"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    LANDMARK = "landmark"


class NameState(StrEnum):
    """How far the name an area bears has been checked."""

    # A method chose it from what publishers write, and no person has read it.
    DRAFT = "draft"
    # A person decided it at the review desk.
    CHECKED = "checked"


class Part(StrEnum):
    """The three files that state their sources once, for the whole file."""

    NEIGHBOURHOODS = "neighbourhoods"
    STATIONS = "stations"
    TRAVEL = "travel"


class GeometryType(StrEnum):
    POLYGON = "Polygon"
    MULTI_POLYGON = "MultiPolygon"


# Operations. Each edit field that may have nothing to say has its own enum,
# because the sentinel is a value like any other: the model's structured output
# cannot express "this field is absent".


class Step(StrEnum):
    NONE = "none"
    UP_SMALL = "up_small"
    UP_LARGE = "up_large"
    DOWN_SMALL = "down_small"
    DOWN_LARGE = "down_large"


class EditProvenance(StrEnum):
    STATED = "stated"
    INFERRED = "inferred"
    UI_EDIT = "ui_edit"


class BudgetAction(StrEnum):
    SET = "set"
    CLEAR = "clear"
    NUDGE = "nudge"


class CommuteAction(StrEnum):
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"


class WeightAction(StrEnum):
    SET = "set"
    NUDGE = "nudge"
    REMOVE = "remove"


class AreaAction(StrEnum):
    EXCLUDE = "exclude"
    ONLY = "only"
    CLEAR = "clear"


class SettingAction(StrEnum):
    SET = "set"
    NUDGE = "nudge"


class Setting(StrEnum):
    COMMUTE_COMBINE = "commute_combine"
    PT_BASIS = "pt_basis"
    COMMUTE_WEIGHT = "commute_weight"
    BUDGET_WEIGHT = "budget_weight"


class Choice(StrEnum):
    SLOWEST = "slowest"
    MEAN = "mean"
    TYPICAL = "typical"
    JUST_MISSED = "just_missed"
    NONE = "none"


class TenureChoice(StrEnum):
    RENT = "rent"
    BUY = "buy"
    UNCHANGED = "unchanged"


class SegmentChoice(StrEnum):
    ROOM = "room"
    STUDIO = "studio"
    BED_1 = "bed_1"
    BED_2 = "bed_2"
    BED_3 = "bed_3"
    BED_4PLUS = "bed_4plus"
    FLAT = "flat"
    TERRACED = "terraced"
    SEMI_DETACHED = "semi_detached"
    DETACHED = "detached"
    UNCHANGED = "unchanged"


class StrictnessChoice(StrEnum):
    SOFT = "soft"
    HARD = "hard"
    UNCHANGED = "unchanged"


class ModeChoice(StrEnum):
    PT = "pt"
    CYCLE = "cycle"
    WALK = "walk"
    UNCHANGED = "unchanged"


class DirectionChoice(StrEnum):
    MORE = "more"
    LESS = "less"
    DEFAULT = "default"


class TowardChoice(StrEnum):
    HIGH = "high"
    LOW = "low"
    DEFAULT = "default"


class OpsGroup(StrEnum):
    """The six arrays of `Operations`, in the order the reducer applies them."""

    BUDGET = "budget_ops"
    COMMUTE = "commute_ops"
    WEIGHT = "weight_ops"
    TAG = "tag_ops"
    AREA = "area_ops"
    SETTING = "setting_ops"


class RejectReason(StrEnum):
    UNKNOWN_PLACE = "unknown_place"
    UNKNOWN_AREA = "unknown_area"
    NOT_IN_RELEASE = "not_in_release"
    TOO_MANY_COMMUTES = "too_many_commutes"
    NO_SUCH_COMMUTE = "no_such_commute"
    OUT_OF_RANGE = "out_of_range"
    SEGMENT_NOT_FOR_TENURE = "segment_not_for_tenure"
    DIRECTION_NOT_ALLOWED = "direction_not_allowed"
    CRIME_NEEDS_EXPLICIT_REQUEST = "crime_needs_explicit_request"
    MISMATCHED_CHOICE = "mismatched_choice"
    NOTHING_TO_CHANGE = "nothing_to_change"


class SpecProblemKind(StrEnum):
    UNKNOWN_PLACE = "unknown_place"
    UNKNOWN_AREA = "unknown_area"
    SEGMENT_NOT_FOR_TENURE = "segment_not_for_tenure"
    DIRECTION_NOT_ALLOWED = "direction_not_allowed"
    NOT_IN_RELEASE = "not_in_release"
    OUT_OF_RANGE = "out_of_range"


class FilterReason(StrEnum):
    """In the order the filters are applied. An area stops at the first that catches it."""

    EXCLUDED = "excluded"
    NOT_SELECTED = "not_selected"
    OVER_BUDGET = "over_budget"
    COMMUTE_CAP = "commute_cap"
    # A firm limit, and a journey that is estimated to be well beyond it. It is an
    # estimate from distance, and the reason says so by having a name of its own.
    COMMUTE_LIKELY_BEYOND = "commute_likely_beyond"


class UnrankedReason(StrEnum):
    NOT_RANKABLE = "not_rankable"
    # Under half of all that counts in the search has a figure.
    INSUFFICIENT_DATA = "insufficient_data"
    # Under half of the features and vibes that count has a figure, whatever
    # is known of the journeys and the cost.
    CHARACTER_UNKNOWN = "character_unknown"


class FactKind(StrEnum):
    AREA = "area"
    FEATURE = "feature"
    TAG = "tag"
    COST = "cost"
    BUDGET_FIT = "budget_fit"
    TRAVEL = "travel"
    STATION = "station"
    MISSING = "missing"
    LIKENESS = "likeness"


class TemplateId(StrEnum):
    AREA = "area"
    FEATURE = "feature"
    FEATURE_CRIME = "feature_crime"
    VIBE = "vibe"
    VIBE_RANGE = "vibe_range"
    VIBE_UNKNOWN = "vibe_unknown"
    COST_RENT = "cost_rent"
    COST_BUY = "cost_buy"
    COST_BUY_MEDIAN = "cost_buy_median"
    COST_BUY_SOLD = "cost_buy_sold"
    COST_RENT_RECORDED = "cost_rent_recorded"
    BUDGET_UNDER = "budget_under"
    BUDGET_OVER = "budget_over"
    BUDGET_AT = "budget_at"
    BUDGET_UNDER_MEDIAN = "budget_under_median"
    BUDGET_OVER_MEDIAN = "budget_over_median"
    BUDGET_AT_MEDIAN = "budget_at_median"
    BUDGET_UNDER_RECORDED = "budget_under_recorded"
    BUDGET_OVER_RECORDED = "budget_over_recorded"
    BUDGET_AT_RECORDED = "budget_at_recorded"
    TRAVEL_PT = "travel_pt"
    TRAVEL_PT_OVER = "travel_pt_over"
    TRAVEL_OTHER = "travel_other"
    TRAVEL_OTHER_OVER = "travel_other_over"
    TRAVEL_BEYOND = "travel_beyond"
    TRAVEL_ESTIMATED = "travel_estimated"
    STATION = "station"
    STATION_NEARBY = "station_nearby"
    MISSING = "missing"
    MISSING_JOURNEY = "missing_journey"
    LIKENESS = "likeness"
    LIKENESS_SAME = "likeness_same"


class SentenceOrigin(StrEnum):
    TEMPLATE = "template"
    MODEL = "model"


class VerdictReason(StrEnum):
    """Why a sentence passed or failed. A code, never the text that failed."""

    OK = "ok"
    UNKNOWN_FACT = "unknown_fact"
    UNSUPPORTED_NUMBER = "unsupported_number"
    VAGUE_QUANTITY = "vague_quantity"
    UNSUPPORTED_NAME = "unsupported_name"
    BANNED_WORD = "banned_word"


class SentenceRole(StrEnum):
    ORIENTATION = "orientation"
    REASON = "reason"
    TRADE_OFF = "trade_off"
    MISSING = "missing"


class InterpretStatus(StrEnum):
    """In the order that decides the status: the first that applies wins."""

    OFF_TOPIC = "off_topic"
    POLICY_REDIRECT = "policy_redirect"
    CLARIFY = "clarify"
    # Nothing was applied, and what was noticed is offered for the person to choose.
    SUGGEST = "suggest"
    OK = "ok"


class SuggestionDirection(StrEnum):
    """What a person may choose of a thing the reader noticed. It never guesses one."""

    MORE = "more"
    LESS = "less"
    IGNORE = "ignore"


class Notice(StrEnum):
    NONE = "none"
    NEUTRAL_PLACES = "neutral_places"
    OFF_TOPIC = "off_topic"


class InterpreterName(StrEnum):
    RULE = "rule"
    MODEL = "model"


class UnmetCategory(StrEnum):
    BROADBAND = "broadband"
    FLOOD_RISK = "flood_risk"
    HEALTH_SERVICES = "health_services"
    DRIVING = "driving"
    LISTINGS = "listings"
    AFFORDABILITY_VERDICT = "affordability_verdict"
    COMMUNITY_AMENITIES = "community_amenities"
    OUTSIDE_THE_CITY = "outside_the_city"
    # What no open data measures at the scale of a neighbourhood.
    STREET_CLEANLINESS = "street_cleanliness"
    UPKEEP = "upkeep"
    RATINGS = "ratings"
    PRICES_AND_HOURS = "prices_and_hours"
    MOBILE_COVERAGE = "mobile_coverage"
    CHANGE_OVER_TIME = "change_over_time"
    OTHER = "other"


class AssumptionCode(StrEnum):
    TENURE = "tenure"
    SEGMENT = "segment"
    STRICTNESS = "strictness"
    MODE = "mode"
    MAX_MINUTES = "max_minutes"
    DIRECTION = "direction"
    WEIGHT = "weight"
    # A word with two meanings was read as its place part alone. The word is quoted.
    WORD = "word"


class OptionKind(StrEnum):
    """What a clarification offers: a place of one of the kinds of 2.7, or an area."""

    STATION = "station"
    DISTRICT = "district"
    POSTCODE_DISTRICT = "postcode_district"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    LANDMARK = "landmark"
    AREA = "area"


RENT_SEGMENTS = (
    Segment.ROOM,
    Segment.STUDIO,
    Segment.BED_1,
    Segment.BED_2,
    Segment.BED_3,
    Segment.BED_4PLUS,
)
BUY_SEGMENTS = (Segment.FLAT, Segment.TERRACED, Segment.SEMI_DETACHED, Segment.DETACHED)


def segments_for(tenure: Tenure) -> tuple[Segment, ...]:
    return RENT_SEGMENTS if tenure is Tenure.RENT else BUY_SEGMENTS


def component_for_feature(feature_id: FeatureId) -> str:
    return f"feature:{feature_id}"


def component_for_tag(tag_id: TagId) -> str:
    return f"tag:{tag_id}"


COMMUTE = "commute"
BUDGET = "budget"
