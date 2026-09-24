# What core needs, for every measure that is built and not yet named

This page lists every change core needs before a measure that is built, and that core does not yet name as it is built, can be in a release. The measures were built beside core's catalogue as it was on the morning of 2026-09-24.

**The changes that were decided are made.** They are in the catalogue at version 12, with the engine at 1.12.0, in one change with the contract, the fixture and the recorded answers. Each row below says what core says now. A row that is not made says what it waits on, and each of those is the founder's to decide. Section 5 says what a change must not do. Section 6 is what the join left to do, and is not about core.

Every figure here is of London as a whole. None is of a named place.

## 1. Measures that are worked out and left out

Before the join a build that named every list worked out 27 measures. It carried 16. It left 11 out by the rule `measure_is_as_core_says`, because core's row was not what the figure is. Each is on the table in `packages/pipeline/src/burro_pipeline/derive/measures.py`. The table now holds 33: the cultural venues joined it, as a count and for each 1,000 homes. A build leaves three out by that rule now: the two of town centres and `park_facilities`.

Seven were a straight line that core named a walk, or a distance that core named a share. The founder decided on 2026-09-24 that a distance says it is a straight line, as the distance to a park already does. Six are named as built. One waits.

| Feature | Core says now | Left |
|---|---|---|
| `play_space_proximity` | Label "Straight-line distance to the nearest marked way into a play space". Unit m. Less is better. Resolution point | |
| `school_primary_nearby` | Label "State primary schools within 800 m in a straight line". Unit count. Resolution point | The founder says whether an infant and a junior school on one site are one school or two. They are counted as two |
| `station_walk` | Label "Straight-line distance to the nearest way in to a station". Unit m. Resolution point. Never a trade-off under 800 m | It is the heaviest weight a search starts with, in `spec.py`. The founder says whether the cable car is a station |
| `highstreet_access` | Label "Straight-line distance to the nearest town centre boundary". Unit m. Less is better. Resolution point. Every recipe that weighs it reads it from its near end | A town centre is not a high street, and no name says one. The founder says whether the boundaries of high streets are to be counted too |
| `gp_walk` | Label "Straight-line distance to the nearest GP practice, placed by its postcode". Unit m. Resolution point. Never a trade-off under 800 m | On no table yet: section 3 |
| `pharmacy_walk` | Label "Straight-line distance to the nearest pharmacy, placed by its postcode". Unit m. Resolution point. Never a trade-off under 800 m | On no table yet: section 3 |
| `park_facilities` | **As it was.** Label "Kinds of thing to do in parks within a 15-minute walk". Resolution network. The figure is the kinds of play and sports site in parks within 1,200 m in a straight line | **It waits for the founder on playing fields**: section 5. The note for "gym" in `lexicon.py`, `NO_GYMS`, says "within a walk" until then |

Every floor of 800 m was chosen for a walk of ten minutes, and a straight line is shorter than the walk. Each is to be looked at again.

Four differed in what is counted. Each is named as built.

| Feature | Core says now | Rests on |
|---|---|---|
| `incident_criminal_damage` | Label "Recorded criminal damage and arson". Unit "per 1,000 homes a year" | Decided 2026-09-24: recorded crime is counted for each 1,000 homes, from the police's own file, over the whole months it holds. The file counts arson with criminal damage. The row of the proxy audit was written first: [the page of recorded incidents](../research/data/incidents.md), section 11 |
| `incident_antisocial` | The label stands. Unit "per 1,000 homes a year" | The same |
| `land_transport_other` | Label "Land used for transport other than roads, such as railways, airports and docks" | The publisher puts depots and yards under storage |
| `water_access` | Label "Share of homes within 300 m, in a straight line, of the centre line of a river, canal or lake" | The figure is of homes and not of land, so the label says homes. The short label still says "Nearer a river or canal", and a lake counts |

Two are of town centres. Each keeps core's name, so a build leaves both out and Village feel holds under 60 in 100 of its recipe.

| Feature | Core says | The figure is | Waits on |
|---|---|---|---|
| `centre_small` | "Share of homes whose nearest town centre is a small one" | The share of homes within 800 m of a town centre whose nearest centre is under 10 ha | The founder says whether 10 hectares and 800 metres are right |
| `centre_compact` | "Share of the nearest town centre within 200 m of its middle" | How much of the smallest circle round the nearest centre the centre fills | The founder looks at the maps. As built, the vibe does not find villages |

