"""Facts: each one thing Burro may say about one area, with where it came from and when.

Every number and proper noun the product shows about a place must trace to a
fact. Numbers are formatted once, here, so a template, a model and the verifier
all see the same spelling. A missing value never produces a fact that carries
a number.

A comparison must be literally true of the release. Areas are scored on a
mid-rank percentile, which counts half of the areas that tie as beaten. A
sentence may not: it states the share of areas strictly beyond this one,
rounded down, names how many areas were compared, and says how many are level.
"""

from bisect import bisect_left, bisect_right
from collections.abc import Callable, Iterator, Mapping
from typing import NamedTuple

from pydantic import Field

from burro_core._record import Record
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import (
    BUDGET,
    COMMUTE,
    Dimension,
    FactKind,
    FeatureId,
    Mode,
    Part,
    PtBasis,
    Segment,
    TagId,
    TemplateId,
    Tenure,
    TravelStatus,
    component_for_feature,
    component_for_tag,
    segments_for,
)
from burro_core.release import (
    MANIFEST,
    TAGS_FILE,
    CostEstimate,
    Neighbourhood,
    Origin,
    Release,
    ReleaseError,
    Travel,
)
from burro_core.spec import Commute, PreferenceSpec, SpecError, check_spec


class FactSource(Record):
    source_id: str
    name: str


class Fact(Record):
    fact_id: str
    area_id: str
    kind: FactKind
    key: str
    label: str
    # The template that states this fact. A failed sentence is replaced by it.
    template: TemplateId
    # The values a template prints, already formatted.
    slots: dict[str, str]
    # Every number that may be printed for this fact, as the verifier normalises it.
    numbers: tuple[str, ...]
    # Every proper noun that may be printed for this fact.
    names: tuple[str, ...]
    sources: tuple[FactSource, ...] = Field(min_length=1)
    as_of: str = Field(min_length=1)
    synthetic: bool


SEGMENT_LABELS: Mapping[Segment, str] = {
    Segment.ROOM: "room in a shared home",
    Segment.STUDIO: "studio",
    Segment.BED_1: "1-bedroom home",
    Segment.BED_2: "2-bedroom home",
    Segment.BED_3: "3-bedroom home",
    Segment.BED_4PLUS: "home with 4 or more bedrooms",
    Segment.FLAT: "flat",
    Segment.TERRACED: "terraced house",
    Segment.SEMI_DETACHED: "semi-detached house",
    Segment.DETACHED: "detached house",
}
MODE_LABELS: Mapping[Mode, str] = {
    Mode.PT: "By public transport",
    Mode.CYCLE: "By bike",
    Mode.WALK: "On foot",
}
COST_LABELS: Mapping[Tenure, str] = {Tenure.RENT: "Rent", Tenure.BUY: "Price"}
# What the `missing` sentence calls a component that has no figure.
MISSING_LABELS: Mapping[str, str] = {COMMUTE: "journey time", BUDGET: "cost"}
# How a tag's score is compared, where a feature has comparatives of its own.
TAG_HIGHER, TAG_LOWER = "above", "below"
# Where a figure sits among the areas it is compared with. Every release says
# "in this release", so a synthetic one can never say "London".
STANDINGS: Mapping[str, str] = {
    "beyond": "{comparative} {pct}% of the {compared} areas compared in this release",
    "beyond_and_level": (
        "{comparative} {pct}% of the {compared} areas compared in this release, "
        "and the same as {level} {other}"
    ),
    "level": "the same as {level} of the {others} other areas compared in this release",
    "all_level": "the same as all {others} other areas compared in this release",
    "one_level": "the same as the only other area compared in this release",
    "alone": "with no other area in this release to compare it with",
}
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def fact_id(area_id: str, kind: FactKind, key: str) -> str:
    """The one rule for a fact's id, so an id `rank()` names is one `facts_for()` returns."""
    return f"{area_id}/{kind}/{key}"


