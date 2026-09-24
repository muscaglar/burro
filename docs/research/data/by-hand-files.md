# The four files a person saved on 2026-09-24

Status: read on 2026-09-24, from the files in the store that day. It is a dated snapshot. A publisher that reissues a file makes another file, with another hash, and this page does not describe it.

No person has checked anything on this page. Every count was made by a program.

It is written for whoever writes the code that reads one of the four. It holds the names of columns and of files inside a zip, counts, and how each file is encoded. It holds no row of any file, no name of a person, a school or a street, no postcode, and no figure of a neighbourhood.

Each file was handed over with `python -m burro_pipeline by-hand`, and then read through `Inputs.open`, which asks the licence gate and holds the file to its receipt.

## In short

| Item of the list | Registry id | File id | Bytes | Kind | Edition | Period | Use on the receipt |
|---|---|---|---|---|---|---|---|
| `naptan-london` | `dft-naptan` | `f-ed03193db0d8` | 4,507,776 | A CSV | `saved 2026-09-24` | 2026-09-24 | `scoring` |
| `gias-establishments` | `dfe-gias` | `f-e2cf7e0c0508` | 8,119,289 | A zip of one CSV | `2026-09-24` | 2026-09-24 | `scoring` |
| `police-crime-london` | `police-uk-street-level-crime` | `f-693f5a9b6e86` | 333,736,416 | A zip of 215 CSVs | `August 2023 to July 2026` | 2023-08 to 2026-07 | `scoring` |
| `postcode-directory` | `ons-postcode-directory` | `f-ab51f1e82bd5` | 253,928,895 | A zip of 222 files | `August 2026` | 2026-08 | `cells` |

What each held that the list did not expect:

| File | What differs |
|---|---|
| Stops and stations | It holds no station. A station is there only as its ways in: 550 to a railway station and 642 to a tram, metro or underground station. The publisher keeps the stations themselves under authorities of their own |
| Schools | It is not UTF-8. `Opened.text` reads UTF-8 alone, and stops on it. It holds 135 columns, and more of them are about people than the registry entry names |
| Recorded crime | It holds outcomes and stop and search beside the crime files. The gate did not refuse it: it reads the names inside a zip for the code of a census table, and for nothing else |
| Postcode directory | The names of its columns are not those of earlier editions: the publisher changed them on 2026-09-07. The zip holds the directory three times over, and unpacks to 4.1 GB |

## Where each came from

The browser's list of downloads gives the site a file came from. The browser also records, on the file, the address the file was saved from and the page that sent it there. That record was read, and is what `by-hand` was given. A parameter of an address was never written down: one address held a signed key.

| File | Saved from, with no parameter | Sent there from | Is that host the host of the publisher's pages |
|---|---|---|---|
| Stops and stations | `https://beta-naptan.dft.gov.uk/Download/MultipleLa` | `https://beta-naptan.dft.gov.uk/` | Yes |
| Schools | `https://ea-edubase-api-prod.azurewebsites.net/edubase/downloads/File.xhtml` | `https://get-information-schools.service.gov.uk/` | No |
| Recorded crime | `https://policeuk-data.s3.amazonaws.com/download/8af8d28d28ffb22827ea2b9ee45fb67e9dd724fd.zip` | `https://data.police.uk/` | No |
| Postcode directory | `https://www.arcgis.com/itemdata/92d347a7683b26a11dab76ccf9a5cac2/9e5a92a3cfb14dc7ad43d6ea7a7b8c7f/ONSPD_AUG_2026.zip` | Not recorded | No |

The registry entry of each names its address under `file_urls`, whole, and no prefix. What stands behind each line:

| File | What stands behind the address |
|---|---|
| Stops and stations | The browser's record. The host is the entry's own. The form's page was opened through a reader that extracts: it shows the authority and the formats, and no address |
| Schools | The browser's record, and nothing else. The publisher forbids reading its pages with a program, so none was read |
| Recorded crime | The browser's record, and nothing else. The form and the archive page were opened through a reader that extracts, and neither names the host |
| Postcode directory | The browser's record, and the portal's own record of the item, which gives the id of the item, the name of the file and its size. All three are in the address or are the file's |

A person should see each of the last three in a browser. Until then the three lines rest on what a browser wrote on a file.

## Stops and stations

`490Stops.csv`, for the authority the form lists as "Greater London / London (490)".

| | |
|---|---|
| Encoding | UTF-8, with no mark at its start. The whole file was read as UTF-8 |
| Rows | 21,288, each with an `ATCOCode` of its own |
| Columns | 43 |
| Rows are keyed by | A point: `Easting` and `Northing`, and `Longitude` and `Latitude`. No row lacks either pair |
| A day in the file | Each row holds the day it was made and the day it was last changed. The latest day any row was changed is 2026-09-15. The file holds no day of its own |

