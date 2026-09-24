"""The release of a build, and its evidence, from what `cells` and `derive` worked out.

What goes into the release:

| File of the release | What it holds in a first build |
|---|---|
| `neighbourhoods.json` | Every area: its label, its borough, a point inside it, its neighbours |
| `geometry.json` | Every area's outline |
| `catalogue.json`, `features.json` | Each measure worked out, and its figure for every area |
| `tags.json` | A row for every area and vibe, as core works one out. Too few parts make none |
| `cost.json` | What each kind of home sold for, where the build read it. No rent |
| `destinations.json`, `places.json` | Nothing |
| `travel.json`, `stations.json` | Nothing, and so no source and no date |

Nothing is filled in. A measure that could not be worked out is left out of
the release, and the evidence holds a row that says so for every area. A
journey and a station are not in a first build at all, and the evidence says
that too. So every pair of an area and a thing Burro measures has a row, and
a state.

A cost is what a home of one kind sold for: the publisher's median, with no
range. An area with no figure for a kind of home has no row of `cost.json`,
and its row of evidence says why: the publisher withheld it, or holds no row
for the area. A build that did not read the prices holds no cost, and the
evidence says of every cost that it is not carried. No build holds a rent.

A percentile, a vibe and its band are worked out by core: `percentile_of`,
`tag_raw` and `band_of`. The pipeline holds no second copy of that arithmetic.

A release carries the ten vibes and gritty as the one scale, which holds
recorded criminal damage and recorded anti-social behaviour beside land use,
main roads, noise and density: decided on 2026-09-24 (ADR 0013, as amended).
A vibe rests on the parts of its recipe that the release holds. Where they are
under 60 in 100 of the recipe it has no band, and that is core's rule too. So
gritty has no band until more of its recipe is measured than roads, noise and
density, and nothing stands in for what is not.

Every area can be ranked. An area is left out of ranking where a rate for each
resident would be unsteady, which needs a count of residents. A first build
reads none, and none of its measures is a rate for each resident. The areas
are the statistics office's own, which it draws to hold some thousands of
people each. Whether any should be left out is the founder's to say.
"""

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass

from burro_core.catalogue import (
    CATALOGUE_VERSION,
    FEATURES,
    TAGS,
    Tag,
    band_of,
    percentile_of,
    tag_raw,
)
from burro_core.catalogue import tags_of as vibes_of
from burro_core.facts import cost_key, fact_id
from burro_core.ids import (
    City,
    FactKind,
    FeatureId,
    GrittyVariant,
    Mode,
    Tenure,
    segments_for,
)
from burro_core.release import (
    SCHEMA_VERSION,
    AreaGeometry,
    CostEstimate,
    Counts,
    Cutoffs,
    FeatureValue,
    Geometry,
    InMemoryRelease,
    Manifest,
    Neighbourhood,
    Origin,
    Source,
    TagValue,
    TravelTable,
)

from burro_pipeline.cells import outline, spine
from burro_pipeline.cells.outline import Outline
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive.measures import TAGGED, Measure, Measured
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.row import FULLY_COVERED, EvidenceRow, State, not_carried
from burro_pipeline.evidence.served import BOUNDARY, NAME, NEAREST
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import period_of, retrieved_on
from burro_pipeline.registry import Registry

# Which way gritty is built in a release of London: as the one scale, which holds land
# use, main roads, noise, density and recorded incidents. Decided on 2026-09-24 (ADR 0013,
# as amended). An area has a band on it only where 60 in 100 of its recipe is measured.
GRITTY = GrittyVariant.B
# The longest journey a release routed, by mode. A first build routed none, and a release
# must still give one: contract, section 13. These are the contract's own, and limit nothing.
NOT_ROUTED = Cutoffs(pt=90, cycle=60, walk=60)


@dataclass(frozen=True)
class Carried:
    """One measure that is in the release, with what stands behind it."""

    measure: Measure
    measured: Measured

    @property
    def feature(self) -> FeatureId:
        return self.measure.feature


