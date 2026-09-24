# Named areas for all of London

Status: design, 2026-09-23. Nothing here was built when it was written, and no dataset was downloaded or opened to write it. It changes no code, no registry entry and no decision record: each change it needs is listed in section 13 for its owner. It is not legal advice. Every threshold is a first guess, to be tuned on the first real build.

Sections 16 to 18 were added on 2026-09-23 and 2026-09-24, once files had been fetched. They say what the first drafts of names and borders did where the design was open. Section 19 was added on 2026-09-24, once the founder had decided that one official publisher is enough for a name: [ADR 0022](../adr/0022-one-official-publisher-is-enough-for-a-name.md). Where sections 1, 6, 10, 11, 13 and 14 asked for two publishers, or for a person to read every name, each now says what was decided. Sections 16 to 18 are left as they were written: each says what a draft did on its day. The code that made the drafts is in `packages/pipeline/src/burro_pipeline/areas/`. [The plan for real data](london-data.md) says what was fetched. Nothing of a draft is in the repository. The counts in the three sections were made from files of Ordnance Survey, the Greater London Authority and the Office for National Statistics: [the page on the files of names and borders](../research/data/m3-files.md) ends with the credit of each.

It rests on PLAN sections 6 and 7, ADRs 0002, 0003, 0004, 0006, 0007, 0010 and 0014, contract sections 2 and 3, `registry/sources/geography.toml` and `docs/research/reports/boundaries.md`. Section 15 says what was read today and what is still unverified.

## 0. What this design assumes about the other parts

| Part, designed by someone else | Assumed here | If that is wrong |
|---|---|---|
| Fetching | Each file fetched is kept once, with its address, the date retrieved and a SHA-256. Raw files are not committed | `snapshots.json` in section 5 is the least that is needed |
| Evidence records | A release can hold, for any fact, rows of `source_id`, `record_id`, `as_written`, `data_date`, `retrieved_on`, `derivation` | Name evidence stays in the repository, and the release cites sources once for the file, as contract 2 does today |
| Where a build runs | A Linux runner with Python, network access to the publishers, 8 GB of memory. Hosted CI is enough. No Java in this part | Section 12 lists what this part needs |
| Travel times | Routed from LSOA centroids and rolled up through `oa_to_area.csv` (ADR 0003). A changed boundary re-runs the roll-up, never the routing | A boundary change would cost a routing run |
| Features, vibes, cost | Worked out per output area or LSOA and rolled up through the same file, weighted by homes. That part supplies homes and residents per output area | This part cannot set `rankable` or check sizes |
| Census panel | Sums output area tables through the same file, and links to each area's list of output areas | None here |
| Place index | Takes area names and aliases for its `district` rows | None here |
| Models | One interface, Gemini first. This part calls it when drafting and never in a release build | Drafting is done by rules alone. It is slower, not blocked |

## 1. In short

| Question | Answer |
|---|---|
| What is an area | A set of 2021 census output areas with one name. About 450, in the range 400 to 500 |
| Why every home is in exactly one | Output areas cover all of London with no gap and no overlap. One file gives each output area one area. A test holds both |
| Where names come from | OS Open Names, Wikidata, GLA town centres, ward names, and House of Commons Library names once its licence is read. Never OpenStreetMap |
| What a name needs | One official publisher that writes it for a populated place, at a point inside the area. A name that no such record fits needs two publishers that write it, and one record that puts it on the map inside the area. Decided on 2026-09-24: section 19 |
| What a boundary is | Burro's own judgement, and it says so. Each output area records the evidence that placed it and who checked it |
| What a model does | Matches spellings and suggests names to look for. It never gives a location, a boundary or a fact that is kept |
| Fastest honest route | About two weeks and 42 founder hours: all of London, every name read by a person, only flagged boundaries reviewed, each area labelled with its state |
| Better route | About six weeks: 93 founder hours, 40 paid hours (GBP 800 to 1,400), every boundary checked by a person who knows it |
| What blocks it | A machine that can download. One licence page the founder must open in a browser. Finding the second reviewer |

## 2. What an area is

| Tier | Count | Has a boundary | Ranked | In the release as |
|---|---|---|---|---|
| Area | 400 to 500 | Yes. A set of output areas | Yes, unless under 3,000 residents (contract 2.2) | A row of `neighbourhoods.json` |
| Alias: another spelling or name of the same ground | No limit | No | No | `aliases` of that area |
| Alias: a smaller place inside one area | 250 to 350 | No. One sourced point inside the area | No | `aliases` of that area |
| Wide name: covers several areas | About 30 | No | No | An alias of each area it covers, five at most, so `resolve_area` ties and offers them (contract 8.3) |
| Borough | 33 | Yes. Output areas dissolved by `LAD22CD` | No | `borough` |

Arithmetic, from counts in the boundaries research that have not been re-counted: 26,369 output areas over 450 areas is 59 each. 1,002 MSOAs over 450 is 2.2 each. 450 over 33 boroughs is 14 each.

## 3. Sources

### 3.1 What may be used

Status is as the registry stands today. "Gate refuses" means `Registry.require(id, gazetteer)` raises, so no code may open the file.

| Source | Registry id | Status | Licence | Format, size | Join key | Gives |
|---|---|---|---|---|---|---|
| Output area boundaries | `ons-output-areas-2021` | approved | OGL v3 | BGC V2 to draw, BFC V8 to place points. Size not read | `OA21CD` | The cells. Every boundary Burro draws is made of these |
| Output area centroids | `ons-oa-pwc-2021` | approved | OGL v3 | Points, V4 | `OA21CD` | Where homes are in each cell |
| Output area lookup | `ons-oa21-lsoa21-msoa21-lad22-lookup` | approved | OGL v3 | Table `OA21_LAD22_LSOA21_MSOA21_LEP22_EN_LU_V2` | `OA21CD`, `LSOA21CD`, `MSOA21CD`, `LAD22CD` | Which cells are London, and the borough of each |
| OS Open Names | `os-open-names` | approved | OGL v3 | CSV, GML 3.1.2 or GeoPackage, British National Grid. Size not read | Record id, point | Place names as points. Each road record names the settlement it is in |
| Wikidata | `wikidata-places-and-landmarks` | approved | CC0 | One query. 720 items, 717 with coordinates (research) | QID, point | Names, other names, and whether an article exists |
| GLA town centres | `gla-town-centre-boundaries` | approved | OGL v3 | `Town_Centres_Boundaries.gpkg`, 1.63 MB, EPSG:27700 | Polygon | Where a centre is. Five classes are named on the page. Whether each polygon carries a name or a class is not known |
| Ward names | `os-boundary-line` | approved | OGL v3 | Not read | Polygon, GSS code | A name for the ground each output area best fits. That the file holds London wards is unconfirmed |
| Road network | `os-open-roads` | approved | OGL v3 | Not read | Links and nodes | Distance along roads, for the draft |
| MSOA Names | `hoc-library-msoa-names` | gated. Gate refuses | Open Parliament Licence, text unread | `MSOA-Names-2.3.csv`, 7,264 rows for England and Wales | MSOA code. Column names not read | The only source where a name comes with ground made of output areas |
| GLA high streets | `gla-high-street-boundaries` | approved for scoring alone. Gate refuses it for a gazetteer | OGL v3, attribution unknown | `GLA_High_Street_boundaries_2.gpkg`, 4.22 MB | Polygon | A second anchor. Not needed |

