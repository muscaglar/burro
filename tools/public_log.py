"""Run one step of a data build, and let only step names, counts and hashes be seen.

The log of a public repository is read by anyone, and it cannot be taken back.
So a step's own words never reach it. This runs the step, reads every line it
writes, and shows a line only if it holds nothing but `name=value`, where the
name is on the list in this file and the value has the shape the list gives
it: a whole number, a hash, or a word from a short list. A name that is not on
the list is withheld whatever stands after it, because a name can carry a row
as well as a value can. Every other line is counted and withheld, a traceback
included. A line that holds a secret, in any form it is likely to be printed
in, fails the step whatever the step returned.

A step that prints a new name adds it to the list here, in the same change.

    python tools/public_log.py --step assemble -- uv run burro-release check FOLDER
    python tools/public_log.py mask
    python tools/public_log.py mask --made-up

`mask` checks every secret it is given: that it is set, and pasted whole. It
then tells the runner to hide what is made from one: the host inside the
store's address, and a key as it is sent. The runner hides only the exact
value of a secret by itself.

`mask --made-up` is for a workflow of which no step reads the store. Its
environment holds made-up values, so that a key is never kept where it is
used for nothing. Each value is checked as `mask` checks it, and must also be
one that opens nothing: an address that ends `.invalid`, and for every other
secret a value that begins `rehearsal-`.

A step run this way cannot write to the run's summary or to a job's outputs:
it is not told where they are. With debug logging on, no step is run at all:
what the runner adds to a log then is not known.

Standard library only. See docs/data-builds.md.
"""

import argparse
import base64
import os
import re
import subprocess
import sys
import time
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from functools import cache
from pathlib import Path
from typing import Any, TextIO, cast
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
# The lists of files a fetch takes. Each names its files, and both names are public.
LISTS = ROOT / "packages" / "pipeline" / "src" / "burro_pipeline" / "fetch" / "lists"

# The names the code reads, in burro_pipeline.fetch. Each is a secret of the
# environment a job runs in, and its value is in no file.
ENDPOINT = "BURRO_STORE_ENDPOINT"
KEY_ID = "BURRO_STORE_KEY_ID"
KEY = "BURRO_STORE_SECRET"
STORE = (ENDPOINT, "BURRO_STORE_BUCKET", KEY_ID, KEY)
# Where a publisher can write to. It is sent to publishers, and kept out of this repository.
CONTACT = "BURRO_FETCH_CONTACT"
# The names burro_pipeline.kept reads: the bucket a release is kept in, which is not the
# store of publishers' files and has keys of its own. They stand in the order of `STORE`.
RELEASES = (
    "BURRO_RELEASES_ENDPOINT",
    "BURRO_RELEASES_BUCKET",
    "BURRO_RELEASES_KEY_ID",
    "BURRO_RELEASES_SECRET",
)
# The two stores a step may be given the key of. Each has an address and a key of its own.
STORES = (STORE, RELEASES)
ENDPOINTS = tuple(names[0] for names in STORES)
# Which secrets each environment holds. A workflow may name no other. A fetch reads the
# contact, so a workflow whose environment holds none can fetch nothing. The build of London
# reads the store with one key and keeps a release with another, and no other workflow
# is given a key that writes a release.
SECRETS_OF = {
    "data-fetch": (*STORE, CONTACT),
    "data-held": STORE,
    "data-build": STORE,
    "data-travel": STORE,
    "data-london": (*STORE, *RELEASES),
}
SECRET_NAMES = (*STORE, CONTACT, *RELEASES)
# The run's own token. The runner sets it, and no step here is given it.
TOKENS = ("GITHUB_TOKEN", "GH_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")
# A shorter secret is found in lines that do not hold it, so it cannot be searched for.
SHORTEST_SECRET = 8
# What a made-up secret looks like. An address that ends so can never be reached.
MADE_UP, MADE_UP_HOST = "rehearsal-", ".invalid"

# The runner sets this, to 1, when a run was started with debug logging.
DEBUG = "RUNNER_DEBUG"

# Where a step could write something the website shows. A step is not told.
RUNNERS_FILES = (
    "GITHUB_STEP_SUMMARY",
    "GITHUB_OUTPUT",
    "GITHUB_ENV",
    "GITHUB_PATH",
    "GITHUB_STATE",
)

