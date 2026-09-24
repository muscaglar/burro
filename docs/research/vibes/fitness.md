# fitness: gyms, studios, pools, courts and pitches

Researched 2026-09-23. A dated snapshot, not a source of truth. Nothing here is legal advice.

## Headline

Sport England's register of sports facilities, Active Places, is published under CC BY 4.0. It covers England, every facility is audited once a year, and each gym record holds the operator's name, who owns it, who manages it, how the public gets in, and how many stations it has. That is enough to say **who runs a gym and what is there**, for all of London, with no rating from anyone. It is not enough to say a gym is good, or what it costs. "Boutique" can honestly be shown only as "class studio". "Value" and "premium" can be shown only for operators on a short list the founder keeps, each backed by the operator's own published words.

## Summary

| Finding | Detail |
|---|---|
| A lawful spine exists | Active Places, CC BY 4.0. The licence page and the website terms were both read today. The terms say the Creative Commons licence governs the data and wins any conflict |
| It was thought unreadable | `community.md` did not read the page and proposed a gated, unverified entry. The page was read on 2026-09-23. The entry below replaces that one |
| What it can tier | Council leisure centre, commercial gym, school or university, sports club, community. Open to the public or not. Chain or independent, by counting an operator's sites. Gym only, or gym with a pool, courts or studios |
| What it cannot tier | Price and quality. Neither is in the register |
| Price | No lawful dataset of membership prices was found. Operators publish prices on their own sites. All six sets of site terms read either keep content to personal or private use, or forbid commercial use without consent |
| Quality | No lawful rating was found. Ratings from Google are banned. The honest position is to say nothing about quality |
| Class studios | Overture Places has categories for yoga, pilates, barre, boot camp, cycling, boxing and climbing. It is already approved. Its quality in London is unmeasured |
| Council centres | OpenActive feeds add sessions and pay-as-you-go prices under CC BY 4.0. Three London publishers were read at source. Commercial chains were not seen among the publishers |
| Courts and pitches | OS Open Greenspace is already approved and marks playing fields, tennis courts, bowling greens and golf courses. Active Places adds who may use them |
| Climbing walls | Not a facility type in Active Places. Overture is the only lawful source found |
| Every feature describes a place | None describes residents. One source found does describe residents, and is proposed as held with no use |
| Tier mix is a proxy | Where premium clubs open follows income. A tier may be asked for, in one direction only. It should never feed a tag |
| Share that can be tiered | Not measured. No data file was opened. Expectations are given below and marked as such. The first spike replaces them with counts |

How this was done, and its limits:

- No web search was made. Every page was reached by opening a known or guessed address, so sources I did not already know of will be missing.
- Pages were read through a reader that summarises. Wording quoted here must be re-read in a browser before it goes into the registry as `attribution_verified = true`, or onto a page a person sees.
- One document was read directly and in full: the Active Places website terms, a PDF of seven pages dated 13 March 2024.
- No data file was downloaded, opened or queried. Rule 1 allows that only for a registered source. Field lists come from layer definitions, which hold no records.

## Sources

"Read at source" means: **yes**, the publisher's own page stating the licence was fetched today; **part**, a related page was; **no**, the page was not read.

| What | Source | Publisher | Licence as read | Read at source | Commercial use | Resolution | All of London | Refreshed | Proposed status |
|---|---|---|---|---|---|---|---|---|---|
| Gyms, studios, pools, sports halls, courts, pitches | Active Places open data | Sport England | CC BY 4.0 | Yes | Yes, with attribution | One point per facility, grouped by site | Yes. England | Snapshot rebuilt nightly. Each facility audited yearly | **Approved**, with three items to settle before launch |
| Sessions, bookable facilities, session prices | OpenActive feeds | Each operator | CC BY 4.0 | Yes, for three publishers | Yes, with attribution to each publisher | One record per session or facility, at a venue | **No.** Only where an operator publishes | Live. Rolling window of about 14 days | Gated. Same id as `community.md` |
| Yoga, pilates, barre, boxing, climbing, martial arts; brand | Overture Places | Overture Maps Foundation | CDLA-Permissive-2.0 and others | Already `approved` | Yes, with conditions | Point | Yes. Quality unmeasured | Monthly | No change |
| Playing fields, tennis courts, bowling greens, golf courses | OS Open Greenspace | Ordnance Survey | OGL v3 | Already `approved` | Yes | One polygon per site | Yes | Every six months | No change |
| Identity of a brand | Wikidata | Wikimedia | CC0 | Already `approved` | Yes | Not a location source | | Continuous | No change |
| Chain locations copied from store locators | AllThePlaces | AllThePlaces project | CC0 waiver | Already `held` | With conditions | Point | Chains only | Weekly, from memory | No change. See decision 4 |
| Club finders, wall finders, price pages | Operators' and governing bodies' own websites | Various | Each site's own terms | Yes, for six | **No** | Point | | | **Banned**, as a class |
| Share of residents who are active | Active Lives small area estimates | Sport England | None stated | Yes | Unknown | LSOA and MSOA, **modelled**. The survey itself is by local authority | Yes | Yearly | **Held, no use.** It describes residents |
| Leisure centres of one borough | Borough open data, for example Lambeth | London boroughs | "Not set" on data.gov.uk for the one found | Part | Unknown | Point | **No.** One borough found | Links dated 2019 | None proposed. Active Places covers it |
| Registered companies | Companies House free data | Companies House | Already `held` | | | Registered office, not the gym | | | No change. A registered office is not where people train |
| Market size and structure | Industry reports | Trade bodies and analysts | Not read | No | | National | | | None proposed |
| Price level and star ratings | Google Places | Google | Already `banned` | | No | | | | No change |
| Rateable value of a gym | VOA rating list | Valuation Office Agency | Already `banned` | | No | | | | No change. It would be a tempting proxy for "premium". It stays banned |

