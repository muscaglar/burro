# The postcode lookup, and what it places

Status: counted on 2026-09-24, from the ONS Postcode Directory of August 2026 as it stood in the store that day. It is a dated snapshot. A later edition is another file, and this page does not describe it.

No person has checked anything on this page. Every count was made by a program.

On the same day the counts were made a second time, by a program written apart from the first: the rows of London, by mark and by borough, whether each postcode is in an area of the build, how far apart postcodes stand, what the rule at the edge of London leaves out, and what the lookup would place of the food register. Each came out the same, and the two lookups gave the same answer for every one of the 332,885 postcodes. The two trials in which a place or a home is moved were run a second time as they were written, and were not written a second time.

It holds counts for London as a whole and for boroughs. It holds no postcode, no point, no name of a business, a surgery or a pharmacy, and no figure of a neighbourhood.

## In short

| | |
|---|---|
| What is built on the real file | The lookup: `packages/pipeline/src/burro_pipeline/cells/postcodes.py` |
| What is built on made-up files with the real columns | The straight-line distance to the nearest GP practice and to the nearest pharmacy: `derive/gp_walk.py` and `derive/pharmacy_walk.py`. Both files have been fetched since. The report of practices has its receipt, and the step stops at it: see "What the first file of practices holds". The pharmacy list is stored with no receipt, because its period is not sure |
| London's postcodes in use | 180,965 |
| Of those, in an area of the build | 180,964. One stands in an output area that is outside London |
| What the lookup would place today | 1,869 of the 1,918 places to eat and drink that the food register gives a postcode and no point |
| To what place a distance is honest | The nearest 100 metres. The ten is not known |

## What the licence registry asks, and how each is kept

| The entry `ons-postcode-directory` says | How it is kept | The test that holds it |
|---|---|---|
| All three credits are required | `credits_of` gives the three, with the year of the data. The row of the catalogue of each measure names the directory as a source | `test_the_three_credits_carry_the_year_of_the_data`, and the same of each measure |
| Drop every row of Northern Ireland at ingest | The file of its postcode area is never opened. A line of any other file that begins as one of its postcodes does is dropped before it is split into columns | `test_the_file_of_northern_ireland_is_never_opened` on the made-up zip, and `test_the_file_of_northern_ireland_was_never_opened` on the real one |
| Keep London's authorities alone | A row is kept only where its local authority is a London borough or the City | `test_a_row_of_another_authority_is_not_kept` |
| Never pass the national file on | Nothing is written. What is kept is held in memory for the length of a build | `test_the_module_writes_nothing` |
| A row at the level of a postcode is never shown, exported or committed | What the lookup gives back holds a point and the codes of areas, and no postcode. It cannot be asked for its postcodes | `test_the_lookup_gives_out_no_postcode` |
| Save the licence section of the guide | It was saved when the file was taken in: `registry/evidence/ons-postcode-directory-2026-09-24.txt` | |

Five columns of the directory say something of who lives in an area. None is read. Nine columns are read, by name: the postcode, the month it ended, the local authority, the easting and the northing, the mark of how good the point is, and the output area, the LSOA and the MSOA of the census of 2021.

## How a postcode is read

Every space is taken out and every letter is made a capital. What is left must have the shape of a postcode. So a postcode is found with its space or without it, and in any case. Nothing is corrected: a letter typed for a digit is not found.

**A postcode that has ended** is in the directory with the month it ended, and is kept. The guide inside the zip says that such a postcode keeps its point, and that its areas are brought up to date at each edition. A register of businesses is older than the directory, so a place may give a postcode that has since ended. It is placed where its postcode last stood. What is given back says that it has ended, and when. It is never counted as in use.

Every one of London's 151,920 postcodes that have ended stands in an area of the build. 105,048 of them have a point that is measured to. 46,872 have a point that is the middle of a sector or was kept from before November 2000, and a place at one of those is placed nowhere.

A postcode that was ended and then given out again is in the directory at its new place alone. The guide says so. Nothing tells such a postcode from any other.

## What the directory holds of London

| | Rows |
|---|---|
| Files of a postcode area in the zip | 124 |
| Files that were opened | 123: every one but Northern Ireland's |
| Rows read, of every authority | 2,665,796 |
| Lines of Northern Ireland in a file of another area | 0 |
| Rows of London | 332,885 |
| In use | 180,965 |
| Ended | 151,920 |
| Postcode areas that hold a row of London | 22. Three of them hold under 1,000 each |

How good the point is, by the publisher's own mark:

| Mark | What the guide says it is | In use | Ended |
|---|---|---|---|
| 1 | Within the building of the matched address closest to the postcode mean | 180,447 | 95,863 |
| 3 | Approximate to within 50 metres | 5 | 327 |
| 4 | The mean of the matched addresses, not moved to a building | 0 | 34 |
| 5 | Imputed by the statistics office, by reference to the postcodes round it | 385 | 8,824 |
| 6 | The mean of the postcode sector, mainly for PO boxes | 128 | 12,644 |
| 8 | Ended before November 2000, with the last point known for it | 0 | 34,228 |

A place is measured to where the mark is 1 to 5. A point of mark 6 is the middle of a sector, which holds thousands of addresses. The guide says a point of mark 8 is mainly to the nearest 100 metres in England and Wales. Each is a place on the map, and neither is measured to.

No row of London has no point. The directory gives a postcode with no point no local authority, so such a postcode is never a row of London, and is not found.

## Whether every postcode is in an area of the build

The build has 1,002 areas, made of 26,369 output areas.

| | Postcodes | Of them in use |
|---|---|---|
| In an output area that is in no area of the build | 1 | 1 |
| In another borough than the build puts its output area in | 42 | 7 |
| In an output area that the directory puts in another LSOA or MSOA than the build does | 0 | 0 |

So 180,964 of the 180,965 postcodes in use are in an area of the build. The one that is not has a point that stands in a London borough of today and in an output area of 2021 that is outside London.

The directory puts a point in the local authority it stands in today. An output area of 2021 may lie across the border of two. So 42 postcodes stand in one borough while the build puts their output area in another. The area of each is still known, because an area is made of output areas. The lookup gives the borough the directory gives.

Two rows stand in an output area of the build and in a local authority outside London. Neither is kept, because the registry keeps London's authorities alone. One is in use. A place at it is not found.

15 output areas of the build hold no postcode in use.

## What it places today: the food register

The measure of places to eat and drink is on another branch. Its reader never reads a postcode, and a business with no point is counted nowhere. These counts were made apart from it, from the 33 files of the register in the store, for the three kinds that measure counts. Of a business with no point, the postcode was looked up and was not kept.

| | All three kinds | Places to eat | Pubs and bars | Takeaways |
|---|---|---|---|---|
| Listed | 40,558 | 27,262 | 3,866 | 9,430 |
| With a point | 37,013 | 24,671 | 3,565 | 8,777 |
| With no point | 3,545 | 2,591 | 301 | 653 |
| Of those, with a postcode | 1,918 | 1,332 | 273 | 313 |
| Of those, with no postcode | 1,627 | 1,259 | 28 | 340 |

Of the 1,918 with a postcode and no point:

| What the lookup makes of it | All three kinds | Places to eat | Pubs and bars | Takeaways |
|---|---|---|---|---|
| Placed | 1,869 | 1,299 | 268 | 302 |
| Of those, at a postcode that has ended | 119 | 90 | 9 | 20 |
| Its point is the middle of a sector, or was kept from before November 2000 | 10 | 6 | 2 | 2 |
| Its postcode is no row of London | 30 | 22 | 3 | 5 |
| What is written has not the shape of a postcode | 9 | 5 | 0 | 4 |

So the places with a point would rise from 37,013 to 38,882 of 40,558: from 91 in 100 to 96. Nothing places the 1,627 that have no postcode.

By the borough the point of the postcode stands in:

| Borough | Places it would add | Of them pubs and bars | Of them at an ended postcode | Postcodes in use |
|---|---|---|---|---|
| Westminster | 173 | 11 | 21 | 13,063 |
| Camden | 169 | 4 | 25 | 8,189 |
| Richmond upon Thames | 157 | 25 | 3 | 4,390 |
| Hackney | 155 | 21 | 1 | 4,564 |
| Islington | 144 | 39 | 5 | 6,411 |
| Wandsworth | 141 | 15 | 8 | 6,320 |
| Bromley | 106 | 54 | 6 | 7,210 |
| Tower Hamlets | 102 | 11 | 9 | 5,933 |
| Waltham Forest | 76 | 22 | 3 | 3,831 |
| Merton | 65 | 5 | 2 | 3,690 |
| Lewisham | 62 | 6 | 4 | 4,987 |
| Ealing | 43 | 5 | 3 | 6,585 |
| Hillingdon | 43 | 5 | 3 | 6,167 |
| Harrow | 41 | 5 | 2 | 4,947 |
| Newham | 39 | 2 | 1 | 4,391 |
| Hounslow | 35 | 2 | 2 | 4,931 |
| City of London | 34 | 3 | 3 | 1,561 |
| Lambeth | 31 | 3 | 1 | 6,166 |
| Southwark | 31 | 2 | 3 | 7,235 |
| Greenwich | 27 | 4 | 1 | 5,238 |
| Haringey | 26 | 1 | 0 | 4,507 |
| Kingston upon Thames | 21 | 5 | 0 | 3,509 |
| Brent | 20 | 0 | 4 | 5,916 |
| Enfield | 20 | 6 | 0 | 6,272 |
| Barking and Dagenham | 18 | 2 | 3 | 3,069 |
| Bexley | 16 | 4 | 0 | 4,406 |
| Croydon | 13 | 1 | 0 | 7,052 |
| Hammersmith and Fulham | 13 | 2 | 1 | 3,677 |
| Barnet | 12 | 1 | 0 | 8,923 |
| Kensington and Chelsea | 11 | 0 | 1 | 4,332 |
| Sutton | 10 | 1 | 2 | 3,835 |
| Havering | 8 | 1 | 1 | 5,040 |
| Redbridge | 7 | 0 | 1 | 4,618 |
| London | 1,869 | 268 | 119 | 180,965 |

The borough is the one the point stands in, which is not always the council that listed the business.

### How the lookup would be given to that measure

Nothing of it is copied here. These are the changes, in the order they would be made, in `derive/food_register.py` and `derive/venue_food_drink.py` as they stand on that branch.

1. **Read the postcode of a business that has no point, and of no other.** `PostCode` is in `LEFT`, the elements whose text is never kept. It would move to the elements that are kept for the length of one business. In the file the postcode stands before the point, so it cannot be known, when the postcode is met, whether the business has a point. The walk would keep it until the business ends, and drop it there where a point was found.
2. **Turn it into a point inside the reader.** `food_register.build` would take the lookup beside the inputs. Where a business has no point and the lookup places its postcode with a point that is good for a distance, the reader makes a `Place` of it. The lookup gives a point on the National Grid and a `Place` holds a longitude and a latitude, so the point goes through `longitude_and_latitude` in `cells/shapes.py`, the pipeline's one fixed operation. The postcode is dropped as soon as it is looked up. So nothing leaves the reader but a kind, an authority and a point, as now.
3. **Count what was placed so.** `Extract` holds, by kind, how many businesses were listed and how many had a point. It would hold a third count: how many were placed by postcode.
4. **Name the directory behind every figure.** `at_homes` would ask `postcodes.build(inputs)` before it reads the register, and add the file of the directory to `behind`. Every row of evidence then rests on it, and the row of the catalogue names it as a source, so that its three credits stand wherever the figure does.
5. **Keep the reader's memory apart.** `_read` remembers what it made of a file. With a lookup in hand, what it makes of a file depends on the lookup too, so the lookup would be part of what it remembers by.
6. **Say what changed beside the figure.** `NO_POINT` says a business with no point is counted nowhere. It would say that a business with no point and no postcode is. `OF_THE_REGISTER` says the directory has no receipt. It has one.

One thing is the founder's to say first. The head of `food_register.py` gives the reason a postcode is never read: an address may be a home. The registry entry for the register does not forbid reading a postcode. It forbids showing or exporting a row.

## Doctors and pharmacies

The store holds two files of NHS England's Organisation Data Service, under the entry `nhs-ods`. They are of trusts and hospital sites, and the entry allows them for destination search alone. Neither is read here.

Two entries were added to the registry on 2026-09-24, each on the licence its publisher's own pages state. Every page was read through a reader that extracts the text of a page, at least twice, in different words. An extraction is not the page, and no person has seen one.

| | GP practices | Pharmacies |
|---|---|---|
| Registry id | `nhs-ods-gp-practices` | `nhsbsa-consolidated-pharmaceutical-list` |
| Publisher | NHS England | NHS Business Services Authority |
| The file | The predefined report `epraccur` | Consolidated Pharmaceutical List, 2026-27 Quarter 1 |
| Licence | Open Government Licence. The page of the service says "ODS data is published under Open Government Licence and is therefore available for all to use" | Open Government Licence 3.0, shown on the dataset's page and on the page of the file |
| What it covers | England and Wales | England |
| How often | The page says the source data updates nightly | Quarterly |
| A row of names | None, by the specification. 27 columns | Yes. 25 fields |
| Read | The postcode, the close date, the status and the prescribing setting: columns 10, 12, 13 and 26 | `POST_CODE` and `CONTRACT_TYPE` |
| Never read | The name, the address and the telephone number: a practice is often named for a doctor | `ORGANISATION_NAME`, which is the name of whoever is on the list and may be the name of one person, the trading name and the address |
| What counts | Active, with no close date, and of the setting `RO76`, which the specification gives as a GP practice | A contract type of Community or LPS. An appliance contractor, DAC, does not count |
| List, and item | `m10-health`, `gp-practices` | `m10-health`, `pharmacy-list-2026-27-q1` |

