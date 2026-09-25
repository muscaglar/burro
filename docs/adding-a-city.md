# Adding a city: what London taught, and what it would take

For the founder, and for whoever builds the next city. Written 2026-09-25, from the code and the registry as they stood that day. It is written for a city of England outside London, and names none.

**Nothing here is built. The pipeline does not take a city.** This page says where London is written into the code and not given to it, so that the work of giving it can be planned. Sections 0 to 7 are the page to read. Sections 8 and 9 are the lists to work from, and are looked up and not read through.

Every count was made by a program that read the code, and by no person. Each place section 8 names was then held to its file, and a test holds the page to the files from now on. A line number is as the file stood on 2026-09-25.

## 0. In short

| Question | Answer |
|---|---|
| What does not care which city it serves | The arithmetic of core, the API's own code, and the maps of the website, the app and the desk |
| What stands in the way first | Core admits two cities, `syn` and `lon`, in the pattern of every id. The contract carries the pattern, and four other parts write it again by hand |
| Where the pipeline writes London into its code | 250 places, of ten kinds |
| How far the 43 sources that hold a receipt reach | 7 London alone, 7 England, 13 England and Wales, 7 Great Britain, 4 the United Kingdom, 1 the world. Of 4 the repository does not say |
| What a second city has on day one | 90 of London's 100 measures, and 9 of its 14 vibes |

## 1. What already does not care which city it serves

Section 8 gives the path and the line of each place named here.

| Part | What of it names London | What of it is blind to the city |
|---|---|---|
| Core | The pattern of every id, which admits `syn` and `lon` (`ids.py:17` to `:21`). The labels of two measures and the meaning of Well connected, which name the Underground and the Overground (`catalogue.py:1199`). A rate of the estimate of a journey (`estimate.py:37`). Two phrases the reader hears (`lexicon.py:951`) | Ranking, percentiles and bands. Every comparison says "in this release", and a test holds every sentence to naming no city |
| The API | Nothing of its own. It serves core's words, so an offer and the prompt to a model name the Underground whatever release is loaded | It holds no city code. It loads one release, so it serves one city |
| The website | The address of an area's page, which knows `lon` alone (`lib/city.ts:9`). Two sentences of the page of methods | Its copy says "Burro covers one city". Its map is framed on the release's outlines |
| The app | The city of a shared address (`SiteAddress.swift:47`), and the name of the bundle | Its copy names no city |
| The desk and its panel | To the desk, what is not made up is London: its banner, the prefix of an item, and eight refusals and printed lines | The queues, the records, the screens of the panel and the file of changes |
| The workflows and tools | The workflow `data-london`. The tool that holds an image to its lock admits `lon-` alone (`tools/release_lock.py:81`) | The five other workflows, and the checks of them |
| Deployment | No value names London. Both hosts stand in London | The image carries whatever release its lock names |

## 2. What does: where the pipeline writes London into its code

All under `packages/pipeline/src/burro_pipeline/`. A place is one definition, with its uses folded into it.

| Kind | Places | The heart of it | What giving it to a build would take |
|---|---|---|---|
| 1. The prefix and the codes of its authorities | 7 | `LONDON = "E09"`, in `cells/spine.py:38` and again in `cells/postcodes.py:118`. The codes `LBO` and `LBW` of Boundary-Line | A build is given the codes of the city's local authorities. Outside London no prefix tells a city's districts from their neighbours' |
| 2. Its boroughs and wards | 28 | Borough is the pipeline's word for a local authority: a column, a layer, a rule of a border | Little for a city of several districts: the columns are national. For a city that is one district, every rule of a border between two is looked at again |
| 3. Its extent | 8 | No box is written in code. Two lists hold the box and the file of the places, and the grid squares of the parks | A list of the city's own |
| 4. Its centre | 0 | None is written. The middle is worked out from the homes | Nothing |
| 5. The prefix of a release's id, and the code of the city | 19 | `lon-n` begins the id of every area (`cells/spine.py:122`). `city=City.LON` is in every manifest (`assemble/release.py:428`). Five patterns admit `lon-` alone | The city is an argument of five steps. Core gains the code, which is a change to the contract and to both clients |
| 6. The names of its lists | 6 | The thirteen lists are named for milestones, as `m1`, and each mixes national files with London's | A list of the national files, and a list of each city's own. The workflows name the lists |
| 7. Sources that are London's alone, named in code | 11 | Four are read by a measure, and one by what a home lets for | A measure says which source it reads for which city, or is left out |
| 8. Files and addresses that are London's | 59 | The two police forces, the authority `490` of the stops, the 33 files of the food register | Each is given with the city |
| 9. Words a person is shown | 74 | "A release of London". "Near the edge of London", beside every figure of places | A sentence takes the name of the city from the build |
| 10. What else is fitted to London | 38 | The kinds of station, told by letters seen in London's file (`derive/connected.py:146`). One tidal river with two banks. A draft of 400 to 500 areas. Five tables of kinds of place | Each is a decision, and not an argument |

## 3. The sources

Section 9 has a row for each of the 43. What a second city acts on is here.

| The publisher reaches | Sources | What a second city does |
|---|---|---|
| England, England and Wales, Great Britain, the United Kingdom | 31 | Takes the same file: 29 are held whole. Four registry entries name London in a condition, and are changed |
| The world | 1: the file of places | Takes the one file of 16 that holds the city, and the city's box. The file that is held runs from 1.59 degrees west |
| Not said in the registry | 4: the food register, the police's files, the NHS reports and the school inspections | Finds out. Each list says "national", and names no nation |
| London alone | 7 | Needs a substitute, below |

Four files that are held were cut for London, each in a list: the food register by authority, the parks by grid square, the places by file and box, and the police's files by force.

