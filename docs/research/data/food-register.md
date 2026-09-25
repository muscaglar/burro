# The food hygiene register: what the files hold, and what was built on them

Written 2026-09-24. A dated snapshot, not a source of truth.

**Since it was written.** The founder decided that the count and the places for each 1,000 homes are both shown, and that a wish for places to eat and drink is ranked on the second. Core says so, and a build carries both: rows 2 and 6 of section 11 are done. Going out was then made of the second figure, a high street and culture venues, and counted no pub. **The pubs have since been held to a second source,** the file of places, which did not confirm them: [what the file gave](cafes-gyms-and-pubs.md), section 4. Pubs and bars are counted from that file, and are in Going out again. The founder accepted on 2026-09-25 that the file stands in the register's place, so row 7 of section 11 waits on nobody. The register's pubs alone are carried by no release. Where this page says that the two measures are held back, or that the second figure is not ranked on, it says what was so when it was written.

**No person has checked anything here.** Every count was made by a program. The 33 files were first fetched on 2026-09-23, and fetched again on 2026-09-24 so that a receipt could be written for each: every receipt gives 2026-09-24 as the day its file was retrieved. They are extracts of 2026-09-09 to 2026-09-16.

A second program, written apart from the first and sharing only the licence gate with it, worked the figures out again and read this page. Section 12 says what it found and what was done about each finding. Where a figure looks wrong, that is a finding and it is written down as one.

No business is named on this page, and nothing of one is given: no name, no address and no rating. No figure is said of a named neighbourhood or of a named area. A borough is named with a count where the count is of its council's file. One borough of London is a single area, so no figure of that borough is given. Every other figure is in a folder that git ignores.

Contains public sector information licensed under the Open Government Licence v3.0. Source: Food Standards Agency.

## 0. In short

| Question | Answer |
|---|---|
| What is it | The register that councils keep of every business that serves or sells food. One file for each of London's 33 authorities |
| How many businesses | 81,529. Each file holds as many as its own header says |
| How many are places to eat and drink | 40,558: 27,262 of the kind restaurant, cafe or canteen, 3,866 of the kind pub, bar or nightclub, and 9,430 of the kind takeaway or sandwich shop |
| How many have a point on the map | 67,268 of all, which is 83 in 100. Of the places to eat and drink, 37,013, which is 91 in 100 |
| Is the count of places to eat and drink a true count | Yes, of what the register lists and gives a point for. Two programs came to the same figure for every area |
| Does the count say something that density does not | Little. About an eighth of its order is its own: section 9 |
| Can it carry pubs alone | No. Pubs alone follow how a council fills in the register as much as they follow pubs: section 6. The measure is held back from every release and every vibe |
| Can it carry places to eat alone, or takeaways alone | They are worked out and not put forward. The kinds do not part the two well: section 6 |
| What would tell areas apart | The places for each 1,000 homes within the same reach. It follows density half as closely. It reads highest where few homes are, so it is put forward as shown and not ranked on |
| What is in a release | Nothing. The two measures that core has an id for are worked out at every build and held back, whatever core's catalogue says: section 9 |
| What is for the founder | Section 11 |

## 1. The files

| | |
|---|---|
| Registry id | `fsa-food-hygiene-ratings`, approved for `scoring` and `validation_only` |
| Files | 33, named `FHRS501en-GB.xml` to `FHRS533en-GB.xml`. 1.3 to 5.7 MB each, 80.4 MB together |
| Kind | XML, all on one line. No document type and no entity |
| Edition and period | The day in `Header/ExtractDate`. 24 files say 2026-09-16, 4 say 2026-09-15, and one each says 2026-09-13, 12, 11, 10 and 9 |
| Receipt | Every file has one, written on 2026-09-24. It states the day the header states |
| Read by | `derive/food_register.py`, through `Inputs.open_each`, which asks the licence gate first |

The step `describe` cannot read XML. It says `kind: not_read` and `looks_like: xml`, and gives the size and the hash. So the files were walked by a program that kept the name of every element and the text of five: the kind and its number, the authority's code and name, and the scheme. Of every other element it kept only whether it held text.

## 2. What the licence registry allows, and what it forbids

The entry has seven conditions. Each is a rule of the parser and of the measures, and `derive/food_register.py` writes them at its head.

