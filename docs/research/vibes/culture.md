# culture: cultural venues, and what "highly ranked" can honestly mean

Gathered on 2026-09-23. A dated snapshot, not a source of truth. Nothing here is legal advice. No data file was downloaded. Two count queries were run against Wikidata and five against the Wikimedia page view service, both CC0, to size what they hold. Every other statement about coverage is the publisher's, not a finding.

## Headline

Burro cannot lawfully hold a rating of any venue, and should not try. Every ratings and awards site read today forbids commercial reuse or building a database from its pages. What Burro can say, and prove, is **who has recognised a venue, under which scheme, on what date**: an accredited museum, an organisation in the Arts Council's National Portfolio, a national museum, a listed building, a World Heritage Site. The word for that is "recognised", always followed by the name of the scheme. It is never "best", "top" or "highly rated". The two lists that matter most, both from Arts Council England, were not read. They are the first thing for the founder to open.

## Summary

| The founder asked for | The engine has today | What is missing | What this research found |
|---|---|---|---|
| Cultural activities | `culture_venues`: one count per km² of six kinds of venue, from Overture Places | Which kinds are there. How far they are. Anything on screen that makes culture the subject | A count of kinds within a walk can be built now. A count of venues within 30 minutes by public transport can be built from the travel table |
| "Especially highly ranked ones" | Nothing | Any sign of standing | Four lawful kinds of standing exist. None is a rating. See "What highly regarded can mean" |
| Theatres, cinemas, galleries, museums, music venues, libraries | Counted together, not apart | A source per kind | The GLA map has a layer for each and is still gated. Overture has them now, quality unmeasured |
| Festivals and markets | Nothing | A source | None found. No London-wide open list of either was found |

Six things matter most.

1. **No rating can be used.** The terms of five sites that publish rankings, awards or listings were read. Each limits use to personal or non-commercial purposes, or forbids building a database. Overture Places holds no rating, review count, popularity or capacity field.
2. **Standing can be stated as recognition.** A public body applied a published standard and put a venue on a list. That is a fact with a source and a date, which is what rule 6 asks for.
3. **Recognition is not quality, and the page must say so.** Accreditation is a standard for how a museum is run. Portfolio funding follows policy as well as merit. A listing grade is about the building, not the stage.
4. **Wikipedia page views are lawful and unfair.** They are CC0. They measure how often the world reads an English article. A waxworks attraction's article was read about fourteen times as often as a chamber music hall's. Hold them for prototyping only.
5. **Recognition follows money and age.** Old, large, central institutions are listed, funded and written about. New, small and community-led ones are not. A score built on recognition alone would call outer London and newer scenes empty. It must sit beside the plain venue count, never replace it, and needs a row in the proxy audit of ADR 0006.
6. **Every feature proposed here describes a place.** None describes who lives there. The one dataset that measures who takes part in culture is a survey of residents, published by borough. It stays out.

## How each page was read

| Code | Meaning |
|---|---|
| S | Read through a reader that summarises. Wording may differ from the page. Re-check before it goes in the registry |
| Q | A count query. The result was read through the same tool |
| R | Taken from this repository's registry. Not re-opened |
| X | Not read. Nothing is claimed about it |

One page was opened in a rendered browser: the London Datastore search, which gave no results. No licence page was read by eye. So no attribution wording here is verified.

## What "highly regarded" can mean

There are five kinds of evidence that a venue has standing. Burro can use the first three.

| Kind | What it is | Who decides | Lawful source | Use |
|---|---|---|---|---|
| 1. Recognition | A public body applied a published standard | Arts Council England, DCMS, Historic England, UNESCO | Arts Council lists (not yet read). Planning data platform (OGL v3) | Yes. This is what "recognised" means |
| 2. Protection of the building | The building is listed | Historic England | `historic-england-listed-buildings`, approved | Yes, said of the building only |
| 3. Measured use | Visits counted by the publisher | DCMS, for the museums it sponsors | GOV.UK statistics | Yes, as a fact on a page. Too few sites to score |
| 4. Attention | How often an article is read. How many languages it is in | Readers of Wikipedia | Wikimedia page views, Wikidata. Both CC0 | No. It measures fame |
| 5. Opinion | Ratings, reviews, critics' lists, awards | Reviewers, critics, juries | None. Terms forbid it, or the data is too thin | No |

### Words Burro can stand behind

| Say | Means exactly | Must carry |
|---|---|---|
| "Accredited museum" | On the list of museums accredited under the UK Museum Accreditation Scheme | The list's date |
| "In Arts Council England's National Portfolio" | Funded by the Arts Council for the stated period | The period |
| "National museum" | One of the museums DCMS sponsors | The date |
| "In a listed building, Grade II*" | The building is on the National Heritage List for England | The date. The word "building" |
| "In a World Heritage Site" | Inside the inscribed boundary | The date |
| "Recorded {n} visits in {year}" | The publisher's own count | The year and the publisher |
| "Recognised venues" | Venues on at least one of the first three lists | The names of the lists, one tap away |
| "{n} of the {m} kinds of cultural venue" | A count of kinds found within the stated walk | The kinds, the walk, the source |

### Words Burro must never use

| Never | Why |
|---|---|
| "Best", "top", "top-rated", "highly rated", "highly ranked", "five-star" | Burro holds no rating. Each word claims one |
| "Acclaimed", "renowned", "world-class", "must-see", "hidden gem" | Opinion, with no fact behind it |
| "Award-winning" | Only with the award and year named, from a source Burro may use. None is registered |
| "Vibrant", "thriving", "cultural hotspot", "cool", "trendy", "up-and-coming" | No dataset measures them. The last is also a claim about who is moving in |
| "Popular with" anyone | It describes people |
| Any score out of 5, 10 or 100 for a venue | Burro ranks areas, never venues |
| That a venue not on a list is worse | The lists are applied for. Many good venues never apply |
| That the Arts Council, Historic England or the GLA backs Burro or an area | The Open Government Licence forbids suggesting endorsement. The London Datastore terms say the same |
| What is on, when it opens, what it costs | No open source holds programmes, hours or prices |
| A borough figure as a neighbourhood's | A borough holds about 14 neighbourhoods |

The verifier already refuses "safe" and its forms. The same step could refuse the words in the first three rows. That is a change to `packages/core`, which this research does not make.

## Sources

Licence is given as the page shows it. "All London" means the publisher covers every borough, not that coverage was measured.

