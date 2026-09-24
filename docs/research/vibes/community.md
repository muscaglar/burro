# community: places to meet and things to join

Researched 2026-09-23. A dated snapshot, not a source of truth. Nothing here is legal advice.

## Headline

No open dataset says whether neighbours know each other in a London neighbourhood. The only survey that asks is published for whole boroughs, describes residents, and has been discontinued. What can be measured honestly is narrower: **how many kinds of place to meet, and things to join, are within a walk**. Two sources for that are already approved. Two more look lawful and wait on a named check. The three most wanted, parkrun, Sport England's facility register and the current libraries list, were not read at all and need the founder.

## Summary

| Finding | Detail |
|---|---|
| The honest measure is of opportunity, not of outcome | Burro can count libraries, allotments, children's centres, sports facilities and regular sessions near a home. It cannot say people there are friendly |
| Usable from approved sources today | Allotments and community growing spaces (`os-open-greenspace`). Children's centres (`dfe-gias`) |
| Lawful on what was read, gated on a check | Registered nurseries (Ofsted, OGL v3). Regular activity sessions (OpenActive, CC BY 4.0) |
| Lawful on what was read, held for fairness or fitness | Places of worship registered for marriage (HM Passport Office, OGL v3). Charities (Charity Commission) |
| Wanted most, and unread | parkrun, Active Places and the Arts Council libraries list: none was read |
| No London-wide open dataset found | Street and farmers' markets, residents' associations, neighbourhood forums, playgroups, running clubs |
| Places of worship by faith | A lawful list exists, but it leaves out every Anglican church and every building not registered for marriages. A count by faith built on it would be wrong, and wrong unevenly. It also presses on ADR 0006. The choice is the founder's |
| The nearest thing that already exists | The GLA's Civic Strength tool. I read its method in full. It mixes places with residents, counts migration as a weakness, and has only 11 measures below borough level. Use it as a map of what others measure, not as an input |

How this was done, and its limits:

- No web search was made. Every page was reached by opening a known or guessed address, so **sources I did not already know of will be missing**. Markets, clubs and forums suffer most from this.
- Pages were read through a reader that summarises. Quoted wording must be re-checked in a browser before it goes into the registry as `attribution_verified = true`.
- No data file was downloaded or opened. Column lists below are marked where they are from memory.
- One document was read in full as text: the GLA's Civic Strength method note.

## Sources

"Read at source" means: **yes**, the publisher's own page stating the licence was fetched today; **part**, only a site footer or a related page was; **no**, the page was not read.