STEPS = frozenset(
    {
        # What is held and how old it is, which is read before a fetch, and what moved
        # between two builds, which is read before the newer is approved.
        "fresh",
        "moved",
        # The steps of a build, as docs/design/london-data-pipeline.md numbers them.
        "plan",
        "fetch",
        "seal",
        "normalise",
        "cells",
        "names",
        # What a person decided at the panel of the review desk, where a build is given it.
        "changes",
        "network",
        "derive",
        "travel",
        "cost",
        "income",
        "places",
        "stations",
        "residents",
        "claims",
        "assemble",
        "check",
        "report",
        "publish",
        # What becomes of a release once it is built: its lock, the bucket it is kept in,
        # and the folder an image is built from.
        "lock",
        "keep",
        "take",
        # The draft of the areas, which a hosted build makes before it builds. It prints
        # under a name of its own, and why it stopped is the name of a rule.
        "areas-draft",
        # What a workflow does around them.
        "secrets",
        "store",
        "manifest",
        "compare",
        "canary",
        "search",
    }
)
STATUSES = frozenset({"ok", "failed", "refused", "skipped", "missing", "differs", "unreadable"})
RELEASE_FILES = frozenset(
    {
        "catalogue.json",
        "cost.json",
        "coverage.json",
        "destinations.json",
        "evidence.json",
        "features.json",
        "geometry.json",
        "lock.json",
        "manifest.json",
        "neighbourhoods.json",
        "places.json",
        "stations.json",
        "tags.json",
        "travel.bin",
        "travel.json",
    }
)
# The files a build writes beside its release, which are not above: the record of the
# build, its hashes, the homes of each area, the report, the name each area bears, and the
# estimates of household income. A name says what a file is, and holds nothing from it.
BESIDE_FILES = frozenset(
    {"build.json", "coverage.md", "hashes.json", "homes.json", "income.json", "names.csv"}
)
# The folders a build writes: the release, the folder of its build, and the folder of
# household income that stands beside it.
FOLDERS = frozenset({"release", "build", "income"})

