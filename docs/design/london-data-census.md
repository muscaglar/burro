# London data: census figures on an area page

Status: design, 2026-09-23. Nothing here is built. **Since 2026-09-24** the record, the folder, the route and the part of the page are built on the made-up city, and part from this design in what stands beside a figure: [the contract](contract.md), sections 2.10 and 9.6, and [the web design](web.md), section 2.1, say what was built, and [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) says where it parts from what is below. No step reads a real census table yet. It changes no code, no registry file and no other document: each change it asks for is listed with its owner. It applies [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md), and ADRs [0002](../adr/0002-deterministic-core.md), [0003](../adr/0003-three-grids.md), [0006](../adr/0006-rank-places-not-residents.md), [0007](../adr/0007-no-solicitor.md) and [0010](../adr/0010-one-contract-one-synthetic-release.md). It is not legal advice, and no lawyer has read it. No dataset was downloaded or opened. What was read on the publisher's pages today, word for word, is in [the research note](../research/data/census-2021-tables.md), and section 14 lists what is unverified. No figure about a real place is below: every share is written `nn%`.

## 0. What this assumes of the other parts

Two of the other drafts, on areas and on the pipeline, were read in part. Two more were searched for the word "census". All may have changed since.

| Part | Assumed here | If that is wrong |
|---|---|---|
| Areas | `gazetteer/london/oa_to_area.csv` gives every London output area of 2021 one `area_id`. About 26,369 rows and 450 areas. No output area is split | Nothing here works. Every figure is a sum through that file |
| Pipeline | Steps start with `Registry.require` and keep each fetched file once, by hash, with a receipt. One step, `residents`, is handed the census files and nothing else, and writes a folder of its own, `<release_id>-residents` | Section 7 still holds, with the file inside the release folder and the same fences in code |
| Evidence | A shared evidence record exists, keyed by `fact_id`. A census row is not a fact and has no `fact_id`, so the artefact carries its own evidence (section 7) | The same fields, under whatever key is chosen |
| Models | None is used here, at build or at answer, whichever provider is in use. No census figure is ever sent to one | |
| Vibes, likeness, the proxy audit | None reads this artefact. The audit keeps its own copy of the tables in its own store, under its own registry entry | |
| Website and iOS | The area page has a last block. Each client prints words the API serves and writes none about a place | |
| Seventh person | Settles the order of changes to the shared files, and the one point where this design and the pipeline draft differ: the name of the use (section 8) | |

## 1. In short

| Question | Answer |
|---|---|
| Which tables | TS003 household composition, TS004 country of birth, TS007A age by five-year bands, TS021 ethnic group, TS030 religion. Each is published for output areas |
| Main language | **Not shown for an area.** TS024 is published for local authorities and larger areas only. The panel says so in one line |
| How an area gets a figure | The office's counts for the area's output areas, added up. A share is one sum over another |
| What is printed | The office's categories, in its words and order, and a share as a whole per cent. "under 1%" below one in a hundred. No count of people in any category |
| Where | The last block of the area page, closed until asked for, loaded from a route of its own. Nowhere else |
| How it is kept from everything else | A registry heading and a use of its own. An artefact outside the release. A record that `Release` cannot return. A route of its own. A test that moves the figures between areas and finds every other answer unchanged |
| Cost | GBP 0. Five files, under 100 MB in all (estimate). Under a minute of compute (estimate) |
| What blocks it | The output area file. A host that can reach the publisher. The registry change |

## 2. The tables

| Topic in ADR 0014 | Table | Counts | Rows printed | Smallest area published |
|---|---|---|---|---|
| Household type | TS003 Household composition | Households | 21: 14 categories under 3 groups | Output area |
| Country of birth | TS004 Country of birth | Usual residents | 13: 11 categories under 2 groups | Output area |
| Age | TS007A Age by five-year age bands | Usual residents | 18 | Output area |
| Ethnic group | TS021 Ethnic group | Usual residents | 24: 19 categories under 5 groups | Output area |
| Main language | TS024 Main language (detailed) | Usual residents aged 3 and over | None | **Local authority** |
| Religion | TS030 Religion | Usual residents | 9, "Not answered" among them | Output area |

