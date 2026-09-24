# Census 2021 tables for the area page: what was read

Read 2026-09-23. A dated snapshot, not a source of truth. It stands behind [the design of the census table](../../design/london-data-census.md).

How this was done, and its limits:

- No data file was downloaded or opened. Only pages that describe the data were read, and the records that list a table's name, categories and area types.
- Every page was read through a reader that summarises. Wording in quotation marks is as that reader returned it. It must be read again in a browser before it is relied on, and before `attribution_verified` is set on any registry entry.
- No web search was made. Every page was reached by a known address.
- Anything marked **memory** was not read today and is unverified.

## 1. The smallest area each table is published for

"Record" is the `lowest_geography` field of the table's record on the statistics office's data service. "Nomis" is the list of area types in the table's record on Nomis, the office's census download site.

| Table | Title as printed | Counts | Record | Nomis lists output areas | Use on the area page |
|---|---|---|---|---|---|
| TS003 | Household composition | Households | `oa` | Yes | Shown |
| TS004 | Country of birth | Persons | `oa` | Yes | Shown |
| TS007A | Age by five-year age bands | Persons | Not read on the data service | Yes. Output areas, LSOAs, MSOAs, local authorities, regions, countries | Shown |
| TS007B | Age by broad age bands | Persons | Not read | Yes | Not chosen. Its bands are of unequal width |
| TS007 | Age by single year | Persons | `msoa` | Not read | Too coarse |
| TS021 | Ethnic group | Persons | `oa` | Yes | Shown |
| TS024 | Main language (detailed) | Persons | `ltla` | **No.** Local authorities, local enterprise partnerships, regions and countries only | **Not shown for an area** |
| TS025 | Household language | Households | `oa` | Yes | Not chosen. Founder decision |
| TS030 | Religion | Persons | `oa` | Yes | Shown |

A trap found today: the office's page for a dataset prints "Area type: Lower tier local authorities" for TS025 as well as for TS024. That line is the page's default view and not the smallest area. The record's `lowest_geography` and the Nomis list of area types are what settle it.

The size of each kind of area, in the office's words: an output area is "between 40 and 250 households and a usually resident population of between 100 and 625 persons". An LSOA has "between 400 and 1,200 households" and "between 1,000 and 3,000 persons". An MSOA has "between 2,000 and 6,000 households" and "between 5,000 and 15,000 persons".

## 2. Categories, in the order printed

From each table's page on Nomis. The first row of each is the total. A colon in a heading is the office's own. The build does not trust this list: it compares it with the headings of the file it downloads, and stops if they differ.

**TS003 Household composition. Total: All households.**

| Group | Rows under it, in order |
|---|---|
| One-person household | Aged 66 years and over · Other |
| Single family household | All aged 66 years and over · Married or civil partnership couple (No children · Dependent children · All children non-dependent) · Cohabiting couple family (No children · With dependent children · All children non-dependent) · Lone parent family (With dependent children · All children non-dependent) · Other single family household (Other family composition) |
| Other household types | With dependent children · Other, including all full-time students and all aged 66 years and over |

**TS004 Country of birth. Total: All usual residents.**

| Group | Rows under it, in order |
|---|---|
| Europe | United Kingdom · EU countries (European Union EU14 · European Union EU8 · European Union EU2 · All other EU countries) · Non-EU countries - All other non-EU countries |
| Africa | |
| Middle East and Asia | |
| The Americas and the Caribbean | |
| Antarctica and Oceania (including Australasia) and Other | |
| British Overseas | |

The office's page on the variable gives no definition of EU14, EU8 or EU2. It speaks of "member countries in March 2001", "countries that joined between April 2001 and March 2011" and "countries that joined between April 2011 and March 2021".

**TS007A Age by five-year age bands. Total.**

Aged 4 years and under · Aged 5 to 9 years · Aged 10 to 14 years · Aged 15 to 19 years · Aged 20 to 24 years · Aged 25 to 29 years · Aged 30 to 34 years · Aged 35 to 39 years · Aged 40 to 44 years · Aged 45 to 49 years · Aged 50 to 54 years · Aged 55 to 59 years · Aged 60 to 64 years · Aged 65 to 69 years · Aged 70 to 74 years · Aged 75 to 79 years · Aged 80 to 84 years · Aged 85 years and over.

**TS021 Ethnic group. Total: All usual residents.**

| Group | Rows under it, in order |
|---|---|
| Asian, Asian British or Asian Welsh | Bangladeshi · Chinese · Indian · Pakistani · Other Asian |
| Black, Black British, Black Welsh, Caribbean or African | African · Caribbean · Other Black |
| Mixed or Multiple ethnic groups | White and Asian · White and Black African · White and Black Caribbean · Other Mixed or Multiple ethnic groups |
| White | English, Welsh, Scottish, Northern Irish or British · Irish · Gypsy or Irish Traveller · Roma · Other White |
| Other ethnic group | Arab · Any other ethnic group |

