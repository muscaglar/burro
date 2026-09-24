"""The spine: London's output areas, what each is part of, and the areas of the first build.

Every file here is made up. The town is Quillhaven and Tallowgate, which do not
exist, in files laid out as the statistics office lays out its own. No file of
a publisher is read, and nothing reaches a network.
"""

import hashlib
import re
from dataclasses import replace
from pathlib import Path

import pytest
from burro_core.ids import AREA_ID_PATTERN
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Area, Homes
from burro_pipeline.evidence.lock import InputKind, Lock, LockedInput, LockError
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from .support import (
    CANARY,
    HOMES_COLUMNS,
    LONDON,
    LOOKUP_COLUMNS,
    TOWN,
    contents,
    held,
    homes_zip,
    inputs_of,
    lookup_csv,
    registry,
)


def built(folder: Path, **files: bytes) -> spine.Spine:
    return spine.build(inputs_of(folder, contents() | files))


def refusal(folder: Path, **files: bytes) -> LockError:
    with pytest.raises(LockError) as refused:
        built(folder, **files)
    return refused.value


def test_london_is_the_rows_whose_borough_code_starts_e09(tmp_path: Path):
    found = built(tmp_path)
    assert len(TOWN) == len(LONDON) + 1
    assert [cell.oa for cell in found.cells] == sorted(unit.oa for unit in LONDON)
    assert {cell.borough for cell in found.cells} == {"E09000901", "E09000902"}


def test_the_spine_counts_what_the_files_hold(tmp_path: Path):
    assert built(tmp_path).counts() == {
        "output_areas": 12,
        "lsoas": 6,
        "msoas": 3,
        "boroughs": 2,
        "areas": 3,
        "homes": sum(unit.homes for unit in LONDON),
    }


def test_an_area_is_an_msoa_under_the_statistics_offices_own_label(tmp_path: Path):
    areas = built(tmp_path).areas
    assert areas[0] == Area(
        area_id="lon-ne02999001",
        code="E02999001",
        name="Quillhaven 001",
        slug="quillhaven-001",
        borough="Quillhaven",
        borough_code="E09000901",
    )
    assert [area.name for area in areas] == ["Quillhaven 001", "Quillhaven 002", "Tallowgate 001"]
    assert all(re.fullmatch(AREA_ID_PATTERN, area.area_id) for area in areas)


def test_an_id_holds_the_code_of_its_msoa_so_it_never_moves():
    assert spine.area_id_of("E02000001") == "lon-ne02000001"
    assert spine.slug_of("Kensington and Chelsea 001") == "kensington-and-chelsea-001"


def test_every_output_area_is_in_one_area_and_part_of_one_lsoa(tmp_path: Path):
    found = built(tmp_path)
    assert set(found.area_of) == {unit.oa for unit in LONDON}
    assert found.area_of["E00999001"] == "lon-ne02999001"
    assert found.lsoa_of["E00999001"] == found.lsoa_of["E00999002"] == "E01999001"
    assert found.area_of_lsoa["E01999006"] == "lon-ne02999003"
    assert set(found.area_of.values()) == {area.area_id for area in found.areas}


def test_a_home_is_the_total_of_the_table_and_no_other_column_is_read(tmp_path: Path):
    found = built(tmp_path)
    assert found.homes == {unit.oa: unit.homes for unit in LONDON}
    # With every other column of the table gone, the spine is the same.
    bare = homes_zip(columns=HOMES_COLUMNS[:4])
    assert built(tmp_path / "bare", homes=bare).homes == found.homes


def test_the_weights_are_every_output_area_with_its_area_and_its_homes(tmp_path: Path):
    weights = built(tmp_path).weights
    assert isinstance(weights, Homes)
    assert weights.areas == ("lon-ne02999001", "lon-ne02999002", "lon-ne02999003")
    assert weights.of_area["lon-ne02999001"] == (
        "E00999001",
        "E00999002",
        "E00999003",
        "E00999004",
    )


def test_the_spine_names_the_files_it_was_read_from(tmp_path: Path):
    files = contents()
    inputs = inputs_of(tmp_path, files)
    found = spine.build(inputs)
    ids = {f"f-{hashlib.sha256(files[which]).hexdigest()[:12]}" for which in ("lookup", "homes")}
    assert set(found.inputs) == ids == {opened.file_id for opened in inputs.opened}


def test_the_same_files_give_the_same_spine(tmp_path: Path):
    assert built(tmp_path / "a") == built(tmp_path / "b")


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    before = held(tmp_path / "store")
    spine.build(inputs)
    assert held(tmp_path / "store") == before


# What stops the build


def test_an_output_area_with_no_count_of_homes_stops_the_build(tmp_path: Path):
    """A figure shared out by homes cannot be worked out round a hole in the weights."""
    error = refusal(tmp_path, homes=homes_zip(TOWN[1:]))
    assert error.rule == "input_is_as_described"
    assert "no count" in str(error)


