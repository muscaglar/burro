import dataclasses
from functools import cache

import pytest
from burro_core.catalogue import FEATURES, JUDGEMENT, NEVER_A_TRADE_OFF
from burro_core.explain import (
    REASON_MIN_UTILITY,
    TRADE_OFF_MAX_UTILITY,
    Ask,
    ExplainedSentence,
    Explainer,
    ExplainInput,
    Explanation,
    TemplateExplainer,
    explain,
    render,
)
from burro_core.facts import Fact, facts_for
from burro_core.ids import (
    Direction,
    FeatureId,
    Mode,
    Provenance,
    SentenceOrigin,
    SentenceRole,
    Strictness,
    TagId,
    Tenure,
    Toward,
)
from burro_core.rank import Contribution, RankedArea, RankResult, rank
from burro_core.reducer import given_way_spec
from burro_core.release import InMemoryRelease
from burro_core.spec import Commute, FeatureWeight, PreferenceSpec, TagWeight, default_spec
from burro_core.verify import Sentence
from pydantic import BaseModel

from .support import (
    area_id,
    build_worked_release,
    build_worked_spec,
    draws,
    feature_value,
    fixture_release,
    random_spec,
    small_release,
    travel_table,
)

ALDERWICK, BRACKENHYTHE, CINDERMOOR, DULCIMER_GREEN = (area_id(n) for n in range(1, 5))
# The figure at or under which a walk, a time or a distance is never a trade-off.
FLOORS = {feature_id.value: figure for feature_id, figure in NEVER_A_TRADE_OFF.items()}


class Planting(TemplateExplainer):
    """An explainer that writes what it likes about each fact it is asked about.

    `explain` takes the template explainer and nothing else, so a test that
    plants a sentence does it from a subclass of it (contract, section 11).
    """

    def __init__(self, write: str) -> None:
        self.write = write
        self.seen: list[ExplainInput] = []

    def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
        self.seen.append(area)
        facts = {fact.fact_id: fact for fact in area.facts}
        return tuple(self.sentence(facts[ask.fact_id], ask) for ask in area.asks)

    def sentence(self, fact: Fact, ask: Ask) -> Sentence:
        text = self.write.format(template=render(fact).text, **fact.slots)
        return Sentence(text=text, fact_ids=(fact.fact_id,), origin=SentenceOrigin.MODEL)


def worked(
    explainer: Explainer | None = None, areas: tuple[str, ...] = (ALDERWICK,)
) -> tuple[Explanation, ...]:
    spec = build_worked_spec()
    release = build_worked_release()
    return explain(rank(spec, release), release, spec, areas, explainer or TemplateExplainer())


def sentences(explanation: Explanation) -> list[ExplainedSentence]:
    trade_off = [explanation.trade_off] if explanation.trade_off else []
    return [explanation.orientation, *explanation.reasons, *trade_off, *explanation.missing]


def test_the_worked_example_is_explained_as_the_contract_says():
    (alderwick,) = worked()
    assert alderwick.area_id == ALDERWICK
    assert alderwick.orientation.text == "Alderwick is in Quillhaven."
    # Reasons: budget, commute and park proximity. It does nothing badly, so it
    # has no trade-off: being leafy, which it does well, was once given as one.
    assert [s.fact_ids for s in alderwick.reasons] == [
        (f"{ALDERWICK}/budget_fit/rent.bed_1",),
        (f"{ALDERWICK}/travel/syn-p0001.pt",),
        (f"{ALDERWICK}/feature/park_proximity",),
    ]
    assert alderwick.trade_off is None
    assert alderwick.missing == ()
    assert [s.text for s in alderwick.reasons] == [
        "The upper end is £50 under your budget of £1,800.",
        "By public transport to Pellam Cross: about 32 minutes on a typical weekday "
        "morning, 37 if you just miss a service.",
        # Two of the four areas are further from a park, and none is level.
        "Straight-line distance to the nearest marked way into a park of 2 ha or more: "
        "280 m, closer than 50% of the 4 areas compared in this release.",
    ]
    assert not any(s.replaced for s in sentences(alderwick))
    assert {s.origin for s in sentences(alderwick)} == {SentenceOrigin.TEMPLATE}


def test_a_reason_is_something_the_area_does_well():
    (cindermoor,) = worked(areas=(CINDERMOOR,))
    result = rank(build_worked_spec(), build_worked_release())
    found = {c.component: c for c in result.ranked[1].contributions}
    # Its journey to place 1 is 44 minutes against a cap of 40, which is worth
    # 0.40. It adds more to the score than being leafy does, and it is still
    # no reason to live there.
    assert found["commute"].utility == 0.4
    assert found["commute"].contribution > found["tag:leafy"].contribution
    assert [s.fact_ids[0].split("/", 1)[1] for s in cindermoor.reasons] == [
        "budget_fit/rent.bed_1",
        "feature/park_proximity",
        "tag/leafy",
    ]
    # It is what the area gives up.
    assert cindermoor.trade_off is not None
    assert cindermoor.trade_off.fact_ids == (f"{CINDERMOOR}/travel/syn-p0001.pt",)
    assert REASON_MIN_UTILITY == 0.5