**TS030 Religion. Total: All usual residents.**

No religion · Christian · Buddhist · Hindu · Jewish · Muslim · Sikh · Other religion · Not answered.

**TS025 Household language (English and Welsh). Total: All households.** Not chosen, listed so the decision can be made.

All adults in household have English in England, or English or Welsh in Wales as a main language · At least one but not all adults in household have English in England, or English or Welsh in Wales as a main language · No adults in household, but at least one person aged 3 to 15 years, has English in England or English or Welsh in Wales as a main language · No people in household have English in England, or English or Welsh in Wales as a main language.

The data service's own classifications add a last category, "Does not apply", to each variable. The Nomis pages list none.

## 3. The office's own definitions

| Variable | Definition, as returned |
|---|---|
| Household composition | "Households according to the relationships between members." |
| Country of birth | "The country in which a person was born." |
| Age | "A person's age on Census Day, 21 March 2021 in England and Wales. Infants aged under 1 year are classified as 0 years of age." |
| Ethnic group | "The ethnic group that the person completing the census feels they belong to. This could be based on their culture, family background, identity or physical appearance." |
| Religion | "The religion people connect or identify with (their religious affiliation), whether or not they practise or have belief in it." And: "This question was voluntary and includes people who identified with one of 8 tick-box response options, including "No religion", alongside those who chose not to answer this question." |
| Main language | "A person's first or preferred language." |

## 4. Disclosure control, in the office's words

From "Protecting personal data in Census 2021 results", published 9 March 2023.

| Subject | As returned |
|---|---|
| Records swapped | "The geographies were changed for between 7% and 10% of households, and for between 2% and 5% of individuals in communal establishments." |
| Counts changed | "A typical dataset would have around 14% of cell counts perturbed by a small amount, and small counts were more likely to have been perturbed than large counts." |
| Totals between tables | "Where two or more different datasets are constructed, the totals of all cells may in turn be different. This is because of the datasets being constructed from different cells that could be perturbed in different ways." |
| Small counts | "Small counts (zero, one, and two) could be included in publicly released outputs if there was sufficient uncertainty as to whether the small cell count was a true value." |
| Adding up | "It is recommended, where possible, to construct the cells that you require, rather than adding up cells from a different dataset." |
| Tables a user builds | "up to four variables can be selected at Output Area (OA) or Lower layer Super Output Area (LSOA) level". Rules on the smallest margin, on one category holding nearly everyone, and on sparse tables apply to those. They do not apply to the published tables used here |

Each table's page on Nomis repeats the two methods: "Swapped records (targeted record swapping)" and "Added small changes to some counts (cell key perturbation)".

## 5. Quality, in the office's words

From the quality and methodology information for Census 2021, last revised 23 November 2023.

| Subject | As returned |
|---|---|
| The pandemic | "The coronavirus pandemic may have affected some people's choice of usual residence on Census Day, for example, students and in some urban areas." |
| Students | "The census counts students at their term-time address." The page cites analysis "showing a marked increase in the number of students who were not at term-time accommodation in the academic year 2020 to 2021" |
| London | "The Greater London Authority (GLA) carried out analysis to understand population change in London during the pandemic. This analysis concluded that there had been a fall in London's population over the first year of the coronavirus pandemic." |
| Response | "We achieved a very high census response rate, at 97% of the usual resident population of England and Wales and more than 88% in all local authorities." |
| Age | "Estimation for non-response is primarily conducted for five-year age groups and uncertainty will be greater for single years of age." |
| Ethnic group | "how a person chooses to identify can change over time" |

## 6. Licence and credit

| Point | As returned | From |
|---|---|---|
| Licence | "All content is available under the Open Government Licence v3.0, except where otherwise stated" | The office's page for TS024 |
| Re-use | "anyone wishing to use or re-use ONS material, whether commercially or privately, may do so freely without a specific application for a licence" | Nomis, copyright page |
| Credit | "Source: Office for National Statistics" | Nomis, copyright page |
| What may be done | "copy, publish, distribute and transmit the Information; adapt the Information; exploit the Information commercially and non-commercially" | Open Government Licence v3.0 |
| What must be done | "acknowledge the source of the Information in your product or application by including or linking to any attribution statement specified by the Information Provider(s)" | The same |
| Not covered | "personal data in the Information" | The same |
| No endorsement | "This licence does not grant you any right to use the Information in a way that suggests any official status or that the Information Provider and/or Licensor endorse you or your use" | The same |
| Not allowed | "You shall not use products to attempt to obtain or derive information relating specifically to an identified person, household or business" | Nomis, copyright page |
| Wording for figures that were added up | **None found.** The office's terms page, as returned, gives no credit line. Its page of licences gives lines for boundaries, lookups and postcode products, and none for statistics or for adapted data | The office's terms page, and its geography licences page |