The Food Standards Agency register is not relevant here, as the brief says.

### Active Places: what was read

| Point | What the publisher says |
|---|---|
| Licence | "Use of data made available through Sport England's Active Places Explorer ("Active Places Data") is licensed under CC BY 4.0" |
| Attribution | "You must always use the following attribution statement in any copies or modifications of Active Places Data to acknowledge the source of the information and, where possible, provide a link to this notice: "Contains Data © Sport England"" |
| What the licence leaves out | Personal data, logos and crests, "third party rights which Sport England is not authorised to license", and other intellectual property such as trade marks |
| Website terms, clause 2 | "These Website Terms do not govern use of the Active Places Data or the Active Places API". Use of both "shall be governed by the Creative Commons Licence". In a conflict, "the terms of the Creative Commons Licence shall prevail" |
| Website terms, clause 4 | Forbids using site content "for any commercial exploitation", and forbids crawling and framing the website, "except ... where ... the Creative Commons Licence expressly permit you to do so" |
| Website terms, clause 7 | "Sport England" and "Active Places" are registered trade marks |
| Size | About 125,000 facilities at about 43,000 sites in England |
| Facility types, 16 | Artificial grass pitches, athletics, cycling, golf, grass pitches, health and fitness, ice rinks, indoor bowls, indoor tennis centres, outdoor tennis courts, padel, ski slopes, sports halls, squash courts, studios, swimming pools |
| What counts as a gym | "Normally a minimum of 5 stations, although some small health & fitness gyms may be included" |
| What counts as a studio | "A purpose-built room where exercise classes and activities are held." Two subtypes: fitness studio and cycle studio |
| Pool subtypes | Main or general, leisure pool, learner or teaching, diving, lido |
| Upkeep | Sites are contacted "on a rolling annual update cycle", so that "most records are no more than a year old" |
| How to get it | A zip of CSV files, one JSON file, GIS layers, and an open API with no sign-in, limited to 120 requests in 60 seconds |

Clause 2 and clause 4 pull in different directions on a first reading. Clause 2 settles it: the licence governs the data and wins. CC BY 4.0 has no limit on commercial use. A short question to Sport England costs nothing and would close the point. It is a courtesy, and no launch waits on the answer (ADR 0007).

Fields on a gym record that matter here, read from the layer definition:

| Field | Use |
|---|---|
| Operator Name | Chain or independent. The key to the founder's operator list |
| Ownership Type, Management Type | Council, commercial, education, sports club, community. In-house, trust or contractor |
| Accessibility Type | Free Public Access, Pay and Play, Sports Club / Community Association use, Registered Membership use, Private use |
| Stations | Size of the gym |
| Operational Status | Operational, closed, planned, temporarily closed, under construction, not known |
| Year Built, Year Refurbished | Age of the facility |
| Last Updated Date | The date behind the fact |
| Site ID | Joins a gym to the pool, studios and courts on the same site |

The site table also holds a contact's title, forename, surname, job title, email and telephone number, and the address, postcode, UPRN and TOID. The licence gives no rights in personal data or third-party rights. All of these are dropped at ingest.

### OpenActive: what was read

| Publisher | Dataset site | Licence on the site | Feeds |
|---|---|---|---|
| Better | `better-admin.org.uk/api/openactive/better` | Creative Commons Attribution Licence (CC-BY v4.0) | Session series, scheduled sessions, facility uses, slots |
| Everyone Active | `data.everyoneactive.com/OpenActive/` | Creative Commons Attribution Licence (CC-BY v4.0) | The same, and course instances |
| Southwark Council | `southwarkcouncil-oa.leisurecloud.net/OpenActive/` | Creative Commons Attribution Licence (CC-BY v4.0) | The same, and course instances |

A facility record must carry a location and a provider, and may carry offers with a price. The price is for one session or one booking. It is not a membership price.

One publisher's website terms forbid crawling and any commercial use of the site. Its open data feed is a separate thing with its own licence. Burro would read the feed and never the site.

### Operators' own sites: what their terms say

| Site | Words read |
|---|---|
| GLL, which runs Better | "You may not use the content of the websites for any commercial purposes whatsoever." The list of forbidden acts includes "crawl". Last updated April 2022 |
| Third Space | "No part of the Website may be used for commercial purposes without our prior written consent." |
| Virgin Active | "You must not use any part of the materials on our Site for commercial purposes without obtaining a licence" |
| David Lloyd Clubs | "This website is for personal and non-commercial use." |
| Nuffield Health | "may not be reproduced other than when downloaded and viewed on a single device for private use only" |
| British Mountaineering Council | No use of site content "except for your own personal, non-commercial use" |

