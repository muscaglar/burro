# Land use, for works and warehouses, gardens and woodland

Researched and built on 2026-09-24. A dated snapshot, not a source of truth. Nothing here is legal advice. No lawyer has read it.

**The table has its receipt, and its figures have been read.** They were first worked out on 2026-09-24, by a program, through the licence gate. They were worked out again the same day by a second reader, written apart from the step, and the two agree: section 4. No person has opened the workbook, and no person has held a figure against a map. What is said of its layout was first read in it with the step `describe`, which gives each row of a sheet that holds words alone and never a row that holds a number. What the code does was tried on made-up files, laid out as the workbook is, and then on the table itself. No figure here is said of a named neighbourhood. A figure is said of London or of a borough.

**In one line: Leafy reads broadly as London does, and Works and warehouses does not yet.** Leafy puts the outer boroughs at the top and the centre at the bottom, but it reads the most rural edge of London as not leafy, because farmland, golf courses and heath count for nothing. Where a public park is a wood, woodland and public parks count the same land, and two of the three areas that score highest on Leafy are such places. Works and warehouses finds the right places at the very top, but a fifth of London is in its highest band, that band begins at 0.7 in 100 of an area's land, and an area with 4.2 in 100 stands in the band below it. Section 5 has both.

## 0. In short

| Question | Answer |
|---|---|
| Is there a source | Yes. Land use statistics: England 2022, from the Department for Levelling Up, Housing and Communities |
| At what geography | By LSOA, in Live Table P405. It is not a borough's figure: London's spine holds 4,994 LSOAs in 33 boroughs |
| What period is shown beside a figure | 2022. The title of each sheet of the workbook ends ", 2022", and the workbook says no more of its date. Section 2 |
| Which edition is the latest | 2022, published on 27 October 2022. No later edition is on the collection page or in the publisher's own search. The publisher plans figures for 2024 to 2026 by the end of 2026, made another way and under other classes of land. Section 1 |
| Under what licence | Open Government Licence v3.0, as the release page, the statistical release and the technical notes each state |
| What is it in the registry | `mhclg-land-use-statistics-2022`, approved for scoring and display, with one thing to settle before launch |
| What is to fetch | Nothing. The one file of the list `m10-land-use` is in the store with its receipt, `f-b8db326abd8b`, of 38,142,392 bytes |
| What is built | Five measures, each a share of an area's land: industry, storage and warehousing, transport other than roads, gardens, woodland. And beside each, for comparing, the mean of the area's shares by homes, which joins no build |
| Does a build carry them | A build that names the list `m10-land-use` carries four of the five, with a figure for each of 1,002 areas. A build that does not name the list carries none, by the rule `input_has_one_receipt` |
| What such a build places | Leafy on all of its recipe, and Works and warehouses on 75 in 100 of it. Section 4 |
| Does Leafy read as London does | Broadly. Its rank correlation with distance from the centre is 0.49, and with homes per hectare -0.56, so it is more than a map of either. It reads wrong at the rural edge and in Wandsworth. Section 5 |
| Does Works and warehouses | At the top, yes. As five bands, no. Section 5 |
| Do two parts of Leafy count the same land | Gardens and public parks: none that the figures can show. Woodland and public parks: yes, where a public park is a wood. It is at least 177 hectares and at most 2,723, and it lies under areas that score highest. Section 4 |
| What differs from the catalogue | One name. Core calls transport other than roads "depots, yards and other transport". Its publisher puts depots and yards under storage |
| How much of Gritty can be worked out today | 65 in 100 of the recipe core held on 2026-09-24, of which a build carries 50. An area is placed at 60. Section 7 |

## 1. The source

| What | As the publisher's pages give it | How it was read |
|---|---|---|
| Name | Land use statistics: England 2022 | S |
| Publisher | Department for Levelling Up, Housing and Communities. The collection page names the Ministry of Housing, Communities and Local Government beside it | S |
| Published | 27 October 2022. Not updated since | S |
| What it holds | "Land uses are classified across 28 land use categories, aggregated into 13 different groups and split between developed and non-developed land use types" | S |
| As at | "As at April 2022", in the statistical release. The technical notes say the dates of the products behind the figures were "chosen to centre around April 2021" | S, P |
| Made from | "Data is provided to the Department by Ordnance Survey Ltd and is derived from Ordnance Survey's AddressBase, Open Greenspace and Mastermap Topography products" | S |
| Geography | National, regional and local authority in Live Tables P400 to P403. Parliamentary constituency in P404. "Lower layer super output area (LSOA) level (Live Table P405)" | S |
| Standing | Official statistics. "These land use statistics are estimates" | P |
| Licence | "All content is available under the Open Government Licence v3.0, except where otherwise stated", on the release page. "This publication is licensed under the terms of the Open Government Licence v3.0 except where otherwise stated", in the statistical release. "You may re-use this information (not including logos) free of charge in any format or medium, under the terms of the Open Government Licence", in the technical notes | S, S, P |
| Editions | 2017, 2018, 2019, 2020, 2021 and 2022. The editions for 2019 to 2021 were published on 24 August 2023, after 2022 | S |
| The next edition | The release of 2022 gives no date: "We are currently considering the best timing and frequency for future editions". A consultation the publisher opened on 16 September 2026 gives one. See "What the publisher plans" below | S |

How each was read:

| Code | Meaning |
|---|---|
| S | Through a reader that extracts the text of a page. It was asked twice of each page, in different words, and what is kept is what it gave both times |
| P | The technical notes are a PDF of 18 pages. Its text was pulled out by a short script and read in full |

### The files on the release page

| File | Format | Size | Taken |
|---|---|---|---|
| Land use statistics: England 2022 - live tables by LSOA and MSOA | ODS | 36.4 MB | Yes. It is the one file of the list |
| Land use statistics: England 2022 - live tables | ODS | 2.32 MB | No. It holds no figure below a local authority or a constituency |
| Land use and Land use change statistics - technical notes | PDF | 357 KB, 18 pages | Read as a document. It is no file of data |
| Land use statistics: England 2022 - factsheet | PDF | 248 KB, 1 page | No |

The address of each is on the release page, written whole. The address of the file that is taken is in the registry entry, under `file_urls`, and in the list.

### The 28 categories

From the technical notes. A measure is made from a category, in the third column. It is never made from a group.

| Group | Category | Code | What the notes say it holds, in short |
|---|---|---|---|
| Community services | Community buildings | C | Health, educational, community and religious buildings, police and fire stations, prisons |
| Community services | Leisure (indoor) | L | Museums, cinemas, theatres, sports halls |
| Defence buildings | Defence buildings | D | Buildings only. Ranges and airfields are not picked out |
| Industry and commerce | **Industry** | I | "Works, refineries, shipbuilding yards, mills and other industrial sites". Those of a public utility are under Utilities |
| Industry and commerce | Offices | J | Government offices, banks, other offices |
| Industry and commerce | Retail | K | "Shops, garages, public houses, restaurants, post offices" |
| Industry and commerce | **Storage and warehousing** | S | "Depots, scrap and timber yards, warehousing" |
| Minerals and landfill | Minerals and mining | M | Surface mineral workings |
| Minerals and landfill | Landfill and waste disposal | Y | Rubbish tips. Waste transfer stations are under Utilities |
| Other developed use | Unidentified building | ~B | |
| Other developed use | Unidentified general manmade surface | ~M | Hard standing, usually a car park |
| Other developed use | Unidentified structure | ~S | |
| Other developed use | Unknown surface type with no classification | ~U | |
| Residential | Communal accommodation | Q | Hotels, hostels, care homes |
| Residential | Residential | R | Houses and flats, to the footprint on the ground |
| Transport and utilities | Highways and roads | H | Through roads, bus stations, public car parks |
| Transport and utilities | **Transport (other)** | T | "Non-highway transport routes and places, e.g. railways, airports and dockland, including all installations within the perimeter of the establishment" |
| Transport and utilities | Utilities | U | Post and telecommunications, gas, electricity, sewage, cemeteries and crematoria |
| Agriculture | Agricultural land | A | |
| Agriculture | Agricultural buildings | B | |
| Forestry, open land and water | **Forestry and woodland** | F | "Areas marked with woodland annotations on the OS map including woodland on farm holdings and woodland used for recreation" |
| Forestry, open land and water | Rough grassland | G | |
| Forestry, open land and water | Natural land | N | |
| Forestry, open land and water | Water | W | Lakes, canals, reservoirs. Canals and rivers are here, and not under transport |
| Outdoor recreation | Outdoor recreation | O | Playing fields, golf courses, country parks, allotments |
| Residential gardens | **Residential gardens** | RG | "Residential gardens of any type, regardless of surface" |
| Undeveloped land | Undeveloped land | X | Land in built-up areas that was never developed |
| Vacant land | Vacant land | V | Cleared sites. The notes say it cannot be said whether it was developed |

