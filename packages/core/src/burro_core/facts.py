"""Facts: each one thing Burro may say about one area, with where it came from and when.

Every number and proper noun the product shows about a place must trace to a
fact. Numbers are formatted once, here, so a template, a model and the verifier
all see the same spelling. A missing value never produces a fact that carries
a number.

A comparison must be literally true of the release. Areas are scored on a
mid-rank percentile, which counts half of the areas that tie as beaten. A
sentence may not: it states the share of areas strictly beyond this one,
rounded down, names how many areas were compared, and says how many are level.

A figure is said from both sides, each as true as the other: from the side
that counts as better for the thing, and from the side that counts as worse.
A reason is filled from the first and a trade-off from the second, so that a
reason never reads as a drawback. A vibe is said as a band, one of five, and
no percentage is ever printed for one.
"""

from bisect import bisect_left, bisect_right
from collections.abc import Callable, Iterator, Mapping
from typing import NamedTuple

from pydantic import Field

from burro_core._record import Record
from burro_core.catalogue import (
    BANDS,
    FAMILIES,
    FEATURES,
    JUDGEMENT,
    MADE_FROM,
    TAGS,
    Tag,
    band_of,
    default_direction,
)
from burro_core.ids import (
    BUDGET,
    COMMUTE,
    Dimension,
    Direction,
    FactKind,
    FeatureId,
    Mode,
    Part,
    PtBasis,
    Segment,
    TagShape,
    TemplateId,
    Tenure,
    TravelStatus,
    component_for_feature,
    component_for_tag,
    segments_for,
)
from burro_core.likeness import Likeness, parts_of, similar
from burro_core.release import (
    MANIFEST,
    TAGS_FILE,
    CostEstimate,
    Neighbourhood,
    Origin,
    Release,
    ReleaseError,
    TagValue,
    Travel,
)
from burro_core.spec import Commute, PreferenceSpec, SpecError, check_spec


class FactSource(Record):
    source_id: str
    name: str
    # Who published it, as the manifest says. A page names the publisher beside
    # the dataset, and has no need to look one up.
    publisher: str


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
# What a sentence calls the homes of a kind, where it says a figure of all of them that
# were sold. A publisher's median is of every size of home of the kind, so the sentence
# says "of all sizes" beside it: no source gives a price by bedrooms.
HOMES_LABELS: Mapping[Segment, str] = {
    Segment.FLAT: "flats",
    Segment.TERRACED: "terraced houses",
    Segment.SEMI_DETACHED: "semi-detached houses",
    Segment.DETACHED: "detached houses",
}
# The period of a cost that is a median of the sales of twelve months.
YEAR_ENDING = "the year ending {month}"
COST_LABELS: Mapping[Tenure, str] = {Tenure.RENT: "Rent", Tenure.BUY: "Price"}
# What the `missing` sentence calls a component that has no figure.
MISSING_LABELS: Mapping[str, str] = {BUDGET: "cost"}
# How the ends of a one-way vibe are said, which has no names for them.
LEAST, MOST = "least", "most"
# A mixed area is said as a range once the middle half of its homes span this many bands.
RANGE_FROM_BANDS = 3
# What a band says of itself where it rests on part of its recipe. A part
# with no figure is dropped and the rest reweighted, and the sentence says
# so: how many parts had a figure, and what they carry of the recipe's 100.
PARTLY = "Worked out from {known} of its {parts} parts, {share} of 100 by weight."
WHOLE = 100
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
    # Nothing is beyond it on this side and nothing is level with it. "The
    # same as 0 others" would be true and would say nothing.
    "none": "{comparative} none of the {others} other areas compared in this release",
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


def journey_key(commute: Commute) -> str:
    """The key of the `missing` fact of one journey that has no time."""
    return f"{COMMUTE}.{travel_key(commute)}"


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
        metres = round(value / 10) * 10
        # Printed with its separator, as money is. The number is held without one.
        return f"{metres:,} m", str(metres)
    if unit == "%":
        number = str(round(value))
        return f"{number}%", percent(number)
    if unit == "£":
        # Printed with its separator, as a cost is. The number is held as money.
        whole = round(value)
        return f"£{money(whole)}", pounds(whole)
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

    def share(self, beyond: int) -> int:
        """The share of the areas compared that `beyond` of them are, rounded down.

        Rounded down and never to the nearest, so that "closer than 40% of
        areas" is true when 40.9% of them are further away.
        """
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


