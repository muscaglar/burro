# Vibes at the centre of Burro: the proposal from difference

Status: a proposal, written 2026-09-23. It is one of three, each from a different angle, and a fourth person will merge them. Nothing here is built and nothing here is decided. It is not legal advice, and no lawyer has read it.

It rests on the seven reports in [`docs/research/vibes/`](../research/vibes/). Where this document states a licence, a figure or what a publisher says, it is repeating one of those reports, and the limits of that report apply: most pages were read through a reader that summarises, and no data file from an unregistered source was opened. Every example uses the made-up city. No sentence here describes a real place.

Written before the registry held the six entries that rest on a permission in writing, as the founder reports: parkrun's events, the two canopy layers of the Greater London Authority, and the three lists of Arts Council England. Where this document says that one of them is not registered, or that it waits on an answer, [the plan for real data](london-data.md) and the registry stand.

The angle: what can Burro do that a property portal or a postcode statistics page cannot? A portal starts from a home. A statistics page starts from a postcode you already have. Burro can start from a feeling, show where in the city it is found, let a person turn it, and move from one area to the areas like it.

## 0. In short

| Idea | What the person gets | What makes it honest |
|---|---|---|
| A vibe is a published recipe | A word such as "leafy", with its ingredients one tap away | Every ingredient is a measured fact about a place, with a source and a date |
| Some vibes are dials | Two named ends, both of which can be asked for: Calm or Buzzy, Polished or Gritty | A dial holds tastes only. Nothing on it is a nuisance, a crime figure or a fact about residents |
| The lens | Before any search, the map coloured by one vibe | It is the release's own figures. No search is made, and nothing a person typed is sent |
| The portrait | An area page that opens with the area's character, not its statistics | It is worked out from the release alone, so it is the same for every visitor |
| Places like this one | "More like this", and "like this but quieter and cheaper" | Likeness is distance between portraits. The model never says what a place is like |
| What Burro cannot see | A fixed line under every vibe | It is written with the recipe, and a test holds it on the page |

| | A property portal | A postcode statistics page | Burro with vibes |
|---|---|---|---|
| Starts from | A home for sale or to let | A postcode the person already has | A feeling, or an area the person already knows |
| Unit | A listing | A postcode or a census area | A named neighbourhood |
| Says | What the home is | Figures, one table at a time | Where the area sits on each vibe, what that is made of, and what cannot be seen |
| Moves by | Filters on homes | Typing another postcode | Turning a dial, or stepping to a place like this one |

## 1. What a vibe is

A vibe is a named recipe that turns measured facts about a place into one position among the areas of the city. "Leafy" is a recipe: so much tree canopy, so much public green space, so much garden. Each ingredient is a feature of the catalogue, with a weight in hundredths that add up to 100. The pipeline works out each area's raw score, and the area's position is the percentile of that score among the areas that could be placed. An area with less than 60 hundredths of a recipe's ingredients is not placed at all. A vibe comes in two shapes. A **dial** has two named ends and a person may ask for either, or for the middle. A **one-ended vibe** has one name and a person may only ask for more of it. Every vibe carries its recipe, the facts shown beside it, the words that call it up, and a list of what it cannot see. A vibe never describes who lives somewhere, never includes recorded crime, and is never written by a model.

| Part | What it is | Engineer's name |
|---|---|---|
| Name and ends | "Street character", with "Polished" and "Gritty" | `label`, `ends` |
| Recipe | Features, each read high or low, in hundredths | `terms`, as `TagTerm` today |
| Position | Percentile of the raw score, drawn in five bands and never printed as a number | `score`, as today |
| Stop | Where the person wants to be: one of five stops along a dial | `target`, new |
| Weight | How much it counts, 0 to 1 | `weight`, as today |
| Beside it | Facts shown with the vibe and never scored in it: kinds of gym, recorded incidents, a borough figure | `beside`, new |
| Cannot see | Fixed lines, such as "Burro cannot tell whether a gym is good" | `cannot_see`, new |

In code and on the wire a vibe stays a `tag`. "Vibe" is the word on the screen.

## 2. The vibes

Fifteen vibes in five families, and one thing the founder asked for that is not a vibe. Weights are first guesses. A vibe ships only when it passes the 40-neighbourhood sanity set, which for a dial must hold places at both ends.

### 2.1 The set