# What a step may count. Each is followed by a whole number and by nothing else.
COUNTS = frozenset(
    {
        # This file, and the step that checks the secrets.
        "exit",
        "withheld",
        "secrets",
        "debug",
        "short",
        "set",
        "real",
        # The canary, and the search of the logs.
        "steps",
        "found",
        "unread",
        "uncaught",
        "jobs",
        "logs",
        "artifacts",
        # The two builds that are compared.
        "wrong",
        "unlisted",
        "differing",
        # Fetch, and what the store holds.
        "n",
        "files",
        "bytes",
        "new",
        "same",
        "by_hand",
        "ready",
        "receipts",
        "lists",
        # How old the files that have a receipt are: how many days ago one was retrieved,
        # how many stand each way, and how many sources say no cadence that is read.
        "days",
        "due",
        "fresh",
        "not_known",
        "older",
        "not_said",
        # What moved between two builds: of the areas, the measures, the vibes, the
        # prices, the files behind each build and the first ten areas of a search.
        "came",
        "went",
        "changed",
        "gained",
        "lost",
        "up",
        "down",
        "kept",
        "reordered",
        "search",
        "searches",
        "searches_moved",
        "areas_came",
        "areas_went",
        "areas_renamed",
        "areas_redrawn",
        "measures_came",
        "measures_went",
        "measures_moved",
        "vibes_came",
        "vibes_went",
        "vibes_moved",
        "costs_moved",
        "files_changed",
        "files_came",
        "files_went",
        # What came and went of the catalogue itself between two builds: the version on
        # each side, the parts of a recipe, its shares, the measures and the vibes that
        # bear another name, and the vibes that became a rough guide or ceased to be one.
        "catalogue_before",
        "catalogue_after",
        "parts_came",
        "parts_went",
        "shares_changed",
        "names_changed",
        "rough_came",
        "rough_went",
        # The lock, the check of the evidence, and the coverage report.
        "inputs",
        "development",
        # Of the files that state their own edition: how many a build took, how many of
        # those it was told to take, and how many receipts of other editions it left.
        "own_edition",
        "named",
        "passed_over",
        "facts",
        "rows",
        "findings",
        "areas",
        "measures",
        "vibes",
        "values",
        "gaps",
        "no_record",
        # The file of changes a build was given: its lines, how many stand, and how many
        # of those the build applied.
        "lines",
        "stand",
        "applied",
        # The geography of a build.
        "output_areas",
        "lsoas",
        "msoas",
        "boroughs",
        # The journeys of a build: what the timetable holds, and what was routed.
        "stops",
        "routes",
        "trips",
        "running",
        "calls",
        "origins",
        "destinations",
        "departures",
        "shards",
        "pairs",
        "beyond",
    }
)
# The rules of the travel step: of the timetable it reads, and of what it routes. A refusal
# names its rule. A test of the pipeline holds this list to the rules there are.
TRAVEL_RULES = frozenset(
    {
        "answers_are_whole",
        "calendar_covers_the_day",
        "calendar_is_readable",
        "destination_is_on_a_street",
        "engine_is_installed",
        "feed_holds_its_tables",
        "feed_is_a_zip",
        "homes_have_a_weight",
        "ids_are_unique",
        "no_trip_is_a_headway",
        "origin_is_on_a_street",
        "origins_are_given_once",
        "references_resolve",
        "same_twice",
        "stop_has_a_point",
        "stop_is_on_a_street",
        "table_holds_its_columns",
        "times_are_in_order",
        "window_is_in_the_timetable",
    }
)
# The rules of the lock and of the evidence. A refusal names its rule, and a check
# counts its findings by rule. A test holds this list to the rules there are.
RULES = frozenset(
    {
        "commit_is_checked_out",
        "commit_is_named",
        "build_is_as_it_was_written",
        "credit_is_the_registrys",
        "evidence_is_for_the_product",
        "evidence_is_of_this_release",
        "fact_has_a_row",
        "file_is_for_the_product",
        "file_is_in_the_vault",
        "gate_refuses",
        "input_has_one_receipt",
        "input_is_allowed",
        "input_is_as_described",
        "input_is_for_the_product",
        "input_is_locked",
        "licence_evidence_is_saved",
        "listed_file_has_a_receipt",
        "listed_file_has_one_receipt",
        "lock_has_an_input",
        "lock_is_for_the_product",
        "lock_is_valid",
        "made_up_is_consistent",
        "measure_has_a_figure",
        "measure_is_as_core_says",
        "measure_is_not_held_back",
        "method_is_found",
        "named_edition_has_a_receipt",
        "one_receipt_for_a_file",
        "percentile_is_cores",
        "real_build_needs_a_registry",
        "real_release_needs_a_lock",
        "real_release_needs_a_registry",
        "real_release_needs_its_hashes",
        "receipt_is_as_committed",
        "receipt_is_listed",
        "receipt_is_the_locked_file",
        "receipt_is_valid",
        "repository_is_read",
        "row_has_a_fact",
        "row_has_a_value",
        "row_holds_the_coverage",
        "row_holds_the_figure",
        "row_names_its_method",
        "row_rests_on_its_file",
        "source_has_a_file",
        "source_is_registered",
        "tag_is_cores",
        "tree_has_no_changes",
    }
)
# What fetch says the kind of: the store a step was given, and what arrived in place of a
# file. Each is a word that burro_pipeline.fetch prints, and a test there holds this list
# to it. A word says what a file is, and holds nothing from it.
KINDS = frozenset(
    {
        # A store.
        "folder",
        "object_store",
        # What arrived.
        "csv",
        "zip",
        "workbook",
        "geopackage",
        "sqlite",
        "html",
        "xml",
        "json",
        "pdf",
        "xls",
        "ods",
        "gzip",
        "parquet",
        "empty",
        "unknown",
    }
)
# What the step `fresh` says of a file that has a receipt: how often its publisher says it
# changes, how it stands against that, and what of its list pins it. Each is a word that
# burro_pipeline.upkeep prints, and a test there holds these lists to it.
CADENCES = frozenset({"weekly", "monthly", "quarterly", "yearly", "rarely", "not_said"})
STATES = frozenset({"due", "fresh", "not_known", "older", "unlisted"})
PINS = frozenset({"none", "period", "edition_and_period", "not_listed"})
# The measures a build may name: the ids of core's catalogue, which is in this repository.
# A test holds this list to it. An id names an idea and holds nothing from a file.
FEATURES = frozenset(
    {
        "air_no2",
        "brand_aldi",
        "brand_anytime_fitness",
        "brand_asda",
        "brand_barrys",
        "brand_blank_street",
        "brand_coop",
        "brand_costa",
        "brand_david_lloyd",
        "brand_equinox",
        "brand_gails",
        "brand_greggs",
        "brand_gymbox",
        "brand_iceland",
        "brand_lidl",
        "brand_mands",
        "brand_mix",
        "brand_morrisons",
        "brand_nero",
        "brand_nuffield",
        "brand_ole_and_steen",
        "brand_pret",
        "brand_puregym",
        "brand_sainsburys",
        "brand_starbucks",
        "brand_tesco",
        "brand_the_gym_group",
        "brand_third_space",
        "brand_virgin_active",
        "brand_waitrose",
        "brand_whole_foods",
        "bus_routes_nearby",
        "bus_stops_nearby",
        "centre_compact",
        "centre_small",
        "coffee_mid_distance",
        "coffee_mid_nearby",
        "coffee_premium_distance",
        "coffee_premium_nearby",
        "coffee_value_distance",
        "coffee_value_nearby",
        "conservation_cover",
        "crime_burglary_theft",
        "crime_violence_robbery",
        "cuisine_variety",
        "culture_venues",
        "culture_venues_per_homes",
        "evening_cluster_exposure",
        "gp_walk",
        "green_cover",
        "grocer_mid_distance",
        "grocer_mid_nearby",
        "grocer_premium_distance",
        "grocer_premium_nearby",
        "grocer_value_distance",
        "grocer_value_nearby",
        "grocery_walk",
        "gym_mid_distance",
        "gym_mid_nearby",
        "gym_premium_distance",
        "gym_premium_nearby",
        "gym_value_distance",
        "gym_value_nearby",
        "highstreet_access",
        "highstreet_conserved",
        "homes_density",
        "homes_flats",
        "homes_higher_bands",
        "homes_post2000",
        "homes_pre1919",
        "households_dependent_children",
        "households_one_person",
        "incident_antisocial",
        "incident_criminal_damage",
        "independents_nearby",
        "land_gardens",
        "land_industry",
        "land_storage",
        "land_transport_other",
        "land_woodland",
        "listed_buildings",
        "noise_exposure",
        "overground_proximity",
        "park_facilities",
        "park_large_proximity",
        "park_proximity",
        "pharmacy_walk",
        "play_space_proximity",
        "price_median",
        "price_rise_10y",
        "price_rise_5y",
        "private_outdoor_space",
        "rail_proximity",
        "residents_aged_20_34",
        "residents_aged_65_over",
        "road_major_exposure",
        "road_traffic_nearby",
        "school_primary_attainment",
        "school_primary_nearby",
        "school_secondary_attainment",
        "station_lines",
        "station_walk",
        "underground_proximity",
        "university_proximity",
        "venue_cafe",
        "venue_cafe_per_homes",
        "venue_evening",
        "venue_evening_per_homes",
        "venue_food_drink",
        "venue_food_drink_per_homes",
        "venue_gym",
        "venue_gym_per_homes",
        "venue_independent",
        "water_access",
    }
)
# The vibes a step may name: the ids of core's catalogue. A test holds this list to it.
VIBES = frozenset(
    {
        "built_age",
        "everyday_on_foot",
        "family_amenities",
        "family_area",
        "foodie",
        "homes",
        "leafy",
        "pace",
        "parks_close_by",
        "quiet_residential",
        "street_character",
        "village_feel",
        "well_connected",
        "works_warehouses",
        "young_professionals",
    }
)
# What is shown as a hash: of a file, or of what a step wrote.
HASHES = frozenset(
    {
        "sha256",
        "manifest_sha256",
        "lock_sha256",
        "evidence_sha256",
        "coverage_sha256",
        "changes_sha256",
    }
)