| London's source | Read by | In its place, from the registry |
|---|---|---|
| `gla-town-centre-boundaries` | Three measures, and the draft of names | `os-functional-areas`, which is held, and taken to be paid |
| `gla-high-street-boundaries` | One measure | The same |
| `tfl-step-free-station-topology` | Two measures of how near a station is | Not known: to be found |
| `tfl-bus-stops-and-routes` | One measure | The stops: `dft-naptan`. The routes: not known: to be found |
| `tfl-journey-planner-timetables` | No module yet | None that is approved. `traveline-tnds` is held, and `network-rail-nwr-schedule` is gated |
| `tfl-ptal-2015` | No module | Not known: to be found |
| `ons-private-rental-market-london-postcode-district` | What a home lets for | By local authority, `ons-price-index-of-private-rents`. By postcode district, not known: to be found |

Eight of the 43 are read by no module, two of London's seven among them. So a second city loses less than the list suggests.

## 4. The measures and the vibes of day one

Day one is the first build of the city, once the pipeline takes one. A measure is on it where every source behind it is registered, approved and reaches the city.

| | Measures | Which |
|---|---|---|
| On day one | 90 | The 57 of the file of places, and the 21 of council tax, land use, parks, the census and median prices. Air, noise, main roads, water, conservation cover, listed buildings, private outdoor space, primary schools, a GP practice, a pharmacy, the nearest station and the stops of buses |
| On day one, if the publisher gives the city's own files | 4 | Places to eat and drink, twice, from the food register. Recorded criminal damage and anti-social behaviour, from the police's files |
| Waits | 4 | `highstreet_access` waits on town centres, `highstreet_conserved` on high streets, and `bus_routes_nearby` on the routes of buses. `rail_proximity` waits on a change to its step alone: the national file holds every railway station |
| Cannot be had as it is named | 2 | `underground_proximity` and `overground_proximity`. Each is named for London's own modes, and an id is never renamed. A measure of the city's own modes is a new measure |

| Vibe | Of its recipe held on day one | Places an area |
|---|---|---|
| Leafy, Quiet streets, Age of buildings, Houses or flats, Family amenities, Family area | 100 in 100 | Yes |
| Young professionals, Everyday on foot, Parks close by | 80, 75 and 70 | Yes |
| Going out, Food and drink | 50 and 40, and 80 with the food register | Only with the food register |
| Gritty | 55, and 100 with the police's files | Only with the police's files |
| Village feel | 55 | No. The high street in a conservation area is 45 in 100 of it, and waits on the outlines of high streets. London serves it as a rough guide |
| Well connected | 0 | No. Its recipe is the Underground, the Overground, National Rail and the routes of buses |

A band needs 60 in 100 of its recipe. What a home lets for is held for London, from a workbook that is of London alone, and none would be for another city until its own is found. A journey is estimated from distance, as in London.

## 5. What London taught

| # | The lesson | Where it was learned |
|---|---|---|
| 1 | Show a count of places within reach, and rank on the places for each 1,000 homes: the count says mostly that a place is built up | `docs/research/data/cafes-gyms-and-pubs.md`, section 2 |
| 2 | List every source whose publisher is the city's own before you build: each is replaced, or its measure goes with it | `docs/research/data/stations.md`, section 5 |
| 3 | Prefer a file a fetch can take to a form a person fills in: a file saved by hand reaches the store from a person's machine alone | `docs/research/data/by-hand-files.md` |
| 4 | Draft the names from publishers' files, let a name stand by rule only where one official publisher writes it, and keep a person's hours for the rest | ADR 0022 and ADR 0025 |
| 5 | Treat every number of the estimate of a journey as London's. **None was fitted to a journey that was timed.** One was widened once the estimate had been held against London's timetables, so that less is promised. Its one faster rate is for an area near the Underground or the DLR | `packages/core/src/burro_core/estimate.py:26`. ADR 0027 |
| 6 | Do not promise a village from conservation areas, old homes and the outlines of high streets: three tries put 8, 24 and 25 villages among fifty, where the bar is 30. London serves the vibe as a rough guide, which says so wherever it is shown and is never taken without a press of its own | `docs/research/data/high-streets.md`. ADR 0013, as amended |
| 7 | Never set a band of one city beside another's: a fifth of any city is in the top band | `docs/design/contract.md`, section 2.4 |
| 8 | Read every file of points for a box wider than the city, and leave a home at the edge out where a file stops there | `docs/research/data/food-register.md`, section 9 |
| 9 | Hold a register that each council keeps against a second source before you rank on one of its kinds | `docs/research/data/food-register.md`, section 6 |
| 10 | Give no figure to the areas of an authority that sent no record, and never nought | `docs/research/data/heritage.md`, section 3 |
| 11 | Hold every file's codes to the census lookup, and work out what a dash means from the file's own rows | `docs/research/data/m1-files.md`, sections 2 and 9 |
| 12 | Hold every measure against homes per hectare on the real city: three of London's first four were close to one | `docs/research/data/m2-second-build.md`, section 6 |
| 13 | Look at how many areas read nought before a measure is served in five bands | `docs/research/data/land-use.md`, section 5 |
| 14 | Measure the memory of the service on the first build: London took 381 MB of a machine of 512 | `deploy/README.md`, "What has not been checked" |
| 15 | Have somebody try to refute every claim the plan rests on: of London's 72, 19 were partly wrong and 1 was refuted | `docs/PLAN.md`, under its first tables |

One thing the research said before London was built did not hold: that a city of England and Wales would reuse the pipeline as it is, because every source was national (`docs/research/reports/boundaries.md`). Seven of the 43 are not.

## 6. An order of work for the first city after London

