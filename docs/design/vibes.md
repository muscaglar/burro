# Vibes: the design

Status: design, 2026-09-23. Revised the same day after two reviews, one on fairness and law and one from a person who knows London. Section 11 lists what the reviews changed, and section 12 what they did not. It is the one design the team builds from. It merges three proposals, which stay beside it as the record of what was weighed: [from the person](vibes-proposal-newcomer.md), [from the data](vibes-proposal-evidence.md) and [from difference](vibes-proposal-difference.md).

Nothing here is built. Nothing here changes a rule, the registry or a decision record: each of those changes is listed, and is made by its owner in the same change as the code. Nothing here is legal advice, and no lawyer has read it. Every weight and threshold is a first guess. Every example uses the made-up city, and no sentence describes a real place. Nothing was measured on real data, so every statement about where a recipe would place a real kind of area is a prediction.

It rests on the seven reports in [`docs/research/vibes/`](../research/vibes/), on [PLAN](../PLAN.md), on ADRs 0002, 0004, 0006, 0007 and 0010, and on [the contract](contract.md). Where this design and a report disagree, this design is what is built. Section 13 lists the pages re-read for this document.

Written before the registry held the six entries that rest on a permission in writing, as the founder reports: parkrun's events, the two canopy layers of the Greater London Authority, and the three lists of Arts Council England. Where this document says that one of them is not registered, or that it waits on an answer, [the plan for real data](london-data.md) and the registry stand.

## 0. In short

| Question | Answer |
|---|---|
| What is a vibe | A named, published recipe over measured facts about a place. It says which of five bands an area sits in among the others, and never what the area "is" |
| How many | 14. Three are scales with two named ends. Eleven have one direction |
| What is new on screen | Everyday words are shown before a search. The map can be coloured by one vibe. An area page opens with a portrait, and ends by saying where to go and look. Any area can start "more like this" |
| What is new in the engine | A tag may be a scale. A spec may point a scale at either end, and may hold one "like this area". `rank()` stays a pure function of a spec and a release |
| Gritty | The founder asked for one metric made of crime, socioeconomic factors and street cleanliness. No honest form of that metric exists (section 3.1). The person's word is kept and quoted. Burro reads it as Works and warehouses, a vibe with a literal name, and says what it cannot measure |
| Who lives there | In no vibe, under any option. The founder chooses between three options for showing census figures (section 4). Until then ADR 0006 stands |
| What can be felt in days | Eleven vibes, the lens, the portrait and "more like this", on the synthetic city (section 8) |
| What London can carry | Ten vibes rest on sources approved today. Four wait on a source or an answer: Works and warehouses, Leafy, Places to train and Places to meet |

## 1. What a vibe is

A vibe is a word for the character of a place, such as leafy or buzzy, that Burro has written down as a recipe. The recipe names its parts and gives each a weight in hundredths. Each part is a feature of the catalogue, with a source and a date. The pipeline works out every area's raw score with `tag_raw()`, and the area's position is the percentile of that score (contract 2.4 and 3.2). An area with under 60 hundredths of a recipe present has no position. In code and on the wire a vibe is a `tag`. "Vibe" is the word on the screen.

A vibe has one of two shapes. A scale has two ends, both named and both plain tastes, such as Calm and Buzzy, and a person may ask for either. A one-way vibe, such as Leafy, has one direction, and a person may ask for more of it.

### The seven promises

| # | Every vibe | What that means | Held by |
|---|---|---|---|
| 1 | Has a recipe anyone can read | Parts and hundredths are on `/vibes`, served by route 11 and repeated in each release. Two parts or more. No part carries 60 hundredths or more | A test on `TAGS`: sums to 100, two parts, none at 60 |
| 2 | Has a source and a date for every part | Each part is a catalogue row with `source_ids`, `vintage`, and whether it is measured, modelled or averaged. A vibe's date is the span of its parts, "parts dated 2021 to 2026", never the day the release was built | `test_every_fact_names_a_source_and_a_date`, `parse_release`, and a change to contract 7.2 |
| 3 | Says what it cannot see | A fixed list. One line on the portrait, all of them on `/vibes` | A test: every vibe has a `cannot_see`, and each line is one of a fixed list of codes |
| 4 | Describes a place | Every part passes the four tests of 2.6, which are run over parts as well as words and recorded. No part is a crime or incident figure. No part describes residents: the field has no value for them | `test_no_feature_or_tag_describes_residents`, widened to ends, words and `cannot_see` |
| 5 | Is a taste and not a verdict | A band among the areas compared. No sentence says a place "is" an end, and no surface ranks the areas by a vibe unless the vibe has earned it (5.2). A scale holds no nuisance. There is no overall vibe score and no vibe about safety | The `vibe` template, the verifier, the surface flags, and a test that a scale holds no nuisance |
| 6 | Is measured from where homes are | A part is a share of homes within a walk, or a mean weighted by homes, and not a count per km² or a share of the drawn boundary. A mixed area is drawn as a range, never as a point in the middle | The `basis` field of a feature. The `spread` of 5.3 |
| 7 | Is Burro's own judgement, and says so | Every vibe carries the fixed line "The recipe is Burro's own. The weights are a judgement." The source line reads "Burro's recipe. Made from data published by: ...", so no publisher appears to have placed the area. No marketing copy uses a vibe word about a real named area. The methods page names a contact, and promises a review within 28 days when a resident objects to how their area is placed | Fixed text in core. A test on the templates. The promise is the founder's to keep |

A vibe ships on real data only when it has passed section 6 on that release. The audit of 6.1 comes first and wins.

## 2. The catalogue

### 2.1 The fourteen

"Shelf" says whether the word is one of the seven shown first, before a search. The rest sit under "more".

| # | Family | Vibe | `tag_id` | Ends, low to high | Plain meaning | Founder's item | Shelf, as |
|---|---|---|---|---|---|---|---|
| 1 | Streets and homes | Homes | `homes` | Houses, Flats | Houses with outdoor space, or flats close together | 1 | |
| 2 | Streets and homes | Built age | `built_age` | Newer, Historic | Homes built since 2000 at one end. Old homes, listed buildings and protected streets at the other | 1 | "period" |
| 3 | Streets and homes | Village feel | `village_feel` | | A small, compact centre of its own, old streets, independent places | 1 | "villagey" |
| 4 | Streets and homes | Quiet streets | `quiet_residential` | | Homes away from main roads and from clusters of late venues, with little transport noise | 1 | "quiet street" |
| 5 | Streets and homes | Works and warehouses | `works_warehouses` | | Land used for industry, storage and transport, near where people live | 2, in part | |
| 6 | Pace and food | Pace | `pace` | Calm, Buzzy | How much there is to eat, drink and go out to within a walk of homes | 1 | "lively" |
| 7 | Pace and food | Food and drink | `foodie` | | Many places to eat and drink, many of them independent | 1 | |
| 8 | Green | Leafy | `leafy` | | Gardens, woodland and trees, and a public park near home | 5 | "leafy" |
| 9 | Green | Parks close by | `parks_close_by` | | A park within a walk, a large one not far, and things to do in it | 5 | "near a big park" |
| 10 | Things to do and join | Culture on the doorstep | `culture_nearby` | | Many kinds of cultural venue within a walk | 4 | |
| 11 | Things to do and join | Places to train | `places_to_train` | | Gyms, pools, courts and pitches open to the public, within a walk | 3 | |
| 12 | Things to do and join | Places to meet | `places_to_meet` | | Many kinds of place you go back to, within a walk | 6 | |
| 13 | Daily life | Family amenities | `family_amenities` | | Primary schools, play space and parks nearby | 1 | |
| 14 | Daily life | Everyday on foot | `everyday_on_foot` | | A food shop, a high street, a station, a GP and a pharmacy within a walk | 7 | "walkable" |

Broadband is not a vibe. It is a line on the portrait, with the regulator's checker for one address (2.5).

### 2.2 Recipes, and whether London can carry them

`low` reads a part from its low end. Every vibe can run on the synthetic city, because a feature may be in core before any real release carries it (contract 2.3). The state below is about London.

**Now**: the source is approved in the registry today, and needs a catalogue row at most. No real data has been ingested for anything. **Licence**: ready when a named licence question is answered by its owner, by a page only a person can open, or by a use added to an entry. **New source**: a report read the licence and proposes an entry, and nobody has registered it or opened the file. "Approved" is the hundredths of the recipe whose source the registry approves today. Under 60, London cannot place the vibe yet.