def travel_key(commute: Commute) -> str:
    return f"{commute.place_id}.{commute.mode}"


def cost_key(tenure: Tenure, segment: Segment) -> str:
    return f"{tenure}.{segment}"


def money(pounds: int) -> str:
    return f"{pounds:,}"


def pounds(amount: int) -> str:
    """An amount of money as the verifier holds it: marked as money, with no separators."""
    return f"£{amount}"


def percent(number: str) -> str:
    """A percentage as the verifier holds it: marked as one."""
    return f"{number}%"


def plain(value: float) -> str:
    """One decimal, with a trailing `.0` dropped."""
    text = f"{round(value, 1):.1f}".removesuffix(".0")
    return "0" if text == "-0" else text


def month(as_of: str) -> str:
    """`2026-08` as people write it: August 2026."""
    year, number = as_of.split("-")[:2]
    return f"{_MONTHS[int(number) - 1]} {year}"


def _value(value: float, unit: str) -> tuple[str, str]:
    """A feature's value as it is printed, unit attached, and the number in it."""
    if unit == "m":
        number = str(round(value / 10) * 10)
        return f"{number} m", number
    if unit == "%":
        number = str(round(value))
        return f"{number}%", percent(number)
    number = plain(value)
    return (number if unit == "count" else f"{number} {unit}"), number


class Standing(NamedTuple):
    """Where one area's figure sits among the rankable areas that have one.

    These are counts of areas, so each is exactly true of the release. The
    area itself is one of `compared` when it is rankable.
    """

    compared: int
    below: int  # areas whose figure is strictly lower
    above: int  # areas whose figure is strictly higher
    level: int  # other areas whose figure is the same

    @property
    def others(self) -> int:
        return self.below + self.above + self.level

    @property
    def higher(self) -> bool:
        """Whether the sentence says what the area is above. It is the side the percentile is on."""
        return self.below >= self.above

    @property
    def pct(self) -> int:
        """The share of the areas compared that are strictly beyond this one, rounded down.

        Rounded down and never to the nearest, so that "closer than 40% of
        areas" is true when 40.9% of them are further away.
        """
        beyond = self.below if self.higher else self.above
        return 100 * beyond // self.compared if self.compared else 0


def standing(value: float, population: list[float], among: bool) -> Standing:
    """Where `value` sits in `population`, which is sorted. `among` if it is one of them."""
    below = bisect_left(population, value)
    equal = bisect_right(population, value) - below
    return Standing(
        compared=len(population),
        below=below,
        above=len(population) - below - equal,
        level=equal - 1 if among else equal,
    )


def said(found: Standing, higher: str, lower: str) -> tuple[dict[str, str], tuple[str, ...]]:
    """The slots that state a standing, and the numbers in them.

    `standing` is the whole clause, which the templates print. The others are
    its parts, for a client that lays them out for itself.
    """
    if found.others == 0:
        return {"standing": STANDINGS["alone"]}, ()
    if found.pct == 0:
        # Nothing is strictly beyond it, or under one area in a hundred is.
        # What is true and worth saying is how many are level with it.
        every = found.level == found.others
        which = ("one_level" if found.others == 1 else "all_level") if every else "level"
        clause = STANDINGS[which].format(level=found.level, others=found.others)
        slots = {"compared": str(found.compared), "level": str(found.level)}
        return slots | {"standing": clause}, (str(found.level), str(found.others))
    slots = {
        "comparative": higher if found.higher else lower,
        "pct": str(found.pct),
        "compared": str(found.compared),
    }
    numbers = [percent(slots["pct"]), slots["compared"]]
    if found.level:
        slots["level"] = str(found.level)
        numbers.append(slots["level"])
    clause = STANDINGS["beyond_and_level" if found.level else "beyond"].format(
        **slots, other="other" if found.level == 1 else "others"
    )
    return slots | {"standing": clause}, tuple(numbers)