| Topic | Source | Publisher | Licence as read | Read at source | Resolution | All of London | Refreshed | Proposed status |
|---|---|---|---|---|---|---|---|---|
| Allotments, community growing | OS Open Greenspace, function "Allotments or Community Growing Spaces" | Ordnance Survey | OGL v3 | Yes (already `approved`) | One polygon per site | Yes | Every six months | Already approved |
| Children's centres | GIAS, "Children's centre fields" download | Department for Education | OGL v3 | Yes (already `approved`) | One row per centre. Location fields not inspected | Yes | Daily, per the registry | Already approved |
| Nurseries and pre-schools | Childcare providers and inspections, provider-level file | Ofsted | OGL v3, GOV.UK footer | Part | One row per provider. Columns not inspected | Yes, England | Twice a year. Latest as at 30 June 2026 | Gated |
| Regular sessions and classes | OpenActive feeds | Many publishers, one standard | CC BY 4.0 | Yes | One record per session or facility, with a venue | **No.** Only where an operator publishes | Live feeds. Resync no more than weekly | Gated |
| Sports halls, pools, lidos, pitches, tracks | Active Places | Sport England | Not read | No | One row per facility, from memory | Expected, not confirmed | Not confirmed | Gated |
| parkrun and junior parkrun | Event list | parkrun | Not read | No | One point per event, from memory | Not confirmed | Not confirmed | Held |
| Libraries, current | Basic dataset for libraries | Arts Council England | Not read | No | One row per library, from memory | Expected, not confirmed | Annual, per GOV.UK | Gated |
| Libraries, old | Public libraries in England: basic dataset, as on 1 July 2016 | DCMS | OGL v3 | Yes | One row per library | Yes | Never. It is ten years old | Held |
| Libraries, GLA layer | Cultural Infrastructure Map 2023, libraries | GLA | OGL v3, upstream unchecked | Already `held` | Point | Yes | Snapshot, captured 2022 and 2023 | Already held |
| Community centres | Cultural Infrastructure Map 2019, community centres | GLA, with an outside body | OGL v3, third-party rights unclear | Already `held` | Point | Yes | Seven years old | Already held |
| Community centres, halls, markets, clubs | Overture Places | Overture Maps Foundation | CDLA-Permissive-2.0 and others | Yes (already `approved`) | Point | Yes, quality unmeasured | Monthly | Already approved. Category names not confirmed |
| Places of worship | Places of worship registered for marriage | HM Passport Office | OGL v3, GOV.UK footer | Part | One row per registered building. Columns not inspected | Partial by design | Page updated 9 September 2026 | Held |
| Charities | Register of charities | Charity Commission | OGL v3 on the API portal footer. The download page was not read | Part | One row per charity, at a contact address | Yes | Not confirmed | Held |
| Grants to local groups | GrantNav | 360Giving and its publishers | CC BY 4.0 | Yes | One row per grant | Uneven | Continuous | Held |
| Assets of community value | planning.data.gov.uk | MHCLG | OGL v3 | Yes | Per asset | **No.** 105 records, one provider, Camden | Daily collector | Held |
| Neighbourhood forums and areas | None found London-wide | | | | | No | | None proposed |
| Allotments, old | Allotment Locations | GLA | OGL v2 | Yes | Point | Yes | Not since May 2007 | Held |
| Neighbourliness, belonging, volunteering | Community Life Survey 2023/24 | DCMS | OGL v3 | Yes | **Local authority.** Nothing smaller | Yes, by borough | Discontinued | Held, audit only |
| Sport and volunteering rates | Active Lives | Sport England | Not stated on the page read | Part | **Local authority** | Yes, by borough | Twice a year, from memory | None proposed. It describes residents, by borough |
| Composite: civic strength | London Civic Strength Index | GLA | OGL v3 on the page. Inputs include third-party data | Yes | Borough for 40 measures. **Ward for 11** | All but the City | 2021, 2023, 2025 | Held |
| Composite: community need | Community Needs Index 2023 | OCSI | Not read | No | LSOA 2021 | Yes, England | 2019, 2023 | Held |
| parkrun, by another route | Wikidata | Wikimedia | CC0 (already `approved`) | Yes | Point | **No.** 2 events in the whole UK | | Not a source for this |

Notes on the rows that matter most:

**parkrun.** Nothing about parkrun's terms is stated in this report, because no page of its site was read. One query to Wikidata found two parkrun events in the United Kingdom, so there is no open route round the publisher, and none should be looked for.

**Active Places.** The open data page was not read. My recollection is that the data is offered under CC BY 4.0 and lists every public and club sports facility in England by type, with lidos as a kind of pool. That is a recollection and not a checked fact.

**OpenActive.** The developer guide's attribution page names CC BY 4.0 and asks that the publisher is credited by name, with a link, beside the data. The status page lists about 370 datasets, test ones included. London publishers seen there: Ealing, Tower Hamlets and Southwark councils, Redbridge Sports Centre, Vision Redbridge, Lampton Leisure and Coram's Fields. parkrun is not listed. Coverage follows who chose to publish, so **an area with no sessions may be an area with no publisher**.

**Places of worship registered for marriage.** The page says: "This list does not cover Church of England/Church in Wales premises (Anglican premises)." It also says accuracy depends on owners telling the Registrar General when a building stops being used for worship. Registration is for holding marriages, so a place of worship that has never registered is absent. How that falls across faiths was not measured.

**Charity Commission.** The Commission's personal information charter says it publishes, and makes available for re-use, trustees' names and the contact's name and email. OGL does not cover personal data. A charity's address is where its post goes, which is often a trustee's home or a head office, not where it works.

**London Civic Strength Index.** Read in full. Of the 11 ward-level measures, six describe places (sport offerings, libraries, community centres, cultural spaces, faith centres, green space), one is transport, and four describe residents, organisations or events (ballots cast, change in occupational class, community interest companies, recorded crime). Its sources include BT footfall, London Sport, Trussell Trust, the Ordnance Survey National Geographic Database, and the GLA's own culture map, which this registry holds. At borough level it scores internal and international migration as lowering civic strength. Safety, which is recorded crime alone, carries 16.6% of the weight.

## What could be built

Every feature below describes a **place**. None describes residents. Each has one direction only: a person may ask for more or nearer, never fewer or further. Asking to be far from a community hall or a place of worship is a way to ask about people, and ADR 0006 already refuses that for campuses. Each needs its row in the proxy audit rule before it ranks: where libraries and children's centres were built is not independent of who lives nearby.