| The registry says | What was done |
|---|---|
| Use for counts, the kind of business and chains only | A business is counted by its kind, and nothing else is worked out |
| Never show a rating | No rating is read: not its value, its key, its date or its scores |
| No logo of the agency or of the scheme | None. The agency is named in words |
| Show the date of the data beside every figure | A figure carries the days of the extracts: 2026-09-09 to 2026-09-16 |
| Never show or export a row of a business | The parser reads no name and no address. A line that prints the register prints counts |
| Do not imply that the agency endorses anything | No sentence says so, and a test holds the sentences to it |
| OpenStreetMap never drops, adds or corrects a record | No record is dropped, added or moved |

The entry does not allow `display`. So a count is a figure for ranking, and whether a count may be printed on a screen is still open: [the sources plan](../../design/london-data-sources.md) leaves it to the founder.

**The day of an inspection is not read.** `RatingDate` is in every record and holds text in 71,336 of 81,529. It is the one element that would say how old a record is. The first condition allows counts, the kind of business and chains, and names no element. So the day was treated as part of a rating, and no value of it was read by either program. One condition added to the entry would settle it: section 11.

## 3. The elements of a record

A file is the root `FHRSEstablishment`, a `Header` of three elements, and an `EstablishmentCollection` of one `EstablishmentDetail` for each business.

| Element | In how many of 81,529 | Read | Why |
|---|---|---|---|
| `Header/ExtractDate`, `ItemCount`, `ReturnCode` | Every file | Yes | The day, the register's own count, and whether the extract succeeded |
| `BusinessType`, `BusinessTypeID` | All | Yes | The kind, in words and as a number. Each is held to the other |
| `LocalAuthorityCode` | All | Yes | The authority, held to the name of the file |
| `Geocode` | All. Empty in 14,261 | Yes | Whether the business has a point |
| `Geocode/Longitude`, `Geocode/Latitude` | 67,268 | Yes | The point |
| `BusinessName` | All | Never | A name may be a person's |
| `AddressLine1` | 58,987 | Never | An address may be a home |
| `AddressLine2`, `AddressLine3`, `AddressLine4` | 53,072, 44,782 and 29,703 | Never | The same |
| `PostCode` | 70,866 | Never | The same. And no postcode directory has a receipt |
| `RatingValue`, `RatingKey`, `RatingDate`, `Scores`, `NewRatingPending` | All. `RatingDate` holds text in 71,336 | Never | The registry forbids a rating |
| `RightToReply` | 10 | Never | It is about a rating |
| `FHRSID`, `LocalAuthorityBusinessID` | All | Never | They name one business |
| `LocalAuthorityName`, `LocalAuthorityWebSite`, `LocalAuthorityEmailAddress` | All | Never | Not needed. The name is not written as the statistics office writes a borough |
| `SchemeType` | All. Always `FHRS` | Never | Not needed |

An element that does not apply is left out. A business with no point has an empty `Geocode`. The parser stops at an element that is not on this list, so that a person says whether a new one may be read.

A longitude is written with up to 18 decimal places, and a longitude beside the meridian as a power, such as `5.2E-05`. The file does not say which datum its points are on. They are taken to be on WGS84.

## 4. The kinds, and how many of each in London

The register names fourteen kinds. Its own kind decides what a business is. No rule is made from a name.

| The register's kind | Its number | Businesses | With a point | It is |
|---|---|---|---|---|
| Restaurant/Cafe/Canteen | 1 | 27,262 | 24,671 | A place to sit and eat |
| Retailers - other | 4613 | 16,733 | 15,027 | A shop that sells food |
| Takeaway/sandwich shop | 7844 | 9,430 | 8,777 | A takeaway |
| Other catering premises | 7841 | 8,053 | 2,867 | None of these |
| Hospitals/Childcare/Caring Premises | 5 | 4,682 | 4,050 | None of these |
| Pub/bar/nightclub | 7843 | 3,866 | 3,565 | A pub or a bar |
| School/college/university | 7845 | 3,501 | 2,837 | None of these |
| Mobile caterer | 7846 | 2,595 | 867 | None of these |
| Retailers - supermarkets/hypermarkets | 7840 | 2,319 | 2,220 | A shop that sells food |
| Manufacturers/packers | 7839 | 1,136 | 766 | None of these |
| Hotel/bed & breakfast/guest house | 7842 | 972 | 908 | None of these |
| Distributors/Transporters | 7 | 669 | 502 | None of these |
| Importers/Exporters | 14 | 278 | 195 | None of these |
| Farmers/growers | 7838 | 33 | 16 | None of these |
| All | | 81,529 | 67,268 | |

