"""What travels over the wire: request bodies, the response envelope and each route's data.

Where a response holds a core record it is that record, so a field has one
name in core, on disk and on the wire. No list mixes types, because one
OpenAPI file has to generate a TypeScript client and a Swift one.

Everything a person typed arrives in a request body defined here, never in a
path or a query string, so it cannot reach an access log.
"""

from collections.abc import Mapping
from enum import StrEnum
from functools import cache
from typing import Annotated, Any, Literal, cast

from burro_core.catalogue import Tag
from burro_core.explain import Explanation
from burro_core.facts import Fact
from burro_core.ids import (
    AreaId,
    InterpreterName,
    InterpretStatus,
    Notice,
    PlaceId,
    PlaceKind,
    ReleaseId,
    UnmetCategory,
)
from burro_core.interpret import MAX_TEXT, Assumption, Clarify, RestsOn
from burro_core.ops import Operations
from burro_core.rank import Filtered, RankedArea, Unranked
from burro_core.reducer import Applied, Rejected
from burro_core.release import (
    CostEstimate,
    Counts,
    Cutoffs,
    FeatureValue,
    Geometry,
    Metric,
    Neighbourhood,
    Point,
    Source,
    StationAccess,
    TagValue,
)
from burro_core.spec import Limits, PreferenceSpec
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    PrivateAttr,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

MAX_BODY_BYTES = 16 * 1024
SHARE_ID_PATTERN = r"^[A-Za-z0-9_-]{22}$"