| # | Step | What proves it is done |
|---|---|---|
| 1 | Decide how two cities are served: one service for each, or one that holds two releases | A decision record, approved |
| 2 | Give core the code of the city, and generate the contract, the website's types and the app's models again | `make ci`, `make web-check` and the app's check pass. A made-up release under the new code is accepted by `burro-release check` |
| 3 | Make the pipeline take a city: its code, and the codes of its local authorities | **London, built with the city given, is the release it was.** `moved` finds nothing between the two |
| 4 | Give each city its lists, with a national file listed once. Write the city's own items: its authorities, its squares, its box, its force | `plan` reads every list ready. A person has read each address on its publisher's page |
| 5 | Read the page of each of the four sources whose reach the registry does not say, and say it in the entry | `make registry-check` passes, and section 9 has no row that reads "not said" |
| 6 | Fetch, by a hosted run, and save by hand what is saved by hand | The check of what the store holds is green. The receipts are committed |
| 7 | Build the first preview on the census areas, under the publisher's labels, with no name | `burro-release check` accepts it. Its coverage report has been read |
| 8 | Hold each measure and each vibe of the preview against homes per hectare and the distance from the middle | A page under `docs/research/data/`, with what was found |
| 9 | Write the measures of how near stops are for the city's own modes, and a recipe of Well connected from them | Core's tests pass. The made-up city still holds every two vibes apart |
| 10 | Take the name of the city from the build in every sentence of kind 9 | A test reads every sentence a build of the new city writes, and finds London in none |
| 11 | Draft the names, and read them at the desk: names first, and then borders | The counts ADR 0022 gives for London, for the new city |
| 12 | Give the city its desk, its workflow, its environment and its keys, and the clients its address | The desk's tests and the check of the workflows pass. A rehearsal with made-up secrets is green |
| 13 | See what moved, approve and deploy, as for London | [Refreshing London](refreshing-london.md), steps 6 to 8 |

## 7. What could not be found out

| Not known | What would settle it |
|---|---|
| Whether the food register, the police's files, the NHS reports and the school inspections reach a city outside London | A person reads each publisher's page |
| What stands in for the town centres, the accessibility levels, the routes of buses and which trains call at a station | A search for each, and an entry in the registry |
| Whether a timetable of another city can be had. Every entry of a national timetable is held or gated | The terms of each, read and saved |
| Which numbers of the draft of names are London's. Two say so in their comments, and of the rest the code does not say | Each tried on the first draft of the new city |
| Whether the five tables of kinds of place, and the table of chains, hold for another city. Each was read in London's part of one release of the file | The first build of the new city: a category a table has not met stops it |
| How long any of it takes. Nothing of it was tried | The first three steps of section 6 |

## 8. The places, one by one

Under `packages/pipeline/src/burro_pipeline/`, but for the last table. The words in the second column are in the file named, as they are written there, within three lines of the line named. A row is one place, unless it says how many it stands for.

### Kind 1: the prefix and the codes of its authorities

7 places.

| Where | What is written | What it does |
|---|---|---|
| `cells/spine.py:38` | `LONDON = "E09"` | The lookup keeps the rows whose authority begins so. Every reader of the spine inherits it |
| `cells/postcodes.py:118` | `LONDON = "E09"` | A second copy, for the postcode directory |
| `cells/postcodes.py:194` | `OF_LONDON = re.compile(r"E09[0-9]{6}")` | A row that is kept and is of another authority stops the build |
| `derive/school_primary_nearby.py:177` | `LONDON = "London"` | The name of the region in the register of schools. It counts, and moves no figure |
| `areas/assign_files.py:75` | `A_BOROUGH, A_WARD = "LBO", "LBW"` | The codes Boundary-Line gives a London borough and its ward. No other row is read |
| `areas/context_read.py:50` | `WARD_OF_LONDON, BOROUGH_OF_LONDON = "LBW", "LBO"` | The same |
| `areas/names_wards.py:29` | `WARD_OF_LONDON, BOROUGH_OF_LONDON = "LBW", "LBO"` | The same |

### Kind 2: its boroughs and wards

28 places.

| Where | What is written | What it does |
|---|---|---|
| `cells/spine.py:41` | `BOROUGH, BOROUGH_NAME = "LAD22CD", "LAD22NM"` | National columns, under London's word. Used on 19 lines |
| `cells/spine.py:48` | `(?P<borough>.+) (?P<number>[0-9]{3})` | The label of an area is its authority and a number |
| `cells/spine.py:176` | `"boroughs"` | A count that is printed |
| `cells/postcodes.py:344` | `in_another_borough` | Two counts |
| `areas/names_wards.py:31` | `WARD_ENDS, BOROUGH_ENDS = " Ward", " London Boro"` | What is cut from a name of Boundary-Line |
| `areas/names_candidates.py:61` | `ENDINGS` | The endings of each file of names |
| `areas/assign_files.py:77` | `WARD_ENDS = " Ward"` | What is cut from the name of a ward |
| `areas/assign_files.py:73` | `BOROUGHS_AND_WARDS` | The two layers of Boundary-Line that are read |
| `areas/context_read.py:47` | `WARDS, BOROUGHS` | The same two layers |
| `areas/names_wards.py:26` | `WARDS, BOROUGHS` | The same two layers |
| `areas/names_candidates.py:70` | `WARD, BOROUGH = "ward", "borough"` | The kind of a name that was put forward |
| `areas/assign.py:48` | `WARD, ROADS, MSOA, CENTRE` | The kinds of evidence of a border |
| `areas/assign.py:84` | `across_a_borough: float = 0.10` | What is put on a distance to a seed in another borough |
| `areas/assign.py:235` | `areas_in_two_boroughs` | A count |
| `areas/assign_files.py:505` | `"boroughs"` | Five counts, to line 522 |
| `areas/flags.py:84` | `TWO_BOROUGHS = "two_boroughs"` | A flag of an area |
| `areas/flags.py:125` | `cells_outside: int = 1` | With `doubt_across_a_borough`, line 129: the rule of an area across a borough line |
| `areas/names_look.py:77` | `ALSO_A_BOROUGH = "also_a_borough"` | With `ALSO_A_WARD`, line 79: two marks of a name |
| `areas/draft_files.py:146` | `BOROUGHS, TIE = "boroughs", "borough_is_a_tie"` | Two columns of the draft |
| `areas/assign_write.py:143` | `"primary_borough"` | A column of the draft's tables, written in six modules |
| `areas/assign_write.py:218` | `"borough"` | A column that is written, in seven modules |
| `areas/assign_write.py:219` | `"ward"` | With `"ward_share"`, line 220: two columns that are written |
| `areas/context.py:93` | `Layer("boroughs"` | With `Layer("wards"`, line 94: two layers of the desk |
| `areas/context_files.py:409` | `boroughs.csv` | A file of the draft, with `boroughs.geojson` and a picture for each borough in `areas/draft_run.py` |
| `areas/draft_rules.py:138` | `a_ward_of_its_name` | With `a_few_cells_across_a_borough_line`, line 251: two rules that are put to the founder |
| `derive/venue_food_drink.py:432` | `def boroughs_of` | Each file of the register is of the borough most of its businesses lie in |
| `derive/venue_food_drink.py:459` | `def held_to_london` | The build stops unless the register holds one file for each borough |
| `derive/rent.py:118` | `BOROUGH, DISTRICT, KIND` | The columns of the workbook of rents. It names a borough and gives no code, and the build stops unless it names every borough, line 547 |