def test_being_over_budget_is_never_given_as_a_reason():
    # Brackenhythe is £150 over a budget of £1,800, which is worth 0.6667. It
    # was given as a reason to live there: "The upper end is £150 over your budget".
    (brackenhythe,) = worked(areas=(BRACKENHYTHE,))
    result = rank(build_worked_spec(), build_worked_release())
    found = {c.component: c for c in result.ranked[2].contributions}
    assert result.ranked[2].area_id == BRACKENHYTHE
    assert found["budget"].utility == 0.6667
    assert [s.fact_ids[0].split("/", 1)[1] for s in brackenhythe.reasons] == ["travel/syn-p0002.pt"]
    assert not any("over your budget" in s.text for s in brackenhythe.reasons)
    # It falls short of the budget the person set, so that is what it gives up.
    # Its walk to a park is worth 0.40, which is neither done well nor badly.
    assert brackenhythe.trade_off is not None
    assert brackenhythe.trade_off.fact_ids == (f"{BRACKENHYTHE}/budget_fit/rent.bed_1",)
    assert brackenhythe.trade_off.text == "The upper end is £150 over your budget of £1,800."
    # Within budget by a pound, or by nothing, it is a reason.
    for amount in (1950, 1951):
        spec = build_worked_spec().replace(
            budget=build_worked_spec().budget.replace(amount=amount), commutes=()
        )
        release = build_worked_release()
        (within,) = explain(
            rank(spec, release), release, spec, (BRACKENHYTHE,), TemplateExplainer()
        )
        assert within.reasons[0].fact_ids == (f"{BRACKENHYTHE}/budget_fit/rent.bed_1",)
        assert "under your budget" in within.reasons[0].text


def test_a_journey_over_its_cap_is_never_given_as_a_reason():
    # With the mean of two journeys scored, Cindermoor's 44 minutes against a
    # cap of 40 and 22 against 30 come to 0.5833, which is done well enough.
    # The sentence would state the 44 minutes, which is over the cap.
    spec = build_worked_spec().replace(commute_combine="mean")
    release = build_worked_release()
    result = rank(spec, release)
    area = next(a for a in result.ranked if a.area_id == CINDERMOOR)
    commute = next(c for c in area.contributions if c.component == "commute")
    assert commute.utility == 0.5833
    assert [(leg.minutes, leg.utility) for leg in area.legs] == [(44, 0.4), (22, 0.7667)]
    (cindermoor,) = explain(result, release, spec, (CINDERMOOR,), TemplateExplainer())
    assert not any("/travel/" in s.fact_ids[0] for s in cindermoor.reasons)
    assert not any("44 minutes" in s.text for s in cindermoor.reasons)
    # With every journey within its cap, the journey is a reason, the cap itself included.
    (alderwick,) = explain(result, release, spec, (ALDERWICK,), TemplateExplainer())
    assert any("/travel/" in s.fact_ids[0] for s in alderwick.reasons)
    at_the_cap = spec.replace(
        commutes=tuple(
            c.replace(max_minutes=32) if c.place_id == "syn-p0001" else c for c in spec.commutes
        )
    )
    ranked = rank(at_the_cap, release)
    (alderwick,) = explain(ranked, release, at_the_cap, (ALDERWICK,), TemplateExplainer())
    assert any("32 minutes" in s.text for s in alderwick.reasons)


class Borrowed:
    """An explainer of the right shape that is not the template explainer."""

    def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
        return TemplateExplainer().draft(area)


def test_explain_takes_the_template_explainer_and_no_other():
    spec = build_worked_spec()
    release = build_worked_release()
    result = rank(spec, release)
    second: Explainer = Borrowed()
    with pytest.raises(TypeError) as refused:
        explain(result, release, spec, (ALDERWICK,), second)
    # The message says where the decision is written down, and repeats nothing it was given.
    said = str(refused.value)
    assert "docs/design/contract.md" in said and "section 11" in said
    assert "TemplateExplainer" in said
    assert "Alderwick" not in said and ALDERWICK not in said
    # It is refused before anything is drafted, and whatever the areas asked for.
    with pytest.raises(TypeError):
        explain(result, release, spec, (), second)
    assert explain(result, release, spec, (ALDERWICK,), TemplateExplainer())


def test_an_area_that_does_nothing_well_is_given_no_reason():
    release = build_worked_release()
    spec = build_worked_spec().replace(
        commutes=(),
        budget=build_worked_spec().budget.replace(amount=1600),
        weights=tuple(w.replace(direction="less") for w in build_worked_spec().weights),
        tags=(),
    )
    # Brackenhythe: a quarter over budget is worth 0.125, and 640 m to a park 0.40.
    (found,) = explain(rank(spec, release), release, spec, (BRACKENHYTHE,), TemplateExplainer())
    assert found.reasons == ()
    assert found.trade_off is not None
    assert found.trade_off.fact_ids == (f"{BRACKENHYTHE}/budget_fit/rent.bed_1",)


