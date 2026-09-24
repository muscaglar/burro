# The first real build of London

Status: built on 2026-09-24, from the files fetched on 2026-09-23 for list `m1`. It takes the place of the build of 2026-09-23, which two checks found wanting. It is a dated snapshot. [The second build](m2-second-build.md) followed it the same day, and this page was left as it was written: File 8 of the Indices of Deprivation has had a receipt since.

**This is a first build, for the founder's eyes. No person has checked anything in it.** No figure here has been held against a map, a visit or a publisher's own page. Every count was made by a program. It is a development build: it is never served to the public. Where a figure looks wrong, that is a finding and it is written down as one. Nothing was smoothed.

No figure here is said of a named neighbourhood, of a named area or of a named borough. An area is one of the statistics office's 1,002 middle layer super output areas (MSOAs) of London, under the office's own label, which is its borough and a number. The only figures on this page are London's lowest, middle and highest for each measure, which the tests hold too. Every other figure is beside the release, in a folder that git ignores.

## 0. In short

| Question | Answer |
|---|---|
| What was built | One release, `lon-2026-09-24-01`: 1,002 areas, their outlines, and four measures |
| How many areas have a figure | Nitrogen dioxide, homes per hectare and flats: all 1,002. Homes built before 1919: 979. The other 23 have no figure, and the release says why |
| What it says of itself | That it is real, `synthetic: false`, and that it is not finished, `preview: true`. The API says both on every response |
| What is not in it | Transport noise, which is the fifth measure. Journeys, costs, stations, places to reach, vibes and names of neighbourhoods. Nothing stands in for any of them |
| What changed since the build of 2026-09-23 | Section 4. The three measures of homes are now the publisher's own count for the area. A dash is never given as nought. A figure is held in its evidence. The service refuses a release with no evidence beside it |
| Does every figure trace | By id and by value. Each of the 4,987 facts has a row of evidence that names its method and its files and, for a figure, holds the figure. Each file is in the lock, has a receipt, and has the hash its receipt gives |
| Does the build repeat | Yes. Built twice from the same files and the same commit, all 18 files written are the same byte for byte |
| Does the product open it | Yes. `burro-release check` passes. The API serves it. The website was built on it and opened in a browser |
| What to look at first | Section 7 |
| How to see it | [The guide to data builds](../../data-builds.md), section 15 |

## 1. What was built

| Thing | Value |
|---|---|
| Release | `lon-2026-09-24-01`, built at `2026-09-24T09:00:00Z`, which is an input and not the clock |
| Command | `make preview ARGS="--release-id lon-2026-09-24-01 --built-at 2026-09-24T09:00:00Z --out data/releases"` |
| Commit of the code | `18b67b2`, read from the repository by the step. The working copy had no change |
| Packages | Not held by hash: no lockfile is committed. So it is a development build |
| `manifest.json`, SHA-256 | `a4a2f7230c8aa7f0774465db9d164828c5c5640852e6300ed6a4f59301a78b8e` |
| `evidence.json`, SHA-256 | `0177d8a88f68db65e6ec6a2419eed585e5759824f5eef2464260382049458f74` |
| `lock.json`, SHA-256 | `6c97eb76fa867321309439434d5f74c527c882f93be329fe39db0de5fe3c50f9` |
| `coverage.json`, SHA-256 | `f116a631452baf5930279a9e932ab7854eab44ae43675b86ee5e4daec5dbc908` |
| Schema and catalogue | Both at version 1 |

The first three hashes are what `hashes.json` holds. The hash of the lock moves with the commit. The other three do not, while the code works the same figures out.

Counted, from the files and held to no number in the code:

| Thing | Count |
|---|---|
| Output areas | 26,369 |
| LSOAs | 4,994 |
| MSOAs, which are the areas | 1,002 |
| Boroughs, the City among them | 33 |
| Homes: households at the census of 2021 | 3,423,767 |
| Homes on the council tax lists at 31 March 2025, as the rows of the 1,002 areas add up | 3,837,870 |
| Facts the release would show | 4,987: a label for each of 1,002 areas, and 3,985 figures |
| Rows of evidence | 51,102: one for every pair of an area and a thing Burro measures |

