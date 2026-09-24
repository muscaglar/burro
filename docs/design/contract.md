# Burro v1 backend contract

Status: built, 2026-09-23. Contract version 1. The three parts exist and `make ci` holds them to this document. What was settled while building is written in where it applies, and [ADR 0010](../adr/0010-one-contract-one-synthetic-release.md) and [ADR 0011](../adr/0011-nothing-is-kept-for-a-search.md) say why.

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
| Engine | `ENGINE_VERSION = "1.3.0"` in `burro_core`. Any change to the arithmetic in section 6, to a rule of the reducer in section 5.3 or to a rule of what an explanation says in section 7.5 bumps it. 1.1.0 compares coverage in whole steps (section 6.6). 1.2.0 lets the defaults give way to a quarter, and keeps off what a person took off (sections 4.1 and 5.3). 1.3.0 gives as a trade-off only what an area does badly (section 7.5) |
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
| `catalogue.py` | `FEATURES`, `TAGS`, `CATALOGUE_VERSION`, `percentile_of()`, `tag_raw()` |
| `release.py` | The `Release` protocol, its records, `InMemoryRelease`, `parse_release()`, `open_release()` |
| `spec.py` | `PreferenceSpec`, `LIMITS`, `default_spec()`, `check_spec()`, `canonical()`, `spec_hash()` |
| `ops.py` | `Operations` and its six edit types |
| `reducer.py` | `apply()` |
| `rank.py` | `rank()`, `RankResult`, the decay and budget functions and their constants |
| `places.py` | `normalise()`, `search_places()`, `resolve_place()`, `resolve_area()`, and `Names`, which holds a release's names normalised once and adds `exact_place()` and `exact_area()` |
| `facts.py` | `Fact`, `facts_for()` |
| `explain.py` | The templates, the `Explainer` protocol, `TemplateExplainer`, `explain()` |
| `verify.py` | `verify()`, `ORDINARY_WORDS`, `BANNED_WORDS` |
| `interpret.py` | The `Interpreter` protocol, `RuleInterpreter`, `assumptions_for()`, `LEXICON`, `POLICY_LEXICON`, the fixed notices, and `sentences_of()`, which says of each sentence whether the reader read it |
| `vocabulary.py` | The closed vocabulary of the rule-based reader: `PLAIN`, the words it reads through, each group with why it is safe; the words it has a rule for; and `WORDS_OF_DOUBT`, which it does not read (section 8.2) |

**`packages/pipeline`**: adds one subpackage beside `registry/`, `release/`, with the synthetic generator inside it. Depends on `burro-core`. No new third-party dependency.

| Module | Holds |
|---|---|
| `release/write.py` | `write_release(release, folder, registry=None)`: the source check of 2.1, canonical JSON, checksums, manifest written last |
| `release/read.py` | `read_release(folder)`: reads the bytes, leaving out a `.DS_Store`, and calls `open_release` (section 2.8) |
| `release/synthetic/build.py` | `build_synthetic(seed, release_id, built_at) -> InMemoryRelease` |
| `release/synthetic/names.py` | The fixed lists of made-up names, and the plan of the made-up city |
| `release/synthetic/journeys.py` | How long a journey takes, and `whole_minutes()`, which holds the shortest at 2 minutes (section 2.9) |
| `release/synthetic/chart.py` | The map the areas are drawn on |
| `release/cli.py` | `burro-release build-synthetic --out FOLDER` and `burro-release check FOLDER` |