| # | Family | Vibe | Shape | Low end, high end | Describes | Founder's item | Data |
|---|---|---|---|---|---|---|---|
| 1 | Streets and buildings | Street character | Dial | Polished, Gritty | Place | 2 | Needs a new source: the land use table |
| 2 | Streets and buildings | Built age | Dial | Modern, Period | Buildings | | Now |
| 3 | Streets and buildings | Homes | Dial | Houses and gardens, Flats close together | Buildings | | Now |
| 4 | Pace and food | Pace | Dial | Calm, Buzzy | Place | 1 | Now |
| 5 | Pace and food | Food variety | One end | | Place | 8, in part | Now, once the category list is read |
| 6 | Pace and food | Village feel | One end | | Place | 1 | Now |
| 7 | Green and water | Leafy | One end | | Place | 5 | Needs a new source: the canopy map |
| 8 | Green and water | Parks close by | One end | | Place | 5 | Now |
| 9 | Green and water | Waterside | One end | | Place | | Now |
| 10 | Things to do and join | Culture | One end | | Place | 4 | Counts now. Standing after a licence answer |
| 11 | Things to do and join | Places to train | One end | | Place | 3 | Needs a new source: Active Places |
| 12 | Things to do and join | Places to meet | One end | | Place | 6 | Part now. Libraries and parkrun after an answer |
| 13 | Daily life | Family amenities | One end | | Place | | Now |
| 14 | Daily life | Everyday on foot | One end | | Place | 7 | Needs a source widened and one gated |
| 15 | Daily life | Home working | One end | | Place | 7 | Needs a new source. Ranked only if London varies |
| 16 | | Local makeup | Not a vibe | | Residents | 8 | Cannot be a vibe honestly. See 2.5 |

"Now" means every source is approved in the registry today. It does not mean measured: the quality of Overture Places in London is still an open spike, and half of these rest on it.

### 2.2 Recipes and data

`high` reads a feature's percentile as it is, `low` reads it turned round. New features are in italics. Status is the registry's, or the status the research proposes.

| Vibe | Recipe, in hundredths | Sources, and what each waits on |
|---|---|---|
| Street character | 45 *`land_industrial`* high + 20 *`road_major_exposure`* high + 15 `homes_density` high + 10 `green_cover` low + 10 `conservation_cover` low | MHCLG land use 2022, proposed gated: open table P405 first. OS Open Roads, approved. Without the land use table only 55 hundredths are present, so the dial is not placed. That is on purpose: without industry it would measure "urban", not "gritty" |
| Built age | 50 `homes_pre1919` high + 30 `conservation_cover` high + 20 *`listed_building_density`* high | All approved. It also meets the registry's condition that conservation areas are combined with listed buildings |
| Homes | 40 `homes_flats` high + 35 `homes_density` high + 25 *`private_outdoor_space`* shortfall high | VOA stock, approved. Outdoor space is in the approved Indices of Deprivation File 8. It needs a catalogue row and a proxy audit row, and is never shown under the word "deprivation" |
| Pace | 35 `venue_evening` high + 30 `venue_food_drink` high + 20 `highstreet_access` high + 15 `culture_venues` high | All approved |
| Food variety | 40 *`cuisine_variety`* high + 35 `venue_food_drink` high + 25 `venue_independent` high | Overture Places, approved. Its cuisine categories have not been read in full. The food hygiene register has no cuisine field. Without cuisines it still runs, on the two ingredients of today's "foodie" |
| Village feel | As today | All approved |
| Leafy | 35 *`canopy_cover`* high + 30 *`street_canopy`* high + 20 `green_cover` high + 15 *`private_outdoor_space`* shortfall low | Forest Research Trees Outside Woodland, OGL v3, proposed approved. Street canopy is unproven until the 20-street spike. Until then, today's recipe |
| Parks close by | 35 `park_proximity` low + 25 *`park_large_proximity`* low + 25 *`park_facilities`* high + 15 *`historic_park_proximity`* low | OS Open Greenspace, approved. Registered parks and gardens, OGL v3, proposed approved |
| Waterside | 100 `water_access` high | Approved |
| Culture | 40 *`culture_kinds_nearby`* high + 25 `culture_venues` high + 10 *`library_proximity`* low + 25 *`culture_recognised_nearby`* high | Overture now. The libraries list and both recognition lists are Arts Council England's, whose pages nobody has read. The founder opens and saves those pages. Recognition stays under 60 hundredths, so it never decides the vibe alone |
| Places to train | 35 *`gym_choice`* high + 25 *`pool_proximity`* low + 20 *`court_pitch_kinds`* high + 20 `park_proximity` low | Sport England Active Places, CC BY 4.0 as read, proposed approved. No tier and no operator is in the recipe |
| Places to meet | 40 *`meeting_place_kinds`* high + 20 *`library_proximity`* low + 20 *`sports_facility_nearby`* high + 10 `play_space_proximity` low + 10 `highstreet_access` high | Allotments and children's centres from approved sources. Libraries and sports facilities as above. parkrun counts as a kind only after a written yes |
| Family amenities | As today. *`nursery_nearby`* joins when the Ofsted file passes its gate | Approved, but for school results, which are gated |
| Everyday on foot | 30 `highstreet_access` high + 25 *`gp_walk`* low + 25 *`pharmacy_walk`* low + 20 `station_walk` low | `nhs-ods` is approved for destination search only and must gain `scoring`. The pharmacy list is proposed gated |
| Home working | 50 *`broadband_gigabit`* high + 30 `noise_exposure` low + 20 `park_proximity` low | Ofcom fixed coverage, Spring 2026, OGL v3, proposed approved. No file has been opened, so nobody knows whether London's areas differ. If they do not, the feature is shown and not ranked |

