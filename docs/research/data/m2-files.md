# What the files of the second build hold

Status: read on 2026-09-24, from the files in the store that day. It is a dated snapshot. A publisher that reissues a file makes another file, with another hash, and this page does not describe it. [The page on the files of the first build](m1-files.md) holds the files that build read.

No person has checked anything on this page. Every count was made by a program.

It is written for whoever writes the code that reads a file. Each section is about one file, and was written by whoever built the measure that reads it. A section holds the names of columns, sheets, layers and members, counts, and how a missing value is written. It holds no row of any file and no figure of any area.

Each file was first read with the pipeline's own step, `python -m burro_pipeline describe`, and then through `Inputs.open`, which asks the licence gate and holds the file to its receipt.

## File 8 of the Indices of Deprivation: transport noise

`File_8_IoD2025_Underlying_Indicators.xlsx`. The first build found this file in the store with no receipt, and read it as a trial. It has a receipt now. What the first build wrote of it is in [section 10 of its page](m1-files.md), and is still so. This section adds what was found since.

| | |
|---|---|
| Registry id | `mhclg-iod-2025-underlying-indicators` |
| File id | `f-cbc9ba7072bd` |
| Bytes | 14,500,506 |
| Kind | A workbook: a zip of 22 parts |
| Receipt | Yes. Edition `2025`, period `2021`, fetched on 2026-09-23. It says `geography: null`, as every receipt does |
| Rows are keyed by | `lsoa21`, read from the name of the column `LSOA code (2021)` |
| Read by | `derive/noise.py`, through `read_sheet` in `derive/noise_sheet.py` |

### The sheets

Eight sheets, none hidden. Seven hold figures. Six of those are about residents, and no step of a build opens one.

| Sheet, in order | Header is at | Rows under it | Columns | Opened by a step of a build |
|---|---|---|---|---|
| `Notes` | Row 11, in columns C to H | 37 | 6 | Yes, for four columns |
| `IoD25 Income Domain` | Row 1 | 33,755 | 7 | Never |
| `IoD25 Employment Domain` | Row 1 | 33,755 | 5 | Never |
| `IoD25 Education Domain` | Row 1 | 33,755 | 6 | Never |
| `IoD25 Health Domain` | Row 1 | 33,755 | 8 | Never |
| `IoD25 Crime Domain` | Row 1 | 33,755 | 12 | Never |
| `IoD25 Barriers Domain` | Row 1 | 33,755 | 14 | Never |
| `IoD25 Living Env Domain` | Row 1 | 33,755 | 14 | Yes, for two columns |

**How the rows and columns of the six were counted.** Added on 2026-09-24, after a check. The counts came from the step `describe`, which was run on the file once. It streams every sheet, takes the first row of each for the names of its columns, and counts the rest. So the first row of each of the six sheets about residents was read, by `describe`, and what it printed holds the names of their columns. That is in a folder git does not hold. No value under a first row was kept. `describe` asks no gate and needs no receipt, which does not square with the rule that every step that reads a publisher's file asks the gate first. Whether `describe` should ask the gate, and pass over a sheet the registry keeps apart, is the founder's to say.

- The sheet that is read is the part `xl/worksheets/sheet8.xml`, which unpacks to 21.7 MB. The reader finds it by the name of the sheet and never by its place.
- The text of every sheet is in one table, `xl/sharedStrings.xml`, of 2.0 MB. Only the text that a cell of a named column points at is kept.
- The file holds no row for an area larger than an LSOA: no MSOA, no district, no region, no total. So there is no figure of the publisher's for an area, and none to hold a sum to.

### The columns that are read

| Sheet | Column | Read | Why |
|---|---|---|---|
| `IoD25 Living Env Domain` | `LSOA code (2021)` | Yes | The code of the area |
| | `Noise pollution` | Yes | The figure |
| | The other 12 | No | Section 10 of the first page lists them |
| `Notes` | `Indicator` | Yes | To find the one row of the indicator |
| | `Data supplier` | Yes | The sentence of the measure names the supplier |
| | `Data time point` | Yes | The period. It is held to the receipt |
| | `Comments` | Yes | What the indicator is |
| | `Domain`, `Published` | No | |

### The column `Noise pollution`

| | |
|---|---|
| What a cell holds | A share from 0 to 1, as a number of the workbook and not as text |
| Decimal places | 3, in every cell. The notes say so of every indicator: "Unless otherwise noted, indicators are published to 3 decimal places" |
| A missing value | None is written. All 33,755 cells hold a number. How the publisher would write one is not known |
| A cell outside 0 to 1 | None |
| A cell that holds nought | None |
| A cell that holds 1 | 49 |
| A code that is there twice | None |
| Codes against the lookup, for England | 33,755 in the sheet, 33,755 in the lookup. None is in one and not in the other |
| Codes of London | 4,994 of 4,994 |
| Which way is more | More is louder. The notes say that every indicator but one is "presented in the form where higher score means more deprived" |

The reader gives an empty cell as none, and never as nought. An LSOA with no share adds nothing to a figure, and the coverage of its area falls by its homes. No cell of this file is empty, so no figure of this build is lowered by one.

### What the notes say of the indicator

The notes hold one row for `Noise pollution`, under the domain `Living Environment Deprivation Domain`.

| Column | What it says |
|---|---|
| `Data supplier` | "Defra’s Noise Modelling System" |
| `Data time point` | `2021` |
| `Published` | `Yes` |
| `Comments`, what it is | "The percentage of the population of each LSOA exposed to noise pollution greater than or equal to 55dB Lden" |
| `Comments`, the measure | The day, evening and night level is "the annual average long-term noise over 24 hours". It adds 5 dB to the evening, from 19:00 to 23:00, and 10 dB to the night, from 23:00 to 07:00 |
| `Comments`, the top | "the number of residents in each LSOA exposed to combined transport noise above 55 dB Lden" |
| `Comments`, the bottom | "the total population of the LSOA in 2021" |
| `Comments`, what was done to it | "Shrinkage was applied to this indicator" |

The step reads this row at every build. It stops if the row no longer gives the year of the receipt, 55 dB, the measure `Lden`, transport noise, residents or population, the supplier, or the shrinkage. So the label and the sentence of the measure say nothing that the file has stopped saying.

### What the file does not say

| Not said | What follows |
|---|---|
| Which kinds of transport were counted. The notes say "combined transport noise", and name no road, railway or airport | Nothing that Burro writes names a kind of transport |
| How a resident is placed in the noise: at a home, at a postcode or otherwise | The sentence says residents "exposed", in the publisher's word |
| Whether the level is at 55 dB or above it. One sentence says "greater than or equal to" and the next says "above" | The label says "55 dB or more", after the sentence that says what the indicator is |
| What shrinkage did, and to which LSOAs | The sentence says that it was applied, and no more |
| A top and a bottom | No sum can be taken. The figure is a mean by homes, marked as averaged |
| A licence of its own for this indicator | See below |

### Is it a measure of a place

It is. The noise is a model's, and the residents are how the places of an LSOA are weighed: a loud place where nobody lives counts for nothing. It says how much of where an area's people live is loud. It says nothing of who they are. The registry entry names noise as the one indicator of this file that is of a place.

It is a share of residents, and not of homes. Core's catalogue calls it "Share of homes at 55 dB or more of transport noise". The file supports "Share of residents exposed to 55 dB or more of transport noise". Until core says so, the measure is worked out and left out of a release, by the rule `measure_is_as_core_says`.

### The words above the table of notes

Rows 1 to 10 of the sheet `Notes` hold no cell. What a person sees there is a drawing, `xl/drawings/drawing1.xml`, which no step of a build reads. It was read once, for this page. It says:

- The file was published on 30 October 2025 and reissued on 13 November 2025. The reissue put right the district of one LSOA, outside London, "with no change to the data".
- "Some of the indicators contain public sector information licensed under the Open Government Licence v3.0". It does not say which.
- "OS data © Crown copyright 2025", and a statement of copyright for AddressBase products. It does not say which indicators either applies to.

The row of the noise indicator carries no statement of copyright. The registry asks that any such statement of an indicator is saved to `registry/evidence/`. None was saved: whether the three lines above are to be saved, and whether the credit of this file must carry them, is the founder's to say.

### What was made from it, and where

Nothing made from the file is in a tracked file, but for the counts on this page and the counts and three figures in `packages/pipeline/tests/derive/test_noise_on_the_real_files.py`. The figure of every area, with its row of evidence, was written to a scratch folder that git does not hold.

### Credit

Contains public sector information licensed under the Open Government Licence v3.0.

The words are the registry's, for `mhclg-iod-2025-underlying-indicators`. The registry marks them as not yet verified against the publisher's page.

The codes the sheet was held to are the statistics office's, from its lookup. Source: Office for National Statistics licensed under the Open Government Licence v.3.0.