The terms of PureGym, The Gym Group and Everyone Active were not found. Nothing is claimed about them. The cautious default is the same: an operator's site is not a dataset.

## How to put a gym in a tier

A single ladder from "value" to "boutique" mixes three different questions. Two of them can be answered from data. One needs a judgement, and that judgement should be the operator's own.

| Axis | Question | Answered by | Judgement by Burro |
|---|---|---|---|
| Who runs it | Council, commercial, school, club, community | Active Places: ownership, management, access | None |
| What is there | Gym only. Gym and pool. Gym, pool and courts. Class studio | Active Places: facilities on the same site. Overture: studio categories | None |
| What it costs | Low-cost, premium | The founder's operator list | Small, and written down |

### The kinds

Each kind is a rule over stored fields. A gym gets the first kind whose rule it meets.

| Kind | Rule | From | Judgement | Honest label |
|---|---|---|---|---|
| Council leisure centre | Ownership is local authority, and access is Pay and Play or Registered Membership | Active Places | None | "Council leisure centre" |
| School, college or university | Ownership or management is education | Active Places | None | "School or university facility". Left out of counts unless access is Pay and Play |
| Sports club or community | Ownership is sports club or community organisation | Active Places | None | "Club facility" |
| Low-cost chain | Commercial, and the operator is on the list as low-cost | Active Places and the list | The list | "Low-cost chain, in the operator's own words" |
| Premium club | Commercial, and the operator is on the list as premium | Active Places and the list | The list | "Premium club, in the operator's own words" |
| Full-service club | Commercial, with a gym and a swimming pool on one site, and not on the list | Active Places | None | "Gym with a pool" |
| Other chain | Commercial, operator has several sites in England, none of the above | Active Places | A threshold, published | "Chain gym". Not "mid-market": nothing measures the middle |
| Independent | Commercial, operator has one site in England | Active Places | None | "Independent gym" |
| Class studio | A studio with no gym on the site, or an Overture studio category | Active Places, Overture | None | "Class studio". Not "boutique": the word claims quality and price |
| Not classified | No operator name, or ownership not known | | None | "Not classified". Never guessed |

### The operator list

| Point | Proposal |
|---|---|
| What it is | A reviewed CSV in the repository. One row per operator. An agent proposes, the founder approves, as with the neighbourhood map |
| Columns | The operator's name as Active Places writes it. The kind. The operator's own words, quoted, under 25 words. The link. The date read. Who approved |
| The rule | An operator is "low-cost" or "premium" only if its own corporate page or annual report says so, in words quoted in the row. No quote, no label |
| Where to read | Corporate and investor pages, and annual reports. They are written to be cited |
| Size | About 30 operators to start |
| Review | Every six months, and whenever an operator asks |
| Published | In full on the methods page, so that any operator can see its row and object |
| What it is not | A price list, a ranking, or Burro's opinion of a gym |

What operators say of themselves. Wording as a reader that summarises returned it on 2026-09-23. Re-read each in a browser before it is used.

| Operator | Page | Words |
|---|---|---|
| The Gym Group | `tggplc.com` | "The Gym Group is the original provider of high quality, low cost gym facilities in the UK." |
| PureGym | `corporate.puregym.com` | "Key elements include low-cost, flexible memberships" |
| Third Space | `thirdspace.london` | "Third Space are London's luxury health clubs" |
| Better | `better.org.uk` | "Better is part of GLL, a charitable social enterprise" |
| David Lloyd Clubs | `davidlloyd.co.uk` | "Europe's leading health and wellness group" |
| Virgin Active | `virginactive.co.uk` | No word of price or tier on the page read |

The last two rows show the limit. Some operators use no word that places them. They stay "chain gym" or "gym with a pool", which is true and says less.

### What share could be tiered

Nothing below is a count. No data file was opened. The third column is my expectation and must not be quoted as a fact.

| Axis | What it needs | Expected reach in London | Why | Measured |
|---|---|---|---|---|
| Who runs it | Ownership and management type | Nearly every gym the register holds | Both are fields on every record. "Not known" is an allowed value | No |
| Open to the public | Access type | The same | A field on every record | No |
| Chain or independent | An operator name | Most | The field exists. How often it is blank is unknown | No |
| Low-cost or premium, by the operator's words | The operator on the list | Perhaps half to three quarters of commercial gym sites. Few studios | A few chains run many sites. The Gym Group's site says about 260 across the UK, and PureGym's says over 700 across four countries. Independents and small studios will not be on a list of 30 | No |
| Price in pounds | A lawful price | None for commercial gyms. Session prices at council centres that publish a feed | Operators' sites are closed to copying | No |
| Quality | A lawful rating | None | None exists | Not applicable |
| Class studios found at all | Overture records | Unknown | London quality of Overture is the open spike in the plan | No |
| Gyms missing from the register | | Unknown | Rooms under 5 stations, personal training rooms and hotel gyms may be absent | No |

The spike that replaces this table:

1. Register Active Places. Download it once.
2. For Greater London, count operational gyms by access type, ownership and management. Count the rows with no operator name. Count sites per operator.
3. Match the 40 largest operator names to a draft list. Report the share of sites and of gyms each kind reaches.
4. In the 20 neighbourhoods of the Overture spike, compare gyms and studios in Overture with Active Places. Overture is not corrected from it, and OpenStreetMap plays no part.
5. Write one decision record with the counts.