The Open Parliament Licence page has not been read. The founder opens it in a browser and saves it (section 9).

### 3.2 Why OpenStreetMap, and anything made from it, cannot supply names or boundaries

| Thing | Why not |
|---|---|
| OSM place nodes and polygons | ODbL is share-alike. A gazetteer seeded from them would plausibly have to be offered to the public. The registry refuses share-alike data for `gazetteer`, and ADR 0004 says why. The research also found only 7 suburb and 3 quarter polygons |
| Overture divisions, Who's On First | The first is ODbL and built from OSM. The second mixes 312 sources. Both are held |
| `wikidata` tags on OSM objects | Matching through them is a join made from OSM. The Wikidata entry forbids it |
| Checking Burro's names against OSM one by one | The OSM Foundation's guideline lists adding data "based on comparison with OpenStreetMap data" as a trigger for share-alike (read today). So OSM may never add, drop or correct a name or a border. This design does not use OSM at all, not even to compare. Wikidata does that job |
| The basemap behind a review tool | The registered basemap is made from OSM and may only be displayed. A reviewer who moves a border to match a label on it has taken a feature from it. So the review page draws its own context from OGL layers (section 9) |
| A model's memory of where a place is | It cannot be cited, and part of it was learnt from maps Burro may not copy. A model never supplies a location (section 7) |
| Wikipedia text, Google Maps, portals, street atlases | Share-alike, banned, or not licensed |

## 4. How areas are built from output areas

| Step | What happens | Output |
|---|---|---|
| 1. Universe | Every output area whose `LAD22CD` is one of the 33 London codes. The count is pinned at first ingest; 26,369 is expected | `universe.csv` |
| 2. Bank | Each output area is north or south of the Thames. It is set by borough. Richmond upon Thames lies on both banks, so its wards are marked by hand, about 18 rows, and its output areas where a ward crosses the river | `bank.csv` |
| 3. Candidates | Every name with a location, from each source, as written, with its record id | `candidates.csv`, 1,000 to 1,500 rows (estimate: 720 Wikidata items plus names only other sources hold) |
| 4. Seeds | Names are scored and tiered (section 6). Each area's seed is put on its town centre if one is within 800 m, else on its OS Open Names point, else on its Wikidata point. OS places a suburb at a major road junction, so the centre is tried first | `seeds.csv` |
| 5. Evidence | For each output area: the settlement most of its named roads give, the names in its MSOA name, its ward name, and its three nearest seeds by road | `oa_evidence.csv` |
| 6. Draft | Each output area goes to the seed with the lowest adjusted distance on its own bank. Distance is metres along OS Open Roads. It is cut by 15% if the MSOA name holds the seed's name, 15% if the roads do, 5% if the ward does, and raised by 10% across a borough line | `oa_to_area.csv`, `basis = auto` |
| 7. Repair | An area must be one piece. A stray part joins the neighbour it shares most border with. An area under 1,500 homes becomes an alias of that neighbour, unless it is on a short kept list | The same file |
| 8. Review | People change rows through patches (section 9). Each changed row records who and why | The same file, `basis = reviewed` |
| 9. Generate | Polygons are dissolved from the BGC file, WGS84, 6 decimals. `neighbours` are areas sharing 50 m or more of border. `centroid` is the output area centroid nearest the homes-weighted middle, so it is always inside the area | `neighbourhoods.json`, `geometry.json` |

Bridges and tunnels join the two banks in the road network, which is why the bank is a rule and not left to distance. Railways need no layer: a road crosses a railway only at a bridge or a crossing.

**Why every home is in exactly one area**

| Link in the chain | Held by |
|---|---|
| Output areas cover London with no gap and no overlap | A check on the full-resolution file: the area of the union equals the sum of the areas, within 1 m² per cell |
| Each output area has one row | `test_every_london_output_area_is_in_exactly_one_area`: the keys equal the universe, and none repeats |
| Each row names a live area | `test_every_row_names_an_area_that_exists` |
| A home has one output area | By coordinates, a point in the full-resolution polygons. By postcode, the ONS Postcode Directory. A test: every live London postcode maps to a row |
| No area spans the Thames or is in two pieces | `test_no_area_spans_the_thames`, `test_every_area_is_one_piece` |

A point is placed by its output area, never by the drawn polygon, which is simplified. A postcode that straddles a border is placed by its centre, so a home on the border can be put next door. The product says "about" when it places a postcode.

## 5. The files that are the source of truth

They sit in `gazetteer/london/`, are committed, and are changed only by pull request. Identity is a role, `founder` or `reviewer-2`, never a person's name.

| File | One row is | Columns | Size |
|---|---|---|---|
| `areas.csv` | An area | `area_id`, `slug`, `name`, `primary_borough`, `seed_record`, `review_state`, `superseded_by` | About 500 rows |
| `oa_to_area.csv` | An output area | `oa21cd`, `area_id`, `basis`, `evidence`, `decided_by`, `decided_on`, `reason` | 26,369 rows, about 1.5 MB (estimate: 60 bytes a row) |
| `aliases.csv` | A name that is not an area's name | `alias`, `area_id`, `kind`, `source_id`, `record_id` | 300 to 500 rows |
| `name_evidence.csv` | One source for one name | Section 6 | 1,500 to 3,000 rows |
| `relations.csv` | Two areas that overlap in how people speak | `area_id`, `other_area_id`, `kind`, `source_id`, `record_id` | Under 200 rows |
| `snapshots.json` | A fetched file | `source_id`, `url`, `retrieved_on`, `sha256`, `bytes`, `version` | About 10 rows |
| `proposals/` | A model's draft | Section 7. A release build never reads it | |