def test_a_sentence_about_the_commute_cites_the_leg_that_drove_the_score():
    (brackenhythe,) = worked(areas=(BRACKENHYTHE,))
    # Place 2, at 28 minutes of a 30 minute cap, is the slower journey for Brackenhythe.
    commute = next(s for s in brackenhythe.reasons if "/travel/" in s.fact_ids[0])
    assert commute.fact_ids == (f"{BRACKENHYTHE}/travel/syn-p0002.pt",)
    assert "Foxholt Works" in commute.text
    assert "28 minutes" in commute.text


def test_a_dropped_component_gets_one_sentence_that_says_it_was_left_out():
    (brackenhythe,) = worked(areas=(BRACKENHYTHE,))
    assert [s.text for s in brackenhythe.missing] == [
        "There is no Share of residents exposed to 55 dB or more of transport noise figure for "
        "Brackenhythe in this release, so it was left out of the score."
    ]
    assert brackenhythe.missing[0].fact_ids == (f"{BRACKENHYTHE}/missing/feature:noise_exposure",)


def test_areas_are_explained_in_the_order_asked_and_only_if_they_were_ranked():
    found = worked(areas=(CINDERMOOR, DULCIMER_GREEN, ALDERWICK, "syn-n0099"))
    # Dulcimer Green was filtered, so it has nothing to explain.
    assert [e.area_id for e in found] == [CINDERMOOR, ALDERWICK]


PLANTED = [
    ("{template} It is close to Victoria Park.", "an invented venue"),
    ("{template} The Dog and Duck is round the corner.", "an invented pub"),
    ("{template} That is 12% better than last year.", "an invented number"),
    ("{template} It is a safe area.", "a verdict on safety"),
    ("{template} It has several parks.", "a vague quantity"),
    ("Alderwick is the best of the three.", "a number as a word"),
    ("London at its finest.", "a city the release never names"),
    (
        "it is about thirty minutes from the office, and rents have fallen by forty percent.",
        "a number over twenty as a word",
    ),
    ("{template} a million people visit each year.", "a million"),
    ("{template} there are zero pubs here.", "zero"),
    ("{template} it is an hour from the coast.", "a length of time with no number"),
    ("{template} a quarter of homes are flats.", "a fraction with no number"),
    ("the station is \uff15 minutes away and the park \u00bd a mile.", "digits that are not ASCII"),
    ("{template} the shops are \u0663 minutes away.", "a digit in another script"),
    ("{template} it scores \u2467 out of ten.", "a number in a circle"),
    ("rent is about \u00a3280 a month.", "a distance said as money"),
    ("it is closer than 32% of areas.", "a journey time said as a share"),
]


class CitesEverything(Planting):
    """Writes what it likes and cites the fact asked about first, then every other fact."""

    def sentence(self, fact: Fact, ask: Ask) -> Sentence:
        drafted = super().sentence(fact, ask)
        others = tuple(f.fact_id for f in self.seen[-1].facts if f.fact_id != fact.fact_id)
        return drafted.model_copy(update={"fact_ids": (fact.fact_id, *others)})


@pytest.mark.parametrize("explainer", [Planting, CitesEverything])
@pytest.mark.parametrize(("write", "what"), PLANTED, ids=[what for _, what in PLANTED])
def test_invented_venue_or_changed_number_is_replaced_by_a_template(
    write: str, what: str, explainer: type[Planting]
):
    (planted,) = worked(explainer(write))
    (honest,) = worked()
    found = sentences(planted)
    assert all(s.replaced for s in found), what
    # What is shown is exactly what the templates would have said.
    assert [s.text for s in found] == [s.text for s in sentences(honest)]
    assert {s.origin for s in found} == {SentenceOrigin.TEMPLATE}
    assert "Victoria" not in planted.model_dump_json()


OF_ANOTHER_FACT = [
    ("the nearest park is 32 minutes away.", "travel"),  # the minutes of the journey
    ("the nearest park is 1,750 m away.", "budget_fit"),  # the upper quartile of the rent
    ("it is 280 minutes to the office.", "feature"),  # the metres to the park
]


@pytest.mark.parametrize(("text", "holds"), OF_ANOTHER_FACT, ids=[t for t, _ in OF_ANOTHER_FACT])
def test_a_number_is_supported_only_by_the_fact_a_sentence_was_asked_about(text: str, holds: str):
    # Citing every fact of the area used to allow any of their numbers anywhere.
    (planted,) = worked(CitesEverything(text))
    assert all(s.replaced for s in sentences(planted))
    # Asked about the fact that holds the number, the sentence is kept, though
    # what it says of the number is untrue. The verifier checks that a number
    # is the fact's, and not what is said of it (contract, section 7.4).
    (planted,) = worked(Planting(text))
    kept = [s for s in sentences(planted) if not s.replaced]
    assert [s.fact_ids[0].split("/")[1] for s in kept] == [holds]