The columns, in order: `ATCOCode`, `NaptanCode`, `PlateCode`, `CleardownCode`, `CommonName`, `CommonNameLang`, `ShortCommonName`, `ShortCommonNameLang`, `Landmark`, `LandmarkLang`, `Street`, `StreetLang`, `Crossing`, `CrossingLang`, `Indicator`, `IndicatorLang`, `Bearing`, `NptgLocalityCode`, `LocalityName`, `ParentLocalityName`, `GrandParentLocalityName`, `Town`, `TownLang`, `Suburb`, `SuburbLang`, `LocalityCentre`, `GridType`, `Easting`, `Northing`, `Longitude`, `Latitude`, `StopType`, `BusStopType`, `TimingStatus`, `DefaultWaitTime`, `Notes`, `NotesLang`, `AdministrativeAreaCode`, `CreationDateTime`, `ModificationDateTime`, `RevisionNumber`, `Modification`, `Status`.

| `StopType` | Rows | What it is, from memory of the publisher's schema and not read on a page |
|---|---|---|
| `BCT` | 20,026 | A bus or coach stop on a street |
| `TMU` | 642 | A way in to a tram, metro or underground station |
| `RSE` | 550 | A way in to a railway station |
| `FTD` | 42 | A way in to a ferry terminal or a dock |
| `BCS` | 28 | A bay in a bus or coach station |

| `Status` | Rows |
|---|---|
| `active` | 21,284 |
| `inactive` | 4 |

Every row has `AdministrativeAreaCode` 082 and an `ATCOCode` that begins 490.

**It holds no station.** No row is of a kind that is a station or a platform. The form lists five authorities that are no place but a network, and the publisher's page gave them so on 2026-09-24, in two readings: "National - National Rail / Great Britain (910)", "National - National Tram / Great Britain (940)", "National - National Air / Great Britain (920)", "National - National Ferry / Great Britain (930)" and "National - National Automated People Mover / Great Britain (945)". The form takes more than one authority at once. So a measure of the way to a station has two roads. It can measure to the nearest way in, which this file holds. Or the founder saves the files of 910 and 940, which are national, and a step keeps what is in or near London.

What it cannot see: which ways in are of one station. The file holds no group of stops. A way in past London's edge is not in it.

## Schools

`extract.zip` holds one file, `edubasealldata20260924.csv`, of 64,682,618 bytes.

| | |
|---|---|
| Encoding | Not UTF-8. It reads whole as Windows-1252. 206 of its bytes are over 127. No mark at its start |
| Rows | 52,582, each with a `URN` of its own |
| Columns | 135 |
| Rows are keyed by | A point on the National Grid, `Easting` and `Northing`. It also holds `Postcode`, `LSOA (code)` and `MSOA (code)` |
| A day in the file | The name of the file holds 20260924 |

`Opened.text` reads UTF-8 and nothing else, so it stops on this file with `input_is_as_described`. A reader of it opens the one member of the zip and decodes it as Windows-1252. That is for the step that reads schools to build, in a module of its own.

| `EstablishmentStatus (name)` | Rows |
|---|---|
| `Open` | 27,174 |
| `Closed` | 25,346 |
| `Proposed to open` | 32 |
| `Open, but proposed to close` | 30 |

So nearly half the rows are of schools that are closed. 5,901 rows are of the region London, by `GOR (name)`. 3,189 of them are open. 3,178 of those have a grid reference, and 3,186 an LSOA code.

The registry entry asks that the list of columns is confirmed on first download. These are the columns that name a person or count pupils, by their names in the file. None is ever read:

| What it is | Columns |
|---|---|
| The name of a head teacher | `HeadTitle (name)`, `HeadFirstName`, `HeadLastName`, `HeadPreferredJobTitle` |
| The name of a proprietor, which may be a person's | `PropsName` |
| Counts of pupils | `NumberOfPupils`, `NumberOfBoys`, `NumberOfGirls`, `PercentageFSM`, `FSM` |
| Counts of pupils with special needs, or on the roll of a unit | `SENStat`, `SENNoStat`, `ResourcedProvisionOnRoll`, `SenUnitOnRoll` |
| A telephone number | `TelephoneNum` |

The registry entry names the first and the third. The others were found in the file. `PropsName` and `TelephoneNum` are the ones to look at: nobody has read what they hold.

Fenced by the registry entry until the founder decides: `ReligiousCharacter (code)`, `ReligiousCharacter (name)`, `ReligiousEthos (name)`, `Diocese (code)`, `Diocese (name)`.

