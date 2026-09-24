# The second real build of London

Status: built on 2026-09-24, from the files fetched on 2026-09-23 for the lists `m1` and `m2-places`. It takes the place of the build `lon-2026-09-24-02` of the same day, which two checks found wanting. It follows [the first build](m1-first-build.md), which stands as it was written. It is a dated snapshot. Since it was written, the two rules under which the check first asked the licence registry again, in section 5, row 7, have become the one rule `input_is_allowed`, under which one fault is found once. The 2,005 findings of section 9 were counted under the two, and row 3 of section 7 can no longer be taken back alone.

**This is a second preview, for the founder's eyes. No person has checked anything in it.** No figure here has been held against a map, a visit or a publisher's own page. Every count was made by a program. It is a development build: it is never served to the public. Where a figure looks wrong, that is a finding and it is written down as one. Nothing was smoothed.

No figure here is said of a named neighbourhood, of a named area or of a named borough, and none is named. The figures on this page are counts, and London's lowest, middle and highest for each measure that is in the release. Every other figure is beside the release, in a folder that git ignores.

## 0. In short

| Question | Answer |
|---|---|
| What was built | One release, `lon-2026-09-24-03`: 1,002 areas, their outlines and four measures |
| What is on the map | What the first build put there: nitrogen dioxide, homes per hectare, flats and homes built before 1919. Nothing else |
| What is not on the map, and was asked for | Quiet, green, water and what a home costs. Each is worked out for all 1,002 areas, and each is left out. Section 4 says what each waits on. Every one waits on a decision, and none on a file |
| Why green cover is no longer in it | It counts public parks and gardens alone, and was shown under the name public green space, with the word greener. The licence registry asks that the sites are never described as all green space. It now carries a name of its own, so a build leaves it out |
| Why the tag Leafy has no score | With green cover left out, under 60 in 100 of its recipe has a figure. The design of the vibes has withdrawn the recipe core holds for it |
| How many areas have a figure | Nitrogen dioxide, homes per hectare and flats: all 1,002. Homes built before 1919: 979, as it had |
| Did any figure move | No. Every figure of every measure, in the release or left out, is the figure the second build worked out. The files of figures, of tags, of outlines and of areas are the same bytes as the first build's |
| Does every figure trace | Yes. Each of the 4,987 facts was followed through the API to its row of evidence, to the files the row names, to each receipt, and to the hash of the file in the store |
| Does the build repeat | Yes. Built twice from the same files and the same commit, with the lists given in either order, all 18 files are the same byte for byte |
| What the checks found | 31 findings, 10 of them major. Section 5 says what became of each |
| What to look at first | Section 8 |
| How to see it | Section 12 |

## 1. What was built

| Thing | Value |
|---|---|
| Release | `lon-2026-09-24-03`, built at `2026-09-24T01:00:00Z`. It is an input and not the clock. It is the hour of the last commit, and it had passed when the step was run |
| Command | `make preview ARGS="--release-id lon-2026-09-24-03 --built-at 2026-09-24T01:00:00Z --out data/releases --list m1 --list m2-places"` |
| Commit of the code | `78874a1`, read from the repository by the step. The working copy had no change |
| Packages | Not held by hash: no lockfile is committed. So it is a development build |
| `manifest.json`, SHA-256 | `d30c34d47ccc8ee760a5aa4c9e26874ce3fd0f73826e17247aabc9bf258b9aaf` |
| `evidence.json`, SHA-256 | `9c411ba73c47a5185ea4f32f9c930c0e98ca9c58a9d3bf897bc846c0d4fd2f8b` |
| `lock.json`, SHA-256 | `aa6e1b92d9976819e0a3490423a218ae328c146465d90599a46f140d8d5f6001` |
| `coverage.json`, SHA-256 | `cdb81a10cbd307ac6c075ce17d72f1e11474d626cb31fdbe4a5538f9f0c14616` |
| Schema and catalogue | Both at version 1 |

The first three hashes are what `hashes.json` holds. No program holds the release to the hashes printed here: they are in a page, and the service reads `hashes.json`. Section 8, row 2.

