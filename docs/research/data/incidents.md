# Recorded criminal damage and anti-social behaviour

Status: written on 2026-09-24, from the police's street-level crime file and from File 8 of the English Indices of Deprivation 2025, as each stood in the store that day, and from the publishers' pages read that day. It is a dated snapshot.

**Since this page was written** core has named both measures as they are built, at catalogue version 12, and a build whose lists hold the police's file carries both. Sections 7 and 8 say what stood in the way on the day they were written. Section 11 is the row of the proxy audit, which was written before either measure was served.

**No person has checked anything on this page.** Every count was made by a program. No figure of any one area is on this page, and none is in a test. A count is of London as a whole. What was found of the areas is said in words. The figures are beside the build, in a folder that git ignores.

## 0. In short

| Question | Answer |
|---|---|
| What is built | Two measures, each counted from the points of the police's own crime files: `incident_criminal_damage` and `incident_antisocial`. Each has a figure for all 1,002 areas |
| Which source | The police's file. The founder decided on 2026-09-24 that a vibe rests on the place, and File 8's two rates were moved by their publisher towards areas where the same kind of people live. No measure reads them. Section 1 |
| What is counted | Records of one kind, at the point the file gives, in the latest 36 months, of which the whole months are counted. Section 5 |
| What it is divided by | The homes of the area at the census of 2021: records a year for each 1,000 homes. The same count over land says little that homes per hectare does not. Section 6 |
| Are they in a release | Yes, since core came to count each for each 1,000 homes, as the row of each says. Section 7 says how it stood before |
| Is the receipt right | Yes. It states August 2023 to July 2026, and every row of every crime file states the month of its file. Nothing is fetched again. Section 5 |
| What is not whole | The three latest months of criminal damage and arson, from the larger force. They are left out, and said. Section 5 |
| What a moved point does | About one record in seven lies within 25 metres of the edge of its area, and may belong next door. Section 6 |
| Does Gritty follow deprivation | **Not known. The check could not be made.** The official measure is not registered, and is not read. Sections 9 and 11 |

## 1. Two sources, and which was taken

| | File 8 of the Indices of Deprivation 2025 | The police's street-level file |
|---|---|---|
| Registry id | `mhclg-iod-2025-underlying-indicators` | `police-uk-street-level-crime` |
| What the gate says, asked for `scoring` | Allowed | Allowed |
| What the gate says, asked for `validation_only` | Refused | Refused |
| In the store | Yes, with a receipt that states 2021, the year of transport noise | Yes, with a receipt that states August 2023 to July 2026. A person saved it from a form |
| What a row is | One small census area (LSOA of 2021), with a rate | One record, with a month, a kind and a point |
| Where an event is put | By "the full police geocodes", as the technical report says | At a point the publisher moves it to, so that it cannot be traced to an address |
| The years | Criminal damage: 2018/19 to 2023/24. Anti-social behaviour: 2022/23 to 2023/24 | August 2023 to July 2026 |
| What it is divided by | Who is "at risk": residents and those who work there | Nothing. Burro divides by the homes of the area |
| Smoothed | Yes, towards areas where the same kind of people live | No |
| Updated | Not until the next Indices. The edition before was 2019 | Each month |

**The police's file is taken.** The first build of these measures read File 8, because it was the one of the two in the store. The police's file has arrived since. The founder decided on 2026-09-24 that a vibe rests on the place, so a rate that its publisher smoothed by who lives in an area is not used. The two columns of File 8 are read by no measure, and the code that read them is taken out. Sections 2 to 4 are kept as the record of what the columns are, and of why they are not used.

**What is lost.** The better placing of events: File 8 was made from where the police placed each event, and the form gives points that were moved. And the years before August 2023.

**What stays on File 8.** Transport noise, with its receipt of 2021. Its publisher smoothed it the same way: section 4.

## 2. What the sheet holds

`File_8_IoD2025_Underlying_Indicators.xlsx`, file id `f-cbc9ba7072bd`. [The page on the files of the second build](m2-files.md) says what the workbook holds as a whole. This section adds the one sheet that was not read before.

