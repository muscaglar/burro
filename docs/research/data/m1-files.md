# What the files of the first real build hold

Status: read on 2026-09-23, from the files fetched that day for list `m1`, and corrected on 2026-09-24 after two checks of the first build. It is a dated snapshot. A publisher that reissues a file makes another file, with another hash, and this page does not describe it. File 8 of the Indices of Deprivation has had a receipt since: [the page on the files of the second build](m2-files.md) says what it holds.

No person has checked anything on this page. Every count was made by a program. The credit of each publisher is at the foot.

It is written for whoever writes the code that reads a file. It holds the names of columns, sheets, layers and members, and counts. It holds no row of any file.

| How it was read | |
|---|---|
| The shape of each file | The pipeline's own step, `python -m burro_pipeline describe --path FILE --inside` |
| What is inside | Each file was then opened by short programs that are not kept. Each asked the licence gate first |
| The counts of the spine, the outlines and the land | The step `python -m burro_pipeline cells`, which is kept and tested |
| What holds the counts from now on | `packages/pipeline/tests/cells/test_the_real_files.py`. It runs where `BURRO_STORE_FOLDER` names the store, and is skipped elsewhere |

One slip is recorded in section 13.

## 1. The eleven files

All eleven files of the list are in the store. Ten have a receipt. One does not.

| Item of the list | Registry id | File id | Bytes | Kind | Rows are keyed by | Receipt |
|---|---|---|---|---|---|---|
| `oa-lookup` | `ons-oa21-lsoa21-msoa21-lad22-lookup` | `f-49321b95f212` | 22,281,470 | CSV | `oa21` | Yes |
| `oa-boundaries-bgc` | `ons-output-areas-2021` | `f-7727e4b03845` | 128,831,488 | GeoPackage | `polygon`, one for each `oa21` | Yes |
| `oa-boundaries-bfc` | `ons-output-areas-2021` | `f-89acdc47cdb1` | 1,169,108,992 | GeoPackage | `polygon`, one for each `oa21` | Yes |
| `oa-centres` | `ons-oa-pwc-2021` | `f-00e1d0532798` | 22,030,298 | CSV | `point`, one for each `oa21` | Yes |
| `lsoa-boundaries-bgc` | `ons-lsoa-2021` | `f-9f549e33f46b` | 50,098,176 | GeoPackage | `polygon`, one for each `lsoa21` | Yes |
| `census-ts044` | `ons-census-2021-housing-tables` | `f-af7b512615ea` | 3,077,120 | Zip of CSV | `oa21`, and a file for each larger geography | Yes |
| `voa-ctsop-1-1` | `voa-council-tax-stock-of-properties` | `f-e1979a4196e2` | 749,909 | Zip of CSV | `lsoa21`, with rows for larger areas too | Yes |
| `voa-ctsop-3-1` | the same | `f-c8891afc8f10` | 7,899,033 | Zip of CSV | the same | Yes |
| `voa-ctsop-4-1` | the same | `f-c4e32565aeb1` | 6,156,819 | Zip of CSV | the same | Yes |
| `iod-file-8` | `mhclg-iod-2025-underlying-indicators` | none | 14,500,506 | Workbook | `lsoa21` | **No** |
| `defra-no2-2024` | `defra-pcm-background-air` | `f-d169e49479d8` | 7,900,343 | CSV | `grid_1km` | Yes |

- **File 8 has no receipt.** The list states no period for it, so fetch stored it and wrote none. The notes sheet of the file gives the period of the noise indicator: section 10. Until a person states it in the list and the receipt is written, no figure may rest on the file, and `Inputs.open` refuses it.
- **Every receipt says `geography: null`.** The column "Rows are keyed by" above is what was read from each file. A receipt is written by fetch and by nothing else, so it was not changed.
- **The folder of receipts now holds receipts of other lists too.** A second file of `defra-pcm-background-air` is there. A step that opens a file of a source with more than one must say which, by `edition=` or `named=`.
- The largest file, the full-resolution boundaries, is not read by any step of the first build.

