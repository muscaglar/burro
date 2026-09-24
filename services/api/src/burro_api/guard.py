"""What code checks of a model's answer before any of it is offered (ADR 0012).

A model says which thing, and which words of the person's. Code says the
rest: which way, how much, how firm, by what way of travelling, and whether
the thing may be offered at all. Nothing a model reads is applied. What is
left of its answer becomes offers, beside what the rules noticed (`merge.py`).

Each check is numbered as the contract numbers it (section 8.2). A check
drops a reading, or puts right a field of it that is code's to say, or takes
the guess away, so that the thing is offered with every way open and none
marked.

Four fields of an answer are not read: `direction` on a thing that runs one
way, `value`, `strictness` and `provenance`. Where one of them says what code
would not, the check that stands in its place is counted.

Nothing here decides what a word means. Every list of words is core's
(`typed.py`). Checks 3 and 4 are a net with holes: no list of the words that
turn a wish round is ever whole. What is known to get through is held in the
tests as tests that are expected to fail.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from burro_core.catalogue import FEATURES, HOLDS_CRIME, RANKED_AS, TAGS
from burro_core.ids import (
    BudgetAction,
    CommuteAction,
    Dimension,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    FeatureKind,
    InterpreterName,
    ModeChoice,
    Notice,
    OpsGroup,
    Polarity,
    SegmentChoice,
    Step,
    StrictnessChoice,
    TagId,
    TagShape,
    Tenure,
    TenureChoice,
    TowardChoice,
    UnmetCategory,
    WeightAction,
    segments_for,
)
from burro_core.interpret import ClarifyOption, InterpretRequest, InterpretResult, Suggestion
from burro_core.ops import BudgetEdit, TagEdit, WeightEdit
from burro_core.places import MAX_OPTIONS, Names, normalise
from burro_core.spec import LIMITS

from burro_api.answer import (
    ModelBudgetEdit,
    ModelCommuteEdit,
    ModelOutput,
    ModelTagEdit,
    ModelUnmet,
    ModelWeightEdit,
)
from burro_api.offers import (
    FIRM,
    GUIDE,
    LESS,
    MORE,
    OFF,
    Degree,
    Unsaid,
    UnsaidCode,
    Way,
    budget_ways,
    journey_ways,
    ways_of,
)
from burro_api.typed import (
    CYCLES,
    DOUBT,
    ESSENTIALLY,
    FIRMLY_OF_MINUTES,
    FIRMLY_OF_MONEY,
    NEAR_ON_FOOT,
    SMALL,
    WALKS,
    Span,
    Typed,
    holds,
    in_doubt,
    is_nuisance,
    not_minded,
    overlap,
    stands_against,
    without,
)

__all__ = ["DOUBTS", "Check", "Guarded", "Reading", "guarded", "settled", "thing_named"]


class Check(StrEnum):
    """Why a reading of a model's is not offered as the model made it.

    It is counted and never served. The first thirteen are the checks of the
    contract, by their numbers.
    """

    WORDS = "01_the_words_are_the_persons"
    NAME = "02_a_name_is_the_whole_of_a_name"
    LEAST = "03_a_least_is_never_a_most"
    TURNED = "04_raised_against_a_word_that_turns"
    NO_END = "05_a_scale_with_no_end"
    CRIME = "06_recorded_crime"
    FIRM = "07_how_firm_is_codes"
    MODE = "08_the_way_of_travelling_is_codes"
    NUMBER = "09_no_number_of_the_models"
    SIZE = "10_a_budget_keeps_its_amount"
    NOTHING = "11_would_change_nothing"
    TWO_WAYS = "12_one_thing_pulled_two_ways"
    PEOPLE = "13_who_lives_somewhere"
    # What is never offered from a model, and what the thirteen rest on.
    DIRECTION = "a_direction_against_the_one_way_a_thing_runs"
    DISAGREES = "the_rules_read_the_words_the_other_way"
    NOT_TYPED = "a_number_the_person_did_not_type"
    NEAREST = "the_rules_offer_what_is_nearest_for_the_words"
    AREA = "a_rule_for_an_area_is_the_rules"
    NOT_WORDED = "no_offer_is_worded_for_it"


# The checks that take the guess away and leave the thing offered, with every way open.
DOUBTS = frozenset(
    {Check.TURNED, Check.NO_END, Check.TWO_WAYS, Check.DIRECTION, Check.DISAGREES, Check.LEAST}
)
_DOWN = frozenset({Step.DOWN_SMALL, Step.DOWN_LARGE})


@dataclass(frozen=True)
class Reading:
    """One thing a model read, where its words stand, and the ways code makes for it."""

    # As a suggestion's target: `feature:<id>`, `tag:<id>`, `commute` or `budget`.
    target: str
    # What it is of, to tell two offers of one kind apart: the id of a place,
    # and nothing for a feature, a vibe or a budget.
    key: str
    span: Span
    # Every way the thing runs. Which of them a search has a use for is asked later.
    ways: tuple[Way, ...]
    # The way the model's answer pointed at, or nothing where it named none.
    meant: str = ""
    fired: frozenset[Check] = frozenset()
    unsaid: tuple[Unsaid, ...] = ()
    # The journey is to a place the release does not hold, which stands here in the text.
    named_at: Span | None = None
    options: tuple[ClarifyOption, ...] = ()


@dataclass
class Guarded:
    """What is left of a model's answer, and how often each check fired."""

    readings: list[Reading] = field(default_factory=list[Reading])
    fired: Counter[Check] = field(default_factory=Counter[Check])
    # The request is about who lives somewhere: the rules say so, or the model does.
    about_people: bool = False
    # What the model said no feature covers, and where the person said it.
    unmet: list[tuple[UnmetCategory, Span | None]] = field(
        default_factory=list[tuple[UnmetCategory, Span | None]]
    )


