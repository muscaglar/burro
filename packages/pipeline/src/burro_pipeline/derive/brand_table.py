"""The table of tiers, and which place of the file is a place of which chain.

The founder decided on 2026-09-24 that the chains of grocers, of gyms and of
coffee in a place say something of it, and gave a table: which chain is
premium, which is mid-range and which is value (ADR 0026). The table is an
opinion, and a person adjusts it. So it is data, in `brand_tiers.toml` beside
this module, and this module reads it and holds no chain and no tier of its
own.

**Which chain a place is of.** The file gives a place a brand where its
publisher has matched it to a chain: a name, and for some the id an
encyclopaedia gives the chain. A place is of a row of the table where its
brand has an id the row holds, which is the surest key. Where it has no id of
any row, it is of the row that holds the name as it is written. A name is
held to the letter, but for its case and for which mark stands for an
apostrophe: nothing is matched by a part of a name, so a bank or an undertaker
that shares a word with a grocer is no grocer.

**What kind of place it is.** A chain of grocers keeps banks, pharmacies and
petrol stations too, and the file gives each the chain's brand. So a place of
a chain counts as the chain's kind only where the file also gives it a
category of that kind. The categories are `OF_KIND`, and each is the
publisher's own word.

| Kind | A category anywhere on the path of the place |
|---|---|
| A grocer | A grocery, a convenience, frozen food or discount store, or a department store |
| A gym | A sport or fitness facility, or a health and wellness club |
| Coffee | Anything the publisher files under food and drink |

A department store is there for one chain, whose larger shops the file calls
department stores and which sell food in nearly every one. A petrol station is
not: it stands beside the shop it belongs to, and would count the shop twice.

**A brand that is on no row has no tier.** It is a chain and nothing more:
it counts where chains are told from independent places, and nowhere else.

This module reads the table and no other file. It names no place.
"""

import re
import tomllib
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from functools import cache, cached_property
from pathlib import Path
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from burro_pipeline.derive.culture_file import Brand, Record

TABLE = Path(__file__).with_name("brand_tiers.toml")
SCHEMA_VERSION = 1
KEY = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"
WIKIDATA = r"^Q[1-9][0-9]*$"
# The marks a file may write where an apostrophe goes. Each is read as one.
APOSTROPHES = "\N{RIGHT SINGLE QUOTATION MARK}\N{LEFT SINGLE QUOTATION MARK}`\N{PRIME}"


class Kind(StrEnum):
    """The three kinds of place the table holds, in the order the founder's table lists them."""

    GROCER = "grocer"
    GYM = "gym"
    COFFEE = "coffee"


class Tier(StrEnum):
    """The three tiers, from premium to value."""

    PREMIUM = "premium"
    MID = "mid"
    VALUE = "value"


# The top of the branch that holds every place to eat, to drink and for coffee.
FOOD_AND_DRINK = "food_and_drink"
# The categories that make a place of a chain a place of the chain's kind, as the publisher
# writes them. A place counts where one of these stands anywhere on its path.
OF_KIND: Mapping[Kind, frozenset[str]] = MappingProxyType(
    {
        Kind.GROCER: frozenset(
            {
                "grocery_store",
                "convenience_store",
                "frozen_foods_store",
                "discount_store",
                "department_store",
            }
        ),
        Kind.GYM: frozenset({"sport_or_fitness_facility", "health_and_wellness_club"}),
        Kind.COFFEE: frozenset({FOOD_AND_DRINK}),
    }
)


class TableError(ValueError):
    """The table of tiers is not as it must be. The message names a row by its key alone."""


