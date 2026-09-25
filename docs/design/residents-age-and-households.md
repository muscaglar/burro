# The age and household make-up of residents

Written 2026-09-24. For whoever changes core next. Not reviewed by a lawyer.

This is the first time anything about who lives somewhere may feed a vibe. It is built narrowly. This page says what was built, what was proposed and not built, and what core, the reader and the website must change, file by file, before a release carries a figure.

**It was built later the same day.** Section 13 says what was built and what was chosen where this page left a choice, and section 12 holds the row of the proxy audit, which was written first. Sections 5 to 11 are kept as they were written, before anything was built, so that what was proposed can be held against what was done.

**The proxy audit was dropped on 2026-09-25.** The founder decided it ([decision record 0006](../adr/0006-rank-places-not-residents.md), as amended that day). It answers question 13 of section 11: no vibe and no measure waits on an audit. Where sections 5 to 11 say that the audit comes first, they say what was proposed. Every rule of section 5 for a part that counts residents stands as it was, and so does every test of section 9.

## 1. What was decided, and its limits

The founder decided on 24 September 2026. The record is [ADR 0006](../adr/0006-rank-places-not-residents.md), as amended that day.

| | Decided |
|---|---|
| Age and household make-up of residents | May feed vibes and ranking, from the census |
| Ethnicity and religion | Shown on the area page, and never ranked on |
| Ranking towards a community a person names | Kept open. Not built |
| Including or excluding areas by who lives there | Not built, and not to be made possible by accident |
| Stop and search data | Never read |
| Gender | Left out |
| Income, employment, health, qualifications, country of birth, language, disability, sexual orientation | Not asked about. Still kept out of ranking |

Two rules follow, and everything below is held to them.

1. **A figure about who lives somewhere says so**: in its name, and beside it on the page, with the year it was counted.
2. **Burro helps a person find, and never helps a person avoid people.** No words and no control ask for fewer of any group.

## 2. What is built

| What | Where | State |
|---|---|---|
| The rule that lets a source of age and household composition feed a score. It asks about every table the source names: under `tables`, in its id, in its name and in every address | `packages/pipeline/src/burro_pipeline/registry/rules.py`, `model.py` | Built and tested |
| The fence that lets a file of such a source into the product | `packages/pipeline/src/burro_pipeline/evidence/fence.py` | Built and tested |
| The gate of fetch, which refuses a file under that source that names any other table: in the list, in its address, or inside a zip | `packages/pipeline/src/burro_pipeline/fetch/gate.py` | Built and tested |
| The registry entry `ons-census-2021-age-and-household-tables` | `registry/sources/residents.toml` | Approved for `scoring` and `census_table` |
| The list of the two files | `packages/pipeline/src/burro_pipeline/fetch/lists/m11-age-and-households.toml` | Written. Both files were fetched on 2026-09-24, and each has a receipt |
| Four measures | `packages/pipeline/src/burro_pipeline/derive/` | Built, tested on made-up tables, and worked out on the two tables as fetched. Each has a figure for each of London's 1,002 areas. Core holds each since catalogue version 13, and each is on the table of measures, so a build that names the list carries it |
| The decision record | `docs/adr/0006-rank-places-not-residents.md` | Amended |
| A change to core, to a recipe, to the reader, to the website | `packages/core`, `services/api`, `apps/web`, `apps/ios` | Made. Section 13 says what each is |

No release that is served holds anything about residents. The committed release, which is made up, carries the four measures and the two vibes, with figures that were made up for it.

## 3. The registry

| Entry | Was | Now |
|---|---|---|
| `ons-census-2021-age-and-household-tables` | Not there. TS003 and TS007A stood in the entry below | New. Approved for `scoring` and `census_table`. Tables TS003 and TS007A |
| `ons-census-2021-resident-tables` | Gated. `census_table`. Five tables | Gated, as it was. `census_table`. Three tables: TS004, TS021, TS030 |
| `ons-census-2021-protected-characteristics` | Gated. No use | The same. One condition names the new entry |

- **The entry of ethnic group, religion and country of birth is still gated.** Its own reason names two checks that have not passed: a person has not opened its licence pages, and the fences round the census table on an area's page are not built. Neither was settled here, so its status was not changed. The gate refuses it for every use, scoring among them. When both checks pass, it is approved for `census_table` alone, and the rule already refuses it any other use.
- **No table of language, disability, sexual orientation or gender identity is shown.** They stand in the audit entry, as they did. [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) names the tables an area's page may show, and the founder did not add to them. See section 11.
- **`display` is not listed.** In this registry `display` is what a file of a release asks for a station. A figure in a release is asked about as `scoring`, and the census table on an area's page as `census_table`. The new entry lists those two.

### The evidence

Every page was opened on 2026-09-24, through a reader that extracts the text of a page. Each was asked twice, in different words. What is recorded is what both gave.

| Page | What it says |
|---|---|
| `https://www.nomisweb.co.uk/home/copyright.asp` | ONS material may be re-used under the terms of the Open Government Licence, "whether commercially or privately". Asks for: "Source: Office for National Statistics". States no version |
| `https://www.ons.gov.uk/datasets/TS003/editions/2021/versions/4` | "All content is available under the Open Government Licence v3.0, except where otherwise stated". Version 4, of 16 November 2023. Its figures can be filtered by statistical area, and it gives MSOA and LSOA as examples |
| `https://www.ons.gov.uk/census/aboutcensus/censusproducts/topicsummaries` | The same licence line. Topic summaries are published down to output areas |
| `https://www.nomisweb.co.uk/datasets/c2021ts007a` | TS007A counts usual residents, in a total and 18 bands of five years. Census Day was 21 March 2021 |
| `https://www.nomisweb.co.uk/datasets/c2021ts003` | TS003 counts households, in a total and 21 categories |
| `https://www.nomisweb.co.uk/sources/census_2021_bulk` | The address of each zip. No size |
| The quality page, below | What the lockdown did |

No page for TS007A was found on the statistics office's own website. A person has still to open each page in a browser: the entry says so under `before_launch`.

### What the publisher says of the lockdown

Two pages of the statistics office say it. Each was read on 2026-09-24, more than once and in different words. A sentence is quoted here where two readings gave the same words.

The first is "Quality and methodology information (QMI) for Census 2021", last revised on 23 November 2023:
`https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/qualityandmethodologyinformationqmiforcensus2021`

Under "Conducting a census during the coronavirus pandemic" it says:

- "The coronavirus pandemic may have affected some people's choice of usual residence on Census Day, for example, students and in some urban areas."
- "These changes might have been temporary for some". The readings do not agree on how the sentence ends: "more long-lasting for others", or "permanent for others". A person should read it in a browser.
- Of students: "The census counts students at their term-time address." It gives as evidence of change "a marked increase in the number of students who were not at term-time accommodation" in the academic year 2020 to 2021, and that "some halls were below full occupancy".
- Of urban areas: it reports an analysis by the Greater London Authority, which found "a fall in London's population over the first year of the coronavirus pandemic", "many young adults leaving London during lockdown", and "many young adults returning to London during the spring and summer of 2021".

The second is the first release of the census, "Population and household estimates, England and Wales: Census 2021", of 28 June 2022:
`https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/bulletins/populationandhouseholdestimatesenglandandwales/census2021`

- Among its limitations it holds the first sentence above, with "(COVID-19)" after "coronavirus".
- "Population change in certain areas may reflect how the coronavirus (COVID-19) pandemic affected people's choice of usual residence on Census Day."

Census Day was 21 March 2021. So the share of young adults is the figure the lockdown bears on most. Section 4 says what was looked for in the figures, and what one census cannot show.

## 4. The measures

Each is a share, in percent, to one decimal place. Each is read from the publisher's own row for the MSOA, one count over another. `derive/census_msoa.py` holds the reading.