| Proposed `feature_id` | Label | Describes | From | Native resolution | Buildable |
|---|---|---|---|---|---|
| `growing_space_proximity` | Walk to the nearest allotment or community growing space | Place | `os-open-greenspace` | Polygon, network walk | Now |
| `childrens_centre_proximity` | Walk to the nearest children's centre | Place | `dfe-gias` | Point, network walk | Now, once the existing entry is confirmed to cover the children's centre file |
| `nursery_nearby` | Registered nurseries and pre-schools within a short walk | Place | Ofsted provider file | Point, network walk | After the gate |
| `library_proximity` | Walk to the nearest public library | Place | Arts Council list | Point, network walk | After the gate |
| `sports_facility_nearby` | Kinds of public or club sports facility within a short walk | Place | Active Places | Point, network walk | After the gate |
| `lido_proximity` | Distance to the nearest open-air pool | Place | Active Places | Point | After the gate |
| `weekly_sessions_nearby` | Venues with a session that repeats every week, within a short walk | Place | OpenActive | Point, network walk | After a coverage check by borough |
| `parkrun_proximity` | Distance to the nearest parkrun or junior parkrun | Place | parkrun | Point | Only with written permission |
| `community_hall_nearby` | Community centres and halls within a short walk | Place | Overture Places | Point | After the London quality spike |
| `market_proximity` | Walk to the nearest regular market | Place | No source found | | Not yet |
| `worship_proximity` | Walk to the nearest place of worship, no faith named | Place | Overture Places, or the marriage list plus a source for Anglican churches | Point | Founder decision first |
| `meeting_place_kinds` | How many of these kinds of place are within a 15-minute walk | Place | The features above | Network walk, from where people live | When at least five kinds have London-wide data |

### Measuring "a place where you get to know people"

| Step | Proposal |
|---|---|
| What is measured | Opportunity for repeated contact: places you go back to, with the same people |
| The kinds | A library. A community hall. A children's centre. An allotment or community garden. A public or club sports facility. A weekly free event. A regular market. A park with a play space. A high street |
| The figure | `meeting_place_kinds`: the count of kinds within a 15-minute walk. Variety, not volume. Ten pubs are one kind |
| Why a count of kinds | It is literally true, it is checkable, and it reads as a sentence: "6 of the 9 kinds of meeting place are within a 15-minute walk" |
| The tag | "Places to meet". Never "friendly", "close-knit", "tight-knit" or "community spirit". Those are claims about residents |
| A first formula, untested | 0.40 `meeting_place_kinds` high + 0.20 `library_proximity` low + 0.20 `sports_facility_nearby` high + 0.10 `play_space_proximity` low + 0.10 `highstreet_access` high |
| When a kind has uneven data | It is left out of the count for every area, and the sentence says "of the 7 kinds Burro has data for". A gap in the data is never counted as an absence |
| The bar to ship | The 40-neighbourhood sanity set, as for every tag. I expect a version without libraries and sports facilities to fail it |

### In search and on the area page

| Element | Content | Needs |
|---|---|---|
| A prompt such as "somewhere with a community feel" | The "Places to meet" tag, with the assumption shown as a chip: "Read 'community' as places to meet nearby". The person can remove it | A tag id and a line in the reader's vocabulary |
| A prompt such as "friendly neighbours" or "people like me" | No edit, as now. It is a request about residents | Nothing |
| A reason on a result card | "Places to meet: 6 of the 9 kinds are within a 15-minute walk", with source and date | The `meeting_place_kinds` fact |
| "Places to meet" section | One line per kind: the nearest one, the walk in minutes, the source and date | `display` use on each source |
| Named places | The library, the lido, the allotment site, by name | A founder decision, below. Today venue sources are aggregates only |
| What Burro does not know | A fixed line: "Burro counts places. It cannot tell you whether a group is welcoming, has room, or still meets." | Nothing |

## What cannot be done honestly