@dataclass(frozen=True)
class Costed:
    """The costs that are in the release, with what stands behind them."""

    # The rows of `cost.json`, in the order a release keeps them.
    rows: tuple[CostEstimate, ...]
    # A row of evidence for each area and each kind of home that was read, with a figure or
    # with why it has none.
    evidence: tuple[EvidenceRow, ...]
    # The receipt of every file a cost was worked out from.
    files: tuple[Receipt, ...]
    methods: tuple[Method, ...]


@dataclass(frozen=True)
class Drawn:
    """The geography of a build, as the release and its evidence need it."""

    spine: Spine
    outlines: Mapping[str, Outline]
    # The receipts of the lookup and of the boundaries the outlines were joined from.
    lookup: Receipt
    boundaries: Receipt

    @property
    def area_ids(self) -> tuple[str, ...]:
        return tuple(area.area_id for area in self.spine.areas)

    def homes(self) -> dict[str, int]:
        """The homes of each area: its households at the census. The weight of a share."""
        found = dict.fromkeys(self.area_ids, 0)
        for cell in self.spine.cells:
            found[self.spine.area_of[cell.oa]] += cell.homes
        return found


def neighbourhoods_of(drawn: Drawn) -> tuple[Neighbourhood, ...]:
    return tuple(
        Neighbourhood(
            area_id=area.area_id,
            slug=area.slug,
            name=area.name,
            borough=area.borough,
            # No file gives an area another name, and none is made up.
            aliases=(),
            centroid=drawn.outlines[area.area_id].centre,
            rankable=True,
            neighbours=drawn.outlines[area.area_id].neighbours,
        )
        for area in drawn.spine.areas
    )


def features_of(carried: Sequence[Carried], areas: Sequence[str]) -> tuple[FeatureValue, ...]:
    """A row for every area and every measure carried, with the percentile core gives it."""
    rankable = [True] * len(areas)
    rows: list[FeatureValue] = []
    for one in carried:
        worked = [one.measured.worked[area] for area in areas]
        percentiles = percentile_of([figure.value for figure in worked], rankable)
        rows += [
            FeatureValue(
                area_id=area,
                feature_id=one.feature,
                value=figure.value,
                percentile=percentile,
                coverage=figure.weight_covered,
            )
            for area, figure, percentile in zip(areas, worked, percentiles, strict=True)
        ]
    return tuple(rows)


def tags_of(
    features: Sequence[FeatureValue], areas: Sequence[str], vibes: Sequence[Tag]
) -> tuple[TagValue, ...]:
    """A row for every area and every vibe, as core works a vibe out from the percentiles.

    The band is core's, from the raw values. No file says how a vibe varies
    inside an area, so the spread is the band itself.
    """
    held: dict[str, dict[FeatureId, float | None]] = {area: {} for area in areas}
    for row in features:
        held[row.area_id][row.feature_id] = row.percentile
    rankable = [True] * len(areas)
    rows: list[TagValue] = []
    for vibe in sorted(vibes, key=lambda one: one.tag_id):
        found = [tag_raw(vibe.tag_id, held[area]) for area in areas]
        scores = percentile_of([one.raw for one in found], rankable)
        bands = band_of([one.raw for one in found], rankable)
        rows += [
            TagValue(
                area_id=area,
                tag_id=vibe.tag_id,
                raw=one.raw,
                score=score,
                coverage=one.coverage,
                band=band,
                spread_low=band,
                spread_high=band,
            )
            for area, one, score, band in zip(areas, found, scores, bands, strict=True)
        ]
    return tuple(rows)


def sources_of(registry: Registry, files: Sequence[Receipt]) -> tuple[Source, ...]:
    """Every source the release cites, as the licence registry credits it.

    A credit is the registry's own words, as it holds them. `retrieved_on` is
    the latest day a file of the source was fetched for this build.
    """
    by_source: dict[str, list[Receipt]] = {}
    for receipt in files:
        by_source.setdefault(receipt.source_id, []).append(receipt)
    found: list[Source] = []
    for source_id in sorted(by_source):
        entry = registry.get(source_id)
        found.append(
            Source(
                source_id=entry.id,
                name=entry.name,
                publisher=entry.publisher,
                licence=entry.licence.value,
                attribution=entry.attribution,
                url=entry.url,
                retrieved_on=retrieved_on(by_source[source_id]),
            )
        )
    return tuple(found)


