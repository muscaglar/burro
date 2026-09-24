# Slice 1: vibes, a reader that asks, and the answer first

Status: built, 2026-09-24, on the made-up city, and joined the same day with the first real builds of London: the engine is then 1.8.0 and the catalogue 4, and [the contract](contract.md) says what a release that is not made up carries of the vibes. It was written on 2026-09-23 as the specification five builders worked to at once. It was then built, walked in a browser, reviewed twice and mended, and then walked a second time and mended again (section 11.1). It turns [vibes.md](vibes.md) section 8, seven decisions of the founder and gaps 1 and 14 to 22 of [web.md](web.md) section 13 into interfaces. It runs on the made-up city only: every name, figure and example below is invented, and no sentence describes a real place. No model is called and no real dataset is read.

| To know | Read |
|---|---|
| What the engine, the release and the API do, rule by rule | [The contract](contract.md). It is right where this document and it disagree |
| What the website shows, state by state | [web.md](web.md). It is right where this document and it disagree |
| What is not built | Section 9 |
| What the founder must decide, each with a recommendation | Section 10 |
| What was found by the walks and the reviews, and what became of each | Section 11, and 11.1 for the second walk |

Where this document and vibes.md disagree, this document is what is built in this slice, and section 9 lists each difference. Sections 1 to 8 are kept as the record of what was specified, and are corrected where what was built differs.

## 0. What is fixed

The seven decisions, and where each is built: (1) a vibe is a published recipe over measured parts, shown as a band among the areas compared, with its parts and what it cannot see (sections 1, 2, 6); (2) gritty is built two ways behind one switch of the release, default B, and no figure about residents' income, employment, health or education is in either (1.1, 2.1); (3) nothing about who lives somewhere is built (9); (4) the rule-based reader applies a prompt only when the whole of it is a plain list, and otherwise applies nothing and offers suggestions (4); (5) plain sentences about money, home and work are read, and wishes about character stay narrow (4.1); (6) the answer comes first, and a results page is at most 3 screens on a desktop and 5 on a phone before anything is opened (6); (7) every sentence, figure and name about a place is the API's, ranking is a pure function, missing data is never filled in, and nothing typed is logged, stored or put in an address.

`CATALOGUE_VERSION` goes from 1 to 2, a release's `schema_version` from 1 to 2, and the contract from version 1 to 2, because `TagEdit` gains a required field. `CATALOGUE_VERSION` went to 3 when two lines of what a vibe cannot see were reworded. `ENGINE_VERSION` went from 1.3.0 to 1.4.0 as the slice was built, to 1.5.0 as it was mended, to 1.6.0 when an explanation came to say a vibe in short, and to 1.7.0 when a result came to show only what an area has most of where nobody asked (contract section 0). On screen the word is "vibe". In code and on the wire it is a `tag`. A part is a feature in a recipe. The two screens measured are 1440 by 900 and 390 by 844.

## 1. The vibes

### 1.1 The eleven, with gritty in both variants

`low` reads a part from its low end. "Here" is the hundredths of the recipe that the synthetic release holds. The first seven are the shelf, in this order. The rest are under "more", in this order.

| `tag_id` | On screen | Shape, ends low to high | `family` | Shelf word, end | Recipe, in hundredths | Here |
|---|---|---|---|---|---|---|
| `leafy` | Leafy | one way | `green` | leafy | 40 `land_gardens` + 30 `land_woodland` + 30 `green_cover` | 100 |
| `village_feel` | Village feel | one way | `streets_homes` | villagey | 25 `independents_nearby` + 20 `centre_small` + 20 `centre_compact` + 20 `homes_pre1919` + 15 `conservation_cover` | 100 |
| `pace` | Pace | scale: Calm, Buzzy | `pace_food` | lively, high | 35 `venue_evening` + 30 `venue_food_drink` + 20 `highstreet_access` + 15 `culture_venues` | 100 |
| `quiet_residential` | Quiet streets | one way | `streets_homes` | quiet street | 40 `road_major_exposure` low + 30 `evening_cluster_exposure` low + 30 `noise_exposure` low | 100 |
| `built_age` | Built age | scale: Newer, Historic | `streets_homes` | period, high | 35 `homes_pre1919` + 25 `conservation_cover` + 20 `listed_buildings` + 20 `homes_post2000` low | 100 |
| `everyday_on_foot` | Everyday on foot | one way | `daily_life` | walkable | 25 `grocery_walk` low + 25 `highstreet_access` + 20 `station_walk` low + 15 `gp_walk` low + 15 `pharmacy_walk` low | 70 |
| `parks_close_by` | Parks close by | one way | `green` | near a big park | 40 `park_proximity` low + 30 `park_large_proximity` low + 30 `park_facilities` | 100 |
| `homes` | Homes | scale: Houses, Flats | `streets_homes` | | 40 `homes_flats` + 35 `homes_density` + 25 `private_outdoor_space` low | 75 |
| `foodie` | Food and drink | one way | `pace_food` | | 40 `venue_food_drink` + 40 `independents_nearby` + 20 `cuisine_variety` | 80 |
| `family_amenities` | Family amenities | one way | `daily_life` | | 40 `school_primary_nearby` + 35 `play_space_proximity` low + 25 `park_proximity` low | 100 |
| A: `works_warehouses` | Works and warehouses | one way | `streets_homes` | | 40 `land_industry` + 35 `land_storage` + 25 `land_transport_other` | 100 |
| B: `street_character` | Street character | scale: Polished, Gritty | `streets_homes` | | 20 `incident_criminal_damage` + 20 `land_industry` + 15 `incident_antisocial` + 15 `road_major_exposure` + 15 `noise_exposure` + 15 `homes_density` | 100 |

| Rule | Held by |
|---|---|
| Every recipe sums to 100, holds two parts or more, and holds no part of 60 or more. No part describes who lives somewhere | Tests on `TAGS`. `test_no_feature_or_tag_describes_residents`, widened to ends, meanings and `cannot_see` |
| No recipe but `street_character` holds a part of dimension `crime`, and no scale but `street_character` holds a nuisance | A test on `TAGS` that names that one id and no other |
| A release carries the ten and exactly one of A and B. `manifest.gritty_variant` says which. B was refused on a release that is not synthetic until 2026-09-24, and is what a release of London carries since (ADR 0013, as amended) | `parse_release`, rule `vibes_match_core` |

### 1.2 The parts

All 23 features of today stay, with their ids, labels and units. 21 are added to core. The synthetic release carries 17 of them. The last four are in core and in no release yet, so three recipes run short, as London would today.

| `feature_id` | Label | Unit | Polarity | `kind` | `family` | In likeness | Made up from the traits |
|---|---|---|---|---|---|---|---|
| `independents_nearby` | Independent places to eat and drink within a 10-minute walk | count | more | taste | `pace_food` | yes | lively, indie, central |
| `centre_small` | Share of homes whose nearest town centre is a small one | % | more | taste | `streets_homes` | yes | street, less lively, less central |
| `centre_compact` | Share of the nearest town centre within 200 m of its middle | % | more | taste | `streets_homes` | yes | street, indie, less lively, less central |
| `listed_buildings` | Listed buildings | per km² | more | taste | `streets_homes` | yes | old, less by the river |
| `homes_post2000` | Homes built since 2000 | % | either | taste | `streets_homes` | yes | less old, by the river |
| `road_major_exposure` | Share of homes within 100 m of a main road | % | less | nuisance | `streets_homes` | no | central, street, works |
| `evening_cluster_exposure` | Share of homes within 150 m of a cluster of evening venues | % | less | nuisance | `pace_food` | no | late, central |
| `land_industry` | Land used for industry | % | either | taste | `streets_homes` | yes | works |
| `land_storage` | Land used for storage and warehousing | % | either | taste | `streets_homes` | yes | works |
| `land_transport_other` | Land used for depots, yards and other transport | % | either | taste | `streets_homes` | yes | works, central |
| `land_gardens` | Land that is residential garden | % | more | amenity | `green` | yes | green, family, less central |
| `land_woodland` | Land that is woodland | % | more | amenity | `green` | yes | green |
| `park_large_proximity` | Walk to the nearest park of 20 ha or more | m | less | amenity | `green` | yes | green, by the river |
| `park_facilities` | Kinds of thing to do in parks within a 15-minute walk | count | more | amenity | `green` | yes | green, family, by the river |
| `grocery_walk` | Walk to the nearest food shop | min | less | amenity | `daily_life` | yes | street, less late, less offices |
| `incident_criminal_damage` | Recorded criminal damage | per 1,000 residents a year | less | nuisance | none | no | late, central, works |
| `incident_antisocial` | Recorded anti-social behaviour | per 1,000 residents a year | less | nuisance | none | no | late, central, works |
| `private_outdoor_space` | Homes with private outdoor space | % | more | amenity | `streets_homes` | no | not in the release |
| `cuisine_variety` | Kinds of food nearby | count | more | taste | `pace_food` | no | not in the release |
| `gp_walk` | Walk to the nearest GP surgery | min | less | amenity | `daily_life` | yes | not in the release |
| `pharmacy_walk` | Walk to the nearest pharmacy | min | less | amenity | `daily_life` | yes | not in the release |

| New field | What the 23 features of today get |
|---|---|
| `kind` | `nuisance`: the two crime features, `air_no2`, `noise_exposure`. `NUISANCES` is read from `kind`. `on_request`: `university_proximity` and the two attainment features. `taste`: `venue_food_drink`, `venue_evening`, `venue_independent`, `homes_flats`, `homes_pre1919`, `homes_density`, `conservation_cover`. `amenity`: the other nine |
| `describes` | Of all 44: `events` for dimension `crime`. `buildings` for `homes_flats`, `homes_pre1919`, `homes_post2000`, `homes_density`, `conservation_cover`, `listed_buildings` and `private_outdoor_space`. `place` for the rest. There is no value for residents |
| `family` | `streets_homes` for dimension `homes`. `pace_food` for `venues_culture`. `green` for `green_water`. `daily_life` for `schools` and `station_access`. None for `crime` and `air_noise` |
| `in_likeness` | True for `homes_pre1919`, `conservation_cover`, `venue_evening`, `venue_food_drink`, `highstreet_access`, `culture_venues`, `green_cover`, `park_proximity`, `play_space_proximity`, `station_walk`. With the 13 above, 23 measures are in the release |
| `method` | `measured` for all 44, as the slice was built. `modelled` and `averaged` waited for real data. Since the slice was joined with the first real builds, `air_no2` is `modelled` (contract, section 3.1) |
| `short_label` | Web gap 16: at most 40 characters, no figure, no place name. It says the wish where the polarity is fixed ("Less transport noise", "Nearer a park") and the measure where it is `either` ("Pubs and bars") |

The `dimension` of a new feature is `crime` for the two `incident_` features, `air_noise` for the two `_exposure` features, `services`, which is a new value, for the three walks of `daily_life`, and otherwise `homes`, `venues_culture` or `green_water` by its family. The two `incident_` features are of dimension `crime`, so every crime rule of contract 3.1 and 5.3 holds for them as features: default weight 0, weighed only on request, the `feature_crime` caveat. The generator draws the 17 new parts from a second stream, `Random(seed + 1)`, after everything it draws today, so no value of the 23 moves. Two traits are set by hand beside the seven, and only the new parts read them: `offices`, which the centre alone has, and `works`, which is `industry` but for Lantern Yard and Gorsebeck. Since 2026-09-24 three more say where an area is not what its place on the map would make it, and the older figures of the areas that were changed moved with them: `flats`, `parks` and `roads` (section 10.1). "Late" is lively, less where there are offices. How much of an area is by the river is measured from the map. Gaps on purpose: Otterby Fields holds none of the 17, so it has a band on Homes alone. Grapnel Dock and Sedgewater Marsh hold no share of homes and no rate.

### 1.3 How a position is worked out and banded

| Step | Rule | Where |
|---|---|---|
| `raw` and `score` | `raw` is the weighted mean of the parts that have a value, each read high or low, and `null` under 60 hundredths present (contract 3.2). `score` is its mid-rank percentile (contract 2.4). It is for ranking and is never printed | `tag_raw()`, `percentile_of()`, unchanged |
| `band` | `1 + min(4, (5 * below) // compared)`. `compared` is the rankable areas with a `raw`. `below` is how many of them are strictly lower. 1 to 5, and `null` when `raw` is. With 22 compared, `below` of 0 to 4 is band 1, 5 to 8 band 2, 9 to 13 band 3, 14 to 17 band 4, 18 to 21 band 5 | `band_of(values, rankable)`, new, in `catalogue.py`. The only implementation, for vibes and for parts |
| Which end | Band 1 is nearest `low_end` and band 5 nearest `high_end`. For a one-way vibe band 5 is most | |
| `spread_low`, `spread_high` | The bands the middle half of homes span. No release holds sub-areas yet, so both equal `band`, but for three areas mixed by hand, one on each scale that both variants carry: Foxholt on `pace` and Sable Reach on `homes`, each band 4, spread 3 to 5. Kindlewharf on `built_age`, band 3, spread 2 to 4 | The generator |
| No percentage | No surface prints a percentage for a vibe. A part keeps its sentence of contract 7.3 | The `vibe` templates |

### 1.4 What each cannot see, and the words that call it up

Every vibe says first, word for word: "One street or one home. An area is many streets." A word marked † is read as `inferred`, so its chip says "assumed". The words are phrases of `LEXICON`. No other word calls up a vibe. A word of a retired tag calls up what took its place: creative and arty† the feature `culture_venues`, a good high street `highstreet_access`, a university `university_proximity`, river and canal† `water_access`. "park", "pubs", "station" and every other phrase of a feature are as today. A new feature answers to its label and its `short_label`, and `grocery_walk` also to "food shop" and "supermarket", and `road_major_exposure` to "main road" and "main roads".