| # | Source | Publisher | What it measures | Licence as shown | Commercial use | Finest unit | All London | Refreshed | Read | Proposed status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | National Portfolio, investment programme data | Arts Council England | Organisations funded for a multi-year period, with art form and grant | Not read | Unclear | Organisation. Whether the file holds a venue postcode is not known | Yes, England | Per funding round | X | gated |
| 2 | List of accredited museums | Arts Council England | Museums that meet the UK accreditation standard | Not read | Unclear | Museum. Address fields not known | Yes | Not known | X | gated |
| 3 | Mapping Museums database | Birkbeck, University of London | Over 4,000 UK museums since 1960 | "Creative Commons (BY)", no version | Yes, with credit | Museum | Yes, UK | Last update 1 February 2026. "No longer being maintained" | S | gated |
| 4 | National Heritage List: listed buildings | Historic England, on the Planning Data platform | 382,270 listed buildings: name, grade, point, date | OGL v3 | Yes, with conditions | Point | Yes | Collected daily | R, S | approved, as now |
| 5 | World heritage sites | Historic England and MHCLG, on the Planning Data platform | 40 sites in England, as boundaries | "Licensed under the Open Government Licence v.3.0" | Yes, with conditions | Polygon | The London sites. Count not checked | Collected daily | S | approved |
| 6 | Cultural Infrastructure Map 2023, per-layer files | Greater London Authority | Venues by kind: theatres, cinemas, museums and public galleries, commercial galleries, arts centres, dance, studios | OGL v3, with "Contains Audience Agency data" and "Contains CAMRA data" | Yes, with conditions | Point | Yes | Captured spring and summer 2022. Music files updated March 2024 | R, S | gated, as now |
| 7 | Cultural Infrastructure Map 2023, music, libraries, LGBTQ+ layers | Greater London Authority, with named outside bodies | Music venues, grassroots venues, nightclubs, libraries, LGBTQ+ venues | OGL v3 on the page. Outside bodies named per layer | Unclear | Point | Yes | As above | R, S | held, as now |
| 8 | Cultural Infrastructure Map 2025 | Greater London Authority | One workbook and a zones file. Data collected late 2025 | None stated | Unclear | Point | Yes | 2026 | R, S | held, as now |
| 9 | Overture Places | Overture Maps Foundation | Places by category. About 280 basic categories | CDLA-Permissive-2.0, Apache 2.0, CC0 by record | Yes, with conditions | Point | Yes. Quality unmeasured | Monthly | R, S | approved, as now |
| 10 | Wikidata, cultural venues | Wikimedia Foundation | Items for venues: kind, coordinates, heritage status, capacity, awards, links to articles | CC0 | Yes | Point | 2,061 items found. See below | Continuous | S, Q | approved |
| 11 | Wikimedia page views | Wikimedia Foundation | Daily and monthly reads of each Wikipedia article | CC0 1.0 | Yes | Article. Not a place | Only venues with an article | Daily | S, Q | held |
| 12 | Museums and galleries monthly visits | DCMS | Visits to the 15 museums DCMS sponsors, by site | OGL v3, from the GOV.UK footer | Yes | Site | No. National museums only | Monthly. Latest April to June 2026 | S | gated |
| 13 | Public libraries basic dataset | Arts Council England, before that DCMS | One row per library | 2016 edition: OGL. Current edition not read | 2016: yes | Library | Yes | 2016 edition never. Current edition yearly, per GOV.UK | S | See `community.md`, which proposes both entries |
| 14 | Theatres Database | Theatres Trust | Almost 4,000 theatre buildings, past and present | Site terms: no commercial use "without obtaining a licence" | No | Building | Yes | Offline. "Taken offline following a review" | S | held |
| 15 | Theatres at Risk register | Theatres Trust | Theatre buildings under threat | Same site terms | No | Building | Few in London | Yearly | S | held, under 14 |
| 16 | Visitor figures | Association of Leading Visitor Attractions | Visits to 409 member sites, 2025 | None stated. "© 2026 Cybertrek Ltd, ALVA" | Unclear | Site | Members only | Yearly | S | held |
| 17 | Annual Survey of Visits to Visitor Attractions | VisitBritain and VisitEngland | Visits per attraction, 2024 | Site terms: "personal, non-commercial use only" | No | Site | Attractions that answer | Yearly | S | held |
| 18 | Museum of the Year, and the site | Art Fund | Prize winners and shortlists | Site terms forbid commercial use and creating a database | No | Venue | A few a year | Yearly | S | held |
| 19 | Olivier Awards, and the site | Society of London Theatre | Awards to productions and people | Site terms: "personal and non-commercial purposes". No harvesting | No | Production, not venue | West End | Yearly | S | held |
| 20 | The Stage Awards, and the site | The Stage | Awards to theatres | Site terms: personal use. No database | No | Venue | A few a year | Yearly | S | held |
| 21 | Listings and "best of" lists | Time Out | Editorial picks and rankings | Site terms: personal use. No use on "any artificial intelligence (AI) or machine learning platform" | No | Venue, area | Yes | Continuous | S | banned |
| 22 | Cinema Treasures | Cinema Treasures | Cinemas past and present, written by users | Site terms: personal use. No "automated means" | No | Cinema | Yes | Continuous | S | banned |
| 23 | Participation Survey | DCMS with Arts Council England | Whether adults took part in arts, museums, libraries, heritage | OGL v3, from the GOV.UK footer | Yes | Local authority | Yes | Yearly | S | held, audit only |
| 24 | Accredited Museums grants 2017 to 2019 | Arts Council England, on 360Giving | Grants to accredited museums | CC BY 4.0 | Yes, with credit | Recipient | Partial | Published 2019. Not updated | S | none: old, and a grant is not standing |
| 25 | Assets of community value | MHCLG Planning Data platform | Buildings a community has nominated | OGL v3 | Yes | Point | No. 105 records, all from Camden | Daily | S | See `community.md` |
| 26 | Heritage at risk | Historic England, on the Planning Data platform | 5,490 entries at risk | OGL v3 | Yes | Point or polygon | Yes | Yearly | S | none: it measures neglect, not standing |
| 27 | Creative Enterprise Zones data repository | Greater London Authority | Jobs and firms by zone, on best-fit MSOAs | None stated | Unclear | MSOA | Zones only | Over a year old | S | none: no licence, and it counts firms |
| 28 | Street markets | | | | | | No London-wide list found. Camden and Hackney publish their own | | S | none |
| 29 | Festivals | | | | | | No dataset found | | S | none |
| 30 | Music Venue Trust | Music Venue Trust | Grassroots music venues | Not read | Unclear | Venue | Members | | X | none |

Google Places and Street View are banned in the registry already. TripAdvisor's terms were not read and nothing is proposed for it.

### What Wikidata holds, by count

Query run on 2026-09-23 against the Wikidata Query Service. It asked for items placed in Greater London whose kind is, or is a kind of, each class below. It counted; it kept nothing.

| Kind | Items | With a capacity | With an English Wikipedia article |
|---|---|---|---|
| Theatre | 355 | 73 | 236 |
| Museum | 370 | 0 | 243 |
| Cinema | 1,187 | 14 | 102 |
| Music venue | 154 | 23 | 123 |
| Art gallery | 115 | 0 | 56 |
| Library | 411 | 0 | 73 |

