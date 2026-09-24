"""Coverage: for every area and every measure, the state it is in and whether a record says so.

`cover` reads a release and its evidence and gives one cell for each area and
measure. There is no blank. `report` writes the tables a person reads from it,
and `summary` the one line a build may print.

Where a row of evidence stands behind a cell and agrees with the release, the
cell takes the row's state. Where none does, the state is worked out from the
release alone, and the cell says that no record stands behind it.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal, NamedTuple, Self

from burro_core.catalogue import FEATURES
from burro_core.facts import cost_key
from burro_core.ids import (
    AreaId,
    FactKind,
    FeatureId,
    Mode,
    ReleaseId,
    SourceId,
    TagId,
    Tenure,
    segments_for,
)
from burro_core.release import InMemoryRelease, Neighbourhood
from pydantic import Field, PrivateAttr, model_validator

from burro_pipeline.evidence.claim import ClaimKind, ReviewStatus
from burro_pipeline.evidence.record import Day, EvidenceRecord, Share, Text, strictly_increasing
from burro_pipeline.evidence.row import FULLY_COVERED, HAS_A_VALUE, IS_A_GAP, State, state_of
from burro_pipeline.evidence.served import BOUNDARY, NAME, NEAREST, journeys
from burro_pipeline.evidence.store import Evidence

SCHEMA_VERSION = 1
# An area has enough to be ranked on when this share of the features carried have a value.
# It is the proposed launch gate, and is the founder's to confirm.
ENOUGH_TO_RANK = 0.8
ESSENTIALS = ("name", "boundary", "journeys", "cost", "enough to rank")

# Why a figure is missing, and what would close the gap, by state.
REASONS: Mapping[State, tuple[str, str]] = {
    State.BELOW_THRESHOLD: (
        "Too little of the area had data to give a figure",
        "A source that covers more of the area",
    ),
    State.SOURCE_GAP: ("The source holds nothing for this area", "A source that holds it"),
    State.SUPPRESSED: ("The publisher withheld the figure", "Nothing. The publisher decides"),
    State.NOT_CARRIED: (
        "This build does not work the measure out",
        "A source the licence registry approves",
    ),
}


# What is said of a measure that a build worked out and left out of its release.
LEFT_OUT = "Worked out, and left out of the release"


class LeftOut(NamedTuple):
    """A measure that a build worked out and left out of its release, and why.

    It is what the build says, and no part of the coverage: a report is given
    it beside the coverage, so that a reader is not told that nothing works
    the measure out.
    """

    # The measure, as a report names it: `feature/green_cover`.
    measure: str
    # The rule of the build that kept it out, and what the rule means, in words that
    # finish a sentence beginning "It".
    rule: str
    why: str
    # What is not settled, and whose it is to settle. Each is a sentence or two.
    waits_on: tuple[str, ...]


class Area(EvidenceRecord):
    area_id: AreaId
    name: Text
    borough: Text
    rankable: bool
    # What the area counts for in a share of the whole: its homes, or 1 where none was given.
    weight: int = Field(ge=0)


class Cell(EvidenceRecord):
    area_id: AreaId
    measure: Text
    state: State
    # Whether a row of evidence stands behind the cell, and agrees with the release.
    record: bool
    # Null where nothing says how much of the area was covered.
    weight_covered: Share | None

    @property
    def has_a_value(self) -> bool:
        return self.state in HAS_A_VALUE

    @property
    def covered(self) -> float:
        """How much was covered, taking a figure with no share as whole and a gap as none."""
        if self.weight_covered is not None:
            return self.weight_covered
        return 1.0 if self.has_a_value else 0.0


class SourceCoverage(EvidenceRecord):
    source_id: SourceId
    files: int = Field(ge=1)
    # The span of the data in its files, and the latest day one was retrieved.
    first_day: Day
    last_day: Day
    retrieved_on: Day
    # Areas where a figure rests on a file of this source.
    areas_with_a_record: int = Field(ge=0)
    # The share of the whole that those figures cover.
    share_covered: Share
    boroughs_with_a_gap: tuple[Text, ...]


class ClaimCount(EvidenceRecord):
    kind: ClaimKind
    found: int = Field(ge=0)
    accepted: int = Field(ge=0)
    pending: int = Field(ge=0)
    # How many were rejected, by reason code.
    rejected: dict[str, int]


class Coverage(EvidenceRecord):
    schema_version: Literal[1] = SCHEMA_VERSION
    release_id: ReleaseId
    synthetic: bool
    # What a share of the whole is a share of.
    weighted_by: Literal["homes", "areas"]
    areas: tuple[Area, ...]
    # In the order a report lists them.
    measures: tuple[Text, ...]
    # One for every area and every measure, by area and then by measure.
    cells: tuple[Cell, ...]
    sources: tuple[SourceCoverage, ...]
    claims: tuple[ClaimCount, ...]

    _cells: dict[tuple[str, str], Cell] = PrivateAttr(default_factory=dict[tuple[str, str], Cell])

    def model_post_init(self, context: object) -> None:
        self._cells.update({(cell.area_id, cell.measure): cell for cell in self.cells})

    @model_validator(mode="after")
    def _has_no_blank(self) -> Self:
        if not strictly_increasing([area.area_id for area in self.areas]):
            raise ValueError("areas are sorted by id, each once")
        if not strictly_increasing([source.source_id for source in self.sources]):
            raise ValueError("sources are sorted by id, each once")
        if len(set(self.measures)) != len(self.measures):
            raise ValueError("a measure is listed once")
        expected = [(a.area_id, m) for a in self.areas for m in sorted(self.measures)]
        if [(cell.area_id, cell.measure) for cell in self.cells] != expected:
            raise ValueError("there is one cell for every area and every measure, in order")
        return self

    def cell(self, area_id: str, measure: str) -> Cell:
        return self._cells[area_id, measure]

    @property
    def gaps(self) -> tuple[Cell, ...]:
        return tuple(cell for cell in self.cells if cell.state in IS_A_GAP)

    @property
    def without_a_record(self) -> tuple[Cell, ...]:
        return tuple(cell for cell in self.cells if not cell.record)


def measures_of(release: InMemoryRelease) -> tuple[str, ...]:
    """Every measure a release is held to, in the order a report lists them.

    A feature that core knows and the release does not carry is a measure too:
    it is `not_carried` in every area. The vibes are the ones the release
    carries: gritty is built one of two ways, and a release holds the one its
    manifest names.
    """
    return (
        f"{FactKind.AREA}/{NAME}",
        f"{FactKind.AREA}/{BOUNDARY}",
        *(f"{FactKind.TRAVEL}/{mode}" for mode in Mode),
        *(
            f"{FactKind.COST}/{cost_key(tenure, segment)}"
            for tenure in Tenure
            for segment in segments_for(tenure)
        ),
        f"{FactKind.STATION}/{NEAREST}",
        *(f"{FactKind.FEATURE}/{feature_id}" for feature_id in sorted(FEATURES)),
        *(f"{FactKind.TAG}/{tag_id}" for tag_id in sorted(vibe.tag_id for vibe in release.vibes)),
    )


class _Reader:
    """Reads one release, and says of an area and a measure what the release holds."""

    def __init__(self, release: InMemoryRelease, evidence: Evidence | None) -> None:
        self.release = release
        self.evidence = evidence
        self.journeys = journeys(release)
        self.carried = {metric.feature_id for metric in release.metrics}
        self.costs = {(c.area_id, cost_key(c.tenure, c.segment)) for c in release.costs}

    def held(self, area_id: str, kind: str, key: str) -> tuple[bool, float | None] | None:
        """Whether the release has a figure, and how much it covered. Null if not carried."""
        release = self.release
        if kind == FactKind.FEATURE:
            if FeatureId(key) not in self.carried:
                return None
            value = release.feature(area_id, FeatureId(key))
            return (False, 0.0) if value is None else (value.value is not None, value.coverage)
        if kind == FactKind.TAG:
            tag = release.tag(area_id, TagId(key))
            return (False, 0.0) if tag is None else (tag.score is not None, tag.coverage)
        if kind == FactKind.TRAVEL:
            known, total = self.journeys[area_id, Mode(key)]
            return known > 0, (known / total if total else 0.0)
        if kind == FactKind.COST:
            return (area_id, key) in self.costs, None
        if kind == FactKind.STATION:
            return any(row.nearest for row in release.stations(area_id)), None
        return (True if key == NAME else release.geometry(area_id) is not None), None

    def row_id(self, area_id: str, kind: str, key: str) -> str:
        """The id of the row that would stand behind a cell."""
        if kind == FactKind.STATION:
            nearest = [row for row in self.release.stations(area_id) if row.nearest]
            key = nearest[0].station_id if nearest else NEAREST
        return f"{area_id}/{kind}/{key}"

    def cell(self, area_id: str, measure: str) -> Cell:
        kind, key = measure.split("/", 1)
        held = self.held(area_id, kind, key)
        row = self.evidence.row(self.row_id(area_id, kind, key)) if self.evidence else None
        if held is None:
            said = row is not None and row.state is State.NOT_CARRIED
            return Cell(
                area_id=area_id,
                measure=measure,
                state=State.NOT_CARRIED,
                record=said,
                weight_covered=None,
            )
        has_value, covered = held
        if row is not None and row.state is State.NOT_CARRIED and not has_value:
            # The release holds no journey, no cost or no station at all, and its
            # evidence says so. That is not a gap in a source: there is no source.
            return Cell(
                area_id=area_id,
                measure=measure,
                state=State.NOT_CARRIED,
                record=True,
                weight_covered=None,
            )
        if row is not None and row.has_a_value == has_value and row.state is not State.NOT_CARRIED:
            return Cell(
                area_id=area_id,
                measure=measure,
                state=row.state,
                record=True,
                weight_covered=row.weight_covered,
            )
        whole = 1.0 if has_value else 0.0
        return Cell(
            area_id=area_id,
            measure=measure,
            state=state_of(has_value, whole if covered is None else covered),
            record=False,
            weight_covered=covered,
        )


def _sources(evidence: Evidence, areas: tuple[Area, ...]) -> Iterable[SourceCoverage]:
    total = sum(area.weight for area in areas)
    for source_id in sorted({receipt.source_id for receipt in evidence.receipts}):
        files = [receipt for receipt in evidence.receipts if receipt.source_id == source_id]
        covered: dict[str, float] = {}
        for row in evidence.rows:
            if row.has_a_value and source_id in evidence.sources_of(row):
                covered[row.area_id] = max(covered.get(row.area_id, 0.0), row.weight_covered)
        share = sum(area.weight * covered.get(area.area_id, 0.0) for area in areas)
        yield SourceCoverage(
            source_id=source_id,
            files=len(files),
            first_day=min(receipt.data_period.days()[0] for receipt in files),
            last_day=max(receipt.data_period.days()[1] for receipt in files),
            retrieved_on=max(receipt.retrieved_on for receipt in files),
            areas_with_a_record=len(covered),
            share_covered=share / total if total else 0.0,
            boroughs_with_a_gap=tuple(
                sorted({area.borough for area in areas if area.area_id not in covered})
            ),
        )


def _claims(evidence: Evidence) -> Iterable[ClaimCount]:
    for kind in ClaimKind:
        found = [claim for claim in evidence.claims if claim.kind is kind]
        status = Counter(claim.review.status for claim in found)
        reasons = Counter(claim.review.reason or "" for claim in found if claim.review.reason)
        if found:
            yield ClaimCount(
                kind=kind,
                found=len(found),
                accepted=status[ReviewStatus.ACCEPTED],
                pending=status[ReviewStatus.PENDING],
                rejected=dict(sorted(reasons.items())),
            )


def cover(
    release: InMemoryRelease,
    evidence: Evidence | None = None,
    homes: Mapping[str, int] | None = None,
) -> Coverage:
    """The coverage of a release: one cell for every area and every measure.

    `homes` is the number of homes in each area. With it, a share of the whole
    is a share of homes. Without it every area counts once, and the report says
    so: no count of homes is ever made up.
    """
    if evidence is not None and evidence.release_id != release.manifest.release_id:
        raise ValueError("the evidence is not of this release")
    if homes is not None and set(homes) != {area.area_id for area in release.neighbourhoods}:
        raise ValueError("homes are given for every area of the release, and for no other")

    def area(found: Neighbourhood) -> Area:
        return Area(
            area_id=found.area_id,
            name=found.name,
            borough=found.borough,
            rankable=found.rankable,
            weight=1 if homes is None else homes[found.area_id],
        )

    areas = tuple(area(found) for found in release.neighbourhoods)
    measures = measures_of(release)
    reader = _Reader(release, evidence)
    return Coverage(
        release_id=release.manifest.release_id,
        synthetic=release.manifest.synthetic,
        weighted_by="areas" if homes is None else "homes",
        areas=areas,
        measures=measures,
        cells=tuple(
            reader.cell(found.area_id, measure) for found in areas for measure in sorted(measures)
        ),
        sources=tuple(_sources(evidence, areas)) if evidence else (),
        claims=tuple(_claims(evidence)) if evidence else (),
    )


# The report. Everything below reads a `Coverage` and nothing else.


def _percent(share: float) -> str:
    """A share as a whole percentage, rounded down so that it never says more than is so."""
    return f"{int(share * 100 + 1e-9)}%"


def _table(head: tuple[str, ...], rows: Iterable[tuple[object, ...]]) -> list[str]:
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(str(item) for item in row) + " |" for row in rows]
    return [*lines, ""]


def _values(cells: Iterable[Cell]) -> int:
    return sum(cell.has_a_value for cell in cells)


def essentials(coverage: Coverage, area_id: str) -> tuple[str, ...]:
    """Which of the five things an honest result needs this area lacks (ADR 0014)."""

    def has(measure: str) -> bool:
        return coverage.cell(area_id, measure).has_a_value

    def any_of(tenure: Tenure) -> bool:
        return any(has(m) for m in coverage.measures if m.startswith(f"cost/{tenure}."))

    features = [
        coverage.cell(area_id, m) for m in coverage.measures if m.startswith(f"{FactKind.FEATURE}/")
    ]
    carried = [cell for cell in features if cell.state is not State.NOT_CARRIED]
    present = {
        "name": has(f"{FactKind.AREA}/{NAME}"),
        "boundary": has(f"{FactKind.AREA}/{BOUNDARY}"),
        "journeys": all(has(f"{FactKind.TRAVEL}/{mode}") for mode in Mode),
        "cost": all(any_of(tenure) for tenure in Tenure),
        "enough to rank": bool(carried) and _values(carried) >= ENOUGH_TO_RANK * len(carried),
    }
    return tuple(name for name in ESSENTIALS if not present[name])


def _by_source(coverage: Coverage) -> list[str]:
    if not coverage.sources:
        return ["No evidence was given, so no source can be counted.", ""]
    head = (
        "Source",
        "Files",
        "Data from",
        "Data to",
        "Retrieved",
        f"Areas with a record, of {len(coverage.areas)}",
        f"Share of {coverage.weighted_by} covered",
        "Boroughs with a gap",
    )
    return _table(
        head,
        (
            (
                source.source_id,
                source.files,
                source.first_day,
                source.last_day,
                source.retrieved_on,
                source.areas_with_a_record,
                _percent(source.share_covered),
                ", ".join(source.boroughs_with_a_gap) or "none",
            )
            for source in coverage.sources
        ),
    )


def _least_covered(coverage: Coverage, measure: str) -> str:
    """The borough where the smallest share of areas has a value, and that share."""
    boroughs: dict[str, list[Cell]] = {}
    for area in coverage.areas:
        boroughs.setdefault(area.borough, []).append(coverage.cell(area.area_id, measure))
    name, cells = min(boroughs.items(), key=lambda item: (_values(item[1]) / len(item[1]), item[0]))
    return f"{name}: {_values(cells)} of {len(cells)}"


def _by_measure(coverage: Coverage) -> list[str]:
    rows: list[tuple[object, ...]] = []
    for measure in coverage.measures:
        cells = [coverage.cell(area.area_id, measure) for area in coverage.areas]
        states = Counter(cell.state for cell in cells)
        rows.append(
            (
                measure,
                *(states[state] for state in State),
                sum(not cell.record for cell in cells),
                _least_covered(coverage, measure),
            )
        )
    head = ("Measure", *(str(state) for state in State), "No record", "Least covered borough")
    return _table(head, rows)


def _by_area(coverage: Coverage) -> list[str]:
    rows: list[tuple[object, ...]] = []
    for area in coverage.areas:
        cells = [coverage.cell(area.area_id, measure) for measure in coverage.measures]
        carried = [cell for cell in cells if cell.state is not State.NOT_CARRIED]
        lacking = essentials(coverage, area.area_id)
        worst = min(carried, key=lambda cell: cell.covered, default=None)
        short = worst is not None and worst.covered < FULLY_COVERED
        rows.append(
            (
                area.area_id,
                area.name,
                area.borough,
                "yes" if area.rankable else "no",
                f"{_values(carried)} of {len(carried)}",
                f"{len(ESSENTIALS) - len(lacking)} of {len(ESSENTIALS)}"
                + (f": lacks {', '.join(lacking)}" if lacking else ""),
                f"{worst.measure}: {worst.state}" if worst and short else "none",
            )
        )
    head = ("Area", "Name", "Borough", "Ranked", "Measures with a value", "Essentials", "Worst")
    return _table(head, rows)


def held_nowhere(coverage: Coverage) -> tuple[str, ...]:
    """The measures that are a gap in every area: the release has no figure for one at all."""
    gaps = dict.fromkeys(coverage.measures, 0)
    for cell in coverage.gaps:
        gaps[cell.measure] += 1
    return tuple(m for m in coverage.measures if gaps[m] and gaps[m] == len(coverage.areas))


def _why(one: LeftOut) -> tuple[str, str]:
    """Why a measure that was worked out is not in the release, and what would bring it in."""
    return f"{LEFT_OUT}: it {one.why} [{one.rule}]", " ".join(one.waits_on)


def _left_out(left_out: Sequence[LeftOut]) -> list[str]:
    """What the build worked out and left out of the release, each with its rule."""
    return [
        "Each of these has a figure and a row of evidence, made by this build. None is in the "
        "release, and nothing stands in for one.",
        "",
        *_table(
            ("Measure", "Rule", "Why", "What it waits on"),
            ((one.measure, one.rule, f"It {one.why}", " ".join(one.waits_on)) for one in left_out),
        ),
    ]


def _said_once(coverage: Coverage, nowhere: set[str], left_out: Mapping[str, LeftOut]) -> list[str]:
    """What no area has a figure for, said once and not once for every area."""
    cells: dict[str, list[Cell]] = {measure: [] for measure in nowhere}
    for cell in coverage.cells:
        if cell.measure in nowhere:
            cells[cell.measure].append(cell)
    rows: list[tuple[object, ...]] = []
    for measure in coverage.measures:
        if measure not in nowhere:
            continue
        states = sorted({cell.state for cell in cells[measure]})
        recorded = "yes" if all(cell.record for cell in cells[measure]) else "no"
        reasons = REASONS[states[0]] if len(states) == 1 else ("It differs by area", "")
        if measure in left_out:
            reasons = _why(left_out[measure])
        rows.append((measure, ", ".join(states), recorded, *reasons))
    held = len(coverage.measures) - len(nowhere)
    return [
        f"Of the {len(coverage.measures)} things Burro measures, {held} have a figure in at "
        f"least one area. Each of the other {len(nowhere)} is a gap in every area, and is "
        "listed once.",
        "",
        *_table(("Measure", "State", "Record", "Reason", "What would close it"), rows),
    ]


def _gaps(coverage: Coverage, left_out: Mapping[str, LeftOut]) -> list[str]:
    if not coverage.gaps:
        return ["No area lacks a measure.", ""]
    order = {measure: index for index, measure in enumerate(coverage.measures)}
    nowhere = set(held_nowhere(coverage))
    lines = _said_once(coverage, nowhere, left_out) if nowhere else []
    here = [cell for cell in coverage.gaps if cell.measure not in nowhere]
    if not here:
        return [*lines, "No area lacks a measure that some other area has.", ""]
    head = ("Area", "Measure", "State", "Record", "Reason", "What would close it")
    return lines + _table(
        head,
        (
            (
                cell.area_id,
                cell.measure,
                cell.state,
                "yes" if cell.record else "no",
                *REASONS[cell.state],
            )
            for cell in sorted(here, key=lambda cell: (cell.area_id, order[cell.measure]))
        ),
    )


def _claims_table(coverage: Coverage) -> list[str]:
    if not coverage.claims:
        return ["This release holds no claim.", ""]
    head = ("Kind", "Found", "Accepted", "Waiting for review", "Rejected, by reason")
    return _table(
        head,
        (
            (
                count.kind,
                count.found,
                count.accepted,
                count.pending,
                ", ".join(f"{reason} {n}" for reason, n in count.rejected.items()) or "none",
            )
            for count in coverage.claims
        ),
    )


def _not_in_the_release(coverage: Coverage, left_out: Sequence[LeftOut]) -> dict[str, LeftOut]:
    """What was left out, by measure. Refused if the release carries one of them after all."""
    found = {one.measure: one for one in left_out}
    for measure in found:
        carried = measure in coverage.measures and any(
            coverage.cell(area.area_id, measure).state is not State.NOT_CARRIED
            for area in coverage.areas
        )
        if carried or measure not in coverage.measures or len(found) != len(left_out):
            raise ValueError(
                "what is said to be left out is a measure of the release, is no measure at all, "
                "or is said twice"
            )
    return found


def report(coverage: Coverage, left_out: Sequence[LeftOut] = ()) -> str:
    """The coverage report: what a person reads before a release is approved.

    `left_out` is what the build worked out and left out of the release, as
    the build says it. With it the report says of each why it is not there.
    Without it such a measure reads as one that no step works out.
    """
    cells = coverage.cells
    kept_out = _not_in_the_release(coverage, left_out)
    unpublished = sum(cell.state is State.NOT_PUBLISHED for cell in cells)
    counted_by = {
        "homes": "homes",
        "areas": "areas, each counted once, because no count of homes was given",
    }[coverage.weighted_by]
    lines = [f"# Coverage of {coverage.release_id}", ""]
    if coverage.synthetic:
        lines += [
            "This release is made up, and so is its evidence. It describes no real place.",
            "",
        ]
    lines += _table(
        ("What", "Count"),
        (
            ("Areas", len(coverage.areas)),
            ("Areas that can be ranked", sum(area.rankable for area in coverage.areas)),
            ("Measures", len(coverage.measures)),
            ("Pairs of an area and a measure", len(cells)),
            ("Pairs with a value", _values(cells)),
            ("Gaps", len(coverage.gaps)),
            ("Not published for areas this small", unpublished),
            ("Pairs with no record behind them", len(coverage.without_a_record)),
            ("A share of the whole is a share of", counted_by),
        ),
    )
    lines += [
        "A gap is a pair in the state `below_threshold`, `source_gap`, `suppressed` or "
        "`not_carried`. An area has enough to rank when "
        f"{_percent(ENOUGH_TO_RANK)} of the features carried have a value, which is a proposed "
        "gate and not yet a confirmed one.",
        "",
    ]
    sections = [
        ("By source", _by_source(coverage)),
        ("By measure", _by_measure(coverage)),
        ("By area", _by_area(coverage)),
        *([("Worked out and left out", _left_out(left_out))] if left_out else []),
        ("Gaps", _gaps(coverage, kept_out)),
        ("Claims", _claims_table(coverage)),
    ]
    for title, table in sections:
        lines += [f"## {title}", "", *table]
    return "\n".join(lines).rstrip("\n") + "\n"


def summary(coverage: Coverage) -> str:
    """One line of counts and a hash: what a build may print where anyone can read it."""
    counts = {
        "release": coverage.release_id,
        "areas": len(coverage.areas),
        "measures": len(coverage.measures),
        "values": _values(coverage.cells),
        "gaps": len(coverage.gaps),
        "no_record": len(coverage.without_a_record),
        "coverage_sha256": coverage.digest(),
    }
    return " ".join(f"{key}={value}" for key, value in counts.items())
