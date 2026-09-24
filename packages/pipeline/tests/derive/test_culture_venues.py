"""Culture nearby, from the file of places to a figure for each area.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places. The centres stand 1,000 metres apart, so that a home is
within reach of what stands by its own centre and of little else, and every
count can be made by hand:

    Quillhaven 001   Q1  a museum, a gallery and a theatre, each 100 metres off
                     Q2  a cinema, 500 metres east, half way to Q3
                     Q3  the same cinema, 500 metres west
                     Q4  a library 790 metres north. A music venue 810 metres north is out of reach
    Quillhaven 002   R1  a library. R2, R3 and R4 have nothing within reach
    Tallowgate 001   T1  two museums and a gallery. T2, T3 and T4 have nothing

Beside Q1 stand six records that are not counted: a cafe, a bookshop, a record
that says no more than that it is a stage of some sort, a choir, a theatre that
says it teaches, and a museum that has closed. A bookshop stands by every
centre, so that the file is seen to hold something within reach of every home.
"""

import re
from pathlib import Path

import pytest
from burro_core.catalogue import FEATURES
from burro_core.ids import FeatureId, NativeResolution, Polarity
from burro_pipeline.cells import spine
from burro_pipeline.derive import culture_venues, culture_venues_per_homes, measures
from burro_pipeline.derive.culture_file import Venue
from burro_pipeline.derive.culture_kinds import KINDS, Kind
from burro_pipeline.derive.culture_venues import (
    CANNOT_SEE,
    CANNOT_SEE_OF_THE_KINDS,
    CANNOT_SEE_OF_THE_RATE,
    EVERY,
    METRES,
    OF_THE_RELEASE,
    ONE_VENUE,
    ONE_VENUE_WORDS,
    Culture,
    as_venues,
)
from burro_pipeline.derive.methods import Worked
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Geography
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence

from ..fetch.parquet_support import Place
from .culture_support import (
    CAFE,
    CANARY,
    CINEMA,
    DAY,
    GALLERY,
    IN_THE_TOWN,
    LIBRARY,
    MUSEUM,
    MUSIC,
    OAS,
    ONE,
    Q1,
    Q2,
    Q4,
    R1,
    R2,
    SOURCE,
    THEATRE,
    THREE,
    TWO,
    beside,
    centres_at,
    inputs_of,
    place,
)

OA_Q1, OA_Q2, OA_Q3, OA_Q4 = OAS[:4]
OA_R1, OA_R2, OA_T1 = OAS[4], OAS[5], OAS[8]
ALL = range(len(KINDS))


def built(folder: Path, *places: Place, centres: bytes | None = None, **how: object) -> Culture:
    given = places if places else IN_THE_TOWN
    inputs = inputs_of(folder, given, centres, **how)  # pyright: ignore[reportArgumentType]
    return culture_venues.build(inputs, spine.build(inputs))


@pytest.fixture
def town(tmp_path: Path) -> Culture:
    return built(tmp_path)


def value_of(worked: Worked) -> float:
    assert worked.value is not None
    return worked.value


# What is within reach


def test_each_home_is_given_the_venues_within_reach_of_its_own_centre(town: Culture):
    reach = town.reach
    assert reach.metres == METRES == 800
    assert reach.of(ALL)[OA_Q1] == 3.0
    assert reach.of(ALL)[OA_Q2] == reach.of(ALL)[OA_Q3] == 1.0
    assert reach.of(ALL)[OA_R1] == 1.0 and reach.of(ALL)[OA_T1] == 3.0
    assert reach.of(ALL)[OA_R2] == 0.0


def test_a_venue_790_metres_off_on_the_grid_is_within_reach_and_one_810_off_is_not(
    town: Culture,
):
    library, music = KINDS.index(Kind.LIBRARY), KINDS.index(Kind.MUSIC_VENUE)
    assert town.reach.within[OA_Q4][library] == 1
    assert town.reach.within[OA_Q4][music] == 0


def test_what_is_not_a_venue_of_culture_is_not_counted(town: Culture):
    """Seven records stand beside Q1 that are no venue. Three that are stand there too."""
    assert town.reach.of(ALL)[OA_Q1] == 3.0
    assert town.reach.of((EVERY,))[OA_Q1] == 10.0


