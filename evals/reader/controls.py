"""Two readers whose faults are known, to measure a real reader against.

`Nothing` reads nothing. It can never reverse a wish or make an edit nobody
asked for, and it is right wherever the right thing is to leave the search
alone. What a reader scores above it is what that reader reads.

`Keywords` raises whatever the words name, whatever is said of it, and adds a
journey to every place it finds. It reads every plain wish and reverses every
wish that is turned round. What a reader scores below it, in cases reversed,
is what that reader's care is worth.

    uv run python evals/reader/score.py --reader nothing
    uv run python evals/reader/score.py --reader keywords
"""

from burro_core.ids import (
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    Step,
    StrictnessChoice,
    TagId,
    TowardChoice,
    UnmetCategory,
    WeightAction,
)
from burro_core.interpret import NO_USAGE, InterpretRequest, InterpretResult, prepare
from burro_core.lexicon import lexicon_of
from burro_core.ops import NO_OPERATIONS, CommuteEdit, Operations, TagEdit, WeightEdit


def _answer(operations: Operations) -> InterpretResult:
    return InterpretResult(
        status=InterpretStatus.OK,
        operations=operations,
        assumptions=(),
        unmet=() if operations.count else (UnmetCategory.OTHER,),
        clarify=(),
        notice=Notice.NONE,
        interpreter=InterpreterName.RULE,
        degraded=False,
        usage=NO_USAGE,
    )


class Nothing:
    # The interface knows two names. The scorer reports this one as `nothing`.
    name = InterpreterName.RULE

    def interpret(self, request: InterpretRequest) -> InterpretResult:
        return _answer(NO_OPERATIONS)


class Keywords:
    name = InterpreterName.RULE

    def interpret(self, request: InterpretRequest) -> InterpretResult:
        words = f" {prepare(request.text)} "
        features: set[FeatureId] = set()
        tags: set[TagId] = set()
        for phrase, target in lexicon_of(request.release.manifest.gritty_variant).items():
            if f" {phrase} " in words:
                features.update(target.features)
                tags.update(target.tags)
        places = [
            place.place_id
            for place in request.release.places
            if any(f" {prepare(name)} " in words for name in (place.name, *place.aliases))
        ]
        return _answer(
            NO_OPERATIONS.replace(
                commute_ops=tuple(
                    CommuteEdit(
                        action=CommuteAction.ADD,
                        place_id=place_id,
                        mode=ModeChoice.UNCHANGED,
                        max_minutes=0,
                        strictness=StrictnessChoice.UNCHANGED,
                        step=Step.NONE,
                        provenance=EditProvenance.STATED,
                    )
                    for place_id in places[:3]
                ),
                weight_ops=tuple(
                    WeightEdit(
                        action=WeightAction.NUDGE,
                        feature_id=feature_id,
                        value=0.0,
                        step=Step.UP_LARGE,
                        direction=DirectionChoice.DEFAULT,
                        provenance=EditProvenance.STATED,
                    )
                    for feature_id in sorted(features)
                ),
                tag_ops=tuple(
                    TagEdit(
                        action=WeightAction.NUDGE,
                        tag_id=tag_id,
                        value=0.0,
                        step=Step.UP_LARGE,
                        # Whichever end was named, it is raised towards the high one.
                        toward=TowardChoice.HIGH,
                        provenance=EditProvenance.STATED,
                    )
                    for tag_id in sorted(tags)
                ),
            )
        )