## 2. Which census the codes follow

Every file that holds area codes uses the codes of the census of 2021. Each was joined to the lookup, and nothing failed to join in either direction.

| File | Codes | In the file | English codes not in the lookup | Lookup codes not in the file | Of London's |
|---|---|---|---|---|---|
| Boundaries, BGC and BFC | `OA21CD` | 188,880: 178,605 English, 10,275 Welsh | 0 | 0 | 26,369 of 26,369 |
| Centres | `OA21CD` | 188,880 | 0 | 0 | 26,369 of 26,369 |
| TS044, by output area | `geography code` | 188,880 | 0 | 0 | 26,369 of 26,369 |
| LSOA boundaries | `LSOA21CD` | 35,672: 33,755 English, 1,917 Welsh | 0 | 0 | 4,994 of 4,994 |
| VOA, all three tables | `ecode` where `geography` is `LSOA` | 35,672 | 0 | 0 | 4,994 of 4,994 |
| VOA, all three tables | `ecode` where `geography` is `MSOA` | 7,264: 6,856 English, 408 Welsh | 0 | 0 | 1,002 of 1,002 |
| File 8, every data sheet | `LSOA code (2021)` | 33,755, England only | 0 | 0 | 4,994 of 4,994 |

- The lookup is England only. A Welsh code was counted and not joined.
- The plan feared that the VOA tables used the codes of 2011. They do not. No lookup from 2011 to 2021 is needed for the first build.
- A file on the codes of 2011 would lack every LSOA that was drawn again for 2021. How many London had in 2011 was not counted: no file of 2011 is in the store.
- In the boundaries of output areas, the column `LSOA21CD` agrees with the lookup for every output area of London.
- File 8 names districts by their codes of 2024. For London each equals the lookup's code of 2022.

## 3. The spine, counted

London is the rows of the lookup whose `LAD22CD` starts `E09`.

| | The design expects | Counted | Differs by |
|---|---|---|---|
| Output areas | 26,369 | 26,369 | 0 |
| LSOAs | 4,994 | 4,994 | 0 |
| MSOAs | 1,002 | 1,002 | 0 |
| Boroughs, with the City | 33 | 33 | 0 |

| What holds of London's rows | |
|---|---|
| Each output area is there once | Yes |
| An output area in two LSOAs, an LSOA in two MSOAs, an MSOA in two boroughs | None. One MSOA outside London is in two districts |
| An LSOA or an MSOA that lies across London's edge | None |
| Output areas in an LSOA | 2 to 12, 5 at the median |
| Output areas in an MSOA | 16 to 46, 26 at the median |
| LSOAs in an MSOA | 3 to 9, 5 at the median |
| MSOAs in a borough | 1 to 45, 30 at the median. The City is one MSOA |
| Households at the census, summed over output areas | 3,423,767 |
| An output area with no household | None |

## 4. The areas of the first build

No named neighbourhood exists yet. An area is an MSOA.

| Field | How it is made | Shape |
|---|---|---|
| `area_id` | `lon-n` and the MSOA's code in lower case | `lon-ne0200nnnn` |
| `name` | `MSOA21NM`, as the lookup gives it | The borough's name, a space, and three digits |
| `slug` | The name in lower case, with a hyphen for each run of other signs | |
| `borough` | `LAD22NM` | |

- All 1,002 labels are the name of the MSOA's own borough and a number. The step stops if one is not.
- The label is the statistics office's own, so it rests on a file. It claims no name.
- The id holds the code, so it cannot move when areas are sorted. A named area of a later build takes an id of another shape.
- The names the House of Commons Library gives to MSOAs are gated in the registry. They were not fetched and are not used.

## 5. The lookup

