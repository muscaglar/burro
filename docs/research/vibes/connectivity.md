# connectivity: Broadband, mobile and other services

Researched on 2026-09-23 for the founder's item 7: "services and utilities, eg 5G coverage or fibre to home connections". A dated snapshot, like everything in `docs/research/`. Nothing here is legal advice, and nothing in the registry has been changed.

## Summary

| Asked for | Short answer |
|---|---|
| Fibre to the home | Partly. Ofcom publishes, twice a year and under the Open Government Licence, the share of homes in every census output area that can order a **gigabit-capable** line. It withholds **full fibre** below constituency level "due to commercial confidentiality". Burro can show gigabit-capable, can rank on it if it varies enough across London, and must never call it full fibre |
| 5G coverage | No, not for a neighbourhood. Ofcom publishes mobile coverage for boroughs and constituencies only, and its API forbids building a dataset. The honest product is a borough figure that says it is a borough figure, and a link to Ofcom's own checker |
| Other services | Walk to a GP surgery, walk to a pharmacy and step-free stations can be built from open data and describe places. Council tax is set by the borough, so a borough figure is exact. Electric vehicle chargers, water hardness, recycling and post offices cannot be done well |

Six things to know:

1. **Broadband was cut from v1 on a wrong fact.** `docs/research/design/unified.md` says "Ofcom has no small-area files". It has. The output area files exist for July 2025 and for January 2026, and the registry entry already says so.
2. **The ban on Ofcom's API stands, and is now confirmed at the source.** Clause 4.3.6 of the terms forbids storing responses "to build a partial or full dataset of your own".
3. **Coverage describes a place. Speed and take-up describe what households bought.** Ofcom's "performance" file, its full-fibre take-up figure and the broadband indicator in the Indices of Deprivation all measure active lines. Under rule 8 as it stands they must not feed ranking or a tag.
4. **Nobody knows yet whether broadband tells London's neighbourhoods apart.** No data file was opened, because the registry allows none to be. If nearly every area sits in the high nineties, a percentile would make a two-point gap look like a ranking. Measure the spread before ranking on it. For scale only: Ofcom's Spring 2026 page gives 89% of UK homes as able to order gigabit-capable broadband and 82% full fibre in January 2026, as the fetch tool returned it. London's figures were not read.
5. **The engine already hears these wishes and turns them away.** `broadband` and `health_services` are values of `UnmetCategory` in the contract. A feature for each turns "Burro cannot answer that" into an answer.
6. **Step-free data stops where TfL stops.** National Rail stations run by other operators are not in TfL's file. Ranking on it today would mark down south London for a gap in the data.

## Do the registry's reasons still stand?

| Entry | Status today | Reason given | What I found | Verdict |
|---|---|---|---|---|
| `ofcom-connected-nations-2025` | held | "Broadband is explicitly out of v1 (PLAN section 4)" | The licence is clear. The scope is the founder's choice, and the founder has now asked for it | The reason is a choice, not a limit. Propose a new entry for the newer snapshot |
| condition: use output area files, avoid postcodes | | | Stands. The January 2026 postcode files were first issued with two duplicated areas and corrected on 7 July 2026 | Stands |
| condition: mobile is local authority and constituency only | | | Stands, in both the 2025 and Spring 2026 documents. Devolved constituencies were added, which does not help London | Stands |
| condition: no full fibre at output area | | | Stands. Ofcom's words: "we report on gigabit-capable coverage but not on full-fibre coverage due to commercial confidentiality" | Stands |
| condition: confirm the licence link is version 3 | | | Closed. In all five "About this data" documents the link on "Open Government Licence" points to `/version/3/` | Closed |
| condition: the logo needs permission | | | Stands. Ofcom's copyright page asks users to request permission for the logo | Stands |
| not recorded | | | A newer snapshot exists: January 2026, published 13 May 2026 | Add |
| not recorded | | | The "performance" file holds speeds of active lines, and only where an output area has five or more | Add a condition: never rank on it |
| `ofcom-coverage-api` | banned, `secondary_source` | "The research reports that the API terms forbid building a dataset" | Confirmed by reading all seven pages of the terms | Stands. Now `primary_source` |
| not recorded | | | The licence is "UK-wide" only. The Ofcom logo and a fixed notice are required. Ofcom's descriptors and colours may not be changed. The basic package allows 50,000 requests in 28 days | Four more reasons |
| not recorded | | | The legacy mobile API closes on 30 November 2026 | Note |

## Sources

How each was read: **document** means I read the publisher's PDF page by page. **tool** means the publisher's page was read through a reader that summarises, so wording must be checked in a browser before anyone relies on it. No data file was opened.

### Broadband and mobile