def thing_named(target: str) -> FeatureId | TagId | None:
    """The feature or the vibe a target names, or nothing where it names neither."""
    kind, _, named = target.partition(":")
    if kind == "feature":
        return FeatureId(named)
    return TagId(named) if kind == "tag" else None


def _against(action: WeightAction, step: Step, value: float) -> bool:
    """Whether an edit takes a thing off or turns it down. No number is taken from it.

    To set a thing to nothing is to take it off. Any other number a model
    gives says that the thing is wanted, and not how much.
    """
    if action is WeightAction.REMOVE:
        return True
    if action is WeightAction.SET:
        return value <= 0
    return step in _DOWN


def _way_of(edit: WeightEdit | TagEdit) -> str:
    """The way an edit of the rules runs, as the ways of an offer are named."""
    if edit.action is WeightAction.REMOVE or edit.step in _DOWN:
        return OFF
    if isinstance(edit, TagEdit):
        return LESS if edit.toward is TowardChoice.LOW else MORE
    feature = FEATURES[edit.feature_id]
    if feature.polarity is Polarity.EITHER:
        return LESS if edit.direction is DirectionChoice.LESS else MORE
    return LESS if feature.kind is FeatureKind.NUISANCE else MORE


def _ways_the_rules_read(by_sentence: InterpretResult) -> dict[str, list[tuple[str, Span]]]:
    """Each wish the rules read in a sentence they know: which way it runs, and where."""
    found: dict[str, list[tuple[str, Span]]] = {}
    edits = by_sentence.operations
    for rests in by_sentence.rests_on:
        if rests.group is OpsGroup.WEIGHT and rests.index < len(edits.weight_ops):
            weight = edits.weight_ops[rests.index]
            target, way = f"feature:{weight.feature_id.value}", _way_of(weight)
        elif rests.group is OpsGroup.TAG and rests.index < len(edits.tag_ops):
            tag = edits.tag_ops[rests.index]
            target, way = f"tag:{tag.tag_id.value}", _way_of(tag)
        else:
            continue
        found.setdefault(target, []).append((way, (rests.start, rests.end)))
    return found


