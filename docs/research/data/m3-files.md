# What the files of names and borders hold

Status: read on 2026-09-23, from the files in the store that day. It is a dated snapshot. A publisher that reissues a file makes another file, with another hash, and this page does not describe it.

It is written for whoever builds the named areas of [the areas design](../../design/london-data-areas.md). It holds the names of layers and columns, the labels a publisher gives to kinds of record, and counts. It holds no row of any file and no name of a place. The credit of each publisher is at the foot. The boundaries, the centres and the lookup of output areas are described in [m1-files.md](m1-files.md), and are not described again.

| How it was read | |
|---|---|
| The gate | `Registry.require(id, gazetteer)` was asked of every source before its file was opened. A source the gate refused was not opened |
| Each file with a receipt | Through `Inputs.open(id, gazetteer)`, which copies the file out of the store and holds the copy to its receipt |
| The file with no receipt | The gate was asked, and the file was copied out of the store and read. Section 6 |
| What is inside | Short programs that are not kept. Nothing was written to the store |
| Geometry | `shapely`, through `cells/shapes.py`, and `sqlite3`. Nothing else |
| What holds the counts from now on | Nothing yet. No reader of these files is in the repository, so no test reads them. Each builder's reader brings its own |

Two slips are recorded in section 12.

## 1. The gate

Every source with a file in the store, and what the gate gives it for. "Counts on it" is whether the areas design does.

| Source | Status | The gate gives | For `gazetteer` | Receipts | The areas design counts on it |
|---|---|---|---|---|---|
| `os-open-names` | approved | `gazetteer`, `destination_search` | Yes | 1 | Yes: the first source of names |
| `os-boundary-line` | approved | `gazetteer`, `display` | Yes | 1 | Yes: ward names |
| `os-open-roads` | approved | `gazetteer`, `scoring` | Yes | 1 | Yes: distance along roads |
| `gla-town-centre-boundaries` | approved | `gazetteer`, `scoring` | Yes | **None** | Yes: where a seed is put, and 3 points |
| `ons-output-areas-2021` | approved | `gazetteer`, `cells`, `display` | Yes | 2 | Yes: the cells |
| `ons-oa-pwc-2021` | approved | `gazetteer`, `cells`, `scoring` | Yes | 1 | Yes: where homes are in a cell |
| `ons-oa21-lsoa21-msoa21-lad22-lookup` | approved | `gazetteer`, `cells`, `scoring` | Yes | 1 | Yes: which cells are London |
| `ons-census-2021-housing-tables` | approved | `scoring`, `display`, `profile_text` | **No** | 1 | **Yes**: homes in each output area. Section 2 |
| `os-open-greenspace` | approved | `scoring`, `display` | **No** | 2 | For a reviewer's map only. Section 2 |
| `os-open-rivers` | approved | `scoring`, `display` | **No** | 1 | For a reviewer's map only. Section 2 |
| `ons-msoa-2021` | approved | `cells` | No | 1 | No. The lookup gives each output area its MSOA |
| `ons-lsoa-2021` | approved | `cells`, `scoring` | No | 1 | No |
| `ons-lsoa-pwc-2021` | approved | `cells`, `routing` | No | 1 | No |
| `osm-geofabrik-greater-london` | approved | `routing` | No | None | Never. It was not opened |
| `voa-council-tax-stock-of-properties` | approved | `scoring`, `display`, `profile_text` | No | 3 | No |
| `defra-pcm-background-air` | approved | `scoring`, `display` | No | 2 | No |
| `mhclg-iod-2025-underlying-indicators` | approved | `scoring`, `display` | No | None | Never |
| `fsa-food-hygiene-ratings` | approved | `scoring`, `validation_only` | No | None, for 33 files | No |
| `nhs-ods` | approved | `destination_search` | No | None, for 2 files | No |
| `ofsted-state-funded-schools-mi` | approved | `scoring`, `display` | No | 1 | No |
| `hmlr-uk-house-price-index` | approved | `scoring`, `display` | No | 1 | Never |
| `ons-median-house-prices-msoa` | approved | `validation_only` | No | 1 | Never |
| `ons-price-index-of-private-rents` | approved | `scoring`, `display` | No | 1 | Never |
| `ons-private-rental-market-london-postcode-district` | approved | `scoring`, `display` | No | 1 | Never |

Sources the design names that have no file in the store:

| Source | Status | For `gazetteer` | What the design wants of it | Why there is no file |
|---|---|---|---|---|
| `wikidata-places-and-landmarks` | approved | Yes | A second publisher for a name: 2 points, and 1 more for a link to an article. The design took 720 of its 1,100 candidates from it | It is a query, and nobody has written it |
| `hoc-library-msoa-names` | gated | No | The only names that come with ground made of output areas | The licence text has not been read |
| `gla-high-street-boundaries` | gated | No | A second anchor. The design says it is not needed | Waits on a reply |
| `dft-naptan` | approved | No | Stations on a reviewer's map | To be saved by a person |
| `ons-postcode-directory` | approved | No | The check that every postcode falls in an area | No address has been read |

