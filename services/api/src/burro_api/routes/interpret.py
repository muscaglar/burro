"""Route 1: from what a person typed to typed edits, applied by the one reducer.

The text is read and dropped. What is kept about the call is metadata: which
interpreter was asked, how it went, how long it took and how many edits came
of it. If a model is slow, capped or broken, the rules answer in its place and
the person still gets their form. So they do where the provider would not
read what was typed, and the answer says that it would not.

Only what the rules read is applied. What a model read is served as offers,
each in four parts, and moves nothing until a person presses it. A caller
that will not wait for a model asks for the rules alone, and is told whether
a model has more to read.
"""

from collections import Counter
from collections.abc import Callable
from concurrent.futures import Future
from threading import Thread

from burro_core.grammar import Grammar
from burro_core.ids import InterpreterName, Tenure
from burro_core.interpret import (
    InterpretRequest,
    InterpretResult,
    NotInRelease,
    RestsOn,
    RuleInterpreter,
    Span,
    not_in_release_of,
    notice_text,
)
from burro_core.ops import Operations
from burro_core.reducer import ReducerResult, apply
from burro_core.spec import PreferenceSpec, spec_hash
from fastapi import APIRouter

from burro_api import logs
from burro_api.calls import Caller, CallRecord, CallStatus, Endpoint
from burro_api.deps import Context, Ctx, Deps
from burro_api.guard import settled
from burro_api.offers import of_the_rules
from burro_api.providers.interface import ModelCapped, ModelRefused, ModelTimeout
from burro_api.reader import Read, asks_a_model
from burro_api.routes.common import (
    PREFIX,
    WITH_BODY,
    RequestId,
    check,
    default_for,
    envelope,
    places_of,
)
from burro_api.typed import CYCLES, WALKS, Typed, holds
from burro_api.wire import (
    Envelope,
    InterpretBody,
    InterpretData,
    Suggestion,
    SuggestionChoice,
    UnmetAt,
)
from burro_api.wording import worded

router = APIRouter(prefix=PREFIX)


def within[T](seconds: float, call: Callable[[], T]) -> T:
    """What `call` returns, or `TimeoutError` if it takes longer than `seconds`.

    A model's client has a timeout of its own, but it times each read and not
    the whole call. This is the limit on how long a person waits. The call
    runs on a thread of its own, which is left to finish if it is late.
    """
    outcome: Future[T] = Future()

    def run() -> None:
        try:
            outcome.set_result(call())
        except BaseException as error:
            outcome.set_exception(error)

    Thread(target=run, daemon=True).start()
    return outcome.result(timeout=seconds)


RESTING = "model_resting"
# The rules, for when they answer in a model's place or are asked for alone.
# They make the names of a release ready once, so one is kept for every call.
_RULES = RuleInterpreter()


def _note_a_rest(deps: Deps) -> None:
    """Say once, by the provider's name, that it is left alone for a while. Nothing of a call."""
    begins = getattr(deps.interpreter, "begins_to_rest", None)
    if callable(begins) and begins() and deps.told.provider is not None:
        logs.warning(RESTING, provider=deps.told.provider)


def answer(
    deps: Deps, request: InterpretRequest, request_id: str = "", ask_model: bool = True
) -> tuple[InterpretResult, CallStatus]:
    """The interpreter's answer, or the rules' if it fails. It never raises for a model.

    Where the caller asked for the rules alone, the rules answer at once and
    no model is asked.
    """
    asked = deps.interpreter
    if isinstance(asked, RuleInterpreter) or not ask_model:
        by_rules = asked if isinstance(asked, RuleInterpreter) else _RULES
        result = by_rules.interpret(request)
        return result, CallStatus(result.status.value)
    # Looked at before the call as well as after, so that a rest which ended
    # with nobody asking is known to have ended.
    _note_a_rest(deps)
    try:
        result = within(deps.model_timeout_s, lambda: asked.interpret(request))
        return result, CallStatus(result.status.value)
    except (ModelTimeout, TimeoutError):
        failed = CallStatus.TIMEOUT
    except ModelCapped:
        failed = CallStatus.CAPPED
    except ModelRefused:
        # Sent as it was typed, and not read. Nothing of it is written down.
        failed = CallStatus.REFUSED
    except Exception as error:
        failed = CallStatus.ERROR
        logs.log_failure(error, request_id=request_id)
    _note_a_rest(deps)
    return _RULES.interpret(request).replace(degraded=True), failed


