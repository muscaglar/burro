"""The food register: what is read of a business, and what stops the step.

Every file here is made up, and says so in a comment above its root. It is
laid out as a file of the register is: see `food_support.py`. Every business
has a made-up name, and the elements that no step may read hold the canary.
"""

import re
from dataclasses import asdict
from pathlib import Path

import pytest
from burro_pipeline.derive import food_register
from burro_pipeline.derive.food_register import Group, Register
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import held, registry
from .food_support import (
    CANARY,
    CATERER,
    DAY,
    EAT,
    EVERY_KIND,
    IN_QUILLHAVEN,
    IN_TALLOWGATE,
    LATER,
    PUB,
    Q1,
    QUILLHAVEN,
    SAID,
    SHOP,
    SOURCE,
    TAKEAWAY,
    TALLOWGATE,
    Business,
    beside,
    detail,
    header_of,
    inputs_of,
    register_receipt,
    register_xml,
    written,
)

ONE_CAFE = (Business(EAT, beside(Q1, 100)),)


def built(folder: Path, **registers: bytes) -> Register:
    """The register of the made-up town, or of the files given, each by its authority."""
    given = {code.removeprefix("of_"): content for code, content in registers.items()}
    return food_register.build(inputs_of(folder, given or None))


def refused(folder: Path, content: bytes, authority: str = QUILLHAVEN, day: str = DAY) -> str:
    """The refusal of one file, which names a rule and repeats nothing the file holds."""
    inputs = inputs_of(folder, {authority: content}, day=day)
    with pytest.raises(LockError) as stopped:
        food_register.build(inputs)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return str(stopped.value)


# What is read


def test_every_business_is_counted_by_its_kind_whether_or_not_it_has_a_point(tmp_path: Path):
    found = built(tmp_path)
    assert [one.authority for one in found.extracts] == [QUILLHAVEN, TALLOWGATE]
    assert [one.businesses for one in found.extracts] == [len(IN_QUILLHAVEN), len(IN_TALLOWGATE)]
    assert found.listed(Group.EAT) == 8 and found.placed(Group.EAT) == 6
    assert found.listed(Group.PUB) == 4 and found.placed(Group.PUB) == 3
    assert found.listed(Group.TAKEAWAY) == 3 and found.placed(Group.TAKEAWAY) == 3
    assert found.listed(Group.SHOP) == 1 and found.listed(Group.NONE) == 5
    assert sum(found.listed(group) for group in Group) == len(IN_QUILLHAVEN) + len(IN_TALLOWGATE)


def test_a_business_with_no_point_is_counted_and_is_put_nowhere(tmp_path: Path):
    """It is never put at the centre of its authority, or anywhere else."""
    found = built(tmp_path)
    without = sum(business.at is None for business in (*IN_QUILLHAVEN, *IN_TALLOWGATE))
    assert without == 3
    assert len(found.places) == len(IN_QUILLHAVEN) + len(IN_TALLOWGATE) - without
    assert sum(found.listed(group) - found.placed(group) for group in Group) == without


def test_a_place_is_where_the_register_says_and_of_the_kind_it_says(tmp_path: Path):
    found = built(tmp_path, of_901=register_xml(ONE_CAFE))
    (place,) = found.places
    assert (place.kind, place.group, place.authority) == ("1", Group.EAT, QUILLHAVEN)
    assert f"<Longitude>{place.longitude}</Longitude>" in written(beside(Q1, 100))
    assert f"<Latitude>{place.latitude}</Latitude>" in written(beside(Q1, 100))


def test_nothing_else_of_a_business_is_kept(tmp_path: Path):
    """No name, no address, no postcode, no rating and no date: each holds the canary."""
    content = register_xml(IN_QUILLHAVEN)
    assert content.count(CANARY.encode()) > 100
    found = built(tmp_path, of_901=content)
    kept = repr(asdict(found))
    assert "longitude" in kept and len(kept) > 1_000
    assert CANARY not in kept
    assert "Made-up Business" not in kept
    assert "1999-09-09" not in kept


def test_a_line_that_prints_the_register_prints_counts_and_no_business(tmp_path: Path):
    found = built(tmp_path)
    assert repr(found) == "Register(files=2, businesses=21, places=18)"
    assert "longitude" not in f"{found} {found!r}"