Ten sources are registered for `gazetteer`. Seven are approved and in the store. One is approved and not in the store. Two are gated.

## 2. What the design counts on and the gate will not give

| The design uses | For | The gate says | What a builder can do |
|---|---|---|---|
| Homes in each output area, from `ons-census-2021-housing-tables` | Step 7: an area under 1,500 homes becomes an alias. Step 9: the centre nearest the middle of the homes. `primary_borough`: the borough with most of an area's homes | Refused for `gazetteer`. `write_release` asks `gazetteer` of every source the file of neighbourhoods cites, so a release that cited the table there would be refused too | Count output areas in place of homes. London holds 129.8 homes an output area on average, so 1,500 homes is about 12 output areas. Or the registry's owner adds the use. It is for the founder to say which |
| `spine.build` | The list of London's output areas | It asks the gate for `scoring`, and reads the table of homes. It cannot be called for `gazetteer` | `spine.read_lookup` on the lookup opened for `gazetteer` gives the same 26,369 rows, with no homes |
| Rivers and green space | Layers behind a border, for a reviewer. The design's section 13 asks the registry's owner for this | Refused for `gazetteer`. Neither file was opened | `os-open-names` holds names of water, woods and stations as points with a box: section 4. The tidal river can be drawn from two files the gate gives: section 9 |
| The river, to say which bank an output area is on | Step 2 | `os-open-rivers` is refused | Section 9. West of the tidal limit no file the gate gives draws the river |
| Stations | A layer for a reviewer | `dft-naptan` is refused, and is not in the store | `os-open-names` holds 575 records of kind `Railway Station` in London |
| Every live postcode falls in an area | A hard measure of the design's section 10 | `ons-postcode-directory` is refused for `gazetteer`, and is not in the store | `os-open-names` holds 180,457 postcode records in London, in 26,354 of the 26,369 output areas. The file's licence note asks for a line of credit to Royal Mail. Whether that is wanted is not for a builder to decide |

## 3. London: how a record is tested

A record is in London if it falls in an output area of the spine: a row of the lookup whose `LAD22CD` starts `E09`. The borough of a record is the borough of that output area.

| A record is | The test | With |
|---|---|---|
| A point | The output area whose full-resolution outline it lies in or on. The outlines are BFC V8 of `ons-output-areas-2021` | `shapely.STRtree` over the 26,369 outlines, asked with the predicate `intersects` |
| A point on the line between two output areas | The output area whose code sorts first. The choice is fixed, so that a build repeats | The same |
| A point in no output area | It is not in London by this test. The outlines stop at the mean high water mark, so a point on the tidal river is in none | |
| A shape | In London if any part of it lies in an output area. How much of it does is kept beside it, as a share of its area | `shapely.intersection` against the 26,369 outlines joined |
| A shape that is a borough or a ward | By its code, which the file gives: section 5 | No geometry |

What the test gave, on the 3,047,173 records of `os-open-names`:

| | Records |
|---|---|
| Within 2 km of the box round London | 312,062 |
| In a full-resolution output area of London | 251,435 |
| On the line between two output areas or more | 7,306. Of them 197 are populated places. One is on the line between two boroughs, and it is a road |
| In a generalised output area of London (BGC V2) | 251,402 |
| In another output area by the generalised outlines than by the full | 11,053. In another borough: 199 |
| That the file itself says are in London, by `COUNTY_UNITARY_TYPE` | 251,539 |
| That both tests take | 251,425 |
| That the file says are in London, in no output area | 114. They are up to 387 m from any output area: tidal water, ferry terminals, wetland, roads, 11 postcodes |
| In an output area, that the file puts outside London | 10 |
| Populated places that either test takes | 690 by both. The two tests agree on every one |

- **Place a point by the full-resolution outlines.** The generalised outlines put one name in 23 in another output area.
- **A populated place is often on a line.** 197 of 690 lie on the line between two output areas. The design read that Ordnance Survey puts a settlement at a road junction, and 504 of the 690 are within 1 m of a node of the roads. An output area's edge often runs down the middle of a road. So "the seed lies inside its own area" needs the fixed choice above.
- **The file's own borough is not the spine's for 4 populated places.** Each is within 4 m of a borough's edge, where the two publishers' lines differ. 323 records in all differ so, and most are roads.
- **One centre of an output area lies outside its own full-resolution outline**, and 320 outside their generalised outline. An output area is known by its code, never by where its centre falls.
- The file's columns write two of the 33 boroughs in a longer form than the lookup does. Match a borough by the output area, not by the text.

## 4. The names of places: OS Open Names

`opname_csv_gb.zip`, file id `f-6175912f1a3b`, edition `2026-07`, 103,259,564 bytes. Receipt: yes, for `gazetteer`.

