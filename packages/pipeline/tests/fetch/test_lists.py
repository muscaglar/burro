"""The list of files for a build, as data. Nothing is fetched and no socket is opened."""

import tomllib
from pathlib import Path

import pytest
from burro_pipeline.evidence import EditionFrom, Where
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


# A file that states its own edition. Its publisher puts another file at the same address
# and names no edition on its page, so the list cannot state one for what a fetch will bring.
STATED = 'edition = "2025"\ndata_period = { as_at = "2025-03-31" }\n'
IN_THE_HEADER = (
    'edition_from = { where = "xml_header", at = "Header/ExtractDate", '
    'words = "extract of", period_too = true }\n'
)
LAST_CHANGE = (
    'edition_from = { where = "geopackage", at = "gpkg_contents.last_change", '
    'words = "last changed", period_too = false }\n'
)
RUNS_TO = (
    'edition_from = { where = "street_extract", '
    'at = "OSMHeader.osmosis_replication_timestamp", period_too = true }\n'
)
THE_DAY_RETRIEVED = (
    'edition_from = { where = "retrieved", at = "", words = "retrieved", period_too = true }\n'
)
AS_XML = ('format = "csv"', 'format = "xml"')
AS_A_GEOPACKAGE = ('format = "csv"', 'format = "gpkg"')
AS_ANOTHER_KIND = ('format = "csv"', 'format = "other"')


def dated(tmp_path: Path, said: str, *swaps: tuple[str, str]) -> Path:
    """The made-up list, with what it says of the edition changed for `said`."""
    assert STATED in LIST
    text = LIST.replace(STATED, said, 1)
    for old, new in swaps:
        assert old in text
        text = text.replace(old, new, 1)
    return written(tmp_path, text)


def test_a_list_may_say_that_a_file_states_its_own_edition_and_where(tmp_path: Path):
    (file,) = load_list(dated(tmp_path, IN_THE_HEADER, AS_XML)).files
    assert file.edition == "" and file.data_period is None
    assert file.edition_from is not None
    assert file.edition_from.in_a_receipt() == EditionFrom(
        where=Where.XML_HEADER, at="Header/ExtractDate", period_too=True
    )
    assert file.edition_from.written("2026-09-16") == "extract of 2026-09-16"
    assert file.ready_for_a_receipt


def test_a_list_may_say_that_an_edition_is_the_day_a_file_was_retrieved(tmp_path: Path):
    (file,) = load_list(dated(tmp_path, THE_DAY_RETRIEVED)).files
    assert file.edition_from is not None and file.edition_from.where is Where.RETRIEVED
    assert file.edition_from.written("2026-09-24") == "retrieved 2026-09-24"
    assert file.ready_for_a_receipt


def test_a_time_a_file_gives_may_be_written_with_no_words_before_it(tmp_path: Path):
    (file,) = load_list(dated(tmp_path, RUNS_TO, AS_ANOTHER_KIND)).files
    assert file.edition_from is not None
    assert file.edition_from.written("2026-09-22T20:22:59Z") == "2026-09-22T20:22:59Z"
    assert file.ready_for_a_receipt


@pytest.mark.parametrize(
    ("said", "swaps", "refused"),
    [
        # A list states an edition, or says that the file states its own. Never both.
        (f'edition = "2025"\n{IN_THE_HEADER}', (AS_XML,), "and not both"),
        (f'{IN_THE_HEADER}unsure = ["edition"]\n', (AS_XML,), "and not both"),
        # Where the file gives the period too, the list states none.
        (f'{IN_THE_HEADER}data_period = {{ as_at = "2025-03-31" }}\n', (AS_XML,), "period"),
        (f'{IN_THE_HEADER}unsure = ["data_period"]\n', (AS_XML,), "period"),
        # A place is of one kind of file.
        (IN_THE_HEADER, (), "format"),
        (LAST_CHANGE, (AS_XML,), "format"),
        (RUNS_TO, (AS_XML,), "format"),
        # A file that a person saves is dated by that person.
        (f"{THE_DAY_RETRIEVED}by_hand = true\n", (), "by hand"),
        # A day that is about the file, or about the fetch, says in words which it is.
        (LAST_CHANGE.replace('words = "last changed", ', ""), (AS_A_GEOPACKAGE,), "words"),
        (THE_DAY_RETRIEVED.replace('words = "retrieved", ', ""), (), "words"),
        (IN_THE_HEADER.replace("extract of", "Extract of 2026"), (AS_XML,), "words"),
        (IN_THE_HEADER.replace("extract of", "x" * 41), (AS_XML,), "words"),
        # The day a GeoPackage was last changed is never the period of its data.
        (LAST_CHANGE.replace("false", "true"), (AS_A_GEOPACKAGE,), "about the file"),
        (IN_THE_HEADER.replace("Header/ExtractDate", "ExtractDate"), (AS_XML,), "header"),
    ],
)
def test_a_list_that_says_two_things_of_an_edition_is_refused(
    tmp_path: Path, said: str, swaps: tuple[tuple[str, str], ...], refused: str
):
    with pytest.raises(ListError, match=refused):
        load_list(dated(tmp_path, said, *swaps))


def test_where_a_file_gives_its_edition_alone_the_list_states_the_period(tmp_path: Path):
    """The day a GeoPackage was last changed is about the file. The period is the list's."""
    period = 'data_period = { as_at = "2025-03-31" }\n'
    (sure,) = load_list(dated(tmp_path, LAST_CHANGE + period, AS_A_GEOPACKAGE)).files
    assert sure.ready_for_a_receipt
    assert sure.data_period is not None and sure.data_period.as_at == "2025-03-31"
    for said in (LAST_CHANGE, f'{LAST_CHANGE}{period}unsure = ["data_period"]\n'):
        (unsure,) = load_list(dated(tmp_path, said, AS_A_GEOPACKAGE)).files
        assert not unsure.ready_for_a_receipt


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