| Across theatres, museums, cinemas, music venues and galleries | Items |
|---|---|
| All | 2,061 |
| With coordinates | 1,960 |
| With a heritage designation | 261 |
| With a closing date | 181 |
| With any award recorded | 14 |

What the counts say:

- Wikidata lists closed venues beside open ones. 181 carry a closing date. Others will have closed with no date entered. The cinema count is far above any count of working cinemas.
- Capacity is known for about one theatre in five and one music venue in seven. It cannot be a London-wide figure.
- Awards are recorded for 14 items of 2,061. Awards cannot be a feature.
- A venue may be counted under two kinds. The totals were not de-duplicated by hand.

### What page views measure

Reads of the English Wikipedia article by people, not by crawlers, September 2025 to August 2026. Totals were summed by the reader. One was checked by hand and was 20 out, so figures are rounded to the nearest thousand.

| Article | Reads in 12 months, about |
|---|---|
| British Museum | 440,000 |
| Madame Tussauds | 249,000 |
| Tate Modern | 142,000 |
| Wigmore Hall | 18,000 |
| Hackney Empire | 15,000 |

| Why it is not a fair sign of standing | |
|---|---|
| It counts readers anywhere in the world | A visitor attraction outranks a concert hall |
| It counts one language | A venue serving a community that reads another language scores low |
| It moves with the news | One article's busiest month was about 60% above its usual month |
| It needs an article to exist | Small, new and community-led venues have none |
| A redirect or a renamed page splits the count | The publisher says redirects are not counted as views of the page |
| Some automated traffic is counted as people | The publisher's own page says detection is incomplete |

## Which can be had for all of London at neighbourhood scale

| Signal | All London | Neighbourhood scale | Verdict |
|---|---|---|---|
| Venues by kind, as points | Yes, from Overture now, from the GLA map once its entry is approved | Yes | Build |
| Accredited museums | Yes, if the list holds an address | Yes, if so | Build after the list is read |
| National Portfolio organisations | Yes | Only if the file holds the venue's postcode. An office address is not a venue | Build after the list is read, or drop |
| Listed buildings | Yes | Yes | Build. The source is approved |
| World Heritage Sites | A handful | Yes, but most areas have none | A fact on a page, not a score |
| Visits to national museums | No. Central sites only | Yes for those sites | A fact on a page, not a score |
| Capacity | No. One theatre in five | | Cannot |
| Programme volume | No | | Cannot |
| Awards | No. 14 of 2,061 | | Cannot |
| Page views | Only venues with an article | | Do not |
| Who takes part in culture | Borough only | No | Do not. It describes residents |

## What could be built

Every feature below describes a **place**. None describes residents. Each has one direction: a person may ask for more or nearer, never fewer or further. The ids are proposals; adding one is a change to the contract and to `packages/core`, for their owners.

| Proposed `feature_id` | Label | Describes | From | Native resolution | Buildable | Honest limits |
|---|---|---|---|---|---|---|
| `culture_kinds_nearby` | Kinds of cultural venue within a 15-minute walk | Place | `overture-places` now. The GLA layers once cleared | Point, network walk | After the Overture quality spike | Counts kinds, not quality. Ten cinemas are one kind. A zero from Overture may be a gap, so it is unknown, not zero |
| `culture_reach_pt` | Cultural venues within 30 minutes by public transport | Place | The same points, and the travel table | Point to hexagon, then the travel table | When real travel times exist | v1 holds weekday morning times only. Culture is used in the evening. The sentence must say "on a weekday morning" until evening times exist |
| `culture_recognised_nearby` | Recognised venues within 30 minutes by public transport | Place | Arts Council lists, DCMS list | Point, if the lists hold addresses | After the founder opens the Arts Council pages | Recognition is applied for. It follows age and money. Central London will dominate. Never shown without `culture_venues` beside it |
| `museum_accredited_nearby` | Accredited museums within a 20-minute walk | Place | Arts Council list, or Mapping Museums | Point | After the gate | The standard is about how a museum is run. Most areas will have none, so most will tie |
| `culture_listed_buildings` | Listed buildings built as theatres, cinemas, libraries, museums or music halls | Place, its buildings | `historic-england-listed-buildings` | Point | Now. The source is approved | The list has no field for kind of building. The match is on words in the name, which is crude. The name is the historic one: a listed cinema may now be a church. It must be labelled as built heritage |
| `cinema_nearby` | Cinemas within a 15-minute walk, and how many are not part of a chain | Place | `overture-places`, brand field | Point | After the Overture quality spike | Brand coverage is unmeasured. "Not part of a chain" means no brand recorded |
| `music_venues_nearby` | Music venues within a 15-minute walk | Place | `overture-places`. The GLA music layers are held | Point | After the Overture quality spike | Grassroots venues cannot be told from others. A pub with a band is not reliably marked |
| `library_proximity` | Walk to the nearest public library | Place | See `community.md` | Point | After the gate | Proposed there. Not repeated here |
| `market_proximity` | Walk to the nearest regular market | Place | None | | Not yet | No source |
| Visits to a national museum | A fact on the area page | Place | DCMS monthly visits | Site | After the gate | About 15 institutions. Not a score |
| In a World Heritage Site | A fact on the area page | Place | Planning Data platform | Polygon | Now, once registered | A handful of sites |

A zero is not always unknown. A complete register gives a true zero: if the accredited list covers England, "no accredited museum within a 20-minute walk" is a fact. A zero from Overture is a gap until the quality spike says otherwise. Each feature must say which kind it is.

### Tags

First formulas, untested. Each must pass the 40-neighbourhood sanity set before it ships.

| Proposed `tag_id` | Label | Formula | Note |
|---|---|---|---|
| `culture_nearby` | Culture on the doorstep | 0.50 `culture_kinds_nearby` high + 0.30 `culture_venues` high + 0.20 `library_proximity` low | Variety first, then volume |
| `culture_in_reach` | Culture within reach | 0.60 `culture_reach_pt` high + 0.40 `culture_recognised_nearby` high | For people who will travel for it. Most of outer London lives this way |
| `creative`, as now | Creative | Unchanged | It counts venues and independents. It should gain the GLA studio and workspace layers once cleared |

Recognition carries less than 60 hundredths of any tag, as conservation areas do today. With the coverage rule, recognition can then never decide a tag alone.

### Experience

The founder asked for the character of a place to be the main thing on screen. For culture that means four changes.

