"""Interpreters: from what a person typed to typed edits.

`RuleInterpreter` needs no model and no network, so the product still works as
a form when a model is slow, capped or absent. It reads the text, produces
edits, and keeps none of the words: assumptions and unmet requests are codes,
notices are fixed text, and every label comes from the catalogue or the
release.

It asks when it is not sure. It applies a prompt by itself only when the whole
of it is plain: a list of things wanted or not wanted, with an optional
opening, a budget and a journey to a place named in full (`grammar.py`). For
any other prompt it applies nothing. It offers what it noticed as
suggestions, each with the directions a person may choose, and says which
stretches of the text it made nothing of. The person chooses. The reader
never guesses a direction, so it never reads a wish backwards (ADR 0012).

Every edit and every suggestion says which words of the text it rests on, by
where they start and end. Nothing here keeps the words.

Burro ranks places first. Of who lives somewhere it counts their age and their
households, at Census 2021, and a phrase for either is offered, towards more
of what is counted, and never applied. Any other request about who lives
somewhere, and any wish for fewer of anyone, gets one neutral sentence and no
edit: no id exists that could express the first, and nothing reads the second.
"""

import dataclasses
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from typing import NamedTuple, Protocol

from burro_core._record import Record
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    CRIME_CAVEAT,
    FEATURES,
    HOLDS_CRIME,
    HOLDS_RESIDENTS,
    TAGS,
)
from burro_core.facts import SEGMENT_LABELS, money
from burro_core.grammar import (
    A_HOME,
    A_JOURNEY,
    AT_WORK,
    BEDROOMS,
    BUY_SEGMENTS,
    BUYS,
    EXPECTS_A_NAME,
    GOES,
    GOES_TO,
    KNOWN_WORDS,
    MONTHLY,
    MUST_BE_READ,
    REACHES,
    RENT_SEGMENTS,
    RENTS,
    TO_A_PLACE,
    TURNS,
    VOCABULARY,
    Grammar,
    Home,
    Kind,
    NotPlain,
    Way,
    Wish,
    about_a_campus,
)
from burro_core.ids import (
    AreaAction,
    AssumptionCode,
    BudgetAction,
    CommuteAction,
    Dimension,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    FeatureKind,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    OpsGroup,
    OptionKind,
    PlaceKind,
    Polarity,
    Provenance,
    RejectReason,
    Segment,
    SegmentChoice,
    Step,
    StrictnessChoice,
    SuggestionDirection,
    TagId,
    TagShape,
    Tenure,
    TenureChoice,
    Toward,
    TowardChoice,
    UnmetCategory,
    WeightAction,
)
from burro_core.lexicon import (
    COUNTED_AT_THE_CENSUS,
    GENERIC_PLACES,
    LEXICON,
    POLICY_LEXICON,
    Target,
    counts_residents,
    prepare,
)
from burro_core.ops import (
    NO_OPERATIONS,
    AreaEdit,
    BudgetEdit,
    CommuteEdit,
    Operations,
    TagEdit,
    WeightEdit,
)
from burro_core.places import Match, Names
from burro_core.reading import MINUTES, Is, Item, Line, lines_of
from burro_core.reducer import Rejected, apply, given_way_spec
from burro_core.release import Release
from burro_core.spec import LIMITS, PreferenceSpec
from burro_core.vocabulary import (
    ARTICLE,
    CAPS,
    FIRM_OF_MINUTES,
    FIRM_OF_MONEY,
    GOOD,
    JOINS,
    NEAR_TO,
    PHRASES_OF_DOUBT,
    SPEAKER,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    TO_DO,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    WISH,
    WORDS_OF_DOUBT,
    WORDS_THAT_TURN_AWAY,
)

__all__ = [
    "GENERIC_PLACES",
    "LEXICON",
    "MAX_TEXT",
    "NOTICES",
    "POLICY_LEXICON",
    "SIGNS_OF_DOUBT",
    "VOCABULARY",
    "Assumption",
    "Choice",
    "Clarify",
    "ClarifyOption",
    "InterpretRequest",
    "InterpretResult",
    "Interpreter",
    "NotInRelease",
    "RestsOn",
    "RuleInterpreter",
    "SentenceRead",
    "Span",
    "Suggestion",
    "Usage",
    "assumptions_for",
    "may_ask_for_fewer",
    "not_in_release_of",
    "notice_text",
    "prepare",
    "sentences_of",
]

MAX_TEXT = 600

# What is said of every request about who lives somewhere that nothing is offered for: a
# wish to find a group that Burro does not count, and a wish for fewer of anyone.
_PLACES_NOT_PEOPLE = (
    "Burro ranks places by what is there. Of who lives in a place it counts only their age "
    "and their households, at the census of 2021, and you cannot ask for fewer of anyone."
)
NOTICES: Mapping[Notice, str] = {
    Notice.NONE: "",
    # The same for every group and every user.
    Notice.NEUTRAL_PLACES: f"{_PLACES_NOT_PEOPLE} The rest of your search has been applied.",
    Notice.OFF_TOPIC: (
        "Burro helps you choose where to live. Say what you want from a place, or use the form."
    ),
}
# What the neutral notice says where nothing that was typed changed the search.
# It is as fixed as the other, and the same for everyone.
NOTHING_CHANGED = f"{_PLACES_NOT_PEOPLE} Nothing you typed has changed your search."


def notice_text(notice: Notice, changed: bool) -> str:
    """The fixed text of a notice. `changed` is whether an edit of the answer changed the spec.

    "The rest of your search has been applied" is untrue where nothing was.
    """
    if notice is Notice.NEUTRAL_PLACES and not changed:
        return NOTHING_CHANGED
    return NOTICES[notice]


@dataclass(frozen=True, repr=False)
class InterpretRequest:
    text: str
    spec: PreferenceSpec  # the spec to edit; a default for a first prompt
    release: Release

    def __post_init__(self) -> None:
        if not 1 <= len(self.text) <= MAX_TEXT:
            raise ValueError(f"text must be 1 to {MAX_TEXT} characters")

    def __repr__(self) -> str:
        # The text is what a person typed. It must never reach a log by way of a repr.
        return "InterpretRequest(text=<hidden>)"


class Assumption(Record):
    """What was chosen for an edit because the text did not say."""

    code: AssumptionCode
    group: OpsGroup
    index: int
    # For the code `word`: the word with two meanings that was read as its place
    # part alone, as the lexicon spells it and never as it was typed. Empty for
    # every other code.
    word: str = ""


class ClarifyOption(Record):
    id: str
    name: str
    kind: OptionKind


class Clarify(Record):
    """An edit whose place or area could not be settled, and what to offer instead."""

    group: OpsGroup
    index: int
    options: tuple[ClarifyOption, ...]


class RestsOn(Record):
    """Which words of the text an edit rests on: where they start and end, never the words.

    `start` and `end` count the characters of the text as it was typed, as
    Python counts them, so `text[start:end]` is the words. An edit made of
    several parts, as a budget is of "renting", "2 bed" and "£1,500", has one
    of these for each part. They are for showing a person which of their
    words made each edit. Nothing stores or logs them.
    """

    group: OpsGroup
    index: int
    start: int
    end: int


class Span(Record):
    """A stretch of the text: where it starts and ends, counted as `RestsOn` counts."""

    start: int
    end: int


class Choice(Record):
    """One thing a person may choose of what the reader noticed, and the edits it would make."""

    direction: SuggestionDirection
    # What the choice is called. Text of Burro's own, never the person's words.
    label: str
    # What is sent to be ranked if it is chosen. Every edit is `ui_edit`: the
    # person pressed it. All six arrays are empty for `ignore`.
    operations: Operations


class Suggestion(Record):
    """A thing the reader noticed in a prompt that is not plain. The person chooses."""

    # `feature:<id>`, `tag:<id>`, `budget`, `tenure`, `commute` or `area`.
    target: str
    # The short label of the thing, or the release's name of the place or the area.
    label: str
    spans: tuple[Span, ...]
    # In the order more, less, ignore. `ignore` is always last.
    choices: tuple[Choice, ...]
    # What a person should know before they choose, in fixed words of Burro's
    # own: that a vibe counts recorded crime, or what Burro has no measure of
    # and what it offers in its place. Empty where there is nothing to add.
    note: str = ""


class NotInRelease(Record):
    """A thing a person asked for that the release holds for no area, so none is ranked on it.

    A vibe that no area has a band for, a measure the release does not carry,
    a budget where it holds no cost of that kind of home, a journey where it
    names no place. It is said, so that a person is told what is not there
    yet. It is never offered, and nothing stands in for it.
    """

    # `feature:<id>`, `tag:<id>`, `budget` or `commute`.
    target: str
    # The short label of the thing. Text of Burro's own, never the person's words.
    label: str
    # Where the words stand. Empty where an edit that was made by no words asked for it.
    spans: tuple[Span, ...]


class Usage(Record):
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


NO_USAGE = Usage(input_tokens=0, output_tokens=0, cache_read_tokens=0)


class InterpretResult(Record):
    status: InterpretStatus
    operations: Operations
    assumptions: tuple[Assumption, ...]
    unmet: tuple[UnmetCategory, ...]
    clarify: tuple[Clarify, ...]
    notice: Notice
    interpreter: InterpreterName
    degraded: bool
    usage: Usage
    # In the order of the six groups, then by edit, then by where the words stand.
    rests_on: tuple[RestsOn, ...] = ()
    # What was noticed in a prompt that is not plain, in the order it stands.
    # Empty for a plain prompt.
    suggestions: tuple[Suggestion, ...] = ()
    # Each stretch of the text that nothing was made of, in order. `unmet`
    # holds `other` exactly when this is not empty.
    unread: tuple[Span, ...] = ()
    # What was noticed in a prompt that is not plain and is not offered, because
    # the release holds it for no area. What an edit asks for and the release
    # lacks is the reducer's to say: `not_in_release_of` names both.
    not_in_release: tuple[NotInRelease, ...] = ()


class Interpreter(Protocol):
    name: InterpreterName

    def interpret(self, request: InterpretRequest) -> InterpretResult: ...


_STATED = EditProvenance.STATED
_INFERRED = EditProvenance.INFERRED
_UI = EditProvenance.UI_EDIT
_Edit = BudgetEdit | CommuteEdit | WeightEdit | TagEdit | AreaEdit
_Span = tuple[int, int]
_BEDS = (
    SegmentChoice.BED_1,
    SegmentChoice.BED_2,
    SegmentChoice.BED_3,
    SegmentChoice.BED_4PLUS,
)
_KINDS_OF_HOME = frozenset(RENT_SEGMENTS) | frozenset(BUY_SEGMENTS)
_HOMES = RENTS | BUYS | BEDROOMS | _KINDS_OF_HOME
# The words that expect the name of a place after them.
_CUES = EXPECTS_A_NAME | GOES_TO | REACHES | NEAR_TO
_BEFORE_A_NAME = frozenset({"the", "a", "an", "my", "our"})
# After a number of "m", it says the number is a distance: "1.5m away".
_AWAY = frozenset({"away"})
IGNORE = Choice(
    direction=SuggestionDirection.IGNORE, label="Leave it out", operations=NO_OPERATIONS
)
TAKE_OFF = "Take it off"
# What a budget and a journey are called where the release can answer neither.
A_BUDGET = "A budget"
A_JOURNEY_TO = "A journey"
BUDGET_TARGET = "budget"
COMMUTE_TARGET = "commute"


@dataclass
class _Made:
    """An edit a plain prompt made, and the words it rests on."""

    group: OpsGroup
    edit: _Edit
    spans: list[_Span]
    # It raises a weight or a vibe, as against lowering one or taking it off.
    raises: bool = True
    options: tuple[ClarifyOption, ...] | None = None
    # The word with two meanings that the edit was read from.
    word: str = ""
    # The minutes of a journey were given as a range, of which the longer was taken.
    # This is the shorter, and nothing where they were no range.
    at_least: int = 0


