# London data, source by source

Status: design, 2026-09-23. It follows [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md). Nothing here is built. No dataset was downloaded or opened for it. It changes no registry entry, no rule and no other document: each change it points to is made by that file's owner, in the same change as the code. Nothing here is legal advice.

Files have been fetched since it was written: 62 files of 24 approved sources, on 2026-09-23. [The plan for real data](london-data.md) names each source, and says that the files are kept outside the repository and that nothing of them is published. Where a row below says that a size or a layout is not known until a file is opened, the pages under `docs/research/data/` that are named for the builds `m1`, `m2` and `m3` say what was found in the files that were fetched. No row below was changed.

Written before the registry held the six entries that rest on a permission in writing, as the founder reports: parkrun's events, the two canopy layers of the Greater London Authority, and the three lists of Arts Council England. Where this document says that one of them is not registered, or that it waits on an answer, [the plan for real data](london-data.md) and the registry stand.

It gives the ingest plan for every source the registry approves (41) and every source the vibes research proposes. Then: the order to ingest them in, what each vibe waits on, what each of the founder's eight points still lacks, and the smallest release of all of London that is honest to launch.

## 0. What this document assumes about the other parts

Five other parts are being written at the same time, and were not read.

| Part | Assumed here |
|---|---|
| Named areas | A reviewed file gives each of London's 26,369 output areas (OAs) to one named area, about 450 in all. Every figure below is worked out per OA or LSOA first and rolled up last, so ingest does not wait for the map. Until the map exists a preview rolls up to the 1,002 MSOAs, shown to nobody outside |
| Release and evidence | The release of contract section 2, plus what ADR 0014 adds: every record keeps its source, the date of the data, the date retrieved and the method. Census figures sit in a file of their own |
| Where a build runs | Any place with outbound HTTPS to the publishers and Python. Routing also needs Java. Section 8 says what each kind of step needs |
| Travel times | Another part designs the routing build. This one lists its inputs |
| A model at build time | Another part designs it. No source below needs a model to be ingested: each is a file or an API that code fetches. Section 9 lists the gaps a model might help with |
| Census panel | Another part designs the page and the registry's new heading. This one lists the tables and how they are summed |
| Vibes | [vibes.md](vibes.md) section 2.2 as written, with its redefinitions: a part is a share of homes or a walk from homes. V1 to V14 below are its 14 vibes in order |

## 1. How to read the tables

| Mark | Meaning |
|---|---|
| R | Stated in this repository's registry or research. Not re-read for this document |
| W | Read on the publisher's own page on 2026-09-23, through a reader that summarises. Wording must be checked by eye before it is relied on. The pages are listed in [the reading log](../research/data/sources-pages-read.md) |
| M | From memory. Unverified |
| E | An estimate. The method is given where it first appears |
| ? | Not known until the file is opened |

| Word | Meaning here |
|---|---|
| Home | An OA's population-weighted centroid, weighted by the OA's households in Census table TS044 |
| Walk | The shortest path on OS Open Roads from a home. 10 minutes is taken as 800 m and 15 as 1,200 m. A first guess |
| Roll-up | Counts are summed over an area's OAs. Rates and shares are means over its homes. An LSOA's value is given to each of its OAs first |
| V1 to V14 | Homes, Built age, Village feel, Quiet streets, Works and warehouses, Pace, Food and drink, Leafy, Parks close by, Culture on the doorstep, Places to train, Places to meet, Family amenities, Everyday on foot. "V4 30" means 30 hundredths of that recipe |

"To settle before launch" leaves out one item that holds for every row: open the licence page in a browser, save it in `registry/evidence/`, and confirm the attribution wording. 37 such items are open today R.

## 2. The 41 approved sources

### 2.1 Geography and names

