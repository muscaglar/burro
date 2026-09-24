# Vibes, designed from the data

Proposal, 2026-09-23. One of three, written without sight of the other two. It changes no code, no rule and no registry entry. Nothing here is legal advice, and no lawyer has read it.

It rests on the seven reports in [`docs/research/vibes/`](../research/vibes/). **No web page was opened for this document.** Every statement about a source or a licence is the report's, with the report's own limits: most pages were read through a reader that summarises, and almost no data file was opened. Every weight and threshold below is a first guess.

Written before the registry held the six entries that rest on a permission in writing, as the founder reports: parkrun's events, the two canopy layers of the Greater London Authority, and the three lists of Arts Council England. Where this document says that one of them is not registered, or that it waits on an answer, [the plan for real data](london-data.md) and the registry stand.

| | |
|---|---|
| In one line | A vibe is a published recipe over measured parts. It ships only after people who know London have said, without seeing the scores, which areas sit at each end, and the recipe agrees with them |
| What is new | Two-ended scales. A portrait on every area page. "More like this". A test each vibe must pass. A fixed line on what each vibe cannot see |
| What does not change | Ranking is a pure function of a spec and a release. No part of any vibe describes residents. Crime is in no recipe. Every figure has a source and a date |
| What the founder must decide | Items 2 and 8 of the list. Sections 2.5 and 2.6 set out the choices |

## 1. What a vibe is

A vibe is a named scale that says where a neighbourhood sits among all the others on one side of its character: how leafy, how buzzy, how gritty. It is worked out from a written recipe of three to six measured parts. Each part has a weight, a source and a date. It describes the place and never the people who live there. On screen it is a line with one or two named ends and a mark in one of five bands. Beside it is a sentence that is literally true, such as "further towards Gritty than 78% of the 450 areas compared". Under it are the parts that put the area there, and one line on what the vibe cannot see. A person can ask for either end of a two-ended scale. To an engineer it is today's tag with four more fields: a name for each end, a list of blind spots, the record of the test it passed, and a direction in the spec.

| Every vibe carries | Rule | Why |
|---|---|---|
| A recipe | Parts in whole hundredths that sum to 100. Three parts at least | A sceptic can work it out again |
| A cap on each part | No part above 50 hundredths. With the coverage rule of 60, no vibe can rest on one measurement | It is the rule conservation areas have today, made general |
| Ends | One name, or two. Two only where both ends are a taste in places | "Far from a community hall" is a request about people |
| Standing | A count of areas strictly beyond, rounded down, as contract 7.3 | It is true wherever areas tie |
| Coverage | Below 60 hundredths present, the area has no position | Missing data is never filled in |
| Blind spots | A fixed list, shown with the vibe everywhere | The reader learns what was not measured |
| A test passed | The result of section 3, printed on the methods page | "Validated" has to mean something |
| What it describes | A place, its buildings, or events in a place | A test refuses a part that describes residents |

A vibe is not a badge: no page says an area "is gritty". It is not a score of quality, not a composite liveability score (PLAN section 15), and not written by a model.

How this differs from a property portal, and from the website as built:

| A portal | The website today | With vibes |
|---|---|---|
| Starts from a listing, and the area is a filter on it | Starts from a search. Tags are switches in the settings | Starts from the character of places. The map can be painted by a vibe before anything is typed |
| Describes an area in an agent's words | Prints each feature as a row | Opens an area page with a portrait: where the place stands on each scale, and why |
| Gives no working | Shows weights and sources for features | Shows the recipe, the parts, the test the vibe passed, and what it cannot see |
| Has no way to say "like here, but nearer work" | Has none either | "More like this", inside the same search |

## 2. The vibes

Thirteen. Three have two ends. Ten have one. Today's twelve tags become six of them; section 5.1 says how. Fewer would be better still: section 3.2 merges any two that turn out to measure the same thing.

### 2.1 What each means

| # | Vibe | Ends | In plain words | Describes | Founder's item |
|---|---|---|---|---|---|
| 1 | Street character | Polished to Gritty | How hard-edged the built place is: works, depots, main roads and dense streets at one end, green and protected streets at the other | Place | 2 |
| 2 | Pace | Calm to Buzzy | How much there is to eat, drink and go out to within the area | Place | 1 |
| 3 | Age of the streets | Historic to Newer | How much of the area is old homes, listed buildings and protected streets | Buildings | 1 |
| 4 | Leafy | Leafy | Trees over streets and gardens, and public green space | Place | 5 |
| 5 | Parks close by | Parks close by | A park within a walk, a large one not far, and things to do in it | Place | 5 |
| 6 | Village feel | Village feel | A small centre of its own, old streets, independent places | Place | 1 |
| 7 | High street life | High street life | A high street within a walk, with places to eat and independents | Place | 1 |
| 8 | Culture on the doorstep | Culture on the doorstep | How many kinds of cultural venue are within a walk | Place | 4 |
| 9 | Places to train | Places to train | Gyms, pools, courts and pitches open to the public within a walk | Place | 3 |
| 10 | Places to meet | Places to meet | How many kinds of place to go back to, with the same people, are within a walk | Place | 6 |
| 11 | Family amenities | Family amenities | Primary schools, play space and parks within a walk | Place | 1 |
| 12 | Everyday on foot | Everyday on foot | A high street, a GP surgery, a pharmacy and a station within a walk | Place | 7 |
| 13 | Set up for home working | Set up for home working | Homes that can order a gigabit-capable line, low transport noise, a park nearby | Place | 7 |