## The grid of fine particles

`mappm252024g.csv`. It is the second file of its source in the store. The first is the grid of nitrogen dioxide, which the first build read: [section 11 of its page](m1-files.md). The two are laid out the same way, and this section says what differs.

| | |
|---|---|
| Registry id | `defra-pcm-background-air` |
| File id | `f-cb95c290ef00` |
| Bytes | 7,857,123 |
| Kind | CSV |
| Receipt | Yes. Edition `2024`, period `2024`, fetched on 2026-09-23 for the list `m2-living`, item `air-pm25-2024`. It says `geography: null`, as every receipt does |
| Rows are keyed by | `grid_1km`, read from the columns `x` and `y` |
| Read by | `derive/air_pm25.py`, with the parser of `derive/air_no2.py` |

### The layout

| | |
|---|---|
| Encoding | Plain ASCII, with no byte order mark |
| Ends of lines | CR LF. The last line has one too |
| Rows 1 to 4 | Notes, each in the first of four cells: `pm2.5`, `2024`, `annual mean`, `ug m-3` |
| Row 5 | Empty: three commas |
| Row 6 | The header: `gridcode`, `x`, `y`, `pm252024g` |
| Rows under it | 254,905, from row 7. Each has four cells |
| A missing value | The publisher writes `MISSING`. One square has it |
| What `describe` prints | 4 columns and 254,910 rows. It prints no names of columns, because the first full row holds empty cells: that row is a note |

| Column | Holds |
|---|---|
| `gridcode` | The publisher's number for the square. Each is there once |
| `x`, `y` | The middle of the square, in whole metres. Each ends in 500 |
| `pm252024g` | The annual mean for 2024, in micrograms a cubic metre, to at most 6 decimal places. No cell holds nought, and none is below nought |

### What differs from the grid of nitrogen dioxide

| | Nitrogen dioxide | Fine particles |
|---|---|---|
| The first note | `no2` | `pm2.5`, with a point |
| The column of values | `no22024` | `pm252024g`: no point, and a `g` at its end |
| The name of the file | `mapno22024.csv` | `mappm252024g.csv` |
| Squares with `MISSING` | None | One |
| Decimal places, at most | 7 | 6 |
| Bytes | 7,900,343 | 7,857,123 |

What is the same: the four notes and their order, the empty row, the place of the header, the 254,905 squares, and the `gridcode`, `x` and `y` of every one of them.

### What a parser must know

- **The note and the column do not name the pollutant the same way.** The note is `pm2.5`. The column is `pm25`, then the year, then `g`. A parser that makes the name of the column from the note finds no column.
- **The file does not say what the `g` stands for.** The list the file was fetched by records that the publisher's page says it stands for gravimetric units. No build reads that page, so no sentence of the measure says it.
- **The one square with no value is the one whose easting is below nought.** It is the most westerly square of the file, and far from London. The grid of nitrogen dioxide gives that square a value.
- **Every centre of an output area of London stands on a square with a value.** They stand on 1,444 squares, as for nitrogen dioxide. So each of the 1,002 areas has a figure, from all of its homes.
- The file does not say which grid `x` and `y` are on. They are those of the grid of nitrogen dioxide, which fit Great Britain on the National Grid.
- The publisher's page says the data begins on row 6. Row 6 is the header, and the data begins on row 7, as in the grid of nitrogen dioxide.
- The file holds no row for an area, a district or a region, and no total. So there is no figure of the publisher's to hold the figure of an area to. A figure is held to the squares it was taken over: it lies between the lowest and the highest of them.

### What the file does not say

| Not said | What follows |
|---|---|
| That the values are modelled, or that they are of the background | The registry entry says both, from the publisher's page. The sentence of the measure says both, as that of nitrogen dioxide does |
| What `g` stands for | Nothing that Burro writes says how the particles were weighed |
| How sure the model is of a value | The figure is given to one decimal place. No sentence gives a margin |
| Which way is better | Core decides that, and holds no feature for fine particles |

### Core holds no measure of it

The registry entry says that PM2.5 "needs its own place on the feature allowlist before it is used". Core's list of features holds nitrogen dioxide, and nothing for fine particles. So the measure is worked out and is in no release. `derive/air_pm25.py` is not among the measures of a build, and a test fails when core gains the feature.

### What was made from it, and where

Nothing made from the file is in a tracked file, but for the counts on this page and the counts and three figures in `packages/pipeline/tests/derive/test_air_pm25_on_the_real_files.py`. The figure of every area, with its row of evidence, was written to a scratch folder that git does not hold.

### Credit

© Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL).

The words are the registry's, for `defra-pcm-background-air`. The registry marks them as not yet verified against the publisher's page.

The centres of output areas are the statistics office's. Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

## Editions of the files that had no receipt

Status: read on 2026-09-24, from 37 files that were fetched on 2026-09-23 and kept in the store with no receipt. No person has checked anything in this section. Every date and every count was read by a program.

A receipt is written by fetch, and only when the list states a file's edition and the period of its data and is sure of both. The page of each of these files names no edition. So the lists stated none, and fetch kept each file and wrote no receipt. Until a file has a receipt, no step of a build may read it.

This section is not about one file, and no measure reads these files yet. It says what each file says of when it was made, how little of it was read to find that, what the lists state now, and what a second fetch will do.

**These files were not read through `Inputs.open`**, which needs a receipt. Each was opened by a short program that is not kept. Each program asked the licence gate first, for the use the list gives, and read the part of the file that dates it. `packages/pipeline/tests/fetch/test_editions_on_the_real_files.py` reads the same parts, and is kept. No step of a build may read a file this way.

### The rule

It is at the head of each list, in three lines.

| # | The rule | Written as |
|---|---|---|
| 1 | The edition is what the publisher calls this version: a label, a number, a time | As the publisher writes it: `2026-09-22T20:22:59Z` |
| 2 | Where the publisher calls it nothing and the file gives a day, the edition is that day | `extract of 2026-09-16`, `last changed 2025-12-22` |
| 3 | Where neither gives one, the edition is the day the file was retrieved, written so and left under `unsure` | `retrieved 2026-09-23` |

- Never a guess. The notes of each item say where in the file its day stands, and name the file by its id.
- The period is the day the data is as at. For a register of what stands, that is the day of its extract.
- A receipt holds the edition and no notes. So the edition itself says which kind of day it is.

### What each file says of itself

| Files | Registry id | Kind | Where its day stands | What it says |
|---|---|---|---|---|
| The food hygiene register, one file for each of 33 authorities | `fsa-food-hygiene-ratings` | XML. 1.3 to 5.7 MB each, 80.4 MB together | `ExtractDate`, in `Header`, the first element under the root `FHRSEstablishment`. The header ends at byte 207 of every file. It holds `ItemCount` and `ReturnCode` too | A day for each file, from 2026-09-09 to 2026-09-16 |
| Town centre boundaries | `gla-town-centre-boundaries` | GeoPackage, 1,712,128 bytes, one layer | `last_change` of the layer, in the table `gpkg_contents` | 2025-12-22T16:37:50.337Z |
| NHS trust sites and NHS trusts | `nhs-ods` | CSV with no header row. Every line holds 27 cells | Nowhere. The name of each file holds no date, and no line is a title or a note | Nothing |
| The street extract | `osm-geofabrik-greater-london` | | The time its data runs to, in the header block of the file | 2026-09-22T20:22:59Z |

Of the street extract nothing else is written here. It is for the routing network and for display alone (ADR 0004).

**The food register, by the day in the header.**

| `ExtractDate` | Files |
|---|---|
| 2026-09-16 | 24 |
| 2026-09-15 | 4 |
| 2026-09-13, 2026-09-12, 2026-09-11, 2026-09-10, 2026-09-09 | 1 each |

- The list gives the day of each file, and the id of the file it was read in.
- For all 33, the day in the header is the day before the "last update" the publisher's page gave for the authority when it was read on 2026-09-23.
- The registry gives the cadence as daily, and the list said that a file changes daily. On the day of the fetch the newest file was 7 days old and the oldest 14. So a file is not made again each day. How often one is made, no file says.
- The licence registry asks that the data date be shown wherever a figure made from the register appears. `ExtractDate` is that date.

**The town centre boundaries.** The layer has a column for the day a boundary was first added, one for the day it was last updated and one for the day it was removed. All three are empty in every one of its 234 rows. The file holds one document of metadata, whose element for dates is empty. So `last_change` is the one day the file gives. The publisher's own record of the dataset gives the next day, 2025-12-23, as the day the file was last checked. The boundaries are of the London Plan: when each was drawn, the file does not say.

### How little was read