| Id | What it counts | Of whom | From |
|---|---|---|---|
| `residents_aged_20_34` | Usual residents aged 20 to 34 | All usual residents | TS007A, three bands |
| `residents_aged_65_over` | Usual residents aged 65 and over | All usual residents | TS007A, five bands |
| `households_dependent_children` | Households with dependent children | All households | TS003, four categories added up |
| `households_one_person` | Households of one person | All households | TS003, one category |

| Id | The name a person reads | What it cannot see, in two sentences |
|---|---|---|
| `residents_aged_20_34` | Residents aged 20 to 34 as a share of all residents, Census 2021 | It counts who was living in the area on 21 March 2021, during a lockdown that the statistics office says may have changed where students and people in some urban areas were living, so the share may read lower than it would in another year. It cannot see who has moved in or out since, and it cannot tell a student from someone in work |
| `residents_aged_65_over` | Residents aged 65 and over as a share of all residents, Census 2021 | It counts who was living in the area on 21 March 2021, during a lockdown, so it cannot see who has moved in or out since, or who lives in a home built since. It is a share of everyone counted, so it cannot tell an area with many older residents from one with few younger ones |
| `households_dependent_children` | Households with dependent children as a share of all households, Census 2021 | It counts households as they were on 21 March 2021, during a lockdown, so it cannot see who has moved in or out since, or who lives in a home built since. It is a share of households, so it cannot see how many children there are, how old they are, or whether they go to school nearby |
| `households_one_person` | Households of one person as a share of all households, Census 2021 | It counts households as they were on 21 March 2021, during a lockdown, so it cannot see who has moved in or out since, or who lives in a home built since. It cannot tell a young person who lives alone from an old one, and it says nothing of how many people live in the other households |

### What was read, and what was not

- **The step was written on made-up tables, and then run on the two tables as fetched.** It read both as they stand. One helper of a test split a header at its commas and was mended. Nothing in the step was changed.
- **The table by MSOA is read, and no other file of a zip.** Each zip holds a table for each of seven geographies. The zip of households also holds a note under `metadata`, which was not opened: the version of that table is still not known. The zip of age holds no note.
- **The two tables name their columns differently.** The table of age writes the variable, a colon and the category. The table of households adds `; measures: Value`, writes "One person" with no hyphen and its total as "Total", and puts every name between quotes. The step finds a column by the name of its category, either way, and stops where a category has no column or two.
- **No count is withheld.** Every cell that is read holds a whole number, in every row of both tables. In every row the categories come to the total to the unit.
- **TS003 names how a couple is joined, and names lone parents.** The four categories with dependent children are read only to be added up. No figure is made from one of them: the step refuses a measure that counts some of the four and not all, and a test holds that moving households between the four moves nothing. What the step keeps of a row holds the four as their one sum, so a measure that is allowed hands back no count of one of them.
- **No measure is made from single family households or from other household types.** Both are read only to hold the table to its total, and neither is kept once a row is held to it. Other household types take in the households of students, which were not decided on. The step refuses a measure that counts either.
- **The split of one-person households by age is not read.** It is a finer cut than was asked about. See section 11.

### What the tables hold

Worked out on 2026-09-24, from the tables of Census 2021. No person has checked a figure. `tests/derive/test_census_msoa_on_the_real_files.py` holds the counts.

| | Age, TS007A | Households, TS003 |
|---|---|---|
| Rows of the table by MSOA | 7,264 | 7,264 |
| Of London | 1,002 | 1,002 |
| What London's areas add up to | 8,799,692 usual residents | 3,423,921 households |
| Areas with no figure | None | None |

| Measure, in percent | Lowest area | Middle | Highest area | London as a whole | Lowest boroughs | Highest boroughs |
|---|---|---|---|---|---|---|
| `residents_aged_20_34` | 9.9 | 22.6 | 58.9 | 24.8 | Richmond upon Thames 15.5, Bromley 16.8, Sutton 17.7 | Tower Hamlets 37.8, Islington 34.4, Lambeth 34.2 |
| `residents_aged_65_over` | 1.1 | 11.2 | 27.8 | 11.9 | Tower Hamlets 5.6, Newham 7.2, Hackney 7.9 | Havering 17.6, Bromley 17.6, Bexley 16.6 |
| `households_dependent_children` | 7.8 | 32.5 | 52.2 | 31.3 | Westminster 19.1, Kensington and Chelsea 20.4, Islington 22.0 | Barking and Dagenham 45.4, Redbridge 40.6, Newham 38.4 |
| `households_one_person` | 13.4 | 28.35 | 56.5 | 29.3 | Harrow 22.1, Redbridge 23.0, Newham 23.4 | Kensington and Chelsea 43.7, Westminster 42.7, Camden 38.7 |

A borough's figure is the counts of its areas added up, one sum over another. The City of London is one area and is left out of the last two columns.

### Do they tell areas apart?

The rank correlation of each measure, over the 1,002 areas. Distance is a straight line from where the homes of the City of London stand, from the statistics office's own file of centres of population. Another centre, where all of London's homes stand, moves no figure by more than 0.08.

| Measure | Homes per hectare | Distance from the centre | Flats | Aged 20 to 34 | Aged 65 and over | With children | Of one person |
|---|---|---|---|---|---|---|---|
| `residents_aged_20_34` | 0.78 | -0.73 | 0.80 | | -0.76 | -0.54 | 0.54 |
| `residents_aged_65_over` | -0.63 | 0.56 | -0.59 | -0.76 | | 0.07 | -0.23 |
| `households_dependent_children` | -0.51 | 0.57 | -0.63 | -0.54 | 0.07 | | -0.79 |
| `households_one_person` | 0.57 | -0.59 | 0.79 | 0.54 | -0.23 | -0.79 | |

- **Residents aged 20 to 34 say little that homes do not.** The measure stands at 0.80 with flats and 0.78 with homes per hectare. Flats, homes per hectare and distance together account for 72 in 100 of its order.
- **Households of one person say little that flats do not**: 0.79, and 63 in 100 of its order with the three together.
- **Households with dependent children and residents aged 65 and over say more of their own.** The three account for 42 and 43 in 100 of each.
- **The four are two pairs.** Fewer young adults is 0.76 the order of more older residents. Fewer households with children is 0.79 the order of more households of one person.

### The lockdown, looked for in the figures

Each area was set against the middle figure of the areas that share a side with it, for residents aged 20 to 34.

| | Areas |
|---|---|
| 5 points or more below the areas beside it | 70 |
| 10 points or more below | 8 |
| 5 points or more above | 104 |
| 10 points or more above | 19 |

- **The dips are where the peaks are.** Wandsworth holds 9 dips and 14 peaks. Tower Hamlets holds 7 dips, Hammersmith and Fulham 6, and Southwark, Lambeth, Kensington and Chelsea and Haringey 5 each. These are boroughs where the share is high and varies most. 37 of the 70 dips still stand above London's middle.
- **30 of the 70 dips go with fewer flats** than the areas beside them, by 10 points or more. 40 do not.
- **No dip can be laid at the door of the lockdown.** One census is one day, and no second year is held to set it against. No file that is held says where a university is or who rents, and tenure was not decided on, so neither was read.
- **What the publisher describes would not show as a dip.** Young adults leaving London as a whole lowers the share across many areas that lie side by side. An area is then no lower than the areas beside it. Only a second year could show it.

## 5. Where the measures enter the vibes

This section is as it was written, when nothing of it was built and no recipe had been changed. Section 13 says what was built of it.

### Three rules for a part that counts residents

| Rule | Why |
|---|---|
| It is read high, and never low | To read it low is to rank towards fewer of a group |
| It stands in a one-way vibe, and never in a scale | The other end of a scale ranks away from what the first end ranks towards |
| It counts towards no likeness between two areas | Two areas are never said to be alike for who lives in them |

### What breaking each rule would do, on the real tables

Worked out on 2026-09-24 and built nowhere. A count beside a borough is how many of its areas are meant.