### 2.2 What each is made of, and whether the data is ready

"Ready" is about licences and sources, not ingest: no real dataset has been ingested. **Now** means parts that carry 60 hundredths or more have a source the registry approves today, which is what the coverage rule needs. **New source** means a report read the licence and proposes an entry. **Waits** means an answer from an owner, or a page only the founder can open.

| # | Recipe, in hundredths. "low" reads a part from its low end | Ready | What would settle it |
|---|---|---|---|
| 1 | 35 `land_industrial` + 25 `road_major_exposure` + 15 `homes_density` + 15 `green_cover` low + 10 `conservation_cover` low | New source | Open the land use table (OGL v3 as read by `grit.md`): LSOA vintage, units, categories. Without it the scale is density and main roads, which is nearness to the centre. Do not ship it without |
| 2 | 35 `venue_evening` + 30 `venue_food_drink` + 20 `highstreet_access` + 15 `culture_venues` | Now | The Overture quality spike, for the culture part |
| 3 | 40 `homes_pre1919` + 30 `conservation_cover` + 30 `listed_buildings` | Now | A catalogue row for listed buildings. It also meets the registry's condition on conservation areas (contract 13) |
| 4 | First: today's 45 `green_cover` + 30 `park_proximity` low + 25 `homes_density` low. Then: 35 `canopy_cover` + 30 `street_canopy` + 20 `green_cover` + 15 `private_outdoor_space` | Now, then new source | Read the accuracy report of the open canopy map. Spike: does canopy reach the road edge on 20 streets called tree-lined. A question for the GLA about its 2024 canopy map, marked All Rights Reserved |
| 5 | 35 `park_proximity` low + 25 `park_large_proximity` low + 25 `park_facilities` + 15 `historic_park_proximity` low | Now | Catalogue rows. The registered parks entry is proposed by `green.md` |
| 6 | As today: 30 `venue_independent` + 20 `homes_pre1919` + 20 `conservation_cover` + 15 `highstreet_access` + 15 `park_proximity` low | Now | The sanity set |
| 7 | 40 `highstreet_access` + 30 `venue_food_drink` + 30 `venue_independent` | Now | The sanity set. `cuisine_variety` may join later, as a count of kinds and never a share |
| 8 | 45 `culture_kinds_nearby` + 30 `culture_venues` + 25 `library_proximity`. Later: recognised venues within reach, capped at 25 | Waits | The Overture spike. The Arts Council pages, which nobody has read. "Recognised" is shown as a fact before it is ever a part |
| 9 | 35 `gym_choice` + 25 `pool_proximity` low + 20 `court_pitch_kinds` + 20 `park_proximity` low | New source | Register Active Places (CC BY 4.0 as read by `fitness.md`). A question for Sport England, as a courtesy. Count London's gyms by kind |
| 10 | 40 `meeting_place_kinds` + 20 `library_proximity` low + 20 `sports_facility_nearby` + 10 `play_space_proximity` low + 10 `highstreet_access` | Waits | At least five kinds with London-wide data. Libraries: a page to open. parkrun: a written yes, and until then it stays out |
| 11 | As today: 30 `school_primary_nearby` + 25 `school_primary_attainment` + 25 `play_space_proximity` low + 20 `park_proximity` low | Now | The attainment source is gated. Nurseries join when the Ofsted file clears |
| 12 | 30 `highstreet_access` + 25 `gp_walk` low + 25 `pharmacy_walk` low + 20 `station_walk` low | New source | The pharmacy list clears its gate. `nhs-ods` gains the use `scoring` |
| 13 | 50 `broadband_gigabit` + 30 `noise_exposure` low + 20 `park_proximity` low | New source | The founder brings broadband into v1. Measure the spread across London first: if most areas sit within a few points, show the figure and do not build the vibe |

Two changes to what the research proposed, both from the rules:

| Change | Why |
|---|---|
| `noise_exposure` is taken out of Street character | `grit.md` sets the condition that nothing on a seekable scale is a nuisance, and its draft recipe holds noise. Noise is a nuisance in contract 3.1. A person who seeks the gritty end would rank noise up |
| "Quiet" becomes two edits: Pace towards Calm, and less `noise_exposure` | The same reason. Pace holds venues only. Noise keeps its one direction |

### 2.3 What each cannot see, and the words that call it up

| # | Cannot see | Five sentences a person might type |
|---|---|---|
| 1 | Litter, fly-tipping, graffiti, street art, empty shops, late licences, whether a place is run-down or improving, who lives there | "somewhere a bit gritty" / "an industrial, warehouse feel" / "railway arches and workshops" / "smart, polished streets" / "nothing too manicured" |
| 2 | Opening hours, how busy a place is, noise from venues or neighbours, whether venues are good | "buzzy, lots going on in the evening" / "bars and restaurants on the doorstep" / "lively" / "a sleepy residential area" / "quiet streets" |
| 3 | The state of a building, its inside, its style. An area the conservation source does not cover is unknown, not zero | "period houses" / "Victorian terraces" / "somewhere with history" / "old streets and listed buildings" / "a newer area with modern flats" |
| 4 | One street. Trees under 3 m. Planting since 2024. Species and blossom. Balconies and front gardens | "leafy" / "tree-lined streets" / "lots of greenery" / "green and full of trees" / "gardens and trees everywhere" |
| 5 | Upkeep, any award, crowding, opening hours | "near a big park" / "a park I can run in" / "tennis courts in the park" / "walk to a common" / "a park with a playground" |
| 6 | Whether neighbours know each other. Markets and events. "Independent" means no brand is recorded | "feels like a village" / "a little centre with its own shops" / "a green and a pub" / "a small-town feel" / "independent shops and old houses" |
| 7 | Empty shops, what the shops sell, prices, ratings, markets | "a proper high street" / "good places to eat nearby" / "independent cafes" / "foodie" / "everything on one street" |
| 8 | Any rating. What is on. Prices and hours. Whether a venue is still open. The grassroots scene | "theatres and galleries nearby" / "near a museum" / "a cinema within walking distance" / "live music" / "highly rated theatres" |
| 9 | Price, quality, how busy. Rooms under 5 stations. Climbing, boxing and martial arts | "a gym and a pool nearby" / "somewhere to swim" / "tennis courts close by" / "yoga studios" / "a cheap gym within a walk" |
| 10 | Whether a group is welcoming, has room, or still meets. How long people stay. Informal ties | "a community feel" / "things to join" / "easy to meet people" / "allotments and a library" / "a parkrun nearby" |
| 11 | Catchments, places free, what childcare costs | "good primary schools and playgrounds" / "somewhere for the kids to play" / "a school within a walk" / "nurseries nearby" / "a park and a playground" |
| 12 | Whether a surgery takes new patients, waits, opening hours, step-free access at every station | "a GP and a chemist nearby" / "I don't drive" / "walkable" / "everything within ten minutes on foot" / "shops and a doctor close by" |
| 13 | Full fibre, the speed a home gets, price, 5G for a neighbourhood, mobile signal indoors | "I work from home" / "fast broadband" / "fibre" / "good internet" / "5G" |

Three of these sentences are answered in part. "Highly rated theatres" is read as Culture on the doorstep, with a line that Burro holds no ratings. "A cheap gym" adds the filter of 2.4. "5G" and "a parkrun nearby" get the unmet line of 4.3.

### 2.4 Asked for, and not a vibe

| Asked for | What Burro does | Why |
|---|---|---|
| Crime inside "gritty" | Street incidents: recorded criminal damage and anti-social behaviour, shown beside Street character. Off until asked. Less only | Section 5.5 |
| Street cleanliness | Says it has no measure | No open data below borough level (`grit.md`) |
| Gym mix: boutique against value | Shown on the portrait as kinds: council leisure centre, chain gym, independent, class studio, gym with a pool. Never a part of a vibe | No lawful price or rating. The mix follows income (`fitness.md`) |
| A low-cost gym | A filter a person asks for. One direction. Off by default. Only for operators the founder names | The label is the operator's own quoted words |
| "Highly ranked" culture | "Recognised": the scheme and the date, as a fact on the portrait | No rating can be used (`culture.md`) |
| 5G | The unmet line and a link to the regulator's checker | Published for boroughs only (`connectivity.md`) |
| Friendly, close-knit | No edit | No dataset measures it. It is a claim about residents |
| Who lives there | Section 2.6 | Rule 8 |

### 2.5 Item 2: what may go into "gritty"

The founder's "gritty" has three parts. Crime can be measured. Street cleanliness cannot. Socioeconomic factors describe residents. The choices are `grit.md`'s.

