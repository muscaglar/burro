# London data pipeline and evidence store

Status: design, 2026-09-23. Nothing here is built. It changes no code, no registry file and no other document. It applies [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md), [ADR 0008](../adr/0008-package-sources.md) and sections 2 and 7 of [the contract](contract.md). Nothing was downloaded and nothing was measured. Every size, time and price below is marked **read** (on a page, today), **repo** (already recorded in the registry or the research) or **estimate** (worked out here, with the sum shown). Section 16 lists what was read and what is unverified.

[The plan for real data](london-data.md) and [ADR 0015](../adr/0015-where-builds-run-and-what-gates-a-launch.md) have since chosen hosted CI for fetch. Where this document recommends another place, they stand.

Files have been fetched since, and the geography, the first measures and a preview were built from them. The plan says what was fetched, and that nothing of it is published. Section 5 names the methods that were added with the builds, each under its date.

## 0. What is assumed of the other parts

| Part | Assumed here |
|---|---|
| Neighbourhood map | It delivers one reviewed CSV, `oa21cd,area_id`, that names every London output area once. About 450 areas. This design builds polygons and every crosswalk from it |
| Sources and measures | Another part chooses them. This design says how any registered source becomes a figure. Sizing uses 45 measures and 14 vibes ([vibes.md](vibes.md)) |
| Travel times | Another part chooses the routing tool and its settings. Here it is one step with stated inputs and outputs: 4,994 origins, about 16,700 destinations, four matrices (repo) |
| Research with a model | Another part designs the prompts and the providers. Here: where its output enters, and the check it must pass |
| Census on the area page | Another part designs the page and the registry entries. Here: where the tables are kept. The registry is assumed to gain a dimension for resident tables whose only product use is `display` |
| Registry | It stays the only list of sources. No step reads a source the gate has not passed |

## 1. In short

| Question | Answer |
|---|---|
| What stands behind a figure | A row in the evidence store: the measure, the area, the publisher's files by hash, the period of the data, the date retrieved, the method, and how much of the area the data covered |
| What stands behind a sentence found with a model | A claim: the page as code fetched it, by hash, and the words it rests on, found in that page as written. No match, no claim |
| How a build repeats | A lock file names every input by hash, the code by commit and the packages by lockfile. The build reads no clock and no network. Hosted CI builds twice and compares bytes |
| Where things are kept | Raw files and working tables in a private object store. Receipts, locks and reports in git. The release in the object store, fetched by the API at deploy |
| Where a build runs | Fetch on a machine that a person runs. The build of record in hosted CI, by hand, from the private store. A rented machine only if routing does not fit |
| What it costs | Under GBP 1 a month for storage. GBP 0 for CI. GBP 0 to 12 a build for routing. Research with a model is capped by an input and is not estimated here |
| How long | 1 to 2.5 hours without routing, on 4 processors (estimate). Routing adds 5 to 15 processor-hours (repo estimate, unmeasured) |
| What blocks it | The output area CSV, a committed lockfile, a build host that can reach the publishers, and a contract change for three new files |

## 2. The stores

| Store | Holds | Format | Where | Who may read | Size |
|---|---|---|---|---|---|
| Vault | Every publisher's file, as fetched, never changed | The publisher's own bytes, under `raw/<source_id>/<sha256>/<file name>` | Private object store. A second copy on a machine that a person runs | The build, by source | 10 to 25 GB at first fetch (estimate, section 10) |
| Receipts and locks | One receipt per fetched file. One lock per build | JSON, a few hundred bytes to 200 kB | Git, `data/receipts/` and `data/locks/`. They hold addresses, hashes and dates, and no data | Anyone | Under 1 MB a release |
| Staging | One table per publisher's file: London rows only, allowed columns only | Parquet, under `staging/<step>/<hash of inputs and code>/` | Build host and vault. Never public | The build | 1 to 3 GB (estimate) |
| Build evidence | Row counts at each step, per-unit detail, the fine travel matrices, the log | Parquet, `uint8` arrays, text | Vault, `builds/<release_id>/` | The founder | 0.5 to 1 GB. The matrices are 4 × 83 MB (repo) |
| Release | What the API serves, with `evidence.json` and `coverage.json` | As contract section 2 | Vault, `releases/<release_id>/` | The API | About 60 MB (estimate, section 10) |
| Residents | Census tables for display, as shares | JSON, its own folder and manifest | Its own prefix, its own key | The area page route | About 1.5 MB (estimate) |
| Audit | Protected tables, for the proxy audit | Parquet | A third prefix and key. No build can read it | The audit alone | Under 1 GB (estimate) |