def release_of(
    release_id: str,
    built_at: str,
    drawn: Drawn,
    carried: Sequence[Carried],
    registry: Registry,
    costed: Costed | None = None,
) -> InMemoryRelease:
    """The release of a first build: areas, outlines, the measures carried and the costs.

    It is a preview. It is as core will read it back, but for the list of its
    files and its counts, which `write_release` works out from the bytes it
    writes. `costed` is what the build read of what a home sells for, or
    nothing where it read none.
    """
    areas = drawn.area_ids
    features = features_of(carried, areas)
    vibes = vibes_of(GRITTY)
    named = (drawn.lookup, drawn.boundaries)
    cited = {receipt.file_id: receipt for receipt in named}
    for one in carried:
        cited |= {receipt.file_id: receipt for receipt in one.measured.files}
    if costed is not None and costed.rows:
        cited |= {receipt.file_id: receipt for receipt in costed.files}
    return InMemoryRelease(
        manifest=Manifest(
            release_id=release_id,
            schema_version=SCHEMA_VERSION,
            built_at=built_at,
            catalogue_version=CATALOGUE_VERSION,
            gritty_variant=GRITTY,
            synthetic=False,
            preview=True,
            city=City.LON,
            seed=None,
            sources=sources_of(registry, list(cited.values())),
            files=(),
            counts=Counts(neighbourhoods=0, rankable=0, destinations=0, places=0, stations=0),
        ),
        neighbourhoods=neighbourhoods_of(drawn),
        neighbourhoods_origin=Origin(
            source_ids=tuple(sorted({receipt.source_id for receipt in named})),
            # A label and a borough are the lookup's, so an area's name is dated as it is.
            as_of=drawn.lookup.data_period.days()[1][:7],
        ),
        travel_table=TravelTable(
            source_ids=(),
            as_of=None,
            area_ids=areas,
            destination_ids=(),
            cutoff_minutes=NOT_ROUTED,
            pt_typical=tuple(() for _ in areas),
            pt_just_missed=tuple(() for _ in areas),
            cycle=tuple(() for _ in areas),
            walk=tuple(() for _ in areas),
        ),
        stations_origin=Origin(source_ids=(), as_of=None),
        metrics=tuple(one.measured.metric for one in carried),
        features=features,
        tags=tags_of(features, areas, vibes),
        vibes=vibes,
        costs=costed.rows if costed is not None else (),
        geometries=tuple(
            AreaGeometry(
                area_id=area, geometry=Geometry.model_validate(drawn.outlines[area].geometry)
            )
            for area in areas
        ),
    )


def _of_the_area(
    area_id: str, key: str, method: Method, files: Sequence[Receipt], used: int, of: int
) -> EvidenceRow:
    """The row behind an area's label or its outline, from how many of its output areas."""
    covered = used / of if of else 0.0
    return EvidenceRow(
        fact_id=fact_id(area_id, FactKind.AREA, key),
        derivation_id=method.derivation_id,
        inputs=tuple(sorted(receipt.file_id for receipt in files)),
        data_period=period_of(files),
        retrieved_on=retrieved_on(files),
        units_used=used,
        units_expected=of,
        weight_covered=covered,
        state=State.PRESENT if covered >= FULLY_COVERED else State.PARTIAL,
    )


def _not_carried(area_id: str, kind: FactKind, key: str) -> EvidenceRow:
    """The row that says a release holds no figure, because it carries no such measure."""
    return not_carried(fact_id(area_id, kind, key))


def _of_a_tag(row: TagValue, behind: Mapping[FeatureId, Sequence[Receipt]]) -> EvidenceRow:
    """The row behind one tag in one area, from the measures of its recipe that had a figure."""
    terms = TAGS[row.tag_id].terms
    files = {
        receipt.file_id: receipt for term in terms for receipt in behind.get(term.feature_id, ())
    }
    if row.coverage == 0 or not files:
        return _not_carried(row.area_id, FactKind.TAG, row.tag_id)
    used = sorted(files.values(), key=lambda receipt: receipt.file_id)
    if row.score is None:
        state = State.BELOW_THRESHOLD
    else:
        state = State.PRESENT if row.coverage >= FULLY_COVERED else State.PARTIAL
    return EvidenceRow(
        fact_id=fact_id(row.area_id, FactKind.TAG, row.tag_id),
        derivation_id=TAGGED.derivation_id,
        inputs=tuple(receipt.file_id for receipt in used),
        data_period=period_of(used),
        retrieved_on=retrieved_on(used),
        units_used=sum(term.feature_id in behind for term in terms),
        units_expected=len(terms),
        weight_covered=row.coverage,
        state=state,
        value=row.score,
    )