def _edits(operations: Operations) -> dict[str, int]:
    """How many edits in each group. Never the edits: a commute edit names a place."""
    return {
        "budget_ops": len(operations.budget_ops),
        "commute_ops": len(operations.commute_ops),
        "weight_ops": len(operations.weight_ops),
        "tag_ops": len(operations.tag_ops),
        "area_ops": len(operations.area_ops),
        "setting_ops": len(operations.setting_ops),
    }


def _in_the_text(start: int, end: int, text: str) -> bool:
    return 0 <= start < end <= len(text)


def as_sent(result: InterpretResult, text: str, lead: int) -> tuple[RestsOn, ...]:
    """Which words each edit rests on, as offsets into the text as it was sent.

    An interpreter reads the text without the space around it, and counts
    from where that begins. Only an edit that is served is pointed at, and
    only at words that are in the text.
    """
    served = _edits(result.operations)
    return tuple(
        rests.replace(start=rests.start + lead, end=rests.end + lead)
        for rests in result.rests_on
        if 0 <= rests.index < served[rests.group.value]
        and _in_the_text(rests.start, rests.end, text)
    )


def stretches(spans: tuple[Span, ...], text: str, lead: int) -> tuple[Span, ...]:
    """Some stretches of the text, as offsets into the text as it was sent. Never the words."""
    return tuple(
        Span(start=span.start + lead, end=span.end + lead)
        for span in spans
        if _in_the_text(span.start, span.end, text)
    )


def offered(
    result: InterpretResult, text: str, lead: int, spec: PreferenceSpec, typed: Typed
) -> tuple[Suggestion, ...]:
    """What was noticed, each in its four parts, with where its words stand as the text was sent.

    An offer says where its words stand, so one that points at nothing in
    the text is not served. The words of every part are Burro's own, made
    here for the rules' offers and a model's alike.
    """
    found: list[Suggestion] = []
    for suggestion in result.suggestions:
        spans = stretches(suggestion.spans, text, lead)
        if not spans:
            continue
        offer = of_the_rules(suggestion)
        # All that the offer rests on is shown: the words that end last may
        # not be the ones that begin last.
        around = (
            min(span.start for span in suggestion.spans),
            max(span.end for span in suggestion.spans),
        )
        sentences = typed.sentences(around)
        shown = sentences if offer.whole_sentence else typed.clause(around)
        # A word for walking or cycling that the offer did not take is said to be so.
        names_a_way = holds(typed.said(sentences), (*WALKS, *CYCLES))
        words = worded(offer, spec, typed.release, settled(offer, typed), names_a_way)
        named = () if offer.named_at is None else stretches((offer.named_at,), text, lead)
        found.append(
            Suggestion(
                target=offer.target,
                label=words.label,
                does=words.does,
                spans=spans,
                shown=Span(start=shown[0] + lead, end=shown[1] + lead),
                follows=words.follows,
                said=words.said,
                choices=tuple(
                    SuggestionChoice(
                        id=way.id,
                        direction=way.direction,
                        label=label,
                        guess=way.guess,
                        operations=way.operations,
                    )
                    for way, label in zip(offer.choices, words.labels, strict=True)
                ),
                note=offer.note,
                read_by=offer.read_by,
                add_all=words.add_all,
                needs=words.needs,
                asks_place=offer.asks_place,
                named_at=named[0] if named else None,
                options=offer.options,
            )
        )
    return tuple(found)


def unmet_at(result: InterpretResult, text: str, lead: int) -> tuple[UnmetAt, ...]:
    """Where the words stand that ask for what nothing measures, where a reader said which."""
    if not isinstance(result, Read):
        return ()
    return tuple(
        UnmetAt(category=category, span=span)
        for category, where in result.unmet_at
        for span in stretches((where,), text, lead)
    )


def missing(
    result: InterpretResult, reduced: ReducerResult, text: str, lead: int
) -> tuple[NotInRelease, ...]:
    """What was asked for that the release holds for no area, each by its name.

    It is said of every reading alike, whoever read the words: what the
    reducer turned away as not in the release, and what the reader noticed
    and did not offer. The words are given as offsets into the text as it
    was sent, and a thing is named whether or not its words can be pointed at.
    """
    return tuple(
        thing.replace(spans=stretches(thing.spans, text, lead))
        for thing in not_in_release_of(result, reduced.rejected)
    )