- A file in the vault is addressed by its hash and is never overwritten. A publisher that reissues a file makes a second file.
- Nothing from the vault or staging is ever a CI artifact, a CI cache entry or a release asset. GitHub says of caches: "Anyone who can open a pull request against your repository can read the contents of caches in the base branch" (read).
- A source can be purged. Some licences end on breach or on notice (TfL, Network Rail: repo). `burro-build purge <source_id>` deletes its raw and staging files and lists every release that cites it.

## 3. The steps, in order

One command, `burro-build`, with one sub-command per step. No orchestrator. A step declares its inputs and outputs, and is skipped when an output for the same input hashes and code already exists.

| # | Step | Reads | Writes | Network | Stops when |
|---|---|---|---|---|---|
| 1 | `plan` | Registry, `build/sources.toml` (which sources and editions this release uses) | The fetch list | No | `Registry.require(id, use)` refuses a source |
| 2 | `fetch` | The fetch list | Raw files, receipts | Yes. The only step that has it | A download fails, or a by-hand file is missing |
| 3 | `seal` | Receipts, the vault's listing | `lock.json` | The vault only | A receipt names a file the vault lacks, or licence evidence named by a registry condition is not in `registry/evidence/` |
| 4 | `normalise` | Raw files | Staging tables, counts of rows in and out, columns dropped | No | A column the step expects is missing, or a column on the deny list is present after the step |
| 5 | `cells` | ONS boundaries and lookups, the output area CSV | The `cell` table, crosswalks with weights, area polygons, destinations | No | An output area is in no area or in two |
| 6 | `network` | OS Open Roads | The walk graph. Never OpenStreetMap (ADR 0004) | No | Over 1% of output area centres are more than 250 m from the graph |
| 7 | `derive` | Staging, cells, walk graph | One value, coverage and evidence row per area and measure | No | A measure has no registered method |
| 8 | `travel` | Timetables, street network | Fine matrices, then the roll-up to area by destination | No. The tool runs in a pinned container | The other part's checks |
| 9 | `cost`, `places`, `stations` | Staging, cells | The rows of `cost.json`, `places.json`, `stations.json` | No | A postcode-level row is in an output |
| 10 | `residents` | Resident tables only | The residents artefact | No | It was handed any other input |
| 11 | `claims` | A bundle of claims and its pages, by hash | Checked claims | No. The pages are in the vault | Never stops. It drops what does not check out, and counts it |
| 12 | `assemble` | Steps 5 to 9 and 11 | The release, through `write_release` | No | The licence gate, or any rule of `open_release` |
| 13 | `check` | The release, the last release, validation sources | The check report | No | Any gate of section 8 |
| 14 | `report` | The release, the evidence | Coverage report, diff report, attributions | No | |
| 15 | `publish` | The release | The release in the vault. A setting names the release the API serves | The vault only | The founder has not approved the reports |

A step's inputs are copied from the vault before it starts, and each is hashed against the lock. Its outputs are copied back when it ends. The step itself runs with sockets refused. Step 4 runs one source at a time, so the largest source sets the disk a build needs: 5.3 GB (repo). Percentiles and vibes are worked out in step 7 by `percentile_of()` and `tag_raw()` in core, as the contract says. The pipeline holds no second copy of the arithmetic.

## 4. The evidence record

Four records. The first three stand behind every figure. The fourth stands behind a sentence or a name that a model helped to find. Every example value is made up.

### 4.1 The receipt: one per publisher's file

