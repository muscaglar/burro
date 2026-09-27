"""Four words of the design that no sentence says to a person.

A release, a recipe, a part of one and "counted from" are words of this repository. A
person who has never seen Burro knows none of them, and read each as a riddle: "in this
release" ended almost every sentence about a figure. What a sentence says in their place
is "the areas Burro compared", "the measurements that go into this vibe", and "where the
bands run from".

Every fixed word core writes for a person is read here, and so is every word of the
catalogue, which a release carries: the name of a measure, and what a vibe means and
cannot see.
"""

import re
from collections.abc import Iterator

from burro_core import census, income
from burro_core.catalogue import (
    CRIME_CAVEAT,
    FAMILIES,
    FEATURES,
    JUDGEMENT,
    MADE_FROM,
    NEAR_A_STATION,
    ROUGH_GUIDE,
    TAGS,
    WHY_A_ROUGH_GUIDE,
)
from burro_core.estimate import ESTIMATED, SAID, VERDICT
from burro_core.explain import IN_SHORT, TEMPLATES
from burro_core.facts import (
    AT_THE_BUDGET,
    AT_THE_LIMIT,
    COST_OF,
    HALF_LET_FOR_LESS,
    HALF_SOLD_FOR_LESS,
    IS_OF,
    MISSING_LABELS,
    PARTLY,
    RENT_CAUTION,
    RENT_IS_OF_A_PLACE,
    STANDINGS,
    facts_for,
)
from burro_core.interpret import (
    A_TERRACED_HOUSE,
    BY_BEDROOMS,
    BY_KIND,
    BY_KIND_OF_HOUSE,
    DOES_NOT_MATTER,
    MAY_BE_ANOTHERS,
    NO_BUDGET_ON_A_VISIT,
    NO_HOME_ON_A_VISIT,
    NO_PRICE_ON_A_VISIT,
    NO_STAYING_AWAY,
    NO_STEP_ON_A_VISIT,
    NOT_SAID_TO_BE_WANTED,
    NOT_WANTED,
    NOT_WANTED_AND_COUNTED,
    NOTHING_CHANGED,
    NOTICES,
    ONE_PRESS_AWAY,
    THE_LEAST_DEAR,
    TIME_NOT_TAKEN,
    TO_RENT_ALONE,
    longer_was_taken,
    worked_out_by_the_month,
)
from burro_core.lexicon import (
    A_RISE_OR_THE_SCALE,
    A_RISE_PROMISES_NOTHING,
    CANNOT_SAY_SAFE,
    COUNTED_AT_THE_CENSUS,
    NO_IDENTITY,
    NO_NEIGHBOURS,
    NO_POOLS,
    NOT_ONE_HOME,
    OF_A_CHAIN,
    PLACES_NOT_PEOPLE,
    WHAT_AGE,
)

from .support import small_release

OF_THE_DESIGN = re.compile(r"\b(?:releases?|recipes?|parts)\b|\bcounted from\b", re.IGNORECASE)
# The name of a slot is no word a person reads: what fills it is.
A_SLOT = re.compile(r"\{[a-z_]+\}")


def read_by_a_person(said: str) -> str:
    """The words of a template without the names of its slots."""
    return A_SLOT.sub("", said)


def of_a_fact() -> Iterator[str]:
    """What a sentence of a fact is made of: every template, and every clause that fills one."""
    yield from TEMPLATES.values()
    yield from IN_SHORT.values()
    yield from STANDINGS.values()
    yield from (PARTLY, JUDGEMENT, MADE_FROM, ESTIMATED, CRIME_CAVEAT)
    yield from (IS_OF, RENT_CAUTION, RENT_IS_OF_A_PLACE, HALF_SOLD_FOR_LESS, HALF_LET_FOR_LESS)
    yield from (AT_THE_BUDGET, AT_THE_LIMIT, *SAID.values(), *VERDICT.values())
    yield from (*COST_OF.values(), *MISSING_LABELS.values())


def of_the_reader() -> Iterator[str]:
    """What is said of what a person typed: each notice, and the note of each offer."""
    yield from NOTICES.values()
    yield NOTHING_CHANGED
    yield from (BY_KIND, BY_BEDROOMS, TO_RENT_ALONE, BY_KIND_OF_HOUSE)
    yield f"{A_TERRACED_HOUSE}{THE_LEAST_DEAR}{ONE_PRESS_AWAY}"
    yield from (NO_STAYING_AWAY, TIME_NOT_TAKEN, MAY_BE_ANOTHERS)
    yield from (longer_was_taken(35, 40), worked_out_by_the_month(350))
    yield from (CANNOT_SAY_SAFE, NO_POOLS, NO_NEIGHBOURS, NOT_ONE_HOME, PLACES_NOT_PEOPLE)
    yield from (NO_IDENTITY, A_RISE_PROMISES_NOTHING, A_RISE_OR_THE_SCALE, OF_A_CHAIN)
    yield from (COUNTED_AT_THE_CENSUS, WHAT_AGE)
    yield from (NO_HOME_ON_A_VISIT, NO_BUDGET_ON_A_VISIT, NO_PRICE_ON_A_VISIT, NO_STEP_ON_A_VISIT)
    yield from (NOT_WANTED, NOT_WANTED_AND_COUNTED, DOES_NOT_MATTER, NOT_SAID_TO_BE_WANTED)