| Vibe | Recipe, in hundredths | State | Approved | What settles it |
|---|---|---|---|---|
| Homes | 40 `homes_flats` + 35 `homes_density` + 25 `private_outdoor_space` shortfall | Now | 100. It runs at 75 until the audit row for outdoor space passes | Outdoor space is a modelled score from the Indices of Deprivation, and the review expects it to follow race and income. It enters only if it is under 0.3 on every table of 6.1 |
| Built age | 35 `homes_pre1919` + 25 `conservation_cover` + 20 `listed_buildings` + 20 `homes_post2000` low | Now | 100 | The build period bands, read in the file. Catalogue rows |
| Village feel | 25 `independents_nearby` + 20 `centre_small` + 20 `centre_compact` + 20 `homes_pre1919` + 15 `conservation_cover` | Now | 100 | Whether each town centre boundary carries its class. The village and high-road trap of 6.2 |
| Quiet streets | 40 `road_major_exposure` low + 30 `evening_cluster_exposure` low + 30 `noise_exposure` low | Now | 100 | Catalogue rows. The golden query "a quiet street near a lively high street" |
| Works and warehouses | 40 `land_industry` + 35 `land_storage` + 25 `land_transport_other` | New source | 0: not placed | Register and open the land use table. What "Transport (other)" holds. The spike of 3.1. Its audit row. All three parts come from one table |
| Pace | 35 `venue_evening` + 30 `venue_food_drink` + 20 `highstreet_access` + 15 `culture_venues` | Now | 100 | The Overture spike, for the culture part. The office and visitor trap of 6.2 |
| Food and drink | 40 `venue_food_drink` + 40 `independents_nearby` + 20 `cuisine_variety` | Now | 100. It runs at 80 until cuisines are read and their audit row passes | Overture's cuisine categories on the pinned release |
| Leafy | First: 40 `land_gardens` + 30 `land_woodland` + 30 `green_cover`. Then: 35 `canopy_cover` + 25 `street_canopy` + 20 `land_gardens` + 20 `green_cover` | New source | 30, then 20: not placed | The land use table, then the canopy map's accuracy report and the 20-street spike. Today's recipe held no tree and is not shipped |
| Parks close by | 40 `park_proximity` low + 30 `park_large_proximity` low + 30 `park_facilities` | Now | 100 | The commons check of 2.3. Catalogue rows |
| Culture on the doorstep | 50 `culture_kinds_nearby` + 30 `culture_venues` + 20 `library_proximity` low | Now, after the spike | 80 | The Overture spike. A zero from Overture is unknown, not zero. It must vary within inner London alone |
| Places to train | 35 `gym_choice` + 25 `pool_proximity` low + 20 `court_pitch_kinds` + 20 `park_proximity` low | New source | 20 | Register Active Places. A question for Sport England, as a courtesy |
| Places to meet | 40 `meeting_place_kinds` + 20 `library_proximity` low + 20 `sports_facility_nearby` + 10 `play_space_proximity` low + 10 `highstreet_access` | Licence | 20 | Five kinds or more with London-wide data. It ranks only if it varies within inner London alone. If not, it is a block on the portrait that lists each kind and the nearest one |
| Family amenities | 40 `school_primary_nearby` + 35 `play_space_proximity` low + 25 `park_proximity` low | Now | 100 | School results moved beside it (2.5) |
| Everyday on foot | 25 `grocery_walk` low + 25 `highstreet_access` + 20 `station_walk` low + 15 `gp_walk` low + 15 `pharmacy_walk` low | Now | 70 | `nhs-ods` gains the use `scoring`. The pharmacy list is registered |

Each count of venues is the number within a 10-minute walk of homes, weighted by homes, and no longer a count per km². `road_major_exposure` and `evening_cluster_exposure` are shares of homes within 100 m of an A road or motorway, and within 150 m of a cluster of evening venues. `green_cover` is the share of homes within 300 m of a Public Park or Garden. A home is placed at the centre of its output area, so "homes" means output areas weighted by their homes, counted from the approved housing tables. A land use part is the mean share across the area's LSOAs, weighted by their homes, because the table is by LSOA: it cannot say how far a home is from a depot. An id names the idea and not the method (contract 3.1), so these change with `CATALOGUE_VERSION` 2.

### 2.3 The data each new part needs

An id in the first column is a registry id today. A source with no id is not registered, and the report that proposes it holds the draft entry.

| Source | Registry today | Gives | State | What settles it |
|---|---|---|---|---|
| `os-open-roads` | approved | `road_major_exposure` | Now | A catalogue row. Road class is not traffic |
| `fsa-food-hygiene-ratings` | approved | `grocery_walk`, `independents_nearby`, `evening_cluster_exposure`, the pub as a kind of meeting place, hotels for the line of 2.5 | Now | The business types read in the file. They were not read for this document (section 13). The data date is printed beside every count |
| `gla-town-centre-boundaries` | approved for `gazetteer` and `scoring` | `centre_small`, `centre_compact`, and the centre's name for "Go and look" | Now for the two parts. Licence for the name | Whether each boundary carries its class and a name. `display` added with evidence before a name is shown |
| `voa-council-tax-stock-of-properties` | approved | `homes_post2000`, and `built_since` of 5.3 | Now | The build period bands, read in the file |
| `historic-england-listed-buildings` | approved | `listed_buildings` | Now | A catalogue row. It also meets the registry's condition on conservation areas (contract 13) |
| `os-open-greenspace` | approved | `green_cover`, `park_large_proximity`, `park_facilities`, `growing_space_proximity` | Now, after one check | Its ten kinds hold no common, heath or woodland, and do hold Cemetery, Golf Course and Religious Grounds. `green_cover` counts Public Park or Garden only. A golf course never counts. Before any park part ships, check that 20 named commons, heaths and forests are in the file, with a way in. If not, find a registered source first |
| `dfe-gias` | approved | `childrens_centre_proximity` | Now | Confirm the entry covers the children's centre file |
| `mhclg-iod-2025-underlying-indicators` | approved, noise only on the allowlist | `private_outdoor_space`, `incident_criminal_damage` | Now | An allowlist row each. The file is named in full wherever a figure from it is shown. The methods page says which columns are used, which never are, and why. No figure is headed "deprivation" |
| `overture-places` | approved, London quality unmeasured | `cuisine_variety`, `culture_kinds_nearby`, community halls as a kind | Now, after the spike | The planned quality spike. The category list read on the pinned release |
| `tfl-journey-planner-timetables` | approved | Services after midnight within a 10-minute walk, as a line | Now, if the founder agrees | Whether the feed holds night services. It leaves out rail, the Overground and the Elizabeth line, and the line says so. PLAN section 4 lists night times as out |
| Land use statistics 2022, table by LSOA | not registered | `land_industry`, `land_storage`, `land_transport_other`, `land_gardens`, `land_woodland`, and offices and retail for the line of 2.5 | New source | Register as gated. Open the table: LSOA vintage, units, what each category holds. Build from categories, never the "industry and commerce" group. It is as at April 2022 and has no later edition |
| Trees Outside Woodland map, with the forest inventory | not registered | `canopy_cover`, `street_canopy` | New source | The accuracy report. Does canopy reach the road edge on 20 streets called tree-lined |
| Sport England Active Places | not registered | `gym_choice`, `pool_proximity`, `court_pitch_kinds`, `sports_facility_nearby`, `lowcost_gym_proximity`, kinds of gym, studios | New source | Register once, from `fitness.md`. A question for Sport England. Studios come from here first, with their operational status. Overture adds studios only if under 1 in 10 of 50 checked by hand is closed |
| Ofcom fixed coverage by output area | `ofcom-connected-nations-2025` is held on scope | `broadband_gigabit`, shown as a line | New source | A new entry for the latest snapshot. It is weighed on request only if the figure varies across London |
| NHS pharmacy list | not registered | `pharmacy_walk` | New source | Open one file: a postcode, and a field that tells a counter from a postal service |
| `nhs-ods` | approved for destination search only | `gp_walk` | Licence | Add `scoring` and `display`, with evidence |
| Arts Council England: libraries, accredited museums, National Portfolio | not registered. Nobody has read the pages | `library_proximity`, recognised venues | Licence | The founder opens and saves the pages. A question for the owner if they are silent on reuse |
| parkrun event list | not registered. Nobody has read the page | parkrun as a kind of meeting place | Licence | A written yes. Until then it stays out, and no list is compiled by hand |
| GLA canopy and green cover 2024 | not registered. The page says All Rights Reserved | A better canopy map | Licence | A question for the GLA GIS team. Build on the open map meanwhile |
| An open map of aircraft noise | none was looked for | Telling aircraft noise from road noise | The founder's task | The approved noise figure mixes road, rail and aircraft |
| An open map of railway lines | none is registered. OpenStreetMap is for routing only | The line "a railway runs through this area" | New source | Until then the line is said of rivers, A roads and motorways only |

| Asked for, and cannot be done honestly | Why |
|---|---|
| Street cleanliness, litter, fly-tipping | No open data below borough level. A borough holds about 14 neighbourhoods |
| Empty shops, graffiti, shutters, late licences | No open source at neighbourhood scale |
| "Gritty", "polished" or "well-kept" as a measure | What a person reads as gritty on a walk is upkeep, shutters, litter and the kind of shops. None is measured. See 3.1 |
| A rating of a gym, a venue or a park. "Best", "top", "highly rated" | Every ratings and awards site the research read forbids commercial reuse or building a database. Google Places is banned |
| Membership prices. "Boutique" as quality. "Mid-market" | No lawful price list was found. The site terms the research read keep content to personal or non-commercial use (`fitness.md`) |
| 5G for a neighbourhood. "Full fibre" for a neighbourhood | Published for boroughs and constituencies only. The coverage API is banned |
| Broadband speed or take-up | They measure what households bought, so they describe residents |
| Whether people are friendly. Whether a group has room | No dataset measures it. It is a claim about residents |
| Weekday from weekend. Whether a place is busy with visitors or with locals | No open source. The line of 2.5 is the nearest measure |
| Markets and festivals | No London-wide open list was found |
| "Up and coming", "on the up" | The 2025 Indices are not comparable with 2019. It is also a claim about who is moving in |
| A language, or a named country of birth, by neighbourhood | The detailed census tables are published for boroughs only |
| Who lives there, read off the places | Inferring residents from places is a guess shown as a fact (`people.md`). Burro shows what is there |
| Who lives there, as a vibe | Rule 8. See section 4 |

### 2.4 What each cannot see, and the sentences that call it up

Every vibe carries one line first, word for word: "One street or one home. An area is many streets." It carries no number, because a release holds no count of residents (ADR 0010). The portrait shows one line for each vibe. `/vibes` shows them all.