## What could be built

Every feature below describes a **place**. None describes residents. Every one is point data, exact to the facility, measured by a walk on the road network from where people live and rolled up to the neighbourhood. None rests on a borough figure. Each has one direction only: nearer or more.

| Proposed `feature_id` | Label | Describes | From | How | Honest limits | Buildable |
|---|---|---|---|---|---|---|
| `gym_proximity` | Walk to the nearest gym open to the public | Place | Active Places | Operational gyms with public access. Network walk | Misses rooms under 5 stations | After registration |
| `gym_choice` | Gyms open to the public within a 15-minute walk | Place | Active Places | Count | Says nothing of price, quality or crowding | After registration |
| `leisure_centre_proximity` | Walk to the nearest council leisure centre | Place | Active Places | Local authority ownership, public access | A centre run by a trust or contractor is still the council's | After registration |
| `pool_proximity` | Walk to the nearest public swimming pool | Place | Active Places | Main, leisure or lido pools with public access | A lido may be seasonal. `community.md` proposes `lido_proximity` from the same source | After registration |
| `court_pitch_kinds` | Kinds of court and pitch within a 15-minute walk | Place | Active Places, OS Open Greenspace | Count of kinds: tennis, padel, squash, sports hall, grass pitch, artificial pitch | OS Open Greenspace does not say who may play. Active Places does | Tennis and playing fields now. The rest after registration |
| `studio_choice` | Class studios within a 15-minute walk | Place | Active Places, Overture | Studios with no gym on site, and Overture studio categories | Overture quality unmeasured. Category names to confirm on the pinned release | After the Overture spike |
| `lowcost_gym_proximity` | Walk to the nearest gym of a low-cost chain | Place | Active Places and the operator list | Operators whose own words say low-cost | Only operators on the list. Off by default. Never in a tag | After the list is approved |
| `climbing_wall_proximity` | Walk to the nearest indoor climbing wall | Place | Overture | Category for climbing gyms | One source, unmeasured | After the Overture spike |
| `session_kinds` | Kinds of class or session on offer at council centres nearby | Place | OpenActive | Distinct activities at venues within a walk | Only where an operator publishes. A gap is unknown, not zero | After the OpenActive gate |

Facts to show and never rank on:

| Fact | From | Why it is not ranked |
|---|---|---|
| Kinds of gym nearby: "2 council leisure centres, 3 chain gyms, 1 independent, 4 class studios" | Active Places, Overture | The mix follows income. It is a description, not a score |
| Operator names nearby | Active Places | A founder decision. See decision 2 |
| Session price at a council centre, with the date | OpenActive | One publisher's price for one session. It cannot be compared across areas |
| Year a facility was built or refurbished | Active Places | Often estimated. The field says when it is |

### A tag

| Step | Proposal |
|---|---|
| Name | "Places to train". Not "sporty" or "active": those describe people |
| First formula, untested | 0.35 `gym_choice` high + 0.25 `pool_proximity` low + 0.20 `court_pitch_kinds` high + 0.20 `park_proximity` low |
| What stays out | Every tier. Every operator name. `lowcost_gym_proximity` |
| The bar to ship | The 40-neighbourhood sanity set, as for every tag |

### Where a person would meet it

| Where | What they see | Needs |
|---|---|---|
| A prompt such as "a cheap gym and a pool nearby" | Two chips: "Low-cost gym within a 15-minute walk" and "Public pool within a 15-minute walk". Each can be removed | Two feature ids and words in the reader's vocabulary |
| A prompt such as "no budget gyms round here" | No edit, and the neutral sentence. It asks about who lives there | Section 8.4 of the contract, as now |
| A reason on a result card | "Gyms open to the public within a 15-minute walk: 6, more than 70% of the areas compared" | The `gym_choice` fact |
| "Places to train" on the area page | One line per kind: how many, the nearest, the walk in minutes, the source and date | `display` use on the source |
| A comparison row | The same figures side by side for 2 to 4 areas | Nothing new |
| What Burro does not know | A fixed line: "Burro counts gyms and says who runs them. It cannot tell you whether a gym is good, busy, or worth the price." | Nothing |
| Credit | "Contains Data © Sport England" beside every figure, and each OpenActive publisher by name | The attributions page |

## What cannot be done honestly

| Claim | Why not |
|---|---|
| "High-quality gyms" | No lawful rating exists. Review sites and Google are out. An operator's own praise is advertising |
| "Boutique" as a mark of quality | It can only mean a class studio that is not a large gym |
| A membership price for a gym | Operators publish prices on sites whose terms forbid commercial copying. No open dataset holds them |
| A price band for an area | It would need a price for every gym. Most have none on file |
| "Mid-market" | Nothing measures the middle. The honest words are "chain gym" |
| A tier for an independent gym | There is no operator statement to cite and no price to store |
| "Open 24 hours" | The register has a timings field whose coverage is unknown. No open source has reliable hours |
| How busy a gym is | Nothing records it |
| Which classes are good, or have room | Feeds list sessions. They do not judge them |
| "Every gym in the area" | The register's floor is normally 5 stations. Hotel gyms and personal training rooms may be absent |
| "People here are active" | It describes residents. The only neighbourhood figure is a model built from who lives there |
| A borough's sport figure shown for a neighbourhood | Active Lives is published for local authorities. One figure would be pasted onto about 14 neighbourhoods |
| Climbing walls, boxing gyms and martial arts clubs with any confidence | One source, and its London quality is unmeasured |
| A gym counted as absent because no source lists it | Missing is unknown, never zero |
| "Gritty" or "up and coming", worked out from the kinds of gym | It turns a fact about venues into a statement about who lives there |