`area_id` is `lon-n0001` onwards, given in order of approval and never reused. A slug is the name in lower case with hyphens. Where two areas share a name the borough is added, as in `hayes-hillingdon` and `hayes-bromley` (an example from general knowledge). `review_state` is `drafted`, `name_checked`, `boundary_checked` or `checked_twice`.

## 6. How a name is chosen, and how the choice is cited

A name is a fact and needs sources. A boundary is Burro's judgement and needs a record of how it was made.

**Salience.** A published table of points decides which names are areas.

| Evidence | Points | Source |
|---|---|---|
| A populated place in OS Open Names | 3 | `os-open-names` |
| 50 or more road records give it as their settlement | 2 | `os-open-names` |
| An "area of London" in Wikidata, with coordinates | 2 | `wikidata-places-and-landmarks` |
| That item links to an English Wikipedia article. The link is structured data. The article is never read | 1 | The same |
| A GLA town centre of district class or above lies within 800 m | 3 | `gla-town-centre-boundaries` |
| It is a name in one MSOA name. In two or more | 2. 3 | `hoc-library-msoa-names`, once approved |
| A ward carries it | 1 | `os-boundary-line` |

| Rule | Detail |
|---|---|
| To be an area | The points asked, and a name that stands. A name stands where an official publisher writes it for a populated place at a point inside the area. One that no such record fits stands on two publishers, and one record that puts it on the map. Decided on 2026-09-24: section 19. Before that: 6 points, from two publishers or more, and one record that puts the name on the map |
| To be an alias | One publisher, and one record with that name lying inside the area |
| Too close | Two seeds within 600 m by road: the lower score becomes an alias of the higher |
| Landing in range | The 6 is moved until the count is between 400 and 500. The value used is written in the release notes |
| Spelling | As OS Open Names writes it. Else as the GLA file does. Else the English label in Wikidata. Burro never respells a name |
| Approval | A person reads every area name that the draft has a mark on, and every one that the rule on one official publisher does not fit, before it ships. The score proposes and the founder approves. A name that stands by that rule alone is read by nobody, and is listed for the founder to skim: section 19. Before 2026-09-24 a person read every area name |
| A name for residents | A name that describes who lives there is kept only where OS or the GLA writes it as the name of the place. Burro never coins one. Each is put to the founder (section 13) |

**The evidence row.** `name_evidence.csv` holds one row for each source of each name.

| Column | Meaning |
|---|---|
| `area_id`, `name`, `role` | `role` is `primary`, `alias` or `wide` |
| `source_id`, `record_id` | The registry id, and the publisher's own id: an OS identifier, a QID, an MSOA code, a GSS code |
| `as_written` | The name exactly as the record holds it |
| `field` | The column it was read from |
| `locates` | `point_inside`, `polygon_overlap`, `label_only` or `none` |
| `data_date`, `retrieved_on`, `snapshot_sha256` | The edition, the day fetched, and the file it was found in |
| `checked` | True when code found `as_written` in that file at that record |
| `chosen_by`, `chosen_on` | A role and a date |

`test_every_area_name_rests_on_a_checked_source` fails if an area lacks a checked row that locates it. It fails too if the area lacks both a row by which the rule on one official publisher fits its name, and two checked rows from two publishers.

**What a page can say.** The form, with made-up values: "Name as written by Ordnance Survey (OS Open Names, edition 2026-10) and Wikidata (Q0000000, retrieved 2026-11-02). Boundary drawn by Burro from 58 census output areas (ONS, 2021). Checked by two people, 2026-11-20." Today the contract cites sources once for the whole of `neighbourhoods.json`. That is enough to build on. The line for each area needs the change asked for in section 13.

## 7. How a model drafts, with a source for each thing

| Job | The model is given | It returns | Code checks | If the check fails |
|---|---|---|---|---|
| Match spellings | Batches of candidate rows from fetched files: the name as written, type, borough, record id | Groups of record ids it takes to be one place | Each id is in the snapshot. Members lie within 1 km of each other | The group is dropped |
| Read a compound label | One MSOA or ward name | The seed names it holds | Each is in the label as written | Dropped |
| Suggest an alias | An area's name and borough, and the names already held | Names people may use for part of it. Text only | The name is searched in the snapshots. It is kept only if a record with that name lies inside the area | It goes to `leads_unsourced.csv`. It is never shown or scored |
| Explain a flag | The evidence rows of one border output area | One line for the reviewer | Every name and number in the line is in the rows | The rows are shown in its place |

| Rule | Why |
|---|---|
| A model never gives a coordinate, a border, or a fact that is kept | ADR 0014: a claim enters only with a source that code has fetched and checked |
| A model reads only files from sources registered for `gazetteer` | Rule 1. Wikipedia text is never put in a prompt |
| What a model returns is a proposal file. A person merges it | An agent proposes and a person approves (PLAN section 6) |
| A release build calls no model and reads no proposal | The same inputs give the same release. `test_a_release_build_calls_no_model` |
| Each proposal file records the provider, the model, the date and a hash of the prompt | So a draft can be traced and made again |
| No text from a user is sent | The input is public data alone |

Cost, an estimate: 44 calls to match 1,100 names and 450 to suggest aliases come to about 1.2 million tokens in and 0.3 million out. At the prices in `docs/research/models/gemini.md` that is about USD 1 a run on `gemini-3.5-flash-lite` and USD 6 on the largest model listed there. Three runs on the largest come to about USD 18. The other providers' prices were not worked out here.

A lead with no source is dropped even when the founder knows it is right. It is the price of ADR 0014. The list of such leads shows which new source would be worth registering.

## 8. Disputed and overlapping names

Ranking needs each home counted once, so membership is crisp. What is in doubt is shown in words and in how the map is drawn, and never as an overlap in the data.