What was written, in two folders. Git ignores both.

| File | Bytes | What it holds |
|---|---|---|
| `lon-2026-09-24-01/neighbourhoods.json` | 271,357 | Each area: its label, its borough, a point inside it, its neighbours |
| `geometry.json` | 1,724,927 | Each area's outline |
| `catalogue.json` | 3,556 | The four measures: name, unit, period, every source, and the sentence a methods page prints |
| `features.json` | 411,404 | A figure for every area and measure, or none, with its percentile and its coverage |
| `tags.json` | 1,109,225 | A row for every area and tag. No tag has a score |
| `cost.json`, `destinations.json`, `places.json` | 12, 20, 14 | Nothing |
| `stations.json` | 41 | Nothing, and no source |
| `travel.json` | 29,224 | Every area, no destination, no source |
| `manifest.json` | 4,636 | The release, its seven sources and the hash of every file above |
| `lon-2026-09-24-01-build/lock.json` | 2,008 | Every input by hash, and the commit |
| `evidence.json` | 12,580,734 | 51,102 rows. The row of a figure holds the figure |
| `hashes.json` | 286 | The hash of the manifest, of the evidence and of the lock |
| `coverage.json`, `coverage.md` | 6,185,896 and 151,589 | The state of every pair, and the report |
| `homes.json` | 22,046 | The homes of each area, which is what a share of London is a share of |
| `build.json` | 2,681 | What was carried, what was left out, and the rule that kept it out |

## 2. From which files

Ten files are in the lock. Nine were read. Each was fetched on 2026-09-23 and has a receipt in `data/receipts/`.

| File | Registry id | Publisher's name for it | Edition | The data is of | Bytes |
|---|---|---|---|---|---|
| `f-49321b95f212` | `ons-oa21-lsoa21-msoa21-lad22-lookup` | `OA21_LAD22_LSOA21_MSOA21_LEP22_EN_LU_V2_...csv` | V2 | December 2022 | 22,281,470 |
| `f-af7b512615ea` | `ons-census-2021-housing-tables` | `census2021-ts044.zip` | Census 2021 TS044 | 21 March 2021 | 3,077,120 |
| `f-7727e4b03845` | `ons-output-areas-2021` | `Output_Areas_2021_EW_BGC_V2_...gpkg` | BGC V2 | December 2021 | 128,831,488 |
| `f-9f549e33f46b` | `ons-lsoa-2021` | `Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5_...gpkg` | BGC V5 | December 2021 | 50,098,176 |
| `f-00e1d0532798` | `ons-oa-pwc-2021` | `Output_Areas_(December_2021)_EW_Population_Weighted_Centroids_(V4)_.csv` | V4 | December 2021 | 22,030,298 |
| `f-e1979a4196e2` | `voa-council-tax-stock-of-properties` | `CTSOP1.1.zip` | 2025 | 31 March 2025 | 749,909 |
| `f-c8891afc8f10` | the same | `CTSOP3.1.zip` | 2025 | 31 March 2025 | 7,899,033 |
| `f-c4e32565aeb1` | the same | `CTSOP4.1.zip` | 2025 | 31 March 2025 | 6,156,819 |
| `f-d169e49479d8` | `defra-pcm-background-air` | `mapno22024.csv` | 2024 | 2024 | 7,900,343 |

| File | Why it is not among the nine |
|---|---|
| `f-89acdc47cdb1`, the output area boundaries at full resolution, 1.17 GB | It is in the lock, because the list names it and it has a receipt. No step reads it |
| File 8 of the Indices of Deprivation, `mhclg-iod-2025-underlying-indicators` | It is in the store and has no receipt. It is in no lock, and no step may read it |

From the census table one column is read: the count of all households in each output area. It is the weight behind nitrogen dioxide, and it says which output areas an area takes in. The three measures of homes no longer rest on it. No column that describes who lives anywhere is read, from this file or from any other.