| | |
|---|---|
| Sheet | `IoD25 Crime Domain`, the sixth of eight |
| Header | Row 1 |
| Rows under it | 33,755: one for each LSOA of England |
| Columns | 12 |
| Read by | No measure, since 2026-09-24 |

| Column | Was read | By |
|---|---|---|
| `LSOA code (2021)` | Yes | Both measures |
| `LSOA name (2021)` | No | |
| `Local Authority District code (2024)`, `Local Authority District name (2024)` | No | |
| `Violence with injury, rate per 1,000 'at-risk population'` | No | |
| `Violence without injury, rate per 1,000 'at-risk population'` | No | |
| `Stalking and harassment, rate per 1,000 'at-risk population'` | No | |
| `Burglary, rate per 1,000 'at-risk properties'` | No | |
| `Theft, rate per 1,000 'at-risk population'` | No | |
| `Criminal damage, rate per 1,000 'at-risk population'` | Yes | `incident_criminal_damage` |
| `Public order and Possession of weapons, rate per 1,000 'at-risk population'` | No | |
| `Anti-Social Behaviour, rate per 1,000 'at-risk population'` | Yes | `incident_antisocial` |

The names were read from the first row of this sheet alone. No other sheet was opened for them. The sheet of notes names the same indicators in other words: `Criminal damage, rate per 1,000 at risk population` and `Anti-social behaviour (ASB), rate per 1,000 at risk population`. So a column is found by its own name, and its row of the notes by the name the notes give.

| Of each of the two columns | |
|---|---|
| What a cell holds | A number of the workbook, and not text |
| Decimal places | One, in every cell |
| A missing value | None is written. All 33,755 cells hold a number |
| A cell below nought | None |
| A cell that holds nought | Criminal damage: none. Anti-social behaviour: 15, none of them in London |
| A code that is there twice | None |
| Codes of London | 4,994 of 4,994 |

The reader gives an empty cell as none, and never as nought. Nought is a rate: the file covers the LSOA and gives none.

## 3. What each column is

What the sheet of notes says, in the file's own words:

| | Criminal damage | Anti-social behaviour |
|---|---|---|
| `Data supplier` | "The National Police Chiefs Council, the Home Office, and individual police forces" | The same |
| `Data time point` | `2018/19 to 2023/24` | `2022/23 to 2023/24` |
| What is counted | "all sub-categories of ‘criminal damage’ and ‘arson’" | "all sub-categories of ASB that are reported to the police and are recorded as police incidents" |
| What it is | "the annual average rate of offences per 1,000 at risk population in the LSOA" | "the annual average rate of incidents per 1,000 at risk population in the LSOA" |
| What was done to it | "Shrinkage has been applied to this indicator" | The same |

No step reads either row now.

What the file does not say, and what the publisher's technical report says of it. The report was read on 2026-09-24, as text taken from the PDF the publisher's page links to.

| Not said in the file | What the technical report says | Where |
|---|---|---|
| Who is at risk | "the resident population plus an estimate of the non-resident workplace population". The residents are the statistics office's estimate for the middle of each year. Those who work there are taken from the censuses of 2011 and 2021, and prisoners are counted | 4.7.11, 4.7.32 |
| Where an event was put | From "the full police geocodes, not the geographically anonymised data released into the public domain". An event within 10 metres of a boundary is shared between the areas on each side. An event recorded at a police station is spread over the whole force area | 4.7.2, 4.7.7, 4.7.29 |
| What the counts were held to | Recorded crime was made to add up to the published totals of each police force. Anti-social behaviour was not | 4.7.9 |
| Why anti-social behaviour is of two years | The year 2021/22 was left out, over how forces recorded breaches of the rules of the pandemic | 4.7.6 |
| What shrinkage did | Each LSOA's rate was moved towards "the average of all LSOAs in the same LSOA Super Group Classification category within the LAD", which the report says is "to reflect shared socio-demographic characteristics". An LSOA with fewer events is moved further | 3.4.3, appendix C |
| How far a rate was moved | Not said. The file holds the rate after it was moved, and no other | |
| Which months a statistical year runs over | Not said | |
| Which police forces gave records | "individual police forces". None is named | 4.7.2 |

