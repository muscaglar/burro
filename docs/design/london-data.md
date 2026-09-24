# Real data for all of London: one plan

Status: design, 2026-09-23. Milestone M0 of section 4 is built, and [the guide to data builds](../data-builds.md) says where it stands. Of M1 and M2 a preview has been made, and of M3 a draft. Neither is finished and neither is served: "What has been fetched since", below, says what each rests on. No later milestone has a build. It applies [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) and joins six designs written the same day: [pipeline](london-data-pipeline.md), [areas](london-data-areas.md), [travel](london-data-travel.md), [census](london-data-census.md), [researcher](london-data-researcher.md) and [sources](london-data-sources.md). Where this document and one of the six disagree, this one is what is built, and section 2 says what was not taken. Each of the six still holds the detail of its part.

No dataset was downloaded to write this plan. Nothing was run or measured for it. Every date, hour and pound below is an estimate unless it says "read". Every date assumes work starts on Thursday 24 September 2026. It is not legal advice.

**What has been fetched since.** On 2026-09-23 the step `fetch` was run outside a workflow, for the three lists `m1`, `m2-places` and `m2-living`. The store holds 62 files of 24 sources, 3.8 GB in all. Each source is approved in the licence registry, and the gate was asked about each file for the use its list gives. No hosted run has fetched a file.

| Publisher | Registry ids | Files | With a receipt |
|---|---|---|---|
| Office for National Statistics | `ons-oa21-lsoa21-msoa21-lad22-lookup`, `ons-output-areas-2021`, `ons-lsoa-2021`, `ons-msoa-2021`, `ons-oa-pwc-2021`, `ons-lsoa-pwc-2021`, `ons-census-2021-housing-tables`, `ons-median-house-prices-msoa`, `ons-price-index-of-private-rents`, `ons-private-rental-market-london-postcode-district` | 11 | 11 |
| Ordnance Survey | `os-open-names`, `os-boundary-line`, `os-open-roads`, `os-open-greenspace`, `os-open-rivers` | 6 | 6 |
| Valuation Office Agency | `voa-council-tax-stock-of-properties` | 3 | 3 |
| Department for Environment, Food and Rural Affairs | `defra-pcm-background-air` | 2 | 2 |
| Ministry of Housing, Communities and Local Government | `mhclg-iod-2025-underlying-indicators` | 1 | 1 |
| HM Land Registry | `hmlr-uk-house-price-index` | 1 | 1 |
| Ofsted | `ofsted-state-funded-schools-mi` | 1 | 1 |
| Food Standards Agency | `fsa-food-hygiene-ratings` | 33 | None |
| Greater London Authority | `gla-town-centre-boundaries` | 1 | None |
| NHS England | `nhs-ods` | 2 | None |
| OpenStreetMap contributors, as Geofabrik publishes the extract | `osm-geofabrik-greater-london` | 1 | None |

- **The files are kept outside the repository.** They are in a store that the environment names and no tracked file does. No file of a publisher is committed, and no row of one.
- **What is committed is the receipt of a file, and counts.** `data/receipts/` holds 25 receipts: the address a file came from, its hash, its size and its dates. Six pages under `docs/research/data/`, named for the builds `m1`, `m2` and `m3`, hold counts made from the files, London's lowest, middle and highest figure for a measure, and how far two measures put the areas in the same order. Each carries the credit of each publisher. No figure is said of a named neighbourhood.
- **37 files had no receipt**, because the page of each names no edition. 36 have one since 2026-09-24, when each was fetched again and read for the edition it states of itself. The street extract has none, and no step of a build reads it.
- **Nothing of it is published, and nothing is served.** Two previews of London and a draft of its named areas were made from the files. Each is written where git does not look, each says that it is not finished, and no person has checked any of them. [The guide to data builds](../data-builds.md), sections 15 and 16, says how a preview is made and seen.
- **The plan below is as it was written.** Where it says that a size, a layout or a census is not known, those six pages say what was found in the files that were fetched.

Reviewed the same day against the six designs, the registry and the code as it stood. Corrected on review: the size of the first files, the schema number, the registry change M1 needs, the method behind the noise figure, and what M1 to M5 wait on. What the review could not settle is in section 14.

Amended the same day, to apply [ADR 0007](../adr/0007-no-solicitor.md) as it now stands: Burro relies on the licence each owner publishes, and no launch waits on a reply from a data owner. A question put to one is a courtesy and a record.

| What the amendment changed | Where |
|---|---|
| No milestone, no step of the critical path and no task waits on a reply from a data owner | Sections 0, 4 to 7, 10 to 12 and 14 |
| The wait on the subscription to the rail schedule being approved is kept. It is the one wait on somebody outside that can stop a launch | Section 5 |
| Three sources that were held back for want of an answer are brought forward, as the registry records them: tree canopy, parkrun and the Arts Council lists | Section 4 |
| No date was moved, and none was added. What the dates now rest on is said beside them | Section 5 |

The six designs were written before the amendment. Where one of them holds a step back until a question is answered, or says that one of the three sources is not registered, this document and the registry stand.

## 0. In short

| Question | Answer |
|---|---|
| What stands behind a statement | A stored record with its source, the date of the data, the date retrieved and the method. Eight kinds of statement, one record each (section 1) |
| Where it runs | Fetch, build, routing and model research in hosted CI on the public repository, started by hand. Files in a private object store. Code is written and tested anywhere, offline |
| What it costs | Under GBP 1 a month between builds. Under GBP 20 in a month with a build. The first build adds GBP 3 to 55 once. One-off: GBP 870 to 1,520 for the second reviewer |
| First real thing on screen | Friday 2 October 2026: five cited measures for every part of London, on official census areas, on the founder's screen only. It holds if rows 1 to 3 of section 14 are settled by Monday 28 September |
| Named areas for all of London | Friday 16 October 2026, with each area's page saying how far its boundary was checked |
| First release that passes every gate of ADR 0014 | Friday 20 November 2026, if the rail subscription is approved in time for its agreement to be read by 9 November. The areas and vibes chains then set the date |
| Launch release | About Friday 18 December 2026, after the December rail timetable change |
| The one wait that can stop it | The subscription to the rail schedule being approved. Nobody has subscribed, and how long approval takes is not known. No launch waits on a reply from a data owner (ADR 0007) |
| Founder hours | About 155 to 20 November, about 210 to 18 December |

## 1. The shape

```
 publisher's host                                   gazetteer/london/oa_to_area.csv
      │ 1 plan: Registry.require(id, use)           (git: drafted by method, changed by people)
      │ 2 fetch: the only step with a network                │
      ▼                                                      │
 VAULT raw/<source_id>/<sha256>/ ── receipt ──► git, data/receipts/
      │ 3 seal ──► lock.json ──► git, data/locks/            │
      │ 4 normalise: London rows, allowed columns            │
      ▼                                                      ▼
 staging ─────────────► 5 cells: crosswalks, polygons, weights by homes
      │      ┌───────────────────┬──────────────────────┬─────────────────────┐
      │      ▼                   ▼                      ▼                     ▼
      │  6, 7 derive         8 travel               9 cost, places,      11 claims
      │  walk graph,         R5 in a pinned         stations             the reviewed bundle,
      │  measures, vibes     image ► fine                                by hash ► code runs
      │      │               matrices (vault)                            its checks again
      │      │               ► roll-up                                        │
      │      └───────────────────┴──────────┬───────────┴─────────────────────┘
      │                                     ▼
      │            12 assemble ► release/<id>/ with evidence.json and coverage.json
      │            13 check ► 14 report ► the founder approves ► 15 publish
      │                                     ▼
      │            the API holds the release in memory ► Fact(sources, as_of, evidence)
      │                                     ▼
      │            template sentence ► verifier ► screen, with its "Sources" line
      │
      └─► 10 residents (own key, own code) ► <id>-residents/census.json
                    ► GET /v1/areas/{id}/census ► the census block, on the area page only

 RESEARCH RUN, before a build (own keys): fetched page ► a model points at sentences
                    ► code checks ► a person accepts ► the bundle, in the vault
 AUDIT store (its own key): reads a release and the protected tables. Writes correlations only.
```