### The land that is never a measure

Three of the 28 categories say something of who lives on the land.

| Category | Code | What the notes say it holds |
|---|---|---|
| Communal accommodation | Q | "hotels, hostels, old people's homes, children's homes, monasteries and convents" |
| Community buildings | C | "Health, educational, community and religious buildings and police stations, prisons, fire stations" |
| Defence buildings | D | Buildings such as "barracks and administration offices" |

Each is read, because all the land of an LSOA is its 28 categories added up. None is ever a measure. `measures_of` in `land_use.py` refuses one, and the registry entry says so. Community buildings hold schools and surgeries too, and those are of a place. They are one figure with the rest, so the whole category is kept out.

### What the publisher plans

From the consultation "Land use statistics in England: methodology changes", which the Ministry of Housing, Communities and Local Government opened on 16 September 2026 and closes on 28 October 2026. It was read twice, in different words, and what is kept is what both readings gave.

| What | As the consultation gives it |
|---|---|
| The latest edition | Land use in England was "Last published for 2022" |
| When publication resumes | "We plan to resume publication of the land use statistics this year (2026), with the first tranche of releases covering the years 2024 to 2026" |
| The timetable | Land use stock for 2024, 2025 and 2026 "By end of 2026". Each later release "Annual, in October each year" |
| What it is made from | The figures up to 2022 were made from data Ordnance Survey prepared from MasterMap and AddressBase. The new series is to rest on Ordnance Survey's National Geographic Database |
| The classes of land | "We propose to publish the statistics using OS's own land classification rather than the 28 LUCS categories used in the legacy series" |
| Whether the two compare | "The new statistics will represent a break in the time series as represented by the legacy statistics from 2013 to 2022" |
| Geography | "by local authority, and at neighbourhood level (MSOA and LSOA, land use stock release only)" |
| Licence | "licensed under the terms of the Open Government Licence v3.0" |

What follows for Burro:

- The table of 2022 is the latest there is. It describes land as it was in April 2022 or April 2021, and section 2 says why the month is not yet sure.
- A table for 2024 to 2026 is planned by the end of 2026. It is a proposal under consultation, so its date, its classes and its layout may change.
- The step written here reads the 28 categories of 2022. It will not read a table under other classes, and must not be made to. The new table is another source, with an entry, a list and a step of its own.
- Industry, storage, gardens and woodland may not be classes of the new table under those names. Whether a recipe can be carried over is not known until the classes are published.
- Whether to build on 2022 now, or to wait, is question 6 of section 9.

## 2. What is in the registry, and in the list

| Thing | Value |
|---|---|
| Entry | `mhclg-land-use-statistics-2022`, in `registry/sources/environment.toml` |
| Status | `approved`, for `scoring` and `display` |
| Why approved | Three of the publisher's own documents state the licence, and the licence allows commercial use. Each was opened on 2026-09-24 |
| To settle before launch | A person opens the workbook once. The pages state the licence "except where otherwise stated". A program read every row of the workbook that holds words alone, and found no statement of rights and no term of use. `registry/evidence/mhclg-land-use-statistics-2022-2026-09-24.md` holds what it read |
| Attribution | The licence's own wording, for a provider that states none. Not verified: no page read states one |
| List | `m10-land-use`, one item, `land-use-lsoa-2022` |
| What `plan` says of it | `status=ok`, and `ready=1`. The gate allows the file, and the list states its edition and its period |
| The receipt | `data/receipts/mhclg-land-use-statistics-2022/f-b8db326abd8b.json`. It is the copy the store holds beside the file, byte for byte |
| What the gate refuses | The national tables of the same page, the same file on another host, a page the entry does not hold, and any use but scoring and display. Each was tried |

How the period was settled. The release says April 2022. The technical notes, which cover land use and land use change together, say the dates of the products "centre around April 2021". The workbook says neither. The title of each of its two sheets, in row 1 and column A, ends ", 2022", and nothing else in it states a date. So the list states the period as the year 2022, and a figure is shown as of 2022, with no month. The list no longer names `data_period` under `unsure`.

## 3. What the workbook holds, and what the code does about each

Read on 2026-09-24 with `python -m burro_pipeline describe`, and with `--sheet` for each sheet. It gives the names of the sheets, how many rows hold something, and each row that holds words alone. It gives no row that holds a number.

| What | As the workbook has it | What the code does |
|---|---|---|
| The sheets | Two: `P404a` and `P404b`. Their titles call them Table 405a and Table 405b. No cover, no contents and no sheet of notes | Is told no name of a sheet. It looks in every sheet |
| The unit | Row 3, column AW: "Per cent" in the first sheet, "Hectares" in the second | Takes the sheet that holds "Hectares" alone in a cell above the names of its columns. It stops where none does, and where two do |
| The sheet of per cent | Its column of industry holds a share as a part of one, where every other column holds it in 100. It is so in all 20,302 rows of England that hold any industry, and the 28 shares of such a row add up to less than 100. The sheet of hectares does not share the fault: each row of London adds up to its grand total, and London's rows add up to 157,342 hectares against 157,334 inside their outlines. Storage, gardens, woodland and transport are the same in both sheets | Never reads the sheet of per cent. A step that did would give industry a hundred times too small |
| The rows that name the columns | Rows 4 to 6. Row 4 names developed use, non-developed use, vacant and the grand total. Row 5 names 12 of the 13 groups, each over the column of its total, and the totals of developed and of non-developed use. The thirteenth group, vacant, is named in row 4. Row 6 names the categories, and calls the last column of each group "Total" | Takes the first row, among the first 30 of a sheet, that names all 28 categories and the grand total |
| A group of one category | Defence, outdoor recreation, residential gardens, undeveloped land and vacant have one column each. Row 6 calls it "Total", and row 5 or row 4 names the group over it | Reads each of the five from the column that row 6 calls a total and a row above names for the group. No group of several categories is ever read so |
| How a category is spelt | As the technical notes spell it, but for two: "Institutional and communal accommo-dations", and "Unknown" | Takes each spelling of the notes, and these two |
| The columns beside the figures | LSOA code, LSOA name, MSOA code, MSOA name, and the MSOA's name from the House of Commons Library | Finds the column of codes by the shape of an LSOA's code. No name of a place is kept |
| Columns that hold nothing | Five, between the blocks of columns | Passes over them |
| The rows | 33,772 rows of each sheet hold something. Seven hold words alone: the title, the unit, the three rows of names and two notes. The rest hold figures: a row for England, a row for each region, and a row for each LSOA | Reads the rows that hold the code of an LSOA, and counts the rest |
| Which census the codes follow | The first note under each table: the data is "mapped to lower layer super output (LSOA) 2021 boundaries at the mean high tide mark" | Holds the table to the spine, which is of 2021, and stops where an LSOA of London has no row |
| Whether the count of rows fits that census | It does. 33,772 rows less the 7 of words is 33,765. The lookup of the statistics office holds 33,755 LSOAs of England at the census of 2021. That leaves 10: a row for England and one for each of 9 regions. No row of figures was read to count this | Nothing. A test on the real table holds the rows under the names to 33,767, which is the 33,765 and the two notes |
| The publisher's own total | The second note: "The grand total column is the sum of all the land use categories" | Adds up the 28 categories, and holds each row to its grand total. The grand total is part of no figure |
| Rows for an MSOA | None. The MSOA of an LSOA is a column of its row | Adds up the LSOAs of an area |
| A row for London | One, among the rows of the regions | No step reads it. A test on the real table holds what London's LSOAs add up to, to it |
| A dash in a cell of figures | Some cells hold "-" where a figure would stand. The workbook does not say what it stands for, and no page read says | Reads a dash as none of that land, and only where the figures of its row add up to the row's grand total with every dash taken as nought. A row that does not add up stops the step |
| How a figure that is withheld is written | Not said. No other mark than a dash was seen among the rows of words | Any other text in a cell of figures stops the step |
| Whether an empty cell is nought | Not said | Reads it as unknown. The LSOA adds nothing, and the area's coverage falls |
| Whether the figures are rounded | Not said | Finds the most decimal places any figure holds, and allows each row that much rounding against its total |
| Where the file states its date | The title of each sheet ends ", 2022" | Nothing. The period is the receipt's, which the list states |
| A statement of rights, or a term of use | None | Nothing. The registry entry says what was read |