### Kind 3: its extent

8 places.

| Where | What is written | What it does |
|---|---|---|
| `fetch/lists/m2-culture.toml:61` | `box = [-0.53, 51.28, 0.33, 51.71]` | The one box of the pipeline: the places are taken inside it |
| `fetch/lists/m2-culture.toml:85` | `box = [-0.53, 51.28, 0.33, 51.71]` | The same, for the brands |
| `fetch/lists/m2-culture.toml:52` | `part-00007` | The one file of 16 that holds the box |
| `fetch/lists/m2-culture.toml:76` | `part-00007` | The same |
| `fetch/lists/m2-places.toml:190` | `area=TQ` | The grid square that holds nearly all of London |
| `fetch/lists/m2-places.toml:207` | `area=TL` | The square north of it |
| `derive/culture_reach.py:92` | `ACROSS, UP = 0.004, 0.0025` | The size of a bucket, in degrees, as wide as it is at London. It changes how fast a figure is found, and no figure |
| `cells/shapes.py:337` | `111_320` | Metres in a degree, good at London's latitude, for a check |

### Kind 4: its centre

No place. No point is written as the middle of the city: where a sentence speaks of the middle, it is worked out from the homes of the build.

### Kind 5: the prefix of a release's id, and the code of the city

19 places.

| Where | What is written | What it does |
|---|---|---|
| `cells/spine.py:122` | `lon-n{msoa.lower()}` | The id of every area |
| `areas/names_evidence.py:58` | `ID = "lon-n{:04d}"` | The id of a drafted place |
| `areas/names_evidence.py:59` | `NUMBER = re.compile(r"lon-n` | The pattern of that id |
| `areas/draft_run.py:493` | `removeprefix("lon-n")` | The label of an area in a picture |
| `derive/station_places.py:90` | `CITY = "lon"` | The id of every place to reach |
| `assemble/release.py:428` | `city=City.LON` | The manifest of every build |
| `assemble/cli.py:121` | `RELEASE_ID_PATTERN.replace("(syn\|lon)", "lon")` | The id `preview` takes |
| `cells/cli.py:44` | `RELEASE_ID = re.compile(r"lon-` | The id `cells` takes |
| `kept/lock.py:41` | `RELEASE_PATTERN = r"^lon-` | The id a lock may name |
| `kept/lock.py:46` | `NAME_PATTERN = r"^lon-` | The name of a file in a lock |
| `evidence/claim.py:36` | `CLAIM_ID_PATTERN = r"^(syn\|lon)-c` | The id of a claim |
| `evidence/row.py:42` | `ROW_ID_PATTERN = rf"^(syn\|lon)-n` | The id of a row of evidence |
| `areas/draft_run.py:133` | `LONDON = "london"` | The name of the picture of the whole draft |
| `assemble/cli.py:336` | `gazetteer/london` | An example |
| `assemble/cli.py:327` | `lon-2026-10-02-01` | An example, on seven lines |
| `cells/cli.py:98` | `lon-2026-10-02-01` | An example, on two lines |
| `evidence/cli.py:114` | `lon-2026-10-02-01` | An example, on six lines |
| `kept/cli.py:106` | `lon-2026-10-02-01` | An example, on five lines |
| `upkeep/cli.py:137` | `lon-2026-09-25-01` | An example, on two lines |

### Kind 6: the names of its lists

6 places.

| Where | What is written | What it does |
|---|---|---|
| `assemble/cli.py:189` | `FIRST_LIST = "m1"` | The list a build takes where none is named |
| `fetch/sources.py:49` | `LISTS = Path(__file__).parent / "lists"` | One folder for every list, with no city in it |
| `assemble/cli.py:329` | `--list m1` | Examples, on five lines |
| `evidence/cli.py:115` | `--list m1` | Examples, on three lines |
| `fetch/cli.py:130` | `--list m1` | Examples, on four lines |
| `fetch/lists/m1.toml:56` | `build = "m1"` | The name of each of the thirteen lists, in its own file |

### Kind 7: sources that are London's alone, named in code

11 places.

| Where | What is written | What it does |
|---|---|---|
| `derive/bus_routes.py:88` | `SOURCE = "tfl-bus-stops-and-routes"` | The routes of buses near a home |
| `derive/tfl_stations.py:50` | `SOURCE = "tfl-step-free-station-topology"` | Which modes call at a station |
| `derive/town_centres.py:80` | `SOURCE = "gla-town-centre-boundaries"` | Three measures of a town centre |
| `derive/high_streets.py:67` | `SOURCE = "gla-high-street-boundaries"` | Read by one measure of a build: how much of the nearest high street lies in a conservation area |
| `areas/names_centres.py:30` | `SOURCE = "gla-town-centre-boundaries"` | A second publisher of a name, used on 27 lines |
| `areas/context.py:63` | `TOWN_CENTRES = "gla-town-centre-boundaries"` | A layer of the desk |
| `registry/model.py:21` | `TFL_OPEN_DATA = "TfL-Open-Data"` | A licence of the registry |
| `fetch/lists/m12-public-transport.toml:55` | `source_id = "tfl-ptal-2015"` | In a list alone |
| `fetch/lists/m5-journeys.toml:63` | `source_id = "tfl-journey-planner-timetables"` | In a list alone |
| `fetch/lists/m2-living.toml:165` | `source_id = "osm-geofabrik-greater-london"` | In a list alone |
| `derive/rent.py:100` | `SOURCE = "ons-private-rental-market-london-postcode-district"` | What a home lets for |

