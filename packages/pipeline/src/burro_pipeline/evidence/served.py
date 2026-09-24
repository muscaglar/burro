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

The registry is asked as it stands on the day of the check, and not as it
stood on the day of the build: a source can lose its approval, or a use, after
a release was built from it. A source is asked about once for a use. Where a
row that is put to the use rests on a file of the source, the row is what is
asked about and what is named. Where no row does, as none does for the source
of a place to reach, the source is asked about for the file of the release
that cites it, and that file is named. Both are named under one rule,
`input_is_allowed`, so one fault is found once.

Where an area stands among the areas is core's to work out, and so is a tag:
`percentile_of` and `tag_raw`. An area is ranked on its percentile, so a rank
can be moved with every figure left as it was. The check works each
percentile and each tag out again from the figures of the release, with core's
own code, and finds any that differ. It holds no second copy of the
arithmetic. The share of an area that stands behind a figure is held to the
row of the figure.

Three kinds of fact depend on what a person asks, so their ids are not known
when a release is built. Each rests on a row that is:

| Fact | Rests on the row of |
|---|---|
| `<area>/travel/<place>.<mode>` | `<area>/travel/<mode>`: the area's journeys by that mode |
| `<area>/budget_fit/<tenure>.<segment>` | `<area>/cost/<tenure>.<segment>` |
| `<area>/missing/<component>` | `<area>/area/name`, the one thing the sentence prints |

Two kinds of fact are counted from the figures of measures, and hold no figure
of their own. Each rests on the rows of those figures, and `rows_behind` says
which:

| Fact | Rests on the rows of |
|---|---|
| `<area>/tag/<vibe>`, of an area that cannot be placed | Its name, and each part with a figure |
| `<area>/likeness/<other>` | Each measure the two areas were compared on, in both areas |