### What the first reading of the figures counted

On 2026-09-24 the table was read through the gate. The step did not stop. Each of the three things the code expected of the layout was as it expected: the sheet of hectares was found by its unit, each group of one category was read from the column its row of names calls a total, and every dash stood in a row that adds up.

| What | Counted |
|---|---|
| Rows that hold the code of an LSOA | 33,755, which is every LSOA of England at the census of 2021 |
| Other rows under the names | 12: England, 9 regions and the two notes |
| The row of names | Row 6 |
| LSOAs of London with a row | 4,994 of 4,994 |
| LSOAs with an empty cell | None |
| Cells of a category that hold a dash, in the rows of LSOAs | 373,063 of 945,140. In London 68,727 of 139,832, which is 49 in 100 |
| Cells of a category that hold the number nought | None, in all of England |
| How the numbers are written | In full, to 13 to 16 decimal places for most. The table is not rounded |
| The furthest a row of London stands from its own grand total | Under a millionth of a square metre |
| The totals of London's LSOAs over the land the build measures in their outlines | 1.0 at the middle LSOA. 157,342 hectares against 157,334 in all |
| London's LSOAs added up, against the publisher's own row for London | Within the gate of 0.5 in 100, for each of the 28 categories and for all the land |
| Figures that move when each hectare is first kept to four decimal places | 1 of 5,010, by 0.1: a share of storage that stands at 0.65002 as written reads 0.6. Of the mean by homes, 4 of 5,010. The definition of each measure says a figure is kept to the square metre |

So a dash is how the workbook writes nought. No cell holds the number nought, and every row adds up to its grand total with each dash taken as nought. Nothing the publisher wrote says it, and the arithmetic leaves no room for anything else.

## 4. The five measures

Built in `packages/pipeline/src/burro_pipeline/derive/land_use.py`, on a made-up workbook that is laid out as the publisher's is, and then run on the table itself.

| Measure | Category | Its column in the workbook | The figure | Named as core names it |
|---|---|---|---|---|
| `land_industry` | Industry (I) | "Industry", in row 6 | Hectares of the category in the area's LSOAs, over all the hectares of those LSOAs, as a percentage to one decimal place | Yes |
| `land_storage` | Storage and warehousing (S) | "Storage and warehousing", in row 6 | The same | Yes |
| `land_transport_other` | Transport (other) (T) | "Transport (other)", in row 6 | The same | No |
| `land_gardens` | Residential gardens (RG) | "Total", under "Residential gardens" in row 5: a group of one category | The same | Yes |
| `land_woodland` | Forestry and woodland (F) | "Forestry and woodland", in row 6 | The same | Yes |

All the land of an LSOA is its 28 categories added up. The method is `lsoa_ratio_by_homes`: one sum over another, never a mean of shares. An LSOA is in one MSOA, so while an area is an MSOA the figure is the land of the category in the area over all the land of the area.

### The other figure: the mean of shares, by homes

`figures_by_homes` in the same module works out, for each measure, the mean of the shares of an area's LSOAs, weighted by their homes at the census of 2021. It is the figure the design of the vibes asked for. It joins no build. A test on the real table holds London's lowest, middle and highest figure of it.

| | The share of the area's land | The mean of shares, by homes |
|---|---|---|
| What it answers | How much of the area is this kind of land | How much of this kind of land stands where the homes are |
| A large works where nobody lives | Counts for all its land | Counts for little: its LSOA holds few homes |
| A small yard among many homes | Counts for little | Counts for more |
| What core would call it | Measured | Averaged |
| What the homes are as at | It reads no homes, but to share out an LSOA that lies in two areas | 21 March 2021 |

### The five measures on the real table

Each has a figure for all 1,002 areas. A figure is in 100 of an area's land, and is of 2022.

| Measure | London as a whole | Lowest area | Middle area | Highest area | Areas at nought | Boroughs with the most, by their own land | Boroughs with the least |
|---|---|---|---|---|---|---|---|
| Gardens | 24.0 | 0.2 | 27.1 | 65.3 | 0 | Sutton 35.0, Harrow 34.1, Croydon 32.2 | City of London 0.2, Westminster 8.7, Tower Hamlets 10.9 |
| Woodland | 5.4 | 0.0 | 1.3 | 37.9 | 154 | Bromley 10.9, Waltham Forest 8.9, Hillingdon 8.8 | City of London 0.0, Tower Hamlets 0.4, Barking and Dagenham 0.9 |
| Industry | 0.4 | 0.0 | 0.1 | 18.6 | 451 | Barking and Dagenham 3.4, Brent 0.8, Tower Hamlets 0.7 | Islington, Lewisham and Westminster, each under 0.05 |
| Storage and warehousing | 0.5 | 0.0 | 0.0 | 13.2 | 536 | Brent 1.9, Newham 1.9, Hounslow 1.4 | Lambeth, Westminster and the City of London, each under 0.1 |
| Transport other than roads | 2.7 | 0.0 | 1.2 | 52.6 | 220 | Hillingdon 12.5, Hammersmith and Fulham 5.1, Newham 4.7 | Sutton 0.7, Richmond upon Thames 0.8, Bexley 0.8 |

Two things stand out. Industry and storage are thin: together they are 0.9 in 100 of London's land, 1,379 hectares, and 357 areas hold none of either. The table counts the ground a works or a warehouse stands on, and classes the yard round it as unidentified manmade surface, which is 5.4 in 100 of London. And a share is given to one decimal place, so industry takes only 43 different values over 1,002 areas, and storage 56.

How each stands to homes per hectare and to the straight-line distance from the centre of London, as a rank correlation over the 1,002 areas. The centre is the middle of London's homes.

| Measure | With homes per hectare | With distance from the centre |
|---|---|---|
| Gardens | -0.19 | 0.38 |
| Woodland | -0.61 | 0.44 |
| Industry | 0.14 | -0.04 |
| Storage and warehousing | 0.01 | 0.06 |
| Transport other than roads | 0.20 | -0.17 |

### The two ways, set side by side on the real table

| Measure | Rank correlation of the two | By homes less by land, middle area | Furthest below | Furthest above | Areas where they differ by 5 points or more | Boroughs that hold most of the 20 widest gaps |
|---|---|---|---|---|---|---|
| Gardens | 0.94 | +1.0 | -5.2 | +32.9 | 172 | Havering 5, Barking and Dagenham 3, Enfield 3 |
| Woodland | 0.98 | 0.0 | -21.6 | +5.4 | 35 | Greenwich 4, Waltham Forest 4, Hillingdon 3 |
| Industry | 0.96 | 0.0 | -9.5 | +1.7 | 1 | Barking and Dagenham 4 |
| Storage and warehousing | 0.97 | 0.0 | -10.9 | +2.5 | 1 | Newham 4, Greenwich 3 |
| Transport other than roads | 0.98 | 0.0 | -33.1 | +7.1 | 12 | Hillingdon 4, Newham 3 |

Where they differ, and why:

- **Gardens differ most, and at the edge of London.** Where one LSOA of an area holds a great deal of open land, the share of land is pulled down and the mean by homes is not. In the 20 areas with the widest gap the middle area has 12.8 in 100 of its land under agriculture and 12.1 under outdoor recreation. London's middle area has 0.6 and 7.0.
- **Woodland, industry, storage and transport differ in few areas, and the other way.** A large wood, works or airfield stands in one LSOA. The share of land counts all of it. The mean by homes counts it for the homes of that LSOA alone.
- **Which is truer to what a person means.** For gardens, the mean by homes: a person who asks for gardens means the streets where homes are, and a field at the edge of the area takes no garden away. It follows houses more closely, with a rank correlation of -0.67 with the share of homes that are flats, against -0.52 for the share of land. For woodland, the share of land: a person means that a wood is there. For works and warehouses it turns on the words. "Works near homes" is the mean by homes. "An area of works" is the share of land. The two rank London almost alike, so the choice moves few areas.
- **A third way for gardens was worked out and joins no build:** the garden land for each home, in square metres. London's middle area has 94.8. Bromley has 260 and Tower Hamlets 18. It is truest to "a garden", and it is close to homes per hectare turned over, with a rank correlation of -0.86, so it would say little that Homes does not.