### Kind 8: files and addresses that are London's

59 places.

| Where | What is written | What it does |
|---|---|---|
| `derive/stops_file.py:78` | `AUTHORITY, FILE_ENDS = "490", "Stops.csv"` | London's file of stops, which two measures and the places to reach still read |
| `derive/street_crime_files.py:60` | `FORCES = ("city-of-london", "metropolitan")` | A file of another force is refused |
| `derive/street_crime_files.py:55` | `EDITION = "August 2023 to July 2026"` | The edition of London's file |
| `derive/tfl_stations.py:54` | `FILE = "tfl-stationdata-detailed.zip"` | The name of the file |
| `derive/tfl_stations.py:56` | `ModesAndLines.csv` | Its four tables and their columns, to line 59 |
| `derive/town_centres.py:84` | `FILE = "Town_Centres_Boundaries.gpkg"` | The name of the file, its layer and its columns |
| `derive/high_streets.py:71` | `FILE = "GLA_High_Street_boundaries_2.gpkg"` | The same |
| `derive/bus_routes.py:92` | `Data_3rdParties_bus-sequences` | The name of the file |
| `derive/bus_routes.py:93` | `Stop_Code_LBSL` | Its columns, to line 99 |
| `derive/rent.py:107` | `FILE_STARTS = "londonrentalstats"` | The name of the workbook of rents. The title of its cover and what its contents say of each table name London too, to line 128 |
| `areas/names_centres.py:31` | `LAYER = "town_centres"` | The layer and the columns of the town centres |
| `areas/context_read.py:52` | `CENTRES = "town_centres"` | The same |
| `fetch/lists/m2-living.toml:123` | `item = "naptan-london"` | London's stops, saved by hand |
| `fetch/lists/m2-living.toml:164` | `item = "osm-greater-london"` | The streets, for routing |
| `fetch/lists/m2-living.toml:193` | `item = "rents-london-districts"` | London's rents |
| `fetch/lists/m2-living.toml:372` | `item = "police-crime-london"` | Two forces, saved by hand |
| `fetch/lists/m2-places.toml:118` | `item = "gla-town-centres"` | The town centres |
| `fetch/lists/m11-high-streets.toml:45` | `item = "gla-high-streets"` | The high streets |
| `fetch/lists/m12-public-transport.toml:54` | `item = "ptal-grid-2015"` | The accessibility levels |
| `fetch/lists/m12-public-transport.toml:68` | `item = "bus-sequences"` | The routes of buses |
| `fetch/lists/m12-public-transport.toml:82` | `item = "bus-stops"` | The stops of buses |
| `fetch/lists/m2-stations.toml:37` | `item = "tfl-station-data"` | The station data |
| `fetch/lists/m5-journeys.toml:62` | `item = "tfl-timetables"` | The timetables |
| `fetch/lists/m2-culture.toml:46` | `item = "overture-places-london"` | The places, in London's box |
| `fetch/lists/m2-culture.toml:70` | `item = "overture-places-london-brands"` | The same, with the brands |
| `fetch/lists/m2-places.toml:723` | `borough and ward boundaries` | A national file, under London's words |
| `fetch/lists/m2-places.toml:237` | `item = "fsa-barking-and-dagenham"` | The first of the 33 files of the food register. An item follows every 13 lines, to line 653 |

### Kind 9: words a person is shown

74 places.