| Claim | Why not |
|---|---|
| "People here know their neighbours" | The only measure is the Community Life Survey. It is by borough, it describes residents, and it has been discontinued. One borough figure would be pasted onto about 14 neighbourhoods |
| "Friendly", "welcoming", "close-knit" | No dataset measures it. The verifier should refuse these words as it refuses "safe" |
| Volunteering rate for a neighbourhood | Survey data, by borough only |
| "There is an active residents' association" | No register was found. Borough lists vary and none was found under an open licence |
| "This area has a neighbourhood forum" | The national planning data platform lists no such dataset. data.gov.uk shows single areas published by single boroughs. No London-wide layer was found |
| Playgroups and stay-and-play | No register of them was found. As far as I know Ofsted registers childcare, not drop-in groups a parent stays at. Not checked |
| Running clubs and sports clubs by name | No open list was found. Governing bodies run their own club finders; their terms were not read and nothing is claimed about them |
| Markets | No open London-wide list was found. This may be a limit of the search, not of the data |
| How busy or how large a parkrun is | That is the publisher's results data. Not read, not proposed |
| A count of places of worship by faith, from the marriage list | The list omits every Anglican church and every unregistered building. The error differs by faith |
| Whether an allotment has a free plot, or a club has room | Sites are mapped. Waiting lists are not |
| Informal ties: school gates, group chats, street parties | Nothing records them |
| How long people stay | The census asks where people lived a year before, from memory. It describes residents, so the rules as they stand keep it out. It is the largest known gap in the place-only measure |
| Charities "in" a neighbourhood | The register holds a contact address, often a home or a head office |
| Any ward or borough figure presented as a neighbourhood's | Resolution is stated on every fact. A borough figure says little about a neighbourhood |

## What the founder must decide

Work should proceed on the recommendation unless the founder says otherwise. Decisions 1 to 3 touch ADR 0006 and are the founder's alone.

### 1. Places of worship

| Choice | What it allows | What it risks |
|---|---|---|
| A. As now: the request is heard and reported as unmet | Nothing new | ADR 0006 promises that a wish for community is met through amenities, and today it is not |
| B. One feature, no faith named: "a place of worship within a walk" | It counts as one kind of meeting place | Low. It says a building is there |
| C. By faith, on an explicit request only. Near, never far. Distance only. Never in a tag. Never shown unprompted | Answers "near a synagogue" or "near a mosque" | A ranking by nearness to one faith's buildings can be read as a map of who lives where. The source must be shown to cover faiths evenly first. Needs an entry in the proxy audit |
| D. The mix of faith buildings shown on every area page, or used in a tag | "Cultural background" at a glance | It describes residents by proxy. It is what ADR 0006 exists to prevent |

Recommendation: B for the tag, and C in principle for explicit requests, held until a source passes a coverage check by faith. Not D.

### 2. Survey answers about neighbours, by borough

| Choice | What it allows | What it risks |
|---|---|---|
| A. Leave out | Nothing | Nothing |
| B. Show as borough context on an area page, labelled as the borough's | A real figure about belonging | It describes residents. It is the same for every neighbourhood in the borough. The survey has ended, so it ages |
| C. Rank on it | | Against ADR 0006, and false precision |

Recommendation: A.

### 3. How long people stay

| Choice | What it allows | What it risks |
|---|---|---|
| A. Leave out | Nothing | The tag misses what may matter most |
| B. Show on the area page, never rank | "Most households have been here over a year" | It describes residents, and correlates with tenure, age and migration |
| C. Use in the tag | A stronger tag | ADR 0006 must change, and no lawyer has read it |

Recommendation: A for now. Write the gap on the methods page.

### 4 to 9. Smaller decisions

| # | Decision | Recommendation |
|---|---|---|
| 4 | Write to parkrun for permission to show event locations and days? | Yes. Until a written yes is saved, parkrun stays out. Do not compile a list by hand from its site |
| 5 | May public facilities be named on area pages: libraries, lidos, allotment sites, children's centres? | Yes, where the source is registered for `display`. Never a childminder, a sole trader or a trustee |
| 6 | The tag's name and its bar | "Places to meet". Ship only when at least five kinds have London-wide data and the sanity set passes |
| 7 | Charities as a ranking input? | No. Address and place of work differ too often |
| 8 | A new `community` dimension in the registry, or file these under `places`? | File under `places` and `culture` now. The entries below do. A new dimension is a code change for the pipeline's owners |
| 9 | Use the GLA's Civic Strength Index? | No. Link to it from the methods page if wanted. Do not ingest it |

### Pages only the founder can open

| Page | What to save | Unblocks |
|---|---|---|
| parkrun's terms page | The terms on use of site content and data | Whether a question is worth asking |
| `activeplacespower.com/opendata` | The licence statement and the list of facility types | Sports facilities, lidos |
| Arts Council England, basic dataset for libraries | The licence line and the edition date | Libraries |
| Charity Commission, full register download | The licence line | Charities, if ever wanted |