### 2.3 What each cannot see, and the words that call it up

| Vibe | Cannot see | Five things a person might type |
|---|---|---|
| Street character | Whether streets are clean. Empty shops. Graffiti or street art. Noise from venues. Whether a place is changing. Anything about who lives there | "somewhere a bit gritty" · "old warehouses and railway arches" · "edgy and industrial, not manicured" · "polished and smart" · "nothing too industrial" |
| Built age | The state of a building. What the inside is like. Whether a period house has been split into flats | "period houses" · "Victorian terraces" · "new-build flats" · "old streets with character" · "modern, nothing old" |
| Homes | Balconies and front gardens. Whether one home has a garden. Building height | "a house with a garden" · "flats are fine, I like it dense" · "not too built up" · "proper city living" · "space between the houses" |
| Pace | Opening hours. How busy a venue is. What is on. Noise, which is shown beside the dial | "buzzy, with lots going on in the evening" · "quiet in the evenings" · "lively but not hectic" · "plenty of bars and restaurants" · "a sleepy sort of place" |
| Food variety | Whether the food is good. Prices. Who eats there | "lots of different cuisines" · "foodie" · "great places to eat" · "restaurants from all over the world" · "independent cafes" |
| Village feel | Whether people know each other. Whether the shops are any good | "village feel" · "like a village in the city" · "independent shops and old streets" · "a proper little centre" · "feels like its own place" |
| Leafy | One named street. Trees under 3 m. Planting or felling since the map was made. Species | "leafy" · "tree-lined streets" · "lots of trees" · "green, with gardens" · "I want to see trees from my window" |
| Parks close by | Whether a park is well kept, busy or pleasant after dark. No open rating of parks exists | "near a big park" · "a park I can run in" · "tennis courts nearby" · "somewhere to walk the dog" · "playing fields close by" |
| Waterside | Whether the bank can be walked. Flood risk | "by the river" · "near a canal" · "waterside" · "a walk along the water" · "close to the river" |
| Culture | Ratings, reviews, awards. What is on, hours, prices. The grassroots scene. Whether a venue is still open | "theatres and galleries nearby" · "a good museum within reach" · "highly rated theatres" · "an independent cinema" · "live music venues" |
| Places to train | Whether a gym is good, busy or worth its price. Membership prices. Gyms under about 5 stations | "a gym and a pool nearby" · "a cheap gym within a walk" · "boutique fitness studios" · "somewhere to swim" · "tennis or squash courts" |
| Places to meet | Whether people are friendly. Whether a group has room or still meets. Informal ties | "a community feel" · "a parkrun nearby" · "a library and a community hall" · "things to join" · "an allotment" |
| Family amenities | Catchments. Whether a school has places. Who the neighbours are | "good primary schools and playgrounds" · "things for the kids to do" · "schools within a walk" · "a playground nearby" · "a nursery close by" |
| Everyday on foot | Whether a surgery takes new patients. Waiting times. Opening hours | "everything within a walk" · "a GP and a chemist nearby" · "a proper high street" · "shops and a doctor close by" · "I want to do the basics on foot" |
| Home working | Full fibre below borough level. What speed a home gets, or what it costs. 5G for a neighbourhood | "I work from home and need fast broadband" · "full fibre" · "good internet" · "5G" · "a quiet place to work from home" |

Four of these sentences are read as something narrower than was typed, and the chip says so: "highly rated" as "recognised by a public body", "boutique" as "class studios", "full fibre" as "gigabit-capable", and "a community feel" as "places to meet". Two are heard and turned away with a reason: "5G", with a link to Ofcom's own checker, and "a parkrun nearby", until parkrun says yes.

### 2.4 Figures that sit beside a vibe, and are never inside one

