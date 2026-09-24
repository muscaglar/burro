# Vibes, designed from the person

Proposal, 2026-09-23. One of three, each written from a different angle. A fourth reader takes the best of the three. Nothing here is decided or built, and nothing here is legal advice. It rests on the seven reports in [`docs/research/vibes/`](../research/vibes/), on [PLAN](../PLAN.md), on ADRs 0002, 0004, 0006, 0007 and 0010, and on [the contract](contract.md) sections 3, 5 and 7. Every weight in every recipe is a first guess. Nothing was measured for this document, and no file but this one was changed.

Written before the registry held the six entries that rest on a permission in writing, as the founder reports: parkrun's events, the two canopy layers of the Greater London Authority, and the three lists of Arts Council England. Where this document says that one of them is not registered, or that it waits on an answer, [the plan for real data](london-data.md) and the registry stand.

## 0. In short

| Question | Answer |
|---|---|
| What is a vibe | A named, published recipe over measured facts about a place. It gives a position among the areas compared, never a verdict |
| How many | 16, in four families. Three are scales with two named ends. Thirteen have one direction |
| What changes on screen | People meet the words before they search. Results and area pages open with character. Any area can start "more like this" |
| What changes in the engine | A tag may be a scale. A spec may point a scale at either end, and may hold "like this area". `rank()` stays a pure function of a spec and a release |
| Gritty | One end of a scale called Street character, built from streets and buildings. Recorded crime sits beside it, never inside it |
| Who lives there | In no vibe, under any option. The founder chooses between three options for showing census figures (section 5) |
| What can be felt in days | All of it, on the synthetic city (section 8) |

## 1. Two people

| | The newcomer | The mover |
|---|---|---|
| Who | Moves to London in three months. Has never been | Has lived in one corner for ten years. Wants a change |
| Knows | Where work is. A budget. Words from other cities | Their own area well, a few by name, the rest by reputation |
| Says | Adjectives: "leafy", "a bit gritty", "walkable" | Comparisons: "like here but quieter", "more space, still near a good high street" |
| Cannot do | Judge a name. A neighbourhood's name means nothing yet | Trust a tool that gets their own area wrong |
| Needs from a vibe | The meaning of the word, in one sentence, before using it | To see where their own area sits, and agree |
| Says "that is exactly the kind of place I mean" when | The top three results share a character they can read at a glance | The areas offered as "like mine" are ones they would have named |
| Loses trust when | Burro uses a word it cannot stand behind | Their own area sits at the wrong end of a scale |

Two things follow. Words must be taught before they are used (section 6, moment 1). And an area must be usable as a word (section 6, moment 7).

A newcomer often reaches for a place abroad: "like the old port district back home". Burro holds no facts about other cities, and a model may not supply them (ADR 0002). That wish is reported as unmet, and the scales are offered in its place.

## 2. What a vibe is

**For a newcomer.** A vibe is a word for the character of a place, such as leafy or buzzy, that Burro has written down as a recipe. The recipe says what is counted and in what proportion. Burro works it out for every neighbourhood from published data and tells you where a neighbourhood sits among the others. It never says a place "is" anything. Each vibe also says what it cannot see.

**For an engineer.** A vibe is a `Tag` of contract section 3.2 with five more fields: `kind` (`one_way` or `scale`), `low_end` and `high_end` (the two names of a scale), `meaning` (one sentence), `cannot_see` (a list), and `beside` (facts shown with it and never used in it). Its score is still the percentile of `raw` by section 2.4, and it is still null below 60 hundredths of coverage.

| Rule | Why |
|---|---|
| Every ingredient describes a place or its buildings | AGENTS.md rule 8 |
| No ingredient is a crime feature | Contract 3.1, as now |
| A scale holds no nuisance. A one-way vibe may read a nuisance `low` only | A scale can be sought at either end, and nobody seeks a nuisance |
| A vibe has two ingredients or more. A single measure is a feature and is shown as a chip | "Waterside" is one measure with a good name, not a recipe |
| A vibe gives a position: the share of areas strictly beyond, rounded down | Contract 7.3. "Gritty" is a judgement. A position on a published recipe is a fact |
| There is no overall vibe score, and no vibe about safety | PLAN section 15 |
| A vibe ships on real data only after the 40-neighbourhood sanity set passes and each new ingredient has a proxy audit row | PLAN section 8, ADR 0006 |

## 3. The words people use, and what Burro does with each

Four tests, asked of every word before it enters the vocabulary.

| # | Test | Fails when |
|---|---|---|
| 1 | Empty the houses. If everyone moved out tonight and other people moved in, would the word still be true? | The word is about people: "studenty", "posh", "international", "friendly" |
| 2 | Can a person want it without wanting harm to anyone? | The word is a nuisance or a verdict: "rough", "safe", "dodgy" |
| 3 | Can it be said as a position and not a verdict? | The word is praise or blame with nothing behind it: "best", "cool", "up-and-coming" |
| 4 | Is there a measure at neighbourhood scale, with a licence on file? | Street cleanliness, 5G, ratings, prices |