## What was not read

| What | Standing | Relied on instead |
|---|---|---|
| Web search | None was made | Known addresses only |
| `parkrun.org.uk`, `parkrun.com`, parkrun's help site | Not read | Nothing. No claim is made about its terms |
| Active Places open data page | Not read | Recollection, marked as such |
| Arts Council England | Not read | The GOV.UK page for the 2016 edition, which says the Arts Council now maintains the list |
| Charity Commission register download | Not read | The API portal footer and the personal information charter |
| London Datastore search | Not used | Dataset addresses already known. Markets, forums and community centres were not searched for |
| GLA pages on markets and on neighbourhood planning | Not read | Nothing |
| Overture's list of categories | Not read | The guide, which confirms a taxonomy of about 2,300 categories and names none |
| OS OpenMap Local code lists | The pages held no values | Nothing. Whether it marks places of worship is not confirmed |
| Community Needs Index licence | The announcement names the UK Data Service. That page was not opened | Nothing |
| The marriage list's columns | The file was not opened, on purpose: it is not in the registry | The page's own description |
| A browser that runs scripts | Not used for reading. It was shared with other work at the time, so it was left alone after one attempt | Fetches |

## Unverified

- Everything about parkrun's terms, data and coverage.
- Active Places: licence, contents, cadence, and that it marks lidos.
- Arts Council libraries list: licence, fields, latest edition.
- Charity Commission download: that OGL v3 covers the data files, not only the site.
- That the GOV.UK footer licence covers the attachments on the Ofsted and HM Passport Office pages. It is the footer, not a statement about the file.
- Every column list. No file was opened.
- OpenActive: that every London feed is CC BY 4.0. The status page was read through a summary.
- Overture category names for community centres, markets, clubs and places of worship by faith.
- Whether the Cultural Infrastructure Map 2023 has a community centres layer. The GLA's method note says it does. The layer list read today does not show one.
- What the census holds on how long people have lived at an address. From memory.
- Active Lives cadence. From memory.

## Proposed registry entries

For review. Not added to the registry. None is `approved`: no licence page for a new source was read well enough to say so. `verified_on` is the day the page was fetched.