| Vibe | Cannot see, word for word | Words, and the edit |
|---|---|---|
| Leafy | Trees under 3 m. Planting or felling since the map was made. Street trees | leafy, green†, greenery†, trees†, tree lined†: more |
| Village feel | Whether neighbours know each other. Which shops there are. Empty units | villagey, village, village feel: more |
| Pace | How a weekday differs from a weekend. Who the venues serve. Opening hours. What is on | lively†, buzzy, bustling†, nightlife†: towards Buzzy. calm†, sleepy†: towards Calm |
| Quiet streets | Noise from neighbours, venues or works. Which noise is from roads and which from aircraft. How busy a road is | quiet, quiet street, peaceful†, residential†, peace and quiet†: more |
| Built age | The state of a building. Its inside. An area the conservation data does not cover is unknown, not zero | period, period houses†, historic†, heritage†, victorian†: towards Historic. new build, modern flats†: towards Newer |
| Everyday on foot | Whether a surgery takes new patients. Opening hours. Step-free access at every station. Which side of a railway a home is on | walkable, walkability: more |
| Parks close by | Upkeep. Whether a park is busy. Opening hours. No open rating of parks exists | big park, near a big park, large park: more |
| Homes | The size of a home inside. Balconies and front gardens. Whether one home has a garden | suburban†, house with a garden†: towards Houses. urban†, city living†: towards Flats |
| Food and drink | Whether the food is good. Prices. Whether a place is still open. Hygiene ratings are never shown | foodie, food scene†, good food†: more |
| Family amenities | Catchments. School places. What childcare costs. Who lives there | family friendly†, good for kids†, good for families†: more |
| A: Works and warehouses | Whether streets are clean or run down. Empty shops. Graffiti. What the land is used for today. Recorded crime. Who lives there | industrial, warehouses, railway arches: more. gritty†, edgy†, raw†: more, with `street_cleanliness` in `unmet` and the word in the assumption. polished, smart, well kept: no edit, `upkeep` in `unmet` |
| B: Street character | Whether streets are clean or run down. Empty shops. Graffiti. Crime that was not reported. Who lives there | gritty, edgy†, raw†: towards Gritty. polished, smart†, well kept†: towards Polished. industrial, warehouses: the feature `land_industry`, more |

## 2. The records

Every record is a frozen model as contract section 0 says. "Required" means the field is always present on the wire. A field not named here is unchanged. In the examples of 2.3 a list is cut to one item. The interpret result has its example in 4.3.

### 2.1 The release, the catalogue, the spec, the edits, the ranked result, the profile and the meta record

| Record | Field | Type | Required | Notes |
|---|---|---|---|---|
| `manifest.json` | `schema_version`, `catalogue_version` | int | yes | 2 and 3 |
| `manifest.json` | `gritty_variant` | `a` or `b` | yes | `build_synthetic(seed, release_id, built_at, gritty_variant="b")`. The committed fixture is `syn-2026-09-23-01`, variant B. `make api GRITTY=a` builds `syn-2026-09-23-02` into a scratch folder and serves it. It is never committed. A test builds it in memory |
| `catalogue.json` | `metrics[]` | `Metric` | yes | Each row gains the six fields of `Feature` below, and each must equal `FEATURES` (rule `catalogue_matches_core`) |
| `catalogue.json` | `vibes` | list of `Tag` | yes | The recipes the release was built with. Each must equal `TAGS` |
| `features.json`, `tags.json` | rows | | | The same shape. 40 features. In `tags.json`, one row for each area and each vibe of `catalogue.vibes`, where it was each `TagId` |
| `tags.json` | `band`, `spread_low`, `spread_high` | int 1 to 5, or null | yes | `null` exactly when `raw` is. `spread_low <= band <= spread_high` (rule `bands_match_raw`) |
| `Feature`, `Metric` | `short_label`, `kind`, `describes`, `family`, `method`, `in_likeness` | str, enum, enum, enum or null, enum, bool | yes | Section 1.2 |
| `Tag` | `short_label`, `meaning` | str | yes | `meaning` is the plain meaning of vibes.md 2.1 |
| `Tag` | `family`, `shape` | enum, `scale` or `one_way` | yes | Section 1.1 |
| `Tag` | `low_end`, `high_end` | str or null | yes | The names of the ends. `null` for a one-way vibe |
| `Tag` | `cannot_see` | list of str | yes | The common line first, then the lines of 1.4, one sentence each |
| `Tag` | `lens`, `strip`, `table` | bool | yes | True for every vibe of a synthetic release |
| `Tag` | `shelf_word`, `shelf_toward`, `shelf_order` | str, `high` or `low`, int; each or null | yes | `shelf_order` 1 to 7 for the shelf, 8 upwards under "more" |
| `TagWeight` | `toward` | `high` or `low` | In a body it may be left out, and is then `high`. It is always returned | `canonical()` writes it only when it is `low`, so no published hash moves |
| `TagEdit` | `toward` | `high`, `low` or `default` | yes, after `step` | `default` leaves it as it is, and is `high` for a vibe not yet in the spec. `low` on a one-way vibe is rejected as `direction_not_allowed`. A `set` that only turns a scale is `changed` true |
| `Assumption` | `code` gains `word`. New field `word` | str | yes | A phrase of the closed list `MIXED_WORDS` in core, in lower case, and `""` for every other code. It is the lexicon's spelling and never the text |
| `UnmetCategory` | new values | | | `street_cleanliness`, `upkeep`, `ratings`, `prices_and_hours`, `mobile_coverage`, `change_over_time` |
| `PreferenceSpec` | | | | No other change. There is no `like` anchor and no seventh array of edits. A retired tag id in a body is 422 `invalid_spec` |
| `Score`, `ComparedArea` | `counted`, `present` | int | yes | How many things count in the spec, and for how many the area has a figure. Both 0 for an area that is not ranked |
| `RankedArea` | `strip` | list of `StripMark` | yes | First the vibes of the spec, heaviest first, then by id, four at most. Then up to two others that hold the `strip` flag and sit in band 1 or 5, then 2 or 4, by id. Since engine 1.7.0, of those others a vibe that runs one way is shown only in band 4 or 5, and a vibe whose recipe holds recorded crime is never among them (contract 6.7). A vibe with no band is left out |
| `StripMark` | `tag_id`, `band`, `spread_low`, `spread_high`, `asked`, `toward`, `fact_id` | id, int, int, int, bool, `high`, `low` or null, str | yes | `toward` is `null` when `asked` is false. `fact_id` is the `tag` fact |
| `Contribution` of `commute` | `present` | bool | yes | True when any leg has a time (5.1) |
| `AreaData` | `portrait` | `Portrait` | yes | Built with no spec, so it is the same for everyone |
| `Portrait` | `scales`, `more`, `less`, `others`, `unplaced` | lists of `PortraitMark` | yes | The order and the two lists are vibes.md 5.1. Street character is last of the scales. Works and warehouses is never first of a list |
| `PortraitMark` | `tag_id`, `fact_id`, `figure_fact_id`, `parts` | id, str, str or null, list of `PortraitPart` | yes | `figure_fact_id` is the `feature` fact of the heaviest part that has a value |
| `PortraitPart` | `feature_id`, `hundredths`, `reading`, `fact_id` | id, int, `high` or `low`, str or null | yes | `fact_id` is `null` where the part has no figure |
| `AreaData` | `similar` | list of `Similar`: `area_id`, `fact_id` | yes | Five at most. Empty when likeness is unknown (5.5). Each `likeness` fact is in `facts` |
| `MetaData` | `features`, `tags` | | yes | With the fields above. `tags` holds the vibes the release carries |
| `MetaData` | `families`, `gritty_variant` | list of `family` and `label`; `a` or `b` | yes | The families in the order of the settings: "Streets and homes", "Pace and food", "Green", "Daily life" |
| `ServedLimits` | `reason_min_utility`, `trade_off_max_utility` | float | yes | 0.5 and 0.35, so the website holds no copy of either |
| `Unranked` | `reason` gains `character_unknown`. New field `missing` | enum, list of str | yes | Added by the mending. An area with a figure for under half of the character that counts is listed here and is in no result. `missing` names each thing it has no figure for, as a `Contribution` names them (contract 6.6 and 6.7) |
| `RankData`, `ShareData` | `areas_ranked`, `areas_listed` | int | yes | Added by the mending. How many areas are ranked, and how many of them the answer holds in full (contract 9.2) |
| `CompareRow` | `place` | `NamedPlace` or null | yes | Added by the mending. A comparison has one row for each journey, and this is where the row's journey is to (contract 9.2) |
| `Suggestion` | `note` | str | yes | Added by the mending. What Burro cannot do, or that a choice counts recorded crime. Often empty. A suggestion with a note is never added with others at one press (contract 8.2) |

### 2.2 Facts and the explanation

| Fact | Change |
|---|---|
| `tag` | One for each vibe of the release, placed or not. Slots `label`, `band`, `low_end`, `high_end`, `compared`, `span`, `spread_low`, `spread_high`, `known`, `parts`, `judgement`. `as_of` is the span of the vintages of the parts that have a value, never `built_at`. `judgement` is the fixed line "The recipe is Burro's own. The weights are a judgement." The source line reads "Burro's recipe. Made from data published by:" and then the sources |
| Template `vibe` | "{label}: band {band} of 5, counted from {low_end} to {high_end}, among the {compared} areas compared in this release. {partly} Parts dated {span}. {judgement}" For a one-way vibe: "counted from least to most". `{partly}` is empty unless the band rests on part of the recipe, and then reads "Worked out from 3 of its 5 parts, 70 of 100 by weight." |
| Template `vibe_range` | Used when the spread is three bands or more. "{label}: varies within this area, from band {spread_low} to band {spread_high} of 5, counted from {low_end} to {high_end}. {partly} Parts dated {span}. {judgement}" |
| A vibe in an explanation | Said in short: the sentence ends after `{partly}`. The dates and the line about judgement stay in the fact, and the website shows them with the source (contract 7.3) |
| Template `vibe_unknown` | Used when `band` is `null`. "Burro cannot place {name} on {label}. Parts with a figure in this release: {known} of {parts}." It holds no figure about the place |
| `feature` | Slots gain `band`, and `standing_worse`, `comparative_worse`, `pct_worse`. `standing` is now said from the better side (5.3) |
| `travel` | Slots gain `limit` and `margin` when the spec sets a cap. New templates `travel_pt_over` and `travel_other_over` end ", {margin} minutes over the {limit} you set." |
| `missing`, for a leg | Key `commute.<place_id>.<mode>`. Template `missing_journey`: "There is no journey time from {name} to {place} in this release, so that journey was left out of the score." One for each leg with no time |
| `likeness`, new kind | Key is the other area's id. Template `likeness`: "{name} is in the same band as {other} on {same} of the {measures} measures compared, and least alike in {family}." Where the two differ in nothing, `likeness_same` |
| The verifier | It refuses "best", "top", "highly rated", "acclaimed", "friendly", "close-knit", "vibrant", "up and coming", "gritty" and "polished". The name of an end passes only from a fact's slots |
| `Explanation` | The same shape. `missing` holds a sentence for each leg with no time. `trade_off` is `null` more often (5.2) |

### 2.3 One example of each

```json
{"manifest.json": {"release_id": "syn-2026-09-23-01", "schema_version": 2, "catalogue_version": 3, "gritty_variant": "b", "synthetic": true}, "tags.json row": {"area_id": "syn-n0007", "tag_id": "pace", "raw": 0.769, "score": 73.8, "coverage": 1.0, "band": 4, "spread_low": 3, "spread_high": 5}}
{"Tag, in the meta record": {"tag_id": "pace", "label": "Pace", "short_label": "Pace", "family": "pace_food", "shape": "scale", "low_end": "Calm", "high_end": "Buzzy", "meaning": "How much there is to eat, drink and go out to within a walk of homes", "cannot_see": ["One street or one home. An area is many streets.", "How a weekday differs from a weekend."], "lens": true, "strip": true, "table": true, "shelf_word": "lively", "shelf_toward": "high", "shelf_order": 3, "terms": [{"feature_id": "venue_evening", "hundredths": 35, "reading": "high"}]}}
{"TagWeight, in the spec": {"tag_id": "pace", "weight": 0.5, "toward": "low", "provenance": "stated"}, "TagEdit": {"action": "nudge", "tag_id": "pace", "value": 0.0, "step": "up_large", "toward": "low", "provenance": "stated"}}
{"Score": {"area_id": "syn-n0001", "score": 78.1, "counted": 5, "present": 4}, "StripMark": {"tag_id": "pace", "band": 1, "spread_low": 1, "spread_high": 1, "asked": true, "toward": "low", "fact_id": "syn-n0001/tag/pace"}}
{"tag fact, in an explanation": {"fact_id": "syn-n0007/tag/pace", "kind": "tag", "template": "vibe_range", "as_of": "2025", "slots": {"label": "Pace", "spread_low": "3", "spread_high": "5", "low_end": "Calm", "high_end": "Buzzy", "span": "2025"}}}
{"Similar, in the profile": {"area_id": "syn-n0024", "fact_id": "syn-n0022/likeness/syn-n0024"}, "PortraitMark": {"tag_id": "foodie", "fact_id": "syn-n0022/tag/foodie", "figure_fact_id": "syn-n0022/feature/venue_food_drink", "parts": [{"feature_id": "cuisine_variety", "hundredths": 20, "reading": "high", "fact_id": null}]}}
{"place, in routes 1, 2, 9 and 10": {"place_id": "syn-p0021", "name": "Cindermoor Works", "kind": "district"}}
```

### 2.4 What becomes of today's 23 features and 12 tags

