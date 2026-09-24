# The first vibes on London

Status: built on 2026-09-24, from the files fetched on 2026-09-23 for the lists `m1` and `m2-places`. It follows [the second build](m2-second-build.md), which stands as it was written. It is a dated snapshot.

**This is a preview, for the founder's eyes. No person has checked anything in it.** No figure here has been held against a map, a visit or a publisher's own page. Every count was made by a program. No audit has been run on any measure or on any vibe. It is a development build: it is never served to the public. Where a figure looks wrong, that is a finding and it is written down as one. Nothing was smoothed.

No figure here is said of a named neighbourhood, of a named area or of a named borough, and none is named. The figures on this page are counts, and London's lowest, middle and highest for each measure that is in the release. Every other figure is beside the release, in a folder that git ignores.

## 0. In short

| Question | Answer |
|---|---|
| What was built | One release, `lon-2026-09-24-21`: 1,002 areas, their outlines, nine measures and eleven vibes |
| What is new on the map | Five measures: transport noise, public parks and gardens, the nearest park, the nearest large park and main roads. Each was worked out before and left out |
| Which vibes have a band | Three of eleven: Homes, Parks close by and Quiet streets. Each rests on two of its three parts, and its sentence says so |
| Which have none | The other eight. Each has under 60 in 100 of its recipe measured. Section 5 says what each waits on |
| Does a vibe say something new | Parks close by does: it does not follow the centre of London or how close together homes stand. Quiet streets follows the centre in part. Homes follows it closely |
| What is still left out | Fine particles, water close by and what a home sells for. Section 3 |
| Did any figure move | No. Every figure of the four measures of the second build is the figure it was. The outlines and the areas are the same bytes |
| Does every figure trace | Yes. `burro-release check` passes with the committed receipts: 26,029 facts, 71,142 rows of evidence, no finding |
| Does the build repeat | Yes. Built twice from the same files and the same commit, all 18 files are the same byte for byte |
| What calls were made | Four, each in a commit of its own, each to be confirmed or undone. Section 4 |
| What to look at first | Section 9 |

## 1. What was built

| Thing | Value |
|---|---|
| Release | `lon-2026-09-24-21`, built at `2026-09-24T07:00:00Z`. It is an input and not the clock. It is the hour of the last commit, and it had passed when the step was run |
| Command | `make preview ARGS="--release-id lon-2026-09-24-21 --built-at 2026-09-24T07:00:00Z --out data/releases --list m1 --list m2-places"` |
| Commit of the code | `370cbea`, read from the repository by the step, which refuses to build where a tracked file has changed |
| Packages | Not held by hash: no lockfile is committed. So it is a development build |
| `manifest.json`, SHA-256 | `e6b9b75a98cd74a386119557f4f7b6f03b27e3d651fbbbc9b89fc529e8b7302b` |
| `evidence.json`, SHA-256 | `5d9d33ce6f2eb84cdc6c5810bdaa7db948437d63a77254205ea5719fb6223e9c` |
| `lock.json`, SHA-256 | `3b746583a4bf1424235afd5e8cc21192fc75d1b79f6c9bebf0e605f4d25d4ff3` |
| `coverage.json`, SHA-256 | `67b1f3d5f529b0ec9595dfb95584d38e993d1f9702bad6ed96015ce2443cbd83` |
| Schema, catalogue and engine | Schema 2, catalogue 5, engine 1.8.0. The catalogue went from 4 to 5 with the names of section 4. No arithmetic moved |

The first three hashes are what `hashes.json` holds. No program holds the release to the hashes printed here.

| Thing | Count |
|---|---|
| Output areas, LSOAs, areas, boroughs | 26,369, 4,994, 1,002 and 33, as in the first build |
| Facts the release would show | 26,029: a label for each of 1,002 areas, 8,995 figures, a fact for each of 11 vibes in each area, and 5,010 of likeness |
| Rows of evidence | 71,142: one for every pair of an area and a thing Burro measures |
| Files in the lock | 52. 33 of them are the food hygiene register, which no measure reads yet |
| Files behind a figure | 13 |
| Files of the two lists with no receipt | 4: the town centres, the conservation areas, the listed buildings and the postcode directory |
| Seconds to build | About 60 |