| Figure | Beside | Direction | Default | Why it is kept out of the recipe |
|---|---|---|---|---|
| Recorded criminal damage, recorded anti-social behaviour | Street character | Less only | Off, closed, with the crime caveat | Nobody seeks it. Inside the dial, asking for "gritty" would rank recorded crime up. Criminal damage moves with violence at 0.81 across London's LSOAs |
| Transport noise, nitrogen dioxide | Street character, Pace | Less only | As today: a small weight until a wish is applied | They are nuisances. A person who asks for Buzzy has not asked for traffic noise |
| Kinds of gym nearby: council, chain, independent, class studio, gym with a pool | Places to train | Shown only | Shown | The mix follows income |
| A low-cost chain gym within a walk | Places to train | Near only | Off until asked | A tier is the operator's own words about itself, on a list the founder keeps. It is a filter a person asks for |
| A place of worship within a walk, no faith named | Places to meet | Near only | Off until asked | A founder decision. It counts as one kind of meeting place |
| Homes that can order full fibre, outdoor 5G | Home working | Shown only | Shown, naming the borough | Published for boroughs only |
| Step-free access at each station | Everyday on foot | Shown only | Shown | Stations run by other operators are missing, so ranking would mark south London down for a gap |

Two things in the research need putting right.

| Where | What | What this proposal does |
|---|---|---|
| `grit.md` | It says nothing on the scale may be a nuisance, and its draft recipe holds `noise_exposure`, which the contract lists as one | Takes noise out and gives its weight to land use and main roads |
| `community.md` and `fitness.md` | Both propose the id `sport-england-active-places`, one as gated and unread, one as approved and read | Registers it once, from `fitness.md`, which read the licence |

### 2.5 The founder's eighth item: local makeup

`people.md` separates three acts: showing an official figure, ranking by it, and building a vibe from it. Its recommendation is followed here: vibes come from places under every option, and the choice between the options is the founder's. If nothing is decided, ADR 0006 stands as written.

| | Option 1. Places only | Option 2. Show, never rank | Option 3. Residents in ranking or vibes |
|---|---|---|---|
| Allows | Food variety, places to meet, a place of worship or community centre named as a destination. A link out to the ONS census pages | All of option 1, and the census figures for the area in a fenced panel | Searching or sorting by who lives somewhere |
| Risks | The "local makeup" part of item 8 is unmet | Wording and staleness. The census is 5 years and 10 months old at launch. Unreviewed | Segregation, indirect discrimination and stereotype are all in play. A filter a person sets can reveal their own faith or origin |
| Must change | Nothing | ADR 0006, PLAN section 15, the registry's rule on audit data, a new `residents` dimension, a release file that `rank()` never opens | All of option 2, rule 8, the neutral sentence, and paid legal advice, which ADR 0007 rules out |
| What this design does | The portrait ends with "Burro counts places. It does not describe the people who live here", and the link | The panel sits last on the area page, below everything else. It is a table, never a sentence. It is never in the portrait, the lens, a result, a comparison, a share or "more like this" | Nothing is designed for it. Every vibe carries `describes`, and a test refuses any value but `place` or `buildings` |

Recommended, as the research recommends: option 2 in two steps. Step 1 at launch: age bands, household type and students. Step 2: country of birth, ethnic group and religion, closed by default, once a free legal clinic has read the panel or the founder has recorded in ADR 0006 that the leftover risk is accepted. Never option 3 without paid advice.

### 2.6 Asked for, and not possible as asked

| Asked for | Why not | What is offered instead |
|---|---|---|
| Street cleanliness in "gritty" | No open data below borough level | Said plainly under the dial. Recorded incidents beside it, on request |
| Socioeconomic factors in "gritty" | They describe residents. The official indicators include asylum support, disability benefits and English language ability | The built place: land use, roads, density, green |
| "Boutique" and "high quality" gyms | No lawful rating or price list exists | Kinds of gym, and "low-cost" or "premium" only in an operator's own published words |
| "Highly ranked" culture | Every ratings and awards site that was read forbids commercial reuse | "Recognised", with the scheme always named |
| parkrun | Nothing was read | A question for parkrun. Until a written yes, it stays out, and no list is compiled by hand |
| 5G for a neighbourhood | Ofcom publishes boroughs only, and its API forbids building a dataset | A borough figure labelled as one, and a link to Ofcom's checker |

### 2.7 What becomes of today's twelve tags

No share outlives a restart today and no real release exists, so nothing stored names a tag. This is the cheapest moment to change the set. A retired id is never reused.

| Today | Becomes |
|---|---|
| `leafy`, `waterside`, `village_feel`, `family_amenities` | Kept. `leafy` gets a new recipe when the canopy map is in |
| `buzzy`, `evening_venues` | The Buzzy end of Pace |
| `quiet_residential` | The Calm end of Pace, with noise beside it as its own figure. "Quiet" makes two chips: "Pace: calm" and "Less traffic noise" |
| `historic_character` | The Period end of Built age |
| `foodie` | Food variety |
| `creative` | Folded into Culture. Studios and workspaces join when the GLA clears that layer |
| `strong_high_street` | Folded into Everyday on foot |
| `near_universities` | No longer a vibe. It was one feature under a tag's name. "Near a campus" stays a chip with one direction |