def test_a_sentence_may_cite_the_fact_it_was_asked_about_and_the_areas_name_and_no_other():
    class Named(Planting):
        def sentence(self, fact: Fact, ask: Ask) -> Sentence:
            text = f"In Alderwick: {render(fact).text}"
            cites = tuple(dict.fromkeys((fact.fact_id, f"{ALDERWICK}/area/name")))
            return Sentence(text=text, fact_ids=cites, origin=SentenceOrigin.MODEL)

    (named,) = worked(Named(""))
    assert not any(s.replaced for s in sentences(named))
    assert all(s.text.startswith("In Alderwick: ") for s in sentences(named))

    (everything,) = worked(CitesEverything("{template}"))
    # Every sentence is true. It is turned away for what it could have said.
    assert all(s.replaced for s in sentences(everything))


def test_a_changed_number_is_replaced_and_the_true_one_is_shown():
    class OffByOne(Planting):
        def sentence(self, fact: Fact, ask: Ask) -> Sentence:
            true = render(fact).text
            changed = true.replace("32 minutes", "23 minutes").replace("£50", "£500")
            return Sentence(text=changed, fact_ids=(fact.fact_id,), origin=SentenceOrigin.MODEL)

    (planted,) = worked(OffByOne(""))
    budget, commute, park = planted.reasons
    assert (budget.replaced, commute.replaced, park.replaced) == (True, True, False)
    assert "£50 under" in budget.text
    assert "32 minutes" in commute.text
    # The sentence that was left alone is kept as the model's.
    assert park.origin is SentenceOrigin.MODEL


def test_a_supported_sentence_from_a_model_is_kept():
    (kept,) = worked(Planting("{template}"))
    assert not any(s.replaced for s in sentences(kept))
    assert {s.origin for s in sentences(kept)} == {SentenceOrigin.MODEL}


def test_a_sentence_that_cites_another_fact_than_the_one_asked_about_is_replaced():
    class Elsewhere(Planting):
        def sentence(self, fact: Fact, ask: Ask) -> Sentence:
            true = render(fact)
            cites = (f"{fact.area_id}/area/name", *true.fact_ids)
            return Sentence(text=true.text, fact_ids=cites, origin=SentenceOrigin.MODEL)

    (found,) = worked(Elsewhere(""), areas=(CINDERMOOR,))
    assert [s.replaced for s in sentences(found)] == [False, True, True, True, True]


@pytest.mark.xfail(strict=True, reason="a known limit of the verifier: contract section 7.4")
@pytest.mark.parametrize(
    "write",
    [
        "a low-crime area popular with young professionals, near waitrose and the tate modern.",
        "{template} it is known for its respectable streets.",
    ],
)
def test_a_name_in_lower_case_or_a_claim_about_residents_is_replaced(write: str):
    # The verifier finds a name by its capital and a verdict by a short list
    # of words. Neither is enough for a sentence a model wrote, and this is
    # why no model-written explanation may be attached until it is extended.
    (planted,) = worked(Planting(write))
    assert all(s.replaced for s in sentences(planted))


@pytest.mark.parametrize("drafted", [0, 1, 3, 9])
def test_a_draft_of_the_wrong_length_is_not_used_at_all(drafted: int):
    class Short(Planting):
        def draft(self, area: ExplainInput) -> tuple[Sentence, ...]:
            return (super().draft(area) * 3)[:drafted]

    (found,) = worked(Short("{template}"))
    (honest,) = worked()
    assert all(s.replaced for s in sentences(found))
    assert [s.text for s in sentences(found)] == [s.text for s in sentences(honest)]


def fields(model: type[BaseModel], seen: set[type] | None = None) -> set[str]:
    seen = seen if seen is not None else set()
    if model in seen:
        return set()
    seen.add(model)
    found = set(model.model_fields)
    for field in model.model_fields.values():
        for inner in (field.annotation, *getattr(field.annotation, "__args__", ())):
            if isinstance(inner, type) and issubclass(inner, BaseModel):
                found |= fields(inner, seen)
    return found


def test_explainer_input_holds_no_user_text():
    # Every field an explainer can see, at any depth. None can carry what a person typed.
    assert fields(ExplainInput) == {
        "area_id",
        "facts",
        "contributions",
        "asks",
        # Fact
        "fact_id",
        "kind",
        "key",
        "label",
        "template",
        "slots",
        "numbers",
        "names",
        "sources",
        "as_of",
        "synthetic",
        "source_id",
        "name",
        # Who published a source, as the release names them.
        "publisher",
        # Contribution
        "component",
        "present",
        "weight",
        "share",
        "utility",
        "contribution",
        "loss",
        "fact_ids",
        # Ask
        "role",
    }
    explainer = Planting("{template}")
    worked(explainer, areas=(ALDERWICK, BRACKENHYTHE))
    assert [seen.area_id for seen in explainer.seen] == [ALDERWICK, BRACKENHYTHE]
    for seen in explainer.seen:
        # It is given the facts of the one area, and asked only about those.
        assert {fact.area_id for fact in seen.facts} == {seen.area_id}
        assert {ask.fact_id for ask in seen.asks} <= {fact.fact_id for fact in seen.facts}
        assert seen.asks[0].role is SentenceRole.ORIENTATION


