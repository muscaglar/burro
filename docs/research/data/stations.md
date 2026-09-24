# The nearest station, and the stations as places

Worked out on 2026-09-24, from the file of London's stops that a person saved that day. A dated snapshot, not a source of truth. Nothing here is legal advice. No lawyer has read it.

No person has checked a figure on this page. Every count was made by a program. No figure is of a named neighbourhood. A count for a borough is named with its borough.

It is written for whoever decides what Everyday on foot rests on, and for whoever builds journeys. The file itself is described in [by-hand-files.md](by-hand-files.md).

## 0. In short

| Question | Answer |
|---|---|
| What was built | The distance in a straight line from where homes are to the nearest way in to a station, for every area. And the table of stations as places a person can name |
| Is it a walk | No. It is a straight line, in metres. No network of streets is built |
| How many areas have a figure | 970 of 1,002. The lowest is 170 metres, the middle 570 and the highest 2,800 |
| Why 32 have none | The file is London's alone. In those areas most homes stand nearer to land outside London than to any station that was found |
| Does a release carry it | No. Core names the measure a walk in minutes. A build works it out and leaves it out. Section 3 says what core needs |
| Does a vibe gain a band | No. The measure is 20 in 100 of Everyday on foot, and a band needs 60 |
| Can a person name a station | Not yet. The table is made, with 641 stations. A release holds a place only with a journey's end, and no build makes one |
| Does it give a journey time | No. Section 7 says what one needs |

## 1. One station is many rows

The file holds 21,288 rows. Each is one point where a person gets on or off. The publisher's schema guide, version 2.5, names the types in its table 3-6. Five are in the file.

| `StopType` | The guide's name for it | Rows | Of them active |
|---|---|---|---|
| `BCT` | Bus or coach stop on a street | 20,026 | 20,023 |
| `TMU` | Tram / Metro / Underground Entrance | 642 | 642 |
| `RSE` | Rail Station Entrance | 550 | 549 |
| `FTD` | Ferry Terminal / Dock Entrance | 42 | Not read |
| `BCS` | A bay of a bus or coach station | 28 | 28 |

**The file holds the ways in to a station, and never the station.** The guide gives a station three types: a way in from the street, an area inside, and a platform. It says who issues each, in its section 3.5.1: "Entrance records are provided by the Local Administrative Area", and the area inside and the platforms "will be provided centrally". So the file of an authority holds the ways in alone. The station, its platforms and the group that joins them are in the national file, under the authorities the form lists as 910 for railways and 940 for trams, metros and the Underground.

**Which types are a station.** Two: `RSE` and `TMU`.

| What a person calls it | In the file as | Can the file tell it apart |
|---|---|---|
| A railway station | `RSE` | Yes, from the second kind |
| The Overground | `RSE` | No. No column says whose trains call |
| The Elizabeth line | `RSE` | No. The same |
| The Underground | `TMU` | Only by a hint |
| The DLR | `TMU` | Only by a hint |
| A tram stop | `TMU` | Only by a hint |
| The cable car | `TMU` | Only by a hint. The guide has types of its own for a cable car, and the file does not use them |

The hint is two letters that most codes of a way in of the second kind hold after `ZZ`. The guide uses such a code in its example of a station, and defines no letters. So the letters are counted here and no figure turns on them.

**How rows are gathered into one station.** The file holds no group of stops. The guide asks, in the same section, that the stops of one station "should have the same CommonName, with a different Indicator value to distinguish them if necessary". So a station is the ways in of one kind that share a name, each within 1,000 metres of another of them. In this file the rule of distance decides nothing: no name is two stations, and the widest station is 512 metres across.

The code does not gather them. The guide says the main way in ends in 0 and the others in another digit, so a code without its last digit should name the station. In the file it does not: 343 such stems stand for 340 names of railway stations, and 323 for 301 of the second kind. One station has ways in under six stems.

