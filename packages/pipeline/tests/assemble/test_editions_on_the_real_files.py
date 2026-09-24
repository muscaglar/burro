"""Which edition a build takes of the food hygiene register, on the receipts that are committed.

Every other test of the rule runs on a made-up register. These read the real
receipts in `data/receipts/` and the real lists, and are skipped where the
store of fetched files is not. The store is named by BURRO_STORE_FOLDER.

The register is a file for each of London's 33 authorities, and its publisher
puts another at the same address when it has one. So these name the editions
that the first fetch kept, on 2026-09-24, and hold the build to those whatever
has arrived since. What is held is a count and three days. No file of the
register is read for what it holds: no business, no address and no rating.
Contains public sector information licensed under the Open Government Licence
v3.0. Source: Food Standards Agency.

Two more files of the list state no edition: the conservation areas and the
listed buildings of the planning data platform, which is made again each day.
Each is dated by the day it was retrieved, so the lock names its edition too.

One more file of the lists states no edition on its page: the town centre
boundaries. Its edition is the day the file says its contents were last
changed, so the lock names its edition too.

Nothing is written to the store. A file is copied out of it to be checked
against its receipt.
"""

import os
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.assemble.cli import of_the_list
from burro_pipeline.evidence.lock import Lock, read_receipts, seal, take
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.sources import Listed, load_list
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)

REGISTER = "fsa-food-hygiene-ratings"
# The two files of the planning data platform, by the name the list gives each, with the
# source of each and the edition that the first fetch of it kept.
PLATFORM = {
    "conservation-areas": "mhclg-planning-data-conservation-areas",
    "listed-buildings": "historic-england-listed-buildings",
}
PLATFORM_FIRST_FETCHED = dict.fromkeys(PLATFORM, "retrieved 2026-09-24")
# The town centre boundaries, by the name the list gives the file, with its source and the
# edition the file stated when it was fetched.
BOUNDARIES = {"gla-town-centres": "gla-town-centre-boundaries"}
BOUNDARIES_FETCHED = dict.fromkeys(BOUNDARIES, "last changed 2025-12-22")
LISTS = ("m1", "m2-places")
RELEASE, BUILT_AT = "lon-2026-09-24-01", "2026-09-24T00:00:00Z"
# No commit of any repository: the tests may be run in a working copy with changes.
COMMIT = "0" * 40
# The day each file stated when it was first fetched. 24 of the 33 stated the newest day.
NEWEST = "2026-09-16"
EARLIER = {
    "fsa-hounslow": "2026-09-09",
    "fsa-havering": "2026-09-10",
    "fsa-haringey": "2026-09-11",
    "fsa-islington": "2026-09-12",
    "fsa-greenwich": "2026-09-13",
    "fsa-barnet": "2026-09-15",
    "fsa-croydon": "2026-09-15",
    "fsa-hackney": "2026-09-15",
    "fsa-hammersmith-and-fulham": "2026-09-15",
}


@pytest.fixture(scope="module")
def listed() -> list[Listed]:
    return [file for name in LISTS for file in load_list(name).files]


@pytest.fixture(scope="module")
def receipts() -> tuple[Receipt, ...]:
    return read_receipts(RECEIPTS)


@pytest.fixture(scope="module")
def first_fetched(listed: list[Listed]) -> dict[str, str]:
    """The edition of each file of the register that the first fetch kept, by its name."""
    items = [file.item for file in listed if file.source_id == REGISTER]
    return {item: f"extract of {EARLIER.get(item, NEWEST)}" for item in items}


def sealed(
    receipts: tuple[Receipt, ...], listed: list[Listed], editions: dict[str, str], folder: Path
) -> Lock:
    """The lock of a build of the two lists, sealed as `preview` seals it."""
    taken, with_a_receipt, _ = of_the_list(receipts, listed, editions)
    vault = {held.key: held.bytes for held in FolderStore(Path(STORE)).list()}
    return seal(
        RELEASE,
        BUILT_AT,
        COMMIT,
        taken,
        vault,
        registry(),
        folder,
        listed=with_a_receipt,
        editions=editions,
    )


def test_the_list_names_a_file_of_the_register_for_each_of_33_authorities(listed: list[Listed]):
    of_the_register = [file for file in listed if file.source_id == REGISTER]
    assert len(of_the_register) == 33
    assert all(file.edition_from is not None and not file.edition for file in of_the_register)
    assert set(EARLIER) < {file.item for file in of_the_register}