| Field | Example | Notes |
|---|---|---|
| `file_id` | `f-3b1c9a0e52d4` | The first 12 hex digits of the hash |
| `source_id`, `use` | `os-open-greenspace`, `scoring` | The registry id, and the use the gate was asked for |
| `publisher_file` | The file's name as the publisher gave it | For a zip, also the name and hash of each member that is read |
| `url` | The address after redirects | Any key or token is removed before it is stored |
| `listed_url` | The address the list gave | Before any redirect, and as clean as `url`. Left out where the list gave none |
| `sha256`, `bytes` | | Of the file as fetched |
| `retrieved_at` | `2026-10-04T09:12:31Z` | From the fetch, never from the build |
| `how` | `fetched` or `by_hand` | A page that code cannot fetch is saved by a person |
| `edition` | The publisher's own label | A version, a release month, a reference number |
| `edition_from` | `{"where": "xml_header", "at": "Header/ExtractDate", "period_too": true}` | Added on 2026-09-24. Where the edition was read, when no page of the publisher states one: in the file as it arrived, or nowhere, and then the edition is the day it was retrieved. Left out where a page stated the edition. A day that is about the file and not about its data is never the period |
| `data_period` | `{"as_at": "2025-03-31"}` or `{"start": "2023-08", "end": "2026-07"}` | The period the data describes, in the publisher's terms |
| `geography` | `oa21`, `lsoa21`, `lsoa11`, `msoa21`, `msoa11`, `lad`, `postcode`, `point`, `grid_1km`, `polygon`, `line` | Read from the file, never assumed |
| `licence_evidence` | A path under `registry/evidence/` | Required where a registry condition asks for a saved copy |

An answer from an API is saved as a file and receipted the same way. Bulk files are preferred, so that a build repeats.

### 4.2 The method: one per way of working a figure out

| Field | Example |
|---|---|
| `derivation_id` | `lsoa_to_area_by_homes@1`. The number rises when the arithmetic changes |
| `sentence` | One sentence for the methods page, with every parameter in it |
| `kind` | `measured`, `modelled` or `averaged`, as [vibes.md](vibes.md) promise 2 asks |
| `parameters` | Distances, thresholds, windows |
| `code` | The module, and the commit the lock names |

### 4.3 The evidence row: one per figure

Its key is the `fact_id` of contract 7.1, so a fact and its evidence cannot part.

| Field | Example | Notes |
|---|---|---|
| `fact_id` | `lon-n0042/feature/homes_pre1919` | |
| `derivation_id` | `lsoa_to_area_by_homes@1` | |
| `inputs` | `["f-3b1c9a0e52d4", "f-77aa01c2e9b3"]` | Every file the figure was worked out from, the crosswalk and the weights included |
| `data_period`, `retrieved_on` | | The span of the inputs, and the latest date any was retrieved |
| `units_used`, `units_expected` | 11, 11 | How many of the source's units the area takes in |
| `weight_covered` | 0.97 | The share of the area's homes, or land, that had data |
| `state` | `partial` | Section 7 |
| `flags` | `rounded_in_source`, `suppressed_in_source`, `unit_split` | What a reader of the figure should know |

To keep it small, `evidence.json` holds two lists. `measures` holds what is the same for every area: the method, the inputs, the period. `rows` holds what differs: units, weight covered, state, flags. At 450 areas that is about 33,000 rows and 4 MB (estimate: 20,250 features, 6,300 vibes, 4,500 costs, 2,000 others, at 120 bytes).

### 4.4 The claim: one per thing a model helped to find

| Field | Notes |
|---|---|
| `claim_id`, `area_id`, `kind` | The kinds are for the research part to name |
| `text` | What would be shown or stored |
| `source_id` | A registered source, approved for the use the claim is put to |
| `page` | The `file_id` of the page, fetched by code and held in the vault |
| `quote`, `start`, `end` | The words the claim rests on, and where they stand in the page's text |
| `found_by` | Provider, model and the hash of the prompt. It records how the claim was found. It is never a source |
| `status` | `kept`, or `dropped` with a reason code |

The check is code and has four parts. The page is one that code fetched. Its host belongs to a registered source. The quote is in the page as written, after white space is made regular. A number in the text is a number in the quote. A claim that fails any part is dropped and counted. A model's answer differs from run to run, so the bundle of claims is itself an input, held by hash. A rebuild runs the check again and never the model. No claim may describe residents, and no resident table is ever sent to a model.

### 4.5 From the store to the screen

| Where | What it carries |
|---|---|
| `manifest.sources` | As today, with `retrieved_on`. Gains `files`: each `file_id`, name, hash, edition and period |
| A catalogue row | Gains `derivation_id` |
| A `Fact` | `sources` and `as_of` as today. Gains `evidence`: the method's sentence, the dates retrieved, and the weight covered |
| The area page | A "Sources" line for every figure: publisher, dataset, period, date retrieved, how it was worked out, how much of the area it covers |
| The methods page | Every method's sentence, and every file of the release with its hash |

## 5. From a file at another geography to a figure for an area