def _is_word(item: Item | None, among: frozenset[str]) -> bool:
    return item is not None and item.what is Is.WORD and item.text in among


def _after(items: Sequence[Item], at: int, cues: frozenset[str]) -> bool:
    """Whether some words stand straight before an item, with at most an article between."""
    while at > 0 and _is_word(items[at - 1], _BEFORE_A_NAME):
        at -= 1
    before = [item.text for item in items[max(at - 4, 0) : at] if item.what is Is.WORD]
    return any(" ".join(before[-size:]) in cues for size in (1, 2, 3, 4) if len(before) >= size)


def _cued(items: Sequence[Item], at: int) -> bool:
    """Whether the words before an item are ones that expect the name of a place."""
    if _after(items, at, _CUES):
        return True
    return _timed(items, at) and _minutes_before(items, at) > 0


# What may stand between a number of minutes and "to", "from" or "of": how the
# journey is made, "a 20 minute walk to", "35 minutes commute from".
_A_WAY_TO_GO = frozenset(GOES) | A_JOURNEY
_AT_WORK = frozenset(word for phrase in AT_WORK for word in phrase.split())


def _to_a_place(items: Sequence[Item], at: int) -> int | None:
    """Where "to", "from" or "of" stands before a place, with where the speaker works between.

    "30 minutes to", "20 minutes from my office at". `None` where no such
    word leads in to the place.
    """

    def beside(back: int) -> bool:
        """Whether nothing but a space stands between an item and the one after it."""
        return back + 1 >= len(items) or not items[back + 1].apart

    back = at - 1
    while back >= 0 and _is_word(items[back], _BEFORE_A_NAME) and beside(back):
        back -= 1
    if back >= 0 and _is_word(items[back], TO_A_PLACE) and beside(back):
        return back
    # Where the speaker works: "from work at", "of my office in".
    far = back
    while far >= 0 and _is_word(items[far], _AT_WORK) and beside(far):
        far -= 1
    said = " ".join(item.text for item in items[far + 1 : back + 1])
    led = far >= 0 and _is_word(items[far], TO_A_PLACE) and beside(far)
    return far if led and said in AT_WORK else None


def _timed(items: Sequence[Item], at: int) -> bool:
    return _to_a_place(items, at) is not None


def _number_before(items: Sequence[Item], at: int) -> Item | None:
    """The number said straight before a place: "30 minutes to", "within 25 mins of".

    How the journey is made may stand between them: "35 minutes commute from".
    """
    to = _to_a_place(items, at)
    if to is None:
        return None
    back = to - 1
    if back >= 0 and _is_word(items[back], _A_WAY_TO_GO) and not items[back + 1].apart:
        back -= 1
    if back >= 0 and _is_word(items[back], MINUTES) and not items[back + 1].apart:
        back -= 1
    number = items[back] if back >= 0 else None
    if number is None or number.what is not Is.NUMBER or number.money or items[back + 1].apart:
        return None
    return number


def _minutes_before(items: Sequence[Item], at: int) -> int:
    """The minutes said straight before a place, where they are minutes a journey may take."""
    number = _number_before(items, at)
    if number is None:
        return 0
    return number.value if LIMITS.minutes_min <= number.value <= LIMITS.minutes_max else 0


def _where_minutes_start(items: Sequence[Item], at: int) -> int:
    number = _number_before(items, at)
    return items[at].start if number is None else number.start


def _range_before(items: Sequence[Item], at: int) -> int:
    """The shorter of a range of minutes said straight before a place, or nothing."""
    number = _number_before(items, at)
    return number.low if number is not None and _minutes_before(items, at) else 0


@dataclass
class _Sentence:
    """One sentence, what it is made of, and what the grammar made of it."""

    line: Line
    items: list[Item]
    wishes: list[Wish] | None  # `None` where the grammar does not make the sentence
    asked: bool = False
    taken_back: bool = False

    @property
    def plain(self) -> bool:
        return self.wishes is not None

    @property
    def own(self) -> bool:
        """Whether the speaker says a wish of their own in it: "I want", "we need"."""
        return any(
            _is_word(first, SPEAKER.words) and _is_word(second, WISH.words)
            for first, second in pairwise(self.items)
        )

    @property
    def names(self) -> bool:
        """Whether it names something: a thing, a place, a number, a home, or what is unmet."""
        named = (Is.THING, Is.NAME, Is.PEOPLE, Is.AMENITY, Is.UNMET)
        return any(
            item.what in named
            or (item.what is Is.NUMBER and (item.money or bool(item.unit) or len(self.items) > 1))
            or _is_word(item, _HOMES)
            or _cued(self.items, at + 1)
            for at, item in enumerate(self.items)
        )


def _option(match: Match) -> ClarifyOption:
    return ClarifyOption(id=match.id, name=match.name, kind=match.kind)


# --- A plain prompt: every item makes the edit the contract gives it -----------------


def _weight_edits(wish: Wish, target: Target) -> Iterator[tuple[_Edit, bool]]:
    """The edits for a thing that was named, from what is said of it (contract 5.2, 8.2)."""
    way = wish.way
    turned = way in (Way.NOT_AT_ALL, Way.LESS)
    up = Step.UP_SMALL if wish.step is Step.UP_SMALL or way is Way.LESS else Step.UP_LARGE
    down = Step.DOWN_LARGE if wish.large else Step.DOWN_SMALL
    for feature_id in target.features:
        action, value, step, direction = WeightAction.NUDGE, 0.0, up, target.direction
        raises = True
        if way is Way.OFF:
            action, step, raises = WeightAction.REMOVE, Step.NONE, False
        elif way is Way.DOWN:
            step, raises = down, False
        elif turned and not target.nuisance:
            raises = False
            if FEATURES[feature_id].polarity is Polarity.EITHER:
                # Fewer of it is a taste in places, so it is a wish like any other.
                step, direction = Step.UP_LARGE, DirectionChoice.LESS
            else:
                # It never raises a weight. Wanted less, the weight is turned down.
                # Not wanted at all, it is taken off, so that a default stops
                # counting for a thing the person has said they do not want.
                step = Step.DOWN_SMALL if way is Way.LESS else Step.NONE
                action = WeightAction.NUDGE if way is Way.LESS else WeightAction.REMOVE
        elif wish.essential:
            action, value, step = WeightAction.SET, 1.0, Step.NONE
        yield (
            WeightEdit(
                action=action,
                feature_id=feature_id,
                value=value,
                step=step,
                direction=direction,
                provenance=target.provenance,
            ),
            raises,
        )
    for tag_id in target.tags:
        scale = TAGS[tag_id].shape is TagShape.SCALE
        action, value, step, raises = WeightAction.NUDGE, 0.0, up, True
        toward = TowardChoice(target.toward.value)
        if way is Way.OFF:
            action, step, raises = WeightAction.REMOVE, Step.NONE, False
            toward = TowardChoice.DEFAULT
        elif way is Way.DOWN:
            step, raises, toward = down, False, TowardChoice.DEFAULT
        elif turned and scale:
            # A turned end is the other end: "not buzzy" is Pace towards Calm.
            toward = TowardChoice.LOW if target.toward is Toward.HIGH else TowardChoice.HIGH
        elif turned:
            # A vibe with one direction can only be turned down, or taken off.
            step = Step.DOWN_SMALL if way is Way.LESS else Step.NONE
            action = WeightAction.NUDGE if way is Way.LESS else WeightAction.REMOVE
            raises, toward = False, TowardChoice.DEFAULT
        elif wish.essential:
            action, value, step = WeightAction.SET, 1.0, Step.NONE
        yield (
            TagEdit(
                action=action,
                tag_id=tag_id,
                value=value,
                step=step,
                toward=toward,
                provenance=target.provenance,
            ),
            raises,
        )


def _budget(home: Home, spec: PreferenceSpec) -> tuple[BudgetEdit, list[_Span]] | None:
    """The one budget edit a prompt makes, from everything it says of the home."""
    amount, hard, where = home.amounts[0] if home.amounts else (0, False, (0, 0))
    spans: list[_Span] = [where] if home.amounts else []
    tenure = TenureChoice.UNCHANGED
    if home.rents or home.buys:
        tenure = TenureChoice.RENT if home.rents else TenureChoice.BUY
        spans += home.rents or home.buys
    elif home.monthly:
        tenure = TenureChoice.RENT
        spans += home.monthly
    # A number alone says which it is: no rent is this high and no price this low.
    elif amount >= LIMITS.buy.minimum and spec.tenure is Tenure.RENT:
        tenure = TenureChoice.BUY
    elif 0 < amount <= LIMITS.rent.maximum and spec.tenure is Tenure.BUY:
        tenure = TenureChoice.RENT
    chosen = spec.tenure if tenure is TenureChoice.UNCHANGED else Tenure(tenure.value)
    segment = SegmentChoice.UNCHANGED
    # A price is published by the type of home and not by its bedrooms.
    beds = [(count, span) for count, span in home.bedrooms if count >= 1]
    if beds and chosen is Tenure.RENT:
        segment = _BEDS[min(beds[0][0], len(_BEDS)) - 1]
        spans.append(beds[0][1])
    kinds = RENT_SEGMENTS if chosen is Tenure.RENT else BUY_SEGMENTS
    for word, span in home.segments:
        if word in kinds and segment is SegmentChoice.UNCHANGED:
            segment = kinds[word]
            spans.append(span)
    if amount or tenure is not TenureChoice.UNCHANGED or segment is not SegmentChoice.UNCHANGED:
        edit = BudgetEdit(
            action=BudgetAction.SET,
            tenure=tenure,
            amount=amount,
            segment=segment,
            strictness=StrictnessChoice.HARD if hard else StrictnessChoice.UNCHANGED,
            step=Step.NONE,
            provenance=_STATED,
        )
        return edit, sorted(set(spans))
    for cheaper, much, span in home.steps[:1]:
        small, large = (
            (Step.DOWN_SMALL, Step.DOWN_LARGE) if cheaper else (Step.UP_SMALL, Step.UP_LARGE)
        )
        edit = BudgetEdit(
            action=BudgetAction.NUDGE,
            tenure=TenureChoice.UNCHANGED,
            amount=0,
            segment=SegmentChoice.UNCHANGED,
            strictness=StrictnessChoice.UNCHANGED,
            step=large if much else small,
            provenance=_STATED,
        )
        return edit, [span]
    return None


def _as_can_be_tested(
    edit: BudgetEdit, spans: list[_Span], amount_at: _Span | None, request: InterpretRequest
) -> list[tuple[BudgetEdit, list[_Span]]]:
    """The budget edit of a prompt, in two where the release cannot test its amount.

    An edit is applied whole or not at all. Where the release holds no cost
    of that kind of home, the one edit was turned away with all it held, and
    "buying a terraced house under £450k" left the search a renter's. What
    is said of the home is kept: to rent or to buy, and the kind of home.
    The amount is an edit of its own, which the reducer turns away, so that
    the person is told what is missing. Where the amount can be tested, or
    nothing else was said, it is one edit, as it always was.
    """
    unsaid = (TenureChoice.UNCHANGED, SegmentChoice.UNCHANGED)
    if edit.action is not BudgetAction.SET or not edit.amount or amount_at is None:
        return [(edit, spans)]
    if (edit.tenure, edit.segment) == unsaid:
        return [(edit, spans)]
    alone = NO_OPERATIONS.replace(budget_ops=(edit,))
    tried = apply(given_way_spec(request.spec), alone, request.release)
    if not any(turned.reason is RejectReason.NOT_IN_RELEASE for turned in tried.rejected):
        return [(edit, spans)]
    home = edit.replace(amount=0, strictness=StrictnessChoice.UNCHANGED)
    amount = edit.replace(tenure=unsaid[0], segment=unsaid[1])
    return [(home, [span for span in spans if span != amount_at]), (amount, [amount_at])]


