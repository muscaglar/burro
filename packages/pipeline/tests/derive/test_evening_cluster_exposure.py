"""Homes near a cluster of pubs and bars, from the file of places to a figure for each area.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places, and `test_venues_nearby.py` holds which record is a pub
or a bar. The centres stand 1,000 metres apart, so every count can be made by
hand:

    Quillhaven 001   Q1  a pub, a bar and a gastropub, each within 150 metres
                     Q2  two pubs within 150 metres, and a third 160 metres off
                     Q3, Q4  none
    Quillhaven 002   R1  one pub. R2, R3 and R4 have none
    Tallowgate 001   none

A bookshop stands by every centre, so that the file is seen to hold something
within reach of every home.
"""

import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES, NUISANCES, TAGS
from burro_core.ids import FeatureId, NativeResolution, Polarity, TagId, TermReading
from burro_pipeline.cells import spine
from burro_pipeline.derive import evening_cluster_exposure, measures, venues_nearby
from burro_pipeline.derive.evening_cluster_exposure import (
    CANNOT_SEE,
    FEWEST,
    METHOD,
    METRES,
    Exposure,
)
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from ..fetch.parquet_support import Place
from .culture_support import (
    BY_EVERY_CENTRE,
    CANARY,
    DAY,
    OAS,
    ONE,
    Q1,
    Q2,
    R1,
    SHOP,
    SOURCE,
    THREE,
    TWO,
    beside,
    centres_at,
    inputs_of,
    place,
)
from .test_venues_nearby import BAR, CAFE, GASTROPUB, PUB, SIDE_BY_SIDE

OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1, OA_R2 = OAS[4], OAS[5]
IN_THE_TOWN = (
    *BY_EVERY_CENTRE,
    *SIDE_BY_SIDE,
    place(beside(Q2, 100), PUB),
    place(beside(Q2, -100), BAR),
    place(beside(Q2, 0, 160), PUB),
    place(beside(R1, 0, 50), PUB),
    # A cafe is no pub, however many stand together.
    *(place(beside(R1, 40.0 * n, -40), CAFE) for n in range(1, 4)),
)


def built(folder: Path, *places: Place, centres: bytes | None = None) -> Exposure:
    inputs = inputs_of(folder, places if places else IN_THE_TOWN, centres)
    return evening_cluster_exposure.build(inputs, spine.build(inputs))


@pytest.fixture
def town(tmp_path: Path) -> Exposure:
    return built(tmp_path)


def test_a_cluster_is_three_or_more_pubs_or_bars_within_150_metres_of_home(town: Exposure):
    assert (METRES, FEWEST) == (150, 3)
    assert town.within[OA_Q1] == 3
    # Two stand within 150 metres of Q2, and the third is 160 metres off.
    assert town.within[OA_Q2] == 2
    assert town.within[OA_R1] == 1 and town.within[OA_R2] == 0
    assert set(town.within) == set(OAS) and town.nothing_seen == ()


def test_the_figure_is_the_share_of_the_areas_homes_that_stand_among_three_or_more(
    town: Exposure,
):
    # Of 500 homes, the 110 of Q1 stand among three. The 120 of Q2 stand among two.
    assert town.worked[ONE] == Worked(22.0, 4, 4, 1.0, State.PRESENT)
    assert town.worked[TWO] == Worked(0.0, 4, 4, 1.0, State.PRESENT)
    assert town.worked[THREE] == Worked(0.0, 4, 4, 1.0, State.PRESENT)


def test_a_third_pub_ten_metres_nearer_makes_a_cluster(tmp_path: Path):
    nearer = (*IN_THE_TOWN, place(beside(Q2, 0, -150), PUB))
    found = built(tmp_path, *nearer)
    assert found.within[OA_Q2] == 3
    assert found.worked[ONE].value == round(100 * (110 + 120) / 500, 1) == 46.0


def test_records_of_one_pub_are_one_pub_and_make_no_cluster(tmp_path: Path):
    """Three records of one door, as a pub, as a bar and as a gastropub."""
    found = built(
        tmp_path, *BY_EVERY_CENTRE, place(Q1, PUB), place(Q1, BAR), place(beside(Q1, 5), GASTROPUB)
    )
    assert found.within[OA_Q1] == 1 and found.worked[ONE].value == 0.0