| Today | Becomes |
|---|---|
| The 23 features | All kept, with their ids, labels, units and polarity. Each gains the fields of 1.2. `venue_independent`, `water_access`, `station_lines`, `air_no2`, `university_proximity` and the two attainment features are in no recipe, and are weighed as features |
| `leafy`, `village_feel`, `family_amenities`, `foodie`, `quiet_residential` | Kept, with the recipes of 1.1. `foodie` is labelled "Food and drink" and `quiet_residential` "Quiet streets" |
| `buzzy`, `evening_venues`, `historic_character` | Retired. The Buzzy end of `pace`, and the Historic end of `built_age` |
| `creative`, `strong_high_street`, `near_universities`, `waterside` | Retired. Their words weigh one feature each (1.4) |
| New ids | `pace`, `built_age`, `homes`, `parks_close_by`, `everyday_on_foot`, `works_warehouses`, `street_character`. A retired id is never reused. No share outlives a restart and no real release exists, so nothing stored names one |

## 3. The routes

No route is added and none is removed. "More like this" is the field `similar` of route 6. Routes 5, 8 and 12 gain no field. Route 5 changes its cache header with routes 4, 6 and 11 (gap 15).

| # | Route | Gains |
|---|---|---|
| 1 | `POST /v1/interpret` | `suggestions`, each with its `note`, `unread`, `places`. The status `suggest`. The second notice text. `tenure_from` moves as gap 20 asks |
| 2 | `POST /v1/rank` | `places`. `counted` and `present` on each `Score`. `strip` on each `RankedArea`. It takes `toward`. `areas_ranked` and `areas_listed`. `missing` on each `Unranked` |
| 3 | `POST /v1/explanations` | `spec_hash`. `facts` also holds the `tag` fact of every strip mark of the areas explained. Sentences by role (5.3). The second threshold (5.2) |
| 4 | `GET /v1/areas` | `bands`: a list of `tag_id` and `marks`, one for each vibe that holds `lens`. A mark is `area_id`, `band`, `spread_low`, `spread_high`. It is one cached answer, so the service is never told which word was pressed |
| 6 | `GET /v1/areas/{id_or_slug}` | `portrait`, `similar`. `facts` holds a `tag` fact for every vibe, and the `likeness` facts |
| 7 | `POST /v1/compare` | `character`: a list of `tag_id` and `marks`, for each vibe that holds `table`, in shelf order, and each mark names its `fact_id`. `counted` and `present` on each `ComparedArea`. Every cell of a row is said from one side. One row for each journey, with its `place`, and a cell for every area |
| 9, 10 | `POST /v1/shares`, `GET /v1/shares/{share_id}` | `places`, of the spec as stored. Route 10 gains all that route 2 does |
| 11 | `GET /v1/meta` | The fields of `MetaData` and `ServedLimits` in 2.1 |

| Gap | What the API now returns | The website then deletes |
|---|---|---|
| 1 | `places` in the `data` of routes 1, 2, 9 and 10, required: one `{place_id, name, kind}` for each commute of the returned spec, in the spec's order. `name` is the release's own name. It is handled as a `place_id` is, and is in no log | "Place 1", `PLACE.unnamed` and its hint. The test marked as failing passes |
| 14 | `spec_hash` in the `data` of route 3, required: the hash of the spec as sent | Its own record of which spec it asked about |
| 15 | Routes 4, 5, 6 and 11 send `Cache-Control: no-cache` with the `ETag` they carry, and answer 304 to an `If-None-Match` that names the loaded release | Nothing. A browser now asks each time |
| 16 | `short_label` on every `Metric` and `Tag` | The switch is named by `short_label`. The line about which way counts stays |
| 17 | One: both sides of a standing in the fact, and a reason and a trade-off each said from its own (5.3). Two: `limit` and `margin` on a `travel` fact. Three: as now. Four: `TRADE_OFF_MAX_UTILITY` of 0.35 (5.2), served in `limits` | Its own figure for the half. The second test marked as failing passes |
| 18 | `counted` and `present` on every `Score` and `ComparedArea` | `basedOn` works it out for the first 20 only. It now reads the two fields for every area |
| 19 | One: the grammar of 4.1 reads cases a, b and c whole. Two: `unread` on route 1 (4.3) | `src/lib/search/unread.ts` and its test |
| 20 | A `BudgetEdit` `set` that names a tenure, and is applied, sets `tenure_from` to its provenance whether or not the tenure moves, and is `changed` true. `spec_hash` does not move | `tenureSaid` and `SaidByThePerson` |
| 21 | Two fixed texts, the same for everyone. Where an edit of the answer changed the spec: the text of today. Otherwise: "Burro ranks places by what is there, such as schools, parks, venues and transport, and never by who lives there. Nothing you typed has changed your search." | `NOTICE.nothingElse` |
| 22 | The journeys are scored on the legs that have a time, and each leg with none has its own sentence (5.1) | `journeysLeftOut` says its line only where no leg has a time |

## 4. The reader

### 4.1 The grammar of a plain prompt

A prompt is plain when the whole of it is made by the grammar below. Words are matched as contract 8.2 matches them: in lower case, token by token, a name only as the whole of a name. `{ }` is none or more, `[ ]` is none or one. `article`, `count`, `good`, `important` and `courtesy` are the words of `_BARE`, of `_COUNTED`, and of the groups of `PLAIN` for good opinion, for how much a thing counts and for courtesy. `segment` is a kind of home of contract 2.5. `after-turn` is a phrase of `TAKES_OFF_AFTER` or `TURNS_DOWN_AFTER`.

```
prompt    = sentence { stop sentence } [ stop ]
stop      = "." | "!" | a line break
sentence  = courtesy | [ opening ] item { joiner item } [ "please" | "thanks" | "too" | "as well" ]
opening   = [ speaker [ wish ] [ "to" ( "live" | "be" | "find" ) ] ] [ somewhere [ "that is" | "that has" | "with" ] ]
speaker   = "I" | "we" | "I'm" | "we're" | "I'd" | "we'd"
wish      = "want" | "need" | "would like" | "would love" | "like" | "love" | "am after" | "am looking for"
somewhere = "somewhere" | "a place" | "an area" | "a neighbourhood"
joiner    = "," | ";" | "and" | "or" | "but" | "plus" | "also" | "with" | "," and then one of these words
item      = want | unwant | tenure | budget | home | journey | rule | people | no-measure
want      = [ degree ] [ article ] thing [ "nearby" | "close by" ] [ "would be" good | "is" important ]
unwant    = turn [ article ] thing | thing after-turn
thing     = a phrase of LEXICON | a label or short label of route 11 | the name of an end of a scale
degree    = a phrase of SMALL_STEP, LARGE_STEP or ESSENTIAL
turn      = a phrase of TURNS_FIRMLY, TURNS_SOFTLY, TAKES_OFF, TURNS_DOWN or TROUBLES
tenure    = [ speaker ] ( "rent" | "renting" | "to rent" | "buy" | "buying" | "to buy" )
budget    = [ tenure ] [ home ] [ [ "can" ] ( "pay" | "spend" ) | [ "my" | "our" ] "budget" [ "is" | "of" ] ] [ cap ] money [ period ] [ "max" ] [ "for" home ]
money     = "£" number [ "k" | "m" ] | number ( "k" | "pounds" | "quid" ) | number period
period    = "a month" | "per month" | "pcm" | "pm" | "monthly"
home      = [ article ] ( count ( "bed" | "bedroom" | "bedrooms" ) | segment ) [ "flat" | "house" | "home" | "place" ]
journey   = cue place [ "and" wish "to get there" time ] [ mode ]
          | time ( "to" | "from" | "of" ) place [ mode ]
          | [ speaker wish "to" ] ( "get to" | "reach" ) place [ "in" ] time [ mode ]
cue       = a phrase of _EXPECTS_A_NAME, which is said of the speaker alone: "work at", "study at", "commute to"
time      = [ cap ] number ( "minutes" | "mins" | "min" )       cap = a phrase of CAPS or CAPS_FIRMLY
mode      = "by bike" | "cycling" | "on foot" | "walking" | "by tube" | "by train" | "by bus" | "by public transport"
place     = the whole of a name or an alias of a place of the release, as typed, side by side
rule      = ( "not" | "not in" | "avoid" | "anywhere but" | "only" | "only in" | "must be in" ) the whole name of an area
people    = [ "lots of" | "many" | "full of" ] a phrase of POLICY_LEXICON [ "like me" | "like us" ]. It makes no edit and sets the notice
no-measure = a phrase for what Burro has no measure of. It makes no edit and adds its category to unmet
```

| Rule | Detail |
|---|---|
| All or nothing | One token that the grammar does not place makes the whole prompt not plain, whichever sentence it stands in. A question mark anywhere does too. Nothing is then applied, not even a budget |
| One turn, one thing | A turn governs the thing straight after it, and the things joined to that by "or". A thing joined to a turned thing by a comma or "and", with nothing said of it but its name, makes the prompt not plain, because the reader cannot say whether the turn reaches it. Today it is left alone. "But", a wish of the speaker's and a word of the thing's own, such as "near" or "good", begin a new wish, as contract 8.2 rule 6 |
| Never both | A thing that is both wanted and turned away in one prompt makes it not plain |
| A nuisance | It is a thing only under a turn, or in a phrase that says low: "less noise", "low crime", "clean air". Named alone, or liked, it makes the prompt not plain |
| A turned end | "Not buzzy" is Pace towards Calm. In variant A, "not gritty" is `upkeep` in `unmet` and no edit |
| "There" | It stands for the one place named earlier in the same sentence, and for nothing else |
| The edit | Where a prompt is plain, each item makes the edit contract 5.2 and 8.2 give it, with `rests_on` |
| What the mending changed | An everyday hedge is a word of degree: "fairly", "quite", "pretty", "reasonably" and "relatively" are a small step, where each made a prompt not plain. What is said after the last thing of a turned list, "nearby", "on my doorstep", never begins a new wish: after "or" the turn carries, and after a comma or "and" the prompt is not plain. Minutes said apart from a place keep how they are travelled and whether they are a limit. The name of a scale names no end, so it is offered with both. A word that is only read into a vibe that holds recorded crime is offered, and never applied. Contract 8.2 has each |
| Widened, and kept narrow | `tenure`, `budget`, `home` and `journey` are widened. They are numbers, names of the release and a closed list of words, so a wrong reading is a wrong number and not a wish turned round. `thing` is kept narrow: a wish about character is read only from a phrase of `LEXICON`, and a new phrase is a case in `evals/` first |

### 4.2 Twenty prompts that are read, and twenty that become suggestions

| # | Plain, and read | As | Not plain | Because | Offered, with the directions a person may choose |
|---|---|---|---|---|---|
| 1 | leafy and quiet, near a park | `leafy`, `quiet_residential` and `park_proximity` up | Pubs are so noisy | A nuisance is only named | Pubs and bars: more, less. Transport noise: less |
| 2 | I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works. | Budget: rent, 1,500, `bed_1`, firm, since "up to" says the most that can be paid. A journey to Cindermoor Works | Some want pubs | The subject is not the speaker | Pubs and bars: more, less |
| 3 | I work at Cindermoor Works and want to get there within 35 minutes. A park nearby would be good. | A journey, 35 minutes, firm, since "within" makes minutes a limit. `park_proximity` up | My street is lively and I need peace and quiet | It says where the person lives now | Pace: towards Buzzy, towards Calm. Quiet streets: more |
| 4 | I need to get to Cindermoor Works in under 40 minutes | A journey, 40 minutes | I want pubs. Actually I do not want pubs. | Wanted and turned away | Pubs and bars: more, less, once |
| 5 | Somewhere lively, 30 minutes to Pellam Cross by bike | `pace` towards Buzzy, assumed. A journey by bike, 30 minutes | My partner works at Pellam Infirmary | The third person | A journey to Pellam Infirmary: more |
| 6 | within 40 minutes of Pellam Infirmary on foot | A journey on foot, 40 minutes | leafy, quiet, and nothing like where I live now | A comparison | Leafy: more. Quiet streets: more |
| 7 | Buying a terraced house under £450k | Budget: buy, `terraced`, 450,000, soft | Moving next month. Somewhere leafy. | The first sentence | Leafy: more |
| 8 | We need two bedrooms, no more than £2,000 pcm | Budget: `bed_2`, 2,000, hard | I used to love pubs | The past | Pubs and bars: more, less |
| 9 | My budget is £1,800 a month | Budget: 1,800, soft | quieter than where I live now | A comparison | Quiet streets: more |
| 10 | no pubs | `venue_evening`, direction less | I can't live without a park | Two turns over one thing | Nearer a park: more, less |
| 11 | not buzzy | `pace` towards Calm | Could you find me somewhere with good pubs? | A question | Pubs and bars: more, less |
| 12 | somewhere calm | `pace` towards Calm, assumed | the kids need a playground | The subject is not the speaker | Nearer a play space: more |
| 13 | period houses, near a big park | `built_age` towards Historic, assumed. `parks_close_by` up | ideally near a park | A word that weakens the whole wish | Nearer a park: more, less |
| 14 | walkable, with a food shop nearby | `everyday_on_foot` and `grocery_walk` up | I like noise | A nuisance that is liked | Transport noise: less |
| 15 | a house with a garden | `homes` towards Houses, assumed | no parks and playgrounds | A list after a turn | Nearer a park: more, less. Nearer a play space: more |
| 16 | less noise and clean air | `noise_exposure` up. `air_no2` up, assumed | We both work in Pellam Cross | A word that is not known | A journey to Pellam Cross: more |
| 17 | I don't care about parks | `park_proximity` taken off | Happy anywhere as long as it is under £1,800 a month | A condition | A budget of £1,800 a month: more |
| 18 | avoid Cindermoor | An `exclude` rule | cross Cindermoor off my list | Words that are not known | Cindermoor: more, which looks only there, and less, which leaves it out |
| 19 | Somewhere leafy with lots of young professionals like me | `leafy` up. The neutral notice. Status `policy_redirect` | a lively high street with plenty going on | Words that are not known | Pace: towards Buzzy, towards Calm. Nearer a high street: more, less |
| 20 | somewhere a bit gritty, near a park | B: `street_character` towards Gritty. A: `works_warehouses` up, assumed, with the word. Both: `park_proximity` up | boozers on every corner would finish me off | Nothing is known | Nothing. `unread` is the whole text, and the status is `ok` |