**What a receipt does not yet carry.** The design of a receipt asks for the geography of a file, read from the file, and for the name and hash of each member of a zip that is read. All 24 receipts in `data/receipts/` have `geography: null`, and the 10 receipts of a zip have no member. Fetch writes a receipt and nothing else may change one. So the trace rests on two other things: the hash of a zip fixes what is inside it, and each measure stops the build if an area of the lookup of 2021 has no row in its file.

## 3. The measures

| Measure | Unit | The data is of | Areas with a figure | Areas without | Lowest | Middle | Highest | Method |
|---|---|---|---|---|---|---|---|---|
| Modelled annual mean nitrogen dioxide | µg/m³ | 2024 | 1,002 | 0 | 8.8 | 17.4 | 32.7 | `grid_at_homes@1`, marked modelled |
| Homes per hectare | per ha | 31 March 2025 | 1,002 | 0 | 1.3 | 32.2 | 154.8 | `area_row_ratio@1` over `land_inside_outline@1` |
| Flats as a share of homes | % | 31 March 2025 | 1,002 | 0 | 1.7 | 53.5 | 99.0 | `area_row_ratio@1` |
| Homes built before 1919 | % | 31 March 2025 | 979 | 23, withheld by the publisher | 0.0 | 23.4 | 97.2 | `area_row_ratio@1` |
| Transport noise | % | 2021 | **None. It is not in the release** | 1,002 | | | | `lsoa_value_by_homes@1`, marked averaged |

Credits for the figures above, in each publisher's own words as the licence registry holds them:

- Nitrogen dioxide: © Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL). Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].
- The three measures of homes: Contains public sector information licensed under the Open Government Licence v3.0. Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

`[year]` is the registry's own placeholder. Which year stands there is the founder's to say, and none was made up.

How each figure is worked out, and what changed:

| Measure | How | What changed on 2026-09-24 |
|---|---|---|
| Nitrogen dioxide | The value of the square each output area's centre stands on, averaged by households at the census of 2021 | Nothing but the rounding of a half |
| Homes per hectare | The publisher's own count of homes for the MSOA, over the land inside the outlines of its LSOAs | The count was the sum of the rows of 4 to 8 LSOAs, each rounded to 10. It is now the MSOA's own row, rounded once |
| Flats | The publisher's own count of flats for the MSOA, over its own count of homes | The same |
| Homes built before 1919 | The publisher's own counts for the two build periods before 1919, over its own count of homes that have a build period | The same. And an area whose old homes are all behind a dash has no figure, where it had 0.0 |

- Every figure is given to one decimal place, with a half taken upward. The website prints a percentage as a whole number.
- Homes built before 1919 covers 764 areas in full and 215 in part, because a home with no recorded build period is left out. The least covered area has 78 in 100 of its homes behind its figure. 21 areas read 0.0, and in each the publisher wrote nought for both periods.
- A tag needs 60 in 100 of its recipe to have a figure. No tag has that, so core gives no tag a score. Nothing was taken out by hand.

What each figure cannot see, as its module holds it for a screen:

| Measure | It cannot see |
|---|---|
| Nitrogen dioxide | It is a model's estimate for a square one kilometre wide, not a reading. It cannot tell a home on a main road from one on a quiet street in the same square. Homes are weighed as they stood at the census of 2021 |
| Homes per hectare | The land is everything inside the boundary: roads, railways, parks and water that is not tidal. It cannot see how tall a building is, or whether a home is lived in |
| Flats | A home of no recorded kind counts as a home and not as a flat, so where fewer kinds are recorded the share reads too low. It cannot tell a tower from a converted house |
| Homes built before 1919 | It counts the build period that is recorded, rounded to 10 homes, and leaves out homes with none. It cannot see what state a home is in |

The contract has no place for these words on a feature, so the release does not carry them. They are in `build.json`.

## 4. What the two checks found, and what was done

Two checks read the first build, changed it and worked its figures out another way. Neither was made by whoever built it. Each finding is here with what became of it.