| Rule broken | What it does |
|---|---|
| Residents aged 65 and over, read low | The first fifth of London holds 29 of Tower Hamlets' 34 areas, 33 of Newham's 40 and 19 of Hackney's 30. It holds no area of Havering, Harrow, Richmond upon Thames, Sutton or Kingston upon Thames |
| Households with dependent children, read low | The first fifth holds 20 of Westminster's 24 areas and 17 of Kensington and Chelsea's 21. It holds no area of Barking and Dagenham, Redbridge, Enfield or Harrow |
| Residents aged 20 to 34, read low | The first fifth holds 21 of Richmond upon Thames' 23 areas and 27 of Bromley's 39. The middle share aged 65 and over among them is 17.9, where London's is 11.2 |
| Young and busy, as a scale | Its other end is 0.75 the order of more residents aged 65 and over. It holds 27 of Bromley's 39 areas and 20 of Havering's 30, and no area of Camden, Hackney, Islington, Lambeth, Newham, Tower Hamlets, Wandsworth, Westminster or three more |
| Residents aged 20 to 34, put in the scale Homes at 35 in 100 of it | 220 areas change band. 28 areas come to the houses end and 28 leave it. Those that come have more flats than those that leave, 33.7 in 100 against 28.0, and more residents aged 65 and over, 17.4 against 12.2. A person who asks for houses is sent to older residents, and not to houses |
| The four, counted in likeness | An area and the five areas most like it stand 7.4 points apart on residents aged 20 to 34 today, where any two areas of London stand 8.5 apart. With the four counted they stand 2.9 apart. So likeness today says next to nothing of who lives somewhere, and with the four it would say it first |

Likeness was counted on the four parts core allows that a build holds today. With so few parts many areas are level, so the last row is the most that the four could do: core holds 25 parts that may be compared, and the four would be 4 of 29.

A low reading also adds nothing a person needs. Fewer young adults is 0.76 the order of more older residents, and fewer households with children is 0.79 the order of more households of one person. A person who wants to find can ask for more of the other.

### The audit comes first

A figure about age or households can stand in for something that was not decided on. Where the old live, where children live and where the young live are not spread evenly across a city, and nor is ethnic group, religion, country of birth or income. So a vibe that counts residents could rank areas by one of those under another name, without anyone meaning it to.

[ADR 0006](../adr/0006-rank-places-not-residents.md) holds the answer: the proxy audit, which stands. The audit is not built, and no feature has been through it. What is proposed is that these go through it first:

1. The rule of the audit is written down for each of the four measures and for each new vibe: the aim it serves, the correlation that starts a review, and what is then done (drop it, cap its weight, or leave it out of every vibe).
2. The audit is run on each, against ethnic group, religion, country of birth and the deprivation of income. It is run offline, under the audit's own entry and in the audit's own store.
3. The founder sees what it found before a vibe that counts residents is in a release.

Whether a vibe waits for the audit is the founder's to say: question 13 of section 11. The audit has not been run. What the real tables show of the two vibes, without it, is below.

### The vibes there are

| Vibe | Proposed | Why |
|---|---|---|
| Family amenities | **Gains nothing.** It stays a vibe of places | A person can then ask for schools and play space without ranking on who lives there. A vibe that counts residents must say so in its name, and this one's name says amenities. Its line on what it cannot see, "Who lives there", stays true |
| Pace | **Gains nothing, and must not** | It is a scale, from Calm to Buzzy. With young adults at its high end, to ask for Calm would rank towards fewer young adults |
| Gritty, in either form | Gains nothing | The founder decided that nothing about who lives there is in it |
| Every other vibe | Gains nothing | None is about who lives somewhere |

If the founder wants one family vibe and not two, the recipe to start from is 30 primary schools nearby, 25 play space, 20 a park within a walk, 25 households with dependent children. It is then renamed, and "Who lives there" leaves what it cannot see.

### New vibes

Each is one-way. Every part is under 60 in 100, and the parts come to 100, as core asks of a recipe. A vibe has a band where 60 in 100 of its recipe is measured, so each is weighed to have one as soon as its census table is in.

**Family area**

| Part | In 100 | Read | In a build today |
|---|---|---|---|
| `households_dependent_children` | 45 | High | Worked out. In no build until core holds it |
| `school_primary_nearby` | 20 | High | No |
| `park_proximity` | 20 | Nearer | Yes |
| `play_space_proximity` | 15 | Nearer | No |

Why: it is the founder's own example, and what "families" most often means when it is typed. Households with children are the thing itself. Schools, parks and play space are what such households look for. It has a band at 65 in 100.

**Young and busy**

| Part | In 100 | Read | In a build today |
|---|---|---|---|
| `residents_aged_20_34` | 40 | High | Worked out. In no build until core holds it |
| `venue_evening` | 20 | High | No |
| `venue_food_drink` | 15 | High | No |
| `homes_flats` | 15 | High | Yes |
| `homes_density` | 10 | High | Yes |

Why: "young professionals" is among the first things people type. It has a band at 65 in 100. **It may say little that Homes and Pace do not.** Young adults, flats and places to go out are found in the same parts of a city. Work out how it stands against each before it ships: the pipeline's own rule is that no two vibes find the same areas.

**Settled**

| Part | In 100 | Read | In a build today |
|---|---|---|---|
| `residents_aged_65_over` | 40 | High | Worked out. In no build until core holds it |
| `homes_flats` | 25 | Low: houses | Yes |
| `land_gardens` | 20 | High | No |
| `road_major_exposure` | 15 | Low: away from main roads | No |

Why: a person who asks for older residents nearby is offered something. **It is the weakest of the three, and it is not to be built as it stands.** Three things are wrong with it.

- Its name says people have stayed, and nothing here counts how long anyone has lived anywhere.
- "Settled" is also said of people, to tell those who have long lived in a country from those who have newly come. A vibe of that name that counts residents could be read as ranking by where people are from.
- Every part of it points the same way: older residents, houses, gardens, and away from main roads. Of the three it is the one most likely to stand in for ethnic group or for income, because nothing in it pulls against the rest. The audit is run on it before anything else is decided.

So the founder is asked whether it is wanted at all, and under what name: section 11.

### What the real tables show of the two vibes

Each was worked out on 2026-09-24 on the parts a build holds today, which is 65 in 100 of its recipe, as core works a vibe out. Neither is built.

**Family area is, today, a map of households with dependent children.** Two parts are held: households with dependent children, and the nearest park. The first is 69 in 100 of what is held.

| Family area, on 65 in 100 | |
|---|---|
| Rank correlation with households with dependent children alone | 0.92 |
| With homes per hectare, with distance from the centre, with flats | -0.45, 0.47, -0.55 |
| With Homes and with Parks close by, each on the parts held | -0.52, 0.34 |
| Areas in the band they would have on households with children alone | 572 of 1,002, and 997 within one band |
| Boroughs with most of their areas in band 5 | Barking and Dagenham 22 of 22, Newham 25 of 40, Redbridge 20 of 33, Hounslow 12 of 29, Enfield 13 of 36, Ealing 14 of 41 |
| Boroughs with most of their areas in band 1 | Kensington and Chelsea 17 of 21, Westminster 19 of 24, Islington 16 of 23, Camden 18 of 27, Hammersmith and Fulham 15 of 25 |
| Boroughs with no area in band 5 | Camden, Islington, Kensington and Chelsea, Lambeth, Westminster, and the City of London |

It is not a map of distance from the centre, though it leans that way: the middle distance from the centre is 15 km in band 5 and 7 km in band 1. It says where children live and little of what a family looks for, while primary schools and play space are not held. Nothing that is held says whether the boroughs at its head differ in anything else about who lives there, and nothing of the kind was read. Whether it stands in for something that was not decided on is what the audit is for.

**Young and busy is, today, the flats end of Homes under another name, and a map of how near the centre a place is.** Three parts are held: residents aged 20 to 34, flats, and homes per hectare.