Every area is a set of output areas. Every method below goes through output areas, so a boundary change needs no new data. "Homes" are households in each output area, from the approved housing tables, which count homes and describe nobody.

| The file is by | Method | How | Coverage is | Said on the methods page as |
|---|---|---|---|---|
| Output area, a count | `oa_sum` | Add the area's output areas | Output areas with a row | "The sum of {n} census output areas" |
| LSOA or MSOA, a count | `lsoa_to_area_by_homes` | Split each unit between the areas it touches, by where its homes are. Then add | Share of the area's homes in units with a value | "From {n} small areas, shared out by where homes are" |
| LSOA or MSOA, a rate or a share | `lsoa_ratio_by_homes` | Split the top and the bottom of the fraction as above, add each, then divide. A mean of rates is never taken | The same | The same, with the denominator's source named |
| The area itself, two counts. Added on 2026-09-24, after the first build | `area_row_ratio` | One count of the publisher's own row for the area over another. Nothing is added up. It is for a file that holds a row for the area, as the council tax tables do while an area is an MSOA: the row is rounded once, where a sum of smaller areas takes in one rounding for each | The share of the area's homes that the bottom counts | "The publisher's own count for the area" |
| Points | `points_near_homes` | From each output area's population-weighted centre, count the points within a walk on the walk graph. Average by homes | Homes whose centre is on the graph | "Places within a {d}-minute walk of homes" |
| Points, nearest one | `walk_to_nearest` | The shortest walk from each centre. The median by homes | The same | "The walk from homes to the nearest {kind}" |
| Points, nearest one, while no walk graph is built. Added on 2026-09-24, with the first park measures | `straight_line_to_nearest` | The distance in a straight line from each centre to the nearest point. The median by homes: where the homes divide exactly in half between two distances, the mean of the two. It is no walk, so a measure that uses it says so in its name, and is not given the name of a walk | Homes whose nearest point is known: where land that no file was read for is nearer than the nearest point found, it is not | "The distance in a straight line from homes to the nearest {kind}" |
| Polygons or lines | `homes_within` | The share of homes whose centre is within {d} m, in a straight line. Built on 2026-09-24, with the measure of main roads: the distance is part of the id of the method, as `homes_within_100m@1`, because the evidence of a release holds one method under one id and two measures may use two distances | Homes in output areas the source covers: those with a centre, inside what the file says it covers. One with no verdict is never taken to be far | "The share of homes within {d} m of {kind}" |
| A 1 km grid | `grid_at_homes` | The grid value at each centre. Average by homes. Marked `modelled` | Homes on a cell with a value | "A modelled value on a 1 km grid, read where homes are" |
| Postcode rows | `postcode_to_area` | Postcode to output area by the postcode directory of the same quarter. Summarise by area. No row below an area is kept | Rows that matched | "From {n} sales in this area", never a postcode |
| Postcode district | `district_to_area_by_homes` | A model input only. Marked `modelled` | Homes in districts with a value | The model's own sentence |
| Borough | `borough_as_prior` | A model input only. Never printed as the area's own figure | | The model's own sentence |
| Origin by destination times | `travel_rollup` | The median over the area's origins, weighted by homes | Origins with a time | The routing part's sentence |

- A figure published for a larger area than the one shown is never pasted onto it. A borough holds about 14 areas (repo).
- The geography of a file is read from the file. The police data's page does not say which census its LSOA codes follow (read). Where a file uses 2011 codes, a registered lookup is needed, or the file's own coordinates are used.
- An area that the source does not cover is unknown and never zero. Below half the homes covered, the value is null (contract section 2).
- A count rounded or withheld by the publisher stays so, and carries its flag.
- Every crosswalk is a file in the vault with its own `file_id`, so a figure cites the boundaries it was built on.

## 6. How a build repeats

| Rule | Detail |
|---|---|
| Inputs by hash | `lock.json` lists every `file_id`, the claim bundle, the output area CSV, and the output of every outside tool |
| Code by commit | The lock names the commit. A build from a tree with changes is refused |
| Packages by lockfile | `uv sync --locked`. This needs the four steps of ADR 0008 done first |
| No clock, no chance, no network | `built_at` and `release_id` are inputs. Nothing is drawn at random. Steps 4 to 14 run with sockets refused, as the tests do |
| Order | Every loop is over a sorted list. Sums use `math.fsum`. Floats are rounded to 6 decimals at writing (contract section 0) |
| One platform of record | Linux on x86-64, one pinned Python 3.13. A build elsewhere is for development and may differ in a last decimal |
| Outside tools | A container named by digest. Its output goes in the vault by hash and is an input to `assemble` |
| Proof | CI runs steps 4 to 12 in two separate jobs and compares the two manifests. A difference fails the build |
| Never overwritten | `write_release` already refuses. A correction is a new release |