| Files | What was read | What was not |
|---|---|---|
| The food register | The first 4,096 bytes of each file were taken, and cut at the end of the header. What stood after it was dropped unread | Every establishment |
| Town centre boundaries | The file's own tables of contents and of metadata. The names of the elements of its metadata, and the text of none but a date. The least and the greatest of each of the three date columns, which gave nothing | Every row of a town centre |
| NHS reports | Every line was split into cells and the cells of each line were counted. No cell was kept, printed or looked at | Every row of an organisation |
| The street extract | The first block of the file, which is its header, and of it the time and the number of fields | Every node, way and relation |

The step `describe` was run on each of the 37 first. What it printed is in a folder that git does not hold.

**None of the 37 had a receipt when it was read.** Added on 2026-09-24, after a check. A file with no receipt is read by no step of a build, and no step of a build read one. But each of the 37 was opened by its path in the store, outside `Inputs.open`, by a scratch program and then by `tests/fetch/test_editions_on_the_real_files.py`, which opened all 37 again whenever the store was named. The gate was asked first each time, and the registry allows each. That module of tests is now skipped, with the store or without it. Whether the part of a file that dates it may be read before a receipt exists is the founder's to say. What was read then is the edition the two lists state, and it stays as it is until that is said.

### What the lists state now

| Files | Edition | Period | Under `unsure` | `plan` says |
|---|---|---|---|---|
| Town centre boundaries | `last changed 2025-12-22` | 2025-12-22 | No | Ready |
| The food register, 33 files | `extract of` and the day in the header | That day | Yes | `why=6` |
| The street extract | `2026-09-22T20:22:59Z` | 2026-09-22 | Yes | `why=6` |
| NHS trust sites and NHS trusts | `retrieved 2026-09-23` | 2026-09-23 | Yes | `why=6` |

`plan --list m2-places` reads 9 of 45 ready, where it read 8. `plan --list m2-living` reads 7 of 15, as before.

**Why 34 files that are dated by their own file are still not sure.** An edition read in a file is sure of that file and of no other. The list cannot name that file to fetch: it names an address, and the publisher puts another file there. The next table says what fetch then does. So where a publisher replaces a file under one address, the edition stays under `unsure`, and `test_editions_a_file_gives.py` holds the lists to that. The town centre boundaries were last changed nine months before the fetch. They are taken as the files of Ordnance Survey in the same list are: ready, with a note of what to look at in the line of the fetch.

That the day a file was retrieved was 2026-09-23 rests on two things. The store wrote each of the 37 between 21:32 and 21:49 UTC that day. And the receipts of the other files of the same two lists give 21:33 to 21:52 UTC that day. No receipt says it of these files, because they have none.

### What a second fetch does

Read in `fetch/run.py` (`keep`, `settle`) and `fetch/store.py` (`put`), and then driven on made-up files, with no network. A file is kept under the hash of its bytes. Fetch looks at what kind of file arrived. It reads no header, and compares what arrived with nothing the list says but its format and its size.

| The list | What arrives | The line | The store | The receipt |
|---|---|---|---|---|
| States the edition, and is sure | The bytes in the store | `status=ok new=0` | Nothing is added | Written, for the file in the store. Its `retrieved_at` is the time of this fetch, not of the first |
| States the edition, and is sure | Other bytes | `status=ok new=1` | A second file is kept beside the first | **Written for the new file, with the edition and the period the list states, which were read in the old one. It is wrong, and nothing says so but `new=1`.** The first receipt of a file is never written over, in the folder or in the store |
| States the edition, under `unsure` | The bytes in the store | `status=missing why=6 new=0` | Nothing is added | None |
| States the edition, under `unsure` | Other bytes | `status=missing why=6 new=1` | A second file is kept beside the first | None |

**What becomes of the file in the store.** It stays. Fetch never writes over a file and never removes one. Where other bytes arrive, the file of 2026-09-23 has no receipt and never gets one from a fetch, so no step can read it. `held` still lists it. The 37 files are 219.2 MB together.

| Files | How often the publisher replaces the file | When it is fetched again |
|---|---|---|
| Town centre boundaries | Seldom | The same bytes, most likely: `new=0`, and a receipt. If the line says `new=1`, the receipt holds the day of another file |
| The food register | When its authority has a new extract. 24 of the 33 were a week old on the day of the fetch | Not known for any one file. The same bytes where no extract was made since, and other bytes where one was. No receipt either way, as the list stands |
| NHS reports | The publisher says the data is updated each night | Other bytes, most likely. No receipt either way |
| The street extract | About daily | Other bytes. No receipt |

### How the 36 can have a receipt

As fetch stands, it takes two fetches close together, and care.

1. Fetch the list as it is committed. Each of the 36 is kept and no receipt is written. The line of each gives `file_id=` and `new=`.
2. Where a line says `new=0`, the list is right. Where it says `new=1`, put the id of what arrived in the notes of the item, run the test on the real files, and state the edition the file gives. For an NHS report, state the day of this fetch. Commit the list, still under `unsure`.
3. At once, copy the list to a folder git does not hold. In the copy take `edition` and `data_period` out of `unsure`. Fetch with `--list` and the path of the copy, and `--only` for each item wanted.
4. Every line must say `status=ok new=0`. A line that says `new=1` has a receipt that is wrong: the publisher changed the file between the two fetches. Its receipt must be taken out of the folder and out of the store by hand, which no step does.

The committed list stays under `unsure`, so that a later fetch cannot write an old day on a new file. A build pairs a receipt with its item by the source, the use, the edition, the period and the address. It does not read `unsure`.

**What would make one fetch enough** is a change to fetch, which is not made here: it is a decision about what a receipt rests on. Either of two would do.

| Change | What it does | What it costs |
|---|---|---|
| The list names the hash of the file an edition was read in. Fetch writes a receipt only for that file | What arrives with another hash is kept, given no receipt, and its line says so | One field of the list, one reason with a number of its own, and its tests. A person still reads each new file |
| Fetch reads the day a file gives, for the kinds it knows, and holds the list to it | The same, and the line can say that the day differs | A reader for each kind of file, in the one part that reaches a network |

### What was not checked

| Not checked | Why |
|---|---|
| Any page of any publisher | None was opened. Nothing was fetched |
| Whether any of the 37 has changed since 2026-09-23 | The same |
| That `last_change` is the day the boundaries are as at | It is the day the file was written. The file says no more |
| That an NHS report is as at the day it is retrieved | The publisher's page says the data is updated each night, as the list records. The file says nothing |
| What time zone `ExtractDate` is in | The header gives a day and no time |
| The address each file arrived from | A receipt holds it, and these files have none. The street extract is kept under a name that holds a day, which the address in the list does not |

### Credits

Every date and count in this section was read in a file of one of these publishers. The words are each publisher's own, as the licence registry holds them.

| Publisher | Files | Credit |
|---|---|---|
| Food Standards Agency | The food hygiene register | Contains public sector information licensed under the Open Government Licence v3.0. |
| Greater London Authority | Town centre boundaries | Greater London Authority - Contains public sector information licensed under the Open Government Licence v3.0 |
| | | Contains OS data © Crown copyright and database rights 2019. |
| NHS England | NHS trust sites and NHS trusts | Contains information from NHS England, licenced under the current version of the Open Government Licence |
| OpenStreetMap contributors, extract published by Geofabrik GmbH | The street extract | © OpenStreetMap contributors |

The Greater London Authority cannot warrant the quality or accuracy of the data. Its boundaries are indicative, as its page says.

## The workbook of median prices paid

`medianpricepaidformsoa.xlsx`. It gives the median price paid for a home in each MSOA, for every year that ends with a quarter since 1995, for all homes and for four kinds of home.

| | |
|---|---|
| Registry id | `ons-median-house-prices-msoa` |
| File id | `f-545982134c5e` |
| Bytes | 68,462,591 |
| Kind | A workbook: a zip of 74 parts, 17 of them sheets |
| Receipt | Yes. Edition `Year ending March 2026`, period `2025-04` to `2026-03`, fetched on 2026-09-23 for the use `validation_only`. It says `geography: null`, as every receipt does |
| Rows are keyed by | `msoa21`. The workbook names no census, so this is what the rows were found to be when held to the lookup |
| Read by | `derive/price.py`, through `read_sheet` in `derive/noise_sheet.py` |

### The registry holds it for validation only

The entry gives the workbook one use, `validation_only`: a check of Burro's own medians, once they are worked out from the sales themselves. Its conditions say that a figure of it is not shown and feeds no ranking, and what must be done before one is: open the workbook, confirm the wording of the credit, and change the uses. The gate allows the file to be read for that use, and refuses it for `scoring` and for `display`.

So the file was read, and figures were worked out, and no release may carry one. `derive/price.py` asks the gate for `validation_only` and is joined to no build. To change the entry is the founder's.

### The sheets

Seventeen sheets, none hidden. Seven are opened.

