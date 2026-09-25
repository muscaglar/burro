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
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    HOLDS_CRIME,
    HOLDS_RESIDENTS,
    RANKED_AS,
    ROUGH_GUIDES,
    TAGS,
)
from burro_core.ids import (
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
    Polarity,
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
    segments_for,
)
from burro_core.interpret import (
    COMMUTE_TARGET,
    MAY_BE_ANOTHERS,
    ClarifyOption,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    Suggestion,
)
from burro_core.ops import BudgetEdit, CommuteEdit, TagEdit, WeightEdit
from burro_core.places import MAX_OPTIONS, Names, normalise
from burro_core.spec import LIMITS, PreferenceSpec

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
    OF_A_HOME,
    OFF,
    Degree,
    Offer,
    Unsaid,
    UnsaidCode,
    Way,
    budget_ways,
    changes,
    for_a_house,
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
    somebody_elses,
    stands_against,
    turned_about,
    without,
)

__all__ = [
    "BEYOND",
    "DOUBTS",
    "Check",
    "Guarded",
    "Reading",
    "guarded",
    "plainly_said",
    "settled",
    "thing_named",
]


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
    ABOUT = "the_words_about_it_turn_it_round"
    ANOTHERS = "the_wish_is_somebody_elses"
    ROUGH = "a_rough_guide_is_taken_by_a_press_of_its_own"