All 23 features stay. About 25 are added as their sources clear, each with a catalogue row and a proxy audit row.

## 3. The experience

Every moment below is drawn from the release or from the last spec the API returned. The website still writes no words about a place: every sentence and heading quoted below is a template or fixed text held in core and served by the API.

### 3.1 Moment by moment

| Moment | On screen | The person can | Must be true underneath |
|---|---|---|---|
| 1. Before a search: the lens | Under the prompt box, the five families and their vibes as words. Pressing one colours the map by that vibe alone, in five bands, with both ends named in the legend. One line says what it is made of. The table of all areas gains a column for it, so the lens is never colour alone | Try each word and see where in the city it is found. Press "Add to my search" | Positions are a function of the release alone, so the page is static and cached. Every vibe comes in one answer, so the server is never told which word was pressed. No lens exists for recorded crime or for any figure of 2.4 |
| 2. Before a search: start from a place | "Know one area already? Start there." A search field over area names | Open that area's portrait, then "More like this" | The name is matched against the release's own names. An area Burro does not hold gets "Burro only knows the areas in this data" |
| 3. In the prompt | The box as today. Example sentences use vibe words and no proper noun | Type anything | Typed text still travels in one `POST` body. Nothing is read key by key |
| 4. What Burro understood | One chip for each vibe, drawn as a small dial with its stop marked: "Street character: towards Gritty". "Assumed" where a looser word was read. The words it rests on are underlined, from `rests_on` | Move the stop, change how much it counts, remove it | The reader maps a closed list of words to a vibe and a stop. "Rough", "dodgy" and "sketchy" map to nothing. A word about people gets the neutral sentence |
| 5. Turning a dial | The list is marked busy, then the map recolours by fit and the live region says how many areas changed place | Turn any dial stop by stop | One edit to route 2 for each stop. The ranking is recomputed, never animated from a guess |
| 6. A result | Under the name, a character line: "More than most: Waterside, Period. Less than most: Places to train." Then reasons and one trade-off, as today. A dial the area misses by most is the trade-off, in a template of its own: "Pace: nearer the Buzzy end than you asked for" | Open the portrait. "More like this" | The character line is the same for every search. Reasons are for this search. Each cites a fact |
| 7. The shortlist | Above the first five: "Your first five are alike on Pace and Leafy. They differ most on Built age." | Press a vibe to sort the five by it | Worked out from the five positions. Labels only, no adjective |
| 8. The area page as a portrait | See 3.2 | Open any recipe. Open the closed blocks | Built on the server from route 6. Reads with scripts off |
| 9. Comparison | A character block first: each dial once, with a marker for each area on the same bar. Then "These differ most on Homes." Then the rows by weight, as today | Add or remove an area | The census panel never appears here, under any option |
| 10. More like this | Five areas, each with "Closest on" and "Differs most on". A button, "Like this, but…", opens the dials set to this area's stops | Turn one dial, add a budget, add a journey | Likeness is distance between portraits over place-only vibes. See 4.4 |

### 3.2 The portrait

```
Thrushcombe, in Quillhaven                              [locator map]
------------------------------------------------------------------
Character
  Street character   Polished  [#]---+---+---+---  Gritty    Made of
  Built age          Modern    ---+---+---+---[#]  Period    Made of
  Homes              Houses    ---[#]---+---+---   Flats     Made of
  Pace               Calm      ---+---[#]---+---   Buzzy     Made of
More than most here      Village feel · Food variety · Leafy
Less than most here      Places to train
Burro cannot place       Home working: no broadband figure in this data
What is here             Culture · Places to train · Places to meet
                         one line per kind, each with source and date
What Burro cannot see    fixed lines, one per vibe shown
More like this           five areas, with what is closest and furthest
Recorded incidents, noise and air            [closed until opened]
Cost · Stations · Sources
Census 2021: who lived here     [only under option 2, last, a table]
```

| Rule | Detail |
|---|---|
| Order | Dials first, in a fixed order. Then up to three vibes at least 25 points above the middle, then up to three at least 25 below, largest first, ties by id |
| Words | "More than most" and "less than most" are fixed headings served with the portrait. Each vibe under them is a `tag` fact, with its standing sentence one tap away |
| "Made of" | The recipe: each ingredient, its weight, this area's value, its standing, its source and its date |
| A marker | Drawn in one of five bands. The percentile is never printed |
| Names | Counts and kinds only, until the founder decides whether public institutions, parks and gym operators may be named |
| Sentences | Templates. A portrait written by a model waits for the verifier to be extended, as the contract says |