| Sheet | Holds the median price paid for | Header is at | Rows under it | Columns | Opened |
|---|---|---|---|---|---|
| `Cover` | Notes, in one column under the title of the workbook | Row 1 is the title | 20 | 1 | Yes |
| `Contents` | What each sheet holds | Row 3 | 15 | 2 | Yes |
| `1a` | A home of any kind | Row 3 | 7,264 | 126 | Yes, for three columns |
| `1b` | A detached house | Row 3 | 7,257 | 126 | The same |
| `1c` | A semi-detached house | Row 3 | 7,262 | 126 | The same |
| `1d` | A terraced house | Row 3 | 7,264 | 126 | The same |
| `1e` | A flat or a maisonette | Row 3 | 7,261 | 126 | The same |
| `2a` to `2e` | The same five, for newly built homes | Row 3 | 7,264, 7,257, 7,262, 7,264, 7,261 | 126 | Never |
| `3a` to `3e` | The same five, for existing homes | Row 3 | The same | 126 | Never |

- A sheet of figures unpacks to between 34.7 and 37.2 MB. The table of text that every sheet points into is 0.5 MB and holds 15,268 texts.
- Above the header of a sheet of figures stand two rows, each of one cell: the title of the table, and its source.
- A row is an MSOA of England or of Wales. Sheet `1a` holds 6,856 English and 408 Welsh, which are the counts the council tax tables hold for the MSOAs of 2021.
- A sheet of one kind of home holds fewer rows than `1a`. An MSOA with no row on such a sheet has no cell to read, in any year.
- The zip holds five parts in a folder named `[trash]`. They are part of no sheet and are not read.

### The columns of a sheet of figures

| Column | Holds | Read |
|---|---|---|
| `Local authority code` | The district the MSOA is in | Yes. It is held to the lookup and is part of no figure |
| `Local authority name` | Its name | No |
| `MSOA code` | The MSOA. Starts `E02` or `W02` | Yes |
| `MSOA name` | Its name | No |
| `Year ending Dec 1995` to `Year ending Mar 2026` | The median for the twelve months to the end of that month. 122 columns, one for each quarter | One: the year the receipt gives, which is the last |

- A year is named by the first three letters of its last month and the year: `Mar`, `Jun`, `Sep`, `Dec`.
- The contents name the same year in full: "year ending March 2026". The step holds the last year the contents give to the receipt.

### How a cell is written

| The file writes | It means | How it is read |
|---|---|---|
| A whole number, as a number of the workbook | The median, in pounds | As it is written. It is not rounded |
| `[x]`, as text | No figure: no sales, or fewer than five, of that kind in that year | No figure. The state is `suppressed` |
| No row for the MSOA | The sheet holds nothing for it | No figure. The state is `source_gap` |

- For London's rows, in nine of the years, no cell was empty and no cell held other text than `[x]`. The step stops at either.
- Every figure of London for the year that is read is a whole number of pounds. The cover does not say whether a median is rounded.
- In all of England and Wales, for the year that is read: `1a` has no `[x]`, `1b` has 1,947, `1c` 687, `1d` 352 and `1e` 2,669.

### London, for the year ending March 2026

| Sheet | Rows of London's MSOAs | With a figure | `[x]` | No row |
|---|---|---|---|---|
| `1a`, any kind | 1,002 | 1,002 | 0 | 0 |
| `1b`, detached | 995 | 195 | 800 | 7 |
| `1c`, semi-detached | 1,000 | 549 | 451 | 2 |
| `1d`, terraced | 1,002 | 873 | 129 | 0 |
| `1e`, flat or maisonette | 1,002 | 927 | 75 | 0 |

In every London row of every sheet that is read, the `Local authority code` is the code the lookup gives the MSOA's borough.

### What the cover says

The words are the publisher's.

| Of | The cover says |
|---|---|
| The unit | "All the figures within these datasets relate to pounds sterling (£)" |
| A cell with no figure | "Where the symbol [x] appears in the tables, no data are available. This is due to there being no house sales or fewer than five house sales of that particular type in the given year for the selected geography. These are suppressed as fewer than 5 sales is not deemed enough to produce a robust average and is therefore not reported." |
| The source | "Source: Office for National Statistics, HM Land Registry." |
| Reuse | "These statistics were adapted from data from the HM Land Registry licensed under the Open Government Licence v.3.0. Users should include a source accreditation to ONS - Source: Office for National Statistics." |

The cover also names a page on quality and method. No build reads a page, so nothing that Burro writes rests on it.

### What a parser must know

- **`[x]` is never nought.** It stands for none to four sales. The file does not tell none from four.
- **The file gives no count of sales.** A figure rests on five sales or more, and the file does not say how many. So a figure of five sales cannot be told from one of five hundred.
- **The file gives a median and no quartile.** A row of `cost.json` holds a lower and an upper quartile and a confidence by the count of sales. None of the three can be read here.
- **The file gives no total.** It holds no row for a borough, for London or for England. So there is no figure of the publisher's to hold the sum of the areas to.
- **What can be held in its place.** The median of all the homes sold lies between the lowest and the highest median of the kinds. In all 160 areas of London where the four kinds each have a figure, it does. In all 57 areas where newly built and existing homes each have a figure, the figure of `1a` lies between the two. Where a kind is withheld the rule need not hold, because the homes behind `[x]` are in the median of all.
- **Read a sheet by its name and hold it to the contents.** The sheets for newly built and for existing homes have the same columns as those that are read.
- **The name of the column changes with the file.** It is made from the period of the receipt.

### What the file does not say

| Not said | What follows |
|---|---|
| How many sales stand behind a figure | No confidence is given. What the figure cannot see says that it may rest on as few as 5 sales |
| Which sales are counted, and which are left out | The sentence of the measure says "the homes that were sold" and no more |
| Whether a year is of the days homes were sold or of the days sales were registered | The sentence says "in the year ending March 2026", as the file does |
| Whether a median is rounded | The figure is given as it is written |
| Which census the codes follow | The sheet of all kinds is held to the MSOAs of the lookup of 2021, and every sheet to its boroughs |
| Which way is better | The file says what was paid. More is dearer |

### Is it a measure of a place

A price is what was paid for a home. It describes sales of buildings, and no column of the workbook describes who lives anywhere. Every column of a sheet is a code, a name or a median price. A price can stand in for who can afford to live somewhere, as any measure of homes can, so it is one for the audit of ADR 0006 before it is ranked on.

### Core holds no measure of it

Core's list of features holds nothing for a price. The contract's place for a price is a row of `cost.json`, by kind of home, which this file cannot fill. So the measure is worked out and is in no release. `derive/price.py` writes its rows of evidence under names of its own, `price_median` and one for each kind, and a test fails when core gains a feature for a price.

### Rents

No rent was read. The statistics office publishes rents for boroughs and for postcode districts, and both files are in the store with a receipt. The plan says that the model which would bring one down to an area was never designed. The contract has no place for a borough's figure beside an area, and the pipeline design forbids a figure of a larger area to be pasted onto a smaller one. So rent is left out.

### What was made from it, and where

Nothing made from the file is in a tracked file, but for the counts on this page and the counts and three figures in `packages/pipeline/tests/derive/test_price_on_the_real_files.py`. The figure of every area, with its row of evidence, was written to a scratch folder that git does not hold.

### Credit

Source: Office for National Statistics. These statistics were adapted from data from the HM Land Registry licensed under the Open Government Licence v.3.0.

The words are the workbook's own, from its cover. The registry holds other words for this source, "Source: Office for National Statistics licensed under the Open Government Licence v.3.0", and marks them as not verified. It also says that a statement of HM Land Registry may be needed. Which words are shown is the founder's to settle before any figure is.

## OS Open Greenspace: parks and green space

**What has changed since this section was written.** Added on 2026-09-24, after two checks of the second build. Green cover and the nearest park are in the list of the measures of a build, `derive/measures.py`: each is worked out at every build. Green cover was carried by the release `lon-2026-09-24-02` under core's name, "Public green space as a share of the area". It now carries a name of its own, "Public parks and gardens as a share of the area", so a build leaves it out, and `lon-2026-09-24-03` does not hold it. The nearest park is named "Straight-line distance to the nearest marked way into a park of 2 ha or more". The check of 20 named commons has not been made. What follows is as it was written.

`opgrsp_gml3_tq.zip` and `opgrsp_gml3_tl.zip`. The publisher cuts the product to the squares of the National Grid that are 100 kilometres wide, and London lies on two. Each file is a zip with one document of GML.

| | TQ | TL |
|---|---|---|
| Registry id | `os-open-greenspace` | the same |
| File id | `f-02f39a296d6f` | `f-f9c10aca1661` |
| Bytes, zipped | 5,203,830 | 2,362,522 |
| The square, by its corner nearest the grid's origin | 500,000 east, 100,000 north | 500,000 east, 200,000 north |
| Receipt | Yes. Edition `2026-04`, period `2026-04`, fetched on 2026-09-23. It says `geography: null` and names no member | the same |
| Rows are keyed by | `polygon` for a site, `point` for a way in | the same |
| Read by | `derive/green_sites.py`, for `derive/green_cover.py` and `derive/park_proximity.py` | the same |

