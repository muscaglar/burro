"""A list may say which part of a file to take. Nothing is fetched and no socket is opened."""

from pathlib import Path

import pytest
from burro_pipeline.fetch.sources import Format, ListError, Take, load_list

LIST = """
schema_version = 1
build = "made-up"

[[file]]
item = "made-up-places"
source_id = "made-up-source"
use = "scoring"
what = "Made-up places of a made-up world, the part round a made-up town"
format = "parquet"
page = "https://made-up.example/places"
url = "https://files.made-up.example/release/1/places.parquet"
max_bytes = 1000
edition = "1"
data_period = { as_at = "2025-03-31" }
take = { box = [2.3, 53.0, 2.7, 54.0], box_in = "bbox", columns = ["geometry", "bbox"] }
"""
TAKE = 'take = { box = [2.3, 53.0, 2.7, 54.0], box_in = "bbox", columns = ["geometry", "bbox"] }'


def written(tmp_path: Path, text: str = LIST) -> Path:
    path = tmp_path / "made-up.toml"
    path.write_text(text, encoding="utf-8")
    return path


def refused(tmp_path: Path, old: str, new: str) -> str:
    assert old in LIST
    with pytest.raises(ListError) as stopped:
        load_list(written(tmp_path, LIST.replace(old, new, 1)))
    return str(stopped.value)


def test_a_list_says_which_part_of_a_file_to_take(tmp_path: Path):
    (file,) = load_list(written(tmp_path)).files
    assert file.format is Format.PARQUET
    assert file.take == Take(
        box=(2.3, 53.0, 2.7, 54.0), box_in="bbox", columns=("geometry", "bbox")
    )
    assert file.ready_for_a_receipt


def test_a_column_inside_another_is_named_from_the_top(tmp_path: Path):
    inside = LIST.replace('"geometry", "bbox"', '"sources.list.element.dataset", "bbox"')
    (file,) = load_list(written(tmp_path, inside)).files
    assert file.take is not None
    assert file.take.columns == ("sources.list.element.dataset", "bbox")


def test_a_file_with_nothing_said_of_a_part_is_fetched_whole(tmp_path: Path):
    (file,) = load_list(written(tmp_path, LIST.replace(TAKE, ""))).files
    assert file.take is None and file.format is Format.PARQUET


@pytest.mark.parametrize(
    ("old", "new", "said"),
    [
        ('format = "parquet"', 'format = "csv"', "format is `parquet`"),
        ('format = "parquet"', 'format = "other"', "format is `parquet`"),
        ('edition = "1"', 'edition = "1"\nby_hand = true', "by fetch alone"),
        ("box = [2.3, 53.0, 2.7, 54.0]", "box = [2.7, 53.0, 2.3, 54.0]", "from west to east"),
        ("box = [2.3, 53.0, 2.7, 54.0]", "box = [2.3, 54.0, 2.7, 53.0]", "from south to north"),
        ("box = [2.3, 53.0, 2.7, 54.0]", "box = [2.3, 53.0, 2.7]", "box"),
        ("box = [2.3, 53.0, 2.7, 54.0]", "box = [2.3, 53.0, 182.7, 54.0]", "in degrees"),
        ("box = [2.3, 53.0, 2.7, 54.0]", "box = [2.30000001, 53.0, 2.7, 54.0]", "six decimal"),
        ("box = [2.3, 53.0, 2.7, 54.0], ", "", "box"),
        ('box_in = "bbox", ', "", "box_in"),
        ('box_in = "bbox"', 'box_in = "box"', "the column that holds the box"),
        ('columns = ["geometry", "bbox"]', "columns = []", "columns"),
        ('columns = ["geometry", "bbox"]', 'columns = ["bbox", "bbox"]', "each column once"),
        ('columns = ["geometry", "bbox"]', 'columns = ["bbox", "na mes"]', "columns"),
        ('columns = ["geometry", "bbox"]', 'columns = ["bbox", "a..b"]', "columns"),
        ('columns = ["geometry", "bbox"]', 'columns = ["bbox", ".a"]', "columns"),
        ('box_in = "bbox"', 'box_in = "bbox", rows = 5', "holds a field"),
    ],
)
def test_a_part_that_is_not_said_as_it_should_be_is_refused(
    tmp_path: Path, old: str, new: str, said: str
):
    found = refused(tmp_path, old, new)
    assert found.startswith("made-up-places: ") and said in found


def test_a_file_that_states_its_own_edition_is_not_taken_in_part(tmp_path: Path):
    """What dates a file is read in the whole of it, and a part holds no such place."""
    with_a_day = LIST.replace('edition = "1"\n', "").replace(
        TAKE,
        TAKE + '\nedition_from = { where = "retrieved", at = "", words = "retrieved", '
        "period_too = false }",
    )
    with pytest.raises(ListError, match="by fetch alone"):
        load_list(written(tmp_path, with_a_day))


def test_a_refusal_repeats_nothing_the_list_holds(tmp_path: Path):
    found = refused(tmp_path, 'box_in = "bbox"', 'box_in = "Zzyzx Parva"')
    assert "Zzyzx" not in found