The choice is question 3 of section 9.

### Where the catalogue's words differ from what the file holds

| Measure | Core says | The publisher's category holds | What follows |
|---|---|---|---|
| `land_transport_other` | "Land used for depots, yards and other transport". Short: "Depots and yards" | Railways, airports and dockland, with everything inside their perimeter. Depots and yards are under Storage and warehousing | The measure carries a name of its own, "Land used for transport other than roads, such as railways, airports and docks". A build leaves it out until core says the same |
| `land_industry` | "Land used for industry" | Industry, without gas, water and power works, which are utilities | The name holds. What it leaves out is said beside the figure |
| `land_storage` | "Land used for storage and warehousing" | Depots, scrap and timber yards, warehousing. A warehouse inside a dock is under transport | The name holds |
| `land_gardens` | "Land that is residential garden" | Gardens "of any type, regardless of surface", so a paved yard counts | The name holds. The surface is said beside the figure |
| `land_woodland` | "Land that is woodland" | "Forestry and woodland": land the map marks as woodland | The name holds. It counts no tree outside such land |
| Works and warehouses, the vibe | "Land used for industry, storage and transport, near homes" | A share of land says nothing of how near a home is | The words "near homes" are not true of a share of land. They are core's to change |
| Every land use part | The design of the vibes: "the mean share across the area's LSOAs, weighted by their homes" | | The figure built is the share of the area's land, which is what core's names say. Question 3 of section 9 |

Nothing in core was changed.

### What a garden and a wood are, and what Leafy counts twice

From the definitions in the technical notes, read again on 2026-09-24. The workbook defines no category.

| Question | What the notes say | What follows |
|---|---|---|
| Is a garden a private garden | "Residential gardens of any type, regardless of surface". The notes do not say private. They say of homes that "Residential land area is limited to the on the ground footprint", so the land round a home is here and not under Residential | It is the garden of a home, front or back, whether one home has it or the homes of a block share it. It is never a public garden. A paved yard and a drive count |
| Does woodland hold the trees of a park | "Areas marked with woodland annotations on the OS map including woodland on farm holdings and woodland used for recreation" | By this definition a wood inside a park is woodland, and the grass of a park, and a tree that stands alone on it, are not. The notes put playing fields, golf courses, country parks and allotments under Outdoor recreation |
| Is any land in two categories of the table | No. The second note under each table says the grand total is the sum of all the categories | Gardens and woodland never count the same land |
| Is any land in a category and in public parks and gardens too | Public parks and gardens are measured from another file, OS Open Greenspace, as the land inside the outline of a park. That file names the kind `Public Park Or Garden` and defines none of its kinds. The technical notes say the land use table is itself made from Open Greenspace, among other products | Settled from the figures, below |

**Gardens and public parks count no land twice that the figures can show. Woodland and public parks do, where a public park is a wood.** What each publisher says does not settle it alone: the table says a garden is the garden of a home, and the file of parks does not say what a park holds. The figures settle part of it. They were set side by side for each of London's 4,994 LSOAs on 2026-09-24, and then again by a second reading.

The table gives one figure for an LSOA and no outline, so the land that two parts count can only be held between a least and a most. The least is the park land that the rest of the LSOA cannot hold. It turns on what is taken as unable to lie inside a park.

| What was counted | Result |
|---|---|
| LSOAs where the park land and the garden land together are more than all the land | None. So no garden land is forced to lie in a park |
| Park land that must be woodland, if any land but woodland may lie in a park | 35 hectares, in 2 LSOAs |
| The same, if homes and their gardens may not | 90 hectares, in 8 LSOAs |
| The same, if roads and railways may not either | 173 hectares, in 21 LSOAs |
| The same, if works, warehouses, offices, shops, mines, tips, farm buildings and communal homes may not either | 177 hectares, in 23 LSOAs of ten boroughs. London holds 13,354 hectares of public park and 8,441 of woodland |
| The most park land that could be woodland, LSOA by LSOA | 2,723 hectares, which is 32 in 100 of London's woodland |
| The most that could be garden | 6,300 hectares |
| Areas where 2 in 100 of the land or more must be counted by both parts | 13 of 1,002. In 4 of them it is 10 in 100 or more: two in Greenwich and two in Bexley |
| Areas where 2 in 100 of the land or more may be | 157 |
| The four LSOAs with the most park land that must be woodland | Public park is 53 to 67 in 100 of their land, woodland 38 to 55 and outdoor recreation 2 to 14. They are in Greenwich and Bexley |
| The land inside a site of any kind of Open Greenspace, set against the table's outdoor recreation, LSOA by LSOA | Across London they are all but the same land. One fits the other at 1.00 hectare for a hectare, and explains 98 in 100 of it |
| The 21 LSOAs where 70 in 100 of the land or more is public park | Of their 2,963 hectares the table classes 80.0 in 100 as outdoor recreation, 5.3 as gardens and 1.4 as woodland |
| The one LSOA that is most park, at 93 in 100 | The table classes 93.0 in 100 of it as outdoor recreation, and under 1 in 100 as woodland |

So the table does not treat every park alike. In the great parks of grass it classes nearly all the land as outdoor recreation, woods and all. Where a park is itself a wood it classes the land as woodland, as its technical notes say it would, and the file of parks counts the same land as park. It classes no part of a park as a garden. Why the two kinds of park differ is not known. The parks are of April 2026 and the table of 2022, so a wood first mapped as a park after 2022 would be woodland in one and park in the other. Nothing read says so.

What it does to Leafy, tried in no build:

| Leafy with | Areas that change band | Of the ten areas that score highest, how many leave the ten | Of the fifty |
|---|---|---|---|
| Woodland less the land that must be counted twice, 177 hectares | 6 | 2 | 1 |
| Woodland less the most that may be, 2,723 hectares | 299 | 6 | 16 |

The hectares are few and the places are the ones at the top. Of the ten areas that score highest, the second and the third are each a wood that is a public park, in Greenwich and in Bexley: 15 and 22 in 100 of their land is counted by both parts, at the least. Whether a wood that is a public park should count twice is question 12 of section 9.

What follows is the other side of the same finding:

- **In the great parks of grass, a wood counts as park and not as woodland.** Richmond upon Thames has 34.9 in 100 of its land in public parks and 3.0 in woodland. In its 6 LSOAs that are 70 in 100 park or more, the table classes 83.4 in 100 of the land as outdoor recreation and 1.8 as woodland.
- **Outdoor recreation that is no public park counts for nothing.** Golf courses are 2.9 in 100 of London's land and playing fields 2.1. Neither is in any part of Leafy.
- **Land the table calls agricultural counts for nothing.** It is 10.3 in 100 of London, 27 in 100 of Bromley and 28 of Havering. The technical notes give it as open land outside a built-up area with no other class, so in London it holds open grass as well as farms.
- **Cemeteries are not where the technical notes put them.** The notes class them as utilities, which is 436 hectares in all of London. Open Greenspace maps 1,246 hectares of cemetery. In the LSOAs that are mostly cemetery, the land is in one of the three categories that are never a measure. No figure rests on it.

### The step, checked a second way

On 2026-09-24 the step was set against a second reader, written apart from it. The table was made up: a row for each of London's 4,994 LSOAs and for 120 made-up ones outside, laid out column for column as `describe` gave the workbook, with merged cells over the names, a run of dashes written once with a count, and each number shown to fewer places than it holds. The second reader takes each column by its place and never by its name, and works each share out in whole fractions.

| Made-up figures given to | Figures compared | That differ |
|---|---|---|
| Two decimal places | 5,010: five measures of 1,002 areas | None |
| Four decimal places | 5,010 | None |
| Every place a number holds | 5,010 | None, where the second reader keeps a hectare to four places as the step does. One, by 0.1, where it does not |

So the names lead the step to the right columns, and its arithmetic is the plain one. The step keeps each hectare to four decimal places before it adds, which is a square metre. Where a share stands on the edge of a tenth that can move it by 0.1. It is a check of the code and of nothing in the real table.

The same day, once the table had its receipt, the step was set against a second reader on the table itself. The second reader was written apart from the step and shares nothing with it but the gate that opens the file. It walks the sheet another way, takes each column by its place, finds London by the name of each LSOA and not by the lookup, takes the MSOA of an LSOA from the workbook's own column, and works each share out in whole fractions from the numbers as written.