## 7. The files

| Point | What is known | Basis |
|---|---|---|
| Where | The Nomis page "Census 2021 bulk data downloads" | Read |
| Packaging | "Bulk data products package all the data from a 2021 Census dataset as a single zip file. Each zip file contains separate CSV files for each geographic type (OA, LSOA, MSOA etc)." | Read |
| Names | `census2021-ts003.zip`, `census2021-ts004.zip`, `census2021-ts007a.zip`, `census2021-ts021.zip`, `census2021-ts030.zip`. A second zip, `-extra`, holds areas added later, and is not needed | Read |
| Members | One CSV for each kind of area, named for the table and the kind, such as `census2021-ts021-oa.csv` and `census2021-ts021-ltla.csv` | **Memory** |
| Columns | `date`, `geography`, `geography code`, then one column for each row of section 2, the total first. A heading begins with the variable's name | **Memory** |
| Join key | `geography code` holds the output area's code, `OA21CD`, such as `E00000001` | **Memory** for the column's name |
| Coverage | England and Wales. London is about 26,369 of about 188,880 output areas | The first is the repository's count, not re-counted. The second is **memory** |
| Size | Not printed on the page. Estimate: 5 to 20 MB a zip, under 100 MB for the five | Estimate: 188,880 rows by 12 to 27 columns of a few digits, for each of about six kinds of area, zipped to a quarter |
| Editions | The office's record for TS021 gives a release date of 28 March 2023 and is version 3. TS004 is dated 16 February 2023 | Read |

## 8. What was read

All on 2026-09-23.

| What | Address |
|---|---|
| Nomis, list of census tables | https://www.nomisweb.co.uk/sources/census_2021_ts |
| Nomis, bulk downloads | https://www.nomisweb.co.uk/sources/census_2021_bulk |
| Nomis, table pages | https://www.nomisweb.co.uk/datasets/c2021ts021 and the same for `ts003`, `ts004`, `ts007a`, `ts007b`, `ts024`, `ts025`, `ts030` |
| Nomis, record of area types for a table | https://www.nomisweb.co.uk/api/v01/dataset/NM_2041_1/geography/TYPE.def.sdmx.json and the same for `NM_2018_1` (TS007B), `NM_2020_1` (TS007A), `NM_2023_1` (TS003), `NM_2024_1` (TS004), `NM_2043_1` (TS024), `NM_2044_1` (TS025), `NM_2049_1` (TS030) |
| Nomis, copyright | https://www.nomisweb.co.uk/home/copyright.asp |
| Data service, record of a table | https://api.beta.ons.gov.uk/v1/datasets/TS021/editions/2021/versions/3 and the same for TS003, TS004, TS007, TS024, TS025, TS030 |
| The office's dataset pages | https://www.ons.gov.uk/datasets/TS024/editions/2021/versions/3 and the same for TS025 |
| Protecting personal data in Census 2021 results | https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/protectingpersonaldataincensus2021results |
| Quality and methodology information for Census 2021 | https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/qualityandmethodologyinformationqmiforcensus2021 |
| Census 2021 dictionary: area types, and the variables of section 3 | https://www.ons.gov.uk/census/census2021dictionary/areatypedefinitions and the pages for household composition, age, country of birth, ethnic group, religion and main language under `/census/census2021dictionary/variablesbytopic/` |
| Open Government Licence v3.0 | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
| The office's terms, and its geography licences | https://www.ons.gov.uk/help/termsandconditions and https://www.ons.gov.uk/methodology/geography/licences |

## 9. What was not read

| What | Standing |
|---|---|
| TS007A on the office's data service | Not read. Nomis holds the table |
| Web search | None was made |
| The office's "Build a custom area profile" tool | Not read. Whether it adds up output areas, as this design does, is not known |
| The definitions of EU14, EU8 and EU2 | Not on the pages read |
| The files themselves | Not opened, by rule |
| The office's census pages for an area, and whether one can be linked to by an area's code | Not read |
| Apple's review guidelines | Not read today |

## 10. Unverified

- The names of the files inside each zip, the names of their columns, and the exact spelling of each heading.
- That a heading in the file matches the label on the table's page, word for word.
- The count of output areas in England and Wales, and the size of each zip.
- That each table's file holds a group's own column, such as "Asian, Asian British or Asian Welsh", beside the columns of its parts.
- The shares of households swapped and of counts changed. They are as the reader returned them.
- That the lockdown in force on 21 March 2021 was a national one. The design's words say "a lockdown", as ADR 0014 does.
- That "Source: Office for National Statistics" is the line the office asks for where its counts have been added up by someone else.
- Every quotation above, until it has been read in a browser.