def _tag_rows(release: InMemoryRelease, carried: Sequence[Carried]) -> Iterator[EvidenceRow]:
    valued = {
        (row.area_id, row.feature_id) for row in release.features if row.percentile is not None
    }
    files = {one.feature: one.measured.files for one in carried}
    for row in release.tags:
        behind = {
            feature: receipts
            for feature, receipts in files.items()
            if (row.area_id, feature) in valued
        }
        yield _of_a_tag(row, behind)


def _area_rows(drawn: Drawn, area_id: str) -> tuple[EvidenceRow, EvidenceRow]:
    """The rows behind an area's label and behind its outline."""
    joined = drawn.outlines[area_id]
    of = joined.units_expected
    drawn_from = (drawn.lookup, drawn.boundaries)
    return (
        # The fact of an area cites what `neighbourhoods.json` cites: the lookup for its label
        # and its borough, and the boundaries for the point inside it and its neighbours.
        _of_the_area(area_id, NAME, spine.LABELLED, drawn_from, of, of),
        _of_the_area(area_id, BOUNDARY, outline.JOINED, drawn_from, joined.units_used, of),
    )


def _absent(release: InMemoryRelease, said: frozenset[str]) -> Iterator[EvidenceRow]:
    """A row for every thing Burro measures that this release does not carry.

    `said` holds the ids of the costs that have a row already, which says why
    an area has no figure: the build read the file, and the file gives none.
    """
    carried = {metric.feature_id for metric in release.metrics}
    costs = [cost_key(tenure, segment) for tenure in Tenure for segment in segments_for(tenure)]
    for area in release.neighbourhoods:
        area_id = area.area_id
        for feature_id in sorted(FEATURES):
            if feature_id not in carried:
                yield _not_carried(area_id, FactKind.FEATURE, feature_id)
        if not release.destinations:
            for mode in Mode:
                yield _not_carried(area_id, FactKind.TRAVEL, mode)
        held = {cost_key(c.tenure, c.segment) for c in release.costs if c.area_id == area_id}
        for key in costs:
            if key not in held and fact_id(area_id, FactKind.COST, key) not in said:
                yield _not_carried(area_id, FactKind.COST, key)
        if not release.stations(area_id):
            yield _not_carried(area_id, FactKind.STATION, NEAREST)


def evidence_of(
    release: InMemoryRelease,
    drawn: Drawn,
    carried: Sequence[Carried],
    costed: Costed | None = None,
) -> Evidence:
    """The evidence of a release: a row for every figure, and for every figure it lacks."""
    receipts = {receipt.file_id: receipt for receipt in (drawn.lookup, drawn.boundaries)}
    methods = {method.derivation_id: method for method in (spine.LABELLED, outline.JOINED)}
    rows: list[EvidenceRow] = []
    for area_id in drawn.area_ids:
        rows += _area_rows(drawn, area_id)
    for one in carried:
        receipts |= {receipt.file_id: receipt for receipt in one.measured.files}
        methods |= {method.derivation_id: method for method in one.measure.methods}
        rows += one.measured.rows
    tagged = list(_tag_rows(release, carried))
    if any(row.derivation_id is not None for row in tagged):
        methods[TAGGED.derivation_id] = TAGGED
    rows += tagged
    said: frozenset[str] = frozenset()
    if costed is not None and costed.rows:
        receipts |= {receipt.file_id: receipt for receipt in costed.files}
        methods |= {method.derivation_id: method for method in costed.methods}
        rows += costed.evidence
        said = frozenset(row.fact_id for row in costed.evidence)
    rows += _absent(release, said)
    return Evidence.of(release.manifest.release_id, receipts.values(), methods.values(), rows)