# The checks that take the guess away and leave the thing offered, with every way open.
DOUBTS = frozenset(
    {
        *(Check.TURNED, Check.NO_END, Check.TWO_WAYS, Check.DIRECTION, Check.DISAGREES),
        *(Check.LEAST, Check.ABOUT, Check.ANOTHERS, Check.ROUGH),
    }
)
# The checks that are made of words which may stand beyond the clause of the thing. The
# whole of the sentence is then shown with the offer, so that the person sees them.
BEYOND = frozenset({Check.DISAGREES, Check.ABOUT, Check.ANOTHERS})
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
        # The things the rules offer with a note of what Burro cannot measure:
        # a reading of a word about identity, about wealth, about safety. Each
        # is theirs to offer, as they offer it with no model.
        self._kept = frozenset(
            suggestion.target for suggestion in ruled.suggestions if suggestion.note
        )
        # Where a place stands that the words ask to be kept away from. The rules offer
        # it with nothing to choose, and no reading of a model's makes a journey to it.
        self._kept_away = tuple(
            (span.start, span.end)
            for suggestion in ruled.suggestions
            if suggestion.target == COMMUTE_TARGET
            and all(way.direction is SuggestionDirection.IGNORE for way in suggestion.choices)
            for span in suggestion.spans
        )
        # The places that may be somebody else's, which the rules offer with no press.
        self._may_be_anothers = frozenset(
            edit.place_id
            for suggestion in ruled.suggestions
            if suggestion.note == MAY_BE_ANOTHERS
            for way in suggestion.choices
            for edit in way.operations.commute_ops
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

    def _is_the_rules(self, target: str) -> bool:
        """Whether a thing is one the rules offer as what is nearest, and so theirs alone.

        A model chooses the words it quotes. A reading of a word the rules
        keep is dropped where it rests on that word, and a model may name the
        same thing and rest it on any other: Village feel on "somewhere
        quiet", of "somewhere quiet, with a real identity". The guess would
        then be marked on the rules' own reading of the word. So a thing the
        rules offer with a note is theirs wherever a model says it stands.
        """
        if target not in self._kept:
            return False
        self._drop(Check.NEAREST)
        return True

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

    def _about(
        self, target: str, span: Span, thing: FeatureId | TagId, fired: set[Check], raised: bool
    ) -> None:
        """What the words about a thing say of the wish, wherever they stand in its sentence.

        A guess is never marked where they turn the wish round, or give it
        to someone else: "a station, heaven forbid", "my mum is after a
        park". It is asked of where the thing stands, as core finds it and
        as the model's words stand in the text, and never of what a model
        says it quoted: the words that turn a wish are the ones a model
        leaves out. What turns a wish is asked only of a wish for the thing.
        A wish against it is the wish a turn makes.
        """
        noticed = self._noticed.get(target, ())
        # Whose wish it is, is read where core finds the thing, where it does: a model that
        # quotes the whole of a sentence quotes what is said of every thing in it.
        if any(somebody_elses(self._typed, where) for where in noticed or (span,)):
            fired.add(Check.ANOTHERS)
        if raised and any(turned_about(self._typed, where, thing) for where in (span, *noticed)):
            fired.add(Check.ABOUT)

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
        if sent.feature_id in COUNTS_RESIDENTS:
            # Check 13: what counts who lives somewhere is never a model's to offer. The
            # rules offer it where the words name it, towards more and no other way.
            self._drop(Check.PEOPLE)
            return
        # A thing that is shown and never ranked on is read as a wish for the thing that is
        # ranked on in its place, as core reads a word that names it.
        sent = sent.replace(feature_id=RANKED_AS.get(sent.feature_id, sent.feature_id))
        feature = FEATURES[sent.feature_id]
        target = f"feature:{sent.feature_id.value}"
        if self._is_the_rules(target):
            return
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
        raised = meant != OFF and not fewer
        if raised and self._turned(target, span, sent.feature_id):
            fired.add(Check.TURNED)
        self._about(target, span, sent.feature_id, fired, raised)
        given = sent.action is WeightAction.SET and sent.value > 0
        degree = self._degree(target, span, fired, given)
        if self._disagrees(target, span, meant):
            fired.add(Check.DISAGREES)
        self._keep(target, "", span, ways_of(sent.feature_id, degree), meant, fired)

    def tag(self, sent: ModelTagEdit) -> None:
        span = self._stands(sent.words)
        if span is None:
            return
        if sent.tag_id in HOLDS_RESIDENTS:
            # Check 13, as of a measure: a vibe that counts who lives somewhere is the
            # rules' to offer, and never a model's.
            self._drop(Check.PEOPLE)
            return
        if sent.tag_id in HOLDS_CRIME:
            # A vibe that counts recorded crime is never a model's to offer,
            # towards either end. Where the words name it, the rules offer it.
            self._drop(Check.CRIME)
            return
        target = f"tag:{sent.tag_id.value}"
        if self._is_the_rules(target):
            return
        fired: set[Check] = set()
        against = _against(sent.action, sent.step, sent.value)
        scale = TAGS[sent.tag_id].shape is TagShape.SCALE
        named: Collection[Toward] = ()
        set_against = False
        if scale and not against:
            named, set_against = self._typed.ends_named(span, sent.tag_id)
        if not scale:
            meant = OFF if against else MORE
        elif sent.toward is TowardChoice.DEFAULT:
            meant = OFF if against else self._end_named(named, set_against, fired)
        else:
            meant = MORE if sent.toward is TowardChoice.HIGH else LESS
            if against or not named:
                # Check 5: less of one end is not said to be more of the other. And no
                # phrase of core's names an end of the scale in these words, whichever
                # of them the model chose. They name the scale alone, or name it in no
                # words core holds.
                fired.add(Check.NO_END)
            elif sent.toward.value not in named:
                # The words name one end in core's own phrase for it, and the
                # model read the other.
                fired.add(Check.DISAGREES)
        # Where the words name an end, what turns a wish has been read with each: an
        # end that is turned away is a wish for the other end.
        if meant in (MORE, LESS) and not named and self._turned(target, span, sent.tag_id):
            fired.add(Check.TURNED)
        self._about(target, span, sent.tag_id, fired, meant in (MORE, LESS))
        given = sent.action is WeightAction.SET and sent.value > 0
        degree = self._degree(target, span, fired, given)
        if meant and self._disagrees(target, span, meant):
            fired.add(Check.DISAGREES)
        if sent.tag_id in ROUGH_GUIDES and not against:
            # A vibe that is a rough guide is taken by a press of its own, so a
            # model's guess of it is no guess. It is offered, and says what it is.
            fired.add(Check.ROUGH)
        self._keep(target, "", span, ways_of(sent.tag_id, degree), meant, fired)

    @staticmethod
    def _end_named(named: Collection[Toward], set_against: bool, fired: set[Check]) -> str:
        """The end of a scale that the person named, where a model named the scale alone.

        A guess takes the end the person named, where they said which by
        turning one away: "houses not flats" is Houses, and "not buzzy" is
        Calm. Check 5: an end that is only named is no more than the rules
        noticed, and a model that names no end has added nothing to it:
        "nightlife, I'll pass". It stays a question.
        """
        if len(named) != 1 or not set_against:
            fired.add(Check.NO_END)
            return ""
        return MORE if Toward.HIGH in named else LESS

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
        if any(overlap(named_at, kept) for kept in self._kept_away):
            # Check 3, wherever the words stand in the sentence: a wish to be far from a
            # place is never a journey to it. What the rules say of it stands.
            self._drop(Check.LEAST)
            return
        fired: set[Check] = set()
        if place_id and place_id in self._may_be_anothers:
            # The place may be somebody else's, so the reading is no guess.
            fired.add(Check.ANOTHERS)
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

    Nor is a wish a model read, where the words about it turn it round or
    give it to someone else, wherever they stand in its sentence: the guess
    was taken from it, so it is asked and not said. What the rules alone
    noticed is offered as it was, and a journey is nobody's wish.
    """
    thing = thing_named(offer.target)
    stands = [(span.start, span.end) for span in offer.spans]
    least = [
        one
        for one in stands
        if not any(one != other and one[0] <= other[0] and other[1] <= one[1] for other in stands)
    ]
    noticed = getattr(offer, "read_by", InterpreterName.RULE) is InterpreterName.RULE
    read = any(getattr(way, "meant", False) for way in offer.choices)
    if thing is not None and any(
        (noticed and is_nuisance(thing) and not_minded(typed, where, thing))
        or (read and (turned_about(typed, where, thing) or somebody_elses(typed, where)))
        for where in least
    ):
        return False
    return not any(
        typed.asks(span) or in_doubt(typed, typed.clause(span), thing, DOUBT) for span in stands
    )


# The rules, to say what they would make of a clause were it all that was typed.
_RULES = RuleInterpreter()


def plainly_said(offers: Sequence[Offer], typed: Typed, spec: PreferenceSpec) -> tuple[Offer, ...]:
    """The offers, with Burro's guess on what a person plainly said of a home and of a journey.

    Decided on 2026-09-25: that a person is renting or buying, a budget with
    its amount, and a kind of home each carry the guess where the rules read
    it with no doubt, whether or not a model reads. So does a journey to one
    place with one time: `_journey_as_said`.

    **With no doubt is that the rules would apply the clause it stands in,
    were the clause all that was typed**: "max 400k for a 1 bed flat". So one
    press takes no more than Burro does unasked of a plain prompt. "I earn
    60k" and "I'm done renting" are no such clause, and are offered with no
    guess. It is what `settled` says too, and two things more. The words give
    one of each: one tenure, one amount, one kind of home. And the wish is
    nobody else's, read where the amount stands, or the word for the tenure
    or the home: "my partner wants to buy".

    A budget for a house of no kind is plainly said too, of a terraced
    house: the rules apply it so, and say that the kind is assumed. The guess
    stands on that way, and every other kind of house is one press away.

    An "if" that leads a clause in is no doubt: "if I'm buying" says which of
    renting and buying the rest is said of, and is read as "I'm buying".
    Where it sets one case against another, "if I rent ..., if I buy ...",
    the words name both tenures, and nothing is the guess.

    Whose wish it is and which tenure is meant are asked of a model's reading
    too. Where either is in doubt no guess stands on what is said of a home,
    whoever read it, so that one press takes none of it.
    """

    def said(offer: Offer) -> list[Way]:
        """The ways of an offer that the words give: of a budget for a house, the first."""
        ways = [way for way in offer.choices if way.direction is not SuggestionDirection.IGNORE]
        return ways[:1] if for_a_house(offer) else ways

    edits = [
        edit
        for offer in offers
        if offer.target in OF_A_HOME
        for way in said(offer)
        for edit in way.operations.budget_ops
    ]
    named = {Tenure(e.tenure.value) for e in edits if e.tenure is not TenureChoice.UNCHANGED}
    one_tenure = len(typed.tenures() | named) < 2
    amounts = {edit.amount for edit in edits if edit.amount}
    kinds = {edit.segment for edit in edits if edit.segment is not SegmentChoice.UNCHANGED}

    def as_it_was_said(offer: Offer) -> Offer:
        ways = said(offer)
        held = [edit for way in ways for edit in way.operations.budget_ops]
        spans = [(span.start, span.end) for span in offer.spans]
        # A model chooses the words it quotes, so an amount is read where it stands.
        stands = [
            where
            for span in spans
            for edit in held
            if edit.amount
            for where in typed.where(span, edit.amount)
        ]
        if not one_tenure or any(somebody_elses(typed, where) for where in stands or spans):
            return offer.replace(choices=tuple(way.replace(guess=False) for way in offer.choices))
        two_of_it = any(
            (edit.amount and len(amounts) > 1)
            or (edit.segment is not SegmentChoice.UNCHANGED and len(kinds) > 1)
            for edit in held
        )
        plain = (
            len(ways) == 1
            and ways[0].ruled
            and not two_of_it
            and settled(offer, typed)
            and all(_applied_alone(typed, span, spec) for span in spans)
        )
        if not plain:
            return offer
        return offer.replace(choices=tuple(w.replace(guess=w is ways[0]) for w in offer.choices))

    def of_each(offer: Offer) -> Offer:
        if offer.target in OF_A_HOME:
            return as_it_was_said(offer)
        return _journey_as_said(offer, typed, spec) if offer.target == COMMUTE_TARGET else offer

    return tuple(of_each(offer) for offer in offers)


def _journey_as_said(offer: Offer, typed: Typed, spec: PreferenceSpec) -> Offer:
    """A journey the rules read with no doubt, offered both ways, with the guess on one.

    Decided on 2026-09-25. The rules offer a journey one way, as it was
    worded. Where the words make it a limit that way is firm, and no press
    takes a firm journey with others: so by the rules alone one press took
    nothing of "at most 40 minutes to work", and no model reads where none is
    turned on. A journey to one place with one time, which the rules would
    apply were its clause all that was typed, is now offered as a model's
    reading of it is: as a firm limit and as a guide, with the guess on the
    way the words give, and `in_add_all` takes the guide.

    What is offered is what the rules would apply of the clause, so the way
    of travelling is the one that was said. Of a range, "35-40min", the rules
    take the longer and read it as a limit, and the offer says so in its
    note. One time is one number of minutes, or one range, in the sentence
    the journey stands in: of "30-45 minutes, no more than 40" which is meant
    is the person's to say. A journey with no time has no limit to be firm,
    and is offered as it was. A journey is nobody's wish, so whose it is is
    not asked.
    """
    ways = [way for way in offer.choices if way.direction is not SuggestionDirection.IGNORE]
    if len(ways) != 1 or not ways[0].ruled or offer.asks_place or offer.alone:
        return offer
    if offer.note == MAY_BE_ANOTHERS:
        # It may be somebody else's place: it is offered, and no press takes it with others.
        return offer.replace(alone=True)
    noticed = ways[0].operations.commute_ops
    if len(noticed) != 1 or not noticed[0].place_id or not noticed[0].max_minutes:
        return offer
    if not settled(offer, typed):
        return offer
    stands = typed.sentences(
        (min(span.start for span in offer.spans), max(span.end for span in offer.spans))
    )
    if typed.minutes(stands) - typed.range_of(stands, noticed[0].max_minutes):
        return offer
    said = [_journey_alone(typed, (span.start, span.end), spec) for span in offer.spans]
    journey = said[0] if said else None
    if journey is None or any(one != journey for one in said):
        return offer
    if (journey.place_id, journey.max_minutes) != (noticed[0].place_id, noticed[0].max_minutes):
        return offer
    firm = journey.strictness is StrictnessChoice.HARD
    both = journey_ways(
        journey.place_id, journey.mode, journey.max_minutes, firm, CommuteAction.ADD
    )
    # Check 11 holds here too: a way that would change nothing is not offered.
    of_use = [way for way in both if changes(way, spec, typed.release)]
    if not of_use or of_use[0] is not both[0]:
        return offer
    skip = tuple(way for way in offer.choices if way.direction is SuggestionDirection.IGNORE)
    marked = tuple(way.replace(guess=way is both[0], ruled=True) for way in of_use)
    return offer.replace(choices=(*marked, *skip))


def _read_alone(typed: Typed, span: Span, spec: PreferenceSpec) -> InterpretResult | None:
    """What the rules make of the clause a stretch stands in, were it all that was typed.

    Nothing where they would not apply it. They apply a prompt only where
    the grammar makes the whole of it, so a clause they apply holds no word
    that they do not place: "earn", "deposit", "done".
    """
    words = typed.alone(span)
    if not words:
        return None
    read = _RULES.interpret(InterpretRequest(text=words, spec=spec, release=typed.release))
    return read if read.status is InterpretStatus.OK else None


def _applied_alone(typed: Typed, span: Span, spec: PreferenceSpec) -> bool:
    """Whether the rules would apply what a clause says of a home, were it all that was typed."""
    read = _read_alone(typed, span, spec)
    return read is not None and bool(read.operations.budget_ops)


def _journey_alone(typed: Typed, span: Span, spec: PreferenceSpec) -> CommuteEdit | None:
    """The one journey the rules would apply of a clause, were it all that was typed."""
    read = _read_alone(typed, span, spec)
    journeys = () if read is None else read.operations.commute_ops
    return journeys[0] if len(journeys) == 1 else None