| Considered and not chosen | Why |
|---|---|
| A borough's main-language table on an area's page | It would be one figure printed on about 14 pages. ADR 0014 shows a table only where it is published "for areas of that size" |
| TS025 Household language | It is published for output areas, and it is not main language: it says whether English is a main language in a household, and never which language is. It reads as a lack. Founder decision 3 |
| TS007B Age by broad age bands, 11 rows | Its bands are 4 to 15 years wide. A band twice as wide reads as twice as many people |
| TS012, TS022, TS031, the detailed tables | Published for local authorities or MSOAs only |
| TS029 English proficiency, TS015 year of arrival, TS005 passports, TS027 national identity | Not named in ADR 0014 |
| TS077 sexual orientation, TS078 gender identity | Never shown. MSOA only, voluntary, and the office warns against use for small groups |
| TS054 tenure | It has its own entry under housing and its own place on the page |

Rules for words and order:

- The categories are the columns of the office's file. `CENSUS_TABLES` in code holds, for each table, every heading in order, with the label and the depth it is printed at. The build stops if a heading in the file is not in the list, if one is missing, or if the order differs.
- A label is the office's heading, split at the office's own colons. "Asian, Asian British or Asian Welsh: Bangladeshi" prints as "Bangladeshi", one step in, under its group. A screen reader is given the heading whole.
- The tables come in the order of the office's table numbers. The rows come in the office's order. Nothing is ever ordered by size.
- A group's row is the office's own column for the group, and not a sum of its parts made by Burro.

## 3. From output areas to a named area

| # | Step | Detail | Stops the build when |
|---|---|---|---|
| 1 | Gate | `Registry.require("ons-census-2021-resident-tables", Use.CENSUS_TABLE)` | The gate refuses |
| 2 | Fetch | `census2021-ts003.zip`, `-ts004`, `-ts007a`, `-ts021`, `-ts030` from the Nomis bulk page. For each: address, date retrieved, bytes, SHA-256 | A hash differs from the last build's. A person looks before it goes on |
| 3 | Read | The output area CSV and the local authority CSV of each zip. Join key: the file's area code to `oa21cd` | A London output area has no row, or has two |
| 4 | Headings | Compared with `CENSUS_TABLES` | Any difference |
| 5 | Add up | For each area, table and column: `count = Σ cell` over the area's output areas. `base` is the same sum of the total column | |
| 6 | Too few | A table is left out for an area where `base` is under 1,000 people, or 400 households. These are the office's lower bounds for an LSOA. A first guess | |
| 7 | Share | `100 × count / base`. Under 1: "under 1%". 99.5 or more: "over 99%". Otherwise the nearest whole number, a tie to the even one (contract 0) | A share is below 0 or above 100 |
| 8 | Base | Rounded to the nearest 100, and printed with "about" | |
| 9 | Check | The same sums for each of the 33 boroughs, against the office's own local authority file from the same zip: 33 × 85 comparisons | A share differs by 0.5 of a point or more. A count that differs by more than 60 is reported (first guess) |
| 10 | Write | `census.json`, with shares and bases as words. No count of a category leaves the build | |

**Why output areas are added up, and larger published areas are not used where they fit.** A sum of fewer, larger cells carries less of the office's noise. The gain is too small to see at a whole per cent, and it costs the one thing a critic needs: anyone can take an area's list of output areas and one public file, and get Burro's figure.

**How far out a share can be.** An estimate, not a measurement. About 14% of cells are changed by a small amount. If a cell is out by one or two, the sum of 59 cells is out by about 5 people (one standard deviation, √(59 × 0.4)). In an area of 19,500 people that is 0.03 of a point. In the smallest area shown, 1,000 people, it is about 0.1 of a point. Swapped households change a category only where the two households differ and lie in different named areas. The office publishes no figure for that. Step 9 measures the whole effect at borough scale on the first build.

**The citation.** Three lines, stored with every table and printed at the foot of the panel:

| Line | Words |
|---|---|
| Source | Source: Office for National Statistics. Census 2021, tables TS003, TS004, TS007A, TS021 and TS030, for output areas. Retrieved {date}. |
| Derivation | Added up by Burro over the {n} census output areas that make up {name}. The shares are Burro's arithmetic on the office's counts. |
| Licence | Contains public sector information licensed under the Open Government Licence v3.0. |

The first five words are the line Nomis asks for, unchanged. The second line is there so that nobody takes Burro's sum for an official figure: the licence gives no right to suggest official status.

## 4. The office's disclosure rules, and small counts

| What the office did or asks | What it means here | The rule |
|---|---|---|
| It swapped the records of 7% to 10% of households with a similar one in a nearby small area | A household that was unusual for its street may be counted next door | The panel says figures were changed to protect privacy |
| It changed about 14% of counts by a small amount, small counts more often | A count of 0, 1 or 2 is not a fact about real people | No count of a category is printed, stored in the artefact, or served |
| Totals differ between tables | Burro's sums match no official total | Each table uses its own total. The panel says no official table will match |
| It publishes small counts where it is unsure they are true | A small share is not reliable | Under 1% reads "under 1%". Nothing reads "0%" or "none" |
| It advises building the cells wanted rather than adding up others | The office builds no table for Burro's areas | Step 9, and the panel's words |
| Nomis: do not try to obtain "information relating specifically to an identified person, household or business" | | No figure for less than a whole named area. No table is crossed with another. One variable at a time |
| The licence does not cover personal data | The tables are statistics, already protected | Burro prints nothing finer than the office publishes: every share can be worked out from its public file |
| Religion was a voluntary question | | "Not answered" is always a row |

## 5. The panel, word for word

Every word below is fixed text, but the three marked (S), which are the client's. It is held in `burro_core/census.py`, written into the artefact by the build, held to those constants by `open_census` on a real release, and served by the API. `{name}`, `{n}`, `{base}` and `{date}` are stored values.

| Part | Words |
|---|---|
| Heading | Census 2021: who lived here |
| Closed, under the heading | Official figures for the people who lived in {name} on 21 March 2021: household composition, country of birth, age, ethnic group and religion. Burro does not use them to rank, filter, compare or describe any area. |
| Button, closed and open (S) | Show the census figures · Hide the census figures |
| Date | Census 2021, taken on 21 March 2021. Published by the Office for National Statistics. |
| Note 1 | The census was taken during a lockdown. Some people were not living where they usually do. |
| Note 2 | An area can change. These figures are of that day, and not of today. |
| Note 3 | {name} is drawn by Burro from {n} census output areas. The figures are the statistics office's counts for those areas, added up by Burro. No official table has this boundary, so none will match exactly. |
| Note 4 | The statistics office changes small counts slightly so that nobody can be picked out. Shares are whole numbers and may not add up to 100%. A share below 1% reads "under 1%". |
| Note 5 | Burro does not use these figures to rank, filter, compare or describe any area. |
| A table's caption | {title}. Census 2021, 21 March 2021. Share of {universe} in {name}. About {base} {unit} counted. |
| Under a caption | The statistics office's definition: "{definition}" |
| Column headings | {variable} · Share |
| A table left out | {title}. Too few {unit} lived in {name} on census day for Burro to give shares. |
| Main language | Main language. The statistics office publishes this table (TS024) for boroughs and larger areas only. Burro shows no figure for {name}. |
| Foot | The three lines of section 3. Then three links: "The output areas that were added up", "How Burro adds them up", "Census 2021 at the Office for National Statistics" |
| Loading, failure (S) | Loading the census figures. · The census figures could not be loaded. Try again. |
| Scripts off (S) | The census figures are loaded when you ask for them, which needs scripts to be on. |

The caption repeats the date, so a picture of any one table carries it. `{universe}` and `{unit}` are "usual residents" and "people", or "households" and "households". A definition is the office's own sentence, in quotation marks, and is checked against its page when the release is built.

