"""One offer for each thing: what a model read, put with what the rules noticed.

The rules offer every thing they notice, with every way it runs, and choose
none. A model's reading of the same thing adds a guess to that offer, where
no check fired. A thing only the model read is an offer of its own. Every
offer of the rules is still there, with every way the rules gave it, so a
person never sees less than the rules alone give (ADR 0012).

Where the rules and the model name different things for the same words, it
is one offer with both as choices, so that nothing is counted twice. What a
word names is core's to say, so the guess is the rules' thing, taken the way
the model read the words.
"""

from collections import Counter
from collections.abc import Iterable, Sequence

from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import (
    DirectionChoice,
    InterpreterName,
    Polarity,
    SegmentChoice,
    TagId,
    TagShape,
    TenureChoice,
    Toward,
)
from burro_core.interpret import InterpretRequest, InterpretResult
from burro_core.interpret import Span as Stretch
from burro_core.ops import BudgetEdit

from burro_api.guard import DOUBTS, Check, Guarded, Reading, thing_named
from burro_api.offers import (
    FIRM,
    GUIDE,
    IGNORE,
    LESS,
    MORE,
    OFF,
    SKIP,
    Offer,
    Unsaid,
    UnsaidCode,
    Way,
    changes,
    journey_ways,
    of_the_rules,
)
from burro_api.typed import Span, Typed, is_nuisance, overlap

__all__ = ["offers_of"]

_FOR, _AGAINST = "for", "against"


def _spans(found: Iterable[Span]) -> tuple[Stretch, ...]:
    return tuple(Stretch(start=start, end=end) for start, end in sorted(set(found)))


def _held(offer: Offer) -> list[Span]:
    return [(span.start, span.end) for span in offer.spans]


def _marked(ways: Iterable[Way], meant: str, guess: bool) -> tuple[Way, ...]:
    """The ways, with the one a model pointed at marked, and marked as the guess if it is one."""
    return tuple(
        way.replace(meant=True, guess=guess) if meant and way.id == meant else way for way in ways
    )


def _minutes_of(offer: Offer) -> int:
    """The minutes the journey of an offer holds, or none."""
    found = [edit.max_minutes for way in offer.choices for edit in way.operations.commute_ops]
    return max(found, default=0)


def _with_the_rules(
    ways: Sequence[Way], meant: str, held: Offer
) -> tuple[Sequence[Way], str, tuple[Way, ...]]:
    """The ways of a journey a model read, put with the journey the rules offer to that place.

    A person never sees less than the rules alone give. So the minutes the
    rules read are kept where the model quoted none, as a guide: nothing in
    the words the model quoted makes them firm. And where the model read
    another number, the rules' own journey is still a choice.
    """
    theirs, ours = (
        _minutes_of(held),
        max((edit.max_minutes for way in ways for edit in way.operations.commute_ops), default=0),
    )
    if not theirs or theirs == ours:
        return ways, meant, ()
    if ours:
        kept = tuple(
            way.replace(id=f"{way.id}/{theirs}") for way in held.choices if way.id != IGNORE
        )
        return ways, meant, kept
    [first, *_] = [edit for way in ways for edit in way.operations.commute_ops]
    with_minutes = journey_ways(first.place_id, first.mode, theirs, False, first.action)
    return with_minutes, GUIDE, ()


def _in_order(ways: Iterable[Way]) -> tuple[Way, ...]:
    order = {MORE: 0, FIRM: 0, GUIDE: 0, LESS: 1, OFF: 2}
    return tuple(sorted(ways, key=lambda way: order.get(way.id, 3)))


def _thing_of(offer: Offer) -> str:
    """What an offer is of: its target, and the place where it is a journey."""
    for way in offer.choices:
        for journey in way.operations.commute_ops:
            return f"{offer.target} {journey.place_id}"
    return offer.target


def _sense(target: str, way: str) -> str:
    """Whether a way of a thing is a wish for the thing, or against it. Nothing for an end."""
    thing = thing_named(target)
    if thing is None or not way:
        return ""
    if way == OFF:
        return _AGAINST
    if isinstance(thing, TagId):
        return "" if TAGS[thing].shape is TagShape.SCALE else _FOR
    if FEATURES[thing].polarity is Polarity.EITHER:
        return _FOR if way == MORE else _AGAINST
    return _FOR


def _way_with(sense: str, offer: Offer, typed: Typed) -> str:
    """The way of an offer of the rules that runs as a model read another thing.

    A wish for one thing is a wish for the other in the way core's own words
    for it run: "nightlife" names the Buzzy end of Pace. A wish against the
    one is a wish for the other end, as the rules read an end that is turned
    away. Where core's words name no way, a thing that runs two ways has no
    guess.
    """
    thing = thing_named(offer.target)
    if thing is None or not sense:
        return ""
    named = [target for span in _held(offer) for target in typed.names(span, thing)]
    if isinstance(thing, TagId):
        if TAGS[thing].shape is not TagShape.SCALE:
            return MORE if sense == _FOR else OFF
        ends = {target.toward for target in named if not target.no_end}
        if len(ends) != 1:
            return ""
        return MORE if (ends == {Toward.HIGH}) is (sense == _FOR) else LESS
    if FEATURES[thing].polarity is Polarity.EITHER:
        fewer = any(target.direction is DirectionChoice.LESS for target in named)
        return LESS if fewer or sense == _AGAINST else MORE
    if sense == _AGAINST:
        return OFF
    return LESS if is_nuisance(thing) else MORE