| | Railway | Tram, metro or underground |
|---|---|---|
| Ways in that are active | 549 | 642 |
| Stations | 340 | 301 |
| Stations with one way in | 193 | 135 |
| The most ways in to one station | 7 | 13 |

16 names are a station of each kind: a railway station and an underground station that share a name are two rows. One of the 16 is a single row of type `RSE` whose name says an underground station. It is counted as the file types it.

**641 is a count of rows of a kind and a name, and not of buildings.** No station is counted twice under two names of one kind: six pairs of names of one kind have ways in within 100 metres of each other, and each pair is two stations that the file names apart. No name holds two stations. But a station that is both a railway station and an underground station is a row of each kind. With the closing words of kind set aside, the 641 rows hold 605 names. 35 of those names are a row of each kind, and one of the 35 is three rows, because the file holds two stations of the second kind under it.

**Against what the operator says it runs.** Transport for London's page "What we do" was read on 2026-09-24, through a reader that extracts.

| Kind | By the letters of the code | What the operator's page says | What stands between the two |
|---|---|---|---|
| The Underground | 215 stations | "11 lines covering 402km and serving 272 stations" | The file is London's alone, and the Underground runs past London's edge. A station whose way in is a railway station's is `RSE` here. Two stations that are the Underground by their names hold other letters, and two hold none |
| The DLR | 41, and one railway station whose code holds its letters | No count on the page | Not known |
| Trams | 37 | No count on the page | Not known |
| The cable car | 2 | It "connects the Greenwich Peninsula with the Royal Docks" | None. Both ends are in the file |
| No letters, or other letters | 6 | | |
| Railway, the Overground and the Elizabeth line together | 340 | No count on any page that was read | No operator runs them all. The page says the Overground is "a group of 6 routes" and gives no count of stations |
| Stops of buses | 20,023 on a street, and 28 bays | "more than 19,000 bus stops" and "around 50 bus stations" | The stops agree with the page. The bays are not held against it: a bay is one stand inside a bus station, and the file holds no row for a bus station itself |

The operator's pages for the DLR, the trams, the Overground and the Elizabeth line were read too. None states a count of stations. So only the Underground and the buses are held against a count the operator states, and the Underground differs by 57. That is not a fault found in the file: it is what a file of ways in, for London alone, cannot show.

## 2. The measure

`derive/station_walk.py` works it out, and `derive/stops_file.py` reads the file.

| | |
|---|---|
| The file | `490Stops.csv`, saved by a person on 2026-09-24. Its receipt says `by_hand` |
| Its edition and period | `saved 2026-09-24`, and that day. The file holds no day of its own |
| Columns read | Six: `ATCOCode`, `StopType`, `Status`, `GridType`, `Easting`, `Northing`. The name is not read. The file holds 43 |
| What counts | Every active row of type `RSE` or `TMU`: 1,191 ways in |
| Where homes are | The centre of population of each output area, from the statistics office |
| The method | `straight_line_to_nearest@1`, as for the distance to a park: from each centre to the nearest way in, then the median over the area's homes, to the nearest 10 metres |
| The edge | A distance is known only where the nearest way in is no further than the nearest land outside London. Section 5 |
| Other files a figure rests on | The centres, the lookup, the table of homes, and the outlines of LSOAs, which give the land outside London |

**Every figure is a straight line.** It is measured across whatever lies between, to a way in and never to the middle of a station. The walk is longer.

What it came to:

| | |
|---|---|
| Areas | 1,002 |
| With a figure | 970 |
| Of those, with every home counted | 905 |
| With a figure and some homes left out | 65 |
| With no figure, under half the homes counted | 25 |
| With no figure, no home counted | 7 |
| The lowest, the middle and the highest | 170, 570 and 2,800 metres |
| A tenth of areas are at or under | 320 metres |
| A tenth are at or over | 1,160 metres |
| Different figures | 159 |
| Areas at or under 800 metres | 716 |
| Output areas whose distance is known | 25,375 of 26,369 |
| Homes within 400, 800 and 1,200 metres of a way in | 31, 71 and 90 in 100 of the homes whose distance is known |