def assumptions_for(operations: Operations, spec: PreferenceSpec) -> tuple[Assumption, ...]:
    """What each edit left to a default, so the person can see it and change it.

    Worked out from the edits and the spec they were made for, so every
    interpreter states the same assumptions for the same edits.
    """
    found: list[Assumption] = []

    def assume(code: AssumptionCode, group: OpsGroup, index: int) -> None:
        found.append(Assumption(code=code, group=group, index=index))

    nobody_chose = spec.budget.provenance is Provenance.DEFAULT
    # What an edit before it said of the home is not assumed of the amount:
    # a budget is made in two where its amount cannot be tested.
    tenure_said = segment_said = False
    for index, edit in enumerate(operations.budget_ops):
        if edit.action is not BudgetAction.SET:
            continue
        if edit.amount != 0:
            unsaid = edit.tenure is TenureChoice.UNCHANGED and not tenure_said
            if unsaid and spec.tenure_from is Provenance.DEFAULT:
                assume(AssumptionCode.TENURE, OpsGroup.BUDGET, index)
            moved = edit.tenure is not TenureChoice.UNCHANGED and edit.tenure.value != spec.tenure
            left = edit.segment is SegmentChoice.UNCHANGED and not segment_said
            if left and (nobody_chose or moved):
                assume(AssumptionCode.SEGMENT, OpsGroup.BUDGET, index)
            if edit.strictness is StrictnessChoice.UNCHANGED and nobody_chose:
                assume(AssumptionCode.STRICTNESS, OpsGroup.BUDGET, index)
        tenure_said = tenure_said or edit.tenure is not TenureChoice.UNCHANGED
        segment_said = segment_said or edit.segment is not SegmentChoice.UNCHANGED

    known = {commute.place_id for commute in spec.commutes}
    for index, commute in enumerate(operations.commute_ops):
        if commute.action is not CommuteAction.ADD or commute.place_id in known:
            continue
        if commute.mode is ModeChoice.UNCHANGED:
            assume(AssumptionCode.MODE, OpsGroup.COMMUTE, index)
        if commute.max_minutes == 0:
            assume(AssumptionCode.MAX_MINUTES, OpsGroup.COMMUTE, index)
        if commute.strictness is StrictnessChoice.UNCHANGED:
            assume(AssumptionCode.STRICTNESS, OpsGroup.COMMUTE, index)

    # A weight that was taken off is in the spec as an entry of nothing.
    weighted = {weight.feature_id for weight in spec.active_weights}
    for index, weight in enumerate(operations.weight_ops):
        if weight.action is WeightAction.REMOVE:
            continue
        if weight.provenance is EditProvenance.INFERRED:
            assume(AssumptionCode.WEIGHT, OpsGroup.WEIGHT, index)
        either = FEATURES[weight.feature_id].polarity is Polarity.EITHER
        unsaid = weight.direction is DirectionChoice.DEFAULT
        if either and unsaid and weight.feature_id not in weighted:
            assume(AssumptionCode.DIRECTION, OpsGroup.WEIGHT, index)
    for index, tag in enumerate(operations.tag_ops):
        if tag.action is not WeightAction.REMOVE and tag.provenance is EditProvenance.INFERRED:
            assume(AssumptionCode.WEIGHT, OpsGroup.TAG, index)
    return tuple(found)


def _about(made: _Made) -> tuple[OpsGroup, str]:
    """What an edit is about: a place, an area, a feature or a vibe, by its id."""
    edit = made.edit
    if isinstance(edit, CommuteEdit):
        return made.group, edit.place_id
    if isinstance(edit, AreaEdit):
        return made.group, edit.area_id
    if isinstance(edit, WeightEdit):
        return made.group, edit.feature_id.value
    if isinstance(edit, TagEdit):
        return made.group, edit.tag_id.value
    return made.group, ""


@dataclass
class _Read:
    """Everything a plain prompt said: the edits it makes, and what makes none."""

    made: list[_Made] = field(default_factory=list[_Made])
    home: Home = field(default_factory=Home)
    # Where the words of the home stand, for the day no edit can be made of them.
    home_spans: list[_Span] = field(default_factory=list[_Span])
    # Minutes said apart from any place, "a 40 minute commute on foot", each
    # with how they are travelled and whether they are a limit.
    loose: list[Wish] = field(default_factory=list[Wish])
    # What may not be applied for what it is: "safe", "a gym", "edgy".
    offered: list[Wish] = field(default_factory=list[Wish])
    # A journey to a place that may be where the person lives now, "I commute
    # from", which is offered and never applied.
    maybe: list[_Made] = field(default_factory=list[_Made])
    unmet: set[UnmetCategory] = field(default_factory=set[UnmetCategory])
    about_people: bool = False


def _read(wishes: Sequence[Wish]) -> _Read:
    found = _Read()
    for wish in wishes:
        if wish.kind is Kind.HOME:
            found.home.add(wish.home)
            found.home_spans += wish.spans
        elif wish.kind is Kind.PEOPLE:
            found.about_people = True
        elif wish.kind is Kind.NO_MEASURE:
            found.unmet |= set(wish.unmet)
        elif wish.kind is Kind.RULE:
            edit = AreaEdit(action=wish.action, area_id=wish.area_id, provenance=_STATED)
            found.made.append(_Made(OpsGroup.AREA, edit, wish.spans))
        elif wish.kind is Kind.JOURNEY and wish.loose:
            found.loose.append(wish)
        elif wish.kind is Kind.JOURNEY and wish.offered:
            found.maybe.append(_journey(wish))
        elif wish.kind is Kind.JOURNEY:
            found.made.append(_journey(wish))
        elif wish.kind is Kind.WISH and wish.offered:
            found.offered.append(wish)
        elif wish.kind is Kind.WISH and wish.target is not None:
            _wished(found, wish, wish.target)
    return found


def _left_to_choose(read: _Read) -> bool:
    """Whether a prompt holds a word that may not be applied, and names what it reaches nowhere.

    "Safe" names no crime, so it sets none counting: it is offered. Beside
    a wish that names the same thing outright, "safe, with low crime", the
    person has asked by name, and the word adds nothing to what they said.
    A place that is commuted from is always left to choose.
    """
    if read.maybe:
        return True
    named = {
        (*_about(made), getattr(made.edit, "toward", TowardChoice.HIGH))
        for made in read.made
        if made.raises and getattr(made.edit, "provenance", None) is _STATED
    }
    for wish in read.offered:
        target = wish.target
        assert target is not None
        toward = TowardChoice(target.toward.value)
        reaches = {(OpsGroup.WEIGHT, f.value, TowardChoice.HIGH) for f in target.features}
        reaches |= {(OpsGroup.TAG, t.value, toward) for t in target.tags}
        if not reaches <= named:
            return True
    return False


def _wished(found: _Read, wish: Wish, target: Target) -> None:
    turned = wish.way is not Way.NONE
    one_way = any(TAGS[tag_id].shape is TagShape.ONE_WAY for tag_id in target.tags)
    if target.word and turned and one_way:
        # "Not gritty", where gritty is built from land use alone. It is no wish
        # for fewer works: Burro has no measure of upkeep, and says so.
        found.unmet.add(UnmetCategory.UPKEEP)
        return
    if target.unmet is not None:
        found.unmet.add(target.unmet)
    for edit, raises in _weight_edits(wish, target):
        group = OpsGroup.TAG if isinstance(edit, TagEdit) else OpsGroup.WEIGHT
        quoted = target.word if edit.provenance is _INFERRED else ""
        found.made.append(_Made(group, edit, list(wish.spans), raises, word=quoted))


def _journey(wish: Wish) -> _Made:
    options = None if wish.options is None else tuple(_option(m) for m in wish.options)
    edit = CommuteEdit(
        action=CommuteAction.ADD,
        place_id="" if options is not None else wish.place_id,
        mode=wish.mode,
        max_minutes=wish.minutes,
        strictness=StrictnessChoice.HARD
        if wish.minutes and wish.firm
        else StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_STATED,
    )
    at_least = wish.at_least if wish.minutes else 0
    return _Made(OpsGroup.COMMUTE, edit, list(wish.spans), options=options, at_least=at_least)


def _given(loose: Sequence[Wish]) -> tuple[set[int], set[ModeChoice]]:
    """The minutes that were said apart from any place, and the ways of travelling them."""
    modes = {wish.mode for wish in loose} - {ModeChoice.UNCHANGED}
    return {wish.minutes for wish in loose}, modes


def _journeys_disagree(read: _Read) -> bool:
    """Whether minutes said apart from any place can be the limit of no journey.

    "A 40 minute commute on foot" is the limit, and the way, of each journey
    of the prompt. Where the prompt names no journey, there is nothing for it
    to be said of. Where a journey was given other minutes or another way,
    or two such wishes differ, the reader cannot say which is meant.
    """
    if not read.loose:
        return False
    minutes, modes = _given(read.loose)
    journeys = [made.edit for made in read.made if isinstance(made.edit, CommuteEdit)]
    return (
        not journeys
        or len(minutes) > 1
        or len(modes) > 1
        or any(edit.max_minutes and edit.max_minutes not in minutes for edit in journeys)
        or any(modes and edit.mode not in (ModeChoice.UNCHANGED, *modes) for edit in journeys)
    )


def _with_loose(made: _Made, loose: Sequence[Wish]) -> _Made:
    """A journey with the minutes that were said apart from it, how, and whether firmly.

    The way of travelling and the firmness of the limit stand with the
    minutes. "A 40 minute commute on foot" was read as 40 minutes by public
    transport, and "no more than 35 minutes" as a wish and no limit.
    """
    edit = made.edit
    if not loose or not isinstance(edit, CommuteEdit):
        return made
    (minutes,), modes = _given(loose)
    firm = any(wish.firm for wish in loose) or edit.strictness is StrictnessChoice.HARD
    spans = [span for wish in loose for span in wish.spans]
    return dataclasses.replace(
        made,
        edit=edit.replace(
            max_minutes=minutes,
            mode=next(iter(modes), edit.mode),
            strictness=StrictnessChoice.HARD if firm else StrictnessChoice.UNCHANGED,
        ),
        spans=[*made.spans, *spans],
        at_least=max(wish.at_least for wish in loose),
    )


def _said_both_ways(read: _Read) -> bool:
    """Whether a prompt both asks for a thing and turns it away, or says two things of one.

    "Pubs or no pubs", "to rent, or to buy", two budgets, one area to be left
    out and to be the only one, a journey of 30 minutes and of 40. The
    reader cannot say which is meant.
    """
    ways: dict[tuple[OpsGroup, str], set[object]] = {}
    for made in read.made:
        edit = made.edit
        if isinstance(edit, WeightEdit):
            said: object = (made.raises, edit.direction is DirectionChoice.LESS)
        elif isinstance(edit, TagEdit):
            said = (made.raises, edit.toward is TowardChoice.LOW)
        elif isinstance(edit, AreaEdit):
            said = edit.action
        else:
            continue
        ways.setdefault(_about(made), set()).add(said)
    twice = any(len(found) > 1 for found in ways.values())
    amounts = {amount for amount, _, _ in read.home.amounts}
    return twice or not read.home.agrees or len(amounts) > 1 or _journeys_disagree(read)


# --- A prompt that is not plain: what was noticed, for the person to choose ---------


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


class _Noticed(NamedTuple):
    """One thing noticed in a text, where it stands, and what may be chosen of it."""

    target: str
    label: str
    span: _Span
    choices: tuple[Choice, ...]
    note: str = ""
    # It is offered whether or not to choose it would change the search, and
    # where nothing of it can be chosen it is still said to have been heard.
    always: bool = False