## 2. The measures in the release

| Measure | Unit | The data is of | Areas with a figure | Lowest | Middle | Highest | Different figures | Ranked on | How it is made |
|---|---|---|---|---|---|---|---|---|---|
| Modelled annual mean nitrogen dioxide | µg/m³ | 2024 | 1,002 | 8.8 | 17.4 | 32.7 | 181 | Yes | Modelled |
| Public parks and gardens as a share of the area | % | April 2026 | 1,002 | 0.0 | 3.3 | 78.1 | 242 | Yes | Measured |
| Homes per hectare | per ha | 31 March 2025 | 1,002 | 1.3 | 32.2 | 154.8 | 587 | Yes | Measured |
| Flats as a share of homes | % | 31 March 2025 | 1,002 | 1.7 | 53.5 | 99.0 | 595 | Yes | Measured |
| Homes built before 1919 | % | 31 March 2025 | 979 | 0.0 | 23.4 | 97.2 | 518 | Yes | Measured |
| Share exposed to 55 dB or more of transport noise | % | 2021 | 1,002 | 15.1 | 50.5 | 100.0 | 532 | Yes | Averaged |
| Straight-line distance to the nearest marked way into a park of 20 ha or more | m | April 2026 | 1,002 | 120 | 1,030 | 4,290 | 260 | Yes | Measured |
| Straight-line distance to the nearest marked way into a park of 2 ha or more | m | April 2026 | 1,002 | 110 | 450 | 2,020 | 123 | Yes | Measured |
| Share of homes within 100 m of a main road | % | April 2026 | 1,002 | 0.0 | 23.4 | 91.2 | 468 | No: it is shown | Measured |

Credits for the figures above, in each publisher's own words as the licence registry holds them:

- Nitrogen dioxide: © Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL).
- The three measures of homes, and transport noise: Contains public sector information licensed under the Open Government Licence v3.0.
- Public parks and gardens, and the two distances to a park: Contains OS data © Crown copyright and database right 2026.
- Main roads: Contains OS data © Crown copyright and database right [year].
- The geography behind each: Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

`[year]` is the registry's own placeholder. No year was made up.

What each figure cannot see is in `build.json` beside the release. The contract still has nowhere to carry it.

## 3. What was worked out and is still left out

| Measure | Why it is not in the release | What would bring it in |
|---|---|---|
| Fine particles, PM2.5 | Core holds no feature for it, so a build makes no row for it. The call was that it comes in shown and not ranked on, if the catalogue has a way to say so. A row of a release can say that a measure is shown and not ranked on. A feature of core cannot, and there is no feature. To add one changes the list of features, which the API's contract, the website's types and the app's models are made from | A feature `air_pm25` in core, with its row in the contract and the clients made again. The list `m2-living` named to the build. The registry asks for the feature before the figure is used. It differs little across London and follows nitrogen dioxide |
| Water close by | It reads nought beside wide tidal water, because its file draws a river as a line with no width. It reads high where a long straight stretch may run under the ground. A build works it out and leaves it out, by the rule `measure_is_as_core_says` | Homes or land, and whether a lake counts. A registered source for the bank of wide water, or a name that says from the middle of the water. A person to look at each long straight stretch |
| What a home sells for | The licence registry holds its source for checking only, and not for showing | A change to the registry, then a feature in core. The file gives no count of sales and no quartile |

Asked of the API, a wish for water close by is refused: `422`, `not_in_release`. Typed as "by the river", the wish is made, rejected as `not_in_release`, and the list that comes back is ranked by the usual settings. No figure of water is served.

## 4. The calls that were made, to be confirmed or undone

Each is in a commit of its own, with its test first. Each was made for the founder, who has not yet seen it. The four commits revert cleanly in the order last to first. One in the middle, reverted alone, leaves conflicts to be settled by hand: in the lists of measures that the tests hold, and in the made-up release, which is made again with `make fixture`.

