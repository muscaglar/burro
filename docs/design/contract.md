# Burro v1 backend contract

Status: built, 2026-09-23. Contract version 2. The three parts exist and `make ci` holds them to this document. What was settled while building is written in where it applies, and [ADR 0010](../adr/0010-one-contract-one-synthetic-release.md) and [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) say why.

Version 2 is the first slice of vibes ([slice-1.md](slice-1.md), [ADR 0013](../adr/0013-vibes-are-the-centre.md)). Every section is written to it, and `packages/core`, `packages/pipeline`, `evals/` and `services/api` are built to it. `contracts/openapi.json` says version 2. `apps/ios` is not: it was built to version 1 and has not been touched.

This is the single source for the three parts of the backend: `packages/core`, the release builder in `packages/pipeline`, and `services/api`. Each can be built alone and must fit the other two. It runs on a synthetic release, so that real data, travel times and live model calls can replace the synthetic ones without changing the code around them.

It applies [PLAN](../PLAN.md) sections 4 to 10 and ADRs [0002](../adr/0002-deterministic-core.md), [0005](../adr/0005-raw-prompts-are-never-stored.md) and [0006](../adr/0006-rank-places-not-residents.md). If code and contract disagree, change one of them in the same commit. Section 13 lists what is a first guess.

## 0. Conventions

| Thing | Rule |
|---|---|
| Models | pydantic v2, `ConfigDict(frozen=True, extra="forbid")`. Sequences are tuples. Enums are `StrEnum` with lower-case values |
| Ids | `^(syn\|lon)-[a-z][0-9a-z]+$`. The prefix is the city; `syn` is synthetic. The letter says what it is: `n` area, `d` destination, `p` place, `s` station. Never reused, never renamed |
| Release id | `^(syn\|lon)-\d{4}-\d{2}-\d{2}-\d{2}$`, for example `syn-2026-09-23-01` |
| Money, minutes | Whole pounds and whole minutes, `int`. Rent is per calendar month |
| Percentile | `float`, 0 to 100, one decimal, mid-rank (section 2.4) |
| Weight | `float`, 0 to 1, in steps of 0.05. `snap(w) = clamp(floor(w * 20 + 0.5), 0, 20) / 20` |
| Rounding | `round` below is Python's built-in `round` on a float, so a tie goes to the even neighbour: `round(72.5)` is 72 and `round(10.5)` is 10. `snap` is the one place that rounds a tie up, and it says so |
| Unknown | A number that is not known is `None` in a record and `null` on the wire. Zero never stands for unknown, except as a sentinel inside `Operations` (section 5.1), where no field may be optional |
| Wire | Where a response holds a core record, it is that record's `model_dump(mode="json")`. A field has one name in core, on disk and on the wire |
| Dates | Date `YYYY-MM-DD`, month `YYYY-MM`, timestamp RFC 3339 in UTC ending `Z` |
| JSON on disk | UTF-8, `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, one trailing newline, floats rounded to 6 decimals before writing |
| Engine | `ENGINE_VERSION = "1.15.0"` in `burro_core`. Any change to the arithmetic in section 6, to a rule of the reducer in section 5.3 or to a rule of what an explanation says in section 7.5 bumps it. 1.1.0 compares coverage in whole steps (section 6.6). 1.2.0 lets the defaults give way to a quarter, and keeps off what a person took off (sections 4.1 and 5.3). 1.3.0 gives as a trade-off only what an area does badly (section 7.5). 1.4.0 ranks by a vibe towards either end of a scale, scores journeys on the legs that have a time (section 6.4), gives a trade-off a threshold of its own, and says a figure from the side of its role (section 7.5). 1.5.0 ranks an area only where it has a figure for half of the character that counts, apart from the journeys and the budget (section 6.6), no longer reads the last thing of a turned list as a new wish for what is said after it (section 8.2), and never weighs a vibe that holds recorded crime on an edit that is only inferred (section 5.3, rule 8), never gives a short walk as a trade-off (section 7.5), and puts the areas most like one area in the order of the count each sentence gives (section 6.9). 1.6.0 says a vibe in short in an explanation (section 7.5). 1.7.0 shows on a result a vibe nobody asked for only where the area has more of it than most or sits towards an end of a scale, and never one whose recipe holds recorded crime (section 6.7), and no longer calls unread the words of a prompt that say what the search already holds (section 8.2). 1.8.0 is that engine joined with the engine of the first real builds, which was 1.3.0 with the preview and the rules of a release that is not made up (sections 2.1 and 2.8). It moves no arithmetic: one number names what both had become. 1.9.0 turns away, as `not_in_release`, a wish for what the release holds for no area: a vibe no area has a band for, a budget where it holds no cost of that kind of home, and a journey where it names no place (sections 4 and 5.3, rule 15). It moves no arithmetic either: a search that was ranked is ranked as it was. 1.10.0 is that engine joined with the one that holds a budget against the median of a cost that has no range (sections 2.5 and 6.5). It moves no result of a release whose costs all have a range. 1.11.0 lets what is said of the place lead: a journey weighs 0.40 and a budget 0.30 until a person moves them, where they weighed 1.00 and 0.80 (section 4.1). It moves no arithmetic, and a search that holds its own weights, as a share does, is ranked as it was. 1.12.0 puts an area with no figure for a thing that was asked for below every area that has one (section 6.6). Its fit is worked out as it was. 1.13.0 estimates a journey by public transport from distance, where a release holds no time for it and says where the homes of the area stand (section 6.10, ADR 0027). It moves no result of a release that holds its times. In the same version a firm budget leaves an area out on a median only where the median is more than a quarter over the budget, and it is said beside a median that is over a budget that about half of the homes sold for less (sections 6.1, 6.5 and 7.3). It moves no result of a release whose costs all have a range. 1.13.0 is one number for both. 1.14.0 holds a budget against the median of a rent that is of a wider place than the area, with the same margin on a firm budget, and says the place wherever the rent is said (sections 2.5, 6.5 and 7.3). It moves no result of a release whose rents are of the area alone. In the same version it calls an estimated journey likely within its limit only where the estimate is 10 minutes or more under it, where it was 5 (section 6.10, ADR 0027 as amended on 2026-09-25). What is likely beyond a limit is what it was, so a firm limit leaves out no more than it did. It moves no result of a release that holds its times. In the same version it says that a cost is at a budget, and a journey at its limit, where the difference is nothing, and gives no difference of nothing as a figure (sections 7.2 and 7.3). It moves no result, and no sentence of a cost that is not the budget to the pound. 1.14.0 is one number for the three: nothing past 1.13.0 had been served when they were joined. 1.15.0 says a flow of traffic whole and with its separator, as it says metres and pounds (section 7.2), and reads the plain ways a person asks for little traffic (section 8.2). It moves no arithmetic: a search is ranked as it was on what a release held before |
| Band | `int`, 1 to 5, or `None`. Where an area sits among the rankable areas that have a figure (section 2.4). It is what a sentence about a vibe says, and what likeness is counted on |
| Errors | Core raises `ReleaseError` and `SpecError`. The reducer never raises on a bad edit; it rejects the edit |
| What an error shows | Every record sets `hide_input_in_errors`, so a validation error says where and what kind, and never what was sent. A `ReleaseError` names the file, the row and the rule, and leaves out even the name of a field it does not know |
| Purity | Nothing in `burro_core` opens a file, reads the clock, the environment or a random source, or logs. A test checks its imports |
| Types below | Records are given as tables, functions and protocols as signatures. Every record is a model configured as in the first row |

## 1. Package layout

Dependencies point one way: `burro_pipeline → burro_core ← burro_api`. The pipeline and the API never import each other. They meet at the release folder, so the deployed API carries no build tooling.

**`packages/core`**: distribution `burro-core`, import `burro_core`. Depends on pydantic only.

| Module | Holds |
|---|---|
| `ids.py` | `FeatureId`, `TagId` and every other enum, and the id patterns. This is the allowlist of ADR 0006 |
| `catalogue.py` | `FEATURES`, `TAGS`, `FAMILIES`, `GRITTY`, `NUISANCES`, `NEVER_A_TRADE_OFF`, `CATALOGUE_VERSION`, `percentile_of()`, `band_of()`, `tag_raw()`, `tags_of()`, and `checked_recipe()`, which holds every recipe to its rules at import |
| `release.py` | The `Release` protocol, its records, `InMemoryRelease`, `parse_release()`, `open_release()`, `open_served()`, `open_built()` and the record `Hashes` |
| `spec.py` | `PreferenceSpec`, `LIMITS`, `default_spec()`, `check_spec()`, `canonical()`, `spec_hash()` |
| `ops.py` | `Operations` and its six edit types |
| `reducer.py` | `apply()` |
| `rank.py` | `rank()`, `RankResult`, `asked_for()`, the decay and budget functions and their constants |
| `places.py` | `normalise()`, `search_places()`, `resolve_place()`, `resolve_area()`, and `Names`, which holds a release's names normalised once and adds `exact_place()` and `exact_area()` |
| `likeness.py` | `similar()`, `Likeness`, and `may_be_compared()`, which says what likeness may never be counted on (section 6.9) |
| `portrait.py` | `portrait()`, `Portrait`: where an area sits on every vibe, with no spec (section 7.6) |
| `facts.py` | `Fact`, `facts_for()` |
| `explain.py` | The templates, the `Explainer` protocol, `TemplateExplainer`, `explain()` |
| `verify.py` | `verify()`, `ORDINARY_WORDS`, `BANNED_WORDS` |
| `interpret.py` | The `Interpreter` protocol, `RuleInterpreter`, `InterpretResult` with its `Suggestion`, `Choice` and `Span`, `assumptions_for()`, the fixed notices and `notice_text()`, and `sentences_of()`, which says of each sentence whether the grammar makes it |
| `grammar.py` | The grammar of a plain prompt: what each part of one is, and `NotPlain` for a prompt it does not make (section 8.2) |
| `reading.py` | Where a sentence ends, what a token is, and which tokens are a thing, a name, a number, or a word about who lives somewhere |
| `lexicon.py` | `LEXICON` and `lexicon_of(variant)`: every phrase that is a thing. `POLICY_LEXICON`. `NO_MEASURE` and `no_measure_of(variant)`: what Burro has no measure of |
| `vocabulary.py` | The words the grammar is made of: `PLAIN`, each group with where it stands and why it is safe there; the words that turn, take off and cap; and `WORDS_OF_DOUBT`, which the reader does not read and the model-backed reader is held to |
| `census.py` | The census figures of an area's page, which are no part of a release: `Census` and its records, `open_census()`, `parse_census()`, `panel()`, `offer()`, the fixed words `CENSUS_2021` and `MADE_UP`, and `CensusError` (section 2.10). No other module of core imports it, and it imports nothing of core but the shape of a record and the form of an id |
| `income.py` | Household income on an area's page, which is no part of a release either: `Income` and its records, `open_income()`, `parse_income()`, `shown()`, `offer()`, the fixed words `ONS` and `MADE_UP`, and `IncomeError` (section 2.11). It is fenced as the census is: no other module of core imports it |

**`packages/pipeline`**: adds one subpackage beside `registry/`, `release/`, with the synthetic generator inside it. Depends on `burro-core`. No new third-party dependency.

| Module | Holds |
|---|---|
| `release/write.py` | `write_release(release, folder, registry=None)`: the source check of 2.1, canonical JSON, checksums, manifest written last |
| `release/read.py` | `read_release(folder)`: reads the bytes, leaving out a `.DS_Store`, and calls `open_release` (section 2.8). `read_served(folder)` reads the folder beside the release too, and calls `open_served`. `read_built(folder)` reads the same, and calls `open_built` |
| `release/synthetic/build.py` | `build_synthetic(seed, release_id, built_at, gritty_variant) -> InMemoryRelease` |
| `release/synthetic/names.py` | The fixed lists of made-up names, and the plan of the made-up city |
| `release/synthetic/journeys.py` | How long a journey takes, and `whole_minutes()`, which holds the shortest at 2 minutes (section 2.9) |
| `release/synthetic/chart.py` | The map the areas are drawn on |
| `release/synthetic/count.py` | `made_up_census(release, seed)`: the made-up count of the made-up city (section 2.10) |
| `release/residents.py` | `write_census(census, release, folder, registry=None)` and `read_census(folder, release)`: the licence gate for `census_table`, canonical JSON, the manifest written last |
| `release/synthetic/estimate.py` | `made_up_income(release, seed)`: the made-up estimate of household income of the made-up city, drawn from noise alone (section 2.11) |
| `release/income.py` | `write_income(income, release, folder, registry=None)` and `read_income(folder, release)`: the licence gate for `display`, canonical JSON, the manifest written last |
| `derive/household_income.py` | Reads the statistics office's workbook for `display`, and hands on the figure of each area to be written beside a release. It is no measure, and is on no list of measures |
| `release/cli.py` | `burro-release build-synthetic --out FOLDER [--gritty a\|b] [--census-out FOLDER] [--income-out FOLDER]` and `burro-release check FOLDER [--census FOLDER] [--income FOLDER]` |

**`services/api`**: distribution `burro-api`, import `burro_api`. Depends on `burro-core`, `fastapi` (the web framework named in the plan), and `uvicorn` (runs it; the plain package, without the `standard` extra). It depends on no library of a provider of a model: each adapter in `providers/` makes one HTTPS call with the standard library (ADR 0019). Tests add `httpx2`, which FastAPI's test client needs.

| Module | Holds |
|---|---|
| `app.py` | `create_app(deps: Deps) -> FastAPI`. `Deps` holds the release, interpreter, explainer, share store, call log, clock, id source and allowed origins, so tests pass fakes |
| `settings.py` | `Settings.from_env()`: release folder, model id, timeouts, and the origins a browser may call from, each held to what a browser sends (section 9.1) |
| `loading.py` | `load_release(folder)`: reads the bytes of the release and of the folder beside it, leaving out a `.DS_Store`, and calls `open_served` (section 2.8) |
| `routes/` | One module per group of routes in section 9 |
| `wire.py`, `errors.py` | Request bodies, the response envelope, the error envelope, and handlers that never echo input |
| `stores.py` | The `ShareStore` protocol with an in-memory implementation |
| `calls.py`, `logs.py` | `CallRecord`, the `CallLog` protocol, logging setup, the request log line, `log_failure()` |
| `reader.py` | `ModelInterpreter` and the instructions: the rules read first, a model is asked of what they left unread, and what it says becomes offers (section 8.2). Tested against a fake `ModelClient` that answers wrongly, and against the answers a model gave, which are on disk |
| `answer.py`, `typed.py`, `guard.py`, `merge.py`, `offers.py`, `wording.py` | The shape a model answers in. Where words stand in the text, and core's lists as the checks read them. The checks. One offer for each thing. The ways code makes for a thing, and what "add all" may take. How an offer is worded |
| `providers/` | One adapter for each of four providers behind `ModelClient`, what people are told of each (`terms.py`), and `choose`, which decides once, as the service starts, who reads what is typed. [models.md](models.md) has the whole of it. No adapter has been run against its provider: there is no key to run one with |
| `deps.py`, `boundary.py`, `cli.py` | `Deps` and what is worked out from it once; the one middleware every request passes; `burro-api serve` and `burro-api openapi` |

**Changes outside the three packages** that the builders must make and report:

- Add `services/*` to the uv workspace members, the pyright `include` and the pytest `testpaths`. Add `burro-core` and `burro-api` to the `dev` group and to `[tool.uv.sources]` as workspace members.
- Add `--allow-unix-socket` to the pytest options. The socket block stops the test client's event loop from making the local socket pair it wakes itself with. Network sockets stay blocked.
- Add a nested `AGENTS.md` with a one-line `CLAUDE.md` to each new package, and update the table in the root `AGENTS.md`.
- Keep the built synthetic release at `data/fixtures/synthetic/syn-2026-09-23-01/` as a tracked, generated file that is never edited by hand. It is built with seed `20260923` and `built_at` `2026-09-23T00:00:00Z`, which are also the defaults of `burro-release build-synthetic`. API tests load that folder, so it is built before the API's tests can pass. Core tests build small releases in memory, and read the committed one for what must hold of the release that is served: that every comparison said of it is true, and that a wish moves its ranking. Core itself still opens no file. The test reads the bytes and hands them to `open_release`.

## 2. The data release

A release is one folder named for its id. Once written it never changes. A correction is a new release. The synthetic release is JSON throughout.

| File | Top-level shape | One row is | Fields |
|---|---|---|---|
| `manifest.json` | object | the release | 2.1 |
| `neighbourhoods.json` | `{"source_ids": [...], "as_of": ..., "neighbourhoods": [...]}` | a named area | 2.2 |
| `geometry.json` | GeoJSON `FeatureCollection` | an area's polygon | `id` and `properties.area_id` both hold the `area_id`; no other properties. `Polygon` or `MultiPolygon`, WGS84, 6 decimals |
| `catalogue.json` | `{"catalogue_version": 15, "metrics": [...], "vibes": [...]}` | a feature this release carries, and a vibe it carries | 2.3 |
| `features.json` | `{"rows": [...]}` | one feature in one area | `area_id`, `feature_id`, `value` (float or null, in the catalogue's unit), `percentile` (float or null), `coverage` (0 to 1) |
| `tags.json` | `{"rows": [...]}` | one vibe in one area | `area_id`, `tag_id`, `raw` (float or null, 0 to 1), `score` (float or null: the percentile of `raw`, for ranking only), `coverage` (0 to 1), `band`, `spread_low`, `spread_high` (int 1 to 5, or null) |
| `cost.json` | `{"rows": [...]}` | one tenure and segment in one area | 2.5 |
| `destinations.json` | `{"destinations": [...]}` | a point journeys end at | `destination_id`, `centroid`. In a real release it is a hexagon (ADR 0003) |
| `travel.json` | object of matrices | | 2.6 |
| `stations.json` | `{"source_ids": [...], "as_of": ..., "rows": [...]}` | one station near one area | `area_id`, `station_id`, `name`, `walk_minutes`, `lines` (line names, sorted), `step_free`, `nearest` |
| `places.json` | `{"places": [...]}` | something a person can name as a destination | 2.7 |

Every file that holds something the product may show names where it came from and when. `neighbourhoods.json`, `stations.json` and `travel.json` do it once for the file, with `source_ids` (a sorted list, at least one) and `as_of` (a date or a month), because each is built in one step from several sources. `catalogue.json` and `cost.json` do it on each row, and so does `places.json`, where a row is one record from one source. Without these a fact about a name, a station or a journey would have no source to cite (section 7.1).

**What a preview may leave unsaid.** A release that is not finished says so, with `preview` in its manifest (section 2.1). A preview may hold no journey and no station, and then `travel.json` or `stations.json` states no source: `source_ids` is empty and `as_of` is `null`. There is nothing in the file to cite, and to name a timetable that was never read would be to make a source up. It is allowed only where all three hold: the release says it is a preview, the file holds nothing (`destination_ids` is empty, or `rows` is), and the source and the date are both left out. Every other file states its sources as before, `neighbourhoods.json` included. No fact is ever made from a file that states none. [ADR 0017](../adr/0017-a-preview-says-it-is-one.md) says why.

**What a finished release holds.** A release that does not say it is a preview holds at least one journey's end, one place to reach, one cost and one station. One that holds none of some of these is a preview, and core refuses it if it says otherwise (`finished_release_is_whole`). It is the least a finished release must hold, and not the gates of a launch, which [ADR 0015](../adr/0015-where-builds-run-and-what-gates-a-launch.md) sets.

**What stands beside a release that is not made up.** A folder named for the release with `-build` after it, which holds what the release was built with. Three of its files are part of this contract: `evidence.json`, `lock.json`, and `hashes.json`, which holds the SHA-256 of the manifest, of the evidence and of the lock. A release that is not made up is served only while all three are there and are as they were written (section 2.8). The release folder itself holds the files of the release and nothing else, as before. [ADR 0018](../adr/0018-a-real-release-is-served-with-its-evidence.md) says why.

Missing data has one spelling per file, and nothing is ever filled in.

- `features.json` holds a row for every area and every feature in `catalogue.json`, and `tags.json` a row for every area and every vibe in `catalogue.json`. A missing value is `null`, because coverage is still reported.
- In `features.json`, `coverage` is the share of the area, by population or by land as the definition says, that the source covered. The pipeline sets `value` to null below 0.5. In `tags.json`, `coverage` is the share of the formula's weight that was present (section 3.2).
- `cost.json` and `stations.json` hold no row where there is no estimate. An area has at most one station row with `nearest` true; its other rows are stations within a 10-minute walk.

### 2.1 `manifest.json`

| Field | Type | Notes |
|---|---|---|
| `release_id` | str | Equals the folder name |
| `schema_version` | int | `2` |
| `built_at` | timestamp | An input to the builder, never read from the clock, so a rebuild is byte-identical |
| `catalogue_version` | int | Must equal `CATALOGUE_VERSION`, which is 15. It went from 2 to 3 when two lines of what a vibe cannot see were said in whole sentences: no recipe, id or name moved. It went to 4 when the vibes were joined with the first real builds, which had been built at 1, and nitrogen dioxide was said to be modelled. It went to 5 when each measure that a real build works out was named for what its file holds (section 3.1): no id and no recipe moved. It went to 6 when transport noise was named a share of residents, which is whose share its file gives: no id and no recipe moved. It went to 7 when three vibes were named for what a person would call them, Going out, Houses or flats and Age of buildings: no id, end or recipe moved. It went to 8 when Gritty became one vibe: the scale that counts recorded crime was named Gritty and given the recipe that was decided, and a release that carries it carries Works and warehouses beside it. It went to 9 when the places to eat and drink were named for what is counted, within 800 m of home in a straight line, and the places for each 1,000 homes became a feature of their own, which a wish is ranked on. It went to 10 when Going out was made of places to eat and drink for each 1,000 homes, high streets and culture, with the pubs held back until a second source confirms them. It went to 11 when what homes sell for became a measure a person may ask for, as the second reading of a word for a smart area. It went to 12 when each measure was named for what its figure is: a distance says it is a straight line, in metres, recorded incidents are counted for each 1,000 homes, the cultural venues are a count that is shown and a rate that a wish is ranked on, Food and drink is made of the places for each 1,000 homes, and a release that carries Gritty does not carry Works and warehouses. It went to 13 when cafes, gyms and pubs became measures, each a count that is shown and a figure for each 1,000 homes that a wish is ranked on: pubs and bars are counted from the file of places and are 35 in 100 of Going out again, and the homes near a cluster of pubs and bars are named for what is counted. In the same version the food shop was named as it is built, a straight line in metres to the nearest grocer, supermarket or convenience store, and Everyday on foot said that each of its distances is a straight line and that nothing is known of how large a food shop is or of what it sells, and said, first of what it cannot see, that it is mostly a map of how built up a place is: on a build of London its order is mostly that of homes to the hectare, and no id and no recipe moved for it. In the same version the chains of grocers, gyms and coffee became measures (section 3.1.1, ADR 0026), and independent places were named for what is measured: a share of the places to eat and drink within 800 m of home, in a straight line. With them Village feel holds 60 in 100 of its recipe, and it places an area only where something of its town centre has a figure (section 3.2). In the same version Well connected joined, with the four measures it is made of and the stops of buses, which are shown. In the same version four measures of who lived somewhere at the census of 2021 were given ids, residents of two ages and households of two kinds, and two vibes that hold one each were added, Family area and Young professionals: Family amenities now says that it counts places alone. In the same version three figures of the homes of a place joined: the share of homes in the higher council tax bands, and how far what homes sold for has risen over five years and over ten. None stands in a vibe or in likeness. In the same version private outdoor space was named for what its file counts, a share of addresses: no id and no recipe moved. Version 13 is one number for what several streams of work each added on 2026-09-24. It went to 14 when how much of the high street nearest a home lies in a conservation area became a measure, `highstreet_conserved`, which a build of London works out: no likeness is counted on it. With it Village feel came to be made of that measure, and a vibe came to say whether it is as sure as the rest or a rough guide (`sureness`, section 3.2). It went to 15 when the traffic near where homes stand became a measure, `road_traffic_nearby`, which a person may rank on: Quiet streets holds it at 20 in 100, which it took from main roads, and no other recipe moved |
| `synthetic` | bool | True for every `syn-` release and for no other |
| `preview` | bool | True for a release that is not finished: it is for the people who build Burro, and is never launched. The builder sets it. It reaches every API response (section 9.1), as `synthetic` does. The two are apart: the first real build is a preview and is not synthetic, and the synthetic release is whole and is no preview |
| `gritty_variant` | `a` or `b` | Whether the release carries Gritty, the one vibe that counts recorded crime (section 3.2). `b` carries it, and not Works and warehouses, which is a part of it. `a` holds no recorded crime, and carries Works and warehouses in the place of Gritty |
| `city`, `seed` | str, int or null | `syn` or `lon`. The seed is set for synthetic releases |
| `sources` | list | `source_id`, `name`, `publisher`, `licence`, `attribution`, `url`, `retrieved_on`, `credit_beside_figures`, and `said_with_attribution` where there is something to say. Every `source_id` used anywhere in the release appears here once. `credit_beside_figures` is true where the publisher asks that its `attribution` stands wherever a figure made from its data is shown, and not on the page of attributions alone: the licence registry says which, and every fact that cites the source then carries the statement (section 7.1). It is false where a release does not say. `said_with_attribution` is what the terms of the publisher ask to be said wherever its credit is shown, in plain words, as the licence registry holds it: it is no part of `attribution`, which stays as the publisher worded it, and a client draws it under the credit wherever it draws the credit. **A source of which nothing is asked does not hold the field**, so a release that rests on no such source is byte for byte what it was. Route 11 serves it with each source, and `null` where a source does not hold it |
| `files` | list | `name`, `sha256`, `bytes` for every other file in the folder |
| `counts` | object | `neighbourhoods`, `rankable`, `destinations`, `places`, `stations` |
| `changes_sha256` | 64 hex digits, or not there | The hash of the file of changes the release was built with: what a person decided at the panel of the review desk (ADR 0029). **A release that was built with none does not hold the field**, and is byte for byte what it was before the field was there. A release that carries a recipe, a name or a label that is not core's must hold it (`changes_are_named`), and the lock of its build must name that very file (`changes_are_locked`, section 2.8) |

The manifest does not name an engine. A release is data and the engine is arithmetic; `rank()` takes both and records both, and a release, which can never be changed, must not have to be rebuilt because the arithmetic moved.

`write_release` checks every source before it writes anything. The use a source must be registered for depends on the file that names it, because the registry approves a source for a use, not in general:

| File naming the source | `Registry.require(id, use)` with |
|---|---|
| `catalogue.json`, `cost.json` | `Use.SCORING` |
| `travel.json` | `Use.ROUTING` |
| `stations.json` | `Use.DISPLAY` |
| `places.json` | `Use.DESTINATION_SEARCH` |
| `neighbourhoods.json` | `Use.GAZETTEER` |

A release that is not synthetic is refused when no registry is passed. The id `synthetic` is reserved: it is allowed only when `synthetic` is true, and then it is the only source allowed and the registry is not consulted. Its attribution is fixed: "Synthetic data generated by Burro for testing. It describes no real place."

### 2.2 `neighbourhoods.json`

| Field | Type | Notes |
|---|---|---|
| `area_id` | str | Immutable |
| `slug` | str | `^[a-z0-9]+(-[a-z0-9]+)*$`, unique. May change between releases; the id may not |
| `name`, `borough` | str | What the user sees |
| `aliases` | list of str | Other names that resolve to this area. May be empty. An area that says a side after its name, as "Foxholt, north", holds the name alone here, so that a search for the name finds every area that bears it |
| `centroid` | `[lon, lat]` | WGS84, 6 decimals |
| `rankable` | bool | The pipeline decides; core only reads. A real release sets it false for an area too small for its rates to be steady, below 3,000 residents |
| `neighbours` | list of `area_id` | Areas sharing a boundary, sorted. Symmetric |
| `named` | `Named` or null | What is known of the name, where the area bears a name that is not its publisher's label. `null` where it bears no other, and in a release written before the field |

**The name an area bears.** An area of a real release is drawn as the statistics office draws a census area, which it labels with a borough and a number. `named` says what is known of any other name the area bears.

| Field of `Named` | Type | Notes |
|---|---|---|
| `label` | str | The label of the area as its publisher gives it. A client shows it beside the name, smaller |
| `source_ids` | list of str | Every source whose own record writes the name, letter for letter. Sorted, at least one, each among the `source_ids` of the file |
| `state` | `draft` or `checked` | `NameState`. `draft`: a method chose the name, and no person has read it. `checked`: a person decided it at the review desk |

| Rule | Detail |
|---|---|
| Which name | An area bears the name of the drafted neighbourhood that holds more of its output areas than any other. The draft of London's named areas gives every output area to one neighbourhood: the one whose seed is nearest to it along the roads ([the areas design](london-data-areas.md)) |
| Counted in | Output areas, and not homes: the licence registry gives no count of homes for naming a place. Of two neighbourhoods that hold as many, the one whose id sorts first gives the name |
| A name | One that a record of a publisher writes letter for letter. None is coined, respelt or supplied from memory |
| No name | An area none of whose output areas lies in a neighbourhood that gives a name keeps its publisher's label as its `name`, and `named` is `null` |
| Two areas of one name | Each says its borough, as every area does. Where two areas of one borough bear one name, each adds the side of them it lies on, after a comma: the nearest of north, east, south and west to the line from the middle of those areas to its own middle, and the nearest of eight points where two would say the same. Two that lie the same way say the same, and the label tells them apart |
| A draft | A name is a draft until a person has decided it at the review desk. The name a person decided takes the place of the draft, as that person spelt it, and says `checked` |
| The id and the slug | Made from the label, whatever the area bears. Neither moves when a name is decided |
| The date | `as_of` of the file is the month of the newest of the lookup and the files that write a name. With no name it is the lookup's, as before |

A build is given the draft as a folder, and bears names only where it is given one. [ADR 0025](../adr/0025-an-area-bears-a-drafted-name-and-says-so.md) says why a draft is served, and what would change it.
| `homes_at` | `[lon, lat]` or null | Where the homes of the area are taken to stand: the middle of the centres of population of its small census areas. A journey is estimated from it where the release holds no journey time (section 6.10). `null` where a release does not say, and nothing is then estimated: the point inside the area never stands in. It lies within half a degree of `centroid`, as a neighbour does |

The release holds no population figure. The pipeline needs one for rates and for `rankable`, and nothing after the pipeline does, so it stays there: a count of residents that is not in the release cannot be ranked on or shown.

### 2.3 `catalogue.json`

| Field | Type | Notes |
|---|---|---|
| `feature_id` | `FeatureId` | Must be in the allowlist |
| `dimension`, `unit`, `polarity`, `kind`, `describes`, `family`, `method`, `in_likeness` | | Must equal `FEATURES` in core. Core decides these; the release repeats them so it can be read alone |
| `label`, `short_label` | str | Core's, unless a person gave the measure another at the panel of the review desk (ADR 0029). A label a person gave is one line of plain words, of 200 characters at most, and a short label of 40 at most with no figure. Neither holds a word that no sentence may say (section 7.4) or a word for a group of people (section 8.4). A measure that counts who lived somewhere is named by core and by no release. `what_a_measure_breaks()` in core holds the rule |
| `native_resolution` | enum | `oa`, `lsoa`, `msoa`, `grid_1km`, `point`, `polygon`, `network` |
| `source_ids` | list of str | Every source the figure was worked out from, sorted, at least one, each in `manifest.sources`. A crime rate names the crime data and the population estimate it was divided by |
| `vintage` | str | The period the data describes, for example `2025` or `2024-10 to 2026-09` |
| `rankable` | bool | False switches the feature off for ranking in this release. Its values are still shown. It is false of every feature core says is shown and never ranked on (`RANKED_AS`, section 3.1), and a release that says otherwise is refused |
| `definition` | str | One sentence with the method and its parameters, shown on the methods page |

A release carries the features it has a cleared source for, which may be fewer than `FeatureId` holds. A feature with no row here is not in the release: it has no rows in `features.json`, it counts as missing in every vibe, and an edit or a spec that weights it meets `not_in_release`, as one that weights a feature with `rankable` false does. Every feature in core can be ranked; only a release switches one off. A real build switches off `road_major_exposure`, which no audit has looked at, and none is to since 2026-09-25 (ADR 0006, as amended): its figure is shown, a wish for it alone meets `not_in_release`, and a vibe whose recipe holds it still rests on it. The synthetic release carries 110 of the 114, each rankable but the six that core shows and never ranks on and the 18 measures of the tiers, which a release shows beside the mix (section 3.1.1). It lacks four: `cuisine_variety`, which waits for a source, and `private_outdoor_space`, `gp_walk` and `pharmacy_walk`, which a build of London carries and the made-up release does not yet. So three recipes run short in it, and their coverage says so.

`vibes` holds the vibes the release carries, each its `Tag` in core (section 3.2) but for what a person may adjust: the eleven and Gritty where `gritty_variant` is `b`, and the eleven and Works and warehouses where it is `a`. A vibe with no row here is not in the release. It has no rows in `tags.json`, and an edit or a spec that names it meets `not_in_release`. So does one that names a vibe the release carries and places no area on: a first build holds under 60 in 100 of most recipes, so no area has a band for them, and a wish for one would leave no area to rank. `Release.placed(tag_id)` says whether any area has a score for a vibe, and `recipes_held(release)` says, for each vibe, how many hundredths of its recipe the release carries a measure for (`held`), how many an area needs (`needed`, 60), whether any area is placed (`placed`), and the parts it waits on, each by the label core gives the measure (`waits_on`).

A release that is not made up carries the same twelve, Gritty among them, whatever it has measured. A vibe rests on the parts of its recipe that the release carries. Where they are 60 in 100 of the recipe or more the area has a band, and the fact of the vibe says how many parts and what share (section 7.3). Village feel has no band without its high street, which is 45 in 100 of it (section 3.2). Where they are fewer it has none, and the fact says that the area cannot be placed. A first build of four measures carries 75 in 100 of one recipe, Houses or flats, and under 60 of every other: so it places every area on Houses or flats and on nothing else. A build of ten measures, main roads, traffic and transport noise among them, carries 70 in 100 of two more, Parks close by and Quiet streets, and places every area on those three. Without its traffic such a build holds 50 in 100 of Quiet streets, and places no area on it. Nothing is taken out by hand, and nothing is put in.

### 2.4 How a percentile is computed

For one feature, the population is the rankable areas with a value, `N` of them. For an area with value `v`, `L` is how many of the population are strictly below `v` and `E` how many equal it, the area itself included if it is rankable.

`percentile = round(100 * (L + 0.5 * E) / N, 1)`

It is a percentile of the raw value. Polarity is applied at ranking time, never baked in. `percentile` is null exactly when `value` is null. If no rankable area has a value, the pipeline leaves the feature out of the release. Example: values 310, 120, 640, 310, 900 give 40.0, 10.0, 70.0, 40.0, 90.0.

`percentile_of(values, rankable) -> tuple[float | None, ...]` in core is the only implementation, for features and for vibes alike. It takes one value and one rankable flag for each area, in the same order. The pipeline calls it, as it calls `tag_raw()`.

**A band** is where an area sits among the same population, in fifths, and it is counted in whole areas so that no float decides it. With `L` and `N` as above, `band = 1 + min(4, (5 * L) // N)`. It is null exactly when the value is. Areas that are level share a band. Example: the five values above give bands 2, 1, 4, 2 and 5. `band_of(values, rankable) -> tuple[int | None, ...]` in core is the only implementation. A vibe's `band` is the band of its `raw`. Its `spread_low` and `spread_high` are the lowest and the highest band among the parts of the area that the pipeline measured, and they hold the band. Where they are three bands apart or more, the area is mixed, and is said to be (section 7.3). The mid-rank percentile is for scoring. A band is what is said and drawn, and what likeness is counted on.

### 2.5 `cost.json`

| Field | Type | Notes |
|---|---|---|
| `area_id`, `tenure` | str, `rent` or `buy` | |
| `segment` | enum | Rent: `room`, `studio`, `bed_1`, `bed_2`, `bed_3`, `bed_4plus`. Buy: `flat`, `terraced`, `semi_detached`, `detached` |
| `median` | int | Pounds |
| `lower_quartile`, `upper_quartile` | int or null | Pounds. Both, or neither. Where both: `lower <= median <= upper` |
| `confidence` | `high`, `medium`, `low`, `unstated` | Of a range. High: at least 50 observations. Medium: 10 to 49, blended. Low: modelled. Of a median that says how many sales it rests on: `high` from 50 sales and `medium` from 10 to 49, and nothing is blended. Of a publisher's median that gives no count: `unstated` |
| `as_of`, `source_ids` | month, list of str | As in 2.3. Of one number, `as_of` is the last month the sales were made in |
| `sales` | int or null | How many sales a median rests on, where a source says. No fewer than `FEWEST_SALES`, which is 10. `null` of a range, and of a publisher's median that gives no count |
| `since` | month or null | The first month the sales were made in, or the rents were recorded in. It is given exactly where `sales` is, or `rents` |
| `rents` | int or null | How many rents a rent of a wider place rests on, as its publisher gives it, which is to the nearest 10. No fewer than 10. `null` of any other row |
| `of` | `CostOf` or null | The place the row is of, where that is wider than the area: `kind`, which is `postcode_district` or `borough`, and `name`. `null` of a row that is of the area alone. It is given exactly where `rents` is |

**A cost is a range, or one number where no range is known.** A row is one of four things, and says which by what it holds.

| A row is | It holds | `confidence` | What it is |
|---|---|---|---|
| A range | Both quartiles and the median | `high`, `medium` or `low` | An estimate that Burro works out from sales or from rents. Rent is rounded to 25 and price to 5,000 |
| One number, from a publisher | The median, and `null` for both quartiles, for `sales` and for `since` | `unstated` | A publisher's own median of what was paid for the homes of one kind that were sold in the twelve months that end with `as_of`. It is carried as the publisher wrote it, to the pound, and is not rounded |
| One number, from the sales | The median, `sales` and `since`, and `null` for both quartiles | `high` from 50 sales, `medium` from 10 to 49 | The median of what was paid in the sales of homes of one kind, from `since` to `as_of`, worked out from the sales themselves. Where the sales are even in number it is the mean of the two in the middle, to the pound with a half taken upward. Where fewer than 10 were made there is no row |
| A rent of a wider place | Both quartiles and the median, `rents`, `since` and `of`, and `null` for `sales` | `high` from 50 rents, `medium` from 10 to 49 | The rents that were recorded for homes of one kind, from `since` to `as_of`, in the postcode district the area lies in or in its borough, as their publisher gives them. It is carried as the publisher wrote it, to the pound, and is not rounded. It is never the area's own, and `of` says which place it is of |

One number is never made into a range, and nothing is put in the place of a quartile that no source gives. A publisher's median says nothing of what it rests on. It is `unstated` because the publisher gives a figure with no count of the sales behind it, so nothing says how steady it is. A median of sales that were counted says how many, and what it rests on is what the count makes it: `confidence_of(sales)` in core is the one rule, and core refuses a row that says otherwise. Either is a price of every size of home of its kind: no source gives a price by bedrooms, and none is worked out. A rent is never one number: no source gives one for an area, and core refuses a rent with no range (`values_are_in_range`).

A build of London reads every sale that HM Land Registry records, of the years it was given, and works the median out for each area and each kind of home. So a flat is priced apart from a house, and a budget for a flat is held against flats. A sale is put in an area by its postcode, which is kept nowhere after that. No row of a sale, no postcode and no line of an address is in a release: what is in it is a median of 10 sales or more, and how many they were. Where a build holds no file of sales it carries the publisher's own median, as it did.

**A rent of London is of a wider place than the area, and says so.** Decided on 2026-09-25 ([ADR 0021](../adr/0021-a-price-is-shown-as-the-publisher-gives-it.md), as amended). Rents are published for boroughs and for postcode districts and not for areas, and no design holds the model that would bring one to an area. So a build of London gives an area the figures of the place it lies in, and the row says the place.

| | The rule |
|---|---|
| Which place | The postcode district where half or more of the area's homes stand, and the area's borough otherwise. Where the district has no row that may be carried, the borough's. Where neither has one the area has no row, and nothing is filled in from a neighbour |
| Which rows | Only a row of the publisher's that holds the median and both quartiles. The publisher gives none of them on fewer than 10 rents |
| One place, one row | Every area of one place holds the same figures for a kind of home. Core refuses a release where two rows of one place differ, and one that says an area is of a borough it is not in |
| What is said | Wherever the rent is shown or a budget is held against it: the place, that the figure is not of the area alone, the months, and how many rents were recorded (section 7.3). What the publisher advises of the figures is said once where a person reads them: `RENT_CAUTION` in core is the one place it is written |

A release that read no rents holds none. A renter's budget is then turned away as `not_in_release` (section 5.3, rule 15), and no area is given a rent that was not published for a place it lies in. ADR 0021 says why a price is shown, and why as one number.

### 2.6 `travel.json`

It holds `source_ids`, `as_of`, `area_ids`, `destination_ids`, `cutoff_minutes` (`{"pt": 90, "cycle": 60, "walk": 60}`) and four matrices: `pt_typical`, `pt_just_missed`, `cycle` and `walk`. `area_ids` holds every area and `destination_ids` every destination, each once and sorted. Each matrix is a list of rows in `area_ids` order, each row a list in `destination_ids` order. Times are door to door, on a weekday morning peak. A journey has several sources because a real one is built from timetables and a street network, and each must be credited beside the time (ADR 0004).

A preview that has routed no journey holds no time: `destination_ids` is empty, every row of every matrix is empty, and the file states no source (section 2). It may still name places to reach, and the ends of the journeys to them: a build of London names its stations. `Release.travel()` then answers `missing` for any journey asked of it, and a journey by public transport is estimated from distance for a search (section 6.10). A release that is finished holds a time, or a cell that says there is none, for every end it names. `cutoff_minutes` must still be given, because the limits of a form are read from it (section 4). It then limits nothing, and what it holds is the builder's to say: it is not yet a thing a release can leave out (section 13).

| Cell | Meaning | `Travel.status` | `Travel.minutes` |
|---|---|---|---|
| int, 0 up to the cutoff | Minutes | `ok` | The int |
| `-1` | No journey within the cutoff. This is data | `beyond_cutoff` | `None` |
| `null` | Not computed. This is missing data | `missing` | `None` |

A fourth status, `estimated`, is of a journey of a search and of no file: no release holds it, and `Travel` refuses it.

Where both are minutes, `pt_just_missed >= pt_typical`. The two spellings exist only in the file; `parse_release` turns them into `Travel(status, minutes)`.

A time of 0 is valid, and core reads one as it stands. Whether a release holds one is the pipeline's to decide: the synthetic release holds no time under 2 minutes (section 2.9), and a real roll-up needs the same floor if it can give less.

### 2.7 `places.json`

| Field | Type | Notes |
|---|---|---|
| `place_id`, `name` | str | The canonical name, shown to the user |
| `aliases` | list of str | |
| `kind` | enum | `station`, `district`, `postcode_district`, `university`, `hospital`, `school`, `landmark` |
| `destination_id` | str | Where journeys to this place end |
| `coarse_place_id` | str | A `station` or `district` place standing in for this one in a shared link. A coarse place names itself |
| `centroid`, `source_id` | `[lon, lat]`, str | |

### 2.8 The `Release` protocol and loading

```python
class Release(Protocol):
    @property
    def manifest(self) -> Manifest: ...
    @property
    def neighbourhoods(self) -> tuple[Neighbourhood, ...]: ...
    @property
    def metrics(self) -> tuple[Metric, ...]: ...
    @property
    def vibes(self) -> tuple[Tag, ...]: ...
    @property
    def places(self) -> tuple[Place, ...]: ...
    def neighbourhood(self, area_id: str) -> Neighbourhood | None: ...
    def geometry(self, area_id: str) -> Geometry | None: ...
    def feature(self, area_id: str, feature_id: FeatureId) -> FeatureValue | None: ...
    def tag(self, area_id: str, tag_id: TagId) -> TagValue | None: ...
    def cost(self, area_id: str, tenure: Tenure, segment: Segment) -> CostEstimate | None: ...
    def place(self, place_id: str) -> Place | None: ...
    def travel(self, area_id: str, destination_id: str, mode: Mode, basis: PtBasis) -> Travel: ...
    def stations(self, area_id: str) -> tuple[StationAccess, ...]: ...
    def origin(self, part: Part) -> Origin: ...
    def cutoff(self, mode: Mode) -> int: ...
```

The three tuples of ids are ordered by id, and `stations` nearest first. `metrics` holds the features this release carries, and `vibes` the vibes, in the order of the shelf and then by id. `None` means the id is unknown to this release, or for `cost` that there is no estimate. `travel` never returns `None`; for a time that is not in the release, and for an id it does not know, it returns `Travel(status=missing, minutes=None)`. `basis` is ignored for `cycle` and `walk`. `Geometry` is a GeoJSON geometry object. `origin` returns the `source_ids` and `as_of` of one of the three files that state them once: `Part` is `neighbourhoods`, `stations` or `travel`. Every record is a frozen model with the fields of the matching file. `cutoff` returns the longest journey the release routed for a mode, which the reducer, `check_spec` and the travel fact all need. `InMemoryRelease` is the one implementation in this build. Its `documents()` is the inverse of `parse_release`, so the shape of every file is stated in one module, and `write_release` serialises what it returns. A release in another format is a second implementation; nothing else changes.

Two pure functions in core do all the checking, so the pipeline and the API cannot come to disagree about what a valid release is:

- `parse_release(documents: Mapping[str, object]) -> InMemoryRelease` takes the parsed content of each file, keyed by file name, and applies the rules in the table below. It is the only parser.
- `open_release(folder_name: str, files: Mapping[str, bytes]) -> InMemoryRelease` takes the bytes of each file in the folder, keyed by file name, and runs the four steps below. It reads no file itself.

1. Parse `manifest.json`. Refuse if `release_id` is not `folder_name`.
2. For each entry in `files`, compare `sha256` and `bytes`, then parse the JSON. Refuse an extra or a missing file.
3. Call `parse_release`.
4. Refuse on any `ReleaseError`. The message names the file, the row and the rule, and never a value.

A third function holds a release to what it was built with:

- `open_served(folder_name: str, files: Mapping[str, bytes], beside: Mapping[str, bytes] | None) -> InMemoryRelease` is `open_release`, and then, for a release that is not made up, three more steps. `beside` is the bytes of `hashes.json`, `evidence.json` and `lock.json` from the folder beside the release, by file name. It reads none of the evidence.

5. Refuse if any of the three files is not in `beside`.
6. Parse `hashes.json` as the record `Hashes`: `release_id`, `manifest_sha256`, `evidence_sha256`, `lock_sha256`. Refuse if its `release_id` is not the release's.
7. Refuse if the SHA-256 of `manifest.json`, of `evidence.json` or of `lock.json` is not the one the record holds.

A fourth reads a release that is never served, to hold one build against another:

- `open_built(folder_name: str, files: Mapping[str, bytes], beside: Mapping[str, bytes] | None) -> InMemoryRelease` is `open_served`, but for the seven rules that hold a release to the catalogue as core holds it today: `versions_match`, `catalogue_matches_core`, `vibes_match_core`, `names_name_no_place`, `held_off_stays_held_off`, `changes_are_named` and `raw_matches_recipe`. `OF_CORES_CATALOGUE` names them. A release that was built under another version of the catalogue breaks them by being what it was built as: it holds another recipe, or a vibe that was held off then. In their place one thing is asked of its versions, under the name `versions_are_its_own`: that `schema_version` is 2, and that the manifest and the catalogue say one `catalogue_version`. Everything else is held as it is of what is served: every file to the manifest, the release to itself, and the release to its build. It is read with the records this code has, so a release that holds a field or an id they do not know is refused as any release of that shape is. `read_built(folder)` in the pipeline calls it, for the step `moved` and for the panel of the review desk. Nothing that serves a release or checks one does.

`read_release(folder)` in the pipeline reads every file in the folder into bytes and calls `open_release`. `read_served(folder)` in the pipeline and `load_release(folder)` in the API read the folder beside the release too, and call `open_served`. So the service and `burro-release check` refuse the same releases. `burro-release check` then reads the evidence, which the service cannot: it fails if any fact the release would show has no row of evidence behind it, or a row that holds another figure.

`read_release` and `load_release` each leave one file out: a file named exactly `.DS_Store`, which a Mac leaves in any folder that has been opened in a window. It is never opened, it is not handed to `open_release`, and it is left where it is. Nothing else is left out: a folder of that name, the same name in another case, `._manifest.json`, `Thumbs.db` and `.gitkeep` are all handed over and refused as before. `write_release` leaves the same file alone when it rebuilds the synthetic release, so a folder that reads as a release can be rebuilt. Core is unchanged: `open_release` still refuses any file the manifest does not list, this one included, if it is handed one. The name is spelt out once in each reader, because the pipeline and the API never import each other, and a test in each holds it to `.DS_Store`.

| Rule in `parse_release` | Refused when |
|---|---|
| `versions_match` | `schema_version` is not 2, or `catalogue_version` is not `CATALOGUE_VERSION` |
| `synthetic_is_consistent` | `synthetic` is true and any id lacks the `syn-` prefix, or false and any id has it, or the reserved source of 2.1 is misused |
| `ids_are_unique` | An id or a slug repeats within its file |
| `references_resolve` | A row names an area, destination, place, station or source that does not exist. A name is written by a source that `neighbourhoods.json` does not state |
| `catalogue_matches_core` | A feature is outside the allowlist, or disagrees with `FEATURES` in anything but its label and its short label, or is labelled in words that are not plain, or is said to be ranked on where core says it is shown and never ranked on |
| `vibes_match_core` | `vibes` is not the vibes of `tags_of(gritty_variant)`: a vibe is missing or extra. Or a vibe disagrees with `TAGS` in anything but what a person may adjust (section 3.2), or what was adjusted breaks a rule of a recipe or of a name |
| `rows_are_complete` | `features.json` lacks a row for an area and a carried feature, `tags.json` for an area and a carried vibe, `geometry.json` lacks an area, or `travel.json` lacks an area or a destination. A preview whose `travel.json` names no destination at all is whole: it has routed no journey |
| `values_are_in_range` | A percentile, coverage, quartile order, cutoff or minute value breaks its range. A cost holds one quartile and not the other, or holds none and is a rent, or holds both and says `unstated` or holds a count of sales. A cost says the place it is of and is no rent, or gives no count of rents, no first month or no range, or gives a count under 10 or a count of sales, or says another confidence than its count of rents makes it, or names a postcode district that is not written as one, or a borough the area is not in. Two rows of one place, tenure and kind of home differ in a figure. A cost with no range gives a count of sales and not the month they begin, or the other way about, or a count under 10, or says another confidence than its count makes it, which is `unstated` where it gives none. A figure of a measure whose unit is `%` is below 0 or above 100, or a figure of any other unit is below 0. A point of an area's outline, or the point inside a neighbour, lies more than half a degree from the point inside the area |
| `null_means_null` | `value` and `percentile`, or `raw` and `score`, disagree about being null |
| `bands_match_raw` | A `band` is not what `band_of` gives for the `raw` values of the file, is null where `raw` is not, or lies outside `spread_low` to `spread_high` |
| `sources_are_stated` | A `source_ids` list is empty, or an `as_of` or a `vintage` is empty. The one exception is `travel.json` or `stations.json` of a preview that holds nothing, which states neither (section 2). A source with no date, or a date with no source, is refused whatever the file holds |
| `neighbours_are_symmetric` | A lists B and B does not list A |
| `finished_release_is_whole` | `preview` is false and the release holds no destination, no place, no cost or no station |
| `percentiles_match_values` | A feature's `percentile` is not what `percentile_of` gives for the `value`s of the file |
| `raw_matches_recipe` | A vibe's `raw` or `coverage` is not what `tag_raw` gives for the area's own percentiles in `features.json`, by the recipe the release carries |
| `names_name_no_place` | A name, a label or a line of what a vibe cannot see that is not core's own holds the name of an area, of a borough or of a place of the release, as a whole name and in whatever case. An area that is named with a part of the compass after a comma is found by what stands before the comma. A name of one word that core's own labels say is a word and no name. Core holds no list of the places of the world: a name is held to the places the release holds |
| `held_off_stays_held_off` | The recipe a release carries places an area on a vibe, and core's own recipe places none, by the release's own figures. A vibe is held off where too little of its recipe has a figure, or where the part it is placed only with has none (section 3.2). To move its shares to the parts that are there would place it on what is left of it. A vibe that core places may have its shares moved, and an area may then gain a band or lose one |
| `changes_are_named` | A release carries a recipe, a name, a label or a line that is not core's, and its manifest holds no `changes_sha256` |
| `scores_match_raw` | A vibe's `score` is not what `percentile_of` gives for the `raw` values of the file |

**What is ranked on never parts from what is shown.** `rank()` reads a feature's `percentile` and a vibe's `score`. A page shows the `value`, the band of the `raw` value, and the parts of the recipe. Four rules hold each to the next: the percentile to the value, the raw value to the recipe and the release's own percentiles, the score to the raw value, and the band to the raw value. Until 1.5.0 only the band was held, so a release whose score stood apart from its raw value, or whose areas stood in each other's place, was accepted. A figure a release holds is the figure core works out where the two differ by less than a millionth, the precision a release is written with. The band is checked with the rows of `tags.json`. The other three are checked last, after every rule that says whether a row is in order at all.

A few checks the table does not spell out are filed under the nearest rule: a list the contract calls sorted must be strictly increasing, and one station id has one name and one set of lines (`ids_are_unique`); a value may not be present below the coverage threshold (`null_means_null`); a tag with a score needs at least one formula feature with a value, or its fact would have no source (`sources_are_stated`). `counts` in the manifest is written from the rows and is not checked against them on reading.

A refusal that is not one of the seventeen rules has a name of its own, raised as the same `ReleaseError`:

| Name | Raised by | Refused when |
|---|---|---|
| `json_is_valid`, `shape_is_valid` | core | A file is not JSON, or a field is missing, unknown or of the wrong type |
| `files_match_manifest`, `files_are_expected` | core | A file is missing, extra or changed, a hidden file included, or is not a file a release has. `read_release` and `load_release` never hand core a `.DS_Store` |
| `release_id_matches_folder` | core | The manifest names a release other than its folder |
| `versions_are_its_own` | core, in `open_built` | `schema_version` is not 2, or the manifest and the catalogue of the release say two versions of the catalogue |
| `real_release_has_its_build` | core, in `open_served` | A release that is not made up has no `hashes.json`, no `evidence.json` or no `lock.json` beside it |
| `build_is_of_this_release` | core, in `open_served` | `hashes.json` names another release |
| `build_is_as_it_was_written` | core, in `open_served` | The manifest, the evidence or the lock does not have the hash `hashes.json` holds for it |
| `changes_are_locked` | core, in `open_served` | The manifest holds `changes_sha256`, and the lock is not there, cannot be read, or does not name one input `changes/...` with that hash and no other. Or the manifest holds none, and the lock names a file of changes. It holds for a made-up release too: one that says it was built with a file of changes is served only beside its lock. **None of the manifest, the hashes and the lock is signed.** Whoever can write all three has made a build of their own, and core cannot tell it from another. What can is the record of the builds that were approved, which is committed (ADR 0015), and which nothing reads when a release is served |
| `folder_is_readable`, `file_is_readable` | `read_release`, `load_release` | The folder or a file in it cannot be read |
| `real_release_needs_a_registry`, `release_is_never_overwritten`, `folder_holds_something_else` | `write_release` | A real release is written with no registry or over itself, or the folder holds something that is not a release file |

`burro-release check FOLDER` says a refusal in plain words. The API says the folder, the file and the rule, because it never imports the pipeline.

### 2.9 The synthetic release

| Rule | Detail |
|---|---|
| Size | 1 borough, 24 areas of which 2 are not rankable, 40 destinations, 16 stations, 4 lines, 44 places. Small enough that each area's character is set by hand, so a test can say which areas a spec should find |
| Names | Every area, borough, station, line and place name comes from a fixed list of made-up names. A test holds the names of the 32 London boroughs, the City, London's tube and rail lines, and 60 well-known London places, and fails if any made-up name contains one. That list guards against London's well-known names and against nothing else. It also holds the real names that the city once used and the list did not catch. Three a reviewer knew from memory: Dunmere, a hamlet in Cornwall; Copper Row, a small street by a bridge in London; and Skerrow, a loch in Galloway. They were replaced by Dulcimer Green, Coracle Row and Scrimshaw Airfield. Then all 102 names of the generator and of the releases the tests build by hand were looked up in one encyclopaedia, by title and by phrase. Two more of the city's names were found: Kilnside, a locality in Renfrewshire, and Withyford, an old spelling of a hamlet in Shropshire. They were replaced by Kindlewharf and Wickerford. Three aliases were what real buildings are called, The Exchange, The Playhouse and Moot Hall, and each has the borough before it now: Quillhaven Exchange, Quillhaven Playhouse, Quillhaven Moot Hall. Every new name sorts where the old one did, so no id moved, and a test holds each id to what it named before. The old names are held in the test's list, with the nine that the tests' own releases held, and a second test looks for each in every file of code and of tests, a constant's name included. **No gazetteer was consulted.** The encyclopaedia does not cover a small street, a farm or a hamlet, which is what three of the five were. A check of every name against a gazetteer of Britain is still to be made (section 13) |
| Location | Every coordinate lies in the box longitude -0.20 to 0.20, latitude -0.15 to 0.15, which is open sea. No synthetic polygon can be laid over a real street |
| Shortest journey | No time in the release is under 2 minutes: not a cell of `travel.json`, and not a `walk_minutes` in `stations.json`. The `station_walk` feature is a distance in metres: the made-up town has no streets, so it is the walk to the nearest station at 80 m a minute, and none is under 160 m. The `grocery_walk` feature is drawn the same way, from the walk in minutes that it once was, so that no area changed places. A time is rounded to whole minutes and then held at 2, by `whole_minutes()` in `journeys.py` and nowhere else. The map can put a place at the middle of its area, and no distance at all is still down the stairs and across the road. Every sentence says "minutes", which 0 and 1 do not read well in |
| Gaps on purpose | About 6% of feature values are null. One rankable area has no cost rows. One has a `null` travel cell and one a `-1`. Otterby Fields, the new town, has none of the 17 features that version 2 added, so it can be placed on Houses or flats and on no other vibe. Otterby Fields has none of the measures of brands either. Grapnel Dock and Sedgewater Marsh, which have too few homes, have no share of homes and no rate, and of the brands no mix and no count of a tier, so neither can be placed on Quiet streets, Age of buildings, Everyday on foot, Houses or flats or Street character. These keep the missing-data paths tested |
| Mixed on purpose | Three areas hold both ends of a scale, one for each scale that a release carries with Gritty and without. Foxholt on Going out: band 4, from 3 to 5. Kindlewharf on Age of buildings: band 3, from 2 to 4. Sable Reach on Houses or flats: band 4, from 3 to 5. Each is set by hand, because no release holds the sub-areas a spread is worked out from |
| The older figures | The 23 features of version 1 are drawn from one stream and the 17 newer ones from a second, `Random(seed + 1)`, so that adding a feature moves no figure that was there. A test holds the older rows to one digest. The plan of the city was redrawn once, on 2026-09-24, so that no two vibes find the same areas: the features, the vibes and the costs of the areas that were changed moved with it, and the digest was taken again. Travel, stations, places and the map read no trait, and are as they were first drawn |
| Journeys, drawn and worked out | The committed release holds journeys that are drawn from where things are. `python -m burro_pipeline travel --made-up` builds the same city with journeys worked out from a made-up timetable, as the step that will route London works them out. It is built on demand as `syn-2026-09-24-07` and is never committed. It routes to 120 minutes by public transport, where the committed release holds 90, and nothing but `travel.json` differs between the two |
| With Gritty, and without | `build_synthetic(..., gritty_variant)` builds either. The committed release is `b`, which carries Gritty. `a`, which holds no recorded crime and carries every vibe but Gritty, is built on demand as `syn-2026-09-23-02` and is never committed. Which is built moves no figure: the two releases differ in one vibe and in nothing else |
| Determinism | `build_synthetic(seed, release_id, built_at, gritty_variant)` draws only from `random.Random(seed).random()`, whose sequence is stable across Python versions. The committed fixture is `syn-2026-09-23-01`, seed `20260923`, built at `2026-09-23T00:00:00Z`. A test rebuilds it and compares bytes |
| Plausibility | Values are drawn so that features correlate the way a city's would (nearer the centre: denser, noisier, shorter journeys, dearer). This is for demos only and is a claim about nothing |
| Districts that differ | The 17 newer features do not all follow the centre, so that the vibes find different areas. The centre is offices: it goes out less late than it is busy, and a food shop is further off. The most is recorded in the nightlife quarter, whose yards are workshops. The large parks are the meadows along the river and the green of an old village. New flats stand on the old quays. A small, compact town centre is one where little goes on. What is independent follows the plan of an area and not how much goes on there. Asked for alone, each end of each vibe puts an area of its own first, with one exception: Going out towards Buzzy and Houses or flats towards Flats both find the centre. A test holds the table of which area each end finds, and that every vibe has areas in every band |
| No two vibes alike | As first drawn, eleven vibes moved as about three: Houses or flats and Food and drink had a rank correlation of 0.97 across the areas, and Going out shared all of its first five areas with both. The plan now says where an area is not what its place on the map would make it, with three traits that are set by hand where they are set at all: how much of it is flats, whether a park is near, and whether its homes stand on a main road. So there are flats that are quiet, a leafy area on a main road, an old one with no green and a lively one where little is independent. Two things are held by a test, on the committed seed and three others, with Gritty and without. No two ends of two vibes share more than 3 of the first 5 areas that a search for each alone finds. No two vibes have a rank correlation above 0.8 across the areas placed on both, either way. Works and warehouses is 30 in 100 of Gritty, and main roads and transport noise are parts of Gritty and of Quiet streets, so Gritty stands nearer to each than any other two vibes stand. What is recorded is drawn to follow the night, the middle of town and a high street more than the works, or Gritty and Works and warehouses would find the same areas: they ran together at 0.92. In the committed release the greatest is 0.76, between Quiet streets and Gritty, and three pairs of 55 are above 0.7. Works and warehouses is compared where a release carries it, which is where it holds no recorded crime |
| The flag | `manifest.synthetic` reaches every API response (section 9.1) |

### 2.10 The census, which is no part of a release

An area's page shows census figures about the people who lived there ([ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md)). They are shown and used for nothing else, so they are kept apart from the release by structure:

| Fence | Held by |
|---|---|
| The census is in a folder of its own, named for the release with `-residents` after it. It holds `manifest.json` and `census.json` and nothing else | `open_census` |
| A release folder that holds a `census.json` is refused | `open_release`, `files_match_manifest` |
| `Release` has no member that returns a census, and `InMemoryRelease` holds none | A test reads the protocol |
| Nothing in core imports `census.py`, and `burro_core` does not export it. It imports `_record` and `ids` and nothing else of core | A test reads the imports |
| `open_census`, `parse_census`, `panel` and `offer` are never handed a release. They are told its id, whether it is made up, and the ids of its areas | A test reads their signatures |
| A kind of table is a `CensusKind`. It is no `FeatureId`, no `TagId`, no `FactKind` and no `Setting`, so no spec, edit, fact or sentence can name one | A test reads every enum of the vocabulary |
| No step of the pipeline that builds what is ranked imports the census, and the writer of the census imports none of them | A test reads the imports |

**The kinds.** `age`, `households`, `country_of_birth`, `ethnic_group` and `religion`. The last three are `SHOWN_AND_NEVER_RANKED_ON`: shown on an area's page, and never ranked, filtered or compared on. Age and the make-up of households are shown here too. A measure that is built from either, to feed a vibe, is a feature of the catalogue with an id and a source of its own, and is read from the release like any other: it is never read from this file.

**`census.json`.**

| Part | Fields | Notes |
|---|---|---|
| Top | `release_id`, `synthetic`, `taken_on`, `retrieved_on`, `sources` | `taken_on` is the day of the census. `sources` holds the fields of a source of a release |
| `tables` | `table_code`, `kind`, `title`, `variable`, `universe`, `unit`, `definition`, `source_id`, `url`, `rows` | Once for the census. `unit` is `people` or `households`. `definition` is the publisher's own sentence. `url` is the publisher's page for the table, and is empty for a made-up table |
| A row of a table | `code`, `heading`, `label`, `depth` | In the publisher's order. `heading` is the publisher's heading whole, for a screen reader. `label` is the part that is printed. `depth` is 0, 1 or 2 |
| `whole` | `name`, `tables` | The whole city: London. Each table as for an area |
| `areas` | `area_id`, `output_areas`, `tables` | Every area of the release once, by id |
| A table of an area, or of the whole | `table_code`, `base`, `counts`, `reason` | `base` is how many were counted. `counts` is in the order of the table's rows, and holds `null` for a count that is under 1 in 100 of `base`. Where the table is left out, `base` is `null`, `counts` is empty and `reason` is `too_few` or `not_held` |

**Small numbers.** The publisher swaps records between small areas and changes about 14 in 100 counts by a small amount, small counts more often. Its guidance names counts of nought, one and two as small, and gives no figure under which a count is withheld or is not to be relied on: both of its pages on the matter were read on 2026-09-24, each twice, and neither names one. So the two figures below are Burro's, and a first guess (section 13).

| Rule | Detail |
|---|---|
| `too_few_are_left_out` | A table is left out for an area where fewer than `FLOOR`, 1,000, were counted in it, people or households |
| `small_counts_are_withheld` | No count is held that is under 1 in 100 of those counted. The share is then said in words, "fewer than 1 in 100", and no count is given. Nothing reads "0%" or "none" |
| Together | No count under 10 is ever held, served or printed |
| What is not hidden | A count that is withheld can be worked out from the others where one row of a group is small. It is no secret: the publisher prints the count itself. It is left out because it is not steady enough to print |

**The rules of `parse_census`**, each a small function in `RULES`, each shown refusing a census by a row of `BROKEN` in `tests/test_census.py`:

| Rule | Refused when |
|---|---|
| `census_is_of_the_release` | It names another release, or says it is made up where the release does not |
| `made_up_is_said` | A made-up count cites a source other than `synthetic`, names an area without the `syn-` prefix, or gives a table an address. A real one does the opposite of any |
| `tables_are_in_order` | A kind or a code of a table repeats, a row's code repeats, a table names a source the census does not hold, or a row stands more than one step under the row before it |
| `areas_are_the_releases` | The areas are not every area of the release once, in the order of its id |
| `rows_are_complete` | An area or the whole city lacks a table, or a table that is not left out lacks a count for a row, or one that is left out holds any |
| `too_few_are_left_out`, `small_counts_are_withheld` | As above |

`open_census(folder_name, files, release_id, synthetic, area_ids)` checks the name of the folder, that it holds the two files and no other, the hash and the length of `census.json` against the manifest, and then calls `parse_census`. A refusal is a `CensusError`, which names the file, the row and the rule and never a value.

**What is served of a row** is worked out by `panel(census, area_id, name)`, and by nothing else:

| Field of `CensusPanelRow` | What it holds |
|---|---|
| `code`, `heading`, `label`, `depth` | The row, as the census holds it |
| `share` | The area's share as it is printed: a whole per cent, `round(100 * count / base)` with a tie to the even number (section 0); "fewer than 1 in 100"; or "over 99%" where the share rounds to 100 and not every one counted is in the row |
| `count` | The count as it is printed, "1,437". `null` where the share is under 1 in 100 |
| `percent` | The share as a whole number, for the picture alone. `null` where the share is under 1 in 100 |
| `city_share`, `city_percent` | The same two for the whole city. No count of the city is served |

The record has no other field, so nothing else can stand beside a figure: no other area, no rank, no band and no word about what the figure means. The rows are served in the order the census holds them, which is the publisher's, and nothing puts one before another by its figure.

**The words** are fixed text in core: `CENSUS_2021` for a real census and `MADE_UP` for the made-up count, which names no real census, no real publisher and no real event. Each fills the same gaps, so that a page laid out on one is laid out for the other. No word of either is one Burro would be choosing of a figure: `NEVER_SAID` holds "diverse", "mixed", "main", "majority", "minority" and the like, and a test reads every word of both, and every string a panel serves but a publisher's own heading.

| Part | Words of `CENSUS_2021` |
|---|---|
| `heading` | Census 2021: who lived here |
| `intro` | Official figures for the people who lived here on {day}: age, households, country of birth, ethnic group and religion. Burro never ranks, filters or compares areas by ethnic group, religion or country of birth. |
| `date_line` | Census 2021, taken on {day}. Published by the Office for National Statistics. |
| `notes` | The census was taken during a lockdown. Some people were not living where they usually do. · An area can change. These figures are of that day, and not of today. · {name} is drawn by Burro from {areas}. The figures are the statistics office's counts, added up by Burro. No official table has this boundary, so none will match exactly. · The statistics office changes small counts slightly so that nobody can be picked out. Shares are whole numbers and may not add up to 100%. Where fewer than 1 in 100 were counted, the table says so and gives no count. · Beside each figure is the figure for {city}, and nothing else. Burro says nothing about what a figure means. |
| `caption` | {title}. Census 2021, {day}. Share of {universe} in {name}, with the number counted, beside the share in {city}. About {base} {unit} counted in {name}. |
| `definition` | The statistics office's definition: "{definition}" |
| `of_the_day`, under the tables of age and of households | The statistics office says: "The coronavirus pandemic may have affected some people's choice of usual residence on Census Day." |
| `shown_only`, under the three tables that are never ranked on | Shown here and nowhere else. Burro never ranks, filters or compares on it. |
| `too_few`, `not_held` | {title}. Too few {unit} lived in {name} on census day for Burro to give shares. · {title}. The census figures Burro holds have none for {name}. |
| `source_line`, `derivation_line`, `licence_line` | Source: Office for National Statistics. Census 2021, tables {codes}, for output areas. Retrieved {retrieved}. · Added up by Burro over the {areas} of {name}. The shares are Burro's arithmetic on the office's counts. · Contains public sector information licensed under the Open Government Licence v3.0. |

The caption repeats the census, its day, the area and how many were counted, so that a picture of any one table carries all of it. `{base}` is the base to the nearest 100. `{areas}` is how many of the publisher's small areas were added up, said so that one reads as one: "1 census output area", "26 census output areas".

**Writing one.** `write_census` asks the licence gate for the one use `census_table` for every source of a census that is not made up, and refuses a table that the entry of its source does not name (`table_is_named_by_its_source`). A real census is refused with no registry, and is never written over. No step reads a real census table yet: what is built is the made-up count, the folder, the gate and the judge.

**The made-up count.** `made_up_census(release, seed)` draws a count for the made-up city from a stream of its own, so that it moves no figure of the release. It is committed at `data/fixtures/residents/syn-2026-09-23-01-residents/`, outside the folder of releases, so that whatever lists the releases of the repository finds releases and nothing else. `make fixture` rebuilds it, and a test compares bytes.

| Rule | Detail |
|---|---|
| Tables | Five, one of each kind: `SYN-HH`, `SYN-BORN`, `SYN-AGE`, `SYN-GRP`, `SYN-BLF`, of 20, 12, 18, 24 and 9 rows, as deep and as long as a publisher's |
| No real group | The three tables that stand in for country of birth, ethnic group and religion name made-up countries, groups and beliefs. A test holds the headings of the three real tables and fails if one is in the count, so that no picture of the made-up city shows a made-up share of real people |
| No trait | Those three tables are drawn from noise alone. Nothing about a made-up group goes with how leafy, how lively or how dear an area is |
| Gaps on purpose | Grapnel Dock and Sedgewater Marsh hold too few, so every table of theirs is `too_few`. Otterby Fields is `not_held`. Every other area holds a row that is under 1 in 100 |
| The whole | Quillhaven, the sum of every area that was counted |

### 2.11 Household income, which is shown and is no measure

An area's page shows what the households of the area are estimated to have as income ([ADR 0028](../adr/0028-household-income-is-shown-and-never-ranked-on.md)). It is a figure about who lives somewhere, so it is shown and used for nothing else, and it is kept apart from a release by structure, exactly as the census is (section 2.10).

| What keeps it apart | Held by |
|---|---|
| It is in a folder of its own, named for the release with `-income` after it. It holds `manifest.json` and `income.json` and nothing else | `open_income` |
| A release folder that holds an `income.json` is refused | `open_release`, `files_match_manifest` |
| `Release` has no member that returns it, and `InMemoryRelease` holds none. It is no `FeatureId`, no `TagId`, no `Segment` and no kind of fact, so no spec, edit, fact or sentence can name it | A test reads the protocol and the vocabulary |
| Nothing in core imports `income.py`, and `burro_core` does not export it. It imports `_record` and `ids` and nothing else of core | A test reads the imports |
| `open_income`, `parse_income`, `shown` and `offer` are never handed a release. They are told its id, whether it is made up, and the ids of its areas | A test reads their signatures |
| The licence registry holds the source for `display` and `validation_only` alone, so the gate refuses the file for a feature, a tag or a cost | `Registry.require`, and a test that asks for `scoring` |
| One module of the pipeline opens the workbook, for `display`. It is on no list of measures, makes no row of a catalogue and no row of evidence, and works out no percentile | A test reads the imports and the list |

**`income.json`.**

| Part | Fields | Notes |
|---|---|---|
| Top | `release_id`, `synthetic`, `start`, `end`, `source` | `start` and `end` are the first and the last month of the year the figures are of, `YYYY-MM`, twelve months apart. `source` holds the fields of a source of a release |
| `areas` | `area_id`, `estimate`, `lower`, `upper` | Every area of the release once, in the order of its id. Whole pounds a year, each a whole number of 1 or more, or all three `null` where the publisher gives no figure for the area. `lower` and `upper` are the limits of the publisher's confidence interval |

`manifest.json` holds `release_id`, `synthetic`, `income_sha256`, `income_bytes` and `source`.

**The rules of `parse_income`**, each a small function in `RULES`, each shown refusing a file by a row of `BROKEN` in `tests/test_income.py`:

| Rule | Refuses |
|---|---|
| `income_is_of_the_release` | It names another release, or says it is made up where the release does not |
| `made_up_is_said` | A made-up file cites a source other than `synthetic`, names an area that is not made up, or gives an address of a publisher. A real one does the opposite of any of these |
| `areas_are_the_releases` | It does not hold every area of the release once, in the order of its id, and no other |
| `limits_hold_the_estimate` | An estimate stands without both its limits, or outside them |
| `year_is_a_year` | The figures are of a period that is not twelve months |

A record refuses a field it does not know, so nothing can be put beside a figure in the file: no percentile, no rank, no figure of the whole city.

**What is served of an area** is put into words by `shown(income, area_id)`, and by nothing else:

| Field | What it is |
|---|---|
| `heading`, `kind`, `definition` | The heading of the block, the publisher's own name for the kind of income, and its own definition of it |
| `estimate`, `lower`, `upper`, `limits` | The figure and its two limits, as they are printed: `£52,300`, and `£46,100 to £59,300`. `null` where the publisher gives none |
| `limits_label`, `none_given` | What the limits are called, and the sentence that stands in the place of a figure where there is none |
| `year_line`, `modelled` | The year the figure is of, and that it is an estimate from a model, in the publisher's words |
| `notes` | That it is a mean and no median, and of the area and of no household. What the publisher says of its confidence interval. That no change over time is shown. That nothing stands beside the figure |
| `source_line`, `licence_line`, `source_url`, `open_source` | The credit the publisher asks for, the licence, the publisher's page, and the words of the link to it |

The record has no other field. So nothing stands beside the figure: no other area, no figure of the whole city, no rank, no band, no colour and no word of Burro's about what it means. The publisher asks that areas are compared only with the confidence intervals in mind, and Burro compares none.

**The words** are fixed text in core: `ONS` for the statistics office's estimates and `MADE_UP` for made-up ones, which name no real publisher. What `ONS` quotes of the publisher is quoted from the workbook, and a build holds the workbook to the same words: `derive/household_income.py` stops at a workbook that does not say that the estimates are model-based, that does not define total annual household income as the page does, whose notes do not give the year of its receipt, or whose terms do not ask for the credit that is given.

**Writing one.** `write_income` asks the licence gate for `display` for the source of figures that are not made up. Real figures are refused with no registry, and are never written over. `preview` writes the folder beside the release where a list of the build names the workbook and it has a receipt. The record of the build says `shown_and_never_ranked_on`, and gives counts and no figure.

**The made-up estimates.** `made_up_income(release, seed)` draws an estimate for each area of the made-up city from a stream of its own, from noise alone: it reads no plan of an area and no figure of the release, so nothing about a made-up income goes with how leafy, how lively or how dear an area is. One area is left with no estimate on purpose. It is committed at `data/fixtures/income/syn-2026-09-23-01-income/`, outside the folder of releases. `make fixture` rebuilds it, and a test compares bytes.

## 3. The v1 feature catalogue

### 3.1 Features

114 features, of which 48 are of the chains of grocers, gyms and coffee and have a table of their own in section 3.1.1. Each describes a place, its buildings, or what was recorded there, but for four that describe who lived there at the census of 2021: residents of two ages, and households of two kinds. Nothing else about who lives anywhere has an id (ADR 0006, as amended on 2026-09-24). An id names the idea, not the method: distances and thresholds live in `definition` and may change with `CATALOGUE_VERSION`. An id is never renamed, reused or given a new meaning.

Polarity is `less` (lower is better), `more` (higher is better) or `either` (the user chooses). The comparatives fill the sentence "*X* than 80% of areas". The last column is the main registry id a real release is expected to use, beside any it needs for a denominator or a network; the synthetic release uses `synthetic` for all. Of the 21 features that version 2 added, two have a source named here, because a real build works them out: `road_major_exposure` and `park_large_proximity`. The rest have none yet: each is chosen from the registry when it is ingested.

| Field of a feature | What it says |
|---|---|
| `short_label` | At most 40 characters, no figure and no place name. It says the wish where the polarity is fixed, "Less transport noise", and the measure where it is `either`, "Pubs and bars". A switch and a suggestion are named by it |
| `kind` | `taste`: wanting less of it is a taste in places. `amenity`: a thing to be near. `nuisance`: a thing it is a nuisance to have, so its one direction is less. `on_request`: weighed only when a person asks in so many words. `residents`: it counts who lived somewhere, and a person may ask for more of what it counts and never for fewer. `NUISANCES` is read from it |
| `describes` | `place`, `buildings`, `events`, which is what was recorded there, or `residents`. `COUNTS_RESIDENTS` is the four features that describe residents, and a test holds the list to those four |
| `family` | One of the five families a setting is grouped by, or none: `streets_homes`, `pace_food`, `green`, `daily_life`, and `who_lives_there`, which is said as "Who lives there, at the 2021 census" |
| `method` | How the figure is made: `measured`, `modelled` or `averaged`. It is `modelled` for `air_no2`, whose publisher gives a model's figure and no reading. It is `averaged` for `noise_exposure`, whose publisher gives a share for each small area and no count behind it, so that an area's figure is the mean of them. It is `measured` for every other until a real build finds one that is not. A build says how each of its figures was made from the method its rows of evidence name, and leaves a measure out where that is not what core says |
| `in_likeness` | Whether likeness may be counted on it (section 6.9) |

| `feature_id` | Dimension | Label | Short label | Unit | Polarity | Kind | Describes | Family | Likeness | Higher / lower | Real source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `crime_violence_robbery` | crime | Recorded violence and robbery | Less recorded violence and robbery | per 1,000 residents a year | less | nuisance | events | none | no | more / less | `police-uk-street-level-crime` |
| `crime_burglary_theft` | crime | Recorded burglary and theft | Less recorded burglary and theft | per 1,000 residents a year | less | nuisance | events | none | no | more / less | `police-uk-street-level-crime` |
| `school_primary_nearby` | schools | State primary schools within 800 m in a straight line | More primary schools nearby | count | more | amenity | place | daily_life | no | more / fewer | `dfe-gias` |
| `school_primary_attainment` | schools | Pupils meeting the expected standard at nearby primaries | Higher primary school results | % | more | on_request | place | daily_life | no | higher / lower | `dfe-school-performance-tables` |
| `school_secondary_attainment` | schools | Attainment 8 at nearby secondaries | Higher secondary school results | points | more | on_request | place | daily_life | no | higher / lower | `dfe-school-performance-tables` |
| `university_proximity` | schools | Distance to the nearest university site | Nearer a university | m | less | on_request | place | daily_life | no | further / closer | `dfe-gias` |
| `green_cover` | green_water | Public parks and gardens as a share of the area | More public parks and gardens | % | more | amenity | place | green | yes | more / less | `os-open-greenspace` |
| `park_proximity` | green_water | Straight-line distance to the nearest marked way into a park of 2 ha or more | Nearer a park | m | less | amenity | place | green | yes | further / closer | `os-open-greenspace` |
| `play_space_proximity` | green_water | Straight-line distance to the nearest marked way into a play space | Nearer a play space | m | less | amenity | place | green | yes | further / closer | `os-open-greenspace` |
| `water_access` | green_water | Share of homes within 300 m, in a straight line, of the centre line of a river, canal or lake | Nearer a river or canal | % | more | amenity | place | green | no | more / less | `os-open-rivers` |
| `air_no2` | air_noise | Modelled annual mean nitrogen dioxide | Cleaner air | µg/m³ | less | nuisance | place | none | no | higher / lower | `defra-pcm-background-air` |
| `noise_exposure` | air_noise | Share of residents exposed to 55 dB or more of transport noise | Less transport noise | % | less | nuisance | place | none | no | noisier / quieter | `mhclg-iod-2025-underlying-indicators` |
| `venue_food_drink` | venues_culture | Places to eat and drink within 800 m of home, in a straight line | Places to eat and drink within reach | count | either | taste | place | pace_food | yes | more / fewer | `fsa-food-hygiene-ratings`. Shown, and never ranked on |
| `venue_evening` | venues_culture | Pubs and bars within 800 m of home, in a straight line | Pubs and bars within reach | count | either | taste | place | pace_food | yes | more / fewer | `overture-places`. Shown, and never ranked on. A nightclub is not counted |
| `venue_independent` | venues_culture | Places to eat and drink that are not part of a chain | More places that are not chains | % | more | taste | place | pace_food | no | more / fewer | `fsa-food-hygiene-ratings` |
| `culture_venues` | venues_culture | Museums, galleries, theatres, cinemas, music venues and libraries within 800 m of home, in a straight line | Cultural venues within reach | count | more | amenity | place | pace_food | yes | more / fewer | `overture-places`. Shown, and never ranked on |
| `highstreet_access` | venues_culture | Straight-line distance to the nearest town centre boundary | Nearer a town centre | m | less | amenity | place | pace_food | yes | further / closer | `gla-town-centre-boundaries`. A town centre is not a high street, and no name of the measure says one. The id is kept |
| `homes_flats` | homes | Flats as a share of homes | Flats | % | either | taste | buildings | streets_homes | no | more / fewer | `voa-council-tax-stock-of-properties` |
| `homes_pre1919` | homes | Homes built before 1919 | Period homes | % | either | taste | buildings | streets_homes | yes | more / fewer | `voa-council-tax-stock-of-properties` |
| `homes_density` | homes | Homes per hectare | Homes close together | per ha | either | taste | buildings | streets_homes | no | denser / less dense | `voa-council-tax-stock-of-properties` |
| `conservation_cover` | homes | Share of the area in a conservation area | More protected streets | % | more | taste | buildings | streets_homes | yes | more / less | `mhclg-planning-data-conservation-areas` |
| `station_walk` | station_access | Straight-line distance to the nearest way in to a station | Nearer a station | m | less | amenity | place | daily_life | yes | further / closer | `dft-naptan` |
| `station_lines` | station_access | Lines within a 10-minute walk | More lines nearby | count | more | amenity | place | daily_life | no | more / fewer | `tfl-journey-planner-timetables` |
| `independents_nearby` | venues_culture | Share of the places to eat and drink within 800 m of home, in a straight line, that belong to no chain | More independent places nearby | % | more | taste | place | pace_food | yes | more / fewer | `overture-places`. A place belongs to a chain where the file gives it a brand |
| `centre_small` | homes | Share of homes whose nearest town centre is a small one | A small town centre | % | more | taste | place | streets_homes | yes | more / less | none named yet |
| `centre_compact` | homes | Share of the nearest town centre within 200 m of its middle | A compact town centre | % | more | taste | place | streets_homes | yes | more / less | none named yet |
| `listed_buildings` | homes | Listed buildings | More listed buildings | per km² | more | taste | buildings | streets_homes | yes | more / fewer | none named yet |
| `homes_post2000` | homes | Homes built since 2000 | New homes | % | either | taste | buildings | streets_homes | yes | more / fewer | none named yet |
| `road_major_exposure` | air_noise | Share of homes within 100 m of a main road | Away from main roads | % | less | nuisance | place | streets_homes | no | more / less | `os-open-roads` |
| `evening_cluster_exposure` | air_noise | Share of homes with three or more pubs or bars within 150 m, in a straight line | Away from clusters of pubs and bars | % | less | nuisance | place | pace_food | no | more / less | `overture-places`. The file cannot say how late a place is open, so no name of the measure says late |
| `land_industry` | homes | Land used for industry | Industrial land | % | either | taste | place | streets_homes | yes | more / less | none named yet |
| `land_storage` | homes | Land used for storage and warehousing | Storage and warehouse land | % | either | taste | place | streets_homes | yes | more / less | none named yet |
| `land_transport_other` | homes | Land used for transport other than roads, such as railways, airports and docks | Transport land other than roads | % | either | taste | place | streets_homes | yes | more / fewer | `mhclg-land-use-statistics-2022`. Its publisher puts depots and yards under storage |
| `land_gardens` | green_water | Land that is residential garden | More gardens | % | more | amenity | place | green | yes | more / less | none named yet |
| `land_woodland` | green_water | Land that is woodland | More woodland | % | more | amenity | place | green | yes | more / less | none named yet |
| `park_large_proximity` | green_water | Straight-line distance to the nearest marked way into a park of 20 ha or more | Nearer a large park | m | less | amenity | place | green | yes | further / closer | `os-open-greenspace` |
| `park_facilities` | green_water | Kinds of thing to do in parks within a 15-minute walk | More to do in parks | count | more | amenity | place | green | yes | more / fewer | none named yet |
| `grocery_walk` | services | Straight-line distance to the nearest food shop | Nearer a food shop | m | less | amenity | place | daily_life | yes | further / closer | `overture-places`. A food shop is a place its file gives as a grocer, a supermarket or a convenience store. The id is kept |
| `incident_criminal_damage` | crime | Recorded criminal damage and arson | Less recorded criminal damage | per 1,000 homes a year | less | nuisance | events | none | no | more / less | `police-uk-street-level-crime` |
| `incident_antisocial` | crime | Recorded anti-social behaviour | Less recorded anti-social behaviour | per 1,000 homes a year | less | nuisance | events | none | no | more / less | `police-uk-street-level-crime` |
| `private_outdoor_space` | homes | Addresses with private outdoor space | More addresses with outdoor space | % | more | amenity | buildings | streets_homes | no | more / fewer | `ons-access-to-garden-space-2020`, held to `ons-msoa11-msoa21-lad22-lookup`. A build of London carries it since 2026-09-25, when the proxy audit it was held back for was dropped (ADR 0006). The made-up release does not |
| `cuisine_variety` | venues_culture | Kinds of food nearby | More kinds of food | count | more | taste | place | pace_food | no | more / fewer | none named yet |
| `gp_walk` | services | Straight-line distance to the nearest GP practice, placed by its postcode | Nearer a GP surgery | m | less | amenity | place | daily_life | yes | further / closer | `nhs-ods-gp-practices`. A build of London carries it, and the made-up release does not |
| `pharmacy_walk` | services | Straight-line distance to the nearest pharmacy, placed by its postcode | Nearer a pharmacy | m | less | amenity | place | daily_life | yes | further / closer | `nhsbsa-consolidated-pharmaceutical-list`. A build of London carries it, and the made-up release does not |
| `venue_food_drink_per_homes` | venues_culture | Places to eat and drink for each 1,000 homes within 800 m, in a straight line | Places to eat and drink | per 1,000 homes | either | taste | place | pace_food | no | more / fewer | `fsa-food-hygiene-ratings`. What a wish for places to eat and drink is ranked on |
| `price_median` | homes | Median price paid for a home | What homes sell for | £ | either | taste | buildings | streets_homes | no | dearer / cheaper | `ons-median-house-prices-msoa`. The second reading of a word for a smart area. In no vibe, and weighed by nothing until a person asks |
| `culture_venues_per_homes` | venues_culture | Museums, galleries, theatres, cinemas, music venues and libraries for each 1,000 homes within 800 m, in a straight line | More culture nearby | per 1,000 homes | more | amenity | place | pace_food | no | more / fewer | `overture-places`. What a wish for culture is ranked on |
| `venue_cafe` | venues_culture | Cafes and coffee shops within 800 m of home, in a straight line | Cafes within reach | count | more | amenity | place | pace_food | no | more / fewer | `overture-places`. Shown, and never ranked on |
| `venue_cafe_per_homes` | venues_culture | Cafes and coffee shops for each 1,000 homes within 800 m, in a straight line | More cafes nearby | per 1,000 homes | more | amenity | place | pace_food | no | more / fewer | `overture-places`. What a wish for cafes is ranked on |
| `venue_gym` | venues_culture | Gyms and fitness studios within 800 m of home, in a straight line | Gyms within reach | count | more | amenity | place | pace_food | no | more / fewer | `overture-places`. Shown, and never ranked on |
| `venue_gym_per_homes` | venues_culture | Gyms and fitness studios for each 1,000 homes within 800 m, in a straight line | More gyms nearby | per 1,000 homes | more | amenity | place | pace_food | no | more / fewer | `overture-places`. What a wish for a gym is ranked on |
| `venue_evening_per_homes` | venues_culture | Pubs and bars for each 1,000 homes within 800 m, in a straight line | Pubs and bars | per 1,000 homes | either | taste | place | pace_food | no | more / fewer | `overture-places`. What a wish for pubs and bars is ranked on, and what Going out holds |

### 3.1.1 The chains of grocers, gyms and coffee

Decided by the founder on 2026-09-24 (ADR 0026): which chains stand in a place says something of it. 48 features, all of dimension `brands`, family `daily_life`, describing a `place`, `measured`, and held out of likeness. None stands in a vibe, and none is weighed by default.

| `feature_id` | Label | Short label | Unit | Polarity | Kind | Higher / lower | What it is for |
|---|---|---|---|---|---|---|---|
| `grocer_premium_nearby`, `grocer_mid_nearby`, `grocer_value_nearby`, and the same for `gym` and `coffee`: nine | "Premium grocers within 800 m of home, in a straight line, by Burro's table of tiers", and so for each kind and tier. The kinds are said "grocers", "gyms" and "coffee places", and the tiers "premium", "mid-range" and "value" | "Premium grocers within reach" | count | more | amenity | more / fewer | Shown on an area's page. A release says `rankable: false` of each |
| `grocer_premium_distance` and the eight like it: nine | "Straight-line distance to the nearest premium grocer within 2,000 m of home, by Burro's table of tiers" | "Nearer a premium grocer" | m | less | amenity | further / closer | Shown on an area's page. A release says `rankable: false` of each |
| `brand_mix` | "Share of the chain grocers, gyms and coffee places within 800 m of home that are premium, with a mid-range one counted as half, by Burro's table of tiers" | "Mix of brands" | % | either | taste | more premium / less premium | What is ranked on. The first reading of a word for a smart area, and the one reading of a word for a plain one (section 8.2) |
| `brand_waitrose`, `brand_mands`, `brand_whole_foods`, `brand_sainsburys`, `brand_tesco`, `brand_coop`, `brand_morrisons`, `brand_asda`, `brand_aldi`, `brand_lidl`, `brand_iceland`, `brand_equinox`, `brand_third_space`, `brand_barrys`, `brand_virgin_active`, `brand_nuffield`, `brand_gymbox`, `brand_david_lloyd`, `brand_anytime_fitness`, `brand_puregym`, `brand_the_gym_group`, `brand_gails`, `brand_ole_and_steen`, `brand_pret`, `brand_nero`, `brand_starbucks`, `brand_costa`, `brand_blank_street`, `brand_greggs`: 29 | "Straight-line distance to the nearest Waitrose within 2,000 m of home" | "Nearer a Waitrose" | m | less | on_request | further / closer | Shown on an area's page, where it names the chain. Weighed only where a person asks for the chain by name |

- **The table of tiers is the founder's, and is data of the pipeline's.** Core names the three kinds, the three tiers and the 29 chains, in `KINDS_OF_CHAIN`, `TIERS` and `CHAINS`. It never says which chain is of which tier. That is in `brand_tiers.toml` in the pipeline, which a person adjusts, and the `definition` of each measure of a release lists the chains it counted. Five of the 29 were added beside the founder's own 24, and the file says which.
- **The mix is what is ranked on.** The counts and the distances of a tier are shown beside it and are never weighed: `SHOWN_BESIDE_THE_MIX` holds the eighteen, a release that says one can be ranked on is refused (`catalogue_matches_core`), and an edit or a spec that weighs one meets `not_in_release`.
- **A chain has one direction.** A person may ask to be near a chain, and never to be far from one: beyond 2,000 m a distance is not known, so far could not be told from missing.
- **Within 800 m, and the nearest as far as 2,000 m.** `WITHIN_M` and `NEAREST_WITHIN_M`. An area where no place of a chain or a tier stands within 2,000 m of most homes has no distance to one: the figure is not known, and is never said as 2,000.
- **Every one of them is of the place.** Each counts shops. None counts a person, and the name of none holds a word for who lives somewhere: a chain of gyms whose name holds such a word is said by the rest of its name. What the mix follows was measured, and written down, before it was served: the row is in `docs/research/data/brands.md`, section 8. The proxy audit it was written for is dropped since 2026-09-25, and the row holds nothing back.
- **A place is of a chain where the file of places gives it the chain's brand**, by the id an encyclopaedia gives the chain or by the name as the file writes it, and is of the chain's kind where the file also gives it a category of that kind. No name of a place is read.
| `underground_proximity` | station_access | Straight-line distance to the nearest Underground or DLR station | Nearer the Underground or DLR | m | less | amenity | place | daily_life | no | further / closer | `dft-naptan`, the national file. To a way in or to the station itself, whichever is nearer |
| `overground_proximity` | station_access | Straight-line distance to the nearest Overground or Elizabeth line station | Nearer the Overground or Elizabeth line | m | less | amenity | place | daily_life | no | further / closer | `dft-naptan`, with `tfl-step-free-station-topology`, which says which modes call at a station. The two are joined by where a station stands |
| `rail_proximity` | station_access | Straight-line distance to the nearest National Rail station or tram stop | Nearer National Rail or a tram stop | m | less | amenity | place | daily_life | no | further / closer | `dft-naptan`, with `tfl-step-free-station-topology`. A station at which no more than the Overground or the Elizabeth line calls is not counted |
| `bus_stops_nearby` | station_access | Bus stops within 400 m of home, in a straight line | Bus stops nearby | count | more | amenity | place | daily_life | no | more / fewer | `dft-naptan`, the national file. Shown, and never ranked on |
| `bus_routes_nearby` | station_access | Bus routes that stop within 400 m of home, in a straight line | More bus routes nearby | count | more | amenity | place | daily_life | no | more / fewer | `tfl-bus-stops-and-routes`. What a wish for buses is ranked on. The routes of London Buses alone, as at the day its file is of |
| `residents_aged_20_34` | residents | Residents aged 20 to 34 as a share of all residents, Census 2021 | More young adults | % | more | residents | residents | who_lives_there | no | more / fewer | `ons-census-2021-age-and-household-tables` |
| `residents_aged_65_over` | residents | Residents aged 65 and over as a share of all residents, Census 2021 | More older residents | % | more | residents | residents | who_lives_there | no | more / fewer | `ons-census-2021-age-and-household-tables` |
| `households_dependent_children` | residents | Households with dependent children as a share of all households, Census 2021 | More households with children | % | more | residents | residents | who_lives_there | no | more / fewer | `ons-census-2021-age-and-household-tables` |
| `households_one_person` | residents | Households of one person as a share of all households, Census 2021 | More households of one person | % | more | residents | residents | who_lives_there | no | more / fewer | `ons-census-2021-age-and-household-tables` |
| `homes_higher_bands` | homes | Homes in council tax bands E to H as a share of homes | Homes in the higher council tax bands | % | either | taste | buildings | streets_homes | no | more / fewer | `voa-council-tax-stock-of-properties`. A reading of a word for a smart area that counts homes and not people. A band is a value of 1991, so it is no price. In no vibe, and weighed by nothing until a person asks |
| `price_rise_5y` | homes | Median price paid for a home, for each £100 of the median five years before | Price rise over five years | £ | either | taste | buildings | streets_homes | no | a steeper rise / a smaller rise | `ons-median-house-prices-msoa`. Offered for a word for a place on the rise. A rise is of prices that were paid, and promises nothing. In no vibe, and weighed by nothing until a person asks |
| `price_rise_10y` | homes | Median price paid for a home, for each £100 of the median ten years before | Price rise over ten years | £ | either | taste | buildings | streets_homes | no | a steeper rise / a smaller rise | `ons-median-house-prices-msoa`. As `price_rise_5y`, over ten years |
| `highstreet_conserved` | homes | Share of the nearest high street that lies in a conservation area | A high street in a conservation area | % | more | taste | buildings | streets_homes | no | more / less | `gla-high-street-boundaries`, with `mhclg-planning-data-conservation-areas`. The high street nearest a home, within 800 m in a straight line, as the mean over an area's homes. It was measured for Village feel. It counts land inside a line a planning authority drew, and cannot tell a village street from a main road through old streets |
| `road_traffic_nearby` | air_noise | Traffic past the busiest count point within 500 m of home, in a straight line | Less traffic nearby | motor vehicles a day | less | nuisance | place | streets_homes | no | more / less | `dft-road-traffic-counts`. The flow of all motor vehicles on an average day of a year, as its publisher estimates it, at the busiest count point within 500 m of where the homes of each small census area are taken to stand, each count point read at the latest year it has a figure for, as the mean over an area's homes. It is `modelled`: its publisher gives an estimate, and no reading. A home with no count point within 500 m has no figure, which is not a figure of nought |

Rules that come with the list:

- `FeatureId` and `TagId` are the only vocabulary an edit, a spec, a model or a fact may use. Adding a feature means adding an enum member, a `FEATURES` row and a row in the table above, in one change.
- Both crime features have default weight 0, appear in no vibe, and may be weighted only on an explicit request (section 5.3). No sentence may call a place safe or unsafe (section 7.4). The two features of recorded incidents, `incident_criminal_damage` and `incident_antisocial`, are of dimension `crime` and are held to the same rule. They are parts of one vibe, Gritty, whose id is `street_character`, and of no other (section 3.2).
- Walk distances are computed on a network that is not OpenStreetMap (ADR 0004). No such network is built yet. So `park_proximity` and `park_large_proximity` are straight lines, from the point where the homes of an output area are taken to stand to the nearest way in that the publisher marks, and their names say so. Since catalogue version 12 the same is so of `play_space_proximity`, `station_walk`, `highstreet_access`, `gp_walk` and `pharmacy_walk`, each a distance in metres, and of `school_primary_nearby`, which counts the schools within 800 m in a straight line. Since version 13 it is so of `grocery_walk`, the last that was named a walk. Each becomes a walk, under a name that says a walk, on the day a walk is worked out. Three measures keep a name that their figure does not yet bear out, so no build carries them: `park_facilities`, until it is decided whether a playing field is a park, and `centre_small` and `centre_compact`, so that Village feel stays off the map.
- Tenure, student share and every protected characteristic but age have no id and cannot be given one without changing ADR 0006. Of age and of what households are made of there are four ids, the last four of the table, and no other is added without a new decision.
- **A feature that counts who lives somewhere is held to six rules**, each by a test. It is read high and never low: its polarity is `more`, the reducer refuses an edit that asks for less of it (`direction_not_allowed`), `check_spec` refuses a spec that does, and no reading of any words asks for fewer of a group of people (section 8.4). It stands in a vibe with one way and never in a scale (section 3.2). It counts towards no likeness (section 6.9). Its label says who is counted and ends ", Census 2021", its unit is a share in 100, and a release holds no count of people. It is of age or of households and of nothing else: no name of one holds a word for ethnic group, religion, country of birth, income, health or qualifications. Its short label holds no figure, so the ages are said in the label: "More young adults" is of residents aged 20 to 34, and "More older residents" of residents aged 65 and over. Gender is left out.
- **Each of the five measures of how near stops are counts how near, and nothing of what runs.** No timetable is held. So none says how often anything runs, where it goes or how long a journey takes, and each says a straight line in its name. The stops of buses are shown and never ranked on, as the count of places to eat is: a stop on each side of a road is two stops, and a stop says nothing of how many buses call at it. `RANKED_AS` names the routes as what a wish for buses is ranked on. All five are held out of likeness, as the count of lines is. Each was to stay out until an audit had looked at it. No audit is run since 2026-09-25 (ADR 0006), and each stays out: whether one joins is the founder's to decide.
- **The traffic near where homes stand is a measure since catalogue version 15.** A build works it out from the Department for Transport's file of the flow at each count point, which is of Great Britain, and the made-up release carries a made-up figure of it. Its publisher counts every link of a main road and a sample of the minor roads, at one point on each. So a home has a figure only where a count point stands within 500 m of it, an area only where half its homes or more have one, and an area with none is never taken to have no traffic: in a vibe its part is left out and the rest is weighed again (section 3.2), and asked for by itself it stands below every area that has a figure (section 6.6). The flows of two count points are never added together: a home is given the busiest. The 500 m is `TRAFFIC_WITHIN_M` in `catalogue.py`, a first choice and the founder's to change: it stands in the label. A release may rank on the measure by itself. It is a nuisance, so no likeness counts it.
- **How much of the nearest high street lies in a conservation area is a measure since catalogue version 14.** A build of London works it out from the file of high street boundaries and the conservation areas, and the made-up release carries a made-up figure of it. An area where under half of the homes have a high street within reach has no figure, and nor has one whose authority sent no conservation area. It is held out of likeness, and whether it joins is the founder's to decide.
- **Independent places are a share, and are told from chains by the brand the file of places gives a shop.** Since catalogue version 13. Every phrase for an independent shop or cafe weighs `independents_nearby`. `venue_independent` keeps its id and its row, and no build carries it.
- **Places to eat and drink are shown as a count and ranked on for each 1,000 homes.** Decided on 2026-09-24. The count is a true count, and on its own it says little more than that an area is dense and central. So both figures are carried and shown, and `RANKED_AS` names the count as shown and never ranked on, with the measure that is ranked on in its place. A release that says the count can be ranked on is refused (`catalogue_matches_core`), an edit or a spec that weighs it meets `not_in_release`, and every word that names it, its own label among them, is read as a wish for the places for each 1,000 homes. No recipe holds a measure that is shown and never ranked on, and `checked_recipe()` refuses one that does. The plain name "Places to eat and drink" is the name of what is ranked on. The cultural venues are held to the same rule: `culture_venues` is the count within reach and is shown, and a wish for culture, and the vibe that holds it, are ranked on `culture_venues_per_homes`, whose plain name is "More culture nearby". Two records of one kind within 25 m are one venue, and no record is left out for how sure its publisher is of it. Both are first choices, for a person to look at again. **Cafes, gyms and pubs are held to the same rule,** and are counted from the same file the same way: `venue_cafe`, `venue_gym` and `venue_evening` are counts that are shown, and a wish is ranked on `venue_cafe_per_homes`, `venue_gym_per_homes` and `venue_evening_per_homes`. A cafe is a cafe, a coffee shop or a tea room. A gym is a gym, a fitness studio, as for yoga or pilates, or a sport or fitness facility, and no trainer, gymnastics centre, pool or court. A pub or a bar is no nightclub, no lounge and no bar for smoking. **Pubs and bars are counted from the file of places, and no longer from the food hygiene register.** The register was held against the file on 2026-09-24 and was not confirmed: its pubs follow how each council fills it in. The file is thin toward the edge of London, and every figure of pubs says so.
- `either` is for features of buildings and venues only, where wanting less is a taste in places. `university_proximity` is `less`: a campus is a place to be near, and "far from a university" would be a way to ask for fewer students, which section 8.4 refuses in words and must not be offered as a slider. Decided, 2026-09-23: the feature keeps one direction.
- Nine features are nuisances, which is every feature of `kind` `nuisance`: the two crime features, the two of recorded incidents, `air_no2`, `noise_exposure`, `road_major_exposure`, `evening_cluster_exposure` and `road_traffic_nearby`. Wanting less of one is caring about it, so "less noise" and "no pollution" raise its weight. A nuisance that is only named, or that the person says they like, makes no edit, because its one direction is less: "I like noise" is a wish no edit can express. Wanting less of anything else is a wish turned round, and no weight is ever raised for one (section 8.2). `NUISANCES` in `catalogue.py` is the list, and is read from `kind`.
- The registry puts conditions on some sources, and the feature inherits them. The ones that shape this contract: food and drink figures carry their data date wherever they appear, and no establishment is ever named; conservation areas never decide a tag alone (section 3.2) and an area the source does not cover is unknown, not zero; the sites of `green_cover` are never described as all green space, so no word of the feature says green space or greener.

### 3.2 Vibes

A vibe is what the product is asked for: leafy, villagey, lively. In the code and on the wire it is a tag, and `TagId` names it. It is a recipe over measured features. Each part reads a feature `high` (`u = percentile / 100`) or `low` (`u = 1 - percentile / 100`).

**A name and a label a person gave say no figure of their own.** A name holds no figure at all. The label of a measure may say again a figure the label of core says, as the distance it counts within, and no other: a label that said "within 500 m" of a measure that counts within 800 would be of nobody's measuring. A line of what a vibe cannot see is held so to the lines core says of that vibe. `figures_of()` in core reads the figures of a text.

**What a person may adjust, and a release may so carry otherwise than core** (ADR 0029). The hundredths of the parts of a recipe. The name of a vibe, which is its `label` and its `short_label` alike, and the names of the two ends of a scale. What it cannot see, after the line every vibe says first. Nothing else: its id, family, shape, meaning, flags and shelf are core's, and so are the parts of its recipe, their order and the end each is read from. So no release adds a part, takes one out or turns one round. What was adjusted is held to every rule below, as core's own are, and a name to the rule of a label in section 2.3, with 40 characters at most and no figure. A line of what a vibe cannot see that names the census or recorded crime is kept. `what_a_vibe_breaks()` in core holds the rule, and the tables below give core's own, which a build starts from.

`raw = sum(w_i * u_i) / sum(w_i)` over the parts whose feature has a value, and `coverage = sum(w_i present)`. The `w_i` are the hundredths the release carries. If `coverage < 0.6` then `raw`, `score` and `band` are null. So are they for a vibe of `PLACED_ONLY_WITH` where none of the parts named for it has a value, whatever `coverage` is. No vibe is named there today: Village feel was, until 2026-09-25, and the rule is kept for any vibe that is held off in future. `score` is the percentile of `raw` and `band` its band, by section 2.4. `tag_raw()` in core is the only implementation; the pipeline calls it, and hands it the recipe the release carries. It rounds `raw` to six decimals, the precision a release is written with, so the number is the same before writing and after reading.

`TAGS` holds each weight as a whole number of hundredths, so that coverage is compared exactly: a vibe is null when the present hundredths sum to less than 60. A float sum of 0.30, 0.15 and 0.15 must not be left to decide which side of the line it falls.

A vibe has one of two shapes. A **scale** has two named ends, and a person may ask for either: Going out runs from Calm to Buzzy. Its high end is the end its recipe counts towards. A vibe with **one way** has no named ends, and a person may ask for more of it or take it off. `family` groups it with the settings of section 3.1. `meaning` is one plain sentence. `cannot_see` is what the recipe cannot see, and its first line is the same for every vibe, word for word: "One street or one home. An area is many streets." `lens`, `strip` and `table` say whether the map, a result and a comparison may show it. Every vibe holds all three, but for the two that count who lived somewhere and the one that is a rough guide, which hold no `strip`: none of them is put on a result by itself, and none is in the lists of what an area has most and least of (sections 6.7 and 7.6). `sureness` says whether a vibe is as sure as the rest, `as_the_rest`, or a rough guide, `rough_guide`. It has those two values and no other, it is no number, and a vibe that does not say is as sure as the rest, which is what a client takes it to be where the field is absent. Village feel is the one rough guide. `shelf_word`, `shelf_toward` and `shelf_order` put seven of them on the shelf a search starts from.

| `tag_id` | Label | Family | Shape and ends | Recipe, in hundredths | Shelf |
|---|---|---|---|---|---|
| `leafy` | Leafy | green | one way | 40 `land_gardens` high + 30 `land_woodland` high + 30 `green_cover` high. It says of itself that a wood that is a public park is counted twice, by woodland and by public parks | 1: "leafy", high |
| `village_feel` | Village feel | streets_homes | one way | 45 `highstreet_conserved` high + 30 `homes_density` low + 15 `homes_pre1919` high + 10 `conservation_cover` high. A rough guide | 2: "villagey", high |
| `pace` | Going out | pace_food | scale, Calm to Buzzy | 35 `venue_evening_per_homes` high + 30 `venue_food_drink_per_homes` high + 20 `highstreet_access` low + 15 `culture_venues_per_homes` high. The town centre is a distance, read from its near end. The pubs were out of it while the food register was the one source of them, and the recipe was then 45, 30 and 25 | 3: "lively", high |
| `quiet_residential` | Quiet streets | streets_homes | one way | 20 `road_major_exposure` low + 20 `road_traffic_nearby` low + 30 `evening_cluster_exposure` low + 30 `noise_exposure` low. It says of itself that an area with no figure of traffic is placed on its other parts, and is not taken to have none | 4: "quiet street", high |
| `built_age` | Age of buildings | streets_homes | scale, Newer to Historic | 35 `homes_pre1919` high + 25 `conservation_cover` high + 20 `listed_buildings` high + 20 `homes_post2000` low | 5: "period", high |
| `everyday_on_foot` | Everyday on foot | daily_life | one way | 25 `grocery_walk` low + 25 `highstreet_access` low + 20 `station_walk` low + 15 `gp_walk` low + 15 `pharmacy_walk` low. It says of itself, first, that it is mostly a map of how built up a place is, and then that each distance is a straight line, that nothing is known of how large a food shop is or of what it sells, and that a surgery may not take new patients | 6: "walkable", high |
| `parks_close_by` | Parks close by | green | one way | 40 `park_proximity` low + 30 `park_large_proximity` low + 30 `park_facilities` high | 7: "near a big park", high |
| `homes` | Houses or flats | streets_homes | scale, Houses to Flats | 40 `homes_flats` high + 35 `homes_density` high + 25 `private_outdoor_space` low | none |
| `foodie` | Food and drink | pace_food | one way | 40 `venue_food_drink_per_homes` high + 40 `independents_nearby` high + 20 `cuisine_variety` high | none |
| `family_amenities` | Family amenities | daily_life | one way | 40 `school_primary_nearby` high + 35 `play_space_proximity` low + 25 `park_proximity` low | none |
| `works_warehouses` | Works and warehouses | streets_homes | one way | 40 `land_industry` high + 35 `land_storage` high + 25 `land_transport_other` high. Carried only where a release holds no recorded crime | none |
| `well_connected` | Well connected | daily_life | one way | 45 `underground_proximity` low + 20 `overground_proximity` low + 15 `rail_proximity` low + 20 `bus_routes_nearby` high. It says of itself that it counts how near stops are, and nothing of how often anything runs, where it goes or how long a journey takes | none |
| `street_character` | Gritty | streets_homes | scale, Polished to Gritty | 30 `incident_criminal_damage` high + 15 `land_industry` high + 15 `land_storage` high + 15 `incident_antisocial` high + 15 `road_major_exposure` high + 10 `noise_exposure` high | none |
| `family_area` | Family area | who_lives_there | one way | 40 `households_dependent_children` high + 25 `school_primary_nearby` high + 20 `play_space_proximity` low + 15 `park_proximity` low | none |
| `young_professionals` | Young professionals | who_lives_there | one way | 40 `residents_aged_20_34` high + 25 `station_walk` low + 20 `venue_food_drink_per_homes` high + 15 `culture_venues_per_homes` high | none |

**Quiet streets holds the traffic near homes.** Since catalogue version 15. Main roads held 40 in 100 of it, and traffic took half of that and nothing of any other part: both are of the roads near a home. Main roads say how many homes stand within 100 m of a motorway or an A road, and traffic how busy the busiest road within 500 m is, which the class of a road cannot say. So roads are 40 in 100 of the vibe, as they were, and clusters of pubs and bars and transport noise are 30 each. Where an area has no figure of traffic the vibe rests on the other 80, by the rule of every recipe, and its fact says on how many parts. Gritty holds main roads and transport noise, and no traffic: its recipe is as it was decided on 2026-09-24. Village feel is as the founder chose to serve it. The weights are a first judgement, for a person to review.

**Well connected counts how near stops are.** Asked for on 2026-09-24, in place of a journey time that no build holds. The Underground and the DLR count for most, the Overground and the Elizabeth line for less, National Rail and the trams for less again, and the routes of buses for a fifth. The weights are a first judgement, for a person to review. It is no journey time and says so: what it cannot see is said with it wherever it is shown.

**Gritty is one vibe, and it counts recorded crime.** Decided on 2026-09-24 (ADR 0013, as amended). It was built two ways so that both could be judged, and a release carried one. It is now the scale alone, from Polished to Gritty, under the id the scale had when it was called Street character: an id is never renamed. Works and warehouses is a part of it, and is not served beside it: as a vibe of its own it was right at the top and wrong as five bands, because most areas hold no such land and tie in the lowest. Its recipe stays in the catalogue for a release that holds no recorded crime, where it is what gritty is read as.

| Part of Gritty | Hundredths |
|---|---|
| Recorded criminal damage | 30 |
| Works and warehouses: land used for industry, and land used for storage and warehousing | 30, as 15 and 15 |
| Recorded anti-social behaviour | 15 |
| Main roads | 15 |
| Transport noise | 10 |

What is recorded is 45 of its 100 hundredths. Homes per hectare and nitrogen dioxide were parts of the recipe as it was first decided, and were taken out the same day: each says central and built up, and between them they put a smart district at the gritty end. The weights are a first judgement, for a person to review. It holds no figure about residents: no income, employment, health or education.

**Two vibes count who lived somewhere.** Decided on 2026-09-24 (ADR 0006, as amended). Each holds one census figure at 40 in 100, read from its high end, and what is there for the other 60: Burro measures places first. Each runs one way, so a person may ask for more of it or take it off, and nothing asks for less. Its meaning names the census, and what it cannot see begins with who has moved in or out since the census was taken, on 21 March 2021, during a lockdown. `HOLDS_RESIDENTS` names the two. The weights are a first judgement, for a person to review.

| Vibe | What it is, and what it is not |
|---|---|
| Family area | Households with dependent children, with primary schools, a play space and a park nearby. It counts who lived there beside what is there. Family amenities counts places alone: the same schools, play space and park, and nothing of who lives there. They are two vibes and not one, so that a person can ask for what is there without counting who lives there. A word that could mean either, "family friendly", is offered as both, and the person chooses |
| Young professionals | Residents aged 20 to 34, with a station, places to eat and drink and culture nearby. It counts residents by their age alone, and says that it cannot see what anyone does for work. A recipe of residents, flats and homes per hectare was proposed and not built: it found the areas that Houses or flats finds |

`manifest.gritty_variant` says what a release carries, and `tags_of(variant)` gives its vibes.

| Variant | What the release carries | What "gritty" is read as | Where it may be served |
|---|---|---|---|
| `b` | Thirteen: the twelve and Gritty. Works and warehouses is a part of Gritty, and is not carried | A wish for Gritty by name, and so for the recorded crime it counts. A word for works and warehouses, "industrial", is read into Gritty and offered | Any release. It is what the committed release and a release of London carry |
| `a` | Thirteen: the twelve and Works and warehouses. It holds no recorded crime, and no Gritty | Works and warehouses, as assumed, with `street_cleanliness` in `unmet` | Any release. It is built on demand, and no release that is served is one |

An area has a band on Gritty only where 60 in 100 of its recipe is measured, as on any vibe. With no recorded crime held, a release holds 55 at most, and no area has a band.

`checked_recipe()` holds every recipe to its rules when `catalogue.py` is imported, so a recipe that breaks one cannot be served:

| Rule of a recipe | Why |
|---|---|
| Its hundredths sum to 100 | Coverage is a share of the whole |
| It holds two parts or more, each a feature of the catalogue, and none twice | |
| No part carries 60 or more | With the coverage rule, no one measure can decide a vibe alone. For `conservation_cover` this is a condition of the source |
| The parts that rest on the conservation areas carry under 60 together: `conservation_cover` and `highstreet_conserved` (`ON_CONSERVATION_AREAS`) | The condition is of the source, and two measures rest on it. With nothing else known of an area, no vibe places it |
| No part is of `kind` `on_request` | What is weighed only when asked for is in no vibe |
| No part is a measure of `RANKED_AS` | What is shown and never ranked on is in no vibe: a vibe is ranked on what a wish is ranked on |
| No recipe but Gritty's holds a part of dimension `crime`, and no scale but Gritty holds a nuisance | `HOLDS_CRIME` names that one id, `street_character`, and a test holds it to no other |
| A vibe with one way reads a nuisance from its low end | More of the vibe is never more of a nuisance |
| A scale names two ends that differ. A vibe with one way names none | |
| `cannot_see` begins with the line every vibe says first | |
| A part that counts who lives somewhere is read from its high end | To read it low is to rank towards fewer of a group of people |
| No scale holds a part that counts who lives somewhere | The other end of a scale ranks away from what the first end ranks towards |
| Where a recipe holds such a part, no part of it carries more than 40 (`PART_MAX_WHERE_RESIDENTS_COUNT`) | A vibe that counts residents is never one census figure under another name, and what is there is most of it |
| Where a recipe holds such a part, its `meaning` names the census, "Census 2021" | A figure about who lives somewhere says so |
| Where a recipe holds such a part, the vibe holds no `strip` | What a result shows of itself is of the place. A vibe that counts residents is shown on a result where a person asked for it |
| A vibe that is a rough guide says why in one sentence, which core holds (`WHY_A_ROUGH_GUIDE`), and no other vibe has one. It holds no `strip` | What is less sure is never said of an area unasked. It is shown on a result where a person asked for it |

**Village feel is served as a rough guide.** Decided by the founder on 2026-09-25 ([ADR 0013](../adr/0013-vibes-are-the-centre.md), as amended). It was tried three times against the bar the founder had set, that 30 of the 50 areas it puts highest read as villages, and did not reach it. The founder chose to serve it all the same, and that it says it is less sure than the other vibes. Its recipe is the second try's, as it was counted: the high street in a conservation area 45, homes per hectare read from the low end 30, homes built before 1919 15 and conservation cover 10. It holds no part for a small or a compact centre, for independent places, for traffic or for homes per hectare of land that is no park. The high street is 45 in 100 of it, so no area has a band without one, and the two parts that rest on the conservation areas are 55, so they place no area alone.

| What a rough guide is held to | Where |
|---|---|
| It says so wherever it is shown, in sight and not behind a press: one short label, "Rough guide", and one sentence that says why. Core holds both (`ROUGH_GUIDE`, `WHY_A_ROUGH_GUIDE`), route 11 serves them as `rough_guides`, and every client draws them word for word. The sentence gives no figure that a build could make false, and names no place | Sections 8.2 and 9.2 |
| It is never taken without a press of its own. The rules apply it from no word, its own name among them, and offer it with its label and its sentence. One press that adds what needs no choice never takes it. A model's guess of it is no guess | Section 8.2 |
| It is used to work out no other thing. No likeness counts the measure that was made for it, it is on a result only where a person asked for it, and it is in neither list of what an area has most and least of | Sections 6.7 and 7.6 |

The sentence of Village feel is: "Of the areas it puts highest, about half read as villages to people, and it takes some busy main roads and some grand inner streets for villages."

**What it was before.** From 2026-09-24 Village feel placed an area only where `centre_small` or `centre_compact` had a figure: with independent places measured, a build of London held 60 in 100 of its first recipe, and on it Village feel found inner London's old streets and no villages. `PLACED_ONLY_WITH` in `catalogue.py` named the two measures. No build carried either, so no build placed an area on it, and a wish for it was turned away as `not_in_release`. `PLACED_ONLY_WITH` names no vibe now. `tag_raw()` still holds its rule, and a release that places an area on a vibe that is held off is still refused (`raw_matches_recipe`, `held_off_stays_held_off`): name a vibe there, and take one out, only in a change the founder has seen.

**Retired.** Seven tags of version 1 are gone, and an id is never reused: `buzzy` and `evening_venues` are the Buzzy end of `pace`; `historic_character` is the Historic end of `built_age`; the words of `creative`, `strong_high_street`, `near_universities` and `waterside` weigh one feature each (section 8.2). No share outlives a restart and no real release exists, so nothing that is stored names one.

## 4. PreferenceSpec

| Field | Type | Notes |
|---|---|---|
| `schema_version` | `Literal[1]` | |
| `tenure` | `Tenure` | `rent` or `buy` |
| `budget` | `Budget` | `amount` (int, or `None` for not stated), `segment` (must suit the tenure), `strictness` (`soft`, `hard`), `weight`, `provenance` |
| `commutes` | tuple of `Commute` | At most 3, and at most one for a place, kept in `place_id` order. `place_id`, `mode` (`pt`, `cycle`, `walk`), `max_minutes` (10 to 120), `strictness`, `provenance` |
| `commute_combine` | `Combine` | `slowest` or `mean` |
| `pt_basis` | `PtBasis` | `typical` or `just_missed`: which public transport time is scored |
| `commute_weight` | float | |
| `weights` | tuple of `FeatureWeight` | At most one for a feature, kept in `feature_id` order. A feature with no entry has weight 0, and so has one with an entry of 0, which records that a person took it off (section 5.1). `feature_id`, `weight`, `direction` (`more`, `less`), `provenance` |
| `tags` | tuple of `TagWeight` | At most one for a vibe, kept in `tag_id` order. `tag_id`, `weight`, `toward` (`high`, `low`), `provenance`. `toward` is the end of a scale that is asked for, and is `high` for a vibe with one way. A spec never holds both ends of one scale |
| `areas` | tuple of `AreaRule` | At most one for an area, kept in `area_id` order. `area_id`, `rule` (`exclude`, `only`), `provenance` |
| `tenure_from`, `commute_combine_from`, `pt_basis_from`, `commute_weight_from` | `Provenance` | Provenance of the four settings that are not records |

`Provenance` is `stated` (the user said it), `inferred` (the interpreter read it into looser words), `default` (nobody chose it) or `ui_edit` (changed with a control). Every weight is snapped on construction, and the four tuples are sorted on construction, so that nothing downstream depends on the order edits arrived in. A repeated place, feature, tag or area is refused on construction, and so is a weight outside 0 to 1: a weight inside the range is snapped, one outside it is not clamped. The spec holds ids and numbers only: no free text, and no place name.

Construction checks each field alone. What depends on another field, the catalogue or the release is left to `check_spec`, which reports it with a path.

`check_spec(spec, release) -> tuple[SpecProblem, ...]` checks what only a release can decide. A `SpecProblem` is a `path` into the spec, such as `commutes[0].place_id`, and a `problem`, which is one of `unknown_place`, `unknown_area`, `segment_not_for_tenure`, `direction_not_allowed`, `not_in_release` and `out_of_range`. A vibe the release does not carry is `not_in_release` at `tags[i].tag_id`, and so is one it carries and places no area on. A budget that is in order, where the release holds no cost of that kind of home for any area, is `not_in_release` at `budget.amount`, whatever the budget counts for: `Release.costed(tenure, segment)` says whether it holds one. The low end of a vibe with one way is `direction_not_allowed` at `tags[i].toward`. The last is a `max_minutes` above the release's cutoff for the mode (section 6.1), or a `budget.amount` outside the limits of 5.2, which a spec from the wire can hold. `check_spec` ignores what `canonical()` drops, a weight of 0 and a budget with no amount, so that two specs with one canonical form are always treated alike. `rank()` raises `SpecError` if it is not empty.

A position in a `path` is a position in the spec as it is kept, which is in id order, and that is the order every response returns a spec in. It is not the position in the body that was sent: a spec sorts its four tuples on construction and does not keep the order they arrived in. A client that sends `commutes` out of id order and is told of `commutes[2]` finds the element by sorting what it sent by `place_id`, or by looking at position 2 of any spec the service has returned to it. Where a route takes edits with the spec, routes 1 and 2, it is the spec as the edits leave it that is checked, so a position is one in that spec (section 9.4).

`LIMITS` holds the numbers of section 5.2. Route 11 serves them, with the cutoffs of the loaded release, so that a form never offers a value the reducer would refuse.

### 4.1 Defaults

`default_spec(tenure)` returns one of these. Every provenance is `default`. Each weight takes the direction its polarity gives.

| Field | Renter | Buyer |
|---|---|---|
| `tenure` | `rent` | `buy` |
| `budget` | amount `None`, `bed_1`, `soft`, weight 0.30 | amount `None`, `flat`, `soft`, weight 0.30 |
| `commutes`, `tags`, `areas` | none | none |
| `commute_combine`, `pt_basis`, `commute_weight` | `slowest`, `typical`, 0.40 | the same |
| `weights` | `station_walk` 0.50, `station_lines` 0.30, `park_proximity` 0.30, `highstreet_access` 0.30, `noise_exposure` 0.20, `air_no2` 0.20 | `station_walk` 0.40, `park_proximity` 0.40, `green_cover` 0.30, `highstreet_access` 0.30, `noise_exposure` 0.30, `station_lines` 0.20, `air_no2` 0.20 |

A commute added without detail gets mode `pt`, 45 minutes, `soft`.

These are the weights of a search in which nothing has yet been said. Nobody chose them, so they give way the first time a wish is applied (section 5.3, rule 11). Each becomes a quarter of what it was, rounded down to a whole step and never less than one step:

| Given way | Renter | Buyer |
|---|---|---|
| `weights` | `station_walk` 0.10, `station_lines` 0.05, `park_proximity` 0.05, `highstreet_access` 0.05, `noise_exposure` 0.05, `air_no2` 0.05, which is 0.35 in all against 1.80 | `station_walk` 0.10, `park_proximity` 0.10, `green_cover` 0.05, `highstreet_access` 0.05, `noise_exposure` 0.05, `station_lines` 0.05, `air_no2` 0.05, which is 0.45 in all against 2.10 |
| `budget.weight`, `commute_weight` | 0.30 and 0.40, as before. They are not scaled | the same |

One thing said is worth 0.50 (section 5.2), so it outweighs all that was left unsaid, for a renter and for a buyer. That is what the quarter is for, and it is why the quarter is rounded down. To the nearest step a quarter of a renter's defaults comes to 0.55 and of a buyer's to 0.60, as a third does, and one mention would not outweigh either. It is counted in whole steps of 0.05, `steps // 4`, so that no float decides which step 0.075 is nearer to.

**What is said of the place leads.** Decided on 2026-09-24. A journey weighed 1.00 and a budget 0.80, against 0.50 for each thing said of the place, so one journey and one budget outweighed three things said. A journey now weighs 0.40 and a budget 0.30 until a person moves them. So each thing said of the place weighs more than a journey and more than a budget, two things said outweigh the two together, and the two together still outweigh all that was left unsaid, which is 0.35 for a renter and 0.45 for a buyer. A person may make either count for more, in the settings, and it stays where they put it. A limit that is firm is a filter and no weight: "at most 35 minutes" leaves out what is over, whatever a journey weighs. A limit that is flexible is a weight and no filter, so an area that is over it can still stand high where it does well on what was said of the place, and its card says what it gives up.

`DEFAULT_WEIGHTS`, `DEFAULT_COMMUTE_WEIGHT`, `DEFAULT_BUDGET_WEIGHT`, `given_way()`, `MENTION_WEIGHT` and `GIVE_WAY_TO_ONE_IN` in `spec.py` hold these numbers.

### 4.2 Canonical form and hash

`canonical(spec) -> str` is the form used for hashing, caching and comparing. Two specs with the same canonical form rank the same. The reverse is not promised: the rules below fold together only the differences that plainly cannot matter.

1. Drop every provenance field.
2. Write each weight as its whole number of 0.05 steps, 0 to 20.
3. Drop any feature or tag whose weight is 0 steps.
4. If `budget.amount` is `None`, write `"budget": null`.
5. If there are no commutes, omit `commute_combine`, `pt_basis` and `commute_weight`.
6. Sort `commutes` by `place_id`, `weights` by `feature_id`, `tags` by `tag_id`, `areas` by `area_id`.
7. Write a vibe's `toward` only where it is `low`. So every spec of version 1 has the canonical form and the hash it had.
8. Serialise with `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.

`spec_hash(spec) = sha256(canonical(spec).encode("utf-8")).hexdigest()`, 64 lower-case hex characters.

Test vectors. The spec of the worked example in section 6.8:

```
{"areas":[],"budget":{"amount":1800,"segment":"bed_1","strictness":"soft","weight":16},"commute_combine":"slowest","commute_weight":20,"commutes":[{"max_minutes":40,"mode":"pt","place_id":"syn-p0001","strictness":"soft"},{"max_minutes":30,"mode":"pt","place_id":"syn-p0002","strictness":"hard"}],"pt_basis":"typical","schema_version":1,"tags":[{"tag_id":"leafy","weight":8}],"tenure":"rent","weights":[{"direction":"less","feature_id":"noise_exposure","weight":6},{"direction":"less","feature_id":"park_proximity","weight":10}]}
```

hashes to `bba9532c96393ce23be1d607aafa73d377e90885ad493868da0f51bff4d0dd6b`. A renter spec with nothing set, `{"areas":[],"budget":null,"commutes":[],"schema_version":1,"tags":[],"tenure":"rent","weights":[]}`, hashes to `879be1ff788f9463f2dc60271c9190fdd35ea3df7522cce631dbde9ce8089a6b`.

## 5. Operations and the reducer

### 5.1 The edits

Sliders, chips and chat all produce `Operations`. It is six arrays, each of one type. Every field of every item is required, and all six arrays are always present, empty when unused. There are no unions and no optional fields, because the model's structured output cannot express them well. A field that an edit has nothing to say in carries its sentinel: `unchanged`, `none`, `default`, `0` or `0.0`.

| Array | Item | Fields, in order |
|---|---|---|
| `budget_ops` | `BudgetEdit` | `action` (`set`, `clear`, `nudge`); `tenure` (`rent`, `buy`, `unchanged`); `amount` (int, `0` for not given); `segment` (a segment, or `unchanged`); `strictness` (`soft`, `hard`, `unchanged`); `step`; `provenance` |
| `commute_ops` | `CommuteEdit` | `action` (`add`, `update`, `remove`); `place_id`; `mode` (`pt`, `cycle`, `walk`, `unchanged`); `max_minutes` (int, `0` for not given); `strictness` (`soft`, `hard`, `unchanged`); `step`, which moves `max_minutes`; `provenance` |
| `weight_ops` | `WeightEdit` | `action` (`set`, `nudge`, `remove`); `feature_id`; `value` (float, read by `set`); `step` (read by `nudge`); `direction` (`more`, `less`, `default`); `provenance` |
| `tag_ops` | `TagEdit` | `action` (`set`, `nudge`, `remove`); `tag_id`; `value` (float, read by `set`); `step` (read by `nudge`); `toward` (`high`, `low`, `default`); `provenance` |
| `area_ops` | `AreaEdit` | `action` (`exclude`, `only`, `clear`); `area_id`; `provenance` |
| `setting_ops` | `SettingEdit` | `action` (`set`, `nudge`); `setting` (`commute_combine`, `pt_basis`, `commute_weight`, `budget_weight`); `choice` (`slowest`, `mean`, `typical`, `just_missed`, `none`); `value` (float, read when setting a weight); `step`; `provenance` |

`step` is one of `none`, `up_small`, `up_large`, `down_small`, `down_large`. `provenance` on an edit is `stated`, `inferred` or `ui_edit`. Enum values are lower-cased before validation, because structured output may change their case. An edit never carries text: a destination or an area named in words is resolved to an id before it becomes an edit (section 8.3). `place_id` and `area_id` are plain strings here, so that an id the release does not know, the empty string included, is a rejected edit and not a validation error.

Which fields an action reads. A field it does not read is ignored, whatever it holds.

| Edit | Action | Reads | Does |
|---|---|---|---|
| `BudgetEdit` | `set` | `tenure`, `amount`, `segment`, `strictness` | Writes each that is not `unchanged` or `0` |
| | `nudge` | `step` | Moves `amount` by the step |
| | `clear` | | Sets `amount` to `None` and touches nothing else |
| `CommuteEdit` | `add` | `place_id`, `mode`, `max_minutes`, `strictness` | Adds the commute. `unchanged` and `0` take the defaults of 4.1 |
| | `update` | `place_id`, `mode`, `max_minutes`, `strictness`, `step` | Writes each that is not `unchanged` or `0`. `step` is read only when `max_minutes` is `0` |
| | `remove` | `place_id` | Removes the commute |
| `WeightEdit` | `set` | `feature_id`, `value`, `direction` | Sets the weight to `value`, which is always read: `0.0` means zero |
| | `nudge` | `feature_id`, `step`, `direction` | Moves the weight by the step |
| | `remove` | `feature_id` | Removes the entry, which is weight 0 |
| `TagEdit` | | | As `WeightEdit`, with `toward` in the place of `direction`: the end of a scale the edit is for |
| `AreaEdit` | `exclude`, `only` | `area_id` | Writes the rule |
| | `clear` | `area_id` | Removes the rule |
| `SettingEdit` | `set` | `setting`, and `choice` for `commute_combine` and `pt_basis`, `value` for the two weights | Writes it. `value` is always read: `0.0` means zero |
| | `nudge` | `setting`, `step` | Moves one of the two weights by the step |

`direction: default` means "as it is": it leaves the direction of a weight already in the spec alone. For a weight that is not yet in the spec it is the direction the polarity gives, and `more` where the polarity is `either`. `toward: default` is the same for a vibe: the end the spec holds, and `high` where it holds none.

A feature or tag weight that reaches 0, by any action, counts for nothing, and a slider and a sentence that both say "ignore this" reach the same canonical spec. A tag is removed from the spec, and so is a feature that no tenure weighs by default. A feature that some tenure does weigh by default leaves an entry behind, with weight 0 and the provenance of the edit that took it off, so that a change of tenure does not bring the default back (section 5.3 rule 5). `canonical()`, `check_spec()` and `rank()` pass over an entry of 0 as they pass over no entry, so the hash and the ranking are the same either way. Taking off what is not in the spec leaves nothing behind and changes nothing. Named again, a thing that was taken off is worth what any mention is.

### 5.2 Bounded steps

A relative request never sets a number of its own choosing. It becomes a step.

| Target | Small | Large | Kept within | Rounded to |
|---|---|---|---|---|
| Any weight | 0.10 | 0.25 | 0 to 1 | 0.05 |
| Budget, rent | 5% | 15% | 300 to 20,000 | 25 |
| Budget, buy | 5% | 15% | 50,000 to 20,000,000 | 5,000 |
| Commute `max_minutes` | 5 | 15 | 10 to 120, and never above the release's cutoff for the mode | 1 |

A step is worked out, rounded to its unit, moved on to the next unit if rounding left it where it started, and then clamped to its limits. So a step always moves the number unless it is already at a limit, and a step never fails for being too big. A number given outright is different: a `set`, an `add` or an `update` that names a number outside the limits is rejected as `out_of_range`, because a person or a model asked for that number and should be told.

"More", "a bit", "slightly" and "somewhat" become a small step. So do "fairly", "quite", "pretty", "reasonably" and "relatively", which say how much a thing is wanted and never whether (section 8.2). "Much", "a lot", "really", "very" and "way more" become a large one. "Less" and "fewer" are words that turn (section 8.2). "Far" is no word of the rule-based reader's, so "far more parks" is left unread by it. "Essential", "most important" and "must have" become `set` to 1.00. "Don't care about", "ignore", "not bothered", "remove" and "get rid of" become `remove`. A weight that is absent counts as 0 when nudged. Nudging a budget with no amount is rejected.

A feature or a tag that is simply named, with no word of degree, is a `nudge` of `up_large`: "leafy" and "near a park" are wishes, and the interpreters never pick a number. Both interpreters follow this rule, the model by its instructions.

**What a mention is worth.** A step up from a weight that nobody has chosen, one that is absent, is still at its default provenance or was taken off, leaves it at `MENTION_WEIGHT`, 0.50, if the step alone would leave it lower. So "leafy" is worth 0.50. So is "more pubs" on a first prompt, where a small step alone would be 0.10: a relative wish for something with no weight yet counts as much as naming it. And so is "near a park", though a park has a default of its own, because a default is nobody's choice. A step up from a weight the person chose is a step and no more: 0.50 and a large step is 0.75. This is the reducer's rule and not the interpreter's, so a chip that sends a `nudge` is worth what a word is.

A budget or a journey time is `soft` unless the words make it a limit. Decided on 2026-09-24: "max", "up to", "at most" and "no more than" make a budget `hard`, and "at most", "max", "no more than" and "within" make a number of minutes `hard`. A range of minutes, "35-40min", is `hard` at its longer end. So are "absolute maximum", "cannot go over" and the like, as they were. With none of these a number stays `soft`: "under", "below", "less than", "around", "maximum" and "tops" leave it a guide, "up to" makes no journey firm, and "within" makes no budget firm. The lists are `FIRM_OF_MONEY` and `FIRM_OF_MINUTES` in `vocabulary.py`. Read as a guide, "max £400k" put first an area where the middle home sold for far more.

### 5.3 The reducer

```python
def apply(spec: PreferenceSpec, ops: Operations, release: Release) -> ReducerResult: ...
```

`ReducerResult` holds `spec`, `applied` (each with `group`, `index`, `changed`) and `rejected` (each with `group`, `index`, `reason`).

1. It is pure and total. The same inputs give the same output, and a well-typed input never raises.
2. Groups are applied in the order budget, commute, weight, tag, area, setting, and within a group in array order. A later edit wins.
3. A bad edit is rejected and the rest are applied. Nothing is half-applied.
4. Each action reads the fields the table in 5.1 gives it, and no others.
5. Changing tenure clears `budget.amount` and sets `segment` to the new tenure's default, unless the same edit supplies them: a rent is not a price, and no segment suits both. It also resets every setting that is still at its default provenance to the new tenure's default: the weights and tags, the budget's strictness and weight, and `commute_combine`, `pt_basis` and `commute_weight`. Anything the person set is kept. A default the release cannot rank is left out, as it is from a default that is served (section 9.4). Commutes and area rules are never defaults, so they are never touched. A weight the person took off has left an entry of 0 behind (section 5.1), which is theirs, so the new tenure's default for it does not come back. What was never in the spec was never taken off: a renter who asks for no green space, which a renter's default does not weigh, has taken nothing off, and a buyer's default for it comes with the switch.
6. `add` on a place already in the spec is an `update`, and one that asks for nothing new is `applied` with `changed` false. A fourth commute is rejected. Changing a commute's mode brings its cap within the new mode's cutoff instead of rejecting the edit. A commute or an area rule already in the spec can always be removed, even if the release no longer knows the id, so a stale spec can be put right. The routes that take edits apply them before they check the spec, so that this can be reached over HTTP (section 9.4).
7. A direction against a fixed polarity is rejected. `default` never is. So is `toward: low` for a vibe with one way. An edit that names a vibe the release does not carry is rejected as `not_in_release`.
8. An `inferred` edit that would leave a crime feature with a weight above 0 is rejected. Crime is weighted only when the user asks for it or moves its control. A vibe whose recipe holds recorded crime (`HOLDS_CRIME`, which is `street_character` alone) is held to the same rule: an `inferred` edit that would leave it with a weight above 0, towards either end, is rejected as `crime_needs_explicit_request`.
9. `exclude` and `only` replace each other for the same area. With any `only` rule present, every area without one is filtered.
10. The setting an edit touches takes the edit's provenance. An edit that is in order but leaves the spec as it was, such as a step at its limit or a `remove` of a weight that is not there, is `applied` with `changed` false and leaves provenance alone. A `set` of a weight or a tag that is still at its default provenance is the one exception: it always takes the edit's provenance, because a slider moved to the very number the default gave has still been moved.
11. **What is said outweighs what is not.** Every edit is applied to the spec with its defaults given way: each feature weight whose provenance is `default` is put at a quarter of the value `default_spec` gives it for the spec's tenure, rounded down to a step (section 4.1). If the edit changes anything, that is the new spec. If it is rejected, or changes nothing, the spec stays exactly as it was, defaults and all. So the first wish that is applied, from words or from a control and of whatever kind, makes the defaults give way; they do it once, because a quarter of a default is the same however often it is worked out; and a step from a default starts from where it gave way to, so that "care less about parks" takes a renter's park weight from 0.05 to nothing and not from 0.30 to 0.20. The budget's weight and the commute's are not scaled. A weight at default provenance for which the tenure has no default, which only a spec from the wire can hold, has nothing to give way to and is left as it is. So is a tag: no default holds a tag today, so none has a default to give way to.
12. A step up from a weight nobody chose is worth a mention at least (section 5.2).
13. **A scale holds one end.** A step or a `set` towards the end the spec does not hold turns the vibe: it starts from nothing, so a step up is worth a mention, and the spec then holds that end. A step down towards an end the spec does not hold has nothing to lower, and is rejected as `nothing_to_change`.
14. **To name the tenure is to choose it.** A `BudgetEdit` with `action` `set` and a `tenure` other than `unchanged`, that is applied, sets `tenure_from` to the edit's provenance, whether or not the tenure moves. Where that is all it changes, `changed` is true, the defaults do not give way, and `spec_hash` does not move, since a provenance is no part of it.
15. **What the release holds for no area cannot be asked for.** An edit is rejected as `not_in_release` where it would weigh a vibe that no area has a band for, where it would leave the spec with a budget and the release holds no cost of that kind of home for any area, and where it adds a journey and the release names no place at all. Each would count in every area and be known in none: on the first real build a budget that was offered and accepted left no area of 1,002 ranked, and so did eight of the eleven vibes. What is said of the home with no amount is applied as ever: to rent or to buy, and the kind of home. A thing that is in the spec already can always be taken off. Where the release names places and not the one that was asked for, the edit is `unknown_place`, as before. Where a release holds a thing for some areas and not for others, nothing changes: it is dropped for the area that lacks it (section 6.6).

Rules 11 to 13 change the spec, so its hash changes with it, and `rank()` is as it was: a pure function of the spec and the release. A spec that is ranked without any edit, a default among them, is ranked as it stands.

**Worked example.** A renter's first prompt is "leafy and quiet, near a park". The interpreter makes three edits, each a `nudge` of `up_large`: `feature:park_proximity`, `tag:leafy`, `tag:quiet_residential`.

| | Before | After |
|---|---|---|
| `station_walk`, `station_lines`, `highstreet_access`, `noise_exposure`, `air_no2` | 0.50, 0.30, 0.30, 0.20, 0.20, all `default` | 0.10, 0.05, 0.05, 0.05, 0.05, all still `default` |
| `park_proximity` | 0.30, `default` | 0.50, `stated`. It gave way to 0.05, a large step made that 0.30, and a mention is worth 0.50 |
| `leafy`, `quiet_residential` | no entry | 0.50 and 0.50, `stated` |
| Said, against unsaid | 0 against 1.80 | 1.50 against 0.30 |

Had the prompt been "near a park" and no more, the last row would read 0.50 against 0.30. Had it been "leafy", 0.50 against 0.35.

`RejectReason` is one of `unknown_place`, `unknown_area`, `not_in_release` (the release does not rank that feature, or holds the thing for no area: rule 15), `too_many_commutes`, `no_such_commute` (an `update` or `remove` on a place not in the spec), `out_of_range` (a number given outright that is outside the limits of 5.2), `segment_not_for_tenure`, `direction_not_allowed` (rule 7), `crime_needs_explicit_request` (rule 8), `mismatched_choice` (a `choice` that does not belong to the `setting`, or a `nudge` of a setting that is not a weight) and `nothing_to_change` (the edit asks for nothing: a budget `set` or a commute `update` whose every field is a sentinel, a `nudge` whose step is `none`, or a `nudge` of a budget with no amount).

## 6. Ranking

```python
def rank(spec: PreferenceSpec, release: Release) -> RankResult: ...
```

The plan writes this as `rank(spec, release_id, engine_version)`. In code the release is passed as an object and the engine version is the constant; the result records both. It does no IO, reads no clock, and gives the same answer on every call.

### 6.1 Hard filters

Applied in this order. An area stops at the first that catches it.

| Reason | Catches |
|---|---|
| `not_rankable` | `rankable` is false. Reported under `unranked`, not `filtered` |
| `excluded` | An `exclude` rule names it |
| `not_selected` | There are `only` rules and none names it |
| `over_budget` | Budget is `hard`, an estimate exists, and it is over the budget: the upper quartile of a range is over `amount`, or the median of a cost with no range is over it by more than `FIRM_BUDGET_MARGIN_PERCENT` in 100, which is 25 (section 6.5) |
| `commute_cap` | A commute is `hard` and its time is over `max_minutes` or beyond the cutoff |
| `commute_likely_beyond` | A commute is `hard`, the release holds no time for it, and it is estimated to be likely beyond `max_minutes` (section 6.10). What is borderline is never left out |

A hard filter removes only an area known to fail. An area with no estimate or no travel time cannot be tested: it stays, the component is dropped from its score, and the filter is listed under `untested_filters`.

`beyond_cutoff` is known to fail, and that is why `max_minutes` may not be above the release's cutoff for the mode: with a cap of 100 and a cutoff of 90, a journey beyond the cutoff might be 95 minutes and inside the cap, and the filter would remove an area it could not test.

### 6.2 Components

The score is a weighted mean of utilities, each between 0 and 1. A component that is not requested appears nowhere in the result and counts towards nothing. Hard filters apply whatever the weights.

| Component | Requested when | Weight `W` | Utility `U` | Missing, for one area, when |
|---|---|---|---|---|
| `commute` | There is a commute and `commute_weight > 0` | `commute_weight` | 6.3 and 6.4, and 6.10 for a journey that is estimated | No destination has a time or an estimate |
| `budget` | `amount` is set and `budget.weight > 0` | `budget.weight` | 6.5 | There is no estimate |
| `feature:<id>` | Its weight is above 0 | its weight | `p / 100` if direction is `more`, else `1 - p / 100` | `percentile` is null |
| `tag:<id>` | Its weight is above 0 | its weight | `score / 100` towards the high end, `1 - score / 100` towards the low end | `score` is null |

The same spec with the end of a scale turned reverses the order on that vibe alone. `tag_utility()` is the one place it is worked out. The band and the spread of a vibe are for showing, and change no rank.

### 6.3 The commute decay curve

For one destination, `t` is the travel time in minutes and `M` the commute's `max_minutes`. With `pt`, `t` is `pt_typical` or `pt_just_missed` as `pt_basis` says.

```
FULL_UNTIL_MIN   = 15     a journey this short is as good as any shorter
FULL_UNTIL_SHARE = 0.5    unless that is more than half the cap
UTILITY_AT_CAP   = 0.5    a journey exactly at the cap is half as good as a short one
ZERO_AT_SHARE    = 1.5    a journey half as long again as the cap is worth nothing

a = min(FULL_UNTIL_MIN, FULL_UNTIL_SHARE * M)        z = ZERO_AT_SHARE * M

u(t) = 1                                                if t <= a
     = 1 - (1 - UTILITY_AT_CAP) * (t - a) / (M - a)     if a < t <= M
     = UTILITY_AT_CAP * (z - t) / (z - M)               if M < t < z
     = 0                                                if t >= z, or status is beyond_cutoff
```

With `M = 40`: 15 minutes gives 1.00, 32 gives 0.66, 40 gives 0.50, 44 gives 0.40, 60 gives 0.

A journey beyond the cutoff scores 0, though the curve does not reach 0 until `z`. Where the cutoff is below `z` this marks down a journey a little over the cap harder than the curve would. It is the honest reading of what the release holds, which is only that the journey is longer than the cutoff.

### 6.4 Several destinations

`slowest`, the default, takes the `min` of the destinations' utilities: the worst journey, measured against what each person will put up with. `mean` takes their arithmetic mean.

**The journeys are scored on the legs that have a time.** With `slowest` it is the leg that does worst against its limit, among those that have a time. With `mean` it is the mean of those. A leg with no time is left out of that and is said to be missing, by a fact and a sentence of its own (section 7.3). The component is missing for an area only when no leg has a time. So an area that is far from one workplace is never lifted because the time to another is not known: until 1.4.0 one missing leg took the whole of the journeys out of the fit, and an area 63 minutes from a place with a limit of 35 came first. A firm limit on a journey with no time is still listed under `untested_filters`.

### 6.5 Budget fit

The budget is tested against the upper quartile, because published rents understate what a new tenant pays. With `B` the amount and `Q3` the upper quartile for the spec's tenure and segment:

```
BUDGET_OVER_SHARE = 0.25
U      = clamp(1 - (Q3 - B) / (BUDGET_OVER_SHARE * B), 0, 1)
margin = B - Q3
```

So `U` is 1 when `Q3 <= B`, and falls in a straight line to 0 when `Q3` is a quarter over. Being further under budget earns nothing: Burro gives no affordability verdict. The confidence tier is reported and changes no arithmetic.

**Where a cost has no range, the budget is held against its median.** `budget_held_against(estimate)` is the upper quartile of a range and the median of one number, and `Q3` above is what it gives. The median is held as it is written. It is never raised to stand for a quartile, and never scaled to a size of home: a buyer who names a one-bedroom flat is held against the median of flats of all sizes, and the sentence beside the figure says so (section 7.3). `BudgetFit.upper_quartile` is then `null`, and `margin` is `B` less the median.

**A rent of a wider place is held on its median too.** Decided on 2026-09-25. Such a row holds both quartiles, as its publisher gives them, and they are shown. They are of a district or a borough and not of the area, so no limit is held against the upper one: `held_on_the_median(estimate)` is true of one number and of a rent of a wider place, and `budget_held_against` gives the median for both. `BudgetFit.upper_quartile` is then `null`, and `margin` is `B` less the median.

**A firm budget leaves an area out on a median only where the median is far over it.** Decided on 2026-09-24. About half of the homes behind a median sold for less than it. So an area whose median is a little over a budget is one where many homes sold within it, and a firm budget that left it out on the median left out places a person could buy in: held so, a firm £400,000 for a flat left out every area of two inner boroughs, in each of which flats sold for less. `over_a_firm_budget(estimate, amount)` is the one rule:

```
FIRM_BUDGET_MARGIN_PERCENT = 25
a range:       left out where  Q3 > B
one number:    left out where  100 * median > (100 + FIRM_BUDGET_MARGIN_PERCENT) * B
a rent of a wider place:  as one number
```

It is counted in whole pounds, so that no float decides which side of the line an area falls. The margin is written in that one place, and is a first figure for the founder to change. Three things stand behind a quarter:

| Why a quarter | |
|---|---|
| What sold within the budget | Of the flats sold in London from 2023 to 2025, against a budget of £400,000: where an area's median stood at the budget about half had sold within it, where it stood a quarter over about a quarter had, and beyond that fewer |
| What a flexible budget does | A quarter over is where a flexible budget counts an area for nothing (`BUDGET_OVER_SHARE`). So a firm budget leaves out what a flexible one gives no credit to, and no more |
| The size of a home | A person who names a size is held against homes of every size, of which the smaller sold for less than the middle |

An area that the margin keeps is ranked lower for its price, as a flexible budget ranks it, and never as if it were within the budget: `U` falls from 1 at the budget to 0 at a quarter over. Its `budget_fit` fact says how far over the median is, and that about half of the homes sold for less (section 7.3). A range is held against its upper quartile as it was, with no margin.

An area with no figure for the kind of home is not left out by a budget and is not ranked as if it were cheap. It stays, the budget is dropped from its score, the filter is listed under `untested_filters`, and a `missing` fact says that there is no cost figure (section 6.4). It is ranked on the rest of what was asked, where that is at least half of the weight. Where the budget is more than half, the area falls under the floor of section 6.6: it is not ranked, it is reported under `unranked` with `insufficient_data`, and `missing` names the budget. It is never reported as `over_budget`.

### 6.6 Missing data, the score and the order

For one area, `R` is the set of requested components and `P` the ones that are present.

```
weight_coverage = sum(W_k for k in P) / sum(W_k for k in R)
share_k         = W_k / sum(W_j for j in P)
contribution_k  = share_k * U_k
loss_k          = share_k * (1 - U_k)
S               = sum(contribution_k for k in P)
score           = round(100 * S, 2)
```

- A missing component is dropped for that area and the remaining weights are rebalanced. Nothing is imputed.
- **What no area has a figure for is never a component.** A spec that requests a vibe no area is placed on, or a budget the release holds no cost for, is refused by `check_spec` before anything is scored (section 4), and an edit that asks for one is rejected (section 5.3, rule 15). What follows is of a thing the release holds for some areas and not for others.
- `MIN_WEIGHT_COVERAGE = 0.5`. Below it the area is not scored and is reported under `unranked` with reason `insufficient_data`. An area with nothing present has coverage 0, so it is never scored and nothing is divided by zero.
- **The character that counts is covered on its own.** The character of a search is every feature and every vibe it requests: all of `R` but `commute` and `budget`. `MIN_CHARACTER_COVERAGE = 0.5`. An area with a figure for under half of it, by weight, is not scored, whatever is known of its journeys and its cost. It is reported under `unranked` with reason `character_unknown`. A journey counts 1.00 and a budget 0.80, so together they are over half of almost any search, and an area with a journey time and a rent passed the floor above with no figure for anything that was asked of the place itself. Until 1.5.0 such an area came first for a person who asked for leafy, quiet and a pub. Where a search requests no feature and no vibe, nothing was asked of the place, and the rule does not apply. It is counted in whole steps, as the floor above is, and the floor above is tested first.
- **Character is every feature and vibe of the spec, whoever chose it.** A default counts as what was said does. Two specs with one canonical form rank the same (section 4.2), and a canonical form holds no provenance, so who chose a weight can never decide whether an area is ranked. What is said outweighs what is not (section 5.3, rule 11), so an area with no figure for the one thing a person asked for has under half of the character, whatever it holds of the defaults.
- **An area with no figure for what was asked stands below every area that has one.** Decided on 2026-09-24. Its fit leaves the thing out and is worked out on the rest, so it says nothing of the thing: such an area came first for a person who had asked for that very thing. It is ranked all the same. It is never left out for it, and never scored as nought. What was asked is every component but a usual setting: `asked_for(spec)` in `rank.py`. A usual setting is a feature the tenure weighs by default (section 4.1) that stands the way its default runs, at the weight of the default or at what that gives way to (section 5.3). It is told by its weight and never by who set it, because two specs with one canonical form rank the same. A journey, a budget and a vibe are always asked for. A usual setting with no figure moves no area: its weight is shared out among the rest, as before.
- **What is dropped is said.** An area that is ranked with a component missing names it: the `Contribution` has `present` false and cites its `missing` fact, the explanation holds one sentence for it (section 7.5), and `counted` and `present` say how many things count and for how many the area has a figure. An area that is not ranked names every component it lacks in `Unranked.missing`. The weight of what is missing is shared among what is present, and no surface may show the fit without saying so.
- Whether an area is below it is decided in whole steps of 0.05, as `canonical()` counts a weight, and never by the float: the area is unranked when twice the steps that are present are fewer than the steps requested. With exactly half present an area is ranked, however the weight is split. In floats, 0.3 and 0.6 present of 1.8 requested come to 0.49999999999999994, and that must not be left to decide which side of the line an area falls, as it must not for a tag (section 3.2). The float is what is reported as `weight_coverage`, and nothing else.
- If nothing is requested, every area that passes the filters is ranked with score 0, `weight_coverage` 1 and no contributions, the order is by `area_id`, and `empty_spec` is true.
- Sums run over components in the order `commute`, `budget`, features by id, vibes by id, so the floating-point result is the same everywhere.
- **Order and ties.** First the areas with a figure for all that was asked, and then the areas with none for some of it. Within each, sort by `round(S, 9)` from high to low, then by `area_id` from low to high. `rank` is the 1-based position. Areas with equal rounded `S` get different ranks; the id decides. So `score` does not fall all the way down a result: it falls to the last area that has every figure, and falls again from there.

### 6.7 The result

| Type | Fields |
|---|---|
| `RankResult` | `spec_hash`, `release_id`, `engine_version`, `synthetic`, `empty_spec`, `ranked` (tuple of `RankedArea`, in rank order), `filtered` (a tuple of `area_id` and `reason`, by `area_id`) and `unranked` (a tuple of `Unranked`, by `area_id`) |
| `Unranked` | `area_id`, `reason` (`not_rankable`, `insufficient_data` or `character_unknown`), `missing` (every component the spec requests that the area has no figure for, as `Contribution.component` names them, in the order the sums run. Empty for `not_rankable`: the area was never scored) |
| `RankedArea` | `area_id`, `rank`, `score` (0 to 100, 2 decimals), `weight_coverage` (0 to 1), `contributions` (every requested component, largest contribution first, then by name), `legs` (in `place_id` order, as the spec keeps them), `budget` (`BudgetFit` or `None`), `untested_filters`, `strip` (tuple of `StripMark`) |
| `StripMark` | `tag_id`, `band`, `spread_low`, `spread_high`, `asked` (the vibe is in the spec), `toward` (the end asked for, or `None`), `fact_id` (the `tag` fact that holds the sentence, the sources and the date) |
| `Contribution` | `component` (`commute`, `budget`, `feature:<id>` or `tag:<id>`), `present`, `weight` (as requested), `share`, `utility` (`None` when missing), `contribution`, `loss`, `fact_ids`. `share`, `contribution` and `loss` are 0 when missing, which is what they are: a dropped component has no share |
| `CommuteLeg` | `place_id`, `mode`, `status` (of the time that was scored), `minutes` (the time that was scored), `minutes_typical`, `minutes_just_missed`, `utility`, `estimate`. Each of the three times is `None` unless that time is `ok`. By bike and on foot all three hold the one time there is. `utility` is `None` when `status` is `missing`, and also when the component was not requested. `estimate` is the band of a journey whose `status` is `estimated`: `likely_within`, `borderline` or `likely_beyond`. It is `None` for every other journey, and a journey that is estimated holds no minutes |
| `BudgetFit` | `upper_quartile` (`None` where the cost has no range, and where it is a rent of a wider place), `margin` (to what the budget was held against, section 6.5), `utility`, `confidence`, `as_of` |

`fact_ids` names the facts of section 7.2 that stand behind the component: the `feature` or `tag` fact, the `budget_fit` fact, or the `travel` facts, with the leg that drove the score first, and then the `missing` fact of each leg that has no time. For a missing component it names the `missing` fact.

**The strip** is the vibes shown under a result's name. It is worked out after ranking and changes none. First the vibes of the spec, heaviest first and then by id, `STRIP_ASKED` = 4 at most. Then `STRIP_OTHERS` = 2 others that the release lets a result show (`Tag.strip`), on which the area sits furthest from the middle: band 1 or 5 first, then 2 or 4, by id. Of those others, a vibe that runs one way is shown only in band 4 or 5, where the area has more of it than most: at its least it read as a warning on a result, about a thing nobody had asked for. A scale has no lesser end and is shown towards either. A vibe whose recipe holds recorded crime (`HOLDS_CRIME`) is never among the others: recorded crime counts, and is shown, only where a person asks for it. Nor is a vibe that counts who lived somewhere, or one that is a rough guide: each holds no `strip`. A vibe that was asked for is shown wherever the area sits on it. A vibe the area cannot be placed on is left out. `RankedArea.counted` and `.present`, how many things count in the spec and for how many of them the area has a figure, are properties in core and not fields: the API works out what it serves from `contributions`. `rank()` and `facts_for()` build ids by the one rule in 7.1, so an id `rank()` names is always an id `facts_for()` returns.

Every area in the release appears in exactly one of `ranked`, `filtered` and `unranked`. `weight_coverage`, `share`, `utility`, `contribution` and `loss` are rounded to 4 decimals on the way out, after sorting. Before that rounding the contributions of a ranked area sum to `S` within 1e-9, which a test inside core checks. After it they sum to `score / 100` within 0.002, which is all a reader of the result can check.

### 6.8 Worked example

A renter with £1,800 a month for one bedroom, soft. Two journeys by public transport: place 1 within 40 minutes, soft, and place 2 within 30 minutes, hard. The slowest drives the score, on typical times. The weights are `commute` 1.00, `budget` 0.80, `feature:park_proximity` 0.50 (direction `less`), `feature:noise_exposure` 0.30 (`less`) and `tag:leafy` 0.40, which is 3.00 requested in total.

| Area | To place 1 | To place 2 | `Q3` | Park percentile | Noise percentile | Leafy score |
|---|---|---|---|---|---|---|
| `syn-n0001` Alderwick | 32 | 24 | 1,750 | 20.0 | 35.0 | 72.0 |
| `syn-n0002` Brackenhythe | 18 | 28 | 1,950 | 60.0 | null | 45.0 |
| `syn-n0003` Cindermoor | 44 | 22 | 1,500 | 10.0 | 15.0 | 88.0 |
| `syn-n0004` Dulcimer Green | 25 | 36 | 1,600 | 30.0 | 30.0 | 60.0 |

**Filters.** Dulcimer Green takes 36 minutes to place 2, over the hard cap of 30. It is filtered with `commute_cap` and not scored. Cindermoor is over the cap to place 1, but that cap is soft, so it stays.

**Utilities.** For place 1, `a = 15` and `z = 60`. For place 2, `a = 15` and `z = 45`. The budget is 1,800, so a quarter over is 450.

| Area | Place 1 | Place 2 | `commute` | `budget` | `margin` |
|---|---|---|---|---|---|
| Alderwick | `1 - 0.5 * 17 / 25 = 0.6600` | `1 - 0.5 * 9 / 15 = 0.7000` | 0.6600 | 1.0000 | +50 |
| Brackenhythe | `1 - 0.5 * 3 / 25 = 0.9400` | `1 - 0.5 * 13 / 15 = 0.5667` | 0.5667 | `1 - 150 / 450 = 0.6667` | -150 |
| Cindermoor | `0.5 * 16 / 20 = 0.4000` | `1 - 0.5 * 7 / 15 = 0.7667` | 0.4000 | 1.0000 | +300 |

**Scores.** Brackenhythe has no noise figure, so that component is dropped, its weights sum to 2.70 and its `weight_coverage` is 0.9000. Each cell is `share`, `U`, `contribution`.

| Component | Alderwick | Brackenhythe | Cindermoor |
|---|---|---|---|
| `commute` | 0.3333, 0.6600, 0.2200 | 0.3704, 0.5667, 0.2099 | 0.3333, 0.4000, 0.1333 |
| `budget` | 0.2667, 1.0000, 0.2667 | 0.2963, 0.6667, 0.1975 | 0.2667, 1.0000, 0.2667 |
| `feature:park_proximity` | 0.1667, 0.8000, 0.1333 | 0.1852, 0.4000, 0.0741 | 0.1667, 0.9000, 0.1500 |
| `feature:noise_exposure` | 0.1000, 0.6500, 0.0650 | missing | 0.1000, 0.8500, 0.0850 |
| `tag:leafy` | 0.1333, 0.7200, 0.0960 | 0.1481, 0.4500, 0.0667 | 0.1333, 0.8800, 0.1173 |
| `S`, the sum of contributions | 0.7810 | 0.5481 | 0.7523 |
| `score` | 78.10 | 54.81 | 75.23 |
| `weight_coverage` | 1.0000 | 0.9000 | 1.0000 |
| `rank` | 1 | 3 | 2 |

Alderwick's losses are `commute` 0.1133, `tag:leafy` 0.0373, `feature:noise_exposure` 0.0350, `feature:park_proximity` 0.0333 and `budget` 0. The result's `ranked` is Alderwick, Cindermoor, Brackenhythe; `filtered` is Dulcimer Green with `commute_cap`; `unranked` is empty.

This example is a required test in `packages/core`, built by hand as an `InMemoryRelease`. The percentiles and the tag scores in the first table are given to that release as they stand. They are not what section 2.4 would make of four areas, and `rank()` must not recompute them.

The weights of this spec are given outright, as a slider sets them, so nothing in the example depends on what a mention is worth or on a default giving way. Those are worked through in section 5.3. What is said of these areas in sentences is worked out from their values and not from the percentiles given here (section 7.3), so Alderwick, scored on a park percentile of 20.0, is said to be closer to a park than 50% of the 4 areas compared: two of the four are further from one.

### 6.9 Likeness

```python
def similar(release: Release, area_id: str, n: int = 5) -> tuple[Likeness, ...]: ...
```

Which rankable areas are most like one area, in streets, buildings and places. It is a pure function of a release, with no spec, so it is the same for everyone. `Likeness` holds `area_id`, `same` (how many measures the two areas are in the same band on, which orders the areas and is what the sentence says), `measures` (the parts both areas have a figure for), `distance` (0 to 1, which orders two areas that share as many, and is never printed) and `family` (the family the two are least alike in, or `None`).

| Rule | Detail |
|---|---|
| What it is counted on | Measured features, and never vibes, so that a walk to a park that six recipes hold counts once. A feature says for itself whether likeness may use it: `in_likeness`. 25 features do, of which the synthetic release carries 23 |
| What it may never be counted on | `may_be_compared()` refuses, whatever the flag says: a feature of `kind` `nuisance` or `on_request`, one that `describes` `events` or `residents`, and one with no family. So recorded crime and recorded incidents are never in it, and nor is the age of residents or what their households are made of: two areas are never said to be alike for who lives in them. Nor is cost, a journey or a vibe's own score, which are no features. `homes_flats`, `homes_density`, `private_outdoor_space` and the school features are held out. Each was to stay out until an audit had passed it. No audit is run since 2026-09-25 (ADR 0006), and each stays out: whether one joins is the founder's to decide. |
| How two areas are compared | Each part by its band, low to high, with no polarity applied: two areas are alike where their figures are. The difference of two bands is 0 to 4. The parts are grouped by family, each family's distance is its mean difference over 4, and `distance` is the mean of the families, rounded to 9 decimals. So each family counts the same, however many parts it holds |
| What is known | An area is compared only if it has a figure for 60% of the parts, counted in whole parts (`MIN_KNOWN_PERCENT`). An area of which too little is known is like nothing, and nothing is like it: `similar()` returns an empty tuple |
| The order | Most alike first: the areas in the same band on the most measures, which is the count each sentence gives. Where two share as many, the one at the least `distance` comes first, and then the `area_id` decides. The five that are served are the first five of that order. Until 1.5.0 the order was by `distance` alone, which no page shows, so an area with 5 measures the same stood above ones with 7 and 8. Never the area itself, and never an area that is not rankable |

### 6.10 A journey that is estimated

No build of London holds a journey time: none has read a timetable. So a journey by public transport is estimated from distance, where the release holds no time for it, and is said to be an estimate wherever it is shown (ADR 0027). `estimate.py` in core holds it, and each number of it is named there, once. Each is the founder's to adjust, and each is a first guess but one: `WITHIN_BY` was 5, and the founder widened it to 10 on 2026-09-25, once the estimate had been held against timetables of the Underground and the DLR. No other number moved, so what a firm limit leaves out did not.

```
FIXED_MINUTES                     = 12     the walk to a stop, the wait, and the far end
MINUTES_A_KM                      = 3.0    for each kilometre in a straight line
MINUTES_A_KM_NEAR_THE_UNDERGROUND = 2.5    where the homes are near the Underground or the DLR
NEAR_THE_UNDERGROUND_M            = 800    how near that is, in a straight line
WITHIN_BY                         = 10     likely within: at least this many minutes under the limit
BEYOND_BY                         = 10     likely beyond: more than this many minutes over it

estimate = FIXED_MINUTES + rate * kilometres(homes_at, place.centroid)
band     = likely_within   if estimate <= M - WITHIN_BY
         = likely_beyond   if estimate >  M + BEYOND_BY
         = borderline      otherwise
```

| Rule | Detail |
|---|---|
| When a journey is estimated | The time that is scored is `missing`, the way of travelling is `pt`, the release holds the place, and it says where the homes of the area stand, `homes_at` (section 2.2). By bike and on foot, and from an area with no `homes_at`, the journey is `missing` as it always was |
| A time that is held | Takes the place of the estimate. `ok` and `beyond_cutoff` are never estimated |
| The distance | In a straight line over the ground, between `homes_at` and the `centroid` of the place |
| Near the Underground or the DLR | The area's `underground_proximity` is at most 800 m. An area with no figure for it is not known to be near |
| What it is worth | `likely_within` 1.0, `borderline` 0.5, `likely_beyond` 0.0. A half is what a journey exactly at its limit is worth (section 6.3). Several journeys are combined as section 6.4 says, on these |
| A firm limit | Leaves out only what is `likely_beyond`, under `commute_likely_beyond` (section 6.1). What is `borderline` stays |
| What is served | The band, as `estimate` of a `CommuteLeg` and of a cell of a comparison, and a `travel` fact whose template is `travel_estimated` (section 7.3). The estimate in minutes is served nowhere |
| What it is a function of | The release and the limit, and nothing else. The same search gives the same answer |
| What says how it is made | Route 11 serves the numbers and the line as `journey_estimate`, where a journey of the release may be estimated, and `null` where none may |

## 7. Facts, explanations and the verifier

### 7.1 The fact row

A fact is one thing Burro may say about one area, with where it came from and when.

| Field | Type | Notes |
|---|---|---|
| `fact_id` | str | `<area_id>/<kind>/<key>`, for example `syn-n0001/feature/park_proximity` |
| `area_id` | str | |
| `kind` | enum | `area`, `feature`, `tag`, `cost`, `budget_fit`, `travel`, `station`, `missing`, `likeness` |
| `key` | str | By kind, as the table in 7.2 gives it |
| `label` | str | From the catalogue or the template table |
| `template` | enum | Which template of 7.3 states this fact. `budget_under`, `budget_over` and `budget_at`, or the nearest station and another, cannot be told apart from the slots alone. A cost with no range has templates of its own, so that a client never draws a range from one number |
| `slots` | mapping of str to str | The values a template prints, already formatted |
| `numbers` | tuple of str | Every number that may be printed for this fact, normalised by 7.4. A number that is money or a share keeps its sign, `£1750` and `80%`, so that it cannot be said of anything else |
| `names` | tuple of str | Every proper noun that may be printed for this fact |
| `sources` | tuple of `FactSource` | `source_id`, `name`, `publisher`, `attribution` and `said_with_attribution`, from the manifest, in `source_id` order. Never empty. `attribution` is the publisher's own statement of credit, where the release says it stands beside every figure (`credit_beside_figures`, section 2.1), and `null` for any other source. A client draws it with the source wherever the fact is shown. `said_with_attribution` is what the terms of the publisher ask to be said wherever its credit is shown (section 2.1). It goes with the credit: a fact holds it where it holds `attribution` and the release holds something to say, and `null` anywhere else. A client draws it after the credit |
| `as_of` | str | The vintage, month or date. Never empty |
| `synthetic` | bool | From the manifest |

A fact has several sources when what it says was built from several, as a journey time and a vibe are. `parse_release` refuses a release in which any fact would lack a source or a date, so `facts_for` never has to invent one.

### 7.2 Building facts

```python
def facts_for(release: Release, area_id: str, spec: PreferenceSpec | None) -> tuple[Fact, ...]: ...
```

It is pure and returns facts ordered by `fact_id`. Without a spec it returns what a profile page needs, the `likeness` facts among it. With one it adds the `travel`, `budget_fit` and `missing` facts for that spec, and leaves likeness out. A missing value never produces a fact that carries a figure about the place.

| Kind | One fact per | `key` | `numbers` | `names` | `sources` and `as_of` from |
|---|---|---|---|---|---|
| `area` | area | `name` | none | area name, borough, and the label where the area bears another name | `origin(neighbourhoods)` |
| `feature` | feature with a value | the feature id | value, and what its comparison states from either side: the share strictly beyond, how many areas were compared, how many are level (7.3). Its band is a slot and no number | none | the catalogue row: `source_ids`, `vintage` |
| `tag` | vibe the release carries, placed or not | the tag id | Placed: the band, 5, and how many areas were compared, or the two ends of its spread, and how many parts have a figure, how many parts there are, what they carry of the recipe, and 100. Not placed: how many parts have a figure, and how many parts there are | Not placed: the area name | the sources of the parts that had a value, and `as_of` the span of their vintages, "2024 to 2025", never the day the release was built. Where no part has a figure, `origin(neighbourhoods)`: the fact then says nothing of the place but its name |
| `cost` | tenure and segment with an estimate | `<tenure>.<segment>` | the three quartiles, or the median alone where the row has no range, and the year and month of `as_of`. Where the row counts its sales: how many, and the year and month of `since` | none | the cost row |
| `budget_fit` | spec with a budget and an estimate | `<tenure>.<segment>` | amount, what the budget was held against (the upper quartile, or the median where the row has no range), and `abs(margin)` where it is not nothing | none | the cost row |
| `travel` | commute in the spec, unless the time that is scored is `missing` and nothing is estimated | `<place_id>.<mode>` | each of the two times that is `ok`, the cutoff when the scored time is beyond it, and the limit and the minutes between the scored time and it, where they are not nothing. Of a journey that is estimated, the limit alone | place name | `origin(travel)`. Of a journey that is estimated: the source of the place, `origin(neighbourhoods)`, and the catalogue row of `underground_proximity` where the area has a figure for it, with `as_of` the span of their dates |
| `station` | station row | the station id | walk minutes | station name, each line name | `origin(stations)` |
| `missing` | component the spec requests that is missing for the area, and each journey of the spec that has no time and no estimate | the component name, or `commute.<place_id>.<mode>` | none | area name, and the place name for a journey | `origin(neighbourhoods)`, or `origin(travel)` for a journey. Where the release has routed no journey and states no source of one, `origin(neighbourhoods)` for a journey too |
| `likeness` | each of the five areas most like this one (section 6.9), where there is no spec | the other area's id | how many measures were compared, and how many are in the same band | both area names | the sources and the span of vintages of the measures both areas have a figure for |

**What the fact of an area says of its name.** Its slots hold `name` and `borough`. Where the area bears a name that is not its publisher's label (section 2.2), they hold three more: `label`, the label; `written_by`, the publishers of the sources that write the name, joined by " and "; and `state`, `draft` or `checked`. The sentence of the fact prints none of the three. A client lays the label out beside the name, smaller, and says in its own words for the state that a name is a draft.

Numbers are formatted once, here: money with thousands separators, metres to the nearest 10 and with thousands separators, "1,080 m", a flow of traffic to the whole vehicle and with thousands separators, "16,915 motor vehicles a day", percentages to whole numbers, other values to one decimal with a trailing `.0` dropped. A share of areas is rounded down to a whole number and never to the nearest, so that a sentence never says more than is so. The mid-rank percentile an area is scored on is not among a fact's numbers and is never printed in a sentence: where areas tie it counts half of them as beaten, which is right for a score and untrue of the release.

### 7.3 Templates

Every template is filled from one fact's `slots`, and every template's output passes the verifier. `{value}` comes with its unit already attached, as people write it: `340 m`, `12%`, `3` for a count. The sentence states where the value sits and passes no judgement. Every comparison says "in this release", so a synthetic one can never say "London".

| Template | Text |
|---|---|
| `area` | {name} is in {borough}. |
| `feature` | {label}: {value}, {standing}. |
| `feature_crime` | The `feature` sentence, then: Recorded crime depends on what is reported, and locations are approximate. |
| `vibe` | {label}: band {band} of 5, counted from {low_end} to {high_end}, among the {compared} areas compared in this release. {partly} Parts dated {span}. {judgement} |
| `vibe_range` | {label}: varies within this area, from band {spread_low} to band {spread_high} of 5, counted from {low_end} to {high_end}. {partly} Parts dated {span}. {judgement} Used where the spread is three bands or more: a mixed area is a range, and never a point in the middle |
| `vibe_unknown` | Burro cannot place {name} on {label}. Parts with a figure in this release: {known} of {parts}. |
| `cost_rent` | Rent for a {segment}: £{lower} to £{upper} a month, middle £{median}, as of {as_of}. Confidence: {confidence}. |
| `cost_buy` | Price for a {segment}: £{lower} to £{upper}, middle £{median}, as of {as_of}. Confidence: {confidence}. |
| `cost_buy_median` | Price for a {segment}: £{median}. This is the middle price of {homes} of all sizes sold in {period}. The publisher gives no range, and does not say how many sales it rests on. Used where the row has no range and no count of sales. `{period}` is "the year ending March 2026", from `as_of`. It prints no word for the confidence, which is a slot |
| `cost_buy_sold` | Price for a {segment}: £{median}. This is the middle price of the {sales} {homes} of all sizes sold from {period}. Used where the row has no range and counts its sales. `{period}` is "January 2023 to December 2025", from `since` and `as_of`, and `{sales}` is the count, as "1,204" |
| `cost_rent_recorded` | Rent for a {segment}: £{lower} to £{upper} a month, middle £{median}. {is_of} It rests on about {rents} rents recorded there from {period}. Used where the row is of a wider place. `{is_of}` is one sentence: "This is of postcode district {of_name}, and not of {name} alone.", or "This is of the whole borough of {of_name}, and not of {name} alone." `{period}` is "April 2025 to March 2026", from `since` and `as_of`. The fact holds `of`, the place in words, `of_kind` and `of_name`, `half_let` and `caution` as slots as well: the last is what the publisher advises, which a page says once. It prints no word for the confidence, which is a slot |
| `budget_under` | The upper end is £{margin} under your budget of £{amount}. |
| `budget_over` | The upper end is £{margin} over your budget of £{amount}. |
| `budget_at`, `budget_at_median`, `budget_at_recorded` | The sentence of `budget_under`, of `budget_under_median` and of `budget_under_recorded`, with "at" where that says "£{margin} under": The upper end is at your budget of £{amount}. Used where what the budget is held against is the budget to the pound. Seen in a browser on 2026-09-25: "£0 under your budget", which was read as a fault. A rent is a round number and so is a budget, so the two are often one amount. The fact holds no `margin`. It holds `verdict`, which is "At your budget", for a page that lays the figures out |
| `budget_under_median` | The middle price of {homes} of all sizes is £{margin} under your budget of £{amount}. Used where the row has no range |
| `budget_over_median` | The middle price of {homes} of all sizes is £{margin} over your budget of £{amount}. {half_sold} Used where the row has no range. `{half_sold}` is one sentence, which says what a median is: "About half of the flats sold here went for under £437,500." The `cost` fact of a row with no range holds the same slot, for a page that shows a price beside a budget |
| `budget_under_recorded` | The middle rent for a {segment} in {of} is £{margin} under your budget of £{amount} a month. Used where the rent is of a wider place. `{of}` is "postcode district {of_name}" or "the whole borough of {of_name}". The fact holds `is_of`, `period` and `rents` as slots, for a page that lays it out |
| `budget_over_recorded` | The middle rent for a {segment} in {of} is £{margin} over your budget of £{amount} a month. {half_let} Used where the rent is of a wider place. `{half_let}` is one sentence, which says what a median is: "About half of the rents recorded there were under £1,400." |
| `travel_pt` | By public transport to {place}: about {typical} minutes on a typical weekday morning, {missed} if you just miss a service. |
| `travel_other` | {mode} to {place}: about {minutes} minutes. Used by bike and on foot, and by public transport when only one of the two times is `ok` |
| `travel_pt_over`, `travel_other_over` | The same, ending: , {margin} {margin_unit} over the {limit} you set. Used when the time that is scored is over the journey's limit. `{margin_unit}` is "minute" or "minutes". A journey that is not over its limit holds `margin` too, which is how far under it is. One that takes the minutes of its limit holds none: it holds `verdict`, which is "At your limit", and its sentence is that of `travel_pt` or `travel_other` |
| `travel_beyond` | {mode} to {place}: more than {cutoff} minutes. Used when the scored time is beyond the cutoff |
| `travel_estimated` | {mode} to {place}: {said} the {limit} minutes you set. {estimated} Used when the release holds no time and the journey is estimated (section 6.10). `{said}` is "likely within", "borderline for" or "likely beyond". `{estimated}` is the line "Estimated from distance, not from a timetable." The slot `band` holds the code, and `verdict` the band as it is said where it stands alone: "Likely within your limit", "Borderline for your limit", "Likely beyond your limit". No slot holds minutes of its own |
| `station` | Nearest station: {name}, about {walk} minutes on foot. Lines: {lines}. |
| `station_nearby` | Station within a short walk: {name}, about {walk} minutes on foot. Lines: {lines}. Used for an area's other stations, of which "nearest" would be untrue |
| `missing` | There is no {label} figure for {name} in this release, so it was left out of the score. |
| `missing_journey` | There is no journey time from {name} to {place} in this release, so that journey was left out of the score. One for each journey with no time |
| `likeness` | {name} is in the same band as {other} on {same} of the {measures} measures compared, and least alike in {family}. |
| `likeness_same` | {name} is in the same band as {other} on all {measures} measures compared. Used where the two differ in nothing |

**A band that rests on part of a recipe says so.** A part with no figure is dropped and the rest reweighted (section 3.2), so a band may rest on as little as 60 of the 100 its recipe adds up to. The slot `share` holds what it rests on, as a whole number of the 100, beside `known` and `parts`. Where that is under 100, `{partly}` is the clause "Worked out from {known} of its {parts} parts, {share} of 100 by weight." Where it is 100 the clause is empty, and the sentence is as it was. Until 1.5.0 a band that rested on two parts of three was said as any other. In the synthetic release Everyday on foot, Homes and Food and drink say it of every area, at 70, 75 and 80.

**In an explanation a vibe is said in short.** A result is to say in a few lines why this place, and the full statement of a vibe ran to thirty words, half of them the same on every result that led with it. So a reason and a trade-off that cite a `vibe` or a `vibe_range` fact end after `{partly}`: "Leafy: band 5 of 5, counted from least to most, among the 21 areas compared in this release." `IN_SHORT` in `explain.py` holds the two, and each is the start of its full statement, word for word, so a short sentence says nothing the full one does not. What it leaves out is not lost. The dates are the fact's `as_of`, and the line about judgement is its slot `judgement`: a client shows both with the source of the sentence, one press away. Every other fact is said in full wherever it is said. Until 1.6.0 an explanation gave the full statement.

**A vibe is said as a band, and never as a percentage, a score or a rank.** `{low_end}` and `{high_end}` are the names of a scale's ends, and "least" and "most" for a vibe with one way. `{judgement}` is fixed: "The recipe is Burro's own. The weights are a judgement." The slot `made_from` holds "Burro's recipe. Made from data published by:", for the line of sources a client sets under it. No sentence about a vibe holds the mid-rank percentile it is ranked on.

**A comparison must be literally true of the release.** `{standing}` is one of the clauses below, filled in `facts.py` and held in the fact's slots beside its parts (`comparative`, `pct`, `compared`, `level`), so that a client can lay them out for itself. `STANDINGS` holds the clauses.

The areas compared are the ones a percentile is worked out over (section 2.4): the rankable areas that have a figure, `compared` of them, this area among them if it is rankable. Of those, `below` have a figure strictly lower than this area's, `above` strictly higher, and `level` others have the same. These are counts of areas, so each is exactly true.

| Clause | Used when | Text |
|---|---|---|
| `beyond` | No other area is level | {comparative} {pct}% of the {compared} areas compared in this release |
| `beyond_and_level` | Some are | {comparative} {pct}% of the {compared} areas compared in this release, and the same as {level} others |
| `all_level`, `one_level` | Every other area is level | the same as all {others} other areas compared in this release; the same as the only other area compared in this release |
| `level` | `{pct}` would be 0, which says nothing: under one area in a hundred is strictly beyond | the same as {level} of the {others} other areas compared in this release |
| `none` | No area is strictly beyond on the side it is said from, and none is level | {comparative} none of the {others} other areas compared in this release |
| `alone` | No other area has a figure | with no other area in this release to compare it with |

- **A sentence is said from the side of its role.** A figure has a better side and a worse one. The better side is the direction the spec weighs the feature in, or the direction its polarity gives where the spec does not weigh it, and `more` where that is `either`. A reason, and a sentence with no role, is said from the better side: how many areas this one does better than. A trade-off is said from the worse side: how many do better than it. Both are held in the fact: `standing`, `comparative` and `pct` for the better side, and `standing_worse`, `comparative_worse` and `pct_worse` for the worse. `render(fact, role)` chooses. Until 1.4.0 the side was the side the percentile was on, so a trade-off could read "closer than 23% of areas", which is true and says the wrong thing of what an area gives up.
- `{comparative}` is the feature's "higher" or "lower" word followed by "than".
- `{pct}` is the share of the areas compared that are strictly beyond this one on that side, `100 * below / compared` or `100 * above / compared`, **rounded down**. An area with no water at all, as 13 of 22 have, is said as a trade-off to have "less than 40% of the 22 areas compared in this release, and the same as 12 others": 9 of 22 have more, which is 40.9%. As a reason it is "the same as 12 of the 21 other areas compared in this release", because none has less. It is scored on a percentile of 29.5, and the sentence it used to get, "less than 70% of areas", was untrue.
- An area that is level is never counted as beaten, and is always counted: `{level}` is stated whenever it is not 0. "Many" is not left to a threshold.
- The figures compared are the values as the release holds them, not as they are printed. Two areas 281 m and 283 m from a park both print as 280 m, and one is still closer than the other.

A test renders every feature fact of the committed release from both sides, and every vibe, and checks each against the rows of the release, so that a change of wording cannot bring the defect back.

### 7.4 The verifier

```python
def verify(sentence: Sentence, facts: Mapping[str, Fact]) -> Verdict: ...
```

`Sentence` holds `text`, `fact_ids` and `origin` (`template` or `model`). `facts` holds the facts of the one area being explained, keyed by `fact_id`, so a fact about another area cannot be cited. `Verdict` holds `ok` and a `reason` code, never the text. The check is inverted: it does not look for names it knows, it rejects anything it cannot account for.

| Step | Rule |
|---|---|
| 1. Citations | Every `fact_id` must be in `facts`. The allowed numbers and names are the union over the cited facts. Their `label` and `slots` count as allowed text. `explain` lets a sentence cite the fact it was asked about and the `area` fact, and no other (7.5) |
| 2. Numbers | A number is a run of ASCII digits with thousands separators and one decimal point, and a `£` before it or a `%` after it if it has one. It is normalised by removing separators and dropping a trailing `.0`, and it keeps its sign. A number with a sign must be among the allowed numbers with the same sign: "£57" is not supported by a fact that holds 57%, nor "57%" by one that holds 57 minutes. A number with no sign may be any allowed number, or stand as a number in the allowed text, as the 8 in a label does |
| 3. Digits that are not ASCII | A character that is numeric and is not ASCII always fails: a full-width digit, a digit of another script, "½", a number in a circle. No fact holds one, so none can be checked. The one exception is the "²" or "³" of a unit, directly after a letter, as in µg/m³ |
| 4. Number words | "zero", "one" to "nineteen", the tens to "ninety", "hundred", "thousand", "million", "billion", "trillion" and their ordinals count as numbers and must be allowed as digits. So do the words for nothing, "nil", "nought", "none", "zilch", which are 0. A ten followed by a unit is one number: "seventy-one" is 71, and is not supported by a fact that holds 70 and 1. A unit said with an article is one of it: "a minute", "a mile", "a stop" need a fact that holds 1. A Roman numeral of two letters or more is the number it states, "xxi" as "XXI". A word that has the shape of a number word and is none, "fourty", "ninty", "twelth", "seventies", and number words run together, "twentyone", say a number nobody can be held to, and always fail. "half", "double", "twice", "dozen", "couple" and "several" always fail, and so do "hour", "day", "week", "fortnight", "year", "decade", "century", "quarter" and their plurals, "thirds", and "tens", "hundreds" and "thousands": no fact holds "an hour". The one exception is a pair of words that stands in the cited fact itself: "a year" where a rate is counted "per 1,000 residents a year". "A month", which a rent is paid by, is not a quantity |
| 5. Proper nouns | Take each maximal run of capitalised tokens. It passes if, casefolded, it is a contiguous part of an allowed name or of allowed text. A single token also passes if it is in `ORDINARY_WORDS`, a short list of sentence openers and common words. Anything else fails. A token mixing letters and digits, such as a postcode, is a proper noun. An ordinary word that opens a sentence is judged apart from the name that follows it, so "In Alderwick" passes; nothing else is loosened, and "The Alderwick Arms" still fails. A word for a number inside a name that passes is no number, provided the name holds a word that is not one: the "Quarter" of "Guild Quarter" |
| 6. Banned words | "safe", "unsafe", "danger", "rough", "dodgy", "sketchy" fail anywhere, in every form they take: "safer", "safely", "safety", "dangerous", "dangerously", "roughly", "dodgier". So do praise and blame with nothing behind them, because no dataset rates a place, says its people are friendly or says where it is heading: "best", "top", "acclaimed", "friendly", "unfriendly", "vibrant", "gritty", "polished", "close-knit", "highly rated" and "up and coming". "Gritty" and "polished" pass in one place only: as the name of an end of a scale, from the `low_end` or `high_end` slot of a fact the sentence cites. A word that only holds one, "safeguarded", says something else and passes. The sentence is checked as it reads and not as it is encoded: accents, zero-width characters and soft hyphens are taken out, and a letter of another alphabet that reads as a Latin one is read as that one, so "safe" with a Cyrillic a is "safe" |
| 7. Other alphabets | A word that holds a letter that is not Latin fails, unless the word stands in a cited fact: the µ of a unit, or a name. Nothing here can read it, so nothing can account for it |
| 8. No citation | A sentence citing nothing passes only if steps 2 to 7 find nothing to check |

On failure the sentence is replaced by the template for its first cited fact, or dropped if it cites none.

**What the verifier does not check.** It checks that a number and a capitalised name are the cited fact's. It does not check what a sentence says of them, and it checks nothing else a sentence asserts. These are limits, stated so that nobody relies on what is not there:

- It finds a name by its capital. "Near waitrose and the tate modern" holds no capital and passes.
- It knows a verdict on safety by the words of step 6. "A secure, low-crime place", "a respectable area" and "popular with young families" hold none of them and pass, though the first two pass judgement and the third describes residents. A banned word spelt with a space or a hyphen between its letters passes too.
- It ties a number to `£` and `%`, and to no other unit and no noun. Asked about a journey of 32 minutes, "the nearest park is 32 minutes away" passes: the number is the fact's and what is said of it is not.
- It does not check which way a comparison runs. "Further than 40%" passes where the fact says "closer than 40%".

None of this reaches a person today. `TemplateExplainer` is the only explainer, its sentences are fixed text, and a test renders every one of them. It is why a model-written explanation may not be attached as the verifier stands, and why `explain()` refuses any other explainer (sections 7.5 and 11). Two tests hold such sentences and are marked as expected to fail, so that they say so when the verifier is extended.

### 7.5 Explanations

```python
class Explainer(Protocol):
    def draft(self, area: ExplainInput) -> tuple[Sentence, ...]: ...


def explain(
    result: RankResult,
    release: Release,
    spec: PreferenceSpec,
    area_ids: tuple[str, ...],
    explainer: Explainer,
) -> tuple[Explanation, ...]: ...
```

`ExplainInput` holds the area's facts and contributions, and `asks`: the sentences wanted, each with its role, its component and the fact it must cite. It never holds user text. For each area `explain` picks:

- **Orientation:** the `area` fact.
- **Reasons:** a reason is something the area does well. Of the present components whose utility is at least `REASON_MIN_UTILITY`, 0.50, the three with the largest `contribution`, ties by component name. Fewer if fewer qualify, and none if none does. A component below 0.5 adds to the score and is still no reason to live there: it can only be the trade-off. **A reason never states a shortfall.** The budget is a reason only when the home is within it, `margin >= 0`: a home £150 over a budget of £1,800 is worth 0.6667 and is no reason. The journey is a reason only when every journey that was scored is within its cap, the cap itself included: the mean of two journeys can be worth a half or more while one of them is over its cap, and the sentence states the slower one.
- **Trade-off:** a trade-off is something the area does badly. Of the present components whose utility is below `TRADE_OFF_MAX_UTILITY`, 0.35, or that are a shortfall (a home over budget, a journey over its cap), the one with the largest `loss`, ties by component name. If the area does nothing it was asked for badly, it has no trade-off: `trade_off` is `null`, and a client says so in fixed words of its own. **A trade-off is never something the area does well**, and "badly" is not "a hair under a half": a walk of 5 minutes to a station, worth 0.48, was given as what an area gives up. A component worth 0.35 or more and less than 0.50 is neither a reason nor a trade-off. It is in the working of a result and in no sentence. 0.35 is a first figure, to be held against recorded searches (section 13). **A trade-off is worse than most and bad in itself.** What a component is worth says where an area stands among the others, and nothing of how far a walk is: a walk of 7 minutes to a station was worth 0.34 in a city where fourteen areas are closer still, and was given as what the area gives up. So each feature that is a walk, a time or a distance has a figure, at or under which it is never a trade-off, whatever it is worth. `NEVER_A_TRADE_OFF` in `catalogue.py` holds them, beside the features and in no rule of code, and `checked_floors()` holds the table to every feature whose unit is minutes or metres and to no other. A walk at or under its figure that is worth under 0.50 is in the working of a result and in no sentence, as what lies between the two thresholds is. A journey of the spec has no such figure: it is measured against the limit the person set.

| Feature | Never a trade-off at or under | How it was chosen |
|---|---|---|
| `park_proximity`, `play_space_proximity`, `station_walk`, `underground_proximity`, `overground_proximity`, `rail_proximity`, `highstreet_access`, `grocery_walk`, `gp_walk`, `pharmacy_walk` | 800 m | What a person walks in ten minutes, at 80 m a minute. Ten minutes on foot is the catalogue's own measure of what is within a walk: `station_lines` and `independents_nearby` each count what is within a 10-minute walk, and a release lists a station as nearby within ten (section 2). Each is a straight line, so the walk is longer than the figure: the floor was chosen for a walk, and is to be looked at again. The food shop stood at 10 minutes while it was named a walk, which is the same walk. **The floor of `station_walk` was looked at on 2026-09-25, and stands:** the founder decided that near a station is about a 10 to 15 minute walk, and a straight line of 800 m is a walk of about that. So no figure moved. An offer of the measure says "Within 800 m in a straight line is about a 10 to 15 minute walk.", which is `NEAR_A_STATION` in `catalogue.py` (section 8.2). The measure is still named a straight line, in metres, and never a walk |
| `park_large_proximity`, `university_proximity` | 1,600 m | Twenty minutes at the same pace. A park of 20 ha and a campus are fewer than a local park, and are walked further to |

Each is a first figure, chosen by judgement and from no source, and is for the founder to hold against real walks (section 13). The table is no part of a release and changes no rank: it is a rule of what an explanation says, and moves with `ENGINE_VERSION`.
- **A journey that is estimated** is a reason only where it is likely within its limit, and is what an area gives up only where it is likely beyond it. One that is borderline is neither. Its sentence says that it is an estimate, in either place.
- **Missing:** one sentence for each dropped component, and one for each journey that has no time and no estimate, each citing its own `missing` fact.

It asks the explainer for a sentence for each, verifies every one, and replaces failures. A sentence of the template explainer, and one that replaces a failure, is the template of its fact, but for a vibe, which is said in short (section 7.3). A sentence is kept only if it cites the fact it was asked about first, and after it nothing but the `area` fact. What a sentence cites is what it may say, so one that could cite every fact of the area could say the minutes of a journey of a park. The `area` fact holds names and no number: it lets a sentence name the area and nothing more.

A sentence about `commute` cites the leg that drove the score, which is the first of the component's `fact_ids`: the leg with the lowest utility, and on a tie the first in `place_id` order. In the worked example Alderwick's reasons are `budget`, `commute` and `feature:park_proximity`, and it has no trade-off: being leafy is worth 0.72 to it and its noise 0.65, so neither is something it does badly, and neither is among its three reasons. Cindermoor's journey to place 1 is 44 minutes against a cap of 40, which is worth 0.40. It contributes 0.1333, more than being leafy does, and it is no reason: Cindermoor's reasons are `budget`, `feature:park_proximity` and `tag:leafy`, and the journey is its trade-off. Brackenhythe is £150 over budget, which is worth 0.6667 and is no reason either: its one reason is its journey. The walk to a park is worth 0.40 to it, which is neither a reason nor a trade-off, so its trade-off is the budget, which is a shortfall.

`Explanation` is `area_id`, `orientation`, `reasons`, `trade_off` and `missing` (one `missing` sentence for each dropped component), where each entry is a `Sentence` plus `replaced: bool`.

**`explain()` takes `TemplateExplainer` and no other explainer.** It is a check in code: passed anything else, a class of the right shape included, it raises `TypeError` before anything is drafted, with a message that names this document and section 11. A second explainer is a second implementation of the protocol, and attaching one is a decision that changes this check and extends `verify()` first, not a parameter. A test that plants a sentence, to show that the verifier replaces it, does it from a subclass of `TemplateExplainer`, which nobody writes by accident.

### 7.6 The portrait

```python
def portrait(release: Release, area_id: str) -> Portrait | None: ...
```

Where an area sits on every vibe of the release, and what cannot be placed. It is built with no spec, so it is the same for everyone. It holds ids and no sentence: each mark names the fact that holds its sentence, its sources and its date, and each part the fact that holds its figure. `None` for an area the release lacks.

| Record | Fields |
|---|---|
| `Portrait` | `scales`, `more`, `less`, `others`, `unplaced`: each a tuple of `PortraitMark`. Every vibe of the release is in exactly one |
| `PortraitMark` | `tag_id`, `fact_id` (its `tag` fact), `figure_fact_id` (the `feature` fact of its heaviest part that has a figure, or `None`), `parts` |
| `PortraitPart` | `feature_id`, `hundredths`, `reading`, `fact_id` (the `feature` fact, or `None` where the area has no figure for the part: nothing is filled in) |

| List | Holds |
|---|---|
| `scales` | The scales the area is placed on, in the fixed order Houses or flats, Going out, Age of buildings, Gritty |
| `more` | The vibes with one way that the area has more of than most: 60% of the areas compared or more sit strictly below it (`MOST_PERCENT`), counted in whole areas. Furthest first, then by id, three at most |
| `less` | The same, with 60% or more strictly above |
| `others` | Placed, and in neither list: near the middle, beyond the three of a list, or a vibe the release does not let a result show. A vibe that counts who lived somewhere is always here where the area is placed on it, whatever its band: it is never what an area is said to have most or least of |
| `unplaced` | The vibes the area cannot be placed on. One is never drawn in the middle |

Neither Gritty nor Works and warehouses is ever the first thing said of an area: where Works and warehouses would head a list it is second, and where it would be alone in one it is among `others`. Gritty is a scale, and is the last of the scales.

## 8. Interpreters

### 8.1 The interface

```python
class Interpreter(Protocol):
    name: InterpreterName

    def interpret(self, request: InterpretRequest) -> InterpretResult: ...
```

| Type | Fields |
|---|---|
| `InterpretRequest` | `text` (1 to 600 characters), `spec` (the spec to edit; a default for a first prompt), `release` |
| `InterpretResult` | `status`, `operations`, `assumptions` (each a `code`, `group`, `index`), `unmet` (tuple of `UnmetCategory`), `clarify` (each a `group`, `index` and up to five options of `id`, `name`, `kind`), `notice` (`none`, `neutral_places`, `off_topic`), `interpreter` (`rule`, `model`), `degraded`, `usage` (`input_tokens`, `output_tokens`, `cache_read_tokens`), `rests_on` (each a `group`, `index`, `start`, `end`), `suggestions` (tuple of `Suggestion`), `unread` (tuple of `Span`), `asks_nothing` (tuple of `Span`, which no route serves), `not_in_release` (tuple of `NotInRelease`, each a `target`, a `label` and `spans`) |
| `Suggestion` | `target` (`feature:<id>`, `tag:<id>`, `budget`, `tenure`, `commute` or `area`), `label` (the `short_label` of the thing, or the release's name of the place or the area, and never the text), `spans` (where the words stand, at least one), `choices` (in the order `more`, `less`, `ignore`, with `ignore` always last), `note` (what a person should know before they choose, in fixed words of core's own, and empty where there is nothing to add) |
| `Choice` | `direction` (`more`, `less`, `ignore`), `label` (text of Burro's own: "Fewer pubs and bars", "Towards Calm", "Add a journey to Pellam Infirmary", "Leave it out"), `operations` (what is sent to be ranked if it is chosen. Every edit is `ui_edit`. Six empty arrays for `ignore`) |
| `Offer`, `Way` | The API's, in `offers.py`: a `Suggestion` and a `Choice` with what a guess needs beside them. A `Way` has an `id` that tells it from every other way of its offer, and `guess`. An `Offer` has `read_by` (`rule` where the rules noticed the thing, `model` where only a model read it), what nobody said (`unsaid`), and, for a journey to a place the release does not hold, `asks_place`, `named_at` and `options`. The rules make a `Suggestion`, and route 1 serves every one as an offer. The rules choose no way of a wish. What a person plainly said of the home they look for carries the guess, whoever reads (section 8.2) |
| `Span` | `start`, `end`: code points into the text as sent, `end` not included, as `rests_on` counts |

`group` is the name of one of the six arrays and `index` a position in it, so an assumption or a clarification always points at an edit in `operations`. An assumption's `code` names what was chosen for that edit because the text did not say: `tenure`, `segment`, `strictness`, `mode`, `max_minutes` or `direction` for a field the edit left to a default, `weight` for a weight or a vibe whose provenance is `inferred`, and `word` for a word with two meanings that was read as its place part alone. An assumption holds `word` too: for the code `word` it is that word, "gritty", "edgy" or "raw", as the lexicon spells it and never as it was typed, and for every other code it is empty. `assumptions_for(operations, spec)` in `interpret.py` works them out from the edits and the spec they were made for, so both interpreters state the same assumptions for the same edits. The rule-based reader states `max_minutes` of one journey more: one whose minutes were typed as a range, "35-40 minutes", of which the longer was taken. The person gave two numbers and the search holds one, so the chip says it was assumed.

`rests_on` says which words of the text each edit rests on, so that a person can be shown which of their words made it. An entry points at an edit by `group` and `index` and holds `start` and `end`, which count the characters of the text as it was sent, as Python counts them (code points, not UTF-16 units), so that `text[start:end]` is the words. An edit made of several parts, as a budget is of "renting", "2 bed" and "£1,500", has an entry for each part, in the order they stand. Every edit the rule-based reader makes has at least one, and all of them lie in one sentence, but for a budget, whose parts may stand in several, and a journey whose minutes are said beside it. It is offsets and never words: nothing stores them and nothing logs them, and they mean nothing without the text, which only the sender holds. No edit of `operations` is a model's (section 8.2), so every entry is the rules' own. What a model read is in `suggestions`, and each offer says where its words stand in `spans`.

The method is synchronous. API routes that call it are plain `def`, so FastAPI runs them on its thread pool and no test has to be written as a coroutine. Nothing in the result holds the user's words: assumptions and unmet requests are codes, notices are fixed text held in core, clarification options come from the release, and `rests_on` holds offsets.

| `status` | Meaning | `operations` |
|---|---|---|
| `ok` | Understood, or nothing in it was noticed | Every edit that could be made |
| `suggest` | The prompt is not plain, and something in it was noticed, by the rules or by a model | Empty. `suggestions` holds what was noticed, for the person to choose |
| `clarify`, of a prompt that is not plain | A place the release does not hold is named where the grammar expects a place | The question alone: an edit that holds an empty id, so that it adds nothing to the search. `suggestions` holds whatever else was noticed |
| `clarify` | A named destination or area matched nothing, or several things | Every edit. The unresolved one carries an empty id, so the reducer rejects it as `unknown_place` or `unknown_area` and applies the rest. `clarify` points at it and lists the options. The client sends it again with the id the person picked |
| `policy_redirect` | Part of the request was about who lives somewhere | Every other edit. `notice` is `neutral_places` |
| `off_topic` | Nothing in it is about choosing where to live | Empty. `notice` is `off_topic` |

`status` is the first that applies in the order `off_topic`, `policy_redirect`, `clarify`, `suggest`, `ok`. `clarify`, `notice`, `suggestions` and `unread` are filled whenever they apply, whatever the status. `RuleInterpreter` cannot tell an off-topic sentence from one it failed to read, so it never answers `off_topic`: it answers `ok` with no edits and `other` in `unmet`. `UnmetCategory` is one of `broadband`, `flood_risk`, `health_services`, `driving`, `listings`, `affordability_verdict`, `community_amenities`, `outside_the_city`, `street_cleanliness`, `upkeep`, `ratings`, `prices_and_hours`, `mobile_coverage`, `change_over_time`, `other`. The six before `other` are what no open data measures at the scale of a neighbourhood: they are heard, make no edit, and are told to the person in fixed words.

What the rule-based reader answers, by what the prompt is:

| The prompt | `status` | `operations` | `suggestions` | `unread` | `notice` |
|---|---|---|---|---|---|
| Plain, and every name is whole | `ok` | Every edit | Empty | Empty | `none` |
| Plain, and the words after a cue are the whole of no name | `clarify` | Every edit. The one asked about holds an empty id | Empty | Empty | `none` |
| Plain, with a phrase about who lives somewhere | `policy_redirect` | Every other edit | Empty | Empty | `neutral_places` |
| Plain, and all of it is what Burro has no measure of | `ok` | Empty | Empty | Empty | `none`. `unmet` names each category |
| Plain, and it names a home of which no edit can be made | `ok` | Every other edit | Empty | The words of the home | `none`. `unmet` holds `other` |
| Not plain, and something was noticed | `suggest` | Empty | One or more | What is left | `none` |
| Not plain, and a sentence the grammar makes names a place the release does not hold | `clarify` | The question alone, which holds an empty id | Whatever was noticed | What is left | `none` |
| Not plain, with a phrase about who lives somewhere | `policy_redirect` | Empty | Whatever was noticed | What is left | `neutral_places` |
| Not plain, and nothing was noticed | `ok` | Empty | Empty | The whole text, where a word of it may have asked for something | `none`. `unmet` holds `other` |

`unread` holds each stretch of the text that no edit, no suggestion, no notice and no `unmet` category but `other` rests on, in order, and two that touch are one. Words that say what the search already holds are not among it: a journey to a place the search holds a journey to is offered nowhere, because to choose it would change nothing, and it was heard all the same. Words whose every edit would be turned away are unread. The size and the kind of a home are the exception to both: they are offered whenever they are named (section 8.2). Suggestions and `unread` are served to the caller, who holds the text. They are never logged, never kept about a call and never stored in a share.

**Words that ask for nothing are not said to be unread.** Seen in a browser on 2026-09-25: after a sentence of thirteen things the page said that some words were not read, and marked "I want to live somewhere". A person reads that as something Burro missed. In a prompt that is not plain, most of what nothing rests on is how a wish is said and no wish. So a stretch that holds nothing but such words is left out of `unread` and kept in `asks_nothing`, which no route serves. The words are core's lists, as `ASKS_NOTHING` in `grammar.py` puts them together: the speaker, what asks Burro, what the speaker wishes to do, "somewhere" and what follows it, an article, whose wish it is, what says near before and after a thing, what joins, courtesy, "if", and what stands between the parts of a home, "for". A wish is among them only where the grammar places it, straight after the speaker, "I want": anywhere else it may compare or be another's, "pubs like I need noise", "some want pubs". A phrase that says how much, whose wish it is, or that turns, is what its words say, whatever each is alone: "a lot", "is looking for". No phrase is put together across a mark or the end of a sentence. Nothing is guessed at: a word that is on none of the lists is unread wherever nothing was made of it, and a stretch is left out whole or not at all, so the words beside such a word are marked with it as they were. `unmet` holds `other` exactly when `unread` or `asks_nothing` is not empty, which is where the reader made nothing of some word, as before. What a model leaves of a stretch is judged the same way (`asks_for_nothing`).

**What was asked for and is not in the release is said, and never offered.** A choice is offered only if its edit would change the search. Where the reducer would turn every choice of a thing away because the release holds the thing for no area (section 5.3, rule 15), the thing is not offered and is not unread: it is listed in `not_in_release`, with the target and the label a suggestion would have had, and where its words stand. A person who pressed such an offer was left with no area ranked. In a prompt that is not plain the reader fills `not_in_release` itself. In a plain prompt the edits are made as ever and the reducer turns away what the release lacks, and `not_in_release_of(result, rejected)` names both kinds alike, each thing once: whoever serves a reading calls it, so that what is missing is said the same way whoever read the words. A budget is named `A budget`, or by its amount where it was noticed, and a journey `A journey`.

**A budget edit is made in two where its amount cannot be tested.** A plain prompt makes one budget edit of all it says of the home, and an edit is applied whole or not at all. Where that edit holds an amount the release cannot test and a tenure or a kind of home as well, the reader makes two: what is said of the home, which is applied, and the amount, with its firmness, which the reducer turns away. "Buying a terraced house under £450k" then leaves the search a buyer's, for a terraced house, and says that the budget is missing. Where the amount can be tested it is one edit, as it always was.

**A journey is listened for by its words where the release names no place.** A journey is noticed by the name of its place, and a release that names no place has none to notice. There, in a prompt that is not plain, a phrase that says a journey is heard for itself: a phrase of `EXPECTS_A_NAME` or `GOES_TO`, and "commute", "commuting" and "journey". It is listed in `not_in_release` with the target `commute`, unless a word before it turns it away. In a plain prompt the journey is made as ever, with an empty id, and the reducer turns it away. Nothing is asked about a place (`clarify` is empty), because there is nothing to choose from and no spelling could match.

### 8.2 What each receives and returns

| | `RuleInterpreter` | `ModelInterpreter` |
|---|---|---|
| Lives in | `burro_core` | `burro_api` |
| Needs | Nothing. No model, no network | A `ModelClient`: the adapter of the provider that `choose` turned on. Every test passes a fake, or an adapter with a function that answers in its provider's place |
| Reads | The text, the spec, the release's names | The same |
| Sends out | Nothing | To the model: instructions, the vocabulary of ids and labels, the fixed policy rules, and the text. The words go alone unless the service is set to send the search with them (`BURRO_MODEL_SENDS_SETTINGS` is `yes`): then the canonical spec goes too, with each `place_id` replaced by its position. Never area data, facts or anything from another request |
| Gets back | | `ModelOutput`: the same six arrays, with `destination_text` and `position` in place of `place_id`, and `area_text` in place of `area_id`, plus `status` (`ok`, `off_topic`), `policy_flags` (a list of `avoid_group`, `seek_group`) and `unmet` (each a `category` and the `words` it rests on). Every edit of every kind also carries `words`: the words of the person's text that it rests on, copied as they were typed, at most 600 characters. `position` is the 1-based position of a commute in the spec that was sent, for a `remove`, and `0` for a destination named in `destination_text`. Like `Operations` it has no union and no optional field. Four fields are in the shape and are not read: `direction` on a thing that runs one way, `value`, `strictness` and `provenance`. An `unmet` that is a bare category, as a model answered before it was asked for the words, is read as one with no words |
| Resolves names with | `Names.whole_place`, `whole_area`, on the text as typed; `Names.search_places` for what to offer | `Names.whole_place` and `whole_area`, on the text as typed: the whole of a name, and only one that stands in the sentence the edit rests on. The model never resolves a destination |
| Returns | `InterpretResult`, `interpreter: rule` | The rules' own `InterpretResult` for a prompt the rules read the whole of, and no call is made. For any other, an `InterpretResult` with `interpreter: model`, no edit, and the offers in `suggestions`. Which provider's model is said by route 11, and never by route 1 |
| On failure | Cannot fail; returns `ok` with no edits if it finds nothing | Raises `ModelTimeout`, `ModelCapped`, `ModelRefused` or `ModelError`, and `ModelError` too when the output does not fit the schema. The route falls back to the rule interpreter and sets `degraded`, and `model_refused` where the provider would not read what was typed |

`ModelInterpreter` reaches the model only through `ModelClient`, so its tests use a fake. `ModelReply` holds `output` and the three token counts. The client, the reply and the three failures are defined once, in `providers/interface.py`, so that an adapter's timeout is a timeout to the route.

**Who reads is decided once, as the service starts, and a key alone turns nothing on.** `providers.choose` reads the environment and gives the service a reader and what people are told of it together. A model reads only when a provider is named (`BURRO_MODEL_PROVIDER`), its key is present, its terms are accepted by naming it (`BURRO_MODEL_TERMS_ACCEPTED`), the model is one its adapter was fitted to, and neither cap on calls to a model is nought (section 9.4). DeepSeek never reads what people type, whatever is set (ADR 0023). With any of them missing the rules read, and one warning says which provider is not used and which does not hold (section 10.1). What is offered of a model's answer does not depend on what was sent: the guard holds each reading to the person's words and to the spec the service holds, and never reads what the model was sent.

**The rule-based reader applies a prompt only when the whole of it is plain.** It is a fallback, and the controls on screen are always there, so a wish it does not read costs little and a wish it reverses costs trust. It was put right twice by listing the words that turn a wish round, and no list of them is ever complete. It was then held to reading a sentence only when it knew every token in it, and a sentence made of known words was still read backwards, because no single word is ever the fault: "Pubs are so noisy" is made of words that are each harmless. So it has a grammar of a plain prompt, and what it does with any other prompt is apply nothing and ask (ADR 0012).

```
prompt    = sentence { stop sentence } [ stop ]
sentence  = courtesy | [ opening ] item { joiner [ opening ] item } [ close ]
opening   = [ speaker [ wish ] [ to-do ] ] [ somewhere [ that ] ]
joiner    = "," | ";" | "and" | "or" | "but" | "plus" | "also" | "with"
item      = want | unwant | home | journey | rule | people | no-measure
want      = [ near ] { degree | good | article } thing [ place ] [ nearby ] [ counts ]
unwant    = turn { article | good } thing [ place ] [ nearby ] | thing after-turn
home      = { tenure | size | budget | cheaper }
journey   = cue place [ mode ] | time to place [ mode ] | reach place [ time ] [ mode ]
          | near place | "to get there" time [ mode ] | time
rule      = ( not-in | only-in ) the whole name of an area
```

`grammar.py` holds it, `vocabulary.py` the words it is made of, and `lexicon.py` what a thing is. One token the grammar does not place makes the whole prompt not plain, whichever sentence it stands in. Nothing is then applied, not even a budget that was read: it is all or nothing.

| Part | What it is |
|---|---|
| A sentence | It ends at a full stop, a question mark, an exclamation mark or a line break, and nowhere else. A sentence that asks is not plain: it ends in a question mark, opens with "is", "are" or "am", or puts a verb before the speaker |
| A token | What stands between two spaces, less the marks around it. It is never split at a mark inside it: "don;t" is one token, and one the grammar does not place. A word typed with a hyphen is read whole or not at all. So is one typed with an ampersand between its letters, which is read as the "and" it stands for: "M&S" is "m and s", the name of a chain |
| A mark | A comma and a semicolon join two items. Any other mark between two tokens, a colon, a dash, a bracket or a quote, makes the prompt not plain. The apostrophe of a plural, "five minutes' walk", is part of its word |
| `joiner` | A comma, a semicolon, "and", "or", "but", "plus", "also" and "with" join two items. Two words that join, side by side, join nothing, but for "with" and "also" straight after "and" or "but", which add nothing to it: "quiet but with some culture", "leafy and also quiet". The first word still says how the wish is joined, so a turn before "and with" may reach what follows, and the prompt is not plain: "no pubs and with parks" |
| `opening` | The speaker and nobody else, "I", "we", with a wish in the present tense, "want", "need", "would like", "am looking for", "care about"; what Burro is asked, "find me"; what the speaker wishes to do, "to live", "to be"; and what a place is called, "somewhere", "a nice area", with "that is", "that has". A wish needs no speaker straight after one in the same sentence, "I rent and want a park", nor at the head of a sentence where it is "need", "want" or "looking for". No past tense, no third person and no word that asks is a word of the grammar |
| `thing` | A phrase of the lexicon: the label or the short label of a feature or a vibe the release carries, the name of an end of a scale, or one of the phrases of section 3 that are listed for it in `lexicon.py`. No other word calls up a vibe. **The label of a scale names no end.** "Street character", "pace" and "built age" say which scale and not which way, so a prompt that holds one is not plain, and the scale is offered with both its ends. A scale answers to the name it has on screen and to the name it had: "going out" and "pace", "age of buildings" and "built age", "houses or flats". The lexicon holds each by itself, so that a scale still answers to both on the day the catalogue calls it by the new one. The words people type for an end are as they were: "buzzy", "calm", "lively", "historic", "period", "new build". Until 1.5.0 the label was read as a wish for the high end, and marked as stated. To take a scale off, or to turn its weight down, needs no end, so "I don't care about pace" is plain. A label or an end that is a word for a home, "flats", "houses", "homes", is no thing: it says what is being looked for. A thing may be followed by what a place is called, "a leafy area", "Victorian terraces" |
| `near`, `nearby` | "Near", "close to", "not far from", "by", "walking distance to", "access to", or minutes to the thing, "within 10 minutes of", before it. "Nearby", "close by", "on my doorstep", "around", "around it", "within a ten minute walk", after it. To have access to a thing is to be near it, and what is around a place is near it. Under a word that turns, "no access to parks", neither is a word of the grammar |
| `degree`, `counts` | The step words of section 5.2 before the thing. After it, that it counts: "is important", "matters to me", "would be good", "is essential", "is a must". **An everyday hedge is a word of degree.** "Fairly", "quite", "pretty", "reasonably" and "relatively" stand before a thing, "fairly quiet", or inside the speaker's own wish, "I would quite like", and are a small step. Until 1.5.0 each made the whole prompt not plain, while "a bit" and "slightly" were read. None can turn a wish round: under a word that turns, "not quite leafy", the prompt is not plain, as with any word of degree. A word that weakens the whole of a wish, "maybe", "ideally", "probably", "if possible", "I think", says whether a thing is wanted and not how much, and is still no word of the grammar. **A hedge says how much, and never which way.** With "slightly", "a bit", "fairly", "somewhat", "quite", "pretty" or "reasonably" before it, every thing of the lexicon leans the way it leans without one, by a small step, and "some" is an article and no step at all. "Not too" is a softer "not": it leans as "not" leans, it takes nothing off, and it is never read as a wish for the thing, but for a nuisance, where to want less of it is to care about it. A thing that is only offered is offered the same with a hedge before it. A test holds every thing of the lexicon to each |
| `turn`, `after-turn` | The words that turn, take off and turn down, in the table below |
| `home` | The tenure, the size or the kind of home, and an amount of money with what caps it, in any order, with nothing between them but "for", "at", "of", "is" and the like. "k" and "m" after a number are thousands and millions: "£400k", "400k", "1.5m". A number of "m" with no pound sign, "5m", "1.5m", is as likely minutes, metres or miles, and a word that caps says nothing of which: "within 10m", "5m max", "no more than 0.5m". It is an amount where a word for paying or the home it is for stands in the same part of the sentence: "a budget of 2m", "a detached house up to 2m", "1.5m for a detached house". In a part of its own, "buying, 1.5m max", "1.2m, detached", it is an amount where the sentence says something else of a home and names no place to reach and nothing that is measured as a distance or a walk, whose distance it could be. Anywhere else the prompt is not plain: "near the tube, 5m max" and "I work at Pellam Cross, 30m max" set no budget, and "1.5m" typed alone is offered as a budget for the person to choose. A whole number of "m" that stands alone, "2m", is no amount at all. With or without a point, it is a distance before "from", "to" or "of" and before "away": "1.5m from a park" is no price, and is offered as none. It is made of numbers and closed lists of words, so a wrong reading is a wrong number and not a wish turned round. A tenure that is turned away, "not rent", is read only beside the other, which it agrees with. **An amount to buy a house of no kind is held against a terraced house** (decided on 2026-09-25): "buying a house, about £600k" names a house and no kind of house, a price is held by the kind of home, and a house is no flat. It was applied, and held against what flats sold for. It is applied, held against what terraced houses sold for, and the kind is said to be assumed: `assumptions` holds `segment` for the edit. It is a default the founder may overturn (ADR 0012). Where the release holds no price for a terraced house the prompt is not plain, and which kind it is is asked (below) |
| `journey` | After a cue, the whole of a name of a place. A cue is said of the speaker alone and in the present tense: "work at", "study at", "commute to", "have a job at". **A place that is commuted from is offered, and never applied.** A person commutes from where they live to where they work, and one who is choosing where to live may say "I commute from" of where they work all the same, so nobody can say which the place is: "I work at Pellam Infirmary and commute from Pellam Cross" names a workplace and a home. The grammar makes the sentence, the journey is offered with what was said of it, and a place the release does not hold is asked about. With a time before it the place is one to reach, and is read by the minutes: "a 40 minute commute from", "at most 25-30min commute from". Minutes before "to", "from" or "of" a place, with where the speaker works between them or not: "30 minutes from work at", "within 20 minutes of my office in". **A range of minutes is read as the longer of the two, and is a limit there.** "35-40min", "35-40 minutes" and "35 to 40 minutes" are 40 minutes, which leaves out nothing the person would take, and the edit is marked as assumed. Whoever gives a range has said how long is too long, so the 40 minutes are `hard`. The second number must be the greater, and a range of anything but minutes, "2-3 bedrooms", "£1,500-£1,800", is two numbers of which the reader sets neither. "There" is the one place named earlier in the same sentence. Minutes with no place, "20 minutes tops", are read beside the one journey of their sentence, and "a 40 minute commute" is the limit of each journey of the prompt. How they are travelled and whether they are a limit stand with the minutes: "a 40 minute commute on foot" is 40 minutes on foot, and "no more than 35 minutes" is a limit. Until 1.5.0 only the number was kept. Where the prompt names no journey for them to be the limit of, where a journey was given other minutes or another way of travelling, or where two such wishes differ, the prompt is not plain |
| `rule` | "Only in X", "not X", "avoid X" and "anywhere but X", before the whole of an area's name. "In X" is no rule, and nor are "except X" and "unless it is X" |
| `people` | A phrase the policy lexicon hears, with whatever is said of it. It makes no edit, and the notice is given (section 8.4) |
| `no-measure` | A phrase for what Burro has no measure of. It makes no edit, and its category is in `unmet` |
| Side by side | A home, or what makes no edit, may stand before a journey or a wish with no word between them: "2 bed within 30 minutes of the works", "broadband near a park". After a thing, only a wish that is led by "near" or a journey: "a quiet street not far from a station". A thing that was turned stands alone: "no pubs near a park" is not plain, since it may be said of the pubs by the park |

The words that turn, and what each says. No other word is ever read as one.

| The words | What they say | Read where |
|---|---|---|
| "no", "not", "without", "avoid", "don't want", "don't like", "not near" | The thing after them is wanted not at all | Before a thing |
| "less", "fewer", "low", "not too", "not many", "not much", "not so", "not very" | The thing after them is wanted less | The same |
| "don't care about", "don't need", "don't mind", "not bothered about", "ignore", "remove", "get rid of"; after the thing, "is not important", "doesn't matter" | The weight is taken off | Before the thing, or after it |
| "care less about"; after the thing, "is less important", "is not essential", "is not a priority", "matters less", "low priority" | The weight is turned down | Before the thing, or after it |
| "worry about", "worried about", "concerned about" | It troubles the person | Before a nuisance, where it is the wish itself. Before anything else the prompt is not plain |
| "up to", "under", "within", "below", "max", "less than", "around", "about"; after the number, "max", "tops" | The most a number may be. Softly, but for the three in the next row | Beside a number of minutes or of money. "About" and "around" may stand between another of these and the number, "within about 30 minutes", "up to around £1,500", and the number is the most it may be all the same |
| "max", before the number or after it; "up to" beside money; "within" beside minutes | The same, as a limit. Decided on 2026-09-24 | "Up to" beside minutes and "within" beside money stay soft |
| "no more than", "not more than", "at most", "cannot go over", "no further than" | The same, as a limit | Beside a number of minutes or of money |
| "too" | "As well" | After the last item of a sentence. Anywhere else it is no word of the grammar |

What a turned thing becomes depends on the thing:

| The thing named | Example | Edit |
|---|---|---|
| A nuisance (section 3.1) | "less noise", "no pollution", "I worry about burglary" | A step up, in its one direction |
| A feature whose polarity is `either` | "fewer pubs", "no pubs" | A step up with `direction: less` |
| An end of a scale | "not buzzy", "no nightlife" | A step up towards the other end: Going out towards Calm |
| A vibe with one way, or any other feature | "no parks nearby", "not near a station", "not leafy" | `remove`. Where less is wanted and not none, "less green space", a small step down. No weight is ever raised |
| A campus | "not near a university" | None. It is a request about who lives somewhere (section 8.4) |
| A word with two meanings, where the release carries no Gritty | "not gritty" in a release of variant `a` | None, and `upkeep` in `unmet`: it is no wish for fewer works |

Four rules stand over the grammar, and a prompt that breaks one is not plain:

| Rule | What it says |
|---|---|
| One turn, one thing | A turn governs the thing straight after it, and the things joined to that by "or": "no pubs or bars". A thing joined to a turned thing by a comma or "and", with nothing said before it, makes the prompt not plain, because the reader cannot say whether the turn reaches it: "no parks, playgrounds or schools". "But", a wish of the speaker's, a turn of its own, and a word before the thing that is the thing's own, such as "near", "good" or "low", begin a new wish: "no pubs, but a park nearby", "less noise and clean air". **What is said after a thing never begins a new wish.** "Nearby", "close by", "on my doorstep", "within walking distance" and "would be good" may be said of every thing of a list, so after "or" the turn carries over them, "I don't want pubs or restaurants nearby" is fewer of both, and after a comma or "and" the prompt is not plain: "avoid pubs and restaurants nearby". Until 1.5.0 the last thing of such a list was read as a new wish and raised. After "or" nothing begins a new wish but a turn of its own, so "no pubs or good restaurants" is not plain. What is said to count after the last thing of a list, "parks, playgrounds and schools are not important", "no parks or pubs are important", may be said of each, so that is not plain either. A turn that is carried is held to the rules below as one that was typed: what troubles a person is carried to a nuisance alone |
| Never both | A thing that is both wanted and turned away in one prompt, both ends of one scale, both tenures, two budgets, or one area to be left out and to be the only one |
| A nuisance | It is a thing only under a turn, in a phrase that says low, "less noise", "low crime", "clean air", or where it is said to count and not to be liked: "I care about noise", "noise matters to me". Named alone, liked, or said to be essential, it makes the prompt not plain |
| A phrase that says which way | "Spacious" and "low crime" say which way the thing is wanted. Under a word that turns they are not plain |

**What is noticed in a prompt that is not plain.** Every thing, every whole name, every amount of money and every word for the tenure is noticed, wherever it stands. Each is offered once, however often it is named, in the order they stand, with the directions a person may choose. The reader chooses none of them.

| What was noticed | `target` | Choices |
|---|---|---|
| A feature whose polarity is `either` | `feature:<id>` | `more` and `less`, each a step up in that direction: "More pubs and bars", "Fewer pubs and bars" |
| A nuisance | `feature:<id>` | `less`, which is to care about it: "Less transport noise" |
| Any other feature | `feature:<id>` | `more`, a step up, and `less`, which takes its weight off |
| A scale | `tag:<id>` | `more`, towards its high end, and `less`, towards its low end: "Towards Buzzy", "Towards Calm" |
| A vibe whose recipe holds recorded crime | `tag:street_character` | As a scale. Each choice says so on its face, "Towards Gritty, counting recorded crime", and `note` names what is counted and carries the caveat of every crime figure: "Gritty counts recorded criminal damage and recorded anti-social behaviour. Recorded crime depends on what is reported, and locations are approximate." |
| A vibe with one way | `tag:<id>` | `more`, a step up, and `less`, which takes it off |
| The whole name of a place | `commute` | `more`, which adds the journey: "Add a journey to Pellam Cross". Where minutes stand straight before the place the choice holds them and its label says so, "Add a journey to Pellam Cross within 30 minutes", and the suggestion rests on those words too. Where the words against the minutes make them a limit, or they are a range, the choice holds a firm limit, says "of no more than 30 minutes", and rests on those words as well. It holds no mode |
| A journey, in a sentence the grammar makes | `commute` | `more`, which adds the journey with all that was said of it, and says all of it: "Add a journey to Pellam Cross of no more than 40 minutes by bike". Minutes said apart from the place are its limit, as in a plain prompt. Where they were a range, `note` says so: "You gave 35 to 40 minutes. Burro has taken the longer." It rests on the whole of the journey's words, and the name in it is not noticed a second time |
| A place the release does not hold, in a sentence the grammar makes | none | It is asked about, as in a plain prompt: `operations` holds the question, an edit with an empty id and what was said of the journey, and `clarify` points at it with what `search_places` offers for the words. It is the one edit a prompt that is not plain may hold, and the reducer turns it away, so nothing is applied |
| The whole name of an area | `area` | `more`, which looks only there, and `less`, which leaves it out: "Look only in Cindermoor", "Leave out Cindermoor". A name that is an area's and a place's is a journey after a cue, and an area anywhere else |
| An amount of money | `budget` | `more`, which sets the amount and no more: "Set a budget of £1,800 a month". It holds a tenure only where the amount cannot be of the tenure the search holds, and the label then says which: "Set a budget of £450,000, to buy". Where the words against the amount say the most that can be paid, "max £400k", "up to £1,800", the choice holds a firm limit, says "Set a budget of no more than £400,000, to buy", and rests on those words too |
| The size or the kind of a home | `budget` | `more`, which sets the kind of home the search can hold for it: "Set a 2-bedroom home". It is one offer for the whole of what was named, "a 1 bed flat", and it is made whether or not the search already holds it. See below |
| A word for renting or buying | `tenure` | `more`, which sets it |

**A choice holds only what its label says.** Every field of the edit of a choice that is not a sentinel is named on the face of the choice: an amount, a tenure, a kind of home, a place, a number of minutes, an end of a scale. Until 1.5.0 a budget carried the size of home and the tenure that stood beside it, and a journey the minutes, and the label said neither. A test holds every choice of a set of prompts to it. And what a suggestion rests on is never reported as unread.

**What was turned away is not offered to be set.** A journey, a tenure and a kind of home have one direction. Where a word that turns a thing away stands before one, "I don't rent", "nowhere near Pellam Cross", "at least 45 minutes from Cindermoor Works", the one choice there is would be the opposite of what was said, so none is offered, and the words are reported as unread. For an area, to look only there is not offered. The words that turn away are the words that turn (section 8.2) and the words of the written list that say none, less or far. The words that lead in to the thing, "to be near", "within 40 minutes of", are passed over, as far as a mark. A word that only weakens, "maybe", turns nothing away.

**A place to stay away from is heard, and no journey to it is offered** (decided on 2026-09-25, ADR 0012). In a prompt that is not plain a place that is named is offered as a journey to it, and one press may take a journey. So of "my ex lives at Pellam Exchange, 30 minutes away at least" one press added a journey to that place, and ranked the person by how near they were to it. A place is kept away from where its sentence holds a word for far, before it or after it, in its clause or in another: "far from", "well away from", "as far as possible from", "and nowhere near it", "30 minutes away", `STAYS_AWAY` in `vocabulary.py`. And where it holds a least against a number of minutes: "at least 30 minutes from", "over 30 minutes", "30 minutes or more", `AT_LEAST`. Lines that no mark ends are read together. Such a place is offered with nothing to choose but to leave it out, and its `note` says why in one sentence: "Burro cannot rank on being far from a place." Nothing is added, by one press or by any. What says near is passed over, whatever word it holds: "not far from", "within walking distance of", "no more than 30 minutes". So is a word for far or for a least that a word before it in its clause turns round: "can't be more than 45 minutes" is the most a journey may take, and "neither of us is more than 40 minutes away" is too. A sentence that asks how far a place is wishes nothing.

**A place that may be somebody else's is offered, and no press takes it with others.** "My ex lives at", "my mate works at", "his mother is in", "she's at", and a place that was left, "we moved from". Its `note` says "Burro cannot tell whether you must reach this place. Add it if you must.", and it carries no guess.

| What is asked of the clause before the name | What it makes of the place |
|---|---|
| The speaker's own words for a journey stand straight before the name: "I work at", "my boss and I work at", "I need to get to" | A place to reach, whoever else is named |
| Somebody is named who is of the household, `OF_THE_HOUSEHOLD`, and no word says that they live there: "my partner works at", "and my partner at", "my husband commutes to" | A place the household must reach |
| Somebody is named who is of the household, with a word of `LIVES_THERE`: "my partner lives at" | It may be somebody else's: where they live is no place the words say must be reached |
| Somebody else is named, `SOMEBODY_ELSE`, who is not of the household: "my ex", "my boss", "my mum", "he", "she's", "their" | It may be somebody else's |
| The place was left, `LEFT_BEHIND`: "we moved from" | It may be somebody else's |
| Nobody else is named: "my kids' school is", "close to" | Read as it was |

Who is of the household is a closed list, and so is every other. Where the words do not say, the place is offered and Burro does not guess. A model's reading of either kind of place is held to what the rules say of it: of a place to stay away from it is dropped (check 3), and of a place that may be somebody else's it is no guess ("the wish is somebody else's").

**A home is offered whenever it is named, for a buyer and a renter alike.** A rent is published by the number of bedrooms and a price by the kind of home, so each tenure has kinds of home of its own (section 4), and "a 1 bed flat" is one thing to a renter and another to a buyer. Until this was mended a home was offered only where to choose it would change the search, and a buyer's bedrooms and a renter's terraced house were reported as unread, with no word of why.

| What is decided | How |
|---|---|
| Which tenure the home is for | The one the words of the prompt name, by a word for renting or buying that is not turned away, or by an amount that can be of one tenure alone: a rent is paid by the month, and no rent is as high as a price. Where they name none, or both, the tenure of the search |
| What the choice sets | For a home to rent, a studio or a room where one is named, and the number of bedrooms otherwise. For a home to buy, its kind: a flat, a terraced, a semi-detached or a detached house. It holds the tenure only where that is not the tenure of the search, and the label then says so: "Set a flat, to buy" |
| What `note` says | What was named and cannot be held. For a home to buy with bedrooms: "Burro holds what homes sell for by kind of home, and not by the number of bedrooms." For a home to rent of a kind that is held for buying alone: "Burro holds rents by the number of bedrooms, and not by kind of home." For a studio or a room to buy: "Burro holds what a studio or a room costs to rent, and not to buy." A flat to rent is said of most homes that are let, and has no note |
| Where nothing of it can be set | "A two bed house", where the person is buying: the offer holds the note and no choice but to leave it out. A flat to rent with no bedrooms named says nothing the search could hold, and is unread |
| Nobody is moved to the other tenure for having named a home | But a person who has chosen no tenure, whose search is the renter's default, and who names a kind of home that is held for buying alone: "a detached house" is offered as "Set a detached house, to buy" |
| A budget to buy a house of no kind | "A house", "a two bed house", where the words name no kind of home that a price is held by, anywhere in the prompt. The amount is offered once for each kind of house, in this order: terraced, semi-detached, detached. Each way holds two edits: the kind, and then the amount as it was worded, each with the tenure where it is not the search's own. Its `id` is the kind, and it says all of it: "Set a budget of £600,000 to buy a terraced house". **The first way is a terraced house, which Burro takes**: its edit of the kind is `inferred`, so that a client marks the kind as assumed after the press, it carries the guess where the budget was plainly said, and `add_all` names it. The edit of the kind of any other way is `ui_edit`: a kind that a person presses is theirs. The `note` says why in one sentence, of the release that is served: "You named no kind of house, so Burro has taken a terraced house, the least dear kind in most areas. Semi-detached and detached are one press away." That it is the least dear is said only where it is, in more than half of the areas that hold a price for any kind of house. An area that holds no price for a terraced house is held to the price of no other kind: it is ranked, and `untested_filters` says that the limit could not be tested. A way whose kind the release holds no price for is not offered. **Where the release holds no price for a terraced house, which kind it is is asked**: the offer says "A budget of £600,000 for a house: semi-detached or detached?", its `note` says "Burro holds what houses sold for by kind of house, so it asks which kind.", no way is the guess and `add_all` names none. Where it holds a price for no kind of house the budget is said to be missing, in `not_in_release`. **A house is never held against what flats sold for**, whoever reads: a model's reading of the same amount rests on words the rules offer with a note, and is dropped (check "the rules offer what is nearest"). A rent is held by the number of bedrooms, and a house to rent is read as it was |

**In a plain prompt a home is applied as it was.** The edit holds what the search can hold of it: "max £350k for a 1 bed flat" is a flat to buy at £350,000, and the bedrooms are left out. Where no edit can be made of it at all, "a two bed house" typed by a buyer, its words are reported as unread and `unmet` holds `other`. It was passed over with no edit and nothing unread, which told the person nothing. It is not offered there: the status of a plain prompt would then say whether the search is to rent or to buy, and a status is kept about a call (section 10.1).

`ignore` is offered with every suggestion. A choice is never offered if its edit would be rejected, and but for a home none is offered if its edit would change nothing, so `less` of a thing with one direction is offered only where the spec holds a weight for it, and a thing of which nothing can be chosen is not offered. A campus is never offered, and nor is a word that names no place after a cue: "I commute to school" offers no schools.

What the rules read and how, where this contract was silent:

- Provenance is `stated` when the text names the thing and `inferred` when it is read into looser words. "Low crime" is stated and weights crime. A word of section 3 marked as read into a vibe, "calm", "lively", "period houses", is `inferred`, and its chip says "assumed".
- **Little traffic is asked for in the plain ways a person says it.** Since engine 1.15.0. Each is a phrase of the lexicon, of a nuisance, so less of it and none of it are the wish itself, and a phrase that is only named, or that stands in words the grammar does not place, is offered one way and never applied:

  | Words | What they are read as |
  |---|---|
  | "no traffic", "less traffic", "low traffic", "no busy roads", "without heavy traffic" | `feature:road_traffic_nearby`, as less of it. Applied where the whole prompt is plain |
  | "away from main roads", "not near a main road", "no main roads" | `feature:road_major_exposure` and `feature:road_traffic_nearby`, each as less of it. A main road is asked of as the homes that stand beside one and as the traffic near home. A release that ranks no area on the first by itself, as a build of London does, turns that edit away as `not_in_release` and applies the second |
  | "quiet road", "a quiet road", "quiet roads" | `tag:quiet_residential`, as "quiet street" is: a quiet road is a quiet street, and the vibe holds the traffic |
  | "not on a busy road", "I don't want to live on a busy road" | Nothing is applied: "on" is no word the grammar places. `feature:road_traffic_nearby` is offered, with the one choice "Less traffic nearby" |
  | "traffic", "busy roads", "I like being on a busy road" | Nothing is applied: a nuisance that is only named, or that is liked, makes no edit. It is offered one way, and may be left out |
  | "traffic noise", "less traffic noise" | `feature:noise_exposure`, as it was: the longer phrase is the noise |

- **What Burro has no measure of is offered what is nearest, and says what it lacks.** The first words a newcomer reaches for led nowhere: each was met with no edit, no suggestion and a line about settings. Each is now a phrase of the lexicon that is never applied. A prompt that holds one is not plain, what is nearest is offered as a choice, and the `note` of the suggestion says what Burro cannot do and why. `Target.note` in `lexicon.py` holds each.
- **Who lived somewhere is offered, towards more, and never applied.** Decided on 2026-09-24 (ADR 0006, as amended). A phrase for those Burro counts is a phrase of the lexicon with a note, so a prompt that holds one is not plain and nothing of it is applied. Each offer has one way to be taken, more of what is counted, and a way to leave it out. Its note is "Burro counts who was living there at the census of 2021. It measures places first." The phrases are the labels and short labels of the four measures and the two vibes, and these:

  | Words | What is offered |
  |---|---|
  | "young professionals" | Young professionals |
  | "young people", "young adults" | More young adults, which is residents aged 20 to 34 |
  | "people my age", "people our age" | More young adults and More older residents, each under a note that begins "What age? Burro counts residents aged 20 to 34, and residents aged 65 and over." |
  | "a family area", "families", "young families", "lots of families", "full of families", "other families" | Family area |
  | "family friendly", "good for kids", "good for families" | Family area and Family amenities, which the person chooses between. Family amenities carries no note: it counts places alone |
  | "older and quieter" | More older residents, and Quiet streets |
  | "retirees", "pensioners", "older people", "old people", "elderly" | More older residents |

  A word that turns a wish, or takes a thing off, makes the same words a wish for fewer of a group of people: "no families", "fewer young professionals", "not too many young people", "away from retirees", "anything but elderly", "too many families". Such a wish draws the notice of section 8.4 and nothing else. A prompt that draws the notice is offered nothing that counts who lives somewhere, whichever of its words drew it, and the rest of it is served. `may_ask_for_fewer()` in `interpret.py` is the rule: a word that turns, takes off, turns down, troubles or doubts, in the clause the words stand in.

  | The words | What is offered | What the note says |
  |---|---|---|
  | "safe", "safer", "safety", "feel safe", "unsafe", "dangerous" | `feature:crime_violence_robbery` and `feature:crime_burglary_theft`, each with the one choice "Less recorded ..." | "Burro cannot say how safe a place is. It can count recorded crime. Recorded crime depends on what is reported, and locations are approximate." |
  | "leisure centre", "sports centre", "swimming pool" | `feature:venue_gym_per_homes`: "More gyms nearby" | "Burro cannot tell a swimming pool or a leisure centre from any other place to train. The nearest it can count is gyms and fitness studios." A gym is asked for by name, and is applied: "gym", "gyms", "near a gym", "yoga" |
  | "community", "sense of community", "community feel", "community spirit", "neighbourly" | `tag:village_feel`: "Add Village feel" | "Burro cannot measure whether neighbours know each other. The nearest it can count is a village feel: a high street in a conservation area, homes that stand apart and period homes." And then what a rough guide says of itself |
  | "garden", "big garden", "large garden", "private garden", "own garden", "outdoor space" | `feature:land_gardens`: "More gardens" | "Burro cannot see whether one home has a garden. It can count how much of an area is residential garden." |
  | "affluent", "posh", "well heeled", "upmarket", "smart", where the release carries Gritty | Three, for the person to choose from, in this order: `feature:brand_mix`, "Mix of brands", with the one choice "More premium"; `tag:street_character`, with the one choice "Towards Polished, counting recorded crime"; `feature:price_median`, "What homes sell for", with the one choice "Dearer", and `feature:homes_higher_bands`, "Homes in the higher council tax bands", with the one choice "More homes in the higher council tax bands" | "Burro measures places, not the people in them." and, of the scale, what it counts |
  | "cheap and cheerful", "unpretentious", "down to earth" | `feature:brand_mix`, with the one choice "Less premium" | "Burro measures places, not the people in them." |
  | The name of a chain of the catalogue, however it is commonly typed: "Waitrose", "near a Waitrose", "a Gail's nearby", "M&S", "marks and spencer", "co-op", "pret a manger", "caffè nero" | The distance to the nearest place of that chain: `feature:brand_waitrose`, "Nearer a Waitrose", with that one choice | "Burro finds a chain by the brand its file of places gives a shop. The file misses some shops, and lists some that have closed." |
  | "identity", "a real identity", "character", "characterful", "its own feel", "a proper neighbourhood", "soul", and "soulless" and "bland" | Three, for the person to choose from: `tag:village_feel` "Add Village feel", `tag:built_age` "Towards Historic" and `feature:highstreet_access` "Nearer a town centre" | "Burro cannot measure the character of a place. The nearest it can count are a village feel (rough guide), the age of the buildings and a town centre nearby. Choose any that fit what you mean." The offer of Village feel says after it what a rough guide says of itself |
  | "on the up", "rising", "rising prices", "prices rising", and "up and coming" where the release carries no Gritty | `feature:price_rise_5y` and `feature:price_rise_10y`, each with the one choice "A steeper rise" | "Burro cannot see where a place is heading. It can count how far what homes sold for has risen. A rise is of prices that were paid, and promises nothing." |
  | "up and coming", where the release carries Gritty | The two rises, and `tag:street_character` as it was offered before a rise was held, each with both its ways. `change_over_time` is no longer in `unmet` | "Burro cannot see where a place is heading. It can count how far what homes sold for has risen, and say where a place stands on Gritty today. A rise is of prices that were paid, and promises nothing." and, of the scale, what it counts |

  **A word for a smart area is read as of the place, and never of who lives there.** Decided on 2026-09-24: "affluent" and its kin have four readings, each of the place. The first is which chains of grocers, gyms and coffee stand within reach, towards premium (ADR 0026). The second is the polished end of Gritty. The third is homes that sell for more than the middle of the city. The fourth is the share of the homes of a place in the higher council tax bands. None is what people earn or who they are, and no id exists that could express either of those (section 3.1). **The mix of brands is offered first**, one way where the other two are, "More premium", and both ways where they are, "More premium" and "Less premium". It is never applied from a word, it stands in no vibe, no likeness is counted on it, and nothing weighs it by default. **"Cheap and cheerful", "unpretentious" and "down to earth" are offered the other end of the mix**, and nothing else: none is a wish for recorded crime, and Burro gives no verdict on what is cheap. **A chain a person names is offered as the distance to the nearest place of it**, and is never applied, since the file of places misses some shops. Where a release holds no place of the chain, the offer is listed with what the release cannot answer. Each is offered one way where the grammar makes the sentence the word stands in: a person who types "slightly affluent" is not offered Gritty. In any other sentence nobody can say which way the word is meant, "not posh", "anything but posh", "posh is not for me", so both ends are offered, and the end that was meant is among them. **What homes sell for is offered beside them.** `price_median` is the median price paid for a home of any kind, as its publisher gives it for the area. It is offered one way where the first is, "Dearer", and both ways where the first is, "Dearer" and "Cheaper". It is never applied from a word, it stands in no vibe, no likeness is counted on it, and nothing weighs it by default. **The higher bands stand beside the price: `homes_higher_bands`, the share of the homes of a place in council tax bands E to H.** It counts homes and not people, it is offered exactly as the price is, and the note of each is "Burro measures places, not the people in them." A band is what a home would have sold for in 1991, so the share is no price and is never shown as one. Where a release carries no Gritty the mix, the price and the bands are the three readings of the word, and "smart" is a word for upkeep there. Where a release holds no price, the offer is listed with what the release cannot answer. A word for people beside it is still a request about who lives somewhere, and is offered nothing: "posh people", "affluent families", "upmarket residents", "posh locals", "affluent households", "down to earth locals", "unpretentious people" (section 8.4).

  **A word for a place on the rise is read as of what homes sold for.** Decided on 2026-09-24: "up and coming", "on the up" and "rising" are offered `price_rise_5y` and `price_rise_10y`, the median price paid in the last year for each £100 of the median five and ten years before. Each is offered one way, a steeper rise, where the grammar makes the sentence, and both ways anywhere else. Neither is ever applied from a word, stands in a vibe or in likeness, or is weighed by default. The note says that a rise is of prices that were paid and promises nothing: it is no forecast, and the verifier still refuses "up and coming" in any sentence Burro writes (section 7.4). "Gentrifying" and "gentrification" say who is moving in, and stay with `change_over_time` in `unmet`.

  **A word for character is offered three ways, whatever is said of it.** "Soulless" and "bland" name a place without character, and "not bland" turns that round again. None is a wish for the opposite of a village feel, and nobody can say which of the three a person means by any of them. So each is offered the same three, one way, under a word that turns as without one, and "I don't care about character" takes nothing off. A word that is offered rests on all that was said of it, "slightly affluent", "a bit of character", where the grammar makes the sentence it stands in. **The note names what is offered, and nothing else.** A release that places no area on one of the three offers the other two, and says of the one that it is not in this data. The note then names the two: "The nearest it can count are the age of the buildings and a town centre nearby. Choose either or both." Of one it says "The nearest it can count is", and no more. `no_identity()` in `lexicon.py` makes the note, and says it of all three word for word as above. It names Village feel with its label, "a village feel (rough guide)", on a release that places an area on it, and names none on a release that does not.

  **A vibe that is a rough guide is offered, and never applied.** No word applies Village feel, its own name among them: "villagey", "a village feel", "I like villages". Each is offered, one way, and the note of the offer is the label and the sentence: "Rough guide. Of the areas it puts highest, about half read as villages to people, and it takes some busy main roads and some grand inner streets for villages." Where the offer holds another note, the label and the sentence stand after it. A prompt that holds such a word is applied in no part, as a prompt that holds "safe" is not: the rest of it is offered beside it. To turn it away, "not villagey", is no wish for it, and takes it off a search that holds it. `is_a_rough_guide()` in `lexicon.py` says which phrases reach one, and `says_rough()` in `catalogue.py` what is said.

  **"Safe" is the hardest.** The rule that crime needs an explicit request stands (section 5.3, rule 8). "Safe" names no crime, so it sets none counting. The offer names recorded crime on the face of the choice, so a person who presses it has asked for it by name: the edit is `ui_edit`, as any control is. Until 1.5.0 "safe" was applied as an inferred edit, which the reducer turned away, and the person was told to ask by name and not told the name. Beside a wish that names the same thing outright, "somewhere safe, with low crime", the person has asked by name, the word adds nothing to what they said, and the prompt is plain.

  **The offer of a budget to rent says what the rents are.** Where a way of the offer sets an amount that would be held against a rent of a wider place, its `note` holds two things: that each rent is of a postcode district or of a whole borough and not of one area alone, and what the publisher advises, `RENT_CAUTION`. The words are core's, and quote no figure. One press takes such a budget as it takes one to buy: `plainly_said` and `in_add_all` decide it, and a note of a budget keeps no way out of `add_all`. Where it is set as a firm limit, the way says "Areas where the middle rent is more than 25% over it are left out."

  **A wish that holds a note is chosen by its own label, and never with others at once.** The note is what a person should know before they choose, so `add_all` names no way of a feature or a vibe whose `note` is not empty, and a client that offers to add several things in one press adds the way `add_all` names and no other. For recorded crime this is the rule of section 5.3 and not a courtesy: a button that adds "all 5" names no crime, so to press it is not to ask for crime by name. A client shows the `note` beside the choice, and a choice of recorded crime only under its own label. **A kind of home is taken with its note**, where it was plainly said (section 8.2, decided on 2026-09-25): the note says which part of what was said the search cannot hold, "Burro holds what homes sell for by kind of home, and not by the number of bedrooms", and is shown with the offer before the press. A journey that carries the guess is taken with its note too, which says which of two numbers was taken: "You gave 35 to 40 minutes. Burro has taken the longer."

  **"Cheap" is heard, and nothing can be offered for it.** What is cheap is a verdict Burro does not give, and a budget is a number only the person can say. "Cheap", "inexpensive", "cheap rent" and "low rent" are phrases of `affordability_verdict`: they make no edit, the category is in `unmet`, and the person is told in fixed words. No choice is offered, because no choice could be made without an amount.
- **A word with two meanings is read as its place part alone.** Where a release holds no recorded crime and carries no Gritty, "gritty", "edgy" and "raw" are read as Works and warehouses, the `word` assumption quotes the word, and `street_cleanliness` is in `unmet` beside the edit, because Burro has no measure of how clean a street is. "Polished", "smart" and "well kept" make no edit there, with `upkeep` in `unmet`. `lexicon_of(variant)` and `no_measure_of(variant)` hold the words for each.
- **Crime counts only when it is asked for by name.** Gritty holds recorded incidents. "Gritty" is its name and the name of its high end, and "polished" the name of its low end, and each is applied as any end is: to type "gritty" is to ask for the vibe by name, and so for the recorded crime it counts, and the chip and the card of a vibe whose recipe holds recorded crime say that it does. "Street character", the name the scale had, names no end and is offered with both. "Industrial", "warehouses", "railway arches" and "works and warehouses" are words for a part of Gritty, which no release that carries Gritty serves as a vibe of its own. So each is read into Gritty as "edgy" is, and offered. Where a release holds no recorded crime they ask for Works and warehouses, and are applied. "Safe" names no crime and is never applied: recorded crime is offered by its name, and the person is told that Burro cannot say how safe a place is. "Edgy", "raw", "rough" and "well kept" are only read into it, so a prompt that holds one is not plain: nothing is applied, and the scale is offered with both its ends, with what it counts said in the offer. Until 1.5.0 they were applied as assumed, and ranked areas by recorded damage for a person who had not named it.
- **The words for a food shop, a surgery and a pharmacy** weigh the distance to each, which is a part of Everyday on foot: "food shop" and "supermarket" `grocery_walk`, "GP", "doctor" and "surgery" `gp_walk`, "pharmacy" and "chemist" `pharmacy_walk`. "Shops" is the town centre, `highstreet_access`, and "walkable" and "everything on foot" are the vibe, the second as assumed. Until catalogue version 13 a word for a surgery or for a pharmacy was heard as what Burro has no measure of, `health_services`. Each is a thing now, so where a release carries no figure for one the wish is listed with what the release cannot answer (section 8.1), by the name "Nearer a GP surgery" or "Nearer a pharmacy". A dentist is still `health_services`. "Doctor", "GP" and "chemist" are words for a person too, and "surgery" for an operation. Each is the place only where the words beside it say that it is wanted near or is to be reached: "near a doctor", "a chemist nearby", "10 minutes from a GP", "she needs to get to a doctor". In a sentence the grammar makes, what says near of a list says it of each thing of it: "a GP and a chemist nearby", "near a park and a doctor". In any other sentence the words must stand straight beside the thing, with no more than an article or a good word between. The speaker who says no wish says who they are: "I'm a chemist, station nearby" asks for a station. Anywhere else the word is one that nothing was made of, so "I am a doctor" is offered no surgery and "I'm a chemist" sets nothing, and the answer says where the word stands. So it is of the word alone in a list where nothing says near: of "parks and a doctor" the park is offered, and nothing is made of the doctor. The founder decided on 2026-09-25 that it stays so. "GP surgery", "GP practice", "doctor's surgery" and "pharmacy" are places wherever they stand.
- **The words of a vibe that was retired** weigh the one feature that took its place: "creative" and "arty" `culture_venues_per_homes`, "a good high street" `highstreet_access`, which is the distance to a town centre, "a university" `university_proximity`, "river", "canal" and "waterside" `water_access`.
- A name is tried with its article and without, because some names are written with one: "the Clinkers" finds a place whose alias is "The Clinkers". No name of the synthetic release is written with one today.
- The rules never produce `setting_ops`, never remove a commute and never move a commute's minutes from words.
- **Generic words are not names.** After "work at", "study at", "commute to", "travel to" and "work in", the words "work", "the office", "school", "uni", "university", "college", "home", "my job", "town", "the city" and the like name no place. No journey is added and nothing is asked, because there is nothing to choose from, and the word is not offered as a wish for schools or for a campus either. A name that begins with one is still a name: "Wexmoor University" is found. `GENERIC_PLACES` holds the words.
- Every place and area that the text names in full is found before anything is read, whatever stands before it. So the "green" of Dulcimer Green is never read as a wish for greenery. A name with no cue before it makes the prompt not plain, and is offered. **A name is matched on the text as typed**, with nothing but a space between its words: it is never put together across a comma, a bracket, a hyphen, a slash, quotes or a line break. "I work at Foxholt (market research)" names Foxholt and not Foxholt Market.
- How much of a name a cue needs. After "N minutes to" and "work at" a name is expected. The whole of a name is taken. Words that are the whole of no name are what the person calls the place: they are asked about, with what `search_places` offers for them, and add no journey, because the edit carries no place. They are asked about only where nothing else is said after them, and where no whole name stands among them: "I work at Pellam" asks which, "I work at Pellam Infirmary sadly" is not plain. It is the one place where words the grammar does not hold are not doubt, because a question adds nothing to a search. So it is asked in a prompt that is not plain too, where the grammar makes the whole of the sentence the words stand in and no sentence beside it takes it back: "Maybe somewhere leafy. I work at Quillhaven Lane." asks which place was meant and offers Leafy. Such a place was once reported as unread, and the person was told nothing of it. After "near", "close to" and "not far from", what follows is as often no name at all, so only the whole of a name or an alias is taken and nothing is asked: "not far from a park" excludes no area, though "far" begins Farrowmere, and "near Pellam" adds no journey, though two places begin with it.
- **The words of Well connected.** "Well connected" is the vibe by its name, and is stated. "Transport links", "good transport", "near the tube", "near a tube", "close to the underground" and "good buses" are read as the vibe too, as inferred: each names one part of it. "Near a station" and "near a train station" are the distance to the nearest station, `station_walk`, as they were: it is what the words say, a search weighs it before anything is said, and "not near a station" takes it off. Near a station is about a 10 to 15 minute walk, which is 800 m in a straight line: decided on 2026-09-25, and said where the measure is offered (section 7.5). "Tube" and "underground" alone are no wish: each is a way of travelling, "35 minutes by tube", and the grammar holds them as that.
- **Two phrases that overlap.** The reading that leaves the fewest tokens as words the grammar does not hold is taken, and of two that leave as few, the one made of the longest phrases. "Good transport links" is "good" and "transport links", though "good transport" is a phrase too, and "Wexmoor University" is the campus and not Wexmoor.
- **What is heard rests on the words said of it.** A notice and an `unmet` category rest on the phrase that was heard and on the words of the grammar beside it, as far as a mark, a word that joins, or a thing. So "can I afford it" is one request, and leaves nothing unread. A word the grammar does not hold is unread wherever it stands: "fast broadband" is `broadband` and `other`.
- **A campus in a prompt that is not plain**, or under a word that turns, is a request about who lives somewhere, by word or by name: no edit, no suggestion for it, and the neutral notice (section 8.4).

`sentences_of(text, names, release)` says of each sentence where it starts and ends and whether the grammar makes it, it does not ask, and no sentence beside it takes it back (`known`), whether it holds a word the reader has a turning rule for (`turning`), whether it holds a word of the written list of doubt or a token with a mark inside it (`doubt`), whether it asks (`asked`) and whether a sentence beside it takes it back (`taken_back`). A sentence that holds doubt and names nothing, "No thanks.", "Not really.", is said of the sentence before it and of what is listed beside it, as far as the list goes. The rule-based reader has no use for this: a prompt that holds such a sentence is not plain, and nothing of it is applied. It is for a caller that must hold edits the reader did not make to the same test, the model-backed interpreter. So is `RuleInterpreter.by_sentence(request)`, which gives the edits of every sentence that is `known`, whatever the other sentences are, each with the words it rests on. It is what the reader would make of each sentence alone, and it is never served as the reader's answer: `interpret()` applies a prompt whole or not at all. `vocabulary.WORDS_OF_DOUBT` and `PHRASES_OF_DOUBT` are the written list: the reader does not read it, since none of its words is a word of the grammar, and a test holds `PLAIN` to it. `SIGNS_OF_DOUBT` is what the model-backed interpreter's generated test draws its sentences from.

What this costs is written in section 13: plain wishes that are no longer applied, and are offered.
- What a model calls the provenance of an edit is not read. Every edit of an offer is `ui_edit`, because it is sent only when a person presses it.
- What is sent to the model is JSON, `{spec, request}`, so nothing typed can close the field it is in.

**The model proposes, the person confirms, code checks.** A model is told all of the above in its instructions, and can still be wrong about each. Until 24 September 2026 a guard kept from a model's answer what the rules bore out, and applied it. It was measured on 113 made-up sentences, each read once by one model: the rules alone read 59 rightly and none backwards, the model behind that guard 47 and one backwards, and the model by itself 75, with 6 backwards. The guard made the product worse than having no model, because it applied only what the model said: whatever the model left out of a plain prompt was lost, though the rules had read it (ADR 0012). So:

1. **The rules read first.** A plain prompt is applied by the rules, and no call is made. Nor is one made where the rules made something of every word of a prompt that is not plain, as of the name of a scale alone: `asks_a_model` is whether `unread` or `asks_nothing` holds anything. Words that ask for nothing are not said to be unread (section 8.1), and a model is asked of a prompt that holds them exactly as it was before they were left out.
2. **For any other prompt the rules make their offers, and the model is asked.** What the model says becomes offers. The two are merged, one offer for each thing, and every offer of the rules is there with every way the rules gave it. A person never sees less than the rules alone give.
3. **Nothing a model reads is applied.** Not a weight, not a budget, not a notice that changes the search. Every edit of `operations` is the rules' own, and every edit of an offer is `ui_edit`, sent to route 2 when a person presses it. This is a test and not a rate: no path through the service applies an edit that came from a model.
4. **The model says which thing, and which words. Code says the rest:** which way, how much, how firm, by what way of travelling, and whether the thing may be offered at all.

Nothing in `guard.py` decides what a word means. Where a sentence ends, what a token is, and every list of words are core's, read in `typed.py`: the written list of doubt, the words that turn, cap, lead in to a thing and say how much, the lexicon, and the words for a way of travelling.

**What code checks before a reading is offered.** A check drops a reading, or puts right a field of it that is code's to say, or takes the guess away. Where the guess is taken away the thing is still offered, with every way open and none marked. `Check` in `guard.py` names each, and how often each fired is counted and never served.

| # | The check | How it is kept | What becomes of the reading |
|---|---|---|---|
| 1 | The words are the person's, and say something | `words` is looked for in the text: the same words, in the same order. The case of a letter, the shape of an apostrophe and every mark around a word are left out of account, so "£400k" is found by "$400k", and the words may stand either side of the end of a sentence. Part of a word is not the word. Words that core's grammar places and that name nothing, the speaker, a wish, an article, a word that joins, are no words to rest a thing on: "a", "I want". What is shown is cut from the text by where the words stand, never the model's copy | Words that are not in the text, or that name nothing, make no offer |
| 2 | A name is the whole of a name the release holds, as typed | `destination_text` must stand in the text, side by side, and be no part of a longer name the person typed. Where it is the whole of a name or an alias of one place, the journey is to that place. Where it is not, it must stand in a sentence the edit rests on | A place the release does not hold is kept as a question, with its minutes: see below. A name the person did not type makes no offer |
| 3 | A least is never a most | The words of the journey, and the words that lead up to them and to the name as far back as a mark, hold a word core lists as turning a wish away or keeping it at a distance: "minimum", "at least", "no less than", "more than", "away". What says a number is the most it may be, "no more than", "within", is taken out first. For a budget it is what stands before the amount, as far as the number before it: "at least £2,000", "my budget isn't 2000" | No journey is offered from the model. What the rules offer stands, with no number, and says so. Where they offer nothing, a fixed line says that Burro cannot keep a search away from a place. A budget is offered with both its ways, and no guess |
| 4 | Raised against a word that turns | A wish for a thing, where its words and what leads up to them hold a word of core's that turns a wish away, takes it off or turns it down: "not", "miles", "wouldn't". What leads in to a thing, "not far from", is taken out first. It is asked of the words a model quoted, and of what leads up to the thing wherever the rules noticed it: a model that rests a park on "is essential", of "I hate parks. But a station is essential", has no guess. A nuisance is wanted less, so a word that turns before it is the wish itself, "no noise", and so is what troubles the person, before it or after: "burglary worries me". A word that turns after it is said of it, and what is said of how much it counts is no wish: "crime doesn't bother me", "I don't mind crime". Named with none of these, it is in doubt: "I like noise" | No guess. To want fewer of a thing that runs two ways is the wish a turn makes, and is no doubt |
| 5 | A scale with no end | The model named a scale and no end of it, or turned an end down. Or no phrase of core's names an end of the scale in the clause, whichever end the model chose: "the pace of the place", "the age of the buildings". **A guess takes the end the person named.** An end is named by core's phrase for it, read with what leads up to it: an end that is turned away is a wish for the other, as the rules read it, so "not buzzy" names Calm and "calm, not buzzy" names it twice. Two words that turn before one end name none: "I wouldn't say no to buzzy". A word for a home says what is being looked for, "a flat", and names an end of Houses or flats only where one end is set against the other: "houses not flats" is Houses. Where the model named an end, the guess is that end where the words name it. Where it named none, the guess is the end the words name only where they said which by turning one away: an end that is only named is no more than the rules noticed | Both ends, and no guess |
| 6 | Recorded crime | A weight on recorded crime is offered only where the words hold a phrase that core's lexicon reads as that crime, as stated. A vibe whose recipe holds recorded crime is never a model's to offer, towards either end | No offer. Where the words name the thing, the rules offer it |
| 7 | How firm is code's | A limit is firm only where a phrase of core's list for its kind stands against its own number: `FIRM_OF_MONEY` for a budget, "max", "up to", "at most", "no more than", "can't go over", and `FIRM_OF_MINUTES` for a journey, "within", "max", "at most", "no more than". Straight before it, with nothing between but a word that caps, "no more than about 40", or straight after it and what it is a number of, "40 minutes at most". It is not looked for in all that a model quoted: "at most" of the bedrooms makes no budget firm, and nor does "no more than" of the minutes that come next. A journey is firm too where its minutes are the longer end of a range the person typed, and never at the shorter end. Any other is offered as a guide first, with the firm limit as the second choice: "under", "around", "up to" of minutes | The order of the two ways, and which is the guess |
| 8 | The way of travelling is code's | On foot or by bike only where a word beside the journey says so: in the clause the name stands in, or in the clause the minutes stand in. It is not looked for in all that a model quoted. A walk said of another thing is not the way to work, in another clause or in the same one: "a supermarket within walking distance", "and a park I can walk to". What core reads as how near a thing is, is the way of the journey only where the name of its place comes next: "I can walk to Pellam Exchange" | Public transport, and the offer says that no way was named, or that one was named and not taken |
| 9 | No number of the model's | A weight is a step, and never `value`. Code reads how much from the words: a word of `SMALL_STEP` is a small step, a word of `ESSENTIAL` counts above all, and any other wish is a mention. It is read where the thing stands: where the rules noticed the thing, in the clause they noticed it in, and where they did not, in what the model quoted, where nothing counts above all in a quote that runs on past a mark. "Essential", of "a park is essential, and maybe pubs", is not said of the pubs. A thing set to nothing is a thing taken off | The step of the way |
| 10 | A budget keeps its amount | A size that does not suit the tenure is left out, and the amount and the tenure are kept. The amount must be a number that stands in the words, and one that core does not read as minutes or as bedrooms. The tenure is kept where the rules noticed a word for it, or the amount can be of no other | The offer says that the size was left out |
| 11 | An edit that would change nothing is not offered as it stands | Every way is tried on the spec as the reducer would apply it. Where the thing runs two ways, to take it off is to want fewer of it. Where it runs one way and is not held, there is nothing to take off | The way is left out. An offer with no way left is not made |
| 12 | One thing, pulled two ways in one answer | Two readings of one thing that run different ways, or two budgets | One offer with both, and no guess |
| 13 | Who lives somewhere | No offer rests on a wish the rules heard as about people, a campus among them. The words a model quoted are read with the whole of the clause they stand in: "somewhere lively", of "somewhere lively for young professionals". And words in which core finds no thing, no name and no number are no wish of their own: in one sentence with a wish about people they are part of it, "like me", of "young professionals, like me". A wish of its own in a clause of its own is the rest of the request, and is offered. Nothing is offered that rests on the words for a community's amenity, "near a synagogue": no feature covers one, and what a model reads into it is a reading of who goes there. Where only the model says the request is about people, code cannot say which words it means, so nothing of its answer is offered | The notice is given, and the rules' own offers stand |

Three more stand beside them. **A direction written against the one way a thing runs** takes the guess away: the field is not read, and written so it shows that the model did not know which way the thing runs. **Where the rules read the words the other way**, in a sentence they know or by a phrase of the lexicon that says which way, it is one offer with both ways, no guess, and the whole sentence shown. **What the rules offer what is nearest for** is the rules' to offer: "safe", "a sense of community", and every word core adds with a note of what Burro cannot measure, a word about wealth or about identity among them. So is every word the rules read into the vibe that counts recorded crime, with a note or with none. A model's reading of the same words is dropped. **So is its reading of the same thing, on whatever words it rests it.** A model chooses the words it quotes, and may name Village feel and rest it on "somewhere quiet", of "somewhere quiet, with a real identity": the guess would then be marked on the rules' own reading of the word about identity. A thing the rules offer with a note is served as the rules give it with no model: the same ways, the same words, and no guess. **A model's guess of a vibe that is a rough guide is no guess.** Where the rules noticed it, the offer is theirs. Where a model reads it in words the rules do not know, "a small-town feel", it is offered with no way marked, in an offer of its own that holds its label and its sentence: it is never a choice of another thing's offer, and never added with others at one press.

**What is said about a thing is read where the thing stands.** A model chooses the words it quotes, and the words that turn a wish round are the ones it leaves out: "a station", of "a station, heaven forbid". So two checks more are made of the sentence itself, where core finds the thing and where the model's words stand in the text, and never of what a model says it quoted. Decided on 2026-09-24, after one model was measured a second time.

| The check | How it is kept | What becomes of the reading |
|---|---|---|
| The words about it turn it round | A wish for a thing. In its own clause, before the thing or after, a word core lists as what a person dreads, thinks little of or cannot bear, `DREADS`, or what says how little a thing counts: "a pub on the corner would be hell", "parks are not important". Straight after the mark that ends its clause, and straight before the mark that begins it where nothing but an article stands between, any word that turns, where nothing more is said beside it: "a station, heaven forbid", "pubs, no thanks", "a playground, I'd hate that", "no, a park", "What I don't want: a station". Words that go on to say something are said of that: "leafy, not too expensive". What leads in to a thing and what says where it is wanted is no doubt about it: "a park within walking distance". A nuisance is wanted less, so what is dreaded of it is the wish itself, and check 4 says what puts one in doubt | No guess |
| The wish is somebody else's | The sentence says who else wishes, `WHO_ELSE`, or holds the third person of a wish with somebody straight before it, `WISHES_OF_ANOTHER`: "my mum is after a park", "everyone wants a station", "the landlord likes a high street". It is read as far back as the start of the sentence, since who wishes is said once for every thing of a list, and no further than a wish of the speaker's own or "but": "my brother wants a pub and I want a park" is a guess at the park. Whichever way the wish runs: what a friend cannot stand is no more the person's own. The heading of a list is nobody's wish but the speaker's, "Wants: a park", and the speaker's own household wishes as the speaker does, "my dog needs a park" | No guess |

Neither reaches further than a word that joins two wishes, a wish of the speaker's own, or another thing that core finds: "quiet but not dead", "a park, not pubs", "pubs are awful and parks are great". Where either fires the thing is still offered, as a question with every way open, the whole of the sentence is shown under "You wrote", and "add all" takes none of it. Both are checks of what a model read, and of a wish. What the rules alone noticed is offered as it was, and a journey is nobody's wish: where a partner works is a place to reach, and whose wish it is, is no sign of doubt that "add all" holds a journey to.

**A number is never offered as another kind than core reads it as.** What core's own words say a number is of is kept with it: money, by its mark or by "a month" or "quid" after it, minutes, or bedrooms. So "45 quid a week" is no journey of 45 minutes, and "900 minutes" no budget of £900. Figures in a word that holds letters of its own, "35b", a postcode, are no number of minutes.

**A model chooses the words it quotes.** So nothing that makes an offer stronger is read from the quote alone. What makes a limit firm, how much a wish counts, the way of travelling and what turns a wish round are each read where the number or the thing stands, as core finds it. `tests/test_adversary.py` holds answers written to get a wrong reading past each check.

**Never offered from a model, whatever it says.** Each has a test.

| What | Why |
|---|---|
| A vibe that counts recorded crime | The model raised it on "interesting streets" and on "slightly affluent", and once called the edit stated |
| A weight on recorded crime that the words do not name in core's own phrase | Whether crime was asked for by name is never the model's to say. To offer "muggings", add the word to core, with a case first |
| Anything about who lives somewhere, and any reading of a word about wealth | ADR 0006. The rules offer what is nearest for such a word, and what they offer stands. **Core lists the words about wealth and about identity.** It offers three readings of the one and three of the other, all of the place. A model adds no reading of "affluent" or of "a real identity", and marks no guess on a reading the rules offer of either, whatever words it rests it on. A test holds each |
| A firm limit nobody gave | A firm limit leaves areas out, and what is left out is not seen to be missing |
| A least distance, as a journey | Burro has no way to keep a person away from a place. The offer would be the opposite of the wish |
| A number for a weight | No sentence gave one, and the model set one in a fifth of its edits |
| A place, an area or an amount the person did not type, and a number typed as another kind | It costs nothing to check |
| A way of travelling nobody named | A walk said of a park is not the way to work |
| An end of a scale that no phrase of core's names | Which end a person means is theirs to say |
| A rule for an area, as a guess | The rules notice every name typed in full, and offer the rules for it. A model adds only a guess at which |
| A change to a setting, a step of the budget, a journey changed or taken off | No offer is worded for one. None is made |

**A place the release does not hold** is kept as a question: a journey with its minutes, its way of travelling and its firmness, and no place. `asks_place` is true, `named_at` says where the name stands in the text, and `options` holds what the release has that is alike, five at most, and is empty where nothing is. A client puts the id of the place the person chooses into the journey before it is sent. The model is never asked where a place is, and is never sent a name of the release.

**One offer for each thing.** `merge.py` puts what a model read with what the rules noticed.

| Where | What is offered |
|---|---|
| The rules noticed the thing | The rules' offer, with every way they gave it. The way the model read is the guess, where no check fired. How much is read from the clause the rules noticed the thing in. The minutes the rules read for a journey are kept where the model quoted none, and where the model read another number the rules' own journey is still a choice |
| Only the model read the thing | An offer of its own, `read_by: model`, with the ways code makes for the thing |
| The rules and the model name different things for the same words | One offer with both as choices, so that nothing is counted twice: "Nearer a park" and "Parks close by". What a word names is core's to say, so the guess is the rules' thing, taken the way the model read the words. For a scale that is the end core's words name: "nightlife" is the Buzzy end of Pace, and a wish against it is a wish for Calm |
| The model names two things for the same words | One offer with both, and no guess |
| A budget | One offer of the amount, the tenure and the home together. What the rules noticed of the same budget is part of it. Another amount, as one the person took back, stands as the rules offered it |

**The same readings make the same offers.** A model does not write its edits in the same order twice. So the readings are put in the order of their words before anything is made of them, and two that stand on the same words in the order of what they hold. The offers stand in the order of their first word, and two that rest on the same words in the order of the places they name. Two that still tie keep the order they were made in, which is the rules' own for what the rules noticed. Nothing a person is shown rests on the order in which a model wrote: which of two things is named first in one offer, which of two budgets is the first choice, which of two journeys stands first. A test writes every answer on disk the other way round and holds the offers to be the same. What a model reads of one sentence may still differ from one asking to the next: which things it reads, which words it quotes, and whether it says the request is about who lives somewhere. Code cannot make those the same.

**How an offer is worded.** The words are the API's, made in `wording.py` and served with the offer, so that every client shows the same. They are made from the edits an offer holds and from the catalogue, and from nothing a person typed.

| Part | Field | What it holds |
|---|---|---|
| What it would do | `does` | It begins with a verb: "Add a journey to Pellam Exchange: at most 40 minutes, by public transport." Where Burro has no guess and the thing runs more than one way it is a question: "Pace runs from Calm to Buzzy. Which way?" So it is where a wish runs one way, no guess is marked and something beside it puts it in doubt: "More culture nearby: count it?", under "theatres? No thanks" |
| You wrote | `spans`, `shown` | Where the words stand, as offsets. `shown` is the clause they stand in, from one mark to the next, or the whole sentence where the rules read it the other way. It holds all that the offer rests on, as far as the words that end last. A client cuts the words from the text it holds, and never retypes them |
| What follows | `follows`, `said`, `note` | What happens to areas: which rank higher, which are left out. What a thing counts, and what a vibe cannot see. Of the distance to a station, what near means, after what is counted: "What Burro counts: straight-line distance to the nearest way in to a station. Within 800 m in a straight line is about a 10 to 15 minute walk." What nobody said, and what Burro took: "You named no way of travelling: Burro took public transport.", "You gave 35 to 40: Burro took 40." |
| The choices | `choices` | Each has an `id`, a `label` and `guess`. Doing nothing is "Skip", and is last. A way that leaves areas out says so on its face. Recorded crime is chosen under its own name |

A wish against a thing is never said to be "counted less": what is said is what happens to areas. An offer says all that each of its ways holds, in what it would do and on the face of the way, and a test holds every field of every edit to it.

**Burro's guess** is a mark on one way of an offer, and applies nothing. It stands on the way a model read the words, where no check fired. And it stands on the one way of what a person plainly said of the home they look for, whether or not a model reads: that they are renting or buying, a budget with its amount, and a kind of home. It stands too on the way the words give of a journey that was plainly said, to one place and with one time, which is then offered both ways, as a firm limit and as a guide. The founder decided so on 2026-09-25 (ADR 0012): the sentence "If I'm buying, max £400k for a 1 bed flat" carried no guess at any of the three, and one press left the search renting, with no budget.

**What is plainly said of a home.** `plainly_said` in `guard.py` holds it, for what the rules read. Every part is asked.

| What is asked | How it is kept |
|---|---|
| The rules would apply the clause, were it all that was typed | The clause the words stand in, from one mark to the next, is read by the rules alone, into the search as it stands. They apply a prompt only where the grammar makes the whole of it (section 8.1): "max £400k for a 1 bed flat", "renting", "about £600k". "I earn 60k", "I have a 50k deposit" and "I'm done renting" are no such clause, for "earn", "deposit" and "done", and are offered with no guess. So one press takes no more than Burro does unasked of a plain prompt |
| An "if" that leads the clause in is no doubt | "If I'm buying" says which of renting and buying the rest is said of, and is read as "I'm buying". Core lists the word, `IN_CASE`. It is no word of the grammar: a prompt that holds it is not plain, and nothing of it is applied |
| The words give one of each | One tenure, by core's words for renting and for buying and by what the offers would set. One amount, and one kind of home. "If I rent, up to £1,700 a month, and if I buy, max £400k" names both tenures, and nothing of a home is the guess. Two amounts leave the tenure and the home plain |
| The wish is nobody else's | `typed.anothers`, asked where the amount stands, or the word for the tenure or the home: "my partner wants to buy" |
| Nothing beside it puts it in doubt | No sign of doubt that core lists stands in its clause, and its sentence does not ask |

Whose wish it is and which tenure is meant are asked of a model's reading of a budget too: where either is in doubt no guess stands on what is said of a home, whoever read it. A model's guess at a budget is not held to the rest, which is said of what the rules read.

**What "add all" may add at one press.** `add_all` of an offer is the `id` of the way it takes, and is empty where it takes none. `needs` says what is then left for the person.

| It may add | It may not add |
|---|---|
| A wish or a vibe, at a mention or a small step | A rule for an area |
| What is said of a home, where it carries the guess: the tenure, the kind of home, and the budget as the person worded it | What is said of a home with no guess |
| A journey, as a guide, to a place named in full | A journey as a firm limit. Where the guess is a firm journey, it adds the guide. A journey to a place that is yet to be chosen |
| | An offer with two ways and no guess marked |
| | Recorded crime, in any form, anything that counts who lives somewhere, and any feature or vibe the rules offer with a note |
| | A vibe that is a rough guide, whoever read it and whatever is said of its offer |

**A budget is taken as the person worded it**: firm where a word of `FIRM_OF_MONEY` stands against its amount, "max", "up to", and a guide where none does. A firm budget leaves areas out, so a client says after the press how many areas the budget left out, from `filtered` of the ranking that follows.

**A journey is never taken as a firm limit.** A journey is estimated from distance and no timetable stands behind it (section 6.10, ADR 0027), so one press must not leave areas out on an estimate: on the first build of London a firm limit of 40 minutes to one station leaves out 422 of 1,002 areas. A person makes a journey firm with a press of its own, and `needs` says that it can be made firm. It is so whoever read the journey. **A journey that was plainly said is offered both ways by the rules alone**, as a model's reading of it is (settled later on 2026-09-25, ADR 0012): it is to one place the release holds, with one time, and the rules would apply its clause were it all that was typed. The guess is on the way the words give, which is the firm limit where a word of `FIRM_OF_MINUTES` stands against the number or the number ends a range, and `add_all` names the guide. One time is one number of minutes, or one range, in the sentence the journey stands in. What is offered is what the rules would apply of the clause, so a way of travelling that was said is kept. Of a range the longer is taken, and the `note` says so. A journey with no time is offered one way, as it was, and one the rules do not read plainly is offered as it was worded: where that is a firm limit, no press takes it with others.

It presses for the person, so it is held to more than a guess is. It takes a thing only where the clause it stands in holds no sign of doubt that core lists, before the thing or after it: "schools are irrelevant". It takes nothing from a sentence that asks: "is a park worth it?" And once a model has read the words, it takes what Burro guesses and nothing that was only noticed.

**When the model is slow, capped or broken** the rules answer, and never a 5xx (section 9.4). So they do when the provider will not read what was typed, for safety or for its own terms, and `model_refused` says so (ADR 0023). A caller that will not wait sends `ask_model: false`: the rules answer at once, no model is asked, and `model_pending` says whether a model has more to read. It asks again to have what the model adds.

**The floor.** A model is not turned on, for any provider, until all of these hold on a measurement of it. `evals/reader/score.py` counts each, and `evals/reader/replay.py` holds the answers on disk to them.

| What | No more than |
|---|---|
| A reading of a model's applied without a press | None. A test, not a rate |
| Anything offered that is never to be offered | None. A test for each row |
| A backwards reading offered with a guess marked | 1 in 100 sentences |
| A backwards reading that a model added, in any form, on sentences that are right to leave alone | 1 in 25 |
| A right reading of the rules, lost because the model was on | None |

On the first look of the 112 sentences whose answers are kept, the guard offers 84 rightly, where the rules alone read 61. No backwards reading is marked as the guess. Nothing is applied, nothing is offered that is never to be offered, and no reading of the rules is lost. That is a fit and not a measurement: the checks were chosen after reading these answers.

**The floor does not hold against a model that means harm, or is careless.** A stand-in that raises whatever a sentence names is marked as the guess, backwards, on 73 of the 820 cases of the evaluation set, where it was 89 before the guess was held to what is said about a thing. So the floor rests on the model reading a turn rightly, on core listing the words, and on the person who presses.

**Measured a second time, it holds with nothing to spare.** The same model read the same 113 sentences again, through the guard. Three were offered backwards with the guess marked, which is more than the floor allows. With the two checks of what is said about a thing, one is: a deposit that a model read as a budget, once in four looks. One in 113 is 0.9 in 100. ADR 0012 has the counts, and what the second measurement could not say.

What this cannot do:

- A wish of somebody else's, in words core does not list: "the vendor insists on a park", "Dave reckons a station is a must". Core lists who is known to the speaker, who is meant at large and the third person of a wish, and no list of them is ever whole.
- A wish turned round, of a thing in words the rules have no phrase for, in words core does not list as doubt: "boozers on every corner would finish me off", "a station would drive me up the wall".
- A turn that stands in another sentence, or in the heading of a list: "A park? Never.", "Pubs, bars, clubs. None of it.", "Dealbreakers: pubs". And a turn beyond a mark that goes on to say something: "a park, not that I would ever use one".
- What is said of several things at once, after the last of them: "pubs and clubs, no thanks" is read of the clubs.
- A wish that is over, in words that are no dread: "I wanted a park but I've changed my mind".
- A number that core does not say the kind of, read as another: "built after 2000" as a budget of £2,000, "£300 a week" as £300 a month, "I earn £3,000 a month" as a budget.
- Any thing on any words that name something. A model that rests Food and drink on "somewhere with a view" is offered, with the guess marked: which thing the words mean is the model's to say, and code checks only that it may be offered.
- A word that troubles, in a form core does not list: "violence scares me" is offered with no guess.
- If the lexicon misses a request about people and the model does not flag it either, nothing in the code knows what the request was about.
- `tests/test_guard.py` holds a wish turned round in words core does not list as a test that is expected to fail, so that the day it is closed the test says so. `tests/test_adversary.py` holds the words about wealth and identity as tests like any other, since core lists them.

```python
class ModelClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: Mapping[str, object],
        model: str,
        max_tokens: int,
        timeout_s: float,
    ) -> ModelReply: ...
```

### 8.3 Resolving names

The text is normalised (casefold, strip accents and punctuation, collapse spaces) and each place is scored by the best of its name and aliases. A place that scores nothing is not a match. Matches are ordered by score from high to low, then by kind in the order of 2.7, then name, then `place_id`.

| Score | The text is | "Pellam Cross" is matched by |
|---|---|---|
| 1.0 | The whole of the name or an alias | "pellam cross" |
| 0.9 | Whole words from the start of it | "pellam" |
| 0.8 | The start of it, stopping part-way through a word | "pel", "pellam cr" |
| 0.6 | Words that all appear in it, in another order or not from the start | "cross" |

Searching and resolving part ways here. A search box is helped by the start of a word, and a person is looking at what it offers. Resolving turns words into a commute or a filter with nobody looking, and an ordinary word that begins a name, "far" for Farrowmere or "b" for Brackenhythe, has named nothing.

| Function | Takes without asking | Otherwise |
|---|---|---|
| `search_places(text, release, limit)`, `search_areas` | Nothing. It is a search | Every match, best first, cut to `limit` |
| `resolve_place(text, release)`, `resolve_area` | The best match, if it scores 0.9 or more and no other match scores the same | The first five matches are the options. That includes a match on part of a word, and a single match at 0.6. No match gives an empty list, and the client shows a search box |
| `Names.exact_place(text)`, `exact_area` | The best match, if it scores 1.0 and no other does | Nothing, and no options. It is for words that may not have been meant as a name at all |

`resolve_area`, `exact_area` and `search_areas` do the same over area names and aliases. Where several areas bear one name, each holds it among its aliases, so each scores 1.0 for it: a search offers them all, and none is taken for the others without asking. `Names.whole_place(words)` and `whole_area` answer as `exact_place` does for words that are already normalised, without scoring every name. The rule-based reader takes a name by these two alone, on the text as typed (section 8.2), and offers what `search_places` finds for words that were given as a name and are the whole of none: it no longer takes whole words from the start of a name without asking. The model-backed interpreter takes a name from a model only by these two, and only one that stands in the sentence the edit rests on, as typed (section 8.2). Where the model's words are not the whole of a name it keeps the question the reader asks of those same words, and nothing otherwise. The text is dropped as soon as it is resolved.

### 8.4 A request about who lives somewhere

Burro ranks places. Of who lives somewhere it counts their age and what their households are made of, at the census of 2021, and nothing else, and no edit can ask for fewer of anyone: a measure of them has one direction, and no words are read as a wish for less of it.

| Request | Example | Response |
|---|---|---|
| To avoid a group | "not too many students", "fewer immigrants", "no families", "fewer young professionals", "away from retirees" | No edit for that part, and no offer. `policy_redirect`. The rest is applied, where the prompt is plain. It is so of those Burro counts as of anyone |
| To find a group Burro counts, by age or by households | "young professionals", "lots of young families", "retirees", "people my age" | Offered towards more, with its note, and never applied (section 8.2). No notice. It is not quietly turned into a tag of places: Going out is not read into "young professionals" |
| To find any other group | "students", "professionals", "young couples", "singles", "gay village", "student village" | No edit for that part. `policy_redirect`. The rest is applied. It is not quietly turned into a tag. What people do for work, whether they study and whether they have a partner are counted by nothing |
| To find those Burro counts by what was not decided on | "young white professionals", "muslim families", "wealthy families", "british families" | `policy_redirect`, and nothing is offered of either. Nothing of ethnic group, religion, country of birth or income is read in any word |
| To be far from a campus | "far from a university", "nowhere near a university", "not near the campus", "miles from any university", "somewhere that isn't near a university", "nowhere near Wexmoor University", "University is not for me" | No edit for that part. `policy_redirect`. The rest is applied. It is a way to ask for fewer students, and the feature has one direction (section 3.1). The rule is not a list of phrases: a campus, by word or by name, in a prompt that is not plain, or under a word that turns, is read this way (section 8.2). "Far" is no word of the grammar, so "quiet, far from a university" applies nothing and offers Quiet streets, and "quiet, not near a university" applies "quiet". "Near a university" and "not far from a university" are wishes about a place and are ordinary edits, and so is "don't care about universities", which takes a weight off |
| For a community's amenities | "near a mosque", "kosher shops", "muslim schools", "gay bars", "Polish shops" | `ok`, with `community_amenities` in `unmet`, and no edit: "muslim schools" is not a weight on school results. The v1 catalogue has no such feature |
| For amenities by name | "good primary schools and playgrounds", "Turkish cafes" | `ok`. Ordinary edits |

The `neutral_places` notice is one of two fixed texts, and `notice_text(notice, changed)` in core chooses. Where an edit of the same answer changed the spec: "Burro ranks places by what is there. Of who lives in a place it counts only their age and their households, at the census of 2021, and you cannot ask for fewer of anyone. The rest of your search has been applied." Otherwise the first two sentences, and then: "Nothing you typed has changed your search." Until 2026-09-24 it said that Burro never ranks by who lives there, which is no longer so. Each is the same for every group and every user. `changed` is the API's to say, from what the reducer applied.

`POLICY_LEXICON` lists the terms for protected characteristics and for kinds of resident, but for those Burro counts, which are phrases of the lexicon. It holds words for people, never for buildings: "mosque" and "kosher shop" name amenities and are not in it, or the fourth row above could never be reached. A group named as a plural noun stands alone. The word directly before a term is closed with it, so "quiet neighbours" makes no edit. One name of a measure says residents, the share of them that transport noise reaches (section 3.1). Typed whole, it is the name of the measure and asks about nobody: `NAMED_FOR_WHOSE_SHARE`. A word more or a word less, and "residents" is heard as it always is.

A word for a group is read with the word after it, whatever that word is, so that it can never be left to the lexicon:

| The word for a group | Beside a word for people | Beside a venue or a shop | Beside anything else |
|---|---|---|---|
| Is a word for nothing else: a religion, a sexuality, "foreign", "immigrant", "religious", "student" | A request about people | A community's amenity, heard and reported as unmet: "muslim schools", "gay bars" | A request about people, and the word after it is closed with it: "gay village" is never the village-feel tag |
| Is also a cuisine, a country or a colour: "Turkish", "Polish", "Asian", "black", "white" | A request about people | A place to eat or drink is an ordinary wish: "Turkish cafes", "Irish pubs". Any other venue or shop is a community's amenity: "Polish shops" | Nothing. "White stucco houses" and "an English garden" ask nothing about people. But beside a word for character it is the character of a people: see below |

**The character of a people is theirs, and no character of a place.** "Identity", "character" and "soul" are offered three ways as of the place (section 8.2). Straight after a word for a group or a term for people each asks who lives somewhere, and is closed with it: "a Polish character", "a Black identity", "working class identity" and "a studenty character" get the notice, and are offered nothing. A word for a smart area or a rough one is of the place too, and beside what people are called it is of them: "posh folk", "affluent households", "an upmarket clientele", "rough people", "rough sleepers". What people are called there is `_WHO` in `lexicon.py`. "A posh area", "posh shops" and "a rough estate" are still of the place.

A venue or a shop is one of a short list of nouns, `_AMENITIES` in `lexicon.py`, looked for within three words of the word for the group, so that "a Catholic primary school" is heard whole.

The lexicon is a first guess: it fires on some innocent sentences ("a diverse range of restaurants", "I am a student nurse") and misses groups it does not list, and a venue that is not on the short list is taken for a request about people. No edit can express such a request either way, so what a miss loses is the notice, and what a false alarm costs is one sentence that did not apply. Both interpreters run it over the text. For `ModelInterpreter` it is a backstop: the status is `policy_redirect` if the rules find a request about people or the model sets a flag, and a model that answers `off_topic` does not overrule it. Either way nothing a model read is applied, and no offer rests on the words the notice is about (section 8.2, check 13), so that the notice is never sent with the request quietly offered beside it as a weight, a journey, a budget, a setting or a filter on areas. What counts who lives somewhere is the rules' to offer and never a model's: a model is told of no such measure and no such vibe, an edit of a model's that names one is dropped under check 13, and what a model reads into the words the rules offer one for is dropped as any reading of a word the rules offer with a note is.

## 9. The API

### 9.1 Every response

```json
{"meta": {"release_id": "syn-2026-09-23-01", "engine_version": "1.15.0", "synthetic": true,
          "preview": false},
 "data": {}}
```

Errors replace `data` with `error`: `{"code": "...", "message": "...", "fields": [{"path": "spec.commutes[0].max_minutes", "problem": "out_of_range"}]}`. `message` is fixed text for the code. `fields` holds paths and problem codes and never a value that was sent. Every response also carries the headers `X-Burro-Synthetic` and `X-Burro-Preview`, each `true` or `false`, and `X-Request-Id`, which the server makes and never takes from a header. `synthetic` says the figures are made up. `preview` says the release is not finished, whether its figures are made up or real. A client shows both: a real figure in a preview is a fact about a place, and the release around it is not yet what Burro promises. Two answers have no body, and so no `meta`: the 204 to a browser that asks first, and the 304 of section 9.3. For each the headers are all that say whether the data is synthetic and whether the release is a preview. Bodies are JSON, at most 16 KiB in. Typed text is measured without the space around it, so a line of spaces is an empty line. All text that a person typed travels in a request body, never in a path or a query string, so it cannot reach an access log.

**A number is sent as a number.** Wherever a body holds a number, in the body itself, in the spec or in an edit, the JSON value must be a number: `true`, `false`, `"1"` and `"0.5"` are refused with `wrong_type` at the field's path (`not_allowed` for `schema_version`, which takes one value), and never read as 1, 0 or 0.5. A whole number is a number wherever one is asked for, so `1` is a weight of 1.0. The check reads each body beside its own schema, so it covers the records of core without changing them, and a field that is added later.

**Browsers.** A page may read an answer only if it was served from an origin on a list. The list comes from the setting `BURRO_ALLOWED_ORIGINS`, origins separated by commas, and is `http://localhost:3000` when nothing is set. An origin is a scheme, a host and perhaps a port, in lower case as a browser sends it, and it is compared exactly: there is no pattern, no "every origin", and `null` is not an origin. An entry that no browser would send would match nothing, and whoever wrote it would not be told, so it is refused when the service starts: one with a path, a slash at the end or a capital; one that names the port its scheme implies, `:443` for `https` and `:80` for `http`, which a browser leaves out; a port of 0, one above 65535 or one written with a nought in front; and a host that is not labels of letters, digits and hyphens with a point between them, each of 1 to 63 characters with a letter or a digit at each end, and 253 characters at most in all. A host that ends in a point is refused with the rest, though a browser can be made to send one. The refusal never repeats what was set.

| The call | The answer |
|---|---|
| From an origin on the list | As any answer, errors included, with `Access-Control-Allow-Origin` set to that origin and `Access-Control-Expose-Headers: X-Burro-Synthetic, X-Burro-Preview, X-Request-Id` |
| From any other origin, or from none | As any answer, with no `Access-Control-` header. The call is answered and the browser keeps the answer from the page |
| `OPTIONS` with `Access-Control-Request-Method`, from an origin on the list | 204 and no body, with `Access-Control-Allow-Methods: GET, POST`, `Access-Control-Allow-Headers: Content-Type` and `Access-Control-Max-Age: 600`, whatever the path |
| The same from any other origin | 405 `method_not_allowed`, as for any `OPTIONS` |

Every response carries `Vary: Origin`, allowed or not, because routes 4, 5, 6 and 11 may be cached and the answer differs by who asked. No response carries `Access-Control-Allow-Credentials`: the service sets no cookie and reads none. What is sent back is the entry of the list and never the header that was sent, and the `Origin` header is logged no more than any other.

### 9.2 Routes

| # | Route | Request | `data` | Errors | Pure |
|---|---|---|---|---|---|
| 1 | `POST /v1/interpret` | `text`, `spec` (optional; a default renter spec if absent), `ask_model` (optional, default true: `false` asks for what the rules make of the text, at once) | `status`, `operations`, `spec` after the reducer, `spec_hash`, `applied`, `rejected`, `assumptions`, `unmet`, `clarify`, `notice`, `notice_text`, `interpreter`, `degraded`, `model_refused`, `rests_on`, `suggestions` (each an offer in four parts, section 8.2), `unread`, `not_in_release`, `unmet_at`, `model_pending`, `places` | 422 `invalid_text`, `invalid_spec`, `unknown_place`, `unknown_area` | No |
| 2 | `POST /v1/rank` | `spec`, `operations` (optional), `limit` (1 to 100, default 20) | `spec` after the reducer, `spec_hash`, `applied`, `rejected`, `places`, `scores` (every ranked area in rank order, each an `area_id`, a `score`, `counted` and `present`), `ranked` (the first `limit` in full, each with its `strip`), `areas_ranked`, `areas_listed`, `filtered`, `unranked` (each with its `reason` and what it lacks), `empty_spec` | 422 `invalid_spec`, `invalid_operations`, `unknown_place`, `unknown_area` | Yes |
| 3 | `POST /v1/explanations` | `spec`, `limit` (1 to 5, default 3) | `spec_hash`, `explanations` for the top `limit` areas, and `facts`: every fact a sentence cites, and the `tag` fact of every mark on the strip of an area explained | 422 as route 2 | Yes |
| 4 | `GET /v1/areas` | | `areas`: `area_id`, slug, name, borough, centroid, rankable, and `named` (section 2.2). `bands`: for each vibe that holds `lens`, in shelf order, its `tag_id` and `marks`, one for each area by id, each an `area_id`, `band`, `spread_low` and `spread_high` | | Yes |
| 5 | `GET /v1/areas/geometry` | | The `FeatureCollection` of `geometry.json` | | Yes |
| 6 | `GET /v1/areas/{id_or_slug}` | | The area, `features`, `tags` (one for each vibe of the release), `cost`, `stations`, `neighbours`, `portrait` (section 7.6), `similar` (five at most, each an `area_id` and the `fact_id` of its `likeness` fact), and `facts` built with no spec | 404 `area_not_found` | Yes |
| 7 | `POST /v1/compare` | `area_ids` (2 to 4, no repeats), `spec` | `areas`, each with its `status` (`ranked`, or the reason it was filtered or left unranked), `counted` and `present`. `character`: for each vibe that holds `table`, in shelf order, its `tag_id` and `marks`, one for each area in the order asked for, each a band, its spread and a `fact_id`. `rows` ordered by the spec's weights from high to low, then by component name, with one row for each journey. A row has the component, its label, its `weight`, the `place` of a journey, and for each area the `value`, `percentile`, `utility`, `contribution` and `fact_id`. `facts` holds every fact a cell or a mark cites | 422 `invalid_compare`, `invalid_spec`, 404 `area_not_found` | Yes |
| 8 | `POST /v1/places/search` | `q` (2 to 80 characters), `limit` (1 to 10, default 8) | `places`: `place_id`, `name`, `kind`, and the name of its coarse place. `areas`: the areas that match, each as route 4 gives an area, best first and cut to `limit` | 422 `invalid_query` | Yes |
| 9 | `POST /v1/shares` | `spec`, `exact_destinations` (default false) | `share_id`, `spec` as stored, `coarsened`, `places` of the spec as stored | 422 as route 2 | No |
| 10 | `GET /v1/shares/{share_id}` | | `spec`, `spec_hash`, `coarsened`, `stale`, `original_release_id`, `places`, and the result of ranking it now, as route 2 gives it with the default limit | 404 `share_not_found`, 410 `release_changed` | No |
| 11 | `GET /v1/meta` | | `release_id`, `built_at`, `synthetic`, `preview`, `engine_version`, `catalogue_version`, `gritty_variant`, `counts`, `holds` (whether the release names any place to reach, `journeys`, and whether it holds what any kind of home costs, `costs`), `journey_estimate` (how a journey is estimated, where one of this release may be: the numbers of section 6.10 and the line that stands wherever an estimate is shown. `null` where none may), `rents` (what is said of the rents of this release, where each is of a wider place than the area: `of_a_place`, the line that stands beside a count of the areas a budget to rent left out, and `caution`, what their publisher advises. Neither holds a figure. `null` where no rent of the release is of a wider place), `attributions`, `features`, `tags` (the vibes the release carries, with their recipes, in shelf order), `recipes` (one `RecipeHeld` for each vibe of `tags`, in the same order: section 2.3), `families` (each a `family` and its `label`, in the order of the settings), `defaults` for a renter and a buyer, `limits` with the release's `cutoff_minutes`, `max_text`, `max_body_bytes`, `reason_min_utility` and `trade_off_max_utility`, and `reader`: who reads what is typed, and what people are told of it (section 9.5), and `census`: whether census figures are served, with the heading and the words of the block that offers them, which hold no figure and name no area (section 9.6), and `rough_guides`: for each vibe of `tags` that is a rough guide, its `tag_id`, the `label` and the sentence that says `why`, which every client draws wherever the vibe is shown (section 3.2). It is empty where the release carries no such vibe, and a client takes it to be empty where it is absent | | Yes |
| 12 | `GET /healthz` | | `{"ok": true}`, with no `meta` | | |
| 13 | `GET /v1/areas/{id_or_slug}/census` | Nothing: no body, and a query of any kind is refused | The census figures of one area (section 9.6): `area_id`, `heading`, `date_line`, `notes`, `city`, `output_areas`, `tables`, `source_line`, `derivation_line`, `licence_line` | 404 `area_not_found`, 404 `census_not_available`, 422 `invalid_request` | Yes |
| 14 | `GET /v1/areas/{id_or_slug}/income` | Nothing: no body, and a query of any kind is refused | The household income of one area, as its publisher estimates it (section 9.7): `area_id`, `heading`, `kind`, `definition`, `estimate`, `limits_label`, `lower`, `upper`, `limits`, `none_given`, `year_line`, `modelled`, `notes`, `source_line`, `licence_line`, `source_url`, `open_source` | 404 `area_not_found`, 404 `income_not_available`, 422 `invalid_request` | Yes |

Routes 4, 5, 6 and 11 also answer 304, with no body (section 9.3). Any route can also return 400 `malformed_json`, 413 `body_too_large`, 415 `unsupported_media_type`, 422 `invalid_request` (a field that belongs to no part of the body named above, such as `limit`) and 500 `internal_error`. A path that is no route answers 404 `not_found`, and a method a route does not take 405 `method_not_allowed`. A path with a slash too many, `/v1/rank/`, is no route: it is never redirected, because a redirect has no envelope and repeats the path, a share's id with it, in a header. No route returns 401, 403 or 429 in this build, and none answers with a redirect.

`problem` in `fields` is one of the codes of `check_spec` (section 4), or what a validation error comes to: `missing`, `unknown_field`, `wrong_type`, `not_allowed`, `bad_format`, `out_of_range` or `invalid`. A position in the path of a `check_spec` problem is a position in the spec in id order, which is the order a spec is returned in, and not in the body as it was sent (section 4). A position in the path of a validation error is the position sent, because a body that does not validate was never made into a spec. A part of a `path` is kept only if it is one of Burro's own field names or a position, because the name of a field that should not be there is itself something the sender wrote.

`suggestions` and `unread` on route 1 are counted as `rests_on` is, which the rest of this paragraph describes, and are handled as it is: served to the caller, who holds the text, and never logged, kept about a call, stored in a share, or taken or returned by another route.

`rests_on` on route 1 says which words of `text` each edit of `operations` rests on (section 8.1): a list of `group`, `index`, `start` and `end`, in the order of the six groups, then by edit, then by where the words stand. `start` and `end` are offsets into the text **as it was sent**, the space around it included, though the text is read without that space. They count code points and not UTF-16 units, so a client in JavaScript takes `Array.from(text).slice(start, end)` and one in Swift counts along `text.unicodeScalars`: `text.slice(start, end)` is wrong by one for every character before the words that is two units long, such as most emoji. Every edit that is served is pointed at, the one that is asked about in `clarify` and one that the reducer rejects among them, and no entry points outside the text or at an edit that was not served. No other route takes or returns them. They are served to the caller, who holds the text, and are never logged, kept about a call or stored in a share (section 10.1).

**What version 2 adds, record by record.** A route works out no score, no band, no likeness and no sentence. It reads the release and calls core.

| Record | Field | What it is |
|---|---|---|
| `NamedPlace`, in `places` of routes 1, 2, 9 and 10, and in `place` of a journey's row of route 7 | `place_id`, `name`, `kind` | One for each commute of the spec that is returned, in the spec's order. `name` is the release's own name for the place, the string route 8 gives and a `travel` fact holds in `slots.place`, and never what was typed. `kind` is a `PlaceKind`: a place is never an area. For a share it is the place the stored spec names, which is the one that stands in where a place was replaced. A name says where someone works as its id does, and is handled as one: it is in the body of an answer, and in no log |
| `Suggestion`, in `suggestions` of route 1 | `target`, `label`, `does`, `spans`, `shown`, `follows`, `said`, `choices`, `note`, `read_by`, `add_all`, `needs`, `asks_place`, `named_at`, `options` | An offer in its four parts (section 8.2), with every span counted in the text as it was sent. It holds every field of core's record (section 8.1). An offer none of whose spans is in the text is not served. No field of it holds a word the person typed: `does`, `follows`, `said`, `label`, `needs` and every `label` of a choice are Burro's own words, made from the edits and the catalogue. `said` may hold a number that stands in the text, as an edit does |
| `SuggestionChoice` | `id`, `direction`, `label`, `guess`, `operations` | Core's `Choice` of a suggestion, with which way of its offer it is and whether it is Burro's guess. It has a name of its own in the document, because core has another `Choice`, what a setting is set to, and one document cannot hold two records of one name. `operations` is what a client sends to route 2 if the choice is pressed, with the spec it holds. At most one choice of an offer is the guess, and a guess applies nothing |
| `Span`, in `unread` of route 1 | `start`, `end` | Counted as `rests_on` counts, in the text as it was sent |
| `NotInRelease`, in `not_in_release` of route 1 | `target`, `label`, `spans` | Core's record (section 8.1), with `spans` counted in the text as it was sent. A thing is named whether or not its words can be pointed at. It is handled as a suggestion is: served to the caller, and in no log, no call record and no share |
| `RoughGuide`, in `rough_guides` of route 11 | `tag_id`, `label`, `why` | Core's record (section 3.2): what a vibe that is a rough guide says of itself wherever it is shown. A client draws the label and the sentence as they are served, and writes neither |
| `Holds`, `RecipeHeld`, `WaitsOn`, in `holds` and `recipes` of route 11 | | What the release can answer at all, so that a client offers nothing that could only be turned away: it says so where a person would look for a journey or a budget, and says of a vibe what share of its recipe is held and what it waits on. A client adds up no share of its own |
| `UnmetAt`, in `unmet_at` of route 1 | `category`, `span` | Where the words stand that ask for what nothing measures, where a model said which they are and they are in the text. Every category here is in `unmet` too. What a model files of words that an offer rests on is left out of both: where every word of them that names something is a word of an offer, the person is offered what they asked for, and nothing of it was left out. A word of degree beside the thing, "slightly" or "a bit", belongs to the thing. A model filed the words for how well off a place is as a verdict on what the person can afford, under four offers for the same words. What a model files with no words, or of words that say more than any offer, is kept |
| `model_refused` of route 1 | A boolean | True where a model was asked and its provider would not read what was typed, for safety or for its own terms. The rules read it as they would with no model, so `degraded` is true as well. A client shows one line that says so. False in every other answer |
| `model_pending` of route 1 | A boolean | True where `ask_model` was `false`, a model is on, and the rules made nothing of some word, whether or not it is said to be unread. A client asks again, with `ask_model` left out or `true`, to have what the model adds. False in every other answer |
| `AreaSummary`, in `areas` of routes 4 and 8, and `neighbours` of route 6 | `named` | Core's `Named` (section 2.2), or `null`. Every list of areas holds it, so that the label stands beside the name wherever an area is named |
| `PlacesData`, of route 8 | `areas` | The areas whose name or other name matches what was typed, scored as a place is (section 8.3). An area is somewhere to live and a place is somewhere to reach, so the two are listed apart: an area is never offered as the end of a journey. Every area that bears a name scores 1.0 for it, and comes first |
| `Score`, `ComparedArea` | `counted`, `present` | How many things count in the spec, and for how many of them the area has a figure. Core counts both, from the area's `contributions`. Both are 0 for a compared area that is not ranked: it was not scored |
| `RankedArea` | `strip` | Core's record (section 6.7) |
| `RankData`, `ShareData` | `areas_ranked`, `areas_listed` | How many areas are ranked, which is how many `scores` holds, and how many of them `ranked` holds in full, which is `limit` at most. Where the second is less than the first, areas stand below the last one listed, and a client says so. A list once stopped at 20 of 22 and said nothing. An area that was filtered or is listed apart is in neither count |
| `Unranked`, in `unranked` of routes 2 and 10 | `area_id`, `reason`, `missing` | Core's record (section 6.7), served as it is. An area with too little known of what was asked of the place is here with `character_unknown`, and `missing` names every component it has no figure for, as a `Contribution` names them: `tag:leafy`, `feature:venue_evening`. It is in no `scores` and no `ranked`, so it can never come first. Route 7 gives it the status `character_unknown`, and each of its cells cites the fact that says there is no figure, or the fact of what is known: its journeys and its cost |
| `BandMark`, in `bands` of route 4 | `area_id`, `band`, `spread_low`, `spread_high` | As `tags.json` holds them. All three are `null` for an area that cannot be placed, and it has a mark all the same, so that a map draws it as unknown and never in the middle. `score` and `raw` are not served here: a vibe is shown as a band |
| `CompareRow`, in `rows` of route 7 | `place` | Where the journey of the row is to: a `NamedPlace`, and `null` for a row that is no journey. Every cell of the row is to that place |
| `CharacterMark`, in `character` of route 7 | The same, and `fact_id` | The `tag` fact that holds the sentence, the sources and the date. An area that cannot be placed has one too, which says so (`vibe_unknown`). It is among `facts` |
| `Similar`, in `similar` of route 6 | `area_id`, `fact_id` | Most alike first, by the count the sentence of each gives. `distance` is never served: it is no fact about a place. Empty where too little is known of the area, and no `likeness` fact is then among `facts` |
| `FamilyLabel`, in `families` of route 11 | `family`, `label` | `FAMILIES` of core, in its order |

`spec_hash` on route 3 is the hash of the spec as sent, since route 3 takes no edits, and is the hash route 2 gives for that spec. It is 64 lower-case hex characters. `notice_text` on route 1 is `notice_text(notice, changed)` of core (section 8.4), where `changed` is whether any edit of the answer has `applied[].changed` true.

**What the document says of a field that has a default.** `TagWeight.toward` and `Assumption.word` have a default in core, so `contracts/openapi.json` does not list them as required. `toward` may be left out of a body, and is then `high`. Both are always returned. So it is with a field that is added and that a client may ignore: `Tag.sureness` and `rough_guides` of route 11 each have a default, the document does not list either as required, the service always returns both, and the contract stays at version 2. A client that was built before them reads a release as it did. So it is with every field that was added since the document was last published: `of` and `rents` of a cost, `rents` of route 11, and `said_with_attribution` of a source and of the source of a fact. None is required, none took the place of a field, and no field changed its shape. **A value that is added to a list of codes is one a client may pass over.** Six were added to `template`, `cost_rent_recorded`, `budget_under_recorded`, `budget_over_recorded`, `budget_at`, `budget_at_median` and `budget_at_recorded`, and two to the ids of a feature, `highstreet_conserved` and `road_traffic_nearby`. The website gives a fact of a template it does not hold no columns and no sentence of its own, and the app draws nothing for a code it does not know. Each draws every other fact as it did. So the contract stays at version 2 for them too. What a client may not pass over is a promise and no part of the document's shape: a client that draws a credit draws what is said with it, and one that names a rough guide says that it is one. A `TagEdit` has no default: a body that leaves `toward` out is refused with 422 `invalid_operations`, `missing` at `operations.tag_ops[n].toward`. The id of a vibe that was retired is no `TagId`, so it is refused where it stands: `not_allowed` at `spec.tags[n].tag_id`, with `invalid_spec`. A vibe that is a `TagId` and that the release does not carry, the other way gritty was built, is `not_in_release`: from `check_spec` in a spec, and as a rejected edit in `operations`.

In a comparison, `value` is the feature's value, the minutes of the journey of the row, and for `budget` what the budget was held against: the upper quartile, or the median of a cost with no range. `percentile` is the feature's percentile, and `null` for a journey, `budget` and a vibe. Until version 2 it held a vibe's score. A vibe is shown as a band, which is in `character`, and the score it is ranked on is no figure of its fact, so no cell holds it to be printed. The rows of `tags` on route 6 are the rows of `tags.json`, `score` and `raw` among them: they are for ranking, and a client never prints them. `utility` and `contribution` are `null` for an area that is not ranked: it was not scored. Every cell that holds a number names the `fact_id` that carries its source and date, because a comparison shows numbers about places like any other page. Every cell of a row is said from one side: the facts of a comparison are built with the spec, so `standing` is from the side that counts as better in that spec, the same for every area (section 7.3).

**A comparison has one row for each journey, with the same destination across the row.** The journeys count as one thing (section 6.2), and until 1.5.0 they had one row, `commute`, which held for each area the one journey that drove its score. With two places in a search, one area was timed to the works beside another timed to the campus, and a journey with no time was not shown at all. Now each commute of the spec has a row, in the spec's order, where the journeys count:

| Field of a journey's row | What it holds |
|---|---|
| `component` | `commute.<place_id>.<mode>`, as core keys a journey (`journey_key`, section 7.2). No row is named `commute` |
| `label`, `weight` | "Journey", and `commute_weight`: the weight of the journeys together, the same in each of their rows. A client says it once |
| `place` | The place the journey is to, by the release's name |
| `value` of a cell | The minutes of the time that is scored, for every area, ranked or not. `null` where the release holds no time, or only that the journey is beyond its cutoff |
| `utility` of a cell | What that journey is worth, which is the `utility` of its `CommuteLeg`. `null` where it has no time, and for an area that is not ranked |
| `contribution` of a cell | What the journeys add to the fit, which is one figure for them all. It stands in the cell of the journey that drove the score, the first fact the component cites, where that journey alone decides it: `commute_combine` is `slowest`, or the spec holds one journey. It is `null` in every other cell. Where `commute_combine` is `mean` and there are two journeys or more, every journey counts, and what one of them adds is not something `rank()` reports: no cell holds it, and a route does not work it out (section 13) |
| `estimate` of a cell | The band of that journey for that area, where the release holds no time for it and it is estimated (section 6.10). `value` is `null` beside it: an estimate is never given in minutes. `null` in every other cell |
| `fact_id` of a cell | The `travel` fact of that journey for that area, or its `missing` fact, whose template is `missing_journey`, where it has no time and no estimate. Every area has one or the other, ranked or not. So a journey with no time is shown as having none, and the journey that left an area out is shown with the limit it is over |

`counted` and `present` count the journeys as one thing, as the score does, so a comparison of a spec with two journeys has one row more than `counted`.

No list on the wire mixes types. `scores` holds objects and not pairs such as `[area_id, score]`, because one OpenAPI file has to generate a TypeScript client and a Swift one, and a list of mixed types generates badly in both.

### 9.3 What "pure" means here

| Routes | Property | Caching |
|---|---|---|
| 4, 5, 6, 11 | A function of the release alone, but for `reader` of route 11, which is of how the service is set | `Cache-Control: no-cache`, `ETag` set to the release id in quotes. On route 11 the tag is the release id, a full stop, and eight characters that change with what people are told, so that an answer which tells of another reader is never said to stand. The address does not name the release, so a browser may keep the answer and must ask each time whether it still stands. A request whose `If-None-Match` names the loaded release, alone or in a list, weak or strong, is answered 304 with the same two headers and no body. `*` names no release and is answered in full. An area the release lacks is 404 whatever is held. What was sent is compared and never sent back or logged |
| 2, 3, 7, 8 | A function of the body and the release. They are `POST` only to keep text and destinations out of URLs | Not cached. Ranking takes milliseconds, so there is nothing to save |
| 1 | Depends on a model when one is configured | Not cached in this build (section 11) |
| 9, 10 | 9 makes a random id. 10 depends on which release is loaded | `Cache-Control: no-store` |
| 13 | A function of the census and of the name of the area | `Cache-Control: no-store`, so that no browser keeps the figures, and `X-Robots-Tag: noindex, nosnippet`. It sets no `ETag` and never answers 304 |
| 14 | A function of the household income that stands beside the release | As route 13 |

### 9.4 Behaviour worth pinning down

- **Form mode.** Route 11 returns everything a form needs: the vocabulary, both defaults and the limits. Routes 2, 3, 7 and 8 need no model. With no key, a slow model or a capped one, the product is that form.
- **The cap on calls to a model.** The whole service makes no more than 30 calls to a model in a minute and 2,000 in a day, by the clock in UTC, unless `BURRO_MODEL_CALLS_PER_MINUTE` or `BURRO_MODEL_CALLS_PER_DAY` says otherwise ([ADR 0032](../adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md)). A call is counted as it is about to be made, and nothing of who made it is read or kept. Over a cap no call is made, and the reader raises `ModelCapped`, so the route answers as it does where a provider says that it is capped: 200, from the rules, with `degraded` true. No route answers 429. With either cap at nought no model is ever called, and route 11 says that the rules read.
- **Falling back.** Route 1 uses the interpreter in `Deps`, with a timeout from settings, 6 seconds by default. The rules read first, and a model is asked only where they left words unread (section 8.2). With `ask_model: false` the rules answer at once and no model is asked, so what the rules offer never waits on a model. On `ModelTimeout`, `ModelCapped`, `ModelRefused` or `ModelError` it answers from `RuleInterpreter` with `degraded` true, its suggestions and what it left unread among the answer. So it does on whatever else the path of a model raises, of any kind: the route is the edge for it, and nothing of it reaches the handler of section 10.1 or the server. It never returns 5xx because a model failed. A model that answers `off_topic` where the reader made an edit, noticed something, or heard a request about who lives somewhere, is answered for in the same way, and the call keeps its status (section 8.2). The interpreter in `Deps` is `RuleInterpreter` itself unless a key is present in the environment, or a test passes another. The route keeps its own deadline around an interpreter that is not the rules, because a client's timeout times each read and not the whole call.
- **Edits first, then the check.** Routes 1 and 2 apply the edits with the reducer and run `check_spec` on the spec they leave, not on the spec that was sent. A spec kept from an older release, which names a place or an area the loaded release has dropped, is refused as it stands and accepted with the edit that takes the name out (section 5.3 rule 6). With no edit, or with one that leaves the problem in, the answer is the same 422 as before, and its paths are into the spec after the edits. Route 1 reads the words before it can know whether the spec will pass, so a spec that is refused there has still cost a call to the interpreter, and the call is on record. Routes 3, 7 and 9 take no edits and check the spec as sent.
- **Defaults.** A default that is served, by route 11 or to a first prompt, leaves out any weight the loaded release cannot rank, so a real release with fewer features does not refuse its own default.
- **Whether Gritty is carried** is the release's to say (`manifest.gritty_variant`), and the API has no setting for it. Route 11 serves the vibes the release carries, and every route that names a vibe reads them from the release and never from `TAGS`. To serve a release that holds no recorded crime, build it and name its folder: `burro-release build-synthetic --gritty a --out FOLDER`, then `BURRO_RELEASE_DIR=FOLDER/syn-2026-09-23-02`.
- **A choice that is pressed** is an edit like any other. A client sends the `operations` of the choice to route 2 with the spec it holds. Route 1 applied nothing of a prompt that is not plain, so the spec it returned is the spec that was sent.
- **The OpenAPI document** is published as `contracts/openapi.json` and is not served by the running service. An operation id is the name of its route. A route is named for its function, but for route 2: the route is `rank`, and its function is `rank_areas`, because it stands beside core's own `rank`.
- **Nothing is kept for a search.** The server holds no search between requests. The client holds the spec and sends it again to rank, to explain and to share. A spec names where someone works, and the only place one is stored is a share, which a person makes on purpose. This is why there is no search id, and no route that returns a search by id: such an id would sit in a URL, a URL reaches logs that Burro does not control, and for as long as the search was kept the id would unlock its destinations.
- **`share_id`** is 128 random bits, URL-safe. It is never derived from the spec, so holding a spec does not reveal a link.
- **Coarsening.** Unless `exact_destinations` is true, route 9 replaces each commute's `place_id` with its `coarse_place_id` before storing. If two commutes come to the same coarse place, the one with the lower `place_id` before coarsening is kept and the other is dropped. The stored spec therefore ranks a little differently from the search it came from, and `coarsened` says so: it is true only when a destination was in fact replaced or dropped.
- **A changed release.** A share outlives releases: route 10 re-ranks on the loaded release and sets `stale` when that differs from `original_release_id`. If the stored spec no longer passes `check_spec`, because a place, an area or a feature has gone, the answer is 410.
- **Stores.** `ShareStore` keeps a share in memory until restart. It is a protocol, and a stored share holds `share_id`, `spec`, `coarsened`, `original_release_id` and `created_at`, and nothing about who made it.

### 9.5 Who reads what is typed

`reader` of route 11 says who reads what a person types, and what people are told of it. It is made by `providers.choose` with the reader itself, so the service cannot send to one provider and tell people of another, or of none (ADR 0019).

| Field | Meaning |
|---|---|
| `model_reads` | False where the rules read, and nothing typed is sent to a language model |
| `provider`, `company` | The provider that reads, one of `gemini`, `openai`, `deepseek`, `anthropic`, and the company as a person would know it. Both `null` where no model reads |
| `notice` | All that people are told, as one paragraph: that what is typed is sent to a language model run by the company, to be read, what goes with it, that nothing private should be typed, and that Burro itself keeps nothing of it. It states nothing about the company as fact (ADR 0023). Where no model reads: "What you type is read by rules that are part of Burro. It is not sent to a language model." |
| `terms_url` | The address of the company's own terms, for a link beside the notice. `null` where no model reads |
| `settings_sent` | Whether the search settings go to the provider with the words |

A client shows `notice` by the box before anything is typed, as it was served, and writes no provider's name and no terms of its own. Nothing of how the service is set is served: no key, no variable and no model's name.

A page may be built ahead of time, and the service may since have been set to another reader. So a client asks route 11 as the page opens, shows nothing of what the page was built on in its place, and sends no sentence to route 1 until it has been answered. The tag of route 11 changes with what is told (section 9.3), so an older answer is never kept.

### 9.6 The census of an area

Route 13 is the only route that reads the census (section 2.10), and the census is all it reads but the name of the area. It stands apart from every route that ranks.

| Point | Detail |
|---|---|
| Takes | One area, by its id or its slug, in the path. No body and no query: a query string of any kind is answered 422 `invalid_request`, with no field named, and is never read. Any other method is 405 |
| One area | No route serves the census of more than one area. So no client can put one area before another by a figure, or set the figures of two areas side by side |
| `data` | Core's `CensusPanel`, as `panel()` makes it. Every word of it is core's or the publisher's: a client writes the words of a button and no other |
| A table | `table_code`, `kind`, `title`, `caption`, `definition`, `shown_only`, `note`, `columns`, `reason`, `left_out`, `rows`, `source_id`, `source_url`, `source_label`. Where the table is left out for the area, `rows` is empty, `reason` is `too_few` or `not_held`, and `left_out` is the sentence that says so |
| A row | `code`, `heading`, `label`, `depth`, `share`, `percent`, `count`, `city_share`, `city_percent` (section 2.10), and nothing else |
| Its source | `source_id` is a source of the census, and is named on the website's page of sources. `source_url` is the publisher's page for the table, one press away, and is empty for a made-up table |
| Errors | 404 `area_not_found` for an area the release lacks. 404 `census_not_available` where the service serves no census |
| Headers | `Cache-Control: no-store`, `X-Robots-Tag: noindex, nosnippet`, and the two flags of the release as ever |
| Log | The route's template, the status and the time taken. Never the area, and nothing of the census (section 10.1) |
| Route 11 | `census` holds `available`, `heading` and `intro`. With no census served, `available` is false and the two are empty |
| Every other route | Gains nothing. No body the service takes has a field for a census figure, and no schema but route 13's and `CensusOffer` of route 11 names a record of the census |

**Where the census is looked for.** With nothing set, the service serves the committed made-up release with the made-up count that was made for it. With a release named by `BURRO_RELEASE_DIR`, the census is looked for beside it, in the folder named for the release with `-residents` after it. A folder that is not there is no census: the service starts, route 13 answers 404 `census_not_available`, and route 11 says `available` false. `BURRO_CENSUS_DIR` names another folder, and then a folder that is not there stops the service. A folder that is there is held to every rule, and the service does not start on one that breaks any. `BURRO_CENSUS=off` serves no census whatever is there, so that the panel can be taken down in one step.

**It never reaches ranking.** The release is handed to `rank()`, to the facts and to the reader. The census is handed to route 13 and to `offer()`, and to nothing else. Four tests try, each over the five kinds and over what a caller might call them: a spec that weighs one as a feature, as a vibe, as a field of its own, as a filter or as a rule about an area; an edit that names one; a body with a field for one; and eleven sentences that ask for one. Each is refused with a code of this contract, or makes no edit, and no answer holds a row of the census. A fifth test serves two services the same searches, one with every area's figures handed to the next area, and finds every answer of routes 1 to 12 the same, byte for byte. A sixth takes the census away and finds one answer changed: what route 11 says is offered.

### 9.7 The household income of an area

Route 14 is the only route that reads household income (section 2.11), and it is all the route reads but the id of the area. **No route ranks on it, compares on it, or explains by it**, and a test holds each.

| Rule | Detail |
|---|---|
| What it takes | An area of the release, by its id or its slug. No body, and a query of any kind is refused with 422 `invalid_request`, whatever it holds |
| One area | No route serves the income of more than one area. So no client can put one area before another by it, or set the figures of two areas side by side |
| What is served | `shown()` of core, as it is. No figure is worked out by the service |
| Errors | 404 `area_not_found` for an area the release lacks. 404 `income_not_available` where the service serves none |
| Headers | `Cache-Control: no-store` and `X-Robots-Tag: noindex, nosnippet`, as route 13 |
| Log | The route's template, the status and the time taken. Never the area, and no figure (section 10.1) |
| Route 11 | `income` holds `available`, `heading` and `intro`. With none served, `available` is false and the two are empty |
| Every other route | Gains nothing. No body the service takes has a field for it, and no schema but route 14's and `IncomeOffer` of route 11 names a record of it |

**Where it is looked for.** As the census is. With nothing set, the service serves the committed made-up release with the made-up estimates that were made for it. With a release named by `BURRO_RELEASE_DIR`, it is looked for beside the release, in the folder named for it with `-income` after it, and a folder that is not there is none. `BURRO_INCOME_DIR` names another folder, and then a folder that is not there stops the service. `BURRO_INCOME=off` serves none, whatever is there.

**It never reaches ranking.** `tests/test_income.py` of the service holds each of these by itself, for routes 2, 7 and 3: the route answers the same, byte for byte, where every area's figures are handed to the next area and where they are taken away, and no answer of it holds a figure of any area or a word for income. A spec that weighs it as a feature, as a vibe, as a field of its own, as a filter or as a kind of home is refused, and so is a body with a field for it. Six sentences that ask for it make no edit and no offer.

## 10. Privacy in the API

### 10.1 What may and may not be logged

| May be logged | Never logged, stored in an error report, or written to a table |
|---|---|
| Request id, method, **route template** (`/v1/shares/{share_id}`), status code, latency | The prompt, or any part of it |
| Release id, engine version, `synthetic`, `preview` | Text typed into place search |
| Interpreter name, provider, model id, interpret status, `degraded` | A request or response body, whole or in part |
| Why a provider that was set is not used, or which cap on calls to a model was reached (`reason`), as one of ten fixed words | A provider's key, or anything else that was set: a value in the wrong variable could be a key |
| Token counts | A `place_id`, a `destination_id`, a place name, a `fact_id` (a journey's holds a `place_id`) |
| The number of edits in each group, and of rejections by reason | A raw path, a query string, a `share_id` |
| Unmet categories and assumption codes | An exception's message |
| Error code, exception type, and the file, line and function of each frame | A header, the `Origin` among them, a cookie, an IP address |
| | The words an edit or an offer rests on, as a model copied them or as offsets into the text (`rests_on`, `words`, `spans`, `shown`, `named_at`, `unmet_at`) |
| | What was noticed in a prompt and what was left unread: a suggestion, its label, its spans, its choices, an unread stretch, or how many there were of either |
| | What a browser says it holds (`If-None-Match`) |
| | A spec, a hash of one, plain or under a key, or any other value worked out from one |

A `place_id` is an id from the release and not the user's words, but it says where someone works or where their child goes to school. It is kept only inside a stored share, and there it is the coarse place unless the sender chose otherwise. The name of a place says the same, and is handled as the id is: `places` is worked out from the spec when an answer is made, served in its body, and kept nowhere.

**What was offered is served and never written.** A suggestion names what was noticed, a journey's names a place, and its spans and the unread stretches are offsets into what was typed. None is logged, none is counted in a line, and none is kept about a call or in a share. The line for a prompt in which four things were noticed is the line for one in which one was, but for how long it took: a test holds it to that. The status `suggest` is in the line and in the call record, as `clarify` is. It says that the prompt was not plain and that something was noticed, and nothing of what.

**Nothing worked out from a spec is logged, or kept about a call.** A spec is stored in one place, a share, which a person makes on purpose (section 9.4). A spec is a small space, so its plain hash gives the spec back to anyone who can try specs: from one log line the README's example gave up its workplace, cap, budget and tag in 21 seconds. For a day the log held the hash under a key made at start-up instead. That could not be reversed, but it could confirm a guess: whoever read the log and could call the service posted guesses and watched for the same value in a new line, and had the workplace after 247 requests. Nothing needs to know that two calls were about the same search, so since 2026-09-23 there is no hash of a spec in a log line or a call record, of any kind, and no key: `logs.LOGGABLE` holds no field for one, `CallRecord` has none, and the service makes no HMAC. The plain hash is served in responses (routes 1, 2 and 10), to the client that holds the spec it is the hash of.

What a line can still say of a search is what it says of any: the status and the error code, how long it took, and on route 1 how many edits were made, how many were rejected for each reason, and the codes of what was assumed and of what could not be met. On routes 2, 3, 7 and 9 a test posts the spec that was searched and guesses at it, and asserts that every line and every record is the same but for its id. **On route 1 that is not so, and the line is not the same for every spec.** Its four fields `edits`, `rejections`, `unmet` and `assumptions` are worked out from the words and the spec together: "I work at Cindermoor Works" assumes a mode where the spec does not hold that place and nothing where it does, and "a bit cheaper" is rejected as `nothing_to_change` where the spec holds no amount. Each holds a count or a code from a closed list, and never an id, a name or a number of the spec; none can be matched to a spec without the words, which are in no line; and the call record of route 1 is the same for every spec. A test holds the line to exactly that (`test_what_a_line_says_of_a_reading_is_counts_and_codes_and_nothing_of_the_spec`). Whether even that is too much is an open point (section 13), and is the founder's to settle: the four are entries of `logs.LOGGABLE`.

How the rule is kept:

1. The server's own access log is switched off. One middleware writes the request line, from the route template.
2. The handler for validation errors builds `fields` from `loc` and `type` only. pydantic's `input`, `ctx` and `msg` are discarded, because they can repeat what was sent.
3. `log_failure(exc)` is the only way an exception is logged. It writes the type and the frames. It never calls `str(exc)`.
4. Logging is set up so that no third-party library logs below `WARNING`, whatever level the library sets on itself, and a library's line is cut down to where it came from.
5. Logging is a list of what may be written and not a scrubber of what may not. A line is an event name and named fields, a field that is not on the list cannot be logged, and no message is ever formatted. A failure is written at the level of an error.
6. Nothing is written to disk. The share store and the call log are in memory. The share store keeps the latest 50,000 and lets the oldest go.
7. No hash of a spec can be logged: no field on the list could hold one, and the routes work none out but the plain hash they serve. Nor can where an edit's words stand, or what was offered: `rests_on`, `words`, `shown`, `named_at`, `unmet_at`, `suggestions`, `unread`, `spans`, `choices`, `label` and `places` are no fields of the list or of the call record, and the words a model copied are held in a field that no `repr` shows.
8. No response is a redirect, so no path is ever sent back in a header.

**What is said of a provider is a fixed word, and never what was set.** Two lines name a provider, both at the level of a warning. `model_not_used` is written once, as the service starts, where something was set and no model reads: it holds `provider`, where what was set names one of the four, and `reason`, the first thing that does not hold: `no_provider`, `unknown_provider`, `no_key`, `unfit_key`, `terms_not_accepted`, `unfit_model`, `not_for_people` or `capped_at_nought`. With nothing set it is not written. `model_resting` is written each time an adapter begins to leave a provider alone, after three refusals in a row: it holds `provider` and nothing of any call. A provider that will not read what was sent gets no line of its own: the line of the call says `refused` in `call_status` (section 10.2). A third line names no provider: `model_capped` is written the first time a cap on calls is reached in its minute or in its day, and holds `reason`, which is `calls_per_minute` or `calls_per_day`, and no count. Each word is the value of an enum, so no line can hold a key, a model's name as it was set, or a word of a person's.

### 10.2 The call-metadata record

One record for each call to route 1 and route 3.

| Field | Type |
|---|---|
| `call_id`, `at` | UUID; timestamp, to the second |
| `endpoint`, `interpreter` | `interpret` or `explain`; `rule`, `model` or `template` |
| `provider` | the provider that was asked, one of the four by name, or empty where the rules read |
| `model` | the model that was asked for, or empty |
| `status` | `ok`, `suggest`, `clarify`, `off_topic`, `policy_redirect`, `timeout`, `capped`, `refused`, `error` |
| `degraded` | bool |
| `input_tokens`, `output_tokens`, `cache_read_tokens`, `latency_ms` | int |
| `release_id`, `engine_version` | str |

Every string field is an enum or has a fixed pattern, so none can hold free text. There is no hash of the prompt: a short prompt can be guessed from its hash. Nor is there a hash of the spec, plain or under a key, for the reasons of section 10.1. Records expire after 30 days, and the in-memory log also keeps no more than the latest 10,000, so it cannot grow without end.

It is adding a record that lets the old ones go. The service adds and never reads, so a log that expired records only when it was read would expire none. Age is measured from the latest time any record has carried, so a clock that is put back brings nothing back, and a record that arrives already too old is not kept. Every record that is too old is let go, wherever it stands: records stand in the order they were added, which is not the order of time once a clock has been put back, so an old record can stand behind a young one. `records(now)` lets go of what is too old at `now` as well. The rule is written on the `CallLog` protocol, for whatever takes the place of the log in memory.

### 10.3 Tests that must exist

Each privacy test plants a canary, a string found nowhere else, in the prompt, the place search and a destination name. It then collects every log record, everything written to standard output and standard error, every call record and every error response, and asserts the canary is absent.

| Test | Proves |
|---|---|
| `test_interpret_timeout_does_not_log_the_prompt` | The timeout path is clean |
| `test_interpret_validation_failure_does_not_log_the_body` | The validation path is clean |
| `test_validation_error_response_does_not_echo_what_was_sent` | `fields` holds paths and codes only |
| `test_unhandled_error_logs_the_type_and_not_the_message` | An exception built from user text leaks nothing |
| `test_place_search_text_never_reaches_a_log` | Route 8 is clean |
| `test_request_log_names_the_route_template_not_the_path` | No `share_id` and no area slug in a log |
| `test_call_record_has_no_field_that_can_hold_free_text` | Every field is an int, a bool, an enum or a patterned string |
| `test_interpret_result_holds_no_user_text` | The canary is absent from the whole of route 1's response |
| `test_explainer_input_holds_no_user_text` | `ExplainInput` has no field for it |
| `test_share_coarsens_destinations_unless_asked_not_to` | The stored spec holds coarse places |
| `test_share_id_is_not_derived_from_the_spec` | Two shares of one spec differ |
| `test_every_response_carries_the_synthetic_flag` | Every route, errors included |
| `test_no_route_takes_typed_text_in_a_path_or_query` | Read from the app's route table |
| `test_no_route_but_a_share_returns_a_spec_it_was_not_sent` | Nothing is kept for a search |
| `test_nothing_worked_out_from_a_spec_is_logged_or_kept` | The reviewer's search finds nothing in a log line or a call record, nothing in either is as long as a hash, and the plain hash is still in the response |
| `test_a_guess_at_a_spec_cannot_be_confirmed_from_the_log` | The search that was made and every guess at it leave the same lines and the same record |
| `test_the_service_holds_no_key_and_nothing_a_spec_could_be_kept_under` | There is no key to look after, and no module that makes an HMAC |
| `test_what_a_browser_says_of_itself_is_neither_logged_nor_sent_back` | The `Origin` is in no line, and what is sent back is the entry of the list |
| `test_a_name_the_model_brought_itself_is_left_out_and_appears_nowhere` | A name that is left out is left out in silence |
| `test_what_is_withheld_from_a_model_is_withheld_in_silence` | Checks 1, 2, 6 and 13 of section 8.2 at once, with the canary in the words and in the model's answer |
| `test_what_is_withheld_for_doubt_is_withheld_in_silence` | Rules 3 to 5: what was withheld, and why, is in no line |
| `test_an_answer_with_words_where_its_numbers_belong_is_not_logged` | Rule 9: the failure is logged by its type, and the answer is not |
| `test_a_stale_spec_is_put_right_without_the_place_being_named` | The place a spec is repaired of is in no log, whether or not the release has it. Words put no spec right, whoever reads them: nothing a model reads is applied |
| `test_the_words_an_edit_rests_on_are_returned_as_offsets_and_written_nowhere` | `rests_on` is in the response of route 1, for the reader and for a model, and the words are in no response, line or record |
| `test_where_the_words_stand_is_written_nowhere_when_a_model_fails`, `test_where_the_words_stand_is_written_nowhere_when_the_route_itself_fails` | The same on every failure path: a timeout, a cap, an error, an answer that quotes the person and does not fit the schema, a spec that is refused after the words were read, and a failure of the service. On each, for a plain prompt and for one that is not, with the canary in what was left unread |
| `test_no_other_route_takes_or_returns_where_the_words_stand`, `test_where_the_words_stand_cannot_be_logged_or_kept_about_a_call` | No other route takes or returns `rests_on`, `suggestions` or `unread`, route 1 does not take them back, a share does not store them, and no log line or call record has a field for them |
| `test_what_a_line_says_of_a_reading_is_counts_and_codes_and_nothing_of_the_spec` | What differs in route 1's line when only the spec differs is four fields of counts and codes, and the call record does not differ |
| `test_what_was_noticed_and_what_was_left_unread_are_offsets_and_written_nowhere` | For the reader and for a model: the canary stands in the unread stretches and beside a place, an area and an amount that are noticed. The answer points at it and holds no word of it, and no line or record holds the canary, a name, an id or a figure |
| `test_what_a_line_says_of_a_prompt_does_not_tell_what_was_noticed_in_it` | The line and the record are the same however much was noticed, and whatever it was |
| `test_the_name_of_a_place_is_in_an_answer_and_in_no_line` | `places` is served by routes 1, 2, 9 and 10, and `place` by route 7, and no name is in a line or a record |
| `test_what_a_browser_says_it_holds_is_compared_and_never_logged_or_sent_back` | `If-None-Match` with the canary in it: the tag sent back is the release's own, and the line is the line of any other request |

## 11. What is deliberately left out

| Left out | How it attaches later, with no change to what is built now |
|---|---|
| Accounts and sign-in | A dependency that reads an identity from a header. No route here needs one, and no spec or share holds a user id |
| Shortlists | New routes over a new table of `user_id` and `area_id`. The area id is already immutable |
| Payments and entitlements | A check placed in front of routes 1 and 3. Those are the only routes that can cost money |
| A limit for each caller, and a check for a bot | Middleware, or `admit`. A refused call to route 1 answers from the rule interpreter, never with a login wall. The cap on calls to a model is built, for the whole service and for no one caller (section 9.4) |
| Streaming | Route 3 stays the snapshot and the source of truth. A streaming route re-emits the same verified sentences |
| A model-written explanation | A second `Explainer`. **`verify()` must be extended first, and no model explainer may be attached until it is.** `explain()` enforces it: it takes `TemplateExplainer` and refuses any other with a `TypeError` that names this row (section 7.5), so the check in `explain()` is changed in the same change that extends the verifier. As it stands `verify()` checks numbers and capitalised names, which is enough for fixed text and not for a sentence a model wrote (section 7.4, what the verifier does not check). Before a model's sentence is shown: (1) run `POLICY_LEXICON` and the group words of section 8.4 over it, and fail a sentence that says who lives somewhere; (2) widen the banned words into a list of words of safety and of judgement, "secure", "respectable", "desirable", "up and coming", "crime-ridden" and the like; (3) allow a model's sentence only the words that occur in the cited fact's label, slots and template, plus a short list of connectives, so that a name in lower case, a unit said of the wrong number and a comparison run the wrong way all fail for holding a word nothing allows; (4) turn the two tests that are marked as expected to fail, `test_a_sentence_about_residents_or_safety_is_rejected` and `test_a_name_in_lower_case_or_a_claim_about_residents_is_replaced`, into tests that pass |
| A run against a provider of a model | Four adapters are built and wired in, and each has only ever met a stand-in. A provider waits for a key, for its terms to be accepted by name, and for a run of the evaluation set ([models.md](models.md), sections 7 and 9) |
| A cache in front of the model | A wrapper around an `Interpreter` or an `Explainer`, in memory, expiring after 24 hours, keyed by an HMAC under a key made at start-up and never stored. With no model to pay for there is nothing for it to save |
| Real data ingest | Pipeline steps, each starting with `Registry.require`, ending in `write_release`. The release format and everything that reads it stay as they are |
| Routing and real travel times | A pipeline step that fills `travel.json`, or a release in another format behind the `Release` protocol. `rank()` sees only `travel()` |
| The database | `ShareStore` and `CallLog` are protocols. A Postgres implementation replaces the in-memory one. `CallRecord` is already column-shaped |
| Several releases loaded at once | `Deps` holds one release today. Route 10 already reports `stale` |
| An error tracker | `log_failure` is the one place an exception is reported, so it is the one place to attach a tracker, with bodies off |
| Route detail from a journey planner | A display-only field on route 6. Never a ranking input |
| The attributed excerpt on profiles | A new release file and a field on route 6. Never sent to a model |
| Generated clients | `contracts/openapi.json` is written by `make openapi` and a test fails when it is out of date. The clients are generated from it when the first one is built |
| Shrinking small-count rates toward the borough mean | A pipeline concern. It changes `value`, and nothing downstream |

## 12. Tests each part must ship

All run offline, side by side in `make ci`, and the limit on how long the whole suite may take is the one `AGENTS.md` states (ADR 0020). `evals/` holds the reader to cases of its own (evals/README.md): no case may be read backwards, and every case that is marked plain must be read correctly. Section 10.3 adds the privacy tests. A generated test draws a fixed sample in `make ci`, the same sentences every time, and runs in full under the marker `full`: `make test ARGS="-m full"`.

| Part | Test | Protects |
|---|---|---|
| core | `test_worked_example_ranks_as_the_contract_says` | Section 6.8, to four decimals: filters, decay, budget fit, rebalancing, order |
| core | `test_rank_gives_the_same_result_every_time` | Determinism, over 100 calls and shuffled input order |
| core | `test_missing_feature_is_dropped_and_weights_rebalanced` | 6.6 |
| core | `test_hard_filter_keeps_an_area_it_cannot_test` | 6.1 |
| core | `test_slowest_destination_drives_the_score` | 6.4 |
| core | `test_canonical_form_matches_the_published_vectors` | 4.2, and that provenance does not change the hash |
| core | `test_slider_and_chat_edits_reach_the_same_spec` | One reducer |
| core | `test_bad_edit_is_rejected_and_the_rest_applied` | 5.3 |
| core | `test_inferred_crime_weight_is_rejected`, `test_an_inferred_edit_never_weighs_a_vibe_whose_recipe_holds_recorded_crime` | 5.3 rule 8 |
| core | `test_a_word_burro_has_no_measure_for_is_offered_what_is_nearest_and_told_what_it_lacks`, `test_recorded_crime_that_is_chosen_from_an_offer_counts_as_asked_for_by_name`, `test_cheap_is_no_verdict_burro_gives_and_is_heard_as_that` | 8.2: the first words of a newcomer |
| core | `test_built_as_a_scale_a_word_that_is_read_into_it_is_offered_and_says_it_counts_crime` | 8.2: crime counts only when it is asked for by name |
| core | `test_nothing_describes_residents_but_the_four_measures_and_the_two_vibes_that_hold_one`, `test_the_guard_lets_the_one_name_of_transport_noise_through_and_refuses_every_other` | A denylist of resident words against every id, label and definition, but for the four measures that count who lived somewhere and the two vibes that hold one. One name of a measure of the place is let through, as the whole of a name: the share of residents that transport noise reaches |
| core | `test_the_measures_that_say_who_lived_somewhere_are_these_four_and_each_says_so`, `test_no_name_that_counts_residents_holds_a_word_for_what_was_not_decided_on`, `test_a_recipe_that_counts_residents_is_read_high_runs_one_way_and_is_no_one_figure`, `test_a_vibe_that_counts_residents_holds_them_at_no_more_than_40_in_100`, `test_the_release_holds_no_count_of_residents`, `test_likeness_is_never_counted_on_who_lives_somewhere_whatever_a_flag_says`, `test_a_spec_may_ask_for_more_of_who_is_counted_and_never_for_fewer`, `test_a_vibe_that_counts_who_lives_somewhere_has_no_low_end_to_ask_for`, `test_a_vibe_that_counts_who_lives_somewhere_is_on_a_result_only_where_it_was_asked_for`, `test_what_counts_who_lives_somewhere_is_never_what_an_area_has_most_or_least_of` | The six rules of a feature that counts who lives somewhere (section 3.1), and the rules of a recipe that holds one (section 3.2) |
| core | `test_a_phrase_for_who_is_counted_is_offered_towards_more_and_never_applied`, `test_no_choice_of_what_counts_who_lives_somewhere_is_ever_less`, `test_a_word_that_turns_before_who_is_counted_draws_the_notice_and_nothing_else`, `test_a_request_about_who_lives_somewhere_is_offered_nothing_that_counts_them` | Who is counted is offered and never applied, towards more and no other way, and a wish for fewer of anyone draws the notice and nothing else (sections 8.2 and 8.4) |
| api | `test_what_counts_who_lives_somewhere_is_never_a_models_to_offer`, `test_the_words_the_rules_offer_who_is_counted_for_are_the_rules_to_read`, `test_what_a_model_reads_into_words_for_who_is_counted_is_dropped` | No model offers what counts who lives somewhere, whatever it answers |
| core | `test_invented_venue_or_changed_number_is_replaced_by_a_template` | The verifier, with a fake explainer that plants each |
| core | `test_every_template_passes_the_verifier` | 7.3 |
| core | `test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served` | 8.4 |
| core | `test_core_imports_nothing_that_does_io` | Purity |
| core | `test_every_fact_names_a_source_and_a_date` | 7.1, for every kind of fact, journeys and stations included |
| core | `test_a_time_that_is_not_known_is_none_and_never_zero` | 2.6 and 6.7 |
| core | `test_a_step_moves_the_number_unless_it_is_at_a_limit` | 5.2, with a buyer's budget at 50,000, where 5% rounds away |
| core | `test_release_with_a_changed_file_is_refused` | 2.8, `open_release` |
| core | `test_every_comparison_said_of_the_release_is_literally_true` | 7.3, on every feature fact of the committed release, from both sides, and on every vibe |
| core | `test_what_a_person_says_decides_which_area_comes_first` | 5.2 and 5.3 rule 11, on the committed release: four wishes, four different areas first |
| core | `test_the_defaults_give_way_the_first_time_a_wish_is_applied` | 5.3 rule 11 |
| core | `test_switching_tenure_keeps_everything_the_person_set` | 5.3 rule 5 |
| core | `test_a_negated_wish_never_raises_a_weight` | 8.2, on the sentences the reviewers found |
| core | `test_a_sentence_that_was_read_backwards_raises_nothing`, `test_a_sentence_that_made_an_edit_nobody_asked_for_makes_none` | 8.2, on the 100 sentences an adversary found reversed after the second round of fixes and the 24 that made an edit nobody asked for, for a renter and a buyer |
| core | `test_a_word_that_is_not_known_beside_any_thing_or_name_makes_the_sentence_unread` | 8.2 rule 1, on a fixed sample of more than 3,500 sentences: every phrase of the lexicon and every name of the committed release beside a word the reader does not know, drawn from more than 600, in 40 places and with every mark. `test_every_word_that_is_not_known_in_every_place_makes_the_sentence_unread` is the whole of it, more than 40,000 sentences, and runs with `-m full` |
| core | `test_known_words_that_no_rule_accounts_for_leave_the_sentence_unread`, `test_a_word_that_turns_governs_the_thing_after_it_and_what_is_joined_to_that_by_or`, `test_a_turn_that_may_reach_further_makes_the_whole_prompt_not_plain` | 8.2: the words that turn, and one turn, one thing |
| core | `test_how_a_wish_is_led_in_to_is_not_said_to_be_unread`, `test_a_word_that_is_on_no_list_is_still_said_to_be_unread_with_the_stretch_it_stands_in`, `test_a_wish_asks_for_nothing_only_where_it_stands_straight_after_the_speaker`, `test_no_word_that_turns_weakens_compares_or_says_how_much_asks_for_nothing`, `test_what_core_does_not_place_asks_for_something_as_far_as_anyone_can_say`, `test_that_nothing_was_made_of_a_word_is_said_as_it_was`, `test_what_is_left_out_is_where_the_words_stand_and_never_the_words` | 8.1: words that ask for nothing are not said to be unread, a stretch is left out whole or not at all, and `other` is said as it was |
| api | `test_a_model_is_asked_as_it_was_where_the_rules_left_only_words_that_ask_for_nothing`, `test_what_a_model_leaves_of_a_stretch_is_not_said_to_be_unread_where_it_asks_for_nothing` | 8.1 and 8.2: a model is asked exactly where it was, and what it leaves of a stretch is judged by the same lists |
| core | `test_what_is_said_after_the_last_thing_of_a_turned_list_never_begins_a_new_wish`, `test_a_turn_carries_over_or_to_a_thing_with_words_after_it`, `test_a_turned_list_that_may_be_read_two_ways_is_not_plain` | 8.2, on the sentences two reviewers found read backwards: a turned list with a word after its last thing |
| core | `test_a_choice_holds_nothing_that_its_label_does_not_say`, `test_a_budget_is_offered_as_its_amount_and_the_size_of_home_as_a_choice_of_its_own`, `test_what_stands_straight_after_a_word_that_turns_it_away_is_not_offered_to_be_set` | 8.2: what is offered |
| core | `test_nothing_of_a_request_is_applied_when_one_sentence_of_it_is_in_doubt`, `test_no_suggestion_would_raise_a_weight_by_a_direction_the_reader_chose`, `test_an_end_of_a_scale_that_is_turned_away_is_a_wish_for_the_other_end`, `test_the_name_of_a_scale_names_no_end_so_it_is_offered_and_never_applied` | 8.1 and 8.2: all or nothing, what is offered, and the ends of a scale |
| core | `test_every_recipe_sums_to_a_hundred_with_two_parts_or_more_and_none_of_sixty`, `test_a_recipe_that_breaks_a_rule_is_refused_when_the_catalogue_is_made`, `test_one_vibe_alone_holds_recorded_crime_and_it_is_one_a_real_release_may_not_carry` | 3.2 |
| core | `test_a_band_is_one_of_five_counted_from_the_areas_strictly_below`, `test_areas_that_are_level_share_a_band_and_none_counts_as_below_another`, `test_a_band_in_a_release_is_the_one_core_works_out_from_the_raw_values` | 2.4 and 2.8, `bands_match_raw` |
| core | `test_what_a_release_ranks_on_is_what_it_shows_and_what_its_figures_make` | 2.8: `percentiles_match_values`, `raw_matches_recipe`, `scores_match_raw` |
| core | `test_gritty_as_a_scale_is_carried_by_a_release_that_is_not_made_up`, `test_gritty_is_one_vibe_on_a_scale_that_counts_recorded_crime`, `test_works_and_warehouses_stays_a_vibe_of_its_own_beside_gritty` | 3.2: Gritty is one vibe, with the recipe that was decided, and a release of London carries it |
| core | `test_a_journey_with_no_time_does_not_lift_an_area_that_is_known_to_be_far`, `test_the_journeys_are_missing_only_when_no_leg_has_a_time` | 6.4 |
| core | `test_a_vibe_towards_its_low_end_is_worth_one_less_its_score`, `test_the_strip_is_shown_and_never_scored` | 6.2 and 6.7 |
| core | `test_likeness_is_never_counted_on_a_nuisance_crime_or_what_is_weighed_on_request`, `test_a_flag_on_a_feature_cannot_bring_a_nuisance_into_likeness`, `test_likeness_is_a_function_of_the_release_alone`, `test_the_areas_most_like_an_area_are_in_the_order_of_the_count_each_sentence_gives` | 6.9 |
| core | `test_a_vibe_is_said_as_a_band_among_the_areas_compared_and_never_as_a_percentage`, `test_no_sentence_about_a_vibe_prints_a_score_a_share_or_a_rank` | 7.3, in a release built by hand and in the committed one |
| core | `test_a_band_that_rests_on_part_of_a_recipe_says_how_much_of_it`, `test_a_range_that_rests_on_part_of_a_recipe_says_so_too` | 7.3: `{partly}` and `share`. `test_every_comparison_said_of_the_release_is_literally_true` holds the clause to the rows of the committed release |
| core | `test_a_reason_is_said_from_the_better_side_and_a_trade_off_from_the_worse`, `test_what_lies_between_the_two_thresholds_is_neither_a_reason_nor_a_trade_off` | 7.3 and 7.5 |
| core | `test_no_sentence_may_praise_or_blame_with_nothing_behind_it`, `test_the_name_of_an_end_of_a_scale_passes_only_from_the_fact_it_is_an_end_of` | 7.4 step 6 |
| core | `test_a_portrait_holds_ids_and_no_sentence_and_is_the_same_for_everyone`, `test_a_vibe_the_area_cannot_be_placed_on_is_listed_as_that_and_never_in_the_middle`, `test_the_way_gritty_was_built_is_never_the_first_thing_said_of_an_area` | 7.6 |
| core | `test_a_tenure_that_is_said_is_the_persons_whether_or_not_it_moves`, `test_a_step_towards_the_other_end_starts_from_nothing` | 5.3 rules 13 and 14 |
| core | `test_a_hedge_that_cannot_turn_a_wish_round_leaves_the_prompt_plain`, `test_a_hedge_that_may_say_whether_a_thing_is_wanted_is_still_not_plain`, `test_a_wish_that_is_hedged_is_worth_what_a_mention_is` | 8.2: an everyday hedge |
| core | `test_a_token_is_never_split_at_a_mark_inside_it`, `test_a_name_is_never_put_together_across_a_mark_or_a_line_break`, `test_a_question_makes_no_edit`, `test_a_sentence_whose_subject_is_not_the_speaker_makes_no_edit`, `test_a_sentence_that_holds_doubt_and_names_nothing_takes_back_what_was_raised`, `test_a_number_that_is_a_minimum_is_never_a_cap`, `test_a_nuisance_that_is_liked_or_only_named_makes_no_edit` | 8.2 rules 3, 4, 7, 8 and 10 |
| core | `test_no_plain_word_can_turn_weaken_compare_question_or_reassign_a_wish`, `test_the_list_of_plain_words_is_short_and_is_reviewed_as_a_whole` | 8.2 rule 2: the vocabulary itself |
| core | `test_every_edit_says_which_words_of_the_text_it_rests_on`, `test_what_an_edit_rests_on_is_offsets_and_holds_no_word_of_the_text` | 8.1, `rests_on` |
| core | `test_a_generic_word_after_a_cue_for_a_place_names_no_place` | 8.2 |
| core | `test_minutes_said_apart_from_a_place_keep_their_way_of_travelling_and_their_limit`, `test_minutes_said_of_no_journey_or_against_one_are_not_said_to_have_been_read` | 8.2: a journey whose minutes stand apart from its place |
| core | `test_a_plain_wish_for_each_thing_is_still_read`, `test_a_plain_journey_to_each_place_is_still_read`, `test_a_plain_area_rule_for_each_area_is_still_read` | That the closed vocabulary has not switched the reader off |
| core | `test_the_share_of_plain_wishes_that_is_read_does_not_fall_without_being_noticed`, `test_the_share_of_sentences_the_vocabulary_was_not_settled_on_is_held_too` | The price of 8.2, with a floor: 170 plain sentences and 60 held out (section 13) |
| core | `test_one_stated_wish_outweighs_everything_that_was_left_unsaid` | 4.1, for a renter and a buyer and every feature and tag |
| core | `test_a_default_the_person_took_off_stays_off_when_the_tenure_changes` | 5.1 and 5.3 rule 5 |
| core | `test_being_over_budget_is_never_given_as_a_reason`, `test_a_journey_over_its_cap_is_never_given_as_a_reason` | 7.5 |
| core | `test_a_cost_that_is_the_budget_to_the_pound_is_said_to_be_at_it`, `test_every_way_a_budget_is_held_has_a_sentence_for_a_difference_of_nothing`, `test_a_journey_that_takes_the_minutes_of_its_limit_is_at_it_and_under_it_by_nothing`, `test_no_fact_of_any_budget_or_limit_gives_a_difference_of_nothing` | 7.2 and 7.3: every sentence that gives a difference is held where the difference is nothing, and a pound or a minute either side of it |
| core | `test_a_trade_off_is_something_the_area_does_badly`, `test_there_is_no_trade_off_when_nothing_is_done_badly` | 7.5, on a fixed sample of 15 searches of the committed release. `test_every_trade_off_of_many_searches_is_something_the_area_does_badly` is 200, and runs with `-m full` |
| core | `test_a_short_walk_is_never_a_trade_off_however_many_areas_are_closer`, `test_a_station_560_metres_off_is_not_what_an_area_gives_up`, `test_every_walk_time_and_distance_has_a_figure_at_which_it_is_never_a_trade_off` | 7.5, `NEVER_A_TRADE_OFF` |
| core | `test_explain_takes_the_template_explainer_and_no_other` | 7.5 and 11 |
| core | `test_an_ordinary_word_that_begins_a_name_is_never_read_as_the_name` | 8.3 |
| core | `test_a_reason_is_something_the_area_does_well` | 7.5 |
| core | `test_exactly_half_the_weight_present_is_ranked_however_the_weight_is_split` | 6.6 |
| core | `test_an_area_with_no_figure_for_what_was_asked_stands_below_every_area_that_has_one`, `test_a_usual_setting_with_no_figure_moves_no_area`, `test_a_journey_and_a_budget_never_stand_in_for_the_character_that_was_asked_for`, `test_the_character_asked_for_is_covered_in_whole_steps_apart_from_journeys_and_money`, `test_which_areas_are_ranked_does_not_depend_on_who_chose_a_weight`, `test_an_area_that_is_not_ranked_says_every_thing_it_has_no_figure_for` | 6.6 and 6.7: the character that counts is covered on its own |
| core | `test_an_area_with_no_figure_for_what_was_asked_of_a_place_is_listed_apart_and_never_first` | 6.6, on the committed release: the new town, for the newcomer's search |
| core | One test for each rule in 2.8 | `parse_release` |
| pipeline | `test_synthetic_release_rebuilds_byte_for_byte` | 2.9 |
| pipeline | `test_synthetic_names_are_not_real_places` | 2.9, against London's names and every name that was replaced |
| pipeline | `test_a_name_that_was_replaced_is_in_no_file_of_code_or_of_tests` | 2.9, in every file of `packages`, `services` and `tools`, the name of a constant included |
| pipeline | `test_a_place_that_was_given_a_new_name_kept_its_id` | 0 and 2.9: a new name moves no id |
| pipeline | `test_no_journey_is_shorter_than_two_minutes` | 2.9, on the committed release and on three other seeds |
| pipeline | `test_no_figure_of_an_older_feature_moved_when_the_newer_parts_were_added`, `test_a_release_is_built_with_gritty_and_without_and_which_moves_no_figure` | 2.9 |
| pipeline | `test_the_new_town_can_be_placed_on_homes_and_on_nothing_else`, `test_an_area_far_from_one_workplace_is_not_first_because_another_has_no_time`, `test_the_village_swallowed_by_the_city_is_most_like_the_other_old_village` | 2.9, 6.4 and 6.9, on the committed seed and on three others |
| pipeline | `test_a_file_the_finder_leaves_behind_is_ignored` | 2.8 |
| pipeline | `test_every_other_stray_file_is_still_refused` | 2.8 |
| pipeline | `test_written_release_reads_back_the_same` | `write_release` and `read_release` agree |
| pipeline | `test_source_must_be_registered_for_the_use_its_file_needs` | 2.1, against the fixture registry: a routing source named in `catalogue.json` is refused |
| pipeline | `test_real_release_is_refused_without_a_registry` | 2.1 |
| api | `test_a_plain_prompt_is_applied_by_the_rules_and_no_call_is_made`, `test_for_any_other_prompt_the_model_is_asked_and_what_it_says_becomes_offers` | 8.2: the order of reading |
| api | `test_no_edit_of_a_models_is_applied_whatever_it_answers`, `test_no_answer_on_disk_is_applied_and_every_edit_that_is_served_is_the_rules_own`, `test_what_is_pressed_is_a_controls_edit_and_never_a_reading` | 8.2: nothing a model reads is applied. A test, and not a rate: every kind of edit at its strongest, whatever provenance the model gives, and every answer on disk |
| api | `test_a_person_never_sees_less_than_the_rules_alone_give`, `test_whatever_a_model_answers_every_way_the_rules_give_is_still_offered` | 8.2: no right reading of the rules is lost because a model is on. The guard that went lost 14 |
| api | `test_the_rules_answer_when_the_model_is_slow_capped_or_broken`, `test_the_rules_offers_are_served_at_once_and_never_wait_on_the_model` | 9.4 and 8.2: never a 5xx for a model, and `ask_model: false` |
| api | `test_what_was_offered_is_not_said_to_have_been_left_out`, `test_what_a_model_could_not_place_is_kept_where_its_words_say_more_than_an_offer` | 9.2: what a model files of words that an offer rests on is not said to have been left out |
| api | `tests/test_guard.py`, a group of tests for each of the thirteen checks, in their order | 8.2: each check, on the answers a model gave that it stops, which are on disk, and on answers written to go wrong in one way. What each costs is held beside it |
| api | `test_never_a_vibe_that_counts_recorded_crime`, `test_never_a_weight_on_recorded_crime_that_the_words_do_not_name`, `test_never_a_reading_of_a_word_the_rules_offer_what_is_nearest_for`, `test_never_anything_about_who_lives_somewhere`, `test_never_a_firm_limit_nobody_gave`, `test_never_a_least_distance_as_a_journey`, `test_never_a_number_for_a_weight`, `test_never_a_place_an_area_or_an_amount_the_person_did_not_type`, `test_never_a_rule_for_an_area_as_a_guess` | 8.2: what is never offered from a model, a test for each row. The third is tried on every phrase of core's lexicon that carries a note, so a word core adds is held to it the day it is added |
| api | `test_no_word_that_turns_lets_a_raise_be_marked_as_the_guess`, `test_every_word_that_turns_beside_every_thing_takes_the_guess_away`, `test_every_sign_of_doubt_keeps_a_thing_out_of_add_all` | 8.2 check 4: every word core lists as turning a wish away, beside every thing of the lexicon. A fixed sample in `make ci`, and all of them with `-m full` |
| api | `test_someone_elses_wish_is_not_marked_as_the_guess`, `test_a_wish_turned_round_in_words_core_does_not_list_is_not_the_guess` | 8.2, "What this cannot do". Expected to fail, and strict |
| api | `tests/test_merge.py` | 8.2: one offer for each thing, two things for the same words, where the rules read the words the other way, and a budget |
| api | `tests/test_offers.py` | 8.2: what "add all" may add at one press, on every answer on disk, and what is plainly said of a home and of a journey. `test_to_press_every_guess_of_the_rules_does_the_opposite_of_no_case_that_is_held` holds what the rules mark to every case of the evaluation set. `test_by_the_rules_alone_one_press_takes_a_journey_that_was_plainly_said_as_a_guide` holds the founder's sentence |
| api | `tests/test_wording.py` | 8.2: the four parts of an offer, that doing nothing is "Skip", that what nobody said is said, that an offer says all that each of its ways holds, and that no word of the person's is in any part of it |
| evals | `evals/reader/test_replay.py` | 8.2: the floor, on the first look of every sentence whose answer is on disk |
| api | `test_every_route_works_with_no_key_configured` | Form mode |
| api | `test_api_loads_the_committed_synthetic_release` | The two halves fit |
| api | `test_a_number_in_a_models_answer_must_be_a_number` | 8.2 and 9.1: a number in a model's answer must be a number, for every number of every edit. An answer that holds `true` for one is no answer, and the rules answer in its place |
| api | `test_where_the_words_stand_is_counted_in_the_text_as_it_was_sent`, `test_each_edit_says_which_words_of_the_text_it_rests_on` | 9.2: `rests_on` on route 1, with space before the text and characters two units long in it |
| api | `test_a_spec_that_has_gone_stale_can_be_put_right_by_an_edit` | 9.4 and 5.3 rule 6, over HTTP |
| api | `test_a_path_with_a_slash_too_many_is_no_route_and_is_never_redirected` | 9.2 |
| api | `test_a_number_must_be_sent_as_a_number` | 9.1, for every number in every body |
| api | `test_an_origin_on_the_list_is_allowed`, `test_an_origin_off_the_list_is_not` | 9.1, on every route and every kind of refusal |
| api | `test_a_call_record_older_than_thirty_days_is_gone_after_the_next_add`, `test_a_record_out_of_the_order_of_time_is_gone_when_it_is_too_old` | 10.2 |
| api | `test_an_origin_that_no_browser_would_send_is_refused_when_the_service_starts` | 9.1 |
| api | `test_an_operation_is_named_for_its_route` | 9.4 |
| api | `test_a_file_the_finder_leaves_behind_does_not_stop_the_service` | 2.8 |
| core | `test_a_real_release_with_nothing_beside_it_is_not_served`, `test_a_release_changed_after_it_was_built_is_not_served`, `test_evidence_or_a_lock_changed_after_the_build_is_not_served` | 2.8, `open_served` |
| core | `test_a_release_with_no_journey_may_not_say_it_is_finished` | 2, what a finished release holds |
| core | `test_an_outline_drawn_far_from_the_point_inside_its_area_is_refused` | 2.8, `values_are_in_range` |
| api | `test_a_release_that_is_not_made_up_is_not_served_with_nothing_beside_it` | 2.8, over `load_release` and the command line |
| pipeline | `test_a_figure_raised_after_the_build_is_found_though_every_hash_agrees` | 2.8, `burro-release check` holds a figure to its row of evidence |
| api | `test_a_plain_prompt_about_money_and_work_is_read_in_full`, `test_a_prompt_that_is_not_plain_applies_nothing_and_offers_what_was_noticed`, `test_a_choice_that_is_pressed_is_an_edit_that_route_2_takes_as_it_is` | 8.1 and 9.2, over the wire |
| api | `test_where_what_was_noticed_stands_is_counted_in_the_text_as_it_was_sent`, `test_an_interpreter_cannot_offer_or_leave_unread_what_is_outside_the_text` | 9.2: `suggestions` and `unread`, with space before the text and characters two units long in it |
| api | `test_every_place_of_a_spec_that_is_returned_is_given_by_name`, `test_a_place_is_named_as_the_release_names_it_and_never_as_it_was_typed` | 9.2, `places` |
| api | `test_the_notice_says_the_rest_was_applied_only_where_something_was`, `test_a_tenure_that_is_said_is_the_persons_own_whether_or_not_it_moves` | 8.4 and 5.3 rule 13, over the wire |
| api | `test_a_scale_is_ranked_towards_the_end_that_is_asked_for_and_can_be_turned`, `test_an_edit_to_a_vibe_must_say_which_end_and_a_one_way_vibe_has_one`, `test_a_vibe_that_was_retired_is_no_longer_a_vibe`, `test_a_vibe_the_release_does_not_carry_cannot_be_ranked_on` | 5.1, 6.2 and 9.2 |
| api | `test_every_result_shows_where_it_sits_on_the_vibes_that_were_asked_for`, `test_how_much_of_what_counts_an_area_has_a_figure_for_is_said_of_every_area`, `test_an_area_far_from_one_workplace_is_not_first_because_another_has_no_time` | 6.4 and 6.7, over the wire |
| api | `test_an_explanation_says_which_spec_it_is_for`, `test_every_mark_on_a_result_that_is_explained_has_its_fact_served`, `test_a_reason_is_said_from_its_better_side_and_a_trade_off_from_its_worse` | 7.3, 7.5 and 9.2 |
| api | `test_the_map_can_be_coloured_by_any_vibe_from_one_answer`, `test_the_portrait_of_an_area_is_the_same_for_everyone_and_holds_no_sentence`, `test_an_area_that_cannot_be_placed_is_said_to_be_that_and_is_like_nothing`, `test_the_areas_most_like_an_area_are_named_with_a_sentence_each` | 6.9, 7.6 and 9.2 |
| api | `test_every_choice_that_is_offered_is_an_edit_that_route_2_applies`, `test_what_burro_cannot_do_is_said_beside_what_it_offers_in_its_place`, `test_a_verdict_burro_does_not_give_is_heard_and_nothing_is_offered_for_it`, `test_an_everyday_hedge_is_read_as_a_word_of_degree`, `test_minutes_said_apart_from_a_place_keep_how_they_are_travelled_and_their_limit`, `test_the_last_thing_of_a_turned_list_is_never_raised` | 8.2, over the wire, on the prompts that a walk in a browser and two reviews found read wrongly |
| api | `test_a_band_that_rests_on_part_of_its_recipe_says_how_much_wherever_it_is_said`, `test_a_station_560_metres_off_is_not_what_an_area_gives_up`, `test_a_distance_of_a_thousand_metres_is_written_as_people_write_it` | 7.2, 7.3 and 7.5, over the wire |
| api | `test_the_service_does_not_start_on_a_release_that_ranks_on_what_it_does_not_show` | 2.8: the three rules that hold what is ranked on to what is shown, from the command line |
| api | `test_a_ranking_says_how_many_areas_are_ranked_and_how_many_of_them_are_listed` | 9.2: `areas_ranked` and `areas_listed`, on routes 2 and 10 |
| api | `test_an_area_with_no_figure_for_what_was_asked_is_listed_apart_with_what_it_lacks`, `test_an_area_that_is_listed_apart_is_compared_with_what_it_lacks` | 6.6 and 9.2, over the wire: the newcomer's search, with every choice pressed |
| api | `test_a_comparison_begins_with_where_each_area_sits_on_every_vibe`, `test_a_comparison_says_how_much_each_fit_is_based_on`, `test_every_cell_of_a_row_is_said_from_one_side` | 9.2, route 7 |
| api | `test_a_comparison_has_one_row_for_each_journey_with_the_same_destination_across_it`, `test_a_journey_with_no_time_is_shown_as_having_none`, `test_what_the_journeys_add_stands_once_beside_the_journey_that_counts`, `test_where_every_journey_counts_no_one_journey_is_said_to_add_the_whole`, `test_an_area_that_is_not_ranked_still_shows_each_of_its_journeys` | 9.2, route 7: the journeys |
| api | `test_meta_gives_the_vibes_the_release_carries_with_all_a_shelf_needs`, `test_every_thing_a_form_shows_has_a_plain_name_of_a_few_words`, `test_which_way_gritty_is_built_is_the_releases_to_say` | 3 and 9.2, route 11 |
| api | `test_a_browser_that_holds_the_loaded_release_is_told_that_it_still_stands`, `test_a_browser_that_holds_anything_else_is_answered_in_full`, `test_only_an_answer_that_would_be_given_is_said_to_stand` | 9.3 |
| api | `test_a_record_has_one_name_and_one_shape_in_the_document`, `test_the_document_is_of_the_second_version_of_the_contract` | 9.2 and 9.4, `contracts/openapi.json` |

**The census.** Every test below plants a canary where it can: the made-up count names groups that are in no release, no catalogue and no sentence, so a heading or a code of it that is seen outside route 13 is the census leaking.

| Part | Test | Proves no figure of the census can reach |
|---|---|---|
| core | `test_nothing_in_core_imports_the_census`, `test_the_census_imports_nothing_of_core_that_ranks_or_says`, `test_a_census_is_never_handed_a_release` | A score, a vibe, a likeness, a fact, a sentence |
| core | `test_a_release_cannot_return_a_census_figure`, `test_a_release_folder_that_holds_a_census_file_is_refused` | The release |
| core | `test_no_word_of_the_vocabulary_names_what_is_never_ranked_on`, `test_no_spec_and_no_edit_has_a_field_for_what_is_never_ranked_on`, `test_a_census_kind_is_no_feature_and_no_vibe` | A spec, an edit, a filter, a share |
| core | `test_nothing_else_stands_beside_a_figure`, `test_rows_are_in_the_order_the_census_holds_them_and_never_by_size`, `test_no_word_is_one_burro_would_be_choosing`, `test_what_is_served_holds_no_word_burro_would_be_choosing` | A comparison, an order, a verdict |
| core | `test_a_share_under_one_in_a_hundred_is_said_in_words_with_no_count`, `test_no_count_under_ten_can_be_held`, `test_a_table_is_left_out_where_too_few_were_counted_and_says_so` | A small count in print |
| pipeline | `test_nothing_that_builds_the_product_imports_the_census_and_it_imports_none_of_them`, `test_a_census_is_no_file_of_a_release` | A score, a vibe, a map layer |
| pipeline | `test_the_made_up_count_holds_no_heading_of_a_real_census_table`, `test_the_made_up_groups_follow_no_trait_of_an_area` | A made-up share of real people |
| pipeline | `test_a_real_census_is_refused_without_a_registry`, `test_a_source_that_is_not_approved_or_not_registered_never_reaches_a_census`, `test_a_table_its_source_does_not_name_never_reaches_a_census` | A page, without the licence gate |
| api | `test_no_search_can_ask_for_a_census_figure`, `test_no_comparison_can_ask_for_a_census_figure`, `test_no_share_and_no_explanation_can_ask_for_a_census_figure`, `test_no_sentence_makes_an_edit_from_a_census_figure` | A search, a comparison's rows, a share, an explanation, the reader |
| api | `test_moving_the_census_between_areas_changes_no_other_answer`, sampled, and in full under `full`. `test_taking_the_census_away_changes_no_answer_but_the_offer_of_it` | Every other answer |
| api | `test_only_the_census_route_serves_a_census_figure`, `test_the_line_for_a_census_names_the_route_and_never_the_area` | Every other route, a header, a log line, a call record |
| api | `test_the_census_route_takes_nothing`, `test_no_route_serves_the_census_of_more_than_one_area`, `test_the_census_route_may_not_be_kept_or_indexed`, `test_the_census_route_can_be_switched_off` | A filter, an order of areas, a cache, a search engine |
| api | `test_nothing_sent_to_a_model_holds_a_census_figure`, `test_a_stored_share_holds_nothing_of_the_census`, `test_no_schema_but_the_census_routes_names_a_census_record` | A model, a share, a generated client |

## 13. Open points

These are first guesses. Each is a constant or a table row, so changing one is a small diff and an engine or catalogue version bump.

| Point | Status |
|---|---|
| What stands beside a census figure | **The founder's decision**, open, 2026-09-24. ADR 0014 as first written said a share and nothing beside it: no count, and no comparison with any average. Route 13 serves the count of each row and the share of the whole city beside it, and a client may draw the two shares. Each is one field of `CensusPanelRow`, and taking one out is taking out a field (section 2.10). The registry's entry for the census tables still holds the conditions as first written, and a real census cannot be written until the two agree |
| `FLOOR` and the share under which a count is withheld | 1,000 counted and 1 in 100, chosen by judgement (section 2.10). The publisher's guidance names no figure for either. Together they mean no count under 10 is printed. To be looked at again on the first real build, against the publisher's own figures for a borough |
| What is said of the lockdown | "The census was taken during a lockdown." Whether the lockdown of 21 March 2021 was the same across London was not read. The sentence under the tables of age and of households is the publisher's own, and is held to its page when a real census is built |
| The cutoff of a release that routed no journey | Open, 2026-09-23. A preview holds no journey, and `travel.json` must still give `cutoff_minutes`, each at least 10: the reducer, `check_spec` and the limits of route 11 read it as a number. The first real build writes the contract's own 90, 60 and 60. They limit nothing, because the preview has no place a journey could end at. But route 11 serves them, and a methods page that prints "the longest journey in this release" prints a journey that was never routed. To make it something a release can leave out, `Cutoffs` becomes optional in `TravelTable` and in `ServedLimits`, and the form takes its limit from `LIMITS` alone. That changes the wire, so it was not done with the flag |
| Where the hashes of an approved release are kept | Decided, 2026-09-25, in [ADR 0030](../adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md). `hashes.json` stands beside the release, in the folder the build wrote, so a person who changes a release can change its hashes with it, and `open_served` cannot tell. To approve a release is to commit its lock under `data/approved/`: the hash and the size of every file of the release and of what stands beside it, `hashes.json` among them. The service is not told which hashes were approved. The image is: the step `take` and the build of the image each hold every file to the committed lock, and an image carries nothing else. A release that is read from a folder on a person's own machine is held as before, by `burro-release check` and by whoever builds it |
| Where a vibe of a release that is not made up may be shown | Open, 2026-09-24. The design of the vibes says that on a real release every flag of a vibe starts off, and is turned on by the outcome of an audit ([vibes.md](vibes.md), section 5.2). Core holds one catalogue, in which every vibe holds `lens`, `strip` and `table`, and `vibes_match_core` refuses a release whose vibes differ from it. So a preview that places its areas on a vibe serves its bands to the map, the strip and the comparison, as the made-up release does. No audit has been run, and nothing in core can turn a flag off for one release. It is the founder's to say before a release is shown to anyone: a flag that a release may turn off and never on, or a preview that is kept to the people who build it. **Since 2026-09-25** no audit is to run (ADR 0006, as amended), so no outcome of one turns a flag on or off. The question stands, and no longer waits on an audit |
| Likeness on few measures | Open, 2026-09-24. Likeness is counted on the measures of a release that it may use, and is unknown for an area with a figure for under 60 in 100 of them (section 6.9). A first build carries one such measure, homes built before 1919. So every area with that figure has five areas said to be like it, on 1 of 1 measures or on none of 1. The sentence says the count, and what it says is little. A least number of measures would close it, and is the founder's to set |
| What is held of a label, an outline, a cost, a journey and a station | Open, 2026-09-24. The row of evidence of a measure holds its figure, and of a tag its score. The row of a cost holds it where the cost is one number: a publisher's median, with no range (ADR 0021). No other row holds a value, because none is one number. The hashes of the build hold them, and nothing else does |
| What `schema_version` a preview is written at | Decided, 2026-09-24, when the vibes were joined with the first real builds: 2. The schema of the vibes holds `preview` beside `gritty_variant`, and `source_ids` and `as_of` of two files may be empty as section 2 says. The made-up release was built again in the same change. A release written before the two were joined lacks `gritty_variant` or `preview` in its manifest, and is refused as `shape_is_valid` before its version is read: none was ever served |
| The decay constants of 6.3 and `BUDGET_OVER_SHARE` | Chosen by judgement. To be tuned on real travel times and with testers |
| A firm budget held against a median | Decided, 2026-09-24 (ADR 0021, as amended): an area is left out only where its median is more than a quarter over the budget, and an area the margin keeps says that about half of the homes sold for less (section 6.5). The quarter is a first figure, written once as `FIRM_BUDGET_MARGIN_PERCENT`, and is the founder's to change |
| What a median rests on | Settled for a build that reads the sales, 2026-09-24: the median is worked out from the sales of three years, says how many it rests on, and is given from 10 sales up (section 2.5). A publisher's own median is still `unstated`: the count the publisher gives as a dataset of its own is registered and not read. Whether 10 sales over three years are enough is a first figure |
| A price for a home of any kind | Open, 2026-09-24. The publisher gives one, and a budget names a kind of home, so no row holds it. It has a place only if `Segment` gains one for it. So does a price for a house of any kind, which no release holds: a build of London holds what flats sold for in 984 of its 1,002 areas, terraced houses in 940, semi-detached houses in 653 and detached houses in 282. Until `Segment` gains one, a budget to buy "a house" is held against what terraced houses sold for, and the kind is said to be assumed (section 8.2, decided on 2026-09-25) |
| The recipes in 3.2 and default weights in 4.1 | Chosen by judgement. A vibe is unvalidated until the 40-neighbourhood sanity set exists; one that fails it is dropped. Every sentence about a vibe says so: "The recipe is Burro's own. The weights are a judgement." |
| Which way gritty is built for London | **Decided on 2026-09-24** (ADR 0013, as amended). Gritty is one vibe, the scale that counts recorded crime, with the recipe of section 3.2, and a release of London carries it. Works and warehouses is a part of it, and is not served beside it. What is still the founder's: the weights, which are a first judgement |
| Anti-social behaviour as a part of a vibe | `incident_antisocial` is 15 hundredths of Gritty. Decided on 2026-09-24 with the recipe: it is a part |
| The names of the ends | "Polished" and "Gritty", "Calm" and "Buzzy", "Newer" and "Historic", "Houses" and "Flats" are first names. "Gritty" and "polished" are words the verifier refuses anywhere but as the name of an end |
| `MIN_CHARACTER_COVERAGE` | 0.5, chosen by judgement (section 6.6). It is the same share as the floor for the whole. At a half, an area that lacks one of two things a person asked for is still ranked, and says what it lacks. A default counts as character, so an area is listed apart where it has a figure for under half of the usual settings and nothing was said of the place: the new town of the made-up city is, for a search by rent and workplace alone. Whether that is wanted is for the founder to judge on screen |
| `NEVER_A_TRADE_OFF` | 800 m and 1,600 m, chosen by judgement (section 7.5). The nearest place of a tier or of a chain is held to 800 m, the reach its count is made within. Every distance is a straight line since catalogue version 13, so the walk is longer than the figure, and each floor is to be looked at again. **Settled for a station, 2026-09-25:** the founder decided that near a station is about a 10 to 15 minute walk, which a straight line of 800 m is, so the floor of `station_walk` stands and its offer says so. The other floors are still to be looked at. No published standard was read for them. With them a result shows a trade-off less often: a short walk that most areas better is in the working and in no sentence |
| How a vibe is said in short | The start of its full statement, word for word (section 7.3), so that a result says nothing new and is shorter. It gives no figure a person can picture. To say the band in words and the figure of a part, a sentence must cite two facts, which section 7.5 does not allow, and must never cite a figure of recorded crime. Whether that is wanted is for the founder (slice-1.md, section 10) |
| `TRADE_OFF_MAX_UTILITY` | 0.35, chosen by judgement (section 7.5). What is worth 0.35 to 0.50 is in no sentence. To be held against recorded searches |
| The sources of the 21 new features | Section 3.1 names the source of each that a build works out. One is in no build: `cuisine_variety` has no source that is cleared. `private_outdoor_space` has a source that is cleared, and a build that names its files carries it since 2026-09-25: it was held back for want of a row of the proxy audit, which is dropped (ADR 0006). The made-up release does not carry it, or `gp_walk` or `pharmacy_walk`, which a build of London does |
| What a model may apply in a prompt that is not plain | **Settled, 2026-09-24: nothing.** The model proposes, the person confirms, code checks (section 8.2, ADR 0012). Nothing a model reads is applied, in a plain prompt or any other. What it reads is offered, and `unread` no longer marks words an offer rests on. `unmet` holds `other` exactly when `unread` is not empty, whoever read |
| What a model may no longer read, since the reader was held to a grammar | Overtaken, 2026-09-24. A model's reading of such a sentence is offered, and never applied (section 8.2). |
| `make api GRITTY=a` | slice-1.md names it. It is not built: the Makefile was not in the change that built the API to version 2. The two commands of section 9.4 do the same |
| `university_proximity` from `dfe-gias` | Assumes that register lists university sites. If not, the feature needs its own registered source |
| `university_proximity` has one direction | Settled, 2026-09-23: it keeps one direction. A person may ask to be near a campus and not to be far from one, because the second is a way to ask for fewer students. The rules now refuse it in words (section 8.4), where before they read "far" as a word of degree and turned the tag up |
| The attainment features | They describe a school's results, which the plan allows, and not residents. They are also the features most likely to stand in for who lives nearby, so the proxy audit should take them first. **Since 2026-09-25** no audit is run (ADR 0006), so nothing looks for it |
| Nurseries in `family_amenities` | ADR 0006 names them. No registered source provides them, so the formula leaves them out |
| Places of worship and specialist shops | ADR 0006 meets community requests through these. No v1 feature covers them, so such requests are reported as unmet |
| What is nearest to a gym, to a sense of community and to a garden | First guesses (section 8.2). A gym is offered what there is to do in parks, community is offered Village feel, and a garden is offered the garden land of an area. Each says in its note that it is the nearest Burro can count and not what was asked for. Places to train and Places to meet are not built (vibes.md). Whether each offer helps or misleads is for the founder to judge on screen |
| Whether a pressed offer of recorded crime is asking by name | Built as yes (section 8.2): the choice reads "Less recorded violence and robbery", and the edit is `ui_edit`. It is what a control on the settings page already does. It is the founder's to confirm |
| Anti-social behaviour and listed-building density | Left out to keep the catalogue near 20. Both have approved sources and can be added. The registry asks that conservation areas be combined with listed-building density and pre-1919 homes. This contract combines them with pre-1919 homes only, and relies on the coverage rule to stop them deciding a tag alone. Whether that meets the condition is the founder's call |
| Gated sources in 3.1 | `dfe-school-performance-tables` is gated today, so the gate will not let it be read for scoring. Its two features are left out of a real release until it is approved (section 2.3), and `family_amenities` is worked out from the other three quarters of its formula |
| Figures from sources registered for scoring only | The food, venue, culture and conservation features come from sources registered for `scoring` and not for `display`, yet their values are printed in sentences. This contract asks for `scoring`. If printing a derived figure counts as display, the registry entries need that use added, with evidence, before a real release |
| A `place_id` in a stored share | No search is stored (section 9.4). A share is, as ADR 0005 provides, and it holds exact places only when the sender asks. ADR 0005 speaks of destination strings; an id is not a string, but it is as revealing. Whether an exact share may reach a database is to be settled before the database arrives |
| The spec hash in logs | Settled twice on 2026-09-23. First the plain hash gave way to the hash under a key made at start-up. Then a checker showed that the keyed hash confirms a guess for whoever reads the log and can call the service, and nothing was found that needs to know two calls were about one search. So nothing worked out from a spec is logged, or kept about a call, at all (section 10.1, ADR 0005 and 0011). **Still open:** the plan names the spec hash among the columns of `llm_calls`; there is no such column. And what route 1's line still says of a reading, the counts of edits and of rejections by reason and the codes of what was assumed and of what could not be met, depends on the spec as well as on the words: an adversary showed that the same words leave a different line when only the spec differs. None names a place, none holds a number of the spec, and none can be matched to a spec without the words, which are in no line (section 10.1, and a test holds the line to it). It is not the letter of "nothing worked out from a spec". To meet the letter, take `edits`, `rejections`, `unmet` and `assumptions` out of `LOGGABLE`, and lose what they tell of how well the readers read; or say in AGENTS.md rule 9 and ADR 0011 that a count which depends on the words and the spec together may be logged. **It is the founder's call, and neither was done** |
| Long caps and the cutoff | A cap may not exceed the release's cutoff (section 6.1), and a journey beyond the cutoff scores 0 although the curve runs on to one and a half times the cap (6.3). Both go away if a real release routes to a cutoff of one and a half times the longest cap, which is a cost to weigh when routing is built |
| Logging the edits a prompt produced | ADR 0005 allows it. This contract logs only their counts, which is stricter, because a commute edit names a place |
| What a plain mention is worth | Settled, 2026-09-23: a mention is worth 0.50 and the defaults give way to a quarter, rounded down to a step, once a wish is applied (sections 4.1, 5.2 and 5.3). One thing said is 0.50 against 0.35 left unsaid for a renter and 0.45 for a buyer. Measured on the committed synthetic release with a renter's first prompt: "leafy and quiet" puts Alderwick first, the leafiest and the quietest area; "somewhere buzzy with bars and restaurants" Pellam Cross, the centre; "good schools and a park for the kids" Dulcimer Green, whose schools have the best results; "by the river" Sable Reach, which has more of its land by the water than any other, where a third left Brackenhythe first. **Still open:** to outweigh in weight is not always to come first. For a buyer "by the river" still puts Brackenhythe first and Sable Reach second, and "leafy" alone puts Brackenhythe first for both, with Alderwick, the leafiest, second or third: Brackenhythe is third of the 21 placed for leafiness, since the city was redrawn on 2026-09-24, and does best on what was left unsaid. If a single wish should always put the best area for it first, the defaults must give way to nothing, which is a different product. **Also open:** the quarter is rounded down, which the decision did not say. To the nearest step it would leave 0.55 and 0.60 unsaid and defeat its purpose |
| A default that was removed comes back | Settled, 2026-09-23: what a person takes off leaves an entry of 0 behind, in their name, where a tenure has a default for the feature, and a change of tenure leaves it off (sections 5.1 and 5.3 rule 5). `canonical()` goes on dropping it. **Still open:** a client sees the entry on the wire, a weight of 0 with a provenance, and must show it as off and not as a wish. And what was never in the spec was never taken off: a renter who says "I don't care about green space" and then switches to buying gets the buyer's default for green cover |
| A first prompt that says "buy" | Settled, 2026-09-23: changing tenure resets what nobody chose to the new tenure's default and keeps what the person set (section 5.3 rule 5). Route 1 still edits the renter's default when no spec is sent, and "buying a flat near a park" now ends with the buyer's defaults |
| Finding a place from part of a word | Settled for resolving, 2026-09-23: `search_places` and `resolve_place` have parted ways (section 8.3). Part of a word is offered by a search and asked about by a resolver, and never taken. Still open for searching: a place matches from the start of its name, or on whole words, so "univ" alone finds nothing. A weaker score for words that begin a word of the name would help a search box |
| A name after "near" | After "near", "not", "avoid" and "only" only the whole of a name or an alias is taken (section 8.2). "Near Pellam" adds no journey and asks nothing, where "work at Pellam" asks which. "Near Alderwick" adds none either if no place has that name, though an area does: a journey ends at a place, and an area's centre is not one |
| Names in lower case, and what a sentence asserts | The verifier finds a name by its capital and a verdict by a list of words (section 7.4). Enough for the templates, and not for a model: section 11 says what must be added first, and `explain()` refuses a second explainer until it is. Closed on 2026-09-23: a number word that is misspelt or run together, a word for nothing, a unit said with an article, a length of time, a Roman numeral in lower case, a banned word in any form it takes, and one written with a letter of another alphabet, an accent or a zero-width character. **Still open:** a name in lower case, a claim about residents, a number said of the wrong thing, a comparison run the wrong way, and a banned word spelt with spaces between its letters |
| Counting the areas compared | `facts_for` counts the areas strictly beyond one, for each feature and vibe, each time it is called: 51 passes over the areas of the release, and likeness bands every part again. It is nothing for 24 areas. For a real release the counts belong in the release, worked out once by the pipeline beside the percentile |
| The plan says the percentile is the explanation | PLAN section 8 says "quieter than 80% of London" is both the score and the explanation. Since 2026-09-23 it is the score only. The sentence states the share strictly beyond, which is lower wherever areas tie |
| A journey in a comparison for an area that was filtered | Settled, 2026-09-24: each journey has a row of its own, and its cell cites the `travel` or the `missing` fact of that journey, which `facts_for` makes for every area (section 9.2). So the journey that broke the cap is shown, with the limit it is over. Nothing needs to know which journey drove a score that was never worked out |
| What one journey adds where every journey counts | Open. With `commute_combine` `mean` and two journeys or more, no cell of a comparison says what the journeys add to the fit (section 9.2). `rank()` reports one contribution for the journeys together, and a route works out no share of it. To show it, core would report what each leg adds, which is a change to `CommuteLeg` and to section 6.7 |
| Names are normalised on every request | Each interpreter builds `Names` from the release it is handed: 0.2 ms for 44 places, and it grows with the place index. A real index of tens of thousands needs it built once |
| A journey of 0 minutes | Settled for the synthetic release, 2026-09-23: no time in it is under 2 minutes (section 2.9). It held one of 0, from Cindermoor to Cindermoor Works, and two walks of 1. It is still a valid time to core (section 2.6). **Still open:** a real roll-up needs the same floor in its own pipeline step, and whether 2 is right for it is to be settled on real journeys |
| Whether every made-up name is made up | Not known. Eight names of the city and nine of the tests' own releases were real and have been replaced (section 2.9). On 2026-09-23 all 102 names were looked up in one encyclopaedia, by title and by phrase. **No gazetteer was consulted**, so a small street, a farm or a hamlet that the encyclopaedia does not cover would not have been found, and the replacements were checked the same way and no better. Two of the five replacements in the city rest on partial evidence (Kilnside, Withyford). Three names could not be settled and are the ones to check first: Alderwick, which may be a street in Hounslow, Foxholt, which may be a street in north-west London or a hamlet in Kent, and the test name "A Hundred Acres", which may be a hamlet in Hampshire and has been replaced to be safe. To settle it, someone with a gazetteer of Britain checks every name in `names.py` once, replaces any that is real with a name that sorts where it did, and adds the old one to the test's list. A canary in the pipeline's tests, which reaches no release, still begins with the name of a real place in California |
| What the rule-based reader no longer reads | Decided, 2026-09-23, third round: it reads a sentence only when it knows every token in it (section 8.2). **The price, measured.** Of 170 plain positive sentences, 90 of them an adversary's own, the reader read 145 in full before, 85.3%, and reads 142, 83.5%; of the adversary's 90 it read 70 and reads 69. Those were used to settle the vocabulary, so the fairer measure is 60 sentences that were written afterwards and never used to widen it: 55 read before, 91.7%, and 46 now, 76.7%. Both have a floor in `tests/test_vocabulary.py`. What is declined now that was read before: a wish beside a word the reader does not know, anywhere between two full stops ("a lively high street with plenty going on", "nice cafes and a decent bakery", "I work from home so I want somewhere quiet"); another person's wish or workplace ("my partner works at Pellam Infirmary", "the kids need a playground"); a question ("could you find me somewhere with good pubs?"); a wish after a sentence that holds doubt and names nothing, where it is only named ("Moving next month. Somewhere leafy."); a wish listed after a turned one ("leafy, no pubs, quiet" reads no "quiet"); "far more", "a few" and "walking distance of" where a word beside them is not known; a nuisance that is only named ("noise"); and part of a name after "work at", which is asked about and no longer taken. What is still declined as before: a double negative, a comparison ("quieter than where I live now") and a condition ("happy anywhere as long as"). A word that is missing costs one wish and never reverses one, and `vocabulary.PLAIN` is where to add it **Decided again, 2026-09-23, fourth round (ADR 0012, slice 1):** it applies a prompt only when the whole of it is plain, and offers what it noticed in any other. Of the 170 plain sentences it now applies 137 in full, 80.6%, and of the adversary's 90, 67. Of the 60 that were held out, 45, 75.0%. On the evaluation set of 738 cases it reads 375 correctly, 50.8%, offers 221 as suggestions, declines 137, reads 5 in part, and reverses and invents none. Every one of the 42 cases that are marked plain is read correctly, and the floor holds that at 1. What it no longer applies it offers, with the direction left to the person **Measured again, 2026-09-23, after the first slice was mended (engine 1.5.0):** of the 170 plain sentences it applies 138, and of the adversary's 90, 68, since a word of degree is read. Of the 60 held out, 45. The evaluation set has 781 cases, 43 of them written from what two reviews and a walk in a browser found. On those 781 the reader as it was reversed 10, made an edit nobody asked for in 11 and left 10 plain prompts unapplied. It now reads 408 correctly, 52.2%, offers 232, declines 136, reads 5 in part, and reverses and invents none, and every one of the 53 plain cases is read correctly **Measured again, 2026-09-25, when an amount to buy a house of no kind came to be held against a terraced house:** of the 170 plain sentences it applies 136, as it has since "family friendly" came to be offered, and of the adversary's 90, 67. For some hours of that day a house of no kind was asked about, and it applied 135 |
| The signs of doubt are a list | Settled, 2026-09-23: the reader no longer reads by one. It reads by the list of what it knows, which is short and can be whole, and a word that is missing from it costs a wish that is not read. `WORDS_OF_DOUBT` is kept for two callers that do not read by it: the test that no plain word is one, and the model-backed reader. What is known to get through the closed vocabulary: a statement of where the person lives now, read as a wish ("I live near a station"); a word with two meanings of which the reader knows one ("flat" as level ground, "rent" as what is paid today); irony with no mark on it ("I just love pubs" is unread for "just", "I love pubs" said in scorn is read); and a sentence that holds doubt, names nothing and stands two sentences away from a wish in which the speaker says what they want |
| The API and a `.DS_Store` | Settled, 2026-09-23: `load_release` leaves it out as `read_release` does (section 2.8), so the service starts on any folder that `burro-release check` passes |
| `HEAD` and `If-None-Match` | Settled for `If-None-Match`, 2026-09-23: a conditional `GET` of routes 4, 5, 6 and 11 is answered 304 while the release stands (section 9.3). A `HEAD` is still answered 405 |
| A release whose content changes under its id | The `ETag` is the release id. The synthetic release was rebuilt under `syn-2026-09-23-01` while version 2 was built, and again on 2026-09-24 when the plan of the city was redrawn (section 2.9), so a browser that held the older answer would be told it still stands. Nothing was deployed then, so nothing was affected. Burro has been deployed with the made-up release since 2026-09-25, so a fixture that is rebuilt and deployed under the same id now reaches a browser that held the older answer there. A release never changes once it is published (section 2), and a rebuilt fixture is the one case where it does: a browser used for development must be reloaded with its cache off after `make fixture` |
| The origins a browser may call from | Settled, 2026-09-23: a list in a setting, `http://localhost:3000` by default, and nowhere else, each entry held to what a browser sends (section 9.1). **Still open:** the web app's real address, which goes in `BURRO_ALLOWED_ORIGINS` where the service is deployed. A deployment that sets nothing allows only a page on the visitor's own machine, which is safe and is not useful |
| A request about people that nobody notices | As it was: one that both the lexicon and the model miss can still be offered as a vibe, and is applied only if the person presses it (section 8.2). |
| What a model's reading loses when part of a request is about people | Narrowed, 2026-09-24. Where the rules heard the request, what a model read of the rest is offered, and only what rests on the words about people is dropped. Where only the model says so, nothing of its answer is offered, because code cannot say which words it means (section 8.2, check 13). |
| Where the words stand, in code points | `rests_on` counts code points, as core counts them, and the API serves core's record as it is (section 9.2). A client in JavaScript counts UTF-16 units, and the two differ after any character that is two units long. It is said in the contract and in the OpenAPI description of `RestsOn`, and nothing enforces it: a client that slices the string directly marks the wrong words after an emoji. If that proves a trap, the API can serve UTF-16 units instead, which is a change to one function in `routes/interpret.py` and to this contract |
| What the model-backed reader no longer reads | Overtaken, 2026-09-24. The guard that kept a model's edit only where the rules made the same one is gone: it read fewer sentences than the rules alone (ADR 0012). What a model reads is offered, under the checks of section 8.2. |
| A doubt that stands after a list | Closed in core, 2026-09-23 (section 8.2 rule 7): a sentence that holds doubt and names nothing takes back what the sentence before it raised, and what is listed beside it. "A park or a playground? No thanks", "leafy, quiet. Not really", "near Pellam Infirmary or Foxholt Market is not for me" and "I work at Pellam Cross or Wexmoor University? No" make no edit |
| A turned wish with no sign of doubt in it | As it was, and now an offer: a model that raises the thing there has its reading marked as the guess, and nothing is applied until it is pressed (section 8.2). |
| A name the model corrected | A name the person did not type makes no journey, corrected or not. A name they typed that the release does not hold is asked about (section 8.2, check 2). |