The address of each file is in the list and in the registry entry, as it was read.

### What the first file of practices holds

The report was fetched on 2026-09-24 and has its receipt, `f-13acc2be00fb`, of 3,316,877 bytes. It was read through the gate and its receipt, for the three columns the step holds it to. No name, no address and no postcode was read.

| Of the file | It holds |
|---|---|
| Lines | 15,651, each of 27 columns. No row of names |
| The status, column 13 | `ACTIVE` in 12,591 lines, `INACTIVE` in 2,808, `DORMANT` in 252. None says closed or proposed |
| The close date, column 12 | 8 digits in 2,808 lines, and empty in the rest. Every line that says `INACTIVE` holds one, and no line that says `ACTIVE` does |
| The prescribing setting, column 26 | `RO76` alone in 8,187 lines. Two roles with a bar between them in 27: `RO76` with another in 6, and two others in 21. Empty in one line |
| Lines of the setting `RO76` alone | 6,558 active with no close date, 1,568 inactive, 61 dormant |

So the step stops at the file, twice over: it names no `INACTIVE`, and it holds a cell to one role. Both are small to put right, and each is a choice. `INACTIVE` reads as what the specification calls closed. Whether a practice with a second role is counted is for whoever puts the step right to say, with the founder. Until then no figure is made from the file.

What was not known until a file was opened, and what still is not:

| Of | What is not known |
|---|---|
| The report of practices | How a status is spelled in full, and whether in capitals. The specification says "A (Active), C (Closed), D (Dormant) or P (Proposed)" were once letters, and that "the status name/description is provided in full" now. The step reads a status in any case, and stops at one that is none of the four. Known now: in capitals, as above |
| The report of practices | How a date is written. The two reports of the same service that are in the store write one as 8 digits. Known now: as 8 digits |
| The pharmacy list | How the file is encoded, and whether a contract type is written as the page writes it |
| The pharmacy list | What day the list is as at. The page of the file gives the day it was made as 29 July 2026 |
| Both | How many places are in London, and how many of their postcodes the lookup places |

Branch surgeries are not read. The publisher gives them in a report of their own. One reading of its specification said that the kind also marks vaccination sites run by primary care networks, and that the report has no column for a status. The registry entry does not cover it.

The pharmacy list has no field that says a pharmacy serves by post alone and takes no callers. Such a pharmacy is counted as any other. Fifteen of its fields are the hours a pharmacy is open. None is read.

### What is built, and on what

Both measures are built and tested on made-up files that are laid out as the publisher's pages say the real ones are. Nothing here is a figure of London. Each was worked out for no area of London, because no file of either was in the store. So none of the 1,002 areas has a figure, and nothing is put in its place.

| | GP practice | Pharmacy |
|---|---|---|
| Built on | A made-up file with the real columns | A made-up file with the real columns |
| Areas with a figure | None | None |
| Lowest, middle and highest | Not known | Not known |
| Rank correlation with homes per hectare | Not known | Not known |
| Rank correlation with distance from the centre | Not known | Not known |

How a figure is made, once a file is there:

1. Each place that counts is looked up by its postcode, and put at the point the directory gives.
2. For each output area, the distance in a straight line from its centre to the nearest place.
3. An output area has a distance only where no home outside London is taken to stand nearer than the nearest place that was found. The lookup places nothing outside London, so a nearer place may stand there.
4. An area's figure is the median of those distances over its homes, given to the nearest 100 metres. Below half the homes covered no figure is given.

It is a straight line, and not a walk. The name of each measure says so.

### What core needs

Core names each measure a walk, in minutes, on a network of streets. What is built is a straight line, in metres, from a point. So the row of the catalogue that each measure writes is not core's. A build would leave the measure out by the rule `input_has_one_receipt` while its file has no receipt, and by `measure_is_as_core_says` after. Nothing in core was changed. For a build to carry either, core would say, in `packages/core/src/burro_core/catalogue.py`:

| Of | Core says now | It would say |
|---|---|---|
| `gp_walk`, the label | Walk to the nearest GP surgery | Straight-line distance to the nearest GP practice, placed by its postcode |
| `pharmacy_walk`, the label | Walk to the nearest pharmacy | Straight-line distance to the nearest pharmacy, placed by its postcode |
| Both, the unit | `min` | `m` |
| Both, what the figure is measured on | A network | A point |
| Both, the figure at which a distance is never a trade-off | 10, in minutes | A figure in metres. The distance to a park has 800 |

The id of each feature keeps the word walk, as an id never moves.

Neither measure is on the list of the measures of a build, `MEASURES` in `derive/measures.py`. A test of each makes the line that puts it there, and calls the measure as the list does.

## A point for a postcode is not a door

The guide inside the zip says what the point is: "the mean of all the addresses in the postcode, snapped to the address closest to the mean". So it is a door of the postcode. It is not the door of any one place in it.

**How much ground a postcode stands for.** 180,965 postcodes in use stand on 166,402 points. 18,797 stand on a point that another shares. From the point of one postcode to the nearest other point:

| Share of points | No further than |
|---|---|
| A quarter | 29 metres |
| Half | 40 metres |
| Three quarters | 55 metres |
| 9 in 10 | 74 metres |
| 99 in 100 | 129 metres |

So a door is mostly within a few tens of metres of the point its place is put at.

**Where homes are taken to stand moves a distance more.** A figure is measured from the centre of each output area. From a postcode in use to the centre of its own output area:

| Share of postcodes | No further than |
|---|---|
| A quarter | 45 metres |
| Half | 78 metres |
| Three quarters | 125 metres |
| 9 in 10 | 196 metres |
| 99 in 100 | 533 metres |

So of one home, a distance of 300 metres may be 200 or 400. It says which places are near and which are far. It does not say whether a home is 250 or 350 metres from a surgery.

**What it does to the figure of an area.** An area's figure is the median over its homes, which is steadier than the distance of one home. A trial measured how much steadier. It is a trial of the method, on made-up places, and says nothing of any real place.

- A made-up place was put at every hundredth point: 1,665 places. Each of the 1,002 areas was given its figure. The edge of London was not looked at.
- Each place was then moved to a spot drawn evenly from the disc round its point that reaches to the nearest other point, which is the ground of its own postcode. Each area was given its figure again.

| | |
|---|---|
| An area's figure moved by, at the middle | 11 metres |
| 9 areas in 10 moved by under | 30 metres |
| Figures that changed, given to the nearest metre | 978 of 1,002 |
| Figures that changed, given to the nearest 10 metres | 767 of 1,002 |
| Figures that changed, given to the nearest 100 metres | 151 of 1,002 |

`tests/derive/test_nearest_by_postcode_on_the_real_files.py` holds this run. Two more runs, drawn otherwise, and three with a place at every 130th point, gave much the same: 747 to 790 figures changed at 10 metres, and 127 to 147 at 100. No test holds those five.

No test holds the second trial, which follows. It left the places where they were and moved the homes of each output area from its centre to the point of one of its own postcodes. An area's figure moved by 18 to 20 metres at the middle, and by under 53 for 9 areas in 10. Given to the nearest 10 metres, 835 and 869 of 1,002 figures changed. Given to the nearest 100, 217 and 233 did.

**So a figure is honest to the hundred metres.** Given to the nearest 10 metres, three figures in four rest on which door of a postcode a place was put at. Given to the nearest 100, one in seven does, and those are the figures that stand near the middle between two hundreds. In core's unit, a walk of 100 metres is a little over a minute, so a figure in minutes is honest to the whole minute and to no decimal place.

The two measures built here give a figure to the nearest 100 metres. The distance to a park is given to the nearest 10. The second trial says the last digit of that figure is not known either. It is for whoever owns that measure to weigh.

A figure given to 100 metres puts the areas on few steps: in the first trial 997 figures stood on 15. Whether an area is ranked on a finer figure than is shown is the founder's to say.

**What the rule at the edge of London costs.** The lookup places nothing outside London. So an output area has a distance only where no home outside London is taken to stand nearer than the nearest place that was found. With the made-up places of the first trial, 230 of the 26,369 output areas were left out, which hold 29,588 of London's 3,423,767 homes: under 1 in 100. Of the 1,002 areas, 955 had a figure that rests on every home, 42 a figure that rests on fewer, and 5 had none. With a place at every 130th point, 320 output areas were left out and 9 areas had no figure. Real surgeries and pharmacies do not stand as evenly as postcodes do, so the real cost may be more. The test on the real files holds the first of the two.

