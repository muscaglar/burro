# Conservation areas and listed buildings

Read and built on 2026-09-24. A dated snapshot, not a source of truth. Nothing here is legal advice. No lawyer has read it.

Both files were read, each through its receipt. Every count here was made by a program. No person has checked one, and no count was held against a planning authority's own list. No figure here is said of a named neighbourhood. A figure is said of a borough where it shows what the file covers.

© Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026. The Historic England GIS Data contained in this material was obtained on 2026-09-24. The most publicly available up to date Historic England GIS Data can be obtained from HistoricEngland.org.uk. Source: Office for National Statistics licensed under the Open Government Licence v.3.0.

## 0. In short

| Question | Answer |
|---|---|
| What was read | Two files of the planning data platform, each GeoJSON for England: conservation areas, 64 MB, and listed buildings, 207 MB |
| What is built | Two measures: `conservation_cover` and `listed_buildings`. Each is named and measured as core says, so a build carries both |
| Does every London authority have conservation areas in the file | Yes, all 33. The fewest is 4 and the most is 86 |
| Is any authority thin | None is shown to be by the file itself. 14 rest wholly on records the file marks `some`, and not `authoritative`. Nobody has held a count against an authority's list. Section 3 |
| How many conservation areas | 1,093 in London, each counted once. 53 records were a second record of one of them |
| How many listed buildings | 19,220 entries in London: 602 of grade I, 1,432 of grade II* and 17,186 of grade II |
| How many areas have a figure | All 1,002, for each measure |
| Does a vibe gain a band | Built age does, for 979 areas. Village feel does not. Section 6 |
| What was put right in the registry | The credit of both sources. Section 7 |
| What is to fetch | Nothing is needed for either measure. One file would name the providers. Section 8 |

## 1. The two files

| What | Conservation areas | Listed buildings |
|---|---|---|
| Registry entry | `mhclg-planning-data-conservation-areas` | `historic-england-listed-buildings` |
| File | `conservation-area.geojson` | `listed-building.geojson` |
| Receipt | `f-450c57d438cb` | `f-3d843cc2d377` |
| Bytes | 64,446,422 | 206,846,502 |
| Edition | retrieved 2026-09-24 | retrieved 2026-09-24 |
| Period | As at 2026-09-24 | As at 2026-09-24 |
| Records in the file | 9,659 | 381,754 |
| Records the dataset page gives | 10,953 | 382,270 |
| Providers in the file | 284 | 1 |
| Providers the dataset page gives | 151 | 1 |
| Where a record is | 9,234 outlines in one piece, 424 in several, 1 point | 379,159 points, 2,595 outlines |
| Records that have ended | 22 | 2,595, which are the outlines |
| Quality, as the file marks it | 5,393 `authoritative`, 4,266 `some` | All `authoritative` |
| Grade | None | I, II* or II on every live record |

The file states no edition. It is made again each day under one address, so its edition is the day it was retrieved, and that day is the day its data is as at.

**The file holds fewer records than the page gives.** For conservation areas the difference is 1,294. What the others are is not known. They may be records with no outline, which a file of outlines cannot hold. The page also gives 151 providers, and the file holds 284 numbers of providers. Neither difference was looked into: both would need the platform's other formats, which are not fetched.

**What a record holds.** Each holds the platform's own number, the number of its provider, a quality, the day it was entered, the day it ended if it has, a name, a reference and a link. A listed building holds its grade too. The name, the reference, the notes and the link are never read. The name of a listed building is often an address.

**Who a provider is.** The file gives a provider as a number. It does not say whose number it is. Provider 16 is Historic England: it is the one provider of the listed buildings, and the dataset page names Historic England as that provider. No other number was put to a name. In London each authority's records come almost wholly from one number, which is likely the authority's own. Two records come from provider 1.

## 2. How each figure is made

### Conservation cover

The share of an area's land that lies inside a conservation area, as a percentage to one decimal place.