`OA21_LAD22_LSOA21_MSOA21_LEP22_EN_LU_V2_*.csv`. The end of the name is a number the portal gives to each download.

| | |
|---|---|
| Encoding | UTF-8, with a byte order mark |
| Ends of lines | CR LF |
| Header | Row 1. No note stands above it |
| Rows under it | 178,605 |
| A missing value | An empty cell, in `LEP22CD2` and `LEP22NM2` only |

| Column | Holds | Read |
|---|---|---|
| `OA21CD` | The output area. Starts `E00` | Yes |
| `LSOA21CD`, `LSOA21NM` | The LSOA. Starts `E01` | Yes |
| `MSOA21CD`, `MSOA21NM` | The MSOA. Starts `E02` | Yes |
| `LEP22CD1`, `LEP22NM1`, `LEP22CD2`, `LEP22NM2` | Local enterprise partnerships | No |
| `LAD22CD`, `LAD22NM` | The district. Starts `E06` to `E09` | Yes |
| `ObjectId` | 1 to 178,605 | No |

## 6. The census table of accommodation type

`census2021-ts044.zip`. It counts households, which the pipeline calls homes. It describes nobody.

| Member | Bytes | Rows under the header |
|---|---|---|
| `census2021-ts044-oa.csv` | 9,028,287 | 188,880 |
| `census2021-ts044-lsoa.csv` | 2,093,435 | 35,672 |
| `census2021-ts044-msoa.csv` | 463,744 | 7,264 |
| `census2021-ts044-ltla.csv` | 24,548 | 331 |
| `census2021-ts044-utla.csv` | 13,585 | 174 |
| `census2021-ts044-rgn.csv` | 1,448 | 10 |
| `census2021-ts044-ctry.csv` | 859 | 3 |
| `metadata/ts044-2021-2.txt` | 4,852 | Notes, not a table |

| | |
|---|---|
| Encoding | UTF-8, with no byte order mark |
| Ends of lines | LF |
| Header | Row 1 |
| A missing value | None was found. Every count is a whole number |
| `date` | `2021` in every row |
| `geography` | In the file by output area, the code again. In the others, the name |

| Column | Read |
|---|---|
| `date`, `geography` | No |
| `geography code` | Yes |
| `Accommodation type: Total: All households` | Yes. It is the weight behind a home |
| `Accommodation type: Detached` | No |
| `Accommodation type: Semi-detached` | No |
| `Accommodation type: Terraced` | No |
| `Accommodation type: In a purpose-built block of flats or tenement` | No |
| `Accommodation type: Part of a converted or shared house, including bedsits` | No |
| `Accommodation type: Part of another converted building, for example, former school, church or warehouse` | No |
| `Accommodation type: In a commercial building, for example, in an office building, hotel or over a shop` | No |
| `Accommodation type: A caravan or other mobile or temporary structure` | No |

- In every output area of London the eight kinds add up to the total.
- The statistics office changes small counts on purpose, and says so in the notes. So the sums differ by geography. For London: 3,423,767 over output areas, 3,423,841 over LSOAs, 3,423,857 over MSOAs, 3,423,885 over boroughs, and 3,423,890 in the row for the region. The pipeline sums output areas, so that a boundary that moves needs no new file.

## 7. The boundaries

Three GeoPackages of one layout. Each is an SQLite file of GeoPackage version 1.4, with one layer.

| | Output areas, to draw | Output areas, full | LSOAs |
|---|---|---|---|
| Layer, which is the table's name | `OA_2021_EW_BGC_V2` | `OA_2021_EW_BFC_V8` | `LSOA_2021_EW_BGC_V5` |
| Features | 188,880 | 188,880 | 35,672 |
| Geometry column | `SHAPE` | `SHAPE` | `SHAPE` |
| Geometry type | `MULTIPOLYGON`, in two dimensions | the same | the same |
| Coordinates | EPSG 27700, the National Grid, in metres | the same | the same |
| An outline that is null or empty | None | None | None |
| Points that draw London | 350,810 | 5,057,374 | 164,622 |