| # | Call | What was done | Commit | To undo |
|---|---|---|---|---|
| 1 | Transport noise comes in, named for what its file holds | Core named it a share of homes. It is now "Share exposed to 55 dB or more of transport noise", and is said to be averaged. **The name does not say residents.** Two tests that guard the rule on ranking places and never residents refuse that word: one in the name of anything that can be ranked on, and one in any file of a release. A third fails with it, because the reader of sentences hears such a name as a request about who lives somewhere, and applies nothing. None of the three was loosened. The sentence of the measure says residents in full | `50aae7c` | Revert it. Noise is then left out, and Quiet streets has no band. To have the name say residents, the first two tests must let the one phrase pass, as they do "per 1,000 residents a year", and the third must let the name of this one measure go unread. That is the founder's to say |
| 2 | Public parks and gardens come in, and are never called green space | The name is "Public parks and gardens as a share of the area", the wish is "More public parks and gardens", and an area has more or less of it. No word says green space or greener. It is a share of land, as it is built | `11bacd2` | Revert it, after 3 and 4. It is then left out |
| 3 | The nearest park and the nearest large park come in, each as a straight line | Each is named "Straight-line distance to the nearest marked way into a park", of 2 ha and of 20 ha or more, and is said to be measured from points | `e5e8249` | Revert it, after 4. Both are then left out, and Parks close by has no band |
| 4 | Main roads come in as the catalogue defines them | The row is core's: "Share of homes within 100 m of a main road". **The release shows the figure and ranks no area on it alone**, as the measure proposed and its test holds, because no audit has been run. Quiet streets rests on it all the same | `2accee9` | Revert it: it reverts alone. Main roads are then in no build, and Quiet streets has no band. To rank on the figure, set `RANKABLE` to true in `derive/road_major_exposure.py` and turn its test round |

Three calls left a measure out, and changed nothing: fine particles, water close by and what a home sells for. Section 3.

Two things were done that no call named, because a call could not be made without them:

| What | Why |
|---|---|
| One line of a test of the API was changed: the version of the catalogue it expects is 5 | Core's rule is that any change to a feature moves the version. No route and no record changed, and the contract is the same bytes |
| The made-up build of the tests gained roads of its own | A build now reads the roads, and the made-up roads of the measure's own tests stand where no home of the made-up build does |

The made-up release was built again, because it repeats core's names. Its figures did not move.

## 5. The eleven vibes

Core places an area on a vibe where 60 in 100 of its recipe is measured. No recipe and no share was changed.

| Vibe | In the release, of its recipe | Band | What it waits on |
|---|---|---|---|
| Homes | 75 in 100: flats 40, homes per hectare 35 | Yes, in all 1,002 areas | Homes with private outdoor space, 25. The design holds it back for an audit |
| Parks close by | 70 in 100: the nearest park 40, the nearest large park 30 | Yes, in all 1,002 areas | What there is to do in parks, 30. No measure is built |
| Quiet streets | 70 in 100: main roads 40, transport noise 30 | Yes, in all 1,002 areas | Homes near a cluster of evening venues, 30. It needs the venues |
| Built age | 35 in 100: homes built before 1919 | No | Conservation areas, 25, and listed buildings, 20: each file is in the list and has no receipt. Homes built since 2000, 20, which the table of homes by period holds and no measure works out. That alone would bring it to 55, which is too few |
| Leafy | 30 in 100: public parks and gardens | No | Garden land, 40, and woodland, 30. No source is registered for either |
| Family amenities | 25 in 100: the nearest park | No | Play space, 35, and primary schools, 40. The file of parks holds play spaces, and no measure reads them. Play space and the nearest park are 60 in 100, which is just enough |
| Village feel | 20 in 100: homes built before 1919 | No | Independent places, the town centres and conservation areas |
| Pace | None | No | Venues, the high street and culture. The food hygiene register is in the lock, and no measure reads it |
| Food and drink | None | No | The same venues, and kinds of food |
| Everyday on foot | None | No | A network to walk on, and every place to walk to |
| Works and warehouses | None | No | The table of land use. No source is registered |

