"""An offer: one thing that was noticed, the ways a person may take it, and Burro's guess.

The model proposes, the person confirms, code checks (ADR 0012). Nothing a
model reads is applied. What it reads becomes an offer, beside what the
rules noticed, and the two are one list: one offer for each thing, so that a
person never sees less than the rules alone give.

An offer is core's `Suggestion` with what a guess needs beside it. Where a
model read a thing, and no check of `guard.py` fired, the way it read is
marked as Burro's guess. So is the one way of what a person plainly said of
the home they look for, whether or not a model reads: that they are renting
or buying, a budget with its amount, a kind of home. And so is the way the
words give of a journey that was plainly said, to one place and with one
time, which is offered as a guide and as a firm limit. A person still
presses it.

Every way of every offer is made here, from the catalogue: which ways a
thing runs, and the edit each would send. A model says which thing and which
words, and never an edit.
"""

from collections.abc import Sequence
from enum import StrEnum

from burro_core._record import Record
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    HOLDS_CRIME,
    HOLDS_RESIDENTS,
    ROUGH_GUIDES,
    TAGS,
)
from burro_core.ids import (
    AreaAction,
    BudgetAction,
    CommuteAction,
    Dimension,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    FeatureKind,
    InterpreterName,
    ModeChoice,
    Polarity,
    Segment,
    SegmentChoice,
    Step,
    StrictnessChoice,
    SuggestionDirection,
    TagId,
    TagShape,
    TenureChoice,
    TowardChoice,
    WeightAction,
)
from burro_core.interpret import COMMUTE_TARGET, Choice, ClarifyOption, Span, Suggestion
from burro_core.ops import (
    NO_OPERATIONS,
    BudgetEdit,
    CommuteEdit,
    Operations,
    TagEdit,
    WeightEdit,
)
from burro_core.reducer import apply, given_way_spec
from burro_core.release import Release
from burro_core.spec import DEFAULT_HOUSE, PreferenceSpec

__all__ = [
    "IGNORE",
    "OF_A_HOME",
    "SKIP",
    "Degree",
    "Offer",
    "Unsaid",
    "UnsaidCode",
    "Way",
    "budget_ways",
    "changes",
    "counts_residents",
    "for_a_house",
    "holds_crime",
    "in_add_all",
    "is_a_rough_guide",
    "journey_ways",
    "kind_of_house",
    "of_the_rules",
    "ways_of",
]

# The kinds of house that what houses sold for is held by.
KINDS_OF_HOUSE = frozenset({Segment.TERRACED, Segment.SEMI_DETACHED, Segment.DETACHED})

_UI = EditProvenance.UI_EDIT
# What a client sends back to say that an offer was left alone.
IGNORE = "ignore"
MORE = "more"
LESS = "less"
# A thing with one way that counts already: to stop counting it.
OFF = "off"
GUIDE = "guide"
FIRM = "firm"
# The targets of what is said of the home a person looks for: whether they rent or buy, and
# the budget, which holds the amount and the kind of home.
OF_A_HOME = frozenset({"tenure", "budget"})


class Degree(StrEnum):
    """How much a wish counts, as code reads it from the person's words. Never a number."""

    SMALL = "small"  # "slightly", "a bit", "fairly"
    MENTION = "mention"  # the thing was named, and no more was said
    ESSENTIAL = "essential"  # "essential", "a must"


class Way(Choice):
    """One way an offer may be taken, and the edits it would send."""

    # Which way of its offer this is. A client sends it back to say what was pressed.
    id: str
    # Burro's guess: the way a model read the words, where no check fired, the one way
    # of what a person plainly said of the home they look for, and the way the words
    # give of a journey that was plainly said.
    guess: bool = False
    # The way a model's answer pointed at, marked as a guess or not. It is for
    # measuring a model, and is never served.
    meant: bool = False
    # The rules give this way of the thing, whoever else does. Never served.
    ruled: bool = False


class UnsaidCode(StrEnum):
    """What the person did not say, and Burro took for them."""

    MODE = "mode"  # no way of travelling was named
    ANOTHER_WAY = "another_way"  # a way of travelling was named, and was not taken
    MINUTES = "minutes"  # no number of minutes was given
    RANGE = "range"  # two numbers were given, and one was taken
    TENURE = "tenure"  # neither renting nor buying was said
    SIZE = "size"  # the size of home does not suit the tenure, and was left out
    LEAST = "least"  # a number of minutes that may be a least was not taken