```toml
# Proposed by docs/research/vibes/community.md on 2026-09-23.
# Goes in registry/sources/places.toml unless the entry says otherwise.

[[source]]
id = "ofsted-childcare-providers"
name = "Childcare providers and inspections: provider-level data"
publisher = "Ofsted"
url = "https://www.gov.uk/government/statistical-data-sets/childcare-providers-and-inspections-management-information"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Ingest childcare on non-domestic premises only. Drop every childminder and every provider on domestic premises at ingest: those rows are about a person at a home address, and OGL does not cover personal data.",
    "Drop any field that names a person.",
    "Counts and distances only. Never show an inspection outcome.",
    "Feeds the family amenities tag and a nursery feature. It describes places, not the children or families who use them.",
]
status = "gated"
status_reason = "The GOV.UK page shows the OGL v3.0 footer, which is a statement about the page and not about the file. Gate: (1) open the provider-level file and save its notes sheet; (2) confirm the columns, and that domestic premises can be told apart and dropped; (3) save a dated copy of the page."
uses = ["scoring"]
cadence = "Twice a year. Latest seen: as at 30 June 2026, published 6 August 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/statistical-data-sets/childcare-providers-and-inspections-management-information",
    "https://www.gov.uk/government/statistics/childcare-providers-and-inspections-as-at-31-march-2026",
]
notes = "Read through a reader that summarises. No file was opened. Answers the founder's open question on nurseries for the family amenities tag."

[[source]]
id = "openactive-opportunity-feeds"
name = "OpenActive opportunity data feeds (sessions and facilities)"
publisher = "OpenActive publishers"
url = "https://openactive.io/"
dimension = "places"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Credit each publisher by name, with a link, beside the data, as the OpenActive attribution guide asks."
attribution_verified = false
conditions = [
    "Each feed is licensed by its own publisher. Record the licence of every feed at ingest and drop any feed that is not CC BY 4.0.",
    "Coverage follows who publishes. An area with no sessions may be an area with no publisher. Never count a gap as an absence.",
    "Resync a feed no more than once a week, as the harvesting guide asks.",
    "Use venues and recurrence only. Drop organiser and leader names.",
    "parkrun is not among the publishers listed. Do not use this entry for parkrun.",
]
status = "gated"
status_reason = "The licence is stated on the developer guide. The gate is coverage, which is a truth question and not a licence one. Gate: (1) list the feeds that hold venues in Greater London and save each feed's licence; (2) measure venues per borough; (3) if any borough has no publisher, the feature is shown as unknown there or is not shipped."
uses = ["scoring"]
cadence = "Live feeds."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://developer.openactive.io/using-data/attribution.md",
    "https://developer.openactive.io/using-data/harvesting-opportunity-data.md",
    "https://status.openactive.io/",
]
notes = "London publishers seen on the status page on 2026-09-23: Ealing, Tower Hamlets and Southwark councils, Redbridge Sports Centre, Vision Redbridge, Lampton Leisure, Coram's Fields. About 370 datasets in all, test ones included. Read through a reader that summarises."

[[source]]
id = "sport-england-active-places"
name = "Active Places open data (sports facilities in England)"
publisher = "Sport England"
url = "https://www.activeplacespower.com/opendata"
dimension = "places"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
conditions = [
    "Nothing may be downloaded until the licence has been read and saved.",
    "If released: facility type, access type and location only. No operator contact names.",
]
status = "gated"
status_reason = "The licence was not read. Gate: (1) open the page in a browser and save the licence statement; (2) if it allows commercial use, set the licence, the attribution and commercial_use from the page; (3) confirm that open-air pools are marked."
uses = ["scoring"]
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = ["https://www.activeplacespower.com/opendata"]
notes = "Recollection, not checked: the data is offered under CC BY 4.0 and covers pools, halls, pitches, tracks, courts and fitness suites, with access type. Also wanted by the gyms research."

[[source]]
id = "arts-council-england-libraries-basic-dataset"
name = "Basic dataset for libraries"
publisher = "Arts Council England"
url = "https://www.artscouncil.org.uk/supporting-arts-museums-and-libraries/supporting-libraries/basic-dataset-libraries"
dimension = "culture"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
conditions = [
    "Nothing may be downloaded until the licence has been read and saved.",
    "If released: open static libraries only. A closed library is not counted.",
]
status = "gated"
status_reason = "The licence was not read. The GOV.UK page for the 2016 edition says the Arts Council now maintains the list and publishes it each year. Gate: open the page in a browser, save the licence line and the edition date, and set the licence from it."
uses = ["scoring"]
cadence = "Annual, according to GOV.UK."
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/publications/public-libraries-in-england-basic-dataset",
]
notes = "Goes in registry/sources/culture.toml. If it clears, it replaces the held GLA libraries layer for this purpose."

[[source]]
id = "dcms-public-libraries-basic-dataset-2016"
name = "Public libraries in England: basic dataset (as on 1 July 2016)"
publisher = "Department for Digital, Culture, Media and Sport"
url = "https://www.gov.uk/government/publications/public-libraries-in-england-basic-dataset"
dimension = "culture"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
status = "held"
status_reason = "Ten years old. Libraries have closed and opened since. Useful only to check a newer list against."
uses = ["validation_only"]
cadence = "None. A snapshot of 1 July 2016, published 2017 and 2018."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/publications/public-libraries-in-england-basic-dataset",
    "https://www.data.gov.uk/dataset/782d6528-11bd-4ae0-ae47-63b456c84e76/public-libraries-in-england-basic-dataset",
]
notes = "Goes in registry/sources/culture.toml."

[[source]]
id = "parkrun-events"
name = "parkrun and junior parkrun event locations"
publisher = "parkrun"
url = "https://www.parkrun.org.uk/"
dimension = "places"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
conditions = [
    "No page of the site may be fetched by code.",
    "No list may be compiled by hand from the site.",
    "If permission is given: event name, location and day only. Never results, attendance or any runner's data.",
]
status = "held"
status_reason = "The terms were not read. Released only by written permission from parkrun that names commercial use in a neighbourhood finder, with a dated note of it in registry/evidence."
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = ["https://www.parkrun.org.uk/"]
notes = "Wikidata holds two parkrun events for the United Kingdom, so there is no open route. OpenActive does not list parkrun as a publisher."

[[source]]
id = "hmpo-places-of-worship-registered-for-marriage"
name = "Places of worship registered for marriage"
publisher = "HM Passport Office"
url = "https://www.gov.uk/government/publications/places-of-worship-registered-for-marriage"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Any use needs a fairness decision under ADR 0006 first. The feature may describe buildings only, and must never stand for who lives in an area.",
    "The list leaves out Church of England and Church in Wales premises, and any building not registered for marriages. A count by faith from this list alone is wrong, and wrong unevenly. Never publish one.",
    "One direction only: near. Never a filter or a weight for fewer or further.",
    "Never in a tag by faith. Never shown unprompted by faith.",
]
status = "held"
status_reason = "Held on fairness and on coverage, not on licence. Released by (1) a founder decision recorded in ADR 0006; (2) a second source that covers Anglican churches; (3) a coverage check by faith against a list the founder trusts."
uses = ["prototyping_only"]
cadence = "Page last updated 9 September 2026. The interval is not stated."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/publications/places-of-worship-registered-for-marriage",
]
notes = "The licence seen is the GOV.UK footer. The file was not opened, so the columns are not confirmed. The page says accuracy depends on owners telling the Registrar General when a building stops being used for worship."

[[source]]
id = "charity-commission-register-of-charities"
name = "Register of charities: data download and API"
publisher = "Charity Commission for England and Wales"
url = "https://register-of-charities.charitycommission.gov.uk/register/full-register-download"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "unknown"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "The register holds trustees' names and contacts' names and email addresses. OGL does not cover personal data. Drop every such field at ingest.",
    "A charity's address is a contact address, often a home or a head office. Never present it as where the charity works.",
    "Not a ranking input.",
]
status = "held"
status_reason = "The licence of the files was not read. The API portal shows the OGL v3.0 footer. Not needed in v1: address and place of work differ too often for an honest feature."
uses = ["prototyping_only"]
verified_how = "secondary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://api-portal.charitycommission.gov.uk/",
    "https://www.gov.uk/government/organisations/charity-commission/about/personal-information-charter",
]

[[source]]
id = "threesixtygiving-grantnav"
name = "GrantNav: UK grants data in the 360Giving standard"
publisher = "360Giving"
url = "https://grantnav.threesixtygiving.org/"
dimension = "places"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Credit the publisher named in each record, as the GrantNav terms ask."
attribution_verified = false
conditions = [
    "Each record belongs to the funder that published it. Credit by publisher.",
    "A grant is located by its recipient's address, which is not where the money was spent.",
]
status = "held"
status_reason = "Not needed in v1. Funding received is a weak and uneven sign of community life, and the location is the recipient's address."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://grantnav.threesixtygiving.org/terms"]

[[source]]
id = "mhclg-planning-data-asset-of-community-value"
name = "Assets of community value"
publisher = "Ministry of Housing, Communities and Local Government"
url = "https://www.planning.data.gov.uk/dataset/asset-of-community-value"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Crown copyright and database right 2026. Licensed under the Open Government Licence v.3.0."
attribution_verified = false
status = "held"
status_reason = "105 records from one provider, the London Borough of Camden, on 2026-09-23. It cannot rank London. Look again when most boroughs provide data."
uses = ["prototyping_only"]
cadence = "The platform collects daily."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.planning.data.gov.uk/dataset/asset-of-community-value"]

[[source]]
id = "gla-allotment-locations-2007"
name = "Allotment Locations"
publisher = "Greater London Authority"
url = "https://data.london.gov.uk/dataset/allotment-locations"
dimension = "environment"
licence = "OGL-2.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v2.0."
attribution_verified = false
status = "held"
status_reason = "Not updated since May 2007. OS Open Greenspace, which is approved, maps allotments and community growing spaces and is refreshed twice a year."
uses = ["validation_only"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://data.london.gov.uk/api/dataset/allotment-locations"]
notes = "Goes in registry/sources/environment.toml."

[[source]]
id = "gla-london-civic-strength-index"
name = "London Civic Strength Index, round 3 (2025)"
publisher = "Greater London Authority"
url = "https://data.london.gov.uk/dataset/london-civic-strength-index"
dimension = "audit"
licence = "OGL-3.0"
additional_licences = ["Bespoke-terms"]
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "unknown"
share_alike = false
attribution = "Source: Greater London Authority, London Civic Strength Index. Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Never an input to ranking, a tag or a page. It is a composite that mixes places with residents: ballots cast, change in occupational class, migration, loneliness, and recorded crime, which carries 16.6% of the weight.",
    "At borough level it scores internal and international migration as lowering civic strength. Burro must not inherit that.",
    "Its inputs include third-party data: BT footfall through the High Streets Data Service, London Sport, Trussell Trust, the Ordnance Survey National Geographic Database, and the GLA's Cultural Infrastructure Map. OGL does not cover rights the GLA cannot license.",
    "Only 11 of its measures exist below borough level.",
    "London Datastore terms apply: state that the GLA cannot warrant the quality or accuracy of the data, and never imply GLA endorsement.",
]
status = "held"
status_reason = "A reference for what others measure, and for the offline proxy audit. It describes residents as well as places, so the fairness rules keep it out of the product."
uses = ["audit_only"]
cadence = "2021, 2023 and 2025."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://data.london.gov.uk/dataset/london-civic-strength-index",
    "https://data.london.gov.uk/api/dataset/london-civic-strength-index",
]
notes = "Goes in registry/sources/audit.toml. The round 3 method note was read in full as text on 2026-09-23. No data file was opened."

[[source]]
id = "dcms-community-life-survey"
name = "Community Life Survey 2023/24"
publisher = "Department for Culture, Media and Sport"
url = "https://www.gov.uk/government/collections/community-life-survey--2"
dimension = "audit"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Published for England, regions and local authorities. Nothing smaller. A borough figure must never be shown as a neighbourhood's.",
    "It describes residents: belonging, talking to neighbours, trust, volunteering. It must never feed ranking or a tag.",
]
status = "held"
status_reason = "It describes residents and stops at the borough. The collection page says the survey has been discontinued and replaced by the Community and Engagement Survey, which was not read."
uses = ["audit_only"]
cadence = "Discontinued. Last seen: January to March 2025, published 10 December 2025."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/collections/community-life-survey--2",
    "https://www.gov.uk/government/statistics/community-life-survey-202324-annual-publication",
]
notes = "Goes in registry/sources/audit.toml."

[[source]]
id = "ocsi-community-needs-index-2023"
name = "Community Needs Index 2023"
publisher = "OCSI"
url = "https://ocsi.uk/community-needs-index/"
dimension = "audit"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
conditions = [
    "A composite that mixes community assets with measures of residents, such as loneliness, participation and population turnover. Never an input to ranking, a tag or a page.",
]
status = "held"
status_reason = "The licence was not read. The publisher's post of 3 July 2026 says the index is open data at the UK Data Service; that page was not opened. It also describes residents, so the fairness rules keep it out of the product."
uses = ["audit_only"]
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = [
    "https://ocsi.uk/community-needs-index/",
    "https://ocsi.uk/2026/07/03/community-needs-index-2023-now-available-as-open-data/",
]
notes = "Goes in registry/sources/audit.toml. On 2021 LSOAs, per the publisher's page."
```