def test_the_elements_of_a_business_are_each_read_or_left_and_none_is_both():
    inside = set(re.findall(r"<([A-Za-z0-9]+)[ >/]", detail(Business(EAT, Q1), QUILLHAVEN, 1)))
    inside -= {food_register.DETAIL}
    assert inside <= set(food_register.READ) | set(food_register.LEFT)
    assert set(food_register.READ) <= inside
    assert not set(food_register.READ) & set(food_register.LEFT)
    for never in ("BusinessName", "AddressLine1", "PostCode", "RatingValue", "RatingDate"):
        assert never in food_register.LEFT
    assert "Scores" in food_register.LEFT and "Hygiene" in food_register.LEFT


def test_the_order_of_the_businesses_changes_nothing(tmp_path: Path):
    turned = built(tmp_path, of_901=register_xml(tuple(reversed(IN_QUILLHAVEN))))
    as_written = built(tmp_path / "as-written", of_901=register_xml(IN_QUILLHAVEN))
    assert turned.places == as_written.places
    assert turned.extracts[0].listed == as_written.extracts[0].listed


def test_the_file_says_that_it_is_made_up():
    assert SAID.encode() in register_xml(IN_QUILLHAVEN)
    assert b"made up" in register_xml(IN_QUILLHAVEN).lower()


# Which kinds are which


def test_every_kind_the_register_names_is_one_of_five_things():
    assert {(name, number) for number, (name, _) in food_register.KINDS.items()} == set(EVERY_KIND)
    assert len(food_register.KINDS) == 14
    of = {name: group for name, group in food_register.KINDS.values()}
    assert of["Restaurant/Cafe/Canteen"] is Group.EAT
    assert of["Pub/bar/nightclub"] is Group.PUB
    assert of["Takeaway/sandwich shop"] is Group.TAKEAWAY
    assert of["Retailers - other"] is Group.SHOP
    assert of["Retailers - supermarkets/hypermarkets"] is Group.SHOP
    none = sorted(name for name, group in of.items() if group is Group.NONE)
    assert none == [
        "Distributors/Transporters",
        "Farmers/growers",
        "Hospitals/Childcare/Caring Premises",
        "Hotel/bed & breakfast/guest house",
        "Importers/Exporters",
        "Manufacturers/packers",
        "Mobile caterer",
        "Other catering premises",
        "School/college/university",
    ]


def test_every_kind_is_read_as_the_register_writes_it(tmp_path: Path):
    one_of_each = tuple(Business(kind, Q1) for kind in EVERY_KIND)
    found = built(tmp_path, of_901=register_xml(one_of_each))
    assert found.extracts[0].listed == dict.fromkeys(sorted(food_register.KINDS), 1)


def test_no_kind_is_told_from_the_name_of_a_business(tmp_path: Path):
    """A caterer named as a cafe is a caterer: the register's kind decides, and no name is read."""
    row = detail(Business(CATERER, Q1), QUILLHAVEN, 1, BusinessName="Made-up Cafe and Pub")
    found = built(tmp_path, of_901=register_xml((), rows=[row]))
    assert found.listed(Group.NONE) == 1 and found.listed(Group.EAT) == 0


@pytest.mark.parametrize(
    "kind",
    [("Restaurant/Cafe/Canteen", "7843"), (CANARY, "1"), ("Pub/bar/nightclub", "9")],
)
def test_a_kind_the_register_is_not_known_to_name_is_refused(tmp_path: Path, kind: tuple[str, str]):
    """A new kind stops the step, so that a person says what it is."""
    content = register_xml((Business(kind, Q1),))
    assert "a kind of business" in refused(tmp_path, content)


# What a file is held to


def test_a_file_is_held_to_the_count_its_header_gives(tmp_path: Path):
    for stated in (0, 2, 17):
        content = register_xml(ONE_CAFE, header=header_of(items=stated))
        assert "as many businesses as its header says" in refused(tmp_path / str(stated), content)
    assert built(tmp_path / "right", of_901=register_xml(ONE_CAFE)).extracts[0].businesses == 1


def test_a_file_with_no_business_is_read_as_holding_none(tmp_path: Path):
    found = built(tmp_path, of_901=register_xml(ONE_CAFE), of_902=register_xml((), TALLOWGATE))
    assert [one.businesses for one in found.extracts] == [1, 0]
    assert found.extracts[1].authority == TALLOWGATE


@pytest.mark.parametrize(
    ("header", "words"),
    [
        (header_of(day=None, items=1), "the day of its extract"),
        (header_of(day=CANARY, items=1), "the day of its extract"),
        (header_of(day=LATER, items=1), "not the day of its receipt"),
        (header_of(items=None), "how many businesses"),
        (header_of(items=CANARY), "how many businesses"),
        (header_of(items=1, code=None), "the extract succeeded"),
        (header_of(items=1, code=CANARY), "the extract succeeded"),
        (header_of(items=1) + header_of(items=1), "laid out"),
        ("", "laid out"),
    ],
)
def test_a_header_that_says_something_else_is_refused(tmp_path: Path, header: str, words: str):
    assert words in refused(tmp_path, register_xml(ONE_CAFE, header=header))