So most vibes have no band: eight of eleven. In 23 areas Built age and Village feel rest on nothing at all, because the publisher withholds the count of old homes there.

Gritty is carried as land use. The scale that counts recorded crime is refused on any release that is not made up, as before.

## 6. Does a vibe on London say something

Each vibe that has a band puts about a fifth of the areas in each band: 201, 200, 201, 200 and 200, from band 1 to band 5. That is how a band is made, and says nothing of London.

What follows was worked out across the 1,002 areas. The centre is the middle of London's homes: the mean of the points inside the areas, each weighed by its homes at the census. The rank correlations are beside the release, with the table for each borough. No figure of them is on this page.

| Vibe | With homes per hectare | With distance from the centre | In words |
|---|---|---|---|
| Homes | Very close | Close | It is the centre again. Flats and homes per hectare follow each other and follow the centre, and the vibe is made of both |
| Parks close by | None | Next to none | It says something new. An area near a park is as likely to be at the edge as in the middle |
| Quiet streets | Moderate, the other way | Moderate | About half of it is distance from the centre. With distance taken out, how close together homes stand adds little |

| Between two vibes | In words |
|---|---|
| Homes and Quiet streets | Moderate, the other way: flats are less quiet |
| Parks close by and either of the others | None |

| Between the parts of one vibe | In words |
|---|---|
| Flats and homes per hectare | Close. The two parts of Homes are near to one part |
| Main roads and transport noise | Moderate. They agree in part, and each adds something |
| The nearest park and the nearest large park | Weak to moderate. In 157 areas the nearest park is a large one, and the two figures are the same |

A first look at venues found that everything tracked the centre. Here one vibe of three does not, one does in part, and one does closely. Of the five measures that came in, two follow the centre in part, which are transport noise and main roads. The three of parks do not follow it at all.

### By borough

No borough is named. A borough is inner, middle or outer by where the mean of its areas stands among the 33, in thirds.

| Vibe | Where band 5 is | Where band 1 is |
|---|---|---|
| Homes, towards Flats | The six boroughs with the greatest share of their areas in band 5 are all inner, and in each it is two areas in three or more. Twelve boroughs of more than one area have no area in band 5 | Five of the six boroughs with the greatest share in band 1 are outer. Eleven boroughs of more than one area have none |
| Parks close by | Every borough of more than one area has an area in band 5. The six with the greatest share are three inner, two middle and one outer. In one outer borough to the east it is over half the areas | Every borough has an area in band 1. In two boroughs of more than one area, one to the north-east and one to the north-west, it is over half the areas |
| Quiet streets | Four of the six boroughs with the greatest share are outer, and none is inner. In one outer borough to the east it is over two areas in three. Three boroughs of more than one area have none | Five of the six with the greatest share are inner. The sixth is an outer borough to the west, with nearly half its areas in band 1 and none in band 5 |

## 7. Three sentences, as a person types them

Read through the API's test client, on the release. No model was called: the rules read each. Every answer said that the release is real and is a preview, in the body and in the headers. No answer was a server error. No line of the log held a word that was typed or the id of an area.

| Typed | Applied | Offered | Refused | What comes first |
|---|---|---|---|---|
| "leafy and quiet" | Leafy and Quiet streets, each as stated | Nothing | Nothing. Leafy has no band in any area, so every result says "There is no Leafy figure", and the list is ranked by Quiet streets and the usual settings | Areas in band 5 of Quiet streets: all of the first twenty. The first five are in four outer and middle boroughs |
| "period homes, clean air" | Homes built before 1919 and nitrogen dioxide, each as assumed | Nothing | Nothing | **The first five areas have no figure for homes built before 1919.** So have eight of the first ten. Each is ranked on its air alone. Section 8, row 1 |
| "somewhere lively near a big park" | Parks close by, as stated, and Pace towards Buzzy, as assumed | Nothing | Nothing. Pace has no band in any area, so every result says "There is no Pace figure" | Areas in band 5 of Parks close by: all of the first twenty. The first five are in outer and middle boroughs to the south and east |