## What the founder must decide

Work can proceed on each recommendation unless the founder says otherwise.

### 1. How far to take the tiers

| Option | Allows | Risks |
|---|---|---|
| A. Kinds only: council, chain, independent, class studio, gym with a pool | True for nearly every gym. No judgement by Burro | Does not say cheap or expensive, which is what was asked for |
| B. A, and "low-cost" or "premium" for operators on the list | Answers the question for the large chains | A label on a named company. It must be the operator's own words, quoted and dated |
| C. A price for each gym | The full answer | Not lawful today without each operator's consent |

**Recommendation: ship A, then B.** Drop the words "boutique" and "mid-market". Try C only by asking: see decision 7.

### 2. Whether to name operators and venues

| Option | Allows | Risks |
|---|---|---|
| Aggregates only, as today | Matches the plan and the conditions on Overture and the food register | "3 chain gyms" without names is thin |
| Operator names from Active Places | "Nearest gym is run by ..." is what people look for | Every name must be a stored fact. No logo. A wrong or stale name is seen at once |
| Venue names too | The fullest page | More to get wrong. The site name may carry a person's name |

**Recommendation: operator names, from Active Places only, on the area page.** CC BY 4.0 allows it with the credit. Overture stays aggregates only, as its entry says.

### 3. Whether a tier may touch ranking

The kinds of gym near a home follow income. Income follows protected characteristics. ADR 0006 allows a feature about venues and asks for a row in the proxy audit.

| Option | Allows | Risks |
|---|---|---|
| Tiers are facts only | Safest | "A cheap gym nearby" cannot be searched for |
| A tier may be asked for, one direction, off by default | "A low-cost gym within a walk" works | A proxy for income, used by choice of the person |
| Tiers feed a tag | A richer "vibe" | The tag would rank areas by who can afford what. It presses on rule 8 |

**Recommendation: the middle option.** `gym_choice` and `pool_proximity` may rank and may feed "Places to train". A tier is a filter a person asks for, never a weight in a tag, and never an input to a composite such as "gritty".

### 4. Whether chain locations copied from store locators may be used

Overture holds records from AllThePlaces, which copies operators' store locators. One search of its code found collectors for at least eight gym and leisure operators in Great Britain. Two of them are operators whose site terms, read above, forbid commercial use or copying. Burro would not be copying, but it would be using the copy.

**Recommendation: leave those records out of fitness features.** Active Places gives the operator's name from the operator's own return to Sport England. The Overture entry already asks that these records can be filtered.

### 5. Who keeps the operator list

It is Burro's own work and the only judgement in this design. It needs an owner, a review date and a way for an operator to object. The contract has no source id for Burro's own judgement; section 7 would need one before a tier can be a fact.

**Recommendation: the founder approves each row, the list is published on the methods page, and it is reviewed every six months.**

### 6 to 9. Smaller decisions

| # | Decision | Recommendation |
|---|---|---|
| 6 | Do school and club facilities count as gyms nearby? | No. Count only Free Public Access, Pay and Play and Registered Membership. Show the rest apart |
| 7 | Ask Sport England, and operators? | Yes to Sport England, as a courtesy. Asking ten operators for leave to show a headline price is cheap and may open option C for some |
| 8 | OpenActive now or later? | Later. The first features rest on Active Places. It shares a gate with `community.md` |
| 9 | A new `sport` dimension in the registry? | No. File under `places`, which needs no code change |

## What this research turned up about other work

| Where | Finding |
|---|---|
| `community.md`, Active Places | Its entry is gated and unverified because the page was not read. The licence has now been read. The entry below replaces it. Its third gate, that open-air pools are marked, is met: lido is a pool subtype |
| `community.md`, OpenActive | Its entry stands. This report adds three dataset sites read at source, and four conditions |
| `overture-places` | Its condition "aggregates only" blocks naming a gym. That is right for Overture and is why names should come from Active Places |
| `overture-places` | The category list read was for October 2025. Overture's guide says the `categories` field is due to be removed in the September 2026 release. Confirm the fitness categories on the pinned release |
| `alltheplaces-poi` | Collectors exist for at least eight gym and leisure operators in Great Britain. This sharpens the reason it is held |
| `companies-house-free-company-data` | Nothing changes. A registered office is not a gym |
| Contract, section 3.1 | The feature table has no dimension for sport. One would be added with the first feature |

## What was not read

