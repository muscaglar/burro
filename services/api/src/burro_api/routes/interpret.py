"""Route 1: from what a person typed to typed edits, applied by the one reducer.

The text is read and dropped. What is kept about the call is metadata: which
interpreter was asked, how it went, how long it took and how many edits came
of it. If a model is slow, capped or broken, the rules answer in its place and
the person still gets their form.
"""

from collections import Counter
from collections.abc import Callable
from concurrent.futures import Future
from threading import Thread

from burro_core.ids import Tenure
from burro_core.interpret import (
    NOTICES,
    InterpretRequest,
    InterpretResult,
    RestsOn,
    RuleInterpreter,
)
from burro_core.ops import Operations
from burro_core.reducer import ReducerResult, apply
from burro_core.spec import spec_hash
from fastapi import APIRouter

from burro_api import logs
from burro_api.calls import Caller, CallRecord, CallStatus, Endpoint
from burro_api.claude import ModelCapped, ModelTimeout
from burro_api.deps import Context, Ctx, Deps
from burro_api.routes.common import PREFIX, WITH_BODY, RequestId, check, default_for, envelope
from burro_api.wire import Envelope, InterpretBody, InterpretData

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


def answer(
    deps: Deps, request: InterpretRequest, request_id: str = ""
) -> tuple[InterpretResult, CallStatus]:
    """The interpreter's answer, or the rules' if it fails. It never raises for a model."""
    asked = deps.interpreter
    if isinstance(asked, RuleInterpreter):
        result = asked.interpret(request)
        return result, CallStatus(result.status.value)
    try:
        result = within(deps.model_timeout_s, lambda: asked.interpret(request))
        return result, CallStatus(result.status.value)
    except (ModelTimeout, TimeoutError):
        failed = CallStatus.TIMEOUT
    except ModelCapped:
        failed = CallStatus.CAPPED
    except Exception as error:
        failed = CallStatus.ERROR
        logs.log_failure(error, request_id=request_id)
    fallback = RuleInterpreter().interpret(request)
    return fallback.replace(degraded=True), failed


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
        and 0 <= rests.start < rests.end <= len(text)
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
    asked = Caller(deps.interpreter.name.value)
    model = deps.model_id if asked is Caller.CLAUDE else ""
    # Nothing of the spec is kept or logged, not even a hash of it (ADR 0011).
    deps.calls.add(
        CallRecord(
            call_id=deps.ids.call_id(),
            at=context.timestamp(),
            endpoint=Endpoint.INTERPRET,
            interpreter=asked,
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
    result, status = answer(deps, asked, request_id)
    reduced = apply(spec, result.operations, release)
    latency_ms = round((deps.clock.elapsed() - began) * 1000)
    # The call was made, so it is on record whether or not its spec can be ranked.
    _record(context, request_id, result, reduced, status, latency_ms)
    # The spec is checked as the edits leave it, so that a spec which names
    # what a newer release has dropped can be put right in words.
    check(reduced.spec, release)

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
            notice_text=NOTICES[result.notice],
            interpreter=result.interpreter,
            degraded=result.degraded,
            rests_on=as_sent(result, body.text, body.lead),
        ),
    )