def held_to_doing_badly(searches: int) -> tuple[int, int]:
    """Every trade-off of some searches of the committed release, held to the rule.

    How many areas were given a trade-off, and how many were given none.
    """
    release = fixture_release()
    draw = draws(29)
    told = none = 0
    for _ in range(searches):
        spec = random_spec(draw, release)
        result = rank(spec, release)
        areas = tuple(area.area_id for area in result.ranked)
        explained = explain(result, release, spec, areas, TemplateExplainer())
        for area, explanation in zip(result.ranked, explained, strict=True):
            present = {c.fact_ids[0]: c for c in area.contributions if c.present}
            caps = {commute.place_id: commute.max_minutes for commute in spec.commutes}
            late = any(
                leg.status == "beyond_cutoff"
                or (leg.minutes is not None and leg.minutes > caps[leg.place_id])
                for leg in area.legs
            )

            def badly(c: Contribution, area: RankedArea = area, late: bool = late) -> bool:
                over = area.budget is not None and area.budget.margin < 0
                short = (c.component == "budget" and over) or (c.component == "commute" and late)
                # A walk that is short in itself is no trade-off, wherever it stands.
                near = False
                if (walked := FLOORS.get(c.component.removeprefix("feature:"))) is not None:
                    figure = release.feature(area.area_id, FeatureId(c.component[8:]))
                    near = figure is not None and (figure.value or 0) <= walked
                worth_little = c.utility is not None and c.utility < TRADE_OFF_MAX_UTILITY
                return c.utility is not None and ((worth_little and not near) or short)

            if explanation.trade_off is None:
                none += 1
                assert not [c for c in present.values() if badly(c) and c.loss > 0]
                continue
            told += 1
            given_up = present[explanation.trade_off.fact_ids[0]]
            assert badly(given_up), explanation.trade_off.text
            assert given_up.loss == max(c.loss for c in present.values() if badly(c))
            assert explanation.trade_off.fact_ids not in [s.fact_ids for s in explanation.reasons]
    return told, none


def test_a_trade_off_is_something_the_area_does_badly():
    # "A 2 minute walk, closer than 77% of areas" was given as what an area
    # gives up, because nothing it was asked for lost more. A trade-off is a
    # thing the area does badly: worth less than a half, or a shortfall that a
    # reason may not state. What it does well is a reason or is left unsaid.
    told, none = held_to_doing_badly(searches=15)
    # Both are met often: an area that does something badly, and one that does not.
    assert told > 50 and none > 10


@pytest.mark.full
def test_every_trade_off_of_many_searches_is_something_the_area_does_badly():
    told, none = held_to_doing_badly(searches=200)
    assert told > 800 and none > 150


def park_alone(
    percentile: float, metres: float | None = None
) -> tuple[PreferenceSpec, InMemoryRelease]:
    """A search for a park and nothing else, and a release where Alderwick's is worth this.

    `metres` is how far its park is, where a test is about that and not
    about where it stands among the areas.
    """
    release = build_worked_release()
    spec = default_spec(Tenure.RENT).replace(
        weights=(
            FeatureWeight(
                feature_id=FeatureId.PARK_PROXIMITY,
                weight=1.0,
                direction=Direction.LESS,
                provenance=Provenance.STATED,
            ),
        )
    )
    moved = dataclasses.replace(
        release,
        features=tuple(
            feature_value(ALDERWICK, FeatureId.PARK_PROXIMITY, percentile).replace(
                **({} if metres is None else {"value": metres})
            )
            if (f.area_id, f.feature_id) == (ALDERWICK, FeatureId.PARK_PROXIMITY)
            else f
            for f in release.features
        ),
    )
    return spec, moved


@pytest.mark.parametrize(
    ("metres", "trade_off"),
    [(290.0, False), (799.0, False), (800.0, False), (801.0, True), (2_400.0, True)],
)
def test_a_short_walk_is_never_a_trade_off_however_many_areas_are_closer(
    metres: float, trade_off: bool
):
    # A trade-off is worse than most and bad in itself. A park at 290 m, further
    # than nine areas in ten, is worth 0.1 and is still a short walk.
    assert NEVER_A_TRADE_OFF[FeatureId.PARK_PROXIMITY] == 800
    spec, release = park_alone(90.0, metres)
    ranked = rank(spec, release)
    (alderwick,) = (area for area in ranked.ranked if area.area_id == ALDERWICK)
    (park,) = alderwick.contributions
    assert park.utility is not None and park.utility < TRADE_OFF_MAX_UTILITY
    (found,) = explain(ranked, release, spec, (ALDERWICK,), TemplateExplainer())
    assert (found.trade_off is not None) == trade_off
    # It is no reason either: it is in the working of the result, and in no sentence.
    assert found.reasons == ()