What is left out of every count, and why:

- A hotel is a place to stay. The register does not say whether it has a place to eat.
- A van has no place of its own. Two in three have no point.
- A caterer of the kind "other catering premises" has, in six cases of ten, no address at all.
- A school, a hospital and a nursery feed those they serve.
- A shop that sells food is a shop. The parser names it as one, and no measure counts it yet.

What the kinds cannot tell apart: a restaurant from a cafe from a canteen at a workplace, a pub from a nightclub, and a takeaway from a sandwich shop. The register has no field for what a place sells, and none for a chain.

## 5. How a place is given

| A business has | Businesses |
|---|---|
| A point and a postcode | 66,756 |
| A point and no postcode | 512 |
| A postcode and no point | 4,110 |
| Neither | 10,151 |

- **One business in six has no point.** It is counted with its kind and is put nowhere. It is never put at the centre of its authority.
- **A postcode is not read.** The design would place a business with no point by its postcode. The postcode directory has no address in the list and no receipt, so nothing can be placed that way yet.
- **Many businesses share a point.** The 67,268 points are 47,674 different points, and 28,341 businesses stand on a point that another shares. The most on one point is 202. Of the 37,013 places to eat and drink with a point, 38 in 100 stand on a point that another of them shares. So a point looks to be the point of a postcode and not of a door. The file does not say.
- **A few points are far from London.** 28 lie more than 2,000 metres from the centre of any output area of London, and some are in another part of the country. An authority lists a business, and the business may stand elsewhere. Such a point is within reach of no home.
- **An authority's businesses lie in its borough.** For each of the 33 files, most of its points stand nearest to the homes of one borough, and each borough is that borough for one file. The build holds the register to this before it reads nought as a count.

Of the 40,558 places to eat and drink, 3,545 have no point. What each holds of an address was counted by whether an element holds text, and no text was kept:

| Kind | With no point | Hold a line of an address | Of those, hold a postcode | Hold nothing of an address |
|---|---|---|---|---|
| Restaurant, cafe or canteen | 2,591 | 1,468 | 1,332 | 1,123 |
| Pub, bar or nightclub | 301 | 292 | 273 | 9 |
| Takeaway or sandwich shop | 653 | 348 | 313 | 305 |
| The three together | 3,545 | 2,108 | 1,918 | 1,437 |

- **A place to eat with no point is of two sorts.** 1,468 have an address, and a postcode would put most of them on the map. 1,123 have nothing of an address: the register does not say why, and they may trade from a home. They are not read as restaurants that are missing.
- **A pub with no point is a real pub.** 292 of 301 have an address. It stands somewhere, and it is within reach of nobody in the figures.
- **The postcode directory would place 1,918** of the three kinds, and 4,110 businesses of every kind.

## 6. What differs from one council to the next

Three things differ, and each moves a figure.

**How many businesses have a point.** Of the three kinds that count together, 91 in 100 have a point in London as a whole. By authority the share runs from 68 to 98 in 100, and the middle authority has 95. It is under 80 in five:

| Authority | Places of the three kinds | With a point, in 100 | Places to eat with a point, in 100 |
|---|---|---|---|
| Redbridge | 1,307 | 68 | 55 |
| Richmond upon Thames | 926 | 73 | 70 |
| Merton | 766 | 73 | 69 |
| Havering | 992 | 77 | 70 |
| Bromley | 1,165 | 79 | 75 |

Most of what is missing in these five has no address at all. In Redbridge 389 places to eat have none, in Havering 209, in Bromley 131 and in Merton 120. If those trade from homes, the count of places to walk to is nearer right than the share suggests. The file cannot say.

Does the missing share show in the figures? For the three kinds together it does not. Once how built up and how central an area is are taken out, what is left of the count of a borough does not follow the share of its places that have a point: a rank correlation of -0.04 across the 33 boroughs by one program, and -0.09 by the other. Redbridge and Havering read high for their density. For takeaways it does show: +0.41. Camden gives a point for 76 in 100 of its takeaways, and 183 have none.

**For pubs the loss is real.** Nearly every pub with no point has an address. The share of pubs with a point is under 85 in 100 in five authorities:

| Authority | Pubs listed | With no point | With a point, in 100 |
|---|---|---|---|
| Bromley | 176 | 61 | 65 |
| Waltham Forest | 89 | 23 | 74 |
| Richmond upon Thames | 129 | 29 | 78 |
| Islington | 226 | 40 | 82 |
| Hackney | 129 | 22 | 83 |

A figure of pubs for an area under one of these five reads low.

**Which kind a business is given.** Each council gives a business its kind. Of its places to eat and drink, Westminster lists 4 in 100 as a pub, a bar or a nightclub, and Bexley 18 in 100. The middle authority lists 9. Westminster lists 158 of that kind among 5,732 businesses, and 3,528 places to eat. By the pubs within reach of its typical home, Westminster stands ninth of the 33 boroughs.

Three things were found of pubs alone:

- Across the 33 boroughs, what is left of the pubs of a borough, once how built up and how central it is are taken out, follows the share of its places that the council lists as a pub: a rank correlation of +0.75 by one program, measured from the middle of London's homes, and +0.79 by the other, measured from Charing Cross. It does not follow the share of pubs that have a point: -0.01. So the figure cannot tell an area with few pubs from an area whose council lists its pubs as places to eat, and nothing in the store can.
- The second program drew 100 of the pubs that are counted, by a fixed seed, and each was judged by its name. 13 were a members', sports or social club. 3 were a hall, a theatre or a bowling alley. 3 were a kitchen that trades inside a pub. 2 could not be told. So 19 in 100 are plainly not a pub that a person can walk into. The names were read for the sample alone. None is in a tracked file, and the first program has not repeated the sample: the parser reads no name.
- The same was done for 100 places to eat. 81 read as a place to eat. 4 were plainly the canteen of a workplace or a caterer under a contract. 6 read as a takeaway by their name. 9 could not be told.

So the three kinds together compare better from one council to the next than any one of them does. Pubs alone are held back. Places to eat and takeaways are not put forward to be shown apart.

## 7. What marks a business that trades from a home, a van or a market

| | What the register gives |
|---|---|
| A van | Its own kind, `Mobile caterer`: 2,595 businesses. 1,553 of them have no address |
| A home | No element marks one. 10,151 businesses have no postcode and no point, and most of those have no line of an address. Of "other catering premises" 4,883 of 8,053 have no line of an address. The file does not say why an address is left out |
| A market | No element marks one. Many businesses on one point may be a market, a food hall or a shopping centre. No rule was made from it |

So a measure leaves out a van by its kind, and leaves out a business with no address because it has no point. It cannot leave out a stall in a market, and it does not try.

## 8. The register held to its own totals

| Check | Result |
|---|---|
| Each file against its header | The parser stops at a file that does not hold as many businesses as `ItemCount` says. All 33 hold what they say: 81,529 together, from 1,318 to 5,732 a file |
| The kinds against the file | The counts of the fourteen kinds add up to the count of the file, in every file |
| The header against the publisher's page | The list of files records the count the page gave for each authority when it was read on 2026-09-23: 81,570 together. The headers say 41 fewer. No authority differs by more than 16, and the page was read a week after most extracts |
| The sum of what is within reach, counted two ways | Counted from each home and counted from each place, the pairs of a home and a place within 800 metres are 2,185,994 and 2,185,979. They differ by 15, because a distance is measured at the latitude of the home |
| The figures, worked out twice | The second program came to the same figure as the first for every one of 1,002 areas, in all eight series, once it measured a distance as the first does |
| A figure followed to its files | The second program drew 30 figures by a fixed seed. Each row of evidence holds its figure, names its method and 36 files, each file has a receipt, and the bytes of each hash to what its receipt says |

No page of the publisher gives a count by kind, so the count of each kind is held to the file alone.

**The last digit of a figure is not known.** The second program first measured each distance on the National Grid, where the first measures it on the ground from a longitude and a latitude. The two differ by under 10 centimetres. 167 of 2.19 million pairs lie that near to 800 metres and fall the other way, and many places share a point, so one point moves several. 59 of the 1,002 counts of the three kinds then differ, 55 by 0.1 and 4 by 0.2. A figure is given to one decimal place because it is a mean over homes. Whether it is shown as a whole number is the founder's to say.

## 9. What was built, and whether it says something