| Choice | What goes in | Allows | Risks | Must change |
|---|---|---|---|---|
| A | Place only | A scale a person can seek at either end | It measures hard-edged, not run-down | Nothing |
| **B** | A, with street incidents beside it | Crime, and the nearest thing to cleanliness, with both seeker and avoider served | Two controls where one word was asked for | Nothing |
| C | Street incidents inside the scale | One word, one number | To seek "gritty" is to rank recorded crime up | ADR 0006, contract 3.1 and 3.2, PLAN 9 and 15 |
| D | Deprivation inside the scale | The everyday sense of the word | It ranks residents. Inputs include asylum support and disability benefits | Rule 8, ADR 0006, and paid legal advice |
| E | Deprivation shown, never ranked | A familiar official figure | It describes residents to a person choosing where to live | PLAN 15 |

I recommend **B**. This design builds B. It works unchanged under A. Under C the test that keeps crime out of recipes would have to be removed by the founder's decision, and I would first ask for the correlation check of section 3.3. I would not build D without the advice ADR 0006 names.

### 2.6 Item 8: who lives there

The data exists and the licence allows it (`people.md`). The question is what Burro does with it. The default, if nothing is decided, is ADR 0006 as written.

| | Option 1: places only | Option 2: show, never rank | Option 3: residents in ranking or vibes |
|---|---|---|---|
| Allows | Cuisines, venues, a place of worship named as a destination | All of 1, and the official 2021 figures on the area page | All of 2, and search by who lives there |
| Risks | Item 8 is met in part only | Wording. A figure 5 years 10 months old at launch. Unreviewed | Segregation, indirect discrimination, stereotype. Unreviewed. The searcher's own filter reveals their faith or origin |
| What I would build | A "Culture and community" block on the portrait, of places only. A link out to the statistics office's own pages. A community place findable as a destination | The same, and a census panel under the portrait: a table, closed by default for origin and belief, in the past tense, with no label and no colour | Nothing, until paid advice says a named input is safe |
| Where vibes stand | Unchanged | Unchanged. The panel is in no vibe, no "more like this", no comparison, no map, no sentence | I would still keep residents out of every named vibe. A filter would be its own control, on request, and would need rule 8, ADR 0006 and the neutral sentence rewritten first |
| Engine | No change | A release file of its own that `rank()`, recipes and `explain()` never open, and a test that proves it | Not designed here |

I recommend what `people.md` recommends: **Option 2 in two steps**, age, household type and students first, then country of birth, ethnic group and religion once a free legal clinic has read the panel or the founder accepts the leftover risk in writing. The vibe design is the same under Options 1 and 2, so it does not wait for the decision.

## 3. How a vibe is validated

A recipe is a claim, and a claim can be wrong. PLAN section 8 already says a tag ships only if it passes a sanity set of 40 neighbourhoods. This section says how that set is made and what passing means.

### 3.1 Would people who know the area agree?

| Step | What happens | Why |
|---|---|---|
| 1. A panel | Five people or more who know London: the founder, the second curator, and testers from different parts of the city | One person's London is half a city |
| 2. Lists before scores | For each vibe each person names up to ten areas at each end, from the list of neighbourhoods, without seeing any score. They are told to judge streets and buildings, not people | A list picked after the scores proves nothing |
| 3. Agreed areas | An area is agreed for an end when three of five name it there and nobody names it at the other end | Disagreement is data: it is left out |
| 4. Enough, and spread | Twelve agreed areas an end at least, in four inner and four outer boroughs at least | A test that only tells the centre from the suburbs is not a test |
| 5. Half held back | Half the agreed areas may be used to set the weights. The other half are used once, to pass or fail | Weights tuned on a list will always fit that list |
| 6. Committed | The lists are in the repository, dated, before the release is built. They hold area names and nothing about a person | The test can be run again by anyone |

### 3.2 What passing means

| Test | A vibe passes when | If it fails |
|---|---|---|
| Agreement | Four in five of the held-back areas sit in the right third of the ranking, and none in the opposite third | Change the recipe once and test on a fresh list, or drop the vibe |
| Its own thing | Its rank correlation with every other shipped vibe is below 0.8 | Merge the two |
| Not the centre by another name | It still separates the agreed areas within inner London alone, and within outer London alone | It is nearness to the centre. Drop it |
| Steady | Moving any one weight by 10 hundredths moves fewer than one area in ten to another fifth | The recipe is too fine for the data |
| Covered | 95 in 100 rankable areas have a position | Say where it cannot be measured, or wait |

A real release carries a vibe only if it passed on that release. The release records the counts, and the methods page prints them: "Street character: 13 of 14 agreed areas in the right third, none in the opposite third. Tested on release X." A vibe that has not passed is not shown as a trial. It is not shown. The synthetic release is the one exception: it shows every vibe, under the banner that says the data is made up.