Every other column, in order: `URN`, `LA (code)`, `LA (name)`, `EstablishmentNumber`, `EstablishmentName`, `TypeOfEstablishment (code)`, `TypeOfEstablishment (name)`, `EstablishmentTypeGroup (code)`, `EstablishmentTypeGroup (name)`, `EstablishmentStatus (code)`, `EstablishmentStatus (name)`, `ReasonEstablishmentOpened (code)`, `ReasonEstablishmentOpened (name)`, `OpenDate`, `ReasonEstablishmentClosed (code)`, `ReasonEstablishmentClosed (name)`, `CloseDate`, `PhaseOfEducation (code)`, `PhaseOfEducation (name)`, `StatutoryLowAge`, `StatutoryHighAge`, `Boarders (code)`, `Boarders (name)`, `NurseryProvision (name)`, `OfficialSixthForm (code)`, `OfficialSixthForm (name)`, `Gender (code)`, `Gender (name)`, `AdmissionsPolicy (code)`, `AdmissionsPolicy (name)`, `SchoolCapacity`, `SpecialClasses (code)`, `SpecialClasses (name)`, `CensusDate`, `TrustSchoolFlag (code)`, `TrustSchoolFlag (name)`, `Trusts (code)`, `Trusts (name)`, `SchoolSponsorFlag (name)`, `SchoolSponsors (name)`, `FederationFlag (name)`, `Federations (code)`, `Federations (name)`, `UKPRN`, `FEHEIdentifier`, `FurtherEducationType (name)`, `LastChangedDate`, `Street`, `Locality`, `Address3`, `Town`, `County (name)`, `Postcode`, `SchoolWebsite`, `BSOInspectorateName (name)`, `InspectorateReport`, `DateOfLastInspectionVisit`, `NextInspectionVisit`, `TeenMoth (name)`, `TeenMothPlaces`, `CCF (name)`, `SENPRU (name)`, `EBD (name)`, `PlacesPRU`, `FTProv (name)`, `EdByOther (name)`, `Section41Approved (name)`, `SEN1 (name)` to `SEN13 (name)`, `TypeOfResourcedProvision (name)`, `ResourcedProvisionCapacity`, `SenUnitCapacity`, `GOR (code)`, `GOR (name)`, `DistrictAdministrative (code)`, `DistrictAdministrative (name)`, `AdministrativeWard (code)`, `AdministrativeWard (name)`, `ParliamentaryConstituency (code)`, `ParliamentaryConstituency (name)`, `UrbanRural (code)`, `UrbanRural (name)`, `GSSLACode (name)`, `Easting`, `Northing`, `MSOA (name)`, `LSOA (name)`, `InspectorateName (name)`, `BoardingEstablishment (name)`, `PreviousLA (code)`, `PreviousLA (name)`, `PreviousEstablishmentNumber`, `Country (name)`, `UPRN`, `SiteName`, `QABName (code)`, `QABName (name)`, `EstablishmentAccredited (code)`, `EstablishmentAccredited (name)`, `QABReport`, `CHNumber`, `MSOA (code)`, `LSOA (code)`, `AccreditationExpiryDate`.

`Gender (name)` says whom a school admits. It is of the school and not of a resident. Whether it is read is for whoever builds the measure to ask.

What it cannot see: which census an LSOA code follows, and where a school with no grid reference is. A distance to a school is not a place at it.

## Recorded crime

`8af8d28d28ffb22827ea2b9ee45fb67e9dd724fd.zip`. The name is the publisher's, made for the one request.

| Names in the zip | Files | Bytes unpacked | Read |
|---|---|---|---|
| End `-street.csv`: recorded crime | 72 | 818,730,999 | By `derive/street_crime_files.py`, for the columns it lists |
| End `-outcomes.csv`: what became of a crime | 72 | 686,874,412 | Never |
| End `-stop-and-search.csv`: each person stopped | 71 | 88,200,843 | Never |

The counts and the sizes are from the list the zip keeps of itself. No file was opened to make them.

A name is a folder for the month, then the month again, the force, and the kind: `2023-08/2023-08-metropolitan-street.csv`. There are 36 months, from 2023-08 to 2026-07, and two forces, `city-of-london` and `metropolitan`. Every month of each force has its crime file. One month of one force has no stop and search file.

The 72 crime files name the same 12 columns, in this order: `Crime ID`, `Month`, `Reported by`, `Falls within`, `Longitude`, `Latitude`, `Location`, `LSOA code`, `LSOA name`, `Crime type`, `Last outcome category`, `Context`.

| Column | Read | Why not |
|---|---|---|
| `Month`, `Reported by`, `Falls within`, `Longitude`, `Latitude`, `LSOA code`, `Crime type` | It may be | |
| `Crime ID` | Never | It is what joins a crime to its outcome |
| `Last outcome category` | Never | It is the outcome, which the registry entry keeps unread |
| `Location`, `LSOA name`, `Context` | Never | A figure needs none of them |