## 2. Measures of who lives somewhere

Four are worked out from two census tables: `residents_aged_20_34`, `residents_aged_65_over`, `households_dependent_children` and `households_one_person`. They are on no table, in no release and in no vibe. Core holds no such feature, and refuses any name that holds a word for residents.

The founder decided on 2026-09-24 that the age of residents and the make-up of households may feed a vibe and a ranking, from the census, and that nothing else about residents may. [Decision record 0006](../adr/0006-rank-places-not-residents.md) holds it. [The design](residents-age-and-households.md), section 9, lists every change to core, file by file. The rule each change is held to:

| Rule | In core |
|---|---|
| A part that counts residents is read high, and never low | `checked_recipe` refuses a recipe that reads one from its low end. A feature of this kind offers one choice: more |
| It stands in a one-way vibe, and never in a scale | `checked_recipe` refuses a scale that holds one |
| It counts towards no likeness | `in_likeness` is false, and `may_be_compared` refuses it whatever the flag says |
| Its name says who is counted, and in which census | Each label ends ", Census 2021". The unit is %. A release holds no count |
| No reading of any words asks for fewer of a group | The notice stands for every wish to avoid people, age and households among them |

Not decided, and not to be built: a filter by who lives somewhere, ranking on gender, and ranking towards a community a person names. Ethnic group, religion and country of birth are shown on an area's page and never ranked on. Stop and search is never read.

## 3. Measures that are built and are on no table

| Measure | Why it is on no table | What brings it in |
|---|---|---|
| `gp_walk` | The report of practices was fetched on 2026-09-24. It writes a status the step does not name, `INACTIVE`, and two prescribing settings in one cell in 27 lines. The step stops at it | The step is put right, with a test on the real file. The founder says whether the walk to a GP comes into the first version: the plan says it does not. Then core's row, as in section 1 |
| `pharmacy_walk` | The pharmacy list is in the store with no receipt: its list is unsure of its period. The list has no column for a pharmacy that serves by post alone | The period is stated and the file fetched again. The founder says whether a figure that counts such pharmacies may be shown |
| `private_outdoor_space` | Its workbook is keyed by the census areas of 2011, and 39 areas of London have no row. The lookup to the areas of 2021 has no receipt. Core says homes, and the workbook counts addresses | The lookup is fetched. Core's label says addresses, or the founder says an address is a home |
| `culture_venues` | **Made.** Core names it as a count within 800 m of home, in a straight line, and it is shown and never ranked on. `culture_venues_per_homes` is ranked on: venues for each 1,000 homes, as food is. Its list holds a receipt | Two records within 25 m are one venue, and there is no floor on how sure a record is. Both are first choices, and the founder's to adjust. The kinds that count have not been checked against a sample |
| Places of worship, community centres and cultural centres | Core holds no feature for any. Nine are proposed | [The design](community-reader.md): core, the reader, the contract and the website change together. Each is weighed on request only, and stands in no vibe |
| The nearest station, from the national file | The measure reads the file of London alone, and leaves out the homes near London's edge | [The page of stations](../research/data/stations.md), section 5, lists what the reader, the measure and the table of stations as places must change |

## 4. Vibes