### 3.3 The proxy audit, before it runs

ADR 0006 asks for a written rule first. For every part of every recipe: the aim it serves, the correlation that triggers a review, and what can be done. Two checks matter most here.

| Check | Against | Review at | Actions |
|---|---|---|---|
| Does seeking the gritty end rank crime up? | Street character against each recorded-crime rate, by neighbourhood | 0.5 | Re-weight, drop a part, or show the scale and do not let it be sought |
| Does a vibe stand in for who lives there? | Each vibe against the audit-only tables, offline | 0.5 | Drop a part, cap it, or make it on request only |

`grit.md` measured one thing that bears on the first check: across London's LSOAs one place-based indicator, lack of private outdoor space, moves with violence with injury at 0.40. None of the scale's own parts has been measured against crime. A correlation is likely, and its size is not known.

### 3.4 After launch

| Way | What it needs | Status |
|---|---|---|
| "Report a figure" link on each part | An address to write to | Build with the portrait |
| "Does this match what you know?" on a vibe: about right, too high, too low | A count for each area, vibe and answer. No text, no spec, no identity. From the area page only | **A founder decision.** It sends something new to the server and needs a store. Not in the first build |
| The sanity set, run on every release, with a report of what moved | Already in PLAN section 8 | Keep |

## 4. The experience

### 4.1 Moment by moment

| Moment | What is shown | What can be changed |
|---|---|---|
| Before a search | Under the prompt box, a shelf of the vibes in this release: each a small line with its end names. A control paints the map by one vibe, in five bands, from data the page already holds. Three example sentences use vibe words | Pick an end, which adds a chip and sends one edit and no text. Open a vibe to read its recipe, sources, test result and blind spots. Paint the map by another vibe |
| In the prompt | The box. Nothing is sent key by key. A "Words Burro knows" list opens from the box: end names and the wishes it cannot answer, from route 11 | Type, or pick a word from the list |
| What Burro understood | One chip a vibe, drawn as the scale with the end sought marked. "Assumed" where a loose word was read as a vibe, with fixed words: "Read as: places to meet nearby". The person's own words are underlined in the box from `rests_on` offsets, in the browser only. One line for each wish Burro cannot measure | Switch end on a two-ended scale. Move the weight. Remove. Open the recipe |
| A result | Under the heading, a strip: the vibes that were asked for, then the two on which this area stands furthest from the middle. Each is a band and a literal sentence. Reasons and the trade-off as now | Open a vibe to see its parts for this area. "More like this" |
| Area page, as a portrait | The page opens with every vibe as a scale, furthest from the middle first. Each opens to its parts: figure, standing, source, date. Then its blind spots. Then facts that are never ranked: gym kinds, cuisines present, recognised venues, broadband, borough figures named as the borough's. Street incidents are closed until opened | Open and close. "Search with this" adds the vibe to a search. "More like this" |
| Comparison | Vibe rows first: one scale a row, a mark for each of the 2 to 4 areas. Then parts. Ordered by the person's weights, then by how far apart the areas stand | Add or drop an area. Open a row to its parts |
| More like this | A list of areas alike on the most scales, each with a literal line: "in the same fifth as X on 9 of the 12 scales compared". With a search open, its limits still apply | Turn it into a search that also weighs journeys and budget. Remove a scale from the likeness |

```
Thrushcombe, Quillhaven                                   made-up data
Stands furthest from the middle on: Village feel, Street character, Leafy

Village feel                  [ . . . . # ]  above 95% of the 22 areas compared
Street character   Polished   [ # . . . . ]  Gritty     further towards Polished than 81% ...
  Industrial and storage land      0% of the area    the same as 9 others     Source, date
  Within 50 m of a main road       6%                less than 77% ...        Source, date
  Homes per hectare                31                less than 59% ...        Source, date
  Public green space               38%               more than 72% ...        Source, date
  In a conservation area           No figure in this data
  Based on 4 of 5 parts. Burro cannot see litter, graffiti, empty shops, or who lives here.
Pace               Calm       [ . # . . . ]  Buzzy      ...
```

### 4.2 What stays fixed

| Rule | Detail |
|---|---|
| A mark is a band, never a number | Five bands. The sentence beside it carries the count. The mid-rank percentile is still never printed (contract 7.2) |
| No badge | The page says where an area stands on a scale. It never says an area "is" an end |
| Parts are always one press away | A vibe with its parts hidden is an opaque score |
| The blind spots travel with the vibe | On the shelf, the chip, the card, the portrait and the methods page |
| A person cannot edit a recipe | They can remove the vibe and weigh its parts one by one, where each part's direction is allowed |

### 4.3 When a vibe cannot be measured