## 7. Coverage

Every area and every measure has a state. There is no blank.

| State | Meaning | Counts as a gap |
|---|---|---|
| `present` | A value, with at least 99% of homes covered | No |
| `partial` | A value, with 50% to 99% covered | No. The share is shown |
| `below_threshold` | Under 50% covered. The value is null | Yes |
| `source_gap` | The publisher holds nothing for these units | Yes |
| `suppressed` | The publisher withheld it | Yes |
| `not_published` | The publisher does not publish it for areas this small. Main language is published for boroughs only (repo) | No. It is said, once |
| `not_carried` | This build does not work the measure out. Its source may be cleared and fetched: the build's own record says why, where a reason is known | Yes, for the release |

`coverage.json` in the release holds the state for every area and measure. The report is written from it, and is committed with the lock:

| Table in the report | One row per | Columns |
|---|---|---|
| By source | Source | Files, period, date retrieved, areas with a record of 450, share of London's homes covered, boroughs with a gap |
| By measure | Measure | Areas in each state, the least covered borough |
| By area | Area | Measures present of those carried, essentials present of five, worst measure |
| Gaps | Area and measure that is a gap | State, reason, what would close it |
| Claims | Kind of claim | Found, kept, dropped by reason |

Launch gates, proposed. ADR 0014 sets the first five. The numbers are for the founder to confirm.

| Gate | Passes when |
|---|---|
| Every home in one area | Every London output area in the lookup is in exactly one area. Every live London postcode resolves to one area. The areas' outlines together match the outline of Greater London |
| Name and boundary | Every area has both, and its neighbours |
| Travel times | Every area has a time, or "beyond the cutoff", to at least 99% of destinations, by every mode |
| Cost range | Every rankable area has a rent range and a price range for at least one segment. Those at `low` confidence are counted |
| Enough to rank | Every rankable area has a value for at least 80% of the measures carried, and none for under 60% |
| Each measure | A value in at least 95% of rankable areas, or the release carries it as not rankable |
| Evidence | Every fact has an evidence row. Every file named is in the lock and in the vault |

## 8. Checks before a release is served

| # | Check | Fails when |
|---|---|---|
| 1 | Structure | `open_release` refuses |
| 2 | Licence | `write_release` finds a source not registered for the use its file needs |
| 3 | Evidence | A fact has no evidence row, or a row names a file that is not in the lock |
| 4 | Coverage | A gate of section 7 |
| 5 | Totals | A London total differs from the publisher's own by more than 0.5%. Census sums are allowed to differ, and the difference is reported |
| 6 | Ranges | A value is outside the range written for its measure |
| 7 | What moved | Against the last release, an area moves over 20 percentile points on a measure whose inputs did not change |
| 8 | Outside checks | A `validation_only` source disagrees beyond the line written for it: MSOA median prices, a sample of 1,000 journeys |
| 9 | What must never be there | A postcode, a `BT` postcode, an establishment's name, a person's name, a hygiene rating, or a row below an area |
| 10 | Lineage | A file of the release has among its inputs a share-alike source outside routing, or any resident or audit source |
| 11 | Real and not synthetic | An id begins `syn-`, or `synthetic` is true |
| 12 | Repeat | The second build's manifest differs |
| 13 | It loads | The API does not start on it, a fixed set of 20 specs does not rank, or memory passes 600 MB on a 1 GB machine |
| 14 | A person | The founder has not read the coverage and diff reports and approved the release by committing its lock and its reports |

The release the API serves is named by a setting. To go back is to name the last release.

## 9. The census tables: kept where scoring cannot read them

ADR 0014 asks that the gate keep them out "by rule and not by care". Each fence below has a test.