Steps 3 to 14 run with sockets refused, but for the vault. A model is called in the research run and nowhere else. A build never calls a model, and nothing asks a model about a place when a person is waiting.

What stands behind each thing a screen can say:

| On screen | Record | Source | Date of the data | Date retrieved | How derived | Kept in |
|---|---|---|---|---|---|---|
| A figure for a measure | Evidence row, keyed by `fact_id` | `inputs`: the receipt of every file used | `data_period` | `retrieved_on` | `derivation_id`, one of twelve named methods (section 2), with its sentence | `evidence.json` |
| A vibe's band | An evidence row for each part. The recipe is in the release | The parts' publishers, after "Burro's recipe. Made from data published by" | The span of the parts | The parts' | `tag_raw()` over the recipe | `tags.json`, `evidence.json` |
| A journey time | One record for the build, not for the cell | Each timetable and the street extract, by receipt | The day modelled | Each feed's | Engine, version, settings, percentiles, roll-up | `travel.json` beside `travel.bin` |
| A cost range | Evidence row | Sales, index, rents, postcode directory | `as_of` month | `retrieved_on` | `postcode_to_area`, then the rent model's own sentence | `cost.json`, `evidence.json` |
| An area's name | Name evidence rows: two publishers, one that places it | `source_id` and the publisher's own record id, `as_written` | `data_date` | `retrieved_on` | `chosen_by` a role, on a date | `name_evidence.csv` in git, copied into `evidence.json` |
| An area's boundary | One row for each output area | The evidence that placed it | | | `basis` auto or reviewed, `decided_by`, `reason` | `oa_to_area.csv`. The manifest holds its hash |
| A census share | The table's own evidence | `source_id`, file, `sha256` | 21 March 2021 | `retrieved_on` | `oa_sum@1`, and the hash of the membership file | `<id>-residents/census.json` |
| A quotation | Claim, keyed by `claim_id` | The page by receipt, its `revision_id` and address | `source_dated` | `retrieved_at` | `start`, `end`, method, models, checks, review | `claims.json`. Pages in the vault |

## 2. Where the six differed, and what was chosen

| Point | Chosen | Not taken |
|---|---|---|
| The record of a fetched file | The pipeline's receipt, for every part. Every other record cites a `file_id` | The areas' `snapshots.json`, the researcher's `evidence/index.jsonl`, and travel's own `inputs` fields. Each held the same things under other names |
| The record of a claim | The researcher's record and its ten checks. Its `page` is a receipt | The pipeline's shorter claim and four checks, which are a subset |
| When the model runs | In a research run of its own. The build takes the reviewed bundle by hash and runs the checks again | Fetching and selecting inside every build, as the researcher's steps read |
| Where fetch runs | Hosted CI, with a file saved by hand where a publisher refuses the runner | Fetching on a machine that a person runs, as the pipeline recommended. The first map should exist in days |
| How the routing engine arrives | R5 and r5py inside one image named by digest, with the jar already in it. The benchmark alone may use r5py as installed | r5py in a dependency group, fetching its jar at run time. A step of a build has no network |
| The registry use for census tables | A new use, `census_table`, under a new heading `residents` | `display` with a rule on the heading. `stations.json` already asks for `display`, so the gate itself would let a table into a release |
| Does the census artefact hold any count | The base of each table, rounded to 100 and written as words. No count of a category | No base at all. A share with no base misleads for a small area |
| OpenStreetMap when checking names | Not used at all in the gazetteer | Aggregate comparison, which the gated entries would allow. Wikidata does the job |
| A walk from homes to the nearest thing | The median by homes, `walk_to_nearest` | The mean, as the sources plan wrote it |
| Roll-up of journeys | The weighted lower median, so every time is one a real home point has | A plain median, which can fall between two times |
| A rate published with no top and bottom, such as the noise share | A mean over the area's LSOAs, weighted by homes: a twelfth method, `lsoa_value_by_homes`, marked `averaged` | No method at all. The pipeline never takes a mean of rates and the sources plan always does. With no method the build stops at the first noise figure |
| Which sales files | The yearly Price Paid files, three or four of 115 to 230 MB (read by the sources plan) | The single 5.3 GB file. The vault is then 5 to 8 GB at first fetch and not 10 to 25 |
| Journeys routed to | 120, 60 and 60 minutes. One byte a cell still holds it | The contract's 90 for public transport |
| Weight behind "homes" | Households by output area, table TS044, which the registry approves for scoring. It gains the use `routing` | A contract change so that `travel.json` need not name it |
| What is shown before the named map exists | A preview on the 1,002 MSOAs, to the founder alone | Showing nothing until the map is reviewed |
| Wikipedia text and a model | Sent to a prompt that returns sentence numbers and writes nothing, if the founder agrees (decision 4) | "Never sent to a model", as the sources plan and three older documents say. If the founder says no, code takes the first two sentences |

## 3. Where it runs

One recommendation: **hosted CI on the public repository does the work, and a private object store holds the files.**

| Work | Runs on | Needs | Network | Cost |
|---|---|---|---|---|
| Writing and testing code | Anywhere | Python. Made-up files shaped like the publishers' | None | 0 |
| Fetch | Hosted CI: a standard runner, 4 processors, 16 GB, 14 GB of disk, free on a public repository (read) | The fetch key. TfL and rail logins | The publishers' hosts | 0 |
| A file a publisher will not give a runner | A person, in a browser | The file is uploaded with a receipt marked `by_hand` | | 0 |
| The rail schedule, until its agreement has been read, and after it if the agreement says UK only | Not on a runner and not in the vault: either may be outside the UK (read, section 13) | A machine and a store in the UK, unless the agreement as executed allows more. Section 14, row 4 | The marketplace | GBP 2 to 12 a build, if rented |
| Build, steps 3 to 14, run twice and compared | Hosted CI | The build key, which cannot write raw files. A committed lockfile | The vault only | 0 |
| Routing | Hosted CI, 8 shards, if the benchmark shows a London network fits in 12 GB of heap | The pinned image. Java 21 is on the runner (read by the travel design) | None | 0 |
| Routing, if it does not fit | A machine rented for the hours of the run | The same image | None | GBP 2 to 12 a build |
| Research with a model | Hosted CI, a workflow of its own | Two provider keys, capped. No vault key for residents | The publisher and two providers | Section 9 |
| The vault | Cloudflare R2, which the plan already names for releases | Three private buckets: product, residents, audit | | Under GBP 1 a month |
| Serving | As today: the API holds one release in memory | The release, fetched at deploy | | PLAN section 12, unchanged |

Rules that come with a public repository:

| Rule | Why |
|---|---|
| Every data workflow starts by hand, on the default branch, in an environment the founder must approve. None runs on a pull request | A pull request from anyone must never meet a key |
| A step prints from a list of what may be printed: step names, counts, hashes, timings. The full log goes to the vault | A public log is read by anyone. Price Paid, the food register and the schools register hold rows about one home or one person |
| No raw file, staging table, matrix, release or rejected claim is ever a CI artifact, a cache entry or a release asset | A cache can be read from a pull request (read by the pipeline design) |
| Receipts, locks, reports and the curated gazetteer files are committed | They hold addresses, hashes, dates, counts and codes, and no row of data. Decision 2 |

What it costs a month: under GBP 1 between builds, and under GBP 20 in a month with a build (section 9).

What the founder does to start, about 5 hours, tasks 1 to 4 of section 6: push the repository and turn on Actions; make the approved environment; make the three buckets and four keys (fetch, build, residents, audit); open the TfL and rail accounts; store eight secrets (four vault keys, the TfL key, the rail login, two model keys).

Three things are not yet in hand. A build of record needs a committed lockfile, which waits on the four steps of ADR 0008. Until then every build is a development build, and M1 to M5 below are development builds. The image host must be added to the allowlist in `tools/check_public_only.py` before a workflow names it. And nothing yet says how the founder opens a release: none may be a CI artifact, nothing is deployed, and whether a release can be brought to where the website runs today is not known (section 14, row 1).

One full build, in numbers. None is measured on real data.

| Thing | Figure | Basis |
|---|---|---|
| Sources in the smallest release that is honest to launch | 29: 28 approved and 1 gated, the rail schedule | The sources plan, section 8 |
| Raw files at first fetch | 5 to 8 GB. The largest is the output area boundary file at full resolution: 1.49 GB for England and Wales, as the publisher's record gives it. OS Open Roads is a 969 MB zip | Sizes read by the sources plan and on review, with 1 GB for unknowns and 1 GB for matrices |
| Staging tables, London rows only | 1 to 3 GB | The pipeline's estimate |
| Pairs in one travel matrix | 4,994 × 16,700 = 83.4 million. One byte each | Arithmetic on counts from the research |
| The release | About 60 MB: `travel.bin` 30.1, places 12, geometry 7, evidence and coverage 6, the rest 3.5 | Estimates. `travel.bin` was measured on made-up numbers by the travel design |
| The residents artefact. `claims.json` | 0.5 to 1.5 MB. About 3.4 MB | Estimates |
| A build without routing | 1 to 2.5 hours on 4 processors | The pipeline's estimate |
| Routing, with and without rail, bike and foot | 6.6 to 26.4 processor-hours. 30 to 90 minutes by the clock in 8 shards | From an unmeasured guess of 2 to 8 seconds an origin |
| Memory of the API on a London release | Under 600 MB on a 1 GB machine, or the release is refused | Check 13 of the pipeline design |

## 4. The order of work

Agents start on every row today, offline, on made-up files. "By" is the Friday the milestone should be met.

| # | By | Real after it | What a person sees | Takes | Waits on |
|---|---|---|---|---|---|
| M0 Ready to fetch | 25 Sep | Nothing of London. The workflows run on the synthetic release. Two builds give one manifest. A planted canary row is in no log | Nothing new | Founder 5 h. Agents 2 days | The founder's push, buckets and secrets |
| M1 First real map | 2 Oct | The spine counted: 26,369 output areas, 4,994 LSOAs, 1,002 MSOAs, 33 boroughs. Five measures for all of London: flats, homes built before 1919, homes per hectare, transport noise, nitrogen dioxide. About 30 MB of tables. The two output area boundary files are 0.37 and 1.49 GB if taken whole (read) | The founder alone: today's website on a preview release of 1,002 official census areas, each under the statistics office's own label. Five cited figures on each page. Sliders rank on them. No journey, cost, vibe or neighbourhood name | Agents 5 days. Compute under 10 minutes. Founder 1 h | M0. The first registry change of section 12. Rows 1 to 3 of section 14. No account, no letter, no gated source |
| M2 Places and walks | 9 Oct | About 15 more measures: parks, water, heritage, schools, places to eat, high streets, station walk. The first coverage report. The commons check. OS Open Names measured. The routing benchmark of 200 origins | The founder alone: the same preview, with green, food and schools on it, and what is missing said in words | Agents 1 week. Compute under 2 hours. Founder 12 h, with the audit rule and the golden set | M1. The TfL key and a first conversion of TfL's feed, for the benchmark |
| M3 Named areas | 16 Oct | About 450 named areas. Every output area in exactly one. Every name read by the founder and resting on two publishers. About 120 flagged boundaries reviewed | Real neighbourhood names and outlines for all of London. Each page says "Boundary drawn by Burro's method. Not yet checked by a person who knows the area" where that is so | 2 weeks from the first download. Founder 42 h | M1, and the OS Open Names and OS Open Roads files of M2. Nobody outside |
| M4 Cost, places to reach, census | 23 Oct | A rent range and a price range for each rankable area. "I work at ..." finds a real place. The census block: five tables, shares as words, checked against the office's borough figures | A range with its confidence on every area. The census block, closed until asked for | Agents 1 to 2 weeks. Founder 5 h | M3. The registry change and rule 8's wording. The rent model, which no design holds yet (section 14, row 5) |
| M5 Journeys without rail | 30 Oct | Bike and foot for all of London. Public transport from TfL's feed, with no time where a train could be the way. 1,000 pairs checked against TfL's planner | Closed testers, by the form: two workplaces on one map, under the notice that trains are not counted (section 7) | Converters 1 to 2 weeks. The build 30 to 90 minutes. Founder 3 h | M3. The TfL key. The next contract schema. A host for testers, with its privacy notice (section 14, row 16) |
| M6 Vibes earn their place | 20 Nov | The audit store and its rule. Every part audited. 25 to 30 people have rated areas they know. Flags set by the outcome | The shelf of words, the lens and the portrait, for each vibe that passed. "Burro cannot place ..." for the rest | 5 weeks from M3: the audit 2, the people test 3. Founder 15 h | M2, M3. **Raters.** ADR 0013 |
| M7 Every gate passes | 20 Nov | Rail, Overground and Elizabeth line times. Every boundary checked by a person who knows it, a tenth by two. Evidence for every fact. Built twice, byte for byte | All of London, with no notice about trains | One build and a week of checks after the gate opens. Reviewer 40 h. Founder 60 h | **The rail subscription being approved. The second reviewer.** The lockfile. The two decision records of task 21, which the registry asks for before launch |
| M8 Quotations | 4 Dec | Up to eight of Wikipedia's own sentences for an area, each checked by code and accepted by a person | A marked box on the area page, "From Wikipedia", or the line that Burro holds none | Founder 49 h. Model GBP 2 to 40 | M3. Decision 4. Gates nothing |
| M9 Launch release | 18 Dec | Every journey rebuilt on the timetables in force after the change | The same product, on the timetable people will travel on | One build. Founder 3 h | **The timetable change**, taken as the weekend of 12 and 13 December |
| M10 The four vibes that wait | Not dated | Works and warehouses, Leafy, Places to train, Places to meet. The broadband line | Four more words on the shelf | | New registry entries, each on the licence its owner publishes: land use, Active Places, Ofcom fixed coverage, the pharmacy list. An owner that publishes no licence is left out until a person answers (ADR 0007), and nothing is held up for it. The three sources below no longer belong here |

### Three sources brought forward