| Where | What changes | Example, with made-up values |
|---|---|---|
| Reading the prompt | "Good theatres", "best museums", "highly rated" are read as a wish for recognised venues, and an assumption chip says so | Chip: "Burro holds no ratings. 'Highly rated' was read as 'recognised by a public body'. Tap to change" |
| Result card | Culture can be a reason, in the template's words | "Kinds of cultural venue within a 15-minute walk: 5, more than 62% of the 450 areas compared in this release" |
| Area page | A "Culture" section. One line per kind, then recognised venues, then what Burro does not know | "Theatres: 2. Cinemas: 1. Museums and public galleries: 3. Source and date on each line" |
| Area page, fixed line | Always shown | "Burro counts venues and says who has recognised them. It does not rate them, and it does not know what is on" |
| Compare | Rows for kinds, reach and recognised venues, ordered by the person's weights | |
| Methods page | Who decides each recognition, and what it does not mean | "Accreditation is a standard for how a museum is run" |

Naming a venue is what makes this section feel like a place. It is a founder decision, below.

### Order of work

| Step | What | Waits on |
|---|---|---|
| 1 | Founder opens the Arts Council pages and saves them | Nothing |
| 2 | Add one question for the GLA, on the Theatres Trust | Nothing |
| 3 | Overture quality spike, with culture categories in it | Already planned, phase 0b |
| 4 | `culture_kinds_nearby` and `culture_listed_buildings` | Step 3, and a real release |
| 5 | `culture_reach_pt` | Real travel times |
| 6 | `culture_recognised_nearby` | Step 1 |
| 7 | Proxy audit row for every feature here | The audit's written rule |

## What cannot be done honestly

| Claim | Why not |
|---|---|
| A rating or review score for a venue | No lawful source. Google Places is banned. The sites read today forbid it |
| "The best theatre in {area}" | Burro ranks areas, never venues |
| What is on, or how much is on | No open source holds programmes. The GLA map defines a theatre as a building with 30 public performances a year. That is a threshold, not a count |
| How big a venue is | Capacity is in Wikidata for one theatre in five. The Theatres Trust database held it and is offline and not licensed for commercial use |
| Opening hours, ticket prices, free entry | No open source |
| Awards as a score | 14 of 2,061 Wikidata items record one. The awarding bodies' sites forbid building a database from them |
| Page views as quality | They measure fame among readers of English Wikipedia |
| Festivals by neighbourhood | No dataset found. A festival is an event, not a place, and many happen once |
| Markets | No London-wide open list found. Two boroughs publish their own |
| The grassroots or underground scene | By its nature it is not on a register |
| Who goes to the theatre, or how many residents visit museums | The Participation Survey asks residents, and is published by borough. It describes residents and stops at the borough |
| "Cultural background" of an area read off its venues | A venue serves whoever comes. Counting a community's venues to say who lives nearby is describing residents by proxy |
| That a venue is still open | Every list ages. The GLA map was captured in 2022. Wikidata keeps closed venues |
| A listing grade as a sign of a good night out | It is about the building |
| Any borough figure as a neighbourhood's | London Borough of Culture, Arts Council priority places and survey figures are all by borough |

## What the founder must decide

Work should proceed on the recommendation unless the founder says otherwise. Decisions 4 and 5 touch ADR 0006 and are the founder's alone.

### 1. What "highly ranked" means in Burro

| Choice | What it allows | What it risks |
|---|---|---|
| A. Drop it. Count venues only | Nothing new | The founder's item 4 is unmet |
| B. "Recognised": on a named public list, with the scheme always shown | A true sentence with a source and a date | Recognition is not quality. It favours old, large and central institutions |
| C. B, plus "well known" from page views and language editions | More venues get a signal | It measures fame and tourism. It would rank a waxworks above a concert hall |
| D. License a ratings source | Real ratings | None found that allows it. Any would cost money and bring display rules |

Recommendation: B. Hold C for prototyping. Do not pursue D.

### 2. May venues be named on area pages?

| Choice | What it allows | What it risks |
|---|---|---|
| A. As now: aggregates only | Nothing new | Culture stays a number. The page never says what is there |
| B. Name public institutions from sources registered for `display`: accredited museums, national museums, listed buildings, libraries | "The {museum} is a 12-minute walk" | A closed venue named as open. Each source needs `display` added, with evidence. The verifier finds names by their capitals only |
| C. Name any venue from Overture | Far more names | Overture's Foursquare records bring a notice duty onto the display. Some records are sole traders. Quality is unmeasured |

Recommendation: B, after the verifier is extended. Not C in v1.

### 3. Recognition and fairness

Recognition is a place fact. It still follows wealth and history, and may follow who lives nearby.

| Choice | What it allows | What it risks |
|---|---|---|
| A. Show it, never rank on it | A fact on the page | None to ranking |
| B. Rank on it, capped below 60 hundredths of any tag, always beside the plain count | "Culture within reach" | A proxy effect. Needs an audit row: aim, threshold, action |
| C. Rank on it with no cap | A stronger tag | Outer and newer areas are called empty |

Recommendation: B, with the audit row written first.

### 4. Venues that serve one community

The GLA publishes a layer of LGBTQ+ night-time venues. The registry holds it, pending "a fairness decision under ADR 0006". Arts centres and cinemas that serve one diaspora raise the same question. ADR 0006 says a wish for community "is met through amenities: places of worship, specialist shops, venues". Today it is not met.

| Choice | What it allows | What it risks |
|---|---|---|
| A. Leave out | Nothing | ADR 0006's promise stays unmet |
| B. Count them as venues of their kind, with no label | They add to the culture count like any venue | Low |
| C. On an explicit request only. Near, never far. Never in a tag. Never shown unprompted | Answers "near LGBTQ+ venues" | A map of venues can be read as a map of people. The licence is not cleared. Needs an audit row |
| D. Show on every page as "cultural background" | The founder's item 8, in part | It describes residents by proxy. It is what ADR 0006 exists to prevent |

Recommendation: B now. C in principle, once the GLA clears the layer and the audit row exists. Not D. `community.md` reaches the same answer for places of worship.

### 5. "Cultural background and vibe" (the founder's item 8), as far as culture data goes

| Choice | What it allows | What it risks |
|---|---|---|
| A. Places only: venues, institutions, buildings, markets | Everything proposed here | Some of what the founder means by "background" is left unsaid |
| B. A, plus the attributed Wikipedia excerpt already approved for profiles | A human account of the area's history, in Wikipedia's words, never Burro's | The excerpt may describe residents. It is shown verbatim, marked, and never fed to a prompt or a score |
| C. Census tables of ethnicity or country of birth on the page | The literal request | ADR 0006 and section 15 of the plan both rule it out. No lawyer has read the position. `people.md` sets it out in full |

Recommendation: B. This report does not decide C.

### 6. to 10.