# What is said on a choice of a vibe whose recipe holds recorded crime, so that
# nobody sets crime counting without being told.
COUNTING_CRIME = ", counting recorded crime"


def _listed(things: Sequence[str]) -> str:
    """The things, as a list is said. A comma stands before the last where one holds "and"."""
    if len(things) == 1:
        return things[0]
    last = ", and " if any(" and " in thing for thing in things) else " and "
    return f"{', '.join(things[:-1])}{last}{things[-1]}"


def counts_crime(tag_id: TagId) -> str:
    """What a vibe whose recipe holds recorded crime says of itself wherever it is offered."""
    tag = TAGS[tag_id]
    parts = [FEATURES[term.feature_id] for term in tag.terms]
    recorded = [_lower_first(part.label) for part in parts if part.dimension is Dimension.CRIME]
    return f"{tag.label} counts {_listed(recorded)}. {CRIME_CAVEAT}"


def _weigh(feature_id: FeatureId, direction: DirectionChoice) -> Operations:
    edit = WeightEdit(
        action=WeightAction.NUDGE,
        feature_id=feature_id,
        value=0.0,
        step=Step.UP_LARGE,
        direction=direction,
        provenance=_UI,
    )
    return NO_OPERATIONS.replace(weight_ops=(edit,))


def _feature_choices(feature_id: FeatureId) -> tuple[Choice, ...]:
    feature = FEATURES[feature_id]
    more, less = SuggestionDirection.MORE, SuggestionDirection.LESS
    if feature_id in COUNTS_RESIDENTS:
        # More of what it counts, and no other choice but to leave it out. No choice of
        # such a measure is ever sent as less, not even to take its weight off.
        wished = _weigh(feature_id, DirectionChoice.MORE)
        return (Choice(direction=more, label=feature.short_label, operations=wished),)
    if feature.polarity is Polarity.EITHER:
        # "More pubs and bars", "Fewer pubs and bars". A word of the feature's
        # own, "denser", stands by itself.
        thing = f" {_lower_first(feature.short_label)}" if feature.higher == "more" else ""
        return (
            Choice(
                direction=more,
                label=f"{feature.higher.capitalize()}{thing}",
                operations=_weigh(feature_id, DirectionChoice.MORE),
            ),
            Choice(
                direction=less,
                label=f"{feature.lower.capitalize()}{thing}",
                operations=_weigh(feature_id, DirectionChoice.LESS),
            ),
        )
    wished = _weigh(feature_id, DirectionChoice.DEFAULT)
    if feature.kind is FeatureKind.NUISANCE:
        # The one direction a nuisance has is less of it, and its short label says so.
        return (Choice(direction=less, label=feature.short_label, operations=wished),)
    off = WeightEdit(
        action=WeightAction.REMOVE,
        feature_id=feature_id,
        value=0.0,
        step=Step.NONE,
        direction=DirectionChoice.DEFAULT,
        provenance=_UI,
    )
    return (
        Choice(direction=more, label=feature.short_label, operations=wished),
        Choice(direction=less, label=TAKE_OFF, operations=NO_OPERATIONS.replace(weight_ops=(off,))),
    )


def _tag_edit(tag_id: TagId, toward: TowardChoice, action: WeightAction) -> Operations:
    edit = TagEdit(
        action=action,
        tag_id=tag_id,
        value=0.0,
        step=Step.UP_LARGE if action is WeightAction.NUDGE else Step.NONE,
        toward=toward,
        provenance=_UI,
    )
    return NO_OPERATIONS.replace(tag_ops=(edit,))


def _one_way(
    choices: tuple[Choice, ...], direction: DirectionChoice = DirectionChoice.DEFAULT
) -> tuple[Choice, ...]:
    """The choices of a thing that is offered one way: more of it, and no other.

    Where the phrase says that less is wanted, it is less of it, and no other.
    """
    less = direction is DirectionChoice.LESS
    wanted = SuggestionDirection.LESS if less else SuggestionDirection.MORE
    return tuple(choice for choice in choices if choice.direction is wanted)


def _tag_choices(tag_id: TagId, only: Toward | None = None) -> tuple[Choice, ...]:
    """What may be chosen of a vibe. `only` is the one end to offer, where one is named."""
    tag = TAGS[tag_id]
    more, less = SuggestionDirection.MORE, SuggestionDirection.LESS
    nudge, remove = WeightAction.NUDGE, WeightAction.REMOVE
    # A choice says all that it sets counting, on its own face.
    crime = COUNTING_CRIME if tag_id in HOLDS_CRIME else ""
    if tag_id in HOLDS_RESIDENTS:
        # More of it, and no other choice but to leave it out.
        only = Toward.HIGH
    if tag.shape is TagShape.SCALE:
        ends = (
            Choice(
                direction=more,
                label=f"Towards {tag.high_end}{crime}",
                operations=_tag_edit(tag_id, TowardChoice.HIGH, nudge),
            ),
            Choice(
                direction=less,
                label=f"Towards {tag.low_end}{crime}",
                operations=_tag_edit(tag_id, TowardChoice.LOW, nudge),
            ),
        )
        return ends if only is None else ends[:1] if only is Toward.HIGH else ends[1:]
    if only is not None:
        add = _tag_edit(tag_id, TowardChoice.HIGH, nudge)
        return (Choice(direction=more, label=f"Add {tag.label}{crime}", operations=add),)
    return (
        Choice(
            direction=more,
            # The name of the vibe, as it is printed wherever the vibe is shown.
            label=f"Add {tag.label}{crime}",
            operations=_tag_edit(tag_id, TowardChoice.HIGH, nudge),
        ),
        Choice(
            direction=less,
            label=TAKE_OFF,
            operations=_tag_edit(tag_id, TowardChoice.DEFAULT, remove),
        ),
    )


# How a journey is travelled, as the label of a choice says it.
_HOW: Mapping[ModeChoice, str] = {
    ModeChoice.PT: " by public transport",
    ModeChoice.CYCLE: " by bike",
    ModeChoice.WALK: " on foot",
}


def _journey_choice(
    name: str,
    place_id: str,
    minutes: int,
    firm: bool = False,
    mode: ModeChoice = ModeChoice.UNCHANGED,
) -> tuple[Choice, ...]:
    """To add a journey to a place, with what was said of it.

    The label says the minutes, whether they are a limit and how they are
    travelled, wherever the choice holds them, so that a person sees all that
    they choose. Of a journey that is only noticed, in a sentence the grammar
    does not make, it holds the minutes said straight before the place, and
    they are a limit where the words against them make them one.
    """
    hard = bool(minutes and firm)
    edit = CommuteEdit(
        action=CommuteAction.ADD,
        place_id=place_id,
        mode=mode,
        max_minutes=minutes,
        strictness=StrictnessChoice.HARD if hard else StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_UI,
    )
    within = f" of no more than {minutes} minutes" if hard else f" within {minutes} minutes"
    return (
        Choice(
            direction=SuggestionDirection.MORE,
            label=f"Add a journey to {name}{within if minutes else ''}{_HOW.get(mode, '')}",
            operations=NO_OPERATIONS.replace(commute_ops=(edit,)),
        ),
    )


def longer_was_taken(at_least: int, minutes: int) -> str:
    """What an offer says of a range of minutes, so that the person sees which was taken."""
    return f"You gave {at_least} to {minutes} minutes. Burro has taken the longer."


def _said_of_what_is_offered(sentences: Sequence["_Sentence"]) -> Iterator[tuple[_Span, _Span]]:
    """Where each thing that is only offered stands, and the words that were said of it.

    In a sentence the grammar makes, a hedge, an article and a word for a
    place belong to the thing they stand with: "slightly affluent", "a
    well-heeled area". The offer rests on all of them, so that none is called
    unread. It is so only of a thing that is offered and never applied.
    """
    for sentence in sentences:
        if not sentence.plain or sentence.taken_back:
            continue
        offered = [wish for wish in sentence.wishes or () if wish.offered]
        for item in sentence.items:
            for wish in offered:
                start, end = wish.spans[0]
                if item.what is Is.THING and start <= item.start and item.end <= end:
                    yield item.span, (start, end)


def _journeys_made(sentences: Sequence["_Sentence"]) -> list[_Made]:
    """The journeys of the sentences the grammar makes, in a prompt that is not plain.

    A journey is made of a cue, a number, words for travelling and a name,
    each of which the grammar places. Where it makes the whole of the
    sentence a journey stands in, and no sentence beside it takes it back,
    the journey is read with all that was said of it: its minutes, whether
    they are a limit and how they are travelled. It is still only offered,
    since the prompt is not plain. Minutes said apart from any place are the
    limit of each, as in a plain prompt, where they agree with it.
    """
    known = [sentence for sentence in sentences if sentence.plain and not sentence.taken_back]
    read = _read([wish for sentence in known for wish in sentence.wishes or ()])
    made = [found for found in read.made if isinstance(found.edit, CommuteEdit)]
    loose = read.loose if made and not _journeys_disagree(read) else []
    journeys = [*(_with_loose(journey, loose) for journey in made), *_maybe(read, bool(made))]
    return sorted(journeys, key=lambda journey: min(journey.spans))


def _maybe(read: _Read, beside_a_journey: bool) -> list[_Made]:
    """The places that are commuted from, each with what may be offered of it.

    Minutes said apart from any place are the limit of the journey to where
    the person works, where the prompt names one. Where the one journey it
    names is from a place, "I commute from Wickerford, at most 40 minutes",
    they are said of that, and the offer holds them.
    """
    minutes, modes = _given(read.loose)
    alone = not beside_a_journey and len(read.maybe) == 1
    if not alone or len(minutes) != 1 or len(modes) > 1:
        return read.maybe
    (journey,) = read.maybe
    assert isinstance(journey.edit, CommuteEdit)
    if journey.edit.max_minutes and journey.edit.max_minutes not in minutes:
        return read.maybe
    return [_with_loose(journey, read.loose)]


def _area_choice(name: str, area_id: str, turned_away: bool) -> tuple[Choice, ...]:
    """An area that was named: to look only there, or to leave it out.

    After a word that turns it away, "avoid Cindermoor if you can", to look
    only there is the opposite of what was said, and is not offered.
    """

    def rule(action: AreaAction) -> Operations:
        edit = AreaEdit(action=action, area_id=area_id, provenance=_UI)
        return NO_OPERATIONS.replace(area_ops=(edit,))

    out = Choice(
        direction=SuggestionDirection.LESS,
        label=f"Leave out {name}",
        operations=rule(AreaAction.EXCLUDE),
    )
    only = Choice(
        direction=SuggestionDirection.MORE,
        label=f"Look only in {name}",
        operations=rule(AreaAction.ONLY),
    )
    return (out,) if turned_away else (only, out)


_TO = {TenureChoice.RENT: ", to rent", TenureChoice.BUY: ", to buy"}


def _budget_choice(
    label: str,
    tenure: TenureChoice = TenureChoice.UNCHANGED,
    amount: int = 0,
    segment: SegmentChoice = SegmentChoice.UNCHANGED,
    firm: bool = False,
) -> tuple[Choice, ...]:
    """One thing said of the budget, and no more: an amount, a tenure, or a kind of home.

    An amount is a firm limit where the words against it say the most that
    can be paid, and the label says so.
    """
    edit = BudgetEdit(
        action=BudgetAction.SET,
        tenure=tenure,
        amount=amount,
        segment=segment,
        strictness=StrictnessChoice.HARD if amount and firm else StrictnessChoice.UNCHANGED,
        step=Step.NONE,
        provenance=_UI,
    )
    return (
        Choice(
            direction=SuggestionDirection.MORE,
            label=label,
            operations=NO_OPERATIONS.replace(budget_ops=(edit,)),
        ),
    )


