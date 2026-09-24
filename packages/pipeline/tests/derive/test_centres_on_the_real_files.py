"""The measures of town centres, worked out from the file its publisher gave.

Every other test of the three measures runs on made-up centres. These read the
real file, and are skipped where it cannot be read: where the store of fetched
files is not, and where the file has no receipt in `data/receipts/`. The store
is named by BURRO_STORE_FOLDER.

What they hold of the file is what `docs/research/data/m3-files.md` records of
it: how many centres it holds, and how large they are. What they hold of the
figures is London's lowest, middle and highest for each measure, and how many
areas have a figure. None is said of a named area or of a borough. Each was
worked out on 2026-09-24, by a program, from the boundaries as the publisher's
file held them on 2025-12-22. No person has checked one.

Greater London Authority - Contains public sector information licensed under
the Open Government Licence v3.0. Contains OS data © Crown copyright and
database rights 2019. The Greater London Authority cannot warrant the quality
or accuracy of the data. Source: Office for National Statistics licensed under
the Open Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import statistics
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.shapes import pieces
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import centre_compact, centre_small, highstreet_access, town_centres
from burro_pipeline.derive.town_centres import Found
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.row import HAS_A_VALUE
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and (RECEIPTS / town_centres.SOURCE).is_dir()),
    reason="the town centres cannot be read here: the store is not named, or the file has "
    "no receipt",
)
# What the file was counted to hold: its centres, and the least, the middle and the most of
# the ground they cover, in hectares.
CENTRES, LEAST, MIDDLE, MOST = 234, 0.95, 9.93, 258.96
AREAS, OUTPUT_AREAS = 1_002, 26_369
# How many of the centres cover under 10 hectares, and how many are drawn in more than one
# piece.
SMALL, IN_PIECES = 118, 37
# Of London's output areas: how many stand nearer to homes beyond London than to any centre
# of the file, and how many have a centre of the file within 800 metres.
BEYOND, WITHIN_REACH = 717, 17_772
# What each measure came to on 2026-09-24: how many areas have a figure, and the lowest,
# the middle and the highest of them.
FIGURES = {
    "highstreet_access": (976, 0.0, 530.0, 2_770.0),
    "centre_small": (682, 0.0, 10.3, 100.0),
    "centre_compact": (682, 3.3, 23.1, 62.9),
}
# Of the 682 areas with a figure for a small centre, how many read nought and how many 100.
NOUGHT, ALL = 317, 158


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def centres(real: Inputs, found: Spine) -> Found:
    return town_centres.build(real, found)


@pytest.fixture(scope="module")
def values(real: Inputs, found: Spine) -> dict[str, list[float]]:
    """The figures of each measure, for the areas that have one."""
    made = {
        "highstreet_access": highstreet_access.build(real, found),
        "centre_small": centre_small.build(real, found),
        "centre_compact": centre_compact.build(real, found),
    }
    return {
        name: sorted(one.value for one in each.worked.values() if one.value is not None)
        for name, each in made.items()
    }


# The file


def test_the_file_holds_as_many_centres_as_were_counted(centres: Found):
    assert len(centres.centres) == CENTRES


def test_about_half_the_centres_are_small_and_some_are_drawn_in_pieces(centres: Found):
    held = centres.centres.values()
    assert sum(one.hectares < centre_small.SMALL_UNDER for one in held) == SMALL
    assert sum(pieces(one.shape) > 1 for one in held) == IN_PIECES


def test_the_centres_cover_as_much_ground_as_was_counted(centres: Found):
    sizes = sorted(one.hectares for one in centres.centres.values())
    assert sizes[0] == pytest.approx(LEAST, rel=town_centres.AS_DRAWN)
    assert statistics.median(sizes) == pytest.approx(MIDDLE, rel=town_centres.AS_DRAWN)
    assert sizes[-1] == pytest.approx(MOST, rel=town_centres.AS_DRAWN)


def test_every_centre_fills_some_of_the_circle_round_it_and_none_fills_more_than_all(
    centres: Found,
):
    assert all(0 < one.fills <= 1 for one in centres.centres.values())


def test_every_home_of_london_is_placed_and_most_have_a_nearest_centre(
    centres: Found, found: Spine
):
    assert centres.placed == len(found.area_of) == OUTPUT_AREAS
    assert len(centres.nearest) + centres.may_be_nearer_beyond == OUTPUT_AREAS
    # A home at the edge of London may have a nearer centre beyond it. Most homes are not there.
    assert centres.may_be_nearer_beyond < OUTPUT_AREAS / 2


def test_a_third_of_londons_output_areas_have_no_centre_of_the_file_within_reach(
    centres: Found,
):
    assert centres.may_be_nearer_beyond == BEYOND
    assert len(town_centres.within_reach(centres)) == WITHIN_REACH
    assert 0.32 < 1 - WITHIN_REACH / OUTPUT_AREAS < 0.33


# The figures


@pytest.mark.parametrize("measure", sorted(FIGURES))
def test_a_measure_comes_to_what_it_came_to(values: dict[str, list[float]], measure: str):
    held = values[measure]
    found = (len(held), held[0], round(statistics.median(held), 1), held[-1])
    assert found == FIGURES[measure]


def test_most_areas_with_a_figure_for_a_small_centre_read_nought_or_100(
    values: dict[str, list[float]],
):
    """An area mostly has one centre near, which is small or is not."""
    held = values["centre_small"]
    assert (held.count(0.0), held.count(100.0)) == (NOUGHT, ALL)
    assert 0.69 < (NOUGHT + ALL) / len(held) < 0.70


def test_every_area_has_a_row_for_each_measure_and_every_figure_is_one_that_can_be(
    real: Inputs, found: Spine
):
    far = highstreet_access.build(real, found)
    small = centre_small.build(real, found)
    compact = centre_compact.build(real, found)
    for made in (far, small, compact):
        assert len(made.worked) == len(made.rows) == AREAS
        assert any(one.value is not None for one in made.worked.values())
        for one in made.worked.values():
            assert (one.value is not None) == (one.state in HAS_A_VALUE)
    assert all(one.value is None or one.value >= 0 for one in far.worked.values())
    for made in (small, compact):
        assert all(one.value is None or 0 <= one.value <= 100 for one in made.worked.values())


def test_a_measure_of_the_size_or_the_shape_of_a_centre_counts_only_homes_with_one_near(
    real: Inputs, found: Spine
):
    far = highstreet_access.build(real, found)
    small = centre_small.build(real, found)
    compact = centre_compact.build(real, found)
    near = {oa for oa, metres in far.of_oa.items() if metres <= town_centres.REACH}
    assert set(small.of_oa) == set(compact.of_oa) == near


def test_built_twice_the_figures_are_the_same(real: Inputs, found: Spine):
    first = centre_compact.build(real, found)
    again = centre_compact.build(real, found)
    assert first.worked == again.worked and first.rows == again.rows


# The store


def test_nothing_was_written_to_the_store(centres: Found, before: dict[str, tuple[int, int]]):
    assert centres.files
    assert listing() == before