| What was set side by side | Result |
|---|---|
| LSOAs of London, MSOAs and boroughs | 4,994, 1,002 and 33 by both. No LSOA is in another MSOA by the workbook than by the lookup |
| Rows of LSOAs, cells that hold a dash, cells that hold the number nought | 33,755, 373,063 and none, by both |
| Gardens, woodland and industry, as a share of land | 1,002 areas of 1,002 agree, for each |
| Storage and warehousing | 1,001 agree. One differs by 0.1, in Lewisham, where the share as written is 0.65002 and the step keeps each hectare to four places first |
| Transport other than roads, which no build carries | 1,002 agree |
| The mean by homes, which no build carries | 5,006 of 5,010 agree. Four differ by 0.1, each on the edge of a tenth |
| Every figure, both ways, where the second reader keeps a hectare to four places as the step does | 10,020 of 10,020 agree |
| The figures of a preview built from the step | The same as the step's, for the four measures a build carries |

### What a recipe would rest on

| Vibe | Recipe in core | Carried by a build that names the list |
|---|---|---|
| Works and warehouses | 40 industry, 35 storage, 25 transport other than roads | 75 in 100: industry and storage. Transport waits on its name. 60 places an area |
| Leafy | 40 gardens, 30 woodland, 30 public parks and gardens | 100 in 100: 70 from this table, and 30 from public parks and gardens, which a build carries |
| Gritty, as the scale core holds | 20 industry, with recorded crime, main roads, noise and homes per hectare | No real release carries the scale: section 7 |

A preview was built on 2026-09-24 with the lists `m1`, `m2-places`, `m2-living` and `m10-land-use`. It holds 1,002 areas and 12 measures: the eight of the first build, and gardens, woodland, industry and storage. It leaves out transport other than roads and water close by, each by `measure_is_as_core_says`. `burro-release check` accepts it, with no finding. Built twice, with the lists in two orders, it is the same 18 files byte for byte. Core places every area on Homes, Parks close by, Leafy and Works and warehouses. It goes to a folder git ignores.

The test of the first real build, `tests/assemble/test_preview_on_the_real_files.py`, builds on `m1` and `m2-places` and is left as it was. Whether a build that is served names `m10-land-use` is the founder's to decide: question 9 of section 9.

## 5. Leafy and Works and warehouses on the real table

Worked out on 2026-09-24 from the preview above. A band is core's: a fifth of London by rank, with band 5 the most. No person has looked at either map.

### Leafy

On all of its recipe: gardens 40, woodland 30, public parks and gardens 30. Gardens and woodland are of 2022, and parks of April 2026.

| | |
|---|---|
| Areas placed | 1,002, about 200 in each band |
| Rank correlation of the score with homes per hectare | -0.56 |
| With distance from the centre | 0.49 |
| With its parts | Gardens 0.60, woodland 0.61, public parks 0.42 |
| With modelled nitrogen dioxide | -0.61 |

So Leafy is not a map of how far a place is from the centre. It leans outward, as a Londoner would expect, and no one part decides it. The two rank correlations are the same to two places whether the centre is the middle of London's homes or Charing Cross.

The two ends of it, category by category:

| End | Where | What the table says of each | Would a person accept it |
|---|---|---|---|
| The ten areas that score highest | Two each in Bexley, Barnet and Kingston upon Thames, and one each in Croydon, Greenwich, Bromley and Enfield | Gardens are 36 to 53 in 100 of the land, woodland 3 to 25 and public parks 5 to 28, at 10 to 23 homes to the hectare. Homes and roads are a fifth to a third of the land | Yes. Each is a suburb of houses with large gardens, a wood and a park. None is at the rural edge and none is in Richmond upon Thames. The second and the third owe their place to a wood that is a public park, which two parts count: section 4 |
| The ten that score lowest | Two in Camden, and one each in the City of London, Tower Hamlets, Newham, Westminster, Redbridge, Hackney, Wandsworth and Kensington and Chelsea | No woodland in any, and public parks under 2 in 100 of the land. Gardens are 0.2 to 18 in 100. Of the homes, 70 to 99 in 100 are flats. The land is roads, railways, offices and buildings of no known use: in one a railway is 37 in 100 of the land | Yes. One of the ten has 8 in 100 of its land under outdoor recreation that is no public park, which counts for nothing |

The score is a mix of three ranks. So it rewards an area that stands above the middle on all three over one that is far ahead on one, and a little woodland counts for much: London's middle area has 1.3 in 100 of its land in woodland, and an area with 2.7 stands above two thirds of London on that part.

| Borough | Areas | Band 1 | Band 2 | Band 3 | Band 4 | Band 5 | In band 4 or 5, in 100 |
|---|---|---|---|---|---|---|---|
| Bexley | 28 | 1 | 3 | 3 | 7 | 14 | 75 |
| Sutton | 24 | 0 | 1 | 7 | 6 | 10 | 67 |
| Bromley | 39 | 0 | 6 | 7 | 12 | 14 | 67 |
| Lewisham | 37 | 1 | 5 | 7 | 6 | 18 | 65 |
| Barnet | 42 | 0 | 8 | 7 | 6 | 21 | 64 |
| Croydon | 45 | 4 | 7 | 5 | 10 | 19 | 64 |
| Harrow | 30 | 0 | 6 | 6 | 10 | 8 | 60 |
| Greenwich | 35 | 7 | 0 | 7 | 9 | 12 | 60 |
| Richmond upon Thames | 23 | 0 | 1 | 9 | 5 | 8 | 57 |
| Hillingdon | 32 | 0 | 7 | 7 | 8 | 10 | 56 |
| Ealing | 41 | 8 | 3 | 8 | 13 | 9 | 54 |
| Merton | 25 | 3 | 4 | 5 | 8 | 5 | 52 |
| Havering | 30 | 1 | 6 | 9 | 7 | 7 | 47 |
| Kingston upon Thames | 20 | 1 | 3 | 7 | 1 | 8 | 45 |
| Hounslow | 29 | 0 | 8 | 8 | 8 | 5 | 45 |
| Redbridge | 33 | 2 | 11 | 5 | 9 | 6 | 45 |
| Enfield | 36 | 4 | 7 | 9 | 10 | 6 | 44 |
| Brent | 35 | 5 | 7 | 8 | 8 | 7 | 43 |
| Haringey | 36 | 3 | 11 | 9 | 10 | 3 | 36 |
| Barking and Dagenham | 22 | 5 | 3 | 6 | 7 | 1 | 36 |
| Lambeth | 35 | 10 | 8 | 8 | 7 | 2 | 26 |
| Islington | 23 | 9 | 5 | 3 | 5 | 1 | 26 |
| Camden | 27 | 10 | 9 | 2 | 6 | 0 | 22 |
| Waltham Forest | 28 | 4 | 8 | 10 | 3 | 3 | 21 |
| Southwark | 34 | 17 | 6 | 5 | 5 | 1 | 18 |
| Kensington and Chelsea | 21 | 8 | 5 | 5 | 2 | 1 | 14 |
| Wandsworth | 38 | 12 | 12 | 9 | 4 | 1 | 13 |
| Newham | 40 | 21 | 10 | 4 | 5 | 0 | 12 |
| Westminster | 24 | 13 | 6 | 4 | 1 | 0 | 4 |
| Hammersmith and Fulham | 25 | 16 | 6 | 2 | 1 | 0 | 4 |
| Hackney | 30 | 10 | 11 | 8 | 1 | 0 | 3 |
| Tower Hamlets | 34 | 25 | 7 | 2 | 0 | 0 | 0 |
| City of London | 1 | 1 | 0 | 0 | 0 | 0 | 0 |

Against what a Londoner expects:

| A Londoner expects | It reads | |
|---|---|---|
| Richmond upon Thames leafy | 13 of 23 areas in band 4 or 5, and 1 in band 1 or 2 | As expected, but ninth of 33 boroughs by its share of areas in band 4 or 5, and not first |
| Bromley leafy | 26 of 39 in band 4 or 5 | As expected. Its 6 areas in band 2 are its most rural |
| Barnet leafy | 27 of 42 in band 4 or 5 | As expected |
| The south-west leafy | Sutton 16 of 24, Merton 13 of 25, Kingston upon Thames 9 of 20, Wandsworth 5 of 38 | Sutton and Merton as expected. Kingston falls just short. Wandsworth reads not leafy |
| The City of London not leafy | Its one area is in band 1 | As expected |
| Tower Hamlets not leafy | 32 of 34 in band 1 or 2, none in band 4 or 5 | As expected |
| Newham not leafy | 31 of 40 in band 1 or 2, none in band 5 | As expected |