| | |
|---|---|
| Inside | 819 tables under `Data/`, `Doc/OS_Open_Names_Header.csv`, `Doc/licence.txt`, `readme.txt`. 1,806,068,128 bytes unpacked |
| A table's name | Two letters and two digits of the National Grid, as `TQ28.csv` |
| Header | **None in any table.** The names of the columns are the one row of `Doc/OS_Open_Names_Header.csv` |
| Encoding | UTF-8 with a byte order mark, in every table and in the header. `Doc/licence.txt` is not UTF-8 |
| Ends of lines | CR LF |
| Columns | 34 in every row of every table |
| Rows | 3,047,173 |
| A missing value | An empty cell |
| Coordinates | The National Grid, in whole metres. The file does not say which grid: London's fit |
| Tables that hold a record of London | 10: `TL20`, `TQ06`, `TQ08`, `TQ24`, `TQ26`, `TQ28`, `TQ44`, `TQ46`, `TQ48`, `TQ68`. 219,154,898 bytes unpacked. A table is not quite the square of its name: test each record |
| Time to read all 819 | 14 seconds |

`Opened.rows` takes the first row of a table for its header, so it cannot read a table here. `Opened.text("TQ28.csv")` gives each table as text, and the header is read the same way.

### The columns

"Filled" is of London's 690 populated places, and of its 65,064 road records.

| Column | Holds | Places | Roads |
|---|---|---|---|
| `ID` | The publisher's id of the record. `osgb` and digits for a place or a road. A postcode's is the postcode | 690 | 65,064 |
| `NAMES_URI` | An address made from the id. For a place it ends in the digits alone, without `osgb` | 690 | 65,064 |
| `NAME1` | The name, as written | 690, 681 of them distinct | 65,064 |
| `NAME1_LANG`, `NAME2_LANG` | The language. Empty in every record of London | 0 | 0 |
| `NAME2` | A second name | 1 | 50 |
| `TYPE` | One of six kinds | 690 | 65,064 |
| `LOCAL_TYPE` | The finer kind | 690 | 65,064 |
| `GEOMETRY_X`, `GEOMETRY_Y` | The point | 690 | 65,064 |
| `MOST_DETAIL_VIEW_RES`, `LEAST_DETAIL_VIEW_RES` | The scales of map the name is meant for | 690 | 65,064 |
| `MBR_XMIN`, `MBR_YMIN`, `MBR_XMAX`, `MBR_YMAX` | A box round the thing named. Every record of London has one, but a postcode | 690 | 65,064 |
| `POSTCODE_DISTRICT`, `POSTCODE_DISTRICT_URI` | The postcode district the point is in | 690 | 65,064 |
| `POPULATED_PLACE`, `POPULATED_PLACE_URI` | The settlement a record is in. **Empty for every populated place** | 0 | 64,773 |
| `POPULATED_PLACE_TYPE` | The kind of that settlement, as an address. **Empty for 27,052 roads that name a settlement.** Do not read the kind from it | 0 | 37,721 |
| `DISTRICT_BOROUGH`, `DISTRICT_BOROUGH_URI`, `DISTRICT_BOROUGH_TYPE` | The borough. The type is an address that ends `LondonBorough` | 690 | 65,064 |
| `COUNTY_UNITARY`, `COUNTY_UNITARY_URI`, `COUNTY_UNITARY_TYPE` | For London, the one authority for the whole. The type ends `GreaterLondonAuthority` | 690 | 65,064 |
| `REGION`, `REGION_URI`, `COUNTRY`, `COUNTRY_URI` | | 690 | 65,064 |
| `RELATED_SPATIAL_OBJECT` | For a section of a road, the id of the road | 0 | 8,931 |
| `SAME_AS_DBPEDIA` | An address at `dbpedia.org` | 441 | 0 |
| `SAME_AS_GEONAMES` | An address at `sws.geonames.org` | 301 | 0 |

### The kinds, and how many of each

| `TYPE` | `LOCAL_TYPE` | Great Britain | London |
|---|---|---|---|
| `populatedPlace` | `City` | 71 | 3 |
| | `Town` | 1,355 | **0** |
| | `Village` | 15,155 | 24 |
| | `Hamlet` | 12,900 | 9 |
| | `Other Settlement` | 2,914 | 128 |
| | `Suburban Area` | 10,876 | 526 |
| | All | 43,271 | **690** |
| `transportNetwork` | `Named Road` | 882,055 | 55,702 |
| | `Section Of Named Road` | 101,301 | 8,746 |
| | `Numbered Road`, `Section Of Numbered Road` | 11,100 | 616 |
| | `Railway Station` | 3,326 | 575 |
| | 15 other kinds | 1,603 | 63 |
| `other` | `Postcode` | 1,743,127 | 180,457 |
| | 25 kinds of school, hospital and works | 36,929 | 3,663 |
| `hydrography` | 7 kinds | 26,870 | 206: `Inland Water` 205, `Tidal Water` 1 |
| `landcover` | 5 kinds | 121,148 | 595: `Woodland Or Forest` 524, `Other Landcover` 43, `Urban Greenspace` 17, `Wetland` 11 |
| `landform` | 11 kinds | 76,443 | 122 |
| All | | 3,047,173 | 251,435 |