## 4. Is it a measure of a place

In what it counts, it is. An offence is recorded at a place, and the publisher placed each by the police's own record of where it was.

In two other ways it leans on who is there.

| | What follows |
|---|---|
| It is divided by those who live and work in the area. Visitors are not counted | The same offences read higher where few live and work and many pass through. An area of offices reads low, because those who work there are counted |
| Each rate was moved towards the average of small areas where the same kind of people live | A part of each figure is drawn from areas like it, and not from the area itself. The classification is made from the census of who lives in each small area. How large that part is cannot be worked out from the file |

**The second is the founder's to decide.** Rule 8 says nothing that describes who lives somewhere may feed ranking or a tag. The figure counts events and not residents. But the publisher used who lives in an area to smooth it. The same is so of transport noise, which a release carries today. The file and the technical report, at 4.9.35, both say shrinkage was applied to it. The report names ten indicators that were moved towards the average of their district alone, and noise is none of them.

What the figure is not: it is not the official measure of deprivation, and no word of the measure says deprived. The sheet is one of seven domains of that measure, and these are two of its eight columns.

## 5. What is built, from points

| | |
|---|---|
| Modules | `derive/incident_criminal_damage.py`, which holds the counting. `derive/incident_antisocial.py`, which counts a second kind with it. `derive/street_crime_files.py`, the one reader of the zip |
| What is opened | The 72 members of the zip whose names end `-street.csv`: a month of a force each. No other member is opened, and a test counts every one that is |
| What is read of a row | Four columns: `Month`, `Crime type`, `Longitude` and `Latitude`. Nothing of an outcome, and nothing of a person. The column that names an LSOA is not read: the file does not say which census it follows |
| The kinds | `Criminal damage and arson`, and `Anti-social behaviour`, as the file names them. It names 14 kinds in all |
| Where a record is counted | In the area whose land its point lies on. The point is turned to the National Grid and laid on the outlines of London's small census areas, which are the outlines the land of an area is measured on |
| Method | `points_in_area_by_homes@1`. Marked as measured |
| Rounding | One decimal place, with a half taken upward |
| Areas with a figure | 1,002 of 1,002 for each. No area is without a record of either kind |
| On the list of a build | Yes, both. Each is carried where a list of the build holds the police's file |

**The receipt is right.** It states the edition `August 2023 to July 2026` and the period 2023-08 to 2026-07. The list read both from the names of the folders of the zip. The rows now bear them out: every row of every crime file states a month, and it is the month of the folder the file is in. The step stops where one does not. So nothing is put right by hand, and nothing is fetched again.

What the crime files hold of the two kinds, over the months that are counted:

| | Criminal damage and arson | Anti-social behaviour |
|---|---|---|
| Months that are whole | 33, from 2023-08 to 2026-04 | 36, from 2023-08 to 2026-07 |
| Records counted in an area of London | 151,235 | 701,377 |
| Records whose point lies in no small census area of London | 366 | 308 |
| Records with no point | 720 | 102 |

**Three months are not whole.** In May, June and July 2026 the larger force's files hold about a twentieth of the criminal damage and arson of any month before them, in every borough alike, while they hold as many records of every kind together as before. The smaller force's files hold what they held before. Nothing in a file says why. So the step holds the months to each other: a month is whole where London's records of the kind are at least half of those of the middle month. A month that is not is left out for every area, and the figure is a count a year over the months that are left. The figure is then marked as partial, with 33 of 36 months behind it. Left in, the three months would lower every figure by about a twelfth, and the one area of the smaller force by nothing. The half is a choice and no finding. Whether the months are left out, or the count waits for a later file, is the founder's to say.

No month of either force is empty. The publisher's list of changes was read once, and said the larger force gave no data for some months of 2024: the zip holds those months, with as many records as the months beside them.

## 6. Over land or over homes, and what a moved point does

The count was worked out both ways, across the 1,002 areas. `for_each_hectare` gives the count over land, and no build carries it.