def test_the_day_of_a_figure_is_the_day_the_file_states(tmp_path: Path):
    content = register_xml(ONE_CAFE, day=LATER)
    inputs = inputs_of(tmp_path, {QUILLHAVEN: content}, day=LATER)
    assert food_register.build(inputs).extracts[0].day == LATER


def test_the_period_is_the_span_of_the_days_the_files_state(tmp_path: Path):
    later = register_xml(IN_TALLOWGATE, TALLOWGATE, day=LATER)
    more = [(register_receipt(later, TALLOWGATE, LATER), later)]
    inputs = inputs_of(tmp_path, {QUILLHAVEN: register_xml(IN_QUILLHAVEN)}, more=more)
    found = food_register.build(inputs)
    assert found.period == Period(start=DAY, end=LATER)
    assert found.as_at == f"{DAY} to {LATER}"
    assert built(tmp_path / "one-day").as_at == DAY


def test_a_file_is_of_one_authority_and_of_the_one_its_name_says(tmp_path: Path):
    two = (Business(EAT, Q1), Business(EAT, Q1, authority=TALLOWGATE))
    assert "of one authority" in refused(tmp_path / "two", register_xml(two))
    other = register_xml(ONE_CAFE, TALLOWGATE)
    assert "the authority its name says" in refused(tmp_path / "other", other, QUILLHAVEN)
    none = detail(Business(EAT, Q1), QUILLHAVEN, 1, LocalAuthorityCode="")
    assert "which authority" in refused(tmp_path / "none", register_xml((), rows=[none]))


@pytest.mark.parametrize(
    "point",
    [
        "<Longitude>1.5</Longitude>",
        "<Latitude>53.5</Latitude>",
        "<Longitude></Longitude><Latitude>53.5</Latitude>",
        f"<Longitude>{CANARY}</Longitude><Latitude>53.5</Latitude>",
        "<Longitude>nan</Longitude><Latitude>53.5</Latitude>",
        "<Longitude>1e2</Longitude><Latitude>53.5</Latitude>",
        "<Longitude>181.0</Longitude><Latitude>53.5</Latitude>",
        "<Longitude>1.5</Longitude><Latitude>-90.5</Latitude>",
        "<Longitude>1.5</Longitude><Latitude>53.5</Latitude><Latitude>53.6</Latitude>",
    ],
)
def test_a_point_that_is_no_point_is_refused(tmp_path: Path, point: str):
    content = register_xml((Business(EAT, None, point=point),))
    assert "a point is no point" in refused(tmp_path, content)


@pytest.mark.parametrize(
    ("as_written", "read_as"),
    [
        ("-0.1234567", -0.1234567),
        ("0.123456789012345678", 0.123456789012345678),
        ("5.2E-05", 0.000052),
        ("-1.25E-05", -0.0000125),
        ("0", 0.0),
    ],
)
def test_a_longitude_is_read_as_the_register_writes_it(
    tmp_path: Path, as_written: str, read_as: float
):
    """It writes up to eighteen decimal places, and a longitude beside the meridian as a power."""
    point = f"<Longitude>{as_written}</Longitude><Latitude>51.5</Latitude>"
    found = built(tmp_path, of_901=register_xml((Business(EAT, None, point=point),)))
    assert [(place.longitude, place.latitude) for place in found.places] == [(read_as, 51.5)]


def test_a_business_that_gives_its_kind_twice_or_never_is_refused(tmp_path: Path):
    twice = detail(Business(EAT, Q1), QUILLHAVEN, 1).replace(
        "<BusinessTypeID>1</BusinessTypeID>",
        "<BusinessTypeID>1</BusinessTypeID><BusinessTypeID>7843</BusinessTypeID>",
    )
    assert "its kind once" in refused(tmp_path / "twice", register_xml((), rows=[twice]))
    never = detail(Business(EAT, Q1), QUILLHAVEN, 1, BusinessTypeID="")
    assert "its kind once" in refused(tmp_path / "never", register_xml((), rows=[never]))


def test_an_element_the_register_is_not_known_to_hold_is_refused(tmp_path: Path):
    """A new element stops the step, so that a person says whether it may be read."""
    row = detail(Business(EAT, Q1), QUILLHAVEN, 1, MadeUpElement=CANARY)
    assert "an element" in refused(tmp_path, register_xml((), rows=[row]))