| Source | File or API | Format, size | Licence. To settle before launch | Joins on | Becomes a figure by | Feeds | Changes | Traps | London |
|---|---|---|---|---|---|---|---|---|---|
| `ons-oa21-lsoa21-msoa21-lad22-lookup` | Open Geography Portal, best-fit lookup V2 | A table behind a map service, also CSV M. About 179,000 rows for England M | OGL v3. ONS line only | `OA21CD`, `LSOA21CD`, `MSOA21CD`, `LAD22CD` | Not a figure. It is the spine: London is the rows whose `LAD22CD` starts `E09` R | Every join. Borough names and outlines | When geographies change. Pin V2 | The service returns rows in pages M. Count them against 26,369 before use | All: 26,369 OAs, 4,994 LSOAs, 1,002 MSOAs, 33 boroughs R |
| `ons-output-areas-2021` | Portal items: OA boundaries BGC V2 (display) and BFC V8 (joins) | GeoPackage, shapefile or GeoJSON M. Size ? | OGL v3. ONS and OS lines, year of supply | `OA21CD` | Not a figure. It is the cell. An area's outline is the union of its OAs | `geometry.json`. Every point-in-area join | Fixed until the 2031 census | British National Grid, so reproject to WGS84. A national file: keep London rows only. Never serve the full-resolution file | All |
| `ons-oa-pwc-2021` | Portal item, OA centroids V4 | CSV or GeoJSON M. About 189,000 points for England and Wales M | OGL v3. Wording rests on an inference R | `OA21CD` | The point where an OA's homes are taken to stand | The start of every walk. Every "share of homes" | Fixed | A centroid can land in a yard or a park. Weights are from 2021, so homes built since carry none | All |
| `ons-lsoa-2021` | Portal item, LSOA boundaries BGC V5 | As above. Size ? | OGL v3 | `LSOA21CD` | LSOA land area in hectares, for density | `homes_density`. Placing grid data | Fixed | Can be made by dissolving OAs instead, which nests exactly | All: 4,994 R |
| `ons-lsoa-pwc-2021` | Portal service `LSOA_PopCentroids_EW_2021_V4` | CSV or GeoJSON M | OGL v3 | `LSOA21CD` | Where each journey starts (ADR 0003) | `travel.json` origins | Fixed. Pin V4 | A large LSOA hides variation. Times from these points carry the OSM credit R | All: 4,994 |
| `ons-msoa-2021` | Portal item, MSOA boundaries BGC V3 | As above | OGL v3 | `MSOA21CD` | Preview areas before the named map. Units for the price check | Validation. Preview only | Fixed | MSOAs do not nest in named areas R. Never the launch geography | All: 1,002 R |
| `ons-postcode-directory` | ONS postcode products page, quarterly ONSPD | Zip of CSV. About 2.7 million UK rows, some hundreds of MB M | OGL v3 with OS and Royal Mail lines. Save the licence section of the user guide from the zip R | Postcode, to `oa21` and a grid reference | Places every record that has only a postcode | Price Paid, NHS sites, pharmacies, rent districts, postcode search | February, May, August, November R | Drop every `BT` row. Keep ended postcodes: old sales use them M. A postcode's point is not the building. Never pass on the raw file | All |
| `ons-lsoa-population-estimates` | ONS dataset page, mid-2022 to mid-2024 | XLSX, 83.4 MB W | OGL v3. Attribution wording: a question for the statistics office | `LSOA21CD` | Residents per LSOA, the total only | Denominator of crime rates. `rankable`: an area under 3,000 residents is not ranked | Annual. Released 7 November 2025 W | The file also holds age and sex: read the total column and nothing else. The figure never enters a release (ADR 0010) | All |
| `os-boundary-line` | OS Data Hub, GB file | GeoPackage zip 770 MB, GML 160 MB W | OGL v3. Save the licence file from the zip | GSS code | Ward names as evidence for area names | Naming only | Spring and autumn R | Not needed for borough outlines: dissolve OAs by `LAD22CD` R. Large for what it gives | Borough and ward layers unconfirmed R |
| `os-open-names` | OS Data Hub, GB file | CSV zip 98.4 MB W | OGL v3. Save `licence.txt` | None. Point to OA | Name seeds for areas. Districts and roads for `places.json` | The named map. Destination search | January, April, July, October R | Drop postcode records R. How many London neighbourhood names it holds is unmeasured R | All, coverage ? |
| `os-open-roads` | OS Data Hub, GB file | GeoPackage zip 969 MB, shapefile 578 MB W | OGL v3. Save the licence file | None. Links and nodes | The walking network. `road_major_exposure`: share of homes within 100 m of an A road or motorway | Every walk. V4 40. The split of OAs between areas | April and October R | No footpaths, so a walk through a park or an alley is overstated R. Take motorways out of the walking graph. Road class is not traffic. Never blended with OSM | All |
| `uber-h3` | The `h3` library | Software. Resolution 9 gives about 16,700 cells R | Apache 2.0. Notice travels with any shipped bundle | Cell id | Where journeys end | `destinations.json` | Never. Pin library and resolution | Compiled code inside the package R | All |
| `wikidata-places-and-landmarks` | Wikidata Query Service, or a dump | JSON. 720 "area of London" items, 717 with coordinates R | CC0 | QID. Coordinates to OA | Name seeds and aliases. Universities, hospitals and landmarks as places to reach | The named map. `places.json` | Continuous. Snapshot per release, QID and date kept | Coordinates can be arbitrary R. Closed places stay listed. Never select through OSM tags R. Registered for no `scoring` use | Landmark coverage unmeasured R |
| `gla-town-centre-boundaries` | London Datastore, one file | GeoPackage, 1.63 MB R | OGL v3. GLA disclaimer on the attributions page. `display` added before a centre is named | None. Polygon to homes by walk | `highstreet_access`: share of homes within a 10-minute walk of a centre. `centre_small`, `centre_compact`: from the polygon's class, or its area and shape if it has none | V3 40, V6 20, V12 10, V14 25. Seeds | Irregular R | Boundaries are "indicative" R. Whether a polygon carries its class or its name is ? | All boroughs by design. Count of centres ? |

### 2.2 Transport and basemap

| Source | File or API | Format, size | Licence. To settle before launch | Joins on | Becomes a figure by | Feeds | Changes | Traps | London |
|---|---|---|---|---|---|---|---|---|---|
| `osm-geofabrik-greater-london` | Geofabrik, `greater-london-latest.osm.pbf` | PBF, 123 MB W | ODbL. Credit on the map and beside every journey time. Methods page names the extract date | None. The router reads it whole | Streets for walking, cycling and the ends of a public transport journey | `travel.json` | Daily W. Pin one per release | Routing only (ADR 0004). The registry asks for a buffer of a few km; whether this extract has one is ? | All |
| `tfl-journey-planner-timetables` | TfL API portal. Needs a registered account | Zip of TransXChange XML, 24.31 MB W | TfL terms. A question for TfL: may a quarterly snapshot be shown. Save the terms at every release | Stop `ATCOCode` | Converted to GTFS, routed from each LSOA centroid to each cell, rolled up to area by destination | `pt_typical`, `pt_just_missed`. `station_lines`. The night-service line | Weekly W | No Overground, Elizabeth line or National Rail R, so `station_lines` undercounts without rail. No engineering works. The zip linked on the page is an example that is not updated R. The conversion is unproven R | Tube, bus, DLR, tram, river, cable car |
| `tfl-step-free-station-topology` | `tfl-stationdata-gtfs.zip`, `tfl-stationdata-detailed.zip` R | Zip of CSV. Size ? | TfL terms. Save the data guide | Station id. The match to NaPTAN is ? | `step_free` for a station. Fare zone from `Stations.csv` R | `stations.json`. No vibe | No frequency stated R | Lists step-free paths only. A blank is unknown, never "no" R | TfL-served stations and part of Thameslink R |
| `tfl-unified-api-journey-planner` | Live API, with a key | JSON. 500 calls a minute R | TfL terms. Two more questions for TfL | Place coordinates | Not ingested. Route detail when a result is opened. About 1,000 checked pairs a release R | Validation of `travel.json` | Live | Never builds the matrix. National Rail legs are shown as returned and not stored R. The key stays on the server | All modes |
| `dft-naptan` | `naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv` R, or by local authority W | CSV or XML W. Size ? | OGL v3. Name DfT beside it | `ATCOCode`. Coordinates to the walk network | `station_walk`: minutes on foot from each home to the nearest station entrance, mean over homes | V14 20. `stations.json`, `places.json`, stops for the timetables | Daily R | One station is many nodes: entrances, platforms, a stop area. Group before counting. Drop inactive stops M | All modes, rail included |
| `protomaps-basemap-london` | Protomaps daily build, cut to London | PMTiles. Planet about 120 GB; London size not known R | ODbL produced work. "© OpenStreetMap" in the map corner | None | Not a figure. The map under the areas | Display | Daily. One per release | Cutting the extract needs a command-line tool. Never read features out of tiles R | All |