| Field | Type | Holds |
|---|---|---|
| `FID` | `INTEGER` | The row's number |
| `SHAPE` | `MULTIPOLYGON` | The outline |
| `OA21CD` | `TEXT(9)` | The output area. Not in the LSOA file |
| `LSOA21CD` | `TEXT(9)` | The LSOA |
| `LSOA21NM` | `TEXT(40)` | Its name |
| `LSOA21NMW` | `TEXT(29)` | Its name in Welsh. Filled for Welsh rows only |
| `BNG_E`, `BNG_N` | `MEDIUMINT` | One point of the unit, on the grid |
| `LAT`, `LONG` | `FLOAT` | The same point, as latitude and longitude |
| `GlobalID` | `TEXT(38)` | The portal's own id |

- An outline is held as the standard's own bytes: the letters `GP`, a version of 0, flags, the code 27700, no box, and then well-known binary, little-endian, of type 6.
- The file holds the tables of an index, `rtree_*`. They are not read. Every row is read and the wanted codes are kept, which takes under a second.
- `gpkg_contents` gives no box for the layer: its four corners are null.
- The file is opened as one that cannot change. SQLite then writes nothing beside it.
- The boundaries are cut at the mean high water mark, as the publisher's record says. So the tidal Thames is in no output area.
- Of the generalised output areas of London, 6 have a side that does not match its neighbour's exactly. They overlap by nothing that can be measured, and all lie inside one MSOA or another. The MSOAs fit together exactly.

## 8. The centres of output areas

`Output_Areas_(December_2021)_EW_Population_Weighted_Centroids_(V4)_.csv`.

| | |
|---|---|
| Encoding | UTF-8, with a byte order mark |
| Ends of lines | LF |
| Header | Row 1 |
| Rows under it | 188,880, one for each output area |
| A missing value | None was found |

| Column | Holds | Read |
|---|---|---|
| `X`, `Y` | Easting and northing in metres. Most are written to 4 decimal places, and 7 of them to 10 | Yes |
| `FID` | 1 to 188,880 | No |
| `OA21CD` | The output area | Yes |
| `GlobalID`, `GlobalID_2` | The portal's own ids. They differ | No |

The file does not say which grid `X` and `Y` are on. London's run from 504,154 to 559,254 east and from 157,194 to 199,948 north, which is London on the National Grid.

## 9. The three tables of homes, from the Valuation Office

Each zip holds a folder with one CSV and one workbook of notes.

| Zip | The table | Bytes | Columns | Rows under the header |
|---|---|---|---|---|
| `CTSOP1.1.zip` | `CTSOP1.1/CTSOP1_1_2025_03_31.csv` | 4,166,831 | 14 | 43,296 |
| `CTSOP3.1.zip` | `CTSOP3.1/CTSOP3_1_2025_03_31.csv` | 91,521,326 | 49 | 392,014 |
| `CTSOP4.1.zip` | `CTSOP4.1/CTSOP4_1_2025_03_31.csv` | 68,591,601 | 35 | 392,014 |

| | |
|---|---|
| Encoding | UTF-8, with a byte order mark |
| Ends of lines | LF |
| Header | Row 1 |
| The data is as at | 31 March 2025, as the cover sheet of each workbook says |
| A count | A whole number that ends in 0. Every count is rounded to 10 |
| `0` | A count of nought. It is written |
| `-` | Not nought, and not a number. The file does not say what it means. See below |
| `..` | In `band_i` of table 1.1, for every English row. Band I is for Wales only |

**The first four columns are the same in all three.**