The design takes every populated place as a candidate, for 3 points. London holds five of the six kinds.

### What a populated place gives

| | `City` | `Other Settlement` | `Suburban Area` | `Village` | `Hamlet` |
|---|---|---|---|---|---|
| Records | 3 | 128 | 526 | 24 | 9 |
| A point | 3 | 128 | 526 | 24 | 9 |
| A box, with the point inside it | 3 | 128 | 526 | 24 | 9 |
| The box, in hectares: least, median, most | 517, 4,511, 233,320 | 25, 845, 3,570 | 25, 228, 1,586 | 28, 66, 517 | 25, 35, 68 |
| Boxes of 500 m by 500 m, the smallest there is | 0 | 22 | 6 | 0 | 3 |
| `LEAST_DETAIL_VIEW_RES`, the commonest | 9,000,000 | 60,000 | 25,000 | 250,000 | 25,000 |
| Within 1 m of a node of `os-open-roads` | 2 | 66 | 413 | 16 | 7 |
| Named as their settlement by road records | 3 | 93 | **0** | 24 | 9 |
| By 50 road records or more | 3 | 90 | 0 | 1 | 0 |
| With `SAME_AS_DBPEDIA` | 1 | 93 | 335 | 12 | 0 |

- **One `City` record has a box 54 km by 43 km.** It is a name for the whole, and not a seed. The design's "wide name" fits it.
- **9 names are held by two records each.** For one of the nine, both records are in the same borough, so the design's slug of name and borough does not tell them apart.
- 681 distinct names: 297 of one word, 356 of two, 28 of three to five. 14 hold an apostrophe and 1 a hyphen. None holds a bracket, a digit or a letter outside ASCII.
- Places in a borough, by the file's column: 2 to 59, 20 at the median.
- The nearest other place is 894 m away at the median, in a straight line, and 50 m at the least. 82 pairs lie within 600 m, and 23 within 300 m. Distance along roads is longer, so the design's rule of 600 m by road takes fewer.
- 317 of the 526 points of kind `Suburban Area` lie in the box of an `Other Settlement`, and 51 of the 128 the other way. The two kinds overlap: neither is simply the larger.
- Every centre of an output area but 26 lies in the box of one place or more. 7,622 lie in one box, 11,344 in two, 7,377 in three or more.
- 71 places have their point outside London and a box that reaches in. By the test they are not London's.
- A crude look for a name that holds a word for a group of people, from a list of some 120 words, found 3 among the places, 2 among the town centres and 5 among the wards. It sees whole words only. It is no test: a person reads every name.

### What a road says of its settlement

The design gives 2 points to a name that 50 road records give as their settlement, and takes 15% off a distance where an output area's roads do. It asked whether a road names a settlement finer than the whole city. It was the first thing to measure.

| | Road records | Output areas, by what most of their roads give |
|---|---|---|
| All | 65,064 | 26,369 |
| Name no settlement | 291 | 3,811. Of them 3,802 have no road record in them |
| Name a `City` | 37,346. One of the three takes 34,813 | 13,151 |
| Name an `Other Settlement` | 27,045 | 9,350 |
| Name a `Village` or a `Hamlet` | 309 | 51 |
| Name a `Suburban Area` | **0** | 0 |
| Name a settlement outside London | 73 | 6 |

- **Join a road to its settlement by `POPULATED_PLACE_URI`, which is the settlement's `NAMES_URI`.** 64,700 of 64,773 join to a place of London so. By name, 4 names of kind `Suburban Area` seem to join: each is the same word for another place.
- **A road is finer than the city for about 4 in 10 records**, and then it names one of 93 large places. The 526 of kind `Suburban Area`, which are most of the candidates, are named by no road.
- So the 2 points are there for 91 places that are not a `City`, and for no `Suburban Area`. The 15% applies only where the seed is one of those places.
- A postcode record names its settlement the same way: 107,700 name a `City`, 71,824 an `Other Settlement`.
- A road record's id is the `road_name_toid` or `road_number_toid` of a link in `os-open-roads`, for 52,062 of the 65,064.

## 5. The boundaries of boroughs and wards: Boundary-Line

`bdline_gpkg_gb.zip`, file id `f-46cd0aa54c44`, edition `2026-05`, 807,724,473 bytes. Receipt: yes, for `gazetteer`.

| | |
|---|---|
| Inside | `Data/bdline_gb.gpkg`, 1,836,081,152 bytes, and six documents under `Doc/` |
| The GeoPackage | Version 1.2, 18 layers, each in the National Grid, each with an index |
| To read it | It must be taken out of the zip first: SQLite cannot read inside one. `Opened` has no call for that |
| `shapes.read_outlines` | **Refuses it.** It stops at a file of more than one layer |
| An outline | `MULTIPOLYGON` in the column `geometry`. None of London's is invalid |

