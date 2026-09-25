"""The table of tiers: what the founder decided, held to the file that holds it.

The table is data, and a person adjusts it. These tests hold what must stay
so whatever a person moves: that the founder's own rows are there, that every
chain core names is on it, and that no place can be of two rows. They read the
table of the repository and no other file.
"""

import json
from pathlib import Path

import pytest
from burro_core.catalogue import CHAINS
from burro_core.ids import FeatureId
from burro_pipeline.derive import brand_table
from burro_pipeline.derive.brand_table import (
    OF_KIND,
    Chain,
    Kind,
    TableError,
    Tier,
    chain_of,
    checked,
    eats_or_drinks,
    folded,
    is_of_kind,
    the_table,
)
from burro_pipeline.derive.culture_file import Brand, Record

# The founder's table, as it was decided on 2026-09-24, by the names Burro says.
FOUNDERS = {
    (Kind.GROCER, Tier.PREMIUM): ("Waitrose", "M&S", "Whole Foods"),
    (Kind.GROCER, Tier.MID): ("Sainsbury's", "Tesco", "Co-op"),
    (Kind.GROCER, Tier.VALUE): ("Asda", "Aldi", "Lidl", "Iceland"),
    (Kind.GYM, Tier.PREMIUM): ("Equinox", "Third Space", "Barry's"),
    (Kind.GYM, Tier.MID): ("Virgin Active", "Nuffield", "Gymbox"),
    (Kind.GYM, Tier.VALUE): ("PureGym", "The Gym Group"),
    (Kind.COFFEE, Tier.PREMIUM): ("Gail's", "Ole & Steen"),
    (Kind.COFFEE, Tier.MID): ("Pret", "Nero", "Starbucks"),
    (Kind.COFFEE, Tier.VALUE): ("Greggs",),
}
# The chains that were added beside their neighbours, each a first guess.
ADDED = {
    "Morrisons": (Kind.GROCER, Tier.MID),
    "David Lloyd": (Kind.GYM, Tier.MID),
    "Anytime Fitness": (Kind.GYM, Tier.MID),
    "Costa": (Kind.COFFEE, Tier.MID),
    "Blank Street": (Kind.COFFEE, Tier.MID),
}


def record(*path: str) -> Record:
    return Record(
        primary=path[-1] if path else None,
        hierarchy=path,
        alternates=(),
        at=(0.0, 51.5),
        closed=False,
        datasets=("meta",),
        confidence=None,
    )


def row(key: str = "gildcrest", **said: object) -> Chain:
    fields = {
        "key": key,
        "name": key.capitalize(),
        "kind": "grocer",
        "tier": "premium",
        "on_the_founders_table": False,
        "wikidata": (),
        "spellings": (key.capitalize(),),
    }
    return Chain.model_validate(fields | said)


def test_the_founders_rows_are_on_the_table_each_in_the_tier_the_founder_gave_it():
    table = the_table()
    for (kind, tier), names in FOUNDERS.items():
        founders = [chain.name for chain in table.of(kind, tier) if chain.on_the_founders_table]
        assert tuple(founders) == names, (kind, tier)


def test_every_other_row_says_that_it_was_added_and_is_one_of_five():
    table = the_table()
    added = {
        chain.name: (chain.kind, chain.tier)
        for chain in table.chains
        if not chain.on_the_founders_table
    }
    assert added == ADDED
    assert len(table.chains) == sum(map(len, FOUNDERS.values())) + len(ADDED) == 29


def test_core_names_every_chain_of_the_table_and_no_other():
    """A person asks for a chain by the name core gives it, so the two lists are one."""
    table = the_table()
    assert {f"brand_{chain.key}" for chain in table.chains} == {f.value for f in CHAINS}
    for chain in table.chains:
        assert CHAINS[FeatureId(f"brand_{chain.key}")].name == chain.name