The sketch shows the layout. Its positions are for illustration and are not taken from the fixture.

### 3.3 When a vibe cannot be measured

| Case | In the lens and the portrait | In a ranking | Words |
|---|---|---|---|
| The area has under 60 hundredths of the recipe | A hatched bar with no marker. Never drawn at the middle | The vibe is dropped for that area and the weights rebalanced, as today. The card's completeness line says so | "Burro cannot place {name} on {label}: {n} of {m} ingredients have no figure in this data." |
| The release does not hold the vibe, because a source is not cleared | It is not offered | An edit meets `not_in_release` | "Burro cannot measure {label} yet." |
| The figure exists for the borough only | Shown beside the vibe, in its own block | Never scored | "Across {borough}: {label}, {value}. This is a figure for the borough, not for {name}." |
| The idea has no honest measure | Not offered | No edit | "Burro has no measure of {thing}, and will not guess." With what it used instead, if anything |
| The request is about who lives somewhere | | No edit for that part | The neutral sentence, word for word, as today |

## 4. How the engine changes

Ranking stays a pure function of a spec and a release. Nothing below adds a call, a clock or a stored search.

### 4.1 A recipe as data

A recipe stays in core, where it is reviewed as code and tested. Route 11 already serves each tag with its formula. It gains the new fields.

```json
{"tag_id": "street_character", "shape": "dial", "family": "streets_and_buildings",
 "label": "Street character", "ends": {"low": "Polished", "high": "Gritty"},
 "describes": "place", "in_likeness": true, "since_catalogue": 2,
 "terms": [{"feature_id": "land_industrial", "hundredths": 45, "reading": "high"},
           {"feature_id": "road_major_exposure", "hundredths": 20, "reading": "high"},
           {"feature_id": "homes_density", "hundredths": 15, "reading": "high"},
           {"feature_id": "green_cover", "hundredths": 10, "reading": "low"},
           {"feature_id": "conservation_cover", "hundredths": 10, "reading": "low"}],
 "beside": ["incident_criminal_damage", "incident_asb", "noise_exposure"],
 "cannot_see": ["street_cleanliness", "empty_shops", "graffiti", "venue_noise", "change_over_time"]}
```

| Rule on a recipe | Held by |
|---|---|
| Weights sum to 100. Under 60 present means not placed | As today |
| No term is a crime or incident feature | The test that exists, widened to the new incident features |
| A dial's terms are tastes only: never a nuisance, and never a feature whose one direction is a fairness rule, such as a campus, a place of worship or a gym tier | New. `Feature` gains `kind`: `taste`, `amenity`, `nuisance`, `on_request` |
| A one-ended vibe may read a nuisance `low`, as `quiet_residential` does today | As today |
| Conservation areas and recognition each carry under 60 hundredths | As today, widened |
| `describes` is `place` or `buildings` | The test `test_no_feature_or_tag_describes_residents`, widened to ends, words and `cannot_see` |
| Every vibe has a proxy audit row written before its data is ingested | The audit's written rule, which does not exist yet |
| A feature is rankable only if its raw values vary across the city by a published threshold | New, in the pipeline. `rankable: false` already exists in the catalogue |

### 4.2 Ranking a dial

A `TagWeight` gains `target`, one of five stops: 0, 25, 50, 75, 100. A one-ended vibe is always at 100.

```
p = the area's score for the vibe, 0 to 100        t = the target
U = 1 - abs(p - t) / max(t, 100 - t)
```

| Target | Utility at p = 0, 50, 100 | Meaning |
|---|---|---|
| 100 | 0, 0.5, 1 | The high end. The same as `score / 100`, so every one-ended vibe ranks exactly as a tag does today |
| 0 | 1, 0.5, 0 | The low end |
| 50 | 0, 1, 0 | The middle: "lively but not hectic" |
| 75 | 0, 0.67, 0.67 | Towards the high end |

| Words | Edit |
|---|---|
| A vibe or an end simply named: "gritty", "leafy" | Stop at that end, weight at what a mention is worth, 0.50 |
| "A bit", "fairly", "quite" before an end | One stop short of that end |
| "Not too" before an end, or "X but not Y" of one dial | The middle, marked assumed |
| "Much more", "really" | No further than the end. It raises the weight by a large step |

`TagEdit` gains `target`, with a sentinel for "unchanged". A target other than 100 on a one-ended vibe is rejected as `direction_not_allowed`. `canonical()` writes the target as a whole number of stops and leaves it out at 100, so the hash of any spec with only one-ended vibes is what it would be today.

### 4.3 Crime on request, beside "gritty"