| Against | Rank correlation | In words |
|---|---|---|
| Homes per hectare | -0.48, over 970 areas | Moderate, the other way: where homes stand closer together a station is nearer |
| Distance from the centre | 0.48 | Moderate: further out, a station is further |

The centre is the middle of London's homes: the mean of the centres of the output areas, each weighed by its homes at the census. An area's distance from it is measured from the middle of the area's own homes.

So about a quarter of what orders the areas is how far out they are. The rest is its own: an area far out that has a station beside it reads near, and the figure says so.

What it cannot see:

- **The walk.** A railway, a river or a main road between a home and a station makes the walk longer than the line.
- **Which trains call, how often, and where they go.** A tram stop and a terminus count the same. The cable car counts as a station.
- **A station past London's edge.** Section 5.
- **A way in that is shut, or has steps.** The file says whether a row is active. It says nothing of steps.
- **Where in its output area a home stands.** Every home of an output area is measured from one point.
- **A station that has opened or closed since the file was saved.** The latest day any row was changed is 2026-09-15, and the latest day a way in to a station was changed is 2026-09-09. Both were read once for this page, from the column `ModificationDateTime`. No step of a build reads that column, and no figure rests on it.

## 3. What core needs

Core's catalogue names the feature `station_walk` "Walk to the nearest station", in minutes, measured on a network. The figure is none of the three. A build holds a measure to what core says of it, so this one is worked out and left out, by the rule `measure_is_as_core_says`. Nothing in `packages/core` was changed.

For a release to carry it, core changes four things together:

| In core | Today | What the figure is |
|---|---|---|
| The label of `station_walk` | "Walk to the nearest station" | "Straight-line distance to the nearest way in to a station" |
| Its unit | `min` | `m` |
| The figure at which it is never a trade-off | 10, which is minutes | A distance in metres. The distance to a park has 800 |
| What it is measured on | A network | Points. A build is not held to this one |

And three things follow from them:

- **The synthetic release.** Its generator writes `station_walk` in minutes, as the walk to the nearest station of `stations.json`. It would write metres, and the fixture is made again.
- **The contract.** Section 2.9 says the feature repeats the walk to the nearest station and is never under 2 minutes. That sentence goes. The table of features in section 3.1 holds the label and the unit, and its row changes with core.
- **The website and the app.** Their recorded answers hold the label and the unit, and are recorded again.

The founder confirmed on 2026-09-24 that a distance says it is a straight line. This is the same change, for one more measure. There is another way: core keeps `station_walk` for the walk, and gains a feature for the straight line, as it has for a park. The recipe of Everyday on foot would then name the new one until the walk is built. So would the two things in core that name `station_walk` beside the recipe: the weights a search starts with, where nothing weighs more for a renter or for a buyer, and the words "near a station" in the lexicon. Left as they are, each would rest on a feature that no release of London carries.

A preview was built as if core said the same, with core's catalogue changed in memory for the one run. It carried the measure for 970 areas and `check` found nothing. So the four changes are all that core's own rules ask. It was built to see that, and is served to nobody.

**What it does for a vibe.** Everyday on foot gives the nearest station 20 in 100. With the measure carried, 970 areas have 20 in 100 of the recipe and 32 have none. A band needs 60. So no area gains a band, and no vibe changes.

## 4. The nearest stop of a bus

Worked out the same way, to the nearest active stop on a street or bay of a bus station. No build carries it, and core has no feature for it.