| Column | Holds |
|---|---|
| `geography` | The kind of area a row is for: `LSOA` 35,672 areas, `MSOA` 7,264, `LAUA` 318, `CTYMET` 29, `REGL` 9, `NATL` 2, `ENGWAL` 1, `UNMD` 1 |
| `ba_code` | The billing authority. Never empty |
| `ecode` | The area's code. For an LSOA it starts `E01` or `W01` |
| `area_name` | The area's name. For an LSOA of London it is the LSOA's name |

**Tables 3.1 and 4.1 have a fifth, `band`.** Each area has a row for `All`, and one for each band from `A` to `H`. A Welsh area has one more, for `I`. So an English LSOA has 9 rows. Read the row where `band` is `All`.

| Table | Columns after those | For the first build |
|---|---|---|
| 1.1, by band | `band_a` to `band_i`, `all_properties` | Not needed |
| 3.1, by kind of home | For each of `bungalow`, `flat_mais`, `house_terraced`, `house_semi`, `house_detached`: `_1` to `_6` by bedrooms, `_unkw`, `_total`. Then `annexe`, `caravan_houseboat_mobilehome`, `unknown`, `all_properties` | Flats are `flat_mais_total`. Homes are `all_properties` |
| 4.1, by when built | `bp_pre_1900`, `bp_1900_1918`, `bp_1919_1929`, `bp_1930_1939`, `bp_1945_1954`, `bp_1955_1964`, `bp_1965_1972`, `bp_1973_1982`, `bp_1983_1992`, `bp_1993_1999`, `bp_2000_2008`, `bp_2009` to `bp_2025` one for each year, `bp_unkw`, `all_properties` | Before 1919 is `bp_pre_1900` and `bp_1900_1918` |

What a parser must know:

- **`-` is a count of 1 to 4, by the file's own rows.** `0` is written where a count is nought, and the smallest number written is 10. The notes workbook in each zip names the columns and says nothing of rounding or of `-`, and the publisher's page was not opened. So the reading is held to the file itself. Over all 6,856 MSOAs of England and every count that is read: where every LSOA has `0` the MSOA has `0`; where any LSOA has `-` or a number the MSOA never has `0`; where the MSOA has `-`, no LSOA has a number and at most four have `-`; and where the MSOA has a number it is within 5 of the sum of its LSOAs for each LSOA and 5 for itself. No row breaks one. `derive/rounded_counts.py` holds the four rules, the build stops if a row of London breaks one, and a test on the real files holds them for England.
- **`-` is never read as nought in a figure.** An area is an MSOA, and its figure is read from the publisher's own row for the MSOA. Where the count on top of a share is `-`, the area has no figure.
- **`-` is common.** For London's LSOAs, in the row for all bands: `flat_mais_total` has 31, `bp_pre_1900` has 480, `bp_1900_1918` has 586. `all_properties` has none.
- **An LSOA with `-` must not be left out of a sum.** Tried on the real files: leaving out the 31 LSOAs with `-` for flats moved an area's share of flats by up to 11 points.
- **A total is rounded by itself.** `all_properties` is not the sum of its parts. For London's LSOAs it differs from the sum by -20 to 20 in table 3.1 and by -50 to 40 in table 4.1.
- **The file gives a row for each MSOA too.** The sum of an MSOA's LSOAs differs from its own row by -20 to 20. The row is rounded once and the sum several times. So the row is the better count, and it is the one a figure is read from while an area is an MSOA.
- **No band covers 1940 to 1944.** The bands go from `bp_1930_1939` to `bp_1945_1954`.
- **Some homes are of no known kind or age.** In the row for London: 33,120 of 3,837,380 homes have an unknown kind, and 32,690 an unknown build period.
- **The notes name the table of 4.1 wrongly.** They call it `CTSOP4_1_2025_13_31`. The file is `CTSOP4_1_2025_03_31.csv`.
- **The notes give no source line.** The registry asks that each be read for one. None of the three holds any.
- London's homes: 3,840,040 summed over LSOAs, 3,837,410 over boroughs, 3,837,380 in the row for the region. The three differ by under 1 in 1,000.