| Fence | How | Test |
|---|---|---|
| Registry | Resident tables sit in their own dimension, with `display` as their only product use | The gate refuses one for `scoring`. A rule refuses the registry if one lists it |
| Vault | Their own prefix and their own key. The product build's key cannot list them | The product build job is given no such key |
| Code | `burro_pipeline.residents` imports nothing from the product steps, and they import nothing from it | An import test, as core has for IO |
| Lineage | The lock lists the inputs of every output file | No file of the release has a resident file among its inputs |
| Artefact | A folder of its own, `<release_id>-residents`, with its own manifest, keyed by `area_id` | `open_release` refuses a release folder that holds a resident file |
| Core | It is not part of the `Release` protocol. `rank`, `facts_for`, `explain` and `similar` cannot be handed it | A test on imports and on signatures |
| Shares only | The artefact holds whole percentages and "under 1%". It holds no count, so none can be printed | A test on the artefact's schema |
| Models | No step that calls a model can read the prefix | The research job is given no such key |
| Audit | A third store. It reads the release and the protected tables, and writes correlations only | A separate job, run by hand |

Two things are not resident tables and stay in the product build: the number of homes in an output area, used as a weight, and the total population of an LSOA, used under a rate. The registry approves both sources for scoring today. The age and sex columns are dropped at step 4.

## 10. Sizes

| File | Size | Basis |
|---|---|---|
| HM Land Registry Price Paid, complete | 5.3 GB | repo |
| OpenStreetMap, Greater London | 123 MB | repo |
| ONS median prices by MSOA | 65.3 MB | repo |
| Land use table by LSOA, not yet registered | 36.4 MB | repo |
| TfL timetables | 24.31 MB | repo |
| Price Index of Private Rents workbook | 17.8 MB | repo |
| Indices of Deprivation, file 8 | 13.8 MB | repo |
| GLA high streets, town centres | 4.22 MB, 1.63 MB | repo |
| Rents by postcode district | 129.4 kB | repo |
| Census tables | One zip per table, one CSV per geography. No size is shown | read |
| Every other source | Not known. National OS products and the postcode directory are assumed at 0.5 to 2 GB each unzipped | estimate |
| **Vault, first fetch** | **10 to 25 GB** | estimate |
| **Vault, after a year of quarterly builds** | **About 40 GB**. A file that did not change is stored once | estimate |

| Part of the release | Rows | Size | Basis |
|---|---|---|---|
| `features.json` | 450 × 45 = 20,250 | 2 MB | estimate, 90 bytes a row |
| `tags.json`, `cost.json`, `stations.json` | 6,300, 4,500, 1,500 | 1.5 MB | estimate |
| `travel`, as one byte a cell | 450 × 16,700 × 4 = 30 million cells | 30 MB | estimate. As JSON it is about 100 MB |
| `places.json` | About 50,000 | 12 MB | estimate |
| `geometry.json` | 450 polygons | 7 MB | estimate |
| `evidence.json`, `coverage.json` | 33,000 | 6 MB | estimate |
| **Release** | | **About 60 MB** | estimate |

## 11. Time and cost of one full build

Times are for the standard hosted runner: 4 processors, 16 GB of memory, 14 GB of disk (read). None is measured.

| Step | Time | How it was estimated |
|---|---|---|
| Fetch | 40 minutes, and the founder's time for by-hand files | 15 GB at 50 megabits a second |
| Seal and normalise | 20 to 40 minutes | One pass over 15 GB. Workbooks are slow to read |
| Cells, polygons, crosswalks | 5 to 10 minutes | 26,369 output areas |
| Walk graph and walk measures | 20 to 60 minutes | 26,369 short searches for each of about 12 kinds of place, in plain Python |
| Other measures, vibes, cost | 10 to 20 minutes | |
| Residents, claims check | Under 5 minutes | |
| Assemble, check, report | 10 to 20 minutes | |
| **Build without routing** | **1 to 2.5 hours** | The sum. The second build for the proof runs beside it |
| Routing | 5 to 15 processor-hours | repo: 2 to 8 seconds an origin, unmeasured, by 4,994 origins, for the public transport run. Walking and cycling are added |

| Item | Cost | Basis |
|---|---|---|
| Hosted CI on a public repository | GBP 0 | read: standard runners are "free and unlimited on public repositories" |
| Vault of 40 GB | USD 0.45 a month | read: USD 0.015 a GB-month, first 10 GB free, no charge to read out |
| Routing on a rented machine, if needed | USD 3 to 15 a build, about GBP 2 to 12 | read: 16 processors and 32 GB at USD 0.72 an hour, the price for Amsterdam. 4 hours, with memory added. The research put it under GBP 20. The exchange rate is assumed |
| Research with a model | Capped by an input that the lock records | Not estimated here |
| **A quarterly build** | **GBP 0 to 12, and under GBP 1 a month** | |