class _Builder:
    """Builds the facts of one area. Holds what every fact of that area shares."""

    def __init__(self, release: Release, area: Neighbourhood) -> None:
        self.release = release
        self.area = area
        self.names = {s.source_id: s.name for s in release.manifest.sources}
        self.metrics = {m.feature_id: m for m in release.metrics}

    def standing(self, value: float, of: Callable[[str], float | None]) -> Standing:
        """Where this area's figure sits among the rankable areas that have one.

        The same areas a percentile is worked out over (section 2.4). `of`
        gives an area's figure, or `None` where it has none.
        """
        population = sorted(
            figure
            for area in self.release.neighbourhoods
            if area.rankable and (figure := of(area.area_id)) is not None
        )
        return standing(value, population, among=self.area.rankable)

    def _feature_value(self, feature_id: FeatureId) -> Callable[[str], float | None]:
        def of(area_id: str) -> float | None:
            row = self.release.feature(area_id, feature_id)
            return None if row is None else row.value

        return of

    def _tag_raw(self, tag_id: TagId) -> Callable[[str], float | None]:
        def of(area_id: str) -> float | None:
            row = self.release.tag(area_id, tag_id)
            return None if row is None or row.score is None else row.raw

        return of

    def fact(
        self,
        kind: FactKind,
        key: str,
        label: str,
        template: TemplateId,
        slots: dict[str, str],
        source_ids: tuple[str, ...],
        as_of: str,
        numbers: tuple[str, ...] = (),
        names: tuple[str, ...] = (),
    ) -> Fact:
        unknown = [s for s in source_ids if s not in self.names]
        if unknown:
            # Never invent a source. `parse_release` refuses such a release.
            raise ReleaseError(MANIFEST, "references_resolve")
        return Fact(
            fact_id=fact_id(self.area.area_id, kind, key),
            area_id=self.area.area_id,
            kind=kind,
            key=key,
            label=label,
            template=template,
            slots=slots,
            numbers=tuple(dict.fromkeys(numbers)),
            names=names,
            sources=tuple(
                FactSource(source_id=s, name=self.names[s]) for s in sorted(set(source_ids))
            ),
            as_of=as_of,
            synthetic=self.release.manifest.synthetic,
        )

    def from_origin(
        self,
        origin: Origin,
        kind: FactKind,
        key: str,
        label: str,
        template: TemplateId,
        slots: dict[str, str],
        numbers: tuple[str, ...] = (),
        names: tuple[str, ...] = (),
    ) -> Fact:
        return self.fact(
            kind, key, label, template, slots, origin.source_ids, origin.as_of, numbers, names
        )

    def area_fact(self) -> Fact:
        return self.from_origin(
            self.release.origin(Part.NEIGHBOURHOODS),
            FactKind.AREA,
            "name",
            "Area",
            TemplateId.AREA,
            {"name": self.area.name, "borough": self.area.borough},
            names=(self.area.name, self.area.borough),
        )

    def features(self) -> Iterator[Fact]:
        for metric in self.release.metrics:
            row = self.release.feature(self.area.area_id, metric.feature_id)
            if row is None or row.value is None or row.percentile is None:
                continue
            feature = FEATURES[metric.feature_id]
            text, number = _value(row.value, feature.unit)
            found = self.standing(row.value, self._feature_value(metric.feature_id))
            slots, numbers = said(found, f"{feature.higher} than", f"{feature.lower} than")
            crime = feature.dimension is Dimension.CRIME
            yield self.fact(
                FactKind.FEATURE,
                metric.feature_id,
                feature.label,
                TemplateId.FEATURE_CRIME if crime else TemplateId.FEATURE,
                {"label": feature.label, "value": text} | slots,
                metric.source_ids,
                metric.vintage,
                numbers=(number, *numbers),
            )

    def _tag_sources(self, features: tuple[FeatureId, ...]) -> tuple[str, ...]:
        """The sources of the features in a formula that had a value for this area."""
        found: list[str] = []
        for feature_id in features:
            row = self.release.feature(self.area.area_id, feature_id)
            metric = self.metrics.get(feature_id)
            if metric is not None and row is not None and row.value is not None:
                found.extend(metric.source_ids)
        return tuple(found)

    def tags(self) -> Iterator[Fact]:
        for tag in TAGS.values():
            row = self.release.tag(self.area.area_id, tag.tag_id)
            if row is None or row.score is None or row.raw is None:
                continue
            sources = self._tag_sources(tuple(term.feature_id for term in tag.terms))
            if not sources:
                raise ReleaseError(TAGS_FILE, "sources_are_stated")
            slots, numbers = said(
                self.standing(row.raw, self._tag_raw(tag.tag_id)), TAG_HIGHER, TAG_LOWER
            )
            yield self.fact(
                FactKind.TAG,
                tag.tag_id,
                tag.label,
                TemplateId.TAG,
                {"label": tag.label} | slots,
                sources,
                # A tag is worked out when the release is built, so that is its date.
                self.release.manifest.built_at[:10],
                numbers=numbers,
            )

    def costs(self) -> Iterator[Fact]:
        for tenure in Tenure:
            for segment in segments_for(tenure):
                row = self.release.cost(self.area.area_id, tenure, segment)
                if row is not None:
                    yield self._cost(row)

    def _cost(self, row: CostEstimate) -> Fact:
        year, number = row.as_of.split("-")[:2]
        rent = row.tenure is Tenure.RENT
        return self.fact(
            FactKind.COST,
            cost_key(row.tenure, row.segment),
            COST_LABELS[row.tenure],
            TemplateId.COST_RENT if rent else TemplateId.COST_BUY,
            {
                "segment": SEGMENT_LABELS[row.segment],
                "lower": money(row.lower_quartile),
                "median": money(row.median),
                "upper": money(row.upper_quartile),
                "as_of": month(row.as_of),
                "confidence": row.confidence,
            },
            row.source_ids,
            row.as_of,
            numbers=(
                pounds(row.lower_quartile),
                pounds(row.median),
                pounds(row.upper_quartile),
                year,
                number,
                str(int(number)),
            ),
        )

    def budget_fit(self, spec: PreferenceSpec) -> Iterator[Fact]:
        amount = spec.budget.amount
        row = self.release.cost(self.area.area_id, spec.tenure, spec.budget.segment)
        if amount is None or row is None:
            return
        margin = amount - row.upper_quartile
        yield self.fact(
            FactKind.BUDGET_FIT,
            cost_key(spec.tenure, spec.budget.segment),
            "Budget",
            TemplateId.BUDGET_UNDER if margin >= 0 else TemplateId.BUDGET_OVER,
            {
                "margin": money(abs(margin)),
                "amount": money(amount),
                "upper": money(row.upper_quartile),
            },
            row.source_ids,
            row.as_of,
            numbers=(pounds(amount), pounds(row.upper_quartile), pounds(abs(margin))),
        )

    def times(self, commute: Commute) -> tuple[Travel, Travel]:
        """The typical time and the just-missed time. By bike and on foot they are one time."""
        place = self.release.place(commute.place_id)
        destination = place.destination_id if place else ""
        area_id = self.area.area_id
        return (
            self.release.travel(area_id, destination, commute.mode, PtBasis.TYPICAL),
            self.release.travel(area_id, destination, commute.mode, PtBasis.JUST_MISSED),
        )

    def travel(self, spec: PreferenceSpec) -> Iterator[Fact]:
        for commute in spec.commutes:
            typical, missed = self.times(commute)
            scored = missed if scored_on_just_missed(commute, spec) else typical
            place = self.release.place(commute.place_id)
            if scored.status is TravelStatus.MISSING or place is None:
                continue
            slots = {"mode": MODE_LABELS[commute.mode], "place": place.name}
            numbers = [str(t.minutes) for t in (typical, missed) if t.minutes is not None]
            if scored.minutes is None:
                template = TemplateId.TRAVEL_BEYOND
                cutoff = str(self.release.cutoff(commute.mode))
                slots["cutoff"] = cutoff
                numbers.append(cutoff)
            elif (
                commute.mode is Mode.PT
                and typical.minutes is not None
                and missed.minutes is not None
            ):
                template = TemplateId.TRAVEL_PT
                slots |= {"typical": str(typical.minutes), "missed": str(missed.minutes)}
            else:
                template = TemplateId.TRAVEL_OTHER
                slots["minutes"] = str(scored.minutes)
            yield self.from_origin(
                self.release.origin(Part.TRAVEL),
                FactKind.TRAVEL,
                travel_key(commute),
                "Journey",
                template,
                slots,
                numbers=tuple(numbers),
                names=(place.name,),
            )

    def stations(self) -> Iterator[Fact]:
        for row in self.release.stations(self.area.area_id):
            walk = str(row.walk_minutes)
            yield self.from_origin(
                self.release.origin(Part.STATIONS),
                FactKind.STATION,
                row.station_id,
                "Station",
                TemplateId.STATION if row.nearest else TemplateId.STATION_NEARBY,
                {"name": row.name, "walk": walk, "lines": ", ".join(row.lines)},
                numbers=(walk,),
                names=(row.name, *row.lines),
            )

    def missing(self, spec: PreferenceSpec) -> Iterator[Fact]:
        for component, label in self._missing_components(spec):
            yield self.from_origin(
                self.release.origin(Part.NEIGHBOURHOODS),
                FactKind.MISSING,
                component,
                label,
                TemplateId.MISSING,
                {"label": label, "name": self.area.name},
                names=(self.area.name,),
            )

    def _missing_components(self, spec: PreferenceSpec) -> Iterator[tuple[str, str]]:
        area_id = self.area.area_id
        if spec.commute_requested and any(
            (missed if scored_on_just_missed(commute, spec) else typical).status
            is TravelStatus.MISSING
            for commute in spec.commutes
            for typical, missed in [self.times(commute)]
        ):
            yield COMMUTE, MISSING_LABELS[COMMUTE]
        if spec.budget_requested and (
            self.release.cost(area_id, spec.tenure, spec.budget.segment) is None
        ):
            yield BUDGET, MISSING_LABELS[BUDGET]
        for weight in spec.active_weights:
            row = self.release.feature(area_id, weight.feature_id)
            if row is None or row.percentile is None:
                yield component_for_feature(weight.feature_id), FEATURES[weight.feature_id].label
        for tag in spec.active_tags:
            score = self.release.tag(area_id, tag.tag_id)
            if score is None or score.score is None:
                yield component_for_tag(tag.tag_id), TAGS[tag.tag_id].label


def scored_on_just_missed(commute: Commute, spec: PreferenceSpec) -> bool:
    """Whether this commute is scored on the time of someone who just missed a service."""
    return commute.mode is Mode.PT and spec.pt_basis is PtBasis.JUST_MISSED


def facts_for(release: Release, area_id: str, spec: PreferenceSpec | None) -> tuple[Fact, ...]:
    """Every fact about one area, ordered by `fact_id`. None for an area the release lacks.

    Without a spec it returns what a profile page needs. With one it adds the
    `travel`, `budget_fit` and `missing` facts for that spec.
    """
    area = release.neighbourhood(area_id)
    if area is None:
        return ()
    if spec is not None:
        problems = check_spec(spec, release)
        if problems:
            raise SpecError(problems)
    build = _Builder(release, area)
    facts = [build.area_fact(), *build.features(), *build.tags(), *build.costs()]
    facts += build.stations()
    if spec is not None:
        facts += [*build.travel(spec), *build.budget_fit(spec), *build.missing(spec)]
    return tuple(sorted(facts, key=lambda fact: fact.fact_id))
