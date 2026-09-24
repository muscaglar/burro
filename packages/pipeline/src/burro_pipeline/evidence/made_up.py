"""Made-up evidence for the synthetic release, so every step can run before a file is fetched.

It reads nothing: no file, no dataset, no network. It is unmistakably made up.
Every receipt is of a file that does not exist, cites the source `synthetic`
and says `made_up`. The one method says that it measures nothing. A row takes
its state from what the synthetic release itself holds, so the gaps the
release has on purpose are gaps here too. A measure that core knows and the
release does not carry has a row that says so, for every area.
"""

import math
from collections.abc import Iterator

from burro_core.catalogue import FEATURES
from burro_core.facts import cost_key, fact_id
from burro_core.ids import FactKind, Mode, Tenure, segments_for
from burro_core.release import InMemoryRelease

from burro_pipeline.evidence.method import Kind, Method
from burro_pipeline.evidence.receipt import Geography, Period, Receipt, made_up_receipt
from burro_pipeline.evidence.row import EvidenceRow, not_carried, state_of
from burro_pipeline.evidence.served import BOUNDARY, NAME, NEAREST, journeys
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry.model import Use

METHOD = Method(
    derivation_id="made_up@1",
    sentence="Made up for testing from the invented character of each area, and it measures "
    "nothing.",
    kind=Kind.MODELLED,
    code="burro_pipeline.release.synthetic",
)
# How many units of a source a made-up area takes in. It is a number and nothing more.
UNITS = 10


def span(receipts: tuple[Receipt, ...]) -> Period:
    """The span of the data in several files."""
    first = min(receipt.data_period.days()[0] for receipt in receipts)
    last = max(receipt.data_period.days()[1] for receipt in receipts)
    return Period(as_at=first) if first == last else Period(start=first, end=last)


class _Files:
    """The made-up files of one synthetic release, each dated as the release dates its parts."""

    def __init__(self, release: InMemoryRelease) -> None:
        built = release.manifest.built_at
        vintages = sorted(metric.vintage for metric in release.metrics)
        months = sorted(cost.as_of for cost in release.costs)

        def file(name: str, use: Use, geography: Geography, *dated: str) -> Receipt:
            period = (
                Period(as_at=dated[0])
                if dated[0] == dated[-1]
                else Period(start=dated[0], end=dated[-1])
            )
            return made_up_receipt(name, use, geography, period, built)

        named = release.neighbourhoods_origin.as_of or built[:10]
        self.areas = file("made-up-areas.gpkg", Use.GAZETTEER, Geography.POLYGON, named)
        self.homes = file("made-up-homes.csv", Use.SCORING, Geography.OA21, named)
        self.measures = file(
            "made-up-measures.csv", Use.SCORING, Geography.LSOA21, vintages[0], vintages[-1]
        )
        self.costs = file(
            "made-up-costs.csv", Use.SCORING, Geography.POSTCODE, months[0], months[-1]
        )
        # A made-up preview may hold no journey and no station, and then dates neither. Its
        # made-up files are dated as its areas are: no row will rest on them.
        self.timetable = file(
            "made-up-timetable.zip",
            Use.ROUTING,
            Geography.NONE,
            release.travel_table.as_of or named,
        )
        self.stations = file(
            "made-up-stations.csv",
            Use.DISPLAY,
            Geography.POINT,
            release.stations_origin.as_of or named,
        )

    def all(self) -> tuple[Receipt, ...]:
        return (
            self.areas,
            self.homes,
            self.measures,
            self.costs,
            self.timetable,
            self.stations,
        )


def _row(
    key: str,
    files: tuple[Receipt, ...],
    has_value: bool,
    covered: float,
    value: float | None = None,
) -> EvidenceRow:
    inputs = tuple(sorted(files, key=lambda receipt: receipt.file_id))
    return EvidenceRow(
        fact_id=key,
        derivation_id=METHOD.derivation_id,
        inputs=tuple(receipt.file_id for receipt in inputs),
        data_period=span(inputs),
        retrieved_on=max(receipt.retrieved_on for receipt in inputs),
        units_used=math.ceil(covered * UNITS),
        units_expected=UNITS,
        weight_covered=covered,
        state=state_of(has_value, covered),
        value=value,
    )


def _rows(release: InMemoryRelease, files: _Files) -> Iterator[EvidenceRow]:
    known = journeys(release)
    measured = (files.homes, files.measures)
    carried = {metric.feature_id for metric in release.metrics}
    for area in release.neighbourhoods:
        for feature_id in sorted(FEATURES):
            if feature_id not in carried:
                yield not_carried(fact_id(area.area_id, FactKind.FEATURE, feature_id))
    for value in release.features:
        key = fact_id(value.area_id, FactKind.FEATURE, value.feature_id)
        yield _row(key, measured, value.value is not None, value.coverage, value.value)
    for tag in release.tags:
        key = fact_id(tag.area_id, FactKind.TAG, tag.tag_id)
        yield _row(key, measured, tag.score is not None, tag.coverage, tag.score)
    for area in release.neighbourhoods:
        area_id = area.area_id
        yield _row(fact_id(area_id, FactKind.AREA, NAME), (files.areas,), True, 1.0)
        drawn = release.geometry(area_id) is not None
        yield _row(fact_id(area_id, FactKind.AREA, BOUNDARY), (files.areas,), drawn, drawn * 1.0)
        for tenure in Tenure:
            for segment in segments_for(tenure):
                held = release.cost(area_id, tenure, segment) is not None
                key = fact_id(area_id, FactKind.COST, cost_key(tenure, segment))
                yield _row(key, (files.homes, files.costs), held, held * 1.0)
        for mode in Mode:
            reached, of = known[area_id, mode]
            key = fact_id(area_id, FactKind.TRAVEL, mode)
            yield _row(key, (files.homes, files.timetable), reached > 0, reached / of if of else 0)
        stations = release.stations(area_id)
        for station in stations:
            key = fact_id(area_id, FactKind.STATION, station.station_id)
            yield _row(key, (files.stations,), True, 1.0)
        if not any(station.nearest for station in stations):
            yield _row(fact_id(area_id, FactKind.STATION, NEAREST), (files.stations,), False, 0.0)


def made_up_evidence(release: InMemoryRelease) -> Evidence:
    """Made-up evidence for every figure of a synthetic release, and for every gap in it."""
    if not release.manifest.synthetic:
        raise ValueError("evidence is made up for a synthetic release, and for no other")
    files = _Files(release)
    return Evidence.of(release.manifest.release_id, files.all(), (METHOD,), _rows(release, files))