What else was tried:

| Asked | Answer |
|---|---|
| A vibe with no band, alone: Leafy, Pace, Built age | Every area is unranked. No list is given |
| Quiet streets, Parks close by or Homes, alone | Every area is ranked |
| "away from main roads", "by the river" | The wish is made and rejected as `not_in_release`. The list that comes back is ranked by the usual settings |
| "green space" | Read as public parks and gardens, as stated, and ranked on |
| "flats near a big park on a quiet street" | Nothing is applied: it is not a plain list. Parks close by and Quiet streets are offered |

An area is a census area with a plain label, which is its borough and a number. No neighbourhood has a name yet.

## 8. What looks wrong

| # | What | Why it matters |
|---|---|---|
| 1 | **Asked for period homes and clean air, the first five areas have no figure for period homes.** The publisher withholds the count in 23 areas. The engine leaves the measure out of their score and ranks each on the rest, and their air is clean | An area with no figure for what was asked comes first. The engine ranks an area that has a figure for half of what counts, and these have. Asked for period homes alone, the 23 are unranked, as they should be |
| 2 | **A vibe with no band is applied, and then left out of every score.** "Leafy and quiet" is ranked by quiet alone, under both words | The answer is honest in its parts: every result says there is no Leafy figure. Nothing says what Leafy waits on, and a person who does not read the line sees a list under their own words |
| 3 | **Parks close by reads far where the publisher maps no public park.** In two boroughs over half the areas are in band 1, and the middle area of each has under 1.5 in 100 of its land in a public park or garden. A common, a heath, a forest or a country park that is mapped as something else is not counted | The design asks that 20 named commons, heaths and forests are looked for in the file before a figure of parks is shown. That check has not been made, and three measures of parks are now on the map |
| 4 | **Homes is how central an area is, under another name** | The two parts that are measured are near to one part, and both follow the centre. The third part would not |
| 5 | **Quiet streets is half distance from the centre.** One outer borough breaks the pattern: its main roads stand near the middle of London's, and its noise is the highest of any borough of more than one area. The file of noise does not say which kinds of transport were counted | It is the one place where the vibe says something the map of the centre would not. It is worth a look on a map |
| 6 | **Transport noise reads high.** In the middle area half of the residents are exposed, in 54 areas it is nine in ten or more, and in 4 it is all | The level of 55 dB is low for a city. The figure tells the quietest areas apart well, and the loudest poorly |
| 7 | **The distance to a park is a straight line.** 879 areas are within 800 metres of a way in, and the figure takes only 123 different values | A railway or a river in between is not seen. The figure at which a walk is never given as a trade-off, 800 metres, was chosen for a walk |
| 8 | **Main roads are shown and not ranked on, and Quiet streets rests on them for 40 of its 70.** A wish to be away from main roads is rejected, and a wish for quiet is ranked on the same figure | Core places a vibe on every part a release holds. A release has no way to show a part and keep it out of a vibe |
| 9 | **No audit has been run on any measure or any vibe.** The design expects main roads and how close together homes stand to follow who lives somewhere | The design says a vibe ships on real data only once it has passed the audit. This is a preview, and ships nothing |
| 10 | **Public parks and gardens read nought in 134 areas**, and main roads in 109 | Nought is a figure here: the publisher maps no park there, and no home is placed within 100 metres of a main road. Each is a true reading of its file, and may not be a true reading of the place |
| 11 | **"Green space" is read as public parks and gardens, as stated** | The chip says what the measure is. The word was the person's, and the measure is narrower |
| 12 | **Likeness now counts on four measures, and three are of one file of parks** | Two areas are then alike mostly by their parks |
| 13 | **Everything the second build listed still stands**: the service is not proof that a release is what was built, the one date beside every source of a fact, `[year]` in the credits, homes weighed as at 2021 | [The second build's page](m2-second-build.md), section 8 |

## 9. What to look at first

In the order to look.

| # | What | What would settle it |
|---|---|---|
| 1 | Type "period homes, clean air", and read the first five results | Decide whether an area with no figure for what was asked may be ranked at all, or may come first. It is a rule of the engine |
| 2 | The name of transport noise. It says "Share exposed", and not "Share of residents exposed" | Say whether the name may say residents. If it may, two tests let the one phrase pass, and the reader of sentences is looked at |
| 3 | Colour the map by Parks close by, and look at what you know to be a common, a heath or a forest | Give the list of 20. If band 1 lies beside them, the file does not map them as parks, and the measure needs another source or another name |
| 4 | Colour the map by Quiet streets, and look at the outer borough to the west | Say whether noise that is not from a road belongs in a vibe called Quiet streets |
| 5 | Whether main roads may be ranked on alone | One line, and its test |
| 6 | Whether a vibe may be shown on a release on which no audit has been run | The contract lists it in section 13 |
| 7 | Which vibe comes next. Play space is in the file of parks, and would bring Family amenities to 60 in 100 | Approve a measure of play space |

## 10. How it was checked

| Check | Result |
|---|---|
| `make ci`: the registry, lint, strict types, and every test | Passes |
| `make eval-reader` | Passes: all 53 plain cases are applied, and none is read backwards |
| The tests on the real files, with the store named | All pass |
| Built twice from the same files and commit | The 18 files are the same byte for byte. The step printed the same lines |
| `burro-release check`, with `--receipts data/receipts` | Passes: `lon-2026-09-24-21: 1002 areas (1002 rankable), 9 measures, 0 destinations, 0 places, 0 stations, real, a preview, with evidence behind every fact` |
| The four measures of the second build, against the release before | All 4,008 rows are the same: every figure, every percentile and every share covered |
| The API on the release, through the test client | The areas, one area, the three sentences of section 7 with the ranking and the reasons of each, seven sentences more, and a ranking alone by six vibes and by six measures. Every response said `synthetic: false` and `preview: true`. No log line held an area's id or a word that was typed |
| The store | Read, and never written to |

What was not checked:

| Not checked | Why |
|---|---|
| Any figure or any band, by a person | None has been held against a map, a visit or a publisher's page |
| The check of 20 commons | The list is the founder's to give |
| An audit of any measure or vibe | None is built |
| The website on this release, in a browser | The API was driven through the test client |
| A build on the platform of record | Nothing ran in hosted CI. Nothing was pushed |
| Any new measure against a published total | No file in the store holds one |

## 11. How to see it

In a working copy of the branch that holds this page, with everything committed, and with `BURRO_STORE_FOLDER` naming the folder that is the store:

| # | Where | Run | You should see |
|---|---|---|---|
| 1 | The top of the repository | `make preview ARGS="--release-id lon-2026-09-24-21 --built-at 2026-09-24T07:00:00Z --out data/releases --list m1 --list m2-places"` | Nine lines of `step=derive status=ok`, one of `step=derive status=skipped` for water close by, and a last line that starts `step=report status=ok`. If the folder is there already, skip this step or give a new id |
| 2 | The same | `uv run burro-release check data/releases/lon-2026-09-24-21 --receipts data/receipts` | `lon-2026-09-24-21: 1002 areas (1002 rankable), 9 measures, 0 destinations, 0 places, 0 stations, real, a preview, with evidence behind every fact` |
| 3 | A first terminal, at the top of the repository | `BURRO_RELEASE_DIR=data/releases/lon-2026-09-24-21 make api` | One line that holds `"preview":true` and `"synthetic":false` |
| 4 | A second terminal, in `apps/web` | `NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:8000 npm run build`, then `NEXT_PUBLIC_BURRO_API_URL=http://127.0.0.1:8000 npx next start -H 127.0.0.1 -p 3000` | The website on `http://localhost:3000`, with the banner that says it is a preview |

Run step 2 before step 3, each time. [The guide to data builds](../../data-builds.md), sections 15 and 16, says what to do first and what to do when a step stops. Built at another commit, the lock has another hash, and so have the hashes of section 1.
