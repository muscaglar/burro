# Travel times for all of London

Status: design, 2026-09-23. No dataset was downloaded or opened to write it. Amended 2026-09-24: the step is built for a made-up town, with a router that is for tests, and no engine is installed. Sections 18 to 20 say what is built, how large the table is at the 1,002 areas of today, and what the first run of the engine must settle. Sections 1 to 17 are as they were written, but for the rule of a percentile in section 4. It applies ADR [0002](../adr/0002-deterministic-core.md), [0003](../adr/0003-three-grids.md), [0004](../adr/0004-openstreetmap.md), [0008](../adr/0008-package-sources.md) and [0014](../adr/0014-evidence-first-and-census-figures-shown.md). It changes no code and no registry file. Section 13 lists the changes it asks others to make.

How to read the figures: **measured** was run for this document, on made-up numbers. **Read** was read on a publisher's page on 2026-09-23 (section 17). **Estimate** is worked out by hand, and the row says how. Anything else comes from the registry or from `docs/research/`, as they stood that day.

## 0. What this assumes about the other parts

| Part | Assumed | If it is not so |
|---|---|---|
| Areas | About 450 named areas, each a reviewed list of 2021 Output Areas, with a weight for each Output Area (homes or residents) | Only the roll-up of section 7 waits. Routing starts from LSOA points and does not need the map |
| Places | `places.json` points each place at one hexagon. This part hands over the list of hexagons that can be routed to | A place in a hexagon with no street is moved to the nearest hexagon that has one |
| Evidence | Every input file has a record: source id, address, date retrieved, checksum, the date the data describes. Every derived table names its inputs and its method | Section 10 gives the fields travel needs, to be fitted to whatever shape is chosen |
| Release format | A release may hold a binary file, listed in the manifest with its checksum | Today's JSON works, at a cost in memory (section 8) |
| Stations | `stations.json`, `station_walk` and `station_lines` are built by the features part, from the same timetable copy, so the dates agree | They carry their own dates |
| Vibes, likeness, census | None reads a travel time. `vibes.md` 7.1 already keeps journeys out of likeness | No change here |
| Models | No language model is used anywhere in travel, at build time or after | |

## 1. In short

| Question | Answer |
|---|---|
| What is computed | Door-to-door minutes from 4,994 home points to about 16,700 hexagons, by public transport, by bike and on foot, for one weekday morning |
| Engine | R5, driven from Python through r5py, with a driver of our own that runs origins side by side |
| Where it runs | Hosted CI. The standard runner has 4 processors, 16 GB and Java 21, and is free for a public repository (read). A rented machine is the second choice |
| Size | 83.4 million pairs a matrix. 7 to 26 processor-hours for the whole first version (estimate). About an hour by the clock in 8 shards (estimate) |
| Cost | Nothing on hosted CI. About £3 to £6 a build on a rented machine (estimate) |
| Typical and just missed | The 50th and the 90th percentile of the fastest journey over 120 departure minutes, 07:00 to 08:59 |
| What is served | 450 areas by 16,700 hexagons by 4 matrices: 30.1 MB of bytes held in memory. One search reads it in about a microsecond (measured) |
| How a time is cited | By the record of the build: each input with its source, data date, date retrieved and checksum; the engine and its settings; the day modelled |
| Kept current | Rebuilt each quarter, after the May and December rail timetables, and when a weekly check finds the timetables have moved |
| The first thing to do | Benchmark 200 origins on a hosted runner. Every estimate of time and memory here is unmeasured until then |
| The thing most likely to stop it | The rail licence. The entry is gated and lists no internal use, so today not even a trial may open the file |
| If rail is not cleared | A release with no public transport time wherever a train could be the way to travel. It is for testers, not for launch (section 11) |

## 2. Inputs, and the gate on each

`travel.json` asks every source it names for the use `routing` (contract 2.1). Status is as the registry had it on 2026-09-23.

| Input | Registry id | Status | File | What still stands in the way |
|---|---|---|---|---|
| Tube, DLR, tram, bus, river, cable car | `tfl-journey-planner-timetables` | approved: routing, scoring, display | TransXChange XML in a zip, 24.31 MB. Republished daily, content changes weekly | Before launch: TfL's written answer on showing times from a stored copy, or a decision record. Registration on TfL's portal comes first |
| National Rail, London Overground, Elizabeth line | `network-rail-nwr-schedule` | **gated** | CIF, fixed-width text. Size not known | Three gate checks: the founder subscribes and saves the agreement; Network Rail confirms use from abroad; the attribution is confirmed |
| Streets for walking and cycling | `osm-geofabrik-greater-london` | approved: routing | `.osm.pbf`, 123 MB | None. The network is built from OSM alone, and timetables are loaded apart from it |
| Where journeys start | `ons-lsoa-pwc-2021` | approved: cells, routing | 4,994 points | None |
| Where journeys end | `uber-h3` | approved: cells | Software. Resolution 9 | None. It is a grid, not a dataset |
| Where stops and stations are | `dft-naptan` | approved: routing and others | CSV | None |
| Checking the result | `tfl-unified-api-journey-planner` | approved: display, validation_only | Live API, 500 calls a minute | Rail legs in an answer may not be stored. Keep the minutes and the error only |
| Weights for the roll-up | The areas part decides | | | Whatever it is must be registered for `routing`, or the contract must stop asking that of it |

Three things found while reading the registry and the gate's code:

1. **The rail entry cannot be opened at all today.** `Registry.require` lets a gated source be read only for an internal use it lists. `network-rail-nwr-schedule` lists `routing`, `scoring` and `display`, and no internal use. So the conversion trial that PLAN phase 0b asks for is refused by the gate. The entry needs `prototyping_only` added before anyone opens a CIF file.
2. **TfL's own feed leaves out two of TfL's own lines.** The Overground and the Elizabeth line come only from the rail schedule. One more question for TfL: does it publish timetables for those two lines under its own terms? A yes would shrink the gap of section 11.
3. **The Geofabrik extract may be cut at the boundary.** The registry asks for a few kilometres of margin. Whether the published extract has one is not known. If not, the network is cut from the England extract with a margin of 5 km, which needs a cutting tool on the runner.