def of_a_page() -> Iterator[str]:
    """What stands on the page of vibes and of an area, which is no sentence of a fact."""
    yield from FAMILIES.values()
    yield from (ROUGH_GUIDE, *WHY_A_ROUGH_GUIDE.values(), NEAR_A_STATION)
    for words in (census.CENSUS_2021, census.MADE_UP, income.ONS, income.MADE_UP):
        for said in words.model_dump(mode="json").values():
            if isinstance(said, str):
                yield said
            elif isinstance(said, list):
                yield from (str(one) for one in said)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


def of_the_catalogue() -> Iterator[str]:
    """What a release carries of core's catalogue, and what core says beside it."""
    for feature in FEATURES.values():
        yield from (feature.label, feature.short_label, feature.unit)
        yield from (feature.higher, feature.lower)
    for tag in TAGS.values():
        yield from (tag.label, tag.short_label, tag.meaning, *tag.cannot_see)
        yield from (end for end in (tag.low_end, tag.high_end) if end)


def test_no_word_of_the_catalogue_is_a_word_of_the_design():
    read = list(of_the_catalogue())
    assert len(read) > 600
    found = [(said, OF_THE_DESIGN.findall(said)) for said in read if OF_THE_DESIGN.search(said)]
    assert found == []
    # A unit is written out where a person would have to know its short form.
    units = {feature.unit for feature in FEATURES.values()}
    assert not units & {"per ha", "per km²"}
    assert {"per hectare", "per square kilometre"} <= units


def test_no_fixed_word_core_writes_for_a_person_is_a_word_of_the_design():
    read = [read_by_a_person(said) for said in (*of_a_fact(), *of_the_reader(), *of_a_page())]
    assert len(read) > 120
    found = [(said, OF_THE_DESIGN.findall(said)) for said in read if OF_THE_DESIGN.search(said)]
    assert found == []


def test_no_fixed_word_core_writes_for_a_person_names_the_settings_or_a_rough_guide():
    """The founder named the settings "Space requirements", and asked that no word of a
    rough guide be passed on. What the review desk is shown of a vibe is no such word: it
    is handed to no client."""
    read = [read_by_a_person(said) for said in (*of_a_fact(), *of_the_reader())]
    read += [said for said in of_a_page() if said not in (ROUGH_GUIDE, *WHY_A_ROUGH_GUIDE.values())]
    never = re.compile(r"\bsettings?\b|\brough guide\b", re.IGNORECASE)
    assert [said for said in read if never.search(said)] == []


def test_every_comparison_names_the_areas_burro_compared_and_no_city():
    for clause in STANDINGS.values():
        assert "Burro" in clause and "London" not in clause
    assert "areas Burro compared" in TEMPLATES[next(iter(IN_SHORT))]


def test_the_check_would_catch_each_of_the_four():
    for said in (
        "closer than 77% of the 22 areas compared in this release",
        "The recipe is Burro's own. The weights are a judgement.",
        "Worked out from 3 of its 4 parts, 70 of 100 by weight.",
        "Leafy: band 5 of 5, counted from least to most",
    ):
        assert OF_THE_DESIGN.search(said), said
    # A word that only holds one of them says something else.
    for said in ("It is part of Burro.", "The sale was released.", "It departs at noon."):
        assert OF_THE_DESIGN.search(said) is None, said


def test_no_sentence_of_any_fact_of_a_release_says_one_but_in_the_name_of_a_thing():
    """A sentence is its template filled from a fact. The name of a measure or of a vibe is
    the release's, which a person may have given, and is read where a release is read."""
    from burro_core.explain import render
    from burro_core.ids import SentenceRole, Tenure
    from burro_core.spec import default_spec

    release = small_release()
    read = 0
    for area in release.neighbourhoods:
        for spec in (None, default_spec(Tenure.RENT)):
            for fact in facts_for(release, area.area_id, spec):
                for role in SentenceRole:
                    text = render(fact, role).text
                    # What is left once the name the release gives the thing is taken out.
                    rest = text.replace(fact.label, "")
                    assert OF_THE_DESIGN.search(rest) is None, text
                    read += 1
    assert read > 2_000