| Question | Answer |
|---|---|
| Does asking for "gritty" weigh crime? | No. The dial holds none, and rule 8 of the reducer is unchanged |
| Can a person have both? | Yes. "Gritty but low crime" makes two edits: the dial towards Gritty, and a stated weight on recorded crime, less only |
| Are the new incident figures crime? | Yes. `incident_criminal_damage` and `incident_asb` join the crime group: default 0, in no recipe, weighted only on a stated request, never "safe" or "unsafe" |
| Does "more like this" read crime? | No. Likeness never reads a figure of 2.4 |
| Is the word "gritty" ever said of a place? | No. It is a label and an end. A sentence says where a place sits: "nearer the Gritty end than 80% of the 22 areas compared in this release" |
| What is left over? | Areas nearer the Gritty end will often have more recorded crime. Burro says nothing of it unless asked. That is the rule as it stands, and the founder should know it |

### 4.4 "Like this area"

| Step | Rule |
|---|---|
| The spec | Gains `like`: at most one anchor, with `area_id`, `weight` and `provenance`. It holds an id and a number, as the rest of the spec does |
| The component | `like`. For each vibe with `in_likeness` that both areas are placed on, and that the person has not set themselves, take `abs(p_area - p_anchor)`. `U = 1 - mean / 100` |
| Missing data | If either area is placed on under 60% of those vibes, the component is missing for that area. If the anchor itself is, the edit is rejected with a new reason, `anchor_not_placed` |
| "But quieter" | A `TagEdit` on Pace. Its target is the anchor's band moved one stop towards Calm, two for "much". The reducer reads the band from the release, which it is already handed |
| "But cheaper" | If a budget is set, a step down. If none is, the amount is set to the anchor's upper quartile for the kind of home and then stepped down, marked assumed. This changes contract 5.2, where a step on a budget with no amount is rejected today. It is the founder's call |
| The anchor in results | Ranked like any area and marked "your starting point" |
| Names | The reader takes an anchor only from the whole of an area's name in the person's own words, after "like", "similar to" or "the same feel as". A model may copy a name and never supply one. It never says what a place is like |
| A place outside the release | No edit. `outside_the_city` in `unmet` |
| On the area page | `similar(release, area_id, n)` in core, pure, with no spec. Route 6 serves the five nearest and, for each, the two closest vibes and the one furthest |
| Sentence | A new fact kind, `likeness`, whose names are the two areas. Template: "Closest to {anchor} on {a} and {b}. Furthest on {c}." |

On the made-up city, "like Thrushcombe but quieter and cheaper" should put Wickerford near the top: both are old and independent, and Wickerford is calmer. That is an expectation from the traits set by hand, and becomes a test once the fixture is rebuilt.

### 4.5 What changes in the contract

| Section | Change |
|---|---|
| 0 | `ENGINE_VERSION` and `CATALOGUE_VERSION` both move |
| 3.1 | `Feature` gains `kind`. New rows as sources clear. The list of nuisances gains the two incident features |
| 3.2 | `Tag` gains `shape`, `ends`, `family`, `describes`, `in_likeness`, `beside`, `cannot_see`. Eight ids are retired and eleven added, which leaves fifteen |
| 4 and 5 | `TagWeight` and `TagEdit` gain `target`. The spec gains `like`, and `Operations` a seventh array, `like_ops` |
| 6.2 | The utility of a tag becomes the formula of 4.2. A `like` component is added |
| 7 | New fact kinds: `likeness`, `mix` (kinds and counts beside a vibe) and `borough`. New templates: `tag_dial`, `likeness`, `borough`. A source id for Burro's own judgement, for the operator list |
| 7.4 | More refused words: "best", "top", "highly rated", "acclaimed", "friendly", "close-knit", "vibrant", "up and coming". "Gritty" and "Polished" pass only as a label or an end |
| 8 | The lexicon maps a word to a vibe and a stop. `UnmetCategory` gains `ratings`, `mobile_coverage` and `not_yet_measured` |
| 9.2 | Route 6 gains `portrait` and `similar`. Route 7 gains the character block. Route 11 serves the fields of 4.1. A new route 13, `GET /v1/vibes`, serves every area's score on every vibe, for the lens. It is a function of the release and is cached as routes 4 to 6 are. It serves every vibe at once, so no call says which one a person looked at |
| 12 | Tests, named for what they protect, among them: `test_a_dial_holds_no_nuisance_and_no_feature_with_a_fairness_direction`, `test_a_target_at_the_high_end_ranks_as_a_tag_did`, `test_a_vibe_with_too_little_data_is_never_drawn_at_the_middle`, `test_like_an_area_never_reads_crime_or_a_figure_kept_beside_a_vibe`, `test_gritty_is_a_label_and_is_never_said_of_a_place`, `test_a_place_is_like_itself_and_likeness_runs_both_ways` |

