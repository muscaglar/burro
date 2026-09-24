"""The vocabulary: every id and every enum the rest of Burro may use.

`FeatureId` and `TagId` are the allowlist of ADR 0006. An edit, a spec, a model
or a fact can name nothing that is not a member, so a feature describing who
lives somewhere cannot be asked for: there is no id for it.
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


class TagId(StrEnum):
    VILLAGE_FEEL = "village_feel"
    BUZZY = "buzzy"
    LEAFY = "leafy"
    CREATIVE = "creative"
    FAMILY_AMENITIES = "family_amenities"
    NEAR_UNIVERSITIES = "near_universities"
    WATERSIDE = "waterside"
    STRONG_HIGH_STREET = "strong_high_street"
    EVENING_VENUES = "evening_venues"
    QUIET_RESIDENTIAL = "quiet_residential"
    FOODIE = "foodie"
    HISTORIC_CHARACTER = "historic_character"


class Dimension(StrEnum):
    CRIME = "crime"
    SCHOOLS = "schools"
    GREEN_WATER = "green_water"
    AIR_NOISE = "air_noise"
    VENUES_CULTURE = "venues_culture"
    HOMES = "homes"
    STATION_ACCESS = "station_access"


class Polarity(StrEnum):
    LESS = "less"  # lower is better
    MORE = "more"  # higher is better
    EITHER = "either"  # the user chooses


class NativeResolution(StrEnum):
    OA = "oa"
    LSOA = "lsoa"
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
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


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


class PlaceKind(StrEnum):
    """In the order that breaks a tie between two matches of the same score."""

    STATION = "station"
    DISTRICT = "district"
    POSTCODE_DISTRICT = "postcode_district"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    LANDMARK = "landmark"


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


class UnrankedReason(StrEnum):
    NOT_RANKABLE = "not_rankable"
    INSUFFICIENT_DATA = "insufficient_data"


class FactKind(StrEnum):
    AREA = "area"
    FEATURE = "feature"
    TAG = "tag"
    COST = "cost"
    BUDGET_FIT = "budget_fit"
    TRAVEL = "travel"
    STATION = "station"
    MISSING = "missing"


class TemplateId(StrEnum):
    AREA = "area"
    FEATURE = "feature"
    FEATURE_CRIME = "feature_crime"
    TAG = "tag"
    COST_RENT = "cost_rent"
    COST_BUY = "cost_buy"
    BUDGET_UNDER = "budget_under"
    BUDGET_OVER = "budget_over"
    TRAVEL_PT = "travel_pt"
    TRAVEL_OTHER = "travel_other"
    TRAVEL_BEYOND = "travel_beyond"
    STATION = "station"
    STATION_NEARBY = "station_nearby"
    MISSING = "missing"


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
    OK = "ok"


class Notice(StrEnum):
    NONE = "none"
    NEUTRAL_PLACES = "neutral_places"
    OFF_TOPIC = "off_topic"


class InterpreterName(StrEnum):
    RULE = "rule"
    CLAUDE = "claude"


class UnmetCategory(StrEnum):
    BROADBAND = "broadband"
    FLOOD_RISK = "flood_risk"
    HEALTH_SERVICES = "health_services"
    DRIVING = "driving"
    LISTINGS = "listings"
    AFFORDABILITY_VERDICT = "affordability_verdict"
    COMMUNITY_AMENITIES = "community_amenities"
    OUTSIDE_THE_CITY = "outside_the_city"
    OTHER = "other"


class AssumptionCode(StrEnum):
    TENURE = "tenure"
    SEGMENT = "segment"
    STRICTNESS = "strictness"
    MODE = "mode"
    MAX_MINUTES = "max_minutes"
    DIRECTION = "direction"
    WEIGHT = "weight"


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