| Rank correlation | Criminal damage, over land | Criminal damage, over homes | Anti-social behaviour, over land | Anti-social behaviour, over homes |
|---|---|---|---|---|
| With homes per hectare | 0.88 | 0.14 | 0.89 | 0.46 |
| With distance from the centre | -0.65 | -0.06 | -0.68 | -0.36 |
| With nitrogen dioxide | 0.74 | 0.26 | 0.77 | 0.56 |
| With the other kind, counted the same way | 0.94 | 0.70 | 0.94 | 0.70 |
| With the rate File 8 gave | 0.53 | 0.67 | 0.77 | 0.84 |

- **Over land, each count says what homes per hectare says.** More happens where more people are, and the land does not know how many are there. The two kinds then put the areas in nearly one order.
- **Over homes, each tells areas apart.** Criminal damage over homes follows neither the centre nor how close together homes stand. It says something no other measure of a release does.
- **Over homes, a place with few homes and many visitors reads high.** The highest areas are the centre, where few live and many come, and an area that holds an airport. That is said beside the figure. It is the price of dividing by nothing that says who is there.
- **Over homes, the figure is nearer the rate File 8 gave**, which was divided by those who live and work in an area.

**What a moved point does.** A point of the file is not where an event happened: the licence registry says the publisher moves each record to a nearby anonymous spot. How far was not read on any page. What the file shows:

| | Criminal damage and arson | Anti-social behaviour |
|---|---|---|
| Different points the records stand at | 42,449 | 43,846 |
| Records at the middle point | 2 | 7 |
| Share of records within 10 metres of the edge of their area | 9 in 100 | 10 in 100 |
| Within 25 metres | 15 in 100 | 16 in 100 |
| Within 50 metres | 29 in 100 | 29 in 100 |

The edge of an area often runs down the middle of a street, and a point often stands on the middle of a street. So a record on a street between two areas is counted in one of them, and which one turns on a few metres. For the middle area about one record in seven lies within 25 metres of its edge. For a few areas it is more than half. So the figure of an area is less sure than its count suggests, and two areas that share a busy street may each read a little wrong. The outlines are generalised, which adds to it. Nothing is shared out between two areas today. File 8's publisher shared an event within 10 metres of a boundary between the areas on each side: whether Burro does the same is for whoever owns the method.

What each figure cannot see, as its module holds it for a screen:

| Measure | It cannot see |
|---|---|
| Both | Each record is at a point its publisher moved, so a record near the edge of an area may be counted in the area next to it |
| Both | It is counted for each 1,000 homes, so a place with few homes and many visitors reads high |
| Both | Whether a force gave every record of a month. A month that holds under half the records of the middle month is left out |
| Criminal damage | It counts what the police recorded as criminal damage or arson, which is not all that happened, and it cannot tell graffiti from a broken window or a fire |
| Anti-social behaviour | It counts what the police recorded, so it follows who calls the police as well as what happens |

## 7. What core needs

Core decides the name, the unit and how a feature is made. The row each measure writes says what the figure is, so it is not core's.

| Feature | What core says | What the figure is |
|---|---|---|
| `incident_criminal_damage`, `label` | Recorded criminal damage | Recorded criminal damage and arson |
| `incident_criminal_damage`, `unit` | per 1,000 residents a year | per 1,000 homes a year |
| `incident_criminal_damage`, `method` | measured | The same |
| `incident_antisocial`, `label` | Recorded anti-social behaviour | The same |
| `incident_antisocial`, `unit` | per 1,000 residents a year | per 1,000 homes a year |
| `incident_antisocial`, `method` | measured | The same |

`test_the_row_is_not_cores_so_a_build_leaves_the_measure_out` and `test_the_name_is_cores_and_the_unit_is_not` hold the list. Each fails on the day core says what the figure is, and the measure is then carried by a build whose lists hold the police's file. Core says each is of an LSOA, and the file is of points: that is core's to say too.

With core changed, in the same change: the rows of `incident_criminal_damage` and `incident_antisocial` in [the contract](../../design/contract.md), section 3.1; the synthetic release, with `make fixture`; and the recorded answers of the website and of the iPhone app, which hold the unit in words.

## 8. Gritty, and the guard on recorded crime

The founder decided on 2026-09-24 that Gritty is one vibe that counts recorded crime, and that typing "gritty" asks for it. Nothing of core was changed by this work. This is what stands in the way, and what does not.