def test_the_figure_of_an_area_is_the_mean_over_its_homes(town: Culture):
    by_hand = (110 * 3 + 120 + 130 + 140) / 500
    assert value_of(town.worked[ONE]) == round(by_hand, 1) == 1.4
    assert value_of(town.worked[TWO]) == round(150 / 660, 1) == 0.2
    assert value_of(town.worked[THREE]) == round(190 * 3 / 820, 1) == 0.7
    assert {one.state for one in town.worked.values()} == {State.PRESENT}


def test_the_second_figure_is_for_each_1000_homes_within_the_same_reach(town: Culture):
    top = 110 * 3 + 120 + 130 + 140
    bottom = 110 * 110 + 120 * 120 + 130 * 130 + 140 * 140
    assert value_of(town.rate[ONE]) == round(1_000 * top / bottom, 1) == 11.4


def test_the_third_figure_is_how_many_of_the_six_kinds_are_within_reach(town: Culture):
    """Q1 has three kinds within reach, and Q2, Q3 and Q4 one each."""
    by_hand = (110 * 3 + 120 + 130 + 140) / 500
    assert value_of(town.kinds[ONE]) == round(by_hand, 1)
    # Tallowgate has two museums and a gallery by T1: three venues, of two kinds.
    assert value_of(town.kinds[THREE]) == round(190 * 2 / 820, 1) == 0.5
    assert value_of(town.worked[THREE]) == 0.7


# One venue with many records


def test_records_of_one_kind_that_stand_together_are_one_venue(tmp_path: Path):
    """A museum with four records, within 25 metres of the first. It counts once."""
    found = built(
        tmp_path,
        place(Q1, MUSEUM),
        place(beside(Q1, 10), MUSEUM),
        place(beside(Q1, 0, 20), MUSEUM),
        place(beside(Q1, 24), ("arts_and_entertainment", "museum", "art_museum")),
        place(beside(Q2, 0), CAFE),
    )
    assert ONE_VENUE == 25
    assert len(found.places.venues) == 4 and len(found.venues) == 1
    assert found.reach.of(ALL)[OA_Q1] == 1.0
    assert found.records_of_one_venue == {Kind.MUSEUM: 3}


def test_five_records_of_one_institution_on_one_spot_count_once(tmp_path: Path):
    found = built(tmp_path, *(place(Q1, MUSEUM) for _ in range(5)), place(Q2, CAFE))
    assert len(found.places.venues) == 5 and len(found.venues) == 1
    assert found.reach.of(ALL)[OA_Q1] == 1.0
    assert found.records_of_one_venue == {Kind.MUSEUM: 4}


def test_records_on_one_spot_are_one_venue_whether_or_not_each_says_how_sure_it_is(
    tmp_path: Path,
):
    """Some records give no number for how sure the publisher is. The build does not stop."""
    records = [
        place(Q1, MUSEUM, confidence=None),
        place(Q1, MUSEUM, confidence=0.9),
        place(Q1, MUSEUM, confidence=None),
        place(Q1, MUSEUM, confidence=0.4),
        place(Q1, MUSEUM),
    ]
    one = built(tmp_path / "a", *records, place(Q2, CAFE))
    other = built(tmp_path / "b", place(Q2, CAFE), *reversed(records))
    assert len(one.places.venues) == 5 and len(one.venues) == 1
    assert one.venues == other.venues
    assert one.records_of_one_venue == {Kind.MUSEUM: 4}


def test_records_are_put_in_one_order_though_some_do_not_say_how_sure_they_are():
    """A record that gives no number stands before one on the same spot that gives one."""
    here = (2.5, 53.5, Kind.MUSEUM, ("meta",))
    records = [Venue(*here, 0.9), Venue(*here, None), Venue(*here, 0.4)]
    (venue,), again = as_venues(records)
    assert again == {Kind.MUSEUM: 2}
    assert as_venues(list(reversed(records))) == ((venue,), again)
    assert venue.confidence is None


def test_venues_of_two_kinds_on_one_spot_are_two_venues(tmp_path: Path):
    found = built(tmp_path, place(Q1, MUSEUM), place(Q1, LIBRARY), place(Q1, THEATRE))
    assert len(found.venues) == 3
    assert found.reach.how_many_of(ALL)[OA_Q1] == 3.0


def test_two_venues_of_one_kind_further_apart_are_two(tmp_path: Path):
    found = built(tmp_path, place(Q1, GALLERY), place(beside(Q1, 26), GALLERY))
    assert len(found.venues) == 2