| Step | What is done | What it left out in London |
|---|---|---|
| Records in the box | Every record whose box touches the box round London, and a kilometre beyond | 1,340 of 9,659 are in the box |
| Live | A record that had ended by the day of the file is left out | None |
| An outline | A record whose place is a point is left out | None |
| Mended | An outline whose rings cross is drawn again as the land it encloses | 1 was mended. None was lost |
| In London | An outline that shares no land with London is left out | 194 |
| Each once | Two records that share half or more of the land they cover together are one area. One is kept | 53 |
| Kept | | 1,093 |

Of two records of one area, the one kept is the one its provider marks `authoritative`, then the one entered last, then the one with the lowest number.

**What the choice moves.** Little. With no record left out, London's conservation land is 8 hectares more, of 24,216. The figure of 31 areas moves, 3 of them by more than one point, and none by more than 2. Land inside two records is counted once either way. So leaving a second record out matters for counting areas, and hardly at all for the figure. At 30 in 100 shared, 60 records are left out. At 90 in 100, 31 are.

**The land.** 24,216 hectares of London lie inside a conservation area, of 157,334. That is 15 in 100.

### Listed buildings

The entries of the national list in an area, for each square kilometre, to one decimal place.

| Step | What is done | What it left out in London |
|---|---|---|
| Records in the box | As above | 24,743 of 381,754 are in the box |
| Live | A record that had ended by the day of the file is left out | 207 |
| A point | A live record that is not a point would be left out, and counted | None |
| In an LSOA | A point that stands in no LSOA of London is counted in no area | 5,316, nearly all outside London |
| Counted | | 19,220 |

**Entries over water.** An outline of an LSOA is cut at the mean high water mark. About 68 live entries lie inside London and in no LSOA: the list maps them over the river or a dock, as a bridge or a pier may be. They are in no area's figure. That is fewer than 4 in every 1,000. They were counted by closing every stretch of water under 400 metres wide, which is a rough way to do it.

**An entry is not a building.** One entry may be a whole terrace. Another may be a bollard, a milestone or a tomb. Each counts as one. The file has no field for what kind of thing an entry is.

**A place is good to 2 metres.** The file gives longitude and latitude, and the land is measured on the National Grid. The way between them is one fixed operation, which its library gives as good to 2 metres. That is nothing beside a share of land. An entry within 2 metres of a line between two areas may be counted on the wrong side.

## 3. Coverage, authority by authority

The licence registry asks that coverage is checked for all 33 London authorities before anything rests on the conservation areas. An authority that sent nothing is unknown, and never nought.

**Every authority has conservation areas in the file.** So every area of London has a figure, and none is withheld for want of coverage. The code still checks at every build: an authority that the file holds no record for gives no figure to any of its areas.