class Chain(BaseModel):
    """One row of the table: a chain, its kind, its tier and how the file writes it."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    key: str = Field(pattern=KEY)
    name: str = Field(min_length=1)
    kind: Kind
    tier: Tier
    on_the_founders_table: bool
    wikidata: tuple[str, ...]
    spellings: tuple[str, ...]

    @model_validator(mode="after")
    def _holds_together(self) -> "Chain":
        if not all(re.fullmatch(WIKIDATA, one) for one in self.wikidata):
            raise ValueError("an id of the encyclopaedia is Q and a number")
        if any(not one.strip() or one != one.strip() for one in self.spellings):
            raise ValueError("a spelling is written as the file writes it, with no space round it")
        if len(set(self.wikidata)) != len(self.wikidata):
            raise ValueError("an id is listed once")
        if len(set(self.spellings)) != len(self.spellings):
            raise ValueError("a spelling is listed once")
        return self


def folded(name: str) -> str:
    """A name as it is compared: in small letters, with one mark for every apostrophe."""
    plain = name.strip().casefold()
    for mark in APOSTROPHES:
        plain = plain.replace(mark, "'")
    return " ".join(plain.split())


@dataclass(frozen=True)
class Table:
    """The table of tiers, as it is read: every chain, and how a brand finds its row."""

    chains: tuple[Chain, ...]
    # Which release of the file the ids and the spellings were read in.
    read_in: str

    @cached_property
    def by_key(self) -> dict[str, Chain]:
        return {chain.key: chain for chain in self.chains}

    @cached_property
    def by_id(self) -> dict[str, Chain]:
        return {one: chain for chain in self.chains for one in chain.wikidata}

    @cached_property
    def by_spelling(self) -> dict[str, Chain]:
        return {folded(one): chain for chain in self.chains for one in chain.spellings}

    def of(self, kind: Kind, tier: Tier) -> tuple[Chain, ...]:
        """The chains of one kind and one tier, in the order of the table."""
        return tuple(chain for chain in self.chains if (chain.kind, chain.tier) == (kind, tier))


def checked(chains: tuple[Chain, ...], read_in: str) -> Table:
    """The table, if no two rows could claim one place. `TableError` if two could."""
    keys = [chain.key for chain in chains]
    ids = [one for chain in chains for one in chain.wikidata]
    # Two spellings of one row may differ in nothing but their case. Each is kept, because
    # it is how the file writes the chain, and the two find the one row.
    spellings = [one for chain in chains for one in {folded(one) for one in chain.spellings}]
    for what, held in (("key", keys), ("id", ids), ("spelling", spellings)):
        if len(set(held)) != len(held):
            raise TableError(f"two rows of the table of tiers hold one {what}")
    if not chains:
        raise TableError("the table of tiers holds no row")
    return Table(chains=chains, read_in=read_in)


def read(path: Path = TABLE) -> Table:
    """The table of tiers, from its file. `TableError` for a file that is not one."""
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError:
        raise TableError("the table of tiers could not be read from disk") from None
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise TableError("the table of tiers is not valid TOML") from None
    if document.get("schema_version") != SCHEMA_VERSION:
        raise TableError(f"the table of tiers must say schema_version = {SCHEMA_VERSION}")
    if set(document) - {"schema_version", "read_in", "chain"}:
        raise TableError("the table of tiers holds what is no row: rows are written as [[chain]]")
    rows = document.get("chain", [])
    read_in = document.get("read_in", "")
    if not isinstance(rows, list) or not isinstance(read_in, str) or not read_in:
        raise TableError("the table of tiers says what it was read in, and holds rows")
    chains: list[Chain] = []
    for position, row in enumerate(rows, start=1):  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        try:
            chains.append(Chain.model_validate(row))
        except ValidationError:
            raise TableError(f"row {position} of the table of tiers is not a row") from None
    return checked(tuple(chains), read_in)


@cache
def of_the_repository() -> Table:
    """The table of tiers of the repository, read once, whatever table a build uses."""
    return read()


# The table a build uses in the place of the repository's, while it is one that a person
# changed at the panel of the review desk. It is set for one build, and put back after it.
_IN_ITS_PLACE: list[Table] = []


def the_table() -> Table:
    """The table of tiers: the repository's, read once, unless a build uses another."""
    return _IN_ITS_PLACE[0] if _IN_ITS_PLACE else of_the_repository()


@contextmanager
def using(table: Table) -> Generator[None]:
    """Use a table in the place of the repository's, until the block ends.

    It is for the table with what a person decided laid over it, which is of
    one build and of no other. One build uses one table: a second inside the
    first is refused.
    """
    if _IN_ITS_PLACE:
        raise RuntimeError("a build uses one table of tiers")
    _IN_ITS_PLACE.append(table)
    try:
        yield
    finally:
        _IN_ITS_PLACE.clear()


def chain_of(brand: Brand | None, table: Table) -> Chain | None:
    """The row of the table a brand is of, or none where it is on no row.

    An id of a row decides. A brand with no id of any row is of the row that
    holds its name as it is written.
    """
    if brand is None:
        return None
    by_id = table.by_id
    if brand.wikidata is not None and brand.wikidata in by_id:
        return by_id[brand.wikidata]
    return None if brand.name is None else table.by_spelling.get(folded(brand.name))


def is_of_kind(record: Record, kind: Kind) -> bool:
    """Whether the file gives a place a category of a kind, anywhere on its path."""
    return bool(OF_KIND[kind] & {*record.hierarchy, *([record.primary] if record.primary else [])})


def eats_or_drinks(record: Record) -> bool:
    """Whether the file files a place under food and drink: to eat, to drink or for coffee."""
    return record.hierarchy[:1] == (FOOD_AND_DRINK,) or record.primary == FOOD_AND_DRINK
