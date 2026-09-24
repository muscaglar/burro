"""The rule that no fact is served without evidence.

`unevidenced` takes a release and its evidence, and names every fact that has
no record behind it. It asks core for the facts, so it sees what the API would
serve and nothing else. A release is fit to serve only when it returns nothing.

Evidence that is kept for the audit or for the census table is no evidence of
the product. A row that rests on such a file is named, and so is every fact
served from it. A release that is not made up is held to the lock of its build
and to the licence registry, and is not checked without them.

The gate is asked again here, of every file a row rests on, for the use the
figure is put to (ADR 0016). A receipt says what the gate was asked when a file
was fetched, and the gate lets a file be read for less than a release does with
it: to validate against, or for a prototype. So a row is named when a file it
rests on was fetched for an internal use, or comes from a source the registry
does not allow for the use of the file of the release that serves the fact:

| Row of | The use that is asked for |
|---|---|
| a name or a boundary | `gazetteer` |
| a feature, a tag or a cost | `scoring` |
| the journeys of a mode | `routing` |
| a station | `display` |

Three kinds of fact depend on what a person asks, so their ids are not known
when a release is built. Each rests on a row that is:

| Fact | Rests on the row of |
|---|---|
| `<area>/travel/<place>.<mode>` | `<area>/travel/<mode>`: the area's journeys by that mode |
| `<area>/budget_fit/<tenure>.<segment>` | `<area>/cost/<tenure>.<segment>` |
| `<area>/missing/<component>` | `<area>/area/name`, the one thing the sentence prints |
"""

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import NamedTuple

import burro_core
from burro_core.facts import fact_id, facts_for
from burro_core.ids import FactKind, Mode, PtBasis
from burro_core.release import InMemoryRelease

from burro_pipeline.evidence.fence import (
    is_kept_apart,
    is_registered,
    names_a_source_kept_apart,
)
from burro_pipeline.evidence.lock import Lock, LockError
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.record import MADE_UP_SOURCE
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import Registry, RegistryError, Use
from burro_pipeline.registry.model import INTERNAL_USES

# The keys of the rows that are not the id of a feature, a tag, a cost or a station.
NAME, BOUNDARY, NEAREST = "name", "boundary", "nearest"

# The use a source must be registered for to stand behind a row, by the kind of the row. It
# is the use of the file of the release that serves the fact: `USE_OF` in `release/write.py`.
USE_OF_A_ROW: Mapping[str, Use] = {
    FactKind.AREA: Use.GAZETTEER,
    FactKind.FEATURE: Use.SCORING,
    FactKind.TAG: Use.SCORING,
    FactKind.COST: Use.SCORING,
    FactKind.TRAVEL: Use.ROUTING,
    FactKind.STATION: Use.DISPLAY,
}

# What each finding means, in words that finish a sentence beginning with the fact.
MEANING: Mapping[str, str] = {
    "evidence_is_of_this_release": "is not the release this evidence was written for",
    "fact_has_a_row": "is served, and no row of evidence stands behind it",
    "row_has_a_value": "is served, and its row says there is no figure",
    "source_has_a_file": "cites a source, and its row rests on no file from that source",
    "input_is_locked": "rests on a file that is not in the lock",
    "input_is_for_the_product": "rests on a file kept for the audit or for the census table",
    "evidence_is_for_the_product": "is served, and the evidence behind it rests on a file kept "
    "for the audit or for the census table",
    "lock_is_for_the_product": "is in the lock, and is kept for the audit or for the census table",
    "source_is_registered": "rests on a file whose source is not in the licence registry, or "
    "is such a file in the lock",
    "input_is_allowed": "rests on a file that the licence registry does not allow for what "
    "this figure is used for, or that was fetched for an internal use",
    "row_has_a_fact": "has a row that says there is a figure, and the release holds none",
    "method_is_found": "names a module that is not in the pipeline or in core, so nobody can "
    "read how its figures were worked out",
}
# Where the arithmetic of a method may be: in the pipeline, or in core, which holds the
# percentiles and the vibes. The lock names the commit both are read at.
HOLDS_THE_ARITHMETIC: Mapping[str, Path] = {
    "burro_pipeline": Path(__file__).parents[1],
    "burro_core": Path(burro_core.__file__ or "").parent,
}