| Notes workbook | Sheets |
|---|---|
| `CTSOP1_1_CSV_table_notes.xlsx` | `Cover Sheet`, `CSV_files`, `CSV_variables`, `BA_code_notes` |
| `CTSOP3_1_CSV_table_notes.xlsx` | `Cover Sheet`, `CSV_files`, `CSV_variables` |
| `CTSOP4_1_CSV_table_notes.xlsx` | `Cover Sheet`, `CSV_files`, `CSV_variables` |

## 10. File 8 of the Indices of Deprivation

`File_8_IoD2025_Underlying_Indicators.xlsx`. It has no receipt, so no step may read it and nothing may be cited to it.

What was done with it, which was more than that allows: the step `describe` was run on it for its sheets and columns, a short program read its notes sheet, and a development program read the noise column of a copy and worked out figures for London, going round the receipt. Those figures were in a test and on this page. They have been taken out of both, and no figure of this file is in any tracked file of this build. The counts of rows and the names of columns below are what `describe` prints. The words quoted are from the notes sheet.

| Sheet, in order | Header is at | Rows under it | Columns |
|---|---|---|---|
| `Notes` | Row 11, in columns C to H | 37 | 6 |
| `IoD25 Income Domain` | Row 1 | 33,755 | 7 |
| `IoD25 Employment Domain` | Row 1 | 33,755 | 5 |
| `IoD25 Education Domain` | Row 1 | 33,755 | 6 |
| `IoD25 Health Domain` | Row 1 | 33,755 | 8 |
| `IoD25 Crime Domain` | Row 1 | 33,755 | 12 |
| `IoD25 Barriers Domain` | Row 1 | 33,755 | 14 |
| `IoD25 Living Env Domain` | Row 1 | 33,755 | 14 |

**Only the last sheet may be read, and of it only the columns marked.** Every other sheet describes residents.

| Column of `IoD25 Living Env Domain` | Read |
|---|---|
| `LSOA code (2021)` | Yes |
| `LSOA name (2021)` | No |
| `Local Authority District code (2024)`, `Local Authority District name (2024)` | No |
| `Housing in poor condition indicator` | No |
| `Housing energy performance deprivation Score` | No |
| `Housing lacking private outdoor space deprivation score` | No. It waits on its audit |
| `Noise pollution` | Yes |
| `Road traffic casualties involving injury to pedestrians and cyclists` | No |
| `Sulphur dioxide (component of air quality indicator)` | No |
| `Nitrogen dioxide (component of air quality indicator)` | No |
| `Benzene (component of air quality indicator)` | No |
| `Particulates (component of air quality indicator)` | No |
| `Air quality indicator` | No |

| `Noise pollution` | |
|---|---|
| What it is | A share from 0 to 1, and not a percentage |
| A missing value | None. All 33,755 cells hold a number |
| How a number is written | As a number of the workbook, and not as text. Many have 17 digits after the point, which is how a workbook keeps a number of three decimal places |
| What the notes say it counts | "The percentage of the population of each LSOA exposed to noise pollution greater than or equal to 55dB Lden" |
| Its top and bottom | Residents exposed to transport noise, over the population of the LSOA in 2021. Neither is published |
| What was done to it | "Shrinkage was applied to this indicator" |
| Who supplied it | "Defra's Noise Modelling System" |
| The period it describes | `2021`, in the column `Data time point` |
| A copyright statement of a third party | None on its row. Rows of the health sheet carry one |

- **The period to state in the list is 2021**, for the noise indicator. The workbook holds many indicators, each with a period of its own, and one receipt states one period.
- The measure is a share of residents exposed, and not of homes. The catalogue in core says homes. The plan already lists that as a fault for the contract's owner.
- No top and bottom are published, so no sum can be taken. The method is the mean by homes, `lsoa_value_by_homes`, marked as averaged.
- The pipeline has no reader of a workbook's cells. `fetch/workbook.py` reads the first rows of a sheet for the names of its columns, and counts the rest. The design names `openpyxl` for the purpose. Whichever is used must open the one sheet by its name and no other.
- Sheet 8 of the workbook unpacks to 21.7 MB of markup. The text of all sheets is in one shared table of 2.0 MB.