**Order.** Heading, date, notes 1 to 5, then TS003, TS004, TS007A, TS021, the main language line, TS030, then the foot.

**Desktop, 1440 wide.** One column, 720 wide at most, in the page's main column. Nothing beside it.

```
Census 2021: who lived here
Census 2021, taken on 21 March 2021. Published by the Office for National Statistics.
1. The census was taken during a lockdown. ...        (notes 1 to 5, numbered, each on its own line)

Ethnic group. Census 2021, 21 March 2021. Share of usual residents in {name}. About {base} people counted.
The statistics office's definition: "The ethnic group that the person completing the census feels ..."
Ethnic group                                                        Share
Asian, Asian British or Asian Welsh                                   nn%
    Bangladeshi                                                       nn%
    Chinese                                                      under 1%
    ...
Black, Black British, Black Welsh, Caribbean or African               nn%
    African                                                           nn%
```

**Phone, 390 wide.** The same column, 16 from each edge. A label wraps. The share keeps its own column, 80 wide, set against the label's first line.

```
Religion. Census 2021, 21 March
2021. Share of usual residents in
{name}. About {base} people counted.
Religion                     Share
No religion                    nn%
Christian                      nn%
Other religion            under 1%
Not answered                   nn%
```

| Rule of layout | Detail |
|---|---|
| One weight and one colour | Every row is set in the same type, weight and colour as body text. A step in is 24 on a desktop and 16 on a phone, and is the only mark of a group |
| No picture of a figure | No bar, chart, map, icon, shading by value or sparkline |
| No control | No sort, no filter, no search within the table, no switch between per cent and count, no download |
| A real table | `<table>` with a `<caption>` and column headers, so it reads with a screen reader and at 200% zoom |
| Closed each time | The panel is closed on every visit. Whether it was opened is kept nowhere |
| Not in the page | The figures are not in the page's HTML, its title, its description or its link preview. The block carries `data-nosnippet` |

## 6. What is never shown beside it

| Never in the panel, over it, or in the same block | Why |
|---|---|
| A rank, a fit, a score, a journey, a budget, or anything else of a person's search | A figure about residents beside a rank is a ranking by residents in all but arithmetic |
| Another area's figures, a borough's, London's, England's, or an average | A figure beside it is "higher than average" without the words |
| Figures from the 2011 census, a change, an arrow | It turns a table into a story about who is arriving or leaving |
| "Main", "largest", "most common", "majority", "minority", "diverse", "mixed", or any adjective | ADR 0014: Burro writes no sentence about them |
| A colour, a bar, a map | ADR 0014 |
| Recorded crime, deprivation, school results, prices or rents | Set side by side they invite a link that no figure here supports. The panel comes after "Sources", and those blocks come before it |
| A vibe, "More like this", "Search for this character", the compare tray | Each leads from the table to a choice of area |
| A photograph, an advertisement, a link to a listing | |
| A sentence written by a model | The verifier cannot catch a claim about residents (contract 7.4) |

## 7. The record, and the field in the API

**The artefact.** A folder beside the release, `<release_id>-residents`, holding `manifest.json` (its files by hash, its sources, `release_id`, `synthetic`) and `census.json`. `open_release` refuses a release folder that holds a `census.json`. `open_census(folder_name, files, area_ids)` in core is the only judge of the artefact: it refuses one made for another release, one that names an area the release lacks, and a share that is not one of the words below.

| In `census.json` | Field | Notes |
|---|---|---|
| Top | `taken_on`, `publisher`, `heading`, `intro`, `notes` | `2021-03-21`. The words of section 5 |
| Top | `method` | `oa_sum@1`, with its one sentence |
| Top | `membership_sha256` | The hash of `oa_to_area.csv` as summed |
| A table | `table_code`, `title`, `variable`, `universe`, `unit`, `definition` | |
| A table | `source_id`, `url`, `file`, `sha256`, `retrieved_on`, `edition` | The evidence: source, date of the data, date retrieved, derivation |
| A table | `shown`, `reason` | `reason` is `not_published_for_small_areas` for TS024 |
| A table | `rows`: `code`, `heading`, `label`, `depth` | Once for the table, in the office's order |
| An area | `area_id`, `output_areas` | How many were added up |
| An area's table | `base`, `shares`, `reason` | `base` is words: "about 19,400". `shares` is a list of words in the order of `rows`, each matching `^(under 1%\|over 99%\|[1-9][0-9]?%)$`. `reason` is `too_few` or null |

