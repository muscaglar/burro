# Primary schools close by

Built on 2026-09-24, from the register of schools as a person saved it that day. A dated snapshot, not a source of truth. Every count was made by a program, and no person has checked one.

This page holds counts, names of columns and figures of London and of its boroughs. It holds no row of the register, no name of a school or of a person, no postcode and no figure of a named neighbourhood.

## 0. In short

| Question | Answer |
|---|---|
| What is measured | How many state primary schools stand within 800 metres of where homes are, in a straight line |
| From what | Get Information About Schools, of the Department for Education: `dfe-gias` in the licence registry, approved for scoring |
| Which file | `f-e2cf7e0c0508`, the establishment download of 2026-09-24. Its receipt says a person saved it |
| What is read of it | Seven columns of 135. Section 1 |
| Which schools count | Open, of one of seven types the state funds, and of a primary phase: 1,795 in London and 16,840 in England. Section 2 |
| How many areas have a figure | All 1,002. None is missing and none is part covered |
| The lowest, the middle and the highest | 0.3, 3.25 and 9.9 schools |
| Does it follow how built up an area is | Yes, in part. Its rank correlation with homes per hectare is 0.69, and with distance from the centre -0.63. Section 5 |
| Does a build carry it | No. It is worked out at every build and left out: core names the measure a walk, and this is a straight line. Section 9 |
| What it cannot see | How good a school is, whether it has a place, and where it takes its pupils from. A school close by is not a place at it. Section 7 |

## 1. The file, and what is read of it

| | |
|---|---|
| Registry entry | `dfe-gias` |
| File | `extract.zip`, which holds one file, `edubasealldata20260924.csv` |
| Edition and period | 2026-09-24, from the name of the file inside the zip. The publisher says the register changes daily |
| How it was taken | Saved by a person from the publisher's form, and handed over with the step `by-hand` |
| How it is written | Windows-1252, with a quote round every name of its first line. It is not UTF-8 |
| Rows and columns | 52,582 rows, each with a number of its own, and 135 columns |

One module opens the file: `packages/pipeline/src/burro_pipeline/derive/schools_file.py`. It hands over a column only if the column is on its list, and the list holds seven:

| Column | What it is | Why it is read |
|---|---|---|
| `URN` | The number the register gives a school | To see that no school is there twice |
| `EstablishmentStatus (name)` | Whether it is open | A closed school is not counted |
| `TypeOfEstablishment (name)` | What type of school it is | To keep the types the state funds |
| `PhaseOfEducation (name)` | Which years it teaches | To keep the primary years |
| `GOR (name)` | The region the register gives it to | To count the schools of London apart, and those past its edge |
| `Easting`, `Northing` | Its point on the National Grid | To measure from |

A line of a CSV cannot be cut before it is parsed. So a line is parsed whole, the seven columns are taken from it by their place, and nothing else of the line is kept or handed over.

Never read, by the names the file gives them:

| What it is | Columns |
|---|---|
| The name of a person | `HeadTitle (name)`, `HeadFirstName`, `HeadLastName`, `HeadPreferredJobTitle`, `PropsName` |
| A telephone number | `TelephoneNum` |
| A count of pupils | `NumberOfPupils`, `NumberOfBoys`, `NumberOfGirls`, `PercentageFSM`, `FSM`, `SENStat`, `SENNoStat`, `ResourcedProvisionOnRoll`, `SenUnitOnRoll` |
| The religious character of a school | `ReligiousCharacter (code)`, `ReligiousCharacter (name)`, `ReligiousEthos (name)`, `Diocese (code)`, `Diocese (name)` |

The name of a school, its street, its postcode and its website are on neither list. None is read: a request for a column that is not among the seven is refused before the file is opened.

The founder decided on 2026-09-24 that the religious character of a school does not count as an amenity. A school is counted without regard to faith, and the registry entry now says that the column is never read.

## 2. Which schools count

The register has no column that says who pays for a school. It names the status, the type and the phase of each. A school counts where all three of these hold:

| Column | Counts |
|---|---|
| Status | `Open`, and `Open, but proposed to close` |
| Type | `Academy converter`, `Academy sponsor led`, `Community school`, `Foundation school`, `Free schools`, `Voluntary aided school`, `Voluntary controlled school` |
| Phase | `Primary`, `Middle deemed primary`, `All-through` |