def _side(found: Standing, beyond: int, comparative: str) -> tuple[dict[str, str], list[str]]:
    """What is said of a standing from one side: the clause, its parts, and the numbers in it.

    `beyond` is how many areas are strictly beyond this one on that side, and
    `comparative` the word for being on it: "closer than".
    """
    if found.others == 0:
        return {"standing": STANDINGS["alone"]}, []
    pct = found.share(beyond)
    if pct == 0:
        # Nothing is strictly beyond it, or under one area in a hundred is.
        # What is true and worth saying is how many are level with it.
        if beyond == 0 and found.level == 0:
            clause = STANDINGS["none"].format(comparative=comparative, others=found.others)
            return {"standing": clause, "comparative": comparative}, [str(found.others)]
        every = found.level == found.others
        which = ("one_level" if found.others == 1 else "all_level") if every else "level"
        clause = STANDINGS[which].format(level=found.level, others=found.others)
        return {"standing": clause}, [str(found.level), str(found.others)]
    slots = {"comparative": comparative, "pct": str(pct)}
    clause = STANDINGS["beyond_and_level" if found.level else "beyond"].format(
        **slots,
        compared=found.compared,
        level=found.level,
        other="other" if found.level == 1 else "others",
    )
    return slots | {"standing": clause}, [percent(slots["pct"]), str(found.compared)]


def said(
    found: Standing, higher: str, lower: str, better: Direction
) -> tuple[dict[str, str], tuple[str, ...]]:
    """The slots that state a standing from both sides, and the numbers in them.

    `better` is the side that counts as better for the thing: `more` where a
    higher figure does, `less` where a lower one does. `standing`,
    `comparative` and `pct` are said from that side, of the areas that do
    strictly worse. `standing_worse`, `comparative_worse` and `pct_worse` are
    said from the other, of the areas that do strictly better. Each is the
    whole clause and its parts, for a client that lays them out for itself.
    """
    up, down = (found.below, higher), (found.above, lower)
    good, bad = (up, down) if better is Direction.MORE else (down, up)
    from_better, numbers = _side(found, *good)
    from_worse, more = _side(found, *bad)
    slots = from_better | {f"{name}_worse": text for name, text in from_worse.items()}
    if found.others:
        slots["compared"] = str(found.compared)
    if found.level and found.others:
        slots["level"] = str(found.level)
        numbers.append(slots["level"])
    return slots, tuple(dict.fromkeys([*numbers, *more]))


def _span(vintages: list[str]) -> str:
    """The span of some periods: "2021 to 2026". A period is a year, a month, or two with "to"."""
    ends = sorted({end.strip() for vintage in vintages for end in vintage.split(" to ")})
    return ends[0] if len(ends) == 1 else f"{ends[0]} to {ends[-1]}"


def _digits(text: str) -> list[str]:
    """Each run of digits in a period, as the verifier reads them: "2024-10" is 2024 and 10."""
    runs = "".join(c if c.isdigit() else " " for c in text).split()
    return [number for run in runs for number in dict.fromkeys((run, str(int(run))))]