"Ignore" is offered with every suggestion. "Less" of a thing with one direction takes its weight off, and is offered only where the spec holds a weight for it: a renter's default weighs parks, so row 15 offers it for a park and not for a play space. A choice is never offered if its edit would change nothing or would be rejected. All forty were read through the API on 2026-09-24 and came to what the table says.

What the mending added to what is offered, each with a `note` that says what Burro cannot do or that the choice counts recorded crime (contract 8.2):

| Typed | Offered | Applied |
|---|---|---|
| safe, safer, safety, feel safe, unsafe, dangerous | Less recorded violence and robbery. Less recorded burglary and theft. Each has one way to be wanted, and says that it counts recorded crime | Nothing |
| smart, well kept, edgy, raw, and the name "street character" | Street character, with both its ends, and the note that it counts recorded crime | Nothing |
| gritty, polished | Nothing: each is the name of an end, and is applied as any end is | Street character towards that end |
| gym, leisure centre, sports centre, swimming pool | More to do in parks, as the nearest Burro can count | Nothing |
| community, sense of community, community feel, neighbourly | Village feel, as the nearest | Nothing |
| garden, big garden, private garden, outdoor space | More gardens, which is the garden land of an area, as the nearest | Nothing |
| cheap, inexpensive, cheap rent, low rent | Nothing. `unmet` holds `affordability_verdict`, and the person is told | Nothing |

### 4.3 The suggestion, the unread stretch, and the status

| Record | Field | Type | Required | Notes |
|---|---|---|---|---|
| `InterpretResult`, `InterpretData` | `suggestions` | list of `Suggestion` | yes | Empty for a plain prompt. In the order the things stand in the text. One for each thing, however often it is named |
| | `unread` | list of `Span` | yes | Each stretch of the text that no edit, no suggestion, no notice and no `unmet` category but `other` rests on, in order. Two that touch are one. `unmet` holds `other` exactly when it is not empty. Words that say what the search already holds, as "a one bed flat" does for a renter, are heard and are not among it |
| `Suggestion` | `target` | str | yes | `feature:<id>`, `tag:<id>`, `budget`, `tenure`, `commute` or `area` |
| | `label` | str | yes | API text: the `short_label` of the thing, or the release's name of the place or the area. Never the text |
| | `spans` | list of `Span` | yes | Where the words stand. At least one |
| | `choices` | list of `Choice` | yes | Two or three, in the order `more`, `less`, `ignore`. `ignore` is always last |
| | `note` | str | yes | Fixed text of core's own, and empty for most. A suggestion with a note is chosen by its own label, and is never taken by a button that adds several at once |
| `Choice` | `direction` | `more`, `less` or `ignore` | yes | For a scale `more` is towards `high_end`. For a journey, a budget and a tenure `more` adds it, and there is no `less`. For an area `more` looks only there and `less` leaves it out |
| | `label` | str | yes | API text: "Fewer pubs and bars", "Towards Calm", "Add a journey to Pellam Infirmary", "Leave it out" |
| | `operations` | `Operations` | yes | What the website sends to route 2 if it is chosen. Every edit is `ui_edit`. Six empty arrays for `ignore`. It holds only what the label says: a budget holds the amount, and the size of a home is a suggestion of its own |
| `Span` | `start`, `end` | int | yes | Code points into the text as sent, `end` not included, as `rests_on` counts |

Suggestions and `unread` are served to the caller, who holds the text. They are never logged, never kept about a call and never stored in a share, and no log field is added. No other route takes or returns them. The model-backed reader serves the rule-based reader's suggestions and `unread` as they are, and is otherwise unchanged. The example is "Pubs are so noisy", cut short: one suggestion of two, and only the array that is not empty in each `operations`.

```json
{"status": "suggest", "unmet": ["other"], "unread": [{"start": 5, "end": 11}], "notice": "none", "places": [], "suggestions": [{"target": "feature:venue_evening", "label": "Pubs and bars", "spans": [{"start": 0, "end": 4}], "choices": [
  {"direction": "more", "label": "More pubs and bars", "operations": {"weight_ops": [{"action": "nudge", "feature_id": "venue_evening", "value": 0.0, "step": "up_large", "direction": "more", "provenance": "ui_edit"}]}},
  {"direction": "less", "label": "Fewer pubs and bars", "operations": {"weight_ops": [{"action": "nudge", "feature_id": "venue_evening", "value": 0.0, "step": "up_large", "direction": "less", "provenance": "ui_edit"}]}},
  {"direction": "ignore", "label": "Leave it out", "operations": {}}]}]}
```

`InterpretStatus` gains `suggest`. The status is the first that applies in the order `off_topic`, `policy_redirect`, `clarify`, `suggest`, `ok`.

| The prompt | `status` | `operations` | `suggestions` | `unread` | `notice` |
|---|---|---|---|---|---|
| Plain, and every name is whole | `ok` | Every edit | Empty | Empty | `none` |
| Plain, and the words after a cue are the whole of no name | `clarify` | Every edit. The one asked about holds an empty id | Empty | Empty | `none` |
| Plain, with a phrase about who lives somewhere | `policy_redirect` | Every other edit | Empty | Empty | `neutral_places`, the first text if an edit changed the spec |
| Plain, and all of it is what Burro has no measure of | `ok` | Empty | Empty | Empty | `none`. `unmet` names each category |
| Not plain, and something was noticed | `suggest` | Empty | One or more | What is left | `none` |
| Not plain, with a phrase about who lives somewhere | `policy_redirect` | Empty | Whatever was noticed | What is left | `neutral_places`, the second text |
| Not plain, and nothing was noticed | `ok` | Empty | Empty | The whole text | `none`. `unmet` holds `other` |

### 4.4 What changes in `evals/`

| Change | Detail |
|---|---|
| A new outcome, `suggested` | The reader moved nothing, and every thing the case asks for is offered, with the direction asked for among its choices. It is neither correct nor reversed. The order, worst first: reversed, unasked, failed, declined, in part, suggested, correct |
| What a suggestion cannot be | Reversed or unasked, because nothing moved. A suggestion that offers only the other direction is `declined` |
| A case that is right to leave alone | It stays `correct` when nothing moved. Suggestions made there are counted on a line of their own: "offered where nothing was asked" |
| The report | A column for `suggested`. The line for cases that ask for something reads "read or offered" |
| A new key, `plain` | Optional, `true` or `false`. `true` says the prompt is plain by 4.1 and must be applied. `false` says it is not, and that any edit applied is unasked |
| The floor | `rule` gains `plain_correct_share`: the least share of cases with `plain` true that are correct. It starts at 1. `correct_share` is measured again, because a prompt of several sentences with one that is not plain is now `suggested`. No case may be reversed, as now |
| New cases | `cases/plain_prompts.jsonl`: the twenty of 4.2 and cases a, b and c of web gap 19. `cases/suggestions.jsonl`: the twenty of 4.2, with the four sentences of ADR 0012. Each vibe of the committed release gets three cases, from vibes.md 2.4 where it has them. The scorer reads the committed release, which is variant B, so the words of variant A are held by core's own tests |
| Cases that name a retired tag | `tag:buzzy` becomes `tag:pace`, and so on by 2.4. The sentence is never changed. Each change is listed in the commit |
| The baseline | `baseline/rule.json` and `BASELINE.md` are written again, with the date, the engine version and the hash |

## 5. The engine's rules that change

| Rule | Case | What the engine does |
|---|---|---|
| 5.1 Journeys | Every leg has a time | As now |
| | Some legs have a time | `commute` is present. With `slowest` its utility is the lowest among the legs that have a time, and with `mean` their mean. One `missing_journey` sentence for each leg with none |
| | No leg has a time | `commute` is not present. One `missing_journey` sentence for each leg |
| | A firm limit on a leg with no time | It is listed in `untested_filters`, as now. The journey is a reason only when every leg has a time and is within its cap |
| | Check | With flexible caps of 35 minutes to Cindermoor Works and 40 to Wexmoor University, Gorsebeck is 63 minutes from the first and has no time to the second. Its journeys now score 0, and it no longer ranks first: it is 20th of 21, with a fit of 11 |
| 5.2 Thresholds | `REASON_MIN_UTILITY`, 0.5 | Unchanged. A reason is worth this or more and is no shortfall |
| | `TRADE_OFF_MAX_UTILITY`, 0.35 | A trade-off is the present component that loses most among those worth less than this, and those that fall short: a home over budget, a leg over its cap. Where none qualifies, `trade_off` is `null` |
| | Between the two | Neither a reason nor a trade-off. It is in the working of a result and nowhere else. Check: a walk of 5 minutes to a station, worth 0.48, is no longer a trade-off |
| | `NEVER_A_TRADE_OFF` | Added by the mending. A walk, a time or a distance at or under its figure is never a trade-off, however many areas are closer: 10 minutes to a station, a food shop, a surgery or a pharmacy, 800 m to a park or a play space, 1,600 m to a large park or a campus (contract 7.5). A walk of 7 minutes to a station was given as what an area gives up |
| 5.3 The side of a role | A reason | Said from the better side for that thing in the spec: its polarity, or the spec's `direction` where the polarity is `either`. The share is of the areas that do strictly worse. Slots `standing`, `comparative`, `pct` |
| | A trade-off | Said from the worse side. The share is of the areas that do strictly better. Slots `standing_worse`, `comparative_worse`, `pct_worse` |
| | Routes 6 and 7 | `standing`. Route 6 has no spec, so the side is the polarity's, and the side of more where it is `either`. Route 7 takes the side from the spec, the same for every cell of a row |
| | Always | Each share is rounded down, and areas that are level are counted and said, as contract 7.3. Where the share on the side asked for would be 0, the `level` clause stands. A vibe has the band sentence of 2.2, the same in every role |
| 5.4 A scale | A one-way vibe, or a scale towards `high` | Utility is `score / 100` |
| | A scale towards `low` | Utility is `1 - score / 100`. The same spec with `toward` turned reverses the order on that vibe alone |
| | Always | A vibe counts once, with one weight and one end. The band and the spread are for showing and never change a rank. An area with no `score` drops the vibe and its weights are rebalanced, as now |
| 5.5 Likeness | What it may use | `similar(release, area_id, n=5)` is a pure function of the release, in a new module of core. It uses the features with `in_likeness` true that the release carries: 23 here. Each once, however many recipes hold it |
| | What it may never use | A feature of `kind` `nuisance` or `on_request`. One that `describes` `events`. Cost, a journey, a vibe's own score. `homes_flats`, `homes_density`, `private_outdoor_space` and the school features, which wait for an audit. Anything about who lives somewhere: there is no such feature |
| | Distance | The band of a part is `band_of` over the values of the rankable areas, with no polarity applied. Within a family, the distance is the mean, over the parts both areas have, of the difference in band, divided by four. Across the families that have such a part, it is the mean. 0 is the same band on every part |
| | Too little known | If either area has a figure for under 60% of the parts, likeness is unknown: `similar` is empty, and no `likeness` fact is made |
| | Which areas, and the sentence | The five rankable areas in the same band on the most measures, which is the count the sentence gives. Where two share as many, the one at the least distance, and then by `area_id` (contract 6.9). It was by distance alone, so counts read 10, 10, 5, 7, 8. Never the area itself. `same` counts the parts in the same band, `measures` the parts both have. `family` is the label of the family with the greatest distance, the first in the order of the settings on a tie |

| 5.6 Character | How much of what was asked of the place must be known | Added by the mending. The character of a search is every feature and vibe it requests: all but the journeys and the budget. An area with a figure for under half of it, by weight, is not ranked, whatever is known of its journeys and its cost. It is `unranked` with `character_unknown` and says what it lacks (contract 6.6). A default counts as character |
| | Check | A job at Cindermoor Works, leafy, quiet, more pubs and £1,600 a month: Otterby Fields was first with a fit of 88 on 4 of 11. It is now in no result, and is listed apart with the seven things it has no figure for |
| 5.7 A band on part of a recipe | What is said | Added by the mending. A band that rests on part of its recipe says how many parts and what share, in the fact and in the sentence (contract 7.3) |
| 5.8 What a release must hold to | Three more rules | Added by the mending. A release is refused where a percentile parts from its value, a raw value from its recipe, or a score from its raw value (contract 2.8) |

## 6. The screens

(A) is API text and (S) is site copy. Heights are in CSS pixels, desktop then phone. The map is beside the list on a desktop. On a phone the first result stands directly after what Burro understood, whole on the first screen, and a strip of the map, 240 high, stands after it, with the whole map one press away. The search page as it is built is described in [web.md](web.md), sections 1, 3, 4, 5.2 and 6, which is right where this table and it disagree. `/methods` lists each vibe with its recipe, its ends and what it cannot see, from route 11. `/vibes` was added by the mending: it sets every vibe side by side as a small map, and then lays each out with its map, both its ends, its recipe and what it cannot see.