class Finding(NamedTuple):
    """One fact that may not be served, and the rule it breaks."""

    fact_id: str
    rule: str

    def __str__(self) -> str:
        return f"{self.fact_id} {MEANING[self.rule]} [{self.rule}]"


def evidence_key(served: str) -> str:
    """The id of the row that stands behind a fact."""
    area_id, kind, key = served.split("/", 2)
    if kind == FactKind.TRAVEL:
        return fact_id(area_id, FactKind.TRAVEL, key.rsplit(".", 1)[-1])
    if kind == FactKind.BUDGET_FIT:
        return fact_id(area_id, FactKind.COST, key)
    if kind == FactKind.MISSING:
        return fact_id(area_id, FactKind.AREA, NAME)
    return served


def module_is_found(code: str) -> bool:
    """Whether the module a method names is there, as a file of the pipeline or of core.

    It is looked for on disk. Nothing is imported, so nothing a file of
    evidence names is ever run.
    """
    package, *within = code.split(".")
    home = HOLDS_THE_ARITHMETIC.get(package)
    if home is None:
        return False
    found = home.joinpath(*within)
    as_a_file = bool(within) and found.with_name(f"{found.name}.py").is_file()
    return as_a_file or (found / "__init__.py").is_file()


def journeys(release: InMemoryRelease) -> dict[tuple[str, Mode], tuple[int, int]]:
    """For each area and mode: how many destinations have a journey, and of how many.

    A journey that is known to be beyond the cutoff is known. By public
    transport a journey is known when both of its times are.
    """
    table = release.travel_table
    total = len(table.destination_ids)
    found = {(area.area_id, mode): (0, total) for area in release.neighbourhoods for mode in Mode}
    for mode in Mode:
        bases = tuple(PtBasis) if mode is Mode.PT else (PtBasis.TYPICAL,)
        matrices = [table.matrix(mode, basis) for basis in bases]
        for index, area_id in enumerate(table.area_ids):
            # A hand-built release may hold a matrix smaller than its ids say.
            if all(index < len(matrix) for matrix in matrices):
                times = zip(*(matrix[index] for matrix in matrices), strict=False)
                known = sum(all(cell is not None for cell in cells) for cells in times)
                found[area_id, mode] = (known, total)
    return found


def served(release: InMemoryRelease) -> Iterator[tuple[str, frozenset[str]]]:
    """The row each fact of a release rests on, with the sources the fact cites."""
    routed = frozenset(release.travel_table.source_ids)
    known = journeys(release)
    for area in release.neighbourhoods:
        for fact in facts_for(release, area.area_id, None):
            yield fact.fact_id, frozenset(source.source_id for source in fact.sources)
        for mode in Mode:
            if known[area.area_id, mode][0]:
                yield fact_id(area.area_id, FactKind.TRAVEL, mode), routed


def is_allowed(receipt: Receipt, use: Use, registry: Registry | None) -> bool:
    """Whether a file may stand behind a figure that is put to a use.

    A file that was fetched for an internal use may stand behind none. Of any
    other, the gate is asked, for the use the figure is put to. With no registry
    there is nothing to ask, and only a made-up file is allowed: it is under no
    entry. What the registry says in refusing is not kept: a finding names a rule.
    """
    if receipt.use in INTERNAL_USES:
        return False
    if receipt.made_up:
        return True
    if registry is None:
        return False
    try:
        registry.require(receipt.source_id, use)
    except RegistryError:
        return False
    return True