Where it reads wrong, and why:

| What | How many areas | Why |
|---|---|---|
| The most rural parts of London read not leafy | 27 areas are in band 1 or 2 though a third or more of their land is open land that no part counts: 5 in Bromley, 4 in Enfield, 4 in Havering | Land the table calls agricultural, golf courses and heath count for nothing, and they take the share of gardens down. Of the 40 areas where a fifth of the land or more is agricultural, 30 are in band 1 to 3 |
| Richmond upon Thames reads ninth | 23 | Its great parks are 35 in 100 of its land. They take the share of gardens down to London's middle, and the table classes the woods inside them as outdoor recreation, so they count as park and not as woodland |
| A wood that is a public park reads twice | 13 areas where 2 in 100 of the land or more must be counted by woodland and by public parks, 7 of them among the fifty that score highest | The table classes the land as woodland, and the file of parks counts it as park: section 4 |
| Wandsworth reads not leafy | 24 of 38 in band 1 or 2 | Gardens are 21 in 100 of its land and woodland 1.0. Its commons count once, as parks. Its middle area holds 50 homes to the hectare, and the borough has 53 square metres of garden for each home, as Newham has. What a Londoner sees there that no part counts is the trees of its streets |
| Lewisham reads above Richmond upon Thames and Bromley | 24 of 37 in band 4 or 5 | It is nearly all homes with gardens, so gardens are 31 in 100 of its land, the fourth most of any borough, though it has 90 square metres of garden for each home against Bromley's 260 |
| A reservoir | Of the 16 areas where a tenth of the land or more is water, 12 are in band 1 or 2, most of them in Enfield, Waltham Forest and Tower Hamlets | Water is land in the table, and no part counts it. It takes every share down |
| A cemetery | Of the 30 areas where a tenth of the land or more is cemetery, 19 are in band 1 or 2 | No part counts a cemetery |
| A golf course | Of the 51 areas where a tenth of the land or more is golf course, 23 are in band 1 to 3 | It is outdoor recreation, which no part counts. It is not counted as woodland |
| An airfield or a railway | Of the 29 areas where a tenth of the land or more is railway, airport or dock, 22 are in band 1 or 2 | It takes every share down. Most of these a Londoner would not call leafy, so it reads right |

What was tried, in no build:

| Leafy with | Areas that change band | Rank correlation with homes per hectare | With distance from the centre |
|---|---|---|---|
| The recipe as core holds it | | -0.56 | 0.49 |
| Gardens as the mean by homes | 202 | -0.67 | 0.57 |
| Gardens as garden land for each home | 439 | -0.84 | 0.64 |
| Gardens by homes, and every kind of open land in place of public parks | 465 | -0.81 | 0.70 |

Each mend of the rural edge makes Leafy more like a map of how far out a place is. With open land counted, 25 of the 27 rural areas above rise to band 3 or higher, and Bromley, Hillingdon and Havering lead. The recipe as core holds it is the least like a map of the centre.

### Works and warehouses

On 75 in 100 of its recipe: industry 40 and storage and warehousing 35, both of 2022.

| | |
|---|---|
| Areas placed | 1,002 |
| Areas in each band, 1 to 5 | 357, 45, 203, 198, 199 |
| Rank correlation of the score with homes per hectare | 0.11 |
| With distance from the centre | -0.01 |
| Areas with no industry and no storage | 357, which share band 1 |
| Areas with under 1 in 100 of their land in industry and storage together | 806 |
| Areas with 5 in 100 or more | 37 |
| Where band 5 begins | At 0.7 in 100 of an area's land in industry and storage together |
| Areas in band 5 with under 2 in 100 | 92 of 199 |
| The most land in band 4 | 4.2 in 100, all of it industry |
| Areas in band 4 with more land in industry and storage than the least of band 5 | 29 of 198 |

It is no map of the centre. The trouble is the bands. A band is a fifth of London, and only 37 areas are works and warehouses in any sense a Londoner would own. So band 5 takes in 12 areas of Tower Hamlets, 11 of Hackney and 10 of Southwark, and the City of London reads band 4 on 0.2 in 100 of its land.

And the bands do not follow the land. The score mixes the rank on industry with the rank on storage, and 451 areas tie at no industry and 536 at no storage. So an area with a little of each stands above an area with much of one: an area with 0.4 in 100 of its land in industry and 0.3 in storage is in band 5, and an area with 4.2 in industry and none in storage is in band 4.

| Borough | Areas | Band 5 | Industry and storage, in 100 of the borough's land | Hectares | Areas with 5 in 100 or more | A Londoner expects works at |
|---|---|---|---|---|---|---|
| Barking and Dagenham | 22 | 10 | 4.75 | 171 | 6 | Barking riverside |
| Brent | 35 | 12 | 2.70 | 117 | 6 | Park Royal |
| Newham | 40 | 10 | 2.41 | 87 | 4 | The Lea Valley and the riverside |
| Ealing | 41 | 14 | 1.71 | 95 | 2 | Park Royal |
| Hounslow | 29 | 13 | 1.70 | 95 | 2 | Heathrow's edge |
| Tower Hamlets | 34 | 12 | 1.36 | 27 | 1 | |
| Greenwich | 35 | 8 | 1.26 | 60 | 4 | Charlton |
| Bexley | 28 | 5 | 1.21 | 73 | 2 | |
| Haringey | 36 | 10 | 1.16 | 34 | 1 | The Lea Valley |
| Sutton | 24 | 4 | 1.14 | 50 | 1 | |
| Merton | 25 | 9 | 1.10 | 41 | 0 | |
| Enfield | 36 | 8 | 1.02 | 84 | 3 | The Lea Valley |
| Hackney | 30 | 11 | 0.80 | 15 | 0 | The Lea Valley |
| Waltham Forest | 28 | 2 | 0.79 | 31 | 0 | The Lea Valley |
| Havering | 30 | 7 | 0.78 | 87 | 1 | |
| Hillingdon | 32 | 7 | 0.75 | 87 | 2 | Heathrow's edge |
| Southwark | 34 | 10 | 0.71 | 20 | 0 | |
| Wandsworth | 38 | 9 | 0.69 | 24 | 1 | |
| Kingston upon Thames | 20 | 5 | 0.54 | 20 | 0 | |
| Croydon | 45 | 10 | 0.51 | 44 | 1 | |
| The other 13 boroughs | 360 | 23 | Under 0.4 each | 116 | 0 | |

Does it find what a Londoner expects:

| A Londoner expects | It finds | |
|---|---|---|
| Park Royal | Brent and Ealing hold 8 of the 37 areas with 5 in 100 or more, and 12 of the 50 areas that score highest | Yes |
| The Lea Valley | Enfield, Haringey and Newham hold 8 of the 37. Waltham Forest and Hackney hold none | In part |
| Barking riverside | Barking and Dagenham holds 6 of the 37, and the most industry of any borough | Yes |
| Charlton | Greenwich holds 4 of the 37 | Yes |
| Heathrow's edge | Hounslow and Hillingdon hold 4 of the 37. The airport itself is transport, which a build leaves out | In part |

So ranked from the top it is right. The 20 areas that score highest are in Brent, Barking and Dagenham, Enfield, Newham, Bexley, Haringey, Greenwich, Havering, Wandsworth, Ealing, Hillingdon and Croydon, and the least of them has 4.9 in 100 of its land in industry and storage. Served as five bands it is not: most of band 5 and all of band 4 would not be recognised.

With transport other than roads, which a build leaves out until core renames it, the bands are five even fifths, 378 areas change band and 37 change by two or more. The score keeps a rank correlation of 0.93 with the score on two parts.

### Through the API

Three sentences were sent to the API on the preview, through its test client, with no model. The rules read each.