`Crime type` holds 14 kinds in the four files of the first two months: `Anti-social behaviour`, `Bicycle theft`, `Burglary`, `Criminal damage and arson`, `Drugs`, `Other crime`, `Other theft`, `Possession of weapons`, `Public order`, `Robbery`, `Shoplifting`, `Theft from the person`, `Vehicle crime`, `Violence and sexual offences`. Whether a later month holds another kind was not read.

**What the gate did.** It looked inside the zip, read the names, and let the file through. It reads a name for the code of a census table about residents, and for nothing else. It has no rule on a name that says outcomes or stop and search, so it did not refuse this zip and would not refuse another like it. To find whether a file in the zip is itself a zip, it reads the first four bytes of every file in it. For a CSV those are the first letters of the name of its first column. It reads no more of any.

So three things keep the rest of the zip unread, and the gate is none of them: the condition on the registry entry, the one reader of the source, and the test that counts every file the reader opens.

What was read of a row: three columns of the four files of the first two months, to count the kinds above, and the columns that may be read of one month of the smaller force, which a test reads to see that a row is handed over with the columns asked for and no other. No other row has been read. Whether a month of a force is whole is not known. Which census an LSOA code follows is not known.

## Postcode directory

`ONSPD_AUG_2026.zip`.

| Folder in the zip | Files | What they are |
|---|---|---|
| `Data/` | 2 | The whole directory, as `ONSPD_AUG_2026_UK.csv` of 1,483,120,391 bytes, and again as text |
| `Data/multi_csv/` | 124 | The directory again, a CSV for each postcode area |
| `Documents/` | 94 | Names and codes of areas, each as a CSV and as a workbook |
| `User Guide/` | 2 | The guide, as a PDF and as an OpenDocument text |

It unpacks to 4,110,589,645 bytes. A step reads a file where it is, and unpacks nothing it does not read.

The 55 columns of the whole file, in order: `pcd7`, `pcd8`, `pcds`, `dointr`, `doterm`, `cty26cd`, `ced25cd`, `lad26cd`, `wd26cd`, `parncp26cd`, `usrtypind`, `east1m`, `north1m`, `gridind`, `hlth19cd`, `nhser24cd`, `ctry26cd`, `rgn26cd`, `ssr95cd`, `pcon24cd`, `eer20cd`, `educ23cd`, `ttwa15cd`, `pco19cd`, `itl25cd`, `wdstl05cd`, `oa01cd`, `wdcas03cd`, `npark16cd`, `lsoa01cd`, `msoa01cd`, `ruc01ind`, `oac01ind`, `oa11cd`, `lsoa11cd`, `msoa11cd`, `wz11cd`, `sicbl26cd`, `bua24cd`, `ruc11ind`, `oac11ind`, `lat`, `long`, `lep21cd1`, `lep21cd2`, `pfa23cd`, `imd20ind`, `cal26cd`, `icb26cd`, `oa21cd`, `lsoa21cd`, `msoa21cd`, `ruc21ind`, `oac21ind`, `imd25ind`.

The file of a postcode area names the same columns.

**The names are new.** The portal's record of the item says an update of 07/09/2026 corrected the names of the fields in the header of the CSV, and did not alter the data. A reader written from an earlier edition will find no column it asks for. Read the names here, and hold the file to them.

Five columns say something of who lives in an area, and are never read: `oac01ind`, `oac11ind` and `oac21ind`, which class an output area by its residents, and `imd20ind` and `imd25ind`, which rank an area by deprivation.

**Northern Ireland.** The guide says a postcode that starts BT needs a licence of its own for commercial use, and that to use such data is to accept the terms for Northern Ireland. So `Data/multi_csv/ONSPD_AUG_2026_UK_BT.csv` is never opened. A step that reads the whole file drops a line that starts BT before it reads a column of it. A step that reads London alone can read the files of London's postcode areas and never meet one.

**London.** One small file was read, for eleven named columns, to see that the names hold: every row of it has the country `E92000001` and the region `E12000007`, a grid reference and an `oa21cd`. About 1 row in 4 of it is of a postcode that is still in use: `doterm` is empty for those.

What was saved from it: the licence section of the guide, as `registry/evidence/ons-postcode-directory-2026-09-24.txt`. The three statements of the registry's attribution are the guide's, letter for letter. `attribution_verified` was left as it was, for a person to set.

## Credit

| File | Credit |
|---|---|
| Stops and stations, schools, recorded crime | Contains public sector information licensed under the Open Government Licence v3.0 |
| Postcode directory | Contains OS data © Crown copyright and database right 2026. Contains Royal Mail data © Royal Mail copyright and database right 2026. Source: Office for National Statistics licensed under the Open Government Licence v.3.0 |