def test_the_table_says_which_release_its_spellings_were_read_in():
    assert the_table().read_in == "overture-places 2026-09-23.0"


def test_two_chains_the_file_gives_no_place_the_brand_of_hold_no_spelling():
    unspelled = [chain.name for chain in the_table().chains if not chain.spellings]
    assert unspelled == ["Third Space", "Gymbox"]
    assert all(not chain.wikidata for chain in the_table().chains if not chain.spellings)


# Which row a brand is of


@pytest.mark.parametrize(
    ("brand", "key"),
    [
        (Brand("Waitrose & Partners", None), "waitrose"),
        (Brand("Little Waitrose", "Q771734"), "waitrose"),
        (Brand("waitrose", None), "waitrose"),
        (Brand("Sainsbury\N{RIGHT SINGLE QUOTATION MARK}s Local", None), "sainsburys"),
        (Brand("ALDI", None), "aldi"),
        (Brand("Aldi", None), "aldi"),
        (Brand("  Tesco   Express ", None), "tesco"),
        (Brand("Caffè Nero", None), "nero"),
        (Brand("Costa Coffee", None), "costa"),
        (Brand("The Gym Group", "Q48815022"), "the_gym_group"),
    ],
)
def test_a_brand_is_of_the_row_that_holds_its_id_or_its_name_as_written(brand: Brand, key: str):
    found = chain_of(brand, the_table())
    assert found is not None and found.key == key


def test_an_id_of_a_row_decides_whatever_the_name_says():
    found = chain_of(Brand("Tesco", "Q771734"), the_table())
    assert found is not None and found.key == "waitrose"
    found = chain_of(Brand(None, "Q37158"), the_table())
    assert found is not None and found.key == "starbucks"


@pytest.mark.parametrize(
    "brand",
    [
        None,
        Brand(None, None),
        Brand("Gildcrest", None),
        # A name that holds the name of a chain is no spelling of it.
        Brand("Co-op Funeralcare", None),
        Brand("Sainsbury's Bank", "Q7400525"),
        Brand("Costa Express", "Q113556385"),
        Brand("Waitrose Wine Bar", None),
        Brand("Caffe Nero", None),
        Brand("Tesc", None),
        Brand("Third Space", None),
    ],
)
def test_a_brand_that_is_on_no_row_has_no_tier(brand: Brand | None):
    assert chain_of(brand, the_table()) is None


def test_a_name_is_compared_in_small_letters_with_one_mark_for_an_apostrophe():
    assert folded("GAIL\N{RIGHT SINGLE QUOTATION MARK}s ") == folded("gail's") == "gail's"
    assert folded("Pret  A   Manger") == "pret a manger"
    # An accent is a letter of the name, and is not taken off.
    assert folded("Caffè Nero") != folded("Caffe Nero")


# What kind of place it is


@pytest.mark.parametrize(
    ("kind", "path"),
    [
        (Kind.GROCER, ("shopping", "food_and_beverage_store", "grocery_store")),
        (
            Kind.GROCER,
            ("shopping", "food_and_beverage_store", "grocery_store", "organic_grocery_store"),
        ),
        (Kind.GROCER, ("shopping", "convenience_store")),
        (Kind.GROCER, ("shopping", "department_store")),
        (Kind.GYM, ("sports_and_recreation", "sport_or_fitness_facility", "gym")),
        (Kind.GYM, ("sports_and_recreation", "sport_or_fitness_facility")),
        (Kind.GYM, ("lifestyle_services", "wellness_service", "health_and_wellness_club")),
        (Kind.COFFEE, ("food_and_drink", "casual_eatery", "bakery")),
        (Kind.COFFEE, ("food_and_drink", "casual_eatery", "sandwich_shop")),
        (Kind.COFFEE, ("food_and_drink", "non_alcoholic_beverage_venue", "coffee_shop")),
    ],
)
def test_a_place_is_of_a_kind_where_a_category_of_the_kind_stands_on_its_path(
    kind: Kind, path: tuple[str, ...]
):
    assert is_of_kind(record(*path), kind)