A share is a string and never a number, so no client holds a value to sort, add or colour by.

**The route.** `GET /v1/areas/{id_or_slug}/census`. It is the only thing that reads the artefact.

| Point | Detail |
|---|---|
| `data` | `area_id`, `heading`, `date_line`, `notes`, `output_areas`, `tables` (each with the fields above and this area's `base`, `shares` and `reason`), `source_line`, `derivation_line`, `licence_line`, `links` |
| Takes | Nothing. No body and no query: a query string of any kind is answered 422 |
| Errors | 404 `area_not_found`. 404 `census_not_available`, where no artefact is loaded or the setting `BURRO_CENSUS` is `off` |
| Headers | `Cache-Control: no-store`, so no browser or phone keeps the figures. `X-Robots-Tag: noindex, nosnippet`. `X-Burro-Synthetic` as ever |
| Route 11 | Gains `census`: `available`, `heading` and `intro`. They are the words of the closed block and hold no figure |
| Routes 1 to 10, and 12 | Gain nothing |
| Log | The route's template, the status and the time taken. Never the area (rule 9) |
| Size | About 10 kB an answer, and 0.5 to 1.5 MB for the artefact (estimate: 85 rows by 450 areas) |

**The synthetic release** gets an artefact of made-up tables on made-up subjects, `SYN1` and `SYN2`, with labels as long and as deep as the office's. Its heading is "A made-up count: who lived here". It holds no heading of any real census table, so no picture of the made-up city can show a made-up share of a real group.

## 8. The licence registry

**A heading of its own.** A new file, `registry/sources/residents.toml`, and a new dimension, `residents`.

**A use of its own.** `census_table`. The pipeline draft assumes `display`. This design asks for a new use because the gate answers by use, and `display` is what `stations.json` already asks for: with `display`, the gate itself would let a census table into a release file, and only care would stop it.

| New rule, an error | Refuses the registry when |
|---|---|
| `resident_sources_feed_the_census_table_and_nothing_else` | A source under `residents` lists a use other than `census_table`, `validation_only` or `prototyping_only`, or names no `tables` |
| `only_resident_sources_feed_the_census_table` | A source under any other heading lists `census_table` |
| `resident_tables_sit_under_residents_or_audit` | A source under any other heading names a census table about people, in `tables` or in an address (`c2021ts021`, `/datasets/TS021`). `RESIDENT_TABLES` holds the codes. The housing tables TS044, TS050 and TS054 are not among them |

| Code | Change |
|---|---|
| `registry/model.py` | `Dimension.RESIDENTS`. `Use.CENSUS_TABLE`. `Source.tables`, a tuple of table codes, empty by default. `RESIDENT_TABLES` |
| `registry/rules.py` | The three rules, in `ERRORS`, each with a case in `test_registry_rules.py` |
| `registry/load.py` | None. `require()` already refuses a use that is not listed |
| `release/write.py` | It refuses a release that cites a source under `residents`, in any file. A new `write_residents()` asks the gate for `census_table`, and refuses a table the entry does not name |
| `registry/README.md` | The new field, the three rules, and a row `census.json` to `census_table` |

**The entry.** For review. Not added.

```toml
[[source]]
id = "ons-census-2021-resident-tables"
name = "Census 2021 tables about residents, for the census table on an area's page and nothing else"
publisher = "Office for National Statistics (via Nomis)"
url = "https://www.nomisweb.co.uk/sources/census_2021_bulk"
dimension = "residents"
tables = ["TS003", "TS004", "TS007A", "TS021", "TS030"]
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Source: Office for National Statistics"
attribution_verified = false
conditions = [
    "Shown on an area's page as the census table, and used for nothing else (ADR 0014). Never an input to a score, a tag, a vibe, a filter, a map layer, a comparison, a likeness, a share, a sentence, or anything sent to a model.",
    "Kept in an artefact of its own, outside the release. No file of a release may cite this entry.",
    "The office's categories, in its words and its order. No label for any group, no comparison, no colour.",
    "Shares only, as whole per cents. Under 1% reads 'under 1%'. No count of a category is printed, stored or served.",
    "State on every panel: Census 2021, taken on 21 March 2021, during a lockdown; an area can change; the figures were added up by Burro.",
    "TS024 main language is published for local authorities only and must not be shown for an area.",
    "Nomis terms: do not use the data to attempt to obtain or derive information about an identified person, household or business.",
    "Link to the Open Government Licence beside the source line. Do not suggest ONS endorses Burro.",
]
status = "gated"
status_reason = "The licence is confirmed from the publisher's pages. Gated until three things exist and pass in CI: the three registry rules of docs/design/london-data-census.md section 8, the refusal of a resident source in a release file, and the tests of section 9 numbered 9, 10 and 13."
uses = ["census_table"]
cadence = "One-off. Census Day was 21 March 2021."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.nomisweb.co.uk/home/copyright.asp",
    "https://www.nomisweb.co.uk/sources/census_2021_bulk",
    "https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3",
]
notes = "Pages were read through a reader that summarises on 2026-09-23: read them in a browser when saving evidence. See docs/research/data/census-2021-tables.md."
```

| Owner | Must change in the same change, or the repository says two things at once |
|---|---|
| Registry | `ons-census-2021-protected-characteristics`: its second condition forbids "any page". It becomes "under this entry". The five tables may stand in both entries, for different uses |
| Registry | `ons-census-2021-housing-tables`: the condition that these tables "must never be loaded into the product" |
| Registry | `registry/README.md`: the reason "Protected-characteristic tables must never reach a user" |
| Root | AGENTS.md rule 8, third sentence: data about residents is `audit_only`, or sits under `residents`, which the gate lets into the census table and nothing else |
| Contract | Sections 2 and 9: the artefact, `open_census`, the route, `census` on route 11. Section 8.4 is unchanged, word for word |
| Questions to data owners | One more question for the statistics office: what line it asks for where its counts were added up by someone else |

## 9. Tests

Each plants a canary where it can: a category label and a share found nowhere else.

| # | Part | Test | Proves no resident figure can reach |
|---|---|---|---|
| 1 | registry | `test_a_resident_source_may_feed_the_census_table_and_nothing_else` | Any use, by rule |
| 2 | registry | `test_the_gate_refuses_a_resident_source_for_every_other_use`, over every member of `Use`, so a use added later is covered | A score, the gazetteer, a display file |
| 3 | registry | `test_a_census_table_about_people_cannot_be_registered_under_another_heading` | A score, by the back door |
| 4 | registry | `test_the_real_registry_keeps_resident_sources_under_residents` | The same, on the files as committed |
| 5 | pipeline | `test_a_release_that_cites_a_resident_source_is_refused`, for every file of a release | A score, a vibe, a map layer |
| 6 | pipeline | `test_the_residents_step_imports_nothing_of_the_product_steps_and_they_nothing_of_it` | The same |
| 7 | pipeline | `test_the_artefact_holds_shares_as_words_and_no_count` | Any arithmetic |
| 8 | pipeline | `test_labels_and_order_are_the_offices_own_and_never_by_size`, `test_a_share_under_one_in_a_hundred_reads_under_1`, `test_borough_sums_are_checked_against_the_offices_own` | A label, an order |
| 9 | core | `test_nothing_in_core_imports_census_and_census_imports_nothing_of_core`, `test_a_release_cannot_return_a_census_figure`, on the protocol's members | A score, a vibe, a likeness, a fact, a sentence |
| 10 | core | `test_a_release_folder_that_holds_a_census_file_is_refused` | The release |
| 11 | core | `test_no_feature_tag_end_or_template_holds_a_census_label`, added to the denylist | A vibe |
| 12 | core | `test_no_edit_and_no_spec_can_name_a_census_category`, on the schema of `Operations` and of `PreferenceSpec`. `test_the_notice_is_the_same_with_and_without_a_census_and_points_to_neither` | The reader, a filter, a share |
| 13 | api | `test_moving_the_census_between_areas_changes_no_other_answer`: two services, one artefact with its areas' figures swapped about. Routes 1 to 12 answer byte for byte the same over 60 searches | A score, a vibe, a filter, a map layer, a comparison, a likeness, a share, the reader |
| 14 | api | `test_only_the_census_route_serves_a_census_figure`: the canary is in no other answer, header, log line or call record | The same, and a log |
| 15 | api | `test_the_census_route_takes_nothing`, `test_the_census_route_may_not_be_kept_or_indexed`, `test_the_census_route_can_be_switched_off` | A filter |
| 16 | api | `test_nothing_sent_to_a_model_holds_a_census_figure` | A model |
| 17 | api | `test_a_stored_share_holds_nothing_of_the_census`, `test_no_schema_but_the_census_routes_names_a_census_record`, on `contracts/openapi.json` | A share, a generated client |
| 18 | web | `only the area page asks for the census`, read from the import graph | A result, a comparison, the map, a share |
| 19 | web | `the figures are not in the page until asked for`, on the built HTML, its title and its description | A search engine, a link preview |
| 20 | web | `the panel prints the rows as served`, `the panel has no bar, colour or control` | An order, a colour |
| 21 | web | `a visit to every other page never meets the canary`, over the recorded visit | Every other screen |
| 22 | pipeline | `test_the_made_up_count_holds_no_heading_of_a_real_census_table` | A made-up share of a real group |

## 10. In the iOS app

| Point | Detail |
|---|---|
| Where | The last row of the area's screen: the heading and the closed words. Pressing it pushes a screen of its own, titled "Census 2021" |
| What the screen holds | The date, the five notes, the tables, the foot. Nothing of a search, no tab of results behind it, no map |
| Loading | From the census route, when the screen opens. Never before |
| Kept | Nowhere. `AreaPage` is what the shortlist keeps, and it gains no field. The answer is `no-store`, and the request is made with the cache off. Offline: "The census figures need a connection." |
| Rows | A label, and the share at the trailing edge. At the largest text sizes the share goes under the label |
| VoiceOver | A row reads the office's heading whole, then the share: "White: Irish, under 1 per cent". A caption is a heading |
| Not offered | No chart, no share sheet, no copy of the table, no widget, no Spotlight entry, no handoff, no deep link that opens the screen |
| Switch | The row is drawn only where route 11 says `available`. A build setting can leave it out |
| Apple's review | Guideline 1.1.1 was named by the earlier research and was not read today. If review objects, the app ships with the row left out and the website is unchanged |
| Tests | `test_the_area_that_is_kept_holds_no_census_figure`, `test_the_census_screen_shows_rows_in_the_order_served`, `test_the_census_screen_is_reached_from_the_area_screen_alone`, `test_nothing_of_the_census_is_written_to_the_phone` |

## 11. Where each part runs, and what it takes

| Part | Needs | Runs with no network | Hosted CI | Waits for |
|---|---|---|---|---|
| Registry code, rules, tests | Python | Yes | Yes | Nothing |
| Core records and words, made-up tables, the route, the web panel | Python, Node | Yes | Yes | The contract change |
| The iOS screen | A simulator | Yes | Yes, on a macOS runner | A simulator |
| Fetch of five zips | HTTPS to `www.nomisweb.co.uk` | No | Not proven: the site answered a reader today | A host that can reach the publisher |
| Build and borough check | `zipfile`, `csv`, `json`, `hashlib`. No Java, no geospatial library, no new dependency | Yes, once the files are in hand | Yes | The fetch |
| Figures for named areas | The same | Yes, once the files are in hand | Yes | `oa_to_area.csv` |

| Item | Estimate | How it was made |
|---|---|---|
| Download | 5 zips, 5 to 20 MB each | 188,880 rows by 12 to 27 columns, for about six kinds of area, zipped to a quarter. Not read from the page |
| Compute | Under 1 minute | About 950,000 CSV rows read once and added |
| Registry, core, pipeline step, route, tests | 3 to 4 days of an agent's work | By likeness to the rules and routes that exist |
| Web panel, iOS screen | 2 to 3 days | One table component and one screen |
| Founder: read each evidence page in a browser and save it | 2 hours | 6 pages |
| Founder: add up three areas by hand in a spreadsheet, and read the panel for ten areas known well | 3 hours | |
| Money | GBP 0 | The data is free. Hosted CI is free for a public repository, as the pipeline draft read |

## 12. The three most likely criticisms

| Criticism | How the design answers | What is left over |
|---|---|---|
| **"A site that ranks areas prints the ethnic group and religion of each one. That is steering with extra steps."** | The table is the office's own, unranked and unlabelled. It is closed until asked for, last on the page, off every result, comparison, map and share, and out of search engines. Nothing can search, sort or filter by it, and no notice points to it. Test 13 shows that moving the figures between areas changes no ranking. `BURRO_CENSUS=off` takes it down in minutes, and removing a table from `tables` takes it out of the next build | A person can still open 450 pages and choose by what they read. No professional has read this (ADR 0007). ADR 0014 names what would change it |
| **"The figures are old, were taken in a lockdown, were changed on purpose, and stop being the office's the moment Burro adds them up."** | The heading and every caption carry the date, in the past tense. Notes 1 to 4 say each of those things in plain words. Shares are whole numbers, never under 1%, never a count, and never for fewer than 1,000 people. Step 9 holds Burro's sums to the office's own at borough scale. The list of output areas is one link away, so anyone can repeat the sum | Nobody knows where London has changed since 2021, and the table cannot say. The next census is planned for 2031 |
| **"You promised never to describe residents, and reversed it in a day with no advice. Why believe the figures stay out of the ranking?"** | It is kept out by structure, in a public repository anyone can run: a registry heading and a use that the gate gives to nothing else, an artefact that a release folder may not hold, a record `Release` cannot return, one route, and tests 1 to 17. The proxy audit is unchanged and still runs in a store of its own | A neutral feature can still follow who lives somewhere. The audit finds that, and this table does not change it. The reversal is on the record, in ADR 0014 |

## 13. For the founder

| # | Decision | Recommended |
|---|---|---|
| 1 | Closed until asked for, and loaded only then? Or open, and in the page | Closed. "Show" is still kept: the figures are one press away on every area's page |
| 2 | Age by five-year bands (18 rows) or by broad bands (11 rows) | Five-year bands. Equal widths cannot mislead |
| 3 | Show TS025 household language where main language cannot be shown | No. It is not main language, and it reads as a lack |
| 4 | The least an area must hold for a table to be shown | 1,000 people, 400 households |
| 5 | Print the base, "About 19,400 people counted" | Yes. A share with no base misleads for a small area |
| 6 | If a table must go, does it go for one area or for all | For all of London. A gap on one page would mark that area |
| 7 | Apply to a free legal clinic, with sections 5 and 6 and one question | Yes, this week. The build does not wait for it |
| 8 | A new use, `census_table`, or `display` with a rule on the heading | The new use |

## 14. Unverified

- Everything the research note lists: the names of the files in each zip and of their columns, the spelling of each heading, the sizes, and every quotation until read in a browser.
- That hosted CI can reach Nomis.
- That the lockdown of 21 March 2021 was national. The words say "a lockdown".
- The noise estimate of section 3, and the two lines of step 9. The first build measures both.
- That London held about 8.8 million usual residents on census day, so about 19,500 an area. From memory.
- That `data-nosnippet` and `X-Robots-Tag` keep the figures out of every search engine. Both are requests.
- That Apple's review will pass the screen.
- That a plain table of official figures is outside the Equality Act's harassment and segregation provisions. A lay reading, from `docs/research/vibes/people.md`. No lawyer has seen it.