| Case | What is said | In ranking |
|---|---|---|
| Too few parts have a figure for this area | "Burro cannot place {name} on {scale}: {k} of its {m} parts have no figure in this data." No mark is drawn, and never one in the middle | The component is dropped for the area and weights are rebalanced, as now |
| The vibe is not in this release | On the shelf, greyed: "Not in this data yet", with the fixed reason: a licence not yet answered, a test not yet passed | The edit is rejected as `not_in_release` |
| No vibe exists for the wish | One fixed line for each: "Burro has no measure of street cleanliness. No open data exists below borough level." | No edit |
| The wish is about who lives somewhere | The neutral sentence of contract 8.4, unchanged | No edit for that part |

New codes for the third row: `street_cleanliness`, `venue_ratings`, `prices_and_hours`, `mobile_coverage`, `neighbourliness`. `broadband` and `health_services` stop being unmet once their features exist.

## 5. How the engine changes

### 5.1 What becomes of the 23 features and the 12 tags

All 23 features stay, with their ids. A feature gains two fields in core: `describes` (`place`, `buildings` or `events`; there is no value for residents, so none can be declared) and `role` (`rank` or `show`). `nuisance` becomes a field on the feature, in place of a list in the reader.

| Tag today | Becomes | Note |
|---|---|---|
| `leafy`, `village_feel`, `family_amenities` | The same ids | An id names the idea, not the method. The recipe of `leafy` moves when canopy is measured |
| `buzzy`, `quiet_residential` | The two ends of `pace` | New id. Noise leaves the recipe |
| `historic_character` | The high end of `street_age` | New id. Gains listed buildings |
| `strong_high_street`, `foodie` | `high_street_life` | New id. The two shared two of their parts |
| `creative` | Retired | "Creative" describes people as much as places. Its venue part is in vibe 8. It may return when studio and workspace layers are cleared |
| `near_universities`, `waterside`, `evening_venues` | Retired as tags. The words now weigh the one feature each was made of | A vibe with one part is a feature |

New features, by when their source allows. Ids are the reports' proposals.

| Wave | Features | Source |
|---|---|---|
| 1. Approved today | `listed_buildings`, `road_major_exposure`, `park_large_proximity`, `park_facilities`, `private_outdoor_space`, `growing_space_proximity`, `incident_criminal_damage`, `incident_asb` | Catalogue rows only |
| 2. Licence read, entry to add | `land_industrial`, `canopy_cover`, `street_canopy`, `historic_park_proximity`, `gym_choice`, `pool_proximity`, `court_pitch_kinds`, `broadband_gigabit` | The entries the reports propose |
| 3. Waits for an answer, a page or a spike | `culture_kinds_nearby`, `library_proximity`, `meeting_place_kinds`, `gp_walk`, `pharmacy_walk`, `nursery_nearby`, `cuisine_variety`, `lowcost_gym_proximity` | See 2.2 |
| Shown, never ranked (`role: show`) | Gym kinds, cuisines present, recognised venues, council tax, borough figures | A new fact kind each: 5.6 |

### 5.2 A recipe as data

Recipes stay in core, because core decides them. They move from code to one table, and each release repeats them, as `catalogue.json` repeats the features, so that a release can be read alone and the methods page is generated.

```json
{
  "vibe_id": "street_character",
  "label": "Street character",
  "high_end": "Gritty",
  "low_end": "Polished",
  "terms": [
    {"feature_id": "land_industrial", "hundredths": 35, "reading": "high"},
    {"feature_id": "road_major_exposure", "hundredths": 25, "reading": "high"},
    {"feature_id": "homes_density", "hundredths": 15, "reading": "high"},
    {"feature_id": "green_cover", "hundredths": 15, "reading": "low"},
    {"feature_id": "conservation_cover", "hundredths": 10, "reading": "low"}
  ],
  "blind_spots": ["street_cleanliness", "empty_shops", "upkeep", "who_lives_here"],
  "tested": {"agreed": 14, "right_third": 13, "opposite_third": 0, "lists_dated": "2026-11-02"}
}
```

The figures under `tested` are an example. `low_end` is `null` for a one-ended vibe. `tested` is written by the pipeline and is `null` in the synthetic release. The arithmetic is `tag_raw()` as it stands.

| Test on the table | Refuses |
|---|---|
| Weights sum to 100 | Any other sum |
| No part above 50, and three parts at least | A vibe that is one feature by another name |
| No part in the crime dimension | Crime in any recipe |
| No nuisance in a vibe with two ends | A scale on which seeking an end ranks a nuisance up |
| Every part has `role: rank` and describes a place, buildings or events | A shown-only figure, or a resident one |
| `university_proximity` is in no vibe with two ends | A way to ask for fewer students |
| A blind spot is one of a fixed list of codes | Free text about a place |