| Where | What is written | What it does |
|---|---|---|
| `cells/cli.py:56` | `London's output areas` | The summary of a step |
| `cells/cli.py:61` | `London is the rows` | The help of a step |
| `cells/cli.py:88` | `its id, label, borough` | The same |
| `cells/cli.py:188` | `release of London` | A refusal |
| `cells/spine.py:52` | `which is the name of its` | The sentence of a method: "its borough and a number" |
| `cells/spine.py:219` | `a label is not a borough and a number` | An error |
| `cells/spine.py:249` | `it holds no row of London` | An error |
| `cells/postcodes.py:282` | `Lookup(london=` | What a lookup says of itself |
| `cells/postcodes.py:492` | `a row of London has no point` | An error |
| `cli.py:82` | `the engine that routes London` | The help of the command line |
| `assemble/cli.py:211` | `a borough and a number` | The help of a step, on three lines |
| `assemble/cli.py:223` | `stations of London` | The same, on two lines |
| `assemble/cli.py:242` | `the rents of London` | The same |
| `assemble/cli.py:1166` | `release of London` | A refusal |
| `assemble/cli.py:1378` | `London's stops` | A note of a build |
| `assemble/cli.py:1551` | `London's named areas` | The help of an argument |
| `assemble/names.py:109` | `another area of its borough` | The sentence of a method |
| `release/read.py:67` | `a borough or a place of the release` | What a rule means |
| `kept/cli.py:118` | `release of London` | The help of a step, on four lines |
| `kept/cli.py:206` | `release of London` | A refusal |
| `kept/cli.py:297` | `releases of London` | A refusal |
| `travel/cli.py:69` | `london-data-travel.md` | The help of a step |
| `evidence/coverage.py:412` | `Boroughs with a gap` | Three headings of the coverage report |
| `areas/cli.py:27` | `London's areas` | The summary of a step |
| `areas/names_cli.py:43` | `London's areas` | The summary of a step |
| `areas/names_cli.py:58` | `town centres` | The help of a step |
| `areas/draft_run.py:142` | `A draft of the areas of London` | What a draft says of itself, on four lines |
| `areas/draft_run.py:468` | `A draft of London's areas` | The title of a picture |
| `areas/draft_run.py:482` | `a draft, made by method` | The title of the picture of a borough |
| `areas/assign_files.py:458` | `no seed lies in an output area of London` | An error |
| `areas/assign_files.py:507` | `seeds_in_london` | A count, with `seeds_outside_london` and `outside_london` in two more modules |
| `areas/assign.py:256` | `a bank is north, south or not drawn` | An error |
| `areas/context.py:137` | `The tidal river needs no layer` | A note for the desk |
| `areas/context.py:147` | `London's file by hand` | A note for the desk |
| `areas/context.py:394` | `two boroughs would share a group` | An error |
| `areas/flags_build.py:47` | `No ward was read` | Three notes of a draft |
| `areas/flags_ground.py:121` | `an outline and a borough` | An error |
| `areas/flags.py:140` | `a borough line, a ward line or a main road` | The line of a rule |
| `areas/flags.py:146` | `main borough.` | The line of a rule |
| `areas/flags.py:151` | `town centres of district class or above` | The line of a rule |
| `areas/flags.py:153` | `both banks of the tidal water` | The line of a rule, and the words the desk shows of it |
| `areas/flags.py:166` | `it lies in two boroughs` | The words the desk shows, with those of two town centres |
| `areas/flags.py:519` | `runs along a borough line` | Why an area is flagged, in four sentences |
| `areas/flags_files.py:417` | `on both banks first` | The order the desk is told |
| `areas/draft_lines.py:162` | `lies outside the main borough` | A reason |
| `areas/draft_lines.py:306` | `Its own town centre` | Four lines the desk shows of a name |
| `areas/draft_rules.py:162` | `Greater London Authority` | A rule that is put to the founder |
| `areas/draft_rules.py:257` | `council tax` | Three more rules that are put to the founder |
| `areas/names_look.py:310` | `The town centre "` | Six marks of a name |
| `areas/names_look.py:475` | `the same borough` | Five more marks of a name |
| `derive/brands_nearby.py:226` | `Near the edge of London` | Beside every figure of a chain |
| `derive/bus_routes.py:89` | `PUBLISHER = "Transport for London"` | The publisher and the product, as they are cited |
| `derive/bus_routes.py:142` | `3 October 2025` | What the measure cannot see, of the day of the file and of London's edge |
| `derive/centre_compact.py:96` | `homes beyond London` | A definition, and what the measure cannot see |
| `derive/centre_small.py:89` | `homes beyond London` | The same |
| `derive/connected.py:185` | `past the edge of London` | Two definitions |
| `derive/connected.py:203` | `Transport for London` | What a measure cannot see |
| `derive/connected.py:252` | `Underground or DLR` | The label and the definition of a measure |
| `derive/connected.py:270` | `Overground or Elizabeth line` | The same, of two measures |
| `derive/culture_reach.py:108` | `outside London` | The end of every sentence of what is within reach |
| `derive/culture_venues.py:221` | `Near the edge of London` | Beside every figure of places, of four kinds |
| `derive/gp_walk.py:140` | `outside London` | A definition. So `derive/pharmacy_walk.py`, line 150 |
| `derive/grocery_walk.py:136` | `box round London` | Beside the nearest food shop |
| `derive/high_streets.py:68` | `Greater London Authority` | The publisher, as it is cited. So `derive/town_centres.py` and `derive/tfl_stations.py` |
| `derive/highstreet_access.py:87` | `homes beyond London` | A definition, and what the measure cannot see |
| `derive/highstreet_conserved.py:123` | `tidal river is no land` | The same |
| `derive/household_income.py:215` | `another borough than the lookup gives` | An error, in three modules |
| `derive/incident_criminal_damage.py:335` | `no record of London` | An error. So `derive/land_use.py` and `derive/noise.py` |
| `derive/nearest_by_postcode.py:97` | `outside London` | The sentence of a method, and two lines beside a figure |
| `derive/park_facilities.py:168` | `inside London or outside it` | A definition, in three modules |
| `derive/price.py:195` | `each borough` | What a renter is told |
| `derive/rent.py:239` | `postcode district or a borough of London` | The definition of what a home lets for |
| `derive/station_walk.py:97` | `Greater London` | A definition, and what the measure cannot see |
| `derive/venue_food_drink.py:242` | `homes outside London` | Beside every figure of the register, and of pubs |

### Kind 10: what else is fitted to London

38 places.