| What | Standing | What I relied on instead |
|---|---|---|
| Active Places licence page, as a person sees it | Not read as a person sees it | The page's text and the website terms, read on 2026-09-23 |
| The information file inside the CSV download | Not downloaded. The source is not registered | Nothing. Listed before launch |
| Active Places data model spreadsheets | Not opened | Layer definitions and the help page |
| Counts of gyms in London | Not queried. The source is not registered | Nothing. Shares are expectations |
| PureGym website terms | Not read | Nothing claimed |
| The Gym Group website terms | The legal index lists none | Nothing claimed |
| Everyone Active website terms | The index page held no terms | Nothing claimed |
| The Gym Group results announcement | Not read | The corporate home page |
| Industry totals | Not read | Nothing. No national total of gyms is quoted |
| Two booking marketplaces | Not read | Nothing claimed about either |
| London Datastore search | Not used | One search of data.gov.uk |
| OS OpenMap Local code lists | Not read | Nothing. Not proposed |
| The climbing wall finder itself | Only the site's terms were read | The terms |
| Overture's current category list | Not read | The October 2025 counts file in Overture's documentation |
| OpenActive status page, as a list | Three reads gave three totals | Each dataset site, read on its own |
| Web search | None was made | Known and guessed addresses |

## Unverified

- Every share in "What share could be tiered".
- That the operator name field is filled in for most gyms.
- That small studios are in Active Places at all.
- That the coordinates in Active Places carry no third-party rights.
- That the information file in the download says the same as the licence page.
- Overture's coverage of gyms and studios in London, and its current category names.
- That commercial chains publish no OpenActive feed. They were not seen on the status page. The page is long and was read through a summary.
- Every quotation from an operator's page. Each was returned by a reader that summarises.
- The count of sites for any operator. Figures are as each operator's page gave them on the day.
- The management types in Active Places beyond the first four. The help page was not read to its end.
- Whether Active Places records opening hours usefully.
- How AllThePlaces is refreshed. From memory.

## Proposed registry entries

For review. Not added to the registry. The block was loaded with the registry's own model and rules on 2026-09-23 and passes, with the warnings that any approved entry with open launch items gives.

One entry is proposed as `approved`. The licence page was read, it names CC BY 4.0, and the website terms say that licence governs the data. A more cautious registrar could hold it at `gated` until the information file has been read.