| Thing | Count |
|---|---|
| Output areas, LSOAs, areas, boroughs | 26,369, 4,994, 1,002 and 33, as in the first build |
| Facts the release would show | 4,987: a label for each of 1,002 areas, and 3,985 figures. No tag has a score |
| Rows of evidence | 51,102: one for every pair of an area and a thing Burro measures |
| Pairs with a value, as the coverage report counts them | 5,989 |
| Files in the lock | 19 |
| Files of the two lists with no receipt | 37. None is read by a step of a build |
| Seconds to build | 22 |

What is the same as the first build, `lon-2026-09-24-01`, byte for byte: `features.json`, `tags.json`, `geometry.json` and `neighbourhoods.json`. What differs: `catalogue.json`, by one sentence, which now says what the share of homes built before 1919 is a share of. The manifest and the evidence differ because they hold the id of the release.

## 2. From which files

Nineteen files are in the lock: every file of the two lists that has a receipt. Each was fetched on 2026-09-23.

| Files | How many | Which |
|---|---|---|
| Behind a figure of the release | 9 | The nine of the first build. [Its page](m1-first-build.md), section 2, lists them |
| Read for a measure that is left out | 4 | The two files of OS Open Greenspace, File 8 of the Indices of Deprivation, and OS Open Rivers |
| In the lock, and read by no step | 6 | The output area boundaries at full resolution, the MSOA boundaries, the centres of LSOAs, OS Open Names, OS Open Roads and Boundary-Line |

[The page on the files of the second build](m2-files.md) says what each file holds. No receipt carries the geography of its file or the members of a zip, as the first build found.

## 3. The measures in the release

| Measure | Unit | The data is of | Areas with a figure | Areas without | Lowest | Middle | Highest | Different figures | Method |
|---|---|---|---|---|---|---|---|---|---|
| Modelled annual mean nitrogen dioxide | µg/m³ | 2024 | 1,002 | 0 | 8.8 | 17.4 | 32.7 | 181 | `grid_at_homes@1`, marked modelled |
| Homes per hectare | per ha | 31 March 2025 | 1,002 | 0 | 1.3 | 32.2 | 154.8 | 587 | `area_row_ratio@1` over `land_inside_outline@1` |
| Flats as a share of homes | % | 31 March 2025 | 1,002 | 0 | 1.7 | 53.5 | 99.0 | 595 | `area_row_ratio@1` |
| Homes built before 1919 | % | 31 March 2025 | 979 | 23, withheld by the publisher | 0.0 | 23.4 | 97.2 | 518 | `area_row_ratio@1` |

Credits for the figures above, in each publisher's own words as the licence registry holds them:

- Nitrogen dioxide: © Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL).
- The three measures of homes: Contains public sector information licensed under the Open Government Licence v3.0.
- The geography behind each: Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

`[year]` is the registry's own placeholder. No year was made up.