| Authority | Conservation areas, each once | Marked `authoritative` | Marked `some` | Second records left out | Land inside a conservation area, in 100 | Listed entries | Listed entries for each km² | Listed entries that stand in a conservation area, in 100 |
|---|---|---|---|---|---|---|---|---|
| Barking and Dagenham | 4 | 4 | 0 | 0 | 0.6 | 44 | 1.2 | 25 |
| Barnet | 15 | 15 | 0 | 0 | 14.4 | 646 | 7.4 | 79 |
| Bexley | 23 | 0 | 23 | 8 | 2.4 | 114 | 1.9 | 46 |
| Brent | 23 | 22 | 1 | 0 | 8.2 | 93 | 2.2 | 49 |
| Bromley | 65 | 0 | 65 | 4 | 8.2 | 413 | 2.8 | 54 |
| Camden | 41 | 41 | 0 | 0 | 52.4 | 1,953 | 89.6 | 92 |
| City of London | 28 | 28 | 0 | 0 | 45.3 | 612 | 211.6 | 84 |
| Croydon | 22 | 1 | 21 | 1 | 5.1 | 177 | 2.0 | 41 |
| Ealing | 32 | 0 | 32 | 0 | 12.2 | 308 | 5.5 | 73 |
| Enfield | 24 | 24 | 0 | 0 | 10.4 | 299 | 3.6 | 63 |
| Greenwich | 14 | 0 | 14 | 0 | 18.5 | 536 | 11.3 | 74 |
| Hackney | 39 | 37 | 2 | 5 | 29.7 | 548 | 28.7 | 78 |
| Hammersmith and Fulham | 44 | 43 | 1 | 3 | 49.4 | 262 | 16.0 | 90 |
| Haringey | 30 | 25 | 5 | 0 | 30.0 | 284 | 9.6 | 88 |
| Harrow | 27 | 0 | 27 | 0 | 8.0 | 289 | 5.7 | 67 |
| Havering | 11 | 0 | 11 | 0 | 3.4 | 146 | 1.3 | 47 |
| Hillingdon | 35 | 32 | 3 | 9 | 6.7 | 429 | 3.7 | 59 |
| Hounslow | 30 | 30 | 0 | 15 | 21.4 | 506 | 9.0 | 84 |
| Islington | 41 | 0 | 41 | 0 | 39.7 | 1,048 | 70.5 | 94 |
| Kensington and Chelsea | 42 | 42 | 0 | 0 | 73.7 | 1,338 | 110.2 | 96 |
| Kingston upon Thames | 28 | 28 | 0 | 0 | 9.5 | 157 | 4.2 | 66 |
| Lambeth | 64 | 63 | 1 | 0 | 28.5 | 938 | 35.0 | 85 |
| Lewisham | 29 | 29 | 0 | 1 | 19.9 | 364 | 10.4 | 74 |
| Merton | 28 | 0 | 28 | 0 | 18.2 | 242 | 6.4 | 87 |
| Newham | 8 | 0 | 8 | 0 | 1.9 | 124 | 3.4 | 21 |
| Redbridge | 17 | 0 | 17 | 2 | 10.1 | 133 | 2.4 | 62 |
| Richmond upon Thames | 86 | 0 | 86 | 0 | 54.1 | 813 | 14.2 | 94 |
| Southwark | 53 | 53 | 0 | 2 | 26.2 | 895 | 31.0 | 70 |
| Sutton | 15 | 0 | 15 | 0 | 4.7 | 206 | 4.7 | 67 |
| Tower Hamlets | 58 | 58 | 0 | 3 | 29.7 | 890 | 45.1 | 86 |
| Waltham Forest | 15 | 15 | 0 | 0 | 3.6 | 117 | 3.0 | 43 |
| Wandsworth | 46 | 0 | 46 | 0 | 29.8 | 303 | 8.8 | 68 |
| Westminster | 56 | 56 | 0 | 0 | 76.5 | 3,993 | 186.0 | 97 |
| London | 1,093 | 646 | 447 | 53 | 15.4 | 19,220 | 12.2 | 84 |

An area is given to the authority that holds most of the land it has in London. So an authority's count may hold an area that its neighbour provided, where the area lies over the line between them. 12 of the 1,093 come from a provider other than the one that gives most of the authority's areas.

**An area may be given to an authority that holds little of it.** Of the 1,093, the authority holds under half of 19, of all that the outline encloses. 13 of them lie wholly in London and take in water, such as the tidal river, which is no part of the land. The other 6 lie mostly outside London and cross its edge: 4 are given to Hillingdon, 1 to Croydon and 1 to Richmond upon Thames. The land of such an area that is in London is conservation land, and is counted. But the area says nothing of what the authority sent. So an authority is covered only where it holds half or more of one area. Every authority holds most of 4 areas or more, so no figure moves.

**Croydon's one `authoritative` record is such an area.** Croydon holds under 1 in 100 of it. Every area that Croydon holds most of is marked `some`. So the table gives 13 authorities with no `authoritative` record, and 14 rest wholly on `some`.

### Is a count believable

| What was looked at | What it shows |
|---|---|
| The total | 1,093. No count of London's conservation areas was read to hold it against |
| The fewest | 4, 8 and 11, in three outer authorities. Each also has few listed buildings and little land in a conservation area, so the three figures agree with one another |
| Quality | By the records given to each, 13 authorities rest wholly on records marked `authoritative`, 13 wholly on records marked `some`, and 7 on both. By the areas each holds most of, it is 14, 14 and 5 |
| Areas at nought | 156 of the 262 areas at nought are in the 14 authorities that rest wholly on `some` |
| Second records | 53, in 11 authorities. More than half are in Hounslow, Hillingdon and Bexley |
| Listed buildings inside a conservation area | 84 in 100 across London. It is lowest where there are few of either. No authority has many listed buildings and few of them in a conservation area, which is what a missing area would look like |