# What may stand between a word that caps and its number: "up to about £1,500".
_OR_SO = frozenset({"about", "around"})


def _said_firmly(
    items: Sequence[Item], first: int, after: int, firmly: frozenset[str]
) -> _Span | None:
    """Where the words that make a limit firm stand against a number, before it or after.

    Before it, with nothing between but "about" or "around": "up to about
    £1,500". After it and what it is a number of: "£1,500 a month max". No
    further than a mark, so that the words of one number make no other firm.
    Nothing where no such words stand against it.
    """
    while first > 0 and not items[first].apart and _is_word(items[first - 1], _OR_SO):
        first -= 1
    led: list[Item] = []
    at = first
    while at > 0 and not items[at].apart and items[at - 1].what is Is.WORD and len(led) < 4:
        led.insert(0, items[at - 1])
        at -= 1
    for size in range(len(led), 0, -1):
        if " ".join(item.text for item in led[-size:]) in firmly:
            return led[-size].start, items[first].start
    if after < len(items) and not items[after].apart:
        said = _phrase_at(items, after, firmly, longest=4)
        if said:
            return items[after - 1].end, said[-1].end
    return None


# What turns away the thing that stands after it, in a prompt that is not
# plain. A word that only weakens a wish, "maybe", turns nothing away.
_TURNS_AWAY = TURNS | WORDS_THAT_TURN_AWAY | frozenset({"anywhere but", "a long way"})
# What may stand between such a word and the thing: what leads in to a place,
# a home or a number, and says nothing of whether it is wanted.
_LEADS_IN = frozenset(
    word
    for phrase in (
        *(NEAR_TO | TO_A_PLACE | EXPECTS_A_NAME | GOES_TO | REACHES | CAPS | MINUTES),
        *(TO_DO.words | WISH.words | _BEFORE_A_NAME),
    )
    for word in phrase.split()
) - {"not"}
_FURTHEST_BACK = 8
# What may say, in a prompt that is not plain, that a thing is wanted less or not at
# all, or that it troubles a person, wherever it stands in the clause of the thing.
_MAY_ASK_FOR_FEWER = (
    _TURNS_AWAY
    | TAKES_OFF
    | TAKES_OFF_AFTER
    | TURNS_DOWN
    | TURNS_DOWN_AFTER
    | TROUBLES
    | PHRASES_OF_DOUBT
    | frozenset({"too many", "too much"})
)
_BUT = frozenset({"but"})


def _begins_anew(items: Sequence[Item], at: int) -> bool:
    """Whether "but" stands here and begins something new, as it does not in "anything but"."""
    if not _is_word(items[at], _BUT):
        return False
    return at == 0 or not _phrase_at(items, at - 1, _MAY_ASK_FOR_FEWER, longest=2)


def may_ask_for_fewer(items: Sequence[Item], at: int) -> bool:
    """Whether a word that turns stands in the clause of a thing, before it or after it.

    It is asked of a thing that counts who lives somewhere: beside such a word
    the person may be asking for fewer of a group of people. Before the thing,
    a clause runs back as far as a mark or "but", because a turn may carry
    over a word that joins: "no pubs or families". After it, a clause runs as
    far as a mark or a word that joins, which begins something else: "young
    people and no pubs".
    """
    first = at
    while first > 0 and not items[first].apart and not _begins_anew(items, first - 1):
        first -= 1
    last = at + 1
    while last < len(items) and not items[last].apart and not _is_word(items[last], JOINS.words):
        last += 1
    clause = items[first:last]
    return any(
        _phrase_at(clause, on, _MAY_ASK_FOR_FEWER, longest=4)
        for on in range(len(clause))
        if on != at - first
    )


def _turned_away(items: Sequence[Item], at: int) -> bool:
    """Whether a thing stands after a word that turns it away: "I don't rent".

    A choice that has one direction, to set a tenure or to add a journey,
    would there be the opposite of what was said. So it is not offered. The
    words that lead in to the thing are passed over, "I don't want to be
    near", as far as a mark.
    """
    least = max(at - _FURTHEST_BACK, 0)
    while at > least and not items[at].apart:
        before = items[at - 1]
        led = _is_word(before, _LEADS_IN) or (before.what is Is.NUMBER and not before.money)
        if _after(items, at, _TURNS_AWAY) or not led:
            break
        at -= 1
    return _after(items, at, _TURNS_AWAY)


# The words that say a journey, whatever place is named after them. They are
# listened for only where the release names no place, so that a person is told
# that it holds no journey: where it names places, a journey is noticed by
# the name of its place.
_SAYS_A_JOURNEY = EXPECTS_A_NAME | GOES_TO | A_JOURNEY | frozenset({"commuting"})


def _phrase_at(
    items: Sequence[Item], at: int, phrases: frozenset[str], longest: int = 3
) -> list[Item]:
    """The longest of some phrases that the words spell from `at`, side by side."""
    for size in range(longest, 0, -1):
        run = list(items[at : at + size])
        together = len(run) == size and not any(item.apart for item in run[1:])
        words = together and all(item.what is Is.WORD for item in run)
        if words and " ".join(item.text for item in run) in phrases:
            return run
    # Typed with a hyphen, it is a phrase only as a whole: "semi-detached".
    one = items[at] if at < len(items) else None
    if one is not None and one.what is Is.WORD and "-" in one.text and one.bare in phrases:
        return [one]
    return []


# What is said of a home that the search cannot hold as it was said. A rent is
# published by the number of bedrooms and a price by the kind of home, so each
# tenure has kinds of home of its own (contract, section 4).
BY_KIND = "Burro holds what homes sell for by kind of home, and not by the number of bedrooms."
BY_BEDROOMS = "Burro holds rents by the number of bedrooms, and not by kind of home."
TO_RENT_ALONE = "Burro holds what a studio or a room costs to rent, and not to buy."
# A kind of home that says little of one to rent: most homes that are let are flats.
_A_FLAT = frozenset(word for word, kind in BUY_SEGMENTS.items() if kind is SegmentChoice.FLAT)
_THE = frozenset({"a", "an", "the"})


class _Home(NamedTuple):
    """The size and the kind of a home as they were named, and where the words stand."""

    bedrooms: int  # nothing where no number of bedrooms was said
    kind: str  # a word of `RENT_SEGMENTS` or `BUY_SEGMENTS`, or none
    span: _Span
    # The item after the last of its words.
    end: int


def _home_at(items: Sequence[Item], at: int) -> _Home | None:
    """The home that is named from here: "a two bed flat", "3 bedrooms", "a terraced house"."""
    first = items[at]
    bedrooms, end = 0, at
    if first.what is Is.NUMBER:
        after = items[at + 1] if at + 1 < len(items) else None
        glued = first.unit == "bed"
        apart = not glued and not first.unit and _is_word(after, BEDROOMS)
        if not (glued or (apart and after is not None and not after.apart)):
            return None
        if first.money or first.low or first.value < 1:
            return None
        bedrooms, end = first.value, at + (1 if glued else 2)
    beside = end == at or (end < len(items) and not items[end].apart)
    said = _phrase_at(items, end, _KINDS_OF_HOME) if beside else []
    kind = " ".join(item.bare or item.text for item in said)
    end += len(said)
    if not bedrooms and not kind:
        return None
    # What a home is called, after either: "a terraced house", "a two bed place".
    if end < len(items) and _is_word(items[end], A_HOME) and not items[end].apart:
        end += 1
    # And the article before it, so that "a two bed house" is read whole.
    led = at > 0 and _is_word(items[at - 1], _THE) and not first.apart
    start = items[at - 1].start if led else first.start
    return _Home(bedrooms, kind, (start, items[end - 1].end), end)


def _segment_for(tenure: Tenure, home: _Home) -> SegmentChoice | None:
    """The kind of home the search can hold for what was said, for one tenure."""
    if tenure is Tenure.BUY:
        return BUY_SEGMENTS.get(home.kind)
    if home.kind in RENT_SEGMENTS:
        return RENT_SEGMENTS[home.kind]
    return _BEDS[min(home.bedrooms, len(_BEDS)) - 1] if home.bedrooms else None


def _said_of(home: _Home) -> str:
    """What a home is called where the search can hold no part of it: what was said."""
    if home.kind:
        kinds = RENT_SEGMENTS if home.kind in RENT_SEGMENTS else BUY_SEGMENTS
        return SEGMENT_LABELS[Segment(kinds[home.kind].value)]
    return SEGMENT_LABELS[Segment(_BEDS[min(home.bedrooms, len(_BEDS)) - 1].value)]


def _not_held(tenure: Tenure, home: _Home) -> str:
    """What is said where part of a home cannot be held for the tenure it is for."""
    if tenure is Tenure.BUY:
        if home.kind in RENT_SEGMENTS:
            return TO_RENT_ALONE
        return BY_KIND if home.bedrooms else ""
    apart = home.kind in BUY_SEGMENTS and home.kind not in _A_FLAT
    return BY_BEDROOMS if apart else ""


