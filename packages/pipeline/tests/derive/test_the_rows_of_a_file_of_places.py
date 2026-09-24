"""Every row of a file of places, handed over for a measure with a table of kinds of its own.

Every file here is made up, and says so: `culture_support.py` draws the town
and writes its places. The file is read as a build reads it, from a store,
through the licence gate, by its receipt. No socket is opened.
"""

from pathlib import Path

import pytest
from burro_pipeline.derive import culture_file
from burro_pipeline.derive.culture_file import Record
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry.model import Use

from ..cells.support import registry
from .culture_support import CANARY, IN_THE_TOWN, MUSEUM, Q1, SOURCE, inputs_of, place


def test_every_row_of_a_file_is_handed_over_with_what_it_says_it_is(tmp_path: Path):
    inputs = inputs_of(tmp_path, [place(Q1, MUSEUM, alternates=("cafe",), confidence=0.4)])
    (record,) = culture_file.records(culture_file.opened_of(inputs))
    assert record.primary == "museum" and record.hierarchy == MUSEUM
    assert record.alternates == ("cafe",) and record.datasets == ("meta",)
    assert (record.closed, record.confidence) == (False, 0.4)
    assert record.at is not None and 2 < record.at[0] < 4.5 and 53 < record.at[1] < 54


def test_a_row_holds_no_name_no_address_and_no_id_of_a_place(tmp_path: Path):
    inputs = inputs_of(tmp_path, IN_THE_TOWN, packed="none")
    found = list(culture_file.records(culture_file.opened_of(inputs)))
    assert len(found) == len(IN_THE_TOWN) and CANARY not in repr(found)
    assert {field for field in Record.__dataclass_fields__} == {
        "primary",
        "hierarchy",
        "alternates",
        "at",
        "closed",
        "datasets",
        "confidence",
    }


def test_the_gate_is_asked_for_scoring_before_the_file_is_opened(tmp_path: Path):
    real = registry()
    asked: list[tuple[str, Use]] = []

    class Watched:
        def require(self, source_id: str, use: Use) -> object:
            asked.append((source_id, use))
            return real.require(source_id, use)

        def __getattr__(self, name: str) -> object:
            return getattr(real, name)

    inputs = inputs_of(tmp_path, IN_THE_TOWN, given=Watched())  # pyright: ignore[reportArgumentType]
    list(culture_file.records(culture_file.opened_of(inputs)))
    assert asked[0] == (SOURCE, Use.SCORING)


@pytest.mark.parametrize(
    "wrong",
    [
        {"status": "zzyzx_parva"},
        {"primary": "art_gallery"},
        {"geometry": b"not a point"},
    ],
)
def test_a_row_that_is_not_as_the_publisher_writes_one_stops_the_build(
    tmp_path: Path, wrong: dict[str, object]
):
    inputs = inputs_of(tmp_path, [place(Q1, MUSEUM, **wrong)])
    with pytest.raises(LockError) as stopped:
        list(culture_file.records(culture_file.opened_of(inputs)))
    assert stopped.value.rule == "input_is_as_described"
    assert "zzyzx" not in str(stopped.value) and CANARY not in str(stopped.value)


def test_a_row_that_the_file_says_has_closed_for_good_says_so(tmp_path: Path):
    inputs = inputs_of(
        tmp_path,
        [place(Q1, MUSEUM, status="permanently_closed"), place(Q1, MUSEUM, status=None)],
    )
    found = list(culture_file.records(culture_file.opened_of(inputs)))
    assert sorted(record.closed for record in found) == [False, True]


def test_a_row_with_no_category_and_no_point_is_handed_over_as_it_is(tmp_path: Path):
    nowhere = b"\x01\x01\x00\x00\x00" + b"\x00\x00\x00\x00\x00\x00\xf8\x7f" * 2
    inputs = inputs_of(tmp_path, [place(Q1, (), geometry=nowhere, confidence=None)])
    (record,) = culture_file.records(culture_file.opened_of(inputs))
    assert (record.primary, record.hierarchy, record.at) == (None, (), None)
    assert record.confidence is None


def test_culture_is_read_as_it_was(tmp_path: Path):
    """The rows that culture reads are the rows that are handed over, and as many."""
    inputs = inputs_of(tmp_path, IN_THE_TOWN)
    places = culture_file.build(inputs)
    handed = list(culture_file.records(culture_file.opened_of(inputs)))
    assert places.rows == len(handed) == len(IN_THE_TOWN)
    assert len(places.every) == sum(record.at is not None for record in handed)
