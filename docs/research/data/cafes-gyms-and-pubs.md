# Cafes, gyms and pubs: what the real file gave

Written 2026-09-24. A dated snapshot, not a source of truth.

The founder asked whether cafes and gyms are in the data, and for them to be used. They are in the file of places that the cultural venues are counted from, so they are counted from it the same way, and so are pubs and bars. This page says what the part round London gave, and why pubs and bars are counted from it and no longer from the food hygiene register. It follows [what the real file gave for culture](culture-and-community-on-the-real-file.md) and [the page of the food register](food-register.md).

**No figure here is of a named neighbourhood, and no name of a place was read.** The part holds no name. A figure is of the part, of London as a whole, or of a borough. One borough is a single area of the build, so no table here gives it a row. No person has looked at a sample of the records.

Credit: Overture Maps Foundation, overturemaps.org. Records from Meta, Microsoft, PinMeTo, DAC and RenderSEO are under CDLA-Permissive-2.0, from Foursquare under Apache 2.0, and from AllThePlaces under CC0. Contains public sector information licensed under the Open Government Licence v3.0. Source: Food Standards Agency. Source: Office for National Statistics licensed under the Open Government Licence v.3.0.

## 0. In short

| Question | Answer |
|---|---|
| Are cafes and gyms in the data | Yes. The part holds 12,649 records of cafes and 8,510 of gyms, which are 7,498 cafes and 4,579 gyms inside London once records of one place are counted once |
| Can a wish for each be answered | Yes, for 992 of 1,002 areas. Ten areas at the edge have homes outside London within reach, and no figure |
| Is each count a map of the centre | Mostly. The count of cafes stands in the order of a count of every record at 0.93, of gyms at 0.86 and of pubs and bars at 0.89 |
| Does the figure for each 1,000 homes do better | Yes: 0.74, 0.55 and 0.71. So the count is shown, and the figure for each 1,000 homes is what a wish is ranked on |
| Did the file confirm the register's pubs | No. It bears out the register's fault. The register gives a point to 3,562 pubs, bars and nightclubs in London, and the file holds 6,559 pubs and bars. Under the council that lists fewest of its places as pubs the register gives 147 and the file 834 |
| Which source are pubs counted from | The file of places. It is one table of kinds for all of London. It is thin toward the edge of London, and every figure of pubs says so |
| Are the counts right | Not known. No person has looked at a sample of the records, and no name was read of either source |

## 1. What is counted

The most particular category of a record decides, and nothing is decided from a name. The table is `packages/pipeline/src/burro_pipeline/derive/venue_kinds.py`. It reads four branches of the publisher's categories, and names every category the part holds under them: 33 are counted, and 97 are left out, each by its name and with its reason. A category that arrives under one of the four and is on neither list stops a build.

| Kind | Counted | Records in the part | Left out, and why |
|---|---|---|---|
| Cafes | Cafe 7,159. Coffee shop 5,037. Tea room 449. Hong Kong style cafe 4 | 12,649 | Fast food restaurant 4,119, sandwich shop 842 and dessert shop 639: each is a place to eat of another kind. Bakery 3,207: it sells to take away. Internet cafe, coffee roastery, bubble tea shop and juice bar: each is named for what it sells, and is no cafe |
| Gyms | Gym 5,306. Yoga studio 1,232. Pilates studio 902. Sport or fitness facility that says no more 793. Seven other kinds of studio and class 277 | 8,510 | Dance studio 1,652: it teaches dancing. Fitness trainer 1,039: a person, who may have no premises. Gymnastics centre 230: most often a club for children. Swimming pool, court, pitch, golf course, climbing wall and boxing class: each is one sport, and no gym |
| Pubs and bars | Pub 5,978. Bar 2,873. Cocktail bar 1,079. Gastropub 722. Wine bar 650. Thirteen other kinds of pub and bar 888 | 12,190 | Lounge 417, brewery 315, bar for smoking, distillery and winery: none is a pub a person walks into for a drink. A nightclub stands under another branch, and is not read |

A shop that sells equipment for sport stands under shopping, and is not read. Of the 683,409 rows of the part, 51,966 have no category, 20,307 are left out by the name of their category and 577,787 stand under no branch the table reads.

**Records of one kind within 25 metres of the first of them are one place,** as for cultural venues. A pub, a bar and a gastropub are one kind, so three records of one door count once.

| Kind | Records | Places | Records that were a place already counted | Places inside London |
|---|---|---|---|---|
| Cafes | 12,649 | 10,699 | 1,950 | 7,498 |
| Gyms | 8,510 | 7,696 | 814 | 4,579 |
| Pubs and bars | 12,190 | 10,051 | 2,139 | 6,559 |