Every figure is the figure of the first build. What each cannot see is in `build.json`, and in [the first build's page](m1-first-build.md), section 3.

**No tag has a score.** Core gives a tag a score once 60 in 100 of its recipe has a figure.

| Tag | Of its recipe | State of its row |
|---|---|---|
| Historic character | 50 in 100: homes built before 1919 | `below_threshold` in 979 areas, `not_carried` in 23 |
| Leafy | 25 in 100: homes per hectare | `below_threshold` |
| Village feel | 20 in 100: homes built before 1919 | `below_threshold` in 979 areas, `not_carried` in 23 |
| Quiet residential | 15 in 100: homes per hectare | `below_threshold` |
| The other eight | None | `not_carried` |

## 4. What was built and is not in the release

Each of these has a figure and a row of evidence for all 1,002 areas, from every home of each area. The first four are worked out at every build and left out by the name of a rule. `build.json` records the rule and what the measure waits on, and `coverage.md` beside the release says both in a section of its own. The rest join no build.

| Measure | Areas with a figure | Why it is not in the release | What it waits on |
|---|---|---|---|
| Public parks and gardens as a share of the area, `green_cover` | 1,002 | `measure_is_as_core_says`. Core names it public green space | A name in core that says parks and gardens. Which reading the id carries: the share of land, as built, or the share of homes within 300 metres of a park, as the design of the vibes words it. The check of 20 named commons |
| Transport noise, `noise_exposure` | 1,002 | `measure_is_as_core_says`. The file counts residents, and core's label says homes | A name in core that says residents |
| The nearest park of 2 ha, `park_proximity` | 1,002 | `measure_is_as_core_says`. It is a straight line to a marked way in, and core's label says a walk | A name in core that says a straight line, or a walk worked out on a network of streets. The check of 20 named commons |
| Water close by, `water_access` | 1,002 | `measure_is_as_core_says`. It counts homes and a lake, and core's label says the area, a river or a canal | Homes or land, and whether a lake counts. A registered source for the bank of wide tidal water, or a name that says from the middle of the water. A person to look at each long straight stretch, which may run under the ground |
| The nearest park of 20 ha | 1,002 | Core has no feature for it | A row in the catalogue |
| Fine particles, PM2.5 | 1,002 | Core has no feature for it. The registry asks that it has a place of its own on the list of features before it is used. Its file is in the list `m2-living`, which this build does not take | A row in the catalogue, and the list named to the build |
| Main roads | 1,002 | Core has no feature for it | A row in the catalogue |
| The price of a home | 1,002, for a home of any kind | The licence registry holds its source for validation only. Nothing of it is on this page or in a test | A change to the registry, then a row in the catalogue |

No figure of these is on this page. London's lowest, middle and highest for each, but for the price, is held by the test of the measure on the real files, with its publisher's credit. Every figure is beside the release.

**Water close by is not to be carried as it stands, whatever it is named.** It is measured to a line along the middle of the water. A check counted what that does: beside wide tidal water, areas with homes on the bank read nought. And where the file draws a long straight stretch, which may be water in a pipe, areas read high from water nobody can see. The counts are beside the release.

Asked of the API, a wish for a measure that is left out is refused: a ranking by green cover, by noise, by the nearest park or by water answers `422`, and a ranking by the tag Leafy, Waterside or Quiet residential leaves every area unranked. None is answered with a figure.

## 5. What the two checks found, and what was done

Two checks read the build `lon-2026-09-24-02`. One worked every figure out a second way. The other changed the release after it was built and looked for what noticed. Every figure agreed, in all 1,002 areas, for every measure. What was found is what the figures were called, what the release could be made to say, and what the pages held.

| # | Finding | How grave | What was done |
|---|---|---|---|
| 1 | The release scored the tag Leafy by a recipe the design of the vibes says is not shipped | Major | Leafy has no score: green cover is left out, so under 60 in 100 of the recipe has a figure. Core still holds the recipe. A test on the real files fails if any tag gains a score. What becomes of the recipe is the founder's: section 10 |
| 2 | Green cover in the release is not the measure the design defines, and the check of commons has not been made | Major | Left out of the release. `build.json` and the coverage report say that it waits on both. Neither was decided here |
| 3 | The product said an area is greener than others, from a figure that counts public parks alone | Major | Green cover carries a name of its own, "Public parks and gardens as a share of the area". It is not core's, so a build leaves it out. Core is not changed |
| 4 | Water close by reads nought beside wide tidal water, and high where a line may run under the ground | Major | It was not in the release and is not. Its name now says that it is measured to the centre line, and what it waits on is written beside its rule |
| 5 | Two lines of this page ranked named boroughs, with no figure and no credit | Major | Taken out. This page names no borough |
| 6 | Three figures of price were in a tracked test, of a source held for validation only | Major | Taken out. The test holds counts, states, and that every figure is the publisher's own cell |
| 7 | `burro-release check` passed a release whose source the registry had gated, or no longer allowed for scoring | Major | The check asks the registry again, as it stands on the day: `input_is_allowed` |
| 8 | A percentile could be changed and neither judge saw it | Major | The check works each percentile and each tag out again with core's own code: `percentile_is_cores`, `tag_is_cores`. It holds the share of an area behind a figure to its row: `row_holds_the_coverage` |
| 9 | The service serves a damaged release once `hashes.json` is rewritten beside it | Major | Not closed in code: it is a decision. [ADR 0018](../../adr/0018-a-real-release-is-served-with-its-evidence.md) and [the guide](../../data-builds.md) now say that only `burro-release check` is proof until a release is approved, and the guide runs it before the service. Section 10 |
| 10 | 37 files with no receipt were opened by their path, and a kept test opened them again | Major | The module of tests is skipped, with the store or without it. No file with no receipt is opened by any test. What was read then is still what the two lists state. Section 10 |
| 11 | All three distances are straight lines, and only one name said so | Minor | Each name says it, and says what is measured to: a marked way in, or a centre line |
| 12 | No publisher's total is in the store for any new measure | Minor | Not closed. No new measure is in the release. Section 11 |
| 13 | Two small choices move a last digit and were in no sentence | Minor | The sentence of the method says what the median is where the homes divide in half. The definition of homes built before 1919 says what the share is a share of. No figure moved |
| 14 | The evidence and the catalogue of green cover name the census table of homes | Minor | Not changed. The table is what the coverage of the figure is counted by. Green cover is in no release. Section 8, row 7 |
| 15 | The language's own rounding was used for hectares and for coverage | Minor | Each is kept with a half taken upward, as a figure is. No figure moved |
| 16 | The check cannot tell which square of the grid a figure lies on | Minor | Not closed. ADR 0018 says so. No measure in the release is cut to squares |
| 17 | The check did not hold the receipts in the evidence, or the lock, to the receipts that were committed | Minor | It holds a receipt to the lock by the whole hash and the size, and to the committed receipt where it is given the folder: `burro-release check --receipts` |
| 18 | The row of a tag was held to no method and no file | Minor | It is held to the method of a tag and to the files of the measures of its recipe |
| 19 | Names, outlines, credits and the sentence of a measure could be changed with the hashes | Minor | The credit and the licence of a source are held to the registry: `credit_is_the_registrys`. A name, an outline and a sentence are held by committed hashes alone, and ADR 0018 says so |
| 20 | The page on the files said three things that were no longer so | Minor | Each section says, under a date, what has changed since it was written |
| 21 | The page said six sheets about residents are never opened, and gave their rows and columns | Minor | The page says that the step `describe` read the first row of each and counted the rest, and that no step of a build opens one. Whether `describe` should ask the gate is a decision: section 10 |
| 22 | Two phrases of a page said where the work was done | Minor | Taken out. A page says what is known, and not where it was found out |
| 23 | The release said it was built at a time that had not come | Minor | This build gives the hour of the last commit, which had passed. The guide says to |
| 24 | This page held tables of rank correlations made from real files | Minor | Taken out. Section 6 says in words what they show. The tables are beside the release |
| 25 | Words of publishers' notes are quoted in a tracked page, and no licence file was saved | Minor | Not changed. No source whose entry asks for a saved licence file stands behind this release. Section 10 |
| 26 | Fine particles were worked out before the registry's condition for them is met | Minor | Not changed. The measure joins no build. Whether working a figure out is use is a decision: section 10 |
| 27 | This page counted its own changes two ways | Minor | Section 7 counts them once |
| 28 | `build.json` said the lists in the order they were typed | Minor | It says them in the order of their names. Built with the lists turned round, all 18 files are the same |
| 29 | The suite takes 42 seconds, and the rule is 30 | Minor | Not closed. Section 11 gives the time. The rule is the founder's to change |
| 30 | The price figures were reported twice, once by each check | | Counted once, as row 6 |
| 31 | What was looked for and not found: a column about residents read, a figure that is not believable, a build that does not repeat | | Nothing was needed |

What was taken out of this page and of a test is still in the history of the branch, in the commits that put it there. Whether that history is published as it is, is the founder's to say.

One thing was found that no check had: a test of the whole build failed once in some runs. It made its made-up files twice, a moment apart, and the zip held the time of the clock, so the two had two hashes. Every made-up zip is now written at one fixed time.

## 6. Do the measures tell areas apart

In part. What follows is said in words. The rank correlations behind it were worked out across the 1,002 areas, and each was worked out again by a check. The tables are beside the release.

- **Three of the four measures in the release are close to one measure.** Nitrogen dioxide, homes per hectare and flats put the areas in much the same order, and each follows how central an area is. With how central taken out, what is left between them is weak.
- **Homes built before 1919 follows the centre less**, and says something of its own.
- **So the release holds about two things, and not four**: how central and built up an area is, and how old its homes are.
- **Of what is left out, fine particles is nitrogen dioxide again.** A rank on both counts the centre twice.
- **Transport noise and main roads agree in part**, and each follows the centre in part. Noise agrees with flats more than with anything else.
- **Green cover, both distances to a park, and water close by do not follow the centre.** They are what would make the map say something new. Green cover and the nearest park are of one file and agree: where more of an area is park, a park is nearer.
- **Water close by agrees with nothing**, and reads nought in about half the areas.

**What this means for a vibe.** A vibe built on the air and the homes alone would be a vibe of how central an area is, whatever it was named.

## 7. What changed in the code, and is the founder's to approve

Each is in a commit of its own, with its test. Nothing of core, of the contract, of the registry or of the catalogue was changed. Four changes of the build before this one stand as they were: the check lets a measure in squares rest on the file of each square, a build takes more than one list, the nearest park and water join the list of a build, and the receipt of File 8 is committed.

| # | What | Commit | To go back |
|---|---|---|---|
| 1 | Green cover carries a name of its own, so a build leaves it out | `78bee15` | Revert it. Green cover and Leafy come back into a release |
| 2 | A measure says what it waits on. `build.json` and the coverage report say why a measure that was worked out is left out. The step `coverage` takes `--build` | `2b18118` | Revert it |
| 3 | The check asks the licence registry again | `88cac40` | Revert it |
| 4 | The check works each percentile and each tag out again | `2a3cda9` | Revert it |
| 5 | No figure of price is held in a test | `0d2dae3` | Revert it |
| 6 | The tests that open a file with no receipt are skipped | `ddc584c` | Take the skip out |
| 7 | Each name and sentence says the choice a second reading could miss | `7dc0bfc` | Revert it. The sentence of homes built before 1919 is in the catalogue of a release |
| 8 | Land and coverage are kept with a half taken upward | `d78b767` | Revert it |
| 9 | The check holds the receipts, the row of a tag and the credits. `burro-release check` takes `--receipts` | `769b45f` | Revert it |
| 10 | `build.json` is the same whatever order the lists are given in | `cff592d` | Revert it |
| 11 | The made-up tables of homes are the same bytes whenever a test makes them | `5bf2169` | Revert it |
| 12 | ADR 0018, the guide and the page on the files say what is so | `78874a1` | |

Two of these change what a step does when something is wrong. A build whose release cites a source for a use the registry does not allow now stops at the check, with exit code 1, where it stopped at the step that writes, with exit code 2. And a release that credits a source otherwise than the registry does fails the check: so a release built before the registry changes a credit must be built again.

## 8. What looks wrong, and what to look at first

In the order to look.

| # | What | Why it matters | What would settle it |
|---|---|---|---|
| 1 | **The map has on it what it had after the first build, and no more.** Quiet, green, water and price are each worked out, and each waits on a decision | Seven measures are built and none can be seen. No file is missing | Section 10, rows 1 to 6 |
| 2 | **The service is not proof that a release is what was built.** It holds a release to `hashes.json`, which stands beside it and is signed by nobody | A person who changes a release and then its hashes gets it served. `burro-release check` finds a changed figure, percentile, tag, credit or receipt. It does not find a changed name, outline or sentence | Run `burro-release check` before the service, on the folder as it stands. Then decide: section 10, row 7 |
| 3 | **A sentence that asks for green space is answered with a ranking by nitrogen dioxide.** The reader makes a wish for green cover, the release does not hold it, and the answer says the wish was rejected as `not_in_release`. The ranking that comes back is by the weight that is left, which is the air | The answer is honest in its parts. A person who does not read the rejected wish sees a ranked list under their own words | Look at what the website shows for it. Decide whether a wish that is rejected should leave the list empty |
| 4 | **Green cover as built reads nought in 134 areas**, and the design's own reading of the same id gives another order of areas | The two readings are different measures. A check found that about half the areas move a long way in the order between them | Decide which the id carries. Make the check of commons. Then look at the map |
| 5 | **Three of the four measures in the release are close to one measure.** Section 6 | Sliders for nitrogen dioxide, homes per hectare and flats move the same areas | Decide which of them a person is shown first. Say on the screen that nitrogen dioxide follows the centre |
| 6 | **The lock holds six files that no step reads**, 3.1 GB of them | The lock is every file of the lists that has a receipt. It says more than was read. The evidence names only what a figure rests on | Decide whether a build names its own files, as the pipeline design's `build/sources.toml` would |
| 7 | **A row of evidence names every file that stood behind it, the weights among them**, so the page of an area would print the census as a source of green cover, which is land over land | The census table is what the coverage is counted by, and is no part of the figure | The design asks that a fact carry its evidence in the next schema. Say then which files a figure rests on and which its coverage |
| 8 | **Everything the first build listed still stands**: the 23 areas with no figure for homes built before 1919, the one date beside every source of a fact, `[year]` in three credits, homes weighed as at 2021 | [The first build's page](m1-first-build.md), section 7 | |

## 9. How it was checked

| Check | Result |
|---|---|
| `make ci`: the registry, lint, strict types, and every test | Passes: 7,507 tests passed, 147 were skipped, and 14 are expected to fail. Section 11 gives the time |
| The tests on the real files, with the store named | All pass. Those of the files with no receipt are skipped |
| Built twice from the same files and commit, with the lists given in either order | The 18 files are the same byte for byte. The step printed the same lines |
| Every figure of every measure, against what the second build worked out | Each of 11 measures was worked out again for all 1,002 areas by the code as it stands. Every figure, every state and every share covered is the same |
| `burro-release check`, with `--receipts data/receipts` | Passes: `1002 areas (1002 rankable), 4 measures, 0 destinations, 0 places, 0 stations, real, a preview, with evidence behind every fact` |
| `check`, that no fact lacks evidence | 4,987 facts, 51,102 rows, 9 files, no finding |
| The release of the build before, damaged as the checks damaged it | With the registry as it stands it passes. With the source of the sites gated, or its use for scoring withdrawn, 2,005 findings. With one percentile moved, one credit changed, one receipt changed, or one row of a tag naming another method, and every hash made to agree: each is found |
| The API on the release, through the test client | The areas, the outlines, every one of 1,002 areas by its id, one by its slug, a ranking by each measure each way that core allows, a ranking by three tags, the sentences of a ranking, and four sentences a person might type. Every response said `synthetic: false` and `preview: true`, in `meta` and in the headers. No log line held an area's id or the id of a fact |
| Every fact, followed | Each of the 4,987 facts the API serves was followed to its row of evidence, to every file the row names, to the lock, to the receipt in `data/receipts/`, and to the hash of the file in the store |
| The store | Read, and never written to. It held 87 files before and after, each of the same size and time |

## 10. What is needed from the founder

| # | What | Why |
|---|---|---|
| 1 | Approve or change core's label for transport noise | It brings noise into the next build. Nothing else keeps it out |
| 2 | Decide which reading the id `green_cover` carries, and its name in core. Give the list of 20 commons, heaths and forests | It brings green cover in. The check of commons stands before any figure of parks |
| 3 | Decide what becomes of the recipe of Leafy that core holds, before green cover is carried | The day green cover is carried, core scores Leafy on 70 in 100 of a recipe the design has withdrawn |
| 4 | Decide whether a straight line to a park may be shown, and under what name, or whether it waits for a walk | It brings the nearest park in |
| 5 | Decide whether water close by counts homes or land, whether a lake counts, and how the bank of wide tidal water is settled | The measure is not to be carried until the bank is settled |
| 6 | Decide whether core gains a feature for fine particles, for main roads and for the nearest large park. Decide whether the price of a home may be shown at all | None can be carried without one. The price needs a change to the registry first |
| 7 | Decide how the service is held to a release that was approved: the hashes committed and read from outside the folder, or the check of evidence run when the service starts | Section 8, row 2 |
| 8 | Decide whether the part of a file that dates it may be read before a receipt exists | 37 files have no receipt because no edition could be stated before one was opened. The tests that read them are skipped until this is said |
| 9 | Decide whether a test may hold three figures of a source held for validation only, and whether a figure of fine particles may be worked out and held in a test before the list of features has it | The first was taken out. The second was left |
| 10 | Decide whether the step `describe` asks the gate, and passes over a sheet the registry keeps apart | It read the first row of six sheets about residents |
| 11 | Decide which words of a publisher's credit are shown, and whether the licence files inside the zips are committed | Four registry entries ask for a saved licence file at first ingest. None stands behind this release |
| 12 | Decide whether a source is registered for validation, to hold each new measure to a published total | Section 11 |
| 13 | Raise the limit of 30 seconds for the tests, or give the generated tests a smaller sample | Section 11 |
| 14 | Approve or revert the changes of section 7, and those of the build before | Each changes what a check or a build does |
| 15 | Decide whether this page, the page on the files and the history behind them are published | Each holds counts made from publishers' files, with the credits |
| 16 | Everything the first build asked for, which still stands | [The first build's page](m1-first-build.md), section 10 |

## 11. What was not checked, and what was not built

| Not checked, or not built | Why |
|---|---|
| Any figure, by a person | None has been held against a map, a visit or a publisher's page |
| Any new measure against a published total | No file in the store holds a row for a borough, for London or for England. What was held in its place is the arithmetic: the lines as drawn against the length the file states, every figure of a grid between the lowest and the highest of its own squares, and the land of each LSOA measured two ways. None is a check of the file |
| The website on this release | It was not built on it or opened in a browser. The contract did not change, and the API was driven through the test client. The release holds what the first build's held, which was opened in a browser |
| The tests of the website and of the iPhone app | They were not run. Neither was changed by this work |
| A build on the platform of record | Nothing ran in hosted CI. Nothing was pushed |
| The design's reading of green cover | It was worked out once by a check, in a scratch program. No module of the pipeline works it out |
| That the whole suite runs in under 30 seconds | It does not. The tests alone took 43 seconds before this work, and 43 to 53 seconds in four runs after it. `make ci` as a whole took 51 seconds before and after. The time of a run moves by more than this work adds: the tests it adds take under a second together |
| A list of the build that names only what the build reads | The lock holds every file of the two lists that has a receipt. Section 8, row 6 |
| Every other thing the first build did not check | [The first build's page](m1-first-build.md), section 9 |

## 12. How to see it

In a working copy of the branch that holds this page, with everything committed, and with `BURRO_STORE_FOLDER` naming the folder that is the store:

| # | Where | Run | You should see |
|---|---|---|---|
| 1 | The top of the repository | `make preview ARGS="--release-id lon-2026-09-24-03 --built-at 2026-09-24T01:00:00Z --out data/releases --list m1 --list m2-places"` | Four lines of `step=derive status=ok`, four of `step=derive status=skipped`, and a last line that starts `step=report status=ok`. It takes 22 seconds. If the folder is there already, skip this step or give a new id |
| 2 | The same | `uv run burro-release check data/releases/lon-2026-09-24-03 --receipts data/receipts` | `lon-2026-09-24-03: 1002 areas (1002 rankable), 4 measures, 0 destinations, 0 places, 0 stations, real, a preview, with evidence behind every fact` |
| 3 | A first terminal, at the top of the repository | `BURRO_RELEASE_DIR=data/releases/lon-2026-09-24-03 make api` | One line that holds `"preview":true` and `"synthetic":false` |
| 4 | A second terminal, in `apps/web` | `NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:8000 npm run build`, then `NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:8000 npx next start -H 127.0.0.1 -p 3000` | The website on `http://localhost:3000`, with the banner that says it is a preview |

Run step 2 before step 3, each time. [The guide to data builds](../../data-builds.md), sections 15 and 16, says what to do first and what to do when a step stops. Built at another commit, the lock has another hash, and the manifest, the evidence and the coverage have the hashes of section 1.