```toml
# Proposed by docs/research/vibes/fitness.md on 2026-09-23.
# Every entry has dimension "places", so each goes in registry/sources/places.toml,
# except the last, which goes in registry/sources/audit.toml.
# Two ids are shared with docs/research/vibes/community.md. Register each id once.

# Same id as community.md proposes. This version replaces that one: the licence
# was read here, and it was not read there.
[[source]]
id = "sport-england-active-places"
name = "Active Places open data (sports facilities in England)"
publisher = "Sport England"
url = "https://www.activeplacespower.com/pages/downloads"
dimension = "places"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/legalcode.en"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains Data © Sport England"
attribution_verified = false
conditions = [
    "Take the data from the bulk download or the open data API named on the downloads page. Never crawl the website: clause 4 of the website terms forbids crawling and framing.",
    "Drop at ingest every field that names or contacts a person: title, forename, surname, job title, email and telephone number. The licence gives no rights in personal data.",
    "Drop at ingest the address lines, postcode, UPRN and TOID. The licence excludes third-party rights, and these fields may carry Royal Mail or Ordnance Survey rights.",
    "Keep only: site id, facility id, coordinates, Output Area and LSOA codes, facility type and subtype, stations, operator name, ownership type, management type, access type, operational status, and the opened, closed, built, refurbished and last-updated dates.",
    "Count a facility only when its status is Operational. Closed, planned, temporarily closed and under construction are never counted as open.",
    "Count as open to the public only the access types Free Public Access, Pay and Play, and Registered Membership use. Sports Club / Community Association use and Private use are counted apart or left out.",
    "A Health and Fitness Gym is 'normally a minimum of 5 stations'. Smaller rooms may be missing. Never describe a count as every gym.",
    "Climbing walls, boxing gyms and martial arts clubs are not among the 16 facility types. An area with none in this source is unknown for those, not zero.",
    "No label of price or of quality is ever derived from this source. It says who runs a facility and what is there.",
    "Show the attribution wherever a figure built from this data appears, with a link to the licence notice where possible. Say on the methods page that Burro filters and counts the data, because CC BY 4.0 asks that changes are indicated.",
    "'Sport England' and 'Active Places' are registered trade marks. Name Sport England as the source. Do not use either name or the logo as a mark, and do not imply endorsement.",
    "Save the information file from inside the CSV download to registry/evidence at first ingest.",
]
status = "approved"
before_launch = [
    "Open https://www.activeplacespower.com/pages/license in a browser, save it to registry/evidence, and set attribution_verified if the wording matches.",
    "Read the information file inside the CSV download. The downloads page says it holds 'additional information on licensing and data currency'. If it differs from the licence page, it governs and this entry goes back to gated.",
    "Ask Sport England in writing to confirm two things: that a commercial consumer product may use the data under CC BY 4.0, given the words on commercial exploitation in clause 4 of the website terms; and whether the coordinates derive from a licensed address product.",
]
uses = ["scoring", "validation_only"]
cadence = "The snapshot is rebuilt nightly. Each facility is audited on a rolling annual cycle. Pin the download date for each data release."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.activeplacespower.com/pages/license",
    "https://www.arcgis.com/sharing/rest/content/items/961ad5b3bd124014b558f85b796bf8e2/data?f=json",
    "https://dataplatform.activeplacespower.com/documents/Active%20Places%20Power%20Website%20T&Cs.pdf",
    "https://www.activeplacespower.com/pages/downloads",
    "https://www.arcgis.com/sharing/rest/content/items/f5415d42f5594ea1a81a584beaa792a3?f=json",
    "https://creativecommons.org/licenses/by/4.0/legalcode.en",
]
notes = "How it was verified: the licence page was read on 2026-09-23, at the second evidence link. It says: 'Use of data made available through Sport England's Active Places Explorer (\"Active Places Data\") is licensed under CC BY 4.0.' The same statement is in the item record of the health and fitness, studios, swimming pools and sites layers. The website terms, a PDF dated 13 March 2024, were read directly and in full. Clause 2 says the terms 'do not govern use of the Active Places Data or the Active Places API', that such use 'shall be governed by the Creative Commons Licence', and that the licence prevails in a conflict. Clause 4 forbids commercial exploitation of site content except where the licence expressly permits it, which is why a question for Sport England is listed, as a courtesy. The field lists were read from the layer definitions, which hold no records. No data file was downloaded, opened or queried. A more cautious registrar could keep this gated until the information file has been read; a spike would then need prototyping_only. 'display' is left out until the founder decides whether operators or venues are named."

# Same id as community.md proposes. Merge the two: keep that entry's coverage gate,
# and add the conditions and evidence below.
[[source]]
id = "openactive-opportunity-feeds"
name = "OpenActive opportunity data feeds (sessions and facilities)"
publisher = "OpenActive publishers"
url = "https://status.openactive.io/"
dimension = "places"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Credit each publisher by name, with a link to its dataset site, beside the data, as the OpenActive attribution guide asks."
attribution_verified = false
conditions = [
    "Each feed is licensed by its own publisher. Save the licence statement from every dataset site at ingest, and drop any feed that is not CC BY 4.0.",
    "Read only the feed addresses a dataset site names. Never read the same operator's website in its place: the website terms of one London publisher forbid crawling and commercial use of the site.",
    "Coverage follows who publishes. An area with no sessions may be an area with no publisher. Never count a gap as an absence.",
    "A price in a feed is the price of one session or one booking. It is never shown as a membership price, and never used to label an operator.",
    "Use venue, facility type, activity, recurrence and offer price only. Drop organiser and leader names.",
    "Feeds cover a rolling window of about 14 days. Take a dated snapshot for each data release, and resync no more often than the harvesting guide asks.",
    "Commercial gym chains were not seen among the publishers. Do not expect this source to describe them.",
]
status = "gated"
status_reason = "The licence is stated on the developer guide and on each dataset site read. The gate is coverage, which is a truth question and not a licence one. Gate: (1) list the feeds that hold venues in Greater London and save each dataset site's licence statement; (2) measure venues per borough; (3) if any borough has no publisher, the feature is shown as unknown there or is not shipped."
uses = ["scoring"]
cadence = "Live feeds, updated every minute on the dataset sites read."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://developer.openactive.io/using-data/attribution",
    "https://better-admin.org.uk/api/openactive/better",
    "https://data.everyoneactive.com/OpenActive/",
    "https://southwarkcouncil-oa.leisurecloud.net/OpenActive/",
    "https://developer.openactive.io/data-model/types/facilityuse",
    "https://developer.openactive.io/data-model/types/offer",
    "https://status.openactive.io/",
]
notes = "Three dataset sites were read on 2026-09-23: Better, Everyone Active and Southwark Council. Each names the Creative Commons Attribution Licence (CC-BY v4.0) and its own name as the attribution. The developer guide says publishers must license under CC BY 4.0 and that data users must attribute 'wherever it is used'. A FacilityUse record must carry a location and a provider, and may carry offers with a price. The status page listed several hundred datasets; three reads of it gave three different totals, so none is quoted. Not needed for the first fitness features, which rest on Active Places."

[[source]]
id = "fitness-operators-own-websites"
name = "Gym, club and governing-body websites (club finders, wall finders and price pages), as a data source"
publisher = "Various operators and governing bodies"
url = "https://www.gll.org/about-us/policies-and-statements/terms-of-use"
dimension = "places"
licence = "Bespoke-terms"
commercial_use = "no"
share_alike = false
status = "banned"
status_reason = "Six sets of website terms were read on 2026-09-23 and each keeps site content to personal or non-commercial use, or forbids commercial use without a licence. One also names crawling. Copying a location list or a price list from such a site, by program or by hand in bulk, is not allowed. This is a class entry: it stands for every operator's own site unless that operator has its own entry. What would change it for one operator: a written licence from that operator, registered as its own entry with a dated note of it in registry/evidence. An operator's open data feed is a different source and has its own entry."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gll.org/about-us/policies-and-statements/terms-of-use",
    "https://www.thirdspace.london/website-tcs/",
    "https://www.virginactive.co.uk/the-legal-stuff/website-terms-of-use",
    "https://www.davidlloyd.co.uk/policy/website-terms-and-conditions/",
    "https://www.nuffieldhealth.com/terms/nuffield-health-website-terms-and-conditions",
    "https://thebmc.co.uk/bmc-website-terms-of-use",
]
notes = "Read through a reader that summarises. The terms of PureGym, The Gym Group and Everyone Active were not found and nothing is claimed about them; the ban is the cautious default for any site whose terms have not been read. The ban is on using a site as a dataset. Citing one sentence in which an operator describes itself, with a link and a date, is a citation and not an ingest; see the operator list in the report."

# Goes in registry/sources/audit.toml.
[[source]]
id = "sport-england-active-lives-small-area-estimates"
name = "Active Lives small area estimates (share of residents who are active, by LSOA and MSOA)"
publisher = "Sport England"
url = "https://www.sportengland.org/research-and-data/tools/small-area-estimates"
dimension = "audit"
licence = "None-stated"
commercial_use = "unknown"
share_alike = false
conditions = [
    "It describes residents: the share of people in an area who are active. ADR 0006 keeps it out of ranking, tags and text.",
    "It is a model. The figures are estimated from survey answers and census characteristics of the people who live in each area, so they restate who lives there.",
    "The survey itself is published for local authorities. A borough figure says little about a neighbourhood.",
]
status = "held"
status_reason = "It describes who lives somewhere, and no licence is stated on the page read. Registered so that nobody adds it later as a measure of how sporty an area is. No use is proposed, not even for the audit."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.sportengland.org/research-and-data/tools/small-area-estimates",
    "https://www.sportengland.org/research-and-data/data/active-lives",
]
notes = "Read through a reader that summarises. The page says the estimates use multilevel regression and poststratification over Active Lives and census data, for Lower and Middle Layer Super Output Areas."
```