@pytest.mark.parametrize(
    "content",
    [
        f"{CANARY}\n".encode(),
        b"<",
        register_xml(ONE_CAFE, root="MadeUpRegister"),
        register_xml(ONE_CAFE, before=f'<!DOCTYPE made [<!ENTITY up "{CANARY}">]>'),
        register_xml(ONE_CAFE)[:-20],
        register_xml((), rows=["<MadeUpDetail></MadeUpDetail>"]),
    ],
)
def test_a_file_that_is_no_file_of_the_register_is_refused(tmp_path: Path, content: bytes):
    assert refused(tmp_path, content)


def test_text_that_stands_where_no_element_is_read_is_never_kept(tmp_path: Path):
    """The longest text a file may hold of what is read is short. More is refused."""
    long = detail(Business(("x" * 500, "1"), Q1), QUILLHAVEN, 1)
    assert "a kind of business" in refused(tmp_path, register_xml((), rows=[long]))


# The gate, the receipts and the store


def without_scoring() -> Registry:
    """The repository's registry, with the register no longer registered for scoring."""
    sources = [
        source.model_copy(update={"uses": (Use.VALIDATION_ONLY,)})
        if source.id == SOURCE
        else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_any_file_is_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, given=without_scoring())
    with pytest.raises(LockError) as stopped:
        food_register.build(inputs)
    assert stopped.value.rule == "gate_refuses"
    assert inputs.opened == ()
    assert not (tmp_path / "work").exists()


def test_the_register_is_asked_for_under_scoring_which_its_entry_allows():
    entry = registry().get(SOURCE)
    assert food_register.USE is Use.SCORING and Use.SCORING in entry.uses
    assert Use.DISPLAY not in entry.uses


def test_a_build_with_no_file_of_the_register_has_no_receipt_to_read(tmp_path: Path):
    with pytest.raises(LockError) as stopped:
        food_register.build(inputs_of(tmp_path, {}))
    assert stopped.value.rule == "input_has_one_receipt"


def test_two_editions_of_one_file_are_refused_and_neither_is_picked(tmp_path: Path):
    later = register_xml(ONE_CAFE, day=LATER)
    more = [(register_receipt(later, QUILLHAVEN, LATER), later)]
    with pytest.raises(LockError) as stopped:
        food_register.build(inputs_of(tmp_path, more=more))
    assert stopped.value.rule == "input_has_one_receipt"


def test_a_file_that_is_not_named_as_the_publisher_names_its_files_is_not_read(tmp_path: Path):
    """The source may come to hold other files. The measure reads the file of an authority."""
    assert food_register.is_a_file("FHRS501en-GB.xml")
    for name in ("FHRS501cy-GB.xml", "FHRS501en-GB.json", "made-up-register-501.xml", "FHRS1.xml"):
        assert not food_register.is_a_file(name)
    other = register_xml(ONE_CAFE, TALLOWGATE)
    receipt = register_receipt(other, TALLOWGATE).model_copy(
        update={"publisher_file": "made-up-register-902.xml"}
    )
    found = food_register.build(
        inputs_of(tmp_path, {QUILLHAVEN: register_xml(ONE_CAFE)}, more=[(receipt, other)])
    )
    assert [one.authority for one in found.extracts] == [QUILLHAVEN]


def test_the_register_names_the_files_it_was_read_from(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    found = food_register.build(inputs)
    assert [receipt.publisher_file for receipt in found.files] == [
        "FHRS901en-GB.xml",
        "FHRS902en-GB.xml",
    ]
    assert [one.file_id for one in found.extracts] == [receipt.file_id for receipt in found.files]
    assert {one.receipt.source_id for one in inputs.opened} == {SOURCE}


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path)
    before = held(tmp_path / "store")
    food_register.build(inputs)
    assert held(tmp_path / "store") == before


def test_the_counts_of_a_kind_are_said_for_each_authority(tmp_path: Path):
    """What is held to the register's own total is the count of each kind, by authority."""
    found = built(tmp_path)
    quillhaven, tallowgate = found.extracts
    assert (quillhaven.of(Group.EAT), quillhaven.with_a_point(Group.EAT)) == (6, 4)
    assert (tallowgate.of(Group.PUB), tallowgate.with_a_point(Group.PUB)) == (2, 1)
    assert (quillhaven.of(Group.SHOP), quillhaven.of(Group.NONE)) == (1, 4)
    for one in found.extracts:
        assert sum(one.listed.values()) == one.businesses
    assert (PUB, TAKEAWAY, SHOP) == (
        ("Pub/bar/nightclub", "7843"),
        ("Takeaway/sandwich shop", "7844"),
        ("Retailers - other", "4613"),
    )