| # | Decision | Recommendation |
|---|---|---|
| 6 | Write to Arts Council England about the licence for its three lists? | Yes, if the pages, once opened, do not settle it. One question covers the National Portfolio, accredited museums and libraries |
| 7 | Ask the GLA about the Theatres Trust too? | Yes. The 2019 theatre layer names the Trust, and the Trust's own terms forbid commercial use without a licence |
| 8 | Ask an awarding body for permission to list winners? | No. Too few winners to matter, and each is a separate question |
| 9 | Is `culture_listed_buildings` culture or heritage? | Heritage. Label it as built heritage, and let it feed `historic_character`, not a culture tag |
| 10 | Should "fewer visitors" be a wish a person can make? | Not in v1. Visits are known for about 15 museums only |

### Pages only the founder can open

| Page | What to save | Unblocks |
|---|---|---|
| Arts Council England, terms and conditions | The wording on reuse and commercial use | All three Arts Council lists |
| Arts Council England, 2023-26 investment programme data | The licence line, the period, and the column list | `culture_recognised_nearby` |
| Arts Council England, accreditation statistics and list | The licence line, the list date, and the column list | `museum_accredited_nearby` |
| Mapping Museums, the newer web application | The licence and its version. Where the accreditation field comes from | The fallback for accredited museums |
| Music Venue Trust, terms | The wording on reuse | Whether a question is worth asking |

## What this research turned up about entries already in the registry

| Entry | Finding | Suggested action |
|---|---|---|
| `gla-cultural-infrastructure-map-2019` | The page lists the theatre layer as "GLA and Theatres Trust", cinemas as "GLA with Independent Cinema Office", and arts centres as "GLA with Future Arts Centres and National Archives". The registry marked the last two as needing re-reading. They were read again, through the same kind of tool | Still to be read by eye |
| `gla-cultural-infrastructure-map-2023-gla-commissioned-layers` | The Theatres Trust's terms, last updated March 2025, say: "You must not use any part of the materials on our site for commercial purposes without obtaining a licence to do so from us or our licensors." If the 2023 theatre layer descends from the Trust's data, OGL cannot cover it | Name the Trust in the question for the GLA |
| The same entry | The theatre file's description gives the test as 30 public performances a year | Use that wording in the label |
| `gla-cultural-infrastructure-map-2023-libraries` | The 2016 DCMS libraries dataset shows "UK Open Government Licence (OGL)" on data.gov.uk. GOV.UK says the Arts Council now maintains the list. A 2023 layer is more likely built on the Arts Council's edition, which was not read | Not yet released |
| `gla-cultural-infrastructure-map-2025` | The page lists one workbook, a zones file and a data note. Still no licence | No change |
| `overture-places` | The guide says the record holds no rating, review count, popularity or capacity, and that confidence "measures existence only". It says the old `categories` property is removed in September 2026 | Overture cannot supply standing. Build on `basic_category` and `taxonomy`, as the entry already says |
| `historic-england-listed-buildings` | A record holds name, grade, reference, link, date and point. It has no field for kind of building | Any "listed theatre" figure is a name match. Say so on the methods page |
| `wikidata-places-and-landmarks` | Its uses are `gazetteer` and `destination_search`. Its conditions list the properties that may be read. Capacity, heritage status and awards are not among them | A second entry is proposed below. The other way is to widen this one |
| London Datastore | The old search address now returns "Legacy search links have been removed due to crawler abuse" and points to the sitemap | Find datasets by the sitemap |

## What was not read

| What | Standing | Relied on instead |
|---|---|---|
| Web search | None was made | Known addresses only |
| Arts Council England: terms, National Portfolio data, accreditation list | Not read | Nothing. No claim is made about its licence |
| Arts Council England in the UK Government Web Archive | 125 captures of the terms page, 2009 to 2022. None was read | Nothing |
| Historic England's own site | Not read | The Planning Data platform, as the registry does |
| Theatres Trust database | Not read. The Trust's page says it is offline | The Trust's terms page and its "Discover theatres" page |
| Internet Archive | Not read | Nothing |
| Music Venue Trust | Not read | Nothing |
| VisitBritain, first terms address | Not read | A second address, which was read |
| London Datastore search | Not used | The sitemap, which may not have been read to its end |
| GLA pages on markets | Not read | Nothing |
| Mapping Museums, newer application | Not read | The older site's copyright page |
| Wikimedia API documentation, first two addresses | Not read | The access policy and page view pages, which were read |
| Any data file | None was opened, on purpose | Page descriptions |

## Unverified

- Everything about Arts Council England's licence, the fields in its lists, the funding period and the number of organisations.
- That the accredited museums list or the National Portfolio file holds an address for the venue. If not, neither can be placed on a map without a second source.
- That the GOV.UK footer licence covers the museum visits spreadsheet. It is the footer, not a statement about the file.
- Which museums DCMS sponsors, and which sites are in London. The page read did not list them.
- How many World Heritage Sites are in London. From memory, four. Not checked.
- The fields in Mapping Museums. From memory it holds accreditation, size, governance, subject and postcode. The page read did not list them.
- Every quotation. Each passed through a reader that summarises.
- The Wikidata counts. They depend on how contributors filled in "located in". No item was looked at.
- The page view totals. Summed by the tool, and one was 20 out.
- Whether a list of award winners is protected by database right. Regulation 13 of the 1997 Regulations gives the right where there has been "a substantial investment in obtaining, verifying or presenting the contents". Regulation 16 says taking "all or a substantial part" infringes, and that "repeated and systematic" taking of small parts may count. Whether that reaches a list of winners is a legal question. ADR 0007 says to design it out, and this report does.
- That the last Arts Council funding round moved money out of London. From memory.

## Proposed registry entries

For review. Not added to the registry. Two are `approved`: the licence page was read today and plainly allows commercial use, and the registry already approves the same publisher's data on the same evidence. Both were read through a reader that summarises, so each carries a `before_launch` item. `verified_on` is the day the page was fetched.