| # | Finding | How grave | What was done |
|---|---|---|---|
| 1 | Figures of noise, worked out from a file with no receipt, were in a tracked test | Blocker | Taken out. The test holds the refusal and no figure. The page on the files says what was done |
| 2 | Figures of one area were in tracked files that said they held none: the City of London is one area | Blocker | Taken out of both tests and of this page |
| 3 | Six in ten figures of homes differed in the last digit from the publisher's own row for the same area | Major | The figure is now read from the publisher's own row. The rows of the LSOAs are kept to hold it to |
| 4 | 31 of the 52 areas that read 0.0 for homes before 1919 were not nought | Major | 0.0 is given only where the publisher wrote nought for both periods: 21 areas. 23 areas have no figure. The other 8 have the publisher's own figure |
| 5 | The evidence proved that a fact had a row, and not that its figure was right | Major | The row of a figure holds the figure, and the checks compare it. The build writes the hash of the manifest, of the evidence and of the lock, and the checks hold all three |
| 6 | The service and `burro-release check` never read the evidence, so a release with none was served | Major | Both refuse a release that is not made up unless its build stands beside it, unchanged. `burro-release check` reads the evidence too |
| 7 | A release was finished on its own word | Major | A release with no journey, no place to reach, no cost or no station says it is a preview, or core refuses it |
| 8 | The tests and this page held tables of figures for named boroughs, with no credit | Major | Each test holds the counts, one sum and three figures. This page holds the three figures of each measure, with the credit under them |
| 9 | A page built on the made-up release said "made up" over real figures | Major | A page gives way to a notice, and shows no figure, once an answer is of another kind of data than the page was built on. Driven in a browser |
| 10 | A receipt does not say which census its codes follow, nor which file of a zip was read | Minor | Not changed: fetch alone writes a receipt. Said in section 2 |
| 11 | The report said weights of 2021 move no figure. They can move nitrogen dioxide | Minor | Corrected here, and said in what the figure cannot see |
| 12 | What a dash means rested on reasoning | Minor | The four rules are in `derive/rounded_counts.py`. The build holds every area to them, and a test holds every MSOA of England |
| 13 | The sums of the areas ran a little above the publisher's row for London | Minor | The areas are now the publisher's own rows. A test holds their sum to the row for London, within 0.5 in 100. The build itself does not yet: section 9 |
| 14 | Nothing published is in the store to hold land, nitrogen dioxide or noise to | Minor | Not closed. Section 9 |
| 15 | A figure on a half was rounded to the even digit | Minor | A half is taken upward, by `to_places`. The sentence of each measure says so |
| 16 | Three things to settle before noise becomes a figure | Minor | Not closed: they wait on the receipt. Section 10 |
| 17 | Two committed pages held figures made from real files, with no publisher's statement | Minor | Both now carry each publisher's credit. Whether either is published is the founder's to say |
| 18 | The pages said a person had checked, and other things that were not so | Minor | Corrected, here and on the page on the files |
| 19 | Core held no figure to a range, and no outline to a place | Minor | A percentage is held from 0 to 100, any other figure at or above nought, and an outline to its own area. London is not held to a box on the map: section 9 |
| 20 | The branch is behind `data-m0`, which has tightened the rules for a receipt | Minor | Not done. Section 10 |
| 21 | The step's own example left publishers' files where git did not ignore them | Minor | `preview` and `cells` refuse an `--out` or a `--work` inside the repository, but for `data/releases/` and `scratch/`, and git ignores both |

**Which way of working a figure out is right.** The checks worked each figure of homes out from the publisher's own row for the MSOA, and the build had added up the rows of its LSOAs. The notes workbook in each zip was read for this: it names the columns, and says nothing of rounding or of a dash. So the file's own rows decide. The row of an MSOA is within 5 of the sum of its LSOAs for each LSOA and 5 for itself, in every one of England's 6,856 MSOAs, which is what one rounding of each row gives. So the MSOA's row is rounded once, a sum of LSOA rows takes in one rounding for each, and the MSOA's row is the nearer to what was counted. It is also the number a reader finds who opens the publisher's table. Nobody has read the publisher's page.

