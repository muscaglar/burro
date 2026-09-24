"""The stations as places, made from the file a person saved.

Every other test of the places runs on made-up stops. These read the real
file, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and the file is read through its receipt in
`data/receipts/`.

They hold counts, and one name: the station the publisher's own guide takes
for its example of a station. The name of a station is the name of a place. A
name that is also the name of a neighbourhood is found in the rows and is
written nowhere here. Each count was made on 2026-09-24.
"""

from collections import Counter
from typing import cast

import pytest
from burro_core.places import Names, normalise
from burro_core.release import Place, Release
from burro_pipeline.derive import station_places
from burro_pipeline.derive.station_places import Places

from .real_files import SKIPPED, real_inputs
from .test_station_places import Held

pytestmark = SKIPPED
# What a person might type for the station the publisher's guide takes for its example.
TYPED = ("Bank", "bank station")


@pytest.fixture(scope="module")
def made(tmp_path_factory: pytest.TempPathFactory) -> Places:
    return station_places.build(real_inputs(tmp_path_factory.mktemp("real")))


@pytest.fixture(scope="module")
def names(made: Places) -> Names:
    """The rows as core would hold them. The journey's end is made up: no build makes one."""
    held = tuple(
        Place(
            place_id=row.place_id,
            name=row.name,
            aliases=row.aliases,
            kind=row.kind,
            destination_id="lon-d0",
            coarse_place_id=row.place_id,
            centroid=row.centroid,
            source_id=row.source_id,
        )
        for row in made.places
    )
    return Names(cast(Release, Held(held)))


def test_the_file_makes_641_places_and_every_one_is_a_station(made: Places):
    assert len(made.places) == len({place.place_id for place in made.places}) == 641
    assert Counter(place.served for place in made.places) == {
        "rail": 340,
        "tram_metro_underground": 301,
    }
    assert (made.saved, made.file.file_id) == ("2026-09-24", "f-ed03193db0d8")


def test_the_letters_of_the_codes_give_a_network_to_296_of_them(made: Places):
    assert Counter(place.network for place in made.places) == {
        None: 345,
        "underground": 215,
        "dlr": 42,
        "tram": 37,
        "cable_car": 2,
    }


def test_every_place_stands_in_or_beside_london(made: Places):
    longitudes = [place.centroid[0] for place in made.places]
    latitudes = [place.centroid[1] for place in made.places]
    assert -0.49 < min(longitudes) < max(longitudes) < 0.26
    assert 51.31 < min(latitudes) < max(latitudes) < 51.69


def test_every_place_has_an_alias_and_71_answer_to_a_name_another_answers_to(made: Places):
    assert all(place.aliases for place in made.places)
    assert sum(place.shares_a_name for place in made.places) == 71
    spelt: Counter[str] = Counter()
    for place in made.places:
        spelt.update({normalise(one) for one in (place.name, *place.aliases)})
    assert max(spelt.values()) == 3


def test_the_rows_hold_605_names_and_35_of_them_are_a_row_of_each_kind(made: Places):
    """A station that is a railway station and an underground station is a row of each kind."""
    served: dict[str, list[str]] = {}
    for place in made.places:
        served.setdefault(normalise(station_places.bare(place.name)), []).append(place.served)
    assert Counter(len(kinds) for kinds in served.values()) == {1: 570, 2: 34, 3: 1}
    of_each_kind = [kinds for kinds in served.values() if len(set(kinds)) == 2]
    # One name is three rows: the file holds two stations of the second kind under it.
    assert Counter(len(kinds) for kinds in of_each_kind) == {2: 34, 3: 1}


def test_the_words_a_person_types_name_one_station(made: Places, names: Names):
    for typed in TYPED:
        found = names.exact_place(typed).resolved
        assert found is not None and names.resolve_place(typed).resolved == found
        (place,) = [place for place in made.places if place.place_id == found]
        assert (place.name, place.served, place.network) == (
            "Bank",
            "tram_metro_underground",
            "underground",
        )
        assert len(place.codes) == 13 and not place.shares_a_name


def test_a_name_with_no_station_of_its_own_is_offered_and_not_taken(made: Places, names: Names):
    """Three stations answer to one name. Core offers them, and takes none without asking.

    The name is read from the rows: it is what the most rows answer to, with
    "station" after it and without.
    """
    spelt: Counter[str] = Counter()
    for place in made.places:
        spelt.update({normalise(one) for one in (place.name, *place.aliases)})
    typed = sorted(spelling for spelling, rows in spelt.items() if rows == 3)
    assert len(typed) == 2
    for words in typed:
        most = names.resolve_place(words)
        assert most.resolved is None and len(most.options) == 3
