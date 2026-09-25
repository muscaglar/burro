"""Burro's ranking engine. Pure Python: no files, no clock, no environment, no network.

The names below are the ones the pipeline and the API are expected to reach for.
Everything else is imported from its module.
"""

from burro_core.catalogue import (
    CATALOGUE_VERSION,
    FEATURES,
    TAGS,
    band_of,
    percentile_of,
    tag_raw,
    tags_of,
)
from burro_core.explain import Explainer, Explanation, TemplateExplainer, explain
from burro_core.facts import Fact, facts_for
from burro_core.ids import FeatureId, TagId
from burro_core.interpret import (
    NOTICES,
    Interpreter,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    Suggestion,
    assumptions_for,
    notice_text,
)
from burro_core.likeness import Likeness, similar
from burro_core.ops import NO_OPERATIONS, Operations
from burro_core.places import resolve_area, resolve_place, search_areas, search_places
from burro_core.portrait import Portrait, portrait
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
    "Likeness",
    "Operations",
    "Portrait",
    "PreferenceSpec",
    "RankResult",
    "ReducerResult",
    "Release",
    "ReleaseError",
    "RuleInterpreter",
    "Sentence",
    "SpecError",
    "Suggestion",
    "TagId",
    "TemplateExplainer",
    "Verdict",
    "apply",
    "assumptions_for",
    "band_of",
    "canonical",
    "check_spec",
    "default_spec",
    "explain",
    "facts_for",
    "notice_text",
    "open_release",
    "parse_release",
    "percentile_of",
    "portrait",
    "rank",
    "resolve_area",
    "resolve_place",
    "search_areas",
    "search_places",
    "similar",
    "spec_hash",
    "tag_raw",
    "tags_of",
    "verify",
]