## 11. The grid of nitrogen dioxide

`mapno22024.csv`.

| | |
|---|---|
| Encoding | Plain ASCII, with no byte order mark |
| Ends of lines | CR LF |
| Rows 1 to 4 | Notes, each in the first of four cells: `no2`, `2024`, `annual mean`, `ug m-3` |
| Row 5 | Empty: three commas |
| Row 6 | The header: `gridcode`, `x`, `y`, `no22024` |
| Rows under it | 254,905, from row 7 |
| A missing value | The publisher writes `MISSING`. This file holds none |

| Column | Holds |
|---|---|
| `gridcode` | The publisher's number for the square. Each is there once |
| `x`, `y` | The middle of the square, in whole metres. Each ends in 500 |
| `no22024` | The annual mean for 2024, in micrograms a cubic metre, to at most 6 decimal places |

- The publisher's page says the data begins on row 6. Row 6 is the header, and the data begins on row 7.
- The name of the fourth column holds the pollutant and the year, so it changes with the file.
- The file does not say which grid `x` and `y` are on. They run from -500 to 655,500 and from 5,500 to 1,219,500, which is Great Britain on the National Grid. One `x` is below nought.
- A point at easting `e` and northing `n` is on the square whose middle is at `floor(e / 1000) * 1000 + 500`, and the same for `n`. `cell_of` in `derive/methods.py` gives the corner, which is the middle less 500.
- Every centre of an output area of London is on a square with a value. They stand on 1,444 squares.
- An area reads 1 to 13 squares, 4 at the median. Neighbouring areas share squares, so the figure varies less than the map suggests. Tried on the real files, 1,002 areas gave 720 different values at two decimal places.

## 12. What was made from them

### The outlines

Each area's outline is the generalised outlines of its output areas joined, with every line between them taken out. Then each point is turned to longitude and latitude and written to 6 decimal places.

| | |
|---|---|
| Areas with an outline | 1,002 of 1,002, each from all of its output areas |
| Points before joining, and after | 350,810, and 73,988 |
| `geometry.json` | 1,724,927 bytes as the contract writes it. 379,674 when compressed by a server |
| What was simplified | Nothing but the joining. No point of the publisher's line was moved or dropped |
| Areas in one piece | 983 |
| Areas in more than one | 19, with 25 pieces beside the largest. The smallest is under 1 square metre and the largest 23.6 hectares. What the pieces are was not looked at: no map was drawn |
| Holes | One, of no size. It is where two output areas do not quite meet |
| Neighbours of an area | 2 to 13, 6 at the median. None has no neighbour |
| Two areas across the tidal Thames | Not neighbours. No boundary crosses the water |

Further simplifying was tried and not taken. It saves little, and moves lines that two areas share.

| Tolerance | Points | File | Furthest a line moved | Most an area's size changed |
|---|---|---|---|---|
| None | 73,988 | 1.71 MB | 0 m | 0 |
| 10 m | 66,770 | 1.56 MB | 57 m | 0.07% |
| 20 m | 61,924 | 1.45 MB | 72 m | 0.39% |
| 50 m | 40,034 | 0.98 MB | 185 m | 4.15% |

**Coordinates.** The National Grid is turned to longitude and latitude by one fixed operation, the seven-parameter shift that the coordinate library lists as "OSGB36 to WGS 84 (6)" and gives as good to 2 metres. It reads no grid file and reaches no network. The boundaries give one point of each output area both ways. For London's 26,369 the operation lands 2.06 m from the publisher's own latitude and longitude on average, and 2.77 m at worst. The exact operation needs a grid file of the Ordnance Survey, which is not a registered source.