def test_a_home_at_the_edge_of_london_has_its_verdict(tmp_path: Path):
    """The figure counts no home outside London, and the file reaches beyond the edge."""
    found = built(tmp_path, centres=centres_at(outside=beside(Q1, 100)))
    assert found.within[OA_Q1] == 3
    assert found.worked[ONE] == Worked(22.0, 4, 4, 1.0, State.PRESENT)


def test_where_the_file_holds_nothing_at_all_within_reach_nothing_is_known(tmp_path: Path):
    found = built(tmp_path, *SIDE_BY_SIDE, place(beside(R1, 50), SHOP))
    assert OA_R2 in found.nothing_seen and OA_R2 not in found.within
    assert found.within[OA_Q1] == 3 and found.within[OA_R1] == 0
    # Q2, Q3 and Q4 have no verdict, so the area stands on under half of its homes.
    assert found.worked[ONE].value is None
    assert found.worked[ONE].state is State.BELOW_THRESHOLD


def test_every_area_has_a_row_that_holds_the_figure_and_names_the_files_behind_it(
    town: Exposure,
):
    assert [row.fact_id for row in town.rows] == [
        f"{area}/feature/evening_cluster_exposure" for area in sorted(town.worked)
    ]
    for row in town.rows:
        area = row.fact_id.split("/")[0]
        assert row.value == town.worked[area].value and row.state is town.worked[area].state
    assert {row.derivation_id for row in town.rows} == {"homes_within_150m@1"}
    assert METHOD.derivation_id == "homes_within_150m@1"
    assert sorted(receipt.source_id for receipt in town.files) == [
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        SOURCE,
    ]
    assert Evidence.of("lon-2026-10-02-01", town.files, (METHOD,), town.rows)


def test_core_names_the_measure_as_it_is_built_so_a_build_carries_it(town: Exposure):
    metric, core = town.metric, FEATURES[FeatureId.EVENING_CLUSTER_EXPOSURE]
    assert says_what_core_says(metric)
    assert metric.label == core.label == evening_cluster_exposure.LABEL
    assert "three or more pubs or bars within 150 m" in metric.label
    assert (metric.unit, metric.polarity) == ("%", Polarity.LESS)
    assert metric.native_resolution is NativeResolution.OA and metric.rankable
    assert metric.vintage == DAY and SOURCE in metric.source_ids
    assert metric.definition.endswith(".") and not re.search(r"[!?\n]", metric.definition)
    for words in ("three or more pubs or bars within 150 metres", "within 800 metres", DAY):
        assert words in metric.definition
    (listed,) = [one for one in measures.MEASURES if one.feature is metric.feature_id]
    assert (listed.source, listed.methods) == (SOURCE, (METHOD,))
    assert not (listed.waits_on or listed.held_back or listed.in_parts or listed.in_squares)


def test_it_is_a_nuisance_that_quiet_streets_reads_from_its_low_end():
    assert FeatureId.EVENING_CLUSTER_EXPOSURE in NUISANCES
    parts = {term.feature_id: term for term in TAGS[TagId.QUIET_RESIDENTIAL].terms}
    part = parts[FeatureId.EVENING_CLUSTER_EXPOSURE]
    assert (part.hundredths, part.reading) == (30, TermReading.LOW)


def test_what_the_figure_cannot_see_is_said_in_whole_sentences():
    assert len(CANNOT_SEE) == len(set(CANNOT_SEE)) == 12
    for said in CANNOT_SEE:
        assert re.fullmatch(r"[A-Z][^!\n|]+\.", said), said
    together = " ".join(CANNOT_SEE)
    for words in (
        "taken for a cluster",
        "A nightclub",
        "how late a pub or a bar is open",
        "not the day of each record",
        "fewer than three",
    ):
        assert words in together
    assert venues_nearby.THIN_AT_THE_EDGE in CANNOT_SEE


def test_with_no_file_of_places_there_is_no_figure_and_nothing_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    with pytest.raises(LockError) as refused:
        evening_cluster_exposure.build(inputs, spine.build(inputs))
    assert refused.value.rule == "input_has_one_receipt"


def test_nothing_the_measure_gives_back_holds_a_name_of_a_place(town: Exposure):
    assert CANARY not in repr(town)


def test_the_order_of_the_rows_of_a_file_changes_no_figure(tmp_path: Path):
    one = built(tmp_path / "a", *IN_THE_TOWN)
    other = built(tmp_path / "b", *reversed(IN_THE_TOWN))
    assert (one.worked, one.within) == (other.worked, other.within)
