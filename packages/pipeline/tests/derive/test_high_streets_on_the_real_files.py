"""The high streets, and how much of each lies in a conservation area, from the real files.

Every other test of the two modules runs on made-up high streets. These read
the real files, and are skipped where they cannot be read: where the store of
fetched files is not, and where the file of high streets has no receipt in
`data/receipts/`. The store is named by BURRO_STORE_FOLDER.

What they hold of the file is what `docs/research/data/high-streets.md`
records of it: how many high streets it holds, how large they are, and how it
stands to the file of town centres. What they hold of the figures is how many
high streets and how many areas have one, and London's lowest, middle and
highest. None is said of a named high street, of a named area or of a borough.
Each was worked out on 2026-09-25, by a program, from the high streets as the
publisher's file held them on 2025-06-19 and the conservation areas as the
platform held them on 2026-09-24. No person has checked one.

Greater London Authority - Contains public sector information licensed under
the Open Government Licence v3.0. The Greater London Authority cannot warrant
the quality or accuracy of the data. Source: Office for National Statistics
licensed under the Open Government Licence v.3.0.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.areas import names_shapes
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.shapes import hectares, joined, pieces
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    conservation_cover,
    high_streets,
    highstreet_conserved,
    planning_data,
    town_centres,
)
from burro_pipeline.derive.heritage_shapes import box_round, in_degrees, land_shared
from burro_pipeline.derive.highstreet_conserved import Conserved
from burro_pipeline.derive.town_centres import Found
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.row import HAS_A_VALUE, State
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and (RECEIPTS / high_streets.SOURCE).is_dir()),
    reason="the high streets cannot be read here: the store is not named, or the file has "
    "no receipt",
)
# What the file was counted to hold: its rows, its high streets, and how many of them are
# drawn as more than one row.
ROWS, STREETS, IN_ROWS = 640, 618, 20
# How many rows enclose under a hundredth of a hectare.
SLIVERS = 17
# The least, the middle and the most of the ground a high street covers, in hectares.
LEAST, MIDDLE, MOST = 0.41, 9.56, 222.35
# How many high streets the file gives a size that is not the size of their outline, to 2 in
# 100, and how many sizes they are given between them.
NOT_THEIR_SIZE, SIZES_GIVEN = 4, 2
AREAS, OUTPUT_AREAS = 1_002, 26_369
# Of London's output areas: how many stand nearer to homes beyond London than to any high
# street of the file, and how many have one within 800 metres.
BEYOND, WITHIN_REACH = 231, 23_791
# The homes with one within 800 metres, in 100 of London's: of a high street, of a town
# centre, and of either.
HOMES_NEAR = {"a high street": 90.4, "a town centre": 67.7, "either": 92.2}
# How the two files stand to each other: the town centres that share land with a high
# street, those with half their outline or more inside one, and the high streets that share
# land with no town centre.
CENTRES, MEET, HALF_INSIDE, ALONE = 234, 207, 197, 403
# The conservation areas that were kept, each once, and the authorities that sent one.
CONSERVATION_AREAS, AUTHORITIES = 1_093, 33
# The shares: how many outlines have one, how many read nought, half or more, 90 or more and
# 100, and the middle of them.
OF_STREETS = (617, 257, 118, 27, 9, 6.1)
OF_CENTRES = (234, 72, 69, 20, 3, 20.05)
# The figure: how many areas have one, and the lowest, the middle and the highest.
FIGURES = (925, 0.0, 12.7, 100.0)
STATES = {
    State.PRESENT: 670,
    State.PARTIAL: 255,
    State.BELOW_THRESHOLD: 70,
    State.SOURCE_GAP: 7,
}


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
def made(real: Inputs, found: Spine) -> Conserved:
    return highstreet_conserved.build(real, found)


@pytest.fixture(scope="module")
def centres(real: Inputs, found: Spine) -> Found:
    return town_centres.build(real, found)


def counted(shares: list[float]) -> tuple[int, int, int, int, int, float]:
    """How many shares there are, how many read nought, half, 90 and 100, and their middle."""
    return (
        len(shares),
        sum(1 for share in shares if share == 0),
        sum(1 for share in shares if share >= 50),
        sum(1 for share in shares if share >= 90),
        sum(1 for share in shares if share == 100),
        round(statistics.median(shares), 2),
    )


# The file


def test_the_file_holds_as_many_rows_and_high_streets_as_were_counted(
    real: Inputs, made: Conserved
):
    opened = real.open(high_streets.SOURCE, Use.SCORING, named=high_streets.is_the_file)
    rows = names_shapes.read_layer(
        opened.path, opened.file_id, high_streets.LAYER, (high_streets.ID,)
    )
    of_each = Counter(row.text(high_streets.ID) for row in rows)
    assert (len(rows), len(of_each)) == (ROWS, STREETS)
    assert sum(1 for rows_of in of_each.values() if rows_of > 1) == IN_ROWS
    assert sum(1 for row in rows if hectares(row.shape) < 0.01) == SLIVERS
    assert len(made.found.centres) == STREETS


def test_a_high_street_drawn_as_several_rows_stands_in_several_pieces(made: Conserved):
    assert sum(1 for one in made.found.centres.values() if pieces(one.shape) > 1) == IN_ROWS


def test_the_high_streets_are_as_large_as_were_counted(made: Conserved):
    sizes = sorted(one.hectares for one in made.found.centres.values())
    assert round(sizes[0], 2) == LEAST and round(sizes[-1], 2) == MOST
    assert round(statistics.median(sizes), 2) == MIDDLE


def test_the_size_the_file_gives_is_not_the_size_of_every_high_street(
    real: Inputs, made: Conserved
):
    """Two pairs of high streets are each given the size of the pair. So no size is read."""
    opened = real.open(high_streets.SOURCE, Use.SCORING, named=high_streets.is_the_file)
    rows = names_shapes.read_layer(
        opened.path, opened.file_id, high_streets.LAYER, (high_streets.ID, "area_ha")
    )
    said = {row.text(high_streets.ID): float(str(row.fields["area_ha"])) for row in rows}
    off = [
        name
        for name, one in made.found.centres.items()
        if abs(one.hectares - said[name]) > 0.02 * said[name]
    ]
    assert len(off) == NOT_THEIR_SIZE
    assert len({round(said[name], 3) for name in off}) == SIZES_GIVEN
    assert all(
        sum(made.found.centres[name].hectares for name in off if round(said[name], 3) == size)
        == pytest.approx(size, rel=0.02)
        for size in {round(said[name], 3) for name in off}
    )


# Where homes are


def test_few_homes_stand_nearer_to_homes_beyond_london_than_to_a_high_street(
    made: Conserved, found: Spine
):
    assert (made.found.placed, made.found.may_be_nearer_beyond) == (OUTPUT_AREAS, BEYOND)
    assert len(town_centres.within_reach(made.found)) == WITHIN_REACH
    assert len(found.areas) == AREAS


def test_a_high_street_is_near_more_of_londons_homes_than_a_town_centre_is(
    made: Conserved, centres: Found, found: Spine
):
    whole = sum(found.homes.values())
    near = {
        "a high street": set(town_centres.within_reach(made.found)),
        "a town centre": set(town_centres.within_reach(centres)),
    }
    near["either"] = near["a high street"] | near["a town centre"]
    assert {
        which: round(100 * sum(found.homes[oa] for oa in oas) / whole, 1)
        for which, oas in near.items()
    } == HOMES_NEAR


def test_most_town_centres_lie_inside_a_high_street_and_most_high_streets_are_no_town_centre(
    made: Conserved, centres: Found
):
    streets = joined([one.shape for one in made.found.centres.values()])
    towns = joined([one.shape for one in centres.centres.values()])
    shared = {name: land_shared(one.shape, streets) for name, one in centres.centres.items()}
    assert len(centres.centres) == CENTRES
    assert sum(1 for part in shared.values() if part is not None) == MEET
    assert (
        sum(
            1
            for name, part in shared.items()
            if part is not None and hectares(part) >= 0.5 * centres.centres[name].hectares
        )
        == HALF_INSIDE
    )
    assert (
        sum(1 for one in made.found.centres.values() if land_shared(one.shape, towns) is None)
        == ALONE
    )


# The share of each outline


def test_as_many_high_streets_have_a_share_as_were_counted(made: Conserved):
    assert made.conservation_areas == CONSERVATION_AREAS
    assert counted(sorted(made.shares.values())) == OF_STREETS
    assert all(0 <= share <= 100 for share in made.shares.values())


def test_the_town_centres_asked_the_same_have_the_shares_that_were_counted(
    real: Inputs, found: Spine, centres: Found
):
    """The measure reads the high streets. The same is asked of the town centres, to compare."""
    boundaries = real.open(land.BOUNDARIES, Use.SCORING, edition=land.BOUNDARIES_EDITION)
    outlines = land.read(boundaries, found)
    opened = real.open(conservation_cover.SOURCE, Use.SCORING, named=conservation_cover.is_the_file)
    read = planning_data.read(
        opened,
        conservation_cover.DATASET,
        in_degrees(box_round(outlines), conservation_cover.MARGIN),
    )
    authorities = conservation_cover.outlines_of_authorities(outlines, found)
    held = conservation_cover.held_for_london(
        read, opened.receipt.data_period.days()[1], authorities
    )
    covered = [authorities[code] for code in sorted(authorities) if held.authorities[code].covered]
    assert len(covered) == len(authorities) == AUTHORITIES
    shares = highstreet_conserved.shares_of(
        {name: one.shape for name, one in centres.centres.items()},
        [one.shape for one in held.kept],
        joined(covered),
    )
    assert counted(sorted(shares.values())) == OF_CENTRES


# The figure


def test_as_many_areas_have_a_figure_as_were_counted(made: Conserved):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (len(values), values[0], statistics.median(values), values[-1]) == FIGURES
    assert len(made.worked) == AREAS
    assert dict(Counter(one.state for one in made.worked.values())) == STATES


def test_every_row_of_evidence_that_holds_a_figure_is_in_a_state_that_has_one(made: Conserved):
    assert len(made.rows) == AREAS
    for row in made.rows:
        assert (row.value is not None) == (row.state in HAS_A_VALUE)
        assert row.derivation_id == highstreet_conserved.METHOD.derivation_id


def test_worked_out_twice_the_figures_are_the_same(real: Inputs, found: Spine, made: Conserved):
    again = highstreet_conserved.build(real, found)
    assert again.worked == made.worked and again.rows == made.rows
    assert again.shares == made.shares


def test_nothing_was_written_to_the_store(made: Conserved, before: dict[str, tuple[int, int]]):
    assert made.worked
    assert listing() == before