## Sources read

All read on 2026-09-23. The addresses given for the Active Places pages are the pages a person would open.

| Page | Address |
|---|---|
| AllThePlaces, collector code (searched, not run) | https://github.com/alltheplaces/alltheplaces |
| Active Places, licence page | https://www.activeplacespower.com/pages/license |
| Active Places, licence page text | https://www.arcgis.com/sharing/rest/content/items/961ad5b3bd124014b558f85b796bf8e2/data?f=json |
| Active Places, website terms (PDF, read directly) | https://dataplatform.activeplacespower.com/documents/Active%20Places%20Power%20Website%20T&Cs.pdf |
| Active Places, downloads | https://www.activeplacespower.com/pages/downloads |
| Active Places, about, help and changes | https://www.activeplacespower.com/pages/about, https://www.activeplacespower.com/pages/help, https://www.activeplacespower.com/pages/breakingchanges |
| Active Places, health and fitness layer record | https://www.arcgis.com/sharing/rest/content/items/f5415d42f5594ea1a81a584beaa792a3?f=json |
| Active Places, health and fitness layer definition | https://services-eu1.arcgis.com/s9MgJChYyPlPX2Nk/arcgis/rest/services/GIS_Active_Places_Power_Health_and_Fitness/FeatureServer/7?f=json |
| Creative Commons Attribution 4.0, legal code | https://creativecommons.org/licenses/by/4.0/legalcode.en |
| OpenActive, attribution | https://developer.openactive.io/using-data/attribution |
| OpenActive, facility and offer types | https://developer.openactive.io/data-model/types/facilityuse, https://developer.openactive.io/data-model/types/offer |
| OpenActive, feed status | https://status.openactive.io/ |
| OpenActive dataset site, Better | https://better-admin.org.uk/api/openactive/better |
| OpenActive dataset site, Everyone Active | https://data.everyoneactive.com/OpenActive/ |
| OpenActive dataset site, Southwark Council | https://southwarkcouncil-oa.leisurecloud.net/OpenActive/ |
| Overture Places, guide and schema | https://docs.overturemaps.org/guides/places/, https://docs.overturemaps.org/schema/reference/places/place/ |
| Overture Places, category counts, October 2025 | https://raw.githubusercontent.com/OvertureMaps/docs/main/docs/guides/places/csv/2025-10-22-counts.csv |
| OS Open Greenspace, function values | https://docs.os.uk/os-downloads/products/land-and-terrain-portfolio/os-open-greenspace/os-open-greenspace-technical-specification/code-lists/functionvalue |
| Sport England, Active Lives | https://www.sportengland.org/research-and-data/data/active-lives |
| Sport England, small area estimates | https://www.sportengland.org/research-and-data/tools/small-area-estimates |
| GLL, website terms | https://www.gll.org/about-us/policies-and-statements/terms-of-use |
| Third Space, website terms | https://www.thirdspace.london/website-tcs/ |
| Virgin Active, website terms | https://www.virginactive.co.uk/the-legal-stuff/website-terms-of-use |
| David Lloyd Clubs, website terms | https://www.davidlloyd.co.uk/policy/website-terms-and-conditions/ |
| Nuffield Health, website terms | https://www.nuffieldhealth.com/terms/nuffield-health-website-terms-and-conditions |
| British Mountaineering Council, website terms | https://thebmc.co.uk/bmc-website-terms-of-use |
| The Gym Group, corporate site | https://www.tggplc.com/ |
| PureGym, corporate site | https://corporate.puregym.com/ |
| data.gov.uk, search for leisure centres | https://www.data.gov.uk/search?q=leisure+centres+london |