| Layer | Features | Of London | How London's are told |
|---|---|---|---|
| `district_borough_unitary` | 350 | **33** | `Area_Code` is `LBO`. `Census_Code` is the spine's `LAD22CD`, for all 33 |
| `district_borough_unitary_ward` | 6,633 | **704** | `Area_Code` is `LBW`. `Census_Code` starts `E05` |
| `greater_london_const` | 14 | 14 | `Area_Code` is `LAC` |
| `westminster_const` | 632 | 75, with half their ground or more in London | By geometry. 17 more reach in |
| `parish` | 14,258 | 34 | 33 are filler with no name. One is a civil parish |
| `polling_districts_england` | 31,631 | 2,717 | By geometry. Its columns are `PD_ID`, `County`, `Distric_Bo`, `Ward`, `Parish` |
| `high_water` | 32,850 lines | 240 within 50 m of London, 192 km | `Feature_Description` is `High Water Mark (HWM)` for all |
| `county` | 22 | 1 | `Area_Code` is `GLA` |
| `english_region` | 9 | 1 | |
| `boundary_line_ceremonial_counties`, `boundary_line_historic_counties`, `historic_european_region` | 91, 95, 2,742 | 2, 1, 1 | `Name` and `Area_Description` only |
| `county_electoral_division`, `unitary_electoral_division`, `community_ward`, `country_region`, `scotland_and_wales_const`, `scotland_and_wales_region` | | 0 | |

The fields of a borough and of a ward are the same:

| Field | Type | Holds |
|---|---|---|
| `fid` | `INTEGER` | The row's number, and its number in the index |
| `geometry` | `MULTIPOLYGON` | The outline |
| `Name` | `TEXT(100)` | The name, with a word after it for the kind: section below |
| `Area_Code`, `Area_Description` | `TEXT(3)`, `TEXT(50)` | `LBO` and `London Borough`. `LBW` and `London Borough Ward` |
| `Census_Code` | `TEXT(9)` | The statistics office's code. Filled for every borough and ward of London |
| `File_Name` | `TEXT(100)` | The same for every ward of London. It does not say which borough a ward is in |
| `Hectares`, `Non_Inland_Area` | `REAL` | The whole, and the part of it that is tidal water |
| `Admin_Unit_ID`, `Global_Polygon_ID`, `Feature_Serial_Number`, `Collection_Serial_Number` | `MEDIUMINT` | The publisher's own numbers |
| `Area_Type_Code`, `Area_Type_Description`, `Non_Area_Type_Code`, `Non_Area_Type_Description` | | `AA` for a borough, `VA` for a ward |

### The boroughs

| | |
|---|---|
| Boroughs | 33, with the codes of the spine |
| `Name` | 32 end ` London Boro`. One is written plain. With the ending taken off, 31 are the lookup's text |
| Land, as the file draws it | 159,462.7 hectares, in one piece. The spine's is 157,342.2, in 12 |
| Why they differ | The file draws a borough to the middle of the tidal river. `Non_Inland_Area` sums to 2,129.7 hectares. The output areas stop at the mean high water mark |
| Spine outside the file | 18.6 hectares in all, and 9.7 at most in one borough |

### The wards

The design asked whether the file holds London's wards. It does.

| | |
|---|---|
| Wards | 704. The design expected 679, from research that was not counted in a file |
| Codes | 704, each once |
| Names | 693 distinct. 11 names are held by two wards each |
| `Name` | Every one ends ` Ward`. 83 hold `&`, 2 a comma, 30 an apostrophe. 139 hold a word of the compass, or `Central`, `Upper` or `Lower` |
| The borough of a ward | No column gives it. Every ward lies wholly in one borough of the same file, to the square metre |
| Wards in a borough | 17 to 28, 21 at the median |
| Land | 5.1 to 3,364.9 hectares, 164.7 at the median |

The wards are those of May 2026. The output areas are those of the census of 2021. They do not nest.

| An output area's share in its best ward | Output areas |
|---|---|
| All of it, to 1 in 1,000 | 18,875 |
| Under 99% | 4,153 |
| Under 95% | 2,340 |
| Under 75% | 1,141 |
| Under 50% | 28 |

- The ward of an output area is the ward that holds most of it, and the share is kept. By the centre of the output area it is the same ward for 25,954 of 26,369.
- No output area's best ward is in another borough than its own.
- 13 wards are the best ward of no output area. A ward is the best ward of 38 output areas at the median, and of 66 at most.

## 6. The town centres

`Town_Centres_Boundaries.gpkg`, 1,712,128 bytes. Its hash begins `4076c2bc276b`.