## 12. Where a build should run

A build host needs four things: a way out to the publishers' hosts, 14 GB of free disk, Python with the locked packages, and, for routing only, Java or a container runtime. Writing and testing the pipeline's code needs none of them: every step is tested offline on small made-up files shaped like the publisher's.

| | A machine that a person runs | Hosted CI on the public repository | A rented cloud machine |
|---|---|---|---|
| Cost | GBP 0 | GBP 0 (read) | USD 0.12 to 0.72 an hour, on the one host whose prices were read |
| Reaches the publishers | Not known. A person can save a page by hand | Not certain. Code has not read the pages of several publishers (repo) | The same doubt as CI |
| Limits | None | 6 hours a job, 14 GB of disk, 16 GB of memory (read) | What is paid for |
| Java for routing | Not known | Java 21 and Docker are on the image (read) | To be installed |
| Repeats cleanly | Only as well as the machine is kept | A fresh machine every run | A fresh machine if built from an image |
| Who can see | The person who runs it | The log is public. Artifacts and caches can be read by others | The person who rents it |
| If it is lost | The vault's second copy is gone | Nothing is kept there | Nothing is kept there |
| Work to set up | Least | One workflow and its secrets | An account, an image, a teardown |

**Recommendation.**

1. **Fetch on a machine that a person runs.** It is the step that needs a person. Each file goes straight to the vault with its receipt.
2. **Build the release of record in hosted CI.** Steps 3 to 14, started by hand on the default branch, in an environment that needs the founder's approval. It reads the vault with a key that cannot write raw files. It prints step names, counts and hashes, and never a row. It uploads the release to the vault and publishes only the reports.
3. **Route in hosted CI if the benchmark fits, and on a rented machine if not.** Origins split across jobs keep each under 6 hours. If the routing tool needs more than 16 GB, rent a machine for the hours of the run.
4. **Develop anywhere.** A development build is never served.

## 13. Libraries, checked against rule 12

Rule 12 and ADR 0008 allow a compiled extension module, and refuse a package that needs its own native program to run.

| Library | Used for | How it installs | Verdict |
|---|---|---|---|
| Standard library: `csv`, `json`, `zipfile`, `hashlib`, `sqlite3`, `struct`, `heapq`, `math`, `urllib` | Reading CSV and zip, hashing, fetching, the walk search, reading a GeoPackage, which is a SQLite file | | Passes |
| `pydantic` | The records | Already a dependency | Passes |
| `duckdb` 1.5.5 | Reading large CSV, writing and reading Parquet, joins and sums | A wheel. It "has zero external dependencies" (read) | Passes, with extensions off |
| DuckDB extensions: `spatial`, `h3`, `httpfs` | | Installing one is "downloading the extension binary", at run time (read) | Fails. Not used. Autoinstall and autoload are set off, and a test says so |
| `shapely` 2.1 | Point in polygon, dissolve, distance | The wheel includes GEOS (read) | Passes |
| `numpy` | The byte matrices | A wheel. Shapely needs it | Passes |
| `pyproj` 3.8 | National Grid to longitude and latitude | A wheel. The "wheels do not include transformation grids" (read) | Passes if PROJ is inside the wheel: check at first install. Network off. The operation is pinned and tested on published points |
| `h3` 4.5 | Destination hexagons | Wheels, no compiler needed (read) | Passes. The registry note that calls it a conflict with ADR 0008 should be corrected by its owner |
| `openpyxl` 3.1 | Workbooks | Pure Python (read) | Passes |
| `defusedxml` | TransXChange and other XML | Believed pure Python | Passes, unverified |
| `pyarrow` | Reading the part of the file of places that fetch took, in the one step that counts cultural venues. Fetch reads a footer with the standard library and does not use it | A wheel of compiled extension modules, with no program of its own | Allowed by the founder on 2026-09-24, for building data only. It is never part of the served API |
| `pyogrio` | A format that `sqlite3` cannot read | The wheels include GDAL (read). A wheel for Python 3.13 was not confirmed | Passes. Not needed at first |
| `pandas`, `geopandas` | | | Not used. Nothing here needs them |
| Routing engines, and `r5py` | Travel times | Need Java, and fetch a program at run time (repo) | Fail as packages. Run as an outside tool in a pinned container (section 6) |
| Job orchestrators | | | Not used |