A vibe that is placed has a row of its own, which holds its score.
"""

from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import NamedTuple

import burro_core
from burro_core.catalogue import TAGS, percentile_of, tag_raw
from burro_core.facts import fact_id, facts_for
from burro_core.ids import FactKind, FeatureId, Mode, PtBasis, Segment, TagId, Tenure
from burro_core.likeness import parts_of
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
from burro_pipeline.release.write import USE_OF
from burro_pipeline.release.write import cited as cited_by

# The keys of the rows that are not the id of a feature, a tag, a cost or a station.
NAME, BOUNDARY, NEAREST = "name", "boundary", "nearest"
# A release writes a figure to this many decimal places, and a figure is held to its row so.
FIGURE_DECIMALS = 6

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
    "row_holds_the_figure": "is served with a figure that is not the one its row of evidence "
    "holds, so one of the two was changed after the build",
    "row_holds_the_coverage": "is held by the release to rest on a share of the area, or of "
    "the recipe, that is not the one its row of evidence holds",
    "percentile_is_cores": "is served with a place among the areas that is not the one core "
    "works out from the figures of the release",
    "tag_is_cores": "is held by the release with a raw value, a score or a share of its recipe "
    "that is not the one core works out from the measures of the release",
    "source_has_a_file": "cites a source, and its row rests on no file from that source",
    "input_is_locked": "rests on a file that is not in the lock",
    "input_is_for_the_product": "rests on a file kept for the audit or for the census table",
    "evidence_is_for_the_product": "is served, and the evidence behind it rests on a file kept "
    "for the audit or for the census table",
    "lock_is_for_the_product": "is in the lock, and is kept for the audit or for the census table",
    "source_is_registered": "rests on a file whose source is not in the licence registry, or "
    "is such a file in the lock",
    "input_is_allowed": "rests on a file that the licence registry does not allow for what "
    "this figure is used for, or that was fetched for an internal use, or is a file of the "
    "release that cites a source the registry does not allow for it",
    "row_has_a_fact": "has a row that says there is a figure, and the release holds none",
    "row_names_its_method": "has a row that names another method than the one the code "
    "works the measure or the tag out by",
    "row_rests_on_its_file": "has a row that does not rest on the one file the code reads "
    "the measure from, or on files of its squares alone where its publisher cuts it to "
    "squares, or on the file of every part where its publisher gives a file for each part, or "
    "is a tag whose row does not rest on the files of the measures of its recipe",
    "method_is_found": "names a module that is not in the pipeline or in core, so nobody can "
    "read how its figures were worked out",
    "receipt_is_the_locked_file": "is a file whose receipt in the evidence gives another hash "
    "or size than the lock gives it",
    "receipt_is_as_committed": "is a file whose receipt in the evidence is not the receipt "
    "that was committed for it, or that has no receipt committed",
    "credit_is_the_registrys": "is a source that the release names, credits or licenses "
    "otherwise than the licence registry does",
}
# Where the arithmetic of a method may be: in the pipeline, or in core, which holds the
# percentiles and the vibes. The lock names the commit both are read at.
HOLDS_THE_ARITHMETIC: Mapping[str, Path] = {
    "burro_pipeline": Path(__file__).parents[1],
    "burro_core": Path(burro_core.__file__ or "").parent,
}


class Behind(NamedTuple):
    """What the code says stands behind a measure: its method, and the file it reads."""

    derivation_id: str
    source_id: str
    # Whether a publisher's name for a file is the name of the file the measure reads.
    reads: Callable[[str], bool]
    # Whether the publisher cuts the product to squares of the National Grid, a file for
    # each. A figure at the edge of a square then rests on the files of more than one. Any
    # other measure is held to one file of its source, as it was before there was a product
    # in squares.
    in_squares: bool = False
    # Whether the publisher gives the product as a file for each part of the whole, as a
    # register with a file for each authority, and the measure reads them all. A figure then
    # rests on the file of every part: it is the whole that makes a count of nought a count.
    in_parts: bool = False


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


def _has_a_figure(release: InMemoryRelease, area_id: str, feature_id: FeatureId) -> bool:
    held = release.feature(area_id, feature_id)
    return held is not None and held.value is not None


def rows_behind(release: InMemoryRelease, served: str) -> tuple[str, ...]:
    """The ids of the rows a fact rests on. Each must hold a figure, or the name of an area.

    Most facts rest on one row. A vibe that cannot be placed says the name of
    the area and how many parts of the recipe have a figure, so it rests on
    the row of the name and on the row of each such part. A likeness is
    counted from the measures both areas have a figure for, so it rests on
    the row of each, in both areas.
    """
    area_id, kind, key = served.split("/", 2)
    carried = {metric.feature_id for metric in release.metrics}
    if kind == FactKind.LIKENESS:
        both = (area_id, key)
        return tuple(
            fact_id(area, FactKind.FEATURE, part.feature_id)
            for part in parts_of(release)
            if all(_has_a_figure(release, area, part.feature_id) for area in both)
            for area in both
        )
    if kind == FactKind.TAG and key in TagId and figure_of(release, served) is None:
        return (
            fact_id(area_id, FactKind.AREA, NAME),
            *(
                fact_id(area_id, FactKind.FEATURE, term.feature_id)
                for term in TAGS[TagId(key)].terms
                if term.feature_id in carried and _has_a_figure(release, area_id, term.feature_id)
            ),
        )
    return (evidence_key(served),)


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


def _cost_of(release: InMemoryRelease, area_id: str, key: str) -> float | None:
    """The median of a cost that is one number. None of a range, which is three."""
    tenure, _, segment = key.partition(".")
    if tenure not in Tenure or segment not in Segment:
        return None
    held = release.cost(area_id, Tenure(tenure), Segment(segment))
    return None if held is None or held.ranged else float(held.median)


def figure_of(release: InMemoryRelease, served: str) -> float | None:
    """The figure a release gives for a fact that is one number, or `None` for any other fact."""
    area_id, kind, key = served.split("/", 2)
    if kind == FactKind.FEATURE:
        held = release.feature(area_id, FeatureId(key))
        return None if held is None else held.value
    if kind == FactKind.TAG:
        scored = release.tag(area_id, TagId(key))
        return None if scored is None else scored.score
    if kind == FactKind.COST:
        return _cost_of(release, area_id, key)
    return None


def _same_figure(one: float | None, other: float | None) -> bool:
    """Whether two figures are one, as a release writes them: to six decimal places."""
    if one is None or other is None:
        return one is other
    return round(one, FIGURE_DECIMALS) == round(other, FIGURE_DECIMALS)


def coverage_of(release: InMemoryRelease, row: EvidenceRow) -> float | None:
    """The share a release says stands behind a measure or a tag in one area.

    It is none for any other row, and for a measure or a tag the release holds
    no row of.
    """
    kind, _, key = row.measure.partition("/")
    if kind == FactKind.FEATURE and key in FeatureId:
        held = release.feature(row.area_id, FeatureId(key))
        return None if held is None else held.coverage
    if kind == FactKind.TAG and key in TagId:
        scored = release.tag(row.area_id, TagId(key))
        return None if scored is None else scored.coverage
    return None


def not_as_core_works_it_out(release: InMemoryRelease) -> Iterator[Finding]:
    """Every percentile and every tag of a release that is not what core gives for it.

    Each is worked out again from what the release itself holds: a percentile
    from the figures of its measure, and a tag from those percentiles. A tag is
    worked out from the percentiles core gives, and not from those the release
    holds, so that one percentile that was moved is found once.
    """
    areas = [area.area_id for area in release.neighbourhoods]
    rankable = [area.rankable for area in release.neighbourhoods]
    placed: dict[str, dict[FeatureId, float | None]] = {area: {} for area in areas}
    for metric in release.metrics:
        feature = metric.feature_id
        held = [release.feature(area, feature) for area in areas]
        worked = percentile_of([None if one is None else one.value for one in held], rankable)
        for area, one, percentile in zip(areas, held, worked, strict=True):
            placed[area][feature] = percentile
            if not _same_figure(None if one is None else one.percentile, percentile):
                yield Finding(fact_id(area, FactKind.FEATURE, feature), "percentile_is_cores")
    # The vibes the release carries. That they are the ones its manifest says is core's rule.
    for tag_id in sorted(vibe.tag_id for vibe in release.vibes):
        raws = [tag_raw(tag_id, placed[area]) for area in areas]
        scores = percentile_of([one.raw for one in raws], rankable)
        for area, raw, score in zip(areas, raws, scores, strict=True):
            scored = release.tag(area, tag_id)
            if scored is None:
                same = raw.raw is None and raw.coverage == 0
            else:
                same = (
                    _same_figure(scored.raw, raw.raw)
                    and _same_figure(scored.score, score)
                    and _same_figure(scored.coverage, raw.coverage)
                )
            if not same:
                yield Finding(fact_id(area, FactKind.TAG, tag_id), "tag_is_cores")


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


def _of_what_is_cited(
    release: InMemoryRelease, evidence: Evidence, registry: Registry
) -> Iterator[Finding]:
    """The files of a release that cite a source the gate refuses for the use of the file.

    The step that writes a release asks the same. It is asked again here, as the
    registry stands on the day of the check.

    A source is asked about once for a use. Every row that rests on a file is
    asked about by `unevidenced`, for the use the row is put to, and is named
    there if the file may not stand behind it. So a source that such a row
    rests on a file of is not asked about again here, and one fault is not
    found twice. What is left is a source that no row put to the use rests on:
    the source of a place to reach, or a source a release cites and took no
    file from.
    """
    through_a_row = {
        (receipt.source_id, use)
        for row in evidence.rows
        if (use := USE_OF_A_ROW.get(row.fact_id.split("/")[1])) is not None
        for receipt in map(evidence.receipt, row.inputs)
        if receipt is not None
    }
    for file, source_id in sorted(set(cited_by(release))):
        if (source_id, USE_OF[file]) in through_a_row:
            continue
        try:
            registry.require(source_id, USE_OF[file])
        except RegistryError:
            yield Finding(file, "input_is_allowed")


def _of_the_credits(release: InMemoryRelease, registry: Registry) -> Iterator[Finding]:
    """Every source a release names, credits or licenses otherwise than the registry does."""
    for credited in release.manifest.sources:
        if not is_registered(credited.source_id, registry):
            continue
        entry = registry.get(credited.source_id)
        said = (credited.name, credited.publisher, credited.licence, credited.attribution)
        held = (entry.name, entry.publisher, entry.licence.value, entry.attribution)
        if (*said, credited.url) != (*held, entry.url):
            yield Finding(credited.source_id, "credit_is_the_registrys")


def _of_the_receipts(
    evidence: Evidence, lock: Lock | None, committed: Mapping[str, Receipt] | None
) -> Iterator[Finding]:
    """Every receipt of the evidence that is not the file the lock names, or not as committed.

    The id of a file is the first twelve digits of its hash, so two files may
    share one. The lock and a receipt are held to each other by the whole hash
    and the size. Where the receipts that were committed are given,
    a receipt of the evidence is held to the one committed for its file, in
    every field: fetch writes a receipt once, and nothing may change one.
    """
    named = {held.name: held for held in lock.inputs} if lock is not None else {}
    for receipt in evidence.receipts:
        held = named.get(receipt.file_id)
        if held is not None and (held.sha256, held.bytes) != (receipt.sha256, receipt.bytes):
            yield Finding(receipt.file_id, "receipt_is_the_locked_file")
    if committed is None:
        return
    for receipt in evidence.receipts:
        if not receipt.made_up and committed.get(receipt.file_id) != receipt:
            yield Finding(receipt.file_id, "receipt_is_as_committed")


def _of_the_tags(
    evidence: Evidence, tagged: str, measures: Mapping[str, Behind]
) -> Iterator[Finding]:
    """The rules the row of a tag breaks, held to the method of a tag and to its recipe.

    The row of a tag that has a score names the method of a tag. It rests on
    every file that the rows of the measures of its recipe rest on in its own
    area, where the measure has a figure there. It rests on no file but those
    that a row of such a measure rests on in some area, and those that such a
    measure reads: a score is where an area stands among all areas, so it may
    name every square of a product that is cut to squares.
    """
    of_measure: dict[str, set[str]] = {}
    for row in evidence.rows:
        kind, _, key = row.measure.partition("/")
        if kind == FactKind.FEATURE and row.has_a_value:
            of_measure.setdefault(key, set()).update(row.inputs)
    for feature, behind in measures.items():
        of_measure.setdefault(feature, set()).update(
            receipt.file_id
            for receipt in evidence.receipts
            if receipt.source_id == behind.source_id and behind.reads(receipt.publisher_file)
        )
    for row in evidence.rows:
        kind, _, key = row.measure.partition("/")
        if kind != FactKind.TAG or not row.has_a_value or key not in TagId:
            continue
        if row.derivation_id != tagged:
            yield Finding(row.fact_id, "row_names_its_method")
        here: set[str] = set()
        anywhere: set[str] = set()
        for term in TAGS[TagId(key)].terms:
            figure = evidence.row(fact_id(row.area_id, FactKind.FEATURE, term.feature_id))
            if figure is not None and figure.has_a_value:
                here |= set(figure.inputs)
                anywhere |= of_measure.get(term.feature_id, set())
        if not (here and here <= set(row.inputs) <= anywhere):
            yield Finding(row.fact_id, "row_rests_on_its_file")


def _of_the_measure(
    evidence: Evidence, row: EvidenceRow, behind: Behind, lock: Lock | None
) -> Iterator[str]:
    """The rules a row of a measure breaks, held to what the code says stands behind it.

    A measure whose publisher gives a file for each part of the whole rests on
    the file of every part. The parts are those the lock names of the source,
    and with no lock those the evidence holds of it: a row that names some of
    them and not all is found.
    """
    if row.derivation_id != behind.derivation_id:
        yield "row_names_its_method"
    named = [
        receipt.publisher_file
        for receipt in (evidence.receipt(file_id) for file_id in row.inputs)
        if receipt is not None and receipt.source_id == behind.source_id
    ]
    # One file, or the file of each of several squares, or the file of every part: never
    # none, never a file twice, and never a file of the source that the measure does not read.
    if behind.in_parts:
        enough = len(named) >= 1 and _every_part(evidence, behind, lock) <= set(row.inputs)
    else:
        enough = len(named) >= 1 if behind.in_squares else len(named) == 1
    if not (enough and len(set(named)) == len(named) and all(map(behind.reads, named))):
        yield "row_rests_on_its_file"


def _every_part(evidence: Evidence, behind: Behind, lock: Lock | None) -> set[str]:
    """The file of every part of a source that is given in parts, by the id of the file.

    The lock names every file of the build, read or not, so what it holds of
    the source is the whole. A made-up release may have no lock, and is held
    to what its evidence holds of the source.
    """
    of_the_evidence = {
        receipt.file_id
        for receipt in evidence.receipts
        if receipt.source_id == behind.source_id and behind.reads(receipt.publisher_file)
    }
    if lock is None:
        return of_the_evidence
    return of_the_evidence | {
        held.name for held in lock.inputs if held.source_id == behind.source_id
    }


def unevidenced(
    release: InMemoryRelease,
    evidence: Evidence,
    lock: Lock | None = None,
    registry: Registry | None = None,
    measures: Mapping[str, Behind] | None = None,
    tagged: str | None = None,
    committed: Mapping[str, Receipt] | None = None,
) -> tuple[Finding, ...]:
    """Every fact of a release with no record behind it, in the order of their ids.

    A row that rests on a file the lock does not name is found too, and so is
    one that rests on a file kept for the audit or for the census table, or on
    a file the registry does not allow for the use its figure is put to. A
    release that is not made up is refused without its lock and the registry.
    A made-up one is built from no file, so its lock may be left out.

    The registry is asked as it stands when the check is run, so a source that
    has been gated since the build, or has lost the use, is found. A source
    that the release cites, and that no row put to the same use rests on a
    file of, is asked about for the file of the release that cites it.

    `measures` is what the code says stands behind each measure it works out,
    by the id of the measure. Where it is given, the row of a figure is held
    to it: a row that names another method, or rests on another file of the
    same source, is found. Two measures may cite one source, and only this
    tells the evidence of one from the evidence of the other. A measure whose
    publisher cuts its product to squares may rest on the file of more than
    one square, and on no other file of the source. A measure whose publisher
    gives a file for each part of the whole rests on the file of every part.

    `tagged` is the id of the method a tag is worked out by, as the code names
    it. Where it is given, the row of a tag is held to it and to the files of
    the measures of its recipe. `committed` is the receipts that were
    committed, by the id of their file. Where it is given, every receipt of
    the evidence is held to the one committed for its file.
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
        behind = [evidence.row(row_id) for row_id in rows_behind(release, key)]
        rows = [row for row in behind if row is not None]
        if len(rows) < len(behind):
            found.append(Finding(key, "fact_has_a_row"))
            continue
        if any(fenced(row) for row in rows):
            found.append(Finding(key, "evidence_is_for_the_product"))
        if not all(row.has_a_value for row in rows):
            found.append(Finding(key, "row_has_a_value"))
        elif not cited <= frozenset().union(*(evidence.sources_of(row) for row in rows)):
            found.append(Finding(key, "source_has_a_file"))
        # The row of a fact that is one number holds the number. It is the row of its own id.
        own = evidence.row(key)
        held = own is not None and own.has_a_value
        if own is not None and held and not _same_figure(own.value, figure_of(release, key)):
            found.append(Finding(key, "row_holds_the_figure"))
    found += not_as_core_works_it_out(release)
    found += _of_the_receipts(evidence, lock, committed)
    if tagged is not None:
        found += _of_the_tags(evidence, tagged, measures or {})
    for row in evidence.rows:
        outline = row.measure == f"{FactKind.AREA}/{BOUNDARY}"
        drawn = outline and release.geometry(row.area_id) is not None
        if row.has_a_value and row.fact_id not in needed and not drawn:
            found.append(Finding(row.fact_id, "row_has_a_fact"))
        # Where the two disagree on whether there is a figure at all, that is what is found.
        agreed = row.has_a_value == (figure_of(release, row.fact_id) is not None)
        covered = coverage_of(release, row)
        if agreed and covered is not None and not _same_figure(covered, row.weight_covered):
            found.append(Finding(row.fact_id, "row_holds_the_coverage"))
        if lock is not None and not all(lock.holds(file_id) for file_id in row.inputs):
            found.append(Finding(row.fact_id, "input_is_locked"))
        if fenced(row):
            found.append(Finding(row.fact_id, "input_is_for_the_product"))
        if not unknown.isdisjoint(row.inputs):
            found.append(Finding(row.fact_id, "source_is_registered"))
        if not allowed(row):
            found.append(Finding(row.fact_id, "input_is_allowed"))
        kind, _, key = row.measure.partition("/")
        if measures and kind == FactKind.FEATURE and key in measures and row.has_a_value:
            found += [
                Finding(row.fact_id, rule)
                for rule in _of_the_measure(evidence, row, measures[key], lock)
            ]
    if registry is not None:
        # A made-up release cites the one source that is no dataset, so nothing is asked of it.
        if not release.manifest.synthetic:
            found += _of_what_is_cited(release, evidence, registry)
        found += _of_the_credits(release, registry)
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