**It has no receipt.** The list says why: the publisher's page states no edition and no period, so the file is stored and nothing may rest on it until a person states both. `Inputs.open` refuses it. Whatever is drafted from it is marked as resting on a file with no receipt.

What the file itself says of its date: `last_change` of its one layer is `2025-12-22`. Every date column of the layer is empty. Its metadata holds no date.

The design asked whether a town centre carries a name and a class. It carries both.

| | |
|---|---|
| Layers | One, `town_centres`. `MULTIPOLYGON` in the column `geom`, in the National Grid |
| Features | 234 |
| Valid outlines | 234 |
| In one piece | 197. 37 are in more, and one is in 28 |
| Land | 0.95 to 258.96 hectares, 9.93 at the median |
| Output areas a centre lies over | 1 to 109, 13 at the median |
| Centres over two boroughs or more | 40 |
| Pairs of centres that lie over each other | 7 |
| Centres with a part in no output area | 15, by up to 23% of their ground |

| Field | Filled | Holds |
|---|---|---|
| `fid`, `OBJECTID` | 234 | 1 to 234 |
| `layerreference` | 234, all distinct | Three letters and eight digits. It is the record's id |
| `sitename` | 234, all distinct | **The name** |
| `classification` | 234 | **The class**: below |
| `borough` | 234 | 33 values. It is the borough of the centre's point for 233 |
| `planningauthority` | 234 | 34 values |
| `easting`, `northing` | 234 | A point. **For 34 centres it lies outside the centre's own outline** |
| `hectares`, `st_area_geom_`, `st_perimeter_geom_`, `Shape_Length`, `Shape_Area` | 234 | The size. `hectares` is the outline's, to 1 in 100 |
| `designation`, `boroughdesignation` | 234 | `Town Centres` in every row |
| `notes` | 234 | The same sentence in every row: "This data belongs to the Planning Authorities. The GLA has not designated these boundaries." |
| `sitereference`, `address`, `uprn`, `firstaddeddate`, `lastupdateddate`, `removeddate`, `status`, `source`, `extrainfo1` to `extrainfo3`, `missing` | 0 | Empty |

| `classification` | Centres |
|---|---|
| `International` | 2 |
| `Metropolitan` | 13 |
| `Major` | 36 |
| `District` | 152 |
| `District Centre` | 2 |
| `Local Centre` | 7 |
| `CAZ retail cluster` | 20 |
| `Unclassified` | 2 |

- The design gives 3 points for a centre "of district class or above". That is 203 centres as written, and 205 if `District Centre` is read as `District`. The file does not say they are the same.
- The sentence in `notes` is a statement about who owns the data. The registry's entry does not quote it. It is for the registry's owner to read.
- 13 names hold `/`, 6 a bracket, 3 the word `and`. 40 hold a word for a road or a market.

### The names of the centres against the names of places

| | |
|---|---|
| Centres whose name is the name of a populated place, letter for letter but for case and marks | 140 of 234. Of district class or above: 135 |
| And that place lies within 800 m of the centre's outline | 134. The other 6 are 954 m to 1,282 m away |
| Centres whose name holds the name of a place as whole words, or is held by one | 57 |
| Neither | 37 |
| Places, but the three of kind `City`, with a centre of district class or above within 800 m of its outline | 380 of 687 |
| The same, measured to the centre's own point | 254 |
| The same, with the place inside the outline | 97 |

The design says "within 800 m" and does not say of what. The outline and the point differ by 126 places.

## 7. The roads: OS Open Roads

`oproad_gpkg_gb.zip`, file id `f-908c0eda3a1b`, edition `2026-04`, 1,016,021,285 bytes. Receipt: yes. It was fetched for `scoring`, and the gate gives `gazetteer` too.

| | |
|---|---|
| Inside | `Data/oproad_gb.gpkg`, 2,144,063,488 bytes, and two notes |
| Layers | `road_link`, 3,961,077 lines. `road_node`, 3,346,499 points. `motorway_junction`, 669 points |
| To read London's | By the layer's index, `rtree_road_link_geometry`, which `read_only` can ask. 3 seconds. The index's `id` is the layer's `fid` |

| London | |
|---|---|
| Links that touch London | 211,334 |
| Their length | 18,515 km. The column `length` is the line's own length, in metres |
| Nodes they start or end at | 168,861, every one in `road_node` |
| The network | 63 pieces. The largest holds 168,627 nodes. 234 nodes are in the other 62 |
| From the centre of an output area to the nearest link | 17 m at the median, 60 m at the 99th of 100. 27 are over 100 m and 1 is over 250 m |
| Links over the tidal river | 48: 44 with no `road_structure`, 4 in a tunnel. They carry 36 names |
| From the centre of an output area to the nearest node | 39 m at the median, 136 m at the 99th of 100, 504 m at most. 5 are over 250 m |
| Centres whose nearest node is off the largest piece | 11 of 26,369. A search from the seeds does not reach them |
| Places whose nearest node is off the largest piece | None of the 687 |
| One search along the roads from all 687 places at once | 0.4 seconds, with `heapq`. It reaches 168,627 nodes |
| Along the roads from a centre's node to the nearest place | 810 m at the median, 1,685 m at the 95th of 100, 3,997 m at most |
| Centres whose nearest place along the roads is their nearest in a straight line | 22,315 of 26,369 |