def test_a_record_is_held_to_the_first_of_its_venue_and_the_words_beside_a_figure_say_so(
    tmp_path: Path,
):
    """Three galleries stand 0, 24 and 26 metres east. The second is the first again. The
    third is 2 metres from the second and 26 from the first, and is a venue of its own."""
    row = [place(beside(Q1, east), GALLERY) for east in (0.0, 24.0, 26.0)]
    assert len(built(tmp_path, *row).venues) == 2
    assert f"within {ONE_VENUE} metres of the first of them" in ONE_VENUE_WORDS
    assert "of each other" not in ONE_VENUE_WORDS


def test_which_records_are_one_venue_does_not_turn_on_the_order_of_the_file(tmp_path: Path):
    row = [place(beside(Q1, 20.0 * n), GALLERY) for n in range(10)]
    one = built(tmp_path / "a", *row)
    other = built(tmp_path / "b", *reversed(row))
    assert one.venues == other.venues and len(one.venues) == 5


def test_a_venue_keeps_every_source_that_gave_a_record_of_it(tmp_path: Path):
    found = built(
        tmp_path,
        place(Q1, MUSEUM, dataset="meta"),
        place(beside(Q1, 5), MUSEUM, dataset="Foursquare"),
    )
    (venue,) = found.venues
    assert venue.datasets == ("Foursquare", "meta")


def test_as_venues_is_handed_records_and_reads_no_file():
    assert as_venues(()) == ((), {})


# When nought is a count


def test_nought_is_a_count_where_the_file_holds_something_within_reach(tmp_path: Path):
    """A cafe stands by R2 and no venue does. The file is seen to hold the place: nought."""
    found = built(tmp_path, place(Q1, MUSEUM), place(R2, CAFE))
    assert found.reach.of(ALL)[OA_R2] == 0.0
    assert OA_R2 not in found.nothing_seen


def test_where_the_file_holds_nothing_at_all_within_reach_nothing_is_known(tmp_path: Path):
    """Nothing of any kind stands by R2, R3 or R4. A gap cannot be told from none."""
    found = built(tmp_path, place(Q1, MUSEUM), place(beside(R1, 50), CAFE))
    assert set(found.nothing_seen) >= {OA_R2}
    assert OA_R2 not in found.counted
    assert found.worked[TWO].value is None or found.worked[TWO].weight_covered < 1
    assert found.worked[ONE].weight_covered < 1
    assert found.worked[ONE].state in (State.PARTIAL, State.BELOW_THRESHOLD)


def test_a_home_with_a_venue_within_reach_is_never_left_out_for_want_of_anything_else(
    tmp_path: Path,
):
    found = built(tmp_path, place(Q1, MUSEUM))
    assert found.counted[OA_Q1] == 1.0


# The edge of London


def test_an_output_area_with_homes_outside_london_within_reach_has_no_count(tmp_path: Path):
    found = built(tmp_path, centres=centres_at(outside=beside(Q4, 500)))
    assert found.reach.near_the_edge == (OA_Q4,)
    assert found.worked[ONE].state is State.PARTIAL
    assert value_of(found.worked[ONE]) == round((110 * 3 + 120 + 130) / 360, 1)


# The evidence


def test_every_area_has_a_row_for_each_figure_that_holds_the_figure(town: Culture):
    for rows, worked, key in (
        (town.rows, town.worked, "culture_venues"),
        (town.rows_of_the_rate, town.rate, "culture_venues_per_homes"),
        (town.rows_of_the_kinds, town.kinds, "culture_kinds_nearby"),
    ):
        assert [row.fact_id for row in rows] == [f"{area}/feature/{key}" for area in sorted(worked)]
        for row in rows:
            area = row.fact_id.split("/")[0]
            assert row.value == worked[area].value and row.state is worked[area].state


def test_a_row_names_the_file_of_places_the_centres_and_the_homes(town: Culture):
    sources = {receipt.file_id: receipt.source_id for receipt in town.files}
    assert sorted(sources.values()) == [
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        SOURCE,
    ]
    for row in (*town.rows, *town.rows_of_the_rate, *town.rows_of_the_kinds):
        assert set(row.inputs) == set(sources)


def test_each_figure_names_the_method_it_was_made_by(town: Culture):
    count, rate, kinds = culture_venues.METHODS
    assert {row.derivation_id for row in town.rows} == {count.derivation_id}
    assert {row.derivation_id for row in town.rows_of_the_rate} == {rate.derivation_id}
    assert {row.derivation_id for row in town.rows_of_the_kinds} == {kinds.derivation_id}
    assert len({count.derivation_id, rate.derivation_id, kinds.derivation_id}) == 3