## Sources read

| Page | Address |
|---|---|
| Places of worship registered for marriage | https://www.gov.uk/government/publications/places-of-worship-registered-for-marriage |
| Childcare providers and inspections | https://www.gov.uk/government/statistical-data-sets/childcare-providers-and-inspections-management-information |
| GIAS downloads | https://get-information-schools.service.gov.uk/Downloads |
| Public libraries in England: basic dataset | https://www.gov.uk/government/publications/public-libraries-in-england-basic-dataset |
| OS Open Greenspace, function values | https://docs.os.uk/os-downloads/products/land-and-terrain-portfolio/os-open-greenspace/os-open-greenspace-technical-specification/code-lists/functionvalue.md |
| OpenActive, attribution | https://developer.openactive.io/using-data/attribution.md |
| OpenActive, harvesting | https://developer.openactive.io/using-data/harvesting-opportunity-data.md |
| OpenActive, feed status | https://status.openactive.io/ |
| Charity Commission API portal | https://api-portal.charitycommission.gov.uk/ |
| Charity Commission personal information charter | https://www.gov.uk/government/organisations/charity-commission/about/personal-information-charter |
| GrantNav terms | https://grantnav.threesixtygiving.org/terms |
| Planning data: datasets | https://www.planning.data.gov.uk/dataset/ |
| Planning data: assets of community value | https://www.planning.data.gov.uk/dataset/asset-of-community-value |
| Community Life Survey, collection | https://www.gov.uk/government/collections/community-life-survey--2 |
| Community Life Survey 2023/24 | https://www.gov.uk/government/statistics/community-life-survey-202324-annual-publication |
| Active Lives | https://www.sportengland.org/research-and-data/data/active-lives |
| London Civic Strength Index | https://data.london.gov.uk/dataset/london-civic-strength-index |
| Allotment Locations | https://data.london.gov.uk/api/dataset/allotment-locations |
| Community Needs Index | https://ocsi.uk/community-needs-index/ |
| Overture Places guide | https://docs.overturemaps.org/guides/places/ |