| Case | What is stored | What a person sees |
|---|---|---|
| Two names for much the same ground | One is the area. The other is an alias if a source places it inside. A row in `relations.csv` | Both names find the area |
| A name that crosses a borough line | One area. `primary_borough` is the borough holding most of its homes. The shares of each borough are kept | The page names every borough the area lies in, because council tax and school admissions follow the borough |
| A name wider than an area | An alias of each area it covers, five at most | A list to choose from. The reader makes no edit from it |
| The same name in two places | Two areas, the same `name`, different slugs | A list to choose from, each with its borough |
| A border two sources place differently | The draft takes the lowest adjusted distance. The margin and the second choice are kept. A reviewer decides and gives a reason | A soft edge, and the word "about" |
| Two reviewers disagree | Both patches are kept. The founder decides. A third view is asked for if the founder does not know the ground | Nothing until it is decided. The draft stands |
| A resident says a border is wrong | A report names the area and the street. It is answered within 28 days, the promise `vibes.md` makes. A change is a pull request with its evidence | Release notes list every border that moved |
| A name an estate agent coined | It is in no registered source, so it has no row | It finds nothing |

An `area_id` outlives every such change. A split or a merge sets `superseded_by`, and an old link still opens.

## 9. The work: who, what tool, how many hours

**The tool.** One static review page for each borough, built by CI and opened in a browser. It needs no install and no server. It draws output areas coloured by area, with context from layers registered for `gazetteer` only: roads from OS Open Roads, road and place names from OS Open Names, town centres, ward outlines and seed points. It shows no OSM tiles. A reviewer clicks output areas to move them, marks a name right or wrong, and exports `patch-<borough>-<role>-<date>.csv` with `oa21cd`, `from_area`, `to_area`, `reason`. The founder merges a patch by pull request, and the checks of section 10 run on it. A borough is about 800 output areas and 1 to 3 MB of GeoJSON (estimate). The page lists flagged items first: border cells with a margin under 10%, areas in the least compact twentieth, areas in two boroughs, areas with two town centres, names with one publisher.

**The reviewer's rule.** Use what you know and what the page shows. Copy no border and no name from a map or a website. If you rely on a document, give its address, so that it can be registered and checked.

**Hours.** Minutes per item are judgement, in line with the 5 to 10 minutes per area in the boundaries research. Nothing was timed.

| Task | Who | Fast route | Better route | How it was estimated |
|---|---|---|---|---|
| Open and save the Open Parliament Licence. Look inside the town centre file for a name and a class | Founder | 1 | 1 | Two pages and one file |
| Read every candidate name: tier, spelling | Founder | 14 | 14 | 1,100 names at 45 seconds |
| Review flagged areas only | Founder | 16 | | 120 areas at 8 minutes |
| Review every area in the half the founder knows | Founder | | 30 | 225 at 8 minutes |
| Review every area in the other half | Second reviewer | | 30 | 225 at 8 minutes |
| Read the second reviewer's patches | Founder | | 7.5 | 225 at 2 minutes |
| Sample the founder's half | Second reviewer | | 4 | 45 at 5 minutes |
| Settle disputed borders | Founder | | 15 | 60 at 15 minutes |
| Talk through the disputed borders with the founder | Second reviewer | | 4 | |
| Look at each borough whole | Founder | 8 | 16.5 | 33 at 15 or 30 minutes |
| Recruit and brief the second reviewer, answer questions | Founder | | 6 | |
| Be briefed | Second reviewer | | 2 | |
| Try the review page and report faults | Founder | 3 | 3 | |
| **Total** | | **Founder 42** | **Founder 93, reviewer 40** | 133 hours in all. The plan allows 100 to 150 |

**Money.** 40 hours at GBP 20 to 35 an hour is GBP 800 to 1,400. The rate is a guess and the founder sets it. Model calls are about USD 1 to 18 on Gemini (section 7). Nothing else in this part costs money.

**The second reviewer.** Someone who has lived or worked for years in the boroughs the founder knows least. The founder marks each of the 33 boroughs "know well", "know a little" or "do not know", and the split follows. Each upkeep release after launch is one to two days.

## 10. How coverage and quality are measured

CI writes `gazetteer-report.json` on every change. A hard measure fails the build. A soft one is reported, and lists what to look at.

| Measure | Target | Kind |
|---|---|---|
| Output areas with exactly one area | 100% of the universe | Hard |
| Live London postcodes that map to a row | 100% | Hard |
| Areas whose name stands: by the rule on one official publisher, or on two publishers and one locating record | 100% | Hard |
| Aliases with one checked record inside their area | 100% | Hard |
| Areas in one piece, on one bank | 100%, less a named list of exceptions | Hard |
| No file of this part reads a share-alike source | `test_no_gazetteer_file_reads_a_share_alike_source` | Hard |
| Area names read by a person, or standing by the rule on one official publisher with no mark on them | 100% before a public release | Hard at launch |
| Count of areas. Count of aliases to smaller places | 400 to 500. 250 to 350 | Soft |
| Homes that lie in a rankable area | 99% or more | Soft |
| Areas under 5,000 or over 45,000 residents | Listed | Soft |
| Seed lies inside its own area | 100% | Soft |
| Output areas whose MSOA name, ward name and roads agree with their area | Reported for each area. Under half is flagged | Soft |
| Wikidata "area of London" labels that find an area or a list | 98% or more | Soft |
| Areas at each `review_state`, by borough | Published on the methods page | Soft |
| Two reviewers on a shared tenth of areas | They agree on 90% of output areas | Soft |
| Border test | Each border cell is moved to its second choice. An area that moves five places in a fixed ranking is flagged | Soft |
| Names that are also plain words of the reader, such as a one-word name | Listed for the reader's owner before a release | Soft |
| Residents asked about their own area in the people test (`vibes.md` 6.2) | Under one in five says the border is wrong | Soft |
| After launch: border reports for each 1,000 area pages opened | Tracked | Soft |

## 11. Two routes, and what ships if curation is late

| | Fast route | Better route |
|---|---|---|
| Covers | All of London, about 450 areas | The same areas |
| Names | Every one read by the founder | The same |
| Boundaries | Drafted by method. About 120 flagged areas reviewed | Every area reviewed by a person who knows it. A tenth by two |
| Elapsed | About 2 weeks from the first download | About 6 weeks, with a reviewer giving 10 hours a week |
| People | Founder, 42 hours | Founder, 93 hours. Reviewer, 40 hours |
| What the product says | Each area's page states its review state | The same line, with more areas checked |
| Good for | Letting every other part build on real areas. A closed beta | Public launch |