**What is already as decided, and needs no change.**

| What | Where |
|---|---|
| The name of an end, "gritty" or "polished", is asking by name. It is applied as `stated` | Contract, section 8.2. `test_an_end_of_the_scale_that_is_named_is_asking_for_it_by_name` |
| A word that is only read into the vibe, "edgy" or "raw", applies nothing. The vibe is offered, and the offer says it counts recorded crime | `read_into_crime` in `grammar.py`. `test_built_as_a_scale_a_word_that_is_read_into_it_is_offered_and_says_it_counts_crime` |
| An edit that is only inferred never weighs the vibe | Rule 8 of the reducer. `test_an_inferred_edit_never_weighs_a_vibe_whose_recipe_holds_recorded_crime` |
| The vibe is on a result only where it was asked for. This is so of the vibes under the name of a result, and of nothing else that is served: rows 11 to 13 below | `rank.py`. `test_a_vibe_that_holds_recorded_crime_is_on_a_result_only_where_it_was_asked_for` |
| Every offer and every figure carries the caveat of recorded crime | `CRIME_CAVEAT` |

**What must change, in one change that a person reads, with a decision record.**

| # | What | Where | How |
|---|---|---|---|
| 1 | A real release is refused if it carries the vibe that holds recorded crime | The rule `gritty_b_is_synthetic` in `release.py`, and its place in `RULES` | Take the rule out |
| 2 | The test of that rule | `test_gritty_as_a_scale_is_refused_on_any_release_that_is_not_synthetic` | It becomes a test that a real release which carries the vibe is opened |
| 3 | The list of the rules of the contract | `test_every_rule_of_the_contract_has_a_release_that_breaks_it` | Take the name out of the set, and the line that excuses it |
| 4 | The test that one vibe alone holds recorded crime | `test_one_vibe_alone_holds_recorded_crime_and_it_is_one_a_real_release_may_not_carry` | It keeps what it asserts. Its name and its comment no longer say a real release may not carry it |
| 5 | The words of the rule | `MEANING` in `release/read.py` of the pipeline. Contract, section 2.8 and section 3.2, the row of variant `b` | Take them out with the rule |
| 6 | A real build carries gritty as land use | `GRITTY = GrittyVariant.A` in `assemble/release.py` of the pipeline, and the two tests of a whole build that hold it | It carries the vibe that was decided |
| 7 | A release carries the ten vibes and one of the two ways gritty was built | `tags_of`, `GRITTY` and `GrittyVariant` in core. `vibes_match_core`. `test_gritty_is_two_vibes_and_a_release_carries_the_ten_and_one_of_them` | The decision names Works and warehouses and Gritty as two vibes of one release. Whether the manifest still says a variant is for whoever owns the catalogue |
| 8 | The name of the vibe | `street_character` is labelled "Street character", with the ends Polished and Gritty. The verifier refuses "gritty" in any sentence but as the name of an end | The decision says the vibe is called Gritty. The id never moves |
| 9 | The decision records | ADR 0013, the row "May be in" and the sentence that ADR 0006 stands for every real release. ADR 0006, which says recorded crime is shown by category. The registry entry of the police file, which says recorded crime is never rolled into one score | Amend each, or add a record that does |
| 10 | The two features: the unit, and the name of the first | Section 7 of this page | |
| 11 | The portrait of an area is built with no spec, and draws every scale of the release. The vibe that holds recorded crime is one of its four scales | `SCALES` and `portrait` in `portrait.py`. `test_a_portrait_holds_ids_and_no_sentence_and_is_the_same_for_everyone` | Decide whether the page of an area shows the vibe to a person who asked for nothing. On the made-up release it is drawn for 21 of 24 areas, and its parts name the figure of each of the two rates |
| 12 | The map can be coloured by any vibe of the release, this one among them | `GET /v1/areas`, `bands`. `test_the_map_can_be_coloured_by_any_vibe_from_one_answer` | The same decision |
| 13 | The page of an area holds every measure the release carries | `GET /v1/areas/{id_or_slug}`, `features` | The two rates are then on every page. The plan shows recorded crime as rates by category, with its caveat, so this may stand as it is: the decision record says which |

