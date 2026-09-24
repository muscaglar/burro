"""Pubs and bars, from the register to a figure for each area.

Every file here is made up, and says so. `food_support.py` draws the town and
writes its register, and `test_venue_food_drink.py` holds the counting, the
edge of London and the evidence. These hold what differs: which kind is
counted, and what is said of the measure.

    Quillhaven 001   a pub by the first centre, and one 790 metres from the last
    Quillhaven 002   none
    Tallowgate 001   a pub by the first centre. One more has no point
"""

import re
from pathlib import Path

from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId
from burro_pipeline.cells import spine
from burro_pipeline.derive import measures, venue_evening, venue_food_drink
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_food_drink import Venues
from burro_pipeline.evidence.row import State

from .food_support import DAY, ONE, THREE, TWO, inputs_of

NEVER_SAID = re.compile(r"\b(rating|rated|hygiene rating|stars?|endorse[sd]?|approved by)\b", re.I)
# What holds a measure back is printed in every report of a build, and names no place.
NAMES_A_BOROUGH = re.compile(r"\b(Westminster|Bexley|Bromley|Islington|Richmond|London Borough)\b")


def built(folder: Path) -> Venues:
    inputs = inputs_of(folder)
    return venue_evening.build(inputs, spine.build(inputs))


def test_the_one_kind_that_counts_is_the_registers_kind_for_a_pub_a_bar_and_a_nightclub():
    assert venue_evening.PUBS_AND_BARS.groups == (Group.PUB,)
    assert venue_evening.PUBS_AND_BARS.kinds == ("Pub/bar/nightclub",)
    assert venue_evening.PUBS_AND_BARS.key == "venue_evening"


def test_an_area_is_given_the_pubs_within_reach_of_its_typical_home(tmp_path: Path):
    found = built(tmp_path)
    # Of 500 homes, 110 have a pub within reach and so have 140.
    assert (110 + 140) / 500 == 0.5
    assert found.worked[ONE] == Worked(0.5, 4, 4, 1.0, State.PRESENT)
    assert found.worked[TWO] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    # Of 820 homes, 190 have one. The pub with no point is within reach of nobody.
    assert found.worked[THREE] == Worked(0.2, 4, 4, 1.0, State.PRESENT)
    assert (found.register.listed(Group.PUB), found.register.placed(Group.PUB)) == (4, 3)


def test_the_second_figure_is_the_pubs_for_each_thousand_homes_within_reach(tmp_path: Path):
    found = built(tmp_path)
    bottom = 110 * 110 + 120 * 120 + 130 * 130 + 140 * 140
    assert round(1000 * (110 + 140) / bottom, 4) == 3.9683
    assert found.rate[ONE] == Worked(4.0, 4, 4, 1.0, State.PRESENT)


def test_the_rows_are_written_under_cores_id_for_the_measure(tmp_path: Path):
    found = built(tmp_path)
    assert [row.fact_id.split("/", 1)[1] for row in found.rows] == ["feature/venue_evening"] * 3
    assert {row.derivation_id for row in found.rows} == {"places_within_800m_at_homes@1"}
    assert venue_evening.METHODS == venue_food_drink.METHODS


def test_the_row_of_the_catalogue_names_what_is_counted_and_is_not_cores(tmp_path: Path):
    """Core says evening venues, for each square kilometre. The register names no other venue."""
    metric = built(tmp_path).metric
    feature = FEATURES[FeatureId.VENUE_EVENING]
    assert metric.feature_id is FeatureId.VENUE_EVENING
    assert metric.label == "Pubs, bars and nightclubs within 800 m of home, in a straight line"
    assert (feature.label, feature.unit) == ("Pubs, bars and evening venues", "per km²")
    assert (metric.unit, metric.polarity) == ("count", feature.polarity)
    assert metric.vintage == DAY and "Pub/bar/nightclub, as at" in metric.definition
    assert not measures.says_what_core_says(metric)


def test_a_check_of_its_figures_holds_the_measure_back_from_every_release():
    """Pubs alone follow how a council fills in the register as much as they follow pubs."""
    (listed,) = [one for one in measures.MEASURES if one.feature is FeatureId.VENUE_EVENING]
    assert listed.held_back == venue_evening.HELD_BACK and len(venue_evening.HELD_BACK) == 4
    said = " ".join(venue_evening.HELD_BACK)
    for words in (
        "councils do not give kinds alike",
        "no pub that a person can walk into",
        "has an address",
        "A second source",
        "no release and no vibe",
    ):
        assert words in said
    for sentence in venue_evening.HELD_BACK:
        assert sentence.endswith(".") and not re.search(r"[!|\n]", sentence)
        assert not NEVER_SAID.search(sentence) and not NAMES_A_BOROUGH.search(sentence)


def test_the_measure_says_what_it_waits_on_and_what_it_cannot_see():
    assert "evening venues" in venue_evening.WAITS_ON[0]
    assert venue_evening.WAITS_ON[1:] == venue_food_drink.OF_THE_REGISTER
    said = " ".join(venue_evening.CANNOT_SEE)
    assert "has closed and is still listed" in said and "trades and is not registered" in said
    assert "how late a place is open" in said and "councils do not give kinds alike" in said
    for sentence in (*venue_evening.CANNOT_SEE, *venue_evening.WAITS_ON):
        assert sentence.endswith(".") and not re.search(r"[!|\n]", sentence)
    assert venue_food_drink.AT_THE_EDGE in venue_evening.CANNOT_SEE
    assert len(venue_evening.CANNOT_SEE) == len(set(venue_evening.CANNOT_SEE)) == 10
    for line in (*venue_food_drink.OF_EVERY_KIND, venue_food_drink.AS_AT_THE_CENSUS):
        assert line in venue_evening.CANNOT_SEE
    assert venue_food_drink.ONE_KIND_FOLLOWS_DENSITY in venue_evening.CANNOT_SEE
    for sentence in venue_evening.CANNOT_SEE:
        assert not re.search(r"[.!?]\s|\d", sentence)