| Vibe | Cannot see. Word for word | Sentences a person might type |
|---|---|---|
| Homes | The size of a home inside. Balconies and front gardens. Whether one home has a garden | "a house with a garden" · "proper city living, flats are fine" · "more suburban, we want space" |
| Built age | The state of a building. Its inside. An area the conservation data does not cover is unknown, not zero | "period houses" · "somewhere with history" · "a newer area with modern flats" |
| Village feel | Whether neighbours know each other. Which shops there are. Empty units | "villagey" · "a little centre with its own shops" · "a small-town feel" |
| Quiet streets | Noise from neighbours, venues or works. Road noise from aircraft noise. How busy a road is | "quiet" · "a quiet street near a lively high street" · "peaceful, residential" |
| Works and warehouses | Whether streets are clean or run down. Empty shops. Graffiti. What the land is used for today. Recorded crime. Who lives there | "old warehouses and railway arches" · "industrial" · "somewhere a bit gritty" |
| Pace | Weekday from weekend. Who the venues serve. Opening hours. What is on | "lively, lots going on in the evening" · "somewhere calm" · "nothing much going on" |
| Food and drink | Whether the food is good. Prices. Whether a place is still open. Hygiene ratings are never shown | "a great food scene" · "independent cafes" · "lots of different food" |
| Leafy | Trees under 3 m. Planting or felling since the map was made. Street trees, until the canopy map is in | "leafy" · "tree-lined streets" · "green, with gardens" |
| Parks close by | Upkeep. Whether a park is busy. Opening hours. No open rating of parks exists | "near a big park" · "a park I can run in" · "tennis courts and a playground" |
| Culture on the doorstep | Ratings. What is on. Prices and hours. Whether a venue is still open. Recognition is not quality | "theatres and galleries nearby" · "arty" · "highly rated theatres" |
| Places to train | Price, quality, crowding, hours. Gyms under about 5 stations. Climbing walls and boxing gyms | "a gym and a pool nearby" · "sporty" · "a cheap gym within a walk" |
| Places to meet | Whether people are friendly. Whether a group has room or still meets. Waiting lists. parkrun, until permission is in writing | "a community feel" · "things to join" · "a parkrun nearby" |
| Family amenities | Catchments. School places. What childcare costs. Who lives there | "good for families" · "primary schools and playgrounds" |
| Everyday on foot | Whether a surgery takes new patients. Opening hours. Step-free access at every station. Which side of a railway a home is on | "walkable" · "a GP and a chemist nearby" · "I do not want to need a car" |

Some of these hold words the rule-based reader does not know today. Each is a golden query first and a vocabulary change second.

### 2.5 What sits beside a vibe, and never inside it

| Beside | What is shown | Direction, default | Why it stays outside |
|---|---|---|---|
| Recorded crime | Recorded criminal damage, by category, with the crime caveat, the period in full and "six-year average". Never on one line with the two existing crime figures, which use another denominator | Less only. Off and closed until asked | Nobody seeks it. It moves with violence at 0.81 across London's LSOAs (`grit.md`). It is listed under recorded crime on `/vibes`, and beside no vibe |
| Recorded anti-social behaviour | Nothing at launch | | It is reports to the police about people nearby, over two years only. It needs its own audit row first |
| Quiet streets, Pace | Transport noise, nitrogen dioxide, "away from main roads" | Less only | They are nuisances. "Away from main roads" is how a person avoids hard-edged streets |
| Pace | Lived-in or destination: offices and retail against homes, by land use, and hotels nearby | Shown only | It tells a neighbourhood high street from an office or visitor district. Each part needs a catalogue row and an audit row |
| Pace, Everyday on foot | Services after midnight within a 10-minute walk | Shown only. A founder decision | It touches PLAN section 4 |
| Places to train | Kinds of gym nearby: council leisure centre, chain gym, independent, class studio, gym with a pool | Shown only | The mix follows income |
| Places to train | A low-cost gym within a walk, for operators whose own published words say so | Near only. Off until asked | It is a filter a person asks for, from a list the founder keeps |
| Culture on the doorstep | Recognised venues, each with its scheme and date | Shown only, at first | Recognition follows age and money |
| Family amenities | Results at nearby primary schools, with source and date | More only. Off until asked, as today's feature is | A result is achieved by the children who attend. It fails test 1 of 2.6 as a part |
| Places to meet | A place of worship within a walk, no faith named | Near only. Off until asked. A founder decision | It is `on_request`, so it is in no vibe and is not a kind of meeting place. Coverage differs by faith, and nobody has measured by how much |
| The portrait | Gigabit-capable broadband can be ordered: the share of homes, and a link to the regulator's checker for one address | Shown. Weighed on request only if it varies | The answer that matters is for one address |
| Waterside, a campus nearby | One measure each, as a chip and a line on the portrait | As the feature's polarity | A vibe with one part is a feature |

### 2.6 The words people use

A word enters the vocabulary, and a part enters a recipe, only if it passes four tests. The answers for every part are recorded in the new decision record.

| # | Test | Fails when |
|---|---|---|
| 1 | Empty the houses. If everyone moved out tonight and other people moved in, would it still be true? | It is about people: "studenty", "posh", "friendly". A school's results |
| 2 | Can a person want it without wanting harm to anyone? | It is a nuisance or a verdict: "rough", "safe" |
| 3 | Can it be said as a position and not a verdict? | It is praise or blame with nothing behind it: "best", "cool", "polished" |
| 4 | Is there a measure at neighbourhood scale, with a licence on file? | Street cleanliness, 5G, ratings |

| Word | Kind | What Burro does |
|---|---|---|
| gritty, edgy, raw | Mixed | The chip quotes the person's word: "'gritty', read as Works and warehouses". Marked "assumed". One fixed line: "Burro has no measure of how clean or run-down a street is." Never a crime weight, never anything about residents |
| industrial, warehouses, railway arches | Place | Works and warehouses |
| polished, smart, manicured, well-kept, not gritty | No data | No edit. One fixed line: "Burro has no measure of upkeep. You can ask for less noise, or to be away from main roads." |
| quiet, peaceful, residential | Place | Quiet streets, and nothing else. It is not a vote against places to eat and drink |
| lively, buzzy | Place | Pace towards Buzzy |
| calm, nothing going on, sleepy | Place | Pace towards Calm, marked "assumed" |
| suburban, urban, more space | Place | Homes, marked "assumed" |
| modern flats, new-build | Place | Built age towards Newer |
| arty, creative | Mixed | Culture on the doorstep, marked "assumed" |
| sporty, active | Mixed | Places to train, marked "assumed" |
| community feel, neighbourly | Mixed | Places to meet, marked "assumed". "Friendly neighbours" is about people: the neutral notice |
| highly rated, best, top | Judgement | Read as the vibe alone. One line says Burro holds no ratings |
| cheap gym, budget gym | Place | The low-cost gym filter, once the operator list exists |
| rough, dodgy, sketchy, safe | Verdict | No edit. The person is told recorded crime can be turned on |
| international, diverse, studenty, posh, hipster, young professionals | People | No edit. The neutral notice of contract 8.4, word for word, the same for everyone |
| up-and-coming, gentrifying | Change, people | No edit. "Burro has no measure of how an area is changing" |
| clean streets · 5G · prices | No data | No edit. One fixed line each. For 5G, a link to the regulator's checker |

A mixed word is read as its place part only. The list of mixed words is short, written in one place and reviewed as a whole, as `PLAIN` is.

### 2.7 What becomes of today's 12 tags

All 23 features stay, with their ids. No share outlives a restart and no real release exists, so nothing stored names a tag. A retired id is never reused.

| Today | Becomes |
|---|---|
| `leafy`, `village_feel`, `family_amenities`, `foodie`, `quiet_residential` | Kept, with new recipes. An id names the idea, not the method. `foodie` is labelled "Food and drink" and `quiet_residential` "Quiet streets" |
| `buzzy`, `evening_venues` | Retired. The Buzzy end of `pace` |
| `historic_character` | Retired. The Historic end of `built_age` |
| `creative`, `strong_high_street` | Retired. The words now call up Culture on the doorstep, and the `highstreet_access` feature |
| `near_universities`, `waterside` | Retired as tags. Each was one feature. The words weigh that feature, and a campus keeps its one direction |

## 3. The founder's eight points

| # | The founder asked for | Burro will | Burro will not | Ready |
|---|---|---|---|---|
| 1 | Vibes as what sets Burro apart | Show everyday words before any search, colour the map by one, open every area page with a portrait that ends in where to go and look, and let a person move from an area to the areas like it | Let a model write or score a vibe. Publish an overall vibe score. Say a place "is" anything | Eleven vibes on the synthetic city in days. London after section 6 |
| 2 | "Gritty", from crime, socioeconomic factors and street cleanliness | Keep the person's word and quote it. Read it as Works and warehouses. Offer less noise and "away from main roads" to a person who wants the opposite. Show recorded criminal damage on request | Build the metric as asked: see 3.1. Name any end of any scale Gritty or Polished. Rank, map or list areas by it | Synthetic now. London once the land use table is opened and the spike of 3.1 is run |
| 3 | Kinds of gym: boutique against value | Build Places to train. Show the kinds of gym nearby. Offer "a low-cost gym within a walk" on request, from operators' own words | Rate a gym. Print a price. Say "boutique" or "mid-market". Put a tier inside a vibe | After Active Places is registered. The operator list is the founder's |
| 4 | Cultural activities, highly ranked ones | Build Culture on the doorstep from kinds of venue within a walk. Show "recognised" venues with the scheme and date named | Say "best", "top" or "highly rated". Say what is on | Counts after the Overture spike. Recognition after the Arts Council pages are opened |
| 5 | Green spaces, leafy and parks | Build Leafy from gardens, woodland and tree canopy, and Parks close by from walks to parks | Call an area leafy for holding a cemetery or a golf course. Rate a park. Say one street is tree-lined | Parks now, after the commons check. Leafy after the land use table |
| 6 | Community building, such as parkrun | Build Places to meet from the kinds of place within a walk, the pub among them | Say people are friendly. Use parkrun without a written yes | Part now. It ranks when five kinds have London-wide data and it varies within inner London |
| 7 | Services: 5G, fibre | Show gigabit-capable coverage on the portrait, with the regulator's checker for one address. Build Everyday on foot on walks to a food shop, a station, a GP and a pharmacy | Rank on 5G. Say "full fibre" of a neighbourhood. Rank on speed or take-up | Everyday on foot now, at 70 hundredths. Broadband after the Ofcom files are registered |
| 8 | Demographics: local makeup, foreign born, ethnicities | Under every option: let a person name a community place they must reach, and rank on the journey. Link to the statistics office. Under option 2, after a reading: the census figures in a fenced panel | Answer "who lives here" through places. Build any vibe, ranking, filter, map layer, comparison or likeness from who lives somewhere. Label an area "diverse" or by a community | Option 1 now, once the place index is checked for such places. Option 2 when someone qualified has read the panel and the founder amends ADR 0006 |