Four measures are worked out, by `derive/venue_food_drink.py`. Each is the places of its kinds within 800 metres of the centre of each output area, in a straight line, as the mean over the area's homes. A second figure is the places for each 1,000 homes within the same reach.

| Measure | Kinds | Id | In a release | Why not |
|---|---|---|---|---|
| Places to eat and drink | The three together | `venue_food_drink`, core's | No | Held back until the founder has decided. And core gives it for each square kilometre |
| Pubs and bars | Pub/bar/nightclub | `venue_evening`, core's | No | Held back until the kind is held to a second source. And core names it evening venues, for each square kilometre |
| Places to eat | Restaurant/Cafe/Canteen | `venue_eat`. Core has none | No | Not put forward to be shown on its own |
| Takeaways | Takeaway/sandwich shop | `venue_takeaway`. Core has none | No | The same |

Each has a figure for 992 of 1,002 areas: 962 for all their homes, 30 for part of them, and 10 have none. London's lowest and middle figure for each, and the figure that nine areas in ten do not pass, are held by the test of the measures on the real files, and are not repeated here. No highest figure is held or given: one area of London is a borough on its own, and it leads two of the series.

**A measure that is held back.** A build works such a measure out and leaves it out, by the rule `measure_is_not_held_back`, whatever core's catalogue says of it. Its own module says what a check found and what would settle it, in `HELD_BACK`, and the coverage report prints it. It is the fourth case in which a build leaves a measure out. It was added here, and it is the founder's to approve or to take out.

It matters because core's catalogue is changing. Had core come to name the count as the measure does, a build would have carried it, and core would have scored the tag `foodie` from it alone: the count is 60 in 100 of that recipe, which is what core asks before it scores a tag. A test builds so, on made-up files, and holds that this is what would happen.

**The edge of London.** A home near the edge may be within reach of a place outside London, and no file of an authority outside London is in the store. The rule asks where homes are: an output area has no count where the centre of an output area outside London lies within 800 metres of its own.

| | By the rule, which asks about homes | By land, which the second program measured |
|---|---|---|
| Output areas with something outside London within 800 metres | 311 | 715 |
| Their homes | 40,373, which is 1.2 in 100 of London's | 93,080 |
| Areas touched | 40, in 13 boroughs | 71, in 14 boroughs |
| Districts beyond | 11 | 15 |

- **404 output areas are counted as whole though land outside London is within their reach.** They hold 52,707 homes, 1.5 in 100 of London's. No home stands on that land within reach, and a place to eat may. In 9 areas half or more of the homes are so counted, and in 30 a fifth or more. 13 of the 60 output areas with no place to eat or drink within reach are among them, and 73 of the 2,072 with no pub.
- The second program measured this against the outlines of output areas, which it read through the gate for `cells`. The first program has not repeated it.
- **The two methods said more than the rule does.** Each said that a figure is not given where too few homes are in an output area "whose whole reach the source covers". Each now says what the rule is, and that land outside London may be within reach of an output area that is counted.
- For each 1,000 homes within reach, the output areas that are counted within 400 metres of land outside London read 7.5, and those 800 to 1,200 metres in read 6.8. So there is no sign in the figures that the first are short of places for their homes. It is no proof that they are not.
- By the rule, 30 areas have a figure for part of their homes and 10 have none.
- The eleven districts with homes within reach are Broxbourne, Buckinghamshire, Dartford, Elmbridge, Epping Forest, Epsom and Ewell, Hertsmere, Reigate and Banstead, Spelthorne, Tandridge and Three Rivers. The four more with land within reach are Brentwood, Sevenoaks, Slough and Thurrock. The files of all fifteen would close the gap.
- A rule that asks about land needs outlines that the licence registry gives for `scoring`. The output area boundaries are given for `cells`, `gazetteer` and `display`. The LSOA boundaries are given for `scoring`, and their entry says what they do there: the land area of an LSOA, and placing data published by LSOA. Saying where London ends is neither. So no outline was read for the rule.

**Does a count say something.** The first look at another source of venues found that its count of places to eat stood in almost the order of a plain count of everything it held: a rank correlation of 0.96. The same was asked here, across the 992 areas that have a figure. Both programs asked it. Measured from one centre they agree to within 0.01. The figures below are measured from the middle of London's homes, which the files give. The second program measured from Charing Cross as well, which moves a figure by 0.02 at most.