class Unsaid(Record):
    code: UnsaidCode
    # For `range`: the least and the most that were given. For `minutes` and
    # `range`: what was taken.
    low: int = 0
    high: int = 0
    took: int = 0


class Offer(Suggestion):
    """A thing that was noticed, by the rules or by a model whose reading code has checked."""

    choices: tuple[Way, ...]  # pyright: ignore[reportIncompatibleVariableOverride]
    read_by: InterpreterName = InterpreterName.RULE
    # The whole sentence is shown with it, and not only the clause its words stand in.
    whole_sentence: bool = False
    unsaid: tuple[Unsaid, ...] = ()
    # The ways hold a journey to no place: the person is asked which place, and
    # the place they choose is put into the edit before it is sent.
    asks_place: bool = False
    # Where the name of that place stands in the text. Offsets, never words.
    named_at: Span | None = None
    # What the release holds that the words may name. Empty where it holds nothing alike.
    options: tuple[ClarifyOption, ...] = ()
    # It may never be added with others at one press, whatever its ways.
    alone: bool = False


SKIP = Way(id=IGNORE, direction=SuggestionDirection.IGNORE, label="Skip", operations=NO_OPERATIONS)


# --- The ways a thing runs, and the edit each would send -------------------------------


def _step(degree: Degree) -> tuple[WeightAction, float, Step]:
    if degree is Degree.ESSENTIAL:
        return WeightAction.SET, 1.0, Step.NONE
    step = Step.UP_SMALL if degree is Degree.SMALL else Step.UP_LARGE
    return WeightAction.NUDGE, 0.0, step


def _weigh(feature_id: FeatureId, direction: DirectionChoice, degree: Degree) -> Operations:
    action, value, step = _step(degree)
    edit = WeightEdit(
        action=action,
        feature_id=feature_id,
        value=value,
        step=step,
        direction=direction,
        provenance=_UI,
    )
    return NO_OPERATIONS.replace(weight_ops=(edit,))


def _unweigh(feature_id: FeatureId) -> Operations:
    edit = WeightEdit(
        action=WeightAction.REMOVE,
        feature_id=feature_id,
        value=0.0,
        step=Step.NONE,
        direction=DirectionChoice.DEFAULT,
        provenance=_UI,
    )
    return NO_OPERATIONS.replace(weight_ops=(edit,))


def _tag(tag_id: TagId, toward: TowardChoice, degree: Degree | None) -> Operations:
    action, value, step = (WeightAction.REMOVE, 0.0, Step.NONE) if degree is None else _step(degree)
    edit = TagEdit(
        action=action, tag_id=tag_id, value=value, step=step, toward=toward, provenance=_UI
    )
    return NO_OPERATIONS.replace(tag_ops=(edit,))


def _way(id: str, direction: SuggestionDirection, operations: Operations) -> Way:
    # The words of a way are written once it is known what stands beside it (`wording.py`).
    return Way(id=id, direction=direction, label="", operations=operations)


def ways_of(thing: FeatureId | TagId, degree: Degree = Degree.MENTION) -> tuple[Way, ...]:
    """Every way a feature or a vibe may be taken, whether or not it would change the search.

    A thing that runs two ways has both. A thing that runs one way has that
    way, and to stop counting it. `changes` says which of them a search has
    any use for.
    """
    more, less = SuggestionDirection.MORE, SuggestionDirection.LESS
    if isinstance(thing, TagId):
        off = _way(OFF, less, _tag(thing, TowardChoice.DEFAULT, None))
        towards_high = _way(MORE, more, _tag(thing, TowardChoice.HIGH, degree))
        if TAGS[thing].shape is TagShape.SCALE:
            return (towards_high, _way(LESS, less, _tag(thing, TowardChoice.LOW, degree)), off)
        return (towards_high, off)
    feature = FEATURES[thing]
    if feature.polarity is Polarity.EITHER:
        return (
            _way(MORE, more, _weigh(thing, DirectionChoice.MORE, degree)),
            _way(LESS, less, _weigh(thing, DirectionChoice.LESS, degree)),
        )
    wished = _weigh(thing, DirectionChoice.DEFAULT, degree)
    # The one way a nuisance runs is less of it, which is to care about it.
    towards = less if feature.kind is FeatureKind.NUISANCE else more
    return (
        _way(LESS if feature.kind is FeatureKind.NUISANCE else MORE, towards, wished),
        _way(OFF, less, _unweigh(thing)),
    )