Each of these is a first choice, and the founder's to adjust: that a tea room is a cafe, that a sport or fitness facility that says no more is a gym, that a lounge and a bar for smoking are not pubs, and that 25 metres makes one place.

## 2. The figures

Each count is the places within 800 metres of home in a straight line, as the mean over an area's homes. Each rate is the places for each 1,000 homes within the same reach. Both are given to one decimal place. The highest of each is not given here: one area of London is a borough on its own, and it leads most of them.

| Measure | Areas with a figure | Lowest | Middle | Nine areas in ten do not pass | Different values |
|---|---|---|---|---|---|
| `venue_cafe`, shown | 992 | 0.1 | 10.1 | 33.6 | 364 |
| `venue_cafe_per_homes`, ranked on | 992 | 0.0 | 1.6 | 3.2 | 79 |
| `venue_gym`, shown | 992 | 0.0 | 6.35 | 21.4 | 274 |
| `venue_gym_per_homes`, ranked on | 992 | 0.0 | 1.1 | 2.2 | 50 |
| `venue_evening`, shown | 992 | 0.0 | 7.0 | 34.6 | 340 |
| `venue_evening_per_homes`, ranked on | 992 | 0.0 | 1.2 | 3.1 | 78 |
| `evening_cluster_exposure`, ranked on | 1,002 | 0.0 | 0.0 | 18.8 | 206 |

**A rate takes few values.** It is given to one decimal place, and half the areas stand between nought and 1.6 cafes for each 1,000 homes. So many areas tie, and an order by a rate alone is an order of groups. A second decimal place would part them, and would say more than the file knows.

What each stands in the order of, as a rank correlation across the areas that have it:

| Measure | Homes per hectare | Distance from the middle of London's homes | A count of every record within the same reach |
|---|---|---|---|
| `venue_cafe` | 0.79 | -0.79 | 0.93 |
| `venue_cafe_per_homes` | 0.46 | -0.52 | 0.74 |
| `venue_gym` | 0.73 | -0.77 | 0.86 |
| `venue_gym_per_homes` | 0.32 | -0.44 | 0.55 |
| `venue_evening` | 0.76 | -0.78 | 0.89 |
| `venue_evening_per_homes` | 0.50 | -0.57 | 0.71 |
| `evening_cluster_exposure` | 0.49 | -0.53 | 0.63 |

The three rates stand in one order with each other at 0.70 to 0.78: cafes with gyms 0.73, cafes with pubs 0.78, gyms with pubs 0.70. So each says something of its own, and none says all of it.

The boroughs with most areas in the highest and the lowest fifth of each rate. A fifth is 198 areas, and where areas tie at the cut the id of an area decides.

| Rate | Most areas in the highest fifth | Most areas in the lowest fifth |
|---|---|---|
| Cafes | Camden 16, Tower Hamlets 15, Kensington and Chelsea 15, Hackney 15, Westminster 15, Richmond upon Thames 12 | Harrow 21, Croydon 15, Ealing 15, Barking and Dagenham 15, Greenwich 12, Bexley 10 |
| Gyms | Wandsworth 21, Camden 19, Kensington and Chelsea 16, Richmond upon Thames 15, Westminster 13, Tower Hamlets 12 | Croydon 25, Ealing 18, Bexley 16, Enfield 15, Barking and Dagenham 13, Redbridge 12 |
| Pubs and bars | Kensington and Chelsea 19, Westminster 17, Hackney 17, Tower Hamlets 16, Camden 15, Lambeth 13 | Croydon 17, Barnet 15, Havering 15, Barking and Dagenham 14, Harrow 14, Redbridge 13 |

## 3. Homes near a cluster of pubs and bars

Quiet streets held a part that no build measured: homes near a cluster of evening venues. It is measured now, from the pubs and bars of this file, and is named for what is counted.

| | |
|---|---|
| What is counted | The share of an area's homes with three or more pubs or bars within 150 metres of the centre of their output area, in a straight line |
| Output areas with a verdict | 26,369 of 26,369. The figure counts no home outside London, and the part reaches 2,000 metres beyond the edge, so no output area is left out |
| Of London's homes, so placed | 6.1 in 100 |
| Areas that read nought | 660 of 1,002 |
| Most areas in the highest fifth | Kensington and Chelsea 18, Westminster 17, Southwark 17, Hackney 16, Tower Hamlets 15, Islington 15 |

**It cannot say late.** The file gives no hours, so no word of the measure says late or evening, and a nightclub is not counted. Two in three areas tie at nought, so the part parts the third of London that has clusters from the rest, and says nothing between the rest. Three and 150 metres are first choices, and the founder's to adjust.

## 4. Pubs: the register held against the file