def test_a_station_560_metres_off_is_not_what_an_area_gives_up():
    # Two journeys, both within their limits, and the one catch shown was a
    # station seven minutes off, because fourteen areas are closer to one.
    release = fixture_release()
    places = {place.name: place.place_id for place in release.places}
    journeys = tuple(
        Commute(
            place_id=places[name],
            mode=Mode.PT,
            max_minutes=minutes,
            strictness=Strictness.SOFT,
            provenance=Provenance.STATED,
        )
        for name, minutes in (("Cindermoor Works", 35), ("Wexmoor University", 40))
    )
    spec = given_way_spec(default_spec(Tenure.RENT).replace(commutes=journeys))
    ranked = rank(spec, release)
    first = ranked.ranked[0]
    walk = release.feature(first.area_id, FeatureId.STATION_WALK)
    assert walk is not None and walk.value == 560
    (station,) = (c for c in first.contributions if c.component == "feature:station_walk")
    assert station.utility is not None and station.utility < TRADE_OFF_MAX_UTILITY
    (found,) = explain(ranked, release, spec, (first.area_id,), TemplateExplainer())
    assert found.trade_off is None or "station" not in found.trade_off.text
    # Across the release, no walk at or under its figure is ever what an area gives up.
    every = explain(
        ranked, release, spec, tuple(a.area_id for a in ranked.ranked), TemplateExplainer()
    )
    for explanation in every:
        if explanation.trade_off is None:
            continue
        key = explanation.trade_off.fact_ids[0].split("/")[-1]
        if explanation.trade_off.fact_ids[0].split("/")[1] == "feature" and key in FLOORS:
            row = release.feature(explanation.area_id, FeatureId(key))
            assert row is not None and row.value is not None and row.value > FLOORS[key]


@pytest.mark.parametrize(
    ("percentile", "reasons", "trade_off"),
    [
        (50.0, 1, False),  # worth a half: a reason
        (52.0, 0, False),  # worth 0.48: neither. It was once given as what the area gives up
        (65.0, 0, False),  # worth 0.35: still neither
        (66.0, 0, True),  # worth 0.34: what the area gives up
        (100.0, 0, True),
    ],
)
def test_what_lies_between_the_two_thresholds_is_neither_a_reason_nor_a_trade_off(
    percentile: float, reasons: int, trade_off: bool
):
    assert (REASON_MIN_UTILITY, TRADE_OFF_MAX_UTILITY) == (0.5, 0.35)
    # The park is a long walk away, so where it stands among the areas decides.
    spec, release = park_alone(percentile, metres=2_000.0)
    (found,) = explain(rank(spec, release), release, spec, (ALDERWICK,), TemplateExplainer())
    assert len(found.reasons) == reasons
    assert (found.trade_off is not None) == trade_off


def test_a_reason_is_said_from_the_better_side_and_a_trade_off_from_the_worse():
    # Under "why it fits" the distance to a park once read "further than 47% of areas".
    spec, release = park_alone(20.0)
    (well,) = explain(rank(spec, release), release, spec, (ALDERWICK,), TemplateExplainer())
    assert [s.text for s in well.reasons] == [
        "Straight-line distance to the nearest marked way into a park of 2 ha or more: "
        "280 m, closer than 50% of the 4 areas compared in this release."
    ]
    spec, release = park_alone(90.0)
    (badly,) = explain(rank(spec, release), release, spec, (ALDERWICK,), TemplateExplainer())
    assert badly.trade_off is not None
    assert badly.trade_off.text == (
        "Straight-line distance to the nearest marked way into a park of 2 ha or more: "
        "910 m, further than 75% of the 4 areas compared in this release."
    )
    assert not badly.trade_off.replaced


Searched = tuple[PreferenceSpec, RankResult, tuple[Explanation, ...]]


@cache
def searches() -> tuple[Searched, ...]:
    """Sixty searches of the small release, each ranked and explained. Made once for them all."""
    release = small_release()
    draw = draws(62)
    found: list[Searched] = []
    for _ in range(60):
        spec = random_spec(draw, release)
        result = rank(spec, release)
        areas = tuple(a.area_id for a in result.ranked)
        found.append((spec, result, explain(result, release, spec, areas, TemplateExplainer())))
    return tuple(found)


@cache
def asked_for_alone(tag_id: TagId, toward: Toward = Toward.HIGH) -> dict[str, Explanation]:
    """Every area of the committed release, explained for a search that asks for one vibe alone."""
    release = fixture_release()
    spec = default_spec(Tenure.RENT).replace(
        weights=(),
        tags=(TagWeight(tag_id=tag_id, weight=1.0, toward=toward, provenance=Provenance.STATED),),
    )
    result = rank(spec, release)
    areas = tuple(area.area_id for area in result.ranked)
    explained = explain(result, release, spec, areas, TemplateExplainer())
    names = {area.area_id: area.name for area in release.neighbourhoods}
    return {names[found.area_id]: found for found in explained}


def about(explanation: Explanation, key: str) -> ExplainedSentence:
    """The sentence of an explanation that cites one fact, whichever role it has."""
    said = [*explanation.reasons, *([explanation.trade_off] if explanation.trade_off else [])]
    return next(sentence for sentence in said if sentence.fact_ids[0].endswith(key))