def _record(
    context: Context,
    request_id: str,
    result: InterpretResult,
    reduced: ReducerResult,
    status: CallStatus,
    latency_ms: int,
) -> None:
    deps, meta = context.deps, context.meta
    # A model was asked where it answered, or where the rules answered in its
    # place. A prompt the rules applied by themselves is the rules' call.
    by_model = result.interpreter is InterpreterName.MODEL or result.degraded
    asked = Caller.MODEL if by_model else Caller.RULE
    model = deps.model_id if by_model else ""
    # The provider that was asked, whether or not it answered. One of the four by name.
    provider = (deps.told.provider or "") if by_model else ""
    # Nothing of the spec is kept or logged, not even a hash of it (ADR 0011).
    deps.calls.add(
        CallRecord(
            call_id=deps.ids.call_id(),
            at=context.timestamp(),
            endpoint=Endpoint.INTERPRET,
            interpreter=asked,
            provider=provider,
            model=model,
            status=status,
            degraded=result.degraded,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
            cache_read_tokens=result.usage.cache_read_tokens,
            latency_ms=latency_ms,
            release_id=meta.release_id,
            engine_version=meta.engine_version,
        )
    )
    logs.event(
        "interpret",
        request_id=request_id,
        endpoint=Endpoint.INTERPRET.value,
        interpreter=asked.value,
        provider=provider,
        model=model,
        interpret_status=result.status.value,
        call_status=status.value,
        degraded=result.degraded,
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        cache_read_tokens=result.usage.cache_read_tokens,
        latency_ms=latency_ms,
        edits=_edits(result.operations),
        rejections=dict(Counter(rejected.reason.value for rejected in reduced.rejected)),
        unmet=tuple(category.value for category in result.unmet),
        assumptions=tuple(assumption.code.value for assumption in result.assumptions),
    )


@router.post("/interpret", response_model=Envelope[InterpretData], responses=WITH_BODY)
def interpret(body: InterpretBody, context: Ctx, request_id: RequestId) -> Envelope[InterpretData]:
    """Read a request in words into typed edits, and apply them to the spec."""
    deps, release = context.deps, context.release
    spec = body.spec or default_for(release, Tenure.RENT)

    began = deps.clock.elapsed()
    asked = InterpretRequest(text=body.text, spec=spec, release=release)
    result, status = answer(deps, asked, request_id, body.ask_model)
    # Every edit here is the rules' own. Nothing a model read is among them.
    reduced = apply(spec, result.operations, release)
    latency_ms = round((deps.clock.elapsed() - began) * 1000)
    # The call was made, so it is on record whether or not its spec can be ranked.
    _record(context, request_id, result, reduced, status, latency_ms)
    # The spec is checked as the edits leave it, so that a spec which names
    # what a newer release has dropped can be put right in words.
    check(reduced.spec, release)
    # "The rest of your search has been applied" is untrue where nothing was.
    changed = any(edit.changed for edit in reduced.applied)
    typed = Typed(body.text, Grammar(context.names, release), release)
    by_rules = isinstance(deps.interpreter, RuleInterpreter)

    return envelope(
        context,
        InterpretData(
            status=result.status,
            operations=result.operations,
            spec=reduced.spec,
            spec_hash=spec_hash(reduced.spec),
            applied=reduced.applied,
            rejected=reduced.rejected,
            assumptions=result.assumptions,
            unmet=result.unmet,
            clarify=result.clarify,
            notice=result.notice,
            notice_text=notice_text(result.notice, changed),
            interpreter=result.interpreter,
            degraded=result.degraded,
            model_refused=status is CallStatus.REFUSED,
            rests_on=as_sent(result, body.text, body.lead),
            # Served to the caller, who holds the text. They are in no line and
            # no record, and no other route takes or returns them.
            suggestions=offered(result, body.text, body.lead, spec, typed),
            unread=stretches(result.unread, body.text, body.lead),
            not_in_release=missing(result, reduced, body.text, body.lead),
            unmet_at=unmet_at(result, body.text, body.lead),
            model_pending=not by_rules and not body.ask_model and asks_a_model(result),
            places=places_of(reduced.spec, release),
        ),
    )