| Field of `road_link` | Values in London |
|---|---|
| `id` | A code of 36 characters, each once |
| `start_node`, `end_node` | The `id` of a node |
| `road_classification` | `Unclassified` 118,898, `Unknown` 34,562, `A Road` 25,563, `Not Classified` 16,061, `Classified Unnumbered` 9,190, `B Road` 6,849, `Motorway` 211 |
| `road_function` | `Local Road` 115,497, `Restricted Local Access Road` 25,995, `A Road` 25,563, `Minor Road` 20,024, `Secondary Access Road` 15,147, `B Road` 6,849, `Local Access Road` 2,048, `Motorway` 211 |
| `form_of_way` | `Single Carriageway` 200,899, `Collapsed Dual Carriageway` 5,938, `Roundabout` 1,973, `Slip Road` 1,674, `Dual Carriageway` 595, `Shared Use Carriageway` 255 |
| `road_structure` | `Road In Tunnel` 86. Empty for the rest. **No link is marked as a bridge** |
| `name_1` | Filled for 173,879, with 37,528 names |
| `road_name_toid`, `road_number_toid` | The id of the road, as `os-open-names` holds it |
| `name_2`, `name_1_lang`, `name_2_lang` | Empty |
| `fictitious`, `loop`, `primary_route`, `trunk_road` | 0 or 1. `fictitious` is 0 for all |
| `length_uom` | `m` for all |

`road_node` holds `id` and `form_of_road_node`: `junction` 114,871, `road end` 42,559, `pseudo node` 9,005, `roundabout` 2,426.

The file holds roads for vehicles. It holds no footpath and no footbridge.

## 8. The output areas, for what is new here

[m1-files.md](m1-files.md) describes the files. Three things matter to a border that the first build did not need.

| | |
|---|---|
| London's output areas, joined | One piece of 157,329 hectares, and 11 islands of 3.7 hectares or less. **Both banks of the river are in the one piece**: they meet west of the tidal limit |
| Output areas in more than one piece | 57, of up to 4 pieces |
| The full-resolution outlines | Fit together with no overlap. The generalised do not quite: six sides, as the first build found |

## 9. The river

The design sets the bank of an output area by its borough, and marks one borough's wards by hand. No file the gate gives says which borough is on which bank, and a builder may not say it from memory. What the files do give:

| | |
|---|---|
| The tidal river, as ground | London as Boundary-Line draws it, less the output areas. One piece of 2,129.7 hectares, which is the sum of `Non_Inland_Area`. 2,093 slivers beside it come to 9 hectares |
| Its reach | 38.5 km from west to east |
| Its banks, as lines | `high_water` of Boundary-Line. 182 km of it runs within 5 m of the edge of that piece |
| Output areas on its edge | 464, in 17 boroughs |
| Roads across it | 48 links of `os-open-roads` |
| West of its western end | 2,523 output areas, in 6 boroughs. **No file the gate gives draws the river there** |
| Named water | 206 records of `os-open-names`, each a point and a box. No line |

So a bank can be worked out from files for the reach that is tidal, and not beyond it. For the rest, the river is in `os-open-rivers`, which the gate refuses for `gazetteer`.

## 10. What the design expected, and what is so

| | The design | The files |
|---|---|---|
| Output areas | 26,369 | 26,369 |
| Wards | 679 | 704 |
| Candidate names | About 1,100, in the range 1,000 to 1,500. 720 of them from Wikidata | 690 populated places. With the names of town centres that no place holds: 772. With the names of wards that neither holds: 1,220. None from Wikidata |
| Does OS Open Names hold few London names | It feared so | No. 690, which is more than the areas wanted |
| Areas | About 450, in the range 400 to 500 | Below |
| Flagged areas | About 120 | Not known before a draft. Below |

### Points, with the files there are

The design's table of points, scored for the 687 places that are not of kind `City`. "Near a centre" is within 800 m of the outline of a centre of district class or above. A ward "carries" a name when the place's point is in a ward whose name holds it as whole words.

| Evidence | Points | Places that have it |
|---|---|---|
| A populated place in OS Open Names | 3 | 687 |
| 50 road records or more name it | 2 | 91 |
| Wikidata | 2, and 1 | None. No file |
| Near a town centre | 3 | 380 |
| An MSOA name | 2 or 3 | None. Gated |
| A ward carries it | 1 | 310 |

| Score | Places | With two publishers |
|---|---|---|
| 9 | 54 | 54 |
| 8 or more | 76 | 76 |
| 7 or more | 212 | 212 |
| 6 or more | 390 | 380 |
| 5 or more | 395 | 380 |
| 4 or more | 505 | 380 |
| 3 or more | 687 | 380 |