# A result is to say in a few lines why this place. The sentence of a vibe ran
# to thirty words, half of them its dates and that the recipe is a judgement,
# the same on every card that led with that vibe.
IN_SHORT = [
    (
        TagId.LEAFY,
        Toward.HIGH,
        "Alderwick",
        "Leafy: band 5 of 5, counted from least to most, among the 21 areas compared in "
        "this release.",
    ),
    # A band that rests on part of a recipe still says so: nothing is filled in.
    (
        TagId.EVERYDAY_ON_FOOT,
        Toward.HIGH,
        "Foxholt",
        "Everyday on foot: band 5 of 5, counted from least to most, among the 21 areas "
        "compared in this release. Worked out from 3 of its 5 parts, 70 of 100 by weight.",
    ),
    # A mixed area is still a range, and never a point in the middle.
    (
        TagId.PACE,
        Toward.HIGH,
        "Foxholt",
        "Going out: varies within this area, from band 3 to band 5 of 5, counted from Calm "
        "to Buzzy.",
    ),
]


@pytest.mark.parametrize(
    ("tag_id", "toward", "name", "text"), IN_SHORT, ids=[f"{t[0].value} {t[2]}" for t in IN_SHORT]
)
def test_a_vibe_is_said_in_short_in_an_explanation(
    tag_id: TagId, toward: Toward, name: str, text: str
):
    sentence = about(asked_for_alone(tag_id, toward)[name], f"/tag/{tag_id.value}")
    assert sentence.text == text
    assert sentence.origin is SentenceOrigin.TEMPLATE and not sentence.replaced


def test_what_a_short_sentence_leaves_out_is_still_held_by_the_fact_it_cites():
    # The dates and the line that a recipe is a judgement are shown with the
    # source, one press away. So the fact must hold both, and the sentence
    # must say nothing the full statement of the fact does not.
    release = fixture_release()
    checked = 0
    for tag_id, _, name, _ in IN_SHORT:
        found = asked_for_alone(tag_id)[name]
        facts = {fact.fact_id: fact for fact in facts_for(release, found.area_id, None)}
        fact = facts[about(found, f"/tag/{tag_id.value}").fact_ids[0]]
        in_full = render(fact).text
        assert in_full.startswith(about(found, f"/tag/{tag_id.value}").text)
        assert in_full.endswith(f"Parts dated {fact.slots['span']}. {JUDGEMENT}")
        assert fact.slots["judgement"] == JUDGEMENT
        assert fact.as_of == fact.slots["span"]
        checked += 1
    assert checked == 3


def test_only_a_vibe_is_said_in_short():
    # Every other sentence of an explanation is the full statement of its fact.
    spec, release = build_worked_spec(), build_worked_release()
    said = vibes = 0
    for found in worked(areas=(ALDERWICK, BRACKENHYTHE, CINDERMOOR)):
        facts = {fact.fact_id: fact for fact in facts_for(release, found.area_id, spec)}
        for sentence in sentences(found):
            fact = facts[sentence.fact_ids[0]]
            in_short = fact.kind.value == "tag"
            assert (sentence.text != render(fact).text) == in_short
            said += 1
            vibes += in_short
    assert said > 10 and vibes >= 1


def test_no_reason_is_said_in_the_word_a_trade_off_is_said_in():
    said = 0
    for spec, _, explained in searches():
        for found in explained:
            for sentence, worse in (
                *((reason, False) for reason in found.reasons),
                *(((found.trade_off, True),) if found.trade_off else ()),
            ):
                kind, key = sentence.fact_ids[0].split("/")[1:3]
                if kind != "feature":
                    continue
                feature_id = FeatureId(key)
                chosen = {w.feature_id: w.direction for w in spec.active_weights}[feature_id]
                feature = FEATURES[feature_id]
                good, bad = (
                    (feature.higher, feature.lower)
                    if chosen is Direction.MORE
                    else (feature.lower, feature.higher)
                )
                if " than " not in sentence.text:
                    continue
                said += 1
                assert f", {bad if worse else good} than " in sentence.text, sentence.text
    assert said > 100


def test_each_journey_with_no_time_has_a_sentence_of_its_own():
    spec = build_worked_spec()
    soft = spec.replace(commutes=tuple(c.replace(strictness="soft") for c in spec.commutes))
    release = dataclasses.replace(
        build_worked_release(),
        travel_table=travel_table(4, 2, ((32, None), (None, None), (44, 22), (25, 36))),
    )
    one, neither = explain(
        rank(soft, release), release, soft, (ALDERWICK, BRACKENHYTHE), TemplateExplainer()
    )
    assert [s.text for s in one.missing] == [
        "There is no journey time from Alderwick to Foxholt Works in this release, "
        "so that journey was left out of the score."
    ]
    # The journey that has a time is still scored. It is no reason while another is unknown.
    assert not any("/travel/" in s.fact_ids[0] for s in one.reasons)
    assert [s.fact_ids[0].split("/", 1)[1] for s in neither.missing] == [
        "missing/commute.syn-p0001.pt",
        "missing/commute.syn-p0002.pt",
        "missing/feature:noise_exposure",
    ]
    assert not any(s.replaced for s in (*one.missing, *neither.missing))


def test_a_journey_over_its_limit_is_what_an_area_gives_up_and_says_by_how_much():
    (cindermoor,) = worked(areas=(CINDERMOOR,))
    assert cindermoor.trade_off is not None
    assert cindermoor.trade_off.text == (
        "By public transport to Pellam Cross: about 44 minutes on a typical weekday morning, "
        "49 if you just miss a service, 4 minutes over the 40 you set."
    )


