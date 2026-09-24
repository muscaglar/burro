"""The fence: what is kept for the audit or for the census table is no part of the product.

A table about residents is read by the audit, or shown as the statistics
office's own table on an area's page, and used for nothing else (ADR 0006 and
0014). The licence gate allows such a file, for that one use. Fetch keeps none
today, because no store is built for one, and it will once there is. So the
gate alone does not keep such a file out of a build: a rule must.

A file is kept apart when any of these holds. One is enough.

- Its receipt says it was fetched for the audit or for the census table.
- The registry holds its source under the heading `audit` or `residents`.
- The registry holds its source for the audit or for the census table, under any heading.

A file kept apart is never sealed into the lock of a product release, and no
row of evidence may rest on it. Nor may one rest on a file whose source the
registry does not hold: nothing shows that such a file is not kept apart.
"""

from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.registry import Registry, RegistryError
from burro_pipeline.registry.model import Dimension, Source, Use

# The uses that are no part of the product: one feeds the audit, the other a table that is
# shown as its publisher wrote it and is never scored.
USES_KEPT_APART = frozenset({Use.AUDIT_ONLY, Use.CENSUS_TABLE})
HEADINGS_KEPT_APART = frozenset({Dimension.AUDIT, Dimension.RESIDENTS})


def source_is_kept_apart(source: Source) -> bool:
    """Whether the registry holds a source for the audit or for the census table."""
    return source.dimension in HEADINGS_KEPT_APART or not USES_KEPT_APART.isdisjoint(source.uses)


def is_kept_apart(receipt: Receipt, registry: Registry | None) -> bool:
    """Whether a file is kept out of the product, by its receipt or by its registry entry.

    With no registry, only the receipt is read. A made-up file is under no
    registry entry, so only its receipt is read too.
    """
    if receipt.use in USES_KEPT_APART:
        return True
    if registry is None or receipt.made_up:
        return False
    return names_a_source_kept_apart(receipt.source_id, registry)


def names_a_source_kept_apart(source_id: str, registry: Registry) -> bool:
    """Whether the registry holds a source, and holds it for the audit or the census table."""
    return is_registered(source_id, registry) and source_is_kept_apart(registry.get(source_id))


def is_registered(source_id: str, registry: Registry) -> bool:
    """Whether the registry holds a source at all."""
    try:
        registry.get(source_id)
    except RegistryError:
        return False
    return True