### 5.3 How a scale with two ends is ranked

| Where | Change |
|---|---|
| `TagWeight`, `TagEdit` | Gain `direction`: `high` or `low`. `default` on an edit means "as it is", and `high` for a vibe not yet in the spec |
| Utility (contract 6.2) | `score / 100` for `high`, `1 - score / 100` for `low`. It is what a feature of polarity `either` does today |
| Reducer rule 7 | `low` on a one-ended vibe is rejected as `direction_not_allowed` |
| `canonical()` | Writes `direction` only when it is `low`. Every spec made before keeps its hash, and the published test vectors stand |
| The sentence | A new template, `scale`: "{label}: further towards {end} than {pct}% of the {compared} areas compared in this release". The counts are those of contract 7.3, from the side the area is on |
| Not offered | The middle. "Not too gritty, not too polished" makes no edit in v1 |

`rank()` is as pure as before: the direction is in the spec, and the score is in the release.

### 5.4 How "like this area" is computed

Likeness is worked out on vibes only. Cost, journeys, crime and anything about residents take no part, by construction.

| Step | Rule |
|---|---|
| Band | Each area's position on each vibe is one of five bands, by the count of areas strictly below |
| Shared | The vibes on which both areas have a position. Fewer than 60 in 100 of the release's vibes: likeness is unknown, and says so |
| Distance | The sum of band differences over the shared vibes, divided by four times their number. 0 is the same band on every scale |
| Order | Distance from low to high, then `area_id` |
| The sentence | A new fact kind, `alike`: "{name} is in the same fifth as {other} on {same} of the {shared} scales compared, and {far} are three fifths apart or more." Every number is a count |
| Step 1 | `alike(release, area_id)` in core, pure, a function of the release alone. Route 6 returns the first five. It can be cached |
| Step 2 | A spec component, `like:<area_id>`, with a weight, at most one. Its utility is one less the distance. "Like Thrushcombe, within 40 minutes of work, under £1,800" is then one ranking, through one `rank()` |

No single "87% alike" is printed. The order and the sentence come from the same bands, so they cannot disagree.

### 5.5 Crime, and the word "gritty"

| Case | What happens | Rule kept |
|---|---|---|
| "Gritty", "edgy", "industrial" | Street character, towards Gritty | No part of the scale is crime or a nuisance |
| "Polished", "smart", "not gritty" | Street character, towards Polished. It is not read as a wish for low crime | Reducer rule 8: an inferred edit never weighs crime |
| "Gritty but low crime" | Two edits: the scale, and the crime features, stated | Crime is weighted only on request |
| "Rough", "dodgy", "sketchy" | No edit. The verifier bans these words and the reader does not map them | Contract 7.4 |
| "Posh", "working class" | The neutral sentence | Contract 8.4 |
| "Up and coming" | No edit, and an unmet line: Burro cannot measure change | The 2025 Indices are not comparable with 2019 |
| Street incidents | `incident_criminal_damage` and `incident_asb` join the crime dimension: weight 0 by default, less only, in no recipe, shown by category with the caveat sentence | Rule 8 of the reducer is keyed on the dimension, not on two ids |
| On the portrait | The Street character scale is open. Street incidents sit under it, closed, and never feed the mark | Crime is never rolled up |

### 5.6 What must change in the contract

| Section | Change |
|---|---|
| 2.3, 2.8 | A release repeats the recipes. `parse_release` gains the tests of 5.2. `CATALOGUE_VERSION` becomes 2 |
| 3.1 | New feature rows by wave. `describes`, `role` and `nuisance` on each. The crime rule names the dimension |
| 3.2 | Tags become vibes: ends, the cap of 50, blind spots, `tested`. Retired ids are listed and never reused |
| 4, 4.2, 5.1, 5.3 | `direction` on a vibe weight and edit. The `canonical()` rule of 5.3. Later, the `like` component |
| 6.2 | Utility of a vibe by direction. Later, utility of `like` |
| 7.1 to 7.3 | Fact kinds `scale`, `alike`, `mix` (counts by kind), `borough` (a figure that names its borough). A template for each, and one for a vibe with no position |
| 7.4 | More refused words: "best", "top", "highly rated", "acclaimed", "friendly", "close-knit", "up and coming". An end name passes only inside the `scale` template |
| 8.1, 8.2, 8.4 | New unmet codes. Vibe words in the lexicon. "Quiet" as two edits. The resident rules unchanged |
| 9.2 | Route 11 serves vibes with ends, recipes, blind spots and test results. Route 4 gains each area's band on each vibe, for the map. Route 6 gains the portrait order and `alike` |
| 13 | Every weight and threshold here, as an open point |

## 6. What to build first, on the synthetic city