def test_told_the_editions_of_the_first_fetch_a_build_takes_them_whatever_has_arrived_since(
    receipts: tuple[Receipt, ...], listed: list[Listed], first_fetched: dict[str, str]
):
    taken, without = take(receipts, listed, first_fetched)
    of_the_register = [one for one in taken if one.receipt.source_id == REGISTER]
    assert len(of_the_register) == 33 and all(one.named for one in of_the_register)
    assert not set(without) & set(first_fetched)
    days = Counter(one.receipt.data_period.days()[0] for one in of_the_register)
    assert (min(days), max(days), days[NEWEST]) == ("2026-09-09", NEWEST, 24)
    assert len({one.receipt.publisher_file for one in of_the_register}) == 33


def test_told_nothing_a_build_takes_the_newest_of_each_and_passes_the_others_over(
    receipts: tuple[Receipt, ...], listed: list[Listed], first_fetched: dict[str, str]
):
    taken, _ = take(receipts, listed)
    of_the_register = {one.item: one for one in taken if one.receipt.source_id == REGISTER}
    assert set(of_the_register) == set(first_fetched)
    for item, one in of_the_register.items():
        assert not one.named
        assert one.receipt.edition >= first_fetched[item]
        assert all(older.edition < one.receipt.edition for older in one.passed_over)
    with_a_receipt = sum(receipt.source_id == REGISTER for receipt in receipts)
    assert 33 + sum(len(one.passed_over) for one in of_the_register.values()) == with_a_receipt


def test_the_lock_names_the_edition_of_each_file_that_states_its_own_and_of_no_other_file(
    receipts: tuple[Receipt, ...],
    listed: list[Listed],
    first_fetched: dict[str, str],
    tmp_path: Path,
):
    """The 33 of the register, the two of the planning data platform, and the town centres."""
    told = first_fetched | PLATFORM_FIRST_FETCHED | BOUNDARIES_FETCHED
    lock = sealed(receipts, listed, told, tmp_path)
    said = {held.item: held.edition for held in lock.inputs if held.item is not None}
    assert said == told
    assert {held.source_id for held in lock.inputs if held.item is not None} == {
        REGISTER,
        *PLATFORM.values(),
        *BOUNDARIES.values(),
    }
    # Sealed again, with the receipts and the lists turned about, it is the same bytes.
    again = sealed(receipts[::-1], listed[::-1], told, tmp_path)
    assert again.canonical() == lock.canonical()


def test_a_file_of_the_platform_is_dated_by_the_day_it_was_retrieved(
    receipts: tuple[Receipt, ...], listed: list[Listed]
):
    taken, _ = take(receipts, listed, PLATFORM_FIRST_FETCHED)
    of_the_platform = {one.item: one for one in taken if one.item in PLATFORM}
    assert set(of_the_platform) == set(PLATFORM)
    for item, one in of_the_platform.items():
        assert one.named and one.receipt.source_id == PLATFORM[item]
        assert one.receipt.edition == PLATFORM_FIRST_FETCHED[item]
        assert one.receipt.data_period.days() == ("2026-09-24", "2026-09-24")
        assert one.receipt.retrieved_on == "2026-09-24"


def test_the_town_centres_are_dated_by_their_last_change_and_their_period_is_the_lists(
    receipts: tuple[Receipt, ...], listed: list[Listed]
):
    taken, _ = take(receipts, listed, BOUNDARIES_FETCHED)
    of_the_boundaries = {one.item: one for one in taken if one.item in BOUNDARIES}
    assert set(of_the_boundaries) == set(BOUNDARIES)
    for item, one in of_the_boundaries.items():
        assert one.named and one.receipt.source_id == BOUNDARIES[item]
        assert one.receipt.edition == BOUNDARIES_FETCHED[item]
        assert one.receipt.edition_from is not None and not one.receipt.edition_from.period_too
        assert one.receipt.data_period.days() == ("2025-12-22", "2025-12-22")


def test_a_step_is_handed_the_33_files_each_as_its_receipt_says(
    receipts: tuple[Receipt, ...],
    listed: list[Listed],
    first_fetched: dict[str, str],
    tmp_path: Path,
):
    taken, _, _ = of_the_list(receipts, listed, first_fetched)
    lock = sealed(receipts, listed, first_fetched, tmp_path)
    inputs = Inputs(registry(), taken, FolderStore(Path(STORE)), tmp_path / "copies", lock)
    opened = inputs.open_each(REGISTER, Use.SCORING)
    assert len(opened) == 33
    assert [one.receipt.publisher_file for one in opened] == sorted(
        one.receipt.publisher_file for one in opened
    )
    assert all(one.path.stat().st_size == one.receipt.bytes for one in opened)
    assert all(lock.holds(one.file_id) for one in opened)