### 3.1 Item 2, said plainly

There is no honest way to build "gritty" as one metric of crime, socioeconomic factors and street cleanliness. Each ingredient fails for a different reason.

| Ingredient | Why it cannot go in | What Burro does with it |
|---|---|---|
| Crime | A person who seeks "gritty" would be asking Burro to rank recorded crime up | Recorded criminal damage, beside, on request, less only |
| Socioeconomic factors | They describe residents. The official indicators include asylum support, disability benefits and English language ability. That is rule 8, and choices D and E of 4.4 | Nothing, unless the founder changes rule 8 with advice |
| Street cleanliness | No open data exists below borough level | One fixed line that says so |
| What is left: land use, main roads, density, little green | The first draft made a scale of these, from Polished to Gritty. Both reviews expect it to fail. Main roads, density and little green are likely to follow race and income in London, so an "avoid" end would rank poorer and more mixed areas down. Industrial land is likely to find trading estates at the edge of London, where few people live, and not the inner high roads people call gritty | Industry, storage and transport land become Works and warehouses, which some people seek. Main roads become a nuisance a person may avoid. Density stays in Homes. Nothing is named Gritty or Polished |

| Step | What happens | If it fails |
|---|---|---|
| The spike, about a day once the land use table is registered | 20 areas that residents describe as full of works, warehouses, depots and arches, and 20 they describe as having none. The recipe must tell them apart | The vibe is dropped. "Gritty" is then answered by the fixed line and the two nuisances, and is not renamed into something else |
| The word, with ten people on the synthetic city | Shown the chip, do they accept Works and warehouses as a fair reading of "gritty"? | If most do not, "gritty" makes no edit and gets the fixed line alone. The vibe stays for the words of its own |
| The audit of 6.1 | Works and warehouses is tested against the audit tables and the income domain before any weight is tuned | At 0.6 it is dropped. It is never shown and barred from being sought |
| Until these pass | On a real release it has no lens, no place in the strip, the table or likeness, and its bands are left out of route 4. On the area page it is never first, and shows its parts with their figures | |

## 4. The founder's decision on residents

Items 2 and 8 press on AGENTS.md rule 8: rank places, never residents. This section sets out the choice. It does not make it. **If nothing is decided, ADR 0006 stands as written and the product is built as option 1.**

`people.md` separates three acts. Showing an official figure is what the statistics office itself does. Ranking or filtering by who lives somewhere makes Burro's own code sort places by race or religion. Building a named vibe from who lives somewhere attaches a judgement to a group's presence, for every user.

### 4.1 The three options

| | Option 1. Places only | Option 2. Show, never rank | Option 3. Residents in ranking or vibes |
|---|---|---|---|
| In one line | ADR 0006 as written, with a link out | Census figures in a fenced panel on the area page. All else as option 1 | Resident data feeds a weight, a filter or a vibe |
| Allows | A place of worship, a community centre or a shop named as a place to reach. Places to meet. A link to the statistics office | All of 1. A person can read who lived in the area in 2021 | All of 2. A person can search or sort by who lives there |
| Answers item 8 | "Local makeup": no, inside Burro. The link answers it outside, for a larger official area. "Cultural background": only through the places a person names | Both | Both, as a search |
| What it costs the founder | The thing asked for is one click away and not on the page | A public promise is reversed: PLAN section 15 says Burro will not show these "even for information". The repository records that demographics were first asked for as a vibe input, and that record will be read in any argument | The public sentence "never by who lives there" has to go |
| Worst fair reading | "It says it never describes residents, then sends you to the census." | "A where-to-live recommender prints the ethnic and religious makeup of each area, from a lockdown census nearly six years old, with no legal advice." | "An app that filters London neighbourhoods by race or religion." |
| Risks | Least. Proxy effects remain, and 6.1 covers them | Wording, staleness and steering by invitation. For race, segregating is less favourable treatment. Unreviewed | Segregation, indirect discrimination and stereotype are all in play. A filter a person sets reveals their own faith or origin, in the spec and in a share. Unreviewed |
| Gate | None | A reading of the panel by someone qualified. A free legal clinic counts. The founder's own written acceptance is not a gate: a signature is not a safeguard | Paid legal advice, which ADR 0007 rules out today |

### 4.2 What changes under each

| Where | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| Product | The portrait ends with one line: "Official census figures", a link to the statistics office if its pages can be linked by area, and "This leads to an official area that is larger than this neighbourhood." | All of 1, and the panel of 4.3 | All of 2, and a control that filters or weighs by residents. Not designed here |
| Release | No change | One new file for resident figures. `rank()`, recipes, `facts_for()`, `similar()` and `explain()` never open it | Resident features in the catalogue |
| Registry | Place sources only, as usual | A new dimension, `residents`. A rule: a source in it may have `display` and internal uses, and no other. The audit entry and `registry/README.md` reworded in the same change | A resident source registered for `scoring` |
| AGENTS.md rule 8 | Unchanged | Its first two sentences stand. Its third, on `audit_only`, is reworded | Rewritten |
| Decision records | A new record for vibes. ADR 0006 unchanged | ADR 0006 amended, with the choice and the weak points of 4.1 written into it | ADR 0006 replaced. ADR 0007 changed |
| PLAN | Sections 4 and 8, for the vibes | Also section 15, section 9 and decision 4 of section 14 | Also section 13 and the public fairness position |
| Contract 8.4 | **Unchanged under every option.** The neutral notice stays word for word. It never names the census, the panel, the link or the statistics office. A person who types "fewer immigrants" is never told where the country-of-birth table is | The same | Rewritten |
| Tests | The resident denylist, widened. The notice is byte for byte the same whether or not a release holds a residents file | Also: nothing that ranks, explains or compares opens the residents file. The panel's text is fixed and rendered by a test | New tests for whatever is allowed |

### 4.3 The panel, if the founder chooses option 2

| Rule | Detail |
|---|---|
| Where | The area page only, last, outside the portrait. Headed "Census 2021: who lived here". The past tense is deliberate |
| Not in the page | The browser loads it when the person asks. It is not in the static page, it carries a no-snippet mark, and the address that serves it is never indexed. A block that is only closed is still in the page text |
| Never beside a rank | The area page is built with no spec and shows no rank. The panel never appears on a result, a comparison, a share or the lens |
| Before a reading | Nothing. Age and students wait too: on `people.md`'s reading age is protected for adults in services, ADR 0006 names both, and the reader refuses "not too many students" in words. Household type alone may be shown first if the founder chooses. The review judged it the least exposed table. That is a lay reading |
| After a reading | What the reading allows, of: household type, age bands, students, country of birth, ethnic group, religion |
| Form | A table: the statistics office's category, in its words and order, and the share as a whole percent. Never a sentence. No London column, because a figure beside it is "higher than average" without the words |
| No labels | No "main group". No colour. A category under 1% reads "under 1%" |
| Can be checked | The figures are sums over Burro's own boundaries, so they match no official table. The panel says so, and links to the list of output areas that were summed |
| Never in | A result, a reason, a vibe, a filter, the lens, a comparison, "more like this", a share, the reader's vocabulary, or anything sent to a model |
| Never shown | Sexual orientation, gender identity, English proficiency, language, detailed country of birth |

### 4.4 Item 2, in the same terms

| Choice for "gritty" | What goes in | It is | Must change |
|---|---|---|---|
| A | Place only | Allowed under every option | Nothing |
| **B** | A, with recorded criminal damage beside it, on request | Allowed under every option | Nothing |
| C | Recorded incidents inside a vibe | A change to the crime rule, not to rule 8. To seek "gritty" would rank recorded crime up | ADR 0006, contract 3.1 and 3.2, PLAN 9 and 15 |
| D | Deprivation inside a vibe | Option 3. Its inputs include asylum support, disability benefits and English language ability | Rule 8, ADR 0006, and paid advice |
| E | Deprivation shown, never ranked | A showing act, as option 2 is, and behind the same gate. The publisher says the index identifies deprivation, not affluence | PLAN 15 |

### 4.5 Recommendation

**Launch on option 1, with the link out. Apply to a free legal clinic this week, and set a date. Build the panel of 4.3 on the day a reading allows it. Choice B for "gritty". Never option 3 without paid advice. Vibes come from places under every option.** The first draft of this design recommended option 2 in two steps, with the founder's signature as one way through the gate. The fairness review showed why that is not a safeguard, and the recommendation changed. The decision is still the founder's.

