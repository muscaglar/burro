"""Burro's ranking engine. Pure Python: no files, no clock, no environment, no network.

The names below are the ones the pipeline and the API are expected to reach for.
Everything else is imported from its module.
"""

from burro_core.catalogue import CATALOGUE_VERSION, FEATURES, TAGS, percentile_of, tag_raw
from burro_core.explain import Explainer, Explanation, TemplateExplainer, explain
from burro_core.facts import Fact, facts_for
from burro_core.ids import FeatureId, TagId
from burro_core.interpret import (
    NOTICES,
    Interpreter,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    assumptions_for,
)
from burro_core.ops import NO_OPERATIONS, Operations
from burro_core.places import resolve_area, resolve_place, search_places
from burro_core.rank import ENGINE_VERSION, RankResult, rank
from burro_core.reducer import ReducerResult, apply
from burro_core.release import (
    InMemoryRelease,
    Release,
    ReleaseError,
    open_release,
    parse_release,
)
from burro_core.spec import (
    LIMITS,
    PreferenceSpec,
    SpecError,
    canonical,
    check_spec,
    default_spec,
    spec_hash,
)
from burro_core.verify import Sentence, Verdict, verify

__all__ = [
    "CATALOGUE_VERSION",
    "ENGINE_VERSION",
    "FEATURES",
    "LIMITS",
    "NOTICES",
    "NO_OPERATIONS",
    "TAGS",
    "Explainer",
    "Explanation",
    "Fact",
    "FeatureId",
    "InMemoryRelease",
    "InterpretRequest",
    "InterpretResult",
    "Interpreter",
    "Operations",
    "PreferenceSpec",
    "RankResult",
    "ReducerResult",
    "Release",
    "ReleaseError",
    "RuleInterpreter",
    "Sentence",
    "SpecError",
    "TagId",
    "TemplateExplainer",
    "Verdict",
    "apply",
    "assumptions_for",
    "canonical",
    "check_spec",
    "default_spec",
    "explain",
    "facts_for",
    "open_release",
    "parse_release",
    "percentile_of",
    "rank",
    "resolve_area",
    "resolve_place",
    "search_places",
    "spec_hash",
    "tag_raw",
    "verify",
]