class Wire(BaseModel):
    """Frozen and closed to unknown fields, like a core record.

    A validation error never shows what failed to validate: it may be what a
    person typed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


# The envelope.


class Meta(Wire):
    release_id: ReleaseId
    engine_version: str
    # True for a synthetic release. It travels with every response, so that no
    # made-up figure can be taken for a fact about a real place.
    synthetic: bool


class Envelope[T](Wire):
    meta: Meta
    data: T


class ErrorCode(StrEnum):
    MALFORMED_JSON = "malformed_json"
    BODY_TOO_LARGE = "body_too_large"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    INTERNAL_ERROR = "internal_error"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    INVALID_REQUEST = "invalid_request"
    INVALID_TEXT = "invalid_text"
    INVALID_SPEC = "invalid_spec"
    INVALID_OPERATIONS = "invalid_operations"
    INVALID_COMPARE = "invalid_compare"
    INVALID_QUERY = "invalid_query"
    UNKNOWN_PLACE = "unknown_place"
    UNKNOWN_AREA = "unknown_area"
    AREA_NOT_FOUND = "area_not_found"
    SHARE_NOT_FOUND = "share_not_found"
    RELEASE_CHANGED = "release_changed"


class Problem(StrEnum):
    """What is wrong with one field. A code, never the value that was sent."""

    MISSING = "missing"
    UNKNOWN_FIELD = "unknown_field"
    WRONG_TYPE = "wrong_type"
    NOT_ALLOWED = "not_allowed"
    BAD_FORMAT = "bad_format"
    OUT_OF_RANGE = "out_of_range"
    INVALID = "invalid"
    # What only a release can decide: the problems of `check_spec`.
    UNKNOWN_PLACE = "unknown_place"
    UNKNOWN_AREA = "unknown_area"
    SEGMENT_NOT_FOR_TENURE = "segment_not_for_tenure"
    DIRECTION_NOT_ALLOWED = "direction_not_allowed"
    NOT_IN_RELEASE = "not_in_release"


class FieldProblem(Wire):
    # A path into the body, such as `spec.commutes[0].max_minutes`.
    path: str
    problem: Problem


class ErrorBody(Wire):
    code: ErrorCode
    # Fixed text for the code.
    message: str
    fields: tuple[FieldProblem, ...]


class ErrorEnvelope(Wire):
    meta: Meta
    error: ErrorBody


# Request bodies.

Schema = Mapping[str, Any]


class _NotANumber:
    """Stands where a boolean or a string was sent in a number's place.

    No number can be read from it, so the field is refused where it stands,
    with every other problem of the body, by the one validator there is.
    """


_NOT_A_NUMBER = _NotANumber()
_NUMBERS = frozenset({"integer", "number"})


def _numbers_kept(value: object, schema: Schema, definitions: Schema) -> object:
    """`value`, with anything that is not a number taken out of a number's place.

    It is read beside the body's own schema, so it holds for every field of
    every record in a body, the records of core included, and for a field
    that is added later.
    """
    if "$ref" in schema:
        schema = definitions[str(schema["$ref"]).rsplit("/", 1)[-1]]
    # A field that may be left empty: a number, or `null`.
    for choice in schema.get("anyOf", []):
        value = _numbers_kept(value, choice, definitions)
    kind = schema.get("type")
    if kind in _NUMBERS:
        return _NOT_A_NUMBER if isinstance(value, bool | str) else value
    if kind == "object":
        return _fields_kept(value, schema.get("properties", {}), definitions)
    if kind == "array" and "items" in schema:
        return _items_kept(value, schema["items"], definitions)
    return value


def _fields_kept(value: object, fields: Schema, definitions: Schema) -> object:
    if not isinstance(value, dict):
        return value
    return {
        name: _numbers_kept(held, fields[name], definitions) if name in fields else held
        for name, held in cast(dict[str, object], value).items()
    }


def _items_kept(value: object, items: Schema, definitions: Schema) -> object:
    if not isinstance(value, list):
        return value
    return [_numbers_kept(held, items, definitions) for held in cast(list[object], value)]


@cache
def _schema_of(body: type[BaseModel]) -> Schema:
    return body.model_json_schema()


class Body(Wire):
    """What a route takes. A number in it must be sent as a number.

    Left to itself the validator reads `true` as 1 and "0.5" as 0.5, so a
    client that sent the wrong type would be answered as if it had sent the
    right one. A model's answer is held to the same rule (`claude.ModelOutput`),
    and is no body of a route, so it is not among `BODIES`.
    """

    @model_validator(mode="before")
    @classmethod
    def _numbers_are_numbers(cls, data: object) -> object:
        schema = _schema_of(cls)
        return _numbers_kept(data, schema, schema.get("$defs", {}))


Limit20 = Annotated[int, Field(ge=1, le=100)]


def _typed(shortest: int, longest: int) -> StringConstraints:
    # Measured without the space around it, so that a line of spaces is an
    # empty line, and is refused before a model is asked to read it.
    return StringConstraints(strip_whitespace=True, min_length=shortest, max_length=longest)


class InterpretBody(Body):
    text: Annotated[str, _typed(1, MAX_TEXT)]
    # The spec to edit. A first prompt sends none and edits the renter's default.
    spec: PreferenceSpec | None = None
    # How many characters of white space stood before the text as it was sent.
    # It is a number and no part of the text, and it is never served or logged.
    _lead: int = PrivateAttr(default=0)

    @model_validator(mode="wrap")
    @classmethod
    def _where_the_text_begins(
        cls, data: object, handler: ModelWrapValidatorHandler["InterpretBody"]
    ) -> "InterpretBody":
        made = handler(data)
        sent = cast(dict[str, object], data).get("text") if isinstance(data, dict) else None
        if isinstance(sent, str):
            # The text is read without the space around it. What is left begins
            # with a character that is not space, so it is first found where it began.
            made._lead = max(sent.find(made.text), 0)
        return made

    @property
    def lead(self) -> int:
        """Where the text that is read begins in the text that was sent.

        The words an edit rests on are given as offsets into the text as it
        was sent, so a client can mark them in what the person typed without
        knowing what the service left out.
        """
        return self._lead


class RankBody(Body):
    spec: PreferenceSpec
    # What a slider or a chip changed. Applied by the one reducer before ranking.
    operations: Operations | None = None
    limit: Limit20 = 20


class ExplanationsBody(Body):
    spec: PreferenceSpec
    limit: int = Field(default=3, ge=1, le=5)


class CompareBody(Body):
    area_ids: tuple[AreaId, ...] = Field(min_length=2, max_length=4)
    spec: PreferenceSpec

    @field_validator("area_ids", mode="after")
    @classmethod
    def _no_repeats(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("area_ids repeats")
        return value


class PlaceSearchBody(Body):
    q: Annotated[str, _typed(2, 80)]
    limit: int = Field(default=8, ge=1, le=10)


class ShareBody(Body):
    spec: PreferenceSpec
    # A shared search names a station or a district in place of a workplace or
    # a school, unless the sender asks for the exact places.
    exact_destinations: StrictBool = False


# Every body a route takes, for what must hold of them all.
BODIES: tuple[type[Body], ...] = (
    InterpretBody,
    RankBody,
    ExplanationsBody,
    CompareBody,
    PlaceSearchBody,
    ShareBody,
)


# Response data, one record for each route.


class InterpretData(Wire):
    status: InterpretStatus
    operations: Operations
    # The spec after the reducer has applied `operations`.
    spec: PreferenceSpec
    spec_hash: str
    applied: tuple[Applied, ...]
    rejected: tuple[Rejected, ...]
    assumptions: tuple[Assumption, ...]
    unmet: tuple[UnmetCategory, ...]
    clarify: tuple[Clarify, ...]
    notice: Notice
    notice_text: str
    interpreter: InterpreterName
    # True when a model was asked and the rules answered in its place.
    degraded: bool
    # Which words of `text` each edit rests on, as offsets into the text as it
    # was sent, counted in code points. Offsets and never words: the sender
    # holds the text, and nothing here stores or logs where in it a wish stood.
    rests_on: tuple[RestsOn, ...]


class Score(Wire):
    area_id: AreaId
    score: float


class Ranking(Wire):
    # Every ranked area in rank order, to colour a map with.
    scores: tuple[Score, ...]
    # The first `limit` in full.
    ranked: tuple[RankedArea, ...]
    filtered: tuple[Filtered, ...]
    unranked: tuple[Unranked, ...]
    empty_spec: bool


class RankData(Ranking):
    spec: PreferenceSpec
    spec_hash: str
    applied: tuple[Applied, ...]
    rejected: tuple[Rejected, ...]


class ExplanationsData(Wire):
    explanations: tuple[Explanation, ...]
    # Every fact a sentence cites, with its source and its date.
    facts: tuple[Fact, ...]


class AreaSummary(Wire):
    area_id: AreaId
    slug: str
    name: str
    borough: str
    centroid: Point
    rankable: bool


class AreasData(Wire):
    areas: tuple[AreaSummary, ...]


class GeoProperties(Wire):
    area_id: AreaId


class GeoFeature(Wire):
    type: Literal["Feature"]
    id: AreaId
    properties: GeoProperties
    geometry: Geometry


class GeometryData(Wire):
    """A GeoJSON `FeatureCollection`, as `geometry.json` holds it."""

    type: Literal["FeatureCollection"]
    features: tuple[GeoFeature, ...]


class AreaData(Wire):
    area: Neighbourhood
    features: tuple[FeatureValue, ...]
    tags: tuple[TagValue, ...]
    cost: tuple[CostEstimate, ...]
    stations: tuple[StationAccess, ...]
    neighbours: tuple[AreaSummary, ...]
    # Built with no spec: what a profile page needs.
    facts: tuple[Fact, ...]


class CompareStatus(StrEnum):
    """`ranked`, or the reason the area was filtered or left unranked.

    One enum and not a union of three, so that a generated client gets one
    type. A test holds it to `FilterReason` and `UnrankedReason`.
    """

    RANKED = "ranked"
    EXCLUDED = "excluded"
    NOT_SELECTED = "not_selected"
    OVER_BUDGET = "over_budget"
    COMMUTE_CAP = "commute_cap"
    NOT_RANKABLE = "not_rankable"
    INSUFFICIENT_DATA = "insufficient_data"


class ComparedArea(Wire):
    area_id: AreaId
    name: str
    status: CompareStatus


class CompareCell(Wire):
    area_id: AreaId
    # The feature's value, the minutes of the journey that drove the score, or
    # the upper quartile. `null` where there is none: nothing is filled in.
    value: float | None
    percentile: float | None
    # `null` for an area that is not ranked.
    utility: float | None
    contribution: float | None
    # The fact that carries the source and the date of the numbers in this cell.
    fact_id: str | None


class CompareRow(Wire):
    component: str
    label: str
    weight: float
    cells: tuple[CompareCell, ...]


class CompareData(Wire):
    areas: tuple[ComparedArea, ...]
    # Ordered by the spec's weights from high to low, then by component name.
    rows: tuple[CompareRow, ...]
    facts: tuple[Fact, ...]


class FoundPlace(Wire):
    place_id: PlaceId
    name: str
    kind: PlaceKind
    # The station or district that stands in for this place in a shared link.
    coarse_name: str


class PlacesData(Wire):
    places: tuple[FoundPlace, ...]


class ShareCreated(Wire):
    share_id: str = Field(pattern=SHARE_ID_PATTERN)
    # The spec as it was stored, which is what the link will show.
    spec: PreferenceSpec
    # True when a destination was replaced by its coarse place, or dropped.
    coarsened: bool


class ShareData(Ranking):
    """A shared search, ranked now on the release that is loaded."""

    spec: PreferenceSpec
    spec_hash: str
    coarsened: bool
    # True when the release loaded now is not the one the share was made on.
    stale: bool
    original_release_id: ReleaseId


class Defaults(Wire):
    rent: PreferenceSpec
    buy: PreferenceSpec


class ServedLimits(Limits):
    """The limits of section 5.2, with the cutoffs of the release that is loaded.

    A form that keeps to these never offers a value the reducer would refuse.
    """

    cutoff_minutes: Cutoffs
    max_text: int
    max_body_bytes: int


class MetaData(Wire):
    release_id: ReleaseId
    built_at: str
    synthetic: bool
    engine_version: str
    catalogue_version: int
    counts: Counts
    attributions: tuple[Source, ...]
    features: tuple[Metric, ...]
    tags: tuple[Tag, ...]
    defaults: Defaults
    limits: ServedLimits


class Health(Wire):
    ok: bool