The seven types are the schools an authority maintains, academies and free schools. That reading rests on the names of the types alone. No page of the publisher was opened for it, because its policy forbids reading its pages with a program. A person should hold the seven to the publisher's own glossary.

A row is asked its status, then its type, then its phase, and is dropped by the first that does not count.

| Step | England | London, by the region the register gives |
|---|---|---|
| Rows | 52,582 | 5,901 |
| Dropped by status | 25,378: 25,346 `Closed`, 32 `Proposed to open` | 2,712, all `Closed` |
| Open | 27,204 | 3,189 |
| Dropped by type | 7,168 | 943 |
| Dropped by phase | 3,196: 3,109 `Secondary`, 86 `Middle deemed secondary`, 1 `16 plus` | 451: 450 `Secondary`, 1 `16 plus` |
| Count | 16,840 | 1,795 |

What the type dropped in London, of the schools that are open:

| Type | Dropped |
|---|---|
| `Other independent school` | 420 |
| `Other independent special school` | 89 |
| `Community special school` | 78 |
| `Local authority nursery school` | 74 |
| `Academy special converter` | 40 |
| `Higher education institutions` | 36 |
| `Pupil referral unit` | 34 |
| `Free schools special` | 31 |
| `Further education` | 30 |
| `Special post 16 institution` | 23 |
| `Miscellaneous` | 21 |
| `Free schools 16 to 19` | 12 |
| `Free schools alternative provision` | 10 |
| `Foundation special school` | 8 |
| `Academy alternative provision converter` | 7 |
| `Academy special sponsor led` | 6 |
| `Sixth form centres` | 5 |
| `University technical college` | 5 |
| `Studio schools` | 4 |
| `Academy 16-19 converter` | 3 |
| `Non-maintained special school` | 3 |
| `Academy alternative provision sponsor led` | 2 |
| `Academy 16 to 19 sponsor led` | 1 |
| `City technology college` | 1 |

The schools of London that count, by type:

| Type | Count |
|---|---|
| `Community school` | 771 |
| `Academy converter` | 432 |
| `Voluntary aided school` | 342 |
| `Academy sponsor led` | 136 |
| `Free schools` | 79 |
| `Foundation school` | 30 |
| `Voluntary controlled school` | 5 |

Of the 1,795, 1,753 are of the phase `Primary` and 42 are `All-through`.

The file holds 39 types, 8 phases and 4 statuses. The build stops on a value that is none of them, so that a school under a new name is never counted as none.

## 3. Where a school stands

The register gives each school one point on the National Grid, in whole metres. It does not say what the point is of: the gate, the building or the postcode.

| | England | London |
|---|---|---|
| Open schools with no point | 721 | 11 |
| Schools that count with no point | 3 | 0 |

So every school of London that counts is placed. A school with no point is placed nowhere and counted nowhere. The build stops where more than 1 in 100 of the schools that count have no point.

Whether one of the three schools with no point stands within reach of a home in London is not known: a school is placed by its point and by nothing else.

Some schools share a point. In London 49 points hold 99 schools that count. An infant school and a junior school on one site are two rows of the register, and each is counted.

## 4. How a figure is made

1. A home is placed at the point the statistics office gives as the centre of population of its output area.
2. For each output area, the schools that count within 800 metres of that point are counted. The distance is a straight line. It is the distance core takes for a walk of ten minutes, and the one at which the nearest park is never a trade-off.
3. An area's figure is those counts added up over the area's homes and divided by the homes, to one decimal place. Homes are counted as at the census of 2021.
4. An output area with no centre adds nothing, and the coverage of its area falls by its homes. Below half the homes covered no figure is given.

Nought is a figure: the register is of England, so a home with no school within reach has none. The build stops where more than 1 in 100 centres have no school within 10,000 metres, because nought would then be a gap read as a figure.

The method is `points_within_800m_by_homes@1`. Each row of evidence rests on four files: the register, the centres of the output areas, the lookup of output areas and the table of homes. Its period runs from the day of the census to the day of the register.

## 5. What it found