The plan held back tree canopy, parkrun and the Arts Council lists for want of an answer. Each owner has since given permission in writing, as the founder reports, and the registry holds an entry for each. So none waits on an answer, and none waits for M10.

Each entry is `gated`, and the gate refuses all six for every use. A reply that only the founder has read is no evidence that a reader can open, so nothing is fetched on it yet.

| Source | Registry ids | Gives, by [the vibes design](vibes.md) | The plan said | What it waits on now |
|---|---|---|---|---|
| Tree canopy and green cover, Greater London Authority | `gla-tree-canopy-cover-2024`, `gla-green-cover-2024` | A better canopy map, for Leafy | It would come later, after an answer from the owner | The founder's note of the reply. Whether the permission reaches the imagery, the height data and the Ordnance Survey data the layers were made from |
| parkrun events | `parkrun-events` | parkrun as a kind of meeting place, for Places to meet | It stayed out until the owner had said yes in writing | The founder's note of the reply. How the events are to be obtained: until parkrun has said, no page of its site is fetched by code |
| The Arts Council lists | `arts-council-england-libraries-basic-dataset`, `arts-council-england-accredited-museums`, `arts-council-england-national-portfolio` | Walks to a library, for Culture on the doorstep and Places to meet. Recognised venues | Libraries would come once the owner's page had been opened and saved | The founder's note of the reply. The addresses of the three pages, which nobody has confirmed |

- **What settles an entry is the founder's to do, and waits on nobody outside.** A dated note written from the reply itself, filed in `registry/evidence/`: [the registry's README](../../registry/README.md), "A permission in writing". It is task 25 of section 6.
- **An automatic reply is no answer** (ADR 0007). A reply that says only that a message arrived gives no permission, and the note says which kind each reply is.
- **One decision stands before all six.** `approved` asks for a link that a reader can open, and a reply has none. Whether a note in the repository can stand as that link is not decided. It is decision 19 of section 11.
- **Each source joins the first build after its entry is approved.** Its measures are audited with the other parts at M6. None is among the sources of the smallest release that is honest to launch, so none gates a launch.
- **A vibe moves only when every part of it has a source.** Leafy still needs the land use table, which is not registered. So the four vibes of M10 keep their place, and this plan gives them no new date.
- The two datasets of the Greater London Authority that have no answer stay `held`: `gla-laei-2022` and `gla-planning-london-datahub`. No milestone of this plan reads either.

M1 is honest because the contract already carries, for each measure, its sources, its vintage, its definition and the date retrieved. A release may carry fewer measures than core knows, and a journey that was not computed is `null`. So the API and website should load the preview unchanged. That is untested, and core moved on 23 September: its working tree holds release schema 2 and catalogue 2, for the vibes slice, so the preview is written to whatever core holds on the day. If the VOA file uses 2011 area codes, M1 shows noise and nitrogen dioxide alone until a lookup is registered. The page for the 2025 edition does not say which it uses (read on review).

What would bring M1 forward by two or three working days (estimate). Fetch first and write code second: the first run prints each file's sheet names, column names, row counts and which census its codes follow. Work at LSOA and MSOA and leave output area boundaries to M3: the fetch falls from about 2 GB to under 100 MB, and a grid square is found by arithmetic on a centre's easting and northing, with no geometry library. Give M1 one bucket and one key, and leave the other buckets, keys and accounts to the day each is first needed. Let a run that reads no key and no row about a home or a person start without an approval.

The files behind each milestone. Sizes were read on publishers' pages by the sources plan unless marked. No file was opened for this table.

| For | Registry id: file, format and size | Joins on |
|---|---|---|
| M1 | `ons-oa21-lsoa21-msoa21-lad22-lookup`: best-fit lookup V2, CSV. `ons-output-areas-2021`: boundaries BGC V2 to draw and BFC V8 to place points, GeoPackage. `ons-oa-pwc-2021`: centroids V4. `ons-census-2021-housing-tables`: `census2021-ts044.zip`. Formats from memory. Sizes not known, but for the two boundary files (section 13) | `OA21CD`, `LSOA21CD`, `MSOA21CD`, `LAD22CD` |
| M1 | `voa-council-tax-stock-of-properties`: CTSOP1.1, 3.1 and 4.1, zips of 732 KB, 7.53 MB and 5.87 MB. `mhclg-iod-2025-underlying-indicators`: File 8, XLSX, 13.8 MB, named columns only. `defra-pcm-background-air`: one CSV for each pollutant and year | LSOA code, of a census not yet known for VOA. `LSOA21CD`. Grid square by easting and northing |
| M2 | `os-open-roads`: GeoPackage zip, 969 MB. `os-open-greenspace`: 56.75 MB. `os-open-rivers`: 50.06 MB. `os-open-names`: CSV zip, 98.4 MB. `gla-town-centre-boundaries`: `Town_Centres_Boundaries.gpkg`, 1.63 MB | None. A point, line or polygon is placed in an output area |
| M2 | `dft-naptan`: CSV. `dfe-gias`: establishment fields, CSV, 61.68 MB. `fsa-food-hygiene-ratings`: 33 XML files, one for each London authority, for the walks. Counting the sites behind a name needs the national register: on London's files alone a chain with one London branch reads as independent. Planning Data: conservation areas and listed buildings, CSV or GeoJSON | `ATCOCode`. `URN`. `FHRSID`. Each by its coordinates to an output area |
| M3 | The M1 and M2 files, and `wikidata-places-and-landmarks`: one query, 720 items (research) | `OA21CD`. The publisher's own record id for a name |
| M4 | `hmlr-price-paid`: three or four yearly CSVs of 115 to 230 MB. `ons-postcode-directory`: zip of CSV, some hundreds of MB (memory). `ons-price-index-of-private-rents`: XLSX, 17.8 MB. The rent workbook, XLSX, 129.4 kB | Postcode to `oa21`. Borough code. Postcode district |
| M4 | Census: `census2021-ts003.zip`, `-ts004`, `-ts007a`, `-ts021`, `-ts030`, under 100 MB in all (estimate) | `geography code` to `OA21CD` (memory) |
| M5 | `osm-geofabrik-greater-london`: `greater-london-latest.osm.pbf`, 123 MB. `tfl-journey-planner-timetables`: zip of TransXChange XML, 24.31 MB. `ons-lsoa-pwc-2021`: 4,994 points. `uber-h3`: resolution 9, about 16,700 cells | Stop `ATCOCode`. `LSOA21CD`. H3 cell id |
| M7 | `network-rail-nwr-schedule`: CIF, fixed-width text. Size not known: the gate forbids opening it | Station codes to NaPTAN |

## 5. The critical path to all of London

| # | Step | Who | Ends |
|---|---|---|---|
| 1 | Push the repository. Make the vault and the secrets | Founder | Thu 24 Sep |
| 2 | Register on Rail Data Marketplace. Subscribe to NWR Schedule | Founder | Thu 24 Sep |
| 3 | **Wait.** The subscription is approved | The marketplace, and Network Rail as the owner | Not known. Nobody has subscribed, and it may be at once. The dates below hold if it ends by Thu 5 Nov |
| 4 | The executed agreement is read and saved, with the terms of use and the Platform Agreement. The rail entry is approved on what they say. The schedule is fetched to where the agreement allows | Founder, agent | Mon 9 Nov |
| 5 | The full build: convert, route with rail, roll up, check 1,000 pairs | Hosted CI | Fri 13 Nov |
| 6 | The founder reads the coverage, diff and validation reports, and approves | Founder | **Fri 20 Nov** |
| 7 | **Wait.** The December timetable change | The rail industry | Sun 13 Dec |
| 8 | The launch rebuild, its checks and approval | Hosted CI, founder | **Fri 18 Dec** |