| Why | |
|---|---|
| The founder has said local makeup is part of the product | So option 2 stays the aim. What changed is the gate, not the goal |
| Showing is where the evidence is least worrying, and it is still unread | `people.md` found no UK action against display, and says that is a limit of its search as much as a finding. It did not read section 19A of the Equality Act, which widens who may complain about a neutral rule (section 13) |
| A reading costs nothing but a wait | ADR 0007 names free legal clinics. The vibes do not wait for the answer |
| If the founder chooses option 2 now | It can be built as 4.3 sets out. The choice, the date and the weak points of 4.1 go into ADR 0006 in the same change |

What is left over under the recommendation: at launch the founder's item 8 is met by a link and by named destinations, and not on the page. No professional has read any of it. A place-only vibe still follows wealth.

### 4.6 Why no option needs rework later

| Switch | What is added | What is untouched |
|---|---|---|
| Option 1 to 2 | The residents file in a release, the registry entries, the amended ADR, the panel's own address. The portrait's last slot gains the button that loads it | Every vibe, recipe, screen and route. The neutral notice |
| Option 2 to 1 | The file is left out of the next release. The slot shows the link alone | The same |
| Either to 3 | A new value of `describes`, a new kind of feature that is on request only, and one explicit control. No vibe is rebuilt | Every vibe. Likeness, which never reads such a feature |

## 5. The experience, moment by moment

Every word about a place is served by the API, as today. The website lays it out. Headings such as "More than most here" are fixed text held in core.

| # | Moment | On screen | The person can | Underneath |
|---|---|---|---|---|
| 1 | Before a search: the shelf | Under the prompt box, seven everyday words as buttons: leafy, villagey, lively, quiet street, period, walkable, near a big park. The rest under "more". A vibe the release lacks is left out, and one line, "more to come", links to `/vibes` | Press a word. Open it to read its meaning, recipe and what it cannot see. "Add to my search" | Route 11. Adding is one edit and no text |
| 2 | Before a search: the lens | Pressing a word colours the map by it, in five bands, and the table of all areas gains a column. Only a vibe with the `lens` flag can be pressed (5.2) | See where in the city a word is found | Route 4 serves, in one cached answer, the bands of every vibe that has a lens, so the server is never told which word was pressed. It serves no band for any other vibe, for crime or for a figure of 2.5 |
| 3 | Before a search: start from a place | "Know one area already? Start there." A field over the area names. Beside it: "Somewhere you need to be near? A school, a place of worship, a shop, a relative." | Open that area's portrait. Add a place to reach | The area names are already on the page. A place is found through the place search field, route 8, and chosen by its id, so its name is never sent to a model |
| 4 | In the prompt | The box, as today. Examples use vibe words and no proper noun | Type anything. Name an area: "like Alderwick, but nearer Pellam Cross" | One `POST` body. Nothing is read key by key |
| 5 | What Burro understood | A chip for each vibe. A scale reads "Pace: towards Calm". A mixed word is quoted: "'gritty', read as Works and warehouses", marked "assumed". The person's own words are underlined, from `rests_on`. One line for each thing not read | Flip a scale to its other end. Change how much it counts. Remove it. Open the recipe | The reader maps a closed list of words to a vibe and an end |
| 6 | Turning a scale | One slider with two named ends. It rests in the middle, which is no weight | Move it towards an end | One edit to route 2. The list is marked busy, then redrawn from the returned spec |
| 7 | A result | Under the name, a strip: the vibes asked for, then up to two others that have the `strip` flag and on which the area sits furthest from the middle. Then reasons and the trade-off, as now | Press a mark for its sentence and sources. "More like this" | The strip is shown, never scored. Only what is in the spec counts. Recorded incidents never appear unasked |
| 8 | The area page | The portrait, below | Open any recipe. Open the closed blocks. "Search for this character" | Route 6, built with no spec, so it is the same for every visitor. It reads with scripts off |
| 9 | Comparison | Character rows first, for vibes with the `table` flag. Each scale is one line with a mark for each area. Then the rows by weight, as now | Add or drop an area | Route 7. The census panel never appears here |
| 10 | More like this | Closed until pressed. Five areas, under the words "alike in streets, buildings and places", each with a line: "Wickerford is in the same band as Thrushcombe on 14 of the 19 measures compared, and least alike in Pace and food." | Turn it into a search that also weighs journeys and budget. Add "but quieter" | `similar()` on the area page. A `like` anchor in the spec for a search |
| 11 | The vocabulary page | `/vibes`: every recipe, its publishers and dates, which parts it shares with other vibes, what it cannot see, the audit rule and each outcome (passed, changed, dropped), and the words Burro will never measure, with the reason | Read before searching | Route 11. Static. It reads with scripts off |

### 5.1 The portrait

```
Thrushcombe, in Quillhaven                                        made-up data
Character
  Homes       Houses  ---[#]---+---+---    Flats      band 2 of 5     Made of
  Pace        Calm    ---+--[#######]--+-  Buzzy      varies within this area
  Built age   Newer   ---+---+---+---[/]   Historic   band 5 of 5     Made of
More than most here   Village feel · Leafy · Food and drink: 31 places to eat within a 10-minute walk
Less than most here   Everyday on foot: 12 minutes on foot to a food shop
Burro cannot place    Works and warehouses. Parts with a figure in this release: 0 of 3
What is here          one line for each kind of place, with its publisher and date
Go and look           the nearest station · the centre · the nearest large park · one walk
What Burro cannot see one line for each vibe shown. The rest is on /vibes
More like this · Recorded incidents, noise and air          [closed until opened]
Cost · Stations · Sources
Census figures        a link to the statistics office. Under option 2, the button of 4.3
```

The sketch shows the layout. Its figures are for illustration and are not taken from the fixture. `[/]` is a hatched mark.

| Rule | Detail |
|---|---|
| Order | Scales first, in a fixed order that starts with Homes. Then up to three vibes with 60% of areas or more strictly below, then up to three with 60% or more strictly above, furthest first, ties by id. A vibe with no `strip` flag is never in either list: it is shown lower, as its parts |
| A mark is a band | One of five. `band = 1 + min(4, (5 * below) // compared)`, where `below` counts the areas strictly below. No percentage is printed for a vibe, on any release: five bands is the precision the parts support |
| The sentence | "Pace: band 2 of 5, counted from Calm to Buzzy, among the 22 areas compared in this release. Parts dated 2021 to 2026. The recipe is Burro's own. The weights are a judgement." If the oldest part is over five years old, the date comes first |
| The plain figure | Beside each mark in the two lists, the figure of the vibe's heaviest part, as a count a newcomer can read: "1 gym within a 15-minute walk". "Less than most here" never stands alone |
| "Made of" | Each part: its weight, this area's figure, its band, its publisher, its date or period in full, and "modelled" or "averaged" where it is. A figure from the Indices of Deprivation names that file in full |
| Kinds of food nearby | Inside "Made of" for Food and drink: the count of kinds, then the kinds in alphabetical order. Never ordered by size, never a leading cuisine, never a label for the area, never under a heading about culture or community |
| One line, one fact | No sentence is composed from several facts, so the verifier stays as it is |
| Names | Counts and kinds only, but for "Go and look" |

### 5.2 Where a vibe may appear

A vibe has three flags: `lens`, `strip` and `table`. A sorted column is a league table, and a coloured map is a map of it, so each is earned.

| Rule | Detail |
|---|---|
| To hold a flag | Both ends are plain tastes. The vibe is under 0.5 on every table of 6.1, and at 0.3 or over its review note is published. The gap between its 20th and 80th percentile areas is large enough to matter, by a threshold written for that vibe |
| On a real release | Every flag starts off, and is turned on by the audit's outcome. A test: no vibe at 0.5 or over has a flag, and none at 0.3 or over has one without a published note |
| Candidates | Pace, Homes, Built age, Leafy, Parks close by, Quiet streets, Village feel, and the amenity vibes |
| On the synthetic city | Every vibe may hold every flag, so the founder can judge the controls |
| What this does not stop | Anyone can read 450 static pages and sort them. With literal names, what they get is a list of areas with the most storage land |

### 5.3 A mixed area, a rebuilt area, and where to go and look

An area holds many thousands of people. Most inner areas hold both ends of every scale.

| Case | What the pipeline works out | What is said | In a ranking |
|---|---|---|---|
| A mixed area | The recipe for each sub-area the parts allow, placed on the areas' band edges. `spread` is the bands that the middle half of homes span | At three bands or more, the mark is drawn as a range: "Pace: varies within this area, from band 2 to band 4 of 5." Never a point in the middle | The area is ranked on its score, as any other |
| An area rebuilt since the data | `built_since`: the share of homes built after the oldest part of the vibe, from the build period table. It describes buildings | At 10% or more, the mark is hatched: "Much of this area was built after this data was gathered." | Ranked as any other. The line is shown on its card. Left out of the tests of 6.2 |
| A railway, river or main road through the area | Whether one crosses it | One fixed line: "A river runs through this area. Check which side a home is on." A railway waits for a registered source | No effect |
| Where to go and look | The nearest station, the town centre by name, the nearest large park by name, conservation area names, and the minutes on foot between them | "Go and look": "Most places to eat and drink are around {centre}. The streets furthest from a main road are to the {direction}." One walk: station, centre, park. Fixed text, no model | No effect |

Every name in "Go and look" comes from a stored fact in a source registered for `display`. Today that is true of stations and of OS Open Greenspace, whose name field is unchecked. The town centre and conservation area entries need `display` added, with evidence. PLAN section 4 lists "named venues" as out, so this is a founder decision (question 7).

### 5.4 When a vibe cannot be measured