**What this cannot show.** That an authority sent every one of its areas. The file does not say how many an authority has. Nor does the file or the dataset page say what `authoritative` and `some` mean. The page says the dataset "Contains some data created by MHCLG", which is being replaced "with data from authoritative sources". A record marked `some` is taken here to be one that is not yet from such a source, and it may be older than the authority's own list. One provider may give records of both kinds. Where an authority has made a new conservation area, or widened one, since such a record was made, the figure is too low, and a nought may not be a true nought.

**What would settle it.** A person reads each authority's own page and counts. The 14 that rest wholly on `some` come first: Bexley, Bromley, Croydon, Ealing, Greenwich, Harrow, Havering, Islington, Merton, Newham, Redbridge, Richmond upon Thames, Sutton and Wandsworth. An authority's page is its own copyright, and the registry holds the appraisals as `held`. Counting the areas a page lists reads no more than a number, and copies nothing.

## 4. The figures

Across London's 1,002 areas, as worked out on 2026-09-24.

| Measure | Areas with a figure | Lowest | Middle | Highest | Areas at nought | Where the highest is |
|---|---|---|---|---|---|---|
| `conservation_cover`, in 100 | 1,002 | 0.0 | 7.75 | 100.0 | 262 | Westminster |
| `listed_buildings`, for each km² | 1,002 | 0.0 | 3.9 | 414.3 | 125 | Westminster |
| Listed entries for each 1,000 homes, where a home is a household counted at the census of 2021. It joins no release | 1,002 | 0.0 | 1.45 | 302.4 | 125 | Westminster |

A census of 2021 is not today: homes built since are in no count of homes here.

The areas at nought for conservation cover are spread over outer London: the authorities with the most are Newham, Croydon, Barnet, Redbridge, Barking and Dagenham, and Havering. Each of those areas is in an authority the file covers, and no conservation area touches it.

## 5. Do they tell areas apart

Said in words. The rank correlations behind it were worked out across the 1,002 areas, against homes per hectare and against the distance from a point at Charing Cross to the middle of each area. The tables are kept beside the release, and are no part of the repository.

- **Both follow the centre, and neither is only the centre.** Conservation cover follows it about as far as homes built before 1919 do. Listed buildings follow it further. Homes per hectare follow it further still.
- **The two agree with one another more than either agrees with anything else.** Where much land is in a conservation area, the list is thickly marked. So the two are close to one thing measured twice: what the state has chosen to protect.
- **Each agrees only in part with homes built before 1919.** Old homes are widespread in places that nothing protects. That is what the two add: they tell a protected old street from an old street.
- **For each square kilometre, listed buildings are close to a map of the centre and of density.** For each 1,000 homes they follow both much less. But that reading puts first the places with few homes, for that reason alone: the City of London has 125 entries for each 1,000 homes and Westminster 42. The two readings put the areas in much the same order, and the same 125 areas are at nought in both.
- **Grade I and grade II\* alone are too few to rank on.** 583 of the 1,002 areas hold none.

## 6. What becomes of the vibes

### Built age

Core's recipe is 35 homes built before 1919, 25 conservation cover, 20 listed buildings, and 20 homes built since 2000 read low.

| What a build holds | In 100 of the recipe | Areas with a band |
|---|---|---|
| Homes built before 1919 alone, as before | 35 | None |
| With conservation cover and listed buildings | 80 | 979 |
| With homes built since 2000 as well, worked out roughly for this page alone | 100 | 1,002 |

The 23 areas with no band have no figure for old homes: their publisher withholds the count. They have 45 in 100 of the recipe, and core asks 60.

**Would someone who knows London recognise the map.** At the Historic end, yes. The authorities with the most of their areas in the highest band are Westminster, Kensington and Chelsea, Hammersmith and Fulham, Camden and Islington, then Lambeth, Hackney and Richmond upon Thames. Nine authorities have no area in the highest band: Barking and Dagenham, Bexley, the City of London, Harrow, Havering, Hillingdon, Redbridge, Sutton and Waltham Forest.