- **Today the Greater London Authority is the only second publisher.** The ward names and the road records are Ordnance Survey's, as the names of places are. So no count of areas above 380 can rest on two publishers, whatever the threshold.
- **The design's rule of 6 points gives 380 areas on two publishers**, before any two that lie too close are joined. That is under 400. The design says what happens then: the founder decides whether one official publisher is enough for the rest.
- **If the second publisher must write the name itself**, and not only lie near it, 140 names pass.
- To land between 400 and 500 the threshold falls to 4 or 5, and 15 to 125 areas rest on Ordnance Survey alone.
- With Wikidata's file, a place would gain up to 3 points and a second publisher. 441 of the 690 places carry `SAME_AS_DBPEDIA`, which holds the title of an article. Whether that joins to a Wikidata item was not tried: there is no file to try it on.

### What a draft would look like

Each output area was given to the nearest seed in a straight line, from its centre, with no other rule. It is a first look and not the method.

| Seeds | Output areas a seed, at the median | Seeds with under 12 | From a centre to its seed |
|---|---|---|---|
| All 687 | 34 | 88, and 13 with none | 559 m at the median, 2,302 m at most |
| The 505 that score 4 or more | 46 | 18 | 619 m, 3,341 m |
| The 390 that score 6 or more | 62 | 10 | 703 m, 5,360 m |

The design's 450 areas would hold 59 output areas each.

### Flags that can be counted before a draft

| Flag of the desk | From the files |
|---|---|
| `one_publisher` | 307 of the 687 places have no second publisher today. Of the areas of a draft, 15 to 125 |
| `two_centres` | Needs the draft. 205 centres of district class or above are there to be shared among the areas |
| `two_boroughs` | Needs the draft. 40 town centres lie over two boroughs or more |
| `margin_under_10`, `least_compact` | Need the draft |
| Names held twice | 9 names, 18 places |
| A seed on the line between two output areas | 197 |

`one_publisher` alone may pass the design's 120.

## 11. What the shared code cannot yet do

| | |
|---|---|
| `Opened` | Reads a table inside a zip as text. It has no call that takes a GeoPackage out of a zip |
| `Opened.rows` | Wants a header in the table. OS Open Names has none |
| `shapes.read_outlines` | Reads the one layer of a file. Boundary-Line has 18 and OS Open Roads 3 |
| `spine.build` | Asks for `scoring` and needs the table of homes |
| The tests that read the real files | Look for receipts in `data/receipts`. Where a working copy holds no such folder every one is skipped, and says the store is missing. The store keeps a copy of each receipt under `receipts/`, and that is what was read here |

## 12. What was not checked, and two slips

| Not checked | Why |
|---|---|
| Any page of any publisher | None was opened. Nothing was fetched |
| That the coordinates of OS Open Names are on the National Grid | The file does not say. They fit |
| What `District Centre` means beside `District` | The file does not say |
| Whether `SAME_AS_DBPEDIA` joins to Wikidata | No file of Wikidata is in the store |
| Distance along roads | Every distance here is a straight line, but for the one search of section 7. That search used no bank and none of the design's adjustments |
| Whether a name describes residents | A list of words is no test |
| Any name on a map | No map was drawn |
| The output of hosted CI | No hosted run has made these counts |

**The first slip.** The names of the files inside the zips of `os-open-greenspace` and `os-open-rivers` were listed, with their sizes, before the gate was asked about either source. The gate refuses both for `gazetteer`. No file inside either was opened, and nothing from either is in this page.

**The second slip.** The scratch programs read the receipts from the store's own copies, and not from a folder of receipts in the repository, because the working copy had none. A build reads receipts from the repository. The two were compared in the working copy of the first build and were the same, file for file.

## 13. Credits

Every count on this page was made from a file of one of these publishers. The words are each publisher's own, as the licence registry holds them. The registry marks each as not yet verified against the publisher's page. Some hold `[year]` where the publisher's page gives a year to fill in: which year is the founder's to say, and none was made up.

| Publisher | Files | Credit |
|---|---|---|
| Ordnance Survey | OS Open Names, Boundary-Line and OS Open Roads | Contains OS data © Crown copyright and database right [year]. |
| Greater London Authority | Town centre boundaries | Greater London Authority - Contains public sector information licensed under the Open Government Licence v3.0 |
| | | Contains OS data © Crown copyright and database rights 2019. |
| Office for National Statistics | The lookup | Source: Office for National Statistics licensed under the Open Government Licence v.3.0 |
| Office for National Statistics | The boundaries and the centres of output areas | Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year] |

The Greater London Authority cannot warrant the quality or accuracy of the data. Its boundaries are indicative, as its page says. The licence note inside OS Open Names asks for a line of credit to Royal Mail. This page holds counts of postcode records and no postcode. Whether the line is wanted here is the founder's to say.