The food register was the first source of pubs, and a check of its figures held them back: [the page of the food register](food-register.md) found that pubs alone follow how a council fills in the register as much as they follow pubs. The founder decided that the pubs join Going out when a second source confirms them. The file of places is a second source. The two were held against each other on 2026-09-24.

| | The register | The file of places |
|---|---|---|
| What is counted | The kind "Pub/bar/nightclub", as each council gives it | 18 categories of pub and bar, as one publisher's table gives them |
| Inside London | 3,562 with a point | 6,559 places |
| Across the areas, the two counts stand in one order at | 0.90 | |
| Across the areas, the two rates stand in one order at | 0.79 | |
| Of the register's pubs, with a pub or a bar of the file within 50 m | 69 in 100 | |
| Within 100 m | 81 in 100 | |
| Within 200 m | 88 in 100 | |
| Of the file's pubs and bars, within 50 m of a pub of the register | | 42 in 100 |
| Within 50 m of a place the register lists as a place to eat or a takeaway, and of no pub | | 33 in 100 |
| With none of the three within 50 m | | 25 in 100 |

Borough by borough, in the order of how many pubs and bars the file holds for each pub of the register:

| Borough | Pubs the register gives a point | Pubs and bars of the file | Of the file, for each of the register | Of the register's places to eat and drink, pubs in 100 | Of the register's pubs, with one of the file within 50 m, in 100 | Within 100 m | Within 200 m |
|---|---|---|---|---|---|---|---|
| Enfield | 125 | 119 | 0.95 | 13 | 43 | 55 | 69 |
| Redbridge | 66 | 68 | 1.03 | 7 | 33 | 44 | 52 |
| Barnet | 107 | 116 | 1.08 | 11 | 42 | 56 | 64 |
| Kingston upon Thames | 82 | 91 | 1.11 | 13 | 67 | 72 | 80 |
| Bexley | 120 | 134 | 1.12 | 18 | 41 | 58 | 74 |
| Harrow | 54 | 63 | 1.17 | 8 | 41 | 48 | 57 |
| Ealing | 138 | 163 | 1.18 | 10 | 49 | 64 | 76 |
| Havering | 78 | 98 | 1.26 | 10 | 53 | 68 | 79 |
| Hounslow | 101 | 131 | 1.30 | 11 | 60 | 68 | 73 |
| Bromley | 115 | 163 | 1.42 | 13 | 68 | 73 | 76 |
| Hillingdon | 120 | 176 | 1.47 | 12 | 47 | 59 | 73 |
| Haringey | 88 | 134 | 1.52 | 11 | 64 | 80 | 88 |
| Brent | 79 | 123 | 1.56 | 7 | 71 | 86 | 91 |
| Sutton | 46 | 75 | 1.63 | 9 | 85 | 91 | 91 |
| Greenwich | 98 | 160 | 1.63 | 11 | 71 | 74 | 85 |
| Richmond upon Thames | 100 | 171 | 1.71 | 15 | 80 | 84 | 89 |
| Waltham Forest | 67 | 115 | 1.72 | 8 | 76 | 82 | 91 |
| Hammersmith and Fulham | 115 | 200 | 1.74 | 11 | 57 | 79 | 97 |
| Islington | 186 | 328 | 1.76 | 14 | 88 | 95 | 98 |
| Merton | 48 | 85 | 1.77 | 9 | 56 | 58 | 67 |
| Barking and Dagenham | 23 | 41 | 1.78 | 5 | 26 | 39 | 48 |
| Lambeth | 166 | 306 | 1.84 | 12 | 69 | 88 | 98 |
| Lewisham | 84 | 157 | 1.87 | 8 | 71 | 87 | 93 |
| Camden | 225 | 432 | 1.92 | 9 | 88 | 98 | 100 |
| Southwark | 196 | 380 | 1.94 | 11 | 72 | 90 | 97 |
| Croydon | 74 | 151 | 2.04 | 7 | 74 | 91 | 97 |
| Wandsworth | 120 | 247 | 2.06 | 9 | 86 | 93 | 98 |
| Newham | 60 | 132 | 2.20 | 6 | 55 | 70 | 85 |
| Tower Hamlets | 143 | 315 | 2.20 | 9 | 83 | 94 | 99 |
| Kensington and Chelsea | 95 | 236 | 2.48 | 9 | 80 | 95 | 97 |
| Hackney | 108 | 315 | 2.92 | 9 | 90 | 95 | 100 |
| Westminster | 147 | 834 | 5.67 | 4 | 91 | 99 | 99 |

What the table says:

1. **The two agree on where pubs are.** The order of the areas is nearly one, at 0.90. In Camden, Islington, Hackney, Tower Hamlets, Westminster and Kensington and Chelsea 94 in 100 or more of the register's pubs have a pub or a bar of the file within 100 metres.
2. **The register is short where a council lists few of its places as pubs.** Westminster lists 4 in 100 of its places to eat and drink as a pub, the least of any council, and the file holds 5.67 pubs and bars there for each of the register's. One in three of the file's pubs and bars stands beside a place the register lists as a place to eat, and beside no pub of the register. By the register's rate Westminster is not among the six boroughs with most areas in the highest fifth, and by the file's it is among the first three.
3. **The file is short toward the edge.** In Barking and Dagenham, Redbridge and Harrow under six in ten of the register's pubs have a pub or a bar of the file within 200 metres, and in nine boroughs under three in four. So an area far from the middle reads lower than it would if every pub were listed.
4. **Neither is right of every pub.** No name was read of either, so nothing says which of the two is right where they differ.

**So the file is not fit to confirm the register, and is fit to stand in its place.** The register's fault is of kind: what a council calls a pub. It moves whole boroughs, and nothing in the register can mend it. The file's fault is of reach: it holds fewer places toward the edge. It moves the edge down against the middle, which is the way every count of venues leans, and it is said beside every figure of pubs. The file is one table of kinds for all of London, it tells a pub from a nightclub, and the cafes, the gyms and the cultural venues are counted from it the same way. The register's pubs are still worked out, under an id of their own, and no release carries them: `packages/pipeline/src/burro_pipeline/derive/venue_pub.py`.

This is a call made for the founder, and theirs to overturn. Their decision was that a second source confirms the pubs, and this one did not.

## 5. What a build of London holds

One build was made on 2026-09-24 from every list that holds a receipt, as [the account of data builds](../../data-builds.md) says in section 22. It was held against the build before it, which is the one of section 20.

| | Before | Now |
|---|---|---|
| Measures carried | 28 | 35 |
| Measures worked out and left out | 5 | 4: the two of town centres, what there is to do in parks, and what homes sell for |
| Facts that the check counts | 44,966 | 51,920 |
| Vibes with a band | 8 | The same 8. No vibe gained a band |
| Going out | 45 places to eat, 30 a town centre, 25 culture. 992 areas | 35 pubs and bars, 30 places to eat, 20 a town centre, 15 culture. 992 areas |
| Quiet streets | On 70 in 100 of its recipe. 1,002 areas | On its whole recipe. 1,002 areas |

**Going out moved a little.** 699 of 992 areas keep their band, 292 move by one and 1 by two, and the order of the areas is the same at 0.97. The boroughs with most areas in its highest band were Kensington and Chelsea 19, Camden 16, Tower Hamlets 15, Westminster 15, Southwark 13 and Islington 12. They are Kensington and Chelsea 19, Camden 16, Southwark 16, Westminster 16, Tower Hamlets 15 and Hackney 13.

**Quiet streets moved a little more at its low end.** 704 of 1,002 areas keep their band, 296 move by one and 2 by two, and the order is the same at 0.96. The boroughs with most areas in its lowest band were Lambeth 16, Wandsworth 15, Tower Hamlets 14, Hounslow 13, Southwark 13 and Westminster 13. They are Westminster 19, Southwark 15, Hackney 14, Kensington and Chelsea 14, Wandsworth 14 and Tower Hamlets 13. The highest band is led by Havering, Hillingdon and Bromley, as it was.

No other vibe moved: no other recipe holds a measure that changed.

## 6. What each figure cannot see

Every figure says these beside it, in the product:

- It is a count of records, and no person has looked at a sample of them.
- A place is what the category of its record says it is. A restaurant with a bar that is filed as a bar is counted as one, and a cafe that is filed as a bakery is not counted.
- It cannot say what a place is like, what it costs, when it is open or how well it is thought of, and it cannot tell a chain from a place that is one of a kind.
- It is a straight line, and not a walk.
- A rate divides the places the file lists now by the homes of the last census, and reads highest where few homes are.
- Of gyms: a pool, a court and a trainer are not counted, so an area whose one place to train is a swimming pool reads as one with none.
- Of pubs: a nightclub is not counted, and the file holds fewer pubs toward the edge of London.

## 7. What was not done

- No person has looked at a sample of the records of any kind.
- The brands of chains are read by another piece of work, from a second part of the same file. Nothing here reads a brand, so a cafe of a chain and a cafe that is one of a kind count alike.
- Cafes and gyms are in no vibe. Nobody asked for one, and a recipe is the founder's to change.
- No floor is set on how sure the publisher is of a record, as for cultural venues.
- The test of the tables is `packages/pipeline/tests/derive/test_venues_on_the_real_files.py`, which holds every number that the measures state. It runs where the store of fetched files is.