| Young and busy, on 65 in 100 | |
|---|---|
| Rank correlation with Homes, on the parts held | 0.93 |
| Residents aged 20 to 34 alone, with Homes on the parts held | 0.84 |
| Its two parts of the place alone, flats and homes per hectare, with Homes on the parts held | 1.00 |
| With flats, with homes per hectare, with distance from the centre | 0.89, 0.86, -0.78 |
| With residents aged 20 to 34 alone | 0.98 |
| Areas in band 5 that are in band 5 of Homes | 156 of 200 |
| Areas within one band of their band on Homes | 984 of 1,002 |
| Boroughs with most of their areas in band 5 | Tower Hamlets 32 of 34, Islington 19 of 23, Westminster 17 of 24, Lambeth 22 of 35, Hammersmith and Fulham 14 of 25 |
| Boroughs with most of their areas in band 1 | Richmond upon Thames 16 of 23, Bromley 27 of 39, Havering 20 of 30, Bexley 18 of 28, Sutton 14 of 24 |
| Middle distance from the centre, band 5 and band 1 | 5.2 km and 17.9 km |

The made-up city is held to a rule that no two vibes stand above 0.8 with each other. On real London this one stands at 0.93 with Homes. Part of that is built in: 25 of the 65 in 100 that are held are flats and homes per hectare, which are the two parts of Homes that are held. The rest is residents aged 20 to 34, which alone stand at 0.84 with Homes. So a smaller part for residents would bring the vibe nearer to Homes and not further from it, while the venues are not held. Whether evening venues and places to eat and drink would pull it away is not known: neither is held, and nothing was measured. It is not to be built as its recipe stands.

### Households of one person

In no recipe at first. It cannot tell a young person who lives alone from an old one, so it would pull Young and busy one way and Settled the other. A person may weigh it by itself. On the real tables it stands at 0.79 with flats, so it says little that Homes does not.

## 6. What a person reads

A vibe or a figure that counts who lives somewhere says three things wherever it is shown: what is counted, of whom, and in which year. The words are fixed, and the same for every area.

| Where | The words |
|---|---|
| The card of a vibe, under its name | This vibe counts who lived here. 45 in 100 of it is the share of households with dependent children at the 2021 census |
| The card, last line | The census was taken on 21 March 2021, during a lockdown. It does not show who lives here now |
| Beside a figure | N% of households had dependent children. Counted at the 2021 census, on 21 March 2021. Source: Office for National Statistics |
| Beside a figure of age | N% of residents were aged 20 to 34. Counted at the 2021 census, on 21 March 2021, during a lockdown, when many young adults had left London |
| In a reason | More households here had dependent children than in N in 100 of the areas compared, at the 2021 census |
| A control in the settings | More households with children (2021 census) |
| The group of the settings | Who lives there, at the 2021 census |
| Where there is no figure | Burro holds no census figure for this area |

- A reason never says why people live somewhere, and never says an area is "popular with" anyone.
- No control and no offer asks for fewer. A control has two positions: counted, and left out. A sentence may say that an area has fewer than most, where a person asked for more: that is what the area gives up for them.
- The group of the settings is new. Everything that counts residents stands in it, apart from what counts places.
- No list, table or map is sorted, coloured or filtered by a figure about residents. A person reaches such a figure through a weight or a vibe, and in no other way. The website has no such control today. None is to be added: a list sorted from the lowest is a filter by another name, and the founder decided that no area is included or excluded by who lives there.

## 7. What the reader must do

### The principle

| What is typed | What it gives |
|---|---|
| A phrase that names an age or a make-up of households that a measure counts, and nothing more | An offer of that measure. Nothing is applied until the person chooses |
| A phrase that names that and also work or a partner: young professionals, young couples, retirees, pensioners | The notice, as today, until the founder has answered question 10 of section 11. Work was not asked about, and nor was how a couple is joined. If the answer is yes: an offer of the age part alone, which quotes the word and says what is not counted |
| A phrase for fewer of any group, none of one, or distance from one | The notice. No edit and no offer |
| A phrase about ethnicity, religion, nationality, class, income or how well off people are | The notice. No edit and no offer |
| A phrase for an age or for households with such a word in the same clause: "white families", "young Muslim families", "wealthy retirees" | The notice. No edit and no offer, of the age or the household part either. An offer beside such a word would rest on it |
| A phrase about students, renters or owners | The notice, as today. None was decided on: section 11 |
| The name of an amenity: a place of worship, a food shop | As today. It is a wish about a place |

- **An offer has two choices: more, and leave it out.** It never has less. Today core offers a feature of one direction a second choice, which takes its weight off and is sent with the direction `less`. For a measure about residents that choice is not made: to leave it out is enough.
- **Words never apply a measure about residents.** Even in a plain list, and even where its label is typed, it is offered. A control applies it.
- **A turning word makes it a request about people.** "No", "not", "fewer", "without", "away from" and "far from", in the clause of a phrase for residents, give the notice. It is what core does today for a campus.
- **A word of the policy lexicon in the same clause withholds the offer.** "Families" is offered. "White families" is not: the notice is given, and nothing is offered for "families" either. Today such a phrase gives the notice because nothing is made of "families". Once "families" is a target, the rule must be written, or the reader would answer a wish about ethnicity with an offer.

### The notices

Two fixed texts, the same for every group and every person. There are two because the first says how a community is found, and a person who asks to be kept from a group is not told how to find one.

| Notice | When | The words |
|---|---|---|
| `neutral_places`, reworded | A wish to find a group that Burro does not count: by ethnicity, religion, nationality, class, income, work, or as students | Burro counts two things about who lives in an area: age, and households. It ranks on nothing else about them. To find a community, name what you want nearby, such as a place of worship, a cultural centre or a food shop |
| `find_never_avoid`, new | A wish for fewer of any group | Burro helps you find a place. It never ranks areas by who you would rather not live near |

- The notice does not point to the census table on an area's page. [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) says it "does not point to the table", and the founder has not changed that. Whether it should is question 6 of section 11.
- The last sentence sends a person to measures of places of worship, cultural centres and food shops. Today Burro hears such a wish and has no measure of it. The notice ships with the first of those measures, and not before.
- The two notices are there because a person who asks to be kept from a group is told one thing only: that Burro does not do it.
- A school's faith is no amenity, as the founder decided the same day, so the notice names no school.

### What each offer says

Each offer quotes the word that was typed, and says what is counted. Where the word says more than is counted, it says what is not.

| Note | The words |
|---|---|
| A | Burro counts residents aged 20 to 34 at the 2021 census |
| B, if question 10 is answered yes | Burro counts residents aged 20 to 34 at the 2021 census. It holds nothing on what people do for work |
| C, if question 10 is answered yes | Burro counts residents aged 20 to 34 at the 2021 census. It holds nothing on whether people live as a couple |
| D | Burro counts residents aged 65 and over at the 2021 census |
| E, if question 10 is answered yes | Burro counts residents aged 65 and over at the 2021 census. It holds nothing on whether people work |
| F | Burro counts households with dependent children at the 2021 census |
| G | Burro counts households of one person at the 2021 census. It cannot tell a young person from an old one |

### Thirty sentences

"Today" is what the reader of rules gives on the synthetic release, as it was run on 2026-09-24.