The step `describe` lists the members of the zip and says of the document `kind: not_read, looks_like: xml`. It has no reader of GML. The document was then read with the pipeline's own reader of XML, `fetch/markup.py`, which refuses a document type and an entity. No library was added.

### The members

| Member, under the folder `OS Open Greenspace (GML) TQ/` | Bytes, TQ | Bytes, TL | Read |
|---|---|---|---|
| `data/OSOpenGreenspace_TQ.gml` | 53,852,844 | 24,286,426 | Yes |
| `doc/licence.txt` | 192 | 192 | Once, for this page |
| `readme.txt` | 592 | 592 | Once, for this page |

The folder and the document of the other file are named for `TL`. The note says how the folders are laid out, and nothing of what the data means.

### The document

| | |
|---|---|
| Encoding | UTF-8, declared, with no byte order mark. A few bytes of each file are outside ASCII, and all are in names of sites |
| Ends of lines | CR LF. Indented with tabs |
| Document type, entity | None declared |
| Root | `os:FeatureCollection`, with `gml:id="OSOpenGreenspace"` |
| `gml:description` | Whose the data is and a year: Ordnance Survey, Crown copyright, 2026. It is the one date in the document |
| `gml:boundedBy` | The box the features of the file fit in. It runs up to 1,150 metres past a side of the square |
| `os:metadata` | A link to the publisher's record of the product. It is the one element that is written empty |
| `os:featureMember` | One for each feature: 68,434 in TQ and 30,753 in TL |
| Coordinates | Every outline and every point says `srsName="urn:ogc:def:crs:EPSG::27700"`, the National Grid, in two dimensions. A number has at most 2 decimal places |
| Order | Every way in stands before every site |

### The two kinds of feature

| Feature | TQ | TL | Both files, each once |
|---|---|---|---|
| `ogsp:GreenspaceSite` | 21,992 | 9,992 | 31,961 |
| `ogsp:AccessPoint` | 46,442 | 20,761 | 67,203 |

- **23 sites are in both files.** Each lies across the line between the two squares, and is drawn the same way in both: the same kind and the same points. The parser keeps it once, and stops if two files draw one site differently.
- **No way in is in both files.** A way in is in the file of the square it stands on. Every one of the 67,203 stands on the square its file is named for.
- **Every site touches the square its file is named for.** So a file holds every site of its square, whole, and the ways in that stand on the square.

### What a site holds

| Element | In how many sites, TQ and TL | Holds | Read |
|---|---|---|---|
| `gml:id`, on the feature | All | `id` and 36 signs of an identifier | Yes |
| `ogsp:function` | All | The kind of site. One of ten, under the code list `OpenFunctionValue` | Yes |
| `ogsp:distinctiveName1` | 6,394 and 2,834 | A name of the site | No |
| `ogsp:distinctiveName2` | 27 and 15 | A second name. Never without the first | No |
| `ogsp:geometry` | All | One `gml:MultiSurface`, of one or more pieces | Yes |

A piece is `gml:surfaceMember`, `gml:Surface`, `gml:patches`, `gml:PolygonPatch`. It holds one `gml:exterior` and then any `gml:interior`, each a `gml:LinearRing` with one `gml:posList`: easting and northing in turn, with a space between.

| Of the outlines | TQ | TL |
|---|---|---|
| Sites in more than one piece | 1,121 | 575 |
| Most pieces in one site | 33 | 21 |
| Sites with a hole | 445 | 196 |
| Holes | 738 | 299 |
| Points in a ring, at the median and at most | 9 and 369 | 9 and 719 |
| A ring that is not closed, or of under 4 points | None | None |
| An outline that is not a valid shape | None | None |

### What a way in holds

| Element | Holds | Read |
|---|---|---|
| `gml:id`, on the feature | An identifier | No |
| `ogsp:accessType` | Who it is for. One of three, under the code list `AccessTypeValue` | Yes |
| `ogsp:refToGreenspaceSite` | The `gml:id` of its site. Every one is the id of a site of the same file | Yes |
| `ogsp:geometry` | One `gml:Point` with one `gml:pos` | Yes |

| `accessType` | Both files |
|---|---|
| `Pedestrian` | 54,149 |
| `Motor Vehicle And Pedestrian` | 12,939 |
| `Motor Vehicle` | 115 |

- Every way in stands on the edge of its own site, to the centimetre.
- 4,331 sites have no way in, counted over both files. Most are tennis courts, sports grounds and play spaces, which are often drawn inside another site.

### The ten kinds of site

Counted over both files, each site once. A hectare is what the outline encloses, less its holes.

| `function` | Sites | Of 2 hectares or more | Of 20 or more | With no way in on foot |
|---|---|---|---|---|
| `Allotments Or Community Growing Spaces` | 2,615 | 347 | 0 | 117 |
| `Bowling Green` | 889 | 2 | 0 | 77 |
| `Cemetery` | 921 | 289 | 11 | 30 |
| `Golf Course` | 515 | 502 | 394 | 16 |
| `Other Sports Facility` | 3,554 | 813 | 37 | 1,226 |
| `Play Space` | 9,459 | 10 | 0 | 653 |
| `Playing Field` | 3,667 | 1,902 | 31 | 101 |
| `Public Park Or Garden` | 4,647 | 1,477 | 312 | 51 |
| `Religious Grounds` | 3,427 | 34 | 0 | 10 |
| `Tennis Court` | 2,267 | 5 | 0 | 2,055 |

**The file names the kinds and defines none of them.** Neither the document, the licence nor the note says what makes a site a park, or who may go into a site of any kind. Nobody has read the publisher's page of definitions. So what counts rests on the names:

| Question | Answer | From what |
|---|---|---|
| Which kind is a park | `Public Park Or Garden` | It is the one kind the publisher names a park |
| Which kinds are public green space | `Public Park Or Garden`, alone | It is the one kind the publisher names as public. The file does not say who may go into any other |
| Does a cemetery or a golf course count | No | The design says neither ever counts |
| Is there a kind for a common, a heath, a wood or a forest | No | The ten kinds. One counts only where the publisher maps it as a public park or garden |

### How a missing value is written

| | |
|---|---|
| A value that does not apply | The element is left out. Most sites have no name |
| An element that is read and is empty | None was found |
| A site with no kind, or with no outline | None |
| A way in with no site, no kind or no point | None |
| A site with no way in | 4,331. It is not a fault of the file: the publisher marks no way in |

The parser stops at a site with no kind or no outline, and at a way in with no site, no kind or no point, and names the element. It never gives a site a kind, and never gives a park a way in that the file does not mark.

### London

London is the 4,994 LSOAs of the spine, as their generalised boundaries draw them.

| | |
|---|---|
| The boundaries of London's LSOAs run | From 503,574 to 561,957 east, and from 155,851 to 200,934 north |
| The centres of London's output areas run | From 504,154 to 559,254 east, and from 157,194 to 199,948 north |
| So London lies | On TQ, but for a strip at its northern edge, under a kilometre deep, which is on TL. No centre of an output area is on TL |
| An output area nearer to a square that was not read than to a park | None of 26,369 |
| An LSOA that lies on a square that was not read | None of 4,994 |
| Sites that touch London | 11,204 |
| Of them, parks | 1,941: 629 of 2 hectares or more, and 139 of 20 or more |
| Parks that touch London and have no way in on foot | 14: 6 of 2 hectares or more, and 2 of 20 or more |
| Output areas whose centre stands inside a park | 117 |
| Figures that rest on the file of TL as well as that of TQ | 4 of green cover, 5 of the nearest park and 9 of the nearest large park, of 1,002 each |

- **Both files are needed, and TL for little.** The list asked whether TL holds any site of London. It does, at the northern edge. Without it, the areas there would have no figure that is known.
- **Sites lie over one another.** A play space, a tennis court or a bowling green is often drawn inside a park: over London, 1,016 pairs of a play space and a park share land. 11 pairs of parks share land, 95 hectares in all. So land is counted once, whatever lies over it.
- **A park may be drawn as several sites.** Over both files, 225 parks touch another park, in 101 groups. Taken as one park each, 55 more sites would be part of a park of 2 hectares, and 66 more of a park of 20. The measures take a site as the publisher draws it.

### Names, for the check of commons

The plan asks that 20 named commons, heaths and forests are looked for in this file before a park measure ships. That check needs a list of names, which is the founder's. What was counted for it, once, by a short program that is not kept and that asked the gate first: of the sites that touch London, how many have a name that holds a word, by kind. No name is on this page.