Chains beside it, each of which must end by step 6:

| Chain | Ends | Its wait on other people |
|---|---|---|
| Areas, every boundary checked | 13 Nov, if the reviewer starts by 19 October and gives 10 hours a week | Finding the second reviewer |
| Vibes: audit, then the people test | 20 Nov | Finding 25 to 30 raters |
| Cost | 23 Oct to build. Before launch: a decision record on the use of the postcode field of Price Paid, which the registry entry takes in place of a reply | Nobody. The founder writes the record: task 21 |
| TfL times | 30 Oct to build. Before launch: a decision record on the timings TfL publishes for its feed, which the registry entry takes in place of a reply | Nobody. The founder writes the record: task 21 |
| Census block | 23 Oct | Nobody |
| Lockfile | Before step 5 | Nobody outside. It waits on the four steps of ADR 0008, which have no date, or on the amendment at the end of section 7 |

**What the critical path now runs through.** Three things, and no letter: the rail subscription being approved, the areas chain and the vibes chain. After them, the December timetable change.

| If | Then |
|---|---|
| The subscription is approved at once, or by 5 November | The areas and vibes chains set the date of step 6, and it is still 20 November |
| The subscription is approved later | Steps 4 to 6 move by as many days. Step 8 holds while step 6 ends before the timetable change |
| The subscription is not approved | Steps 4 to 8 have no date |
| The agreement as executed holds the data to the UK, as the public copy of it does | The schedule is held and worked on in the UK, on a rented machine. Whether a time worked out from it may be shown to a reader abroad is decision 15. No reply is waited for |

The public launch also waits on things outside this plan: the privacy notice, the company and accounts (PLAN section 11).

## 6. What the founder must do, in order

| # | When | Task | Hours |
|---|---|---|---|
| 1 | 24 Sep | Push the repository, turn on Actions, make the approved environment | 1 |
| 2 | 24 Sep | Make the buckets and keys. Store the secrets | 1 |
| 3 | 24 Sep | Register on the TfL API portal and make a key | 0.5 |
| 4 | 24 Sep | Register on Rail Data Marketplace. Subscribe to NWR Schedule. Read and save the executed agreement, the terms of use and the Platform Agreement | 2.5 |
| 5 | When there is time | Questions to data owners. Each is a courtesy and a record, and no task, milestone or launch waits on one (ADR 0007) | 3 |
| 6 | 24 to 25 Sep | Make decisions 1 to 8 of section 11 | 2 |
| 7 | 25 Sep | Mark each of the 33 boroughs "know well", "know a little" or "do not know". Start looking for the second reviewer | 1 |
| 8 | 25 Sep | Open and save the pages that nobody has read: Open Parliament Licence, DfE performance tables, Arts Council England, Active Places licence, Code-Point Open | 2 |
| 9 | 25 Sep | Apply to a free legal clinic, with sections 5 and 6 of the census design | 2 |
| 10 | By 2 Oct | Write the proxy audit rule of vibes 6.1, before any audit table is opened | 4 |
| 11 | By 2 Oct | Approve the registry changes and the new wording of rule 8 | 2 |
| 12 | By 9 Oct | Read the first coverage report. Check that 20 named commons, heaths and forests are in the greenspace file | 2 |
| 13 | By 9 Oct | Mark every sentence of 30 articles fit or unfit: the golden set | 6 |
| 14 | 5 to 16 Oct | Curate areas, fast route: read 1,100 names, review 120 flagged areas, look at 33 boroughs whole, try the review page | 42 |
| 15 | By 23 Oct | Census: save six evidence pages, add up three areas by hand, read the block for ten areas known well | 5 |
| 16 | By 30 Oct | Do the four steps of ADR 0008 | 1 |
| 17 | By 30 Oct | Read the first travel validation report. Approve the tester release | 3 |
| 18 | 19 Oct to 13 Nov | Curate areas, better route: brief the reviewer, review the half you know, read the reviewer's patches, settle disputes | 51 |
| 19 | 19 Oct to 13 Nov | People test: find and brief the raters, read the results | 15 |
| 20 | By 13 Nov | Open, save and confirm the 37 licence items the strict registry check lists | 6 |
| 21 | 5 Nov | Write the two decision records the registry asks for before launch: on the timings TfL publishes for its feed, and on the use of the postcode field of Price Paid. Make decision 15, on rail | 2 |
| 22 | By 20 Nov | Read the three reports. Approve the release by committing its lock | 3 |
| 23 | 9 Nov to 4 Dec | Review claims: confirm the map of areas to articles, read 3,100 claims, open the source for one in ten, read each block whole | 49 |
| 24 | 14 to 18 Dec | Approve the launch release | 3 |
| 25 | Before the first build that reads one | For each of the three owners who gave permission in writing, as the founder reports, file a dated note written from the reply itself, and make decision 19. The registry's README says what a note holds | Not timed |
| | | **To 20 November: about 155. To 18 December: about 210** | |

Row 25 is in neither total. Hours for rows 10, 19 and 20 are this document's own guesses. The rest are the six designs' guesses. None was timed. Not counted: starting and approving each data run and reading its log, accepting ADR 0013, standing up a host for the preview and for testers, and finding more than one reviewer (section 14, rows 2, 12 and 16).

## 7. If something is late

| Late | What ships | What Burro tells people |
|---|---|---|
| Rail is not cleared | The tester release only. Bike and foot are complete. No public transport time where both ends are within a 15-minute walk of a rail, Overground or Elizabeth line station. The public launch is held | Above every search: "Public transport times here count the Tube, the DLR, trams and buses. They do not yet count National Rail, the London Overground or the Elizabeth line. Where a train could be the way to travel, Burro gives no public transport time." |
| The second reviewer is not found | All areas. The founder reviews the other half, 30 hours more | "Checked by one person." |
| Some boundaries are unreviewed | All areas, to testers only | "Boundary drawn by Burro's method. Not yet checked by a person who knows the area." |
| A decision record of task 21 is not written | The tester release only. The strict registry check lists both, and the launch gate on licences needs it to pass | Nothing, until it is written. The methods page then says the figure rests on Burro's own reading of the published terms |
| The City of London has no published rent | A price range only, for areas there | "No rent figure is published for this borough." |
| The registry change for census tables | The block is left out of every area's page | Nothing. No line points to it |
| The audit store or its rule | No vibe is shown on a real release. Ranking is by measures and sliders | On `/vibes`: "Not in this data yet", with the reason |
| A vibe fails its audit or its people test | It is dropped from the release, or loses its place on the shelf, the map and the table | On `/vibes`: the rule, and the outcome as passed, changed or dropped |
| The Overture check fails | Culture on the doorstep is not in the release. Pace and Food and drink run at 85 and 80 hundredths | On `/vibes`: "Not in this data yet", with the reason |
| The commons check fails | Parks close by waits for a registered source | The same line on `/vibes` |
| Claims are not reviewed | Areas with no quotation | "Burro holds no cited description of {name} in this release." |
| The founder says no to decision 4 | Code takes the first two sentences of each article | The same box and credit |
| Routing does not fit a hosted runner | The same release, built on a rented machine | Nothing changes |
| The lockfile is not committed | Development builds only. Nothing is served in public | |
| A publisher refuses the runner | The file is saved by hand. Its receipt says so | Nothing changes |