class _Notices:
    """What is noticed in the sentences of a prompt, in the order it stands."""

    def __init__(
        self, release: Release, grammar: Grammar, spec: PreferenceSpec, about_people: bool = False
    ) -> None:
        self.release = release
        self.grammar = grammar
        self.spec = spec
        # The words draw the notice: they ask who lives somewhere in a way nothing is
        # offered for, or may ask for fewer of a group of people. Nothing that counts
        # who lives somewhere is then offered, whatever else the words name.
        self.about_people = about_people
        # The tenures the words of the prompt name, which a home that is named is for.
        self.said: frozenset[Tenure] = frozenset()
        # Where a thing that is only offered stands, with what was said of it:
        # "slightly affluent", "a bit of character". By where the thing stands.
        self.whole: dict[_Span, _Span] = {}

    def of(self, sentences: Sequence["_Sentence"], journeys: Sequence[_Made]) -> list[_Noticed]:
        """What is noticed in the sentences, with the journeys the grammar made of them.

        A name that stands in such a journey is read there, and is not
        noticed a second time by itself.
        """
        found: list[_Noticed] = []
        read = [span for journey in journeys for span in journey.spans]
        for journey in journeys:
            if journey.options is None:
                found += self._journey(journey)
        self.said = frozenset(
            tenure for sentence in sentences for tenure in self._tenures(sentence.items)
        )
        self.whole = dict(_said_of_what_is_offered(sentences))
        for sentence in sentences:
            items = sentence.items
            skip = 0
            for at, item in enumerate(items):
                if at < skip:
                    continue
                if item.what is Is.THING:
                    found += self._thing(items, at)
                elif item.what is Is.NAME:
                    if not any(start <= item.start and item.end <= end for start, end in read):
                        found += self._name(items, at)
                elif item.what is Is.NUMBER:
                    found += self._money(items, at)
                    if (home := _home_at(items, at)) is not None:
                        found += self._home(items, at, home)
                        skip = home.end
                elif item.what is Is.WORD and (said := _phrase_at(items, at, RENTS | BUYS)):
                    found += self._tenure(items, at, said)
                    skip = at + len(said)
                elif item.what is Is.WORD and (home := _home_at(items, at)) is not None:
                    found += self._home(items, at, home)
                    skip = home.end
                elif (
                    item.what is Is.WORD
                    and not self.release.places
                    and (said := _phrase_at(items, at, _SAYS_A_JOURNEY, longest=4))
                ):
                    # A journey the grammar made holds these words already, and is
                    # said to be missing by all of them.
                    if not any(start <= item.start and said[-1].end <= end for start, end in read):
                        found += self._journey_said(items, at, said)
                    skip = at + len(said)
        return found

    def _tenures(self, items: Sequence[Item]) -> Iterator[Tenure]:
        """The tenures a sentence names: by a word for one, or by an amount of one alone.

        A rent is paid by the month, and no rent is as high as a price. A
        word that is turned away, "I don't rent", names nothing.
        """
        for at, item in enumerate(items):
            if item.what is Is.WORD and (said := _phrase_at(items, at, RENTS | BUYS)):
                if not _turned_away(items, at):
                    rents = " ".join(word.text for word in said) in RENTS
                    yield Tenure.RENT if rents else Tenure.BUY
            elif item.what is Is.NUMBER and item.unit not in ("min", "bed"):
                by_month = item.unit == "month" or bool(_phrase_at(items, at + 1, MONTHLY))
                if by_month or (item.money and item.value <= LIMITS.rent.maximum):
                    yield Tenure.RENT
                elif item.money and item.value >= LIMITS.buy.minimum:
                    yield Tenure.BUY

    def _home(self, items: Sequence[Item], at: int, home: _Home) -> Iterator[_Noticed]:
        """The size and the kind of a home, offered whenever they are named.

        A home is for the tenure the words of the prompt name, and for the
        tenure of the search where they name none or both. The choice holds
        the kind of home the search can hold for that tenure, and the tenure
        where it is not the search's own, and says both. Where part of what
        was said cannot be held, the offer says why. Where none of it can,
        nothing is offered to be set, and it is still said to have been
        heard. Nobody is moved to the other tenure for having named a home,
        but a person who has chosen no tenure and names a kind of home that
        is held for buying alone: the choice says that it is to buy.
        """
        if _turned_away(items, at):
            return
        named = next(iter(self.said)) if len(self.said) == 1 else None
        tenure = named or self.spec.tenure
        segment = _segment_for(tenure, home)
        note = _not_held(tenure, home)
        nobody_chose = not self.said and self.spec.tenure_from is Provenance.DEFAULT
        for_sale_alone = home.kind in BUY_SEGMENTS and home.kind not in _A_FLAT
        if segment is None and nobody_chose and tenure is Tenure.RENT and for_sale_alone:
            tenure, segment = Tenure.BUY, BUY_SEGMENTS[home.kind]
        if segment is None:
            if note:
                yield _Noticed("budget", f"A {_said_of(home)}", home.span, (), note, always=True)
            return
        moved = TenureChoice.UNCHANGED if tenure is self.spec.tenure else TenureChoice(tenure.value)
        label = f"A {SEGMENT_LABELS[Segment(segment.value)]}"
        choice = _budget_choice(f"Set {_lower_first(label)}{_TO.get(moved, '')}", moved, 0, segment)
        yield _Noticed("budget", label, home.span, choice, note, always=True)

    def _journey(self, made: _Made) -> Iterator[_Noticed]:
        """A journey the grammar made, to a place the release holds, as an offer."""
        edit = made.edit
        assert isinstance(edit, CommuteEdit)
        place = self.release.place(edit.place_id)
        if place is None or place.kind is PlaceKind.UNIVERSITY:
            return
        firm = edit.strictness is StrictnessChoice.HARD
        choices = _journey_choice(place.name, place.place_id, edit.max_minutes, firm, edit.mode)
        note = longer_was_taken(made.at_least, edit.max_minutes) if made.at_least else ""
        for span in made.spans:
            yield _Noticed("commute", place.name, span, choices, note)

    def _thing(self, items: Sequence[Item], at: int) -> Iterator[_Noticed]:
        item = items[at]
        target = self.grammar.known.lexicon[item.text]
        if about_a_campus(target) or _names_no_place(items, at):
            # A campus in a prompt that is not plain is heard as a request about
            # people. And "I commute to school" is no wish for schools.
            return
        # What is offered one way is offered so where the grammar makes the
        # sentence it stands in, and nothing turns it. In any other sentence
        # nobody can say which way it is meant, "anything but posh", and both
        # ways are offered. A word for character is offered one way whatever
        # is said of it. So is a thing that counts who lives somewhere, of
        # which nothing but more is ever offered.
        of_people = counts_residents(target)
        one_way = target.one_way and (target.whatever or of_people or item.span in self.whole)
        span = self.whole.get(item.span, item.span)
        no_measure = COUNTS_RESIDENTS if self.about_people else frozenset[FeatureId]()
        no_vibe = HOLDS_RESIDENTS if self.about_people else frozenset[TagId]()
        features = [
            _Noticed(
                f"feature:{feature_id}",
                FEATURES[feature_id].short_label,
                span,
                _one_way(_feature_choices(feature_id), target.direction)
                if one_way
                else _feature_choices(feature_id),
                _note_of(target, feature_id in COUNTS_RESIDENTS),
            )
            for feature_id in target.features
            if feature_id not in no_measure
        ]
        tags = [
            _Noticed(
                f"tag:{tag_id}",
                TAGS[tag_id].short_label,
                span,
                _tag_choices(tag_id, target.toward if one_way else None),
                " ".join(
                    said
                    for said in (
                        _note_of(target, tag_id in HOLDS_RESIDENTS),
                        counts_crime(tag_id) if tag_id in HOLDS_CRIME else "",
                    )
                    if said
                ),
            )
            for tag_id in target.tags
            if tag_id not in no_vibe
        ]
        # Of what is only nearest, a vibe comes before the measures it is made of, but
        # for a measure that is the first reading of the word.
        if not target.one_way:
            yield from (*features, *tags)
            return
        leads = {f"feature:{feature_id}" for feature_id in target.leads}
        first = [one for one in features if one.target in leads]
        yield from (*first, *tags, *(one for one in features if one.target not in leads))

    def _name(self, items: Sequence[Item], at: int) -> Iterator[_Noticed]:
        item = items[at]
        place = self.release.place(item.place) if item.place else None
        area = self.release.neighbourhood(item.area) if item.area else None
        if place is not None and place.kind is PlaceKind.UNIVERSITY:
            return
        turned_away = _turned_away(items, at)
        # A name that is an area's and a place's is a journey after words that
        # expect a place, and an area anywhere else.
        if place is not None and (area is None or _cued(items, at)):
            if not turned_away:
                minutes = _minutes_before(items, at)
                # It rests on the minutes too, where it holds them.
                start = _where_minutes_start(items, at) if minutes else item.start
                shorter = _range_before(items, at)
                number = _number_before(items, at) if minutes else None
                firmly = (
                    _said_firmly(items, items.index(number), len(items), FIRM_OF_MINUTES)
                    if number is not None
                    else None
                )
                if firmly is not None:
                    start = min(start, firmly[0])
                # A range is a limit at its longer end, and so are minutes that are capped.
                firm = bool(shorter) or firmly is not None
                choices = _journey_choice(place.name, place.place_id, minutes, firm)
                note = longer_was_taken(shorter, minutes) if shorter else ""
                yield _Noticed("commute", place.name, (start, item.end), choices, note)
        elif area is not None:
            choices = _area_choice(area.name, area.area_id, turned_away)
            yield _Noticed("area", area.name, item.span, choices)

    @staticmethod
    def _journey_said(items: Sequence[Item], at: int, said: Sequence[Item]) -> Iterator[_Noticed]:
        """A journey that is said where the release names no place to make one to.

        Its one choice names no place, and the reducer turns it away: it is
        there to be said to be missing, and is never offered.
        """
        if _turned_away(items, at):
            return
        span = (said[0].start, said[-1].end)
        yield _Noticed(COMMUTE_TARGET, A_JOURNEY_TO, span, _journey_choice("", "", 0))

    def _of_which_tenure(self, amount: int, by_month: bool) -> TenureChoice:
        """The tenure an amount must be of, where it cannot be of the search's own.

        A rent is paid by the month, and no rent is as high as a price. It is
        `unchanged` wherever the amount can be of the tenure the search holds.
        """
        rent = LIMITS.rent.minimum <= amount <= LIMITS.rent.maximum
        buy = LIMITS.buy.minimum <= amount <= LIMITS.buy.maximum and not by_month
        suits = rent if self.spec.tenure is Tenure.RENT else buy
        if suits or not (rent or buy or by_month):
            return TenureChoice.UNCHANGED
        return TenureChoice.RENT if rent or by_month else TenureChoice.BUY

    def _money(self, items: Sequence[Item], at: int) -> Iterator[_Noticed]:
        """An amount of money, offered as the budget. The choice holds the amount alone.

        The size of home and the tenure that stand beside it are no part of
        it, since the label names neither: each is offered for itself. The
        tenure is part of it only where the amount cannot be of the tenure
        the search holds, and the label then says which it is of.
        """
        item = items[at]
        by_month = [item] if item.unit == "month" else _phrase_at(items, at + 1, MONTHLY)
        if item.unit in ("min", "bed") or not (item.money or by_month):
            return
        after = items[at + 1] if at + 1 < len(items) else None
        if item.distance and _is_word(after, TO_A_PLACE | _AWAY):
            return  # "1.5m from a park" and "1.5m away" are distances
        span = (item.start, by_month[-1].end if by_month else item.end)
        tenure = self._of_which_tenure(item.value, bool(by_month))
        label = f"A budget of £{money(item.value)}{' a month' if by_month else ''}"
        last = items.index(by_month[-1]) if by_month and by_month[-1] is not item else at
        firmly = _said_firmly(items, at, last + 1, FIRM_OF_MONEY)
        if firmly is not None:
            # It rests on the words that make it a limit too: "max £400k".
            span = (min(span[0], firmly[0]), max(span[1], firmly[1]))
        most = f"A budget of no more than £{money(item.value)}{' a month' if by_month else ''}"
        said = f"Set {_lower_first(most if firmly else label)}{_TO.get(tenure, '')}"
        choice = _budget_choice(said, tenure, amount=item.value, firm=firmly is not None)
        yield _Noticed("budget", label, span, choice)

    @staticmethod
    def _tenure(items: Sequence[Item], at: int, said: Sequence[Item]) -> Iterator[_Noticed]:
        if _turned_away(items, at):
            return
        rent = " ".join(item.text for item in said) in RENTS
        label = "Renting" if rent else "Buying"
        tenure = TenureChoice.RENT if rent else TenureChoice.BUY
        choice = _budget_choice(f"Set {label.lower()}", tenure)
        yield _Noticed("tenure", label, (said[0].start, said[-1].end), choice)


def _note_of(target: Target, counts_who_lives_there: bool) -> str:
    """What is said beside one thing a phrase is offered as.

    What a phrase says of what it asks for is said of every thing it is
    offered as, but for the line that a thing counts who lived somewhere at the
    census, which is said of the things that do and of no other: "family
    friendly" is offered as a vibe that counts households and as one that
    counts places alone.
    """
    if counts_who_lives_there:
        return target.note
    return "" if target.note == COUNTED_AT_THE_CENSUS else target.note


class _Offered(NamedTuple):
    """What came of what was noticed: what is offered, what is heard, and what is missing."""

    suggestions: tuple[Suggestion, ...]
    # Where the words stand of what the search holds already.
    already: list[_Span]
    # What the release holds for no area, in the order it stands in the text.
    missing: tuple[NotInRelease, ...]