| The order of | Every business within the same reach | Every kind but its own | Homes per hectare | Distance from the centre | The share that density and the centre give | What is left, against what is left of every other kind | The share that is its own |
|---|---|---|---|---|---|---|---|
| The three kinds, count | 0.99 | 0.93 | 0.81 | -0.74 | 0.69 | 0.77 | 0.13 |
| The three kinds, for each 1,000 homes | 0.80 | 0.71 | 0.49 | -0.44 | 0.24 | 0.62 | 0.47 |
| Places to eat, count | 0.96 | 0.90 | 0.79 | -0.74 | 0.66 | 0.69 | 0.18 |
| Pubs, count | 0.78 | 0.76 | 0.66 | -0.66 | 0.49 | 0.46 | 0.40 |
| Takeaways, count | 0.85 | 0.81 | 0.71 | -0.58 | 0.51 | 0.57 | 0.33 |

- **The first look's finding is repeated by a true count.** The count of the three kinds stands in the order of every registered business within the same reach: 0.99.
- How built up an area is and how central it is give about seven tenths of its order. Once both are taken out, what is left follows what is left of every other kind of business at 0.77. So about an eighth of the order is the measure's own.
- So a count is a true count, of a register kept by law, and on its own it says little more than that an area is dense and central. A vibe built on the count alone would be a vibe of the centre, as the first look feared.
- Pubs and takeaways follow density less. Pubs follow the council's way of listing instead: section 6.

**Does the second figure say more.** Yes.

- For each 1,000 homes within reach, density and the centre give about a quarter of the order of the three kinds, and nearly half of the order is its own.
- An area moves by a median of 9 places in 100 of the order between the count and the second figure, and 193 of 992 areas move by 20 or more.
- It reads highest where few homes are. An area of offices leads it.
- It divides the places the register lists in 2026 by the homes of the census of 2021. Where many homes have been built since, it reads too high.

**Which the product should rank on.** It is the founder's to decide, and the measure is held back until it is decided. What the two programs put forward:

- Rank a wish on the count of the three kinds together. A person who asks for somewhere to eat asks how many places are within a walk. The second figure puts an area with few homes and few places above an area with many of both, which is not what was asked.
- Show the count with words that say it follows how built up an area is. `CANNOT_SEE` holds them.
- Show the places for each 1,000 homes beside it, and do not rank on it.
- Build no vibe on the count alone.

**The distance moves little.** The areas stand in nearly the same order at 600 metres and at 1,000 as at 800: 0.98 and 0.99. At 400 it is 0.94.

**Is the order believable.** By the typical home of each borough, the order of the three kinds together is believable on its face: the boroughs about the middle of London stand first, with Westminster second, and the outer boroughs stand last. The order of pubs is not: Westminster stands ninth. No person has looked at a map of either.

## 10. What a figure cannot see

Each line is shown beside a figure, from `CANNOT_SEE` in the module of the measure.

| It cannot see | Why |
|---|---|
| A place that has closed and is still listed | A register is as old as its last visit. The file has no field for closed |
| How long ago a place was last seen | The day of the last inspection is in the file, and it is not read: section 2 |
| A place that trades and is not registered | It is not in the register |
| A business with no point | It is counted by kind and is within reach of nobody. An area under a council that gives few points reads low |
| Where the door is | Many places share a point, so a place near the end of the reach is counted or missed by where its point was put |
| A walk | The distance is a straight line. No network of streets is built |
| What a place sells, what it charges, when it is open | The register has no field for any |
| A canteen from a cafe | One kind holds both |
| A place outside London | No file of an authority outside London is in the store. Where only land outside London is within reach, the homes are counted and a place on that land is missed |
| Whether a council gives kinds as its neighbour does | Nothing in the file says |
| More than how dense and central an area is | The count follows both: section 9 |
| Homes built since the census | Homes are weighed as they stood in 2021 |

The figure for each 1,000 homes has two lines of its own: that it divides the places of one year by the homes of another, and that it reads highest where few homes are.

## 11. What is needed