| Where | What is written | What it does |
|---|---|---|
| `derive/connected.py:131` | `UNDERGROUND_PROXIMITY` | Four measures that are named for London's modes |
| `derive/connected.py:146` | `UNDERGROUND_OR_DLR = ("LU", "DL", "BP", "NE")` | The letters of a stop's code, as they were seen in London's file, with `TRAM = ("CR",)` |
| `derive/connected.py:152` | `OVERGROUND_OR_ELIZABETH` | The modes of Transport for London's file |
| `derive/connected.py:161` | `MARGIN = 25_000` | The build stops where a home is further from the nearest stop of a kind |
| `derive/connected.py:156` | `JOINED_WITHIN = 200` | How near a station of one file is to the same station of the other |
| `derive/tfl_stations.py:61` | `tube` | Seven modes. A mode that is not one of them stops the build |
| `derive/stops_file.py:113` | `"LU": "underground"` | The kind of a station, by the letters of its code |
| `derive/station_places.py:81` | `tram_metro_underground` | How a station is served, and the endings of its name on line 84 |
| `derive/bus_routes.py:106` | `STANDS_IN` | How London Buses names a bus that stands in for a train |
| `derive/measures.py:250` | `bus_routes` | The one list of measures, which no city can leave one out of |
| `areas/assign.py:50` | `NORTH, SOUTH, NOT_DRAWN` | One tidal river with two banks, which no area may cross |
| `areas/assign.py:56` | `BOTH_BANKS` | An area on both banks breaks a rule |
| `areas/assign_files.py:204` | `def banks_of` | The two largest pieces east of the water's west end |
| `areas/assign_files.py:95` | `least_water` | The hectares under which no tidal water is taken |
| `areas/assign_shapes.py:168` | `def water_between` | The tidal water, as the boroughs less the land |
| `areas/context_read.py:194` | `def boroughs_to_the_water` | The layer of the water |
| `areas/draft_run.py:138` | `SIDE_BY_SIDE = 400.0` | Fitted to the width of the tidal water |
| `areas/seeds.py:121` | `least: int = 400` | With `most: int = 500`, line 122: how many areas a draft must come to |
| `areas/seeds.py:112` | `place: int = 3` | Eleven numbers of the points of a name, to line 126. The code does not say which are London's |
| `areas/flags.py:109` | `follows_share` | With `margin_share`, line 119: each set from the first draft of London |
| `areas/flags.py:103` | `publishers` | Seven numbers of a flag, to line 123. The code does not say which are London's |
| `areas/assign.py:71` | `nearest: int = 3` | Four numbers of a border. The same |
| `areas/draft_names.py:72` | `overlap: float = 0.05` | Three numbers of a name. The same |
| `areas/draft_rules.py:108` | `ROADS_NEEDED = 50` | With the kinds of a smaller place and the words of a built place, to line 113. The same |
| `areas/names_look.py:127` | `BUILT` | The words of a built place, and `SMALLEST_BOX`, line 188. The same |
| `areas/flags_files.py:85` | `FIRST = (50, 100, 120, 150, 200, 300)` | How many areas a person looks at first |
| `areas/names_centres.py:35` | `DISTRICT_OR_ABOVE` | The classes of a town centre, as London's file names them. So `areas/context_read.py`, line 57 |
| `areas/context_files.py:59` | `ROADS_DRAWN` | Local roads are not drawn, for how many London holds |
| `assemble/release.py:133` | `GRITTY = GrittyVariant.B` | Which way Gritty is built in a release of London |
| `assemble/release.py:136` | `NOT_ROUTED = Cutoffs(pt=90, cycle=60, walk=60)` | The longest journey of a build that routed none. It is the contract's own |
| `derive/incident_criminal_damage.py:102` | `MONTHS = 36` | With two forces, 72 files are expected |
| `derive/centres_nearby.py:155` | `ELSEWHERE` | A table of kinds, read in London's part of the file of places |
| `derive/culture_kinds.py:191` | `ELSEWHERE` | The same |
| `derive/food_shop_kinds.py:127` | `IS_NOT` | The same |
| `derive/worship_kinds.py:237` | `NO_WORSHIP` | The same |
| `derive/venue_kinds.py:157` | `OF_FOOD_AND_DRINK` | The same |
| `derive/brand_tiers.toml:44` | `read_in = "overture-places 2026-09-23.0"` | The table of chains, whose spellings were read in London's part of the file |
| `release/synthetic/names.py:23` | `BOROUGH = "Quillhaven"` | The made-up city is shaped as London is: a river with two banks, an Underground and an Overground |

### Outside the pipeline

What section 1 names, with the whole path of each.

| Where | What is written | Part | What it does |
|---|---|---|---|
| `packages/core/src/burro_core/ids.py:21` | `RELEASE_ID_PATTERN = r"^(syn\|lon)-` | Core | The pattern of the id of a release. Lines 17 to 20 hold the same of an area, a destination, a place and a station |
| `packages/core/src/burro_core/ids.py:316` | `LON = "lon"` | Core | The one city that is not made up |
| `packages/core/src/burro_core/release.py:221` | `city: City` | Core | The city of a manifest |
| `packages/core/src/burro_core/ids.py:159` | `UNDERGROUND_PROXIMITY = "underground_proximity"` | Core | With `OVERGROUND_PROXIMITY`, line 160: the ids of two measures |
| `packages/core/src/burro_core/catalogue.py:1199` | `Underground or DLR` | Core | The label of a measure. So line 1214, of the Overground, and line 1832, the meaning of Well connected |
| `packages/core/src/burro_core/estimate.py:37` | `MINUTES_A_KM_NEAR_THE_UNDERGROUND = 2.5` | Core | With `NEAR_THE_UNDERGROUND_M`, line 39. Both are names of the contract |
| `packages/core/src/burro_core/lexicon.py:951` | `outside london` | Core | What the reader hears. So "near a tube", line 650, and "by tube" in `grammar.py`, line 161 |
| `packages/core/src/burro_core/rank.py:136` | `FIRM_BUDGET_MARGIN_PERCENT = 25` | Core | Reasoned on flats sold in London: the comment above it |
| `apps/web/src/lib/city.ts:9` | `lon: "london"` | Website | The first part of the address of an area's page. Line 21 gives any other city no page |
| `apps/web/src/content/methods.ts:44` | `London's neighbourhoods` | Website | A sentence of the page of methods. So line 149, of the Underground |
| `apps/web/scripts/check-pages.mjs:252` | `synthetic\|london` | Website | How the check of the built pages knows the page of an area |
| `apps/ios/BurroKit/Sources/BurroKit/Shell/SiteAddress.swift:47` | `case "lon"` | App | The city of a shared address |
| `apps/ios/BurroKit/Sources/BurroKit/Features/Area/IncomingLink.swift:44` | `"lon-"` | App | The cities a link that is opened may name |
| `apps/ios/Burro.xcodeproj/project.pbxproj:211` | `london.burro.app` | App | The name of the bundle, on two lines |
| `tools/desk/server.py:66` | `REAL DATA FOR LONDON` | Desk | The banner over real data. So `tools/desk/page/logic.mjs`, line 26 |
| `tools/desk/cli.py:84` | `The made-up city and London are` | Desk | A refusal. So `tools/desk/compile.py`, lines 571 and 862, `tools/desk/publish.py`, line 136, and `tools/desk/fill/__init__.py`, line 102 |
| `tools/desk/cli.py:289` | `real data for London` | Desk | A line that is printed. So `tools/desk/fill/__init__.py`, line 162 |
| `tools/desk/cli.py:327` | `gazetteer/london` | Desk | Where the decisions are published to, in a line of help |
| `tools/desk/fill/draft.py:1265` | `"lon"` | Desk | The prefix of an item of real data |
| `tools/desk/fill/draft.py:330` | `gla-town-centre-boundaries` | Desk | A source of the evidence of a name |
| `tools/desk/panel/numbers.py:83` | `Underground` | Desk | Two numbers of the estimate of a journey, as the panel lists them |
| `.github/workflows/data-london.yml:1` | `name: data-london` | Workflows | The workflow, its environment and its group |
| `.github/workflows/data-london.yml:123` | `--list m1 --list m10-health` | Workflows | The thirteen lists a build takes, on two lines |
| `tools/public_log.py:83` | `"data-london"` | Tools | The one environment that is given the key that writes a release |
| `tools/release_lock.py:81` | `LONDON = re.compile(r"lon-` | Tools | The lock an image is held to. Line 80 admits `syn` and `lon` |
| `Makefile:146` | `gazetteer/london` | Tools | Two lines of help |
| `deploy/api/fly.toml:16` | `primary_region = "lhr"` | Deployment | Where the service stands |
| `deploy/web/vercel.json:6` | `"lhr1"` | Deployment | Where the website stands |