def unevidenced(
    release: InMemoryRelease,
    evidence: Evidence,
    lock: Lock | None = None,
    registry: Registry | None = None,
) -> tuple[Finding, ...]:
    """Every fact of a release with no record behind it, in the order of their ids.

    A row that rests on a file the lock does not name is found too, and so is
    one that rests on a file kept for the audit or for the census table, or on
    a file the registry does not allow for the use its figure is put to. A
    release that is not made up is refused without its lock and the registry.
    A made-up one is built from no file, so its lock may be left out.
    """
    release_id = release.manifest.release_id
    if not release.manifest.synthetic:
        # A check that was handed less would pass what it could not see.
        if lock is None:
            raise LockError("real_release_needs_a_lock", release_id)
        if registry is None:
            raise LockError("real_release_needs_a_registry", release_id)
    if evidence.release_id != release_id or (lock is not None and lock.release_id != release_id):
        return (Finding(release_id, "evidence_is_of_this_release"),)
    kept_apart = {
        receipt.file_id for receipt in evidence.receipts if is_kept_apart(receipt, registry)
    }
    unknown = {
        receipt.file_id
        for receipt in evidence.receipts
        if registry is not None
        and not receipt.made_up
        and not is_registered(receipt.source_id, registry)
    }

    # A file that is kept apart, or whose source the registry does not hold, is named by a
    # rule of its own, for every row that rests on it. Every other file is asked about here.
    asked = [r for r in evidence.receipts if r.file_id not in kept_apart | unknown]
    refused = {
        use: frozenset(r.file_id for r in asked if not is_allowed(r, use, registry))
        for use in frozenset(USE_OF_A_ROW.values())
    }

    def fenced(row: EvidenceRow) -> bool:
        return not kept_apart.isdisjoint(row.inputs)

    def allowed(row: EvidenceRow) -> bool:
        use = USE_OF_A_ROW.get(row.fact_id.split("/")[1])
        # A kind of row that has no use to be asked for is allowed nothing.
        return not row.inputs or (use is not None and refused[use].isdisjoint(row.inputs))

    found = [
        Finding(method.derivation_id, "method_is_found")
        for method in evidence.methods
        if not module_is_found(method.code)
    ]
    needed: set[str] = set()
    for key, cited in served(release):
        needed.add(key)
        row = evidence.row(key)
        if row is None:
            found.append(Finding(key, "fact_has_a_row"))
            continue
        if fenced(row):
            found.append(Finding(key, "evidence_is_for_the_product"))
        if not row.has_a_value:
            found.append(Finding(key, "row_has_a_value"))
        elif not cited <= evidence.sources_of(row):
            found.append(Finding(key, "source_has_a_file"))
    for row in evidence.rows:
        outline = row.measure == f"{FactKind.AREA}/{BOUNDARY}"
        drawn = outline and release.geometry(row.area_id) is not None
        if row.has_a_value and row.fact_id not in needed and not drawn:
            found.append(Finding(row.fact_id, "row_has_a_fact"))
        if lock is not None and not all(lock.holds(file_id) for file_id in row.inputs):
            found.append(Finding(row.fact_id, "input_is_locked"))
        if fenced(row):
            found.append(Finding(row.fact_id, "input_is_for_the_product"))
        if not unknown.isdisjoint(row.inputs):
            found.append(Finding(row.fact_id, "source_is_registered"))
        if not allowed(row):
            found.append(Finding(row.fact_id, "input_is_allowed"))
    if lock is not None and registry is not None:
        for held in lock.inputs:
            if held.source_id is None or held.source_id == MADE_UP_SOURCE:
                continue
            if not is_registered(held.source_id, registry):
                found.append(Finding(held.name, "source_is_registered"))
            elif names_a_source_kept_apart(held.source_id, registry):
                found.append(Finding(held.name, "lock_is_for_the_product"))
    return tuple(sorted(set(found)))


def counted(findings: tuple[Finding, ...]) -> dict[str, int]:
    """How many findings each rule made. This is what a build may print."""
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.rule] = counts.get(finding.rule, 0) + 1
    return dict(sorted(counts.items()))