If the four steps of ADR 0008 are not done by 30 October, hosted CI can write a requirements file with a hash for every package, which names no host, and the build can install from it. That needs ADR 0008 amended. Whether the tool leaves index addresses out by default is from memory and unverified.

## 8. The founder's eight points

| # | Point | Real for all of London | What is real then | Never |
|---|---|---|---|---|
| 1 | Vibes at the centre | 20 Nov, for each vibe that passes the audit and the people test | Up to nine on the smallest source set: Homes, Built age, Village feel, Quiet streets, Pace, Food and drink, Parks close by, Family amenities, Everyday on foot. Culture on the doorstep after the Overture check | A vibe written or scored by a model. An overall vibe score |
| 2 | "Gritty" | 20 Nov at the earliest, and only if the land use table is registered by 9 October and the spike and audit pass | The word quoted and read as Works and warehouses. Recorded criminal damage beside it, on request | One metric of crime, deprivation and street cleanliness. No data on cleanliness exists below borough level |
| 3 | Kinds of gym | 18 Dec at the earliest, if Active Places is registered by 16 October, on the licence it publishes | Places to train, from gyms, pools, courts and pitches within a walk. The kinds of gym nearby, shown | "Boutique", a price, a rating. The low-cost filter waits for the founder's operator list |
| 4 | Culture, highly ranked | 20 Nov for counts and kinds. Libraries and recognised venues in the first build after the Arts Council entries are approved (section 4) | Culture on the doorstep at 80 hundredths, on one source | "Best", "top", "highly rated". Every ratings source forbids reuse |
| 5 | Green, leafy, parks | Parks close by: 20 Nov. Leafy: as point 2, on the land use table | Walks to parks, large parks and play space. Gardens and woodland once the table is in. Tree canopy in the first build after its entry is approved (section 4) | A cemetery or a golf course counted as green. A rating of a park |
| 6 | Community, parkrun | 18 Dec at the earliest, once libraries or sports facilities are in. It ranks only if it varies within inner London | Places to meet, from kinds of place within a walk. A block on the portrait if it does not vary | "Friendly". parkrun while its entry is gated. A list of events compiled by hand |
| 7 | Services: 5G, fibre | Everyday on foot: 20 Nov, at 70 hundredths. Broadband: 18 Dec at the earliest, once the Ofcom file is registered | Walks to a food shop, a high street and a station. Then a GP and a pharmacy. Gigabit-capable coverage as a line | 5G or "full fibre" for a neighbourhood. They are published for boroughs only |
| 8 | Demographics | 23 Oct on the founder's screen. 20 Nov in the first release that passes every gate | Five census tables on each area's page: household composition, country of birth, age, ethnic group, religion | Main language for an area. Any ranking, filter, map, vibe or sentence from the figures |

## 9. Money

Pounds are at an assumed USD 1.30 to the pound. Every data source is free.

| Item | Provider | One-off | Monthly | Basis |
|---|---|---|---|---|
| Hosted CI | GitHub Actions, standard runners | 0 | 0 | Read today: "free and unlimited on public repositories" |
| Vault, 5 to 8 GB at first and 40 GB after a year | Cloudflare R2 | 0 | 0 under 10 GB. Under GBP 1 at 40 GB | Read today: USD 0.015 a GB-month, 10 GB free, no charge to read out |
| Routing image | A public container registry | 0 | 0 | Unverified. The billing page was not read |
| Routing on a rented machine, only if needed | Any host by the hour | | GBP 2 to 12 a build | One host's price, read by the pipeline design |
| Model, first full research run | Gemini to select. A second provider to check | GBP 2 to 40 | | The researcher's table: USD 3 to 50 |
| Model, drafting names | Gemini | GBP 1 to 14 | | The areas design: USD 1 to 18 for up to three runs |
| Model, each later build | The same two | | Under GBP 6 a build | Under USD 7 |
| Spending cap | Each provider's own setting | | USD 50 a month each, as a ceiling | |
| Second reviewer, 40 hours on areas and 3.5 on claims | A person the founder finds | GBP 870 to 1,520 | | GBP 20 to 35 an hour. The rate is a guess |
| Raters for the people test | 25 to 30 people | Not priced. GBP 375 to 750 if each is paid GBP 15 to 25 | | Decision 14. The sum is the review's guess and is not in the total |
| Legal reading of the census block | A free legal clinic | 0 | | ADR 0007 |
| Serving | As PLAN section 12 | | USD 65 to 120 | Unchanged by this plan. It starts with the testers of M5 and not at launch: about USD 27 a month for one API machine of 1 GB and the website's paid plan (`deploy/README.md`) |
| **The data, in all** | | **GBP 873 to 1,574** | **Under GBP 1 between builds. Under GBP 20 in a month with a build** | |

## 10. The five risks that matter

| Risk | Why it matters | What would show it early |
|---|---|---|
| The rail subscription is not approved, or the agreement says UK only | No rail, Overground or Elizabeth line. No honest launch for all of London | On the day of subscribing: whether approval is at once. On the day the agreement is executed: what its Schedule 1, section 7 says |
| Routing does not fit a hosted runner | The build moves to a rented machine or to the slower plan B | The benchmark of 200 origins, by 9 October: peak memory over 12 GB |
| The map feels wrong, or names fall short | A border that a resident knows to be wrong ends trust on sight | The first gazetteer report, by 6 October: how many names reach two publishers, and whether road records name anything finer than "London". No reviewer agreed by 16 October |
| A row, a key or a rejected claim reaches a public log | It cannot be taken back. TfL's licence ends on breach | M0: a canary row is planted in a made-up file, and the public log and artifacts of that run are searched for it before any real file is fetched. A second canary sits in a row that makes a parser fail, so that the error path is searched too |
| Vibes fail the audit or the people test | What the founder wants at the centre is thin at launch. Five of the ten rest partly on the food register and three on Overture | Each part is audited on LSOAs as soon as M2 lands, before any recipe is tuned. Any part at 0.5 or over. The Overture check in 20 areas |

Accepted, and so not listed: no professional has read the census block (ADR 0007, ADR 0014). Every estimate here is unmeasured; the first fetch shows real sizes, on the lines of its run and in the listing of the store.

## 11. Decisions for the founder

Work proceeds on the recommendation unless the founder says otherwise.