| Vibe | What core must do | Rests on |
|---|---|---|
| Gritty | **Made.** One vibe, a scale, with the recipe recorded criminal damage 30, works and warehouses 30, recorded anti-social behaviour 15, main roads 15, transport noise 10. Homes per hectare and nitrogen dioxide are not in it. Works and warehouses is land for industry and land for storage, at 15 each | Decided 2026-09-24, and the recipe of that afternoon stands over the one shown in the morning. Typing "gritty" counts as asking for recorded crime. Nothing about who lives somewhere is in it |
| Gritty, in a real release | **Made.** No rule refuses a real release whose Gritty holds recorded incidents, and a release of London carries Gritty. What is left is the portrait of an area, the bands of the map and the measures on an area's page, which are built with no search: a release that carries Gritty shows it, and both rates, to a person who asked for nothing | [The page of recorded incidents](../research/data/incidents.md), section 8, rows 11 to 13. The founder says whether that is wanted |
| Works and warehouses | **Made.** It is a part of Gritty, and a release that carries Gritty serves no vibe of that name. `tags_of()` leaves it out, and the words for it are offered as Gritty | Its figures are right at the top and wrong as five bands: 357 areas hold no such land and tie in the lowest band, and an area with a little of each kind stands above an area with much of one |
| Leafy | **Made.** Its `cannot_see` says that a wood that is a public park is counted twice, by woodland and by public parks. It is served on core's recipe | No file of woodland outlines is held, so the figure cannot be put right. In 13 areas 2 in 100 of the land or more must be counted by both |
| Parks close by | Nothing, until the founder decides on playing fields. It stays on 70 in 100 of its recipe. Changing the label of `park_facilities` brings the measure into the vibe at once | With playing fields read as parks, the order of areas is 0.57 the same |
| Family amenities | **Made.** `school_primary_nearby` and `play_space_proximity` are named together, so it gains a band where both are measured. A build that names no list of schools places it on play space and the park alone, at 60 in 100, and puts inner London first | It stays a vibe of places, and gains no part that counts residents |
| Built age | Nothing. With homes built since 2000 it rests on its whole recipe, and places 1,001 of 1,002 areas | |
| Village feel | Not served. It waits on the two measures of town centres | Section 1 |
| Going out and Food and drink | **Made.** Each ranks on places for each 1,000 homes, and Going out on cultural venues for each 1,000 homes. No recipe holds a count that is shown and never ranked on: `checked_recipe` refuses one | Decision 11, applied alike |
| Everyday on foot | **Made.** It reads the station, the GP, the pharmacy and the town centre from the near end of a distance | It holds 45 in 100 of its recipe, the town centre and the station, until the GP and the pharmacy are on a table or the food shop is measured. So it is not served |
| Family area, proposed | Not built. It waits on primary schools and play space, and on the proxy audit. On the parts held it is one census figure under a vibe's name | The design, section 5 |
| Young and busy, proposed | Not to be built as its recipe stands. On the parts held it finds the areas that Homes finds | The same |
| Settled, proposed | Not to be built | The same |

## 5. What a change must not do

- Do not name a straight line a walk, in a label, a sentence or a note.
- Do not change one label of a vibe's parts alone where that places the vibe at once. Name `school_primary_nearby` and `play_space_proximity` together, and `park_facilities` only after the founder has decided on playing fields.
- Do not serve a release that names the list of land use before the founder has looked at the maps. A build that names it places every area on Leafy and on Works and warehouses.
- Do not put a count of places of worship or of cultural venues on the map as a number before the founder has settled the distance at which two records are one venue, and a floor on how sure a record is.
- Do not write the proxy audit's row after a measure is served. Decision record 0006 asks for it first, for recorded incidents and for every measure that counts residents.

## 6. What the join left to do

The join is made. The words for how well off a place is are core's, with two readings, both of the place. The guard on a model stands over the reader of a whole search. The test of the areas most like an area holds both mends. Every generated file was made again. The decision record that was numbered 0030 is 0023.

| What | Why |
|---|---|
| The iPhone app | Its generated files are in step with the contract, and its sources and tests pass the compiler's type check. It does not yet draw an offer in its four parts, and the tests that name a figure have not been brought to the answers as they are now recorded. `make -C apps/ios check`, on a Mac with Xcode |
| A firm limit, in the rules and in the guard | **Made.** "Max", "up to", "at most" and "no more than" make a budget a firm limit. "At most", "max", "no more than" and "within" make a number of minutes one, and a range is firm at its longer end. The lists are core's, `FIRM_OF_MONEY` and `FIRM_OF_MINUTES`, and the guard and the scorer of the evaluation read them. Each was a call made for the founder, and is theirs to overturn |
| An area with no figure for what was asked | **Made.** It stands below every area that has one, and its card says which figure it has none for. It is never left out for it, and never scored as nought. A usual setting that nobody chose moves no area |
| One module for where London ends | Three modules say it: `derive/culture_reach.py`, `derive/nearest_by_postcode.py` and `derive/station_walk.py`. A test names the two that say it another way, so that a fourth is refused. The rule at the edge is to be made one |
| `derive/heritage_shapes.py` and `derive/station_shapes.py` | Each says in its first lines that it is to be folded into `cells/shapes.py` |
| The credit of a source | A release carries "[date]" and "[year]" in a credit as written. [The design of the heritage measures](heritage-measures.md), section 2.1, says what fills them. It moves the hash of every release |