## 5. Coverage

`coverage.md` beside the release is the report. It was written from `coverage.json`, which holds a state for every one of the 51,102 pairs of an area and a thing Burro measures. Every pair has a row of evidence behind it. The report names the boroughs and the areas with a gap. This page does not.

| Measure | With a figure, in full | In part | Withheld by the publisher | Not carried |
|---|---|---|---|---|
| The label of an area, and its outline | 1,002 | 0 | 0 | 0 |
| Nitrogen dioxide | 1,002 | 0 | 0 | 0 |
| Homes per hectare | 1,002 | 0 | 0 | 0 |
| Flats | 1,002 | 0 | 0 | 0 |
| Homes built before 1919 | 764 | 215 | 23 | 0 |
| Transport noise | 0 | 0 | 0 | 1,002 |
| Each of the other 18 measures core knows | 0 | 0 | 0 | 1,002 |
| Each of the 12 tags | 0 | 0 | 0 | 1,002. Four have some of their parts and too few. Eight have none |
| A journey, by each of 3 modes | 0 | 0 | 0 | 1,002 |
| A cost, for each of 10 kinds of home | 0 | 0 | 0 | 1,002 |
| The nearest station | 0 | 0 | 0 | 1,002 |

The report now gives "This build does not work the measure out" as the reason for a measure that is not carried. `build.json` gives the rule that kept noise out.

## 6. What the contract insisted on, and what was changed

Each change below has its test, and is the founder's to approve. [ADR 0017](../../adr/0017-a-preview-says-it-is-one.md) and [ADR 0018](../../adr/0018-a-real-release-is-served-with-its-evidence.md) record them, both as proposed.

| # | The rule | What was changed | Commit |
|---|---|---|---|
| 1 | `travel.json` and `stations.json` had to name a source and a date, whatever they held | A preview may leave both unsaid, where the file holds nothing | `105cd19` |
| 2 | Nothing said that a release was unfinished | The manifest says `preview`, and every response carries it | `105cd19`, `99fae1d` |
| 3 | A release was finished on its own word | A new rule of core, `finished_release_is_whole`: a release with no journey's end, no place to reach, no cost or no station is a preview | `1694af1` |
| 4 | `values_are_in_range` held no figure of a measure | It holds a percentage from 0 to 100, any other figure at or above nought, and an outline and a neighbour to within half a degree of the point inside an area | `1694af1` |
| 5 | A release was opened with nothing beside it | A release that is not made up is served only with `hashes.json`, `evidence.json` and `lock.json` in the folder beside it, each as it was written. `open_served` in core holds them, for the service and for `burro-release check` | `18b67b2` |
| 6 | A row of evidence held no figure | The row of a measure holds its value, and the row of a tag its score. The canonical form of a row moved, and with it every hash of evidence | `d018832` |
| 7 | The step `check` took evidence and a lock | It takes the hashes of the build too, and refuses a release that is not made up without them | `18b67b2` |
| 8 | The state `not_carried` said "no cleared source" | It says that the build does not work the measure out | `9d2177f` |
| 9 | The design named five methods | A sixth, `area_row_ratio`, for a file that holds a row for the area itself | `235b443` |

What the contract insisted on and was **not** changed:

| # | The rule | What the release does | Why it was left |
|---|---|---|---|
| 10 | `travel.json` must give `cutoff_minutes`, the longest journey the release routed | It holds the contract's own 90, 60 and 60. No journey was routed | To leave it out changes what the service serves and the form the website draws. Contract, section 13 |
| 11 | Core's label for noise is "Share of homes at 55 dB or more of transport noise" | Noise is left out | The file counts residents. To change the label changes the catalogue, the synthetic release and every recorded answer. It touches rule 8, so it is the founder's |
| 12 | A fact has one date for all its sources | The date is the measure's | Section 7, row 3 |
| 13 | `schema_version` | It is still 1 | Another change in flight moves the schema. Whoever brings the two together gives the number |