The fast route is the first stage of the better one. No work is thrown away: the better route goes on from the same files.

| If, at launch | What ships | What a page says |
|---|---|---|
| Some boundaries are unreviewed | All areas. An unreviewed area is ranked as any other | "Boundary drawn by Burro's method. Not yet checked by a person who knows the area." |
| No second reviewer was found | All areas. The founder reviews the other half too, 30 more hours | "Checked by one person." The people test is the second look |
| Some names that are asked about are unread | Nothing. Reading names waits on nobody. It was guessed at 14 hours, and is 5.3 on the draft of London since section 19 | |
| The Open Parliament Licence is not cleared | The build runs without MSOA names. More cells are flagged | No change |
| OS Open Names holds few London names | Wikidata, town centres and wards carry the names. If under 400 areas reach two publishers, the founder decides whether one official publisher is enough for the rest. Decided on 2026-09-24: it is, by the rule of section 19 | The source line names one publisher |
| The town centre file has no names | Centres anchor by overlap alone, and give points but no name evidence | No change |

What never ships: an output area with no area, a name with no checked source, a border taken from a map, a name or place supplied by a model.

## 12. Where it runs, and what it costs to run

| Need | Detail |
|---|---|
| Network | The publishers' download hosts, and the Wikidata query service |
| Software | Python. `shapely` to dissolve and to test a point in a polygon, `pyproj` to turn the National Grid into WGS84. Both are compiled extension modules, which ADR 0008 allows. Each needs its one-line reason. A GeoPackage is a SQLite file, which the standard library reads |
| Download | Under 2.5 GB (estimate from memory of the national files, none measured). Only the two GLA files were sized today |
| Compute | Under 15 minutes on a hosted runner (estimate, not measured). Reading the national road file is most of it. The draft itself is one shortest-path pass from all seeds at once |
| Storage | Snapshots kept outside the repository. The curated files are under 3 MB |
| Secrets | A model key, for drafting alone. A release build needs none |

## 13. What this asks of others, and what the founder decides

| Ask | Of whom | Why |
|---|---|---|
| Open the Open Parliament Licence in a browser and save it | Founder | Clears `hoc-library-msoa-names` |
| Add an area's `review_state`, its boroughs with their shares, and its name evidence to the release | Contract owner | So a page can cite a name and state how far a boundary was checked |
| Record the hash of the four curated files in the manifest | Contract owner | So a release names the gazetteer it was built from |
| Say whether a layer shown to a reviewer as context needs `gazetteer`. If it does, add it to `dft-naptan`, `os-open-greenspace` and `os-open-rivers`, so that stations, parks and rivers can be drawn on the review page | Registry owner | A reviewer finds their way by them. Until then the page shows roads, names, centres and wards |
| Confirm on first download that Boundary-Line holds London wards. If not, register an ONS ward file | Registry owner | Ward names are a prior |
| Supply homes and residents for each output area | Pipeline designer | For `rankable`, the size checks and the centroid |

| Founder decision | Recommendation |
|---|---|
| May an area ship with a boundary no person has checked, if its page says so | Yes for a beta. For public launch, review every area |
| Are small, well-known central areas kept as areas when under 3,000 residents | Yes. Shown and searchable, not ranked |
| A name that describes residents, written so by OS or the GLA | Keep it as the publisher writes it. Never coin one |
| The second reviewer: who, which boroughs, what rate | 40 hours. Start recruiting now, because it is the only wait on another person in this part |
| How a resident reports a border | A link that opens an email. A form would send a person's words somewhere new, which AGENTS.md says to ask about first |
| Are the curated files committed in the public repository | Yes, with the ONS and OS credit lines beside them. MSOA names stay out until the licence is read |
| If too few areas reach two publishers, is one official publisher enough | Decided on 2026-09-24, on the first draft's count: yes, for a name it writes for a populated place at a point inside the area. [ADR 0022](../adr/0022-one-official-publisher-is-enough-for-a-name.md), and section 19 |

## 14. Risks

| Risk | What is done |
|---|---|
| A border feels wrong to a resident | Review by people who know the ground, soft edges, the word "about", a report link, release notes |
| OS Open Names is thin for London | Measured on the first day. Wikidata and town centres are independent of it |
| The two-publisher rule leaves gaps in outer London | The report shows them in the first week. The founder decides the rule for the rest. Decided: section 19 |
| A name that stands by the rule on one official publisher is wrong, and nobody read it | The marks of the draft hold back a name that may be a street or a building, one that stands in two places, and one in whose area a heavier name lies. Every area is looked at in Borders under its name. A name is turned down by hand, and the draft made again. The people test asks residents about names |
| Sources are less independent than they look | The House of Commons Library does not say what it drew its names from, and a Wikidata coordinate may have been copied from elsewhere. Two publishers are required, not proof |
| A reviewer copies from a map | The written rule, a page with no such map, and a reason on every changed row |
| Ranking moves with a border | The border test of section 10 |
| Census geography is redrawn after 2031 | The cell system is versioned. ONS publishes lookups from old cells to new |
| The second reviewer cannot be found | The founder reviews all of London and the page says one person checked |

## 15. What was read today, and what is unverified

Read on 2026-09-23 through a reader that extracts, which is not the page itself. Check any quoted wording in a browser before it goes on a page people see.

| Page | What it showed |
|---|---|
| House of Commons Library, MSOA Names | Version 2.3, 13 February 2026. 7,264 MSOAs in England and Wales. Excel and CSV. "Published under the Open Parliament Licence". Column names are not listed on the page |
| parliament.uk, Open Parliament Licence | Not read |
| OS Open Names technical specification | CSV, GML 3.1.2 and GeoPackage. British National Grid. Point geometry, with a bounding box for settlements. Local types of populated place: City, Town, Village, Hamlet, Other Settlement, Suburban Area. A town or city is placed by hand at its notional centre, and any other settlement at a major road junction. A road record names the settlement it is in |
| GLA, Town Centre Boundaries | OGL v3. `Town_Centres_Boundaries.gpkg`, 1.63 MB, EPSG:27700. Five classes named. Indicative boundaries. Based on Ordnance Survey mapping |
| GLA, High Street Boundaries | OGL v3. `GLA_High_Street_boundaries_2.gpkg`, 4.22 MB. No attribution wording |
| ONS, geography licences | The credit lines for boundaries, lookups and postcode products, as the registry holds them |
| ONS, Census 2021 geographies | An output area holds 100 to 625 people and 40 to 250 households. An MSOA holds 5,000 to 15,000 people. About 200 output areas were realigned to wards |
| Wikidata, licensing | Structured data is CC0 |
| OSM Foundation, Horizontal Layers guideline | Adding data on the basis of a comparison with OSM triggers share-alike |