| Source | Measures | Licence | Read | Finest level | Refreshed | Describes | Proposed |
|---|---|---|---|---|---|---|---|
| Ofcom fixed coverage, [Spring 2026](https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026) | Share and count of premises that can order 30, 100, 300 Mbit/s and gigabit-capable lines; share that cannot get 10 or 30 Mbit/s | [OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/), stated in the [document](https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/about-this-data-fixed-broadband-coverage-and-full-fibre-take-up-2026.pdf) | document | Output area, 2021 | January and July snapshots | A place | approved |
| Ofcom full fibre availability | Share of premises that can order full fibre | OGL v3, same document | document | Local authority and constituency | Same | A place | shown only, naming the borough |
| Ofcom full-fibre take-up | Active full-fibre lines as a share of premises | OGL v3, same document | document | Local authority | Same | Residents | not used |
| Ofcom fixed performance, [2025](https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-20252/data-downloads-2025) | Average maximum speed of active lines, by speed band | OGL v3, stated in the [document](https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2025/about-this-data---fixed-broadband-performance.pdf) | document | Output area, five lines or more | Annual. Not in the Spring update | Residents | not used |
| Ofcom mobile coverage, Spring 2026 | Share of premises and of land with 2G, 4G, 5G and 5G standalone, by number of operators | OGL v3, stated in the [document](https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/about-this-data---mobile-coverage-2026.pdf) | document | Local authority and constituency | January and July snapshots | A place | gated |
| Ofcom coverage APIs | Coverage for one postcode at a time | [Ofcom API terms of use 2025](https://www.ofcom.org.uk/siteassets/ofcom/phones-telecoms-and-internet/advice-for-consumers-/broadband-and-mobile-coverage-checker/ofcom-api-terms-of-use-2025.pdf) | document | Postcode | Quarterly, as the terms say | A place | banned |
| Ofcom Map Your Mobile | Predicted coverage in 50 m squares; a performance score by postcode district from crowdsourced tests | None found. Not offered as data | tool | 50 m, on screen only | Not stated | Both | link out only |
| Indices of Deprivation 2025, broadband speed indicator | Average line speed of active connections, December 2024 | [OGL v3](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025) | document ([technical report](https://assets.publishing.service.gov.uk/media/68ff59c80f801e57b5bef907/ID_2025_Technical_Report.pdf)) | LSOA | Irregular. Last was 2019 | Residents | not used |
| Ookla open data | Speeds from tests people ran | [CC BY-NC-SA 4.0](https://github.com/teamookla/ookla-open-data). Commercial use forbidden | tool | Tile of about 610 m | Quarterly | Both | banned |
| OpenCelliD | Where masts are | [CC BY-SA 4.0](https://docs.opencellid.org/docs/attribution). Share-alike | tool | Point | Daily | A place | held |

### Other services

| Source | Measures | Licence | Read | Finest level | Refreshed | Describes | Proposed |
|---|---|---|---|---|---|---|---|
| `tfl-step-free-station-topology`, already approved | Step-free routes, lifts and toilets at TfL-served stations | TfL open data terms | registry, and tool | Station | No frequency stated | A place | no change |
| National Rail Knowledgebase, stations | Facilities and access at National Rail stations | Not read. Behind the Rail Data Marketplace | not read | Station | Not known | A place | held |
| `nhs-ods`, already approved for destination search | Where GP surgeries and branch surgeries are | OGL, stated on the service page | registry | Postcode | Nightly | A place | widen its uses |
| [Patients Registered at a GP Practice](https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice) | List size of each practice; practice by LSOA each quarter | None on the page. [Site terms](https://digital.nhs.uk/about-nhs-digital/terms-and-conditions) clause 8.1: OGL, current version | tool | Practice; LSOA quarterly | Monthly | Both | gated |
| [General Practice Workforce](https://digital.nhs.uk/data-and-information/publications/statistical/general-and-personal-medical-services) | Full-time-equivalent GPs at each practice | None on the page. Site terms as above | tool | Practice | Monthly | A place | gated |
| Indices of Deprivation 2025, patient-to-GP ratio | Patients per full-time GP, spread to LSOAs by where patients live. November 2024 | OGL v3 | document | LSOA | Irregular | Both | inside the approved source; needs an allowlist entry |
| Indices of Deprivation 2025, Connectivity Score | Travel time on foot, by bike and by public transport to 33 kinds of destination. 2025 | OGL v3 | document | LSOA | Irregular | A place | validation only |
| [Consolidated Pharmaceutical List](https://opendata.nhsbsa.net/dataset/consolidated-pharmaceutical-list) | Every NHS community pharmacy in England | OGL 3.0, shown on the dataset page | tool | Postcode | Quarterly | A place | gated |
| [CQC care directory](https://www.cqc.org.uk/about-us/transparency/using-cqc-data) | Registered services and their ratings | OGL v3, with an acknowledgement | tool | Postcode | Weekly and monthly | A place | held |
| [Council Tax levels 2026 to 2027](https://www.gov.uk/government/statistics/council-tax-levels-set-by-local-authorities-in-england-2026-to-2027) | The charge each billing authority set | OGL v3, page footer | tool | Borough, which is where the charge is set | Annual, in March | A place | gated |
| `voa-council-tax-stock-of-properties`, already approved | How many homes are in each band | OGL v3 | registry | LSOA | Annual | A place | no change |
| [Electric vehicle charging statistics](https://www.gov.uk/government/collections/electric-vehicle-charging-infrastructure-statistics) | Public chargers | OGL v3 for the tables. The points are not published | tool | Local authority | Quarterly | A place | held |
| [Local authority collected waste](https://www.gov.uk/government/statistical-data-sets/env18-local-authority-collected-waste-annual-results-tables) | Waste collected and recycled | OGL v3, page footer | tool | Local authority | Annual | Both | not used |
| TfL BikePoint | Where cycle hire docking stations are | TfL open data terms | tool | Point | Not stated | A place | held |
| Post Office branches | | Terms not read | not read | | | A place | held |
| Water hardness | | No dataset found | tool | | | A place | not used |

### What "finest level" means for Burro

| Level | How many in London | How it meets a neighbourhood of about 60 output areas |
|---|---|---|
| Output area | About 26,400 (PLAN section 6) | Exactly. Neighbourhoods are built from output areas, so counts add up |
| LSOA | About 5,000 (PLAN section 6) | Closely. A neighbourhood is a dozen or so, and edges may split one |
| Point, located by postcode | | Well enough for a walk to the nearest 50 m or so. Not to the nearest 10 m |
| Borough | 33 | Not at all. Every neighbourhood in a borough gets the same number. It is honest only for a thing the borough sets, such as council tax, or when the sentence names the borough |

One caution on "exactly". Ofcom puts each premises in an output area by its postcode, not by its position (methodology annex, paragraph 69). A postcode can cross a boundary, so a single output area's figure is slightly blurred. Summed over 60, it matters little.

## What could be built

### Features that could be ranked on

Ids follow the catalogue in contract section 3.1. All weights and thresholds are first guesses.

| Proposed `feature_id` | Label | Unit | Polarity | Native | From | Describes | Honest limits |
|---|---|---|---|---|---|---|---|
| `broadband_gigabit` | Homes that can order gigabit-capable broadband | % | more | oa | `ofcom-connected-nations-spring-2026-fixed-coverage`, residential file | A place | Gigabit-capable, not full fibre: it includes cable. Where a line can be ordered, not what a home has, pays or gets. A flat in a covered street can still lack it. Four to ten months old when shown. Rank on it only if the spread across London is wide enough to mean something |
| `gp_walk` | Walk to the nearest GP surgery | m | less | network | `nhs-ods`, with its uses widened | A place | Near is not the same as able to register: a surgery may have a closed list or a catchment that stops short. A branch surgery may keep shorter hours. Located by postcode |
| `pharmacy_walk` | Walk to the nearest pharmacy | m | less | network | `nhsbsa-consolidated-pharmaceutical-list` | A place | Says nothing of opening hours unless the file holds them, which nobody has checked. Pharmacies that serve only by post must be left out |
| `station_step_free_walk` | Walk to the nearest station recorded as step-free | min | less | network | `tfl-step-free-station-topology` | A place | Do not rank on it yet. The file covers TfL services and part of Thameslink. Where the nearest station is another operator's, the true answer is unknown, and a missing record means "not recorded", never "no" |

How `broadband_gigabit` is worked out, so that it is exact and checkable: for the output areas of a neighbourhood, add up "Number of premises with Gigabit availability" and divide by the sum of "All Premises", both from the residential file. Never average the percentages.

### Facts to show and never rank on

| Fact | From | Level | Describes | Why it is shown only |
|---|---|---|---|---|
| Homes that cannot get 30 Mbit/s | Ofcom fixed coverage | Output area | A place | Expected to be zero in most areas, though nobody has measured it, so it cannot order areas. Where it is not zero a newcomer should be told |
| Council tax for the year, Band D, and for the most common band in the area | `mhclg-council-tax-levels-2026-27` and `voa-council-tax-stock-of-properties` | Borough for the charge, LSOA for the mix of bands | A place | The charge is the same across a borough. A person's own bill depends on the home they choose |
| Homes that can order full fibre | Ofcom fixed coverage, local authority file | Borough | A place | Borough only |
| Premises with outdoor 5G from all four operators | Ofcom mobile coverage | Borough | A place | Borough only. Outdoor only. Predicted, not measured |
| Patients for each full-time GP at the surgeries local people use | Patients registered by LSOA, and GP workforce | LSOA | Both | It is a ratio, not a wait. It is a deprivation indicator in the 2025 Indices, so it waits for the proxy audit's written rule |
| Step-free access at each station on the area page | `tfl-step-free-station-topology` | Station | A place | `stations.json` already holds `step_free` and no fact carries it (web.md section 13, gap 9). A fact with a source and a date closes that gap |

A borough figure needs a home in the contract. Section 7.1 has no fact that belongs to a borough. A new kind would need its own template, along the lines of: "Across {borough}: {label}, {value}. This is a figure for the borough, not for {name}."

### Tags

A tag is a named recipe over features, so these fit the engine as it is. Each would have to pass the 40-neighbourhood sanity set.

| Proposed `tag_id` | Label | Formula | When |
|---|---|---|---|
| `everyday_on_foot` | Everyday needs on foot | 0.30 `highstreet_access` high + 0.25 `gp_walk` low + 0.25 `pharmacy_walk` low + 0.20 `station_walk` low | Once the two walks exist |
| `home_working` | Set up for home working | 0.50 `broadband_gigabit` high + 0.30 `noise_exposure` low + 0.20 `park_proximity` low | Only if `broadband_gigabit` turns out to vary across London |

### Where a person would meet it

| Place in the product | What changes |
|---|---|
| The prompt | "fibre", "broadband", "work from home", "doctor", "GP", "chemist", "pharmacy", "lift", "step-free", "pram" become words the rules can read. Today the first group is answered with `broadband` in `unmet` and the second with `health_services` |
| Chips and sliders | A chip for each new feature, drawn from the spec like any other |
| A result card | A reason in the usual form. With made-up figures: "Homes that can order gigabit-capable broadband: 96%, higher than 60% of the 450 areas compared in this release." |
| The area page | A "Services" block: each row a value, where it stands, its source and its date. Under it, a "Borough" block for council tax and the borough-only figures, each naming the borough |
| The area page, links | "Check one address" goes to Ofcom's broadband checker and mobile checker. Ofcom's copyright page says: "We welcome links to Ofcom's website, and there is no need to ask our permission first." Nothing is fetched and no postcode is passed |
| The methods page | Says that gigabit-capable is not full fibre, that coverage is where a line can be ordered, that mobile figures are the operators' predictions, and gives each snapshot's date |

## What cannot be done honestly

| Wish | Why not | What to do instead |
|---|---|---|
| Rank neighbourhoods on 5G | Ofcom publishes boroughs and constituencies only. The operators' 100 m squares are not released | Borough figure, labelled. Link to Ofcom's checker |
| Say which network is best in an area | The borough file counts operators and does not name them. Named operators appear only for the UK and its nations | Link to Ofcom's checker |
| Say anything about 5G indoors | Ofcom publishes 5G outdoors only | Say so |
| Say "full fibre" of a neighbourhood | Withheld below constituency level | Say "gigabit-capable" and explain it once |
| Say what speed a home will get, or what it will cost | Coverage is availability. No open source holds prices | Link to Ofcom's checker |
| Rank on average speed, on take-up, or on the deprivation index's broadband indicator | Each measures the lines people chose to buy. That is a fact about households, and is likely to follow income | Rank on availability only |
| Use Ofcom's API, or copy what Map Your Mobile shows | Clause 4.3.6 forbids building a dataset. Map Your Mobile is offered on screen only | The open files |
| Use speed-test maps | The one open set found forbids commercial use | Nothing |
| Say how long it takes to see a GP | No open measure exists. Patients per GP is not a wait | Show the ratio as a ratio, if at all |
| Say a station has no step-free access | TfL's guide says its list of pathways is not exhaustive | "Recorded as step-free" or nothing |
| Rank on step-free access today | National Rail stations run by other operators are missing, and PLAN section 13 says south London is unusable without rail | Show the fact per station. Rank once National Rail data is cleared |
| Count chargers near a neighbourhood | The open register closed on 28 November 2024. The statistics stop at the borough | Borough figure, if driving ever comes into scope |
| Tell areas apart by water hardness | No dataset found. The one publisher read says "Most of the water in the South-East of England is hard" | Leave out |
| Rank on recycling | Borough only, and it mixes what the council offers with what residents do | Leave out |
| Count post offices from an official list | None found, and the publisher's site was not read | Count them from `overture-places` once its London quality is measured |
| One "connectivity score" or "services score" | It would hide its parts. PLAN section 15 rules out composite liveability scores | Tags with a published recipe |

## What the founder must decide

Work can proceed on the recommendation. Decisions 4 and 5 touch rule 8. The recommendation for each keeps the rule as written, so nothing about fairness changes unless the founder chooses otherwise.

| # | Decision | Choices | Allows | Risks | Recommendation |
|---|---|---|---|---|---|
| 1 | Bring broadband into v1? PLAN section 4 lists it as out | (a) Keep it out. (b) Show it. (c) Show it and rank on it | (b) and (c) answer a wish the product now turns away | (c) may rank on gaps too small to matter | (b) now. (c) only after the spread is measured |
| 2 | What to say when someone asks for 5G? | (a) "Burro cannot answer that". (b) A borough figure, labelled. (c) A link to Ofcom's checker | (b) gives a number. (c) gives the true answer for one address | (b) reads as a fact about the area unless the label is very plain | (a) and (c) together. (b) later, if testers ask |
| 3 | What word to use for fibre? | (a) "Gigabit-capable", explained once. (b) "Full fibre", from the borough file | (a) is true of the neighbourhood | (b) is true only of the borough | (a) |
| 4 | Are speed and take-up facts about residents? | (a) Yes: never rank or tag on them. (b) No: treat them as facts about the network | (b) allows "average speed here" | (b) ranks areas by what their households can afford, which is a proxy for income and may follow protected groups | (a). It keeps rule 8 as written |
| 5 | Is patients-per-GP a fact about a place? | (a) A place: rank on it. (b) Both: show it, never rank. (c) Leave it out | (a) answers "is the surgery stretched?" | It is a deprivation indicator. Ranking on it may steer by who lives there | (b), after the proxy audit's rule is written. Rank on the walk instead |
| 6 | Bring GP and pharmacy access into v1? PLAN section 4 lists GP access as out | (a) Keep out. (b) The two walks only | (b) is place-based and cheap | The `nhs-ods` entry must gain `scoring`, and the pharmacy list must clear its gate | (b) |
| 7 | Step-free access | (a) Show per station now. (b) Rank on it now. (c) Rank once National Rail stations are in | (a) closes a gap the website already has | (b) marks down areas for missing data | (a) now, (c) later |
| 8 | A wish for step-free stations can hint at a disability. A share stores the spec | (a) Treat it as any other weight. (b) Leave it out of what a share stores | (a) is simple | (a) means a shared link can carry the hint | (a), with the chip named for the place: "step-free stations". Parents with prams ask for it too. Say so in the privacy notice |
| 9 | Show council tax? | (a) No. (b) On the area page. (c) In the budget test | (b) tells a newcomer about a bill they may not know exists | (c) edges towards an affordability verdict, which PLAN section 15 rules out | (b) |
| 10 | Allow facts that belong to a borough? | (a) No. (b) Yes, as their own kind, never scored, always naming the borough | (b) makes council tax, 5G and full fibre showable | A reader may still take it for the area's | (b) |
| 11 | A `services` dimension in the registry? | (a) File new sources under `housing`, `places` and `transport`. (b) Add `services` | (b) is tidier | (b) is a code change in `model.py` and a new file | (a) now, as the entries below do. (b) when the first is ingested |

Questions that would settle a gate.

| To | Ask | Unblocks |
|---|---|---|
| NHS England | Are "Patients Registered at a GP Practice" and "General Practice Workforce" released under the Open Government Licence, as clause 8.1 of the site terms suggests? What attribution is required? | The two NHS entries |
| Ofcom, its Connected Nations data team | What acknowledgement should accompany figures built from the output area files? Will mobile coverage be published below local authority level? | The attribution wording; decision 2 |
| Rail Delivery Group, through the Rail Data Marketplace | What terms apply to the Knowledgebase stations feed, and may step-free status be stored in a quarterly snapshot and shown in a commercial product? | Decision 7(c) |

## What was not read

| What | Standing | What I relied on | So |
|---|---|---|---|
| Web search | None was made | Addresses from the registry, from links on pages read, and a few guesses | Sources I did not already know of may exist and be missing here |
| Any data file | The registry lists no internal use for the held Ofcom entry, and the others are not registered, so rule 1 forbids a download | Ofcom's "About this data" documents | Column names are as documented, not as found. **No London figure is known**: not the spread of gigabit coverage, not how many areas have slow pockets |
| Ofcom's API portal, list of products | Not read | The terms of use, read in full | The second portal's terms are assumed to be the same document. Not checked |
| Ofcom's Connected Nations FAQ | Not read | The methodology annex | |
| Post Office terms | Not read | Nothing | Licence unknown. Held |
| Arts Council England's libraries dataset | Not read | Nothing | Libraries are left to the culture research |
| Rail Data Marketplace catalogue | Not read | National Rail's developer page, through the tool | Terms unread. Held |
| DfT Connectivity Tool's own page | Not read | The Indices of Deprivation technical report, which describes it | Its own licence is unread. The score inside File 8 is under the Indices' licence |
| Table 10 of the council tax release | Not opened | The release page, through the tool | That it lists Band D for each London borough is expected, not confirmed |
| The pharmacy list's columns | Not opened | The dataset page, through the tool | Opening hours and a marker for postal-only pharmacies are not confirmed |
| Water hardness data | One publisher's page, no dataset | That page | Not pursued. Other water companies may serve parts of London and were not read |
| Exact wording on pages marked "tool" | The tool summarises | | Check each in a browser when saving evidence |

Two notes in `docs/research/` are out of date and are left as they are, since that folder is a dated snapshot:

| File | Says | Found |
|---|---|---|
| `design/unified.md`, line 283 | "Ofcom has no small-area files. Broadband cut from v1." | Output area and postcode files exist for July 2025 and January 2026 |
| `verification/verify-data-licences.md`, lines 69 and 84 | If the small-area files are missing, switch to the Indices of Deprivation broadband indicator | That indicator measures active lines, so it describes households. Do not switch to it |

## Proposed registry entries

Not applied. `registry/` is unchanged. Every entry below was parsed by the registry's own model and passed its rules with no errors on 2026-09-23. The one approved entry raises four warnings, as it should: its attribution wording is unchecked, and three items are listed to settle before launch.

Three entries that exist today would also change, if the founder agrees:

| Existing entry | Change |
|---|---|
| `ofcom-connected-nations-2025` | Drop the condition about the licence version: it is closed. Add: "The performance file and the take-up file describe active lines. They are never an input to ranking or a tag." Add `prototyping_only` to `uses` if it is to stay held, so that a spike may open the file |
| `nhs-ods` | Add `scoring` and `display` to `uses`, for GP practices and branch surgeries. Replace the condition "v1 use is destination search only" once decision 6 is taken |
| `mhclg-iod-2025-underlying-indicators` | Add a condition: "The broadband speed indicator measures active lines (December 2024) and describes households. It is never an input to ranking or a tag." |

```toml
schema_version = 1

# --- New entries ---

[[source]]
id = "ofcom-connected-nations-spring-2026-fixed-coverage"
name = "Ofcom Connected Nations update, Spring 2026: fixed broadband coverage by census output area (January 2026 snapshot)"
publisher = "Ofcom"
url = "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026"
dimension = "housing"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Ofcom. Connected Nations update: Spring 2026, fixed broadband coverage data. Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "For scoring, use the two census output area files only: 202601_fixed_oa_res_coverage_r1.csv (residential premises) and 202601_fixed_oa_coverage_r1.csv (all premises). They are on 2021 output areas for England.",
    "The local authority file holds full fibre availability. It may be shown, never scored, and only in a sentence that names the borough.",
    "The full-fibre take-up file describes active lines, which is what households bought. It is never an input to ranking or a tag.",
    "Do not ingest the postcode files. Postcodes bring Royal Mail and Ordnance Survey rights, and the first issue of the January 2026 postcode files held two duplicated areas, corrected on 7 July 2026.",
    "Say 'gigabit-capable', never 'full fibre'. Ofcom's document says: 'For census output area and postcode, we report on gigabit-capable coverage but not on full-fibre coverage due to commercial confidentiality.'",
    "The figure is where a service could be ordered, not what a home has, what it costs, or what speed is reached. Say so beside it.",
    "Aggregate with the counts, not the percentages: premises with gigabit availability summed over a neighbourhood's output areas, divided by premises summed.",
    "Ofcom assigns each premises to an output area through its postcode, so a figure for one output area can hold premises from a neighbour. Do not show a figure for a single output area.",
    "The Ofcom logo needs separate permission. Do not use it.",
    "Do not suggest that Ofcom endorses Burro.",
]
status = "approved"
before_launch = [
    "PLAN section 4 lists broadband as out of v1. The founder amends it, or this entry goes back to held.",
    "Read the exact acknowledgement Ofcom asks for on its copyright page in a browser, save the page in registry/evidence, and correct the attribution if it differs.",
    "Measure the spread of the gigabit figure across London's neighbourhoods. If most sit within a few points of each other, show the figure and do not rank on it.",
]
uses = ["scoring", "display"]
cadence = "Twice a year. January snapshot published in May (13 May 2026, corrected 7 July 2026). July snapshot published with the annual report in November (19 November 2025)."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/about-this-data-fixed-broadband-coverage-and-full-fibre-take-up-2026.pdf",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2025/cn2025---methodology-annex.pdf",
    "https://www.ofcom.org.uk/about-ofcom/website/copyright",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
]
notes = "How it was verified: Ofcom's 'About this data' document for the January 2026 snapshot was read page by page as a document on 2026-09-23, not through a summary. It says 'We are providing this data on an open basis via the Open Government Licence', and the link on those words points to version 3. It lists the output area files with 238,878 rows (all premises) and 238,850 rows (residential) for the UK. No data file was opened, so column names are as the document gives them. The premises base is built from Ordnance Survey AddressBase Premium; the output area files hold counts and percentages only."

[[source]]
id = "ofcom-connected-nations-spring-2026-mobile-coverage"
name = "Ofcom Connected Nations update, Spring 2026: mobile coverage by local authority and constituency (January 2026 snapshot)"
publisher = "Ofcom"
url = "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026"
dimension = "housing"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Ofcom. Connected Nations update: Spring 2026, mobile coverage data. Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Published for local authorities and constituencies only. It cannot rank neighbourhoods and must never be a scoring input.",
    "Any figure shown is labelled with the borough it is for, and says it is not a figure for the neighbourhood.",
    "5G figures are outdoor only. Indoor figures exist for 4G only.",
    "The local authority file counts operators (0 to 4). It does not name them. Named operators appear only in the UK and nations file.",
    "Coverage is predicted by the operators, not measured. Say so beside the figure.",
    "State which 5G level is shown. 'High confidence' is a predicted signal of -110 dBm or better and 'very high confidence' is -100 dBm or better.",
]
status = "gated"
status_reason = "The licence is clear: the document says the data is provided under the Open Government Licence and links to version 3. Two things hold it. The release format has no fact for a figure that belongs to a borough and not to an area, so there is nowhere honest to show it. And the founder has not decided whether a borough figure is worth showing at all. Clears when the contract gains a borough-level fact and the founder says yes."
uses = ["display"]
cadence = "Twice a year, with the fixed coverage files."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/about-this-data---mobile-coverage-2026.pdf",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2025/cn2025---methodology-annex.pdf",
]
notes = "How it was verified: the 'About this data' document for the January 2026 snapshot was read page by page as a document on 2026-09-23. It lists three levels and no others: local and unitary authority, Westminster constituency, devolved constituency. The operators supply predictions as 100 m by 100 m squares, and Ofcom publishes none of them."

[[source]]
id = "nhsbsa-consolidated-pharmaceutical-list"
name = "Consolidated Pharmaceutical List (community pharmacies and appliance contractors in England)"
publisher = "NHS Business Services Authority"
url = "https://opendata.nhsbsa.net/dataset/consolidated-pharmaceutical-list"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Count community pharmacies only. Leave out appliance contractors, and leave out any pharmacy that serves by post or online and takes no callers, if the file marks them.",
    "Locate each pharmacy by its postcode through the ONS postcode directory. Its attribution lines then apply too.",
    "Never name a pharmacy in a sentence. Show a walk and a count.",
    "Do not use NHS branding.",
]
status = "gated"
status_reason = "The dataset page shows 'Open Government Licence 3.0 (United Kingdom)', read through a reader that summarises on 2026-09-23. Nobody has opened the file. Gate: open the dataset page in a browser and save it; open one quarter's file and confirm it holds a postcode and a field that separates a pharmacy with a counter from one without; read any notes on third-party rights."
uses = ["scoring", "display"]
cadence = "Quarterly: August, December, February and May. Latest is 2026-27 quarter 1, published 18 August 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://opendata.nhsbsa.net/dataset/consolidated-pharmaceutical-list",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
]

[[source]]
id = "nhs-england-patients-registered-at-a-gp-practice"
name = "Patients Registered at a GP Practice (practice totals monthly, practice by LSOA quarterly)"
publisher = "NHS England"
url = "https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://digital.nhs.uk/about-nhs-digital/terms-and-conditions"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains information from NHS England, licenced under the current version of the Open Government Licence"
attribution_verified = false
conditions = [
    "Use the 'Totals (GP practice, all persons)' file and the quarterly practice-by-LSOA totals only. The age and sex files are never downloaded.",
    "A list size is a fact about a surgery. It is never turned into a statement about who lives in an area.",
    "Do not use NHS branding. Information owned by third parties is outside the grant.",
    "Show an as-of month beside anything built from it.",
]
status = "gated"
status_reason = "The publication page states no licence. NHS England's site terms (clause 8.1) release 'NHS England Content' under the current version of the Open Government Licence, and clause 8.3 leaves out third-party information. Gate: confirm in writing, or from a page that names this publication, that the practice totals are NHS England Content under the OGL. The founder must also bring GP access into scope: PLAN section 4 lists it as out of v1."
uses = ["display"]
cadence = "Monthly, on the first of the month. September 2026 was published on 10 September 2026. LSOA files come with the January, April, July and October editions."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice",
    "https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice/september-2026",
    "https://digital.nhs.uk/about-nhs-digital/terms-and-conditions",
]
notes = "Pages were read through a reader that summarises. The attribution is the 'modified content' form from clause 8.4 of NHS England's terms, as the registry already records for nhs-ods."

[[source]]
id = "nhs-england-general-practice-workforce"
name = "General Practice Workforce (full-time-equivalent GPs by practice)"
publisher = "NHS England"
url = "https://digital.nhs.uk/data-and-information/publications/statistical/general-and-personal-medical-services"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://digital.nhs.uk/about-nhs-digital/terms-and-conditions"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains information from NHS England, licenced under the current version of the Open Government Licence"
attribution_verified = false
conditions = [
    "Use the practice-level count of full-time-equivalent GPs only. Staff age, gender and role breakdowns are never downloaded.",
    "A ratio of patients to GPs says how many people share a doctor. It does not say how long anyone waits. No sentence may say or suggest a waiting time.",
    "Do not use NHS branding.",
]
status = "gated"
status_reason = "The publication page states no licence; the site terms apply as for the patients-registered entry. Gate: the same written confirmation, and a written rule for the proxy audit, because the Indices of Deprivation use this ratio as a deprivation indicator."
uses = ["display"]
cadence = "Monthly. The latest figures are for 31 July 2026, published 27 August 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://digital.nhs.uk/data-and-information/publications/statistical/general-and-personal-medical-services",
    "https://digital.nhs.uk/about-nhs-digital/terms-and-conditions",
]

[[source]]
id = "mhclg-council-tax-levels-2026-27"
name = "Council Tax levels set by local authorities in England 2026 to 2027"
publisher = "Ministry of Housing, Communities and Local Government"
url = "https://www.gov.uk/government/statistics/council-tax-levels-set-by-local-authorities-in-england-2026-to-2027"
dimension = "housing"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "A council tax charge is set by the borough, so the figure is a fact about the borough. Show it with the borough's name and the tax year.",
    "Never add it to a rent or fold it into the budget test without saying so: PLAN section 15 rules out affordability verdicts.",
    "Do not use a band as a price estimate: bands reflect 1991 values.",
]
status = "gated"
status_reason = "The page footer reads 'All content is available under the Open Government Licence v3.0, except where otherwise stated', read through a reader that summarises. Nobody has opened Table 10. Gate: open Table 10, confirm it gives the Band D charge for each London billing authority with the Greater London Authority's share included, and read its notes sheet for any other rights statement."
uses = ["display"]
cadence = "Annual. The 2026 to 2027 edition was published on 25 March 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/statistics/council-tax-levels-set-by-local-authorities-in-england-2026-to-2027",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
]

[[source]]
id = "cqc-care-directory"
name = "CQC care directory with ratings (GP practices and other registered services)"
publisher = "Care Quality Commission"
url = "https://www.cqc.org.uk/about-us/transparency/using-cqc-data"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
conditions = [
    "CQC asks users to acknowledge that they are using CQC information.",
    "A rating that is out of date misleads. A release is a snapshot, so a rating would need its inspection date beside it.",
]
status = "held"
status_reason = "Not used in v1. A rating is a judgement on a named service, and Burro names no establishment. Revisit if a count of GP surgeries with a current adverse rating is wanted, as the schools features treat Ofsted."
cadence = "Directory weekly, ratings files monthly, as the publisher's page says."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.cqc.org.uk/about-us/transparency/using-cqc-data"]

[[source]]
id = "dft-electric-vehicle-charging-infrastructure-statistics"
name = "Electric vehicle public charging infrastructure statistics (table EVCI0102, public chargers by local authority)"
publisher = "Department for Transport"
url = "https://www.gov.uk/government/collections/electric-vehicle-charging-infrastructure-statistics"
dimension = "transport"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
status = "held"
status_reason = "Not used in v1: driving is out of scope (PLAN section 3). The finest table is by local authority, so it cannot rank neighbourhoods. The counts come from Zapmap, and the points behind them are not published. The National Chargepoint Registry, which held points under an open licence, was decommissioned on 28 November 2024."
cadence = "Quarterly. Latest is 1 July 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/collections/electric-vehicle-charging-infrastructure-statistics",
    "https://www.gov.uk/government/statistical-data-sets/electric-vehicle-charging-infrastructure-statistics-data-tables-evci",
    "https://www.gov.uk/guidance/find-and-use-data-on-public-electric-vehicle-chargepoints",
]

[[source]]
id = "tfl-bikepoint-cycle-hire-docking-stations"
name = "TfL Unified API: BikePoint (cycle hire docking station locations)"
publisher = "Transport for London"
url = "https://tfl.gov.uk/info-for/open-data-users/our-open-data"
dimension = "transport"
licence = "TfL-Open-Data"
licence_url = "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service"
commercial_use = "yes_with_conditions"
share_alike = false
conditions = [
    "The terms forbid automated extraction from the cycle hire website. Use the API only.",
    "Locations only. Live availability is not a fact about a place.",
    "Follow TfL's branding rules. Say 'cycle hire docking station' and use no sponsor's or TfL's marks.",
]
status = "held"
status_reason = "Not checked far enough to use. The open data page lists BikePoint under the Transport Data Service terms but shows no timing values for it. Clears when someone reads the page and the API documentation in a browser, and TfL's answer on snapshots is in."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://tfl.gov.uk/info-for/open-data-users/our-open-data",
    "https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service",
]

[[source]]
id = "rdg-knowledgebase-stations"
name = "National Rail Knowledgebase: stations feed (facilities and step-free access at National Rail stations)"
publisher = "Rail Delivery Group"
url = "https://www.nationalrail.co.uk/developers/"
dimension = "transport"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
status = "held"
status_reason = "The terms have not been read. The feed is reached through the Rail Data Marketplace, which needs an account, and its catalogue has not been read. It is the only source found for step-free access at the National Rail stations that TfL's data leaves out. Clears when the founder, signed in, reads and saves the terms for this feed."
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = ["https://www.nationalrail.co.uk/developers/"]

[[source]]
id = "post-office-branch-finder"
name = "Post Office branch finder"
publisher = "Post Office Limited"
url = "https://www.postoffice.co.uk/"
dimension = "places"
licence = "None-stated"
commercial_use = "unknown"
share_alike = false
status = "held"
status_reason = "No open dataset of branches was found. The publisher's terms page (https://www.postoffice.co.uk/terms-conditions) has not been read. The site must not be scraped. Post offices may be counted from overture-places, which is approved, once its London quality is measured. Clears only if the publisher offers the list under a licence that allows commercial use."
verified_how = "unverified"
verified_on = 2026-09-23

[[source]]
id = "opencellid-cell-towers"
name = "OpenCelliD cell tower database"
publisher = "OpenCelliD"
url = "https://opencellid.org/"
dimension = "housing"
licence = "CC-BY-SA-4.0"
licence_url = "https://docs.opencellid.org/docs/attribution"
commercial_use = "yes_with_conditions"
share_alike = true
conditions = [
    "Share-alike. It may never reach the gazetteer or scoring.",
]
status = "held"
status_reason = "Not used. It records where masts are, not where a phone works, and it is share-alike. Registered so that nobody reaches for it to fill the gap in small-area mobile data."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://docs.opencellid.org/docs/attribution"]

[[source]]
id = "ookla-open-data"
name = "Speedtest by Ookla global fixed and mobile network performance map tiles"
publisher = "Ookla"
url = "https://github.com/teamookla/ookla-open-data"
dimension = "housing"
licence = "Bespoke-terms"
licence_url = "https://github.com/teamookla/ookla-open-data"
commercial_use = "no"
share_alike = false
status = "banned"
status_reason = "The publisher's repository states the data is under CC BY-NC-SA 4.0, which forbids commercial use. Burro is a commercial product. The licence list in model.py has no value for this licence, so it is recorded as bespoke terms. The tiles also measure tests that people chose to run, which says as much about who ran them as about the place."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://github.com/teamookla/ookla-open-data"]

# --- Replaces the existing entry of the same id in housing.toml ---

[[source]]
id = "ofcom-coverage-api"
name = "Ofcom coverage APIs (fixed and mobile lookups by postcode)"
publisher = "Ofcom"
url = "https://api.ofcom.org.uk/"
dimension = "housing"
licence = "Bespoke-terms"
licence_url = "https://www.ofcom.org.uk/siteassets/ofcom/phones-telecoms-and-internet/advice-for-consumers-/broadband-and-mobile-coverage-checker/ofcom-api-terms-of-use-2025.pdf"
commercial_use = "yes_with_conditions"
share_alike = false
status = "banned"
status_reason = "Clause 4.3.6 of the Ofcom API terms of use 2025: 'you are not permitted to cache, aggregate or otherwise store the Information in order to build a partial or full dataset of your own. Any data cached for performance reasons should be held for a period of no longer than one month.' Burro works only from stored data releases, so it cannot use the API. The terms also grant a 'UK-wide' licence only (clause 2.1), require the Ofcom logo (4.2.1), a fixed notice beside the data (4.2.2) and Ofcom's own descriptors and colours unchanged (4.3.4). Fixed coverage is available as open files in the Connected Nations entries. A plain link to Ofcom's own checker is not use of the API and is allowed: Ofcom's copyright page says it welcomes links."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.ofcom.org.uk/siteassets/ofcom/phones-telecoms-and-internet/advice-for-consumers-/broadband-and-mobile-coverage-checker/ofcom-api-terms-of-use-2025.pdf",
    "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/ofcom-checker",
    "https://api.ofcom.org.uk/",
    "https://www.ofcom.org.uk/about-ofcom/website/copyright",
]
notes = "How it was verified: all seven pages of the terms were read as a document on 2026-09-23. The portal's front page says the legacy mobile API takes no new subscriptions and closes on 30 November 2026, and that new 2G and 4G/5G APIs are on a second portal. The terms name a limit of 100 requests a minute and 50,000 requests in 28 days on the basic packages."
```