| Word | What people mean | Kind of word | What Burro does |
|---|---|---|---|
| gritty, edgy, raw, industrial | Hard-edged streets: works, arches, main roads, little greenery. Often also "poorer" and "more crime" | Mixed | Reads the place part only: Street character, towards gritty. Never weights crime or anything about residents |
| polished, smart, manicured, well-kept | Conserved, green, low-traffic streets. Often also "wealthy" | Mixed | Street character, towards polished. Says on the recipe that it measures the street, not upkeep or wealth |
| rough round the edges | Unpolished | Mixed | The whole phrase is read as towards gritty, marked assumed. "Rough" alone is a verdict on safety: no edit, and the person is told recorded crime can be turned on |
| leafy, green, tree-lined | Trees and gardens | Place | Leafy |
| villagey | Small centre, old buildings, independent shops | Place | Village feel |
| buzzy, lively, in the thick of it | A lot to do nearby, late | Place | Pace, towards buzzy |
| sleepy, not much going on | Few venues | Place | Pace, towards sleepy. Today this wish has no edit |
| quiet, peaceful | Little noise | Place | Quiet streets. Not the same as sleepy: a quiet street can be near a buzzy one |
| suburban, urban, city feel, more space | Houses and gardens, or flats and density | Place | Built form |
| period, historic, characterful | Old buildings | Place | Historic character |
| by the water | Near a river or canal | Place | The `water_access` measure, as a chip |
| arty, creative | Galleries, studios, independents. Also "artists live here" | Mixed | Creative, marked assumed |
| sporty, active | "People here exercise". Also gyms, pools, courts | Mixed | Places to train, marked assumed: "Read 'sporty' as places to train nearby" |
| family, family-friendly | Schools, play space, nurseries. Also "families live here" | Mixed | "Good for families" reads Family amenities. "Lots of young families" is about people: the neutral notice |
| community feel, neighbourly | Places to meet. Also "people know each other" | Mixed | "Community feel" reads Places to meet, marked assumed. "Friendly neighbours" is about people: no edit |
| walkable, everything on the doorstep | Daily needs on foot | Place | Everyday on foot |
| work from home, fast broadband, fibre | A line that can be ordered | Place | Home working. "Fibre" is read as gigabit-capable, and the chip says so |
| highly rated, best, top | A rating | Judgement | Burro holds no rating. Read as "recognised by a public body", marked assumed, with the scheme named |
| foodie, world food | Many places to eat, many kinds | Place | Food and drink |
| international, diverse, cosmopolitan, multicultural | People from many places | People | No edit. The neutral notice of contract 8.4, the same for everyone |
| studenty | Students live here | People | No edit. The neutral notice. "Near a university" is a place wish and is read |
| posh, working class, hipster, young professionals | A class or a kind of person | People | No edit. The neutral notice |
| up-and-coming, on the up, gentrifying | Change over time, and who is moving in | Change, people | No edit. "Burro has no measure of how an area is changing" |
| safe, dodgy, sketchy | A verdict on safety | Verdict | No edit. Recorded crime is offered by category, off until asked, as now |
| cheap and cheerful, good value | Low cost | Not a vibe | Budget. Burro gives no affordability verdict |
| clean, tidy streets | Street cleanliness | No data | No edit. "Burro has no measure of street cleanliness below borough level" |
| 5G, good signal | Mobile coverage | No data at this scale | No edit. A link to the regulator's own checker |
| cool, trendy, vibrant | Fashion | Judgement | No edit. Nothing measures it |

The list of mixed words that are read as their place part is short, written down in one place, and reviewed as a whole, as `PLAIN` is today. A mixed word is always marked "assumed" and always says how it was read.

One reading here goes further than `grit.md`, which says the reader does not map "rough" onto the scale. If the founder prefers, "rough round the edges" makes no edit either.

## 4. The vibes

### 4.1 The sixteen

| # | Family | Vibe | `tag_id` | Ends | Plain meaning | Founder's item |
|---|---|---|---|---|---|---|
| 1 | Streets and homes | Street character | `street_character` (new) | Polished to Gritty | How hard-edged or how manicured the built streets are | 2 |
| 2 | Streets and homes | Pace | `buzzy` (kept) | Sleepy to Buzzy | How much there is to go out to nearby | 1 |
| 3 | Streets and homes | Built form | `built_form` (new) | Suburban to Urban | Houses with outdoor space, or flats at density | 1 |
| 4 | Streets and homes | Quiet streets | `quiet_residential` | One way | Little transport noise and few late venues | 1 |
| 5 | Streets and homes | Village feel | `village_feel` | One way | A small centre with old buildings and independent shops | 1 |
| 6 | Streets and homes | Historic character | `historic_character` | One way | Old homes and protected streets | 1 |
| 7 | Green | Leafy | `leafy` | One way | Trees over streets and gardens, not only parks | 5 |
| 8 | Green | Parks close by | `parks_close_by` (new) | One way | A park within a walk, a large one not far, and things to do in it | 5 |
| 9 | Things to do | Culture on the doorstep | `culture_nearby` (new) | One way | Many kinds of cultural venue within a walk | 4 |
| 10 | Things to do | Creative | `creative` | One way | Cultural venues and independent places | 4 |
| 11 | Things to do | Food and drink | `foodie` | One way | Many places to eat and drink, many of them independent | 1 |
| 12 | Things to do | Places to train | `places_to_train` (new) | One way | Gyms, pools, courts and pitches open to the public, within a walk | 3 |
| 13 | Everyday life | Places to meet | `places_to_meet` (new) | One way | Many kinds of place you go back to, within a walk | 6 |
| 14 | Everyday life | Family amenities | `family_amenities` | One way | Primary schools, play space and parks nearby | 1 |
| 15 | Everyday life | Everyday on foot | `everyday_on_foot` (new) | One way | A high street, a GP, a pharmacy and a station within a walk | 7 |
| 16 | Everyday life | Home working | `home_working` (new) | One way | A gigabit-capable line can be ordered, and the days are quiet | 7 |