| Not verified | Where it came from |
|---|---|
| 26,369 output areas, 4,994 LSOAs, 1,002 MSOAs and 679 wards in London | The boundaries research. Not re-counted |
| 720 Wikidata areas of London | The boundaries research |
| London's borough codes run from E09000001 to E09000033. Only Richmond upon Thames lies on both banks. It has about 18 wards | General knowledge |
| How many London names OS Open Names holds, and whether its road records name a settlement finer than "London" | Not measured. It is the first thing to measure |
| Whether the town centre and high street polygons carry a name or a class | Not stated on either page |
| That Boundary-Line holds London wards | Not confirmed on a page that was read |
| The column names of the MSOA Names file | Not on the page |
| Every file size but the two GLA files. The download and compute figures of section 12 | Estimates from memory |
| That hosted CI can reach each publisher's download host | Not tried |
| Every hour, every rate and every threshold in this document | Judgement. None was measured |

## 16. The first draft of names and seeds, 2026-09-23

Sections 3, 4 and 6 were written before any file was opened. This is what the first draft did where they were open, and what it counted. Every rule is the draft's guess, for the founder to confirm. The code is `packages/pipeline/src/burro_pipeline/areas/names_*.py` and `seeds*.py`, and each module says the same in its first lines. No name was supplied by a person or a model.

| Left open | What the draft does | Counted |
|---|---|---|
| The second publisher | Wikidata has no file and MSOA names are gated. The town centres are the only second publisher | 234 town centres |
| What is one place | The same name within 1 km, as section 7 says. Or the same name, with the town centre wholly in the box Ordnance Survey draws round the place | 137 joined within 1 km. 6 more by the box, 1.0 to 1.5 km off, each marked |
| Who writes a name | A label that is the name, or is several names of which one is the name. A label that holds the name among other words adds points and is no second publisher | 157 populated places are written by both publishers |
| Within 800 m of what | Of the centre's outline. A place that is itself the centre has the points however far apart the two records lie | 385 populated places |
| "District class or above" | The four classes written so. A fifth, written with another word beside the rank, is read as one and marked | 2 centres, 5 places |
| A ward carries a name | The ward's label writes or holds the name, and the ward lies within 1 km of the place | 390 populated places. For 310 the ward holds the place |
| 50 road records | Counted over the whole file, by the settlement's address and never by its name | 92 places. No road names a `Suburban Area` |
| "Its town centre" | The centre of the same name, however far. Else one within 800 m whose label writes or holds the name. Never a centre of another name: that centre is a name of its own | 175 seeds stand on a centre. 19 stand over 800 m from the place's own point |
| A wide name | A `City` whose box is over 1,750 hectares, which is five areas of 350 | 2. The third city is weighed as any other place |
| Too close | As section 6. With as many points each: the one more publishers write, then the one more roads name, then the record id that sorts first | 34 gave way. 6 pairs had as many points |
| A name only a town centre holds | It is a place of its own, with no points for being a populated place | 91. 6 are put forward as areas |

| Points asked | From two publishers | From one or two |
|---|---|---|
| 9 | 66 | 66 |
| 8 | 78 | 78 |
| 7 | 252 | 252 |
| 6, the design's rule | 363 | 374 |
| 5 | 363 | 377 |
| 4, the draft's | 369 | 516 |
| 3 | 369 | 676 |

No number of points lands between 400 and 500. The draft takes 4 points with one publisher allowed, and says so of every area it lets in. It takes the larger count because the review desk can turn a name put forward as an area into another name, and cannot turn another name into an area.

| | Section 5 or 10 guessed | The draft |
|---|---|---|
| Candidate records | 1,000 to 1,500 | 1,661 of Ordnance Survey and the Greater London Authority, under 1,231 names. 33 borough names of the lookup beside them |
| Areas | 400 to 500 | 516. By the design's rule, 363 |
| Areas whose name two publishers write | All | 156. One publisher writes the other 360 |
| Areas whose points come from two publishers | All | 369 |
| Other names | 300 to 500 | 274 rows: 260 places inside an area, 4 other names of the same ground, 10 of two wide names |
| Wide names | About 30 | 2 |
| Rows of evidence | 1,500 to 3,000 | 1,268 that write a name. 1,518 with the labels that hold one |
| Areas that rest on a file with no receipt | None | 372 |

| For the founder | The draft assumes |
|---|---|
| Is one official publisher enough for a name | Yes, marked `one_publisher`, until Wikidata or MSOA names give a second |
| May a draft rest on the town centres before their file has a receipt | Yes, marked `no_receipt`. A build may not |
| Are the six pairs joined by the box one place each | Yes, marked `joined_beyond_1km` |
| Is a class with another word beside the rank of district class | Yes, marked `class_was_read` |
| Is 516 too many | The founder turns a name into another name at the desk. Or the draft is made again with `--points` and `--publishers` |

## 17. The first whole draft: a name for each area, 2026-09-24

Section 16 drafted the names before any border was drawn. Section 4 then grew the areas from the seeds. Only after both can it be said which names lie in which area. This is what the first whole draft did where sections 5, 6 and 8 were open. Every rule is the draft's guess, for the founder to confirm. The code is `packages/pipeline/src/burro_pipeline/areas/draft_*.py`, and [the first draft](../research/data/m3-first-draft.md) says what it counted and what looks wrong. No name was supplied by a person or a model.