def _covered_by(offer: Offer, budget: BudgetEdit) -> bool:
    """Whether a budget holds all that an offer of the rules would set."""
    held = [edit for way in offer.choices for edit in way.operations.budget_ops]
    return bool(held) and all(
        (not edit.amount or edit.amount == budget.amount)
        and (edit.tenure is TenureChoice.UNCHANGED or edit.tenure is budget.tenure)
        and (edit.segment is SegmentChoice.UNCHANGED or edit.segment is budget.segment)
        for edit in held
    )


class _Merge:
    """Puts each thing a model read where it belongs among the offers."""

    def __init__(self, request: InterpretRequest, typed: Typed, rules: Sequence[Offer]) -> None:
        self._spec = request.spec
        self._release = request.release
        self._typed = typed
        self.offers: list[Offer] = list(rules)
        self.fired: Counter[Check] = Counter()

    def _of_use(self, ways: Iterable[Way], asks_place: bool = False) -> tuple[Way, ...]:
        """Check 11: a way that would change nothing, or would be turned away, is not offered.

        A journey to a place that is yet to be chosen is tried with no place,
        and is kept: the place is the person's to choose.
        """
        return tuple(way for way in ways if asks_place or changes(way, self._spec, self._release))

    def _at(self, thing: str) -> int | None:
        return next((at for at, offer in enumerate(self.offers) if _thing_of(offer) == thing), None)

    def _beside(self, span: Span) -> int | None:
        """The wish that is offered for the same words, where one is."""
        for at, offer in enumerate(self.offers):
            wish = thing_named(offer.target) is not None
            if wish and any(overlap(span, held) for held in _held(offer)):
                return at
        return None

    def add(self, together: Sequence[Reading]) -> None:
        """One thing a model read, however often it read it."""
        first = together[0]
        fired = set[Check]().union(*(reading.fired for reading in together))
        meant = {reading.meant for reading in together}
        if len(meant) > 1:
            # Check 12: one thing, pulled two ways in one answer.
            fired.add(Check.TWO_WAYS)
            self.fired[Check.TWO_WAYS] += 1
        guess = not fired & DOUBTS
        pointed = first.meant if len(meant) == 1 else ""
        spans = [reading.span for reading in together]
        if first.target == "budget":
            self._budget(together, guess, spans)
        elif first.target == "commute":
            self._journey(first, fired, pointed, guess, spans)
        else:
            self._wish(first, fired, pointed, guess, spans)

    def _wish(
        self, read: Reading, fired: set[Check], meant: str, guess: bool, spans: list[Span]
    ) -> None:
        ways = self._of_use(read.ways)
        at = self._at(read.target)
        if at is not None:
            # The rules noticed the thing. Every way they give is kept, and
            # the way the model read is marked, where no check fired.
            held = self.offers[at]
            ruled = {way.id for way in held.choices}
            kept = {way.id: way.replace(ruled=way.id in ruled) for way in ways}
            for way in held.choices:
                if way.id != SKIP.id:
                    kept.setdefault(way.id, way)
            self.offers[at] = held.replace(
                choices=(*_marked(_in_order(kept.values()), meant, guess), SKIP),
                spans=_spans([*spans, *_held(held)]),
                whole_sentence=held.whole_sentence or Check.DISAGREES in fired,
            )
            return
        if not ways or (meant and meant not in {way.id for way in ways}):
            # Nothing the model read of it would change the search.
            self.fired[Check.NOTHING] += 1
            return
        beside = self._beside(spans[0])
        if beside is None:
            self.offers.append(
                Offer(
                    target=read.target,
                    label="",
                    spans=_spans(spans),
                    choices=(*_marked(ways, meant, guess), SKIP),
                    read_by=InterpreterName.MODEL,
                    whole_sentence=Check.DISAGREES in fired,
                )
            )
            return
        # Another thing is offered for the same words. It is one offer with
        # both as choices, so that nothing is counted twice. Where the rules
        # named the other thing, that is the guess, taken the way the model
        # read the words. Where a model named both, it has not said which the
        # words mean, and neither is the guess.
        held = self.offers[beside]
        sure = guess and held.read_by is InterpreterName.RULE
        same_way = _way_with(_sense(read.target, meant), held, self._typed) if sure else ""
        theirs = _marked([way for way in held.choices if way.id != SKIP.id], same_way, sure)
        others = tuple(
            way.replace(id=f"{read.target}/{way.id}")
            for way in _marked(ways, meant, False)
            if way.id != OFF
        )
        self.offers[beside] = held.replace(
            choices=(*(way if sure else way.replace(guess=False) for way in theirs), *others, SKIP),
            spans=_spans([*spans, *_held(held)]),
        )

    def _journey(
        self, read: Reading, fired: set[Check], meant: str, guess: bool, spans: list[Span]
    ) -> None:
        at = self._at(f"commute {read.key}") if read.key else None
        held = None if at is None else self.offers[at]
        if Check.LEAST in fired:
            # Burro has no way to keep a person away from a place, so no
            # journey is offered from words that may give a least. What the
            # rules offer stands, and says that no number was taken.
            least = Unsaid(code=UnsaidCode.LEAST)
            if held is not None and at is not None:
                # It says that no number was taken only where the rules took none.
                said = held.unsaid if _minutes_of(held) else (*held.unsaid, least)
                self.offers[at] = held.replace(unsaid=said, alone=True)
                return
            notice = Offer(
                target="commute",
                label="",
                spans=_spans(spans),
                choices=(SKIP,),
                read_by=InterpreterName.MODEL,
                unsaid=(least,),
                alone=True,
            )
            self.offers.append(notice)
            return
        asks_place = read.named_at is not None
        given, kept = read.ways, ()
        if held is not None:
            given, meant, kept = _with_the_rules(read.ways, meant, held)
        ways = self._of_use(given, asks_place)
        if not ways:
            self.fired[Check.NOTHING] += 1
            return
        named = [] if read.named_at is None else [read.named_at]
        offer = Offer(
            target="commute",
            label="" if held is None else held.label,
            spans=_spans([*spans, *([] if held is None else _held(held)), *named]),
            choices=(*_marked(ways, meant, guess), *kept, SKIP),
            read_by=InterpreterName.MODEL if held is None else InterpreterName.RULE,
            unsaid=read.unsaid,
            asks_place=asks_place,
            named_at=(
                None
                if read.named_at is None
                else Stretch(start=read.named_at[0], end=read.named_at[1])
            ),
            options=read.options,
        )
        if at is None:
            self.offers.append(offer)
        else:
            self.offers[at] = offer

    def _budget(self, together: Sequence[Reading], guess: bool, spans: list[Span]) -> None:
        one = len(together) == 1
        ways: list[Way] = []
        for reading in together:
            of_use = self._of_use(reading.ways)
            if one:
                ways += _marked(of_use, reading.meant, guess)
                continue
            # Two budgets in one answer: each is a choice, as a guide, and neither the guess.
            guide = next((way for way in of_use if way.id != FIRM), None)
            if guide is not None:
                ways.append(guide.replace(id=f"{guide.id}/{len(ways)}", meant=True))
        if not ways:
            self.fired[Check.NOTHING] += 1
            return
        budgets = [edit for way in ways for edit in way.operations.budget_ops]
        # What the rules noticed of the same budget is part of this offer. What
        # they noticed beside it, another amount or another size, stands as it was.
        folded = [
            offer
            for offer in self.offers
            if one
            and offer.target in ("budget", "tenure")
            and any(_covered_by(offer, budget) for budget in budgets)
        ]
        around = self._typed.sentences((min(spans)[0], max(end for _, end in spans)))
        beside = [held for offer in folded for held in _held(offer) if overlap(around, held)]
        self.offers = [offer for offer in self.offers if offer not in folded]
        self.offers.append(
            Offer(
                target="budget",
                label="",
                spans=_spans([*spans, *beside]),
                choices=(*ways, SKIP),
                read_by=InterpreterName.MODEL,
                unsaid=tuple(unsaid for reading in together for unsaid in reading.unsaid),
            )
        )


def offers_of(
    found: Guarded, request: InterpretRequest, typed: Typed, ruled: InterpretResult
) -> tuple[tuple[Offer, ...], Counter[Check]]:
    """What is offered: what the rules noticed, with what a model read put beside it.

    There is one offer for each thing, in the order of their words. With
    them comes how often the checks fired that are made once every reading is
    in: one thing pulled two ways, and what would change nothing.
    """
    merge = _Merge(request, typed, [of_the_rules(suggestion) for suggestion in ruled.suggestions])
    things: dict[tuple[str, str, Span | None], list[Reading]] = {}
    for reading in found.readings:
        # A place that is asked about is told apart by where its name stands.
        things.setdefault((reading.target, reading.key, reading.named_at), []).append(reading)
    for together in things.values():
        merge.add(together)
    # A model read the words, so what it did not read is for the person: "add
    # all" takes what Burro guesses, and no thing that was only noticed.
    left = (
        offer if any(way.guess for way in offer.choices) else offer.replace(alone=True)
        for offer in merge.offers
    )
    return tuple(sorted(left, key=lambda offer: offer.spans[0].start)), merge.fired