| # | Typed | Today | Should give |
|---|---|---|---|
| 1 | young professionals | Notice | Notice, `neutral_places`, as today, until question 10 is answered. If yes: an offer of more residents aged 20 to 34, note B |
| 2 | somewhere leafy with lots of young professionals like me | Notice. Leafy applied | The same as today, until question 10 is answered. If yes: offers of Leafy and of more residents aged 20 to 34, note B, and nothing applied |
| 3 | young people | Notice | Offer: more residents aged 20 to 34. Note A |
| 4 | young couples | Notice | Notice, `neutral_places`, as today, until question 10 is answered. If yes: an offer of more residents aged 20 to 34, note C |
| 5 | lots of young families | Notice | Offers: more households with children, note F, and Family amenities |
| 6 | families | Nothing is made of it | Offers: more households with children, note F, and Family amenities |
| 7 | other families with kids nearby | Notice | Offer: more households with children. Note F |
| 8 | good for families | Family amenities applied | The same. The words ask what a place has |
| 9 | family friendly | Family amenities applied | The same |
| 10 | retirees | Notice | Notice, `neutral_places`, as today, until question 10 is answered. If yes: an offer of more residents aged 65 and over, note E |
| 11 | good for retirees | Notice | Notice, `neutral_places`, as today, until question 10 is answered. If yes: the same offer |
| 12 | older people | Notice | Offer: more residents aged 65 and over. Note D |
| 13 | pensioners | Notice | Notice, `neutral_places`, as today, until question 10 is answered. If yes: the same offer |
| 14 | people living alone | Nothing is made of it | Offer: more households of one person. Note G |
| 15 | households with children | Nothing is made of it | Offer: more households with children. Note F |
| 16 | singles | Notice | Notice, `neutral_places`. It says whether a person has a partner, which nothing counts |
| 17 | professionals | Notice | Notice, `neutral_places`. It says what people do for work |
| 18 | students | Notice | Notice, `neutral_places`. Not decided on |
| 19 | a student area | Notice | Notice, `neutral_places` |
| 20 | not too many students | Notice | Notice, `find_never_avoid`. No edit |
| 21 | no families | Nothing is made of it | Notice, `find_never_avoid`. No edit and no offer |
| 22 | away from old people | Notice | Notice, `find_never_avoid`. No edit and no offer |
| 23 | somewhere without many pensioners | Notice | Notice, `find_never_avoid`. No edit and no offer |
| 24 | fewer young professionals | Notice | Notice, `find_never_avoid`. No edit and no offer |
| 25 | quiet, not many young people | Notice. Quiet streets applied | Notice, `find_never_avoid`. Quiet streets applied, as today |
| 26 | no families with screaming kids next door, quiet | Offer: Quiet streets. No notice | Notice, `find_never_avoid`. Offer: Quiet streets. No offer of households |
| 27 | a Muslim area | Notice | Notice, `neutral_places`, reworded |
| 28 | near a mosque | Heard. No measure yet | The same. It is a wish about a place |
| 29 | lots of Polish people | Notice | Notice, `neutral_places`, reworded |
| 30 | middle class | Notice | Notice, `neutral_places`, reworded |

The same holds for: diverse, rich people, people on benefits, people like me, gay friendly. Each keeps the notice. "Affluent" is read of the place alone, as the founder decided the same day, and is no part of this page.

Four more, each a phrase for an age or for households beside a word that was not decided on. Each gives the notice today, and must still give it, with no offer, once "families" and "older people" are offered:

| Typed | Today | Should give |
|---|---|---|
| white families | Notice | Notice, `neutral_places`. No offer of households |
| young Muslim families | Notice | The same |
| middle class families | Notice | The same |
| wealthy retirees | Notice | The same |

### What a model may do

A model proposes and the person confirms. For a measure about residents a model may propose an offer with the choice more, and nothing else. Code withholds an edit on such a measure that asks for less, and withholds every edit a model proposes for a request the rules heard as about people, as it does today.

## 8. Rule 8, proposed

The rule in `AGENTS.md` is left as it is until the founder has approved a wording. This is the wording that is proposed.

| | Rule 8 |
|---|---|
| Today | Rank places, never residents. Nothing that describes who lives somewhere may feed ranking or a tag. Protected-characteristic data is registered as `audit_only`, which the gate keeps out of scoring, or under `residents` for the one use `census_table`, which the gate lets into the census table on an area's page and nothing else. See ADR 0006. |
| Proposed | Help a person find a place, and never avoid people. Two things about who lives somewhere may feed ranking and a vibe: the age of residents and the make-up of households, from the census. Each says in its name what it counts and the year it was counted, and a person may ask for more of it and never for fewer. Nothing else that describes who lives somewhere may feed ranking, a vibe or a filter. Ethnicity and religion are shown on an area's page and never ranked on. Stop and search data is never read. Every census table about residents is registered under `residents` or as `audit_only`, and the gate lets only the tables of age and of household composition into scoring. See ADR 0006. |

The heading of the rule, "Fairness", stands. Rule 8 of each nested `AGENTS.md` that repeats it changes with it.

## 9. Core's guards

Core was not changed. Each row is one change, to be made together in one reviewed change. After it, age and household make-up pass, and everything else about residents is refused as it is today.

### The vocabulary: `packages/core/src/burro_core/ids.py`

| What | Change |
|---|---|
| `FeatureId` | Add four members, with the ids of section 4 |
| `Describes` | Add `RESIDENTS = "residents"`. Its docstring says there is no value for who lives somewhere: it now says there is one, for age and household make-up alone |
| `FeatureKind` | Add `RESIDENTS = "residents"`: more of it only, by a fairness rule, and it may stand in a one-way vibe. `ON_REQUEST` will not do: it may stand in no vibe |
| `Dimension` | Add `RESIDENTS = "residents"` |
| `Family` | Add `WHO_LIVES_THERE = "who_lives_there"`, last in the order |
| `TagId` | Add a member for each new vibe that is built |
| `Notice` | Add `FIND_NEVER_AVOID = "find_never_avoid"` |
| The docstring of the module | It says a feature describing who lives somewhere cannot be asked for, because there is no id for it. It now names the four ids that there are |

### The catalogue: `packages/core/src/burro_core/catalogue.py`

| What | Change |
|---|---|
| `_FEATURES` | Add the four, each with the label and short label of section 4, unit `%`, polarity `MORE`, the comparatives `more` and `fewer`, kind `RESIDENTS` |
| `_feature` | `describes` is `RESIDENTS` where the dimension is `RESIDENTS`. `in_likeness` is false for such a feature |
| `_FAMILY_OF` | `Dimension.RESIDENTS` is shown in `Family.WHO_LIVES_THERE` |
| `FAMILIES` | The label of the new group: "Who lives there, at the 2021 census" |
| `checked_recipe` | Three new refusals. A recipe reads a part that describes residents from its high end. A scale holds no part that describes residents. A recipe that holds such a part says so first in its meaning |
| `_TAGS` | The new vibes of section 5, once the founder has chosen |

### Likeness: `packages/core/src/burro_core/likeness.py`

| What | Change |
|---|---|
| `may_be_compared` | Add `feature.describes is not Describes.RESIDENTS`, beside the line for events. A flag alone is not enough: it is what no flag may undo |
| The docstring | "Nothing here describes who lives somewhere, because no feature does" becomes: likeness is never counted on a feature that does |

### The reader: `lexicon.py`, `grammar.py`, `reading.py`, `interpret.py`

| What | Change |
|---|---|
| `POLICY_LEXICON` in `lexicon.py` | Take out: young families, lots of families, full of families, other families, young people, old people, older people, elderly. Keep every other phrase, `students` and `singles` among them. Keep young professionals, young couples, pensioners and retirees until the founder has answered question 10 of section 11 |
| `LEXICON` in `lexicon.py` | Add each phrase taken out, and families, people living alone, living alone, as a target with the note of section 7. A target with a note is offered and never applied |
| `Target` in `lexicon.py` | No new field. `direction` is `MORE` |
| `about_a_campus` in `grammar.py` | Widen it to any target that describes residents. A wish that turns such a target is a wish about people: `Kind.PEOPLE` |
| `_thing` in `interpret.py` | In a prompt that is not plain, a target that describes residents is offered unless a turning word, or a phrase of `POLICY_LEXICON`, stands in its clause. Where one does, nothing is offered |
| `_feature_choices` in `interpret.py` | For a feature that describes residents, one choice: more. Today a feature of one direction is given a second, with the direction `less`, which takes its weight off. "Leave it out" is added last to every offer, as it is today |
| `NOTICES` and `NOTHING_CHANGED` in `interpret.py` | The words of section 7. `_PLACES_NOT_PEOPLE` says Burro never ranks by who lives there, which is no longer so |
| The docstrings that say "Burro ranks places, never residents" | `interpret.py`, `lexicon.py`, `rank.py`, `catalogue.py`. Each now says what is ranked on |