### 4.2 Recipes, data, and whether the data is ready

Ready means: **now**, every ingredient comes from a source the registry approves today; **licence**, an ingredient waits on a reply, a page to be read or a named check; **new source**, an ingredient's source is not in the registry yet. No real data has been ingested for any of them. All sixteen describe a place. None describes residents.

| Vibe | Made of, in hundredths | Sources | Ready |
|---|---|---|---|
| Street character | 30 `land_industrial` high, 25 `road_major_exposure` high, 15 `homes_density` high, 15 `green_cover` low, 15 `conservation_cover` low | Land use table P405 (proposed, gated). OS Open Roads, VOA stock, OS Open Greenspace, conservation areas (approved) | New source |
| Pace | 30 `venue_food_drink`, 30 `venue_evening`, 20 `culture_venues`, 20 `highstreet_access`, all high. Unchanged from `buzzy` | Food hygiene register, Overture Places, town centre boundaries (approved) | Now |
| Built form | 55 `homes_density` high, 45 `homes_flats` high. Later 40, 35, and 25 `private_outdoor_space` | VOA stock (approved). Indices of Deprivation File 8 (approved; needs an allowlist row) | Now |
| Quiet streets | 35 `venue_evening` low, 35 `noise_exposure` low, 15 `venue_food_drink` low, 15 `homes_density` low. Unchanged | Approved | Now |
| Village feel | Unchanged: 30 `venue_independent`, 20 `homes_pre1919`, 20 `conservation_cover`, 15 `highstreet_access`, 15 `park_proximity` low | Approved | Now |
| Historic character | Unchanged: 50 `conservation_cover`, 50 `homes_pre1919`. Later a share for `culture_listed_buildings` | Approved | Now |
| Leafy | Today: 45 `green_cover`, 30 `park_proximity` low, 25 `homes_density` low. Rebuilt: 35 `canopy_cover`, 30 `street_canopy`, 20 `green_cover`, 15 `private_outdoor_space` low | Today's recipe: approved. Rebuilt: Forest Research canopy map (proposed), after its accuracy report and the street spike | Now, then new source |
| Parks close by | 35 `park_proximity` low, 25 `park_large_proximity` low, 25 `park_facilities` high, 15 `historic_park_proximity` low | OS Open Greenspace (approved). Registered parks and gardens (proposed) | Now |
| Culture on the doorstep | 50 `culture_kinds_nearby`, 30 `culture_venues`, 20 `library_proximity` low. Recognition sits beside it at first | Overture Places (approved, London quality unmeasured). Libraries list (unread, gated). Recognition lists (unread) | Now for kinds. Licence for recognition |
| Creative | Unchanged: 60 `culture_venues`, 40 `venue_independent`. Later studios and workspaces | Approved. Studio layers wait on the GLA's reply | Now |
| Food and drink | Unchanged: 60 `venue_food_drink`, 40 `venue_independent`. Later a share for `cuisine_variety` | Approved. Cuisine needs the Overture category list read | Now |
| Places to train | 35 `gym_choice`, 25 `pool_proximity` low, 20 `court_pitch_kinds`, 20 `park_proximity` low | Active Places (licence read, not yet registered). OS Open Greenspace (approved) | New source |
| Places to meet | 40 `meeting_place_kinds`, 20 `library_proximity` low, 20 `sports_facility_nearby`, 10 `play_space_proximity` low, 10 `highstreet_access` | Allotments, children's centres, play space, high streets (approved). Libraries and Active Places (above). parkrun (held: written permission only) | Licence |
| Family amenities | Unchanged. Later a share for `nursery_nearby` | Approved. Nurseries gated | Now |
| Everyday on foot | 30 `highstreet_access`, 25 `gp_walk` low, 25 `pharmacy_walk` low, 20 `station_walk` low | Approved, but `nhs-ods` lacks the `scoring` use. Pharmacy list gated | Licence |
| Home working | 50 `broadband_gigabit`, 30 `noise_exposure` low, 20 `park_proximity` low | Ofcom output area files (OGL v3; today's entry is held on scope). Ships only if the figure varies across London | New source |

Three things in these recipes depart from the research, on purpose.

| Departure | Reason |
|---|---|
| Street character leaves out `noise_exposure`, which the draft in `grit.md` holds | The contract lists noise as a nuisance. `grit.md` itself says nothing on a scale may be a nuisance. With noise inside, seeking the gritty end would rank up noise. Main roads stay in, as built form. If the founder counts a main road as a nuisance, it leaves too |
| A scale sought at one end counts less of a good thing: less green cover at the gritty end, fewer venues at the sleepy end | Today no tag reads a feature against its polarity, and the reader treats "less of a good thing" as a wish no edit can express. A scale needs it. The founder should see this and agree (section 9) |
| Gym tiers, recognition and street incidents are beside a vibe and not inside one | Each follows income or is a crime figure. See 4.5 |

### 4.3 What each cannot see

| Vibe | What it cannot see. Shown on the recipe card, word for word |
|---|---|
| Street character | Whether streets are clean. Empty shops. Graffiti. Whether an area is run down or changing. Recorded crime. Who lives there. It measures hard-edged, not run-down |
| Pace | Opening hours. How busy a place is. What is on. Noise from venues. Whether any of it is good |
| Built form | The size of a home inside. Balconies. Buildings finished after the data. Who lives in them |
| Quiet streets | Noise from neighbours, venues, industry and building works. The noise figure is modelled road, rail and aircraft noise for 2021 |
| Village feel | Which shops there are. Empty units. Whether anyone knows your name |
| Historic character | The condition of a building. An area the conservation data does not cover is unknown, not zero |
| Leafy | One street or one home. Trees under 3 m. Species. The canopy map spans 2017 to 2024 |
| Parks close by | Upkeep, quality, opening hours. Whether a registered garden is open to the public |
| Culture on the doorstep | Ratings. What is on. Prices and hours. Whether a venue is still open. Recognition is not quality |
| Creative | Artists' homes. Studios, until the layers are cleared. Anything not on a register |
| Food and drink | Quality and price. Cuisine, until the category list is read. Hygiene ratings are never shown |
| Places to train | Price, quality, crowding, hours. Gyms under 5 stations. Climbing walls and boxing gyms are weakly covered |
| Places to meet | Whether people are friendly. Whether a group has room or still meets. parkrun, until permission is in writing |
| Family amenities | Catchments, school places, the cost of childcare. Who lives there |
| Everyday on foot | Whether a surgery is taking patients. Opening hours. Step-free access at stations other operators run |
| Home working | The speed a home gets. Price. Full fibre. 5G. Indoor signal. It says where a line can be ordered |

### 4.4 Sentences that should call each one up

| Vibe | Five sentences |
|---|---|
| Street character | "somewhere a bit gritty" · "old warehouses and railway arches" · "edgy and industrial" · "smart, well-kept streets" · "nothing too manicured" |
| Pace | "lively, lots going on in the evening" · "somewhere sleepy" · "a buzzy high street with bars" · "I want to be in the thick of it" · "not too buzzy" |
| Built form | "a proper city feel, flats are fine" · "more suburban, houses with gardens" · "we want more space" · "low-rise terraced streets" · "dense and urban" |
| Quiet streets | "a quiet residential street" · "peaceful at night" · "away from traffic noise" · "no bars under my window" · "calm and residential" |
| Village feel | "villagey" · "feels like a village" · "a little high street with a bakery" · "a small-town feel" · "independent shops round a green" |
| Historic character | "period houses" · "old streets with character" · "somewhere historic" · "terraces from before the war" · "a conservation area" |
| Leafy | "leafy" · "tree-lined streets" · "green, with gardens" · "lots of trees" · "I want to see green from the window" |
| Parks close by | "near a big park" · "somewhere I can run in a park" · "a park with tennis courts and a playground" · "green space within a walk" · "close to a common" |
| Culture on the doorstep | "theatres and galleries nearby" · "near good museums" · "a cinema and a library" · "highly rated cultural venues" · "culture on my doorstep" |
| Creative | "arty" · "studios and galleries" · "a creative scene" · "artsy and independent" · "independent shops and galleries" |
| Food and drink | "a great food scene" · "lots of restaurants and cafes" · "good coffee and brunch" · "independent restaurants, not chains" · "food from all over the world" |
| Places to train | "sporty" · "a gym and a pool within walking distance" · "a cheap gym nearby" · "yoga and pilates studios" · "tennis courts and a leisure centre" |
| Places to meet | "a community feel" · "I want to meet people locally" · "a parkrun nearby" · "a library, an allotment, clubs to join" · "things to join at the weekend" |
| Family amenities | "good for families" · "good primary schools and playgrounds" · "family-friendly" · "nurseries and parks for the kids" · "somewhere to bring up children" |
| Everyday on foot | "walkable" · "everything on my doorstep" · "a GP, a pharmacy and shops within a walk" · "I do not want to need a car" · "a 15-minute neighbourhood" |
| Home working | "I work from home" · "fast broadband" · "fibre to the home" · "good for remote working" · "good internet and a quiet place to work" |

Some of these hold words the rule-based reader does not know today. Each is a golden query first and a vocabulary change second.

### 4.5 What sits beside a vibe, and never inside it

| Beside | What is shown | Why it stays outside |
|---|---|---|
| Street character | Street incidents: recorded criminal damage and anti-social behaviour, by category, closed until the person opens them, with the crime caveat | Crime is weighted only on request. Recorded criminal damage moves with recorded violence with injury at 0.81 across London's LSOAs (`grit.md`) |
| Places to train | Kinds of gym nearby: council leisure centre, chain gym, independent, class studio, gym with a pool. "Low-cost" only for operators whose own words say so | The mix of gyms follows income. A low-cost gym may be asked for, near only, off by default |
| Culture on the doorstep | Recognised venues, each with its scheme and date: accredited museum, national museum, listed building | Recognition follows age and money. It may enter a recipe later, under 60 hundredths, after its audit row |
| Home working, Everyday on foot | A Borough block: council tax, full fibre, outdoor 5G, each naming the borough. A link to the regulator's checker for one address | A borough figure is not a neighbourhood's. It is never scored |
| Places to meet | A place of worship within a walk, no faith named, as one kind of meeting place | By faith is a founder decision (`community.md`, decision 1) |

## 5. The founder's items 2 and 8

Both press on AGENTS.md rule 8. This section sets out the choices. It does not make them.

### 5.1 Item 2: what may go into "gritty"

| Choice | What goes in | Allows | Risks | Must change |
|---|---|---|---|---|
| A | Place only | A scale sought at either end | It will still follow deprivation. Needs a proxy audit row | Nothing |
| B | A, with street incidents beside it | Crime and the nearest thing to cleanliness, each where it belongs | Two controls where one word was asked for | Nothing |
| C | Street incidents inside | One number | Asking for gritty ranks up recorded crime. A composite that includes crime | ADR 0006, contract 3.1 and 3.2, PLAN 9 and 15 |
| D | Deprivation inside | The everyday sense of the word | It ranks residents. Inputs include asylum support, disability benefits and English language ability | Rule 8, ADR 0006, PLAN 9 and 15. Legal advice |
| E | Deprivation shown, never ranked | A familiar figure | It describes residents to a person choosing where to live | PLAN 15 |

Recommended: **B**. This document is written for B. Under A, drop the first row of 4.5. Under C, D or E, stop and amend ADR 0006 first.

### 5.2 Item 8: who lives there

| | Option 1. Places only | Option 2. Show, never rank | Option 3. Residents in ranking or vibes |
|---|---|---|---|
| A person can | Ask for cuisines, shops, venues. Name a place of worship or a community centre as a place to reach | All of 1, and read official census figures on the area page | All of 2, and search or sort by who lives there |
| Answers item 8 | "Cultural background and vibe": from places. "Local makeup": no | Both | Both, as a search |
| Risk, as `people.md` reads it | Least. Proxy effects remain | Low, and mostly in the wording. Unreviewed | High. Segregation, indirect discrimination and stereotype are all in play |
| Must change | Nothing | ADR 0006, PLAN 15, the registry's audit rule, a `residents` dimension, a code fence with a test | All of 2, and rule 8, and the neutral notice. Paid advice first, which ADR 0007 rules out |

| If the founder chooses | This design does |
|---|---|
| Option 1 | Adds a "Culture and community" block to the portrait: kinds of cuisine in alphabetical order, community venues, a place of worship within a walk. Ends with "Burro counts places. It does not describe the people who live here." Links to the statistics office's own pages. Lets a place of worship or community centre be named as a destination |
| Option 2 | All of Option 1. Adds a census panel, last on the area page and outside the portrait, headed "Census 2021: who lived here". Step 1 at launch: age bands, household type, students. Step 2: country of birth, ethnic group, religion, closed by default, after a free legal clinic has read it or the founder accepts the risk in writing. A table, never a sentence. No "main group", no "higher than average", no colour. Never in a result, a vibe, a comparison, the map, "more like this", a share, or anything sent to a model |
| Option 3 | Nothing until ADR 0006 is replaced and advice is on file. Even then, no vibe is built from residents: a named vibe built on who lives somewhere is a stereotype written as arithmetic. The most this design could take is one explicit, opt-in filter on age band or household type, never on race or religion, and never in "more like this" |

Recommended, following `people.md`: **Option 2 in two steps. Never Option 3 without paid advice. Vibes come from places under every option.** If nothing is decided, ADR 0006 stands as written and this design runs as Option 1.

## 6. The experience, moment by moment

| # | Moment | What the person sees | What they can do | When a vibe cannot be measured |
|---|---|---|---|---|
| 1 | Before a search | Under the prompt box, "Words Burro understands": the 16 vibes in four families. A scale is drawn as a line with its two ends named. A page, `/vibes`, holds every recipe and reads with scripts off | Open a vibe to read its meaning, recipe and what it cannot see. Colour the map by one vibe. "Add to my search", which is an edit and needs no model | A vibe the release does not carry is greyed: "Not in this data yet. Waits on a licence reply." Words Burro will never measure are listed with the reason |
| 2 | In the prompt | The box. Examples that use vibe words and hold no proper noun. Nothing is read until Search is pressed | Type in their own words. Mix vibes with places and a budget. Name an area: "like Alderwick, but nearer Pellam Cross" | |
| 3 | What Burro understood | A chip for each vibe read. A scale reads "Street character: towards gritty". The words each chip rests on are marked in the box, from `rests_on`. A mixed word is marked "assumed" and says how it was read | Remove a chip. Flip a scale to its other end. Change how much it counts. Open the recipe | One line for each thing not read, by category: "Burro has no measure of how an area is changing." For a word about people, the neutral notice, the same for everyone |
| 4 | In a result | Under the name: the three scales as dots on lines, then up to two vibes the area stands out for. Then reasons and the trade-off, as now. A vibe can be either | Press a dot for its sentence and source. "More like this". Add to compare | "There is no Places to train figure for Otterby Fields in this release, so it was left out of the score." The completeness line counts it |
| 5 | Area page, as a portrait | Character first. The three scales. "Stands out for" and "Has less of". "Cannot say". Each vibe opens to its ingredients, each with figure, standing, source and date. Then what sits beside each (4.5). Then what Burro does not know, in fixed lines | Open an ingredient. Open street incidents. "More like this". "Search for this character" | "Cannot say" names each unknown vibe and why: "2 of its 5 ingredients have a figure here" |
| 6 | Comparison | Character rows first. Each scale is one line with every area's dot on it. Then the vibes that count in the search, by weight. Then the vibes where these areas differ most | Open any cell's source. Remove an area | A cell reads "No figure in this data". A gap never reads as a zero. The census panel never appears here |
| 7 | More like this | A chip, "Like Alderwick". Results ranked on likeness with journeys and budget. Each card says "Alike in: pace, leafy. Differs in: street character, further towards gritty" | Choose which vibes to match on. Change how much it counts. Add "but quieter" | "Too few of Alderwick's vibes are known to match on." |

Rules for this section.

| Rule | Detail |
|---|---|
| A portrait is a list of facts, not prose | One line, one fact, one source. No sentence is composed from several facts, so the verifier stays as it is |
| A dot is a band, not a percentile | Five bands, worked out in core from the share strictly beyond, and held in the fact's slots. The website draws what it is given |
| A scale's sentence names the end | "Street character: further towards gritty than 80% of the 450 areas compared in this release." No sentence says a place is gritty |
| Character nobody asked for is shown, not scored | The strip on a card shows where an area sits. Only what is in the spec counts towards the fit |
| The notice for a word about people is not tailored | It offers the vocabulary page, the same for everyone. It never suggests "near a university" because "studenty" was typed. Tailoring would say which group was heard |
| Street incidents never appear unasked | Not in the strip, not under "Stands out for", not in likeness |

## 7. How the engine changes

### 7.1 What becomes of the 23 features and the 12 tags

All 23 features stay, with their ids. All 12 tag ids stay valid, so no old spec or share breaks.

| Tag today | Becomes |
|---|---|
| `buzzy` | The Pace scale. Same recipe. Gains `kind: scale` and the low end "Sleepy" |
| `leafy` | Kept. Recipe rebuilt when canopy is in a release. Bumps `CATALOGUE_VERSION` |
| `village_feel`, `historic_character`, `quiet_residential`, `creative`, `foodie`, `family_amenities` | Kept as they are. Six of the sixteen |
| `waterside`, `evening_venues`, `near_universities` | Kept in the engine. Shown as single measures, not vibes: each is one feature at 100 hundredths |
| `strong_high_street` | Kept in the engine and still read from words. Shown under Everyday on foot, which it overlaps |

| New features, by when | Ids |
|---|---|
| From sources approved today | `park_large_proximity`, `park_facilities`, `road_major_exposure`, `growing_space_proximity`, `childrens_centre_proximity`, `private_outdoor_space`, `culture_listed_buildings` |
| Crime rules apply: weight 0 by default, in no vibe, on explicit request only | `incident_criminal_damage`, `incident_asb` |
| After a gate or a registration | `land_industrial`, `canopy_cover`, `street_canopy`, `gym_choice`, `pool_proximity`, `court_pitch_kinds`, `culture_kinds_nearby`, `library_proximity`, `meeting_place_kinds`, `sports_facility_nearby`, `gp_walk`, `pharmacy_walk`, `broadband_gigabit`, `cuisine_variety`, `historic_park_proximity` |
| One direction, off by default, never in a vibe | `lowcost_gym_proximity` |

A feature id may be in core before any real release carries it (contract 2.3). That is what lets the synthetic city hold all sixteen vibes now.

### 7.2 A recipe as data

```json
{
  "tag_id": "street_character",
  "label": "Street character",
  "family": "streets_and_homes",
  "kind": "scale",
  "low_end": "Polished",
  "high_end": "Gritty",
  "meaning": "How hard-edged or how manicured the built streets are.",
  "terms": [
    {"feature_id": "land_industrial", "hundredths": 30, "reading": "high"},
    {"feature_id": "road_major_exposure", "hundredths": 25, "reading": "high"},
    {"feature_id": "homes_density", "hundredths": 15, "reading": "high"},
    {"feature_id": "green_cover", "hundredths": 15, "reading": "low"},
    {"feature_id": "conservation_cover", "hundredths": 15, "reading": "low"}
  ],
  "cannot_see": ["Whether streets are clean", "Recorded crime", "Who lives there"],
  "beside": ["incident_criminal_damage", "incident_asb"]
}
```

Recipes stay in core, as `TAGS` is today, and are served by route 11. They are not loaded from a file at run time: core does no IO.

| Test on every recipe | Protects |
|---|---|
| Hundredths sum to 100 | As now |
| No term is in the crime dimension | As now, widened from two ids to the dimension |
| No term of a scale is in `NUISANCES`. A nuisance in a one-way vibe is read `low` | Nobody seeks a nuisance |
| `conservation_cover`, recognition and `private_outdoor_space` each carry under 60 hundredths | None can decide a vibe alone |
| Every vibe has a `meaning` and at least one `cannot_see` line, and none holds a banned word | The vocabulary page is never empty of limits |
| No two vibes in a release correlate above a set bar | Sixteen words must not be one axis said sixteen ways (section 10) |

### 7.3 How a two-ended scale is ranked

| Step | Rule |
|---|---|
| Score | The percentile of `raw`, as for any tag. High is the `high_end` |
| In the spec | `TagWeight` gains `toward`: `high` or `low`. `low` is allowed only where `kind` is `scale`. Otherwise `check_spec` answers `direction_not_allowed` |
| Utility | `score / 100` towards high. `1 - score / 100` towards low |
| Default | No weight. A scale counts only when a person points it |
| From a word | "gritty" is a `nudge` of `up_large` with `toward: high`. "polished" the same with `toward: low`. A mention is worth 0.50, as now |
| From a control | One slider with two named ends. It rests in the middle, which is weight 0. Moving it towards an end sets `toward` and raises the weight |
| A turned wish | "Not buzzy" becomes Pace towards sleepy. Today it is a `remove` and an unmet wish. For a one-way vibe nothing changes |
| Sentence | Said from the side the area is on, naming that end |

### 7.4 How "like this area" is computed

| Step | Rule |
|---|---|
| In the spec | A new field, `likes`: at most 2, each an `area_id`, a `weight`, the `vibes` to match on, and a provenance |
| Component | `like:<area_id>`, beside `commute`, `budget`, `feature:` and `tag:` |
| Utility | The mean, over the chosen vibes that both areas have a score for, of `1 - abs(score - reference) / 100` |
| Default vibes | Every vibe in the release. Never a crime feature, a nuisance, cost or a journey |
| Missing | The component is missing when fewer than 60% of the chosen vibes are known for either area |
| The reference area | Stays in the results, marked "the area you named" |
| Showing the working | A `likeness` fact for each result: the vibes in the same band, and the vibes that differ, each with its end |
| Purity | It reads the spec and the release and nothing else. The same spec and release give the same order |
| Privacy | An area named as "like" may be where someone lives. It is never logged, as no part of a spec is. A share stores it, as it stores an `only` rule today |

### 7.5 How "gritty" fits the rule that crime is weighted only on request

| Case | What happens |
|---|---|
| "gritty" is typed | Street character towards gritty. No crime feature is touched. Rule 8 of the reducer would reject an inferred crime edit in any case |
| "gritty but low crime" | Two chips. The scale towards gritty, and recorded crime weighted less, because crime was named |
| "polished" or "smart" is typed | Street character towards polished. It is not read as a wish for low crime |
| "rough", "dodgy", "safe" | No edit. The person is told recorded crime can be turned on |
| The area page | Street incidents sit in a closed block under Street character, by category, with the caveat of contract 7.3 |
| "More like this" | Never matches on crime or a nuisance |
| Proxy | Street character will still follow recorded crime and deprivation. It gets a proxy audit row before it ships: the aim, the threshold, and what is done if it is crossed |

### 7.6 What must change in the contract

| Section | Change |
|---|---|
| 3.1 | New feature rows. `road_major_exposure` and `land_industrial` have polarity `either`. The incident features join the crime rules |
| 3.2 | `Tag` gains `kind`, `low_end`, `high_end`, `family`, `meaning`, `cannot_see`, `beside`. New recipes. The tests of 7.2 |
| 4 | `TagWeight.toward`. `likes`. `schema_version` 2: a version 1 spec is read as `toward: high` with no likes |
| 4.2 | `canonical()` writes `toward` and `likes`. New test vectors |
| 5.1, 5.3 | `TagEdit.toward` (`high`, `low`, `default`). A seventh array, `like_ops`. Rules: `low` only on a scale, a like names a rankable area, at most 2 likes |
| 6.2 | The utility of a tag by `toward`. The `like:` component |
| 7.1 to 7.3 | Fact kinds `likeness` and `borough`. A `band` slot on tag facts. Templates `scale`, `likeness`, `vibe_unknown` and `borough` |
| 7.4 | Banned in any sentence: "best", "top", "highly rated", "friendly", "up-and-coming" and their forms. "Gritty", "polished", "sleepy" pass only as the end named by the `scale` template |
| 8.1, 8.2 | New words in `LEXICON`. The list of mixed words. New `UnmetCategory` values: `change_over_time`, `ratings`, `street_cleanliness`, `mobile_coverage`, `another_city` |
| 9.2 | Route 6 gains `portrait`. A new cached route serves one vibe's band for every area, for the map. Route 11 serves the new tag fields |
| Versions | `CATALOGUE_VERSION` and `ENGINE_VERSION` both move. A new ADR records that a vibe is a position on a published recipe |

## 8. What to build first, on the synthetic city

Nothing here needs a licence, a download or a model. Every figure is made up and says so.

| Step | Days | What | The founder can then |
|---|---|---|---|
| 1 | 1 | Make `buzzy` a scale: `kind`, the two ends, `toward`, the utility, the `scale` template, the two-ended slider. No new data | Drag Pace towards sleepy and watch Marrowfen and Gorsebeck rise and Lantern Yard and Pellam Cross fall |
| 2 | 1 | `meaning` and `cannot_see` for the 12 tags. The vocabulary strip under the prompt box and the `/vibes` page | Read every recipe before searching |
| 3 | 1 to 2 | The portrait: character first on the area page, the strip on a result card, "Cannot say" | Open Otterby Fields, where nine tags are unknown, and see what Burro says |
| 4 | 1 to 2 | Street character: two made-up features in the generator, with the character of each area set by hand. The two incident features under the crime rules. The words "gritty", "edgy", "polished", "smart" | Type "a bit gritty" and see one chip and no crime weight. Open street incidents on a page |
| 5 | 2 | "More like this": `likes`, the component, the chip, the `likeness` fact | Type "like Alderwick, but nearer Pellam Cross" |
| 6 | 1 | Colour the map by one vibe, before any search | Explore the city by character with nothing typed |
| 7 | 2 | The other new vibes on made-up features, each with a badge that says what real source it waits on | Feel all sixteen, and see at a glance which ones London can carry at launch |

Two cautions. The synthetic city will feel richer than London can at launch, so step 7's badges must show on the synthetic city too. And nothing seen on it says whether a recipe matches what people mean: only the 40-neighbourhood sanity set on real data can.

PLAN phase 0b already asks for a test with five people who moved to London. Add five who have lived here ten years. On synthetic data, test only whether the words are understood and the controls make sense.

## 9. What the founder must decide

Work proceeds on the recommendation unless the founder says otherwise. The first four touch a rule and are the founder's alone.

| # | Decision | Choices | Recommended |
|---|---|---|---|
| 1 | What may go into "gritty" | A to E, section 5.1 | B |
| 2 | Who lives there | Options 1 to 3, section 5.2 | Option 2 in two steps. Option 1 stands until decided |
| 3 | May a scale count less of a good thing at one end | Yes, inside a scale only. Or build scales from `either` features alone | Yes. Without it neither the gritty end nor the sleepy end has enough to stand on |
| 4 | The notice for a word about people | Untailored, as now. Or tailored offers | Untailored |
| 5 | May a sentence name an end of a scale | Yes, in the `scale` template only. Or only "above" and "below" | Yes. "Above 80% of areas" tells a newcomer nothing |
| 6 | The names of the ends | "Polished to Gritty", "Sleepy to Buzzy", "Suburban to Urban". Or plainer words | As written. Test them on people who live at each end |
| 7 | Character nobody asked for, on a result card | Show the strip. Or show only what counts in the search | Show it, without street incidents. It is how a newcomer learns the words |
| 8 | Names on the portrait | Counts only. Public institutions and parks from sources registered for display. Any venue | Public institutions, parks and gym operators from their official registers. Never from Overture |
| 9 | Broadband, GP and pharmacy in v1 | Keep out, as PLAN section 4 says. Show. Show and rank | Show. Rank on the two walks. Rank on broadband only if it varies across London |
| 10 | "Like this area" in a share | Store the area. Or drop it from the share | Store it. It is a neighbourhood, not an address. Say so in the privacy notice |

## 10. Risks

| Risk | What this design does about it |
|---|---|
| Sixteen vibes may be one axis: near the centre or far from it. Air quality, travel time and lack of outdoor space move together at 0.75 to 0.84 across London's LSOAs (`grit.md`) | Measure the correlation between vibes on the first real release. Merge or drop any pair above the bar |
| Venue density is an ingredient of four vibes, so likeness leans on it | The person chooses which vibes to match on. Matching on features, each counted once, is the fallback |
| Street character follows deprivation and recorded crime, and could be read as a map of poverty | Place-only ingredients. No nuisance. A proxy audit row first. A position, never a verdict. Street incidents closed by default |
| The name of an end offends people who live there | No sentence says a place is gritty or sleepy. Test the names. Plainer names are one line to change |
| Recipes are guesses, and the sanity set is opinion | Publish every recipe. Let a person see and change what counts. Say what each vibe cannot see |
| The synthetic city promises more than launch can deliver | Badges on every vibe that waits on a source, on the synthetic city too |
| Many vibes wait on letters and unread pages | Eleven of sixteen rest on sources the registry approves today. The rest are greyed, with the reason |
| Every licence quotation in the research was read through a reader that summarises | Nothing here changes the registry. Each page is opened and saved before its source is used |
| A mixed word is read wrongly as its place part | The list is short and reviewed whole. Every such reading is marked "assumed" and says how it was read |
| Overture's London quality is unmeasured | Culture, studios and cuisine ship only after the quality spike. A gap is unknown, never zero |
| Vibes are composites, and PLAN section 15 rules out a composite liveability score | No overall score. Every vibe has a published recipe, named ingredients and a list of limits |
| No professional has read any of this | ADR 0007 stands. Where a choice needs advice, this design does not take it |
