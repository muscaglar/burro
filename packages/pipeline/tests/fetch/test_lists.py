"""The list of files for a build, as data. Nothing is fetched and no socket is opened."""

import tomllib
from pathlib import Path

import pytest
from burro_pipeline.fetch.sources import LISTS, Format, ListError, load_list
from burro_pipeline.registry import Use, load

REPOSITORY = Path(__file__).parents[4]
REGISTRY = REPOSITORY / "registry" / "sources"

LIST = """
schema_version = 1
build = "made-up"

[[file]]
item = "made-up-homes"
source_id = "made-up-source"
use = "scoring"
what = "Made-up homes by made-up area"
format = "csv"
page = "https://made-up.example/homes"
url = "https://files.made-up.example/homes.csv"
max_bytes = 1000
edition = "2025"
data_period = { as_at = "2025-03-31" }
"""


def written(tmp_path: Path, text: str = LIST) -> Path:
    path = tmp_path / "made-up.toml"
    path.write_text(text, encoding="utf-8")
    return path


def changed(tmp_path: Path, old: str, new: str) -> Path:
    assert old in LIST
    return written(tmp_path, LIST.replace(old, new, 1))


def test_a_list_names_each_file_with_its_source_and_its_use(tmp_path: Path):
    listed = load_list(written(tmp_path))
    assert listed.build == "made-up"
    (file,) = listed.files
    assert (file.item, file.source_id, file.use) == ("made-up-homes", "made-up-source", Use.SCORING)
    assert file.format is Format.CSV
    assert file.max_bytes == 1000
    assert file.data_period is not None and file.data_period.as_at == "2025-03-31"
    assert file.ready_for_a_receipt


@pytest.mark.parametrize(
    ("old", "new", "said"),
    [
        (
            'url = "https://files.made-up.example/homes.csv"',
            'url = "http://made-up.example/h"',
            "https",
        ),
        (
            'url = "https://files.made-up.example/homes.csv"',
            'url = "https://u:p@made-up.example/h"',  # public-only: allow
            "login",
        ),
        ('page = "https://made-up.example/homes"', 'page = "made-up.example"', "https"),
        ("max_bytes = 1000", "max_bytes = 0", "max_bytes"),
        ("max_bytes = 1000\n", "", "max_bytes"),
        ('use = "scoring"', 'use = "anything"', "use"),
        ('format = "csv"', 'format = "spreadsheet"', "format"),
        ('item = "made-up-homes"', 'item = "Made Up"', "item"),
        ('edition = "2025"', 'edition = "2025"\nsize = 3', "does not have"),
        ('edition = "2025"', 'edition = "2025"\nunsure = ["colour"]', "unsure"),
        (
            'data_period = { as_at = "2025-03-31" }',
            'data_period = { as_at = "soon" }',
            "data_period",
        ),
        ("schema_version = 1", "schema_version = 2", "schema_version"),
        ('build = "made-up"', "", "build"),
        ("[[file]]", "[[files]]", "file"),
    ],
)
def test_a_list_that_is_not_in_order_is_refused(tmp_path: Path, old: str, new: str, said: str):
    with pytest.raises(ListError, match=said):
        load_list(changed(tmp_path, old, new))


def test_a_refusal_names_the_item_and_repeats_no_value(tmp_path: Path):
    path = changed(
        tmp_path, 'url = "https://files.made-up.example/homes.csv"', 'url = "ftp://zzyzx"'
    )
    with pytest.raises(ListError) as refused:
        load_list(path)
    assert "made-up-homes" in str(refused.value)
    assert "zzyzx" not in str(refused.value)


def test_an_item_may_be_listed_once(tmp_path: Path):
    entry = LIST.split("[[file]]")[1]
    with pytest.raises(ListError, match="more than once: made-up-homes"):
        load_list(written(tmp_path, LIST + "[[file]]" + entry))


def test_a_file_with_no_address_yet_is_listed_and_says_so(tmp_path: Path):
    listed = load_list(changed(tmp_path, 'url = "https://files.made-up.example/homes.csv"\n', ""))
    assert listed.files[0].url == ""
    assert not listed.files[0].has_an_address


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('edition = "2025"\n', ""),
        ('data_period = { as_at = "2025-03-31" }\n', ""),
        ('edition = "2025"', 'edition = "2025"\nunsure = ["edition"]'),
        ('edition = "2025"', 'edition = "2025"\nunsure = ["data_period"]'),
    ],
)
def test_what_nobody_is_sure_of_cannot_stand_in_a_receipt(tmp_path: Path, old: str, new: str):
    assert not load_list(changed(tmp_path, old, new)).files[0].ready_for_a_receipt


def test_a_list_is_found_by_its_name():
    assert load_list("m1").build == "m1"
    assert (LISTS / "m1.toml").is_file()


def test_a_name_that_is_no_list_is_refused():
    with pytest.raises(ListError, match="no list"):
        load_list("../../etc/passwd")
    with pytest.raises(ListError, match="no list"):
        load_list("m99")


def test_every_file_of_the_first_build_passes_the_gate_as_the_registry_stands():
    registry = load(REGISTRY)
    for file in load_list("m1").files:
        assert registry.require(file.source_id, file.use).id == file.source_id


def test_the_first_build_lists_the_sources_the_plan_names_for_it():
    assert {file.source_id for file in load_list("m1").files} == {
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-output-areas-2021",
        "ons-oa-pwc-2021",
        "ons-lsoa-2021",
        "ons-census-2021-housing-tables",
        "voa-council-tax-stock-of-properties",
        "mhclg-iod-2025-underlying-indicators",
        "defra-pcm-background-air",
    }


def test_every_page_of_the_first_build_is_one_the_registry_entry_holds():
    """No address in the list was made up: each is in the entry of its source."""
    registry = load(REGISTRY)
    for file in load_list("m1").files:
        source = registry.get(file.source_id)
        assert file.page in {source.url, *source.evidence_urls}, file.item


def test_the_list_is_no_part_of_a_workflow_and_names_no_store():
    text = (LISTS / "m1.toml").read_text(encoding="utf-8")
    assert "BURRO_STORE" not in text
    assert "r2.cloudflarestorage" not in text
    assert ".github" not in LISTS.as_posix()
    assert tomllib.loads(text)["schema_version"] == 1