### Facts and sentences: `facts.py`, `explain.py`, `verify.py`, `ids.py`

| What | Change |
|---|---|
| `TemplateId` | Add `FEATURE_RESIDENTS`. Its sentence holds the year of the census, which the plain template has no slot for |
| The fact of such a feature | Its slots hold who is counted and the day of the census, so that the verifier finds "2021" in the fact a sentence cites |
| `verify.py` | Nothing. It still has no list of words for residents, which is the known limit of contract section 7.4 |

### The tests of core

| Test | Today | Change |
|---|---|---|
| `test_catalogue.py::test_no_feature_or_tag_describes_residents` | No word for who lives somewhere stands in any name, and `Describes` has three values | Keep the word list as it is, and hold everything else to it as today. Leave out of what is searched: for a feature whose `describes` is `RESIDENTS`, its id, label, short label and the sentence of its measure, and for a vibe that holds such a part, its id, label, meaning, shelf word and what it cannot see. Leave out the label of the new group of the settings. `Describes` has four values |
| A new test beside it | | The features that describe residents are the four of section 4, by id and by label, letter for letter. Each has polarity `MORE`, kind `RESIDENTS`, unit `%` and `in_likeness` false. Each label ends `, Census 2021` |
| A new test beside it | | No name of a feature that describes residents holds a word of the second list below. Nor does anything that is left out of the search above for a vibe that holds such a part: its id, label, meaning, shelf word and what it cannot see. So a vibe that counts households can never be named for a faith, a nation or a class |
| `test_catalogue.py::test_the_denylist_would_catch_a_feature_that_describes_residents` | Six names are caught | Keep all six: "Share of residents aged 20 to 24" and "Households with children" are no label of the four, so both are still caught. Add: "Residents aged 20 to 34 by ethnic group", "Households of lone parents", "Residents born abroad", "Students as a share of all residents" |
| `test_catalogue.py::test_the_catalogue_holds_every_feature_and_tag_once` | 44 features, 12 vibes | 48 features, and 12 vibes and each new one |
| `test_catalogue.py::test_the_families_are_four_in_the_order_of_the_settings` | Four groups | Five |
| `test_release.py::test_the_release_holds_no_count_of_residents` | The words "population" and "residents" are nowhere in a release | A release holds no count: every metric that describes residents has the unit `%`. With those metrics, the vibes that hold one and the facts of each taken out, the two words are nowhere in a release |
| `test_likeness.py` | | Add: likeness is never counted on a feature that describes residents, whatever its flag says |
| `test_interpret.py::test_a_request_about_who_lives_somewhere_makes_no_edit_at_all` | Every phrase of `WHO_LIVES_THERE` gives the notice | Move the phrases that become offers to a new list. For each: no edit, status `suggest`, one offer with the choices more and leave it out |
| `test_interpret.py::test_a_request_to_find_a_group_is_not_turned_into_the_tag_that_sounds_like_it` | "lots of young families" makes no edit for families | It still makes no edit. It now offers households with children, and Family amenities is still not applied by it |
| `test_interpret.py::test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served` | The notice is `neutral_places` | The notice is `find_never_avoid` |
| `test_interpret.py::test_the_policy_lexicon_holds_words_for_people_and_never_for_buildings` | | Add: no phrase of `POLICY_LEXICON` is a phrase of `LEXICON`, which it already holds, and no phrase for ethnicity, religion, nationality, class or income is in `LEXICON` |
| `test_interpret.py::test_every_feature_and_vibe_is_recognised_by_its_label_and_its_short_label` | A label that is typed is applied | A label of a feature that describes residents is offered, and not applied |
| A new test | | Over every phrase that becomes an offer, and every turning word before it: the notice, no edit, no offer |
| A new test | | Over every phrase that becomes an offer, and every phrase of `POLICY_LEXICON` in the same clause, before it and after it: the notice, no edit, no offer |
| A new test | | No choice of any offer of a feature that describes residents has the direction less |
| `test_fixture.py::test_a_request_about_who_lives_somewhere_changes_no_ranking` | | Add "no families" and "away from old people" |
| `test_verify.py::test_a_sentence_about_residents_or_safety_is_rejected` | Expected to fail, as a known limit | The same. "Popular with young families" is still a sentence no explainer may write |

The second list, of what was not decided on. It is every word of `RESIDENT_WORDS` that is no word for age or for households, and seven more. Each is matched as `RESIDENT_WORDS` matches it, so that "religious" is caught with "religion". No name that can be ranked on holds one:

`ethnic`, `race`, `racial`, `religion`, `faith`, `born`, `birth`, `language`, `gender`, `sex`, `disabled`, `disability`, `health`, `income`, `deprived`, `poor`, `rich`, `wealth`, `class`, `migrant`, `immigrant`, `nationality`, `student`, `tenure`, `tenant`, `owner`, `married`, `marriage`, `partnership`, `cohabiting`, `lone parent`, `employed`, `qualification`.

### The pipeline, on the day core changes

| File | Change |
|---|---|
| `derive/census_msoa.py` | `Proposed` becomes a row of the catalogue, made with `catalogue_row`. `core_holds` and the test that core holds no such feature go |
| `derive/measures.py` | Add the four to `MEASURES`, in the order of their ids. Each is `Measure(FeatureId(module.KEY), module.SOURCE, module.is_the_table, module.METHODS, module.CANNOT_SEE, ...)`, and its build is handed the spine. The source holds two files, and `is_the_table` tells them apart |
| `native_resolution` in core's catalogue | Core says the smallest area the publisher gives a figure for. For both tables that is the output area, so `OA`, and no new value is needed. The rows are keyed by MSOA while an area is one, as they are for flats |
| `evidence/row.py` | Consider a flag for a count its publisher changed a little before publishing. None was added here |
| The synthetic release | `make fixture`. The made-up city needs made-up figures for the four |

### Everything else

| Where | Change |
|---|---|
| `contracts/openapi.json` | `make openapi`. The lists of features, vibes and notices grow |
| `docs/design/contract.md` | Sections on the catalogue, the reader and the notice |
| `apps/web`, `apps/ios` | `make web-types`, `make web-record`, the models of the iPhone app. The card of a vibe and the line beside a figure, as section 6. The new group of the settings. A test that no control sorts, colours or filters by a feature that describes residents |
| `services/api/tests/test_reader.py`, `test_reader_kept.py`, `test_routes.py` | The tests named for a request about who lives somewhere, as the tests of core above |
| `evals/reader/cases/who_lives_there.jsonl` | `who-004` becomes an offer. `who-005`, `who-041` and `plainp-019` in `plain_prompts.jsonl` stand as they are until the founder has answered question 10 of section 11 |
| `docs/PLAN.md` | The row on census figures in the table at its head. The two lines of section 9 that say nothing about residents feeds a score. The row on steering in section 13. Decision 4 of section 14. The line of section 15 on ranking by who lives somewhere. Each now names age and household make-up as what may be ranked on |
| `registry/README.md` | Done |

## 10. What was fetched

| List | Item | Source | Address | Size |
|---|---|---|---|---|
| `m11-age-and-households` | `census-ts007a` | `ons-census-2021-age-and-household-tables` | `https://www.nomisweb.co.uk/output/census/2021/census2021-ts007a.zip` | 5,714,105 bytes |
| `m11-age-and-households` | `census-ts003` | The same | `https://www.nomisweb.co.uk/output/census/2021/census2021-ts003.zip` | 6,170,227 bytes |