## 9. The sources, one row for each that holds a receipt

"Whole" is the file as the publisher gives it, with London's rows kept as it is read. "A cut" is a file that was chosen for London. A substitute is named only where the registry holds it.

| Source | Reaches | Held | For a city of England outside London |
|---|---|---|---|
| `defra-pcm-background-air` | United Kingdom | Whole | The same file |
| `dfe-gias` | England | Whole, saved by hand | The same file |
| `dft-naptan` | Great Britain | Both: London's cut, saved by hand, and the whole | The whole, which is held |
| `fsa-food-hygiene-ratings` | Not said in the registry | A cut: a file for each of London's 33 authorities | The files of the city's own authorities, if the register holds them |
| `gla-high-street-boundaries` | London alone | Whole | `os-functional-areas`, which is held and taken to be paid |
| `gla-town-centre-boundaries` | London alone | Whole | `os-functional-areas`, as above |
| `historic-england-listed-buildings` | England | Whole | The same file |
| `hmlr-price-paid` | England and Wales | Whole | The same files |
| `hmlr-uk-house-price-index` | United Kingdom | Whole | The same file. Its entry allows London's series alone. No module reads it |
| `mhclg-iod-2025-underlying-indicators` | England | Whole | The same file |
| `mhclg-land-use-statistics-2022` | England | Whole | The same file |
| `mhclg-planning-data-conservation-areas` | England, and its page says it may not yet cover all of it | Whole | The same file, held authority by authority |
| `nhs-ods` | Not said in the registry | Whole | The same reports, if they reach it. No module reads them |
| `nhs-ods-gp-practices` | England and Wales | Whole | The same report |
| `nhsbsa-consolidated-pharmaceutical-list` | England | Whole | The same file |
| `ofsted-state-funded-schools-mi` | Not said in the registry | Whole | The same file, if it reaches it. No module reads it |
| `ons-access-to-garden-space-2020` | Great Britain | Whole | The same file |
| `ons-census-2021-age-and-household-tables` | England and Wales | Whole | The same tables |
| `ons-census-2021-housing-tables` | England and Wales | Whole | The same table |
| `ons-income-estimates-small-areas` | England and Wales | Whole | The same workbook |
| `ons-lsoa-2021` | England and Wales | Whole | The same file |
| `ons-lsoa-pwc-2021` | England and Wales | Whole | The same file. No module reads it |
| `ons-median-house-prices-msoa` | England and Wales | Whole | The same workbook |
| `ons-msoa-2021` | England and Wales | Whole | The same file. No module reads it |
| `ons-msoa11-msoa21-lad22-lookup` | England and Wales | Whole | The same file. Its entry says to read London's rows alone |
| `ons-oa-pwc-2021` | England and Wales | Whole | The same file |
| `ons-oa21-lsoa21-msoa21-lad22-lookup` | England | Whole | The same file |
| `ons-output-areas-2021` | England and Wales | Whole | The same files |
| `ons-postcode-directory` | United Kingdom | Whole, saved by hand | The same file. Its entry says to keep Greater London's rows |
| `ons-price-index-of-private-rents` | United Kingdom | Whole | The same workbook. No module reads it |
| `ons-private-rental-market-london-postcode-district` | London alone | Whole | By local authority, `ons-price-index-of-private-rents`. By postcode district, not known: to be found |
| `os-boundary-line` | Great Britain | Whole | The same file |
| `os-open-greenspace` | Great Britain | A cut: the grid squares TQ and TL | The city's own squares, or the one file of Great Britain |
| `os-open-names` | Great Britain | Whole | The same file |
| `os-open-rivers` | Great Britain | Whole | The same file |
| `os-open-roads` | Great Britain | Whole | The same file |
| `overture-places` | The world | A cut: one file of 16, and a box within it | The file that holds the city, and its box. The file that is held runs from 1.59 degrees west |
| `police-uk-street-level-crime` | Not said in the registry | A cut: two forces, from a form, saved by hand | The file of the city's own force, if the site gives it |
| `tfl-bus-stops-and-routes` | London alone | Whole | The stops: `dft-naptan`. The routes that call at a stop: not known: to be found |
| `tfl-journey-planner-timetables` | London alone | Whole | None that is approved. `traveline-tnds` is held, and `network-rail-nwr-schedule` is gated. The one entry of the Bus Open Data Service, `dft-bods-london-gtfs`, is of London's file. No module reads it |
| `tfl-ptal-2015` | London alone | Whole | Not known: to be found. No module reads it |
| `tfl-step-free-station-topology` | London alone | Whole | Not known: to be found |
| `voa-council-tax-stock-of-properties` | England and Wales | Whole | The same tables |