| Screen | On screen, in order | Each press | Height |
|---|---|---|---|
| Search, before a search | The banner (S). The box and "Search" (S). The shelf: seven words as buttons (A, `shelf_word`), then "more" (S). Rent or buy, and a place to reach (S). Three examples (S). The map in one colour | A word opens its card in place: label, meaning, recipe, what it cannot see (A), and "Add to my search" (S). The map is coloured by that vibe in five bands, from route 4, with a legend that names the ends (A). "Add to my search" sends one `TagEdit` to route 2 with `shelf_toward`. "more" shows the other four words | One screen on each. The shelf is two rows at most |
| Just after a search | The banner, which is one line on a phone. The box, on one line. One line that says what happened (S, with counts), and which of a journey, a budget and the place counts most. The chips, which wrap and are never cut: vibes first, six at most, the usual settings last, and the rest behind "+N" (S). Suggestions, if any. Then the first result, the ways to the settings and to sharing, the map on a phone, and the rest of the first five results in short form, rows for results 6 to 10, and "Show 10 more" (S). On its line, a button that says how many areas are not ranked, closed (S, with the API's count). Settings, sharing and the compare tray are closed | "Show 10 more" shows rows 11 to 20, and then one line says how many of the areas ranked are listed (S, with the API's counts). The button of the areas that are not ranked opens to each by name, with why and what it has no figure for (A, and S for the reason). A chip opens its control in place. A chip of a scale reads "Pace: towards Calm" (A), and "Turn" (S) sends a `set` with the other end. A chip of a vibe whose recipe holds recorded crime says "counts recorded crime" (S) | The first result is whole on the first screen. Measured on 2026-09-24: on a phone it starts at 322 to 476 and ends at 575 to 802, of 844. The page is within the limits of 2,700 and 4,220 |
| A result, short | Rank, name and borough (A). The name leads to the page of the area. Fit as "78 of 100" and, where it rests on part of what counts, what it is based on, from `counted` and `present` (S, with the API's counts). The strip: one mark for each `StripMark`, with its vibe's name and ends (A). The first reason and the trade-off, one sentence each (A), or "No trade-off found" (S). A vibe is said in short. "Show the working", "More like this", "Compare" (S) | A mark shows its vibe's fact and "Source" in place. "Source" on a sentence about a vibe shows its date, whose recipe it is and that the weights are a judgement. "Show the working" opens the result. Results 6 to 20 are rows: rank, name, fit, what it is based on, the strip | Hoped for: 148 and 196 at most, and a row of 44 and 56. Not met. Measured on 2026-09-24, before a vibe was said in short: a card is 186 to 264 and 253 to 336, a row 66 to 115 and 90 to 160. So ten results are shown at first |
| A result, opened | Under the short form: every reason, what has no figure, each journey with "within" or "over", the cost range, the score breakdown, and "Source" on every line, as web.md section 4 | "Source" opens the source, the date and "Made-up data" in place. Opening one result closes no other | No limit. It is one press away |
| Suggestions | Under the chips, the heading "Burro was not sure. Choose what to add." and one line that says why Burro asks (S). Where two or more things in sight have one way to be wanted, one button that adds them all (S). For each suggestion one button for each choice (A), and its `label` where it could be meant two ways. "Show in the box" (S) where `unread` is not empty | A choice sends its `operations` to route 2, and its suggestion goes. "Leave it out" sends nothing, and the suggestion goes. "Show in the box" selects the spans in the box. The words are drawn nowhere else. Every suggestion goes when the box changes or a sentence is sent | Four are shown, and with them every other thing that has one way to be wanted. The rest, which are questions, are behind "Show all". With suggestions pending beside a ranking, the first result still begins on the first screen of a phone: at 633 to 734, measured on 2026-09-24 |
| Settings, by vibe | Closed at first. Opened: "Budget and home", "Journeys", one group for each family (A, `families`), "Air and noise" for the two features that belong to no family, and "Recorded crime", each closed. That is eight groups, where seven were specified. In a family: one row for each vibe, with its name, a slider, and for a scale its two ends (A). Under a vibe, "Made of" (S): its parts, each with a switch and a slider. A feature in no recipe is under "Other things that count" (S) in its family | A slider sends one `TagEdit` on release. The slider of a scale rests in the middle, which is no weight, and moves towards either end. A part's switch is a `WeightEdit`, as now | With the settings open and no group open, 12 controls at most are on screen. Today there are 100 |
| The area page | Name and borough (A). The portrait opens with "In short", five lines at most in words a person would use, each with one figure, and beside it "Where it is" (headings and the words for a band S, the rest A). Then the scales, "More than most here", "Less than most here", "Burro cannot place", each mark with its plain figure (headings S, the rest A). A band that rests on part of a recipe says so beside the band (A). What it cannot see, one line for each vibe shown (A). The nearest station (A). "More like this", recorded crime, noise and air, closed. Cost, stations, sources, as now | "Made of" on a mark opens its parts, each with its weight, figure, band, source and date, or "No figure in this data" (S). "Search for this character" (S) opens the search with the vibes of "More than most here", one edit each | The portrait is whole on the first screen of a desktop, and within two on a phone. The page reads with scripts off |
| More like this | Closed until pressed. The heading "Alike in streets, buildings and places" (S). Five areas, each with its `likeness` sentence (A) and a link to its page | A name opens that area's page. It starts no search in this slice | 5 lines |
| The comparison | The areas' names. Character rows first, from `character`: a scale is one line with a mark for each area. Then the rows by weight, with one row for each journey and the same destination across it (A). Beside each fit, what it is based on. An area that is not ranked says why in words | As now | No limit |

## 7. The order of work, and the seams

| Part | Owns | Takes, as a fixed interface | Hands over | Done when |
|---|---|---|---|---|
| E. Engine | `packages/core` but for the reader. Contract sections 2 to 7. ADR 0013 | This document | The records of section 2, `FEATURES`, `TAGS`, `tag_raw`, `percentile_of`, `band_of`, `rank`, `facts_for`, `explain`, `similar`, the portrait, `parse_release` | `make ci` |
| R. Reader | `interpret.py`, `vocabulary.py`, `evals/`. Contract section 8. ADR 0012, amended | From E: `TagEdit.toward`, the shape and the ends of a `Tag`, `MIXED_WORDS`, `apply()`. It asks the reducer whether a choice would change the spec | `RuleInterpreter.interpret()` with `suggestions` and `unread`. The scorer and the cases | `make ci`, and the scorer passes its floor |
| G. Generator | `packages/pipeline/.../synthetic`, `data/fixtures/synthetic` | From E: `FEATURES`, `TAGS`, `tag_raw`, `percentile_of`, `band_of`, and the records `Manifest`, `Metric`, `TagValue`. It works out no band of its own | The release of 2.1, in both variants | `make fixture`, then `make ci` |
| A. API | `services/api`, `contracts/openapi.json`. Contract sections 9 and 10 | From E and G: `open_release`, the fixture folder, and the functions E hands over. From R: `InterpretResult`, to which a route adds `places` and the notice text and nothing else. A route works out no score, band or sentence | The routes of section 3 | `make openapi`, then `make ci` |
| W. Website | `apps/web`. web.md | From A: `contracts/openapi.json` and the recordings. It writes no sentence, band or name about a place | The screens of section 6 | `make web-record`, then `npm run check`, then section 8 by hand |

| Step | Who | What | After it |
|---|---|---|---|
| 0 | E, with A | One change that holds names and shapes and no behaviour: every enum, every record field of sections 2 and 4.3, the rows of 1.1 and 1.2, and `make openapi`. New fields are served empty or `null` | Every name in this document is in code and in `contracts/openapi.json`. The four others start |
| 1 | E, R, G at once | E: the rules of section 5, the facts and the templates. R: the grammar. G: the 17 parts, the bands, the mixed area, variant A | Each passes its own tests on releases built in memory |
| 2 | G, then A | `make fixture`. Then the routes are filled | The API serves the committed release |
| 3 | W | It builds against the generated types and its own stand-ins from step 0, and against recordings once step 2 is done | The screens |
| 4 | W, then everyone | The recordings are made again. One visit is walked by hand | Section 8 |

## 8. Acceptance: ten minutes in a browser

Run the API on the committed release and the website against it. Make each check at 1440 by 900, and those marked P also at 390 by 844. Checks 7, 8, 12 and 13 name areas: E and G each hold them as a test on the committed release and on three other seeds. Checks 17 to 20 were added by the mending, and 21 to 24 by the last mend. Section 11 says what the first walk saw of checks 1 to 16.

| # | Do | Expect |
|---|---|---|
| 1 | Open `/` | The banner, the box, seven words, and the map in one colour. No result. P |
| 2 | Press "leafy" | The map is in five bands with a legend. A card gives the meaning, the recipe and what Leafy cannot see |
| 3 | Press "Add to my search" | A chip "Leafy". The first result is whole on screen with no scrolling. `document.documentElement.scrollHeight` is at most 2,700, and 4,220 on a phone. P |
| 4 | Start again. Type prompt 2 of 4.2 and search | Chips for renting, for £1,500 a month for one bedroom, and for Cindermoor Works by name. Nothing reads "Place 1". No line says a part was not read |
| 5 | Start again. Type "Pubs are so noisy" and search | No ranking comes. Two suggestions, and no chip for pubs. Press "Fewer pubs and bars": a chip comes, the suggestion goes, and the areas are ranked |
| 6 | Press "Show in the box" | "are so" is selected in the box. The words are nowhere else on the page |
| 7 | Start again. Type "not buzzy" and search, then press "Turn" on the chip | The chip reads "Pace: towards Calm", and Lantern Yard is not among the first ten. After "Turn" it reads "Pace: towards Buzzy", Pellam Cross is first and Lantern Yard second |
| 8 | Add Cindermoor Works within 35 minutes and Wexmoor University within 40, both flexible | Gorsebeck is not among the first five. Where it is listed, its journey to Wexmoor University reads as having no time, and its journey to Cindermoor Works as over the limit |
| 9 | Search "near a station". Read the first five results | Every reason is said in the better word, such as "closer", and every trade-off in the worse one. No walk of 5 minutes is a trade-off |
| 10 | Open the first result. Press "Source" on a reason | The working opens in place. The source, the date and "Made-up data" show |
| 11 | Open the settings | Eight groups, all closed, and 12 controls at most. Open "Pace and food": Pace has one slider with Calm and Buzzy at its ends |
| 12 | Open the page of Foxholt, then of Otterby Fields | Foxholt: Pace is drawn as a range, and reads "varies within this area". Otterby Fields: "Burro cannot place" for ten of the eleven vibes |
| 13 | Open the page of Thrushcombe. Press "More like this" | Five areas, each with one sentence that names a count and a family. The counts read 10, 9, 8, 8, 7. Wickerford is among them, the fifth |
| 14 | Compare three areas from their results | Character rows come first. Beside each fit is what it is based on |
| 15 | Type "somewhere a bit gritty". Then serve variant A, build the website again and repeat | B: a chip "Street character: towards Gritty, counts recorded crime". Pellam Cross is first and Lantern Yard second. "Source" on its sentence names the recorded parts. A: a chip for Works and warehouses, marked "assumed", that quotes "gritty", and the line that Burro has no measure of how clean a street is |
| 17 | Type "I have a job at Cindermoor Works, somewhere leafy and fairly quiet, not too far from a decent pub, about £1,600 a month" and search | It is read whole, with nothing to choose. Farrowmere is first. Otterby Fields is in no result. Under the list, "3 areas are not ranked" opens to it, with why and the things it has no figure for. P |
| 18 | Press "Show 10 more" | Twenty results, and the line "20 of the 21 areas ranked are listed here. The table of all areas holds every one." |
| 19 | Type "somewhere safe" and search | No ranking comes. Two offers, each of recorded crime by name, each with a note. No button adds both at once |
| 20 | Compare Wexmoor, Marrowfen, Gorsebeck and Otterby Fields on a search with the two journeys of check 8 | Two rows of journeys, "To Cindermoor Works" and "To Wexmoor University". Gorsebeck reads "No journey time in this data" in the second. What the journeys count for is said once |
| 21 | Type any sentence and press Enter. With the focus still in the box, press the first thing under it, once | It does what it says, the first time: a suggestion, a chip, the name of a result, "Show in the box". Nothing under the box moves while the button is down. P |
| 22 | Type "I am moving to the city in three months for a job at Cindermoor Works. I have never lived there. I want somewhere leafy and fairly quiet, not too far from a decent pub. I can spend about £1,600 a month on a one bed flat." and search | Five things in sight, and no "Show all". "Add the 4 that need no choice", and then one press for the pubs. The budget chip reads "£1,600 a month, rest assumed". "One bed" is not among what "Show in the box" selects. P |
| 23 | After check 22, read the line under the box | "21 areas ranked. What you asked for counts most." Farrowmere is first, in band 3 for Leafy. Gorsebeck, in band 5 for both vibes, is fourth. Until it was decided on 2026-09-24 that what is said of the place leads, the line read "Journey and budget count most." and Gorsebeck was seventh |
| 24 | Press "Table of all areas" on a desktop | Every area is a block, and "Show" is in sight beside each name. The box does not scroll sideways |
| 16 | Watch the network panel through checks 4 to 7 | What was typed is in the body of `POST /v1/interpret` and in no address. Nothing is in browser storage |

## 9. What is not built, and what differs from vibes.md

| Not in this slice | Until |
|---|---|
| Culture on the doorstep, Places to train, Places to meet. So of what the founder named, kinds of gym and community are not felt yet, and culture is a feature and not a vibe. A gym, a sense of community and a garden are offered what is nearest, and say so | vibes.md step 12 |
| Anything about who lives somewhere: no panel, no figure, no link | The founder's decision, vibes.md section 4 |
| The `like` anchor, so "more like this" starts no search. "Go and look" beyond the nearest station. `built_since`. `basis` and `period` on a feature | vibes.md steps 8, 11 and 13 |
| The places a person named, marked on the map | An answer that says where a place is (web.md section 13, gap 5) |
| A place of worship to name as a place to reach. "Near a mosque" is heard, and leads nowhere | Real data that carries such places (section 10, row 81) |
| A mark where the sentence in the box is cut | A field of one line, or a browser that draws one (section 10, row 84) |
| A reason that gives a figure a person can picture beside the band of a vibe | A sentence that may cite two facts (section 10, row 36) |
| What each journey adds to the fit, where the average of the journeys counts | Core reporting what each leg adds (contract section 13) |
| `make api GRITTY=a`. The two commands of contract 9.4 do the same | Whoever next changes the Makefile |
| Venue counts measured from homes: the 23 keep their units. The audit and the people test of vibes.md section 6 | Real data |
| A model, and what a model may apply in a prompt that is not plain | A key, and a decision |
| `apps/ios`. It is not touched, so it is behind contract version 2, and the recorded answers its tests read were all written again. Web gaps 2 to 12 | Their own slices |

| Differs from vibes.md | Here |
|---|---|
| 3.1 and 11 say no scale is named Gritty or Polished, and no vibe holds a crime figure | Variant B is built, by decision 2, on made-up data only. It breaks promises 4 and 5 of vibes.md section 1 for that one id. A rule of `parse_release` kept it from a real release until the founder decided on 2026-09-24 that a release of London carries it (ADR 0013, as amended) |
| 2.5 says recorded anti-social behaviour is not shown at launch | It is a part of variant B, and a feature that can be weighed on request |
| 8 puts the comparison and a `/vibes` page out of the slice and "Go and look" in | The comparison gains character rows, and `/vibes` is built. "Go and look" holds the stations and what each vibe cannot see |
| Step 7 bans "gritty" and "polished" in a sentence | They pass as the names of the ends of variant B, from a fact's slots only |
| Step 8 has one made-up area mixed on purpose | Three are, one on each scale that both variants carry (1.3) |
| Promise 7 says every vibe carries the line that its recipe is a judgement | On a result the sentence of a vibe is short, and the line is one press away, with the source. It stands in full on the page of an area and on `/vibes` |

**What the verify skill still says.** `.claude/skills/verify/SKILL.md` says three things that are no longer so. It was not changed with the slice, and is for whoever next edits it to put right:

| The skill says | It is now |
|---|---|
| Routes 4, 5, 6 and 11 answer `Cache-Control: public` | `Cache-Control: no-cache`, with the `ETag` (contract 9.3) |
| "Safe" is rejected with `crime_needs_explicit_request` | "Safe" is offered: status `suggest`, nothing applied, two offers of recorded crime by name, each with a note |
| A prompt about who lives somewhere has the rest applied | Only where the prompt is plain. In any other, nothing is applied and what was noticed is offered |

## 10. For the founder

Written as the first slice was mended and joined, 2026-09-24. Nothing here is decided. No vibe and no end was renamed, and neither way of building gritty was removed. Every decision that the five menders and the joiner left is a row of the one table below. A row is one candidate, with its case in three lines: what it says or does, what is for it, and what is against it. Each has a recommendation, which is the joiner's and is yours to overrule. "As built" marks what the code does today.

Judge the names and the two ways of gritty on screen, on the city as it was redrawn (section 10.1). Until it was redrawn every vibe coloured the map in nearly the same way, and no name could be judged.

| # | To decide | Candidate | What it says, or does | For | Against | Recommended |
|---|---|---|---|---|---|---|
| 1 | The name of `pace` | **Pace**, as built | How fast a place moves | One short word, and it fits a scale | It is a heading from a report. A person types "not buzzy" and is given back "Pace: towards Calm". Nobody asks for pace | No |
| 2 |  | **Going out** | How much there is to go out to | It is what the recipe counts: places to eat, drink and go out to | It leaves out the high street, which is a fifth of the recipe. It reads oddly with a literal low end: "Going out: towards Little nearby" | Yes, with the ends as built: "Going out: towards Calm" |
| 3 | The low end of `pace` | **Calm**, as built | A place at rest | It is a kind word, and people type it | It is a kind word for the least to eat, drink and go out to. "Calm" and "quiet" call up two different vibes, and nothing says how they differ | Yes, keep. Say in the meaning of each how Calm differs from Quiet streets |
| 4 |  | **Little nearby** | Few places within a walk | It is what is measured, and passes no judgement | Nobody seeks it by that name. It reads as a fault, and a person who wants it has to choose a fault | No |
| 5 | The high end of `pace` | **Buzzy**, as built | A place with a lot going on | People type it, and it names a taste | It promises a feeling. The recipe cannot tell a weekday from a weekend, or who the venues serve | Yes, keep |
| 6 |  | **Lots nearby** | Many places within a walk | It is what is measured | It names no kind of place: lots of what? It does not say eating, drinking or going out | No |
| 7 | The name of `homes` | **Homes**, as built | Where people live | It is short | It says nothing until the ends are read. It is also a word for what is being looked for, so the reader cannot take it as a thing | No |
| 8 |  | **Houses or flats** | Which of the two an area is made of | It says both ends in the name, so the scale explains itself | It is three words on a chip. It leaves out how close together homes stand, which is 35 of the 100 | Yes |
| 9 | The name of `built_age` | **Built age**, as built | When an area was built | It is short, and it is about buildings and not people | It is not a phrase anyone says. "Age" beside a place can be read as the age of who lives there | No |
| 10 |  | **Age of buildings** | How old the buildings are | It cannot be read as the age of residents | It is longer. A quarter of the recipe is protected streets, which is not an age | Yes |
| 11 | The shelf word of Quiet streets | **quiet street**, as built | One quiet street | It is what people want | A vibe is said of an area, and the first line of what it cannot see is "One street or one home". The word promises the one thing the vibe says it cannot see | No |
| 12 |  | **quiet** | A quiet area | It promises no one street, and it is the word people type | It may be read as quiet at night, or quiet neighbours, which the recipe cannot see either | Yes |
| 13 | The shelf word of Parks close by | **near a big park**, as built | A large park within reach | A large park is 30 of the 100, and is what sets this vibe apart from a walk to any park | Typing "near a park" calls up a feature and not this vibe, so two things of nearly one name stand on one card | Yes, keep |
| 14 |  | **near parks** | Parks within a walk | It matches the label, Parks close by | It loses "big", so it no longer says how it differs from the feature "Nearer a park" | No |
| 15 | The name of `street_character` | **Street character**, as built | What the streets are like | It sounds like a taste | Every vibe is the character of a street, so it names nothing. It does not say that 35 of its 100 are recorded incidents | No |
| 16 |  | **Industry, traffic and recorded damage** | What the recipe holds | It is literal. Nobody could choose it without knowing it counts recorded crime | It is long, and it is no word a person would type or seek. It reads as a warning more than as a taste | Yes, if this way of building gritty is kept at all (row 24) |
| 17 |  | **Worn and busy** | A place that shows its use | It is short and can be sought | It is still a judgement, and "worn" is a claim about upkeep, which the recipe says it cannot see | No |
| 18 | The ends of `street_character` | **Polished** and **Gritty**, as built | Smart at one end, rough at the other | They are the founder's own words, and people type them | In speech both are about upkeep: clean or run down. The vibe lists that under what it cannot see. A dense, smart, central district is placed as Gritty | No, if the literal name is taken. Keep both as words a person may type |
| 19 |  | **Less** and **More** | Less or more of what the recipe holds | They pass no judgement, and fit a literal label | They need the literal label beside them. "Towards More" says nothing alone on a chip | Yes, with the literal name |
| 20 | The meaning of Leafy | As built: it says trees, and a public park near home | What a person pictures when they say leafy | It is how people speak | The recipe holds gardens, woodland and green cover as shares of an area. It holds no tree and no distance, and "Street trees" is under what it cannot see | Reword at the next catalogue version, to what is counted. Stop "tree lined" calling it up |
| 21 | Two lines of what a vibe cannot see | As built since the last mend: "Which noise is from roads and which from aircraft." and "How a weekday differs from a weekend." | That the vibe cannot tell the one from the other | Each is a whole sentence. They read "Road noise from aircraft noise." and "Weekday from weekend.", as if a word were missing | They are longer, and the catalogue went to version 3 to hold them | Keep, or reword either in `catalogue.py` and build the made-up release again |
| 22 | The order of the parts in the meaning of Street character | As built: the crime parts are said last, "with recorded criminal damage" | What the vibe is made of | It reads as a sentence | Together the two recorded parts are its largest share, 35 of 100 | Say them first, if this way of building gritty is kept |
| 23 | Which way gritty is built for London | **A**, Works and warehouses: land used for industry, storage and depots, one way | A word such as "gritty" is read into it as assumed, the chip quotes the word, and the page says Burro has no measure of how clean a street is | It needs no change to any decision. It holds no recorded crime. A reviewer found it the more trustworthy of the two | It is not all a person means by gritty. In the made-up city the fields of Gorsebeck are second for it, for the yards of a depot | Yes. A for London |
| 24 |  | **B**, Street character: a scale from Polished to Gritty, as served today | 35 of its 100 are recorded criminal damage and recorded anti-social behaviour. The rest is industry, main roads, noise and density | It is the founder's own word, as a scale a person can turn | It breaks promises 4 and 5 of vibes.md, and needs ADR 0006 changed. It ranks recorded damage up for a person who seeks Gritty. Its ends are words for upkeep, which it cannot see. In a real city its parts all rise towards the centre, so it is likely to follow the centre | No for London. Keep it behind the switch on the made-up release until you have felt both, and then remove it |
| 25 | Whether recorded anti-social behaviour may be a part of anything a place is called | As built: in B alone | 15 of the 100 of Street character | It is recorded, and it is about places | It depends on who reports, and it marks an area by what is said to happen there | No. It goes with B |
| 26 | Whether the name of an end asks for recorded crime by name | As built: "gritty" and "polished" are applied. Since the last mend the chip reads "Street character: towards Gritty, counts recorded crime", and its control and the source of its sentence name the recorded parts | Street character is weighed towards that end, recorded incidents among its parts, and the page of results says so before anything is opened | Each is the name of an end, and the person typed it. The page no longer counts recorded crime unseen | Neither word names a crime. Decision 3 asks for crime by name, and the person is told only after it has counted | If B is kept, offer them as "edgy" and "smart" are offered, with the note. It is one line in the lexicon, and it moves acceptance check 15 and three cases of `evals/` |
| 27 | What "safe" does | **Offer**, as built | Nothing is applied. Two offers: "Less recorded violence and robbery" and "Less recorded burglary and theft", each with a note that it counts recorded crime. No button adds both at once | The choice names recorded crime on its face, so a press is asking by name. Nothing is counted unasked. The person is told the name they were told to ask by | It is two presses. A person who says "safe" may not mean recorded crime at all | Yes, keep |
| 28 |  | **Refuse**, as it was before the mending | The edit is rejected, and the page says crime counts only when asked for by name | It is the letter of decision 3 | The person is told to ask by name and is not told the name. The first word a newcomer reaches for leads nowhere | No |
| 29 |  | **Apply** | Recorded crime is weighed at once | One press fewer | It breaks decision 3: the word named no crime | No |
| 30 | Whether pressing an offer of recorded crime is asking by name | As built: yes | The edit is a `ui_edit`, as any control's is | It is what the control on the settings page already does | The words that were typed named no crime | Yes, keep |
| 31 | Whether a vibe whose recipe holds recorded crime is in a summary | As built: it is left out of "In short" and of what two areas share | It has its line in the portrait, which says it counts recorded crime | Recorded crime is shown to nobody who did not ask | The summary of an area leaves one vibe out | Keep. It falls away if B is removed |
| 32 | The one sentence that says when recorded crime counts | As built: it names three ways, the third being to ask for a vibe whose recipe holds it. Since the last mend it is followed by "In this data no vibe holds it." wherever no vibe of the release does | It is said word for word on every page that speaks of crime | It is true of either way gritty is built, and the line after it says what is true of the release | Where gritty is built from land use the rule still names a third way, and then says that it leads nowhere | Keep while B is served. Cut the third way, and the line after it, if B is removed |
| 33 | How much of the character asked for an area must have a figure for | As built: a half, by weight, and a default counts as character | An area under it is in no result and is listed apart, with what it lacks | An area with no figure for what was asked can never come first. A ranking cannot depend on who chose a weight | The new town, Otterby Fields, is listed apart even for a search by rent and workplace alone, where it was second | Keep a half. On real data, count how many areas it sets apart before launch |
| 34 | What a result leads with | As built: the reason that adds most to the fit | With a journey in the search, the first thing said of most areas is the journey | It is the largest part of the fit | Vibes are the centre of the product. A person who asked for leafy and quiet reads a bus time first, and the vibe third or not at all | Lead with what was said of the place, where the area does it well. It is a change to the order of the reasons (contract 7.5). Not made. Since the last mend the line under the box says "Journey and budget count most." where that is so, and the order of the reasons is as it was (row 80) |
| 35 | What a plain mention is worth against a journey and a budget | As built: a mention is 0.50, a journey 1.00 and a budget 0.80 | For "renting a 1 bed up to £1,700, leafy and quiet, 35 minutes to Cindermoor Works", Cindermoor is second: the works, in band 2 of 5 for Leafy | It was settled on 2026-09-23, and one thing said outweighs all that was not | A journey and a budget together outweigh everything said of the place. "Historic by the river" with a journey puts Foxholt first, in the middle band for Built age | Judge it on screen on the redrawn city. If the place should lead, let a mention be worth what a journey is. Not changed by the last mend: for the newcomer's search the first five sit in bands 3, 2, 4, 4 and 3 for Leafy, and Gorsebeck, in band 5 for Leafy and for Quiet streets, is seventh. **Decided on 2026-09-24: what is said of the place leads.** A journey weighs 0.40 and a budget 0.30 until a person moves them, and a mention is still 0.50. For the search of this row Cindermoor is fourth, and for the newcomer's Gorsebeck is fourth and the first five sit in bands 3, 3, 4, 5 and 4 for Leafy |
| 36 | How a vibe is said in short | As built: the start of its full statement. "Leafy: band 5 of 5, counted from least to most, among the 21 areas compared in this release." | The dates and the line about judgement are behind "Source" | Nothing is said that the full statement does not say. The sentence is some 90 characters, where it was some 170 | It is still a sentence for a statistician. It gives no figure a person can picture. The line that the recipe is a judgement is one press away, where vibes.md promises it of every vibe | Keep for now. Next, the band in words and one figure: "Leafy: among the most here. Gardens are 27% of the land." It needs a sentence that may cite two facts, and never a figure of crime |
| 37 | Whether a GP and a pharmacy come into the first version | As built: neither is in any release, so Everyday on foot rests on 70 of its 100 | The band says so: "Worked out from 3 of its 5 parts, 70 of 100 by weight." | No source is cleared for either | A vibe about daily life that leaves out the surgery | Bring both in before real data, if a source can be cleared (vibes.md, question 8) |
| 38 | How little a thing must be worth to be a trade-off | As built: under 0.35 | What is worth 0.35 to 0.50 is in no sentence | A walk of 5 minutes is no longer what an area gives up | More results show no trade-off | Keep. Hold it against searches on real data |
| 39 | How short a walk must be to be no trade-off | As built: 10 minutes, 800 m, and 1,600 m to a large park or a campus | A walk at or under its figure is never given as what an area gives up | A walk of 7 minutes to a station is good by any measure | The figures were chosen by judgement. No published standard was read | Keep. Check them against a published walking standard before real data |
| 40 | The order of "More like this" | As built: by the count each sentence gives | The areas in the same band on the most measures come first | The order can be checked on the page | The five that are served can change with it. Under each sentence the page also names the vibes the two areas share a band on, and that count runs another way: for one area the first of the five shares one vibe and the third shares six | Keep the order. Judge on screen whether the vibes two areas share should stand there at all, or should be what the order is by |
| 41 | What each journey adds, where the average of the journeys counts | As built: no cell of a comparison says it, and one line says why | The engine reports one figure for the journeys together | Nothing is worked out in a route or a page | A comparison of two journeys shows no figure for either | Leave it until a person asks. To show it, the engine reports what each journey adds |
| 42 | What is offered for a gym and for a sense of community | As built: what there is to do in parks, and Village feel, each with a note that it is only the nearest | An offer, and nothing applied | The word leads somewhere | Neither is what was asked for. Village feel says itself that it cannot see whether neighbours know each other | Say that Burro has no measure of either, as it does of a place of worship, until Places to train and Places to meet are built |
| 43 | What is offered for a garden | As built: the garden land of an area, with a note | An offer, and nothing applied | It is near to what was meant | It is the land of an area, and not the garden of a home | Keep |
| 44 | What is offered for "cheap" | As built: nothing. The person is told Burro gives no verdict on what is affordable | `unmet` holds `affordability_verdict` | A budget is a number only the person can say | The word leads to no control | Keep, and let the line lead to the budget control |
| 45 | Which hedges are read as a word of degree | As built: "fairly", "quite", "pretty", "reasonably", "relatively". Not "maybe", "ideally", "probably", "I think" | A hedge before a thing is a small step | None of the five can turn a wish round | A person who says "ideally near a park" still has to press | Keep |
| 46 | A sentence about the past in a prompt | As built: "I have never lived there" makes the whole prompt not plain | Nothing is applied, and what was noticed is offered | The grammar never reads a past tense, so no wish is read backwards | The newcomer's own prompt is offered and not applied | Keep. One button now adds every thing that has one way |
| 47 | A workplace at a university | As built: "My partner works at Wexmoor University" gets the notice about who lives somewhere, and no journey is offered | A campus in a prompt that is not plain is heard as a request about residents | It keeps a request for students from being read as a journey | A person who names a workplace is told Burro never ranks by who lives there | After words that say someone works or studies there, offer the journey and give no notice. It changes contract 8.4, so it waits for your word |
| 48 | What "Pubs are so noisy" is offered | As built: pubs both ways, and less transport noise | Section 4.2 names transport noise | It was specified so | Transport noise is not what the person meant | Offer Quiet streets, which holds the late venues, in place of transport noise |
| 49 | A double negative | "It's impossible for me to be far from Pellam Infirmary" was offered a journey and is now declined | No journey is offered where a word that turns it away stands before the place | Nothing is read backwards | One sentence that was offered is now not | Keep |
| 50 | A name that is both a place and an area, after "or" | "within 35 minutes of Cindermoor Works or Pellam Cross" offers a journey to the first, and for the second to look only there or to leave it out | After "or" the name is taken for the area | An area is never taken for a journey's end | The person meant a second journey | Offer the journey to the place as well |
| 51 | The size of a home in a prompt that is not plain | As built since the last mend: a size the search does not hold is offered, "Set a 2-bedroom home". A size it holds already, as one bedroom is for a renter, is heard and offered nowhere, because to choose it would change nothing, and is no longer marked as not read | A choice holds only what its label says, and none is offered that would do nothing | Nothing is said to be unread that was heard | A person who typed "one bed" sees no sign of it but that "Show in the box" passes over it. The chip of the budget says the size was assumed | Keep. To show it, let a size that is named count as chosen whether or not it moves, as a tenure does (contract 5.3). It is a rule of the reducer |
| 52 | What a model may apply, and what turns a model on | As built: no model runs. A key alone would turn one on, and a model may apply an edit in a prompt the reader would apply nothing of | Nothing reaches a person today | There is no key | Decision 2 would not hold on that path. The site says a provider may keep words for up to 30 days, which is not true of each | Before any key is set: a key alone turns nothing on, a model applies nothing in a prompt that is not plain, and the line about how long words are kept is served by provider |
| 53 | Whether the made-up city reads as a city | As redrawn: Cindermoor, the works, is fifth for Village feel, and Gorsebeck, the fields, is second for Works and warehouses | Each change has a line in `names.py` that says what the area is | Without them Food and drink and Pace run together again, at 0.83 | A person who knows cities may find either odd | Keep. The city is there to part the vibes, and describes no real place |
| 54 | Whether two vibes may put one area first | As redrawn: Pace towards Buzzy and Homes towards Flats both put Pellam Cross first | They share 3 of their first 5, and sit at 0.62 | The centre is both | The two names cannot be told apart by their first area | Part them with one value, the flats of Pellam Cross, before the names are judged |
| 55 | The limit on how alike two vibes may be | As built: a rank correlation of 0.8, held by a test on four seeds | No pair is above 0.73 | It is the figure vibes.md proposes for real data | vibes.md proposes 0.6 where two vibes share a part, and five such pairs are above 0.5 | Keep 0.8 for the made-up city. Hold real data to both figures of vibes.md |
| 56 | How often one area may lead | As redrawn: Thrushcombe is in the first five of eight of the fifteen lists | It is the village that has everything | Such places exist | It may hide what the vibes add | Keep |
| 57 | Which area is most like Thrushcombe | As redrawn: Wickerford, the other old village, is the fifth of its five, where it was first | On 29 other seeds it is first to fourth, and most often second | The order is the engine's, by the count each sentence gives | A person may expect the two old villages to stand together | Keep. Say if the committed city should put it first |
| 58 | Which area is first for "somewhere a bit gritty" | As redrawn: Pellam Cross, the centre, with Lantern Yard second. Asked for alone, Street character puts Lantern Yard first | "A bit" counts for little, so the usual settings tip it | It is the arithmetic of the engine | The nightlife quarter is what the word was drawn for | Keep. It falls away if B is removed |
| 59 | Whether a release id may be used again for different content | As built: `syn-2026-09-23-01` has held three contents | The `ETag` is the release id, so a browser that held an older answer is told it still stands | Nothing is deployed | A published release must never change | Never once anything is deployed. Give the fixture a new id whenever its content changes |
| 60 | Whether the contract needs a new version | As built: version 2, though answers gained required fields and the row of a journey changed its name | A client built to version 2 as first written would refuse an answer | Nothing outside the repository reads the API | The iPhone app is already behind | Call it version 3 before anything outside the repository reads the API |
| 61 | What the log line of route 1 says of a reading | As built: counts of edits, and the codes of what could not be met and of why an edit was refused | No word, no place and no number of the spec | It helps to see what the reader cannot do | It is worked out from the words, and sits beside a time and a request id | Log how many, and not which. Count the codes in the call record, with no time beside them |
| 62 | The limit of 30 seconds for the backend's tests | As built: no check holds it, and the time differs from one run to the next | 20.6 to 23.7 seconds in three runs on 2026-09-24, with 5,083 tests, and 42.9 in one. Joined with the first real builds, the suite holds some 11,000 tests and takes about 75 seconds | The limit keeps the suite quick to run | A limit nobody measures is not held | Time it in hosted CI. If it is over 27 there, run the tests of the providers that wait on a clock under the marker `full` |
| 63 | The message of commit 3d56449 | It says about 85 tests were added. The figure is 47 | It is in the history of the branch | Nothing depends on it | It is untrue | Put it right when the history is squashed for the first push |
| 64 | Which vibes a result draws on a phone | As built: the ones that were asked for, and not the two others the API chose | The others are on the page of the area | It keeps a result to a few lines | A person on a phone sees less than one at a desk | Keep. Judge it on a phone |
| 65 | Where the ways to the settings and to sharing stand | As built: after the first result, at every width | Nothing stands between what Burro understood and the answer | The answer comes first | The settings are further from the box. On a desktop, where there is room, the second walk found them odd between the first result and the second | Keep on a phone. Judge on a desktop whether they should stand over the list there |
| 66 | What the banner says once a search is open, on a phone | As built: "This is made-up test data." and no more | Before a search, and on every other page, it says all of it | It gives the answer a line | It says less | Keep. The flag is on every page and every response |
| 67 | One button that adds several things at once | As built: it adds every thing that has one way to be wanted, and never one that carries a note. Since the last mend every such thing is in sight, so the button counts them all | A newcomer's sentence of five things takes 2 presses, where it took 5 or 6 | Nothing is guessed, and recorded crime is never added unnamed | A person may add what they did not read. With many things noticed the list is longer than four lines | Keep |
| 68 | Whether the title of the page is drawn once a search is open | As built: "Decide where to live" is kept for a screen reader and not drawn | It is drawn before a search and on a shared search | It gives the answer a line | The page has no visible title | Keep |
| 69 | Whether a word a person typed may be quoted on a chip | As built: yes, where it is one of `MIXED_WORDS`: the chip reads that Works and warehouses was read from "gritty" | It is the lexicon's spelling, and never the text | The person sees that their word was swapped | A typed word is drawn on the page | Keep |
| 70 | The places a person named, on the map | As built: they are not marked | No answer says where a place is | The website takes no position from anywhere but the API | A newcomer cannot see where they work | Serve where each place is, in `places`. It is the next thing the map needs |
| 71 | The areas that are not ranked, on the results page | As built: a closed button under the list that says how many, and opens to each with why and what it lacks. It holds the areas the data never ranks as well | Such an area is in no result, and a person can see that it is there | The answer stays a few lines however many areas are set apart | A person must press to see which area was set apart | Keep. Judge on screen whether it should stand open where it holds one area |
| 72 | Site copy written by the menders | "It never guesses what you meant, so it asks.", "Add all 4", "What you asked for counts most.", "In short", "Where it is", "among the most here", "3 areas are not ranked", "Too little is known of the character that counts in your search". By the last mend: "Journey and budget count most.", "counts recorded crime", "Weight 100", "A weight says how much a thing counts beside the others, from 0 to 100, as its slider is set. The weights are not shares, and do not add up to 100.", "Nothing in that could be read. Burro reads plain English, such as “leafy and quiet, near a park”.", and the line under the chips that says how to let the place lead | None says anything of a place | Each is plain | None was read by you | Read each on screen, and change any in `apps/web/src/content/` |
| 73 | The figure that stands beside a vibe | As built since the last mend: of the parts a person can picture, the website chooses the one that sits nearest the band of the vibe, and never a figure of crime | The API names the heaviest part of all, which for three vibes is a count for each square kilometre, and which may sit at the other end from the band | The figure never reads against the band: "among the most here" stood beside the one figure that said otherwise | The rule is the website's and not the engine's, and the part shown differs from area to area | Let the API name the figure, by this rule |
| 74 | What the summary of an area says of a band that rests on part of a recipe | As built: "from 2 of its 3 parts". The full clause, with the share, is on the line of the vibe below | Both counts are the fact's own | A line of the summary stays short | The share is one press further | Keep |
| 75 | When the page of an area shows journey times | As built: only while a search is open and its ranking is in hand | Route 6 serves no journey | The page sends nothing about a search | A person who opens an area from a link sees no journey | Keep. To change it the page would send the spec of the search |
| 76 | How long the portrait is on a phone | As built: it ends within three and a half screens. The summary and where the area is are within a screen and a half | The whole list of vibes stands open | Nothing is hidden | It was two screens before | Keep. Close the full list behind a press only if a walk on a phone finds it long |
| 77 | How long the longest pages are | As built: `/vibes` is 16,131 px on a phone and Methods 22,152 | Each vibe carries its map and the areas at each end. Methods lists 40 features | Nothing is hidden | They are long to scroll on a phone | Close the list of features on Methods behind a press. Leave `/vibes` |
| 78 | The room for other names on `/vibes` | As built: it is empty | `OTHER_NAMES` in `apps/web/src/content/names.ts` | No name stands on a page before you have chosen | The page cannot yet show the choice | Fill it once rows 1 to 19 are decided |
| 79 | What a result shows of a vibe nobody asked for | As built since the last mend: a vibe that runs one way only where the area has more of it than most, a scale towards either end, and never a vibe whose recipe holds recorded crime | The first result of a search by two journeys opened with two vibes at "least", which read as two warnings on the best answer | A result says what a place has. Recorded crime is shown to nobody who did not ask | What an area has least of is one press further, on its page | Keep. Judge on screen |
| 80 | What is done where a journey and a budget outweigh the vibes | As built since the last mend: the order is as it was, and the line under the box says "Journey and budget count most." With the chips opened out, one line says where to change it | A person who asked for leafy and quiet is told why the first result is not the leafiest | Nothing is ranked otherwise than you settled, and nothing is said that is not so | Vibes are the centre of the product, and the answer is still led by the journey. It is an account, and no cure | Read the line on screen, and then decide rows 34 and 35. If the place should lead, row 35 is the change that moves the order. **Decided on 2026-09-24**: the place leads (row 35). The line is now said only where a person has made a journey or a budget count for more than what they asked of the place |
| 81 | What "near a mosque" leads to | As built: the page says Burro has no data on places of worship, and offers nothing | Decision 3 allows a place of worship named as a place to reach | Nothing is said of who lives anywhere | The made-up release holds no such place to name, so the line leads nowhere | Carry places of worship among the places a person can reach, in real data. The line can then lead to the place field |
| 82 | A workplace that a shared link keeps by name | As built: a share keeps "Cindermoor Works", because the release calls it a district | Only a place that is not a station or a district is replaced by the station that stands in for it | A district is coarse already | The panel says a link does not say where you work, and this one names a works | Decide what kinds of place a link may name. In the made-up release a works is better called a landmark, which a link replaces |
| 83 | The map before a search, on a phone | As built: it is on the second screen | The shelf, the tenure, the place field and the examples stand over it. A word of the shelf shows the city in its own card | Every way to start a search is on the first screen | Check 1 asks for the map on the first screen | Say what should give way on a phone: the examples, or the tenure and the place field |
| 84 | A long sentence in the box, once a search is open | As built: the box is one line, and cuts what does not fit in the middle of a word | With the focus in it the box wraps, and shows all of it | The answer comes first | No mark says that the line is cut: the browser that was tried draws none in a box of several lines | Leave it, or draw the sentence in a field of one line, which a browser does end with a mark |

### 10.1 What the made-up city now shows, to judge the names by

As first drawn, the eleven vibes moved as about three: central, old and green. Pressing one word after another coloured the map in nearly the same way, so nobody could judge what a vibe adds, or whether its name is right. The plan of the city was redrawn on 2026-09-24. No recipe, no name and no rule of the engine was changed to do it.

| Measured across the areas, for every pair of vibes | As first drawn | As redrawn |
|---|---|---|
| The greatest rank correlation, either way | 0.97, Homes with Food and drink | 0.73, Pace with Quiet streets |
| Pairs above 0.8, of 55 | 14 | 0 |
| Pairs above 0.7 | 17 | 1 |
| The most that two vibes share of their first five areas | 5 | 3 |
| Pairs that share more than 3 | 11 | 0 |

A test holds two of these on the committed seed and three others, for both ways of gritty: no two ends of two vibes share more than 3 of their first 5, and no pair has a rank correlation above 0.8. Both also hold on 38 of 40 seeds that were tried. On the other two, one pair shares four of its first five, and the greatest rank correlation on any of the forty is 0.78. Every case the tests of the pipeline name holds on the first twelve.

| Asked for alone | The five areas that come first |
|---|---|
| Leafy | Alderwick, Larkspur Hill, Brackenhythe, Gorsebeck, Thrushcombe |
| Village feel | Thrushcombe, Wickerford, Tallowgate, Brackenhythe, Cindermoor |
| Pace, towards Buzzy | Pellam Cross, Lantern Yard, Wexmoor, Kindlewharf, Tallowgate |
| Pace, towards Calm | Marrowfen, Gorsebeck, Alderwick, Farrowmere, Cindermoor |
| Quiet streets | Gorsebeck, Alderwick, Sable Reach, Larkspur Hill, Wickerford |
| Built age, towards Historic | Tallowgate, Thrushcombe, Wickerford, Lantern Yard, Alderwick |
| Built age, towards Newer | Sable Reach, Marrowfen, Dulcimer Green, Farrowmere, Osierholm |
| Everyday on foot | Foxholt, Tallowgate, Pellam Cross, Thrushcombe, Dulcimer Green |
| Parks close by | Brackenhythe, Larkspur Hill, Thrushcombe, Sable Reach, Foxholt |
| Homes, towards Flats | Pellam Cross, Lantern Yard, Farrowmere, Hollinsworth Quay, Foxholt |
| Homes, towards Houses | Otterby Fields, Gorsebeck, Cindermoor, Thrushcombe, Marrowfen |
| Food and drink | Kindlewharf, Thrushcombe, Tallowgate, Hollinsworth Quay, Wickerford |
| Family amenities | Dulcimer Green, Osierholm, Eskerfold, Larkspur Hill, Thrushcombe |
| Street character, towards Gritty | Lantern Yard, Pellam Cross, Kindlewharf, Hollinsworth Quay, Cindermoor |
| Street character, towards Polished | Larkspur Hill, Alderwick, Wickerford, Eskerfold, Brackenhythe |
| Works and warehouses, where gritty is built that way | Cindermoor, Gorsebeck, Lantern Yard, Marrowfen, Kindlewharf |

| An area that breaks a pattern | What it is now |
|---|---|
| Wexmoor | Lively, and no place for food: student bars, most of them chains |
| Tallowgate | Old, and not leafy: terraces on lanes too narrow for a main road |
| Dulcimer Green | Leafy, and on a main road |
| Farrowmere | Flats, and quiet: estates at the end of a line |
| Thrushcombe | Leafy, and lively |
| Alderwick | Old, and calm. Leafy, with no park close by: the green is private |
| Foxholt | A large park behind the high street, and not leafy |
| Cindermoor | Works and depots, with cafes of its own and a small centre |

| What to weigh | |
|---|---|
| Whether the city reads as a city | Each change has a line in `names.py` that says what the area is. Cindermoor is fifth for Village feel, because its centre is small and its cafes are its own. Gorsebeck is second for Works and warehouses, for the yards of its depot. Say if either should not be |
| What two vibes still share | Street character and Quiet streets share two parts, read opposite ways, and sit at 0.63. Pace and Quiet streets share none and sit at 0.73: where little goes on, streets are quiet. On real data that pair is the one to watch |
| What moved with it | The figures of the 23 older features, and the costs, of the areas that were changed. The map, the journeys, the stations and the places did not move. Every answer the website recorded is stale until it is recorded again |
| Named cases that moved | The five areas most like Thrushcombe are now Dulcimer Green, Osierholm, Tallowgate, Eskerfold and Wickerford, where Wickerford was first. On most other seeds Wickerford is first or second. Foxholt's portrait now reads more than most for Parks close by and Family amenities, where it read Food and drink and Village feel |

## 11. What was found, and what became of it

The first slice was walked in a browser and reviewed twice on 2026-09-23. They found 2 blockers, 17 major faults and some minor ones. Each was mended with a test that failed first, but where this table says otherwise.

| Found | How bad | What became of it |
|---|---|---|
| An area with no figure for what was asked came first | Blocker | Mended. The engine ranks an area only where it has a figure for half of the character that counts (5.6). The page lists the rest apart |
| A turned list was read backwards where a word followed its last thing | Blocker | Mended. "I don't want pubs or restaurants nearby" is fewer of both |
| On a phone the answer was not first | Major | Mended. Measured on 2026-09-24, in the three searches that were measured last: the first result begins at 404 to 480 px and ends at 686 to 786, of 844 |
| What Burro understood was cut off, and the vibes were the part that was hidden | Major | Mended. The chips wrap, and what was asked of the place comes first |
| On a phone a word of the shelf coloured a map the person could not see | Major | Mended. The card of a word shows the city in five bands |
| Pressing an area on the map led nowhere, and a result's name was no link | Major | Mended |
| The comparison showed a different journey for each area | Major | Mended. One row for each journey, in the API and on the page |
| A result did not say in five lines why this place | Major | Mended in part. A vibe is said in short, and the strip is not drawn twice. It gives no figure a person can picture (section 10, row 36) |
| A natural sentence cost five or six presses, and a hedge made a prompt a question | Major | Mended. Five hedges are read, and one button adds every thing that has one way. Since the last mend every such thing is in sight, and a newcomer's sentence of five things takes two presses |
| The first words a newcomer reaches for led nowhere | Major | Mended in part. Safe, a gym, community and a garden are offered what is nearest. Cheap is heard and offers nothing. A place of worship has no place to name (rows 27 to 29, and 42 to 44) |
| The made-up city could not show what a vibe adds | Major | Mended. No two vibes run above 0.73 together (section 10.1) |
| Six names were found wrong, and Leafy's meaning promises what it cannot see | Major | Not mended, by the founder's decision. The case for each is in section 10, rows 1 to 22 |
| Street character's ends are named for what it cannot see, and Gritty ranks recorded damage up | Major | Not mended: the choice of A or B is the founder's (rows 23 to 26). "Gritty but safe" now applies nothing |
| A walk of 7 minutes to a station was shown as what an area gives up | Major | Mended. It is not said that a trade-off may be a setting nobody chose |
| The map and the portrait gave a newcomer no bearings | Major | Mended in part. The areas are named on the map, and the portrait opens with what an area is like. The places a person named are not marked (row 70) |
| A plain journey lost its way of travelling and its firm limit | Major | Mended |
| An assumed word ranked areas by recorded crime | Major | Mended. Such a word is offered, with a note, and never applied |
| The name of a scale was read as a wish for its high end | Major | Mended. It is offered with both ends |
| A suggestion's edit held more than its label said | Major | Mended |
| A release was accepted though what it ranks on parted from what it shows | Major | Mended. Three rules more |
| A band worked out from part of a recipe was shown as any other | Major | Mended. The fact, the sentence and the page say how much it rests on |
| "More like this" was not in the order its heading promised | Minor | Mended |
| The list stopped at 20 and did not say so | Minor | Mended |
| Where gritty is a scale it counted recorded crime while the page said crime counts only when named | Minor | Mended. One sentence says when recorded crime counts, on every page, and since the last mend the chip of such a vibe says that it counts recorded crime. "Gritty" is still applied where it is typed plainly (row 26) |
| Page height limits were passed in three cases | Minor | Mended as measured on 2026-09-24. To be measured again after the last change of layout |
| On a phone the table cut the fit, and pins overlapped | Minor | Mended |
| "Start again" left the compare tray and the chosen area | Minor | Mended |
| After a suggestion was chosen the page still said nothing typed had changed the search | Minor | Mended |
| The only choice offered could be the opposite of what was said | Minor | Mended, but for a workplace at a university (row 47) |
| A label repeated on its only button, "1080 m", a box that cut its text, "asked for: Buzzy Buzzy" | Minor | Mended |
| "Road noise from aircraft noise." | Minor | Mended by the last mend, with the line of Pace beside it. The catalogue is version 3 (row 21) |
| The slice document no longer said what was built | Minor | Mended, here |
| The backend's tests sat on their limit of 30 seconds | Minor | Mended in part. 20.6 to 23.7 seconds in three runs on 2026-09-24. No check holds the limit (row 62) |
| A key alone turns a model on | Minor | Not mended. No model runs (row 52) |

### 11.1 The second walk, and the last mend

The mended slice was walked in a browser a second time on 2026-09-24. It found one blocker, two major faults and some minor ones, and that three earlier faults were mended only in part. Each that was mended has a test that failed first.

| Found | How bad | What became of it |
|---|---|---|
| The first press after a typed search did nothing | Blocker | Mended. With the focus in it the box was three lines high, by a rule of its style sheet. A press elsewhere took the focus, the box dropped to one line, and what was under it moved under the press. How high the box is now follows what was done and never the focus alone, and a test reads every style sheet for a rule that moves anything with the focus. Seen in a browser at both sizes: the first press landed each time. Not tried by touch |
| Where gritty is a scale, typing it ranked on recorded crime and the results never said so | Major | Mended as far as the page goes. The chip, its control, its slider and the source of its sentence say that the vibe counts recorded crime, and what it counts. A result shows such a vibe only where it was asked for. "Gritty" is still applied where it is typed plainly: whether it should be offered is row 26 |
| With a journey and a budget, the answer was not led by the vibes asked for | Major | Mended on 2026-09-24, by the founder's decision: what is said of the place weighs more than a journey and more than a budget (row 35). The order of the reasons is still the order of what adds most to the fit (row 34) |
| A natural sentence took three presses, and the budget was the thing that was hidden | Earlier fault | Mended. Every thing that has one way to be wanted is in sight, and the button counts them all |
| "On a one bed flat" was offered nowhere | Earlier fault | Mended in part. It is no longer called unread: a renter's search holds one bedroom already, so there is nothing to choose. It is still offered nowhere (row 51) |
| A sentence in Spanish led nowhere | Earlier fault | Mended in part. The page says what Burro reads, and gives a sentence that it does read. Burro cannot tell one language from another |
| "Near a mosque" led nowhere | Earlier fault | Not mended. The release holds no place of worship to name as a place to reach (row 81) |
| A budget chosen from an offer said "One bedroom, flexible", which nobody chose | Minor | Mended. It reads "£1,600 a month, rest assumed" |
| On a desktop the last column of the table of all areas was out of sight | Minor | Mended. The table is stacked by the width of its own box |
| "Counts for 100 of 100" stood beside "Counts for 10 of 100" | Minor | Mended. Each is said as a weight, and one line says what a weight is |
| The best result opened with two vibes nobody asked for, both at "least" | Minor | Mended, in the engine (row 79) |
| The figure beside a band could read against the band | Minor | Mended (row 73) |
| What an area lacks listed the usual settings before what was asked for | Minor | Mended |
| In the land-use release the rule on recorded crime named a vibe whose recipe holds it, and none does | Minor | Mended. The rule is followed by a line that says so (row 32) |
| The end word of a mark sat 1 px from its border | Minor | Mended |
| The map names few areas, and none of the places a person named | Minor | Not mended. The places wait for an answer that says where a place is (row 70) |
| On a phone the map is on the second screen before a search | Minor | Not mended. What should give way is the founder's (row 83) |
| Settings and Share stand between results 1 and 2 on a desktop | Minor | Not mended (row 65) |
| A share keeps a workplace by name | Minor | Not mended (row 82) |
| Unfocused, the box cuts a long sentence in the middle of a word | Minor | Not mended. The browser that was tried draws no mark where a line of such a box is cut (row 84) |
| In "More like this" an area that shares six vibes stood third, and one that shares one stood first | Minor | Not mended. The order is by measures in the same band, and the vibes two areas share are another count (row 40) |
| A workplace at a university still gets the notice about residents | Minor | Not mended. It changes contract 8.4, and waits for the founder (row 47) |

What the last mend could not check: a touch screen, a screen reader, and any browser but one. Heights were measured for one search on a phone, which was 3,466 px with one thing still to choose, and the first result began at 607 px. The search page was not measured again on a desktop.