Edition: Census 2021, by the code of each table. Period: 21 March 2021. Each address was read on the publisher's page of bulk downloads, twice. Both were fetched on 2026-09-24, and each has a receipt under `data/receipts/`. Nothing is left to fetch.

## 11. Beside what was decided

Nothing was built on any of these. Each is a question for the founder.

| # | Question | What it would add | What it would take |
|---|---|---|---|
| 1 | May students be counted? | "Student area" is a thing people type, and the census counts full-time students by area | A decision. In the cases the reader is scored on, most phrases about students ask to be kept from them |
| 2 | May the share who rent be ranked on? | It says where a renter will find homes to rent. The registry holds tenure for display alone | A decision. Tenure describes households, and stands close to income |
| 3 | May one-person households be split by age, as the table splits them? | It would tell a young person who lives alone from an old one, which the measure cannot | A decision. Both parts are age and household, but the cut is finer than was asked about |
| 4 | May any other band of age be counted, such as children, or 35 to 49? | A family vibe could count children, and not only households that hold them | A decision on which bands. The table holds 18 |
| 5 | Are disability, sexual orientation and gender identity to be shown on an area's page? | Nothing for ranking. They are not among the tables that are shown today | A decision. Two of the three are published for MSOAs only, and one was marked down by its publisher |
| 6 | Is the notice to point to the census table? | A person who asks about a community is told where the figures are | To confirm. ADR 0014 says it does not |
| 7 | Is Settled wanted, and under what name? | A vibe for a person who types "retirees" | A name that claims no more than is counted |
| 8 | One family vibe or two? | Family amenities stays about places, or gains households with children | A choice of section 5 |
| 9 | Is a figure of 2021 to be ranked on in 2027? | Nothing. It is a risk | A line on the page is built. Whether it is enough is the founder's to say. The next census is not before 2031 |
| 10 | May a phrase that names an age and also work or a partner be offered for its age alone: young professionals, young couples, retirees, pensioners? | "Young professionals" is among the first things people type | A decision. The ranking would rest on age alone, and the offer would say so. But the words name what people do for work, which was not asked about, and a person may take the offer for more than it is |
| 11 | How a couple is joined, and lone parents | Nothing. The table of household composition names both, and the step refuses a measure of either | Nothing, unless the founder wants one. Marriage and civil partnership is a protected characteristic |
| 12 | Is the census table of age and of household composition approved to be shown before the fences round the census table are built? | The entry of the two tables is approved, and lists `census_table` beside `scoring`. The entry of the other three tables is gated until those fences pass | To confirm. Fetch and the fence still keep a file apart that was fetched for the census table, so nothing is shown yet |
| 13 | Does a vibe that counts residents wait for the proxy audit? | A check that no vibe ranks by ethnic group, religion, country of birth or income under another name. Settled is the vibe most likely to | The audit, which is not built. Without it, a vibe ships on the founder's judgement of its recipe alone |
| 14 | Is Young and busy built at all? | Little. On the parts held it stands at 0.93 with Homes, and 156 of its first 200 areas are the first 200 of Homes | A choice: drop it, or wait for the venues and measure it again. A smaller part for residents does not help while the venues are not held: what is left of the recipe is the two parts of Homes |
| 15 | May a vibe that counts residents have a band while residents are most of what is held? | Family area has a band at 65 in 100 of its recipe, and households with children are 69 in 100 of that. It stands at 0.92 with that one measure | A rule in core: such a vibe has no band until its parts about the place are held, or residents are held to a share of what is held and not only of the recipe |
| 16 | Is the note inside the zip of households to be opened? | The version of the table, which no page gives for the zip | To open one file of text that holds no count |

## 12. The row of the proxy audit

**The proxy audit was dropped on 25 September 2026**, by the founder's decision ([decision record 0006](../adr/0006-rank-places-not-residents.md), as amended that day). This row stays where it is, as a record of what was measured, and holds nothing back.

[Decision record 0006](../adr/0006-rank-places-not-residents.md) asks for this row before a measure is served. It covers the four measures, and the two vibes that hold one at 40 in 100 of their recipes: Family area, which holds households with dependent children, and Young professionals, which holds residents aged 20 to 34. It follows the row written for [recorded incidents](../research/data/incidents.md), section 11. It was written on 2026-09-24, before any of the six was in a release. Nobody has reviewed it, and no audit has run.

| | |
|---|---|
| The aim it serves | To say where more residents of an age lived, and where more households of a kind were, for a person who asks for them: young adults, older residents, households with children, households of one person. In a vibe, to say at what stage of life an area was lived, beside what is there for it |
| Why it is in proportion | It counts the age of residents and what their households are made of, from two census tables, and nothing else about who lives anywhere. Each figure is a share in 100, and no count of people is held. A person may ask for more of what a figure counts, and never for fewer: it has one direction, it stands in no scale and no filter, and no reading of any words asks for less of it. It counts only where a person asks: every phrase for it is offered and never applied, no button that adds several things adds it, no model may offer it, and no result shows it to a person who did not ask. It counts towards no likeness between two areas. Its name says who is counted and ends ", Census 2021", and each offer says that Burro counts who was living there at the census of 2021, and measures places first. In a vibe it is 40 in 100 at most, and what is there is the rest |
| What it was measured against | Other measures of the place, across London's 1,002 areas, as rank correlations. The table below holds them |
| What could not be measured | Whether any of the four, or either vibe, follows what was not decided on: ethnic group, religion, country of birth, income, health or qualifications |
| Why it could not | No step that runs an audit is built. The census tables of ethnic group, religion and country of birth are held for the table on an area's page and for the audit, and the gate refuses each for anything else. The measure of deprivation is held for the audit alone. So no figure of any of them was read here, and no correlation with one is claimed |
| What is known all the same | Each of the four follows how built up a place is, and how near the centre. Residents aged 20 to 34 stand at 0.80 with flats, and households of one person at 0.79. Inner and outer London differ in much that was not decided on, so a measure that tells inner from outer London may follow it. How far is not known. Family area does not tell inner from outer London: it stands at nought with flats and with distance from the centre. Young professionals does, as the measure it holds does. The census was taken on 21 March 2021, during a lockdown, and its publisher says that the pandemic may have affected where some people were counted, and names students and some urban areas: the young are the most likely to have been counted somewhere else |
| What triggers a review | A rank correlation of 0.5 or more, either way, between any of the four measures or either vibe and any figure of ethnic group, religion, country of birth or income, across London's areas. It is the figure the row for recorded incidents gives, and the founder's to set |
| What can then be done | Take the measure out of the vibe. Lower its share of the recipe below 40 in 100. Serve it as a measure a person may weigh and not as a vibe. Or take it out of the release |

What each stands at with measures of the place, as rank correlations across London's 1,002 areas. The four measures are worked out from the two tables as fetched. Each vibe is worked out as core works a vibe out, from the four and from the measures of the place of a build of London made the same day.

| | Flats | Homes per hectare | Distance from the centre | Houses or flats |
|---|---|---|---|---|
| Residents aged 20 to 34 | 0.80 | 0.78 | -0.74 | 0.84 |
| Residents aged 65 and over | -0.59 | -0.63 | 0.51 | -0.65 |
| Households with dependent children | -0.63 | -0.51 | 0.64 | -0.60 |
| Households of one person | 0.79 | 0.57 | -0.64 | 0.73 |
| Family area | 0.00 | 0.14 | -0.04 | 0.08 |
| Young professionals | 0.82 | 0.75 | -0.74 | 0.84 |

Family area stands at 0.65 with Family amenities and at 0.57 with households with dependent children alone. Young professionals stands at 0.83 with Going out and at 0.87 with residents aged 20 to 34 alone.

## 13. What was built, and what was chosen

Built on 2026-09-24, after the row of section 12 was written. Every rule of section 5 is a test. Where this page left a choice, this says which way it went, and each is the founder's to overturn.