def test_there_is_no_trade_off_when_nothing_is_done_badly():
    release = build_worked_release()
    spec = build_worked_spec()
    spec = spec.replace(commutes=(), weights=(), tags=())
    # Only the budget is asked for, and Alderwick is within it.
    (alderwick,) = explain(rank(spec, release), release, spec, (ALDERWICK,), TemplateExplainer())
    assert len(alderwick.reasons) == 1
    assert alderwick.trade_off is None
    # Brackenhythe is over budget. Its one component is no reason, and it is its trade-off.
    (over,) = explain(rank(spec, release), release, spec, (BRACKENHYTHE,), TemplateExplainer())
    assert over.reasons == ()
    assert over.trade_off is not None
    assert over.trade_off.fact_ids == (f"{BRACKENHYTHE}/budget_fit/rent.bed_1",)
    # A component that is a reason is never the trade-off, though nothing else gives
    # anything up and it loses a little to the areas that do better still.
    park = build_worked_spec().replace(commutes=(), tags=(), weights=spec.weights)
    park = park.replace(
        budget=park.budget.replace(amount=None), weights=build_worked_spec().weights[1:]
    )
    ranked = rank(park, release)
    (only,) = explain(ranked, release, park, (ALDERWICK,), TemplateExplainer())
    (alderwick,) = (area for area in ranked.ranked if area.area_id == ALDERWICK)
    (alone,) = (c for c in alderwick.contributions if c.present and c.loss > 0)
    assert alone.utility is not None and alone.utility >= REASON_MIN_UTILITY
    assert [s.fact_ids for s in only.reasons] == [alone.fact_ids[:1]]
    assert only.trade_off is None


def test_a_spec_that_asks_for_nothing_is_explained_with_the_area_alone():
    spec = default_spec(build_worked_spec().tenure).replace(weights=())
    release = build_worked_release()
    (found,) = explain(rank(spec, release), release, spec, (ALDERWICK,), TemplateExplainer())
    assert found.orientation.text == "Alderwick is in Quillhaven."
    assert (found.reasons, found.trade_off, found.missing) == ((), None, ())


def test_explain_refuses_a_result_that_is_not_the_ranking_of_this_spec_and_release():
    release = build_worked_release()
    spec = build_worked_spec()
    result = rank(spec, release)
    other_spec = spec.replace(commute_weight=0.5)
    with pytest.raises(ValueError, match="not the ranking"):
        explain(result, release, other_spec, (ALDERWICK,), TemplateExplainer())
    other = dataclasses.replace(
        release, manifest=release.manifest.replace(release_id="syn-2026-09-24-01")
    )
    with pytest.raises(ValueError, match="not the ranking"):
        explain(result, other, spec, (ALDERWICK,), TemplateExplainer())


def test_every_explanation_of_every_search_is_made_of_sentences_that_passed():
    explained = 0
    for _, _, every in searches():
        for found in every:
            shown = sentences(found)
            assert not any(s.replaced for s in shown)
            assert all(s.fact_ids and s.fact_ids[0].startswith(found.area_id) for s in shown)
            assert len(found.reasons) <= 3
            assert len({s.fact_ids for s in found.reasons}) == len(found.reasons)
            explained += 1
    assert explained > 100


def test_no_reason_in_any_search_is_something_the_area_does_badly():
    reasons = without = over_budget = over_the_cap = 0
    for spec, result, explained in searches():
        caps = {c.place_id: c.max_minutes for c in spec.commutes}
        for area, found in zip(result.ranked, explained, strict=True):
            behind = {c.fact_ids[0]: c for c in area.contributions if c.present}
            for reason in found.reasons:
                utility = behind[reason.fact_ids[0]].utility
                assert utility is not None and utility >= 0.5
                # A reason never states a shortfall: no home over budget, no journey over its cap.
                assert "over your budget" not in reason.text
                assert "more than" not in reason.text or "/travel/" not in reason.fact_ids[0]
                reasons += 1
            # Worked out here from the result, and not by the code under test.
            short_of = set[str]()
            if area.budget is not None and area.budget.margin < 0:
                short_of.add("budget")
            if any(leg.minutes is None or leg.minutes > caps[leg.place_id] for leg in area.legs):
                short_of.add("commute")
            done_well = [
                c
                for c in behind.values()
                if c.utility is not None and c.utility >= 0.5 and c.component not in short_of
            ]
            passed_over = [
                c
                for c in behind.values()
                if c.utility is not None and c.utility >= 0.5 and c.component in short_of
            ]
            over_budget += any(c.component == "budget" for c in passed_over)
            over_the_cap += any(c.component == "commute" for c in passed_over)
            # Everything done well is a reason, up to three, largest contribution first.
            assert [r.fact_ids[0] for r in found.reasons] == [
                c.fact_ids[0] for c in area.contributions if c in done_well
            ][:3]
            without += not found.reasons and bool(behind)
    assert reasons > 300
    assert without > 5
    # Both happen in these searches: each was a reason before, for being worth a half or more.
    assert over_budget > 5
    assert over_the_cap > 0