| | The nearest station | The nearest stop of a bus |
|---|---|---|
| Areas with a figure | 970 | 1,002 |
| The lowest, the middle and the highest | 170, 570 and 2,800 metres | 60, 130 and 380 metres |
| A tenth of areas are at or under | 320 | 100 |
| A tenth are at or over | 1,160 | 180 |
| Different figures | 159 | 27 |
| Areas within 100 metres of the middle figure | 27 in 100 | 98 in 100 |
| Homes within 400 metres | 31 in 100 | 98 in 100 |
| Rank correlation with homes per hectare | -0.48 | -0.36 |
| Rank correlation with distance from the centre | 0.48 | 0.40 |

**It does not tell areas apart.** Eight areas in ten read between 100 and 180 metres. A home may stand 100 metres from the centre of its output area, so that spread is inside what the method cannot see. Nearly every home in London is near a stop. What would tell areas apart is how many buses call and where they go, which is a timetable and not a file of stops.

The rank correlation between the two distances is 0.28. The distance to a stop of a bus is not the distance to a station over again, and it is not much of anything else either.

## 5. The edge

The file holds the stops of London and no other. One way in of the 1,191 stands on no land of London, 46 metres past the edge. So a home near the edge may have a nearer station outside, in a file that was not read.

The rule: the distance of an output area is known only where the nearest way in that was found is no further than the nearest land outside London. Land outside London is the outline of every LSOA that the lookup gives to no London borough. Water is no land, so a home beside the tidal river is at no edge.

| | |
|---|---|
| Output areas whose distance is not known | 994 of 26,369 |
| Homes in them | 127,165 of 3,423,767, which is 3.7 in 100 |
| Areas that hold such a home | 97 |
| Of those, with a figure from the homes that are left | 65 |
| Of those, with no figure | 32 |
| Boroughs that hold such an area | 14, all of them outer boroughs |

| Borough | Areas the edge touches | Of them with no figure |
|---|---|---|
| Havering | 13 | 5 |
| Hillingdon | 11 | 4 |
| Sutton | 9 | 3 |
| Croydon | 8 | 3 |
| Kingston upon Thames | 8 | 3 |
| Redbridge | 8 | 5 |
| Bromley | 7 | 2 |
| Barnet | 6 | 1 |
| Harrow | 6 | 0 |
| Bexley | 5 | 1 |
| Enfield | 5 | 1 |
| Hounslow | 5 | 2 |
| Waltham Forest | 4 | 1 |
| Richmond upon Thames | 2 | 1 |

**How they are marked.** The row of evidence of each area holds the share of its homes that was counted, and its state: `partial` for the 65, and `below_threshold` or `source_gap` for the 32. The measure lists the areas and the output areas under `edge`. No figure is put in their place.

**The rule leaves out more than it must.** It asks whether a nearer station could lie outside, and not whether one does. Most of the 994 will keep the distance that was found once the stations outside are read.

**How the edge is closed.** With the national file. It is listed in `m2-living` as `naptan-national`. The registry entry names its address, and it was fetched on 2026-09-24:

| | |
|---|---|
| Its address | `https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv` |
| Where it was read | The record of the dataset at data.gov.uk, which names the Department for Transport as its publisher. Read twice on 2026-09-24, in different words |
| The publisher's own page | `https://beta-naptan.dft.gov.uk/download/national`. It offers the same file from a form, and names that host as its API. It writes no address of a file |
| Its receipt | `f-7fbe1ec6aaff`, fetched, for scoring. The publisher names the file `Stops.csv`. 101,596,247 bytes |
| Its edition | `retrieved 2026-09-24`. The file states none, and is made again each day under one address |
| The licence | The same entry, `dft-naptan`: the Open Government Licence v3.0 |

**What the national file holds.** It was read through the gate and its receipt, for its types, its statuses and its grid alone. No name was read.