| | Schools within 800 metres | Metres to the nearest school |
|---|---|---|
| Areas with a figure | 1,002 of 1,002 | 1,002 of 1,002 |
| Lowest | 0.3 | 130 |
| Middle | 3.25 | 340 |
| Highest | 9.9 | 1,000 |
| A tenth of areas are below | 1.6 | 220 |
| A tenth of areas are above | 5.9 | 510 |
| Different figures | 89 | 70 |
| Rank correlation with homes per hectare | 0.69 | -0.55 |
| Rank correlation with distance from the centre | -0.63 | 0.52 |

The two middle areas read 3.2 and 3.3. No area reads nought. 768 of 26,369 output areas have no school within 800 metres.

Homes per hectare is the measure `homes_density` of the same build. The centre is the mean point of London's homes: the mean of the centres of its output areas, each weighed by its homes. An area's distance from it is measured from the mean point of the area's own homes. The rank correlation between homes per hectare and that distance is -0.77.

The middle figure of each borough, in the order of the figure. The City of London is one area, and is left out.

| Borough | Areas | Schools within 800 metres, the middle area | Metres to the nearest, the middle area |
|---|---|---|---|
| Tower Hamlets | 34 | 6.95 | 220 |
| Hackney | 30 | 5.6 | 250 |
| Islington | 23 | 5.2 | 260 |
| Southwark | 34 | 5.2 | 240 |
| Newham | 40 | 5.1 | 245 |
| Hammersmith and Fulham | 25 | 5 | 260 |
| Haringey | 36 | 4.4 | 305 |
| Lambeth | 35 | 4.4 | 270 |
| Westminster | 24 | 4.05 | 275 |
| Lewisham | 37 | 3.8 | 290 |
| Kensington and Chelsea | 21 | 3.7 | 270 |
| Wandsworth | 38 | 3.7 | 295 |
| Barking and Dagenham | 22 | 3.6 | 330 |
| Camden | 27 | 3.6 | 290 |
| Waltham Forest | 28 | 3.6 | 325 |
| Greenwich | 35 | 3.3 | 320 |
| Brent | 35 | 3.2 | 370 |
| Croydon | 45 | 2.9 | 410 |
| Merton | 25 | 2.9 | 340 |
| Enfield | 36 | 2.85 | 355 |
| Barnet | 42 | 2.75 | 390 |
| Ealing | 41 | 2.7 | 350 |
| Redbridge | 33 | 2.7 | 370 |
| Richmond upon Thames | 23 | 2.7 | 370 |
| Bexley | 28 | 2.45 | 385 |
| Hounslow | 29 | 2.4 | 390 |
| Kingston upon Thames | 20 | 2.4 | 415 |
| Sutton | 24 | 2.3 | 385 |
| Havering | 30 | 2.05 | 435 |
| Hillingdon | 32 | 2 | 400 |
| Harrow | 30 | 1.95 | 425 |
| Bromley | 39 | 1.9 | 440 |

The order is close to the order of homes per hectare. The measure says where schools stand thick on the ground, which is where homes do.

## 6. The count or the distance

Both were worked out, the same way, from the same points. The distance is the median over an area's homes of the straight line to the nearest school, to the nearest 10 metres: the arithmetic of the nearest park.

| | The count | The distance |
|---|---|---|
| What it says | How many schools there are to choose between | Whether there is one at all |
| How far areas differ | The area a tenth of the way up reads 1.6 and the one nine tenths up 5.9 | 220 metres and 510 |
| What an area in the middle differs from its neighbour by | A school or two | Tens of metres. A home may stand a hundred metres from the centre of its output area |
| Areas where the nearest school is past 800 metres | | 6 of 1,002 |
| How far it follows homes per hectare | 0.69 | -0.55 |

The count tells areas apart, and the distance does so poorly. In all but six areas the nearest school is within 800 metres, and half of all areas lie between 260 and 420 metres. A difference of that size is within what is lost by placing every home at the centre of its output area.

The count pays for it by following homes per hectare more closely. The rank correlation between the count and the distance is -0.78.

## 7. What it cannot see