def _offered(noticed: Sequence[_Noticed], spec: PreferenceSpec, release: Release) -> _Offered:
    """The suggestions for what was noticed, and where the words stand that need none.

    There is one suggestion for each thing, however often it is named. A
    choice is never offered if its edit would be turned away, or would change
    nothing. A thing of which nothing can be chosen is not offered.

    A thing that is not offered because the search holds it already was heard
    all the same: "near a park", said where the search holds a park already.
    Its words are given back, so that they are not said to be unread. So was
    a thing that is not offered because the release holds it for no area: it
    is said to be missing, by its name. A thing whose every edit would be
    turned away for any other reason was not heard.

    The size and the kind of a home are offered whatever the search holds:
    a person who names one is told that it was heard. Where nothing of it can
    be set it is offered with what is said of it, and with nothing to choose
    but to leave it out. Where the release holds no cost of it for any area,
    it is said to be missing, as any other thing is.
    """
    found: dict[tuple[str, str], tuple[list[_Span], tuple[Choice, ...], str]] = {}
    always: set[tuple[str, str]] = set()
    for thing in noticed:
        about = (thing.target, thing.label)
        spans, choices, note = found.setdefault(about, ([], thing.choices, thing.note))
        if thing.span not in spans:
            spans.append(thing.span)
        # Named twice, and once where more of it may be chosen, or where more is
        # to be said of it: "posh, but not too posh" is offered with both ends of
        # the scale, and "not rough, not posh" with what is said of both words.
        more = thing.choices if len(thing.choices) > len(choices) else choices
        found[about] = (spans, more, thing.note if len(thing.note) > len(note) else note)
        if thing.always:
            always.add(about)

    # Every choice is tried on the spec with its defaults given way, which is
    # what the reducer applies an edit to. It is worked out once for them all.
    ready = given_way_spec(spec)

    def tried(choice: Choice) -> bool | RejectReason:
        """Whether a choice would change the search, or why it would be turned away."""
        result = apply(ready, choice.operations, release)
        if result.rejected:
            return result.rejected[0].reason
        return any(applied.changed for applied in result.applied)

    suggestions: list[Suggestion] = []
    already: list[_Span] = []
    missing: list[NotInRelease] = []
    for (target, label), (spans, choices, note) in found.items():
        outcomes = [(choice, tried(choice)) for choice in choices]
        # Why a choice would be turned away is no answer to whether it changes anything.
        whatever = (target, label) in always
        open_to = tuple(
            choice
            for choice, changes in outcomes
            if changes is True or (whatever and changes is False)
        )
        stood = tuple(Span(start=start, end=end) for start, end in sorted(spans))
        lacking = any(changes is RejectReason.NOT_IN_RELEASE for _, changes in outcomes)
        if open_to or (whatever and note and not lacking):
            suggestions.append(
                Suggestion(
                    target=target, label=label, spans=stood, choices=(*open_to, IGNORE), note=note
                )
            )
        elif outcomes and all(changes is False for _, changes in outcomes):
            already += spans
        elif any(changes is RejectReason.NOT_IN_RELEASE for _, changes in outcomes):
            missing.append(NotInRelease(target=target, label=label, spans=stood))
    return _Offered(
        tuple(sorted(suggestions, key=lambda suggestion: suggestion.spans[0].start)),
        already,
        tuple(sorted(missing, key=lambda thing: thing.spans[0].start)),
    )


def _named(edit: object) -> tuple[str, str] | None:
    """What an edit asks for, as a suggestion names it: its target and its label."""
    if isinstance(edit, WeightEdit):
        return f"feature:{edit.feature_id}", FEATURES[edit.feature_id].short_label
    if isinstance(edit, TagEdit):
        return f"tag:{edit.tag_id}", TAGS[edit.tag_id].short_label
    if isinstance(edit, BudgetEdit):
        return BUDGET_TARGET, A_BUDGET
    if isinstance(edit, CommuteEdit):
        return COMMUTE_TARGET, A_JOURNEY_TO
    return None


def not_in_release_of(
    result: InterpretResult, rejected: Sequence[Rejected]
) -> tuple[NotInRelease, ...]:
    """Everything a reading asked for that the release holds for no area, each named once.

    `rejected` is what the reducer turned away of the edits of the reading.
    What it turned away as not in the release is named here by the label of
    the thing, with the words its edit rests on. What the reader noticed and
    did not offer follows. It is for whoever serves a reading: every
    interpreter's edits are held to the one reducer, so what is missing is
    said the same way whoever read the words.
    """
    found: dict[str, tuple[str, list[Span]]] = {}
    for turned in rejected:
        if turned.reason is not RejectReason.NOT_IN_RELEASE:
            continue
        # A group is named as its array of the edits is.
        edits: Sequence[object] = getattr(result.operations, turned.group.value)
        named = _named(edits[turned.index]) if turned.index < len(edits) else None
        if named is None:
            continue
        spans = found.setdefault(named[0], (named[1], []))[1]
        spans += [
            Span(start=rests.start, end=rests.end)
            for rests in result.rests_on
            if (rests.group, rests.index) == (turned.group, turned.index)
        ]
    for thing in result.not_in_release:
        found.setdefault(thing.target, (thing.label, []))[1].extend(thing.spans)
    return tuple(
        NotInRelease(
            target=target,
            label=label,
            spans=tuple(sorted(set(spans), key=lambda span: (span.start, span.end))),
        )
        for target, (label, spans) in found.items()
    )


def _heard(sentence: "_Sentence") -> set[int]:
    """The tokens that a notice or an unmet category rests on.

    What Burro has no measure of, and who lives somewhere, are heard with the
    words said of them: "can I afford it" is one request. The words go as far
    as a mark, a word that joins, a word the grammar does not hold, or a
    thing, a name or a number, which is noticed for itself.
    """
    items = sentence.items
    heard: set[int] = set()
    for at, item in enumerate(items):
        if item.what not in (Is.PEOPLE, Is.AMENITY, Is.UNMET):
            continue
        heard |= set(range(item.first, item.last))
        for step in (-1, 1):
            on = at + step
            while 0 <= on < len(items) and items[on].what in (Is.WORD, Is.GENERIC):
                parted = items[on].apart if step > 0 else items[on + 1].apart
                unknown = items[on].what is Is.WORD and items[on].text not in KNOWN_WORDS
                if parted or unknown or items[on].text in JOINS.words:
                    break
                heard |= set(range(items[on].first, items[on].last))
                on += step
    return heard


def _unread(sentences: Sequence["_Sentence"], rested_on: Sequence[_Span]) -> tuple[Span, ...]:
    """Each stretch of the text that nothing rests on. Two that touch are one."""
    found: list[list[int]] = []
    open_run = False
    for sentence in sentences:
        heard = _heard(sentence)
        for index, token in enumerate(sentence.line.tokens):
            read = index in heard or any(
                start <= token.start and token.end <= end for start, end in rested_on
            )
            if read:
                open_run = False
            elif open_run:
                found[-1][1] = token.end
            else:
                found.append([token.start, token.end])
                open_run = True
    return tuple(Span(start=start, end=end) for start, end in found)


# --- The reader ---------------------------------------------------------------------


def _asks(line: Line, items: Sequence[Item]) -> bool:
    """Whether a sentence asks and does not tell.

    It ends in a question mark, opens with "is", "are" or "am", or puts a verb
    before the speaker: "would I want a pub next door".
    """
    verbs = frozenset(
        {
            *("is", "are", "am", "would", "must", "have", "has", "can", "could", "should"),
            *("do", "does", "will", "shall", "may", "might"),
        }
    )
    turned_about = any(
        _is_word(verb, verbs) and _is_word(who, SPEAKER.words) and not who.apart
        for verb, who in pairwise(items)
    )
    opens = bool(items) and _is_word(items[0], frozenset({"is", "are", "am"}))
    return line.asked or turned_about or opens


# What says that a thing is wanted near, or is to be reached. "By" is not among
# them here: in a sentence the grammar does not make it may say who did a thing.
_NEAR_OR_REACHED = (NEAR_TO - {"by"}) | frozenset({"get to", "reach", "walk to"})
# What may stand between such words and the thing: "close to a good doctor".
_BEFORE_A_THING = ARTICLE.words | GOOD.words


def _no_place(line: Line, items: Sequence[Item], grammar: Grammar) -> list[Item]:
    """The items of a sentence the grammar does not make, less each person read as a place.

    "Doctor" is a person too. In a sentence the grammar makes, it has held
    the word to what says near. In any other, the word is a thing only where
    the words straight beside it say that it is wanted near or is to be
    reached, "she wants to be near a doctor", and is left a word anywhere
    else: "I am a doctor" is offered no surgery.
    """
    found = list(items)
    for at, item in enumerate(items):
        if item.what is not Is.THING or not grammar.known.lexicon[item.text].near_only:
            continue
        back = at
        while back > 0 and _is_word(items[back - 1], _BEFORE_A_THING) and not items[back].apart:
            back -= 1
        led = _after(items, back, _NEAR_OR_REACHED)
        timed = _timed(items, back) and _minutes_before(items, back) > 0
        if not (led or timed or grammar.nearby(items[at + 1 :])):
            token = line.tokens[item.first]
            found[at] = dataclasses.replace(item, what=Is.WORD, text=token.word, bare=token.bare)
    return found


def _sentences(text: str, grammar: Grammar) -> list[_Sentence]:
    found: list[_Sentence] = []
    for line in lines_of(text):
        items = grammar.items(line)
        asked = _asks(line, items)
        try:
            wishes = None if asked else grammar.sentence(line, items)
        except NotPlain:
            wishes = None
        if wishes is None:
            items = _no_place(line, items, grammar)
        found.append(_Sentence(line, items, wishes, asked=asked))
    _take_back(found)
    return found


def _closes(sentence: _Sentence) -> bool:
    """Whether a sentence holds doubt and names nothing: "No thanks.", "I disagree."."""
    return not sentence.plain and not sentence.names


def _take_back(sentences: Sequence[_Sentence]) -> None:
    """A sentence that holds doubt and names nothing is said of what stands beside it.

    "I want a station. Not really." The reader applies nothing of a prompt
    that holds such a sentence. It marks what the sentence is said of all
    the same, for a caller that holds edits the reader did not make: the
    sentence before it, and what is listed beside it, as far as the list goes.
    """
    for at, sentence in enumerate(sentences):
        if not _closes(sentence):
            continue
        back = at - 1
        if back >= 0 and not _closes(sentences[back]):
            sentences[back].taken_back = True
            while (
                back > 0
                and not sentences[back].own
                and not sentences[back - 1].own
                and not _closes(sentences[back - 1])
            ):
                back -= 1
                sentences[back].taken_back = True
        on = at + 1
        while on < len(sentences) and not sentences[on].own and not _closes(sentences[on]):
            sentences[on].taken_back = True
            on += 1


def _names_no_place(items: Sequence[Item], at: int) -> bool:
    """Whether a thing stands where a place was expected, and names none: "I work at uni"."""
    generic = items[at].text.split()[-1] in GENERIC_PLACES
    return generic and _after(items, at, EXPECTS_A_NAME | GOES_TO)


def _asks_for_fewer(sentences: Sequence[_Sentence], grammar: Grammar) -> bool:
    """Whether the words name who lives somewhere and may ask for fewer of them.

    A thing that counts who lives somewhere is offered towards more of what it
    counts. Beside a word that turns, or in a sentence that the next takes
    back, the words may ask for fewer of a group of people. Nothing reads
    that: it is a request about people, and gets the notice and nothing else.
    """
    return any(
        item.what is Is.THING
        and counts_residents(grammar.known.lexicon[item.text])
        and (sentence.taken_back or may_ask_for_fewer(sentence.items, at))
        for sentence in sentences
        for at, item in enumerate(sentence.items)
    )


def _names_a_campus(sentences: Sequence[_Sentence], grammar: Grammar) -> bool:
    """Whether a campus is named, by word or by name.

    In a prompt the reader cannot read, a campus may be what the person wants
    distance from, which is a way to ask for fewer students (contract 8.4).
    """
    release = grammar.release
    for sentence in sentences:
        for at, item in enumerate(sentence.items):
            place = release.place(item.place) if release is not None and item.place else None
            if place is not None and place.kind is PlaceKind.UNIVERSITY:
                return True
            campus = item.what is Is.THING and about_a_campus(grammar.known.lexicon[item.text])
            if campus and not _names_no_place(sentence.items, at):
                return True
    return False