## 7. What looks wrong, and what to look at first

In the order to look.

| # | What | Why it matters | What would settle it |
|---|---|---|---|
| 1 | **23 areas have no figure for homes built before 1919, and the map shows a gap there.** In each the publisher wrote a dash for one or both periods and no number, so the area has 1 to 8 old homes of some thousands | The share is above nought and under about half of one in 100. Rule 7 says a number that is not known is never nought. A gap is honest and is less than is known | Decide whether such an area is given no figure, as now, or the words "under 1 in 100", which the contract has no place for yet |
| 2 | **ADR 0018 changes what a release is served with.** The service refuses the release of 2026-09-23, because nothing was written beside it that holds its hashes | A release copied without its `-build` folder does not start. That is the point, and it is new | Read ADR 0018 and approve or change it |
| 3 | **The date beside a source is wrong for most sources.** The page of an area prints each source of a figure with the figure's one date. So it says "Lower layer Super Output Areas (December 2021). Data from 31 March 2025" beside homes per hectare | The contract gives a fact one date. The evidence holds the right date for each file, and the screen cannot show it | `evidence` on a fact, which the pipeline design asks of the next schema |
| 4 | **A budget, a journey or a vibe ranks nothing.** The three examples on the first page of the website each ask for one of these | It is what the engine does with a wish it cannot test, and it is honest. But the first thing a person tries shows an empty result | Use Settings to rank. Decide whether route 11 should offer only the tags a release can score |
| 5 | **The credits of three sources hold the words `[year]`** | No year was made up. The sources page shows the placeholder | Open the publisher's licence page and say which year is meant |
| 6 | **Homes of no recorded kind make the share of flats read low** where many homes have none. They are in the bottom of the share and not the top | The figure is a floor there | Decide whether to say so on the screen, or to divide by homes of known kind |
| 7 | **Nitrogen dioxide weighs homes as they stood in 2021.** Where homes have been built since, or stand empty, the weights are not where the homes of 2025 are | A checker found 123 areas with a fifth more homes on the list of 2025 than households in 2021, and that the squares under such an area can differ by several micrograms. How far a figure moves was not measured: no count of homes by output area for 2025 is in the store | A count of homes by output area for a later year, from a registered source |
| 8 | **Nitrogen dioxide is close to a measure of distance from the centre**, and its grid is coarse: 181 different values for 1,002 areas | Neighbours share a figure. It cannot show a main road | It is what the source is. Say so on the screen |
| 9 | **The page of an area is 1.7 MB**, and the built website is 4 GB | Each page draws all 1,002 outlines to show where the area is | A smaller drawing for the locator |
| 10 | **Every area can be ranked.** No rule decided it | The contract leaves out an area under 3,000 residents. A first build reads no count of residents | Say whether any area should be left out, and by what |
| 11 | **An area is an MSOA under the office's label** | It claims no name. It is no neighbourhood | Milestone M3 |

## 8. How it was checked

| Check | Result |
|---|---|
| `make ci`: the registry, lint, strict types, and every test | Passes: 6,954 tests passed, 71 were skipped, which are those that read the real files, and 14 are expected to fail. With the store named they run, and pass. Section 9 gives the time |
| The website's own check, `npm run check` | Passes |
| Built twice from the same files and commit | The 18 files are the same byte for byte. A test on made-up files holds the step to it, and so does one on the real files |
| `burro-release check` | Passes: `1002 areas (1002 rankable), 4 measures, 0 destinations, 0 places, 0 stations, real, a preview, with evidence behind every fact` |
| `check`, that no fact lacks evidence | 4,987 facts, 51,102 rows, 9 files, no finding |
| Every figure of homes against the publisher's own row | A test on the real files works each figure out again from the row of the MSOA and holds it to the one served. All agree |
| The sum of the areas against the publisher's row for London | Homes, flats and homes before 1919 are each within 0.5 in 100 |
| What a dash means | The four rules hold for every MSOA of England, for every count that is read: 4 counts of homes by build period, 3 of homes by kind, 1 of homes by band |
| The release, damaged | A figure raised with the manifest made to agree is refused by `burro-release check` and by the service. With the hashes made to agree too, `burro-release check` finds the figure. With no folder beside it, both refuse the release. Section 9 says what the service alone cannot see |
| The API on the release, through the test client | Every route tried answered. Every response said `synthetic: false` and `preview: true`. No log line held an area's id |
| The website, built on the release and opened in a browser at 1440 by 900 | 1,002 pages of areas were built. The banner says it is a preview, and no banner says it is made up. With a measure turned on in Settings, areas are ranked with a cited sentence on each card. With homes built before 1919 turned on, 979 areas are ranked and 23 are not |
| The website, read while the service held the made-up release | The page gave way to the notice "This page cannot be shown", and showed no figure |
| The store | Read, and never written to. It held 86 files before and after |