class _Guard:
    """Goes through a model's answer, and keeps of each edit what code can say for itself."""

    def __init__(
        self,
        request: InterpretRequest,
        typed: Typed,
        names: Names,
        ruled: InterpretResult,
        by_sentence: InterpretResult,
    ) -> None:
        self._spec = request.spec
        self._typed = typed
        self._names = names
        self._people = typed.about_people()
        # A community's amenity is no wish about people, and no feature
        # covers it. What a model reads into one is a reading of who goes
        # there, so nothing is offered that rests on the words for one.
        self._amenities = typed.amenities()
        # Where the words stand that the rules offer what is nearest for, and
        # the words they offer a vibe that counts recorded crime for, with a
        # note or with none.
        self._nearest = tuple(
            (span.start, span.end)
            for suggestion in ruled.suggestions
            if suggestion.note or thing_named(suggestion.target) in HOLDS_CRIME
            for span in suggestion.spans
        )
        # Where the rules noticed each thing, which is where core finds it named.
        self._noticed: dict[str, list[Span]] = {}
        for suggestion in ruled.suggestions:
            held = self._noticed.setdefault(suggestion.target, [])
            held += [(span.start, span.end) for span in suggestion.spans]
        self._read = _ways_the_rules_read(by_sentence)
        # The tenures the rules noticed a word for, which a budget may then hold.
        self._tenures = frozenset(
            edit.tenure
            for suggestion in ruled.suggestions
            for choice in suggestion.choices
            for edit in choice.operations.budget_ops
            if edit.tenure is not TenureChoice.UNCHANGED
        )
        self.found = Guarded()

    # What every reading is held to.

    def _drop(self, check: Check) -> None:
        self.found.fired[check] += 1

    def _about_people(self, *spans: Span) -> bool:
        """Check 13: whether some words are part of a wish about who lives somewhere.

        A model chooses the words it quotes, and may leave out the ones that
        say whom the wish is about. So the words are read with the whole of
        the clause they stand in, "somewhere lively", of "somewhere lively
        for young professionals". And words in which core finds no thing, no
        name and no number are no wish of their own: beside a wish about
        people in one sentence, they are part of it, "like me", of "young
        professionals, like me". Nor is anything offered that rests on the
        words for a community's amenity: "near a synagogue".
        """

        def beside(reach: Span) -> bool:
            return any(overlap(reach, people) for people in self._people)

        return any(
            beside(self._typed.clause(span))
            or (beside(self._typed.sentences(span)) and not self._typed.reads(span))
            or any(overlap(span, amenity) for amenity in self._amenities)
            for span in spans
        )

    def _stands(self, words: str) -> Span | None:
        """Where the words of a wish stand, or nothing where the wish is not to be offered.

        Check 1: the words are the person's, and say something: a quote made
        of words that name nothing, "a", "I want", is no quote. Check 13: no
        offer rests on a wish about who lives somewhere. And what the rules
        offer what is nearest for is the rules' to offer: "safe", "a sense of
        community", and every word core adds with a note of what Burro cannot
        measure. So is a word they offer a vibe that counts recorded crime
        for: "gritty", and a word for a smart area or a rough one where core
        reads it towards an end of that scale.
        """
        span = self._typed.find(words)
        if span is None or not self._typed.says_something(span):
            self._drop(Check.WORDS)
        elif self._about_people(span):
            self._drop(Check.PEOPLE)
        elif any(overlap(span, nearest) for nearest in self._nearest):
            self._drop(Check.NEAREST)
        else:
            return span
        return None

    def _degree(self, target: str, span: Span, fired: set[Check], given: bool) -> Degree:
        """Check 9: how much a wish counts is read from the person's words, never a number.

        It is read where the thing stands. Where the rules noticed the
        thing, that is the clause they noticed it in, however much a model
        quoted: "essential", of "a park is essential, and maybe pubs", is
        not said of the pubs. Where they did not, it is the words a model
        quoted, and nothing makes a thing count above all in a quote that
        runs on past a mark.
        """
        if given:
            fired.add(Check.NUMBER)
        noticed = self._noticed.get(target, ())
        led_up = [self._typed.led_up_to(where) for where in noticed or (span,)]
        if noticed:
            around = [self._typed.clause(where) for where in noticed]
        else:
            first = self._typed.clause((span[0], span[0] + 1))
            around = [self._typed.led_up_to(span)] if span[1] <= first[1] else []
        if any(holds(self._typed.said(reach), ESSENTIALLY) for reach in around):
            return Degree.ESSENTIAL
        small = any(holds(self._typed.said(reach), SMALL) for reach in led_up)
        return Degree.SMALL if small else Degree.MENTION

    def _turned(self, target: str, span: Span, thing: FeatureId | TagId) -> bool:
        """Check 4: whether a wish for a thing stands with a word that turns a wish away.

        It is asked of what leads up to the words a model quoted, and of what
        leads up to the thing wherever the rules noticed it. A model chooses
        the words it quotes, and may rest a thing on words that stand clear
        of what turns it: "is essential", of "I hate parks. But a station is
        essential".
        """
        noticed = self._noticed.get(target, ())
        if noticed and is_nuisance(thing):
            return any(self._not_minded(where, thing) for where in noticed)
        stands = [span, *noticed]
        return any(in_doubt(self._typed, self._typed.led_up_to(where), thing) for where in stands)

    def _not_minded(self, where: Span, thing: FeatureId | TagId) -> bool:
        """Whether a nuisance, where the rules noticed it, is not said to be unwanted.

        What is said of it is read as far as the next thing the rules
        noticed either way: "not bothered about" is said of the burglary, in
        "not bothered about burglary but violence scares me".
        """
        others = [other for spans in self._noticed.values() for other in spans]
        return not_minded(self._typed, where, thing, others)

    def _disagrees(self, target: str, span: Span, meant: str) -> bool:
        """Whether the rules read the same thing the other way, in the same sentence."""
        return any(
            way != meant and self._typed.same_sentence(span, where)
            for way, where in self._read.get(target, ())
        )

    def _keep(
        self,
        target: str,
        key: str,
        span: Span,
        ways: tuple[Way, ...],
        meant: str,
        fired: set[Check],
        unsaid: tuple[Unsaid, ...] = (),
        named_at: Span | None = None,
        options: tuple[ClarifyOption, ...] = (),
    ) -> None:
        self.found.fired.update(fired)
        self.found.readings.append(
            Reading(target, key, span, ways, meant, frozenset(fired), unsaid, named_at, options)
        )

    # Each kind of edit.

    def weight(self, sent: ModelWeightEdit) -> None:
        span = self._stands(sent.words)
        if span is None:
            return
        # A thing that is shown and never ranked on is read as a wish for the thing that is
        # ranked on in its place, as core reads a word that names it.
        sent = sent.replace(feature_id=RANKED_AS.get(sent.feature_id, sent.feature_id))
        feature = FEATURES[sent.feature_id]
        target = f"feature:{sent.feature_id.value}"
        named = self._typed.names(self._typed.led_up_to(span), sent.feature_id)
        stated = any(one.provenance is EditProvenance.STATED for one in named)
        if feature.dimension is Dimension.CRIME and not stated:
            # Check 6: whether crime was asked for by name is never the model's to say.
            self._drop(Check.CRIME)
            return
        fired: set[Check] = set()
        against = _against(sent.action, sent.step, sent.value)
        if feature.polarity is Polarity.EITHER:
            meant = LESS if against or sent.direction is DirectionChoice.LESS else MORE
            said = {
                one.direction
                for one in self._typed.names(span, sent.feature_id)
                if one.direction is not DirectionChoice.DEFAULT
            }
            if said and DirectionChoice(meant) not in said:
                # The words say which way in core's own phrase, and the model read the other.
                fired.add(Check.DISAGREES)
        else:
            meant = OFF if against else (LESS if is_nuisance(sent.feature_id) else MORE)
            if not against and sent.direction not in (
                DirectionChoice.DEFAULT,
                DirectionChoice(feature.polarity.value),
            ):
                # The field is not read. Written against the one way the thing
                # runs, it shows that the model did not know which way that is.
                fired.add(Check.DIRECTION)
        # To want fewer of a thing is the wish that a word that turns makes.
        fewer = feature.polarity is Polarity.EITHER and meant == LESS
        if meant != OFF and not fewer and self._turned(target, span, sent.feature_id):
            fired.add(Check.TURNED)
        given = sent.action is WeightAction.SET and sent.value > 0
        degree = self._degree(target, span, fired, given)
        if self._disagrees(target, span, meant):
            fired.add(Check.DISAGREES)
        self._keep(target, "", span, ways_of(sent.feature_id, degree), meant, fired)

    def tag(self, sent: ModelTagEdit) -> None:
        span = self._stands(sent.words)
        if span is None:
            return
        if sent.tag_id in HOLDS_CRIME:
            # A vibe that counts recorded crime is never a model's to offer,
            # towards either end. Where the words name it, the rules offer it.
            self._drop(Check.CRIME)
            return
        target = f"tag:{sent.tag_id.value}"
        fired: set[Check] = set()
        against = _against(sent.action, sent.step, sent.value)
        scale = TAGS[sent.tag_id].shape is TagShape.SCALE
        if scale and sent.toward is TowardChoice.DEFAULT:
            # Check 5: the model named a scale and no end of it.
            meant = OFF if against else ""
            if not against:
                fired.add(Check.NO_END)
        elif scale:
            meant = MORE if sent.toward is TowardChoice.HIGH else LESS
            if against:
                # Less of one end is not said to be more of the other.
                fired.add(Check.NO_END)
            named = self._typed.names(self._typed.clause(span), sent.tag_id)
            ends = {one.toward.value for one in named if not one.no_end}
            if not ends:
                # Check 5: no phrase of core's names an end of the scale in
                # these words, whichever of them the model chose. They name
                # the scale alone, or name it in no words core holds.
                fired.add(Check.NO_END)
            if ends and sent.toward.value not in ends:
                # The words name one end in core's own phrase for it, and the
                # model read the other.
                fired.add(Check.DISAGREES)
        else:
            meant = OFF if against else MORE
        if meant in (MORE, LESS) and self._turned(target, span, sent.tag_id):
            fired.add(Check.TURNED)
        given = sent.action is WeightAction.SET and sent.value > 0
        degree = self._degree(target, span, fired, given)
        if meant and self._disagrees(target, span, meant):
            fired.add(Check.DISAGREES)
        self._keep(target, "", span, ways_of(sent.tag_id, degree), meant, fired)

    def budget(self, sent: ModelBudgetEdit) -> None:
        span = self._stands(sent.words)
        if span is None:
            return
        if sent.action is not BudgetAction.SET:
            # A step of the budget, and a budget taken off: no offer is worded for either.
            self._drop(Check.NOT_WORDED)
            return
        if sent.amount and sent.amount not in self._typed.amounts(span):
            self._drop(Check.NOT_TYPED)
            return
        fired: set[Check] = set()
        unsaid: list[Unsaid] = []
        tenure = self._tenure(sent)
        held = self._spec.tenure if tenure is TenureChoice.UNCHANGED else Tenure(tenure.value)
        segment = sent.segment
        suits = {fits.value for fits in segments_for(held)}
        if segment is not SegmentChoice.UNCHANGED and segment.value not in suits:
            # Check 10: a size that does not suit the tenure is left out, and the amount kept.
            segment = SegmentChoice.UNCHANGED
            fired.add(Check.SIZE)
            unsaid.append(Unsaid(code=UnsaidCode.SIZE))
        nothing = TenureChoice.UNCHANGED is tenure and segment is SegmentChoice.UNCHANGED
        if not sent.amount and nothing:
            self._drop(Check.NOTHING)
            return
        firm = self._firm(span, sent.amount, sent.strictness, fired, FIRMLY_OF_MONEY)
        before = [before for before, _ in self._typed.beside(span, sent.amount)]
        if sent.amount and any(in_doubt(self._typed, reach, None) for reach in before):
            # Check 3: an amount that may be a least, or that is turned away,
            # is never offered as the most: "at least", "my budget isn't".
            fired.add(Check.LEAST)
        meant = (FIRM if firm else GUIDE) if sent.amount else MORE
        ways = budget_ways(tenure, sent.amount, segment, firm)
        self._keep("budget", "", span, ways, meant, fired, tuple(unsaid))

    def _tenure(self, sent: BudgetEdit) -> TenureChoice:
        """The tenure of a budget, where the words bear it out. Otherwise the search's own.

        An amount says which it is of where it cannot be of the other: no
        rent is as high as a price, and no price as low as a rent. Any other
        tenure is kept only where the rules noticed a word for it.
        """
        held = self._spec.tenure
        other = Tenure.BUY if held is Tenure.RENT else Tenure.RENT
        ours, theirs = LIMITS.money(held), LIMITS.money(other)
        if (
            sent.amount
            and theirs.minimum <= sent.amount <= theirs.maximum
            and not ours.minimum <= sent.amount <= ours.maximum
        ):
            return TenureChoice(other.value)
        if sent.tenure.value == held.value or sent.tenure in self._tenures:
            return sent.tenure
        return TenureChoice.UNCHANGED

    def _firm(
        self,
        span: Span,
        number: int,
        called: StrictnessChoice,
        fired: set[Check],
        firmly: Sequence[str],
        *,
        ends_a_range: bool = False,
    ) -> bool:
        """Check 7: a limit is firm only where the person's words make it one.

        The words are looked for against the number, straight before it or
        straight after it, and not in the whole of what the model quoted:
        "at most" of the bedrooms makes no budget firm, and nor does "no more
        than" of the minutes that come next. `firmly` is core's list for the
        kind of limit: "up to" makes a budget firm and no journey, and
        "within" a journey and no budget. A range of minutes is firm at its
        longer end, as it is where the rules read one.
        """
        firm = ends_a_range or any(
            stands_against(self._typed.said(before), self._typed.said(after), firmly)
            for before, after in self._typed.beside(span, number)
        )
        if called is StrictnessChoice.HARD and not firm:
            fired.add(Check.FIRM)
        return firm

    def commute(self, sent: ModelCommuteEdit) -> None:
        span = self._typed.find(sent.words)
        if span is None or not self._typed.says_something(span):
            self._drop(Check.WORDS)
            return
        if sent.position > 0 or sent.action is not CommuteAction.ADD:
            # To change a journey or take one off: no offer is worded for either.
            self._drop(Check.NOT_WORDED)
            return
        named = self._named(sent.destination_text, span)
        if named is None:
            self._drop(Check.NAME)
            return
        named_at, place_id = named
        reaches = (self._typed.led_up_to(span), self._typed.led_up_to(named_at))
        if self._about_people(span, named_at):
            self._drop(Check.PEOPLE)
            return
        fired: set[Check] = set()
        unsaid: list[Unsaid] = []
        minutes = self._minutes(sent.max_minutes, span, fired, unsaid)
        mode = self._mode(sent.mode, span, named_at, minutes, fired, unsaid)
        longest = any(one.code is UnsaidCode.RANGE and one.high == minutes for one in unsaid)
        firm = bool(minutes) and self._firm(
            span, minutes, sent.strictness, fired, FIRMLY_OF_MINUTES, ends_a_range=longest
        )
        if any(in_doubt(self._typed, reach, None) for reach in reaches):
            # Check 3: a number that may be a least is never offered as a most.
            fired.add(Check.LEAST)
        ways = journey_ways(place_id, mode, minutes, firm, CommuteAction.ADD)
        meant = (FIRM if firm else GUIDE) if minutes else MORE
        if place_id:
            self._keep("commute", place_id, span, ways, meant, fired, tuple(unsaid))
            return
        # Check 2: a place the release does not hold is asked about, and not dropped.
        fired.add(Check.NAME)
        typed_name = self._typed.text[named_at[0] : named_at[1]]
        options = tuple(
            ClarifyOption(id=match.id, name=match.name, kind=match.kind)
            for match in self._names.search_places(typed_name, MAX_OPTIONS)
        )
        self._keep("commute", "", span, ways, meant, fired, tuple(unsaid), named_at, options)

    def _named(self, name: str, span: Span) -> tuple[Span, str] | None:
        """Where a name stands as typed, and the place it is the whole name of, if any.

        The words of the name stand in the text side by side, as the model
        copied them. Where they are the whole of a name or an alias of the
        release, the place is that one. Where they are not, they stand in a
        sentence the edit rests on, and the place is for the person to
        choose. A name the person did not type is no name, and nor is part
        of a longer name that they did.
        """
        whole_of = self._names.whole_place(normalise(name))
        for found in self._typed.every(name):
            if self._typed.part_of_a_longer_name(found):
                continue
            beside = overlap(self._typed.sentences(span), self._typed.sentences(found))
            if beside or whole_of is not None:
                return found, whole_of or ""
        return None

    def _minutes(self, given: int, span: Span, fired: set[Check], unsaid: list[Unsaid]) -> int:
        """The minutes of a journey, where the person typed the number. Otherwise none."""
        if not given:
            return 0
        typed = self._typed.minutes(span)
        if given not in typed or not LIMITS.minutes_min <= given <= LIMITS.minutes_max:
            fired.add(Check.NOT_TYPED)
            return 0
        others = sorted(
            number
            for number in self._typed.range_of(span, given)
            if LIMITS.minutes_min <= number <= LIMITS.minutes_max
        )
        if len(others) > 1:
            unsaid.append(Unsaid(code=UnsaidCode.RANGE, low=others[0], high=others[-1], took=given))
        return given

    def _mode(
        self,
        given: ModeChoice,
        span: Span,
        named_at: Span,
        minutes: int,
        fired: set[Check],
        unsaid: list[Unsaid],
    ) -> ModeChoice:
        """Check 8: on foot or by bike only where a word beside the journey says so.

        It is read in the clause the name stands in and in the clause the
        minutes stand in, and not in all that a model quoted. A walk that is
        said of another thing is not the way to work, in another clause or
        in the same one: "a supermarket within walking distance", "and a
        park I can walk to". What core reads as how near a thing is, is the
        way of the journey only where the name of its place comes next.
        """
        beside = (named_at, *self._typed.where(span, minutes))
        said = " ".join(self._typed.said(self._typed.clause(where)) for where in beside)
        name = self._typed.said(named_at)
        to_the_place = holds(said, tuple(f"{near} {name}" for near in NEAR_ON_FOOT))
        named = holds(said, (*WALKS, *CYCLES))
        rest = without(said, NEAR_ON_FOOT)
        walked, cycled = to_the_place or holds(rest, WALKS), holds(rest, CYCLES)
        if walked != cycled:
            return ModeChoice.WALK if walked else ModeChoice.CYCLE
        if given in (ModeChoice.WALK, ModeChoice.CYCLE):
            fired.add(Check.MODE)
        # Where the words name a way that was not taken, the offer says so.
        unsaid.append(Unsaid(code=UnsaidCode.ANOTHER_WAY if named else UnsaidCode.MODE))
        return ModeChoice.UNCHANGED

    def unmet(self, sent: ModelUnmet) -> None:
        if sent.category is UnmetCategory.OTHER:
            return  # What nothing was made of is said by where the words stand.
        where = self._typed.find(sent.words) if sent.words else None
        self.found.unmet.append((sent.category, where))