| A name that holds | Sites that are a `Public Park Or Garden` | Sites of another kind |
|---|---|---|
| Common | 38 | 7 |
| Heath | 7 | 10 |
| Forest | 3 | 9 |
| Wood | 9 | 15 |
| Park | 449 | 159 |

- 3,352 of the 11,204 sites that touch London have a name. Of the 629 parks of 2 hectares or more, 528 have one.
- So commons and heaths are in the file, as parks. Whether the 20 that a Londoner would name are among them is not known.

### What a parser must know

- **A file is held to its square.** The two letters of the file's name stand for a square of the National Grid, by the grid's own lettering. The parser works the square out from the letters, and stops if a way in is not on it or a site does not touch it. That is what lets a build say that a home is covered.
- **A site is in two files where it lies across a line.** Keep it once.
- **The year in the document is the year of the copyright.** It is held to the year of the receipt. The document holds no month and no edition: the edition is in the address the file was fetched from, and in the list.
- **A kind that is not one of the ten stops the step.** A new kind may be a common or a wood, and a person must decide whether it counts.
- **A name is never read.** No figure needs one. The registry holds the source for `display` too, but the name field has not been checked by anybody.
- **The document is large when unpacked, and is walked, not loaded.** 54 MB for TQ. Both files are read in under 3 seconds.

### What the file does not say

| Not said | What follows |
|---|---|
| What makes a site a park, or a site of any kind | The measures count the one kind that is named a park, and say so |
| Who may go into a site, and when | Nothing that Burro writes says that a site is open |
| Which month the data is of | The period is the receipt's: `2026-04`, from the list |
| Whether a way in is a gate, a path or a gap in a fence | It is called a way in, and no more |
| Whether a site with no way in can be entered | A park with no way in on foot is not counted as a park that a home is near |
| A total of any kind: no count of sites, no hectares | There is no figure of the publisher's to hold a sum to. The park land of 4,994 LSOAs is held to the park land of London measured as one outline, which is a check of the arithmetic and not of the file |

### Is it a measure of a place

It is. A site is land and a way in is a point on its edge. No element of the document describes who lives anywhere or who uses a site. The weight behind a figure is the count of households of an output area, which describes nobody.

### What core holds for it

| Measure | Core's feature | What was built | In a release |
|---|---|---|---|
| Park land as a share of the land of an area | `green_cover`, "Public green space as a share of the area" | The figure, under core's name. It counts public parks and gardens alone, and its sentence says so | It can be carried |
| The distance to the nearest park of 2 hectares or more | `park_proximity`, "Walk to the nearest park of 2 ha or more" | The figure, as a straight line, under a name that says so | No. Its name is not core's, so a build leaves it out by the rule `measure_is_as_core_says` |
| The distance to the nearest park of 20 hectares or more | None. The design names it `park_large_proximity` | The figure and its evidence, under the design's name | No. It has no row of the catalogue |
| The walk to the nearest play space | `play_space_proximity` | Nothing | |

Neither measure is in the list of measures of a build, `derive/measures.py`. Each is called as the measures of that list are, and gives the same things back.

### What was made from it, and where

Nothing made from the files is in a tracked file, but for the counts on this page and the counts and three figures of each measure in `packages/pipeline/tests/derive/test_green_on_the_real_files.py`. The figure of every area, with its row of evidence, was written to a scratch folder that git does not hold.

### Credit

Contains OS data © Crown copyright and database right 2026.

The words are the registry's. The licence inside each zip says "Contains Ordnance Survey data © Crown copyright and database right 2026". The registry asks that the licence file is saved to `registry/evidence/` at first ingest. It was not saved: nothing made from a publisher's file is committed by a build, and whether this one is, is the founder's to say.

The boundaries of LSOAs and the centres of output areas are the statistics office's. Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

## OS Open Roads: main roads

`oproad_gpkg_gb.zip`. It is the road network of Great Britain, as one GeoPackage inside a zip.

| | |
|---|---|
| Registry id | `os-open-roads` |
| File id | `f-908c0eda3a1b` |
| Bytes | 1,016,021,285 as a zip. The GeoPackage inside is 2,144,063,488 |
| Kind | Zip of one GeoPackage |
| Receipt | Yes. Edition `2026-04`, period `2026-04`, fetched on 2026-09-23 for the list `m2-places`, item `os-open-roads`, for the use `scoring`. It says `geography: null` and names no member, as every receipt does |
| Rows are keyed by | `line`: one line for each stretch of road, read from the column `geometry` |
| Read by | `derive/road_major_exposure.py` |

### The zip

| Member | Bytes | What it is |
|---|---|---|
| `Data/oproad_gb.gpkg` | 2,144,063,488 | The GeoPackage |
| `Doc/licence.txt` | 284 | The publisher's notice of the licence, with the words of its credit. Windows-1252 |
| `Doc/readme.txt` | 502 | Says that the data is under `data` and the notes under `doc`. It says nothing of the data |

`describe` takes each of the two notes for a table of one column. They are text.

### The GeoPackage

An SQLite file, of GeoPackage version 1.2. It names the National Grid as EPSG 27700, and every layer is on it.

| Layer | Geometry | Rows | Last changed, as `gpkg_contents` says | Read |
|---|---|---|---|---|
| `road_link` | `LINESTRING`, in two dimensions | 3,961,077 | 2026-04-07 | Yes |
| `road_node` | `POINT` | 3,346,499 | 2026-04-07 | No |
| `motorway_junction` | `POINT` | 669 | 2026-04-07 | No |

- `gpkg_contents` gives the box each layer covers. For `road_link` it runs from 9,123 to 655,563 east and from 8,046 to 1,216,649 north, which is Great Britain.
- `gpkg_ogr_contents` gives the count of rows of each layer. Each is the count of the layer itself.
- **The file has an index of where each row lies**, which `gpkg_extensions` names as `gpkg_rtree_index`. For `road_link` it is the table `rtree_road_link_geometry`, of 3,961,077 rows: one for each road. It holds the box each line fits in, as numbers of 32 bits, so a box is up to 0.1 m wider than its line.
- The day a layer was last changed is the only date in the file. It falls in the month the receipt gives as the edition.

### The columns of `road_link`

| Column | Type | Holds | Read |
|---|---|---|---|
| `fid` | `INTEGER` | The row's number, from 1 | Only to join the index to the layer |
| `geometry` | `LINESTRING` | The line of the road | Yes |
| `id` | `TEXT` | The publisher's id of the stretch. Each is there once | No |
| `fictitious` | `BOOLEAN` | `0` in every row | Yes. A row with `1` stops the build |
| `road_classification` | `TEXT` | One of seven classes. Never empty | Yes |
| `road_function` | `TEXT` | One of eight functions. Never empty | No |
| `form_of_way` | `TEXT` | One of seven forms. Never empty | No |
| `road_classification_number` | `TEXT` | The number of a road that has one | No |
| `name_1`, `name_2` | `TEXT` | The name of the road, and a second name | No |
| `name_1_lang`, `name_2_lang` | `TEXT` | The language of a name, where it is Welsh or Gaelic, and of the second where it is English | No |
| `road_structure` | `TEXT` | `Road In Tunnel`, or empty | Yes |
| `length` | `REAL` | How long the stretch is, in whole metres. From 1 to 19,190 | Yes, to hold the lines to |
| `length_uom` | `TEXT` | `m` in every row | No |
| `loop` | `BOOLEAN` | `1` for 25,052 rows | No |
| `primary_route` | `BOOLEAN` | `1` for 110,494 rows | No |
| `trunk_road` | `BOOLEAN` | `1` for 37,388 rows | No |
| `start_node`, `end_node` | `TEXT` | The ids of the nodes at each end | No |
| `road_number_toid`, `road_name_toid` | `TEXT` | The publisher's ids of the numbered road and of the named road | No |

No column describes who lives anywhere. The names and numbers of roads are left unread because the measure needs neither.

### How the file classes a road

Counted over Great Britain, and over the roads that were read: those whose line comes within 250 metres of the box London's centres of output areas stand in. That box is wider than London, and takes in roads of the counties round it.

| `road_classification` | Great Britain | Read | Is a main road |
|---|---|---|---|
| `Motorway` | 7,208 | 454 | Yes |
| `A Road` | 291,483 | 29,533 | Yes |
| `B Road` | 164,344 | 8,731 | No |
| `Classified Unnumbered` | 352,203 | 11,877 | No |
| `Unclassified` | 1,852,327 | 139,038 | No |
| `Not Classified` | 405,159 | 21,778 | No |
| `Unknown` | 888,353 | 43,244 | No |
| All | 3,961,077 | 254,655 | |

| `road_function` | Great Britain |
|---|---|
| `Local Road` | 1,735,717 |
| `Restricted Local Access Road` | 887,188 |
| `Minor Road` | 692,656 |
| `A Road` | 291,483 |
| `B Road` | 164,344 |
| `Secondary Access Road` | 134,534 |
| `Local Access Road` | 47,947 |
| `Motorway` | 7,208 |