| # | By | Decision | Recommended |
|---|---|---|---|
| 1 | 24 Sep | Do fetch, build, routing and research run in hosted CI, from a private vault on Cloudflare R2 | Yes |
| 2 | 24 Sep | May receipts, locks, coverage reports and the curated gazetteer files be committed in public. A coverage report names real areas that have gaps | Yes |
| 3 | 25 Sep | A new registry use `census_table`, and rule 8's third sentence reworded to allow the heading `residents` | Yes |
| 4 | 25 Sep | May Wikipedia text be sent to a prompt that returns sentence numbers and writes nothing. Three documents say it is never sent to a model | Yes, with all three reworded in the same change |
| 5 | 25 Sep | Add `prototyping_only` to the rail entry, so a trial may open the file | Yes. The trial opens the file only where section 14, row 4 allows |
| 6 | 25 Sep | The census block: closed until asked for, five-year age bands, no household language, a floor of 1,000 people or 400 households, the base printed, a table withdrawn for all of London or for none | Yes to each |
| 7 | 25 Sep | Main language is published for boroughs only. Amend ADR 0014 to say it is not shown. Amend its cost test to read "a cost range, for rent or for sale" | Yes to both |
| 8 | 25 Sep | Does evidence travel inside the release, about 6 MB | Yes |
| 9 | 16 Oct | May an area ship with a boundary no person has checked, if its page says so | To testers, yes. At launch, no |
| 10 | 16 Oct | A place name that describes residents, written so by Ordnance Survey or the GLA | Keep it as the publisher writes it. Never coin one |
| 11 | 16 Oct | If under 400 areas reach two publishers, is one official publisher enough | Decide on the first build's count |
| 12 | 30 Oct | The launch gates: a time to 99% of destinations, 80% of measures in every rankable area and none under 60%, each measure in 95% of areas | Yes, as a start |
| 13 | 30 Oct | Do the walks to a GP and a pharmacy, and a broadband line, come into the first version. PLAN section 4 lists them as out | Yes |
| 14 | 30 Oct | Are raters paid, and at what rate is the second reviewer paid | The founder's call |
| 15 | 5 Nov | If rail is not cleared: hold the launch, launch with stated gaps, or open the gate on the founder's own reading of the agreement as executed | Hold while the subscription is not approved. Once it is, the agreement is what is relied on, and the founder records what it says on territory in a decision record (ADR 0007). To launch with stated gaps needs ADR 0014 amended |
| 16 | 5 Nov | TfL's feed and Price Paid are used on their published terms, each on a decision record, and neither waits on a reply | Decided by ADR 0007 as it now stands. The founder writes the two records: task 21 |
| 17 | 9 Nov | Is the first version of claims quotations only. Which second provider | Yes. Settle the provider on the golden set |
| 18 | When needed | May up to GBP 12 a build be spent on a rented machine | Yes |
| 19 | Before the first build that reads one | May a dated note in `registry/evidence/`, written from a reply that the founder holds, stand as the evidence that `approved` asks for. Six entries rest on it | The founder's call. Until it is made the six stay gated, and the gate refuses them |

## 12. What this asks of other owners