def test_the_rows_are_ones_the_evidence_of_a_release_would_hold(town: Culture):
    rows = (*town.rows, *town.rows_of_the_rate, *town.rows_of_the_kinds)
    evidence = Evidence.of("lon-2026-10-02-01", town.files, culture_venues.METHODS, rows)
    assert len(evidence.rows) == 9


def test_the_period_of_a_figure_runs_from_the_census_to_the_release(town: Culture):
    (row, *_) = town.rows
    assert row.data_period is not None
    assert row.data_period.days() == ("2021-03-21", DAY)


def test_the_places_are_keyed_by_a_point(town: Culture):
    assert town.geography is Geography.POINT


# The name, the unit and the sentences


def test_core_names_the_count_and_the_rate_as_they_are_measured_so_a_build_carries_both(
    town: Culture,
):
    """The count is within reach of homes, and is shown. A wish is ranked on the rate."""
    assert culture_venues.KEY == "culture_venues" == FeatureId.CULTURE_VENUES
    assert culture_venues.KEY_OF_THE_RATE == FeatureId.CULTURE_VENUES_PER_HOMES
    assert culture_venues.core_holds_it()
    count, rate = FEATURES[FeatureId.CULTURE_VENUES], FEATURES[FeatureId.CULTURE_VENUES_PER_HOMES]
    assert (count.label, count.unit) == (culture_venues.LABEL, culture_venues.UNIT)
    assert (rate.label, rate.unit) == (
        culture_venues.LABEL_OF_THE_RATE,
        culture_venues.UNIT_OF_THE_RATE,
    )
    assert measures.says_what_core_says(town.metric)
    assert measures.says_what_core_says(town.metric_of_the_rate)
    assert (town.metric.rankable, town.metric_of_the_rate.rankable) == (False, True)
    for_each_square_kilometre = town.metric.model_copy(update={"unit": "per km²"})
    assert not measures.says_what_core_says(for_each_square_kilometre)
    listed = {measure.feature: measure for measure in measures.MEASURES}
    for feature in (FeatureId.CULTURE_VENUES, FeatureId.CULTURE_VENUES_PER_HOMES):
        assert (listed[feature].source, listed[feature].waits_on) == (SOURCE, ())


def test_the_rate_is_a_measure_of_a_build_with_the_rows_and_the_words_of_the_second_figure(
    tmp_path: Path, town: Culture
):
    inputs = inputs_of(tmp_path / "again", IN_THE_TOWN, None)
    rate = culture_venues_per_homes.build(inputs, spine.build(inputs))
    assert rate.worked == town.rate
    assert [row.fact_id for row in rate.rows] == [row.fact_id for row in town.rows_of_the_rate]
    assert rate.metric == town.metric_of_the_rate
    assert rate.metric.feature_id is FeatureId.CULTURE_VENUES_PER_HOMES
    assert culture_venues_per_homes.CANNOT_SEE == CANNOT_SEE_OF_THE_RATE
    assert culture_venues_per_homes.METHODS == (culture_venues.METHOD_OF_THE_RATE,)


def test_core_holds_no_measure_of_the_kinds():
    known = {feature.value for feature in FeatureId}
    assert culture_venues.KEY_OF_THE_KINDS not in known


def test_the_rows_the_catalogue_needs_say_what_is_measured(town: Culture):
    count, rate, kinds = town.proposed
    assert count.label == (
        "Museums, galleries, theatres, cinemas, music venues and libraries within 800 m of "
        "home, in a straight line"
    )
    assert rate.label == (
        "Museums, galleries, theatres, cinemas, music venues and libraries for each 1,000 "
        "homes within 800 m, in a straight line"
    )
    assert kinds.label == "Kinds of cultural venue within 800 m of home, in a straight line, of 6"
    assert (count.unit, rate.unit, kinds.unit) == ("count", "per 1,000 homes", "kinds")
    for row in town.proposed:
        assert row.polarity is Polarity.MORE
        assert row.native_resolution is NativeResolution.POINT
        assert row.source_ids == tuple(sorted({receipt.source_id for receipt in town.files}))
        assert row.vintage == DAY


def test_the_rate_alone_is_ranked_on(town: Culture):
    """The count is shown beside it, as the count of places to eat and drink is."""
    assert [row.rankable for row in town.proposed] == [False, True, False]