| Sentence | What is applied | The first ten areas, by borough | The first fifty |
|---|---|---|---|
| "leafy" | Leafy, towards more | Harrow, Barnet, Croydon, Bromley, Bexley, Hillingdon, Croydon, Kingston upon Thames, Redbridge, Bexley. Each is in band 5 | Croydon 7, Bromley 7, Barnet 6, Bexley 6, Harrow 5, Sutton 4. Richmond upon Thames has none: its first area is 54th |
| "leafy and quiet" | Leafy and Quiet streets, each towards more | The same ten, in the same order | The same fifty. Quiet streets has no band in this release, so it adds nothing. The answer says so: the part is marked as missing, and the share of the wish that is covered falls to 57 in 100 |
| "somewhere green with a garden" | Nothing. Two offers are made: add Leafy, and more gardens. Two stretches of the sentence are marked as not read | On the offers taken: Hillingdon, Harrow, Kingston upon Thames, Barnet, Croydon, Croydon, Bexley, Sutton, Croydon, Harrow | Bromley 10, Barnet 7, Croydon 5, Bexley 5, Harrow 4 |

Every answer says `synthetic: false` and `preview: true`. The offer of gardens carries its note: "Burro cannot see whether one home has a garden. It can count how much of an area is residential garden."

## 6. What is done, and what is left to do

| # | Do | Standing on 2026-09-24 |
|---|---|---|
| 1 | Fetch the list `m10-land-use`. The file is stored and has no receipt | Done. `f-b8db326abd8b`, 38,142,392 bytes |
| 2 | Run `describe` on the file. Read its cover and its notes | Done, by a program. It holds no cover and no sheet of notes. Section 3 |
| 3 | Find what the file says of its date. State it in the list, and take `data_period` out of `unsure` | Done. The period is the year 2022 |
| 4 | Find any statement of Ordnance Survey's rights, or of any term beside the licence. Save what it says to `registry/evidence` | Done, by a program. It states none. A person has still to open the workbook once |
| 5 | Fetch again. The receipt is written | Done. The file that arrived is the file that was stored |
| 6 | Commit the receipt, under `data/receipts/mhclg-land-use-statistics-2022/` | Done |
| 7 | Run `packages/pipeline/tests/derive/test_land_use_on_the_real_files.py` with the store named | Done. Each of the nine tests that waited on the receipt passes on the real table |
| 8 | If the step stops, read its words against section 3. Put the code right, with a test on a made-up workbook | Not needed. The step did not stop |
| 9 | Add to the tests what the table holds: the rows of LSOAs, the cells that hold a dash, London's lowest, middle and highest for each measure | Done, for the share of land and for the mean by homes |
| 10 | Build with the list named: `make preview ARGS="... --list m1 --list m2-places --list m2-living --list m10-land-use"` | Done, to a folder git ignores. Section 4. The test of the first real build is left on its two lists until the founder has looked at the maps |
| 11 | Set the share of land beside the mean of shares by homes, for every area. Look at where they differ most | Done. Section 4. The choice is question 3 of section 9 |
| 11a | Look at the two maps, of Leafy and of Works and warehouses | **To do, by a person.** A program drew them and counted the bands by borough. Section 5 |
| 12 | Write the row of the proxy audit for each measure, before any weight is tuned | To do. ADR 0006. It reads figures about residents, which are read for the audit alone and by no step of this work |
| 13 | A person opens the workbook once, and says so in the evidence note | To do |

What would stop a run on a table that had changed, and what the step then says:

| If the table | The step says |
|---|---|
| Holds other text than a dash in a cell of figures | "an area of land is not a number" |
| Holds a row that does not add up to its grand total | "a row does not add up to its total" |
| Holds an LSOA of London with no row | "an LSOA of the census of 2021 has no row" |
| Gives totals far from the land of its LSOAs | "its totals are not the hectares of its LSOAs" |

## 7. Gritty on what is held

The founder decided on 2026-09-24 that Gritty is one vibe, made of works and warehouses, recorded criminal damage, recorded anti-social behaviour, main roads, noise and density, and of whatever else is measured of the place. Its recipe is not written yet. On 2026-09-24 core held the scale `street_character`, from Polished to Gritty, and that is the recipe counted here.

Each part was worked out from the files the store held on 2026-09-24. Counts only.

| Part | Hundredths | File in the store | Areas with a figure | Can be worked out today |
|---|---|---|---|---|
| Main roads, `road_major_exposure` | 15 | Yes | 1,002 of 1,002 | Yes |
| Transport noise, `noise_exposure` | 15 | Yes | 1,002 of 1,002 | Yes |
| Homes per hectare, `homes_density` | 15 | Yes | 1,002 of 1,002 | Yes |
| Land used for industry, `land_industry` | 20 | Yes | 1,002 of 1,002 | Yes |
| Recorded criminal damage, `incident_criminal_damage` | 20 | No | None | No. The file is not saved, and no code reads it |
| Recorded anti-social behaviour, `incident_antisocial` | 15 | No | None | No. The same |
| **Held today** | **65** | | | **Enough to place an area, at 60. No real release carries the scale: see below** |

| If | Hundredths with a figure | Areas placed |
|---|---|---|
| Nothing more is done | 65 | Every area, were the scale allowed in a real release and main roads on the list of a build |
| Recorded crime is saved and read | 100 | The same |

Nitrogen dioxide is in the store, with a figure for all 1,002 areas. It is in no recipe of core. Whether it joins Gritty, as one more measure of the place, is for whoever writes the recipe.

Four things the recipe's writer should know:

- Industry is thin. 451 of the 1,002 areas hold none, and London's middle area has 0.1 in 100 of its land in it. As a part of a recipe it tells areas apart in the upper half alone. Section 4.
- The decision names works and warehouses, which is three measures. The scale counted here holds industry alone. Core's rule is that no part carries 60 hundredths or more, so that no one source decides a vibe. Industry, storage and transport are three parts from one table, so the rule does not see that they are one source.
- A release that is not made up refused a vibe that holds recorded crime, by the rule `gritty_b_is_synthetic`. That was ADR 0013, which the decision changes. The record is amended and the rule is taken out: a build of London carries Gritty as the scale, and places an area on it once 60 in 100 of its recipe is measured.
- Main roads are worked out and are not on the list of the measures of a build. Its module says core holds no such measure. Core now does.

### What the founder must do for each missing part

| Part | What to do | Then |
|---|---|---|
| Land use | Nothing | Done. The table is read, and industry has a figure for every area |
| Recorded criminal damage, recorded anti-social behaviour | Section 8, or question 1 of section 9 | No code reads the police file yet. A rate needs a count of residents, and the registry names the source of one |
| The recipe | Write it in core, with ADR 0013 amended | Core's tests hold a recipe to its rules |

## 8. Recorded crime: the file a person saves

The registry entry `police-uk-street-level-crime` is approved for scoring and display. It allows the crime files alone. The list `m2-living` holds the file as `police-crime-london`, to be saved by a person.

The form was read twice on 2026-09-24, in different words. Both readings gave the same months, the same forces, the same three boxes and the same button. They differed on which boxes start ticked. So look at each box, and trust no starting state.

| # | On the page https://data.police.uk/data/ | Set it to |
|---|---|---|
| 1 | Date range, from | August 2023, the earliest month offered |
| 2 | Date range, to | July 2026, the latest month offered |
| 3 | Forces: "All forces" | Not ticked |
| 4 | Forces: "Metropolitan Police Service" | Ticked |
| 5 | Forces: "City of London Police" | Ticked |
| 6 | Every other force, "British Transport Police" among them | Not ticked |
| 7 | "Include crime data" | Ticked |
| 8 | "Include outcomes data" | Not ticked. Untick it if it is ticked |
| 9 | "Include stop and search data" | Not ticked. Untick it if it is ticked |
| 10 | "Generate file" | Press it, and save what it offers |

Why each box:

| Box | Why |
|---|---|
| Outcomes | The registry entry says: "Do not ingest the outcomes files either" |
| Stop and search | The registry entry says the files "hold the ethnicity, gender and age of the person stopped". It is never taken |
| British Transport Police | The list names two forces. The publisher's changelog, as the research on gritty read it, shows no crime data from the transport police for the months since March 2025. Whether to add the force is question 2 of section 9 |

Before the file is handed over:

| # | Do | Why |
|---|---|---|
| 1 | Look at the names inside the zip. A name that says outcomes or stop and search means a box was ticked. Delete the file and start again | The registry forbids both |
| 2 | Write down the address the browser saved the file from | `by-hand` holds the file to the registry entry by that address |
| 3 | Name that address under `file_urls` in the registry entry, in a change that a person reads. The entry names none today | A file is taken from no address the entry does not name |
| 4 | If the months saved are not August 2023 to July 2026, put the edition and the period right in the list | The receipt states what the list states |
| 5 | Hand it over: `uv run python -m burro_pipeline by-hand --list m2-living --item police-crime-london --file FILE --url ADDRESS --saved-on DAY` | The file is stored, with a receipt that says `by_hand` |