The aim is that the founder can type "somewhere a bit gritty, near a park", see the scale, paint the map and open a portrait within days. It needs no new real data. Nothing seen on it says how vibes will feel on London (ADR 0010). It tests the vocabulary and the flows.

| Order | Part | What | Done when |
|---|---|---|---|
| 1 | core | `direction` on a vibe weight and edit, and the utility of 5.3 | A test: the same spec with `low` reverses the order on that vibe alone |
| 2 | core | The recipe table with ends and blind spots, and its tests. Seven vibes first: 1, 2, 3, 4, 6, 7 and 11. Catalogue rows for three features: `land_industrial`, `road_major_exposure`, `listed_buildings` | Every recipe passes the tests of 5.2 |
| 3 | pipeline | Made-up values for the three: the first two from the `industry` trait each area already has, the third from `old`. `make fixture` | "Gritty" finds Cindermoor first and "polished" finds a leafy old area, on the committed seed and three others |
| 4 | core | `alike()` and the `scale` and `alike` facts | Every sentence is literally true of the release, by the existing test |
| 5 | api | Routes 11, 4 and 6 as in 5.6. `make openapi` | The contract test passes |
| 6 | web | The shelf, the map painted by a vibe, the vibe chip, the strip on a card | A person can pick an end with no typing |
| 7 | web | The portrait, the comparison rows, "more like this" | The area page opens with scales, and each opens to its parts |
| 8 | pipeline, core | Made-up features for vibes 5, 8, 9, 10, 12 and 13, each from a trait set by hand | All thirteen are on the shelf |

Alongside, with no code:

| Task | Who | Unblocks |
|---|---|---|
| Recruit the panel and collect the lists of 3.1 | Founder | Every vibe on real data. It needs no data and can start now |
| Decide items 2 and 8 | Founder | 2.5 and 2.6 |
| Write the proxy audit rule of 3.3 | Founder | Any new feature on real data |
| Open the land use table and the canopy map's accuracy report | A spike, once the entries are registered | Vibes 1 and 4 |
| Questions: the GLA on canopy, Sport England, parkrun. Pages: the Arts Council | Founder | Vibes 4, 8, 9 and 10 |

## 7. Risks, and what is left to decide

| Risk | Why it matters | What this design does |
|---|---|---|
| Street character measures hard-edged, not what people mean by gritty | The founder's own word would feel wrong on screen | It ships only if the panel's lists agree. If not, it is dropped, not renamed |
| The panel's idea of an end encodes who lives there | A recipe that fits the panel may fit a stereotype | The panel judges streets and buildings. The proxy audit runs after, on a written rule |
| Seeking the gritty end ranks crime up by proxy | It would break the crime rule in effect | The check of 3.3, with actions named before it runs |
| Most of the new data is not yet licensed or measured | Six of thirteen vibes wait on a source, an answer or a spike | The shelf says "not in this data yet". Seven vibes can ship on sources approved today |
| A position reads as a verdict | People who live in an area may read "Gritty" as an insult | No badge. A scale name that passes no judgement. A sentence that states a count |
| Thirteen scales are too many to read | The portrait becomes a dashboard | Furthest from the middle first. The rest closed |
| Retiring four tags loses wishes people type | "Creative" and "by the river" are common | The words still make an edit, on a feature. Nothing a person types stops working |
| A recipe is tuned until it passes | The test then proves nothing | Lists are committed before scores. Half are held back and used once |
| The reports' licence readings are wrong | Most pages were read through a reader that summarises | No entry is approved on this document. Each is re-read in a browser before launch |
| "More like this" reproduces a pattern of who lives where | Like places have like residents | Likeness uses vibes only, and every vibe has passed the audit |

| Decision | Recommendation |
|---|---|
| Item 2: what may go into "gritty" | B: place only, with street incidents beside it |
| Item 8: who lives there | Option 2, in two steps. Vibes from places under every option |
| Item 3: how far to take gym tiers | Kinds first. Then "low-cost" or "premium" for operators the founder names, in the operator's own words. Drop "boutique" and "mid-market" |
| Item 4: what "highly ranked" means | "Recognised", with the scheme and the date named. Never "best" or "top" |
| Item 7: bring broadband into v1? | Show it. Rank on it, and build vibe 13, only if the spread across London is wide |
| May a position be shown for a vibe that has not passed its test? | No |
| The cap of 50 hundredths on any part | Yes. It retires three one-part tags |
| The thresholds of section 3 | Accept as first guesses. Tune once, on real data, before the held-back lists are used |
| A count of "about right" answers on the area page | Later, and only by decision. It sends something new to the server |
| Naming parks, operators and public institutions on the portrait | As the reports recommend: only from a source registered for display, after the verifier is extended |