## 5. What to build first

On the made-up city, in this order, so that the founder can feel it within days. No new real data is needed. The generator already sets seven traits for each area by hand, and one of them, `industry`, feeds no feature of its own today.

| Day | Build | The founder can then | Done when |
|---|---|---|---|
| 1 | `target` on a tag, and the utility of 4.2. Pace, Built age and Homes as dials, from features the release already holds | Turn three dials in the settings and watch the list and map change | The high end of each dial ranks as the old tag did. The low end finds the area the traits say it should |
| 2 | Two made-up features, `land_industrial` and `road_major_exposure`, from the `industry` trait. Street character as a dial. The fixture rebuilt | Ask for "gritty" and for "polished" | "Gritty" puts Cindermoor first among the areas that can be ranked. No recipe holds crime |
| 3 | Route 13 and the lens | Press a word before any search and see the city coloured by it | The lens sends nothing a person typed. An area that is not placed is hatched |
| 4 | The portrait on the area page: dials, "Made of", more and less than most, cannot see | Read an area as a character | The page reads with scripts off. Every line has a source and a date |
| 5 | `similar()` and "More like this" on the area page. The `like` anchor, and "like {area} but quieter" in the rule-based reader | Start from an area and walk the city by likeness | A place is like itself. Likeness runs both ways. The anchor is never supplied by a model |
| 6 | Made-up features for the founder's other items: gym choice and kinds, culture kinds, meeting place kinds, canopy, gigabit broadband. The character block in comparison. The shortlist line | See all eight items on one screen, with item 8 as the fixed line and the link | Every kind is a made-up kind. No operator and no venue is named |

The banner stays on every page. Nothing seen on the made-up city says how London will feel: the founder is judging the interaction, not the truth of any vibe.

Work that can start beside it, and needs the founder: open and save the Arts Council England pages, the Active Places information file and parkrun's terms; put the questions to Sport England, the GLA GIS team and parkrun; write the proxy audit's rule.

## 6. Risks, and what the founder must decide

| Risk | What is done about it |
|---|---|
| A place-only vibe still follows wealth, and wealth follows protected groups. Likeness gathers every such effect into one number | A proxy audit row for every vibe before ingest, and one for likeness as a whole. A vibe that fails is capped, made on-request, or dropped |
| A map coloured by "Gritty" can be passed round as a map of bad areas | A neutral name for the dial, two ends drawn with equal weight and no "bad" colour, and no lens for crime. Whether Street character has a lens at all is the founder's call |
| "Gritty" reads as an insult to people who live there | It is never said of a place. It is an end of a scale with a published recipe |
| The new set retires eight tag ids, and the contract's worked examples change | Done now, before any real release or stored share |
| The sanity set doubles for dials, which need places at both ends | More curation hours. They are the founder's and the second curator's |
| A percentile makes a small gap look large, as broadband may | A feature is ranked only if its spread passes a published threshold |
| Half the vibes rest on Overture Places, whose London quality is unmeasured | The planned spike comes first. A zero from Overture is unknown, not zero |
| Four vibes wait on a publisher's page or answer | Each runs in a reduced form, or is not offered. None is filled in |
| "Like the area I live in now" says where a person lives, and a share stores the spec | The share panel says the link will hold the starting area. It is an area, never an address |
| Templates make the portrait read stiffly | Accepted. A model writes nothing until the verifier can check a claim about residents |
| Fifteen vibes is a lot to learn | Five families, and the lens, which teaches a word by showing it |

| # | Decision | Recommendation |
|---|---|---|
| 1 | Item 8: option 1, 2 or 3 | Option 2 in two steps, as `people.md` recommends. Until decided, ADR 0006 stands |
| 2 | What may go into "gritty" | Place only, with recorded incidents beside it on request. `grit.md` choice B |
| 3 | The name of the dial | "Street character", with "Polished" and "Gritty" as its ends |
| 4 | May Street character be a lens on the map before a search? | Yes, after its audit row is written and the sanity set passes |
| 5 | Retire eight tag ids into the new set now? | Yes |
| 6 | May public institutions, the nearest large park and gym operators be named? | Yes, from sources registered for display, after the verifier is extended. Never a sole trader |
| 7 | May "cheaper than {area}" set a budget from that area's rents? | Yes, marked assumed |
| 8 | May a share hold the starting area of "like this"? | Yes, and the share panel says so |
| 9 | Gym tiers | Kinds first. "Low-cost" and "premium" only in an operator's own words, as a filter a person asks for |
| 10 | "Highly ranked" culture | "Recognised", with the scheme named. No ratings licence is sought |