| What | The national file | The file of London |
|---|---|---|
| Columns | The same 43, in the same order | 43 |
| Rows | 435,633 | 21,288 |
| A type or a status the guide does not name | None | None |
| A code that stands twice | None | None |
| Rows with no grid named | 15,672, none of them an active row of a station | None |
| Active ways in to a railway station, `RSE` | 3,730, of which 549 are London's | 549 |
| Active ways in to a tram, metro or underground station, `TMU` | 1,419, of which 642 are London's | 642 |
| Active railway stations, `RLY` | 2,672, all under the authority 910 | None |
| Active metro and underground stations, `MET` | 954, of which 942 are under 940 | None |
| Active platforms, `RPL` and `PLT` | 3 and 1,572 | None |

So the ways in of London are in the national file as they are in London's own, and the stations that London's file lacks are there with a code of their own.

**No measure reads it yet.** What each must change to read it:

| Where | What changes |
|---|---|
| `derive/stops_file.py`, `is_the_file` and `open_the_file` | They hold the name of the file to `490Stops.csv`. The national file is named `Stops.csv`. The reader opens the national file by that name, and `AUTHORITY` no longer names a file. Both files are of one source, so the name is what tells them apart |
| `derive/stops_file.py`, `read` | It keeps the rows within reach of London and drops the rest, by where a row is and never by its authority: a way in outside London is of another authority. It holds the point of a row to the grid only where the row is kept, as it does today. 15,672 rows name no grid, and a step that reads the stops of a bus must not stop on one that is far from London |
| `derive/station_walk.py`, the rule of the edge | It goes. `outside_london`, `_edge` and `_land_outside` leave out a home that stands nearer to land outside London than to any way in that was found. With the ways in of every authority read, the nearest is known. What is left is a margin: the file is read out to the furthest distance a home of London was found to stand from a way in, and a test holds that |
| `derive/station_walk.py`, `DEFINITION` and `CANNOT_SEE` | Neither says any longer that the file holds no station outside London. 994 output areas in 97 areas are left out today, and 32 areas have no figure. Each then has one |
| `derive/station_walk.py`, `definition_of` and `metric_of` | They write the day a person saved the file. The national file is fetched, and its edition is the day it was retrieved |
| `derive/station_places.py` | A station is its own row, of type `RLY` or `MET`, with the code and the point the publisher gives it, and is no longer gathered from ways in that share a name. `place_id` is made from that code, which settles the draft. `served` is read from the type as before. The ways in stay the rows of `RSE` and `TMU`, and are given to a station by name and by distance, because the file holds no group of stops |
| `tests/derive/stops_support.py` and the tests of both | The made-up file gains rows of another authority, rows of `RLY` and `MET`, and a row with no grid |

**What is still the founder's to say.** Whether the nearest station is measured to its nearest way in, as the name of the measure says, or to the station's own point. A station with no way in recorded is found only by the second. How many there are near London is not known.

## 6. The stations as places

`derive/station_places.py` makes the table. It asks the gate for destination search, which the registry allows for this source.

**A station's name may be shown.** No tracked file here holds the name of a person, of a school or of a business: those are the names the rule is about. A station's name is the name of a place. Its publisher gives it under the Open Government Licence, and it is what a person types. The registry asks two things of how it is shown: the Department for Transport is named as the source, and no roundel, map or typeface of the operator is used. The words "London Underground", "Tube", "DLR" and "London Overground" may be used as labels.

| Part of a row | It is |
|---|---|
| `name` | The name, exactly as the file writes it. It is what is shown |
| `aliases` | What a person may type in its place. Made by rule, matched, and never shown |
| `kind` | `station`, which is core's |
| `served` | A railway station, or a tram, metro or underground station, from the file's type |
| `network` | The Underground, the DLR, a tram or the cable car, from the letters of the code. A hint, or nothing |
| `point`, `centroid` | The middle of its ways in, on the National Grid and as longitude and latitude |
| `codes` | The code of each way in, which leads back to its row of the file |
| `place_id` | Made from the first of its codes. A draft: the national file gives a station a code of its own |