| What | Why |
|---|---|
| How good a school is | The register holds no inspection and no result |
| Whether a school has a place | The counts of pupils are never read, and a count is no offer of a place |
| Where a school takes its pupils from | The register holds no catchment. A school close by is not a place at it |
| Whom a school admits | The columns for the sex it admits, for how it selects and for its religious character are not read |
| The walk | The distance is a straight line. A railway, a river or a main road in between makes the walk longer |
| A school on two sites | The register gives one point for a school |
| An infant and a junior school as one | They are two rows, and are counted as two |
| A school that opened or closed after 2026-09-24 | The file is of one day |
| Homes built since 2021 | An output area weighs what it did at the census |

What counting a pair as two does. With every point counted once, however many schools it holds, 183 of the 1,002 areas read lower, the most by 1.8 schools. The order of the areas barely moves: the rank correlation between the two counts is 0.99. Whether a pair is one school or two is the founder's to say.

## 8. The edge of London

The register is of England, so a school just past the edge of London is in it, and the measure sees it. A school counts for a home in London wherever it stands within 800 metres of it.

| | Schools |
|---|---|
| Within 800 metres of a centre of London | 1,811 |
| Of those, given by the register to a region other than London | 16 |
| Of those, given to London | 1,795, which is every school of London that counts |

## 9. What a build does with it, and what core needs

A build works the figure out and leaves it out, under the rule `measure_is_as_core_says`. The row of the catalogue it makes differs from core's in one field:

| Field | Core says | The measure says |
|---|---|---|
| `label` | State primary schools within a short walk | State primary schools within 800 m in a straight line |

Core's unit is `count` and its polarity is more, and the measure says the same. Core also gives the feature's resolution as a network, where the measure is made from points. A release is not held to that field, and the row of the measure says `point`.

So core needs one change to carry the measure: the label of `school_primary_nearby` as the measure writes it, and `point` for its resolution, as core gives the nearest park. The list of features is core's to change.

**What follows on that day.** Family amenities gives primary schools 40 in 100 of its recipe, and the nearest park 25, which a build carries. Together they are 65 in 100, and an area is placed at 60. So every area would be placed on Family amenities on two of its three parts, before the nearest play space is carried. A test on made-up files holds a build to that. A vibe that gains a band is a person's to look at before it is served.

## 10. The inspectorate's file

The registry holds `ofsted-state-funded-schools-mi`, approved for scoring and display, and its file of latest inspections as at 31 August 2026 has a receipt. Nothing here reads it, and nothing is built on it.

| Question | Answer |
|---|---|
| What it would add | The published outcome of each school's latest inspection, and its date. It answers a part of "how good is a school", which the register cannot |
| How it would join | By the number of the school, `URN`, which the registry entry of the register gives as the key to join on |
| What its registry entry forbids | A composite grade. The file mixes three ways of inspecting, which its publisher says cannot be compared. An outcome is shown as published, with its date |
| What that rules out | A count of "good schools" close by. To count them, a build must say which outcome of each of the three ways is good. That is a composite grade by another name |
| What the design says | The design of the vibes keeps the results of schools beside Family amenities and out of its recipe. It does not speak of inspections |
| What is not settled in its entry | Its attribution is not verified. Nobody has read the footer of the page the file is on |
| What is not known of the file | Its columns. The list of files says, from memory, that it holds a column on the deprivation of a school's pupils, which would never be read |

The founder should be asked before anything is built on it: whether an inspection outcome is shown beside a school and never ranked on, or ranked on when a person asks for it. Until then it stays unread.

## 11. For the founder

| # | Question |
|---|---|
| 1 | Does core name the measure a straight line, as it names the nearest park, so that a build carries it |
| 2 | Is Family amenities served on two of its three parts, or held until the nearest play space is carried |
| 3 | Is an infant school and a junior school on one site one school or two |
| 4 | Are the seven types the right ones. A person should hold them to the publisher's glossary |
| 5 | Is 800 metres the reach. It is the distance of a ten minute walk, and a straight line of 800 metres is a longer walk |
| 6 | Does a measure that follows homes per hectare at 0.69 say enough of its own to be ranked on |
| 7 | May anything be built on the inspectorate's file, and is an outcome shown or ranked on |
| 8 | Do `PropsName` and `TelephoneNum` join the columns the registry entry names. Both are already refused by the reader |