Banned and held routes stay shut: Google Routes, Mapbox Matrix, TravelTime, the RDG feed, and the prebuilt rail GTFS that rests on it.

The publishers' pages were read again on 2026-09-24. [What a journey time needs](london-data-timetables.md) holds what each said that day, the steps to sign up, the list of files, and what a card may say of a journey. It corrects two things above. The 24.31 MB is the size of an example that the page says is not updated: the size of the file that is kept up to date is not known, and its page names no address for it. And no timetable is given to a person who has signed nothing, so registration on TfL's portal comes before the first fetch as well as before launch.

## 3. Engines

| | R5, through r5py | OpenTripPlanner 2 | RAPTOR in pure Python |
|---|---|---|---|
| Made for | Tables of travel time from many origins | Telling one passenger one route | Whatever we write |
| Licence | MIT. r5py is MIT or GPL-3.0-or-later, our choice | LGPL 3.0 | Ours |
| Needs | Java 21 or later (read). Python 3.10 or later. r5py 1.1.7 fetches its own build of R5 7.5.1, checked by checksum | Java 25 or later (read) | Python. A reader for `.osm.pbf`, which is a compiled extension |
| One search gives | One origin to every destination, for every minute of a window, as percentiles | One origin to one destination at one time | The same as R5, once written |
| Percentiles | Up to 5 a run (verification report). Default is the median alone (read) | None | Ours to write |
| Runs origins side by side | No. r5py takes them one at a time. We add that | Not relevant | Ours to write |
| Memory for London | 6 to 10 GB (estimate: unmeasured. The verification report sized 128 GB for 16 to 32 workers, which is 4 to 8 GB each) | Similar | 2 to 4 GB (estimate) |
| Time for one public transport run | 2.8 to 11.1 processor-hours (estimate: 2 to 8 seconds an origin, the verification report's unmeasured guess) | 48 days for one departure minute (estimate: 83.4 million queries at 50 ms) | 28 to 550 processor-hours (estimate: 10 to 50 times slower than R5) |
| Time to build it | 1 to 2 weeks (estimate) | | 3 to 5 weeks, then as long again to trust it (estimate) |
| Weakness | "R5 does not currently expose a stable programming interface", and its makers give no help to outsiders (read). So every version is pinned | Cannot make a table | No track record. Every fault is ours to find |
| Verdict | **Use it** | Not for the table | Plan B |

Why plan B is real and not only a line in a table: one wave of hosted CI is 20 jobs of 4 processors for 6 hours, which is 480 processor-hours (read, then multiplied). A pure Python engine fits in that at the lower end of its estimate. It becomes plan A if London's network does not fit in 16 GB and no money is to be spent, or if r5py stops working with a Java the runner offers.

ADR 0008 already says that the routing engine runs in CI. Java is a prerequisite of the runner, like `ruff`, and the engine is a jar that r5py fetches and checks. The routing dependencies go in a group of their own, so `make ci` and the API's image never install them.

## 4. What is computed, exactly

| Setting | Value | Note |
|---|---|---|
| Origins | 4,994 LSOA population-weighted centroids | A point more than 200 m from a street is counted as a defect, and the build stops until a person has looked at it |
| Destinations | Every resolution 9 hexagon whose centre is in Greater London: about 16,700 | The routing point is the point on a walkable street nearest the centre, inside the hexagon. A hexagon with no street inside it is left out and counted |
| Day modelled | One Tuesday, Wednesday or Thursday, in school term, in a week with no bank holiday, inside every feed's dates | Of the midweek days that qualify, the one whose count of trips in the window is nearest the median. A day of engineering works is not chosen by accident |
| Window | Every departure minute from 07:00 to 08:59: 120 of them | r5py's default is 10 minutes (read), so this must be set |
| Public transport | Walk to a stop, wait, ride, change, walk to the door. Or walk all the way, if that is faster | Up to 4 rides. No bike to the station |
| Cutoff | Public transport 120 minutes. Bike 60. Foot 60 | r5py's default limit is 2 hours (read). See decision 3 in section 15 |
| Walking | 4.8 km/h | r5py's default is 3.6 (read), so this must be set |
| Cycling | 15 km/h, on streets up to traffic stress 3, flat | r5py's default is 12 (read). Hills are not counted, and the methods page says so |
| Shortest time | 2 minutes | The floor the contract already holds the synthetic release to (2.9) |

**How typical and just missed are derived.** For one origin, the engine finds the fastest door-to-door journey to every destination for each of the 120 departure minutes. For one pair that gives 120 times. A minute with no journey inside the cutoff counts as longer than any other. Sorted, they give:

| Figure | Percentile | In words | Stored |
|---|---|---|---|
| `pt_typical` | 50th | Half of the departure minutes do at least this well | Served |
| `pt_just_missed` | 90th | Nine departure minutes in ten do at least this well. It is what a person meets who leaves as a train or bus pulls out | Served |
| | 10th, 25th, 75th | Kept so that the choice of 90 can be changed without routing again | Build store only |

**The rule of a percentile.** Put the times of the window in order, shortest first, with a minute that has no journey counted as the longest. The figure at `p` is the time at place `ceil(p × n / 100)` of the `n`, counted from 1. It is always a time that some departure minute has: nothing is averaged. `percentile_of` in `travel/engine.py` is the rule, and whether R5 counts the same way is for its first run to show (section 18).

Both figures come from the same run, so the second costs nothing. With one service every 10 minutes and a ride of 20, typical is 25 and just missed is 29: the worst case is 30, and the 90th percentile stops one odd minute from deciding it. The example holds where a person must be at the stop a minute before the train leaves: the waits are then 1 to 10 minutes, each 12 times over. A test holds the rule and the router to it. `pt_just_missed >= pt_typical` always holds, as the contract asks, because one is a higher percentile of the same list. Where the typical time is inside the cutoff and the just-missed time is not, the second cell is `-1`.

**The same inputs must give the same table.** The converters write every trip with its own times and never a headway, so the engine has nothing to draw at random. Whether R5 is then the same on every run is to be proven: one shard is run twice in every build and the bytes compared.

## 5. The size of the job

All times are estimates until the benchmark. Seconds per origin for public transport are the verification report's unmeasured guess of 2 to 8. Foot and bike are my guess, from the smaller area each search covers.

| Run | Origins | Departure minutes | Journeys found | Seconds an origin | Processor-hours |
|---|---|---|---|---|---|
| Public transport, weekday morning | 4,994 | 120 | 10.0 billion | 2 to 8 | 2.8 to 11.1 |
| The same without rail, for section 11 and as a check | 4,994 | 120 | 10.0 billion | 2 to 8 | 2.8 to 11.1 |
| On foot | 4,994 | 1 | 83.4 million | 0.2 to 1 | 0.3 to 1.4 |
| By bike | 4,994 | 1 | 83.4 million | 0.5 to 2 | 0.7 to 2.8 |
| **The first version** | | | | | **6.6 to 26.4** |
| Later: weekday evening, 19:00 to 20:59 | 4,994 | 120 | 10.0 billion | 2 to 8 | 2.8 to 11.1 |
| Later: Saturday, 11:00 to 12:59 | 4,994 | 120 | 10.0 billion | 2 to 8 | 2.8 to 11.1 |
| Later: after midnight | 4,994 | 120 | 10.0 billion | 2 to 8 | 2.8 to 11.1, and the feed must first be rewritten: R5 cannot read a time past 24:00:00 |
| Later: the journey home, from every hexagon | 16,700 | 120 | 10.0 billion | 2 to 8 | 9.3 to 37.1 |
| Not planned: Output Area origins | 26,369 | 120 | 52.8 billion | 2 to 8 | 14.6 to 58.6 |

| On hosted CI | Figure | Basis |
|---|---|---|
| One runner | 4 processors, 16 GB, 14 GB of disk | Read |
| One job | Up to 6 hours | Read |
| Jobs at once | 20 on the free plan. 256 in one matrix | Read |
| Price | "free and unlimited on public repositories" | Read |
| Shards | 8, each about 625 origins, 4 searches at a time in one Java process sharing one network | Proposed |
| Each shard | 10 to 20 minutes to build the network, then 12 to 50 minutes of routing | Estimate: 625 origins at 4.7 to 19 seconds for all four runs, 4 at a time |
| The whole build by the clock | 30 to 90 minutes. About 10 runner-hours at most | Estimate |
| Memory | 12 GB of heap on a 16 GB runner. **If London needs more, hosted CI is out** and the build moves to a rented machine | The first thing the benchmark settles |

| Stored | Cells | Bytes |
|---|---|---|
| One fine matrix, origins by hexagons | 83.4 million | 83.4 MB |
| The build store: 5 percentiles, with and without rail, then foot and bike | 12 matrices | 1.0 GB |
| One served matrix, areas by hexagons | 7.5 million | 7.5 MB |
| The served table: 4 matrices | 30.1 million | 30.1 MB (measured) |
| The inputs of one build, kept as evidence | | 0.2 to 0.4 GB (estimate; the rail file's size is not known) |

## 6. The steps, and where each can run

Three places are compared. "Python alone" is any machine with Python and nothing more: no Java, no geospatial libraries, no network.

| # | Step | Needs | Python alone | Hosted CI | Rented machine |
|---|---|---|---|---|---|
| 1 | Fetch each input, after `Registry.require`. Record address, time, checksum, size | The network. TfL and rail accounts | No | Yes, to be tried. Code has not yet read any publisher's file | Yes |
| 2 | Convert TransXChange to GTFS, for the one day modelled | Python, standard library | Code and tests, on small made-up files | Yes | Yes |
| 3 | Convert CIF to GTFS, for the same day, with station positions from NaPTAN | Python, standard library | The same | Yes | Yes |
| 4 | Check each feed: every line present, trips in the window counted by line | Python. A second opinion from the GTFS validator needs Java | Own checks only | Yes | Yes |
| 5 | Make the hexagons and their routing points | `h3`, a compiled extension. The street network | No | Yes | Yes |
| 6 | Build the network and route each shard | Java 21, 12 GB | No | Yes | Yes |
| 7 | Join the shards. Roll up to areas. Apply the floor | Python, standard library | Yes, on made-up matrices | Yes | Yes |
| 8 | Compare 1,000 pairs with TfL's planner. Compare with the last release | TfL key. The network | No | Yes | Yes |
| 9 | Write the release, through `write_release` | The registry | Yes, for a made-up one | Yes | Yes |
| 10 | Serve | 30 MB of memory | Yes | | |

**Two converters of our own, each for one day.** A general converter must understand calendars, exceptions and overlays. A converter for one chosen day need only ask of each journey: does it run that day? That is a few hundred lines of Python for each format, testable offline. It also closes a gap the research found: the known rail converter is written for the held RDG feed, not for Network Rail's. The second path that PLAN phase 0b asks for is an existing tool, run once as a check: trips per line in the window must agree within 1 in 100.

**What hosted CI means for a public repository.**

| Fact | Basis | So |
|---|---|---|
| A public repository's logs are open to read | Not checked today | A log line holds counts, checksums and timings. Never a key, never a signed address |
| An artifact can be downloaded by anyone with read access | Read | Inputs and matrices are not passed as artifacts. Shards write to a private bucket, which the plan already pays for |
| The free plan lists 500 MB of artifact storage. Whether that binds a public repository is not stated | Read | Another reason to use the bucket |
| The build needs three secrets: a TfL key, a rail login and a bucket key | | The workflow runs on a schedule or by hand. Never on a pull request |
| The terms forbid use "unrelated to the production, testing, deployment, or publication of the software project", and burden "disproportionate to the benefits" | Read | About 10 runner-hours a quarter is the project building its own data. A nightly rebuild would be 3,650 a year, and is not proposed |

## 7. From home points to named areas

An area holds about 11 LSOAs. An LSOA's weight in an area is the summed weight of the area's Output Areas that lie in it.

| Rule | Detail |
|---|---|
| The figure | The weighted lower median of the LSOAs' times. It is always a time some real home point has, so nothing is rounded or averaged |
| Beyond the cutoff | Counts as longer than any time. If the median lands there, the cell is `-1` |
| Not computed | Never produced by a finished build. A build with one origin unrouted fails. `null` is used only on purpose, as in section 11 |
| The floor | A time under 2 minutes is written as 2 |
| The spread | The shortest and longest LSOA time for each cell are kept in the build store. Serving them is decision 5 |
| When the map changes | Only this step runs again: minutes, not hours. The fine matrices are untouched (ADR 0003) |

## 8. How the table is stored and served

Loading a table of London's size as today's contract writes it, on made-up numbers:

| Format | On disk | To load | Peak memory | One search: 3 destinations, 2 matrices |
|---|---|---|---|---|
| `travel.json`, nested lists | 93.6 MB | 0.9 s to parse, 0.5 s more for core's record, before core's own checks | 707 to 730 MB | |
| `travel.bin`, one byte a cell | 30.1 MB | 2 ms | 44 MB, of which 30 is the table | About 1 microsecond |

All measured once, with Python 3.13. The JSON works. It needs a server with 1 GB to start on, to hold 30 MB.

| Proposed | Detail |
|---|---|
| `travel.json` | Keeps `source_ids`, `as_of`, `area_ids`, `destination_ids`, `cutoff_minutes`. Gains `method` and `inputs` (section 10), and `matrices`: the order of the four in the binary file |
| `travel.bin` | Bytes only, no header. For each matrix, for each destination, one byte for each area in `area_ids` order. A search reads one destination's 450 areas in one slice |
| A cell | 0 to 253 is minutes. 254 is beyond the cutoff. 255 is not computed |
| In memory | One `bytes` object. `Release.travel()` keeps its signature and works out an offset. No new dependency in core |
| Checked | Listed in the manifest with its checksum like any file. `parse_release` checks length, range and `pt_just_missed >= pt_typical` in one pass |
| The build store | Fine matrices as raw bytes, origins by hexagons, with an index file. In a private bucket. Never served, never in a release |

Production runs no routing engine, no database of journeys and no queue. A request never leaves the process to find a time.

## 9. Keeping it current

| Trigger | What happens |
|---|---|
| Each quarter | A full rebuild and a new release |
| The May and December rail timetables | A full rebuild, on a day modelled after the change. The launch release is built after the December 2026 change |
| Each week, on a schedule | Fetch both timetables. Count trips in the window by line. If any line moves by more than 1 in 20, or a line appears or goes, open an issue that says a rebuild is due. Nothing is published by this job |
| A new line or station | A rebuild by hand |
| TfL answers that a stored copy must be fresher | The same workflow on the cadence TfL names. Weekly matches how often the feed's content changes, and is about 520 runner-hours a year. Daily is a decision for the founder (decision 4) |

Every rebuild writes a report: cells that moved by more than 5 minutes, the 20 areas that moved most, and the share of pairs with a time, by mode and borough. A build is refused if more than 1 cell in 20 moved by more than 10 minutes and nobody has written down why. That catches a broken feed before a person sees it. The threshold is a first guess.

## 10. How a journey is cited

ADR 0014 asks four things of every record: its source, the date of the data, the date retrieved, and how it was derived. A travel time has several sources and one method. The record is per build, not per cell: 30 million cells share it.

| Proposed field of `travel.json` | Holds |
|---|---|
| `inputs` | For each input file: `source_id`, file name, `sha256`, `bytes`, `retrieved_on`, `published_on` where the publisher states it, and the dates the feed says it covers |
| `method.engine` | Name, version, and the checksum of the jar |
| `method.converters` | Version of each converter, as a commit |
| `method.day`, `method.window` | The day modelled, and 07:00 to 08:59 |
| `method.percentiles` | `{"pt_typical": 50, "pt_just_missed": 90}` |
| `method.settings` | Speeds, cutoffs, longest walk to a stop, most rides, traffic stress |
| `method.origins`, `method.destinations` | The version of the centroid service, the H3 version and resolution, and how many of each were routed and left out |
| `method.roll_up` | "weighted lower median", the weight's source, the floor |
| `as_of` | The day modelled. It is the date a `travel` fact carries |

What a person reads under a time, built by the client from the fact and this record:

> Timetabled time, for a weekday morning. Transport for London timetables of 9 November 2026. Network Rail schedule of 8 November 2026. Streets © OpenStreetMap contributors, 3 November 2026. Worked out by Burro for departures between 07:00 and 09:00 on Tuesday 10 November 2026. It takes no account of delays or engineering works. How this is worked out.

The dates above are examples. "OpenStreetMap" links to its copyright page, and TfL's three statements are on the sources page, as the registry asks.

| What is not cited, and why | |
|---|---|
| The route | The table holds minutes, not legs. Burro does not say which line a time rests on, because no stored record says so |
| Route detail from TfL, when a result is opened | It is TfL's answer for today, fetched then, and may differ from the stored time. It is shown as TfL's, with the time it was fetched, never blended with Burro's figure, never stored and never scored. The server sends TfL the hexagon's routing point and nothing that names the person or the place |
| A number of changes | Two more runs, with rides capped at 1 and at 2, would give "direct" or "one change" as a stored fact. 5.6 to 22.2 processor-hours more (estimate). Left for later |

## 11. If rail is not cleared in time

Without the rail schedule Burro has no National Rail, no Overground and no Elizabeth line. A time worked out without them is an upper limit: the true timetabled time is the same or shorter. For much of south, east and outer London it is far too long.

| Choice | What it does | Verdict |
|---|---|---|
| A. Show the longer times everywhere, with a label | Ranks every rail-served area too low. A newcomer cannot correct for it, and a Londoner sees it is wrong at once | No. It presents a figure known to be incomplete as the area's commute, against rule 7 |
| B. No time where a train could be the way to travel | The engine already drops a missing component and says so | **Yes, for testers** |
| C. No public transport at all until rail is in | Bike and foot only | The fallback of the fallback |
| D. Serve rail times to people in the UK only | Closes gate check 2 by design | Not proposed. It turns away people who have not moved yet, and needs each visitor's country |

**Choice B, exactly.**

| Rule | Detail |
|---|---|
| A place is near a train | A station of National Rail, the Overground or the Elizabeth line is within a 15-minute walk on the routing network. Stations come from NaPTAN, which is approved. No gated data decides it. The 15 is a first guess |
| A cell is `null` | The destination is near a train, and LSOAs holding half or more of the area's weight are near one |
| Every other cell | Comes from the run without rail |
| Bike and foot | Complete, for all of London |
| How much of London goes dark | Not known. My guess is more than half of all areas, for a destination in the centre. The first build measures it, and the coverage report prints it by borough |

**What Burro must then tell people.**

| Where | Words |
|---|---|
| Above every search and result | "Public transport times here count the Tube, the DLR, trams and buses. They do not yet count National Rail, the London Overground or the Elizabeth line. Where a train could be the way to travel, Burro gives no public transport time." |
| Beside a time that is shown | The usual sentence, then: "Trains are not counted." |
| Where there is none | "There is no public transport time from {name} to {place} in this release. A train may be the way to travel, and train times are not in Burro's data yet. It was left out of the score." |
| On an area's page, stations | Rail stations are listed, from NaPTAN. Their lines are not, since line names come from the gated schedule |
| Methods page | The modes counted, the share of pairs with a time, by borough, and the date this is expected to change |
| Nowhere | "All of London", said of public transport. A time that a reader could take to include trains |

ADR 0014 says a release is not fit to launch while any area lacks travel times. A release under choice B lacks them for many areas. So it goes to testers, and the public launch waits for rail, unless the founder amends the ADR (decision 1).

Once the founder has subscribed and the entry lists `prototyping_only`, both runs are made in every build, whether or not the gate is open. The run with rail stays in the build store until the entry is approved. Then one more build, about an hour, makes the full release.

## 12. How we know it is right

| Check | Passes when | Status of the threshold |
|---|---|---|
| Against TfL's planner, 1,000 pairs spread by borough and distance | The median difference is 3 minutes or less, and 9 in 10 pairs are within 10 | First guess |
| Every line is there | Each Tube line, the DLR, trams, and each rail operator that serves London has trips in the window | Firm |
| Coverage | No cell is `null`, save those section 11 makes so on purpose. By public transport every area reaches at least 9 in 10 hexagons inside the cutoff | First guess |
| The same twice | One shard run twice gives the same bytes | Firm |
| Against the last release | Section 9's report, read by a person before the release is used | Firm |
| A second opinion | The Connectivity Score in the Indices of Deprivation 2025, in aggregate only | Optional |

## 13. Changes this asks of others

| Where | Change | Why |
|---|---|---|
| Registry, `network-rail-nwr-schedule` | Add `prototyping_only` | So that a trial may open the file while the gate is shut |
| Registry, the roll-up's weight source | Add `routing`, with the reason | `travel.json` asks it of every source it names |
| The questions for TfL | Add: are Overground and Elizabeth line timetables published under your terms? | It may halve the gap of section 11 |
| Contract 2.6 | `travel.bin`, and `method` and `inputs` in `travel.json` | Sections 8 and 10 |
| Contract 2.6 | `cutoff_minutes` of 120, 60 and 60 in a real release | Section 4 |
| Contract 7.3 | A `travel_pt` sentence that ends "Trains are not counted.", and a reason in the `missing` sentence | Section 11 only |
| Contract 13 | The floor of 2 minutes is applied in the roll-up | Closes an open point |
| `packages/pipeline` | A `routing` dependency group: `r5py`, `h3`, and a reader for `.osm.pbf` | Each needs its one-line reason (rule 12) |
| A new ADR | The engine, the day modelled, the percentiles, and hosted CI as the place it runs | PLAN phase 0b asks for one record per spike |

## 14. Risks

| Risk | How likely | What we do |
|---|---|---|
| Rail is not cleared before the launch build | High. Nobody has subscribed | Gate check 1 and the question for Network Rail this week. Section 11 |
| London does not fit in 16 GB | Unknown | Benchmark first. Then a rented machine, or plan B |
| Seconds per origin are far above 8 | Unknown | More shards. 20 jobs at once is free |
| TfL requires a fresher copy than a quarter | Medium | Weekly rebuilds cost nothing. Section 9 |
| TransXChange holds services given only as "every N minutes" | Unknown. The file has not been opened | Write them out as trips at that headway, and record it as a derivation |
| A publisher will not give a file to a runner | Medium | Fetch by hand elsewhere and upload to the bucket. The checksum is recorded either way |
| r5py or R5 changes under us | Low for a pinned batch job | Pin both, and the jar's checksum. A failure delays a rebuild, not the product |
| Our own converters are wrong | Medium | Counts by line against a second tool. 1,000 pairs against TfL |
| A key leaks into a public log | Low | No pull request trigger. Logs are counts only. Rotate on any doubt |

## 15. What the founder must decide

| # | Decision | Recommendation |
|---|---|---|
| 1 | If rail is not cleared by the launch build: hold the launch, launch with stated gaps, or open the gate on your own reading of the licence? | Hold. The second needs ADR 0014 amended, the third ADR 0007 |
| 2 | Is just missed the 90th percentile or the 85th? | The 90th. All five percentiles are kept, so it can change without routing again |
| 3 | Are journeys routed to 120 minutes, or to 180 so that a limit of 120 is scored fairly past its end? | 120. The benchmark prices 180 |
| 4 | If TfL asks for a daily copy, rebuild daily or check daily and rebuild on change? | Check daily, rebuild on change, and write the decision record the registry allows |
| 5 | Show the spread of times within an area? | Later. Keep it in the build store now |
| 6 | May the fine matrices be published openly? | Not yet. Publishing would settle the share-alike question for good, and hand the table to anyone |

## 16. What can start today, and what it waits for

| Can start now, with Python alone | Waits for |
|---|---|
| Both converters and their tests, on small made-up files | Real files, to meet what the documents do not say |
| The roll-up, the floor and the binary format, on made-up matrices | The contract change |
| The driver that runs origins side by side, against a fake engine | Java, on a runner |
| The workflow file, not yet run | A first push, the secrets and the bucket |
| The rule for choosing the day, and the weekly check | Real feeds |

| Needs a person | Hours | Blocks |
|---|---|---|
| Register on TfL's portal. Put the questions to TfL | 1 | The TfL launch gate |
| Register on Rail Data Marketplace, subscribe, read and save the agreement. Put the question to Network Rail | 2 to 3 | Every rail time |
| Push the repository, add the three secrets, make the bucket | 1 | Every real build |
| Read the first validation report | 1 | The first real release |

## 17. What was read, and what is not known

Read on 2026-09-23 through a reader that summarises a page. Check the wording in a browser before relying on it.

| Page | What was taken from it |
|---|---|
| GitHub Docs: GitHub-hosted runners | 4 processors, 16 GB, 14 GB for a public repository. Free and unlimited there |
| GitHub Docs: Actions limits | 6 hours a job, 256 jobs a matrix, 20 jobs at once on the free plan |
| GitHub Docs: billing for Actions | 500 MB of artifact storage on the free plan. Silent on public repositories |
| GitHub Docs: downloading artifacts | Read access is enough. Kept 90 days by default |
| GitHub terms for additional products | The list of forbidden uses of Actions |
| Runner image readme, Ubuntu 24.04 | Java 8, 11, 17, 21 and 25, with 17 the default. Docker and Python 3.13. No GDAL, no osmium, no R |
| r5py: installation, travel-time matrices, reference | Java 21 or later. Window of 10 minutes, limit of 2 hours, walking 3.6 km/h, cycling 12 km/h, 8 rides, stress 3, the median alone |
| R5 readme | No stable interface. No help for outside users |
| OpenTripPlanner: version comparison | Java 25 or later. Analysis moved to other projects |
| Conveyal: methodology | Not read |

Not known, and nothing here should be read as if it were:

| Thing | What settles it |
|---|---|
| Seconds per origin, and memory, for London | The benchmark of 200 origins |
| That London has 4,994 LSOAs and about 16,700 hexagons | Counting them. The second is a calculation in the verification report |
| The size and layout of the rail file | The first download, once the gate allows it |
| That NaPTAN gives a position for every rail timing point | Opening the file |
| That R5 gives the same bytes twice | Running one shard twice |
| That R5 counts a minute with no journey as longer than any other | Its source, or a trial on a pair served once an hour |
| That the Geofabrik extract has a margin | Opening it |
| How much of London is within a 15-minute walk of a rail station | The first build |
| That the bucket is free at this size | The provider's price page |
| That secrets are withheld from a fork's pull request | GitHub's page on it. The design does not rely on it |
| The date of the December 2026 timetable change | Network Rail |
| The rented machine's price | A quote. £3 to £6 assumes £1.50 to £3 an hour for 32 processors and 128 GB, for 2 hours |

## 18. What is built, and what the first run of the engine must settle

Added 2026-09-24. **Measured** here was run on made-up numbers with Python 3.13. **Read** was read on the publisher's own page on 2026-09-24, twice, in different words, and what both readings gave is kept.

### 18.1 The shape of the step

| In | As | Through |
|---|---|---|
| A timetable, for the one day that is modelled | A feed in the open format that transit feeds use (GTFS): a zip of tables | `travel/feed.py`, which checks it as it reads |
| The streets, for the walk at each end | For London, the street extract, which the engine reads itself. For the made-up town, a list of points and links | The engine |
| Where the homes of each area are | Home points, each with its area and a count of homes | `travel/roll_up.py` |
| The places a person may name | The points journeys end at. `places.json` points each place at one | `travel/engine.py` |

| Out | As |
|---|---|
| For each area and each point journeys end at: the time by public transport that half of the departure minutes from 07:00 to 08:59 do at least as well as, the time that nine in ten do, the time by bike and the time on foot. Door to door, in whole minutes | `travel.json`, as contract 2.6 lays it out |
| The same from every home point, at five percentiles, one byte a journey | The fine matrices, for the build store |

| Module of `packages/pipeline/src/burro_pipeline/travel/` | What it does | Fit for London |
|---|---|---|
| `feed.py` | Reads a feed and holds it to ten rules: every stop has a point, every trip has its times in order, the calendar covers the day, no trip is a headway. A refusal names the table, the line and the rule | Yes. It is slow on a large feed: section 18.4 |
| `write_feed.py` | Writes a feed as a zip, the same bytes on any machine | Yes. The converters of section 6 will write through it |
| `engine.py` | What an engine is asked and gives back. The settings of section 4. The rule of a percentile | Yes |
| `route.py` | Origins in shards, the shards joined, one shard routed twice and compared. The fine matrices as bytes | Yes |
| `roll_up.py` | The weighted lower median of section 7, the floor, and the table a release holds | Yes |
| `plain.py` | A plain, slow router. Its first line says it is for tests | **No.** It measures as if the ground were flat and reads no street extract |
| `made_up.py` | The city of the synthetic release as a timetable, streets and homes | It is made up |
| `cli.py` | The step `python -m burro_pipeline travel --made-up` | It routes the made-up town alone. Without `--made-up` it stops, and names the rule `engine_is_installed` |
| `transxchange.py` | Reads a publisher's timetable in TransXChange as it stands on one day: the journeys that run, where each calls and when. It reads no name, and refuses a day on which a line has two timetables. It writes no feed: the converters of section 6 are not built | For the Underground and the DLR, whose files it has read as they were fetched on 2026-09-24. No timetable of a bus has been read with it |
| `timed.py` | Times a journey on the trains it is handed, by when a person must be there: what an estimate of a journey is held against ([ADR 0027](../adr/0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md)). It is no step of a build | For the check alone. It knows no street: a walk is a straight line made longer by one number |

What is not built: the two converters of section 6, the adapter that asks R5, the hexagons and their routing points, the rule that chooses the day, the comparison with TfL's planner, the weekly check, and `travel.bin`.

### 18.2 The engine, and the rule on programs

Section 3 chose R5, driven through r5py: it is made for tables of travel time from many origins, and it gives percentiles over a window in one search. Nothing built here changes that.

ADR 0008 says the project installs no package that ships a program it needs to run, and that work which needs one, "such as the routing engine", runs in CI. So R5 may run on a hosted runner and nowhere else, and no package of this repository depends on it. The step asks an engine through `Engine` in `travel/engine.py`, and the adapter that asks R5 is one module still to be written.

| Read on 2026-09-24 | Where | So |
|---|---|---|
| r5py needs a Java Development Kit of version 21 or later | r5py: installation | As section 3 has it |
| The runner image holds Java 8, 11, 17, 21 and 25. 17 is what the plain `java` starts. The folder of 21 is named by `JAVA_HOME_21_X64` | Runner image readme, Ubuntu 24.04 | The adapter must point at 21 itself. A step behind `tools/public_log.py` is given the runner's environment, so it can read the name. No action need be added to set Java up |
| With nothing set, r5py downloads R5 as it starts: `r5-v7.6-r5py-all.jar`, from the releases of `r5py/r5` on GitHub, held to a SHA-256 written in r5py's own source | r5py: `util/classpath.py` | Section 3 has 7.5.1. The version moves, so r5py is pinned to one version and the jar to one hash |
| The setting `r5-classpath` names a jar that is already on the disk. Left unset, r5py "downloads the latest compatible version" | r5py: configuration | Routing must reach no network (ADR 0015). So the jar is fetched by the step `fetch`, as a file of a registry entry, kept in the store under its hash, and named with `r5-classpath` |
| r5py names 15 packages that it needs. Among them are `requests`, which reaches a network, `jpype1`, which starts Java inside the Python process, `geopandas`, `rasterio` and `scikit-learn` | r5py: `pyproject.toml` | Each is a new dependency, with more beneath it. None is installed by this change. Section 18.3, rows 1 to 3 |
| The default heap of the Java machine is 80 in 100 of the machine's memory | r5py: configuration | 12.8 GB on a runner of 16 GB, where section 5 asks 12 |

### 18.3 What stands between the workflow and a run of the engine

`.github/workflows/data-travel.yml` is written as the other data workflows are, and `tools/check_data_workflows.py` holds it to the same rules. Today it routes the made-up town on two machines and compares the two. Each row below is for a person to decide or to do. None is worked round here.

| # | What | Why it is a person's | Until then |
|---|---|---|---|
| 1 | A second line that installs: the pipeline with a group `routing` | Rule 7 of the workflow check: one line installs, and it is the same in every job. A job that routes would install r5py and what it needs, and that job is given a key of the store | The workflow installs the pipeline alone |
| 2 | r5py and what it needs, each with its one-line reason | Rule 12 of `AGENTS.md`. r5py brings a library that reaches a network and one that starts a program | No package is added |
| 3 | A module of the pipeline that may start Java | `tests/fetch/test_only_fetch_reaches_a_network.py` lets no module of the pipeline name a library that reaches a network or runs a program, but for two modules of fetch. The adapter would be a third, added by a person with its reason | The step has no adapter. Without `--made-up` it stops |
| 4 | A registry entry for the jar of R5, with the address of its file and its licence as read on its publisher's page | The jar is a file that is fetched. No entry names it | Nothing fetches it |
| 5 | A timetable. TfL's is approved, and waits on registration at TfL's portal. It is TransXChange, so it waits on the converter of section 6 too. Rail is gated (section 2) | The registration is the founder's | The made-up timetable |
| 6 | A receipt for the street extract | The extract was fetched before fetch read an edition, and has no receipt. A file with no receipt is not opened | The made-up streets |
| 7 | A way for shards to hand their matrices to the job that joins them | No matrix is ever an artifact (ADR 0015). The store's code keeps raw files only, and a build key cannot write | The made-up town is routed whole in one job, in four shards |
| 8 | The environment `data-travel`, with its reviewer, its branch rule and four made-up secrets | Only the founder can make it | The workflow is on no default branch and has never run |

### 18.4 What the first run of the engine must settle

Every row is unmeasured. The first nine decide whether a release made with R5 means what the step says it means.

| # | To settle | How |
|---|---|---|
| 1 | Whether London fits in 16 GB, and the seconds an origin takes | The benchmark of 200 origins (section 1). It needs rows 1 to 6 of section 18.3 |
| 2 | Whether R5's percentile is the rule of section 4 | One pair served every 10 minutes, as the example of section 4. R5 must give 25 and 29 |
| 3 | Whether R5 counts a minute with no journey as longer than any other | A pair served once an hour, with a cutoff of 40 minutes |
| 4 | Whether R5 gives the same twice | `same_twice` in `travel/route.py`, on the first shard of every build |
| 5 | How R5 turns seconds into minutes. The router that is for tests rounds up | A pair whose time is known to the second |
| 6 | The slack before boarding, the longest walk to a stop and the longest walk of a change. `Settings` gives 60 seconds, 2,400 metres and 800 metres, and the last two are first guesses | R5's own settings, read in its source, and then a decision |
| 7 | That r5py starts with `r5-classpath` set and every socket refused | The step runs inside `sockets_refused()`, as the made-up town is routed |
| 8 | That R5 takes the feed the converters write, and that `feed.py` refuses what R5 would | Both read the same feed |
| 9 | That a time past 24:00:00 in a feed does not stop a morning run | Section 5 says R5 cannot read one |
| 10 | How long `feed.py` takes on a day of London's timetable | It keeps every call of every trip in memory, as Python numbers |
| 11 | How long the roll-up takes. It is 66.9 million medians at 1,002 areas, in plain Python | Time it on the fine matrices of the benchmark |
| 12 | The number of hexagons. 16,700 is a calculation | Counting them |

## 19. How many journeys

Section 1 sized the table for 450 named areas. A build of today has 1,002 areas: each is an MSOA, until named areas are curated. London has 4,994 LSOAs, counted in the first build, which settles one row of section 17. So an area has about 5 home points, and not 11.

| Journeys end at | How many | Cells, at 1,002 areas and 4 matrices | As `travel.json` | As bytes | What a time means |
|---|---|---|---|---|---|
| Every hexagon, as section 4 has it | About 16,700 (estimate, not counted) | 66.9 million | 208.3 MB (measured) | 66.9 MB (measured) | Door to door, to within a hexagon of the place |
| Every place a person could name | About 50,000 (the pipeline design's estimate) | 200 million | About 620 MB (estimate, at 3.1 bytes a cell) | 200 MB | Door to door. Two places in one hexagon hold the same times twice |
| Every station | Not known: no file of stations has been counted | 4,008 for each station | 12.5 KB for each station (estimate) | 4 KB for each station | To the station. The walk from the station to the place is not in it |

| Measured, at 16,700 hexagons | 450 areas | 1,002 areas |
|---|---|---|
| `travel.json` on disk | 93.7 MB | 208.3 MB |
| To parse it, and to make core's record of it, before core's own checks | 1.1 s and 0.9 s | 2.5 s and 1.8 s |
| Peak memory of the process that did so | 673 MB | 1,491 MB |
| The same table as bytes, one a cell | 30.1 MB | 66.9 MB |
| One search in the bytes: 3 places, 2 matrices, every area | | 0.47 ms, in a loop of plain Python |

What the numbers say:

1. **Hexagons are the right columns.** Places outnumber hexagons, so a column for each place is a larger table that says nothing more. A column for each station is far smaller, and changes what a time means: the contract says a time is door to door (2.6), and a time to a station is not. It would also leave a place that is far from any station with no honest time at all.
2. **The table has more than doubled since section 8 was measured.** As `travel.json` it needs about 1.5 GB to load, where section 8 found 0.7 GB. So `travel.bin` is no longer a saving to take later: a release with journeys for 1,002 areas should not be written as JSON. It is a change to the contract and to core, and is not made here.
3. **The fine matrices have not grown.** They are keyed by LSOA, and are 83.4 MB each whatever the areas are. Only the roll-up runs again when the areas change (section 7).

**When a person names a place that is not in the table.** With a column for every hexagon, every place of `places.json` has a column, so the cases are these. A test holds the first two on the release the step writes, and core's own tests hold the third.

| What was named | What the API does |
|---|---|
| Words that are the name of no place | The search of places finds nothing. The reader makes no journey: its status is `clarify`, with no offers, and nothing is applied. No place is guessed at |
| The id of a place the release does not hold | 422 `unknown_place`. The answer names the field and never the id |
| A place the release holds, from an area whose cell is `null` | The area stays. The journey is left out of its score and is said to be missing, and a firm limit is listed as not tested (contract 6.1). A finished build writes no `null` but on purpose (section 11) |
| A limit longer than the release routed | 422 `invalid_spec`: a journey beyond the cutoff could be inside the limit, and could not be tested |
| A place in a hexagon with no street | It is moved to the nearest hexagon that has one (section 0). Not built |

## 20. No record of the place that was asked for

A place a person names is where they work. It is in the body of a request and nowhere else (rule 9 of `AGENTS.md`).

| Part | Why it holds no record | Held by |
|---|---|---|
| The step | It is never told of a place. It works out every pair before anyone asks. It takes no argument that could name one, and reads no environment | `test_the_step_takes_no_word_that_could_name_a_place` |
| What the step prints | One line of counts and hashes, each under a name on the list of `tools/public_log.py`. No id of a place, of a point or of an area, and no name | `test_the_step_is_never_told_of_a_place_and_prints_none` |
| The release | It holds a time for every area and every point. Nothing in it says which was asked for, and a search changes no byte of it | `test_the_release_holds_every_pair_so_nothing_in_it_says_which_was_asked_for`, `test_a_search_changes_nothing_of_the_release` |
| The service's log, and its record of each call | No line and no record holds a place's id, its name or the id of its point. The line of a search to one place is the line of a search to any other, but for its id, its time and how long it took | `test_the_place_that_was_asked_for_is_in_no_line_and_no_record`, `test_the_line_of_a_search_to_one_place_is_the_line_of_a_search_to_any_other` |
| An address | No route that searches answers `GET`, so a place cannot stand in a path or a query | `test_a_place_is_named_in_the_body_of_a_request_and_never_in_its_address` |

One thing is outside this. Section 10 would ask TfL for the detail of a route when a result is opened, and would send TfL the hexagon's routing point. That is a place that was asked for, sent to another party. It is not built, and it is the founder's to decide before it is.