def guarded(
    output: ModelOutput,
    request: InterpretRequest,
    typed: Typed,
    names: Names,
    ruled: InterpretResult,
    by_sentence: InterpretResult,
) -> Guarded:
    """What is left of a model's answer once every check has been made of it.

    `ruled` is what the rules made of the whole request, and `by_sentence`
    what they make of each sentence alone.
    """
    guard = _Guard(request, typed, names, ruled, by_sentence)
    heard = ruled.notice is Notice.NEUTRAL_PLACES
    guard.found.about_people = heard or bool(output.policy_flags)
    if output.policy_flags and not heard:
        # Check 13: the model says the request is about who lives somewhere,
        # and code cannot say which words it means. Nothing of its answer is
        # offered, and the rules' own offers stand.
        guard.found.fired[Check.PEOPLE] += output.count
        return guard.found
    for budget in output.budget_ops:
        guard.budget(budget)
    for commute in output.commute_ops:
        guard.commute(commute)
    for weight in output.weight_ops:
        guard.weight(weight)
    for tag in output.tag_ops:
        guard.tag(tag)
    # The rules notice every name typed in full, and offer both rules for it.
    # A model adds only a guess at which, and a guess at a filter is never
    # offered. And no offer is worded for a setting.
    guard.found.fired[Check.AREA] += len(output.area_ops)
    guard.found.fired[Check.NOT_WORDED] += len(output.setting_ops)
    for unmet in output.unmet:
        guard.unmet(unmet)
    guard.found.fired = +guard.found.fired
    return guard.found