| Case | What is said | In a ranking |
|---|---|---|
| The area has under 60 hundredths of the recipe | "Burro cannot place {name} on {label}. Parts with a figure in this release: {known} of {parts}." A hatched bar. Never a mark in the middle | The vibe is dropped for that area and the weights rebalanced, as now |
| The release does not hold the vibe | It is not on the shelf. On `/vibes`: "Not in this data yet", with the fixed reason | The edit is rejected as `not_in_release` |
| The idea has no honest measure | One fixed line: "Burro has no measure of street cleanliness below borough level." | No edit |
| The wish is about who lives somewhere | The neutral sentence of contract 8.4, word for word | No edit for that part |

## 6. How a vibe earns its place on real data

PLAN section 8 says a tag ships only if it passes a sanity set of 40 neighbourhoods. The first draft asked five people to name areas at each end. That could not be assembled, and it would have rewarded a recipe for matching an area's reputation. It is replaced by an audit and a test with people, in that order. **When the audit and the people disagree, the audit wins.**

### 6.1 The proxy audit, written before any recipe is tuned

ADR 0006 asks for a written rule before the audit runs, and the founder writes it. This is the rule the design proposes. It has a line at which a vibe is dropped without discretion, because a rule that only triggers a review leaves the founder judging their own product.

| Part of the rule | Proposal |
|---|---|
| Measure | Spearman rank correlation across the rankable neighbourhoods, in size, whichever its sign. It will run higher than the LSOA figures in `grit.md`, because averaging removes noise |
| Tested against | The share of each broad ethnic group. Born outside the UK. Each religion. Aged 65 and over. Households with children. Disability. The income domain of the Indices of Deprivation, which needs its own audit-only entry and has none today. Each recorded-crime rate |
| What is tested | Every part. Every vibe, in each direction it can be sought. Ten fixed specs, each asking for several vibes at once: the top 20 areas are compared with London as a whole. Likeness as a whole: how far an area's five nearest areas are from it on the audit tables, against five random areas |
| At 0.3 | Review. A note on the methods page says what was found, the aim the vibe serves and why it is kept. Without the note the vibe holds no flag. The largest figure over all the tables is the one that counts |
| At 0.5 | The vibe loses its lens, strip and table flags, leaves likeness, and cannot be sought in the direction that ranks the group down. The action "show it and do not let it be sought" is not open to a vibe that keeps a lens |
| At 0.6 | The vibe or the part is dropped from the release. Nobody may overrule this |
| When | The rule is committed, with its date, before any audit table is opened. Each part is audited before its recipe is tuned, so a failure arrives before the work is sunk |
| Published | The rule, and each outcome: passed, changed or dropped |
| What it cannot do | It tests what Burro can correlate. It does not say whether an aim is legitimate or a means proportionate. That is a legal judgement. Nobody independent checks the founder's arithmetic |

The audit tables are gated in the registry until a store the product cannot read exists, with its check in CI. That gate is unchanged.

### 6.2 The people test

| Step | What happens | Why |
|---|---|---|
| Who | 25 to 30 people who know parts of London well, residents of areas at each end among them | One person's London is half a city |
| Rate, do not name | Each rates only the areas they know well, about 15, from 1 to 5 on each vibe, with the drawn boundary in view and no score shown | Nobody can name ten areas at each end of 14 vibes. A list picked after the scores proves nothing |
| A written rubric | In words about streets, buildings and places. For Works and warehouses it asks about works, depots, warehouses and arches, and never uses the word "gritty". No street imagery: none is registered, and Street View is banned | What people call gritty is shaped by who lives there and by what they have heard |
| Which vibes | Only those people hold opinions on: the three scales, Leafy, Village feel, Quiet streets, Food and drink, Works and warehouses. The amenity vibes are checked against counts made by hand in 20 sampled areas | Nobody has a view on which area leads for pharmacies |
| Traps | Ten centres people call villages and ten long high roads: Village feel must separate them. Office districts and visitor districts: Pace must not place them with lived-in high streets, or the line of 2.5 must say so. Two agreed mixed areas a scale: each must show as a range | A recipe can pass on the ends and still mislead |
| Own area | Residents see the portrait of their own area and mark each line "right", "wrong" or "cannot say" | A mover checks their own area first |
| When | After neighbourhood map v0, because a recipe scores a drawn boundary | |
| Kept private | The ratings name real areas, so they stay out of the public repository. A salted hash of the file is committed before the release is built, and counts alone are published: "13 of 14 in the right band" | Promise 5. Anyone can see the file was fixed first |

| Test | A vibe passes when | If it fails |
|---|---|---|
| Agreement | The rank correlation between the median rating and the band is 0.6 or more, and 7 of the 10 highest-rated areas are in the top fifth | Change the recipe once and test on fresh ratings, or drop the vibe |
| Own area | Under one in five residents marks the vibe "wrong" for their own area | The same |
| Like this | Ten residents each name three areas like their own. For seven of the ten, one of the three is among the five Burro offers | Likeness is not shown |
| Its own thing | Its rank correlation with every other vibe is below 0.8, and below 0.6 where the two share a part | Merge the two |
| Not the centre by another name | It still separates the rated areas within inner London alone, and within outer London alone | Drop it |
| Covered | 95 in 100 rankable areas have a position | Say where it cannot be measured, or wait |

A vibe that has not passed is not shown on a real release. The synthetic release shows every vibe, under its banner, and a vibe that waits on a source carries a badge that says so.

## 7. Changes to the engine and the contract, in order

Code and contract change together. Steps 1 to 10 are the first slice. The new decision record is numbered 0013: 0012 is taken.

| # | Where | Change | Done when |
|---|---|---|---|
| 1 | `docs/adr`, contract | ADR 0013: a vibe is a band on a published recipe. It holds the surface rule of 5.2, the audit lines of 6.1, the four tests run over every part, and the rule that a vibe over the drop line is dropped and not shown. The founder agrees that a scale may read a good thing low at one end | The record is accepted |
| 2 | core, contract 3.1 | `Feature` gains `describes` (`place`, `buildings`, `events`), `kind` (`taste`, `amenity`, `nuisance`, `on_request`), `basis` (`homes`, `area`), `method` (`measured`, `modelled`, `averaged`), `period` and `in_likeness`. `NUISANCES` is read from `kind`. The crime rules name the dimension, not two ids. A row for every new part of 2.2 and 2.5. The redefinitions of 2.2 | The resident denylist test covers the new fields |
| 3 | core, contract 2.3, 3.2 | `Tag` gains `shape`, `low_end`, `high_end`, `family`, `meaning`, `cannot_see`, `beside`, and the flags `lens`, `strip` and `table`. The 14 recipes. Seven ids retired. A release repeats the recipes and flags it was built with. `CATALOGUE_VERSION` 2 | Every recipe passes: sums to 100, two parts, none at 60, no crime, no nuisance in a scale, no `on_request` part, every part describes a place or buildings |
| 4 | core, contract 4, 5.1, 5.3 | `TagWeight.toward` and `TagEdit.toward`: `high`, `low`, and `default` on an edit. `low` on a one-way vibe is rejected as `direction_not_allowed` | The same spec with `low` reverses the order on that vibe alone |
| 5 | core, contract 4.2 | `canonical()` writes `toward` only when it is `low` | The published test vectors still pass |
| 6 | core, contract 6.2 | Utility of a vibe: `score / 100` towards high, `1 - score / 100` towards low. `ENGINE_VERSION` 1.4.0 | A vibe towards high ranks as the tag did |
| 7 | core, contract 7 | Contract 7.2, row `tag`: `as_of` is the span of the parts, not `built_at`. Slots `band`, `end`, `spread_low`, `spread_high`. Templates `vibe`, `vibe_range` and `vibe_unknown`. The source line and the fixed line of promise 7. The verifier refuses "best", "top", "highly rated", "acclaimed", "friendly", "close-knit", "vibrant", "up and coming", "gritty" and "polished". An end's name passes only from a fact's slots | Every sentence is literally true of the release |
| 8 | pipeline, contract 2.3 | A release holds `spread` and `built_since` for each area and vibe. Made-up land use from the `industry` trait, `listed_buildings` and `homes_post2000` from `old`, and `grocery_walk`, `park_large_proximity` and `park_facilities`. One made-up area is mixed on purpose. `make fixture` | The fixture rebuilds byte for byte |
| 9 | core, contract 8 | Vibe words in `LEXICON`. The list of mixed words. A turned end becomes the other end: "not buzzy" is Pace towards Calm. "Not gritty" makes no edit. New `UnmetCategory` values: `street_cleanliness`, `upkeep`, `ratings`, `prices_and_hours`, `mobile_coverage`, `change_over_time` | Each example sentence of 2.4 is a golden query. One area can sit high on Quiet streets and towards Buzzy on Pace |
| 10 | core, api, contract 9.2 | `similar(release, area_id, n)` and the `likeness` fact. Route 11 serves the vibe fields. Route 4 gains `bands`, for vibes with a lens only. Route 6 gains `portrait` and `similar`. `make openapi` | The contract test passes. No new route. The neutral notice is byte for byte what contract 8.4 holds |
| 11 | core, contract 4, 5, 6.2 | The spec gains `like`: one anchor at most. A seventh array of edits, `like_ops`. The `like` component. `ENGINE_VERSION` 1.5.0 | A place is like itself. Likeness runs both ways |
| 12 | pipeline, core | Made-up features for the other three vibes, each with its badge | All 14 are on `/vibes` |
| 13 | core, contract 7 | Fact kinds `mix`, for kinds and counts beside a vibe, `look`, for the names and walks of "Go and look", and `borough`. A source id for Burro's own operator list | With the first real release that needs them |
| 14 | registry, pipeline | The entries of 2.3, each re-read in a browser. The audit of 6.1 first, then ingest and the people test. The release records each vibe's outcome, and `/vibes` prints it | A vibe passes section 6 on a real release |

