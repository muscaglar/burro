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
from burro_core.census import CensusOffer
from burro_core.explain import Explanation
from burro_core.facts import Fact
from burro_core.ids import (
    AreaId,
    Family,
    GrittyVariant,
    InterpreterName,
    InterpretStatus,
    Notice,
    PlaceId,
    PlaceKind,
    ReleaseId,
    SuggestionDirection,
    TagId,
    UnmetCategory,
)
from burro_core.interpret import (
    MAX_TEXT,
    Assumption,
    Clarify,
    ClarifyOption,
    NotInRelease,
    RestsOn,
    Span,
)
from burro_core.ops import Operations
from burro_core.portrait import Portrait
from burro_core.rank import Filtered, RankedArea, Unranked
from burro_core.reducer import Applied, Rejected
from burro_core.release import (
    Band,
    CostEstimate,
    Counts,
    Cutoffs,
    FeatureValue,
    Geometry,
    Metric,
    Neighbourhood,
    Point,
    RecipeHeld,
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

from burro_api.providers.terms import Provider

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
    # True for a release that is not finished. It travels with every response too, so
    # that nothing built for the people who make Burro can be taken for what is launched.
    preview: bool


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
    CENSUS_NOT_AVAILABLE = "census_not_available"


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
    right one. A model's answer is held to the same rule (`reader.ModelOutput`),
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
    # `false` asks for what the rules make of the text, at once, and no model
    # is asked. The answer says whether a model has more to read
    # (`model_pending`), and a client that wants it asks again with `true`.
    # So what the rules offer never waits on a model.
    ask_model: StrictBool = True
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


class NamedPlace(Wire):
    """A place a spec names, by the release's own name for it. Never what was typed.

    A spec holds a `place_id` and no name. A name says where someone works as
    an id does, so it is handled as one: served in a body, and in no log.
    """

    place_id: PlaceId
    name: str
    kind: PlaceKind


class SuggestionChoice(Wire):
    """One way a person may take an offer, and the edits it would make.

    It has a name of its own here because core has another `Choice`, what a
    setting is set to, and one document cannot hold two records of one name.
    """

    # Which way of its offer this is. It is unlike every other of the same
    # offer, and a client tells two ways apart by it and by nothing else.
    id: str
    # `ignore` is doing nothing, and is always last.
    direction: SuggestionDirection
    # The words on the button. Text of Burro's own, never the person's words.
    label: str
    # The way Burro reads the words, where a model read them and no check
    # fired. It is a mark on the choice. Nothing is applied until it is pressed.
    guess: bool
    # What is sent to route 2 if it is chosen. Every edit is `ui_edit`.
    operations: Operations


class Suggestion(Wire):
    """An offer: a thing that was noticed, in four parts. The person chooses.

    What it would do (`does`), the person's own words (`spans`, shown within
    `shown`), what follows for areas (`follows`), and the choices. Every word
    is Burro's own. The person's words are never here: a client cuts them
    from the text it holds, by where they stand.
    """

    # `feature:<id>`, `tag:<id>`, `budget`, `tenure`, `commute` or `area`.
    target: str
    # The short label of the thing, or the release's name of the place or the area.
    label: str
    # What it would do, which begins with a verb. Where Burro has no guess and
    # the thing runs more than one way, it is a question.
    does: str
    # Where the words it rests on stand in the text as it was sent. Offsets, never words.
    spans: tuple[Span, ...]
    # The stretch of the text to show under "You wrote": the clause the words
    # stand in, or the whole sentence. `spans` lie within it.
    shown: Span
    # What follows for areas if it is taken: which rank higher, and which are left out.
    follows: str
    # What the person did not say, and what Burro took: "You named no way of
    # travelling: Burro took public transport."
    said: tuple[str, ...]
    # `ignore` is always last.
    choices: tuple[SuggestionChoice, ...]
    # What a person should know before they choose, in fixed words of core's
    # own. Empty where there is nothing to add.
    note: str
    # Who noticed the thing: the rules, or a model alone.
    read_by: InterpreterName
    # The way that "add all" takes, by its `id`. Empty where it may take none:
    # what leaves areas out, what runs two ways with no guess, a journey to a
    # place that is yet to be chosen, and recorded crime.
    add_all: str
    # What is left for the person once "add all" has been pressed. Empty
    # where nothing is.
    needs: str
    # The journey is to a place the release does not hold. The ways hold no
    # place: a client puts in the id of the place the person chooses.
    asks_place: bool
    # Where the name of that place stands in the text, or `null`.
    named_at: Span | None
    # What the release holds that the name may mean. Empty where nothing is alike.
    options: tuple[ClarifyOption, ...]


class UnmetAt(Wire):
    """Something that was asked for which nothing measures, and where it was said."""

    category: UnmetCategory
    # Where the words stand in the text as it was sent. Offsets, never words.
    span: Span


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
    # True when that was because the provider would not read what was typed,
    # for safety or for its own terms. A client says so in one line.
    model_refused: bool
    # Which words of `text` each edit rests on, as offsets into the text as it
    # was sent, counted in code points. Offsets and never words: the sender
    # holds the text, and nothing here stores or logs where in it a wish stood.
    rests_on: tuple[RestsOn, ...]
    # What was noticed in a prompt that is not plain, for the person to choose
    # from. Its spans are offsets as `rests_on` holds them. Empty for a plain prompt.
    suggestions: tuple[Suggestion, ...]
    # Each stretch of the text that nothing was made of, as offsets, in order.
    unread: tuple[Span, ...]
    # What was asked for that the release holds for no area: a vibe no area has
    # a band for, a measure it does not carry, a budget where it holds no cost,
    # a journey where it names no place. Each is named, with where its words
    # stand, and none is applied or offered. Empty where nothing is missing.
    not_in_release: tuple[NotInRelease, ...]
    # Where the words stand that ask for what nothing measures, where a reader
    # said which they are. Every category here is in `unmet` too.
    unmet_at: tuple[UnmetAt, ...]
    # True where the rules answered at once, as they were asked to, and a
    # model has more to read. A client asks again to have it.
    model_pending: bool
    # One for each commute of `spec`, in the spec's order.
    places: tuple[NamedPlace, ...]


class Score(Wire):
    area_id: AreaId
    score: float
    # How many things count in the spec, and for how many the area has a figure.
    counted: int
    present: int


class Ranking(Wire):
    # Every ranked area in rank order, to colour a map with.
    scores: tuple[Score, ...]
    # The first `limit` in full.
    ranked: tuple[RankedArea, ...]
    # How many areas are ranked, and how many of them `ranked` holds. Where
    # the second is less, areas stand below the last one listed, and a client
    # says so: a list once stopped at 20 of 22 and said nothing.
    areas_ranked: int
    areas_listed: int
    # What a filter left out, and what is listed apart for want of data, each with its reason.
    filtered: tuple[Filtered, ...]
    unranked: tuple[Unranked, ...]
    empty_spec: bool


class RankData(Ranking):
    spec: PreferenceSpec
    spec_hash: str
    applied: tuple[Applied, ...]
    rejected: tuple[Rejected, ...]
    # One for each commute of `spec`, in the spec's order.
    places: tuple[NamedPlace, ...]


class ExplanationsData(Wire):
    # The hash of the spec the sentences were written for, which is the spec as sent.
    spec_hash: str
    explanations: tuple[Explanation, ...]
    # Every fact a sentence cites, and the `tag` fact of every mark on the
    # strip of an area that is explained, each with its source and its date.
    facts: tuple[Fact, ...]


class AreaSummary(Wire):
    area_id: AreaId
    slug: str
    name: str
    borough: str
    centroid: Point
    rankable: bool


class BandMark(Wire):
    """Where one area sits on one vibe: a band, one of five, and the bands it spans.

    All three are `null` for an area that cannot be placed. It is never drawn
    in the middle. The score a vibe is ranked on is not here, and is never shown.
    """

    area_id: AreaId
    band: Band | None
    spread_low: Band | None
    spread_high: Band | None


class VibeBands(Wire):
    tag_id: TagId
    # One for each area of the release, by id.
    marks: tuple[BandMark, ...]


class AreasData(Wire):
    areas: tuple[AreaSummary, ...]
    # One for each vibe the release lets a map be coloured by, in shelf order.
    # It is one answer for every vibe, so the service is never told which was pressed.
    bands: tuple[VibeBands, ...]


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


class Similar(Wire):
    """One of the areas most like this one. The sentence is in the `likeness` fact it names."""

    area_id: AreaId
    fact_id: str


class AreaData(Wire):
    area: Neighbourhood
    features: tuple[FeatureValue, ...]
    tags: tuple[TagValue, ...]
    cost: tuple[CostEstimate, ...]
    stations: tuple[StationAccess, ...]
    neighbours: tuple[AreaSummary, ...]
    # Where the area sits on every vibe. Built with no spec, so it is the same for everyone.
    portrait: Portrait
    # Five at most, most alike first. Empty where too little is known of the area.
    similar: tuple[Similar, ...]
    # Built with no spec: what a profile page needs. It holds a `tag` fact
    # for every vibe, and the `likeness` fact of each area in `similar`.
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
    CHARACTER_UNKNOWN = "character_unknown"


class ComparedArea(Wire):
    area_id: AreaId
    name: str
    status: CompareStatus
    # As on a `Score`. Both are 0 for an area that is not ranked: it was not scored.
    counted: int
    present: int


class CompareCell(Wire):
    area_id: AreaId
    # The feature's value, the minutes of the journey of the row, or the upper
    # quartile. `null` where there is none: nothing is filled in.
    value: float | None
    # The feature's percentile. `null` for a journey, a budget and a vibe: a
    # vibe is shown as a band, which is in `character`.
    percentile: float | None
    # `null` for an area that is not ranked. For a journey it is what that
    # journey is worth, and `null` where it has no time.
    utility: float | None
    # `null` for an area that is not ranked. The journeys add one figure
    # between them: it stands beside the journey that drove the score, and
    # in no cell where every journey counts.
    contribution: float | None
    # The fact that carries the source and the date of the numbers in this
    # cell, or that says there is no figure. For a journey with no time it is
    # the `missing` fact of that journey.
    fact_id: str | None


class CompareRow(Wire):
    """One thing that counts, across the areas. The journeys have a row each.

    Every cell of a journey's row is to the same place. The row is named as
    core keys a journey, `commute.<place_id>.<mode>`, and carries the weight
    of the journeys, which count as one thing between them.
    """

    component: str
    label: str
    weight: float
    # Where the journey of this row is to. `null` for a row that is no journey.
    place: NamedPlace | None
    cells: tuple[CompareCell, ...]


class CharacterMark(BandMark):
    # The `tag` fact that holds the sentence, the sources and the date. An
    # area that cannot be placed has one too, which says so.
    fact_id: str


class CharacterRow(Wire):
    tag_id: TagId
    # One for each area compared, in the order they were asked for.
    marks: tuple[CharacterMark, ...]


class CompareData(Wire):
    areas: tuple[ComparedArea, ...]
    # One for each vibe the release lets a comparison show, in shelf order.
    character: tuple[CharacterRow, ...]
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
    # One for each commute of the spec as stored: the place that stands in, where one does.
    places: tuple[NamedPlace, ...]


class ShareData(Ranking):
    """A shared search, ranked now on the release that is loaded."""

    spec: PreferenceSpec
    spec_hash: str
    coarsened: bool
    # True when the release loaded now is not the one the share was made on.
    stale: bool
    original_release_id: ReleaseId
    places: tuple[NamedPlace, ...]


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
    # What a thing must be worth to be given as a reason, and what it must be
    # worth less than to be given as a trade-off. A client holds no copy of either.
    reason_min_utility: float
    trade_off_max_utility: float


class FamilyLabel(Wire):
    family: Family
    label: str


class Reader(Wire):
    """Who reads what a person types, and what people are told of it.

    It is how the service is set, and no part of the release. A client shows
    `notice` by the box before anything is typed, as it is served, and writes
    no provider's name or terms of its own.
    """

    # False where the rules read, and nothing typed is sent to a language model.
    model_reads: bool
    # The provider that reads, and the company as a person would know it.
    # Both `null` where no model reads.
    provider: Provider | None
    company: str | None
    # All that people are told, as one paragraph: whose language model reads
    # what is typed, what goes with it, that nothing private should be typed,
    # and that Burro keeps nothing of it. It says nothing of what the company
    # does with it.
    notice: str
    # The company's own page of terms, for a link beside the notice. `null`
    # where no model reads.
    terms_url: str | None
    # Whether the search settings go to the provider with the words.
    settings_sent: bool


class Holds(Wire):
    """What a release holds to answer a search with, apart from its measures and its vibes.

    A first build holds neither. A client then says so where a person would
    look for it, and offers no control that could only be turned away.
    """

    # Whether it names any place to reach, and so holds any journey.
    journeys: bool
    # Whether it holds what any kind of home costs, to rent or to buy.
    costs: bool


class MetaData(Wire):
    release_id: ReleaseId
    built_at: str
    synthetic: bool
    preview: bool
    engine_version: str
    catalogue_version: int
    counts: Counts
    holds: Holds
    attributions: tuple[Source, ...]
    features: tuple[Metric, ...]
    # The vibes this release carries, in the order of the shelf and then of "more".
    tags: tuple[Tag, ...]
    # One for each vibe of `tags`, in the same order: how much of its recipe
    # the release carries, whether any area has a band for it, and the parts
    # it waits on, by name.
    recipes: tuple[RecipeHeld, ...]
    # The groups of the settings, in the order they are shown.
    families: tuple[FamilyLabel, ...]
    # Which of the two ways gritty was built this release carries.
    gritty_variant: GrittyVariant
    defaults: Defaults
    limits: ServedLimits
    # Who reads what is typed. It is of the service as it is set, and the tag
    # of the route changes with it.
    reader: Reader
    # Whether census figures are served for the areas of this release, and the words of
    # the block that offers them. It holds no figure and names no area.
    census: CensusOffer


class Health(Wire):
    ok: bool