def settled(offer: Suggestion, typed: Typed) -> bool:
    """Whether nothing beside an offer puts it in doubt, so that "add all" may take it.

    The rules offer a thing wherever it is named, and choose no way. Where
    there is one way to take it, "add all" would choose for them. So it takes
    a thing only where the clause it stands in holds no sign of doubt core
    lists, before the thing or after it: "schools are irrelevant". It is
    held to every sign of doubt, where a guess is held to the words that
    turn: a guess is shown to be pressed or not, and "add all" presses. And
    it takes nothing from a sentence that asks: "is a park worth it?"

    A nuisance that the rules noticed is held to what is said of it either
    side of where it is named, which is the least of the words the offer
    rests on: "crime doesn't bother me" is not settled.
    """
    thing = thing_named(offer.target)
    stands = [(span.start, span.end) for span in offer.spans]
    noticed = getattr(offer, "read_by", InterpreterName.RULE) is InterpreterName.RULE
    if noticed and thing is not None and is_nuisance(thing):
        named = [
            one
            for one in stands
            if not any(
                one != other and one[0] <= other[0] and other[1] <= one[1] for other in stands
            )
        ]
        if any(not_minded(typed, where, thing) for where in named):
            return False
    return not any(
        typed.asks(span) or in_doubt(typed, typed.clause(span), thing, DOUBT) for span in stands
    )