### 2.3 Housing and cost

| Source | File or API | Format, size | Licence. To settle before launch | Joins on | Becomes a figure by | Feeds | Changes | Traps | London |
|---|---|---|---|---|---|---|---|---|---|
| `hmlr-price-paid` | GOV.UK, yearly files | CSV. 115 to 230 MB a year W. The single file is 5.3 GB R | OGL v3, with address fields under Royal Mail terms. A question for HM Land Registry | Postcode, through ONSPD, to OA | Per area and property type: lower quartile, median and upper quartile of 36 months of sales, each moved to the release month by UK HPI. Rounded to 5,000. Confidence by count: 50 and 10 (contract 2.5) | `cost.json`, buy. The flat-price ratio in the rent model | Monthly. Latest July 2026 W | No header row M. Drop every address column but postcode at ingest R. Leave out category B and type "other" M. Recent months are thin: sales register late M. No bedrooms R. No row in a log, an artefact or a fixture | All. Thin where few homes sell |
| `hmlr-uk-house-price-index` | GOV.UK, UK HPI downloads | CSV. Size not confirmed: the tool read "34KB" W | OGL v3. Show the index month | Borough code, month, property type | The index that moves a sale to the release month | `cost.json` | Monthly. Latest 12 months revised R | Record the release used. A borough with few sales has a jumpy series M | 33 boroughs ? |
| `ons-price-index-of-private-rents` | ONS dataset page | XLSX, 17.8 MB W | OGL v3. Attribution wording: a question for the statistics office, or the workbook's cover sheet | Borough code, bedrooms | The borough anchor of the rent model | `cost.json`, rent | Monthly. Next 21 October 2026 W. Last two months provisional R | Layout never opened R. All tenancies, so it understates a new let R. No room or studio figure ? | 32 boroughs. City of London not published R |
| `ons-private-rental-market-london-postcode-district` | ONS ad hoc 3389, `londonrentalstatsaccessibleq12026.xlsx` R | XLSX, 129.4 kB R | OGL v3. Save the workbook's caveat. A question for the statistics office: does the series continue | Postcode district and bedrooms. District to OA through ONSPD, by households | A ratio inside each borough that moves the anchor. Never shown raw | `cost.json`, rent | Frozen: no edition since April 2026 R. Archive all nine | ONS says the figures should not be compared between areas R. Burro does so inside a model, and must say so. Under 5 observations is suppressed R | 247 of 329 districts have a median. Gaps in W1 and the City R |
| `voa-council-tax-stock-of-properties` | GOV.UK: CTSOP1.1, CTSOP3.1, CTSOP4.1 | Zip: 732 KB, 7.53 MB, 5.87 MB W. Contents ? | OGL v3. Read each notes sheet for a source line | LSOA code, vintage ? | `homes_flats`: flats over all homes. `homes_pre1919`, `homes_post2000`: build-period bands over all. `homes_density`: homes over hectares. Counts summed, then divided | V1 75, V2 55, V3 20. `built_since` | Annual. As at 31 March 2025 W. The 2026 edition is due about now | Counts rounded to 10 R. The build-period bands are not yet read R. A band is not a price | All LSOAs R |
| `ons-census-2021-housing-tables` | Nomis bulk: TS044, TS050 | One zip per table, a CSV for each geography W. Size ? | OGL v3. "Source: Office for National Statistics" | `OA21CD` | Households per OA: the weight behind "home". Bedrooms mix for cost segments | Weights. Profile text | Once. 21 March 2021 | Households, not dwellings. Empty homes are missing R. Taken in lockdown | All |
| `ons-census-2021-tenure-ts054` | Nomis bulk: TS054 | As above | OGL v3 | `OA21CD` | Private-rented share, summed over OAs | Area page only. Never a score R | Once | Describes households. Which shares may be shown is open for the founder | All |
| `ons-median-house-prices-msoa` | ONS dataset page | XLSX, 65.3 MB R | OGL v3. Never shown | `MSOA21CD` | A test: Burro's medians, summed again to MSOAs, against ONS's | Validation only | Twice a year R | MSOAs do not match areas | All |

### 2.4 Places, schools, heritage, safety, environment, text