| | |
|---|---|
| Rows | 641 |
| Railway stations | 340 |
| Tram, metro or underground stations | 301 |
| With a network from the letters | 296 |
| That answer to a name another row answers to | 71 |
| The most rows that answer to one name | 3 |

**Why aliases.** The file writes "Station" after 366 names, nothing after 202, "Tram Stop" after 36, "Rail Station" after 19, and "Underground Station", "DLR Station", "Station DLR", "DLR" or "Overground Station" after the rest. A person types the name alone, or the name and "station". Core takes a name without asking only where the words typed are the whole of a name or of an alias. So without aliases most stations are not found by the words a person types. A test holds that, on made-up names and on the real file.

**Two stations may answer to one name.** A railway station and an underground station of one name are two rows. Core then offers both, and takes neither without asking. That is core's rule, and it is right where the two stand apart. Where they stand together a person means either.

**What core and a release need before a place is carried:**

| What | Why | Whose |
|---|---|---|
| A journey's end for each place | A place names the `destination_id` its journeys end at, and core refuses one that is in no `destinations.json` | The build of journeys, which makes the hexagons |
| A release that may hold a journey's end with no journey | Core holds `travel.json` to the same ends as `destinations.json`. So an end with no journey is refused today | Core and the contract |
| A step that writes `places.json` | No step of a build writes a place. The table is made, and is written nowhere a release reads | The pipeline |
| A row of evidence for a place | Every fact a release shows rests on a row. A place has none yet | The pipeline |

Core's search needs no change to read the rows. Given a journey's end that is made up, core finds a station by its name, by its alias, and offers both where two answer.

## 7. What this does not give: a journey time

A place is a name and a point. "35 minutes from a station" needs a journey, and no release holds one. [The design of travel](../../design/london-data-travel.md) says how one is made. What stands in the way, as the registry and the store stood on 2026-09-24:

| What | Registry id | How it stands | What it needs |
|---|---|---|---|
| Timetables of the Underground, the DLR, trams, buses, the river and the cable car | `tfl-journey-planner-timetables` | Approved for routing. Not fetched | **The operator's key.** Register on Transport for London's portal before the first download: the licence applies from the day of registration. Save dated copies of the terms |
| The same, before launch | | | A written answer from the operator on showing times from a stored copy, or a decision record |
| Timetables of railways, the Overground and the Elizabeth line | `network-rail-nwr-schedule` | **Gated.** It lists no internal use, so not even a trial may open a file | **The rail timetable.** Subscribe on the Rail Data Marketplace and save the agreement. A written answer on use from outside the UK. The attribution confirmed |
| The streets | `osm-geofabrik-greater-london` | Approved for routing. In the store, with no receipt | Its receipt. Whether the extract reaches past London's edge is not known |
| Where journeys start | `ons-lsoa-pwc-2021` | Approved | Nothing |
| Where journeys end | `uber-h3` | Approved for cells | The hexagons made. It is a compiled extension |
| Where stations are | `dft-naptan` | Approved for routing | The national file, section 5. The file of stops holds no code of a railway: the guide keeps those in a file of rail references, and in the XML. The national CSV holds the stations and no code of a railway: it has the same 43 columns as the file of London |
| The routing engine | | No step of the pipeline runs one | **R5**, which the plan names, driven from Python. The design gives it Java 21 and about 12 GB of memory |
| Two converters, from each timetable to the form the engine reads | | Not written | A few hundred lines each, for the one day that is modelled |
| A first measure of time and memory | | Not made | 200 origins routed on a hosted runner. Every estimate of the design waits on it |

**What the founder must do**, in the order that unblocks the most:

1. Register on the operator's portal, and save the terms that day.
2. Subscribe to the rail schedule, save the agreement, and ask the two questions the registry entry names.
3. Say whether the rail entry may list `prototyping_only`, so that a trial may open a file.
4. Read the line of the registry entry `dft-naptan` that names the address of the national file of stops. It was taken by `fetch` on 2026-09-24.