Rows 1 to 6 and 9 are needed for any real release to carry Gritty. Rows 7 and 8 are choices the decision leaves to the catalogue. Rows 11 to 13 are what a real release would then serve to a person who asked for nothing. None is changed by rows 1 to 10, so each is decided before row 1 is made, and not after.

**Would rows 1 to 10 let recorded crime count on a word that does not name it?** No, for this vibe and for every other, while three things are left as they are. `HOLDS_CRIME` names one vibe. `checked_recipe` refuses the recipe of any other vibe that holds a measure of recorded crime. The reducer turns away an edit that is only inferred, of such a vibe and of such a measure. No row above touches one of the three. A change that adds a vibe to `HOLDS_CRIME`, or gives a second recipe a measure of recorded crime, is another decision.

**Gritty on London, on the recipe the founder was shown.** It was worked out beside the build, on all of the recipe: recorded criminal damage 20, works and warehouses 20, recorded anti-social behaviour 15, main roads 15, transport noise 10, homes per hectare 10 and nitrogen dioxide 10. Works and warehouses is the land used for industry and the land used for storage, added up, as [the page on land use](land-use.md) works each out. Core places every area. In words:

- **It follows how built-up and central an area is.** With the two counts over homes it follows homes per hectare at 0.58 and distance from the centre at -0.51. With the two counts over land it follows them at 0.83 and -0.70.
- **It reads the inner boroughs as Gritty and the outer ones as Polished.**
- **It is not believable at the centre, and recorded crime is not why.** Boroughs that most people would call polished have no area in the two bands nearest Polished. Four parts put them there: main roads, transport noise, homes per hectare and nitrogen dioxide. They are 45 in 100 of the recipe, and each is high at the centre whatever a street is like. They follow one another: nitrogen dioxide follows homes per hectare at 0.77, and noise follows main roads at 0.58. So nearly half the recipe says one thing four times. Taken alone, the four put such a borough's areas towards Gritty. Taken alone, the two counts over homes spread the same areas over every band.
- **No one weight is to blame.** With any one of the four taken out, the same areas move a little and stay towards Gritty. It is the four together.
- **Works and warehouses moves few areas.** Most areas hold next to no such land, so most areas stand level on it, and it tells apart only the few that hold some.
- **Counted over land, recorded crime joins the four.** Four fifths of the recipe then say how central an area is.

**Whether it follows deprivation is not known.** Section 9.

## 9. What could not be checked

| What | Why | What would settle it |
|---|---|---|
| Whether Gritty, or either measure, follows the official measure of deprivation | The licence registry holds no entry for it. The entry of File 8 allows `scoring` and `display`, and the gate refuses it for `validation_only` and for `audit_only`. Its conditions keep the columns about residents out of ranking, and its notes ask that the domains of deprivation are registered apart, for the audit alone | An entry for File 7 of the same release, for the audit alone. The publisher's page lists it as "File 7: All Ranks, Scores, Deciles and Population Denominators", a CSV of 9.44 MB, under the Open Government Licence v3.0. A file that is kept for the audit is fetched to a store of its own, which is not built. Both are the founder's to decide |
| How far shrinkage moved a rate of File 8, or its share of noise | The file holds each after it was moved | The publisher |
| Whether the three latest months of criminal damage will be filled | Nothing in a file says why they are short | A file saved from the form in a later month |
| How far a point was moved | No page that was read says | The publisher |
| Either figure against a published total | The file holds no row for a borough or for London | The Metropolitan Police's own table by LSOA, which the registry holds for validation and which is not in the store |
| The figures, by a person | None has been held against a map or a visit | |

## 10. The police file: what a person saves next

The registry entry `police-uk-street-level-crime` is approved for scoring and display. It allows the crime files alone. The list `m2-living` holds the file as `police-crime-london`. [The page on the files a person saved](by-hand-files.md) says what the zip of 2026-09-24 holds. The next file is saved so:

| On the page https://data.police.uk/data/ | Set it to |
|---|---|
| Date range | The latest 36 months the form offers |
| Forces | "Metropolitan Police Service" and "City of London Police", and no other |
| "Include crime data" | Ticked |
| "Include outcomes data" | Not ticked |
| "Include stop and search data" | Not ticked |
| "Generate file" | Press it, and save what it offers |

The last two are never taken: the registry entry forbids both, and the second holds the ethnicity, the gender and the age of a person stopped. Look at the names inside the zip before it is handed over.

What the publisher's pages said on 2026-09-24, read once through a reader that extracts, and held to nothing:

- A point is not where an event happened. It is the nearest of a list of points, each over the middle of a street or a public place.
- The publisher's list of changes says the Metropolitan Police gave no crime data for some months of 2024, and that the transport police have given no data on anti-social behaviour since April 2016. The zip holds a crime file for every month of 2024, each with as many records as the months beside it. The transport police are not on the list, so what they record at a station is in no figure.

## 11. The row of the proxy audit

**The proxy audit was dropped on 25 September 2026**, by the founder's decision ([decision record 0006](../../adr/0006-rank-places-not-residents.md), as amended that day). This row stays where it is, as a record of what was measured, and holds nothing back.

[Decision record 0006](../../adr/0006-rank-places-not-residents.md) asks for this row before a measure is served. It covers both measures, and Gritty, which holds them at 45 in 100 of its recipe. It was written on 2026-09-24, before either was in a release. Nobody has reviewed it.

| | |
|---|---|
| The aim it serves | To say where more criminal damage and more anti-social behaviour were recorded, as a part of how gritty or how polished a place is |
| Why it is in proportion | It counts what was recorded at a place, from the police's own open file. It is divided by homes, and holds nothing of who lives anywhere. It is never said as safe or unsafe. It counts only where a person asks for recorded crime, or for Gritty, by name. Every offer and every figure says that recorded crime depends on what is reported |
| What it was measured against | Other measures of the place, across London's 1,002 areas, as rank correlations. Criminal damage over homes stands at 0.14 with homes per hectare, -0.06 with distance from the centre and 0.26 with nitrogen dioxide. Anti-social behaviour over homes stands at 0.46, -0.36 and 0.56. The two kinds stand at 0.70 with each other. Section 6 holds the table |
| What could not be measured | Whether either measure, or Gritty, follows who lives in an area: the official measure of deprivation, or any count of residents by ethnic group, religion, country of birth, age, health or income |
| Why it could not | No file is registered for the audit alone, and no store holds one. The registry allows File 8 for scoring and for display, and the gate refuses it for an audit. No step that runs an audit is built. So no figure about residents was read, and no correlation with one is claimed |
| What is known all the same | Each figure follows the rate File 8 gave for the same kind, at 0.67 and 0.84. That rate is a part of the official measure of deprivation, and its publisher moved it towards areas where the same kind of people live. So each figure follows that part of the measure. How far it follows the whole is not known |
| What triggers a review | A rank correlation of 0.5 or more, either way, between either measure or Gritty and any figure of who lives in an area, across London's areas. It is a first figure, and the founder's to set |
| What can then be done | Take the measure out of Gritty. Cap its weight in the recipe. Or leave it as it is served today, behind a press that says it counts recorded crime |

## 12. Pages read

| Page | Address |
|---|---|
| English indices of deprivation 2025 | https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025 |
| English indices of deprivation 2025: technical report, the page | https://www.gov.uk/government/publications/english-indices-of-deprivation-2025-technical-report |
| The technical report, a PDF of 134 pages | https://assets.publishing.service.gov.uk/media/68ff59c80f801e57b5bef907/ID_2025_Technical_Report.pdf |
| data.police.uk, data downloads | https://data.police.uk/data/ |
| data.police.uk, about | https://data.police.uk/about/ |
| data.police.uk, changelog | https://data.police.uk/changelog/ |

Credits for the counts on this page, in each publisher's own words as the licence registry holds them:

- The police's street-level crime file, and File 8 of the Indices of Deprivation: Contains public sector information licensed under the Open Government Licence v3.0.
- The geography behind each figure: Source: Office for National Statistics licensed under the Open Government Licence v.3.0.