| Source | File or API | Format, size | Licence. To settle before launch | Joins on | Becomes a figure by | Feeds | Changes | Traps | London |
|---|---|---|---|---|---|---|---|---|---|
| `fsa-food-hygiene-ratings` | ratings.food.gov.uk: one file per local authority, or the API | XML or JSON. 33 London files W. Size ? | OGL v3. Does printing a count need `display`: open for the founder | `FHRSID`. Longitude and latitude, else postcode through ONSPD | Venues within a 10-minute walk of each home, by business type, mean over homes. "Independent" is a name seen at fewer than N sites, N published | V3 25, V4 30, V6 65, V7 80, V14 25. The pub as a kind in V12. Hotels line | Daily W | No cuisine and no brand field R. Schools, hospitals and makers are in the file: keep venue types only. Some records have no location M. Never a rating, never a row. The data date beside every count R | All 33 authorities W |
| `overture-places` | Overture release on S3 or Azure, cut by bounding box W | GeoParquet. London cut about 0.1 to 0.3 GB E | CDLA-Permissive 2.0, Apache 2.0, CC0 by record. Copy the attribution again for the pinned release | Point to OA. Never the GERS id R | Counts and kinds within a walk of homes | V6 15, V7 20, V10 80. Halls as a kind in V12 | Monthly. Latest 2026-08-19 W | London quality is unmeasured: the spike comes first. A zero is unknown. `categories` is gone from September 2026 W: build on `basic_category` and `taxonomy`. Aggregates only. Keep `sources` so Foursquare and AllThePlaces rows can be dropped | All, quality ? |
| `dfe-gias` | GIAS downloads: establishment fields, children's centre fields | CSV, 61.68 MB and 0.74 MB W | OGL v3. Attribution verified R | `URN`. Easting and northing to OA | `school_primary_nearby`: open state primaries within 800 m of homes, in a straight line. `childrens_centre_proximity` | V13 40. A kind in V12. Schools in `places.json` | Daily W | Drop head teacher names and pupil intake columns R. Religious character is never read R. Universities are not in it R, so `university_proximity` has no source today | All |
| `ofsted-state-funded-schools-mi` | GOV.UK, "latest inspections" | CSV, 16.3 MB W | OGL v3. Save the page footer | `URN` | The published outcome and its date, shown as they are | Beside V13. Never inside | Monthly. As at 31 August 2026 W | Three regimes that do not compare. No composite grade R | All state schools |
| `nhs-ods` | Data Search and Export, CSV reports | CSV. Size ? | OGL. `scoring` and `display` added, with evidence, before `gp_walk` | ODS code. Postcode through ONSPD | Hospital sites as places to reach. With the uses added: `gp_walk` | `places.json`. V14 15 once widened | Nightly R | Placed by postcode. Closed sites and branch surgeries. Near is not able to register | All |
| `historic-england-listed-buildings` | planning.data.gov.uk | CSV, JSON, GeoJSON or Parquet. 382,270 records for England W | OGL v3. The page's attribution has two more sentences than the registry holds W | List entry reference. Point to OA | `listed_buildings`: entries in an area for each 1,000 homes | V2 20 | Collected daily W | "May be incomplete" W. One entry can be a whole terrace M. No field for the kind of building R | All. London count ? |
| `mhclg-planning-data-conservation-areas` | planning.data.gov.uk | The same formats. 10,953 records from 151 providers W | OGL v3. The same longer attribution W | None. Polygons over homes | `conservation_cover`: share of homes inside any conservation area, after the polygons are merged | V2 25, V3 15 | Collected daily W | Holds duplicates W. An authority that sent nothing is unknown, not zero R | Coverage of the 33 authorities unchecked R |
| `police-uk-street-level-crime` | data.police.uk custom download: crime only, three forces | Zip of CSV, one for each force and month. August 2023 to July 2026 W | OGL v3 | The snapped point, to OA. The row's own LSOA code has vintage ? | Recorded crimes a year for each 1,000 residents, by category group, over 24 or 36 months | `crime_*`. Beside, off by default. No vibe | Monthly | The archive zips, 1.5 GB each, hold stop and search W, which must never be downloaded R: use the form. Points are snapped | Met months missing in 2024. Transport police absent from March 2025 R |
| `defra-pcm-background-air` | UK-AIR, one file for each pollutant and year | CSV, 1 km grid, data from row 6 W. Size ? | OGL v3. Attribution year is the year on UK-AIR at retrieval | Grid square, by easting and northing | `air_no2`: the square each home falls in, mean over homes | Beside V4 and V6. No vibe | Annual. Latest 2024. 2025 due by mid-October W | Modelled background, not the kerb. Files are reissued: keep a checksum R | All |
| `mhclg-iod-2025-underlying-indicators` | GOV.UK, File 8 | XLSX, 13.8 MB W. Eight sheets R | OGL v3. Save the notes sheet. One allowlist row for each column used | `LSOA21CD` | `noise_exposure`, `private_outdoor_space`: the LSOA's value, mean over homes. `incident_criminal_damage` beside | V4 30, V1 25 | Irregular. 2025, before that 2019 | Read named columns only: the file also holds income and health R. Noise is a share from 0 to 1, of residents, not of homes R. Outdoor space waits on its audit row | 4,994 of 4,994 LSOAs R |
| `os-open-greenspace` | OS Data Hub, GB file | GeoPackage zip 56.75 MB. The TQ tile alone is 4.94 MB W | OGL v3. Save `licence.txt` | Site id. Access points to the walk network | `green_cover`: share of homes within 300 m of a Public Park or Garden. `park_proximity` (2 ha), `park_large_proximity` (20 ha), `play_space_proximity`: walk to the nearest access point. `park_facilities`: kinds within 15 minutes | V8 30, V9 100, V11 20, V12 10, V13 60 | April and October R | No common, heath or woodland kind R: check 20 named sites first. A cemetery or golf course never counts. One park can be several polygons. The name field is unchecked R | All, with that gap |
| `os-open-rivers` | OS Data Hub, GB file | GeoPackage zip 50.06 MB W | OGL v3 | None. Lines | `water_access`: share of homes within 300 m of a river or canal line | Waterside chip. "A river runs through this area" | Six-monthly R | Centre lines with no width: 300 m from the middle of the Thames is about 175 m from its bank E. Small drains may be in it ? | All |
| `wikimedia-wikipedia-excerpts` | MediaWiki API, lead extract | JSON. About 700 articles R | CC BY-SA 4.0. Shown verbatim with link, licence and "shortened" | Wikidata QID to article. Revision id kept | Not a figure. A quoted paragraph | Area page only | Continuous | Never sent to a model. Never scored R. An excerpt can describe residents in Wikipedia's words: section 10 | 703 of 720 area items have an article R |

## 3. The ten gated sources