## 14. What this design asks of other owners

| Owner | Change |
|---|---|
| Contract | `schema_version` 2: `evidence.json` and `coverage.json` in a release, `files` in `manifest.sources`, `derivation_id` on a catalogue row, `evidence` on a fact. Travel as bytes and not as JSON, which the contract already allows as a second implementation |
| Contract | The residents artefact as a folder of its own, and the rule that a release folder never holds one |
| Registry | The dimension for resident tables. A lookup from 2011 to 2021 LSOAs, if any file needs one. `display` on any source whose figure is printed (contract 13) |
| ADR 0008 | The four steps, so that a lockfile is committed |
| A new decision record | Where builds run, what may be committed, and the launch gates |

## 15. Risks and open questions

| Risk | What this design does |
|---|---|
| A row is printed to a public log | The build prints from a list of what may be printed. The full log goes to the vault |
| A publisher refuses the build host | Fetch is apart from build, and a file may be saved by hand |
| LSOA codes of two censuses are joined | The geography is a field of the receipt, and a join across two is refused |
| A new GEOS or PROJ moves a byte | Packages are locked. One platform is of record |
| The vault is lost | Two copies. The receipts in git say what to fetch again, where the publisher still serves it |
| A licence ends | `purge`, and the list of releases to withdraw |
| Census sums do not match the office's totals | The office changes small counts on purpose (repo). Shares only, "under 1%", and the report states the difference |
| The release outgrows the API's memory | Check 13. Travel as bytes |
| Every estimate here is wrong | The first fetch writes real sizes. A benchmark of 200 origins and one of step 7 on one borough come before any plan is fixed |

| # | For the founder | Recommended |
|---|---|---|
| 1 | Where does the build of record run? | Hosted CI, from a private vault, started by hand |
| 2 | May receipts, locks and coverage reports be committed to the public repository? | Yes. They hold no data |
| 3 | Which object store holds the vault, at under GBP 1 a month? | The one the plan already names for tiles |
| 4 | Are the launch gates of section 7 right? | Yes, as a start |
| 5 | Does evidence travel inside the release, at about 6 MB? | Yes |
| 6 | Does the residents artefact hold shares only, and no counts? | Yes |
| 7 | Is a position good to a few metres enough, or is the national grid file registered as a source? | A few metres is enough for an area |

## 16. What was read, and what is unverified

Every page was read on 2026-09-23 through a reader that summarises, so wording must be checked in a browser before it is relied on. No data file was opened.

| Page | What it says |
|---|---|
| GitHub: hosted runners, limits, billing, caching, artifacts, releases | Linux runner for public repositories: 4 processors, 16 GB, 14 GB SSD, free. A job runs up to 6 hours. Caches: 10 GB, removed after 7 days unused, readable from a pull request. Artifacts kept 90 days. A release file must be under 2 GiB |
| GitHub: Ubuntu 24.04 runner image | Java 8, 11, 17, 21 and 25. Docker. Python 3.13 |
| PyPI and project pages: `duckdb`, `shapely`, `pyproj`, `h3`, `openpyxl`, `pyogrio` | The versions and the words quoted in section 13 |
| DuckDB: extensions, Parquet | Installing an extension downloads a binary. Parquet "is bundled with almost all clients" |
| Nomis: Census 2021 bulk | One zip per table, CSV files by geography. TS003, TS004, TS007A, TS021, TS024, TS025, TS030, TS044, TS050 and TS054 are listed |
| data.police.uk: about | The columns of the crime file. The census of the LSOA codes is not stated |
| Cloudflare R2 pricing, Fly.io pricing | The prices in section 11. One other host's prices were not read |

Unverified: every size and time marked estimate. Whether PROJ is inside the `pyproj` wheel, and how exact its answer is without a grid file. Whether `defusedxml` and `pyarrow` pass rule 12. Whether every publisher's GeoPackage opens with `sqlite3`. Whether the housing tables are published for output areas. Whether hosted runners can reach each publisher. How much memory routing needs. The counts 26,369, 4,994 and 16,700, which the research worked out and nobody has counted in a file. Another part's document, `london-data-researcher.md`, appeared in this folder while this was written and was not read.