Without rail, much of south London has no honest journey time. The design says such a release is for testers and not for launch.

## 8. For the founder to decide

| # | Question | What turns on it |
|---|---|---|
| 1 | Does core name `station_walk` a straight line in metres, or gain a second feature for it | Whether any release carries the measure |
| 2 | Is the cable car a station | 30 output areas, with 4,045 homes, have an end of the cable car for their nearest station. Left out, the figure of two areas moves, by 210 metres and by 10 |
| 3 | Is the nearest station measured to its nearest way in, or to the station's own point | The national file is taken, by `fetch`. It holds both. The 97 areas at the edge, and the code of each station, wait on the measure reading it: section 5 |
| 4 | Are a railway station and an underground station of one name one place | 71 rows answer to a name that another answers to |
| 5 | May a preview hold a place with no journey | Whether a station can be named before journeys are built |
| 6 | Is the nearest stop of a bus shown | It ranks nothing. It could be shown as a fact on an area's page |

## 9. How it was checked

| What | How |
|---|---|
| The reader | 45 tests on made-up files with the publisher's 43 columns. A canary stands in every column that is not read, and a test holds the columns asked for to the six and the seven |
| The measure | 33 tests on a made-up town, each distance worked out by hand |
| The places | 35 tests, of which 9 hand the rows to core's own search |
| The real file | 24 tests hold the counts on this page. They are skipped where the store is not |
| A second source | Every railway station that OS Open Names holds in Greater London, 576 of them, has a way in of the file within 250 metres. So no station that source knows of is missing from the file. 39 stations of the file have none of that source within 300 metres, 35 of the second kind and 4 railway stations: most are tram stops, which that source does not hold. No output area whose distance is known has a station of that source outside London nearer than the way in that was found, and 124 of the 994 whose distance is not known have one. It was read for destination search, which the registry allows it for, and nothing was made from it but these counts |
| The figure, worked out a second time | By code that shares nothing with the measure: every pair of a centre and a way in measured, the land outside joined into one shape, the median taken on whole numbers of homes. All 1,002 areas came to the same figure and the same state, and all 26,369 output areas to the same distance |
| A build | `preview` was run on the real files of three lists, under an id of its own, into a folder git ignores. The measure was worked out and left out by the name of its rule. `check` found nothing, and `burro-release check` passed the release |
| The gate | Asked for each use. It allows scoring, destination search, routing and display for this source, and refuses every other |

Not checked: any figure by a person. Any distance against a map. Whether a way in is where the file says. Any row of the national file beyond its type, its status, its grid and its code.

## 10. Pages read

Each was read on 2026-09-24 through a reader that extracts the text of a page. An extraction is not the page.

| Page | What was taken from it |
|---|---|
| `https://beta-naptan.dft.gov.uk/download` | That a national file and a file by authority are offered |
| `https://beta-naptan.dft.gov.uk/download/national` | The formats, the sizes, and that the page writes no address of a file |
| `https://www.data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/naptan` | The address of the national file, and the publisher of the record |
| `https://www.gov.uk/government/publications/national-public-transport-access-node-schema` | Where the guides are |
| `https://naptan.dft.gov.uk/naptan/schema/2.5/doc/NaPTANSchemaGuide-2.5-v0.67.pdf` | The types of stop, who issues each, and how the stops of one station are named. Its text was taken out of the file by a program, which loses the layout of a table |
| `https://tfl.gov.uk/corporate/about-tfl/what-we-do` | The count of stations of the Underground, and of stops of buses |
| `https://tfl.gov.uk/modes/dlr/`, `/modes/trams/`, `/modes/london-overground/`, `/modes/elizabeth-line/` | That none states a count of stations |

## Credit

Contains public sector information licensed under the Open Government Licence v3.0. Source of the stops: Department for Transport. Source of the centres, the lookup, the outlines and the homes: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right 2026.