| Source | It would give | What opens the gate | If it stays shut |
|---|---|---|---|
| `network-rail-nwr-schedule` | Rail, Overground and Elizabeth line timetables (CIF, daily). Joins on station codes to NaPTAN | A Rail Data Marketplace account, the executed agreement saved, and a question for Network Rail on territory and attribution | No rail time may be shown R. Much of south London has no honest journey time, so no launch |
| `dfe-school-performance-tables` | Attainment at nearby schools, by `URN`. Shown beside V13 | The founder opens the download page in a browser and saves its footer | School results are left out. V13 is unaffected |
| `gla-cultural-infrastructure-map-2023-gla-commissioned-layers` | Venue points by kind, a second source for V10 | A question for the GLA | V10 rests on Overture alone |
| `gla-high-street-boundaries` | A second anchor for `highstreet_access`, 4.22 MB R | Nothing. Approved for scoring on 2026-09-24, on the licence its page shows (ADR 0007). The file is read for a statement of rights at first ingest | Town centres cover it R |
| `hoc-library-msoa-names` | Names for MSOAs: a prior for the named map and for the preview | The founder opens the Open Parliament Licence page and saves it | The preview shows codes, not names |
| `os-code-point-open` | Postcode points | `Doc/licence.txt` read from the zip | Nothing: ONSPD covers it R. Recommend it is dropped |
| `geolytix-retail-points` | Grocery chains, a second source for `grocery_walk` | A question for the publisher, or a licence file in the download | `grocery_walk` rests on the food register's business type |
| `ons-census-2021-protected-characteristics` | The audit tables of vibes.md 6.1 | A store the product cannot read, its CI check, and the written audit rule | No vibe can hold a flag on a real release. This gate sits in front of every vibe |
| `osm-place-nodes`, `openstreetmap-points-of-interest` | Aggregate checks of names and venues | A CI test that no feature table reads OSM | Checks use Wikidata and the food register |

## 4. Sources the vibes research proposes

None is in the registry. Each keeps the id its report gave it. "Proposed" is the status that report asked for.

| Source, proposed status | File or API | Format, size | Licence. To settle | Joins on | Becomes a figure by | Feeds | Changes | Traps | London |
|---|---|---|---|---|---|---|---|---|---|
| `mhclg-land-use-statistics-2022`, gated | GOV.UK, "live tables by LSOA and MSOA" | ODS, 36.4 MB W | OGL v3 W. Read the table's notes for OS terms | LSOA code, vintage ? | Share of each LSOA's land in a category, mean over an area's homes | V5 100. V8 first recipe 70. Offices and retail for the lived-in line | None since 27 October 2022 W. As at April 2022 | Build from categories, never the "Industry and commerce" group R. Units ?. It is a share of land, not a distance from a home. A large ODS is slow to read | All, by the publisher's account R |
| `forest-research-trees-outside-woodland-v1`, approved | Defra data platform, `FR_TOW_V1_London.zip` R | GeoPackage or shapefile W. Size ? | OGL v3 R. Read the accuracy report | None. Polygons cut by OA | `canopy_cover`: canopy over land. `street_canopy`: share of street length with canopy within 10 m | V8 second recipe 60 | First release, April 2025. Data 2017 to 2024 R | Leaves out woodland, so it needs the forest inventory. Roads are "removed", which may cut street crowns R. The platform page was not read W | All R. Accuracy ? |
| `forestry-commission-national-forest-inventory-england-2024`, gated | Forestry Commission open data | Polygons. 361,039 records for England R | "Custom License", not opened R | None | The woodland part of `canopy_cover` | V8 | Annual R | Holds felled and newly planted land R | All |
| `sport-england-active-places`, approved | Downloads page: zip of CSV, JSON, or an API at 120 calls a minute R | About 125,000 facilities at 43,000 sites R. Size ? | CC BY 4.0 R. Read the information file in the zip. A question for Sport England | `Site ID`. The file carries OA and LSOA codes R | `gym_choice`: operational public gyms within 15 minutes of homes. `pool_proximity`, `court_pitch_kinds`, `sports_facility_nearby` | V11 80, V12 20. Kinds of gym beside V11 | Nightly. Each site audited yearly R | Drop contact names, addresses and UPRN R. Count Operational only. Gyms under 5 stations, climbing and boxing are absent R. The downloads page was not read W | England. London count ? |
| `ofcom-connected-nations-spring-2026-fixed-coverage`, approved | Ofcom zip. Inside: `202601_fixed_oa_res_coverage_r1.csv` R | Zip, 32.2 MB W. 238,850 UK rows R | OGL v3 R. PLAN section 4 lists broadband as out | `OA21CD` | `broadband_gigabit`: premises with gigabit summed over OAs, over premises summed | A line on the portrait. Weighed only if it varies | January and July snapshots | Gigabit-capable, never "full fibre" R. The spread across London is unmeasured | All OAs ? |
| `nhsbsa-consolidated-pharmaceutical-list`, gated | NHSBSA open data portal | CSV, one a quarter W. Size ? | OGL v3 W. Open one file | ODS code. Postcode through ONSPD | `pharmacy_walk` | V14 15 | Quarterly. Latest 18 August 2026 W | Postal-only pharmacies and appliance contractors must be left out. The column that tells them apart is ? W | England |
| `arts-council-england-libraries-basic-dataset`, gated | Arts Council page. Not read R | ? | Not read. The founder opens and saves the page. A question for the owner if it is silent | Postcode or coordinates ? | `library_proximity` | V10 20, V12 20 | Annual R | Closed libraries. No other library source is usable: the GLA layer is held and the DCMS list is from 2016 R | ? |
| `arts-council-england-accredited-museums`, `arts-council-england-national-portfolio`, gated | The same site | ? | Not read | Address ? | "Recognised" venues, each with its scheme and date | Shown beside V10 | By round | An office is not a venue. Recognition follows age and money R | ? |
| `wikidata-cultural-venues`, approved | Wikidata Query Service | 2,061 items, 1,960 with coordinates, 181 with a closing date R | CC0 | QID | A cross-check on Overture by kind. Names of public institutions | Beside V10. "Go and look" | Continuous | Keeps closed venues. Never the only evidence R | Uneven |
| Census tables for the area page: `ons-census-2021-life-stage-tables`, `ons-census-2021-origin-and-belief-tables` | Nomis bulk: TS007A age, TS003 household type, TS004 country of birth, TS021 ethnic group, TS030 religion | One zip per table, a CSV for each geography W. Size ? | OGL v3. Needs the registry's new heading and its display-only rule. The audit entry still forbids "any page" and changes with it | `OA21CD` | Counts summed over an area's OAs, then each category over the total, as a whole percent. Under 1% reads "under 1%" | The census table on an area's page. No feature, no vibe, no score | Once. 21 March 2021 | Main language (TS024) is published for boroughs only R, so it cannot be shown for an area. TS007A at OA level is expected and unconfirmed R W. ONS swaps and nudges small counts, so sums over about 59 OAs carry noise R. TS003 counts households. Students (TS068) are not in ADR 0014's list | All OAs |
| `historic-england-registered-parks-and-gardens`, `historic-england-world-heritage-sites`, approved | planning.data.gov.uk | 1,723 and 40 records for England R | OGL v3 R | None. Polygons | A fact on the page. Names for "Go and look" | No recipe in vibes.md | Collected daily | Some registered gardens are private R | London counts ? |
| `natural-england-local-nature-reserves` approved, `natural-england-ancient-woodland` gated | planning.data.gov.uk | 1,731 records for England R | OGL v3 R | None. Polygons | A fallback if London's commons and woods are missing from OS Open Greenspace | V9, only if the commons check fails | Collected daily | A designation is not a way in R | ? |
| `ofsted-childcare-providers`, gated | GOV.UK, provider-level file | ? | OGL v3 footer only R | Provider id ?. Postcode | Nurseries within a walk | Not in V13 as written. ADR 0006 names nurseries | Twice a year R | Drop every childminder and home address R | England |
| `openactive-opportunity-feeds`, gated | One feed per operator | JSON feeds | CC BY 4.0, by publisher R | Venue point | Venues with a weekly session | A kind in V12, later | Live | An area with no sessions may be an area with no publisher R | Not all boroughs R |
| `lfb-incident-records`, gated | London Datastore | 39 fields R. Size ? | OGL v2 R | Coordinates rounded to 50 m | Outdoor rubbish fires for each km² a year | In no recipe of vibes.md | Monthly or quarterly R | Whether rubbish fires can be picked out is ? R | All |
| `mhclg-council-tax-levels-2026-27`, `ofcom-connected-nations-spring-2026-mobile-coverage` (zip, 254 KB W), gated | GOV.UK, Ofcom | Tables by borough | OGL v3 | Borough code | A figure for the borough, named as the borough's | A borough line, once the contract has a borough fact | Annual, twice a year | A borough figure is the same for about 14 areas R | By borough only |
| `nhs-england-patients-registered-at-a-gp-practice`, `nhs-england-general-practice-workforce`, gated | NHS England publications | CSV | No licence on the page R. A question for NHS England | Practice code | Patients for each full-time GP, shown as a ratio | Shown only, after its audit row | Monthly R | A ratio is not a wait R | England |
| `dcms-sponsored-museums-monthly-visits`, `birkbeck-mapping-museums`, `esa-worldcover-2021`, gated | As each report gives | ? | As each report gives | | Fallbacks only | None at launch | | Each is a second choice behind a row above | |