**Held against memory, by no person.** 21 areas were taken, one in each of 21 boroughs, and the point inside each was held against the builder's memory of where that borough is. All 21 agreed with it. That is no check against a map, and no person made it. London as drawn runs from 51.2868 to 51.6919 north and from 0.5103 west to 0.3340 east.

### The land

| | |
|---|---|
| The land of an LSOA | What its generalised outline encloses. The grid is in metres, so nothing is projected |
| The land of an area | The sum of the land of its LSOAs. Each LSOA is part of one MSOA |
| Source | `ons-lsoa-2021`, which the registry holds for scoring. The boundaries of output areas are not held for scoring |
| London | 157,333.6 hectares |
| An LSOA | 0.85 to 1,580.62 hectares, 19.70 at the median |
| An area | 29.4 to 2,244.8 hectares, 111.8 at the median |
| Against the outlines of output areas, generalised | The same to within 0.0006% for every area |
| Against the full-resolution outlines | London is 157,342.2 hectares. An area differs by 0.25% at the median, by 0.85% at the 95th of 100, and by 2.33% at worst |

What counts as land is everything inside the line: homes, roads, parks, reservoirs and docks. Nothing seaward of the mean high water mark counts, so the tidal Thames does not.

### Homes since the census

The weights are households at the census of 2021. The Valuation Office counts homes at 31 March 2025. The two are not the same thing: an empty home is a home and no household. By LSOA, homes of 2025 over households of 2021 run from 0.66 to 5.2, with 1.063 at the median. 617 of London's 4,994 LSOAs hold a fifth more homes than they held households, and 213 hold half as many again. Open question 8 of the plan asks for this count. What to do about it is the founder's to decide.

## 13. What was not checked, and one slip

| Not checked | Why |
|---|---|
| What the publisher says `-` means in the VOA tables | The notes in each zip do not say, and nobody has read the publisher's page. What the file's own rows show is in section 9, and is held by a test |
| That `X`, `Y`, `x` and `y` are on the National Grid | Neither CSV says. Both fit |
| That the boundaries are generalised to 20 metres | From memory of the publisher's description. The file does not say, so no sentence of a method says it |
| The outlines on a map | No map was drawn for this page. 21 points were held against the builder's memory of where boroughs are |
| The exact position of any point | The fixed operation is good to about 2 metres |
| Any page of any publisher | None was opened |
| The output of hosted CI | No hosted run has made these counts. Another version of the geometry library may order points differently |

**The slip.** A short program written to read the notes sheet of File 8 unpacked every sheet of the workbook to count its rows. Seven of the eight sheets hold figures about residents. Nothing from them was kept, printed or written down but the count of rows and the names of the columns, which the step `describe` prints too. A reader of File 8 must open the one sheet it names.

## 14. Credits

Every count on this page was made from a file of one of these publishers. The words are each publisher's own, as the licence registry holds them. Three hold `[year]` where the publisher's page gives a year to fill in: which year is the founder's to say, and none was made up.

| Publisher | Files | Credit |
|---|---|---|
| Office for National Statistics | The lookup | Source: Office for National Statistics licensed under the Open Government Licence v.3.0 |
| Office for National Statistics | The boundaries of output areas and of LSOAs, and the centres of output areas | Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year] |
| Office for National Statistics, through Nomis | The census table of accommodation type | Source: Office for National Statistics |
| Valuation Office Agency | The three tables of homes | Contains public sector information licensed under the Open Government Licence v3.0. |
| Department for Environment, Food and Rural Affairs | The grid of nitrogen dioxide | © Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open Government Licence (OGL). |
| Ministry of Housing, Communities and Local Government | File 8 of the Indices of Deprivation | No figure of it is on this page. Its credit is the registry's to give once the file has a receipt |