## 9. What was not checked, and what was not built

| Not checked, or not built | Why |
|---|---|
| Any figure, by a person | None has been held against a map, a visit or a publisher's page |
| What the publisher says of rounding and of a dash | The notes in each zip do not say. The publisher's page was not opened |
| Land, nitrogen dioxide and noise against a published total | Nothing published is in the store to hold them to. The statistics office's standard area measurements are not a registered source. The measures of homes are the only ones held to a publisher's total |
| A check of totals inside the build | The design asks for one, against the publisher's rows for London and for each borough. It is held by a test on the real files, and the build itself does not run it |
| London held to a box on the map | Every test builds its town under real ids and draws it in open sea. A box round London would refuse them all. An outline is held to its own area, so one area drawn elsewhere is caught, and a whole release drawn elsewhere is not |
| What the service alone cannot see | The service holds a release to its hashes and reads no evidence. A person who changes a release, and then its hashes, gets it served. `burro-release check` finds it. Once a release is approved its hashes are committed, and a change shows in the history |
| A value in the evidence of a label, an outline, a cost, a journey or a station | None is one number. The hashes hold them |
| A lock that says its commit was given by hand | Where there is no repository to read, the step takes the commit it is given. Nothing marks such a lock |
| The tests of the iPhone app | They were not run. The app was not changed by this work |
| A build on the platform of record | Nothing ran in hosted CI |
| The website at the width of a phone, and by keyboard | It was opened at 1440 by 900 only |
| That the whole suite runs in under 30 seconds | It does not. It took 43 to 48 seconds by the clock, and 36 to 42 before this work. No one test is slow: the slowest takes under a second, and there are nearly 7,000 |

## 10. What is needed from the founder

| # | What | Why |
|---|---|---|
| 1 | Look at the map | Nobody has looked at it against a map they know |
| 2 | Approve or change ADR 0017 and ADR 0018 | Both change the contract |
| 3 | Decide what becomes of an area whose old homes are all behind a dash: no figure, or "under 1 in 100" | Section 7, row 1 |
| 4 | Fetch File 8 again, so that fetch writes its receipt: `uv run python -m burro_pipeline fetch --list m1 --only iod-file-8 --words` | Until then no noise figure may be cited |
| 5 | Decide the label of the noise measure: residents, as the file says, or homes, as core says. When the receipt is written, say in the method that the publisher's value is already smoothed, and save the row of the notes sheet for noise to `registry/evidence/`, with a note that it states no licence of its own | With the receipt alone, noise is still left out |
| 6 | Say which year stands in the credits that hold `[year]` | Section 7, row 5 |
| 7 | Decide whether this page and the page on the files are published | Each holds counts made from publishers' files, and each now carries the credits |
| 8 | Bring `data-m0` into this branch before it is published, and build again | `data-m0` has tightened what a receipt holds. The release should come out the same bytes |
| 9 | Decide whether a release that routed no journey may leave `cutoff_minutes` out | Section 6, row 10 |
| 10 | Decide whether the statistics office's standard area measurements are registered, for validation only | It is the one published figure the land could be held to |
