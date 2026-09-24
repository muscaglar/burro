# Pages read for the source-by-source plan

Read on 2026-09-23 for [london-data-sources.md](../../design/london-data-sources.md). A dated snapshot, not a source of truth.

Every page was read through a reader that summarises. The tool can paraphrase and can misread a number. Check each by eye before it is relied on. No dataset was downloaded and no data file was opened. Where a listing of file names and sizes was read, the files themselves were not fetched. Nothing here is legal advice.

## What was read, and what it said

| Page | What it said |
|---|---|
| Nomis, Census 2021 bulk data (`nomisweb.co.uk/sources/census_2021_bulk`) | "Bulk data products package all the data from a 2021 Census dataset as a single zip file. Each zip file contains separate CSV files for each geographic type (OA, LSOA, MSOA etc)". A second zip, marked "-extra", holds 2021 wards. TS003, TS004, TS007A, TS021, TS030, TS044, TS050, TS054 and TS068 are listed. No sizes. Footer: "© Crown Copyright" |
| Nomis, TS007A (`nomisweb.co.uk/datasets/c2021ts007a`) | "TS007A - Age by five-year age bands". Units: persons. The page does not list the geographies it is published for |
| ONS data service, TS007A, version 3 | Not read. The vibes research did not read it either |
| data.police.uk, custom download | Dates from August 2023 to July 2026. Three tick boxes: crime, outcomes, stop and search. The Metropolitan Police Service, City of London Police and British Transport Police are on the form. CSV |
| data.police.uk, archive | One zip a month, each holding about three years. Recent zips are about 1.5 to 1.6 GB. They hold "crime, outcome, and stop and search data". An MD5 sum beside each. All but the latest "is out of date and should not be used" |
| GOV.UK, Price Paid Data downloads | Latest month July 2026, released 28 August 2026. Yearly files "from 115 MB to 230 MB". The attribution statement and the Royal Mail wording are as the registry records them |
| GOV.UK, UK House Price Index downloads, July 2026 | A full file and one file for each attribute, all CSV. The sizes are not known |
| ONS, Price Index of Private Rents dataset page | Latest release 16 September 2026. Next release 21 October 2026. One Excel file, 17.8 MB. OGL v3 footer. The page does not describe the layout |
| ONS, LSOA mid-year population estimates | Latest edition mid-2022 to mid-2024, released 7 November 2025. XLSX, 83.4 MB. OGL v3 footer |
| GOV.UK, Council Tax: stock of properties 2025 | CTSOP1.1 zip 732 KB, CTSOP3.1 zip 7.53 MB, CTSOP4.1 zip 5.87 MB, all by local authority and lower and middle super output area, at 31 March 2025. OGL v3 footer. The vintage of the areas is not stated |
| GOV.UK, English Indices of Deprivation 2025 | Published 30 October 2025, updated 17 November 2025. File 8, underlying indicators, Excel, 13.8 MB. File 7, all ranks and scores, CSV, 9.44 MB. OGL v3 |
| GOV.UK, Land use in England 2022 | Published 27 October 2022. "Live tables by LSOA and MSOA", ODS, 36.4 MB. Live tables, ODS, 2.32 MB. OGL v3 footer |
| GOV.UK, Ofsted monthly management information | As at 31 August 2026, page updated 10 September 2026. "Latest inspections" CSV 16.3 MB. The full file ODS 10.4 MB. No licence footer was returned |
| Get Information About Schools, downloads | Establishment fields CSV 61.68 MB. Establishment links CSV 2.4 MB. Children's centre fields CSV 0.74 MB. Governor fields CSV 31.99 MB, which is never ingested. "This data is updated daily". OGL v3 footer |
| Food Standards Agency, open data | XML files grouped by local authority, updated daily, with a complete CSV and an API in XML and JSON. 33 files for London. "Terms and conditions apply" |
| Overture Maps, Places guide | Latest release 19 August 2026. GeoParquet on Amazon S3 and Azure. A bounding box can be cut with the Python client or with DuckDB. Records by source: Meta 58,489,657, Microsoft 6,278,097, Foursquare 4,630,865, BrightQuery 2,289,171, AllThePlaces 1,609,565. "The `categories` property in the places schema has been deprecated and will be removed in the September 2026 release" |
| planning.data.gov.uk, listed building | 382,270 records, one provider. CSV, JSON, GeoJSON and Parquet. "Licensed under the Open Government Licence v.3.0". Attribution: "© Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026. The Historic England GIS Data contained in this material was obtained on [date]. The most publicly available up to date Historic England GIS Data can be obtained from HistoricEngland.org.uk". "The data may be incomplete and not yet cover all of England" |
| planning.data.gov.uk, conservation area | 10,953 records from 151 providers. The same formats, licence line and attribution. It "contains a number of duplicate conservation areas" |
| Ordnance Survey, OS Open Greenspace product page | Shapefile, GeoPackage, GML and vector tiles. Great Britain. "Updated every six months". "Free to use for everyone" |
| Ordnance Survey, downloads listing, file names and sizes only | OS Open Greenspace: GeoPackage zip 59,489,052 bytes; shapefile zip 39,508,821; the TQ tile as a shapefile 5,184,042. OS Open Roads: GeoPackage zip 1,016,021,285; shapefile zip 606,145,264. OS Open Names: CSV zip 103,259,564. OS Open Rivers: GeoPackage zip 52,490,978. Boundary-Line: GeoPackage zip 807,724,473; GML zip 167,677,814 |
| Geofabrik, Greater London | `greater-london-latest.osm.pbf`, 123 MB, with data to 2026-09-22T20:22:59Z. "License: ODbL 1.0". The page does not say whether the extract has a buffer |
| Transport for London, our open data | Journey Planner timetables: zip, 24.31 MB, for "London Underground, bus, DLR, tram, cable car and river services". Published every 1,440 minutes, 10 minutes from capture to display, 1,440 minutes on display. "The timetables are updated every 7 days. They do not take account of planned engineering works" |
| Department for Transport, NaPTAN download page | National data, or by local authority. CSV or XML. OGL v3 footer. No size |
| UK-AIR, modelled background pollution data | CSV on a 1 km grid, in British National Grid coordinates, with data from row 6. Latest year 2024. Maps are made over the summer and are usually out by mid-October. OGL v3 footer |
| Ofcom, Connected Nations update, Spring 2026 | Fixed coverage and full fibre take-up: zip, 32.2 MB, January 2026 snapshot, published 13 May 2026. Mobile coverage: zip, 254 KB. The page points to Ofcom's terms of use for the licence |
| NHS Business Services Authority, Consolidated Pharmaceutical List | "Open Government Licence 3.0 (United Kingdom)". One CSV a quarter, from 2022-23. Latest 2026-27 quarter 1, updated 18 August 2026. No column list on the page |
| Forest Research, Trees Outside Woodland map | Available under the Open Government Licence. GeoPackage and shapefile. Trees from 3 m tall. The page gives no sizes, no date range and no accuracy figure |
| GitHub, hosted runners and limits | A standard Linux runner for a public repository has 4 cores, 16 GB of memory and 14 GB of disk. "Each job in a workflow can run for up to 6 hours". Cache storage is 10 GB a repository |

## What was not read

| Page | Standing |
|---|---|
| Defra Data Services Platform, the Trees Outside Woodland dataset page | Not read. The London file's size is unknown |
| Active Places, downloads | Not read. The size and the list of files are unknown |
| ONS data service, TS007A | Not read. Whether age by five-year bands is published for output areas is still unconfirmed |
| Arts Council England, parkrun | Not read. The vibes research did not read them either |

## Not checked at all

Every statement in the plan marked M is from memory. Every statement marked E is an estimate. The main ones:

| Statement | Why it matters |
|---|---|
| The Price Paid files have no header row, and late registration thins the latest months | The ingest step and the window of months |
| The police files carry an LSOA code whose vintage is unknown | Rates by area |
| The Ordnance Survey GeoPackage can be opened as an SQLite file with no system library | Where the build can run |
| A London cut of Overture Places is 0.1 to 0.3 GB | Disk and time. Guessed from the world count and London's share of people |
| The ONS postcode directory is some hundreds of MB | Disk |
| A log or an artefact of a public repository can be read by anyone | No raw row may be printed or uploaded |
| Every compute time in section 5 of the plan | Nothing was run |