```toml
# Proposed by docs/research/vibes/culture.md on 2026-09-23.
# Goes in registry/sources/culture.toml unless the entry says otherwise.
# Libraries are proposed in docs/research/vibes/community.md and are not repeated here.

[[source]]
id = "wikidata-cultural-venues"
name = "Wikidata structured data (cultural venues in Greater London)"
publisher = "Wikimedia Foundation (Wikidata contributors)"
url = "https://www.wikidata.org/wiki/Wikidata:Data_access"
dimension = "culture"
licence = "CC0-1.0"
licence_url = "https://creativecommons.org/publicdomain/zero/1.0/"
commercial_use = "yes"
share_alike = false
conditions = [
    "Main namespace only: kind, coordinates, heritage designation, capacity, closing date, identifiers and sitelinks. Text in other namespaces is CC BY-SA 4.0 and is not covered.",
    "Never the only evidence that a venue exists or is open. Wikidata keeps closed venues: 181 of 2,061 London items carried a closing date on 2026-09-23, and others will have closed with none entered.",
    "Drop every item with a closing date at ingest.",
    "Capacity and awards are too thin to score: about one theatre in five has a capacity, and 14 items of 2,061 record an award.",
    "Select items by Wikidata query only. Never use the wikidata tags on OpenStreetMap objects to pick or match records.",
    "Store the QID and retrieval date for every record.",
    "Send a User-Agent that names the project and a contact, as the Wikimedia User-Agent policy asks. Use a dump when the result set is large.",
]
status = "approved"
before_launch = [
    "Measure coverage by kind against an approved venue list, in aggregate.",
    "Read the licensing page by eye and save a dated copy.",
]
uses = ["scoring", "display"]
cadence = "Continuous. Snapshot per data release."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.wikidata.org/wiki/Wikidata:Licensing",
    "https://www.wikidata.org/wiki/Wikidata:Data_access",
]
notes = "Same dataset and licence as wikidata-places-and-landmarks, with a different selection and different conditions. The other way is to widen that entry's uses and conditions. Wikidata:Licensing was read as 'All structured data in the main, property and lexeme namespaces is made available under the Creative Commons CC0 License'. CC0 is a waiver by contributors; it cannot clear rights in a fact copied from a restricted source. Read through a reader that summarises."

[[source]]
id = "arts-council-england-national-portfolio"
name = "National Portfolio: investment programme data"
publisher = "Arts Council England"
url = "https://www.artscouncil.org.uk/how-we-invest-public-money/2023-26-Investment-Programme/2023-26-investment-programme-data"
dimension = "culture"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
conditions = [
    "Nothing may be downloaded until the licence has been read and saved.",
    "If released: count an organisation only where the file gives the address of a venue the public can visit. An office is not a venue, and a touring company has none.",
    "Say 'funded by Arts Council England' and give the period. Never say 'best' or 'top', and never suggest the Arts Council endorses Burro or an area.",
    "Never shown without the plain venue count beside it.",
]
status = "gated"
status_reason = "Neither the licence nor the file was read. Gate: (1) open the terms page and the data page in a browser and save both; (2) set the licence, commercial_use and attribution from what they say; (3) confirm the file holds a venue address; (4) if the pages are silent on reuse, ask the Arts Council in writing."
uses = ["scoring"]
cadence = "Per funding round. The period was not read."
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.artscouncil.org.uk/terms-and-conditions",
]
notes = "The address is the one the page was expected at. Nobody has opened it. GrantNav lists Arts Council England as a registered charity, number 1036733. No page read today says it publishes under the Open Government Licence, so that licence cannot be assumed."

[[source]]
id = "arts-council-england-accredited-museums"
name = "UK Museum Accreditation Scheme: list of accredited museums"
publisher = "Arts Council England"
url = "https://www.artscouncil.org.uk/supporting-arts-museums-and-libraries/uk-museum-accreditation-scheme/accreditation-statistics-and-list-accredited-museums"
dimension = "culture"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
conditions = [
    "Nothing may be downloaded until the licence has been read and saved.",
    "If released: say 'accredited museum' and give the list's date. Accreditation is a standard for how a museum is run. It is not a rating.",
    "Count museums with full or provisional accreditation apart, if the list tells them apart.",
]
status = "gated"
status_reason = "Neither the licence nor the file was read. Gate: as for arts-council-england-national-portfolio, and confirm the list holds an address for each museum."
uses = ["scoring", "display"]
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.artscouncil.org.uk/terms-and-conditions",
]
notes = "The address is the one the page was expected at. Nobody has opened it."

[[source]]
id = "birkbeck-mapping-museums"
name = "Mapping Museums database"
publisher = "Birkbeck, University of London (Mapping Museums project)"
url = "https://museweb.dcs.bbk.ac.uk/data"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://museweb.dcs.bbk.ac.uk/copyright"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Data downloaded from the Mapping Museums website at www.mappingmuseums.org, Accessed on [date]."
attribution_verified = false
conditions = [
    "The page says 'Creative Commons (BY)' and gives no version. Until the version is confirmed, treat the publisher's own sentence as the terms: 'copy, distribute, remix and build upon the research, so long the Mapping Museums team is credited'.",
    "The accreditation field comes from another body. The page names no third-party source and no terms for one.",
    "The site's source code is under the GNU General Public License. That covers the software, not the data.",
    "The older site says this version is no longer maintained. Use the date of the data, not the date of download.",
]
status = "gated"
status_reason = "The licence is stated without a version, and the source of the accreditation and size fields is not named. Gate: (1) read the copyright page and the newer application by eye and save both; (2) confirm the Creative Commons version; (3) ask the project where the accreditation field comes from, if the pages do not say. If the Arts Council list clears first, this entry moves to held."
uses = ["scoring"]
cadence = "Last update 1 February 2026, per the older site. Downloadable files dated 30 September 2021."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://museweb.dcs.bbk.ac.uk/copyright",
    "https://museweb.dcs.bbk.ac.uk/data",
    "https://museweb.dcs.bbk.ac.uk/home",
]
notes = "A fallback for accredited museums. Read through a reader that summarises. The newer application was not read."

[[source]]
id = "dcms-sponsored-museums-monthly-visits"
name = "Museums and galleries monthly visits"
publisher = "Department for Culture, Media and Sport"
url = "https://www.gov.uk/government/statistical-data-sets/museums-and-galleries-monthly-visits"
dimension = "culture"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Covers the museums DCMS sponsors, and no others. It is a fact about a site, not a measure of an area.",
    "State the year and 'DCMS' wherever a figure is shown.",
    "Never turn visits into a rank of museums.",
    "Do not suggest DCMS endorses Burro.",
]
status = "gated"
status_reason = "The page shows the OGL v3.0 footer, which is a statement about the page and not about the file. Gate: (1) open the spreadsheet and save its notes sheet; (2) confirm figures are given by site; (3) save a dated copy of the page."
uses = ["display"]
cadence = "Monthly figures, published quarterly. Latest seen: April to June 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/statistical-data-sets/museums-and-galleries-monthly-visits",
    "https://www.gov.uk/government/statistics/dcms-sponsored-museums-and-galleries-annual-performance-indicators-202425",
]
notes = "Read through a reader that summarises. No file was opened."

[[source]]
id = "wikimedia-pageviews"
name = "Wikimedia page views, per article"
publisher = "Wikimedia Foundation"
url = "https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/"
dimension = "culture"
licence = "CC0-1.0"
licence_url = "https://creativecommons.org/publicdomain/zero/1.0/"
commercial_use = "yes"
share_alike = false
conditions = [
    "Never an input to ranking or a tag. Reads of an article measure fame among readers of one language, anywhere in the world.",
    "Never shown as a sign of quality.",
    "Send a User-Agent that names the project and a contact.",
]
status = "held"
status_reason = "The licence is clear and the signal is not fair. On 2026-09-23 a visitor attraction's article had about fourteen times the reads of a chamber music hall's. Held for prototyping, so that anyone who proposes it later can see the skew for themselves."
uses = ["prototyping_only"]
cadence = "Daily."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html",
    "https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html",
    "https://dumps.wikimedia.org/legal.html",
    "https://meta.wikimedia.org/wiki/Research:Page_view",
]
notes = "The access policy was read as 'Data provided by the API is available under the CC0 1.0 license'. The dumps page was read as 'All Analytics datasets are available under the Creative Commons Zero (CC0) public domain dedication'."

[[source]]
id = "theatres-trust-theatres-database"
name = "Theatres Database and Theatres at Risk register"
publisher = "Theatres Trust"
url = "https://www.theatrestrust.org.uk/discover-theatres"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://www.theatrestrust.org.uk/terms-conditions"
commercial_use = "no"
share_alike = false
conditions = [
    "The terms allow one printed copy and extracts 'for your personal reference'.",
    "The terms say: 'You must not use any part of the materials on our site for commercial purposes without obtaining a licence to do so from us or our licensors.'",
    "Do not compile a list by hand from the site.",
]
status = "held"
status_reason = "Commercial use needs a licence from the Trust, and the database is offline: the Trust's page says it was taken offline 'following a review of the resource and its content'. Released only by a written licence from the Trust."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.theatrestrust.org.uk/terms-conditions",
    "https://www.theatrestrust.org.uk/discover-theatres",
    "https://www.theatrestrust.org.uk/how-we-help/theatres-at-risk",
]
notes = "Terms last updated March 2025, as read. The 2019 Cultural Infrastructure Map names the Trust as a source of its theatre layer. Read through a reader that summarises."

[[source]]
id = "alva-visitor-figures"
name = "Visits made to visitor attractions in membership with ALVA"
publisher = "Association of Leading Visitor Attractions"
url = "https://www.alva.org.uk/details.cfm?p=423"
dimension = "culture"
licence = "None-stated"
commercial_use = "unknown"
share_alike = false
conditions = [
    "The page carries '© 2026 Cybertrek Ltd, ALVA' and no reuse statement.",
]
status = "held"
status_reason = "No licence is stated. It covers members only, so it cannot rank London. Released only by written permission."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.alva.org.uk/details.cfm?p=423"]

[[source]]
id = "visitbritain-visitor-attractions-survey"
name = "Annual Survey of Visits to Visitor Attractions"
publisher = "VisitBritain and VisitEngland (British Tourist Authority)"
url = "https://www.visitbritain.org/research-insights/england-visitor-attractions-latest"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://www.visitbritain.org/terms-use"
commercial_use = "no"
share_alike = false
conditions = [
    "The site terms say use is 'for information and/or personal, non-commercial use only' and that no part may be 'reproduced or stored in any other website without our prior written consent'.",
]
status = "held"
status_reason = "The site terms forbid commercial reuse. The survey page states no licence of its own. Released only by written consent."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.visitbritain.org/terms-use",
    "https://www.visitbritain.org/research-insights/england-visitor-attractions-latest",
]

[[source]]
id = "art-fund-museum-of-the-year"
name = "Art Fund Museum of the Year: winners and shortlists, as published on the Art Fund site"
publisher = "Art Fund"
url = "https://www.artfund.org/terms-and-conditions/use-of-this-website-and-mobile-applications"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://www.artfund.org/terms-and-conditions/use-of-this-website-and-mobile-applications"
commercial_use = "no"
share_alike = false
conditions = [
    "The terms forbid 'Copying or distribution of material on the Website or in the Apps for any commercial or business purpose'.",
    "The terms forbid a user to 'create a database (electronic or otherwise) that includes material downloaded or otherwise obtained from the Website'.",
]
status = "held"
status_reason = "The site's terms forbid every step Burro would take. A few winners a year cannot rank 450 areas. Released only by written permission, which is not worth asking for."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.artfund.org/terms-and-conditions/use-of-this-website-and-mobile-applications",
]
notes = "Terms dated 14 May 2012, as read. Read through a reader that summarises."

[[source]]
id = "solt-olivier-awards"
name = "Olivier Awards: winners, as published on Official London Theatre"
publisher = "Society of London Theatre"
url = "https://officiallondontheatre.com/terms/"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://officiallondontheatre.com/terms/"
commercial_use = "no"
share_alike = false
conditions = [
    "The terms say material 'may only be used for your personal and non-commercial purposes'.",
    "The terms forbid a user to 'use software to harvest information from the Site'.",
    "The awards go to productions and people, not to venues or areas.",
]
status = "held"
status_reason = "The site's terms forbid commercial reuse and harvesting, and the awards do not describe a place."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://officiallondontheatre.com/terms/"]
notes = "Terms dated 13 September 2017, as read. Read through a reader that summarises."

[[source]]
id = "the-stage-awards"
name = "The Stage Awards: winners, as published on The Stage"
publisher = "The Stage"
url = "https://www.thestage.co.uk/terms-and-conditions"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://www.thestage.co.uk/terms-and-conditions"
commercial_use = "no"
share_alike = false
conditions = [
    "The terms allow extracts 'for your own personal and non-commercial use only'.",
    "The terms forbid downloading 'in a systematic or regular manner or otherwise so as to create a database'.",
]
status = "held"
status_reason = "The site's terms forbid commercial reuse and building a database. A few winners a year cannot rank 450 areas."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.thestage.co.uk/terms-and-conditions"]
notes = "The publisher is given by the site's name; its legal name was not read. Read through a reader that summarises."

[[source]]
id = "time-out-listings"
name = "Time Out listings, reviews and ranked lists"
publisher = "Time Out"
url = "https://www.timeout.com/terms-of-use"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://www.timeout.com/terms-of-use"
commercial_use = "no"
share_alike = false
status = "banned"
status_reason = "The terms allow viewing and printing 'for your personal and non-commercial use only'. They say Time Out 'does not permit the use of the Content on any artificial intelligence (AI) or machine learning platform, tool, software or system in any way' without written approval. The content is opinion, which Burro may not present as fact."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.timeout.com/terms-of-use"]
notes = "Terms last updated October 2024, as read. The publisher is given by the site's name; its legal name was not read. Read through a reader that summarises."

[[source]]
id = "cinema-treasures"
name = "Cinema Treasures"
publisher = "Cinema Treasures"
url = "https://cinematreasures.org/terms"
dimension = "culture"
licence = "Bespoke-terms"
licence_url = "https://cinematreasures.org/terms"
commercial_use = "no"
share_alike = false
status = "banned"
status_reason = "The terms allow personal use only and say a user may not 'use any automated means to use the site or collect information from it (including without limitation the use of bots, spiders or scripts)'."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://cinematreasures.org/terms"]
notes = "Terms last modified 11 February 2002, as read. The publisher is given by the site's name; its legal name was not read. Read through a reader that summarises."

# For registry/sources/heritage.toml

[[source]]
id = "historic-england-world-heritage-sites"
name = "World heritage sites"
publisher = "Historic England (copy published on the MHCLG Planning Data platform)"
url = "https://www.planning.data.gov.uk/dataset/world-heritage-site"
dimension = "heritage"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "© Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026."
attribution_verified = false
conditions = [
    "Approval covers only the copy on planning.data.gov.uk, which states the licence and attribution.",
    "A fact on an area page, or one term of a heritage tag. Most areas have none, so it must never decide a tag alone.",
    "Say 'inside the World Heritage Site' only of the inscribed boundary. The buffer zone is a separate dataset and is not covered.",
    "Update the year in the statement to match the data used.",
    "Do not suggest that Historic England or UNESCO endorses Burro or an area.",
]
status = "approved"
before_launch = [
    "Read the dataset page by eye, save a dated copy, and confirm the attribution wording.",
    "Count the London sites and check each boundary against the publisher's map.",
]
uses = ["scoring", "display"]
cadence = "Collector runs daily."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.planning.data.gov.uk/dataset/world-heritage-site",
    "https://www.planning.data.gov.uk/dataset/",
]
notes = "40 records for England. The page was read as 'Licensed under the Open Government Licence v.3.0', with the same attribution statement as the listed building dataset the registry already approves. Read through a reader that summarises."

# For registry/sources/audit.toml

[[source]]
id = "dcms-participation-survey"
name = "Participation Survey"
publisher = "Department for Culture, Media and Sport, with Arts Council England"
url = "https://www.gov.uk/government/statistics/participation-survey-2023-24-annual-publication"
dimension = "audit"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "It describes residents: whether adults aged 16 and over took part in the arts, museums, libraries and heritage. It must never feed ranking or a tag.",
    "Published for England, regions and local authorities. Nothing smaller. A borough figure must never be shown as a neighbourhood's.",
]
status = "held"
status_reason = "It describes residents and stops at the borough. Useful only to check, offline, whether a culture feature tracks who takes part."
uses = ["audit_only"]
cadence = "Yearly."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/statistics/participation-survey-2023-24-annual-publication",
]
notes = "The licence is the GOV.UK footer, not a statement about the file. Read through a reader that summarises."
```