def test_the_sentence_of_a_methods_page_says_what_is_counted_and_what_is_not(town: Culture):
    count, rate, kinds = (row.definition for row in town.proposed)
    for said in (count, rate, kinds):
        assert said.endswith(".") and "!" not in said and "\n" not in said
        assert "Overture Maps Foundation" in said and DAY in said
        assert "800 metres in a straight line" in said
        assert "within 25 metres" in said
        assert "walk" not in said.replace("not along any street", "")
    assert "a museum, a gallery, a theatre, a cinema, a music venue or a library" in count
    assert "for each 1,000 homes" in rate and "kinds" in kinds


def test_the_words_beside_every_figure_say_that_the_day_is_of_the_release():
    """The file states no period. The founder stated the day of the publisher's release, with
    a note that many records are years older, and a figure is never shown without the note."""
    for lines in (CANNOT_SEE, CANNOT_SEE_OF_THE_RATE, CANNOT_SEE_OF_THE_KINDS):
        assert OF_THE_RELEASE in lines
    assert "not the day of each record" in OF_THE_RELEASE
    assert "years before it" in OF_THE_RELEASE


def test_no_word_of_the_measure_says_who_lives_or_goes_anywhere():
    said = " ".join((*CANNOT_SEE, *CANNOT_SEE_OF_THE_RATE, *CANNOT_SEE_OF_THE_KINDS)).lower()
    for word in ("resident", "people who", "affluent", "income", "visitor", "tourist"):
        assert word not in said


def test_what_the_figure_cannot_see_is_said_in_whole_sentences(town: Culture):
    for lines in (CANNOT_SEE, CANNOT_SEE_OF_THE_RATE, CANNOT_SEE_OF_THE_KINDS):
        assert len(lines) == len(set(lines)) >= 3
        for said in lines:
            assert re.fullmatch(r"[A-Z][^!\n|]+\.", said), said
    joined = " ".join(CANNOT_SEE)
    for must in ("closed", "straight line", "category", "25 metres", "census"):
        assert must in joined


def test_the_rate_says_that_it_reads_highest_where_few_homes_are():
    assert any("few homes" in said for said in CANNOT_SEE_OF_THE_RATE)
    assert not any("few homes" in said for said in CANNOT_SEE)


# The files


def test_the_gate_is_asked_of_the_places_and_of_the_centres(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = spine.build(inputs)
    before = {opened.receipt.source_id for opened in inputs.opened}
    culture_venues.build(inputs, found)
    after = {opened.receipt.source_id for opened in inputs.opened}
    assert after - before == {SOURCE, "ons-oa-pwc-2021"}


def test_with_no_file_of_places_there_is_no_figure_and_nothing_is_filled_in(tmp_path: Path):
    inputs = inputs_of(tmp_path, None)
    with pytest.raises(LockError) as stopped:
        culture_venues.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_the_spine_must_be_made_from_files_of_this_build(tmp_path: Path):
    other = spine.build(inputs_of(tmp_path / "other"))
    changed = inputs_of(tmp_path / "this")
    changed.receipts = [
        receipt for receipt in changed.receipts if "lookup" not in receipt.source_id
    ]
    with pytest.raises(ValueError, match="files of this build"):
        culture_venues.build(changed, other)


def test_nothing_the_measure_gives_back_holds_a_name_of_a_place(tmp_path: Path):
    found = built(tmp_path, packed="none")
    assert CANARY not in repr(found)


def test_built_twice_from_the_same_file_the_figures_and_the_rows_are_the_same(tmp_path: Path):
    one, other = built(tmp_path / "a"), built(tmp_path / "b")
    assert (one.worked, one.rate, one.kinds) == (other.worked, other.rate, other.kinds)
    assert (one.rows, one.rows_of_the_rate) == (other.rows, other.rows_of_the_rate)
    assert one.rows_of_the_kinds == other.rows_of_the_kinds


def test_the_order_of_the_rows_of_a_file_changes_no_figure(tmp_path: Path):
    """It is another file, with another hash, so a row names another input. No figure moves."""
    one, other = built(tmp_path / "a"), built(tmp_path / "b", *reversed(IN_THE_TOWN))
    assert (one.worked, one.rate, one.kinds) == (other.worked, other.rate, other.kinds)
    assert one.venues == other.venues
    assert one.places.file.file_id != other.places.file.file_id


def test_a_music_venue_and_a_cinema_are_counted_as_the_others_are(tmp_path: Path):
    found = built(tmp_path, place(Q1, MUSIC), place(beside(Q1, 100), CINEMA))
    assert found.reach.of(ALL)[OA_Q1] == 2.0 and found.reach.how_many_of(ALL)[OA_Q1] == 2.0