| Left open | What the draft does | Counted |
|---|---|---|
| Which name an area takes | The name it was grown from, where a record that writes the name lies in the area as drawn | 484 of 488 areas |
| An area whose own name lies outside it | It is offered the name with most points that lies in it, and is marked. The name it was grown from is offered where its record lies | 3 areas |
| An area no name lies in | It has no name and no slug. The three names nearest to it are listed beside it. It is never given one | 1 area |
| A record lies in an area | A point lies in the area of its output area. An outline lies in every area that holds a twentieth of it or more | 463 areas are placed by a point. 24 by an outline alone |
| `locates`, once a border is drawn | `point_inside` and `polygon_overlap` as section 6 gives them. `label_only` for a record that writes the name and lies outside the area | 1,266 rows of evidence |
| A seed whose area was too small | It is another name of the area its record lies in, of kind `inside`. Section 4 says an alias of the neighbour it joined: for 2 of 28 that is another area | 28 seeds |
| A name put under an area before the borders were drawn | It is offered where its record lies, and marked where that is another area | 29 names |
| `primary_borough` | The borough that holds most of the area's output areas. Section 8 says most of its homes, and the gate does not give homes for `gazetteer` | 169 areas lie in two boroughs or more |
| The kinds of `relations.csv` | `same_name`: two areas bear one name. `name_lies_over`: a third or more of an outline that writes one area's name lies in the other. `grown_from_a_name_in`: the name an area was grown from lies in the other | 8, 94 and 4 rows |
| How a row says it is a draft | Every curated file has one column more than section 5 gives it, the last: `state`. The review desk is handed the same rows without it | Every row |
| `area_id` | The id the draft of names gave the place the area was grown from. An id of a place that is no area is kept, and never given to another | 488 of 781 ids are areas |

| | Sections 1, 5 and 9 guessed | The first whole draft |
|---|---|---|
| Areas | About 450, in the range 400 to 500 | 488. By section 6's own rule of 6 points from two publishers, 351 |
| Names to read | 1,100 | 789: 488 areas and 301 other names. The review desk makes 783 items of them |
| Other names | 300 to 500 | 301 |
| Rows of evidence | 1,500 to 3,000 | 1,266 |
| Relations | Under 200 | 106 |
| Flagged areas | About 120 | 279 by the flags of section 9 as the draft turns them. The desk has words for every one |
| Areas whose name rests on two publishers | All | 154, and 134 letter for letter. One publisher writes the other 333 |

| For the founder | The draft assumes |
|---|---|
| Is a ward's outline enough to say a name lies in an area | Yes, marked `by_an_outline_alone`. It is so for 4 areas, whose own point lies next door |
| Does an area keep the name it was grown from when a heavier name lies in it | Yes, marked `heavier_name_inside`. It is so for 8 areas. In 5 the heavier name is a seed whose own area was too small |
| Is the twentieth right | A town centre that a border cuts in two lies in both areas. At a twentieth, an outline that writes an area's name lies over a second area 490 times: 46 times a town centre, and 444 times a ward |

## 18. After the checks: what was decided where the design was open, 2026-09-24

Two checkers read the first whole draft, one against this design and one at the review desk. The draft was made again the same day. This is what was decided where the design, or the desk's design, was open. Every rule is the draft's guess, for the founder to confirm. The code is `packages/pipeline/src/burro_pipeline/areas/draft_*.py`, and [the first draft](../research/data/m3-first-draft.md) says what was found and what is still wrong. No name was supplied by a person or a model.

| Left open | What the draft does | Counted |
|---|---|---|
| How a name put forward as an area is turned down | Section 16 took it that the desk can. It cannot: it sets the answer aside while the area holds cells. So the draft is made again from the desk's own table of answers, under the same ids. A name that was turned down is no seed. One that is not kept is in no list. One a person made an area stands however small, and none gives way to it | Tried with 7 names: 481 areas, and 290 output areas given to 24 neighbours |
| When names are read | Before any border. A border looked at before its neighbours' names are settled may be looked at twice | 29 areas lie beside the 7 |
| The points asked for, once names are turned down | Chosen before any decision is laid over them. Turning names down never moves the rule | 4 points, from one publisher or two |
| The kept list of section 4 | A file of area ids, read with `--kept`. A name a person made an area is kept without being listed | None is listed |
| Which forms the desk may offer as a spelling | Section 6 gives the order: OS Open Names, then the town centres. A ward is not in it. So the desk is handed no row of a ward. The curated file keeps every row | 320 of 1,266 rows |
| How a doubt reaches the person who decides | As a line of the item it is about, in `lines.csv`. The desk reads that file when it fills its queues, and refuses a line of an item it does not make | 10,842 lines |
| What is said of an output area in doubt | Its margin and second choice, its ward, its borough where that is not the area's own, and up to 4 streets that run in it, from OS Open Roads with local roads kept. What its roads give as their settlement is left out where that is a wide name | 4,955 output areas. 4,898 have a named street |
| A flag the desk has no words for | None is left. The desk has words for every flag the draft raises, and a test of the areas build holds the draft's words to the desk's. A flag is never folded into another: the item would then say what is not so | 0 areas. It was 49 |
| A point on the line between two output areas | It lies in every area it touches. A name is placed in its own area where that is one of them, else in the one whose id sorts first, and is marked `on_the_line` | 17 names. 4 areas were told that no point of their name lay in them |
| A name that may say who lives there | Kept as its publisher writes it, flagged `describes_residents` at the desk, and listed first | 1 name |
| The least size of an area | 12 output areas, as a guess of its own. Section 4 says 1,500 homes. No home is counted, and the number rests on no table | 26 seeds were taken in |
| The main borough where two hold as many output areas | The one whose code sorts first, marked as a tie | 1 area |
| A rule that settles a name without a person | None is adopted. Section 6 says a person reads every area name. What each of eight rules would settle is counted and listed | 438 of 783 names, and 26 of 279 flagged borders |

| For the founder | The draft assumes | What turns on it |
|---|---|---|
| Does a town centre give points only to a place whose name it writes or holds | No: section 6 says a town centre within 800 m. The item says where the centre is of another name | 95 of 516 names put forward reach their points only so |
| May a record in the smallest box the file draws be a seed | Yes, marked | 10 names put forward |
| May a seed be moved to a town centre whose label only holds its name | Yes, marked | 22 seeds |
| May homes be read for `gazetteer` | No, until the registry says so | The least size, the main borough, sizes in homes |
| Is a slug made with a hyphen where a name has an apostrophe | Yes, as the first build's function makes it | 10 slugs |
| Does a wide name cover an area that holds nothing of it | Yes: it is offered over the five areas nearest it | 2 wide names |
| Which of the eight rules are adopted | None | 8.9 hours at the design's pace |