class RuleInterpreter:
    """Reads a request with rules alone. It cannot fail, and it never answers `off_topic`.

    It applies a prompt only when the whole of it is plain. For any other it
    applies nothing, offers what it noticed, and says what it made nothing of.
    It cannot tell an off-topic sentence from one it failed to read, so for
    either it answers `ok` with no edits and `other` among what was unmet.
    """

    name = InterpreterName.RULE

    def __init__(self) -> None:
        # The names and the words of the release last read, so that they are made
        # ready once and not for every request. A release never changes.
        self._grammar: tuple[Release, Grammar] | None = None

    def _grammar_of(self, release: Release) -> Grammar:
        if self._grammar is None or self._grammar[0] is not release:
            self._grammar = (release, Grammar(Names(release), release))
        return self._grammar[1]

    def interpret(self, request: InterpretRequest) -> InterpretResult:
        grammar = self._grammar_of(request.release)
        sentences = _sentences(request.text, grammar)
        if all(sentence.plain for sentence in sentences):
            read = _read([wish for sentence in sentences for wish in sentence.wishes or ()])
            if not _said_both_ways(read) and not _left_to_choose(read):
                return self._applied(read, request)
        return self._suggested(sentences, grammar, request)

    def by_sentence(self, request: InterpretRequest) -> InterpretResult:
        """What the reader makes of each sentence alone. It is never served as its answer.

        It is for a caller that holds edits the reader did not make to the
        reader's own reading, sentence by sentence: the model-backed
        interpreter. It holds the edits of every sentence that the grammar
        makes and that no sentence beside it takes back, whatever the other
        sentences are. `interpret` applies a prompt whole or not at all, and
        this does not change that: nothing here is applied for the reader.
        """
        grammar = self._grammar_of(request.release)
        sentences = _sentences(request.text, grammar)
        heard = self._suggested(sentences, grammar, request)
        known = [s for s in sentences if s.plain and not s.taken_back]
        read = _read([wish for sentence in known for wish in sentence.wishes or ()])
        if not any(isinstance(made.edit, CommuteEdit) for made in read.made):
            # Minutes whose journey stands in a sentence the reader does not
            # know are the limit of nothing here, and take nothing else back.
            read.loose = []
        if _said_both_ways(read):
            read = _Read(unmet=read.unmet, about_people=read.about_people)
        found = self._applied(read, request)
        if len(known) == len(sentences):
            return found
        # What was heard in the sentences it does not know is said all the same.
        about_people = read.about_people or heard.notice is Notice.NEUTRAL_PLACES
        unmet = {*found.unmet, *heard.unmet}
        return found.replace(
            status=InterpretStatus.POLICY_REDIRECT if about_people else found.status,
            notice=Notice.NEUTRAL_PLACES if about_people else Notice.NONE,
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            unread=heard.unread,
        )

    def _applied(self, read: _Read, request: InterpretRequest) -> InterpretResult:
        """A plain prompt: every item makes the edit the contract gives it."""
        made = list(read.made)
        # What was named outright is read before what was only implied, so that
        # "safe, with low crime" is the explicit request its second half makes it.
        made.sort(key=lambda m: getattr(m.edit, "provenance", _STATED) is _INFERRED)
        groups: dict[OpsGroup, list[_Made]] = {group: [] for group in OpsGroup}
        budget = _budget(read.home, request.spec)
        if budget is not None:
            where = read.home.amounts[0][2] if read.home.amounts else None
            groups[OpsGroup.BUDGET] += [
                _Made(OpsGroup.BUDGET, edit, spans)
                for edit, spans in _as_can_be_tested(*budget, where, request)
            ]
        # A home of which no edit can be made, "a two bed house" typed by a
        # buyer, was passed over in silence: no edit, no offer, nothing unread.
        # It is said to be unread. It is not offered here, because the status
        # of a plain prompt would then say whether the search is to rent or to
        # buy, and a status is kept about a call (contract, section 10.1).
        passed_over = budget is None and bool(read.home.bedrooms or read.home.segments)
        unread = sorted(set(read.home_spans)) if passed_over else []
        unmet = read.unmet | ({UnmetCategory.OTHER} if unread else set[UnmetCategory]())
        seen: set[tuple[OpsGroup, str]] = set()
        for found in made:
            about = _about(found)
            if about[1] and about in seen:
                continue
            seen.add(about)
            # "A 40 minute commute", said apart from any place, is the limit
            # of each journey of the prompt.
            groups[found.group].append(_with_loose(found, read.loose))
        edits = [found.edit for listed in groups.values() for found in listed]
        operations = Operations(
            budget_ops=tuple(edit for edit in edits if isinstance(edit, BudgetEdit)),
            commute_ops=tuple(edit for edit in edits if isinstance(edit, CommuteEdit)),
            weight_ops=tuple(edit for edit in edits if isinstance(edit, WeightEdit)),
            tag_ops=tuple(edit for edit in edits if isinstance(edit, TagEdit)),
            area_ops=tuple(edit for edit in edits if isinstance(edit, AreaEdit)),
            setting_ops=(),
        )
        indexed = [
            (group, index, found)
            for group, listed in groups.items()
            for index, found in enumerate(listed)
        ]
        # A question offers places to choose from, or a field to look one up
        # in. A release that names no place has neither, so nothing is asked:
        # the reducer turns the journey away, as not in the release.
        clarify = tuple(
            Clarify(group=group, index=index, options=found.options)
            for group, index, found in indexed
            if found.options is not None and request.release.places
        )
        quoted = tuple(
            Assumption(code=AssumptionCode.WORD, group=group, index=index, word=found.word)
            for group, index, found in indexed
            if found.word
        )
        # Of a range of minutes the longer was taken. The person gave two numbers
        # and the search holds one, so it is said to be assumed.
        ranged = tuple(
            Assumption(code=AssumptionCode.MAX_MINUTES, group=group, index=index)
            for group, index, found in indexed
            if found.at_least
        )
        if read.about_people:
            status = InterpretStatus.POLICY_REDIRECT
        elif clarify:
            status = InterpretStatus.CLARIFY
        else:
            status = InterpretStatus.OK
        return InterpretResult(
            status=status,
            operations=operations,
            assumptions=(*assumptions_for(operations, request.spec), *ranged, *quoted),
            # In the order the categories are listed, whatever order they were heard in.
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            clarify=clarify,
            notice=Notice.NEUTRAL_PLACES if read.about_people else Notice.NONE,
            interpreter=self.name,
            degraded=False,
            usage=NO_USAGE,
            rests_on=tuple(
                RestsOn(group=group, index=index, start=start, end=end)
                for group, index, found in indexed
                for start, end in sorted(found.spans)
            ),
            unread=tuple(Span(start=start, end=end) for start, end in unread),
        )

    def _suggested(
        self, sentences: Sequence[_Sentence], grammar: Grammar, request: InterpretRequest
    ) -> InterpretResult:
        """A prompt that is not plain: nothing is applied, and what was noticed is offered.

        A place the release does not hold, named where the grammar expects a
        place, is asked about all the same. The question is an edit that
        carries no place, so it adds nothing to the search until the person
        says which place was meant.
        """
        journeys = _journeys_made(sentences)
        asked = self._applied(_Read(made=[j for j in journeys if j.options is not None]), request)
        items = [item for sentence in sentences for item in sentence.items]
        about_people = (
            any(item.what is Is.PEOPLE for item in items)
            or _names_a_campus(sentences, grammar)
            or _asks_for_fewer(sentences, grammar)
        )
        notices = _Notices(request.release, grammar, request.spec, about_people)
        noticed = notices.of(sentences, journeys)
        suggestions, already, missing = _offered(noticed, request.spec, request.release)
        # What is offered, what is said to be missing and what is asked about were all heard.
        rested_on = [
            (span.start, span.end) for found in (*suggestions, *missing) for span in found.spans
        ]
        rested_on += [(rests.start, rests.end) for rests in asked.rests_on]
        unread = _unread(sentences, [*rested_on, *already])
        unmet = {item.unmet for item in items if item.unmet is not None}
        # What Burro cannot say of a thing it offers what is nearest for.
        things = [grammar.known.lexicon[item.text] for item in items if item.what is Is.THING]
        unmet |= {thing.unmet for thing in things if thing.note and thing.unmet is not None}
        if any(item.what is Is.AMENITY for item in items):
            unmet.add(UnmetCategory.COMMUNITY_AMENITIES)
        if unread:
            unmet.add(UnmetCategory.OTHER)
        if about_people:
            status = InterpretStatus.POLICY_REDIRECT
        elif asked.clarify:
            status = InterpretStatus.CLARIFY
        elif suggestions:
            status = InterpretStatus.SUGGEST
        else:
            status = InterpretStatus.OK
        return InterpretResult(
            status=status,
            operations=asked.operations,
            assumptions=asked.assumptions,
            unmet=tuple(category for category in UnmetCategory if category in unmet),
            clarify=asked.clarify,
            notice=Notice.NEUTRAL_PLACES if about_people else Notice.NONE,
            interpreter=self.name,
            degraded=False,
            usage=NO_USAGE,
            rests_on=asked.rests_on,
            suggestions=suggestions,
            unread=unread,
            not_in_release=missing,
        )


# --- For a caller that holds edits the reader did not make ----------------------------


class SentenceRead(NamedTuple):
    """A sentence of a request as the reader sees it. It holds no word of it, only where it is."""

    start: int
    end: int
    # The grammar makes the whole of it, it does not ask, and no sentence beside
    # it takes it back. An edit the reader made rests on words of such a sentence.
    known: bool
    # It holds a word that turns, takes off, caps or confines: "no", "less",
    # "don't care about", "within", "only".
    turning: bool
    # It holds a word of the written list of doubt, or a token with a mark inside it.
    doubt: bool
    # It asks and does not tell.
    asked: bool
    # A sentence beside it, which holds doubt and names nothing, is said of it.
    taken_back: bool


def _holds(sentence: _Sentence, phrases: frozenset[str], longest: int = 4) -> bool:
    """Whether a sentence holds one of some phrases, word for word and side by side."""
    tokens = sentence.line.tokens
    for at in range(len(tokens)):
        for size in range(1, longest + 1):
            run = tokens[at : at + size]
            if len(run) == size and not any(token.apart for token in run[1:]):
                spelt = (" ".join(t.word for t in run), " ".join(t.bare for t in run))
                if spelt[0] in phrases or spelt[1] in phrases:
                    return True
    return False


def _holds_doubt(sentence: _Sentence) -> bool:
    odd = any(token.odd for token in sentence.line.tokens)
    return odd or _holds(sentence, WORDS_OF_DOUBT | PHRASES_OF_DOUBT)


def sentences_of(
    text: str, names: Names | None = None, release: Release | None = None
) -> tuple[SentenceRead, ...]:
    """The sentences of a request, and which of them the reader could read.

    It is the reader's own reading, for a caller that must hold edits the
    reader did not make to the same test (the model-backed interpreter). The
    offsets count the characters of the text as it was typed.
    """
    return tuple(
        SentenceRead(
            start=sentence.line.start,
            end=sentence.line.end,
            known=sentence.plain and not sentence.taken_back,
            turning=_holds(sentence, MUST_BE_READ),
            doubt=_holds_doubt(sentence),
            asked=sentence.asked,
            taken_back=sentence.taken_back,
        )
        for sentence in _sentences(text, Grammar(names, release))
    )


# Every word that puts a sentence in doubt for a caller that holds a model's edits
# to the rules: the written list, and the words that turn a wish away.
SIGNS_OF_DOUBT: frozenset[str] = (
    WORDS_OF_DOUBT | PHRASES_OF_DOUBT | TURNS | TROUBLES | frozenset({"anywhere but"})
)