## What stands behind each figure on this page

| Figures | The file, its edition and its period | The columns that were read | How, in one sentence | Held by |
|---|---|---|---|---|
| The rows of London, in use and ended, by mark and by borough | ONS Postcode Directory, the zip of August 2026, period 2026-08, file `f-ab51f1e82bd5` | `pcds`, `doterm`, `lad26cd`, `east1m`, `north1m`, `gridind`, `oa21cd`, `lsoa21cd`, `msoa21cd` | Every row of the file of each postcode area but Northern Ireland's is read, and a row is counted where its local authority is a London borough or the City | `tests/cells/test_postcodes_on_the_real_files.py` |
| Whether a postcode is in an area of the build | The directory, and the lookup of output areas, edition V2, period 2022-12 | The nine above, and the codes of the lookup | The output area of each postcode is looked for among the output areas of the build | The same |
| How far apart postcodes stand | The directory | `east1m`, `north1m`, `doterm` | For each point a postcode in use stands on, the distance to the nearest other such point | `tests/derive/test_nearest_by_postcode_on_the_real_files.py` |
| How far a postcode stands from the centre of its output area | The directory, and the centres of output areas, edition V4, period 2021-12 | The nine above, and the point of each output area | For each postcode in use, the distance from its point to the centre of its own output area | The same |
| The trial | The directory, the centres, the lookup, and the census table of homes, period 2021-03-21 | As above, and the count of homes of each output area | The median over an area's homes of the distance to the nearest made-up place, before and after each place is moved | The same, for the first run |
| What the lookup would place of the food register | The 33 files of the food hygiene register, each an extract of a day from 2026-09-09 to 2026-09-16, and the directory | Of a business: `BusinessTypeID`, `LocalAuthorityCode`, `Geocode`, and `PostCode` where it has no point | Each business of the three kinds that has no point and a postcode is looked up, and counted by what the lookup makes of it | No test. The reader of the register is on another branch, and reads no postcode |

What the counts cannot see: whether a point the directory gives is where a business is, whether a business that is listed still trades, and why the register gives a business no point.

## What the measures cannot see

| Of | What it cannot see |
|---|---|
| Both | A walk. It is a straight line, so a railway, a river or a main road in between makes the real walk longer |
| Both | Where in its postcode a place stands |
| Both | A place outside London. Near the edge of London the homes that have homes outside London nearer than the nearest place found are left out |
| Both | A place whose postcode is no row of London, or has a point that is not measured to |
| GP practice | A branch surgery. Whether a practice takes new patients. When it is open |
| Pharmacy | Whether a pharmacy serves by post alone. When it is open. Whether it is on the list still: the list is made once a quarter |

## For the founder

| # | What is to be decided or seen |
|---|---|
| 1 | Two registry entries were marked approved, on pages read through a reader that extracts. Each lists under `before_launch` what a person has still to see. Say whether each stands |
| 2 | The plan, in section 4, lists GP access as out of the first version. The design of the London data recommends that the two walks come in. Say which stands |
| 3 | An approved entry may be fetched under the approval of 23 September. Neither file was fetched. Say whether each is to be |
| 4 | The registry keeps London's rows of the postcode directory alone. So a surgery or a pharmacy outside London is placed nowhere, and the homes near the edge of London have no distance. Say whether the rows of the districts that border London may be kept |
| 5 | The reader of the food register never reads a postcode, because an address may be a home. Reading the postcode of a business that has no point would place 1,869 more places to eat and drink. Say whether it may |
| 6 | Say whether a place at a postcode that has ended is counted. Here it is, and it is counted apart: 119 of the 1,869 |
| 7 | Say whether a figure that is given to the nearest 100 metres may be ranked on a finer figure than is shown |
| 8 | Set `attribution_verified` for the postcode directory if the guide is accepted as the publisher's own wording |

## Credit

| File | Credit |
|---|---|
| Postcode directory | Contains OS data © Crown copyright and database right 2026. Contains Royal Mail data © Royal Mail copyright and database right 2026. Source: Office for National Statistics licensed under the Open Government Licence v.3.0 |
| Food hygiene register | Contains public sector information licensed under the Open Government Licence v3.0 |
| GP practices, once fetched | Contains information from NHS England, licenced under the current version of the Open Government Licence |
| Pharmacies, once fetched | Contains public sector information licensed under the Open Government Licence v3.0 |