| `form_of_way` | Great Britain | Of the main roads read |
|---|---|---|
| `Single Carriageway` | 3,811,710 | 20,845 |
| `Collapsed Dual Carriageway` | 57,432 | 5,504 |
| `Roundabout` | 56,738 | 1,734 |
| `Slip Road` | 21,384 | 1,286 |
| `Dual Carriageway` | 10,387 | 618 |
| `Shared Use Carriageway` | 3,272 | None |
| `Guided Busway` | 154 | None |

| `road_structure` | Great Britain | Of the main roads read |
|---|---|---|
| Empty | 3,960,539 | 29,940 |
| `Road In Tunnel` | 538 | 47: 44 of an A road, 3 of a motorway |

- **A road's function says the same as its class, for the roads that matter here.** Every row of class `Motorway`, `A Road` or `B Road` has the function of the same name, and no other row has one of those functions. So no main road is hidden under `Unknown` or `Not Classified`, as far as the file can say.
- A motorway that is numbered as an A road, as `A1(M)`, is of class `Motorway`: 795 rows of Great Britain.
- The file holds no structure but a tunnel. A bridge and a flyover are not marked.

### How a missing value is written

| Column | Where nothing is known |
|---|---|
| `road_classification` | It is never empty. The publisher writes `Unknown`, or `Not Classified`, which are classes of their own |
| `road_structure` | Empty, as an SQL null, in all but 538 rows. It means no tunnel |
| `road_classification_number`, `road_number_toid` | Null in 3,498,042 rows: every road that is no motorway, A road or B road |
| `name_1`, `road_name_toid` | Null in 1,380,477 rows |
| `name_1_lang`, `name_2_lang` | Null in all but 13,127 rows |
| `geometry`, `id`, `length`, `road_function`, `form_of_way`, `start_node`, `end_node` | Never null |

The number and the first name of a road were counted for an empty string, and neither holds one. Nothing is written as a dash or as nought where it is not known.

### The lines

| | |
|---|---|
| How a line is held | The standard's own bytes: the letters `GP`, a version of 0, flags of 3, the code 27700, the box the line fits in as four numbers, then well-known binary, little-endian, of type 2 |
| Dimensions | Two. No line has a height |
| A line that is null or empty | None |
| Points in a line, of the roads read | 2 to 104. 1,281,778 in all |
| A coordinate | In metres, to at most 2 decimal places |
| What the line follows | The file does not say. Where a road has two carriageways the form `Collapsed Dual Carriageway` says that one line stands for both |

**The lines are as long as the file says.** The file gives the length of each stretch in whole metres. For each of the 254,655 roads read, the line as drawn is within 1 metre of it. Together the roads read are 23,378,205 metres by the file and 23,379,608 as drawn, which differ by 6 in 100,000. It is the one figure of the publisher's in the file that a line can be held to, and the parser holds the lines to it.

### What a parser must know

- **The GeoPackage must be unpacked to be read.** SQLite reads a file and not a member of a zip. It is unpacked to the step's own folder, and removed once read. That needs 2.1 GB of disk for some seconds.
- **The read takes seconds, so no extract was made.** Timed once, with the file lately read: 1 second to copy the zip and check its hash, 4 to unpack it, 3 to count the layer, read London's roads by the index and parse their lines, and 1 to measure. About 9 seconds in all. Without the index every one of the 3,961,077 rows is read and parsed.
- **Read by the index, then hold each line to the box.** The box of the index is a little wider than the line. A road kept by the index alone, and not by its line, would make the count of roads read turn on whether there is an index.
- **Hold the index to the layer.** The index has a row for a road only where the road has a line. A road with no line is in no index, and would never be seen. The file has none.
- **A class that is not one of the seven stops the build.** If the publisher renamed `A Road`, every area would otherwise read nought, and nought would be a gap read as a figure.
- **Nothing in the file says which edition it is but the day a layer was last changed.** The list the file was fetched by warns that a later edition arrives at the same address. So the parser holds that day to the month of the receipt.
- The file gives no count of homes, no area code and no boundary. A road is placed by its line alone.

### What the file does not say

| Not said | What follows |
|---|---|
| How much traffic a road carries | The measure counts by class. A quiet A road counts, and a busy road of a lower class does not |
| How wide a road is, or where its kerb is | The distance is to the line, and not to the edge of the road |
| What `fictitious` means | No row has it, and no note in the zip explains it. A row that has it stops the build until a person has read the publisher's own account |
| Whether a road is raised, sunk or screened | Only a tunnel is marked |
| The day the survey was made | The edition is a month. The file gives the day its layers were written |
| What a footpath, a cycle track or an alley is | The file holds roads. The walks of a later build will read too long through a park |

### Core holds no measure of it

The design calls the measure `road_major_exposure`: the share of homes within 100 metres of an A road or a motorway. Core's list of features holds no such id. So the measure is worked out and is in no release. `derive/road_major_exposure.py` is not among the measures of a build, and a test fails when core gains the feature.

### What was made from it, and where

Nothing made from the file is in a tracked file, but for the counts on this page and the counts and three figures in `packages/pipeline/tests/derive/test_road_major_exposure_on_the_real_files.py`. The figure of every area, with its row of evidence, was written to a scratch folder that git does not hold.

### Credit

Contains OS data © Crown copyright and database right [year].

The words are the registry's, for `os-open-roads`. The registry marks them as not yet verified, and asks that the licence file inside the zip be saved and compared with them. `Doc/licence.txt` was read for this page and was not saved. Its words differ a little: "Contains OS data © Crown Copyright and database rights 2026." So the file itself gives the year as 2026. Which words are shown is the founder's to settle.

The centres of output areas are the statistics office's. Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

## OS Open Rivers: water close by

**What has changed since this section was written.** Added on 2026-09-24, after two checks of the second build. Water close by is in the list of the measures of a build, `derive/measures.py`: it is worked out at every build, and left out of the release. Its name is now "Share of homes within 300 m, in a straight line, of the centre line of a river, canal or lake". A check counted what this section says in words: beside wide tidal water a home on the bank reads as away from water, and an area can read high from a long straight stretch that may run under the ground. So the measure is not carried, whatever core names it, until the bank is settled. What follows is as it was written.

`oprvrs_gpkg_gb.zip`. It is the rivers, canals and lakes of Great Britain as lines, as one GeoPackage inside a zip.

| | |
|---|---|
| Registry id | `os-open-rivers` |
| File id | `f-b31e85f9fd41` |
| Bytes | 52,490,978 as a zip. The GeoPackage inside is 118,403,072 |
| Kind | Zip of one GeoPackage |
| Receipt | Yes. Edition `2026-04`, period `2026-04`, fetched on 2026-09-23 for the list `m2-places`, item `os-open-rivers`, for the use `scoring`. It says `geography: null` and names no member, as every receipt does |
| Rows are keyed by | `line`: one line for each stretch of water, read from the column `geometry` |
| Read by | `derive/water_access.py` |

### The zip

| Member | Bytes | What it is |
|---|---|---|
| `Data/oprvrs_gb.gpkg` | 118,403,072 | The GeoPackage |
| `Doc/licence.txt` | 286 | The publisher's notice of the licence, with the words of its credit. Windows-1252 |
| `Doc/readme.txt` | 502 | Says that the data is under `data` and the notes under `doc`. It says nothing of the data |

`describe` takes each of the two notes for a table of one column. They are text. No note in the zip says what a column or a form means.

### The GeoPackage

An SQLite file, of GeoPackage version 1.2. It names the National Grid as EPSG 27700, and both layers are on it.

| Layer | Geometry | Rows | Last changed, as `gpkg_contents` says | Read |
|---|---|---|---|---|
| `watercourse_link` | `LINESTRING`, in two dimensions | 193,040 | 2026-04-14 | Yes |
| `hydro_node` | `POINT` | 197,734 | 2026-04-14 | No |

- `gpkg_contents` gives the box each layer covers. For `watercourse_link` it runs from 64,394 to 655,208 east and from 13,275 to 1,216,428 north, which is Great Britain.
- `gpkg_ogr_contents` gives the count of rows of each layer. Each is the count of the layer itself.
- **The file has an index of where each row lies**, which `gpkg_extensions` names as `gpkg_rtree_index`. For `watercourse_link` it is the table `rtree_watercourse_link_geometry`, of 193,040 rows: one for each stretch.
- The file holds the two tables a GeoPackage keeps for tiles. Both are empty.
- The day a layer was last changed is the only date in the file. It falls in the month the receipt gives as the edition.

### The columns of `watercourse_link`