## Sources read

| Page | Address |
|---|---|
| Wikidata: licensing | https://www.wikidata.org/wiki/Wikidata:Licensing |
| Wikidata: data access | https://www.wikidata.org/wiki/Wikidata:Data_access |
| Wikidata: maximum capacity | https://www.wikidata.org/wiki/Property:P1083 |
| Wikidata Query Service | https://query.wikidata.org/ |
| Wikimedia analytics API: access policy | https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html |
| Wikimedia analytics API: page views | https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html |
| Wikimedia dumps: legal | https://dumps.wikimedia.org/legal.html |
| Research: page view | https://meta.wikimedia.org/wiki/Research:Page_view |
| Wikimedia User-Agent policy | https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy |
| Planning data: datasets | https://www.planning.data.gov.uk/dataset/ |
| Planning data: listed building | https://www.planning.data.gov.uk/dataset/listed-building |
| Planning data: world heritage site | https://www.planning.data.gov.uk/dataset/world-heritage-site |
| Planning data: heritage at risk | https://www.planning.data.gov.uk/dataset/heritage-at-risk |
| Planning data: asset of community value | https://www.planning.data.gov.uk/dataset/asset-of-community-value |
| Cultural Infrastructure Map 2023 | https://data.london.gov.uk/dataset/cultural-infrastructure-map-2023 |
| Cultural Infrastructure Map 2019 | https://data.london.gov.uk/dataset/cultural-infrastructure-map |
| Cultural Infrastructure Map 2025 | https://data.london.gov.uk/dataset/cultural-infrastructure-map-2025-2rj5o |
| Creative Enterprise Zones data repository | https://data.london.gov.uk/dataset/creative-enterprise-zones-cez-data-repository-e66pp |
| London Datastore sitemap | https://data.london.gov.uk/sitemap.xml |
| Museums and galleries monthly visits | https://www.gov.uk/government/statistical-data-sets/museums-and-galleries-monthly-visits |
| DCMS-sponsored museums, annual indicators 2024/25 | https://www.gov.uk/government/statistics/dcms-sponsored-museums-and-galleries-annual-performance-indicators-202425 |
| Participation Survey 2023/24 | https://www.gov.uk/government/statistics/participation-survey-2023-24-annual-publication |
| Public libraries basic dataset | https://www.gov.uk/government/publications/public-libraries-in-england-basic-dataset |
| Public libraries basic dataset, data.gov.uk record | https://www.data.gov.uk/dataset/782d6528-11bd-4ae0-ae47-63b456c84e76/public-libraries-in-england-basic-dataset |
| Open Government Licence v3.0 | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
| Database regulations, regulation 13 | https://www.legislation.gov.uk/uksi/1997/3032/regulation/13 |
| Database regulations, regulation 16 | https://www.legislation.gov.uk/uksi/1997/3032/regulation/16 |
| Mapping Museums: data | https://museweb.dcs.bbk.ac.uk/data |
| Mapping Museums: copyright | https://museweb.dcs.bbk.ac.uk/copyright |
| 360Giving registry | https://registry.threesixtygiving.org/ |
| GrantNav: Arts Council England | https://grantnav.threesixtygiving.org/org/GB-CHC-1036733 |
| Overture Places guide | https://docs.overturemaps.org/guides/places/ |
| Theatres Trust: terms | https://www.theatrestrust.org.uk/terms-conditions |
| Theatres Trust: discover theatres | https://www.theatrestrust.org.uk/discover-theatres |
| Theatres Trust: theatres at risk | https://www.theatrestrust.org.uk/how-we-help/theatres-at-risk |
| ALVA visitor figures | https://www.alva.org.uk/details.cfm?p=423 |
| VisitBritain: attractions survey | https://www.visitbritain.org/research-insights/england-visitor-attractions-latest |
| VisitBritain: terms | https://www.visitbritain.org/terms-use |
| Art Fund: website terms | https://www.artfund.org/terms-and-conditions/use-of-this-website-and-mobile-applications |
| Official London Theatre: terms | https://officiallondontheatre.com/terms/ |
| The Stage: terms | https://www.thestage.co.uk/terms-and-conditions |
| Time Out: terms | https://www.timeout.com/terms-of-use |
| Cinema Treasures: terms | https://cinematreasures.org/terms |