Proposed as held or banned, so no ingest plan. Each is named so that nobody picks it up by mistake.

| Report | Sources | What would change it |
|---|---|---|
| `green.md` | `gla-tree-canopy-cover-2024`, `gla-green-cover-2024`, `gla-green-and-blue-cover-2019`, `breadboard-labs-curio-canopy-2018`, `forest-research-uk-ward-canopy-cover`, `keep-britain-tidy-green-flag-award-winners`, `fields-in-trust-green-space-index`, `american-forests-tree-equity-score-uk` | A written licence from the GLA GIS team for the first two |
| `fitness.md` | `fitness-operators-own-websites` (banned), `sport-england-active-lives-small-area-estimates` | Nothing. The second describes residents |
| `community.md` | `parkrun-events`, `hmpo-places-of-worship-registered-for-marriage`, `charity-commission-register-of-charities`, `threesixtygiving-grantnav`, `mhclg-planning-data-asset-of-community-value`, `gla-allotment-locations-2007`, `dcms-public-libraries-basic-dataset-2016`, `gla-london-civic-strength-index`, `dcms-community-life-survey`, `ocsi-community-needs-index-2023` | parkrun: a written yes. Places of worship: a founder decision and a second source for Anglican churches |
| `connectivity.md` | `cqc-care-directory`, `dft-electric-vehicle-charging-infrastructure-statistics`, `tfl-bikepoint-cycle-hire-docking-stations`, `rdg-knowledgebase-stations`, `post-office-branch-finder`, `opencellid-cell-towers`, `ookla-open-data` (banned) | `rdg-knowledgebase-stations` is the only source found for step-free access at National Rail stations. The report also gives a fuller reason for the ban on `ofcom-coverage-api`, which is in the registry already |
| `culture.md` | `wikimedia-pageviews`, `theatres-trust-theatres-database`, `alva-visitor-figures`, `visitbritain-visitor-attractions-survey`, `art-fund-museum-of-the-year`, `solt-olivier-awards`, `the-stage-awards`, `dcms-participation-survey`, `time-out-listings` and `cinema-treasures` (both banned) | Nothing worth asking for |
| `grit.md` | `mhclg-planning-data-brownfield-land`, `defra-fly-tipping-statistics`, `mysociety-fixmystreet-geographic-counts`, `os-openmap-local`, `gambling-commission-premises-register`, `home-office-alcohol-licensing-statistics`, `gla-night-time-economy-by-msoa`, `ons-uk-business-counts`, `ons-bres-open-access`, `gla-high-streets-data-service-partnership-data` | `os-openmap-local` may hold railway lines for "a railway runs through this area". Its layers are ? |

## 5. The order to ingest them in

The rule: the smallest files that need no account first, so that a true map of London exists within days. Travel lands late, so its waits start on day one. Compute is an estimate from file sizes and row counts. Nothing was run.

