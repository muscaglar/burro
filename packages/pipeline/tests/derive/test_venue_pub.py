"""The register's pubs and bars, from the register to a figure for each area.

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
from burro_pipeline.derive import measures, venue_food_drink, venue_pub, venues_nearby
from burro_pipeline.derive.food_register import Group
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.venue_pub import Places
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from .food_support import DAY, ONE, THREE, TWO, inputs_of

NEVER_SAID = re.compile(r"\b(rating|rated|hygiene rating|stars?|endorse[sd]?|approved by)\b", re.I)
# What keeps a figure out of a release is printed where anyone reads it, and names no place.
NAMES_A_BOROUGH = re.compile(r"\b(Westminster|Bexley|Bromley|Islington|Richmond|London Borough)\b")


def built(folder: Path) -> Places:
    inputs = inputs_of(folder)
    return venue_pub.build(inputs, spine.build(inputs))


def test_the_one_kind_that_counts_is_the_registers_kind_for_a_pub_a_bar_and_a_nightclub():
    assert venue_pub.WHAT.groups == (Group.PUB,)
    assert venue_pub.WHAT.kinds == ("Pub/bar/nightclub",)
    assert venue_pub.WHAT.key == venue_pub.KEY == "venue_pub"


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


def test_the_rows_are_written_under_an_id_of_their_own_and_never_under_cores(tmp_path: Path):
    """Core's id for pubs and bars names the figure of the file of places."""
    found = built(tmp_path)
    assert [row.fact_id.split("/", 1)[1] for row in found.rows] == ["feature/venue_pub"] * 3
    assert [row.fact_id.split("/", 1)[1] for row in found.rows_of_the_rate] == [
        "feature/venue_pub_per_homes"
    ] * 3
    assert {row.derivation_id for row in found.rows} == {"places_within_800m_at_homes@1"}
    rows = (*found.rows, *found.rows_of_the_rate)
    assert Evidence.of("lon-2026-10-02-01", found.files, venue_pub.METHODS, rows)
    assert venue_pub.METHODS == venue_food_drink.METHODS


def test_core_holds_no_measure_of_it_so_no_build_carries_one():
    assert not venue_pub.core_holds_it()
    assert venue_pub.KEY not in {feature.value for feature in FeatureId}
    assert venue_pub.KEY not in {measure.feature for measure in measures.MEASURES}
    assert not hasattr(venue_pub, "FEATURE")
    # Nothing of the register is a measure of pubs and bars: the file of places is.
    by_feature = {measure.feature: measure for measure in measures.MEASURES}
    for feature in (FeatureId.VENUE_EVENING, FeatureId.VENUE_EVENING_PER_HOMES):
        assert by_feature[feature].source == venues_nearby.SOURCE != venue_pub.SOURCE
        assert not by_feature[feature].held_back and not by_feature[feature].waits_on
    # No measure is held back.
    assert [one.feature for one in measures.MEASURES if one.held_back] == []


def test_what_the_row_of_the_catalogue_would_say_names_a_nightclub_as_core_does_not(
    tmp_path: Path,
):
    """The register has one kind for the three. Core's measure counts no nightclub."""
    proposed = built(tmp_path).proposed
    assert proposed.key == "venue_pub"
    assert proposed.label == "Pubs, bars and nightclubs within 800 m of home, in a straight line"
    assert FEATURES[FeatureId.VENUE_EVENING].label == (
        "Pubs and bars within 800 m of home, in a straight line"
    )
    assert proposed.vintage == DAY and "Pub/bar/nightclub, as at" in proposed.definition


def test_what_keeps_the_figure_out_of_every_release_is_said_and_names_no_place():
    """Pubs alone follow how a council fills in the register as much as they follow pubs."""
    assert len(venue_pub.NOT_CARRIED) == 4
    said = " ".join(venue_pub.NOT_CARRIED)
    for words in (
        "councils do not give kinds alike",
        "no pub that a person can walk into",
        "has an address",
        "held to a second source",
        "did not confirm it",
        "no release carries this figure",
    ):
        assert words in said
    for sentence in venue_pub.NOT_CARRIED:
        assert sentence.endswith(".") and not re.search(r"[!|\n]", sentence)
        assert not NEVER_SAID.search(sentence) and not NAMES_A_BOROUGH.search(sentence)


def test_the_measure_says_what_it_cannot_see():
    said = " ".join(venue_pub.CANNOT_SEE)
    assert "has closed and is still listed" in said and "trades and is not registered" in said
    assert "how late a place is open" in said and "councils do not give kinds alike" in said
    for sentence in venue_pub.CANNOT_SEE:
        assert sentence.endswith(".") and not re.search(r"[!|\n]", sentence)
    assert venue_food_drink.AT_THE_EDGE in venue_pub.CANNOT_SEE
    assert len(venue_pub.CANNOT_SEE) == len(set(venue_pub.CANNOT_SEE)) == 10
    for line in (*venue_food_drink.OF_EVERY_KIND, venue_food_drink.AS_AT_THE_CENSUS):
        assert line in venue_pub.CANNOT_SEE
    assert venue_food_drink.ONE_KIND_FOLLOWS_DENSITY in venue_pub.CANNOT_SEE
    for sentence in venue_pub.CANNOT_SEE:
        assert not re.search(r"[.!?]\s|\d", sentence)