| Column | Type | Holds | Read |
|---|---|---|---|
| `fid` | `INTEGER` | The row's number, from 1 | Only to join the index to the layer |
| `geometry` | `LINESTRING` | The line of the stretch | Yes |
| `id` | `TEXT` | The publisher's id of the stretch. Each is there once | No |
| `flow_direction` | `TEXT` | `in direction` in 192,992 rows, `in opposite direction` in 3, empty in 45 | No |
| `length` | `REAL` | How long the stretch is, in whole metres. From 1 to 41,462 | Yes, to hold the lines to |
| `fictitious` | `TEXT` | The text `0` in every row | Yes. A row with anything else stops the build |
| `form` | `TEXT` | One of four forms. Never empty | Yes |
| `watercourse_name` | `TEXT` | The name of the water, where it has one | No |
| `watercourse_name_alternative` | `TEXT` | A second name. Only a row with a first name has one | No |
| `start_node`, `end_node` | `TEXT` | The ids of the nodes at each end | No |

`hydro_node` has four columns: `fid`, `geometry`, `id` and `hydro_node_category`, which is `source` in 70,867 rows, `junction` in 66,739, `outlet` in 5,680 and empty in 54,448. None is read.

No column describes who lives anywhere. The names of rivers are left unread because the measure needs none, and a release shows none.

### How the file says what kind of water a stretch is

By the column `form`, and by nothing else. Counted over Great Britain, and over the stretches that were read: those whose line comes within 10,000 metres of the box London's centres of output areas stand in. That box is wider than London, and takes in water of the counties round it.

| `form` | Great Britain | Kilometres, as the file gives them | With a name | Read | Read, with a name | Counts as water |
|---|---|---|---|---|---|---|
| `inlandRiver` | 155,779 | 138,346 | 90,753 | 2,065 | 1,212 | Yes |
| `lake` | 24,146 | 5,721 | 6,042 | 438 | 112 | Yes |
| `tidalRiver` | 11,539 | 5,738 | 7,653 | 176 | 139 | Yes |
| `canal` | 1,576 | 2,721 | 1,457 | 68 | 66 | Yes |
| All | 193,040 | 152,527 | 105,905 | 2,747 | 1,529 | |

- **The file names the forms and defines none of them.** No page of the publisher was opened. So what each form is rests on its name alone.
- **A lake is a line and not an outline.** The layer holds a stretch of form `lake` where a line of the network runs through a lake. The file holds no outline of any water, so a lake, a pond, a dock or a reservoir that no line is drawn through is not in the file.
- **No column marks a culvert, a pipe or a tunnel.** `fictitious` is the one column that could mark a stretch that is not there as drawn, and it is `0` in every row. So the file cannot tell water in the open from water under the ground.
- **No column gives the size of a stream.** A brook and a ditch are both `inlandRiver`. 45 in 100 rows have no name, and a name is no class. Leaving out the water with no name was tried once, and changed the figure of 75 of the 1,002 areas. What the water with no name is, the file does not say, so it is counted.
- The 45 rows with no `flow_direction` are all of form `tidalRiver`.

### How a missing value is written

| Column | Where nothing is known |
|---|---|
| `watercourse_name` | Empty, as an SQL null, in 87,135 rows |
| `watercourse_name_alternative` | Null in 187,705 rows |
| `flow_direction` | Null in 45 rows |
| `hydro_node_category` | Null in 54,448 rows |
| `geometry`, `id`, `length`, `fictitious`, `form`, `start_node`, `end_node` | Never null |

No column holds an empty string. Nothing is written as a dash or as nought where it is not known.

### The lines

| | |
|---|---|
| How a line is held | The standard's own bytes: the letters `GP`, a version of 0, flags of 3, the code 27700, the box the line fits in as four numbers, then well-known binary, little-endian, of type 2 |
| Dimensions | Two. No line has a height |
| A line that is null or empty | None |
| Points in a line | 2 or more. 2,137,230 in all of Great Britain, and 29,908 in the stretches read. 44,536 stretches of Great Britain are drawn with two points alone |
| A coordinate | In metres, to at most 2 decimal places |
| A width | None. The file does not say how wide any water is, or where its bank is |
| What the line follows | The file does not say. The licence registry records, from the publisher's page, that the product is a network of centre lines |

**The lines are as long as the file says.** The file gives the length of each stretch in whole metres. For every one of the 193,040 rows the line as drawn is within 1 metre of it. The stretches read are 2,505,993 metres by the file and 2,505,985 as drawn. It is the one figure of the publisher's in the file that a line can be held to, and the parser holds the lines to it.

**Some stretches are drawn as one long straight line.** The stretches read are drawn in 27,161 straight parts, of 65 metres at the median. 185 parts are 500 metres or longer, and 33 are a kilometre or longer. The longest is 3,342 metres. Of the 185, 122 are of form `inlandRiver`, 29 `canal`, 29 `tidalRiver` and 5 `lake`. Together they are 148 of the 2,506 kilometres read. The file does not say what they are. A canal may run straight, and so may a river in a pipe. None is left out.

### How far a line is from the edge of the water

Tried once, by a short program that is not kept, for tidal water alone. The boundaries of LSOAs are cut at mean high water, so tidal water is where no LSOA is. The lines of form `tidalRiver` that were read run for 124 kilometres, 104 of them where no LSOA is. Along those, the line is 96 metres from the nearest land at the median, over 150 metres for a third of its length, and 591 metres at most. So a distance to the line is shorter than the distance to the bank by up to that much, and a measure that counts homes within 300 metres of the line leaves out homes that stand nearer than that to the water's edge. How many is for the report of the build, and is in no tracked file.

### What a parser must know

- **The GeoPackage must be unpacked to be read.** SQLite reads a file and not a member of a zip. It is unpacked to the step's own folder, and removed once read. That needs 118 MB of disk for a moment.
- **The read takes about 2 seconds, so no extract was made.** Timed once, with the file lately read, from the copy to the figure of every area. Without the index every one of the 193,040 rows is read and parsed, which took about 2 seconds more.
- **Read by the index, then hold each line to the box**, as the roads are read. `line_of` in `derive/road_major_exposure.py` reads a line of either file: the publisher holds both the same way.
- **`fictitious` is text here and a number in the roads.** The roads hold `0` as a number. This file holds the text `0`. The parser takes either, and stops at anything else.
- **A form that is not one of the four stops the build.** If the publisher renamed a form, its water would otherwise be counted as none.
- **Nothing in the file says which edition it is but the day a layer was last changed.** So the parser holds that day to the month of the receipt.
- **Look for water well beyond the distance that is asked about.** Every centre of an output area of London has a line within 6,671 metres, and half have one within 834. The parser reads 10,000 metres round the homes of a build, and stops a build where more than 1 in 100 centres have no line that near.
- The file gives no count of homes, no area code and no boundary. A stretch is placed by its line alone.

### What the file does not say

| Not said | What follows |
|---|---|
| Whether a stretch runs in the open or under the ground | The measure cannot leave out a culvert, and says so beside the figure |
| How wide the water is, or where its bank is | The distance is to the line. Beside wide water the figure is too low |
| What each form means | The reading rests on the four names |
| What `fictitious` means | No row has it, and no note in the zip explains it. A row that has it stops the build until a person has read the publisher's own account |
| Whether a stream is a river or a ditch | Every stretch counts, named or not |
| Where a lake, a pond, a dock or a reservoir is that no line runs through | It is not in the file, and is not counted |
| Whether a person can reach the water, or see it | The measure claims neither. The registry asks that the product is never used to claim a view or a frontage |
| The day the survey was made | The edition is a month. The file gives the day its layers were written |

### Is it a measure of a place

Yes. The file holds lines of water and nothing of who lives anywhere. The homes are households at the census, used as a weight and as nothing else.

### Core names it a share of the area

Core's catalogue holds the feature `water_access`, as "Share of the area within 300 m of a river or canal". The pipeline design asks for the share of homes, which is what `homes_within` works out and what `derive/water_access.py` makes. The two are different figures. So the row of the catalogue that is made carries a label of its own, "Share of homes within 300 m of a river, canal or lake", and the measure is in no release until core says the same. It is not among the measures of a build, and a test fails on the day core's label changes.

### What was made from it, and where

Nothing made from the file is in a tracked file, but for the counts on this page and the counts and three figures in `packages/pipeline/tests/derive/test_water_access_on_the_real_files.py`. The figure of every area, with its row of evidence, was written to a scratch folder that git does not hold. Each figure was worked out a second time with the geometry library, by a short program that is not kept, and the two agree for every area.

### Credit

Contains OS data © Crown copyright and database right 2026.

The words are the registry's, for `os-open-rivers`. The registry marks them as not yet verified, and asks that the licence file inside the zip be saved at first ingest. `Doc/licence.txt` was read for this page and was not saved: a builder commits nothing made from a publisher's file. Its words differ a little: "Contains OS data © Crown Copyright and database rights 2026." Which words are shown, and the saving of the file, are the founder's to settle.

The homes and the centres of output areas are the statistics office's. Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].