| Step | Sources | What can be seen when it lands | Compute E | Waits on |
|---|---|---|---|---|
| 0. Waits that start today | | | | TfL account. Rail Data Marketplace account. The questions for TfL, Network Rail, HM Land Registry and the statistics office. The pages only a person can open. The audit store |
| 1. The spine | Lookup, OA boundaries, OA and LSOA centroids, TS044, population estimates | London drawn as 26,369 cells, 4,994 LSOAs and 33 boroughs, with a weight on each. The preview geography | Minutes | Nothing |
| 2. Tables by LSOA | VOA stock (14 MB), Indices File 8 (14 MB), Defra NO2 | The first true map: flats, pre-1919 homes, density, noise, nitrogen dioxide, for every LSOA. V1 at 75 | Under 10 minutes | Nothing |
| 3. Shapes | OS Open Greenspace, OS Open Rivers, conservation areas, listed buildings, town centres | Green cover, water, heritage. V2 | Under 30 minutes | Nothing |
| 4. Walks and venues | OS Open Roads, NaPTAN, GIAS, the food register | Every walk from a home. V3, V4, V6 at 85, V7 at 80, V9, V13, V14 at 70 | Under 1 hour: about 26,000 short searches on a London graph | The commons check. The town centre class |
| 5. Cost | Price Paid (three or four yearly files), UK HPI, rents index, rent workbook, ONSPD, TS050 | A buy range by property type and a rent range by bedrooms for each area | Under 30 minutes | The rent model's design. The question for HM Land Registry before launch |
| 6. Places to reach | OS Open Names, Wikidata, NaPTAN, GIAS, NHS sites, ONSPD | "I work at ..." resolves to a real place | Minutes | Nothing |
| 7. Travel | OSM extract, TfL timetables, NaPTAN, H3, then Network Rail | Journey times. Without rail they are a preview and are shown to nobody | Not measured. The research's guess is 1 to 4 hours on 16 to 32 cores with a parallel driver R | Both accounts. The rail gate. Java. The conversion spike |
| 8. The rest of the approved list | Overture (after its spike), police crime, Ofsted, step-free, Wikipedia, tenure | V10. V6 and V7 at 100. Crime and school facts beside. The area page's quoted paragraph | Under 1 hour | The Overture spike |
| 9. Census panel | The five census tables | The census table on an area's page | Minutes | The registry's new heading |
| 10. New sources | Land use, Active Places, Ofcom, pharmacy list, Arts Council libraries, tree canopy | V5, V8, V11, V12, V14 at 100, broadband line | Canopy overlay about 1 to 2 hours. The rest minutes | Registration of each. The questions of section 10 |
| 11. Before any vibe is shown | The audit tables, in their own store | Each vibe's audit outcome, and so its flags | Minutes | The written rule. The store and its check |

A raw copy of everything in steps 1 to 9 is about 3 to 4 GB E, the sum of the sizes above with 1 GB allowed for the unknowns. Every source in this document is free of charge. The only money is a rented machine for step 7, if hosted CI proves too small.

## 6. The vibes: what each waits on

"Approved" counts the hundredths whose source the registry approves today. A vibe is placed at 60 or more. Every row also waits on the audit of step 11, and on the people test of vibes.md 6.2.

| Vibe | Approved, by source | Placed for all London on approved sources alone | Waits on an owner's answer, or a page a person must open | Waits on a new source | Check first |
|---|---|---|---|---|---|
| V1 Homes | 100: VOA 75, Indices 25 | Yes, at 75 until outdoor space passes its audit row | | | The build-period and type bands in the VOA files |
| V2 Built age | 100: VOA 55, conservation areas 25, listed buildings 20 | Yes. At 75 where a borough sent no conservation areas | | | Conservation coverage by borough |
| V3 Village feel | 100: town centres 40, food register 25, VOA 20, conservation areas 15 | Yes | | | Does a town centre carry its class. The chain rule for "independent" |
| V4 Quiet streets | 100: OS Open Roads 40, food register 30, Indices 30 | Yes | | | Noise is a share of residents, not homes |
| V5 Works and warehouses | 0 | No | | The land use table | The spike of vibes.md 3.1 |
| V6 Pace | 100: food register 65, town centres 20, Overture 15 | Yes, at 85 before the Overture spike | | | Office and visitor districts |
| V7 Food and drink | 100: food register 80, Overture 20 | Yes, at 80 until cuisines are read and audited | | | Overture's cuisine categories |
| V8 Leafy | 30 | No | The better canopy map: a question for the GLA GIS team | The land use table, then the tree canopy map and the forest inventory | Canopy at the road edge on 20 streets |
| V9 Parks close by | 100: OS Open Greenspace | Yes, if the commons check passes | | Only if the check fails | 20 named commons, heaths and forests |
| V10 Culture on the doorstep | 80: Overture | Yes in name. All 80 rest on one source whose London quality is unmeasured | Libraries: the Arts Council page. A second venue source: a question for the GLA | | The Overture spike. Does it vary inside inner London |
| V11 Places to train | 20 | No | A question for Sport England, before launch | Active Places | Operator name filled in. Gyms per borough |
| V12 Places to meet | 20 as vibes.md counts it. 60 if `meeting_place_kinds` is counted from five kinds on approved sources: allotment, children's centre, play space, high street, pub | Only on that reading, and only just | Libraries: the Arts Council page. parkrun: a written yes | Active Places | Does it vary inside inner London |
| V13 Family amenities | 100: GIAS 40, OS Open Greenspace 60 | Yes | School results beside it: the DfE download page | | Open state primaries only |
| V14 Everyday on foot | 70: food register 25, town centres 25, NaPTAN 20 | Yes, at 70 | GP walk: `nhs-ods` gains `scoring` and `display` | The pharmacy list | The business type for a food shop |

Ten vibes can be placed on approved sources alone. None of the ten waits on an owner's answer to be placed. Five of the ten rest partly on the food register and three on Overture, so those two files decide much of what London looks like.

## 7. The founder's eight points: what is still missing

| # | Asked for | In hand on approved sources | Still missing |
|---|---|---|---|
| 1 | Vibes at the centre | Ten of 14 recipes | Any real release. The named map. The audit store and rule. The Overture spike. ADR 0013 is not yet written |
| 2 | "Gritty" | Recorded criminal damage, in Indices File 8, beside | The land use table is not registered or opened: its LSOA vintage, units and what "Transport (other)" holds are unknown. An allowlist row for criminal damage. Street cleanliness has no source below borough level, and none is expected |
| 3 | Kinds of gym | Tennis courts and playing fields | Active Places is not registered. Its information file is unread. The operator list does not exist |
| 4 | Culture, highly ranked | Venue counts from Overture, unmeasured | The three Arts Council lists are unread. `wikidata-cultural-venues` is not registered. The GLA's venue map is not cleared. No rating can ever be held |
| 5 | Green, leafy, parks | Parks and play space | The commons check. Gardens and woodland wait on the land use table. Trees wait on the canopy map, whose accuracy report is unread |
| 6 | Community, parkrun | Five kinds of meeting place | Libraries and sports facilities. parkrun's terms have not been read |
| 7 | 5G, fibre | Station, high street and food shop walks | The Ofcom entry for January 2026 is not registered. PLAN section 4 still lists broadband and GP access as out. 5G exists by borough only, and the contract has no borough fact. `nhs-ods` lacks two uses. The pharmacy file is unopened |
| 8 | Demographics | Decided: shown, never ranked (ADR 0014) | The registry has no heading or entry that allows display. Main language is not published below borough. TS007A at OA level is unconfirmed. The release has no file for the figures |

