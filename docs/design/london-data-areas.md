# Named areas for all of London

Status: design, 2026-09-23. Nothing here is built. No dataset was downloaded or opened to write it. It changes no code, no registry entry and no decision record: each change it needs is listed in section 13 for its owner. It is not legal advice. Every threshold is a first guess, to be tuned on the first real build.

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
| What a name needs | Two publishers that write it, and one record that puts it on the map inside the area |
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
| GLA high streets | `gla-high-street-boundaries` | gated. Gate refuses | OGL v3, attribution unknown | `GLA_High_Street_boundaries_2.gpkg`, 4.22 MB | Polygon | A second anchor. A question for the GLA. Not needed |

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
| To be an area | 6 points, from two publishers or more, and one record that puts the name on the map |
| To be an alias | One publisher, and one record with that name lying inside the area |
| Too close | Two seeds within 600 m by road: the lower score becomes an alias of the higher |
| Landing in range | The 6 is moved until the count is between 400 and 500. The value used is written in the release notes |
| Spelling | As OS Open Names writes it. Else as the GLA file does. Else the English label in Wikidata. Burro never respells a name |
| Approval | A person reads every area name before it ships. The score proposes and the founder approves |
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

`test_every_area_name_rests_on_a_checked_source` fails if an area lacks two checked rows from two publishers, or lacks one that locates it.

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
| Areas with a name resting on two publishers and one locating record | 100%, or the rule the founder sets if too few reach it (section 13) | Hard |
| Aliases with one checked record inside their area | 100% | Hard |
| Areas in one piece, on one bank | 100%, less a named list of exceptions | Hard |
| No file of this part reads a share-alike source | `test_no_gazetteer_file_reads_a_share_alike_source` | Hard |
| Area names read by a person | 100% before a public release | Hard at launch |
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
| Some names are unread | Nothing. Reading names is 14 hours and waits on nobody | |
| The Open Parliament Licence is not cleared | The build runs without MSOA names. More cells are flagged | No change |
| OS Open Names holds few London names | Wikidata, town centres and wards carry the names. If under 400 areas reach two publishers, the founder decides whether one official publisher is enough for the rest | The source line names one publisher |
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
| If too few areas reach two publishers, is one official publisher enough | Decide on the first build's count |

## 14. Risks

| Risk | What is done |
|---|---|
| A border feels wrong to a resident | Review by people who know the ground, soft edges, the word "about", a report link, release notes |
| OS Open Names is thin for London | Measured on the first day. Wikidata and town centres are independent of it |
| The two-publisher rule leaves gaps in outer London | The report shows them in the first week. The founder decides the rule for the rest |
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