| # | What | Whose |
|---|---|---|
| 1 | A unit and a name in core for a count within reach of homes, in a straight line. Core gives `venue_food_drink` for each square kilometre. The measure says unit `count` and label `Places to eat and drink within 800 m of home, in a straight line` | Core's |
| 2 | A feature in core for the places for each 1,000 homes within reach, shown and not ranked on: `venue_food_drink_per_homes`, unit `per 1,000 homes` | Core's |
| 3 | No recipe of a tag that core can score from the count alone. Today `foodie` gives it 60 in 100, and core scores a tag at 60 | Core's |
| 4 | A place in core's record of a feature for the lines shown beside a figure, and the fields the design of the vibes asks for: `basis` homes, `method` measured, and the period as a span of days | Core's |
| 5 | No feature for places to eat alone or for takeaways alone | Core's |
| 6 | Whether a wish is ranked on the count, which words stand beside it, and whether the second figure is shown with it. Then `HELD_BACK` in `derive/venue_food_drink.py` is taken out | The founder's |
| 7 | A second source of pubs to hold the register's kind to. None is registered for it. Until then no release and no vibe carries pubs alone, and the design gives pubs 35 in 100 of Pace. **Settled on 2026-09-25:** the file of places was held against the register, did not confirm it, and stands in its place. The founder accepted it | Nobody's. It was the founder's |
| 8 | One condition added to the registry entry: that the day of the last inspection may be read to count businesses by how long ago they were inspected, and is never shown of one business. The share of places last inspected over three years ago then takes minutes to work out | The founder's |
| 9 | The postcode directory, with a receipt, to place the 1,918 places to eat and drink that have a postcode and no point. It would place 273 of the 301 pubs | The founder's |
| 10 | The files of the fifteen districts with land within reach of London's homes, in the registry and in the list. Or a rule that asks about land: a sentence added to the entry of the LSOA boundaries that says they may be read for where London ends | The founder's |
| 11 | Whether a count may be printed on a screen: the entry does not allow `display` | The founder's |
| 12 | Whether a figure is shown to one decimal place or as a whole number | The founder's |
| 13 | Whether the fourth case in which a build leaves a measure out stands: a measure that a check holds back | The founder's |
| 14 | A person to look at the map | Nobody has |

What was needed and is done: the check that no fact is served without evidence held a row to one file of its source, or to the file of each square of a grid. A measure may now say that its publisher gives a file for each part of the whole. Its row then rests on the file of every part that the lock names, and a row that names some of the register's files and not all is found.

## 12. What the second count found, and what was done

| # | Finding | How grave | What was done | What is left |
|---|---|---|---|---|
| 1 | Pubs alone measure how a council fills in the register as much as they measure pubs | It blocks pubs from the map and from any vibe | `venue_evening` is held back from every release, whatever core says. `HELD_BACK` says why, and the coverage report prints it | A second source. What Pace is made of meanwhile |
| 2 | The count says little that density and the centre do not | Grave | `venue_food_drink` is held back until the founder has decided. The line is shown beside the figure. The second figure is put forward as shown and not ranked on | Items 3 and 6 of section 11 |
| 3 | The rule for where a count is whole asks about homes outside London, not land | Grave | The two methods and the line beside a figure say what the rule is, and claim no more. This page asks for fifteen districts | Item 10 |
| 4 | Nothing says whether a listed place is still open, and the age of inspections was not measured | Grave | The line is shown beside the figure, and the measure says that it waits on it. No day of an inspection was read | Item 8 |
| 5 | Missing points are not spread evenly, and for pubs the loss is real | Grave | Pubs are held back, and what holds them back says so. The line beside a figure says that an area under a council that gives few points reads low. The shares are in section 6 | Item 9 |
| 6 | No written file holds a row of evidence for a venue figure | Small | The check has leave for a row that rests on a file for each authority, so that a release can carry the rows once the hold is lifted | Nothing before then |
| 7 | One decimal place says more than the points know | Small | The line is shown beside the figure, and the module says what the last digit is worth | Item 12 |
| 8 | Places to eat hold canteens, and some takeaways | Small | Places to eat and takeaways are not put forward to be shown apart. `NOT_ALONE` says why | Nothing |
| 9 | The page said the files were fetched on 2026-09-23, and every receipt says 2026-09-24 | Small | The page says both days | Nothing |
| 10 | Two figures of the one area that is a borough stood in a test, as London's highest | Small | No highest figure is held by a test of these measures | The tests of other measures hold a highest figure. Whether that stands is the founder's to say |
| 11 | The second figure divides places of 2026 by homes of 2021 | Small | The line is shown beside the second figure | Nothing |