## 8. The smallest release of all London that is honest to launch

ADR 0014 asks that every area has a name, a boundary, travel times, a cost range, and enough of what is measured to be ranked.

| Need | Sources | State today | Without it |
|---|---|---|---|
| Name and boundary | Lookup, OA boundaries, OA centroids, OS Open Names, Wikidata, OS Open Roads, town centres. And the reviewed file of areas | All approved. The file does not exist | No release |
| Travel times | OSM extract, TfL timetables, **Network Rail schedule**, NaPTAN, LSOA centroids, H3 | Five approved, one gated. Questions for TfL and Network Rail | No launch. Rail cannot be left out of London |
| Places to reach | OS Open Names, NaPTAN, ONSPD, Wikidata, GIAS, NHS sites | All approved | A workplace cannot be named |
| Cost range | Price Paid, UK HPI, rents index, rent workbook, ONSPD, census housing tables | All approved. Questions for HM Land Registry and the statistics office | No launch |
| Enough to be ranked | VOA stock, OS Open Greenspace, food register, GIAS, Indices File 8, Defra NO2, conservation areas, listed buildings, population estimates | All approved | Fewer features, each said to be missing |
| Usable, not needed for honesty | Protomaps basemap, TfL step-free, TfL live journey detail | All approved | A map of outlines only |

The first five rows are 29 sources: 28 approved and one gated. The last row adds three. The set carries nine vibes before the audit: V1, V2, V3, V4, V6, V7, V9, V13 and V14. It leaves out Overture, so V10 waits, and V6 and V7 run at 85 and 80. It leaves out crime, school results, the census table and the quoted paragraph. The founder has asked for the census table in the first version, which adds the five census tables once the registry can hold them.

One area fails the test as written. The rents index does not publish the City of London R, so an area there has no rent anchor. Section 10 puts the choice to the founder.

| Kind of step | Needs | Can run on |
|---|---|---|
| Tables by OA or LSOA | HTTPS, Python, readers for XLSX and ODS | Hosted CI: 4 cores, 16 GB of memory, 14 GB of disk, 6 hours a job W |
| Points, lines and polygons | The same, and a geometry library. A GeoPackage is an SQLite file M, so no system library is needed to open one | Hosted CI |
| The Overture cut | A reader of Parquet over HTTPS | Hosted CI |
| Routing and the timetable conversion | Java, and memory for a London network. Account keys held as secrets | Hosted CI only if the spike shows it fits. If not, a rented machine, at tens of pounds a quarter R |
| The basemap cut | One command-line tool | Hosted CI |
| Pages that only a person can open | A browser | The founder |

The repository is public, so a CI log and a build artefact can be read by anyone M. No step may print a row or upload a raw file. Price Paid, the food register, GIAS and Active Places all hold rows about one home or one person.

## 9. Gaps that no dataset fills

| Gap | Why | What a model could do when a release is built, under ADR 0014 |
|---|---|---|
| Street markets | No London-wide open list R | Find each borough's own page. Code must then fetch the page and find the words. Each site's terms are read first |
| Aliases and smaller names of areas | Sources disagree | Propose. A person approves, as the plan says |
| The operator list for gyms | It is Burro's own judgement R | Find the sentence in which an operator describes itself. The founder approves each row |
| Festivals, opening hours, prices, ratings, street cleanliness | No lawful source R | Nothing. These stay unsaid |
| Aircraft noise apart from road noise. Railway lines | No source was looked for R | Nothing. These need a registered dataset |

## 10. For the founder, and for the owners of other files

| # | Decision for the founder | Recommended |
|---|---|---|
| 1 | The City of London has no published rent. May an area launch with a buy range and the words "no rent figure is published for this borough"? | Yes. It is what rule 7 asks for. ADR 0014's test then reads "a cost range, for rent or for sale" |
| 2 | Main language is in ADR 0014's list and is published for boroughs only | Leave it off the panel, and say so in the ADR |
| 3 | Do broadband, the GP walk and the pharmacy walk come into the first version? | Yes for the two walks. Broadband as a line |
| 4 | Count Places to meet from five kinds on approved sources, at 60 hundredths? | No. Wait for libraries or sports facilities: 60 is the line itself |
| 5 | May a Wikipedia excerpt that describes residents be shown? | Decide with the census panel. Burro's own rule is that it writes no sentence about residents; this one is quoted |
| 6 | This design adds a question for each of seven owners: Sport England, Arts Council England, parkrun, GLA GIS on canopy, NHS England, Ofcom, MHCLG on land use | Sport England and the Arts Council first. They bear on V10, V11 and V12 |
| 7 | If routing does not fit hosted CI, rent a machine? | Yes, by the hour |

| Owner | Finding |
|---|---|
| Registry | The attribution on the listed building and conservation area pages is longer than the two entries record W |
| Registry | `police-uk-street-level-crime` should name the custom download form. The archive holds stop and search W |
| Registry | The entry for population estimates gives no size. The file is 83.4 MB W |
| Registry, contract | `university_proximity` names `dfe-gias`, which holds no universities R. Wikidata holds them and has no `scoring` use |
| Registry, contract | `station_lines` names the TfL timetables, which hold no rail lines R |
| Contract | The catalogue says `noise_exposure` is a share of homes. The file counts residents R |
| Registry | Overture removes `categories` from its September 2026 release W. Pin a release and name the field used |
| Pipeline | The Defra 2025 maps are due by mid-October W. The VOA 2025 edition came out on 25 September 2025 R, so a 2026 edition may be days away. Record the edition in every figure |

Everything marked M, E or ? above is unverified. So is every W until a person has read the page by eye.