Never the archive of the same site, and never its API: the list says why.

What no page says of the file: its size, where it is served from, and which census the LSOA code of a row follows.

## 9. What the founder must decide

| # | Question | Choices | What is recommended |
|---|---|---|---|
| 1 | Which file recorded criminal damage and anti-social behaviour are read from | The police file of section 8, which is monthly, snapped to points and needs a count of residents. Or File 8 of the Indices of Deprivation 2025, which is in the store, gives both as rates by LSOA, and is an average to March 2024. The research on gritty recommended File 8. Its registry entry allows the noise indicator alone, so each rate needs its place on the list of features first | File 8, for what is a slow-moving character. It needs no file saved. The decision is the founder's, because it widens what is read from a file that holds figures about residents on other sheets |
| 2 | Whether the transport police are one of the forces | Two forces, as the list has it. Or three | Two, until someone has seen that the third sends data |
| 3 | Whether a land use part is a share of the area's land, or a mean of its LSOAs' shares by homes | The share of land is what core's names say, and is what a build carries. The mean by homes counts a works among homes for more than one where nobody lives, and is what the design of the vibes asked for. Core would then say the measure is averaged. Both are worked out by the code, and section 4 sets them side by side on the real table | The share of land for the page of an area, and for woodland in Leafy. The mean by homes for gardens in Leafy: it moves 202 areas by a band, most of them at the edge of London. For works and warehouses either, since they rank London almost alike |
| 4 | What core calls transport other than roads | Core's name says depots and yards. The category holds railways, airports and docks | Rename it in core. The measure is then carried |
| 5 | Whether the entry stands as approved before a person has opened the workbook | Approved, with the reading as a thing to settle before launch. Or gated until a person has read it | Approved. Three of the publisher's own documents state the licence, and the workbook states nothing otherwise |
| 6 | Whether to build on the table of 2022, or to wait for the one the publisher plans for 2024 to 2026 | Build on 2022 now, and say its date beside every figure. Or wait for the new table, which is planned by the end of 2026 and is not yet settled | Build on 2022 now, with its date beside every figure. The code is written, and the new table is not settled. Read the new table when it is published, as a source of its own |

| 7 | Whether what a program read of the workbook is enough for its receipt | Enough, as it has stood for the files of list m1. Or put `data_period` back under `unsure` until a person has opened the workbook | Enough. The title of each sheet states the year, and a person can see it in a minute |
| 8 | Whether a figure is shown as of 2022, or as of April 2022 | The year, which the workbook states. Or the month, which the statistical release states and the workbook does not | The year. The technical notes of the same release give another month and year for the products behind the figures |
| 9 | Whether Leafy is served on the recipe core holds | Core places every area on Leafy in any build that names the list `m10-land-use`. The design of the vibes says that recipe holds no tree and is not shipped. Section 5 says how it reads: broadly as London does, wrong at the rural edge | Look at the map, then serve it, with its words put right: it counts gardens, woodland and public parks, a wood that is a public park twice, and no golf course, farm, heath or street tree |
| 10 | Whether Works and warehouses is served as five bands | As it is, a fifth of London is in band 5, which begins at 0.7 in 100 of an area's land. Or a band is given only above a least share of land. Or the vibe is shown for the areas at the top alone | Not as it is. The rule of a band is core's, and is one rule for every vibe, so this is a change to core and a decision |
| 11 | Whether Leafy should count open land that is no public park | It counts none today: no golf course, playing field, heath or land the table calls agricultural. Counting it mends the rural edge and makes Leafy more like a map of distance from the centre: section 5 | The founder's to choose. The recipe as it stands is the least like a map of the centre |
| 12 | Whether a wood that is a public park should count twice in Leafy | It does today, as woodland and as public park, each at 30 in 100. For 2 in 100 of an area's land or more it must in 13 areas and may in 157, and two of the three areas that score highest are such places. The table cannot say which land it is. The outlines of woodland would, and no file of them is held | Leave it and say so beside the vibe, until a file of the outlines of woodland is registered. A wood that is open to walk in is what a person means by leafy, so the fault is of measure and not of kind |

## 10. What was not read

| What | Standing | What rests on it |
|---|---|---|
| The figures of the table | Read on 2026-09-24, by a program, through the gate | Every figure of every measure, and every band |
| The table, by a person | Not opened | Section 3, which a program read |
| The maps of Leafy and of Works and warehouses, by a person | Drawn, and not looked at | Section 5, which a program counted |
| Ordnance Survey's own definition of a public park or garden | Not read. The file names the kind and defines none | What is said in section 4 of where a park falls in the table rests on the figures |
| Any figure about who lives in an area | Not read, for any part of this work | The proxy audit, which is still to do |
| The national live tables | Not opened | Nothing. They are not taken |
| The factsheet | Not read | Nothing |
| The editions before 2022 | Their pages were not read | Nothing. The entry covers 2022 alone |
| A web search | None was made. The publisher's collection page and its own search were read | A later edition published under another title, or by another body, would be missed |
| The police changelog and archive | Not read on 2026-09-24 | What section 8 says of the transport police is from the research on gritty |
| A lookup from the LSOAs of 2011 to those of 2021 | Not looked for | Nothing. The workbook says its rows are of the LSOAs of 2021 |
| Ordnance Survey's terms for the products behind the figures | Not read | The entry uses the published table alone |

## 11. Unverified

- That a dash is none of that land, in the publisher's own words. Nothing says so. The figures do: no cell holds the number nought, and every row adds up to its grand total with each dash taken as nought. Section 3.
- That the figures are as at April 2022 and not April 2021. The workbook says 2022, and no month.
- That what `describe` gave is all the words the workbook holds. It reads the part that holds the sheets, and no picture, no header of a printed page and no property of the document.
- That a share of land separates the places people call full of works from the places they do not. The design asks for that to be tried on 20 of each, by name. It was tried by borough alone: section 5.
- That either map looks like London to a person. A program counted the bands by borough, and no person has looked.
- How much woodland lies inside a public park, to the hectare. It is at least 177 hectares and at most 2,723. The least rests on taking homes, gardens, roads, railways and works as unable to lie inside a park's outline. With nothing taken so it is 35 hectares. Where the truth lies between the least and the most is not known: section 4.
- Why the table classes one park as outdoor recreation and another as woodland. The two files are four years apart, and nothing read says whether that is why.
- That the publisher knows its sheet of per cent gives industry as a part of one. No page read says so. No figure here rests on that sheet: section 3.
- Why the table holds so little industry and storage. It may count the ground a building stands on and no yard. No page read says so.
- Where cemeteries stand in the table. The technical notes say utilities, and the figures say otherwise: section 4.
- Every weight of every recipe.

## 12. Pages read

| Page | Address |
|---|---|
| Land use in England, the collection | https://www.gov.uk/government/collections/land-use-in-england |
| Land use statistics in England: methodology changes, the consultation | https://www.gov.uk/government/consultations/land-use-statistics-in-england-methodology-changes/land-use-statistics-in-england-methodology-changes |
| Land use in England, 2022 | https://www.gov.uk/government/statistics/land-use-in-england-2022 |
| Land use statistics: England 2022, the statistical release | https://www.gov.uk/government/statistics/land-use-in-england-2022/land-use-statistics-england-2022 |
| Land use and Land use change statistics, technical notes | https://assets.publishing.service.gov.uk/media/63595b6ed3bf7f0bd5cea49d/Land_Use_and_Land_Use_Change_-_Technical_Notes.pdf |
| Open Government Licence v3.0 | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
| GOV.UK, research and statistics, searched for the title | https://www.gov.uk/search/research-and-statistics |
| data.police.uk, data downloads | https://data.police.uk/data/ |

Credits for the figures of this page, in each publisher's own words as the licence registry holds them:

- Land use, transport noise and homes per hectare: Contains public sector information licensed under the Open Government Licence v3.0.
- Public parks and gardens: Contains OS data © Crown copyright and database right [year].
- Main roads: Contains OS data © Crown copyright and database right [year].
- Nitrogen dioxide: © Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL).
- The geography behind each: Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year].

`[year]` is the registry's own placeholder. No year was made up.