def journey_ways(
    place_id: str, mode: ModeChoice, minutes: int, firm_first: bool, action: CommuteAction
) -> tuple[Way, ...]:
    """The ways a journey may be added: as a guide or as a firm limit, where minutes were given.

    A limit is firm first only where the person's words make it one. A
    journey with no minutes has no limit to be firm.
    """

    def journey(strictness: StrictnessChoice) -> Operations:
        edit = CommuteEdit(
            action=action,
            place_id=place_id,
            mode=mode,
            max_minutes=minutes,
            strictness=strictness,
            step=Step.NONE,
            provenance=_UI,
        )
        return NO_OPERATIONS.replace(commute_ops=(edit,))

    more = SuggestionDirection.MORE
    if not minutes:
        return (_way(MORE, more, journey(StrictnessChoice.UNCHANGED)),)
    guide = _way(GUIDE, more, journey(StrictnessChoice.SOFT))
    firm = _way(FIRM, more, journey(StrictnessChoice.HARD))
    return (firm, guide) if firm_first else (guide, firm)


def budget_ways(
    tenure: TenureChoice, amount: int, segment: SegmentChoice, firm_first: bool
) -> tuple[Way, ...]:
    """The ways a budget may be set: as a guide or as a firm limit, where an amount was given."""

    def budget(strictness: StrictnessChoice) -> Operations:
        edit = BudgetEdit(
            action=BudgetAction.SET,
            tenure=tenure,
            amount=amount,
            segment=segment,
            strictness=strictness,
            step=Step.NONE,
            provenance=_UI,
        )
        return NO_OPERATIONS.replace(budget_ops=(edit,))

    more = SuggestionDirection.MORE
    if not amount:
        return (_way(MORE, more, budget(StrictnessChoice.UNCHANGED)),)
    guide = _way(GUIDE, more, budget(StrictnessChoice.SOFT))
    firm = _way(FIRM, more, budget(StrictnessChoice.HARD))
    return (firm, guide) if firm_first else (guide, firm)


def changes(way: Choice, spec: PreferenceSpec, release: Release) -> bool:
    """Whether a way would change the search. One the reducer turns away changes nothing.

    It is tried on the spec with its defaults given way, which is what the
    reducer applies an edit to. A way that holds a journey to no place yet is
    tried with none, and is kept: the place is the person's to choose.
    """
    result = apply(given_way_spec(spec), way.operations, release)
    return not result.rejected and any(applied.changed for applied in result.applied)


# --- What the rules noticed, as an offer ---------------------------------------------------


def of_the_rules(suggestion: Suggestion) -> Offer:
    """What the rules noticed, as they gave it: every choice, and no guess."""
    if isinstance(suggestion, Offer):
        return suggestion
    ways = tuple(
        SKIP
        if choice.direction is SuggestionDirection.IGNORE
        else Way(
            id=_id_of(choice),
            direction=choice.direction,
            label=choice.label,
            operations=choice.operations,
            ruled=True,
        )
        for choice in suggestion.choices
    )
    return Offer(
        target=suggestion.target,
        label=suggestion.label,
        spans=suggestion.spans,
        choices=ways,
        note=suggestion.note,
    )


def _id_of(choice: Choice) -> str:
    """The way of a thing that a choice of the rules is, by the edit it holds.

    A budget for a house is offered once for each kind of house it may be
    held against, and each way is told from the others by its kind.
    """
    edits = choice.operations
    for weight in edits.weight_ops:
        if weight.action is WeightAction.REMOVE:
            return OFF
    for tag in edits.tag_ops:
        if tag.action is WeightAction.REMOVE:
            return OFF
    kind = kind_of_house(edits)
    return choice.direction.value if kind is None else kind.value


def kind_of_house(edits: Operations) -> Segment | None:
    """The kind of house that an amount is held against, where the edits hold both.

    The kind may stand in an edit of its own, before the amount, so that it
    can say whose it is: Burro's where a person named no kind of house.
    """
    kinds = [
        Segment(edit.segment.value)
        for edit in edits.budget_ops
        if edit.segment is not SegmentChoice.UNCHANGED
    ]
    amount = any(edit.amount for edit in edits.budget_ops)
    return kinds[-1] if amount and kinds and kinds[-1] in KINDS_OF_HOUSE else None


def for_a_house(offer: Offer) -> bool:
    """Whether an offer is a budget for a house of no kind, with the kind Burro takes first.

    Its ways differ only in the kind of house, and the first is held against
    `DEFAULT_HOUSE` in an edit that says the kind is Burro's.
    """
    ways = [way for way in offer.choices if way.direction is not SuggestionDirection.IGNORE]
    kinds = [kind_of_house(way.operations) for way in ways]
    if len(ways) < 2 or None in kinds or kinds[0] is not DEFAULT_HOUSE:
        return False
    first = ways[0].operations.budget_ops
    return all(way.ruled for way in ways) and first[0].provenance is EditProvenance.INFERRED