**`services/api`**: distribution `burro-api`, import `burro_api`. Depends on `burro-core`, `fastapi` (the web framework named in the plan), `uvicorn` (runs it; the plain package, without the `standard` extra) and `anthropic` (the provider's SDK, imported by `claude_sdk.py` alone and only when a key is present). Tests add `httpx2`, which FastAPI's test client needs.

| Module | Holds |
|---|---|
| `app.py` | `create_app(deps: Deps) -> FastAPI`. `Deps` holds the release, interpreter, explainer, share store, call log, clock, id source and allowed origins, so tests pass fakes |
| `settings.py` | `Settings.from_env()`: release folder, model id, timeouts, and the origins a browser may call from, each held to what a browser sends (section 9.1) |
| `loading.py` | `load_release(folder)`: reads the bytes, leaving out a `.DS_Store`, and calls `open_release` (section 2.8) |
| `routes/` | One module per group of routes in section 9 |
| `wire.py`, `errors.py` | Request bodies, the response envelope, the error envelope, and handlers that never echo input |
| `stores.py` | The `ShareStore` protocol with an in-memory implementation |
| `calls.py`, `logs.py` | `CallRecord`, the `CallLog` protocol, logging setup, the request log line, `log_failure()` |
| `claude.py` | `ClaudeInterpreter`, the `ModelClient` protocol, the `ModelOutput` schema, and what is kept from a model's answer (section 8.2). Tested against a fake `ModelClient` that answers wrongly |
| `claude_sdk.py` | `AnthropicModelClient`, the one `ModelClient` that imports the provider's SDK. Tested against the SDK with a transport that answers in the provider's place. It has not been run against the provider: there is no key to run it with |
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
| `catalogue.json` | `{"catalogue_version": 1, "metrics": [...]}` | a feature this release carries | 2.3 |
| `features.json` | `{"rows": [...]}` | one feature in one area | `area_id`, `feature_id`, `value` (float or null, in the catalogue's unit), `percentile` (float or null), `coverage` (0 to 1) |
| `tags.json` | `{"rows": [...]}` | one tag in one area | `area_id`, `tag_id`, `raw` (float or null, 0 to 1), `score` (float or null: the percentile of `raw`), `coverage` (0 to 1) |
| `cost.json` | `{"rows": [...]}` | one tenure and segment in one area | 2.5 |
| `destinations.json` | `{"destinations": [...]}` | a point journeys end at | `destination_id`, `centroid`. In a real release it is a hexagon (ADR 0003) |
| `travel.json` | object of matrices | | 2.6 |
| `stations.json` | `{"source_ids": [...], "as_of": ..., "rows": [...]}` | one station near one area | `area_id`, `station_id`, `name`, `walk_minutes`, `lines` (line names, sorted), `step_free`, `nearest` |
| `places.json` | `{"places": [...]}` | something a person can name as a destination | 2.7 |

Every file that holds something the product may show names where it came from and when. `neighbourhoods.json`, `stations.json` and `travel.json` do it once for the file, with `source_ids` (a sorted list, at least one) and `as_of` (a date or a month), because each is built in one step from several sources. `catalogue.json` and `cost.json` do it on each row, and so does `places.json`, where a row is one record from one source. Without these a fact about a name, a station or a journey would have no source to cite (section 7.1).

Missing data has one spelling per file, and nothing is ever filled in.

- `features.json` holds a row for every area and every feature in `catalogue.json`, and `tags.json` a row for every area and every `TagId`. A missing value is `null`, because coverage is still reported.
- In `features.json`, `coverage` is the share of the area, by population or by land as the definition says, that the source covered. The pipeline sets `value` to null below 0.5. In `tags.json`, `coverage` is the share of the formula's weight that was present (section 3.2).
- `cost.json` and `stations.json` hold no row where there is no estimate. An area has at most one station row with `nearest` true; its other rows are stations within a 10-minute walk.

### 2.1 `manifest.json`

| Field | Type | Notes |
|---|---|---|
| `release_id` | str | Equals the folder name |
| `schema_version` | int | `1` |
| `built_at` | timestamp | An input to the builder, never read from the clock, so a rebuild is byte-identical |
| `catalogue_version` | int | Must equal `CATALOGUE_VERSION` |
| `synthetic` | bool | True for every `syn-` release and for no other |
| `city`, `seed` | str, int or null | `syn` or `lon`. The seed is set for synthetic releases |
| `sources` | list | `source_id`, `name`, `publisher`, `licence`, `attribution`, `url`, `retrieved_on`. Every `source_id` used anywhere in the release appears here once |
| `files` | list | `name`, `sha256`, `bytes` for every other file in the folder |
| `counts` | object | `neighbourhoods`, `rankable`, `destinations`, `places`, `stations` |

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
| `aliases` | list of str | Other names that resolve to this area. May be empty |
| `centroid` | `[lon, lat]` | WGS84, 6 decimals |
| `rankable` | bool | The pipeline decides; core only reads. A real release sets it false for an area too small for its rates to be steady, below 3,000 residents |
| `neighbours` | list of `area_id` | Areas sharing a boundary, sorted. Symmetric |

The release holds no population figure. The pipeline needs one for rates and for `rankable`, and nothing after the pipeline does, so it stays there: a count of residents that is not in the release cannot be ranked on or shown.

### 2.3 `catalogue.json`

| Field | Type | Notes |
|---|---|---|
| `feature_id` | `FeatureId` | Must be in the allowlist |
| `label`, `dimension`, `unit`, `polarity` | | Must equal `FEATURES` in core. Core decides these; the release repeats them so it can be read alone |
| `native_resolution` | enum | `oa`, `lsoa`, `grid_1km`, `point`, `polygon`, `network` |
| `source_ids` | list of str | Every source the figure was worked out from, sorted, at least one, each in `manifest.sources`. A crime rate names the crime data and the population estimate it was divided by |
| `vintage` | str | The period the data describes, for example `2025` or `2024-10 to 2026-09` |
| `rankable` | bool | False switches the feature off for ranking in this release. Its values are still shown |
| `definition` | str | One sentence with the method and its parameters, shown on the methods page |

A release carries the features it has a cleared source for, which may be fewer than `FeatureId` holds. A feature with no row here is not in the release: it has no rows in `features.json`, it counts as missing in every tag, and an edit or a spec that weights it meets `not_in_release`, as one that weights a feature with `rankable` false does. Every feature in core can be ranked; only a release switches one off. The synthetic release carries all 23, all rankable.

### 2.4 How a percentile is computed

For one feature, the population is the rankable areas with a value, `N` of them. For an area with value `v`, `L` is how many of the population are strictly below `v` and `E` how many equal it, the area itself included if it is rankable.

`percentile = round(100 * (L + 0.5 * E) / N, 1)`

It is a percentile of the raw value. Polarity is applied at ranking time, never baked in. `percentile` is null exactly when `value` is null. If no rankable area has a value, the pipeline leaves the feature out of the release. Example: values 310, 120, 640, 310, 900 give 40.0, 10.0, 70.0, 40.0, 90.0.

`percentile_of(values, rankable) -> tuple[float | None, ...]` in core is the only implementation, for features and for tags alike. It takes one value and one rankable flag for each area, in the same order. The pipeline calls it, as it calls `tag_raw()`.

### 2.5 `cost.json`

| Field | Type | Notes |
|---|---|---|
| `area_id`, `tenure` | str, `rent` or `buy` | |
| `segment` | enum | Rent: `room`, `studio`, `bed_1`, `bed_2`, `bed_3`, `bed_4plus`. Buy: `flat`, `terraced`, `semi_detached`, `detached` |
| `lower_quartile`, `median`, `upper_quartile` | int | Pounds. Rent rounded to 25, price to 5,000. `lower <= median <= upper` |
| `confidence` | `high`, `medium`, `low` | High: at least 50 observations. Medium: 10 to 49, blended. Low: modelled |
| `as_of`, `source_ids` | month, list of str | As in 2.3 |

### 2.6 `travel.json`

It holds `source_ids`, `as_of`, `area_ids`, `destination_ids`, `cutoff_minutes` (`{"pt": 90, "cycle": 60, "walk": 60}`) and four matrices: `pt_typical`, `pt_just_missed`, `cycle` and `walk`. `area_ids` holds every area and `destination_ids` every destination, each once and sorted. Each matrix is a list of rows in `area_ids` order, each row a list in `destination_ids` order. Times are door to door, on a weekday morning peak. A journey has several sources because a real one is built from timetables and a street network, and each must be credited beside the time (ADR 0004).

| Cell | Meaning | `Travel.status` | `Travel.minutes` |
|---|---|---|---|
| int, 0 up to the cutoff | Minutes | `ok` | The int |
| `-1` | No journey within the cutoff. This is data | `beyond_cutoff` | `None` |
| `null` | Not computed. This is missing data | `missing` | `None` |

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

The three tuples are ordered by id, and `stations` nearest first. `metrics` holds the features this release carries. `None` means the id is unknown to this release, or for `cost` that there is no estimate. `travel` never returns `None`; for a time that is not in the release, and for an id it does not know, it returns `Travel(status=missing, minutes=None)`. `basis` is ignored for `cycle` and `walk`. `Geometry` is a GeoJSON geometry object. `origin` returns the `source_ids` and `as_of` of one of the three files that state them once: `Part` is `neighbourhoods`, `stations` or `travel`. Every record is a frozen model with the fields of the matching file. `cutoff` returns the longest journey the release routed for a mode, which the reducer, `check_spec` and the travel fact all need. `InMemoryRelease` is the one implementation in this build. Its `documents()` is the inverse of `parse_release`, so the shape of every file is stated in one module, and `write_release` serialises what it returns. A release in another format is a second implementation; nothing else changes.

Two pure functions in core do all the checking, so the pipeline and the API cannot come to disagree about what a valid release is:

- `parse_release(documents: Mapping[str, object]) -> InMemoryRelease` takes the parsed content of each file, keyed by file name, and applies the rules in the table below. It is the only parser.
- `open_release(folder_name: str, files: Mapping[str, bytes]) -> InMemoryRelease` takes the bytes of each file in the folder, keyed by file name, and runs the four steps below. It reads no file itself.

1. Parse `manifest.json`. Refuse if `release_id` is not `folder_name`.
2. For each entry in `files`, compare `sha256` and `bytes`, then parse the JSON. Refuse an extra or a missing file.
3. Call `parse_release`.
4. Refuse on any `ReleaseError`. The message names the file, the row and the rule, and never a value.

`read_release(folder)` in the pipeline and `load_release(folder)` in the API do one thing each: read every file in the folder into bytes and call `open_release`.

`read_release` and `load_release` each leave one file out: a file named exactly `.DS_Store`, which a Mac leaves in any folder that has been opened in a window. It is never opened, it is not handed to `open_release`, and it is left where it is. Nothing else is left out: a folder of that name, the same name in another case, `._manifest.json`, `Thumbs.db` and `.gitkeep` are all handed over and refused as before. `write_release` leaves the same file alone when it rebuilds the synthetic release, so a folder that reads as a release can be rebuilt. Core is unchanged: `open_release` still refuses any file the manifest does not list, this one included, if it is handed one. The name is spelt out once in each reader, because the pipeline and the API never import each other, and a test in each holds it to `.DS_Store`.

| Rule in `parse_release` | Refused when |
|---|---|
| `versions_match` | `schema_version` is not 1, or `catalogue_version` is not `CATALOGUE_VERSION` |
| `synthetic_is_consistent` | `synthetic` is true and any id lacks the `syn-` prefix, or false and any id has it, or the reserved source of 2.1 is misused |
| `ids_are_unique` | An id or a slug repeats within its file |
| `references_resolve` | A row names an area, destination, place, station or source that does not exist |
| `catalogue_matches_core` | A feature is outside the allowlist, or disagrees with `FEATURES` |
| `rows_are_complete` | `features.json` lacks a row for an area and a carried feature, `tags.json` for an area and a tag, `geometry.json` lacks an area, or `travel.json` lacks an area or a destination |
| `values_are_in_range` | A percentile, coverage, quartile order, cutoff or minute value breaks its range |
| `null_means_null` | `value` and `percentile`, or `raw` and `score`, disagree about being null |
| `sources_are_stated` | A `source_ids` list is empty, or an `as_of` or a `vintage` is empty |
| `neighbours_are_symmetric` | A lists B and B does not list A |

A few checks the table does not spell out are filed under the nearest rule: a list the contract calls sorted must be strictly increasing, and one station id has one name and one set of lines (`ids_are_unique`); a value may not be present below the coverage threshold (`null_means_null`); a tag with a score needs at least one formula feature with a value, or its fact would have no source (`sources_are_stated`). `counts` in the manifest is written from the rows and is not checked against them on reading.

A refusal that is not one of the ten rules has a name of its own, raised as the same `ReleaseError`:

| Name | Raised by | Refused when |
|---|---|---|
| `json_is_valid`, `shape_is_valid` | core | A file is not JSON, or a field is missing, unknown or of the wrong type |
| `files_match_manifest`, `files_are_expected` | core | A file is missing, extra or changed, a hidden file included, or is not a file a release has. `read_release` and `load_release` never hand core a `.DS_Store` |
| `release_id_matches_folder` | core | The manifest names a release other than its folder |
| `folder_is_readable`, `file_is_readable` | `read_release`, `load_release` | The folder or a file in it cannot be read |
| `real_release_needs_a_registry`, `release_is_never_overwritten`, `folder_holds_something_else` | `write_release` | A real release is written with no registry or over itself, or the folder holds something that is not a release file |

`burro-release check FOLDER` says a refusal in plain words. The API says the folder, the file and the rule, because it never imports the pipeline.

### 2.9 The synthetic release

| Rule | Detail |
|---|---|
| Size | 1 borough, 24 areas of which 2 are not rankable, 40 destinations, 16 stations, 4 lines, 44 places. Small enough that each area's character is set by hand, so a test can say which areas a spec should find |
| Names | Every area, borough, station, line and place name comes from a fixed list of made-up names. A test holds the names of the 32 London boroughs, the City, London's tube and rail lines, and 60 well-known London places, and fails if any made-up name contains one. That list guards against London's well-known names and against nothing else. It also holds the real names that the city once used and the list did not catch. Three a reviewer knew from memory: Dunmere, a hamlet in Cornwall; Copper Row, a small street by a bridge in London; and Skerrow, a loch in Galloway. They were replaced by Dulcimer Green, Coracle Row and Scrimshaw Airfield. Then all 102 names of the generator and of the releases the tests build by hand were looked up in one encyclopaedia, by title and by phrase. Two more of the city's names were found: Kilnside, a locality in Renfrewshire, and Withyford, an old spelling of a hamlet in Shropshire. They were replaced by Kindlewharf and Wickerford. Three aliases were what real buildings are called, The Exchange, The Playhouse and Moot Hall, and each has the borough before it now: Quillhaven Exchange, Quillhaven Playhouse, Quillhaven Moot Hall. Every new name sorts where the old one did, so no id moved, and a test holds each id to what it named before. The old names are held in the test's list, with the nine that the tests' own releases held, and a second test looks for each in every file of code and of tests, a constant's name included. **No gazetteer was consulted.** The encyclopaedia does not cover a small street, a farm or a hamlet, which is what three of the five were. A check of every name against a gazetteer of Britain is still to be made (section 13) |
| Location | Every coordinate lies in the box longitude -0.20 to 0.20, latitude -0.15 to 0.15, which is open sea. No synthetic polygon can be laid over a real street |
| Shortest journey | No time in the release is under 2 minutes: not a cell of `travel.json`, not a `walk_minutes` in `stations.json`, and not the `station_walk` feature, which repeats the walk to the nearest station. A time is rounded to whole minutes and then held at 2, by `whole_minutes()` in `journeys.py` and nowhere else. The map can put a place at the middle of its area, and no distance at all is still down the stairs and across the road. Every sentence says "minutes", which 0 and 1 do not read well in |
| Gaps on purpose | About 5% of feature values are null. One rankable area has no cost rows. One has a `null` travel cell and one a `-1`. One tag is null in at least one area. These keep the missing-data paths tested |
| Determinism | `build_synthetic(seed, release_id, built_at)` draws only from `random.Random(seed).random()`, whose sequence is stable across Python versions. The committed fixture is `syn-2026-09-23-01`, seed `20260923`, built at `2026-09-23T00:00:00Z`. A test rebuilds it and compares bytes |
| Plausibility | Values are drawn so that features correlate the way a city's would (nearer the centre: denser, noisier, shorter journeys, dearer). This is for demos only and is a claim about nothing |
| The flag | `manifest.synthetic` reaches every API response (section 9.1) |

## 3. The v1 feature catalogue

### 3.1 Features

23 features. Each describes a place or its buildings. None describes who lives there. An id names the idea, not the method: distances and thresholds live in `definition` and may change with `CATALOGUE_VERSION`. An id is never renamed, reused or given a new meaning.

Polarity is `less` (lower is better), `more` (higher is better) or `either` (the user chooses). The comparatives fill the sentence "*X* than 80% of areas". The last column is the main registry id a real release is expected to use, beside any it needs for a denominator or a network; the synthetic release uses `synthetic` for all.

| `feature_id` | Dimension | Label | Unit | Polarity | Native | Higher / lower | Real source |
|---|---|---|---|---|---|---|---|
| `crime_violence_robbery` | crime | Recorded violence and robbery | per 1,000 residents a year | less | lsoa | more / less | `police-uk-street-level-crime` |
| `crime_burglary_theft` | crime | Recorded burglary and theft | per 1,000 residents a year | less | lsoa | more / less | `police-uk-street-level-crime` |
| `school_primary_nearby` | schools | State primary schools within a short walk | count | more | network | more / fewer | `dfe-gias` |
| `school_primary_attainment` | schools | Pupils meeting the expected standard at nearby primaries | % | more | point | higher / lower | `dfe-school-performance-tables` |
| `school_secondary_attainment` | schools | Attainment 8 at nearby secondaries | points | more | point | higher / lower | `dfe-school-performance-tables` |
| `university_proximity` | schools | Distance to the nearest university site | m | less | point | further / closer | `dfe-gias` |
| `green_cover` | green_water | Public green space as a share of the area | % | more | polygon | greener / less green | `os-open-greenspace` |
| `park_proximity` | green_water | Walk to the nearest park of 2 ha or more | m | less | network | further / closer | `os-open-greenspace` |
| `play_space_proximity` | green_water | Walk to the nearest play space | m | less | network | further / closer | `os-open-greenspace` |
| `water_access` | green_water | Share of the area within 300 m of a river or canal | % | more | polygon | more / less | `os-open-rivers` |
| `air_no2` | air_noise | Modelled annual mean nitrogen dioxide | µg/m³ | less | grid_1km | higher / lower | `defra-pcm-background-air` |
| `noise_exposure` | air_noise | Share of homes at 55 dB or more of transport noise | % | less | lsoa | noisier / quieter | `mhclg-iod-2025-underlying-indicators` |
| `venue_food_drink` | venues_culture | Places to eat and drink | per km² | either | point | more / fewer | `fsa-food-hygiene-ratings` |
| `venue_evening` | venues_culture | Pubs, bars and evening venues | per km² | either | point | more / fewer | `fsa-food-hygiene-ratings` |
| `venue_independent` | venues_culture | Places to eat and drink that are not part of a chain | % | more | point | more / fewer | `fsa-food-hygiene-ratings` |
| `culture_venues` | venues_culture | Theatres, cinemas, galleries, museums, libraries and music venues | per km² | more | point | more / fewer | `overture-places` |
| `highstreet_access` | venues_culture | Share of homes within a 10-minute walk of a high street or town centre | % | more | network | more / less | `gla-town-centre-boundaries` |
| `homes_flats` | homes | Flats as a share of homes | % | either | lsoa | more / fewer | `voa-council-tax-stock-of-properties` |
| `homes_pre1919` | homes | Homes built before 1919 | % | either | lsoa | more / fewer | `voa-council-tax-stock-of-properties` |
| `homes_density` | homes | Homes per hectare | per ha | either | lsoa | denser / less dense | `voa-council-tax-stock-of-properties` |
| `conservation_cover` | homes | Share of the area in a conservation area | % | more | polygon | more / less | `mhclg-planning-data-conservation-areas` |
| `station_walk` | station_access | Walk to the nearest station | min | less | network | further / closer | `dft-naptan` |
| `station_lines` | station_access | Lines within a 10-minute walk | count | more | network | more / fewer | `tfl-journey-planner-timetables` |

Rules that come with the list:

- `FeatureId` and `TagId` are the only vocabulary an edit, a spec, a model or a fact may use. Adding a feature means adding an enum member, a `FEATURES` row and a row in the table above, in one change.
- Both crime features have default weight 0, appear in no tag, and may be weighted only on an explicit request (section 5.3). No sentence may call a place safe or unsafe (section 7.4).
- Walk distances are computed on a network that is not OpenStreetMap (ADR 0004).
- Tenure, household type, age, student share and every protected characteristic have no id and cannot be given one without changing ADR 0006.
- `either` is for features of buildings and venues only, where wanting less is a taste in places. `university_proximity` is `less`: a campus is a place to be near, and "far from a university" would be a way to ask for fewer students, which section 8.4 refuses in words and must not be offered as a slider. Decided, 2026-09-23: the feature keeps one direction.
- Four features are nuisances: the two crime features, `air_no2` and `noise_exposure`. Wanting less of one is caring about it, so "less noise" and "no pollution" raise its weight. A nuisance that is only named, or that the person says they like, makes no edit, because its one direction is less: "I like noise" is a wish no edit can express. Wanting less of anything else is a wish turned round, and no weight is ever raised for one (section 8.2). `NUISANCES` in `interpret.py` is the list.
- The registry puts conditions on some sources, and the feature inherits them. The ones that shape this contract: food and drink figures carry their data date wherever they appear, and no establishment is ever named; conservation areas never decide a tag alone (section 3.2) and an area the source does not cover is unknown, not zero.

### 3.2 Tags

A tag is a weighted combination of feature percentiles. Each term reads a feature `high` (`u = percentile / 100`) or `low` (`u = 1 - percentile / 100`).

`raw = sum(w_i * u_i) / sum(w_i)` over the terms whose feature has a value, and `coverage = sum(w_i present)`. If `coverage < 0.6` then `raw` and `score` are null. `score` is the percentile of `raw` by section 2.4. `tag_raw()` in core is the only implementation; the pipeline calls it. It rounds `raw` to six decimals, the precision a release is written with, so the number is the same before writing and after reading.

`TAGS` holds each weight as a whole number of hundredths, so that coverage is compared exactly: a tag is null when the present hundredths sum to less than 60. A float sum of 0.30, 0.15 and 0.15 must not be left to decide which side of the line it falls.

| `tag_id` | Label | Formula |
|---|---|---|
| `village_feel` | Village feel | 0.30 `venue_independent` high + 0.20 `homes_pre1919` high + 0.20 `conservation_cover` high + 0.15 `highstreet_access` high + 0.15 `park_proximity` low |
| `buzzy` | Buzzy | 0.30 `venue_food_drink` high + 0.30 `venue_evening` high + 0.20 `culture_venues` high + 0.20 `highstreet_access` high |
| `leafy` | Leafy | 0.45 `green_cover` high + 0.30 `park_proximity` low + 0.25 `homes_density` low |
| `creative` | Creative | 0.60 `culture_venues` high + 0.40 `venue_independent` high |
| `family_amenities` | Family amenities | 0.30 `school_primary_nearby` high + 0.25 `school_primary_attainment` high + 0.25 `play_space_proximity` low + 0.20 `park_proximity` low |
| `near_universities` | Near universities | 1.00 `university_proximity` low |
| `waterside` | Waterside | 1.00 `water_access` high |
| `strong_high_street` | Strong high street | 0.50 `highstreet_access` high + 0.25 `venue_food_drink` high + 0.25 `venue_independent` high |
| `evening_venues` | Evening venues | 1.00 `venue_evening` high |
| `quiet_residential` | Quiet residential | 0.35 `venue_evening` low + 0.35 `noise_exposure` low + 0.15 `venue_food_drink` low + 0.15 `homes_density` low |
| `foodie` | Foodie | 0.60 `venue_food_drink` high + 0.40 `venue_independent` high |
| `historic_character` | Historic character | 0.50 `conservation_cover` high + 0.50 `homes_pre1919` high |

A test asserts that each formula's weights sum to 100 hundredths, that no term names a crime feature, and that `conservation_cover` carries less than 60 hundredths of any tag. With the coverage rule, that last point means conservation areas can never decide a tag alone, which is a condition of the source.

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
| `tags` | tuple of `TagWeight` | At most one for a tag, kept in `tag_id` order. `tag_id`, `weight`, `provenance` |
| `areas` | tuple of `AreaRule` | At most one for an area, kept in `area_id` order. `area_id`, `rule` (`exclude`, `only`), `provenance` |
| `tenure_from`, `commute_combine_from`, `pt_basis_from`, `commute_weight_from` | `Provenance` | Provenance of the four settings that are not records |

`Provenance` is `stated` (the user said it), `inferred` (the interpreter read it into looser words), `default` (nobody chose it) or `ui_edit` (changed with a control). Every weight is snapped on construction, and the four tuples are sorted on construction, so that nothing downstream depends on the order edits arrived in. A repeated place, feature, tag or area is refused on construction, and so is a weight outside 0 to 1: a weight inside the range is snapped, one outside it is not clamped. The spec holds ids and numbers only: no free text, and no place name.

Construction checks each field alone. What depends on another field, the catalogue or the release is left to `check_spec`, which reports it with a path.

`check_spec(spec, release) -> tuple[SpecProblem, ...]` checks what only a release can decide. A `SpecProblem` is a `path` into the spec, such as `commutes[0].place_id`, and a `problem`, which is one of `unknown_place`, `unknown_area`, `segment_not_for_tenure`, `direction_not_allowed`, `not_in_release` and `out_of_range`. The last is a `max_minutes` above the release's cutoff for the mode (section 6.1), or a `budget.amount` outside the limits of 5.2, which a spec from the wire can hold. `check_spec` ignores what `canonical()` drops, a weight of 0 and a budget with no amount, so that two specs with one canonical form are always treated alike. `rank()` raises `SpecError` if it is not empty.

A position in a `path` is a position in the spec as it is kept, which is in id order, and that is the order every response returns a spec in. It is not the position in the body that was sent: a spec sorts its four tuples on construction and does not keep the order they arrived in. A client that sends `commutes` out of id order and is told of `commutes[2]` finds the element by sorting what it sent by `place_id`, or by looking at position 2 of any spec the service has returned to it. Where a route takes edits with the spec, routes 1 and 2, it is the spec as the edits leave it that is checked, so a position is one in that spec (section 9.4).

`LIMITS` holds the numbers of section 5.2. Route 11 serves them, with the cutoffs of the loaded release, so that a form never offers a value the reducer would refuse.

### 4.1 Defaults

`default_spec(tenure)` returns one of these. Every provenance is `default`. Each weight takes the direction its polarity gives.

| Field | Renter | Buyer |
|---|---|---|
| `tenure` | `rent` | `buy` |
| `budget` | amount `None`, `bed_1`, `soft`, weight 0.80 | amount `None`, `flat`, `soft`, weight 0.80 |
| `commutes`, `tags`, `areas` | none | none |
| `commute_combine`, `pt_basis`, `commute_weight` | `slowest`, `typical`, 1.00 | the same |
| `weights` | `station_walk` 0.50, `station_lines` 0.30, `park_proximity` 0.30, `highstreet_access` 0.30, `noise_exposure` 0.20, `air_no2` 0.20 | `station_walk` 0.40, `park_proximity` 0.40, `green_cover` 0.30, `highstreet_access` 0.30, `noise_exposure` 0.30, `station_lines` 0.20, `air_no2` 0.20 |

A commute added without detail gets mode `pt`, 45 minutes, `soft`.

These are the weights of a search in which nothing has yet been said. Nobody chose them, so they give way the first time a wish is applied (section 5.3, rule 11). Each becomes a quarter of what it was, rounded down to a whole step and never less than one step:

| Given way | Renter | Buyer |
|---|---|---|
| `weights` | `station_walk` 0.10, `station_lines` 0.05, `park_proximity` 0.05, `highstreet_access` 0.05, `noise_exposure` 0.05, `air_no2` 0.05, which is 0.35 in all against 1.80 | `station_walk` 0.10, `park_proximity` 0.10, `green_cover` 0.05, `highstreet_access` 0.05, `noise_exposure` 0.05, `station_lines` 0.05, `air_no2` 0.05, which is 0.45 in all against 2.10 |
| `budget.weight`, `commute_weight` | 0.80 and 1.00, as before. They are not scaled | the same |

One thing said is worth 0.50 (section 5.2), so it outweighs all that was left unsaid, for a renter and for a buyer. That is what the quarter is for, and it is why the quarter is rounded down. To the nearest step a quarter of a renter's defaults comes to 0.55 and of a buyer's to 0.60, as a third does, and one mention would not outweigh either. It is counted in whole steps of 0.05, `steps // 4`, so that no float decides which step 0.075 is nearer to.

`DEFAULT_WEIGHTS`, `given_way()`, `MENTION_WEIGHT` and `GIVE_WAY_TO_ONE_IN` in `spec.py` hold these numbers.

### 4.2 Canonical form and hash

`canonical(spec) -> str` is the form used for hashing, caching and comparing. Two specs with the same canonical form rank the same. The reverse is not promised: the rules below fold together only the differences that plainly cannot matter.

1. Drop every provenance field.
2. Write each weight as its whole number of 0.05 steps, 0 to 20.
3. Drop any feature or tag whose weight is 0 steps.
4. If `budget.amount` is `None`, write `"budget": null`.
5. If there are no commutes, omit `commute_combine`, `pt_basis` and `commute_weight`.
6. Sort `commutes` by `place_id`, `weights` by `feature_id`, `tags` by `tag_id`, `areas` by `area_id`.
7. Serialise with `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.

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
| `tag_ops` | `TagEdit` | `action` (`set`, `nudge`, `remove`); `tag_id`; `value` (float, read by `set`); `step` (read by `nudge`); `provenance` |
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
| `TagEdit` | | | As `WeightEdit`, with no direction |
| `AreaEdit` | `exclude`, `only` | `area_id` | Writes the rule |
| | `clear` | `area_id` | Removes the rule |
| `SettingEdit` | `set` | `setting`, and `choice` for `commute_combine` and `pt_basis`, `value` for the two weights | Writes it. `value` is always read: `0.0` means zero |
| | `nudge` | `setting`, `step` | Moves one of the two weights by the step |

`direction: default` means "as it is": it leaves the direction of a weight already in the spec alone. For a weight that is not yet in the spec it is the direction the polarity gives, and `more` where the polarity is `either`.

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

"More", "a bit", "slightly" and "somewhat" become a small step. "Much", "a lot", "really", "very" and "way more" become a large one. "Less" and "fewer" are words that turn (section 8.2). "Far" is no word of the rule-based reader's, so "far more parks" is left unread by it. "Essential", "most important" and "must have" become `set` to 1.00. "Don't care about", "ignore", "not bothered", "remove" and "get rid of" become `remove`. A weight that is absent counts as 0 when nudged. Nudging a budget with no amount is rejected.

A feature or a tag that is simply named, with no word of degree, is a `nudge` of `up_large`: "leafy" and "near a park" are wishes, and the interpreters never pick a number. Both interpreters follow this rule, the model by its instructions.

**What a mention is worth.** A step up from a weight that nobody has chosen, one that is absent, is still at its default provenance or was taken off, leaves it at `MENTION_WEIGHT`, 0.50, if the step alone would leave it lower. So "leafy" is worth 0.50. So is "more pubs" on a first prompt, where a small step alone would be 0.10: a relative wish for something with no weight yet counts as much as naming it. And so is "near a park", though a park has a default of its own, because a default is nobody's choice. A step up from a weight the person chose is a step and no more: 0.50 and a large step is 0.75. This is the reducer's rule and not the interpreter's, so a chip that sends a `nudge` is worth what a word is.

A budget or a journey time is `soft` unless the words make it a limit. "Max", "under" and "up to" leave it soft. "No more than", "at most", "absolute maximum", "cannot go over" and the like make it `hard`.

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
7. A direction against a fixed polarity is rejected. `default` never is.
8. An `inferred` edit that would leave a crime feature with a weight above 0 is rejected. Crime is weighted only when the user asks for it or moves its control.
9. `exclude` and `only` replace each other for the same area. With any `only` rule present, every area without one is filtered.
10. The setting an edit touches takes the edit's provenance. An edit that is in order but leaves the spec as it was, such as a step at its limit or a `remove` of a weight that is not there, is `applied` with `changed` false and leaves provenance alone. A `set` of a weight or a tag that is still at its default provenance is the one exception: it always takes the edit's provenance, because a slider moved to the very number the default gave has still been moved.
11. **What is said outweighs what is not.** Every edit is applied to the spec with its defaults given way: each feature weight whose provenance is `default` is put at a quarter of the value `default_spec` gives it for the spec's tenure, rounded down to a step (section 4.1). If the edit changes anything, that is the new spec. If it is rejected, or changes nothing, the spec stays exactly as it was, defaults and all. So the first wish that is applied, from words or from a control and of whatever kind, makes the defaults give way; they do it once, because a quarter of a default is the same however often it is worked out; and a step from a default starts from where it gave way to, so that "care less about parks" takes a renter's park weight from 0.05 to nothing and not from 0.30 to 0.20. The budget's weight and the commute's are not scaled. A weight at default provenance for which the tenure has no default, which only a spec from the wire can hold, has nothing to give way to and is left as it is. So is a tag: no default holds a tag today, so none has a default to give way to.
12. A step up from a weight nobody chose is worth a mention at least (section 5.2).

Rules 11 and 12 change the spec, so its hash changes with it, and `rank()` is as it was: a pure function of the spec and the release. A spec that is ranked without any edit, a default among them, is ranked as it stands.

**Worked example.** A renter's first prompt is "leafy and quiet, near a park". The interpreter makes three edits, each a `nudge` of `up_large`: `feature:park_proximity`, `tag:leafy`, `tag:quiet_residential`.

| | Before | After |
|---|---|---|
| `station_walk`, `station_lines`, `highstreet_access`, `noise_exposure`, `air_no2` | 0.50, 0.30, 0.30, 0.20, 0.20, all `default` | 0.10, 0.05, 0.05, 0.05, 0.05, all still `default` |
| `park_proximity` | 0.30, `default` | 0.50, `stated`. It gave way to 0.05, a large step made that 0.30, and a mention is worth 0.50 |
| `leafy`, `quiet_residential` | no entry | 0.50 and 0.50, `stated` |
| Said, against unsaid | 0 against 1.80 | 1.50 against 0.30 |

Had the prompt been "near a park" and no more, the last row would read 0.50 against 0.30. Had it been "leafy", 0.50 against 0.35.

`RejectReason` is one of `unknown_place`, `unknown_area`, `not_in_release` (the release does not rank that feature), `too_many_commutes`, `no_such_commute` (an `update` or `remove` on a place not in the spec), `out_of_range` (a number given outright that is outside the limits of 5.2), `segment_not_for_tenure`, `direction_not_allowed` (rule 7), `crime_needs_explicit_request` (rule 8), `mismatched_choice` (a `choice` that does not belong to the `setting`, or a `nudge` of a setting that is not a weight) and `nothing_to_change` (the edit asks for nothing: a budget `set` or a commute `update` whose every field is a sentinel, a `nudge` whose step is `none`, or a `nudge` of a budget with no amount).

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
| `over_budget` | Budget is `hard`, an estimate exists, and `upper_quartile > amount` |
| `commute_cap` | A commute is `hard` and its time is over `max_minutes` or beyond the cutoff |

A hard filter removes only an area known to fail. An area with no estimate or no travel time cannot be tested: it stays, the component is dropped from its score, and the filter is listed under `untested_filters`.

`beyond_cutoff` is known to fail, and that is why `max_minutes` may not be above the release's cutoff for the mode: with a cap of 100 and a cutoff of 90, a journey beyond the cutoff might be 95 minutes and inside the cap, and the filter would remove an area it could not test.

### 6.2 Components

The score is a weighted mean of utilities, each between 0 and 1. A component that is not requested appears nowhere in the result and counts towards nothing. Hard filters apply whatever the weights.

| Component | Requested when | Weight `W` | Utility `U` | Missing, for one area, when |
|---|---|---|---|---|
| `commute` | There is a commute and `commute_weight > 0` | `commute_weight` | 6.3 and 6.4 | Any destination's time is `missing` |
| `budget` | `amount` is set and `budget.weight > 0` | `budget.weight` | 6.5 | There is no estimate |
| `feature:<id>` | Its weight is above 0 | its weight | `p / 100` if direction is `more`, else `1 - p / 100` | `percentile` is null |
| `tag:<id>` | Its weight is above 0 | its weight | `score / 100` | `score` is null |

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

`slowest`, the default, takes the `min` of the destinations' utilities: the worst journey, measured against what each person will put up with. `mean` takes their arithmetic mean. If the time to any destination is `missing`, the slowest cannot be known, so the whole component is missing for that area. The legs that are known are still reported.

### 6.5 Budget fit

The budget is tested against the upper quartile, because published rents understate what a new tenant pays. With `B` the amount and `Q3` the upper quartile for the spec's tenure and segment:

```
BUDGET_OVER_SHARE = 0.25
U      = clamp(1 - (Q3 - B) / (BUDGET_OVER_SHARE * B), 0, 1)
margin = B - Q3
```

So `U` is 1 when `Q3 <= B`, and falls in a straight line to 0 when `Q3` is a quarter over. Being further under budget earns nothing: Burro gives no affordability verdict. The confidence tier is reported and changes no arithmetic.

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
- `MIN_WEIGHT_COVERAGE = 0.5`. Below it the area is not scored and is reported under `unranked` with reason `insufficient_data`. An area with nothing present has coverage 0, so it is never scored and nothing is divided by zero.
- Whether an area is below it is decided in whole steps of 0.05, as `canonical()` counts a weight, and never by the float: the area is unranked when twice the steps that are present are fewer than the steps requested. With exactly half present an area is ranked, however the weight is split. In floats, 0.3 and 0.6 present of 1.8 requested come to 0.49999999999999994, and that must not be left to decide which side of the line an area falls, as it must not for a tag (section 3.2). The float is what is reported as `weight_coverage`, and nothing else.
- If nothing is requested, every area that passes the filters is ranked with score 0, `weight_coverage` 1 and no contributions, the order is by `area_id`, and `empty_spec` is true.
- Sums run over components in the order `commute`, `budget`, features by id, tags by id, so the floating-point result is the same everywhere.
- **Order and ties.** Sort by `round(S, 9)` from high to low, then by `area_id` from low to high. `rank` is the 1-based position. Areas with equal rounded `S` get different ranks; the id decides.

### 6.7 The result

| Type | Fields |
|---|---|
| `RankResult` | `spec_hash`, `release_id`, `engine_version`, `synthetic`, `empty_spec`, `ranked` (tuple of `RankedArea`, in rank order), `filtered` and `unranked` (each a tuple of `area_id` and `reason`, by `area_id`) |
| `RankedArea` | `area_id`, `rank`, `score` (0 to 100, 2 decimals), `weight_coverage` (0 to 1), `contributions` (every requested component, largest contribution first, then by name), `legs` (in `place_id` order, as the spec keeps them), `budget` (`BudgetFit` or `None`), `untested_filters` |
| `Contribution` | `component` (`commute`, `budget`, `feature:<id>` or `tag:<id>`), `present`, `weight` (as requested), `share`, `utility` (`None` when missing), `contribution`, `loss`, `fact_ids`. `share`, `contribution` and `loss` are 0 when missing, which is what they are: a dropped component has no share |
| `CommuteLeg` | `place_id`, `mode`, `status` (of the time that was scored), `minutes` (the time that was scored), `minutes_typical`, `minutes_just_missed`, `utility`. Each of the three times is `None` unless that time is `ok`. By bike and on foot all three hold the one time there is. `utility` is `None` when `status` is `missing`, and also when the component was not requested |
| `BudgetFit` | `upper_quartile`, `margin`, `utility`, `confidence`, `as_of` |

`fact_ids` names the facts of section 7.2 that stand behind the component: the `feature` or `tag` fact, the `budget_fit` fact, or the `travel` facts, with the leg that drove the score first. For a missing component it names the `missing` fact. `rank()` and `facts_for()` build ids by the one rule in 7.1, so an id `rank()` names is always an id `facts_for()` returns.

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

## 7. Facts, explanations and the verifier

### 7.1 The fact row

A fact is one thing Burro may say about one area, with where it came from and when.

| Field | Type | Notes |
|---|---|---|
| `fact_id` | str | `<area_id>/<kind>/<key>`, for example `syn-n0001/feature/park_proximity` |
| `area_id` | str | |
| `kind` | enum | `area`, `feature`, `tag`, `cost`, `budget_fit`, `travel`, `station`, `missing` |
| `key` | str | By kind, as the table in 7.2 gives it |
| `label` | str | From the catalogue or the template table |
| `template` | enum | Which template of 7.3 states this fact. `budget_under` and `budget_over`, or the nearest station and another, cannot be told apart from the slots alone |
| `slots` | mapping of str to str | The values a template prints, already formatted |
| `numbers` | tuple of str | Every number that may be printed for this fact, normalised by 7.4. A number that is money or a share keeps its sign, `£1750` and `80%`, so that it cannot be said of anything else |
| `names` | tuple of str | Every proper noun that may be printed for this fact |
| `sources` | tuple of `FactSource` | `source_id` and `name`, from the manifest, in `source_id` order. Never empty |
| `as_of` | str | The vintage, month or date. Never empty |
| `synthetic` | bool | From the manifest |

A fact has several sources when what it says was built from several, as a journey time and a tag are. `parse_release` refuses a release in which any fact would lack a source or a date, so `facts_for` never has to invent one.

### 7.2 Building facts

```python
def facts_for(release: Release, area_id: str, spec: PreferenceSpec | None) -> tuple[Fact, ...]: ...
```

It is pure and returns facts ordered by `fact_id`. Without a spec it returns what a profile page needs. With one it adds the `travel`, `budget_fit` and `missing` facts for that spec. A missing value never produces a fact that carries a number.

| Kind | One fact per | `key` | `numbers` | `names` | `sources` and `as_of` from |
|---|---|---|---|---|---|
| `area` | area | `name` | none | area name, borough | `origin(neighbourhoods)` |
| `feature` | feature with a value | the feature id | value, and what its comparison states: the share strictly beyond, how many areas were compared, how many are level (7.3) | none | the catalogue row: `source_ids`, `vintage` |
| `tag` | tag with a score | the tag id | what its comparison states, as for a feature | none | the sources of the features in its formula that had a value; the date of `built_at`, when the tag was worked out |
| `cost` | tenure and segment with an estimate | `<tenure>.<segment>` | the three quartiles, the year and month of `as_of` | none | the cost row |
| `budget_fit` | spec with a budget and an estimate | `<tenure>.<segment>` | amount, upper quartile, `abs(margin)` | none | the cost row |
| `travel` | commute in the spec, unless the time that is scored is `missing` | `<place_id>.<mode>` | each of the two times that is `ok`, and the cutoff when the scored time is beyond it | place name | `origin(travel)` |
| `station` | station row | the station id | walk minutes | station name, each line name | `origin(stations)` |
| `missing` | component the spec requests that is missing for the area | the component name | none | area name | `origin(neighbourhoods)` |

Numbers are formatted once, here: money with thousands separators, metres to the nearest 10, percentages to whole numbers, other values to one decimal with a trailing `.0` dropped. A share of areas is rounded down to a whole number and never to the nearest, so that a sentence never says more than is so. The mid-rank percentile an area is scored on is not among a fact's numbers and is never printed in a sentence: where areas tie it counts half of them as beaten, which is right for a score and untrue of the release.

### 7.3 Templates

Every template is filled from one fact's `slots`, and every template's output passes the verifier. `{value}` comes with its unit already attached, as people write it: `340 m`, `12%`, `3` for a count. The sentence states where the value sits and passes no judgement. Every comparison says "in this release", so a synthetic one can never say "London".

| Template | Text |
|---|---|
| `area` | {name} is in {borough}. |
| `feature` | {label}: {value}, {standing}. |
| `feature_crime` | The `feature` sentence, then: Recorded crime depends on what is reported, and locations are approximate. |
| `tag` | {label}: ranks {standing}. |
| `cost_rent` | Rent for a {segment}: £{lower} to £{upper} a month, middle £{median}, as of {as_of}. Confidence: {confidence}. |
| `cost_buy` | Price for a {segment}: £{lower} to £{upper}, middle £{median}, as of {as_of}. Confidence: {confidence}. |
| `budget_under` | The upper end is £{margin} under your budget of £{amount}. |
| `budget_over` | The upper end is £{margin} over your budget of £{amount}. |
| `travel_pt` | By public transport to {place}: about {typical} minutes on a typical weekday morning, {missed} if you just miss a service. |
| `travel_other` | {mode} to {place}: about {minutes} minutes. Used by bike and on foot, and by public transport when only one of the two times is `ok` |
| `travel_beyond` | {mode} to {place}: more than {cutoff} minutes. Used when the scored time is beyond the cutoff |
| `station` | Nearest station: {name}, about {walk} minutes on foot. Lines: {lines}. |
| `station_nearby` | Station within a short walk: {name}, about {walk} minutes on foot. Lines: {lines}. Used for an area's other stations, of which "nearest" would be untrue |
| `missing` | There is no {label} figure for {name} in this release, so it was left out of the score. |

**A comparison must be literally true of the release.** `{standing}` is one of the clauses below, filled in `facts.py` and held in the fact's slots beside its parts (`comparative`, `pct`, `compared`, `level`), so that a client can lay them out for itself. `STANDINGS` holds the clauses.

The areas compared are the ones a percentile is worked out over (section 2.4): the rankable areas that have a figure, `compared` of them, this area among them if it is rankable. Of those, `below` have a figure strictly lower than this area's, `above` strictly higher, and `level` others have the same. These are counts of areas, so each is exactly true.

| Clause | Used when | Text |
|---|---|---|
| `beyond` | No other area is level | {comparative} {pct}% of the {compared} areas compared in this release |
| `beyond_and_level` | Some are | {comparative} {pct}% of the {compared} areas compared in this release, and the same as {level} others |
| `all_level`, `one_level` | Every other area is level | the same as all {others} other areas compared in this release; the same as the only other area compared in this release |
| `level` | `{pct}` would be 0, which says nothing: under one area in a hundred is strictly beyond | the same as {level} of the {others} other areas compared in this release |
| `alone` | No other area has a figure | with no other area in this release to compare it with |

- The sentence is said from the side the percentile is on: from above when `below >= above`, which is when the mid-rank percentile is 50 or more, and otherwise from below. `{comparative}` is then the feature's "higher" or "lower" word followed by "than", and "above" or "below" for a tag.
- `{pct}` is the share of the areas compared that are strictly beyond this one on that side, `100 * below / compared` or `100 * above / compared`, **rounded down**. An area with no water at all, as 13 of 22 have, is "less than 40% of the 22 areas compared in this release, and the same as 12 others": 9 of 22 have more, which is 40.9%. It is scored on a percentile of 29.5, and the sentence it used to get, "less than 70% of areas", was untrue.
- An area that is level is never counted as beaten, and is always counted: `{level}` is stated whenever it is not 0. "Many" is not left to a threshold.
- The figures compared are the values as the release holds them, not as they are printed. Two areas 281 m and 283 m from a park both print as 280 m, and one is still closer than the other.

A test renders every feature and tag fact of the committed release and checks each comparison against the rows of the release, so that a change of wording cannot bring the defect back.

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
| 6. Banned words | "safe", "unsafe", "danger", "rough", "dodgy", "sketchy" fail anywhere, in every form they take: "safer", "safely", "safety", "dangerous", "dangerously", "roughly", "dodgier". A word that only holds one, "safeguarded", says something else and passes. The sentence is checked as it reads and not as it is encoded: accents, zero-width characters and soft hyphens are taken out, and a letter of another alphabet that reads as a Latin one is read as that one, so "safe" with a Cyrillic a is "safe" |
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
- **Reasons:** a reason is something the area does well. Of the present components whose utility is at least `REASON_MIN_UTILITY`, 0.5, the three with the largest `contribution`, ties by component name. Fewer if fewer qualify, and none if none does. A component below 0.5 adds to the score and is still no reason to live there: it can only be the trade-off. **A reason never states a shortfall.** The budget is a reason only when the home is within it, `margin >= 0`: a home £150 over a budget of £1,800 is worth 0.6667 and is no reason. The journey is a reason only when every journey that was scored is within its cap, the cap itself included: the mean of two journeys can be worth a half or more while one of them is over its cap, and the sentence states the slower one.
- **Trade-off:** a trade-off is something the area does badly. Of the present components that could never be a reason, because their utility is below `REASON_MIN_UTILITY` or because they are a shortfall (a home over budget, a journey over its cap), the one with the largest `loss`, ties by component name. If the area does nothing it was asked for badly, it has no trade-off: `trade_off` is `null`, and a client says so in fixed words of its own. **A trade-off is never something the area does well.** "A 2 minute walk, closer than 77% of areas" loses a little to the areas that are closer still, and was given as what the area gives up, because nothing it was asked for lost more. Every present component is now a possible reason or a possible trade-off, and never both.

It asks the explainer for a sentence for each, verifies every one, and replaces failures. A sentence is kept only if it cites the fact it was asked about first, and after it nothing but the `area` fact. What a sentence cites is what it may say, so one that could cite every fact of the area could say the minutes of a journey of a park. The `area` fact holds names and no number: it lets a sentence name the area and nothing more.

A sentence about `commute` cites the leg that drove the score, which is the first of the component's `fact_ids`: the leg with the lowest utility, and on a tie the first in `place_id` order. In the worked example Alderwick's reasons are `budget`, `commute` and `feature:park_proximity`, and it has no trade-off: being leafy is worth 0.72 to it and its noise 0.65, so neither is something it does badly, and neither is among its three reasons. Cindermoor's journey to place 1 is 44 minutes against a cap of 40, which is worth 0.40. It contributes 0.1333, more than being leafy does, and it is no reason: Cindermoor's reasons are `budget`, `feature:park_proximity` and `tag:leafy`, and the journey is its trade-off. Brackenhythe is £150 over budget, which is worth 0.6667 and is no reason either: its one reason is its journey, and its trade-off is the walk to a park, which is worth 0.40 and loses it more than the budget does.

`Explanation` is `area_id`, `orientation`, `reasons`, `trade_off` and `missing` (one `missing` sentence for each dropped component), where each entry is a `Sentence` plus `replaced: bool`.

**`explain()` takes `TemplateExplainer` and no other explainer.** It is a check in code: passed anything else, a class of the right shape included, it raises `TypeError` before anything is drafted, with a message that names this document and section 11. A second explainer is a second implementation of the protocol, and attaching one is a decision that changes this check and extends `verify()` first, not a parameter. A test that plants a sentence, to show that the verifier replaces it, does it from a subclass of `TemplateExplainer`, which nobody writes by accident.

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
| `InterpretResult` | `status`, `operations`, `assumptions` (each a `code`, `group`, `index`), `unmet` (tuple of `UnmetCategory`), `clarify` (each a `group`, `index` and up to five options of `id`, `name`, `kind`), `notice` (`none`, `neutral_places`, `off_topic`), `interpreter` (`rule`, `claude`), `degraded`, `usage` (`input_tokens`, `output_tokens`, `cache_read_tokens`), `rests_on` (each a `group`, `index`, `start`, `end`) |

`group` is the name of one of the six arrays and `index` a position in it, so an assumption or a clarification always points at an edit in `operations`. An assumption's `code` names what was chosen for that edit because the text did not say: `tenure`, `segment`, `strictness`, `mode`, `max_minutes` or `direction` for a field the edit left to a default, and `weight` for a weight or a tag whose provenance is `inferred`. `assumptions_for(operations, spec)` in `interpret.py` works them out from the edits and the spec they were made for, so both interpreters state the same assumptions for the same edits.

`rests_on` says which words of the text each edit rests on, so that a person can be shown which of their words made it. An entry points at an edit by `group` and `index` and holds `start` and `end`, which count the characters of the text as it was sent, as Python counts them (code points, not UTF-16 units), so that `text[start:end]` is the words. An edit made of several parts, as a budget is of "renting", "2 bed" and "£1,500", has an entry for each part, in the order they stand. Every edit the rule-based reader makes has at least one, and all of them lie in one sentence that the reader knows, but for a budget, whose parts may stand in several. It is offsets and never words: nothing stores them and nothing logs them, and they mean nothing without the text, which only the sender holds. An edit kept from a model rests on the words the reader read it from, where the reader made it too, and otherwise on the words the model copied, where they were found in the text (section 8.2).

The method is synchronous. API routes that call it are plain `def`, so FastAPI runs them on its thread pool and no test has to be written as a coroutine. Nothing in the result holds the user's words: assumptions and unmet requests are codes, notices are fixed text held in core, clarification options come from the release, and `rests_on` holds offsets.

| `status` | Meaning | `operations` |
|---|---|---|
| `ok` | Understood, in whole or in part | Every edit that could be made |
| `clarify` | A named destination or area matched nothing, or several things | Every edit. The unresolved one carries an empty id, so the reducer rejects it as `unknown_place` or `unknown_area` and applies the rest. `clarify` points at it and lists the options. The client sends it again with the id the person picked |
| `policy_redirect` | Part of the request was about who lives somewhere | Every other edit. `notice` is `neutral_places` |
| `off_topic` | Nothing in it is about choosing where to live | Empty. `notice` is `off_topic` |

`status` is the first that applies in the order `off_topic`, `policy_redirect`, `clarify`, `ok`. `clarify` and `notice` are filled whenever they apply, whatever the status. `RuleInterpreter` cannot tell an off-topic sentence from one it failed to read, so it never answers `off_topic`: it answers `ok` with no edits and `other` in `unmet`. `UnmetCategory` is one of `broadband`, `flood_risk`, `health_services`, `driving`, `listings`, `affordability_verdict`, `community_amenities`, `outside_the_city`, `other`.

### 8.2 What each receives and returns

| | `RuleInterpreter` | `ClaudeInterpreter` |
|---|---|---|
| Lives in | `burro_core` | `burro_api` |
| Needs | Nothing. No model, no network | A `ModelClient`. In this build the only one is the fake in the tests |
| Reads | The text, the spec, the release's names | The same |
| Sends out | Nothing | To the model: instructions, the vocabulary of ids and labels, the fixed policy rules, the text, and the canonical spec with each `place_id` replaced by its position. Never area data, facts or anything from another request |
| Gets back | | `ModelOutput`: the same six arrays, with `destination_text` and `position` in place of `place_id`, and `area_text` in place of `area_id`, plus `status` (`ok`, `off_topic`), `policy_flags` (a list of `avoid_group`, `seek_group`) and `unmet` (a list of `UnmetCategory`). Every edit of every kind also carries `words`: the words of the person's text that it rests on, copied as they were typed, at most 600 characters. `position` is the 1-based position of a commute in the spec that was sent, for a `remove`, and `0` for a destination named in `destination_text`. Like `Operations` it has no union and no optional field |
| Resolves names with | `Names.whole_place`, `whole_area`, on the text as typed; `Names.search_places` for what to offer | `Names.whole_place` and `whole_area`, on the text as typed: the whole of a name, and only one that stands in the sentence the edit rests on. The model never resolves a destination |
| Returns | `InterpretResult`, `interpreter: rule` | `InterpretResult`, `interpreter: claude` |
| On failure | Cannot fail; returns `ok` with no edits if it finds nothing | Raises `ModelTimeout`, `ModelCapped` or `ModelError`, and `ModelError` too when the output does not fit the schema. The route falls back to the rule interpreter and sets `degraded` |

`RuleInterpreter` must recognise at least: rent or buy; an amount with `£`, `k`, "pcm", "a month", "under", "up to" or "max"; bedrooms and property types; "N minutes to X", "work at X", "near X", with "cycle" or "walk"; every feature and tag by its label and by the phrases in `LEXICON`; the step words of 5.2; "not X", "avoid X" and "anywhere but X" for an area name. It reads a sentence only when it knows every token in it, and makes no edit from any other (below). `ClaudeInterpreter` reaches the model only through `ModelClient`, so its tests use a fake. `ModelReply` holds `output` and the three token counts.

What the rules read and how, where this contract was silent:

- Provenance is `stated` when the text names the thing and `inferred` when it is read into looser words. "Low crime" is stated and weights crime; "safe" is inferred, so the reducer rejects it.
- A name is tried with its article and without, because some names are written with one: "the Clinkers" finds a place whose alias is "The Clinkers". No name of the synthetic release is written with one today.
- The rules never produce `setting_ops`, never remove a commute and never move a commute's minutes from words. "In X" is not read as an `only` rule; "only in X", "not X", "avoid X" and "anywhere but X" are, and no other words are: "except X" and "unless it is X" make no rule.
- **Generic words are not names.** After "work at", "study at", "commute to", "travel to", "work in" and "N minutes to", the words "work", "the office", "school", "uni", "university", "college", "home", "my job", "town", "the city" and the like name no place. No journey is added and nothing is asked, because there is nothing to choose from, and the word is not read as a wish for schools or for a campus either. A name that begins with one is still a name: "Wexmoor University" is found. `GENERIC_PLACES` holds the words.
- Every place and area that the text names in full is found before anything is read, whatever stands before it. So the reader knows which sentence a name stands in, and the "green" of Dulcimer Green is never read as a wish for greenery. A name with no cue before it makes no edit. **A name is matched on the text as typed**, with nothing but a space between its words: it is never put together across a comma, a bracket, a hyphen, a slash, quotes or a line break. "I work at Foxholt (market research)" names Foxholt and not Foxholt Market.
- How much of a name a cue needs. After "N minutes to" and "work at" a name is expected. The whole of a name is taken. Words that are the whole of no name are what the person calls the place: they are asked about, with what `search_places` offers for them, and add no journey, because the edit carries no place. They are asked about only where nothing else is said after them, and where no whole name stands among them: "I work at Pellam" asks which, "I work at Pellam Infirmary sadly" is left unread. It is the one place where words the reader does not know are not doubt, because a question adds nothing to a search. After "not", "avoid", "only", "near", "close to" and "not far from", what follows is as often no name at all, so only the whole of a name or an alias is taken and nothing is asked: "not far from a park" excludes no area, though "far" begins Farrowmere, and "near Pellam" adds no journey, though two places begin with it.
- **The reader reads a sentence only when it knows every token in it.** It is a fallback, and the controls on screen are always there, so a wish it does not read costs little and a wish it reverses costs trust. It was put right twice by listing the words that turn a wish round, and each time an adversary found a hundred more sentences that came out as the opposite of what was asked: English has too many such words, and people mistype them. So the rule was turned round. The reader keeps no list of reasons to doubt a sentence. It keeps the list of what it knows, and reads nothing else.

  1. **What is known.** A token is known if it is, or is part of: a phrase of `LEXICON`; the whole of a name or an alias of the release; a number, an amount of money, or a number typed with its unit ("£1,500", "450k", "30mins", "2-bed"); a word for what Burro cannot answer or for who lives somewhere, which is heard and makes no edit; a plain word of `vocabulary.PLAIN`; or a word the reader has an explicit rule for. Every other token makes the sentence unknown: the reader makes no edit from it and reports `other` in `unmet`. `VOCABULARY` in `interpret.py` is every word and phrase that is known besides the lexicon and the names.
  2. **The plain words are short, written down in one place, and reviewed as a whole.** `vocabulary.PLAIN` holds about 130 of them in groups, each group with why it is safe: the speaker ("I", "we", "my"), to wish in the present tense ("want", "need", "like", "would"), to be and to have, articles and words of plenty, what a place is called, words of good opinion, words that strengthen, where a thing is, what joins two wishes, how a place is reached, courtesy, and how much a thing counts. A word is plain only if it can never turn a wish round, weaken it, compare it, question it or give it to someone else. So there is no past tense among them ("wanted", "was", "used"), no third person ("wants", "works", "they", "people", "you"), no word that asks ("who", "why", "should", "do"), no word that weakens ("maybe", "quite", "ideally", "if") and no word of distance or absence ("far", "away", "off", "none"). Some words are known only with others beside them: "on foot", "walking distance", "close by", "I can", "for the kids". "Like" and "love" are known only straight after the speaker, where they are what the speaker does: "I need pubs like I need noise" is left unread. Adding a word to `PLAIN` is the only way to widen what the reader reads, and a test holds the number.
  3. **A sentence ends only at a full stop, a question mark, an exclamation mark or a line break.** A comma, a semicolon, a colon, a dash, a bracket and a quote do not end it, so a word the reader does not know anywhere between two full stops leaves the whole of it unread: "leafy, quiet, and nothing like where I live now" reads nothing. A token is what stands between two spaces, less the marks around it, and is never split at a mark inside it: "don;t" is one token that the reader does not know, and so are "pubs/bars", "-pubs", a face, and a word in quotes. A word written with a hyphen is read whole or not at all: "well-connected" is the phrase of the lexicon, and "pub-free" is nothing.
  4. **A question makes no edit.** A sentence is one if it ends in a question mark, opens with "is", "are" or "am", or puts a verb before the speaker ("would I want a pub next door"). Nor does a sentence whose subject is not the speaker, which follows from what is known: "my partner works at" and "kids love playgrounds" hold words the reader does not know, and "some work at Pellam Cross" has no speaker before its verb.
  5. **A word that turns is read by one rule, or the sentence is left unread.** The words the reader has a rule for are these, and no other word is ever read as one:

     | The words | What they say | Read where |
     |---|---|---|
     | "no", "not", "without", "avoid", "don't want", "don't like", "not near" | The first thing after them is wanted not at all | They stand before a thing, with only plain words between |
     | "less", "fewer", "low", "not too", "not many", "not much", "not so", "not very" | The first thing after them is wanted less | The same |
     | "don't care about", "don't need", "don't mind", "not bothered about", "ignore", "remove", "get rid of"; after the thing, "is not important", "doesn't matter" | The weight is taken off | Before the thing, or after it |
     | "care less about"; after the thing, "is less important", "is not essential", "is not a priority", "matters less", "low priority" | The weight is turned down | Before the thing, or after it |
     | "worry about", "worried about", "concerned about" | It troubles the person | Before a nuisance, where it is the wish itself. Before anything else, no edit |
     | "up to", "under", "within", "below", "max", "less than", "around", "about" | The most a number may be, softly | Before a number of minutes or of money |
     | "no more than", "not more than", "at most", "cannot go over" | The same, as a limit | The same |
     | "only", "only in", "must be in", "has to be in" | An `only` rule | Before the whole of an area's name, in a part of the sentence that says nothing else |
     | "not", "not in", "avoid", "anywhere but" | An `exclude` rule | The same |
     | "not far from", "not too far from" | "Near" | Before a thing or a place |
     | "too" | "As well" | After a thing, at the end of a part of the sentence. Anywhere else it is not known |

     A word that turns governs the first thing after it and no more. What a turned thing becomes depends on the thing, as before:

     | The thing named | Example | Edit | `unmet` |
     |---|---|---|---|
     | A nuisance (section 3.1) | "less noise", "no pollution", "I worry about burglary" | A step up, in its one direction | |
     | A feature whose polarity is `either` | "fewer pubs", "no pubs" | A step up with `direction: less` | |
     | A campus | "not near a university" | None. It is a request about who lives somewhere (section 8.4) | |
     | Any other feature, or a tag | "no parks nearby", "not near a station", "not leafy" | `remove`. Where less is wanted and not none, "less green space", "not too buzzy", a small step down | `other`, because to be away from the thing is a wish no edit can express |
     | A phrase that says which way it is wanted | "not spacious", "no low crime" | None | `other` |
     | A second thing in the same part of the sentence | the park of "no pubs near a park" | None. The word governs one thing | `other` |
     | A place, a journey, a number or a word for the home | "not near Pellam Cross", "not renting", "not under £1,500" | None | `other` |

     A sentence is left unread as a whole where a word that turns has nothing after it to turn ("pubs, no", "pubs are not for me", "a park is not a must"), where two of them stand over one thing ("not without a park", "avoid areas with no parks", "not only parks"), and where known words mean the opposite together ("a bit much"). What is both asked for and turned away in one request makes no edit: "pubs or no pubs", "to buy or not to buy", "I commute to Pellam Cross and I want to not commute to Pellam Cross".
  6. **A list shares what turns it.** What is joined to a turned thing by "or" is wanted as the first is: "no parks, playgrounds or schools" takes all three off. What is joined to it by a comma or "and", with nothing said of it but its name, is left alone, because the reader cannot say: "no parks and playgrounds" takes the parks off and does nothing about playgrounds, and "leafy, no pubs, quiet" reads "leafy" and not "quiet". "But", the speaker's own wish ("I want") and a word of its own ("near", "good") begin a new wish: "no pubs, but a park nearby" asks for a park. What is said after the last item of a list is said of every item, and only the last is edited: "parks, playgrounds and schools are not important".
  7. **A sentence that holds doubt and names nothing takes back what stands beside it.** It holds doubt if the reader did not read it, and names nothing if it holds no thing, no place, no number and no word for the home: "No thanks.", "None of that for me.", "Not really.", "I disagree." It takes back every raising edit of the sentence before it, whatever that is. And it takes back what is listed beside it, before and after, as far as the list goes: "Pubs. Bars. None of it." raises nothing, and nor does "Dealbreakers:" on a line of its own with a pub on each line below. A list ends at a sentence in which the speaker says what they want: "Things I hate. Pubs. Bars. I want a park." raises the park. What was lowered or taken off is not taken back.
  8. **A number that is a minimum is never a cap.** "At least", "more than", "no less than", "further than", "over" and "minimum" are no words of the reader's, so "at least 30 minutes from Wexmoor University" makes no edit, and gets the notice of section 8.4 because a campus is named. A number of things is no limit the reader sets either: "at most 2 pubs" is left unread. A number with no sign of money on it is an amount only beside a word that limits or a word for the home or for money, and only from 100 up.
  9. **A word for renting or buying** sets the tenure only in a sentence that is known, and not under a word that turns: "I'm done renting" and "not renting" make no edit. "I want to buy, not rent" sets buying.
  10. **A nuisance the person says they like** makes no edit: "I like noise", "somewhere noisy and lively" reads "lively" alone. Nor does one that is only named, "noise". It is read where less of it is wanted, where it troubles the person, where it is said to matter ("noise matters to me", "I care about crime"), and where the phrase says so itself: "low crime", "clean air". That it is a must is not that it matters: "pollution is a must" makes no edit.
  11. **Two phrases that overlap.** The reading that leaves the fewest tokens unknown is taken, and of two that leave none, the one made of the longest phrases. "Good transport links" is "good" and "transport links", though "good transport" is a phrase too, and "Wexmoor University" is the campus and not the area of Wexmoor.
  12. **A campus in a sentence the reader does not read**, or under a word that turns, is a request about who lives somewhere, by word or by name: no edit, and the neutral notice (section 8.4).

  `sentences_of(text, names, release)` says of each sentence where it starts and ends and whether the reader read it (`known`), whether it holds a word the reader has a turning rule for (`turning`), whether it holds a word of the written list of doubt or a token with a mark inside it (`doubt`), whether it asks (`asked`) and whether a sentence beside it took back what it raised (`taken_back`). It is for a caller that must hold edits the reader did not make to the same test, the model-backed interpreter. `vocabulary.WORDS_OF_DOUBT` and `PHRASES_OF_DOUBT` are the written list: the reader does not read it, since none of its words is known to it, and a test holds `PLAIN` to it so that no word that ever turned a wish round is read through. The model-backed interpreter reads by `sentences_of` and by the reader's own edits (below). `clauses_of` and `signs_of_doubt` are worked out from the same one reading and are no longer called by it; `SIGNS_OF_DOUBT` is what its generated test draws its sentences from.

  What this costs is written in section 13: plain wishes that are no longer read.
- A model's `ui_edit` is read as `inferred`. A model is not a control, and without this it could weight crime by calling its reading a slider's.
- What is sent to the model is JSON, `{spec, request}`, so nothing typed can close the field it is in.

**What is kept from a model.** A model is told all of the above in its instructions, and can still be wrong about each. So `ClaudeInterpreter` keeps from a model's answer only what the code can justify without trusting the model. The model must say, for each edit, which words of the person's it rests on. The code looks for those words in the text as it was typed, asks the rule-based reader what it made of the sentence they stand in (`sentences_of`, and the reader's own edits with their `rests_on`), and keeps the edit or leaves it out by that. Nothing in `claude.py` decides what a word means: the vocabulary, the lexicon, the written list of doubt and where a sentence ends are core's. Each rule holds whatever the model answers, and each is tested with a stand-in that answers wrongly.

| Rule | How it is kept | What the person sees |
|---|---|---|
| 1. An edit rests on words of the person's, in one sentence | `words` is looked for in the text as it was sent: the same words, in the same order, with the same marks between them, all within one sentence as core divides the text. The case of a letter, the shape of an apostrophe, the width of the space between two words and the marks before the first word and after the last are left out of account, and nothing else is. Part of a word is not the word. Words that stand in the text more than once are read where some sentence bears the edit out. An edit with no words, with words the person did not type, with their words in another order or with one left out, or with words from either side of a full stop or a line break, is left out | No edit, and `other` in `unmet` |
| 2. A place or an area is kept only if the words of its name stand in that sentence, as typed | `destination_text` and `area_text` must stand in the sentence the edit rests on, side by side with nothing but space between them, and be the whole of a name or an alias of one place or area (`Names.whole_place`, `whole_area`). A name is never put together across a bracket, a hyphen, a slash, quotes, a comma, a colon, a dash or a line break, in the person's words or in the model's: "I like Foxholt (market towns generally)" does not name Foxholt Market, and "lantern-yard" is one word. The longest name is the one that is named: "Wexmoor University" is the campus and not the area of Wexmoor. The model may only copy: a name it corrected, completed, shortened or swapped for another name of the same place is left out. Words that are the whole of no name are kept only as the question the reader asks of them, after words that expect a place ("I work at Pellam"), with the reader's options and with no minutes, mode or strictness of the model's | No edit, no question, and `other` in `unmet`. A name the model supplied is the model steering from what it knows of a city (ADR 0002), and on a request about people it is steering by area (ADR 0006) |
| 3. In a sentence the reader knows, the reader's reading is the whole of it | Where the words stand in a sentence the reader read in full (`known`), the edit is kept only if the reader made an edit of the same kind from words of that sentence: the same feature or tag, raised or lowered alike and in the same direction; a journey added to the same place, or the same question; the same rule for the same area; a budget edit of the same action. What is applied is the reader's own edit, so not a number, a mode, a strictness or a degree is the model's, and the words it rests on are the ones the reader read it from. The reader knew every word, so there is nothing in the sentence for a model to add: "I love pubs" read as fewer pubs, "quiet and leafy" read as buzzy, "I am renting a one bed" read as buying, "I like noise" read as a wish for quiet, a park taken off in "I really want to be near a park", and a setting changed in "no pubs" are all left out. The reader never changes a setting and never changes or removes a journey, so in such a sentence none of those is kept | The reader's edit, or no edit and `other` in `unmet` |
| 4. In a sentence the reader does not know, a model reads a wish for a thing the reader has no phrase for, and no more | A weight or a tag is kept there, as `inferred` whatever the model called it, if the sentence does not name that feature or tag in a phrase of `LEXICON` or by its label, and: to raise it, the sentence holds no word the reader has a turning rule for (`turning`) and no word of the written list of doubt or token with a mark inside it (`doubt`), does not ask, and no sentence beside it takes it back; to lower it or take it off, the sentence holds a word of the written list of doubt, or a word the reader has a rule for that turns a wish away or takes it off ("no", "not", "less", "don't care about"), and does not ask. A word that caps a number or confines a search turns nothing away: "an absolute maximum" is no reason to take a budget off. A change to a setting is kept on the same terms as a raise. A weight turned against the usual direction of its feature is never kept there. A journey and a budget are made of a name, a number and words for travelling and for the home, all of which the reader knows: where it could not read the sentence they stand in it cannot say whose journey it is, or which way a number runs, so nobody adds, changes or sets one there. To remove a journey or clear a budget is kept on the terms on which a weight is taken off. One edit is kept for each thing, however often the model says it | The model's edit, shown with `weight` among the `assumptions`, or no edit and `other` in `unmet` |
| 5. A rule about an area is the reader's alone | An area rule is a filter. It is kept only where the reader reads the same rule for the same area, in a sentence it knows: "only Cindermoor" with a model that answers `exclude` makes no rule, praise of a place excludes nothing, and a rule is cleared only where the reader reads a clearing, which today it never does | No edit, and `other` in `unmet`. The controls are on the screen |
| 6. When the request is about who lives somewhere, only the edits the reader makes are kept | The request is one if the reader finds it so or the model sets a flag. Rule 3 then holds in every sentence, known or not, and in all six groups of edits: what is kept is the reader's own edit, where the model made one of the same kind from words of the same sentence | `policy_redirect` and the notice. What only the model read is withheld, a wish in the rest of the request among it. Words the person did not type add `other` to `unmet`; the rest is what the notice is about |
| 7. Recorded crime is weighted only where the reader makes a stated edit that raises it | In a sentence the reader knows, rule 3: the edit applied is the reader's, `stated` for "low crime" and `inferred` for "safe". In any other sentence a weight on crime that a model raises is marked `inferred`, as every weight there is. It is decided feature by feature: "burglary" asks about theft and not about violence | The reducer rejects an `inferred` weight on crime, `crime_needs_explicit_request` (section 5.3 rule 8) |
| 8. A model that answers off topic does not overrule the reader | The reader reads the text whatever the model's `status`. If it makes an edit or finds a request about who lives somewhere, its answer is served in the model's place | The reader's answer, with `interpreter: rule` and `degraded` true. The tokens the model used are still counted |
| 9. A number in the answer is a number | `ModelOutput` is held to the rule of section 9.1: `true`, `false`, `"1"` and `"0.5"` in a number's place are refused before they can be read as 1, 0 or 0.5. The answer is then no answer, and `ModelError` is raised with no message | The rules answer in the model's place, with `degraded` true. `true` for a position once took the first journey out of a person's spec |

Rules 3, 5 and the second half of rule 4 go further than the decision they were built to. The decision was that an edit which raises is kept if its sentence is known and the reader makes the same kind of edit, or if its sentence holds no word that turns and no word of the written list of doubt. Held to that letter in the sentences the reader does not know, a stand-in that raised every thing a sentence names got an edit applied in 52 of the 124 sentences an adversary had written against the reader, because no list of doubt is ever whole: "Pubs, yuck", "I dinnae want pubs", "Dealbreakers: pubs, a station", "My ex works at Pellam Infirmary". Held to the rules above it gets one through, which is the reader's own and right. What that costs a model that reads every plain sentence as it is meant is in section 13.

What this cannot do:

- If the lexicon misses a request about people and the model does not flag it either, nothing in the code knows what the request was about, and a model that turns it into a tag is believed. "Full of bankers and yummy mummies", read by a model as `family_amenities` with no flag, still goes through. It can no longer be turned into a rule about an area or a journey. Closing the rest needs a wider lexicon in core, and it is measured by the golden queries of the plan.
- A wish turned round, of a thing in words the reader has no phrase for, in a sentence that holds nothing core lists as doubt: "boozers on every corner would finish me off", "a proper brunch spot is my idea of hell". A model that raises the thing there is believed. It is shown as an assumption, with the words it rests on.
- Someone else's wish for such a thing, in words core does not list: "My sister swears by a proper brunch spot".
- A sentence that holds doubt and names nothing, in words core does not list, after a wish only a model reads: "Somewhere with a proper brunch spot. I disagree." The reader takes back what it could have read itself, and says nothing of a sentence it could not.
- `tests/test_claude_kept.py` holds each of these as a test that is expected to fail, so that the day one is closed the test says so.

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
| `search_places(text, release, limit)` | Nothing. It is a search | Every match, best first, cut to `limit` |
| `resolve_place(text, release)`, `resolve_area` | The best match, if it scores 0.9 or more and no other match scores the same | The first five matches are the options. That includes a match on part of a word, and a single match at 0.6. No match gives an empty list, and the client shows a search box |
| `Names.exact_place(text)`, `exact_area` | The best match, if it scores 1.0 and no other does | Nothing, and no options. It is for words that may not have been meant as a name at all |

`resolve_area` and `exact_area` do the same over area names and aliases. `Names.whole_place(words)` and `whole_area` answer as `exact_place` does for words that are already normalised, without scoring every name. The rule-based reader takes a name by these two alone, on the text as typed (section 8.2), and offers what `search_places` finds for words that were given as a name and are the whole of none: it no longer takes whole words from the start of a name without asking. The model-backed interpreter takes a name from a model only by these two, and only one that stands in the sentence the edit rests on, as typed (section 8.2). Where the model's words are not the whole of a name it keeps the question the reader asks of those same words, and nothing otherwise. The text is dropped as soon as it is resolved.

### 8.4 A request about who lives somewhere

Burro ranks places, never residents, so no edit can express such a request: there is no id for it.

| Request | Example | Response |
|---|---|---|
| To avoid a group | "not too many students", "fewer immigrants" | No edit for that part. `policy_redirect`. The rest is applied, where the rules know every other word of the sentence |
| To find a group | "lots of young families", "young professionals", "gay village", "student village" | No edit for that part. `policy_redirect`. The rest is applied. It is not quietly turned into a tag |
| To be far from a campus | "far from a university", "nowhere near a university", "not near the campus", "miles from any university", "somewhere that isn't near a university", "nowhere near Wexmoor University", "University is not for me" | No edit for that part. `policy_redirect`. The rest is applied. It is a way to ask for fewer students, and the feature has one direction (section 3.1). The rule is not a list of phrases: a campus, by word or by name, in a sentence the reader does not read, or under a word that turns, is read this way (section 8.2). "The rest" is then every other sentence: a comma does not end one, so "quiet, far from a university" reads nothing, and "Quiet. Far from a university." reads "quiet". "Near a university" and "not far from a university" are wishes about a place and are ordinary edits, and so is "don't care about universities", which takes a weight off |
| For a community's amenities | "near a mosque", "kosher shops", "muslim schools", "gay bars", "Polish shops" | `ok`, with `community_amenities` in `unmet`, and no edit: "muslim schools" is not a weight on school results. The v1 catalogue has no such feature |
| For amenities by name | "good primary schools and playgrounds", "Turkish cafes" | `ok`. Ordinary edits |

The `neutral_places` notice is one fixed sentence: "Burro ranks places by what is there, such as schools, parks, venues and transport, and never by who lives there. The rest of your search has been applied." It is the same for every group and every user.

`POLICY_LEXICON` lists the terms for protected characteristics and for kinds of resident. It holds words for people, never for buildings: "mosque" and "kosher shop" name amenities and are not in it, or the fourth row above could never be reached. A group named as a plural noun stands alone. The word directly before a term is closed with it, so "quiet neighbours" makes no edit.

A word for a group is read with the word after it, whatever that word is, so that it can never be left to the lexicon:

| The word for a group | Beside a word for people | Beside a venue or a shop | Beside anything else |
|---|---|---|---|
| Is a word for nothing else: a religion, a sexuality, "foreign", "immigrant", "religious", "student" | A request about people | A community's amenity, heard and reported as unmet: "muslim schools", "gay bars" | A request about people, and the word after it is closed with it: "gay village" is never the village-feel tag |
| Is also a cuisine, a country or a colour: "Turkish", "Polish", "Asian", "black", "white" | A request about people | A place to eat or drink is an ordinary wish: "Turkish cafes", "Irish pubs". Any other venue or shop is a community's amenity: "Polish shops" | Nothing. "White stucco houses" and "an English garden" ask nothing about people |

A venue or a shop is one of a short list of nouns, `_AMENITIES` in `interpret.py`, looked for within three words of the word for the group, so that "a Catholic primary school" is heard whole.

The lexicon is a first guess: it fires on some innocent sentences ("a diverse range of restaurants", "I am a student nurse") and misses groups it does not list, and a venue that is not on the short list is taken for a request about people. No edit can express such a request either way, so what a miss loses is the notice, and what a false alarm costs is one sentence that did not apply. Both interpreters run it over the text. For `ClaudeInterpreter` it is a backstop: the status is `policy_redirect` if the rules find a request about people or the model sets a flag, and a model that answers `off_topic` does not overrule it. Either way what is applied is then the rules' own edits, and of those only the ones the model made too, in every group of edits (section 8.2), so that the notice is never sent with the request quietly applied beside it as a weight, a journey, a budget, a setting or a filter on areas.

## 9. The API

### 9.1 Every response

```json
{"meta": {"release_id": "syn-2026-09-23-01", "engine_version": "1.3.0", "synthetic": true},
 "data": {}}
```

Errors replace `data` with `error`: `{"code": "...", "message": "...", "fields": [{"path": "spec.commutes[0].max_minutes", "problem": "out_of_range"}]}`. `message` is fixed text for the code. `fields` holds paths and problem codes and never a value that was sent. Every response also carries the header `X-Burro-Synthetic: true` or `false`, and `X-Request-Id`, which the server makes and never takes from a header. Bodies are JSON, at most 16 KiB in. Typed text is measured without the space around it, so a line of spaces is an empty line. All text that a person typed travels in a request body, never in a path or a query string, so it cannot reach an access log.

**A number is sent as a number.** Wherever a body holds a number, in the body itself, in the spec or in an edit, the JSON value must be a number: `true`, `false`, `"1"` and `"0.5"` are refused with `wrong_type` at the field's path (`not_allowed` for `schema_version`, which takes one value), and never read as 1, 0 or 0.5. A whole number is a number wherever one is asked for, so `1` is a weight of 1.0. The check reads each body beside its own schema, so it covers the records of core without changing them, and a field that is added later.

**Browsers.** A page may read an answer only if it was served from an origin on a list. The list comes from the setting `BURRO_ALLOWED_ORIGINS`, origins separated by commas, and is `http://localhost:3000` when nothing is set. An origin is a scheme, a host and perhaps a port, in lower case as a browser sends it, and it is compared exactly: there is no pattern, no "every origin", and `null` is not an origin. An entry that no browser would send would match nothing, and whoever wrote it would not be told, so it is refused when the service starts: one with a path, a slash at the end or a capital; one that names the port its scheme implies, `:443` for `https` and `:80` for `http`, which a browser leaves out; a port of 0, one above 65535 or one written with a nought in front; and a host that is not labels of letters, digits and hyphens with a point between them, each of 1 to 63 characters with a letter or a digit at each end, and 253 characters at most in all. A host that ends in a point is refused with the rest, though a browser can be made to send one. The refusal never repeats what was set.

| The call | The answer |
|---|---|
| From an origin on the list | As any answer, errors included, with `Access-Control-Allow-Origin` set to that origin and `Access-Control-Expose-Headers: X-Burro-Synthetic, X-Request-Id` |
| From any other origin, or from none | As any answer, with no `Access-Control-` header. The call is answered and the browser keeps the answer from the page |
| `OPTIONS` with `Access-Control-Request-Method`, from an origin on the list | 204 and no body, with `Access-Control-Allow-Methods: GET, POST`, `Access-Control-Allow-Headers: Content-Type` and `Access-Control-Max-Age: 600`, whatever the path |
| The same from any other origin | 405 `method_not_allowed`, as for any `OPTIONS` |

Every response carries `Vary: Origin`, allowed or not, because routes 4, 5, 6 and 11 may be cached and the answer differs by who asked. No response carries `Access-Control-Allow-Credentials`: the service sets no cookie and reads none. What is sent back is the entry of the list and never the header that was sent, and the `Origin` header is logged no more than any other.

### 9.2 Routes

| # | Route | Request | `data` | Errors | Pure |
|---|---|---|---|---|---|
| 1 | `POST /v1/interpret` | `text`, `spec` (optional; a default renter spec if absent) | `status`, `operations`, `spec` after the reducer, `spec_hash`, `applied`, `rejected`, `assumptions`, `unmet`, `clarify`, `notice`, `notice_text`, `interpreter`, `degraded`, `rests_on` | 422 `invalid_text`, `invalid_spec`, `unknown_place`, `unknown_area` | No |
| 2 | `POST /v1/rank` | `spec`, `operations` (optional), `limit` (1 to 100, default 20) | `spec` after the reducer, `spec_hash`, `applied`, `rejected`, `scores` (every ranked area in rank order, each an `area_id` and a `score`), `ranked` (the first `limit` in full), `filtered`, `unranked`, `empty_spec` | 422 `invalid_spec`, `invalid_operations`, `unknown_place`, `unknown_area` | Yes |
| 3 | `POST /v1/explanations` | `spec`, `limit` (1 to 5, default 3) | `explanations` for the top `limit` areas, and `facts` for every fact cited | 422 as route 2 | Yes |
| 4 | `GET /v1/areas` | | `areas`: `area_id`, slug, name, borough, centroid, rankable | | Yes |
| 5 | `GET /v1/areas/geometry` | | The `FeatureCollection` of `geometry.json` | | Yes |
| 6 | `GET /v1/areas/{id_or_slug}` | | The area, `features`, `tags`, `cost`, `stations`, `neighbours`, and `facts` built with no spec | 404 `area_not_found` | Yes |
| 7 | `POST /v1/compare` | `area_ids` (2 to 4, no repeats), `spec` | `areas`, each with its `status` (`ranked`, or the reason it was filtered or left unranked), and `rows` ordered by the spec's weights from high to low, then by component name. A row has the component, its label, its `weight`, and for each area the `value`, `percentile`, `utility`, `contribution` and `fact_id`. `facts` holds every fact a cell cites | 422 `invalid_compare`, `invalid_spec`, 404 `area_not_found` | Yes |
| 8 | `POST /v1/places/search` | `q` (2 to 80 characters), `limit` (1 to 10, default 8) | `places`: `place_id`, `name`, `kind`, and the name of its coarse place | 422 `invalid_query` | Yes |
| 9 | `POST /v1/shares` | `spec`, `exact_destinations` (default false) | `share_id`, `spec` as stored, `coarsened` | 422 as route 2 | No |
| 10 | `GET /v1/shares/{share_id}` | | `spec`, `spec_hash`, `coarsened`, `stale`, `original_release_id`, and the result of ranking it now, as route 2 gives it with the default limit | 404 `share_not_found`, 410 `release_changed` | No |
| 11 | `GET /v1/meta` | | `release_id`, `built_at`, `synthetic`, `engine_version`, `catalogue_version`, `counts`, `attributions`, `features`, `tags` with their formulas, `defaults` for a renter and a buyer, `limits` with the release's `cutoff_minutes`, `max_text` and `max_body_bytes` | | Yes |
| 12 | `GET /healthz` | | `{"ok": true}`, with no `meta` | | |

Any route can also return 400 `malformed_json`, 413 `body_too_large`, 415 `unsupported_media_type`, 422 `invalid_request` (a field that belongs to no part of the body named above, such as `limit`) and 500 `internal_error`. A path that is no route answers 404 `not_found`, and a method a route does not take 405 `method_not_allowed`. A path with a slash too many, `/v1/rank/`, is no route: it is never redirected, because a redirect has no envelope and repeats the path, a share's id with it, in a header. No route returns 401, 403 or 429 in this build, and none answers with a redirect.

`problem` in `fields` is one of the codes of `check_spec` (section 4), or what a validation error comes to: `missing`, `unknown_field`, `wrong_type`, `not_allowed`, `bad_format`, `out_of_range` or `invalid`. A position in the path of a `check_spec` problem is a position in the spec in id order, which is the order a spec is returned in, and not in the body as it was sent (section 4). A position in the path of a validation error is the position sent, because a body that does not validate was never made into a spec. A part of a `path` is kept only if it is one of Burro's own field names or a position, because the name of a field that should not be there is itself something the sender wrote.

`rests_on` on route 1 says which words of `text` each edit of `operations` rests on (section 8.1): a list of `group`, `index`, `start` and `end`, in the order of the six groups, then by edit, then by where the words stand. `start` and `end` are offsets into the text **as it was sent**, the space around it included, though the text is read without that space. They count code points and not UTF-16 units, so a client in JavaScript takes `Array.from(text).slice(start, end)` and one in Swift counts along `text.unicodeScalars`: `text.slice(start, end)` is wrong by one for every character before the words that is two units long, such as most emoji. Every edit that is served is pointed at, the one that is asked about in `clarify` and one that the reducer rejects among them, and no entry points outside the text or at an edit that was not served. No other route takes or returns them. They are served to the caller, who holds the text, and are never logged, kept about a call or stored in a share (section 10.1).

In a comparison, `value` is the feature's value, the minutes of the leg that drove the score for `commute`, and the upper quartile for `budget`. `percentile` is the feature's percentile or the tag's score, and `null` for `commute` and `budget`. `utility` and `contribution` are `null` for an area that is not ranked, and so is the journey: which leg drives the score is decided by scoring, and an area that was filtered was not scored (section 13). Every cell that holds a number names the `fact_id` that carries its source and date, because a comparison shows numbers about places like any other page.

No list on the wire mixes types. `scores` holds objects and not pairs such as `[area_id, score]`, because one OpenAPI file has to generate a TypeScript client and a Swift one, and a list of mixed types generates badly in both.

### 9.3 What "pure" means here

| Routes | Property | Caching |
|---|---|---|
| 4, 5, 6, 11 | A function of the release alone | `Cache-Control: public, max-age=3600`, `ETag` set to the release id |
| 2, 3, 7, 8 | A function of the body and the release. They are `POST` only to keep text and destinations out of URLs | Not cached. Ranking takes milliseconds, so there is nothing to save |
| 1 | Depends on a model when one is configured | Not cached in this build (section 11) |
| 9, 10 | 9 makes a random id. 10 depends on which release is loaded | `Cache-Control: no-store` |

### 9.4 Behaviour worth pinning down

- **Form mode.** Route 11 returns everything a form needs: the vocabulary, both defaults and the limits. Routes 2, 3, 7 and 8 need no model. With no key, a slow model or a capped one, the product is that form.
- **Falling back.** Route 1 uses the interpreter in `Deps`, with a timeout from settings, 6 seconds by default. On `ModelTimeout`, `ModelCapped` or `ModelError` it answers from `RuleInterpreter` with `degraded` true. It never returns 5xx because a model failed. A model that answers `off_topic` where the reader made an edit, or heard a request about who lives somewhere, is answered for in the same way, and the call keeps its status (section 8.2 rule 8). The interpreter in `Deps` is `RuleInterpreter` itself unless a key is present in the environment, or a test passes another. The route keeps its own deadline around an interpreter that is not the rules, because a client's timeout times each read and not the whole call.
- **Edits first, then the check.** Routes 1 and 2 apply the edits with the reducer and run `check_spec` on the spec they leave, not on the spec that was sent. A spec kept from an older release, which names a place or an area the loaded release has dropped, is refused as it stands and accepted with the edit that takes the name out (section 5.3 rule 6). With no edit, or with one that leaves the problem in, the answer is the same 422 as before, and its paths are into the spec after the edits. Route 1 reads the words before it can know whether the spec will pass, so a spec that is refused there has still cost a call to the interpreter, and the call is on record. Routes 3, 7 and 9 take no edits and check the spec as sent.
- **Defaults.** A default that is served, by route 11 or to a first prompt, leaves out any weight the loaded release cannot rank, so a real release with fewer features does not refuse its own default.
- **The OpenAPI document** is published as `contracts/openapi.json` and is not served by the running service. An operation id is the name of its route. A route is named for its function, but for route 2: the route is `rank`, and its function is `rank_areas`, because it stands beside core's own `rank`.
- **Nothing is kept for a search.** The server holds no search between requests. The client holds the spec and sends it again to rank, to explain and to share. A spec names where someone works, and the only place one is stored is a share, which a person makes on purpose. This is why there is no search id, and no route that returns a search by id: such an id would sit in a URL, a URL reaches logs that Burro does not control, and for as long as the search was kept the id would unlock its destinations.
- **`share_id`** is 128 random bits, URL-safe. It is never derived from the spec, so holding a spec does not reveal a link.
- **Coarsening.** Unless `exact_destinations` is true, route 9 replaces each commute's `place_id` with its `coarse_place_id` before storing. If two commutes come to the same coarse place, the one with the lower `place_id` before coarsening is kept and the other is dropped. The stored spec therefore ranks a little differently from the search it came from, and `coarsened` says so: it is true only when a destination was in fact replaced or dropped.
- **A changed release.** A share outlives releases: route 10 re-ranks on the loaded release and sets `stale` when that differs from `original_release_id`. If the stored spec no longer passes `check_spec`, because a place, an area or a feature has gone, the answer is 410.
- **Stores.** `ShareStore` keeps a share in memory until restart. It is a protocol, and a stored share holds `share_id`, `spec`, `coarsened`, `original_release_id` and `created_at`, and nothing about who made it.

## 10. Privacy in the API

### 10.1 What may and may not be logged

| May be logged | Never logged, stored in an error report, or written to a table |
|---|---|
| Request id, method, **route template** (`/v1/shares/{share_id}`), status code, latency | The prompt, or any part of it |
| Release id, engine version | Text typed into place search |
| Interpreter name, model id, interpret status, `degraded` | A request or response body, whole or in part |
| Token counts | A `place_id`, a `destination_id`, a place name, a `fact_id` (a journey's holds a `place_id`) |
| The number of edits in each group, and of rejections by reason | A raw path, a query string, a `share_id` |
| Unmet categories and assumption codes | An exception's message |
| Error code, exception type, and the file, line and function of each frame | A header, the `Origin` among them, a cookie, an IP address |
| | The words an edit rests on, as a model copied them or as offsets into the text (`rests_on`, `words`) |
| | A spec, a hash of one, plain or under a key, or any other value worked out from one |

A `place_id` is an id from the release and not the user's words, but it says where someone works or where their child goes to school. It is kept only inside a stored share, and there it is the coarse place unless the sender chose otherwise.

**Nothing worked out from a spec is logged, or kept about a call.** A spec is stored in one place, a share, which a person makes on purpose (section 9.4). A spec is a small space, so its plain hash gives the spec back to anyone who can try specs: from one log line the README's example gave up its workplace, cap, budget and tag in 21 seconds. For a day the log held the hash under a key made at start-up instead. That could not be reversed, but it could confirm a guess: whoever read the log and could call the service posted guesses and watched for the same value in a new line, and had the workplace after 247 requests. Nothing needs to know that two calls were about the same search, so since 2026-09-23 there is no hash of a spec in a log line or a call record, of any kind, and no key: `logs.LOGGABLE` holds no field for one, `CallRecord` has none, and the service makes no HMAC. The plain hash is served in responses (routes 1, 2 and 10), to the client that holds the spec it is the hash of.

What a line can still say of a search is what it says of any: the status and the error code, how long it took, and on route 1 how many edits were made, how many were rejected for each reason, and the codes of what was assumed and of what could not be met. On routes 2, 3, 7 and 9 a test posts the spec that was searched and guesses at it, and asserts that every line and every record is the same but for its id. **On route 1 that is not so, and the line is not the same for every spec.** Its four fields `edits`, `rejections`, `unmet` and `assumptions` are worked out from the words and the spec together: "I work at Cindermoor Works" assumes a mode where the spec does not hold that place and nothing where it does, and "a bit cheaper" is rejected as `nothing_to_change` where the spec holds no amount. Each holds a count or a code from a closed list, and never an id, a name or a number of the spec; none can be matched to a spec without the words, which are in no line; and the call record of route 1 is the same for every spec. A test holds the line to exactly that (`test_what_a_line_says_of_a_reading_is_counts_and_codes_and_nothing_of_the_spec`). Whether even that is too much is an open point (section 13), and is the founder's to settle: the four are entries of `logs.LOGGABLE`.

How the rule is kept:

1. The server's own access log is switched off. One middleware writes the request line, from the route template.
2. The handler for validation errors builds `fields` from `loc` and `type` only. pydantic's `input`, `ctx` and `msg` are discarded, because they can repeat what was sent.
3. `log_failure(exc)` is the only way an exception is logged. It writes the type and the frames. It never calls `str(exc)`.
4. Logging is set up so that no third-party library logs below `WARNING`, whatever level the library sets on itself, and a library's line is cut down to where it came from.
5. Logging is a list of what may be written and not a scrubber of what may not. A line is an event name and named fields, a field that is not on the list cannot be logged, and no message is ever formatted. A failure is written at the level of an error.
6. Nothing is written to disk. The share store and the call log are in memory. The share store keeps the latest 50,000 and lets the oldest go.
7. No hash of a spec can be logged: no field on the list could hold one, and the routes work none out but the plain hash they serve. Nor can where an edit's words stand: `rests_on` and `words` are no fields of the list or of the call record, and the words a model copied are held in a field that no `repr` shows.
8. No response is a redirect, so no path is ever sent back in a header.

### 10.2 The call-metadata record

One record for each call to route 1 and route 3.

| Field | Type |
|---|---|
| `call_id`, `at` | UUID; timestamp, to the second |
| `endpoint`, `interpreter` | `interpret` or `explain`; `rule`, `claude` or `template` |
| `model` | the configured model id, or empty |
| `status` | `ok`, `clarify`, `off_topic`, `policy_redirect`, `timeout`, `capped`, `error` |
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
| `test_what_is_withheld_from_a_model_is_withheld_in_silence` | Rules 1, 2, 6 and 7 of section 8.2 at once, with the canary in the words and in the model's answer |
| `test_what_is_withheld_for_doubt_is_withheld_in_silence` | Rules 3 to 5: what was withheld, and why, is in no line |
| `test_an_answer_with_words_where_its_numbers_belong_is_not_logged` | Rule 9: the failure is logged by its type, and the answer is not |
| `test_a_stale_spec_is_put_right_without_the_place_being_named` | The place a spec is repaired of is in no log, whether or not the release has it |
| `test_the_words_an_edit_rests_on_are_returned_as_offsets_and_written_nowhere` | `rests_on` is in the response of route 1, for the reader and for a model, and the words are in no response, line or record |
| `test_where_the_words_stand_is_written_nowhere_when_a_model_fails`, `test_where_the_words_stand_is_written_nowhere_when_the_route_itself_fails` | The same on every failure path: a timeout, a cap, an error, an answer that quotes the person and does not fit the schema, a spec that is refused after the words were read, and a failure of the service |
| `test_no_other_route_takes_or_returns_where_the_words_stand`, `test_where_the_words_stand_cannot_be_logged_or_kept_about_a_call` | No other route takes or returns them, a share does not store them, and no log line or call record has a field for them |
| `test_what_a_line_says_of_a_reading_is_counts_and_codes_and_nothing_of_the_spec` | What differs in route 1's line when only the spec differs is four fields of counts and codes, and the call record does not differ |

## 11. What is deliberately left out

| Left out | How it attaches later, with no change to what is built now |
|---|---|
| Accounts and sign-in | A dependency that reads an identity from a header. No route here needs one, and no spec or share holds a user id |
| Shortlists | New routes over a new table of `user_id` and `area_id`. The area id is already immutable |
| Payments and entitlements | A check placed in front of routes 1 and 3. Those are the only routes that can cost money |
| Quotas, rate limits, bot checks | Middleware. A refused call to route 1 answers from the rule interpreter, never with a login wall |
| Streaming | Route 3 stays the snapshot and the source of truth. A streaming route re-emits the same verified sentences |
| A model-written explanation | A second `Explainer`. **`verify()` must be extended first, and no model explainer may be attached until it is.** `explain()` enforces it: it takes `TemplateExplainer` and refuses any other with a `TypeError` that names this row (section 7.5), so the check in `explain()` is changed in the same change that extends the verifier. As it stands `verify()` checks numbers and capitalised names, which is enough for fixed text and not for a sentence a model wrote (section 7.4, what the verifier does not check). Before a model's sentence is shown: (1) run `POLICY_LEXICON` and the group words of section 8.4 over it, and fail a sentence that says who lives somewhere; (2) widen the banned words into a list of words of safety and of judgement, "secure", "respectable", "desirable", "up and coming", "crime-ridden" and the like; (3) allow a model's sentence only the words that occur in the cited fact's label, slots and template, plus a short list of connectives, so that a name in lower case, a unit said of the wrong number and a comparison run the wrong way all fail for holding a word nothing allows; (4) turn the two tests that are marked as expected to fail, `test_a_sentence_about_residents_or_safety_is_rejected` and `test_a_name_in_lower_case_or_a_claim_about_residents_is_replaced`, into tests that pass |
| A run against the model provider | `claude_sdk.py` is built and selected when a key is present, but it has only ever met a stand-in. It waits for a key, and for the golden queries of the plan |
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

All run offline and the whole suite stays under 30 seconds. Section 10.3 adds the privacy tests. A generated test draws a fixed sample in `make ci`, the same sentences every time, and runs in full under the marker `full`: `make test ARGS="-m full"`.

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
| core | `test_inferred_crime_weight_is_rejected` | 5.3 rule 8 |
| core | `test_no_feature_or_tag_describes_residents` | A denylist of resident words against every id, label and definition |
| core | `test_invented_venue_or_changed_number_is_replaced_by_a_template` | The verifier, with a fake explainer that plants each |
| core | `test_every_template_passes_the_verifier` | 7.3 |
| core | `test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served` | 8.4 |
| core | `test_core_imports_nothing_that_does_io` | Purity |
| core | `test_every_fact_names_a_source_and_a_date` | 7.1, for every kind of fact, journeys and stations included |
| core | `test_a_time_that_is_not_known_is_none_and_never_zero` | 2.6 and 6.7 |
| core | `test_a_step_moves_the_number_unless_it_is_at_a_limit` | 5.2, with a buyer's budget at 50,000, where 5% rounds away |
| core | `test_release_with_a_changed_file_is_refused` | 2.8, `open_release` |
| core | `test_every_comparison_said_of_the_release_is_literally_true` | 7.3, on every feature and tag fact of the committed release |
| core | `test_what_a_person_says_decides_which_area_comes_first` | 5.2 and 5.3 rule 11, on the committed release: four wishes, four different areas first |
| core | `test_the_defaults_give_way_the_first_time_a_wish_is_applied` | 5.3 rule 11 |
| core | `test_switching_tenure_keeps_everything_the_person_set` | 5.3 rule 5 |
| core | `test_a_negated_wish_never_raises_a_weight` | 8.2, on the sentences the reviewers found |
| core | `test_a_sentence_that_was_read_backwards_raises_nothing`, `test_a_sentence_that_made_an_edit_nobody_asked_for_makes_none` | 8.2, on the 100 sentences an adversary found reversed after the second round of fixes and the 24 that made an edit nobody asked for, for a renter and a buyer |
| core | `test_a_word_that_is_not_known_beside_any_thing_or_name_makes_the_sentence_unread` | 8.2 rule 1, on a fixed sample of more than 3,500 sentences: every phrase of the lexicon and every name of the committed release beside a word the reader does not know, drawn from more than 600, in 40 places and with every mark. `test_every_word_that_is_not_known_in_every_place_makes_the_sentence_unread` is the whole of it, more than 40,000 sentences, and runs with `-m full` |
| core | `test_known_words_that_no_rule_accounts_for_leave_the_sentence_unread`, `test_a_word_that_turns_governs_the_first_thing_after_it_and_no_more` | 8.2 rules 5 and 6 |
| core | `test_a_token_is_never_split_at_a_mark_inside_it`, `test_a_name_is_never_put_together_across_a_mark_or_a_line_break`, `test_a_question_makes_no_edit`, `test_a_sentence_whose_subject_is_not_the_speaker_makes_no_edit`, `test_a_sentence_that_holds_doubt_and_names_nothing_takes_back_what_was_raised`, `test_a_number_that_is_a_minimum_is_never_a_cap`, `test_a_nuisance_that_is_liked_or_only_named_makes_no_edit` | 8.2 rules 3, 4, 7, 8 and 10 |
| core | `test_no_plain_word_can_turn_weaken_compare_question_or_reassign_a_wish`, `test_the_list_of_plain_words_is_short_and_is_reviewed_as_a_whole` | 8.2 rule 2: the vocabulary itself |
| core | `test_every_edit_says_which_words_of_the_text_it_rests_on`, `test_what_an_edit_rests_on_is_offsets_and_holds_no_word_of_the_text` | 8.1, `rests_on` |
| core | `test_a_generic_word_after_a_cue_for_a_place_names_no_place` | 8.2 |
| core | `test_a_plain_wish_for_each_thing_is_still_read`, `test_a_plain_journey_to_each_place_is_still_read`, `test_a_plain_area_rule_for_each_area_is_still_read` | That the closed vocabulary has not switched the reader off |
| core | `test_the_share_of_plain_wishes_that_is_read_does_not_fall_without_being_noticed`, `test_the_share_of_sentences_the_vocabulary_was_not_settled_on_is_held_too` | The price of 8.2, with a floor: 170 plain sentences and 60 held out (section 13) |
| core | `test_one_stated_wish_outweighs_everything_that_was_left_unsaid` | 4.1, for a renter and a buyer and every feature and tag |
| core | `test_a_default_the_person_took_off_stays_off_when_the_tenure_changes` | 5.1 and 5.3 rule 5 |
| core | `test_being_over_budget_is_never_given_as_a_reason`, `test_a_journey_over_its_cap_is_never_given_as_a_reason` | 7.5 |
| core | `test_a_trade_off_is_something_the_area_does_badly`, `test_there_is_no_trade_off_when_nothing_is_done_badly` | 7.5, on 60 searches of the committed release |
| core | `test_explain_takes_the_template_explainer_and_no_other` | 7.5 and 11 |
| core | `test_an_ordinary_word_that_begins_a_name_is_never_read_as_the_name` | 8.3 |
| core | `test_a_reason_is_something_the_area_does_well` | 7.5 |
| core | `test_exactly_half_the_weight_present_is_ranked_however_the_weight_is_split` | 6.6 |
| core | One test for each rule in 2.8 | `parse_release` |
| pipeline | `test_synthetic_release_rebuilds_byte_for_byte` | 2.9 |
| pipeline | `test_synthetic_names_are_not_real_places` | 2.9, against London's names and every name that was replaced |
| pipeline | `test_a_name_that_was_replaced_is_in_no_file_of_code_or_of_tests` | 2.9, in every file of `packages`, `services` and `tools`, the name of a constant included |
| pipeline | `test_a_place_that_was_given_a_new_name_kept_its_id` | 0 and 2.9: a new name moves no id |
| pipeline | `test_no_journey_is_shorter_than_two_minutes` | 2.9, on the committed release and on three other seeds |
| pipeline | `test_a_file_the_finder_leaves_behind_is_ignored` | 2.8 |
| pipeline | `test_every_other_stray_file_is_still_refused` | 2.8 |
| pipeline | `test_written_release_reads_back_the_same` | `write_release` and `read_release` agree |
| pipeline | `test_source_must_be_registered_for_the_use_its_file_needs` | 2.1, against the fixture registry: a routing source named in `catalogue.json` is refused |
| pipeline | `test_real_release_is_refused_without_a_registry` | 2.1 |
| api | `test_interpret_falls_back_to_rules_when_the_model_times_out` | 9.4 |
| api | `test_every_route_works_with_no_key_configured` | Form mode |
| api | `test_api_loads_the_committed_synthetic_release` | The two halves fit |
| api | `test_a_place_the_person_did_not_name_is_never_added_by_a_model` | 8.2, with a stand-in that names places of its own |
| api | `test_a_model_cannot_weight_crime_by_calling_a_loose_wish_stated` | 8.2 and 5.3 rule 8, whatever provenance the model gives |
| api | `test_a_models_edits_for_a_request_about_who_lives_somewhere_are_withheld` | 8.2 and 8.4, whether the lexicon or the model noticed |
| api | `test_an_edit_whose_words_are_not_in_the_text_as_typed_and_in_one_sentence_is_left_out`, `test_an_edit_whose_words_are_in_one_sentence_is_kept_and_says_where_they_stand` | 8.2 rule 1: words nobody typed, part of a word, another order, across a full stop, and what is left out of account |
| api | `test_a_name_is_never_put_together_from_words_that_do_not_stand_side_by_side`, `test_a_place_the_person_named_in_full_is_kept` | 8.2 rule 2: a name across a bracket, a line break, a slash, quotes, a hyphen and every other mark, a word that begins a name, and a name the model completed |
| api | `test_in_a_sentence_the_reader_knows_a_model_adds_nothing_to_what_the_reader_read`, `test_what_the_reader_read_too_is_kept_as_the_reader_put_it` | 8.2 rule 3: a wish read backwards, wishes nobody made, the tenure moved, a number ten times what was said, a journey removed by position, settings nobody asked for |
| api | `test_a_model_raises_nothing_in_a_sentence_that_holds_doubt`, `test_a_model_makes_nothing_of_a_thing_the_reader_knows_in_a_sentence_it_does_not`, `test_a_journey_a_budget_and_a_rule_are_read_by_the_reader_or_by_nobody`, `test_a_model_takes_nothing_away_in_words_that_hold_nothing_that_turns` | 8.2 rules 4 and 5, by hand |
| api | `test_no_sign_of_doubt_lets_a_model_raise_what_the_reader_does_not` | 8.2 rule 4, on a fixed sample of more than 600 sentences: every sign of doubt core holds, beside a feature, a tag, a place, an area and a campus, in one sentence and in two, with every edit resting on each part in turn. `test_every_sign_of_doubt_beside_every_thing_in_every_order_is_held_to_the_reader` is the whole of it, more than 40,000, and runs with `-m full` |
| api | `test_on_a_request_about_people_only_the_edits_the_reader_makes_are_applied` | 8.2 rule 6, in all six groups, with a stand-in that takes every chance |
| api | `test_crime_that_is_named_and_not_asked_for_is_never_weighted` | 8.2 rule 7 |
| api | `test_a_model_that_answers_off_topic_does_not_overrule_the_reader` | 8.2 rule 8 |
| api | `test_every_thing_asked_for_in_plain_words_is_still_read_through_a_model` | That the guard has not switched the model off: every phrase of the lexicon, every place and every area |
| api | `test_the_share_of_plain_wishes_read_through_a_model_does_not_fall_without_being_noticed`, `test_what_a_model_that_reads_backwards_gets_through_does_not_grow_without_being_noticed` | The price of 8.2 and what it buys, on core's own sentences, with a floor and a ceiling (section 13) |
| api | `test_a_wish_turned_round_in_words_core_does_not_list_is_not_raised` | What 8.2 cannot do, each expected to fail |
| api | `test_a_number_in_a_models_answer_must_be_a_number` | 8.2 rule 9, for every number of every edit |
| api | `test_where_the_words_stand_is_counted_in_the_text_as_it_was_sent`, `test_each_edit_says_which_words_of_the_text_it_rests_on` | 9.2: `rests_on` on route 1, with space before the text and characters two units long in it |
| api | `test_a_spec_that_has_gone_stale_can_be_put_right_by_an_edit` | 9.4 and 5.3 rule 6, over HTTP |
| api | `test_a_path_with_a_slash_too_many_is_no_route_and_is_never_redirected` | 9.2 |
| api | `test_a_number_must_be_sent_as_a_number` | 9.1, for every number in every body |
| api | `test_an_origin_on_the_list_is_allowed`, `test_an_origin_off_the_list_is_not` | 9.1, on every route and every kind of refusal |
| api | `test_a_call_record_older_than_thirty_days_is_gone_after_the_next_add`, `test_a_record_out_of_the_order_of_time_is_gone_when_it_is_too_old` | 10.2 |
| api | `test_an_origin_that_no_browser_would_send_is_refused_when_the_service_starts` | 9.1 |
| api | `test_an_operation_is_named_for_its_route` | 9.4 |
| api | `test_a_file_the_finder_leaves_behind_does_not_stop_the_service` | 2.8 |

## 13. Open points

These are first guesses. Each is a constant or a table row, so changing one is a small diff and an engine or catalogue version bump.

| Point | Status |
|---|---|
| The decay constants of 6.3 and `BUDGET_OVER_SHARE` | Chosen by judgement. To be tuned on real travel times and with testers |
| Tag weights in 3.2 and default weights in 4.1 | Chosen by judgement. Tags are unvalidated until the 40-neighbourhood sanity set exists; one that fails it is dropped |
| `university_proximity` from `dfe-gias` | Assumes that register lists university sites. If not, the feature needs its own registered source |
| `university_proximity` has one direction | Settled, 2026-09-23: it keeps one direction. A person may ask to be near a campus and not to be far from one, because the second is a way to ask for fewer students. The rules now refuse it in words (section 8.4), where before they read "far" as a word of degree and turned the tag up |
| The attainment features | They describe a school's results, which the plan allows, and not residents. They are also the features most likely to stand in for who lives nearby, so the proxy audit should take them first |
| Nurseries in `family_amenities` | ADR 0006 names them. No registered source provides them, so the formula leaves them out |
| Places of worship and specialist shops | ADR 0006 meets community requests through these. No v1 feature covers them, so such requests are reported as unmet |
| Anti-social behaviour and listed-building density | Left out to keep the catalogue near 20. Both have approved sources and can be added. The registry asks that conservation areas be combined with listed-building density and pre-1919 homes. This contract combines them with pre-1919 homes only, and relies on the coverage rule to stop them deciding a tag alone. Whether that meets the condition is the founder's call |
| Gated sources in 3.1 | `dfe-school-performance-tables` is gated today, so the gate will not let it be read for scoring. Its two features are left out of a real release until it is approved (section 2.3), and `family_amenities` is worked out from the other three quarters of its formula |
| Figures from sources registered for scoring only | The food, venue, culture and conservation features come from sources registered for `scoring` and not for `display`, yet their values are printed in sentences. This contract asks for `scoring`. If printing a derived figure counts as display, the registry entries need that use added, with evidence, before a real release |
| A `place_id` in a stored share | No search is stored (section 9.4). A share is, as ADR 0005 provides, and it holds exact places only when the sender asks. ADR 0005 speaks of destination strings; an id is not a string, but it is as revealing. Whether an exact share may reach a database is to be settled before the database arrives |
| The spec hash in logs | Settled twice on 2026-09-23. First the plain hash gave way to the hash under a key made at start-up. Then a checker showed that the keyed hash confirms a guess for whoever reads the log and can call the service, and nothing was found that needs to know two calls were about one search. So nothing worked out from a spec is logged, or kept about a call, at all (section 10.1, ADR 0005 and 0011). **Still open:** the plan names the spec hash among the columns of `llm_calls`; there is no such column. And what route 1's line still says of a reading, the counts of edits and of rejections by reason and the codes of what was assumed and of what could not be met, depends on the spec as well as on the words: an adversary showed that the same words leave a different line when only the spec differs. None names a place, none holds a number of the spec, and none can be matched to a spec without the words, which are in no line (section 10.1, and a test holds the line to it). It is not the letter of "nothing worked out from a spec". To meet the letter, take `edits`, `rejections`, `unmet` and `assumptions` out of `LOGGABLE`, and lose what they tell of how well the readers read; or say in AGENTS.md rule 9 and ADR 0011 that a count which depends on the words and the spec together may be logged. **It is the founder's call, and neither was done** |
| Long caps and the cutoff | A cap may not exceed the release's cutoff (section 6.1), and a journey beyond the cutoff scores 0 although the curve runs on to one and a half times the cap (6.3). Both go away if a real release routes to a cutoff of one and a half times the longest cap, which is a cost to weigh when routing is built |
| Logging the edits a prompt produced | ADR 0005 allows it. This contract logs only their counts, which is stricter, because a commute edit names a place |
| What a plain mention is worth | Settled, 2026-09-23: a mention is worth 0.50 and the defaults give way to a quarter, rounded down to a step, once a wish is applied (sections 4.1, 5.2 and 5.3). One thing said is 0.50 against 0.35 left unsaid for a renter and 0.45 for a buyer. Measured on the committed synthetic release with a renter's first prompt: "leafy and quiet" puts Alderwick first, the leafiest and the quietest area; "somewhere buzzy with bars and restaurants" Pellam Cross, the centre; "good schools and a park for the kids" Dulcimer Green, whose schools have the best results; "by the river" Sable Reach, which has more of its land by the water than any other, where a third left Brackenhythe first. **Still open:** to outweigh in weight is not always to come first. For a buyer "by the river" still puts Brackenhythe first and Sable Reach second, and "leafy" alone puts Brackenhythe first for both, with Alderwick, the leafiest, second or third: Brackenhythe is fourth of 22 for leafiness and does best on what was left unsaid. If a single wish should always put the best area for it first, the defaults must give way to nothing, which is a different product. **Also open:** the quarter is rounded down, which the decision did not say. To the nearest step it would leave 0.55 and 0.60 unsaid and defeat its purpose |
| A default that was removed comes back | Settled, 2026-09-23: what a person takes off leaves an entry of 0 behind, in their name, where a tenure has a default for the feature, and a change of tenure leaves it off (sections 5.1 and 5.3 rule 5). `canonical()` goes on dropping it. **Still open:** a client sees the entry on the wire, a weight of 0 with a provenance, and must show it as off and not as a wish. And what was never in the spec was never taken off: a renter who says "I don't care about green space" and then switches to buying gets the buyer's default for green cover |
| A first prompt that says "buy" | Settled, 2026-09-23: changing tenure resets what nobody chose to the new tenure's default and keeps what the person set (section 5.3 rule 5). Route 1 still edits the renter's default when no spec is sent, and "buying a flat near a park" now ends with the buyer's defaults |
| Finding a place from part of a word | Settled for resolving, 2026-09-23: `search_places` and `resolve_place` have parted ways (section 8.3). Part of a word is offered by a search and asked about by a resolver, and never taken. Still open for searching: a place matches from the start of its name, or on whole words, so "univ" alone finds nothing. A weaker score for words that begin a word of the name would help a search box |
| A name after "near" | After "near", "not", "avoid" and "only" only the whole of a name or an alias is taken (section 8.2). "Near Pellam" adds no journey and asks nothing, where "work at Pellam" asks which. "Near Alderwick" adds none either if no place has that name, though an area does: a journey ends at a place, and an area's centre is not one |
| Names in lower case, and what a sentence asserts | The verifier finds a name by its capital and a verdict by a list of words (section 7.4). Enough for the templates, and not for a model: section 11 says what must be added first, and `explain()` refuses a second explainer until it is. Closed on 2026-09-23: a number word that is misspelt or run together, a word for nothing, a unit said with an article, a length of time, a Roman numeral in lower case, a banned word in any form it takes, and one written with a letter of another alphabet, an accent or a zero-width character. **Still open:** a name in lower case, a claim about residents, a number said of the wrong thing, a comparison run the wrong way, and a banned word spelt with spaces between its letters |
| Counting the areas compared | `facts_for` counts the areas strictly beyond one, for each feature and tag, each time it is called: 35 passes over the areas of the release. It is nothing for 24 areas. For a real release the counts belong in the release, worked out once by the pipeline beside the percentile |
| The plan says the percentile is the explanation | PLAN section 8 says "quieter than 80% of London" is both the score and the explanation. Since 2026-09-23 it is the score only. The sentence states the share strictly beyond, which is lower wherever areas tie |
| A journey in a comparison for an area that was filtered | The cell is empty (section 9.2). Showing the journey that broke the cap needs `rank()` to report legs for a filtered area, or core to offer them apart from ranking |
| Names are normalised on every request | Each interpreter builds `Names` from the release it is handed: 0.2 ms for 44 places, and it grows with the place index. A real index of tens of thousands needs it built once |
| A journey of 0 minutes | Settled for the synthetic release, 2026-09-23: no time in it is under 2 minutes (section 2.9). It held one of 0, from Cindermoor to Cindermoor Works, and two walks of 1. It is still a valid time to core (section 2.6). **Still open:** a real roll-up needs the same floor in its own pipeline step, and whether 2 is right for it is to be settled on real journeys |
| Whether every made-up name is made up | Not known. Eight names of the city and nine of the tests' own releases were real and have been replaced (section 2.9). On 2026-09-23 all 102 names were looked up in one encyclopaedia, by title and by phrase. **No gazetteer was consulted**, so a small street, a farm or a hamlet that the encyclopaedia does not cover would not have been found, and the replacements were checked the same way and no better. Two of the five replacements in the city rest on partial evidence (Kilnside, Withyford). Three names could not be settled and are the ones to check first: Alderwick, which may be a street in Hounslow, Foxholt, which may be a street in north-west London or a hamlet in Kent, and the test name "A Hundred Acres", which may be a hamlet in Hampshire and has been replaced to be safe. To settle it, someone with a gazetteer of Britain checks every name in `names.py` once, replaces any that is real with a name that sorts where it did, and adds the old one to the test's list. A canary in the pipeline's tests, which reaches no release, still begins with the name of a real place in California |
| What the rule-based reader no longer reads | Decided, 2026-09-23, third round: it reads a sentence only when it knows every token in it (section 8.2). **The price, measured.** Of 170 plain positive sentences, 90 of them an adversary's own, the reader read 145 in full before, 85.3%, and reads 142, 83.5%; of the adversary's 90 it read 70 and reads 69. Those were used to settle the vocabulary, so the fairer measure is 60 sentences that were written afterwards and never used to widen it: 55 read before, 91.7%, and 46 now, 76.7%. Both have a floor in `tests/test_vocabulary.py`. What is declined now that was read before: a wish beside a word the reader does not know, anywhere between two full stops ("a lively high street with plenty going on", "nice cafes and a decent bakery", "I work from home so I want somewhere quiet"); another person's wish or workplace ("my partner works at Pellam Infirmary", "the kids need a playground"); a question ("could you find me somewhere with good pubs?"); a wish after a sentence that holds doubt and names nothing, where it is only named ("Moving next month. Somewhere leafy."); a wish listed after a turned one ("leafy, no pubs, quiet" reads no "quiet"); "far more", "a few" and "walking distance of" where a word beside them is not known; a nuisance that is only named ("noise"); and part of a name after "work at", which is asked about and no longer taken. What is still declined as before: a double negative, a comparison ("quieter than where I live now") and a condition ("happy anywhere as long as"). A word that is missing costs one wish and never reverses one, and `vocabulary.PLAIN` is where to add it |
| The signs of doubt are a list | Settled, 2026-09-23: the reader no longer reads by one. It reads by the list of what it knows, which is short and can be whole, and a word that is missing from it costs a wish that is not read. `WORDS_OF_DOUBT` is kept for two callers that do not read by it: the test that no plain word is one, and the model-backed reader. What is known to get through the closed vocabulary: a statement of where the person lives now, read as a wish ("I live near a station"); a word with two meanings of which the reader knows one ("flat" as level ground, "rent" as what is paid today); irony with no mark on it ("I just love pubs" is unread for "just", "I love pubs" said in scorn is read); and a sentence that holds doubt, names nothing and stands two sentences away from a wish in which the speaker says what they want |
| The API and a `.DS_Store` | Settled, 2026-09-23: `load_release` leaves it out as `read_release` does (section 2.8), so the service starts on any folder that `burro-release check` passes |
| `HEAD` and `If-None-Match` | A `HEAD` is answered 405 and a conditional `GET` in full. Each is a line of configuration |
| The origins a browser may call from | Settled, 2026-09-23: a list in a setting, `http://localhost:3000` by default, and nowhere else, each entry held to what a browser sends (section 9.1). **Still open:** the web app's real address, which goes in `BURRO_ALLOWED_ORIGINS` where the service is deployed. A deployment that sets nothing allows only a page on the visitor's own machine, which is safe and is not useful |
| A request about people that nobody notices | The rules of section 8.2 hold whatever a model answers, but the sixth needs the request to be noticed, by the lexicon or by the model. One that both miss can still be turned into a tag by a model, with no notice, where the sentence names the tag in no phrase of the lexicon and holds no doubt. It can no longer be turned into a rule about an area, a journey or a budget, which are the reader's alone. A wider lexicon narrows it and cannot close it. It is for the golden queries to measure before a key is set |
| What a model's reading loses when part of a request is about people | What is applied is then the rules' own edits, and only those the model made too, so a wish in the rest of the request that only the model could read, "a proper brunch", is withheld, a degree that only the model read ("much more") is the rules', and the notice still says the rest was applied. It is the cost of not taking the model's word for which part was which |
| Where the words stand, in code points | `rests_on` counts code points, as core counts them, and the API serves core's record as it is (section 9.2). A client in JavaScript counts UTF-16 units, and the two differ after any character that is two units long. It is said in the contract and in the OpenAPI description of `RestsOn`, and nothing enforces it: a client that slices the string directly marks the wrong words after an emoji. If that proves a trap, the API can serve UTF-16 units instead, which is a change to one function in `routes/interpret.py` and to this contract |
| What the model-backed reader no longer reads | Decided, 2026-09-23, third round: from a model's answer the code keeps only what it can justify by the words each edit rests on and by what the reader made of their sentence (section 8.2). The rule that a doubt anywhere in the request silenced the model is gone: the doubt of one sentence is no doubt about the next. **The price, measured** with a stand-in that reads every plain sentence as it is meant, on core's own sentences. Of the 170 plain sentences the reader alone reads 142 in full and a model through the guard 152; of the 60 that were held out, 46 and 53. So a model adds 17 of 230, all of them wishes in words the reader has no phrase for: "somewhere I can walk the dog", "a place with a real buzz", "lots to do in the evenings". With rule 4 held to the letter of the decision, so that a model is believed in any sentence the reader does not know that holds no listed doubt, it would add 28, and a model that reads backwards would get an edit applied in 52 of the adversary's 124 sentences and not in one. What is declined through a model that a careful model had right: a journey, a budget or a rule about an area in any sentence the reader does not know ("we both work in Pellam Cross", "easy commute to Pellam Cross", "my partner and I are after a two bed"); a wish for a thing the reader knows by that word, beside a word it does not ("a garden would be nice, and a park nearby", "primary schools with good results", "I want it all: parks, pubs and a station"); any wish in a sentence that holds a word that turns or a word of the written list of doubt ("I can't live without a park", "quieter than where I live now", "ideally near a park"); a question ("could you find me somewhere with good pubs?"); a wish beside a sentence that holds doubt and names nothing; anything the reader did not read in a sentence it knows ("somewhere for the kids", "I need to get to Cindermoor Works in under 40 minutes"); a name the model corrected or swapped for another name of the same place; a journey's minutes, mode and strictness and a wish's degree, which are the reader's; and a journey changed, as opposed to removed, in words. Each is reported as `other` in `unmet`, and the controls are on the screen. Both figures have a floor in `tests/test_claude_kept.py`. **Still open:** rules 3, 4 and 5 of section 8.2 go further than the decision's letter, for the reason measured above. To go back to the letter is one change in `claude.py`: let `mine` keep a raise of a thing the sentence names, and a journey or a budget, where the sentence holds no doubt. **Found in core while this was built, and not changed here:** `sentences_of` hears "we're" as the past tense "were", because it tests a token without its apostrophe against the written list of doubt, so a wish that only a model reads is withheld wherever the sentence begins "We're"; and it marks no sentence `taken_back` that the reader could not have read a wish in, so the guard asks the reader about the neighbours of such a sentence itself |
| A doubt that stands after a list | Closed in core, 2026-09-23 (section 8.2 rule 7): a sentence that holds doubt and names nothing takes back what the sentence before it raised, and what is listed beside it. "A park or a playground? No thanks", "leafy, quiet. Not really", "near Pellam Infirmary or Foxholt Market is not for me" and "I work at Pellam Cross or Wexmoor University? No" make no edit |
| A turned wish with no sign of doubt in it | Narrowed, 2026-09-23. "A park would be a mistake", "Pubs, yuck" and "I dinnae want pubs" hold nothing core lists as doubt, and a model that raised the park or the pubs there was believed. It is believed no longer: the sentence names the thing in a word the reader knows, and the reader could not read what was said of it (section 8.2 rule 4). What is left is a thing in words the reader has no phrase for, turned round in words core does not list: "boozers on every corner would finish me off". A model that raises the thing there is believed, and the edit is shown as an assumption with the words it rests on. To close it the model path would have to keep a raise only where the reader makes it too, which would leave a model nothing to read |
| A name the model corrected | A model that puts right a name the person misspelt, or writes another name of the same place, has supplied a name, and the edit is left out with `other` in `unmet`. A model that copies the misspelling, as it is told to, leads to a question with options only where the reader asks it too, after words that expect a place: "I work at Pelam". Anywhere else it is left out. **Also open:** a model that copies the words an edit rests on with a letter changed, a comma dropped or a word left out loses the edit, whatever it read. How often a real model does that is for the golden queries to measure before a key is set; the match can be loosened in `_Text.find`, and every loosening is a way to rest an edit on words nobody typed |
