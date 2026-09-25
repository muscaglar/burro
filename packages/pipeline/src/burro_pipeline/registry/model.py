"""The shape of one licence registry entry."""

from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class Licence(StrEnum):
    OGL_3 = "OGL-3.0"
    OGL_2 = "OGL-2.0"
    CC0_1 = "CC0-1.0"
    ODBL_1 = "ODbL-1.0"
    CDLA_PERMISSIVE_2 = "CDLA-Permissive-2.0"
    APACHE_2 = "Apache-2.0"
    CC_BY_4 = "CC-BY-4.0"
    CC_BY_SA_4 = "CC-BY-SA-4.0"
    CC_BY_SA_2 = "CC-BY-SA-2.0"
    OPEN_PARLIAMENT = "Open-Parliament-Licence"
    TFL_OPEN_DATA = "TfL-Open-Data"
    NETWORK_RAIL_OGL_BASED = "Network-Rail-OGL-based"
    BESPOKE = "Bespoke-terms"
    NONE_STATED = "None-stated"


SHARE_ALIKE_LICENCES = frozenset({Licence.ODBL_1, Licence.CC_BY_SA_4, Licence.CC_BY_SA_2})
NO_ATTRIBUTION_LICENCES = frozenset({Licence.CC0_1})


class Status(StrEnum):
    APPROVED = "approved"  # licence confirmed from a primary source; may be ingested
    GATED = "gated"  # wanted for v1, but a named check must pass first
    HELD = "held"  # not used in v1
    BANNED = "banned"  # must never be used


class Use(StrEnum):
    GAZETTEER = "gazetteer"
    CELLS = "cells"
    DESTINATION_SEARCH = "destination_search"
    ROUTING = "routing"
    BASEMAP = "basemap"
    SCORING = "scoring"
    DISPLAY = "display"
    PROFILE_TEXT = "profile_text"
    # Shown as the statistics office's own table on an area's page. See ADR 0014.
    CENSUS_TABLE = "census_table"
    AUDIT_ONLY = "audit_only"
    VALIDATION_ONLY = "validation_only"
    PROTOTYPING_ONLY = "prototyping_only"


# Uses that never reach a user. A held source may have these and nothing else.
INTERNAL_USES = frozenset({Use.AUDIT_ONLY, Use.VALIDATION_ONLY, Use.PROTOTYPING_ONLY})

# Share-alike data is kept out of the gazetteer and the scoring tables, so the
# obligation to publish derived data cannot spread to them. See ADR 0004.
SHARE_ALIKE_ALLOWED_USES = frozenset(
    {Use.BASEMAP, Use.ROUTING, Use.DISPLAY, Use.PROFILE_TEXT} | INTERNAL_USES
)

# The census tables an area's page may show: household composition, country of birth,
# age by five-year bands, ethnic group and religion. See ADR 0014.
SHOWN_TABLES = frozenset({"TS003", "TS004", "TS007A", "TS021", "TS030"})

# The two of them that may also feed a score: household composition and age by five-year
# bands. The founder decided it on 24 September 2026, for these two and no other. See the
# amendment of that day to ADR 0006.
SCORED_TABLES = frozenset({"TS003", "TS007A"})

# The census tables held under housing: accommodation type, bedrooms and tenure. Every
# other census table is taken to be about residents, so that a table nobody has thought
# about is fenced, not let through.
HOUSING_TABLES = frozenset({"TS044", "TS050", "TS054"})


class CommercialUse(StrEnum):
    YES = "yes"
    YES_WITH_CONDITIONS = "yes_with_conditions"
    NO = "no"
    UNKNOWN = "unknown"


class VerifiedHow(StrEnum):
    PRIMARY_SOURCE = "primary_source"
    SECONDARY_SOURCE = "secondary_source"
    UNVERIFIED = "unverified"


class Dimension(StrEnum):
    GEOGRAPHY = "geography"
    DESTINATION_SEARCH = "destination_search"
    TRANSPORT = "transport"
    BASEMAP = "basemap"
    HOUSING = "housing"
    SAFETY = "safety"
    SCHOOLS = "schools"
    ENVIRONMENT = "environment"
    PLACES = "places"
    CULTURE = "culture"
    HERITAGE = "heritage"
    TEXT = "text"
    AUDIT = "audit"
    RESIDENTS = "residents"


# A census table's code, as the statistics office writes it: TS021, TS007A.
TableCode = Annotated[str, Field(pattern=r"^TS[0-9]{3}[A-Z]?$")]


class Source(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    name: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    url: str
    dimension: Dimension
    tables: tuple[TableCode, ...] = ()
    licence: Licence
    additional_licences: tuple[Licence, ...] = ()
    licence_url: str = ""
    commercial_use: CommercialUse
    share_alike: StrictBool
    attribution: str = ""
    attribution_verified: StrictBool = False
    # True where the publisher asks that its statement stands wherever a figure made from
    # the data is shown, and not on the page of attributions alone. A release then says so
    # of the source, and every fact that cites it carries the statement.
    attribution_beside_figures: StrictBool = False
    conditions: tuple[str, ...] = ()
    status: Status
    status_reason: str = ""
    before_launch: tuple[str, ...] = ()
    uses: tuple[Use, ...] = ()
    cadence: str = ""
    verified_how: VerifiedHow
    verified_on: date
    evidence_urls: tuple[str, ...] = ()
    # The addresses its files are fetched from: a whole address, or a prefix that ends in
    # `/` and at the dataset. A file is fetched from no other address. See `addresses.py`.
    file_urls: tuple[str, ...] = ()
    notes: str = ""

    @property
    def licences(self) -> frozenset[Licence]:
        return frozenset({self.licence, *self.additional_licences})
