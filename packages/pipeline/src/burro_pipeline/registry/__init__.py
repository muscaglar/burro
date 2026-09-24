"""The licence registry: what data Burro may use, and for what.

Every ingest step calls `Registry.require` before it downloads anything.
"""

from burro_pipeline.registry.load import DEFAULT_PATH, Registry, RegistryError, find, load
from burro_pipeline.registry.model import (
    CommercialUse,
    Dimension,
    Licence,
    Source,
    Status,
    Use,
    VerifiedHow,
)
from burro_pipeline.registry.rules import Problem, Severity, check

__all__ = [
    "DEFAULT_PATH",
    "CommercialUse",
    "Dimension",
    "Licence",
    "Problem",
    "Registry",
    "RegistryError",
    "Severity",
    "Source",
    "Status",
    "Use",
    "VerifiedHow",
    "check",
    "find",
    "load",
]