TOKEN = re.compile(r"([a-z][a-z0-9_]{0,39})=(\S{1,80})")
COUNT = re.compile(r"[0-9]{1,15}")
SECONDS = re.compile(r"[0-9]{1,9}(\.[0-9]{1,3})?")
SHA256 = re.compile(r"[0-9a-f]{64}")
FILE_ID = re.compile(r"f-[0-9a-f]{12}")
RELEASE_ID = re.compile(r"[a-z]{3}-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}")
# A day: the day a file was retrieved, and the day the days are counted to.
DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
# The reason a file was not fetched, as a number: `python -m burro_pipeline why` lists them.
WHY = re.compile(r"[0-9]{1,2}")
# The status a publisher answered with.
HTTP = re.compile(r"[1-5][0-9]{2}")
# A host is never shown by name. What is shown is the start of a hash of it.
HOST = re.compile(r"[0-9a-f]{12}")


@cache
def registry_ids() -> frozenset[str]:
    """Every id in the licence registry. They are public: the registry is in this repository."""
    found = {"synthetic"}
    for file in sorted((ROOT / "registry" / "sources").glob("*.toml")):
        try:
            document = tomllib.loads(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        entries = cast(list[dict[str, Any]], document.get("source", []))
        found |= {str(entry.get("id", "")) for entry in entries}
    return frozenset(found)


@cache
def listed() -> dict[str, frozenset[str]]:
    """The name of every list of files, and the name of every item of a list.

    They are public: the lists are in this repository. A name is one a person gave a
    file, and holds nothing from a file.
    """
    lists: set[str] = set()
    items: set[str] = set()
    for file in sorted(LISTS.glob("*.toml")):
        try:
            document = tomllib.loads(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        lists.add(str(document.get("build", "")))
        entries = cast(list[dict[str, Any]], document.get("file", []))
        items |= {str(entry.get("item", "")) for entry in entries}
    return {"list": frozenset(lists - {""}), "item": frozenset(items - {""})}


def _may_be_shown(key: str, value: str) -> bool:
    """Whether a name is on the list, and what stands after it has the shape the list gives."""
    if key == "step":
        return value in STEPS
    if key == "status":
        return value in STATUSES
    if key == "copy":
        return value in ("a", "b")
    if key == "source":
        return value in registry_ids()
    if key in ("list", "item"):
        return value in listed()[key]
    if key == "file":
        return value in RELEASE_FILES | BESIDE_FILES
    if key == "folder":
        return value in FOLDERS
    if key == "kind":
        return value in KINDS
    if key == "feature":
        return value in FEATURES
    if key == "vibe":
        return value in VIBES
    if key in ("cadence", "state", "pins"):
        return value in {"cadence": CADENCES, "state": STATES, "pins": PINS}[key]
    shape = (
        SHA256
        if key in HASHES
        # Fetch counts its files by how each ended, so a status is a name too.
        else COUNT
        if key in COUNTS or key in RULES or key in TRAVEL_RULES or key in STATUSES
        else {
            "release": RELEASE_ID,
            "before": RELEASE_ID,
            "after": RELEASE_ID,
            "file_id": FILE_ID,
            "seconds": SECONDS,
            "why": WHY,
            "http": HTTP,
            "host": HOST,
            "retrieved": DAY,
            "on": DAY,
        }.get(key)
    )
    return shape is not None and shape.fullmatch(value) is not None


def is_public(line: str) -> bool:
    """Whether a line holds nothing but names on the list, each with a value of its shape."""
    tokens = line.split(" ")
    matches = [TOKEN.fullmatch(token) for token in tokens]
    return all(match is not None and _may_be_shown(match[1], match[2]) for match in matches)


def _as_sent(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _forms(environ: Mapping[str, str]) -> Iterator[tuple[str, bool]]:
    """Each form a secret may be printed in, and whether the runner hides it by itself."""
    for name in (*SECRET_NAMES, *TOKENS):
        if value := environ.get(name, ""):
            yield value, True
            yield _as_sent(value), False
    for endpoint, _, key_id, key in STORES:
        if host := urlsplit(environ.get(endpoint, "")).hostname:
            yield host, False
        if environ.get(key_id) and environ.get(key):
            yield _as_sent(f"{environ[key_id]}:{environ[key]}"), False


def forms_of(environ: Mapping[str, str]) -> frozenset[str]:
    """What to search a line for, in lower case. A line is searched in lower case too."""
    return frozenset(form.lower() for form, _ in _forms(environ))


def holds_a_secret(line: str, forms: frozenset[str]) -> bool:
    lowered = line.lower()
    return any(form in lowered or form in unquote(lowered) for form in forms)


def _too_short(environ: Mapping[str, str]) -> list[str]:
    return [name for name in SECRET_NAMES if 0 < len(environ.get(name, "")) < SHORTEST_SECRET]


def _exit_code(returned: int) -> int:
    """A step killed by a signal returns a negative number. A shell would say 128 and the signal."""
    return returned if returned >= 0 else 128 - returned


def run_step(step: str, command: Sequence[str], environ: Mapping[str, str], out: TextIO) -> int:
    """Run a command and write to `out` only what may be public. Returns the code to exit with."""

    def say(line: str) -> None:
        print(line, file=out, flush=True)

    if environ.get(DEBUG):
        say(f"step={step} status=refused debug=1")
        return 1
    if short := _too_short(environ):
        # `mask` says which. Nothing is run with a secret that cannot be searched for.
        say(f"step={step} status=refused short={len(short)}")
        return 1

    forms = forms_of(environ)
    given = {name: value for name, value in environ.items() if name not in RUNNERS_FILES}
    started = time.monotonic()
    withheld = secrets = 0
    try:
        process = subprocess.Popen(
            list(command),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=given,
        )
    except OSError:
        say(f"step={step} status=failed exit=127 withheld=0")
        return 127
    assert process.stdout is not None
    with process.stdout as written:
        for raw in written:
            line = raw.decode(errors="replace").rstrip("\r\n")
            if holds_a_secret(line, forms):
                secrets += 1
            elif is_public(line):
                say(line)
            else:
                withheld += 1
    code = _exit_code(process.wait())
    seconds = f"{time.monotonic() - started:.1f}"
    if secrets:
        # Every line with a secret was withheld. The key is rotated all the same.
        say(f"step={step} status=failed exit={code} secrets={secrets} withheld={withheld}")
        return code or 1
    status = "failed" if code else "ok"
    say(f"step={step} status={status} exit={code} withheld={withheld} seconds={seconds}")
    return code


def _not_made_up(environ: Mapping[str, str]) -> list[str]:
    """The secrets whose value could be a real one."""

    def made_up(name: str, value: str) -> bool:
        if name in ENDPOINTS:
            return (urlsplit(value).hostname or "").endswith(MADE_UP_HOST)
        return value.startswith(MADE_UP)

    given = ((name, environ.get(name, "")) for name in SECRET_NAMES)
    return [name for name, value in given if value and not made_up(name, value)]


def mask(environ: Mapping[str, str], out: TextIO, made_up: bool = False) -> int:
    """Check every secret the step was given, and have the runner hide what is made from one.

    A secret that does not exist reaches a step as an empty value. So a name
    that is there and empty is a secret that was never stored. With `made_up`,
    a value that could be a real one is refused.
    """
    if environ.get(DEBUG):
        print("error: this run has debug logging on. Start it again without", file=out)
        print("step=secrets status=refused debug=1", file=out)
        return 1
    given = [name for name in SECRET_NAMES if name in environ]
    problems = [f"{name} is not set" for name in given if not environ[name]]
    if not given:
        problems.append("No secret was given to this step")
    problems += [
        f"{name} is shorter than {SHORTEST_SECRET} characters" for name in _too_short(environ)
    ]
    problems += [
        f"{name} holds a space or a line break. Paste it again"
        for name in SECRET_NAMES
        if re.search(r"\s", environ.get(name, ""))
    ]
    for endpoint in ENDPOINTS:
        address = urlsplit(environ.get(endpoint, ""))
        if environ.get(endpoint) and (address.scheme != "https" or not address.hostname):
            problems.append(f"{endpoint} must begin https:// and name a host")
    for problem in problems:
        print(f"error: {problem}. See docs/data-builds.md", file=out)
    if problems:
        print(f"step=secrets status=missing missing={len(problems)}", file=out)
        return 1
    if made_up and (real := _not_made_up(environ)):
        for name in real:
            why = "No step of this workflow reads the store, so it is given made-up values only"
            print(f"error: {name} is not a made-up value. {why}. See docs/data-builds.md", file=out)
        print(f"step=secrets status=refused real={len(real)}", file=out)
        return 1
    for form, hidden_already in sorted(set(_forms(environ))):
        if not hidden_already:
            print(f"::add-mask::{form}", file=out)
    print(f"step=secrets set={len(given)} missing=0", file=out, flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="public_log", description=__doc__)
    parser.add_argument("--step", help="the step's name, from the list in this file")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="`mask`, or `--` and a command")
    args = parser.parse_args(argv)
    command: list[str] = args.command
    if command in (["mask"], ["mask", "--made-up"]) and args.step is None:
        return mask(os.environ, sys.stdout, made_up=len(command) == 2)
    if command[:1] == ["--"]:
        command = command[1:]
    # A name that is not on the list is never repeated: it may not be a name at all.
    if args.step not in STEPS or not command:
        usage = "public_log.py --step NAME -- COMMAND, or public_log.py mask [--made-up]"
        parser.exit(2, f"usage: {usage}\n")
    return run_step(args.step, command, os.environ, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