| What | Built as | Where this page left a choice |
|---|---|---|
| The four measures | Features of core, `COUNTS_RESIDENTS`, each of kind and of dimension `residents` and of the family "Who lives there, at the 2021 census". Polarity more, unit %, in no likeness. A person may weigh each on request | Their short labels hold no figure, as every short label does: "More young adults" is of residents aged 20 to 34, and "More older residents" of residents aged 65 and over. The label holds the ages |
| Family area | One way: households with dependent children 40, primary schools within 800 m 25, the nearest play space 20, the nearest park 15 | The recipe of section 5 gave the households 45. No part is over 40 now, and the three parts of the place are in the order and near the shares that Family amenities gives them |
| One family vibe or two, question 8 | Two. Family amenities stays a vibe of places, and says in its meaning that it counts places alone | A person can still ask for what is there without counting who lives there, which the decision record says they can. "Family friendly", "good for kids" and "good for families" are offered as both, and the person chooses. "Families" and "a family area" are offered as Family area |
| Young professionals | One way: residents aged 20 to 34 at 40, the nearest station 25, places to eat and drink for each 1,000 homes 20, cultural venues for each 1,000 homes 15. It says it cannot see what anyone does for work | It is built in place of Young and busy, which held flats and homes per hectare and found the areas that Houses or flats finds. Section 14 says how it stands against Houses or flats on London's areas |
| Settled, question 7 | Not built. "Retirees", "pensioners", "older people" and "elderly" are offered as More older residents, and "older and quieter" as that and Quiet streets | |
| Words that name an age and also work, question 10 | "Young professionals", "retirees" and "pensioners" are offered for the age alone. "Professionals", "young couples", "singles" and "students" draw the notice | What people do for work, whether they study and whether they have a partner are counted by nothing |
| "People my age" | Offered as both ages, under a note that begins "What age?" | |
| A wish for fewer of anyone | The notice, and nothing else. A prompt that draws the notice is offered nothing that counts who lives somewhere, whichever of its words drew it | The notice was reworded, because it said that Burro never ranks by who lives there: "Burro ranks places by what is there. Of who lives in a place it counts only their age and their households, at the census of 2021, and you cannot ask for fewer of anyone." |
| A word that was not decided on, beside those who are counted | The notice: "young white professionals", "muslim families", "wealthy families" | |
| What a result shows | A vibe that counts residents holds no `strip`. It is on a result where it was asked for, and is among the others on the portrait of an area, never in the list of what the area has most or least of | Recorded crime is held the same way on a result |
| A model | It is told of no measure and no vibe that counts residents, and an edit of its that names one is dropped | |
| Whether a vibe waits for the audit to run, question 13 | It did not wait. The row is written, and no audit has run. Since 2026-09-25 none is to run: the founder dropped the proxy audit | The founder asked for it to work. No release of London is served |
| A band while residents are most of what is held, question 15 | Core's rule stands: a vibe has a band where 60 in 100 of its recipe is measured | With every part held, residents are 40 in 100. Where one part of the place is missing they are more of what is held: half, where primary schools are missing from Family area |
| The website | It draws each where it draws a measure or a vibe: the settings, the shelf, the page of vibes, the methods, the map, a comparison and the page of an area. An offer is drawn with its note, as the API sends it | The page of an area draws eight lines more at most before anything is opened, and its height was not measured again in a browser |
| The iPhone app | Its generated files are made again, and it names the new group of measures. Its tests and its build were not run | |

## 14. What a build of London shows

London was built once with the four measures in it, on 2026-09-24, from every list that holds a receipt: `lon-2026-09-24-80`, a preview that is served to nobody. It carries 32 measures, and every fact of it has evidence behind it. Each of the four has a figure in each of the 1,002 areas. Every figure here is of London as a whole or of a borough. None is of a named place.

| | Family area | Young professionals |
|---|---|---|
| Areas with a band | 1,002 of 1,002 | 994 of 1,002. Eight areas at the edge of London have a figure for the census part alone, which is 40 in 100 |
| Rank correlation with Houses or flats | 0.08 | 0.84 |
| With flats alone | 0.00 | 0.82 |
| With homes per hectare | 0.14 | 0.75 |
| With distance from the centre of London | -0.04 | -0.74 |
| With the census figure it holds, alone | 0.57 | 0.87 |
| With the vibe nearest to it | Family amenities, 0.65 | Going out, 0.83 |
| Areas of its highest band that are in the highest band of Houses or flats | 26 of 200 | 133 of 198 |
| Middle distance from the centre, highest band and lowest | 12.7 km and 14.3 km | 5.5 km and 17.2 km |
| Boroughs with most areas in its highest band | Newham 29 of 40, Barking and Dagenham 16 of 22, Ealing 14 of 41, Enfield 14 of 36, Tower Hamlets 13 of 34, Redbridge 12 of 33 | Tower Hamlets 22 of 34, Camden 18 of 27, Hackney 17 of 30, Hammersmith and Fulham 16 of 25, Islington 16 of 23, Westminster 16 of 24 |
| Boroughs with most areas in its lowest band | Bromley 19 of 39, Croydon 15 of 45, Havering 13 of 30, Kensington and Chelsea 12 of 21, Westminster 11 of 24, Camden 9 of 27 | Bromley 26 of 39, Bexley 18 of 28, Croydon 16 of 45, Havering 16 of 30, Barnet 14 of 42, Sutton 13 of 24 |
| Boroughs with no area in its highest band | Bromley, Camden, Islington, and the City of London | Barking and Dagenham, Barnet, Bexley, Bromley, Enfield, Havering, Redbridge, Richmond upon Thames, Sutton |

**Young professionals is served as a vibe, and it says little that Houses or flats and Going out do not.** It stands at 0.84 with Houses or flats, under the 0.9 at which it would have been served as a measure alone, and at 0.83 with Going out. Two of its parts are 70 in 100 of Going out's recipe, and the census figure it holds stands at 0.84 with Houses or flats by itself. A Londoner would know its map: the inner boroughs at its head, and Bromley, Bexley, Havering and Sutton at its foot. They would know the same map from Houses or flats. The made-up city holds every two vibes to 0.8 at most, and London does not hold these two to it.

**Family area finds where households with children live close to schools, play space and parks, and that is not where a Londoner would look first.** It is no map of inner and outer London, and no map of flats: it stands at nought with both. It puts Newham, Barking and Dagenham, Enfield and Redbridge at its head, which a Londoner would know as places where many children live. It puts Tower Hamlets and Hackney there too, and puts Bromley, Havering and Kingston upon Thames low: 19 of Bromley's 39 areas are in its lowest band, and none is in its highest. The three parts of the place are counted in a straight line, within 800 metres or to the nearest, so each is nearer where homes stand closer together. An outer borough of houses and gardens has children and has fewer schools and play spaces within reach of each home. Family amenities shows the same lean more strongly: it puts Tower Hamlets, Southwark, Lambeth, Hackney and Islington first. Look at the map of each before either is served.

Two searches were made of the build through the API, with every offer pressed. Nothing was applied from the words of either.

| Typed | Offered | The first ten, by borough |
|---|---|---|
| "young professionals, lively, near a station" | Young professionals, with its note. Going out, towards Buzzy or towards Calm. Nearer a station | Camden, Westminster, Westminster, Lambeth, Camden, Camden, Westminster, Newham, Hammersmith and Fulham, Westminster. 994 areas are ranked. Of the first fifty, nine are in Westminster, seven in Camden and seven in Tower Hamlets |
| "a family area with good parks" | Family area, with its note. Nearer a park. "With good" was not read, and the answer says so | Croydon, Newham, Greenwich, Merton, Haringey, Tower Hamlets, Barking and Dagenham, Sutton, Newham, Newham. 1,002 areas are ranked. Of the first fifty, nine are in Newham and five in Barking and Dagenham |

The row of section 12 was written before the build, from the two tables and from the measures of the place of a build made earlier that day. The build gives every figure of it as it was written.
