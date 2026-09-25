"""Which areas kept the outline they had in 2011, from the lookup its publisher gave.

Every other test of the reader runs on a made-up lookup. These read the real
one, and are skipped where the store of fetched files is not, and until the
lookup has its receipt in `data/receipts/`. The store is named by
BURRO_STORE_FOLDER, and the file is read through its receipt.

They hold counts, so that a publisher's file that changes is noticed. None is
said of a named area or of a named borough. Each was counted on 2026-09-24,
from the file its record calls V2, and no person has checked one.

The publisher's words for its source, as the licence registry holds them:
"Source: Office for National Statistics licensed under the Open Government
Licence v.3.0".

Nothing is written to the store. A file is copied out of it to be read.
"""

from collections import Counter

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import areas_of_2011 as lookup
from burro_pipeline.derive.areas_of_2011 import Changes, Mark
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from .areas_of_2011_support import COLUMNS, lookup_csv
from .real_files import RECEIPTS, SKIPPED, real_inputs

pytestmark = [
    SKIPPED,
    pytest.mark.skipif(
        not (RECEIPTS / lookup.SOURCE).is_dir(),
        reason="the lookup has no receipt yet: it is written when the file is fetched again",
    ),
]
FILE = "f-674387d9ace6"


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def changes(real: Inputs, found: Spine) -> Changes:
    return lookup.build(real, found)


def test_the_receipt_states_what_the_list_states(real: Inputs):
    opened = real.open(lookup.SOURCE, Use.SCORING, edition=lookup.EDITION)
    assert opened.file_id == FILE
    assert opened.receipt.use is Use.CELLS
    assert opened.receipt.data_period == Period(as_at="2022-12")
    # The publisher's own name for the download bears the edition out.
    assert opened.receipt.publisher_file.endswith(f"({lookup.EDITION}).csv")


def test_the_made_up_file_is_laid_out_as_the_real_one(real: Inputs):
    """Its nine columns in its order, a mark at the start, and lines that end with a line feed."""
    opened = real.open(lookup.SOURCE, Use.SCORING, edition=lookup.EDITION)
    with opened.path.open("rb") as file:
        first = file.readline()
    assert first == lookup_csv().splitlines(keepends=True)[0]
    assert first.decode("utf-8-sig").rstrip("\n").split(",") == list(COLUMNS)


def test_the_file_holds_as_many_rows_as_were_counted(changes: Changes):
    assert changes.rows == 7_286
    assert len(changes.pairs) == 1_003


def test_every_area_of_the_build_stands_in_the_lookup_and_no_other_does(
    changes: Changes, found: Spine
):
    assert set(changes.of_2021) == {area.code for area in found.areas}
    assert len(changes.of_2021) == 1_002
    assert len({pair.of_2011 for pair in changes.pairs}) == 983


def test_the_rows_of_london_hold_three_of_the_four_marks(changes: Changes):
    """None is marked as a pair that does not fit."""
    assert Counter(pair.mark for pair in changes.pairs) == {
        Mark.UNCHANGED: 963,
        Mark.SPLIT: 38,
        Mark.MERGED: 2,
    }
    assert Counter(changes.marks.values()) == {
        Mark.UNCHANGED: 963,
        Mark.SPLIT: 38,
        Mark.MERGED: 1,
    }


def test_eighteen_areas_were_split_and_two_were_joined(changes: Changes):
    split = Counter(pair.of_2011 for pair in changes.pairs if pair.mark is Mark.SPLIT)
    joined = Counter(pair.of_2021 for pair in changes.pairs if pair.mark is Mark.MERGED)
    assert Counter(split.values()) == {2: 16, 3: 2}
    assert Counter(joined.values()) == {2: 1}


def test_a_figure_is_carried_to_963_areas_and_to_no_other(changes: Changes, found: Spine):
    taken = {area.code: changes.taken_from(area.code) for area in found.areas}
    assert sum(1 for of_2011 in taken.values() if of_2011 is not None) == 963
    assert all(of_2011 in (None, code) for code, of_2011 in taken.items())
    without = Counter(area.borough_code for area in found.areas if taken[area.code] is None)
    assert sorted(without.values(), reverse=True) == [5, 4, 4, 4, 4, 3, 2, 2, 2, 2, 2, 2, 2, 1]