def test_an_output_area_outside_london_needs_no_count_of_homes(tmp_path: Path):
    assert built(tmp_path, homes=homes_zip(LONDON)).counts()["output_areas"] == 12


def test_an_output_area_listed_twice_stops_the_build(tmp_path: Path):
    error = refusal(tmp_path, lookup=lookup_csv((*TOWN, TOWN[0])))
    assert (error.rule, "twice" in str(error)) == ("input_is_as_described", True)


def test_an_lsoa_that_is_part_of_two_msoas_stops_the_build(tmp_path: Path):
    moved = replace(TOWN[0], msoa=TOWN[4].msoa, msoa_name=TOWN[4].msoa_name)
    error = refusal(tmp_path, lookup=lookup_csv((moved, *TOWN[1:])))
    assert (error.rule, "part of two" in str(error)) == ("input_is_as_described", True)


def test_a_label_that_is_not_the_borough_and_a_number_stops_the_build(tmp_path: Path):
    """A label that claims a name of its own is not what this build shows."""
    named = [replace(unit, msoa_name=CANARY) for unit in TOWN[:4]]
    error = refusal(tmp_path, lookup=lookup_csv((*named, *TOWN[4:])))
    assert error.rule == "input_is_as_described"
    assert CANARY not in str(error)


@pytest.mark.parametrize("missing", ["OA21CD", "MSOA21NM", "LAD22CD"])
def test_a_lookup_that_lacks_a_column_stops_the_build(tmp_path: Path, missing: str):
    columns = [name for name in LOOKUP_COLUMNS if name != missing]
    error = refusal(tmp_path, lookup=lookup_csv(columns=columns))
    assert (error.rule, "column" in str(error)) == ("input_is_as_described", True)
    assert missing not in str(error)


def test_a_table_of_homes_that_lacks_its_total_stops_the_build(tmp_path: Path):
    columns = [name for name in HOMES_COLUMNS if "Total" not in name]
    error = refusal(tmp_path, homes=homes_zip(columns=columns))
    assert (error.rule, "column" in str(error)) == ("input_is_as_described", True)


def test_a_refusal_repeats_nothing_from_a_file(tmp_path: Path):
    broken = lookup_csv().replace(b"E00999001", b"Zzyzx-001")
    error = refusal(tmp_path, lookup=broken)
    assert error.rule == "input_is_as_described"
    assert "Zzyzx" not in str(error)
    assert str(tmp_path) not in str(error)


# The gate, the receipt and the lock


def without_scoring() -> Registry:
    """The repository's registry, with the lookup no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.CELLS, Use.GAZETTEER)})
        if source.id == spine.LOOKUP
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_a_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents(), registry=without_scoring())
    with pytest.raises(LockError) as refused:
        spine.build(inputs)
    assert refused.value.rule == "gate_refuses"
    assert inputs.opened == ()
    assert not (tmp_path / "work").exists()


def test_a_file_with_no_receipt_is_not_read(tmp_path: Path):
    files = contents()
    inputs = inputs_of(tmp_path, {which: files[which] for which in files if which != "homes"})
    with pytest.raises(LockError) as refused:
        spine.build(inputs)
    assert (refused.value.rule, refused.value.subject) == ("input_has_one_receipt", spine.HOMES)


def test_a_file_that_is_not_the_one_its_receipt_names_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    kept = next((tmp_path / "store" / "raw" / spine.LOOKUP).rglob("*.csv"))
    kept.write_bytes(lookup_csv(TOWN[:-1]))
    with pytest.raises(LockError) as refused:
        spine.build(inputs)
    assert refused.value.rule == "file_is_in_the_vault"
    assert refused.value.subject.startswith("f-")


def lock_of(inputs_named: list[LockedInput]) -> Lock:
    return Lock(
        release_id="lon-2026-09-23-01",
        built_at="2026-09-23T00:00:00Z",
        commit="0123456789abcdef0123456789abcdef01234567",
        inputs=tuple(sorted(inputs_named, key=lambda locked: locked.name)),
    )


def test_a_file_the_lock_does_not_name_is_refused(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    named = [
        LockedInput(
            name=receipt.file_id,
            kind=InputKind.PUBLISHER_FILE,
            sha256=receipt.sha256,
            bytes=receipt.bytes,
            source_id=receipt.source_id,
        )
        for receipt in inputs.receipts
    ]
    inputs.lock = lock_of(named)
    # A lock that holds no packages by hash is still the lock of a development build.
    assert inputs.development
    assert not replace(
        inputs, lock=inputs.lock.model_copy(update={"packages": "0" * 64})
    ).development
    assert spine.build(inputs).counts()["areas"] == 3

    homes = next(receipt for receipt in inputs.receipts if receipt.source_id == spine.HOMES)
    fewer = inputs_of(tmp_path / "fewer", contents())
    fewer.lock = lock_of([locked for locked in named if locked.name != homes.file_id])
    with pytest.raises(LockError) as refused:
        spine.build(fewer)
    assert (refused.value.rule, refused.value.subject) == ("input_is_locked", homes.file_id)