@pytest.mark.parametrize(
    ("kind", "path"),
    [
        (Kind.GROCER, ("services_and_business", "financial_service", "atm")),
        (Kind.GROCER, ("travel_and_transportation", "fueling_station", "gas_station")),
        (Kind.GROCER, ("shopping", "specialty_store", "pharmacy_and_drug_store", "pharmacy")),
        (Kind.GROCER, ("shopping",)),
        (Kind.GROCER, ("food_and_drink", "casual_eatery", "cafe")),
        (Kind.GYM, ("health_care", "hospital")),
        (Kind.GYM, ("sports_and_recreation", "sport_league")),
        (Kind.COFFEE, ("services_and_business", "rental_service", "rental_kiosk")),
        (Kind.COFFEE, ()),
    ],
)
def test_a_bank_a_pharmacy_or_a_petrol_station_of_a_chain_is_not_of_its_kind(
    kind: Kind, path: tuple[str, ...]
):
    assert not is_of_kind(record(*path), kind)


def test_a_place_to_eat_or_drink_is_whatever_the_file_files_under_food_and_drink():
    assert eats_or_drinks(record("food_and_drink", "restaurant", "asian_restaurant"))
    assert eats_or_drinks(record("food_and_drink", "alcoholic_beverage_venue", "bar"))
    assert eats_or_drinks(record("food_and_drink"))
    assert not eats_or_drinks(record("shopping", "food_and_beverage_store", "grocery_store"))
    assert not eats_or_drinks(record())
    assert set(OF_KIND) == set(Kind)


# A table that is not one


def test_two_rows_that_could_claim_one_place_are_refused():
    for other in (
        row("gildcrest"),
        row("plainfare", spellings=("GILDCREST",)),
        row("plainfare", wikidata=("Q1",)),
    ):
        with pytest.raises(TableError):
            checked((row(wikidata=("Q1",)), other), "made up")
    with pytest.raises(TableError):
        checked((), "made up")
    assert len(checked((row(), row("plainfare")), "made up").chains) == 2


@pytest.mark.parametrize(
    "said",
    [
        {"tier": "luxury"},
        {"kind": "bank"},
        {"key": "Gild crest"},
        {"wikidata": ("771734",)},
        {"spellings": (" Gildcrest",)},
        {"spellings": ("Gildcrest", "Gildcrest")},
        {"owner": "somebody"},
    ],
)
def test_a_row_that_is_not_a_row_is_refused(said: dict[str, object], tmp_path: Path):
    fields = row().model_dump(mode="json") | said
    lines = ["schema_version = 1", 'read_in = "made up"', "[[chain]]"]
    # A row as TOML writes one: a list, true or false, or a word between quotes.
    lines += [f"{name} = {json.dumps(held)}" for name, held in fields.items()]
    path = tmp_path / "table.toml"
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(TableError) as refused:
        brand_table.read(path)
    # The refusal says which row, and repeats nothing the row holds.
    assert "row 1" in str(refused.value) and "luxury" not in str(refused.value)


@pytest.mark.parametrize(
    "written",
    [
        "",
        "schema_version = 2\nread_in = 'made up'\n",
        "schema_version = 1\n",
        "schema_version = 1\nread_in = 'made up'\nchain = 'Gildcrest'\n",
        "schema_version = 1\nread_in = 'made up'\n[[brand]]\nkey = 'gildcrest'\n",
        "not toml at all [",
    ],
)
def test_a_file_that_is_no_table_is_refused(written: str, tmp_path: Path):
    path = tmp_path / "table.toml"
    path.write_text(written, encoding="utf-8")
    with pytest.raises(TableError):
        brand_table.read(path)
    with pytest.raises(TableError):
        brand_table.read(tmp_path / "missing.toml")