What `kind` decides:

| `kind` | A person may want | In a vibe |
|---|---|---|
| `taste` | More or less of it: venues, flats, density, storage land | Any |
| `amenity` | More of it, or nearer: a park, a food shop, green cover | Any. Inside a scale it may be read low |
| `nuisance` | Less of it only: noise, air, main roads, recorded crime | A one-way vibe may read it low. Never in a scale. Crime in none |
| `on_request` | One direction, by a fairness rule: a campus, a place of worship, a low-cost gym | None. Off by default |

### 7.1 Likeness

| Step | Rule |
|---|---|
| What is compared | Parts, not vibes, and each part once. The first draft compared vibes, which counted the walk to a park six times. Only a part with `in_likeness`. Never crime, a nuisance, cost, a journey, a figure of 2.5, or a part at 0.5 or over in 6.1. `private_outdoor_space`, `homes_flats`, `homes_density` and the school parts stay out until the likeness row of the audit passes |
| Distance | The parts are grouped by family. Within a family, the mean difference in band, divided by four. Across families, the mean, so each family counts the same. 0 is the same band on every part |
| In a search | Never a part of a vibe the person has set themselves, so "like Thrushcombe but quieter" matches on everything but the parts of Quiet streets. Component `like`, utility one less the distance, weight as any mention. The anchor stays in the results, marked "your starting point" |
| Too little known | If either area has a figure for under 60% of those parts, likeness is unknown and says so. If the anchor has, the edit is rejected as `anchor_not_placed` |
| On the area page | `similar()` is a function of the release alone. Route 6 serves the first five, ordered by distance, then `area_id`. The page shows them only when the person opens the block |
| The anchor's name | Taken only from the whole of an area's name in the person's own words. A model may copy a name and never supply one |
| Privacy | The anchor may be where someone lives. It is never logged, as no part of a spec is. A share leaves it out unless the sender ticks "include my starting area", as a share coarsens a workplace unless the sender chooses otherwise |

## 8. The first slice, on the synthetic city

It needs no licence, no download and no model. Every figure is made up and says so.

| | |
|---|---|
| Vibes | Eleven, placed: the seven shelf words (Leafy, Village feel, Pace, Quiet streets, Built age, Everyday on foot, Parks close by), and Homes, Food and drink, Family amenities and Works and warehouses. The other three are on `/vibes` with a badge |
| Leads with | Pace and Leafy. Works and warehouses is in the slice so the founder can judge how "gritty" is answered, and is never the first thing shown |
| Screens | The search page (shelf, lens, chips, two-ended slider, strip on a card). The area page (portrait, "Go and look" with made-up names, "more like this"). `/vibes` |
| Routes | 1, 2, 4, 6 and 11, extended. No new route |
| Not in it | The `like` anchor in a search. Comparison rows. Anything from the census. The audit and the people test, which need real data |

| Day | Core, pipeline and API | Website | The founder can then |
|---|---|---|---|
| 1 | Steps 1 to 3: the catalogue | | Read all 14 recipes as route 11 serves them |
| 2 | Steps 4 to 6 and 8: scales are ranked, and the fixture holds the new parts | The two-ended slider | Drag Pace towards Calm and watch the list and the map change |
| 3 | Steps 7 and 9: sentences and words | The chips | Type "a quiet street near a lively high street" and see two chips that do not pull against each other. Type "somewhere a bit gritty, near a park" and see the word quoted, what it was read as, the fixed line, and no crime weight |
| 4 | Step 10: the routes | The shelf and the lens | Press "leafy" before any search and see the city coloured by it |
| 5 | | The portrait and the strip | Open the mixed area and see a range, not a point. Open Otterby Fields, which most surveys have not reached, and read what Burro says it cannot place |
| 6 | | `/vibes`. "Go and look". "More like this" | Start from Thrushcombe and walk the city by likeness |
| 7 | | The recorded answers made again. One whole visit walked by hand | Judge the words and the controls |

Four cautions. Nothing seen on the synthetic city says how London will feel (ADR 0010): the founder is judging the words and the controls, not the truth of any vibe. The synthetic city will feel richer than London can at launch, so the badges of section 6 show there too. Other teams are changing `packages/` and `apps/` now, so step 3 lands as one coordinated change. And section 5 describes behaviour, not one client: the iOS app reads the same routes.

Work that can start beside it, and needs no code: write the audit rule of 6.1; apply to a free legal clinic; recruit the raters; open and save the pages of 2.3; put the questions to the owners.

## 9. What was taken from each proposal

These choices still stand after the reviews. Where a review overturned one, section 11 says so.

| Question | Chosen | Not taken, and why |
|---|---|---|
| One part, or a cap | Two parts or more, none at 60 | A cap of 50 and three parts (data): stricter than the coverage rule needs. Waterside at 100 (difference): a vibe with one part is a feature |
| Tag ids | New ids for scales. Seven retired now | Keeping all 12 (person): it leaves `buzzy` naming a scale whose other end is Calm |
| Direction | `toward`: `high` or `low` | Five stops with a middle (difference): no simple sentence is literally true of the middle |
| "But cheaper" | Asks for a budget if none is set | A budget set from the anchor's rents (difference): it edges towards an affordability verdict |
| The lens | Bands in route 4 | A new route (person, difference): not needed. Scores on the wire (difference): a client cannot print what it is not sent |
| The four tests for a word, the lens, the portrait, likeness | Sections 2.6, 5 and 7.1 | Taken from the person and difference proposals |

## 10. Risks and open questions

| Risk | What this design does about it |
|---|---|
| Fourteen vibes may be one axis: near the centre or far from it. Air quality, travel time and lack of outdoor space move together at 0.75 to 0.84 across London's LSOAs (`grit.md`) | The "its own thing" and "not the centre" tests of 6.2 |
| A search for Leafy, Historic, Village feel and Houses together may rank areas much as wealth does | The ten fixed specs of 6.1. Nothing else. A place-only product still follows wealth, and this design does not claim otherwise |
| The raters' idea of a vibe encodes who lives there, so a recipe that fits them may fit a stereotype | A rubric about streets and buildings. Ratings, not named lists. The audit runs first and wins |
| A map or a list of any vibe can be passed round as a map of bad areas | Literal names. Flags that are earned. No vibe named for a verdict. No marketing copy that uses a vibe word of a real area |
| A true figure can mislead by how it is shown. The Digital Markets, Competition and Consumers Act 2024, section 226(3), as read through a tool: "an overall presentation may be deceiving even if the information it contains is true". Whether Burro's free pages fall under it is not known. It matters more once Burro sells passes | Bands and not percentages. The span of dates. "Modelled" and "averaged" on the part. The fixed line that the recipe is Burro's own |
| A source line can read as official backing. The Open Government Licence gives no right to use information "in a way that suggests any official status" or endorsement | "Burro's recipe. Made from data published by: ...". Publishers are named on the parts, never on the position |
| Vibes are composites, and PLAN section 15 rules out a composite liveability score | No overall score. Published recipes. A band, not a verdict. A critic may not accept the distinction |
| A person who starts from their own area and asks for five more like it may be walked through areas that match who lives round them | The likeness row of 6.1. Parts held out until it passes. The block is closed until pressed |
| A named place of worship says what faith a person holds | It is chosen through the place search field and not typed into the prompt. A share coarsens it as it does a workplace, and a test says so. The privacy notice says a destination can reveal something about a person. A row in the impact assessment |
| Half the vibes rest on Overture Places, whose London quality is unmeasured | The spike comes first. A gap reads as unknown, never zero |
| App store review may object to any of this | Nothing here can settle it |
| Licence wording in the research was read through a reader that summarises | Nothing here changes the registry. Each page is opened and saved before its source is used |

| # | Open question | Recommended | Who can answer |
|---|---|---|---|
| 1 | Residents: option 1, 2 or 3 | Option 1 at launch. Option 2 when a reading allows | The founder |
| 2 | What may go into "gritty": A to E | B | The founder |
| 3 | May "Gritty" be the name of a vibe or of an end on screen? | No. The word is quoted where the person typed it. If yes: only after residents of those areas accept the word for their own area, and with no lens, strip, table or likeness | The founder |
| 4 | May a scale read a good thing low at one end: fewer venues at the Calm end? | Yes, inside a scale only | The founder |
| 5 | Are "Calm", "Newer", "Houses" and "Works and warehouses" the right names? | Test them in the own-area test | The founder, with residents |
| 6 | May the strip on a card show character nobody asked for? | Yes, for vibes that hold the `strip` flag | The founder |
| 7 | May the town centre, the nearest large park and conservation areas be named in "Go and look"? | Yes, from sources registered for `display`, after the verifier is extended. Never from Overture | The founder |
| 8 | Do broadband, a food shop, a GP and a pharmacy come into v1? PLAN section 4 lists them as out | Show broadband. Rank on the walks | The founder |
| 9 | May services after midnight be shown? PLAN section 4 lists night times as out | Yes, as a line, if the feed holds them | The founder |
| 10 | May a place of worship within a walk, no faith named, be weighed on request? | Yes, near only, after a check of coverage by faith against a list the founder trusts | The founder |
| 11 | May household type be shown before a reading? | The founder's call. See 4.3 | The founder |
| 12 | Who keeps the operator list, and may it say "premium"? | The founder approves each row. The operator's own words only | The founder |
| 13 | The lines of the proxy audit | 0.3, 0.5 and 0.6 | The founder writes the rule. ADR 0006 asks for it before any audit runs |
| 14 | May a consumer service print census tables about residents on an area page, if it never ranks or filters on them? | | A free legal clinic |
| 15 | Does the land use table tell works and warehouses from the rest? What does "Transport (other)" hold? Which LSOA vintage? | | The spike of 3.1. MHCLG |
| 16 | Are London's commons, heaths and forests in OS Open Greenspace, with a way in and a name? | | A check of 20 named sites |
| 17 | Does each town centre boundary carry its class and its name? | | Open the file |
| 18 | The licence questions of 2.3: Active Places under clause 4 of its website terms, parkrun, the Arts Council lists, the GLA canopy map | | Each publisher, in writing |
| 19 | Does gigabit-capable coverage vary across London? Does Places to meet vary within inner London? | | A spike each |
| 20 | How good is Overture in London, and which cuisine and culture categories does the pinned release hold? | | The planned spike of phase 0b |
| 21 | Do people understand the words, the bands and the two-ended slider? | | Five people who moved to London and five who have lived here ten years, on the synthetic city |