class _Builder:
    """Builds the facts of one area. Holds what every fact of that area shares."""

    def __init__(self, release: Release, area: Neighbourhood) -> None:
        self.release = release
        self.area = area
        self.names = {s.source_id: s.name for s in release.manifest.sources}
        self.publishers = {s.source_id: s.publisher for s in release.manifest.sources}
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

    def _band(self, feature_id: FeatureId) -> int | None:
        """The band of this area's figure, among the rankable areas that have one."""
        areas = self.release.neighbourhoods
        of = self._feature_value(feature_id)
        bands = band_of([of(area.area_id) for area in areas], [area.rankable for area in areas])
        mine = self.area.area_id
        return next(band for area, band in zip(areas, bands, strict=True) if area.area_id == mine)

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
                FactSource(source_id=s, name=self.names[s], publisher=self.publishers[s])
                for s in sorted(set(source_ids))
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
        if not origin.source_ids or origin.as_of is None:
            # A part that states no source holds nothing to make a fact of. `parse_release`
            # refuses a release where it does.
            raise ReleaseError(MANIFEST, "sources_are_stated")
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

    def features(self, spec: PreferenceSpec | None) -> Iterator[Fact]:
        # The side that counts as better is the polarity's, and the spec's
        # where the polarity leaves a person to choose. With no spec, more.
        chosen = {w.feature_id: w.direction for w in spec.active_weights} if spec else {}
        for metric in self.release.metrics:
            row = self.release.feature(self.area.area_id, metric.feature_id)
            if row is None or row.value is None or row.percentile is None:
                continue
            feature = FEATURES[metric.feature_id]
            text, number = _value(row.value, feature.unit)
            found = self.standing(row.value, self._feature_value(metric.feature_id))
            better = chosen.get(metric.feature_id, default_direction(metric.feature_id))
            slots, numbers = said(found, f"{feature.higher} than", f"{feature.lower} than", better)
            band = self._band(metric.feature_id)
            crime = feature.dimension is Dimension.CRIME
            yield self.fact(
                FactKind.FEATURE,
                metric.feature_id,
                feature.label,
                TemplateId.FEATURE_CRIME if crime else TemplateId.FEATURE,
                {"label": feature.label, "value": text, "band": str(band)} | slots,
                metric.source_ids,
                metric.vintage,
                # No sentence prints the band of a figure, so it is no number of the fact.
                numbers=(number, *numbers),
            )

    def _valued(self, tag: Tag) -> list[FeatureId]:
        """The parts of a recipe that have a figure for this area, in the order of the recipe."""
        found: list[FeatureId] = []
        for term in tag.terms:
            row = self.release.feature(self.area.area_id, term.feature_id)
            if term.feature_id in self.metrics and row is not None and row.value is not None:
                found.append(term.feature_id)
        return found

    def tags(self) -> Iterator[Fact]:
        """One fact for each vibe of the release, whether or not the area can be placed on it."""
        for tag in self.release.vibes:
            row = self.release.tag(self.area.area_id, tag.tag_id)
            if row is not None:
                yield self._tag(tag, row)

    def _tag(self, tag: Tag, row: TagValue) -> Fact:
        valued = self._valued(tag)
        known, parts = str(len(valued)), str(len(tag.terms))
        carried = sum(term.hundredths for term in tag.terms if term.feature_id in valued)
        share = str(carried)
        if row.band is None or row.spread_low is None or row.spread_high is None:
            # It holds no figure about the place: only how much of the recipe is known.
            slots = {"label": tag.label, "name": self.area.name, "known": known, "parts": parts}
            if not valued:
                # With no part to cite, it cites where the area itself came from.
                return self.from_origin(
                    self.release.origin(Part.NEIGHBOURHOODS),
                    FactKind.TAG,
                    tag.tag_id,
                    tag.label,
                    TemplateId.VIBE_UNKNOWN,
                    slots,
                    numbers=(known, parts),
                    names=(self.area.name,),
                )
            return self.fact(
                FactKind.TAG,
                tag.tag_id,
                tag.label,
                TemplateId.VIBE_UNKNOWN,
                slots,
                tuple(s for f in valued for s in self.metrics[f].source_ids),
                _span([self.metrics[f].vintage for f in valued]),
                numbers=(known, parts),
                names=(self.area.name,),
            )
        if not valued:
            raise ReleaseError(TAGS_FILE, "sources_are_stated")
        compared = sum(
            1
            for area in self.release.neighbourhoods
            if area.rankable
            and (other := self.release.tag(area.area_id, tag.tag_id)) is not None
            and other.raw is not None
        )
        scale = tag.shape is TagShape.SCALE
        # The date of a vibe is the span of its parts, never the day the release was built.
        span = _span([self.metrics[f].vintage for f in valued])
        slots = {
            "label": tag.label,
            "band": str(row.band),
            "low_end": (tag.low_end if scale else None) or LEAST,
            "high_end": (tag.high_end if scale else None) or MOST,
            "compared": str(compared),
            "span": span,
            "spread_low": str(row.spread_low),
            "spread_high": str(row.spread_high),
            "known": known,
            "parts": parts,
            # What the band rests on, of the 100 the recipe adds up to, and
            # the clause that says so where it is not the whole of it.
            "share": share,
            "partly": ""
            if carried == WHOLE
            else PARTLY.format(known=known, parts=parts, share=share),
            "judgement": JUDGEMENT,
            "made_from": MADE_FROM,
        }
        varies = row.spread_high - row.spread_low + 1 >= RANGE_FROM_BANDS
        return self.fact(
            FactKind.TAG,
            tag.tag_id,
            tag.label,
            TemplateId.VIBE_RANGE if varies else TemplateId.VIBE,
            slots,
            tuple(s for f in valued for s in self.metrics[f].source_ids),
            span,
            numbers=(
                slots["band"],
                str(BANDS),
                slots["compared"],
                slots["spread_low"],
                slots["spread_high"],
                known,
                parts,
                share,
                str(WHOLE),
                *_digits(span),
            ),
        )

    def likeness(self) -> Iterator[Fact]:
        """One fact for each of the areas most like this one."""
        for found in similar(self.release, self.area.area_id):
            yield self._likeness(found)

    def _likeness(self, found: Likeness) -> Fact:
        other = self.release.neighbourhood(found.area_id)
        assert other is not None
        compared = [
            self.metrics[part.feature_id]
            for part in parts_of(self.release)
            if all(
                (row := self.release.feature(area_id, part.feature_id)) is not None
                and row.value is not None
                for area_id in (self.area.area_id, other.area_id)
            )
        ]
        slots = {
            "name": self.area.name,
            "other": other.name,
            "same": str(found.same),
            "measures": str(found.measures),
        }
        if found.family is not None:
            slots["family"] = FAMILIES[found.family]
        return self.fact(
            FactKind.LIKENESS,
            other.area_id,
            "Likeness",
            TemplateId.LIKENESS if found.family is not None else TemplateId.LIKENESS_SAME,
            slots,
            tuple(s for metric in compared for s in metric.source_ids),
            _span([metric.vintage for metric in compared]),
            numbers=(slots["same"], slots["measures"]),
            names=(self.area.name, other.name),
        )

    def costs(self) -> Iterator[Fact]:
        for tenure in Tenure:
            for segment in segments_for(tenure):
                row = self.release.cost(self.area.area_id, tenure, segment)
                if row is not None:
                    yield self._cost(row)

    def _median(self, row: CostEstimate) -> Fact:
        """The fact of a price that is one number: a publisher's median, with no range."""
        year, number = row.as_of.split("-")[:2]
        return self.fact(
            FactKind.COST,
            cost_key(row.tenure, row.segment),
            COST_LABELS[row.tenure],
            TemplateId.COST_BUY_MEDIAN,
            {
                "segment": SEGMENT_LABELS[row.segment],
                "homes": HOMES_LABELS[row.segment],
                "median": money(row.median),
                "as_of": month(row.as_of),
                # The sales are those of twelve months, and the row gives the last of them.
                "period": YEAR_ENDING.format(month=month(row.as_of)),
                "confidence": row.confidence,
            },
            row.source_ids,
            row.as_of,
            numbers=(pounds(row.median), year, number, str(int(number))),
        )

    def _cost(self, row: CostEstimate) -> Fact:
        if row.lower_quartile is None or row.upper_quartile is None:
            return self._median(row)
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
        # What the budget is held against, as the ranking holds it: the upper quartile of
        # a range, and the median of a cost that has none.
        if row.upper_quartile is None:
            held, slot, slots = row.median, "median", {"homes": HOMES_LABELS[row.segment]}
            under, over = TemplateId.BUDGET_UNDER_MEDIAN, TemplateId.BUDGET_OVER_MEDIAN
        else:
            held, slot, slots = row.upper_quartile, "upper", {}
            under, over = TemplateId.BUDGET_UNDER, TemplateId.BUDGET_OVER
        margin = amount - held
        yield self.fact(
            FactKind.BUDGET_FIT,
            cost_key(spec.tenure, spec.budget.segment),
            "Budget",
            under if margin >= 0 else over,
            {"margin": money(abs(margin)), "amount": money(amount), slot: money(held)} | slots,
            row.source_ids,
            row.as_of,
            numbers=(pounds(amount), pounds(held), pounds(abs(margin))),
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
            # The limit the person set, so that a journey over it can say by how much.
            limit = str(commute.max_minutes)
            slots = {"mode": MODE_LABELS[commute.mode], "place": place.name, "limit": limit}
            numbers = [str(t.minutes) for t in (typical, missed) if t.minutes is not None]
            numbers.append(limit)
            over = scored.minutes is not None and scored.minutes > commute.max_minutes
            if scored.minutes is not None:
                margin = abs(scored.minutes - commute.max_minutes)
                slots |= {"margin": str(margin), "margin_unit": _minutes(margin)}
                numbers.append(slots["margin"])
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
                template = TemplateId.TRAVEL_PT_OVER if over else TemplateId.TRAVEL_PT
                slots |= {"typical": str(typical.minutes), "missed": str(missed.minutes)}
            else:
                template = TemplateId.TRAVEL_OTHER_OVER if over else TemplateId.TRAVEL_OTHER
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
        yield from self._missing_journeys(spec)
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

    def _missing_journeys(self, spec: PreferenceSpec) -> Iterator[Fact]:
        """One fact for each journey that has no time, which names the journey.

        "There is no journey time figure for this area" named none, and read
        as if the area had no journey at all, above a table that gave one.
        """
        if not spec.commute_requested:
            return
        for commute in spec.commutes:
            typical, missed = self.times(commute)
            scored = missed if scored_on_just_missed(commute, spec) else typical
            place = self.release.place(commute.place_id)
            if scored.status is not TravelStatus.MISSING or place is None:
                continue
            yield self.from_origin(
                self.release.origin(Part.TRAVEL),
                FactKind.MISSING,
                journey_key(commute),
                "Journey",
                TemplateId.MISSING_JOURNEY,
                {"name": self.area.name, "place": place.name},
                names=(self.area.name, place.name),
            )

    def _missing_components(self, spec: PreferenceSpec) -> Iterator[tuple[str, str]]:
        area_id = self.area.area_id
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


def _minutes(count: int) -> str:
    return "minute" if count == 1 else "minutes"


def scored_on_just_missed(commute: Commute, spec: PreferenceSpec) -> bool:
    """Whether this commute is scored on the time of someone who just missed a service."""
    return commute.mode is Mode.PT and spec.pt_basis is PtBasis.JUST_MISSED


def facts_for(release: Release, area_id: str, spec: PreferenceSpec | None) -> tuple[Fact, ...]:
    """Every fact about one area, ordered by `fact_id`. None for an area the release lacks.

    Without a spec it returns what a profile page needs, the areas most like
    this one among it. With one it returns what a ranking needs: the
    `travel`, `budget_fit` and `missing` facts for that spec, and each
    figure said from the side that counts as better in that spec.
    """
    area = release.neighbourhood(area_id)
    if area is None:
        return ()
    if spec is not None:
        problems = check_spec(spec, release)
        if problems:
            raise SpecError(problems)
    build = _Builder(release, area)
    facts = [build.area_fact(), *build.features(spec), *build.tags(), *build.costs()]
    facts += build.stations()
    if spec is None:
        facts += build.likeness()
    else:
        facts += [*build.travel(spec), *build.budget_fit(spec), *build.missing(spec)]
    return tuple(sorted(facts, key=lambda fact: fact.fact_id))