| Asked of | Change |
|---|---|
| The desk's owner | Read `lines.csv` of the draft folder and show its lines, so that no step lays them over the items. Give words to seven flags: `seeds_close`, `follows_nothing`, `size_unlike_neighbours`, `two_pieces`, `both_banks`, `seed_outside`, `no_receipt`. Say on the page at once that an answer will be set aside. A key for the next flagged item. Put names in the order of the boroughs a reviewer knows |
| The first build's owner | A way to list the files of one source of the store, so that a run looks in no other folder. The slug of a name with an apostrophe |
| The registry's owner | Whether homes gain `gazetteer`. Whether parks and rivers do, as section 13 asks |

## 19. One official publisher is enough for a name, 2026-09-24

The founder decided it: [ADR 0022](../adr/0022-one-official-publisher-is-enough-for-a-name.md) holds the decision and its reasons. This is what the draft does with it where the decision was open, and what it counted when it was made again the same day. Every rule beyond the decision itself is the draft's guess, for the founder to confirm. The code is `packages/pipeline/src/burro_pipeline/areas/draft_decided.py`. No name was supplied by a person or a model, and the ground did not change: every output area is in the area it was in.

**The rule.** A name that an official publisher writes for a populated place, at a point inside the area, is a name. It needs no second publisher.

| Left open | What the draft does | Counted |
|---|---|---|
| What an official publisher is | A public body whose file is its own list of populated places, each with a point. OS Open Names alone is one today. A town centre is an outline of a shopping street, and a ward is an outline: neither is a populated place | 690 records of populated places |
| Writes the name | The label of the record is the name, letter for letter | |
| At a point inside the area | The point lies in the area as drawn. A point on the line between two areas lies in both, as section 18 has it: the rule fits, the name is marked `on_the_line`, and so it is still read | The rule fits 463 of 488 areas. It fits 6 only by a point on the line |
| A name the rule does not fit | It is held to section 6 as it was: two publishers, and one record that puts it inside. It is flagged where one publisher writes it | 25 areas: an outline alone places 24, and 1 has no name. 8 are flagged for one publisher |
| Which names stand by the rule alone | The name of an area that the rule fits, with no mark that the draft lists on it, and none listed on another name that bears on it: a heavier name that lies in the area, or the seed of another area that does | 362 areas. One publisher writes 257 of them, and two write 105 |
| A name the rule fits that is still read | One with a mark. A mark is a doubt the decision did not settle | 101 areas |
| Another name of an area | The rule lifts the flag, and the name is still read. The decision is about the name of an area | The rule fits 210 other names |
| A wide name | The rule says nothing of it: no point puts it inside one area | 2 |
| A name a person has answered | It stays an item, so that what was said of it stands | None yet |
| How a row says that its name stands | `review_state` is `named_by_rule`, a state of its own below `name_checked`. No person is in `chosen_by` | 362 rows of `areas.csv` |
| How a name still says who writes it | `areas.csv` names every publisher that writes each name, in `publishers_writing`. `name_evidence.csv` holds a row for each record, as before. An item at the desk says it in a line, "Publishers" | 257 standing names say one publisher, and 105 say two |
| What the desk is handed of a name that stands | No item, no line, no flag and no rule. Its border is an item as before | 2,770 lines of names, where there were 5,140 |
| What the border of such an area says | First, that nobody has read the name, what the name stands on, and to say so in a note if it looks wrong | 362 borders |
| How a person skims what stands | `named_by_the_rule.csv` lists every area the rule fits, those that stand first, each with who writes it and the record that puts it inside | 463 rows |
| How a name that stands is turned down | By hand: its `area_id` and an answer in the file of decisions, and the draft made again with `--decided`. The desk holds no item of it | |
| How every name is read again | `--read-every-name`. The rule then lifts the flag, and no name stands by it alone | 783 items, as before |

| | Before the decision | The draft made again |
|---|---|---|
| Areas | 488 | 488, of the same output areas |
| Areas whose name stands with no person reading it | 0 | 362 |
| Items in the queue of names | 783 | 421: 126 names of areas, and 295 other names |
| Hours in that queue, at 45 seconds a name | 9.8 | 5.3 |
| Names flagged for one publisher | 613 | 86 |
| Names flagged for anything | 674 | 267 |
| What the eight rules would settle | 438 names, 26 borders | 172 names, 26 borders |
| Flagged borders | 279 | 279 |

**The eight rules of section 18.** None is adopted, and each stays the founder's to adopt at the desk. Each says on its own screen what the decision has settled of it.

| Rule | Fitted | Stand by the decision | Left for the rule |
|---|---|---|---|
| 1. Two publishers write it | 104 | 104 | 0 |
| 2. A ward of its name | 120 | 120 | 0 |
| 3. Many roads name it | 16 | 16 | 0 |
| 4. A smaller place by its own point | 109 | 0 | 109 |
| 5. A mark that asks nothing | 21 | 0 | 21 |
| 6. Named for a built thing | 19 | 0 | 19 |
| 7. A label of two names | 23 | 0 | 23 |
| 8. A few cells across a borough line | 26 borders | 0 | 26 borders |

The first three ask what the decision asks, and then more, so nothing is left for them. The second fitted 127 names, and the fifth 40. The 7 and the 19 that each no longer fits are names of areas with a mark: 5 in whose area a heavier name lies, 2 in whose area lies the name another area was grown from, and 19 with a mark that says only that a station of the name stands elsewhere. Each is read by a person. The fifth rule leant on the first three. It now lets through another name alone, and leans on the fourth.

| For the founder | The draft assumes | What turns on it |
|---|---|---|
| Does a name that stands by the rule leave the queue, or is only its flag lifted | It leaves the queue | 362 names, and 4.5 hours at the design's pace. With `--read-every-name` every name is read, and the first three rules settle 240 of them if adopted |
| Does a point on the line between two areas put a name inside | Yes, and the name is still read for its mark | 6 areas |
| Is a name with a mark that says only that a station of the name stands elsewhere read by a person | Yes | 19 names of areas |
| Is another name that the rule fits read by a person | Yes. The fourth rule would settle 109 of them | 210 other names |
| Is a name read by a person where a heavier name lies in its area, or the name another area was grown from | Yes. The rule fits it, and no rule settles it | 7 names that the second rule once fitted |

| Asked of | Change |
|---|---|
| The owner of the plan for London | Its sections that ask for two publishers, and for the founder to read every name, say what was decided here |
| The contract's owner | `review_state` may be `named_by_rule`. A page says of such a name who writes it, and that it stands by a rule and was read by nobody |