## 11. What the two reviews changed

F is the review on fairness and law. L is the review from a person who knows London. Every blocker and major finding is here or in section 12.

| Finding | What changed | Where |
|---|---|---|
| F, L, blockers: "Gritty" is a stand-in for deprivation or the wrong word, "Polished" is a way to avoid areas without saying why, and the recipe would find trading estates | The scale is gone. Works and warehouses is one-way, literal, and built from land use alone. The avoid side is two nuisances. Neither word names anything. The spike runs before screens are built round it | 2.1, 2.6, 3.1, 8 |
| F, blocker: four surfaces publish a league table | Flags that are earned. Route 4 serves no band for a vibe without a lens. The order starts with Homes | 5.1, 5.2 |
| F, blocker: the neutral notice may point to the census | Struck. The notice is the same byte for byte under every option | 4.2, step 10 |
| L, blocker: one mark for many thousands of people | Parts are measured from homes. A mixed area is a range. One line on every vibe | Promise 6, 2.4, 5.3 |
| F: option 2 has a gate the founder can sign alone | The signature is no gate. Every table waits on a reading. The panel is not in the static page and has no London column. The recommendation changed | 4.1 to 4.5 |
| F: the audit cannot carry the weight put on it | A written rule with a drop line, result lists, likeness, the income domain, and the order of work | 6.1 |
| F, L: the panel test tunes to reputation, names real areas in public, and cannot be assembled | Ratings against a rubric. An own-area test. Traps. The file stays private, behind a committed hash. The audit wins | 6.2 |
| F, L: likeness gathers every proxy and counts the walk to a park six times | Parts, each once, by family. Its own audit row. Parts held out. Closed until pressed. A share leaves the anchor out by default | 6.1, 7.1 |
| F: cuisines stand in for ethnic makeup | Shown as food, inside Food and drink. Capped at 20 and behind an audit row. Item 8 no longer claims to answer "who lives here" through places | 2.2, 3, 5.1 |
| F: dates and precision overstate | The span of the parts. Bands, no percentage. "Modelled" and "averaged". The fixed line | Promises 2 and 7, 5.1 |
| F: source lines read as official backing, and one source is hidden | "Burro's recipe. Made from data published by: ...". The deprivation file is named in full | Promise 7, 2.3 |
| L: "quiet" read as "few venues" | Quiet streets is restored, measured from where homes are. "Quiet" no longer moves Pace | 2.2, 2.6 |
| L: Leafy held no tree, and parks may miss the commons | A new recipe. No cemetery or golf course counts. Leafy waits for the land use table. The commons check | 2.2, 2.3 |
| L: share of independents rewards long high roads | A count near homes, the class of the centre, and how compact it is | 2.2, 6.2 |
| L: Pace cannot tell a neighbourhood from an office district | Venues are weighted by homes. A line for lived-in or destination. Traps in the test | 2.2, 2.5, 6.2 |
| L: what a newcomer most needs | A food shop in Everyday on foot. Services after midnight, road against aircraft noise, and which side of the line: each as far as the data allows | 2.2, 2.3, 2.5, 5.3 |
| L: the portrait is as sure of a rebuilt area, and of a closed venue | `built_since` and a hatched mark. Studios from the audited register first. The data date beside every count | 2.3, 5.3 |
| L: the portrait does not say where to go and look | "Go and look": names, a pointer and one walk | 5.3 |
| L: "Newer" is interwar suburb | `homes_post2000` is a part of Built age | 2.2 |
| L: clever, but few would choose by it | Broadband is a line. Places to meet ranks only if it varies. The pub is a kind. The historic park part is gone. The rest of this finding is in section 12 | 2.1, 2.5 |
| The minor findings | Anti-social behaviour is not added. A place of worship is `on_request` in all three places. School results sit beside Family amenities. A named place of worship goes through the search field. The shelf leads with seven words, and the plain figure stands beside each mark | 2.5, 5, 10 |

## 12. Considered and not changed

| Asked for | Why it was not done |
|---|---|
| L: make Culture on the doorstep a count on the portrait and not a vibe | The founder asked for cultural activities by name, and a person can honestly want them within a walk. It stays a vibe, off the first row of the shelf, and ships only if it varies within inner London |
| L: make Places to meet a block and not a vibe | The founder asked for community-building places. It stays a vibe if the spike shows it varies, and is a block if not |
| F: keep Street character on the synthetic city for the founder to judge | A control that cannot ship teaches nothing. What the founder judges is how the word "gritty" is answered. Question 3 lets the founder bring the name back, behind a gate |
| F: photographs of streets in the rubric | No source of street imagery is registered, and Street View is banned. The rubric is words |
| F: refuse "food from all over the world" as it refuses "diverse" | Contract 8.4 already reads a wish about places to eat as an ordinary wish. The vibe has one direction, so nobody can ask for fewer kinds. The part is capped and audited |
| L: print "an area holds about 20,000 people" | A release holds no count of residents (ADR 0010), and every number on screen needs a stored fact. The line is said without the number |
| L: counts for each cuisine, as a table | The reviewer's own second choice, to be decided with option 2. Presence alone at launch |
| F: no flag for any vibe over the review line | Taken at 0.5, not at 0.3. The reviewer expects Homes, Pace and Built age to follow income or age to some degree and still names them as candidates. Across some 25 tables most place measures will pass 0.3 on one. At 0.3 a note must be published. At 0.5 the flags go, and nobody may overrule it |
| F: drop option 2 | It is the founder's decision. It is set out in full, with the gate corrected |

## 13. What was re-read for this document

The three proposals opened no web page. "Tool" means a reader that summarises, so the wording must still be checked in a browser before it goes in the registry. "Read" says that a page was read, and no more. No data file was opened. The first six rows hold the eight pages read for the first draft. The rest were read for this revision. All were read on 2026-09-23.

| Page | How | What it says |
|---|---|---|
| Land use statistics: England 2022, on GOV.UK | Tool, twice | Open Government Licence v3.0 "except where otherwise stated". "As at April 2022". Live tables to LSOA level. Categories include Industry, Offices, Retail, Storage and warehousing, Highways and roads, Transport (other), Utilities, Residential gardens, Forestry and woodland, Rough grassland and Natural land. The department is "considering the best timing and frequency for future editions". The table was not opened |
| Trees Outside Woodland map, Forest Research | Tool | "The TOW map is available under open government licence". Trees of 3 m and canopy of 5 m² or more |
| Active Places, licence page | Read | "licensed under CC BY 4.0" and "Contains Data © Sport England" |
| Ofcom, Connected Nations update, Spring 2026, and "About this data" | Tool, and text pulled by a script | January 2026 snapshot. Open Government Licence. Files for census output areas report gigabit-capable coverage and not full fibre |
| Indices of Deprivation 2025, on GOV.UK | Tool | "File 8: Underlying indicators" is listed. The file was not opened |
| parkrun, home page. Arts Council England, terms | Not read | Nothing was read |
| OS Open Greenspace, function code list | Tool | Ten values: Allotments or Community Growing Spaces, Bowling Green, Cemetery, Religious Grounds, Golf Course, Other Sports Facility, Play Space, Playing Field, Public Park or Garden, Tennis Court. None for a common, heath, woodland or forest |
| Council Tax: stock of properties 2025, on GOV.UK | Tool | Table CTSOP4.1 gives properties by build period for LSOAs, as at 31 March 2025. The bands were not shown. The review's reading, single years from 2009, is unverified here |
| GLA town centre boundaries | Tool | Five types of centre are named. Open Government Licence v3. The page does not say whether a boundary carries its class or its name |
| Food Standards Agency, business types | Not read | The data host was not read, and the help page lists no types. "Retailers - supermarkets/hypermarkets" and "Hotel/bed & breakfast/guest house" are the review's reading, unverified here |
| Open Government Licence v3.0 | Tool | The licence "does not grant you any right to use the Information in a way that suggests any official status or that the Information Provider and/or Licensor endorse you or your use of the Information" |
| Equality Act 2010, section 19A, on legislation.gov.uk | Tool | "Indirect discrimination: same disadvantage". Inserted on 1 January 2024. A person who does not share the characteristic may claim where a rule puts them at substantively the same disadvantage. `people.md` did not read it |
| Digital Markets, Competition and Consumers Act 2024, section 226 | Tool | The words quoted in section 10. The page shows the section in force from 6 April 2025 |
| ONS, "One in eight British households has no garden", 14 May 2020 | Tool | "In England, Black people are nearly four times as likely as White people to have no access to outdoor space at home". It is why outdoor space waits on its audit row |

The fairness review also read a report for the GLA on air pollution and inequality, and the EHRC Code's page on GOV.UK. Neither was re-read here, and nothing in this design rests on a figure from either. No other statement in this document was checked against its source.

