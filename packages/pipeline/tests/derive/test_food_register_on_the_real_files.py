"""The food register, read from the files its publisher gave.

Every other test of the parser runs on a made-up register. These read the 33
real files, and are skipped where the store of fetched files is not. The store
is named by BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold counts, so that a file that changes is noticed. A count is of all of
London, or the least and the most of the 33 files. No business is named, and
nothing of one is held: no name, no address and no rating. Each count was made
on 2026-09-24, from the extracts of 2026-09-09 to 2026-09-16.

Contains public sector information licensed under the Open Government Licence
v3.0. Source: Food Standards Agency.

Nothing is written to the store. A file is copied out of it to be read.
"""

from pathlib import Path

import pytest
from burro_pipeline.derive import food_register
from burro_pipeline.derive.food_register import KINDS, Group, Register
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.inputs import Inputs

from .food_real_files import SKIPPED, STORE, listing, real_inputs

pytestmark = SKIPPED


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Register:
    return food_register.build(real)


def test_the_register_is_a_file_for_each_of_33_authorities(found: Register):
    assert len(found.extracts) == len(found.files) == 33
    assert [one.authority for one in found.extracts] == [str(code) for code in range(501, 534)]
    assert [receipt.publisher_file for receipt in found.files] == [
        f"FHRS{code}en-GB.xml" for code in range(501, 534)
    ]


def test_every_file_holds_as_many_businesses_as_its_header_says(found: Register):
    """The parser stops at a file that does not. So what was read is the register's own count."""
    counts = sorted(one.businesses for one in found.extracts)
    assert (sum(counts), counts[0], counts[-1]) == (81_529, 1_318, 5_732)
    for one in found.extracts:
        assert sum(one.listed.values()) == one.businesses


def test_the_extracts_run_from_the_ninth_to_the_sixteenth_of_september(found: Register):
    assert found.period == Period(start="2026-09-09", end="2026-09-16")
    assert found.as_at == "2026-09-09 to 2026-09-16"
    assert sum(one.day == "2026-09-16" for one in found.extracts) == 24


def test_london_holds_so_many_businesses_of_each_kind(found: Register):
    of_kind = {
        KINDS[kind][0]: sum(one.listed[kind] for one in found.extracts) for kind in sorted(KINDS)
    }
    assert of_kind == {
        "Restaurant/Cafe/Canteen": 27_262,
        "Importers/Exporters": 278,
        "Retailers - other": 16_733,
        "Hospitals/Childcare/Caring Premises": 4_682,
        "Distributors/Transporters": 669,
        "Farmers/growers": 33,
        "Manufacturers/packers": 1_136,
        "Retailers - supermarkets/hypermarkets": 2_319,
        "Other catering premises": 8_053,
        "Hotel/bed & breakfast/guest house": 972,
        "Pub/bar/nightclub": 3_866,
        "Takeaway/sandwich shop": 9_430,
        "School/college/university": 3_501,
        "Mobile caterer": 2_595,
    }


def test_about_one_business_in_six_has_no_point_and_is_put_nowhere(found: Register):
    assert len(found.places) == 67_268
    assert sum(found.listed(group) - found.placed(group) for group in Group) == 14_261
    listed = {group.value: (found.listed(group), found.placed(group)) for group in Group}
    assert listed == {
        "eat": (27_262, 24_671),
        "pub": (3_866, 3_565),
        "takeaway": (9_430, 8_777),
        "shop": (19_052, 17_247),
        "none": (21_919, 13_008),
    }


def test_how_many_places_to_eat_have_a_point_differs_from_one_authority_to_the_next(
    found: Register,
):
    """It is the widest of the three kinds. An authority that gives few points reads low."""
    shares = sorted(
        round(100 * one.with_a_point(Group.EAT) / one.of(Group.EAT)) for one in found.extracts
    )
    assert (shares[0], shares[len(shares) // 2], shares[-1]) == (55, 95, 98)
    assert sum(share < 80 for share in shares) == 5


def test_every_point_is_a_point_of_the_earth_and_most_are_in_london(found: Register):
    on_the_earth = sum(
        -180 <= place.longitude <= 180 and -90 <= place.latitude <= 90 for place in found.places
    )
    # A box drawn wide round London. A business may be listed by an authority it is not in.
    in_the_box = sum(
        -0.6 < place.longitude < 0.4 and 51.2 < place.latitude < 51.8 for place in found.places
    )
    assert (on_the_earth, in_the_box) == (67_268, 67_248)


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, found: Register, before: dict[str, tuple[int, int]]
):
    assert {one.receipt.source_id for one in real.opened} == {food_register.SOURCE}
    assert len(real.opened) == 33
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