# --- What counts recorded crime, and what may be added at one press --------------------


def holds_crime(operations: Operations) -> bool:
    """Whether some edit sets recorded crime counting, by itself or inside a vibe."""
    return any(
        FEATURES[edit.feature_id].dimension is Dimension.CRIME for edit in operations.weight_ops
    ) or any(edit.tag_id in HOLDS_CRIME for edit in operations.tag_ops)


def counts_residents(operations: Operations) -> bool:
    """Whether some edit sets counting who lived somewhere, by a measure or inside a vibe."""
    return any(edit.feature_id in COUNTS_RESIDENTS for edit in operations.weight_ops) or any(
        edit.tag_id in HOLDS_RESIDENTS for edit in operations.tag_ops
    )


def is_a_rough_guide(operations: Operations) -> bool:
    """Whether some edit adds a vibe that is a rough guide. To take one off is not to add it."""
    return any(
        edit.tag_id in ROUGH_GUIDES and edit.action is not WeightAction.REMOVE
        for edit in operations.tag_ops
    )


def _firm_journey(operations: Operations) -> bool:
    return any(edit.strictness is StrictnessChoice.HARD for edit in operations.commute_ops)


def _rules_an_area(operations: Operations) -> bool:
    return any(edit.action is not AreaAction.CLEAR for edit in operations.area_ops)


def _taken_up(way: Way) -> bool:
    """Whether a way adds a wish at a mention or a small step, or sets what is no wish."""
    wishes: Sequence[WeightEdit | TagEdit] = (*way.operations.weight_ops, *way.operations.tag_ops)
    return all(
        wish.action is WeightAction.NUDGE and wish.step in (Step.UP_SMALL, Step.UP_LARGE)
        for wish in wishes
    )


def in_add_all(offer: Offer) -> Way | None:
    """The one way of an offer that "add all" takes, or nothing where it may take none.

    It takes a wish or a vibe at a mention or a small step, and a journey as
    a guide to a place named in full. And it takes what a person plainly said
    of the home they look for, which is what carries the guess: that they are
    renting or buying, the kind of home, and the budget as they worded it,
    firm where they used a firm word and a guide where they used none
    (decided on 2026-09-25). What is said of a home with no guess is for the
    person, and what Burro cannot hold of a home is said in its note.

    **It never takes a journey as a firm limit.** A journey is estimated from
    distance and no timetable stands behind it (ADR 0027), so one press must
    not leave areas out on an estimate. Where the guess is a firm journey,
    what is added is the guide, and a person makes it firm with a press of
    its own. It is so whoever read the journey, a model or the rules alone.

    Nor does it take a rule for an area, what runs two ways with no guess, a
    journey to a place the person has yet to choose, recorded crime, what
    counts who lives somewhere, or a vibe that is a rough guide, which is
    taken by a press of its own whoever read it and whatever is said of its
    offer (decided on 2026-09-25). A wish the rules offer with a note is a
    reading they keep for themselves, and is chosen by its own label. What
    was plainly said is taken with what is said of it: a kind of home with
    what Burro cannot hold of it, and a journey that carries the guess with
    which of two numbers was taken.
    """
    of_a_home = offer.target in OF_A_HOME
    ways = [way for way in offer.choices if way.direction is not SuggestionDirection.IGNORE]
    guessed = [way for way in ways if way.guess]
    said_plainly = of_a_home or (offer.target == COMMUTE_TARGET and bool(guessed))
    if offer.alone or offer.asks_place or (offer.note and not said_plainly):
        return None
    if guessed:
        taken = guessed[0]
        if _firm_journey(taken.operations):
            guides = [way for way in ways if way.id == GUIDE]
            if not guides:
                return None
            taken = guides[0]
    elif len(ways) == 1 and not of_a_home:
        # The rules' own: a thing there is one way to want.
        taken = ways[0]
    else:
        return None
    if holds_crime(taken.operations) or counts_residents(taken.operations):
        return None
    if is_a_rough_guide(taken.operations):
        return None
    if _firm_journey(taken.operations) or _rules_an_area(taken.operations):
        return None
    return taken if _taken_up(taken) and _names_its_place(taken) else None


def _names_its_place(way: Way) -> bool:
    return all(edit.place_id for edit in way.operations.commute_ops)