| Owner | Change | Needed by |
|---|---|---|
| Registry | The second gate check of the rail entry asks Network Rail for a confirmation in writing. Reword it to what the agreement as executed must say, in a change the founder reads, so that the entry waits on no reply (ADR 0007). The TfL and Price Paid entries already take a decision record | M7 |
| Registry | A dated note written from the reply, for each of the six entries that rest on a permission in writing (task 25, decision 19) | Before the first build that reads one |
| Registry | `scoring` on the geography sources a measure is worked out from: `ons-oa-pwc-2021`, `ons-lsoa-2021` and the lookup. Or a contract rule that a source registered for `cells` may stand behind a catalogue row. `write_release` asks `scoring` of every source a catalogue row names, so it refuses M1 as the registry stands. Say too which use a source named only in `evidence.json` is asked for | Done: ADR 0016 took the first way |
| Registry | `prototyping_only` on the rail entry. The police entry names the custom download form, never the archive, which holds stop and search | M2 |
| Registry | The heading `residents`, the use `census_table`, the field `tables`, three rules, the entry as gated. The audit entry, the housing entry and the README reworded in the same change | Done, for the founder to approve: task 11 |
| Registry | `routing` on the housing tables. `display`, with evidence, on each source whose figure or name is printed | M5 |
| Registry | `claims.json` to `profile_text`. The Wikipedia entry's third condition. `validation_only` on Wikidata | M8 |
| Registry | New entries: land use, Active Places, Ofcom fixed coverage, the pharmacy list. A lookup from 2011 to 2021 LSOAs if a file needs one. Tree canopy is registered, and gated: section 4 | M10 |
| Contract | The next schema (core's working tree already holds 2): `evidence.json`, `coverage.json`, files in the manifest, `derivation_id`, `evidence` on a fact, `travel.bin` with `method` and `inputs`, the 2-minute floor, the no-rail sentences | M5 |
| Contract | Each area's `review_state` and boroughs. The hash of the gazetteer files in the manifest | M5 |
| Contract | The residents artefact, `open_census`, the census route, and a release folder that refuses a census file | M4 |
| Contract | `claims.json` and the fact kind `quote` | M8 |
| Contract | Three faults found: `university_proximity` names a source with no universities, `station_lines` a feed with no rail, and `noise_exposure` is a share of residents, not homes | M1 for the noise label, which M1 prints. M5 for the rest |
| Deploy | The API takes the release and the residents artefact from the vault at deploy, by hash. Today the image copies a release from the repository, and the machine has 512 MB | M5 |
| AGENTS.md | Rule 8, third sentence | Done, for the founder to approve: task 11 |
| Decision records | 0013 on vibes. New records on the routing engine and the day modelled, and on the researcher. ADR 0014 amended by decision 7. Written: 0015, on where builds run and the launch gates, and 0016, on the geography behind a measure | With the code |
| PLAN | Sections 4, 7, 11 and 12 | With the code |
| `tools/check_public_only.py` | The image host on the allowlist, by M5. The check reads every URL in a workflow file, so from M0 the vault's address is a secret and the fetch list lives outside workflow files | M0 |

## 13. What was read, and what is unverified

Read on 2026-09-23 for this document, through a reader that summarises. Check the wording in a browser before relying on it.

| Page | What it says |
|---|---|
| GitHub Docs, GitHub-hosted runners | A standard Linux runner on a public repository has 4 processors, 16 GB and 14 GB of disk. "Use of the standard GitHub-hosted runners is free and unlimited on public repositories." |
| Cloudflare R2, pricing | "$0.015 / GB-month". "10 GB-month / month" free. Reading out "does not incur data transfer (egress) charges" |
| Network Rail, electronic national rail timetable | "The May 2026 timetable will be in operation from Sunday 17th May 2026 until Sunday 12th December 2026." 12 December 2026 is a Saturday, so the day or the date is wrong as read. The change is taken here as the weekend of 12 and 13 December |
| GitHub Docs, billing for packages | Not read |
| On review: GitHub Docs, managing environments, and GitHub-hosted runners | "Users with GitHub Free plans can only configure environments for public repositories." A person may approve a run they started unless "Prevent self-review" is set. "Windows and Ubuntu runners are hosted in Azure". No region or country is given |
| On review: Cloudflare R2, data location, and upload objects | Location hints by continent. Jurisdictions: European Union, FedRAMP, United States. No UK-only bucket. Wrangler is "limited to files under 315 MB". No limit is given for the dashboard |
| On review: the publisher's item records for output area boundaries | BFC V8: 1,494,728,704 bytes. BGC V2: 370,442,240 bytes. Each is the hosted layer for England and Wales, not a download. Both are "clipped to the coastline (Mean High Water mark)" |
| On review: GOV.UK, Council Tax stock of properties 2025, and Land use in England 2022 | The file sizes as this plan gives them. Neither page says which census its LSOA codes follow. The first was published on 25 September 2025 and updated on 22 May 2026 |

Unverified, beside everything the six designs list as unverified:

- Every date in sections 4 to 6. Each rests on hours that nobody has timed, and the rail dates on an approval that nobody has promised.
- That today's API and website load a preview release of 1,002 areas with five measures and no journeys. It follows from the contract and was not tried. Core is being changed today: on review its working tree held release schema 2 and catalogue 2, and the contract still said 1.
- That the statistics office's lookup gives each MSOA a label of its own. From memory.
- The date of the December 2026 timetable change, and whether 15 to 17 December falls in school term in every borough.
- That a key on the object store can be held to one bucket. From memory.
- That the second reviewer and the raters can be found by the dates given.
- The repository gained `docs/research/models/openai.md` after the researcher's design was written. Its model names differ from those in the researcher's cost table, which must be priced again before a provider is chosen.

## 14. Open questions

Found on review, 2026-09-23. None is a plain error, so none is corrected above. "Memory" marks what was not read. The dates of section 4 assume every row is settled on time. If rows 1 to 5 slip, the review's own estimate is a tester release in mid-November 2026, and a first release that passes every gate between Friday 18 December 2026 and Friday 22 January 2027. The later date is what follows if the days of 15 to 17 December are missed: the next midweek days in school term are in January. Without the rail subscription there is still no date.

| # | Open | Why it matters | What would settle it | Who, by |
|---|---|---|---|---|
| 1 | How the founder opens a release before anything is deployed | M1 to M4 are "on the founder's screen". A release sits in the vault and may not be a CI artifact. Without a way to open one, M1 shows nothing | On day one, bring one small file from the store to where the website runs. If that fails: a private host for the API and the website, behind a login | Founder, 25 Sep |
| 2 | Who starts a data run, and who reads what it printed | The founder starts and approves each run, and the public log holds counts only. Whoever writes the code cannot see why a run failed. M1 allows the founder 1 hour. Ten to thirty runs are likely before five files of unknown shape parse (a guess) | A lane with no approval for a run that reads no key and no row about a home or a person. A way for the code's author to read the full log | Founder, 25 Sep |
| 3 | Which census each file's LSOA codes follow | The VOA stock, the land use table and the police file do not say. LSOAs were split where London grew (memory), so a join on codes of the wrong census drops the newest districts and says nothing | Test every code against both code lists. Never trust a label. Register the office's lookup from 2011 to 2021 LSOAs now | Agent, first fetch. Registry owner |
| 4 | May the rail schedule be stored and worked on outside the UK. Is subscribing instant, and in whose name | The registry records "UK" under territorial use. The plan fetches to runners and a store that may be outside the UK. Nobody has subscribed, and nobody has read the executed agreement | Subscribing, and reading the agreement as executed. Until it has been read the schedule is held and converted in the UK, the trial included, and it stays there if the agreement says UK only. If the trial must wait for the approval, step 5 of section 5 needs two weeks and not four days (estimate) | Founder, 24 Sep |
| 5 | The rent model, and a price where under ten homes sold | No design holds it. The research gives one formula, untested. The office says its district rents should not be compared between areas, the workbook is frozen, and no source gives a room or a studio. It is not one of the twelve methods, so a rent range has no derivation to cite | A design with its sentence, its backtest and the error it publishes. A rule for a segment with few sales | Agent, 9 Oct. Founder approves |
| 6 | London's edge | Every file is cut to London's rows. A home at the edge may have its nearest station, park, school or shop over the boundary, and would read as far from everything. Whether the street extract has a margin is not known | A margin of 2 km (a first guess) on every point, line and polygon source and on the walk graph. The food register of the authorities next to London. Edge areas listed apart in the coverage report | Agent, M2 |
| 7 | The river | Output area boundaries stop at mean high water (read). A pier, a moored home or a point on a bridge is in no area. `water_access` measures from a centre line: where the Thames is over 600 m wide, 300 m from its middle is still water | A rule for a point in no output area: the nearest within 100 m, counted. A registered source for the bank, or the measure says "from the middle of the river" | Agent, M2. Registry owner |
| 8 | Homes built since 2021 | Weights and centres are of census day. An output area that has gained a tower weighs what it did in 2021. `built_since` of vibes 5.3 marks such an area and corrects nothing | Compare VOA homes at 2025 with census households, by LSOA. List each LSOA that grew by a fifth or more. The founder decides whether to weight by the newer count | Agent, M1. Founder, M3 |
| 9 | Figures that mislead at the scale of an area | Nitrogen dioxide is on a 1 km grid and an inner area is about 2 km² (estimate: 319 km² over about 175 areas), so neighbours share a value. A rate for each 1,000 residents or homes is large where few live: the City, the West End, an airport. The City may hold no rankable area | The first coverage report counts the distinct values of each measure, and lists every area under 3,000 residents with the rates it carries | Agent, M2. Founder reads |
| 10 | People who do not live in a household | Four of the five census tables count every usual resident, in a prison, a hall of residence or a barracks too (memory). In a small area one such place can shape every share. The panel's five notes do not say so | The founder decides on a sixth note | Founder, 23 Oct |
| 11 | Rows a join can lose | A sale with no postcode, or with one the directory lacks. A venue with no position. A station held as many nodes. The pipeline counts rows in and out of each step, and no gate reads the count | For each source: rows read, placed and lost, in the coverage report. A launch gate on the share lost, at 2 in 100 (a first guess) | Agent, M2. Founder, decision 12 |
| 12 | Can one person know half of London | M7 asks that every boundary is checked by a person who knows it. The plan finds one reviewer for about 225 areas in some 16 boroughs | The borough marking of task 7. Recruit by borough, and expect several people | Founder, 19 Oct |
| 13 | A boundary moved by who lives there | A reviewer moves output areas on what they know. A border that follows an estate changes every score on both sides. Nothing checks for it | In the audit store, for each patch: do the cells moved differ from the area they left, on the audit tables. One more line in the reviewer's rule | Agent, with M6. Founder |
| 14 | A model's drafts in a public repository | The areas design commits `proposals/` and a list of leads with no source. One of its jobs asks a model, from memory, for names people use. The researcher's design rules that out even as a lead. A review page built by CI would show a model's line | Drafts, leads and review pages live in the vault or behind a login. Or the job is dropped and aliases come from the sources alone | Founder, 2 Oct |
| 15 | Journeys: places with no street, and the check against TfL | A terminal, a hospital or a campus may sit in a hexagon with no walkable street. TfL's planner may answer only for today and later (memory): the 1,000 pairs are then asked before the day modelled has passed, and without rail in the tester release. With 20 jobs at once, the driver that runs origins side by side may not be needed | Thirty named workplaces must resolve and have a time. Ask the planner about a past date. Time one search at a time in the benchmark | Agent, M2 and M5 |
| 16 | Pages and records for reviewers, raters and testers | None is designed or costed: the review page, the rating page, a host, a login. A rating says where a person lives, so it is personal data. Testers need the privacy notice. The User-Agent line of a fetch needs a contact address that is not a person's own | One design for the pages. A store and a notice for ratings. The regulator's fee of GBP 52 before the first outside person | Agent, 9 Oct. Founder |
| 17 | The basemap | No milestone makes it, so testers at M5 see outlines on blank ground. The cut needs a command-line tool, and the tiles need a host | A milestone beside M5, or "a map of outlines" in what testers are told | Founder, 16 Oct |
| 18 | One vault, and files too large to upload by hand | Publishers replace files: TfL's feed each week, and the rent workbook may go. If the one store is lost, no release can be built again. A file saved by hand cannot go through Wrangler over 315 MB (read), and OS Open Roads is 969 MB | A second copy in another account, under GBP 1 a month. The device and the tool for an upload by hand, tried once at M0 | Founder, M0 |
| 19 | What the launch gate on measures means | "80% of measures in every rankable area and none under 60%" reads two ways | The founder states it with decision 12 | Founder, 30 Oct |