**At the Newer end, not yet.** The lowest band is mostly in outer London: Barking and Dagenham, Havering, Bexley, Harrow and Brent have the most of their areas in it. Those are areas with few old homes, little protected land and few listed buildings. They are not areas of new homes: in the lowest band the middle area has about 9 homes in 100 built since 2000, and London's middle area has about 11. Until homes built since 2000 are in the recipe, the low end says "not historic", and the name of that end says "Newer".

**The City of London has no area in the highest band**, though it has the most listed buildings for each square kilometre of any authority. It has few homes built before 1919, and old homes are the largest part of the recipe.

**With the fourth part, the order moves little.** Two areas in three keep their band, and the rest move by one. The authorities where the most areas move toward Newer are Tower Hamlets and Southwark, which is what the fourth part is for. The fourth part was worked out roughly, from the same table as old homes, with a count too small to publish read as nothing. It is not yet built as a measure.

**The vibe leans on the centre more than any of its parts.** Each part follows the centre in part, and the recipe adds them up.

### Village feel

Core's recipe is 25 independent places, 20 a small centre, 20 a compact centre, 20 homes built before 1919, and 15 conservation cover. A build now holds 35 in 100 of it. No area has a band, and none should: the three parts that say whether a place has a centre of its own are not built.

## 7. The credit

The registry held two sentences for each source. The dataset page of each holds four:

> © Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026. The Historic England GIS Data contained in this material was obtained on [date]. The most publicly available up to date Historic England GIS Data can be obtained from HistoricEngland.org.uk

| What | How it stands |
|---|---|
| How it was read | Each page was read three times on 2026-09-24, through a reader that extracts, asked in different words each time. Each reading gave the same statement, letter for letter |
| Is it verified | No. An extraction is not the page. `attribution_verified` stays false until a person has read it in a browser |
| The date | The statement asks for the day the data was obtained. That is the day the file was retrieved, which its receipt gives. The entry now asks for it |
| The last sentence | It ends with no full stop on the page, and the entry writes it so |
| The conservation areas | The page gives Historic England's statement for the whole dataset, though many of its records are an authority's own. The entry records what the page gives |

A release carries the credit as the registry writes it, with the day the file was retrieved beside it. It does not put the day into the sentence. [The design page](../../design/heritage-measures.md) says what must change for that.

## 8. What is to fetch

Nothing that either measure needs. One file would put a name to each provider's number:

| File | Why | Where its address is |
|---|---|---|
| The platform's dataset of organisations | To say which authority a provider is, so that a record an authority gave can be told from one a neighbour gave | Not read. It is a dataset of the same platform, and would need an entry of its own in the registry |

It is not in any list, because no page of it was opened. It changes no figure.

## 9. Questions for the founder

| # | Question | What it would change |
|---|---|---|
| 1 | Is every London authority's count of conservation areas to be held against the authority's own page before Built age is served | Whether 14 authorities rest on records that may be out of date. 156 of the 262 areas at nought are in them. A person can count the 33 in an afternoon |
| 2 | Is "Listed buildings" the right name for a count of entries, where one entry may be a terrace or a milestone | The name is core's. The definition and the line beside the figure say what an entry is |
| 3 | Should listed buildings be for each square kilometre, as core has it, or for each 1,000 homes, as the design of the data once had it | For each square kilometre follows the centre more. For each 1,000 homes puts places with few homes first |
| 4 | May Built age be served on three of its four parts | Its low end is named "Newer", and until the fourth part is in, the low end is the suburbs built between the wars |
| 5 | Should likeness count both conservation cover and listed buildings | Core counts both. The two are close to one thing, so likeness counts it twice |
| 6 | Is printing a figure made from a source registered for `scoring` a use of it for `display` | The contract asks this of every such source. Both entries here are registered for `scoring` alone |

## 10. What was not read

- Historic England's own site, and its own terms. The registry approves the copy on the platform alone.
- Any planning authority's page, appraisal or map.
- The platform's other formats: CSV, JSON and Parquet.
- The name, the reference, the notes and the link of any record.
